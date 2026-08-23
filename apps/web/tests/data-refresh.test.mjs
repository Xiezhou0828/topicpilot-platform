import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const root = new URL("../app/", import.meta.url);
const read = (relative) => readFile(new URL(relative, root), "utf8");

test("the V2 route tree keeps shared providers and explicit surface owners", async () => {
  const [layout, rootPage, v2Page, home, topics, stocks, favorites, opportunities, store, quality] = await Promise.all([
    read("layout.tsx"),
    read("page.tsx"),
    read("components/v2/V2Page.tsx"),
    read("components/v2/TodayMarketPage.tsx"),
    read("components/v2/TopicListPage.tsx"),
    read("components/v2/StockExplorerPage.tsx"),
    read("components/v2/FavoritesWorkspacePage.tsx"),
    read("opportunities/page.tsx"),
    read("lib/snapshot-store.tsx"),
    read("components/DataQualityPanel.tsx"),
  ]);
  assert.match(layout, /<SnapshotProvider>\{children\}<\/SnapshotProvider>/);
  assert.match(rootPage, /import V2Page from "\.\/components\/v2\/V2Page"/);
  assert.match(v2Page, /import TodayMarketPage from "\.\/TodayMarketPage"/);
  assert.match(v2Page, /path === "\/"/);
  assert.match(v2Page, /<TodayMarketPage \/>/);
  assert.match(home, /useTodayMainlines/);
  assert.match(home, /resource\.marketOverview/);
  assert.match(topics, /fetchTopics/);
  assert.match(stocks, /fetchFormalStocks/);
  assert.match(favorites, /fetchFormalStocks/);
  assert.match(opportunities, /V2Page path="\/opportunities"/);
  assert.match(store, /requestRef\.current/);
  assert.match(store, /if \(requestRef\.current\) return requestRef\.current/);
  assert.match(quality, /useQualityPanel/);
});

test("V2 Home keeps research content separate from the scan-only Stock Explorer", async () => {
  const [home, stocks] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read("components/v2/StockExplorerPage.tsx"),
  ]);
  assert.match(home, /useTodayMainlines/);
  assert.match(home, /mainlines\.resource\.data\.map/);
  assert.match(home, /mainlines\.resource\.state === "UNAVAILABLE"/);
  assert.match(home, /href=\{`\/topics\/\$\{topic\.slug\}`\}/);
  assert.match(home, /OpportunityTeaserCard/);
  assert.match(home, /mainlines\.resource\.opportunities/);
  assert.doesNotMatch(home, /strategyRegistry|strategyCandidates|Strong Buy|Buy|Sell|stop-loss|Entry Score/);
  assert.match(stocks, /fetchFormalStocks/);
  assert.match(stocks, /openDetailPanel/);
  assert.match(stocks, /const \[strategy, setStrategy\]/);
  assert.doesNotMatch(stocks, /Strong Buy|stop-loss|target price/);
});

test("V2 topic and stock surfaces use formal adapters without parsing rule text", async () => {
  const [topics, topicApi, stocks, stockApi, adapter] = await Promise.all([
    read("components/v2/TopicListPage.tsx"),
    read("lib/topic-api.ts"),
    read("components/v2/StockExplorerPage.tsx"),
    read("lib/stock-api.ts"),
    read("lib/snapshot-adapter.ts"),
  ]);
  assert.match(topics, /fetchTopics\(\)/);
  assert.match(topics, /resource\?\.source === "unavailable"/);
  assert.match(topics, /PreviewBadge/);
  assert.match(topicApi, /\/api\/v2\/topics\?limit=200&offset=0/);
  assert.match(stocks, /fetchFormalStocks/);
  assert.match(stockApi, /\/api\/v2\/stocks/);
  assert.match(adapter, /toMarketDecision/);
  assert.match(adapter, /toStrategyRegistry/);
  assert.doesNotMatch(topics, /bundle\.stockUniverse|parse.*rule/i);
});

test("refresh controller polls every 3 minutes only while visible and in market session", async () => {
  const [store, liveData, source] = await Promise.all([
    read("lib/snapshot-store.tsx"),
    read("lib/live-data.mjs"),
    read("lib/data-source.ts"),
  ]);
  assert.match(liveData, /LIVE_REFRESH_INTERVAL_MS = 3 \* 60_000/);
  assert.match(store, /marketSession \? marketSession === "OPEN" : isTaiwanMarketSession\(\)/);
  assert.match(store, /document\.visibilityState === "visible" && marketIsOpen/);
  assert.match(store, /window\.addEventListener\("focus"/);
  assert.match(store, /document\.addEventListener\("visibilitychange"/);
  assert.match(store, /abortRef\.current\?\.abort\("unmount"\)/);
  assert.match(source, /cache: "no-store"/);
  assert.match(source, /refresh=\$\{Date\.now\(\)\}/);
});

test("existing frontend reads the FastAPI snapshot through one data layer", async () => {
  const source = await read("lib/data-source.ts");
  assert.match(source, /NEXT_PUBLIC_API_BASE_URL/);
  assert.match(source, /NEXT_PUBLIC_SNAPSHOT_API_URL/);
  assert.match(await read("layout.tsx"), /data-snapshot-api-url=\{snapshotApiUrl\}/);
  assert.match(source, /\/snapshot-api\.json\?refresh=\$\{Date\.now\(\)\}/);
  assert.match(source, /document\.documentElement\.dataset\.snapshotApiUrl/);
  assert.match(source, /parsed\.protocol === "https:" \|\| parsed\.protocol === "http:"/);
  assert.match(source, /\/api\/v1\/snapshot\/latest/);
  assert.match(source, /DEMO_FALLBACK_ENABLED/);
  assert.doesNotMatch(source, /X-Snapshot-Source|source !== "r2"/);
});

test("a successful refresh swaps the complete bundle before publishing its state", async () => {
  const store = await read("lib/snapshot-store.tsx");
  assert.match(store, /const next = buildBundleFromRaw\(raw\)/);
  assert.match(store, /setBundle\(next\);[\s\S]*setStatus\(/);
  assert.match(store, /Math\.max\(next\.watchlistData\.rows\.length, next\.stockUniverse\.length\)/);
  assert.match(store, /DEMO_FALLBACK_ENABLED \? getBundledBundle\(\) : getUnavailableBundle\(\)/);
});
