import rawSnapshotJson from "./web_snapshot.json";
import type { RawSnapshot, RawStock, RawTopic } from "./types";
import { getPreviewTopicIdentities, getPreviewTopicIdentity, getPreviewTopicRotation, groupNameLabel, PREVIEW_LABEL, readableFreshness, readableTopicState, topicNameLabel, type TopicDirection, type TopicRotationEvent } from "./topic-preview";

export type TopicSource = "api" | "synthetic-snapshot" | "unavailable";

export type TopicSummary = {
  slug: string;
  name: string;
  groupName: string | null;
  topicType: string;
  enabled: boolean;
  dataDate: string | null;
  score: number | null;
  grade: string | null;
  strengthState: string | null;
  readableState: string;
  coveragePct: number | null;
  constituentCount: number;
};

export type TopicConstituent = {
  code: string;
  name: string;
  relationType: string;
  role: "代表股" | "核心股" | "關聯股";
  weight: number | null;
  price: number | null;
  changePct: number | null;
  dataDate: string | null;
  dataFreshness: string | null;
};

export type TopicDetail = TopicSummary & {
  constituents: TopicConstituent[];
};

export type TopicResource<T> = {
  source: TopicSource;
  data: T | null;
  error: string | null;
};

export type TopicRotationResource = TopicResource<TopicRotationEvent[]>;

type ApiTopicSummary = Omit<TopicSummary, "readableState"> & { readableState?: never };
type ApiTopicDetail = Omit<TopicDetail, "readableState" | "constituents"> & {
  constituents: Array<{
    code: string;
    name: string;
    relationType: string;
    weight: number | null;
  }>;
};

type ApiTopicRotation = {
  change: number | null;
  days: number;
  groupName: string | null;
  latestCoveragePct: number | null;
  latestDate: string;
  latestGrade: string | null;
  latestScore: number | null;
  latestStrengthState: string | null;
  pointCount: number;
  topicName: string;
  topicSlug: string;
};

type SyntheticRelation = {
  stockCode: string;
  stockName: string;
  topicSlug: string;
  relationType: string;
  weight: number | null;
};

const ROLE_LABELS: Record<string, "代表股" | "核心股" | "關聯股"> = {
  PRIMARY: "代表股",
  REPRESENTATIVE: "代表股",
  LEADER: "代表股",
  SECONDARY: "核心股",
  CORE: "核心股",
  RELATED: "關聯股",
};

function apiBaseUrl(): string | null {
  const runtime = typeof document !== "undefined"
    ? document.documentElement.dataset.apiBaseUrl?.trim()
    : "";
  const configured = runtime || process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "";
  return configured ? configured.replace(/\/+$/, "") : null;
}

function readableState(value: string | null | undefined): string {
  return readableTopicState(value);
}

function roleFor(value: string | null | undefined): "代表股" | "核心股" | "關聯股" {
  return ROLE_LABELS[(value ?? "").trim().toUpperCase()] ?? "關聯股";
}

function summaryFromApi(item: ApiTopicSummary): TopicSummary {
  return {
    ...item,
    name: topicNameLabel(item.slug, item.name),
    groupName: groupNameLabel(item.groupName),
    readableState: readableState(item.strengthState),
  };
}

