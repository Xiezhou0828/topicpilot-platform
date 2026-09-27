import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

async function distributionSources() {
  const [page, fields, css] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read("lib/today-market-fields.ts"),
    read("globals.css"),
  ]);
  const chart = page.match(/<div className="tp-home-target-bar-item"[\s\S]*?<\/div>\)}/)?.[0] ?? "";
  return { page, fields, css, chart };
}

test("PRICE_DISTRIBUTION_PERCENT_HIDDEN=PASS", async () => {
  const { chart } = await distributionSources();
  assert.doesNotMatch(chart, /formatMarketShare|bucket\.percentage\)\}/);
  assert.doesNotMatch(chart, /·/);
});

test("PRICE_DISTRIBUTION_COUNT_VISIBLE=PASS", async () => {
  const { chart } = await distributionSources();
  assert.match(chart, /<strong className="tp-home-target-bar-count">\{formatMarketNumber\(bucket\.count\)\}<\/strong>/);
});

test("PRICE_DISTRIBUTION_LABELS_BELOW_BARS=PASS", async () => {
  const { chart, css } = await distributionSources();
  assert.match(chart, /<i aria-hidden="true" style=\{\{ height:/);
  assert.match(chart, /<span className="tp-home-target-bar-label" title=\{bucket\.label\}>\{formatMarketDistributionLabel\(bucket\.key, bucket\.label\)\}<\/span>/);
  assert.ok(chart.indexOf("tp-home-target-bar-count") < chart.indexOf("<i aria-hidden"));
  assert.ok(chart.indexOf("<i aria-hidden") < chart.indexOf("tp-home-target-bar-label"));
  assert.match(css, /\.tp-home-target-bar-item\{grid-template-rows:auto 64px auto\}/);
});

test("PRICE_DISTRIBUTION_LABEL_ORDER=PASS", async () => {
  const { fields } = await distributionSources();
  const labels = [
    'PCT_GE_10: "漲幅 ≥10%"',
    'PCT_7_TO_10: "+7~10%"',
    'PCT_3_TO_7: "+3~7%"',
    'PCT_0_TO_3: "0~3%"',
    'FLAT: "平盤"',
    'PCT_NEG_0_TO_3: "-3~0%"',
    'PCT_NEG_3_TO_7: "-7~-3%"',
    'PCT_NEG_7_TO_10: "-10~-7%"',
    'PCT_LE_NEG_10: "跌幅 ≥10%"',
  ];
  let previousIndex = -1;
  for (const label of labels) {
    const index = fields.indexOf(label);
    assert.ok(index > previousIndex, `label order must include ${label}`);
    previousIndex = index;
  }
});

test("PRICE_DISTRIBUTION_TITLE_TYPOGRAPHY_CONSISTENT=PASS", async () => {
  const { page, css } = await distributionSources();
  assert.match(page, /<h3>漲跌幅分布（上市＋上櫃）<\/h3>/);
  assert.match(css, /\.tp-home-target-card-title strong\{font-size:17px\}/);
  assert.match(css, /\.tp-home-target-subheading h3\{font-size:17px;font-weight:650;letter-spacing:-\.02em\}/);
});

test("PRICE_DISTRIBUTION_UNIVERSE_HELPER_PRESERVED=PASS", async () => {
  const { page } = await distributionSources();
  assert.match(page, /完整收盤／前收資料 · 排除未成交或缺值/);
  assert.match(page, /總家數 \{formatMarketNumber\(distribution\.eligible\)\}/);
  assert.match(page, /title=\{distributionUniverse\} aria-label=\{`分布統計範圍：\$\{distributionUniverse\}`\}/);
});

test("Today price distribution keeps the formal semantic edge labels", async () => {
  const { fields } = await distributionSources();
  assert.doesNotMatch(fields, /PCT_GE_10:\s*"漲停"/);
  assert.doesNotMatch(fields, /PCT_LE_NEG_10:\s*"跌停"/);
  assert.match(fields, /PCT_GE_10: "漲幅 ≥10%"/);
  assert.match(fields, /PCT_LE_NEG_10: "跌幅 ≥10%"/);
});
