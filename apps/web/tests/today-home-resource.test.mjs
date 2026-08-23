import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Today Home exposes one shared resource envelope for every Home section", async () => {
  const home = await read("lib/today-home.ts");
  assert.match(home, /export type TodayHomeResource/);
  assert.match(home, /transportState: TodayHomeTransportState/);
  assert.match(home, /publicationState: TodayHomePublicationState/);
  assert.match(home, /home: HomeResponse \| null/);
  for (const section of [
    "mainTopics",
    "heatingTopics",
    "coolingTopics",
    "dailyFocus",
    "marketPulse",
    "opportunities",
    "marketOverview",
  ]) {
    assert.match(home, new RegExp(`${section}:`));
  }
  for (const metadata of [
    "dataDate",
    "asOf",
    "source",
    "dataQuality",
    "temporarySections",
    "missingSections",
    "classification",
    "status",
    "reason",
  ]) {
    assert.match(home, new RegExp(`${metadata}:`));
  }
});

test("Today Home uses the generated contract and exactly one runtime Home request", async () => {
  const home = await read("lib/today-home.ts");
  assert.match(home, /components\["schemas"\]\["HomeResponse"\]/);
  assert.match(home, /HomeDailyFocus/);
  assert.match(home, /HomeMarketPulseEvent/);
  assert.match(home, /HomeOpportunityTopic/);
  assert.match(home, /HomeMarketOverview/);
  assert.equal((home.match(/client\.getHome\(/g) ?? []).length, 1);
  assert.doesNotMatch(home, /getHomeV2|getTodayHome|getTodayMarket/);
});

test("Today Home keeps transport and publication state separate and fail-closed", async () => {
  const home = await read("lib/today-home.ts");
  assert.match(home, /TodayHomeTransportState = "LOADING" \| "READY" \| "ERROR"/);
  assert.match(home, /TodayHomePublicationState = "FORMAL" \| "TEMPORARY" \| "PREVIEW" \| "UNAVAILABLE"/);
  assert.match(home, /transportState: "READY"/);
  assert.match(home, /state: "TEMPORARY"/);
  assert.match(home, /state: "PREVIEW"/);
  assert.match(home, /state: "UNAVAILABLE"/);
  assert.match(home, /previewEnabled/);
  assert.doesNotMatch(home, /mock|fallback/i);
});

test("Today Home maps sections without browser ranking, lifecycle, breadth, or opportunity rules", async () => {
  const home = await read("lib/today-home.ts");
  assert.match(home, /dailyFocus: home\.dailyFocus \?\? null/);
  assert.match(home, /marketPulse: Array\.isArray\(home\.marketPulse\) \? home\.marketPulse : \[\]/);
  assert.match(home, /opportunities: Array\.isArray\(home\.opportunities\) \? home\.opportunities : \[\]/);
  assert.match(home, /marketOverview: home\.marketOverview \?\? null/);
  assert.doesNotMatch(home, /\.sort\(/);
  assert.doesNotMatch(home, /rank|ranking|breadth|lifecycle|dedup|severity calculation|opportunity qualification/i);
});

test("Today Market consumes backend-owned events through the shared envelope", async () => {
  const [page, mainlines] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read("lib/today-mainlines.ts"),
  ]);
  assert.match(mainlines, /useTodayHomeResource/);
  assert.match(mainlines, /toTodayMainlinesResource/);
  assert.match(mainlines, /marketEvents: TodayMarketEventsResource/);
  assert.match(mainlines, /mapMarketEvents/);
  assert.match(page, /useTodayMainlines/);
  assert.match(page, /resource\.marketEvents/);
  assert.match(page, /event\.description/);
  assert.doesNotMatch(page, /const events = \[/);
  assert.match(mainlines, /opportunities: TodayOpportunityResource/);
  assert.match(mainlines, /mapOpportunities\(resource, previewEnabled\)/);
  assert.match(page, /OpportunityTeaserCard/);
  assert.match(page, /mainlines\.resource\.opportunities/);
  assert.doesNotMatch(page, /const opportunities = \[/);
  assert.doesNotMatch(page, /createTopicPilotClient|getTodayHome|getTodayMarket/);
});
