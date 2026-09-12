"use client";

import Link from "next/link";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchFormalStock, fetchFormalStockTechnical, type StockApiItem, type StockDetailResource } from "../../lib/stock-api";
import type { StockEodRead, StockTechnicalResource, StockTechnicalState } from "../../lib/stock-api";
import { selectStockQuote } from "../../lib/stock-eod-presenter";
import { commercialDataState, commercialStateLabel } from "../../lib/commercial-state.mjs";
import { useFavoritesState } from "../FavoriteButton";
import { FavoriteStar, Freshness, RoleChip } from "./V2Foundation";
import { StockPriceHistoryPanel } from "./StockPriceHistoryPanel";

export type StockDrawerTopic = { name: string; role: string | null };

export type StockDrawerItem = {
  code: string;
  name: string;
  market?: string | null;
  exchange?: string | null;
  listing?: string | null;
  industry?: string | null;
  price: number | null;
  changePct: number | null;
  volume?: number | null;
  eod?: StockEodRead | null;
  updateMode?: string | null;
  dataFreshness: string | null;
  updatedAt?: string | null;
  dataDate?: string | null;
  topics: StockDrawerTopic[];
  mainTopic?: { name: string; grade?: string | null; state?: string | null; lifecycle?: string | null } | null;
  institutionFlows?: Record<string, unknown> | null;
  summary?: string | null;
  opportunity?: Record<string, unknown> | null;
  isPreview?: boolean;
};

const label = (value: string | null) => {
  return value?.trim() || "角色尚未發布";
};

const fresh = (value: string | null): "盤中更新" | "盤後更新" | "資料待更新" => {
  const v = (value ?? "").toUpperCase();
  if (/CURRENT|LIVE|INTRADAY/.test(v)) return "盤中更新";
  if (/EOD|POST|AFTER/.test(v)) return "盤後更新";
  return "資料待更新";
};

export function formalDrawerItem(detail: StockApiItem): StockDrawerItem {
  const asOfDate = typeof detail.historyCoverage?.asOfDate === "string" ? detail.historyCoverage.asOfDate : null;
  return {
    code: detail.code,
    name: detail.name ?? detail.code,
    market: detail.market,
    exchange: detail.exchange,
    listing: detail.listing,
    price: detail.price,
    changePct: detail.changePct,
    volume: detail.volume,
    eod: detail.eod,
    updateMode: detail.updateMode,
    dataFreshness: detail.dataFreshness,
    updatedAt: detail.eod?.retrievedAt ?? detail.retrievedAt,
    dataDate: detail.eod?.tradingDate ?? asOfDate,
    topics: detail.topicRelations.map((topic) => ({ name: topic.topicName, role: topic.topicRole })),
    mainTopic: detail.mainTopic,
    institutionFlows: detail.institutionFlows,
    summary: detail.summary,
    opportunity: detail.opportunity,
    isPreview: false,
  };
}

function displayValue(value: string | number | boolean | null | undefined): string {
  if (value === null || value === undefined || value === "") return "尚未提供";
  if (typeof value === "boolean") return value ? "是" : "否";
  if (typeof value === "number") return value.toLocaleString("zh-TW", { maximumFractionDigits: 2 });
  return value;
}

function displayNumber(value: number | null | undefined): string {
  return value === null || value === undefined
    ? "—"
    : value.toLocaleString("zh-TW", { maximumFractionDigits: 4 });
}

