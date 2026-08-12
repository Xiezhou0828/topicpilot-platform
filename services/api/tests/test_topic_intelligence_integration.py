from datetime import date

from topicpilot_api.topic_engine import (
    EvaluationBundle,
    FeatureRuntimeConfig,
    ScoringPolicy,
    TopicScorer,
    aggregate_features,
    run_topic_intelligence,
)
from topicpilot_api.topic_engine.features.availability import availability_features
from topicpilot_api.topic_engine.features.hierarchy import hierarchy_features
from topicpilot_api.topic_engine.features.membership import membership_features


def test_integration_is_deterministic_and_traceable():
    config = FeatureRuntimeConfig(
        "features-v1",
        "feature-runtime-v1",
        "aggregate-v1",
        ("membership_count",),
        (membership_features, hierarchy_features, availability_features),
    )
    bundle = EvaluationBundle("calc-v1", date(2026, 8, 8), topics=({"id": "b"}, {"id": "a"}))
    aggregates = aggregate_features(bundle, config)
    result = run_topic_intelligence(
        aggregates, TopicScorer("scorer-runtime-v1"), ScoringPolicy("topic-policy", "v1")
    )
    assert result == run_topic_intelligence(
        aggregates, TopicScorer("scorer-runtime-v1"), ScoringPolicy("topic-policy", "v1")
    )
    assert [score.topic_id for score in result.scores] == ["a", "b"]
    assert result.feature_runtime_version == "feature-runtime-v1"
    assert result.scorer_runtime_version == "scorer-runtime-v1"
    assert all(score.status in {"DEFERRED", "DATA_INSUFFICIENT"} for score in result.scores)


def test_integration_keeps_ineligible_topics_out_of_collectors():
    config = FeatureRuntimeConfig(
        "features-v1",
        "feature-runtime-v1",
        "aggregate-v1",
        ("membership_count",),
        (membership_features, hierarchy_features, availability_features),
    )
    bundle = EvaluationBundle(
        "calc-v1",
        date(2026, 8, 8),
        topics=({"id": "ready"}, {"id": "thin"}),
        memberships=({"topic_id": "ready", "instrument_id": "i1"},),
        observations=({"topic_id": "ready", "instrument_id": "i1"},),
    )
    calls = []

    def collector(_aggregate):
        calls.append("collector")
        return {"breadth": None, "leadership": None}

    result = run_topic_intelligence(
        aggregate_features(bundle, config),
        TopicScorer("scorer-runtime-v1", component_collector=collector),
        ScoringPolicy("topic-policy", "v1"),
    )
    by_topic = {score.topic_id: score for score in result.scores}
    assert by_topic["ready"].eligibility == "ELIGIBLE"
    assert by_topic["thin"].eligibility == "INELIGIBLE"
    assert calls == ["collector"]
