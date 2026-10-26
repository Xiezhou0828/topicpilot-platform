import {
  createTopicPilotClient,
  type FetchLike,
} from "../../../../packages/api-client/src/client.mjs";
import type { components } from "./generated-api";
import { getFormalApiBaseUrl } from "./stock-api";

export type FormalTopicSnapshot = components["schemas"]["TopicFormalSnapshotRead"];
export type FormalTopicSnapshotEnvelope = components["schemas"]["TopicCurrentSnapshotRead"];

export type FormalTopicSnapshotState = "LOADING" | "FORMAL" | "UNAVAILABLE" | "ERROR";

export type FormalTopicSnapshotMetadata = {
  snapshotDate: string | null;
  asOf: string | null;
  source: string | null;
  publicationStatus: string | null;
  publicationMode: string | null;
  publishedAt: string | null;
};

export type FormalTopicSnapshotResource = {
  state: FormalTopicSnapshotState;
  data: FormalTopicSnapshot | null;
  metadata: FormalTopicSnapshotMetadata;
  reason: string | null;
};

const EMPTY_METADATA: FormalTopicSnapshotMetadata = {
  snapshotDate: null,
  asOf: null,
  source: null,
  publicationStatus: null,
  publicationMode: null,
  publishedAt: null,
};

function hasText(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function metadataFromSnapshot(snapshot: FormalTopicSnapshot | null): FormalTopicSnapshotMetadata {
  if (!snapshot) return EMPTY_METADATA;
  return {
    snapshotDate: hasText(snapshot.snapshotDate) ? snapshot.snapshotDate : null,
    asOf: hasText(snapshot.asOfAt) ? snapshot.asOfAt : null,
    source: hasText(snapshot.source.sourceArtifactId)
      ? snapshot.source.sourceArtifactId
      : hasText(snapshot.source.sourceRunId)
        ? snapshot.source.sourceRunId
        : null,
    publicationStatus: hasText(snapshot.publication.state) ? snapshot.publication.state : null,
    publicationMode: hasText(snapshot.publication.mode) ? snapshot.publication.mode : null,
    publishedAt: hasText(snapshot.publication.publishedAt) ? snapshot.publication.publishedAt : null,
  };
}

function formalSnapshotReason(snapshot: FormalTopicSnapshot): string | null {
  if (snapshot.publication.mode !== "FORMAL") return "Topic Snapshot 尚未進入正式發布模式。";
  if (snapshot.publication.state !== "PUBLISHED") return "Topic Snapshot 尚未完成正式發布。";
  if (snapshot.publication.membershipMode !== "PIT_FORMAL") return "Topic Snapshot 缺少正式 PIT membership。";
  if (snapshot.publication.finalityState !== "FINAL") return "Topic Snapshot 尚未完成 finality。";
  if (!hasText(snapshot.topicId) || !hasText(snapshot.topicSlug) || !hasText(snapshot.publication.snapshotIdentity)) {
    return "Topic Snapshot 缺少正式 identity。";
  }
  if (!hasText(snapshot.source.lineageHash)) return "Topic Snapshot 缺少 lineage。";
  return null;
}

export function loadingFormalTopicSnapshotResource(): FormalTopicSnapshotResource {
  return { state: "LOADING", data: null, metadata: EMPTY_METADATA, reason: "正在讀取正式 Topic Snapshot。" };
}

export function unavailableFormalTopicSnapshotResource(
  reason: string,
  state: "UNAVAILABLE" | "ERROR" = "UNAVAILABLE",
): FormalTopicSnapshotResource {
  return { state, data: null, metadata: EMPTY_METADATA, reason };
}

export function toFormalTopicSnapshotResource(
  envelope: FormalTopicSnapshotEnvelope | null,
): FormalTopicSnapshotResource {
  if (!envelope || envelope.availability.state !== "AVAILABLE" || !envelope.snapshot) {
    return unavailableFormalTopicSnapshotResource(
      envelope?.availability.reason ?? "正式 Topic Snapshot 尚未提供。",
    );
  }
  const metadata = metadataFromSnapshot(envelope.snapshot);
  const reason = formalSnapshotReason(envelope.snapshot);
  if (reason) return { state: "UNAVAILABLE", data: null, metadata, reason };
  return { state: "FORMAL", data: envelope.snapshot, metadata, reason: null };
}

export async function fetchFormalTopicSnapshot(
  topicSlug: string,
  options: { baseUrl?: string | null; fetchImpl?: FetchLike; signal?: AbortSignal } = {},
): Promise<FormalTopicSnapshotResource> {
  const baseUrl = options.baseUrl?.trim() || getFormalApiBaseUrl();
  if (!baseUrl) return unavailableFormalTopicSnapshotResource("尚未設定正式 FastAPI origin；Topic Snapshot 暫不可用。");

  try {
    const client = createTopicPilotClient({
      baseUrl,
      ...(options.fetchImpl ? { fetchImpl: options.fetchImpl } : {}),
    });
    const envelope = await client.getCurrentTopicSnapshot(topicSlug, {}, { signal: options.signal });
    return toFormalTopicSnapshotResource(envelope);
  } catch (error) {
    if (options.signal?.aborted) return unavailableFormalTopicSnapshotResource("Topic Snapshot 請求已取消。");
    return unavailableFormalTopicSnapshotResource(
      error instanceof Error ? error.message : "無法讀取正式 Topic Snapshot。",
      "ERROR",
    );
  }
}

export function formalTopicSnapshotDisplay(resource: FormalTopicSnapshotResource): string {
  if (resource.state === "LOADING") return "讀取中";
  if (resource.state === "FORMAL") return "正式資料";
  return resource.state === "ERROR" ? "讀取失敗" : "尚未提供";
}

export { EMPTY_METADATA as EMPTY_FORMAL_TOPIC_SNAPSHOT_METADATA };
