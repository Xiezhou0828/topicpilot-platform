from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from topicpilot_api.live.history_probe import probe_historical_window
from topicpilot_api.market_data.history import (
    HistoricalBar,
    HistoricalFetchResult,
    HistoricalProviderError,
)


class StubProvider:
    source_code = "STUB"
    adapter_version = "stub.v1"

    def fetch_daily(self, instrument_code, market_code):
        if instrument_code == "FAIL":
            raise HistoricalProviderError("TIMEOUT", "test")
        return HistoricalFetchResult(
            instrument_code=instrument_code,
            market_code=market_code,
            source_symbol=f"{instrument_code}@{market_code}",
            source_code=self.source_code,
            adapter_version=self.adapter_version,
            retrieved_at=datetime(2026, 8, 10, tzinfo=UTC),
            bars=(
                HistoricalBar(
                    date(2026, 7, 27),
                    Decimal("100"),
                    Decimal("101"),
                    Decimal("99"),
                    Decimal("100"),
                    Decimal("1000"),
                ),
                HistoricalBar(
                    date(2026, 7, 28), Decimal("100"), Decimal("102"), Decimal("99"), None, None
                ),
            ),
            raw_point_count=2,
        )


def test_historical_window_probe_reports_available_data_and_missing_values_separately():
    results = probe_historical_window(
        StubProvider(),
        [("2330", "TPE"), ("FAIL", "TPE")],
        requested_from=date(2026, 7, 27),
        requested_to=date(2026, 8, 9),
    )

    assert results[0].status == "AVAILABLE"
    assert results[0].returned_point_count == 2
    assert results[0].available_close_count == 1
    assert results[0].missing_close_count == 1
    assert results[0].to_dict()["dateFrom"] == "2026-07-27"
    assert results[1].status == "PROVIDER_ERROR"
    assert results[1].error_code == "TIMEOUT"
