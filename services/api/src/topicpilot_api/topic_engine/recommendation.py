"""Deterministic, downstream Recommendation contract over Topic Intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .integration import TopicIntelligenceRuntimeResult

RECOMMENDATION_CONTRACT_VERSION = "recommendation-contract.v1"


@dataclass(frozen=True)
class RecommendationCandidateFact:
    """Explicit upstream candidate fact; this module never discovers candidates."""

    candidate_id: str
    topic_id: str
    label: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class TopicIntelligenceLineage:
    """Immutable upstream identity and explainability context for one item."""

    as_of: date | None
    scorer_runtime_version: str | None
    feature_set_version: str | None
    feature_runtime_version: str | None
    aggregation_version: str | None
    policy_id: str | None
    policy_version: str | None
    eligibility: str | None
    score: float | None
    grade: str | None
    confidence: float | None
    components: tuple[tuple[str, float | None], ...] | None
    evidence_reference: tuple[str, ...] | None


@dataclass(frozen=True)
class RecommendationItem:
    candidate_id: str
    topic_id: str
    label: str
    status: str
    reason: str
    topic_context: TopicIntelligenceLineage | None
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class RecommendationResult:
    contract_version: str
    as_of: date | None
    status: str
    items: tuple[RecommendationItem, ...]


def build_recommendations(
    runtime: TopicIntelligenceRuntimeResult | None,
    candidates: tuple[RecommendationCandidateFact, ...] = (),
) -> RecommendationResult:
    """Project explicit facts downstream without calculating or ranking Topic Score."""
    if runtime is None:
        return RecommendationResult(RECOMMENDATION_CONTRACT_VERSION, None, "UNAVAILABLE", ())
    scores = {score.topic_id: score for score in runtime.scores}
    if len(scores) != len(runtime.scores):
        raise ValueError("Topic Intelligence runtime contains duplicate topic identities")
    for score in runtime.scores:
        expected = (
            runtime.as_of,
            runtime.feature_set_version,
            runtime.aggregation_version,
            runtime.policy_id,
            runtime.policy_version,
        )
        actual = (
            score.as_of,
            score.feature_set_version,
            score.aggregation_version,
            score.policy_id,
            score.policy_version,
        )
        if actual != expected:
            raise ValueError("Topic Intelligence score lineage does not match runtime identity")
    items: list[RecommendationItem] = []
    for candidate in sorted(candidates, key=lambda value: value.candidate_id):
        score = scores.get(candidate.topic_id)
        if score is None:
            status, reason = "DEFERRED", "TOPIC_INTELLIGENCE_MISSING"
        elif score.status != "SCORED":
            status, reason = "DEFERRED", f"TOPIC_INTELLIGENCE_{score.status}"
        elif score.eligibility != "ELIGIBLE":
            status, reason = "DEFERRED", "TOPIC_INTELLIGENCE_INELIGIBLE"
        else:
            status, reason = "AVAILABLE", "TOPIC_INTELLIGENCE_AVAILABLE"
        context = (
            None
            if score is None
            else TopicIntelligenceLineage(
                runtime.as_of,
                runtime.scorer_runtime_version,
                runtime.feature_set_version,
                runtime.feature_runtime_version,
                runtime.aggregation_version,
                runtime.policy_id,
                runtime.policy_version,
                score.eligibility,
                score.score,
                score.grade,
                score.confidence,
                score.components,
                _evidence_reference(score.evidence),
            )
        )
        items.append(
            RecommendationItem(
                candidate.candidate_id,
                candidate.topic_id,
                candidate.label,
                status,
                reason,
                context,
                candidate.evidence,
            )
        )
    status = (
        "AVAILABLE" if items and all(item.status == "AVAILABLE" for item in items) else "DEFERRED"
    )
    return RecommendationResult(
        RECOMMENDATION_CONTRACT_VERSION, runtime.as_of, status, tuple(items)
    )


__all__ = [
    "RECOMMENDATION_CONTRACT_VERSION",
    "RecommendationCandidateFact",
    "RecommendationItem",
    "RecommendationResult",
    "TopicIntelligenceLineage",
    "build_recommendations",
]


def _evidence_reference(evidence: object) -> tuple[str, ...] | None:
    if evidence is None:
        return None
    return (
        evidence.status,
        evidence.feature_set_version,
        evidence.aggregation_version,
        *evidence.quality_flags,
    )
