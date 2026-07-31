export type NullableNumber = number | null;
export type DataOrigin = "api" | "demo";

export interface DataStatus {
  dataDate: string | null;
  updatedAt: string | null;
  bundleVersion: string | null;
  sourceMode: string | null;
  apiStatus: "healthy" | "degraded" | "unavailable";
  databaseStatus: "healthy" | "degraded" | "unavailable";
  latencyMs: NullableNumber;
  counts: { stocks: NullableNumber; topics: NullableNumber; strategyCandidates: NullableNumber };
  quality: { passed: NullableNumber; warnings: NullableNumber; failed: NullableNumber };
}

export interface StockSummary {
  code: string;
  name: string;
  market: string | null;
  group: string | null;
  price: NullableNumber;
  changePct: NullableNumber;
  volumeRatio: NullableNumber;
  signal: string | null;
  topicNames: string[];
  updatedAt: string | null;
}

export interface StockDetail extends StockSummary {
  description: string | null;
  technical: {
    trend: string | null;
    aboveMa20: boolean | null;
    relativeStrength20: NullableNumber;
    volatility20: NullableNumber;
  };
  fundamental: {
    revenueYoy: NullableNumber;
    revenueMom: NullableNumber;
    grossMargin: NullableNumber;
  };
  qualityNotes: string[];
}

export interface TopicTrendPoint { date: string; score: NullableNumber }

export interface TopicSummary {
  slug: string;
  name: string;
  parentName: string | null;
  grade: string | null;
  score: NullableNumber;
  change14d: NullableNumber;
  memberCount: NullableNumber;
  state: string | null;
}

export interface TopicDetail extends TopicSummary {
  description: string | null;
  trend: TopicTrendPoint[];
  stocks: StockSummary[];
}

export type StrategyKey = "MAS" | "MAV" | "TMC" | "BB" | "PB" | "KD";

export interface StrategySummary {
  key: StrategyKey;
  name: string;
  summary: string;
  status: string | null;
  candidateCount: NullableNumber;
  dataDate: string | null;
}

export interface StrategyCandidate {
  strategyKey: StrategyKey;
  rank: NullableNumber;
  code: string;
  name: string;
  score: NullableNumber;
  price: NullableNumber;
  topic: string | null;
  reason: string | null;
  dataDate: string | null;
}

export interface StrategyPerformance {
  strategyKey: StrategyKey;
  horizon: string;
  sampleCount: NullableNumber;
  returnPct: NullableNumber;
  winRatePct: NullableNumber;
}

export interface TopicRotationItem extends TopicSummary {
  direction: "warming" | "cooling" | "steady";
}

export interface ApiList<T> { items: T[]; total: number; limit: number; offset: number }

export interface LoadedResource<T> {
  data: T;
  origin: DataOrigin;
  warning: string | null;
}
