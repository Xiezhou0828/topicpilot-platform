"use client";

import Link from "next/link";
import { ChevronDown, ChevronRight, Layers3, Search, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchTopics, scoreLabel, type TopicResource, type TopicSummary } from "../../lib/topic-api";
import { getTopicOverviewLifecycle, getTopicOverviewMeta, PREVIEW_LABEL, type TopicGrade, type TopicLifecycleStage, type TopicOverviewLifecycle, type TopicOverviewMeta } from "../../lib/topic-preview";
import { AppShell, Card, DataState, EmptyState, PageContainer, Skeleton } from "./V2Foundation";

type DirectionFilter = "全部" | "轉強" | "轉弱";
type GradeFilter = "全部" | TopicGrade;
type OverviewTopic = TopicSummary & { meta: TopicOverviewMeta };
type LifecycleTopic = { topic: OverviewTopic; lifecycle: TopicOverviewLifecycle };

const GRADE_LANES: Array<{ grade: TopicGrade; label: string }> = [
  { grade: "S", label: "S｜市場主線" },
  { grade: "A", label: "A｜重點觀察" },
  { grade: "B", label: "B｜輪動題材" },
  { grade: "D", label: "D｜等待確認" },
];

const LIFECYCLE_STAGES: TopicLifecycleStage[] = ["萌芽", "發酵", "主升", "高檔整理", "退潮", "觀察"];

function gradeClass(grade: string | null): string {
  return `tp-grade-${(grade ?? "unknown").toLowerCase()}`;
}

function isMarketTopic(topic: TopicSummary): boolean {
  return topic.topicType !== "MAJOR_GROUP";
}

function filterByDirection(topic: OverviewTopic, filter: DirectionFilter): boolean {
  return filter === "全部" || (filter === "轉強" ? topic.meta.direction === "up" : topic.meta.direction === "down");
}

function PreviewBadge() {
  return <span className="tp-preview-badge">{PREVIEW_LABEL}</span>;
}

function KanbanTopicCard({ topic }: { topic: OverviewTopic }) {
  const grade = topic.meta.laneGrade;
  return <Link href={`/topics/${topic.slug}`} className={`tp-topic-kanban-card tp-topic-direction--${topic.meta.direction} ${gradeClass(grade)}`}>
    <span className="tp-topic-direction-rail" aria-hidden="true" />
    <span className="tp-topic-kanban-card-top"><strong>{topic.name}</strong><span className="tp-topic-direction-mark" aria-label={`今日方向 ${topic.meta.directionLabel}`}>{topic.meta.directionSymbol}</span></span>
    <span className="tp-topic-kanban-score"><small>今日分數</small><b>{scoreLabel(topic.score)}</b></span>
    <span className="tp-topic-kanban-drill">深入研究 <ChevronRight size={14} aria-hidden="true" /></span>
  </Link>;
}

function LifecycleChip({ item }: { item: LifecycleTopic }) {
  return <Link href={`/topics/${item.topic.slug}`} className={`tp-topic-lifecycle-chip tp-topic-direction--${item.topic.meta.direction}`}>
    <span><b>{item.topic.name}</b><small>Day {item.lifecycle.day}</small></span>
    <strong>{scoreLabel(item.topic.score)}</strong>
  </Link>;
}

function TopicLifecycle({ topics }: { topics: OverviewTopic[] }) {
  const stageMap = useMemo(() => {
    const map = new Map<TopicLifecycleStage, LifecycleTopic[]>(LIFECYCLE_STAGES.map((stage) => [stage, []]));
    topics.forEach((topic) => {
      const lifecycle = getTopicOverviewLifecycle(topic.slug);
      map.set(lifecycle.stage, [...(map.get(lifecycle.stage) ?? []), { topic, lifecycle }]);
    });
    return map;
  }, [topics]);

  return <section className="tp-topic-lifecycle-section" aria-labelledby="topic-lifecycle-title">
    <div className="tp-topic-lifecycle-heading"><h2 id="topic-lifecycle-title">Topic Lifecycle</h2><PreviewBadge /></div>
    <div className="tp-topic-lifecycle-track">{LIFECYCLE_STAGES.map((stage) => <section className="tp-topic-lifecycle-stage" key={stage} aria-labelledby={`topic-stage-${stage}`}>
      <h3 id={`topic-stage-${stage}`}>{stage}</h3>
      <div className="tp-topic-lifecycle-items">{stageMap.get(stage)?.length ? stageMap.get(stage)?.map((item) => <LifecycleChip item={item} key={item.topic.slug} />) : <span className="tp-topic-lifecycle-empty">—</span>}</div>
    </section>)}</div>
  </section>;
}

