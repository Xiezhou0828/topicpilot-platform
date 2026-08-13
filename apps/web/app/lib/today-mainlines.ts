"use client";

import { useEffect, useState } from "react";
import {
  createTopicPilotClient,
  type FetchLike,
} from "../../../../packages/api-client/src/client.mjs";
import type { components } from "./generated-api";
import { getFormalApiBaseUrl } from "./stock-api";

type HomeResponse = components["schemas"]["HomeResponse"];
type HomeTopicCard = components["schemas"]["HomeTopicCard"];
type HomeRotationTopic = components["schemas"]["HomeRotationTopic"];

export type TodayMainlinesState = "FORMAL" | "PREVIEW" | "UNAVAILABLE";

export type TodayRotationResource = {
  state: TodayMainlinesState;
  data: HomeRotationTopic[];
  dataDate: string | null;
  asOf: string | null;
  source: string | null;
  classification: string | null;
  qualityStatus: string | null;
  reason: string | null;
};

export type TodayMainlinesResource = {
  state: TodayMainlinesState;
  data: HomeTopicCard[];
  dataDate: string | null;
  asOf: string | null;
  source: string | null;
  classification: string | null;
  qualityStatus: string | null;
  reason: string | null;
  heating: TodayRotationResource;
  cooling: TodayRotationResource;
};

export type TodayMainlinesLoadState = {
  loading: boolean;
  resource: TodayMainlinesResource;
};

export const TODAY_MAINLINES_PREVIEW_ENABLED = process.env.NEXT_PUBLIC_ENABLE_TODAY_MAINLINES_PREVIEW === "true";

function emptyResource(reason: string): TodayMainlinesResource {
  const emptyRotation: TodayRotationResource = {
    state: "UNAVAILABLE",
    data: [],
    dataDate: null,
    asOf: null,
    source: null,
    classification: null,
    qualityStatus: null,
    reason,
  };
  return {
    state: "UNAVAILABLE",
    data: [],
    dataDate: null,
    asOf: null,
    source: null,
    classification: null,
    qualityStatus: null,
    reason,
    heating: emptyRotation,
    cooling: emptyRotation,
  };
}

function metadataFromHome(home: HomeResponse) {
  const quality = home.dataQuality;
  return {
    dataDate: home.mainTopics?.find((topic) => topic.dataDate)?.dataDate
      ?? home.marketOverview.dataDate
      ?? null,
    asOf: home.asOf ?? home.generatedAt ?? home.marketOverview.updatedAt ?? null,
    source: quality.source || home.marketOverview.source || null,
    classification: quality.classification ?? null,
    qualityStatus: quality.status || home.marketOverview.dataStatus || null,
  };
}

function hasNonFormalSource(home: HomeResponse): boolean {
  const quality = home.dataQuality;
  const sectionMarkers = [
    ...(quality.temporarySections ?? []).filter((section) => /main.?topics|mainlines|heating.?topics|cooling.?topics|rotation/i.test(section)),
    ...(quality.missingSections ?? []).filter((section) => /main.?topics|mainlines|heating.?topics|cooling.?topics|rotation/i.test(section)),
  ];
  const sourceMarkers = [
    quality.classification,
    quality.source,
    quality.status,
    home.marketOverview.dataStatus,
    ...sectionMarkers,
  ].filter(Boolean).join(" ");
  return /SYNTHETIC|FIXTURE|DEMO|SHADOW|PARTIAL|UNAVAILABLE|NOT[_ -]?AVAILABLE|TEMPORARY|G1|DOWNSTREAM/i.test(sourceMarkers);
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

function mapHomeToTodayRotation(
  home: HomeResponse,
  data: HomeRotationTopic[],
  metadata: ReturnType<typeof metadataFromHome>,
  previewEnabled: boolean,
  direction: "heating" | "cooling",
): TodayRotationResource {
  const section = direction === "heating" ? "heatingTopics" : "coolingTopics";

  if (data.length === 0) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...metadata,
      reason: `Home.${section} is empty; Today rotation is unavailable.`,
    };
  }

  if (!data.every(isHomeRotationTopic)) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...metadata,
      reason: `Home.${section} has incomplete fields; Today rotation is unavailable.`,
    };
  }

  if (hasUnknownPublicationMetadata(home)) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...metadata,
      reason: "Home publication metadata is incomplete; Today rotation is unavailable.",
    };
  }

  if (!hasNonFormalSource(home)) {
    return { state: "FORMAL", data, ...metadata, reason: null };
  }

  if (previewEnabled) {
    return {
      state: "PREVIEW",
      data,
      ...metadata,
      reason: "Home rotation is not a formal source; Preview is explicitly enabled.",
    };
  }

  return {
    state: "UNAVAILABLE",
    data: [],
    ...metadata,
    reason: "Formal Today rotation data is not ready; non-formal data is hidden.",
  };
}

