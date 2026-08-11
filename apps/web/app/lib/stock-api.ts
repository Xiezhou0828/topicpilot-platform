import type { components } from "./generated-api";

export type StockApiSource = "api" | "synthetic-snapshot" | "unavailable";

type FormalStockRead = components["schemas"]["StockReadModel"];
type FormalStockPage = components["schemas"]["StockReadModelPage"];

export type StockApiRelation = components["schemas"]["StockTopicRelationRead"];

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
  return { source: "unavailable", data: null, error, universe: {} };
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
  query: {
    market?: string;
    topic?: string;
    updateMode?: string;
    sort?: string;
  } = {},
  options: { signal?: AbortSignal } = {},
): Promise<StockApiResource> {
  const base = getFormalApiBaseUrl();
  if (!base) {
    return {
      source: "synthetic-snapshot",
      data: null,
      error: "Formal FastAPI origin is not configured; the page is running in explicit Preview mode.",
      universe: {},
    };
  }

  const params: Record<string, string> = {
    limit: "1000",
    offset: "0",
    sort: query.sort ?? "symbolAsc",
  };
  if (query.market && query.market !== "all") params.market = query.market;
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
