from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from topicpilot_api.topic_lifecycle_contract import LifecycleAvailability


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
    git_sha: str = Field(default="UNKNOWN", alias="gitSha")


class MigrationRevisionResponse(ApiModel):
    alembic_revision: str | None = Field(alias="alembicRevision")
    read_only: Literal[True] = Field(default=True, alias="readOnly")


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


class HistoricalPriceSource(ApiModel):
    source_code: str = Field(alias="sourceCode")
    adapter_version: str = Field(alias="adapterVersion")
    observation_semantics: str = Field(alias="observationSemantics")
    reference_data_version: str = Field(alias="referenceDataVersion")
    normalization_contract_version: str = Field(alias="normalizationContractVersion")
    mapping_policy_version: str = Field(alias="mappingPolicyVersion")


class HistoricalPricePoint(ApiModel):
    trading_date: date = Field(alias="tradingDate")
    observed_at: datetime = Field(alias="observedAt")
    retrieved_at: datetime | None = Field(default=None, alias="retrievedAt")
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None
    source_code: str = Field(alias="sourceCode")
    quality_state: str = Field(alias="qualityState")
    adjustment_state: str = Field(default="UNKNOWN", alias="adjustmentState")
    source: HistoricalPriceSource | None = None
    adapter_version: str | None = Field(default=None, alias="adapterVersion")
    normalization_contract_version: str | None = Field(
        default=None, alias="normalizationContractVersion"
    )
    mapping_policy_version: str | None = Field(default=None, alias="mappingPolicyVersion")
    reference_data_version: str | None = Field(default=None, alias="referenceDataVersion")
    volume_unit_code: str | None = Field(default=None, alias="volumeUnitCode")
    volume_scale: int | None = Field(default=None, alias="volumeScale")
    volume_aggregation: str | None = Field(default=None, alias="volumeAggregation")


class HistoricalLifecycle(ApiModel):
    status_code: str = Field(alias="statusCode")
    effective_from: date = Field(alias="effectiveFrom")
    effective_to: date | None = Field(default=None, alias="effectiveTo")
    evidence_id: str = Field(alias="evidenceId")


class HistoricalPriceHistoryResponse(ApiModel):
    code: str
    market: str
    as_of: datetime | None = Field(default=None, alias="asOf")
    requested_from: date = Field(alias="requestedFrom")
    requested_to: date = Field(alias="requestedTo")
    returned_from: date | None = Field(default=None, alias="returnedFrom")
    returned_to: date | None = Field(default=None, alias="returnedTo")
    latest_trading_date: date | None = Field(default=None, alias="latestTradingDate")
    latest_observed_at: datetime | None = Field(default=None, alias="latestObservedAt")
    latest_retrieved_at: datetime | None = Field(default=None, alias="latestRetrievedAt")
    status: str
    coverage_state: str = Field(default="UNKNOWN", alias="coverageState")
    freshness_state: str = Field(default="UNKNOWN", alias="freshnessState")
    availability_reason: str | None = Field(alias="availabilityReason")
    point_count: int = Field(alias="pointCount")
    has_more: bool = Field(default=False, alias="hasMore")
    lifecycle: HistoricalLifecycle | None = None
    items: list[HistoricalPricePoint]


class StockTechnicalInputProvenance(ApiModel):
    authority: Literal["V2_CANONICAL_OBSERVATION_CHAIN"]
    series_semantics: Literal["RAW_OBSERVED_DAILY_BAR"] = Field(alias="seriesSemantics")
    adjustment_state: Literal["ADJUSTED", "UNADJUSTED", "UNKNOWN", "CONFLICT"] = Field(
        alias="adjustmentState"
    )
    quality_states: list[str] = Field(alias="qualityStates")
    observation_semantics: list[str] = Field(alias="observationSemantics")
    source_codes: list[str] = Field(alias="sourceCodes")
    adapter_versions: list[str] = Field(alias="adapterVersions")
    normalization_contract_versions: list[str] = Field(alias="normalizationContractVersions")
    mapping_policy_versions: list[str] = Field(alias="mappingPolicyVersions")
    reference_data_versions: list[str] = Field(alias="referenceDataVersions")
    lineage_state: Literal["VERSIONED", "MIXED", "INCOMPLETE"] = Field(alias="lineageState")
    observation_count: int = Field(alias="observationCount")
    returned_from: date | None = Field(alias="returnedFrom")
    returned_to: date | None = Field(alias="returnedTo")
    latest_trading_date: date | None = Field(alias="latestTradingDate")
    latest_observed_at: datetime | None = Field(alias="latestObservedAt")
    latest_retrieved_at: datetime | None = Field(alias="latestRetrievedAt")


class TechnicalObservationWindow(ApiModel):
    start_session: date | None = Field(default=None, alias="startSession")
    end_session: date | None = Field(default=None, alias="endSession")
    observation_count: int = Field(alias="observationCount")


