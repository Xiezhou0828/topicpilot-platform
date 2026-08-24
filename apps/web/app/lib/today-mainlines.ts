"use client";

import {
  fetchTodayHomeResource,
  mapHomeToTodayHomeResource,
  TODAY_MAINLINES_PREVIEW_ENABLED,
  useTodayHomeResource,
  type HomeResponse,
  type HomeDailyFocus,
  type HomeMarketOverview,
  type HomeMarketPulseEvent,
  type HomeOpportunityStock,
  type HomeOpportunityTopic,
  type HomeRotationTopic,
  type TodayHomeSectionState,
  type TodayHomePublicationState,
  type TodayHomeResource,
} from "./today-home";

export type { HomeResponse } from "./today-home";
export { TODAY_MAINLINES_PREVIEW_ENABLED } from "./today-home";
export type TodaySectionState = Exclude<TodayHomeSectionState, "LOADING">;
export type TodayMainlinesState = TodaySectionState;

type TodaySectionMetadata = {
  dataDate: string | null;
  generatedAt: string | null;
  latestSnapshotTime: string | null;
  asOf: string | null;
  source: string | null;
  classification: string | null;
  qualityStatus: string | null;
  temporarySections: string[];
  missingSections: string[];
  qualityNotes: string[];
};

export type TodayRotationResource = {
  state: TodayMainlinesState;
  data: HomeRotationTopic[];
  dataDate: string | null;
  generatedAt: string | null;
  latestSnapshotTime: string | null;
  asOf: string | null;
  source: string | null;
  classification: string | null;
  qualityStatus: string | null;
  temporarySections: string[];
  missingSections: string[];
  qualityNotes: string[];
  reason: string | null;
};

export type TodayDailyFocusResource = {
  state: TodayHomePublicationState | "ERROR";
  data: HomeDailyFocus | null;
  dataDate: string | null;
  generatedAt: string | null;
  latestSnapshotTime: string | null;
  asOf: string | null;
  source: string | null;
  mode: string | null;
  temporary: boolean | null;
  classification: string | null;
  qualityStatus: string | null;
  temporarySections: string[];
  missingSections: string[];
  qualityNotes: string[];
  reason: string | null;
};

export type TodayMarketEventsResource = {
  state: TodayHomePublicationState | "ERROR";
  data: HomeMarketPulseEvent[];
  dataDate: string | null;
  generatedAt: string | null;
  latestSnapshotTime: string | null;
  asOf: string | null;
  source: string | null;
  classification: string | null;
  qualityStatus: string | null;
  temporarySections: string[];
  missingSections: string[];
  qualityNotes: string[];
  reason: string | null;
};

export type TodayOpportunityResource = {
  state: TodayMainlinesState;
  data: HomeOpportunityTopic[];
  dataDate: string | null;
  generatedAt: string | null;
  latestSnapshotTime: string | null;
  asOf: string | null;
  source: string | null;
  classification: string | null;
  qualityStatus: string | null;
  temporarySections: string[];
  missingSections: string[];
  qualityNotes: string[];
  reason: string | null;
};

export type TodayMarketOverviewResource = {
  state: TodayHomePublicationState | "ERROR";
  data: HomeMarketOverview | null;
  dataDate: string | null;
  generatedAt: string | null;
  latestSnapshotTime: string | null;
  asOf: string | null;
  source: string | null;
  dataStatus: string | null;
  classification: string | null;
  qualityStatus: string | null;
  temporarySections: string[];
  missingSections: string[];
  qualityNotes: string[];
  reason: string | null;
};

export type TodayMainlinesResource = {
  state: TodayMainlinesState;
  data: TodayHomeResource["sections"]["mainTopics"];
  dataDate: string | null;
  generatedAt: string | null;
  latestSnapshotTime: string | null;
  asOf: string | null;
  source: string | null;
  classification: string | null;
  qualityStatus: string | null;
  temporarySections: string[];
  missingSections: string[];
  qualityNotes: string[];
  reason: string | null;
  dailyFocus: TodayDailyFocusResource;
  marketEvents: TodayMarketEventsResource;
  marketOverview: TodayMarketOverviewResource;
  opportunities: TodayOpportunityResource;
  heating: TodayRotationResource;
  cooling: TodayRotationResource;
};

