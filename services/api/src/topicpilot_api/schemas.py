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


class HistoricalPricePoint(ApiModel):
    trading_date: date = Field(alias="tradingDate")
    observed_at: datetime = Field(alias="observedAt")
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None
    source_code: str = Field(alias="sourceCode")
    quality_state: str = Field(alias="qualityState")


class HistoricalPriceHistoryResponse(ApiModel):
    code: str
    market: str
    requested_from: date = Field(alias="requestedFrom")
    requested_to: date = Field(alias="requestedTo")
    status: str
    availability_reason: str | None = Field(alias="availabilityReason")
    point_count: int = Field(alias="pointCount")
    items: list[HistoricalPricePoint]


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
    strong_stock_count: int = Field(alias="strongStockCount")
    weak_stock_count: int = Field(alias="weakStockCount")
    average_change: float | None = Field(alias="averageChange")
    observed_stock_count: int = Field(alias="observedStockCount")
    coverage_pct: float | None = Field(alias="coveragePct")
    data_status: str = Field(alias="dataStatus")
    score_status: str = Field(alias="scoreStatus")
    calculation_version: str = Field(alias="calculationVersion")
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
    history: list[TopicLifecycleSegmentRead] = Field(default_factory=list)
    data_status: str = Field(alias="dataStatus")
    evaluation_date: date | None = Field(default=None, alias="evaluationDate")
    previous_stage: str | None = Field(default=None, alias="previousStage")
    candidate_stage: str | None = Field(default=None, alias="candidateStage")
    transition_decision: str | None = Field(default=None, alias="transitionDecision")
    transition_reason: str | None = Field(default=None, alias="transitionReason")
    policy_version: str | None = Field(default=None, alias="policyVersion")
    evidence: dict[str, Any] = Field(default_factory=dict)
    confidence: dict[str, Any] = Field(default_factory=dict)


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
    data_status: str = Field(alias="dataStatus")
    tracked_stock_count: int = Field(alias="trackedStockCount")
    tracked_topic_count: int = Field(alias="trackedTopicCount")
    latest_snapshot_time: datetime | None = Field(alias="latestSnapshotTime")
    market_health: HomeMarketHealth | None = Field(alias="marketHealth")
    source: str


class HomeDailyFocus(ApiModel):
    mode: str
    temporary: bool
    headline: str
    bullets: list[str] = Field(default_factory=list)
    data_date: date | None = Field(alias="dataDate")
    source: str


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
    current_grade: str = Field(alias="currentGrade")
    summary: str


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
