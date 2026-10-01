from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from topicpilot_api.daily_market import reconcile_daily_market
from topicpilot_api.market_data.availability import classify_availability
from topicpilot_api.market_data.corporate_action_authority import (
    CorporateActionAuthorityRecord,
    authority_by_identity,
    load_official_corporate_action_snapshot,
)
from topicpilot_api.trading_status_authority import (
    AuthorityClass,
    TradingStatusAuthorityRecord,
    resolve_effective_trading_status,
)

TARGET = next(
    item
    for item in load_official_corporate_action_snapshot()
    if item.instrument_code == "2601"
)
TARGET_STATUS = TARGET.to_trading_status_record()


def _resolution(trading_date: date, *, close: Decimal | None = None):
    return resolve_effective_trading_status(
        SimpleNamespace(instrument_code="2601", market_code="TPE"),
        trading_date,
        same_session_close=close,
        corporate_action_authority=(TARGET_STATUS,),
    )


@pytest.mark.parametrize(
    ("trading_date", "close", "expected_status"),
    [
        (date(2026, 9, 22), Decimal("12.0"), "AVAILABLE"),
        (date(2026, 9, 23), None, "SUSPENDED"),
        (date(2026, 9, 30), None, "SUSPENDED"),
        (date(2026, 10, 3), None, "SUSPENDED"),
        (date(2026, 10, 5), Decimal("12.5"), "AVAILABLE"),
    ],
)
def test_2601_capital_reduction_authority_is_effective_dated(
    trading_date: date, close: Decimal | None, expected_status: str
) -> None:
    result = _resolution(trading_date, close=close)

    assert result.status == expected_status
    if expected_status == "SUSPENDED":
        assert result.reason_code == "CAPITAL_REDUCTION_TRADING_SUSPENSION"
        assert result.effective_from == date(2026, 9, 23)
        assert result.effective_to == date(2026, 10, 3)
        assert result.resume_date == date(2026, 10, 5)
        assert result.is_legitimate_unavailable is True
        assert result.blocks_publication is False


def test_corporate_action_authority_overrides_a_same_session_close_without_mutating_price():
    result = _resolution(date(2026, 9, 30), close=Decimal("99.0"))

    assert result.status == "SUSPENDED"
    assert result.reason_code == "CAPITAL_REDUCTION_TRADING_SUSPENSION"


def test_corporate_action_authority_precedes_conflicting_lifecycle_status():
    lifecycle = TradingStatusAuthorityRecord(
        status_code="DELISTED",
        effective_from=date(2026, 9, 30),
        effective_to=date(2026, 9, 30),
        source="REFERENCE_INSTRUMENT_LIFECYCLE",
        source_reference="lifecycle-conflict",
        authority_class=AuthorityClass.REFERENCE_LIFECYCLE.value,
    )
    result = resolve_effective_trading_status(
        object(),
        date(2026, 9, 30),
        official_authority=(lifecycle,),
        corporate_action_authority=(TARGET_STATUS,),
    )

    assert result.status == "SUSPENDED"
    assert result.authority_class == AuthorityClass.OFFICIAL_CORPORATE_ACTION.value
    assert result.reason_code == "CAPITAL_REDUCTION_TRADING_SUSPENSION"


def test_corporate_action_adapter_is_generic_and_not_a_2601_code_path():
    other = CorporateActionAuthorityRecord(
        market_code="TPE",
        instrument_code="9999",
        event_type="CAPITAL_REDUCTION",
        effective_from=date(2026, 9, 23),
        effective_to=date(2026, 9, 30),
        resume_date=date(2026, 10, 1),
        source="TWSE_OFFICIAL_CORPORATE_ACTION",
        source_reference="fixture-9999-capital-reduction",
        source_url="https://mops.twse.com.tw/mops/web/t05st01",
    )
    result = resolve_effective_trading_status(
        object(),
        date(2026, 9, 30),
        corporate_action_authority=(other.to_trading_status_record(),),
    )

    assert result.status == "SUSPENDED"
    assert result.reason_code == "CAPITAL_REDUCTION_TRADING_SUSPENSION"


