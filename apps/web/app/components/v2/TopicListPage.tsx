"use client";

import Link from "next/link";
import { Activity, ChevronDown, ChevronRight, CircleHelp, Crown, Sprout, TrendingDown, TrendingUp, type LucideIcon, Layers3, Search, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchTopics, scoreLabel, type TopicResource, type TopicSummary } from "../../lib/topic-api";
import { getTopicOverviewLifecycle, getTopicOverviewMeta, PREVIEW_LABEL, type TopicGrade, type TopicLifecycleStage, type TopicOverviewLifecycle, type TopicOverviewMeta } from "../../lib/topic-preview";
import { AppShell, Card, DataState, EmptyState, PageContainer, Skeleton } from "./V2Foundation";
import { useTopicFavoritesState } from "../FavoriteButton";

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

type DisplayLifecycleStage = "萌芽" | "發酵" | "主升" | "成熟" | "衰退";

const LIFECYCLE_STAGES: Array<{ stage: DisplayLifecycleStage; hint: string; icon: LucideIcon }> = [
  { stage: "萌芽", hint: "開始出現反應", icon: Sprout },
  { stage: "發酵", hint: "關注度擴大", icon: Activity },
  { stage: "主升", hint: "市場主流", icon: TrendingUp },
  { stage: "成熟", hint: "高檔整理", icon: Crown },
  { stage: "衰退", hint: "熱度下降", icon: TrendingDown },
];

const MAX_VISIBLE_LIFECYCLE_TOPICS = 4;

const LIFECYCLE_HELP = [
  { stage: "萌芽", description: "題材開始出現市場反應，但尚未形成廣泛共識。" },
  { stage: "發酵", description: "關注度與資金反應開始擴大，題材逐漸形成。" },
  { stage: "主升", description: "題材形成明顯市場主線，代表股與相關股票同步活躍。" },
  { stage: "成熟", description: "題材仍具有強度，但進入高檔或輪動整理階段。" },
  { stage: "衰退", description: "市場關注與資金反應下降，題材影響力逐步減弱。" },
] as const;

function gradeClass(grade: string | null): string {
  return `tp-grade-${(grade ?? "unknown").toLowerCase()}`;
}

function isMarketTopic(topic: TopicSummary): boolean {
  return topic.topicType !== "MAJOR_GROUP";
}

function filterByDirection(topic: OverviewTopic, filter: DirectionFilter): boolean {
  return filter === "全部" || (filter === "轉強" ? topic.meta.direction === "up" : topic.meta.direction === "down");
}

function displayLifecycleStage(stage: TopicLifecycleStage): DisplayLifecycleStage | null {
  if (stage === "高檔整理") return "成熟";
  if (stage === "退潮") return "衰退";
  if (stage === "觀察") return null;
  return stage;
}

function formalLifecycleStage(stage: string | null | undefined): TopicLifecycleStage | null {
  const labels: Record<string, TopicLifecycleStage> = {
    SPROUTING: "萌芽",
    FERMENTING: "發酵",
    MAIN_RISE: "主升",
    MATURE: "高檔整理",
    DECLINING: "退潮",
  };
  return stage ? labels[stage] ?? null : null;
}

function lifecycleForTopic(topic: OverviewTopic, preview: boolean): TopicOverviewLifecycle | null {
  if (!preview) {
    if (!topic.lifecycle || topic.lifecycle.dataStatus !== "SHADOW_AVAILABLE") return null;
    const stage = formalLifecycleStage(topic.lifecycle.currentStage);
    return stage ? { stage, day: topic.lifecycle.currentStageTradingDays ?? 1 } : null;
  }
  if (topic.lifecycle && topic.lifecycle.dataStatus !== "PREVIEW") return null;
  return getTopicOverviewLifecycle(topic.slug);
}

function PreviewBadge() {
  return <span className="tp-preview-badge">{PREVIEW_LABEL}</span>;
}

function KanbanTopicCard({ topic }: { topic: OverviewTopic }) {
  const grade = topic.meta.laneGrade;
  return <Link href={`/topics/${topic.slug}`} className={`tp-topic-kanban-card tp-topic-direction--${topic.meta.direction} ${gradeClass(grade)}`}>
    <span className="tp-topic-direction-rail" aria-hidden="true" />
    <span className="tp-topic-kanban-card-row"><strong>{topic.name}</strong><span className="tp-topic-kanban-card-meta"><b className="tp-topic-kanban-score-value">{scoreLabel(topic.score)}</b><span className="tp-topic-direction-mark" aria-label={`今日方向 ${topic.meta.directionLabel}`}>{topic.meta.directionSymbol}</span></span></span>
  </Link>;
}

