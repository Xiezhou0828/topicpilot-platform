import rawSnapshotJson from "./web_snapshot.json";
import type { RawSnapshot, RawStock, RawTopic } from "./types";
import type { components } from "./generated-api";
import type { LifecycleAvailability } from "./topic-lifecycle-contract";
import { getPreviewTopicIdentities, getPreviewTopicIdentity, getPreviewTopicRotation, groupNameLabel, PREVIEW_LABEL, readableFreshness, readableTopicState, topicNameLabel, type TopicDirection, type TopicRotationEvent } from "./topic-preview";

export type TopicSource = "api" | "synthetic-snapshot" | "unavailable";

export type TopicKind = "PARENT" | "LEAF";
export type TopicHierarchyNode = components["schemas"]["TopicHierarchyNodeRead"];
export type TopicHierarchy = Omit<components["schemas"]["TopicHierarchyRead"], "parents" | "children"> & {
  parents: TopicHierarchyNode[];
  children: TopicHierarchyNode[];
};
export type TopicCatalogNode = components["schemas"]["TopicMinimumRead"];
export type TopicCatalogPage = components["schemas"]["TopicMinimumReadPage"];
export type TopicAvailabilityState = components["schemas"]["TopicAvailabilityRead"]["state"];

export type TopicPublicationState = "FORMAL" | "FORMAL_NOT_WIRED" | "SHADOW" | "TEMPORARY" | "PREVIEW" | "DEFERRED" | "UNAVAILABLE" | "NOT_APPLICABLE" | "CONTRACT_GAP";

export type TopicPublicationField =
  | "identity"
  | "hierarchy"
  | "relations"
  | "score"
  | "grade"
  | "snapshot"
  | "participation"
  | "lifecycle"
  | "leaderCore"
  | "technicalRelative"
  | "events"
  | "news"
  | "heatmap"
  | "summary"
  | "opportunity"
  | "source";

export type TopicPublicationDisclosure = {
  field: TopicPublicationField;
  state: TopicPublicationState;
  note: string;
};

export type TopicPublication = Record<TopicPublicationField, TopicPublicationDisclosure>;

export type TopicLeafState = {
  topicId: string;
  slug: string;
  dataDate: string | null;
  score: number | null;
  grade: string | null;
  direction: string | null;
  strengthState: string | null;
  readableState: string;
  coveragePct: number | null;
  constituentCount: number;
  status: TopicStatus[];
  lifecycle: TopicLifecycle;
  publication?: Record<string, unknown>;
  quality?: Record<string, unknown>;
  lineage?: Record<string, unknown>;
};

export type TopicSummary = {
  topicId: string;
  slug: string;
  name: string;
  kind: TopicKind;
  hierarchy: TopicHierarchy;
  /** Canonical identity payload. Null only for explicitly enabled local Preview data. */
  catalog: TopicCatalogNode | null;
  leafState: TopicLeafState | null;
  snapshotAvailability: TopicAvailabilityState;
  snapshotAvailabilityReason: string | null;
  groupName: string | null;
  topicType: string;
  enabled: boolean;
  dataDate: string | null;
  score: number | null;
  grade: string | null;
  strengthState: string | null;
  readableState: string;
  coveragePct: number | null;
  constituentCount: number | null;
  direction: string | null;
  status?: TopicStatus[];
  lifecycle?: TopicLifecycle;
  publication?: Record<string, unknown>;
  quality?: Record<string, unknown>;
  lineage?: Record<string, unknown>;
};

export type TopicStatus = {
  key: "族群表現" | "領漲核心" | "動能擴散";
  state: string | null;
  evidence: Record<string, unknown>;
};

