import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";
import ts from "typescript";

const app = fileURLToPath(new URL("../app/", import.meta.url));
const require = createRequire(import.meta.url);
const moduleCache = new Map();

function moduleUrl(file) {
  if (moduleCache.has(file)) return moduleCache.get(file);
  const output = ts.transpileModule(readFileSync(file, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 },
    fileName: file,
  }).outputText.replace(/from (['"])([^'"]+)\1/g, (_, quote, name) => {
    if (!name.startsWith(".")) return `from ${JSON.stringify(pathToFileURL(resolve(dirname(file), name)).href)}`;
    const base = resolve(dirname(file), name);
    const dependency = [base, `${base}.ts`, `${base}.tsx`, `${base}.mjs`].find(existsSync);
    if (!dependency) throw new Error(`Cannot resolve ${name} from ${file}`);
    const url = /\.tsx?$/.test(dependency) ? moduleUrl(dependency) : pathToFileURL(dependency).href;
    return `from ${JSON.stringify(url)}`;
  });
  const url = `data:text/javascript;base64,${Buffer.from(output).toString("base64")}`;
  moduleCache.set(file, url);
  return url;
}

const stockApi = await import(moduleUrl(resolve(app, "lib/stock-api.ts")));
const originalFetch = globalThis.fetch;
const originalBase = process.env.NEXT_PUBLIC_API_BASE_URL;

function response(payload, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: { "content-type": "application/json" } });
}

function stock(market) {
  return {
    code: "9001", symbol: "9001", instrumentId: `${market}-9001`, market, name: `Fixture ${market}`,
    exchange: market, listing: "fixture", price: 123, changePct: 1, volume: 100,
    updateMode: "POST_CLOSE", dataFreshness: "STALE", retrievedAt: "2026-08-28T07:00:00Z",
    historyCoverage: {}, mainTopic: null, topicRelations: [], technicalEvidence: null,
    institutionFlows: null, summary: null, opportunity: null, eod: null,
  };
}

async function withApi(fetcher, callback) {
  process.env.NEXT_PUBLIC_API_BASE_URL = "https://fixture.invalid";
  globalThis.fetch = fetcher;
  try { await callback(); } finally {
    globalThis.fetch = originalFetch;
    if (originalBase === undefined) delete process.env.NEXT_PUBLIC_API_BASE_URL;
    else process.env.NEXT_PUBLIC_API_BASE_URL = originalBase;
  }
}

test("formal detail is exact-market and ambiguity-safe", async () => {
  await withApi(async (url) => {
    const parsed = new URL(url);
    assert.equal(parsed.pathname, "/api/v2/stocks");
    assert.equal(parsed.searchParams.get("search"), "9001");
    return response({ items: [stock("TPE"), stock("TWO")], total: 2, universe: {} });
  }, async () => {
    assert.equal((await stockApi.fetchFormalStock("9001", { market: "TWO" })).data.market, "TWO");
    const ambiguous = await stockApi.fetchFormalStock("9001");
    assert.equal(ambiguous.state, "UNAVAILABLE");
    assert.equal(ambiguous.data, null);
  });
});

test("formal detail failure, missing origin and invalid market fail closed", async () => {
  await withApi(async () => response({ items: [], total: 0, universe: {} }), async () => {
    assert.equal((await stockApi.fetchFormalStock("9001")).state, "EMPTY");
    assert.equal((await stockApi.fetchFormalStock("9001", { market: "BAD" })).state, "UNAVAILABLE");
  });
  await withApi(async () => response({ error: "down" }, 503), async () => {
    const result = await stockApi.fetchFormalStock("9001");
    assert.equal(result.state, "ERROR");
    assert.equal(result.data, null);
  });
  await withApi(async () => { throw new Error("must not fetch"); }, async () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    assert.equal((await stockApi.fetchFormalStock("9001")).state, "UNAVAILABLE");
  });
});

