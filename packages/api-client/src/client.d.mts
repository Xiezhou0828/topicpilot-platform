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
