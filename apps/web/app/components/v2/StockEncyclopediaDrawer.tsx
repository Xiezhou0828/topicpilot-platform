"use client";

import Link from "next/link";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import {
  fetchFormalCompanyResearchV4,
  fetchFormalStock,
  type CompanyResearchV4,
  type StockApiItem,
} from "../../lib/stock-api";
import type { StockEodRead } from "../../lib/stock-api";
import { selectStockQuote } from "../../lib/stock-eod-presenter";
import { useFavoritesState } from "../FavoriteButton";
import { FavoriteStar, Freshness, RoleChip } from "./V2Foundation";
import { StockPriceHistoryPanel } from "./StockPriceHistoryPanel";

export type StockDrawerTopic = { name: string; role: string | null };

export type StockDrawerTechnicalEvidence = {
  above20MA: boolean | null;
  above60MA: boolean | null;
  ma20: number | null;
  ma60: number | null;
  breakoutState: string | null;
  technicalState: string | null;
};

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
  technicalEvidence?: StockDrawerTechnicalEvidence | null;
  institutionFlows?: Record<string, unknown> | null;
  summary?: string | null;
  opportunity?: Record<string, unknown> | null;
  isPreview?: boolean;
};

const label = (value: string | null) => {
  const v = (value ?? "").trim().toUpperCase();
  if (["代表股", "PRIMARY", "REPRESENTATIVE", "LEADER"].includes(v)) return "代表股";
  if (["核心股", "CORE", "SECONDARY"].includes(v)) return "核心股";
  if (["關聯股", "RELATED"].includes(v)) return "關聯股";
  return "尚未提供";
};

const fresh = (value: string | null): "盤中更新" | "盤後更新" | "資料待更新" => {
  const v = (value ?? "").toUpperCase();
  if (/CURRENT|LIVE|INTRADAY/.test(v)) return "盤中更新";
  if (/EOD|POST|AFTER/.test(v)) return "盤後更新";
  return "資料待更新";
};

