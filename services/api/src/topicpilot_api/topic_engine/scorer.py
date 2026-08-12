"""Pluggable Topic Scorer runtime; business formulas remain policy-owned."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from .aggregation import AggregateStatus, FeatureAggregate
from .scoring_contracts import ScoringPolicy, TopicScore, scoring_input


class ComponentCollector(Protocol):
    def __call__(self, aggregate: FeatureAggregate) -> Mapping[str, float | None]: ...


class AggregationPolicy(Protocol):
    def aggregate(
        self, components: Mapping[str, float | None], policy: ScoringPolicy
    ) -> float | None: ...


class GradeMapper(Protocol):
    def __call__(self, score: float | None, policy: ScoringPolicy) -> str | None: ...


class ConfidenceProvider(Protocol):
    def __call__(self, aggregate: FeatureAggregate) -> float | None: ...


@dataclass(frozen=True)
class DeferredAggregationPolicy:
    """Safe default until PM-approved aggregation mechanics are supplied."""

    def aggregate(
        self, components: Mapping[str, float | None], policy: ScoringPolicy
    ) -> float | None:
        return None


def deferred_components(_: FeatureAggregate) -> Mapping[str, float | None]:
    return {"breadth": None, "leadership": None}


def passthrough_confidence(_: FeatureAggregate) -> float | None:
    return None


def no_grade(score: float | None, policy: ScoringPolicy) -> str | None:
    return None


@dataclass(frozen=True)
class TopicScorer:
    runtime_version: str
    component_collector: ComponentCollector = deferred_components
    aggregation_policy: AggregationPolicy = DeferredAggregationPolicy()
    grade_mapper: GradeMapper = no_grade
    confidence_provider: ConfidenceProvider = passthrough_confidence

    def __post_init__(self) -> None:
        if not self.runtime_version.strip():
            raise ValueError("runtime_version must be non-empty")

    def score(self, aggregate: FeatureAggregate, policy: ScoringPolicy) -> TopicScore:
        value = scoring_input(aggregate, runtime_version=self.runtime_version)
        if aggregate.status != AggregateStatus.READY_UNSCORED:
            return TopicScore(
                value.topic_id,
                value.as_of,
                policy.policy_id,
                policy.policy_version,
                value.feature_set_version,
                value.runtime_version,
                value.aggregation_version,
                aggregate.status,
                evidence=aggregate,
                eligibility="INELIGIBLE",
            )
        components = dict(self.component_collector(aggregate))
        score = self.aggregation_policy.aggregate(components, policy)
        return TopicScore(
            value.topic_id,
            value.as_of,
            policy.policy_id,
            policy.policy_version,
            value.feature_set_version,
            value.runtime_version,
            value.aggregation_version,
            "SCORED" if score is not None else "DEFERRED",
            score=score,
            grade=self.grade_mapper(score, policy) if score is not None else None,
            evidence=aggregate,
            components=tuple(sorted(components.items())),
            confidence=self.confidence_provider(aggregate),
            eligibility="ELIGIBLE",
        )


__all__ = [
    "AggregationPolicy",
    "ComponentCollector",
    "ConfidenceProvider",
    "DeferredAggregationPolicy",
    "GradeMapper",
    "TopicScorer",
    "deferred_components",
    "no_grade",
    "passthrough_confidence",
]
