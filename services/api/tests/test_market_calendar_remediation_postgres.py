from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import topicpilot_api.market_calendar_remediation as calendar_remediation
from topicpilot_api.market_calendar_remediation import (
    MarketCalendarRemediationConflict,
    remediate_market_calendar,
)
from topicpilot_api.reference_check import inspect_reference_preflight
from topicpilot_api.reference_data import load_bundle
from topicpilot_api.reference_data.bootstrap import (
    ReferenceBootstrapConflict,
    bootstrap_reference_bundle,
)

pytestmark = pytest.mark.postgres

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "src" / "topicpilot_api" / "reference_data" / "bundles" / "tw-reference-v1"


def _require_empty_isolated_database(engine) -> None:
    tables = (
        "markets",
        "instruments",
        "topics",
        "topic_hierarchy",
        "instrument_topic_relations",
        "reference_registry_sets",
    )
    with engine.connect() as connection:
        if any(
            connection.execute(text(f"SELECT count(*) FROM topicpilot.{table}")).scalar_one()
            for table in tables
        ):
            pytest.skip("market calendar integration requires an empty isolated PostgreSQL DB")


def _cleanup(engine) -> None:
    with engine.begin() as connection:
        for table in (
            "reference_calendar_dates",
            "reference_instrument_lifecycles",
            "reference_adjustments",
            "reference_trading_statuses",
            "reference_sessions",
            "reference_timezones",
            "reference_currencies",
        ):
            connection.execute(text(f"DELETE FROM topicpilot.{table}"))
        connection.execute(text("DELETE FROM topicpilot.reference_registry_sets"))
        connection.execute(text("DELETE FROM topicpilot.instruments"))
        connection.execute(text("DELETE FROM topicpilot.markets"))


def _seed_production_like_state(engine, bundle, *, calendar_code: str | None) -> None:
    market_ids = {}
    with engine.begin() as connection:
        for row in bundle.markets:
            market_id = uuid4()
            market_ids[row["code"]] = market_id
            connection.execute(
                text(
                    "INSERT INTO topicpilot.markets "
                    "(id, code, name, exchange_code, timezone, calendar_code, is_active) "
                    "VALUES (:id, :code, :name, :exchange, :timezone, :calendar, true)"
                ),
                {
                    "id": market_id,
                    "code": row["code"],
                    "name": row["name"],
                    "exchange": row["exchange_code"],
                    "timezone": row["timezone"],
                    "calendar": calendar_code,
                },
            )
        connection.execute(
            text(
                "INSERT INTO topicpilot.instruments "
                "(id, market_id, instrument_code, name, instrument_type, currency, is_active) "
                "VALUES (:id, :market_id, :code, :name, :type, :currency, false)"
            ),
            [
                {
                    "id": uuid4(),
                    "market_id": market_ids[row["market_code"]],
                    "code": row["instrument_code"],
                    "name": row["name"],
                    "type": row["instrument_type"],
                    "currency": row["currency"],
                }
                for row in bundle.instruments
            ],
        )


def _market_rows(engine):
    with engine.connect() as connection:
        return connection.execute(
            text(
                "SELECT id, code, name, exchange_code, timezone, calendar_code, is_active "
                "FROM topicpilot.markets ORDER BY code"
            )
        ).all()


def _instrument_rows(engine):
    with engine.connect() as connection:
        return connection.execute(
            text(
                "SELECT id, market_id, instrument_code, name, instrument_type, currency, "
                "valid_from, valid_to, is_active FROM topicpilot.instruments ORDER BY id"
            )
        ).all()


def _reference_counts(engine) -> dict[str, int]:
    tables = (
        "reference_registry_sets",
        "reference_currencies",
        "reference_timezones",
        "reference_sessions",
        "reference_trading_statuses",
        "reference_adjustments",
        "reference_calendar_dates",
        "reference_instrument_lifecycles",
    )
    with engine.connect() as connection:
        return {
            table: connection.execute(text(f"SELECT count(*) FROM topicpilot.{table}")).scalar_one()
            for table in tables
        }