class TechnicalEvidence(ApiModel):
    instrument_identity: str = Field(alias="instrumentIdentity")
    symbol: str
    market: str
    indicator_id: str = Field(alias="indicatorId")
    indicator_family: str = Field(alias="indicatorFamily")
    indicator_version: str = Field(alias="indicatorVersion")
    value: Decimal | None
    session_date: date = Field(alias="sessionDate")
    as_of: datetime | None = Field(default=None, alias="asOf")
    required_observation_count: int = Field(alias="requiredObservationCount")
    actual_observation_count: int = Field(alias="actualObservationCount")
    required_observation_window: TechnicalObservationWindow | None = Field(
        default=None, alias="requiredObservationWindow"
    )
    actual_observation_window: TechnicalObservationWindow | None = Field(
        default=None, alias="actualObservationWindow"
    )
    algorithm_id: str = Field(alias="algorithmId")
    algorithm_version: str = Field(alias="algorithmVersion")
    parameter_set: dict[str, Any] = Field(alias="parameterSet")
    price_basis: Literal["RAW_OBSERVED", "NOT_PRICE_BASED"] = Field(alias="priceBasis")
    continuity_state: Literal[
        "CONTINUITY_PASS_BOUNDED", "CONTINUITY_FAIL", "CONTINUITY_UNKNOWN"
    ] = Field(alias="continuityState")
    continuity_evidence: dict[str, Any] = Field(alias="continuityEvidence")
    event_authority_status: Literal[
        "KNOWN_EVENT",
        "NO_KNOWN_EVENT_EVIDENCE",
        "LOOKUP_UNAVAILABLE",
        "NOT_APPLICABLE",
        "ERROR",
    ] = Field(alias="eventAuthorityStatus")
    event_lookup_state: str = Field(alias="eventLookupState")
    event_lookup_evidence: dict[str, Any] = Field(alias="eventLookupEvidence")
    known_event_handling: list[dict[str, Any]] = Field(alias="knownEventHandling")
    source_authority: str = Field(alias="sourceAuthority")
    source_lineage: dict[str, Any] = Field(alias="sourceLineage")
    publication_state: Literal[
        "FORMAL", "FORMAL_WITH_LIMITATION", "UNAVAILABLE", "DEFERRED", "UNKNOWN"
    ] = Field(alias="publicationState")
    availability_reason: str | None = Field(default=None, alias="availabilityReason")
    limitation_reasons: list[str] = Field(alias="limitationReasons", default_factory=list)


class StockTechnicalPublicationRead(ApiModel):
    code: str
    market: str
    technical_contract_version: str = Field(alias="technicalContractVersion")
    requested_from: date = Field(alias="requestedFrom")
    requested_to: date = Field(alias="requestedTo")
    as_of: datetime | None = Field(default=None, alias="asOf")
    technical_policy_version: str = Field(alias="technicalPolicyVersion")
    status: Literal["FORMAL", "DEFERRED", "UNAVAILABLE"]
    publication_state: Literal[
        "FORMAL",
        "FORMAL_WITH_LIMITATION",
        "DEFERRED",
        "UNAVAILABLE",
        "NOT_PUBLISHED",
    ] = Field(alias="publicationState")
    input_state: Literal["RAW_OBSERVED", "UNAVAILABLE"] = Field(alias="inputState")
    calculation_owner: Literal["BACKEND_ONLY"] = Field(alias="calculationOwner")
    browser_calculation_allowed: Literal["NO"] = Field(alias="browserCalculationAllowed")
    availability_reasons: list[str] = Field(alias="availabilityReasons")
    reason_codes: list[str] = Field(alias="reasonCodes")
    limitation_reasons: list[str] = Field(alias="limitationReasons")
    technical_result_status: Literal["VALID", "INELIGIBLE", "UNAVAILABLE", "ERROR"] = Field(
        alias="technicalResultStatus"
    )
    technical_eligibility: Literal["ELIGIBLE", "INELIGIBLE", "UNAVAILABLE", "ERROR"] = Field(
        alias="technicalEligibility"
    )
    event_authority_status: Literal[
        "KNOWN_EVENT",
        "NO_KNOWN_EVENT_EVIDENCE",
        "LOOKUP_UNAVAILABLE",
        "NOT_APPLICABLE",
        "ERROR",
    ] = Field(alias="eventAuthorityStatus")
    publication_status: Literal[
        "AVAILABLE",
        "AVAILABLE_WITH_LIMITATION",
        "BLOCKED",
        "UNAVAILABLE",
        "ERROR",
    ] = Field(alias="publicationStatus")
    deferred_indicator_families: list[str] = Field(alias="deferredIndicatorFamilies")
    published_indicators: list[str] = Field(alias="publishedIndicators")
    algorithm_id: str | None = Field(alias="algorithmId")
    algorithm_version: str | None = Field(alias="algorithmVersion")
    parameter_set_id: str | None = Field(alias="parameterSetId")
    adjustment_policy_id: str | None = Field(alias="adjustmentPolicyId")
    price_basis: Literal["RAW_OBSERVED"] = Field(alias="priceBasis")
    continuity_policy: str = Field(alias="continuityPolicy")
    technical_evidence: list[TechnicalEvidence] = Field(alias="technicalEvidence")
    provenance: StockTechnicalInputProvenance | None


