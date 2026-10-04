import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Topic Detail uses research-workspace reading order and formal identity boundaries", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  for (const marker of ["今日判讀", "強度與結構", "正式成分與關聯股票", "題材生命週期", "題材介紹", "歷史走勢與輪動"]) {
    assert.match(page, new RegExp(marker));
  }
  assert.match(page, /publication\.identity/);
  assert.match(page, /publication\.hierarchy/);
  assert.match(page, /aria-labelledby="topic-v1-members-title"/);
  assert.ok(page.lastIndexOf("<TodayJudgementSection") < page.lastIndexOf("<TopicStatusSection"));
  assert.ok(page.lastIndexOf("<TopicStatusSection") < page.lastIndexOf("<ConstituentsSection"));
  assert.ok(page.lastIndexOf("<FormalLifecycle") < page.lastIndexOf("<ConstituentsSection"));
});

test("Topic Detail preserves mixed formal/deferred structure fields without browser derivation", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  assert.match(page, /topic\.status\.find/);
  assert.match(page, /publication\.participation/);
  assert.match(page, /尚未提供/);
  assert.match(page, /formalAbsoluteScore\(topic\)/);
  assert.doesNotMatch(page, /calculate.*score|derive.*grade|strengthScore\s*[+*/-]|topic\.score\s*\?\?/i);
});

test("Shadow is displayable while unavailable Lifecycle states remain fail closed", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  assert.match(page, /lifecycleStageForDetail/);
  assert.match(page, /lifecycleStatusLabel/);
  assert.match(page, /dataStatus/);
  assert.match(page, /尚未可安全呈現/);
  assert.match(page, /leader_change_pct/);
  assert.match(page, /PROXY evidence only/);
  assert.doesNotMatch(page, /function LifecyclePreview/);
  assert.doesNotMatch(page, /getTopicOverviewLifecycle|derive.*lifecycle/i);
});

test("Constituents stay relation-ordered and do not become browser-ranked leaders", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  assert.match(page, /publication\.relations/);
  assert.match(page, /publication\.leaderCore/);
  assert.match(page, /角色直接沿用 relation API/);
  assert.match(page, /visible\.map/);
  assert.doesNotMatch(page, /topic\.constituents\.sort\(/);
  assert.doesNotMatch(page, /leaderScore|breadthRatio\s*[+*/-]/i);
});

test("Preview and API error boundaries remain explicit", async () => {
  const [page, api, css] = await Promise.all([
    read("components/v2/TopicDetailPage.tsx"),
    read("lib/topic-api.ts"),
    read("globals.css"),
  ]);
  assert.match(page, /source === "synthetic-snapshot"/);
  assert.match(page, /Preview 不提供正式歷史序列/);
  assert.match(page, /resource\?\.source === "unavailable"/);
  assert.match(api, /source: "unavailable", data: null, error/);
  assert.match(css, /tp-topic-v1-section/);
  assert.match(css, /@media\(max-width:720px\)/);
});
