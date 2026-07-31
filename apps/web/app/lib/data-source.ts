// WEB-DATA-002 前端資料存取層（雙軌：snapshot 優先，缺則 fallback 到 data.ts mock）。
//
// 設計：
//   - 頁面「不直接 import ../data」，改呼叫 getHomeData() / getWatchlistData()。
//   - snapshot 來源為 build 時 bundle 的 app/lib/web_snapshot.json（由 tools/export_web_snapshot.py 產生、
//     並發布到 public/data/web_snapshot.json）。
//   - build-time snapshot 僅供 SSR 初始資料；runtime API 失敗時不得把舊資料當成 LIVE。
//   - 仍屬 mock 的區塊（題材 / 新聞 / 近觸發卡片）由本層 re-export，維持單一資料入口。
//   - FRONTEND-SNAPSHOT-API-001：前端走可注入的獨立 snapshot API；不依賴 Sites runtime binding。

import rawSnapshotJson from "./web_snapshot.json";
import {
  marketIndices as mockMarketIndices,
  news as mockNews,
  topics as mockTopics,
  watchlist as mockWatchlist,
  type NewsItem,
  type Topic,
  type WatchItem,
} from "../data";
import {
  buildHomeFromSnapshot,
  buildWatchlistFromSnapshot,
  isSnapshotUsable,
  toTopicGroupViews,
  toTopicViews,
  toFreshness,
  toQualityView,
  toStockUniverse,
  toTopicRelations,
  toTopicStrengthHistory,
  toMarketRadar,
  toMarketDecision,
  toStrategyCandidates,
  toStrategyPerformance,
  toStrategyRegistry,
} from "./snapshot-adapter";
import type {
  Freshness,
  HomeData,
  MarketIndexView,
  ObservationRow,
  QualityPanelData,
  RawSnapshot,
  SnapshotBundle,
  TopicView,
  TopicGroupView,
  WatchRow,
  WatchlistData,
} from "./types";

// 企業版保留原 UI，只把集中式資料入口切換到 FastAPI read model。
// NEXT_PUBLIC_SNAPSHOT_API_URL 保留向後相容；新部署建議設定 API base URL。
const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ?? "";
const configuredSnapshotApiUrl = process.env.NEXT_PUBLIC_SNAPSHOT_API_URL?.trim() ?? "";
export const DEMO_FALLBACK_ENABLED = process.env.NEXT_PUBLIC_ENABLE_DEMO_FALLBACK !== "false";

function snapshotEndpointFromBase(baseUrl: string): string {
  const trimmed = baseUrl.replace(/\/+$/, "");
  return trimmed.endsWith("/api/v1/snapshot/latest")
    ? trimmed
    : `${trimmed}/api/v1/snapshot/latest`;
}

export const PUBLISHED_SNAPSHOT_URL = configuredSnapshotApiUrl
  || (configuredApiBaseUrl ? snapshotEndpointFromBase(configuredApiBaseUrl) : null);

export function getSnapshotApiUrl(): string | null {
  const runtimeUrl = typeof document !== "undefined"
    ? document.documentElement.dataset.snapshotApiUrl?.trim()
    : null;
  return runtimeUrl || PUBLISHED_SNAPSHOT_URL;
}

let runtimeConfigPromise: Promise<string | null> | null = null;

export function loadSnapshotApiUrl(): Promise<string | null> {
  const configured = getSnapshotApiUrl();
  if (configured || typeof window === "undefined") return Promise.resolve(configured);
  if (!runtimeConfigPromise) {
    runtimeConfigPromise = fetch(`/snapshot-api.json?refresh=${Date.now()}`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) return null;
        const payload = (await response.json()) as { snapshotApiUrl?: unknown; apiBaseUrl?: unknown };
        const direct = typeof payload.snapshotApiUrl === "string" ? payload.snapshotApiUrl.trim() : "";
        const base = typeof payload.apiBaseUrl === "string" ? payload.apiBaseUrl.trim() : "";
        const value = direct || (base ? snapshotEndpointFromBase(base) : "");
        if (!isAbsoluteSnapshotApiUrl(value)) return null;
        document.documentElement.dataset.snapshotApiUrl = value;
        return value;
      })
      .catch(() => null);
  }
  return runtimeConfigPromise;
}

export type SnapshotApiErrorCode =
  | "API_URL_NOT_CONFIGURED"
  | "HTTP_ERROR"
  | "INVALID_JSON"
  | "INVALID_CONTRACT";

export class SnapshotApiError extends Error {
  readonly code: SnapshotApiErrorCode;
  readonly status: number | null;