export type TodayMainlinesLoadState = {
  loading: boolean;
  resource: TodayMainlinesResource;
};

function stateFromHomeResource(
  resource: TodayHomeResource,
  previewEnabled: boolean,
): TodayMainlinesState {
  if (resource.transportState === "ERROR") return "ERROR";
  if (resource.transportState !== "READY") return "UNAVAILABLE";
  if (resource.publicationState === "FORMAL") return "FORMAL";
  const state = resource.publicationState;
  if (state === "PREVIEW" && !previewEnabled) return "UNAVAILABLE";
  return state;
}

function metadata(resource: TodayHomeResource): TodaySectionMetadata {
  return {
    dataDate: resource.metadata.dataDate,
    generatedAt: resource.metadata.generatedAt,
    latestSnapshotTime: resource.metadata.latestSnapshotTime,
    asOf: resource.metadata.asOf,
    source: resource.metadata.source,
    classification: resource.metadata.classification,
    qualityStatus: resource.metadata.status,
    temporarySections: [...resource.metadata.temporarySections],
    missingSections: [...resource.metadata.missingSections],
    qualityNotes: [...resource.metadata.qualityNotes],
  };
}

function transportErrorReason(resource: TodayHomeResource, section: string): string {
  return resource.metadata.reason ?? `目前無法讀取${section}資料。`;
}

function sectionUserMessage(
  resource: TodayHomeResource,
  section: string,
  defaultMessage: string,
): string {
  return resource.metadata.sectionStatuses[section]?.userMessage
    ?? resource.metadata.reason
    ?? defaultMessage;
}

function isHomeRotationTopic(value: HomeRotationTopic): boolean {
  return Boolean(
    value
      && typeof value.topic === "string"
      && typeof value.topicSlug === "string"
      && value.topicSlug.length > 0
      && typeof value.strengthDelta === "number"
      && Number.isFinite(value.strengthDelta)
      && typeof value.currentGrade === "string"
      && typeof value.summary === "string",
  );
}

function isHomeDailyFocus(value: HomeDailyFocus | null): value is HomeDailyFocus {
  return Boolean(
    value
      && typeof value.mode === "string"
      && value.mode.trim().length > 0
      && typeof value.source === "string"
      && value.source.trim().length > 0
      && typeof value.headline === "string"
      && value.headline.trim().length > 0
      && Array.isArray(value.bullets)
      && value.bullets.length > 0
      && value.bullets.every((bullet) => typeof bullet === "string" && bullet.trim().length > 0)
      && (value.dataDate === null || (typeof value.dataDate === "string" && value.dataDate.trim().length > 0))
      && typeof value.temporary === "boolean",
  );
}

function mapDailyFocus(
  resource: TodayHomeResource,
  previewEnabled: boolean,
): TodayDailyFocusResource {
  const data = resource.sections.dailyFocus;
  const shared = metadata(resource);
  const dailyMetadata = {
    ...shared,
    dataDate: data?.dataDate ?? null,
    asOf: shared.asOf,
    source: data?.source ?? shared.source,
    mode: data?.mode ?? null,
    temporary: typeof data?.temporary === "boolean" ? data.temporary : null,
  };

  if (resource.transportState === "ERROR") {
    return {
      state: "ERROR",
      data: null,
      ...dailyMetadata,
      reason: transportErrorReason(resource, "Market Story"),
    };
  }

  if (!isHomeDailyFocus(data)) {
    return {
      state: "UNAVAILABLE",
      data: null,
      ...dailyMetadata,
      reason: sectionUserMessage(resource, "dailyFocus", "今日市場重點尚未完成。"),
    };
  }

  let state: TodaySectionState = stateFromHomeResource(resource, previewEnabled);
  if (state === "FORMAL" && data.temporary) state = "TEMPORARY";

  if (state === "UNAVAILABLE") {
    return {
      state,
      data: null,
      ...dailyMetadata,
      reason: resource.metadata.reason ?? "今日市場重點尚未完成。",
    };
  }

  return {
    state,
    data,
    ...dailyMetadata,
    reason: state === "FORMAL"
      ? null
      : resource.metadata.reason ?? "今日市場重點目前僅供預覽。",
  };
}

