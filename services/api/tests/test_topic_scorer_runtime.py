from dataclasses import replace
from datetime import date

from topicpilot_api.topic_engine import (
    FeatureRuntimeConfig,
    TopicScorer,
    aggregate_features,
)
from topicpilot_api.topic_engine.contracts import EvaluationBundle
from topicpilot_api.topic_engine.features.availability import availability_features
from topicpilot_api.topic_engine.features.hierarchy import hierarchy_features
from topicpilot_api.topic_engine.features.membership import membership_features
from topicpilot_api.topic_engine.scoring_contracts import ScoringPolicy


def make_aggregate():
    config = FeatureRuntimeConfig(
        "features-v1",
        "runtime-v1",
        "aggregate-v1",
        ("membership_count",),
        (membership_features, hierarchy_features, availability_features),
    )
    bundle = EvaluationBundle("calc-v1", date(2026, 8, 8), topics=({"id": "a"},))
    return aggregate_features(bundle, config).aggregates[0]


def test_default_runtime_is_pluggable_and_deferred():
    aggregate = replace(make_aggregate(), status="READY_UNSCORED")
    result = TopicScorer("scorer-v1").score(aggregate, ScoringPolicy("topic", "v1"))
    assert result.status == "DEFERRED"
    assert result.eligibility == "ELIGIBLE"
    assert result.components == (("breadth", None), ("leadership", None))
    assert result.score is None and result.grade is None and result.confidence is None


def test_ineligible_aggregate_is_gate_before_policy():
    aggregate = make_aggregate()
    policy = ScoringPolicy("topic", "v1")
    calls = []

    def collector(_aggregate):
        calls.append("collector")
        return {"breadth": 1.0}

    def confidence(_aggregate):
        calls.append("confidence")
        return 0.9

    class Aggregator:
        def aggregate(self, _components, _policy):
            calls.append("aggregation")
            return 1.0

    def grade(_score, _policy):
        calls.append("grade")
        return "A"

    result = TopicScorer(
        "scorer-v1",
        component_collector=collector,
        aggregation_policy=Aggregator(),
        grade_mapper=grade,
        confidence_provider=confidence,
    ).score(aggregate, policy)
    assert result.evidence == aggregate
    assert result.status == "DATA_INSUFFICIENT"
    assert result.eligibility == "INELIGIBLE"
    assert result.score is None and result.grade is None and result.confidence is None
    assert result.components == ()
    assert calls == []


def test_eligible_deferred_path_collects_and_provides_confidence_after_gate():
    aggregate = replace(make_aggregate(), status="READY_UNSCORED")
    calls = []

    def collector(_aggregate):
        calls.append("collector")
        return {"breadth": None, "leadership": None}

    def confidence(_aggregate):
        calls.append("confidence")
        return 0.7

    result = TopicScorer(
        "scorer-v1",
        component_collector=collector,
        confidence_provider=confidence,
    ).score(aggregate, ScoringPolicy("topic", "v1"))

    assert result.status == "DEFERRED"
    assert result.eligibility == "ELIGIBLE"
    assert result.score is None and result.grade is None
    assert result.confidence == 0.7
    assert calls == ["collector", "confidence"]
