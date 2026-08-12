from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from statistics import fmean

from .contracts import EvaluationBundle
from .features.contracts import FeatureEvaluation, FeatureResult, FeatureStatus
from .runtime import FeatureRuntimeConfig, run_feature_runtime


class AggregateStatus:
    INVALID_INPUT = "INVALID_INPUT"
    DATA_INSUFFICIENT = "DATA_INSUFFICIENT"
    READY_UNSCORED = "READY_UNSCORED"


@dataclass(frozen=True)
class QualitySummary:
    ready_feature_count: int
    insufficient_feature_count: int
    invalid_feature_count: int
    coverage_min: float | None
    coverage_mean: float | None


@dataclass(frozen=True)
class FeatureAggregate:
    topic_id: str
    as_of: date
    feature_set_version: str
    aggregation_version: str
    status: str
    feature_results: tuple[FeatureResult, ...]
    quality: QualitySummary
    quality_flags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AggregationResult:
    as_of: date
    feature_set_version: str
    runtime_version: str
    aggregation_version: str
    aggregates: tuple[FeatureAggregate, ...]


def aggregate_features(bundle: EvaluationBundle, config: FeatureRuntimeConfig) -> AggregationResult:
    return aggregate_evaluation(run_feature_runtime(bundle, config), config)


def aggregate_evaluation(
    evaluation: FeatureEvaluation, config: FeatureRuntimeConfig
) -> AggregationResult:
    grouped: dict[str, list[FeatureResult]] = {}
    for result in evaluation.results:
        grouped.setdefault(result.topic_id, []).append(result)
    aggregates = tuple(
        _aggregate_topic(topic_id, tuple(results), evaluation, config)
        for topic_id, results in sorted(grouped.items())
    )
    return AggregationResult(
        evaluation.as_of,
        evaluation.feature_set_version,
        config.runtime_version,
        config.aggregation_version,
        aggregates,
    )


def _aggregate_topic(
    topic_id: str,
    results: tuple[FeatureResult, ...],
    evaluation: FeatureEvaluation,
    config: FeatureRuntimeConfig,
) -> FeatureAggregate:
    ordered = tuple(sorted(results, key=lambda item: (item.feature_name, item.feature_version)))
    invalid = sum(result.status == FeatureStatus.INVALID_INPUT for result in ordered)
    insufficient = sum(result.status == FeatureStatus.DATA_INSUFFICIENT for result in ordered)
    ready = sum(result.status == FeatureStatus.READY for result in ordered)
    required = set(config.required_feature_names)
    required_results = tuple(result for result in ordered if result.feature_name in required)
    if any(result.status == FeatureStatus.INVALID_INPUT for result in required_results):
        status = AggregateStatus.INVALID_INPUT
    elif any(result.status == FeatureStatus.DATA_INSUFFICIENT for result in required_results):
        status = AggregateStatus.DATA_INSUFFICIENT
    else:
        status = AggregateStatus.READY_UNSCORED
    coverages = tuple(result.coverage for result in ordered if result.coverage is not None)
    quality = QualitySummary(
        ready,
        insufficient,
        invalid,
        min(coverages) if coverages else None,
        fmean(coverages) if coverages else None,
    )
    flags = tuple(sorted({flag for result in ordered for flag in result.quality_flags}))
    return FeatureAggregate(
        topic_id,
        evaluation.as_of,
        evaluation.feature_set_version,
        config.aggregation_version,
        status,
        ordered,
        quality,
        flags,
    )


__all__ = [
    "AggregateStatus",
    "AggregationResult",
    "FeatureAggregate",
    "QualitySummary",
    "aggregate_evaluation",
    "aggregate_features",
]