export default function TopicListPage() {
  const [resource, setResource] = useState<TopicResource<TopicSummary[]> | null>(null);
  const [query, setQuery] = useState("");
  const [directionFilter, setDirectionFilter] = useState<DirectionFilter>("全部");
  const [gradeFilter, setGradeFilter] = useState<GradeFilter>("全部");
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [openGroups, setOpenGroups] = useState<Set<string>>(new Set());

  useEffect(() => {
    let active = true;
    fetchTopics().then((next) => { if (active) setResource(next); });
    return () => { active = false; };
  }, []);

  const overviewTopics = useMemo<OverviewTopic[]>(() => (resource?.data ?? [])
    .filter(isMarketTopic)
    .map((topic) => ({ ...topic, meta: getTopicOverviewMeta(topic, resource?.source !== "api") })), [resource]);
  const scanTopics = useMemo(() => overviewTopics.filter((topic) => filterByDirection(topic, directionFilter)), [directionFilter, overviewTopics]);
  const normalizedQuery = query.trim().toLocaleLowerCase("zh-TW");
  const filteredTopics = useMemo(() => scanTopics.filter((topic) => {
    const text = `${topic.name} ${topic.slug} ${topic.meta.groupName ?? ""}`.toLocaleLowerCase("zh-TW");
    return (!normalizedQuery || text.includes(normalizedQuery)) && (gradeFilter === "全部" || topic.meta.laneGrade === gradeFilter);
  }), [gradeFilter, normalizedQuery, scanTopics]);
  const lanes = useMemo(() => GRADE_LANES.map((lane) => ({ ...lane, topics: scanTopics.filter((topic) => topic.meta.laneGrade === lane.grade) })), [scanTopics]);
  const groupRows = useMemo(() => {
    const groups = new Map<string, OverviewTopic[]>();
    overviewTopics.forEach((topic) => {
      const group = topic.meta.groupName ?? "其他題材";
      groups.set(group, [...(groups.get(group) ?? []), topic]);
    });
    return Array.from(groups.entries()).sort(([a], [b]) => a.localeCompare(b, "zh-TW"));
  }, [overviewTopics]);
  const previewMode = resource?.source !== "api";

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

  return <AppShell currentPath="/topics"><PageContainer title="題材" className="tp-topic-overview-page">
    {!resource && <Card className="tp-topic-data-card"><div className="tp-topic-loading-row"><Skeleton /><Skeleton /><Skeleton /></div><Skeleton className="tp-topic-loading-table" /></Card>}
    {resource?.data && <>
      <section className="tp-topic-kanban-section" aria-labelledby="topic-kanban-title">
        <div className="tp-topic-section-heading tp-topic-map-heading"><div><h2 id="topic-kanban-title">今日題材地圖</h2></div><div className="tp-topic-map-tools"><div className="tp-topic-filter-group" role="group" aria-label="今日方向篩選">{(["全部", "轉強", "轉弱"] as DirectionFilter[]).map((item) => <button type="button" key={item} className={directionFilter === item ? "is-active" : ""} onClick={() => setDirectionFilter(item)}>{item}</button>)}</div>{previewMode ? <PreviewBadge /> : <DataState state="AVAILABLE" />}</div></div>
        <div className="tp-topic-kanban-board">{lanes.map((lane) => <section key={lane.grade} className={`tp-topic-kanban-lane tp-topic-kanban-lane--${lane.grade.toLowerCase()}`} aria-labelledby={`topic-lane-${lane.grade}`}>
          <header className="tp-topic-kanban-lane-header"><strong id={`topic-lane-${lane.grade}`}>{lane.label}</strong></header>
          <div className="tp-topic-kanban-lane-cards">{lane.topics.length ? lane.topics.map((topic) => <KanbanTopicCard topic={topic} key={topic.slug} />) : <p className="tp-topic-kanban-empty">—</p>}</div>
        </section>)}</div>
      </section>

      <TopicLifecycle topics={scanTopics} />

      <section className="tp-topic-groups-section" aria-labelledby="topic-groups-title">
        <div className="tp-topic-section-heading"><div><h2 id="topic-groups-title">依大族群瀏覽</h2></div></div>
        <div className="tp-topic-group-grid">{groupRows.map(([group, topics]) => { const isOpen = openGroups.has(group); return <section className={`tp-topic-group-card ${isOpen ? "is-open" : ""}`} key={group}>
          <button type="button" className="tp-topic-group-toggle" aria-expanded={isOpen} onClick={() => toggleGroup(group)}><span><Layers3 size={18} aria-hidden="true" /><strong>{group}</strong><small>{topics.length} 個題材</small></span><ChevronDown size={18} aria-hidden="true" /></button>
          {isOpen && <div className="tp-topic-group-children">{topics.map((topic) => <Link href={`/topics/${topic.slug}`} className="tp-topic-group-child" key={topic.slug}><span><b>{topic.name}</b><small>{topic.meta.directionLabel}</small></span><span className="tp-topic-group-child-score">{scoreLabel(topic.score)}</span><span className={`tp-chip tp-grade-chip ${gradeClass(topic.meta.laneGrade)}`}>{topic.meta.laneGrade ?? "—"}</span><ChevronRight size={15} aria-hidden="true" /></Link>)}</div>}
        </section>; })}</div>
      </section>

      <section className="tp-topic-overview-list-section" aria-labelledby="topic-list-title">
        <div className="tp-topic-section-heading"><div><h2 id="topic-list-title">全部題材</h2></div></div>
        <Card className="tp-topic-overview-list-card"><div className="tp-topic-overview-list-controls"><label className="tp-search-input"><Search size={17} aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜尋題材名稱或代號" /></label><div className="tp-topic-grade-filters" role="group" aria-label="等級篩選">{(["全部", "S", "A", "B", "D"] as GradeFilter[]).map((item) => <button type="button" key={item} className={gradeFilter === item ? "is-active" : ""} onClick={() => setGradeFilter(item)}>{item === "全部" ? "全部" : item}</button>)}</div></div>
          <div className="tp-topic-overview-list-head" aria-hidden="true"><span>題材名稱</span><span>大族群</span><span>等級</span><span>今日分數</span><span>今日方向</span><span>股票數</span><span>收藏</span></div>
          <div className="tp-topic-overview-list-items">{filteredTopics.map((topic) => <div className="tp-topic-overview-list-row" key={topic.slug}><Link href={`/topics/${topic.slug}`} className="tp-topic-overview-list-link"><span className="tp-topic-overview-name"><b>{topic.name}</b><small>{topic.slug}</small></span><span>{topic.meta.groupName ?? "其他題材"}</span><span className={`tp-chip tp-grade-chip ${gradeClass(topic.meta.laneGrade)}`}>{topic.meta.laneGrade ?? "—"}</span><strong className="tp-topic-overview-score">{scoreLabel(topic.score)}</strong><span className={`tp-topic-overview-direction tp-topic-direction--${topic.meta.direction}`}><span>{topic.meta.directionSymbol}</span>{topic.meta.directionLabel}</span><span className="tp-topic-overview-count">{topic.constituentCount} 檔</span><ChevronRight size={16} aria-hidden="true" /></Link><button type="button" className={`tp-topic-row-star ${favorites.has(topic.slug) ? "is-active" : ""}`} aria-label={favorites.has(topic.slug) ? `取消收藏 ${topic.name}` : `收藏 ${topic.name}`} aria-pressed={favorites.has(topic.slug)} onClick={() => toggleFavorite(topic.slug)}><Star size={18} fill={favorites.has(topic.slug) ? "currentColor" : "none"} aria-hidden="true" /></button></div>)}</div>
          {filteredTopics.length === 0 && <EmptyState title="找不到符合條件的題材" description="調整搜尋文字或篩選條件後再試一次。" />}
        </Card>
      </section>
    </>}
  </PageContainer></AppShell>;
}