  constructor(code: SnapshotApiErrorCode, message: string, status: number | null = null) {
    super(message);
    this.name = "SnapshotApiError";
    this.code = code;
    this.status = status;
  }
}

function isAbsoluteSnapshotApiUrl(value: string | null | undefined): value is string {
  if (!value) return false;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" || parsed.protocol === "http:";
  } catch {
    return false;
  }
}

async function resolveSnapshotApiUrl(url?: string | null): Promise<string> {
  const resolved = url?.trim() || await loadSnapshotApiUrl();
  if (!isAbsoluteSnapshotApiUrl(resolved)) {
    throw new SnapshotApiError(
      "API_URL_NOT_CONFIGURED",
      "尚未設定 FastAPI 資料服務，改用公開合成展示資料。",
    );
  }
  return resolved;
}

const rawSnapshot = rawSnapshotJson as unknown as RawSnapshot;
const SNAPSHOT_USABLE = isSnapshotUsable(rawSnapshot);

const MOCK_FRESHNESS: Freshness = {
  dataDate: "2026-07-12",
  generatedAt: null,
  completeness: "示範資料（mock）",
  note: "目前顯示的是內建示範資料，尚未接上後端 snapshot。",
  sourceLabel: "示範資料（mock）",
  priceAsOf: "2026-07-12",
  quoteUpdatedAt: null,
  quoteSource: null,
  quoteStatus: null,
  latestTradingDate: null,
  marketSession: null,
  marketSessionReason: null,
  technicalAsOf: "2026-07-12",
  institutionalAsOf: null,
  tdccAsOf: null,
  fundamentalYm: null,
  stale: false,
  staleReason: null,
};

function mockMarketIndexViews(): MarketIndexView[] {
  return mockMarketIndices.map((m) => ({
    name: m.name,
    value: m.value,
    change: m.change,
    stance: m.stance,
    pending: false,
    subLabel: null,
    asOf: null,
  }));
}

function mockWatchToObservation(item: WatchItem): ObservationRow {
  return {
    code: item.code,
    name: item.name,
    section: item.status,
    subType: item.setup,
    price: item.price,
    change: null,
    volume: null,
    volumeRatio: null,
    volumeStatus: null,
    trigger: item.trigger ?? null,
    triggerLabel: item.trigger != null ? String(item.trigger) : null,
    distance: item.distance ?? null,
    entryScore: null,
    gate: item.gate,
    fundingConfirm: item.foreignFlow > 0 ? `外資 +${item.foreignFlow.toFixed(1)}%` : null,
    fundamentalCatalyst: null,
    shortRisk: item.marginChange > 2 ? "融資偏熱" : null,
    watchDays: null,
    dataFreshness: null,
    updatedAt: null,
    topicRole: "主要",
    topicDefinition: "主要核心",
  };
}

function mockWatchToRow(item: WatchItem, i: number): WatchRow {
  const obs = mockWatchToObservation(item);
  return {
    ...obs,
    rank: item.rank ?? i + 1,
    topic: item.topic,
    support: null,
    supportLabel: null,
    resistance: null,
    resistanceLabel: null,
    invalidation: item.stop ?? null,
    invalidationLabel: item.stop != null ? String(item.stop) : null,
    stopPct: item.risk ?? null,
    gateReason: null,
    foreignFlow: item.foreignFlow,
    hasFunding: item.foreignFlow > 0,
    hasCatalyst: false,
    hasRisk: item.marginChange > 2,
  };
}

function buildHomeFromMock(): HomeData {
  const rows = mockWatchlist.map(mockWatchToObservation);
  const counts = new Map<string, number>();
  for (const r of rows) counts.set(r.section ?? "未分段", (counts.get(r.section ?? "未分段") ?? 0) + 1);
  return {
    source: "mock",
    freshness: MOCK_FRESHNESS,
    quality: null,
    marketIndices: mockMarketIndexViews(),
    observation: {
      total: rows.length,
      asOf: MOCK_FRESHNESS.dataDate,
      summary: Array.from(counts.entries()).map(([section, count]) => ({ section, count })),
      completenessNote: "示範資料（mock）",
    },
    preview: rows,
  };
}

function buildWatchlistFromMock(): WatchlistData {
  const rows = mockWatchlist.map(mockWatchToRow);
  const sections = Array.from(new Set(rows.map((r) => r.section ?? "未分段")));
  return {
    source: "mock",
    freshness: MOCK_FRESHNESS,
    quality: null,
    rows,
    sections,
  };
}

