from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from topicpilot_api.corporate_action_authority import corporate_action_authorities_for
from topicpilot_api.market_data.availability import MarketAvailability
from topicpilot_api.trading_status_authority import (
    AuthorityClass,
    ManualTradingStatusOverride,
    ResolutionState,
    TradingStatusAuthorityError,
    TradingStatusAuthorityRecord,
    authority_from_official_daily_result,
    normalize_source_status,
    resolve_effective_trading_status,
    resolve_missing_statuses_with_budget,
)

TRADE_DATE = date(2026, 9, 30)


def _record(
    status: str,
    *,
    source: str = "TWSE_OFFICIAL_DAILY",
    reference: str | None = None,
    effective_from: date = TRADE_DATE,
    effective_to: date | None = TRADE_DATE,
    superseded_by: str | None = None,
) -> TradingStatusAuthorityRecord:
    return TradingStatusAuthorityRecord(
        status_code=status,
        effective_from=effective_from,
        effective_to=effective_to,
        source=source,
        source_reference=reference or f"{source}:{status}",
        reason_code=status,
        superseded_by=superseded_by,
    )


def _manual(status: str, *, expires_at: date | None = None) -> ManualTradingStatusOverride:
    return ManualTradingStatusOverride(
        status_code=status,
        effective_from=TRADE_DATE,
        effective_to=TRADE_DATE,
        source="OPERATOR_GOVERNED_OVERRIDE",
        source_reference="operator-ticket-024",
        reason_code="operator-confirmed-status",
        operator_id="operator-1",
        expires_at=expires_at,
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("SUSPENDED", "SUSPENDED"),
        ("NO_TRADE", "NO_TRADE"),
        ("EXCHANGE_CONFIRMED_NO_DATA", "EXCHANGE_CONFIRMED_NO_DATA"),
        ("HALTED", "HALTED"),
        ("DELISTED", "DELISTED"),
        ("TERMINATED", "TERMINATED"),
    ],
)
def test_official_no_price_states_are_typed_and_non_blocking(status: str, expected: str) -> None:
    result = resolve_effective_trading_status(
        SimpleNamespace(instrument_code="2330"),
        TRADE_DATE,
        official_authority=(_record(status),),
    )

    assert result.status == expected
    assert result.resolution_state == ResolutionState.RESOLVED.value
    assert result.is_legitimate_unavailable is True
    assert result.blocks_publication is False


def test_normal_price_is_available_without_status_lookup() -> None:
    result = resolve_effective_trading_status(
        object(), TRADE_DATE, same_session_close=Decimal("1200")
    )

    assert result.status == "AVAILABLE"
    assert result.reason_code == "VALID_SAME_SESSION_CLOSE"
    assert result.authority_class == AuthorityClass.PRICE_SESSION.value
    assert result.blocks_publication is False


def test_same_session_close_precedes_temporary_halt_and_preserves_event() -> None:
    result = resolve_effective_trading_status(
        object(),
        TRADE_DATE,
        same_session_close=Decimal("100"),
        official_authority=(_record("HALTED"),),
    )

    assert result.status == "AVAILABLE"
    assert result.preserved_event_status == "HALTED"
    assert result.preserved_event_source == "TWSE_OFFICIAL_DAILY"


def test_missing_price_without_authority_is_not_a_status_inference() -> None:
    result = resolve_effective_trading_status(object(), TRADE_DATE)

    assert result.status == MarketAvailability.MISSING_MARKET_DATA.value
    assert result.reason_code == "MISSING_MARKET_DATA"
    assert result.resolution_state == ResolutionState.UNRESOLVED.value
    assert result.blocks_publication is True


def test_official_available_without_price_remains_missing_data() -> None:
    result = resolve_effective_trading_status(
        object(), TRADE_DATE, official_authority=(_record("AVAILABLE"),)
    )

    assert result.status == "MISSING_MARKET_DATA"
    assert result.reason_code == "OFFICIAL_STATUS_EXPECTS_PRICE"
    assert result.blocks_publication is True


def test_provider_failure_is_distinct_from_missing_authority() -> None:
    result = resolve_effective_trading_status(object(), TRADE_DATE, provider_failure=True)

    assert result.status == "PROVIDER_ERROR"
    assert result.resolution_state == ResolutionState.PROVIDER_FAILURE.value
    assert result.reason_code == "PROVIDER_ERROR"


