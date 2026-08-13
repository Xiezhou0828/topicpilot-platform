from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from topicpilot_api.market_identity_remediation import (
    MarketIdentityRemediationConflict,
    remediate_market_identity,
)
from topicpilot_api.reference_check import inspect_reference_preflight
from topicpilot_api.reference_data import load_bundle
from topicpilot_api.reference_data.bootstrap import bootstrap_reference_bundle

pytestmark = pytest.mark.postgres

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "src" / "topicpilot_api" / "reference_data" / "bundles" / "tw-reference-v1"


def _seed_legacy_markets(engine) -> dict[str, str]:
    with engine.begin() as connection:
        rows = {}
        for code, name, exchange in (
            ("TPE", "Taiwan Stock Exchange", "TPE"),
            ("TWO", "Taipei Exchange", "TWO"),
        ):
            row_id = connection.execute(
                text(
                    "INSERT INTO topicpilot.markets "
                    "(id, code, name, exchange_code, timezone, calendar_code, is_active) "
                    "VALUES (:id, :code, :name, :exchange, 'Asia/Taipei', 'TW_MARKET', true) "
                    "RETURNING id"
                ),
                {"id": uuid4(), "code": code, "name": name, "exchange": exchange},
            ).scalar_one()
            rows[code] = str(row_id)
        return rows


def _seed_bundle_instruments(engine, bundle, market_ids, *, is_active: bool) -> None:
    payload = [
        {
            "id": uuid4(),
            "market_id": market_ids[row["market_code"]],
            "instrument_code": row["instrument_code"],
            "name": row["name"],
            "instrument_type": row["instrument_type"],
            "currency": row["currency"],
            "is_active": is_active,
        }
        for row in bundle.instruments
    ]
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO topicpilot.instruments "
                "(id, market_id, instrument_code, name, instrument_type, currency, is_active) "
                "VALUES (:id, :market_id, :instrument_code, :name, :instrument_type, "
                ":currency, :is_active)"
            ),
            payload,
        )


def _cleanup(engine) -> None:
    with engine.begin() as connection:
        for table in (
            "reference_calendar_dates",
            "reference_adjustments",
            "reference_trading_statuses",
            "reference_sessions",
            "reference_timezones",
            "reference_currencies",
        ):
            connection.execute(
                text(
                    f"DELETE FROM topicpilot.{table} WHERE registry_set_id IN "
                    "(SELECT id FROM topicpilot.reference_registry_sets "
                    "WHERE reference_data_version = 'tw-reference-v1')"
                )
            )
        connection.execute(
            text(
                "DELETE FROM topicpilot.reference_registry_sets "
                "WHERE reference_data_version = 'tw-reference-v1'"
            )
        )
        connection.execute(
            text(
                "DELETE FROM topicpilot.instruments WHERE market_id IN "
                "(SELECT id FROM topicpilot.markets WHERE code IN ('TPE', 'TWO'))"
            )
        )
        connection.execute(text("DELETE FROM topicpilot.markets WHERE code IN ('TPE', 'TWO')"))


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
            pytest.skip(
                "market identity remediation integration requires an empty isolated "
                "PostgreSQL DB"
            )


