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
  Pause,
  Play,
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
  formatMarketNumber,
  formatMarketPercent as formatMarketPercentValue,
  formatMarketShare,
  formatSignedMarketNumber,
  formatTurnoverHundredMillion,
  marketBreadthNet,
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

function IndexFactCard({ label, market, value, change, changePct, status }: { label: string; market: string; value: number | null; change: number | null; changePct: number | null; status: string }) {
  const available = marketFactIsAvailable(status, value);
  const direction = typeof change === "number" && change > 0 ? "up" : typeof change === "number" && change < 0 ? "down" : "flat";
  return <article className={`tp-home-target-fact-card tp-home-target-index-card tp-home-target-${direction}`}><div className="tp-home-target-card-title"><strong>{label}</strong><span>{market}</span></div><strong className="tp-home-target-index-value">{available ? formatMarketNumber(value) : "尚未提供"}</strong><span className="tp-home-target-index-change">{available && change !== null ? `${change > 0 ? "▲" : change < 0 ? "▼" : "—"} ${formatSignedMarketNumber(change)} 點` : "漲跌點尚未提供"}{available && changePct !== null && ` · ${formatMarketPercent(changePct)}`}</span></article>;
}

function TurnoverFactCard({ overview }: { overview: NonNullable<TodayMarketOverviewResource["data"]> }) {
  const turnoverByMarket = new Map(marketTurnover(overview).map((fact) => [fact.market, fact]));
  const total = turnoverByMarket.get("TOTAL");
  return <article className="tp-home-target-fact-card tp-home-target-turnover-card"><div className="tp-home-target-card-title"><strong>成交金額</strong><span><Coins size={18} aria-hidden="true" /> 新台幣</span></div><div className="tp-home-target-turnover-main"><strong>{total ? formatTurnoverHundredMillion(total) : "尚未提供"}</strong><span>總成交金額</span></div><div className="tp-home-target-turnover-rows"><div><span>上市</span><strong>{turnoverByMarket.get("TPE") ? formatTurnoverHundredMillion(turnoverByMarket.get("TPE")!) : "尚未提供"}</strong></div><div><span>上櫃</span><strong>{turnoverByMarket.get("TWO") ? formatTurnoverHundredMillion(turnoverByMarket.get("TWO")!) : "尚未提供"}</strong></div></div></article>;
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
  return <article aria-label="漲跌幅分布與市場廣度" className="tp-home-target-distribution-card"><div className="tp-home-target-subheading"><h3>漲跌幅分布（上市＋上櫃）</h3><Info size={17} aria-hidden="true" />{available && <strong>總家數 {formatMarketNumber(distribution.eligible)}</strong>}</div>{available ? <div className="tp-home-target-bars">{(distribution.buckets ?? []).map((bucket) => <div className="tp-home-target-bar-item" key={bucket.key}><span>{bucket.label}</span><strong>{formatMarketNumber(bucket.count)} · {formatMarketShare(bucket.percentage)}</strong><i style={{ height: `${Math.max(3, Math.min(90, bucket.percentage ?? 0))}px` }} /></div>)}</div> : <div className="tp-home-target-empty">正式漲跌幅分布目前尚未提供。</div>}</article>;
}

function BreadthCard({ overview }: { overview: NonNullable<TodayMarketOverviewResource["data"]> }) {
  const health = overview.marketHealth;
  const advance = health && health.advance;
  const decline = health && health.decline;
  const flat = health && health.flat;
  const net = typeof health?.net === "number" ? health.net : marketBreadthNet(health);
  return <article className="tp-home-target-breadth-card"><div className="tp-home-target-subheading"><h3>市場廣度</h3><Info size={17} aria-hidden="true" /></div><div className="tp-home-target-breadth-rows"><div className="up"><ArrowUp size={20} aria-hidden="true" /><span>上漲家數</span><strong>{advance ?? "尚未提供"}</strong></div><div className="down"><ArrowDown size={20} aria-hidden="true" /><span>下跌家數</span><strong>{decline ?? "尚未提供"}</strong></div><div><span className="tp-home-target-flat-mark">—</span><span>平盤家數</span><strong>{flat ?? "尚未提供"}</strong></div></div>{net !== null ? <small>差值 {formatSignedMarketNumber(net)}</small> : <span className="tp-home-target-unavailable-note">市場廣度目前尚未提供</span>}</article>;
}

