"""Provider-neutral, deterministic Topic Engine feature contracts and runtime."""

from .contracts import FeatureEvaluation, FeatureResult, FeatureStatus, FeatureValue
from .evaluator import evaluate_features

__all__ = [
    "FeatureEvaluation",
    "FeatureResult",
    "FeatureStatus",
    "FeatureValue",
    "evaluate_features",
]
