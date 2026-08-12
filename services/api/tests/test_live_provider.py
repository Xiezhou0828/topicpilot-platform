from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from topicpilot_api.live.contracts import LiveProviderError
from topicpilot_api.market_data import TaishinIntradayProvider


class FakeIntradayClient:
    def __init__(self, rows):
        self.rows = rows

    def fetch_intraday_bars(self, instrument_code, market_code, interval, session_date):
        assert (instrument_code, market_code, interval, session_date) == (
            "2330",
            "TPE",
            "5m",
            date(2026, 8, 7),
        )
        return self.rows


def test_taishin_intraday_provider_maps_vendor_kbar_to_taipei_timestamp():
    provider = TaishinIntradayProvider(
        client=FakeIntradayClient(
            [
                SimpleNamespace(
                    KBar=SimpleNamespace(
                        Date="20260807",
                        TimeSn="1316",
                        TimeSn_Dply="1320",
                        OPrice="100",
                        HPrice="103",
                        LPrice="99",
                        CPrice="102",
                        Quantity="1200",
                    )
                )
            ]
        ),
        clock=lambda: datetime(2026, 8, 7, 5, 22, tzinfo=UTC),
    )

    result = provider.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 7))

    assert result.source_code == "TAISHIN_TECH_ANALYSIS_INTRADAY"
    assert result.adapter_version == "taishin-tech-analysis-intraday.v1"
    assert result.latest is not None
    assert result.latest.observed_at == datetime(2026, 8, 7, 5, 20, tzinfo=UTC)
    assert result.latest.close == Decimal("102")
    assert result.latest.volume == Decimal("1200")


def test_taishin_intraday_provider_does_not_turn_missing_values_into_zero():
    provider = TaishinIntradayProvider(
        client=FakeIntradayClient(
            [
                {
                    "Date": "20260807",
                    "TimeSn_Dply": "1320",
                    "OPrice": None,
                    "HPrice": None,
                    "LPrice": None,
                    "CPrice": None,
                    "Volume": None,
                }
            ]
        ),
        clock=lambda: datetime(2026, 8, 7, 5, 22, tzinfo=UTC),
    )

    result = provider.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 7))

    assert result.latest is not None
    assert result.latest.close is None
    assert result.latest.volume is None
    assert result.latest.close != Decimal("0")


def test_taishin_intraday_provider_rejects_empty_provider_response():
    provider = TaishinIntradayProvider(
        client=FakeIntradayClient([]),
        clock=lambda: datetime(2026, 8, 7, 5, 22, tzinfo=UTC),
    )

    with pytest.raises(LiveProviderError, match="EMPTY_INTRADAY_DATA"):
        provider.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 7))
