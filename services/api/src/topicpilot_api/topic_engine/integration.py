"""Deterministic Topic Intelligence integration runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .aggregation import AggregationResult
from .scorer import TopicScorer
from .scoring_contracts import ScoringPolicy, TopicScore


@dataclass(frozen=True)
class TopicIntelligenceRuntimeResult:
    """Traceable, ephemeral output for one complete Topic Engine evaluation."""

    as_of: date
    feature_set_version: str
    feature_runtime_version: str
    aggregation_version: str
    scorer_runtime_version: str
    policy_id: str
    policy_version: str
    scores: tuple[TopicScore, ...]


def run_topic_intelligence(
    aggregates: AggregationResult, scorer: TopicScorer, policy: ScoringPolicy
) -> TopicIntelligenceRuntimeResult:
    """Orchestrate aggregate evidence through the eligibility-first scorer."""
    scores = tuple(scorer.score(aggregate, policy) for aggregate in aggregates.aggregates)
    return TopicIntelligenceRuntimeResult(
        aggregates.as_of,
        aggregates.feature_set_version,
        aggregates.runtime_version,
        aggregates.aggregation_version,
        scorer.runtime_version,
        policy.policy_id,
        policy.policy_version,
        scores,
    )


__all__ = ["TopicIntelligenceRuntimeResult", "run_topic_intelligence"]
