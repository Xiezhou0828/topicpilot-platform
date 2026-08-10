"use client";

import Link from "next/link";
import {
  ArrowDownRight,
  ArrowUpRight,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Layers3,
  Newspaper,
  Star,
  X,
} from "lucide-react";
import { useState } from "react";
import { AppShell, Card, GradeChip, PageContainer, RoleChip } from "./V2Foundation";

type StockRole = "代表股" | "核心股" | "關聯股";

type MockStock = {
  code: string;
  name: string;
  price: string;
  change: string;
  tone: "up" | "down";
  role: StockRole;
  note: string;
};

type MockTopic = {
  slug: string;
  parent: string;
  group: string;
  name: string;
  grade: string;
  strength: string;
  state: string;
  day: string;
  stockCount: string;
  summary: string;
  lifecycle: {
    current: string;
    entered: string;
    duration: string;
    segments: Array<{ stage: string; date: string; duration: string; active?: boolean }>;
  };
  events: Array<{ date: string; title: string; detail: string; tone: "brand" | "up" | "down" }>;
  stocks: Record<StockRole, MockStock[]>;
  news: Array<{ time: string; title: string; source: string; detail: string }>;
  related: Array<{ slug: string; name: string; state: string; strength: string; tone: "warm" | "neutral" | "soft" }>;
  heatmap: Array<{ name: string; value: string; span: number; tone: "strong" | "medium" | "light" | "quiet" }>;
};

const topicMocks: Record<string, MockTopic> = {
  "ai-server": {
    slug: "ai-server",
    parent: "電子",
    group: "AI",
    name: "AI伺服器",
    grade: "S",
    strength: "92",
    state: "全面走強",
    day: "Day 4",
    stockCount: "14 檔",
    summary: "目前仍為市場主線，量價同步、資金集中。代表股維持強勢，今日題材等級維持 S。",
    lifecycle: {
      current: "主升",
      entered: "8/06 進入",
      duration: "已持續 4 個交易日",
      segments: [
        { stage: "萌芽", date: "7/01", duration: "2 日" },
        { stage: "發酵", date: "7/03", duration: "3 日" },
        { stage: "主升", date: "8/06", duration: "4 日", active: true },
        { stage: "高檔整理", date: "—", duration: "尚未進入" },
        { stage: "退潮", date: "—", duration: "尚未進入" },
      ],
    },
    events: [
      { date: "7/01", title: "題材開始聚焦", detail: "伺服器供應鏈出現第一批同步轉強個股。", tone: "brand" },
      { date: "7/03", title: "升至 A", detail: "代表股量價同步，核心成員開始擴散。", tone: "up" },
      { date: "7/06", title: "升至 S", detail: "市場主線確立，題材強度與參與度同步上升。", tone: "up" },
      { date: "今天", title: "維持主升", detail: "盤中仍有資金集中，暫未出現主線退出訊號。", tone: "brand" },
    ],
    stocks: {
      代表股: [
        { code: "2382", name: "廣達", price: "312.50", change: "+3.20%", tone: "up", role: "代表股", note: "主線維持強勢" },
        { code: "2317", name: "鴻海", price: "198.00", change: "+1.54%", tone: "up", role: "代表股", note: "量能同步放大" },
      ],
      核心股: [
        { code: "6669", name: "緯穎", price: "2,385.00", change: "+2.80%", tone: "up", role: "核心股", note: "高檔量價穩定" },
        { code: "3231", name: "緯創", price: "128.50", change: "+2.39%", tone: "up", role: "核心股", note: "核心成員同步" },
      ],
      關聯股: [
        { code: "3017", name: "奇鋐", price: "742.00", change: "+1.78%", tone: "up", role: "關聯股", note: "散熱需求延伸" },
        { code: "2313", name: "華通", price: "82.40", change: "-0.60%", tone: "down", role: "關聯股", note: "族群內部略有分歧" },
      ],
    },
    news: [
      { time: "10:32", title: "伺服器供應鏈維持量價同步", source: "市場快訊", detail: "代表股與核心成員的成交動能仍高於近五日均值。" },
      { time: "09:48", title: "雲端資本支出預期支撐需求", source: "產業摘要", detail: "本則僅作為題材脈絡，未形成額外推薦結論。" },
      { time: "昨日", title: "散熱與高速傳輸出現擴散", source: "盤後整理", detail: "關聯股參與度提高，但角色仍低於核心成員。" },
    ],
    related: [
      { slug: "cpo", name: "CPO", state: "開始轉強", strength: "78", tone: "warm" },
      { slug: "high-speed-transmission", name: "高速傳輸", state: "量能回流", strength: "74", tone: "neutral" },
      { slug: "bbu", name: "BBU", state: "高檔整理", strength: "66", tone: "soft" },
    ],
    heatmap: [
      { name: "AI伺服器", value: "92", span: 5, tone: "strong" },
      { name: "CPO", value: "78", span: 3, tone: "medium" },
      { name: "高速傳輸", value: "74", span: 3, tone: "medium" },
      { name: "BBU", value: "66", span: 2, tone: "light" },
      { name: "散熱", value: "61", span: 2, tone: "light" },
      { name: "PCB", value: "54", span: 2, tone: "quiet" },
    ],
  },
};