function isHomeMarketPulseEvent(value: HomeMarketPulseEvent): boolean {
  return Boolean(
    value
      && typeof value.eventTime === "string"
      && value.eventTime.trim().length > 0
      && typeof value.topic === "string"
      && value.topic.trim().length > 0
      && typeof value.eventType === "string"
      && value.eventType.trim().length > 0
      && typeof value.description === "string"
      && value.description.trim().length > 0
      && typeof value.severity === "string"
      && value.severity.trim().length > 0
      && typeof value.topicSlug === "string"
      && value.topicSlug.trim().length > 0
      && typeof value.source === "string"
      && value.source.trim().length > 0,
  );
}

function mapMarketEvents(
  resource: TodayHomeResource,
  previewEnabled: boolean,
): TodayMarketEventsResource {
  const shared = metadata(resource);
  const data = resource.sections.marketPulse;
  const state: TodaySectionState = stateFromHomeResource(resource, previewEnabled);

  if (resource.transportState === "ERROR") {
    return {
      state: "ERROR",
      data: [],
      ...shared,
      reason: transportErrorReason(resource, "Market Events"),
    };
  }

  if (data.length === 0) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...shared,
      reason: sectionUserMessage(resource, "marketEvents", "今日市場事件尚未提供。"),
    };
  }

  if (!data.every(isHomeMarketPulseEvent)) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...shared,
      reason: sectionUserMessage(resource, "marketEvents", "今日市場事件尚未提供。"),
    };
  }

  if (state === "UNAVAILABLE") {
    return {
      state,
      data: [],
      ...shared,
      reason: resource.metadata.reason ?? "今日市場事件尚未完成。",
    };
  }

  return {
    state,
    data,
    ...shared,
    reason: state === "FORMAL"
      ? null
      : resource.metadata.reason ?? "今日市場事件目前僅供預覽。",
  };
}

function isHomeOpportunityStock(value: HomeOpportunityStock): boolean {
  return Boolean(
    value
      && typeof value.code === "string"
      && value.code.trim().length > 0
      && typeof value.name === "string"
      && value.name.trim().length > 0
      && (value.dataDate === null || (typeof value.dataDate === "string" && value.dataDate.trim().length > 0))
      && (value.reason === null || typeof value.reason === "string")
      && isNullableCount(value.score)
      && (value.strategyKeys === undefined
        || (Array.isArray(value.strategyKeys)
          && value.strategyKeys.every((key) => typeof key === "string" && key.trim().length > 0))),
  );
}

function isHomeOpportunityTopic(value: HomeOpportunityTopic): boolean {
  return Boolean(
    value
      && typeof value.topic === "string"
      && value.topic.trim().length > 0
      && typeof value.topicSlug === "string"
      && value.topicSlug.trim().length > 0
      && (value.grade === null || typeof value.grade === "string")
      && isNullableCount(value.strength)
      && (value.currentState === null || typeof value.currentState === "string")
      && typeof value.summary === "string"
      && value.summary.trim().length > 0
      && typeof value.temporary === "boolean"
      && Array.isArray(value.validatedStocks)
      && value.validatedStocks.length > 0
      && value.validatedStocks.every(isHomeOpportunityStock),
  );
}

function hasShadowOpportunityData(
  resource: TodayHomeResource,
  data: HomeOpportunityTopic[],
): boolean {
  const markers = [
    resource.metadata.classification,
    resource.metadata.source,
    resource.metadata.status,
  ].filter(Boolean).join(" ");
  return resource.metadata.temporarySections.includes("opportunities")
    || data.some((topic) => topic.temporary)
    || /SHADOW|SYNTHETIC|FIXTURE|DEMO/i.test(markers);
}

function hasFormalOpportunityAuthority(
  resource: TodayHomeResource,
  data: HomeOpportunityTopic[],
): boolean {
  return resource.publicationState === "FORMAL"
    && !resource.metadata.temporarySections.includes("opportunities")
    && !resource.metadata.missingSections.includes("opportunities")
    && !hasShadowOpportunityData(resource, data);
}

