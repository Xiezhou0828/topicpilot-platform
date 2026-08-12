"""Immutable boundary between score-free aggregation and future scoring policies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .aggregation import AggregateStatus, FeatureAggregate


@dataclass(frozen=True)
class ScoringPolicy:
    """Versioned policy identity and opaque configuration, without business rules."""

    policy_id: str
    policy_version: str
    configuration: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError("policy_id must be non-empty")
        if not self.policy_version.strip():
            raise ValueError("policy_version must be non-empty")
        keys = tuple(key for key, _ in self.configuration)
        if any(not key.strip() for key in keys):
            raise ValueError("policy configuration keys must be non-empty")
        if len(keys) != len(set(keys)):
            raise ValueError("policy configuration keys must not contain duplicates")
        if tuple(sorted(self.configuration)) != self.configuration:
            raise ValueError("policy configuration must be canonically sorted")


@dataclass(frozen=True)
class ScoringInput:
    """A lossless, identity-preserving input snapshot for a policy executor."""

    topic_id: str
    as_of: date
    feature_set_version: str
    runtime_version: str
    aggregation_version: str
    aggregate_status: str
    aggregate: FeatureAggregate

    def __post_init__(self) -> None:
        if not self.runtime_version.strip():
            raise ValueError("runtime_version must be non-empty")
        if self.topic_id != self.aggregate.topic_id:
            raise ValueError("topic_id must match aggregate evidence")
        if self.as_of != self.aggregate.as_of:
            raise ValueError("as_of must match aggregate evidence")
        if self.feature_set_version != self.aggregate.feature_set_version:
            raise ValueError("feature_set_version must match aggregate evidence")
        if self.aggregation_version != self.aggregate.aggregation_version:
            raise ValueError("aggregation_version must match aggregate evidence")
        if self.aggregate_status != self.aggregate.status:
            raise ValueError("aggregate_status must match aggregate evidence")


@dataclass(frozen=True)
class TopicScore:
    """Deferred score result; business values remain null until PM approval."""

    topic_id: str
    as_of: date
    policy_id: str
    policy_version: str
    feature_set_version: str
    runtime_version: str
    aggregation_version: str
    status: str
    score: float | None = None
    grade: str | None = None
    strength: str | None = None
    evidence: FeatureAggregate | None = None
    components: tuple[tuple[str, float | None], ...] = ()
    confidence: float | None = None
    eligibility: str = "UNKNOWN"


def scoring_input(aggregate: FeatureAggregate, *, runtime_version: str) -> ScoringInput:
    return ScoringInput(
        aggregate.topic_id,
        aggregate.as_of,
        aggregate.feature_set_version,
        runtime_version,
        aggregate.aggregation_version,
        aggregate.status,
        aggregate,
    )


def deferred_score(value: ScoringInput, policy: ScoringPolicy) -> TopicScore:
    """Create a traceable contract result without executing a scoring formula."""
    return TopicScore(
        value.topic_id,
        value.as_of,
        policy.policy_id,
        policy.policy_version,
        value.feature_set_version,
        value.runtime_version,
        value.aggregation_version,
        (
            AggregateStatus.INVALID_INPUT
            if value.aggregate_status == AggregateStatus.INVALID_INPUT
            else "DEFERRED"
        ),
        evidence=value.aggregate,
    )


__all__ = ["ScoringInput", "ScoringPolicy", "TopicScore", "deferred_score", "scoring_input"]