test("history and Technical V0 consumers enforce identity, authority and backend ownership", async () => {
  const technical = {
    code: "9001", market: "TWO", requestedTo: "2026-08-28", publicationStatus: "BLOCKED",
    publicationState: "UNAVAILABLE", technicalEvidence: [], reasonCodes: ["CONTINUITY_FAIL"],
    calculationOwner: "BACKEND_ONLY", browserCalculationAllowed: "NO", provenance: null,
  };
  await withApi(async (url) => {
    const parsed = new URL(url);
    if (parsed.pathname.endsWith("/price-history")) return response({ code: "9001", market: "TWO", items: [], coverageState: "EMPTY" });
    assert.equal(parsed.searchParams.get("market"), "TWO");
    assert.equal(parsed.searchParams.get("to"), "2026-08-28");
    return response(technical);
  }, async () => {
    assert.equal((await stockApi.fetchFormalStockHistory("9001", { market: "TWO" })).data.market, "TWO");
    const result = await stockApi.fetchFormalStockTechnical("9001", { market: "TWO", sessionDate: "2026-08-28" });
    assert.equal(result.state, "UNAVAILABLE");
    assert.equal(result.data.publicationStatus, "BLOCKED");
  });
  await withApi(async () => response({ ...technical, market: "TPE" }), async () => {
    assert.equal((await stockApi.fetchFormalStockTechnical("9001", { market: "TWO", sessionDate: "2026-08-28" })).state, "ERROR");
  });
});

test("fixed Technical V0 indicator set and state mapping remain canonical", () => {
  assert.deepEqual(stockApi.FORMAL_TECHNICAL_INDICATOR_IDS, [
    "MA5", "MA10", "MA20", "MA60", "DISTANCE_TO_MA20", "RAW_CLOSE_RETURN_5D", "RAW_CLOSE_RETURN_20D",
    "VOLUME_MA5", "VOLUME_MA20", "VOLUME_RATIO_20", "RSI14", "MACD_12_26_9", "MACD_SIGNAL_12_26_9", "MACD_HISTOGRAM_12_26_9",
  ]);
  const evidence = stockApi.FORMAL_TECHNICAL_INDICATOR_IDS.map((indicatorId) => ({
    indicatorId, sessionDate: "2026-08-28", publicationState: "FORMAL", value: "1",
  }));
  const available = { publicationStatus: "AVAILABLE", requestedTo: "2026-08-28", provenance: { latestTradingDate: "2026-08-28" }, technicalEvidence: evidence };
  assert.equal(stockApi.technicalPresentationState(available), "AVAILABLE");
  assert.equal(stockApi.technicalPresentationState({ ...available, publicationStatus: "AVAILABLE_WITH_LIMITATION" }), "PARTIAL");
  assert.equal(stockApi.technicalPresentationState({ ...available, technicalEvidence: [] }), "EMPTY");
  assert.equal(stockApi.technicalPresentationState({ ...available, publicationStatus: "BLOCKED" }), "UNAVAILABLE");
});

test("shared consumer and standalone route contain no legacy trigger or browser technical path", () => {
  const drawer = readFileSync(resolve(app, "components/v2/StockEncyclopediaDrawer.tsx"), "utf8");
  const route = readFileSync(resolve(app, "stocks/[code]/page.tsx"), "utf8");
  const explorer = readFileSync(resolve(app, "components/v2/StockExplorerPage.tsx"), "utf8");
  assert.match(drawer, /fetchFormalStockTechnical/);
  assert.match(drawer, /calculationOwner/);
  assert.doesNotMatch(drawer, /above20MA|above60MA|breakoutState|technicalState/);
  assert.doesNotMatch(route, /useSnapshot|evaluateTriggerState|StockSignalLamps|screener/);
  assert.match(route, /get\("market"\)/);
  assert.match(explorer, /\$\{row\.market\}:\$\{row\.code\}/);
  assert.match(explorer, /selected\?\.market === stock\.market/);
});