export type TopicLifecycleEvidence = {
  leadership?: {
    leaderChangePct?: number | null;
    leaderProxy?: boolean | null;
    leaderSemanticAvailable?: boolean | null;
    [key: string]: unknown;
  };
  diffusion?: {
    positiveBreadth?: number | null;
    coveragePct?: number | null;
    expectedMemberCount?: number | null;
    observedMemberCount?: number | null;
    [key: string]: unknown;
  };
  groupStrength?: {
    strongBreadth?: number | null;
    weakRatio?: number | null;
    averageChangePct?: number | null;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

export type TopicLifecycle = {
  currentStage: string | null;
  currentStageEnteredAt: string | null;
  currentStageTradingDays: number | null;
  history: Array<{ stage: string; enteredAt: string | null; exitedAt: string | null; tradingDays: number | null; current: boolean }>;
  dataStatus: LifecycleAvailability;
  evaluationDate?: string | null;
  previousStage?: string | null;
  candidateStage?: string | null;
  transitionDecision?: string | null;
  transitionReason?: string | null;
  policyVersion?: string | null;
  evidence?: TopicLifecycleEvidence;
  confidence?: Record<string, unknown>;
  lineage?: Record<string, unknown>;
};

export type TopicConstituent = {
  code: string;
  name: string;
  relationType: string;
  role: "代表股" | "核心股" | "關聯股" | null;
  weight: number | null;
  price: number | null;
  changePct: number | null;
  dataDate: string | null;
  dataFreshness: string | null;
  technicalState: string | null;
  relativeTopicState: string | null;
};

export type TopicDetail = TopicSummary & {
  constituents: TopicConstituent[];
  status: TopicStatus[];
  lifecycle?: TopicLifecycle;
};

export type TopicResource<T> = {
  source: TopicSource;
  data: T | null;
  error: string | null;
};

export type TopicRotationResource = TopicResource<TopicRotationEvent[]>;

type ApiTopicSummary = components["schemas"]["TopicReadModel"];
type ApiTopicConstituent = components["schemas"]["TopicConstituentRead"];
type ApiTopicDetail = ApiTopicSummary;

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

function topicPreviewEnabled(): boolean {
  return process.env.NODE_ENV === "development"
    && process.env.NEXT_PUBLIC_ENABLE_TOPIC_PREVIEW === "true";
}

function readableState(value: string | null | undefined): string {
  return readableTopicState(value);
}

function roleFor(value: string | null | undefined): "代表股" | "核心股" | "關聯股" | null {
  return ROLE_LABELS[(value ?? "").trim().toUpperCase()] ?? null;
}

function normalizeHierarchy(catalog: TopicCatalogNode): TopicHierarchy {
  return {
    kind: catalog.kind,
    parents: catalog.hierarchy.parents ?? [],
    children: catalog.hierarchy.children ?? [],
  };
}

function normalizeStatus(items: components["schemas"]["TopicStatusRead"][] | undefined): TopicStatus[] {
  const allowed = new Set<TopicStatus["key"]>(["族群表現", "領漲核心", "動能擴散"]);
  return (items ?? [])
    .filter((item): item is components["schemas"]["TopicStatusRead"] & { key: TopicStatus["key"] } => allowed.has(item.key as TopicStatus["key"]))
    .map((item) => ({ key: item.key, state: item.state, evidence: item.evidence ?? {} }));
}

function normalizeLifecycle(item: ApiTopicSummary): TopicLifecycle {
  return {
    ...item.lifecycle,
    history: (item.lifecycle.history ?? []).map((segment) => ({
      stage: segment.stage,
      enteredAt: segment.enteredAt,
      exitedAt: segment.exitedAt,
      tradingDays: segment.tradingDays,
      current: segment.current,
    })),
  };
}

function leafStateFromApi(item: ApiTopicSummary): TopicLeafState {
  return {
    topicId: item.topicId,
    slug: item.slug,
    dataDate: item.dataDate,
    score: item.score,
    grade: item.grade,
    direction: item.direction,
    strengthState: item.strengthState,
    readableState: item.readableState || readableState(item.strengthState),
    coveragePct: item.coveragePct,
    constituentCount: item.constituentCount,
    status: normalizeStatus(item.status),
    lifecycle: normalizeLifecycle(item),
    publication: item.publication,
    quality: item.quality,
    lineage: item.lineage,
  };
}

function snapshotLeafState(catalog: TopicCatalogNode): Pick<TopicSummary, "dataDate" | "score" | "grade" | "direction" | "coveragePct" | "constituentCount"> {
  const snapshot = catalog.currentFormalSnapshot.snapshot;
  return {
    dataDate: snapshot?.snapshotDate ?? null,
    score: snapshot?.topicScore ?? null,
    grade: snapshot?.marketGrade ?? null,
    direction: snapshot?.topicDirection ?? null,
    coveragePct: snapshot?.coveragePct ?? null,
    constituentCount: catalog.kind === "LEAF" ? snapshot?.stockCount ?? catalog.members?.length ?? null : null,
  };
}

function summaryFromCatalog(catalog: TopicCatalogNode, state: ApiTopicSummary | null): TopicSummary {
  const hierarchy = normalizeHierarchy(catalog);
  const snapshotState = snapshotLeafState(catalog);
  const leafState = state ? leafStateFromApi(state) : null;
  const groupName = hierarchy.parents[0]?.name ?? null;
  return {
    topicId: catalog.topicId,
    slug: catalog.slug,
    name: catalog.name,
    kind: catalog.kind,
    hierarchy,
    catalog,
    leafState,
    snapshotAvailability: catalog.currentFormalSnapshot.availability.state,
    snapshotAvailabilityReason: catalog.currentFormalSnapshot.availability.reason ?? null,
    groupName,
    topicType: catalog.kind,
    enabled: catalog.enabled,
    dataDate: leafState?.dataDate ?? snapshotState.dataDate,
    score: leafState?.score ?? snapshotState.score,
    grade: leafState?.grade ?? snapshotState.grade,
    strengthState: catalog.kind === "LEAF" ? leafState?.strengthState ?? null : null,
    readableState: catalog.kind === "LEAF" ? leafState?.readableState ?? readableState(null) : "Parent Topic",
    coveragePct: leafState?.coveragePct ?? snapshotState.coveragePct,
    constituentCount: catalog.kind === "LEAF" ? leafState?.constituentCount ?? snapshotState.constituentCount : null,
    direction: catalog.kind === "LEAF" ? leafState?.direction ?? snapshotState.direction : null,
    status: catalog.kind === "LEAF" ? leafState?.status ?? [] : [],
    lifecycle: catalog.kind === "LEAF" ? leafState?.lifecycle : undefined,
    publication: leafState?.publication,
    quality: leafState?.quality,
    lineage: leafState?.lineage,
  };
}

function disclosure(field: TopicPublicationField, state: TopicPublicationState, note: string): TopicPublicationDisclosure {
  return { field, state, note };
}

function sourceDisclosure(field: TopicPublicationField, source: TopicSource, apiState: TopicPublicationState, apiNote: string): TopicPublicationDisclosure {
  if (source === "synthetic-snapshot") return disclosure(field, "PREVIEW", "Preview 題材資料；不代表正式 Read Model。" );
  if (source === "unavailable") return disclosure(field, "UNAVAILABLE", "正式 API 未回傳可用資料。" );
  return disclosure(field, apiState, apiNote);
}

function lifecyclePublicationState(status: LifecycleAvailability | null | undefined): TopicPublicationState {
  if (status === "SHADOW_AVAILABLE") return "SHADOW";
  if (status === "AVAILABLE" || status === "FORMAL_AVAILABLE") return "FORMAL";
  if (status === "NOT_AVAILABLE" || status === "FAIL_CLOSED") return "UNAVAILABLE";
  return "DEFERRED";
}

export function lifecycleStageAvailable(status: LifecycleAvailability | null | undefined): boolean {
  return status === "AVAILABLE" || status === "FORMAL_AVAILABLE" || status === "SHADOW_AVAILABLE";
}

export function lifecycleStatusLabel(status: LifecycleAvailability | null | undefined): string {
  switch (status) {
    case "AVAILABLE": return "可用";
    case "FORMAL_AVAILABLE": return "正式可用";
    case "SHADOW_AVAILABLE": return "Forward Shadow";
    case "INSUFFICIENT_DATA": return "資料不足";
    case "PENDING": return "等待評估";
    case "WAITING_FOR_FORMAL_LINEAGE": return "等待正式 lineage";
    case "FAIL_CLOSED": return "FAIL_CLOSED";
    case "NOT_AVAILABLE": return "Unavailable";
    case "PREVIEW": return "Preview";
    default: return "Lifecycle 狀態待確認";
  }
}

export function getTopicPublication(source: TopicSource, topic: TopicSummary | TopicDetail): TopicPublication {
  if (topic.kind === "PARENT") {
    return {
      identity: sourceDisclosure("identity", source, "FORMAL", "正式 Topic Catalog identity。"),
      hierarchy: sourceDisclosure("hierarchy", source, "FORMAL", "正式 Parent → children hierarchy。"),
      relations: disclosure("relations", "NOT_APPLICABLE", "Parent Topic 不承擔 Leaf market membership semantics。"),
      score: disclosure("score", "NOT_APPLICABLE", "Parent Topic 不顯示正式 Score。"),
      grade: disclosure("grade", "NOT_APPLICABLE", "Parent Topic 不進入 Grade lanes。"),
      snapshot: disclosure("snapshot", "NOT_APPLICABLE", "Parent Topic 不需要 formal daily snapshot。"),
      participation: disclosure("participation", "NOT_APPLICABLE", "Parent Topic 不顯示 Leaf participation state。"),
      lifecycle: disclosure("lifecycle", "NOT_APPLICABLE", "Parent Topic 不進入 Lifecycle lanes。"),
      leaderCore: disclosure("leaderCore", "NOT_APPLICABLE", "Parent Topic 不具備正式 Leader/Core member semantics。"),
      technicalRelative: disclosure("technicalRelative", "NOT_APPLICABLE", "Parent Topic 不顯示 Leaf technical state。"),
      events: disclosure("events", "CONTRACT_GAP", "Topic events 尚未提供 formal Topic Detail contract。"),
      news: disclosure("news", "CONTRACT_GAP", "Topic news/context 尚未提供 formal Topic Detail contract。"),
      heatmap: disclosure("heatmap", "NOT_APPLICABLE", "Parent Topic 不進入 Leaf market heatmap。"),
      summary: disclosure("summary", "CONTRACT_GAP", "Formal summary/narrative 尚未提供。"),
      opportunity: disclosure("opportunity", "DEFERRED", "Opportunity 為下游 deferred/shadow boundary。"),
      source: sourceDisclosure("source", source, "FORMAL", "Identity/hierarchy 由 Topic Catalog 提供。"),
    };
  }
  const snapshotReady = Boolean(topic.dataDate) && (topic.direction !== null || topic.strengthState !== null || topic.coveragePct !== null);
  const statusReady = Boolean(topic.dataDate) && (topic.status ?? []).length === 3 && (topic.status ?? []).every((item) => item.state !== null);
  const lifecycleState = lifecyclePublicationState(topic.lifecycle?.dataStatus);
  const lifecycleNote = topic.lifecycle?.dataStatus === "SHADOW_AVAILABLE"
    ? "Canonical API 提供 Forward Shadow Lifecycle；僅供目前/影子研究顯示，不代表正式 production publication。"
    : topic.lifecycle?.dataStatus === "FAIL_CLOSED"
      ? "Lifecycle backend 已 fail closed；前端不補 stage、不推導。"
      : "正式 Lifecycle current/history 尚未提供足夠資料；前端不自行推導。";

  return {
    identity: sourceDisclosure("identity", source, "FORMAL", "正式 Topic Catalog identity。"),
    hierarchy: sourceDisclosure("hierarchy", source, topic.hierarchy.parents.length || topic.hierarchy.children.length ? "FORMAL" : "FORMAL_NOT_WIRED", topic.hierarchy.parents.length || topic.hierarchy.children.length ? "正式 hierarchy projection。" : "正式 hierarchy 尚未回傳 edge。"),
    relations: sourceDisclosure("relations", source, "FORMAL", "正式 effective-dated relation/read route。"),
    score: sourceDisclosure("score", source, topic.score === null ? "DEFERRED" : "FORMAL", topic.score === null ? "正式 score 尚未發布；前端不自行計算。" : "正式 API 已回傳 score。"),
    grade: sourceDisclosure("grade", source, topic.grade === null ? "DEFERRED" : "FORMAL", topic.grade === null ? "正式 grade 尚未發布；不推導 S/A/B/D。" : "正式 API 已回傳 grade。"),
    snapshot: sourceDisclosure("snapshot", source, topic.snapshotAvailability === "AVAILABLE" && snapshotReady ? "FORMAL" : "UNAVAILABLE", topic.snapshotAvailability === "AVAILABLE" && snapshotReady ? "Topic Catalog current formal snapshot 已提供。" : topic.snapshotAvailabilityReason ?? "正式 Topic Snapshot 尚未發布；前端不自行補值。"),
    participation: sourceDisclosure("participation", source, statusReady ? "FORMAL" : "FORMAL_NOT_WIRED", statusReady ? "三個 participation status 均由 API 回傳。" : "participation/leadership/diffusion 尚未有完整 published evidence。"),
    lifecycle: sourceDisclosure("lifecycle", source, lifecycleState, lifecycleNote),
    leaderCore: sourceDisclosure("leaderCore", source, "CONTRACT_GAP", "Leader/Core formal contract 尚未提供。"),
    technicalRelative: sourceDisclosure("technicalRelative", source, "CONTRACT_GAP", "Technical/relative topic state 尚未提供 formal contract。"),
    events: sourceDisclosure("events", source, "CONTRACT_GAP", "Topic events 尚未提供 formal Topic Detail contract。"),
    news: sourceDisclosure("news", source, "CONTRACT_GAP", "Topic news/context 尚未提供 formal Topic Detail contract。"),
    heatmap: sourceDisclosure("heatmap", source, "CONTRACT_GAP", "Formal heatmap sizing/value contract 尚未提供。"),
    summary: sourceDisclosure("summary", source, "CONTRACT_GAP", "Formal summary/narrative 尚未提供。"),
    opportunity: sourceDisclosure("opportunity", source, "DEFERRED", "Opportunity 為下游 deferred/shadow boundary。"),
    source: sourceDisclosure("source", source, "CONTRACT_GAP", "API 只代表 transport path；欄位 publication/source lineage 另行揭露。"),
  };
}

function rawTopicSlug(topic: RawTopic): string | null {
  const value = (topic as RawTopic & { slug?: unknown }).slug;
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function rawTopicSummary(topic: RawTopic): TopicSummary | null {
  const slug = rawTopicSlug(topic);
  if (!slug) return null;
  const hierarchy: TopicHierarchy = { kind: "LEAF", parents: [], children: [] };
  return {
    topicId: slug,
    slug,
    name: topicNameLabel(slug, topic.name),
    kind: "LEAF",
    hierarchy,
    catalog: null,
    leafState: null,
    snapshotAvailability: "UNAVAILABLE",
    snapshotAvailabilityReason: "PREVIEW_DATA",
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
    direction: null,
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
      topicId: slug,
      slug,
      name: item.name,
      kind: "LEAF" as const,
      hierarchy: { kind: "LEAF" as const, parents: [], children: [] },
      catalog: null,
      leafState: null,
      snapshotAvailability: "UNAVAILABLE" as const,
      snapshotAvailabilityReason: "PREVIEW_DATA",
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
      direction: null,
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
        technicalState: null,
        relativeTopicState: null,
      })),
      status: [],
      lifecycle: { currentStage: null, currentStageEnteredAt: null, currentStageTradingDays: null, history: [], dataStatus: "PREVIEW" },
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
        technicalState: null,
        relativeTopicState: null,
      };
    }),
    status: [],
    lifecycle: { currentStage: null, currentStageEnteredAt: null, currentStageTradingDays: null, history: [], dataStatus: "PREVIEW" },
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

