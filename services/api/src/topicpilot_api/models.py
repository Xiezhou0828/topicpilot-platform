from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
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

from topicpilot_api.database import Base


def jsonb_column(default: Any) -> Mapped[dict[str, Any]]:
    return mapped_column(JSONB, nullable=False, default=default, server_default="{}")


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(160))
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    group_name: Mapped[str | None] = mapped_column(String(160))
    topic_type: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class TopicHierarchy(Base):
    __tablename__ = "topic_hierarchy"
    __table_args__ = (
        UniqueConstraint("parent_topic_id", "child_topic_id", name="uq_topic_hierarchy_edge"),
        CheckConstraint("parent_topic_id <> child_topic_id", name="ck_topic_hierarchy_not_self"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    parent_topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
    )
    child_topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
    )
    weight: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class StockTopicRelation(Base):
    __tablename__ = "stock_topic_relations"
    __table_args__ = (
        UniqueConstraint("stock_id", "topic_id", "relation_type", name="uq_stock_topic_role"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="RESTRICT"), nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    evidence_summary: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class NewsArticle(Base):
    __tablename__ = "news_articles"
    __table_args__ = (
        UniqueConstraint("article_key", name="uq_news_article_key"),
        CheckConstraint(
            "classification IN ('PUBLIC_SYNTHETIC', 'PRIVATE_FORMAL')",
            name="ck_news_article_classification",
        ),
        Index("ix_news_articles_published_at", "published_at"),
        Index("ix_news_articles_source_name_published_at", "source_name", "published_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    article_key: Mapped[str] = mapped_column(String(200), nullable=False)
    source_name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    language: Mapped[str | None] = mapped_column(String(16))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    classification: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class NewsStockRelation(Base):
    __tablename__ = "news_stock_relations"
    __table_args__ = (
        UniqueConstraint(
            "news_article_id",
            "stock_id",
            "relation_type",
            name="uq_news_stock_relation",
        ),
        Index("ix_news_stock_relations_stock_article", "stock_id", "news_article_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    news_article_id: Mapped[int] = mapped_column(
        ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False
    )
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="RESTRICT"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    evidence_summary: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class NewsTopicRelation(Base):
    __tablename__ = "news_topic_relations"
    __table_args__ = (
        UniqueConstraint(
            "news_article_id",
            "topic_id",
            "relation_type",
            name="uq_news_topic_relation",
        ),
        Index("ix_news_topic_relations_topic_article", "topic_id", "news_article_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    news_article_id: Mapped[int] = mapped_column(
        ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    evidence_summary: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract_version: Mapped[str] = mapped_column(String(64), nullable=False)
    bundle_version: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    data_date: Mapped[date] = mapped_column(Date, nullable=False)
    bundle_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_name: Mapped[str] = mapped_column(String(160), nullable=False)
    classification: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    row_counts: Mapped[dict[str, Any]] = jsonb_column(dict)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)


class SourceArtifact(Base):
    __tablename__ = "source_artifacts"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id", "artifact_name", name="uq_source_artifact_run_name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ingestion_run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    artifact_name: Mapped[str] = mapped_column(String(80), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id", "data_date", "market", name="uq_market_snapshot_run"),
        CheckConstraint(
            "total_stocks IS NULL OR total_stocks >= 0", name="ck_market_total_nonnegative"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ingestion_run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    data_date: Mapped[date] = mapped_column(Date, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    total_stocks: Mapped[int | None] = mapped_column(Integer)
    advance_count: Mapped[int | None] = mapped_column(Integer)
    decline_count: Mapped[int | None] = mapped_column(Integer)
    unchanged_count: Mapped[int | None] = mapped_column(Integer)
    unavailable_count: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class StockSnapshot(Base):
    __tablename__ = "stock_snapshots"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id", "data_date", "stock_id", name="uq_stock_snapshot_run"),
        Index("ix_stock_snapshots_stock_date", "stock_id", "data_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ingestion_run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    data_date: Mapped[date] = mapped_column(Date, nullable=False)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="RESTRICT"), nullable=False
    )
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    change_pct: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    ma5: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    ma20: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    rs20: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    technical_state: Mapped[str | None] = mapped_column(String(80))
    chip_score: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    data_freshness: Mapped[str | None] = mapped_column(String(32))
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class TopicSnapshot(Base):
    __tablename__ = "topic_snapshots"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id", "data_date", "topic_id", name="uq_topic_snapshot_run"),
        Index("ix_topic_snapshots_topic_date", "topic_id", "data_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ingestion_run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    data_date: Mapped[date] = mapped_column(Date, nullable=False)
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
    )
    score: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    grade: Mapped[str | None] = mapped_column(String(16))
    strength_state: Mapped[str | None] = mapped_column(String(48))
    advance_count: Mapped[int | None] = mapped_column(Integer)
    decline_count: Mapped[int | None] = mapped_column(Integer)
    unchanged_count: Mapped[int | None] = mapped_column(Integer)
    unavailable_count: Mapped[int | None] = mapped_column(Integer)
    coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class StrategyRun(Base):
    __tablename__ = "strategy_runs"
    __table_args__ = (
        UniqueConstraint(
            "ingestion_run_id", "strategy_key", "data_date", "model_version", name="uq_strategy_run"
        ),
        CheckConstraint(
            "strategy_key IN ('MAS','MAV','TMC','BB','PB','KD')", name="ck_strategy_key"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ingestion_run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    strategy_key: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    data_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_count: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class StrategyCandidate(Base):
    __tablename__ = "strategy_candidates"
    __table_args__ = (
        UniqueConstraint("strategy_run_id", "stock_id", name="uq_strategy_candidate_stock"),
        UniqueConstraint("strategy_run_id", "rank", name="uq_strategy_candidate_rank"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    strategy_run_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_runs.id", ondelete="CASCADE"), nullable=False
    )
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="RESTRICT"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    reason: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    selected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    trigger_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    support_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    invalidation_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class StrategyPerformance(Base):
    __tablename__ = "strategy_performance"
    __table_args__ = (
        UniqueConstraint("strategy_run_id", "horizon", name="uq_strategy_performance_horizon"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    strategy_run_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_runs.id", ondelete="CASCADE"), nullable=False
    )
    horizon: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    sample_count: Mapped[int | None] = mapped_column(Integer)
    win_rate_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    average_return_pct: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    reason: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


class DataQualityEvent(Base):
    __tablename__ = "data_quality_events"
    __table_args__ = (Index("ix_data_quality_events_date_severity", "data_date", "severity"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ingestion_run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False
    )
    data_date: Mapped[date] = mapped_column(Date, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    event_code: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(64))
    entity_key: Mapped[str | None] = mapped_column(String(160))
    metadata_json: Mapped[dict[str, Any]] = jsonb_column(dict)


# Declarative models are compatibility/public-owned. Set the schema on the
# already-declared tables as well as on the metadata default so generated ORM
# SQL cannot resolve through PostgreSQL search_path into topicpilot.
for _table in Base.metadata.tables.values():
    if _table.schema is None:
        _table.schema = "public"
