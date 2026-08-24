"""Canonical V2 Home publication and market-fact persistence."""

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

from .base import Base, CreatedAtMixin, IdentityMixin, UpdatedAtMixin


class HomePublication(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    """One immutable-input, replayable Home publication envelope."""

    __tablename__ = "home_publications"
    __table_args__ = (
        UniqueConstraint(
            "trading_date",
            "source_dataset_id",
            "publication_version",
            name="uq_home_publications_identity",
        ),
        CheckConstraint(
            "publication_state IN ('COLLECTED', 'MATERIALIZED', 'VALIDATED', "
            "'PUBLISHED', 'UNAVAILABLE', 'SUPERSEDED')",
            name="ck_home_publications_state",
        ),
        Index(
            "ix_home_publications_latest",
            "publication_state",
            "trading_date",
            "published_at",
            "id",
        ),
    )

    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    as_of_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    publication_state: Mapped[str] = mapped_column(String(32), nullable=False)
    publication_version: Mapped[str] = mapped_column(String(96), nullable=False)
    source_run_id: Mapped[str | None] = mapped_column(String(128))
    source_dataset_id: Mapped[str] = mapped_column(String(256), nullable=False)
    lineage_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    completeness: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    diagnostic_reason: Mapped[str | None] = mapped_column(Text)


class HomePublicationSection(Base, IdentityMixin, CreatedAtMixin):
    """Typed, operator-readable section status for one Home envelope."""

    __tablename__ = "home_publication_sections"
    __table_args__ = (
        UniqueConstraint(
            "publication_id",
            "section_key",
            name="uq_home_publication_sections_key",
        ),
        CheckConstraint(
            "status IN ('AVAILABLE', 'PARTIAL', 'UNAVAILABLE')",
            name="ck_home_publication_sections_status",
        ),
        Index(
            "ix_home_publication_sections_lookup",
            "publication_id",
            "section_key",
        ),
    )

    publication_id: Mapped[UUID] = mapped_column(
        ForeignKey("topicpilot.home_publications.id", ondelete="CASCADE"), nullable=False
    )
    section_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    data_date: Mapped[date | None] = mapped_column(Date)
    as_of_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str | None] = mapped_column(String(256))
    reason_code: Mapped[str | None] = mapped_column(String(96))
    user_message: Mapped[str | None] = mapped_column(Text)
    diagnostic_detail: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class HomeMarketFact(Base, IdentityMixin, CreatedAtMixin):
    """Typed market aggregate fact consumed by a Home publication."""

    __tablename__ = "home_market_facts"
    __table_args__ = (
        UniqueConstraint(
            "publication_id",
            "fact_type",
            "market",
            "index_code",
            name="uq_home_market_facts_identity",
        ),
        CheckConstraint(
            "fact_type IN ('INDEX', 'TURNOVER', 'BREADTH', 'LIMITS')",
            name="ck_home_market_facts_type",
        ),
        CheckConstraint(
            "publication_state IN ('MATERIALIZED', 'VALIDATED', 'PUBLISHED', 'UNAVAILABLE')",
            name="ck_home_market_facts_state",
        ),
        Index(
            "ix_home_market_facts_publication",
            "publication_id",
            "fact_type",
            "market",
        ),
    )

    publication_id: Mapped[UUID] = mapped_column(
        ForeignKey("topicpilot.home_publications.id", ondelete="CASCADE"), nullable=False
    )
    fact_type: Mapped[str] = mapped_column(String(16), nullable=False)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    index_code: Mapped[str | None] = mapped_column(String(64))
    index_name: Mapped[str | None] = mapped_column(String(160))
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    session: Mapped[str | None] = mapped_column(String(64))
    value: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    previous_close: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    change: Mapped[Decimal | None] = mapped_column(Numeric(38, 18))
    change_pct: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    currency: Mapped[str | None] = mapped_column(String(3))
    unit: Mapped[str | None] = mapped_column(String(32))
    scale: Mapped[int | None] = mapped_column(Integer)
    as_of_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(256), nullable=False)
    lineage: Mapped[str] = mapped_column(Text, nullable=False)
    publication_state: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(96))
    coverage: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


__all__ = ["HomeMarketFact", "HomePublication", "HomePublicationSection"]
