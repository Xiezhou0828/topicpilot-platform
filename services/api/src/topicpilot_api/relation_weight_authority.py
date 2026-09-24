"""Governed Topic Relation Weight authority and deterministic proposal support.

Relation Weight is intentionally independent from Structural Role, Score
Importance, Topic Score, Grade, Lifecycle, and Today rotation.  This module is
the only application-level authority resolver for relation weights.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .orm import Instrument, InstrumentTopicRelation, Market, RelationWeightAuthority, Topic
from .orm.relation_weights import (
    RELATION_WEIGHT_AUTHORITY_EFFECTIVE_DATE,
    RELATION_WEIGHT_AUTHORITY_VERSION,
)

PRIMARY_MIN = Decimal("0.5")
PRIMARY_MAX = Decimal("2.0")
SECONDARY_MIN = Decimal("0.3")
SECONDARY_MAX = Decimal("0.8")
PRIMARY_DEFAULT = Decimal("1.0")
SECONDARY_DEFAULT = Decimal("0.5")
PROPOSAL_SOURCE_LEGACY = "LEGACY_RECOVERED"
PROPOSAL_SOURCE_DEFAULT = "DEFAULT_INITIALIZATION"
PROPOSAL_SOURCE_INVALID_LEGACY_DEFAULT = "INVALID_LEGACY_DEFAULT_INITIALIZATION"
APPROVAL_PROPOSED = "PROPOSED"
APPROVAL_APPROVED = "APPROVED"
OWNER_APPROVAL_APPLY_ENABLED = False

_UUID_NAMESPACE = uuid.UUID("f3b3c27d-0d36-4c09-8f35-2dd0b9152f2b")


class RelationWeightError(ValueError):
    """Base error for fail-closed Relation Weight validation."""


class RelationWeightIdentityError(RelationWeightError):
    """Raised when an exact relation identity cannot be resolved."""


class RelationWeightRangeError(RelationWeightError):
    """Raised for a missing, non-numeric, or out-of-range weight."""


class RelationWeightApprovalError(RelationWeightError):
    """Raised when a proposal is treated as formal without approval."""


@dataclass(frozen=True, order=True)
class RelationIdentity:
    market: str
    instrument: str
    topic: str
    relation_type: str

    def as_tuple(self) -> tuple[str, str, str, str]:
        return (self.market, self.instrument, self.topic, self.relation_type)


@dataclass(frozen=True)
class RelationWeightProposal:
    id: uuid.UUID
    identity: RelationIdentity
    relation_id: str | None
    instrument_id: str | None
    topic_id: str | None
    weight: Decimal
    legacy_original_value: Decimal | None
    legacy_recovery_evidence: dict[str, Any] | None
    approval_state: str
    effective_from: date
    effective_to: date | None
    authority_version: str
    approval_reference: str | None
    source_kind: str
    source_artifact_id: str | None
    source_artifact_hash: str | None
    source_location: str | None
    proposal_reason: str
    correction_sequence: int
    supersedes_id: uuid.UUID | None
    lineage_hash: str


@dataclass(frozen=True)
class ProposalGenerationResult:
    proposals: tuple[RelationWeightProposal, ...]
    current_relation_count: int
    primary_relation_count: int
    secondary_relation_count: int
    legacy_recovered_count: int
    invalid_legacy_defaulted_count: int
    default_initialization_count: int
    ambiguous_history_count: int
    missing_history_count: int
    unresolved_relation_count: int
    ambiguous_identity_count: int


@dataclass(frozen=True)
class RelationWeightReadModel:
    relation_id: str
    current_proposal: RelationWeightProposal | None
    current_approved: RelationWeightProposal | None

    @property
    def formal_weight(self) -> Decimal | None:
        """Return only approved authority; never fall back to proposal."""

        return self.current_approved.weight if self.current_approved else None


def _field(row: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None


def _required_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RelationWeightIdentityError(f"{field_name} is required for exact relation identity")
    return text


def relation_identity(row: Mapping[str, Any]) -> RelationIdentity:
    relation_type = _required_text(
        _field(row, "relation_type", "relationType"), "relation_type"
    ).upper()
    if relation_type not in {"PRIMARY", "SECONDARY"}:
        raise RelationWeightIdentityError(f"unsupported relation_type: {relation_type}")
    return RelationIdentity(
        market=_required_text(_field(row, "market", "market_code", "marketCode"), "market"),
        instrument=_required_text(
            _field(row, "symbol", "instrument", "instrument_code", "instrumentCode"),
            "instrument",
        ),
        topic=_required_text(
            _field(row, "topic", "topic_slug", "topicSlug", "topic_id", "topicId"), "topic"
        ),
        relation_type=relation_type,
    )


def parse_weight(value: Any, *, relation_type: str) -> Decimal:
    """Parse a decimal without coercing blanks, booleans, NaN, or bad tokens."""

    if isinstance(value, bool) or value is None:
        raise RelationWeightRangeError("weight must be a numeric decimal")
    if isinstance(value, str) and not value.strip():
        raise RelationWeightRangeError("weight must not be blank")
    try:
        weight = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise RelationWeightRangeError(f"invalid numeric weight: {value!r}") from exc
    if not weight.is_finite():
        raise RelationWeightRangeError("weight must be finite")
    relation_type = relation_type.upper()
    if relation_type == "PRIMARY":
        minimum, maximum = PRIMARY_MIN, PRIMARY_MAX
    elif relation_type == "SECONDARY":
        minimum, maximum = SECONDARY_MIN, SECONDARY_MAX
    else:
        raise RelationWeightRangeError(f"unsupported relation_type: {relation_type}")
    if not minimum <= weight <= maximum:
        raise RelationWeightRangeError(
            f"{relation_type} weight {weight} outside inclusive range {minimum}-{maximum}"
        )
    return weight


def parse_legacy_value(value: Any) -> Decimal:
    """Parse a legacy numeric value without applying the current range."""

    if isinstance(value, bool) or value is None:
        raise RelationWeightRangeError("legacy value must be numeric")
    if isinstance(value, str) and not value.strip():
        raise RelationWeightRangeError("legacy value must not be blank")
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise RelationWeightRangeError(f"invalid legacy numeric value: {value!r}") from exc
    if not parsed.is_finite():
        raise RelationWeightRangeError("legacy value must be finite")
    return parsed


def default_weight(relation_type: str) -> Decimal:
    relation_type = relation_type.upper()
    if relation_type == "PRIMARY":
        return PRIMARY_DEFAULT
    if relation_type == "SECONDARY":
        return SECONDARY_DEFAULT
    raise RelationWeightRangeError(f"unsupported relation_type: {relation_type}")


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _lineage_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _proposal_id(identity: RelationIdentity, *, effective_from: date, version: str) -> uuid.UUID:
    return uuid.uuid5(
        _UUID_NAMESPACE,
        "|".join((*identity.as_tuple(), effective_from.isoformat(), version)),
    )


def _artifact_value(
    row: Mapping[str, Any], *, source_artifact_id: str | None, source_artifact_hash: str | None
) -> tuple[str | None, str | None, str | None]:
    return (
        str(_field(row, "source_artifact_id", "sourceArtifactId") or source_artifact_id or "")
        or None,
        str(_field(row, "source_artifact_hash", "sourceArtifactHash") or source_artifact_hash or "")
        or None,
        str(_field(row, "historical_source", "source_location", "sourceLocation") or "") or None,
    )


def _legacy_evidence(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "recoveryStatus": _field(row, "recovery_status", "recoveryStatus"),
        "historicalWeight": _field(row, "historical_weight", "historicalWeight"),
        "historicalSource": _field(row, "historical_source", "source_location", "sourceLocation"),
        "sourceRows": _field(row, "source_rows", "sourceRows"),
        "confidence": _field(row, "confidence"),
        "recommendedAction": _field(row, "recommended_action", "recommendedAction"),
        "notes": _field(row, "notes"),
    }


def generate_proposals(
    current_relations: Iterable[Mapping[str, Any]],
    historical_evidence: Iterable[Mapping[str, Any]],
    *,
    effective_from: date = RELATION_WEIGHT_AUTHORITY_EFFECTIVE_DATE,
    authority_version: str = RELATION_WEIGHT_AUTHORITY_VERSION,
    source_artifact_id: str | None = None,
    source_artifact_hash: str | None = None,
) -> ProposalGenerationResult:
    """Generate exactly one deterministic proposal per current relation.

    The caller must supply the current canonical relation universe.  Historical
    evidence is matched only by market + instrument + topic + relation_type.
    """

    if effective_from < RELATION_WEIGHT_AUTHORITY_EFFECTIVE_DATE:
        raise RelationWeightError("formal Relation Weight authority cannot be backdated")

    current_by_identity: dict[RelationIdentity, Mapping[str, Any]] = {}
    for row in current_relations:
        identity = relation_identity(row)
        if identity in current_by_identity:
            raise RelationWeightIdentityError(f"duplicate current relation identity: {identity}")
        current_by_identity[identity] = row

    evidence_by_identity: dict[RelationIdentity, Mapping[str, Any]] = {}
    for row in historical_evidence:
        identity = relation_identity(row)
        if identity in evidence_by_identity:
            raise RelationWeightIdentityError(f"duplicate historical evidence identity: {identity}")
        evidence_by_identity[identity] = row

    unresolved = sorted(set(current_by_identity) - set(evidence_by_identity))
    extra = sorted(set(evidence_by_identity) - set(current_by_identity))
    if unresolved or extra:
        raise RelationWeightIdentityError(
            "historical evidence must cover the exact current relation universe; "
            f"unresolved={len(unresolved)}, extra={len(extra)}"
        )

    proposals: list[RelationWeightProposal] = []
    legacy_recovered = invalid_legacy_defaulted = ambiguous_history = missing_history = 0
    for identity in sorted(current_by_identity):
        current = current_by_identity[identity]
        evidence = evidence_by_identity[identity]
        recovery_status = str(_field(evidence, "recovery_status", "recoveryStatus") or "").strip()
        legacy_original_value: Decimal | None = None
        legacy_recovery_evidence = _legacy_evidence(evidence)
        if recovery_status == "RECOVERABLE_WITH_OWNER_CONFIRMATION":
            legacy_original_value = parse_legacy_value(
                _field(evidence, "historical_weight", "historicalWeight")
            )
            try:
                weight = parse_weight(legacy_original_value, relation_type=identity.relation_type)
            except RelationWeightRangeError:
                weight = default_weight(identity.relation_type)
                source_kind = PROPOSAL_SOURCE_INVALID_LEGACY_DEFAULT
                proposal_reason = (
                    "LEGACY_VALUE_INVALID_UNDER_CURRENT_POLICY; CURRENT_DEFAULT_PROPOSAL"
                )
                invalid_legacy_defaulted += 1
            else:
                source_kind = PROPOSAL_SOURCE_LEGACY
                proposal_reason = "RECOVERABLE_HISTORICAL_VALUE; OWNER_REVIEW_REQUIRED"
                legacy_recovered += 1
        else:
            weight = default_weight(identity.relation_type)
            source_kind = PROPOSAL_SOURCE_DEFAULT
            if recovery_status == "RELATIONS_WITH_AMBIGUOUS_SOURCE":
                proposal_reason = "AMBIGUOUS_HISTORICAL_WEIGHT; DO_NOT_RECONSTRUCT"
                ambiguous_history += 1
            elif recovery_status == "NO_HISTORICAL_WEIGHT":
                proposal_reason = "NO_HISTORICAL_WEIGHT; DEFAULT_INITIALIZATION"
                missing_history += 1
            else:
                raise RelationWeightError(
                    f"unsupported historical recovery status for {identity}: {recovery_status!r}"
                )

        relation_id = _field(current, "relation_id", "relationId", "id")
        relation_id_text = str(relation_id) if relation_id else None
        instrument_id = _field(current, "instrument_id", "instrumentId")
        topic_id = _field(current, "topic_id", "topicId")
        source_id, source_hash, source_location = _artifact_value(
            evidence,
            source_artifact_id=source_artifact_id,
            source_artifact_hash=source_artifact_hash,
        )
        proposal_key = {
            "identity": identity.as_tuple(),
            "relationId": relation_id_text,
            "weight": str(weight),
            "legacyOriginalValue": (
                str(legacy_original_value) if legacy_original_value is not None else None
            ),
            "legacyRecoveryEvidence": legacy_recovery_evidence,
            "approvalState": APPROVAL_PROPOSED,
            "effectiveFrom": effective_from.isoformat(),
            "authorityVersion": authority_version,
            "sourceKind": source_kind,
            "sourceArtifactId": source_id,
            "sourceArtifactHash": source_hash,
            "sourceLocation": source_location,
            "proposalReason": proposal_reason,
        }
        lineage_hash = _lineage_hash(proposal_key)
        proposals.append(
            RelationWeightProposal(
                id=_proposal_id(identity, effective_from=effective_from, version=authority_version),
                identity=identity,
                relation_id=relation_id_text,
                instrument_id=str(instrument_id) if instrument_id else None,
                topic_id=str(topic_id) if topic_id else None,
                weight=weight,
                legacy_original_value=legacy_original_value,
                legacy_recovery_evidence=legacy_recovery_evidence,
                approval_state=APPROVAL_PROPOSED,
                effective_from=effective_from,
                effective_to=None,
                authority_version=authority_version,
                approval_reference=None,
                source_kind=source_kind,
                source_artifact_id=source_id,
                source_artifact_hash=source_hash,
                source_location=source_location,
                proposal_reason=proposal_reason,
                correction_sequence=0,
                supersedes_id=None,
                lineage_hash=lineage_hash,
            )
        )

    return ProposalGenerationResult(
        proposals=tuple(proposals),
        current_relation_count=len(proposals),
        primary_relation_count=sum(p.identity.relation_type == "PRIMARY" for p in proposals),
        secondary_relation_count=sum(p.identity.relation_type == "SECONDARY" for p in proposals),
        legacy_recovered_count=legacy_recovered,
        invalid_legacy_defaulted_count=invalid_legacy_defaulted,
        default_initialization_count=ambiguous_history + missing_history,
        ambiguous_history_count=ambiguous_history,
        missing_history_count=missing_history,
        unresolved_relation_count=0,
        ambiguous_identity_count=0,
    )


def _proposal_from_model(row: RelationWeightAuthority) -> RelationWeightProposal:
    raise NotImplementedError("ORM-to-proposal conversion requires joined market/topic identity")


def resolve_relation_weight_read_model(
    session: Session, relation_id: uuid.UUID | str, *, as_of_date: date
) -> RelationWeightReadModel:
    """Read proposal and approved authority without proposal fallback."""

    relation_uuid = uuid.UUID(str(relation_id))
    rows = session.scalars(
        select(RelationWeightAuthority)
        .where(
            RelationWeightAuthority.relation_id == relation_uuid,
            RelationWeightAuthority.effective_from <= as_of_date,
            (RelationWeightAuthority.effective_to.is_(None))
            | (RelationWeightAuthority.effective_to >= as_of_date),
        )
        .order_by(
            RelationWeightAuthority.effective_from.desc(),
            RelationWeightAuthority.correction_sequence.desc(),
            RelationWeightAuthority.created_at.desc(),
        )
    ).all()
    proposal_row = next((row for row in rows if row.approval_state == APPROVAL_PROPOSED), None)
    approved_row = next((row for row in rows if row.approval_state == APPROVAL_APPROVED), None)

    def convert(row: RelationWeightAuthority | None) -> RelationWeightProposal | None:
        if row is None:
            return None
        identity = RelationIdentity(
            market="",
            instrument=str(row.instrument_id),
            topic=str(row.topic_id),
            relation_type=row.relation_type,
        )
        return RelationWeightProposal(
            id=row.id,
            identity=identity,
            relation_id=str(row.relation_id),
            instrument_id=str(row.instrument_id),
            topic_id=str(row.topic_id),
            weight=Decimal(row.weight),
            legacy_original_value=(
                Decimal(row.legacy_original_value)
                if row.legacy_original_value is not None
                else None
            ),
            legacy_recovery_evidence=row.legacy_recovery_evidence,
            approval_state=row.approval_state,
            effective_from=row.effective_from,
            effective_to=row.effective_to,
            authority_version=row.authority_version,
            approval_reference=row.approval_reference,
            source_kind=row.source_kind,
            source_artifact_id=row.source_artifact_id,
            source_artifact_hash=row.source_artifact_hash,
            source_location=row.source_location,
            proposal_reason=row.proposal_reason or "",
            correction_sequence=row.correction_sequence,
            supersedes_id=row.supersedes_id,
            lineage_hash=row.lineage_hash,
        )

    return RelationWeightReadModel(
        relation_id=str(relation_uuid),
        current_proposal=convert(proposal_row),
        current_approved=convert(approved_row),
    )


def resolve_approved_weight(
    session: Session, relation_id: uuid.UUID | str, *, as_of_date: date
) -> Decimal | None:
    """Fail-closed formal resolver: PROPOSED is never substituted."""

    return resolve_relation_weight_read_model(
        session, relation_id, as_of_date=as_of_date
    ).formal_weight


def resolve_approved_weight_by_identity(
    session: Session, identity: RelationIdentity, *, as_of_date: date
) -> Decimal | None:
    """Resolve by exact market + instrument + topic + relation_type identity."""

    relation_rows = session.execute(
        select(InstrumentTopicRelation.id)
        .join(Instrument, Instrument.id == InstrumentTopicRelation.instrument_id)
        .join(Market, Market.id == Instrument.market_id)
        .join(Topic, Topic.id == InstrumentTopicRelation.topic_id)
        .where(
            Market.code == identity.market,
            Instrument.instrument_code == identity.instrument,
            Topic.slug == identity.topic,
            InstrumentTopicRelation.relation_type == identity.relation_type,
            InstrumentTopicRelation.valid_from <= as_of_date,
            (InstrumentTopicRelation.valid_to.is_(None))
            | (InstrumentTopicRelation.valid_to >= as_of_date),
        )
    ).scalars().all()
    if len(relation_rows) != 1:
        raise RelationWeightIdentityError(
            f"exact identity resolved to {len(relation_rows)} relation rows: {identity}"
        )
    return resolve_approved_weight(session, relation_rows[0], as_of_date=as_of_date)


def load_proposals_nonproduction(
    session: Session,
    result: ProposalGenerationResult,
    *,
    nonproduction: bool = True,
) -> int:
    """Idempotently load proposals into an explicitly non-production session."""

    if not nonproduction:
        raise RelationWeightApprovalError("proposal loading is restricted to non-production")
    inserted = 0
    for proposal in result.proposals:
        if proposal.relation_id is None:
            raise RelationWeightIdentityError(
                f"non-production load requires canonical relation_id: {proposal.identity}"
            )
        relation_uuid = uuid.UUID(proposal.relation_id)
        existing = session.scalar(
            select(RelationWeightAuthority).where(
                RelationWeightAuthority.relation_id == relation_uuid,
                RelationWeightAuthority.authority_version == proposal.authority_version,
                RelationWeightAuthority.effective_from == proposal.effective_from,
                RelationWeightAuthority.correction_sequence == proposal.correction_sequence,
            )
        )
        if existing is not None:
            if (
                Decimal(existing.weight) != proposal.weight
                or existing.approval_state != APPROVAL_PROPOSED
                or existing.lineage_hash != proposal.lineage_hash
            ):
                raise RelationWeightError(
                    f"non-deterministic existing proposal for relation {proposal.relation_id}"
                )
            continue
        session.add(
            RelationWeightAuthority(
                id=proposal.id,
                relation_id=relation_uuid,
                instrument_id=uuid.UUID(str(_require_uuid(proposal.instrument_id))),
                topic_id=uuid.UUID(str(_require_uuid(proposal.topic_id))),
                relation_type=proposal.identity.relation_type,
                weight=proposal.weight,
                legacy_original_value=proposal.legacy_original_value,
                legacy_recovery_evidence=proposal.legacy_recovery_evidence,
                approval_state=proposal.approval_state,
                effective_from=proposal.effective_from,
                effective_to=proposal.effective_to,
                authority_version=proposal.authority_version,
                approval_reference=proposal.approval_reference,
                source_kind=proposal.source_kind,
                source_artifact_id=proposal.source_artifact_id,
                source_artifact_hash=proposal.source_artifact_hash,
                source_location=proposal.source_location,
                proposal_reason=proposal.proposal_reason,
                correction_sequence=proposal.correction_sequence,
                supersedes_id=proposal.supersedes_id,
                lineage_hash=proposal.lineage_hash,
            )
        )
        inserted += 1
    session.flush()
    return inserted


def apply_owner_approved_proposal(
    session: Session,
    proposal_id: uuid.UUID | str,
    *,
    approval_reference: str,
    owner_approval_apply_enabled: bool = OWNER_APPROVAL_APPLY_ENABLED,
) -> None:
    """Reserved explicit apply boundary for the Owner-review task.

    001D deliberately keeps this disabled.  The function exists so an import
    path cannot silently turn workbook input into formal authority; 001E must
    explicitly enable and govern the mutation.
    """

    if not owner_approval_apply_enabled:
        raise RelationWeightApprovalError(
            "Owner approval/apply is disabled in 001D; use the governed 001E path"
        )
    if not approval_reference.strip():
        raise RelationWeightApprovalError("explicit approval_reference is required")
    raise RelationWeightApprovalError(
        "Owner approval/apply implementation is reserved for the governed 001E path"
    )


def _require_uuid(value: str) -> uuid.UUID:
    """Support DB loaders that pass UUID strings as identity fields."""

    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise RelationWeightIdentityError(
            "ORM proposal load requires instrument/topic UUID fields in the canonical relation row"
        ) from exc


def assert_formal_weight(value: Decimal | None, *, approval_state: str) -> Decimal:
    if approval_state != APPROVAL_APPROVED or value is None:
        raise RelationWeightApprovalError(
            "formal Relation Weight is unavailable without APPROVED authority"
        )
    return value


__all__ = [
    "APPROVAL_APPROVED",
    "APPROVAL_PROPOSED",
    "OWNER_APPROVAL_APPLY_ENABLED",
    "PRIMARY_DEFAULT",
    "PRIMARY_MAX",
    "PRIMARY_MIN",
    "PROPOSAL_SOURCE_INVALID_LEGACY_DEFAULT",
    "SECONDARY_DEFAULT",
    "SECONDARY_MAX",
    "SECONDARY_MIN",
    "ProposalGenerationResult",
    "RelationIdentity",
    "RelationWeightApprovalError",
    "RelationWeightError",
    "RelationWeightIdentityError",
    "RelationWeightProposal",
    "RelationWeightRangeError",
    "RelationWeightReadModel",
    "apply_owner_approved_proposal",
    "assert_formal_weight",
    "default_weight",
    "generate_proposals",
    "load_proposals_nonproduction",
    "parse_legacy_value",
    "parse_weight",
    "relation_identity",
    "resolve_approved_weight",
    "resolve_approved_weight_by_identity",
    "resolve_relation_weight_read_model",
]
