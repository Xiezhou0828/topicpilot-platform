from dataclasses import replace
from datetime import date

import pytest

from topicpilot_api.topic_engine import (
    EvaluationBundle,
    FeatureRuntimeConfig,
    FormulaResearchValidationError,
    ResearchBounds,
    ResearchCandidate,
    ScoringPolicy,
    TopicScorer,
    aggregate_features,
    run_formula_research,
)
from topicpilot_api.topic_engine.features.availability import availability_features
from topicpilot_api.topic_engine.features.hierarchy import hierarchy_features
from topicpilot_api.topic_engine.features.membership import membership_features


class SyntheticConstantAggregation:
    """Test-only constant; it is not a TopicPilot formula candidate."""

    def __init__(self, value):
        self.value = value

    def aggregate(self, _components, _policy):
        return self.value


def aggregates(*, include_ineligible=False):
    topics = ({"id": "b"}, {"id": "a"})
    memberships = (
        {"topic_id": "a", "instrument_id": "i1"},
        {"topic_id": "b", "instrument_id": "i2"},
    )
    observations = (
        {"topic_id": "a", "instrument_id": "i1"},
        {"topic_id": "b", "instrument_id": "i2"},
    )
    if include_ineligible:
        memberships = memberships[:1]
        observations = observations[:1]
    bundle = EvaluationBundle(
        "calc-v1",
        date(2026, 8, 8),
        topics=topics,
        memberships=memberships,
        observations=observations,
    )
    config = FeatureRuntimeConfig(
        "features-v1",
        "feature-runtime-v1",
        "aggregate-v1",
        ("membership_count",),
        (membership_features, hierarchy_features, availability_features),
    )
    result = aggregate_features(bundle, config)
    return replace(
        result,
        aggregates=tuple(
            replace(item, status="READY_UNSCORED")
            if not include_ineligible or item.topic_id == "a"
            else item
            for item in result.aggregates
        ),
    )


def candidate(
    candidate_id,
    score,
    *,
    components=None,
    grade=None,
    confidence=None,
    score_bounds=None,
    configuration=(),
):
    component_values = components or {"breadth": 25.0, "leadership": 75.0}
    scorer = TopicScorer(
        f"scorer-{candidate_id}",
        component_collector=lambda _aggregate: component_values,
        aggregation_policy=SyntheticConstantAggregation(score),
        grade_mapper=lambda _score, _policy: grade,
        confidence_provider=lambda _aggregate: confidence,
    )
    policy = ScoringPolicy(candidate_id, "v1", configuration)
    return ResearchCandidate(
        candidate_id,
        "v1",
        scorer,
        policy,
        score_bounds or ResearchBounds(0.0, 100.0),
        ResearchBounds(0.0, 100.0),
    )


def test_research_is_canonical_deterministic_and_digestible():
    first = candidate("candidate-b", 65.0, grade="A", confidence=0.7)
    second = candidate("candidate-a", 40.0, grade="B", confidence=0.9)

    result = run_formula_research(
        aggregates(), (first, second), research_runtime_version="research-v1"
    )
    reversed_result = run_formula_research(
        aggregates(), (second, first), research_runtime_version="research-v1"
    )

    assert result == reversed_result
    assert result.mode == "RESEARCH_ONLY"
    assert len(result.replay_digest) == 64
    assert [item.candidate_id for item in result.candidate_results] == [
        "candidate-a",
        "candidate-b",
    ]
    assert [item.topic_id for item in result.topic_comparisons] == ["a", "b"]
    assert result.candidate_results[0].summary.scored_count == 2
    assert result.candidate_results[0].summary.status_counts == (("SCORED", 2),)
    assert all(
        score.evidence is not None
        for item in result.candidate_results
        for score in item.runtime_result.scores
    )


def test_candidate_identity_and_uniqueness_fail_closed():
    scorer = TopicScorer("scorer-v1")
    with pytest.raises(FormulaResearchValidationError, match="candidate_id"):
        ResearchCandidate(
            " ",
            "v1",
            scorer,
            ScoringPolicy("candidate", "v1"),
            ResearchBounds(0.0, 100.0),
        )
    with pytest.raises(FormulaResearchValidationError, match="must match"):
        ResearchCandidate(
            "candidate",
            "v1",
            scorer,
            ScoringPolicy("different", "v1"),
            ResearchBounds(0.0, 100.0),
        )

    duplicate = candidate("candidate", 50.0)
    with pytest.raises(FormulaResearchValidationError, match="unique"):
        run_formula_research(
            aggregates(), (duplicate, duplicate), research_runtime_version="research-v1"
        )


def test_policy_configuration_is_part_of_replay_digest():
    first = candidate("candidate", 50.0, configuration=(("variant", "a"),))
    second = candidate("candidate", 50.0, configuration=(("variant", "b"),))

    first_result = run_formula_research(
        aggregates(), (first,), research_runtime_version="research-v1"
    )
    second_result = run_formula_research(
        aggregates(), (second,), research_runtime_version="research-v1"
    )

    assert first_result.replay_digest != second_result.replay_digest
    assert first_result.candidate_results[0].policy_configuration == (("variant", "a"),)


@pytest.mark.parametrize("bad_score", [float("nan"), float("inf"), -1.0, 101.0])
def test_non_finite_and_out_of_bounds_scores_fail_closed(bad_score):
    with pytest.raises(FormulaResearchValidationError, match="score"):
        run_formula_research(
            aggregates(),
            (candidate("candidate", bad_score),),
            research_runtime_version="research-v1",
        )


@pytest.mark.parametrize(
    ("components", "confidence", "match"),
    [
        ({"breadth": 10.0}, None, "breadth and leadership"),
        ({"breadth": 10.0, "extra": 20.0}, None, "breadth and leadership"),
        ({"breadth": float("nan"), "leadership": 20.0}, None, "finite"),
        ({"breadth": 10.0, "leadership": 20.0}, float("inf"), "confidence"),
    ],
)
def test_component_and_confidence_validation_fail_closed(components, confidence, match):
    with pytest.raises(FormulaResearchValidationError, match=match):
        run_formula_research(
            aggregates(),
            (candidate("candidate", 50.0, components=components, confidence=confidence),),
            research_runtime_version="research-v1",
        )


def test_grade_vocabulary_is_frozen_without_adding_thresholds():
    with pytest.raises(FormulaResearchValidationError, match="grade"):
        run_formula_research(
            aggregates(),
            (candidate("candidate", 50.0, grade="X"),),
            research_runtime_version="research-v1",
        )


def test_valid_zero_and_ineligible_null_remain_distinct():
    result = run_formula_research(
        aggregates(include_ineligible=True),
        (candidate("candidate", 0.0),),
        research_runtime_version="research-v1",
    )
    by_topic = {item.topic_id: item.candidates[0] for item in result.topic_comparisons}

    assert by_topic["a"].score == 0.0
    assert by_topic["a"].eligibility == "ELIGIBLE"
    assert by_topic["b"].score is None
    assert by_topic["b"].eligibility == "INELIGIBLE"
    assert by_topic["b"].components == ()
