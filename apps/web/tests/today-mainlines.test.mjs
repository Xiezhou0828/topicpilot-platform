import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Today mainlines use the generated HomeResponse runtime path", async () => {
  const [adapter, client, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read(new URL("../../../packages/api-client/src/client.mjs", app)),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(adapter, /components\["schemas"\]\["HomeResponse"\]/);
  assert.match(adapter, /client\.getHome\(\{ signal: options\.signal \}\)/);
  assert.match(client, /getHome: \(init\) => request\("\/api\/v2\/home", init\)/);
  assert.match(page, /useTodayMainlines/);
  assert.doesNotMatch(page, /const mainlines = \[/);
});

test("Today mainlines preserve backend order and never compute ranking in the browser", async () => {
  const adapter = await read("lib/today-mainlines.ts");
  assert.match(adapter, /const data = Array\.isArray\(home\.mainTopics\) \? home\.mainTopics : \[\]/);
  assert.match(adapter, /data,/);
  assert.doesNotMatch(adapter, /\.sort\(/);
  assert.doesNotMatch(adapter, /rank|ranking|strengthScore|lifecycle/);
});

test("Today mainlines fail closed and only expose Preview explicitly", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(adapter, /TODAY_MAINLINES_PREVIEW_ENABLED/);
  assert.match(adapter, /state: "PREVIEW"/);
  assert.match(adapter, /state: "UNAVAILABLE"/);
  assert.match(adapter, /return emptyResource\(error instanceof Error/);
  assert.doesNotMatch(adapter, /mock|fallback/i);
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
