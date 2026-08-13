from __future__ import annotations

import json
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from topicpilot_api.provider_preflight import load_g2_preflight_context, run_provider_preflight

pytestmark = pytest.mark.postgres


def _count(engine, table: str) -> int:
    with engine.connect() as connection:
        return int(
            connection.execute(text(f"SELECT count(*) FROM topicpilot.{table}")).scalar() or 0
        )


def _twse_payload(codes: tuple[str, ...]) -> bytes:
    return json.dumps(
        {
            "stat": "OK",
            "date": "20260807",
            "tables": [
                {
                    "fields": [
                        "證券代號",
                        "證券名稱",
                        "成交股數",
                        "成交筆數",
                        "成交金額",
                        "開盤價",
                        "最高價",
                        "最低價",
                        "收盤價",
                    ],
                    "data": [
                        [code, "Fixture", "1,000", "10", "100,000", "100", "105", "99", "104"]
                        for code in codes
                    ],
                }
            ],
        }
    ).encode()


def _tpex_payload(codes: tuple[str, ...]) -> bytes:
    return json.dumps(
        {
            "stat": "ok",
            "date": "20260807",
            "tables": [
                {
                    "title": "上櫃股票行情",
                    "fields": [
                        "代號",
                        "名稱",
                        "收盤",
                        "漲跌",
                        "開盤",
                        "最高",
                        "最低",
                        "均價",
                        "成交股數",
                    ],
                    "data": [
                        [code, "Fixture", "50", "+1", "49", "51", "48", "50", "3,000"]
                        for code in codes
                    ],
                }
            ],
        }
    ).encode()


def test_provider_preflight_is_select_only_and_leaves_all_write_tables_unchanged(
    postgres_engine,
):
    with Session(postgres_engine, expire_on_commit=False) as session:
        context = load_g2_preflight_context(
            session,
            target_date=date(2026, 8, 7),
            reference_version="tw-reference-v1",
        )
    if not context.context_ready:
        pytest.skip("requires the completed tw-reference-v1 identity/context state")

    tables = (
        "markets",
        "instruments",
        "reference_registry_sets",
        "reference_calendar_dates",
        "raw_market_observations",
        "observation_timeline_batches",
        "observation_timeline_entries",
        "observation_timeline_quality_events",
        "canonical_observations",
        "canonical_price_observations",
        "canonical_volume_observations",
        "canonical_trading_status_observations",
        "live_collector_runs",
        "live_collector_attempts",
        "live_tracking_universe",
        "topic_snapshots",
        "topic_lifecycle_results",
    )
    before = {table: _count(postgres_engine, table) for table in tables}

    def transport(url: str, _timeout: float) -> bytes:
        if "MI_INDEX" in url:
            return _twse_payload(
                next(m.instrument_codes for m in context.markets if m.market_code == "TPE")
            )
        if "dailyQuotes" in url:
            return _tpex_payload(
                next(m.instrument_codes for m in context.markets if m.market_code == "TWO")
            )
        raise AssertionError(f"unexpected provider URL: {url}")

    with Session(postgres_engine, expire_on_commit=False) as session:
        result = run_provider_preflight(
            session,
            target_date=date(2026, 8, 7),
            reference_version="tw-reference-v1",
            transport=transport,
        )

    after = {table: _count(postgres_engine, table) for table in tables}
    assert result["status"] == "PASS"
    assert result["readOnly"] is True
    assert result["productionWriteSet"] == []
    assert result["nonReferenceWriteSet"] == []
    assert before == after
