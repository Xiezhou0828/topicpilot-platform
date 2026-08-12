"use client";

import Link from "next/link";
import { ChevronRight, Star } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchTopic, scoreLabel, sourceLabel, type TopicConstituent, type TopicDetail as TopicData, type TopicResource } from "../../lib/topic-api";
import { getTopicPreview, PREVIEW_LABEL, type TopicPreview } from "../../lib/topic-preview";
import { AppShell, Card, DataState, EmptyState, GradeChip, PageContainer, RoleChip, Table } from "./V2Foundation";
import { StockEncyclopediaDrawer, type StockDrawerItem } from "./StockEncyclopediaDrawer";

const LIFECYCLE_STAGES = ["萌芽", "發酵", "主升", "成熟", "衰退"] as const;

function TopicSectionHeading({ title, description, badge = true }: { title: string; description?: string; badge?: boolean }) {
  return <div className="tp-topic-section-heading"><div><h2>{title}</h2>{description && <p>{description}</p>}</div>{badge && <PreviewBadge />}</div>;
}

function PreviewBadge() {
  return <span className="tp-preview-badge">{PREVIEW_LABEL}</span>;
}

function changeTone(value: number | null): "up" | "down" | null {
  return value === null ? null : value >= 0 ? "up" : "down";
}

function displayLifecycleStage(stage: string): (typeof LIFECYCLE_STAGES)[number] {
  if (stage === "高檔整理") return "成熟";
  if (stage === "退潮") return "衰退";
  return LIFECYCLE_STAGES.includes(stage as (typeof LIFECYCLE_STAGES)[number]) ? stage as (typeof LIFECYCLE_STAGES)[number] : "—" as (typeof LIFECYCLE_STAGES)[number];
}

function LifecyclePreview({ preview }: { preview: TopicPreview }) {
  const current = displayLifecycleStage(preview.lifecycle.current);
  return <Card className="tp-topic-detail-card tp-topic-detail-lifecycle-card"><TopicSectionHeading title="題材生命週期" description="以單一路徑閱讀題材目前位置；正式歷史與交易日欄位尚未接入。" /><div className="tp-topic-detail-lifecycle-current"><span>目前階段</span><strong>{current}</strong><b>{preview.lifecycle.entered}</b><span>交易日數尚未提供</span></div><ol className="tp-topic-detail-lifecycle-track">{LIFECYCLE_STAGES.map((stage) => { const segment = preview.lifecycle.segments.find((item) => displayLifecycleStage(item.stage) === stage); const active = current === stage; return <li className={active ? "is-active" : ""} key={stage}><span className="tp-topic-detail-lifecycle-dot" aria-hidden="true" /><strong>{stage}</strong><small>{segment?.entered ?? "—"}</small><em>{segment ? "交易日數尚未提供" : "—"}</em></li>; })}</ol></Card>;
}

function TopicStatusSection({ topic, preview, formal }: { topic: TopicData; preview: TopicPreview | null; formal: boolean }) {
  const items = formal
    ? topic.status.map((item) => ({ label: item.key, value: item.state ?? "尚未提供", note: item.state ? "正式語意" : String(item.evidence.reason ?? "正式規則尚未提供") }))
    : preview
      ? [{ label: "族群表現", value: preview.metrics.participation, note: "Preview · 等待正式 Read Model" }, { label: "領漲核心", value: preview.metrics.leaderDrive, note: "Preview · 等待正式 Read Model" }, { label: "動能擴散", value: preview.metrics.leaderConsistency, note: "Preview · 等待正式 Read Model" }]
      : [];
  return <Card className="tp-topic-detail-card tp-topic-status-card"><TopicSectionHeading title="題材狀態" description="三個研究視角保留為獨立欄位；狀態與證據由後端 Read Model 提供。" badge={!formal} /><div className="tp-topic-status-grid">{items.map((item) => <div key={item.label}><span>{item.label}</span><strong>{item.value}</strong><small>{item.note}</small></div>)}</div></Card>;
}

function TimelinePreview({ preview }: { preview: TopicPreview }) {
  return <Card className="tp-topic-preview-card tp-topic-history-card"><TopicSectionHeading title="題材歷程" description="只保留影響研究判斷的重要節點。" /><ol className="tp-topic-history-list">{preview.events.map((event) => <li key={`${event.date}-${event.title}`}><time>{event.date}</time><span className="tp-topic-history-marker" aria-hidden="true" /><div><strong>{event.title}</strong><p>{event.detail}</p></div></li>)}</ol></Card>;
}

