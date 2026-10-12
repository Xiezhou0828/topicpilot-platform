import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");
const [cards, detail, adapter, fixture1303, fixture1314, fixture1319, css] = await Promise.all([
  read("app/components/v2/StockResearchCards.tsx"),
  read("app/components/v2/StockDetailPage.tsx"),
  read("app/lib/stock-research-preview.ts"),
  read("app/data/research-v2/1303.json"),
  read("app/data/research-v2/1314.json"),
  read("app/data/research-v2/1319.json"),
  read("app/globals.css"),
]);

test("Company Research renders six V2-driven sections with desktop hierarchy", () => {
  for (const marker of ["公司研究概況", "產品與營收結構", "產業鏈與競爭位置", "成長驅動與主要風險", "財報與法說會補充", "研究來源與資料限制"]) {
    assert.match(cards, new RegExp(marker));
  }
  for (const marker of ["getResearchGroup", "RevenueDonut", "group.investments", "growthFactors", "riskFactors", "group.metrics", "managementTopics", "getOfficialSources", "fullResearch"]) {
    assert.match(cards, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  assert.match(detail, /StockResearchCards companyName=\{identityName\} research=\{researchBundle\}/);
  assert.match(css, /tp-company-research-business-layout/);
  assert.match(css, /tp-company-research-growth-risk-grid/);
  for (const marker of ["tp-company-research-financial-highlights", "tp-company-research-financial-table", "tp-company-research-other-limitations", "@media(max-width:1100px)"]) {
    assert.match(css, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
});

test("Preview adapter loads the actual 1303, 1314 and 1319 Research V2 JSON", () => {
  assert.match(adapter, /research-v2\/1303\.json/);
  assert.match(adapter, /research-v2\/1314\.json/);
  assert.match(adapter, /research-v2\/1319\.json/);
  assert.match(adapter, /CompanyResearchViewV2/);
  assert.match(fixture1303, /"schemaVersion": "company-research-view\.v2"/);
  assert.match(fixture1314, /"schemaVersion": "company-research-view\.v2"/);
  assert.match(fixture1319, /"schemaVersion": "company-research-view\.v2"/);
  assert.match(fixture1319, /"nameZh": "東陽"/);
  assert.match(fixture1319, /"formalTopicMutation": "NO"/);
  assert.match(fixture1314, /investment-china-engineering/);
  assert.match(fixture1314, /metric-equity-method-loss-zhonghua-engineering-h1-2026/);
  assert.match(fixture1303, /多事業群綜合材料製造商/);
  assert.match(fixture1314, /核心業務涵蓋 AN/);
  assert.match(fixture1303, /公司獲利時，需把各事業群本業表現/);
  assert.match(fixture1314, /不能把尚未揭露的專案收入視為已實現獲利/);
});

test("Research V2 resolves only confirmed listed competitors into navigable stock links", () => {
  assert.match(cards, /CompetitorLinks/);
  assert.match(cards, /resolveCompetitor/);
  assert.match(cards, /href=\{`\/stocks\/\$\{competitor\.stockId\}`\}/);
  assert.match(cards, /is-unresolved/);
  assert.doesNotMatch(cards, /<TagList items=\{chain\.competitors\}/);
  for (const marker of [
    '"1802"',
    '"1815"',
    '"6213"',
    '"6274"',
    '"1326"',
    '"6505"',
    "股票主檔無法唯一確認代號",
  ]) {
    assert.ok((adapter + cards).includes(marker), `missing competitor marker: ${marker}`);
  }
});

test("V2.2 keeps positioning readable and financial values high contrast", () => {
  for (const marker of [
    ".tp-company-research-overview-layout{grid-template-columns:1fr",
    ".tp-company-research-overview-facts{grid-template-columns:repeat(4",
    ".tp-company-research-competitor-link",
    ".tp-company-research-financial-table td strong{color:#292524",
  ]) {
    assert.ok(css.includes(marker), `missing V2.2 CSS marker: ${marker}`);
  }
});

test("Research UI does not expose internal evidence identifiers or infer formal topics", () => {
  assert.doesNotMatch(cards, /sourceEvidenceIds/);
  assert.doesNotMatch(cards, /formalTopic/);
  assert.match(cards, /研究內容目前為 Preview 審閱版/);
  assert.match(cards, /publicationStatus.*PUBLISHED/);
  assert.match(css, /tp-company-research-publication-note/);
  assert.match(cards, /前端保留官方網站或交易所官方入口/);
  assert.match(adapter, /source\.tier === "P2"/);
  assert.match(adapter, /FIXTURE\|INTERNAL\|TEST\|MAPPING/);
  assert.match(adapter, /fixture\|test/);
});

test("Research interactions retain all factors and degrade missing data safely", () => {
  for (const marker of ["<details", "主要產品與事業群", "上游", "中游", "下游", "競爭優勢", "競爭限制", "查看詳情", "關閉轉投資詳情", "尚未提供"]) {
    assert.match(cards, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  for (const marker of ["tp-company-research-business-tabs", "tp-company-research-period-select", "查看全部", "statusLabel", "有依據的觀察對象"]) {
    assert.doesNotMatch(cards, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  assert.match(cards, /tp-company-research-revenue-total/);
  assert.match(cards, /營收結構/);
  assert.match(cards, /FinancialSection/);
  assert.match(cards, /FinancialHighlights/);
  assert.match(cards, /FinancialComparison/);
  assert.match(cards, /SpecialMetrics/);
  assert.match(cards, /顯示其他限制/);
  assert.match(cards, /formatAmount\(dataset\.total, dataset\.unit, dataset\.currency\)/);
  assert.match(cards, /formatMetricValue\(metric\)/);
  for (const marker of ["overflow-wrap:anywhere", "@media(max-width:1180px)", "@media(max-width:680px)", "tp-company-research-factor-card"]) {
    assert.match(css, new RegExp(marker.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
});
