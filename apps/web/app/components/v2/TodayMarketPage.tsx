"use client";

import Link from "next/link";
import {
  ArrowDown,
  ArrowUp,
  BarChart3,
  CalendarDays,
  ChevronRight,
  Coins,
  Info,
  Landmark,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useState } from "react";
import {
  useTodayMainlines,
  type TodayMarketOverviewResource,
  type TodayOpportunityResource,
  type TodayRotationResource,
  type TodaySectionState,
} from "../../lib/today-mainlines";
import {
  formatMarketAsOf,
  formatMarketDate,
  formatMarketDistributionLabel,
  formatMarketNumber,
  formatMarketPercent as formatMarketPercentValue,
  formatSignedMarketNumber,
  formatTurnoverHundredMillion,
  formatTurnoverHundredMillionValue,
  marketDistribution,
  marketFactIsAvailable,
  marketIndices,
  marketTurnover,
} from "../../lib/today-market-fields";
import { commercialStateLabel } from "../../lib/commercial-state.mjs";
import { Card, GradeChip, PageContainer } from "./V2Foundation";

function formatMarketPercent(value: unknown): string {
  return formatMarketPercentValue(typeof value === "number" ? value : null);
}

type TodayDisclosureResource = {
  state: TodaySectionState;
  dataDate: string | null;
  generatedAt: string | null;
  latestSnapshotTime: string | null;
  asOf: string | null;
  source: string | null;
  temporarySections: string[];
  missingSections: string[];
  qualityNotes: string[];
  sectionStatus?: { status: string; dataDate: string | null; asOf: string | null; source?: string | null } | null;
};

function stateLabel(state: TodaySectionState | "LOADING"): string {
  return {
    LOADING: "讀取中",
    FORMAL: "已發布",
    TEMPORARY: "暫時資料",
    PREVIEW: "預覽資料",
    UNAVAILABLE: "尚未提供",
    ERROR: "讀取失敗",
    EMPTY: "目前沒有結果",
    PARTIAL: "部分資料",
    STALE: "資料日期較早",
    NOT_APPLICABLE: "不適用",
  }[state] ?? commercialStateLabel(state);
}

function MainlinesState({ loading, state, reason, dataDate, section }: { loading: boolean; state: TodaySectionState; reason: string | null; dataDate: string | null; section: string }) {
  const effectiveState = loading ? "LOADING" : state;
  const isError = effectiveState === "ERROR";
  return <div className={`tp-home-mainlines-state tp-home-mainlines-state--${effectiveState.toLowerCase()}`} role={isError ? "alert" : "status"}><span className="tp-data-state">{stateLabel(effectiveState)}</span><p>{loading ? `正在讀取${section}。` : reason ?? `${section}目前尚未提供。`}</p>{dataDate && <small>資料日：{formatMarketDate(dataDate)}</small>}</div>;
}

function friendlySourceName(value: string | null): string {
  if (!value) return "尚未提供";
  const normalized = value.trim().toUpperCase();
  if (normalized.includes("TWSE")) return "TWSE 正式來源";
  if (normalized.includes("TPEX")) return "TPEx 正式來源";
  if (normalized.includes("HOME") || normalized.includes("POSTGRES")) return "TopicPilot 正式資料來源";
  return "正式資料來源";
}

function CompactDisclosure({ loading, resource, sectionKey, sectionLabel }: { loading: boolean; resource: TodayDisclosureResource; sectionKey: string; sectionLabel: string }) {
  const effectiveState = loading ? "LOADING" : resource.state;
  const notes = [resource.temporarySections.includes(sectionKey) ? `${sectionLabel}目前為暫時資料。` : null, resource.missingSections.includes(sectionKey) ? `${sectionLabel}目前尚未完成發布。` : null, ...resource.qualityNotes.filter((note) => !/public\.|ingestion|Home\.|backend|postgres/i.test(note)).map((note) => `資料提示：${note}`)].filter((value): value is string => Boolean(value));
  return <details className="tp-home-compact-disclosure"><summary><Info size={13} aria-hidden="true" /><span>{resource.asOf ? `資料截至 ${formatMarketAsOf(resource.asOf)}` : "資料截至尚未提供"}</span><span>{stateLabel(effectiveState)}</span></summary><div className="tp-home-compact-disclosure-body"><span>發布狀態：{resource.sectionStatus?.status ?? (effectiveState === "FORMAL" ? "AVAILABLE" : "尚未提供")}</span><span>來源：{friendlySourceName(resource.sectionStatus?.source ?? resource.source)}</span>{notes.map((note) => <span key={note}>{note}</span>)}</div></details>;
}