function rawTopicSlug(topic: RawTopic): string | null {
  const value = (topic as RawTopic & { slug?: unknown }).slug;
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function rawTopicSummary(topic: RawTopic): TopicSummary | null {
  const slug = rawTopicSlug(topic);
  if (!slug) return null;
  return {
    slug,
    name: topicNameLabel(slug, topic.name),
    groupName: groupNameLabel(topic.group ?? null),
    topicType: topic.type ?? "UNKNOWN",
    enabled: true,
    dataDate: null,
    score: topic.strengthScore ?? topic.score ?? null,
    grade: topic.grade ?? null,
    strengthState: topic.strengthState ?? null,
    readableState: readableState(topic.strengthState),
    coveragePct: topic.breadthRatio ?? null,
    constituentCount: topic.stockCount ?? 0,
  };
}

function snapshot(): RawSnapshot {
  return rawSnapshotJson as unknown as RawSnapshot;
}

function syntheticTopics(): TopicSummary[] {
  const snapshotTopics = (snapshot().topics ?? [])
    .map(rawTopicSummary)
    .filter((item): item is TopicSummary => item !== null);
  const known = new Set(snapshotTopics.map((item) => item.slug));
  const previewTopics = getPreviewTopicIdentities()
    .filter(([slug]) => !known.has(slug))
    .map(([slug, item]) => ({
      slug,
      name: item.name,
      groupName: item.groupName,
      topicType: "PREVIEW",
      enabled: true,
      dataDate: null,
      score: item.score,
      grade: item.grade,
      strengthState: item.state,
      readableState: item.state,
      coveragePct: null,
      constituentCount: item.constituents.length,
    }));
  return [...snapshotTopics, ...previewTopics];
}

function syntheticDetail(slug: string): TopicDetail | null {
  const raw = snapshot();
  const summary = syntheticTopics().find((item) => item.slug === slug);
  if (!summary) return null;
  const relations = (raw.topicRelations ?? []) as unknown as SyntheticRelation[];
  const stocks = raw.stocks ?? {};
  const previewIdentity = getPreviewTopicIdentity(slug);
  if (previewIdentity) {
    return {
      ...summary,
      constituents: previewIdentity.constituents.map((item) => ({
        ...item,
        role: roleFor(item.relationType),
        dataDate: null,
        dataFreshness: "Preview",
      })),
    };
  }
  return {
    ...summary,
    constituents: relations.filter((item) => item.topicSlug === slug).map((item) => {
      const stock = stocks[item.stockCode] as RawStock | undefined;
      const price = stock?.price ?? {};
      return {
        code: item.stockCode,
        name: item.stockName,
        relationType: item.relationType,
        role: roleFor(item.relationType),
        weight: item.weight ?? null,
        price: typeof price.close === "number" ? price.close : null,
        changePct: typeof price.changePct === "number" ? price.changePct : null,
        dataDate: typeof price.dataDate === "string" ? price.dataDate : null,
        dataFreshness: readableFreshness(stock?.risk?.dataFreshness ?? null),
      };
    }),
  };
}

async function request<T>(path: string): Promise<TopicResource<T>> {
  const base = apiBaseUrl();
  if (!base) {
    return { source: "unavailable", data: null, error: "尚未設定 FastAPI API origin。" };
  }
  try {
    const response = await fetch(`${base}${path}`, { cache: "no-store" });
    if (!response.ok) {
      return { source: "unavailable", data: null, error: `FastAPI 回應 ${response.status}。` };
    }
    return { source: "api", data: await response.json() as T, error: null };
  } catch {
    return { source: "unavailable", data: null, error: "FastAPI 目前無法連線。" };
  }
}

export async function fetchTopics(): Promise<TopicResource<TopicSummary[]>> {
  const base = apiBaseUrl();
  if (!base) {
    const data = syntheticTopics();
    return data.length
      ? { source: "synthetic-snapshot", data, error: null }
      : { source: "unavailable", data: null, error: "尚未設定 FastAPI API origin。" };
  }
  const result = await request<{ items: ApiTopicSummary[] }>("/api/v1/topics?limit=200&offset=0");
  return result.source === "api"
    ? { source: "api", data: (result.data?.items ?? []).map(summaryFromApi), error: null }
    : { source: result.source, data: null, error: result.error };
}

export async function fetchTopic(slug: string): Promise<TopicResource<TopicDetail>> {
  const base = apiBaseUrl();
  if (!base) {
    const data = syntheticDetail(slug);
    return data
      ? { source: "synthetic-snapshot", data, error: null }
      : { source: "unavailable", data: null, error: "此 slug 不在公開合成 snapshot，且尚未設定 FastAPI API origin。" };
  }
  const result = await request<ApiTopicDetail>(`/api/v1/topics/${encodeURIComponent(slug)}`);
  if (result.source !== "api" || !result.data) return { source: result.source, data: null, error: result.error };
  const detail = result.data;
  return {
    source: "api",
    error: null,
    data: {
      ...detail,
      name: topicNameLabel(detail.slug, detail.name),
      groupName: groupNameLabel(detail.groupName),
      readableState: readableState(detail.strengthState),
      constituents: detail.constituents.map((item) => ({
        ...item,
        role: roleFor(item.relationType),
        price: null,
        changePct: null,
        dataDate: detail.dataDate,
        dataFreshness: null,
      })),
    },
  };
}

export function roleRank(role: TopicConstituent["role"]): number {
  return role === "代表股" ? 0 : role === "核心股" ? 1 : 2;
}

export function scoreLabel(score: number | null): string {
  return score === null ? "—" : Number.isInteger(score) ? String(score) : score.toFixed(1);
}

export function sourceLabel(source: TopicSource): string {
  return source === "api" ? "正式 API" : source === "synthetic-snapshot" ? PREVIEW_LABEL : "資料來源未連線";
}

function rotationDirection(change: number | null, strengthState: string | null): TopicDirection {
  if (change !== null) return change > 0 ? "up" : change < 0 ? "down" : "flat";
  const state = (strengthState ?? "").toUpperCase();
  return /WARM|HEAT|ACTIVE|BROAD|MAINLINE/.test(state) ? "up" : /COOL|WEAK|DIVERG/.test(state) ? "down" : "flat";
}

function rotationAction(item: ApiTopicRotation): string {
  if (item.change === null) return "輪動狀態待確認";
  if (item.change > 0) return "強度上升";
  if (item.change < 0) return "強度下降";
  return "維持盤整";
}

function rotationFromApi(item: ApiTopicRotation): TopicRotationEvent {
  const direction = rotationDirection(item.change, item.latestStrengthState);
  const toGrade = item.latestGrade === "S" || item.latestGrade === "A" || item.latestGrade === "B" || item.latestGrade === "D" ? item.latestGrade : null;
  return {
    id: `api-rotation-${item.topicSlug}-${item.latestDate}`,
    occurredAt: item.latestDate,
    timeLabel: item.latestDate,
    topicSlug: item.topicSlug,
    topicName: topicNameLabel(item.topicSlug, item.topicName),
    action: rotationAction(item),
    detail: `${toGrade ? `目前 ${toGrade} 級` : "正式輪動摘要"} · ${item.pointCount} 個觀測點`,
    direction,
    fromGrade: null,
    toGrade,
    source: "api",
  };
}

export async function fetchTopicRotation(): Promise<TopicRotationResource> {
  const base = apiBaseUrl();
  if (!base) return { source: "synthetic-snapshot", data: getPreviewTopicRotation(), error: null };
  const result = await request<{ items: ApiTopicRotation[] }>("/api/v1/analytics/topic-rotation?days=14&limit=100&offset=0");
  if (result.source === "api" && result.data?.items?.length) {
    const data = result.data.items.map(rotationFromApi).sort((a, b) => b.occurredAt.localeCompare(a.occurredAt));
    return { source: "api", data, error: null };
  }
  return { source: "synthetic-snapshot", data: getPreviewTopicRotation(), error: result.error ?? "正式輪動 read model 尚未提供完整事件欄位。" };
}
