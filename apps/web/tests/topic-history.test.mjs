import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";
import ts from "typescript";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

// Execute the real typed consumer and React views, without a live API or database.
const require = createRequire(import.meta.url);
const cache = new Map();
function moduleUrl(path) {
  if (cache.has(path)) return cache.get(path);
  const result = ts.transpileModule(readFileSync(path, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 },
    fileName: path,
  }).outputText.replace(/from (["'])([^"']+)\1/g, (_, quote, name) => {
    let url;
    if (name.startsWith(".")) {
      const base = resolve(dirname(path), name);
      const dependency = [base, `${base}.ts`, `${base}.tsx`].find(existsSync);
      url = /\.tsx?$/.test(dependency) ? moduleUrl(dependency) : pathToFileURL(dependency).href;
    } else url = pathToFileURL(require.resolve(name)).href;
    return `from ${JSON.stringify(url)}`;
  });
  const url = `data:text/javascript;base64,${Buffer.from(result).toString("base64")}`;
  cache.set(path, url);
  return url;
}
const app = fileURLToPath(new URL("../app/", import.meta.url));
const { loadTopicHistory, historyWindow, currentSnapshot } = await import(moduleUrl(resolve(app, "lib/topic-history.ts")));
const { HistoryContent, TopicSnapshotHistory, SnapshotTable } = await import(moduleUrl(resolve(app, "components/v2/TopicSnapshotHistory.tsx")));
const { TopicCatalogDetail } = await import(moduleUrl(resolve(app, "components/v2/TopicCatalogPage.tsx")));
const asOf = "2026-08-28";
const availability = (state = "AVAILABLE", reasonCode = null) => ({ state, asOf, reasonCode, reason: reasonCode });
function snapshot(date = asOf) {
  return { topicId: "fixture-leaf", topicSlug: "synthetic/leaf", topicName: "Synthetic Leaf", snapshotDate: date,
    stockCount: 8, observedStockCount: 5, averageChange: -1.25, coveragePct: null, topicScore: null, marketGrade: null,
    dataStatus: "PARTIAL", scoreStatus: "UNAVAILABLE", calculationVersion: "fixture.calc", asOfAt: `${date}T08:00:00Z`,
    source: { authority: "topicpilot.topic_snapshots", sourceRunId: "fixture.run", sourceArtifactId: "fixture.artifact", sourceArtifactHash: "fixture.artifact.hash", lineageHash: "fixture.lineage", referenceRegistryVersion: "fixture.registry", mappingPolicyVersion: "fixture.mapping", asOfAt: `${date}T08:00:00Z` },
    publication: { mode: "FORMAL", state: "PUBLISHED", membershipMode: "PIT_FORMAL", finalityState: "FINAL", snapshotIdentity: `fixture:${date}`, correctionSequence: 0,
      relationVersion: "fixture.relation", mappingEffectiveFrom: "2026-08-07", membershipSnapshotId: "fixture.members", membershipSnapshotHash: "fixture.members.hash", generatedAt: null, finalizedAt: null, publishedAt: `${date}T09:00:00Z` } };
}
function topic() {
  return { topicId: "fixture-leaf", slug: "synthetic/leaf", name: "Synthetic Leaf", kind: "LEAF", asOf,
    status: "ACTIVE", enabled: true, availability: availability(), hierarchy: { kind: "LEAF", parents: [], children: [] },
    members: [], membersAvailability: availability(), source: {}, currentFormalSnapshot: { availability: availability(), snapshot: snapshot() } };
}
const page = (items = [snapshot()], state = "AVAILABLE", reasonCode = null) => ({ items, total: items.length, limit: 100, offset: 0, asOf, availability: availability(state, reasonCode) });
const options = (data, requests = []) => ({ baseUrl: "https://fixture.invalid", fetchImpl: async (url, init) => { requests.push({ url, init }); return new Response(JSON.stringify(data)); } });
const html = (resource) => renderToStaticMarkup(React.createElement(HistoryContent, { resource, retry() {}, onPage() {} }));

