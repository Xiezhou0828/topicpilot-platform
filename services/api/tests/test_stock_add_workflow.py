from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from topicpilot_api.company_profile_v4.store import approval_content_sha256
from topicpilot_api.stock_add_workflow import (
    MASTER_MATCH_FOUND,
    MASTER_NO_MATCH,
    MASTER_RETRIEVAL_BLOCKED,
    TOPIC_CONFLICT,
    TOPIC_INFERENCE,
    TOPIC_INSUFFICIENT,
    TOPIC_OFFICIAL_ADJACENT,
    TOPIC_OFFICIAL_CORE,
    AuthorityReadEvidence,
    StockAddWorkflowError,
    TopicAssessment,
    build_stock_add_plan,
    new_operation,
    operation_from_record,
    operation_to_record,
    record_checkpoint,
    verify_final_confirmation,
)

OFFICIAL_URL = "https://company.example/annual-report.pdf"


def _read_evidence(digest_char: str) -> AuthorityReadEvidence:
    return AuthorityReadEvidence(
        source="TopicPilot V2 formal read API",
        environment="PRODUCTION_READ_ONLY",
        read_at=datetime.now(UTC).isoformat(timespec="seconds"),
        complete=True,
        sha256=digest_char * 64,
    )


def _published_package(stock_code: str = "2468") -> dict:
    package = {
        "packageVersion": "topicpilot-stock-research.v4",
        "company": {"stockCode": stock_code, "displayName": "華經"},
        "sourceRegister": [
            {"evidenceId": "SOURCE-1", "url": "https://company.example/annual-report.pdf"}
        ],
        "frontendProjection": {
            "contractVersion": "company-research-frontend.v4",
            "researchGovernance": {
                "dataCompletenessScore": 0.72,
                "publication": {
                    "publicationStatus": "PUBLISHED",
                    "ownerReviewStatus": "APPROVED",
                    "sourceRightsStatus": "APPROVED",
                    "blockingIssues": [],
                    "approvalEvidence": {
                        "decisionId": "decision-1",
                        "reviewer": "owner",
                        "approvedAt": "2026-10-25T00:00:00Z",
                    },
                }
            },
            "investmentThemes": [],
        },
    }
    publication = package["frontendProjection"]["researchGovernance"]["publication"]
    publication["approvalEvidence"]["packageSha256"] = ""
    publication["approvalEvidence"]["packageSha256"] = approval_content_sha256(package)
    return package


def _assessment(
    basis: str,
    *,
    topic_id: str | None = "t-1",
    slug: str | None = "cloud",
) -> TopicAssessment:
    return TopicAssessment(
        topic_id=topic_id,
        slug=slug,
        name="雲端整合服務",
        evidence_basis=basis,
        evidence_summary="年報列示該服務為公司現行業務。",
        source_urls=(OFFICIAL_URL,),
    )


def _ready_plan(**overrides):
    params = {
        "stock_code": "2468",
        "market": "TPE",
        "package": _published_package(),
        "master_status": MASTER_NO_MATCH,
        "master_read_evidence": _read_evidence("a"),
        "topic_catalog_status": "READY",
        "topic_catalog_read_evidence": _read_evidence("b"),
        "assessments": (_assessment(TOPIC_OFFICIAL_CORE),),
        "reference_bundle_sha256": "c" * 64,
    }
    params.update(overrides)
    return build_stock_add_plan(**params)


def test_retrieval_blocked_never_becomes_an_add_candidate() -> None:
    plan = _ready_plan(
        master_status=MASTER_RETRIEVAL_BLOCKED,
        master_read_evidence=None,
    )
    assert plan.plan_status == "MASTER_CHECK_BLOCKED"
    assert plan.final_confirmation is None
    assert len(plan.topic_decisions) == 1
    assert plan.topic_decisions[0].decision == "RELATION_CANDIDATE"
    with pytest.raises(StockAddWorkflowError, match="PLAN_NOT_READY"):
        new_operation(plan)


def test_non_production_or_incomplete_master_read_cannot_confirm_absence() -> None:
    stale_snapshot = AuthorityReadEvidence(
        source="maintenance workbook snapshot",
        environment="PRODUCTION_READ_ONLY",
        read_at="2026-09-27T10:54:11Z",
        complete=True,
        sha256="a" * 64,
    )
    plan = _ready_plan(master_read_evidence=stale_snapshot)
    assert plan.plan_status == "MASTER_CHECK_BLOCKED"
    assert plan.final_confirmation is None


def test_expired_formal_read_cannot_confirm_master_absence() -> None:
    expired_read = AuthorityReadEvidence(
        source="TopicPilot V2 formal read API",
        environment="PRODUCTION_READ_ONLY",
        read_at=(datetime.now(UTC) - timedelta(minutes=16)).isoformat(),
        complete=True,
        sha256="a" * 64,
    )
    plan = _ready_plan(master_read_evidence=expired_read)
    assert plan.plan_status == "MASTER_CHECK_BLOCKED"
    assert plan.final_confirmation is None


