import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}-${path}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request(`http://localhost${path}`, { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("renders the approved V2 and retained workspace routes", async () => {
  const routes = [
    ["/", "tp-home-overview-card"],
    ["/market", null, 307],
    ["/topics", "tp-topic-overview-page"],
    ["/watchlist", "stockUniverseShell"],
    ["/guide", "guideShell"],
    ["/studio", "studioPage"],
    ["/stocks/DEMO-A1", "stockDetailGrid"],
  ];
  for (const [path, marker, expectedStatus = 200] of routes) {
    const response = await render(path);
    assert.equal(response.status, expectedStatus);
    if (path === "/market") {
      assert.equal(response.headers.get("location"), "http://localhost/#market-overview");
      continue;
    }
    const html = await response.text();
    assert.match(html, /lang="zh-Hant"/);
    assert.match(html, /TopicPilot/);
    assert.match(html, new RegExp(marker));
  }
});

test("V2 Home source contains the frozen market workflow and safety boundary", async () => {
  const home = await readFile(new URL("../app/components/v2/TodayMarketPage.tsx", import.meta.url), "utf8");
  const liveData = await readFile(new URL("../app/lib/live-data.mjs", import.meta.url), "utf8");
  for (const marker of [
    "market-overview-title",
    "tp-home-story-card",
    "mainline-title",
    "events-title",
    "rotation-title",
    "opportunities-title",
    "marketOverview",
    "市場廣度資料目前不可用",
    "只顯示具備明確發布狀態的機會資料",
  ]) assert.match(home, new RegExp(marker));
  assert.match(home, /useTodayMainlines/);
  assert.match(home, /mainlines\.resource\.data\.map/);
  assert.match(home, /mainlines\.resource\.state === "UNAVAILABLE"/);
  assert.match(home, /href=\{`\/topics\/\$\{topic\.slug\}`\}/);
  assert.match(liveData, /canShowTradeJudgement/);
  assert.doesNotMatch(home, /Buy|Sell|Strong Buy|stop-loss|Entry Score/);
});

test("trading theme keeps quote cards dark and exposes trigger emphasis", async () => {
  const css = await readFile(new URL("../app/globals.css", import.meta.url), "utf8");
  assert.match(css, /--ink: #f1f5f6/);
  assert.match(css, /\.priorityStock\.trigger-hit/);
  assert.match(css, /@keyframes triggerPulse/);
  assert.match(css, /prefers-reduced-motion/);
  assert.doesNotMatch(css, /#fcfcfc|#fffafa|#fff4f3/);
});

test("glossary keeps meaning, action and invalidation columns", async () => {
  const glossary = await readFile(new URL("../app/components/TradingGlossary.tsx", import.meta.url), "utf8");
  assert.match(glossary, /glossaryPanel/);
  assert.match(glossary, /className="glossaryGrid"/);
  assert.match(glossary, /<b>意思<\/b>/);
  assert.match(glossary, /<b>動作<\/b>/);
  assert.match(glossary, /<b>失效<\/b>/);
  assert.match(glossary, /TERMS\.map/);
});
