from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from topicpilot_api.market_data import TaishinTechnicalAnalysisProvider
from topicpilot_api.market_data.history import HistoricalProviderError
from topicpilot_api.normalizer import (
    HistoricalDailyBarNormalizer,
    InputEnvelope,
    MappingPolicy,
    ReferenceContext,
)


class FakeTaishinClient:
    def __init__(self, rows):
        self.rows = rows

    def fetch_daily_bars(self, instrument_code: str, market_code: str):
        assert instrument_code == "2330"
        assert market_code == "TPE"
        return self.rows


def _provider(rows):
    return TaishinTechnicalAnalysisProvider(
        client=FakeTaishinClient(rows),
        start_date=date(2026, 7, 1),
        clock=lambda: datetime(2026, 8, 10, 9, tzinfo=UTC),
    )


def test_taishin_provider_maps_vendor_fields_and_sorts_without_credentials():
    rows = [
        SimpleNamespace(
            KBar=SimpleNamespace(
                Date="20260807",
                OPrice="100.0",
                HPrice="103.0",
                LPrice="99.0",
                CPrice="102.0",
                Volume="1200",
            )
        ),
        {
            "Date": "20260806",
            "OPrice": 98,
            "HPrice": 101,
            "LPrice": 97,
            "CPrice": 100,
            "Volume": 900,
        },
    ]

    result = _provider(rows).fetch_daily("2330", "TPE")

    assert result.source_code == "TAISHIN_TECH_ANALYSIS"
    assert result.adapter_version == "taishin-tech-analysis.v1"
    assert result.source_symbol == "2330@TPE"
    assert [bar.trading_date.isoformat() for bar in result.bars] == ["2026-08-06", "2026-08-07"]
    assert result.bars[0].close == Decimal("100")
    assert result.bars[0].volume == Decimal("900")


def test_taishin_provider_preserves_null_and_reports_duplicate_date():
    result = _provider(
        [
            {
                "Date": "20260807",
                "OPrice": 100,
                "HPrice": 103,
                "LPrice": 99,
                "CPrice": None,
                "Volume": None,
            }
        ]
    ).fetch_daily("2330", "TPE")
    assert result.bars[0].close is None
    assert result.bars[0].volume is None

    with pytest.raises(HistoricalProviderError, match="DUPLICATE_DATE"):
        _provider(
            [
                {"Date": "20260807", "OPrice": 1, "HPrice": 1, "LPrice": 1, "CPrice": 1},
                {"Date": "20260807", "OPrice": 1, "HPrice": 1, "LPrice": 1, "CPrice": 1},
            ]
        ).fetch_daily("2330", "TPE")


def _envelope(payload: dict):
    now = datetime(2026, 8, 7, tzinfo=UTC)
    return InputEnvelope(payload, uuid4(), uuid4(), uuid4(), uuid4(), now, now, now, "2026-08-07")


def _reference():
    return ReferenceContext(
        "tw-reference-v1",
        "Asia/Taipei",
        "REGULAR",
        "TW_MARKET",
        "TWD",
        2,
        statuses=frozenset({"OPEN"}),
    )


def test_historical_normalizer_is_nullable_and_never_zero_fills():
    mapper = HistoricalDailyBarNormalizer()
    result = mapper(
        _envelope(
            {
                "date": "2026-08-07",
                "open": "100",
                "high": "103",
                "low": "99",
                "close": None,
                "volume": None,
            }
        ),
        _reference(),
        MappingPolicy(mapping_policy_version="historical-daily-mapping-v1"),
    )

    price = result.candidates[0]
    assert price.quality_state == "INCOMPLETE"
    assert price.values["close"] is None
    assert price.values["close"] != Decimal("0")
    assert len(result.candidates) == 1


def test_historical_normalizer_rejects_invalid_ohlc():
    result = HistoricalDailyBarNormalizer()(
        _envelope({"open": "100", "high": "90", "low": "80", "close": "85", "volume": "1"}),
        _reference(),
        MappingPolicy(mapping_policy_version="historical-daily-mapping-v1"),
    )
    assert result.candidates == ()
    assert result.failures[0].code == "INVALID_OHLC"