function mapOpportunities(
  resource: TodayHomeResource,
  previewEnabled: boolean,
): TodayOpportunityResource {
  const shared = metadata(resource);
  const data = resource.sections.opportunities;

  if (resource.transportState === "ERROR") {
    return {
      state: "ERROR",
      data: [],
      ...shared,
      reason: transportErrorReason(resource, "Opportunities"),
    };
  }

  if (data.length === 0) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...shared,
      reason: sectionUserMessage(resource, "opportunities", "今日機會資料尚未提供。"),
    };
  }

  if (!data.every(isHomeOpportunityTopic)) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...shared,
      reason: sectionUserMessage(resource, "opportunities", "今日機會資料尚未提供。"),
    };
  }

  if (hasFormalOpportunityAuthority(resource, data)) {
    return {
      state: "FORMAL",
      data,
      ...shared,
      reason: null,
    };
  }

  if (resource.publicationState !== "UNAVAILABLE" && previewEnabled) {
    return {
      state: "PREVIEW",
      data,
      ...shared,
      reason: "今日機會尚未正式發布，目前僅在預覽模式顯示。",
    };
  }

  return {
    state: "UNAVAILABLE",
    data: [],
    ...shared,
    reason: hasShadowOpportunityData(resource, data)
      ? "今日機會資料尚未完成正式驗證。"
      : "今日機會目前尚未提供正式資料。",
  };
}

function isNullableCount(value: number | null): boolean {
  return value === null || (typeof value === "number" && Number.isFinite(value));
}

function isHomeMarketOverview(value: HomeMarketOverview | null): value is HomeMarketOverview {
  const health = value?.marketHealth;
  return Boolean(
    value
      && (value.dataDate === null || typeof value.dataDate === "string")
      && (value.updatedAt === null || typeof value.updatedAt === "string")
      && typeof value.dataStatus === "string"
      && value.dataStatus.trim().length > 0
      && typeof value.trackedStockCount === "number"
      && Number.isFinite(value.trackedStockCount)
      && typeof value.trackedTopicCount === "number"
      && Number.isFinite(value.trackedTopicCount)
      && (value.latestSnapshotTime === null || typeof value.latestSnapshotTime === "string")
      && typeof value.source === "string"
      && value.source.trim().length > 0
      && (!health
        || (typeof health.market === "string"
          && health.market.trim().length > 0
          && typeof health.status === "string"
          && health.status.trim().length > 0
          && isNullableCount(health.totalStocks)
          && isNullableCount(health.advance)
          && isNullableCount(health.decline)
          && isNullableCount(health.flat)
          && isNullableCount(health.unavailable))),
  );
}

function mapMarketOverview(
  resource: TodayHomeResource,
  previewEnabled: boolean,
): TodayMarketOverviewResource {
  const data = resource.sections.marketOverview;
  const shared = metadata(resource);
  const state: TodaySectionState = stateFromHomeResource(resource, previewEnabled);
  const dataDate = data?.dataDate ?? shared.dataDate;
  const asOf = data?.updatedAt ?? shared.asOf;
  const source = data?.source ?? shared.source;
  const dataStatus = data?.dataStatus ?? null;

  if (resource.transportState === "ERROR") {
    return {
      state: "ERROR",
      data: null,
      ...shared,
      dataDate,
      asOf,
      source,
      dataStatus,
      reason: transportErrorReason(resource, "Market Overview"),
    };
  }

  if (!isHomeMarketOverview(data)) {
    return {
      state: "UNAVAILABLE",
      data: null,
      ...shared,
      dataDate,
      asOf,
      source,
      dataStatus,
      reason: sectionUserMessage(resource, "marketOverview", "市場資料尚未完整。"),
    };
  }

  if (state === "UNAVAILABLE") {
    return {
      state,
      data: null,
      ...shared,
      dataDate,
      asOf,
      source,
      dataStatus,
      reason: resource.metadata.reason ?? "市場概況尚未完成發布。",
    };
  }

  return {
    state,
    data,
    ...shared,
    dataDate,
    asOf,
    source,
    dataStatus,
    reason: state === "FORMAL"
      ? null
      : resource.metadata.reason ?? "市場概況目前僅供預覽。",
  };
}

