"""Formula-agnostic gate for PM-approved Topic Score policy activation.

This module validates approval metadata only.  It deliberately does not inspect
or interpret formulas, weights, thresholds, or normalization rules.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

POLICY_APPROVAL_SCHEMA_VERSION = "topic-score-pm-approval.v1"
APPROVED = "APPROVED"
PRODUCTION = "production"
ALLOWED = "ALLOWED"
BLOCKED = "BLOCKED"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PolicyApprovalError(ValueError):
    """Raised when a caller requires an approval record that is not allowed."""

    def __init__(self, reason_code: str, reason: str) -> None:
        super().__init__(f"{reason_code}: {reason}")
        self.reason_code = reason_code
        self.reason = reason


class PolicyApprovalArtifactError(ValueError):
    """Raised when an approval artifact cannot be parsed safely."""

    def __init__(self, reason_code: str, reason: str) -> None:
        super().__init__(f"{reason_code}: {reason}")
        self.reason_code = reason_code
        self.reason = reason


@dataclass(frozen=True)
class PolicyApprovalRecord:
    """Opaque PM approval metadata; business-rule values remain references."""

    decision_status: str
    reviewed_dataset_id: str
    reviewed_dataset_version: str
    reviewed_validation_runtime_version: str
    reviewed_report_digest: str
    approved_candidate_id: str | None
    approved_candidate_version: str | None
    approved_policy_version: str | None
    approved_effective_date: date | None
    approved_scope: str
    approved_breadth_policy: str | None
    approved_leadership_policy: str | None
    approved_normalization_policy: str | None
    approved_aggregation_policy: str | None
    approved_weights: str | None
    approved_eligibility_policy: str | None
    approved_grade_thresholds: str | None
    rollback_policy: str | None
    owner: str | None
    decision_rationale: str | None
    limitations: str | None
    schema_version: str = POLICY_APPROVAL_SCHEMA_VERSION


@dataclass(frozen=True)
class PolicyApprovalDecision:
    """Stable result used by future provider factories and activation code."""

    allowed: bool
    status: str
    reason_code: str
    reason: str


_POLICY_REFERENCES = (
    "approved_breadth_policy",
    "approved_leadership_policy",
    "approved_normalization_policy",
    "approved_aggregation_policy",
    "approved_weights",
    "approved_eligibility_policy",
    "approved_grade_thresholds",
)

_ARTIFACT_FIELDS = (
    "decision_status",
    "reviewed_dataset_id",
    "reviewed_dataset_version",
    "reviewed_validation_runtime_version",
    "reviewed_report_digest",
    "approved_candidate_id",
    "approved_candidate_version",
    "approved_policy_version",
    "approved_effective_date",
    "approved_scope",
    "approved_breadth_policy",
    "approved_leadership_policy",
    "approved_normalization_policy",
    "approved_aggregation_policy",
    "approved_weights",
    "approved_eligibility_policy",
    "approved_grade_thresholds",
    "rollback_policy",
    "owner",
    "decision_rationale",
    "limitations",
    "schema_version",
)


def export_policy_approval_artifact(record: PolicyApprovalRecord) -> dict[str, object]:
    """Export an approval record to a JSON-compatible, lossless mapping."""

    return {
        field: record.approved_effective_date.isoformat()
        if field == "approved_effective_date" and record.approved_effective_date is not None
        else getattr(record, field)
        for field in _ARTIFACT_FIELDS
    }


def parse_policy_approval_artifact(payload: Mapping[str, object]) -> PolicyApprovalRecord:
    """Parse one strict artifact without applying approval semantics."""

    if not isinstance(payload, Mapping):
        raise PolicyApprovalArtifactError("INVALID_PAYLOAD", "approval artifact must be an object")
    actual = set(payload)
    expected = set(_ARTIFACT_FIELDS)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        raise PolicyApprovalArtifactError(
            "MISSING_FIELD", f"approval artifact is missing: {', '.join(missing)}"
        )
    if unknown:
        raise PolicyApprovalArtifactError(
            "UNKNOWN_FIELD", f"approval artifact contains: {', '.join(unknown)}"
        )
    values = {field: payload[field] for field in _ARTIFACT_FIELDS}
    effective_date = _parse_artifact_date(values["approved_effective_date"])
    return PolicyApprovalRecord(
        decision_status=_required_text(values, "decision_status"),
        reviewed_dataset_id=_required_text(values, "reviewed_dataset_id"),
        reviewed_dataset_version=_required_text(values, "reviewed_dataset_version"),
        reviewed_validation_runtime_version=_required_text(
            values, "reviewed_validation_runtime_version"
        ),
        reviewed_report_digest=_required_text(values, "reviewed_report_digest"),
        approved_candidate_id=_optional_text(values, "approved_candidate_id"),
        approved_candidate_version=_optional_text(values, "approved_candidate_version"),
        approved_policy_version=_optional_text(values, "approved_policy_version"),
        approved_effective_date=effective_date,
        approved_scope=_required_text(values, "approved_scope"),
        approved_breadth_policy=_optional_text(values, "approved_breadth_policy"),
        approved_leadership_policy=_optional_text(values, "approved_leadership_policy"),
        approved_normalization_policy=_optional_text(values, "approved_normalization_policy"),
        approved_aggregation_policy=_optional_text(values, "approved_aggregation_policy"),
        approved_weights=_optional_text(values, "approved_weights"),
        approved_eligibility_policy=_optional_text(values, "approved_eligibility_policy"),
        approved_grade_thresholds=_optional_text(values, "approved_grade_thresholds"),
        rollback_policy=_optional_text(values, "rollback_policy"),
        owner=_optional_text(values, "owner"),
        decision_rationale=_optional_text(values, "decision_rationale"),
        limitations=_optional_text(values, "limitations"),
        schema_version=_required_text(values, "schema_version"),
    )


def evaluate_policy_approval(record: PolicyApprovalRecord) -> PolicyApprovalDecision:
    """Return an allow/block decision without evaluating business semantics."""

    if record.schema_version != POLICY_APPROVAL_SCHEMA_VERSION:
        return _blocked("SCHEMA_MISMATCH", "approval schema version is not supported")
    if record.decision_status != APPROVED:
        return _blocked("DECISION_NOT_APPROVED", "PM decision status is not APPROVED")
    if record.approved_scope != PRODUCTION:
        return _blocked("NON_PRODUCTION_SCOPE", "approval scope is not production")
    if not all(
        _present(getattr(record, field))
        for field in (
            "reviewed_dataset_id",
            "reviewed_dataset_version",
            "reviewed_validation_runtime_version",
        )
    ):
        return _blocked("MISSING_PROVENANCE", "reviewed dataset provenance is incomplete")
    if not _SHA256.fullmatch(record.reviewed_report_digest):
        return _blocked("INVALID_REPORT_DIGEST", "reviewed report digest must be lowercase SHA-256")
    if not all(
        _present(getattr(record, field))
        for field in (
            "approved_candidate_id",
            "approved_candidate_version",
            "approved_policy_version",
        )
    ):
        return _blocked(
            "MISSING_POLICY_IDENTITY", "approved candidate or policy identity is incomplete"
        )
    if not all(_present(getattr(record, field)) for field in _POLICY_REFERENCES):
        return _blocked(
            "MISSING_POLICY_REFERENCE", "one or more approved policy references are missing"
        )
    if record.approved_effective_date is None:
        return _blocked("MISSING_EFFECTIVE_DATE", "production approval requires an effective date")
    if not all(
        _present(getattr(record, field))
        for field in ("rollback_policy", "owner", "decision_rationale", "limitations")
    ):
        return _blocked(
            "MISSING_GOVERNANCE_METADATA",
            "rollback, ownership, rationale, or limitations are missing",
        )
    return PolicyApprovalDecision(
        True, ALLOWED, "APPROVED", "PM-approved production policy metadata is complete"
    )


def require_policy_approval(record: PolicyApprovalRecord) -> PolicyApprovalDecision:
    """Fail closed when a caller requires production approval."""

    decision = evaluate_policy_approval(record)
    if not decision.allowed:
        raise PolicyApprovalError(decision.reason_code, decision.reason)
    return decision


def _blocked(reason_code: str, reason: str) -> PolicyApprovalDecision:
    return PolicyApprovalDecision(False, BLOCKED, reason_code, reason)


def _present(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _required_text(values: Mapping[str, object], field: str) -> str:
    value = values[field]
    if not isinstance(value, str):
        raise PolicyApprovalArtifactError("INVALID_FIELD_TYPE", f"{field} must be a string")
    return value


def _optional_text(values: Mapping[str, object], field: str) -> str | None:
    value = values[field]
    if value is not None and not isinstance(value, str):
        raise PolicyApprovalArtifactError("INVALID_FIELD_TYPE", f"{field} must be a string or null")
    return value


def _parse_artifact_date(value: object) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise PolicyApprovalArtifactError(
            "INVALID_FIELD_TYPE", "approved_effective_date must be an ISO date or null"
        )
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise PolicyApprovalArtifactError(
            "INVALID_DATE", "approved_effective_date must be a canonical ISO date"
        ) from exc


__all__ = [
    "ALLOWED",
    "APPROVED",
    "BLOCKED",
    "POLICY_APPROVAL_SCHEMA_VERSION",
    "PolicyApprovalArtifactError",
    "PolicyApprovalDecision",
    "PolicyApprovalError",
    "PolicyApprovalRecord",
    "evaluate_policy_approval",
    "export_policy_approval_artifact",
    "parse_policy_approval_artifact",
    "require_policy_approval",
]
