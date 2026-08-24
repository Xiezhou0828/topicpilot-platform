import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Today Market Events reuse the single Home resource and the generated marketPulse contract", async () => {
  const [adapter, home, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("lib/today-home.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(home, /marketPulse: Array\.isArray\(home\.marketPulse\)/);
  assert.match(adapter, /HomeMarketPulseEvent/);
  assert.match(adapter, /marketEvents: TodayMarketEventsResource/);
  assert.match(adapter, /mapMarketEvents\(resource, previewEnabled\)/);
  assert.match(page, /mainlines\.resource\.marketEvents/);
  assert.equal((home.match(/client\.getHome\(/g) ?? []).length, 1);
});

test("Today Market Events preserve backend order and event authority", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  for (const field of ["eventTime", "topic", "eventType", "description", "severity", "topicSlug"]) {
    assert.match(adapter, new RegExp(`value\\.${field}`));
    assert.match(page, new RegExp(`event\\.${field}`));
  }
  assert.match(adapter, /value\.source/);
  assert.match(page, /resource\.data\.map\(\(event\)/);
  assert.doesNotMatch(`${adapter}\n${page}`, /marketEvents[\s\S]{0,1200}\.sort\(/);
  assert.doesNotMatch(page, /const events = \[/);
  assert.doesNotMatch(`${adapter}\n${page}`, /severity calculation|event derivation|ranking/i);
});

test("Today Market Events fail closed and preserve publication semantics", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);
  assert.match(adapter, /今日市場事件尚未提供/);
  assert.match(adapter, /state === "PREVIEW" && !previewEnabled/);
  assert.match(adapter, /state: TodayHomePublicationState/);
  assert.match(page, /resource\.state !== "FORMAL"/);
  assert.match(page, /resource\.state === "UNAVAILABLE"/);
  assert.doesNotMatch(page, /fallback hardcoded|mock formal/i);
});
