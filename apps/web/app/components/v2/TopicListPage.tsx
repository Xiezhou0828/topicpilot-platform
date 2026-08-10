"use client";

import Link from "next/link";
import { ArrowDownRight, ArrowRight, ArrowUpRight, ChevronDown, ChevronRight, Layers3, Search, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchTopicRotation, fetchTopics, scoreLabel, type TopicResource, type TopicRotationResource, type TopicSummary } from "../../lib/topic-api";
import { getTopicOverviewMeta, PREVIEW_LABEL, type TopicDirection, type TopicGrade, type TopicOverviewMeta, type TopicRotationEvent } from "../../lib/topic-preview";
import { AppShell, Card, DataState, EmptyState, PageContainer, Skeleton } from "./V2Foundation";

type DirectionFilter = "全部" | "走強" | "走弱";
type GradeFilter = "全部" | TopicGrade;
type OverviewTopic = TopicSummary & { meta: TopicOverviewMeta };

const GRADE_LANES: Array<{ grade: TopicGrade; label: string; note: string }> = [
  { grade: "S", label: "S 級", note: "市場主線" },
  { grade: "A", label: "A 級", note: "重點觀察" },
  { grade: "B", label: "B 級", note: "題材擴散" },
  { grade: "D", label: "D 級", note: "等待確認" },
];

function gradeClass(grade: string | null): string {
  return `tp-grade-${(grade ?? "unknown").toLowerCase()}`;
}

function directionIcon(direction: TopicDirection) {
  if (direction === "up") return <ArrowUpRight size={16} aria-hidden="true" />;
  if (direction === "down") return <ArrowDownRight size={16} aria-hidden="true" />;
  return <ArrowRight size={16} aria-hidden="true" />;
}

function directionSymbol(direction: TopicDirection): string {
  return direction === "up" ? "↑" : direction === "down" ? "↓" : "→";
}

function isMarketTopic(topic: TopicSummary): boolean {
  return topic.topicType !== "MAJOR_GROUP";
}

function filterByDirection(topic: OverviewTopic, filter: DirectionFilter): boolean {
  return filter === "全部" || (filter === "走強" ? topic.meta.direction === "up" : topic.meta.direction === "down");
}

function PreviewBadge() {
  return <span className="tp-preview-badge">{PREVIEW_LABEL}</span>;
}

function KanbanTopicCard({ topic }: { topic: OverviewTopic }) {
  const grade = topic.meta.laneGrade;
  return <Link href={`/topics/${topic.slug}`} className={`tp-topic-kanban-card tp-topic-direction--${topic.meta.direction} ${gradeClass(grade)}`}>
    <span className="tp-topic-direction-rail" aria-hidden="true" />
    <span className="tp-topic-kanban-card-top"><strong>{topic.name}</strong><span className="tp-topic-direction-mark" aria-label={`今日方向 ${topic.meta.directionLabel}`}>{directionIcon(topic.meta.direction)}<b>{topic.meta.directionSymbol}</b></span></span>
    <span className="tp-topic-kanban-score"><small>今日題材分數</small><b>{scoreLabel(topic.score)}</b></span>
    <span className="tp-topic-kanban-drill">深入研究 <ChevronRight size={15} aria-hidden="true" /></span>
  </Link>;
}

function RotationRow({ event }: { event: TopicRotationEvent }) {
  return <Link href={`/topics/${event.topicSlug}`} className={`tp-topic-rotation-row tp-topic-direction--${event.direction}`}>
    <time>{event.timeLabel}</time>
    <span className="tp-topic-rotation-direction" aria-label={event.direction === "up" ? "走強" : event.direction === "down" ? "走弱" : "持平"}>{directionSymbol(event.direction)}</span>
    <span className="tp-topic-rotation-copy"><b>{event.action}</b><small>{event.topicName} · {event.detail}</small></span>
    {event.toGrade && <span className={`tp-chip tp-grade-chip ${gradeClass(event.toGrade)}`}>{event.toGrade}</span>}
    <ChevronRight size={16} aria-hidden="true" />
  </Link>;
}

