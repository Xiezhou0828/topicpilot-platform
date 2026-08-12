"use client";

import Link from "next/link";
import {
  ArrowDownRight,
  ArrowUpRight,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import { useSnapshot } from "../../lib/snapshot-store";
import type { MarketIndexView } from "../../lib/types";
import { useTodayMainlines } from "../../lib/today-mainlines";
import {
  Card,
  GradeChip,
  PageContainer,
  RoleChip,
} from "./V2Foundation";

type MarketMetric = {
  label: string;
  value: string;
  change?: string;
  tone?: "up" | "down" | "neutral";
  note?: string;
  source?: "live" | "mock";
};

const mockMarketMetrics: MarketMetric[] = [
  { label: "加權指數", value: "23,184.72", change: "+286.14  +1.25%", tone: "up", note: "較昨收" },
  { label: "OTC 指數", value: "248.31", change: "+2.18  +0.89%", tone: "up", note: "較昨收" },
  { label: "成交金額", value: "3,428 億", note: "估計值" },
  { label: "上漲家數", value: "682", tone: "up" },
  { label: "下跌家數", value: "417", tone: "down" },
  { label: "平盤家數", value: "126", tone: "neutral" },
  { label: "漲停", value: "38", tone: "up" },
  { label: "跌停", value: "7", tone: "down" },
  { label: "更新時間", value: "10:48" },
];

function formatAsOf(value: string | null): string | null {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("zh-TW", { timeZone: "Asia/Taipei", hour: "2-digit", minute: "2-digit", hour12: false }).format(parsed);
}

function findIndex(indices: MarketIndexView[], name: string): MarketIndexView | null {
  const index = indices.find((item) => item.name === name);
  return index && !index.pending && index.value !== "待接資料源" ? index : null;
}

function liveMetric(index: MarketIndexView | null, fallback: MarketMetric): MarketMetric {
  if (!index) return fallback;
  return {
    ...fallback,
    value: index.value,
    change: index.change === null ? undefined : `${index.change > 0 ? "+" : ""}${index.change.toFixed(2)}%`,
    source: "live",
    note: index.asOf ? `後端快照 · ${formatAsOf(index.asOf) ?? index.asOf}` : "後端快照",
  };
}

const events = [
  { time: "09:08", topic: "BBU", event: "首次升至 S", tone: "up" as const },
  { time: "09:42", topic: "機器人", event: "開始升溫", tone: "up" as const },
  { time: "10:15", topic: "AI伺服器", event: "開始分歧", tone: "neutral" as const },
  { time: "10:48", topic: "重電", event: "退出主線", tone: "down" as const },
];

const warmingTopics = [
  { name: "機器人", state: "快速升溫", grade: "A" },
  { name: "PCB", state: "量能回流", grade: "A" },
  { name: "光通訊", state: "開始轉強", grade: "B" },
];

const coolingTopics = [
  { name: "BBU", state: "高檔分歧", grade: "S" },
  { name: "重電", state: "快速退潮", grade: "B" },
  { name: "ABF", state: "主線轉弱", grade: "B" },
];

const opportunities = [
  { name: "AI伺服器", count: "3 檔符合條件", note: "主線維持強勢" },
  { name: "機器人", count: "2 檔符合條件", note: "盤中首次升溫" },
  { name: "PCB", count: "1 檔符合條件", note: "量能重新集中" },
];

function MetricValue({ metric }: { metric: MarketMetric }) {
  const Icon = metric.tone === "down" ? ArrowDownRight : ArrowUpRight;
  return (
    <div className={`tp-home-metric tp-home-metric--${metric.tone ?? "neutral"}`}>
      <span className="tp-home-metric-label">{metric.label}</span>
      <strong>{metric.value}</strong>
      {metric.change && <span className="tp-home-metric-change"><Icon size={15} aria-hidden="true" />{metric.change}</span>}
      {metric.note && <small>{metric.note}</small>}
    </div>
  );
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

function MainlinesState({ loading, state, reason, dataDate }: { loading: boolean; state: "FORMAL" | "PREVIEW" | "UNAVAILABLE"; reason: string | null; dataDate: string | null }) {
  const label = loading ? "讀取中" : state === "PREVIEW" ? "Preview" : "資料暫不可用";
  return (
    <div className={`tp-home-mainlines-state tp-home-mainlines-state--${loading ? "loading" : state.toLowerCase()}`} role="status">
      <span className="tp-data-state">{label}</span>
      <p>{loading ? "正在讀取後端主線資料。" : reason}</p>
      {dataDate && <small>資料日：{dataDate}</small>}
    </div>
  );
}

export default function TodayMarketPage() {
  const { bundle, status } = useSnapshot();
  const mainlines = useTodayMainlines();
  const isSyntheticPreview = bundle.qualityPanelData.freshness.sourceLabel === "公開合成資料";
  const canUseBackendData = bundle.source === "snapshot" && status.dataState !== "UNAVAILABLE" && !isSyntheticPreview;
  const liveWeighted = canUseBackendData ? findIndex(bundle.homeData.marketIndices, "加權指數") : null;
  const liveOtc = canUseBackendData ? findIndex(bundle.homeData.marketIndices, "櫃買指數") : null;
  const liveBreadth = canUseBackendData ? bundle.marketRadar?.breadth : null;
  const asOf = canUseBackendData
    ? formatAsOf(bundle.qualityPanelData.freshness.quoteUpdatedAt) ?? formatAsOf(bundle.qualityPanelData.freshness.generatedAt)
    : null;
  const marketMetrics: MarketMetric[] = [
    liveMetric(liveWeighted, mockMarketMetrics[0]),
    liveMetric(liveOtc, mockMarketMetrics[1]),
    mockMarketMetrics[2],
    liveBreadth?.advance === null || liveBreadth?.advance === undefined ? mockMarketMetrics[3] : { ...mockMarketMetrics[3], value: liveBreadth.advance.toLocaleString("en-US"), source: "live", note: "後端快照" },
    liveBreadth?.decline === null || liveBreadth?.decline === undefined ? mockMarketMetrics[4] : { ...mockMarketMetrics[4], value: liveBreadth.decline.toLocaleString("en-US"), source: "live", note: "後端快照" },
    liveBreadth?.flat === null || liveBreadth?.flat === undefined ? mockMarketMetrics[5] : { ...mockMarketMetrics[5], value: liveBreadth.flat.toLocaleString("en-US"), source: "live", note: "後端快照" },
    ...mockMarketMetrics.slice(6, 8),
    asOf ? { ...mockMarketMetrics[8], value: asOf, source: "live" } : mockMarketMetrics[8],
  ];
  const marketSession = bundle.qualityPanelData.freshness.marketSession;
  const freshnessLabel = !isSyntheticPreview && status.dataState === "LIVE" && marketSession === "OPEN"
    ? "盤中更新"
    : !isSyntheticPreview && status.dataState === "SNAPSHOT"
      ? "盤後更新"
      : "資料待更新";
  return (
    <PageContainer className="tp-home-page-container" title="今日市場" hideHeader>
      <div className="tp-home-content">
        <section className="tp-home-section" aria-labelledby="market-overview-title">
          <Card className="tp-home-overview-card">
            <SectionHeading id="market-overview-title" title="市場概況" trailing={<span className="tp-home-live-status"><span className={`tp-home-live-status-dot tp-home-live-status-dot--${freshnessLabel === "盤中更新" ? "live" : freshnessLabel === "盤後更新" ? "after" : "pending"}`} aria-hidden="true" />{freshnessLabel}{asOf && <time>{asOf}</time>}</span>} />
            <div className="tp-home-primary-metrics">
              {marketMetrics.slice(0, 3).map((metric) => <MetricValue key={metric.label} metric={metric} />)}
            </div>
            <div className="tp-home-secondary-metrics">
              {marketMetrics.slice(3).map((metric) => <MetricValue key={metric.label} metric={metric} />)}
            </div>
          </Card>
        </section>

        <section className="tp-home-section" aria-labelledby="market-story-title">
          <Card className="tp-home-story-card">
            <SectionHeading id="market-story-title" title="今日市場重點" />
            <ul className="tp-home-story-list">
              <li><strong>AI伺服器</strong>仍為市場主線。</li>
              <li><strong>BBU</strong>開始高檔分歧。</li>
              <li><strong>機器人</strong>盤中快速升溫。</li>
            </ul>
            <div className="tp-home-one-line"><span>今日一句話</span><strong>今天研究重心：觀察 AI 是否開始擴散。</strong></div>
          </Card>
        </section>

        <section className="tp-home-section" aria-labelledby="mainline-title">
          <SectionHeading id="mainline-title" title="今日主線" description="先看最值得深入研究的三個題材，再進入題材頁查看完整脈絡。" link={{ label: "查看全部題材", href: "/topics" }} />
          {mainlines.loading || mainlines.resource.state === "UNAVAILABLE" ? (
            <MainlinesState
              loading={mainlines.loading}
              state={mainlines.resource.state}
              reason={mainlines.resource.reason}
              dataDate={mainlines.resource.dataDate}
            />
          ) : (
            <>
              {mainlines.resource.state === "PREVIEW" && (
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
        </section>

        <section className="tp-home-section" aria-labelledby="events-title">
          <Card className="tp-home-events-card">
            <SectionHeading id="events-title" title="盤中重要事件" description="只記錄真正值得注意的題材狀態轉換。" />
            <ol className="tp-home-events">
              {events.map((item) => (
                <li key={`${item.time}-${item.topic}`}>
                  <time>{item.time}</time>
                  <span className={`tp-home-event-marker tp-home-event-marker--${item.tone}`} aria-hidden="true" />
                  <div><strong>{item.topic}</strong><span>{item.event}</span></div>
                </li>
              ))}
            </ol>
          </Card>
        </section>

        <section className="tp-home-section" aria-labelledby="rotation-title">
          <SectionHeading id="rotation-title" title="快速升溫／快速退潮" description="用精簡清單看資金正在往哪裡移動。" />
          <div className="tp-home-rotation-grid">
            <Card className="tp-home-rotation-card tp-home-rotation-card--warming">
              <div className="tp-home-rotation-heading"><TrendingUp size={18} aria-hidden="true" /><h3>快速升溫</h3><span>3 個題材</span></div>
              <div className="tp-home-topic-list">
                {warmingTopics.map((topic) => <Link href="/topics" key={topic.name}><span><b>{topic.name}</b><small>{topic.state}</small></span><RoleChip>{topic.grade}</RoleChip><ChevronRight size={16} aria-hidden="true" /></Link>)}
              </div>
            </Card>
            <Card className="tp-home-rotation-card tp-home-rotation-card--cooling">
              <div className="tp-home-rotation-heading"><ArrowDownRight size={18} aria-hidden="true" /><h3>快速退潮</h3><span>3 個題材</span></div>
              <div className="tp-home-topic-list">
                {coolingTopics.map((topic) => <Link href="/topics" key={topic.name}><span><b>{topic.name}</b><small>{topic.state}</small></span><RoleChip>{topic.grade}</RoleChip><ChevronRight size={16} aria-hidden="true" /></Link>)}
              </div>
            </Card>
          </div>
        </section>

        <section className="tp-home-section" aria-labelledby="opportunities-title">
          <Card className="tp-home-opportunities-card">
            <SectionHeading id="opportunities-title" title="今日機會" description="只呈現研究入口，不在首頁完成推薦分析。" link={{ label: "查看更多", href: "/opportunities" }} />
            <div className="tp-home-opportunity-list">
              {opportunities.map((item) => <Link href="/opportunities" key={item.name}><div><strong>{item.name}</strong><span>{item.note}</span></div><b>{item.count}</b><ChevronRight size={16} aria-hidden="true" /></Link>)}
            </div>
          </Card>
        </section>
      </div>
    </PageContainer>
  );
}
