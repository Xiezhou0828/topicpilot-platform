from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from topicpilot_api.topic_engine import (
    POLICY_APPROVED,
    LeaderDefinition,
    ParticipationObservation,
    ProductionPolicyError,
    ProductionTopicInput,
    ProductionV1PolicyBundle,
    TopicIntelligenceRuntimeResult,
    classify_participation,
    evaluate_production_v1,
    grade_for_score,
    normalize_absolute,
    select_rollback,
)
from topicpilot_api.topic_engine.policy_approval import PolicyApprovalRecord
from topicpilot_api.topic_intelligence_api import serialize_topic_intelligence

AS_OF = date(2026, 8, 7)


def policy(
    version: str = "policy.v1", effective_date: date = date(2026, 8, 1)
) -> ProductionV1PolicyBundle:
    return ProductionV1PolicyBundle(
        candidate_id="approved-candidate",
        candidate_version="v1",
        policy_id="topic-score-policy",
        policy_version=version,
        effective_date=effective_date,
        leader_set_version="leaders.v1",
        breadth_policy_ref="pm://breadth/v1",
        leadership_policy_ref="pm://leadership/v1",
        normalization_policy_ref="pm://normalization/v1",
        aggregation_policy_ref="pm://aggregation/v1",
        weights_policy_ref="pm://weights/v1",
        eligibility_policy_ref="pm://eligibility/v1",
        grade_threshold_ref="pm://grade/v1",
        rollback_policy="select-earlier-approved-version",
        lifecycle=POLICY_APPROVED,
    )


def topic_input(
    returns: tuple[float | None, ...],
    *,
    latest: bool = True,
    observation_as_of: date | None = AS_OF,
    leaders: tuple[LeaderDefinition, ...] = (
        LeaderDefinition("s1", 1.0),
        LeaderDefinition("s2", 0.75),
        LeaderDefinition("s3", 0.5),
    ),
    leader_returns: dict[str, float | None] | None = None,
) -> ProductionTopicInput:
    core_ids = tuple(f"s{index}" for index in range(1, len(returns) + 1))
    values = dict(zip(core_ids, returns, strict=True))
    if leader_returns:
        values.update(leader_returns)
    return ProductionTopicInput(
        topic_id="topic-1",
        as_of=AS_OF,
        core_member_ids=core_ids,
        observations=tuple(
            ParticipationObservation(member_id, value) for member_id, value in values.items()
        ),
        leaders=leaders,
        leader_set_version="leaders.v1",
        observation_as_of=observation_as_of,
        latest_approved_session=latest,
    )


def test_participation_boundaries_are_exact() -> None:
    assert classify_participation(7.0) == "STRONG_POSITIVE"
    assert classify_participation(6.999) == "POSITIVE"
    assert classify_participation(2.0) == "POSITIVE"
    assert classify_participation(1.999) == "NEUTRAL"
    assert classify_participation(-2.0) == "NEGATIVE"
    assert classify_participation(-7.0) == "STRONG_NEGATIVE"
    assert classify_participation(-6.999) == "NEGATIVE"
    assert classify_participation(None) is None


def test_normalization_and_grade_boundaries_are_frozen() -> None:
    assert normalize_absolute(-1.0) == 0.0
    assert normalize_absolute(-0.5) == 25.0
    assert normalize_absolute(0.0) == 50.0
    assert normalize_absolute(0.5) == 75.0
    assert normalize_absolute(1.0) == 100.0
    assert normalize_absolute(0.25) == 62.5
    assert grade_for_score(80.0) == "S"
    assert grade_for_score(79.999) == "A"
    assert grade_for_score(65.0) == "A"
    assert grade_for_score(64.999) == "B"
    assert grade_for_score(50.0) == "B"
    assert grade_for_score(49.999) == "D"
    with pytest.raises(ProductionPolicyError):
        normalize_absolute(1.01)


def test_production_v1_scores_breadth_and_leadership_with_lineage() -> None:
    result = evaluate_production_v1(
        topic_input((7.0, 2.0, 0.0, -2.0, -7.0)),
        policy(),
    )

    assert result.eligibility_audit.eligible is True
    assert result.eligibility_audit.core_coverage == 1.0
    assert result.breadth_raw == 0.0
    assert result.breadth_score == 50.0
    assert result.leadership_score is not None
    assert result.score.status == "SCORED"
    assert result.score.eligibility == "ELIGIBLE"
    assert result.score.policy_id == "topic-score-policy"
    assert result.score.policy_version == "policy.v1"
    assert result.policy.candidate_id == "approved-candidate"
    assert result.policy.weights_policy_ref == "pm://weights/v1"
    assert result.score.grade in {"S", "A", "B", "D"}
    assert result.score.evidence is not None
    assert {item.feature_name for item in result.score.evidence.feature_results} == {
        "production_breadth",
        "production_leadership",
    }


