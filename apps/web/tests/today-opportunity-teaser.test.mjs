import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("Today Opportunity is Formal only behind a field-level publication authority gate", async () => {
  const adapter = await read("lib/today-mainlines.ts");

  assert.match(adapter, /export type TodayOpportunityResource/);
  assert.match(adapter, /function hasFormalOpportunityAuthority/);
  assert.match(adapter, /resource\.publicationState === "FORMAL"/);
  assert.match(adapter, /!resource\.metadata\.temporarySections\.includes\("opportunities"\)/);
  assert.match(adapter, /!resource\.metadata\.missingSections\.includes\("opportunities"\)/);
  assert.match(adapter, /!hasShadowOpportunityData\(resource, data\)/);
  assert.match(adapter, /state: "FORMAL",\n\s+data,/);
});

test("Today Opportunity maps empty, incomplete, Shadow, Preview, and transport states fail-closed", async () => {
  const [adapter, page] = await Promise.all([
    read("lib/today-mainlines.ts"),
    read("components/v2/TodayMarketPage.tsx"),
  ]);

  assert.match(adapter, /Home\.opportunities is empty/);
  assert.match(adapter, /Home\.opportunities has incomplete fields/);
  assert.match(adapter, /state: "ERROR"/);
  assert.match(adapter, /state: "PREVIEW"/);
  assert.match(adapter, /resource\.publicationState !== "UNAVAILABLE" && previewEnabled/);
  assert.match(adapter, /Shadow or temporary data; explicit Today Preview is required/);
  assert.match(adapter, /No formal Today Opportunity publication authority is configured/);
  assert.match(page, /resource\.state === "FORMAL" \|\| resource\.state === "PREVIEW"/);
  assert.match(page, /resource\.state === "PREVIEW"/);
});

test("Today Opportunity removes the static teaser and browser-side recommendation derivation", async () => {
  const [page, adapter, home] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read("lib/today-mainlines.ts"),
    read("lib/today-home.ts"),
  ]);
  const source = `${home}\n${adapter}\n${page}`;

  assert.doesNotMatch(page, /const opportunities = \[/);
  assert.doesNotMatch(page, /href="\/opportunities"/);
  assert.doesNotMatch(page, /validatedStocks|strength|score|ranking|ranked|favorite|favorites/i);
  assert.doesNotMatch(source, /mock|fixture fallback|static teaser|snapshot fallback/i);
  assert.equal((home.match(/client\.getHome\(/g) ?? []).length, 1);
});
