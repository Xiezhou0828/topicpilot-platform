from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class ProblemDetails(ApiModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str | None = None
    errors: list[dict[str, Any]] | None = None


class HealthResponse(ApiModel):
    status: str


class DataStatus(ApiModel):
    contract_version: str = Field(alias="contractVersion")
    bundle_version: str = Field(alias="bundleVersion")
    bundle_hash: str = Field(alias="bundleHash")
    data_date: date = Field(alias="dataDate")
    generated_at: datetime = Field(alias="generatedAt")
    completed_at: datetime = Field(alias="completedAt")
    source_kind: str = Field(alias="sourceKind")
    source_name: str = Field(alias="sourceName")
    classification: str
    freshness: str
    age_days: int = Field(alias="ageDays")
    row_counts: dict[str, int] = Field(alias="rowCounts")


class TopicReference(ApiModel):
    slug: str
    name: str
    relation_type: str = Field(alias="relationType")
    weight: float | None


class StockResponse(ApiModel):
    code: str
    name: str
    market: str
    industry: str | None
    active: bool
    data_date: date | None = Field(alias="dataDate")
    price: float | None
    change_pct: float | None = Field(alias="changePct")
    volume: int | None
    ma5: float | None
    ma20: float | None
    rs20: float | None
    technical_state: str | None = Field(alias="technicalState")
    chip_score: float | None = Field(alias="chipScore")
    data_freshness: str | None = Field(alias="dataFreshness")
    topics: list[TopicReference] = []


class StockSummary(ApiModel):
    code: str
    name: str
    market: str
    industry: str | None
    active: bool
    data_date: date | None = Field(alias="dataDate")
    price: float | None
    change_pct: float | None = Field(alias="changePct")
    volume: int | None
    technical_state: str | None = Field(alias="technicalState")
    data_freshness: str | None = Field(alias="dataFreshness")


class Constituent(ApiModel):
    code: str
    name: str
    relation_type: str = Field(alias="relationType")
    weight: float | None


class TopicResponse(ApiModel):
    slug: str
    name: str
    group_name: str | None = Field(alias="groupName")
    topic_type: str = Field(alias="topicType")
    enabled: bool
    data_date: date | None = Field(alias="dataDate")
    score: float | None
    grade: str | None
    strength_state: str | None = Field(alias="strengthState")
    coverage_pct: float | None = Field(alias="coveragePct")
    constituent_count: int = Field(alias="constituentCount")
    constituents: list[Constituent] = []


class TopicSummary(ApiModel):
    slug: str
    name: str
    group_name: str | None = Field(alias="groupName")
    topic_type: str = Field(alias="topicType")
    enabled: bool
    data_date: date | None = Field(alias="dataDate")
    score: float | None
    grade: str | None
    strength_state: str | None = Field(alias="strengthState")
    coverage_pct: float | None = Field(alias="coveragePct")
    constituent_count: int = Field(alias="constituentCount")


class StrategyResponse(ApiModel):
    strategy_key: str = Field(alias="strategyKey")
    name: str
    model_version: str = Field(alias="modelVersion")
    data_date: date = Field(alias="dataDate")
    status: str
    candidate_count: int = Field(alias="candidateCount")
    selected_count: int = Field(alias="selectedCount")


class CandidateResponse(ApiModel):
    strategy_key: str = Field(alias="strategyKey")
    model_version: str = Field(alias="modelVersion")
    data_date: date = Field(alias="dataDate")
    rank: int
    code: str
    name: str
    score: float | None
    reason: str | None
    price: float | None
    selected: bool
    trigger_price: float | None = Field(alias="triggerPrice")
    support_price: float | None = Field(alias="supportPrice")
    invalidation_price: float | None = Field(alias="invalidationPrice")


class TopicRotationResponse(ApiModel):
    topic_slug: str = Field(alias="topicSlug")
    topic_name: str = Field(alias="topicName")
    group_name: str | None = Field(alias="groupName")
    latest_date: date = Field(alias="latestDate")
    latest_score: float | None = Field(alias="latestScore")
    latest_grade: str | None = Field(alias="latestGrade")
    latest_strength_state: str | None = Field(alias="latestStrengthState")
    latest_coverage_pct: float | None = Field(alias="latestCoveragePct")
    change: float | None
    point_count: int = Field(alias="pointCount")
    days: int


class StrategyPerformanceResponse(ApiModel):
    strategy_key: str = Field(alias="strategyKey")
    strategy_name: str = Field(alias="strategyName")
    model_version: str = Field(alias="modelVersion")
    data_date: date = Field(alias="dataDate")
    run_status: str = Field(alias="runStatus")
    candidate_count: int = Field(alias="candidateCount")
    selected_count: int = Field(alias="selectedCount")
    horizon: str
    status: str
    sample_count: int | None = Field(alias="sampleCount")
    win_rate_pct: float | None = Field(alias="winRatePct")
    average_return_pct: float | None = Field(alias="averageReturnPct")
    reason: str | None


class Page[T](ApiModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class SnapshotResponse(ApiModel):
    model_config = ConfigDict(extra="allow")

    snapshot_version: str = Field(alias="snapshotVersion")
    classification: str
    generated_at: datetime = Field(alias="generatedAt")
    data_date: date = Field(alias="dataDate")
