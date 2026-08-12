"""V2 daily topic snapshot facts.

These rows are an append-only-as-of-date read model.  They intentionally live
in the ``topicpilot`` schema and do not replace the legacy/public snapshot
bundle.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdentityMixin, UpdatedAtMixin


class TopicSnapshot(Base, IdentityMixin, UpdatedAtMixin):
    __tablename__ = "topic_snapshots"
    __table_args__ = (
        UniqueConstraint("topic_id", "snapshot_date", name="uq_topic_snapshots_topic_date"),
        Index("ix_topic_snapshots_date", "snapshot_date", "topic_slug"),
        Index("ix_topic_snapshots_topic_date", "topic_id", "snapshot_date"),
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
    strong_stock_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weak_stock_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_change: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    observed_stock_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    data_status: Mapped[str] = mapped_column(String(32), nullable=False)
    score_status: Mapped[str] = mapped_column(String(32), nullable=False)
    calculation_version: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_payload: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)


__all__ = ["TopicSnapshot"]
