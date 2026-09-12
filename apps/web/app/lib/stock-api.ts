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
export type StockTechnicalRead = components["schemas"]["StockTechnicalPublicationRead"];
export type StockTechnicalEvidence = components["schemas"]["TechnicalEvidence"];

export type StockHistoryResource = {
  source: "api" | "unavailable";
  data: StockHistoryRead | null;
  error: string | null;
  state: "UNAVAILABLE" | "ERROR" | null;
};

export type StockTechnicalState =
  | "AVAILABLE"
  | "PARTIAL"
  | "EMPTY"
  | "UNAVAILABLE"
  | "ERROR";

export type StockTechnicalResource = {
  source: "api" | "unavailable";
  data: StockTechnicalRead | null;
  error: string | null;
  state: StockTechnicalState;
};

export const FORMAL_TECHNICAL_INDICATOR_IDS = [
  "MA5",
  "MA10",
  "MA20",
  "MA60",
  "DISTANCE_TO_MA20",
  "RAW_CLOSE_RETURN_5D",
  "RAW_CLOSE_RETURN_20D",
  "VOLUME_MA5",
  "VOLUME_MA20",
  "VOLUME_RATIO_20",
  "RSI14",
  "MACD_12_26_9",
  "MACD_SIGNAL_12_26_9",
  "MACD_HISTOGRAM_12_26_9",
] as const;

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

export type StockDetailResource = {
  source: "api" | "unavailable";
  data: StockApiItem | null;
  error: string | null;
  state: "PUBLISHED" | "EMPTY" | "UNAVAILABLE" | "ERROR";
};

export async function fetchFormalStock(
  symbol: string,
  options: { market?: string | null; signal?: AbortSignal } = {},
): Promise<StockDetailResource> {
  if (!getFormalApiBaseUrl()) return {
    source: "unavailable", data: null, state: "UNAVAILABLE",
    error: "正式股票資料尚未連線。",
  };
  if (options.market && !["TPE", "TWO"].includes(options.market)) return {
    source: "unavailable", data: null, state: "UNAVAILABLE", error: "不支援的市場識別。",
  };
  // The existing symbol-only detail endpoint picks the first market. Resolve
  // exact identity from the same formal list projection instead of guessing.
  const result = await fetchFormalStocks({ search: symbol, market: options.market ?? undefined }, options);
  if (result.source !== "api" || !result.data) return {
    source: "unavailable", data: null, state: "ERROR", error: "正式股票資料讀取失敗，請重試。",
  };
  const matches = result.data.filter((item) => item.code === symbol && (!options.market || item.market === options.market));
  if (matches.length !== 1) return {
    source: "unavailable", data: null, state: matches.length ? "UNAVAILABLE" : "EMPTY",
    error: matches.length ? "股票代碼屬於多個市場，請指定 TPE 或 TWO。" : "找不到此市場與代碼的正式股票資料。",
  };
  return { source: "api", data: matches[0], error: null, state: "PUBLISHED" };
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
    const data = await response.json() as StockHistoryRead;
    if (data.code !== symbol || (options.market && data.market !== options.market)) {
      throw new Error("Historical price identity does not match the requested instrument.");
    }
    return {
      source: "api",
      data: data,
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

export function technicalPresentationState(data: StockTechnicalRead): StockTechnicalState {
  if (data.publicationStatus !== "AVAILABLE" && data.publicationStatus !== "AVAILABLE_WITH_LIMITATION") {
    return "UNAVAILABLE";
  }
  const session = data.provenance?.latestTradingDate ?? data.requestedTo;
  const evidence = data.technicalEvidence.filter((item) => item.sessionDate === session);
  const available = evidence.filter((item) =>
    (item.publicationState === "FORMAL" || item.publicationState === "FORMAL_WITH_LIMITATION")
    && item.value !== null
  );
  if (available.length === 0) return "EMPTY";
  if (
    data.publicationStatus === "AVAILABLE_WITH_LIMITATION"
    || available.length !== evidence.length
    || evidence.length !== FORMAL_TECHNICAL_INDICATOR_IDS.length
    || FORMAL_TECHNICAL_INDICATOR_IDS.some((indicatorId) =>
      !evidence.some((item) => item.indicatorId === indicatorId)
    )
    || evidence.some((item) => item.publicationState === "FORMAL_WITH_LIMITATION")
  ) return "PARTIAL";
  return "AVAILABLE";
}

export async function fetchFormalStockTechnical(
  symbol: string,
  options: { market?: string | null; sessionDate?: string | null; signal?: AbortSignal } = {},
): Promise<StockTechnicalResource> {
  const base = getFormalApiBaseUrl();
  if (!base || !options.market || !options.sessionDate) {
    return {
      source: "unavailable",
      data: null,
      error: !base
        ? "正式技術資料尚未連線。"
        : "正式技術證據需要明確市場與 EOD 交易日。",
      state: "UNAVAILABLE",
    };
  }
  if (!["TPE", "TWO"].includes(options.market) || !/^\d{4}-\d{2}-\d{2}$/.test(options.sessionDate)) {
    return { source: "unavailable", data: null, error: "技術證據的市場或交易日無效。", state: "UNAVAILABLE" };
  }

  const params = new URLSearchParams({
    from: "2000-01-01",
    to: options.sessionDate,
    market: options.market,
    limit: "200",
  });
  try {
    const response = await fetch(
      `${base}/api/v2/stocks/${encodeURIComponent(symbol)}/technical?${params.toString()}`,
      { cache: "no-store", signal: options.signal },
    );
    if (!response.ok) throw new Error(`FastAPI stock technical evidence returned HTTP ${response.status}`);
    const data = await response.json() as StockTechnicalRead;
    if (
      data.code !== symbol
      || data.market !== options.market
      || data.requestedTo !== options.sessionDate
      || data.calculationOwner !== "BACKEND_ONLY"
      || data.browserCalculationAllowed !== "NO"
      || ((data.publicationStatus === "AVAILABLE" || data.publicationStatus === "AVAILABLE_WITH_LIMITATION")
        && data.provenance?.authority !== "V2_CANONICAL_OBSERVATION_CHAIN")
      || data.technicalEvidence.some((item) => item.symbol !== symbol || item.market !== options.market)
    ) {
      throw new Error("Technical evidence identity or authority does not match the requested instrument.");
    }
    return { source: "api", data, error: null, state: technicalPresentationState(data) };
  } catch (error) {
    if (options.signal?.aborted) {
      return { source: "unavailable", data: null, error: "正式技術資料讀取已取消。", state: "UNAVAILABLE" };
    }
    return {
      source: "unavailable",
      data: null,
      error: error instanceof Error ? error.message : "正式技術資料讀取失敗。",
      state: "ERROR",
    };
  }
}