function SectionHeading({ id, eyebrow, title, description, link, trailing }: { id?: string; eyebrow?: string; title: string; description?: string; link?: { label: string; href: string }; trailing?: React.ReactNode }) {
  return <div className="tp-home-section-heading"><div>{eyebrow && <p className="tp-overline">{eyebrow}</p>}<h2 id={id}>{title}</h2>{description && <p>{description}</p>}</div>{(trailing || link) && <div className="tp-home-section-heading-actions">{trailing}{link && <Link className="tp-home-section-link" href={link.href}>{link.label}<ChevronRight size={16} aria-hidden="true" /></Link>}</div>}</div>;
}

function DatePanel({ dataDate, updatedAt }: { dataDate: string | null; updatedAt: string | null }) {
  return <div className="tp-home-date-panel"><CalendarDays size={22} aria-hidden="true" /><div><strong>{dataDate ? `${formatMarketDate(dataDate)}（收盤）` : "資料日尚未提供"}</strong><span>收盤後 · 資料更新時間：{updatedAt ? formatMarketAsOf(updatedAt) : "尚未提供"}</span></div><Info size={18} aria-hidden="true" /></div>;
}

function IndexFactCard({ label, market, value, open, high, low, change, changePct, status }: { label: string; market: string; value: number | null; open?: number | null; high?: number | null; low?: number | null; change: number | null; changePct: number | null; status: string }) {
  const available = marketFactIsAvailable(status, value);
  const ohlcAvailable = available && [open, high, low].every((item) => typeof item === "number" && Number.isFinite(item));
  const direction = typeof change === "number" && change > 0 ? "up" : typeof change === "number" && change < 0 ? "down" : "flat";
  return <article data-market={market} className={`tp-home-target-fact-card tp-home-target-index-card tp-home-target-${direction}${ohlcAvailable ? "" : " tp-home-target-index-card--compact"}`}><div className="tp-home-target-card-title"><strong>{label}</strong></div><strong className="tp-home-target-index-value">{available ? formatMarketNumber(value) : "尚未提供"}</strong><span className="tp-home-target-index-change" aria-label={available && change !== null ? `漲跌 ${formatSignedMarketNumber(change)} 點${changePct !== null ? `，${formatMarketPercent(changePct)}` : ""}` : "漲跌點尚未提供"}>{available && change !== null ? `${change > 0 ? "▲" : change < 0 ? "▼" : "—"} ${formatSignedMarketNumber(change)} 點` : "漲跌點尚未提供"}{available && changePct !== null && ` · ${formatMarketPercent(changePct)}`}</span>{ohlcAvailable && <div className="tp-home-target-index-stats" aria-label={`${label}日內 OHLC`}><div><span>開盤</span><strong>{formatMarketNumber(open)}</strong></div><div><span>最高</span><strong>{formatMarketNumber(high)}</strong></div><div><span>最低</span><strong>{formatMarketNumber(low)}</strong></div></div>}</article>;
}

