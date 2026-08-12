import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("formal topic catalog consumes backend lifecycle only when shadow data is available", async () => {
  const [api, page] = await Promise.all([
    read("lib/topic-api.ts"),
    read("components/v2/TopicListPage.tsx"),
  ]);
  assert.match(api, /lifecycle\?: TopicLifecycle/);
  assert.match(page, /\.dataStatus !== "SHADOW_AVAILABLE"/);
  assert.match(page, /lifecycleForTopic\(topic, preview\)/);
  assert.match(page, /formalLifecycleStage/);
});

test("formal topic detail has an explicit pending state and no client derivation", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  assert.match(page, /function FormalLifecycle/);
  assert.match(page, /dataStatus !== "SHADOW_AVAILABLE"/);
  assert.match(page, /<EmptyState title=/);
  assert.match(page, /backend authority|dataStatus/);
  assert.match(page, /topic\.lifecycle\.dataStatus === "SHADOW_AVAILABLE"/);
});