test("five formal sessions render unchanged through the bounded typed client", async () => {
  const items = [28, 27, 26, 25, 24].map((day) => snapshot(`2026-08-${day}`));
  const requests = [];
  const result = await loadTopicHistory(topic(), 0, options(page(items), requests));
  assert.equal(result.state, "AVAILABLE");
  assert.deepEqual(result.data.items, items);
  assert.equal(requests[0].url, "https://fixture.invalid/api/v2/topic-catalog/synthetic%2Fleaf/snapshots?limit=100&offset=0&asOf=2026-08-28&from=2026-08-07&to=2026-08-28");
  const rendered = html(result);
  assert.match(rendered, /此頁 5 筆/);
  for (const row of items) assert.ok(rendered.includes(row.snapshotDate));
  assert.match(rendered, /-1.25%/);
  assert.doesNotMatch(rendered, /15.session|Heating|Cooling/);
});

test("loading, transport errors, HTTP problems and missing configuration are distinct", async () => {
  assert.match(html({ state: "LOADING", data: null }), /data-history-state="LOADING"/);
  assert.match(html(await loadTopicHistory(topic(), 0, { baseUrl: null })), /data-history-state="UNAVAILABLE"/);
  for (const fetchImpl of [async () => { throw new Error("private stack"); }, async () => new Response(JSON.stringify({ detail: "private problem" }), { status: 503 })]) {
    const result = await loadTopicHistory(topic(), 0, { baseUrl: "https://fixture.invalid", fetchImpl });
    assert.match(html(result), /data-history-state="ERROR"/);
    assert.match(html(result), /重新載入題材/);
    assert.doesNotMatch(html(result), /private|此範圍尚無/);
  }
});

test("unconfigured history authority offers no transport retry or inherited facts", async () => {
  const resource = await loadTopicHistory(topic(), 0, { baseUrl: null });
  assert.equal(resource.state, "UNAVAILABLE");
  const rendered = html(resource);
  assert.match(rendered, /data-history-state="UNAVAILABLE"/);
  assert.match(rendered, /尚未設定題材資料來源/);
  assert.doesNotMatch(rendered, /<button|<table|fixture.run|-1.25/);
});

test("empty AVAILABLE and backend no-publication results retain original availability", async () => {
  for (const data of [page([]), page([], "UNAVAILABLE", "FORMAL_SNAPSHOT_NOT_PUBLISHED")]) {
    const result = await loadTopicHistory(topic(), 0, options(data));
    assert.equal(result.state, "EMPTY");
    assert.deepEqual(result.data.availability, data.availability);
    assert.match(html(result), /此範圍尚無正式歷史紀錄/);
  }
});

test("authority failure, pre-boundary and unknown unavailable reasons never become empty", async () => {
  for (const reason of ["FORMAL_SNAPSHOT_AUTHORITY_UNAVAILABLE", "PRE_FORMAL_SNAPSHOT_BOUNDARY", "UNKNOWN_REASON"]) {
    const result = await loadTopicHistory(topic(), 0, options(page([], "UNAVAILABLE", reason)));
    assert.equal(result.state, "UNAVAILABLE");
    assert.ok(html(result).includes(reason));
    assert.doesNotMatch(html(result), /此範圍尚無正式歷史紀錄/);
    assert.doesNotMatch(html(result), /重新載入題材/);
  }
});

test("Parent history stays NOT_APPLICABLE and makes no request even with rogue rows", async () => {
  const parent = { ...topic(), kind: "PARENT" };
  const result = await loadTopicHistory(parent, 0, { fetchImpl: async () => { assert.fail("Parent must not fetch Leaf history"); } });
  assert.equal(result.state, "NOT_APPLICABLE");
  assert.equal(currentSnapshot(parent), null);
  const rendered = renderToStaticMarkup(React.createElement(TopicSnapshotHistory, { topic: parent, retry() {} }));
  assert.match(rendered, /data-history-state="NOT_APPLICABLE"/);
  assert.doesNotMatch(rendered, /<table|-1.25/);
});

test("date window stays bounded after a year and across leap days without widening pagination", async () => {
  for (const value of [asOf, "2028-02-29", "2030-09-08"]) {
    const window = historyWindow(value);
    assert.equal(window.to, value);
    assert.ok(window.from >= "2026-08-07");
    assert.ok((Date.parse(window.to) - Date.parse(window.from)) / 86400000 <= 366);
  }
  assert.deepEqual(historyWindow("2026-08-06"), { from: "2026-08-06", to: "2026-08-06" });
  for (const invalid of ["2026-02-30", "junk"]) assert.throws(() => historyWindow(invalid));
  const requests = [];
  const data = { ...page(), total: 201, offset: 100 };
  const result = await loadTopicHistory(topic(), 100, options(data, requests));
  assert.match(requests[0].url, /limit=100&offset=100&asOf=2026-08-28&from=2026-08-07&to=2026-08-28/);
  assert.match(html(result), /上一頁歷史/);
  assert.match(html(result), /下一頁歷史/);
});

