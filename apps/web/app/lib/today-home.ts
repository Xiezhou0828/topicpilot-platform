"use client";

import { useEffect, useState } from "react";
import {
  createTopicPilotClient,
  type FetchLike,
} from "../../../../packages/api-client/src/client.mjs";
import type { components } from "./generated-api";
import { getFormalApiBaseUrl } from "./stock-api";

export type HomeResponse = components["schemas"]["HomeResponse"];
export type HomeTopicCard = components["schemas"]["HomeTopicCard"];
export type HomeRotationTopic = components["schemas"]["HomeRotationTopic"];
export type HomeDailyFocus = components["schemas"]["HomeDailyFocus"];
export type HomeMarketPulseEvent = components["schemas"]["HomeMarketPulseEvent"];
export type HomeOpportunityStock = components["schemas"]["HomeOpportunityStock"];
export type HomeOpportunityTopic = components["schemas"]["HomeOpportunityTopic"];
export type HomeMarketOverview = components["schemas"]["HomeMarketOverview"];
export type HomeDataQuality = components["schemas"]["HomeDataQuality"];
export type HomeSectionStatus = components["schemas"]["HomeSectionStatus"];
export type HomePublication = components["schemas"]["HomePublication"];

export type TodayHomeTransportState = "LOADING" | "READY" | "ERROR";
export type TodayHomePublicationState = "FORMAL" | "TEMPORARY" | "PREVIEW" | "UNAVAILABLE";
export type TodayHomeSectionState = TodayHomePublicationState | "LOADING" | "ERROR";

export type TodayHomeMetadata = {
  dataDate: string | null;
  generatedAt: string | null;
  latestSnapshotTime: string | null;
  asOf: string | null;
  source: string | null;
  dataQuality: HomeDataQuality | null;
  temporarySections: string[];
  missingSections: string[];
  qualityNotes: string[];
  classification: string | null;
  status: string | null;
  reason: string | null;
  sectionStatuses: Record<string, HomeSectionStatus>;
};

export type TodayHomeSections = {
  mainTopics: HomeTopicCard[];
  heatingTopics: HomeRotationTopic[];
  coolingTopics: HomeRotationTopic[];
  dailyFocus: HomeDailyFocus | null;
  marketPulse: HomeMarketPulseEvent[];
  opportunities: HomeOpportunityTopic[];
  marketOverview: HomeMarketOverview | null;
};

export type TodayHomeResource = {
  transportState: TodayHomeTransportState;
  publicationState: TodayHomePublicationState;
  home: HomeResponse | null;
  sections: TodayHomeSections;
  metadata: TodayHomeMetadata;
};

export type TodayHomeLoadState = {
  loading: boolean;
  resource: TodayHomeResource;
};

export const TODAY_MAINLINES_PREVIEW_ENABLED = process.env.NEXT_PUBLIC_ENABLE_TODAY_MAINLINES_PREVIEW === "true";

function emptySections(): TodayHomeSections {
  return {
    mainTopics: [],
    heatingTopics: [],
    coolingTopics: [],
    dailyFocus: null,
    marketPulse: [],
    opportunities: [],
    marketOverview: null,
  };
}

function emptyMetadata(reason: string | null = null): TodayHomeMetadata {
  return {
    dataDate: null,
    generatedAt: null,
    latestSnapshotTime: null,
    asOf: null,
    source: null,
    dataQuality: null,
    temporarySections: [],
    missingSections: [],
    qualityNotes: [],
    classification: null,
    status: null,
    reason,
    sectionStatuses: {},
  };
}

function emptyResource(
  transportState: TodayHomeTransportState,
  reason: string,
): TodayHomeResource {
  return {
    transportState,
    publicationState: "UNAVAILABLE",
    home: null,
    sections: emptySections(),
    metadata: emptyMetadata(reason),
  };
}

export function loadingTodayHomeResource(): TodayHomeResource {
  return emptyResource("LOADING", "正在讀取 Today Home 資料。");
}

export function errorTodayHomeResource(reason: string): TodayHomeResource {
  return emptyResource("ERROR", reason);
}

function metadataFromHome(home: HomeResponse): TodayHomeMetadata {
  const quality = home.dataQuality;
  return {
    dataDate: home.mainTopics?.find((topic) => topic.dataDate)?.dataDate
      ?? home.marketOverview.dataDate
      ?? home.asOf
      ?? null,
    generatedAt: home.generatedAt ?? null,
    latestSnapshotTime: home.marketOverview.latestSnapshotTime ?? null,
    asOf: home.asOf ?? home.marketOverview.updatedAt ?? home.generatedAt ?? null,
    source: quality.source || home.marketOverview.source || null,
    dataQuality: quality,
    temporarySections: [...(quality.temporarySections ?? [])],
    missingSections: [...(quality.missingSections ?? [])],
    qualityNotes: [...(quality.notes ?? [])],
    classification: quality.classification ?? null,
    status: quality.status || home.marketOverview.dataStatus || null,
    reason: null,
    sectionStatuses: home.sectionStatuses ?? {},
  };
}

