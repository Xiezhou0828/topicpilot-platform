"""Canonical, effective-dated Topic Relation Weight authority."""

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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CreatedAtMixin, IdentityMixin, UpdatedAtMixin

RELATION_WEIGHT_AUTHORITY_EFFECTIVE_DATE = date(2026, 9, 24)
RELATION_WEIGHT_AUTHORITY_VERSION = "relation-weight-authority-20260924.v1"


class RelationWeightAuthority(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    """One proposal or approved value for one canonical instrument-topic relation.

    The relation row is retained as the identity anchor.  The duplicated
    instrument/topic/relation-type columns make the authority row auditable and
    allow the effective-dated authority to remain independently queryable.
    """

    __tablename__ = "relation_weight_authorities"
    __table_args__ = (
        UniqueConstraint(
            "relation_id",
            "authority_version",
            "effective_from",
            "correction_sequence",
            name="uq_relation_weight_authority_revision",
        ),
        CheckConstraint(
            "relation_type IN ('PRIMARY', 'SECONDARY')",
            name="ck_relation_weight_authority_relation_type",
        ),
        CheckConstraint(
            "approval_state IN ('PROPOSED', 'APPROVED')",
            name="ck_relation_weight_authority_approval_state",
        ),
        CheckConstraint(
            "effective_from >= DATE '2026-09-24'",
            name="ck_relation_weight_authority_not_backdated",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_relation_weight_authority_valid_range",
        ),
        CheckConstraint(
            "correction_sequence >= 0",
            name="ck_relation_weight_authority_correction_sequence",
        ),
        CheckConstraint(
            "(relation_type = 'PRIMARY' AND weight >= 0.5 AND weight <= 2.0) OR "
            "(relation_type = 'SECONDARY' AND weight >= 0.3 AND weight <= 0.8)",
            name="ck_relation_weight_authority_weight_range",
        ),
        Index(
            "ix_relation_weight_authority_effective",
            "relation_id",
            "effective_from",
            "effective_to",
            "approval_state",
            "correction_sequence",
        ),
        Index(
            "ix_relation_weight_authority_identity",
            "instrument_id",
            "topic_id",
            "relation_type",
            "effective_from",
            "approval_state",
        ),
    )

    relation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.instrument_topic_relations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT"), nullable=False
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.topics.id", ondelete="RESTRICT"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    legacy_original_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    legacy_recovery_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    approval_state: Mapped[str] = mapped_column(String(16), nullable=False)
    effective_from: Mapped[date] = mapped_column(
        Date, nullable=False, default=RELATION_WEIGHT_AUTHORITY_EFFECTIVE_DATE
    )
    effective_to: Mapped[date | None] = mapped_column(Date)
    authority_version: Mapped[str] = mapped_column(
        String(64), nullable=False, default=RELATION_WEIGHT_AUTHORITY_VERSION
    )
    approval_reference: Mapped[str | None] = mapped_column(String(256))
    source_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    source_artifact_id: Mapped[str | None] = mapped_column(String(256))
    source_artifact_hash: Mapped[str | None] = mapped_column(String(128))
    source_location: Mapped[str | None] = mapped_column(String(512))
    proposal_reason: Mapped[str | None] = mapped_column(String(256))
    correction_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topicpilot.relation_weight_authorities.id", ondelete="RESTRICT"),
    )
    lineage_hash: Mapped[str] = mapped_column(String(128), nullable=False)


__all__ = [
    "RELATION_WEIGHT_AUTHORITY_EFFECTIVE_DATE",
    "RELATION_WEIGHT_AUTHORITY_VERSION",
    "RelationWeightAuthority",
]
