import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Today commercial surface is EOD-first and excludes mockup values", async () => {
  const page = await read("components/v2/TodayMarketPage.tsx");

  for (const marker of ["市場概況", "今日市場重點", "今日主線", "今日題材動態", "快速升溫", "快速退潮", "今日機會"]) {
    assert.match(page, new RegExp(marker));
  }
  assert.match(page, /收盤後 EOD/);
  assert.doesNotMatch(page, /24,612\.38|4,382|8 檔|網通 \+3\.82%|sparkline|盤中重要事件/);
  assert.doesNotMatch(page, /追蹤股票|追蹤題材|不可用家數|provider|generatedAt.*顯示/);
});

test("Today distribution, ticker, and opportunity entry remain backend-owned", async () => {
  const [page, fields, css] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read("lib/today-market-fields.ts"),
    read("globals.css"),
  ]);

  assert.match(page, /marketDistribution\(overview\)/);
  assert.match(page, /distribution\.buckets/);
  assert.doesNotMatch(page, /indices\.reduce|turnover\.reduce|distribution.*sort|changePct.*calculate/i);
  assert.match(page, /暫停題材動態/);
  assert.match(page, /href="\/opportunities"/);
  assert.match(page, /正式機會資料尚未發布|正式機會資料已發布/);
  assert.match(fields, /HomeMarketDistribution/);
  assert.match(css, /tp-home-topic-ticker-track/);
  assert.match(css, /prefers-reduced-motion: reduce/);
  assert.match(css, /overflow-x:auto/);
});
