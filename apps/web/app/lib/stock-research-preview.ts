import research1303 from "../data/research-v2/1303.json";
import research1314 from "../data/research-v2/1314.json";
import research1319 from "../data/research-v2/1319.json";

export type ResearchStatus = string;

export type ResearchSource = {
  id: string;
  title?: string | null;
  documentTitle?: string | null;
  type?: string | null;
  publisher?: string | null;
  publishedAt?: string | null;
  documentDate?: string | null;
  retrievedAt?: string | null;
  url?: string | null;
  status?: string | null;
  claim?: string | null;
  tier?: string | null;
};

export type RevenueItem = {
  id: string;
  name: string;
  value: number;
  share?: number | null;
  businessGroupId?: string | null;
  sourceEvidenceIds?: string[];
};

export type RevenueDataset = {
  id: string;
  name?: string | null;
  period?: string | null;
  periodType?: string | null;
  reportingBasis?: string | null;
  currency?: string | null;
  unit?: string | null;
  total?: number | null;
  items: RevenueItem[];
  reconciliation?: string | null;
  chartEligible?: boolean;
  notes?: string | null;
  status?: ResearchStatus;
};

export type BusinessGroup = {
  id: string;
  name: string;
  summary?: string | null;
  products?: string[];
  applications?: string[];
  sourceEvidenceIds?: string[];
  status?: ResearchStatus;
};

export type ResearchProduct = {
  id: string;
  name: string;
  businessGroupId?: string | null;
  applications?: string[];
  sourceEvidenceIds?: string[];
  status?: ResearchStatus;
};

export type Investment = {
  id: string;
  name: string;
  stockCode?: string | null;
  relationshipType?: string | null;
  holdingPercent?: number | null;
  materiality?: string | null;
  materialityReason?: string | null;
  businessDescription?: string | null;
  financialImpact?: string | null;
  strategicImpact?: string | null;
  accountingTreatment?: string | null;
  sourceEvidenceIds?: string[];
  status?: ResearchStatus;
};

export type Chain = {
  id: string;
  name: string;
  businessGroupId?: string | null;
  upstream?: string | null;
  companyRole?: string | null;
  downstream?: string | null;
  competitiveAdvantages?: string[];
  competitiveConstraints?: string[];
  competitors?: string[];
  evidenceIds?: string[];
  status?: ResearchStatus;
};

export type ResolvedCompetitor = {
  name: string;
  stockId: string | null;
  market: "TPE" | "TWO" | null;
};

// Deterministic aliases resolved from the checked-in Taiwan instrument reference
// bundle. A missing alias stays non-navigable instead of becoming a guessed link.
const COMPETITOR_STOCK_MASTER: Record<string, { stockId: string; market: "TPE" | "TWO" }> = {
  "台玻": { stockId: "1802", market: "TPE" },
  "富喬": { stockId: "1815", market: "TWO" },
  "聯茂": { stockId: "6213", market: "TPE" },
  "台燿": { stockId: "6274", market: "TWO" },
  "台化": { stockId: "1326", market: "TPE" },
  "台塑化": { stockId: "6505", market: "TPE" },
};

export function resolveCompetitor(name: string): ResolvedCompetitor {
  const normalized = name.trim();
  const match = COMPETITOR_STOCK_MASTER[normalized];
  return { name: normalized, stockId: match?.stockId ?? null, market: match?.market ?? null };
}

export type GrowthFactor = {
  id: string;
  name: string;
  summary?: string | null;
  mechanism?: string | null;
  affectedBusinesses?: string[];
  observationIndicators?: string[];
  indicators?: string[];
  timeHorizon?: string | null;
  horizon?: string | null;
  relatedRiskIds?: string[];
  supportingEvidenceIds?: string[];
  sourceEvidenceIds?: string[];
  status?: ResearchStatus;
};

export type RiskFactor = {
  id: string;
  name: string;
  summary?: string | null;
  mechanism?: string | null;
  affectedBusinesses?: string[];
  observationIndicators?: string[];
  indicators?: string[];
  timeHorizon?: string | null;
  horizon?: string | null;
  relatedGrowthIds?: string[];
  supportingEvidenceIds?: string[];
  sourceEvidenceIds?: string[];
  status?: ResearchStatus;
};

export type FinancialMetric = {
  id: string;
  label: string;
  value: number;
  unit?: string | null;
  currency?: string | null;
  period?: string | null;
  periodType?: string | null;
  periodLabelType?: string | null;
  reportingBasis?: string | null;
  metricDefinition?: string | null;
  comparisonPeriod?: string | null;
  type?: string | null;
  status?: ResearchStatus;
};

