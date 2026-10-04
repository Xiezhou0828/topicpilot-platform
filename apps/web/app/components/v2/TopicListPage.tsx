"use client";

import Link from "next/link";
import { Activity, BookOpen, ChevronRight, CircleHelp, Crown, Search, Sprout, Star, TrendingDown, TrendingUp, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTopicFavoritesState } from "../FavoriteButton";
import { fetchTopics, getTopicPublication, type TopicPublicationDisclosure, type TopicResource, type TopicSource, type TopicSummary } from "../../lib/topic-api";
import { getTopicKnowledge, knowledgeSearchText } from "../../lib/topic-knowledge";
import { GRADE_LABELS, GRADE_ORDER, lifecycleStageForOverview, type OverviewLifecycleStage, type StrengthView, type TopicGrade, validGrade } from "../../lib/topic-presentation";
import { AppShell, Card, DataState, EmptyState, PageContainer, Skeleton } from "./V2Foundation";

type GradeFilter = "全部" | TopicGrade;
type LifecycleFilter = "全部" | OverviewLifecycleStage;
type SortMode = "strength" | "name";
type OverviewTopic = TopicSummary & { source: TopicSource };
type DrawerKind = "map" | "lifecycle" | "guide" | null;
const EMPTY_TOPIC_LIST: TopicSummary[] = [];

const LIFECYCLE_STAGES: Array<{ stage: OverviewLifecycleStage; hint: string; icon: typeof Sprout }> = [
  { stage: "萌芽", hint: "開始出現反應", icon: Sprout },
  { stage: "發酵", hint: "關注度擴大", icon: Activity },
  { stage: "主升", hint: "市場形成主線", icon: TrendingUp },
  { stage: "成熟", hint: "高檔整理", icon: Crown },
  { stage: "衰退", hint: "熱度下降", icon: TrendingDown },
];

const MAX_VISIBLE_MAP_TOPICS = 3;
const MAX_VISIBLE_LIFECYCLE_TOPICS = 4;
const GUIDE = [
  ["今日題材地圖", "先切換絕對強度或相對市場，再從 S／A／B／D 四個 lane 進入題材。卡片只顯示正式分類，不在瀏覽器重算分數。"],
  ["題材生命週期", "只顯示後端已確認的五個市場階段；BASE 不會被硬塞進地圖，但仍可在探索區找到。"],
  ["探索題材", "可依 Parent、Lifecycle、Grade、收藏與名稱搜尋；搜尋會涵蓋題材名稱、slug、別名與摘要。"],
  ["正式與待提供", "相對強度、歷史或敘事尚未由正式 API 發布時，頁面會明確標示尚未提供，不把絕對值當替代品。"],
] as const;

function gradeClass(grade: string | null): string {
  return `tp-grade-${(grade ?? "unknown").toLowerCase()}`;
}

function PreviewBadge() {
  return <span className="tp-preview-badge">Preview</span>;
}

const PUBLICATION_FIELD_LABELS: Record<TopicPublicationDisclosure["field"], string> = {
  identity: "Identity", hierarchy: "Hierarchy", relations: "Relations", score: "Score", grade: "Grade", snapshot: "Snapshot", participation: "Participation", lifecycle: "Lifecycle", leaderCore: "Leader/Core", technicalRelative: "Technical/Relative", events: "Events", news: "News", heatmap: "Heatmap", summary: "Summary", opportunity: "Opportunity", source: "Source",
};

function PublicationDisclosure({ disclosure }: { disclosure: TopicPublicationDisclosure }) {
  return <span className="tp-chip tp-topic-publication-state" data-publication-field={disclosure.field} data-publication-state={disclosure.state} title={disclosure.note}>{PUBLICATION_FIELD_LABELS[disclosure.field]}: {disclosure.state}</span>;
}

function lifecycleForTopic(topic: OverviewTopic): OverviewLifecycleStage | null {
  return lifecycleStageForOverview(topic.lifecycle?.currentStage);
}

