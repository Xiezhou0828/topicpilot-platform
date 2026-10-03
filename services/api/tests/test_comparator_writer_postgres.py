"""Transactional writer tests using only the disposable PostgreSQL test DB."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from test_final_publication_contract import PRIOR, TARGET, point

from topicpilot_api.comparator import (
    ComparatorError,
    ComparatorPlan,
    persist_comparator,
    read_comparator,
)
from topicpilot_api.orm.models import (
    CanonicalObservation,
    Instrument,
    Market,
    RawMarketObservation,
    ReferenceAdjustment,
    ReferenceCurrency,
    ReferenceRegistrySet,
    ReferenceSession,
    ReferenceTimezone,
    ReferenceTradingStatus,
)


@pytest.fixture
def comparator_fixture(db_session):
    market = db_session.scalar(select(Market).where(Market.code == "TPE"))
    if market is None:
        market = Market(
            code="TPE",
            name="Comparator test",
            timezone="Asia/Taipei",
            calendar_code="TW_MARKET",
            exchange_code="TWSE",
        )
        db_session.add(market)
        db_session.flush()
    instrument = Instrument(
        market_id=market.id,
        instrument_code=f"CMP{uuid4().hex[:10]}",
        name="Test comparator",
        instrument_type="EQUITY",
        currency="TWD",
    )
    ref = ReferenceRegistrySet(reference_data_version=f"cmp-{uuid4().hex}", status="ACTIVE")
    db_session.add_all([instrument, ref])
    db_session.flush()
    db_session.add_all(
        [
            ReferenceCurrency(registry_set_id=ref.id, code="TWD", scale=2),
            ReferenceTimezone(registry_set_id=ref.id, name="Asia/Taipei"),
            ReferenceSession(registry_set_id=ref.id, code="REGULAR", calendar_code="TW_MARKET"),
            ReferenceTradingStatus(registry_set_id=ref.id, code="OPEN"),
            ReferenceAdjustment(registry_set_id=ref.id, code="UNKNOWN"),
        ]
    )
    db_session.flush()
    p = replace(point(), instrument_id=instrument.id, code=instrument.instrument_code)
    return db_session, ComparatorPlan(PRIOR, TARGET, ref.reference_data_version, (p,), ())


def test_comparator_write_is_price_only_with_complete_idempotent_lineage(comparator_fixture):
    session, plan = comparator_fixture
    first = persist_comparator(session, plan)
    second = persist_comparator(
        session,
        replace(
            plan,
            points=tuple(
                replace(p, retrieved_at=datetime(2026, 10, 5, tzinfo=UTC)) for p in plan.points
            ),
        ),
    )
    assert first["created"] == 1 and second["created"] == 0 and second["reused"] == 1
    result = read_comparator(session, plan)
    assert result["status"] == "PASS"
    assert result["lineage"][0]["provenance"]["responseDate"] == "20261001"
    assert result["lineage"][0]["provenance"]["payloadSize"] > 0
    assert result["lineage"][0]["idempotencyKey"]
    assert list(
        session.scalars(
            select(CanonicalObservation.family_code).where(
                CanonicalObservation.instrument_id == plan.points[0].instrument_id
            )
        )
    ) == ["PRICE"]


def test_comparator_correction_preserves_supersession_and_rejects_stale_replay(comparator_fixture):
    session, plan = comparator_fixture
    persist_comparator(session, plan)
    original = read_comparator(session, plan)["lineage"][0]
    changed = replace(
        plan,
        points=(
            replace(
                plan.points[0], bar=replace(plan.points[0].bar, close=plan.points[0].bar.close - 1)
            ),
        ),
    )
    persist_comparator(session, changed)
    assert (
        read_comparator(session, changed)["lineage"][0]["supersedesId"] == original["canonicalId"]
    )
    with pytest.raises(ComparatorError, match="STALE_OR_BROKEN_LINEAGE"):
        persist_comparator(session, plan)


def test_comparator_invalid_second_market_never_partially_writes(comparator_fixture):
    session, plan = comparator_fixture
    before = session.scalar(select(func.count()).select_from(RawMarketObservation))
    bad = replace(
        plan.points[0],
        instrument_id=uuid4(),
        market="TWO",
        bar=replace(plan.points[0].bar, close=None),
    )
    with pytest.raises(ComparatorError):
        persist_comparator(session, replace(plan, points=(*plan.points, bad)))
    assert session.scalar(select(func.count()).select_from(RawMarketObservation)) == before


def test_comparator_wrong_instrument_identity_is_rejected_before_writes(comparator_fixture):
    session, plan = comparator_fixture
    before = session.scalar(select(func.count()).select_from(RawMarketObservation))
    wrong = replace(plan, points=(replace(plan.points[0], instrument_id=uuid4()),))
    with pytest.raises(ComparatorError, match="INSTRUMENT_IDENTITY_MISMATCH"):
        persist_comparator(session, wrong)
    assert session.scalar(select(func.count()).select_from(RawMarketObservation)) == before
