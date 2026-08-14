from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from topicpilot_api.orm.models import ReferenceRegistrySet
from topicpilot_api.provider_preflight import load_g2_preflight_context
from topicpilot_api.reference_check import inspect_reference_preflight
from topicpilot_api.reference_data import load_bundle
from topicpilot_api.reference_data.bootstrap import ReferenceBootstrapConflict
from topicpilot_api.reference_data.transition import (
    derive_transition_version,
    transition_reference_registry,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "src" / "topicpilot_api" / "reference_data" / "bundles" / "tw-reference-v1"
OLD_BUNDLE_SHA = "5db36231decaeb12010ca7624c0d2bdc18da3b86dcec5611aa5ff7c132af15e6"


def _cleanup(engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM topicpilot.reference_registry_transitions"))
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


def _require_empty(engine) -> None:
    with engine.connect() as connection:
        tables = (
            "markets",
            "instruments",
            "reference_registry_sets",
            "reference_registry_transitions",
        )
        if any(
            connection.execute(text(f"SELECT count(*) FROM topicpilot.{table}")).scalar_one()
            for table in tables
        ):
            pytest.skip("registry transition integration requires an empty isolated database")


def _seed_old_active_registry(engine) -> None:
    with Session(engine, expire_on_commit=False) as session:
        session.add(
            ReferenceRegistrySet(
                reference_data_version="tw-reference-v1",
                status="ACTIVE",
                description="old production reference registry fixture",
                bundle_sha256=OLD_BUNDLE_SHA,
                source_manifest_sha256="a" * 64,
            )
        )
        session.commit()


def test_transition_version_is_deterministic_and_hash_bound():
    assert (
        derive_transition_version("tw-reference-v1", "a" * 64)
        == "tw-reference-v1-rollover-aaaaaaaaaaaaaaaa"
    )
    with pytest.raises(ReferenceBootstrapConflict):
        derive_transition_version("tw-reference-v1", "not-a-sha")


@pytest.mark.postgres
def test_reference_registry_rollover_preserves_provenance_and_is_idempotent(postgres_engine):
    _require_empty(postgres_engine)
    bundle = load_bundle(BUNDLE_PATH)
    target_version = derive_transition_version("tw-reference-v1", bundle.digest())
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
    try:
        _seed_old_active_registry(postgres_engine)
        with postgres_engine.connect() as connection:
            non_reference_before = {
                table: connection.execute(
                    text(f"SELECT count(*) FROM topicpilot.{table}")
                ).scalar_one()
                for table in non_reference_tables
            }
        with (
            pytest.raises(ReferenceBootstrapConflict, match="same-version hash"),
            Session(postgres_engine) as session,
        ):
            transition_reference_registry(
                session,
                bundle,
                from_reference_version="tw-reference-v1",
                expected_from_bundle_sha256=bundle.digest(),
                activate=False,
                dry_run=True,
            )
        with Session(postgres_engine, expire_on_commit=False) as session:
            plan = transition_reference_registry(
                session,
                bundle,
                from_reference_version="tw-reference-v1",
                expected_from_bundle_sha256=OLD_BUNDLE_SHA,
                activate=False,
                dry_run=True,
            )
        assert plan.operation == "PLAN"
        assert plan.dry_run is True
        assert plan.to_reference_data_version == target_version
        assert plan.to_dict()["nonReferenceWriteSet"] == []
        assert "reference_registry_transitions" in plan.to_dict()["writeSet"]
        with postgres_engine.connect() as connection:
            assert connection.execute(
                text("SELECT count(*) FROM topicpilot.reference_registry_sets")
            ).scalar_one() == 1
            assert connection.execute(
                text("SELECT count(*) FROM topicpilot.markets")
            ).scalar_one() == 0

        with Session(postgres_engine, expire_on_commit=False) as session:
            applied = transition_reference_registry(
                session,
                bundle,
                from_reference_version="tw-reference-v1",
                expected_from_bundle_sha256=OLD_BUNDLE_SHA,
                activate=True,
            )
        assert applied.operation == "TRANSITION_ACTIVATED"
        assert applied.status == "ACTIVE"
        assert applied.to_reference_data_version == target_version
        assert applied.retired_registry_sets == 1
        assert applied.transition_recorded is True

        with postgres_engine.connect() as connection:
            assert connection.execute(
                text(
                    "SELECT count(*) FROM topicpilot.reference_registry_sets "
                    "WHERE status = 'ACTIVE'"
                )
            ).scalar_one() == 1
            assert connection.execute(
                text(
                    "SELECT status FROM topicpilot.reference_registry_sets "
                    "WHERE reference_data_version = 'tw-reference-v1'"
                )
            ).scalar_one() == "RETIRED"
            assert connection.execute(
                text("SELECT count(*) FROM topicpilot.reference_registry_transitions")
            ).scalar_one() == 1
            assert connection.execute(
                text("SELECT count(*) FROM topicpilot.reference_instrument_lifecycles")
            ).scalar_one() == 1
            assert connection.execute(
                text("SELECT count(*) FROM topicpilot.instruments")
            ).scalar_one() == 507
            assert {
                table: connection.execute(
                    text(f"SELECT count(*) FROM topicpilot.{table}")
                ).scalar_one()
                for table in non_reference_tables
            } == non_reference_before

        with Session(postgres_engine) as session:
            ready = inspect_reference_preflight(
                session,
                requested_version=target_version,
                expected_market_codes=("TPE", "TWO"),
                required_session_code="REGULAR",
                required_calendar_code="TW_MARKET",
            )
            context = load_g2_preflight_context(
                session,
                target_date=date(2026, 8, 13),
                reference_version=target_version,
            )
        assert ready["referenceLoadStatus"] == "READY"
        assert context.context_ready is True
        assert {market.market_code: len(market.instrument_codes) for market in context.markets} == {
            "TPE": 313,
            "TWO": 193,
        }

        with Session(postgres_engine, expire_on_commit=False) as session:
            noop = transition_reference_registry(
                session,
                bundle,
                from_reference_version="tw-reference-v1",
                expected_from_bundle_sha256=OLD_BUNDLE_SHA,
                activate=True,
            )
        assert noop.operation == "NOOP"
        assert noop.transition_recorded is True
    finally:
        _cleanup(postgres_engine)


@pytest.mark.postgres
def test_transition_failure_rolls_back_retirement_and_target_creation(postgres_engine):
    _require_empty(postgres_engine)
    bundle = load_bundle(BUNDLE_PATH)
    try:
        _seed_old_active_registry(postgres_engine)
        with postgres_engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO topicpilot.markets "
                    "(id, code, name, exchange_code, timezone, calendar_code, is_active) "
                    "VALUES (:id, 'TPE', 'conflicting market', 'TWSE', "
                    "'Asia/Taipei', 'TW_MARKET', true)"
                ),
                {"id": uuid4()},
            )
        with (
            pytest.raises(ReferenceBootstrapConflict),
            Session(postgres_engine, expire_on_commit=False) as session,
        ):
            transition_reference_registry(
                session,
                bundle,
                from_reference_version="tw-reference-v1",
                expected_from_bundle_sha256=OLD_BUNDLE_SHA,
                activate=True,
            )

        with postgres_engine.connect() as connection:
            assert connection.execute(
                text(
                    "SELECT status FROM topicpilot.reference_registry_sets "
                    "WHERE reference_data_version = 'tw-reference-v1'"
                )
            ).scalar_one() == "ACTIVE"
            assert connection.execute(
                text("SELECT count(*) FROM topicpilot.reference_registry_transitions")
            ).scalar_one() == 0
            assert connection.execute(
                text("SELECT count(*) FROM topicpilot.reference_registry_sets")
            ).scalar_one() == 1
            assert connection.execute(
                text("SELECT count(*) FROM topicpilot.instruments")
            ).scalar_one() == 0
    finally:
        _cleanup(postgres_engine)
