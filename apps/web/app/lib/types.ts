// WEB-DATA-002 前端資料型別契約
// 說明：這裡同時定義「後端 snapshot 原始形狀（Raw*）」與「頁面消費的視圖模型（*View / *Data）」。
// 視圖模型刻意讓每個欄位都可為 null，讓缺資料不會炸頁面（見 WEB_DATA_GAP_MAP.md）。

export type DataSourceKind = "snapshot" | "mock";

export type Stance = "risk-on" | "neutral" | "risk-off";

// ---- 後端 snapshot 原始形狀（來自 tools/export_web_snapshot.py）----
export type RawStock = {
  code: string;
  name: string | null;
  price?: Record<string, number | string | null>;
  technical?: Record<string, unknown>;
  entry?: Record<string, number | string | null>;
  chip?: Record<string, number | string | null>;
  fundamental?: Record<string, number | string | null>;
  risk?: Record<string, string | null>;
  topicMain?: string | null;
  topicSub?: string | null;
  topicMainWeight?: number | null;
  topicSubWeight?: number | null;
  topicRelations?: Array<Record<string, unknown>>;
  quality?: Record<string, unknown>;
};

export type RawObservation = {
  rank?: number | null;
  code: string;
  name: string | null;
  section?: string | null;
  setup: string | null;
  watchDays: number | null;
  firstSeen?: string | null;
  lastSeen?: string | null;
  topic?: string | null;
  topicRole?: string | null;
  topicDefinition?: string | null;
  marketNote?: string | null;
  technicalSubtype?: string | null;
  dailySetupScore?: number | null;
  entryScore?: number | null;
  price?: number | null;
  trigger?: number | string | null;
  triggerValue?: number | null;
  triggerLabel?: string | null;
  support?: number | string | null;
  supportValue?: number | null;
  supportLabel?: string | null;
  pressure?: number | string | null;
  pressureValue?: number | null;
  pressureLabel?: string | null;
  invalid?: number | string | null;
  invalidationValue?: number | null;
  invalidationLabel?: string | null;
  distanceToTriggerPct?: number | null;
  stopLossPct?: number | null;
  gate?: string | null;
  gateReason?: string | null;
  chipConfirmation?: string | null;
  fundamentalCatalyst?: string | null;
  shortRisk?: string | null;
  dataFreshness?: string | null;
  exceptionMessage?: string | null;
  mainRisk?: string | null;
  suggestedAction?: string | null;
  updatedAt?: string | null;
  現價?: number | null;
  觸發價?: number | null;
  "距觸發價%"?: number | null;
  EntryScore?: number | null;
  Gate?: string | null;
};

export type RawIndex = {
  name: string;
  market?: string;
  close?: number | null;
  ma20?: number | null;
  "ma20Slope%"?: number | null;
  env?: string | null;
  asOf?: string | null;
  source?: string | null;
};

export type RawQuality = {
  priceRows?: number;
  technicalRows?: number;
  chipRows?: number;
  fundamentalRows?: number;
  entryRows?: number;
  dailyObservationRows?: number;
  dailyObservationSource?: string | null;
  entrySource?: string | null;
  universe?: number;
  missingPrice?: string[];
  missingTechnical?: string[];
  missingChip?: string[];
  missingFundamental?: string[];
  missingEntry?: string[];
  unavailableTechnicalFields?: string[];
};

export type RawQuoteMeta = {
  status?: "COMPLETE" | "PARTIAL" | "FAILED" | "NOT_RUN" | null;
  dataDate?: string | null;
  updatedAt?: string | null;
  source?: string | null;
  totalSymbols?: number | null;
  successSymbols?: number | null;
  failedSymbols?: number | null;
  failedCodes?: string[];
};

export type RawMarketSession = {
  market?: string | null;
  timezone?: string | null;
  currentDate?: string | null;
  latestTradingDate?: string | null;
  isTradingDay?: boolean | null;
  session?: "PREOPEN" | "OPEN" | "CLOSED" | "HOLIDAY" | "SUSPENDED" | null;
  reason?: string | null;
  nextTradingDate?: string | null;
};

export type RawRadarMetric = {
  count?: number | null;
  denominator?: number | null;
  pct?: number | null;
};

