"""Minimum Topic API read-model schemas.

The minimum contract deliberately keeps Topic identity and effective membership
readable when the formal daily snapshot authority is not available. Snapshot
fields are exposed only through an explicit, leaf-only envelope.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from topicpilot_api.schemas import ApiModel

AvailabilityState = Literal["AVAILABLE", "UNAVAILABLE", "NOT_APPLICABLE"]
TopicKind = Literal["PARENT", "LEAF"]


class TopicAvailabilityRead(ApiModel):
    state: AvailabilityState
    reason_code: str | None = Field(default=None, alias="reasonCode")
    reason: str | None = None
    as_of: date = Field(alias="asOf")


class TopicSourceReferenceRead(ApiModel):
    authority: str
    as_of: date = Field(alias="asOf")
    version: str | None = None


class TopicSourceRead(ApiModel):
    identity: TopicSourceReferenceRead
    hierarchy: TopicSourceReferenceRead
    members: TopicSourceReferenceRead | None = None
    snapshot: TopicSourceReferenceRead


class TopicHierarchyNodeRead(ApiModel):
    topic_id: str = Field(alias="topicId")
    slug: str
    name: str


class TopicHierarchyRead(ApiModel):
    kind: TopicKind
    parents: list[TopicHierarchyNodeRead] = Field(default_factory=list)
    children: list[TopicHierarchyNodeRead] = Field(default_factory=list)


class TopicMemberRead(ApiModel):
    instrument_id: str = Field(alias="instrumentId")
    code: str
    name: str | None
    market: str
    relation_type: str = Field(alias="relationType")
    relation_version: str = Field(alias="relationVersion")
    valid_from: date = Field(alias="validFrom")
    valid_to: date | None = Field(default=None, alias="validTo")


class TopicSnapshotSourceRead(ApiModel):
    authority: Literal["topicpilot.topic_snapshots"]
    as_of_at: datetime | None = Field(default=None, alias="asOfAt")
    source_run_id: str | None = Field(default=None, alias="sourceRunId")
    source_artifact_id: str | None = Field(default=None, alias="sourceArtifactId")
    source_artifact_hash: str | None = Field(default=None, alias="sourceArtifactHash")
    lineage_hash: str | None = Field(default=None, alias="lineageHash")
    reference_registry_version: str | None = Field(
        default=None, alias="referenceRegistryVersion"
    )
    mapping_policy_version: str | None = Field(default=None, alias="mappingPolicyVersion")


class TopicSnapshotPublicationRead(ApiModel):
    mode: Literal["FORMAL"]
    state: Literal["PUBLISHED"]
    membership_mode: Literal["PIT_FORMAL"] = Field(alias="membershipMode")
    generated_state: str | None = Field(default=None, alias="generatedState")
    finality_state: Literal["FINAL"] = Field(alias="finalityState")
    trading_day_state: str | None = Field(default=None, alias="tradingDayState")
    freshness_state: str | None = Field(default=None, alias="freshnessState")
    snapshot_identity: str = Field(alias="snapshotIdentity")
    correction_sequence: int = Field(alias="correctionSequence")
    relation_version: str = Field(alias="relationVersion")
    mapping_effective_from: date = Field(alias="mappingEffectiveFrom")
    membership_snapshot_id: str = Field(alias="membershipSnapshotId")
    membership_snapshot_hash: str = Field(alias="membershipSnapshotHash")
    generated_at: datetime | None = Field(default=None, alias="generatedAt")
    finalized_at: datetime | None = Field(default=None, alias="finalizedAt")
    published_at: datetime | None = Field(default=None, alias="publishedAt")


class TopicFormalSnapshotRead(ApiModel):
    snapshot_date: date = Field(alias="snapshotDate")
    topic_id: str = Field(alias="topicId")
    topic_slug: str = Field(alias="topicSlug")
    topic_name: str = Field(alias="topicName")
    topic_direction: str | None = Field(default=None, alias="topicDirection")
    topic_score: float | None = Field(default=None, alias="topicScore")
    market_grade: str | None = Field(default=None, alias="marketGrade")
    stock_count: int = Field(alias="stockCount")
    observed_stock_count: int = Field(alias="observedStockCount")
    coverage_pct: float | None = Field(default=None, alias="coveragePct")
    average_change: float | None = Field(default=None, alias="averageChange")
    data_status: str = Field(alias="dataStatus")
    score_status: str = Field(alias="scoreStatus")
    calculation_version: str = Field(alias="calculationVersion")
    as_of_at: datetime | None = Field(default=None, alias="asOfAt")
    source: TopicSnapshotSourceRead
    publication: TopicSnapshotPublicationRead


class TopicCurrentSnapshotRead(ApiModel):
    availability: TopicAvailabilityRead
    snapshot: TopicFormalSnapshotRead | None = None


class TopicMinimumRead(ApiModel):
    topic_id: str = Field(alias="topicId")
    slug: str
    name: str
    status: str
    enabled: bool
    kind: TopicKind
    as_of: date = Field(alias="asOf")
    availability: TopicAvailabilityRead
    hierarchy: TopicHierarchyRead
    members: list[TopicMemberRead] = Field(default_factory=list)
    members_availability: TopicAvailabilityRead = Field(alias="membersAvailability")
    source: TopicSourceRead
    current_formal_snapshot: TopicCurrentSnapshotRead = Field(alias="currentFormalSnapshot")


class TopicMinimumReadPage(ApiModel):
    items: list[TopicMinimumRead]
    total: int
    limit: int
    offset: int
    as_of: date = Field(alias="asOf")


class TopicSnapshotHistoryReadPage(ApiModel):
    items: list[TopicFormalSnapshotRead]
    total: int
    limit: int
    offset: int
    as_of: date = Field(alias="asOf")
    availability: TopicAvailabilityRead


__all__ = [
    "TopicAvailabilityRead",
    "TopicCurrentSnapshotRead",
    "TopicFormalSnapshotRead",
    "TopicHierarchyNodeRead",
    "TopicHierarchyRead",
    "TopicMemberRead",
    "TopicMinimumRead",
    "TopicMinimumReadPage",
    "TopicSnapshotHistoryReadPage",
    "TopicSnapshotPublicationRead",
    "TopicSnapshotSourceRead",
    "TopicSourceRead",
    "TopicSourceReferenceRead",
]
