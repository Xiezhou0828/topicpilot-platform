from dataclasses import replace
from datetime import date

import pytest

from topicpilot_api.topic_engine import (
    ALLOWED,
    APPROVED,
    BLOCKED,
    PolicyApprovalError,
    PolicyApprovalRecord,
    evaluate_policy_approval,
    export_policy_approval_artifact,
    parse_policy_approval_artifact,
    require_policy_approval,
)
from topicpilot_api.topic_engine.policy_approval import PolicyApprovalArtifactError


def _record() -> PolicyApprovalRecord:
    return PolicyApprovalRecord(
        decision_status=APPROVED,
        reviewed_dataset_id="validation-demo",
        reviewed_dataset_version="v1",
        reviewed_validation_runtime_version="validator.v1",
        reviewed_report_digest="a" * 64,
        approved_candidate_id="candidate-a",
        approved_candidate_version="v1",
        approved_policy_version="policy.v1",
        approved_effective_date=date(2026, 8, 9),
        approved_scope="production",
        approved_breadth_policy="pm://breadth/approved/v1",
        approved_leadership_policy="pm://leadership/approved/v1",
        approved_normalization_policy="pm://normalization/approved/v1",
        approved_aggregation_policy="pm://aggregation/approved/v1",
        approved_weights="pm://weights/approved/v1",
        approved_eligibility_policy="pm://eligibility/approved/v1",
        approved_grade_thresholds="pm://grade/approved/v1",
        rollback_policy="rollback-to-previous-approved-policy",
        owner="product-owner",
        decision_rationale="reviewed historical evidence",
        limitations="limited reviewed sample",
    )


def test_complete_approved_production_record_is_allowed() -> None:
    decision = evaluate_policy_approval(_record())

    assert decision == decision.__class__(True, ALLOWED, "APPROVED", decision.reason)
    assert require_policy_approval(_record()).allowed is True


@pytest.mark.parametrize(
    ("field", "value", "reason_code"),
    (
        ("decision_status", "REJECTED", "DECISION_NOT_APPROVED"),
        ("approved_scope", "staging", "NON_PRODUCTION_SCOPE"),
        ("reviewed_report_digest", "not-a-digest", "INVALID_REPORT_DIGEST"),
        ("approved_policy_version", None, "MISSING_POLICY_IDENTITY"),
        ("approved_breadth_policy", None, "MISSING_POLICY_REFERENCE"),
        ("approved_effective_date", None, "MISSING_EFFECTIVE_DATE"),
        ("rollback_policy", None, "MISSING_GOVERNANCE_METADATA"),
    ),
)
def test_guard_blocks_invalid_or_incomplete_records(
    field: str, value: object, reason_code: str
) -> None:
    decision = evaluate_policy_approval(replace(_record(), **{field: value}))

    assert decision.status == BLOCKED
    assert decision.allowed is False
    assert decision.reason_code == reason_code


def test_schema_mismatch_is_fail_closed() -> None:
    decision = evaluate_policy_approval(replace(_record(), schema_version="v0"))

    assert decision.reason_code == "SCHEMA_MISMATCH"
    assert not decision.allowed


def test_require_raises_stable_error_for_blocked_record() -> None:
    with pytest.raises(PolicyApprovalError, match="NON_PRODUCTION_SCOPE") as exc_info:
        require_policy_approval(replace(_record(), approved_scope="staging"))

    assert exc_info.value.reason_code == "NON_PRODUCTION_SCOPE"


def test_same_record_produces_same_decision_and_opaque_references_are_not_parsed() -> None:
    first = evaluate_policy_approval(_record())
    second = evaluate_policy_approval(_record())

    assert first == second
    assert first.allowed


def test_approval_artifact_round_trips_and_composes_with_guard() -> None:
    artifact = export_policy_approval_artifact(_record())
    parsed = parse_policy_approval_artifact(artifact)

    assert parsed == _record()
    assert evaluate_policy_approval(parsed).allowed
    assert artifact["approved_effective_date"] == "2026-08-09"


@pytest.mark.parametrize(
    ("mutation", "reason_code"),
    (
        (lambda payload: payload.pop("owner"), "MISSING_FIELD"),
        (lambda payload: payload.__setitem__("unexpected", "value"), "UNKNOWN_FIELD"),
        (
            lambda payload: payload.__setitem__("approved_effective_date", "2026-99-99"),
            "INVALID_DATE",
        ),
        (lambda payload: payload.__setitem__("approved_weights", 0.5), "INVALID_FIELD_TYPE"),
    ),
)
def test_artifact_parser_fails_closed_for_invalid_payloads(mutation, reason_code: str) -> None:
    payload = export_policy_approval_artifact(_record())
    mutation(payload)

    with pytest.raises(PolicyApprovalArtifactError) as exc_info:
        parse_policy_approval_artifact(payload)

    assert exc_info.value.reason_code == reason_code


def test_artifact_parser_preserves_none_without_defaulting() -> None:
    payload = export_policy_approval_artifact(_record())
    payload["approved_policy_version"] = None
    parsed = parse_policy_approval_artifact(payload)

    assert parsed.approved_policy_version is None
    assert evaluate_policy_approval(parsed).reason_code == "MISSING_POLICY_IDENTITY"
