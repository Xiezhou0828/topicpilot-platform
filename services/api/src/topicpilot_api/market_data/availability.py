"""Typed market-data availability policy.

The policy is deliberately evidence-driven.  A status code is a legitimate
unavailable state only when it came from the canonical trading-status
authority; an absent price without that evidence remains blocking.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MarketAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    NO_TRADE = "NO_TRADE"
    SUSPENDED = "SUSPENDED"
    EXCHANGE_CONFIRMED_NO_DATA = "EXCHANGE_CONFIRMED_NO_DATA"
    HALTED = "HALTED"
    DELISTED = "DELISTED"
    TERMINATED = "TERMINATED"
    MISSING_MARKET_DATA = "MISSING_MARKET_DATA"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    DATE_MISMATCH = "DATE_MISMATCH"
    UNKNOWN = "UNKNOWN"


LEGITIMATE_UNAVAILABLE_CODES = frozenset(
    {
        MarketAvailability.NO_TRADE.value,
        MarketAvailability.SUSPENDED.value,
        MarketAvailability.EXCHANGE_CONFIRMED_NO_DATA.value,
        MarketAvailability.HALTED.value,
        MarketAvailability.DELISTED.value,
        MarketAvailability.TERMINATED.value,
    }
)
PIPELINE_FAILURE_CODES = frozenset(
    {
        MarketAvailability.MISSING_MARKET_DATA.value,
        MarketAvailability.PROVIDER_ERROR.value,
        MarketAvailability.DATE_MISMATCH.value,
    }
)
UNKNOWN_CODES = frozenset({MarketAvailability.UNKNOWN.value})


class AvailabilityClass(StrEnum):
    AVAILABLE = "AVAILABLE"
    LEGITIMATE_UNAVAILABLE = "LEGITIMATE_UNAVAILABLE"
    DATA_PIPELINE_FAILURE = "DATA_PIPELINE_FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class AvailabilityDecision:
    """The publication-relevant interpretation of one instrument state."""

    status: str
    reason_code: str | None
    classification: str
    is_legitimate_unavailable: bool
    blocks_formal_publication: bool


def classify_availability(
    *,
    status_code: str | None,
    reason_code: str | None = None,
    has_canonical_status_evidence: bool = False,
) -> AvailabilityDecision:
    """Classify a price gap without turning absence into an exchange claim."""

    status = str(status_code or MarketAvailability.UNKNOWN.value).upper()
    reason = str(reason_code).upper() if reason_code else None
    if status == MarketAvailability.AVAILABLE.value:
        return AvailabilityDecision(
            status=status,
            reason_code=reason,
            classification=AvailabilityClass.AVAILABLE.value,
            is_legitimate_unavailable=False,
            blocks_formal_publication=False,
        )
    if status in LEGITIMATE_UNAVAILABLE_CODES and has_canonical_status_evidence:
        return AvailabilityDecision(
            status=status,
            reason_code=reason or status,
            classification=AvailabilityClass.LEGITIMATE_UNAVAILABLE.value,
            is_legitimate_unavailable=True,
            blocks_formal_publication=False,
        )
    if reason in PIPELINE_FAILURE_CODES or status in PIPELINE_FAILURE_CODES:
        return AvailabilityDecision(
            status=status if status in PIPELINE_FAILURE_CODES else MarketAvailability.UNKNOWN.value,
            reason_code=reason or status,
            classification=AvailabilityClass.DATA_PIPELINE_FAILURE.value,
            is_legitimate_unavailable=False,
            blocks_formal_publication=True,
        )
    return AvailabilityDecision(
        status=status if status in UNKNOWN_CODES else MarketAvailability.UNKNOWN.value,
        reason_code=reason or MarketAvailability.UNKNOWN.value,
        classification=AvailabilityClass.UNKNOWN.value,
        is_legitimate_unavailable=False,
        blocks_formal_publication=True,
    )


__all__ = [
    "LEGITIMATE_UNAVAILABLE_CODES",
    "PIPELINE_FAILURE_CODES",
    "UNKNOWN_CODES",
    "AvailabilityClass",
    "AvailabilityDecision",
    "MarketAvailability",
    "classify_availability",
]