function displaySigned(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${value >= 0 ? "+" : ""}${displayNumber(value)}`;
}

function displayPercent(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

const EOD_STATUS_LABEL: Record<string, string> = {
  AVAILABLE: "可用",
  PARTIAL: "部分可用",
  UNAVAILABLE: "不可用",
  NO_TRADE: "無交易",
  SUSPENDED: "停牌",
  ADJUSTMENT_UNKNOWN: "除權息狀態未知",
  SOURCE_CONFLICT: "來源衝突",
  PREVIEW: "Preview",
};

function statusLabel(value: string | null | undefined): string {
  return value ? EOD_STATUS_LABEL[value] ?? value : "尚未提供";
}

function sourceLabel(source: StockEodRead["priceSource"] | StockEodRead["volumeSource"] | null | undefined): string {
  if (!source) return "尚未提供";
  return source.sourceCode;
}

function EvidenceGrid({ rows }: { rows: Array<[string, string | number | boolean | null | undefined]> }) {
  return <dl className="tp-stock-encyclopedia-evidence-grid">{rows.map(([name, value]) => <div key={name}><dt>{name}</dt><dd>{displayValue(value)}</dd></div>)}</dl>;
}

const TECHNICAL_INDICATOR_LABELS: Record<string, string> = {
  MA5: "MA5",
  MA10: "MA10",
  MA20: "MA20",
  MA60: "MA60",
  DISTANCE_TO_MA20: "收盤距 MA20（原始比率）",
  RAW_CLOSE_RETURN_5D: "5 日原始收盤報酬（比率）",
  RAW_CLOSE_RETURN_20D: "20 日原始收盤報酬（比率）",
  VOLUME_MA5: "成交量 MA5",
  VOLUME_MA20: "成交量 MA20",
  VOLUME_RATIO_20: "成交量／20 日均量（比率）",
  RSI14: "RSI14",
  MACD_12_26_9: "MACD 12/26/9",
  MACD_SIGNAL_12_26_9: "MACD Signal 12/26/9",
  MACD_HISTOGRAM_12_26_9: "MACD Histogram 12/26/9",
};

function technicalEvidenceValue(value: string | null): string {
  return value ?? "—";
}

export function StockTechnicalEvidenceContent({ resource, state, onRetry }: {
  resource: StockTechnicalResource | null;
  state: StockTechnicalState | "LOADING";
  onRetry?: () => void;
}) {
  const data = resource?.data ?? null;
  const evidenceSession = data?.provenance?.latestTradingDate ?? data?.requestedTo ?? null;
  const evidence = data?.technicalEvidence.filter((item) => item.sessionDate === evidenceSession) ?? [];
  return <section className="tp-stock-encyclopedia-section tp-stock-technical-evidence" data-technical-state={state} aria-label="正式技術證據">
    <div className="tp-stock-encyclopedia-section-heading"><h3>技術證據</h3><span>{commercialStateLabel(state)}</span></div>
    {state === "LOADING" && <p className="tp-stock-encyclopedia-muted">正在讀取正式技術證據。</p>}
    {state === "ERROR" && <><p className="tp-stock-encyclopedia-muted">{resource?.error ?? "正式技術證據讀取失敗。"}</p>{onRetry && <button type="button" onClick={onRetry}>重新讀取技術證據</button>}</>}
    {state === "UNAVAILABLE" && <p className="tp-stock-encyclopedia-muted">{resource?.error ?? (data?.reasonCodes.join("、") || "正式技術證據目前不可用。")}</p>}
    {state === "EMPTY" && <p className="tp-stock-encyclopedia-muted">正式技術 authority 可用，但此交易日沒有可發布的 evidence。</p>}
    {(state === "AVAILABLE" || state === "PARTIAL") && data && <>
      <EvidenceGrid rows={[
        ["技術結果", data.technicalResultStatus],
        ["MA60 資格", data.technicalEligibility],
        ["事件權威", data.eventAuthorityStatus],
        ["發布狀態", data.publicationStatus],
        ["計算權責", data.calculationOwner],
        ["瀏覽器計算", data.browserCalculationAllowed],
      ]} />
      {state === "PARTIAL" && <p className="tp-stock-encyclopedia-muted">此批證據為 PARTIAL；受限值維持 FORMAL_WITH_LIMITATION，不代表完整事件權威。</p>}
      <div className="tp-stock-eod-lineage">
        <span>來源：{data.provenance?.authority ?? "尚未提供"}</span>
        <span>資料語意：{data.provenance?.seriesSemantics ?? data.priceBasis}</span>
        <span>證據交易日：{evidenceSession ?? "尚未提供"}</span>
        <span>asOf：{data.asOf ?? "尚未提供"}</span>
        <span>除權息：{data.provenance?.adjustmentState ?? "UNKNOWN"}</span>
        <span>時效狀態：契約未發布</span>
      </div>
      {data.limitationReasons.length > 0 && <p className="tp-stock-encyclopedia-muted">限制：{data.limitationReasons.join("、")}</p>}
      <dl className="tp-stock-encyclopedia-evidence-grid">
        {evidence.map((item) => <div key={`${item.sessionDate}-${item.indicatorId}`} data-indicator-id={item.indicatorId} data-indicator-publication={item.publicationState}>
          <dt>{TECHNICAL_INDICATOR_LABELS[item.indicatorId] ?? item.indicatorId}</dt>
          <dd>{technicalEvidenceValue(item.value)} · {item.publicationState}{item.availabilityReason ? ` · ${item.availabilityReason}` : ""}</dd>
        </div>)}
      </dl>
      <p className="tp-stock-encyclopedia-muted">版本：{data.technicalContractVersion} · {data.technicalPolicyVersion}。數值由 backend 正式 evidence 原樣顯示；raw price history 不用於瀏覽器技術計算。</p>
    </>}
  </section>;
}

function StockTechnicalEvidencePanel({ code, market, sessionDate, enabled, isPreview }: {
  code: string;
  market?: string | null;
  sessionDate?: string | null;
  enabled: boolean;
  isPreview: boolean;
}) {
  const requestKey = `${market ?? ""}:${code}:${sessionDate ?? ""}`;
  const [result, setResult] = useState<{ key: string; resource: StockTechnicalResource } | null>(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!enabled || isPreview || !market || !sessionDate) return;
    let active = true;
    const controller = new AbortController();
    fetchFormalStockTechnical(code, { market, sessionDate, signal: controller.signal }).then((resource) => {
      if (active) setResult({ key: requestKey, resource });
    });
    return () => { active = false; controller.abort(); };
  }, [code, enabled, isPreview, market, requestKey, retry, sessionDate]);
  const resource = result?.key === requestKey ? result.resource : null;
  const state: StockTechnicalState | "LOADING" = !enabled || isPreview || !market || !sessionDate
    ? "UNAVAILABLE"
    : resource?.state ?? "LOADING";
  const unavailable = !enabled || isPreview || !market || !sessionDate
    ? { source: "unavailable", data: null, error: isPreview ? "Preview 不代表正式技術證據。" : "正式技術證據需要已發布的市場與 EOD 交易日。", state: "UNAVAILABLE" } as const
    : resource;
  return <StockTechnicalEvidenceContent resource={unavailable} state={state} onRetry={() => { setResult(null); setRetry((value) => value + 1); }} />;
}

export function emptyFormalStock(stock: StockDrawerItem): StockDrawerItem {
  return { code: stock.code, name: stock.code, market: stock.market,
    price: null, changePct: null, dataFreshness: null, topics: [], isPreview: false };
}

type ViewProps = { stock: StockDrawerItem; onClose: () => void; presentation?: "overlay" | "inline" | "push"; isClosing?: boolean };

export function StockEncyclopediaDrawer(props: ViewProps) {
  const { stock } = props;
  const requestKey = `${stock.market ?? ""}:${stock.code}:${stock.isPreview === true}`;
  const [state, setState] = useState<{ key: string; result: StockDetailResource } | null>(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    if (stock.isPreview !== true) {
      fetchFormalStock(stock.code, { market: stock.market, signal: controller.signal }).then((result) => {
        if (active) setState({ key: requestKey, result });
      });
    }
    return () => { active = false; controller.abort(); };
  }, [requestKey, stock.code, stock.market, stock.isPreview, retry]);
  const result = state?.key === requestKey ? state.result : null;
  const displayStock = stock.isPreview === true ? stock : result?.data ? formalDrawerItem(result.data) : emptyFormalStock(stock);
  return <StockEncyclopediaView {...props} stock={displayStock}
    detailState={stock.isPreview === true ? "PREVIEW" : result?.state ?? "LOADING"}
    detailError={result?.error ?? null} onRetry={() => { setState(null); setRetry((value) => value + 1); }} />;
}

export function StockEncyclopediaView({ stock: displayStock, onClose, presentation = "overlay", isClosing = false, detailState, detailError, onRetry }: ViewProps & {
  detailState: string; detailError: string | null; onRetry: () => void;
}) {
  const { isFavorite, toggle: toggleFavorite } = useFavoritesState();
  const quote = selectStockQuote(displayStock);
  const tone = quote.changePct === null ? "flat" : quote.changePct >= 0 ? "up" : "down";
  const eodStatus = displayStock.isPreview ? "PREVIEW" : displayStock.eod?.dataStatus ?? "UNAVAILABLE";
  const commercialState = displayStock.isPreview ? "PREVIEW" : detailState === "PUBLISHED"
    ? commercialDataState({ status: eodStatus, freshness: displayStock.dataFreshness, rowCount: displayStock.eod ? 1 : 0 }).state
    : detailState;
  const institutionEntries = Object.entries(displayStock.institutionFlows ?? {}).filter(([, value]) => value !== null && value !== undefined);
  const presentationClass = presentation === "inline"
    ? "tp-stock-encyclopedia-drawer--inline"
    : presentation === "push"
      ? `tp-stock-encyclopedia-drawer--push${isClosing ? " is-closing" : ""}`
      : "";
  const drawer = <aside className={`tp-stock-encyclopedia-drawer ${presentationClass}`} role="dialog" aria-modal={presentation === "overlay" ? true : undefined} aria-labelledby="stock-encyclopedia-title" onClick={(event) => event.stopPropagation()}>
    <header className="tp-stock-encyclopedia-header">
      <div>
        <p className="tp-eyebrow">股票圖鑑</p>
        <h2 id="stock-encyclopedia-title">{displayStock.name}</h2>
        <span>{displayStock.code}{displayStock.market ? ` · ${displayStock.market}` : ""}{displayStock.exchange ? ` · ${displayStock.exchange}` : ""}</span>
      </div>
      <div className="tp-stock-encyclopedia-actions"><FavoriteStar active={isFavorite(displayStock.code, displayStock.market)} onClick={() => toggleFavorite(displayStock.code, { market: displayStock.market, displayLabel: displayStock.name })} /><button type="button" className="tp-stock-close" aria-label="Close stock drawer" title="Close" onClick={onClose}><X size={18} aria-hidden="true" /></button></div>
    </header>
    <div className="tp-stock-encyclopedia-body" data-stock-read-state={commercialState}>
      <p role={commercialState === "ERROR" ? "alert" : "status"}>{displayStock.isPreview ? "Preview" : `正式 V2 股票讀取 · ${commercialStateLabel(commercialState)}`} · {displayStock.market ?? "市場待確認"}:{displayStock.code}</p>
      {detailState === "PUBLISHED" && <p>行情可用狀態：{displayStock.eod?.dataStatus ?? "UNAVAILABLE"} · 資料時效：{displayStock.dataFreshness ?? "UNKNOWN"} · 交易日：{displayStock.dataDate ?? "尚未提供"}（不代表已更新至最新交易日）。發布批次／時間：尚未提供。</p>}
      {detailState === "ERROR" && <button type="button" onClick={onRetry}>重新讀取</button>}
      {detailState === "EMPTY" && <p>此市場與代碼沒有正式股票結果。</p>}
      {detailState === "PUBLISHED" && <StockPriceHistoryPanel symbol={displayStock.code} market={displayStock.market} isPreview={displayStock.isPreview === true} />}
      <div className="tp-stock-encyclopedia-freshness"><Freshness state={fresh(displayStock.dataFreshness)} asOf={displayStock.dataDate ?? "資料日期待補"} />{displayStock.isPreview && <span className="tp-stock-preview-label">Preview</span>}{detailState === "LOADING" && <span className="tp-muted">正在讀取正式 detail</span>}{detailState === "UNAVAILABLE" && !displayStock.isPreview && <span className="tp-muted">正式 detail 暫不可用</span>}</div>
      {detailError && !displayStock.isPreview && <p className="tp-stock-encyclopedia-muted">{detailError}</p>}
      <div className="tp-stock-encyclopedia-price"><strong>{quote.price === null ? "—" : quote.price.toLocaleString("zh-TW", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>{quote.changePct === null ? <span className="tp-muted">漲跌資料待更新</span> : <span className={`tp-topic-change tp-topic-change--${tone}`}>{displayPercent(quote.changePct)}</span>}</div>
      <section className="tp-stock-encyclopedia-section tp-stock-eod-read" data-eod-status={eodStatus} aria-label="正式 EOD 資料"><div className="tp-stock-encyclopedia-section-heading"><h3>EOD 行情</h3><span>{statusLabel(eodStatus)}</span></div>{displayStock.eod && !displayStock.isPreview ? <><EvidenceGrid rows={[["收盤價", displayNumber(displayStock.eod.close)], ["前收", displayNumber(displayStock.eod.previousClose)], ["漲跌", displaySigned(displayStock.eod.change)], ["漲跌幅", displayPercent(displayStock.eod.changePct)], ["開盤", displayNumber(displayStock.eod.open)], ["最高", displayNumber(displayStock.eod.high)], ["最低", displayNumber(displayStock.eod.low)], ["成交量", displayNumber(displayStock.eod.volume)], ["成交金額", displayNumber(displayStock.eod.turnover)], ["交易日", displayStock.eod.tradingDate]]} /><div className="tp-stock-eod-lineage"><span>價格來源：{sourceLabel(displayStock.eod.priceSource)}</span><span>成交量來源：{sourceLabel(displayStock.eod.volumeSource)}</span><span>除權息：{displayStock.eod.adjustmentState}</span><span>觀測：{displayStock.eod.observedAt ?? "尚未提供"}</span><span>讀取：{displayStock.eod.retrievedAt ?? "尚未提供"}</span></div></> : <p className="tp-stock-encyclopedia-muted">{displayStock.isPreview ? "Preview 不代表正式 EOD；正式 API 可用後才顯示。" : "正式 EOD 尚未提供；不以盤中值、歷史資料或 Preview 補值。"}</p>}</section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>股票身份</h3><span>{displayStock.listing ?? displayStock.industry ?? "正式欄位待補"}</span></div><EvidenceGrid rows={[["市場", displayStock.market], ["交易所", displayStock.exchange], ["產業／類別", displayStock.industry], ["資料日期", displayStock.dataDate]]} /></section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>題材歸屬</h3><span>{displayStock.topics.length} 個關係</span></div>{displayStock.topics.length ? <div className="tp-stock-encyclopedia-topics">{displayStock.topics.map((topic) => <div className="tp-stock-encyclopedia-topic" key={`${topic.name}-${topic.role ?? "unknown"}`}><strong>{topic.name}</strong><RoleChip>{label(topic.role)}</RoleChip></div>)}</div> : <p className="tp-stock-encyclopedia-muted">{detailState === "PUBLISHED" ? "目前正式題材關係為 0 筆。" : "正式題材關係尚未提供"}</p>}</section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>主要題材</h3><span>正式欄位優先</span></div>{displayStock.mainTopic ? <div className="tp-stock-encyclopedia-main-topic"><div><strong>{displayStock.mainTopic.name}</strong><p>{displayStock.mainTopic.state ?? "狀態尚未提供"}{displayStock.mainTopic.lifecycle ? ` · ${displayStock.mainTopic.lifecycle}` : ""}</p></div>{displayStock.mainTopic.grade && <RoleChip>{displayStock.mainTopic.grade}</RoleChip>}</div> : <p className="tp-stock-encyclopedia-muted">正式主題欄位尚未提供</p>}</section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>摘要</h3><span>正式 read model</span></div><p className="tp-stock-encyclopedia-muted">{displayStock.summary ?? "正式摘要尚未提供；未由前端生成。"}</p></section>
      <StockTechnicalEvidencePanel code={displayStock.code} market={displayStock.market} sessionDate={displayStock.eod?.tradingDate ?? null} enabled={detailState === "PUBLISHED"} isPreview={displayStock.isPreview === true} />
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>法人流向</h3><span>provider evidence</span></div>{institutionEntries.length ? <EvidenceGrid rows={institutionEntries.map(([key, value]) => [key, typeof value === "object" ? JSON.stringify(value) : value as string | number | boolean])} /> : <p className="tp-stock-encyclopedia-muted">正式法人資料尚未提供</p>}</section>
      <div className="tp-stock-encyclopedia-note">{displayStock.isPreview ? "此區塊目前為 Preview；正式 API 可用時才顯示正式欄位。" : "沒有正式 evidence 的欄位保持尚未提供，不由前端推導。"}</div>
      {presentation !== "inline" && !displayStock.isPreview && displayStock.market && <Link href={`/stocks/${encodeURIComponent(displayStock.code)}?market=${encodeURIComponent(displayStock.market)}`} target="_blank" rel="noopener noreferrer" className="tp-button tp-button--secondary">開啟獨立頁（新分頁，保留目前篩選）</Link>}
      {displayStock.opportunity ? <Link href="/opportunities" className="tp-button tp-button--secondary tp-stock-encyclopedia-cta">進入機會頁</Link> : <span className="tp-button tp-button--secondary tp-stock-encyclopedia-cta" aria-disabled="true">機會資料尚未提供</span>}
    </div>
  </aside>;
  return presentation === "inline" || presentation === "push" ? drawer : <div className="tp-stock-encyclopedia-layer" role="presentation" onClick={onClose}>{drawer}</div>;
}
