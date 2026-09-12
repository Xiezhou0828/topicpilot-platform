"""Fail-closed Structural Role Authority read and as-of resolution."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..orm.models import InstrumentTopicRelation

STRUCTURAL_ROLE_REPRESENTATIVE = "REPRESENTATIVE"
STRUCTURAL_ROLE_CORE = "CORE"
STRUCTURAL_ROLE_RELATED = "RELATED"
STRUCTURAL_ROLES = frozenset(
    {
        STRUCTURAL_ROLE_REPRESENTATIVE,
        STRUCTURAL_ROLE_CORE,
        STRUCTURAL_ROLE_RELATED,
    }
)
AUTHORITY_READ_CURRENT = "CURRENT"
AUTHORITY_READ_HISTORICAL = "HISTORICAL"
AUTHORITY_APPROVED = "APPROVED"


class StructuralRoleAuthorityError(ValueError):
    """Raised when a formal role authority cannot be resolved safely."""


@dataclass(frozen=True)
class StructuralRoleAuthorityRecord:
    """Immutable formal projection of one InstrumentTopicRelation row."""

    authority_id: str
    topic_id: str
    instrument_id: str
    structural_role: str | None
    approval_state: str | None
    effective_from: date
    effective_to: date | None
    authority_version: str | None
    source_artifact_id: str | None
    source_artifact_hash: str | None
    approval_reference: str | None
    correction_sequence: int | None
    supersedes_authority_id: str | None
    superseded_by_authority_id: str | None
    lineage_hash: str | None

    @classmethod
    def from_relation(cls, relation: InstrumentTopicRelation) -> StructuralRoleAuthorityRecord:
        return cls(
            authority_id=str(relation.id),
            topic_id=str(relation.topic_id),
            instrument_id=str(relation.instrument_id),
            structural_role=relation.structural_role,
            approval_state=relation.approval_state,
            effective_from=relation.valid_from,
            effective_to=relation.valid_to,
            authority_version=relation.authority_version,
            source_artifact_id=relation.source_artifact_id,
            source_artifact_hash=relation.source_artifact_hash,
            approval_reference=relation.approval_reference,
            correction_sequence=relation.correction_sequence,
            supersedes_authority_id=(
                str(relation.supersedes_authority_id)
                if relation.supersedes_authority_id is not None
                else None
            ),
            superseded_by_authority_id=(
                str(relation.superseded_by_authority_id)
                if relation.superseded_by_authority_id is not None
                else None
            ),
            lineage_hash=relation.lineage_hash,
        )


@dataclass(frozen=True)
class StructuralRoleResolution:
    """Resolved authority plus the explicit read boundary used."""

    record: StructuralRoleAuthorityRecord
    as_of: date
    read_mode: str

    @property
    def authority_id(self) -> str:
        return self.record.authority_id

    @property
    def structural_role(self) -> str:
        if self.record.structural_role is None:  # pragma: no cover - guarded by resolver
            raise StructuralRoleAuthorityError("resolved structural role is missing")
        return self.record.structural_role

    @property
    def is_superseded(self) -> bool:
        return self.record.superseded_by_authority_id is not None


def _required_text(value: str | None, field: str) -> str:
    if value is None or not value.strip() or value != value.strip():
        raise StructuralRoleAuthorityError(f"{field} is missing or not canonical")
    return value


def _validate_record(record: StructuralRoleAuthorityRecord) -> None:
    if record.structural_role not in STRUCTURAL_ROLES:
        raise StructuralRoleAuthorityError("structural role is missing or invalid")
    if record.approval_state != AUTHORITY_APPROVED:
        raise StructuralRoleAuthorityError("structural role authority is not APPROVED")
    _required_text(record.authority_version, "authority_version")
    _required_text(record.source_artifact_id, "source_artifact_id")
    _required_text(record.source_artifact_hash, "source_artifact_hash")
    _required_text(record.approval_reference, "approval_reference")
    _required_text(record.lineage_hash, "lineage_hash")
    if record.correction_sequence is None or record.correction_sequence < 0:
        raise StructuralRoleAuthorityError("correction_sequence is missing or invalid")
    if record.supersedes_authority_id == record.authority_id:
        raise StructuralRoleAuthorityError("authority cannot supersede itself")
    if record.superseded_by_authority_id == record.authority_id:
        raise StructuralRoleAuthorityError("authority cannot be superseded by itself")


def _effective(record: StructuralRoleAuthorityRecord, as_of: date) -> bool:
    return record.effective_from <= as_of and (
        record.effective_to is None or as_of <= record.effective_to
    )


def resolve_structural_role_records(
    records: Iterable[StructuralRoleAuthorityRecord],
    topic_id: str | UUID,
    instrument_id: str | UUID,
    as_of: date,
    *,
    read_mode: str = AUTHORITY_READ_CURRENT,
) -> StructuralRoleResolution:
    """Resolve one formal role from already-loaded relation records.

    ``CURRENT`` excludes superseded authorities. ``HISTORICAL`` preserves the
    authority that was effective on the requested date, including an older
    row that has a later approved successor.
    """

    if read_mode not in {AUTHORITY_READ_CURRENT, AUTHORITY_READ_HISTORICAL}:
        raise StructuralRoleAuthorityError("read_mode must be CURRENT or HISTORICAL")
    topic_key = str(topic_id)
    instrument_key = str(instrument_id)
    matched = tuple(
        record
        for record in records
        if record.topic_id == topic_key and record.instrument_id == instrument_key
    )
    if not matched:
        raise StructuralRoleAuthorityError("STRUCTURAL_ROLE_AUTHORITY_MISSING")

    effective = tuple(record for record in matched if _effective(record, as_of))
    if not effective:
        raise StructuralRoleAuthorityError("STRUCTURAL_ROLE_AUTHORITY_NOT_EFFECTIVE")
    for record in effective:
        _validate_record(record)

    if read_mode == AUTHORITY_READ_CURRENT:
        candidates = tuple(
            record for record in effective if record.superseded_by_authority_id is None
        )
        if not candidates:
            raise StructuralRoleAuthorityError("STRUCTURAL_ROLE_AUTHORITY_SUPERSEDED")
    else:
        candidates = effective

    if len(candidates) != 1:
        raise StructuralRoleAuthorityError("STRUCTURAL_ROLE_AUTHORITY_CONFLICT")
    return StructuralRoleResolution(record=candidates[0], as_of=as_of, read_mode=read_mode)


def resolve_structural_role(
    session: Session,
    topic_id: str | UUID,
    instrument_id: str | UUID,
    as_of: date,
    *,
    read_mode: str = AUTHORITY_READ_CURRENT,
) -> StructuralRoleResolution:
    """Resolve formal role authority from the canonical relation carrier."""

    rows = session.scalars(
        select(InstrumentTopicRelation).where(
            InstrumentTopicRelation.topic_id == topic_id,
            InstrumentTopicRelation.instrument_id == instrument_id,
            InstrumentTopicRelation.structural_role.is_not(None),
        )
    ).all()
    return resolve_structural_role_records(
        (StructuralRoleAuthorityRecord.from_relation(row) for row in rows),
        topic_id,
        instrument_id,
        as_of,
        read_mode=read_mode,
    )


__all__ = [
    "AUTHORITY_APPROVED",
    "AUTHORITY_READ_CURRENT",
    "AUTHORITY_READ_HISTORICAL",
    "STRUCTURAL_ROLES",
    "STRUCTURAL_ROLE_CORE",
    "STRUCTURAL_ROLE_RELATED",
    "STRUCTURAL_ROLE_REPRESENTATIVE",
    "StructuralRoleAuthorityError",
    "StructuralRoleAuthorityRecord",
    "StructuralRoleResolution",
    "resolve_structural_role",
    "resolve_structural_role_records",
]