class LiveRunSummary(ApiModel):
    id: str
    type: str
    started_at: datetime = Field(alias="startedAt")
    completed_at: datetime | None = Field(alias="completedAt")
    latency_ms: int | None = Field(alias="latencyMs")
    requested_count: int = Field(alias="requestedCount")


class LiveStatusResponse(ApiModel):
    status: str
    last_run: LiveRunSummary | None = Field(alias="lastRun")
    provider_status: str = Field(alias="providerStatus")
    freshness_state: str = Field(alias="freshnessState")
    heartbeat_at: datetime | None = Field(alias="heartbeatAt")
    success_count: int = Field(alias="successCount")
    failure_count: int = Field(alias="failureCount")
    retry_count: int = Field(alias="retryCount")
    skipped_count: int = Field(default=0, alias="skippedCount")
    universe_counts: dict[str, int] = Field(default_factory=dict, alias="universeCounts")
    failure_code: str | None = Field(default=None, alias="failureCode")
    failure_message: str | None = Field(default=None, alias="failureMessage")
    provider_health: list[dict[str, object]] = Field(default_factory=list, alias="providerHealth")


class LiveTrackingResponse(ApiModel):
    instrument_code: str = Field(alias="instrumentCode")
    market: str
    update_mode: str = Field(alias="updateMode")
    moving_average_state: str = Field(alias="movingAverageState")
    moving_average_period: int = Field(alias="movingAveragePeriod")
    latest_close: float | None = Field(alias="latestClose")
    moving_average: float | None = Field(alias="movingAverage")
    observation_count: int = Field(alias="observationCount")
    observed_at: datetime | None = Field(alias="observedAt")
    updated_at: datetime | None = Field(alias="updatedAt")
    freshness_state: str = Field(alias="freshnessState")
    reason: str


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


class TopicSnapshotResponse(ApiModel):
    snapshot_date: date = Field(alias="snapshotDate")
    topic_id: str = Field(alias="topicId")
    topic_slug: str = Field(alias="topicSlug")
    topic_name: str = Field(alias="topicName")
    parent_topic: str | None = Field(alias="parentTopic")
    market_grade: str | None = Field(alias="marketGrade")
    topic_score: float | None = Field(alias="topicScore")
    topic_direction: str = Field(alias="topicDirection")
    stock_count: int = Field(alias="stockCount")
    strong_stock_count: int | None = Field(alias="strongStockCount")
    weak_stock_count: int | None = Field(alias="weakStockCount")
    average_change: float | None = Field(alias="averageChange")
    observed_stock_count: int = Field(alias="observedStockCount")
    coverage_pct: float | None = Field(alias="coveragePct")
    data_status: str = Field(alias="dataStatus")
    score_status: str = Field(alias="scoreStatus")
    calculation_version: str = Field(alias="calculationVersion")
    publication_mode: str | None = Field(default=None, alias="publicationMode")
    membership_mode: str | None = Field(default=None, alias="membershipMode")
    relation_version: str | None = Field(default=None, alias="relationVersion")
    mapping_effective_from: date | None = Field(default=None, alias="mappingEffectiveFrom")
    membership_snapshot_id: str | None = Field(default=None, alias="membershipSnapshotId")
    membership_snapshot_hash: str | None = Field(default=None, alias="membershipSnapshotHash")
    session_code: str | None = Field(default=None, alias="sessionCode")
    calendar_code: str | None = Field(default=None, alias="calendarCode")
    trading_day_state: str | None = Field(default=None, alias="tradingDayState")
    generated_state: str | None = Field(default=None, alias="generatedState")
    finality_state: str | None = Field(default=None, alias="finalityState")
    publication_state: str | None = Field(default=None, alias="publicationState")
    generated_at: datetime | None = Field(default=None, alias="generatedAt")
    as_of_at: datetime | None = Field(default=None, alias="asOfAt")
    finalized_at: datetime | None = Field(default=None, alias="finalizedAt")
    published_at: datetime | None = Field(default=None, alias="publishedAt")
    expected_count: int | None = Field(default=None, alias="expectedCount")
    eligible_count: int | None = Field(default=None, alias="eligibleCount")
    no_trade_count: int | None = Field(default=None, alias="noTradeCount")
    unknown_count: int | None = Field(default=None, alias="unknownCount")
    excluded_count: int | None = Field(default=None, alias="excludedCount")
    positive_count: int | None = Field(default=None, alias="positiveCount")
    flat_count: int | None = Field(default=None, alias="flatCount")
    negative_count: int | None = Field(default=None, alias="negativeCount")
    freshness_state: str | None = Field(default=None, alias="freshnessState")
    unavailable_reason: str | None = Field(default=None, alias="unavailableReason")
    quality_flags: dict[str, Any] | None = Field(default=None, alias="qualityFlags")
    reference_registry_version: str | None = Field(default=None, alias="referenceRegistryVersion")
    mapping_policy_version: str | None = Field(default=None, alias="mappingPolicyVersion")
    source_run_id: str | None = Field(default=None, alias="sourceRunId")
    source_artifact_id: str | None = Field(default=None, alias="sourceArtifactId")
    source_artifact_hash: str | None = Field(default=None, alias="sourceArtifactHash")
    lineage_hash: str | None = Field(default=None, alias="lineageHash")
    snapshot_identity: str | None = Field(default=None, alias="snapshotIdentity")
    correction_sequence: int | None = Field(default=None, alias="correctionSequence")
    supersedes_snapshot_id: str | None = Field(default=None, alias="supersedesSnapshotId")
    supersession_reason: str | None = Field(default=None, alias="supersessionReason")
    updated_at: datetime = Field(alias="updatedAt")


