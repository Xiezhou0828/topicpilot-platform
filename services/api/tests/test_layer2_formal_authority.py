from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from topicpilot_api.topic_engine import (
    ACTIVATION_ACTIVE,
    ACTIVATION_NOT_ACTIVE,
    AUTHORITY_POLICY_APPROVED,
    DAILY_STRENGTH_PARTIAL_BY_DESIGN,
    FORMAL_OWNER_PRINCIPAL,
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
    SCORE_GRADE_APPROVED_VERIFIED,
    SCORE_GRADE_PENDING_RECORD,
    SCORE_GRADE_RECORD_CREATED,
    DailyStrengthContract,
    Layer2AuthorityError,
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


def _provenance(
    artifact_id: str,
    status: str,
    *,
    digest: str | None = None,
) -> Layer2Provenance:
    return Layer2Provenance(
        artifact_id=artifact_id,
        artifact_version="v1",
        source_ref=f"repo://{artifact_id}",
        status=status,
        sha256=digest,
        scope="Layer 2 authority evidence",
    )


def _daily_strength() -> DailyStrengthContract:
    return DailyStrengthContract(
        status=DAILY_STRENGTH_PARTIAL_BY_DESIGN,
        verified_components=("Score/Grade deterministic foundation",),
        unverified_components=(
            "exact current/day-level aggregation",
            "freshness and history parameter contract",
        ),
        parameter_provenance=(
            _provenance(
                "003F-score-grade-mechanics",
                PROVENANCE_VERIFIED_IMPLEMENTATION,
                digest="a" * 64,
            ),
            _provenance("daily-strength-unverified-parameters", PROVENANCE_UNVERIFIED),
        ),
        fail_closed=True,
    )


def _score_grade(*, record_state: str = SCORE_GRADE_RECORD_CREATED) -> ScoreGradeContract:
    return ScoreGradeContract(
        status=SCORE_GRADE_APPROVED_VERIFIED,
        legacy_schema_version="topic-score-pm-approval.v1",
        approval_artifact_id="PHASE_3_7_003F_PM_FORMULA_APPROVAL_BRIEF",
        approval_artifact_sha256="77319ae5fd51470265dd0030f38a5cc9b18ae0214d01a0a508c2b32025b8c8a9",
        policy_record_state=record_state,
        policy_record_sha256=None if record_state == SCORE_GRADE_PENDING_RECORD else "b" * 64,
    )


def _lifecycle() -> LifecycleContract:
    return LifecycleContract(
        status=LIFECYCLE_APPROVED,
        stages=LAYER2_LIFECYCLE_STAGES,
        independent_from_daily_strength=True,
        independent_from_score_grade=True,
        transition_status=LIFECYCLE_TRANSITIONS_PARTIAL_BY_DESIGN,
        transition_policy_ref=None,
        transition_provenance=(
            _provenance(
                "lifecycle-five-stage-archaeology",
                PROVENANCE_VERIFIED_IMPLEMENTATION,
                digest="c" * 64,
            ),
            _provenance("lifecycle-transition-parameters", PROVENANCE_UNVERIFIED),
        ),
        fail_closed=True,
    )


def _record() -> Layer2FormalAuthorityRecord:
    return Layer2FormalAuthorityRecord(
        schema_version=LAYER2_FORMAL_AUTHORITY_SCHEMA_VERSION,
        policy_bundle_id=LAYER2_POLICY_BUNDLE_ID,
        policy_bundle_version=LAYER2_POLICY_BUNDLE_VERSION,
        candidate_id=LAYER2_CANDIDATE_ID,
        candidate_version=LAYER2_CANDIDATE_VERSION,
        owner_identity=FORMAL_OWNER_PRINCIPAL,
        approval_reference="OWNER_APPROVAL:TOPIC_B2_LAYER2_POLICY_V1",
        approval_timestamp=datetime(2026, 9, 15, tzinfo=UTC),
        effective_date=date(2026, 9, 15),
        authority_state=AUTHORITY_POLICY_APPROVED,
        publication_state="READY",
        activation_state=ACTIVATION_NOT_ACTIVE,
        reviewed_provenance=(
            _provenance(
                "layer2-owner-policy-decision",
                PROVENANCE_APPROVED_ARCHITECTURE,
                digest="d" * 64,
            ),
            _provenance(
                "003F-score-grade-mechanics",
                PROVENANCE_VERIFIED_IMPLEMENTATION,
                digest="e" * 64,
            ),
            _provenance("layer2-partial-runtime-provenance", PROVENANCE_PARTIAL),
        ),
        daily_strength=_daily_strength(),
        score_grade=_score_grade(),
        lifecycle=_lifecycle(),
        limitations=(
            "Daily Strength exact parameters remain PARTIAL_BY_DESIGN.",
            "Formal DB readback and A9 writer activation remain separate gates.",
        ),
    )


def test_complete_layer2_contract_is_valid_without_implying_activation() -> None:
    decision = evaluate_layer2_authority(_record())

    assert decision.allowed is True
    assert decision.reason_code == "VALID"
    metadata = export_layer2_metadata(_record())
    assert metadata["policyApproved"] is True
    assert metadata["productionActive"] is False
    assert metadata["dailyStrength"]["status"] == DAILY_STRENGTH_PARTIAL_BY_DESIGN
    assert metadata["lifecycle"]["stages"] == list(LAYER2_LIFECYCLE_STAGES)


def test_missing_owner_identity_is_the_exact_fail_closed_stop() -> None:
    decision = evaluate_layer2_authority(replace(_record(), owner_identity=None))

    assert decision.allowed is False
    assert decision.reason_code == "FORMAL_OWNER_IDENTITY_REQUIRED"


def test_display_name_or_fixture_owner_is_not_a_formal_identity() -> None:
    decision = evaluate_layer2_authority(replace(_record(), owner_identity="product-owner"))

    assert decision.allowed is False
    assert decision.reason_code == "INVALID_OWNER_IDENTITY"


def test_daily_strength_unknown_parameters_cannot_be_marked_complete() -> None:
    with pytest.raises(Layer2AuthorityError, match="DAILY_STRENGTH_STATUS_UNSUPPORTED"):
        replace(_daily_strength(), status="APPROVED")


def test_daily_strength_partial_parameters_must_fail_closed() -> None:
    with pytest.raises(Layer2AuthorityError, match="DAILY_STRENGTH_NOT_FAIL_CLOSED"):
        replace(_daily_strength(), fail_closed=False)


def test_lifecycle_stage_identity_and_separation_are_strict() -> None:
    with pytest.raises(Layer2AuthorityError, match="INVALID_LIFECYCLE_STAGE"):
        replace(_lifecycle(), stages=("SPROUTING", "FERMENTING", "MAIN_RISE", "MATURE", "BASE"))
    with pytest.raises(Layer2AuthorityError, match="LAYER2_OUTPUTS_NOT_INDEPENDENT"):
        replace(_lifecycle(), independent_from_score_grade=False)


def test_pending_legacy_score_record_blocks_full_layer2_authority() -> None:
    pending = replace(_record(), score_grade=_score_grade(record_state=SCORE_GRADE_PENDING_RECORD))

    decision = evaluate_layer2_authority(pending)

    assert decision.reason_code == "LEGACY_SCORE_GRADE_RECORD_MISSING"
    assert not decision.allowed


def test_strict_003h_round_trip_and_hash_are_stable() -> None:
    artifact = export_layer2_authority_artifact(_record())
    parsed = parse_layer2_authority_artifact(artifact)

    assert parsed == _record()
    assert layer2_authority_sha256(parsed) == layer2_authority_sha256(_record())
    assert artifact["effectiveDate"] == "2026-09-15"
    assert artifact["dailyStrength"]["failClosed"] is True


@pytest.mark.parametrize("mutation", ("missing", "unknown"))
def test_strict_003h_rejects_missing_or_unknown_fields(mutation: str) -> None:
    artifact = export_layer2_authority_artifact(_record())
    if mutation == "missing":
        artifact.pop("lifecycle")
    else:
        artifact["lifecycle"]["unexpected"] = "value"

    with pytest.raises(Layer2AuthorityError) as exc_info:
        parse_layer2_authority_artifact(artifact)

    assert exc_info.value.reason_code in {"MISSING_FIELD", "UNKNOWN_FIELD"}


def test_003h_metadata_preserves_partial_and_does_not_grant_authority() -> None:
    record = replace(_record(), owner_identity=None)
    metadata = export_layer2_metadata(record)

    assert metadata["ownerIdentityPresent"] is False
    assert metadata["policyApproved"] is True
    assert evaluate_layer2_authority(record).allowed is False


def test_production_active_state_is_not_authorized_by_this_contract() -> None:
    active = replace(
        _record(),
        authority_state="PRODUCTION_ACTIVE",
        publication_state="ACTIVE",
        activation_state=ACTIVATION_ACTIVE,
    )

    decision = evaluate_layer2_authority(active)

    assert decision.reason_code == "PRODUCTION_ACTIVATION_NOT_AUTHORIZED"
    assert not decision.allowed
