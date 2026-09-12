import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Topic adapter maps transport source to field-level publication states", async () => {
  const source = await read("lib/topic-api.ts");
  for (const state of ["FORMAL", "FORMAL_NOT_WIRED", "SHADOW", "TEMPORARY", "PREVIEW", "DEFERRED", "UNAVAILABLE", "CONTRACT_GAP"]) {
    assert.match(source, new RegExp(`"${state}"`));
  }
  assert.match(source, /export function getTopicPublication/);
  assert.match(source, /topic\.score === null \? "DEFERRED"/);
  assert.match(source, /topic\.grade === null \? "DEFERRED"/);
  assert.match(source, /API 只代表 transport path/);
});

test("Topic List exposes deferred grade and Lifecycle states without deriving them", async () => {
  const page = await read("components/v2/TopicListPage.tsx");
  assert.match(page, /getTopicPublication/);
  assert.match(page, /data-publication-state=\{disclosure\.state\}/);
  assert.match(page, /topic\.meta\.laneGrade \?\? <PublicationDisclosure disclosure=\{gradeDisclosure\}/);
  assert.match(page, /<TopicLifecycle topics=\{overviewTopics\} preview=\{previewMode\} source=\{resource\.source\}/);
  assert.doesNotMatch(page, /<DataState state="AVAILABLE" \/>/);
  assert.doesNotMatch(page, /getTopicOverviewMeta\([^\n]*true\)/);
});

test("Topic Detail discloses formal identity separately from unavailable domains", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  assert.match(page, /getTopicPublication/);
  assert.match(page, /publication\.source/);
  assert.match(page, /publication\.grade/);
  assert.match(page, /publication\.summary/);
  assert.match(page, /publication\.events/);
  assert.match(page, /publication\.opportunity/);
  assert.match(page, /function FormalLifecycle/);
  assert.match(page, /disclosure=\{disclosure\}/);
  assert.doesNotMatch(page, /getTopicOverviewMeta|derive.*lifecycle|calculate.*grade/i);
});

test("Configured Topic API errors remain unavailable instead of falling back to Preview", async () => {
  const source = await read("lib/topic-api.ts");
  assert.match(source, /source: "unavailable", data: null, error: result\.error/);
  assert.match(source, /topicPreviewEnabled\(\)/);
  assert.doesNotMatch(source, /return \{ source: "synthetic-snapshot", data: getPreviewTopicRotation\(\), error: result\.error/);
});