function formalDrawerItem(base: StockDrawerItem, detail: StockApiItem): StockDrawerItem {
  const asOfDate = typeof detail.historyCoverage?.asOfDate === "string" ? detail.historyCoverage.asOfDate : null;
  return {
    ...base,
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
    updatedAt: detail.retrievedAt,
    dataDate: detail.eod?.tradingDate ?? asOfDate,
    topics: detail.topicRelations.map((topic) => ({ name: topic.topicName, role: topic.topicRole })),
    mainTopic: detail.mainTopic,
    technicalEvidence: detail.technicalEvidence,
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

function researchUnit(unit: string | null | undefined): string {
  if (unit === "TWD_100_MILLION") return " 億元";
  if (unit === "TWD_PER_SHARE") return " 元";
  if (unit === "PERCENT") return "%";
  return "";
}

function researchMetric(metric: { value: number | null; unit: string | null; statusNote: string | null } | undefined): string {
  if (!metric || metric.value === null) return metric?.statusNote ?? "—";
  return `${displayNumber(metric.value)}${researchUnit(metric.unit)}`;
}

function researchShare(value: number | null): string {
  if (value === null) return "";
  const percent = Math.abs(value) <= 1 ? value * 100 : value;
  return `${displayNumber(percent)}%`;
}

function CompanyResearchSection({ data, loading, error }: { data: CompanyResearchV4 | null; loading: boolean; error: string | null }) {
  const published = data?.publicationStatus === "PUBLISHED";
  const businessSummary = data?.overviewData?.businessModel?.shortDesc
    ?? data?.overviewData?.coreBusiness?.shortDesc
    ?? data?.sections?.companyAndBusiness?.summary;
  const products = data?.sections?.productsAndMarket;
  const finance = data?.finance;
  const historical = finance?.historicalTable;
  const historicalHeaders = historical?.headers ?? [];
  const historicalRows = historical?.rows ?? [];
  const segments = finance?.segmentPerformanceTable?.rows ?? [];
  const operatingGroups = data?.operatingMatrix ?? [];
  const annualSnapshot = data?.sections?.financialPerformance?.annualSnapshot;
  const customerConcentration = data?.sections?.customersAndChannels?.customerConcentration;

  return <section className="tp-stock-encyclopedia-section tp-company-research" aria-label="公司研究">
    <div className="tp-stock-encyclopedia-section-heading"><h3>公司研究</h3><span>{published ? `研究截至 ${data?.researchAsOf ?? "日期未提供"}` : "正式研究內容"}</span></div>
    {loading ? <p className="tp-stock-encyclopedia-muted">正在讀取已核准的公司研究內容。</p>
      : error ? <p className="tp-stock-encyclopedia-muted">公司研究資料暫時無法讀取。</p>
        : !published ? <p className="tp-stock-encyclopedia-muted">研究內容尚未公開；完成核准後才會顯示。</p>
          : <div className="tp-company-research-content">
            {businessSummary && <p className="tp-company-research-summary">{businessSummary}</p>}
            {products?.summary && <p className="tp-stock-encyclopedia-muted">{products.summary}</p>}
            {products?.revenueMix?.length ? <div className="tp-company-research-list" aria-label="營收結構">
              {products.revenueMix.map((row) => <div key={row.category}><strong>{row.category}</strong><span>{row.value === null ? "—" : `${displayNumber(row.value)}${researchUnit(row.unit)}`}{row.share === null ? "" : ` · ${researchShare(row.share)}`}</span></div>)}
            </div> : null}
            {customerConcentration && <p className="tp-stock-encyclopedia-muted">客戶集中度{customerConcentration.period ? ` · ${customerConcentration.period}` : ""}：{customerConcentration.largestCustomerRevenueShare === null || customerConcentration.largestCustomerRevenueShare === undefined ? customerConcentration.statusNote ?? "—" : `${displayNumber(customerConcentration.largestCustomerRevenueShare)}${researchUnit(customerConcentration.unit)}`}</p>}
            {operatingGroups.length ? <div className="tp-company-research-list" aria-label="主要產品與事業群">
              {operatingGroups.map((group) => <div className="tp-company-research-group" key={group.name}><strong>{group.name}{group.revenue && ` · 營收 ${researchMetric(group.revenue)}`}{group.profit && ` · 損益 ${researchMetric(group.profit)}`}</strong><span>{group.products?.map((product) => product.lifecycle ? `${product.name}（${product.lifecycle}）` : product.name).filter(Boolean).join("、") || group.applications?.join("、") || "產品資訊未提供"}</span>{group.products?.some((product) => product.specification || product.generation || product.qualificationStatus || product.contributionTimeline) && <small>{group.products.map((product) => [product.specification, product.generation, product.qualificationStatus, product.contributionTimeline].filter(Boolean).join(" · ")).filter(Boolean).join("；")}</small>}</div>)}
            </div> : null}
            {data?.investmentThemes?.length ? <div className="tp-company-research-themes">
              {data.investmentThemes.map((theme) => <article key={theme.themeTitle}><div><strong>{theme.themeTitle}</strong>{theme.timeHorizon && <span>{theme.timeHorizon}</span>}</div>{theme.opportunity?.summary && <p><b>機會</b>{theme.opportunity.summary}</p>}{theme.risk?.summary && <p><b>風險</b>{theme.risk.summary}</p>}</article>)}
            </div> : null}
            {(finance?.forecast || finance?.valuation || annualSnapshot) && <dl className="tp-company-research-metrics">
              {finance?.forecast?.forwardEps !== null && finance?.forecast?.forwardEps !== undefined && <div><dt>預估 Forward EPS</dt><dd>{researchMetric({ value: finance.forecast.forwardEps, unit: finance.forecast.unit, statusNote: finance.forecast.statusNote })}</dd></div>}
              {finance?.valuation?.valuationStatus && <div><dt>估值判讀</dt><dd>{finance.valuation.valuationStatus}</dd></div>}
              {finance?.valuation?.peBands?.fair !== null && finance?.valuation?.peBands?.fair !== undefined && <div><dt>合理價參考</dt><dd>{displayNumber(finance.valuation.peBands.fair)}</dd></div>}
              {annualSnapshot?.revenue !== null && annualSnapshot?.revenue !== undefined && <div><dt>{annualSnapshot.period ?? "年度"}營收</dt><dd>{researchMetric({ value: annualSnapshot.revenue, unit: annualSnapshot.unit, statusNote: annualSnapshot.statusNote ?? null })}</dd></div>}
              {annualSnapshot?.operatingIncome !== null && annualSnapshot?.operatingIncome !== undefined && <div><dt>營業利益</dt><dd>{researchMetric({ value: annualSnapshot.operatingIncome, unit: annualSnapshot.unit, statusNote: annualSnapshot.statusNote ?? null })}</dd></div>}
            </dl>}
            {historicalRows.length ? <div className="tp-company-research-table-wrap"><table className="tp-company-research-table"><thead><tr>{historicalHeaders.map((header) => <th key={header.key ?? header.label}>{header.label ?? "—"}</th>)}</tr></thead><tbody>{historicalRows.map((row) => <tr key={row.metricKey ?? row.label}>{historicalHeaders.map((header) => <td key={`${row.metricKey}-${header.key}`}>{header.key === "metric" ? row.label ?? "—" : displayNumber(row.values[header.key ?? ""])}{header.key === "metric" ? "" : researchUnit(row.unit)}</td>)}</tr>)}</tbody></table>{historical?.unitNote && <small>{historical.unitNote}</small>}</div> : null}
            {segments.length ? <div className="tp-company-research-list" aria-label="分部績效">{segments.map((segment) => <div key={segment.segmentName}><strong>{segment.segmentName}</strong><span className={segment.isNegative ? "is-negative" : ""}>{segment.metricValue === null ? "—" : `${displayNumber(segment.metricValue)}${researchUnit(segment.unit)}`}</span></div>)}</div> : null}
            {data?.limitationsZhTw?.length ? <p className="tp-company-research-limitations">{data.limitationsZhTw.join("；")}</p> : null}
          </div>}
  </section>;
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

export function StockEncyclopediaDrawer({ stock, onClose, presentation = "overlay", isClosing = false }: { stock: StockDrawerItem; onClose: () => void; presentation?: "overlay" | "inline" | "push"; isClosing?: boolean }) {
  const { isFavorite, toggle: toggleFavorite } = useFavoritesState();
  const [formalDetailState, setFormalDetailState] = useState<{ symbol: string; data: StockApiItem | null; status: "available" | "unavailable"; error: string | null } | null>(null);
  const [researchState, setResearchState] = useState<{ symbol: string; data: CompanyResearchV4 | null; status: "available" | "unavailable"; error: string | null } | null>(null);

  useEffect(() => {
    let active = true;
    if (stock.isPreview === true) {
      return () => { active = false; };
    }
    fetchFormalStock(stock.code).then((result) => {
      if (!active) return;
      if (result.source === "api" && result.data) {
        setFormalDetailState({ symbol: stock.code, data: result.data, status: "available", error: null });
      } else {
        setFormalDetailState({ symbol: stock.code, data: null, status: "unavailable", error: result.error });
      }
    });
    return () => { active = false; };
  }, [stock.code, stock.isPreview]);

  useEffect(() => {
    let active = true;
    if (stock.isPreview === true) return () => { active = false; };
    fetchFormalCompanyResearchV4(stock.code).then((result) => {
      if (!active) return;
      setResearchState({
        symbol: stock.code,
        data: result.data,
        status: result.source === "api" ? "available" : "unavailable",
        error: result.error,
      });
    });
    return () => { active = false; };
  }, [stock.code, stock.isPreview]);

  const formalDetail = formalDetailState?.symbol === stock.code ? formalDetailState.data : null;
  const detailState = stock.isPreview === true ? "idle" : formalDetailState?.symbol === stock.code ? formalDetailState.status : "loading";
  const detailError = formalDetailState?.symbol === stock.code ? formalDetailState.error : null;
  const researchDetail = researchState?.symbol === stock.code ? researchState.data : null;
  const researchStatus = stock.isPreview === true ? "unavailable" : researchState?.symbol === stock.code ? researchState.status : "loading";
  const researchError = researchState?.symbol === stock.code ? researchState.error : null;
  const displayStock = formalDetail ? formalDrawerItem(stock, formalDetail) : stock;
  const quote = selectStockQuote(displayStock);
  const tone = quote.changePct === null ? "flat" : quote.changePct >= 0 ? "up" : "down";
  const eodStatus = displayStock.isPreview ? "PREVIEW" : displayStock.eod?.dataStatus ?? "UNAVAILABLE";
  const technical = displayStock.technicalEvidence;
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
    <div className="tp-stock-encyclopedia-body">
      <StockPriceHistoryPanel symbol={displayStock.code} market={displayStock.market} isPreview={displayStock.isPreview === true} />
      <div className="tp-stock-encyclopedia-freshness"><Freshness state={fresh(displayStock.dataFreshness)} asOf={displayStock.updatedAt ?? displayStock.dataDate ?? "資料日期待補"} />{displayStock.isPreview && <span className="tp-stock-preview-label">Preview</span>}{detailState === "loading" && <span className="tp-muted">正在讀取正式 detail</span>}{detailState === "unavailable" && !displayStock.isPreview && <span className="tp-muted">正式 detail 暫不可用</span>}</div>
      {detailError && !displayStock.isPreview && <p className="tp-stock-encyclopedia-muted">{detailError}</p>}
      <div className="tp-stock-encyclopedia-price"><strong>{quote.price === null ? "—" : quote.price.toLocaleString("zh-TW", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>{quote.changePct === null ? <span className="tp-muted">漲跌資料待更新</span> : <span className={`tp-topic-change tp-topic-change--${tone}`}>{displayPercent(quote.changePct)}</span>}</div>
      <section className="tp-stock-encyclopedia-section tp-stock-eod-read" data-eod-status={eodStatus} aria-label="正式 EOD 資料"><div className="tp-stock-encyclopedia-section-heading"><h3>EOD 行情</h3><span>{statusLabel(eodStatus)}</span></div>{displayStock.eod && !displayStock.isPreview ? <><EvidenceGrid rows={[["收盤價", displayNumber(displayStock.eod.close)], ["前收", displayNumber(displayStock.eod.previousClose)], ["漲跌", displaySigned(displayStock.eod.change)], ["漲跌幅", displayPercent(displayStock.eod.changePct)], ["開盤", displayNumber(displayStock.eod.open)], ["最高", displayNumber(displayStock.eod.high)], ["最低", displayNumber(displayStock.eod.low)], ["成交量", displayNumber(displayStock.eod.volume)], ["成交金額", displayNumber(displayStock.eod.turnover)], ["交易日", displayStock.eod.tradingDate]]} /><div className="tp-stock-eod-lineage"><span>價格來源：{sourceLabel(displayStock.eod.priceSource)}</span><span>成交量來源：{sourceLabel(displayStock.eod.volumeSource)}</span><span>除權息：{displayStock.eod.adjustmentState}</span><span>觀測：{displayStock.eod.observedAt ?? "尚未提供"}</span><span>讀取：{displayStock.eod.retrievedAt ?? "尚未提供"}</span></div></> : <p className="tp-stock-encyclopedia-muted">{displayStock.isPreview ? "Preview 不代表正式 EOD；正式 API 可用後才顯示。" : "正式 EOD 尚未提供；不以盤中值、歷史資料或 Preview 補值。"}</p>}</section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>股票身份</h3><span>{displayStock.listing ?? displayStock.industry ?? "正式欄位待補"}</span></div><EvidenceGrid rows={[["市場", displayStock.market], ["交易所", displayStock.exchange], ["產業／類別", displayStock.industry], ["資料日期", displayStock.dataDate]]} /></section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>題材歸屬</h3><span>{displayStock.topics.length} 個關係</span></div>{displayStock.topics.length ? <div className="tp-stock-encyclopedia-topics">{displayStock.topics.map((topic) => <div className="tp-stock-encyclopedia-topic" key={`${topic.name}-${topic.role ?? "unknown"}`}><strong>{topic.name}</strong><RoleChip>{label(topic.role)}</RoleChip></div>)}</div> : <p className="tp-stock-encyclopedia-muted">正式題材關係尚未提供</p>}</section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>主要題材</h3><span>正式欄位優先</span></div>{displayStock.mainTopic ? <div className="tp-stock-encyclopedia-main-topic"><div><strong>{displayStock.mainTopic.name}</strong><p>{displayStock.mainTopic.state ?? "狀態尚未提供"}{displayStock.mainTopic.lifecycle ? ` · ${displayStock.mainTopic.lifecycle}` : ""}</p></div>{displayStock.mainTopic.grade && <RoleChip>{displayStock.mainTopic.grade}</RoleChip>}</div> : <p className="tp-stock-encyclopedia-muted">正式主題欄位尚未提供</p>}</section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>摘要</h3><span>正式 read model</span></div><p className="tp-stock-encyclopedia-muted">{displayStock.summary ?? "正式摘要尚未提供；未由前端生成。"}</p></section>
      {!displayStock.isPreview && <CompanyResearchSection data={researchDetail} loading={researchStatus === "loading"} error={researchError} />}
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>技術證據</h3><span>20MA / 60MA</span></div>{technical ? <EvidenceGrid rows={[["站上 20MA", technical.above20MA], ["站上 60MA", technical.above60MA], ["20MA", technical.ma20], ["60MA", technical.ma60], ["突破狀態", technical.breakoutState], ["技術狀態", technical.technicalState]]} /> : <p className="tp-stock-encyclopedia-muted">正式 technical read model 尚未提供</p>}</section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>法人流向</h3><span>provider evidence</span></div>{institutionEntries.length ? <EvidenceGrid rows={institutionEntries.map(([key, value]) => [key, typeof value === "object" ? JSON.stringify(value) : value as string | number | boolean])} /> : <p className="tp-stock-encyclopedia-muted">正式法人資料尚未提供</p>}</section>
      <div className="tp-stock-encyclopedia-note">{displayStock.isPreview ? "此區塊目前為 Preview；正式 API 可用時才顯示正式欄位。" : "沒有正式 evidence 的欄位保持尚未提供，不由前端推導。"}</div>
      {displayStock.opportunity ? <Link href="/opportunities" className="tp-button tp-button--secondary tp-stock-encyclopedia-cta">進入機會頁</Link> : <span className="tp-button tp-button--secondary tp-stock-encyclopedia-cta" aria-disabled="true">機會資料尚未提供</span>}
    </div>
  </aside>;
  return presentation === "inline" || presentation === "push" ? drawer : <div className="tp-stock-encyclopedia-layer" role="presentation" onClick={onClose}>{drawer}</div>;
}