export type RawRadarRotationItem = {
  name?: string | null;
  score?: number | null;
  grade?: string | null;
  strengthState?: string | null;
  breadth?: {
    advance?: number | null;
    decline?: number | null;
    flat?: number | null;
    unavailable?: number | null;
    denominator?: number | null;
    pct?: number | null;
  };
  coverage?: RawRadarMetric;
  stockCount?: number | null;
  historyChange14d?: number | null;
  historyChangeReason?: string | null;
  historyPointCount?: number | null;
  historyStartDate?: string | null;
  historyEndDate?: string | null;
  scoreSource?: string | null;
};

export type RawMarketRadar = {
  asOf?: string | null;
  dataDate?: string | null;
  source?: Record<string, string | null>;
  universe?: {
    label?: string | null;
    scope?: string | null;
    total?: number | null;
    priced?: number | null;
    technicalEligible?: number | null;
    missing?: { price?: number | null; technical?: number | null };
  };
  breadth?: {
    advance?: number | null;
    decline?: number | null;
    flat?: number | null;
    unavailable?: number | null;
    aboveMa60?: RawRadarMetric;
    rs5Positive?: RawRadarMetric;
    rs20Positive?: RawRadarMetric;
    macdPositive?: RawRadarMetric;
  };
  chipBreadth?: {
    positive?: number | null;
    negative?: number | null;
    neutral?: number | null;
    missing?: number | null;
    denominator?: number | null;
    institutionalAsOf?: string | null;
    tdccAsOf?: string | null;
  };
  topicRotation?: {
    groups?: RawRadarRotationItem[];
    topics?: RawRadarRotationItem[];
    history?: {
      source?: string | null;
      asOf?: string | null;
      maxTradingDays?: number | null;
      availableTradingDates?: string[];
      availableTradingDayCount?: number | null;
      formalTopicCount?: number | null;
      historyHeaderTopicCount?: number | null;
      formalTopicsWithoutHistory?: string[];
      unmappedHistoryTopics?: string[];
      excludedNonTradingDates?: string[];
      degradationPolicy?: string | null;
    };
  };
  definitions?: Record<string, string | null>;
};

export type RawMarketDecisionEvidence = {
  code?: string | null;
  label?: string | null;
  signal?: string | null;
  count?: number | null;
  denominator?: number | null;
  pct?: number | null;
  detail?: string | null;
  positive?: number | null;
  negative?: number | null;
  missing?: number | null;
};

export type RawMarketDecision = {
  version?: string | null;
  asOf?: string | null;
  dataDate?: string | null;
  state?: { code?: string | null; label?: string | null };
  observationMode?: { code?: string | null; label?: string | null };
  headline?: string | null;
  confidence?: { code?: string | null; validSignals?: number | null; totalSignals?: number | null };
  evidence?: RawMarketDecisionEvidence[];
  risks?: Array<{ code?: string | null; label?: string | null; severity?: string | null; detail?: string | null }>;
  topicRotationSummary?: {
    warmingCount?: number | null;
    coolingCount?: number | null;
    flatCount?: number | null;
    missingCount?: number | null;
    topWarming?: Array<{ topic?: string | null; change14d?: number | null; score?: number | null; grade?: string | null }>;
    topCooling?: Array<{ topic?: string | null; change14d?: number | null; score?: number | null; grade?: string | null }>;
  };
};

export type RawStrategyRegistryItem = {
  strategyId?: string | null;
  name?: string | null;
  modelVersion?: string | null;
  batchDate?: string | null;
  batchStatus?: string | null;
  candidateCount?: number | null;
  selectedCount?: number | null;
  rankingCount?: number | null;
  missingReason?: string | null;
};

export type RawStrategyCandidate = {
  strategyId?: string | null;
  strategyKey?: string | null;
  modelVersion?: string | null;
  batchDate?: string | null;
  rank?: number | null;
  code?: string | null;
  name?: string | null;
  majorGroup?: string | null;
  fineTopic?: string | null;
  score?: number | null;
  reason?: string | null;
  price?: number | null;
  dataDate?: string | null;
  dataTime?: string | null;
  selected?: boolean | null;
  trigger?: number | null;
  support?: number | null;
  invalidation?: number | null;
};

