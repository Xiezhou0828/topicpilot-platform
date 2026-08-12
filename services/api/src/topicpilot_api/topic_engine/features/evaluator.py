from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from ..contracts import EvaluationBundle
from .availability import availability_features
from .contracts import FeatureEvaluation, FeatureResult
from .hierarchy import hierarchy_features
from .membership import membership_features

FeatureCalculator = Callable[[EvaluationBundle], Iterable[FeatureResult]]

@dataclass(frozen=True)
class FeatureCalculatorSpec:
    calculator: FeatureCalculator
    feature_names: tuple[str, ...]
    version: str = "v1"

    def __post_init__(self) -> None:
        names = tuple(name.strip() for name in self.feature_names)
        if not names or any(not name for name in names) or len(names) != len(set(names)):
            raise ValueError("feature calculator spec must contain unique non-blank names")
        if not self.version.strip():
            raise ValueError("feature calculator version must be non-empty")
        object.__setattr__(self, "feature_names", names)
DEFAULT_FEATURE_SET_VERSION = "topic-features-v1"
DEFAULT_CALCULATORS: tuple[FeatureCalculator, ...] = (
    membership_features,
    hierarchy_features,
    availability_features,
)
DEFAULT_CALCULATOR_SPECS: tuple[FeatureCalculatorSpec, ...] = (
    FeatureCalculatorSpec(membership_features, ("membership_coverage", "membership_count")),
    FeatureCalculatorSpec(hierarchy_features, ("hierarchy_quality",)),
    FeatureCalculatorSpec(availability_features, ("observation_availability",)),
)

def catalogue_for_calculators(
    calculators: tuple[FeatureCalculator, ...],
) -> tuple[FeatureCalculatorSpec, ...]:
    known = {spec.calculator: spec for spec in DEFAULT_CALCULATOR_SPECS}
    try:
        return tuple(known[calculator] for calculator in calculators)
    except KeyError as exc:
        raise ValueError("every calculator must have a declarative feature catalogue spec") from exc


def evaluate_features(
    bundle: EvaluationBundle,
    *,
    feature_set_version: str = DEFAULT_FEATURE_SET_VERSION,
    calculators: tuple[FeatureCalculator, ...] = DEFAULT_CALCULATORS,
) -> FeatureEvaluation:
    if not feature_set_version.strip():
        raise ValueError("feature_set_version must be non-empty")
    results = tuple(result for calculator in calculators for result in calculator(bundle))
    ordered_results = tuple(
        sorted(
            results,
            key=lambda result: (result.topic_id, result.feature_name, result.feature_version),
        )
    )
    return FeatureEvaluation(feature_set_version, bundle.as_of, ordered_results)

__all__ = [
    "DEFAULT_CALCULATOR_SPECS",
    "FeatureCalculator",
    "FeatureCalculatorSpec",
    "catalogue_for_calculators",
    "evaluate_features",
]
