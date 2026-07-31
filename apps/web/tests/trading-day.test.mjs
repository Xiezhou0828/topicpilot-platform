import assert from "node:assert/strict";
import { test } from "node:test";
import {
  evaluateFreshness,
  evaluateStaleness,
  latestTradingDayOnOrBefore,
  parseDateOnly,
  STALE_THRESHOLDS,
  toISO,
  tradingDaysBetween,
} from "../app/lib/trading-day.mjs";

test("parseDateOnly accepts YYYY-MM-DD and YYYYMMDD, rejects junk/month", () => {
  assert.equal(toISO(parseDateOnly("2026-07-09")), "2026-07-09");
  assert.equal(toISO(parseDateOnly("20260709")), "2026-07-09");
  assert.equal(parseDateOnly("202606"), null); // 月資料
  assert.equal(parseDateOnly(""), null);
  assert.equal(parseDateOnly(null), null);
  assert.equal(parseDateOnly("2026-02-30"), null); // 不存在的日期
  assert.equal(parseDateOnly("abc"), null);
});

test("weekend does not create false alarm (0 trading-day gap)", () => {
  // dataDate 週五、today 週日 → 最近交易日仍是週五 → 不過期
  const r = evaluateStaleness({ date: "2026-07-10", today: "2026-07-12", thresholdDays: 1 });
  assert.equal(r.valid, true);
  assert.equal(r.gapTradingDays, 0);
  assert.equal(r.stale, false);
});

test("one trading day behind is flagged (spec example 07-09 vs 07-12)", () => {
  const r = evaluateStaleness({ date: "2026-07-09", today: "2026-07-12", thresholdDays: 1 });
  assert.equal(r.stale, true);
  assert.equal(r.gapTradingDays, 1);
  assert.equal(r.latestTradingDay, "2026-07-10"); // 週五
});

test("same-day is fresh", () => {
  const r = evaluateStaleness({ date: "2026-07-10", today: "2026-07-10", thresholdDays: 1 });
  assert.equal(r.stale, false);
  assert.equal(r.gapTradingDays, 0);
});

test("cross-weekend Thu->Mon counts trading days correctly", () => {
  // 2026-07-09 Thu -> 2026-07-13 Mon：中間 Fri(10) + Mon(13) = 2 交易日
  const from = parseDateOnly("2026-07-09");
  const to = parseDateOnly("2026-07-13");
  assert.equal(tradingDaysBetween(from, to), 2);
});

test("latestTradingDayOnOrBefore skips weekend", () => {
  assert.equal(toISO(latestTradingDayOnOrBefore(parseDateOnly("2026-07-12"))), "2026-07-10"); // Sun -> Fri
  assert.equal(toISO(latestTradingDayOnOrBefore(parseDateOnly("2026-07-11"))), "2026-07-10"); // Sat -> Fri
});

test("holidays are treated as non-trading", () => {
  const holidays = new Set(["2026-07-10"]);
  // today 週日、假設週五(10)休市 → 最近交易日退到週四(09)
  assert.equal(toISO(latestTradingDayOnOrBefore(parseDateOnly("2026-07-12"), holidays)), "2026-07-09");
  const r = evaluateStaleness({ date: "2026-07-09", today: "2026-07-12", thresholdDays: 1, holidays });
  assert.equal(r.stale, false); // 09 就是最近交易日
});

test("missing/malformed date is safe (valid:false, not stale)", () => {
  const r = evaluateStaleness({ date: null, today: "2026-07-12", thresholdDays: 1 });
  assert.equal(r.valid, false);
  assert.equal(r.stale, false);
  const r2 = evaluateStaleness({ date: "2026-07-09", today: "bad", thresholdDays: 1 });
  assert.equal(r2.valid, false);
  assert.equal(r2.stale, false);
});

test("evaluateFreshness separates sources; TDCC/fundamental never price-stale", () => {
  const f = {
    dataDate: "2026-07-09",
    institutionalAsOf: "20260709",
    tdccAsOf: "20260703",
    fundamentalYm: "202606",
  };
  const out = evaluateFreshness(f, "2026-07-12");
  const byKey = Object.fromEntries(out.items.map((i) => [i.key, i]));
  assert.equal(byKey.quote.stale, true);
  assert.match(byKey.quote.reason, /最近交易日/);
  // 法人 20260709 vs 最近交易日 20260710 → gap 1 < 門檻 2 → 不過期
  assert.equal(byKey.institutional.stale, false);
  // TDCC / 基本面：僅顯示，不過期
  assert.equal(byKey.tdcc.stale, false);
  assert.equal(byKey.tdcc.date, "2026-07-03");
  assert.equal(byKey.fundamental.stale, false);
  assert.equal(byKey.fundamental.date, "202606");
  assert.equal(out.anyStale, true);
});

test("STALE_THRESHOLDS is centrally defined", () => {
  assert.equal(typeof STALE_THRESHOLDS.quoteTradingDays, "number");
  assert.equal(typeof STALE_THRESHOLDS.institutionalTradingDays, "number");
});
