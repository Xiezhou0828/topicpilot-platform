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
  formatTurnoverHundredMillion,
  marketBreadthNet,
  marketIndexDisplayName,
  marketDistribution,
  marketFactIsAvailable,
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
  const targetIndexLabels = {
    TPE: "加權指數",
    TWO: "櫃買指數",
  } as const;
  const indices = marketIndices(overview);
  const turnover = marketTurnover(overview);
  const turnoverByMarket = new Map(turnover.map((fact) => [fact.market, fact]));
  const turnoverRows = [
    { market: "TPE", label: "上市" },
    { market: "TWO", label: "上櫃" },
  ];
  const totalTurnover = turnoverByMarket.get("TOTAL");
  return (
    <div className="tp-home-official-market">
      <div className="tp-home-official-market-heading">
        <div>
          <span className="tp-overline">收盤後</span>
          <h3>大盤指數與成交金額</h3>
        </div>
        <span className="tp-home-eod-badge">資料日 {formatMarketDate(overview.dataDate)}</span>
      </div>
      <div className="tp-home-market-summary-grid">
        {indices.map((index) => {
          const available = marketFactIsAvailable(index.status, index.value);
          const direction = typeof index.change === "number" && index.change > 0
            ? "tp-home-market-value--up"
            : typeof index.change === "number" && index.change < 0 ? "tp-home-market-value--down" : "";
          return (
            <article className="tp-home-index-card" key={`${index.market}-${index.indexCode}`}>
              <div className="tp-home-index-card-topline"><strong>{targetIndexLabels[index.market as keyof typeof targetIndexLabels] ?? marketIndexDisplayName(index)}</strong><span>{index.market}</span></div>
              <strong className={`tp-home-index-value ${direction}`}>{available ? formatMarketNumber(index.value) : "尚未提供"}</strong>
              <span className={`tp-home-index-change ${direction}`}>
                {available && index.change !== null
                  ? `${index.change > 0 ? "▲" : index.change < 0 ? "▼" : "—"} ${formatSignedMarketNumber(index.change)} 點`
                  : "漲跌點尚未提供"}
                {available && index.changePct !== null && ` · ${formatMarketPercent(index.changePct)}`}
              </span>
              {!available && <span className="tp-home-fact-status">正式指數資料尚未提供</span>}
            </article>
          );
        })}
        <article className="tp-home-turnover-card tp-home-turnover-card--summary">
          <div className="tp-home-index-card-topline"><strong>成交金額</strong><span>新台幣</span></div>
          <div className="tp-home-turnover-breakdown">
            {turnoverRows.map(({ market, label }) => {
              const fact = turnoverByMarket.get(market);
              return <div className="tp-home-turnover-row" key={market}><span>{label}</span><strong>{fact ? formatTurnoverHundredMillion(fact) : "尚未提供"}</strong></div>;
            })}
          </div>
          <div className="tp-home-turnover-total"><span>總成交金額</span><strong>{totalTurnover ? formatTurnoverHundredMillion(totalTurnover) : "尚未提供"}</strong></div>
          {!totalTurnover && <span className="tp-home-fact-status">正式成交金額合計尚未提供</span>}
        </article>
      </div>
    </div>
  );
}

function BreadthAndDistribution({ overview }: { overview: NonNullable<TodayMarketOverviewResource["data"]> }) {
  const health = overview.marketHealth;
  const distribution = marketDistribution(overview);
  const net = typeof health?.net === "number" ? health.net : marketBreadthNet(health);
  const distributionAvailable = distribution?.status === "AVAILABLE" && distribution.eligible > 0;
  return (
    <div className="tp-home-market-structure">
      <div className="tp-home-market-structure-heading">
        <div><span className="tp-overline">收盤後觀察</span><h3>漲跌幅分布與市場廣度</h3></div>
        <span>{distributionAvailable ? `${distribution.eligible} 檔有完整漲跌幅` : "正式分布尚未提供"}</span>
      </div>
      {distributionAvailable ? (
        <div className="tp-home-distribution-panel">
          <div className="tp-home-distribution-grid" aria-label="漲跌幅分布">
            {(distribution.buckets ?? []).map((bucket) => {
              const share = distribution.eligible > 0 ? Math.max(0, Math.min(100, (bucket.count / distribution.eligible) * 100)) : 0;
              return <div className="tp-home-distribution-item" key={bucket.key} style={{ "--tp-home-distribution-share": `${share}%` } as React.CSSProperties}><div className="tp-home-distribution-label"><span>{bucket.label}</span><strong>{formatMarketNumber(bucket.count)}</strong></div><div className="tp-home-distribution-bar" aria-hidden="true" /></div>;
            })}
          </div>
          <p className="tp-home-distribution-caption">各區間互斥，合計 {formatMarketNumber(distribution.eligible)} 檔；比例依完整收盤與前收觀測計算。</p>
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
            <div className="tp-home-breadth-metric"><span>差值</span><strong>{net === null ? "尚未提供" : `${net > 0 ? "▲" : net < 0 ? "▼" : "—"} ${formatSignedMarketNumber(net)}`}</strong></div>
          </div>
        ) : <div className="tp-home-official-empty">市場廣度目前尚未提供。</div>}
        {health?.breadthEligible ? <p className="tp-home-structure-note">以上比例基於 {formatMarketNumber(health.breadthEligible)} 檔具備當日與前收的正式觀測。</p> : null}
      </div>
    </div>
  );
}

