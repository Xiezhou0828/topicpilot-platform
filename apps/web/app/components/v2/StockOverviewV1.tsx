"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  fetchFormalStockHistory,
  type StockApiItem,
  type StockHistoryPoint,
  type StockHistoryRead,
} from "../../lib/stock-api";
import type { StockTechnicalPublicationRead } from "../../lib/stock-api";
import type { StockView } from "../../lib/types";

type Period = "1M" | "3M" | "6M" | "1Y";
type HistoryStatus = "LOADING" | "AVAILABLE" | "EMPTY" | "UNAVAILABLE" | "ERROR";

export type OverviewTopic = {
  name: string;
  href: string | null;
  role: string | null;
  weight: number | null;
};

type StockOverviewV1Props = {
  symbol: string;
  formal: StockApiItem | null;
  preview: StockView | null;
  technical: StockTechnicalPublicationRead | null;
  topics: OverviewTopic[];
  onOpenTechnical: () => void;
  onOpenTopics: () => void;
};

type HistoryState = {
  status: HistoryStatus;
  data: StockHistoryRead | null;
  error: string | null;
};

const PERIODS: Array<{ id: Period; label: string; months: number }> = [
  { id: "1M", label: "1 個月", months: 1 },
  { id: "3M", label: "3 個月", months: 3 },
  { id: "6M", label: "6 個月", months: 6 },
  { id: "1Y", label: "1 年", months: 12 },
];

const EMPTY_VALUE = "尚未提供";

function formatNumber(value: number | null | undefined, digits = 2): string {
  return typeof value === "number"
    ? value.toLocaleString("zh-TW", { minimumFractionDigits: digits, maximumFractionDigits: digits })
    : EMPTY_VALUE;
}

function formatPercent(value: number | null | undefined): string {
  return typeof value === "number" ? `${value >= 0 ? "+" : ""}${value.toFixed(2)}%` : EMPTY_VALUE;
}

function formatDate(value: string | null | undefined): string {
  if (!value) return EMPTY_VALUE;
  return value.slice(0, 10);
}

function translateState(value: string | null | undefined): string {
  if (!value) return EMPTY_VALUE;
  const labels: Record<string, string> = {
    ABOVE_MA20: "位於月線之上",
    BELOW_MA20: "位於月線之下",
    ABOVE_MA60: "位於季線之上",
    BELOW_MA60: "位於季線之下",
    BULLISH: "偏多結構",
    BEARISH: "偏弱結構",
    NEUTRAL: "中性",
    STRONG: "偏強",
    WEAK: "偏弱",
    NORMAL: "正常",
    HIGH: "偏高",
    LOW: "偏低",
    RISING: "上升",
    FALLING: "下降",
    FLAT: "持平",
  };
  return labels[value.trim().toUpperCase()] ?? value;
}

function translateReason(value: string | null | undefined): string {
  if (!value) return EMPTY_VALUE;
  const normalized = value.trim().toUpperCase();
  const insufficient = normalized.match(/^INSUFFICIENT_ACCEPTED_PRICE_HISTORY:(\d+)\/(\d+)$/);
  if (insufficient) return `歷史價格資料目前不足（已接受 ${insufficient[1]}／${insufficient[2]} 筆）`;
  if (normalized === "EVENT_LOOKUP_UNAVAILABLE") return "事件查核資料暫不可用";
  if (normalized === "NO_FORMAL_SIGNAL") return "目前沒有正式訊號摘要";
  return value;
}

function historyStatus(data: StockHistoryRead): HistoryStatus {
  return data.items.some((item) => item.close !== null) && data.coverageState !== "EMPTY" ? "AVAILABLE" : "EMPTY";
}

function distinctTradingDays(items: StockHistoryPoint[]): StockHistoryPoint[] {
  const byDate = new Map<string, StockHistoryPoint>();
  for (const item of items) {
    if (item.close === null || byDate.has(item.tradingDate)) continue;
    byDate.set(item.tradingDate, item);
  }
  return [...byDate.values()].sort((left, right) => left.tradingDate.localeCompare(right.tradingDate));
}

