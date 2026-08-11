export type StockApiSource = "api" | "synthetic-snapshot" | "unavailable";

export type StockApiRelation = {
  topicId: string;
  topicSlug: string;
  topicName: string;
  topicRole: "代表股" | "核心股" | "關聯股" | null;
  relationType: string;
  relationWeight: number | null;
};

export type StockApiItem = {
  instrumentId: string;
  symbol: string;
  code: string;
  name: string | null;
  market: "TPE" | "TWO";
  exchange: string | null;
  listing: string | null;
  active: boolean;
  enabled: boolean;
  price: number | null;
  changePct: number | null;
  volume: number | null;
  observedAt: string | null;
  retrievedAt: string | null;
  dataFreshness: "盤中更新" | "盤後更新" | "資料待更新";
  updateMode: "INTRADAY" | "POST_CLOSE" | "UNKNOWN";
  marketStatus: string;
  mainTopic: { slug?: string; name: string; grade?: string | null; state?: string | null } | null;
  topicRelations: StockApiRelation[];
  trackingMode: string;
  trackingReason: string | null;
  ma20State: string | null;
  ma60State: string | null;
  historyCoverage: Record<string, unknown>;
  favorite: Record<string, unknown> | null;
  opportunity: Record<string, unknown> | null;
  technicalEvidence: {
    above20MA: boolean | null;
    above60MA: boolean | null;
    ma20: number | null;
    ma60: number | null;
    breakoutState: string | null;
    technicalState: string | null;
  } | null;
  institutionFlows: Record<string, unknown> | null;
  summary: string | null;
};

export type StockApiResource = {
  source: StockApiSource;
  data: StockApiItem[] | null;
  error: string | null;
  universe: Record<string, number>;
};

function apiBaseUrl(): string | null {
  const runtime = typeof document !== "undefined"
    ? document.documentElement.dataset.apiBaseUrl?.trim()
    : "";
  const configured = runtime || process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "";
  return configured ? configured.replace(/\/+$/, "") : null;
}

export async function fetchFormalStocks(query: {
  market?: string;
  topic?: string;
  updateMode?: string;
  sort?: string;
} = {}): Promise<StockApiResource> {
  const base = apiBaseUrl();
  if (!base) {
    return {
      source: "synthetic-snapshot",
      data: null,
      error: "尚未設定 FastAPI API origin。",
      universe: {},
    };
  }
  const params = new URLSearchParams({ limit: "1000", sort: query.sort ?? "symbolAsc" });
  if (query.market && query.market !== "all") params.set("market", query.market);
  if (query.topic) params.set("topic", query.topic);
  if (query.updateMode && query.updateMode !== "all") params.set("updateMode", query.updateMode);
  try {
    const response = await fetch(`${base}/api/v2/stocks?${params.toString()}`, { cache: "no-store" });
    if (!response.ok) return { source: "unavailable", data: null, error: `FastAPI 回應 ${response.status}。`, universe: {} };
    const payload = await response.json() as { items?: StockApiItem[]; universe?: Record<string, number> };
    return { source: "api", data: payload.items ?? [], error: null, universe: payload.universe ?? {} };
  } catch {
    return { source: "unavailable", data: null, error: "FastAPI 目前無法連線。", universe: {} };
  }
}

export async function fetchFormalStock(symbol: string): Promise<{ source: StockApiSource; data: StockApiItem | null; error: string | null }> {
  const base = apiBaseUrl();
  if (!base) return { source: "synthetic-snapshot", data: null, error: "尚未設定 FastAPI API origin。" };
  try {
    const response = await fetch(`${base}/api/v2/stocks/${encodeURIComponent(symbol)}`, { cache: "no-store" });
    if (!response.ok) return { source: "unavailable", data: null, error: `FastAPI 回應 ${response.status}。` };
    return { source: "api", data: await response.json() as StockApiItem, error: null };
  } catch {
    return { source: "unavailable", data: null, error: "FastAPI 目前無法連線。" };
  }
}