function isLeafTopic(topic: TopicSummary): boolean {
  return topic.kind === "LEAF";
}

function MapCard({ topic, view, onOpen }: { topic: OverviewTopic; view: StrengthView; onOpen?: () => void }) {
  const grade = validGrade(view === "ABSOLUTE" ? topic.formalStrength?.absolute.grade ?? topic.grade : topic.formalStrength?.relative.grade);
  const relativeUnavailable = view === "RELATIVE" && !grade;
  return <Link href={`/topics/${topic.slug}`} onClick={onOpen} className={`tp-topic-v1-map-card ${gradeClass(grade)} ${relativeUnavailable ? "is-unavailable" : ""}`}>
    <span className="tp-topic-v1-map-card-top"><b>{topic.name}</b><span className="tp-topic-v1-map-card-arrow"><ChevronRight size={16} aria-hidden="true" /></span></span>
    <span className="tp-topic-v1-map-card-bottom">{relativeUnavailable ? "相對強度尚未提供" : `${grade}｜${GRADE_LABELS[view][grade as TopicGrade]}`}</span>
    <span className="tp-topic-v1-map-card-parent">{topic.groupName ?? "未分層"}</span>
  </Link>;
}

function TopicDrawer({ kind, title, onClose, children, query, onQueryChange }: { kind: Exclude<DrawerKind, null>; title: string; onClose: () => void; children: React.ReactNode; query?: string; onQueryChange?: (value: string) => void }) {
  return <div className="tp-topic-v1-drawer-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <aside className="tp-topic-v1-drawer" role="dialog" aria-modal="true" aria-label={title} data-drawer-kind={kind}>
      <header className="tp-topic-v1-drawer-header"><div><p className="tp-overline">TopicPilot</p><h2>{title}</h2></div><button type="button" className="tp-topic-v1-close" onClick={onClose} aria-label="關閉"><X size={18} /></button></header>
      {onQueryChange && <label className="tp-topic-v1-drawer-search"><Search size={16} aria-hidden="true" /><input autoFocus value={query ?? ""} onChange={(event) => onQueryChange(event.target.value)} placeholder="搜尋題材" /></label>}
      <div className="tp-topic-v1-drawer-body">{children}</div>
    </aside>
  </div>;
}

function TopicMap({ topics, view, preview, onOpenDrawer }: { topics: OverviewTopic[]; view: StrengthView; preview: boolean; onOpenDrawer: (stage: "map") => void }) {
  const lanes = GRADE_ORDER.map((grade) => ({ grade, topics: topics.filter((topic) => validGrade(view === "ABSOLUTE" ? topic.formalStrength?.absolute.grade ?? topic.grade : topic.formalStrength?.relative.grade) === grade) }));
  const unavailable = view === "RELATIVE" && topics.some((topic) => !validGrade(topic.formalStrength?.relative.grade));
  return <section className="tp-topic-v1-section tp-topic-v1-map-section" aria-labelledby="topic-v1-map-title">
    <div className="tp-topic-v1-section-heading"><div><p className="tp-overline">Formal daily classification</p><h2 id="topic-v1-map-title">今日題材地圖</h2><p>以正式 {view === "ABSOLUTE" ? "絕對強度" : "相對市場強度"} 分類瀏覽；卡片不顯示分數，避免把分類誤讀成排名。</p></div><div className="tp-topic-v1-heading-actions">{preview ? <PreviewBadge /> : <span className="tp-topic-v1-formal-note">正式資料</span>}<button type="button" className="tp-topic-v1-guide-button" onClick={() => onOpenDrawer("map")}><BookOpen size={16} />閱讀地圖說明</button></div></div>
    <div className="tp-topic-v1-lanes">{lanes.map((lane) => <section className={`tp-topic-v1-lane ${gradeClass(lane.grade)}`} key={lane.grade} aria-labelledby={`topic-v1-lane-${lane.grade}`}><header><strong id={`topic-v1-lane-${lane.grade}`}>{lane.grade}</strong><span>{GRADE_LABELS[view][lane.grade]}</span></header><div className="tp-topic-v1-lane-cards">{lane.topics.slice(0, MAX_VISIBLE_MAP_TOPICS).map((topic) => <MapCard topic={topic} view={view} key={topic.slug} />)}{lane.topics.length > MAX_VISIBLE_MAP_TOPICS && <button type="button" className="tp-topic-v1-more-card" onClick={() => onOpenDrawer("map")}>查看另外 {lane.topics.length - MAX_VISIBLE_MAP_TOPICS} 個</button>}{lane.topics.length === 0 && <span className="tp-topic-v1-empty">此分類目前沒有正式題材</span>}</div></section>)}</div>
    {unavailable && <p className="tp-topic-v1-unavailable-note">相對強度正式資料尚未完整發布；缺少分類的題材不會被放入其他 lane。</p>}
  </section>;
}

