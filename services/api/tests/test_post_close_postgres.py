from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from topicpilot_api.daily_market import reconcile_daily_market
from topicpilot_api.live.post_close import expected_post_close_universe
from topicpilot_api.reference_data import load_bundle
from topicpilot_api.reference_data.bootstrap import bootstrap_reference_bundle

pytestmark = pytest.mark.postgres

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT / "src" / "topicpilot_api" / "reference_data" / "bundles" / "tw-reference-v1"
RUN_DATE = date(2026, 8, 13)


def _table_counts(engine) -> dict[str, int]:
    tables = inspect(engine).get_table_names(schema="topicpilot")
    with engine.connect() as connection:
        return {
            table: int(
                connection.execute(text(f'SELECT count(*) FROM topicpilot."{table}"')).scalar()
                or 0
            )
            for table in tables
        }


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


def test_post_close_reference_universe_is_313_193_and_excludes_6806(
    postgres_engine,
):
    if any(_table_counts(postgres_engine).values()):
        pytest.skip(
            "post-close universe integration requires an empty isolated PostgreSQL database"
        )

    bundle = load_bundle(BUNDLE_PATH)
    try:
        with Session(postgres_engine, expire_on_commit=False) as session:
            bootstrap = bootstrap_reference_bundle(session, bundle, activate=True)
            assert bootstrap.status == "ACTIVE"
            expected = expected_post_close_universe(
                session,
                run_date=RUN_DATE,
                reference_version="tw-reference-v1",
            )
            assert len(expected["TPE"]) == 313
            assert len(expected["TWO"]) == 193
            assert "6806" not in expected["TPE"]

            rows = session.execute(
                text(
                    """
                    SELECT i.id
                    FROM topicpilot.instruments i
                    JOIN topicpilot.markets m ON m.id = i.market_id
                    WHERE (m.code, i.instrument_code) IN (
                        SELECT 'TPE', unnest(:tpe_codes)
                        UNION ALL
                        SELECT 'TWO', unnest(:two_codes)
                    )
                    """
                ),
                {"tpe_codes": list(expected["TPE"]), "two_codes": list(expected["TWO"])},
            ).scalars()
            eligible_ids = tuple(rows)
            reconciliation = reconcile_daily_market(
                session,
                RUN_DATE,
                expected_instrument_ids=eligible_ids,
            )
            assert reconciliation.expected_count == 506
            assert reconciliation.market_counts["TPE"]["expected"] == 313
            assert reconciliation.market_counts["TWO"]["expected"] == 193
    finally:
        _cleanup(postgres_engine)
