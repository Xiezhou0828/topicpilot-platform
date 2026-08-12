from __future__ import annotations

from dataclasses import dataclass

from .contracts import EvaluationBundle
from .features.contracts import FeatureEvaluation
from .features.evaluator import FeatureCalculator, catalogue_for_calculators, evaluate_features


@dataclass(frozen=True)
class FeatureRuntimeConfig:
    feature_set_version: str
    runtime_version: str
    aggregation_version: str
    required_feature_names: tuple[str, ...]
    calculators: tuple[FeatureCalculator, ...]

    def __post_init__(self) -> None:
        for field_name in ("feature_set_version", "runtime_version", "aggregation_version"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must be non-empty")
        names = tuple(name.strip() for name in self.required_feature_names)
        if any(not name for name in names):
            raise ValueError("required_feature_names must not contain blank names")
        if len(names) != len(set(names)):
            raise ValueError("required_feature_names must not contain duplicates")
        object.__setattr__(self, "required_feature_names", names)
        if not self.calculators:
            raise ValueError("calculators must be non-empty")
        catalogue = catalogue_for_calculators(self.calculators)
        unknown = set(names) - {name for spec in catalogue for name in spec.feature_names}
        if unknown:
            raise ValueError(
                "required feature names are not produced by calculators: "
                + ", ".join(sorted(unknown))
            )


def run_feature_runtime(
    bundle: EvaluationBundle, config: FeatureRuntimeConfig
) -> FeatureEvaluation:
    evaluation = evaluate_features(
        bundle, feature_set_version=config.feature_set_version, calculators=config.calculators
    )
    return evaluation


__all__ = ["FeatureRuntimeConfig", "run_feature_runtime"]