function LifecycleBoard({ topics, preview, onOpenDrawer }: { topics: OverviewTopic[]; preview: boolean; onOpenDrawer: (stage: "lifecycle") => void }) {
  return <section className="tp-topic-v1-section tp-topic-v1-lifecycle-section" aria-labelledby="topic-v1-lifecycle-title"><div className="tp-topic-v1-section-heading"><div><p className="tp-overline">Confirmed lifecycle stage</p><h2 id="topic-v1-lifecycle-title">題材生命週期</h2><p>五個可呈現的市場階段；BASE／尚未形成不在 Overview 階段欄中。</p></div>{preview ? <PreviewBadge /> : <span className="tp-topic-v1-formal-note">{topics.some((topic) => topic.lifecycle?.dataStatus === "FORMAL_AVAILABLE") ? "Backend formal" : "階段依 API 提供"}</span>}</div><div className="tp-topic-v1-lifecycle-board">{LIFECYCLE_STAGES.map(({ stage, hint, icon: Icon }) => { const items = topics.filter((topic) => lifecycleForTopic(topic) === stage); const visible = items.slice(0, MAX_VISIBLE_LIFECYCLE_TOPICS); return <section className="tp-topic-v1-lifecycle-column" key={stage}><header><span className="tp-topic-v1-lifecycle-icon"><Icon size={17} /></span><div><h3>{stage}</h3><small>{hint}</small></div></header><div className="tp-topic-v1-lifecycle-items">{visible.map((topic) => <Link href={`/topics/${topic.slug}`} key={topic.slug} className="tp-topic-v1-lifecycle-item"><span><b>{topic.name}</b><small>{topic.lifecycle?.currentStageTradingDays === null || topic.lifecycle?.currentStageTradingDays === undefined ? "Day 尚未提供" : `Day ${topic.lifecycle.currentStageTradingDays}`}</small></span><ChevronRight size={15} /></Link>)}{items.length === 0 && <span className="tp-topic-v1-empty">—</span>}</div>{items.length > MAX_VISIBLE_LIFECYCLE_TOPICS && <button type="button" className="tp-topic-v1-more-button" onClick={() => onOpenDrawer("lifecycle")}>查看另外 {items.length - visible.length} 個</button>}</section>; })}</div><div className="tp-topic-v1-lifecycle-note">{preview ? "Preview lifecycle 只供介面探索，不代表正式出版。" : "階段、Day N 與候選轉換均沿用 backend read model；前端不重建時間序列。"}</div></section>;
}

function ParentNav({ parents, selected, onSelect }: { parents: Array<{ slug: string; name: string; count: number }>; selected: string | null; onSelect: (slug: string | null) => void }) {
  return <nav className="tp-topic-v1-parent-nav tp-topic-group-grid" aria-label="Parent 題材群組"><button type="button" className={selected === null ? "is-active" : ""} onClick={() => onSelect(null)}>全部題材</button>{parents.map((parent) => <button type="button" key={parent.slug} className={selected === parent.slug ? "is-active" : ""} onClick={() => onSelect(parent.slug)}><span>{parent.name}</span><small>{parent.count}</small></button>)}</nav>;
}