def test_official_no_trade_available_missing_unknown_and_provider_error_are_distinct():
    no_trade = TradingStatusAuthorityRecord(
        status_code="NO_TRADE",
        effective_from=date(2026, 9, 30),
        effective_to=date(2026, 9, 30),
        source="TWSE_OFFICIAL_DAILY",
        source_reference="official-no-trade",
    )
    assert (
        resolve_effective_trading_status(
            object(), date(2026, 9, 30), official_authority=(no_trade,)
        ).status
        == "NO_TRADE"
    )
    assert resolve_effective_trading_status(object(), date(2026, 9, 30), official_authority=(
        TradingStatusAuthorityRecord(
            status_code="AVAILABLE",
            effective_from=date(2026, 9, 30),
            effective_to=date(2026, 9, 30),
            source="TWSE_OFFICIAL_DAILY",
            source_reference="official-available",
        ),
    )).reason_code == "OFFICIAL_STATUS_EXPECTS_PRICE"
    assert (
        resolve_effective_trading_status(object(), date(2026, 9, 30)).status
        == "MISSING_MARKET_DATA"
    )
    assert (
        resolve_effective_trading_status(
            object(), date(2026, 9, 30), provider_failure=True
        ).status
        == "PROVIDER_ERROR"
    )
    assert classify_availability(
        status_code="UNKNOWN", reason_code="DATE_MISMATCH"
    ).blocks_formal_publication is True


def test_conflicting_corporate_action_authority_fails_closed():
    conflict = TradingStatusAuthorityRecord(
        status_code="NO_TRADE",
        effective_from=date(2026, 9, 23),
        effective_to=date(2026, 10, 3),
        source="TWSE_OFFICIAL_CORPORATE_ACTION",
        source_reference="conflicting-corporate-action",
        authority_class=AuthorityClass.OFFICIAL_CORPORATE_ACTION.value,
    )
    result = resolve_effective_trading_status(
        object(),
        date(2026, 9, 30),
        corporate_action_authority=(TARGET_STATUS, conflict),
    )

    assert result.status == "UNKNOWN"
    assert result.reason_code == "CONFLICTING_CORPORATE_ACTION_AUTHORITY"
    assert result.blocks_publication is True


def test_lifecycle_only_authority_remains_distinct_from_corporate_action_authority():
    lifecycle = TradingStatusAuthorityRecord(
        status_code="SUSPENDED",
        effective_from=date(2026, 9, 30),
        effective_to=date(2026, 9, 30),
        source="REFERENCE_INSTRUMENT_LIFECYCLE",
        source_reference="lifecycle-only",
        authority_class=AuthorityClass.REFERENCE_LIFECYCLE.value,
    )
    result = resolve_effective_trading_status(
        object(), date(2026, 9, 30), official_authority=(lifecycle,)
    )

    assert result.status == "SUSPENDED"
    assert result.authority_class == AuthorityClass.REFERENCE_LIFECYCLE.value
    assert result.reason_code == "SUSPENDED"


def test_reconciliation_consumes_resolved_corporate_action_and_keeps_price_null(monkeypatch):
    row = {
        "instrument_id": uuid4(),
        "symbol": "2601",
        "name": "益航",
        "market": "TPE",
        "close": None,
        "observed_at": None,
        "status_observation_id": None,
        "status_source": None,
        "status_code": None,
        "status_reason": None,
        "source_code": "TWSE_OFFICIAL_DAILY",
        "last_valid_price_date": date(2026, 9, 29),
        "last_valid_close": Decimal("10.0"),
        "formal_topic_membership_count": 1,
        "affected_topic_slugs": ["shipping"],
    }

    class FakeSession:
        def scalar(self, *_args, **_kwargs):
            return 0

    monkeypatch.setattr(
        "topicpilot_api.daily_market.read_daily_market_rows",
        lambda *_args, **_kwargs: [row],
    )
    result = reconcile_daily_market(
        FakeSession(),
        date(2026, 9, 30),
        corporate_action_authority_by_identity=authority_by_identity((TARGET,)),
    )

    item = result.unavailable_instruments[0]
    assert result.downstream_ready is True
    assert result.expected_count == 1
    assert result.priced_count == 0
    assert result.covered_count == 1
    assert item.status == "SUSPENDED"
    assert item.reason_code == "CAPITAL_REDUCTION_TRADING_SUSPENSION"
    assert item.last_valid_close == Decimal("10.0")
