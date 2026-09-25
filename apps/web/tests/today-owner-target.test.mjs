import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Today mainline cards expose formal topic direction and evidence metrics", async () => {
  const page = await read("components/v2/TodayMarketPage.tsx");
  assert.match(page, /topic\.currentState/);
  assert.match(page, /rankingEvidence/);
  assert.match(page, /averageChange/);
  assert.match(page, /observedStockCount/);
  assert.match(page, /平均日變化/);
  assert.match(page, /觀測檔數/);
  assert.doesNotMatch(page, /Relation Weight|relationWeight/);
});

test("Today rotation lists use formal current metrics and preserve 14-day delta", async () => {
  const [page, schema] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read(new URL("../../../services/api/src/topicpilot_api/schemas.py", app)),
  ]);
  assert.match(page, /topic\.averageDailyChange/);
  assert.match(page, /topic\.observedStockCount/);
  assert.match(page, /topic\.strengthDelta/);
  assert.match(schema, /average_daily_change: float \| None/);
  assert.match(schema, /observed_stock_count: int \| None/);
});

test("Today composition keeps the investor-first section order", async () => {
  const page = await read("components/v2/TodayMarketPage.tsx");
  const composition = page.slice(page.indexOf("export default function TodayMarketPage"));
  const order = [
    "<MarketOverviewCard",
    "<MarketSignalCards",
    "<MainlineCards",
    "<TopicPulseTicker",
    "<RotationCard",
  ].map((marker) => composition.indexOf(marker));
  assert.ok(order.every((index) => index >= 0));
  assert.deepEqual(order, [...order].sort((a, b) => a - b));
});
