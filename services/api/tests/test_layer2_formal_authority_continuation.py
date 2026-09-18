from datetime import date

from topicpilot_api.governance_identity import (
    FORMAL_OWNER_ID,
    FORMAL_OWNER_PRINCIPAL,
    GOVERNANCE_OWNER_KIND,
    require_governance_identity,
    resolve_governance_principal,
)
from topicpilot_api.topic_engine import (
    ACTIVATION_NOT_ACTIVE,
    AUTHORITY_POLICY_APPROVED,
    DAILY_STRENGTH_PARTIAL_BY_DESIGN,
    LAYER2_CANDIDATE_ID,
    LAYER2_CANDIDATE_VERSION,
    LAYER2_FORMAL_AUTHORITY_SCHEMA_VERSION,
    LAYER2_LIFECYCLE_STAGES,
    LAYER2_POLICY_BUNDLE_ID,
    LAYER2_POLICY_BUNDLE_VERSION,
    LIFECYCLE_APPROVED,
    LIFECYCLE_TRANSITIONS_PARTIAL_BY_DESIGN,
    PROVENANCE_APPROVED_ARCHITECTURE,
    PROVENANCE_PARTIAL,
    PROVENANCE_UNVERIFIED,
    PROVENANCE_VERIFIED_IMPLEMENTATION,
    PUBLICATION_BLOCKED,
    SCORE_GRADE_APPROVED_VERIFIED,
    SCORE_GRADE_RECORD_CREATED,
    DailyStrengthContract,
    Layer2FormalAuthorityRecord,
    Layer2Provenance,
    LifecycleContract,
    ScoreGradeContract,
    evaluate_layer2_authority,
    export_layer2_authority_artifact,
    export_layer2_metadata,
    layer2_authority_sha256,
    parse_layer2_authority_artifact,
)
from topicpilot_api.topic_engine.policy_approval import (
    APPROVED,
    PolicyApprovalRecord,
    evaluate_policy_approval,
    export_policy_approval_artifact,
    parse_policy_approval_artifact,
    policy_approval_sha256,
)

THREE_F_DIGEST = "77319ae5fd51470265dd0030f38a5cc9b18ae0214d01a0a508c2b32025b8c8a9"


def _provenance(
    artifact_id: str,
    status: str,
    *,
    digest: str | None = None,
    source_ref: str | None = None,
) -> Layer2Provenance:
    return Layer2Provenance(
        artifact_id=artifact_id,
        artifact_version="v1",
        source_ref=source_ref or f"repo://{artifact_id}",
        status=status,
        sha256=digest,
        scope="Topic/B2 Layer 2 formal policy authority",
    )


def _legacy_policy_record() -> PolicyApprovalRecord:
    brief = "PHASE_3_7_003F_PM_FORMULA_APPROVAL_BRIEF"
    return PolicyApprovalRecord(
        decision_status=APPROVED,
        reviewed_dataset_id=brief,
        reviewed_dataset_version="PHASE-3.7-NEXT-V2",
        reviewed_validation_runtime_version=LAYER2_FORMAL_AUTHORITY_SCHEMA_VERSION,
        reviewed_report_digest=THREE_F_DIGEST,
        approved_candidate_id=LAYER2_CANDIDATE_ID,
        approved_candidate_version=LAYER2_CANDIDATE_VERSION,
        approved_policy_version=LAYER2_POLICY_BUNDLE_VERSION,
        approved_effective_date=date(2026, 9, 15),
        approved_scope="production",
        approved_breadth_policy=f"{brief}#breadth-participation",
        approved_leadership_policy=f"{brief}#leadership",
        approved_normalization_policy=f"{brief}#normalization",
        approved_aggregation_policy=f"{brief}#aggregation",
        approved_weights=f"{brief}#aggregation-weight:0.60-breadth-0.40-leadership",
        approved_eligibility_policy=f"{brief}#eligibility",
        approved_grade_thresholds=f"{brief}#grade",
        rollback_policy="FORMAL_PUBLICATION_REMAINS_INACTIVE_UNTIL_INDEPENDENT_GATES_PASS",
        owner=FORMAL_OWNER_ID,
        decision_rationale=(
            "OWNER_POLICY_DECISION=APPROVE_EXISTING_LAYER2_POLICY_WITH_FAIL_CLOSED_ACTIVATION"
        ),
        limitations=(
            "Daily Strength remains PARTIAL_BY_DESIGN; Lifecycle is independent; "
            "formal DB and runtime publication gates remain separate."
        ),
    )


