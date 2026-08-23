import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Today exposes an auditable six-state section contract", async () => {
  const [home, adapter, page] = await Promise.all([
    read("lib/today-home.ts"),
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);

  assert.match(home, /TodayHomeSectionState = TodayHomePublicationState \| "LOADING" \| "ERROR"/);
  assert.match(adapter, /TodaySectionState = Exclude<TodayHomeSectionState, "LOADING">/);
  assert.match(adapter, /resource\.transportState === "ERROR"/);
  assert.match(adapter, /return "ERROR"/);
  assert.match(adapter, /const state = resource\.publicationState/);
  assert.match(page, /ERROR: "Load error"/);
  assert.match(page, /role=\{isError \? "alert" : "status"\}/);
});

test("Today surfaces freshness, source, and data-quality metadata without classification logic in the browser", async () => {
  const [home, adapter, page] = await Promise.all([
    read("lib/today-home.ts"),
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);

  for (const field of ["generatedAt", "latestSnapshotTime", "qualityNotes"]) {
    assert.match(home, new RegExp(`${field}:`));
    assert.match(adapter, new RegExp(`resource\.metadata\.${field}`));
    assert.match(page, new RegExp(field));
  }
  assert.match(page, /data-quality-disclosure/);
  assert.match(page, /friendlySourceName/);
  assert.doesNotMatch(page, /Date\.now\(|new Date\(\).*data|freshness.*classification/i);
});

test("Today keeps one Home request and never substitutes Preview/mock data after transport failure", async () => {
  const [home, adapter, page] = await Promise.all([
    read("lib/today-home.ts"),
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);

  assert.equal((home.match(/client\.getHome\(/g) ?? []).length, 1);
  assert.match(home, /return errorTodayHomeResource\(error instanceof Error/);
  assert.match(adapter, /transportErrorReason/);
  assert.doesNotMatch(`${home}\n${adapter}\n${page}`, /mock|snapshot fallback|fallback hardcoded/i);
  assert.doesNotMatch(`${home}\n${adapter}\n${page}`, /\.sort\(|changePct|strengthScore|turnover\s*[:=].*(calculate|derive|reduce|\+)|score derivation|freshness calculation/i);
});

test("Today sections preserve Temporary instead of collapsing partial Home data to Unavailable", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);

  assert.match(adapter, /let state: TodaySectionState = stateFromHomeResource/);
  assert.match(adapter, /if \(state === "FORMAL" && data\.temporary\) state = "TEMPORARY"/);
  assert.match(adapter, /state === "FORMAL"\n\s+\? null\n\s+: resource\.metadata\.reason/);
  assert.match(page, /state === "PREVIEW" \|\| mainlines\.resource\.state === "TEMPORARY"/);
  assert.match(page, /resource\.temporarySections\.includes\(sectionKey\)/);
  assert.match(page, /resource\.missingSections\.includes\(sectionKey\)/);
});
