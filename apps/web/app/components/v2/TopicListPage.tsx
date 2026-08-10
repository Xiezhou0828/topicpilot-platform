"use client";

import Link from "next/link";
import { ChevronRight, Search, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchTopics, scoreLabel, sourceLabel, type TopicResource, type TopicSummary } from "../../lib/topic-api";
import { AppShell, Card, DataState, EmptyState, PageContainer, Skeleton, Table } from "./V2Foundation";

type TopicFilter = "全部" | "升溫" | "退潮";

function filterMatches(topic: TopicSummary, filter: TopicFilter): boolean {
  if (filter === "全部") return true;
  const state = `${topic.readableState} ${topic.strengthState ?? ""}`.toUpperCase();
  return filter === "升溫" ? /升溫|WARM|STRENGTH|BROAD/.test(state) : /退潮|降溫|COOL|DIVERG|WEAK/.test(state);
}

export default function TopicListPage() {
  const [resource, setResource] = useState<TopicResource<TopicSummary[]> | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<TopicFilter>("全部");
  const [favorites, setFavorites] = useState<Set<string>>(new Set());

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

  function toggleFavorite(slug: string) {
    setFavorites((current) => {
      const next = new Set(current);
      if (next.has(slug)) next.delete(slug); else next.add(slug);
      return next;
    });
  }

  return (
    <AppShell currentPath="/topics">
      <PageContainer eyebrow="題材探索" title="題材" description="以正式 Topic read model 查看題材強弱，再進入單一題材的研究脈絡。" className="tp-topic-list-page">
        <div className="tp-topic-list-toolbar">
          <label className="tp-search-input"><Search size={18} aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜尋題材名稱或 slug" /></label>
          <div className="tp-segmented" role="tablist" aria-label="題材篩選">
            {(["全部", "升溫", "退潮"] as TopicFilter[]).map((item) => <button type="button" key={item} className={filter === item ? "is-active" : ""} onClick={() => setFilter(item)}>{item}</button>)}
          </div>
          {resource && <span className="tp-topic-source-note">{sourceLabel(resource.source)}</span>}
        </div>

        {resource?.source === "unavailable" && <Card className="tp-topic-data-card"><DataState state="UNAVAILABLE" /><EmptyState title="題材資料目前無法取得" description={resource.error ?? "請確認 FastAPI read model 是否已啟動。"} /></Card>}
        {!resource && <Card className="tp-topic-data-card"><div className="tp-topic-loading-row"><Skeleton /><Skeleton /><Skeleton /></div><Skeleton className="tp-topic-loading-table" /></Card>}
        {resource?.data && <>
          <Card className="tp-topic-table-card">
            <div className="tp-topic-card-heading"><div><p className="tp-overline">TOPIC RANKING</p><h2>題材清單</h2></div><DataState state={resource.source === "api" ? "AVAILABLE" : "STALE"} /></div>
            <Table>
              <thead><tr><th>題材</th><th>題材強度</th><th>等級</th><th>目前狀態</th><th>股票數</th><th aria-label="收藏" /></tr></thead>
              <tbody>{topics.map((topic) => <tr key={topic.slug}>
                <td><Link className="tp-topic-list-link" href={`/topics/${topic.slug}`}><span><b>{topic.name}</b><small>{topic.groupName ?? "未分組"} · {topic.slug}</small></span><ChevronRight size={16} aria-hidden="true" /></Link></td>
                <td><strong className="tp-topic-score">{scoreLabel(topic.score)}</strong></td>
                <td><span className="tp-chip tp-grade-chip">{topic.grade ?? "—"}</span></td>
                <td><span className="tp-topic-state-label">{topic.readableState}</span>{topic.strengthState && <small className="tp-topic-raw-state">{topic.strengthState}</small>}</td>
                <td>{topic.constituentCount} 檔</td>
                <td><button type="button" className={`tp-topic-row-star ${favorites.has(topic.slug) ? "is-active" : ""}`} aria-label={favorites.has(topic.slug) ? `取消收藏 ${topic.name}` : `收藏 ${topic.name}`} aria-pressed={favorites.has(topic.slug)} onClick={() => toggleFavorite(topic.slug)}><Star size={18} fill={favorites.has(topic.slug) ? "currentColor" : "none"} aria-hidden="true" /></button></td>
              </tr>)}</tbody>
            </Table>
            {topics.length === 0 && <EmptyState title="找不到符合條件的題材" description="調整搜尋文字或篩選條件後再試一次。" />}
          </Card>

          <Card className="tp-topic-heatmap-card tp-topic-list-heatmap">
            <div className="tp-topic-card-heading"><div><p className="tp-overline">MARKET PRESENCE</p><h2>題材地圖</h2></div><span className="tp-muted">矩形只呈現 read model 的相對瀏覽入口</span></div>
            <div className="tp-topic-list-heatmap-grid">{(resource.data ?? []).slice(0, 16).map((topic) => <Link key={topic.slug} href={`/topics/${topic.slug}`} className="tp-topic-list-heatmap-cell"><strong>{topic.name}</strong><span>{scoreLabel(topic.score)} · {topic.readableState}</span></Link>)}</div>
          </Card>
        </>}
      </PageContainer>
    </AppShell>
  );
}