function mapRotation(
  resource: TodayHomeResource,
  data: HomeRotationTopic[],
  direction: "heating" | "cooling",
  previewEnabled: boolean,
): TodayRotationResource {
  const state = resource.publicationState === "PREVIEW" && !previewEnabled
    ? "UNAVAILABLE"
    : stateFromHomeResource(resource, previewEnabled);
  const section = direction === "heating" ? "heatingTopics" : "coolingTopics";
  const shared = metadata(resource);

  if (state === "ERROR") {
    return {
      state,
      data: [],
      ...shared,
      reason: transportErrorReason(resource, section),
    };
  }

  if (data.length === 0) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...shared,
      reason: sectionUserMessage(resource, section, "目前沒有足夠的 14 日資料。"),
    };
  }

  if (!data.every(isHomeRotationTopic)) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...shared,
      reason: sectionUserMessage(resource, section, "目前沒有足夠的 14 日資料。"),
    };
  }

  if (state === "UNAVAILABLE") {
    return {
      state,
      data: [],
      ...shared,
      reason: resource.metadata.reason ?? "目前沒有足夠的 14 日資料。",
    };
  }

  return {
    state,
    data,
    ...shared,
    reason: state === "FORMAL"
      ? null
      : resource.metadata.reason ?? `${section === "heatingTopics" ? "升溫" : "降溫"}資料目前僅供預覽。`,
  };
}

export function toTodayMainlinesResource(
  resource: TodayHomeResource,
  previewEnabled = TODAY_MAINLINES_PREVIEW_ENABLED,
): TodayMainlinesResource {
  const shared = metadata(resource);
  const dailyFocus = mapDailyFocus(resource, previewEnabled);
  const marketEvents = mapMarketEvents(resource, previewEnabled);
  const marketOverview = mapMarketOverview(resource, previewEnabled);
  const opportunities = mapOpportunities(resource, previewEnabled);
  const heating = mapRotation(resource, resource.sections.heatingTopics, "heating", previewEnabled);
  const cooling = mapRotation(resource, resource.sections.coolingTopics, "cooling", previewEnabled);
  const state = stateFromHomeResource(resource, previewEnabled);
  const data = resource.sections.mainTopics;

  if (state === "ERROR") {
    return {
      state,
      data: [],
      ...shared,
      reason: transportErrorReason(resource, "Main Topics"),
      dailyFocus,
      marketEvents,
      marketOverview,
      opportunities,
      heating,
      cooling,
    };
  }

  if (data.length === 0) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...shared,
      reason: sectionUserMessage(resource, "mainTopics", "題材資料尚未完成發布。"),
      dailyFocus,
      marketEvents,
      marketOverview,
      opportunities,
      heating,
      cooling,
    };
  }

  if (state === "UNAVAILABLE") {
    return {
      state,
      data: [],
      ...shared,
      reason: resource.metadata.reason ?? "今日主線尚未完成發布。",
      dailyFocus,
      marketEvents,
      marketOverview,
      opportunities,
      heating,
      cooling,
    };
  }

  return {
    state,
    data,
    ...shared,
    reason: state === "FORMAL"
      ? null
      : resource.metadata.reason ?? "今日主線目前僅供預覽。",
    dailyFocus,
    marketEvents,
    marketOverview,
    opportunities,
    heating,
    cooling,
  };
}

export function mapHomeToTodayMainlines(
  home: HomeResponse,
  previewEnabled = TODAY_MAINLINES_PREVIEW_ENABLED,
): TodayMainlinesResource {
  return toTodayMainlinesResource(mapHomeToTodayHomeResource(home, previewEnabled), previewEnabled);
}

export async function fetchTodayMainlines(
  options: Parameters<typeof fetchTodayHomeResource>[0] = {},
): Promise<TodayMainlinesResource> {
  const resource = await fetchTodayHomeResource(options);
  return toTodayMainlinesResource(
    resource,
    options.previewEnabled ?? TODAY_MAINLINES_PREVIEW_ENABLED,
  );
}

export function useTodayMainlines(): TodayMainlinesLoadState {
  const { loading, resource } = useTodayHomeResource();
  return {
    loading,
    resource: toTodayMainlinesResource(resource),
  };
}
