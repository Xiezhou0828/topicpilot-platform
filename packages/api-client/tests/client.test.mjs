import assert from "node:assert/strict";
import test from "node:test";

import { TopicPilotProblem, createTopicPilotClient } from "../src/client.mjs";

test("typed client returns a successful paginated response", async () => {
  const fetchImpl = async (url, init) => {
    assert.equal(url, "https://api.example/api/v1/stocks?limit=2&offset=1");
    assert.equal(init.headers.Accept, "application/json");
    return new Response(
      JSON.stringify({ items: [{ code: "DEMO-A1" }], total: 4, limit: 2, offset: 1 }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  };
  const client = createTopicPilotClient({ baseUrl: "https://api.example/", fetchImpl });

  const page = await client.getStocks({ limit: 2, offset: 1 });

  assert.equal(page.total, 4);
  assert.equal(page.items[0].code, "DEMO-A1");
});

test("typed client returns the generated HomeResponse contract", async () => {
  const fetchImpl = async (url, init) => {
    assert.equal(url, "https://api.example/api/v2/home");
    assert.equal(init.headers.Accept, "application/json");
    return new Response(
      JSON.stringify({
        contractVersion: "home-v1",
        asOf: null,
        generatedAt: null,
        marketOverview: { dataDate: null, dataStatus: "UNAVAILABLE", latestSnapshotTime: null, marketHealth: null, source: "TEST", trackedStockCount: 0, trackedTopicCount: 0, updatedAt: null },
        dailyFocus: { mode: "UNAVAILABLE", temporary: false, headline: "", bullets: [], dataDate: null, source: "TEST" },
        dataQuality: { status: "UNAVAILABLE", source: "TEST", classification: null },
        mainTopics: [{ slug: "ai-server", name: "AI Server", grade: null, currentState: null, dataDate: null, favorite: false, stockCount: 0, strength: null, summary: "" }],
      }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  };
  const client = createTopicPilotClient({ baseUrl: "https://api.example", fetchImpl });

  const home = await client.getHome();

  assert.equal(home.mainTopics[0].slug, "ai-server");
});

test("typed client reads the formal institutional-flow route with explicit bounds", async () => {
  const fetchImpl = async (url, init) => {
    assert.equal(
      url,
      "https://api.example/api/v2/market/institutional-flow?limit=20&market=TPE&asOf=2026-09-15&from=2026-09-01&to=2026-09-15",
    );
    assert.equal(init.headers.Accept, "application/json");
    return new Response(JSON.stringify({ status: "UNAVAILABLE", markets: [] }), { status: 200 });
  };
  const client = createTopicPilotClient({ baseUrl: "https://api.example", fetchImpl });

  const flow = await client.getInstitutionalFlow({
    market: "TPE",
    asOf: "2026-09-15",
    from: "2026-09-01",
    to: "2026-09-15",
    limit: 20,
  });
  assert.equal(flow.status, "UNAVAILABLE");
});

test("typed client exposes all WS-B Topic catalog read routes", async () => {
  const requests = [];
  const fetchImpl = async (url) => {
    requests.push(url);
    return new Response(JSON.stringify({ items: [], total: 0, limit: 200, offset: 0, asOf: "2026-08-31" }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };
  const client = createTopicPilotClient({ baseUrl: "https://api.example", fetchImpl });

  await client.getTopicCatalog({ asOf: "2026-08-31", limit: 20, offset: 5 });
  await client.getTopicCatalogDetail("ai/server", { asOf: "2026-08-31" });
  await client.getCurrentTopicSnapshot("ai/server", { asOf: "2026-08-31" });
  await client.getTopicSnapshotHistory("ai/server", {
    asOf: "2026-08-31",
    from: "2026-08-07",
    to: "2026-08-31",
    limit: 10,
    offset: 2,
  });

  assert.deepEqual(requests, [
    "https://api.example/api/v2/topic-catalog?limit=20&offset=5&asOf=2026-08-31",
    "https://api.example/api/v2/topic-catalog/ai%2Fserver?asOf=2026-08-31",
    "https://api.example/api/v2/topic-catalog/ai%2Fserver/snapshot?asOf=2026-08-31",
    "https://api.example/api/v2/topic-catalog/ai%2Fserver/snapshots?limit=10&offset=2&asOf=2026-08-31&from=2026-08-07&to=2026-08-31",
  ]);
});

test("typed client raises the normalized problem response", async () => {
  const fetchImpl = async () => new Response(
    JSON.stringify({
      type: "https://topicpilot.example/problems/not-found",
      title: "Resource not found",
      status: 404,
      detail: "Stock was not found",
      instance: "/api/v1/stocks/UNKNOWN",
    }),
    { status: 404, headers: { "content-type": "application/problem+json" } },
  );
  const client = createTopicPilotClient({ baseUrl: "https://api.example", fetchImpl });

  await assert.rejects(
    client.getStock("UNKNOWN"),
    (error) => error instanceof TopicPilotProblem
      && error.status === 404
      && error.type.endsWith("/not-found"),
  );
});

test("typed client requests stock institutional-flow evidence with market identity", async () => {
  const fetchImpl = async (url, init) => {
    assert.equal(
      url,
      "https://api.example/api/v2/stocks/2330/institutional-flow?limit=200&market=TPE&asOf=2026-09-16",
    );
    assert.equal(init.headers.Accept, "application/json");
    return new Response(
      JSON.stringify({ contractVersion: "fund-b.stock-institutional-flow.v1", status: "OK" }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  };
  const client = createTopicPilotClient({ baseUrl: "https://api.example", fetchImpl });

  const response = await client.getStockInstitutionalFlow(
    "2330",
    { market: "TPE", asOf: "2026-09-16" },
  );

  assert.equal(response.status, "OK");
});
