"""Formal, append-only Lifecycle V1.3 publication facts."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdentityMixin, UpdatedAtMixin


class TopicLifecycleFormalResult(Base, IdentityMixin, UpdatedAtMixin):
    """One formal Lifecycle result or fail-closed unavailable decision.

    This table is intentionally separate from ``topic_lifecycle_results``.
    Shadow/calibration rows therefore cannot be promoted by a read query or a
    retry; every formal row must be written by the V1.3 formal evaluator.
    """

    __tablename__ = "topic_lifecycle_formal_results"
    __table_args__ = (
        CheckConstraint(
            "evaluation_mode = 'FORMAL'", name="ck_topic_lifecycle_formal_mode"
        ),
        CheckConstraint(
            "publication_status IN ('UNAVAILABLE', 'PUBLISHED', 'SUPERSEDED')",
            name="ck_topic_lifecycle_formal_publication_status",
        ),
        CheckConstraint(
            "supersession_state IN ('ACTIVE', 'SUPERSEDED')",
            name="ck_topic_lifecycle_formal_supersession_state",
        ),
        Index(
            "ix_topic_lifecycle_formal_topic_date",
            "topic_id",
            "evaluation_date",
            "publication_status",
        ),
        Index(
            "ix_topic_lifecycle_formal_date",
            "evaluation_date",
            "topic_slug",
            "publication_status",
        ),
        # Corrections append a new immutable revision and point back to the
        # prior decision.  Current is derived from the absence of a successor.
        UniqueConstraint(
            "topic_id",
            "evaluation_date",
            "contract_version",
            "decision_revision",
            name="uq_topic_lifecycle_formal_identity",
        ),
        UniqueConstraint(
            "supersedes_decision_id",
            name="uq_topic_lifecycle_formal_supersedes_once",
        ),
    )
    evaluation_date: Mapped[date] = mapped_column(Date, nullable=False)
    topic_id: Mapped[UUID] = mapped_column(
        ForeignKey("topicpilot.topics.id", ondelete="RESTRICT"), nullable=False
    )
    topic_slug: Mapped[str] = mapped_column(String(128), nullable=False)
    previous_stage: Mapped[str | None] = mapped_column(String(32))
    candidate_stage: Mapped[str | None] = mapped_column(String(32))
    final_stage: Mapped[str | None] = mapped_column(String(32))
    stage_entered_at: Mapped[date | None] = mapped_column(Date)
    stage_trading_days: Mapped[int | None] = mapped_column(Integer)
    evaluation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    data_status: Mapped[str] = mapped_column(String(48), nullable=False)
    transition_decision: Mapped[str] = mapped_column(String(64), nullable=False)
    transition_reason: Mapped[str] = mapped_column(String(256), nullable=False)
    unavailable_reason: Mapped[str | None] = mapped_column(String(256))
    publication_status: Mapped[str] = mapped_column(String(32), nullable=False)
    evaluation_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default="FORMAL", server_default="FORMAL"
    )
    contract_version: Mapped[str] = mapped_column(String(96), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(96), nullable=False)
    calculation_version: Mapped[str] = mapped_column(String(96), nullable=False)
    leadership_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    diffusion_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    group_strength_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    divergence_decay_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    persistence_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    sample_confidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    confirmation_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    state_memory: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    main_rise_segment: Mapped[int | None] = mapped_column(Integer)
    segment_entry_date: Mapped[date | None] = mapped_column(Date)
    segment_anchor_date: Mapped[date | None] = mapped_column(Date)
    days_since_meaningful_expansion: Mapped[int | None] = mapped_column(Integer)
    drawdown_from_peak_pct: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    average_change: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))

    input_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topicpilot.topic_snapshots.id", ondelete="RESTRICT")
    )
    input_snapshot_identity: Mapped[str | None] = mapped_column(String(256))
    input_snapshot_hash: Mapped[str | None] = mapped_column(String(128))
    membership_snapshot_id: Mapped[str | None] = mapped_column(String(128))
    membership_snapshot_hash: Mapped[str | None] = mapped_column(String(128))
    relation_version: Mapped[str | None] = mapped_column(String(128))
    reference_registry_version: Mapped[str | None] = mapped_column(String(64))
    mapping_policy_version: Mapped[str | None] = mapped_column(String(96))
    session_code: Mapped[str | None] = mapped_column(String(128))
    calendar_code: Mapped[str | None] = mapped_column(String(128))
    source_artifact_id: Mapped[str | None] = mapped_column(String(128))
    source_artifact_hash: Mapped[str | None] = mapped_column(String(128))
    source_reference: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    lineage_hash: Mapped[str | None] = mapped_column(String(128))
    member_fact_hashes: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    correction_sequence: Mapped[int | None] = mapped_column(Integer)
    decision_revision: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    supersedes_decision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topicpilot.topic_lifecycle_formal_results.id", ondelete="RESTRICT")
    )
    supersession_reason: Mapped[str | None] = mapped_column(String(128))
    supersession_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ACTIVE", server_default="ACTIVE"
    )
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    as_of_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    diagnostic_detail: Mapped[str | None] = mapped_column(Text)

__all__ = ["TopicLifecycleFormalResult"]