function buildTopicsFromMock(): TopicView[] {
  return mockTopics.map((topic) => ({
    name: topic.name,
    group: topic.group,
    type: "示範資料",
    grade: topic.grade,
    childGrade: topic.grade,
    strengthState: topic.signal,
    confidence: "示範資料",
    score: topic.score,
    strengthScore: topic.score,
    strengthSource: "mock",
    calculationStatus: "示範資料",
    breadth: topic.breadth,
    breadthRatio: null,
    stockCount: null,
    observedCount: null,
    strongCount: null,
    weakCount: null,
    signal: topic.signal,
    leaders: topic.leaders,
    relationCount: null,
    note: topic.note,
  }));
}

function buildTopicGroupsFromTopics(topics: TopicView[]): TopicGroupView[] {
  const groups = new Map<string, TopicView[]>();
  for (const topic of topics) {
    const group = topic.group ?? "未分類";
    groups.set(group, [...(groups.get(group) ?? []), topic]);
  }
  return Array.from(groups.entries()).map(([name, children]) => {
    const scored = children.filter((child) => child.strengthScore != null);
    const strongest = [...scored].sort((a, b) => (b.strengthScore ?? -Infinity) - (a.strengthScore ?? -Infinity))[0];
    const score = scored.length ? scored.reduce((sum, child) => sum + (child.strengthScore ?? 0), 0) / scored.length : null;
    return {
      name,
      score,
      strengthState: "細題材彙總觀察",
      childCount: children.length,
      scoredChildCount: scored.length,
      strongestChild: strongest?.name ?? null,
      strongestChildScore: strongest?.strengthScore ?? null,
      children: children.sort((a, b) => (b.strengthScore ?? -Infinity) - (a.strengthScore ?? -Infinity)).map((child) => child.name),
    };
  });
}

export function getHomeData(): HomeData {
  return SNAPSHOT_USABLE ? buildHomeFromSnapshot(rawSnapshot) : buildHomeFromMock();
}

export function getWatchlistData(): WatchlistData {
  return SNAPSHOT_USABLE ? buildWatchlistFromSnapshot(rawSnapshot) : buildWatchlistFromMock();
}

export function isUsingSnapshot(): boolean {
  return SNAPSHOT_USABLE;
}

// 目前（build 時 bundle 的 snapshot）資料品質，供品質面板初始顯示。
export function getQualityPanelData(): QualityPanelData {
  if (SNAPSHOT_USABLE) {
    return { source: "snapshot", freshness: toFreshness(rawSnapshot), quality: toQualityView(rawSnapshot) };
  }
  return { source: "mock", freshness: MOCK_FRESHNESS, quality: null };
}

// 相容品質面板的單次抓取入口；runtime API 失敗時回 null，不改動分數或 Gate。
export async function fetchPublishedSnapshot(
  url?: string | null,
): Promise<QualityPanelData | null> {
  try {
    const raw = await fetchRawPublishedSnapshot(url);
    if (!isSnapshotUsable(raw)) return null;
    return { source: "snapshot", freshness: toFreshness(raw), quality: toQualityView(raw) };
  } catch {
    return null;
  }
}

// TASK H：把「一份 raw snapshot」組成首頁 / 觀察清單 / 品質面板共用的整包資料。
function mockBundle(): SnapshotBundle {
  const topics = buildTopicsFromMock();
  return {
    source: "mock",
    homeData: buildHomeFromMock(),
    watchlistData: buildWatchlistFromMock(),
    qualityPanelData: { source: "mock", freshness: MOCK_FRESHNESS, quality: null },
    topics,
    topicGroups: buildTopicGroupsFromTopics(topics),
    stockUniverse: [],
    topicRelations: [],
    topicStrengthHistory: [],
    marketRadar: null,
    marketDecision: null,
    strategyRegistry: null,
    strategyCandidates: [],
    strategyPerformance: [],
  };
}

export function getUnavailableBundle(): SnapshotBundle {
  const freshness: Freshness = {
    dataDate: null,
    generatedAt: null,
    completeness: "目前沒有可用的 snapshot",
    note: "獨立 snapshot API 尚未提供可用資料。",
    sourceLabel: "獨立 snapshot API",
    priceAsOf: null,
    quoteUpdatedAt: null,
    quoteSource: null,
    quoteStatus: null,
    latestTradingDate: null,
    marketSession: null,
    marketSessionReason: null,
    technicalAsOf: null,
    institutionalAsOf: null,
    tdccAsOf: null,
    fundamentalYm: null,
    stale: false,
    staleReason: null,
  };
  const homeData: HomeData = {
    source: "snapshot",
    freshness,
    quality: null,
    marketIndices: [],
    observation: { total: 0, asOf: null, summary: [], completenessNote: "目前沒有可用的 snapshot" },
    preview: [],
  };
  const watchlistData: WatchlistData = {
    source: "snapshot",
    freshness,
    quality: null,
    rows: [],
    sections: [],
  };
  return {
    source: "snapshot",
    homeData,
    watchlistData,
    qualityPanelData: { source: "snapshot", freshness, quality: null },
    topics: [],
    topicGroups: [],
    stockUniverse: [],
    topicRelations: [],
    topicStrengthHistory: [],
    marketRadar: null,
    marketDecision: null,
    strategyRegistry: null,
    strategyCandidates: [],
    strategyPerformance: [],
  };
}