class TopicSnapshotPage(ApiModel):
    items: list[TopicSnapshotResponse]
    total: int
    limit: int
    offset: int
    query: dict[str, Any]


class StockTopicRelationRead(ApiModel):
    topic_id: str = Field(alias="topicId")
    topic_slug: str = Field(alias="topicSlug")
    topic_name: str = Field(alias="topicName")
    topic_role: str | None = Field(alias="topicRole")
    relation_type: str = Field(alias="relationType")
    relation_weight: float | None = Field(alias="relationWeight")


class StockTechnicalEvidence(ApiModel):
    above_20_ma: bool | None = Field(alias="above20MA")
    above_60_ma: bool | None = Field(alias="above60MA")
    ma20: float | None
    ma60: float | None
    breakout_state: str | None = Field(alias="breakoutState")
    technical_state: str | None = Field(alias="technicalState")


class StockEodSource(ApiModel):
    source_code: str = Field(alias="sourceCode")
    adapter_version: str = Field(alias="adapterVersion")
    observation_semantics: str = Field(alias="observationSemantics")
    quality_state: str = Field(alias="qualityState")
    observed_at: datetime | None = Field(alias="observedAt")
    retrieved_at: datetime | None = Field(alias="retrievedAt")
    reference_data_version: str = Field(alias="referenceDataVersion")
    normalization_contract_version: str = Field(alias="normalizationContractVersion")
    mapping_policy_version: str = Field(alias="mappingPolicyVersion")
    adjustment_state: str | None = Field(default=None, alias="adjustmentState")


class StockEodRead(ApiModel):
    trading_date: date = Field(alias="tradingDate")
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    previous_close: float | None = Field(alias="previousClose")
    change: float | None
    change_pct: float | None = Field(alias="changePct")
    volume: float | None
    turnover: float | None
    adjustment_state: Literal["ADJUSTED", "UNADJUSTED", "UNKNOWN"] = Field(alias="adjustmentState")
    price_source: StockEodSource | None = Field(alias="priceSource")
    volume_source: StockEodSource | None = Field(alias="volumeSource")
    observed_at: datetime | None = Field(alias="observedAt")
    retrieved_at: datetime | None = Field(alias="retrievedAt")
    data_status: Literal[
        "AVAILABLE",
        "PARTIAL",
        "UNAVAILABLE",
        "NO_TRADE",
        "SUSPENDED",
        "ADJUSTMENT_UNKNOWN",
        "SOURCE_CONFLICT",
    ] = Field(alias="dataStatus")


class StockReadModel(ApiModel):
    instrument_id: str = Field(alias="instrumentId")
    symbol: str
    code: str
    name: str | None
    market: str
    exchange: str | None
    listing: str | None
    active: bool
    enabled: bool
    price: float | None
    change_pct: float | None = Field(alias="changePct")
    volume: float | None
    eod: StockEodRead | None
    observed_at: datetime | None = Field(alias="observedAt")
    retrieved_at: datetime | None = Field(alias="retrievedAt")
    data_freshness: str = Field(alias="dataFreshness")
    update_mode: str = Field(alias="updateMode")
    market_status: str = Field(alias="marketStatus")
    main_topic: dict[str, Any] | None = Field(alias="mainTopic")
    topic_relations: list[StockTopicRelationRead] = Field(
        alias="topicRelations", default_factory=list
    )
    tracking_mode: str = Field(alias="trackingMode")
    tracking_reason: str | None = Field(alias="trackingReason")
    ma20_state: str | None = Field(alias="ma20State")
    ma60_state: str | None = Field(alias="ma60State")
    history_coverage: dict[str, Any] = Field(alias="historyCoverage", default_factory=dict)
    favorite: dict[str, Any] | None
    opportunity: dict[str, Any] | None
    technical_evidence: StockTechnicalEvidence | None = Field(alias="technicalEvidence")
    institution_flows: dict[str, Any] | None = Field(alias="institutionFlows")
    summary: str | None


class StockReadModelPage(ApiModel):
    items: list[StockReadModel]
    total: int
    limit: int
    offset: int
    query: dict[str, Any]
    universe: dict[str, int]


class TopicStatusRead(ApiModel):
    key: str
    state: str | None
    evidence: dict[str, Any] = Field(default_factory=dict)


