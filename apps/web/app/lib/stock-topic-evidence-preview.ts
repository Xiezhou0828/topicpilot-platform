import topicStories1303 from "../data/topic-stories-v1/1303.json";
import topicStories1314 from "../data/topic-stories-v1/1314.json";
import topicStories1319 from "../data/topic-stories-v1/1319.json";

export type EvidenceStatus = "FACT" | "INFERENCE" | "UNVERIFIED" | "UNDISCLOSED";
export type StoryPattern =
  | "PRODUCT_SUPPLY_CHAIN"
  | "PRICE_PROFIT_TRANSMISSION"
  | "ASSET_PROJECT_TIMELINE"
  | "EVIDENCE_GAP"
  | "GENERAL_OPERATING_RELATIONSHIP";

export type TopicStoryEvidence = {
  evidenceId: string;
  title: string;
  claim: string;
  evidenceType: string;
  sourceRef: string;
  sourceDate: string | null;
  documentTitle: string;
  documentLocator: string;
  sourceUrl?: string | null;
  evidenceStatus: EvidenceStatus;
  limitations: string;
};

export type TopicStoryNode = {
  nodeId: string;
  label: string;
  nodeType: string;
  description: string;
  companyParticipation: string;
  evidenceStatus: EvidenceStatus;
  evidenceRefs: string[];
  visualHint?: string | null;
};

export type TopicStoryEdge = {
  edgeId: string;
  sourceNodeId: string;
  targetNodeId: string;
  relationType: string;
  relationDescription: string;
  evidenceStatus: EvidenceStatus;
  evidenceRefs: string[];
};

export type TopicStoryFinancialImpact = {
  metricName: string;
  metricValue: number | null;
  unit: string | null;
  period: string | null;
  scope: "company" | "segment" | "product" | "topic";
  scopeLabel: string;
  sourceRef: string | null;
  evidenceStatus: EvidenceStatus;
  attributionLimitations: string;
};

export type TopicStoryTimelineEvent = {
  eventId: string;
  eventDate?: string | null;
  datePrecision?: string | null;
  eventTitle: string;
  eventType: string;
  milestoneStatus: string;
  evidenceRefs: string[];
  description?: string;
};

export type TopicStoryView = {
  schemaVersion: "stock-topic-evidence-view.v1";
  stockId: string;
  stockName: string;
  topicId: string;
  canonicalTopicName: string;
  formalAssociationReference: {
    relationId?: string | null;
    relationType: string;
    approvalState: string;
    referenceSource: string;
  };
  formalAuthorityVersion: string;
  effectiveDate: string;
  structuralRoleReference: {
    relationId?: string | null;
    structuralRole: string;
    relationType?: string | null;
    authorityVersion: string;
    effectiveDate?: string | null;
  };
  researchAsOfDate: string;
  researchStatus: "READY" | "READY_WITH_LIMITATIONS" | "PARTIAL_READY" | "NOT_READY";
  storyPattern: StoryPattern;
  storyTitle: string;
  storySummary: string;
  companyParticipationSummary: string;
  sections: Array<{ sectionId: string; title: string; summary: string; evidenceRefs?: string[] }>;
  nodes: TopicStoryNode[];
  edges: TopicStoryEdge[];
  evidence: TopicStoryEvidence[];
  financialImpact: TopicStoryFinancialImpact[];
  timeline: TopicStoryTimelineEvent[];
  limitations: string[];
  watchIndicators: string[];
  formalTopicMutation: "NO";
};

export type TopicStoryCollection = {
  schemaVersion: "stock-topic-evidence-collection.v1";
  stockId: string;
  stockName: string;
  formalAuthorityVersion: string;
  structuralRoleAuthorityVersion: string;
  researchAsOfDate: string;
  formalTopicMutation: "NO";
  stories: TopicStoryView[];
};

const PREVIEW_STORIES: Record<string, TopicStoryCollection> = {
  "1303": topicStories1303 as TopicStoryCollection,
  "1314": topicStories1314 as TopicStoryCollection,
  "1319": topicStories1319 as TopicStoryCollection,
};

export function getPreviewStockTopicStories(stockId: string): TopicStoryCollection | null {
  return PREVIEW_STORIES[stockId.trim()] ?? null;
}

export function getTopicStoryRelationPreview(collection: TopicStoryCollection | null) {
  return collection?.stories.map((story) => ({
    topicName: story.canonicalTopicName,
    topicSlug: story.canonicalTopicName,
    relationType: story.formalAssociationReference.relationType,
    topicRole: story.structuralRoleReference.structuralRole,
  })) ?? [];
}

export function getTopicStoryEvidence(story: TopicStoryView, evidenceIds: string[]): TopicStoryEvidence[] {
  const selected = new Set(evidenceIds);
  return story.evidence.filter((item) => selected.has(item.evidenceId));
}