def _record() -> Layer2FormalAuthorityRecord:
    legacy = _legacy_policy_record()
    return Layer2FormalAuthorityRecord(
        schema_version=LAYER2_FORMAL_AUTHORITY_SCHEMA_VERSION,
        policy_bundle_id=LAYER2_POLICY_BUNDLE_ID,
        policy_bundle_version=LAYER2_POLICY_BUNDLE_VERSION,
        candidate_id=LAYER2_CANDIDATE_ID,
        candidate_version=LAYER2_CANDIDATE_VERSION,
        owner_identity=FORMAL_OWNER_PRINCIPAL,
        approval_reference="OWNER_DECISION:TOPIC_B2_LAYER2_POLICY_V1:2026-09-15",
        approval_timestamp=None,
        effective_date=date(2026, 9, 15),
        authority_state=AUTHORITY_POLICY_APPROVED,
        publication_state=PUBLICATION_BLOCKED,
        activation_state=ACTIVATION_NOT_ACTIVE,
        reviewed_provenance=(
            _provenance(
                "TASK-TOPIC-B2-LAYER2-FORMAL-POLICY-APPROVAL-001",
                PROVENANCE_APPROVED_ARCHITECTURE,
                digest="4c7bdc60f2ff9c222a0c9f3ac287ab2d29d931f456dcacea3ddd433b5734106b",
            ),
            _provenance(
                "PHASE_3_7_003F_PM_FORMULA_APPROVAL_BRIEF",
                PROVENANCE_VERIFIED_IMPLEMENTATION,
                digest=THREE_F_DIGEST,
                source_ref="docs/reports/PHASE_3_7_003F_PM_FORMULA_APPROVAL_BRIEF.md",
            ),
            _provenance("layer2-runtime-publication-gates", PROVENANCE_PARTIAL),
        ),
        daily_strength=DailyStrengthContract(
            status=DAILY_STRENGTH_PARTIAL_BY_DESIGN,
            verified_components=(
                "breadth participation boundaries",
                "consensus modifier bands",
                "normalization mapping",
                "weighted aggregation",
            ),
            unverified_components=(
                "standalone daily strength level/history parameters",
                "Leader Set artifact binding",
            ),
            parameter_provenance=(
                _provenance(
                    "PHASE_3_7_003F_PM_FORMULA_APPROVAL_BRIEF",
                    PROVENANCE_VERIFIED_IMPLEMENTATION,
                    digest=THREE_F_DIGEST,
                ),
                _provenance("layer2-daily-strength-unresolved-parameters", PROVENANCE_UNVERIFIED),
            ),
            fail_closed=True,
        ),
        score_grade=ScoreGradeContract(
            status=SCORE_GRADE_APPROVED_VERIFIED,
            legacy_schema_version="topic-score-pm-approval.v1",
            approval_artifact_id="PHASE_3_7_003F_PM_FORMULA_APPROVAL_BRIEF",
            approval_artifact_sha256=THREE_F_DIGEST,
            policy_record_state=SCORE_GRADE_RECORD_CREATED,
            policy_record_sha256=policy_approval_sha256(legacy),
        ),
        lifecycle=LifecycleContract(
            status=LIFECYCLE_APPROVED,
            stages=LAYER2_LIFECYCLE_STAGES,
            independent_from_daily_strength=True,
            independent_from_score_grade=True,
            transition_status=LIFECYCLE_TRANSITIONS_PARTIAL_BY_DESIGN,
            transition_policy_ref=None,
            transition_provenance=(
                _provenance(
                    "TASK-TOPIC-B2-LIFECYCLE-HISTORICAL-IMPLEMENTATION-ARCHAEOLOGY-001",
                    PROVENANCE_PARTIAL,
                    source_ref="git://topic-b2-lifecycle-archaeology@ff66df999a13fe54ec581c4b298d493895f0a578",
                ),
                _provenance("lifecycle-transition-parameters", PROVENANCE_UNVERIFIED),
            ),
            fail_closed=True,
        ),
        limitations=(
            "Daily Strength exact parameters remain PARTIAL_BY_DESIGN and fail closed.",
            "Formal DB readback for 107 Leaf / 25 Parent and 1160 roles remains pending.",
            "A10/A9 remains branch-only/operator-gated; Production activation is not performed.",
        ),
    )


def test_owner_registry_resolves_stable_non_credential_identity() -> None:
    identity = require_governance_identity(FORMAL_OWNER_ID)

    assert identity.kind == GOVERNANCE_OWNER_KIND
    assert identity.credential is False
    assert identity.account_binding == "none"
    assert "PRODUCT_POLICY_APPROVAL" in identity.authority
    assert resolve_governance_principal(FORMAL_OWNER_PRINCIPAL) == identity


def test_legacy_record_and_layer2_record_are_authoritatively_validated() -> None:
    legacy = _legacy_policy_record()
    record = _record()

    assert evaluate_policy_approval(legacy).allowed is True
    assert parse_policy_approval_artifact(export_policy_approval_artifact(legacy)) == legacy
    assert evaluate_layer2_authority(record).allowed is True


def test_policy_and_layer2_hashes_are_deterministic_and_readback_is_truthful() -> None:
    legacy = _legacy_policy_record()
    record = _record()

    assert policy_approval_sha256(legacy) == policy_approval_sha256(legacy)
    artifact = export_layer2_authority_artifact(record)
    assert parse_layer2_authority_artifact(artifact) == record
    assert layer2_authority_sha256(record) == layer2_authority_sha256(record)

    metadata = export_layer2_metadata(record)
    assert metadata["ownerIdentityPresent"] is True
    assert metadata["policyApproved"] is True
    assert metadata["productionActive"] is False
    assert metadata["publicationState"] == PUBLICATION_BLOCKED
    assert metadata["dailyStrength"]["status"] == DAILY_STRENGTH_PARTIAL_BY_DESIGN
    assert metadata["lifecycle"]["stages"] == list(LAYER2_LIFECYCLE_STAGES)