function constituentFromApi(item: ApiTopicConstituent, dataDate: string | null): TopicConstituent {
  return {
    code: item.code,
    name: item.name ?? item.code,
    relationType: item.role ?? "FORMAL",
    role: roleFor(item.role),
    weight: item.relationWeight,
    price: item.price,
    changePct: item.changePct,
    dataDate,
    dataFreshness: item.freshness,
    technicalState: item.technicalState,
    relativeTopicState: item.relativeTopicState,
  };
}

function constituentsFromCatalog(catalog: TopicCatalogNode): TopicConstituent[] {
  if (catalog.kind === "PARENT") return [];
  return (catalog.members ?? []).map((item) => ({
    code: item.code,
    name: item.name ?? item.code,
    relationType: item.relationType,
    role: roleFor(item.relationType),
    weight: null,
    price: null,
    changePct: null,
    dataDate: null,
    dataFreshness: "UNAVAILABLE",
    technicalState: null,
    relativeTopicState: null,
  }));
}

function detailFromCatalog(catalog: TopicCatalogNode, state: ApiTopicDetail | null): TopicDetail {
  const summary = summaryFromCatalog(catalog, state);
  const stateConstituents = state?.constituents ?? [];
  const constituents = catalog.kind === "PARENT"
    ? []
    : stateConstituents.length > 0
      ? stateConstituents.map((item) => constituentFromApi(item, state?.dataDate ?? null))
      : constituentsFromCatalog(catalog);
  return {
    ...summary,
    constituents,
    status: summary.status ?? [],
    lifecycle: summary.lifecycle,
  };
}