function NewsPreview({ preview }: { preview: TopicPreview }) {
  return <Card className="tp-topic-preview-card tp-topic-news-preview"><TopicSectionHeading title="題材新聞" description="限定的相關脈絡與證據摘要，不建立通用新聞流。" /><div className="tp-topic-news-list">{preview.news.map((item) => <article key={`${item.time}-${item.title}`}><time>{item.time}</time><div><strong>{item.title}</strong><span>{item.source}</span></div></article>)}</div></Card>;
}

function RelatedPreview({ preview }: { preview: TopicPreview }) {
  return <Card className="tp-topic-preview-card"><TopicSectionHeading title="相關題材" description="從市場故事的相鄰位置切換研究入口。" /><div className="tp-topic-related-grid">{preview.related.map((related) => <Link href={`/topics/${related.slug}`} className="tp-topic-related-card" key={related.slug}><span className="tp-topic-related-strength">{related.strength}</span><div><strong>{related.name}</strong><span>{related.state}</span></div><span className="tp-chip tp-grade-chip">{related.grade}</span><ChevronRight size={18} aria-hidden="true" /></Link>)}</div></Card>;
}

function HeatmapPreview({ preview }: { preview: TopicPreview }) {
  return <Card className="tp-topic-preview-card tp-topic-detail-heatmap"><TopicSectionHeading title="市場題材熱圖" description="保留在下層作為 Preview 研究脈絡，不提升到 Topic Detail 首屏。" /><div className="tp-topic-treemap-grid" aria-label="市場題材強度預覽地圖">{preview.heatmap.map((cell) => <Link key={cell.slug} href={`/topics/${cell.slug}`} className="tp-topic-treemap-cell" style={{ gridColumn: `span ${cell.span}`, gridRow: `span ${cell.rows}` }}><span><b>{cell.name}</b><small>{cell.state}</small></span><strong>{scoreLabel(cell.strength)}</strong></Link>)}</div></Card>;
}

function stockDrawerItem(topic: TopicData, stock: TopicConstituent, source: TopicResource<TopicData>): StockDrawerItem {
  return {
    code: stock.code,
    name: stock.name,
    price: stock.price,
    changePct: stock.changePct,
    dataFreshness: stock.dataFreshness,
    dataDate: stock.dataDate,
    topics: [{ name: topic.name, role: stock.role }],
    mainTopic: { name: topic.name, grade: topic.grade, state: topic.readableState },
    isPreview: source.source === "synthetic-snapshot" || stock.dataFreshness === "Preview",
  };
}

