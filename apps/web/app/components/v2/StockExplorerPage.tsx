"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AppShell, Card, DataState, EmptyState, Freshness, PageContainer } from "./V2Foundation";
import { StockEncyclopediaDrawer, type StockDrawerItem } from "./StockEncyclopediaDrawer";
import {
  fetchFormalStocks,
  getFormalApiBaseUrl,
  type StockApiItem,
  type StockApiResource,
} from "../../lib/stock-api";
import { useFavoritesState } from "../FavoriteButton";
import { useSnapshot } from "../../lib/snapshot-store";
import type { StockView } from "../../lib/types";

type SortKey = "change" | "price" | "volume";
type FilterValue = "all" | "above20" | "above60" | "available";
type ExplorerRow = {
  code: string;
  name: string;
  market: string;
  exchange: string | null;
  listing: string | null;
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
  technicalEvidence: StockDrawerItem["technicalEvidence"];
  institutionFlows: Record<string, unknown> | null;
  favorite: Record<string, unknown> | null;
  opportunity: Record<string, unknown> | null;
  summary: string | null;
  isPreview: boolean;
};

type DetailPanelState = "closed" | "open" | "closing";

const UI = {
  eyebrow: "\u80a1\u7968\u63a2\u7d22",
  title: "\u80a1\u7968",
  description: "\u5f9e\u6b63\u5f0f\u80a1\u7968\u5b87\u5b99\u7be9\u9078\u503c\u5f97\u7814\u7a76\u7684\u6a19\u7684",
  market: "\u5e02\u5834",
  all: "\u5168\u90e8",
  listed: "\u4e0a\u5e02",
  otc: "\u4e0a\u6ac3",
  sort: "\u6392\u5e8f",
  change: "\u6f32\u5e45",
  price: "\u80a1\u50f9",
  volume: "\u6210\u4ea4\u91cf",
  advanced: "\u9032\u968e\u7be9\u9078",
  resort: "\u91cd\u65b0\u6392\u5e8f",
  topic: "\u984c\u6750",
  technical: "\u6280\u8853",
  chip: "\u7c4c\u78bc / \u6cd5\u4eba",
  strategy: "\u500b\u4eba\u7b56\u7565",
  updateMode: "\u66f4\u65b0\u6a21\u5f0f",
  live: "LIVE",
  eod: "EOD",
  postClose: "\u76e4\u5f8c\u66f4\u65b0",
  lastSorted: "\u6700\u5f8c\u6392\u5e8f",
  formalReadModel: "\u6b63\u5f0f V2 Read Model",
  preview: "Preview \u00b7 \u50c5\u4f9b\u9810\u89bd\uff0c\u672a\u9023\u63a5\u6b63\u5f0f API",
  loading: "\u6b63\u5728\u8f09\u5165\u6b63\u5f0f\u80a1\u7968\u8cc7\u6599",
  unavailable: "\u80a1\u7968\u6b63\u5f0f\u8cc7\u6599\u7121\u6cd5\u8f09\u5165",
  unavailableDescription: "\u8acb\u5148\u914d\u7f6e FastAPI stock read model origin\uff1b\u9810\u89bd\u6a21\u5f0f\u4e0d\u6703\u8986\u84cb\u6b63\u5f0f\u8cc7\u6599",
  missing: "\u5f85\u8cc7\u6599",
  noTopic: "\u5c1a\u7121\u984c\u6750",
  noRows: "\u6c92\u6709\u7b26\u5408\u76ee\u524d\u7be9\u9078\u7684\u80a1\u7968",
  allTopics: "\u5168\u90e8\u984c\u6750",
  allTechnical: "\u5168\u90e8\u6280\u8853\u72c0\u614b",
  above20: "\u9ad8\u65bc 20MA",
  above60: "\u9ad8\u65bc 60MA",
  technicalAvailable: "\u6709\u6280\u8853\u8b49\u64da",
  allChip: "\u5168\u90e8\u7c4c\u78bc\u72c0\u614b",
  chipAvailable: "\u6709\u6cd5\u4eba\u8b49\u64da",
  allStrategy: "\u5168\u90e8\u500b\u4eba\u7b56\u7565",
  favorites: "\u6211\u7684\u6536\u85cf",
  opportunities: "\u6709\u6a5f\u6703",
  allUpdateModes: "\u5168\u90e8\u66f4\u65b0\u6a21\u5f0f",
  count: "\u6a94",
} as const;

function formatPrice(value: number | null): string {
  return value === null ? "—" : value.toLocaleString("zh-TW", { maximumFractionDigits: 2 });
}

