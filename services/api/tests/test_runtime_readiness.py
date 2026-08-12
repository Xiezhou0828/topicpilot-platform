from datetime import UTC, date, datetime

import pytest

from topicpilot_api.topic_engine import (
    LEADER_SET_APPROVED,
    RUNTIME_BLOCKED,
    RUNTIME_READY,
    GovernedLeaderSet,
    LeaderDefinition,
    ObservationAsOfBinding,
    ParticipationObservation,
    ProductionTopicInput,
    ProductionV1PolicyBundle,
    RuntimeReadinessError,
    build_eligibility_audit_report,
    evaluate_activation_readiness,
)
from topicpilot_api.topic_engine.policy_approval import PolicyApprovalRecord

AS_OF = date(2026, 8, 7)


def _policy() -> ProductionV1PolicyBundle:
    return ProductionV1PolicyBundle(
        candidate_id="candidate-approved",
        candidate_version="v1",
        policy_id="topic-score-policy",
        policy_version="policy.v1",
        effective_date=date(2026, 8, 1),
        leader_set_version="leaders.v1",
        breadth_policy_ref="pm://breadth/v1",
        leadership_policy_ref="pm://leadership/v1",
        normalization_policy_ref="pm://normalization/v1",
        aggregation_policy_ref="pm://aggregation/v1",
        weights_policy_ref="pm://weights/v1",
        eligibility_policy_ref="pm://eligibility/v1",
        grade_threshold_ref="pm://grade/v1",
        rollback_policy="select-earlier-approved-version",
        lifecycle="APPROVED",
    )


def _approval() -> PolicyApprovalRecord:
    return PolicyApprovalRecord(
        decision_status="APPROVED",
        reviewed_dataset_id="dataset-1",
        reviewed_dataset_version="v1",
        reviewed_validation_runtime_version="validation.v1",
        reviewed_report_digest="a" * 64,
        approved_candidate_id="candidate-approved",
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
        limitations="runtime prerequisites remain explicit",
    )


def _topic(topic_id: str = "topic-1", *, observed: bool = True) -> ProductionTopicInput:
    return ProductionTopicInput(
        topic_id=topic_id,
        as_of=AS_OF,
        core_member_ids=("s1", "s2", "s3"),
        observations=tuple(
            ParticipationObservation(member_id, 7.0 if observed else None)
            for member_id in ("s1", "s2", "s3")
        ),
        leaders=(LeaderDefinition("s1", 1.0),),
        leader_set_version="leaders.v1",
        observation_as_of=AS_OF,
        latest_approved_session=True,
    )


def _leader_set() -> GovernedLeaderSet:
    return GovernedLeaderSet(
        version="leaders.v1",
        lifecycle=LEADER_SET_APPROVED,
        artifact_id="leader-set-artifact-v1",
        effective_date=date(2026, 8, 1),
        topic_leaders=(("topic-1", (LeaderDefinition("s1", 1.0),)),),
    )


def _binding(*, fresh: bool = True, count: int = 3) -> ObservationAsOfBinding:
    return ObservationAsOfBinding(
        query_version="canonical-price-as-of.v1",
        source_id="source-approved-v1",
        as_of=AS_OF,
        session_code="REGULAR",
        latest_approved_session=True,
        fresh=fresh,
        observation_count=count,
        input_hash="b" * 64,
        bound_at=datetime(2026, 8, 7, 8, 0, tzinfo=UTC),
    )


def test_eligibility_audit_is_replayable_and_covers_the_explicit_universe():
    report = build_eligibility_audit_report(
        (_topic(), _topic("topic-2", observed=False)), _policy()
    )

    assert report.topic_ids == ("topic-1", "topic-2")
    assert report.as_of == AS_OF
    assert report.eligible_count == 1
    assert report.ineligible_count == 1
    assert report.audits[1].valid_observed_core_count == 0


def test_activation_readiness_is_ready_only_when_every_identity_is_explicit():
    report = build_eligibility_audit_report((_topic(),), _policy())

    readiness = evaluate_activation_readiness(
        approval_record=_approval(),
        policy=_policy(),
        leader_set=_leader_set(),
        observation_binding=_binding(),
        eligibility_audit=report,
    )

    assert readiness.status == RUNTIME_READY
    assert readiness.allowed is True
    assert readiness.blockers == ()


def test_activation_readiness_reports_missing_runtime_prerequisites():
    readiness = evaluate_activation_readiness(
        approval_record=None,
        policy=None,
        leader_set=None,
        observation_binding=None,
        eligibility_audit=None,
    )

    assert readiness.status == RUNTIME_BLOCKED
    assert readiness.allowed is False
    assert readiness.blockers == (
        "APPROVAL_ARTIFACT_MISSING",
        "ELIGIBILITY_AUDIT_MISSING",
        "LEADER_SET_MISSING",
        "OBSERVATION_AS_OF_BINDING_MISSING",
        "POLICY_BUNDLE_MISSING",
    )


def test_stale_or_empty_observation_binding_blocks_activation_without_fallback():
    report = build_eligibility_audit_report((_topic(),), _policy())
    readiness = evaluate_activation_readiness(
        approval_record=_approval(),
        policy=_policy(),
        leader_set=_leader_set(),
        observation_binding=_binding(fresh=False, count=0),
        eligibility_audit=report,
    )

    assert readiness.status == RUNTIME_BLOCKED
    assert readiness.blockers == ("OBSERVATION_AS_OF_EMPTY", "OBSERVATION_AS_OF_NOT_FRESH")


def test_observation_binding_rejects_naive_bound_timestamp():
    with pytest.raises(RuntimeReadinessError, match="timezone-aware"):
        _binding().__class__(
            query_version="canonical-price-as-of.v1",
            source_id="source-approved-v1",
            as_of=AS_OF,
            session_code="REGULAR",
            latest_approved_session=True,
            fresh=True,
            observation_count=3,
            input_hash="b" * 64,
            bound_at=datetime(2026, 8, 7, 8, 0),
        )


def test_audit_rejects_partial_topic_universe():
    with pytest.raises(RuntimeReadinessError, match="complete topic universe"):
        from topicpilot_api.topic_engine.runtime_readiness import EligibilityAuditReport

        report = build_eligibility_audit_report((_topic(),), _policy())
        EligibilityAuditReport(AS_OF, ("topic-1", "topic-2"), report.audits)
