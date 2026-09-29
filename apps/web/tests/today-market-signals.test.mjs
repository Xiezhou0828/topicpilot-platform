import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const page = await readFile(new URL("../app/components/v2/TodayMarketPage.tsx", import.meta.url), "utf8");

test("Today market signals render only backend-active signals", () => {
  assert.match(page, /\.filter\(\(signal\) => signal\.isActive !== false\)/);
  assert.doesNotMatch(page, /signal\.key ===|signal\.name ===|signal\.title ===/);
});

test("Today market signals show at most five cards with explicit pagination", () => {
  assert.match(page, /const pageSize = 5/);
  assert.match(page, /signals\.slice\(safePage \* pageSize/);
  assert.match(page, /aria-label="上一組市場訊號"/);
  assert.match(page, /aria-label="下一組市場訊號"/);
  assert.match(page, /顯示 \{safePage \* pageSize \+ 1\}/);
  assert.doesNotMatch(page, /setInterval|setTimeout/);
});

test("Today market signal cards expose temporal and deterministic frequency fields", () => {
  assert.match(page, /signal\.signalTemporalStatus === "NEW"/);
  assert.match(page, /延續第 \$\{signal\.streakDays\} 日/);
  assert.match(page, /近20日發生 \$\{signal\.occurrenceDays20d\} 日/);
  assert.match(page, /signal\.frequencyMessage \?\? signal\.summary/);
});