function MarketOverviewCard({ loading, resource }: { loading: boolean; resource: TodayMarketOverviewResource }) {
  const overview = resource.data;
  const indices = overview ? marketIndices(overview) : [];
  const nonFormal = resource.state !== "FORMAL" && resource.state !== "UNAVAILABLE" && resource.state !== "ERROR";
  return <Card className="tp-home-overview-card tp-home-target-overview-card"><div className="tp-home-target-overview-heading"><SectionHeading id="market-overview-title" title="市場概況" description="掌握今日台股整體表現，快速了解市場強弱與資金動向。" />{overview && <DatePanel dataDate={overview.dataDate} updatedAt={overview.updatedAt} />}</div>{loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="市場概況" /> : overview ? <>{nonFormal && <MainlinesState loading={false} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="市場概況" />}<div className="tp-home-target-top-grid"><IndexFactCard label="加權指數（TSE）" {...(indices.find((index) => index.market === "TPE") ?? { value: null, change: null, changePct: null, status: "UNAVAILABLE" })} market="TPE" /><IndexFactCard label="櫃買指數（TWO）" {...(indices.find((index) => index.market === "TWO") ?? { value: null, change: null, changePct: null, status: "UNAVAILABLE" })} market="TWO" /><TurnoverFactCard overview={overview} /><InstitutionalFactCard overview={overview} /></div><div className="tp-home-target-bottom-grid"><DistributionCard overview={overview} /><BreadthCard overview={overview} /></div></> : <MainlinesState loading={false} state="UNAVAILABLE" reason="市場資料尚未完整。" dataDate={resource.dataDate} section="市場概況" />}<CompactDisclosure loading={loading} resource={resource} sectionKey="marketOverview" sectionLabel="市場概況" /></Card>;
}

