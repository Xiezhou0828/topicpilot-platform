import json
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from topicpilot_api.market_data.exchange import (
    TpexOfficialDailyProvider,
    TwseOfficialDailyProvider,
)
from topicpilot_api.market_data.history import (
    HistoricalBar,
    HistoricalFetchResult,
    HistoricalProviderError,
)
from topicpilot_api.normalizer import (
    HistoricalDailyBarNormalizer,
    InputEnvelope,
    MappingPolicy,
    ReferenceContext,
)


def test_official_empty_exchange_response_is_confirmed_no_data():
    provider = TwseOfficialDailyProvider(
        start_date=date(2026, 8, 7),
        end_date=date(2026, 8, 7),
        transport=lambda _url, _timeout: b'{"stat":"OK","data":[]}',
        clock=lambda: datetime(2026, 8, 7, 7, tzinfo=UTC),
    )

    result = provider.fetch_daily("2330", "TPE")

    assert result.bars == ()
    assert result.instrument_status == "EXCHANGE_CONFIRMED_NO_DATA"
    assert result.status_explicit is True
    assert result.status_reason


def test_twse_market_batch_fetches_once_and_resolves_multiple_symbols():
    urls: list[str] = []
    payload = json.dumps(
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
                        ["2330", "TSMC", "1,000", "10", "100,000", "100", "105", "99", "104"],
                        ["2317", "Hon Hai", "2,000", "20", "200,000", "200", "205", "199", "204"],
                    ],
                }
            ],
        }
    ).encode()

    provider = TwseOfficialDailyProvider(
        start_date=date(2026, 8, 7),
        end_date=date(2026, 8, 7),
        market_batch=True,
        transport=lambda url, _timeout: (urls.append(url), payload)[1],
    )

    first = provider.fetch_daily("2330", "TPE")
    second = provider.fetch_daily("2317", "TPE")

    assert len(urls) == 1
    assert "MI_INDEX" in urls[0]
    assert first.bars[0].close == Decimal("104")
    assert second.bars[0].close == Decimal("204")


def test_tpex_market_batch_fetches_once_and_resolves_multiple_symbols():
    urls: list[str] = []
    payload = json.dumps(
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
                        ["4979", "Example", "50", "+1", "49", "51", "48", "50", "3,000"],
                        ["6510", "Example2", "60", "+1", "59", "61", "58", "60", "4,000"],
                        ["6806", "No trade", " ---", "--- ", "---", "---", "---", "0.00", "0"],
                    ],
                }
            ],
        }
    ).encode()

    provider = TpexOfficialDailyProvider(
        start_date=date(2026, 8, 7),
        end_date=date(2026, 8, 7),
        market_batch=True,
        transport=lambda url, _timeout: (urls.append(url), payload)[1],
    )

    first = provider.fetch_daily("4979", "TWO")
    second = provider.fetch_daily("6510", "TWO")

    assert len(urls) == 1
    assert "dailyQuotes" in urls[0]
    assert first.bars[0].close == Decimal("50")
    assert first.bars[0].volume == Decimal("3000")
    assert second.bars[0].close == Decimal("60")
    missing = provider.fetch_daily("6806", "TWO")
    assert missing.bars[0].close is None


def test_market_batch_rejects_wrong_provider_date():
    payload = b'{"stat":"OK","date":"20260806","tables":[]}'
    provider = TwseOfficialDailyProvider(
        start_date=date(2026, 8, 7),
        end_date=date(2026, 8, 7),
        market_batch=True,
        transport=lambda _url, _timeout: payload,
    )

    with pytest.raises(HistoricalProviderError, match="PROVIDER_DATE_MISMATCH"):
        provider.fetch_daily("2330", "TPE")


def test_explicit_no_trade_normalizes_to_price_null_plus_status_evidence():
    now = datetime(2026, 8, 7, tzinfo=UTC)
    envelope = InputEnvelope(
        {
            "date": "2026-08-07",
            "open": None,
            "high": None,
            "low": None,
            "close": None,
            "volume": None,
            "instrument_status": "EXCHANGE_CONFIRMED_NO_DATA",
            "status_reason": "official exchange response contained no row",
        },
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
        now,
        now,
        now,
        "2026-08-07",
    )
    reference = ReferenceContext(
        "tw-reference-v1",
        "Asia/Taipei",
        "REGULAR",
        "TW_MARKET",
        "TWD",
        2,
        statuses=frozenset({"OPEN"}),
    )

    result = HistoricalDailyBarNormalizer()(
        envelope,
        reference,
        MappingPolicy(mapping_policy_version="historical-daily-mapping-v1"),
    )

    assert [item.family_code for item in result.candidates] == ["PRICE", "TRADING_STATUS"]
    price, status = result.candidates
    assert price.quality_state == "INCOMPLETE"
    assert price.values["close"] is None
    assert price.values["close"] != Decimal("0")
    assert status.quality_state == "ACCEPTED"
    assert status.values["status_code"] == "EXCHANGE_CONFIRMED_NO_DATA"
    assert status.values["status_context"]["coverageMeaning"] == "APPROVED_NO_TRADE"


def test_unknown_missing_bar_does_not_become_approved_no_trade():
    now = datetime(2026, 8, 7, tzinfo=UTC)
    result = HistoricalFetchResult(
        "2330",
        "TPE",
        "2330",
        "TWSE_OFFICIAL_DAILY",
        "twse-official-daily.v1",
        now,
        (
            HistoricalBar(
                date(2026, 8, 7),
                None,
                None,
                None,
                None,
                None,
            ),
        ),
        1,
    )

    assert result.instrument_status == "AVAILABLE"
    assert result.covered_no_trade is False
