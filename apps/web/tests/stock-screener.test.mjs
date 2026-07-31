import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { evaluateFilter, evaluateStockFilters, SCREENER_GROUPS } from "../app/lib/stock-screener.mjs";

const fixture = JSON.parse(await readFile(new URL("./fixtures/stock-screener.synthetic.json", import.meta.url), "utf8"));
assert.equal(fixture.fixtureType, "SYNTHETIC_FIXTURE");
const { match, miss, missing } = fixture.cases;
const ids = SCREENER_GROUPS.flatMap((group) => group.filters.map(([id]) => id));

test("every five-category filter has matching, non-matching and missing fixtures", () => {
  for (const id of ids) {
    assert.equal(evaluateFilter(match, id), true, `${id}: matching fixture`);
    assert.equal(evaluateFilter(miss, id), false, `${id}: non-matching fixture`);
    assert.equal(evaluateFilter(missing, id), null, `${id}: missing fixture`);
  }
});

test("RSI14 and price ranges use backend values without indicator recalculation", () => {
  const ranges = { rsiMin: 40, rsiMax: 70, priceMin: 50, priceMax: 200 };
  assert.equal(evaluateFilter(match, "rsi_range", ranges), true);
  assert.equal(evaluateFilter(miss, "rsi_range", ranges), false);
  assert.equal(evaluateFilter(missing, "rsi_range", ranges), null);
  assert.equal(evaluateFilter(match, "price_range", ranges), true);
  assert.equal(evaluateFilter(miss, "price_range", ranges), false);
  assert.equal(evaluateFilter(missing, "price_range", ranges), null);
});

test("AND/OR and missing-data semantics are consistent", () => {
  assert.deepEqual(evaluateStockFilters(match, [], "AND"), { matches: true, missing: 0 });
  assert.equal(evaluateStockFilters(match, ["above_ma20", "rs5_positive"], "AND").matches, true);
  assert.equal(evaluateStockFilters(miss, ["above_ma20", "rs5_positive"], "OR").matches, false);
  assert.equal(evaluateStockFilters(missing, ["above_ma20"], "AND").matches, false);
  const partial = structuredClone(match); partial.screener.rs5Pct = null;
  assert.deepEqual(evaluateStockFilters(partial, ["above_ma20", "rs5_positive"], "AND"), { matches: false, missing: 1 });
  assert.deepEqual(evaluateStockFilters(partial, ["above_ma20", "rs5_positive"], "OR"), { matches: true, missing: 1 });
});

test("clear combination filters use only explicit snapshot values", () => {
  const combined = structuredClone(match);
  combined.screener.reclaimedMa20 = null;
  combined.screener.breakoutWithVolume = null;
  combined.screener.institutionsInSync = null;
  assert.equal(evaluateFilter(combined, "reclaimed_ma20"), true);
  assert.equal(evaluateFilter(combined, "breakout_volume"), true);
  assert.equal(evaluateFilter(combined, "institutions_sync"), true);
});

test("source and fixture labels enforce backend-only production data", async () => {
  const [page, adapter, types] = await Promise.all([
    readFile(new URL("../app/watchlist/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/lib/snapshot-adapter.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/lib/types.ts", import.meta.url), "utf8"),
  ]);
  assert.match(page, /bundle\.source === "snapshot" \? bundle\.stockUniverse : \[\]/);
  assert.match(page, />全部符合</);
  assert.match(page, />任一符合</);
  assert.match(page, />漲跌%</);
  assert.match(page, /法人加碼/);
  assert.doesNotMatch(page, /setPriceCap\(true\)|priceCap/);
  assert.match(adapter, /MACD柱翻正/);
  assert.match(adapter, /大戶資料日期/);
  assert.match(types, /StockScreenerSignals/);
});
