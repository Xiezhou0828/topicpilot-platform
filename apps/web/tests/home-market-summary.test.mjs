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
  assert.match(home, /useTodayMainlines/);
  assert.doesNotMatch(home, /marketDecision/);
});

test("V2 Home renders backend-owned Market Overview values without browser aggregation", async () => {
  const [home, adapter] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read("lib/today-mainlines.ts"),
  ]);
  assert.match(home, /resource\.marketOverview/);
  assert.match(home, /overview\.trackedStockCount/);
  assert.match(home, /overview\.trackedTopicCount/);
  assert.match(home, /health\.advance/);
  assert.match(home, /health\.decline/);
  assert.match(home, /health\.flat/);
  assert.match(adapter, /marketOverview: TodayMarketOverviewResource/);
  assert.match(adapter, /mapMarketOverview\(resource, previewEnabled\)/);
  assert.doesNotMatch(home, /mockMarketMetrics|marketIndices|marketRadar|liveBreadth|useSnapshot/);
  assert.doesNotMatch(home, /evidence\.count\s*\/\s*evidence\.denominator/);
});

test("V2 Home keeps bounded rotation and Opportunity teaser surfaces", async () => {
  const home = await read("components/v2/TodayMarketPage.tsx");
  assert.match(home, /mainlines\.resource\.heating/);
  assert.match(home, /mainlines\.resource\.cooling/);
  assert.match(home, /RotationCard/);
  assert.match(home, /href=\{`\/topics\/\$\{topic\.topicSlug\}`\}/);
  assert.match(home, /OpportunityTeaserCard/);
  assert.match(home, /mainlines\.resource\.opportunities/);
  assert.match(home, /只顯示具備明確發布狀態的機會資料/);
  assert.doesNotMatch(home, /const opportunities = \[/);
  assert.doesNotMatch(home, /href="\/opportunities"/);
  assert.doesNotMatch(home, /const warmingTopics\s*=/);
  assert.doesNotMatch(home, /const coolingTopics\s*=/);
  assert.doesNotMatch(home, /topWarming|topCooling|topicChange.*sort/);
});

test("market route redirects to the frozen Home market anchor", async () => {
  const [nav, redirect] = await Promise.all([read("components/AppNav.tsx"), read("market/page.tsx")]);
  assert.doesNotMatch(nav, /市場雷達/);
  assert.match(redirect, /redirect\("\/#market-overview"\)/);
});

test("V2 Home exposes explicit Home publication and unavailable semantics", async () => {
  const [home, foundation] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read("components/v2/V2Foundation.tsx"),
  ]);
  assert.match(home, /useTodayMainlines/);
  assert.match(home, /resource\.marketOverview/);
  assert.match(home, /resource\.state === "UNAVAILABLE"/);
  assert.match(home, /resource\.state !== "FORMAL"/);
  assert.match(home, /resource\.dataDate/);
  assert.match(home, /resource\.source/);
  assert.doesNotMatch(home, /isSyntheticPreview|canUseBackendData|freshnessLabel|useSnapshot/);
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
  assert.match(home, /只顯示具備明確發布狀態的機會資料/);
  assert.doesNotMatch(home, /candidate\.sort|strategyId|rankScore|targetPrice/);
});

test("public Home preserves the environment boundary without exposing MA20 slope copy", async () => {
  const [home, adapter] = await Promise.all([read("components/v2/TodayMarketPage.tsx"), read("lib/snapshot-adapter.ts")]);
  assert.match(adapter, /const sub = env/);
  assert.doesNotMatch(adapter, /const sub[\s\S]{0,160}MA20 slope/);
  assert.doesNotMatch(home, /MA20 slope/);
});