function LifecycleChip({ item }: { item: LifecycleTopic }) {
  return <Link href={`/topics/${item.topic.slug}`} className="tp-topic-lifecycle-chip">
    <span><b>{item.topic.name}</b><small>Day {item.lifecycle.day}</small></span>
    <strong>{scoreLabel(item.topic.score)}</strong>
  </Link>;
}

function TopicLifecycle({ topics, preview }: { topics: OverviewTopic[]; preview: boolean }) {
  const allowPreview = preview;
  const [showHelp, setShowHelp] = useState(false);
  const [expandedStage, setExpandedStage] = useState<DisplayLifecycleStage | null>(null);
  const stageMap = useMemo(() => {
    const map = new Map<DisplayLifecycleStage, LifecycleTopic[]>(LIFECYCLE_STAGES.map(({ stage }) => [stage, []]));
    topics.forEach((topic) => {
      const lifecycle = lifecycleForTopic(topic, preview);
      if (lifecycle) {
        const stage = displayLifecycleStage(lifecycle.stage);
        if (stage) map.set(stage, [...(map.get(stage) ?? []), { topic, lifecycle }]);
      }
    });
    return map;
  }, [preview, topics]);

  return <section className="tp-topic-lifecycle-section" aria-labelledby="topic-lifecycle-title">
    <div className="tp-topic-lifecycle-heading"><div className="tp-topic-lifecycle-heading-main"><h2 id="topic-lifecycle-title">題材生命週期</h2><span className="tp-topic-lifecycle-help-wrap"><button type="button" className="tp-topic-lifecycle-help-trigger" aria-label="題材生命週期說明" aria-expanded={showHelp} aria-haspopup="dialog" onClick={() => setShowHelp((value) => !value)}><CircleHelp size={18} aria-hidden="true" /></button>{showHelp && <div className="tp-topic-lifecycle-help" role="dialog" aria-label="題材生命週期說明"><strong>題材生命週期說明</strong>{LIFECYCLE_HELP.map((item) => <p key={item.stage}><b>{item.stage}</b><span>{item.description}</span></p>)}<p><b>Day N</b><span>代表題材目前連續停留於此生命階段的天數。</span></p><p className="tp-topic-lifecycle-help-note">這只是市場狀態描述，不是買賣建議。</p></div>}</span></div>{allowPreview ? <PreviewBadge /> : <DataState state="UNAVAILABLE" />}</div>
    <div className="tp-topic-lifecycle-track">{LIFECYCLE_STAGES.map(({ stage, hint, icon: StageIcon }) => { const items = stageMap.get(stage) ?? []; const isExpanded = expandedStage === stage; const visibleItems = isExpanded ? items : items.slice(0, MAX_VISIBLE_LIFECYCLE_TOPICS); const remaining = items.length - visibleItems.length; return <section className={`tp-topic-lifecycle-stage ${isExpanded ? "is-expanded" : ""}`} key={stage} aria-labelledby={`topic-stage-${stage}`}>
      <header className="tp-topic-lifecycle-stage-header"><h3 id={`topic-stage-${stage}`}><StageIcon size={17} strokeWidth={1.8} aria-hidden="true" /><span>{stage}</span></h3><small>{hint}</small></header>
      <div className="tp-topic-lifecycle-items">{visibleItems.length ? visibleItems.map((item) => <LifecycleChip item={item} key={item.topic.slug} />) : <span className="tp-topic-lifecycle-empty">—</span>}</div>
      {items.length > MAX_VISIBLE_LIFECYCLE_TOPICS && <button type="button" className="tp-topic-lifecycle-expand" onClick={() => setExpandedStage(isExpanded ? null : stage)}>{isExpanded ? "收合 ↑" : `查看另外 ${remaining} 個 →`}</button>}
    </section>; })}</div>
  </section>;
}