function formatInstitutionalNet(value: string | number | null | undefined): string {
  const numeric = typeof value === "number" ? value : typeof value === "string" && value.trim() ? Number(value) : null;
  return typeof numeric === "number" && Number.isFinite(numeric)
    ? formatMarketNumber(numeric)
    : "尚未提供";
}

function InstitutionalFlowSummary({ overview }: { overview: NonNullable<TodayMarketOverviewResource["data"]> }) {
  const flow = overview.institutionFlows;
  const markets = flow?.markets ?? [];
  const marketLabels = new Map([["TPE", "上市"], ["TWO", "上櫃"]]);

  return (
    <div className="tp-home-institutional-flow" data-flow-status={flow?.status ?? "UNAVAILABLE"}>
      <div className="tp-home-institutional-flow-heading">
        <div><span className="tp-overline">正式法人資料</span><h3>三大法人買賣超</h3></div>
        <span>{flow?.asOfDate ? `資料日 ${formatMarketDate(flow.asOfDate)}` : "資料日尚未提供"}</span>
      </div>
      {markets.length > 0 ? (
        <div className="tp-home-institutional-flow-grid">
          {markets.map((market) => {
            const current = market.current;
            const rows = [
              ["外資", current?.foreign?.net],
              ["投信", current?.investmentTrust?.net],
              ["自營商", current?.dealer?.net],
              ["三大法人合計", current?.total?.net],
            ] as const;
            return (
              <article className="tp-home-institutional-flow-market" key={market.market}>
                <div className="tp-home-institutional-flow-market-heading">
                  <strong>{marketLabels.get(market.market) ?? market.market}</strong>
                  <span>{market.freshness === "CURRENT" ? "當日" : "正式資料"}</span>
                </div>
                <div className="tp-home-institutional-flow-values">
                  {rows.map(([label, value]) => (
                    <div className="tp-home-institutional-flow-value" key={label}>
                      <span>{label}</span>
                      <strong>{formatInstitutionalNet(value)}</strong>
                    </div>
                  ))}
                </div>
                {market.statusReason && <span className="tp-home-fact-status">{market.statusReason}</span>}
              </article>
            );
          })}
        </div>
      ) : (
        <div className="tp-home-official-empty">正式法人流向目前尚未提供；不以 0 代替缺少的買賣超資料。</div>
      )}
      {flow && flow.status !== "AVAILABLE" && <p className="tp-home-structure-note">法人流向狀態：{flow.status}，僅呈現目前正式可用的市場資料。</p>}
    </div>
  );
}

function signalDisplayName(key: string, formalName: string): string {
  return {
    INSTITUTION_PRICE_DIVERGENCE: "法人逆勢",
    INDEX_DIVERGENCE: "上市櫃分化",
    OTC_VOLUME_PRICE_DIVERGENCE: "櫃買量能放大",
    BREADTH_DIVERGENCE: "市場廣度異常",
  }[key] ?? formalName;
}

