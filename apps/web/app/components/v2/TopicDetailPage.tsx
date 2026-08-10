"use client";

import Link from "next/link";
import { ChevronRight, Layers3, Star, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchTopic, roleRank, scoreLabel, sourceLabel, type TopicConstituent, type TopicDetail as TopicData, type TopicResource } from "../../lib/topic-api";
import { getTopicPreview, type TopicPreview } from "../../lib/topic-preview";
import { AppShell, Card, DataState, EmptyState, GradeChip, PageContainer, RoleChip, Table } from "./V2Foundation";

function TopicSectionHeading({ title, description, badge = true }: { title: string; description?: string; badge?: boolean }) {
  return <div className="tp-topic-section-heading"><div><h2>{title}</h2>{description && <p>{description}</p>}</div>{badge && <span className="tp-preview-badge">Preview · 等待正式 Read Model</span>}</div>;
}

function PreviewBadge() {
  return <span className="tp-preview-badge">Preview · 等待正式 Read Model</span>;
}

function priceLabel(value: number | null): string {
  return value === null ? "—" : value.toLocaleString("zh-TW", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function changeTone(value: number | null): "up" | "down" | null {
  return value === null ? null : value >= 0 ? "up" : "down";
}

function gradeClass(grade: string | null): string {
  return `tp-grade-${(grade ?? "unknown").toLowerCase()}`;
}

function StockDrawer({ topic, stock, onClose }: { topic: TopicData; stock: TopicConstituent; onClose: () => void }) {
  const tone = changeTone(stock.changePct);
  return <div className="tp-topic-drawer-layer" role="presentation" onClick={onClose}><aside className="tp-topic-stock-drawer" role="dialog" aria-modal="true" aria-labelledby="stock-drawer-title" onClick={(event) => event.stopPropagation()}>
    <div className="tp-topic-drawer-header"><div><p className="tp-overline">個股詳情 · 共用抽屜</p><h2 id="stock-drawer-title">{stock.name}</h2><span>{stock.code}</span></div><button type="button" className="tp-icon-button" aria-label="關閉股票詳情" onClick={onClose}><X size={20} aria-hidden="true" /></button></div>
    <div className="tp-topic-drawer-price"><strong>{priceLabel(stock.price)}</strong>{stock.changePct === null ? <PreviewBadge /> : <span className={`tp-topic-change tp-topic-change--${tone}`}>{stock.changePct >= 0 ? "+" : ""}{stock.changePct.toFixed(2)}%</span>}</div>
    <div className="tp-topic-drawer-grid"><div><span>所屬題材</span><b>{topic.name}</b></div><div><span>題材角色</span><b><RoleChip>{stock.role}</RoleChip></b></div><div><span>資料日期</span><b>{stock.dataDate ?? "Preview"}</b></div><div><span>更新狀態</span><b>{stock.dataFreshness ?? "Preview"}</b></div></div>
    <div className="tp-topic-drawer-note"><Layers3 size={18} aria-hidden="true" /><p>正式 Topic API 目前只提供成分股身份；價格與即時更新欄位在 Preview Mode 以示意資料呈現，等待 Stock read model。</p></div>
    <Link href={`/stocks/${stock.code}`} className="tp-topic-drawer-link">前往股票頁 <ChevronRight size={16} aria-hidden="true" /></Link>
  </aside></div>;
}

function LifecyclePreview({ preview }: { preview: TopicPreview }) {
  return <Card className="tp-topic-preview-card tp-topic-lifecycle-preview"><TopicSectionHeading title="題材生命圖" description="用階段與持續天數理解題材目前走到哪裡。" /><div className="tp-topic-lifecycle-current"><span>目前階段</span><strong>{preview.lifecycle.current}</strong><b>{preview.lifecycle.entered}</b><span>{preview.lifecycle.duration}</span></div><ol className="tp-topic-lifecycle-track">{preview.lifecycle.segments.map((segment) => <li className={segment.active ? "is-active" : ""} key={segment.stage}><span className="tp-topic-lifecycle-dot" aria-hidden="true" /><strong>{segment.stage}</strong><small>{segment.entered}</small><em>{segment.duration}</em></li>)}</ol></Card>;
}

function PreviewMetrics({ preview }: { preview: TopicPreview }) {
  const items = [["族群參與度", preview.metrics.participation], ["龍頭帶動力", preview.metrics.leaderDrive], ["龍頭一致性", preview.metrics.leaderConsistency], ["資料完整度", preview.metrics.completeness], ["評分狀態", preview.metrics.scoring]];
  return <Card className="tp-topic-preview-card tp-topic-metrics-card"><TopicSectionHeading title="題材研究摘要" description="用可讀語言整理目前可用的研究訊號。" /><div className="tp-topic-metrics-grid">{items.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong>{value === "Preview" && <PreviewBadge />}</div>)}</div></Card>;
}

function TimelinePreview({ preview }: { preview: TopicPreview }) {
  return <Card className="tp-topic-preview-card tp-topic-history-card"><TopicSectionHeading title="題材歷程" description="只保留影響研究判斷的重要節點。" /><ol className="tp-topic-history-list">{preview.events.map((event) => <li key={`${event.date}-${event.title}`}><time>{event.date}</time><span className="tp-topic-history-marker" aria-hidden="true" /><div><strong>{event.title}</strong><p>{event.detail}</p></div></li>)}</ol></Card>;
}

function NewsPreview({ preview }: { preview: TopicPreview }) {
  return <Card className="tp-topic-preview-card tp-topic-news-preview"><TopicSectionHeading title="題材新聞" description="限定的相關脈絡與證據摘要，不建立通用新聞流。" /><div className="tp-topic-news-list">{preview.news.map((item) => <article key={`${item.time}-${item.title}`}><time>{item.time}</time><div><strong>{item.title}</strong><span>{item.source}</span></div></article>)}</div></Card>;
}

function RelatedPreview({ preview }: { preview: TopicPreview }) {
  return <Card className="tp-topic-preview-card"><TopicSectionHeading title="相關題材" description="從市場故事的相鄰位置切換研究入口。" /><div className="tp-topic-related-grid">{preview.related.map((related) => <Link href={`/topics/${related.slug}`} className="tp-topic-related-card" key={related.slug}><span className="tp-topic-related-strength">{related.strength}</span><div><strong>{related.name}</strong><span>{related.state}</span></div><span className={`tp-chip tp-grade-chip ${gradeClass(related.grade)}`}>{related.grade}</span><ChevronRight size={18} aria-hidden="true" /></Link>)}</div></Card>;
}

function HeatmapPreview({ preview }: { preview: TopicPreview }) {
  return <Card className="tp-topic-preview-card tp-topic-detail-heatmap"><TopicSectionHeading title="市場題材熱圖" description="矩形大小依 Preview 題材強度，顏色依 Grade 保持中性層次。" /><div className="tp-topic-treemap-grid" aria-label="市場題材強度預覽地圖">{preview.heatmap.map((cell) => <Link key={cell.slug} href={`/topics/${cell.slug}`} className={`tp-topic-treemap-cell ${gradeClass(cell.grade)}`} style={{ gridColumn: `span ${cell.span}`, gridRow: `span ${cell.rows}` }}><span><b>{cell.name}</b><small>{cell.state}</small></span><strong>{scoreLabel(cell.strength)}</strong></Link>)}</div></Card>;
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

  const stocks = useMemo(() => [...(resource?.data?.constituents ?? [])].sort((a, b) => roleRank(a.role) - roleRank(b.role) || a.code.localeCompare(b.code)), [resource]);
  const topic = resource?.data;
  const preview = topic ? getTopicPreview(slug, topic.name, topic.score, topic.grade) : null;

  return <AppShell currentPath="/topics"><PageContainer className="tp-topic-page" title={topic?.name ?? slug} hideHeader><div className="tp-topic-detail-page">
    {!resource && <Card className="tp-topic-data-card"><DataState state="STALE" /><EmptyState title="正在載入題材資料" description="正在讀取 Topic read model。" /></Card>}
    {resource?.source === "unavailable" && <Card className="tp-topic-data-card"><DataState state="UNAVAILABLE" /><EmptyState title="題材資料目前無法取得" description={resource.error ?? "請確認 FastAPI read model 是否已啟動。"} /></Card>}
    {topic && preview && <>
      <header className="tp-topic-identity"><nav className="tp-topic-breadcrumb" aria-label="題材階層"><Link href="/topics">題材</Link><span aria-hidden="true">›</span>{topic.groupName && <><span>{topic.groupName}</span><span aria-hidden="true">›</span></>}<strong>{topic.name}</strong></nav>
        <div className="tp-topic-title-row"><div><p className="tp-overline">題材詳情 · {sourceLabel(resource.source)}</p><h1>{topic.name}</h1></div><button type="button" className={`tp-topic-favorite ${favorite ? "is-active" : ""}`} aria-pressed={favorite} onClick={() => setFavorite((value) => !value)}><Star size={18} fill={favorite ? "currentColor" : "none"} aria-hidden="true" />{favorite ? "已收藏題材" : "收藏題材"}</button></div>
        <div className="tp-topic-meta-row"><GradeChip grade={topic.grade ?? "—"} /><span><b>題材強度</b> {scoreLabel(topic.score)}</span><span><b>目前狀態</b> {topic.readableState}</span><span><b>股票數</b> {topic.constituentCount} 檔</span><span><b>資料日期</b> {topic.dataDate ?? "Preview"}</span></div>
        <div className="tp-topic-summary-preview"><PreviewBadge /><p>{preview.summary}</p></div>
      </header>

      <div className="tp-topic-content"><LifecyclePreview preview={preview} /><PreviewMetrics preview={preview} />
        <section aria-labelledby="stocks-title"><TopicSectionHeading title="題材內股票" description="正式成分股依代表股、核心股、關聯股排序；點擊股票開啟共用 Stock Drawer。" badge={false} /><Card className="tp-topic-role-card tp-topic-stock-table-card"><div className="tp-topic-role-heading"><div><p className="tp-overline">題材成分股</p><h3 id="stocks-title">正式成分股清單</h3></div><RoleChip>{stocks.length} 檔</RoleChip></div>{stocks.length ? <Table><thead><tr><th>股票／股號</th><th>題材角色</th><th>現價</th><th>漲跌幅</th><th>更新狀態</th><th /></tr></thead><tbody>{stocks.map((stock) => { const tone = changeTone(stock.changePct); return <tr key={stock.code}><td><button type="button" className="tp-topic-stock-row" onClick={() => setSelectedStock(stock)}><span className="tp-topic-stock-identity"><b>{stock.name}</b><small>{stock.code}</small></span><ChevronRight size={16} aria-hidden="true" /></button></td><td><RoleChip>{stock.role}</RoleChip></td><td>{priceLabel(stock.price)}</td><td>{stock.changePct === null ? <span className="tp-muted">Preview</span> : <span className={`tp-topic-change tp-topic-change--${tone}`}>{stock.changePct >= 0 ? "+" : ""}{stock.changePct.toFixed(2)}%</span>}</td><td>{stock.dataFreshness ?? "Preview"}</td><td><ChevronRight size={16} aria-hidden="true" /></td></tr>; })}</tbody></Table> : <EmptyState title="目前沒有成分股資料" description="Topic read model 尚未回傳 constituent rows。" />}</Card></section>
        <TimelinePreview preview={preview} /><NewsPreview preview={preview} /><RelatedPreview preview={preview} /><HeatmapPreview preview={preview} />
      </div>
    </>}
  </div>{topic && selectedStock && <StockDrawer topic={topic} stock={selectedStock} onClose={() => setSelectedStock(null)} />}</PageContainer></AppShell>;
}
