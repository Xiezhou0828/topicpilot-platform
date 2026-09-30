from datetime import date
from decimal import Decimal

import pytest

from topicpilot_api.daily_market import (
    UnavailableInstrument,
    assess_daily_coverage,
    build_unavailable_instruments,
)
from topicpilot_api.market_data.availability import (
    LEGITIMATE_UNAVAILABLE_CODES,
    MarketAvailability,
    classify_availability,
)


@pytest.mark.parametrize("status", sorted(LEGITIMATE_UNAVAILABLE_CODES))
def test_exchange_confirmed_unavailable_status_is_non_blocking(status: str) -> None:
    decision = classify_availability(
        status_code=status,
        reason_code=status,
        has_canonical_status_evidence=True,
    )

    assert decision.is_legitimate_unavailable is True
    assert decision.blocks_formal_publication is False


def test_legitimate_status_without_canonical_evidence_is_unknown_and_blocking() -> None:
    decision = classify_availability(
        status_code=MarketAvailability.SUSPENDED.value,
        reason_code=MarketAvailability.SUSPENDED.value,
    )

    assert decision.classification == "UNKNOWN"
    assert decision.blocks_formal_publication is True


@pytest.mark.parametrize("code", ["MISSING_MARKET_DATA", "PROVIDER_ERROR", "DATE_MISMATCH"])
def test_pipeline_failure_is_fail_closed(code: str) -> None:
    decision = classify_availability(status_code="UNKNOWN", reason_code=code)

    assert decision.classification == "DATA_PIPELINE_FAILURE"
    assert decision.blocks_formal_publication is True


def test_unavailable_read_model_is_typed_and_never_zero_filled() -> None:
    items = build_unavailable_instruments(
        [
            {
                "symbol": "2330",
                "name": "台積電",
                "market": "TPE",
                "close": None,
                "status_code": "NO_TRADE",
                "status_reason": "NO_TRADE",
                "status_observation_id": "status-1",
                "status_source": "TWSE_OFFICIAL_DAILY",
                "last_valid_price_date": date(2026, 9, 29),
                "last_valid_close": Decimal("1200"),
                "formal_topic_membership_count": 2,
                "affected_topic_slugs": ["ai", "semiconductor"],
            },
            {
                "symbol": "9999",
                "name": "未知",
                "market": "TPE",
                "close": None,
                "status_code": None,
                "status_observation_id": None,
                "last_valid_price_date": None,
                "last_valid_close": None,
                "formal_topic_membership_count": 0,
                "affected_topic_slugs": [],
            },
        ],
        trade_date=date(2026, 9, 30),
    )

    assert len(items) == 2
    assert items[0].is_legitimate_unavailable is True
    assert items[0].blocks_formal_publication is False
    assert items[0].last_valid_close == Decimal("1200")
    assert items[1].reason_code == "MISSING_MARKET_DATA"
    assert items[1].blocks_formal_publication is True
    assert items[1].last_valid_close is None
    assert items[0].to_dict()["lastValidClose"] == Decimal("1200")


def test_legitimate_unavailable_does_not_block_unrelated_formal_publication() -> None:
    unavailable = UnavailableInstrument(
        trading_date=date(2026, 9, 30),
        symbol="2330",
        name="台積電",
        market="TPE",
        status="SUSPENDED",
        reason_code="SUSPENDED",
        source="TWSE_OFFICIAL_DAILY",
        last_valid_price_date=date(2026, 9, 29),
        last_valid_close=Decimal("1200"),
        formal_topic_membership_count=1,
        affected_topic_slugs=("semiconductor",),
        is_legitimate_unavailable=True,
        blocks_formal_publication=False,
    )
    result = assess_daily_coverage(
        trade_date=date(2026, 9, 30),
        expected_by_market={"TPE": 2},
        observed_by_market={"TPE": 2},
        priced_by_market={"TPE": 1},
        covered_by_market={"TPE": 2},
        unavailable_instruments=(unavailable,),
    )

    assert result.downstream_ready is True
    assert result.pipeline_failure_count == 0
    assert result.unavailable_instruments[0].affected_topic_slugs == ("semiconductor",)
