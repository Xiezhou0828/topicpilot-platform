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
const { loadCatalog, catalogHref } = await import(moduleUrl(resolve(app, "lib/topic-catalog.ts")));
const { CatalogContent, TopicCatalogDetail } = await import(moduleUrl(resolve(app, "components/v2/TopicCatalogPage.tsx")));
const asOf = "2026-08-28";
const availability = (state, reason = null) => ({ state, reason, reasonCode: reason, asOf });
const ref = { authority: "synthetic.fixture", asOf, version: "fixture.v1" };
function leaf() {
  return { topicId: "leaf-id", slug: "solar", name: "Synthetic Solar", kind: "LEAF", status: "ACTIVE", enabled: true, asOf,
    availability: availability("AVAILABLE"), hierarchy: { kind: "LEAF", parents: [{ topicId: "parent-id", slug: "energy", name: "Synthetic Energy" }], children: [] },
    members: [{ instrumentId: "synthetic-id", code: "TEST", name: "Synthetic Stock", market: "TEST", relationType: "MEMBER", relationVersion: "fixture.v1", validFrom: "2026-08-07", validTo: asOf }],
    membersAvailability: availability("AVAILABLE"), source: { identity: ref, hierarchy: ref, members: ref, snapshot: ref },
    currentFormalSnapshot: { availability: availability("UNAVAILABLE", "FORMAL_SNAPSHOT_NOT_PUBLISHED"), snapshot: null } };
}
const detail = (topic) => renderToStaticMarkup(React.createElement(TopicCatalogDetail, { topic }));
const content = (resource) => renderToStaticMarkup(React.createElement(CatalogContent, { resource, retry() {} }));

test("Parent presents NOT_APPLICABLE members and snapshot, with date-bound child navigation", () => {
  const topic = leaf();
  topic.kind = "PARENT";
  topic.hierarchy = { kind: "PARENT", parents: [], children: [{ topicId: "leaf-id", slug: "solar", name: "Synthetic Solar" }] };
  topic.membersAvailability = availability("NOT_APPLICABLE");
  topic.currentFormalSnapshot.availability = availability("NOT_APPLICABLE");
  const html = detail(topic);
  assert.equal((html.match(/data-availability="NOT_APPLICABLE"/g) ?? []).length, 2);
  assert.match(html, /\/topics\/solar\?asOf=2026-08-28/);
  assert.doesNotMatch(html, /Synthetic Stock|0 members/);
});

test("Leaf preserves backend effective membership, inclusive dates and source versions", async () => {
  const topic = leaf();
  let url;
  const result = await loadCatalog({ slug: topic.slug, asOf }, { baseUrl: "https://fixture.invalid", fetchImpl: async (input) => { url = input; return { ok: true, json: async () => topic }; } });
  assert.equal(url, "https://fixture.invalid/api/v2/topic-catalog/solar?asOf=2026-08-28");
  assert.deepEqual(result.data.members, topic.members);
  const html = detail(result.data);
  for (const text of ["Synthetic Stock", "2026-08-07", asOf, "fixture.v1", "synthetic.fixture"]) {
    assert.ok(html.includes(text));
  }
  assert.match(html, /\/topics\/energy\?asOf=2026-08-28/);
});

test("zero available members is distinct from unavailable and NOT_APPLICABLE", () => {
  const topic = leaf();
  topic.members = [];
  assert.match(detail(topic), /data-members-state="EMPTY"/);
  topic.membersAvailability = availability("UNAVAILABLE", "PRE_FORMAL_MEMBERSHIP_BOUNDARY");
  const html = detail(topic);
  assert.match(html, /PRE_FORMAL_MEMBERSHIP_BOUNDARY/);
  assert.doesNotMatch(html, /0 members|data-members-state="EMPTY"/);
});

test("loading, missing configuration, request error and successful empty list stay distinct", async () => {
  assert.match(content({ state: "LOADING", data: null }), /data-state="LOADING"/);
  const missing = await loadCatalog({}, { baseUrl: null });
  assert.match(content(missing), /data-state="UNAVAILABLE"/);
  const error = await loadCatalog({}, { baseUrl: "https://fixture.invalid", fetchImpl: async () => { throw new Error("private stack"); } });
  assert.match(content(error), /data-state="ERROR"/);
  assert.doesNotMatch(content(error), /private stack|沒有題材/);
  assert.match(content({ state: "AVAILABLE", data: { items: [], total: 0, limit: 100, offset: 0, asOf } }), /沒有題材/);
});

test("list and detail share identity, hierarchy and asOf without score/grade lanes", async () => {
  const topic = leaf();
  let url;
  const result = await loadCatalog({ asOf, offset: 100 }, { baseUrl: "https://fixture.invalid", fetchImpl: async (input) => { url = input; return { ok: true, json: async () => ({ items: [topic], total: 101, offset: 100, limit: 100, asOf }) }; } });
  assert.match(url, /limit=100&offset=100&asOf=2026-08-28/);
  for (const text of [topic.name, topic.kind, asOf, "Synthetic Energy"]) {
    assert.ok(content(result).includes(text));
    assert.ok(detail(topic).includes(text));
  }
  assert.doesNotMatch(content(result), new RegExp(`${topic.slug} · ${topic.topicId}`));
  assert.doesNotMatch(content(result), /enabled (true|false)/);
  assert.equal(catalogHref("a/b", asOf), "/topics/a%2Fb?asOf=2026-08-28");
  assert.doesNotMatch(content(result), /tp-grade|laneGrade|topicScore/);
});

test("formal snapshot reference and publication metadata remain visible", () => {
  const topic = leaf();
  topic.currentFormalSnapshot = { availability: availability("AVAILABLE"), snapshot: { topicId: topic.topicId, topicSlug: topic.slug, snapshotDate: asOf, source: { authority: "topicpilot.topic_snapshots", referenceRegistryVersion: "synthetic.registry", sourceRunId: "synthetic.run", lineageHash: "synthetic.hash" }, publication: { mode: "FORMAL", state: "PUBLISHED", publishedAt: "2026-08-28T10:00:00Z", membershipMode: "PIT_FORMAL", finalityState: "FINAL", snapshotIdentity: "synthetic.snapshot" } } };
  const html = detail(topic);
  for (const value of ["synthetic.registry", "synthetic.run", "synthetic.hash", "FORMAL", "PUBLISHED", "2026-08-28T10:00:00Z"]) assert.ok(html.includes(value));
});

test("omitted optional membership and hierarchy arrays remain unknown, not empty", () => {
  const topic = leaf();
  delete topic.members;
  delete topic.hierarchy.parents;
  const html = detail(topic);
  assert.match(html, /data-members-state="UNKNOWN"/);
  assert.match(html, /階層資料未提供/);
  assert.doesNotMatch(html, /0 members|無上層關係/);
});

test("both public Topic routes use catalog and preserve the asOf query", () => {
  for (const path of ["topics/page.tsx", "topics/[slug]/page.tsx"]) {
    const source = readFileSync(resolve(app, path), "utf8");
    assert.match(source, /<TopicCatalogPage/);
    assert.match(source, /asOf=\{asOf\}/);
    assert.doesNotMatch(source, /<V2Page|<TopicDetailPage/);
  }
});
