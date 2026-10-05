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
    ComparatorResolution,
    ComparatorStatus,
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
    "project_return_dimensions",
]
