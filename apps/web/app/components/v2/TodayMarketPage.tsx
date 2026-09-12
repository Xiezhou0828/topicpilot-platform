"use client";

import Link from "next/link";
import { ChevronRight, Info, Pause, Play, TrendingDown, TrendingUp } from "lucide-react";
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
  formatMarketPercent,
  formatSignedMarketNumber,
  formatTurnoverUnit,
  marketDataStatusLabel,
  marketDistribution,
  marketFactIsAvailable,
  marketFactState,
  marketIndices,
  marketTurnover,
} from "../../lib/today-market-fields";
import { commercialStateLabel } from "../../lib/commercial-state.mjs";
import { Card, GradeChip, PageContainer } from "./V2Foundation";

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
    FORMAL: "正式資料",
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

function MainlinesState({
  loading,
  state,
  reason,
  dataDate,
  section = "Today",
}: {
  loading: boolean;
  state: TodaySectionState;
  reason: string | null;
  dataDate: string | null;
  section?: string;
}) {
  const effectiveState = loading ? "LOADING" : state;
  const isError = effectiveState === "ERROR";
  return (
    <div
      className={`tp-home-mainlines-state tp-home-mainlines-state--${effectiveState.toLowerCase()}`}
      role={isError ? "alert" : "status"}
      aria-live={isError ? "assertive" : "polite"}
    >
      <span className="tp-data-state">{stateLabel(effectiveState)}</span>
      <p>{loading ? `正在讀取${section}。` : reason ?? `${section}目前尚未提供。`}</p>
      {dataDate && <small>資料日：{formatMarketDate(dataDate)}</small>}
    </div>
  );
}

function friendlySourceName(value: string | null): string {
  if (!value) return "尚未提供";
  const normalized = value.trim().toUpperCase();
  if (normalized.includes("TWSE")) return "TWSE 正式來源";
  if (normalized.includes("TPEX")) return "TPEx 正式來源";
  if (normalized.includes("HOME") || normalized.includes("POSTGRES")) return "TopicPilot 正式資料來源";
  return "正式資料來源";
}

function CompactDisclosure({
  loading,
  resource,
  sectionKey,
  sectionLabel,
}: {
  loading: boolean;
  resource: TodayDisclosureResource;
  sectionKey: string;
  sectionLabel: string;
}) {
  const effectiveState = loading ? "LOADING" : resource.state;
  const sectionStatus = resource.sectionStatus?.status ?? (effectiveState === "FORMAL" ? "AVAILABLE" : null);
  const notes = [
    resource.temporarySections.includes(sectionKey) ? `${sectionLabel}目前為暫時資料。` : null,
    resource.missingSections.includes(sectionKey) ? `${sectionLabel}目前尚未完成發布。` : null,
    ...resource.qualityNotes
      .filter((note) => !/public\.|ingestion|Home\.|backend|postgres/i.test(note))
      .map((note) => `資料提示：${note}`),
  ].filter((value): value is string => Boolean(value));

  return (
    <details className="tp-home-compact-disclosure">
      <summary>
        <Info size={13} aria-hidden="true" />
        <span>{resource.asOf ? `資料截至 ${formatMarketAsOf(resource.asOf)}` : "資料截至尚未提供"}</span>
        <span aria-label={`${sectionLabel} 狀態`}>{stateLabel(effectiveState)}</span>
      </summary>
      <div className="tp-home-compact-disclosure-body">
        <span>發布狀態：{sectionStatus ?? "尚未提供"}</span>
        <span>來源：{friendlySourceName(resource.sectionStatus?.source ?? resource.source)}</span>
        {notes.map((note) => <span key={note}>{note}</span>)}
      </div>
    </details>
  );
}

