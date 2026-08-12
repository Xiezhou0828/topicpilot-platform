"""Evidence-backed but non-production Topic Formula policy candidates."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from .aggregation import FeatureAggregate
from .features.contracts import FeatureResult, FeatureStatus
from .research import (
    FROZEN_COMPONENT_NAMES,
    RESEARCH_ONLY,
    FormulaResearchValidationError,
    ResearchBounds,
    ResearchCandidate,
)
from .scorer import TopicScorer
from .scoring_contracts import ScoringPolicy

STRICT_PARTICIPATION = "STRICT_PARTICIPATION"
DIFFUSION_PARTICIPATION = "DIFFUSION_PARTICIPATION"
WEIGHTED_ARITHMETIC = "WEIGHTED_ARITHMETIC"
_SUPPORTED_METHODS = {STRICT_PARTICIPATION, DIFFUSION_PARTICIPATION}
_COUNT_FIELDS = frozenset({"positiveCount", "unchangedCount", "negativeCount"})


@dataclass(frozen=True)
class ParticipationCounts:
    positive_count: int
    unchanged_count: int
    negative_count: int

    @property
    def total_count(self) -> int:
        return self.positive_count + self.unchanged_count + self.negative_count


@dataclass(frozen=True)
class ParticipationResearchSpec:
    """All mechanics are explicit; no module-level policy candidate or weight default exists."""

    candidate_id: str
    candidate_version: str
    scorer_runtime_version: str
    breadth_feature_name: str
    breadth_feature_version: str
    breadth_method: str
    breadth_weight: float
    leadership_feature_name: str
    leadership_feature_version: str
    leadership_method: str
    leadership_weight: float
    source_references: tuple[str, ...]

    def __post_init__(self) -> None:
        for label, value in (
            ("candidate_id", self.candidate_id),
            ("candidate_version", self.candidate_version),
            ("scorer_runtime_version", self.scorer_runtime_version),
            ("breadth_feature_name", self.breadth_feature_name),
            ("breadth_feature_version", self.breadth_feature_version),
            ("leadership_feature_name", self.leadership_feature_name),
            ("leadership_feature_version", self.leadership_feature_version),
        ):
            _require_identity(value, label)
        for label, method in (
            ("breadth_method", self.breadth_method),
            ("leadership_method", self.leadership_method),
        ):
            if method not in _SUPPORTED_METHODS:
                raise FormulaResearchValidationError(f"unsupported {label}: {method}")
        _validate_weight(self.breadth_weight, "breadth_weight")
        _validate_weight(self.leadership_weight, "leadership_weight")
        if not math.isclose(
            self.breadth_weight + self.leadership_weight,
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise FormulaResearchValidationError("research component weights must sum to one")
        if not self.source_references:
            raise FormulaResearchValidationError("source_references must be non-empty")
        for source in self.source_references:
            _require_identity(source, "source reference")
        if self.source_references != tuple(sorted(self.source_references)):
            raise FormulaResearchValidationError("source_references must be canonically sorted")
        if len(self.source_references) != len(set(self.source_references)):
            raise FormulaResearchValidationError("source_references must be unique")


@dataclass(frozen=True)
class ParticipationComponentCollector:
    breadth_feature_name: str
    breadth_feature_version: str
    breadth_method: str
    leadership_feature_name: str
    leadership_feature_version: str
    leadership_method: str

    def __call__(self, aggregate: FeatureAggregate) -> Mapping[str, float | None]:
        return {
            "breadth": _component(
                aggregate,
                self.breadth_feature_name,
                self.breadth_feature_version,
                self.breadth_method,
            ),
            "leadership": _component(
                aggregate,
                self.leadership_feature_name,
                self.leadership_feature_version,
                self.leadership_method,
            ),
        }


@dataclass(frozen=True)
class WeightedArithmeticResearchAggregation:
    breadth_weight: float
    leadership_weight: float

    def __post_init__(self) -> None:
        _validate_weight(self.breadth_weight, "breadth_weight")
        _validate_weight(self.leadership_weight, "leadership_weight")
        if not math.isclose(
            self.breadth_weight + self.leadership_weight,
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise FormulaResearchValidationError("research component weights must sum to one")

    def aggregate(
        self, components: Mapping[str, float | None], policy: ScoringPolicy
    ) -> float | None:
        if tuple(sorted(components)) != FROZEN_COMPONENT_NAMES:
            raise FormulaResearchValidationError(
                "research aggregation requires breadth and leadership only"
            )
        breadth = components["breadth"]
        leadership = components["leadership"]
        if breadth is None or leadership is None:
            return None
        _validate_component_value(breadth, "breadth")
        _validate_component_value(leadership, "leadership")
        return self.breadth_weight * breadth + self.leadership_weight * leadership


def build_participation_research_candidate(
    spec: ParticipationResearchSpec,
) -> ResearchCandidate:
    """Build one explicit research candidate; callers must provide every policy choice."""

    collector = ParticipationComponentCollector(
        spec.breadth_feature_name,
        spec.breadth_feature_version,
        spec.breadth_method,
        spec.leadership_feature_name,
        spec.leadership_feature_version,
        spec.leadership_method,
    )
    aggregation = WeightedArithmeticResearchAggregation(
        spec.breadth_weight,
        spec.leadership_weight,
    )
    configuration = tuple(
        sorted(
            (
                ("aggregation_method", WEIGHTED_ARITHMETIC),
                (
                    "breadth_feature",
                    f"{spec.breadth_feature_name}@{spec.breadth_feature_version}",
                ),
                ("breadth_method", spec.breadth_method),
                ("breadth_weight", _number_text(spec.breadth_weight)),
                (
                    "leadership_feature",
                    f"{spec.leadership_feature_name}@{spec.leadership_feature_version}",
                ),
                ("leadership_method", spec.leadership_method),
                ("leadership_weight", _number_text(spec.leadership_weight)),
                ("mode", RESEARCH_ONLY),
                ("source_references", ",".join(spec.source_references)),
            )
        )
    )
    policy = ScoringPolicy(spec.candidate_id, spec.candidate_version, configuration)
    scorer = TopicScorer(
        spec.scorer_runtime_version,
        component_collector=collector,
        aggregation_policy=aggregation,
    )
    bounds = ResearchBounds(0.0, 100.0)
    return ResearchCandidate(
        spec.candidate_id,
        spec.candidate_version,
        scorer,
        policy,
        bounds,
        bounds,
    )


def _component(
    aggregate: FeatureAggregate,
    feature_name: str,
    feature_version: str,
    method: str,
) -> float | None:
    matches = tuple(
        feature
        for feature in aggregate.feature_results
        if (feature.feature_name, feature.feature_version) == (feature_name, feature_version)
    )
    if not matches:
        return None
    if len(matches) != 1:
        raise FormulaResearchValidationError("research feature identity must be unique")
    feature = matches[0]
    if feature.status != FeatureStatus.READY:
        return None
    counts = _participation_counts(feature)
    if counts.total_count == 0:
        return None
    if method == STRICT_PARTICIPATION:
        numerator = float(counts.positive_count)
    elif method == DIFFUSION_PARTICIPATION:
        numerator = counts.positive_count + 0.5 * counts.unchanged_count
    else:
        raise FormulaResearchValidationError(f"unsupported participation method: {method}")
    return 100.0 * numerator / counts.total_count


def _participation_counts(feature: FeatureResult) -> ParticipationCounts:
    value = feature.value
    if not isinstance(value, dict) or set(value) != _COUNT_FIELDS:
        raise FormulaResearchValidationError(
            "participation evidence must contain positiveCount, unchangedCount, and negativeCount"
        )
    return ParticipationCounts(
        _count(value["positiveCount"], "positiveCount"),
        _count(value["unchangedCount"], "unchangedCount"),
        _count(value["negativeCount"], "negativeCount"),
    )


def _count(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FormulaResearchValidationError(f"{label} must be a non-negative integer")
    return value


def _validate_weight(value: float, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise FormulaResearchValidationError(f"{label} must be finite")
    if value <= 0.0:
        raise FormulaResearchValidationError(f"{label} must be positive")


def _validate_component_value(value: float, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise FormulaResearchValidationError(f"{label} component must be finite")
    if not 0.0 <= value <= 100.0:
        raise FormulaResearchValidationError(f"{label} component is outside research bounds")


def _require_identity(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise FormulaResearchValidationError(f"{label} must be a trimmed non-empty string")


def _number_text(value: float) -> str:
    return format(float(value), ".17g")


__all__ = [
    "DIFFUSION_PARTICIPATION",
    "STRICT_PARTICIPATION",
    "WEIGHTED_ARITHMETIC",
    "ParticipationComponentCollector",
    "ParticipationCounts",
    "ParticipationResearchSpec",
    "WeightedArithmeticResearchAggregation",
    "build_participation_research_candidate",
]
