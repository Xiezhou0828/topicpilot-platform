from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from topicpilot_api.market_data.exchange import TwseOfficialDailyProvider
from topicpilot_api.market_data.history import HistoricalBar, HistoricalFetchResult
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