def test_production_evidence_satisfies_the_existing_api_contract():
    result = evaluate_production_v1(topic_input((7.0, 2.0, 0.0)), policy())
    runtime = TopicIntelligenceRuntimeResult(
        AS_OF,
        "production-v1",
        "production-v1",
        result.policy.aggregation_policy_ref,
        "production-v1",
        result.policy.policy_id,
        result.policy.policy_version,
        (result.score,),
    )

    body = serialize_topic_intelligence(runtime)

    assert body["status"] == "AVAILABLE"
    assert body["topics"][0]["evidence"]["features"]


def test_eligibility_is_fail_closed_and_missing_is_not_zero() -> None:
    result = evaluate_production_v1(
        topic_input((7.0, None, None, -2.0, None), latest=False),
        policy(),
    )

    assert result.score.status == "INELIGIBLE"
    assert result.score.score is None
    assert result.score.grade is None
    assert result.score.eligibility == "INELIGIBLE"
    assert result.eligibility_audit.eligible is False
    assert result.eligibility_audit.valid_observed_core_count == 2
    assert "CORE_COVERAGE_BELOW_60_PERCENT" in result.eligibility_audit.excluded_reasons
    assert "VALID_OBSERVED_CORE_COUNT_BELOW_3" in result.eligibility_audit.excluded_reasons
    assert "LATEST_APPROVED_AS_OF_EVIDENCE_MISSING" in result.eligibility_audit.excluded_reasons


def test_leader_partialness_disables_consensus_but_not_eligibility() -> None:
    leaders = (
        LeaderDefinition("l1", 1.0),
        LeaderDefinition("l2", 1.0),
        LeaderDefinition("l3", 1.0),
    )
    result = evaluate_production_v1(
        topic_input(
            (7.0, 7.0, 7.0, 7.0),
            leaders=leaders,
            leader_returns={"l1": 7.0},
        ),
        policy(),
    )

    assert result.score.status == "SCORED"
    assert result.score.eligibility == "ELIGIBLE"
    assert result.leader_weight_coverage == pytest.approx(1 / 3)
    assert result.consensus_modifier == 0.0
    assert "INSUFFICIENT_LEADER_WEIGHT_COVERAGE" in result.quality_flags


def test_effective_date_is_a_fail_closed_policy_gate() -> None:
    result = evaluate_production_v1(
        topic_input((7.0, 7.0, 7.0)),
        policy(effective_date=date(2026, 8, 8)),
    )

    assert result.score.status == "INELIGIBLE"
    assert result.score.score is None
    assert "POLICY_NOT_EFFECTIVE" in result.eligibility_audit.excluded_reasons


def test_rollback_selects_an_earlier_approved_policy_without_mutation() -> None:
    current = policy("policy.v2", date(2026, 8, 5))
    prior = policy("policy.v1", date(2026, 8, 1))

    selected = select_rollback(current, (prior,), "policy.v1")

    assert selected == prior
    assert current.policy_version == "policy.v2"
    with pytest.raises(ProductionPolicyError):
        select_rollback(current, (replace(prior, lifecycle="CANDIDATE"),), "policy.v1")


def test_bundle_can_be_constructed_only_from_complete_approval_artifact() -> None:
    record = PolicyApprovalRecord(
        decision_status="APPROVED",
        reviewed_dataset_id="dataset-1",
        reviewed_dataset_version="v1",
        reviewed_validation_runtime_version="validation.v1",
        reviewed_report_digest="a" * 64,
        approved_candidate_id="approved-candidate",
        approved_candidate_version="v1",
        approved_policy_version="policy.v1",
        approved_effective_date=date(2026, 8, 1),
        approved_scope="production",
        approved_breadth_policy="pm://breadth/v1",
        approved_leadership_policy="pm://leadership/v1",
        approved_normalization_policy="pm://normalization/v1",
        approved_aggregation_policy="pm://aggregation/v1",
        approved_weights="pm://weights/v1",
        approved_eligibility_policy="pm://eligibility/v1",
        approved_grade_thresholds="pm://grade/v1",
        rollback_policy="select-earlier-approved-version",
        owner="pm",
        decision_rationale="approved mechanics",
        limitations="activation prerequisites remain",
    )

    bundle = ProductionV1PolicyBundle.from_approval(
        record,
        policy_id="topic-score-policy",
        leader_set_version="leaders.v1",
    )

    assert bundle.lifecycle == POLICY_APPROVED
    assert bundle.policy_version == "policy.v1"
    assert bundle.weights_policy_ref == "pm://weights/v1"
    with pytest.raises(ProductionPolicyError):
        ProductionV1PolicyBundle(
            **{**bundle.__dict__, "lifecycle": "UNKNOWN"},
        )
