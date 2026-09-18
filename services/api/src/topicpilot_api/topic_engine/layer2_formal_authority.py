"""Versioned, fail-closed formal authority for Topic/B2 Layer 2.

The legacy ``topic-score-pm-approval.v1`` artifact remains the authoritative
Score/Grade subset.  This module composes that subset with the independent
Daily Strength and Five-Stage Lifecycle contracts without treating Lifecycle
as a score component or treating policy approval as Production activation.

The module is deliberately artifact-oriented and has no database, scheduler,
provider, or Production side effects.  A record with an absent Owner identity
can be represented for bounded governance/readback, but the 003G-style
validator rejects it with ``FORMAL_OWNER_IDENTITY_REQUIRED``.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Final

from topicpilot_api.governance_identity import resolve_governance_principal

from .policy_approval import POLICY_APPROVAL_SCHEMA_VERSION

LAYER2_FORMAL_AUTHORITY_SCHEMA_VERSION = "topic-layer2-formal-authority.v1"
LAYER2_POLICY_BUNDLE_ID = "topic-b2-layer2-policy"
LAYER2_POLICY_BUNDLE_VERSION = "topic-b2-layer2-policy-v1"
LAYER2_CANDIDATE_ID = "TOPIC_B2_LAYER2_POLICY_V1"
LAYER2_CANDIDATE_VERSION = "v1"

AUTHORITY_POLICY_APPROVED = "POLICY_APPROVED"
AUTHORITY_PRODUCTION_ACTIVE = "PRODUCTION_ACTIVE"
AUTHORITY_BLOCKED = "BLOCKED"
AUTHORITY_STATES: Final = frozenset(
    {AUTHORITY_POLICY_APPROVED, AUTHORITY_PRODUCTION_ACTIVE, AUTHORITY_BLOCKED}
)

PUBLICATION_UNPUBLISHED = "UNPUBLISHED"
PUBLICATION_READY = "READY"
PUBLICATION_ACTIVE = "ACTIVE"
PUBLICATION_BLOCKED = "BLOCKED"
PUBLICATION_STATES: Final = frozenset(
    {PUBLICATION_UNPUBLISHED, PUBLICATION_READY, PUBLICATION_ACTIVE, PUBLICATION_BLOCKED}
)

ACTIVATION_NOT_ACTIVE = "NOT_ACTIVE"
ACTIVATION_ACTIVE = "ACTIVE"
ACTIVATION_STATES: Final = frozenset({ACTIVATION_NOT_ACTIVE, ACTIVATION_ACTIVE})

DAILY_STRENGTH_PARTIAL_BY_DESIGN = "PARTIAL_BY_DESIGN"
SCORE_GRADE_APPROVED_VERIFIED = "APPROVED_VERIFIED"
SCORE_GRADE_PENDING_RECORD = "PENDING_RECORD"
SCORE_GRADE_RECORD_CREATED = "CREATED"
LIFECYCLE_APPROVED = "APPROVED"
LIFECYCLE_TRANSITIONS_VERIFIED_COMPONENTS_ONLY = "VERIFIED_COMPONENTS_ONLY"
LIFECYCLE_TRANSITIONS_PARTIAL_BY_DESIGN = "PARTIAL_BY_DESIGN"

PROVENANCE_APPROVED_ARCHITECTURE = "APPROVED_ARCHITECTURE"
PROVENANCE_VERIFIED_IMPLEMENTATION = "VERIFIED_IMPLEMENTATION"
PROVENANCE_PARTIAL = "PARTIAL_PROVENANCE"
PROVENANCE_UNVERIFIED = "UNVERIFIED_PARAMETERS"
PROVENANCE_STATUSES: Final = frozenset(
    {
        PROVENANCE_APPROVED_ARCHITECTURE,
        PROVENANCE_VERIFIED_IMPLEMENTATION,
        PROVENANCE_PARTIAL,
        PROVENANCE_UNVERIFIED,
    }
)

LAYER2_LIFECYCLE_STAGES: Final = (
    "SPROUTING",
    "FERMENTING",
    "MAIN_RISE",
    "MATURE",
    "DECLINING",
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class Layer2AuthorityError(ValueError):
    """Raised when a Layer 2 authority artifact is malformed or blocked."""

    def __init__(self, reason_code: str, reason: str) -> None:
        super().__init__(f"{reason_code}: {reason}")
        self.reason_code = reason_code
        self.reason = reason


@dataclass(frozen=True)
class Layer2AuthorityDecision:
    """Stable 003G-style result; it never grants approval or activation."""

    allowed: bool
    status: str
    reason_code: str
    reason: str


@dataclass(frozen=True)
class Layer2Provenance:
    """One reviewed evidence reference with explicit completeness status."""

    artifact_id: str
    artifact_version: str
    source_ref: str
    status: str
    sha256: str | None
    scope: str

    def __post_init__(self) -> None:
        for field_name in (
            "artifact_id",
            "artifact_version",
            "source_ref",
            "scope",
        ):
            _required_text(getattr(self, field_name), field_name)
        if self.status not in PROVENANCE_STATUSES:
            raise Layer2AuthorityError("INVALID_PROVENANCE_STATUS", "unknown provenance status")
        if self.sha256 is not None and not _SHA256.fullmatch(self.sha256):
            raise Layer2AuthorityError(
                "INVALID_PROVENANCE_DIGEST", "sha256 must be lowercase SHA-256"
            )
        if (
            self.status
            in {
                PROVENANCE_APPROVED_ARCHITECTURE,
                PROVENANCE_VERIFIED_IMPLEMENTATION,
            }
            and self.sha256 is None
        ):
            raise Layer2AuthorityError(
                "MISSING_PROVENANCE_DIGEST",
                "approved or verified provenance requires a SHA-256 digest",
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "artifactId": self.artifact_id,
            "artifactVersion": self.artifact_version,
            "sourceRef": self.source_ref,
            "status": self.status,
            "sha256": self.sha256,
            "scope": self.scope,
        }


@dataclass(frozen=True)
class DailyStrengthContract:
    """Current/day-level strength contract, including unresolved parameters."""

    status: str
    verified_components: tuple[str, ...]
    unverified_components: tuple[str, ...]
    parameter_provenance: tuple[Layer2Provenance, ...]
    fail_closed: bool

    def __post_init__(self) -> None:
        _required_text(self.status, "daily_strength.status")
        if self.status != DAILY_STRENGTH_PARTIAL_BY_DESIGN:
            raise Layer2AuthorityError(
                "DAILY_STRENGTH_STATUS_UNSUPPORTED",
                "current Layer 2 policy only authorizes PARTIAL_BY_DESIGN",
            )
        _non_empty_unique(self.verified_components, "daily_strength.verified_components")
        _non_empty_unique(self.unverified_components, "daily_strength.unverified_components")
        if not self.parameter_provenance:
            raise Layer2AuthorityError(
                "DAILY_STRENGTH_PROVENANCE_MISSING",
                "partial Daily Strength requires parameter provenance",
            )
        if not self.fail_closed:
            raise Layer2AuthorityError(
                "DAILY_STRENGTH_NOT_FAIL_CLOSED",
                "unverified Daily Strength parameters must fail closed",
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "verifiedComponents": list(self.verified_components),
            "unverifiedComponents": list(self.unverified_components),
            "parameterProvenance": [item.as_dict() for item in self.parameter_provenance],
            "failClosed": self.fail_closed,
        }


@dataclass(frozen=True)
class ScoreGradeContract:
    """Composition reference to the legacy Score/Grade approval subset."""

    status: str
    legacy_schema_version: str
    approval_artifact_id: str
    approval_artifact_sha256: str
    policy_record_state: str
    policy_record_sha256: str | None

    def __post_init__(self) -> None:
        if self.status not in {SCORE_GRADE_APPROVED_VERIFIED, SCORE_GRADE_PENDING_RECORD}:
            raise Layer2AuthorityError("INVALID_SCORE_GRADE_STATUS", "unknown Score/Grade status")
        if self.legacy_schema_version != POLICY_APPROVAL_SCHEMA_VERSION:
            raise Layer2AuthorityError(
                "LEGACY_SCHEMA_MISMATCH",
                "Score/Grade composition must reference the supported legacy schema",
            )
        _required_text(self.approval_artifact_id, "score_grade.approval_artifact_id")
        if not _SHA256.fullmatch(self.approval_artifact_sha256):
            raise Layer2AuthorityError(
                "INVALID_SCORE_GRADE_DIGEST",
                "Score/Grade approval artifact digest must be lowercase SHA-256",
            )
        if self.policy_record_state not in {SCORE_GRADE_PENDING_RECORD, SCORE_GRADE_RECORD_CREATED}:
            raise Layer2AuthorityError("INVALID_SCORE_GRADE_RECORD_STATE", "unknown record state")
        if self.policy_record_state == SCORE_GRADE_RECORD_CREATED:
            if self.policy_record_sha256 is None or not _SHA256.fullmatch(
                self.policy_record_sha256
            ):
                raise Layer2AuthorityError(
                    "MISSING_SCORE_GRADE_RECORD_DIGEST",
                    "a created legacy record requires a lowercase SHA-256",
                )
        elif self.policy_record_sha256 is not None:
            raise Layer2AuthorityError(
                "UNEXPECTED_SCORE_GRADE_RECORD_DIGEST",
                "a pending legacy record cannot carry a record digest",
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "legacySchemaVersion": self.legacy_schema_version,
            "approvalArtifactId": self.approval_artifact_id,
            "approvalArtifactSha256": self.approval_artifact_sha256,
            "policyRecordState": self.policy_record_state,
            "policyRecordSha256": self.policy_record_sha256,
        }


@dataclass(frozen=True)
class LifecycleContract:
    """Independent five-stage Lifecycle policy and bounded transition status."""

    status: str
    stages: tuple[str, ...]
    independent_from_daily_strength: bool
    independent_from_score_grade: bool
    transition_status: str
    transition_policy_ref: str | None
    transition_provenance: tuple[Layer2Provenance, ...]
    fail_closed: bool

    def __post_init__(self) -> None:
        if self.status != LIFECYCLE_APPROVED:
            raise Layer2AuthorityError("LIFECYCLE_NOT_APPROVED", "Lifecycle must be Owner-approved")
        if self.stages != LAYER2_LIFECYCLE_STAGES:
            raise Layer2AuthorityError(
                "INVALID_LIFECYCLE_STAGE",
                "Lifecycle stages must be the exact approved five-stage sequence",
            )
        if not self.independent_from_daily_strength or not self.independent_from_score_grade:
            raise Layer2AuthorityError(
                "LAYER2_OUTPUTS_NOT_INDEPENDENT",
                "Lifecycle must remain independent from Daily Strength and Score/Grade",
            )
        if self.transition_status not in {
            LIFECYCLE_TRANSITIONS_VERIFIED_COMPONENTS_ONLY,
            LIFECYCLE_TRANSITIONS_PARTIAL_BY_DESIGN,
        }:
            raise Layer2AuthorityError(
                "INVALID_LIFECYCLE_TRANSITION_STATUS",
                "unknown Lifecycle transition status",
            )
        if (
            self.transition_status == LIFECYCLE_TRANSITIONS_PARTIAL_BY_DESIGN
            and not self.fail_closed
        ):
            raise Layer2AuthorityError(
                "LIFECYCLE_NOT_FAIL_CLOSED",
                "unverified Lifecycle transition parameters must fail closed",
            )
        if not self.transition_provenance:
            raise Layer2AuthorityError(
                "LIFECYCLE_PROVENANCE_MISSING",
                "Lifecycle requires transition provenance",
            )
        if self.transition_status == LIFECYCLE_TRANSITIONS_VERIFIED_COMPONENTS_ONLY:
            if self.transition_policy_ref is not None:
                _required_text(self.transition_policy_ref, "lifecycle.transition_policy_ref")
        elif self.transition_policy_ref is not None:
            _required_text(self.transition_policy_ref, "lifecycle.transition_policy_ref")

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "stages": list(self.stages),
            "independentFromDailyStrength": self.independent_from_daily_strength,
            "independentFromScoreGrade": self.independent_from_score_grade,
            "transitionStatus": self.transition_status,
            "transitionPolicyRef": self.transition_policy_ref,
            "transitionProvenance": [item.as_dict() for item in self.transition_provenance],
            "failClosed": self.fail_closed,
        }


@dataclass(frozen=True)
class Layer2FormalAuthorityRecord:
    """Complete Layer 2 authority envelope; validation remains a separate guard."""

    schema_version: str
    policy_bundle_id: str
    policy_bundle_version: str
    candidate_id: str
    candidate_version: str
    owner_identity: str | None
    approval_reference: str
    approval_timestamp: datetime | None
    effective_date: date
    authority_state: str
    publication_state: str
    activation_state: str
    reviewed_provenance: tuple[Layer2Provenance, ...]
    daily_strength: DailyStrengthContract
    score_grade: ScoreGradeContract
    lifecycle: LifecycleContract
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != LAYER2_FORMAL_AUTHORITY_SCHEMA_VERSION:
            raise Layer2AuthorityError("SCHEMA_MISMATCH", "Layer 2 schema version is not supported")
        for field_name in (
            "policy_bundle_id",
            "policy_bundle_version",
            "candidate_id",
            "candidate_version",
            "approval_reference",
        ):
            _required_text(getattr(self, field_name), field_name)
        if self.authority_state not in AUTHORITY_STATES:
            raise Layer2AuthorityError("INVALID_AUTHORITY_STATE", "unknown Layer 2 authority state")
        if self.publication_state not in PUBLICATION_STATES:
            raise Layer2AuthorityError("INVALID_PUBLICATION_STATE", "unknown publication state")
        if self.activation_state not in ACTIVATION_STATES:
            raise Layer2AuthorityError("INVALID_ACTIVATION_STATE", "unknown activation state")
        if self.approval_timestamp is not None and (
            self.approval_timestamp.tzinfo is None or self.approval_timestamp.utcoffset() is None
        ):
            raise Layer2AuthorityError(
                "APPROVAL_TIMESTAMP_NOT_TIMEZONE_AWARE",
                "approval timestamp must be timezone-aware",
            )
        if not self.reviewed_provenance:
            raise Layer2AuthorityError(
                "REVIEWED_PROVENANCE_MISSING", "reviewed provenance is required"
            )
        _non_empty_unique(self.limitations, "limitations")
        if (
            self.publication_state == PUBLICATION_ACTIVE
            and self.activation_state != ACTIVATION_ACTIVE
        ):
            raise Layer2AuthorityError(
                "PUBLICATION_ACTIVATION_MISMATCH",
                "active publication requires active activation state",
            )
        if (
            self.activation_state == ACTIVATION_ACTIVE
            and self.authority_state != AUTHORITY_PRODUCTION_ACTIVE
        ):
            raise Layer2AuthorityError(
                "PRODUCTION_AUTHORITY_MISMATCH",
                "active activation requires PRODUCTION_ACTIVE authority",
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "policyBundleId": self.policy_bundle_id,
            "policyBundleVersion": self.policy_bundle_version,
            "candidateId": self.candidate_id,
            "candidateVersion": self.candidate_version,
            "ownerIdentity": self.owner_identity,
            "approvalReference": self.approval_reference,
            "approvalTimestamp": (
                self.approval_timestamp.isoformat() if self.approval_timestamp is not None else None
            ),
            "effectiveDate": self.effective_date.isoformat(),
            "authorityState": self.authority_state,
            "publicationState": self.publication_state,
            "activationState": self.activation_state,
            "reviewedProvenance": [item.as_dict() for item in self.reviewed_provenance],
            "dailyStrength": self.daily_strength.as_dict(),
            "scoreGrade": self.score_grade.as_dict(),
            "lifecycle": self.lifecycle.as_dict(),
            "limitations": list(self.limitations),
        }


_ARTIFACT_FIELDS: Final = (
    "schemaVersion",
    "policyBundleId",
    "policyBundleVersion",
    "candidateId",
    "candidateVersion",
    "ownerIdentity",
    "approvalReference",
    "approvalTimestamp",
    "effectiveDate",
    "authorityState",
    "publicationState",
    "activationState",
    "reviewedProvenance",
    "dailyStrength",
    "scoreGrade",
    "lifecycle",
    "limitations",
)


def evaluate_layer2_authority(record: Layer2FormalAuthorityRecord) -> Layer2AuthorityDecision:
    """Validate complete formal authority without granting activation."""

    if record.schema_version != LAYER2_FORMAL_AUTHORITY_SCHEMA_VERSION:
        return _blocked("SCHEMA_MISMATCH", "Layer 2 schema version is not supported")
    if record.policy_bundle_id != LAYER2_POLICY_BUNDLE_ID:
        return _blocked("UNKNOWN_POLICY_BUNDLE_ID", "policy bundle identity is not governed")
    if record.policy_bundle_version != LAYER2_POLICY_BUNDLE_VERSION:
        return _blocked("UNKNOWN_POLICY_BUNDLE_VERSION", "policy bundle version is not governed")
    if (
        record.candidate_id != LAYER2_CANDIDATE_ID
        or record.candidate_version != LAYER2_CANDIDATE_VERSION
    ):
        return _blocked("UNKNOWN_POLICY_CANDIDATE", "candidate identity/version is not governed")
    if record.owner_identity is None or not record.owner_identity.strip():
        return _blocked(
            "FORMAL_OWNER_IDENTITY_REQUIRED",
            "a stable repository-authoritative Owner identity is required",
        )
    if not _is_governance_identity(record.owner_identity):
        return _blocked(
            "INVALID_OWNER_IDENTITY",
            "Owner identity must use a repository governance principal form",
        )
    if record.activation_state == ACTIVATION_ACTIVE:
        return _blocked(
            "PRODUCTION_ACTIVATION_NOT_AUTHORIZED",
            "this contract validates authority but never authorizes Production activation",
        )
    if record.authority_state != AUTHORITY_POLICY_APPROVED:
        return _blocked("AUTHORITY_NOT_POLICY_APPROVED", "Layer 2 authority is not policy-approved")
    if record.score_grade.policy_record_state != SCORE_GRADE_RECORD_CREATED:
        return _blocked(
            "LEGACY_SCORE_GRADE_RECORD_MISSING",
            "the composed legacy Score/Grade PolicyApprovalRecord is not created",
        )
    return Layer2AuthorityDecision(
        True,
        "VALID",
        "VALID",
        "Layer 2 formal authority is structurally valid; publication remains separate",
    )


def require_layer2_authority(record: Layer2FormalAuthorityRecord) -> Layer2AuthorityDecision:
    decision = evaluate_layer2_authority(record)
    if not decision.allowed:
        raise Layer2AuthorityError(decision.reason_code, decision.reason)
    return decision


def export_layer2_authority_artifact(record: Layer2FormalAuthorityRecord) -> dict[str, object]:
    """Export the strict 003H-compatible JSON artifact."""

    return record.as_dict()


def parse_layer2_authority_artifact(
    payload: Mapping[str, object],
) -> Layer2FormalAuthorityRecord:
    """Parse a strict artifact without applying the 003G authority decision."""

    if not isinstance(payload, Mapping):
        raise Layer2AuthorityError("INVALID_PAYLOAD", "Layer 2 artifact must be an object")
    actual = set(payload)
    expected = set(_ARTIFACT_FIELDS)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        raise Layer2AuthorityError(
            "MISSING_FIELD", f"Layer 2 artifact is missing: {', '.join(missing)}"
        )
    if unknown:
        raise Layer2AuthorityError(
            "UNKNOWN_FIELD", f"Layer 2 artifact contains: {', '.join(unknown)}"
        )
    return _record_from_mapping(payload)


def export_layer2_metadata(record: Layer2FormalAuthorityRecord) -> dict[str, object]:
    """003H metadata view; it reports authority but never grants it."""

    return {
        "schemaVersion": record.schema_version,
        "policyBundleId": record.policy_bundle_id,
        "policyBundleVersion": record.policy_bundle_version,
        "candidateId": record.candidate_id,
        "candidateVersion": record.candidate_version,
        "ownerIdentityPresent": record.owner_identity is not None,
        "authorityState": record.authority_state,
        "policyApproved": record.authority_state == AUTHORITY_POLICY_APPROVED,
        "productionActive": record.activation_state == ACTIVATION_ACTIVE,
        "publicationState": record.publication_state,
        "dailyStrength": {
            "status": record.daily_strength.status,
            "failClosed": record.daily_strength.fail_closed,
        },
        "scoreGrade": {
            "status": record.score_grade.status,
            "legacySchemaVersion": record.score_grade.legacy_schema_version,
            "policyRecordState": record.score_grade.policy_record_state,
        },
        "lifecycle": {
            "status": record.lifecycle.status,
            "stages": list(record.lifecycle.stages),
            "independentFromDailyStrength": record.lifecycle.independent_from_daily_strength,
            "independentFromScoreGrade": record.lifecycle.independent_from_score_grade,
            "transitionStatus": record.lifecycle.transition_status,
            "failClosed": record.lifecycle.fail_closed,
        },
        "limitations": list(record.limitations),
    }


def layer2_authority_sha256(record: Layer2FormalAuthorityRecord) -> str:
    """Return the deterministic SHA-256 of canonical 003H serialization."""

    encoded = json.dumps(
        export_layer2_authority_artifact(record),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _record_from_mapping(payload: Mapping[str, object]) -> Layer2FormalAuthorityRecord:
    return Layer2FormalAuthorityRecord(
        schema_version=_required_mapping_text(payload, "schemaVersion"),
        policy_bundle_id=_required_mapping_text(payload, "policyBundleId"),
        policy_bundle_version=_required_mapping_text(payload, "policyBundleVersion"),
        candidate_id=_required_mapping_text(payload, "candidateId"),
        candidate_version=_required_mapping_text(payload, "candidateVersion"),
        owner_identity=_optional_mapping_text(payload, "ownerIdentity"),
        approval_reference=_required_mapping_text(payload, "approvalReference"),
        approval_timestamp=_parse_timestamp(payload["approvalTimestamp"]),
        effective_date=_parse_date(payload["effectiveDate"], "effectiveDate"),
        authority_state=_required_mapping_text(payload, "authorityState"),
        publication_state=_required_mapping_text(payload, "publicationState"),
        activation_state=_required_mapping_text(payload, "activationState"),
        reviewed_provenance=_parse_provenance(payload["reviewedProvenance"]),
        daily_strength=_parse_daily_strength(payload["dailyStrength"]),
        score_grade=_parse_score_grade(payload["scoreGrade"]),
        lifecycle=_parse_lifecycle(payload["lifecycle"]),
        limitations=_parse_string_tuple(payload["limitations"], "limitations"),
    )


def _parse_provenance(value: object) -> tuple[Layer2Provenance, ...]:
    if not isinstance(value, (list, tuple)):
        raise Layer2AuthorityError("INVALID_FIELD_TYPE", "reviewedProvenance must be an array")
    records = []
    for item in _mapping_items(value, "reviewedProvenance"):
        _require_exact_keys(
            item,
            {"artifactId", "artifactVersion", "sourceRef", "status", "sha256", "scope"},
            "reviewedProvenance",
        )
        records.append(
            Layer2Provenance(
                artifact_id=_required_mapping_text(item, "artifactId"),
                artifact_version=_required_mapping_text(item, "artifactVersion"),
                source_ref=_required_mapping_text(item, "sourceRef"),
                status=_required_mapping_text(item, "status"),
                sha256=_optional_mapping_text(item, "sha256"),
                scope=_required_mapping_text(item, "scope"),
            )
        )
    return tuple(records)


def _parse_daily_strength(value: object) -> DailyStrengthContract:
    mapping = _mapping(value, "dailyStrength")
    _require_exact_keys(
        mapping,
        {
            "status",
            "verifiedComponents",
            "unverifiedComponents",
            "parameterProvenance",
            "failClosed",
        },
        "dailyStrength",
    )
    return DailyStrengthContract(
        status=_required_mapping_text(mapping, "status"),
        verified_components=_parse_string_tuple(
            mapping["verifiedComponents"], "verifiedComponents"
        ),
        unverified_components=_parse_string_tuple(
            mapping["unverifiedComponents"], "unverifiedComponents"
        ),
        parameter_provenance=_parse_provenance(mapping["parameterProvenance"]),
        fail_closed=_required_bool(mapping, "failClosed"),
    )


def _parse_score_grade(value: object) -> ScoreGradeContract:
    mapping = _mapping(value, "scoreGrade")
    _require_exact_keys(
        mapping,
        {
            "status",
            "legacySchemaVersion",
            "approvalArtifactId",
            "approvalArtifactSha256",
            "policyRecordState",
            "policyRecordSha256",
        },
        "scoreGrade",
    )
    return ScoreGradeContract(
        status=_required_mapping_text(mapping, "status"),
        legacy_schema_version=_required_mapping_text(mapping, "legacySchemaVersion"),
        approval_artifact_id=_required_mapping_text(mapping, "approvalArtifactId"),
        approval_artifact_sha256=_required_mapping_text(mapping, "approvalArtifactSha256"),
        policy_record_state=_required_mapping_text(mapping, "policyRecordState"),
        policy_record_sha256=_optional_mapping_text(mapping, "policyRecordSha256"),
    )


def _parse_lifecycle(value: object) -> LifecycleContract:
    mapping = _mapping(value, "lifecycle")
    _require_exact_keys(
        mapping,
        {
            "status",
            "stages",
            "independentFromDailyStrength",
            "independentFromScoreGrade",
            "transitionStatus",
            "transitionPolicyRef",
            "transitionProvenance",
            "failClosed",
        },
        "lifecycle",
    )
    return LifecycleContract(
        status=_required_mapping_text(mapping, "status"),
        stages=_parse_string_tuple(mapping["stages"], "stages"),
        independent_from_daily_strength=_required_bool(mapping, "independentFromDailyStrength"),
        independent_from_score_grade=_required_bool(mapping, "independentFromScoreGrade"),
        transition_status=_required_mapping_text(mapping, "transitionStatus"),
        transition_policy_ref=_optional_mapping_text(mapping, "transitionPolicyRef"),
        transition_provenance=_parse_provenance(mapping["transitionProvenance"]),
        fail_closed=_required_bool(mapping, "failClosed"),
    )


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Layer2AuthorityError("INVALID_FIELD_TYPE", f"{field} must be an object")
    return value


def _mapping_items(value: object, field: str) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        raise Layer2AuthorityError("INVALID_FIELD_TYPE", f"{field} must be an array")
    return tuple(_mapping(item, field) for item in value)


def _parse_string_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise Layer2AuthorityError("INVALID_FIELD_TYPE", f"{field} must be an array")
    return tuple(_required_text(item, field) for item in value)


def _parse_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise Layer2AuthorityError("INVALID_FIELD_TYPE", f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise Layer2AuthorityError("INVALID_DATE", f"{field} must be a canonical ISO date") from exc


def _parse_timestamp(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise Layer2AuthorityError(
            "INVALID_FIELD_TYPE", "approvalTimestamp must be an ISO timestamp"
        )
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise Layer2AuthorityError(
            "INVALID_TIMESTAMP", "approvalTimestamp must be a canonical ISO timestamp"
        ) from exc


def _required_mapping_text(mapping: Mapping[str, object], field: str) -> str:
    if field not in mapping:
        raise Layer2AuthorityError("MISSING_FIELD", f"missing {field}")
    return _required_text(mapping[field], field)


def _require_exact_keys(mapping: Mapping[str, object], expected: set[str], field: str) -> None:
    actual = set(mapping)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        raise Layer2AuthorityError("MISSING_FIELD", f"{field} is missing: {', '.join(missing)}")
    if unknown:
        raise Layer2AuthorityError("UNKNOWN_FIELD", f"{field} contains: {', '.join(unknown)}")


def _optional_mapping_text(mapping: Mapping[str, object], field: str) -> str | None:
    if field not in mapping:
        raise Layer2AuthorityError("MISSING_FIELD", f"missing {field}")
    value = mapping[field]
    if value is not None:
        return _required_text(value, field)
    return None


def _required_bool(mapping: Mapping[str, object], field: str) -> bool:
    if field not in mapping or not isinstance(mapping[field], bool):
        raise Layer2AuthorityError("INVALID_FIELD_TYPE", f"{field} must be boolean")
    return mapping[field]


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise Layer2AuthorityError("INVALID_TEXT", f"{field} must be a trimmed non-empty string")
    return value


def _non_empty_unique(values: tuple[str, ...], field: str) -> None:
    if not values or any(not isinstance(value, str) or not value.strip() for value in values):
        raise Layer2AuthorityError("INVALID_TEXT_LIST", f"{field} must be non-empty")
    if any(value != value.strip() for value in values) or len(values) != len(set(values)):
        raise Layer2AuthorityError(
            "INVALID_TEXT_LIST", f"{field} must contain unique trimmed values"
        )


def _is_governance_identity(value: str) -> bool:
    return resolve_governance_principal(value) is not None


def _blocked(reason_code: str, reason: str) -> Layer2AuthorityDecision:
    return Layer2AuthorityDecision(False, "BLOCKED", reason_code, reason)


__all__ = [
    "ACTIVATION_ACTIVE",
    "ACTIVATION_NOT_ACTIVE",
    "AUTHORITY_BLOCKED",
    "AUTHORITY_POLICY_APPROVED",
    "AUTHORITY_PRODUCTION_ACTIVE",
    "DAILY_STRENGTH_PARTIAL_BY_DESIGN",
    "LAYER2_CANDIDATE_ID",
    "LAYER2_CANDIDATE_VERSION",
    "LAYER2_FORMAL_AUTHORITY_SCHEMA_VERSION",
    "LAYER2_LIFECYCLE_STAGES",
    "LAYER2_POLICY_BUNDLE_ID",
    "LAYER2_POLICY_BUNDLE_VERSION",
    "LIFECYCLE_APPROVED",
    "LIFECYCLE_TRANSITIONS_PARTIAL_BY_DESIGN",
    "LIFECYCLE_TRANSITIONS_VERIFIED_COMPONENTS_ONLY",
    "PROVENANCE_APPROVED_ARCHITECTURE",
    "PROVENANCE_PARTIAL",
    "PROVENANCE_UNVERIFIED",
    "PROVENANCE_VERIFIED_IMPLEMENTATION",
    "PUBLICATION_ACTIVE",
    "PUBLICATION_BLOCKED",
    "PUBLICATION_READY",
    "PUBLICATION_UNPUBLISHED",
    "SCORE_GRADE_APPROVED_VERIFIED",
    "SCORE_GRADE_PENDING_RECORD",
    "SCORE_GRADE_RECORD_CREATED",
    "DailyStrengthContract",
    "Layer2AuthorityDecision",
    "Layer2AuthorityError",
    "Layer2FormalAuthorityRecord",
    "Layer2Provenance",
    "LifecycleContract",
    "ScoreGradeContract",
    "evaluate_layer2_authority",
    "export_layer2_authority_artifact",
    "export_layer2_metadata",
    "layer2_authority_sha256",
    "parse_layer2_authority_artifact",
    "require_layer2_authority",
]