function publicationMarkers(home: HomeResponse): string {
  const quality = home.dataQuality;
  return [
    quality.classification,
    quality.source,
    quality.status,
    home.marketOverview.dataStatus,
    ...(quality.temporarySections ?? []),
    ...(quality.missingSections ?? []),
  ].filter(Boolean).join(" ");
}

function hasUnknownPublicationMetadata(home: HomeResponse): boolean {
  const quality = home.dataQuality;
  return [
    quality.status,
    quality.source,
    quality.classification,
    home.marketOverview.dataStatus,
  ].some((value) => typeof value !== "string" || value.trim().length === 0);
}

function classifyPublication(
  home: HomeResponse,
  previewEnabled: boolean,
): { state: TodayHomePublicationState; reason: string | null } {
  if (home.publication) {
    if (home.publication.state === "PUBLISHED") {
      return { state: "FORMAL", reason: null };
    }
    if (home.publication.state === "UNAVAILABLE") {
      return { state: "UNAVAILABLE", reason: "今日市場資料尚未完成發布。" };
    }
    if (previewEnabled) {
      return {
        state: "PREVIEW",
        reason: "今日資料尚未完成正式發布，僅在明確開啟預覽時顯示。",
      };
    }
    return { state: "UNAVAILABLE", reason: "今日市場資料尚未完成發布。" };
  }
  if (hasUnknownPublicationMetadata(home)) {
    return {
      state: "UNAVAILABLE",
      reason: "今日市場資料尚未完成發布。",
    };
  }

  const markers = publicationMarkers(home);
  const previewOnly = /SYNTHETIC|FIXTURE|DEMO|SHADOW/i.test(markers);
  const gateUnavailable = /UNAVAILABLE|NOT[_ -]?AVAILABLE|G1|DOWNSTREAM/i.test(markers);
  const temporary = /PARTIAL|TEMPORARY/i.test(markers) || (home.dataQuality.temporarySections ?? []).length > 0;

  if (!previewOnly && !gateUnavailable && !temporary) {
    return { state: "FORMAL", reason: null };
  }

  if (previewEnabled) {
    return {
      state: "PREVIEW",
      reason: "今日資料尚未正式發布，目前僅在預覽模式顯示。",
    };
  }

  if (temporary && !gateUnavailable && !previewOnly) {
    return {
      state: "TEMPORARY",
      reason: "今日資料仍在整理中，正式區塊暫不顯示。",
    };
  }

  return {
    state: "UNAVAILABLE",
    reason: "今日市場資料尚未完成發布。",
  };
}

export function mapHomeToTodayHomeResource(
  home: HomeResponse,
  previewEnabled = TODAY_MAINLINES_PREVIEW_ENABLED,
): TodayHomeResource {
  const metadata = metadataFromHome(home);
  const publication = classifyPublication(home, previewEnabled);
  return {
    transportState: "READY",
    publicationState: publication.state,
    home,
    sections: {
      mainTopics: Array.isArray(home.mainTopics) ? home.mainTopics : [],
      heatingTopics: Array.isArray(home.heatingTopics) ? home.heatingTopics : [],
      coolingTopics: Array.isArray(home.coolingTopics) ? home.coolingTopics : [],
      dailyFocus: home.dailyFocus ?? null,
      marketPulse: Array.isArray(home.marketPulse) ? home.marketPulse : [],
      opportunities: Array.isArray(home.opportunities) ? home.opportunities : [],
      marketOverview: home.marketOverview ?? null,
    },
    metadata: {
      ...metadata,
      reason: publication.reason,
    },
  };
}

export async function fetchTodayHomeResource(options: {
  baseUrl?: string | null;
  fetchImpl?: FetchLike;
  signal?: AbortSignal;
  previewEnabled?: boolean;
} = {}): Promise<TodayHomeResource> {
  const baseUrl = options.baseUrl?.trim() || getFormalApiBaseUrl();
  if (!baseUrl) {
    return errorTodayHomeResource("尚未設定 FastAPI origin；Today Home 暫不可用。");
  }

  try {
    const client = createTopicPilotClient({
      baseUrl,
      ...(options.fetchImpl ? { fetchImpl: options.fetchImpl } : {}),
    });
    const home = await client.getHome({ signal: options.signal });
    return mapHomeToTodayHomeResource(home, options.previewEnabled ?? TODAY_MAINLINES_PREVIEW_ENABLED);
  } catch (error) {
    if (options.signal?.aborted) {
      return errorTodayHomeResource("Today Home 請求已取消。");
    }
    return errorTodayHomeResource(error instanceof Error ? error.message : "無法讀取 Today Home 資料。");
  }
}

export function useTodayHomeResource(): TodayHomeLoadState {
  const [loading, setLoading] = useState(true);
  const [resource, setResource] = useState<TodayHomeResource>(() => loadingTodayHomeResource());

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    void fetchTodayHomeResource({ signal: controller.signal }).then((next) => {
      if (!active) return;
      setResource(next);
      setLoading(false);
    });
    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  return { loading, resource };
}
