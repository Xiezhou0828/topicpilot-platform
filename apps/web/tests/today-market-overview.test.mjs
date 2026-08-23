import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Today Market Overview reuses the single Home resource and generated contract", async () => {
  const [home, adapter, page] = await Promise.all([
    read("lib/today-home.ts"),
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(home, /marketOverview: home\.marketOverview \?\? null/);
  assert.match(adapter, /HomeMarketOverview/);
  assert.match(adapter, /marketOverview: TodayMarketOverviewResource/);
  assert.match(adapter, /mapMarketOverview\(resource, previewEnabled\)/);
  assert.match(page, /resource\.marketOverview/);
  assert.doesNotMatch(page, /createTopicPilotClient|getTodayHome|getTodayMarket/);
  assert.equal((home.match(/client\.getHome\(/g) ?? []).length, 1);
});

test("Today Market Overview renders backend fields without market aggregation", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  for (const field of ["dataStatus", "trackedStockCount", "trackedTopicCount", "marketHealth", "source"]) {
    const pattern = field === "marketHealth"
      ? /value\?\.marketHealth/
      : new RegExp(`value\\.${field}|data\\?\\.${field}`);
    assert.match(adapter, pattern);
  }
  for (const field of ["advance", "decline", "flat", "unavailable"]) {
    assert.match(page, new RegExp(`health\\.${field}`));
  }
  assert.doesNotMatch(`${adapter}\n${page}`, /marketIndices|marketRadar|aggregate instruments|market scoring|bullish|bearish|market narrative/i);
  assert.doesNotMatch(page, /mockMarketMetrics|useSnapshot|liveBreadth/);
});

test("Today Market Overview preserves publication states and fails closed", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(adapter, /state: TodayHomePublicationState/);
  assert.match(adapter, /Home\.marketOverview is incomplete/);
  assert.match(adapter, /state === "PREVIEW" && !previewEnabled/);
  assert.match(adapter, /state === "UNAVAILABLE"/);
  assert.match(page, /resource\.state !== "FORMAL"/);
  assert.match(page, /市場廣度資料目前不可用/);
  assert.doesNotMatch(`${adapter}\n${page}`, /API error[\s\S]{0,120}mock|fallback hardcoded/i);
});
