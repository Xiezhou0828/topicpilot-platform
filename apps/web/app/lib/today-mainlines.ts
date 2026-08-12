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

export type TodayMainlinesState = "FORMAL" | "PREVIEW" | "UNAVAILABLE";

export type TodayMainlinesResource = {
  state: TodayMainlinesState;
  data: HomeTopicCard[];
  dataDate: string | null;
  asOf: string | null;
  source: string | null;
  classification: string | null;
  qualityStatus: string | null;
  reason: string | null;
};

export type TodayMainlinesLoadState = {
  loading: boolean;
  resource: TodayMainlinesResource;
};

export const TODAY_MAINLINES_PREVIEW_ENABLED = process.env.NEXT_PUBLIC_ENABLE_TODAY_MAINLINES_PREVIEW === "true";

function emptyResource(reason: string): TodayMainlinesResource {
  return {
    state: "UNAVAILABLE",
    data: [],
    dataDate: null,
    asOf: null,
    source: null,
    classification: null,
    qualityStatus: null,
    reason,
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
    ...(quality.temporarySections ?? []).filter((section) => /main.?topics|mainlines/i.test(section)),
    ...(quality.missingSections ?? []).filter((section) => /main.?topics|mainlines/i.test(section)),
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

export function mapHomeToTodayMainlines(
  home: HomeResponse,
  previewEnabled = TODAY_MAINLINES_PREVIEW_ENABLED,
): TodayMainlinesResource {
  const data = Array.isArray(home.mainTopics) ? home.mainTopics : [];
  const metadata = metadataFromHome(home);

  if (data.length === 0) {
    return {
      ...emptyResource("後端 Home.mainTopics 目前沒有可發布的題材主線。"),
      ...metadata,
    };
  }

  if (!hasNonFormalSource(home)) {
    return {
      state: "FORMAL",
      data,
      ...metadata,
      reason: null,
    };
  }

  if (previewEnabled) {
    return {
      state: "PREVIEW",
      data,
      ...metadata,
      reason: "目前 Home 來源仍是合成、暫時或未完成資料；本區以明確 Preview 狀態展示。",
    };
  }

  return {
    state: "UNAVAILABLE",
    data: [],
    ...metadata,
    reason: "Today 主線後端資料尚未達正式發布條件。",
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
