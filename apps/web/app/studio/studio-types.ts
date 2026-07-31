export type CharacterId = "coda" | "mori" | "prism" | "volt";
export type StudioTab = "meeting" | "character" | "portfolio";
export type MeetingStage = "independent" | "debate" | "conclusion";

export type CharacterProfile = {
  id: CharacterId;
  name: string;
  color: string;
  portrait: string;
  roomSprite: string;
  roomSpriteWidth: number;
  visual: string;
  personality: string;
  speakingStyle: string;
  meetingRole: string;
  strength: string;
  blindSpot: string;
  roomPosition: { left: string; top: string };
};

export type ModelProfile = {
  id: string;
  provider: string;
  modelName: string;
  modelVersion: string;
  badge: string;
  apiStatus: "UNAVAILABLE";
};

export type StrategyProfile = {
  id: string;
  name: string;
  strategyVersion: string;
  factors: string[];
  holdingPeriod: string;
  positionCount: string;
  riskPreference: string;
};

export type AgentAssignment = {
  id: string;
  sessionId: string;
  characterId: CharacterId;
  modelId: string;
  strategyId: string;
};

export type StudioSession = {
  id: string;
  sessionVersion: string;
  title: string;
  mode: "DEMO";
  source: "SCRIPTED_FIXTURE";
  asOf: string;
};

export type StudioOpinion = {
  id: string;
  sessionId: string;
  stage: MeetingStage;
  characterId: CharacterId;
  stance: "看多" | "中性" | "保守";
  confidence: number;
  summary: string;
  reasons: string[];
  risk: string;
  invalidation: string;
  candidates: string[];
  sealed: boolean;
};

export type PortfolioHolding = {
  code: string;
  name: string;
  weight: number;
  note: string;
};

export type PortfolioSnapshot = {
  id: string;
  characterId: CharacterId;
  modelVersion: string;
  strategyVersion: string;
  sessionVersion: string;
  status: "DEMO";
  returnPct: number;
  excessReturnPct: number;
  winRate: number;
  maxDrawdownPct: number;
  sampleSize: number;
  equity: number[];
  holdings: PortfolioHolding[];
};

export type DemoScenario = {
  id: string;
  title: string;
  shortLabel: string;
  session: StudioSession;
  assignments: AgentAssignment[];
  opinions: StudioOpinion[];
  conclusion: string;
};

export type DiscussionPhase = "INDEPENDENT" | "DEBATE" | "FINAL";
export type DiscussionStatus = "DEMO" | "MOCK" | "LIVE" | "RATE_LIMITED" | "UNAVAILABLE" | "ERROR";

export type DiscussionEvidence = {
  evidenceId: string;
  sourceRef: string;
  label: string;
  availability: "AVAILABLE" | "MISSING";
  value: unknown;
  observedAt: string | null;
};

export type DiscussionEvent = {
  contractVersion: "1.0.0";
  eventId: string;
  sessionId: string;
  topic: string;
  snapshotVersion: string;
  dataDate: string;
  phase: DiscussionPhase;
  phaseSequence: number;
  characterId: CharacterId | null;
  personaVersion: string | null;
  strategyId: string | null;
  strategyVersion: string | null;
  providerId: string | null;
  modelId: string | null;
  modelVersion: string | null;
  thesis: string | null;
  evidence: DiscussionEvidence[];
  risks: string[];
  confidence: number | null;
  generatedAt: string;
  latencyMs: number | null;
  usage: { inputTokens: number | null; outputTokens: number | null };
  status: DiscussionStatus;
  immutable: boolean;
  parentEventIds: string[];
  researchOnly: true;
  error?: { code: string; message: string; retryable: boolean } | null;
};

export type DiscussionRequest = {
  contractVersion: "1.0.0";
  sessionId: string;
  topic: string;
  snapshotVersion: string;
  dataDate: string;
  mode: "DEMO" | "LIVE";
  participants: Array<{
    characterId: CharacterId;
    personaVersion: string;
    strategyId: string;
    strategyVersion: string;
    bindingId: string;
  }>;
  phasePolicy: {
    order: ["INDEPENDENT", "DEBATE", "FINAL"];
    independentImmutable: true;
    appendOnly: true;
  };
};

export type OrchestrationState = "idle" | "loading" | "complete" | "partial" | "unavailable" | "rate_limited" | "error";

export type StudioOrchestration = {
  state: OrchestrationState;
  events: DiscussionEvent[];
  request: DiscussionRequest | null;
  error: string | null;
  source: "DEMO" | "MOCK" | "LIVE" | null;
};