def test_005f_fixture_calendar_remediation_and_bootstrap_end_to_end(postgres_engine):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        _seed_production_like_state(postgres_engine, bundle, calendar_code=None)
        markets_before = _market_rows(postgres_engine)
        instruments_before = _instrument_rows(postgres_engine)

        with (
            pytest.raises(ReferenceBootstrapConflict, match="market TPE calendar"),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            bootstrap_reference_bundle(session, bundle, activate=False, dry_run=True)
        with (
            pytest.raises(ReferenceBootstrapConflict, match="market TPE calendar"),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            bootstrap_reference_bundle(session, bundle, activate=True)
        assert _reference_counts(postgres_engine) == {
            "reference_registry_sets": 0,
            "reference_currencies": 0,
            "reference_timezones": 0,
            "reference_sessions": 0,
            "reference_trading_statuses": 0,
            "reference_adjustments": 0,
            "reference_calendar_dates": 0,
            "reference_instrument_lifecycles": 0,
        }

        with Session(postgres_engine, expire_on_commit=False) as session:
            planned = remediate_market_calendar(session, bundle, apply=False, dry_run=True)
        assert planned.operation == "PLAN"
        assert planned.status == "VALIDATED"
        assert planned.semantic_compatibility == "BUNDLE_COMPATIBLE_NULL_CALENDAR"
        assert planned.instrument_count == 507
        assert {change["newCalendarCode"] for change in planned.changes} == {"TW_MARKET"}
        assert _market_rows(postgres_engine) == markets_before
        assert _instrument_rows(postgres_engine) == instruments_before

        with Session(postgres_engine, expire_on_commit=False) as session:
            applied = remediate_market_calendar(session, bundle, apply=True, dry_run=False)
        assert applied.operation == "APPLIED"
        assert {row.calendar_code for row in _market_rows(postgres_engine)} == {"TW_MARKET"}
        assert [row[:5] + row[6:] for row in _market_rows(postgres_engine)] == [
            row[:5] + row[6:] for row in markets_before
        ]
        assert _instrument_rows(postgres_engine) == instruments_before

        with Session(postgres_engine, expire_on_commit=False) as session:
            noop = remediate_market_calendar(session, bundle, apply=True, dry_run=False)
        assert noop.operation == "NOOP"

        with Session(postgres_engine, expire_on_commit=False) as session:
            bootstrap_plan = bootstrap_reference_bundle(
                session, bundle, activate=False, dry_run=True
            )
        assert bootstrap_plan.operation == "PLAN"
        with Session(postgres_engine, expire_on_commit=False) as session:
            activated = bootstrap_reference_bundle(session, bundle, activate=True)
        assert activated.operation == "ACTIVATED"
        assert activated.status == "ACTIVE"

        with Session(postgres_engine, expire_on_commit=False) as session:
            ready = inspect_reference_preflight(
                session,
                requested_version="tw-reference-v1",
                expected_market_codes=("TPE", "TWO"),
                required_session_code="REGULAR",
                required_calendar_code="TW_MARKET",
            )
        assert ready["referenceLoadStatus"] == "READY"
        assert ready["marketCount"] == 2
        assert ready["instrumentCount"] == 507
        assert ready["missingMarkets"] == []
        assert ready["missingInstruments"] == []
        assert ready["duplicateIdentities"] == []
        with postgres_engine.connect() as connection:
            distribution = dict(
                connection.execute(
                    text(
                        "SELECT markets.code, count(*) FROM topicpilot.instruments "
                        "JOIN topicpilot.markets ON markets.id = instruments.market_id "
                        "WHERE instruments.is_active IS true GROUP BY markets.code"
                    )
                ).all()
            )
        assert distribution == {"TPE": 314, "TWO": 193}
    finally:
        _cleanup(postgres_engine)


@pytest.mark.parametrize(
    "mutation",
    (
        "UPDATE topicpilot.markets SET calendar_code='OTHER' WHERE code='TPE'",
        "UPDATE topicpilot.markets SET timezone='UTC' WHERE code='TPE'",
        "UPDATE topicpilot.markets SET name='Unexpected' WHERE code='TPE'",
    ),
)
def test_conflicting_market_context_blocks_without_mutation(postgres_engine, mutation):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        _seed_production_like_state(postgres_engine, bundle, calendar_code=None)
        with postgres_engine.begin() as connection:
            connection.execute(text(mutation))
        markets_before = _market_rows(postgres_engine)
        instruments_before = _instrument_rows(postgres_engine)
        with (
            pytest.raises(MarketCalendarRemediationConflict),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            remediate_market_calendar(session, bundle, apply=True, dry_run=False)
        assert _market_rows(postgres_engine) == markets_before
        assert _instrument_rows(postgres_engine) == instruments_before
        assert not any(_reference_counts(postgres_engine).values())
    finally:
        _cleanup(postgres_engine)


def test_unexpected_market_blocks_calendar_remediation(postgres_engine):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        _seed_production_like_state(postgres_engine, bundle, calendar_code=None)
        with postgres_engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO topicpilot.markets "
                    "(id, code, name, timezone, is_active) "
                    "VALUES (:id, 'THIRD', 'Unexpected', 'Asia/Taipei', true)"
                ),
                {"id": uuid4()},
            )
        before = _market_rows(postgres_engine)
        with (
            pytest.raises(MarketCalendarRemediationConflict, match="market topology"),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            remediate_market_calendar(session, bundle, apply=False, dry_run=True)
        assert _market_rows(postgres_engine) == before
    finally:
        _cleanup(postgres_engine)


def test_apply_postcondition_failure_rolls_back_calendars(postgres_engine, monkeypatch):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        _seed_production_like_state(postgres_engine, bundle, calendar_code=None)
        before = _market_rows(postgres_engine)
        original = calendar_remediation._inspect
        calls = 0

        def fail_after_flush(session, reference_bundle):
            nonlocal calls
            result = original(session, reference_bundle)
            calls += 1
            if calls == 2:
                raise MarketCalendarRemediationConflict("injected postcondition failure")
            return result

        monkeypatch.setattr(calendar_remediation, "_inspect", fail_after_flush)
        with (
            pytest.raises(MarketCalendarRemediationConflict, match="injected"),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            remediate_market_calendar(session, bundle, apply=True, dry_run=False)
        assert _market_rows(postgres_engine) == before
        assert not any(_reference_counts(postgres_engine).values())
    finally:
        _cleanup(postgres_engine)