export default function TopicDetailPage({ slug }: { slug: string }) {
  const [resource, setResource] = useState<TopicResource<TopicData> | null>(null);
  const [favorite, setFavorite] = useState(false);
  const [selectedStock, setSelectedStock] = useState<TopicConstituent | null>(null);

  useEffect(() => {
    let active = true;
    fetchTopic(slug).then((next) => { if (active) setResource(next); });
    return () => { active = false; };
  }, [slug]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => { if (event.key === "Escape" && selectedStock) setSelectedStock(null); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [selectedStock]);

  const topic = resource?.data;
  const preview = topic && resource?.source === "synthetic-snapshot" ? getTopicPreview(slug, topic.name, topic.score, topic.grade) : null;
  const stocks = resource?.data?.constituents ?? [];

  return <AppShell currentPath="/topics"><PageContainer className="tp-topic-page" title={topic?.name ?? slug} hideHeader><div className="tp-topic-detail-page">
    {!resource && <Card className="tp-topic-data-card"><DataState state="STALE" /><EmptyState title="正在載入題材資料" description="正在讀取 Topic read model。" /></Card>}
    {resource?.source === "unavailable" && <Card className="tp-topic-data-card"><DataState state="UNAVAILABLE" /><EmptyState title="題材資料目前無法取得" description={resource.error ?? "請確認 FastAPI read model 是否已啟動。"} /></Card>}
    {topic && <>
      <header className="tp-topic-identity">
        <nav className="tp-topic-breadcrumb" aria-label="題材階層"><Link href="/topics">題材</Link><span aria-hidden="true">›</span>{topic.groupName && <><span>{topic.groupName}</span><span aria-hidden="true">›</span></>}<strong>{topic.name}</strong></nav>
        <div className="tp-topic-title-row"><div><p className="tp-overline">題材詳情 · {sourceLabel(resource.source)}</p><h1>{topic.name}</h1></div><button type="button" className={`tp-topic-favorite ${favorite ? "is-active" : ""}`} aria-pressed={favorite} onClick={() => setFavorite((value) => !value)}><Star size={18} fill={favorite ? "currentColor" : "none"} aria-hidden="true" />{favorite ? "已收藏題材" : "收藏題材"}</button></div>
        <div className="tp-topic-meta-row"><GradeChip grade={topic.grade ?? "—"} /><span><b>題材強度</b> {scoreLabel(topic.score)}</span><span><b>目前狀態</b> {topic.readableState}</span><span><b>股票數</b> {topic.constituentCount} 檔</span><span><b>資料日期</b> {topic.dataDate ?? (resource.source === "api" ? "資料日期待補" : "Preview")}</span></div>
        {preview ? <div className="tp-topic-summary-preview"><PreviewBadge /><p>{preview.summary}</p></div> : <div className="tp-topic-summary-preview"><DataState state="UNAVAILABLE" /><p>題材 identity 已由正式 Catalog 提供；摘要與生命週期資料待正式 Read Model 累積。</p></div>}
      </header>

      <div className="tp-topic-content">{preview ? <LifecyclePreview preview={preview} /> : <Card className="tp-topic-detail-card tp-topic-detail-lifecycle-card"><TopicSectionHeading title="題材生命週期" description="正式生命週期資料尚未提供。" badge={false} /><EmptyState title="資料待累積" description="此題材仍存在於正式 Catalog，不因生命週期缺值而隱藏。" /></Card>}<TopicStatusSection topic={topic} preview={preview} formal={resource.source === "api" && topic.status.length === 3} />
        <section aria-labelledby="stocks-title"><TopicSectionHeading title="題材內股票" description="保留後端成分股順序；點擊任一列直接切換共用 Stock Encyclopedia Drawer。" badge={false} /><div className="tp-topic-stocks-workspace"><Card className="tp-topic-role-card tp-topic-stock-table-card"><div className="tp-topic-role-heading"><div><p className="tp-overline">題材成分股</p><h3 id="stocks-title">研究股票清單</h3></div><RoleChip>{stocks.length} 檔</RoleChip></div>{stocks.length ? <Table><thead><tr><th>股票／股號</th><th>題材角色</th><th>今日漲跌</th><th>題材表現</th><th>技術狀態</th><th>更新狀態</th><th>Action</th></tr></thead><tbody>{stocks.map((stock) => { const tone = changeTone(stock.changePct); const open = () => setSelectedStock(stock); return <tr key={stock.code} className="tp-topic-stock-table-row" role="button" tabIndex={0} onClick={open} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(); } }} aria-label={`查看${stock.name}股票圖鑑`}><td><span className="tp-topic-stock-identity"><b>{stock.name}</b><small>{stock.code}</small></span></td><td><RoleChip>{stock.role ?? "—"}</RoleChip></td><td>{stock.changePct === null ? <span className="tp-muted">—</span> : <span className={`tp-topic-change tp-topic-change--${tone}`}>{stock.changePct >= 0 ? "+" : ""}{stock.changePct.toFixed(2)}%</span>}</td><td>{stock.relativeTopicState ? <span>{stock.relativeTopicState}</span> : <span className="tp-topic-field-pending">尚未提供</span>}</td><td>{stock.technicalState ? <span>{stock.technicalState}</span> : <span className="tp-topic-field-pending">尚未提供</span>}</td><td>{stock.dataFreshness ?? "資料待更新"}</td><td><span className="tp-topic-row-action">查看 <ChevronRight size={16} aria-hidden="true" /></span></td></tr>; })}</tbody></Table> : <EmptyState title="目前沒有成分股資料" description="Topic read model 尚未回傳 constituent rows。" />}</Card>{selectedStock && <StockEncyclopediaDrawer presentation="inline" stock={stockDrawerItem(topic, selectedStock, resource)} onClose={() => setSelectedStock(null)} />}</div></section>
        {preview ? <><TimelinePreview preview={preview} /><NewsPreview preview={preview} /><RelatedPreview preview={preview} /><HeatmapPreview preview={preview} /></> : <Card className="tp-topic-preview-card"><TopicSectionHeading title="題材歷程與相關脈絡" description="等待正式事件、新聞與關聯題材 Read Model。" badge={false} /><EmptyState title="資料待累積" description="Production 不以 Preview 內容覆蓋正式題材 identity。" /></Card>}
      </div>
    </>}
  </div></PageContainer></AppShell>;
}
