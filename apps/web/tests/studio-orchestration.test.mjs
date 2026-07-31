import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

test("studio client uses only an explicitly configured public endpoint", async () => {
  const client = await readFile(new URL("../app/studio/studio-client.ts", import.meta.url), "utf8");
  assert.match(client, /NEXT_PUBLIC_AI_STUDIO_ORCHESTRATION_URL/);
  assert.match(client, /公開作品未連接私人 AI 服務/);
  assert.match(client, /method: "POST"/);
  assert.doesNotMatch(client, /\.workers\.dev|GEMINI_API_KEY|OPENROUTER_API_KEY|Authorization/);
});

test("studio request builder uses backend canonical character bindings", async () => {
  const client = await readFile(new URL("../app/studio/studio-client.ts", import.meta.url), "utf8");
  for (const binding of ["coda", "mori", "prism", "volt"]) assert.match(client, new RegExp(`${binding}:`));
  for (const strategy of ["momentum-execution", "risk-invalidation", "theme-catalyst", "event-reversal"]) assert.match(client, new RegExp(strategy));
  assert.match(client, /bindingId: character\.id/);
});

test("studio client validates append-only phases and safe statuses", async () => {
  const client = await readFile(new URL("../app/studio/studio-client.ts", import.meta.url), "utf8");
  for (const phase of ["INDEPENDENT", "DEBATE", "FINAL"]) assert.match(client, new RegExp(phase));
  for (const status of ["DEMO", "MOCK", "LIVE", "RATE_LIMITED", "UNAVAILABLE", "ERROR"]) assert.match(client, new RegExp(status));
  assert.match(client, /append-only/);
  assert.match(client, /eventId/);
  assert.match(client, /researchOnly/);
});

test("studio page maps remote event metadata and never uses remote events as performance", async () => {
  const page = await readFile(new URL("../app/studio/page.tsx", import.meta.url), "utf8");
  assert.match(page, /fetchDiscussion/);
  assert.match(page, /providerId/);
  assert.match(page, /modelId/);
  assert.match(page, /重新嘗試/);
  assert.match(page, /沒有收到正式 AI 結論/);
  assert.match(page, /!orchestration\.events\.length/);
});
