"""Canonical persistence for stock-level institutional-flow observations."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

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
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CreatedAtMixin, IdentityMixin, UpdatedAtMixin


class StockInstitutionalFlowDaily(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    """One immutable-source, one-instrument, one-session flow fact."""

    __tablename__ = "stock_institutional_flow_daily"
    __table_args__ = (
        UniqueConstraint(
            "instrument_id",
            "trading_date",
            "source_identity",
            name="uq_stock_institutional_flow_daily_identity",
        ),
        CheckConstraint(
            "market IN ('TPE', 'TWO')", name="ck_stock_institutional_flow_daily_market"
        ),
        CheckConstraint(
            "status IN ('OK', 'NO_DATA', 'NOT_TRADING_DAY', 'PROVIDER_UNAVAILABLE', "
            "'AUTH_ERROR', 'RATE_LIMITED', 'SCHEMA_ERROR', 'MAPPING_ERROR', 'PARTIAL', "
            "'STALE', 'UNKNOWN')",
            name="ck_stock_institutional_flow_daily_status",
        ),
        CheckConstraint(
            "freshness IN ('CURRENT', 'STALE', 'UNKNOWN')",
            name="ck_stock_institutional_flow_daily_freshness",
        ),
        CheckConstraint("unit = 'SHARES'", name="ck_stock_institutional_flow_daily_unit"),
        CheckConstraint("scale = 0", name="ck_stock_institutional_flow_daily_scale"),
        Index(
            "ix_stock_institutional_flow_daily_instrument_date",
            "instrument_id",
            "trading_date",
        ),
        Index(
            "ix_stock_institutional_flow_daily_source_as_of",
            "source_identity",
            "source_as_of",
        ),
    )

    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT"), nullable=False
    )
    market: Mapped[str] = mapped_column(String(8), nullable=False)
    instrument_code: Mapped[str] = mapped_column(String(64), nullable=False)
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)

    source_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    source_identity: Mapped[str] = mapped_column(String(128), nullable=False)
    source_dataset: Mapped[str] = mapped_column(String(256), nullable=False)
    source_endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(128), nullable=False)
    source_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    unit: Mapped[str] = mapped_column(String(16), nullable=False, default="SHARES")
    scale: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    foreign_buy: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)
    foreign_sell: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)
    foreign_net: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)
    investment_trust_buy: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)
    investment_trust_sell: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)
    investment_trust_net: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)
    dealer_buy: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)
    dealer_sell: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)
    dealer_net: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)
    total_buy: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)
    total_sell: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)
    total_net: Mapped[int] = mapped_column(Numeric(38, 0), nullable=False)

    foreign_dealer_buy: Mapped[int | None] = mapped_column(Numeric(38, 0))
    foreign_dealer_sell: Mapped[int | None] = mapped_column(Numeric(38, 0))
    foreign_dealer_net: Mapped[int | None] = mapped_column(Numeric(38, 0))
    dealer_self_buy: Mapped[int | None] = mapped_column(Numeric(38, 0))
    dealer_self_sell: Mapped[int | None] = mapped_column(Numeric(38, 0))
    dealer_self_net: Mapped[int | None] = mapped_column(Numeric(38, 0))
    dealer_hedge_buy: Mapped[int | None] = mapped_column(Numeric(38, 0))
    dealer_hedge_sell: Mapped[int | None] = mapped_column(Numeric(38, 0))
    dealer_hedge_net: Mapped[int | None] = mapped_column(Numeric(38, 0))

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OK")
    freshness: Mapped[str] = mapped_column(String(16), nullable=False, default="UNKNOWN")
    status_reason: Mapped[str | None] = mapped_column(String(256))
    lineage: Mapped[str] = mapped_column(Text, nullable=False)
    response_content_hash: Mapped[str | None] = mapped_column(String(128))
    raw_payload: Mapped[Any | None] = mapped_column(JSONB)


__all__ = ["StockInstitutionalFlowDaily"]
