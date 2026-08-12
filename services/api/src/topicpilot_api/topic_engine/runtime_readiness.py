"""Fail-closed boundaries for the non-activating Production V1 runtime.

This module does not select a policy, create a Leader Set, infer an as-of
session, or turn a report into an approval. It only verifies that all
explicitly supplied, governed inputs line up before a future provider could be
activated.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime

from .policy_approval import PolicyApprovalRecord, evaluate_policy_approval
from .production_policy import (
    EligibilityAudit,
    LeaderDefinition,
    ProductionTopicInput,
    ProductionV1PolicyBundle,
    evaluate_production_v1,
)

RUNTIME_READY = "READY"
RUNTIME_BLOCKED = "BLOCKED"
LEADER_SET_APPROVED = "APPROVED"


class RuntimeReadinessError(ValueError):
    """Raised when an explicit readiness input violates its boundary."""


@dataclass(frozen=True)
class GovernedLeaderSet:
    """Explicit, versioned Leader Set input; no default set is supplied."""

    version: str
    lifecycle: str
    artifact_id: str | None
    effective_date: date | None
    topic_leaders: tuple[tuple[str, tuple[LeaderDefinition, ...]], ...]

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise RuntimeReadinessError("Leader Set version must be non-empty")
        if self.lifecycle.strip() != self.lifecycle or not self.lifecycle.strip():
            raise RuntimeReadinessError("Leader Set lifecycle must be a trimmed non-empty value")
        topic_ids = tuple(topic_id for topic_id, _ in self.topic_leaders)
        if any(not topic_id.strip() or topic_id != topic_id.strip() for topic_id in topic_ids):
            raise RuntimeReadinessError("Leader Set topic ids must be trimmed and non-empty")
        if len(topic_ids) != len(set(topic_ids)):
            raise RuntimeReadinessError("Leader Set topic ids must be unique")
        for topic_id, leaders in self.topic_leaders:
            leader_ids = tuple(leader.member_id for leader in leaders)
            if len(leader_ids) != len(set(leader_ids)):
                raise RuntimeReadinessError(f"Leader Set contains duplicate members for {topic_id}")

    def leaders_for(self, topic_id: str) -> tuple[LeaderDefinition, ...]:
        """Return only the explicitly governed leaders for one topic."""

        for candidate_topic_id, leaders in self.topic_leaders:
            if candidate_topic_id == topic_id:
                return leaders
        return ()


@dataclass(frozen=True)
class ObservationAsOfBinding:
    """The exact observation boundary a production evaluation is allowed to use."""

    query_version: str
    source_id: str
    as_of: date
    session_code: str
    latest_approved_session: bool
    fresh: bool
    observation_count: int
    input_hash: str
    bound_at: datetime

    def __post_init__(self) -> None:
        for field_name in ("query_version", "source_id", "session_code", "input_hash"):
            value = getattr(self, field_name)
            if not value.strip() or value != value.strip():
                raise RuntimeReadinessError(f"{field_name} must be a trimmed non-empty value")
        if self.observation_count < 0:
            raise RuntimeReadinessError("observation_count must not be negative")
        if self.bound_at.tzinfo is None or self.bound_at.utcoffset() is None:
            raise RuntimeReadinessError("bound_at must be timezone-aware")


@dataclass(frozen=True)
class EligibilityAuditReport:
    """Complete audit coverage for the V2 topic universe at one as-of date."""

    as_of: date
    topic_ids: tuple[str, ...]
    audits: tuple[EligibilityAudit, ...]

    def __post_init__(self) -> None:
        if len(self.topic_ids) != len(set(self.topic_ids)):
            raise RuntimeReadinessError("Eligibility Audit topic ids must be unique")
        audit_ids = tuple(audit.topic_id for audit in self.audits)
        if len(audit_ids) != len(set(audit_ids)):
            raise RuntimeReadinessError("Eligibility Audit rows must be unique by topic")
        if set(audit_ids) != set(self.topic_ids):
            raise RuntimeReadinessError("Eligibility Audit must cover the complete topic universe")
        if any(audit.as_of != self.as_of for audit in self.audits):
            raise RuntimeReadinessError("Eligibility Audit as-of values must match the report")

    @property
    def eligible_count(self) -> int:
        return sum(audit.eligible for audit in self.audits)

    @property
    def ineligible_count(self) -> int:
        return len(self.audits) - self.eligible_count


@dataclass(frozen=True)
class ActivationReadiness:
    """Deterministic activation decision and machine-readable blockers."""

    status: str
    blockers: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.status == RUNTIME_READY


def build_eligibility_audit_report(
    inputs: Iterable[ProductionTopicInput], policy: ProductionV1PolicyBundle
) -> EligibilityAuditReport:
    """Evaluate an explicit V2 topic universe without fetching or defaulting data."""

    ordered_inputs = tuple(sorted(inputs, key=lambda value: value.topic_id))
    topic_ids = tuple(value.topic_id for value in ordered_inputs)
    if not topic_ids:
        raise RuntimeReadinessError("Eligibility Audit requires a non-empty topic universe")
    if len(topic_ids) != len(set(topic_ids)):
        raise RuntimeReadinessError("Production topic inputs must be unique by topic")
    evaluations = tuple(evaluate_production_v1(value, policy) for value in ordered_inputs)
    as_ofs = {evaluation.eligibility_audit.as_of for evaluation in evaluations}
    if len(as_ofs) != 1:
        raise RuntimeReadinessError("Eligibility Audit requires one shared as-of date")
    return EligibilityAuditReport(
        as_of=next(iter(as_ofs)),
        topic_ids=topic_ids,
        audits=tuple(evaluation.eligibility_audit for evaluation in evaluations),
    )


def evaluate_activation_readiness(
    *,
    approval_record: PolicyApprovalRecord | None,
    policy: ProductionV1PolicyBundle | None,
    leader_set: GovernedLeaderSet | None,
    observation_binding: ObservationAsOfBinding | None,
    eligibility_audit: EligibilityAuditReport | None,
) -> ActivationReadiness:
    """Check production prerequisites without activating a provider."""

    blockers: list[str] = []
    if approval_record is None:
        blockers.append("APPROVAL_ARTIFACT_MISSING")
    else:
        decision = evaluate_policy_approval(approval_record)
        if not decision.allowed:
            blockers.append(f"POLICY_APPROVAL_BLOCKED:{decision.reason_code}")

    if policy is None:
        blockers.append("POLICY_BUNDLE_MISSING")
    else:
        if policy.lifecycle != "APPROVED":
            blockers.append("POLICY_BUNDLE_NOT_APPROVED")
        if approval_record is not None:
            if policy.policy_version != approval_record.approved_policy_version:
                blockers.append("POLICY_VERSION_MISMATCH")
            if policy.candidate_id != approval_record.approved_candidate_id:
                blockers.append("CANDIDATE_ID_MISMATCH")

    if leader_set is None:
        blockers.append("LEADER_SET_MISSING")
    else:
        if leader_set.lifecycle != LEADER_SET_APPROVED:
            blockers.append("LEADER_SET_NOT_APPROVED")
        if not leader_set.artifact_id:
            blockers.append("LEADER_SET_ARTIFACT_MISSING")
        if policy is not None and leader_set.version != policy.leader_set_version:
            blockers.append("LEADER_SET_VERSION_MISMATCH")

    if observation_binding is None:
        blockers.append("OBSERVATION_AS_OF_BINDING_MISSING")
    else:
        if not observation_binding.latest_approved_session:
            blockers.append("OBSERVATION_AS_OF_NOT_LATEST_APPROVED")
        if not observation_binding.fresh:
            blockers.append("OBSERVATION_AS_OF_NOT_FRESH")
        if observation_binding.observation_count == 0:
            blockers.append("OBSERVATION_AS_OF_EMPTY")

    if eligibility_audit is None:
        blockers.append("ELIGIBILITY_AUDIT_MISSING")
    elif observation_binding is not None and eligibility_audit.as_of != observation_binding.as_of:
        blockers.append("ELIGIBILITY_AUDIT_AS_OF_MISMATCH")

    return ActivationReadiness(
        RUNTIME_READY if not blockers else RUNTIME_BLOCKED,
        tuple(sorted(set(blockers))),
    )


__all__ = [
    "LEADER_SET_APPROVED",
    "RUNTIME_BLOCKED",
    "RUNTIME_READY",
    "ActivationReadiness",
    "EligibilityAuditReport",
    "GovernedLeaderSet",
    "ObservationAsOfBinding",
    "RuntimeReadinessError",
    "build_eligibility_audit_report",
    "evaluate_activation_readiness",
]
