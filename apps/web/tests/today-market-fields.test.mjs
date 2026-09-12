import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Today official market consumer uses every generated index and turnover field", async () => {
  const [fields, page, home] = await Promise.all([
    read("lib/today-market-fields.ts"),
    read("components/v2/TodayMarketPage.tsx"),
    read("lib/today-home.ts"),
  ]);
  for (const field of ["indices", "turnover", "indexCode", "indexName", "value", "change", "changePct", "tradingDate", "asOf", "status", "currency", "unit", "scale"]) {
    assert.match(`${fields}\n${page}`, new RegExp(field));
  }
  assert.match(home, /components\["schemas"\]\["HomeResponse"\]/);
  assert.match(page, /OfficialMarketFields/);
});

test("Today official market consumer keeps EOD, trading-date and as-of semantics explicit", async () => {
  const [fields, page] = await Promise.all([
    read("lib/today-market-fields.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(page, /收盤後 EOD/);
  assert.match(page, /不代表盤中即時/);
  assert.match(page, /交易日/);
  assert.match(page, /截至/);
  assert.match(fields, /Asia\/Taipei/);
  assert.match(fields, /formatMarketDate/);
  assert.match(fields, /formatMarketAsOf/);
  assert.doesNotMatch(`${fields}\n${page}`, /Date\.now\(|new Date\(\)\.toISOString\(\)|intraday|live quote/i);
});

test("Today official market consumer has truthful normal, weekend, null, partial and unavailable paths", async () => {
  const [fields, page, adapter] = await Promise.all([
    read("lib/today-market-fields.ts"),
    read("components/v2/TodayMarketPage.tsx"),
    read("lib/today-mainlines.ts"),
  ]);
  const cases = {
    normalOfficialEod: ["marketFactIsAvailable", "資料可用", "formatMarketNumber"],
    weekendAsOf: ["tradingDate", "formatMarketDate", "formatMarketAsOf"],
    nullValue: ["尚未提供", "value: number | null", "value === null"],
    partial: ["PARTIAL", "部分資料", "marketFactState"],
    unavailable: ["UNAVAILABLE", "尚未提供", "正式成交金額尚未提供"],
    error: ["ERROR", "讀取失敗", "state: \"ERROR\""],
  };
  for (const [name, markers] of Object.entries(cases)) {
    for (const marker of markers) {
      assert.match(`${fields}\n${page}\n${adapter}`, new RegExp(marker), `${name} should remain represented`);
    }
  }
  assert.doesNotMatch(`${fields}\n${page}`, /turnover\s*\+|indices\.reduce|turnover\.reduce|\.sort\(/i);
  assert.match(adapter, /state: "UNAVAILABLE"/);
});

test("Today official market consumer never falls back to legacy or demo market values", async () => {
  const [fields, page, home] = await Promise.all([
    read("lib/today-market-fields.ts"),
    read("components/v2/TodayMarketPage.tsx"),
    read("lib/today-home.ts"),
  ]);
  assert.doesNotMatch(`${fields}\n${page}\n${home}`, /mockMarketMetrics|mockMarketIndices|buildHomeFromMock|useSnapshot|fallback hardcoded/i);
  assert.match(home, /client\.getHome\(\{ signal: options\.signal \}\)/);
  assert.match(home, /return errorTodayHomeResource\(error instanceof Error/);
});