export type RawStrategyPerformance = {
  strategyId?: string | null;
  strategyKey?: string | null;
  name?: string | null;
  modelVersion?: string | null;
  dataDate?: string | null;
  status?: string | null;
  sampleCount?: number | null;
  availableHorizonCount?: number | null;
  horizons?: Record<string, { status?: string | null; sampleCount?: number | null; winRate?: number | null; returnPct?: number | null; avgReturnPct?: number | null; reason?: string | null }>;
  source?: string | null;
};

export type RawSnapshot = {
  snapshotVersion?: string;
  classification?: string | null;
  generatedAt?: string | null;
  dataDate?: string | null;
  quoteMeta?: RawQuoteMeta;
  marketSession?: RawMarketSession;
  quality?: RawQuality;
  market?: { indices?: RawIndex[] };
  topics?: RawTopic[];
  topicGroups?: RawTopicGroup[];
  topicRelations?: RawTopicRelation[];
  topicStrengthHistory?: RawTopicStrengthHistory[] | Record<string, unknown>;
  marketRadar?: RawMarketRadar;
  marketDecision?: RawMarketDecision;
  strategyRegistry?: { version?: string | null; dataDate?: string | null; strategies?: RawStrategyRegistryItem[] };
  strategyCandidates?: RawStrategyCandidate[];
  strategyPerformance?: RawStrategyPerformance[];
  dailyObservation?: RawObservation[];
  entrySetups?: unknown[];
  stocks?: Record<string, RawStock>;
};

export type RawTopic = {
  name: string;
  group?: string | null;
  type?: string | null;
  grade?: string | null;
  childGrade?: string | null;
  strengthState?: string | null;
  confidence?: string | null;
  score?: number | null;
  strengthScore?: number | null;
  strengthSource?: string | null;
  calculationStatus?: string | null;
  breadth?: string | null;
  breadthRatio?: number | null;
  stockCount?: number | null;
  observedCount?: number | null;
  strongCount?: number | null;
  weakCount?: number | null;
  signal?: string | null;
  leaders?: string[];
  relationCount?: number | null;
  note?: string | null;
};

export type RawTopicGroup = {
  name: string;
  score?: number | null;
  strengthState?: string | null;
  childCount?: number | null;
  scoredChildCount?: number | null;
  strongestChild?: string | null;
  strongestChildScore?: number | null;
  children?: string[];
};

export type RawTopicRelation = {
  股號: string;
  名稱?: string | null;
  題材: string;
  題材角色?: string | null;
  題材類型?: string | null;
  主大族群?: string | null;
  關聯大族群?: string | null;
  關係?: string | null;
  權重?: number | null;
  是否計分?: string | null;
  是否啟用?: string | null;
  最低有效樣本數?: number | null;
  大族群內權重?: number | null;
  標準化狀態?: string | null;
  題材順序?: number | null;
};

export type RawTopicStrengthPoint = {
  date?: string | null;
  tradingDate?: string | null;
  score?: number | null;
  strengthScore?: number | null;
  grade?: string | null;
  strengthState?: string | null;
};

export type RawTopicStrengthHistory = {
  topic?: string | null;
  name?: string | null;
  points?: RawTopicStrengthPoint[];
};

// ---- 頁面消費的視圖模型 ----
export type MarketIndexView = {
  name: string;
  value: string; // 顯示字串；缺資料時為「待接資料源」
  change: number | null; // 日漲跌%；snapshot 無日變動時為 null
  stance: Stance;
  pending: boolean; // true = 尚無真實資料，僅 placeholder
  subLabel: string | null; // 例如環境/斜率或資料時間
  asOf: string | null;
};

// 觀察列（首頁 preview 與觀察清單共用的核心欄位）
export type ObservationRow = {
  code: string;
  name: string | null;
  section: string | null; // 分段（回檔轉強 / 等突破 / 波段新高等回測…）
  subType: string | null; // 技術子型態（型態階段 / RS 狀態近似）
  price: number | null;
  change: number | null;
  volume: number | null;
  volumeRatio: number | null;
  volumeStatus: string | null;
  trigger: number | null;
  triggerLabel: string | null; // 觸發價原始描述（可能含文字，如「突破近期高點 18.3」）
  distance: number | null; // 距觸發%
  entryScore: number | null;
  gate: string | null; // PASS / WARN / BLOCK
  fundingConfirm: string | null; // 資金確認燈號文字
  fundamentalCatalyst: string | null; // 基本面催化燈號文字
  shortRisk: string | null; // 短線風險
  watchDays: number | null;
  dataFreshness: string | null; // 個股資料新鮮度（CURRENT / STALE…）
  exceptionMessage: string | null;
  updatedAt: string | null; // 該列最後更新時間
  topicRole: string | null;
  topicDefinition: string | null;
};

