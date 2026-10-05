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


class LiveCollectorCheckpoint(Base, IdentityMixin, CreatedAtMixin):
    """Immutable checkpoint events for restart-safe live runs.

    Migration 0040 deliberately models checkpoints as an append-only event
    stream.  The latest event for a ``run_id``/``batch_key`` is the durable
    phase state; a new event is written for every retry or state transition.
    """

    __tablename__ = "live_collector_checkpoints"
    __table_args__ = (
        CheckConstraint(
            "status IN ('IN_PROGRESS', 'COMPLETED', 'PARTIAL', 'FAILED')",
            name="ck_live_collector_checkpoints_status",
        ),
        UniqueConstraint(
            "run_id",
            "batch_key",
            "attempt_number",
            name="uq_live_collector_checkpoints_event",
        ),
        Index("ix_live_collector_checkpoints_run_batch", "run_id", "batch_number"),
    )
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("topicpilot.live_collector_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_number: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_key: Mapped[str] = mapped_column(String(128), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    succeeded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_request_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    provider_failure_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    checkpoint_hash: Mapped[str] = mapped_column(String(128), nullable=False)
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


class DailyFormalPublicationReceipt(Base, IdentityMixin, CreatedAtMixin):
    """Append-only semantic receipt for one daily formal publication state.

    A new row is written for every durable state observation.  The execution
    key and receipt hash make the same observation idempotent without allowing
    a later correction to overwrite the original authority.
    """

    __tablename__ = "daily_formal_publication_receipts"
    __table_args__ = (
        CheckConstraint(
            "receipt_status IN ("
            "'COMPLETE', 'MARKET_CLOSED', 'WAITING_FOR_DATA', 'FAILED_CLOSED', "
            "'DEADLINE_EXCEEDED', 'CORRECTION_COMPLETE', 'CORRECTION_FAILED'"
            ")",
            name="ck_daily_formal_publication_receipts_status",
        ),
        CheckConstraint(
            "execution_generation >= 1 AND receipt_revision >= 1",
            name="ck_daily_formal_publication_receipts_sequence",
        ),
        UniqueConstraint(
            "execution_key",
            "receipt_hash",
            name="uq_daily_formal_publication_receipts_observation",
        ),
        Index(
            "ix_daily_formal_publication_receipts_date_revision",
            "trading_date",
            "receipt_revision",
            "created_at",
        ),
        Index(
            "ix_daily_formal_publication_receipts_run",
            "source_run_id",
            "created_at",
        ),
    )

    trading_date: Mapped[date] = mapped_column(nullable=False)
    calendar_code: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_data_version: Mapped[str] = mapped_column(String(128), nullable=False)
    calendar_decision: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    execution_key: Mapped[str] = mapped_column(String(320), nullable=False)
    execution_scope: Mapped[str] = mapped_column(String(64), nullable=False)
    execution_generation: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    receipt_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topicpilot.live_collector_runs.id", ondelete="RESTRICT")
    )
    source_run_status: Mapped[str | None] = mapped_column(String(32))
    started_at: Mapped[datetime | None] = mapped_column()
    readiness_at: Mapped[datetime | None] = mapped_column()
    publication_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    post_close_state: Mapped[str] = mapped_column(String(64), nullable=False)
    reconciliation_state: Mapped[str] = mapped_column(String(64), nullable=False)
    absolute_strength_state: Mapped[str] = mapped_column(String(64), nullable=False)
    relative_strength_state: Mapped[str] = mapped_column(String(64), nullable=False)
    formal_grade_state: Mapped[str] = mapped_column(String(64), nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(String(64), nullable=False)
    home_state: Mapped[str] = mapped_column(String(64), nullable=False)
    formal_readback_state: Mapped[str] = mapped_column(String(64), nullable=False)
    receipt_status: Mapped[str] = mapped_column(String(32), nullable=False)
    failure_stage: Mapped[str | None] = mapped_column(String(128))
    reason_code: Mapped[str | None] = mapped_column(String(128))
    receipt_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    runtime_provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    formal_identifiers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    correction_lineage: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    supersedes_receipt_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "topicpilot.daily_formal_publication_receipts.id",
            ondelete="RESTRICT",
        )
    )
    operational_events: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


__all__ = [
    "DailyFormalPublicationReceipt",
    "LiveCollectorAttempt",
    "LiveCollectorCheckpoint",
    "LiveCollectorRun",
    "LiveTrackingUniverse",
]
