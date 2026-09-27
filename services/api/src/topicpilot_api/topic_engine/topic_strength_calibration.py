"""Read-only calibration foundation for the role-strength Design Freeze.

The helpers in this module describe canonical historical observations.  They
never choose production knots, optimize a future outcome, or turn a
distribution into an approved policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final

from .topic_strength_contract import (
    ABSOLUTE,
    RELATIVE,
    TopicStrengthError,
    benchmark_for_market,
)

CALIBRATION_REGISTER_VERSION: Final = "topic-strength-calibration-register.v1"
CALIBRATION_REQUIRED_PARAMETERS: Final = (
    "absolute_representative_response_knots",
    "absolute_core_response_knots",
    "related_breadth_magnitude_mapping",
    "absolute_grade_bands",
    "relative_neutral_band",
    "relative_representative_response_knots",
    "relative_core_response_knots",
    "relative_related_diffusion_mapping",
    "relative_grade_bands",
    "lifecycle_role_breadth_thresholds",
    "lifecycle_role_magnitude_thresholds",
    "lifecycle_confirmation_days",
    "mature_persistence_parameters",
    "declining_deterioration_parameters",
)


@dataclass(frozen=True)
class RoleDayObservation:
    """Canonical point-in-time row used only for descriptive calibration."""

    topic_id: str
    as_of: date
    member_id: str
    role: str
    return_pct: float | None
    market: str | None = None
    benchmark_return_pct: float | None = None
    source_kind: str = "CANONICAL_HISTORICAL"

    def value_for(self, view: str) -> float | None:
        if self.return_pct is None:
            return None
        if self.source_kind != "CANONICAL_HISTORICAL":
            raise TopicStrengthError("calibration requires canonical historical observations")
        if view == ABSOLUTE:
            return float(self.return_pct)
        if view != RELATIVE or self.benchmark_return_pct is None:
            return None
        benchmark_for_market(self.market or "")
        return float(self.return_pct) - float(self.benchmark_return_pct)


@dataclass(frozen=True)
class RoleDayDistribution:
    role: str
    view: str
    observation_count: int
    topic_day_count: int
    minimum: float | None
    p10: float | None
    p25: float | None
    median: float | None
    p75: float | None
    p90: float | None
    maximum: float | None

    def as_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "view": self.view,
            "observationCount": self.observation_count,
            "topicDayCount": self.topic_day_count,
            "minimum": self.minimum,
            "p10": self.p10,
            "p25": self.p25,
            "median": self.median,
            "p75": self.p75,
            "p90": self.p90,
            "maximum": self.maximum,
        }


def _percentile(values: tuple[float, ...], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentile
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return round(ordered[lower] + fraction * (ordered[upper] - ordered[lower]), 6)


def describe_role_day_distributions(
    observations: tuple[RoleDayObservation, ...],
) -> tuple[RoleDayDistribution, ...]:
    """Return descriptive role/day distributions with no threshold selection."""

    groups: dict[tuple[str, str], list[float]] = {}
    topic_days: dict[tuple[str, str], set[tuple[str, date]]] = {}
    for item in observations:
        for view in (ABSOLUTE, RELATIVE):
            value = item.value_for(view)
            if value is None:
                continue
            key = (item.role, view)
            groups.setdefault(key, []).append(value)
            topic_days.setdefault(key, set()).add((item.topic_id, item.as_of))
    result: list[RoleDayDistribution] = []
    for (role, view), raw_values in sorted(groups.items()):
        values = tuple(raw_values)
        result.append(
            RoleDayDistribution(
                role=role,
                view=view,
                observation_count=len(values),
                topic_day_count=len(topic_days[(role, view)]),
                minimum=round(min(values), 6),
                p10=_percentile(values, 0.10),
                p25=_percentile(values, 0.25),
                median=_percentile(values, 0.50),
                p75=_percentile(values, 0.75),
                p90=_percentile(values, 0.90),
                maximum=round(max(values), 6),
            )
        )
    return tuple(result)


def calibration_register() -> dict[str, object]:
    """Return the explicit open-parameter register for governance reports."""

    return {
        "version": CALIBRATION_REGISTER_VERSION,
        "status": "CALIBRATION_REQUIRED",
        "noLookahead": True,
        "sourceRequirement": "CANONICAL_HISTORICAL",
        "parameters": [
            {"name": name, "status": "CALIBRATION_REQUIRED"}
            for name in CALIBRATION_REQUIRED_PARAMETERS
        ],
    }


__all__ = [
    "CALIBRATION_REGISTER_VERSION",
    "CALIBRATION_REQUIRED_PARAMETERS",
    "RoleDayDistribution",
    "RoleDayObservation",
    "calibration_register",
    "describe_role_day_distributions",
]
