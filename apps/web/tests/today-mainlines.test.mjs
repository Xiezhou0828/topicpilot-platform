import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Today mainlines use the generated HomeResponse runtime path", async () => {
  const [adapter, home, client, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("lib/today-home.ts"),
    read(new URL("../../../packages/api-client/src/client.mjs", app)),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(home, /components\["schemas"\]\["HomeResponse"\]/);
  assert.match(home, /client\.getHome\(\{ signal: options\.signal \}\)/);
  assert.match(client, /getHome: \(init\) => request\("\/api\/v2\/home", init\)/);
  assert.match(adapter, /useTodayHomeResource/);
  assert.match(page, /useTodayMainlines/);
  assert.doesNotMatch(page, /const mainlines = \[/);
});

test("Today mainlines preserve backend order and never compute ranking in the browser", async () => {
  const [adapter, home] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("lib/today-home.ts"),
  ]);
  assert.match(home, /mainTopics: Array\.isArray\(home\.mainTopics\) \? home\.mainTopics : \[\]/);
  assert.match(adapter, /const data = resource\.sections\.mainTopics/);
  assert.match(adapter, /data,/);
  assert.match(adapter, /data: TodayHomeResource\["sections"\]\["mainTopics"\]/);
  assert.match(adapter, /topicSlug/);
  assert.doesNotMatch(adapter, /\.sort\(/);
  assert.doesNotMatch(home, /\.sort\(/);
  assert.doesNotMatch(`${adapter}\n${home}`, /rank|ranking|strengthScore|lifecycle/);
});

test("Today mainlines fail closed and only expose Preview explicitly", async () => {
  const [adapter, home, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("lib/today-home.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(adapter, /TODAY_MAINLINES_PREVIEW_ENABLED/);
  assert.match(adapter, /state: "UNAVAILABLE"/);
  assert.match(home, /state: "PREVIEW"/);
  assert.match(home, /return errorTodayHomeResource\(error instanceof Error/);
  assert.doesNotMatch(`${adapter}\n${home}`, /mock|fallback/i);
  assert.match(page, /mainlines\.resource\.state === "UNAVAILABLE"/);
  assert.match(page, /mainlines\.resource\.state === "PREVIEW"/);
  assert.doesNotMatch(page, /mainlines\s*=\s*\[/);
});

test("Today mainline cards navigate with the backend topic slug and preserve null semantics", async () => {
  const page = await read("components/v2/TodayMarketPage.tsx");
  assert.match(page, /key=\{topic\.slug\}/);
  assert.match(page, /GradeChip grade=\{topic\.grade \?\? "—"\}/);
  assert.match(page, /topic\.currentState \?\?/);
  assert.match(page, /href=\{`\/topics\/\$\{topic\.slug\}`\}/);
});

test("Today heating and cooling reuse the Home response and preserve backend order", async () => {
  const [home, page] = await Promise.all([
    read("lib/today-home.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(home, /heatingTopics: Array\.isArray\(home\.heatingTopics\) \? home\.heatingTopics : \[\]/);
  assert.match(home, /coolingTopics: Array\.isArray\(home\.coolingTopics\) \? home\.coolingTopics : \[\]/);
  assert.equal((home.match(/client\.getHome\(/g) ?? []).length, 1);
  assert.doesNotMatch(home, /heatingTopics[\s\S]{0,400}\.sort\(/);
  assert.doesNotMatch(home, /coolingTopics[\s\S]{0,400}\.sort\(/);
  assert.match(page, /mainlines\.resource\.heating/);
  assert.match(page, /mainlines\.resource\.cooling/);
  assert.match(page, /topic\.topicSlug/);
  assert.match(page, /href=\{`\/topics\/\$\{topic\.topicSlug\}`\}/);
  assert.doesNotMatch(page, /const warmingTopics\s*=/);
  assert.doesNotMatch(page, /const coolingTopics\s*=/);
});

test("Today heating and cooling fail closed and only expose Preview explicitly", async () => {
  const adapter = await read("lib/today-mainlines.ts");
  assert.match(adapter, /function mapRotation/);
  assert.match(adapter, /resource\.publicationState === "FORMAL"/);
  assert.match(adapter, /resource\.publicationState === "PREVIEW"/);
  assert.match(adapter, /state: "UNAVAILABLE"/);
  assert.match(adapter, /data\.length === 0/);
  assert.match(adapter, /data\.every\(isHomeRotationTopic\)/);
  assert.match(adapter, /目前沒有足夠的 14 日資料/);
  assert.doesNotMatch(adapter, /fallback|rank|ranking|direction inference|strength calculation/i);
});
