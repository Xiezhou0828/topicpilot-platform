"""Fail-closed bridge from formal PIT daily state to Topic Score policy input.

The migration-0030 snapshot and member-fact rows are the only source accepted
by this adapter.  It deliberately does not write PostgreSQL, register a
provider, or expose an API.  An explicit approval record, governed CORE set,
Leader Set, and observation as-of binding are required before the existing
non-activating Production V1 policy executor can evaluate a score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from .policy_approval import PolicyApprovalRecord, evaluate_policy_approval
from .production_policy import (
    POLICY_APPROVED,
    ParticipationObservation,
    ProductionTopicInput,
    ProductionV1Evaluation,
    ProductionV1PolicyBundle,
    evaluate_production_v1,
)
from .runtime_readiness import (
    LEADER_SET_APPROVED,
    GovernedLeaderSet,
    ObservationAsOfBinding,
)

FORMAL_TOPIC_SCORE_CONTRACT_VERSION = "topic-score-formal.v1"
FORMAL_PUBLICATION_MODE = "FORMAL"
FORMAL_MEMBERSHIP_MODE = "PIT_FORMAL"
FORMAL_PUBLICATION_STATE = "UNPUBLISHED"
FORMAL_MAPPING_EARLIEST_DATE = date(2026, 8, 7)
_FACT_STATES = frozenset({"OBSERVED", "NO_TRADE", "UNKNOWN"})


class FormalTopicScoreAuthorityError(ValueError):
    """Raised when a formal Topic Score input cannot be proven authoritative."""


@dataclass(frozen=True)
class FormalTopicScoreSnapshot:
    """The typed 0030 authority required for one score evaluation."""

    snapshot_id: str
    snapshot_identity: str
    topic_id: str
    snapshot_date: date
    publication_mode: str
    membership_mode: str
    publication_state: str
    superseded_by_snapshot_id: str | None
    finality_state: str
    trading_day_state: str
    session_code: str
    calendar_code: str
    mapping_effective_from: date | None
    membership_snapshot_id: str | None
    membership_snapshot_hash: str | None
    relation_version: str | None
    reference_registry_version: str | None
    source_artifact_id: str | None
    source_artifact_hash: str | None
    lineage_hash: str | None


@dataclass(frozen=True)
class FormalTopicScoreMemberFact:
    """The minimum immutable 0030 member fact needed by the scorer."""

    instrument_id: str
    observation_date: date
    fact_state: str
    change_pct: Decimal | float | int | None
    fact_hash: str
    source_artifact_id: str
    source_artifact_hash: str


@dataclass(frozen=True)
class FormalTopicScoreAuthority:
    """Explicit external authorities; no production defaults are supplied."""

    approval_record: PolicyApprovalRecord
    policy: ProductionV1PolicyBundle
    leader_set: GovernedLeaderSet
    core_member_ids: tuple[str, ...]
    core_authority_id: str
    observation_binding: ObservationAsOfBinding

    def __post_init__(self) -> None:
        decision = evaluate_policy_approval(self.approval_record)
        if not decision.allowed:
            raise FormalTopicScoreAuthorityError(f"policy approval blocked: {decision.reason_code}")
        if self.policy.lifecycle != POLICY_APPROVED:
            raise FormalTopicScoreAuthorityError("policy bundle is not APPROVED")
        if self.policy.policy_version != self.approval_record.approved_policy_version:
            raise FormalTopicScoreAuthorityError("policy version does not match approval")
        if self.policy.candidate_id != self.approval_record.approved_candidate_id:
            raise FormalTopicScoreAuthorityError("candidate id does not match approval")
        if self.policy.candidate_version != self.approval_record.approved_candidate_version:
            raise FormalTopicScoreAuthorityError("candidate version does not match approval")
        if self.policy.effective_date != self.approval_record.approved_effective_date:
            raise FormalTopicScoreAuthorityError("policy effective date does not match approval")
        for policy_field, approval_field in (
            ("breadth_policy_ref", "approved_breadth_policy"),
            ("leadership_policy_ref", "approved_leadership_policy"),
            ("normalization_policy_ref", "approved_normalization_policy"),
            ("aggregation_policy_ref", "approved_aggregation_policy"),
            ("weights_policy_ref", "approved_weights"),
            ("eligibility_policy_ref", "approved_eligibility_policy"),
            ("grade_threshold_ref", "approved_grade_thresholds"),
            ("rollback_policy", "rollback_policy"),
        ):
            if getattr(self.policy, policy_field) != getattr(self.approval_record, approval_field):
                raise FormalTopicScoreAuthorityError(f"{policy_field} does not match approval")
        if self.leader_set.lifecycle != LEADER_SET_APPROVED:
            raise FormalTopicScoreAuthorityError("Leader Set is not APPROVED")
        if not self.leader_set.artifact_id:
            raise FormalTopicScoreAuthorityError("Leader Set artifact is missing")
        if self.leader_set.version != self.policy.leader_set_version:
            raise FormalTopicScoreAuthorityError("Leader Set version does not match policy")
        if self.leader_set.effective_date is None:
            raise FormalTopicScoreAuthorityError("Leader Set effective date is missing")
        if not self.core_member_ids:
            raise FormalTopicScoreAuthorityError("formal CORE authority is missing")
        if any(
            not member_id.strip() or member_id != member_id.strip()
            for member_id in self.core_member_ids
        ):
            raise FormalTopicScoreAuthorityError("CORE member ids must be non-empty")
        if len(set(self.core_member_ids)) != len(self.core_member_ids):
            raise FormalTopicScoreAuthorityError("CORE member ids must be unique")
        if (
            not self.core_authority_id.strip()
            or self.core_authority_id != self.core_authority_id.strip()
        ):
            raise FormalTopicScoreAuthorityError("CORE authority identity is missing")
        if not self.observation_binding.latest_approved_session:
            raise FormalTopicScoreAuthorityError("observation is not the latest approved session")
        if not self.observation_binding.fresh:
            raise FormalTopicScoreAuthorityError("observation as-of binding is not fresh")
        if self.observation_binding.observation_count <= 0:
            raise FormalTopicScoreAuthorityError("observation as-of binding is empty")


@dataclass(frozen=True)
class FormalTopicScoreLineage:
    """Immutable provenance carried by a future formal publication writer."""

    contract_version: str
    snapshot_id: str
    snapshot_identity: str
    membership_snapshot_id: str
    membership_snapshot_hash: str
    relation_version: str
    reference_registry_version: str
    source_artifact_id: str
    source_artifact_hash: str
    snapshot_lineage_hash: str
    core_authority_id: str
    policy_id: str
    policy_version: str
    candidate_id: str
    candidate_version: str
    approval_report_digest: str
    leader_set_version: str
    leader_set_artifact_id: str
    observation_query_version: str
    observation_source_id: str
    observation_input_hash: str
    observation_session_code: str

    def as_dict(self) -> dict[str, str]:
        return {
            "contractVersion": self.contract_version,
            "snapshotId": self.snapshot_id,
            "snapshotIdentity": self.snapshot_identity,
            "membershipSnapshotId": self.membership_snapshot_id,
            "membershipSnapshotHash": self.membership_snapshot_hash,
            "relationVersion": self.relation_version,
            "referenceRegistryVersion": self.reference_registry_version,
            "sourceArtifactId": self.source_artifact_id,
            "sourceArtifactHash": self.source_artifact_hash,
            "snapshotLineageHash": self.snapshot_lineage_hash,
            "coreAuthorityId": self.core_authority_id,
            "policyId": self.policy_id,
            "policyVersion": self.policy_version,
            "candidateId": self.candidate_id,
            "candidateVersion": self.candidate_version,
            "approvalReportDigest": self.approval_report_digest,
            "leaderSetVersion": self.leader_set_version,
            "leaderSetArtifactId": self.leader_set_artifact_id,
            "observationQueryVersion": self.observation_query_version,
            "observationSourceId": self.observation_source_id,
            "observationInputHash": self.observation_input_hash,
            "observationSessionCode": self.observation_session_code,
        }


@dataclass(frozen=True)
class FormalTopicScorePublication:
    """Non-persistent publication envelope for the future formal read model."""

    evaluation: ProductionV1Evaluation
    lineage: FormalTopicScoreLineage
    publication_state: str = FORMAL_PUBLICATION_STATE

    def as_dict(self) -> dict[str, Any]:
        score = self.evaluation.score
        audit = self.evaluation.eligibility_audit
        return {
            "contractVersion": FORMAL_TOPIC_SCORE_CONTRACT_VERSION,
            "publicationMode": FORMAL_PUBLICATION_MODE,
            "publicationState": self.publication_state,
            "topicId": score.topic_id,
            "asOf": score.as_of.isoformat(),
            "status": score.status,
            "eligibility": score.eligibility,
            "score": score.score,
            "grade": score.grade,
            "components": [{"name": name, "value": value} for name, value in score.components],
            "eligibilityAudit": {
                "coreMemberCount": audit.core_member_count,
                "validObservedCoreCount": audit.valid_observed_core_count,
                "coreCoverage": audit.core_coverage,
                "latestApprovedSession": audit.latest_approved_session,
                "observationAsOf": (
                    audit.observation_as_of.isoformat() if audit.observation_as_of else None
                ),
                "eligible": audit.eligible,
                "excludedReasons": list(audit.excluded_reasons),
            },
            "lineage": self.lineage.as_dict(),
        }


def derive_formal_topic_score(
    snapshot: FormalTopicScoreSnapshot,
    facts: tuple[FormalTopicScoreMemberFact, ...],
    authority: FormalTopicScoreAuthority,
) -> FormalTopicScorePublication:
    """Derive one score from formal PIT evidence without persisting or activating it."""

    _validate_snapshot(snapshot)
    binding = authority.observation_binding
    if binding.as_of != snapshot.snapshot_date:
        raise FormalTopicScoreAuthorityError("observation as-of does not match snapshot date")
    if binding.session_code != snapshot.session_code:
        raise FormalTopicScoreAuthorityError("observation session does not match snapshot")
    if authority.leader_set.effective_date > snapshot.snapshot_date:
        raise FormalTopicScoreAuthorityError("Leader Set is not effective for snapshot date")

    ordered_facts = tuple(sorted(facts, key=lambda fact: fact.instrument_id))
    if not ordered_facts:
        raise FormalTopicScoreAuthorityError("formal member facts are missing")
    fact_ids = tuple(fact.instrument_id for fact in ordered_facts)
    if len(fact_ids) != len(set(fact_ids)):
        raise FormalTopicScoreAuthorityError("formal member facts must be unique by instrument")
    if not set(authority.core_member_ids).issubset(fact_ids):
        raise FormalTopicScoreAuthorityError("CORE authority references a non-member fact")

    leaders = authority.leader_set.leaders_for(snapshot.topic_id)
    if not leaders:
        raise FormalTopicScoreAuthorityError("approved Leader Set has no topic members")
    leader_ids = tuple(leader.member_id for leader in leaders)
    if not set(leader_ids).issubset(set(authority.core_member_ids)):
        raise FormalTopicScoreAuthorityError("Leader Set contains a non-CORE member")

    observations = tuple(
        ParticipationObservation(
            fact.instrument_id,
            _return_pct(fact, snapshot.snapshot_date),
        )
        for fact in ordered_facts
    )
    input_value = ProductionTopicInput(
        topic_id=snapshot.topic_id,
        as_of=snapshot.snapshot_date,
        core_member_ids=authority.core_member_ids,
        observations=observations,
        leaders=leaders,
        leader_set_version=authority.leader_set.version,
        observation_as_of=binding.as_of,
        latest_approved_session=binding.latest_approved_session and binding.fresh,
    )
    evaluation = evaluate_production_v1(input_value, authority.policy)
    lineage = FormalTopicScoreLineage(
        contract_version=FORMAL_TOPIC_SCORE_CONTRACT_VERSION,
        snapshot_id=snapshot.snapshot_id,
        snapshot_identity=snapshot.snapshot_identity,
        membership_snapshot_id=_required(snapshot.membership_snapshot_id, "membership snapshot id"),
        membership_snapshot_hash=_required(
            snapshot.membership_snapshot_hash, "membership snapshot hash"
        ),
        relation_version=_required(snapshot.relation_version, "relation version"),
        reference_registry_version=_required(
            snapshot.reference_registry_version, "reference registry version"
        ),
        source_artifact_id=_required(snapshot.source_artifact_id, "source artifact id"),
        source_artifact_hash=_required(snapshot.source_artifact_hash, "source artifact hash"),
        snapshot_lineage_hash=_required(snapshot.lineage_hash, "snapshot lineage hash"),
        core_authority_id=authority.core_authority_id,
        policy_id=authority.policy.policy_id,
        policy_version=authority.policy.policy_version,
        candidate_id=authority.policy.candidate_id,
        candidate_version=authority.policy.candidate_version,
        approval_report_digest=authority.approval_record.reviewed_report_digest,
        leader_set_version=authority.leader_set.version,
        leader_set_artifact_id=_required(
            authority.leader_set.artifact_id, "Leader Set artifact id"
        ),
        observation_query_version=binding.query_version,
        observation_source_id=binding.source_id,
        observation_input_hash=binding.input_hash,
        observation_session_code=binding.session_code,
    )
    return FormalTopicScorePublication(evaluation=evaluation, lineage=lineage)


def _validate_snapshot(snapshot: FormalTopicScoreSnapshot) -> None:
    for name in (
        "snapshot_id",
        "snapshot_identity",
        "topic_id",
        "session_code",
        "calendar_code",
    ):
        _required(getattr(snapshot, name), name)
    if snapshot.publication_mode != FORMAL_PUBLICATION_MODE:
        raise FormalTopicScoreAuthorityError("snapshot is not FORMAL")
    if snapshot.membership_mode != FORMAL_MEMBERSHIP_MODE:
        raise FormalTopicScoreAuthorityError("snapshot is not PIT_FORMAL")
    if snapshot.publication_state != "PUBLISHED":
        raise FormalTopicScoreAuthorityError("snapshot is not PUBLISHED")
    if snapshot.superseded_by_snapshot_id is not None:
        raise FormalTopicScoreAuthorityError("snapshot is superseded")
    if snapshot.finality_state != "FINAL":
        raise FormalTopicScoreAuthorityError("snapshot is not FINAL")
    if snapshot.trading_day_state != "TRADING":
        raise FormalTopicScoreAuthorityError("snapshot is not a trading day")
    if snapshot.snapshot_date < FORMAL_MAPPING_EARLIEST_DATE:
        raise FormalTopicScoreAuthorityError("snapshot is before the formal PIT boundary")
    if snapshot.mapping_effective_from != FORMAL_MAPPING_EARLIEST_DATE:
        raise FormalTopicScoreAuthorityError("snapshot mapping boundary is not canonical")


def _return_pct(fact: FormalTopicScoreMemberFact, authority_date: date) -> float | None:
    if fact.fact_state not in _FACT_STATES:
        raise FormalTopicScoreAuthorityError(f"unknown member fact state: {fact.fact_state}")
    for name, value in (
        ("instrument id", fact.instrument_id),
        ("fact hash", fact.fact_hash),
        ("source artifact id", fact.source_artifact_id),
        ("source artifact hash", fact.source_artifact_hash),
    ):
        _required(value, name)
    if fact.observation_date != authority_date:
        raise FormalTopicScoreAuthorityError("member fact date does not match snapshot")
    if fact.fact_state != "OBSERVED":
        if fact.change_pct is not None:
            raise FormalTopicScoreAuthorityError(
                "non-observed member facts cannot carry a return fallback"
            )
        return None
    if fact.change_pct is None:
        return None
    if isinstance(fact.change_pct, bool):
        raise FormalTopicScoreAuthorityError("member return must be numeric or null")
    value = float(fact.change_pct)
    if not math.isfinite(value):
        raise FormalTopicScoreAuthorityError("member return must be finite")
    return value


def _required(value: str | None, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise FormalTopicScoreAuthorityError(f"{label} must be a trimmed non-empty value")
    return value


__all__ = [
    "FORMAL_MAPPING_EARLIEST_DATE",
    "FORMAL_MEMBERSHIP_MODE",
    "FORMAL_PUBLICATION_MODE",
    "FORMAL_PUBLICATION_STATE",
    "FORMAL_TOPIC_SCORE_CONTRACT_VERSION",
    "FormalTopicScoreAuthority",
    "FormalTopicScoreAuthorityError",
    "FormalTopicScoreLineage",
    "FormalTopicScoreMemberFact",
    "FormalTopicScorePublication",
    "FormalTopicScoreSnapshot",
    "derive_formal_topic_score",
]
