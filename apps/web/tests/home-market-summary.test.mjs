import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const app = new URL("../app/", import.meta.url);
const read = (path) => readFile(new URL(path, app), "utf8");

test("home consumes backend market decision in one focused market judgement", async () => {
  const home = await read("page.tsx");
  for (const text of ["今日市場焦點", "今日市場判斷", "市場狀態", "今日操作方式", "主要風險", "市場健康度", "marketDecision", "market-overview"]) assert.match(home, new RegExp(text));
  assert.match(home, /decision\?\.state\.label/);
  assert.match(home, /decision\?\.observationMode\.label/);
  assert.match(home, /decision\?\.risks\[0\]\?\.detail/);
  assert.doesNotMatch(home, /marketState.*price|marketState.*marketIndices/);
});

test("home displays four canonical health metrics without recomputing values", async () => {
  const home = await read("page.tsx");
  for (const text of ["BREADTH_ADVANCE", "ABOVE_MA60", "RS20_POSITIVE", "MACD_POSITIVE", "上漲股票占比", "站上季線比例", "近 20 日強於大盤", "MACD 偏多比例", "aria-label"]) assert.match(home, new RegExp(text));
  assert.match(home, /healthMetrics/);
  assert.match(home, /evidencePct\(evidence\)/);
  assert.match(home, /evidenceRatio\(evidence\)/);
  assert.doesNotMatch(home, /evidence\.count\s*\/\s*evidence\.denominator/);
});

test("home shows backend-limited strongest, warming, and cooling topics with existing links", async () => {
  const home = await read("page.tsx");
  for (const text of ["題材輪動", "目前最強", "正在升溫", "正在降溫", "topWarming", "topCooling"]) assert.match(home, new RegExp(text));
  assert.match(home, /decision\?\.topicRotationSummary\.topWarming/);
  assert.match(home, /decision\?\.topicRotationSummary\.topCooling/);
  assert.match(home, /\/topics\?topic=/);
  assert.doesNotMatch(home, /topicChange.*sort|topWarming\.slice|topCooling\.slice/);
});

test("market radar navigation is removed and the old route redirects to the home anchor", async () => {
  const [nav, redirect] = await Promise.all([read("components/AppNav.tsx"), read("market/page.tsx")]);
  assert.doesNotMatch(nav, /label: "市場雷達"/);
  assert.match(redirect, /redirect\("\/#market-overview"\)/);
});

test("home copy has plain-language missing and freshness states", async () => {
  const home = await read("page.tsx");
  for (const text of ["資料延遲，以下為", "行情更新至", "正在更新市場摘要，完成前不提供替代判斷。", "目前無法提供市場結論"] ) assert.match(home, new RegExp(text));
  for (const text of ["盤中", "已收盤", "休市", "資料尚未更新", "資料延遲"]) assert.match(home, new RegExp(text));
  assert.match(home, /taiwanDate\(undefined\)/);
  for (const term of ["marketRadar", "snapshot 尚未提供市場雷達契約", "前端不會重算", "schema", "scope"]) assert.doesNotMatch(home, new RegExp(term));
});

test("market decision adapter and bundle wiring are explicit", async () => {
  const [types, adapter, source] = await Promise.all([read("lib/types.ts"), read("lib/snapshot-adapter.ts"), read("lib/data-source.ts")]);
  assert.match(types, /RawMarketDecision/);
  assert.match(types, /MarketDecisionView/);
  assert.match(adapter, /export function toMarketDecision/);
  assert.match(source, /marketDecision: toMarketDecision\(raw\)/);
});

test("home focus CSS is responsive", async () => {
  const css = await read("globals.css");
  for (const selector of [".marketJudgement", ".marketEvidenceGrid", ".topicRotationGrid", ".strategyLabels", "@media (max-width: 820px)"]) assert.match(css, new RegExp(selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
});

test("strategy candidate drilldown uses only canonical registry, candidates, and performance", async () => {
  const [home, types, adapter, source] = await Promise.all([read("page.tsx"), read("lib/types.ts"), read("lib/snapshot-adapter.ts"), read("lib/data-source.ts")]);
  for (const text of ["strategyRegistry.strategies", "COMPLETE_EMPTY", "今日無符合標的", "此策略未提供進場價位", "樣本累積中", "strategyKey"]) assert.match(home, new RegExp(text));
  assert.match(home, /useSearchParams/);
  assert.match(home, /strategyId === selectedStrategy\.strategyId/);
  assert.doesNotMatch(home, /strategyCandidates.*sort/);
  for (const text of ["RawStrategyRegistryItem", "RawStrategyCandidate", "RawStrategyPerformance", "StrategyRegistryView", "StrategyCandidateView", "StrategyPerformanceView"]) assert.match(types, new RegExp(text));
  for (const text of ["toStrategyRegistry", "toStrategyCandidates", "toStrategyPerformance"]) assert.match(adapter, new RegExp(text));
  for (const text of ["strategyRegistry: toStrategyRegistry\\(raw\\)", "strategyCandidates: toStrategyCandidates\\(raw\\)", "strategyPerformance: toStrategyPerformance\\(raw\\)"]) assert.match(source, new RegExp(text));
});

test("strategy logic copy is fixed by strategyId and never inferred from candidates", async () => {
  const home = await read("page.tsx");
  const approved = {
    trend_continuation: "趨勢與動能同時偏強的股票，在當日完整排名中取前 10% 作為候選。",
    breakout_volume: "股價位階接近或確認突破，且成交量與價格表現支持突破的股票。",
    pullback_timing: "尋找既有趨勢中的回檔時點，搭配擺盪位置與回檔量縮條件。",
    topic_chip: "題材強度與籌碼資料同步符合條件；任一必要資料不足時不補假值。",
    risk_first: "先用風險與可執行性條件篩選，再在符合者中排序；不把風險分數當作報酬預測。",
    current_composite: "沿用既有 Trading／Entry／Daily 的正式規則，顯示今日交易觀察結果。",
  };
  for (const [strategyId, copy] of Object.entries(approved)) {
    assert.match(home, new RegExp(strategyId));
    assert.match(home, new RegExp(copy.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  assert.match(home, /前 10% 指當日可分析股票的完整排名前 10%/);
  assert.doesNotMatch(home, /勝率|保證報酬|買進建議/);
});

test("public index view keeps market environment but never exposes MA20 slope copy", async () => {
  const [home, adapter] = await Promise.all([read("page.tsx"), read("lib/snapshot-adapter.ts")]);
  assert.match(adapter, /const sub = env/);
  assert.doesNotMatch(adapter, /const sub[\s\S]{0,160}MA20斜率/);
  assert.doesNotMatch(home, /MA20斜率/);
});