export type FinancialItem = {
  id: string;
  type?: string | null;
  label: string;
  summary?: string | null;
  period?: string | null;
  reportingBasis?: string | null;
  unit?: string | null;
};

export type FullResearch = {
  revenueStructure?: {
    known?: string | null;
    segmentProfit?: string | null;
    geography?: string | null;
    investmentProfitDrivers?: string | null;
    investmentCoverage?: string | null;
    notEstablished?: string[];
    reason?: string | null;
    v2?: {
      summary?: { summary?: string | null; status?: ResearchStatus; evidenceIds?: string[] } | string | null;
      revenueDatasets?: RevenueDataset[];
      profitDatasets?: RevenueDataset[];
      financialMetrics?: FinancialMetric[];
      investmentItems?: Investment[];
      investmentStatus?: ResearchStatus;
      investmentReason?: string | null;
      managementTopics?: ManagementTopic[];
    } | null;
  } | null;
  researchHistory?: {
    version?: string | null;
    asOf?: string | null;
    method?: string | null;
    publication?: string | null;
    nextReview?: string | null;
  } | null;
};

export type ManagementTopic = {
  id: string;
  topic: string;
  summary?: string | null;
  statementDate?: string | null;
  sourceEvidenceIds?: string[];
  status?: ResearchStatus;
};

export type ResearchGap = {
  fieldPath?: string | null;
  status?: ResearchStatus;
  reason?: string | null;
};

export type CompanyResearchGroup = {
  id: string;
  title: string;
  summary?: string | null;
  positioning?: string | null;
  facts?: string[];
  operatingModel?: string | null;
  coreBusiness?: string | null;
  products?: ResearchProduct[] | string | null;
  industryRole?: string | null;
  coreObservation?: string | null;
  businessGroups?: BusinessGroup[];
  revenue?: {
    datasets?: RevenueDataset[];
    metrics?: FinancialMetric[];
    narrative?: string | null;
    basis?: string | null;
    status?: ResearchStatus;
  } | null;
  profit?: {
    datasets?: RevenueDataset[];
    metrics?: FinancialMetric[];
    narrative?: string | null;
    basis?: string | null;
    status?: ResearchStatus;
  } | null;
  investments?: {
    items?: Investment[];
    limitations?: string[];
    status?: ResearchStatus;
    reason?: string | null;
  } | null;
  chains?: Chain[];
  customers?: string[];
  competitors?: string[];
  competitivePosition?: string | null;
  limitations?: string[];
  growthFactors?: GrowthFactor[];
  riskFactors?: RiskFactor[];
  metrics?: FinancialMetric[];
  items?: FinancialItem[];
  managementTopics?: ManagementTopic[];
  updatedAt?: string | null;
  periods?: string[];
  sources?: ResearchSource[];
  gaps?: ResearchGap[];
  conflicts?: string[];
  uncertainties?: string[];
  fullResearch?: FullResearch | null;
};

export type CompanyResearchViewV2 = {
  schemaVersion: "company-research-view.v2";
  inputSchemaVersion?: string;
  researchId: string;
  stock: { code: string; nameZh: string; market?: string | null };
  researchVersion?: string | null;
  researchAsOf?: string | null;
  coverageStatus?: ResearchStatus;
  publicationStatus?: string | null;
  summary?: string | null;
  groups: CompanyResearchGroup[];
};

const FIXTURES: Record<string, CompanyResearchViewV2> = {
  "1303": research1303 as CompanyResearchViewV2,
  "1314": research1314 as CompanyResearchViewV2,
  "1319": research1319 as CompanyResearchViewV2,
};

export function getPreviewStockResearch(code: string): CompanyResearchViewV2 | null {
  return FIXTURES[code.trim()] ?? null;
}

export function getResearchGroup(view: CompanyResearchViewV2 | null, id: string): CompanyResearchGroup | null {
  return view?.groups.find((group) => group.id === id) ?? null;
}

export function getOfficialSources(view: CompanyResearchViewV2 | null): ResearchSource[] {
  const group = getResearchGroup(view, "sources_and_limitations");
  const sources = group?.sources ?? [];
  const seen = new Set<string>();
  return sources.filter((source) => {
    const isOfficial = source.tier === "P2" || source.type?.startsWith("OFFICIAL_");
    const isInternal = /FIXTURE|INTERNAL|TEST|MAPPING/i.test(source.type ?? "") || /fixture|test/i.test(`${source.title ?? ""} ${source.documentTitle ?? ""}`);
    if (!isOfficial || isInternal || !source.url || seen.has(source.url)) return false;
    seen.add(source.url);
    return true;
  });
}
