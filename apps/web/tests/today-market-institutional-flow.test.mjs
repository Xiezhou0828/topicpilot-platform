import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const root = new URL("../app/", import.meta.url);
const read = (relative) => readFile(new URL(relative, root), "utf8");

test("Today Market renders the formal additive institutional-flow payload", async () => {
  const [page, types] = await Promise.all([
    read("components/v2/TodayMarketPage.tsx"),
    read("lib/generated-api.d.ts"),
  ]);
  assert.match(page, /overview\.institutionFlows/);
  assert.match(page, /current\?\.foreign\?\.net/);
  assert.match(page, /current\?\.investmentTrust\?\.net/);
  assert.match(page, /法人流向資料尚未提供/);
  assert.match(page, /data-flow-status=\{flow\.status\}/);
  assert.match(types, /institutionFlows\?: components\["schemas"\]\["HomeInstitutionalFlow"\]/);
  assert.doesNotMatch(page, /institutionFlows.*\|\|.*0/);
});
