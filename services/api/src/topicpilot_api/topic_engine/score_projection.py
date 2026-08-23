"""Formal Score Projection V1 resolution and GovernedLeaderSet adaptation."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..orm.score_projections import TopicScoreProjection, TopicScoreProjectionMember
from .production_policy import LeaderDefinition
from .runtime_readiness import GovernedLeaderSet
from .structural_role_authority import (
    AUTHORITY_READ_CURRENT,
    AUTHORITY_READ_HISTORICAL,
    STRUCTURAL_ROLE_CORE,
    StructuralRoleAuthorityError,
    StructuralRoleResolution,
    resolve_structural_role,
)

SCORE_PROJECTION_APPROVED = "APPROVED"
SCORE_PROJECTION_READ_CURRENT = AUTHORITY_READ_CURRENT
SCORE_PROJECTION_READ_HISTORICAL = AUTHORITY_READ_HISTORICAL
ALLOWED_SCORE_IMPORTANCE = frozenset({Decimal("1.00"), Decimal("0.75"), Decimal("0.50")})


class ScoreProjectionError(ValueError):
    """Raised when an approved Score projection cannot be reconstructed."""


@dataclass(frozen=True)
class ScoreProjectionMemberRecord:
    instrument_id: str
    score_importance: Decimal
    structural_role_authority_id: str
    structural_role_authority_version: str
    member_lineage: dict[str, Any] | None

    @classmethod
    def from_model(cls, member: TopicScoreProjectionMember) -> ScoreProjectionMemberRecord:
        return cls(
            instrument_id=str(member.instrument_id),
            score_importance=Decimal(str(member.score_importance)),
            structural_role_authority_id=str(member.structural_role_authority_id),
            structural_role_authority_version=member.structural_role_authority_version,
            member_lineage=member.member_lineage,
        )


@dataclass(frozen=True)
class ScoreProjectionRecord:
    projection_row_id: str
    topic_id: str
    projection_id: str
    projection_version: str
    effective_from: date
    effective_to: date | None
    approval_state: str
    approval_reference: str
    source_structural_role_authority_id: str
    source_structural_role_authority_version: str
    selected_core_members: tuple[ScoreProjectionMemberRecord, ...]
    projection_lineage: dict[str, Any]
    lineage_hash: str
    correction_sequence: int
    supersedes_projection_id: str | None
    superseded_by_projection_id: str | None

    @classmethod
    def from_model(cls, projection: TopicScoreProjection) -> ScoreProjectionRecord:
        return cls(
            projection_row_id=str(projection.id),
            topic_id=str(projection.topic_id),
            projection_id=projection.projection_id,
            projection_version=projection.projection_version,
            effective_from=projection.effective_from,
            effective_to=projection.effective_to,
            approval_state=projection.approval_state,
            approval_reference=projection.approval_reference,
            source_structural_role_authority_id=projection.source_structural_role_authority_id,
            source_structural_role_authority_version=(
                projection.source_structural_role_authority_version
            ),
            selected_core_members=tuple(
                ScoreProjectionMemberRecord.from_model(member) for member in projection.members
            ),
            projection_lineage=dict(projection.projection_lineage),
            lineage_hash=projection.lineage_hash,
            correction_sequence=projection.correction_sequence,
            supersedes_projection_id=(
                str(projection.supersedes_projection_id)
                if projection.supersedes_projection_id is not None
                else None
            ),
            superseded_by_projection_id=(
                str(projection.superseded_by_projection_id)
                if projection.superseded_by_projection_id is not None
                else None
            ),
        )


@dataclass(frozen=True)
class ScoreProjectionResolution:
    record: ScoreProjectionRecord
    member_authorities: tuple[StructuralRoleResolution, ...]
    as_of: date
    read_mode: str

    @property
    def topic_id(self) -> str:
        return self.record.topic_id


def _required_text(value: str | None, field: str) -> str:
    if value is None or not value.strip() or value != value.strip():
        raise ScoreProjectionError(f"{field} is missing or not canonical")
    return value


def _effective(record: ScoreProjectionRecord, as_of: date) -> bool:
    return record.effective_from <= as_of and (
        record.effective_to is None or as_of <= record.effective_to
    )


def _validate_projection(record: ScoreProjectionRecord) -> None:
    _required_text(record.projection_id, "projection_id")
    _required_text(record.projection_version, "projection_version")
    if record.approval_state != SCORE_PROJECTION_APPROVED:
        raise ScoreProjectionError("SCORE_PROJECTION_NOT_APPROVED")
    _required_text(record.approval_reference, "approval_reference")
    _required_text(
        record.source_structural_role_authority_id,
        "source_structural_role_authority_id",
    )
    _required_text(
        record.source_structural_role_authority_version,
        "source_structural_role_authority_version",
    )
    _required_text(record.lineage_hash, "lineage_hash")
    if not record.projection_lineage:
        raise ScoreProjectionError("projection_lineage is missing")
    if record.correction_sequence < 0:
        raise ScoreProjectionError("correction_sequence is invalid")
    if record.superseded_by_projection_id == record.projection_row_id:
        raise ScoreProjectionError("projection cannot be superseded by itself")


def _validate_importance(value: Decimal) -> Decimal:
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ScoreProjectionError("SCORE_IMPORTANCE_INVALID") from exc
    if normalized not in ALLOWED_SCORE_IMPORTANCE:
        raise ScoreProjectionError("SCORE_IMPORTANCE_INVALID")
    return normalized


AuthorityResolver = Callable[..., StructuralRoleResolution]


def resolve_score_projection_records(
    projections: Iterable[ScoreProjectionRecord],
    topic_id: str | UUID,
    as_of: date,
    authority_resolver: AuthorityResolver,
    *,
    read_mode: str = SCORE_PROJECTION_READ_CURRENT,
) -> ScoreProjectionResolution:
    """Resolve one topic projection and validate every selected CORE member."""

    if read_mode not in {SCORE_PROJECTION_READ_CURRENT, SCORE_PROJECTION_READ_HISTORICAL}:
        raise ScoreProjectionError("read_mode must be CURRENT or HISTORICAL")
    topic_key = str(topic_id)
    matched = tuple(projection for projection in projections if projection.topic_id == topic_key)
    if not matched:
        raise ScoreProjectionError("SCORE_PROJECTION_MISSING")
    effective = tuple(projection for projection in matched if _effective(projection, as_of))
    if not effective:
        raise ScoreProjectionError("SCORE_PROJECTION_NOT_EFFECTIVE")
    for projection in effective:
        _validate_projection(projection)

    if read_mode == SCORE_PROJECTION_READ_CURRENT:
        candidates = tuple(
            projection
            for projection in effective
            if projection.superseded_by_projection_id is None
        )
        if not candidates:
            raise ScoreProjectionError("SCORE_PROJECTION_SUPERSEDED")
    else:
        candidates = effective
    if len(candidates) != 1:
        raise ScoreProjectionError("SCORE_PROJECTION_CONFLICT")

    selected = candidates[0]
    if not selected.selected_core_members:
        raise ScoreProjectionError("SCORE_PROJECTION_MEMBERS_MISSING")
    member_ids = tuple(member.instrument_id for member in selected.selected_core_members)
    if len(member_ids) != len(set(member_ids)):
        raise ScoreProjectionError("SCORE_PROJECTION_MEMBER_CONFLICT")

    member_authorities: list[StructuralRoleResolution] = []
    for member in selected.selected_core_members:
        _validate_importance(member.score_importance)
        try:
            authority = authority_resolver(
                selected.topic_id,
                member.instrument_id,
                as_of,
                read_mode=read_mode,
            )
        except StructuralRoleAuthorityError as exc:
            raise ScoreProjectionError(
                f"STRUCTURAL_ROLE_AUTHORITY_INVALID:{member.instrument_id}"
            ) from exc
        if authority.structural_role != STRUCTURAL_ROLE_CORE:
            raise ScoreProjectionError("SCORE_PROJECTION_MEMBER_NOT_CORE")
        if authority.authority_id != member.structural_role_authority_id:
            raise ScoreProjectionError("SCORE_PROJECTION_MEMBER_AUTHORITY_MISMATCH")
        if authority.record.authority_version != member.structural_role_authority_version:
            raise ScoreProjectionError("SCORE_PROJECTION_MEMBER_VERSION_MISMATCH")
        if authority.record.authority_version != selected.source_structural_role_authority_version:
            raise ScoreProjectionError("SCORE_PROJECTION_SOURCE_VERSION_MISMATCH")
        member_authorities.append(authority)

    return ScoreProjectionResolution(
        record=selected,
        member_authorities=tuple(member_authorities),
        as_of=as_of,
        read_mode=read_mode,
    )


def resolve_score_projection(
    session: Session,
    topic_id: str | UUID,
    as_of: date,
    *,
    read_mode: str = SCORE_PROJECTION_READ_CURRENT,
) -> ScoreProjectionResolution:
    """Resolve one topic's formal projection from the V2 read model."""

    rows = session.scalars(
        select(TopicScoreProjection)
        .options(selectinload(TopicScoreProjection.members))
        .where(TopicScoreProjection.topic_id == topic_id)
    ).all()

    def authority_resolver(
        resolved_topic_id: str,
        instrument_id: str,
        resolved_as_of: date,
        *,
        read_mode: str,
    ) -> StructuralRoleResolution:
        return resolve_structural_role(
            session,
            resolved_topic_id,
            instrument_id,
            resolved_as_of,
            read_mode=read_mode,
        )

    return resolve_score_projection_records(
        (ScoreProjectionRecord.from_model(row) for row in rows),
        topic_id,
        as_of,
        authority_resolver,
        read_mode=read_mode,
    )


def build_governed_leader_set(
    resolution: ScoreProjectionResolution,
) -> GovernedLeaderSet:
    """Adapt a validated projection into the existing Score input shape only."""

    record = resolution.record
    leaders = tuple(
        LeaderDefinition(member.instrument_id, float(member.score_importance))
        for member in record.selected_core_members
    )
    return GovernedLeaderSet(
        version=record.projection_version,
        lifecycle=record.approval_state,
        artifact_id=record.projection_id,
        effective_date=record.effective_from,
        topic_leaders=((record.topic_id, leaders),),
    )


build_governed_leader_set_from_projection = build_governed_leader_set


__all__ = [
    "ALLOWED_SCORE_IMPORTANCE",
    "SCORE_PROJECTION_APPROVED",
    "SCORE_PROJECTION_READ_CURRENT",
    "SCORE_PROJECTION_READ_HISTORICAL",
    "ScoreProjectionError",
    "ScoreProjectionMemberRecord",
    "ScoreProjectionRecord",
    "ScoreProjectionResolution",
    "build_governed_leader_set",
    "build_governed_leader_set_from_projection",
    "resolve_score_projection",
    "resolve_score_projection_records",
]
