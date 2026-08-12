from datetime import date

import pytest

from topicpilot_api.topic_engine import FeatureRuntimeConfig, aggregate_features
from topicpilot_api.topic_engine.contracts import EvaluationBundle
from topicpilot_api.topic_engine.features.availability import availability_features
from topicpilot_api.topic_engine.features.hierarchy import hierarchy_features
from topicpilot_api.topic_engine.features.membership import membership_features
from topicpilot_api.topic_engine.scoring_contracts import (
    ScoringPolicy,
    deferred_score,
    scoring_input,
)


def aggregate():
    config = FeatureRuntimeConfig(
        "features-v1",
        "runtime-v1",
        "aggregate-v1",
        ("membership_count",),
        (membership_features, hierarchy_features, availability_features),
    )
    bundle = EvaluationBundle("calc-v1", date(2026, 8, 8), topics=({"id": "a"},))
    return aggregate_features(bundle, config).aggregates[0]


def test_contract_identity_and_traceability_are_deterministic():
    item = scoring_input(aggregate(), runtime_version="runtime-v1")
    policy = ScoringPolicy("topic-score", "v1", (("mode", "deferred"),))
    assert item == scoring_input(aggregate(), runtime_version="runtime-v1")
    result = deferred_score(item, policy)
    assert result.evidence == item.aggregate
    assert result.policy_id == "topic-score"
    assert result.score is None and result.grade is None


def test_contracts_are_immutable():
    with pytest.raises((AttributeError, TypeError)):
        policy = ScoringPolicy("p", "v1")
        policy.policy_id = "changed"


def test_invalid_policy_configuration_is_rejected():
    with pytest.raises(ValueError, match="policy_id"):
        ScoringPolicy(" ", "v1")
    with pytest.raises(ValueError, match="duplicates"):
        ScoringPolicy("p", "v1", (("x", "1"), ("x", "2")))
    with pytest.raises(ValueError, match="sorted"):
        ScoringPolicy("p", "v1", (("z", "1"), ("a", "2")))


def test_scoring_input_rejects_identity_mismatch():
    source = aggregate()
    with pytest.raises(ValueError, match="runtime"):
        from topicpilot_api.topic_engine.scoring_contracts import ScoringInput

        ScoringInput(
            source.topic_id,
            source.as_of,
            source.feature_set_version,
            " ",
            source.aggregation_version,
            "READY_UNSCORED",
            source,
        )
