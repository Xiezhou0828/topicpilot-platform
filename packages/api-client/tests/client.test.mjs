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
