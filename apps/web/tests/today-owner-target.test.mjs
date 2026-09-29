import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Today mainline cards expose formal Lifecycle and Strength metrics", async () => {
  const page = await read("components/v2/TodayMarketPage.tsx");
  assert.match(page, /topic\.lifecycle/);
  assert.match(page, /topic\.absoluteScore/);
  assert.match(page, /topic\.relativeScore/);
  assert.doesNotMatch(page, /topic\.currentState/);
  assert.doesNotMatch(page, /averageChange|平均日變化/);
  assert.doesNotMatch(page, /Relation Weight|relationWeight/);
});

test("Today rotation lists use formal absolute strength and five-session baseline", async () => {
  const [page, schema] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read(new URL("../../../services/api/src/topicpilot_api/schemas.py", app)),
  ]);
  assert.match(page, /topic\.absoluteScore/);
  assert.match(page, /topic\.baselineMedian/);
  assert.match(page, /topic\.strengthDelta/);
  assert.match(schema, /baseline_median: float \| None/);
  assert.match(schema, /observed_stock_count: int \| None/);
});

test("Today composition keeps the investor-first section order", async () => {
  const page = await read("components/v2/TodayMarketPage.tsx");
  const composition = page.slice(page.indexOf("export default function TodayMarketPage"));
  const order = [
    "<MarketOverviewCard",
    "<MarketSignalCards",
    "<MainlineCards",
    "<TopicPulsePanel",
    "<RotationCard",
  ].map((marker) => composition.indexOf(marker));
  assert.ok(order.every((index) => index >= 0));
  assert.deepEqual(order, [...order].sort((a, b) => a - b));
});
