"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AppNav } from "../components/AppNav";
import { EmptyState } from "../components/EmptyState";
import { FavoriteButton, useFavoriteCodes } from "../components/FavoriteButton";
import { LiveDataBanner } from "../components/LiveDataBanner";
import { StockSignalLamps } from "../components/StockSignalLamps";
import { useSnapshot } from "../lib/snapshot-store";
import { evaluateFilter, evaluateStockFilters, SCREENER_GROUPS } from "../lib/stock-screener.mjs";
import type { StockView } from "../lib/types";

type FilterMode = "AND" | "OR";
type QuickFilterId = "trend" | "breakout" | "institution" | "topic" | "risk";

const quickFilters: Array<{ id: QuickFilterId; label: string }> = [
  { id: "trend", label: "趨勢偏多" },
  { id: "breakout", label: "接近突破" },
  { id: "institution", label: "法人加碼" },
  { id: "topic", label: "題材強勢" },
  { id: "risk", label: "風險較低" },
];

function inputNumber(value: string) {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function displayNumber(value: number | null, digits = 2) {
  return value === null ? "資料不足" : value.toLocaleString("zh-TW", { maximumFractionDigits: digits });
}

function mainGroup(stock: StockView) {
  return stock.relations.find((item) => item.parentGroup)?.parentGroup ?? "待分類";
}

function topicLabel(stock: StockView) {
  return stock.topicNames.slice(0, 2).join("、") || stock.topicMain || "資料不足";
}

function roleLabel(stock: StockView) {
  return stock.relations.find((item) => item.role)?.role ?? stock.technicalSubtype ?? "技術角色待補";
}

function safetyLabel(stock: StockView) {
  if (stock.dataFreshness === "EXCEPTION") return "特殊狀態";
  if (stock.dataFreshness && !/CURRENT|LIVE/i.test(stock.dataFreshness)) return "資料需確認";
  return null;
}

function quickEvaluation(stock: StockView, id: QuickFilterId, strongTopics: Set<string>): boolean | null {
  if (id === "trend") {
    const structure = evaluateFilter(stock, "bullish_structure");
    return structure ?? evaluateFilter(stock, "above_ma60");
  }
  if (id === "breakout") return evaluateFilter(stock, "near_20d_high");
  if (id === "institution") return evaluateFilter(stock, "institutions_sync");
  if (id === "topic") {
    if (!stock.topicNames.length) return null;
    return stock.topicNames.some((name) => strongTopics.has(name));
  }
  const risk = stock.riskNote ?? stock.watch?.shortRisk;
  if (!stock.watch && risk === null) return null;
  return risk === null || /暫無|無明顯|低風險/.test(risk);
}

function StockIdentity({ stock }: { stock: StockView }) {
  return <span className="universeIdentity"><strong>{stock.name ?? "未提供名稱"} <small>{stock.code}</small></strong><span>{roleLabel(stock)}</span>{safetyLabel(stock) && <em>{safetyLabel(stock)}</em>}</span>;
}

export default function WatchlistPage() {
  const router = useRouter();
  const { bundle, status, refresh } = useSnapshot();
  const favorites = useFavoriteCodes();
  const sourceRows = useMemo(() => bundle.source === "snapshot" ? bundle.stockUniverse : [], [bundle.source, bundle.stockUniverse]);
  const strongTopics = useMemo(() => new Set(bundle.topics.filter((item) => item.grade === "S" || item.grade === "A" || item.childGrade === "S" || item.childGrade === "A").map((item) => item.name)), [bundle.topics]);
  const [quickSelected, setQuickSelected] = useState<QuickFilterId[]>([]);
  const [advancedSelected, setAdvancedSelected] = useState<string[]>([]);
  const [filterMode, setFilterMode] = useState<FilterMode>("AND");
  const [query, setQuery] = useState("");
  const [rsiMin, setRsiMin] = useState("");
  const [rsiMax, setRsiMax] = useState("");
  const [priceMin, setPriceMin] = useState("");
  const [priceMax, setPriceMax] = useState("");

  const ranges = useMemo(() => ({
    rsiMin: inputNumber(rsiMin), rsiMax: inputNumber(rsiMax),
    priceMin: inputNumber(priceMin), priceMax: inputNumber(priceMax),
  }), [rsiMin, rsiMax, priceMin, priceMax]);
  const advancedFilters = useMemo(() => [
    ...advancedSelected,
    ...(ranges.rsiMin !== null || ranges.rsiMax !== null ? ["rsi_range"] : []),
    ...(ranges.priceMin !== null || ranges.priceMax !== null ? ["price_range"] : []),
  ], [advancedSelected, ranges]);
  const hasConditions = quickSelected.length + advancedFilters.length > 0;

  const evaluations = useMemo(() => new Map(sourceRows.map((stock) => {
    const quickValues = quickSelected.map((id) => quickEvaluation(stock, id, strongTopics));
    const advanced = evaluateStockFilters(stock, advancedFilters, filterMode, ranges);
    const values = [...quickValues, ...(advancedFilters.length ? [advanced.matches] : [])];
    const missing = quickValues.filter((item) => item === null).length + advanced.missing;
    const matches = !values.length || (filterMode === "OR" ? values.some((item) => item === true) : values.every((item) => item === true));
    return [stock.code, { matches, missing }];
  })), [sourceRows, quickSelected, strongTopics, advancedFilters, filterMode, ranges]);

  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return sourceRows.filter((stock) => {
      const keywordMatch = !keyword || `${stock.code} ${stock.name ?? ""} ${mainGroup(stock)} ${topicLabel(stock)} ${roleLabel(stock)}`.toLowerCase().includes(keyword);
      return keywordMatch && (evaluations.get(stock.code)?.matches ?? false);
    });
  }, [sourceRows, query, evaluations]);

  const allConditionDataMissing = hasConditions && sourceRows.length > 0 && [...evaluations.values()].every((item) => item.missing > 0);
  const snapshotUnavailable = bundle.source !== "snapshot" || status.state === "error" || status.dataState === "UNAVAILABLE";
  const volumeLabel = bundle.qualityPanelData.freshness.marketSession === "OPEN" ? "成交量（盤中累計）" : "成交量（當日）";

  function openStock(code: string) { router.push(`/stocks/${code}`); }
  function rowKey(event: React.KeyboardEvent, code: string) {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openStock(code); }
  }
  function toggleQuick(id: QuickFilterId) { setQuickSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]); }
  function toggleAdvanced(id: string) { setAdvancedSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]); }
  function clearFilters() { setQuickSelected([]); setAdvancedSelected([]); setRsiMin(""); setRsiMax(""); setPriceMin(""); setPriceMax(""); setQuery(""); }

  const emptyState = bundle.source !== "snapshot" || status.state === "error"
    ? { title: "股票資料尚未載入", description: "目前無法取得正式 snapshot，列表不會用示範資料或前端推算補值。", retry: true }
    : sourceRows.length === 0
      ? { title: "正式股票數為 0", description: "snapshot 已載入，但目前沒有可供股票一覽顯示的正式股票。", retry: true }
      : allConditionDataMissing
        ? { title: "所選條件缺少必要資料", description: "目前股票資料不足以判斷這組條件；缺資料不會被視為符合。", retry: false }
        : { title: "有資料，但沒有符合條件的股票", description: "可以清除部分條件或改用其他快速篩選。", retry: false };

  return (
    <main><AppNav /><div className="appShell stockUniverseShell">
      <header className="topbar"><div><p className="eyebrow">Stock universe</p><h1>股票一覽</h1></div><div className="topActions"><span>{bundle.qualityPanelData.freshness.dataDate ?? "資料日期不足"} · {sourceRows.length} 檔</span><strong>{favorites.length} 檔自選</strong></div></header>
      <LiveDataBanner />

      <section className="panel universeFilters">
        <div className="sectionHead compact"><div><p className="eyebrow">Quick filters</p><h2>快速篩選</h2></div><span>只縮小顯示範圍，不改變系統目前排序</span></div>
        <div className="quickFilterRow" aria-label="快速篩選">{quickFilters.map((filter) => <button aria-pressed={quickSelected.includes(filter.id)} className={quickSelected.includes(filter.id) ? "active" : ""} key={filter.id} onClick={() => toggleQuick(filter.id)} type="button">{filter.label}</button>)}</div>
        <div className="universeSearchRow"><label><span>搜尋股票或題材</span><input onChange={(event) => setQuery(event.target.value)} placeholder="股號、名稱、大族群、題材" type="search" value={query} /></label><div className="modeControl" aria-label="條件組合"><button className={filterMode === "AND" ? "active" : ""} onClick={() => setFilterMode("AND")} type="button">全部符合</button><button className={filterMode === "OR" ? "active" : ""} onClick={() => setFilterMode("OR")} type="button">任一符合</button></div>{(hasConditions || query) && <button className="clearFilters" onClick={clearFilters} type="button">清除條件</button>}</div>
        <details className="advancedFilterDisclosure"><summary>進階篩選 <span>MA、RS、MACD、KD、RSI、量價、法人</span></summary><div className="advancedFilterBody">{SCREENER_GROUPS.map((group) => <fieldset key={group.id}><legend>{group.label}</legend><div>{group.filters.map(([id, label]) => <label key={id}><input checked={advancedSelected.includes(id)} onChange={() => toggleAdvanced(id)} type="checkbox" />{label}</label>)}</div></fieldset>)}<fieldset><legend>數值區間</legend><div className="rangeInputs"><label>RSI 最低<input inputMode="decimal" onChange={(event) => setRsiMin(event.target.value)} value={rsiMin} /></label><label>RSI 最高<input inputMode="decimal" onChange={(event) => setRsiMax(event.target.value)} value={rsiMax} /></label><label>股價最低<input inputMode="decimal" onChange={(event) => setPriceMin(event.target.value)} value={priceMin} /></label><label>股價最高<input inputMode="decimal" onChange={(event) => setPriceMax(event.target.value)} value={priceMax} /></label></div></fieldset></div></details>
      </section>

      <section className="panel universeResults">
        <div className="sectionHead compact"><div><p className="eyebrow">Results</p><h2>市場股票</h2></div><span>{filtered.length} / {sourceRows.length} 檔 · 點選查看完整判讀</span></div>
        {snapshotUnavailable ? <EmptyState title={emptyState.title} description={emptyState.description} onRetry={() => refresh("manual")} actions={[{ href: "/guide", label: "查看使用指南" }]} /> : filtered.length ? <>
          <div className="universeTableWrap"><table className="stockUniverseTable"><thead><tr><th>自選</th><th>個股</th><th>主大族群</th><th>題材</th><th>現價</th><th>漲跌%</th><th>{volumeLabel}</th><th>燈號</th></tr></thead><tbody>{filtered.map((stock) => <tr className="universeRow" key={stock.code} onClick={() => openStock(stock.code)} onKeyDown={(event) => rowKey(event, stock.code)} role="link" tabIndex={0}><td onClick={(event) => event.stopPropagation()} onKeyDown={(event) => event.stopPropagation()}><FavoriteButton code={stock.code} /></td><td><StockIdentity stock={stock} /></td><td>{mainGroup(stock)}</td><td>{topicLabel(stock)}</td><td className="numCell">{displayNumber(stock.price)}</td><td className={`numCell ${stock.change === null ? "flat" : stock.change > 0 ? "up" : stock.change < 0 ? "down" : "flat"}`}>{stock.change === null ? "資料不足" : `${stock.change > 0 ? "+" : ""}${stock.change.toFixed(2)}%`}</td><td className="numCell">{stock.volume === null ? "資料不足" : `${displayNumber(stock.volume, 0)} 張`}</td><td><StockSignalLamps stock={stock} /></td></tr>)}</tbody></table></div>
          <div className="universeMobileCards">{filtered.map((stock) => <article className="universeMobileCard" key={stock.code} onClick={() => openStock(stock.code)} onKeyDown={(event) => rowKey(event, stock.code)} role="link" tabIndex={0}><header><StockIdentity stock={stock} /><span onClick={(event) => event.stopPropagation()} onKeyDown={(event) => event.stopPropagation()}><FavoriteButton code={stock.code} /></span></header><div className="mobileTopicLine"><span>{mainGroup(stock)}</span><strong>{topicLabel(stock)}</strong></div><dl><div><dt>現價</dt><dd>{displayNumber(stock.price)}</dd></div><div><dt>漲跌%</dt><dd className={stock.change === null ? "flat" : stock.change > 0 ? "up" : stock.change < 0 ? "down" : "flat"}>{stock.change === null ? "資料不足" : `${stock.change > 0 ? "+" : ""}${stock.change.toFixed(2)}%`}</dd></div><div><dt>{volumeLabel}</dt><dd>{stock.volume === null ? "資料不足" : `${displayNumber(stock.volume, 0)} 張`}</dd></div></dl><StockSignalLamps stock={stock} /></article>)}</div>
        </> : <EmptyState title={emptyState.title} description={emptyState.description} onRetry={emptyState.retry ? () => refresh("manual") : clearFilters} retryLabel={emptyState.retry ? "重新載入" : "清除篩選"} actions={[{ href: "/guide", label: "查看使用指南" }]} />}
      </section>
    </div></main>
  );
}
