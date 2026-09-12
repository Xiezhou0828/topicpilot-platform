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
      const dependency = [base, `${base}.ts`, `${base}.tsx`, `${base}.mjs`].find(existsSync);
      url = /\.tsx?$/.test(dependency) ? moduleUrl(dependency) : pathToFileURL(dependency).href;
    } else url = pathToFileURL(require.resolve(name)).href;
    return `from ${JSON.stringify(url)}`;
  });
  const url = `data:text/javascript;base64,${Buffer.from(result).toString("base64")}`;
  cache.set(path, url);
  return url;
}
const app = fileURLToPath(new URL("../app/", import.meta.url));
const { FORMAL_TECHNICAL_INDICATOR_IDS, fetchFormalStock, fetchFormalStockHistory, fetchFormalStockTechnical, technicalPresentationState } = await import(moduleUrl(resolve(app, "lib/stock-api.ts")));
const { StockEncyclopediaDrawer, StockEncyclopediaView, StockTechnicalEvidenceContent, formalDrawerItem, emptyFormalStock } = await import(moduleUrl(resolve(app, "components/v2/StockEncyclopediaDrawer.tsx")));
const { StockHistoryContent, historyStatus } = await import(moduleUrl(resolve(app, "components/v2/StockPriceHistoryPanel.tsx")));
const originalFetch = globalThis.fetch;
const originalBase = process.env.NEXT_PUBLIC_API_BASE_URL;
const stock = (market = "TPE") => ({ code: "9001", symbol: "9001", instrumentId: `${market}-fixture`, market, name: `Synthetic ${market}`, exchange: market, listing: "synthetic", price: 9999, changePct: 99, volume: 999, updateMode: "POST_CLOSE", dataFreshness: "STALE", retrievedAt: "2026-09-09T00:00:00Z", historyCoverage: {}, mainTopic: null, topicRelations: [{ topicName: "Synthetic relation", topicSlug: "fixture", topicRole: null }], technicalEvidence: null, institutionFlows: null, summary: null, opportunity: null,
  eod: { tradingDate: "2026-08-28", close: 123, change: null, changePct: null, open: 120, high: 124, low: 118, previousClose: null, volume: 55, turnover: null, dataStatus: "PARTIAL", adjustmentState: "UNKNOWN", priceSource: { sourceCode: "SYNTHETIC_OFFICIAL_FIXTURE" }, volumeSource: null, observedAt: "2026-08-28T06:00:00Z", retrievedAt: "2026-08-28T07:00:00Z" } });
const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props));
const props = { onClose() {}, onRetry() {}, detailError: null, detailState: "PUBLISHED" };
async function withApi(fetcher, fn) {
  process.env.NEXT_PUBLIC_API_BASE_URL = "https://fixture.invalid";
  globalThis.fetch = fetcher;
  try { await fn(); } finally { globalThis.fetch = originalFetch; if (originalBase === undefined) delete process.env.NEXT_PUBLIC_API_BASE_URL; else process.env.NEXT_PUBLIC_API_BASE_URL = originalBase; }
}
const response = (items) => new Response(JSON.stringify({ items, total: items.length, universe: {} }));

test("market-aware detail resolves exact formal list identity and rejects ambiguous code", async () => {
  await withApi(async (url) => {
    const parsed = new URL(url);
    assert.equal(parsed.pathname, "/api/v2/stocks");
    assert.equal(parsed.searchParams.get("search"), "9001");
    return response([stock("TPE"), stock("TWO")]);
  }, async () => {
    assert.equal((await fetchFormalStock("9001", { market: "TWO" })).data.market, "TWO");
    assert.equal((await fetchFormalStock("9001", { market: "TPE" })).data.market, "TPE");
    const ambiguous = await fetchFormalStock("9001");
    assert.equal(ambiguous.state, "UNAVAILABLE");
    assert.equal(ambiguous.data, null);
    assert.equal((await fetchFormalStock("9001", { market: "INVALID" })).state, "UNAVAILABLE");
  });
});