// 觀察清單列（ObservationRow + 進階欄位）
export type WatchRow = ObservationRow & {
  rank: number;
  topic: string | null;
  support: number | null; // 觀察支撐
  supportLabel: string | null;
  resistance: number | null; // 壓力價
  resistanceLabel: string | null;
  invalidation: number | null; // 失效價
  invalidationLabel: string | null;
  stopPct: number | null; // 停損幅度%
  gateReason: string | null; // Gate 原因
  entrySetup: string | null; // 後端既有 Entry Setup
  suggestedAction: string | null; // 後端既有建議動作
  foreignFlow: number | null; // 外資5日買超佔量%
  hasFunding: boolean;
  hasCatalyst: boolean;
  hasRisk: boolean;
};

export type Freshness = {
  snapshotVersion?: string | null;
  dataDate: string | null;
  generatedAt: string | null;
  completeness: string; // 例如「報價 188、技術 188、籌碼 188、基本面 188、Gate 31」
  note: string | null;
  sourceLabel: string; // 「後端 snapshot」/「示範資料（mock）」
  priceAsOf: string | null; // 報價資料日期
  quoteUpdatedAt: string | null; // 後台報價更新時間
  quoteSource: string | null; // 後台報價來源
  quoteStatus: string | null;
  latestTradingDate: string | null;
  marketSession: string | null;
  marketSessionReason: string | null;
  technicalAsOf: string | null; // 技術資料時間
  institutionalAsOf: string | null; // 法人資料日期
  tdccAsOf: string | null; // TDCC 大戶資料日期
  fundamentalYm: string | null; // 基本面資料年月
  stale: boolean; // 是否有資料被標記為過舊
  staleReason: string | null;
};

export type QualityView = {
  total: number;
  priceRows: number;
  technicalRows: number;
  chipRows: number;
  fundamentalRows: number;
  entryRows: number;
  missingChip: number;
  missingFundamental: number;
  missingEntry: number;
  unavailableTechnical: string[];
  dailyObservationSource: string | null;
  entrySource: string | null;
} | null;

export type ObservationSummary = { section: string; count: number };

export type HomeData = {
  source: DataSourceKind;
  freshness: Freshness;
  quality: QualityView;
  marketIndices: MarketIndexView[];
  observation: {
    total: number;
    asOf: string | null;
    summary: ObservationSummary[];
    completenessNote: string;
  };
  preview: ObservationRow[];
};

export type WatchlistData = {
  source: DataSourceKind;
  freshness: Freshness;
  quality: QualityView;
  rows: WatchRow[];
  sections: string[]; // 可篩的分段清單
};

// TASK G：資料品質面板消費的精簡結構（由 freshness + quality 組出）。
export type QualityPanelData = {
  source: DataSourceKind;
  freshness: Freshness;
  quality: QualityView;
};

// TASK H：單一 loader 產出的整包資料，供首頁 / 觀察清單 / 品質面板共用同一份 snapshot。
export type SnapshotBundle = {
  source: DataSourceKind;
  homeData: HomeData;
  watchlistData: WatchlistData;
  qualityPanelData: QualityPanelData;
  topics: TopicView[];
  topicGroups: TopicGroupView[];
  stockUniverse: StockView[];
  topicRelations: TopicRelationView[];
  topicStrengthHistory: TopicStrengthHistoryView[];
  marketRadar: MarketRadarView | null;
  marketDecision: MarketDecisionView | null;
  strategyRegistry: StrategyRegistryView | null;
  strategyCandidates: StrategyCandidateView[];
  strategyPerformance: StrategyPerformanceView[];
};

export type StrategyRegistryItemView = {
  strategyId: string;
  name: string;
  modelVersion: string | null;
  batchDate: string | null;
  batchStatus: string | null;
  candidateCount: number | null;
  selectedCount: number | null;
  rankingCount: number | null;
  missingReason: string | null;
};

