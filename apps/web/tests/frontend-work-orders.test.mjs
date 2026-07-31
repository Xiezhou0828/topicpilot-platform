import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const snapshotUrl = new URL("../app/lib/web_snapshot.json", import.meta.url);

test("public frontend snapshot contains only the four synthetic issuers", async () => {
  const raw = JSON.parse(await readFile(snapshotUrl, "utf8"));
  assert.equal(raw.classification, "PUBLIC_SYNTHETIC");
  assert.deepEqual(Object.keys(raw.stocks), ["DEMO-A1", "DEMO-B2", "DEMO-C3", "DEMO-D4"]);
  assert.equal(raw.quoteMeta.source, "TopicPilot public portfolio demo");
});

test("fourteen-day synthetic topic history is preserved", async () => {
  const raw = JSON.parse(await readFile(snapshotUrl, "utf8"));
  const edgeAi = raw.topicStrengthHistory.find((item) => item.slug === "edge-ai");
  assert.equal(edgeAi.points.length, 14);
});
