"""V2 daily topic snapshot facts.

These rows are an append-only-as-of-date read model.  They intentionally live
in the ``topicpilot`` schema and do not replace the legacy/public snapshot
bundle.
"""

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


class TopicSnapshot(Base, IdentityMixin, UpdatedAtMixin):
    __tablename__ = "topic_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_identity", name="uq_topic_snapshots_identity"),
        CheckConstraint(
            "publication_mode IN ('FORMAL', 'RESEARCH_ONLY', 'SHADOW')",
            name="ck_topic_snapshots_publication_mode",
        ),
        CheckConstraint(
            "membership_mode IN ("
            "'PIT_FORMAL', 'CURRENT_MAPPING_RECONSTRUCTED_RESEARCH_ONLY', 'SHADOW'"
            ")",
            name="ck_topic_snapshots_membership_mode",
        ),
        CheckConstraint(
            "publication_state IN ("
            "'DRAFT', 'FINALIZED', 'PUBLISHED', 'UNPUBLISHED', 'SUPERSEDED', 'UNAVAILABLE'"
            ")",
            name="ck_topic_snapshots_publication_state",
        ),
        CheckConstraint(
            "publication_mode <> 'FORMAL' OR ("
            "membership_mode = 'PIT_FORMAL' AND "
            "mapping_effective_from >= DATE '2026-08-07' AND "
            "membership_snapshot_id IS NOT NULL AND "
            "membership_snapshot_hash IS NOT NULL AND "
            "relation_version IS NOT NULL AND snapshot_identity IS NOT NULL"
            ")",
            name="ck_topic_snapshots_formal_authority",
        ),
        Index("ix_topic_snapshots_date", "snapshot_date", "topic_slug"),
        Index("ix_topic_snapshots_topic_date", "topic_id", "snapshot_date"),
        Index(
            "ix_topic_snapshots_formal_publication",
            "publication_mode",
            "publication_state",
            "snapshot_date",
            "topic_id",
            "superseded_by_snapshot_id",
        ),
    )

    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    topic_id: Mapped[UUID] = mapped_column(
        ForeignKey("topicpilot.topics.id", ondelete="RESTRICT"), nullable=False
    )
    topic_slug: Mapped[str] = mapped_column(String(128), nullable=False)
    topic_name: Mapped[str] = mapped_column(String(160), nullable=False)
    parent_topic: Mapped[str | None] = mapped_column(String(160))
    market_grade: Mapped[str | None] = mapped_column(String(16))
    topic_score: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    topic_direction: Mapped[str] = mapped_column(String(16), nullable=False)
    stock_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    strong_stock_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weak_stock_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_change: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    observed_stock_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    data_status: Mapped[str] = mapped_column(String(32), nullable=False)
    score_status: Mapped[str] = mapped_column(String(32), nullable=False)
    calculation_version: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_payload: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)

    # Typed formal/research publication authority.  Legacy/research writers may
    # leave the formal-only fields null; the database check above prevents a
    # formal row from bypassing the PIT authority boundary.
    publication_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="RESEARCH_ONLY", server_default="RESEARCH_ONLY"
    )
    membership_mode: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="CURRENT_MAPPING_RECONSTRUCTED_RESEARCH_ONLY",
        server_default="CURRENT_MAPPING_RECONSTRUCTED_RESEARCH_ONLY",
    )
    relation_version: Mapped[str | None] = mapped_column(String(128))
    mapping_effective_from: Mapped[date | None] = mapped_column(Date)
    membership_snapshot_id: Mapped[str | None] = mapped_column(String(128))
    membership_snapshot_hash: Mapped[str | None] = mapped_column(String(128))
    session_code: Mapped[str | None] = mapped_column(String(128))
    calendar_code: Mapped[str | None] = mapped_column(String(128))
    trading_day_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN"
    )
    generated_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN"
    )
    finality_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN"
    )
    publication_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default="UNPUBLISHED", server_default="UNPUBLISHED"
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    as_of_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expected_count: Mapped[int | None] = mapped_column(Integer)
    eligible_count: Mapped[int | None] = mapped_column(Integer)
    no_trade_count: Mapped[int | None] = mapped_column(Integer)
    unknown_count: Mapped[int | None] = mapped_column(Integer)
    excluded_count: Mapped[int | None] = mapped_column(Integer)
    positive_count: Mapped[int | None] = mapped_column(Integer)
    flat_count: Mapped[int | None] = mapped_column(Integer)
    negative_count: Mapped[int | None] = mapped_column(Integer)
    freshness_state: Mapped[str | None] = mapped_column(String(32))
    unavailable_reason: Mapped[str | None] = mapped_column(Text)
    quality_flags: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    reference_registry_version: Mapped[str | None] = mapped_column(String(64))
    mapping_policy_version: Mapped[str | None] = mapped_column(String(96))
    source_run_id: Mapped[str | None] = mapped_column(String(128))
    source_artifact_id: Mapped[str | None] = mapped_column(String(128))
    source_artifact_hash: Mapped[str | None] = mapped_column(String(128))
    lineage_hash: Mapped[str | None] = mapped_column(String(128))
    snapshot_identity: Mapped[str] = mapped_column(String(256), nullable=False)
    correction_sequence: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    supersedes_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topicpilot.topic_snapshots.id", ondelete="RESTRICT")
    )
    superseded_by_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topicpilot.topic_snapshots.id", ondelete="RESTRICT")
    )
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    supersession_reason: Mapped[str | None] = mapped_column(String(128))


class TopicSnapshotMemberFact(Base, IdentityMixin):
    """Immutable selected member evidence for one Topic Daily State snapshot."""

    __tablename__ = "topic_snapshot_member_facts"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "instrument_id", name="uq_topic_snapshot_member_fact"),
        CheckConstraint(
            "fact_state IN ('OBSERVED', 'NO_TRADE', 'UNKNOWN')",
            name="ck_topic_snapshot_member_fact_state",
        ),
    )

    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("topicpilot.topic_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT"), nullable=False
    )
    membership_order: Mapped[int] = mapped_column(Integer, nullable=False)
    fact_identity: Mapped[str] = mapped_column(String(256), nullable=False)
    fact_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    fact_state: Mapped[str] = mapped_column(String(32), nullable=False)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    price_observation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topicpilot.canonical_observations.id", ondelete="RESTRICT")
    )
    volume_observation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topicpilot.canonical_observations.id", ondelete="RESTRICT")
    )
    trading_status_observation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topicpilot.canonical_observations.id", ondelete="RESTRICT")
    )
    close: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    previous_close: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    change_pct: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    observed_classification: Mapped[str | None] = mapped_column(String(16))
    strength_classification: Mapped[str | None] = mapped_column(String(32))
    classifier_version: Mapped[str | None] = mapped_column(String(96))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_fact_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    source_artifact_id: Mapped[str | None] = mapped_column(String(128))
    source_artifact_hash: Mapped[str | None] = mapped_column(String(128))


__all__ = ["TopicSnapshot", "TopicSnapshotMemberFact"]
