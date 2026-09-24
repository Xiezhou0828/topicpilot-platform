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

test("Today Market Overview renders backend-owned official index and turnover fields", async () => {
  const [adapter, page, fields] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
    read("lib/today-market-fields.ts"),
  ]);
  for (const field of ["dataStatus", "trackedStockCount", "trackedTopicCount", "marketHealth", "source"]) {
    const pattern = field === "marketHealth"
      ? /value\?\.marketHealth/
      : new RegExp(`value\\.${field}|data\?\\.${field}`);
    assert.match(adapter, pattern);
  }
  assert.match(fields, /overview\.indices/);
  assert.match(fields, /overview\.turnover/);
  for (const field of ["advance", "decline", "flat", "net"]) {
    assert.match(page, new RegExp(`health\\.${field}`));
  }
  assert.doesNotMatch(page, /health\.unavailable/);
  for (const field of ["indexCode", "indexName", "changePct", "tradingDate", "asOf", "currency", "unit", "scale"]) {
    assert.match(`${adapter}\n${page}\n${fields}`, new RegExp(field));
  }
  assert.doesNotMatch(`${adapter}\n${page}\n${fields}`, /marketRadar|aggregate instruments|market scoring|bullish|bearish|market narrative|indices\\.reduce|turnover\\.reduce/i);
  assert.doesNotMatch(page, /mockMarketMetrics|useSnapshot|liveBreadth/);
});

test("Today Market Overview preserves publication states and fails closed", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(adapter, /state: TodayHomePublicationState/);
  assert.match(adapter, /市場資料尚未完整/);
  assert.match(adapter, /state === "PREVIEW" && !previewEnabled/);
  assert.match(adapter, /state === "UNAVAILABLE"/);
  assert.match(page, /resource\.state !== "FORMAL"/);
  assert.match(page, /市場廣度目前尚未提供/);
  assert.doesNotMatch(`${adapter}\n${page}`, /API error[\s\S]{0,120}mock|fallback hardcoded/i);
});
