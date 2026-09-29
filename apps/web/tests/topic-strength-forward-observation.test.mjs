import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const root = process.cwd();
const detail = readFileSync(join(root, "app/components/v2/TopicDetailPage.tsx"), "utf8");
const topicApi = readFileSync(join(root, "app/lib/topic-api.ts"), "utf8");
const generated = readFileSync(join(root, "app/lib/generated-api.d.ts"), "utf8");

test("Topic detail presents the backend Owner-seeded V0 read model", () => {
  for (const token of [
    "ownerSeededV0",
    "forwardObservation",
    "今日強度",
    "生命週期",
    "Absolute",
    "Relative",
    "觀察中",
    "data-checkpoint-status",
  ]) {
    assert.match(detail, new RegExp(token));
  }
  assert.match(topicApi, /item\.ownerSeededV0/);
  assert.match(topicApi, /item\.forwardObservation/);
  assert.match(generated, /TopicOwnerSeededV0Read/);
  assert.match(generated, /TopicForwardObservationRead/);
});

test("Topic detail does not reproduce frozen policy threshold logic", () => {
  assert.doesNotMatch(detail, /\b(?:82|62)\b/);
  assert.doesNotMatch(detail, /MAIN_RISE.*(?:threshold|>=|<=)/i);
  assert.doesNotMatch(detail, /CORE.*(?:breadth|threshold).*\d/i);
});
