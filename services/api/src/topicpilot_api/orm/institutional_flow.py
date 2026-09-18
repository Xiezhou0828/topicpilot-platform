"""FUND-A formal daily market institutional-flow persistence."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
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


class MarketInstitutionalFlowDaily(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    """One replayable official cash-value observation per market/session/source."""

    __tablename__ = "market_institutional_flow_daily"
    __table_args__ = (
        UniqueConstraint(
            "market",
            "trading_date",
            "source_identity",
            name="uq_market_institutional_flow_daily_identity",
        ),
        CheckConstraint(
            "market IN ('TPE', 'TWO')", name="ck_market_institutional_flow_daily_market"
        ),
        CheckConstraint(
            "availability IN ('AVAILABLE', 'NOT_YET_PUBLISHED', 'SOURCE_UNAVAILABLE', "
            "'INGESTION_FAILED', 'NON_TRADING_DAY')",
            name="ck_market_institutional_flow_daily_availability",
        ),
        CheckConstraint(
            "freshness IN ('CURRENT', 'STALE', 'UNKNOWN')",
            name="ck_market_institutional_flow_daily_freshness",
        ),
        CheckConstraint("unit = 'TWD'", name="ck_market_institutional_flow_daily_unit"),
        CheckConstraint("scale >= 0", name="ck_market_institutional_flow_daily_scale"),
        Index(
            "ix_market_institutional_flow_daily_lookup",
            "market",
            "trading_date",
            "source_identity",
        ),
        Index(
            "ix_market_institutional_flow_daily_source_as_of",
            "source_identity",
            "source_as_of",
        ),
    )

    market: Mapped[str] = mapped_column(String(8), nullable=False)
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    source_identity: Mapped[str] = mapped_column(String(128), nullable=False)
    source_dataset: Mapped[str] = mapped_column(String(256), nullable=False)
    source_endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(128), nullable=False)
    source_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    unit: Mapped[str] = mapped_column(String(8), nullable=False, default="TWD")
    scale: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    foreign_buy: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))
    foreign_sell: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))
    foreign_net: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))
    investment_trust_buy: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))
    investment_trust_sell: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))
    investment_trust_net: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))
    dealer_buy: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))
    dealer_sell: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))
    dealer_net: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))
    total_buy: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))
    total_sell: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))
    total_net: Mapped[Decimal | None] = mapped_column(Numeric(38, 0))

    availability: Mapped[str] = mapped_column(String(32), nullable=False)
    freshness: Mapped[str] = mapped_column(String(16), nullable=False)
    status_reason: Mapped[str | None] = mapped_column(String(128))
    lineage: Mapped[str] = mapped_column(Text, nullable=False)
    lineage_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    response_content_hash: Mapped[str | None] = mapped_column(String(128))
    raw_payload: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)


__all__ = ["MarketInstitutionalFlowDaily"]
