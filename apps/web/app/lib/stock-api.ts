import type { components, operations } from "./generated-api";

export type StockApiSource = "api" | "synthetic-snapshot" | "unavailable";

type FormalStockRead = components["schemas"]["StockReadModel"];
type FormalStockPage = components["schemas"]["StockReadModelPage"];

export type StockListQuery = NonNullable<
  operations["stocks_api_v2_stocks_get"]["parameters"]["query"]
>;

export type StockEodRead = components["schemas"]["StockEodRead"];
export type StockApiRelation = components["schemas"]["StockTopicRelationRead"];
export type StockHistoryRead = components["schemas"]["HistoricalPriceHistoryResponse"];
export type StockHistoryPoint = components["schemas"]["HistoricalPricePoint"];

export type CompanyResearchV4 = {
  stockCode: string;
  displayName: string | null;
  researchAsOf: string | null;
  publicationStatus: "PUBLISHED" | "UNPUBLISHED" | "NOT_CONNECTED" | "BLOCKED";
  overviewData?: Record<string, { shortDesc?: string | null } | undefined> | null;
  sections?: Record<string, { summary?: string | null } | undefined> & {
    customersAndChannels?: {
      summary?: string | null;
      customerConcentration?: {
        period?: string | null;
        largestCustomerRevenueShare?: number | null;
        unit?: string | null;
        statusNote?: string | null;
      };
    };
    financialPerformance?: {
      summary?: string | null;
      annualSnapshot?: {
        period?: string | null;
        unit?: string | null;
        revenue?: number | null;
        operatingIncome?: number | null;
        pretaxIncome?: number | null;
        netIncome?: number | null;
        operatingCashFlow?: number | null;
        statusNote?: string | null;
      };
    };
    productsAndMarket?: {
      summary?: string | null;
      revenueMixPeriod?: string | null;
      revenueMix?: Array<{ category: string; value: number | null; unit: string | null; share: number | null }>;
      currentProductsAndServices?: string[];
    };
  } | null;
  investmentThemes: Array<{
    themeTitle: string;
    timeHorizon: string | null;
    opportunity?: { summary: string | null; metrics: string[] };
    risk?: { summary: string | null; metrics: string[] };
  }>;
  operatingMatrix: Array<{
    name: string;
    revenue?: { value: number | null; unit: string | null; period: string | null; statusNote: string | null; share?: number | null };
    profit?: { value: number | null; unit: string | null; period: string | null; statusNote: string | null; share?: number | null };
    products?: Array<{
      name: string;
      lifecycle?: string | null;
      specification?: string | null;
      generation?: string | null;
      qualificationStatus?: string | null;
      contributionTimeline?: string | null;
      applications?: string[];
    }>;
    applications?: string[];
  }>;
  finance?: {
    forecast?: {
      forwardEps: number | null;
      unit: string | null;
      epsTrend: string | null;
      forecastStatus: string | null;
      modelMethod: string | null;
      statusNote: string | null;
    };
    valuation?: {
      valuationMethod: string | null;
      currentPrice: number | null;
      valuationStatus: string | null;
      valuationDisplay: string | null;
      peBands: { cheap: number | null; fair: number | null; expensive: number | null };
      statusNote: string | null;
    };
    historicalTable?: {
      unitNote?: string | null;
      headers?: Array<{ key: string | null; label: string | null }>;
      rows?: Array<{
        metricKey: string | null;
        label: string | null;
        unit: string | null;
        values: Record<string, number | null>;
        statusNote?: string | null;
      }>;
    };
    segmentPerformanceTable?: {
      period?: string | null;
      basis?: string | null;
      rows?: Array<{ segmentName: string; metricValue: number | null; unit: string | null; isNegative: boolean }>;
    };
  } | null;
  limitationsZhTw: string[];
};

export type CompanyResearchV4Resource = {
  source: "api" | "unavailable";
  data: CompanyResearchV4 | null;
  error: string | null;
};

export type StockHistoryResource = {
  source: "api" | "unavailable";
  data: StockHistoryRead | null;
  error: string | null;
  state: "UNAVAILABLE" | "ERROR" | null;
};

export type StockApiMainTopic = {
  name: string;
  grade?: string | null;
  state?: string | null;
  lifecycle?: string | null;
} | null;

export type StockApiItem = Omit<FormalStockRead, "topicRelations" | "historyCoverage" | "mainTopic"> & {
  topicRelations: StockApiRelation[];
  historyCoverage: Record<string, unknown>;
  mainTopic: StockApiMainTopic;
};

export type StockApiResource = {
  source: StockApiSource;
  data: StockApiItem[] | null;
  total: number;
  error: string | null;
  universe: Record<string, number>;
};

export function getFormalApiBaseUrl(): string | null {
  const runtime = typeof document !== "undefined"
    ? document.documentElement.dataset.apiBaseUrl?.trim()
    : "";
  const configured = runtime || process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "";
  return configured ? configured.replace(/\/+$/, "") : null;
}

export function hasFormalApiBaseUrl(): boolean {
  return getFormalApiBaseUrl() !== null;
}

