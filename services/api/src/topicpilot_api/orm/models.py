"""Typed skeleton registry. Columns are deliberately limited to the frozen catalogue."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, CreatedAtMixin, IdentityMixin, UpdatedAtMixin


class Market(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "markets"
    __table_args__ = (
        UniqueConstraint("code", name="uq_markets_code"),
        CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name="ck_markets_valid_range",
        ),
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    exchange_code: Mapped[str | None] = mapped_column(String(32))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    calendar_code: Mapped[str | None] = mapped_column(String(64))
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    instruments: Mapped[list[Instrument]] = relationship(back_populates="market")


class Instrument(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "instruments"
    __table_args__ = (
        UniqueConstraint("market_id", "instrument_code", name="uq_instruments_market_code"),
        CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name="ck_instruments_valid_range",
        ),
    )
    market_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.markets.id", ondelete="RESTRICT"), nullable=False
    )
    instrument_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(160))
    instrument_type: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    market: Mapped[Market] = relationship(back_populates="instruments")
    security_identities: Mapped[list[SecurityIdentity]] = relationship(back_populates="instrument")
    topic_relationships: Mapped[list[InstrumentTopicRelation]] = relationship(
        back_populates="instrument"
    )


class SecurityIdentity(Base, IdentityMixin, CreatedAtMixin):
    __tablename__ = "security_identities"
    __table_args__ = (
        UniqueConstraint(
            "market_id",
            "identifier_namespace",
            "identifier_value",
            "valid_from",
            name="uq_security_identities_effective",
        ),
        CheckConstraint(
            "valid_to IS NULL OR valid_to >= valid_from", name="ck_security_identities_valid_range"
        ),
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT"), nullable=False
    )
    market_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.markets.id", ondelete="RESTRICT"), nullable=False
    )
    identifier_namespace: Mapped[str] = mapped_column(String(64), nullable=False)
    identifier_value: Mapped[str] = mapped_column(String(128), nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(32), nullable=False, default="MAPPED")
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    instrument: Mapped[Instrument] = relationship(back_populates="security_identities")
    market: Mapped[Market] = relationship()


class Topic(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "topics"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_topics_slug"),
        CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name="ck_topics_valid_range",
        ),
    )
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PROPOSED", server_default="PROPOSED"
    )
    dictionary_version: Mapped[str | None] = mapped_column(String(64))
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    display_metadata: Mapped[dict[str, Any] | None] = mapped_column("display_metadata", JSONB)
    parent_relationships: Mapped[list[TopicHierarchy]] = relationship(
        foreign_keys="TopicHierarchy.child_topic_id", back_populates="child"
    )
    child_relationships: Mapped[list[TopicHierarchy]] = relationship(
        foreign_keys="TopicHierarchy.parent_topic_id", back_populates="parent"
    )
    instrument_relationships: Mapped[list[InstrumentTopicRelation]] = relationship(
        back_populates="topic"
    )


class InstrumentTopicRelation(Base, IdentityMixin, CreatedAtMixin):
    __tablename__ = "instrument_topic_relations"
    __table_args__ = (
        UniqueConstraint(
            "instrument_id",
            "topic_id",
            "relation_version",
            "valid_from",
            name="uq_instrument_topic_relation_effective",
        ),
        CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name="ck_instrument_topic_relation_valid_range",
        ),
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT"), nullable=False
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.topics.id", ondelete="RESTRICT"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    relation_version: Mapped[str] = mapped_column(String(64), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    relationship_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "relationship_metadata", JSONB
    )
    instrument: Mapped[Instrument] = relationship(back_populates="topic_relationships")
    topic: Mapped[Topic] = relationship(back_populates="instrument_relationships")


class MarketDataSource(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "market_data_sources"
    __table_args__ = (
        UniqueConstraint("source_code", "adapter_version", name="uq_market_data_sources_identity"),
    )
    source_code: Mapped[str] = mapped_column(String(64), nullable=False)
    source_category: Mapped[str] = mapped_column(String(32), nullable=False)
    adapter_version: Mapped[str] = mapped_column(String(64), nullable=False)
    observation_semantics: Mapped[str | None] = mapped_column(String(64))
    adjustment_policy: Mapped[str | None] = mapped_column(String(64))
    calendar_policy: Mapped[str | None] = mapped_column(String(64))
    licensing_classification: Mapped[str | None] = mapped_column(String(64))
    source_rank: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100, server_default="100"
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="REGISTERED", server_default="REGISTERED"
    )


class RawMarketObservation(Base, IdentityMixin, CreatedAtMixin):
    __tablename__ = "raw_market_observations"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "content_hash", name="uq_raw_market_observations_source_hash"
        ),
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.market_data_sources.id", ondelete="RESTRICT"), nullable=False
    )
    instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT")
    )
    upstream_observation_id: Mapped[str | None] = mapped_column(String(160))
    source_instrument_identifier: Mapped[str] = mapped_column(String(128), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    quality_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="CAPTURED", server_default="CAPTURED"
    )
    ingestion_correlation_id: Mapped[str | None] = mapped_column(String(128))
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topicpilot.raw_market_observations.id", ondelete="RESTRICT")
    )


class ObservationTimelineBatch(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "observation_timeline_batches"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "request_key", name="uq_observation_timeline_batches_request"
        ),
        CheckConstraint(
            "(requested_from IS NULL) = (requested_to IS NULL)",
            name="ck_timeline_batch_requested_window_pair",
        ),
        CheckConstraint(
            "requested_to IS NULL OR requested_to >= requested_from",
            name="ck_timeline_batch_requested_window_order",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'COMPLETED', 'PARTIAL', 'FAILED')", name="ck_timeline_batch_status"
        ),
        CheckConstraint(
            "coverage_status IN ('UNKNOWN', 'SPARSE', 'COMPLETE', 'CONFLICTED')",
            name="ck_timeline_batch_coverage",
        ),
        CheckConstraint(
            "status = 'OPEN' OR completed_at IS NOT NULL", name="ck_timeline_batch_completion"
        ),
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.market_data_sources.id", ondelete="RESTRICT"), nullable=False
    )
    requested_instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT")
    )
    requested_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    requested_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="OPEN", server_default="OPEN"
    )
    coverage_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN"
    )
    request_key: Mapped[str | None] = mapped_column(String(160))
    metadata_payload: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ObservationTimelineEntry(Base, IdentityMixin, CreatedAtMixin):
    __tablename__ = "observation_timeline_entries"
    __table_args__ = (
        UniqueConstraint("raw_observation_id", name="uq_observation_timeline_entries_raw"),
        UniqueConstraint(
            "instrument_id",
            "source_id",
            "observed_at",
            "content_hash",
            name="uq_observation_timeline_entries_business_dedup",
        ),
        CheckConstraint(
            "supersedes_id IS NULL OR supersedes_id <> id",
            name="ck_observation_timeline_entries_no_self_supersession",
        ),
        CheckConstraint(
            "entry_status IN ('ACTIVE', 'SUPERSEDED', 'QUARANTINED')",
            name="ck_observation_timeline_entries_status",
        ),
        ForeignKeyConstraint(
            ["raw_observation_id", "source_id", "instrument_id"],
            [
                "topicpilot.raw_market_observations.id",
                "topicpilot.raw_market_observations.source_id",
                "topicpilot.raw_market_observations.instrument_id",
            ],
            name="fk_timeline_entry_raw_lineage",
            ondelete="RESTRICT",
        ),
        Index("ix_timeline_entries_replay", "instrument_id", "observed_at", "ordering_key", "id"),
        Index("ix_timeline_entries_source_time", "source_id", "observed_at"),
        Index("ix_timeline_entries_batch_time", "batch_id", "observed_at"),
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT"), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.market_data_sources.id", ondelete="RESTRICT"), nullable=False
    )
    raw_observation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.raw_market_observations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.observation_timeline_batches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ordering_key: Mapped[str] = mapped_column(String(256), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topicpilot.observation_timeline_entries.id", ondelete="RESTRICT")
    )
    entry_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ACTIVE", server_default="ACTIVE"
    )


class ObservationTimelineQualityEvent(Base, IdentityMixin, CreatedAtMixin):
    __tablename__ = "observation_timeline_quality_events"
    __table_args__ = (
        CheckConstraint(
            "entry_id IS NOT NULL OR batch_id IS NOT NULL", name="ck_timeline_quality_event_owner"
        ),
        CheckConstraint(
            "severity IN ('INFO', 'WARNING', 'ERROR')", name="ck_timeline_quality_event_severity"
        ),
        Index("ix_timeline_quality_entry_time", "entry_id", "detected_at"),
        Index("ix_timeline_quality_batch_time", "batch_id", "detected_at"),
    )
    entry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topicpilot.observation_timeline_entries.id", ondelete="RESTRICT")
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topicpilot.observation_timeline_batches.id", ondelete="RESTRICT")
    )
    event_code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TopicHierarchy(Base, IdentityMixin, CreatedAtMixin):
    __tablename__ = "topic_hierarchy"
    __table_args__ = (
        UniqueConstraint(
            "parent_topic_id",
            "child_topic_id",
            "hierarchy_version",
            "valid_from",
            name="uq_topic_hierarchy_effective",
        ),
        CheckConstraint(
            "parent_topic_id <> child_topic_id", name="ck_topic_hierarchy_no_self_parent"
        ),
        CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name="ck_topic_hierarchy_valid_range",
        ),
    )
    parent_topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.topics.id", ondelete="RESTRICT"), nullable=False
    )
    child_topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.topics.id", ondelete="RESTRICT"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PARENT", server_default="PARENT"
    )
    hierarchy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    display_order: Mapped[int | None] = mapped_column(Integer)
    parent: Mapped[Topic] = relationship(
        foreign_keys=[parent_topic_id], back_populates="child_relationships"
    )
    child: Mapped[Topic] = relationship(
        foreign_keys=[child_topic_id], back_populates="parent_relationships"
    )


class CanonicalObservation(Base, IdentityMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "canonical_observations"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_canonical_observations_idempotency"),
        CheckConstraint(
            "family_code IN ('PRICE','VOLUME','QUOTE','TRADING_STATUS')",
            name="ck_canonical_observations_family",
        ),
        CheckConstraint(
            "quality_state IN ('ACCEPTED','INCOMPLETE','AMBIGUOUS','CONFLICTING',"
            "'QUARANTINED','REJECTED')",
            name="ck_canonical_observations_quality",
        ),
        CheckConstraint(
            "supersedes_id IS NULL OR supersedes_id <> id",
            name="ck_canonical_observations_no_self_supersession",
        ),
        CheckConstraint(
            "length(normalization_contract_version)>0 AND length(mapping_policy_version)>0 "
            "AND length(reference_data_version)>0 AND length(content_hash)>0 "
            "AND length(idempotency_key)>0",
            name="ck_canonical_observations_nonempty_lineage",
        ),
    )
    timeline_entry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.observation_timeline_entries.id", ondelete="RESTRICT"),
        nullable=False,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT"), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.market_data_sources.id", ondelete="RESTRICT"), nullable=False
    )
    raw_observation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.raw_market_observations.id", ondelete="RESTRICT"), nullable=False
    )
    session_code: Mapped[str] = mapped_column(String(64), nullable=False)
    timezone_name: Mapped[str] = mapped_column(String(64), nullable=False)
    calendar_code: Mapped[str] = mapped_column(String(64), nullable=False)
    family_code: Mapped[str] = mapped_column(String(32), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_field_path: Mapped[str | None] = mapped_column(String(512))
    ordering_key: Mapped[str] = mapped_column(String(256), nullable=False)
    normalization_contract_version: Mapped[str] = mapped_column(String(64), nullable=False)
    mapping_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_data_version: Mapped[str] = mapped_column(String(64), nullable=False)
    quality_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ACCEPTED", server_default="ACCEPTED"
    )
    quality_warnings: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    validation_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    disposition: Mapped[str | None] = mapped_column(String(64))
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topicpilot.canonical_observations.id", ondelete="RESTRICT")
    )
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    price = relationship(
        "CanonicalPriceObservation", back_populates="canonical_observation", uselist=False
    )
    volume = relationship(
        "CanonicalVolumeObservation", back_populates="canonical_observation", uselist=False
    )
    quote = relationship(
        "CanonicalQuoteObservation", back_populates="canonical_observation", uselist=False
    )
    trading_status = relationship(
        "CanonicalTradingStatusObservation", back_populates="canonical_observation", uselist=False
    )


def _canonical_detail(name, table, fields):
    checks = {
        "canonical_price_observations": (
            CheckConstraint("price_scale BETWEEN 0 AND 18", name="ck_canonical_price_scale"),
            CheckConstraint(
                "price_currency_code ~ '^[A-Z]{3}$'", name="ck_canonical_price_currency_code"
            ),
        ),
        "canonical_volume_observations": (
            CheckConstraint(
                "volume_scale BETWEEN 0 AND 18 OR volume_scale IS NULL",
                name="ck_canonical_volume_scale",
            ),
            CheckConstraint(
                "turnover_scale BETWEEN 0 AND 18 OR turnover_scale IS NULL",
                name="ck_canonical_turnover_scale",
            ),
            CheckConstraint(
                "volume_quantity IS NULL OR (volume_unit_code IS NOT NULL "
                "AND volume_scale IS NOT NULL)",
                name="ck_canonical_volume_quantity_pair",
            ),
            CheckConstraint(
                "turnover_amount IS NULL OR (turnover_currency_code IS NOT NULL "
                "AND turnover_scale IS NOT NULL)",
                name="ck_canonical_turnover_pair",
            ),
            CheckConstraint(
                "turnover_currency_code IS NULL OR turnover_currency_code ~ '^[A-Z]{3}$'",
                name="ck_canonical_turnover_currency_code",
            ),
        ),
        "canonical_quote_observations": (
            CheckConstraint("price_scale BETWEEN 0 AND 18", name="ck_canonical_quote_price_scale"),
            CheckConstraint(
                "quote_currency_code ~ '^[A-Z]{3}$'", name="ck_canonical_quote_currency_code"
            ),
            CheckConstraint(
                "size_scale BETWEEN 0 AND 18 OR size_scale IS NULL",
                name="ck_canonical_quote_size_scale",
            ),
            CheckConstraint(
                "(bid_size IS NULL AND ask_size IS NULL) OR (size_unit_code IS NOT NULL "
                "AND size_scale IS NOT NULL)",
                name="ck_canonical_quote_size_pair",
            ),
        ),
        "canonical_trading_status_observations": (),
    }[table]
    backref = {
        "canonical_price_observations": "price",
        "canonical_volume_observations": "volume",
        "canonical_quote_observations": "quote",
        "canonical_trading_status_observations": "trading_status",
    }[table]
    return type(
        name,
        (Base,),
        {
            "__tablename__": table,
            "__module__": __name__,
            "__table_args__": checks,
            "canonical_observation_id": mapped_column(
                ForeignKey("topicpilot.canonical_observations.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            "canonical_observation": relationship(
                "CanonicalObservation", back_populates=backref, uselist=False
            ),
            **fields,
        },
    )


CanonicalPriceObservation = _canonical_detail(
    "CanonicalPriceObservation",
    "canonical_price_observations",
    {k: mapped_column(Numeric(38, 18)) for k in ("open", "high", "low", "close", "last", "vwap")}
    | {
        "price_currency_code": mapped_column(String(3), nullable=False),
        "price_scale": mapped_column(sa.SmallInteger, nullable=False),
        "adjustment_state": mapped_column(
            String(16), nullable=False, default="UNKNOWN", server_default="UNKNOWN"
        ),
        "price_context": mapped_column(JSONB),
    },
)
CanonicalVolumeObservation = _canonical_detail(
    "CanonicalVolumeObservation",
    "canonical_volume_observations",
    {
        "volume_quantity": mapped_column(Numeric(38, 18)),
        "volume_unit_code": mapped_column(String(32)),
        "volume_scale": mapped_column(sa.SmallInteger),
        "turnover_amount": mapped_column(Numeric(38, 18)),
        "turnover_currency_code": mapped_column(String(3)),
        "turnover_scale": mapped_column(sa.SmallInteger),
        "aggregation_code": mapped_column(String(32), nullable=False),
        "volume_context": mapped_column(JSONB),
    },
)
CanonicalQuoteObservation = _canonical_detail(
    "CanonicalQuoteObservation",
    "canonical_quote_observations",
    {
        "bid_price": mapped_column(Numeric(38, 18)),
        "ask_price": mapped_column(Numeric(38, 18)),
        "quote_currency_code": mapped_column(String(3), nullable=False),
        "price_scale": mapped_column(sa.SmallInteger, nullable=False),
        "bid_size": mapped_column(Numeric(38, 18)),
        "ask_size": mapped_column(Numeric(38, 18)),
        "size_unit_code": mapped_column(String(32)),
        "size_scale": mapped_column(sa.SmallInteger),
        "adjustment_state": mapped_column(
            String(16), nullable=False, default="UNKNOWN", server_default="UNKNOWN"
        ),
        "quote_context": mapped_column(JSONB),
    },
)
CanonicalTradingStatusObservation = _canonical_detail(
    "CanonicalTradingStatusObservation",
    "canonical_trading_status_observations",
    {
        "status_code": mapped_column(String(32), nullable=False),
        "status_reason": mapped_column(String(256)),
        "session_code": mapped_column(String(32), nullable=False),
        "calendar_code": mapped_column(String(64), nullable=False),
        "status_catalogue_version": mapped_column(String(64), nullable=False),
        "status_context": mapped_column(JSONB),
    },
)


class ReferenceRegistrySet(Base, IdentityMixin, CreatedAtMixin):
    __tablename__ = "reference_registry_sets"
    __table_args__ = (
        UniqueConstraint("reference_data_version", name="uq_reference_registry_sets_version"),
    )
    reference_data_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="DRAFT", server_default="DRAFT"
    )
    description: Mapped[str | None] = mapped_column(Text)
    bundle_sha256: Mapped[str | None] = mapped_column(String(64))
    source_manifest_sha256: Mapped[str | None] = mapped_column(String(64))


class ReferenceCurrency(Base, IdentityMixin):
    __tablename__ = "reference_currencies"
    __table_args__ = (
        UniqueConstraint("registry_set_id", "code", name="uq_reference_currencies_registry_code"),
    )
    registry_set_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.reference_registry_sets.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(3), nullable=False)
    scale: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False)


class ReferenceTimezone(Base, IdentityMixin):
    __tablename__ = "reference_timezones"
    __table_args__ = (
        UniqueConstraint("registry_set_id", "name", name="uq_reference_timezones_registry_name"),
    )
    registry_set_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.reference_registry_sets.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)


class ReferenceSession(Base, IdentityMixin):
    __tablename__ = "reference_sessions"
    __table_args__ = (
        UniqueConstraint("registry_set_id", "code", name="uq_reference_sessions_registry_code"),
    )
    registry_set_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.reference_registry_sets.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    calendar_code: Mapped[str] = mapped_column(String(64), nullable=False)


class ReferenceTradingStatus(Base, IdentityMixin):
    __tablename__ = "reference_trading_statuses"
    __table_args__ = (
        UniqueConstraint(
            "registry_set_id", "code", name="uq_reference_trading_statuses_registry_code"
        ),
    )
    registry_set_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.reference_registry_sets.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)


class ReferenceAdjustment(Base, IdentityMixin):
    __tablename__ = "reference_adjustments"
    __table_args__ = (
        UniqueConstraint("registry_set_id", "code", name="uq_reference_adjustments_registry_code"),
    )
    registry_set_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.reference_registry_sets.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)


class ReferenceCalendarDate(Base, IdentityMixin):
    __tablename__ = "reference_calendar_dates"
    __table_args__ = (
        UniqueConstraint(
            "registry_set_id",
            "calendar_code",
            "calendar_date",
            name="uq_reference_calendar_dates_registry_date",
        ),
        CheckConstraint(
            "date_kind IN ('HOLIDAY', 'SUSPENDED')",
            name="ck_reference_calendar_dates_kind",
        ),
    )
    registry_set_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topicpilot.reference_registry_sets.id", ondelete="RESTRICT"), nullable=False
    )
    calendar_code: Mapped[str] = mapped_column(String(64), nullable=False)
    calendar_date: Mapped[date] = mapped_column(Date, nullable=False)
    date_kind: Mapped[str] = mapped_column(String(16), nullable=False)