class TopicLifecycleSegmentRead(ApiModel):
    stage: str
    entered_at: date | None = Field(alias="enteredAt")
    exited_at: date | None = Field(alias="exitedAt")
    trading_days: int | None = Field(alias="tradingDays")
    current: bool


class TopicLifecycleRead(ApiModel):
    current_stage: str | None = Field(alias="currentStage")
    current_stage_entered_at: date | None = Field(alias="currentStageEnteredAt")
    current_stage_trading_days: int | None = Field(alias="currentStageTradingDays")
    main_rise_segment: int | None = Field(default=None, alias="mainRiseSegment")
    segment_entry_date: date | None = Field(default=None, alias="segmentEntryDate")
    segment_anchor_date: date | None = Field(default=None, alias="segmentAnchorDate")
    days_since_meaningful_expansion: int | None = Field(
        default=None, alias="daysSinceMeaningfulExpansion"
    )
    drawdown_from_peak_pct: float | None = Field(default=None, alias="drawdownFromPeakPct")
    history: list[TopicLifecycleSegmentRead] = Field(default_factory=list)
    data_status: LifecycleAvailability = Field(alias="dataStatus")
    evaluation_date: date | None = Field(default=None, alias="evaluationDate")
    previous_stage: str | None = Field(default=None, alias="previousStage")
    candidate_stage: str | None = Field(default=None, alias="candidateStage")
    transition_decision: str | None = Field(default=None, alias="transitionDecision")
    transition_reason: str | None = Field(default=None, alias="transitionReason")
    policy_version: str | None = Field(default=None, alias="policyVersion")
    evidence: dict[str, Any] = Field(default_factory=dict)
    confidence: dict[str, Any] = Field(default_factory=dict)
    lineage: dict[str, Any] = Field(default_factory=dict)


class TopicConstituentRead(ApiModel):
    instrument_id: str = Field(alias="instrumentId")
    symbol: str
    code: str
    name: str | None
    role: str | None
    relation_weight: float | None = Field(alias="relationWeight")
    price: float | None
    change_pct: float | None = Field(alias="changePct")
    observed_at: datetime | None = Field(alias="observedAt")
    update_mode: str = Field(alias="updateMode")
    freshness: str
    technical_state: str | None = Field(alias="technicalState")
    relative_topic_state: str | None = Field(alias="relativeTopicState")
    fact_state: str | None = Field(default=None, alias="factState")
    observation_date: date | None = Field(default=None, alias="observationDate")
    observed_classification: str | None = Field(default=None, alias="observedClassification")
    fact_hash: str | None = Field(default=None, alias="factHash")


class TopicReadModel(ApiModel):
    topic_id: str = Field(alias="topicId")
    slug: str
    name: str
    group_name: str | None = Field(alias="groupName")
    topic_type: str = Field(alias="topicType")
    enabled: bool
    data_date: date | None = Field(alias="dataDate")
    score: float | None
    grade: str | None
    direction: str | None
    strength_state: str | None = Field(alias="strengthState")
    readable_state: str = Field(alias="readableState")
    coverage_pct: float | None = Field(alias="coveragePct")
    constituent_count: int = Field(alias="constituentCount")
    status: list[TopicStatusRead] = Field(default_factory=list)
    lifecycle: TopicLifecycleRead
    constituents: list[TopicConstituentRead] = Field(default_factory=list)
    publication: dict[str, Any] = Field(default_factory=dict)
    quality: dict[str, Any] = Field(default_factory=dict)
    lineage: dict[str, Any] = Field(default_factory=dict)


class TopicReadModelPage(ApiModel):
    items: list[TopicReadModel]
    total: int
    limit: int
    offset: int
    query: dict[str, Any]


class TopicIntelligenceVersions(ApiModel):
    feature_set: str = Field(alias="featureSet")
    feature_runtime: str = Field(alias="featureRuntime")
    aggregation: str
    scorer_runtime: str = Field(alias="scorerRuntime")


class TopicIntelligencePolicy(ApiModel):
    policy_id: str = Field(alias="policyId")
    policy_version: str = Field(alias="policyVersion")


class TopicIntelligenceComponent(ApiModel):
    name: str
    value: float | None


class TopicIntelligenceFeatureEvidence(ApiModel):
    name: str
    version: str
    status: str
    value: Any | None
    coverage: float | None
    quality_flags: list[str] = Field(alias="qualityFlags")
    metadata: dict[str, Any]


class TopicIntelligenceQuality(ApiModel):
    ready_feature_count: int = Field(alias="readyFeatureCount")
    insufficient_feature_count: int = Field(alias="insufficientFeatureCount")
    invalid_feature_count: int = Field(alias="invalidFeatureCount")
    coverage_min: float | None = Field(alias="coverageMin")
    coverage_mean: float | None = Field(alias="coverageMean")


class TopicIntelligenceEvidence(ApiModel):
    aggregate_status: str = Field(alias="aggregateStatus")
    quality: TopicIntelligenceQuality
    quality_flags: list[str] = Field(alias="qualityFlags")
    features: list[TopicIntelligenceFeatureEvidence]


