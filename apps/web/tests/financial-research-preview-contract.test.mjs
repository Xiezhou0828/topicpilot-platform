import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");
const [api, detail, cards, css] = await Promise.all([
  read("app/lib/financial-research-api.ts"),
  read("app/components/v2/StockDetailPage.tsx"),
  read("app/components/v2/StockResearchCards.tsx"),
  read("app/globals.css"),
]);

test("Company Research Preview has a read-only financial API contract", () => {
  assert.match(api, /financial-summary/);
  assert.match(api, /financial-coverage/);
  assert.match(api, /financial-statements/);
  assert.match(api, /financial-research-status/);
  assert.match(api, /source: "api" \| "unavailable"/);
  assert.match(api, /cache: "no-store"/);
  assert.match(api, /available_periods/);
});

test("Stock Detail passes financial readout into the company-first research view", () => {
  assert.match(detail, /fetchFinancialResearchReadout/);
  assert.match(detail, /financialReadout=\{financialReadout\}/);
  assert.match(cards, /FinancialApiStatusNote/);
  assert.match(cards, /financialReadout\?: FinancialResearchReadout/);
  assert.match(cards, /RealFinancialReadiness/);
  assert.match(cards, /受控 Preview/);
  assert.match(cards, /目前 Preview 尚未接入官方財報唯讀數值/);
  assert.match(css, /tp-company-research-financial-source-note/);
  assert.match(css, /tp-company-research-real-financial-readiness/);
});