function ExplorationRow({ topic, view, favorite, onToggleFavorite }: { topic: OverviewTopic; view: StrengthView; favorite: boolean; onToggleFavorite: () => void }) {
  const grade = validGrade(view === "ABSOLUTE" ? topic.formalStrength?.absolute.grade ?? topic.grade : topic.formalStrength?.relative.grade);
  const lifecycle = lifecycleForTopic(topic);
  return <div className="tp-topic-v1-explore-row"><Link href={`/topics/${topic.slug}`} className="tp-topic-v1-explore-main"><span><b>{topic.name}</b><small>{topic.slug}{topic.groupName ? ` · ${topic.groupName}` : ""}</small></span><ChevronRight size={17} /></Link><span className="tp-topic-v1-explore-cell">{grade ? <span className={`tp-chip tp-grade-chip ${gradeClass(grade)}`}>{grade}｜{GRADE_LABELS[view][grade]}</span> : <span className="tp-topic-v1-muted">尚未提供</span>}</span><span className="tp-topic-v1-explore-cell">{lifecycle ?? <span className="tp-topic-v1-muted">尚未形成／待確認</span>}</span><button type="button" className={`tp-topic-v1-favorite ${favorite ? "is-active" : ""}`} aria-label={favorite ? `取消收藏 ${topic.name}` : `收藏 ${topic.name}`} aria-pressed={favorite} onClick={onToggleFavorite}><Star size={17} fill={favorite ? "currentColor" : "none"} /></button></div>;
}

function GuideDrawer({ onClose }: { onClose: () => void }) {
  return <TopicDrawer kind="guide" title="題材地圖與探索說明" onClose={onClose}>{GUIDE.map(([title, body]) => <section className="tp-topic-v1-guide-section" key={title}><h3>{title}</h3><p>{body}</p></section>)}</TopicDrawer>;
}

