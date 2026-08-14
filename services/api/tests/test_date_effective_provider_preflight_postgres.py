from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from topicpilot_api.provider_preflight import load_g2_preflight_context
from topicpilot_api.reference_data import load_bundle
from topicpilot_api.reference_data.bootstrap import bootstrap_reference_bundle

pytestmark = pytest.mark.postgres

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "src" / "topicpilot_api" / "reference_data" / "bundles" / "tw-reference-v1"


def _count(engine, table: str) -> int:
    with engine.connect() as connection:
        return int(
            connection.execute(text(f"SELECT count(*) FROM topicpilot.{table}")).scalar() or 0
        )


def _cleanup(engine) -> None:
    with engine.begin() as connection:
        for table in (
            "reference_instrument_lifecycles",
            "reference_calendar_dates",
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


def test_date_effective_g2_universe_uses_reference_lifecycle_rows(postgres_engine):
    if any(
        _count(postgres_engine, table)
        for table in ("markets", "instruments", "reference_registry_sets")
    ):
        pytest.skip("date-effective integration requires an empty isolated PostgreSQL DB")
    bundle = load_bundle(BUNDLE_PATH)
    try:
        with Session(postgres_engine, expire_on_commit=False) as session:
            result = bootstrap_reference_bundle(session, bundle, activate=True)
        assert result.status == "ACTIVE"
        assert _count(postgres_engine, "reference_instrument_lifecycles") == 1

        with Session(postgres_engine, expire_on_commit=False) as session:
            context = load_g2_preflight_context(
                session,
                target_date=date(2026, 8, 13),
                reference_version="tw-reference-v1",
            )

        assert context.context_ready is True
        assert context.eligibility_error is None
        assert {
            market.market_code: len(market.instrument_codes) for market in context.markets
        } == {"TPE": 313, "TWO": 193}
        assert "6806" not in next(
            market.instrument_codes for market in context.markets if market.market_code == "TPE"
        )
        assert _count(postgres_engine, "instruments") == 507
    finally:
        _cleanup(postgres_engine)
