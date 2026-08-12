from datetime import date
from types import SimpleNamespace

import pytest

from topicpilot_api.topic_engine import RecommendationCandidateFact, build_recommendations
from topicpilot_api.topic_engine.scoring_contracts import TopicScore

AS_OF = date(2026, 8, 9)


def runtime(*scores: TopicScore):
    return SimpleNamespace(
        as_of=AS_OF,
        feature_set_version="features.v1",
        feature_runtime_version="runtime.v1",
        aggregation_version="aggregation.v1",
        scorer_runtime_version="scorer.v1",
        policy_id="policy",
        policy_version="policy.v1",
        scores=scores,
    )


def score(topic_id: str, **kwargs) -> TopicScore:
    return TopicScore(
        topic_id,
        AS_OF,
        "policy",
        "policy.v1",
        "features.v1",
        "runtime.v1",
        "aggregation.v1",
        kwargs.pop("status", "SCORED"),
        **kwargs,
    )


def test_recommendation_is_fail_closed_without_topic_intelligence() -> None:
    result = build_recommendations(None, (RecommendationCandidateFact("c1", "t1", "One"),))
    assert result.status == "UNAVAILABLE"
    assert result.as_of is None
    assert result.items == ()


def test_available_candidate_preserves_full_upstream_lineage_without_recomputation() -> None:
    upstream = score(
        "t1",
        score=7.5,
        grade="A",
        confidence=None,
        components=(("breadth", None),),
        evidence=None,
        eligibility="ELIGIBLE",
    )
    result = build_recommendations(
        runtime(upstream), (RecommendationCandidateFact("c1", "t1", "One"),)
    )
    context = result.items[0].topic_context
    assert result.status == "AVAILABLE"
    assert context is not None
    assert context.as_of == AS_OF
    assert context.scorer_runtime_version == "scorer.v1"
    assert context.feature_set_version == "features.v1"
    assert context.policy_version == "policy.v1"
    assert context.eligibility == "ELIGIBLE"
    assert context.score == 7.5
    assert context.grade == "A"
    assert context.confidence is None
    assert context.components == (("breadth", None),)
    assert context.evidence_reference is None


def test_deferred_and_ineligible_upstream_scores_remain_non_actionable() -> None:
    result = build_recommendations(
        runtime(
            score("deferred", status="DEFERRED"), score("ineligible", eligibility="INELIGIBLE")
        ),
        (
            RecommendationCandidateFact("c2", "ineligible", "I"),
            RecommendationCandidateFact("c1", "deferred", "D"),
        ),
    )
    assert result.status == "DEFERRED"
    assert [item.candidate_id for item in result.items] == ["c1", "c2"]
    assert result.items[0].reason == "TOPIC_INTELLIGENCE_DEFERRED"
    assert result.items[1].reason == "TOPIC_INTELLIGENCE_INELIGIBLE"


def test_missing_topic_is_deferred_and_candidate_evidence_is_preserved() -> None:
    result = build_recommendations(
        runtime(), (RecommendationCandidateFact("c2", "missing", "Two", ("observed",)),)
    )
    item = result.items[0]
    assert result.status == "DEFERRED"
    assert item.reason == "TOPIC_INTELLIGENCE_MISSING"
    assert item.topic_context is None
    assert item.evidence == ("observed",)


def test_inconsistent_upstream_identity_fails_closed() -> None:
    mismatched = TopicScore(
        "t1",
        AS_OF,
        "other-policy",
        "policy.v1",
        "features.v1",
        "runtime.v1",
        "aggregation.v1",
        "SCORED",
    )
    with pytest.raises(ValueError, match="lineage"):
        build_recommendations(
            runtime(mismatched), (RecommendationCandidateFact("c1", "t1", "One"),)
        )
