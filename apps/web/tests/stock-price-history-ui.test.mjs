import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const [api, panel, drawer, topic, css] = await Promise.all([
  readFile(new URL("../app/lib/stock-api.ts", import.meta.url), "utf8"),
  readFile(new URL("../app/components/v2/StockPriceHistoryPanel.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/components/v2/StockEncyclopediaDrawer.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/components/v2/TopicDetailPage.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
]);

const historyClient = api.slice(api.indexOf("export async function fetchFormalStockHistory"));

test("history client uses the generated V2 contract and a bounded request", () => {
  assert.match(historyClient, /StockHistoryRead/);
  assert.match(historyClient, /\/api\/v2\/stocks\/\$\{encodeURIComponent\(symbol\)\}\/price-history/);
  assert.match(historyClient, /from: "2000-01-01"/);
  assert.match(historyClient, /to: "2100-01-01"/);
  assert.match(historyClient, /limit: "200"/);
  assert.match(historyClient, /signal: options\.signal/);
  assert.doesNotMatch(historyClient, /\/api\/v1\/|synthetic-snapshot|legacy|fetchFormalStock\(/);
});

test("history panel exposes all formal states and keeps source/disclosure facts visible", () => {
  for (const state of ["LOADING", "AVAILABLE", "EMPTY", "UNAVAILABLE", "ERROR"]) {
    assert.match(panel, new RegExp(`"${state}"`));
  }
  for (const marker of ["data-history-status", "returnedFrom", "returnedTo", "asOf", "freshnessState", "latestObservedAt", "latestRetrievedAt", "sourceCode", "adjustmentState", "原始交易價格／未套用除權息調整"]) {
    assert.match(panel, new RegExp(marker));
  }
  assert.match(panel, /Preview, mock, and legacy data are not used/);
  assert.match(panel, /items\.map/);
  assert.doesNotMatch(panel, /\?\?\s*0|\|\|\s*0/);
});

test("history loading is stale-safe and API errors do not fall back", () => {
  assert.match(panel, /new AbortController\(\)/);
  assert.match(panel, /let active = true/);
  assert.match(panel, /if \(!active\) return/);
  assert.match(panel, /controller\.abort\(\)/);
  assert.doesNotMatch(`${historyClient}\n${panel}`, /fetchFormalStock\(|\/api\/v1\//);
});

test("history is mounted additively in the shared Drawer and protects existing surfaces", () => {
  assert.match(drawer, /StockPriceHistoryPanel/);
  assert.match(drawer, /symbol=\{displayStock\.code\}/);
  assert.match(drawer, /market=\{displayStock\.market\}/);
  assert.match(drawer, /isPreview=\{displayStock\.isPreview === true\}/);
  assert.match(drawer, /presentation/);
  assert.match(drawer, /FavoriteStar/);
  assert.match(topic, /StockEncyclopediaDrawer/);
  assert.match(topic, /presentation="inline"/);
  for (const className of ["tp-stock-encyclopedia-drawer--push", "tp-stock-encyclopedia-drawer--inline", "tp-stock-history-table"]) {
    assert.match(css, new RegExp(className.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
});

test("browser history surface remains render-only", () => {
  assert.doesNotMatch(panel, /\bMA\d+\b|\b(?:RSI|MACD|ATR|momentum|turnover|resistance)\b|volume\s*ratio/i);
  assert.doesNotMatch(panel, /close\s*[-+*/]\s*(?:close|previous)|volume\s*[-+*/]\s*(?:volume|close)/i);
  assert.doesNotMatch(panel, /Math\.(?:min|max)|\.sort\(/);
});
