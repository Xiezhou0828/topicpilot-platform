import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { selectStockQuote } from "../app/lib/stock-eod-presenter.mjs";

const [explorer, drawer, presenter, css, generated] = await Promise.all([
  readFile(new URL("../app/components/v2/StockExplorerPage.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/components/v2/StockEncyclopediaDrawer.tsx", import.meta.url), "utf8"),
  readFile(new URL("../app/lib/stock-eod-presenter.mjs", import.meta.url), "utf8"),
  readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  readFile(new URL("../app/lib/generated-api.d.ts", import.meta.url), "utf8"),
]);

const eod = {
  adjustmentState: "UNADJUSTED",
  change: -1.25,
  changePct: -1.23,
  close: 98.75,
  dataStatus: "PARTIAL",
  high: 101,
  low: 97,
  observedAt: "2026-08-14T06:30:00Z",
  open: 100,
  previousClose: 100,
  priceSource: { sourceCode: "TWSE_DAILY", adapterVersion: "a", mappingPolicyVersion: "m", normalizationContractVersion: "n", observationSemantics: "daily", qualityState: "accepted", referenceDataVersion: "r", observedAt: null, retrievedAt: null },
  retrievedAt: "2026-08-14T06:31:00Z",
  tradingDate: "2026-08-14",
  turnover: null,
  volume: 123456,
  volumeSource: null,
};

test("formal EOD quote uses backend EOD fields and preserves null turnover", () => {
  assert.deepEqual(selectStockQuote({
    price: 101.5,
    changePct: null,
    volume: 999,
    updateMode: "POST_CLOSE",
    eod,
  }), {
    source: "EOD_SOURCE",
    price: 98.75,
    change: -1.25,
    changePct: -1.23,
    volume: 123456,
    dataStatus: "PARTIAL",
  });
});

test("intraday quote stays separate from completed-session EOD", () => {
  assert.deepEqual(selectStockQuote({
    price: 102.25,
    changePct: 0.5,
    volume: 88,
    updateMode: "INTRADAY",
    eod,
  }), {
    source: "INTRADAY_SOURCE",
    price: 102.25,
    change: null,
    changePct: 0.5,
    volume: 88,
    dataStatus: "UNAVAILABLE",
  });
});

test("formal eod=null fails closed instead of falling back to top-level or Preview values", () => {
  assert.deepEqual(selectStockQuote({
    price: 102.25,
    changePct: 0.5,
    volume: 88,
    updateMode: "POST_CLOSE",
    eod: null,
  }), {
    source: "UNAVAILABLE",
    price: null,
    change: null,
    changePct: null,
    volume: null,
    dataStatus: "UNAVAILABLE",
  });
});

test("formal API errors stay unavailable instead of silently switching to Preview", () => {
  assert.match(explorer, /resource\.source === "unavailable"/);
  assert.match(explorer, /<EmptyState title=\{UI\.unavailable\}/);
  assert.match(drawer, /detailState === "unavailable"/);
  assert.doesNotMatch(drawer, /detailState === "unavailable"[^}]*fromPreview/);
});

test("Preview is explicit and never presented as formal EOD", () => {
  const result = selectStockQuote({
    isPreview: true,
    price: 12,
    changePct: 1.2,
    volume: 10,
    updateMode: "POST_CLOSE",
    eod: null,
  });
  assert.equal(result.source, "PREVIEW");
  assert.equal(result.dataStatus, "PREVIEW");
});

test("EOD status and lineage fields are wired into the Drawer", () => {
  for (const status of ["AVAILABLE", "PARTIAL", "UNAVAILABLE", "NO_TRADE", "SUSPENDED", "ADJUSTMENT_UNKNOWN", "SOURCE_CONFLICT"]) {
    assert.match(drawer, new RegExp(status));
  }
  for (const field of ["tradingDate", "previousClose", "change", "changePct", "volume", "turnover", "priceSource", "volumeSource", "observedAt", "retrievedAt"]) {
    assert.match(drawer, new RegExp(`eod\\.${field}`));
  }
  assert.match(explorer, /eod: item\.eod/);
  assert.match(explorer, /selectStockQuote\(stock\)/);
  assert.match(generated, /StockEodRead:/);
});

test("browser remains render-only for EOD business semantics", () => {
  assert.doesNotMatch(`${explorer}\n${drawer}\n${presenter}`, /eod\.(?:close|change|changePct|previousClose)\s*[-+*/]/);
  assert.doesNotMatch(`${explorer}\n${drawer}\n${presenter}`, /(?:close|price)\s*\*\s*(?:volume|turnover)|turnover\s*=.*(?:price|close)/i);
  assert.doesNotMatch(`${explorer}\n${drawer}\n${presenter}`, /setDate|subtract|setUTCDate|previous.*calendar|new Date\([^)]*trading/i);
});

test("existing Drawer interaction and advanced topic filter remain protected", () => {
  for (const marker of ["presentation=\"push\"", "isClosing", "Escape", "data-detail-state", "topic", "setTopic", "topics.map"]) {
    assert.match(explorer, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  assert.match(css, /tp-stock-encyclopedia-drawer--push[^\n]*position:sticky/);
  assert.match(css, /tp-stock-encyclopedia-drawer--push[^\n]*height:calc\(100vh - 72px\)/);
  assert.match(css, /tp-stock-encyclopedia-drawer--push[^\n]*overflow:hidden/);
  assert.match(css, /tp-stock-encyclopedia-drawer--push\.is-closing/);
});
