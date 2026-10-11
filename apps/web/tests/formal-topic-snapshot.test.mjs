import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("formal Topic Snapshot consumer follows the current catalog contract", async () => {
  const [consumer, client, topicApi] = await Promise.all([
    read("lib/formal-topic-snapshot.ts"),
    read(new URL("../../../packages/api-client/src/client.mjs", app)),
    read("lib/topic-api.ts"),
  ]);
  assert.match(consumer, /TopicFormalSnapshotRead/);
  assert.match(client, /getCurrentTopicSnapshot/);
  assert.match(client, /topic-catalog\/\$\{encodeURIComponent\(slug\)\}\/snapshot/);
  assert.match(consumer, /publication\.mode/);
  assert.match(consumer, /publication\.state/);
  assert.match(consumer, /membershipMode/);
  assert.match(consumer, /finalityState/);
  assert.match(consumer, /source\.lineageHash/);
  assert.match(topicApi, /toFormalTopicSnapshotResource\(catalog\.currentFormalSnapshot\)/);
  assert.doesNotMatch(consumer, /web_snapshot|synthetic|fallback/i);
});

test("formal Topic Snapshot consumer exposes provenance metadata and fails closed", async () => {
  const consumer = await read("lib/formal-topic-snapshot.ts");
  for (const field of ["asOf", "source", "publicationStatus", "publishedAt"]) {
    assert.match(consumer, new RegExp(`${field}:`));
  }
  assert.match(consumer, /availability\.state !== "AVAILABLE"/);
  assert.match(consumer, /return \{ state: "UNAVAILABLE", data: null, metadata, reason \}/);
});