function SectionHeading({
  id,
  eyebrow,
  title,
  description,
  link,
  trailing,
}: {
  id?: string;
  eyebrow?: string;
  title: string;
  description?: string;
  link?: { label: string; href: string };
  trailing?: React.ReactNode;
}) {
  return (
    <div className="tp-home-section-heading">
      <div>
        {eyebrow && <p className="tp-overline">{eyebrow}</p>}
        <h2 id={id}>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {(trailing || link) && (
        <div className="tp-home-section-heading-actions">
          {trailing}
          {link && <Link className="tp-home-section-link" href={link.href}>{link.label}<ChevronRight size={16} aria-hidden="true" /></Link>}
        </div>
      )}
    </div>
  );
}

function OfficialMarketFields({ overview }: { overview: NonNullable<TodayMarketOverviewResource["data"]> }) {
  const indices = marketIndices(overview);
  const turnover = marketTurnover(overview);
  const indexState = marketFactState(indices);
  const turnoverState = marketFactState(turnover);
  return (
    <div className="tp-home-official-market">
      <div className="tp-home-official-market-heading">
        <div>
          <span className="tp-overline">收盤後 EOD</span>
          <h3>指數與成交金額</h3>
        </div>
        <span className="tp-home-eod-badge">不代表盤中即時</span>
      </div>
      <div className="tp-home-market-fact-group">
        <div className="tp-home-market-fact-heading"><h4>市場指數</h4><span>{marketDataStatusLabel(indexState)}</span></div>
        <div className="tp-home-index-grid">
          {indices.map((index) => {
            const available = marketFactIsAvailable(index.status, index.value);
            const direction = typeof index.change === "number" && index.change > 0
              ? "tp-home-market-value--up"
              : typeof index.change === "number" && index.change < 0 ? "tp-home-market-value--down" : "";
            return (
              <article className="tp-home-index-card" key={`${index.market}-${index.indexCode}`}>
                <div className="tp-home-index-card-topline"><strong>{index.indexName}</strong><span>{index.market}</span></div>
                <span className={`tp-home-market-availability ${available ? "is-available" : "is-unavailable"}`}>{available ? "資料可用" : "尚未提供"}</span>
                <strong className={`tp-home-index-value ${direction}`}>{available ? formatMarketNumber(index.value) : "尚未提供"}</strong>
                <span className={`tp-home-index-change ${direction}`}>
                  {available && index.change !== null ? `漲跌 ${formatSignedMarketNumber(index.change)}` : "漲跌點尚未提供"}
                  {available && ` · ${formatMarketPercent(index.changePct)}`}
                </span>
                <dl className="tp-home-fact-meta">
                  <div><dt>交易日</dt><dd>{formatMarketDate(index.tradingDate ?? overview.dataDate)}</dd></div>
                  <div><dt>截至</dt><dd>{formatMarketAsOf(index.asOf ?? overview.updatedAt)}</dd></div>
                </dl>
              </article>
            );
          })}
        </div>
      </div>
      <div className="tp-home-market-fact-group">
        <div className="tp-home-market-fact-heading"><h4>成交金額</h4><span>{marketDataStatusLabel(turnoverState)}</span></div>
        <div className="tp-home-turnover-grid">
          {turnover.map((fact) => {
            const available = marketFactIsAvailable(fact.status, fact.value);
            return (
              <article className="tp-home-turnover-card" key={`${fact.market}-turnover`}>
                <div className="tp-home-index-card-topline"><strong>{fact.market} 市場</strong><span>{fact.session ?? "收盤"}</span></div>
                <strong className="tp-home-turnover-value">{available ? formatMarketNumber(fact.value) : "尚未提供"}</strong>
                <span>{available ? formatTurnoverUnit(fact) : "正式成交金額尚未提供"}</span>
              </article>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function BreadthAndDistribution({ overview }: { overview: NonNullable<TodayMarketOverviewResource["data"]> }) {
  const health = overview.marketHealth;
  const distribution = marketDistribution(overview);
  return (
    <div className="tp-home-market-structure">
      <div className="tp-home-market-structure-heading">
        <div><span className="tp-overline">EOD 觀測</span><h3>漲跌幅分布與市場廣度</h3></div>
        <span>{distribution?.status === "AVAILABLE" ? `${distribution.eligible} 檔可計算` : "正式分布尚未提供"}</span>
      </div>
      {distribution ? (
        <div className="tp-home-distribution-grid" aria-label="漲跌幅分布">
          {(distribution.buckets ?? []).map((bucket) => <div className="tp-home-distribution-item" key={bucket.key}><span>{bucket.label}</span><strong>{formatMarketNumber(bucket.count)}</strong></div>)}
        </div>
      ) : <div className="tp-home-official-empty">正式漲跌幅分布目前尚未提供。</div>}
      {distribution && distribution.excluded > 0 && <p className="tp-home-structure-note">{formatMarketNumber(distribution.excluded)} 檔因缺少可用的前收／當日報價或受 no-quote 狀態影響，未納入分布；不以 0% 代替。</p>}
      <div className="tp-home-breadth-panel">
        <div className="tp-home-breadth-heading"><h4>市場廣度</h4><span>{health?.market ?? "TPE+TWO"}</span></div>
        {health ? (
          <div className="tp-home-breadth-metrics">
            <div className="tp-home-breadth-metric tp-home-breadth-metric--up"><span>上漲</span><strong>{health.advance ?? "尚未提供"}</strong></div>
            <div className="tp-home-breadth-metric tp-home-breadth-metric--down"><span>下跌</span><strong>{health.decline ?? "尚未提供"}</strong></div>
            <div className="tp-home-breadth-metric"><span>平盤</span><strong>{health.flat ?? "尚未提供"}</strong></div>
            <div className="tp-home-breadth-metric"><span>差值</span><strong>{health.net === null || health.net === undefined ? "尚未提供" : formatSignedMarketNumber(health.net)}</strong></div>
          </div>
        ) : <div className="tp-home-official-empty">市場廣度目前尚未提供。</div>}
        {health?.breadthEligible ? <p className="tp-home-structure-note">以上比例基於 {formatMarketNumber(health.breadthEligible)} 檔具備當日與前收的正式觀測。</p> : null}
      </div>
    </div>
  );
}

function MarketOverviewCard({ loading, resource }: { loading: boolean; resource: TodayMarketOverviewResource }) {
  const overview = resource.data;
  return (
    <Card className="tp-home-overview-card">
      <SectionHeading id="market-overview-title" eyebrow="TODAY / MARKET" title="市場概況" description="以正式收盤資料快速掌握指數、成交金額、漲跌幅分布與市場廣度。" />
      {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? (
        <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="市場概況" />
      ) : overview ? (
        <>
          {resource.state !== "FORMAL" && <MainlinesState loading={false} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="市場概況" />}
          <OfficialMarketFields overview={overview} />
          <BreadthAndDistribution overview={overview} />
        </>
      ) : <MainlinesState loading={false} state="UNAVAILABLE" reason="市場資料尚未完整。" dataDate={resource.dataDate} section="市場概況" />}
      <CompactDisclosure loading={loading} resource={resource} sectionKey="marketOverview" sectionLabel="市場概況" />
    </Card>
  );
}

function MarketHighlightsCard({ loading, resource }: { loading: boolean; resource: ReturnType<typeof useTodayMainlines>["resource"]["dailyFocus"] }) {
  return (
    <Card className="tp-home-highlights-card">
      <SectionHeading id="market-highlights-title" title="今日市場重點" description="只從已發布的指數與市場廣度 facts 產生，沒有 LLM 敘事或盤中推測。" />
      {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? (
        <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日市場重點" />
      ) : resource.data ? (
        <>
          {resource.state !== "FORMAL" && <MainlinesState loading={false} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日市場重點" />}
          <p className="tp-home-highlights-headline">{resource.data.headline}</p>
          <ul className="tp-home-story-list">{(resource.data.bullets ?? []).map((bullet) => <li key={bullet}>{bullet}</li>)}</ul>
        </>
      ) : <MainlinesState loading={false} state="UNAVAILABLE" reason="今日市場重點尚未完成。" dataDate={resource.dataDate} section="今日市場重點" />}
      <CompactDisclosure loading={loading} resource={resource} sectionKey="dailyFocus" sectionLabel="今日市場重點" />
    </Card>
  );
}

function MainlineCards({ loading, resource }: { loading: boolean; resource: ReturnType<typeof useTodayMainlines>["resource"] }) {
  return (
    <section className="tp-home-section" aria-labelledby="mainline-title">
      <SectionHeading id="mainline-title" title="今日主線" description="最多三個正式 Topic 入口；詳細脈絡請進入題材頁。" link={{ label: "查看全部題材", href: "/topics" }} />
      {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? (
        <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日主線" />
      ) : (
        <>
          {resource.state !== "FORMAL" && <MainlinesState loading={false} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日主線" />}
          <div className="tp-home-mainline-grid">
            {resource.data.map((topic) => (
              <article className="tp-home-mainline-card" key={topic.slug}>
                <div className="tp-home-card-topline"><h3>{topic.name}</h3>{topic.grade && <GradeChip grade={topic.grade} />}</div>
                <p className="tp-home-topic-detail">{topic.summary}</p>
                <Link href={`/topics/${topic.slug}`} className="tp-home-card-action">進入題材頁 <ChevronRight size={16} aria-hidden="true" /></Link>
              </article>
            ))}
          </div>
        </>
      )}
      <CompactDisclosure loading={loading} resource={resource} sectionKey="mainTopics" sectionLabel="今日主線" />
    </section>
  );
}

function TopicPulseTicker({ loading, resource }: { loading: boolean; resource: ReturnType<typeof useTodayMainlines>["resource"] }) {
  const [paused, setPaused] = useState(false);
  const topics = resource.data;
  const tickerItems = topics.length > 1 ? [...topics, ...topics] : topics;
  const tickerState = resource.state === "FORMAL" && topics.length === 0 ? "EMPTY" : resource.state;
  return (
    <section className="tp-home-section" aria-labelledby="topic-pulse-title">
      <Card className="tp-home-topic-ticker-card">
        <SectionHeading id="topic-pulse-title" eyebrow="收盤後題材脈動" title="今日題材動態" description="僅呈現今日正式 Topic snapshot；沒有盤中曲線，也不推測盤中排名變化。" trailing={topics.length > 0 ? <button className="tp-home-ticker-control" type="button" onClick={() => setPaused((value) => !value)} aria-label={paused ? "播放題材動態" : "暫停題材動態"}>{paused ? <Play size={14} aria-hidden="true" /> : <Pause size={14} aria-hidden="true" />}{paused ? "播放" : "暫停"}</button> : undefined} />
        {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" || topics.length === 0 ? (
          <MainlinesState loading={loading} state={tickerState} reason={resource.reason} dataDate={resource.dataDate} section="題材動態" />
        ) : (
          <div className={`tp-home-topic-ticker-viewport ${paused ? "is-paused" : ""}`}>
            <div className="tp-home-topic-ticker-track">
              {tickerItems.map((topic, index) => <Link className="tp-home-topic-ticker-item" href={`/topics/${topic.slug}`} key={`${topic.slug}-${index}`}><strong>{topic.name}</strong><span>{topic.summary}</span><ChevronRight size={14} aria-hidden="true" /></Link>)}
            </div>
          </div>
        )}
        <CompactDisclosure loading={loading} resource={resource} sectionKey="mainTopics" sectionLabel="題材動態" />
      </Card>
    </section>
  );
}

function RotationCard({ loading, resource, direction }: { loading: boolean; resource: TodayRotationResource; direction: "heating" | "cooling" }) {
  const isHeating = direction === "heating";
  const section = isHeating ? "快速升溫" : "快速退潮";
  const availableRows = resource.state === "FORMAL" || resource.state === "PARTIAL" || resource.state === "STALE";
  return (
    <Card className={`tp-home-rotation-card tp-home-rotation-card--${isHeating ? "warming" : "cooling"}`}>
      <div className="tp-home-rotation-heading">{isHeating ? <TrendingUp size={18} aria-hidden="true" /> : <TrendingDown size={18} aria-hidden="true" />}<h3>{section}</h3>{availableRows && <span>{resource.data.length} 個題材</span>}</div>
      {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" || !availableRows ? (
        <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section={section} />
      ) : resource.data.length === 0 ? (
        <MainlinesState loading={false} state="EMPTY" reason={`${section}目前沒有符合結果。`} dataDate={resource.dataDate} section={section} />
      ) : (
        <div className="tp-home-topic-list">{resource.data.map((topic) => <Link href={`/topics/${topic.topicSlug}`} key={topic.topicSlug}><span><b>{topic.topic}</b><small>{topic.summary}</small></span>{topic.currentGrade && <GradeChip grade={topic.currentGrade} />}<ChevronRight size={16} aria-hidden="true" /></Link>)}</div>
      )}
      <CompactDisclosure loading={loading} resource={resource} sectionKey={isHeating ? "heatingTopics" : "coolingTopics"} sectionLabel={section} />
    </Card>
  );
}

function OpportunityTeaserCard({ loading, resource }: { loading: boolean; resource: TodayOpportunityResource }) {
  const formal = resource.state === "FORMAL";
  return (
    <Card className="tp-home-opportunities-card">
      <SectionHeading id="opportunities-title" title="今日機會" description="Today 只提供正式機會資料的摘要入口；完整內容維持在機會頁。" link={{ label: "探索今日機會", href: "/opportunities" }} />
      {loading || !formal ? (
        <MainlinesState loading={loading} state={resource.state} reason={resource.reason ?? "正式機會資料尚未發布。"} dataDate={resource.dataDate} section="今日機會" />
      ) : (
        <div className="tp-home-opportunity-summary"><strong>正式機會資料已發布</strong><span>{resource.data.length} 個題材入口可供進一步研究。</span><Link className="tp-button tp-button--primary" href="/opportunities">探索今日機會 <ChevronRight size={16} aria-hidden="true" /></Link></div>
      )}
      <CompactDisclosure loading={loading} resource={resource} sectionKey="opportunities" sectionLabel="今日機會" />
    </Card>
  );
}

export default function TodayMarketPage() {
  const mainlines = useTodayMainlines();
  return (
    <PageContainer className="tp-home-page-container" title="今日市場" hideHeader>
      <div className="tp-home-content">
        <section className="tp-home-section" aria-labelledby="market-overview-title"><MarketOverviewCard loading={mainlines.loading} resource={mainlines.resource.marketOverview} /></section>
        <section className="tp-home-section" aria-labelledby="market-highlights-title"><MarketHighlightsCard loading={mainlines.loading} resource={mainlines.resource.dailyFocus} /></section>
        <MainlineCards loading={mainlines.loading} resource={mainlines.resource} />
        <TopicPulseTicker loading={mainlines.loading} resource={mainlines.resource} />
        <section className="tp-home-section" aria-labelledby="rotation-title"><SectionHeading id="rotation-title" title="快速升溫／快速退潮" description="只在正式 14 個交易日資料可用時顯示，沒有自行推導排名箭頭。" /><div className="tp-home-rotation-grid"><RotationCard loading={mainlines.loading} resource={mainlines.resource.heating} direction="heating" /><RotationCard loading={mainlines.loading} resource={mainlines.resource.cooling} direction="cooling" /></div></section>
        <section className="tp-home-section" aria-labelledby="opportunities-title"><OpportunityTeaserCard loading={mainlines.loading} resource={mainlines.resource.opportunities} /></section>
      </div>
    </PageContainer>
  );
}
