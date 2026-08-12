from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal

import pytest

from topicpilot_api.market_data.history import (
    HistoricalProviderError,
    YahooChartHistoricalProvider,
    probe_history_availability,
)


def _payload(*, missing_close: bool = False, duplicate: bool = False) -> bytes:
    timestamps = [1783296000, 1783382400, 1783468800]
    if duplicate:
        timestamps[2] = timestamps[1]
    close = [10.5, None if missing_close else 10.8, 11.0]
    return json.dumps(
        {
            "chart": {
                "result": [
                    {
                        "timestamp": timestamps,
                        "indicators": {
                            "quote": [
                                {
                                    "open": [10, 10.5, 10.8],
                                    "high": [11, 11, 11.2],
                                    "low": [9.8, 10.2, 10.5],
                                    "close": close,
                                    "volume": [100, 120, 130],
                                }
                            ]
                        },
                    }
                ]
            }
        }
    ).encode()


def _provider(payload: bytes, urls: list[str] | None = None) -> YahooChartHistoricalProvider:
    def transport(url: str, _timeout: float) -> bytes:
        if urls is not None:
            urls.append(url)
        return payload

    return YahooChartHistoricalProvider(
        transport=transport,
        clock=lambda: datetime(2026, 8, 10, 9, 0),
    )


def test_provider_maps_tpe_and_preserves_lineage_without_raw_payload():
    urls: list[str] = []
    result = _provider(_payload(), urls).fetch_daily("2330", "TPE")

    assert result.source_symbol == "2330.TW"
    assert result.source_code == "YAHOO_CHART_DAILY"
    assert result.adapter_version == "yahoo-chart-daily.v1"
    assert result.available_close_count == 3
    assert result.bars[0].close == Decimal("10.5")
    assert "2330.TW" in urls[0]
    assert "interval=1d" in urls[0]
    assert "range=1mo" in urls[0]


def test_provider_maps_two_and_missing_close_is_not_zero():
    result = _provider(_payload(missing_close=True)).fetch_daily("4979", "TWO")

    assert result.source_symbol == "4979.TWO"
    assert result.available_close_count == 2
    assert result.missing_close_count == 1
    assert result.bars[1].close is None
    assert result.bars[1].close != Decimal("0")


def test_probe_reports_insufficient_history_and_provider_failure_per_symbol():
    class StubProvider:
        source_code = "STUB"
        adapter_version = "stub.v1"

        def fetch_daily(self, instrument_code: str, market_code: str):
            if instrument_code == "FAIL":
                raise HistoricalProviderError("TIMEOUT", "test")
            return _provider(_payload(missing_close=True)).fetch_daily(instrument_code, market_code)

    results = probe_history_availability(
        StubProvider(), [("2330", "TPE"), ("FAIL", "TWO")], minimum_points=3
    )

    assert [item.status for item in results] == ["INSUFFICIENT_HISTORY", "PROVIDER_ERROR"]
    assert results[0].missing_close_count == 1
    assert results[1].error_code == "TIMEOUT"
    assert results[1].to_dict()["availableCloseCount"] == 0


def test_provider_rejects_duplicate_dates_and_invalid_ohlc():
    with pytest.raises(HistoricalProviderError, match="DUPLICATE_DATE"):
        _provider(_payload(duplicate=True)).fetch_daily("2330", "TPE")

    payload = json.loads(_payload())
    payload["chart"]["result"][0]["indicators"]["quote"][0]["low"][0] = 12
    with pytest.raises(HistoricalProviderError, match="INVALID_OHLC"):
        _provider(json.dumps(payload).encode()).fetch_daily("2330", "TPE")


def test_provider_failure_is_machine_readable_and_no_network_fallback_is_used():
    def transport(_url: str, _timeout: float) -> bytes:
        raise TimeoutError("network unavailable")

    provider = YahooChartHistoricalProvider(transport=transport)
    results = probe_history_availability(provider, [("2330", "TPE")])

    assert results[0].status == "PROVIDER_ERROR"
    assert results[0].error_code == "PROVIDER_REQUEST_FAILED"
    assert results[0].available_close_count == 0