export type StrategyRegistryView = { version: string | null; dataDate: string | null; strategies: StrategyRegistryItemView[] };

export type StrategyCandidateView = {
  strategyId: string;
  strategyKey: string | null;
  modelVersion: string | null;
  batchDate: string | null;
  rank: number | null;
  code: string;
  name: string | null;
  majorGroup: string | null;
  fineTopic: string | null;
  score: number | null;
  reason: string | null;
  price: number | null;
  dataDate: string | null;
  dataTime: string | null;
  trigger: number | null;
  support: number | null;
  invalidation: number | null;
};

export type StrategyPerformanceHorizonView = { horizon: string; status: string | null; sampleCount: number | null; winRate: number | null; returnPct: number | null; reason: string | null };
export type StrategyPerformanceView = { strategyId: string; strategyKey: string | null; name: string | null; modelVersion: string | null; dataDate: string | null; status: string | null; sampleCount: number | null; availableHorizonCount: number | null; horizons: StrategyPerformanceHorizonView[]; source: string | null };

export type RadarMetricView = {
  count: number | null;
  denominator: number | null;
  pct: number | null;
};

export type RadarRotationItemView = {
  name: string;
  score: number | null;
  grade: string | null;
  strengthState: string | null;
  breadth: {
    advance: number | null;
    decline: number | null;
    flat: number | null;
    unavailable: number | null;
    denominator: number | null;
    pct: number | null;
  };
  coverage: RadarMetricView;
  stockCount: number | null;
  historyChange14d: number | null;
  historyChangeReason: string | null;
  historyPointCount: number | null;
  historyStartDate: string | null;
  historyEndDate: string | null;
  scoreSource: string | null;
};

export type MarketRadarView = {
  asOf: string | null;
  dataDate: string | null;
  source: Record<string, string | null>;
  universe: {
    label: string | null;
    scope: string | null;
    total: number | null;
    priced: number | null;
    technicalEligible: number | null;
    missingPrice: number | null;
    missingTechnical: number | null;
  };
  breadth: {
    advance: number | null;
    decline: number | null;
    flat: number | null;
    unavailable: number | null;
    aboveMa60: RadarMetricView;
    rs5Positive: RadarMetricView;
    rs20Positive: RadarMetricView;
    macdPositive: RadarMetricView;
  };
  chipBreadth: {
    positive: number | null;
    negative: number | null;
    neutral: number | null;
    missing: number | null;
    denominator: number | null;
    institutionalAsOf: string | null;
    tdccAsOf: string | null;
  };
  groups: RadarRotationItemView[];
  topics: RadarRotationItemView[];
  history: {
    source: string | null;
    asOf: string | null;
    maxTradingDays: number | null;
    availableTradingDates: string[];
    availableTradingDayCount: number | null;
    formalTopicCount: number | null;
    historyHeaderTopicCount: number | null;
    formalTopicsWithoutHistory: string[];
    unmappedHistoryTopics: string[];
    excludedNonTradingDates: string[];
    degradationPolicy: string | null;
  };
  definitions: Record<string, string | null>;
};

export type MarketDecisionEvidenceView = {
  code: string | null;
  label: string | null;
  signal: string | null;
  count: number | null;
  denominator: number | null;
  pct: number | null;
  detail: string | null;
  positive: number | null;
  negative: number | null;
  missing: number | null;
};

export type MarketDecisionTopicView = {
  topic: string;
  change14d: number | null;
  score: number | null;
  grade: string | null;
};

export type MarketDecisionView = {
  version: string | null;
  asOf: string | null;
  dataDate: string | null;
  state: { code: string | null; label: string | null };
  observationMode: { code: string | null; label: string | null };
  headline: string | null;
  confidence: { code: string | null; validSignals: number | null; totalSignals: number | null };
  evidence: MarketDecisionEvidenceView[];
  risks: Array<{ code: string | null; label: string | null; severity: string | null; detail: string | null }>;
  topicRotationSummary: {
    warmingCount: number | null;
    coolingCount: number | null;
    flatCount: number | null;
    missingCount: number | null;
    topWarming: MarketDecisionTopicView[];
    topCooling: MarketDecisionTopicView[];
  };
};

