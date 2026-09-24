import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("catalog model keeps Parent/Leaf semantics separate from Leaf state", async () => {
  const source = await read("lib/topic-api.ts");
  assert.match(source, /export type TopicCatalogNode/);
  assert.match(source, /export type TopicLeafState/);
  assert.match(source, /kind: TopicKind/);
  assert.match(source, /parents: TopicHierarchyNode\[\]/);
  assert.match(source, /children: TopicHierarchyNode\[\]/);
  assert.match(source, /catalog\.kind === "PARENT"/);
  assert.match(source, /snapshotAvailabilityReason/);
});

test("catalog composition preserves identity when Leaf state is unavailable", async () => {
  const source = await read("lib/topic-api.ts");
  assert.match(source, /const stateBySlug = new Map/);
  assert.match(source, /stateBySlug\.get\(catalog\.slug\) \?\? null/);
  assert.match(source, /catalogResult\.source !== "api"/);
  assert.match(source, /summaryFromCatalog\(catalog, stateBySlug/);
  assert.match(source, /catalog\.currentFormalSnapshot\.availability\.state/);
  assert.match(source, /Topic Catalog identity read model is unavailable/);
});

test("list surfaces use canonical parents and exclude parents from market lanes", async () => {
  const page = await read("components/v2/TopicListPage.tsx");
  assert.match(page, /function isLeafTopic/);
  assert.match(page, /filter\(isLeafTopic\)/);
  assert.match(page, /topic\.hierarchy\.parents\.length/);
  assert.match(page, /parent\.hierarchy\.children/);
  assert.match(page, /全部題材（Leaf 題材）/);
  assert.match(page, /Leaf 題材/);
  assert.match(page, /Parent Topic/);
});

test("detail surfaces preserve Parent NOT_APPLICABLE and Leaf formal state boundaries", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  assert.match(page, /function TopicHierarchySection/);
  assert.match(page, /function ParentTopicState/);
  assert.match(page, /Snapshot NOT_APPLICABLE/);
  assert.match(page, /topic\.kind === "PARENT"/);
  assert.match(page, /topic\.lifecycle &&/);
  assert.match(page, /正式成分與關聯股票/);
  assert.match(page, /不以名稱或 groupName 推導關係/);
});

test("formal frontend remains fail closed and does not infer hierarchy from groupName", async () => {
  const [source, page] = await Promise.all([
    read("lib/topic-api.ts"),
    read("components/v2/TopicListPage.tsx"),
  ]);
  assert.match(source, /production 不使用 Preview 題材清單替代/);
  assert.match(source, /source === "unavailable"/);
  assert.match(source, /前端不自行補值/);
  assert.doesNotMatch(page, /topic\.topicType !== "MAJOR_GROUP"/);
  assert.match(page, /topic\.kind === "LEAF"/);
});