test("formal detail handles missing, HTTP failure and unconfigured origin without fallback", async () => {
  await withApi(async () => response([]), async () => assert.equal((await fetchFormalStock("9001")).state, "EMPTY"));
  await withApi(async () => new Response("no", { status: 503 }), async () => {
    const result = await fetchFormalStock("9001");
    assert.equal(result.state, "ERROR"); assert.equal(result.data, null);
  });
  await withApi(async () => { throw new Error("must not fetch"); }, async () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    assert.equal((await fetchFormalStock("9001")).state, "UNAVAILABLE");
  });
});

test("first paint suppresses bundled and caller values on both Drawer and standalone", () => {
  const contaminated = { ...formalDrawerItem(stock()), name: "LEGACY NAME", price: 777777, eod: { ...stock().eod, close: 777777 }, topics: [{ name: "LEGACY TOPIC", role: "PRIMARY" }], mainTopic: { name: "LEGACY MAIN" }, summary: "LEGACY SUMMARY" };
  for (const presentation of ["inline", "push", "overlay"]) {
    const html = render(StockEncyclopediaDrawer, { ...props, presentation, stock: contaminated });
    assert.match(html, /LOADING/);
    assert.doesNotMatch(html, /777,777|LEGACY|2026-08-28|data-history-status/);
  }
});

test("standalone and Drawer render identical core EOD date/source/identity and raw history component", () => {
  const item = formalDrawerItem(stock("TWO"));
  const inline = render(StockEncyclopediaView, { ...props, stock: item, presentation: "inline" });
  const push = render(StockEncyclopediaView, { ...props, stock: item, presentation: "push" });
  for (const html of [inline, push]) {
    for (const marker of ["TWO:9001", "123.00", "2026-08-28", "SYNTHETIC_OFFICIAL_FIXTURE", "PARTIAL", "STALE", "UNKNOWN", "data-history-status", "Synthetic relation", "正式主題欄位尚未提供"]) assert.ok(html.includes(marker), marker);
    assert.doesNotMatch(html, /9,999|20MA|60MA/);
  }
  assert.match(inline, /data-stock-read-state="PARTIAL"/);
  assert.match(push, /href="\/stocks\/9001\?market=TWO"/);
  assert.match(push, /target="_blank"/);
  assert.equal(item.updatedAt, stock().eod.retrievedAt);
  assert.equal(item.mainTopic, null);
  assert.equal(item.topics[0].role, null);
});

test("loading/error/unavailable/empty states render no inherited formal facts", () => {
  for (const detailState of ["LOADING", "ERROR", "UNAVAILABLE", "EMPTY"]) {
    const html = render(StockEncyclopediaView, { ...props, stock: emptyFormalStock(formalDrawerItem(stock())), detailState });
    assert.match(html, new RegExp(`data-stock-read-state="${detailState}"`));
    assert.doesNotMatch(html, /123.00|SYNTHETIC_OFFICIAL_FIXTURE|Synthetic relation/);
    if (detailState === "ERROR") assert.match(html, /重新讀取/);
    if (detailState === "UNAVAILABLE") assert.doesNotMatch(html, /重新讀取/);
  }
  const html = render(StockEncyclopediaView, { ...props, stock: formalDrawerItem({ ...stock(), topicRelations: [], eod: null }) });
  assert.match(html, /目前正式題材關係為 0 筆/);
  assert.match(html, /正式 EOD 尚未提供/);
  assert.doesNotMatch(html, /9,999/);
});

const history = () => ({ code: "9001", market: "TWO", status: "AVAILABLE", coverageState: "AVAILABLE", freshnessState: "STALE", asOf: "2026-08-28T07:00:00Z", returnedFrom: "2026-08-28", returnedTo: "2026-08-28", pointCount: 1, hasMore: false,
  items: [{ tradingDate: "2026-08-28", close: 123, volume: null, adjustmentState: "UNKNOWN", sourceCode: "SYNTHETIC_OFFICIAL_FIXTURE" }] });

