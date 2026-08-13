import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Daily Focus uses the shared TodayHomeResource and does not add a request", async () => {
  const [adapter, home, page, client] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("lib/today-home.ts"),
    read("components/v2/TodayMarketPage.tsx"),
    read(new URL("../../../packages/api-client/src/client.mjs", app)),
  ]);
  assert.match(home, /dailyFocus: home\.dailyFocus \?\? null/);
  assert.match(adapter, /dailyFocus: TodayDailyFocusResource/);
  assert.match(adapter, /mapDailyFocus\(resource, previewEnabled\)/);
  assert.match(page, /mainlines\.resource\.dailyFocus/);
  assert.equal((home.match(/client\.getHome\(/g) ?? []).length, 1);
  assert.doesNotMatch(`${adapter}\n${page}`, /getDailyFocus|getMarketStory|getHomeDailyFocus/);
  assert.match(client, /getHome: \(init\) => request\("\/api\/v2\/home", init\)/);
});

test("Daily Focus headline and bullets remain backend-owned and ordered", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(adapter, /data: HomeDailyFocus \| null/);
  assert.match(adapter, /const data = resource\.sections\.dailyFocus/);
  assert.match(page, /dailyFocus\.data\.headline/);
  assert.match(page, /dailyFocus\.data\.bullets\?\.map/);
  assert.doesNotMatch(`${adapter}\n${page}`, /dailyFocus[\s\S]{0,500}\.sort\(/);
  assert.doesNotMatch(page, /dailyFocus[^;\n]*(?:new Date|toLocaleString|reduce|sort)/i);
});

test("Daily Focus preserves mode, source, data date, as-of, and temporary metadata", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  for (const field of ["mode", "source", "dataDate", "asOf", "temporary"]) {
    assert.match(adapter, new RegExp(`${field}:`));
  }
  assert.match(page, /模式：\{mainlines\.resource\.dailyFocus\.mode\}/);
  assert.match(page, /來源：\{mainlines\.resource\.dailyFocus\.source\}/);
  assert.match(page, /資料日：\$\{mainlines\.resource\.dailyFocus\.dataDate\}/);
  assert.match(adapter, /state === "FORMAL" && data\.temporary/);
  assert.match(adapter, /state = "TEMPORARY"/);
});

test("Daily Focus exposes shared FORMAL, TEMPORARY, PREVIEW, and UNAVAILABLE semantics", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  for (const state of ["FORMAL", "TEMPORARY", "PREVIEW", "UNAVAILABLE"]) {
    assert.match(adapter, new RegExp(`state(?:\\s*[:=]|\\s*===)\\s*"${state}"`));
  }
  assert.match(page, /state === "TEMPORARY"/);
  assert.match(page, /state === "TEMPORARY" \? "TEMPORARY"/);
  assert.match(page, /state === "PREVIEW"/);
  assert.match(page, /state === "UNAVAILABLE"/);
});

test("Daily Focus fails closed for null, empty, incomplete, gated, and error states", async () => {
  const [adapter, page, home] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
    read("lib/today-home.ts"),
  ]);
  assert.match(adapter, /if \(!isHomeDailyFocus\(data\)\)/);
  assert.match(adapter, /value\.bullets\.length > 0/);
  assert.match(adapter, /value\.dataDate === null/);
  assert.match(adapter, /Home\.dailyFocus is incomplete/);
  assert.match(adapter, /state === "UNAVAILABLE"/);
  assert.match(home, /return errorTodayHomeResource\(error instanceof Error/);
  assert.doesNotMatch(page, /AI伺服器.*市場主線|BBU.*高檔分歧|機器人.*盤中快速升溫/);
  assert.doesNotMatch(page, /今天研究重心：觀察 AI 是否開始擴散/);
});

test("Daily Focus keeps TODAY-002 and TODAY-003 projections on the same resource", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(adapter, /dailyFocus/);
  assert.match(adapter, /mainTopics/);
  assert.match(adapter, /heatingTopics/);
  assert.match(adapter, /coolingTopics/);
  assert.match(page, /mainlines\.resource\.heating/);
  assert.match(page, /mainlines\.resource\.cooling/);
  assert.doesNotMatch(`${adapter}\n${page}`, /createTopicPilotClient|getTodayHome|getTodayMarket/);
});
