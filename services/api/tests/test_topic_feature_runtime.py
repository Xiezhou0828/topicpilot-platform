from datetime import date

import pytest

from topicpilot_api.topic_engine import (
    AggregateStatus,
    EvaluationBundle,
    FeatureRuntimeConfig,
    aggregate_features,
)
from topicpilot_api.topic_engine.features.availability import availability_features
from topicpilot_api.topic_engine.features.hierarchy import hierarchy_features
from topicpilot_api.topic_engine.features.membership import membership_features

CALCULATORS = (membership_features, hierarchy_features, availability_features)
REQUIRED = (
    "membership_coverage",
    "membership_count",
    "hierarchy_quality",
    "observation_availability",
)


def config(
    *, feature_set_version="features-v1", runtime_version="runtime-v1",
    aggregation_version="aggregate-v1", required=REQUIRED
):
    return FeatureRuntimeConfig(
        feature_set_version, runtime_version, aggregation_version, required, CALCULATORS
    )


def bundle(**changes) -> EvaluationBundle:
    values = {
        "calculation_version": "calc-v1",
        "as_of": date(2026, 8, 8),
        "topics": ({"id": "b"}, {"id": "a"}),
        "memberships": ({"topic_id": "a", "instrument_id": "i1"},),
        "observations": ({"topic_id": "a", "instrument_id": "i1"},),
    }
    values.update(changes)
    return EvaluationBundle(**values)


def test_runtime_and_aggregation_are_deterministic_and_canonically_grouped():
    first = aggregate_features(bundle(), config())
    assert first == aggregate_features(bundle(), config())
    assert [item.topic_id for item in first.aggregates] == ["a", "b"]
    assert all(
        item.feature_results
        == tuple(sorted(item.feature_results, key=lambda r: (r.feature_name, r.feature_version)))
        for item in first.aggregates
    )


def test_versions_change_identity_without_changing_feature_evidence():
    first = aggregate_features(
        bundle(),
        config(),
    )
    changed = aggregate_features(
        bundle(), config(runtime_version="runtime-v2")
    )
    assert first != changed
    assert tuple(item.feature_results for item in first.aggregates) == tuple(
        item.feature_results for item in changed.aggregates
    )
    assert first.runtime_version == "runtime-v1"
    assert changed.runtime_version == "runtime-v2"


def test_required_invalid_input_propagates_but_optional_invalid_does_not_block():
    invalid_bundle = bundle(hierarchy=({"parent_id": "a", "child_id": "missing"},))
    assert (
        aggregate_features(invalid_bundle, config()).aggregates[0].status
        == AggregateStatus.INVALID_INPUT
    )
    optional = aggregate_features(invalid_bundle, config(required=())).aggregates[0]
    assert optional.status == AggregateStatus.READY_UNSCORED


def test_required_insufficient_data_and_ready_statuses_are_explicit():
    insufficient = aggregate_features(
        bundle(), config(required=("membership_coverage",))
    ).aggregates[1]
    assert insufficient.status == AggregateStatus.DATA_INSUFFICIENT
    ready = aggregate_features(bundle(), config()).aggregates[0]
    assert ready.status == AggregateStatus.READY_UNSCORED
    assert all(
        getattr(ready, field) is None
        for field in ("score", "grade", "strength")
        if hasattr(ready, field)
    )


def test_required_feature_configuration_is_validated():
    with pytest.raises(ValueError, match="duplicates"):
        config(required=("membership_count", "membership_count"))
    with pytest.raises(ValueError, match="not produced"):
        config(required=("not_a_feature",))
    with pytest.raises(ValueError, match="aggregation_version"):
        config(aggregation_version=" ")


def test_empty_topic_bundle_validates_catalogue_and_returns_empty_result():
    result = aggregate_features(bundle(topics=(), memberships=(), observations=()), config())
    assert result.aggregates == ()