def test_existing_master_match_stops_add() -> None:
    plan = _ready_plan(master_status=MASTER_MATCH_FOUND)
    assert plan.plan_status == "MASTER_MATCH_FOUND"
    assert plan.final_confirmation is None
    assert plan.topic_decisions == ()


def test_confirmed_master_absence_is_expected_add_entry_and_runs_topic_comparison() -> None:
    plan = _ready_plan(assessments=(_assessment(TOPIC_OFFICIAL_CORE),))

    assert plan.master_status == MASTER_NO_MATCH
    assert plan.plan_status == "FINAL_APPROVAL_PENDING"
    assert len(plan.topic_decisions) == 1
    assert plan.topic_decisions[0].decision == "RELATION_CANDIDATE"
    assert plan.topic_decisions[0].relation_type == "PRIMARY"


def test_research_score_above_threshold_uses_standing_publication_policy() -> None:
    package = _published_package()
    publication = package["frontendProjection"]["researchGovernance"]["publication"]
    publication.update(
        {
            "publicationStatus": "UNPUBLISHED",
            "ownerReviewStatus": "PENDING",
            "approvalEvidence": None,
        }
    )
    plan = _ready_plan(package=package)
    assert plan.research_status == "RESEARCH_READY"
    assert plan.plan_status == "FINAL_APPROVAL_PENDING"


def test_research_package_at_policy_threshold_still_requires_publication_review() -> None:
    package = _published_package()
    governance = package["frontendProjection"]["researchGovernance"]
    publication = governance["publication"]
    governance["dataCompletenessScore"] = 0.70
    publication.update(
        {
            "publicationStatus": "UNPUBLISHED",
            "ownerReviewStatus": "PENDING",
            "approvalEvidence": None,
        }
    )
    plan = _ready_plan(package=package)
    assert plan.research_status == "RESEARCH_REVIEW_REQUIRED"
    assert plan.plan_status == "RESEARCH_REVIEW_REQUIRED"


def test_draft_research_still_compares_against_current_topic_catalog() -> None:
    package = _published_package()
    publication = package["frontendProjection"]["researchGovernance"]["publication"]
    publication.update(
        {
            "publicationStatus": "UNPUBLISHED",
            "ownerReviewStatus": "PENDING",
            "sourceRightsStatus": "UNVERIFIED",
            "approvalEvidence": None,
        }
    )

    plan = _ready_plan(package=package)

    assert plan.research_status == "RESEARCH_REVIEW_REQUIRED"
    assert plan.plan_status == "RESEARCH_REVIEW_REQUIRED"
    assert len(plan.topic_decisions) == 1
    assert plan.topic_decisions[0].decision == "RELATION_CANDIDATE"
    assert plan.final_confirmation is None


@pytest.mark.parametrize(
    ("basis", "relation_type", "weight"),
    [
        (TOPIC_OFFICIAL_CORE, "PRIMARY", 1.0),
        (TOPIC_OFFICIAL_ADJACENT, "SECONDARY", 0.5),
    ],
)
def test_fixed_official_evidence_mapping(basis: str, relation_type: str, weight: float) -> None:
    plan = _ready_plan(assessments=(_assessment(basis),))
    decision = plan.topic_decisions[0]
    assert decision.decision == "RELATION_CANDIDATE"
    assert decision.relation_type == relation_type
    assert decision.weight == weight


@pytest.mark.parametrize("basis", [TOPIC_INFERENCE, TOPIC_CONFLICT, TOPIC_INSUFFICIENT])
def test_inference_conflict_or_missing_evidence_is_suggestion_only(basis: str) -> None:
    plan = _ready_plan(assessments=(_assessment(basis),))
    decision = plan.topic_decisions[0]
    assert decision.decision == "SUGGESTION_ONLY"
    assert decision.relation_type is None
    assert decision.weight is None


def test_no_formal_topic_match_is_a_suggestion_not_a_topic_creation() -> None:
    suggestion = _assessment(TOPIC_OFFICIAL_CORE, topic_id=None, slug=None)
    plan = _ready_plan(assessments=(suggestion,))
    decision = plan.topic_decisions[0]
    assert decision.decision == "SUGGESTION_ONLY"
    assert decision.reason == "TOPIC_NOT_CONFIRMED_ACTIVE_IN_FORMAL_CATALOG"
    assert decision.topic_id is None
    assert decision.weight is None


def test_duplicate_topic_assessments_are_collapsed_and_conflicts_stay_suggestions() -> None:
    duplicate = _assessment(TOPIC_OFFICIAL_CORE)
    plan = _ready_plan(assessments=(duplicate, duplicate))
    assert len(plan.topic_decisions) == 1
    assert plan.topic_decisions[0].relation_type == "PRIMARY"

    conflicting = _assessment(TOPIC_OFFICIAL_ADJACENT)
    plan = _ready_plan(assessments=(duplicate, conflicting))
    assert len(plan.topic_decisions) == 1
    assert plan.topic_decisions[0].decision == "SUGGESTION_ONLY"
    assert plan.topic_decisions[0].weight is None


