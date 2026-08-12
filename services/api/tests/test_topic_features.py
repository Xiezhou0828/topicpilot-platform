from datetime import date

import pytest

from topicpilot_api.topic_engine import EvaluationBundle, FeatureStatus, evaluate, evaluate_features


def bundle() -> EvaluationBundle:
    return EvaluationBundle(
        "v0",
        date(2026, 8, 8),
        topics=({"id": "root"}, {"id": "child"}),
        hierarchy=({"parent_id": "root", "child_id": "child"},),
        memberships=(
            {"topic_id": "child", "instrument_id": "i1"},
            {"topic_id": "child", "instrument_id": "i1"},
        ),
        observations=({"topic_id": "child", "instrument_id": "i1"},),
    )


def test_features_are_stable_and_topic_state_coverage_is_in_parity() -> None:
    first = evaluate_features(bundle())
    assert first == evaluate_features(bundle())
    assert first.feature_set_version == "topic-features-v1"
    assert [(item.topic_id, item.feature_name) for item in first.results] == sorted(
        (item.topic_id, item.feature_name) for item in first.results
    )
    coverage = next(
        item
        for item in first.results
        if item.feature_name == "membership_coverage" and item.topic_id == "root"
    )
    assert coverage.value == evaluate(bundle())[0].coverage == 1


def test_counts_deduplicate_and_empty_is_explicit_without_scores() -> None:
    results = evaluate_features(
        EvaluationBundle("v0", date(2026, 8, 8), topics=({"id": "a"},))
    ).results
    count = next(item for item in results if item.feature_name == "membership_count")
    assert count.value == {
        "direct_member_count": 0,
        "rolled_up_member_count": 0,
        "observed_member_count": 0,
    }
    assert count.status == "DATA_INSUFFICIENT"
    assert all(item.value is None or item.feature_name != "score" for item in results)


def test_hierarchy_quality_flags_missing_reference_and_cycle() -> None:
    results = evaluate_features(
        EvaluationBundle(
            "v0",
            date(2026, 8, 8),
            topics=({"id": "a"},),
            hierarchy=(
                {"parent_id": "a", "child_id": "missing"},
                {"parent_id": "a", "child_id": "a"},
            ),
        )
    ).results
    quality = next(item for item in results if item.feature_name == "hierarchy_quality")
    assert quality.status == "INVALID_INPUT"
    assert quality.quality_flags == ("HIERARCHY_CYCLE", "MISSING_HIERARCHY_REFERENCE")
    availability = next(item for item in results if item.feature_name == "observation_availability")
    assert availability.status == FeatureStatus.INVALID_INPUT


def test_evaluation_identity_is_explicit_and_versioned() -> None:
    first = evaluate_features(bundle(), feature_set_version="v1")
    same = evaluate_features(bundle(), feature_set_version="v1")
    changed = evaluate_features(bundle(), feature_set_version="v2")
    assert first == same
    assert first.as_of == bundle().as_of
    assert first.results == changed.results
    assert first.feature_set_version != changed.feature_set_version


@pytest.mark.parametrize("version", ["", "   "])
def test_blank_feature_set_version_is_rejected(version: str) -> None:
    with pytest.raises(ValueError):
        evaluate_features(bundle(), feature_set_version=version)


def test_availability_status_distinguishes_observed_and_unobserved_topics() -> None:
    results = evaluate_features(
        EvaluationBundle(
            "v0",
            date(2026, 8, 8),
            topics=({"id": "observed"}, {"id": "unobserved"}),
            observations=({"topic_id": "observed", "instrument_id": "i1"},),
        )
    ).results
    by_topic = {
        item.topic_id: item
        for item in results
        if item.feature_name == "observation_availability"
    }
    assert by_topic["observed"].status == FeatureStatus.READY
    assert by_topic["unobserved"].status == FeatureStatus.DATA_INSUFFICIENT
