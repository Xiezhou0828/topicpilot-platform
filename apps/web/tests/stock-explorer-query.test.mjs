import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const page = await readFile(new URL("../app/components/v2/StockExplorerPage.tsx", import.meta.url), "utf8");
const client = await readFile(new URL("../app/lib/stock-api.ts", import.meta.url), "utf8");
const topicApi = await readFile(new URL("../app/lib/topic-api.ts", import.meta.url), "utf8");
const generated = await readFile(new URL("../app/lib/generated-api.d.ts", import.meta.url), "utf8");
const styles = await readFile(new URL("../app/globals.css", import.meta.url), "utf8");

test("market filter is sent to the formal backend query", () => {
  assert.match(page, /market: market === "all" \? undefined : market/);
  assert.match(client, /if \(query\.market\) params\.market = query\.market/);
});

test("topic filter uses the backend topic identifier", () => {
  assert.match(page, /topic: topic \|\| undefined/);
  assert.match(client, /if \(query\.topic\) params\.topic = query\.topic/);
  assert.match(page, /value=\{item\.slug\}/);
});

test("topic options come from the formal topic catalog, not stock relation rows", () => {
  assert.match(page, /fetchTopics/);
  assert.match(page, /const topicOptions = topicResource\?\.data \?\? \[\]/);
  assert.match(topicApi, /\/api\/v2\/topics\?limit=200&offset=0/);
  assert.equal(page.includes("baseRows.forEach((row) => row.topics"), false);
});

test("unavailable topic options stay disabled and are never hardcoded", () => {
  assert.match(page, /topicResource\?\.source === "unavailable"/);
  assert.match(page, /disabled=\{topicOptionsDisabled\}/);
  assert.match(page, /topicOptionsLoading \|\| topicOptionsUnavailable/);
  assert.equal(page.includes("<option value=\"tech\">"), false);
});

test("formal search is sent as a trimmed backend query", () => {
  assert.match(page, /search: search \|\| undefined/);
  assert.match(client, /const normalizedSearch = query\.search\?\.trim\(\)/);
  assert.match(client, /if \(normalizedSearch\) params\.search = normalizedSearch/);
  assert.match(generated, /search\?: string \| null;/);
});

test("formal search is composed with the existing filters and resets pagination", () => {
  assert.match(page, /\[market, mode, search, sort, topic\]/);
  assert.match(page, /limit: 1000,\n    offset: 0/);
  assert.match(page, /type="search"/);
  assert.equal(page.includes("displayRows = useMemo(() => baseRows.filter"), false);
});

test("search input is debounced and filtered totals are displayed", () => {
  assert.match(page, /setSearch\(searchInput\.trim\(\)\)/);
  assert.match(page, /setTimeout\(\(\) => setSearch\(searchInput\.trim\(\)\), 250\)/);
  assert.match(page, /resource\?\.source === "api" \? resource\.total : baseRows\.length/);
  assert.match(client, /total: first\.total/);
});

test("update mode maps UI labels to formal enum values", () => {
  assert.match(page, /updateMode: mode === "live" \? "INTRADAY" : mode === "eod" \? "POST_CLOSE" : undefined/);
  assert.match(client, /if \(query\.updateMode && query\.updateMode !== "all"\) params\.updateMode = query\.updateMode/);
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
  assert.match(client, /limit: "1000"/);
  assert.match(client, /offset: "0"/);
  assert.match(generated, /limit\?: number;\s+offset\?: number;/s);
});

test("filter changes reload from the first offset", () => {
  assert.match(page, /\}\), \[market, mode, search, sort, topic\]\);/);
  assert.match(page, /void loadFormal\(formalQuery\)/);
  assert.equal(page.includes("setOffset"), false);
});

test("refresh preserves the current formal query", () => {
  assert.match(page, /setInterval\(\(\) => void loadFormal\(formalQuery\), 60_000\)/);
  assert.match(page, /void loadFormal\(formalQuery\);/);
});

test("formal rendering preserves backend order", () => {
  assert.match(page, /const displayRows = useMemo/);
  assert.match(page, /formalOrder\.flatMap/);
});

test("formal topic results remain backend-owned and preserve backend order", () => {
  assert.match(page, /resource\?\.source === "api" \|\| !topic/);
  assert.match(page, /formalOrder\.flatMap/);
  assert.equal(page.includes("baseRows.forEach((row) => row.topics"), false);
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
});

test("browser business logic is not introduced for technical, chip, or strategy rules", () => {
  assert.match(page, /above20MA === true/);
  assert.equal(page.includes("institutionFlows"), true);
  assert.match(page, /favorite.*row\.favorite/);
  assert.match(page, /opportunity.*row\.opportunity/);
});

test("generated OpenAPI query types are the runtime query authority", () => {
  assert.match(client, /operations\["stocks_api_v2_stocks_get"\]/);
  assert.match(generated, /stocks_api_v2_stocks_get: \{/);
  assert.match(generated, /market\?: string \| null;/);
  assert.match(generated, /topic\?: string \| null;/);
  assert.match(generated, /updateMode\?: string \| null;/);
  assert.match(generated, /sort\?: string;/);
});