function periodItems(data: StockHistoryRead | null, period: Period): StockHistoryPoint[] {
  if (!data) return [];
  const points = distinctTradingDays(data.items);
  const config = PERIODS.find((item) => item.id === period) ?? PERIODS[1];
  const anchor = points.at(-1)?.tradingDate;
  if (!anchor) return points;
  const start = new Date(`${anchor}T00:00:00Z`);
  start.setUTCMonth(start.getUTCMonth() - config.months);
  const from = start.toISOString().slice(0, 10);
  return points.filter((item) => item.tradingDate >= from);
}

function SectionHeading({ title, note, action }: { title: string; note?: string; action?: ReactNode }) {
  return <div className="tp-overview-v1-heading"><div><h2>{title}</h2>{note ? <span>{note}</span> : null}</div>{action}</div>;
}

function Missing({ title, description }: { title: string; description: string }) {
  return <div className="tp-overview-v1-missing"><strong>{title}</strong><p>{description}</p></div>;
}

function SignalOverview({ preview, formal }: { preview: StockView | null; formal: StockApiItem | null }) {
  const signals = [
    preview?.technicalSubtype ? { label: "技術型態", value: translateState(preview.technicalSubtype) } : null,
    preview?.volumeStatus ? { label: "成交量狀態", value: translateState(preview.volumeStatus) } : null,
    formal?.trackingReason ? { label: "訊號可用性", value: translateReason(formal.trackingReason) } : null,
  ].filter((item): item is { label: string; value: string } => Boolean(item));

  return <section className="tp-overview-v1-section tp-overview-v1-signals" aria-labelledby="stock-overview-signals-title">
    <SectionHeading title="近期訊號" note="只呈現已由後端提供的狀態" />
    {signals.length ? <div className="tp-overview-v1-signal-grid">{signals.slice(0, 3).map((signal) => <div className="tp-overview-v1-signal" key={signal.label}><span>{signal.label}</span><strong>{signal.value}</strong></div>)}</div> : <Missing title="近期訊號尚未提供" description="目前沒有可供此頁呈現的正式訊號摘要。" />}
  </section>;
}