def test_manual_override_requires_governed_metadata_and_is_used_without_official() -> None:
    result = resolve_effective_trading_status(
        object(), TRADE_DATE, manual_overrides=(_manual("SUSPENDED"),)
    )

    assert result.status == "SUSPENDED"
    assert result.is_manual_override is True
    assert result.authority_class == AuthorityClass.MANUAL_GOVERNED.value
    assert result.is_legitimate_unavailable is True

    with pytest.raises(TradingStatusAuthorityError, match="MISSING_OVERRIDE_REASON"):
        ManualTradingStatusOverride(
            status_code="SUSPENDED",
            effective_from=TRADE_DATE,
            effective_to=TRADE_DATE,
            source="operator",
            source_reference="ticket",
            operator_id="operator-1",
        )


def test_official_authority_supersedes_manual_and_expired_override_is_ignored() -> None:
    manual = _manual("SUSPENDED", expires_at=date(2026, 9, 29))
    expired = resolve_effective_trading_status(object(), TRADE_DATE, manual_overrides=(manual,))
    assert expired.status == "MISSING_MARKET_DATA"

    official = resolve_effective_trading_status(
        object(),
        TRADE_DATE,
        official_authority=(_record("NO_TRADE"),),
        manual_overrides=(_manual("SUSPENDED"),),
    )
    assert official.status == "NO_TRADE"
    assert official.is_manual_override is False


def test_effective_date_and_supersession_boundaries_are_deterministic() -> None:
    prior = _record(
        "SUSPENDED",
        effective_from=date(2026, 9, 29),
        effective_to=date(2026, 9, 29),
        reference="prior",
    )
    current = _record(
        "NO_TRADE",
        reference="current",
        superseded_by=None,
    )
    assert (
        resolve_effective_trading_status(
            object(), TRADE_DATE, official_authority=(prior, current)
        ).status
        == "NO_TRADE"
    )
    assert (
        resolve_effective_trading_status(
            object(), date(2026, 9, 29), official_authority=(prior, current)
        ).status
        == "SUSPENDED"
    )

    superseded = _record("SUSPENDED", reference="old", superseded_by="new")
    assert (
        resolve_effective_trading_status(
            object(), TRADE_DATE, official_authority=(superseded, current)
        ).status
        == "NO_TRADE"
    )


def test_duplicate_official_delivery_is_idempotent() -> None:
    item = _record("NO_TRADE", reference="same-event")
    result = resolve_effective_trading_status(object(), TRADE_DATE, official_authority=(item, item))
    assert result.status == "NO_TRADE"
    assert result.source_reference == "same-event"


def test_conflicting_official_events_fail_closed_as_unknown() -> None:
    result = resolve_effective_trading_status(
        object(),
        TRADE_DATE,
        official_authority=(_record("NO_TRADE", reference="a"), _record("HALTED", reference="b")),
    )
    assert result.status == "UNKNOWN"
    assert result.reason_code == "AMBIGUOUS_AUTHORITY"
    assert result.blocks_publication is True


def test_unknown_source_value_does_not_get_fuzzy_mapped() -> None:
    assert normalize_source_status("停牌疑似", source="TWSE_OFFICIAL_DAILY") == "UNKNOWN"
    result = authority_from_official_daily_result(
        SimpleNamespace(
            source_code="TWSE_OFFICIAL_DAILY",
            status_explicit=True,
            instrument_status="停牌疑似",
            instrument_code="2330",
            status_reason=None,
            retrieved_at=None,
        ),
        trading_date=TRADE_DATE,
    )
    assert result is not None
    assert result.status_code == "UNKNOWN"


def test_unsupported_market_source_fails_closed() -> None:
    with pytest.raises(TradingStatusAuthorityError, match="UNSUPPORTED_STATUS_SOURCE"):
        authority_from_official_daily_result(
            SimpleNamespace(source_code="NEWS", status_explicit=True),
            trading_date=TRADE_DATE,
        )


def test_tpe_and_two_source_authority_remain_independent() -> None:
    tpe = _record("SUSPENDED", source="TWSE_OFFICIAL_DAILY", reference="tpe")
    two = _record("NO_TRADE", source="TPEX_OFFICIAL_DAILY", reference="two")
    assert (
        resolve_effective_trading_status(object(), TRADE_DATE, official_authority=(tpe,)).status
        == "SUSPENDED"
    )
    assert (
        resolve_effective_trading_status(object(), TRADE_DATE, official_authority=(two,)).status
        == "NO_TRADE"
    )


