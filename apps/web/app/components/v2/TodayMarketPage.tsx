"use client";

import Link from "next/link";
import {
  ArrowDownRight,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import {
  useTodayMainlines,
  type TodayMarketEventsResource,
  type TodayMarketOverviewResource,
  type TodayOpportunityResource,
  type TodayRotationResource,
  type TodaySectionState,
} from "../../lib/today-mainlines";
import {
  Card,
  GradeChip,
  PageContainer,
} from "./V2Foundation";

function formatEventTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("zh-TW", {
    timeZone: "Asia/Taipei",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(parsed);
}

function SectionHeading({ id, eyebrow, title, description, link, trailing }: { id?: string; eyebrow?: string; title: string; description?: string; link?: { label: string; href: string }; trailing?: React.ReactNode }) {
  return (
    <div className="tp-home-section-heading">
      <div>
        {eyebrow && <p className="tp-overline">{eyebrow}</p>}
        <h2 id={id}>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {(trailing || link) && <div className="tp-home-section-heading-actions">{trailing}{link && <Link className="tp-home-section-link" href={link.href}>{link.label}<ChevronRight size={16} aria-hidden="true" /></Link>}</div>}
    </div>
  );
}

function MainlinesState({ loading, state, reason, dataDate, section = "Today section" }: { loading: boolean; state: TodaySectionState; reason: string | null; dataDate: string | null; section?: string }) {
  const labels: Record<TodaySectionState | "LOADING", string> = {
    LOADING: "Loading",
    FORMAL: "Formal data",
    TEMPORARY: "Temporary data",
    PREVIEW: "Preview data",
    UNAVAILABLE: "Unavailable",
    ERROR: "Load error",
  };
  const effectiveState = loading ? "LOADING" : state;
  const isError = effectiveState === "ERROR";
  const temporaryState = state === "TEMPORARY" ? "TEMPORARY" : null;
  const label = loading ? labels.LOADING : temporaryState ? labels[temporaryState] : labels[state];
  return (
    <div
      className={`tp-home-mainlines-state tp-home-mainlines-state--${effectiveState.toLowerCase()}`}
      role={isError ? "alert" : "status"}
      aria-live={isError ? "assertive" : "polite"}
    >
      <span className="tp-data-state">{label}</span>
      <p>{loading ? `Loading ${section}.` : reason ?? `${section} is not currently publishable.`}</p>
      {dataDate && <small>資料日：{dataDate}</small>}
    </div>
  );
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
};

const disclosureSectionLabels: Record<string, string> = {
  mainTopics: "Main Topics",
  heatingTopics: "Heating",
  coolingTopics: "Cooling",
  dailyFocus: "Daily Focus",
  marketPulse: "Market Events",
  marketOverview: "Market Overview",
  [["market", "Indices"].join("")]: "Market indices",
  [["turn", "over"].join("")]: "Market turnover",
};

function friendlySectionName(value: string): string {
  return disclosureSectionLabels[value] ?? "another Today section";
}

function friendlySourceName(value: string | null): string {
  if (!value) return "Not disclosed";
  const normalized = value.trim().toUpperCase();
  const labels: Record<string, string> = {
    POSTGRESQL: "backend database",
    BACKEND: "backend service",
    TWSE: "TWSE source",
    TPEX: "TPEx source",
  };
  return labels[normalized] ?? "backend-provided source";
}

function SectionDisclosure({
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
  const stateLabel: Record<TodaySectionState | "LOADING", string> = {
    LOADING: "Loading",
    FORMAL: "Formal data",
    TEMPORARY: "Temporary data",
    PREVIEW: "Preview data",
    UNAVAILABLE: "Unavailable",
    ERROR: "Load error",
  };
  const effectiveState = loading ? "LOADING" : resource.state;
  const messages = [
    resource.temporarySections.includes(sectionKey)
      ? `${sectionLabel} is temporarily published and is not formal data.`
      : null,
    resource.missingSections.includes(sectionKey)
      ? `${sectionLabel} is not complete enough to publish.`
      : null,
    resource.temporarySections.some((value) => value !== sectionKey)
      ? `Other temporary sections: ${resource.temporarySections.filter((value) => value !== sectionKey).map(friendlySectionName).join(", ")}.`
      : null,
    resource.missingSections.some((value) => value !== sectionKey)
      ? `Other unavailable sections: ${resource.missingSections.filter((value) => value !== sectionKey).map(friendlySectionName).join(", ")}.`
      : null,
    ...resource.qualityNotes.map((note) => `Data note: ${note}`),
  ].filter((message): message is string => Boolean(message));

  return (
    <div className="tp-home-section-disclosure" aria-label={`${sectionLabel} data disclosure`}>
      <small>
        Status: {stateLabel[effectiveState]} · Data date: {resource.dataDate ?? "Not disclosed"} · As of: {resource.asOf ?? "Not disclosed"} · Latest snapshot: {resource.latestSnapshotTime ?? "Not disclosed"} · Generated: {resource.generatedAt ?? "Not disclosed"} · Source: {friendlySourceName(resource.source)}
      </small>
      {messages.length > 0 && (
        <ul data-quality-disclosure="true">
          {messages.map((message) => <li key={message}>{message}</li>)}
        </ul>
      )}
    </div>
  );
}

function OverviewValue({ label, value }: { label: string; value: number | string | null }) {
  const formatted = typeof value === "number" ? value.toLocaleString("en-US") : value ?? "—";
  return (
    <div className="tp-home-metric tp-home-metric--neutral">
      <span className="tp-home-metric-label">{label}</span>
      <strong>{formatted}</strong>
    </div>
  );
}

function OpportunityTeaserCard({
  loading,
  resource,
}: {
  loading: boolean;
  resource: TodayOpportunityResource;
}) {
  const canRenderData = resource.state === "FORMAL" || resource.state === "PREVIEW";
  return (
    <Card className="tp-home-opportunities-card">
      <SectionHeading
        id="opportunities-title"
        title="今日機會"
        description="只顯示具備明確發布狀態的機會資料。"
      />
      {loading || !canRenderData ? (
        <MainlinesState
          loading={loading}
          state={resource.state}
          reason={resource.reason}
          dataDate={resource.dataDate}
          section="今日機會"
        />
      ) : (
        <>
          {resource.state === "PREVIEW" && (
            <MainlinesState
              loading={false}
              state={resource.state}
              reason={resource.reason}
              dataDate={resource.dataDate}
              section="今日機會"
            />
          )}
          <div className="tp-home-opportunity-list" aria-label="Today opportunities">
            {resource.data.map((opportunity) => (
              <article key={opportunity.topicSlug}>
                <div>
                  <strong>{opportunity.topic}</strong>
                  <span>{opportunity.summary}</span>
                </div>
              </article>
            ))}
          </div>
        </>
      )}
      <SectionDisclosure loading={loading} resource={resource} sectionKey="opportunities" sectionLabel="Today Opportunities" />
    </Card>
  );
}

function MarketOverviewCard({
  loading,
  resource,
}: {
  loading: boolean;
  resource: TodayMarketOverviewResource;
}) {
  const overview = resource.data;
  const health = overview?.marketHealth ?? null;
  return (
    <Card className="tp-home-overview-card">
      <SectionHeading id="market-overview-title" title="市場概況" description="只顯示 Home contract 提供的市場總覽資料。" />
      {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? (
        <MainlinesState
          loading={loading}
          state={resource.state}
          reason={resource.reason}
          dataDate={resource.dataDate}
          section="市場概況"
        />
      ) : overview ? (
        <>
          {resource.state !== "FORMAL" && (
            <MainlinesState
              loading={false}
              state={resource.state}
              reason={resource.reason}
              dataDate={resource.dataDate}
              section="市場概況"
            />
          )}
          <div className="tp-home-primary-metrics">
            <OverviewValue label="資料狀態" value={overview.dataStatus} />
            <OverviewValue label="追蹤股票" value={overview.trackedStockCount} />
            <OverviewValue label="追蹤題材" value={overview.trackedTopicCount} />
          </div>
          {health ? (
            <div className="tp-home-secondary-metrics">
              <OverviewValue label={`${health.market} 市場狀態`} value={health.status} />
              <OverviewValue label="市場總數" value={health.totalStocks} />
              <OverviewValue label="上漲家數" value={health.advance} />
              <OverviewValue label="下跌家數" value={health.decline} />
              <OverviewValue label="平盤家數" value={health.flat} />
              <OverviewValue label="不可用家數" value={health.unavailable} />
            </div>
          ) : (
            <div className="tp-empty-state"><p>市場廣度資料目前不可用。</p></div>
          )}
        </>
      ) : (
        <MainlinesState
          loading={false}
          state="UNAVAILABLE"
          reason="Home.marketOverview is unavailable."
          dataDate={resource.dataDate}
          section="市場概況"
        />
      )}
      <SectionDisclosure loading={loading} resource={resource} sectionKey="marketOverview" sectionLabel="Market Overview" />
    </Card>
  );
}

function MarketEventsCard({
  loading,
  resource,
}: {
  loading: boolean;
  resource: TodayMarketEventsResource;
}) {
  return (
    <Card className="tp-home-events-card">
      <SectionHeading id="events-title" title="盤中重要事件" description="只記錄 backend contract 提供的市場事件。" />
      {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? (
        <MainlinesState
          loading={loading}
          state={resource.state}
          reason={resource.reason}
          dataDate={resource.dataDate}
          section="盤中重要事件"
        />
      ) : (
        <>
          {resource.state !== "FORMAL" && (
            <MainlinesState
              loading={false}
              state={resource.state}
              reason={resource.reason}
              dataDate={resource.dataDate}
              section="盤中重要事件"
            />
          )}
          <ol className="tp-home-events">
            {resource.data.map((event) => (
              <li key={`${event.eventTime}-${event.topicSlug}-${event.eventType}`}>
                <time>{formatEventTime(event.eventTime)}</time>
                <span className="tp-home-event-marker" aria-hidden="true" />
                <div>
                  <Link href={`/topics/${event.topicSlug}`}><strong>{event.topic}</strong></Link>
                  <span>{event.description}</span>
                  <small>{event.eventType} · {event.severity} · {event.source}</small>
                </div>
              </li>
            ))}
          </ol>
        </>
      )}
      <SectionDisclosure loading={loading} resource={resource} sectionKey="marketPulse" sectionLabel="Market Events" />
    </Card>
  );
}

function RotationCard({
  loading,
  resource,
  direction,
}: {
  loading: boolean;
  resource: TodayRotationResource;
  direction: "heating" | "cooling";
}) {
  const isHeating = direction === "heating";
  const section = isHeating ? "升溫" : "退潮";
  return (
    <Card className={`tp-home-rotation-card tp-home-rotation-card--${isHeating ? "warming" : "cooling"}`}>
      <div className="tp-home-rotation-heading">
        {isHeating ? <TrendingUp size={18} aria-hidden="true" /> : <ArrowDownRight size={18} aria-hidden="true" />}
        <h3>{isHeating ? "快速升溫" : "快速退潮"}</h3>
        <span>{resource.data.length} 個題材</span>
      </div>
      {loading || resource.state === "UNAVAILABLE" || resource.state === "ERROR" ? (
        <MainlinesState
          loading={loading}
          state={resource.state}
          reason={resource.reason}
          dataDate={resource.dataDate}
          section={section}
        />
      ) : (
        <>
          {resource.state !== "FORMAL" && (
            <MainlinesState
              loading={false}
              state={resource.state}
              reason={resource.reason}
              dataDate={resource.dataDate}
              section={section}
            />
          )}
          <div className="tp-home-topic-list">
            {resource.data.map((topic) => (
              <Link href={`/topics/${topic.topicSlug}`} key={topic.topicSlug}>
                <span><b>{topic.topic}</b><small>{topic.summary}</small></span>
                <GradeChip grade={topic.currentGrade} />
                <ChevronRight size={16} aria-hidden="true" />
              </Link>
            ))}
          </div>
        </>
      )}
      <SectionDisclosure loading={loading} resource={resource} sectionKey={isHeating ? "heatingTopics" : "coolingTopics"} sectionLabel={section} />
    </Card>
  );
}

export default function TodayMarketPage() {
  const mainlines = useTodayMainlines();
  return (
    <PageContainer className="tp-home-page-container" title="今日市場" hideHeader>
      <div className="tp-home-content">
        <section className="tp-home-section" aria-labelledby="market-overview-title">
          <MarketOverviewCard loading={mainlines.loading} resource={mainlines.resource.marketOverview} />
        </section>

        <section className="tp-home-section" aria-labelledby="market-story-title">
          <Card className="tp-home-story-card">
            <SectionHeading id="market-story-title" title="今日市場重點" />
            {mainlines.loading || mainlines.resource.dailyFocus.state === "UNAVAILABLE" || mainlines.resource.dailyFocus.state === "ERROR" ? (
              <MainlinesState
                loading={mainlines.loading}
                state={mainlines.resource.dailyFocus.state}
                reason={mainlines.resource.dailyFocus.reason}
                dataDate={mainlines.resource.dailyFocus.dataDate}
                section="市場焦點"
              />
            ) : (
              <>
                {mainlines.resource.dailyFocus.state !== "FORMAL" && (
                  <MainlinesState
                    loading={false}
                    state={mainlines.resource.dailyFocus.state}
                    reason={mainlines.resource.dailyFocus.reason}
                    dataDate={mainlines.resource.dailyFocus.dataDate}
                    section="市場焦點"
                  />
                )}
                {mainlines.resource.dailyFocus.data && (
                  <>
                    <ul className="tp-home-story-list">
                      {mainlines.resource.dailyFocus.data.bullets?.map((bullet) => <li key={bullet}>{bullet}</li>)}
                    </ul>
                    <div className="tp-home-one-line"><span>今日一句話</span><strong>{mainlines.resource.dailyFocus.data.headline}</strong></div>
                    <small>模式：{mainlines.resource.dailyFocus.mode} · 來源：{mainlines.resource.dailyFocus.source}{mainlines.resource.dailyFocus.dataDate && ` · 資料日：${mainlines.resource.dailyFocus.dataDate}`}</small>
                  </>
                )}
              </>
            )}
            <SectionDisclosure loading={mainlines.loading} resource={mainlines.resource.dailyFocus} sectionKey="dailyFocus" sectionLabel="Daily Focus" />
          </Card>
        </section>

        <section className="tp-home-section" aria-labelledby="mainline-title">
          <SectionHeading id="mainline-title" title="今日主線" description="先看最值得深入研究的三個題材，再進入題材頁查看完整脈絡。" link={{ label: "查看全部題材", href: "/topics" }} />
          {mainlines.loading || mainlines.resource.state === "UNAVAILABLE" || mainlines.resource.state === "ERROR" ? (
            <MainlinesState
              loading={mainlines.loading}
              state={mainlines.resource.state}
              reason={mainlines.resource.reason}
              dataDate={mainlines.resource.dataDate}
            />
          ) : (
            <>
              {(mainlines.resource.state === "PREVIEW" || mainlines.resource.state === "TEMPORARY") && (
                <MainlinesState
                  loading={false}
                  state={mainlines.resource.state}
                  reason={mainlines.resource.reason}
                  dataDate={mainlines.resource.dataDate}
                />
              )}
              <div className="tp-home-mainline-grid">
                {mainlines.resource.data.map((topic) => (
                  <article className="tp-home-mainline-card" key={topic.slug}>
                    <div className="tp-home-card-topline">
                      <h3>{topic.name}</h3>
                      <GradeChip grade={topic.grade ?? "—"} />
                    </div>
                    <p className="tp-home-topic-state">{topic.currentState ?? "狀態待後端提供"}</p>
                    <p className="tp-home-topic-detail">{topic.summary || "摘要待後端提供"}</p>
                    <Link href={`/topics/${topic.slug}`} className="tp-home-card-action">進入題材頁 <ChevronRight size={16} aria-hidden="true" /></Link>
                  </article>
                ))}
              </div>
            </>
          )}
          <SectionDisclosure loading={mainlines.loading} resource={mainlines.resource} sectionKey="mainTopics" sectionLabel="Main Topics" />
        </section>

        <section className="tp-home-section" aria-labelledby="events-title">
          <MarketEventsCard loading={mainlines.loading} resource={mainlines.resource.marketEvents} />
        </section>

        <section className="tp-home-section" aria-labelledby="rotation-title">
          <SectionHeading id="rotation-title" title="快速升溫／快速退潮" description="用精簡清單看資金正在往哪裡移動。" />
          <div className="tp-home-rotation-grid">
            <RotationCard loading={mainlines.loading} resource={mainlines.resource.heating} direction="heating" />
            <RotationCard loading={mainlines.loading} resource={mainlines.resource.cooling} direction="cooling" />
          </div>
        </section>

        <section className="tp-home-section" aria-labelledby="opportunities-title">
          <OpportunityTeaserCard loading={mainlines.loading} resource={mainlines.resource.opportunities} />
        </section>
      </div>
    </PageContainer>
  );
}
