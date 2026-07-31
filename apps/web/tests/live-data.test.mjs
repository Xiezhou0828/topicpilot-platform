import assert from "node:assert/strict";
import { test } from "node:test";
import {
  canShowTradeJudgement,
  evaluateLiveData,
  evaluateTriggerState,
  isTaiwanMarketSession,
  LIVE_REFRESH_INTERVAL_MS,
} from "../app/lib/live-data.mjs";

const complete = {
  source: "snapshot",
  dataDate: "2026-07-14",
  generatedAt: "2026-07-14T09:01:00+08:00",
  quoteUpdatedAt: "09:00:58",
  quoteStatus: "COMPLETE",
  latestTradingDate: "2026-07-14",
  marketSession: "OPEN",
  rowCount: 5,
};

test("classifies complete, stale and unavailable snapshots", () => {
  assert.equal(evaluateLiveData(complete, "2026-07-14").state, "LIVE");
  assert.equal(evaluateLiveData({ ...complete, marketSession: "CLOSED" }, "2026-07-14").state, "SNAPSHOT");
  const stale = evaluateLiveData({ ...complete, dataDate: "2026-07-10" }, "2026-07-14");
  assert.equal(stale.state, "STALE");
  assert.equal(stale.delayedTradingDays, 2);
  assert.match(stale.message, /目前不適合盤中交易/);
  const delayedBatch = evaluateLiveData(complete, "2026-07-16");
  assert.equal(delayedBatch.state, "STALE");
  assert.equal(delayedBatch.delayedTradingDays, 2);
  assert.equal(evaluateLiveData({ ...complete, quoteUpdatedAt: null }, "2026-07-14").state, "UNAVAILABLE");
  assert.equal(evaluateLiveData({ ...complete, rowCount: 0 }, "2026-07-14").state, "UNAVAILABLE");
  assert.equal(evaluateLiveData({ ...complete, quoteStatus: "PARTIAL" }, "2026-07-14").state, "UNAVAILABLE");
});

test("trigger presentation distinguishes waiting, near, hit and invalid", () => {
  assert.equal(evaluateTriggerState({ price: 98, trigger: 100, invalidation: 90, distance: 4 }, true).tone, "waiting");
  assert.equal(evaluateTriggerState({ price: 99, trigger: 100, invalidation: 90, distance: 1 }, true).tone, "near");
  assert.equal(evaluateTriggerState({ price: 100, trigger: 100, invalidation: 90, distance: 0 }, true).tone, "hit");
  assert.equal(evaluateTriggerState({ price: 89, trigger: 100, invalidation: 90, distance: 12 }, true).tone, "invalid");
  assert.equal(evaluateTriggerState({ price: 100, trigger: 100, invalidation: 90, distance: 0 }, false).tone, "disabled");
});

test("trade judgement needs both LIVE data and a numeric trigger", () => {
  assert.equal(canShowTradeJudgement("LIVE", 100), true);
  assert.equal(canShowTradeJudgement("LIVE", 100, "EXCEPTION"), false);
  assert.equal(canShowTradeJudgement("LIVE", null), false);
  for (const state of ["LOADING", "SNAPSHOT", "STALE", "ERROR", "UNAVAILABLE"]) {
    assert.equal(canShowTradeJudgement(state, 100), false);
  }
});

test("market-session polling window is deterministic in Taipei", () => {
  assert.equal(LIVE_REFRESH_INTERVAL_MS, 180_000);
  assert.equal(isTaiwanMarketSession(new Date("2026-07-14T01:00:00Z")), true);
  assert.equal(isTaiwanMarketSession(new Date("2026-07-14T05:40:00Z")), false);
  assert.equal(isTaiwanMarketSession(new Date("2026-07-12T01:00:00Z")), false);
});

test("A to B to C frames never inherit a prior trigger decision", () => {
  const frames = [
    { state: "LIVE", trigger: 101 },
    { state: "LIVE", trigger: null },
    { state: "STALE", trigger: 103 },
  ];
  assert.deepEqual(frames.map((frame) => canShowTradeJudgement(frame.state, frame.trigger)), [true, false, false]);
});
