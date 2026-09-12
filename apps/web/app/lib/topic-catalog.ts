import { createTopicPilotClient, type FetchLike } from "../../../../packages/api-client/src/client.mjs";
import type { components } from "./generated-api";

export type CatalogTopic = components["schemas"]["TopicMinimumRead"];
export type CatalogPage = components["schemas"]["TopicMinimumReadPage"];
export type CatalogAvailability = components["schemas"]["TopicAvailabilityRead"];
export type CatalogResource<T> =
  | { state: "LOADING"; data: null }
  | { state: "AVAILABLE"; data: T }
  | { state: "UNAVAILABLE" | "ERROR"; data: null; reason: string };

export function catalogBaseUrl(): string | null {
  const runtime = typeof document !== "undefined" ? document.documentElement.dataset.apiBaseUrl?.trim() : "";
  return (runtime || process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "").replace(/\/+$/, "") || null;
}

export async function loadCatalog(
  query: { slug?: string; asOf?: string; offset?: number },
  options: { baseUrl?: string | null; fetchImpl?: FetchLike; signal?: AbortSignal } = {},
): Promise<CatalogResource<CatalogTopic | CatalogPage>> {
  const baseUrl = options.baseUrl === undefined ? catalogBaseUrl() : options.baseUrl;
  if (!baseUrl) return { state: "UNAVAILABLE", data: null, reason: "尚未設定題材資料來源。" };
  try {
    const client = createTopicPilotClient({ baseUrl, fetchImpl: options.fetchImpl });
    const data = query.slug !== undefined
      ? await client.getTopicCatalogDetail(query.slug, { asOf: query.asOf }, { signal: options.signal })
      : await client.getTopicCatalog({ asOf: query.asOf, offset: query.offset, limit: 100 }, { signal: options.signal });
    return { state: "AVAILABLE", data };
  } catch {
    return { state: "ERROR", data: null, reason: "題材資料讀取失敗，請重試。" };
  }
}

export function catalogHref(slug: string | null, asOf?: string): string {
  const path = slug === null ? "/topics" : `/topics/${encodeURIComponent(slug)}`;
  return asOf ? `${path}?${new URLSearchParams({ asOf })}` : path;
}