export default function TopicListPage() {
  const [resource, setResource] = useState<TopicResource<TopicSummary[]> | null>(null);
  const [query, setQuery] = useState("");
  const [strengthView, setStrengthView] = useState<StrengthView>("ABSOLUTE");
  const [gradeFilter, setGradeFilter] = useState<GradeFilter>("全部");
  const [lifecycleFilter, setLifecycleFilter] = useState<LifecycleFilter>("全部");
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [selectedParent, setSelectedParent] = useState<string | null>(null);
  const [sortMode, setSortMode] = useState<SortMode>("strength");
  const [drawer, setDrawer] = useState<DrawerKind>(null);
  const [drawerQuery, setDrawerQuery] = useState("");
  const { slugs: favoriteSlugs, toggle: toggleTopicFavorite } = useTopicFavoritesState();
  const favorites = useMemo(() => new Set(favoriteSlugs), [favoriteSlugs]);

  useEffect(() => { let active = true; fetchTopics().then((next) => { if (active) setResource(next); }); return () => { active = false; }; }, []);
  const catalogTopics = resource?.data ?? EMPTY_TOPIC_LIST;
  const overviewTopics = useMemo<OverviewTopic[]>(() => catalogTopics.filter(isLeafTopic).map((topic) => ({ ...topic, source: resource?.source ?? "unavailable" })), [catalogTopics, resource?.source]);
  const previewMode = resource?.source === "synthetic-snapshot";
  const parents = useMemo(() => { const counts = new Map<string, { slug: string; name: string; count: number }>(); overviewTopics.forEach((topic) => { const parent = topic.hierarchy.parents[0]; if (parent) { const current = counts.get(parent.slug) ?? { slug: parent.slug, name: parent.name, count: 0 }; current.count += 1; counts.set(parent.slug, current); } }); return Array.from(counts.values()).sort((a, b) => a.name.localeCompare(b.name, "zh-TW")); }, [overviewTopics]);
  const normalizedQuery = query.trim().toLocaleLowerCase("zh-TW");
  const filteredTopics = useMemo(() => {
    const result = overviewTopics.filter((topic) => {
      const knowledge = getTopicKnowledge(topic);
      const text = `${topic.name} ${topic.slug} ${topic.groupName ?? ""} ${knowledgeSearchText(knowledge)}`.toLocaleLowerCase("zh-TW");
      const grade = validGrade(strengthView === "ABSOLUTE" ? topic.formalStrength?.absolute.grade ?? topic.grade : topic.formalStrength?.relative.grade);
      const parentMatches = selectedParent === null || topic.hierarchy.parents.some((parent) => parent.slug === selectedParent);
      const gradeMatches = gradeFilter === "全部" || grade === gradeFilter;
      const lifecycle = lifecycleForTopic(topic);
      return parentMatches && gradeMatches && (lifecycleFilter === "全部" || lifecycle === lifecycleFilter) && (!favoriteOnly || favorites.has(topic.slug)) && (!normalizedQuery || text.includes(normalizedQuery));
    });
    // Strength order remains the backend/catalog order; the browser must not rank by a score threshold or recompute strength.
    return sortMode === "name" ? [...result].sort((a, b) => a.name.localeCompare(b.name, "zh-TW")) : result;
  }, [favoriteOnly, favorites, gradeFilter, lifecycleFilter, normalizedQuery, overviewTopics, selectedParent, sortMode, strengthView]);
  const drawerTopics = useMemo(() => { const text = drawerQuery.trim().toLocaleLowerCase("zh-TW"); return overviewTopics.filter((topic) => !text || `${topic.name} ${topic.slug}`.toLocaleLowerCase("zh-TW").includes(text)); }, [drawerQuery, overviewTopics]);
  const publication = overviewTopics[0] ? getTopicPublication(overviewTopics[0].source, overviewTopics[0]) : null;

  function openDrawer(kind: Exclude<DrawerKind, null>) { setDrawer(kind); setDrawerQuery(""); }

  return <AppShell currentPath="/topics"><PageContainer title="題材" hideHeader className="tp-topic-overview-page tp-topic-v1-page">
    {!resource && <Card className="tp-topic-data-card"><div className="tp-topic-loading-row"><Skeleton /><Skeleton /><Skeleton /></div><Skeleton className="tp-topic-loading-table" /></Card>}
    {resource?.source === "unavailable" && <Card className="tp-topic-data-card"><DataState state="UNAVAILABLE" /><EmptyState title="正式題材清單目前無法取得" description={resource.error ?? "請確認正式 API 狀態。"} /></Card>}
    {resource?.data && <>
      <header className="tp-topic-v1-intro"><div><p className="tp-overline">Topic intelligence workspace</p><h1>題材總覽</h1><p>先看今日地圖，再用探索區查找完整題材宇宙。正式資料的缺口會直接標示，不用推估補齊。</p><span className="tp-topic-v1-muted">{overviewTopics.length} 個 Leaf 題材 · Parent Topic 作為瀏覽入口</span></div><button type="button" className="tp-topic-v1-guide-button" onClick={() => openDrawer("guide")}><CircleHelp size={17} />使用說明</button></header>
      <div className="tp-topic-v1-view-switch" role="group" aria-label="強度視圖切換"><button type="button" className={strengthView === "ABSOLUTE" ? "is-active" : ""} onClick={() => setStrengthView("ABSOLUTE")}>絕對強度</button><button type="button" className={strengthView === "RELATIVE" ? "is-active" : ""} onClick={() => setStrengthView("RELATIVE")}>相對市場</button></div>
      <TopicMap topics={overviewTopics} view={strengthView} preview={previewMode} onOpenDrawer={openDrawer} />
      <LifecycleBoard topics={overviewTopics} preview={previewMode} onOpenDrawer={openDrawer} />
      <section className="tp-topic-v1-exploration" aria-labelledby="topic-v1-exploration-title"><aside><p className="tp-overline">Explore the universe</p><h2 id="topic-v1-exploration-title">探索題材</h2><p>Parent 只作瀏覽入口；Leaf 的正式狀態仍以各自 Detail read model 為準。</p><ParentNav parents={parents} selected={selectedParent} onSelect={setSelectedParent} /></aside><div className="tp-topic-v1-explore-panel"><div className="tp-topic-v1-explore-toolbar"><label className="tp-search-input"><Search size={17} aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜尋題材、slug 或別名" /></label><div className="tp-topic-v1-filter-row"><select aria-label="Lifecycle 篩選" value={lifecycleFilter} onChange={(event) => setLifecycleFilter(event.target.value as LifecycleFilter)}><option value="全部">全部 Lifecycle</option>{LIFECYCLE_STAGES.map(({ stage }) => <option key={stage} value={stage}>{stage}</option>)}</select><select aria-label="Grade 篩選" value={gradeFilter} onChange={(event) => setGradeFilter(event.target.value as GradeFilter)}>{["全部", ...GRADE_ORDER].map((item) => <option key={item} value={item}>{item === "全部" ? "全部 Grade" : `${item}｜${GRADE_LABELS[strengthView][item as TopicGrade]}`}</option>)}</select><select aria-label="排序" value={sortMode} onChange={(event) => setSortMode(event.target.value as SortMode)}><option value="strength">今日強度（Backend 順序）</option><option value="name">名稱</option></select><button type="button" className={`tp-topic-v1-filter-toggle ${favoriteOnly ? "is-active" : ""}`} aria-pressed={favoriteOnly} onClick={() => setFavoriteOnly((value) => !value)}><Star size={14} fill={favoriteOnly ? "currentColor" : "none"} />只看收藏</button></div></div><div className="tp-topic-v1-result-summary">{filteredTopics.length} 個 Leaf 題材{publication && <span><PublicationDisclosure disclosure={publication.identity} /><PublicationDisclosure disclosure={publication.relations} /></span>}</div><div className="tp-topic-v1-explore-head"><span>題材</span><span>正式分類</span><span>Lifecycle</span><span>收藏</span></div><div className="tp-topic-v1-explore-list">{filteredTopics.length ? filteredTopics.map((topic) => <ExplorationRow key={topic.slug} topic={topic} view={strengthView} favorite={favorites.has(topic.slug)} onToggleFavorite={() => toggleTopicFavorite(topic.slug, { displayLabel: topic.name })} />) : <EmptyState title="找不到符合條件的題材" description="請放寬搜尋、Parent、Lifecycle、Grade 或收藏篩選。" />}</div></div></section>
    </>}
    {drawer === "guide" && <GuideDrawer onClose={() => setDrawer(null)} />}
    {drawer === "map" && <TopicDrawer kind="map" title="今日題材地圖：完整清單" onClose={() => setDrawer(null)} query={drawerQuery} onQueryChange={setDrawerQuery}><p className="tp-topic-v1-drawer-intro">目前視圖：{strengthView === "ABSOLUTE" ? "絕對強度" : "相對市場"}。缺少正式相對分類的題材會保留為未提供。</p>{drawerTopics.map((topic) => <MapCard key={topic.slug} topic={topic} view={strengthView} />)}</TopicDrawer>}
    {drawer === "lifecycle" && <TopicDrawer kind="lifecycle" title="題材生命週期：完整清單" onClose={() => setDrawer(null)} query={drawerQuery} onQueryChange={setDrawerQuery}><p className="tp-topic-v1-drawer-intro">這裡列出目前已確認階段的題材；BASE／尚未形成仍可從探索區進入。</p>{drawerTopics.filter((topic) => lifecycleForTopic(topic)).map((topic) => <Link href={`/topics/${topic.slug}`} key={topic.slug} className="tp-topic-v1-drawer-row"><span><b>{topic.name}</b><small>{lifecycleForTopic(topic)} · {topic.lifecycle?.currentStageTradingDays == null ? "Day 尚未提供" : `Day ${topic.lifecycle.currentStageTradingDays}`}</small></span><ChevronRight size={16} /></Link>)}</TopicDrawer>}
  </PageContainer></AppShell>;
}
