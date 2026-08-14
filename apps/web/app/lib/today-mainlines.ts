"use client";

import {
  fetchTodayHomeResource,
  mapHomeToTodayHomeResource,
  TODAY_MAINLINES_PREVIEW_ENABLED,
  useTodayHomeResource,
  type HomeResponse,
  type HomeDailyFocus,
  type HomeRotationTopic,
  type TodayHomePublicationState,
  type TodayHomeResource,
} from "./today-home";

export type { HomeResponse } from "./today-home";
export { TODAY_MAINLINES_PREVIEW_ENABLED } from "./today-home";
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

export type TodayDailyFocusResource = {
  state: TodayHomePublicationState;
  data: HomeDailyFocus | null;
  dataDate: string | null;
  asOf: string | null;
  source: string | null;
  mode: string | null;
  temporary: boolean | null;
  reason: string | null;
};

export type TodayMainlinesResource = {
  state: TodayMainlinesState;
  data: TodayHomeResource["sections"]["mainTopics"];
  dataDate: string | null;
  asOf: string | null;
  source: string | null;
  classification: string | null;
  qualityStatus: string | null;
  reason: string | null;
  dailyFocus: TodayDailyFocusResource;
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
  if (resource.transportState !== "READY") return "UNAVAILABLE";
  if (resource.publicationState === "FORMAL") return "FORMAL";
  if (resource.publicationState === "PREVIEW" && previewEnabled) return "PREVIEW";
  return "UNAVAILABLE";
}

function metadata(resource: TodayHomeResource) {
  return {
    dataDate: resource.metadata.dataDate,
    asOf: resource.metadata.asOf,
    source: resource.metadata.source,
    classification: resource.metadata.classification,
    qualityStatus: resource.metadata.status,
  };
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
    dataDate: data?.dataDate ?? null,
    asOf: shared.asOf,
    source: data?.source ?? shared.source,
    mode: data?.mode ?? null,
    temporary: typeof data?.temporary === "boolean" ? data.temporary : null,
  };

  if (!isHomeDailyFocus(data)) {
    return {
      state: "UNAVAILABLE",
      data: null,
      ...dailyMetadata,
      reason: "Home.dailyFocus is incomplete; Today Market Story is unavailable.",
    };
  }

  let state: TodayHomePublicationState = resource.publicationState;
  if (state === "PREVIEW" && !previewEnabled) state = "UNAVAILABLE";
  if (state === "FORMAL" && data.temporary) state = "TEMPORARY";

  if (state === "UNAVAILABLE") {
    return {
      state,
      data: null,
      ...dailyMetadata,
      reason: resource.metadata.reason ?? "Formal Today Market Story is not ready; non-formal data is hidden.",
    };
  }

  return {
    state,
    data,
    ...dailyMetadata,
    reason: state === "FORMAL"
      ? null
      : resource.metadata.reason ?? "Home.dailyFocus is temporary and is not formal production insight.",
  };
}

function mapRotation(
  resource: TodayHomeResource,
  data: HomeRotationTopic[],
  direction: "heating" | "cooling",
  previewEnabled: boolean,
): TodayRotationResource {
  const state = stateFromHomeResource(resource, previewEnabled);
  const section = direction === "heating" ? "heatingTopics" : "coolingTopics";
  const shared = metadata(resource);

  if (data.length === 0) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...shared,
      reason: `Home.${section} is empty; Today rotation is unavailable.`,
    };
  }

  if (!data.every(isHomeRotationTopic)) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...shared,
      reason: `Home.${section} has incomplete fields; Today rotation is unavailable.`,
    };
  }

  if (state === "UNAVAILABLE") {
    return {
      state,
      data: [],
      ...shared,
      reason: resource.metadata.reason ?? "Formal Today rotation data is not ready; non-formal data is hidden.",
    };
  }

  return {
    state,
    data,
    ...shared,
    reason: state === "PREVIEW" ? resource.metadata.reason : null,
  };
}

export function toTodayMainlinesResource(
  resource: TodayHomeResource,
  previewEnabled = TODAY_MAINLINES_PREVIEW_ENABLED,
): TodayMainlinesResource {
  const shared = metadata(resource);
  const dailyFocus = mapDailyFocus(resource, previewEnabled);
  const heating = mapRotation(resource, resource.sections.heatingTopics, "heating", previewEnabled);
  const cooling = mapRotation(resource, resource.sections.coolingTopics, "cooling", previewEnabled);
  const state = stateFromHomeResource(resource, previewEnabled);
  const data = resource.sections.mainTopics;

  if (data.length === 0) {
    return {
      state: "UNAVAILABLE",
      data: [],
      ...shared,
      reason: resource.metadata.reason ?? "Home.mainTopics is empty; Today mainlines are unavailable.",
      dailyFocus,
      heating,
      cooling,
    };
  }

  if (state === "UNAVAILABLE") {
    return {
      state,
      data: [],
      ...shared,
      reason: resource.metadata.reason ?? "Formal Today mainlines are not ready; non-formal data is hidden.",
      dailyFocus,
      heating,
      cooling,
    };
  }

  return {
    state,
    data,
    ...shared,
    reason: state === "PREVIEW" ? resource.metadata.reason : null,
    dailyFocus,
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