test("raw history request and returned identity are market-bound", async () => {
  await withApi(async (url) => {
    assert.equal(new URL(url).searchParams.get("market"), "TWO");
    return new Response(JSON.stringify(history()));
  }, async () => assert.equal((await fetchFormalStockHistory("9001", { market: "TWO" })).data.market, "TWO"));
  await withApi(async () => new Response(JSON.stringify(history())), async () => {
    const result = await fetchFormalStockHistory("9001", { market: "TPE" });
    assert.equal(result.state, "ERROR"); assert.equal(result.data, null);
  });
});

test("raw history preserves unknown adjustment, nulls, source and stale asOf; does not promote unavailable bars", () => {
  const data = history();
  assert.equal(historyStatus(data), "AVAILABLE");
  assert.equal(historyStatus({ ...data, status: "UNAVAILABLE" }), "UNAVAILABLE");
  assert.equal(historyStatus({ ...data, items: [] }), "EMPTY");
  const html = render(StockHistoryContent, { data, status: "AVAILABLE", error: null });
  for (const marker of ["Raw observed daily price history", "UNKNOWN", "STALE", "2026-08-28", "SYNTHETIC_OFFICIAL_FIXTURE", "—"]) assert.ok(html.includes(marker), marker);
  for (const status of ["LOADING", "EMPTY", "UNAVAILABLE", "ERROR"]) {
    const html = render(StockHistoryContent, { data: null, status, error: null });
    assert.ok(html.includes(`data-history-status="${status}"`));
    assert.doesNotMatch(html, /<table/);
  }
});