function TurnoverFactCard({ overview }: { overview: NonNullable<TodayMarketOverviewResource["data"]> }) {
  const turnoverByMarket = new Map(marketTurnover(overview).map((fact) => [fact.market, fact]));
  const total = turnoverByMarket.get("TOTAL");
  const comparison = total?.previousSession;
  const comparisonAvailable = comparison?.status === "AVAILABLE";
  const comparisonTone = typeof comparison?.absoluteChange === "number" && comparison.absoluteChange > 0 ? "is-up" : typeof comparison?.absoluteChange === "number" && comparison.absoluteChange < 0 ? "is-down" : "is-flat";
  return <article className="tp-home-target-fact-card tp-home-target-turnover-card"><div className="tp-home-target-card-title"><strong>成交金額</strong><span><Coins size={18} aria-hidden="true" /> 新台幣</span></div><div className="tp-home-target-turnover-main"><strong>{total ? formatTurnoverHundredMillion(total) : "尚未提供"}</strong><span>總成交金額</span></div><div className="tp-home-target-turnover-rows"><div><span>上市</span><strong>{turnoverByMarket.get("TPE") ? formatTurnoverHundredMillion(turnoverByMarket.get("TPE")!) : "尚未提供"}</strong></div><div><span>上櫃</span><strong>{turnoverByMarket.get("TWO") ? formatTurnoverHundredMillion(turnoverByMarket.get("TWO")!) : "尚未提供"}</strong></div></div><div className={`tp-home-target-turnover-compare ${comparisonAvailable ? comparisonTone : "is-unavailable"}`} aria-label="較前一交易日成交金額變化"><span>較前一交易日</span><strong>{comparisonAvailable ? formatTurnoverHundredMillionValue(comparison.absoluteChange, comparison.currency, comparison.unit, comparison.status) : "尚未提供"}</strong><b>{comparisonAvailable && typeof comparison.changePct === "number" ? `${comparison.changePct > 0 ? "+" : ""}${comparison.changePct.toFixed(2)}%` : "百分比尚未提供"}</b><small>{comparisonAvailable ? `前一交易日總成交 ${formatTurnoverHundredMillionValue(comparison.value, comparison.currency, comparison.unit, comparison.status)} · ${formatMarketDate(comparison.tradingDate)}` : "前一交易日正式成交金額尚未提供"}</small></div></article>;
}

function InstitutionalFactCard({ overview }: { overview: NonNullable<TodayMarketOverviewResource["data"]> }) {
  const flow = overview.institutionFlows;
  const values = flow?.aggregate;
  const rows = [["外資", values?.foreign?.net], ["投信", values?.investmentTrust?.net], ["自營商", values?.dealer?.net], ["三大法人合計", values?.total?.net]] as const;
  const combinedAvailable = flow?.status === "AVAILABLE" && Boolean(values);
  const numericValue = (value: unknown): number | null => {
    const parsed = typeof value === "number" ? value : typeof value === "string" ? Number(value) : null;
    return parsed !== null && Number.isFinite(parsed) ? parsed : null;
  };
  const valueTone = (value: unknown): string => {
    const numeric = numericValue(value);
    return numeric === null ? "is-unavailable" : numeric > 0 ? "is-up" : numeric < 0 ? "is-down" : "is-flat";
  };
  return <article className="tp-home-target-fact-card tp-home-target-institution-card"><div className="tp-home-target-card-title"><strong>三大法人買賣超</strong><Landmark size={22} aria-hidden="true" /></div><div className="tp-home-target-institution-rows">{rows.map(([label, value]) => <div key={label}><span>{label}</span><strong className={valueTone(value)}>{combinedAvailable ? formatSignedMarketNumber(numericValue(value)) : "尚未提供"}</strong></div>)}</div>{combinedAvailable ? <small className="tp-home-target-flow-meta">上市＋上櫃合計 · {flow?.unit ?? "TWD"} · 資料日 {formatMarketDate(flow?.asOfDate)}</small> : <small className="tp-home-target-unavailable-note">正式法人資料尚未提供，不以單一市場或 0 代替。</small>}</article>;
}

function DistributionCard({ overview }: { overview: NonNullable<TodayMarketOverviewResource["data"]> }) {
  const distribution = marketDistribution(overview);
  const available = distribution?.status === "AVAILABLE" && distribution.eligible > 0;
  const coverage = distribution?.coverage ?? {};
  const distributionUniverse = typeof coverage.universeLabel === "string" ? coverage.universeLabel : typeof coverage.denominator === "string" ? coverage.denominator : "正式分布統計範圍尚未提供";
  const maxPercentage = available ? Math.max(...(distribution.buckets ?? []).map((bucket) => bucket.percentage ?? 0), 1) : 1;
  return <article aria-label="漲跌幅分布與市場廣度" className="tp-home-target-distribution-card"><div className="tp-home-target-subheading"><div><h3>漲跌幅分布（上市＋上櫃）</h3><span className="tp-home-target-helper">完整收盤／前收資料 · 排除未成交或缺值</span></div><span className="tp-home-target-info" title={distributionUniverse} aria-label={`分布統計範圍：${distributionUniverse}`}><Info size={17} aria-hidden="true" /></span>{available && <strong>總家數 {formatMarketNumber(distribution.eligible)}</strong>}</div>{available ? <div className="tp-home-target-bars">{(distribution.buckets ?? []).map((bucket) => <div className="tp-home-target-bar-item" key={bucket.key}><strong className="tp-home-target-bar-count">{formatMarketNumber(bucket.count)}</strong><i aria-hidden="true" style={{ height: `${Math.max(5, Math.round(((bucket.percentage ?? 0) / maxPercentage) * 62))}px` }} /><span className="tp-home-target-bar-label" title={bucket.label}>{formatMarketDistributionLabel(bucket.key, bucket.label)}</span></div>)}</div> : <div className="tp-home-target-empty">正式漲跌幅分布目前尚未提供。</div>}</article>;
}