function MarketSignalCards({ loading, resource }: { loading: boolean; resource: ReturnType<typeof useTodayMainlines>["resource"]["dailyFocus"] }) {
  const signals = resource.data?.signals ?? [];
  const data = resource.data;
  return (
    <Card className="tp-home-signals-card" data-signal-count={signals.length}>
      <SectionHeading id="market-signals-title" title="今日市場訊號" description="只呈現正式市場資料觸發的訊號規則。" />
      {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? (
        <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日市場訊號" />
      ) : data ? (
        <>
          {resource.state !== "FORMAL" && <MainlinesState loading={false} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日市場訊號" />}
          {signals.length > 0 ? (
            <div className="tp-home-signal-grid" data-flow-status="formal">
              {signals.map((signal) => (
                <article className={`tp-home-signal-card tp-home-signal-card--${signal.severity.toLowerCase()}`} key={signal.key}>
                  <div className="tp-home-signal-card-heading"><span>{signalDisplayName(signal.key, signal.name)}</span><b>{signal.severity === "WARNING" ? "注意" : signal.severity === "WATCH" ? "觀察" : "訊息"}</b></div>
                  {signalDisplayName(signal.key, signal.name) !== signal.name && <small>{signal.name}</small>}
                  <p>{signal.interpretation}</p>
                  <ul>{(signal.evidence ?? []).map((item) => <li key={item}>{item}</li>)}</ul>
                </article>
              ))}
            </div>
          ) : (
            <div className="tp-home-signal-empty" data-flow-status="formal-no-triggered-signal">
              <strong>{data.headline}</strong>
              {(data.bullets ?? []).length > 0 ? (
                <ul>{(data.bullets ?? []).map((bullet) => <li key={bullet}>{bullet}</li>)}</ul>
              ) : <p>目前沒有符合正式規則的市場訊號。</p>}
            </div>
          )}
        </>
      ) : <MainlinesState loading={false} state="UNAVAILABLE" reason="今日市場訊號尚未完成。" dataDate={resource.dataDate} section="今日市場訊號" />}
      <CompactDisclosure loading={loading} resource={resource} sectionKey="dailyFocus" sectionLabel="今日市場訊號" />
    </Card>
  );
}

function MarketOverviewCard({ loading, resource }: { loading: boolean; resource: TodayMarketOverviewResource }) {
  const overview = resource.data;
  return (
    <Card className="tp-home-overview-card">
      <SectionHeading id="market-overview-title" eyebrow="TODAY / MARKET" title="市場概況" description="以收盤後資料掌握大盤方向、成交金額與市場廣度。" />
      {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? (
        <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="市場概況" />
      ) : overview ? (
        <>
          {resource.state !== "FORMAL" && <MainlinesState loading={false} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="市場概況" />}
          <OfficialMarketFields overview={overview} />
          <InstitutionalFlowSummary overview={overview} />
          <BreadthAndDistribution overview={overview} />
        </>
      ) : <MainlinesState loading={false} state="UNAVAILABLE" reason="市場資料尚未完整。" dataDate={resource.dataDate} section="市場概況" />}
      <CompactDisclosure loading={loading} resource={resource} sectionKey="marketOverview" sectionLabel="市場概況" />
    </Card>
  );
}

function MainlineCards({ loading, resource }: { loading: boolean; resource: ReturnType<typeof useTodayMainlines>["resource"] }) {
  const evidenceNumber = (topic: typeof resource.data[number], key: string): number | null => {
    const value = topic.rankingEvidence?.[key];
    return typeof value === "number" && Number.isFinite(value) ? value : null;
  };
  const topicStateLabel = (state: string | null): string => ({
    WARMING: "升溫",
    COOLING: "退潮",
    FLAT: "持平",
  }[state ?? ""] ?? state ?? "狀態尚未提供");
  const topicStateClass = (state: string | null): string => state?.toLowerCase() ?? "unknown";
  return (
    <section className="tp-home-section" aria-labelledby="mainline-title">
      <SectionHeading id="mainline-title" title="今日主線" description="最多三個正式題材入口；詳細脈絡請進入題材頁。" link={{ label: "查看全部題材", href: "/topics" }} />
      {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? (
        <MainlinesState loading={loading} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日主線" />
      ) : (
        <>
          {resource.state !== "FORMAL" && <MainlinesState loading={false} state={resource.state} reason={resource.reason} dataDate={resource.dataDate} section="今日主線" />}
          <div className="tp-home-mainline-grid">
            {resource.data.map((topic) => (
              <article className="tp-home-mainline-card" key={topic.slug}>
                <div className="tp-home-card-topline"><h3>{topic.name}</h3>{topic.grade && <GradeChip grade={topic.grade} />}</div>
                <div className="tp-home-mainline-meta" aria-label={`${topic.name} 今日主線指標`}>
                  <span className={`tp-home-topic-state tp-home-topic-state--${topicStateClass(topic.currentState)}`}>{topicStateLabel(topic.currentState)}</span>
                  <span><small>平均日變化</small><strong>{formatMarketPercent(evidenceNumber(topic, "averageChange"))}</strong></span>
                  <span><small>觀測檔數</small><strong>{evidenceNumber(topic, "observedStockCount") === null ? "尚未提供" : formatMarketNumber(evidenceNumber(topic, "observedStockCount"))}</strong></span>
                </div>
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
        <SectionHeading id="topic-pulse-title" eyebrow="收盤後題材脈動" title="今日題材動態" description="只呈現今天已發布的題材資料。" trailing={topics.length > 0 ? <button className="tp-home-ticker-control" type="button" onClick={() => setPaused((value) => !value)} aria-label={paused ? "播放題材動態" : "暫停題材動態"}>{paused ? <Play size={14} aria-hidden="true" /> : <Pause size={14} aria-hidden="true" />}{paused ? "播放" : "暫停"}</button> : undefined} />
        {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" || topics.length === 0 ? (
          <MainlinesState loading={loading} state={tickerState} reason={resource.reason} dataDate={resource.dataDate} section="題材動態" />
        ) : (
          <div className={`tp-home-topic-ticker-viewport ${paused ? "is-paused" : ""}`}>
            <div className="tp-home-topic-ticker-track">
              {tickerItems.map((topic, index) => {
                const average = topic.rankingEvidence?.averageChange;
                const state = topic.currentState === "WARMING" ? "升溫" : topic.currentState === "COOLING" ? "退潮" : topic.currentState ?? "狀態尚未提供";
                return <Link className="tp-home-topic-ticker-item" href={`/topics/${topic.slug}`} key={`${topic.slug}-${index}`} aria-hidden={index >= topics.length ? "true" : undefined} tabIndex={index >= topics.length ? -1 : undefined}><strong>{topic.name}</strong><span className={`tp-home-topic-ticker-direction tp-home-topic-ticker-direction--${topic.currentState?.toLowerCase() ?? "unknown"}`}>{state}</span><span>{typeof average === "number" && Number.isFinite(average) ? `平均日變化 ${formatMarketPercent(average)}` : "平均日變化尚未提供"}</span><small>資料日 {formatMarketDate(topic.dataDate)}</small><ChevronRight size={14} aria-hidden="true" /></Link>;
              })}
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
        <div className="tp-home-topic-list">{resource.data.map((topic) => <Link href={`/topics/${topic.topicSlug}`} key={topic.topicSlug}><span><b>{topic.topic}</b><small>{topic.summary}</small><span className="tp-home-topic-list-meta"><span>平均日變化 <strong>{formatMarketPercent(topic.averageDailyChange)}</strong></span><span>觀測檔數 <strong>{topic.observedStockCount === null ? "尚未提供" : formatMarketNumber(topic.observedStockCount)}</strong></span><span>14 日差異 <strong>{formatSignedMarketNumber(topic.strengthDelta)}</strong></span></span></span>{topic.currentGrade && <GradeChip grade={topic.currentGrade} />}<ChevronRight size={16} aria-hidden="true" /></Link>)}</div>
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
        <section className="tp-home-section" aria-labelledby="market-signals-title"><MarketSignalCards loading={mainlines.loading} resource={mainlines.resource.dailyFocus} /></section>
        <MainlineCards loading={mainlines.loading} resource={mainlines.resource} />
        <TopicPulseTicker loading={mainlines.loading} resource={mainlines.resource} />
        <section className="tp-home-section" aria-labelledby="rotation-title"><SectionHeading id="rotation-title" title="快速升溫／快速退潮" description="僅在正式 14 個交易日資料可用時列出結果。" /><div className="tp-home-rotation-grid"><RotationCard loading={mainlines.loading} resource={mainlines.resource.heating} direction="heating" /><RotationCard loading={mainlines.loading} resource={mainlines.resource.cooling} direction="cooling" /></div></section>
        <section className="tp-home-section" aria-labelledby="opportunities-title"><OpportunityTeaserCard loading={mainlines.loading} resource={mainlines.resource.opportunities} /></section>
      </div>
    </PageContainer>
  );
}