const fallbackTopic = topicMocks["ai-server"];
const roleOrder: StockRole[] = ["代表股", "核心股", "關聯股"];

function getTopic(slug: string): MockTopic {
  if (topicMocks[slug]) return topicMocks[slug];
  return { ...fallbackTopic, slug, name: slug === "bbu" ? "BBU" : slug === "cpo" ? "CPO" : fallbackTopic.name };
}

function TopicSectionHeading({ title, description, action }: { title: string; description?: string; action?: React.ReactNode }) {
  return (
    <div className="tp-topic-section-heading">
      <div>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {action}
    </div>
  );
}

function ChangeValue({ value, tone }: { value: string; tone: "up" | "down" }) {
  const Icon = tone === "up" ? ArrowUpRight : ArrowDownRight;
  return <span className={`tp-topic-change tp-topic-change--${tone}`}><Icon size={14} aria-hidden="true" />{value}</span>;
}

export default function TopicDetailPage({ slug }: { slug: string }) {
  const topic = getTopic(slug);
  const [favorite, setFavorite] = useState(false);
  const [newsOpen, setNewsOpen] = useState(false);
  const [selectedStock, setSelectedStock] = useState<MockStock | null>(null);

  return (
    <AppShell currentPath="/topics">
      <PageContainer className="tp-topic-page" title={topic.name} hideHeader>
        <div className="tp-topic-detail-page">
      <header className="tp-topic-identity">
        <nav className="tp-topic-breadcrumb" aria-label="題材階層">
          <Link href="/topics">題材</Link><span aria-hidden="true">›</span><Link href="/topics">{topic.parent}</Link><span aria-hidden="true">›</span><Link href="/topics">{topic.group}</Link><span aria-hidden="true">›</span><strong>{topic.name}</strong>
        </nav>
        <div className="tp-topic-title-row">
          <div>
            <p className="tp-overline">TOPIC DETAIL · MOCK PROTOTYPE</p>
            <h1>{topic.name}</h1>
          </div>
          <button type="button" className={`tp-topic-favorite ${favorite ? "is-active" : ""}`} aria-pressed={favorite} onClick={() => setFavorite((value) => !value)}>
            <Star size={18} fill={favorite ? "currentColor" : "none"} aria-hidden="true" />
            {favorite ? "已收藏題材" : "收藏題材"}
          </button>
        </div>
        <div className="tp-topic-meta-row">
          <GradeChip grade={topic.grade} />
          <span><b>題材強度</b> {topic.strength}</span>
          <span><b>生命週期</b> {topic.lifecycle.current} · {topic.day}</span>
          <span><b>股票數</b> {topic.stockCount}</span>
          <span className="tp-topic-mock-label">Mock Data · 10:48</span>
        </div>
        <p className="tp-topic-summary">{topic.summary}</p>
      </header>

      <div className="tp-topic-content">
        <section aria-labelledby="lifecycle-title">
          <Card className="tp-topic-lifecycle-card">
            <TopicSectionHeading title="題材生命圖" description="用階段與持續天數理解題材目前走到哪裡。" />
            <div className="tp-topic-lifecycle-current"><span>目前階段</span><strong>{topic.lifecycle.current}</strong><b>{topic.day}</b><span>{topic.lifecycle.entered} · {topic.lifecycle.duration}</span></div>
            <ol id="lifecycle-title" className="tp-topic-lifecycle-track">
              {topic.lifecycle.segments.map((segment) => <li className={segment.active ? "is-active" : ""} key={segment.stage}><span className="tp-topic-lifecycle-dot" aria-hidden="true" /><strong>{segment.stage}</strong><small>{segment.date}</small><em>{segment.duration}</em></li>)}
            </ol>
          </Card>
        </section>

        <section aria-labelledby="history-title">
          <Card className="tp-topic-history-card">
            <TopicSectionHeading title="題材歷程" description="只保留影響研究判斷的重要節點。" />
            <ol id="history-title" className="tp-topic-history-list">
              {topic.events.map((event) => <li key={`${event.date}-${event.title}`}><time>{event.date}</time><span className={`tp-topic-history-marker tp-topic-history-marker--${event.tone}`} aria-hidden="true" /><div><strong>{event.title}</strong><p>{event.detail}</p></div></li>)}
            </ol>
          </Card>
        </section>

        <section aria-labelledby="stocks-title">
          <TopicSectionHeading title="題材內股票" description="依代表股、核心股、關聯股排序；點擊股票開啟 Stock Detail Drawer。" />
          <div id="stocks-title" className="tp-topic-role-grid">
            {roleOrder.map((role) => <Card className={`tp-topic-role-card tp-topic-role-card--${role === "代表股" ? "lead" : role === "核心股" ? "core" : "related"}`} key={role}>
              <div className="tp-topic-role-heading"><div><p className="tp-overline">{role === "代表股" ? "LEADER SET" : role === "核心股" ? "CORE MEMBERS" : "RELATED MEMBERS"}</p><h3>{role}</h3></div><RoleChip>{topic.stocks[role].length} 檔</RoleChip></div>
              <div className="tp-topic-stock-list">
                {topic.stocks[role].map((stock) => <button type="button" className="tp-topic-stock-row" key={stock.code} onClick={() => setSelectedStock(stock)}>
                  <span className="tp-topic-stock-identity"><b>{stock.name}</b><small>{stock.code} · {stock.note}</small></span>
                  <span className="tp-topic-stock-price"><b>{stock.price}</b><ChangeValue value={stock.change} tone={stock.tone} /></span>
                  <ChevronRight size={16} aria-hidden="true" />
                </button>)}
              </div>
            </Card>)}
          </div>
        </section>

        <section aria-labelledby="news-title">
          <Card className="tp-topic-news-card">
            <button type="button" className="tp-topic-collapse-trigger" aria-expanded={newsOpen} onClick={() => setNewsOpen((value) => !value)}><span><Newspaper size={18} aria-hidden="true" /><span><b id="news-title">題材新聞</b><small>相關脈絡與證據摘要，預設收合</small></span></span><ChevronDown className={newsOpen ? "is-open" : ""} size={18} aria-hidden="true" /></button>
            {newsOpen && <div className="tp-topic-news-list">{topic.news.map((item) => <article key={`${item.time}-${item.title}`}><time>{item.time}</time><div><strong>{item.title}</strong><span>{item.source}</span><p>{item.detail}</p></div><ExternalLink size={16} aria-hidden="true" /></article>)}</div>}
          </Card>
        </section>

        <section aria-labelledby="related-title">
          <TopicSectionHeading title="題材關聯" description="從市場故事的相鄰位置切換研究入口。" />
          <div id="related-title" className="tp-topic-related-grid">
            {topic.related.map((related) => <Link href={`/topics/${related.slug}`} className={`tp-topic-related-card tp-topic-related-card--${related.tone}`} key={related.slug}><span className="tp-topic-related-strength">{related.strength}</span><div><strong>{related.name}</strong><span>{related.state}</span></div><ChevronRight size={18} aria-hidden="true" /></Link>)}
          </div>
        </section>

        <section aria-labelledby="heatmap-title">
          <Card className="tp-topic-heatmap-card">
            <TopicSectionHeading title="市場題材熱圖" description="Mock Data：以相對強度與市場關聯度呈現題材位置。" />
            <div id="heatmap-title" className="tp-topic-heatmap" aria-label="市場題材熱圖">{topic.heatmap.map((cell) => <div className={`tp-topic-heatmap-cell tp-topic-heatmap-cell--${cell.tone}`} style={{ gridColumn: `span ${cell.span}` }} key={cell.name}><strong>{cell.name}</strong><span>{cell.value}</span></div>)}</div>
          </Card>
        </section>
      </div>

      {selectedStock && <div className="tp-topic-drawer-layer" role="presentation" onClick={() => setSelectedStock(null)}><aside className="tp-topic-stock-drawer" role="dialog" aria-modal="true" aria-labelledby="stock-drawer-title" onClick={(event) => event.stopPropagation()}>
        <div className="tp-topic-drawer-header"><div><p className="tp-overline">STOCK DETAIL · MOCK</p><h2 id="stock-drawer-title">{selectedStock.name}</h2><span>{selectedStock.code} · {selectedStock.role}</span></div><button type="button" className="tp-icon-button" aria-label="關閉股票詳情" onClick={() => setSelectedStock(null)}><X size={20} aria-hidden="true" /></button></div>
        <div className="tp-topic-drawer-price"><strong>{selectedStock.price}</strong><ChangeValue value={selectedStock.change} tone={selectedStock.tone} /></div>
        <div className="tp-topic-drawer-grid"><div><span>所屬題材</span><b>{topic.name}</b></div><div><span>題材角色</span><b>{selectedStock.role}</b></div><div><span>今日狀態</span><b>{selectedStock.note}</b></div><div><span>資料狀態</span><b>Mock · 10:48</b></div></div>
        <div className="tp-topic-drawer-note"><Layers3 size={18} aria-hidden="true" /><p>這是 Stock Detail Drawer 的 UI Prototype。正式版本將沿用股票頁的共用個股圖鑑與資料狀態。</p></div>
        <Link href={`/stocks/${selectedStock.code}`} className="tp-topic-drawer-link">前往股票頁 <ChevronRight size={16} aria-hidden="true" /></Link>
      </aside></div>}
        </div>
      </PageContainer>
    </AppShell>
  );
}
