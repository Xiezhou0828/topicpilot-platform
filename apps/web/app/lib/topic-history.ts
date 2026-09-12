import { createTopicPilotClient, type FetchLike } from "../../../../packages/api-client/src/client.mjs";
import type { components } from "./generated-api";
import { catalogBaseUrl, type CatalogTopic } from "./topic-catalog";

export type FormalSnapshot = components["schemas"]["TopicFormalSnapshotRead"];
export type HistoryPage = components["schemas"]["TopicSnapshotHistoryReadPage"];
export type HistoryResource =
  | { state: "LOADING"; data: null }
  | { state: "ERROR" | "UNAVAILABLE"; data: null; reason: string }
  | { state: "AVAILABLE" | "EMPTY" | "UNAVAILABLE" | "NOT_APPLICABLE"; data: HistoryPage };

export const HISTORY_LIMIT = 100;
const FORMAL_BOUNDARY = "2026-08-07";

export function historyWindow(asOf: string): { from: string; to: string } {
  const date = new Date(`${asOf}T00:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(asOf) || !Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== asOf) throw new Error("Invalid asOf");
  date.setUTCDate(date.getUTCDate() - 366);
  const from = date.toISOString().slice(0, 10);
  return { from: asOf < FORMAL_BOUNDARY ? asOf : from < FORMAL_BOUNDARY ? FORMAL_BOUNDARY : from, to: asOf };
}

// Check transport identity/publication only. The backend owns row eligibility and all metrics.
export function isFormalSnapshot(row: FormalSnapshot, topic: CatalogTopic): boolean {
  return row.topicId === topic.topicId && row.topicSlug === topic.slug
    && row.snapshotDate <= topic.asOf && Boolean(row.publication?.snapshotIdentity)
    && row.source?.authority === "topicpilot.topic_snapshots"
    && row.publication.mode === "FORMAL" && row.publication.state === "PUBLISHED"
    && row.publication.membershipMode === "PIT_FORMAL" && row.publication.finalityState === "FINAL";
}

export function currentSnapshot(topic: CatalogTopic): FormalSnapshot | null {
  const current = topic.currentFormalSnapshot;
  return topic.kind === "LEAF" && current.availability.state === "AVAILABLE"
    && current.availability.asOf === topic.asOf && current.snapshot && isFormalSnapshot(current.snapshot, topic)
    ? current.snapshot : null;
}

export async function loadTopicHistory(
  topic: CatalogTopic,
  offset = 0,
  options: { baseUrl?: string | null; fetchImpl?: FetchLike; signal?: AbortSignal } = {},
): Promise<HistoryResource> {
  if (topic.kind === "PARENT") return { state: "NOT_APPLICABLE", data: {
    items: [], total: 0, limit: HISTORY_LIMIT, offset: 0, asOf: topic.asOf,
    availability: { state: "NOT_APPLICABLE", asOf: topic.asOf, reasonCode: "PARENT_TOPIC_NOT_ELIGIBLE_FOR_FORMAL_SNAPSHOT", reason: "Parent 僅供階層導航，正式歷史屬於 Leaf。" },
  } };
  const baseUrl = options.baseUrl === undefined ? catalogBaseUrl() : options.baseUrl;
  if (!baseUrl) return { state: "UNAVAILABLE", data: null, reason: "尚未設定題材資料來源。" };
  try {
    const window = historyWindow(topic.asOf);
    const client = createTopicPilotClient({ baseUrl, fetchImpl: options.fetchImpl });
    const data = await client.getTopicSnapshotHistory(topic.slug, { asOf: topic.asOf, ...window, limit: HISTORY_LIMIT, offset }, { signal: options.signal });
    if (data.asOf !== topic.asOf || data.availability.asOf !== topic.asOf || !Array.isArray(data.items)) throw new Error("History envelope mismatch");
    if (data.availability.state !== "AVAILABLE") {
      // Preserve backend availability and reason; distinguish a known no-publication result from authority failure.
      const empty = data.availability.state === "UNAVAILABLE" && data.availability.reasonCode === "FORMAL_SNAPSHOT_NOT_PUBLISHED" && data.items.length === 0 && data.total === 0;
      return { state: empty ? "EMPTY" : data.availability.state, data };
    }
    const current = currentSnapshot(topic);
    if (topic.currentFormalSnapshot.availability.state === "AVAILABLE" && !current) throw new Error("Current snapshot mismatch");
    if (!Number.isInteger(data.limit) || data.limit < 1 || data.limit > HISTORY_LIMIT || data.offset !== offset
      || !Number.isInteger(data.total) || data.total < 0 || data.items.length > data.limit) throw new Error("History pagination mismatch");
    if (data.items.some((row) => !isFormalSnapshot(row, topic) || row.snapshotDate < window.from || row.snapshotDate > window.to
      || (current && row.snapshotDate === current.snapshotDate && (row.publication.snapshotIdentity !== current.publication.snapshotIdentity
        || row.publication.correctionSequence !== current.publication.correctionSequence || row.asOfAt !== current.asOfAt
        || row.source.lineageHash !== current.source.lineageHash || row.publication.membershipSnapshotHash !== current.publication.membershipSnapshotHash)))) throw new Error("History row mismatch");
    return { state: data.items.length ? "AVAILABLE" : "EMPTY", data };
  } catch {
    return { state: "ERROR", data: null, reason: "正式歷史讀取失敗或與目前題材資料不一致，請重新載入題材。" };
  }
}
