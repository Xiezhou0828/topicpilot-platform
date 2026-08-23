import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("topic catalog consumes backend lifecycle stages and keeps non-stage states visible", async () => {
  const [api, page] = await Promise.all([
    read("lib/topic-api.ts"),
    read("components/v2/TopicListPage.tsx"),
  ]);
  assert.match(api, /lifecycle\?: TopicLifecycle/);
  assert.match(page, /lifecycleStageAvailable/);
  assert.match(page, /lifecycleForTopic\(topic, preview\)/);
  assert.match(page, /formalLifecycleStage/);
  assert.match(page, /lifecycleStatusLabel/);
  assert.match(page, /data-lifecycle-status/);
});

test("topic detail displays backend lifecycle/shadow data and has explicit pending states", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  assert.match(page, /function FormalLifecycle/);
  assert.match(page, /lifecycleStageAvailable/);
  assert.match(page, /dataStatus/);
  assert.match(page, /StrengthEvidenceSection/);
  assert.match(page, /leader_change_pct/);
  assert.match(page, /<EmptyState title=/);
  assert.match(page, /canonical backend Lifecycle read model/);
  assert.match(page, /publication\?\.lifecycle/);
});
