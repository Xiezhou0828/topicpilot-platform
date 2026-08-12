"""Append-only V2 topic lifecycle shadow evaluation facts."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdentityMixin, UpdatedAtMixin


class TopicLifecycleResult(Base, IdentityMixin, UpdatedAtMixin):
    """One deterministic, explainable lifecycle evaluation for one topic/date.

    The table is deliberately separate from ``topic_snapshots``.  It is a
    shadow result, not a replacement for the formal topic semantic, and keeps
    the policy/evidence lineage required for replay and PM calibration.
    """

    __tablename__ = "topic_lifecycle_results"
    __table_args__ = (
        UniqueConstraint(
            "topic_id",
            "evaluation_date",
            "policy_version",
            "evaluation_mode",
            name="uq_topic_lifecycle_result_identity",
        ),
        Index("ix_topic_lifecycle_results_date", "evaluation_date", "topic_slug"),
        Index("ix_topic_lifecycle_results_topic_date", "topic_id", "evaluation_date"),
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
    data_status: Mapped[str] = mapped_column(String(32), nullable=False)
    transition_decision: Mapped[str] = mapped_column(String(64), nullable=False)
    transition_reason: Mapped[str] = mapped_column(String(256), nullable=False)
    leadership_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    diffusion_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    group_strength_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    divergence_decay_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    persistence_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    sample_confidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    confirmation_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    policy_version: Mapped[str] = mapped_column(String(96), nullable=False)
    calculation_version: Mapped[str] = mapped_column(String(96), nullable=False)
    evaluation_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default="SHADOW", server_default="SHADOW"
    )
    snapshot_date: Mapped[date | None] = mapped_column(Date)
    average_change: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))


__all__ = ["TopicLifecycleResult"]
