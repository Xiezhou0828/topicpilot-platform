"""Smallest-scope formal readiness projections.

The projection is deliberately in-memory and provenance-carrying.  Formal
membership remains authoritative elsewhere; this module only describes which
calculation dimensions a selected member can contribute on one date.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from topicpilot_api.previous_close_authority import (
    AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE,
    ComparatorResolution,
    ComparatorStatus,
)

_OFFICIAL_CORPORATE_ACTION_SOURCES = frozenset(
    {"TWSE_OFFICIAL_REDUCTION", "TPEX_OFFICIAL_REDUCTION"}
)


class Dimension(StrEnum):
    EOD_PRICE = "EOD_PRICE"
    DAILY_COMPARATOR = "DAILY_COMPARATOR"
    DAILY_RETURN = "DAILY_RETURN"
    BENCHMARK_RETURN = "BENCHMARK_RETURN"
    RELATIVE_RETURN = "RELATIVE_RETURN"
    RAW_VOLUME = "RAW_VOLUME"
    TURNOVER_VALUE = "TURNOVER_VALUE"
    TURNOVER_RATE = "TURNOVER_RATE"
    TECHNICAL_SERIES = "TECHNICAL_SERIES"
    MA20 = "MA20"
    MA60 = "MA60"


class DimensionStatus(StrEnum):
    READY = "READY"
    ACCOUNTED_UNAVAILABLE = "ACCOUNTED_UNAVAILABLE"
    ERROR = "ERROR"


def is_authorized_accounted_unavailable_fact(fact: Any) -> bool:
    """Return whether a formal member fact is an authority-backed no-trade gap.

    A company-action suspension can be covered by the formal universe without
    fabricating a close or return.  Only the explicit ``NO_TRADE`` fact state
    with the canonical comparator reason is eligible for this exception;
    ordinary ``UNKNOWN`` or missing-data facts remain fail-closed.
    """

    if getattr(fact, "fact_state", None) != "NO_TRADE":
        return False
    if getattr(fact, "change_pct", None) is not None:
        return False
    payload = getattr(fact, "raw_fact_payload", None) or {}
    eligibility = payload.get("dimensionEligibility") or {}
    daily_return = eligibility.get("DAILY_RETURN") or {}
    comparator = payload.get("comparatorAuthority") or {}
    if daily_return.get("status") != DimensionStatus.ACCOUNTED_UNAVAILABLE.value:
        return False

    reason_code = daily_return.get("reasonCode")
    if reason_code == AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE:
        return True
    if comparator.get("status") != DimensionStatus.ACCOUNTED_UNAVAILABLE.value:
        return False

    # Canonical member facts carry the concrete official corporate-action
    # reason (for example CAPITAL_REDUCTION_TRADING_SUSPENSION), while the
    # comparator resolver uses the generic reason above.  Accept the concrete
    # form only when both projections carry the same official authority and
    # independently verifiable source reference.
    source = daily_return.get("authoritySource")
    reference = daily_return.get("sourceReference")
    return (
        getattr(fact, "trading_status_observation_id", None) is not None
        and
        reason_code
        and source in _OFFICIAL_CORPORATE_ACTION_SOURCES
        and source == comparator.get("authoritySource")
        and reference
        and reference == comparator.get("sourceReference")
        and str(reference).startswith(("https://", "http://"))
        and reason_code == comparator.get("reasonCode")
    )


@dataclass(frozen=True)
class DimensionEligibility:
    dimension: Dimension
    status: DimensionStatus
    reason_code: str | None = None
    authority_source: str | None = None
    source_reference: str | None = None
    comparator_type: str | None = None

    @property
    def eligible(self) -> bool:
        return self.status == DimensionStatus.READY

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "status": self.status.value,
            "reasonCode": self.reason_code,
            "authoritySource": self.authority_source,
            "sourceReference": self.source_reference,
            "comparatorType": self.comparator_type,
        }


def project_return_dimensions(
    comparator: ComparatorResolution,
    *,
    current_price_ready: bool,
    benchmark_status: DimensionStatus = DimensionStatus.READY,
) -> dict[Dimension, DimensionEligibility]:
    """Project return-related dimensions without changing membership.

    A corporate-action comparator absence is accounted only for the affected
    return dimensions.  A current-price failure or unresolved comparator stays
    an error.  Benchmark readiness is supplied independently and is never
    inferred from an individual instrument comparator.
    """

    if not current_price_ready and comparator.status != ComparatorStatus.ACCOUNTED_UNAVAILABLE:
        eod = DimensionEligibility(
            Dimension.EOD_PRICE,
            DimensionStatus.ERROR,
            "CURRENT_EOD_PRICE_UNAVAILABLE",
        )
        status = DimensionStatus.ERROR
        reason = "CURRENT_EOD_PRICE_UNAVAILABLE"
    elif not current_price_ready:
        reason = comparator.reason_code
        eod = DimensionEligibility(
            Dimension.EOD_PRICE,
            DimensionStatus.ACCOUNTED_UNAVAILABLE,
            reason,
            comparator.authority_source,
            comparator.source_reference,
            comparator.comparator_type.value if comparator.comparator_type else None,
        )
        status = DimensionStatus.ACCOUNTED_UNAVAILABLE
    else:
        eod = DimensionEligibility(Dimension.EOD_PRICE, DimensionStatus.READY)
        status = DimensionStatus(
            comparator.status.value
            if comparator.status in {
                ComparatorStatus.READY,
                ComparatorStatus.ACCOUNTED_UNAVAILABLE,
            }
            else DimensionStatus.ERROR.value
        )
        reason = comparator.reason_code

    comparator_dimension = DimensionEligibility(
        Dimension.DAILY_COMPARATOR,
        status,
        reason,
        comparator.authority_source,
        comparator.source_reference,
        comparator.comparator_type.value if comparator.comparator_type else None,
    )
    daily_return = DimensionEligibility(
        Dimension.DAILY_RETURN,
        status,
        reason,
        comparator.authority_source,
        comparator.source_reference,
        comparator.comparator_type.value if comparator.comparator_type else None,
    )
    benchmark = DimensionEligibility(
        Dimension.BENCHMARK_RETURN,
        benchmark_status,
        None if benchmark_status == DimensionStatus.READY else "BENCHMARK_FACTS_UNAVAILABLE",
        "OFFICIAL_INDEX_AUTHORITY" if benchmark_status == DimensionStatus.READY else None,
    )
    relative_status = (
        status
        if status != DimensionStatus.READY
        else benchmark_status
    )
    relative = DimensionEligibility(
        Dimension.RELATIVE_RETURN,
        relative_status,
        (
            reason
            if status != DimensionStatus.READY
            else benchmark.reason_code
        ),
        (
            comparator.authority_source
            if status != DimensionStatus.READY
            else benchmark.authority_source
        ),
        (
            comparator.source_reference
            if status != DimensionStatus.READY
            else benchmark.source_reference
        ),
        comparator.comparator_type.value if comparator.comparator_type else None,
    )
    return {
        Dimension.EOD_PRICE: eod,
        Dimension.DAILY_COMPARATOR: comparator_dimension,
        Dimension.DAILY_RETURN: daily_return,
        Dimension.BENCHMARK_RETURN: benchmark,
        Dimension.RELATIVE_RETURN: relative,
    }


def dimension_payload(
    dimensions: dict[Dimension, DimensionEligibility],
) -> dict[str, dict[str, Any]]:
    return {dimension.value: value.to_dict() for dimension, value in dimensions.items()}


__all__ = [
    "Dimension",
    "DimensionEligibility",
    "DimensionStatus",
    "dimension_payload",
    "is_authorized_accounted_unavailable_fact",
    "project_return_dimensions",
]