def _market_rows(engine):
    with engine.connect() as connection:
        return connection.execute(
            text(
                "SELECT code, name, exchange_code FROM topicpilot.markets "
                "WHERE code IN ('TPE', 'TWO') ORDER BY code"
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


def test_production_like_507_instruments_are_immutable_and_bootstrap_compatible(postgres_engine):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        market_ids = _seed_legacy_markets(postgres_engine)
        _seed_bundle_instruments(postgres_engine, bundle, market_ids, is_active=False)
        instruments_before = _instrument_rows(postgres_engine)
        markets_before = _market_rows(postgres_engine)

        with Session(postgres_engine, expire_on_commit=False) as session:
            baseline = inspect_reference_preflight(
                session,
                requested_version="tw-reference-v1",
                expected_market_codes=("TPE", "TWO"),
                required_session_code="REGULAR",
                required_calendar_code="TW_MARKET",
            )
        assert baseline["marketCount"] == 2
        assert baseline["instrumentCount"] == 0
        assert baseline["referenceLoadStatus"] == "NOT_READY"

        with Session(postgres_engine, expire_on_commit=False) as session:
            planned = remediate_market_identity(session, bundle, apply=False, dry_run=True)
        assert planned.operation == "PLAN"
        assert planned.instrument_count == 507
        assert planned.instrument_compatibility == "CANONICAL_BUNDLE_COMPATIBLE"
        assert _market_rows(postgres_engine) == markets_before
        assert _instrument_rows(postgres_engine) == instruments_before

        with Session(postgres_engine, expire_on_commit=False) as session:
            applied = remediate_market_identity(session, bundle, apply=True, dry_run=False)
        assert applied.operation == "APPLIED"
        assert applied.instrument_count == 507
        assert _instrument_rows(postgres_engine) == instruments_before

        with Session(postgres_engine, expire_on_commit=False) as session:
            noop = remediate_market_identity(session, bundle, apply=True, dry_run=False)
        assert noop.operation == "NOOP"
        assert _instrument_rows(postgres_engine) == instruments_before

        with Session(postgres_engine, expire_on_commit=False) as session:
            bootstrapped = bootstrap_reference_bundle(session, bundle, activate=True)
        assert bootstrapped.operation == "ACTIVATED"
        with Session(postgres_engine, expire_on_commit=False) as session:
            ready = inspect_reference_preflight(
                session,
                requested_version="tw-reference-v1",
                expected_market_codes=("TPE", "TWO"),
                required_session_code="REGULAR",
                required_calendar_code="TW_MARKET",
            )
        assert ready["referenceLoadStatus"] == "READY"
        assert ready["instrumentCount"] == 507
        with postgres_engine.connect() as connection:
            counts = dict(
                connection.execute(
                    text(
                        "SELECT markets.code, count(*) FROM topicpilot.instruments "
                        "JOIN topicpilot.markets ON markets.id = instruments.market_id "
                        "GROUP BY markets.code"
                    )
                ).all()
            )
        assert counts == {"TPE": 314, "TWO": 193}
    finally:
        _cleanup(postgres_engine)


@pytest.mark.parametrize(
    ("corrupt_sql", "error"),
    (
        (
            "UPDATE topicpilot.instruments SET currency = 'USD' "
            "WHERE id = (SELECT id FROM topicpilot.instruments ORDER BY id LIMIT 1)",
            "bundle/database conflict",
        ),
        (
            "UPDATE topicpilot.instruments SET market_id = "
            "(SELECT id FROM topicpilot.markets WHERE code = 'TWO') "
            "WHERE id = (SELECT instruments.id FROM topicpilot.instruments "
            "JOIN topicpilot.markets ON markets.id = instruments.market_id "
            "WHERE markets.code = 'TPE' ORDER BY instruments.id LIMIT 1)",
            "instrument identity set mismatch",
        ),
        (
            "DELETE FROM topicpilot.instruments WHERE id = "
            "(SELECT id FROM topicpilot.instruments ORDER BY id LIMIT 1)",
            "instrument identity set mismatch",
        ),
    ),
)
def test_incompatible_existing_instruments_block_before_market_mutation(
    postgres_engine, corrupt_sql, error
):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        market_ids = _seed_legacy_markets(postgres_engine)
        _seed_bundle_instruments(postgres_engine, bundle, market_ids, is_active=False)
        with postgres_engine.begin() as connection:
            connection.execute(text(corrupt_sql))
        markets_before = _market_rows(postgres_engine)
        instruments_before = _instrument_rows(postgres_engine)
        with (
            pytest.raises(MarketIdentityRemediationConflict, match=error),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            remediate_market_identity(session, bundle, apply=True, dry_run=False)
        assert _market_rows(postgres_engine) == markets_before
        assert _instrument_rows(postgres_engine) == instruments_before
    finally:
        _cleanup(postgres_engine)


def test_legacy_state_dry_run_apply_idempotency_and_reference_bootstrap(postgres_engine):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        primary_keys = _seed_legacy_markets(postgres_engine)
        before = _market_rows(postgres_engine)
        with Session(postgres_engine, expire_on_commit=False) as session:
            planned = remediate_market_identity(session, bundle, apply=False, dry_run=True)
        assert planned.operation == "PLAN"
        assert planned.dry_run is True
        assert planned.changes
        assert _market_rows(postgres_engine) == before

        with Session(postgres_engine, expire_on_commit=False) as session:
            applied = remediate_market_identity(session, bundle, apply=True, dry_run=False)
        assert applied.operation == "APPLIED"
        assert applied.status == "CANONICAL"
        assert _market_rows(postgres_engine) == [
            ("TPE", "TWSE Listed", "TWSE"),
            ("TWO", "TPEx OTC", "TPEx"),
        ]
        with postgres_engine.connect() as connection:
            current_ids = {
                code: str(row_id)
                for code, row_id in connection.execute(
                    text("SELECT code, id FROM topicpilot.markets WHERE code IN ('TPE', 'TWO')")
                ).all()
            }
        assert current_ids == primary_keys

        with Session(postgres_engine, expire_on_commit=False) as session:
            noop = remediate_market_identity(session, bundle, apply=False, dry_run=True)
        assert noop.operation == "NOOP"
        assert noop.changes == ()

        with Session(postgres_engine, expire_on_commit=False) as session:
            noop_apply = remediate_market_identity(session, bundle, apply=True, dry_run=False)
        assert noop_apply.operation == "NOOP"

        with Session(postgres_engine, expire_on_commit=False) as session:
            bootstrapped = bootstrap_reference_bundle(session, bundle, activate=True)
        assert bootstrapped.operation == "ACTIVATED"
        assert bootstrapped.status == "ACTIVE"
        with postgres_engine.connect() as connection:
            assert (
                connection.execute(text("SELECT count(*) FROM topicpilot.markets")).scalar_one()
                == 2
            )
            assert (
                connection.execute(
                    text("SELECT count(*) FROM topicpilot.instruments")
                ).scalar_one()
                == 507
            )
        with Session(postgres_engine, expire_on_commit=False) as session:
            ready = inspect_reference_preflight(
                session,
                requested_version="tw-reference-v1",
                expected_market_codes=("TPE", "TWO"),
                required_session_code="REGULAR",
                required_calendar_code="TW_MARKET",
            )
        assert ready["referenceLoadStatus"] == "READY"
        assert ready["instrumentCount"] == 507
    finally:
        _cleanup(postgres_engine)


def test_unexpected_mixed_market_state_blocks_without_mutation(postgres_engine):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        _seed_legacy_markets(postgres_engine)
        with postgres_engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE topicpilot.markets SET name = 'TWSE Listed', "
                    "exchange_code = 'TWSE' WHERE code = 'TPE'"
                )
            )
        before = _market_rows(postgres_engine)
        with (
            pytest.raises(MarketIdentityRemediationConflict, match="neither"),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            remediate_market_identity(session, bundle, apply=True, dry_run=False)
        assert _market_rows(postgres_engine) == before
    finally:
        _cleanup(postgres_engine)


def test_unexpected_market_shape_blocks_without_mutation(postgres_engine):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        _seed_legacy_markets(postgres_engine)
        with postgres_engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO topicpilot.markets "
                    "(id, code, name, exchange_code, timezone, calendar_code, is_active) "
                    "VALUES (:id, 'OTHER', 'Unexpected', 'OTHER', 'Asia/Taipei', "
                    "'TW_MARKET', true)"
                ),
                {"id": uuid4()},
            )
        before = _market_rows(postgres_engine)
        with (
            pytest.raises(MarketIdentityRemediationConflict, match="unexpected market count"),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            remediate_market_identity(session, bundle, apply=True, dry_run=False)
        assert _market_rows(postgres_engine) == before
    finally:
        with postgres_engine.begin() as connection:
            connection.execute(text("DELETE FROM topicpilot.markets WHERE code = 'OTHER'"))
        _cleanup(postgres_engine)


def test_instrument_state_blocks_legacy_remediation_without_changing_market_rows(postgres_engine):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        ids = _seed_legacy_markets(postgres_engine)
        with postgres_engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO topicpilot.instruments "
                    "(id, market_id, instrument_code, name, instrument_type, currency, is_active) "
                    "VALUES (:id, :market_id, 'TEST', 'Fixture', 'EQUITY', 'TWD', true)"
                ),
                {"id": uuid4(), "market_id": ids["TPE"]},
            )
        before = _market_rows(postgres_engine)
        with (
            pytest.raises(
                MarketIdentityRemediationConflict, match="instrument identity set mismatch"
            ),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            remediate_market_identity(session, bundle, apply=True, dry_run=False)
        assert _market_rows(postgres_engine) == before
    finally:
        with postgres_engine.begin() as connection:
            connection.execute(
                text("DELETE FROM topicpilot.instruments WHERE instrument_code = 'TEST'")
            )
        _cleanup(postgres_engine)


def test_reference_registry_state_blocks_legacy_remediation_without_mutation(postgres_engine):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        _seed_legacy_markets(postgres_engine)
        with postgres_engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO topicpilot.reference_registry_sets "
                    "(id, reference_data_version, status) "
                    "VALUES (:id, 'fixture-reference', 'DRAFT')"
                ),
                {"id": uuid4()},
            )
        before = _market_rows(postgres_engine)
        with (
            pytest.raises(MarketIdentityRemediationConflict, match="reference registry state"),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            remediate_market_identity(session, bundle, apply=True, dry_run=False)
        assert _market_rows(postgres_engine) == before
    finally:
        with postgres_engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM topicpilot.reference_registry_sets "
                    "WHERE reference_data_version = 'fixture-reference'"
                )
            )
        _cleanup(postgres_engine)


def test_apply_failure_rolls_back_both_market_metadata_rows(postgres_engine, monkeypatch):
    bundle = load_bundle(BUNDLE_PATH)
    _require_empty_isolated_database(postgres_engine)
    _cleanup(postgres_engine)
    try:
        _seed_legacy_markets(postgres_engine)
        before = _market_rows(postgres_engine)
        import topicpilot_api.market_identity_remediation as remediation

        original_classify = remediation._classify_state
        calls = 0

        def fail_postcondition(markets):
            nonlocal calls
            calls += 1
            if calls == 2:
                return "BROKEN"
            return original_classify(markets)

        monkeypatch.setattr(remediation, "_classify_state", fail_postcondition)
        with (
            pytest.raises(MarketIdentityRemediationConflict, match="postcondition"),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            remediate_market_identity(session, bundle, apply=True, dry_run=False)
        assert _market_rows(postgres_engine) == before
    finally:
        _cleanup(postgres_engine)
