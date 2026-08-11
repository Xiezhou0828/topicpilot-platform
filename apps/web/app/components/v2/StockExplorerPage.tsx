"use client";

import { useEffect, useMemo, useState } from "react";
import { AppShell, Card, DataState, EmptyState, Freshness, PageContainer } from "./V2Foundation";
import { StockEncyclopediaDrawer, type StockDrawerItem } from "./StockEncyclopediaDrawer";
import { fetchFormalStocks, type StockApiItem, type StockApiResource } from "../../lib/stock-api";
import { useSnapshot } from "../../lib/snapshot-store";
import type { StockView } from "../../lib/types";

type SortKey = "change" | "price" | "volume";
type ExplorerRow = {
  code: string;
  name: string;
  market: string;
  price: number | null;
  changePct: number | null;
  volume: number | null;
  dataFreshness: string | null;
  updateMode: string;
  observedAt: string | null;
  dataDate: string | null;
  updatedAt: string | null;
  topics: Array<{ slug: string; name: string; role: string | null }>;
  mainTopic: StockDrawerItem["mainTopic"];
  isPreview: boolean;
};

const price = (value: number | null) => value === null ? "—" : value.toLocaleString("zh-TW", { maximumFractionDigits: 2 });
const change = (value: number | null) => value === null ? "—" : `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
const isLive = (row: ExplorerRow) => row.updateMode === "INTRADAY" || /CURRENT|LIVE|INTRADAY/i.test(row.dataFreshness ?? "");

function fromFormal(item: StockApiItem): ExplorerRow {
  return {
    code: item.code,
    name: item.name ?? "未提供名稱",
    market: item.market,
    price: item.price,
    changePct: item.changePct,
    volume: item.volume,
    dataFreshness: item.dataFreshness,
    updateMode: item.updateMode,
    observedAt: item.observedAt,
    dataDate: item.historyCoverage.asOfDate as string | null ?? null,
    updatedAt: item.retrievedAt,
    topics: item.topicRelations.map((relation) => ({ slug: relation.topicSlug, name: relation.topicName, role: relation.topicRole })),
    mainTopic: item.mainTopic,
    isPreview: false,
  };
}

function fromPreview(item: StockView): ExplorerRow {
  return {
    code: item.code,
    name: item.name ?? "未提供名稱",
    market: "DEMO",
    price: item.price,
    changePct: item.change,
    volume: item.volume,
    dataFreshness: item.dataFreshness,
    updateMode: isLive({ ...item, updateMode: "", changePct: item.change, market: "DEMO", name: item.name ?? "", topics: [], mainTopic: null, dataDate: item.dataDate, observedAt: null, updatedAt: item.updatedAt, isPreview: true }) ? "INTRADAY" : "POST_CLOSE",
    observedAt: null,
    dataDate: item.dataDate,
    updatedAt: item.updatedAt,
    topics: item.relations.map((relation) => ({ slug: relation.topic, name: relation.topic, role: relation.role })),
    mainTopic: item.topicMain ? { name: item.topicMain, grade: null, state: null } : null,
    isPreview: true,
  };
}

export default function StockExplorerPage() {
  const { bundle } = useSnapshot();
  const [resource, setResource] = useState<StockApiResource | null>(null);
  const [market, setMarket] = useState("all");
  const [sort, setSort] = useState<SortKey>("change");
  const [mode, setMode] = useState("all");
  const [topic, setTopic] = useState("");
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [selected, setSelected] = useState<ExplorerRow | null>(null);
  const [lastSorted, setLastSorted] = useState(() => new Date());

  useEffect(() => {
    let active = true;
    const apiSort = sort === "price" ? "priceDesc" : sort === "volume" ? "volumeDesc" : "changePctDesc";
    fetchFormalStocks({ sort: apiSort }).then((next) => { if (active) setResource(next); });
    return () => { active = false; };
  }, [sort]);

  const baseRows = useMemo(() => {
    if (resource?.source === "api") return (resource.data ?? []).map(fromFormal);
    if (resource?.source === "unavailable") return [];
    return bundle.source === "snapshot" ? bundle.stockUniverse.map(fromPreview) : [];
  }, [bundle.source, bundle.stockUniverse, resource]);

  const topics = useMemo(() => {
    const values = new Map<string, string>();
    baseRows.forEach((row) => row.topics.forEach((item) => values.set(item.slug, item.name)));
    return [...values.entries()].sort((a, b) => a[1].localeCompare(b[1], "zh-Hant"));
  }, [baseRows]);

  const rows = useMemo(() => baseRows.filter((row) => (
    (market === "all" || row.market === market)
    && (mode === "all" || (mode === "live" ? row.updateMode === "INTRADAY" : row.updateMode === "POST_CLOSE"))
    && (!topic || row.topics.some((item) => item.slug === topic))
  )), [baseRows, market, mode, topic]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => { if (event.key === "Escape" && selected) setSelected(null); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [selected]);

  const drawerItem = (stock: ExplorerRow): StockDrawerItem => ({
    code: stock.code,
    name: stock.name,
    price: stock.price,
    changePct: stock.changePct,
    dataFreshness: stock.dataFreshness,
    updatedAt: stock.updatedAt,
    dataDate: stock.dataDate,
    isPreview: stock.isPreview,
    topics: stock.topics.map((item) => ({ name: item.name, role: item.role })),
    mainTopic: stock.mainTopic,
  });

  const dataState = resource === null ? "STALE" : resource.source === "api" ? "AVAILABLE" : resource.source === "unavailable" ? "UNAVAILABLE" : "STALE";
  const displayRows = resource?.source === "unavailable" ? [] : rows;
  const totalLabel = resource?.source === "api" ? resource.universe.total ?? displayRows.length : displayRows.length;

  return <AppShell currentPath="/stocks">
    <PageContainer eyebrow="股票資料庫" title="股票" description="市場圖鑑：瀏覽完整股票資料庫，從市場身份開始理解個股。">
      <div className="tp-stock-meta">
        <Freshness state={resource?.source === "api" ? "盤後更新" : "資料待更新"} asOf={resource?.source === "api" ? "正式 V2 Read Model" : "資料日期待補"} />
        <DataState state={dataState} />
        {resource?.source !== "api" && <span className="tp-preview-badge">Preview · 部分資料等待正式 Read Model</span>}
      </div>
      <section className="tp-stock-workspace">
        <div className="tp-stock-main">
          <Card className="tp-stock-toolbar">
            <label>市場<select value={market} onChange={(event) => setMarket(event.target.value)}><option value="all">全部</option><option value="TPE">上市（TPE）</option><option value="TWO">上櫃（TWO）</option></select></label>
            <label>排序<select value={sort} onChange={(event) => { setSort(event.target.value as SortKey); setLastSorted(new Date()); }}><option value="change">漲幅</option><option value="price">股價</option><option value="volume">成交量</option></select></label>
            <button type="button" className={`tp-stock-advanced-toggle ${advancedOpen ? "is-open" : ""}`} aria-expanded={advancedOpen} onClick={() => setAdvancedOpen((value) => !value)}>進階篩選⌄</button>
            <button type="button" className="tp-stock-resort" onClick={() => setLastSorted(new Date())}>↻ 重新排序</button>
          </Card>
          {advancedOpen && <Card className="tp-stock-advanced"><label>題材<select value={topic} onChange={(event) => setTopic(event.target.value)}><option value="">全部題材</option>{topics.map(([slug, name]) => <option key={slug} value={slug}>{name}</option>)}</select></label><span>均線</span><span>法人</span><span>技術</span><span>更新狀態</span><span className="tp-muted">題材清單來自正式 Topic read model／股票關聯。</span></Card>}
          <div className="tp-stock-segments"><button className={mode === "all" ? "is-active" : ""} onClick={() => setMode("all")}>全部</button><button className={mode === "live" ? "is-active" : ""} onClick={() => setMode("live")}>LIVE</button><button className={mode === "eod" ? "is-active" : ""} onClick={() => setMode("eod")}>EOD</button><span className="tp-muted">最後排序 {lastSorted.toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit" })} · {totalLabel} 檔</span></div>
          {resource === null ? <Card><EmptyState title="正在載入正式股票資料" description="正在讀取 PostgreSQL-backed Stock read model。" /></Card> : resource.source === "unavailable" ? <Card><EmptyState title="股票資料目前無法取得" description={resource.error ?? "請確認 FastAPI read model 是否已啟動。"} /></Card> : <div className="tp-stock-grid">{displayRows.map((stock) => <button type="button" className={`tp-stock-tile ${selected?.code === stock.code ? "is-selected" : ""}`} key={stock.code} onClick={() => setSelected(stock)}><span className="tp-stock-tile-top"><strong>{stock.name}</strong><em>{isLive(stock) ? "LIVE" : "EOD"}</em></span><small>{stock.code} · {stock.topics[0]?.name ?? "題材待補"}</small><span className="tp-stock-tile-quote"><b>{price(stock.price)}</b><i className={stock.changePct !== null && stock.changePct < 0 ? "tp-stock-down" : "tp-stock-up"}>{change(stock.changePct)}</i></span>{!isLive(stock) && <span className="tp-stock-eod-note">盤後更新</span>}</button>)}</div>}
        </div>
        {selected && <StockEncyclopediaDrawer presentation="inline" stock={drawerItem(selected)} onClose={() => setSelected(null)} />}
      </section>
    </PageContainer>
  </AppShell>;
}
