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

test("renders all primary workspace routes", async () => {
  const routes = [
    ["/", "今日市場焦點"],
    ["/market", "今日市場焦點", 307],
    ["/topics", "題材總覽"],
    ["/watchlist", "股票一覽"],
    ["/guide", "使用指南"],
    ["/studio", "AI投資工作室"],
    ["/stocks/DEMO-A1", "Aster Systems"],
  ];
  for (const [path, expected, expectedStatus = 200] of routes) {
    const response = await render(path);
    assert.equal(response.status, expectedStatus);
    if (path === "/market") {
      assert.equal(response.headers.get("location"), "http://localhost/#market-overview");
      continue;
    }
    const html = await response.text();
    assert.match(html, /lang="zh-Hant"/);
    assert.match(html, /題材領航/);
    assert.match(html, new RegExp(expected));
  }
});

test("home source contains focused market workflow and safety language", async () => {
  const home = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  const liveData = await readFile(new URL("../app/lib/live-data.mjs", import.meta.url), "utf8");
  for (const text of [
    "今日市場判斷",
    "市場健康度",
    "題材輪動",
    "策略候選股",
    "現價",
    "觸發",
    "支撐",
    "失效",
    "此策略未提供進場價位",
    "樣本累積中",
  ]) assert.match(home, new RegExp(text));
  assert.match(home, /strategyId === selectedStrategy\.strategyId/);
  assert.match(liveData, /已碰觸發價/);
  assert.doesNotMatch(home, /即時強度|待接資料源/);
});

test("trading theme keeps quote cards dark and exposes trigger emphasis", async () => {
  const css = await readFile(new URL("../app/globals.css", import.meta.url), "utf8");
  assert.match(css, /--ink: #f1f5f6/);
  assert.match(css, /\.priorityStock\.trigger-hit/);
  assert.match(css, /@keyframes triggerPulse/);
  assert.match(css, /prefers-reduced-motion/);
  assert.doesNotMatch(css, /#fcfcfc|#fffafa|#fff4f3/);
});

test("glossary explains meaning, action and invalidation", async () => {
  const glossary = await readFile(new URL("../app/components/TradingGlossary.tsx", import.meta.url), "utf8");
  for (const term of ["進場條件分數", "觀察資格", "回檔轉強", "等突破", "雙週期領先", "資金先行", "消息共振", "族群分歧", "細分主導"]) {
    assert.match(glossary, new RegExp(term));
  }
  assert.match(glossary, /<b>意思<\/b>/);
  assert.match(glossary, /<b>動作<\/b>/);
  assert.match(glossary, /<b>失效<\/b>/);
});