function formatChange(value: number | null): string {
  return value === null ? "—" : `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function asOfDate(item: StockApiItem): string | null {
  const value = item.historyCoverage?.asOfDate;
  return typeof value === "string" ? value : null;
}

function mainTopic(value: StockApiItem["mainTopic"]): StockDrawerItem["mainTopic"] {
  if (!value || typeof value.name !== "string") return null;
  return {
    name: value.name,
    grade: typeof value.grade === "string" ? value.grade : null,
    state: typeof value.state === "string" ? value.state : null,
    lifecycle: typeof value.lifecycle === "string" ? value.lifecycle : null,
  };
}

function fromFormal(item: StockApiItem): ExplorerRow {
  return {
    code: item.code,
    name: item.name ?? item.code,
    market: item.market,
    exchange: item.exchange,
    listing: item.listing,
    price: item.price,
    changePct: item.changePct,
    volume: item.volume,
    dataFreshness: item.dataFreshness,
    updateMode: item.updateMode,
    observedAt: item.observedAt,
    dataDate: asOfDate(item),
    updatedAt: item.retrievedAt,
    topics: (item.topicRelations ?? []).map((relation) => ({
      slug: relation.topicSlug,
      name: relation.topicName,
      role: relation.topicRole,
    })),
    mainTopic: mainTopic(item.mainTopic),
    technicalEvidence: item.technicalEvidence,
    institutionFlows: item.institutionFlows,
    favorite: item.favorite,
    opportunity: item.opportunity,
    summary: item.summary,
    isPreview: false,
  };
}

function fromPreview(item: StockView): ExplorerRow {
  return {
    code: item.code,
    name: item.name ?? item.code,
    market: "DEMO",
    exchange: null,
    listing: null,
    price: item.price,
    changePct: item.change,
    volume: item.volume,
    dataFreshness: item.dataFreshness,
    updateMode: "POST_CLOSE",
    observedAt: null,
    dataDate: item.dataDate,
    updatedAt: item.updatedAt,
    topics: item.relations.map((relation) => ({ slug: relation.topic, name: relation.topic, role: relation.role })),
    mainTopic: item.topicMain ? { name: item.topicMain, grade: null, state: null } : null,
    technicalEvidence: null,
    institutionFlows: null,
    favorite: null,
    opportunity: null,
    summary: null,
    isPreview: true,
  };
}

function isLive(row: ExplorerRow): boolean {
  return row.updateMode.toUpperCase() === "INTRADAY";
}

function hasValue(record: Record<string, unknown> | null): boolean {
  return Object.values(record ?? {}).some((value) => value !== null && value !== undefined && value !== "");
}

function compareRows(a: ExplorerRow, b: ExplorerRow, sort: SortKey): number {
  const left = sort === "change" ? a.changePct : sort === "price" ? a.price : a.volume;
  const right = sort === "change" ? b.changePct : sort === "price" ? b.price : b.volume;
  if (left === null && right !== null) return 1;
  if (left !== null && right === null) return -1;
  if (left !== null && right !== null && left !== right) return right - left;
  return a.code.localeCompare(b.code, "en");
}

function apiSort(sort: SortKey): string {
  return sort === "price" ? "priceDesc" : sort === "volume" ? "volumeDesc" : "changePctDesc";
}

export default function StockExplorerPage() {
  const { bundle } = useSnapshot();
  const { codes: favoriteCodes } = useFavoritesState();
  const [resource, setResource] = useState<StockApiResource | null>(null);
  const [market, setMarket] = useState("all");
  const [sort, setSort] = useState<SortKey>("change");
  const [mode, setMode] = useState("all");
  const [topic, setTopic] = useState("");
  const [technical, setTechnical] = useState<FilterValue>("all");
  const [chip, setChip] = useState("all");
  const [strategy, setStrategy] = useState("all");
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [selected, setSelected] = useState<ExplorerRow | null>(null);
  const [detailPanelState, setDetailPanelState] = useState<DetailPanelState>("closed");
  const [lastSorted, setLastSorted] = useState(() => new Date());
  const orderRef = useRef<string[]>([]);
  const [formalOrder, setFormalOrder] = useState<string[]>([]);
  const requestIdRef = useRef(0);
  const controllerRef = useRef<AbortController | null>(null);
  const detailCloseTimerRef = useRef<number | null>(null);

  const openDetailPanel = useCallback((stock: ExplorerRow) => {
    if (detailCloseTimerRef.current !== null) {
      window.clearTimeout(detailCloseTimerRef.current);
      detailCloseTimerRef.current = null;
    }
    setSelected(stock);
    setDetailPanelState("open");
  }, []);

  const closeDetailPanel = useCallback(() => {
    if (!selected || detailPanelState === "closing") return;
    setDetailPanelState("closing");
    detailCloseTimerRef.current = window.setTimeout(() => {
      setSelected(null);
      setDetailPanelState("closed");
      detailCloseTimerRef.current = null;
    }, 280);
  }, [detailPanelState, selected]);

  const loadFormal = useCallback(async (requestedSort: SortKey, resetOrder: boolean) => {
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    const next = await fetchFormalStocks({ sort: apiSort(requestedSort) }, { signal: controller.signal });
    if (requestId !== requestIdRef.current) return;
    if (next.source === "api" && next.data) {
      const incomingCodes = next.data.map((item) => item.code);
      let nextOrder: string[];
      if (resetOrder || orderRef.current.length === 0) {
        nextOrder = incomingCodes;
      } else {
        const incoming = new Set(incomingCodes);
        nextOrder = orderRef.current.filter((code) => incoming.has(code));
        nextOrder.push(...incomingCodes.filter((code) => !nextOrder.includes(code)));
      }
      orderRef.current = nextOrder;
      setFormalOrder(nextOrder);
    }
    setResource(next);
  }, []);

  useEffect(() => {
    void loadFormal(sort, true);
    return () => controllerRef.current?.abort();
  }, [loadFormal, sort]);

  useEffect(() => {
    if (!getFormalApiBaseUrl()) return;
    const timer = window.setInterval(() => void loadFormal(sort, false), 60_000);
    return () => window.clearInterval(timer);
  }, [loadFormal, sort]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape" && selected) closeDetailPanel();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [closeDetailPanel, selected]);

  useEffect(() => () => {
    if (detailCloseTimerRef.current !== null) window.clearTimeout(detailCloseTimerRef.current);
  }, []);

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

  const filteredRows = useMemo(() => baseRows.filter((row) => {
    const technicalMatch = technical === "all"
      || (technical === "above20" && row.technicalEvidence?.above20MA === true)
      || (technical === "above60" && row.technicalEvidence?.above60MA === true)
      || (technical === "available" && row.technicalEvidence !== null);
    const chipMatch = chip === "all" || (chip === "available" && hasValue(row.institutionFlows));
    const strategyMatch = strategy === "all"
      || (strategy === "favorite" && (favoriteCodes.includes(row.code) || row.favorite !== null))
      || (strategy === "opportunity" && row.opportunity !== null);
    const modeMatch = mode === "all" || (mode === "live" ? isLive(row) : !isLive(row));
    return (market === "all" || row.market === market)
      && modeMatch
      && (!topic || row.topics.some((item) => item.slug === topic))
      && technicalMatch
      && chipMatch
      && strategyMatch;
  }), [baseRows, chip, favoriteCodes, market, mode, strategy, technical, topic]);

  const displayRows = useMemo(() => {
    if (resource?.source !== "api") return [...filteredRows].sort((a, b) => compareRows(a, b, sort));
    const byCode = new Map(filteredRows.map((row) => [row.code, row]));
    const ordered = formalOrder.flatMap((code) => {
      const row = byCode.get(code);
      return row ? [row] : [];
    });
    const known = new Set(ordered.map((row) => row.code));
    ordered.push(...filteredRows.filter((row) => !known.has(row.code)));
    return ordered;
  }, [filteredRows, formalOrder, resource?.source, sort]);

  const drawerItem = (stock: ExplorerRow): StockDrawerItem => ({
    code: stock.code,
    name: stock.name,
    market: stock.market,
    exchange: stock.exchange,
    listing: stock.listing,
    price: stock.price,
    changePct: stock.changePct,
    dataFreshness: stock.dataFreshness,
    updatedAt: stock.updatedAt,
    dataDate: stock.dataDate,
    isPreview: stock.isPreview,
    topics: stock.topics.map((item) => ({ name: item.name, role: item.role })),
    mainTopic: stock.mainTopic,
    technicalEvidence: stock.technicalEvidence,
    institutionFlows: stock.institutionFlows,
    opportunity: stock.opportunity,
    summary: stock.summary,
  });

  const dataState = resource === null
    ? "STALE"
    : resource.source === "api"
      ? "AVAILABLE"
      : resource.source === "unavailable"
        ? "UNAVAILABLE"
        : "STALE";
  const total = resource?.source === "api" ? resource.universe.total ?? baseRows.length : baseRows.length;
  const isPreview = resource?.source !== "api";

  return <AppShell currentPath="/stocks">
    <PageContainer eyebrow={UI.eyebrow} title={UI.title} description={UI.description}>
      <div className="tp-stock-meta">
        <Freshness state={resource?.source === "api" ? "\u76e4\u4e2d\u66f4\u65b0" : "\u8cc7\u6599\u5f85\u66f4\u65b0"} asOf={resource?.source === "api" ? UI.formalReadModel : "Preview snapshot"} />
        <DataState state={dataState} />
        {isPreview && <span className="tp-preview-badge">{UI.preview}</span>}
      </div>
      <section className="tp-stock-workspace tp-stock-workspace--push" data-detail-state={detailPanelState}>
        <div className="tp-stock-main">
          <Card className="tp-stock-toolbar">
            <label><span>{UI.market}</span><select value={market} onChange={(event) => setMarket(event.target.value)}><option value="all">{UI.all}</option><option value="TPE">{UI.listed} · TPE</option><option value="TWO">{UI.otc} · TWO</option></select></label>
            <label><span>{UI.sort}</span><select value={sort} onChange={(event) => { setSort(event.target.value as SortKey); setLastSorted(new Date()); }}><option value="change">{UI.change}</option><option value="price">{UI.price}</option><option value="volume">{UI.volume}</option></select></label>
            <button type="button" className={`tp-stock-advanced-toggle ${advancedOpen ? "is-open" : ""}`} aria-expanded={advancedOpen} onClick={() => setAdvancedOpen((value) => !value)}>{UI.advanced}⌄</button>
            <button type="button" className="tp-stock-resort" onClick={() => { setLastSorted(new Date()); void loadFormal(sort, true); }}>{UI.resort}</button>
          </Card>
          {advancedOpen && <Card className="tp-stock-advanced">
            <label><span>{UI.topic}</span><select value={topic} onChange={(event) => setTopic(event.target.value)}><option value="">{UI.allTopics}</option>{topics.map(([slug, name]) => <option key={slug} value={slug}>{name}</option>)}</select></label>
            <label><span>{UI.technical}</span><select value={technical} onChange={(event) => setTechnical(event.target.value as FilterValue)}><option value="all">{UI.allTechnical}</option><option value="above20">{UI.above20}</option><option value="above60">{UI.above60}</option><option value="available">{UI.technicalAvailable}</option></select></label>
            <label><span>{UI.chip}</span><select value={chip} onChange={(event) => setChip(event.target.value)}><option value="all">{UI.allChip}</option><option value="available">{UI.chipAvailable}</option></select></label>
            <label><span>{UI.strategy}</span><select value={strategy} onChange={(event) => setStrategy(event.target.value)}><option value="all">{UI.allStrategy}</option><option value="favorite">{UI.favorites}</option><option value="opportunity">{UI.opportunities}</option></select></label>
            <label><span>{UI.updateMode}</span><select value={mode} onChange={(event) => setMode(event.target.value)}><option value="all">{UI.allUpdateModes}</option><option value="live">{UI.live}</option><option value="eod">{UI.eod}</option></select></label>
          </Card>}
          <div className="tp-stock-segments"><button type="button" className={mode === "all" ? "is-active" : ""} onClick={() => setMode("all")}>{UI.all}</button><button type="button" className={mode === "live" ? "is-active" : ""} onClick={() => setMode("live")}>{UI.live}</button><button type="button" className={mode === "eod" ? "is-active" : ""} onClick={() => setMode("eod")}>{UI.eod}</button><span className="tp-muted">{UI.lastSorted} {lastSorted.toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit" })} · {displayRows.length}/{total} {UI.count}</span></div>
          {resource === null ? <Card><EmptyState title={UI.loading} description="PostgreSQL-backed Stock read model" /></Card> : resource.source === "unavailable" ? <Card><EmptyState title={UI.unavailable} description={resource.error ?? UI.unavailableDescription} /></Card> : displayRows.length === 0 ? <Card><EmptyState title={UI.noRows} description={UI.unavailableDescription} /></Card> : <div className="tp-stock-grid">{displayRows.map((stock) => <button type="button" className={`tp-stock-tile ${selected?.code === stock.code ? "is-selected" : ""} ${isLive(stock) ? "" : "is-eod"}`} key={stock.code} onClick={() => openDetailPanel(stock)} aria-label={`${stock.name} ${stock.code}`}><span className="tp-stock-tile-top"><strong>{stock.name}</strong><em>{isLive(stock) ? UI.live : UI.eod}</em></span><small>{stock.code} · {stock.market} · {stock.topics[0]?.name ?? UI.noTopic}</small><span className="tp-stock-tile-quote"><b>{formatPrice(stock.price)}</b><i className={stock.changePct === null ? "tp-muted" : stock.changePct < 0 ? "tp-stock-down" : "tp-stock-up"}>{formatChange(stock.changePct)}</i></span>{!isLive(stock) && <span className="tp-stock-eod-note">{UI.postClose}</span>}</button>)}</div>}
        </div>
        {selected && <StockEncyclopediaDrawer presentation="push" isClosing={detailPanelState === "closing"} stock={drawerItem(selected)} onClose={closeDetailPanel} />}
      </section>
    </PageContainer>
  </AppShell>;
}
