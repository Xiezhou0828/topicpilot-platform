import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("guide remains a fixed navigation destination with a defined workflow", async () => {
  const [nav, guide] = await Promise.all([read("components/AppNav.tsx"), read("guide/page.tsx")]);
  assert.match(nav, /href: "\/guide"/);
  for (const marker of ["guideShell", "guideJump", "guideSection", "guideWarnings", "guideDefinitions"]) {
    assert.match(guide, new RegExp(marker));
  }
});

test("V2 Home exposes guided publication states without recommendation language", async () => {
  const [home, foundation] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read("components/v2/V2Foundation.tsx"),
  ]);
  for (const marker of ["useTodayMainlines", "resource.marketOverview", "market-overview-title", "tp-home-mainlines-state"]) {
    assert.match(home, new RegExp(marker));
  }
  assert.doesNotMatch(home, /freshnessLabel|isSyntheticPreview|canUseBackendData|useSnapshot/);
  assert.match(foundation, /DataState/);
  assert.match(foundation, /state === "UNAVAILABLE"/);
  assert.match(foundation, /tp-state-\$\{/);
  assert.doesNotMatch(home, /Live watchlist|Entry Score|Strong Buy|stop-loss|Buy|Sell/);
});

test("legacy watchlist preserves its eight-column scan hierarchy", async () => {
  const page = await read("watchlist/page.tsx");
  assert.match(page, /stockUniverseTable/);
  assert.match(page, /quickFilters/);
  assert.match(page, /StockSignalLamps/);
  assert.match(page, /stock\.volume/);
  assert.match(page, /status\.state === "error" \|\| status\.dataState === "UNAVAILABLE"/);
  assert.doesNotMatch(page, /<th>Entry|<th>Gate|<th>Target/);
});

test("signal lamps retain positive, negative, neutral and missing states", async () => {
  const [lamps, css, detail] = await Promise.all([
    read("components/StockSignalLamps.tsx"),
    read("globals.css"),
    read("stocks/[code]/page.tsx"),
  ]);
  for (const state of ["positive", "negative", "neutral", "missing"]) {
    assert.match(lamps, new RegExp(`"${state}"`));
    assert.match(css, new RegExp(`\\.signalLamp\\.${state}`));
  }
  assert.match(detail, /stockDetailGrid/);
  assert.match(detail, /Evidence summary/);
  assert.match(detail, /trigger-/);
  assert.match(detail, /dataGapText/);
});

test("V2 Topic Overview has explicit unavailable and Preview recovery states", async () => {
  const [topics, api] = await Promise.all([read("components/v2/TopicListPage.tsx"), read("lib/topic-api.ts")]);
  assert.match(topics, /fetchTopics\(\)/);
  assert.match(topics, /resource\?\.source === "unavailable"/);
  assert.match(topics, /<DataState state="UNAVAILABLE" \/>/);
  assert.match(topics, /<EmptyState title=/);
  assert.match(topics, /PreviewBadge/);
  assert.match(api, /NEXT_PUBLIC_ENABLE_TOPIC_PREVIEW/);
  assert.match(api, /\/api\/v2\/topics/);
});