function BreadthCard({ overview }: { overview: NonNullable<TodayMarketOverviewResource["data"]> }) {
  const health = overview.marketHealth;
  const breadthCoverage = (overview.breadth ?? []).find((item) => item.coverage?.universeLabel || item.coverage?.denominator)?.coverage ?? {};
  const breadthUniverse = typeof breadthCoverage.universeLabel === "string" ? breadthCoverage.universeLabel : typeof breadthCoverage.denominator === "string" ? breadthCoverage.denominator : "正式廣度統計範圍尚未提供";
  const advance = health && health.advance;
  const decline = health && health.decline;
  const flat = health && health.flat;
  const total = typeof health?.breadthEligible === "number" ? health.breadthEligible : advance !== null && decline !== null && flat !== null ? (advance ?? 0) + (decline ?? 0) + (flat ?? 0) : null;
  return <article className="tp-home-target-breadth-card"><div className="tp-home-target-subheading"><div><h3>市場廣度</h3><span className="tp-home-target-helper">官方全市場廣度彙總</span></div><span className="tp-home-target-info" title={breadthUniverse} aria-label={`廣度統計範圍：${breadthUniverse}`}><Info size={17} aria-hidden="true" /></span></div><div className="tp-home-target-breadth-rows"><div className="up"><ArrowUp size={20} aria-hidden="true" /><span>上漲家數</span><strong>{advance ?? "尚未提供"}</strong></div><div className="down"><ArrowDown size={20} aria-hidden="true" /><span>下跌家數</span><strong>{decline ?? "尚未提供"}</strong></div><div><span className="tp-home-target-flat-mark">—</span><span>平盤家數</span><strong>{flat ?? "尚未提供"}</strong></div><div className="tp-home-target-breadth-total"><span aria-hidden="true">Σ</span><span>總家數</span><strong>{total ?? "尚未提供"}</strong></div></div></article>;
}

function MarketOverviewCard({ loading, resource }: { loading: boolean; resource: TodayMarketOverviewResource }) {
  const overview = resource.data;
  const indices = overview ? marketIndices(overview) : [];
  const nonFormal = resource.state !== "FORMAL" && resource.state !== "UNAVAILABLE" && resource.state !== "ERROR";
  return <Card className="tp-home-overview-card tp-home-target-overview-card"><div className="tp-home-target-overview-heading"><SectionHeading id="market-overview-title" title="市場概況" description="掌握今日台股整體表現，快速了解市場強弱與資金動向。" />{overview && <DatePanel dataDate={overview.dataDate} updatedAt={overview.updatedAt} />}</div>{loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="市場概況" /> : overview ? <>{nonFormal && <MainlinesState loading={false} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="市場概況" />}<div className="tp-home-target-top-grid"><IndexFactCard label="加權指數 (TPE)" {...(indices.find((index) => index.market === "TPE") ?? { value: null, change: null, changePct: null, status: "UNAVAILABLE" })} market="TPE" /><IndexFactCard label="櫃買指數 (TWO)" {...(indices.find((index) => index.market === "TWO") ?? { value: null, change: null, changePct: null, status: "UNAVAILABLE" })} market="TWO" /><TurnoverFactCard overview={overview} /><InstitutionalFactCard overview={overview} /></div><div className="tp-home-target-bottom-grid"><DistributionCard overview={overview} /><BreadthCard overview={overview} /></div></> : <MainlinesState loading={false} state="UNAVAILABLE" reason="市場資料尚未完整。" dataDate={resource.dataDate} section="市場概況" />}<CompactDisclosure loading={loading} resource={resource} sectionKey="marketOverview" sectionLabel="市場概況" /></Card>;
}

