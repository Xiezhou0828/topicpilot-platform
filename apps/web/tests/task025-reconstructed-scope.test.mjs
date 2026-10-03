// Synthetic unit/presentation evidence; no provider or Production request.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import ts from "typescript";

const fields = await readFile(new URL("../app/lib/today-market-fields.ts", import.meta.url), "utf8");
const page = await readFile(new URL("../app/components/v2/TodayMarketPage.tsx", import.meta.url), "utf8");
const css = await readFile(new URL("../app/globals.css", import.meta.url), "utf8");
const output = ts.transpileModule(fields, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const display = await import(`data:text/javascript;base64,${Buffer.from(output).toString("base64")}`);

test("TASK025 distribution always remains covered stocks, even with a legacy whole-market marker", () => {
  for (const scope of ["COVERED_STOCKS", "WHOLE_MARKET", undefined]) {
    const meta = display.marketDistributionDisplayMeta({
      eligible: 552, excluded: 1,
      coverage: { scope, eligibleUniverse: 553, observedComplete: 552, excludedCount: 1,
        coveragePct: 99.8192, distributionDenominator: "LEGACY_DENOMINATOR" },
    });
    assert.equal(meta.scope, "COVERED_STOCKS");
    assert.equal(meta.title, "已覆蓋股票漲跌幅分布");
    assert.equal(meta.denominator, "COMPLETE_CLOSE_PREVIOUS_CLOSE");
    assert.equal(meta.completeCount, 552);
    assert.equal(meta.universeCount, 553);
    assert.equal(meta.excludedCount, 1);
    assert.equal(meta.coveragePct, 99.8192);
  }
  assert.doesNotMatch(fields, /上市＋上櫃全市場|scope === "WHOLE_MARKET"/);
});

test("TASK025 missing backend coverage percentage is not derived in the browser", () => {
  const meta = display.marketDistributionDisplayMeta({
    eligible: 552, excluded: 1, coverage: { eligibleUniverse: 553, observedComplete: 552 },
  });
  assert.equal(meta.coveragePct, null);
  assert.equal(display.formatMarketNumber(null), "尚未提供");
});

test("TASK025 Home renders complete, eligible, excluded and coverage separately", () => {
  assert.match(page, /完整收盤／前收：\{formatMarketNumber\(displayMeta.completeCount\)\}/);
  assert.match(page, /符合資格股票：\$\{formatMarketNumber\(displayMeta.universeCount\)\}/);
  assert.match(page, /<span>\{universeText\}<\/span>/);
  assert.match(page, /覆蓋率：/);
  assert.match(page, /排除：\{formatMarketNumber\(displayMeta.excludedCount\)\}/);
});

for (const [value, expected] of [
  [123450000, "1 億 2,345 萬"], [-123450000, "-1 億 2,345 萬"],
  [100000000, "1 億"], [45000, "4.5 萬"], [-45000, "-4.5 萬"],
  [0, "0 元"], [null, "尚未提供"], [Number.NaN, "尚未提供"],
]) {
  test(`TASK025 institutional amount ${String(value)} uses governed numeric formatting`, () => {
    assert.equal(display.formatInstitutionalAmount(value), expected);
  });
}

test("TASK025 blank/null institutional values never become zero", () => {
  for (const invalid of ["", " ", null, undefined, "NaN", "Infinity"]) {
    assert.equal(display.institutionalAmountValue(invalid), null);
  }
  assert.equal(display.institutionalAmountValue("0"), 0);
  assert.equal(display.institutionalAmountValue("-45000"), -45000);
});

test("TASK025 high/low color is relative to previous close, never today's close", () => {
  assert.equal(display.indexPointTone(105, 100), "is-up");
  assert.equal(display.indexPointTone(95, 100), "is-down");
  assert.equal(display.indexPointTone(100, 100), "is-flat");
  for (const invalid of [0, null, undefined, Number.NaN, Number.POSITIVE_INFINITY]) {
    assert.equal(display.indexPointTone(105, invalid), "is-unavailable");
    assert.equal(display.indexPointTone(invalid, 100), "is-unavailable");
  }
  assert.match(page, /indexPointTone\(high, previousClose\)/);
  assert.match(page, /indexPointTone\(low, previousClose\)/);
  assert.match(css, /strong\.is-up\{color:#d72e32\}/);
  assert.match(css, /strong\.is-down\{color:#159563\}/);
});

test("TASK025 actual flex-axis alignment centers bar, count and label", () => {
  assert.match(css, /\.tp-home-target-bar-item\{align-items:center;justify-items:center\}/);
  assert.match(css, /\.tp-home-target-bar-item>\*\{width:100%;text-align:center\}/);
  assert.match(css, /\.tp-home-target-bar-item i\{width:min\(100%,54px\)\}/);
});

test("TASK025 public Home excludes engineering diagnostics without hiding product disclosure", () => {
  assert.deepEqual(display.publicHomeQualityNotes([
    "UNAVAILABLE_INSTRUMENT:MISSING_MARKET_DATA:2601", "postgres checkpoint detail",
    "ingestion failed", "Home.publication internal", "lastValidPriceDate=old",
    "unavailable instrument diagnostic", "今日資料仍在整理中。", "正式歷史資料不足。",
  ]), ["今日資料仍在整理中。", "正式歷史資料不足。"]);
  assert.match(page, /publicHomeQualityNotes\(resource.qualityNotes\)/);
});

test("TASK025 ACTIVE-only cards and full backend catalog retain the formal data date", () => {
  assert.match(page, /allSignals.filter\(\(signal\) => signal.isActive === true && signal.signalStatus === "ACTIVE"\)/);
  assert.match(page, /\(data\?\.signalCatalog \?\? \[\]\).map/);
  assert.match(page, /資料日：\{formatMarketDate\(data\?\.dataDate\)\}/);
  assert.match(page, /current\?\.signalStatus \?\? "NOT_EVALUABLE"/);
  assert.match(page, /catalogSignals.length === 0 && <p role="status">正式訊號目錄尚未提供。/);
  assert.doesNotMatch(page, /Date.now\(|setInterval|new Date\(\)/);
});
