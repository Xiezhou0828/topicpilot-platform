import type { components } from "./schema";

export interface RequestInitLike {
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export type FetchLike = (input: string, init?: RequestInitLike) => Promise<Response>;

export declare class TopicPilotProblem extends Error {
  readonly status: number;
  readonly type: string;
  readonly title: string;
  readonly detail: string;
  readonly instance: string | null;
}

export interface TopicPilotClient {
  getDataStatus(init?: RequestInitLike): Promise<components["schemas"]["DataStatus"]>;
  getHome(init?: RequestInitLike): Promise<components["schemas"]["HomeResponse"]>;
  getTopicCatalog(
    query?: { asOf?: string | null; limit?: number; offset?: number },
    init?: RequestInitLike,
  ): Promise<components["schemas"]["TopicMinimumReadPage"]>;
  getTopicCatalogDetail(
    slug: string,
    query?: { asOf?: string | null },
    init?: RequestInitLike,
  ): Promise<components["schemas"]["TopicMinimumRead"]>;
  getCurrentTopicSnapshot(
    slug: string,
    query?: { asOf?: string | null },
    init?: RequestInitLike,
  ): Promise<components["schemas"]["TopicCurrentSnapshotRead"]>;
  getTopicSnapshotHistory(
    slug: string,
    query?: {
      asOf?: string | null;
      from?: string | null;
      to?: string | null;
      limit?: number;
      offset?: number;
    },
    init?: RequestInitLike,
  ): Promise<components["schemas"]["TopicSnapshotHistoryReadPage"]>;
  getStocks(
    page?: { limit?: number; offset?: number },
    init?: RequestInitLike,
  ): Promise<components["schemas"]["Page_StockSummary_"]>;
  getStock(
    code: string,
    init?: RequestInitLike,
  ): Promise<components["schemas"]["StockResponse"]>;
  getTopics(
    page?: { limit?: number; offset?: number },
    init?: RequestInitLike,
  ): Promise<components["schemas"]["Page_TopicSummary_"]>;
}

export declare function createTopicPilotClient(options: {
  baseUrl: string;
  fetchImpl?: FetchLike;
}): TopicPilotClient;