@pytest.mark.parametrize(
    "trading_date",
    [date(2026, 9, 23), date(2026, 9, 30), date(2026, 10, 3)],
)
def test_twse_reduction_authority_resolves_2601_as_suspended(trading_date: date) -> None:
    authority = tuple(
        item.to_trading_status_record()
        for item in corporate_action_authorities_for(
            symbol="2601", market="TPE", trading_date=trading_date
        )
    )

    result = resolve_effective_trading_status(object(), trading_date, official_authority=authority)

    assert result.status == "SUSPENDED"
    assert result.reason_code == "CAPITAL_REDUCTION_TRADING_SUSPENSION"
    assert result.authority_source == "TWSE_OFFICIAL_REDUCTION"
    assert result.authority_class == AuthorityClass.CORPORATE_ACTION.value
    assert result.blocks_publication is False


def test_reduction_authority_does_not_infer_available_after_resume_date() -> None:
    authority = tuple(
        item.to_trading_status_record()
        for item in corporate_action_authorities_for(
            symbol="2601", market="TPE", trading_date=date(2026, 10, 5)
        )
    )

    result = resolve_effective_trading_status(
        object(), date(2026, 10, 5), official_authority=authority
    )

    assert result.status == "MISSING_MARKET_DATA"
    assert result.blocks_publication is True


def test_same_session_close_precedes_reduction_authority_without_discarding_event() -> None:
    authority = tuple(
        item.to_trading_status_record()
        for item in corporate_action_authorities_for(
            symbol="2601", market="TPE", trading_date=date(2026, 9, 30)
        )
    )

    result = resolve_effective_trading_status(
        object(), date(2026, 9, 30), same_session_close=5.91, official_authority=authority
    )

    assert result.status == "AVAILABLE"
    assert result.preserved_event_status == "SUSPENDED"
    assert result.preserved_event_source == "TWSE_OFFICIAL_REDUCTION"


def test_bounded_resolution_retries_until_authority_arrives() -> None:
    missing = resolve_effective_trading_status(object(), TRADE_DATE)
    hit = resolve_effective_trading_status(
        object(), TRADE_DATE, official_authority=(_record("SUSPENDED"),)
    )
    responses = iter(((missing,), (hit,)))
    now = [0.0]
    sleeps: list[float] = []

    result = resolve_missing_statuses_with_budget(
        lambda: next(responses),
        candidate_count=1,
        max_attempts=3,
        max_total_wait_seconds=90,
        backoff_seconds=30,
        clock=lambda: now[0],
        sleep=lambda seconds: (sleeps.append(seconds), now.__setitem__(0, now[0] + seconds)),
    )

    assert result.resolutions[0].status == "SUSPENDED"
    assert result.metrics.lookup_count == 2
    assert result.metrics.retry_count == 1
    assert result.metrics.legitimate_unavailable_count == 1
    assert sleeps == [30]


def test_bounded_resolution_stops_after_budget() -> None:
    missing = resolve_effective_trading_status(object(), TRADE_DATE)
    now = [0.0]
    result = resolve_missing_statuses_with_budget(
        lambda: (missing,),
        candidate_count=1,
        max_attempts=3,
        max_total_wait_seconds=90,
        backoff_seconds=30,
        clock=lambda: now[0],
        sleep=lambda seconds: now.__setitem__(0, now[0] + seconds),
    )

    assert result.metrics.lookup_count == 3
    assert result.metrics.retry_count == 2
    assert result.metrics.total_wait_seconds == 90
    assert result.metrics.unresolved_unavailable_count == 1


def test_empty_status_lookup_is_not_treated_as_resolved() -> None:
    result = resolve_missing_statuses_with_budget(
        lambda: (),
        candidate_count=1,
        max_attempts=1,
        max_total_wait_seconds=0,
        backoff_seconds=0,
    )

    assert len(result.resolutions) == 1
    assert result.resolutions[0].status == "MISSING_MARKET_DATA"
    assert result.resolutions[0].blocks_publication is True
    assert result.metrics.unresolved_unavailable_count == 1


def test_status_provider_failure_is_observable_and_fail_closed() -> None:
    result = resolve_missing_statuses_with_budget(
        lambda: (_ for _ in ()).throw(TradingStatusAuthorityError("bad payload")),
        candidate_count=2,
        max_attempts=1,
        max_total_wait_seconds=0,
        backoff_seconds=0,
    )

    assert len(result.resolutions) == 2
    assert all(item.status == "PROVIDER_ERROR" for item in result.resolutions)
    assert result.metrics.provider_failure_count == 1
    assert result.metrics.unresolved_unavailable_count == 2
