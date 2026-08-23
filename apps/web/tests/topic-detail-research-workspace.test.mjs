import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Topic Detail uses research-workspace reading order and formal identity boundaries", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  for (const marker of ["題材研究工作台", "今日狀態", "核心結構三格", "正式成分與關聯股票", "題材生命週期", "題材說明", "層級與相關題材", "歷史走勢與輪動"]) {
    assert.match(page, new RegExp(marker));
  }
  assert.match(page, /publication\.identity/);
  assert.match(page, /publication\.hierarchy/);
  assert.match(page, /aria-labelledby="stocks-title"/);
  assert.ok(page.lastIndexOf("<TodayStatusSection") < page.lastIndexOf("<TopicStatusSection"));
  assert.ok(page.lastIndexOf("<TopicStatusSection") < page.lastIndexOf("<ConstituentsSection"));
  assert.ok(page.lastIndexOf("<ConstituentsSection") < page.lastIndexOf("<FormalLifecycle"));
});

test("Topic Detail preserves mixed formal/deferred structure fields without browser derivation", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  assert.match(page, /CORE_STRUCTURE_KEYS/);
  assert.match(page, /item\?\.state\s*\?/);
  assert.match(page, /publication\.participation/);
  assert.match(page, /尚未提供/);
  assert.match(page, /scoreLabel\(topic\.score\)/);
  assert.doesNotMatch(page, /calculate.*score|derive.*grade|strengthScore\s*[+*/-]|topic\.score\s*\?\?/i);
});

test("Shadow is displayable while unavailable Lifecycle states remain fail closed", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  assert.match(page, /lifecycleStageAvailable/);
  assert.match(page, /lifecycleStatusLabel/);
  assert.match(page, /INSUFFICIENT_DATA/);
  assert.match(page, /FAIL_CLOSED/);
  assert.match(page, /前端 fail closed/);
  assert.match(page, /leader_change_pct/);
  assert.match(page, /PROXY evidence only/);
  assert.doesNotMatch(page, /function LifecyclePreview/);
  assert.doesNotMatch(page, /getTopicOverviewLifecycle|derive.*lifecycle/i);
});

test("Constituents stay relation-ordered and do not become browser-ranked leaders", async () => {
  const page = await read("components/v2/TopicDetailPage.tsx");
  assert.match(page, /publication\.relations/);
  assert.match(page, /publication\.leaderCore/);
  assert.match(page, /後端關係角色/);
  assert.match(page, /stocks\.map/);
  assert.doesNotMatch(page, /stocks\.(sort|slice)\(/);
  assert.doesNotMatch(page, /leaderScore|breadthRatio\s*[+*/-]/i);
});

test("Preview and API error boundaries remain explicit", async () => {
  const [page, api, css] = await Promise.all([
    read("components/v2/TopicDetailPage.tsx"),
    read("lib/topic-api.ts"),
    read("globals.css"),
  ]);
  assert.match(page, /resource\?\.source === "synthetic-snapshot"/);
  assert.match(page, /previewDisclosure\("events"/);
  assert.match(page, /resource\?\.source === "unavailable"/);
  assert.match(api, /source: "unavailable", data: null, error/);
  assert.match(css, /tp-topic-research-grid/);
  assert.match(css, /@media \(max-width: 760px\)/);
});