def test_catalog_read_blocked_suppresses_all_relation_candidates() -> None:
    plan = _ready_plan(
        topic_catalog_status="RETRIEVAL_BLOCKED",
        topic_catalog_read_evidence=None,
    )
    assert plan.plan_status == "TOPIC_CATALOG_BLOCKED"
    assert plan.master_status == MASTER_NO_MATCH
    assert plan.topic_decisions == ()
    assert plan.final_confirmation is None


def test_final_confirmation_is_bound_to_exact_digest() -> None:
    plan = _ready_plan()
    assert plan.plan_status == "FINAL_APPROVAL_PENDING"
    verify_final_confirmation(plan, plan.final_confirmation or "")
    with pytest.raises(StockAddWorkflowError, match="HASH_MISMATCH"):
        verify_final_confirmation(plan, "APPLY STOCK ADD 2468 " + "0" * 64)


def test_operation_checkpoints_are_idempotent_ordered_and_hash_bound() -> None:
    plan = _ready_plan()
    operation = new_operation(plan)
    first = record_checkpoint(
        operation,
        plan_sha256=plan.plan_sha256,
        stage="MASTER_DATA_VERIFIED",
        status="PASS",
        artifact_sha256="d" * 64,
    )
    assert (
        record_checkpoint(
            first,
            plan_sha256=plan.plan_sha256,
            stage="MASTER_DATA_VERIFIED",
            status="PASS",
            artifact_sha256="d" * 64,
        )
        == first
    )
    with pytest.raises(StockAddWorkflowError, match="OUT_OF_ORDER"):
        record_checkpoint(
            first,
            plan_sha256=plan.plan_sha256,
            stage="POST_CLOSE_VERIFIED",
            status="PASS",
            artifact_sha256="e" * 64,
        )
    with pytest.raises(StockAddWorkflowError, match="HASH_MISMATCH"):
        record_checkpoint(
            first,
            plan_sha256="f" * 64,
            stage="TOPIC_RELATIONS_VERIFIED",
            status="PASS",
            artifact_sha256="e" * 64,
        )


def test_blocked_checkpoint_can_be_resumed_but_not_skipped() -> None:
    plan = _ready_plan()
    operation = new_operation(plan)
    blocked = record_checkpoint(
        operation,
        plan_sha256=plan.plan_sha256,
        stage="MASTER_DATA_VERIFIED",
        status="BLOCKED",
        artifact_sha256="d" * 64,
    )
    with pytest.raises(StockAddWorkflowError, match="OUT_OF_ORDER"):
        record_checkpoint(
            blocked,
            plan_sha256=plan.plan_sha256,
            stage="TOPIC_RELATIONS_VERIFIED",
            status="PASS",
            artifact_sha256="e" * 64,
        )
    resumed = record_checkpoint(
        blocked,
        plan_sha256=plan.plan_sha256,
        stage="MASTER_DATA_VERIFIED",
        status="PASS",
        artifact_sha256="f" * 64,
    )
    assert [event.status for event in resumed.events] == ["BLOCKED", "PASS"]


def test_operation_record_round_trip_supports_safe_resume() -> None:
    plan = _ready_plan()
    operation = new_operation(plan)
    operation = record_checkpoint(
        operation,
        plan_sha256=plan.plan_sha256,
        stage="MASTER_DATA_VERIFIED",
        status="PASS",
        artifact_sha256="d" * 64,
    )
    restored = operation_from_record(operation_to_record(operation))
    assert restored == operation
    resumed = record_checkpoint(
        restored,
        plan_sha256=plan.plan_sha256,
        stage="TOPIC_RELATIONS_VERIFIED",
        status="PASS",
        artifact_sha256="e" * 64,
    )
    assert len(resumed.events) == 2

    corrupted = operation_to_record(operation)
    corrupted["events"].append(
        {
            "stage": "POST_CLOSE_VERIFIED",
            "status": "PASS",
            "artifact_sha256": "f" * 64,
        }
    )
    with pytest.raises(StockAddWorkflowError, match="OUT_OF_ORDER"):
        operation_from_record(corrupted)


def test_operation_record_rejects_tampered_identity_or_extra_fields() -> None:
    plan = _ready_plan()
    record = operation_to_record(new_operation(plan))
    record["operationId"] = "stock-add:9999:" + plan.plan_sha256
    with pytest.raises(StockAddWorkflowError, match="INVALID_OPERATION_RECORD_IDENTITY"):
        operation_from_record(record)

    record = operation_to_record(new_operation(plan))
    record["unexpected"] = True
    with pytest.raises(StockAddWorkflowError, match="INVALID_OPERATION_RECORD_FIELDS"):
        operation_from_record(record)


def test_checkpoint_requires_sha256_artifact_digest() -> None:
    plan = _ready_plan()
    operation = new_operation(plan)
    with pytest.raises(StockAddWorkflowError, match="INVALID_CHECKPOINT"):
        record_checkpoint(
            operation,
            plan_sha256=plan.plan_sha256,
            stage="MASTER_DATA_VERIFIED",
            status="PASS",
            artifact_sha256="not-a-digest",
        )
