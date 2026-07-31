import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("guide is a fixed navigation destination and explains the core workflow", async () => {
  const [nav, guide] = await Promise.all([read("components/AppNav.tsx"), read("guide/page.tsx")]);
  assert.match(nav, /href: "\/guide", label: "使用指南"/);
  for (const text of ["今天先看哪一頁", "題材頁與股票一覽的差別", "觸發價", "支撐價", "失效價", "風險幅度", "資料過期", "快速篩選", "進階篩選"]) assert.match(guide, new RegExp(text));
});

test("home has focused guidance and guided unavailable states", async () => {
  const home = await read("page.tsx");
  for (const label of ["市場狀態", "今日操作方式", "主要風險"]) assert.match(home, new RegExp(`<b>${label}</b>`));
  assert.match(home, /市場資料尚未更新/);
  assert.match(home, /正在更新市場摘要/);
  assert.match(home, /策略候選股/);
  assert.match(home, /選擇策略查看當日後端選中的標的與已成熟的績效摘要/);
  assert.doesNotMatch(home, /Live watchlist|最近一次觀察股|Entry Score|沿用後台順序與分數/);
});

test("stock universe uses the eight-column hierarchy and separates detail-only fields", async () => {
  const page = await read("watchlist/page.tsx");
  assert.match(page, /<th>自選<\/th><th>個股<\/th><th>主大族群<\/th><th>題材<\/th><th>現價<\/th><th>漲跌%<\/th><th>\{volumeLabel\}<\/th><th>燈號<\/th>/);
  for (const text of ["趨勢偏多", "接近突破", "法人加碼", "題材強勢", "風險較低", "MA、RS、MACD、KD、RSI、量價、法人"]) assert.match(page, new RegExp(text));
  for (const state of ["股票資料尚未載入", "正式股票數為 0", "所選條件缺少必要資料", "有資料，但沒有符合條件的股票"]) assert.match(page, new RegExp(state));
  assert.match(page, /role="link" tabIndex=\{0\}/);
  assert.match(page, /event\.key === "Enter" \|\| event\.key === " "/);
  assert.match(page, /event\.stopPropagation\(\)/);
  assert.match(page, /stock\.volume/);
  assert.match(page, /盤中累計/);
  assert.match(page, /status\.state === "error" \|\| status\.dataState === "UNAVAILABLE"/);
  assert.doesNotMatch(page, /<th>觸發|<th>距觸發|<th>Entry|<th>Gate|<th>排序/);
});

test("three lamps expose four visually distinct states and detail shows existing evidence", async () => {
  const [lamps, css, detail] = await Promise.all([read("components/StockSignalLamps.tsx"), read("globals.css"), read("stocks/[code]/page.tsx")]);
  for (const state of ["positive", "negative", "neutral", "missing"]) {
    assert.match(lamps, new RegExp(`"${state}"`));
    assert.match(css, new RegExp(`\\.signalLamp\\.${state}`));
  }
  for (const text of ["籌碼動向", "營運動能", "短線風險", "法人同步", "400 張以上持股", "近 3 月 YoY", "觀察資格原因", "量能狀態／量比"]) assert.match(detail, new RegExp(text));
  assert.match(detail, /不以 EPS 或其他資料替代/);
});

test("topic empty state explains purpose and provides recovery routes", async () => {
  const topics = await read("topics/page.tsx");
  assert.match(topics, /題材總覽用來比較資金集中方向/);
  assert.match(topics, /前往股票一覽/);
  assert.match(topics, /查看使用指南/);
  assert.match(topics, /refresh\("manual"\)/);
});
