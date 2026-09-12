"""Formal, append-only Score Projection V1 read models.

The tables in this module store governed input artifacts only.  They do not
select members, calculate importance, or materialize Score/Grade output.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAtMixin, IdentityMixin


class TopicScoreProjection(Base, IdentityMixin, CreatedAtMixin):
    """One approved, effective-dated Score consumer projection artifact."""

    __tablename__ = "topic_score_projections"
    __table_args__ = (
        UniqueConstraint("projection_id", name="uq_topic_score_projections_projection_id"),
        UniqueConstraint(
            "topic_id",
            "projection_version",
            "effective_from",
            name="uq_topic_score_projections_effective",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_topic_score_projections_valid_range",
        ),
        CheckConstraint(
            "approval_state IN ('DRAFT', 'PROPOSED', 'APPROVED', 'DEPRECATED', 'REJECTED')",
            name="ck_topic_score_projections_approval_state",
        ),
        CheckConstraint(
            "correction_sequence >= 0",
            name="ck_topic_score_projections_correction_sequence",
        ),
        Index(
            "ix_topic_score_projections_effective",
            "topic_id",
            "effective_from",
            "effective_to",
            "approval_state",
            "superseded_by_projection_id",
        ),
    )

    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.topics.id", ondelete="RESTRICT"), nullable=False
    )
    projection_id: Mapped[str] = mapped_column(String(128), nullable=False)
    projection_version: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    approval_state: Mapped[str] = mapped_column(String(32), nullable=False)
    approval_reference: Mapped[str] = mapped_column(String(256), nullable=False)
    source_structural_role_authority_id: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    source_structural_role_authority_version: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    projection_lineage: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    lineage_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    correction_sequence: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    supersedes_projection_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topicpilot.topic_score_projections.id", ondelete="RESTRICT")
    )
    superseded_by_projection_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topicpilot.topic_score_projections.id", ondelete="RESTRICT")
    )
    supersession_reason: Mapped[str | None] = mapped_column(String(128))

    members: Mapped[list[TopicScoreProjectionMember]] = relationship(
        back_populates="projection",
        cascade="all, delete-orphan",
        order_by="TopicScoreProjectionMember.instrument_id",
    )


class TopicScoreProjectionMember(Base, IdentityMixin):
    """An explicitly approved CORE member in one Score projection artifact."""

    __tablename__ = "topic_score_projection_members"
    __table_args__ = (
        UniqueConstraint(
            "projection_id",
            "instrument_id",
            name="uq_topic_score_projection_members_member",
        ),
        CheckConstraint(
            "score_importance IN (0.50, 0.75, 1.00)",
            name="ck_topic_score_projection_member_importance",
        ),
    )

    projection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.topic_score_projections.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT"), nullable=False
    )
    structural_role_authority_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.instrument_topic_relations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    structural_role_authority_version: Mapped[str] = mapped_column(String(64), nullable=False)
    score_importance: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    member_lineage: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    projection: Mapped[TopicScoreProjection] = relationship(back_populates="members")


__all__ = ["TopicScoreProjection", "TopicScoreProjectionMember"]
