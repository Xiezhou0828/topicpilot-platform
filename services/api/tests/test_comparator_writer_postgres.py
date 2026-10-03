"""Transactional writer tests using only the disposable PostgreSQL test DB."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, inspect, select
from test_final_publication_contract import PRIOR, TARGET, point

from topicpilot_api.comparator import (
    ComparatorError,
    ComparatorPlan,
    persist_comparator,
    read_comparator,
)
from topicpilot_api.market_data.ingestion import HistoricalIngestionError
from topicpilot_api.normalizer import NormalizationRuntime
from topicpilot_api.orm import LiveCollectorRun
from topicpilot_api.orm.home import HomePublication
from topicpilot_api.orm.models import (
    CanonicalObservation,
    Instrument,
    Market,
    MarketDataSource,
    ObservationTimelineBatch,
    ObservationTimelineEntry,
    RawMarketObservation,
    ReferenceAdjustment,
    ReferenceCurrency,
    ReferenceRegistrySet,
    ReferenceSession,
    ReferenceTimezone,
    ReferenceTradingStatus,
)
from topicpilot_api.orm.snapshots import TopicSnapshot
from topicpilot_api.provider_preflight import (
    PROVIDER_AUTHORITY_BY_MARKET,
    PROVIDER_VERSION_BY_MARKET,
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


@pytest.fixture(params=("TPE", "TWO"))
def official_source_fixture(comparator_fixture, request):
    """Seed the real existing official source contract inside the test transaction."""
    session, plan = comparator_fixture
    market_code = request.param
    if market_code == "TWO":
        market = session.scalar(select(Market).where(Market.code == "TWO"))
        if market is None:
            market = Market(
                code="TWO",
                name="Comparator test",
                timezone="Asia/Taipei",
                calendar_code="TW_MARKET",
                exchange_code="TPEx",
            )
            session.add(market)
            session.flush()
        instrument = Instrument(
            market_id=market.id,
            instrument_code=f"CMP{uuid4().hex[:10]}",
            name="Test comparator",
            instrument_type="EQUITY",
            currency="TWD",
        )
        session.add(instrument)
        session.flush()
        p = replace(
            plan.points[0],
            instrument_id=instrument.id,
            code=instrument.instrument_code,
            market=market_code,
            receipt={
                **plan.points[0].receipt,
                "endpoint": (
                    "https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes?"
                    "date=2026%2F10%2F01&response=json"
                ),
            },
        )
        plan = replace(plan, points=(p,))
    source = session.scalar(
        select(MarketDataSource).where(
            MarketDataSource.source_code == PROVIDER_AUTHORITY_BY_MARKET[market_code],
            MarketDataSource.adapter_version == PROVIDER_VERSION_BY_MARKET[market_code],
        )
    )
    if source is None:
        source = MarketDataSource(
            source_code=PROVIDER_AUTHORITY_BY_MARKET[market_code],
            adapter_version=PROVIDER_VERSION_BY_MARKET[market_code],
        )
        session.add(source)
    # This controlled seed is local-only and rolled back by db_session. It
    # represents an existing official registration, not a writer repair.
    source.source_category = "HISTORICAL_DAILY"
    source.observation_semantics = "DAILY_BAR"
    source.adjustment_policy = "UNKNOWN"
    source.calendar_policy = "MARKET_CALENDAR"
    source.licensing_classification = "OFFICIAL_PUBLIC"
    source.status = "REGISTERED"
    session.flush()
    return session, plan, source


def source_state(source):
    return {
        column.key: getattr(source, column.key) for column in inspect(MarketDataSource).column_attrs
    }


def write_scope_counts(session):
    return {
        model.__tablename__: session.scalar(select(func.count()).select_from(model))
        for model in (
            RawMarketObservation,
            ObservationTimelineBatch,
            ObservationTimelineEntry,
            CanonicalObservation,
            HomePublication,
            TopicSnapshot,
            LiveCollectorRun,
        )
    }


def test_existing_official_source_persists_and_reuses_without_metadata_change(
    official_source_fixture,
):
    session, plan, source = official_source_fixture
    before = source_state(source)
    unrelated = write_scope_counts(session)
    result = persist_comparator(session, plan)
    assert result["created"] == 1
    readback = read_comparator(session, plan)
    assert readback["status"] == "PASS"
    canonical_id = readback["lineage"][0]["canonicalId"]
    canonical = session.scalar(
        select(CanonicalObservation).where(
            CanonicalObservation.instrument_id == plan.points[0].instrument_id,
        )
    )
    assert str(canonical.id) == canonical_id and canonical.source_id == source.id
    assert canonical.family_code == "PRICE" and canonical.quality_state == "ACCEPTED"
    repeated = persist_comparator(session, plan)
    assert repeated["created"] == 0 and repeated["reused"] == 1
    assert read_comparator(session, plan)["lineage"][0]["canonicalId"] == canonical_id
    session.refresh(source)
    assert source_state(source) == before
    after = write_scope_counts(session)
    for model in (HomePublication, TopicSnapshot, LiveCollectorRun):
        assert after[model.__tablename__] == unrelated[model.__tablename__]


def test_nonofficial_registration_remains_rejected_without_writes(official_source_fixture):
    session, plan, source = official_source_fixture
    source.licensing_classification = "PRIVATE_RUNTIME"
    session.flush()
    before, counts = source_state(source), write_scope_counts(session)
    with pytest.raises(HistoricalIngestionError, match="SOURCE_METADATA_CONFLICT"):
        persist_comparator(session, plan)
    assert write_scope_counts(session) == counts
    session.refresh(source)
    assert source_state(source) == before


def test_existing_official_source_write_failure_rolls_back_entire_chain(
    official_source_fixture,
    monkeypatch,
):
    session, plan, source = official_source_fixture
    original = session.get(Instrument, plan.points[0].instrument_id)
    second = Instrument(
        market_id=original.market_id,
        instrument_code=f"CMP{uuid4().hex[:10]}",
        name="Test comparator rollback",
        instrument_type="EQUITY",
        currency="TWD",
    )
    session.add(second)
    session.flush()
    plan = replace(
        plan,
        points=(
            *plan.points,
            replace(
                plan.points[0],
                instrument_id=second.id,
                code=second.instrument_code,
            ),
        ),
    )
    before, counts = source_state(source), write_scope_counts(session)
    normalize = NormalizationRuntime.normalize_timeline_entry
    calls = []

    def fail_after_first_price(runtime, *args, **kwargs):
        calls.append(args[0])
        if len(calls) == 2:
            raise RuntimeError("CONTROLLED_TEST_WRITE_FAILURE")
        return normalize(runtime, *args, **kwargs)

    monkeypatch.setattr(NormalizationRuntime, "normalize_timeline_entry", fail_after_first_price)
    with pytest.raises(RuntimeError, match="CONTROLLED_TEST_WRITE_FAILURE"), session.begin_nested():
        persist_comparator(session, plan)
    assert len(calls) == 2  # A real PRICE write preceded the controlled failure.
    assert write_scope_counts(session) == counts
    session.refresh(source)
    assert source_state(source) == before