export async function fetchTopics(): Promise<TopicResource<TopicSummary[]>> {
  const base = apiBaseUrl();
  if (!base) {
    const data = topicPreviewEnabled() ? syntheticTopics() : [];
    return data.length
      ? { source: "synthetic-snapshot", data, error: null }
      : { source: "unavailable", data: null, error: "尚未設定正式 FastAPI API origin；production 不使用 Preview 題材清單替代。" };
  }
  const [catalogResult, stateResult] = await Promise.all([
    request<TopicCatalogPage>("/api/v2/topic-catalog?limit=500&offset=0"),
    request<{ items: ApiTopicSummary[] }>("/api/v2/topics?limit=500&offset=0"),
  ]);
  if (catalogResult.source !== "api" || !catalogResult.data) {
    return { source: "unavailable", data: null, error: catalogResult.error ?? "Topic Catalog identity read model is unavailable." };
  }
  const stateBySlug = new Map((stateResult.data?.items ?? []).map((item) => [item.slug, item]));
  const data = catalogResult.data.items.map((catalog) => summaryFromCatalog(catalog, stateBySlug.get(catalog.slug) ?? null));
  return {
    source: "api",
    data,
    error: stateResult.source === "unavailable" ? stateResult.error : null,
  };
}

export async function fetchTopic(slug: string): Promise<TopicResource<TopicDetail>> {
  const base = apiBaseUrl();
  if (!base) {
    const data = topicPreviewEnabled() ? syntheticDetail(slug) : null;
    return data
      ? { source: "synthetic-snapshot", data, error: null }
      : { source: "unavailable", data: null, error: "此 slug 不在公開合成 snapshot，且尚未設定 FastAPI API origin。" };
  }
  const [catalogResult, stateResult] = await Promise.all([
    request<TopicCatalogNode>(`/api/v2/topic-catalog/${encodeURIComponent(slug)}`),
    request<ApiTopicDetail>(`/api/v2/topics/${encodeURIComponent(slug)}`),
  ]);
  if (catalogResult.source !== "api" || !catalogResult.data) {
    return { source: "unavailable", data: null, error: catalogResult.error ?? "Topic Catalog identity read model is unavailable." };
  }
  return {
    source: "api",
    error: stateResult.source === "unavailable" ? stateResult.error : null,
    data: detailFromCatalog(catalogResult.data, stateResult.data ?? null),
  };
}