export function mapHomeToTodayMainlines(
  home: HomeResponse,
  previewEnabled = TODAY_MAINLINES_PREVIEW_ENABLED,
): TodayMainlinesResource {
  const data = Array.isArray(home.mainTopics) ? home.mainTopics : [];
  const metadata = metadataFromHome(home);
  const heating = mapHomeToTodayRotation(
    home,
    Array.isArray(home.heatingTopics) ? home.heatingTopics : [],
    metadata,
    previewEnabled,
    "heating",
  );
  const cooling = mapHomeToTodayRotation(
    home,
    Array.isArray(home.coolingTopics) ? home.coolingTopics : [],
    metadata,
    previewEnabled,
    "cooling",
  );

  if (data.length === 0) {
    return {
      ...emptyResource("後端 Home.mainTopics 目前沒有可發布的題材主線。"),
      ...metadata,
      heating,
      cooling,
    };
  }

  if (!hasNonFormalSource(home)) {
    return {
      state: "FORMAL",
      data,
      ...metadata,
      reason: null,
      heating,
      cooling,
    };
  }

  if (previewEnabled) {
    return {
      state: "PREVIEW",
      data,
      heating,
      cooling,
      ...metadata,
      reason: "目前 Home 來源仍是合成、暫時或未完成資料；本區以明確 Preview 狀態展示。",
    };
  }

  return {
    state: "UNAVAILABLE",
    data: [],
    ...metadata,
    reason: "Today 主線後端資料尚未達正式發布條件。",
    heating,
    cooling,
  };
}

export async function fetchTodayMainlines(options: {
  baseUrl?: string | null;
  fetchImpl?: FetchLike;
  signal?: AbortSignal;
  previewEnabled?: boolean;
} = {}): Promise<TodayMainlinesResource> {
  const baseUrl = options.baseUrl?.trim() || getFormalApiBaseUrl();
  if (!baseUrl) {
    return emptyResource("尚未設定 FastAPI origin，Today 主線暫不可用。");
  }

  try {
    const client = createTopicPilotClient({
      baseUrl,
      ...(options.fetchImpl ? { fetchImpl: options.fetchImpl } : {}),
    });
    const home = await client.getHome({ signal: options.signal });
    return mapHomeToTodayMainlines(home, options.previewEnabled ?? TODAY_MAINLINES_PREVIEW_ENABLED);
  } catch (error) {
    if (options.signal?.aborted) {
      return emptyResource("Today 主線請求已取消。");
    }
    return emptyResource(error instanceof Error ? error.message : "無法讀取 Today 主線資料。");
  }
}

export function useTodayMainlines(): TodayMainlinesLoadState {
  const [loading, setLoading] = useState(true);
  const [resource, setResource] = useState<TodayMainlinesResource>(() => emptyResource("正在讀取後端主線資料。"));

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    void fetchTodayMainlines({ signal: controller.signal }).then((next) => {
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