export default function TopicListPage() {
  const [resource, setResource] = useState<TopicResource<TopicSummary[]> | null>(null);
  const [query, setQuery] = useState("");
  const [directionFilter, setDirectionFilter] = useState<DirectionFilter>("全部");
  const [gradeFilter, setGradeFilter] = useState<GradeFilter>("全部");
  const { slugs: favoriteSlugs, toggle: toggleTopicFavorite } = useTopicFavoritesState();
  const favorites = useMemo(() => new Set(favoriteSlugs), [favoriteSlugs]);
  const [openGroups, setOpenGroups] = useState<Set<string>>(new Set());

  useEffect(() => {
    let active = true;
    fetchTopics().then((next) => { if (active) setResource(next); });
    return () => { active = false; };
  }, []);

  const overviewTopics = useMemo<OverviewTopic[]>(() => (resource?.data ?? [])
    .filter(isMarketTopic)
    .map((topic) => ({ ...topic, meta: getTopicOverviewMeta(topic, resource?.source !== "api") })), [resource]);
  const marketTopics = useMemo(() => overviewTopics.filter((topic) => filterByDirection(topic, directionFilter)), [directionFilter, overviewTopics]);
  const normalizedQuery = query.trim().toLocaleLowerCase("zh-TW");
  const filteredTopics = useMemo(() => overviewTopics.filter((topic) => {
    const text = `${topic.name} ${topic.slug} ${topic.meta.groupName ?? ""}`.toLocaleLowerCase("zh-TW");
    return (!normalizedQuery || text.includes(normalizedQuery)) && (gradeFilter === "全部" || topic.meta.laneGrade === gradeFilter);
  }), [gradeFilter, normalizedQuery, overviewTopics]);
  const lanes = useMemo(() => GRADE_LANES.map((lane) => ({ ...lane, topics: marketTopics.filter((topic) => topic.meta.laneGrade === lane.grade) })), [marketTopics]);
  const groupRows = useMemo(() => {
    const groups = new Map<string, OverviewTopic[]>();
    overviewTopics.forEach((topic) => {
      const group = topic.meta.groupName ?? "其他題材";
      groups.set(group, [...(groups.get(group) ?? []), topic]);
    });
    return Array.from(groups.entries()).sort(([a], [b]) => a.localeCompare(b, "zh-TW"));
  }, [overviewTopics]);
  const previewMode = resource?.source !== "api";

  function toggleGroup(group: string) {
    setOpenGroups((current) => {
      const next = new Set(current);
      if (next.has(group)) next.delete(group); else next.add(group);
      return next;
    });
  }

  return <AppShell currentPath="/topics"><PageContainer title="題材" hideHeader className="tp-topic-overview-page">
    {!resource && <Card className="tp-topic-data-card"><div className="tp-topic-loading-row"><Skeleton /><Skeleton /><Skeleton /></div><Skeleton className="tp-topic-loading-table" /></Card>}
    {resource?.source === "unavailable" && <Card className="tp-topic-data-card"><DataState state="UNAVAILABLE" /><EmptyState title="正式題材清單目前無法取得" description={resource.error ?? "請確認 FastAPI API origin 與服務狀態。"} /></Card>}
    {resource?.data && <>
      <section className="tp-topic-kanban-section" aria-labelledby="topic-kanban-title">
        <div className="tp-topic-section-heading tp-topic-map-heading"><div><h2 id="topic-kanban-title">今日題材地圖</h2></div><div className="tp-topic-map-tools"><div className="tp-topic-filter-group" role="group" aria-label="今日方向篩選">{(["全部", "轉強", "轉弱"] as DirectionFilter[]).map((item) => <button type="button" key={item} className={directionFilter === item ? "is-active" : ""} onClick={() => setDirectionFilter(item)}>{item}</button>)}</div>{previewMode ? <PreviewBadge /> : <DataState state="AVAILABLE" />}</div></div>
        <div className="tp-topic-kanban-board">{lanes.map((lane) => <section key={lane.grade} className={`tp-topic-kanban-lane tp-topic-kanban-lane--${lane.grade.toLowerCase()}`} aria-labelledby={`topic-lane-${lane.grade}`}>
          <header className="tp-topic-kanban-lane-header"><strong id={`topic-lane-${lane.grade}`}>{lane.label}</strong></header>
          <div className="tp-topic-kanban-lane-cards" tabIndex={0} aria-label={`${lane.label}題材列表`}>{lane.topics.length ? lane.topics.map((topic) => <KanbanTopicCard topic={topic} key={topic.slug} />) : <p className="tp-topic-kanban-empty">—</p>}</div>
        </section>)}</div>
      </section>

      <TopicLifecycle topics={overviewTopics} preview={previewMode} />

      <section className="tp-topic-groups-section" aria-labelledby="topic-groups-title">
        <div className="tp-topic-section-heading"><div><h2 id="topic-groups-title">依大族群瀏覽</h2></div></div>
        <div className="tp-topic-group-grid">{groupRows.map(([group, topics]) => { const isOpen = openGroups.has(group); return <section className={`tp-topic-group-card ${isOpen ? "is-open" : ""}`} key={group}>
          <button type="button" className="tp-topic-group-toggle" aria-expanded={isOpen} onClick={() => toggleGroup(group)}><span><Layers3 size={18} aria-hidden="true" /><strong>{group}</strong><small>{topics.length} 個題材</small></span><ChevronDown size={18} aria-hidden="true" /></button>
          {isOpen && <div className="tp-topic-group-children">{topics.map((topic) => <Link href={`/topics/${topic.slug}`} className="tp-topic-group-child" key={topic.slug}><span><b>{topic.name}</b><small>{topic.meta.directionLabel}</small></span><span className="tp-topic-group-child-score">{scoreLabel(topic.score)}</span><span className={`tp-chip tp-grade-chip ${gradeClass(topic.meta.laneGrade)}`}>{topic.meta.laneGrade ?? "—"}</span><ChevronRight size={15} aria-hidden="true" /></Link>)}</div>}
        </section>; })}</div>
      </section>

      <section className="tp-topic-overview-list-section" aria-labelledby="topic-list-title">
        <div className="tp-topic-section-heading"><div><h2 id="topic-list-title">全部題材</h2><p>完整正式題材目錄；尚無分數、等級或生命週期的題材仍會保留顯示。</p></div><span>{overviewTopics.length} 個題材</span></div>
        <Card className="tp-topic-overview-list-card"><div className="tp-topic-overview-list-controls"><label className="tp-search-input"><Search size={17} aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜尋題材名稱或代號" /></label><div className="tp-topic-grade-filters" role="group" aria-label="等級篩選">{(["全部", "S", "A", "B", "D"] as GradeFilter[]).map((item) => <button type="button" key={item} className={gradeFilter === item ? "is-active" : ""} onClick={() => setGradeFilter(item)}>{item === "全部" ? "全部" : item}</button>)}</div></div>
          <div className="tp-topic-overview-list-head" aria-hidden="true"><span>題材名稱</span><span>大族群</span><span>等級</span><span>今日分數</span><span>今日方向</span><span>股票數</span><span>收藏</span></div>
          <div className="tp-topic-overview-list-items">{filteredTopics.map((topic) => <div className="tp-topic-overview-list-row" key={topic.slug}><Link href={`/topics/${topic.slug}`} className="tp-topic-overview-list-link"><span className="tp-topic-overview-name"><b>{topic.name}</b><small>{topic.slug}</small></span><span>{topic.meta.groupName ?? "其他題材"}</span><span className={`tp-chip tp-grade-chip ${gradeClass(topic.meta.laneGrade)}`}>{topic.meta.laneGrade ?? "—"}</span><strong className="tp-topic-overview-score">{scoreLabel(topic.score)}</strong><span className={`tp-topic-overview-direction tp-topic-direction--${topic.meta.direction}`}><span>{topic.meta.directionSymbol}</span>{topic.meta.directionLabel}</span><span className="tp-topic-overview-count">{topic.constituentCount} 檔</span><ChevronRight size={16} aria-hidden="true" /></Link><button type="button" className={`tp-topic-row-star ${favorites.has(topic.slug) ? "is-active" : ""}`} aria-label={favorites.has(topic.slug) ? `取消收藏 ${topic.name}` : `收藏 ${topic.name}`} aria-pressed={favorites.has(topic.slug)} onClick={() => toggleTopicFavorite(topic.slug)}><Star size={18} fill={favorites.has(topic.slug) ? "currentColor" : "none"} aria-hidden="true" /></button></div>)}</div>
          {filteredTopics.length === 0 && <EmptyState title="找不到符合條件的題材" description="調整搜尋文字或篩選條件後再試一次。" />}
        </Card>
      </section>
    </>}
  </PageContainer></AppShell>;
}