export function roleRank(role: TopicConstituent["role"]): number {
  return role === "代表股" ? 0 : role === "核心股" ? 1 : 2;
}

export function scoreLabel(score: number | null): string {
  return score === null ? "—" : Number.isInteger(score) ? String(score) : score.toFixed(1);
}

export function sourceLabel(source: TopicSource): string {
  return source === "api" ? "API 傳輸 · 欄位狀態另行揭露" : source === "synthetic-snapshot" ? PREVIEW_LABEL : "資料來源未連線";
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
  if (!base) {
    return topicPreviewEnabled()
      ? { source: "synthetic-snapshot", data: getPreviewTopicRotation(), error: null }
      : { source: "unavailable", data: null, error: "正式 API origin 未設定；production 不使用 Preview 輪動資料替代。" };
  }
  const result = await request<{ items: ApiTopicRotation[] }>("/api/v1/analytics/topic-rotation?days=14&limit=100&offset=0");
  if (result.source === "api" && result.data?.items?.length) {
    const data = result.data.items.map(rotationFromApi).sort((a, b) => b.occurredAt.localeCompare(a.occurredAt));
    return { source: "api", data, error: null };
  }
  return { source: "unavailable", data: null, error: result.error ?? "正式輪動 read model 尚未提供完整事件欄位。" };
}