class TopicIntelligenceTopic(ApiModel):
    topic_id: str = Field(alias="topicId")
    status: str
    eligibility: str
    score: float | None
    grade: str | None
    strength: str | None
    confidence: float | None
    components: list[TopicIntelligenceComponent]
    evidence: TopicIntelligenceEvidence


class TopicIntelligenceResponse(ApiModel):
    contract_version: str = Field(alias="contractVersion")
    mode: str
    status: str
    as_of: date = Field(alias="asOf")
    versions: TopicIntelligenceVersions
    policy: TopicIntelligencePolicy
    topics: list[TopicIntelligenceTopic]


class RecommendationComponent(ApiModel):
    name: str
    value: float | None


class RecommendationTopicContext(ApiModel):
    as_of: date | None = Field(alias="asOf")
    scorer_runtime_version: str | None = Field(alias="scorerRuntimeVersion")
    feature_set_version: str | None = Field(alias="featureSetVersion")
    feature_runtime_version: str | None = Field(alias="featureRuntimeVersion")
    aggregation_version: str | None = Field(alias="aggregationVersion")
    policy_id: str | None = Field(alias="policyId")
    policy_version: str | None = Field(alias="policyVersion")
    eligibility: str | None
    score: float | None
    grade: str | None
    confidence: float | None
    components: list[RecommendationComponent] = Field(default_factory=list)
    evidence_reference: list[str] = Field(alias="evidenceReference", default_factory=list)


class RecommendationItemResponse(ApiModel):
    candidate_id: str = Field(alias="candidateId")
    topic_id: str = Field(alias="topicId")
    label: str
    status: str
    reason: str
    topic_context: RecommendationTopicContext | None = Field(alias="topicContext")
    evidence: list[str] = Field(default_factory=list)


class RecommendationResponse(ApiModel):
    contract_version: str = Field(alias="contractVersion")
    as_of: date | None = Field(alias="asOf")
    status: str
    items: list[RecommendationItemResponse] = Field(default_factory=list)


class OpportunityShadowTopic(ApiModel):
    id: str
    name: str
    grade: str | None
    lifecycle: str | None
    strength: float | None


class OpportunityShadowInstrument(ApiModel):
    id: str
    symbol: str
    name: str


class OpportunityShadowQualification(ApiModel):
    qualification_class: str = Field(alias="class")
    qualification_status: str = Field(alias="status")
    reason_codes: list[str] = Field(alias="reasonCodes", default_factory=list)
    exception_candidate: bool = Field(alias="exceptionCandidate")
    policy_version: str | None = Field(alias="policyVersion")
    parameter_version: str | None = Field(alias="parameterVersion")


class OpportunityShadowCard(ApiModel):
    opportunity_id: str = Field(alias="opportunityId")
    opportunity_key: str = Field(alias="opportunityKey")
    strategy_id: str = Field(alias="strategyId")
    strategy_type: str = Field(alias="strategyType")
    strategy_label_key: str = Field(alias="strategyLabelKey")
    display_key: str = Field(alias="displayKey")
    label_key: str = Field(alias="labelKey")
    display_order: int = Field(alias="displayOrder")
    rank: int
    rank_score: float | None = Field(alias="rankScore")
    ranking_status: str = Field(alias="rankingStatus")
    instrument: OpportunityShadowInstrument
    topic: OpportunityShadowTopic
    instrument_id: str = Field(alias="instrumentId")
    symbol: str
    name: str
    topic_id: str = Field(alias="topicId")
    topic_name: str = Field(alias="topicName")
    topic_grade: str | None = Field(alias="topicGrade")
    topic_lifecycle: str | None = Field(alias="topicLifecycle")
    topic_strength: float | None = Field(alias="topicStrength")
    opportunity_state: str = Field(alias="opportunityState")
    eligibility: str
    status: str
    qualification: OpportunityShadowQualification
    qualification_class: str = Field(alias="qualificationClass")
    qualification_status: str = Field(alias="qualificationStatus")
    qualification_provenance: dict[str, Any] = Field(alias="qualificationProvenance")
    confidence: str | None
    confidence_basis: list[str] = Field(alias="confidenceBasis", default_factory=list)
    entry_context: list[dict[str, Any]] = Field(alias="entryContext", default_factory=list)
    support_context: list[dict[str, Any]] = Field(alias="supportContext", default_factory=list)
    risk_context: list[dict[str, Any]] = Field(alias="riskContext", default_factory=list)
    positive_factors: list[dict[str, Any]] = Field(alias="positiveFactors", default_factory=list)
    waiting_factors: list[dict[str, Any]] = Field(alias="waitingFactors", default_factory=list)
    risk_factors: list[dict[str, Any]] = Field(alias="riskFactors", default_factory=list)
    exclusion_factors: list[dict[str, Any]] = Field(alias="exclusionFactors", default_factory=list)
    exclusion_codes: list[str] = Field(alias="exclusionCodes", default_factory=list)
    reason_codes: list[str] = Field(alias="reasonCodes", default_factory=list)
    explanation: dict[str, Any] = Field(default_factory=dict)
    evidence_coverage: dict[str, Any] = Field(alias="evidenceCoverage", default_factory=dict)
    missing_evidence: list[str] = Field(alias="missingEvidence", default_factory=list)
    policy_version: str = Field(alias="policyVersion")
    parameter_version: str = Field(alias="parameterVersion")
    ranking_profile_version: str | None = Field(alias="rankingProfileVersion")
    as_of: date | None = Field(alias="asOf")
    publication_status: str = Field(alias="publicationStatus")
    data_status: str = Field(alias="dataStatus")
    source_data_status: str | None = Field(alias="sourceDataStatus", default=None)
    detail: dict[str, Any] | None = None