export type TopicRelationView = {
  code: string;
  name: string | null;
  topic: string;
  role: string | null;
  type: string | null;
  parentGroup: string | null;
  relatedGroup: string | null;
  relation: string | null;
  weight: number | null;
  scoring: string | null;
};

export type StockView = {
  code: string;
  name: string | null;
  price: number | null;
  change: number | null;
  volume: number | null;
  volumeRatio: number | null;
  volumeStatus: string | null;
  dataDate: string | null;
  updatedAt: string | null;
  source: string | null;
  fundamental: StockFundamentalView;
  riskNote: string | null;
  dataFreshness: string | null;
  exceptionMessage: string | null;
  technicalSubtype: string | null;
  signalSummary: {
    chipActive: boolean;
    chipAvailable: boolean;
    operationsActive: boolean;
    operationsAvailable: boolean;
    riskActive: boolean;
    riskAvailable: boolean;
  };
  screener: StockScreenerSignals;
  topicMain: string | null;
  topicSub: string | null;
  topicNames: string[];
  relations: TopicRelationView[];
  watch: WatchRow | null;
};

export type StockFundamentalView = {
  revenueYoY: number | null;
  revenueMoM: number | null;
  revenue3mYoY: number | null;
  revenue3mPreviousYoY: number | null;
  asOf: string | null;
  source: string | null;
};

// FRONTEND-STOCK-SCREENER-001：只搬運 snapshot 已計算的值；null 代表資料不足。
export type StockScreenerSignals = {
  close: number | null;
  ma20: number | null;
  ma60: number | null;
  ma20SlopePct: number | null;
  daysAboveMa20: number | null;
  reclaimedMa20: boolean | null;
  movingAverageAlignment: string | null;
  structureState: string | null;
  rs5Pct: number | null;
  rs20Pct: number | null;
  rsState: string | null;
  distanceTo20DayHighPct: number | null;
  breakout20DayHigh: boolean | null;
  macdDif: number | null;
  macdSignal: number | null;
  macdHist: number | null;
  macdHistTurnedPositive: boolean | null;
  macdGoldenCross: boolean | null;
  difAboveZero: boolean | null;
  kdK: number | null;
  kdD: number | null;
  kdGoldenCross: boolean | null;
  kdLowGoldenCross: boolean | null;
  kdMidLowGoldenCross: boolean | null;
  rsi14: number | null;
  volumeRatio: number | null;
  volumeStatus: string | null;
  upVolumeRatio: number | null;
  breakoutWithVolume: boolean | null;
  pullbackVolumeShrinkRatio: number | null;
  restartConfirmed: boolean | null;
  foreignBuyStreakDays: number | null;
  trustBuyStreakDays: number | null;
  institutionsInSync: boolean | null;
  foreignFiveDayBuyPct: number | null;
  trustFiveDayBuyPct: number | null;
  largeHolderWeeklyChangePp: number | null;
  largeHolder400Pct: number | null;
  largeHolder1000Pct: number | null;
  largeHolder1000WeeklyChangePp: number | null;
  retailHolderWeeklyChangePp: number | null;
  technicalAsOf: string | null;
  institutionalAsOf: string | null;
  tdccAsOf: string | null;
  chipDataGap: string | null;
};

export type TopicStrengthPointView = {
  date: string;
  score: number | null;
  grade: string | null;
  strengthState: string | null;
};

export type TopicStrengthHistoryView = {
  topic: string;
  points: TopicStrengthPointView[];
};

export type TopicView = {
  name: string;
  group: string | null;
  type: string | null;
  grade: string;
  childGrade: string | null;
  strengthState: string | null;
  confidence: string | null;
  score: number | null;
  strengthScore: number | null;
  strengthSource: string | null;
  calculationStatus: string | null;
  breadth: string | null;
  breadthRatio: number | null;
  stockCount: number | null;
  observedCount: number | null;
  strongCount: number | null;
  weakCount: number | null;
  signal: string | null;
  leaders: string[];
  relationCount: number | null;
  note: string | null;
};

export type TopicGroupView = {
  name: string;
  score: number | null;
  strengthState: string | null;
  childCount: number | null;
  scoredChildCount: number | null;
  strongestChild: string | null;
  strongestChildScore: number | null;
  children: string[];
};