function normalizeStock(item: FormalStockRead): StockApiItem {
  const topic = item.mainTopic;
  return {
    ...item,
    topicRelations: item.topicRelations ?? [],
    historyCoverage: item.historyCoverage ?? {},
    mainTopic: topic && typeof topic.name === "string"
      ? {
          name: topic.name,
          grade: typeof topic.grade === "string" ? topic.grade : null,
          state: typeof topic.state === "string" ? topic.state : null,
          lifecycle: typeof topic.lifecycle === "string" ? topic.lifecycle : null,
        }
      : null,
  };
}

function unavailable(error: string): StockApiResource {
  return { source: "unavailable", data: null, total: 0, error, universe: {} };
}

async function fetchStockPage(
  base: string,
  query: Record<string, string>,
  signal?: AbortSignal,
): Promise<FormalStockPage> {
  const params = new URLSearchParams(query);
  const response = await fetch(`${base}/api/v2/stocks?${params.toString()}`, {
    cache: "no-store",
    signal,
  });
  if (!response.ok) throw new Error(`FastAPI stock list returned HTTP ${response.status}`);
  return await response.json() as FormalStockPage;
}

export async function fetchFormalStocks(
  query: StockListQuery = {},
  options: { signal?: AbortSignal } = {},
): Promise<StockApiResource> {
  const base = getFormalApiBaseUrl();
  if (!base) {
    return {
      source: "synthetic-snapshot",
      data: null,
      total: 0,
      error: "Formal FastAPI origin is not configured; the page is running in explicit Preview mode.",
      universe: {},
    };
  }

  const params: Record<string, string> = {
    limit: "1000",
    offset: "0",
    sort: query.sort ?? "symbolAsc",
  };
  const normalizedSearch = query.search?.trim();
  if (normalizedSearch) params.search = normalizedSearch;
  if (query.market) params.market = query.market;
  if (query.topic) params.topic = query.topic;
  if (query.updateMode && query.updateMode !== "all") params.updateMode = query.updateMode;

  try {
    const first = await fetchStockPage(base, params, options.signal);
    const items = first.items.map(normalizeStock);
    let offset = items.length;
    while (offset < first.total) {
      const next = await fetchStockPage(base, { ...params, offset: String(offset) }, options.signal);
      if (!next.items.length) break;
      items.push(...next.items.map(normalizeStock));
      offset += next.items.length;
    }
    if (items.length < first.total) {
      return unavailable(`FastAPI stock list returned ${items.length}/${first.total} rows.`);
    }
    return {
      source: "api",
      data: items,
      total: first.total,
      error: null,
      universe: first.universe ?? {},
    };
  } catch (error) {
    if (options.signal?.aborted) return unavailable("Formal stock request was cancelled.");
    return unavailable(error instanceof Error ? error.message : "Formal stock request failed.");
  }
}

export async function fetchFormalStock(
  symbol: string,
): Promise<{ source: StockApiSource; data: StockApiItem | null; error: string | null }> {
  const base = getFormalApiBaseUrl();
  if (!base) {
    return {
      source: "synthetic-snapshot",
      data: null,
      error: "Formal FastAPI origin is not configured; the page is running in explicit Preview mode.",
    };
  }
  try {
    const response = await fetch(`${base}/api/v2/stocks/${encodeURIComponent(symbol)}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`FastAPI stock detail returned HTTP ${response.status}`);
    return { source: "api", data: normalizeStock(await response.json() as FormalStockRead), error: null };
  } catch (error) {
    return {
      source: "unavailable",
      data: null,
      error: error instanceof Error ? error.message : "Formal stock detail request failed.",
    };
  }
}

export async function fetchFormalCompanyResearchV4(
  symbol: string,
): Promise<CompanyResearchV4Resource> {
  const base = getFormalApiBaseUrl();
  if (!base) {
    return {
      source: "unavailable",
      data: null,
      error: "Formal FastAPI origin is not configured.",
    };
  }
  try {
    const response = await fetch(
      `${base}/api/v2/stocks/${encodeURIComponent(symbol)}/research-v4`,
      { cache: "no-store" },
    );
    if (!response.ok) throw new Error(`Company Research V4 returned HTTP ${response.status}`);
    return { source: "api", data: await response.json() as CompanyResearchV4, error: null };
  } catch (error) {
    return {
      source: "unavailable",
      data: null,
      error: error instanceof Error ? error.message : "Company Research V4 request failed.",
    };
  }
}

export async function fetchFormalStockHistory(
  symbol: string,
  options: { market?: string | null; signal?: AbortSignal } = {},
): Promise<StockHistoryResource> {
  const base = getFormalApiBaseUrl();
  if (!base) {
    return {
      source: "unavailable",
      data: null,
      error: "Formal FastAPI origin is not configured; historical price history is unavailable.",
      state: "UNAVAILABLE",
    };
  }

  const params = new URLSearchParams({
    from: "2000-01-01",
    to: "2100-01-01",
    limit: "200",
  });
  if (options.market) params.set("market", options.market);

  try {
    const response = await fetch(
      `${base}/api/v2/stocks/${encodeURIComponent(symbol)}/price-history?${params.toString()}`,
      { cache: "no-store", signal: options.signal },
    );
    if (!response.ok) throw new Error(`FastAPI stock price history returned HTTP ${response.status}`);
    return {
      source: "api",
      data: await response.json() as StockHistoryRead,
      error: null,
      state: null,
    };
  } catch (error) {
    return {
      source: "unavailable",
      data: null,
      error: error instanceof Error ? error.message : "Formal stock price history request failed.",
      state: "ERROR",
    };
  }
}