class OpportunityShadowStrategySection(ApiModel):
    strategy_id: str = Field(alias="strategyId")
    strategy_type: str = Field(alias="strategyType")
    strategy_label_key: str = Field(alias="strategyLabelKey")
    fit: str
    candidate_count: int = Field(alias="candidateCount")
    backend_candidate_count: int = Field(alias="backendCandidateCount")
    presented_count: int = Field(alias="presentedCount")
    presentation_cap: int | None = Field(alias="presentationCap")
    full_ranking_retained: bool = Field(alias="fullRankingRetained")
    backend_ranking: list[dict[str, Any]] = Field(alias="backendRanking", default_factory=list)
    opportunities: list[OpportunityShadowCard] = Field(default_factory=list)


class OpportunityShadowResponse(ApiModel):
    """Typed, shadow-only Opportunity read contract."""

    contract_version: str = Field(alias="contractVersion")
    status: str
    publication_status: str = Field(alias="publicationStatus")
    data_status: str = Field(alias="dataStatus")
    as_of: date | None = Field(alias="asOf")
    query: dict[str, Any] = Field(default_factory=dict)
    topic: OpportunityShadowTopic | None = None
    topic_id: str | None = Field(alias="topicId", default=None)
    topic_name: str | None = Field(alias="topicName", default=None)
    topic_grade: str | None = Field(alias="topicGrade", default=None)
    topic_lifecycle: str | None = Field(alias="topicLifecycle", default=None)
    topic_strength: float | None = Field(alias="topicStrength", default=None)
    stock: OpportunityShadowInstrument | None = None
    topics: list[dict[str, Any]] = Field(default_factory=list)
    strategies: dict[str, OpportunityShadowStrategySection] = Field(default_factory=dict)
    opportunities: list[OpportunityShadowCard] = Field(default_factory=list)
    opportunity: OpportunityShadowCard | None = None


class HomeSectionStatus(ApiModel):
    status: Literal["AVAILABLE", "PARTIAL", "UNAVAILABLE"]
    data_date: date | None = Field(alias="dataDate")
    as_of: datetime | None = Field(alias="asOf")
    source: str | None = None
    reason_code: str | None = Field(alias="reasonCode", default=None)
    user_message: str | None = Field(alias="userMessage", default=None)


class HomePublicationLineage(ApiModel):
    canonical_daily_market: str | None = Field(alias="canonicalDailyMarket", default=None)
    formal_topics: str | None = Field(alias="formalTopics", default=None)


class HomePublication(ApiModel):
    trading_date: date | None = Field(alias="tradingDate")
    as_of: datetime | None = Field(alias="asOf")
    generated_at: datetime | None = Field(alias="generatedAt")
    published_at: datetime | None = Field(alias="publishedAt")
    state: Literal[
        "COLLECTED",
        "MATERIALIZED",
        "VALIDATED",
        "PUBLISHED",
        "UNAVAILABLE",
        "SUPERSEDED",
    ]
    version: str
    source_run_id: str | None = Field(alias="sourceRunId", default=None)
    source_dataset_id: str | None = Field(alias="sourceDatasetId", default=None)
    lineage: HomePublicationLineage = Field(default_factory=HomePublicationLineage)
    completeness: dict[str, Any] = Field(default_factory=dict)


class HomeMarketIndex(ApiModel):
    market: str
    index_code: str = Field(alias="indexCode")
    index_name: str = Field(alias="indexName")
    trading_date: date | None = Field(alias="tradingDate")
    session: str | None = None
    value: float | None
    previous_close: float | None = Field(alias="previousClose")
    change: float | None
    change_pct: float | None = Field(alias="changePct")
    as_of: datetime | None = Field(alias="asOf")
    source: str | None = None
    lineage: str | None = None
    status: str
    reason_code: str | None = Field(alias="reasonCode", default=None)


class HomeMarketTurnover(ApiModel):
    market: str
    trading_date: date | None = Field(alias="tradingDate")
    session: str | None = None
    value: float | None
    currency: str | None
    unit: str | None
    scale: int | None
    as_of: datetime | None = Field(alias="asOf")
    source: str | None = None
    lineage: str | None = None
    status: str
    reason_code: str | None = Field(alias="reasonCode", default=None)


class HomeMarketBreadth(ApiModel):
    market: str
    eligible: int
    observed: int
    advance: int | None
    decline: int | None
    flat: int | None
    unavailable: int
    coverage: dict[str, Any] = Field(default_factory=dict)
    as_of: datetime | None = Field(alias="asOf")
    source: str


