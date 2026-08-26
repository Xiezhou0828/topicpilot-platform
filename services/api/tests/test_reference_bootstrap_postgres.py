from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from topicpilot_api.reference_check import inspect_reference_preflight
from topicpilot_api.reference_data import load_bundle
from topicpilot_api.reference_data.bootstrap import (
    ReferenceBootstrapConflict,
    bootstrap_reference_bundle,
)

pytestmark = pytest.mark.postgres

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "src" / "topicpilot_api" / "reference_data" / "bundles" / "tw-reference-v1"


def _table_count(engine, table: str) -> int:
    with engine.connect() as connection:
        return int(
            connection.execute(text(f"SELECT count(*) FROM topicpilot.{table}")).scalar() or 0
        )


def _cleanup(engine, versions: tuple[str, ...]) -> None:
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
            connection.execute(
                text(
                    f"DELETE FROM topicpilot.{table} WHERE registry_set_id IN "
                    "(SELECT id FROM topicpilot.reference_registry_sets "
                    "WHERE reference_data_version = ANY(:versions))"
                ),
                {"versions": list(versions)},
            )
        connection.execute(
            text(
                "DELETE FROM topicpilot.reference_instrument_lifecycles "
                "WHERE instrument_id IN ("
                "SELECT id FROM topicpilot.instruments "
                "WHERE market_id IN (SELECT id FROM topicpilot.markets "
                "WHERE code IN ('TPE', 'TWO'))"
                ")"
            )
        )
        connection.execute(
            text(
                "DELETE FROM topicpilot.reference_registry_sets "
                "WHERE reference_data_version = ANY(:versions)"
            ),
            {"versions": list(versions)},
        )
        connection.execute(
            text(
                "DELETE FROM topicpilot.instruments WHERE market_id IN "
                "(SELECT id FROM topicpilot.markets WHERE code IN ('TPE', 'TWO'))"
            )
        )
        connection.execute(
            text("DELETE FROM topicpilot.markets WHERE code IN ('TPE', 'TWO')")
        )


def test_empty_database_bootstrap_dry_run_rerun_activation_and_reference_check(postgres_engine):
    non_reference_tables = (
        "topics",
        "topic_hierarchy",
        "instrument_topic_relations",
        "raw_market_observations",
        "observation_timeline_entries",
        "canonical_observations",
        "topic_snapshots",
        "topic_lifecycle_results",
    )
    can_cleanup = False
    reference_version = "tw-reference-v1"
    second_version = "tw-reference-v1-test-second"
    bad_version = "tw-reference-v1-test-rollback"
    try:
        if any(_table_count(postgres_engine, table) for table in non_reference_tables):
            pytest.skip("reference bootstrap integration requires an empty isolated PostgreSQL DB")
        if any(_table_count(postgres_engine, table) for table in ("markets", "instruments")):
            pytest.skip("identity tables are not empty in this PostgreSQL test DB")
        can_cleanup = True

        bundle = load_bundle(BUNDLE_PATH)
        reference_version = bundle.manifest["referenceDataVersion"]
        with Session(postgres_engine, expire_on_commit=False) as session:
            result = bootstrap_reference_bundle(session, bundle, activate=True)
        assert result.operation == "ACTIVATED"
        assert result.status == "ACTIVE"
        assert _table_count(postgres_engine, "markets") == 2
        assert _table_count(postgres_engine, "instruments") == 507
        assert _table_count(postgres_engine, "reference_calendar_dates") == 24
        assert _table_count(postgres_engine, "reference_instrument_lifecycles") == len(
            bundle.instrument_lifecycles
        )

        before_dry_run = {
            table: _table_count(postgres_engine, table)
            for table in ("markets", "instruments", "reference_registry_sets")
        }
        with Session(postgres_engine, expire_on_commit=False) as session:
            dry_run = bootstrap_reference_bundle(session, bundle, activate=False, dry_run=True)
        assert dry_run.dry_run is True
        assert {
            table: _table_count(postgres_engine, table)
            for table in before_dry_run
        } == before_dry_run

        with Session(postgres_engine, expire_on_commit=False) as session:
            rerun = bootstrap_reference_bundle(session, bundle, activate=True)
        assert rerun.operation == "NOOP"

        with Session(postgres_engine, expire_on_commit=False) as session:
            ready = inspect_reference_preflight(
                session,
                requested_version=reference_version,
                expected_market_codes=("TPE", "TWO"),
                required_session_code="REGULAR",
                required_calendar_code="TW_MARKET",
            )
        assert ready["referenceLoadStatus"] == "READY"
        assert ready["instrumentCount"] == 507
        assert ready["REFERENCE_CALENDAR_DATE_COUNT"] == 24

        with postgres_engine.connect() as connection:
            lifecycle_rows = connection.execute(
                text(
                    "SELECT rl.status_code, rl.effective_from, rl.effective_to "
                    "FROM topicpilot.reference_instrument_lifecycles rl "
                    "JOIN topicpilot.instruments i ON i.id = rl.instrument_id "
                    "JOIN topicpilot.markets m ON m.id = i.market_id "
                    "WHERE rl.registry_set_id = ("
                    "SELECT id FROM topicpilot.reference_registry_sets "
                    "WHERE reference_data_version = :reference_version"
                    ") AND i.instrument_code = '5371' AND m.code = 'TWO' "
                    "ORDER BY rl.effective_from"
                ),
                {"reference_version": reference_version},
            ).all()
        assert lifecycle_rows == [
            ("SUSPENDED", date(2026, 8, 24), date(2026, 9, 2)),
            ("TERMINATED", date(2026, 9, 3), None),
        ]

        second_manifest = dict(bundle.manifest)
        second_version = f"{reference_version}-test-second"
        second_manifest["referenceDataVersion"] = second_version
        second = replace(bundle, manifest=second_manifest)
        with Session(postgres_engine, expire_on_commit=False) as session:
            second_result = bootstrap_reference_bundle(session, second, activate=True)
        assert second_result.status == "ACTIVE"
        with postgres_engine.connect() as connection:
            active_count = connection.execute(
                text(
                    "SELECT count(*) FROM topicpilot.reference_registry_sets "
                    "WHERE status = 'ACTIVE'"
                )
            ).scalar()
            first_status = connection.execute(
                text(
                    "SELECT status FROM topicpilot.reference_registry_sets "
                    "WHERE reference_data_version = :reference_version"
                ),
                {"reference_version": reference_version},
            ).scalar_one()
        assert active_count == 1
        assert first_status == "RETIRED"

        bad_manifest = dict(bundle.manifest)
        bad_version = f"{reference_version}-test-rollback"
        bad_manifest["referenceDataVersion"] = bad_version
        bad_markets = (dict(bundle.markets[0], name="conflicting market"), *bundle.markets[1:])
        bad_bundle = replace(bundle, manifest=bad_manifest, markets=bad_markets)
        with (
            pytest.raises(ReferenceBootstrapConflict),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            bootstrap_reference_bundle(session, bad_bundle, activate=True)
        assert _table_count(postgres_engine, "reference_registry_sets") == 2
    finally:
        if can_cleanup:
            _cleanup(
                postgres_engine,
                (
                    reference_version,
                    second_version,
                    bad_version,
                ),
            )
