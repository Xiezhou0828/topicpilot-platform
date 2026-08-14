from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

import topicpilot_api.market_semantics as semantics
from topicpilot_api.market_data.history import HistoricalBar
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
                connection.execute(text(f'SELECT count(*) FROM topicpilot."{table}"')).scalar() or 0
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


class _FakeAdapter:
    market_batch = True

    def __init__(self, *, version: str, codes: tuple[str, ...]) -> None:
        self.adapter_version = version
        self._codes = codes

    def fetch_market_day(self):
        bars = {
            code: HistoricalBar(
                trading_date=RUN_DATE,
                open=Decimal("1"),
                high=Decimal("1"),
                low=Decimal("1"),
                close=Decimal("1"),
                volume=Decimal("1"),
            )
            for code in self._codes
        }
        return datetime(2026, 8, 13), bars


class _FakeRegistration:
    def __init__(self, code: str, adapter: _FakeAdapter) -> None:
        self.code = code
        self.adapter = adapter


class _FakeRegistry:
    def __init__(self, registrations: dict[str, _FakeRegistration]) -> None:
        self._registrations = registrations

    def for_market(self, market_code: str):
        return (self._registrations[market_code],)


def test_g3_postgres_select_only_pass_keeps_every_table_count_unchanged(
    postgres_engine, monkeypatch
):
    if any(_table_counts(postgres_engine).values()):
        pytest.skip("G3 integration requires an empty isolated PostgreSQL database")

    bundle = load_bundle(BUNDLE_PATH)
    try:
        with Session(postgres_engine, expire_on_commit=False) as session:
            bootstrap = bootstrap_reference_bundle(session, bundle, activate=True)
        assert bootstrap.status == "ACTIVE"

        with Session(postgres_engine, expire_on_commit=False) as session:
            context = semantics.load_g3_preflight_context(
                session,
                target_date=RUN_DATE,
                reference_version="tw-reference-v1",
            )
        expected = {
            market.market_code: market.expected_instrument_codes for market in context.markets
        }
        monkeypatch.setattr(
            semantics,
            "build_historical_provider_registry",
            lambda **_: _FakeRegistry(
                {
                    "TPE": _FakeRegistration(
                        "TWSE_OFFICIAL_DAILY",
                        _FakeAdapter(version="twse-official-daily.v2", codes=expected["TPE"]),
                    ),
                    "TWO": _FakeRegistration(
                        "TPEX_OFFICIAL_DAILY",
                        _FakeAdapter(version="tpex-official-daily.v2", codes=expected["TWO"]),
                    ),
                }
            ),
        )
        before = _table_counts(postgres_engine)
        with Session(postgres_engine, expire_on_commit=False) as session:
            result = semantics.run_market_semantics_check(
                session,
                target_date=RUN_DATE,
                reference_version="tw-reference-v1",
            )
        after = _table_counts(postgres_engine)

        assert result["status"] == "PASS"
        assert result["productionWriteSet"] == []
        assert before == after
        assert result["markets"]["TPE"]["expectedEligibleCount"] == 313
        assert result["markets"]["TWO"]["expectedEligibleCount"] == 193
    finally:
        _cleanup(postgres_engine)