class HomeMarketLimits(ApiModel):
    limit_up: int | None = Field(alias="limitUp")
    limit_down: int | None = Field(alias="limitDown")
    reason_code: str | None = Field(alias="reasonCode", default=None)
    source: str | None = None


class HomeMarketHealth(ApiModel):
    market: str
    status: str
    total_stocks: int | None = Field(alias="totalStocks")
    advance: int | None
    decline: int | None
    flat: int | None
    unavailable: int | None


class HomeMarketOverview(ApiModel):
    data_date: date | None = Field(alias="dataDate")
    updated_at: datetime | None = Field(alias="updatedAt")
    data_status: Literal["AVAILABLE", "PARTIAL", "UNAVAILABLE"] = Field(alias="dataStatus")
    tracked_stock_count: int = Field(alias="trackedStockCount")
    tracked_topic_count: int = Field(alias="trackedTopicCount")
    latest_snapshot_time: datetime | None = Field(alias="latestSnapshotTime")
    market_health: HomeMarketHealth | None = Field(alias="marketHealth")
    breadth: list[HomeMarketBreadth] = Field(default_factory=list)
    indices: list[HomeMarketIndex] = Field(default_factory=list)
    turnover: list[HomeMarketTurnover] = Field(default_factory=list)
    limits: HomeMarketLimits | None = None
    source: str


class HomeDailyFocus(ApiModel):
    mode: str
    temporary: bool
    headline: str
    bullets: list[str] = Field(default_factory=list)
    data_date: date | None = Field(alias="dataDate")
    source: str
    reason_code: str | None = Field(alias="reasonCode", default=None)
    user_message: str | None = Field(alias="userMessage", default=None)


class HomeTopicCard(ApiModel):
    slug: str
    name: str
    grade: str | None
    strength: float | None
    current_state: str | None = Field(alias="currentState")
    stock_count: int = Field(alias="stockCount")
    summary: str
    favorite: bool
    data_date: date | None = Field(alias="dataDate")
    ranking_evidence: dict[str, Any] = Field(alias="rankingEvidence", default_factory=dict)


class HomeMarketPulseEvent(ApiModel):
    event_time: datetime = Field(alias="eventTime")
    topic: str
    event_type: str = Field(alias="eventType")
    description: str
    severity: str
    topic_slug: str = Field(alias="topicSlug")
    source: str


class HomeRotationTopic(ApiModel):
    topic: str
    topic_slug: str = Field(alias="topicSlug")
    strength_delta: float = Field(alias="strengthDelta")
    current_grade: str | None = Field(alias="currentGrade")
    summary: str
    data_date: date | None = Field(alias="dataDate", default=None)
    as_of: datetime | None = Field(alias="asOf", default=None)
    rotation_evidence: dict[str, Any] = Field(alias="rotationEvidence", default_factory=dict)


class HomeOpportunityStock(ApiModel):
    code: str
    name: str
    strategy_keys: list[str] = Field(alias="strategyKeys", default_factory=list)
    score: float | None
    reason: str | None
    data_date: date | None = Field(alias="dataDate")


class HomeOpportunityTopic(ApiModel):
    topic: str
    topic_slug: str = Field(alias="topicSlug")
    grade: str | None
    strength: float | None
    current_state: str | None = Field(alias="currentState")
    summary: str
    validated_stocks: list[HomeOpportunityStock] = Field(
        alias="validatedStocks", default_factory=list
    )
    temporary: bool


class HomeDataQuality(ApiModel):
    status: str
    source: str
    classification: str | None
    temporary_sections: list[str] = Field(alias="temporarySections", default_factory=list)
    missing_sections: list[str] = Field(alias="missingSections", default_factory=list)
    notes: list[str] = Field(default_factory=list)
    diagnostic_codes: dict[str, str] = Field(alias="diagnosticCodes", default_factory=dict)


class HomeResponse(ApiModel):
    contract_version: str = Field(alias="contractVersion")
    as_of: date | None = Field(alias="asOf")
    generated_at: datetime | None = Field(alias="generatedAt")
    market_overview: HomeMarketOverview = Field(alias="marketOverview")
    daily_focus: HomeDailyFocus = Field(alias="dailyFocus")
    main_topics: list[HomeTopicCard] = Field(alias="mainTopics", default_factory=list)
    market_pulse: list[HomeMarketPulseEvent] = Field(alias="marketPulse", default_factory=list)
    heating_topics: list[HomeRotationTopic] = Field(alias="heatingTopics", default_factory=list)
    cooling_topics: list[HomeRotationTopic] = Field(alias="coolingTopics", default_factory=list)
    opportunities: list[HomeOpportunityTopic] = Field(default_factory=list)
    data_quality: HomeDataQuality = Field(alias="dataQuality")
    publication: HomePublication | None = None
    section_statuses: dict[str, HomeSectionStatus] = Field(
        alias="sectionStatuses", default_factory=dict
    )
