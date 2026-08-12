import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const adapterUrl = new URL("../app/lib/opportunity-shadow-adapter.ts", import.meta.url);

test("shadow adapter preserves backend semantic fields and caps", async () => {
  const source = await readFile(adapterUrl, "utf8");
  assert.match(source, /publicationStatus: \"SHADOW\"/);
  assert.match(source, /fullRankingRetained/);
  assert.match(source, /displayOrder/);
  assert.match(source, /qualificationProvenance/);
  assert.match(source, /topicSections/);
  assert.match(source, /backendCandidateCount/);
  assert.match(source, /shadowUiStateFromStatus/);
  assert.doesNotMatch(source, /minimumOpportunityScore|expectedReturn|buy=true|STRONG_BUY/);
});

test("shadow adapter exposes all UI state semantics", async () => {
  const source = await readFile(adapterUrl, "utf8");
  for (const state of ["LOADING", "READY", "EMPTY", "DEFERRED", "UNAVAILABLE", "ERROR"]) {
    assert.match(source, new RegExp(`\\\"${state}\\\"`));
  }
});
