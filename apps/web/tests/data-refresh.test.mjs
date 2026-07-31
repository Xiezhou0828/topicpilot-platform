import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const root = new URL("../app/", import.meta.url);
const read = (relative) => readFile(new URL(relative, root), "utf8");

test("one SnapshotProvider owns all live data refreshes", async () => {
  const [layout, store, home, watchlist, quality] = await Promise.all([
    read("layout.tsx"),
    read("lib/snapshot-store.tsx"),
    read("page.tsx"),
    read("watchlist/page.tsx"),
    read("components/DataQualityPanel.tsx"),
  ]);
  assert.match(layout, /<SnapshotProvider>\{children\}<\/SnapshotProvider>/);
  assert.match(home, /useHomeData/);
  assert.match(home, /useSnapshot/);
  assert.match(watchlist, /useSnapshot/);
  assert.match(quality, /useQualityPanel/);
  assert.doesNotMatch(home, /mockTopicsData|mockWatchlistData/);
  assert.match(store, /requestRef\.current/);
  assert.match(store, /if \(requestRef\.current\) return requestRef\.current/);
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
  assert.match(source, /FastAPI 回傳 HTTP \$\{res\.status\}/);
  assert.match(source, /FastAPI 回傳內容不是有效 JSON/);
  assert.match(source, /FastAPI 回傳資料不符合前端契約/);
});

test("strategy drilldown stays on home while the stock universe remains scan-only", async () => {
  const [home, watchlist, liveData] = await Promise.all([
    read("page.tsx"),
    read("watchlist/page.tsx"),
    read("lib/live-data.mjs"),
  ]);
  assert.match(home, /strategyRegistry/);
  assert.doesNotMatch(watchlist, /canShowTradeJudgement/);
  assert.match(watchlist, /點選查看完整判讀/);
  assert.match(liveData, /dataState === "LIVE"/);
  assert.match(liveData, /state: "SNAPSHOT"/);
  assert.match(home, /此策略未提供進場價位/);
  assert.match(home, /策略候選股/);
});

test("new backend quote contract is adapted without parsing rule text", async () => {
  const [types, adapter, source, topics] = await Promise.all([
    read("lib/types.ts"),
    read("lib/snapshot-adapter.ts"),
    read("lib/data-source.ts"),
    read("topics/page.tsx"),
  ]);
  for (const field of ["triggerValue", "supportValue", "pressureValue", "invalidationValue", "quoteMeta", "marketSession"]) {
    assert.match(types, new RegExp(field));
  }
  assert.match(adapter, /num\(o\.triggerValue\)/);
  assert.match(adapter, /raw\.quoteMeta\?\.updatedAt/);
  assert.match(adapter, /raw\.marketSession\?\.latestTradingDate/);
  assert.match(source, /topics,\s*topicGroups:/s);
  assert.match(source, /stockUniverse: toStockUniverse\(raw\)/);
  assert.match(adapter, /toTopicRelations/);
  assert.match(topics, /bundle\.stockUniverse/);
  assert.match(topics, /bundle\.source !== "snapshot"/);
  assert.match(topics, /正式 snapshot 載入前不顯示示範題材/);
});

test("a successful refresh swaps the complete bundle before publishing its state", async () => {
  const store = await read("lib/snapshot-store.tsx");
  assert.match(store, /const next = buildBundleFromRaw\(raw\)/);
  assert.match(store, /setBundle\(next\);[\s\S]*setStatus\(/);
  assert.match(store, /Math\.max\(next\.watchlistData\.rows\.length, next\.stockUniverse\.length\)/);
  assert.match(store, /DEMO_FALLBACK_ENABLED \? getBundledBundle\(\) : getUnavailableBundle\(\)/);
});
