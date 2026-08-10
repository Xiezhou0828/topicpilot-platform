"use client";

import Link from "next/link";
import { ChevronRight, Layers3, Search, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchTopics, scoreLabel, type TopicResource, type TopicSummary } from "../../lib/topic-api";
import { AppShell, Card, DataState, EmptyState, PageContainer, Skeleton } from "./V2Foundation";

type TopicFilter = "全部" | "升溫" | "退潮";
type HeatmapTopic = TopicSummary & { span: number; rows: number };

function filterMatches(topic: TopicSummary, filter: TopicFilter): boolean {
  if (filter === "全部") return true;
  const state = `${topic.readableState} ${topic.strengthState ?? ""}`.toUpperCase();
  return filter === "升溫" ? /升溫|WARM|STRENGTH|BROAD/.test(state) : /退潮|降溫|COOL|DIVERG|WEAK/.test(state);
}

function gradeClass(grade: string | null): string {
  return `tp-grade-${(grade ?? "unknown").toLowerCase()}`;
}

function buildHeatmap(topics: TopicSummary[]): HeatmapTopic[] {
  const scored = topics.map((topic) => topic.score).filter((score): score is number => score !== null);
  const min = scored.length ? Math.min(...scored) : 0;
  const max = scored.length ? Math.max(...scored) : 1;
  return topics.slice(0, 12).map((topic, index) => {
    const ratio = topic.score === null || max === min ? 0.5 : (topic.score - min) / (max - min);
    return { ...topic, span: Math.max(3, Math.min(8, Math.round(3 + ratio * 5))), rows: index === 0 ? 2 : 1 };
  });
}

function PreviewBadge() {
  return <span className="tp-preview-badge">Preview · 等待正式 Read Model</span>;
}

export default function TopicListPage() {
  const [resource, setResource] = useState<TopicResource<TopicSummary[]> | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<TopicFilter>("全部");
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [hoveredSlug, setHoveredSlug] = useState<string | null>(null);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchTopics().then((next) => { if (active) setResource(next); });
    return () => { active = false; };
  }, []);

  const topics = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("zh-TW");
    return (resource?.data ?? []).filter((topic) => {
      const matchesQuery = !normalized || `${topic.name} ${topic.slug} ${topic.groupName ?? ""}`.toLocaleLowerCase("zh-TW").includes(normalized);
      return matchesQuery && filterMatches(topic, filter);
    });
  }, [filter, query, resource]);
  const heatmapTopics = useMemo(() => buildHeatmap(resource?.data ?? []), [resource]);

  function toggleFavorite(slug: string) {
    setFavorites((current) => {
      const next = new Set(current);
      if (next.has(slug)) next.delete(slug); else next.add(slug);
      return next;
    });
  }

  return <AppShell currentPath="/topics"><PageContainer eyebrow="題材探索" title="題材" description="先看市場題材的強弱與狀態，再進入單一題材的完整研究脈絡。" className="tp-topic-list-page">
    <div className="tp-topic-list-toolbar">
      <label className="tp-search-input"><Search size={18} aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜尋題材名稱或代號" /></label>
      <div className="tp-segmented" role="tablist" aria-label="題材篩選">{(["全部", "升溫", "退潮"] as TopicFilter[]).map((item) => <button type="button" key={item} className={filter === item ? "is-active" : ""} onClick={() => setFilter(item)}>{item}</button>)}</div>
      {resource?.source === "synthetic-snapshot" && <PreviewBadge />}
      {resource?.source === "api" && <DataState state="AVAILABLE" />}
    </div>

    {resource?.source === "unavailable" && <Card className="tp-topic-data-card"><DataState state="UNAVAILABLE" /><EmptyState title="題材資料目前無法取得" description={resource.error ?? "請確認 FastAPI read model 是否已啟動。"} /></Card>}
    {!resource && <Card className="tp-topic-data-card"><div className="tp-topic-loading-row"><Skeleton /><Skeleton /><Skeleton /></div><Skeleton className="tp-topic-loading-table" /></Card>}
    {resource?.data && <>
      <section className="tp-topic-list-summary" aria-label="題材清單摘要"><div><span>目前題材</span><strong>{resource.data.length}</strong></div><div><span>強勢題材</span><strong>{resource.data.filter((topic) => topic.grade === "S" || topic.grade === "A").length}</strong></div><div><span>目前顯示</span><strong>{topics.length}</strong></div></section>
      <Card className="tp-topic-list-results"><div className="tp-topic-card-heading"><div><p className="tp-overline">題材排行</p><h2>題材清單</h2></div><span className="tp-muted">點擊任一題材進入詳情</span></div>
        <div className="tp-topic-list-items">{topics.map((topic) => <article key={topic.slug} className={`tp-topic-list-item ${hoveredSlug === topic.slug ? "is-hovered" : ""} ${selectedSlug === topic.slug ? "is-selected" : ""}`} onMouseEnter={() => setHoveredSlug(topic.slug)} onMouseLeave={() => setHoveredSlug(null)}>
          <Link className="tp-topic-list-item-link" href={`/topics/${topic.slug}`} onClick={() => setSelectedSlug(topic.slug)} aria-current={selectedSlug === topic.slug ? "page" : undefined}>
            <span className="tp-topic-list-icon" aria-hidden="true"><Layers3 size={18} /></span>
            <span className="tp-topic-list-main"><b>{topic.name}</b><small>{topic.groupName ?? "未分組"}</small></span>
            <span className="tp-topic-list-strength"><small>題材強度</small><strong>{scoreLabel(topic.score)}</strong></span>
            <span className={`tp-topic-state-chip ${topic.readableState === "資料待更新" ? "is-pending" : ""}`}>{topic.readableState}</span>
            <span className={`tp-chip tp-grade-chip ${gradeClass(topic.grade)}`}>{topic.grade ?? "—"}</span>
            <span className="tp-topic-list-count">{topic.constituentCount} 檔</span>
            <ChevronRight size={18} aria-hidden="true" />
          </Link>
          <button type="button" className={`tp-topic-row-star ${favorites.has(topic.slug) ? "is-active" : ""}`} aria-label={favorites.has(topic.slug) ? `取消收藏 ${topic.name}` : `收藏 ${topic.name}`} aria-pressed={favorites.has(topic.slug)} onClick={() => toggleFavorite(topic.slug)}><Star size={18} fill={favorites.has(topic.slug) ? "currentColor" : "none"} aria-hidden="true" /></button>
        </article>)}</div>
        {topics.length === 0 && <EmptyState title="找不到符合條件的題材" description="調整搜尋文字或篩選條件後再試一次。" />}
      </Card>

      <Card className="tp-topic-treemap-card"><div className="tp-topic-card-heading"><div><p className="tp-overline">市場題材地圖</p><h2>題材強度地圖</h2></div><PreviewBadge /></div><p className="tp-topic-map-note">矩形大小依目前題材強度分配，顏色依 S/A/B/D 保持中性層次；此區塊為產品預覽，等待正式 Heatmap read model。</p><div className="tp-topic-treemap-grid" aria-label="題材強度預覽地圖">{heatmapTopics.map((topic) => <Link key={topic.slug} href={`/topics/${topic.slug}`} className={`tp-topic-treemap-cell ${gradeClass(topic.grade)}`} style={{ gridColumn: `span ${topic.span}`, gridRow: `span ${topic.rows}` }}><span><b>{topic.name}</b><small>{topic.readableState}</small></span><strong>{scoreLabel(topic.score)}</strong></Link>)}</div></Card>
    </>}
  </PageContainer></AppShell>;
}