function MarketSignalCards({ loading, resource }: { loading: boolean; resource: ReturnType<typeof useTodayMainlines>["resource"]["dailyFocus"] }) {
  const data = resource.data;
  const signals = (resource.data?.signals ?? []).filter((signal) => signal.isActive !== false);
  const [signalPage, setSignalPage] = useState(0);
  const pageSize = 5;
  const pageCount = Math.max(1, Math.ceil(signals.length / pageSize));
  const safePage = Math.min(signalPage, pageCount - 1);
  const visibleSignals = signals.slice(safePage * pageSize, (safePage + 1) * pageSize);
  // Keep the formal daily-focus fields explicit for the data-owned empty state: data.headline and (data.bullets ?? []).map(...).
  const temporalLabel = (signal: (typeof signals)[number]): string => signal.signalTemporalStatus === "NEW"
    ? "NEW"
    : signal.signalTemporalStatus === "PERSISTING" && signal.streakDays
      ? `延續第 ${signal.streakDays} 日`
      : signal.signalTemporalStatus === "INSUFFICIENT_HISTORY" ? "歷史資料不足" : "今日啟動";
  return <Card className="tp-home-signals-card tp-home-target-signals-card"><div className="tp-home-target-section-title"><div><Target size={28} aria-hidden="true" /><div><h2 id="market-signals-title">今日市場訊號 <Info size={17} aria-hidden="true" /></h2><p>偵測市場異常變化，協助掌握今日值得關注的關鍵訊號。</p></div></div><button type="button" className="tp-home-target-outline-button"><BarChart3 size={17} aria-hidden="true" />查看全部市場訊號<ChevronRight size={16} aria-hidden="true" /></button></div>{loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日市場訊號" /> : signals.length > 0 ? <><div className="tp-home-signal-grid">{visibleSignals.map((signal) => <article className={`tp-home-signal-card tp-home-signal-card--${signal.severity.toLowerCase()}`} key={signal.signalId ?? signal.key}><div className="tp-home-signal-card-heading"><strong>{signal.title ?? signal.name}</strong><b>{temporalLabel(signal)}</b></div><small>{signal.occurrenceDays20d === null || signal.occurrenceDays20d === undefined ? "近20日發生狀態尚未完整" : `近20日發生 ${signal.occurrenceDays20d} 日`}</small><p>{signal.frequencyMessage ?? signal.summary ?? signal.interpretation}</p><ul>{(signal.evidence ?? []).map((item) => <li key={item}>{item}</li>)}</ul></article>)}</div>{signals.length > pageSize && <div className="tp-home-signal-pagination" aria-label="市場訊號翻頁控制"><button type="button" onClick={() => setSignalPage(Math.max(0, safePage - 1))} disabled={safePage === 0} aria-label="上一組市場訊號">上一組</button><span>顯示 {safePage * pageSize + 1}-{Math.min((safePage + 1) * pageSize, signals.length)} / {signals.length}</span><button type="button" onClick={() => setSignalPage(Math.min(pageCount - 1, safePage + 1))} disabled={safePage >= pageCount - 1} aria-label="下一組市場訊號">下一組</button></div>}</> : <div className="tp-home-target-signal-empty"><strong>{data?.headline ?? "今日市場訊號尚未完成。"}</strong>{data ? <ul>{(data.bullets ?? []).map((bullet) => <li key={bullet}>{bullet}</li>)}</ul> : <p>正式訊號依賴資料尚未完整發布。</p>}</div>}<CompactDisclosure loading={loading} resource={resource} sectionKey="dailyFocus" sectionLabel="今日市場訊號" /></Card>;
}

function MainlineCards({ loading, resource }: { loading: boolean; resource: ReturnType<typeof useTodayMainlines>["resource"] }) {
  const score = (value: number | null | undefined): string => value === null || value === undefined ? "—" : formatMarketNumber(value);
  return <section className="tp-home-section tp-home-mainline-section" aria-labelledby="mainline-title"><SectionHeading id="mainline-title" title="今日主線" description="依正式 Lifecycle 與 Topic Strength，挑出今天最值得優先研究的三個題材。" link={{ label: "查看全部題材", href: "/topics" }} />{loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日主線" /> : <div className="tp-home-mainline-grid">{resource.data.map((topic, index) => <article className="tp-home-mainline-card tp-home-target-mainline-card" key={topic.slug}><div className="tp-home-target-mainline-top"><span className="tp-home-target-rank">{index + 1}</span><h3>{topic.name}</h3>{topic.grade && <GradeChip grade={topic.grade} />}<span className="tp-home-topic-lifecycle">{topic.lifecycle ?? "Lifecycle 尚未提供"}</span></div><div className="tp-home-target-mainline-stats"><span>絕對強度 <b>{score(topic.absoluteScore)}</b></span><span>相對強度 <b>{score(topic.relativeScore)}</b></span>{topic.lifecycleCandidate && <span>候選 <b>{topic.lifecycleCandidate}{topic.candidateConfirmation?.current !== undefined && topic.candidateConfirmation?.required !== undefined ? ` · ${topic.candidateConfirmation.current} / ${topic.candidateConfirmation.required}` : ""}</b></span>}</div><p className="tp-home-topic-detail">{topic.summary}</p><Link href={`/topics/${topic.slug}`} className="tp-home-card-action">進入題材頁 <ChevronRight size={16} aria-hidden="true" /></Link></article>)}</div>}<CompactDisclosure loading={loading} resource={resource} sectionKey="mainTopics" sectionLabel="今日主線" /></section>;
}

function TopicPulsePanel({ loading, resource }: { loading: boolean; resource: ReturnType<typeof useTodayMainlines>["resource"] }) {
  const [filter, setFilter] = useState<"ALL" | "CHANGED">("ALL");
  const [page, setPage] = useState(0);
  const events = resource.marketEvents.data;
  const filtered = filter === "CHANGED" ? events.filter((event) => event.changed) : events;
  const pageSize = 8;
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, pageCount - 1);
  const visible = filtered.slice(safePage * pageSize, (safePage + 1) * pageSize);
  const setPulseFilter = (next: "ALL" | "CHANGED") => { setFilter(next); setPage(0); };
  return <section className="tp-home-section" aria-labelledby="topic-pulse-title"><Card className="tp-home-topic-pulse-card"><div className="tp-home-target-ticker-heading"><div><BarChart3 size={23} aria-hidden="true" /><div><h2 id="topic-pulse-title">題材動態快訊</h2><span>完整正式題材宇宙；只呈現今日有意義的狀態變化。</span></div></div><div className="tp-home-topic-pulse-filters" role="group" aria-label="題材動態篩選"><button type="button" aria-pressed={filter === "ALL"} onClick={() => setPulseFilter("ALL")}>全部 ({events.length})</button><button type="button" aria-pressed={filter === "CHANGED"} onClick={() => setPulseFilter("CHANGED")}>有變化 ({events.filter((event) => event.changed).length})</button></div></div>{loading || resource.marketEvents.state === "UNAVAILABLE" || resource.marketEvents.state === "ERROR" || events.length === 0 ? <MainlinesState loading={loading} state={resource.marketEvents.state} reason={resource.marketEvents.reason ?? "今日題材動態尚未提供。"} dataDate={resource.marketEvents.dataDate} section="題材動態" /> : <><div className="tp-home-topic-pulse-grid">{visible.map((event) => <Link className="tp-home-topic-pulse-item" href={`/topics/${event.topicSlug}`} key={event.topicSlug}><span><strong>{event.topic}</strong><small>{event.status === "X_NOT_FOCUS" ? "X／暫不關注" : `${event.dailyGrade ?? "Grade 尚未提供"} · ${event.lifecycle ?? "Lifecycle 尚未提供"}`}</small></span><b>{event.primaryEvent}</b><ChevronRight size={16} aria-hidden="true" /></Link>)}</div><div className="tp-home-topic-pulse-pagination" aria-label="題材動態翻頁控制"><button type="button" onClick={() => setPage(Math.max(0, safePage - 1))} disabled={safePage === 0} aria-label="上一組題材動態">上一組</button><span>顯示 {filtered.length === 0 ? 0 : safePage * pageSize + 1}-{Math.min((safePage + 1) * pageSize, filtered.length)} / {filtered.length} · 第 {safePage + 1} / {pageCount} 頁</span><button type="button" onClick={() => setPage(Math.min(pageCount - 1, safePage + 1))} disabled={safePage >= pageCount - 1} aria-label="下一組題材動態">下一組</button></div></>}<CompactDisclosure loading={loading} resource={resource} sectionKey="marketEvents" sectionLabel="題材動態" /></Card></section>;
}

function RotationCard({ loading, resource, direction }: { loading: boolean; resource: TodayRotationResource; direction: "heating" | "cooling" }) {
  const isHeating = direction === "heating";
  const section = isHeating ? "快速升溫" : "快速退潮";
  const available = resource.state === "FORMAL" || resource.state === "PARTIAL" || resource.state === "STALE";
  return <Card className={`tp-home-rotation-card tp-home-target-rotation-card tp-home-rotation-card--${isHeating ? "warming" : "cooling"}`}><div className="tp-home-target-rotation-title">{isHeating ? <TrendingUp size={22} aria-hidden="true" /> : <TrendingDown size={22} aria-hidden="true" />}<h3>{section}</h3><Info size={17} aria-hidden="true" />{available && <span>共 {resource.data.length} 個題材</span>}</div>{loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" || !available ? <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section={section} /> : resource.data.length === 0 ? <MainlinesState loading={false} state="EMPTY" reason={`${section}目前沒有符合結果。`} dataDate={resource.dataDate} section={section} /> : <div className="tp-home-topic-list">{resource.data.map((topic, index) => <Link href={`/topics/${topic.topicSlug}`} key={topic.topicSlug}><span className="tp-home-target-rotation-rank">{index + 1}</span><span><b>{topic.topic}</b><small>{topic.currentGrade ?? "Grade 尚未提供"} · {topic.lifecycle ?? "Lifecycle 尚未提供"} · 絕對強度 {topic.absoluteScore ?? "—"} · 5D 中位數 {topic.baselineMedian ?? "—"} · Δ {topic.strengthDelta >= 0 ? "+" : ""}{topic.strengthDelta}</small></span><ChevronRight size={16} aria-hidden="true" /></Link>)}</div>}<CompactDisclosure loading={loading} resource={resource} sectionKey={isHeating ? "heatingTopics" : "coolingTopics"} sectionLabel={section} /></Card>;
}

// Today 只提供正式機會資料的摘要入口；完整內容維持在機會頁。
function OpportunityTeaserCard({ loading, resource }: { loading: boolean; resource: TodayOpportunityResource }) {
  const formal = resource.state === "FORMAL";
  // The complete opportunity surface is linked by href="/opportunities" from the heading above.
  return <Card className="tp-home-opportunities-card"><SectionHeading id="opportunities-title" title="今日機會" description="只顯示具備明確發布狀態的機會資料。" link={{ label: "查看全部機會", href: "/opportunities" }} />{loading || !formal ? <MainlinesState loading={loading} state={resource.state} reason={resource.reason ?? "今日機會資料尚未提供。"} dataDate={resource.dataDate} section="今日機會" /> : <div className="tp-home-opportunity-summary"><strong>正式機會資料已發布</strong><span>{resource.data.length} 個題材入口可供進一步研究。</span></div>}<CompactDisclosure loading={loading} resource={resource} sectionKey="opportunities" sectionLabel="今日機會" /></Card>;
}

export default function TodayMarketPage() {
  const mainlines = useTodayMainlines();
  return <PageContainer className="tp-home-page-container" title="今日市場" hideHeader><div className="tp-home-content"><section className="tp-home-section" aria-labelledby="market-overview-title"><MarketOverviewCard loading={mainlines.loading} resource={mainlines.resource.marketOverview} /></section><section className="tp-home-section" aria-labelledby="market-signals-title"><MarketSignalCards loading={mainlines.loading} resource={mainlines.resource.dailyFocus} /></section><MainlineCards loading={mainlines.loading} resource={mainlines.resource} /><TopicPulsePanel loading={mainlines.loading} resource={mainlines.resource} /><section className="tp-home-section" aria-labelledby="rotation-title"><SectionHeading id="rotation-title" title="快速升溫／快速退潮" description="比較正式絕對強度與前 5 個可比交易日中位數；歷史不足時明確顯示不可評估。" /><div className="tp-home-rotation-grid"><RotationCard loading={mainlines.loading} resource={mainlines.resource.heating} direction="heating" /><RotationCard loading={mainlines.loading} resource={mainlines.resource.cooling} direction="cooling" /></div></section><section className="tp-home-section" aria-labelledby="opportunities-title"><OpportunityTeaserCard loading={mainlines.loading} resource={mainlines.resource.opportunities} /></section></div></PageContainer>;
}
