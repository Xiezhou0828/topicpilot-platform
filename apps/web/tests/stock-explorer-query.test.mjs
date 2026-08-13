import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const page = await readFile(new URL("../app/components/v2/StockExplorerPage.tsx", import.meta.url), "utf8");
const client = await readFile(new URL("../app/lib/stock-api.ts", import.meta.url), "utf8");
const generated = await readFile(new URL("../app/lib/generated-api.d.ts", import.meta.url), "utf8");
const styles = await readFile(new URL("../app/globals.css", import.meta.url), "utf8");

test("market filter is sent to the formal backend query", () => {
  assert.match(page, /market: market === "all" \? undefined : market/);
  assert.match(client, /if \(query\.market\) params\.market = query\.market/);
});

test("topic filter uses the backend topic identifier", () => {
  assert.match(page, /topic: topic \|\| undefined/);
  assert.match(client, /if \(query\.topic\) params\.topic = query\.topic/);
  assert.match(page, /value=\{slug\}/);
});

test("update mode maps UI labels to formal enum values", () => {
  assert.match(page, /updateMode: mode === "live" \? "INTRADAY" : mode === "eod" \? "POST_CLOSE" : undefined/);
  assert.match(client, /if \(query\.updateMode\) params\.updateMode = query\.updateMode/);
  assert.match(generated, /updateMode\?: string \| null/);
});

test("sort is mapped to the existing backend sort contract", () => {
  assert.match(page, /sort: apiSort\(sort\)/);
  assert.match(client, /sort: query\.sort \?\? "symbolAsc"/);
});

test("all/default state omits optional backend filters", () => {
  assert.match(page, /market === "all" \? undefined/);
  assert.match(page, /topic \|\| undefined/);
  assert.match(page, /: undefined,\n    sort:/);
});

test("formal query includes the existing limit and offset pagination", () => {
  assert.match(page, /limit: 1000,\n    offset: 0/);
  assert.match(client, /limit: String\(pageLimit\)/);
  assert.match(client, /offset: String\(initialOffset\)/);
  assert.match(generated, /limit\?: number;\s+offset\?: number;/s);
});

test("filter changes reload from the first offset", () => {
  assert.match(page, /\}\), \[market, mode, sort, topic\]\);/);
  assert.match(page, /void loadFormal\(formalQuery\)/);
  assert.equal(page.includes("setOffset"), false);
});

test("refresh preserves the current formal query", () => {
  assert.match(page, /setInterval\(\(\) => void loadFormal\(formalQuery\), 60_000\)/);
  assert.match(page, /void loadFormal\(formalQuery\);/);
});

test("formal rendering preserves backend order", () => {
  assert.match(page, /if \(resource\?\.source === "api"\) return baseRows;/);
  assert.equal(page.includes("formalOrder"), false);
});

test("formal results are not browser-sorted or browser-filtered", () => {
  assert.equal(page.includes("filteredRows"), false);
  assert.equal(page.includes("formalOrder"), false);
  assert.equal(page.includes("baseRows.filter"), false);
  assert.match(page, /return \[\.\.\.baseRows\]\.sort\(\(a, b\) => compareRows\(a, b, sort\)\);/);
  assert.match(page, /if \(resource\?\.source === "api"\) return baseRows;/);
});

test("configured API failures remain unavailable", () => {
  assert.match(client, /return unavailable\(error instanceof Error \? error\.message/);
  assert.match(page, /if \(resource\?\.source === "unavailable"\) return \[\];/);
  assert.match(page, /resource\.source === "unavailable" \? <Card>/);
});

test("API failure never silently falls back to Preview", () => {
  assert.match(page, /if \(resource\?\.source === "unavailable"\) return \[\];/);
  assert.match(page, /return bundle\.source === "snapshot" \? bundle\.stockUniverse\.map\(fromPreview\) : \[\];/);
});

test("Preview is explicit and only selected without a formal origin", () => {
  assert.match(client, /if \(!base\) \{/);
  assert.match(client, /source: "synthetic-snapshot"/);
  assert.match(page, /const isPreview = resource\?\.source !== "api"/);
});

test("nullable formal market values are rendered without fabrication", () => {
  assert.match(page, /function formatPrice\(value: number \| null\): string \{/);
  assert.match(page, /return value === null \? "—"/);
  assert.match(page, /price: item\.price,\n    changePct: item\.changePct,\n    volume: item\.volume/);
});

test("topic relation display remains presentation-only", () => {
  assert.match(page, /topics: \(item\.topicRelations \?\? \[\]\)\.map/);
  assert.match(page, /stock\.topics\[0\]\?\.name/);
  assert.equal(page.includes("mainTopic: item.topicRelations"), false);
});

test("canonical main-topic authority is not inferred in the Explorer", () => {
  assert.match(page, /mainTopic: mainTopic\(item\.mainTopic\)/);
  assert.equal(page.includes("mainTopic: item.topicRelations[0]"), false);
});

test("Drawer switching and close animation remain wired", () => {
  assert.match(page, /setSelected\(stock\);/);
  assert.match(page, /presentation="push"/);
  assert.match(page, /isClosing=\{detailPanelState === "closing"\}/);
  assert.match(page, /\}, 280\);/);
});

test("Drawer sticky and full-height behavior remains unchanged", () => {
  assert.match(styles, /\.tp-stock-encyclopedia-drawer--push\{position:sticky!important;top:72px!important;/);
  assert.match(styles, /height:calc\(100vh - 72px\)/);
  assert.match(styles, /\.tp-stock-encyclopedia-drawer--push \.tp-stock-encyclopedia-body[^{]*\{[^}]*overflow-y:auto/s);
});

test("unsupported advanced controls are visibly unavailable", () => {
  assert.match(page, /UI\.technical}.*disabled/);
  assert.match(page, /UI\.chip}.*disabled/);
  assert.match(page, /UI\.strategy}.*disabled/);
  assert.equal(page.includes("evaluateStockFilters"), false);
  assert.equal(page.includes("technicalMatch"), false);
  assert.equal(page.includes("chipMatch"), false);
  assert.equal(page.includes("strategyMatch"), false);
});

test("browser business logic is not introduced for technical, chip, or strategy rules", () => {
  assert.equal(page.includes("above20MA === true"), false);
  assert.equal(page.includes("institutionFlows"), true);
  assert.equal(page.includes("favoriteCodes"), false);
  assert.equal(page.includes("opportunity !== null"), false);
});

test("generated OpenAPI query types are the runtime query authority", () => {
  assert.match(client, /operations\["stocks_api_v2_stocks_get"\]/);
  assert.match(generated, /stocks_api_v2_stocks_get: \{/);
  assert.match(generated, /market\?: string \| null;/);
  assert.match(generated, /topic\?: string \| null;/);
  assert.match(generated, /updateMode\?: string \| null;/);
  assert.match(generated, /sort\?: string;/);
});
