"""Shared validation for formal Topic daily calculation inputs.

Point-in-time membership remains intact when a member has no quote. Only
exchange-accounted no-trade facts and quote gaps explicitly accepted by the
daily-market reconciliation may be excluded from daily-return calculations.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from topicpilot_api.daily_market import MAX_TOLERATED_MISSING_QUOTES
from topicpilot_api.formal_eligibility import Dimension
from topicpilot_api.market_data.availability import LEGITIMATE_UNAVAILABLE_CODES
from topicpilot_api.previous_close_authority import (
    AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE,
)

DAILY_RETURN_EXCLUSION_POLICY_VERSION = "topic-daily-return-exclusion.v1"
DAILY_MARKET_RECONCILIATION_AUTHORITY = "DAILY_MARKET_RECONCILIATION"
TOLERATED_MISSING_QUOTE_REASON = "TOLERATED_MISSING_QUOTE"


def _daily_return_eligibility(fact: Any) -> Mapping[str, Any]:
    raw = getattr(fact, "raw_fact_payload", None) or {}
    dimensions = raw.get("dimensionEligibility") or {}
    value = dimensions.get(Dimension.DAILY_RETURN.value) or {}
    return value if isinstance(value, Mapping) else {}


def is_authorized_missing_quote(fact: Any) -> bool:
    """Whether a missing quote has explicit, date-bound tolerance evidence."""

    raw = getattr(fact, "raw_fact_payload", None) or {}
    exclusion = raw.get("calculationExclusion") or {}
    if not isinstance(exclusion, Mapping):
        return False
    tolerance_count = exclusion.get("toleratedMissingCount")
    tolerance_limit = exclusion.get("missingToleranceLimit")
    try:
        tolerance_count = int(tolerance_count)
        tolerance_limit = int(tolerance_limit)
    except (TypeError, ValueError):
        return False
    fact_date = getattr(fact, "observation_date", None) or getattr(fact, "trading_date", None)
    fact_date_text = fact_date.isoformat() if hasattr(fact_date, "isoformat") else None
    return bool(
        getattr(fact, "fact_state", None) == "UNKNOWN"
        and getattr(fact, "close", None) is None
        and getattr(fact, "change_pct", None) is None
        and getattr(fact, "price_observation_id", None) is None
        and exclusion.get("status") == "EXCLUDED_FROM_DAILY_TOPIC_CALCULATION"
        and exclusion.get("reasonCode") == TOLERATED_MISSING_QUOTE_REASON
        and exclusion.get("authority") == DAILY_MARKET_RECONCILIATION_AUTHORITY
        and exclusion.get("reconciliationReasonCode") in {"MISSING_MARKET_DATA", "UNKNOWN"}
        and exclusion.get("tradingDate") == raw.get("tradingDate")
        and exclusion.get("tradingDate") == fact_date_text
        and exclusion.get("market") == raw.get("marketCode")
        and exclusion.get("symbol") == raw.get("symbol")
        and 0 < tolerance_count <= tolerance_limit <= MAX_TOLERATED_MISSING_QUOTES
    )


def is_authorized_no_trade(fact: Any) -> bool:
    """Whether a null quote is backed by accepted exchange status evidence."""

    raw = getattr(fact, "raw_fact_payload", None) or {}
    status = raw.get("tradingStatus")
    return bool(
        getattr(fact, "fact_state", None) == "NO_TRADE"
        and getattr(fact, "close", None) is None
        and getattr(fact, "change_pct", None) is None
        and raw.get("tradingStatusObservationId")
        and status in LEGITIMATE_UNAVAILABLE_CODES
        and _daily_return_eligibility(fact).get("status") == "ACCOUNTED_UNAVAILABLE"
    )


def is_authorized_comparator_unavailable(fact: Any) -> bool:
    """Whether an observed close lacks only an authorized daily comparator."""

    daily_return = _daily_return_eligibility(fact)
    return bool(
        getattr(fact, "fact_state", None) == "OBSERVED"
        and getattr(fact, "change_pct", None) is None
        and daily_return.get("status") == "ACCOUNTED_UNAVAILABLE"
        and daily_return.get("reasonCode") == AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE
    )


def validate_formal_calculation_members(snapshot: Any, facts: Iterable[Any]) -> str | None:
    """Validate that every omitted daily input has an explicit authority."""

    fact_rows = tuple(facts)
    data_status = getattr(snapshot, "data_status", None)
    if data_status not in {"COMPLETE", "PARTIAL"}:
        return f"SNAPSHOT_DATA_STATUS_{data_status}"
    stock_count = int(getattr(snapshot, "stock_count", 0) or 0)
    if stock_count <= 0 or len(fact_rows) != stock_count:
        return "FORMAL_MEMBER_COUNT_MISMATCH"

    observed = sum(getattr(fact, "fact_state", None) == "OBSERVED" for fact in fact_rows)
    no_trade = sum(getattr(fact, "fact_state", None) == "NO_TRADE" for fact in fact_rows)
    unknown = sum(getattr(fact, "fact_state", None) == "UNKNOWN" for fact in fact_rows)
    if getattr(snapshot, "observed_stock_count", None) != observed:
        return "FORMAL_MEMBER_OBSERVED_COUNT_MISMATCH"
    if (
        getattr(snapshot, "no_trade_count", None) is not None
        and snapshot.no_trade_count != no_trade
    ):
        return "FORMAL_MEMBER_NO_TRADE_COUNT_MISMATCH"
    if getattr(snapshot, "unknown_count", None) is not None and snapshot.unknown_count != unknown:
        return "FORMAL_MEMBER_UNKNOWN_COUNT_MISMATCH"
    if unknown and data_status != "PARTIAL":
        return "SNAPSHOT_DATA_STATUS_UNKNOWN_COUNT_MISMATCH"
    if data_status == "PARTIAL" and not unknown:
        return "SNAPSHOT_DATA_STATUS_PARTIAL"

    for fact in fact_rows:
        state = getattr(fact, "fact_state", None)
        if state == "OBSERVED":
            continue
        if state == "NO_TRADE":
            if not is_authorized_no_trade(fact):
                return "FORMAL_MEMBER_OBSERVATION_UNAVAILABLE"
        elif state == "UNKNOWN":
            if not is_authorized_missing_quote(fact):
                return "FORMAL_MEMBER_OBSERVATION_UNAVAILABLE"
        else:
            return "FORMAL_MEMBER_OBSERVATION_UNAVAILABLE"
    return None


def excluded_member_counts(facts: Iterable[Any]) -> dict[str, int]:
    """Count PIT members omitted from the daily-return sample by authority."""

    rows = tuple(facts)
    return {
        "pointInTimeMemberCount": len(rows),
        "excludedNoTradeMemberCount": sum(is_authorized_no_trade(fact) for fact in rows),
        "excludedMissingQuoteMemberCount": sum(is_authorized_missing_quote(fact) for fact in rows),
        "excludedComparatorUnavailableMemberCount": sum(
            is_authorized_comparator_unavailable(fact) for fact in rows
        ),
    }


__all__ = [
    "DAILY_MARKET_RECONCILIATION_AUTHORITY",
    "DAILY_RETURN_EXCLUSION_POLICY_VERSION",
    "TOLERATED_MISSING_QUOTE_REASON",
    "excluded_member_counts",
    "is_authorized_comparator_unavailable",
    "is_authorized_missing_quote",
    "is_authorized_no_trade",
    "validate_formal_calculation_members",
]
