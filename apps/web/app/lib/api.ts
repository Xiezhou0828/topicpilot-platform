import {
  mapDataStatus,
  mapStock,
  mapStrategy,
  mapTopic,
  nullableNumber,
  nullableString,
  readValue,
  unwrapItems,
} from "./mapping.mjs";
import type { components } from "./generated-api";
import type {
  ApiList,
  DataStatus,
  StockDetail,
  StockSummary,
  StrategyCandidate,
  StrategyKey,
  StrategyPerformance,
  StrategySummary,
  TopicDetail,
  TopicRotationItem,
  TopicSummary,
} from "./types";

const configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "") ?? "";

type WireDataStatus = components["schemas"]["DataStatus"];
type WireStockPage = components["schemas"]["Page_StockSummary_"];
type WireStockDetail = components["schemas"]["StockResponse"];
type WireTopicPage = components["schemas"]["Page_TopicSummary_"];
type WireTopicDetail = components["schemas"]["TopicResponse"];
type WireStrategyPage = components["schemas"]["Page_StrategyResponse_"];
type WireCandidatePage = components["schemas"]["Page_CandidateResponse_"];
type WireRotationPage = components["schemas"]["Page_TopicRotationResponse_"];
type WirePerformancePage = components["schemas"]["Page_StrategyPerformanceResponse_"];

export const demoFallbackEnabled = process.env.NEXT_PUBLIC_ENABLE_DEMO_FALLBACK === "true";

export class ApiProblem extends Error {
  status: number | null;
  detail: string;
  retryable: boolean;

  constructor(message: string, options: { status?: number | null; detail?: string; retryable?: boolean } = {}) {
    super(message);
    this.name = "ApiProblem";
    this.status = options.status ?? null;
    this.detail = options.detail ?? message;
    this.retryable = options.retryable ?? true;
  }
}

