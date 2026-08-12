import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("V2 Home uses the frozen TodayMarket hierarchy", async () => {
  const [root, v2, home] = await Promise.all([
    read("page.tsx"),
    read("components/v2/V2Page.tsx"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(root, /V2Page path="\/"/);
  assert.match(v2, /<TodayMarketPage \/>/);
  for (const marker of ["tp-home-overview-card", "market-overview-title", "tp-home-story-card", "mainline-title", "events-title", "rotation-title", "opportunities-title"]) {
    assert.match(home, new RegExp(marker));
  }
  assert.match(home, /const opportunities = \[/);
  assert.match(home, /useTodayMainlines/);
  assert.doesNotMatch(home, /marketDecision/);
});

test("V2 Home displays canonical market metrics without browser recomputation", async () => {
  const home = await read("components/v2/TodayMarketPage.tsx");
  assert.match(home, /const mockMarketMetrics: MarketMetric\[\] = \[/);
  assert.match(home, /const liveWeighted/);
  assert.match(home, /const liveOtc/);
  assert.match(home, /const liveBreadth/);
  assert.match(home, /liveMetric\(liveWeighted/);
  assert.match(home, /liveMetric\(liveOtc/);
  assert.match(home, /liveBreadth\?\.advance/);
  assert.match(home, /marketMetrics\.slice\(0, 3\)/);
  assert.match(home, /marketMetrics\.slice\(3\)/);
  assert.doesNotMatch(home, /evidence\.count\s*\/\s*evidence\.denominator/);
});

test("V2 Home keeps bounded rotation and Opportunity teaser surfaces", async () => {
  const home = await read("components/v2/TodayMarketPage.tsx");
  assert.match(home, /const warmingTopics = \[/);
  assert.match(home, /const coolingTopics = \[/);
  assert.match(home, /const opportunities = \[/);
  assert.match(home, /warmingTopics\.map/);
  assert.match(home, /coolingTopics\.map/);
  assert.match(home, /href="\/topics"/);
  assert.match(home, /href="\/opportunities"/);
  assert.match(home, /只呈現研究入口/);
  assert.doesNotMatch(home, /topWarming|topCooling|topicChange.*sort/);
});

test("market route redirects to the frozen Home market anchor", async () => {
  const [nav, redirect] = await Promise.all([read("components/AppNav.tsx"), read("market/page.tsx")]);
  assert.doesNotMatch(nav, /市場雷達/);
  assert.match(redirect, /redirect\("\/#market-overview"\)/);
});

test("V2 Home exposes explicit freshness and Preview/unavailable semantics", async () => {
  const [home, foundation] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read("components/v2/V2Foundation.tsx"),
  ]);
  assert.match(home, /isSyntheticPreview/);
  assert.match(home, /canUseBackendData/);
  assert.match(home, /freshnessLabel/);
  assert.match(home, /status\.dataState === "LIVE"/);
  assert.match(home, /status\.dataState === "SNAPSHOT"/);
  assert.match(home, /sourceLabel/);
  assert.match(foundation, /state === "UNAVAILABLE"/);
  assert.match(foundation, /state === "UNAVAILABLE"/);
  assert.match(foundation, /tp-state-\$\{/);
});

test("market decision adapter and bundle wiring remain explicit for legacy compatibility", async () => {
  const [types, adapter, source] = await Promise.all([
    read("lib/types.ts"),
    read("lib/snapshot-adapter.ts"),
    read("lib/data-source.ts"),
  ]);
  assert.match(types, /RawMarketDecision/);
  assert.match(types, /MarketDecisionView/);
  assert.match(adapter, /export function toMarketDecision/);
  assert.match(source, /marketDecision: toMarketDecision\(raw\)/);
});

test("V2 Home focus CSS is responsive", async () => {
  const css = await read("globals.css");
  for (const selector of [".tp-home-overview-card", ".tp-home-rotation-grid", ".tp-home-mainline-grid", "@media (max-width: 820px)"]) {
    assert.match(css, new RegExp(selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
});

test("V2 Home does not expose the legacy strategy candidate drilldown", async () => {
  const [home, stocks] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read("components/v2/StockExplorerPage.tsx"),
  ]);
  assert.doesNotMatch(home, /strategyRegistry|strategyCandidates|selectedStrategy|useSearchParams/);
  assert.match(home, /mainlines\.resource\.data\.map/);
  assert.match(home, /href=\{`\/topics\/\$\{topic\.slug\}`\}/);
  assert.match(stocks, /fetchFormalStocks/);
  assert.match(stocks, /tp-stock-grid/);
  assert.match(stocks, /tp-stock-advanced-toggle/);
  assert.doesNotMatch(home, /Buy|Sell|Strong Buy|Entry Score|stop-loss/);
});

test("V2 Home keeps strategy semantics out of presentation copy", async () => {
  const home = await read("components/v2/TodayMarketPage.tsx");
  assert.match(home, /mainlines\.resource\.data\.map/);
  assert.match(home, /GradeChip grade=\{topic\.grade \?\? "—"\}/);
  assert.match(home, /tp-home-topic-state/);
  assert.match(home, /tp-home-topic-detail/);
  assert.match(home, /只呈現研究入口，不在首頁完成推薦分析/);
  assert.doesNotMatch(home, /candidate\.sort|strategyId|rankScore|targetPrice/);
});

test("public Home preserves the environment boundary without exposing MA20 slope copy", async () => {
  const [home, adapter] = await Promise.all([read("components/v2/TodayMarketPage.tsx"), read("lib/snapshot-adapter.ts")]);
  assert.match(adapter, /const sub = env/);
  assert.doesNotMatch(adapter, /const sub[\s\S]{0,160}MA20 slope/);
  assert.doesNotMatch(home, /MA20 slope/);
});