test("route uses shared formal consumer and preserves browser back; no legacy screening/trigger", () => {
  const route = readFileSync(resolve(app, "stocks/[code]/page.tsx"), "utf8");
  assert.match(route, /StockEncyclopediaDrawer/); assert.match(route, /get\("market"\)/);
  assert.match(route, /router.back\(\)/); assert.match(route, /router.push\("\/stocks"\)/);
  assert.doesNotMatch(route, /useSnapshot|evaluateTriggerState|StockSignalLamps|bundle|screener/);
  const explorer = readFileSync(resolve(app, "components/v2/StockExplorerPage.tsx"), "utf8");
  assert.match(explorer, /\[\`\$\{row.market\}:\$\{row.code\}\`, row\]/);
  assert.match(explorer, /selected\?\.market === stock.market/);
});

const technicalEvidence = (indicatorId, overrides = {}) => ({
  actualObservationCount: 60,
  actualObservationWindow: { startSession: "2026-06-01", endSession: "2026-08-28", observationCount: 60 },
  algorithmId: `formal.${indicatorId.toLowerCase()}.v1`,
  algorithmVersion: "v1",
  asOf: "2026-08-28T07:00:00Z",
  availabilityReason: null,
  continuityEvidence: {},
  continuityState: "CONTINUITY_PASS_BOUNDED",
  eventAuthorityStatus: "NO_KNOWN_EVENT_EVIDENCE",
  eventLookupEvidence: {},
  eventLookupState: "NO_KNOWN_VERIFIED_BREAKING_EVENT_FOUND",
  indicatorFamily: "SYNTHETIC_TEST_FAMILY",
  indicatorId,
  indicatorVersion: "v1",
  instrumentIdentity: "TWO-fixture",
  knownEventHandling: [],
  limitationReasons: [],
  market: "TWO",
  parameterSet: {},
  priceBasis: "RAW_OBSERVED",
  publicationState: "FORMAL",
  requiredObservationCount: 60,
  requiredObservationWindow: { startSession: "2026-06-01", endSession: "2026-08-28", observationCount: 60 },
  sessionDate: "2026-08-28",
  sourceAuthority: "V2_CANONICAL_OBSERVATION_CHAIN",
  sourceLineage: {},
  symbol: "9001",
  value: "123.456789",
  ...overrides,
});

const technical = (overrides = {}) => ({
  adjustmentPolicyId: "raw-observed-known-event-v1",
  algorithmId: "technical-v0",
  algorithmVersion: "v1",
  asOf: "2026-08-28T07:00:00Z",
  availabilityReasons: [],
  browserCalculationAllowed: "NO",
  calculationOwner: "BACKEND_ONLY",
  code: "9001",
  continuityPolicy: "FORMAL_RAW_OBSERVED + KNOWN_EVENT_AWARE_OFFICIAL_OVERLAY",
  deferredIndicatorFamilies: [],
  eventAuthorityStatus: "NO_KNOWN_EVENT_EVIDENCE",
  inputState: "RAW_OBSERVED",
  limitationReasons: [],
  market: "TWO",
  parameterSetId: "technical-v0",
  priceBasis: "RAW_OBSERVED",
  publicationState: "FORMAL",
  publicationStatus: "AVAILABLE",
  publishedIndicators: ["MA20", "RSI14"],
  reasonCodes: [],
  requestedFrom: "2000-01-01",
  requestedTo: "2026-08-28",
  status: "FORMAL",
  technicalContractVersion: "stock-technical-v0.v1",
  technicalEligibility: "ELIGIBLE",
  technicalEvidence: [
    technicalEvidence("MA20", { sessionDate: "2026-08-27", value: "999999" }),
    ...FORMAL_TECHNICAL_INDICATOR_IDS.map((indicatorId) => technicalEvidence(indicatorId, indicatorId === "RSI14" ? { value: "55.125" } : {})),
  ],
  technicalPolicyVersion: "stock-technical-v0-policy.v4",
  technicalResultStatus: "VALID",
  provenance: {
    authority: "V2_CANONICAL_OBSERVATION_CHAIN",
    seriesSemantics: "RAW_OBSERVED_DAILY_BAR",
    adjustmentState: "UNKNOWN",
    qualityStates: [], observationSemantics: [], sourceCodes: ["SYNTHETIC_OFFICIAL_FIXTURE"], adapterVersions: [], normalizationContractVersions: [], mappingPolicyVersions: [], referenceDataVersions: [],
    lineageState: "VERSIONED", observationCount: 60, returnedFrom: "2026-06-01", returnedTo: "2026-08-28", latestTradingDate: "2026-08-28", latestObservedAt: "2026-08-28T06:00:00Z", latestRetrievedAt: "2026-08-28T07:00:00Z",
  },
  ...overrides,
});

test("formal technical request is market/date bound and rejects mismatched authority identity", async () => {
  await withApi(async (url) => {
    const parsed = new URL(url);
    assert.equal(parsed.pathname, "/api/v2/stocks/9001/technical");
    assert.equal(parsed.searchParams.get("market"), "TWO");
    assert.equal(parsed.searchParams.get("to"), "2026-08-28");
    assert.equal(parsed.searchParams.get("limit"), "200");
    return new Response(JSON.stringify(technical()));
  }, async () => {
    const result = await fetchFormalStockTechnical("9001", { market: "TWO", sessionDate: "2026-08-28" });
    assert.equal(result.state, "AVAILABLE");
    assert.equal(result.data.market, "TWO");
  });
  await withApi(async () => new Response(JSON.stringify(technical({ market: "TPE" }))), async () => {
    const result = await fetchFormalStockTechnical("9001", { market: "TWO", sessionDate: "2026-08-28" });
    assert.equal(result.state, "ERROR");
    assert.equal(result.data, null);
  });
});

test("technical state keeps limited evidence partial and authority failure unavailable", () => {
  assert.deepEqual(FORMAL_TECHNICAL_INDICATOR_IDS, ["MA5", "MA10", "MA20", "MA60", "DISTANCE_TO_MA20", "RAW_CLOSE_RETURN_5D", "RAW_CLOSE_RETURN_20D", "VOLUME_MA5", "VOLUME_MA20", "VOLUME_RATIO_20", "RSI14", "MACD_12_26_9", "MACD_SIGNAL_12_26_9", "MACD_HISTOGRAM_12_26_9"]);
  assert.equal(technicalPresentationState(technical()), "AVAILABLE");
  assert.equal(technicalPresentationState(technical({ publicationStatus: "AVAILABLE_WITH_LIMITATION", publicationState: "FORMAL_WITH_LIMITATION" })), "PARTIAL");
  assert.equal(technicalPresentationState(technical({ technicalEvidence: [technicalEvidence("MA20"), technicalEvidence("RSI14", { value: null, publicationState: "UNAVAILABLE", availabilityReason: "UNAVAILABLE_INSUFFICIENT_HISTORY" })] })), "PARTIAL");
  assert.equal(technicalPresentationState(technical({ publicationStatus: "BLOCKED", publicationState: "UNAVAILABLE", technicalEvidence: [] })), "UNAVAILABLE");
  assert.equal(technicalPresentationState(technical({ publicationStatus: "AVAILABLE", technicalEvidence: [] })), "EMPTY");
});

test("technical evidence shows formal source/asOf and only backend-published session values", () => {
  const available = { source: "api", data: technical(), error: null, state: "AVAILABLE" };
  const html = render(StockTechnicalEvidenceContent, { resource: available, state: "AVAILABLE" });
  for (const marker of ["data-technical-state=\"AVAILABLE\"", "MA20", "RSI14", "123.456789", "55.125", "V2_CANONICAL_OBSERVATION_CHAIN", "RAW_OBSERVED_DAILY_BAR", "2026-08-28T07:00:00Z", "契約未發布", "BACKEND"] ) assert.match(html, new RegExp(marker));
  assert.doesNotMatch(html, /999999|買進|賣出|突破/);

  const partialData = technical({
    publicationStatus: "AVAILABLE_WITH_LIMITATION",
    publicationState: "FORMAL_WITH_LIMITATION",
    limitationReasons: ["EVENT_LOOKUP_UNAVAILABLE"],
    technicalEvidence: FORMAL_TECHNICAL_INDICATOR_IDS.map((indicatorId) => technicalEvidence(indicatorId, { publicationState: "FORMAL_WITH_LIMITATION", limitationReasons: ["EVENT_LOOKUP_UNAVAILABLE"] })),
  });
  const partial = render(StockTechnicalEvidenceContent, { resource: { source: "api", data: partialData, error: null, state: "PARTIAL" }, state: "PARTIAL" });
  assert.match(partial, /data-technical-state="PARTIAL"/);
  assert.match(partial, /FORMAL_WITH_LIMITATION/);
  assert.match(partial, /EVENT_LOOKUP_UNAVAILABLE/);
});

test("technical loading, unavailable and transport error remain distinct", () => {
  const cases = [
    ["LOADING", null, /正在讀取正式技術證據/, false],
    ["UNAVAILABLE", { source: "api", data: technical({ publicationStatus: "BLOCKED", publicationState: "UNAVAILABLE", reasonCodes: ["CONTINUITY_FAIL"] }), error: null, state: "UNAVAILABLE" }, /CONTINUITY_FAIL/, false],
    ["ERROR", { source: "unavailable", data: null, error: "HTTP 503", state: "ERROR" }, /HTTP 503/, true],
  ];
  for (const [state, resource, message, retryable] of cases) {
    const html = render(StockTechnicalEvidenceContent, { resource, state, onRetry() {} });
    assert.match(html, new RegExp(`data-technical-state="${state}"`));
    assert.match(html, message);
    assert.equal(html.includes("重新讀取技術證據"), retryable);
  }
});

test("shared Drawer/detail consumer ignores legacy browser-shaped technical fields", () => {
  const contaminated = formalDrawerItem({ ...stock("TWO"), technicalEvidence: { above20MA: true, above60MA: true, ma20: 1, ma60: 2, breakoutState: "LEGACY_BREAKOUT", technicalState: "LEGACY_TECHNICAL" } });
  for (const presentation of ["inline", "push"]) {
    const html = render(StockEncyclopediaView, { ...props, stock: contaminated, presentation });
    assert.match(html, /data-technical-state="LOADING"/);
    assert.doesNotMatch(html, /LEGACY_BREAKOUT|LEGACY_TECHNICAL|above20MA/);
  }
  const source = readFileSync(resolve(app, "components/v2/StockEncyclopediaDrawer.tsx"), "utf8");
  assert.match(source, /fetchFormalStockTechnical/);
  assert.doesNotMatch(source, /above20MA|above60MA|breakoutState|technicalState/);
  assert.doesNotMatch(source, /reduce\(|movingAverage|calculate|evaluateTriggerState/);
});
