import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Topic Experience V1 has one shared formal presentation boundary", async () => {
  const presentation = await read("lib/topic-presentation.ts");
  assert.match(presentation, /ABSOLUTE: \{ S: "極強", A: "強勢", B: "中性", D: "弱勢" \}/);
  assert.match(presentation, /RELATIVE: \{ S: "大幅領先", A: "領先", B: "接近市場", D: "落後" \}/);
  assert.match(presentation, /if \(stage === "BASE"\) return "尚未形成"/);
  assert.match(presentation, /case "SPROUTING": return "萌芽"/);
  assert.match(presentation, /topic\.formalStrength\?\.relative/);
});

test("Topic Overview is a formal map plus discoverable universe", async () => {
  const page = await read("components/v2/TopicListPage.tsx");
  assert.match(page, /ABSOLUTE/);
  assert.match(page, /RELATIVE/);
  assert.match(page, /MAX_VISIBLE_MAP_TOPICS = 3/);
  assert.match(page, /data-drawer-kind/);
  assert.match(page, /題材生命週期/);
  assert.match(page, /探索題材/);
  assert.match(page, /selectedParent/);
  assert.match(page, /lifecycleFilter/);
  assert.match(page, /useTopicFavoritesState/);
  assert.match(page, /getTopicKnowledge/);
  assert.doesNotMatch(page, /score\s*[<>]=?\s*\d+/);
});

test("Topic Detail keeps knowledge, formal history, exact members and folded diagnostics separate", async () => {
  const [page, knowledge, api] = await Promise.all([
    read("components/v2/TopicDetailPage.tsx"),
    read("lib/topic-knowledge.ts"),
    read("lib/topic-api.ts"),
  ]);
  for (const marker of ["今日判讀", "題材介紹", "強度與結構", "題材生命週期", "歷史走勢與輪動", "正式成分與關聯股票", "<details>", "Preview 不提供正式歷史序列"]) assert.match(page, new RegExp(marker));
  for (const header of ["股號", "股名", "角色", "今日漲跌幅"]) assert.match(page, new RegExp(`<th>${header}</th>`));
  assert.match(page, /fetchTopicHistory/);
  assert.match(api, /relativeScore: null/);
  assert.match(page, /href=\{`\/stocks\/\$\{member\.code\}`\}/);
  assert.match(knowledge, /TopicKnowledge/);
  assert.match(knowledge, /never owns membership/);
  assert.match(api, /\/api\/v2\/topic-catalog\/\$\{encodeURIComponent\(slug\)\}\/snapshots/);
});
