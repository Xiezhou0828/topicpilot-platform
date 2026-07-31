import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);

test("the original UI adapter accepts normalized FastAPI fields", async () => {
  const adapter = await readFile(new URL("lib/snapshot-adapter.ts", app), "utf8");
  for (const alias of ["close", "changePct", "volume", "dataDate", "stockName", "topicName", "groupName", "relationType"]) {
    assert.match(adapter, new RegExp(`\"${alias}\"`));
  }
  assert.match(adapter, /FastAPI \/ PostgreSQL read model/);
});

test("the committed fallback is reproducible and contains all six strategy IDs", async () => {
  const snapshot = JSON.parse(await readFile(new URL("lib/web_snapshot.json", app), "utf8"));
  assert.deepEqual(snapshot.strategyRegistry.strategies.map((item) => item.strategyId).sort(), ["BB", "KD", "MAS", "MAV", "PB", "TMC"]);
  assert.equal(snapshot.strategyCandidates.length, 6);
  assert.equal(snapshot.strategyPerformance.length, 6);
  const histories = snapshot.topicStrengthHistory.filter((item) => item.points.length > 0);
  assert.equal(histories.length, 3);
  assert.ok(histories.every((item) => item.points.length === 14));
});

test("public source does not point at the private R2 or AI workers", async () => {
  const [source, studio] = await Promise.all([
    readFile(new URL("lib/data-source.ts", app), "utf8"),
    readFile(new URL("studio/studio-client.ts", app), "utf8"),
  ]);
  assert.doesNotMatch(source, /production-mp3|r2\.dev|workers\.dev/);
  assert.doesNotMatch(studio, /workers\.dev/);
});