export default function TopicListPage() {
  const [resource, setResource] = useState<TopicResource<TopicSummary[]> | null>(null);
  const [rotationResource, setRotationResource] = useState<TopicRotationResource | null>(null);
  const [query, setQuery] = useState("");
  const [directionFilter, setDirectionFilter] = useState<DirectionFilter>("全部");
  const [gradeFilter, setGradeFilter] = useState<GradeFilter>("全部");
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [openGroups, setOpenGroups] = useState<Set<string>>(new Set());

  useEffect(() => {
    let active = true;
    Promise.all([fetchTopics(), fetchTopicRotation()]).then(([topics, rotation]) => {
      if (!active) return;
      setResource(topics);
      setRotationResource(rotation);
    });
    return () => { active = false; };
  }, []);

  const overviewTopics = useMemo<OverviewTopic[]>(() => (resource?.data ?? [])
    .filter(isMarketTopic)
    .map((topic) => ({ ...topic, meta: getTopicOverviewMeta(topic, resource?.source !== "api") })), [resource]);

  const normalizedQuery = query.trim().toLocaleLowerCase("zh-TW");
  const filteredTopics = useMemo(() => overviewTopics.filter((topic) => {
    const text = `${topic.name} ${topic.slug} ${topic.meta.groupName ?? ""}`.toLocaleLowerCase("zh-TW");
    const matchesQuery = !normalizedQuery || text.includes(normalizedQuery);
    return matchesQuery && filterByDirection(topic, directionFilter) && (gradeFilter === "全部" || topic.meta.laneGrade === gradeFilter);
  }), [directionFilter, gradeFilter, normalizedQuery, overviewTopics]);

  const lanes = useMemo(() => GRADE_LANES.map((lane) => ({ ...lane, topics: filteredTopics.filter((topic) => topic.meta.laneGrade === lane.grade) })), [filteredTopics]);
  const groupRows = useMemo(() => {
    const groups = new Map<string, OverviewTopic[]>();
    overviewTopics.forEach((topic) => {
      const group = topic.meta.groupName ?? "其他題材";
      groups.set(group, [...(groups.get(group) ?? []), topic]);
    });
    return Array.from(groups.entries()).sort(([a], [b]) => a.localeCompare(b, "zh-TW"));
  }, [overviewTopics]);
  const rotationEvents = rotationResource?.data ?? [];
  const previewMode = resource?.source !== "api" || rotationResource?.source !== "api";

  function toggleFavorite(slug: string) {
    setFavorites((current) => {
      const next = new Set(current);
      if (next.has(slug)) next.delete(slug); else next.add(slug);
      return next;
    });
  }

  function toggleGroup(group: string) {
    setOpenGroups((current) => {
      const next = new Set(current);
      if (next.has(group)) next.delete(group); else next.add(group);
      return next;
    });
  }

  return <AppShell currentPath="/topics"><PageContainer eyebrow="市場掃描" title="題材" description="10 秒看完整個市場今天的題材分布、等級與方向，再進入單一題材深入研究。" className="tp-topic-overview-page">
    <div className="tp-topic-overview-toolbar">
      <label className="tp-search-input"><Search size={18} aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜尋題材名稱或代號" /></label>
      <div className="tp-topic-filter-group" role="group" aria-label="今日方向篩選"><span>方向</span>{(["全部", "走強", "走弱"] as DirectionFilter[]).map((item) => <button type="button" key={item} className={directionFilter === item ? "is-active" : ""} onClick={() => setDirectionFilter(item)}>{item}</button>)}</div>
      {previewMode ? <PreviewBadge /> : <DataState state="AVAILABLE" />}
    </div>

    {!resource && <Card className="tp-topic-data-card"><div className="tp-topic-loading-row"><Skeleton /><Skeleton /><Skeleton /></div><Skeleton className="tp-topic-loading-table" /></Card>}
    {resource?.data && <>
      <section className="tp-topic-kanban-section" aria-labelledby="topic-kanban-title">
        <div className="tp-topic-section-heading"><div><p className="tp-overline">MARKET SCAN</p><h2 id="topic-kanban-title">今日題材地圖</h2><p>按照 S/A/B/D 市場分類看今天所有題材；卡片只保留分數、方向與深入研究入口。</p></div><span className="tp-topic-scan-count">{filteredTopics.length} 個題材</span></div>
        <div className="tp-topic-kanban-board">{lanes.map((lane) => <section key={lane.grade} className={`tp-topic-kanban-lane tp-topic-kanban-lane--${lane.grade.toLowerCase()}`} aria-labelledby={`topic-lane-${lane.grade}`}>
          <header className="tp-topic-kanban-lane-header"><div><strong id={`topic-lane-${lane.grade}`}>{lane.label}</strong><span>{lane.note}</span></div><b>{lane.topics.length}</b></header>
          <div className="tp-topic-kanban-lane-cards">{lane.topics.length ? lane.topics.map((topic) => <KanbanTopicCard topic={topic} key={topic.slug} />) : <p className="tp-topic-kanban-empty">目前沒有符合條件的題材</p>}</div>
        </section>)}</div>
      </section>

      <section className="tp-topic-rotation-section" aria-labelledby="topic-rotation-title">
        <div className="tp-topic-section-heading"><div><p className="tp-overline">MARKET ROTATION</p><h2 id="topic-rotation-title">市場輪動</h2><p>依事件時間排序，快速看今天新增升溫、退潮與等級變化。</p></div>{rotationResource?.source === "api" ? <DataState state="AVAILABLE" /> : <PreviewBadge />}</div>
        <Card className="tp-topic-rotation-card"><div className="tp-topic-rotation-list">{rotationEvents.map((event) => <RotationRow event={event} key={event.id} />)}</div></Card>
      </section>

      <section className="tp-topic-groups-section" aria-labelledby="topic-groups-title">
        <div className="tp-topic-section-heading"><div><p className="tp-overline">BROWSE BY GROUP</p><h2 id="topic-groups-title">依大族群瀏覽</h2><p>收合或展開大族群，快速找到下一個要研究的子題材。</p></div><span className="tp-topic-scan-count">{groupRows.length} 個大族群</span></div>
        <div className="tp-topic-group-grid">{groupRows.map(([group, topics]) => { const isOpen = openGroups.has(group); return <section className={`tp-topic-group-card ${isOpen ? "is-open" : ""}`} key={group}>
          <button type="button" className="tp-topic-group-toggle" aria-expanded={isOpen} onClick={() => toggleGroup(group)}><span><Layers3 size={18} aria-hidden="true" /><strong>{group}</strong><small>{topics.length} 個題材</small></span><ChevronDown size={18} aria-hidden="true" /></button>
          {isOpen && <div className="tp-topic-group-children">{topics.map((topic) => <Link href={`/topics/${topic.slug}`} className="tp-topic-group-child" key={topic.slug}><span><b>{topic.name}</b><small>{topic.meta.directionLabel}</small></span><span className="tp-topic-group-child-score">{scoreLabel(topic.score)}</span><span className={`tp-chip tp-grade-chip ${gradeClass(topic.meta.laneGrade)}`}>{topic.meta.laneGrade ?? "—"}</span><ChevronRight size={15} aria-hidden="true" /></Link>)}</div>}
        </section>; })}</div>
      </section>

      <section className="tp-topic-overview-list-section" aria-labelledby="topic-list-title">
        <div className="tp-topic-section-heading"><div><p className="tp-overline">FULL TOPIC LIST</p><h2 id="topic-list-title">全部題材</h2><p>搜尋、收藏與篩選後，點擊任一列進入 Topic Detail。</p></div><span className="tp-topic-scan-count">顯示 {filteredTopics.length} / {overviewTopics.length}</span></div>
        <Card className="tp-topic-overview-list-card"><div className="tp-topic-grade-filters" role="group" aria-label="等級篩選">{(["全部", "S", "A", "B", "D"] as GradeFilter[]).map((item) => <button type="button" key={item} className={gradeFilter === item ? "is-active" : ""} onClick={() => setGradeFilter(item)}>{item === "全部" ? "全部等級" : `${item} 級`}</button>)}</div>
          <div className="tp-topic-overview-list-head" aria-hidden="true"><span>題材名稱</span><span>大族群</span><span>等級</span><span>今日分數</span><span>今日方向</span><span>股票數</span><span>收藏</span></div>
          <div className="tp-topic-overview-list-items">{filteredTopics.map((topic) => <div className="tp-topic-overview-list-row" key={topic.slug}><Link href={`/topics/${topic.slug}`} className="tp-topic-overview-list-link"><span className="tp-topic-overview-name"><b>{topic.name}</b><small>{topic.slug}</small></span><span>{topic.meta.groupName ?? "其他題材"}</span><span className={`tp-chip tp-grade-chip ${gradeClass(topic.meta.laneGrade)}`}>{topic.meta.laneGrade ?? "—"}</span><strong className="tp-topic-overview-score">{scoreLabel(topic.score)}</strong><span className={`tp-topic-overview-direction tp-topic-direction--${topic.meta.direction}`}><span>{topic.meta.directionSymbol}</span>{topic.meta.directionLabel}</span><span className="tp-topic-overview-count">{topic.constituentCount} 檔</span><ChevronRight size={16} aria-hidden="true" /></Link><button type="button" className={`tp-topic-row-star ${favorites.has(topic.slug) ? "is-active" : ""}`} aria-label={favorites.has(topic.slug) ? `取消收藏 ${topic.name}` : `收藏 ${topic.name}`} aria-pressed={favorites.has(topic.slug)} onClick={() => toggleFavorite(topic.slug)}><Star size={18} fill={favorites.has(topic.slug) ? "currentColor" : "none"} aria-hidden="true" /></button></div>)}</div>
          {filteredTopics.length === 0 && <EmptyState title="找不到符合條件的題材" description="調整搜尋文字或篩選條件後再試一次。" />}
        </Card>
      </section>
    </>}
  </PageContainer></AppShell>;
}