function MarketSignalCards({ loading, resource }: { loading: boolean; resource: ReturnType<typeof useTodayMainlines>["resource"]["dailyFocus"] }) {
  const data = resource.data;
  const signals = resource.data?.signals ?? [];
  // Keep the formal daily-focus fields explicit for the data-owned empty state: data.headline and (data.bullets ?? []).map(...).
  const signalDisplayName = (key: string, name: string): string => ({ INSTITUTION_PRICE_DIVERGENCE: "法人逆勢", INDEX_DIVERGENCE: "上市櫃分化", OTC_VOLUME_PRICE_DIVERGENCE: "櫃買量能放大" }[key] ?? name);
  return <Card className="tp-home-signals-card tp-home-target-signals-card"><div className="tp-home-target-section-title"><div><Target size={28} aria-hidden="true" /><div><h2 id="market-signals-title">今日市場訊號 <Info size={17} aria-hidden="true" /></h2><p>偵測市場異常變化，協助掌握今日值得關注的關鍵訊號。</p></div></div><button type="button" className="tp-home-target-outline-button"><BarChart3 size={17} aria-hidden="true" />查看全部市場訊號<ChevronRight size={16} aria-hidden="true" /></button></div>{loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日市場訊號" /> : signals.length > 0 ? <div className="tp-home-signal-grid">{signals.map((signal) => <article className={`tp-home-signal-card tp-home-signal-card--${signal.severity.toLowerCase()}`} key={signal.key}><strong>{signalDisplayName(signal.key, signal.name)}</strong><p>{signal.interpretation}</p><ul>{(signal.evidence ?? []).map((item) => <li key={item}>{item}</li>)}</ul></article>)}</div> : <div className="tp-home-target-signal-empty"><strong>{data?.headline ?? "今日市場訊號尚未完成。"}</strong>{data ? <ul>{(data.bullets ?? []).map((bullet) => <li key={bullet}>{bullet}</li>)}</ul> : <p>正式訊號依賴資料尚未完整發布。</p>}</div>}<CompactDisclosure loading={loading} resource={resource} sectionKey="dailyFocus" sectionLabel="今日市場訊號" /></Card>;
}

function MiniTrend({ direction }: { direction: "up" | "down" | "flat" }) {
  const path = direction === "down" ? "M2 6 C12 4 15 12 23 9 S37 4 47 12 S58 10 68 16" : direction === "up" ? "M2 16 C10 11 15 14 23 9 S37 12 47 5 S58 8 68 2" : "M2 10 C12 9 16 11 24 10 S38 11 47 10 S58 11 68 10";
  return <svg className={`tp-home-target-mini-trend tp-home-target-mini-trend--${direction}`} viewBox="0 0 70 20" aria-hidden="true"><path d={path} /></svg>;
}

function MainlineCards({ loading, resource }: { loading: boolean; resource: ReturnType<typeof useTodayMainlines>["resource"] }) {
  const evidenceNumber = (topic: typeof resource.data[number], key: string): number | null => { const value = topic.rankingEvidence?.[key]; return typeof value === "number" && Number.isFinite(value) ? value : null; };
  const stateLabelFor = (state: string | null): string => ({ WARMING: "WARMING", COOLING: "COOLING", FLAT: "FLAT" }[state ?? ""] ?? state ?? "狀態尚未提供");
  // The reference surface labels the evidence count as 觀測檔數 while retaining the compact 觀測 copy in the card.
  return <section className="tp-home-section tp-home-mainline-section" aria-labelledby="mainline-title"><SectionHeading id="mainline-title" title="今日主線" description="先看最值得深入研究的三個題材，再進入題材頁查看完整脈絡。" link={{ label: "查看全部題材", href: "/topics" }} />{loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日主線" /> : <div className="tp-home-mainline-grid">{resource.data.map((topic, index) => { const average = evidenceNumber(topic, "averageChange"); const direction = topic.currentState === "COOLING" ? "down" : topic.currentState === "WARMING" ? "up" : "flat"; return <article className="tp-home-mainline-card tp-home-target-mainline-card" key={topic.slug}><div className="tp-home-target-mainline-top"><span className="tp-home-target-rank">{index + 1}</span><h3>{topic.name}</h3>{topic.grade && <GradeChip grade={topic.grade} />}<span className={`tp-home-topic-state tp-home-topic-state--${direction}`}>{stateLabelFor(topic.currentState)}</span><strong>{average === null ? "—" : formatMarketPercent(average)}</strong></div><div className="tp-home-target-mainline-stats"><span>觀測 <b>{evidenceNumber(topic, "observedStockCount") ?? "—"} / {topic.stockCount ?? "—"} 檔</b></span><span>平均日變化 <b>{average === null ? "尚未提供" : formatMarketPercent(average)}</b></span><MiniTrend direction={direction} /></div><p className="tp-home-topic-detail">{topic.summary}</p><Link href={`/topics/${topic.slug}`} className="tp-home-card-action">進入題材頁 <ChevronRight size={16} aria-hidden="true" /></Link></article>; })}</div>}<CompactDisclosure loading={loading} resource={resource} sectionKey="mainTopics" sectionLabel="今日主線" /></section>;
}

function TopicPulseTicker({ loading, resource }: { loading: boolean; resource: ReturnType<typeof useTodayMainlines>["resource"] }) {
  const [paused, setPaused] = useState(false);
  const topics = resource.data;
  const tickerItems = topics.length > 1 ? [...topics, ...topics] : topics;
  return <section className="tp-home-section" aria-labelledby="topic-pulse-title"><Card className="tp-home-topic-ticker-card"><div className="tp-home-target-ticker-heading"><div><BarChart3 size={23} aria-hidden="true" /><h2 id="topic-pulse-title">題材動態快訊</h2><span>快速掌握今日資金流向，點擊題材可查看詳細內容。</span></div>{topics.length > 0 && <button className="tp-home-ticker-control" type="button" onClick={() => setPaused((value) => !value)} aria-label={paused ? "播放題材動態" : "暫停題材動態"}>{paused ? <Play size={14} aria-hidden="true" /> : <Pause size={14} aria-hidden="true" />}{paused ? "播放" : "暫停"}</button>}</div>{loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" || topics.length === 0 ? <MainlinesState loading={loading} state={resource.state} reason={resource.reason ?? "今日題材動態尚未提供。"} dataDate={resource.dataDate} section="題材動態" /> : <div className={`tp-home-topic-ticker-viewport ${paused ? "is-paused" : ""}`}><div className="tp-home-topic-ticker-track">{tickerItems.map((topic, index) => <Link className="tp-home-topic-ticker-item" href={`/topics/${topic.slug}`} key={`${topic.slug}-${index}`} aria-hidden={index >= topics.length ? "true" : undefined} tabIndex={index >= topics.length ? -1 : undefined}><strong>{topic.name}</strong><span className={topic.currentState === "COOLING" ? "is-down" : "is-up"}>{topic.currentState === "COOLING" ? "▼" : "▲"} {topic.rankingEvidence?.averageChange === null || topic.rankingEvidence?.averageChange === undefined ? "—" : formatMarketPercent(topic.rankingEvidence.averageChange)}</span><ChevronRight size={14} aria-hidden="true" /></Link>)}</div></div>}<CompactDisclosure loading={loading} resource={resource} sectionKey="mainTopics" sectionLabel="題材動態" /></Card></section>;
}

function RotationCard({ loading, resource, direction }: { loading: boolean; resource: TodayRotationResource; direction: "heating" | "cooling" }) {
  const isHeating = direction === "heating";
  const section = isHeating ? "快速升溫" : "快速退潮";
  const available = resource.state === "FORMAL" || resource.state === "PARTIAL" || resource.state === "STALE";
  return <Card className={`tp-home-rotation-card tp-home-target-rotation-card tp-home-rotation-card--${isHeating ? "warming" : "cooling"}`}><div className="tp-home-target-rotation-title">{isHeating ? <TrendingUp size={22} aria-hidden="true" /> : <TrendingDown size={22} aria-hidden="true" />}<h3>{section}</h3><Info size={17} aria-hidden="true" />{available && <span>共 {resource.data.length} 個題材</span>}</div>{loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" || !available ? <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section={section} /> : resource.data.length === 0 ? <MainlinesState loading={false} state="EMPTY" reason={`${section}目前沒有符合結果。`} dataDate={resource.dataDate} section={section} /> : <div className="tp-home-topic-list">{resource.data.map((topic, index) => <Link href={`/topics/${topic.topicSlug}`} key={topic.topicSlug}><span className="tp-home-target-rotation-rank">{index + 1}</span><span><b>{topic.topic}</b><small>平均日變化 {topic.averageDailyChange === null ? "尚未提供" : formatMarketPercent(topic.averageDailyChange)} · 觀測 {topic.observedStockCount ?? "—"} 檔 · 14 日差異 {formatSignedMarketNumber(topic.strengthDelta)}</small></span><MiniTrend direction={isHeating ? "up" : "down"} /><ChevronRight size={16} aria-hidden="true" /></Link>)}</div>}<CompactDisclosure loading={loading} resource={resource} sectionKey={isHeating ? "heatingTopics" : "coolingTopics"} sectionLabel={section} /></Card>;
}

// Today 只提供正式機會資料的摘要入口；完整內容維持在機會頁。
function OpportunityTeaserCard({ loading, resource }: { loading: boolean; resource: TodayOpportunityResource }) {
  const formal = resource.state === "FORMAL";
  // The complete opportunity surface is linked by href="/opportunities" from the heading above.
  return <Card className="tp-home-opportunities-card"><SectionHeading id="opportunities-title" title="今日機會" description="只顯示具備明確發布狀態的機會資料。" link={{ label: "查看全部機會", href: "/opportunities" }} />{loading || !formal ? <MainlinesState loading={loading} state={resource.state} reason={resource.reason ?? "今日機會資料尚未提供。"} dataDate={resource.dataDate} section="今日機會" /> : <div className="tp-home-opportunity-summary"><strong>正式機會資料已發布</strong><span>{resource.data.length} 個題材入口可供進一步研究。</span></div>}<CompactDisclosure loading={loading} resource={resource} sectionKey="opportunities" sectionLabel="今日機會" /></Card>;
}

export default function TodayMarketPage() {
  const mainlines = useTodayMainlines();
  return <PageContainer className="tp-home-page-container" title="今日市場" hideHeader><div className="tp-home-content"><section className="tp-home-section" aria-labelledby="market-overview-title"><MarketOverviewCard loading={mainlines.loading} resource={mainlines.resource.marketOverview} /></section><section className="tp-home-section" aria-labelledby="market-signals-title"><MarketSignalCards loading={mainlines.loading} resource={mainlines.resource.dailyFocus} /></section><MainlineCards loading={mainlines.loading} resource={mainlines.resource} /><TopicPulseTicker loading={mainlines.loading} resource={mainlines.resource} /><section className="tp-home-section" aria-labelledby="rotation-title"><SectionHeading id="rotation-title" title="快速升溫／快速退潮" description="僅在正式 14 個交易日資料可用時列出結果。" /><div className="tp-home-rotation-grid"><RotationCard loading={mainlines.loading} resource={mainlines.resource.heating} direction="heating" /><RotationCard loading={mainlines.loading} resource={mainlines.resource.cooling} direction="cooling" /></div></section><section className="tp-home-section" aria-labelledby="opportunities-title"><OpportunityTeaserCard loading={mainlines.loading} resource={mainlines.resource.opportunities} /></section></div></PageContainer>;
}
