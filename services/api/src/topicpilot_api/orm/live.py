"""ORM mappings for live runtime operations and tracking state."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
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


class LiveTrackingUniverse(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "live_tracking_universe"
    __table_args__ = (
        UniqueConstraint("instrument_id", name="uq_live_tracking_universe_instrument"),
        CheckConstraint(
            "update_mode IN ('INTRADAY', 'POST_CLOSE', 'UNKNOWN')",
            name="ck_live_tracking_universe_update_mode",
        ),
        CheckConstraint(
            "moving_average_state IN ('ABOVE', 'BELOW', 'UNKNOWN')",
            name="ck_live_tracking_universe_ma_state",
        ),
        Index("ix_live_tracking_universe_mode", "update_mode", "instrument_id"),
    )
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT"), nullable=False
    )
    market_code: Mapped[str] = mapped_column(String(32), nullable=False)
    instrument_code: Mapped[str] = mapped_column(String(64), nullable=False)
    moving_average_period: Mapped[int] = mapped_column(Integer, nullable=False)
    moving_average_state: Mapped[str] = mapped_column(String(16), nullable=False)
    update_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    latest_close: Mapped[Any | None] = mapped_column(Numeric(38, 18))
    moving_average: Mapped[Any | None] = mapped_column(Numeric(38, 18))
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reference_observed_at: Mapped[datetime | None] = mapped_column()
    as_of_date: Mapped[date | None] = mapped_column()
    classification_reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topicpilot.market_data_sources.id", ondelete="RESTRICT")
    )


class LiveCollectorRun(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "live_collector_runs"
    __table_args__ = (
        CheckConstraint(
            "run_type IN ('INTRADAY', 'POST_CLOSE', 'TRACKING_REFRESH')",
            name="ck_live_collector_runs_type",
        ),
        CheckConstraint(
            (
                "status IN ('RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED', "
                "'MARKET_CLOSED', 'WAITING_LIVE_VALIDATION')"
            ),
            name="ck_live_collector_runs_status",
        ),
        Index("ix_live_collector_runs_started", "started_at", "run_type"),
    )
    run_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_code: Mapped[str] = mapped_column(String(64), nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    heartbeat_at: Mapped[datetime] = mapped_column(nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column()
    requested_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    freshness_state: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    provider_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    failure_code: Mapped[str | None] = mapped_column(String(64))
    failure_message: Mapped[str | None] = mapped_column(Text)
    metadata_payload: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)


class LiveCollectorAttempt(Base, IdentityMixin, CreatedAtMixin):
    __tablename__ = "live_collector_attempts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('SUCCESS', 'FAILED', 'TIMEOUT', 'RETRYING', 'SKIPPED')",
            name="ck_live_collector_attempts_status",
        ),
        Index("ix_live_collector_attempts_run", "run_id", "started_at"),
        Index("ix_live_collector_attempts_instrument", "instrument_id", "observed_at"),
    )
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("topicpilot.live_collector_runs.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT")
    )
    instrument_code: Mapped[str] = mapped_column(String(64), nullable=False)
    market_code: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    retrieved_at: Mapped[datetime | None] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
    observed_at: Mapped[datetime | None] = mapped_column()
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    freshness_state: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    payload_hash: Mapped[str | None] = mapped_column(String(128))


__all__ = ["LiveCollectorAttempt", "LiveCollectorRun", "LiveTrackingUniverse"]