function PriceChart({ symbol, market }: { symbol: string; market: string | null }) {
  const [period, setPeriod] = useState<Period>("3M");
  const [showMa20, setShowMa20] = useState(false);
  const [state, setState] = useState<HistoryState>({ status: "LOADING", data: null, error: null });
  const [activePoint, setActivePoint] = useState<StockHistoryPoint | null>(null);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const today = new Date();
    const from = new Date(today);
    from.setUTCFullYear(from.getUTCFullYear() - 1);
    void fetchFormalStockHistory(symbol, {
      market,
      from: from.toISOString().slice(0, 10),
      to: today.toISOString().slice(0, 10),
      limit: 200,
      signal: controller.signal,
    }).then((result) => {
      if (!active) return;
      if (result.source === "api" && result.data) {
        setState({ status: historyStatus(result.data), data: result.data, error: null });
      } else {
        setState({ status: result.state ?? "ERROR", data: null, error: result.error });
      }
    });
    return () => {
      active = false;
      controller.abort();
    };
  }, [market, symbol]);

  const points = useMemo(() => periodItems(state.data, period), [period, state.data]);
  const latest = points.at(-1) ?? null;
  const selected = activePoint && points.some((point) => point.tradingDate === activePoint.tradingDate) ? activePoint : latest;
  const chart = useMemo(() => {
    if (!points.length) return null;
    const width = 720;
    const height = 250;
    const left = 16;
    const right = 16;
    const top = 18;
    const bottom = 30;
    const closes = points.map((point) => point.close).filter((value): value is number => typeof value === "number");
    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const span = max - min || Math.max(max * 0.02, 1);
    const x = (index: number) => left + (index / Math.max(points.length - 1, 1)) * (width - left - right);
    const y = (value: number) => top + (1 - (value - min) / span) * (height - top - bottom);
    return { width, height, points: points.map((point, index) => ({ point, x: x(index), y: y(point.close ?? min) })), min, max };
  }, [points]);

  return <section className="tp-overview-v1-section tp-overview-v1-price" aria-labelledby="stock-overview-price-title">
    <SectionHeading title="股價走勢" note={latest ? `最新交易日 ${formatDate(latest.tradingDate)}` : "資料待補"} action={<div className="tp-overview-v1-periods" role="group" aria-label="股價期間">{PERIODS.map((item) => <button key={item.id} type="button" className={period === item.id ? "is-active" : ""} onClick={() => { setPeriod(item.id); setActivePoint(null); }}>{item.label}</button>)}<button type="button" className={showMa20 ? "is-active" : ""} aria-pressed={showMa20} aria-label="切換 MA20" onClick={() => setShowMa20((current) => !current)}>MA20 <small>待正式序列</small></button></div>} />
    {state.status === "LOADING" && <Missing title="正在讀取歷史收盤資料" description="只讀取正式歷史行情，不使用示範資料或前填值。" />}
    {state.status === "UNAVAILABLE" && <Missing title="歷史收盤資料尚未提供" description="目前 Preview 沒有可用的正式歷史行情端點。" />}
    {state.status === "ERROR" && <Missing title="歷史收盤資料讀取失敗" description={state.error ?? "正式資料端點暫時無法回應。"} />}
    {state.status === "EMPTY" && <Missing title="此期間沒有可用的歷史收盤資料" description={state.data?.availabilityReason ?? "資料端點沒有回傳可接受的觀測值。"} />}
    {state.status === "AVAILABLE" && chart ? <>
      <div className="tp-overview-v1-chart-wrap" data-chart-status="real-observed-close">
        <svg className="tp-overview-v1-chart" viewBox={`0 0 ${chart.width} ${chart.height}`} role="img" aria-label={`${symbol} ${period} 實際收盤價走勢`}>
          <line x1="16" x2="704" y1="18" y2="18" className="tp-overview-v1-gridline" />
          <line x1="16" x2="704" y1="128" y2="128" className="tp-overview-v1-gridline" />
          <line x1="16" x2="704" y1="220" y2="220" className="tp-overview-v1-gridline" />
          <polyline points={chart.points.map(({ x, y }) => `${x},${y}`).join(" ")} className="tp-overview-v1-line" fill="none" />
          {chart.points.map(({ point, x, y }) => <circle key={point.tradingDate} cx={x} cy={y} r="4" className="tp-overview-v1-point" tabIndex={0} onMouseEnter={() => setActivePoint(point)} onFocus={() => setActivePoint(point)} onMouseLeave={() => setActivePoint(null)} onBlur={() => setActivePoint(null)}><title>{`${point.tradingDate} 收盤 ${formatNumber(point.close)}`}</title></circle>)}
        </svg>
        <div className="tp-overview-v1-chart-labels"><span>{formatDate(points[0]?.tradingDate)}</span><span>{formatDate(points.at(-1)?.tradingDate)}</span></div>
        {selected ? <div className="tp-overview-v1-tooltip" data-tooltip-date={selected.tradingDate}><span>{formatDate(selected.tradingDate)}</span><strong>{formatNumber(selected.close)}</strong><small>收盤價</small></div> : null}
      </div>
      <div className="tp-overview-v1-chart-meta"><span>已回傳 {points.length} 個實際交易日</span><span>原始收盤價，未套用除權息調整</span>{showMa20 ? <span>正式 MA20 歷史序列尚未發布，未繪製均線</span> : null}{state.data?.hasMore ? <span>結果受端點上限限制</span> : null}</div>
    </> : null}
  </section>;
}

function TechnicalSummary({ formal, preview, onOpenTechnical }: { formal: StockApiItem | null; preview: StockView | null; onOpenTechnical: () => void }) {
  const evidence = formal?.technicalEvidence ?? null;
  const screener = preview?.screener ?? null;
  const rows = [
    { label: "月線位置", value: evidence?.technicalState ?? screener?.structureState, detail: evidence ? `MA20 ${formatNumber(evidence.ma20)} · MA60 ${formatNumber(evidence.ma60)}` : null },
    { label: "均線結構", value: formal?.ma20State ?? screener?.movingAverageAlignment, detail: screener?.ma20SlopePct === null || screener?.ma20SlopePct === undefined ? null : `MA20 斜率 ${formatPercent(screener.ma20SlopePct)}` },
    { label: "相對大盤強弱", value: screener?.rsState, detail: screener ? `5日 ${formatPercent(screener.rs5Pct)} · 20日 ${formatPercent(screener.rs20Pct)}` : null },
    { label: "成交量變化", value: preview?.volumeStatus ?? screener?.volumeStatus, detail: screener?.volumeRatio === null || screener?.volumeRatio === undefined ? null : `量比 ${formatNumber(screener.volumeRatio, 2)}` },
  ];
  return <section className="tp-overview-v1-section tp-overview-v1-technical" aria-labelledby="stock-overview-technical-title">
    <SectionHeading title="技術狀態" note="重用後端已發布欄位" action={<button type="button" className="tp-overview-v1-link" onClick={onOpenTechnical}>查看技術分析 →</button>} />
    <div className="tp-overview-v1-technical-grid">{rows.map((row) => <div className="tp-overview-v1-technical-card" key={row.label}><span>{row.label}</span><strong>{translateState(row.value)}</strong><small>{row.detail ?? "狀態由後端提供；未在瀏覽器重新計算。"}</small></div>)}</div>
  </section>;
}

