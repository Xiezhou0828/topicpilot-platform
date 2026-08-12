/**
 * TASK-BE-024C frontend adapter.
 *
 * This file maps the backend shadow read contract into a page model.  It may
 * group and format backend-provided sections, but it intentionally does not
 * calculate eligibility, risk, opportunity state, score, or ranking.
 */

export type ShadowUiState =
  | "LOADING"
  | "READY"
  | "EMPTY"
  | "DEFERRED"
  | "UNAVAILABLE"
  | "ERROR";

export type ShadowOpportunityStatus = "READY" | "EMPTY" | "DEFERRED" | "UNAVAILABLE" | "ERROR";

export type ShadowTopicIdentity = {
  id: string;
  name: string;
  grade: string | null;
  lifecycle: string | null;
  strength: number | null;
};

export type ShadowInstrumentIdentity = {
  id: string;
  symbol: string;
  name: string;
};

export type ShadowOpportunityCard = {
  opportunityId: string;
  opportunityKey: string;
  strategyId: string;
  strategyType: string;
  strategyLabelKey: string;
  displayOrder: number;
  rank: number;
  rankScore: number | null;
  rankingStatus: string;
  topic: ShadowTopicIdentity;
  instrument: ShadowInstrumentIdentity;
  instrumentId: string;
  symbol: string;
  name: string;
  topicId: string;
  topicName: string;
  topicGrade: string | null;
  topicLifecycle: string | null;
  topicStrength: number | null;
  opportunityState: string;
  eligibility: string;
  status: string;
  qualification: Record<string, unknown>;
  qualificationProvenance: Record<string, unknown>;
  confidence: string | null;
  confidenceBasis: string[];
  entryContext: Record<string, unknown>[];
  supportContext: Record<string, unknown>[];
  riskContext: Record<string, unknown>[];
  positiveFactors: Record<string, unknown>[];
  waitingFactors: Record<string, unknown>[];
  riskFactors: Record<string, unknown>[];
  exclusionFactors: Record<string, unknown>[];
  exclusionCodes: string[];
  reasonCodes: string[];
  explanation: Record<string, unknown>;
  evidenceCoverage: Record<string, unknown>;
  missingEvidence: string[];
  policyVersion: string;
  parameterVersion: string;
  rankingProfileVersion: string | null;
  asOf: string | null;
  publicationStatus: "SHADOW";
  dataStatus: string;
};

export type ShadowStrategySection = {
  strategyId: string;
  strategyType: string;
  strategyLabelKey: string;
  fit: string;
  candidateCount: number;
  backendCandidateCount: number;
  presentedCount: number;
  presentationCap: number | null;
  fullRankingRetained: boolean;
  backendRanking: Array<Record<string, unknown>>;
  opportunities: ShadowOpportunityCard[];
};

export type ShadowTopicSection = {
  id: string;
  name: string;
  grade: string | null;
  lifecycle: string | null;
  strength: number | null;
  topicId: string;
  topicName: string;
  topicGrade: string | null;
  topicLifecycle: string | null;
  topicStrength: number | null;
  asOf: string | null;
  publicationStatus: "SHADOW";
  dataStatus: string;
  strategies: Record<string, ShadowStrategySection>;
};

export type ShadowOpportunityApiResponse = {
  contractVersion: "opportunity-shadow-read.v1";
  status: ShadowOpportunityStatus;
  publicationStatus: "SHADOW";
  dataStatus: string;
  asOf: string | null;
  query: Record<string, unknown>;
  topic: ShadowTopicIdentity | null;
  topicId: string | null;
  topicName: string | null;
  topicGrade: string | null;
  topicLifecycle: string | null;
  topicStrength: number | null;
  stock: ShadowInstrumentIdentity | null;
  topics: ShadowTopicSection[];
  strategies: Record<string, ShadowStrategySection>;
  opportunities: ShadowOpportunityCard[];
  opportunity: ShadowOpportunityCard | null;
};

export type OpportunityPageModel = {
  state: ShadowUiState;
  contractVersion: string;
  publicationStatus: "SHADOW";
  dataStatus: string;
  asOf: string | null;
  query: Record<string, unknown>;
  topic: ShadowTopicIdentity | null;
  stock: ShadowInstrumentIdentity | null;
  strategySections: ShadowStrategySection[];
  topicSections: ShadowTopicSection[];
  opportunities: ShadowOpportunityCard[];
  detail: ShadowOpportunityCard | null;
};

export function shadowUiStateFromStatus(status: ShadowOpportunityStatus): ShadowUiState {
  switch (status) {
    case "READY":
      return "READY";
    case "EMPTY":
      return "EMPTY";
    case "DEFERRED":
      return "DEFERRED";
    case "UNAVAILABLE":
      return "UNAVAILABLE";
    case "ERROR":
      return "ERROR";
    default:
      return "ERROR";
  }
}

function byBackendDisplayOrder(left: ShadowOpportunityCard, right: ShadowOpportunityCard): number {
  return left.displayOrder - right.displayOrder;
}

/** Map only formal backend semantic fields; never infer new business meaning. */
export function adaptShadowOpportunityResponse(
  response: ShadowOpportunityApiResponse,
): OpportunityPageModel {
  const strategySections = Object.values(response.strategies)
    .map((section) => ({
      ...section,
      opportunities: [...section.opportunities].sort(byBackendDisplayOrder),
    }));

  return {
    state: shadowUiStateFromStatus(response.status),
    contractVersion: response.contractVersion,
    publicationStatus: response.publicationStatus,
    dataStatus: response.dataStatus,
    asOf: response.asOf,
    query: response.query,
    topic: response.topic,
    stock: response.stock,
    strategySections,
    topicSections: response.topics,
    opportunities: [...response.opportunities].sort(byBackendDisplayOrder),
    detail: response.opportunity,
  };
}

export function loadingOpportunityPageModel(): Pick<OpportunityPageModel, "state"> {
  return { state: "LOADING" };
}
