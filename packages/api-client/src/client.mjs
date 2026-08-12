export class TopicPilotProblem extends Error {
  constructor(problem) {
    super(problem.detail ?? problem.title ?? `TopicPilot API returned HTTP ${problem.status}`);
    this.name = "TopicPilotProblem";
    this.status = problem.status;
    this.type = problem.type ?? "about:blank";
    this.title = problem.title ?? "API request failed";
    this.detail = problem.detail ?? this.message;
    this.instance = problem.instance ?? null;
  }
}

export function createTopicPilotClient({ baseUrl, fetchImpl = globalThis.fetch }) {
  if (!baseUrl) throw new TypeError("baseUrl is required");
  if (typeof fetchImpl !== "function") throw new TypeError("fetchImpl must be a function");
  const origin = baseUrl.replace(/\/$/, "");

  async function request(path, init = {}) {
    const response = await fetchImpl(`${origin}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...init.headers },
    });
    const body = await response.json();
    if (!response.ok) {
      throw new TopicPilotProblem({ ...body, status: body.status ?? response.status });
    }
    return body;
  }

  return Object.freeze({
    getDataStatus: (init) => request("/api/v1/meta/data-status", init),
    getHome: (init) => request("/api/v2/home", init),
    getStocks: ({ limit = 50, offset = 0 } = {}, init) =>
      request(`/api/v1/stocks?limit=${limit}&offset=${offset}`, init),
    getStock: (code, init) => request(`/api/v1/stocks/${encodeURIComponent(code)}`, init),
    getTopics: ({ limit = 50, offset = 0 } = {}, init) =>
      request(`/api/v1/topics?limit=${limit}&offset=${offset}`, init),
  });
}
