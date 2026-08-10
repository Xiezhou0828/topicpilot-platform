import Link from "next/link";
import {
  ArrowDownRight,
  ArrowUpRight,
  ChevronRight,
  Clock3,
  TrendingUp,
} from "lucide-react";
import {
  Card,
  DataState,
  Freshness,
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
};

const marketMetrics: MarketMetric[] = [
  { label: "加權指數", value: "23,184.72", change: "+286.14  +1.25%", tone: "up", note: "較昨收" },
  { label: "OTC 指數", value: "248.31", change: "+2.18  +0.89%", tone: "up", note: "較昨收" },
  { label: "成交金額", value: "3,428 億", note: "估計值" },
  { label: "上漲家數", value: "682", tone: "up" },
  { label: "下跌家數", value: "417", tone: "down" },
  { label: "平盤家數", value: "126", tone: "neutral" },
  { label: "漲停", value: "38", tone: "up" },
  { label: "跌停", value: "7", tone: "down" },
  { label: "更新時間", value: "10:48", note: "盤中快照" },
];

const mainlines = [
  { name: "AI伺服器", grade: "S", state: "全面走強", detail: "量能與主流股同步，仍是今日市場核心方向。" },
  { name: "BBU", grade: "S", state: "高檔整理", detail: "高位震盪加劇，留意族群內部開始分歧。" },
  { name: "機器人", grade: "A", state: "快速升溫", detail: "盤中關注度上升，資金開始擴散至相關零組件。" },
] as const;

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

function SectionHeading({ id, eyebrow, title, description, link }: { id?: string; eyebrow?: string; title: string; description?: string; link?: { label: string; href: string } }) {
  return (
    <div className="tp-home-section-heading">
      <div>
        {eyebrow && <p className="tp-overline">{eyebrow}</p>}
        <h2 id={id}>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {link && <Link className="tp-home-section-link" href={link.href}>{link.label}<ChevronRight size={16} aria-hidden="true" /></Link>}
    </div>
  );
}

export default function TodayMarketPage() {
  return (
    <PageContainer eyebrow="今日市場" title="今日市場" description="從市場脈動開始，整理今天值得繼續研究的方向。">
      <div className="tp-home-page-status" aria-label="市場資料狀態">
        <Freshness state="盤中更新" asOf="開發用固定快照 · 10:48" />
        <DataState state="資料待更新" />
      </div>

      <div className="tp-home-content">
        <section className="tp-home-section" aria-labelledby="market-overview-title">
          <Card className="tp-home-overview-card">
            <SectionHeading id="market-overview-title" eyebrow="MARKET PULSE" title="市場概況" description="用一眼掌握今日市場的廣度與方向。" />
            <div className="tp-home-primary-metrics">
              {marketMetrics.slice(0, 3).map((metric) => <MetricValue key={metric.label} metric={metric} />)}
            </div>
            <div className="tp-home-secondary-metrics">
              {marketMetrics.slice(3).map((metric) => <MetricValue key={metric.label} metric={metric} />)}
            </div>
            <div className="tp-home-card-footnote"><Clock3 size={14} aria-hidden="true" />資料為開發用固定快照，正式版將由市場聚合 API 提供。</div>
          </Card>
        </section>

        <section className="tp-home-section" aria-labelledby="market-story-title">
          <Card className="tp-home-story-card">
            <SectionHeading id="market-story-title" eyebrow="TODAY'S READ" title="今日市場重點" />
            <p className="tp-home-story">AI伺服器仍為市場主線，BBU 高檔開始分歧，機器人盤中快速升溫；今天的研究重心從主線延伸到資金是否持續擴散。</p>
          </Card>
        </section>

        <section className="tp-home-section" aria-labelledby="mainline-title">
          <SectionHeading id="mainline-title" eyebrow="TOP 3" title="今日主線" description="先看最值得深入研究的三個題材，再進入題材頁查看完整脈絡。" link={{ label: "查看全部題材", href: "/topics" }} />
          <div className="tp-home-mainline-grid">
            {mainlines.map((topic, index) => (
              <Link href="/topics" className="tp-home-mainline-card" key={topic.name}>
                <div className="tp-home-card-topline"><span className="tp-home-card-index">0{index + 1}</span><GradeChip grade={topic.grade} /></div>
                <h3>{topic.name}</h3>
                <p className="tp-home-topic-state">{topic.state}</p>
                <p className="tp-home-topic-detail">{topic.detail}</p>
                <span className="tp-home-card-action">進入題材頁 <ChevronRight size={16} aria-hidden="true" /></span>
              </Link>
            ))}
          </div>
        </section>

        <section className="tp-home-section" aria-labelledby="events-title">
          <Card className="tp-home-events-card">
            <SectionHeading id="events-title" eyebrow="INTRADAY SIGNALS" title="盤中重要事件" description="只記錄真正值得注意的題材狀態轉換。" />
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
          <SectionHeading id="rotation-title" eyebrow="CAPITAL ROTATION" title="快速升溫／快速退潮" description="用精簡清單看資金正在往哪裡移動。" />
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
            <SectionHeading id="opportunities-title" eyebrow="RESEARCH QUEUE" title="今日機會" description="只呈現研究入口，不在首頁完成推薦分析。" link={{ label: "查看更多", href: "/opportunities" }} />
            <div className="tp-home-opportunity-list">
              {opportunities.map((item) => <Link href="/opportunities" key={item.name}><div><strong>{item.name}</strong><span>{item.note}</span></div><b>{item.count}</b><ChevronRight size={16} aria-hidden="true" /></Link>)}
            </div>
          </Card>
        </section>
      </div>
    </PageContainer>
  );
}
