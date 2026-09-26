"""Read-only Production boundary for persisted structural-role authority."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from .orm.models import Instrument, InstrumentTopicRelation, Market, Topic

ALLOWED_RELATION_TYPES = frozenset({"PRIMARY", "SECONDARY"})
ALLOWED_STRUCTURAL_ROLES = frozenset({"REPRESENTATIVE", "CORE", "RELATED"})
APPROVED_STATE = "APPROVED"


class StructuralRoleAuthorityReadError(ValueError):
    """Raised when current structural-role authority cannot be read safely."""


class StructuralRoleAuthorityReadItem(BaseModel):
    relation_id: str
    instrument_id: str
    instrument_code: str
    market_code: str
    topic_id: str
    topic_slug: str
    relation_type: Literal["PRIMARY", "SECONDARY"]
    structural_role: Literal["REPRESENTATIVE", "CORE", "RELATED"]
    approval_state: Literal["APPROVED"]
    authority_version: str
    effective_from: date
    effective_to: date | None
    source_artifact_id: str
    source_artifact_hash: str
    approval_reference: str
    correction_sequence: int
    supersedes_authority_id: str | None
    superseded_by_authority_id: str | None
    lineage_hash: str


class StructuralRoleAuthorityReadPage(BaseModel):
    items: list[StructuralRoleAuthorityReadItem]
    total: int
    limit: int
    offset: int
    has_more: bool
    as_of_date: date
    read_only: Literal[True] = True


@dataclass(frozen=True)
class StructuralRoleAuthorityCandidate:
    relation_id: str
    instrument_id: str
    instrument_code: str
    market_code: str
    topic_id: str
    topic_slug: str
    relation_type: str
    structural_role: str | None
    approval_state: str | None
    authority_version: str | None
    effective_from: date
    effective_to: date | None
    source_artifact_id: str | None
    source_artifact_hash: str | None
    approval_reference: str | None
    correction_sequence: int | None
    supersedes_authority_id: str | None
    superseded_by_authority_id: str | None
    lineage_hash: str | None


def _required_text(value: str | None, field: str, relation_id: str) -> str:
    if value is None or not value.strip() or value != value.strip():
        raise StructuralRoleAuthorityReadError(
            f"STRUCTURAL_ROLE_AUTHORITY_INVALID:{relation_id}:{field}"
        )
    return value


def _effective(row: StructuralRoleAuthorityCandidate, as_of: date) -> bool:
    return row.effective_from <= as_of and (
        row.effective_to is None or as_of <= row.effective_to
    )


def _validate_authority(row: StructuralRoleAuthorityCandidate) -> None:
    if row.relation_type not in ALLOWED_RELATION_TYPES:
        raise StructuralRoleAuthorityReadError(
            f"STRUCTURAL_ROLE_AUTHORITY_INVALID_RELATION_TYPE:{row.relation_id}"
        )
    if row.structural_role not in ALLOWED_STRUCTURAL_ROLES:
        raise StructuralRoleAuthorityReadError(
            f"STRUCTURAL_ROLE_AUTHORITY_INVALID_ROLE:{row.relation_id}"
        )
    if row.approval_state != APPROVED_STATE:
        raise StructuralRoleAuthorityReadError(
            f"STRUCTURAL_ROLE_AUTHORITY_NOT_APPROVED:{row.relation_id}"
        )
    for field in (
        "authority_version",
        "source_artifact_id",
        "source_artifact_hash",
        "approval_reference",
        "lineage_hash",
    ):
        _required_text(getattr(row, field), field, row.relation_id)
    if row.correction_sequence is None or row.correction_sequence < 0:
        raise StructuralRoleAuthorityReadError(
            f"STRUCTURAL_ROLE_AUTHORITY_INVALID_CORRECTION_SEQUENCE:{row.relation_id}"
        )
    if row.effective_to is not None and row.effective_to < row.effective_from:
        raise StructuralRoleAuthorityReadError(
            f"STRUCTURAL_ROLE_AUTHORITY_INVALID_EFFECTIVE_RANGE:{row.relation_id}"
        )
    if row.supersedes_authority_id == row.relation_id:
        raise StructuralRoleAuthorityReadError(
            f"STRUCTURAL_ROLE_AUTHORITY_SELF_SUPERSESSION:{row.relation_id}"
        )
    if row.superseded_by_authority_id == row.relation_id:
        raise StructuralRoleAuthorityReadError(
            f"STRUCTURAL_ROLE_AUTHORITY_SELF_SUPERSESSION:{row.relation_id}"
        )


def _validate_supersession_graph(
    rows: tuple[StructuralRoleAuthorityCandidate, ...],
) -> None:
    by_id = {row.relation_id: row for row in rows}
    if len(by_id) != len(rows):
        raise StructuralRoleAuthorityReadError("STRUCTURAL_ROLE_AUTHORITY_DUPLICATE_ID")
    for row in rows:
        for pointer_field, target_field in (
            ("supersedes_authority_id", "superseded_by_authority_id"),
            ("superseded_by_authority_id", "supersedes_authority_id"),
        ):
            target_id = getattr(row, pointer_field)
            if target_id is None:
                continue
            target = by_id.get(target_id)
            if target is None:
                raise StructuralRoleAuthorityReadError(
                    f"STRUCTURAL_ROLE_AUTHORITY_MISSING_SUPERSESSION_TARGET:{row.relation_id}"
                )
            if (target.instrument_id, target.topic_id) != (row.instrument_id, row.topic_id):
                raise StructuralRoleAuthorityReadError(
                    f"STRUCTURAL_ROLE_AUTHORITY_CROSS_IDENTITY_SUPERSESSION:{row.relation_id}"
                )
            if getattr(target, target_field) != row.relation_id:
                raise StructuralRoleAuthorityReadError(
                    f"STRUCTURAL_ROLE_AUTHORITY_AMBIGUOUS_SUPERSESSION:{row.relation_id}"
                )


def resolve_current_structural_role_authority(
    rows: tuple[StructuralRoleAuthorityCandidate, ...], as_of: date
) -> list[StructuralRoleAuthorityCandidate]:
    """Resolve one current authority per active instrument/topic identity."""

    _validate_supersession_graph(rows)
    for row in rows:
        if row.effective_to is not None and row.effective_to < row.effective_from:
            raise StructuralRoleAuthorityReadError(
                f"STRUCTURAL_ROLE_AUTHORITY_INVALID_EFFECTIVE_RANGE:{row.relation_id}"
            )
    grouped: dict[tuple[str, str], list[StructuralRoleAuthorityCandidate]] = defaultdict(list)
    for row in rows:
        if _effective(row, as_of):
            grouped[(row.instrument_id, row.topic_id)].append(row)

    resolved: list[StructuralRoleAuthorityCandidate] = []
    for identity, effective_rows in grouped.items():
        candidates = [row for row in effective_rows if row.superseded_by_authority_id is None]
        if len(candidates) != 1:
            raise StructuralRoleAuthorityReadError(
                "STRUCTURAL_ROLE_AUTHORITY_CONFLICT:"
                f"{identity[0]}:{identity[1]}:{len(candidates)}"
            )
        candidate = candidates[0]
        _validate_authority(candidate)
        resolved.append(candidate)
    return sorted(
        resolved,
        key=lambda row: (row.market_code, row.instrument_code, row.topic_slug, row.relation_id),
    )


def _candidate_from_relation(
    relation: InstrumentTopicRelation,
    instrument: Instrument,
    topic: Topic,
    market: Market,
) -> StructuralRoleAuthorityCandidate:
    return StructuralRoleAuthorityCandidate(
        relation_id=str(relation.id),
        instrument_id=str(relation.instrument_id),
        instrument_code=instrument.instrument_code,
        market_code=market.code,
        topic_id=str(relation.topic_id),
        topic_slug=topic.slug,
        relation_type=relation.relation_type,
        structural_role=relation.structural_role,
        approval_state=relation.approval_state,
        authority_version=relation.authority_version,
        effective_from=relation.valid_from,
        effective_to=relation.valid_to,
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


def current_structural_role_authority_query(as_of: date) -> Select:
    """Build the read-only active instrument/topic relation query."""

    return (
        select(InstrumentTopicRelation, Instrument, Topic, Market)
        .join(Instrument, Instrument.id == InstrumentTopicRelation.instrument_id)
        .join(Topic, Topic.id == InstrumentTopicRelation.topic_id)
        .join(Market, Market.id == Instrument.market_id)
        .where(
            Instrument.is_active.is_(True),
            Instrument.instrument_type == "EQUITY",
            (Instrument.valid_from.is_(None) | (Instrument.valid_from <= as_of)),
            (Instrument.valid_to.is_(None) | (Instrument.valid_to >= as_of)),
            Market.is_active.is_(True),
            Market.code.in_(("TPE", "TWO")),
            Topic.status.not_in(("DISABLED", "RETIRED")),
            (Topic.valid_from.is_(None) | (Topic.valid_from <= as_of)),
            (Topic.valid_to.is_(None) | (Topic.valid_to >= as_of)),
        )
        .order_by(
            Market.code,
            Instrument.instrument_code,
            Topic.slug,
            InstrumentTopicRelation.valid_from,
            InstrumentTopicRelation.id,
        )
    )


def read_current_structural_role_authority(
    session: Session, as_of: date
) -> list[StructuralRoleAuthorityReadItem]:
    rows = tuple(
        _candidate_from_relation(relation, instrument, topic, market)
        for relation, instrument, topic, market in session.execute(
            current_structural_role_authority_query(as_of)
        ).all()
    )
    resolved = resolve_current_structural_role_authority(rows, as_of)
    return [
        StructuralRoleAuthorityReadItem(
            relation_id=row.relation_id,
            instrument_id=row.instrument_id,
            instrument_code=row.instrument_code,
            market_code=row.market_code,
            topic_id=row.topic_id,
            topic_slug=row.topic_slug,
            relation_type=row.relation_type,
            structural_role=row.structural_role,
            approval_state=row.approval_state,
            authority_version=row.authority_version,
            effective_from=row.effective_from,
            effective_to=row.effective_to,
            source_artifact_id=row.source_artifact_id,
            source_artifact_hash=row.source_artifact_hash,
            approval_reference=row.approval_reference,
            correction_sequence=row.correction_sequence,
            supersedes_authority_id=row.supersedes_authority_id,
            superseded_by_authority_id=row.superseded_by_authority_id,
            lineage_hash=row.lineage_hash,
        )
        for row in resolved
    ]


__all__ = [
    "ALLOWED_RELATION_TYPES",
    "ALLOWED_STRUCTURAL_ROLES",
    "StructuralRoleAuthorityCandidate",
    "StructuralRoleAuthorityReadError",
    "StructuralRoleAuthorityReadItem",
    "StructuralRoleAuthorityReadPage",
    "current_structural_role_authority_query",
    "read_current_structural_role_authority",
    "resolve_current_structural_role_authority",
]