test("current and history share snapshot identity, dates, status, source and lineage rendering", async () => {
  const item = topic();
  const history = html(await loadTopicHistory(item, 0, options(page())));
  const current = renderToStaticMarkup(React.createElement(TopicCatalogDetail, { topic: item }));
  for (const value of ["fixture-leaf", "synthetic/leaf", "fixture:2026-08-28", "2026-08-28T08:00:00Z", "PARTIAL", "PUBLISHED", "PIT_FORMAL", "FINAL", "fixture.run", "fixture.lineage", "fixture.members.hash", "fixture.registry", "fixture.mapping", "fixture.artifact", "fixture.relation"]) {
    assert.ok(history.includes(value), `history ${value}`);
    assert.ok(current.includes(value), `current ${value}`);
  }
  assert.match(current, /data-history-state="LOADING"/);
});

test("foreign identity, date drift and mismatched current revision fail closed", async () => {
  for (const mutate of [
    (data) => { data.asOf = "2026-08-29"; },
    (data) => { data.availability.asOf = "2026-08-29"; },
    (data) => { data.items[0].topicId = "other"; },
    (data) => { data.items[0].topicSlug = "other"; },
    (data) => { data.items[0].snapshotDate = "2026-08-29"; },
    (data) => { data.items[0].snapshotDate = "2026-08-06"; },
    (data) => { data.items[0].publication.snapshotIdentity = "another revision"; },
    (data) => { data.items[0].publication.correctionSequence = 1; },
    (data) => { data.items[0].asOfAt = null; },
    (data) => { data.items[0].source.lineageHash = "other"; },
    (data) => { data.items[0].publication.membershipSnapshotHash = "other"; },
  ]) {
    const data = page(); mutate(data);
    const result = await loadTopicHistory(topic(), 0, options(data));
    assert.equal(result.state, "ERROR");
    assert.doesNotMatch(html(result), /<table/);
  }
});

test("research, shadow, unfinished and legacy sources cannot become formal history", async () => {
  for (const mutate of [
    (row) => { row.publication.mode = "RESEARCH"; },
    (row) => { row.publication.state = "SHADOW"; },
    (row) => { row.publication.membershipMode = "CURRENT"; },
    (row) => { row.publication.finalityState = "DRAFT"; },
    (row) => { row.source.authority = "legacy"; },
  ]) {
    const row = snapshot(); mutate(row);
    assert.equal((await loadTopicHistory(topic(), 0, options(page([row])))).state, "ERROR");
    const item = topic(); item.currentFormalSnapshot.snapshot = row;
    assert.equal(currentSnapshot(item), null);
  }
});

test("one row, nullable metrics, zero and observed counts render without recomputation", async () => {
  const row = snapshot(); row.averageChange = null; row.observedStockCount = 0;
  const data = page([row]);
  const result = await loadTopicHistory(topic(), 0, options(data));
  assert.deepEqual(result.data.items, [row]);
  assert.match(html(result), /此頁 1 筆/);
  assert.match(html(result), /<td>0 \/ 8<\/td>/);
  assert.match(html(result), /<td>未提供<\/td>/);
  row.averageChange = 0;
  assert.match(renderToStaticMarkup(React.createElement(SnapshotTable, { snapshots: [row] })), /<td>0%<\/td>/);
});

test("abort signal reaches typed transport; route and effect prevent stale topic results", async () => {
  const requests = [];
  const controller = new AbortController();
  await loadTopicHistory(topic(), 0, { ...options(page(), requests), signal: controller.signal });
  assert.equal(requests[0].init.signal, controller.signal);
  const source = readFileSync(resolve(app, "components/v2/TopicSnapshotHistory.tsx"), "utf8");
  assert.match(source, /if \(!controller.signal.aborted\) setResource\(next\)/);
  assert.match(source, /return \(\) => controller.abort\(\)/);
  assert.match(source, /setResource\(\{ state: "LOADING", data: null \}\)/);
  assert.doesNotMatch(readFileSync(resolve(app, "lib/topic-history.ts"), "utf8"), /getStocks|getTopicSnapshots\(|web_snapshot|\.reduce\(/);
});