export function buildBundleFromRaw(raw: RawSnapshot): SnapshotBundle {
  if (!isSnapshotUsable(raw)) return mockBundle();
  const topics = toTopicViews(raw);
  return {
    source: "snapshot",
    homeData: buildHomeFromSnapshot(raw),
    watchlistData: buildWatchlistFromSnapshot(raw),
    qualityPanelData: { source: "snapshot", freshness: toFreshness(raw), quality: toQualityView(raw) },
    topics,
    topicGroups: toTopicGroupViews(raw).length ? toTopicGroupViews(raw) : buildTopicGroupsFromTopics(topics),
    stockUniverse: toStockUniverse(raw),
    topicRelations: toTopicRelations(raw),
    topicStrengthHistory: toTopicStrengthHistory(raw),
    marketRadar: toMarketRadar(raw),
    marketDecision: toMarketDecision(raw),
    strategyRegistry: toStrategyRegistry(raw),
    strategyCandidates: toStrategyCandidates(raw),
    strategyPerformance: toStrategyPerformance(raw),
  };
}

// build 時 bundle 的 snapshot 組出的初始整包資料（SSR / 首次載入 / fetch 失敗時的 fallback）。
export function getBundledBundle(): SnapshotBundle {
  return SNAPSHOT_USABLE ? buildBundleFromRaw(rawSnapshot) : mockBundle();
}

// 從 FastAPI 抓完整 raw snapshot。免費服務冷啟動時會有限次重試，
// 最終失敗再由 SnapshotProvider 切回公開合成資料。
export async function fetchRawPublishedSnapshot(
  url?: string | null,
  signal?: AbortSignal,
): Promise<RawSnapshot | null> {
  const apiUrl = await resolveSnapshotApiUrl(url);
  const separator = apiUrl.includes("?") ? "&" : "?";
  const requestUrl = `${apiUrl}${separator}refresh=${Date.now()}`;
  let res: Response | null = null;
  let lastError: unknown = null;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      res = await fetch(requestUrl, { cache: "no-store", signal });
      if (res.ok || res.status < 500) break;
      lastError = new SnapshotApiError("HTTP_ERROR", `FastAPI 回傳 HTTP ${res.status}。`, res.status);
    } catch (error) {
      lastError = error;
      if (signal?.aborted) throw error;
    }
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(resolve, attempt === 0 ? 2_000 : 5_000);
      signal?.addEventListener("abort", () => {
        clearTimeout(timer);
        reject(signal.reason);
      }, { once: true });
    });
  }

  if (!res) {
    throw lastError instanceof Error
      ? lastError
      : new SnapshotApiError("HTTP_ERROR", "FastAPI 暫時無法連線。");
  }
  if (!res.ok) {
    throw lastError instanceof SnapshotApiError
      ? lastError
      : new SnapshotApiError("HTTP_ERROR", `FastAPI 回傳 HTTP ${res.status}。`, res.status);
  }

  let raw: RawSnapshot;
  try {
    raw = (await res.json()) as RawSnapshot;
  } catch {
    throw new SnapshotApiError("INVALID_JSON", "FastAPI 回傳內容不是有效 JSON。");
  }

  if (!isSnapshotUsable(raw)) {
    throw new SnapshotApiError("INVALID_CONTRACT", "FastAPI 回傳資料不符合前端契約。");
  }
  return raw;
}

// 仍屬 mock 的 UI 區塊（題材訊號 / 題材新聞 / 近觸發卡片）— 由本層統一 re-export，
// 讓頁面維持「只從 data-source 取資料」。詳見 AI/WEB_DATA_GAP_MAP.md。
export const mockTopicsData: Topic[] = mockTopics;
export const mockNewsData: NewsItem[] = mockNews;
export const mockWatchlistData: WatchItem[] = mockWatchlist;
export type { NewsItem, Topic, WatchItem };