function TopicsSummary({ topics, onOpenTopics }: { topics: OverviewTopic[]; onOpenTopics: () => void }) {
  return <section className="tp-overview-v1-section tp-overview-v1-topics" aria-labelledby="stock-overview-topics-title">
    <SectionHeading title="正式題材概況" note="只顯示目前正式題材權威關聯" action={<button type="button" className="tp-overview-v1-link" onClick={onOpenTopics}>查看全部 →</button>} />
    {topics.length ? <div className="tp-overview-v1-topic-list">{topics.slice(0, 6).map((topic) => topic.href ? <Link href={topic.href} key={`${topic.name}-${topic.role}`}><strong>{topic.name}</strong><span>{topic.role ?? "正式關聯"}</span></Link> : <div key={`${topic.name}-${topic.role}`}><strong>{topic.name}</strong><span>{topic.role ?? "正式關聯"}</span></div>)}</div> : <Missing title="正式題材資料尚未提供" description="此區不使用 AI 推導或研究建議補入正式題材。" />}
  </section>;
}

function InstitutionalSummary({ preview }: { preview: StockView | null }) {
  const screener = preview?.screener ?? null;
  const values = [
    { label: "外資連續買超", value: typeof screener?.foreignBuyStreakDays === "number" ? `${screener.foreignBuyStreakDays} 日` : null },
    { label: "投信連續買超", value: typeof screener?.trustBuyStreakDays === "number" ? `${screener.trustBuyStreakDays} 日` : null },
    { label: "法人同步狀態", value: typeof screener?.institutionsInSync === "boolean" ? (screener.institutionsInSync ? "同步" : "未同步") : null },
    { label: "資料日期", value: screener?.institutionalAsOf ?? null },
  ].filter((item): item is { label: string; value: string } => Boolean(item.value));
  return <section className="tp-overview-v1-section tp-overview-v1-institutional" aria-labelledby="stock-overview-institutional-title">
    <SectionHeading title="法人摘要" note="不以缺資料推導法人方向" />
    {values.length ? <div className="tp-overview-v1-institutional-grid">{values.map((item) => <div key={item.label}><span>{item.label}</span><strong>{item.value}</strong></div>)}</div> : <Missing title="法人摘要尚未提供" description="目前沒有可供此頁呈現的正式個股法人資料，暫不顯示推測數字。" />}
  </section>;
}

export function StockOverviewV1({ symbol, formal, preview, technical, topics, onOpenTechnical, onOpenTopics }: StockOverviewV1Props) {
  return <div className="tp-overview-v1" data-overview-version="v1" data-technical-publication={technical?.publicationState ?? "UNAVAILABLE"}>
    <SignalOverview preview={preview} formal={formal} />
    <div className="tp-overview-v1-main-grid"><PriceChart symbol={symbol} market={formal?.market ?? null} /><TechnicalSummary formal={formal} preview={preview} onOpenTechnical={onOpenTechnical} /></div>
    <div className="tp-overview-v1-lower-grid"><TopicsSummary topics={topics} onOpenTopics={onOpenTopics} /><InstitutionalSummary preview={preview} /></div>
    <p className="tp-overview-v1-disclosure">行情線圖來自正式歷史觀測；未填補缺漏、未套用除權息調整。題材區僅呈現目前正式關聯，研究建議不會自動轉成正式題材。</p>
  </div>;
}