function record(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

async function requestJson<T = unknown>(path: string, signal?: AbortSignal): Promise<T> {
  if (!configuredBaseUrl) {
    throw new ApiProblem("尚未設定 FastAPI 位址。", {
      detail: "請設定 NEXT_PUBLIC_API_BASE_URL；正式環境不會自動以展示資料掩蓋 API 錯誤。",
      retryable: false,
    });
  }

  let response: Response;
  try {
    response = await fetch(`${configuredBaseUrl}${path}`, {
      signal,
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiProblem("無法連線至資料 API。", {
      detail: "免費展示服務可能正在冷啟動，通常需要約一分鐘。請稍候後重試。",
    });
  }

  if (!response.ok) {
    let body: Record<string, unknown> = {};
    try { body = record(await response.json()); } catch { /* non-JSON problem response */ }
    const detail = nullableString(readValue(body, "detail", "message", "title"));
    throw new ApiProblem(response.status >= 500 ? "資料服務暫時無法使用。" : "資料請求未完成。", {
      status: response.status,
      detail: detail ?? (response.status >= 500
        ? "服務可能正在冷啟動或維護中，請稍候後重試。"
        : `FastAPI 回傳 HTTP ${response.status}。`),
      retryable: response.status === 408 || response.status === 429 || response.status >= 500,
    });
  }

  return response.json() as Promise<T>;
}

function paged<T>(payload: unknown, mapper: (raw: Record<string, unknown>) => T): ApiList<T> {
  const source = record(payload);
  const nested = record(source.data);
  const items = unwrapItems(payload).map((item) => mapper(record(item)));
  return {
    items,
    total: nullableNumber(readValue(source, "total", "count") ?? readValue(nested, "total", "count")) ?? items.length,
    limit: nullableNumber(readValue(source, "limit") ?? readValue(nested, "limit")) ?? items.length,
    offset: nullableNumber(readValue(source, "offset") ?? readValue(nested, "offset")) ?? 0,
  };
}

function booleanOrNull(value: unknown): boolean | null {
  if (typeof value === "boolean") return value;
  if (value === 1 || value === "1" || value === "true") return true;
  if (value === 0 || value === "0" || value === "false") return false;
  return null;
}

function mapStockDetail(payload: unknown): StockDetail {
  const outer = record(payload);
  const raw = record(Object.keys(record(outer.data)).length ? outer.data : outer);
  const summary = mapStock(raw);
  const technical = record(readValue(raw, "technical", "technical_snapshot"));
  const fundamental = record(readValue(raw, "fundamental", "fundamental_snapshot"));
  const notes = readValue(raw, "qualityNotes", "quality_notes");
  const price = nullableNumber(readValue(raw, "price", "close_price", "close"));
  const ma20 = nullableNumber(readValue(raw, "ma20", "MA20"));
  return {
    ...summary,
    description: nullableString(readValue(raw, "description", "profile")),
    technical: {
      trend: nullableString(readValue(technical, "trend", "trend_state") ?? readValue(raw, "technicalState", "technical_state")),
      aboveMa20: booleanOrNull(readValue(technical, "aboveMa20", "above_ma20") ?? (price !== null && ma20 !== null ? price > ma20 : null)),
      relativeStrength20: nullableNumber(readValue(technical, "relativeStrength20", "relative_strength_20", "rs20") ?? readValue(raw, "rs20")),
      volatility20: nullableNumber(readValue(technical, "volatility20", "volatility_20")),
    },
    fundamental: {
      revenueYoy: nullableNumber(readValue(fundamental, "revenueYoy", "revenue_yoy")),
      revenueMom: nullableNumber(readValue(fundamental, "revenueMom", "revenue_mom")),
      grossMargin: nullableNumber(readValue(fundamental, "grossMargin", "gross_margin")),
    },
    qualityNotes: Array.isArray(notes) ? notes.map(nullableString).filter((item): item is string => item !== null) : [],
  };
}

function mapTopicDetail(payload: unknown): TopicDetail {
  const outer = record(payload);
  const raw = record(Object.keys(record(outer.data)).length ? outer.data : outer);
  const summary = mapTopic(raw);
  const trendRaw = readValue(raw, "trend", "history", "strength_history");
  const stocksRaw = readValue(raw, "stocks", "members", "constituents");
  return {
    ...summary,
    description: nullableString(readValue(raw, "description", "note")),
    trend: Array.isArray(trendRaw) ? trendRaw.map((item) => {
      const point = record(item);
      return {
        date: nullableString(readValue(point, "date", "data_date")) ?? "",
        score: nullableNumber(readValue(point, "score", "strength_score")),
      };
    }).filter((point) => point.date) : [],
    stocks: Array.isArray(stocksRaw) ? stocksRaw.map((item) => mapStock(record(item))) : [],
  };
}

function mapCandidate(raw: Record<string, unknown>): StrategyCandidate {
  return {
    strategyKey: (nullableString(readValue(raw, "strategyKey", "strategy_key", "strategyId", "strategy_id")) ?? "MAS") as StrategyKey,
    rank: nullableNumber(readValue(raw, "rank")),
    code: nullableString(readValue(raw, "code", "stock_code")) ?? "UNKNOWN",
    name: nullableString(readValue(raw, "name", "stock_name")) ?? "未命名標的",
    score: nullableNumber(readValue(raw, "score")),
    price: nullableNumber(readValue(raw, "price", "close_price")),
    topic: nullableString(readValue(raw, "topic", "fine_topic")),
    reason: nullableString(readValue(raw, "reason", "summary")),
    dataDate: nullableString(readValue(raw, "dataDate", "data_date")),
  };
}

function mapPerformance(raw: Record<string, unknown>): StrategyPerformance {
  return {
    strategyKey: (nullableString(readValue(raw, "strategyKey", "strategy_key", "strategyId", "strategy_id")) ?? "MAS") as StrategyKey,
    horizon: nullableString(readValue(raw, "horizon")) ?? "—",
    sampleCount: nullableNumber(readValue(raw, "sampleCount", "sample_count")),
    returnPct: nullableNumber(readValue(raw, "returnPct", "return_pct", "averageReturnPct", "average_return_pct")),
    winRatePct: nullableNumber(readValue(raw, "winRatePct", "win_rate_pct")),
  };
}

export const api = {
  async getDataStatus(signal?: AbortSignal): Promise<DataStatus> {
    return mapDataStatus(record(await requestJson<WireDataStatus>("/api/v1/meta/data-status", signal)));
  },
  async getLatestSnapshot(signal?: AbortSignal): Promise<Record<string, unknown>> {
    return record(await requestJson<components["schemas"]["SnapshotResponse"]>("/api/v1/snapshot/latest", signal));
  },
  async getStocks(signal?: AbortSignal): Promise<ApiList<StockSummary>> {
    return paged(await requestJson<WireStockPage>("/api/v1/stocks?limit=100&offset=0", signal), mapStock);
  },
  async getStock(code: string, signal?: AbortSignal): Promise<StockDetail> {
    return mapStockDetail(await requestJson<WireStockDetail>(`/api/v1/stocks/${encodeURIComponent(code)}`, signal));
  },
  async getTopics(signal?: AbortSignal): Promise<ApiList<TopicSummary>> {
    return paged(await requestJson<WireTopicPage>("/api/v1/topics?limit=100&offset=0", signal), mapTopic);
  },
  async getTopic(slug: string, signal?: AbortSignal): Promise<TopicDetail> {
    return mapTopicDetail(await requestJson<WireTopicDetail>(`/api/v1/topics/${encodeURIComponent(slug)}`, signal));
  },
  async getStrategies(signal?: AbortSignal): Promise<StrategySummary[]> {
    return unwrapItems(await requestJson<WireStrategyPage>("/api/v1/strategies", signal)).map((item) => mapStrategy(record(item))) as StrategySummary[];
  },
  async getStrategyCandidates(key: StrategyKey, signal?: AbortSignal): Promise<StrategyCandidate[]> {
    return unwrapItems(await requestJson<WireCandidatePage>(`/api/v1/strategies/${key}/candidates?limit=50&offset=0`, signal)).map((item) => mapCandidate(record(item)));
  },
  async getTopicRotation(signal?: AbortSignal): Promise<TopicRotationItem[]> {
    return unwrapItems(await requestJson<WireRotationPage>("/api/v1/analytics/topic-rotation?days=14", signal)).map((item) => {
      const raw = record(item);
      const mapped = mapTopic(raw);
      const direction = nullableString(readValue(raw, "direction"));
      const inferredDirection = mapped.change14d === null || mapped.change14d === 0
        ? "steady"
        : mapped.change14d > 0 ? "warming" : "cooling";
      return { ...mapped, direction: direction === "warming" || direction === "cooling" ? direction : inferredDirection };
    });
  },
  async getStrategyPerformance(signal?: AbortSignal): Promise<StrategyPerformance[]> {
    return unwrapItems(await requestJson<WirePerformancePage>("/api/v1/analytics/strategy-performance", signal)).map((item) => mapPerformance(record(item)));
  },
};
