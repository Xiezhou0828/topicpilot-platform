"use client";

import Link from "next/link";
import { ChevronRight, Search, Star, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useTopicFavoritesState } from "../FavoriteButton";
import { fetchTopic, fetchTopicHistory, getTopicPublication, lifecycleStatusLabel, sourceLabel, type TopicDetail, type TopicHistoryPoint, type TopicLifecycle, type TopicPublicationDisclosure, type TopicResource, type TopicSource } from "../../lib/topic-api";
import { getTopicKnowledge } from "../../lib/topic-knowledge";
import { DETAIL_LIFECYCLE_STAGES, formalAbsoluteGrade, formalAbsoluteScore, formalRelativeGrade, formalRelativeScore, freshnessCopy, gradeCopy, lifecycleLabel, lifecycleStageForDetail, topicHasFormalCurrentState } from "../../lib/topic-presentation";
import { AppShell, Card, DataState, EmptyState, PageContainer, RoleChip, Table } from "./V2Foundation";

const PUBLICATION_FIELD_LABELS: Record<TopicPublicationDisclosure["field"], string> = {
  identity: "Identity", hierarchy: "Hierarchy", relations: "Relations", score: "Score", grade: "Grade", snapshot: "Snapshot", participation: "Participation", lifecycle: "Lifecycle", leaderCore: "Leader/Core", technicalRelative: "Technical/Relative", events: "Events", news: "News", heatmap: "Heatmap", summary: "Summary", opportunity: "Opportunity", source: "Source",
};

function PublicationDisclosure({ disclosure }: { disclosure: TopicPublicationDisclosure }) {
  return <span className="tp-chip tp-topic-publication-state" data-publication-field={disclosure.field} data-publication-state={disclosure.state} title={disclosure.note}>{PUBLICATION_FIELD_LABELS[disclosure.field]}: {disclosure.state}</span>;
}

function PreviewBadge() {
  return <span className="tp-preview-badge">Preview</span>;
}

function TopicSectionHeading({ eyebrow, title, description }: { eyebrow?: string; title: string; description: string }) {
  return <div className="tp-topic-v1-section-heading"><div>{eyebrow && <p className="tp-overline">{eyebrow}</p>}<h2>{title}</h2><p>{description}</p></div></div>;
}

function scoreDisplay(value: number | null): string {
  return value === null ? "尚未提供" : Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function changeCopy(value: number | null): string {
  return value === null ? "尚未提供" : `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function changeTone(value: number | null): string {
  return value === null ? "unknown" : value > 0 ? "up" : value < 0 ? "down" : "flat";
}

function Hero({ topic, source, favorite, onToggle }: { topic: TopicDetail; source: TopicSource; favorite: boolean; onToggle: () => void }) {
  const absoluteGrade = formalAbsoluteGrade(topic);
  const relativeGrade = formalRelativeGrade(topic);
  const currentLifecycle = lifecycleStageForDetail(topic.lifecycle?.currentStage);
  return <header className="tp-topic-v1-detail-hero"><nav className="tp-topic-breadcrumb" aria-label="題材階層"><Link href="/topics">題材</Link><span aria-hidden="true">›</span>{topic.groupName && <><span>{topic.groupName}</span><span aria-hidden="true">›</span></>}<strong>{topic.name}</strong></nav><div className="tp-topic-v1-detail-title-row"><div><p className="tp-overline">Topic Detail · {sourceLabel(source)} {source === "synthetic-snapshot" && <PreviewBadge />}</p><h1>{topic.name}</h1><p className="tp-topic-v1-detail-subtitle">{topic.kind === "PARENT" ? "Parent Topic · canonical hierarchy node" : "Leaf Topic · formal market read model"}</p></div><button type="button" className={`tp-topic-favorite ${favorite ? "is-active" : ""}`} aria-label={favorite ? `取消收藏 ${topic.name}` : `收藏 ${topic.name}`} aria-pressed={favorite} onClick={onToggle}><Star size={18} fill={favorite ? "currentColor" : "none"} />{favorite ? "已收藏" : "收藏題材"}</button></div>{topic.kind === "PARENT" ? <div className="tp-topic-v1-detail-meta"><span>Parent children {topic.hierarchy.children.length}</span><span>不承擔 Leaf market state</span></div> : <div className="tp-topic-v1-detail-metrics"><div><span>絕對強度</span><strong>{absoluteGrade ? gradeCopy(absoluteGrade, "ABSOLUTE") : "尚未提供"}</strong><small>{scoreDisplay(formalAbsoluteScore(topic))}</small></div><div><span>相對市場</span><strong>{relativeGrade ? gradeCopy(relativeGrade, "RELATIVE") : "尚未提供"}</strong><small>{scoreDisplay(formalRelativeScore(topic))}</small></div><div><span>生命週期</span><strong>{lifecycleLabel(currentLifecycle)}</strong><small>{topic.lifecycle?.currentStageTradingDays == null ? "Day 尚未提供" : `Day ${topic.lifecycle.currentStageTradingDays}`}</small></div><div><span>題材成員</span><strong>{topic.constituentCount == null ? "尚未提供" : `${topic.constituentCount} 檔`}</strong><small>{freshnessCopy(topic)}</small></div></div>}</header>;
}

function TodayJudgementSection({ topic, publication }: { topic: TopicDetail; publication: ReturnType<typeof getTopicPublication> }) {
  if (topic.kind === "PARENT") return <Card className="tp-topic-v1-parent-state"><TopicSectionHeading title="Parent Topic 狀態" description="Parent 只作 hierarchy 入口，不顯示 Leaf 的今日強度、Grade 或 Lifecycle。" /><div className="tp-topic-v1-judgement-empty"><strong>今日判讀不適用</strong><span>Snapshot NOT_APPLICABLE · 請從 children 進入個別 Leaf Topic Detail。</span></div></Card>;
  const state = topic.readableState && topic.readableState !== "—" ? topic.readableState : "正式今日狀態尚未提供";
  const lifecycle = lifecycleStageForDetail(topic.lifecycle?.currentStage);
  const candidate = lifecycleStageForDetail(topic.lifecycle?.candidateStage);
  return <section className="tp-topic-v1-section tp-topic-v1-judgement" aria-labelledby="topic-v1-judgement-title"><TopicSectionHeading eyebrow="Today at a glance" title="今日判讀" description="文字只整理 backend 已發布的 state、Grade 與 Lifecycle；不由前端自行推導市場結論。" /><div className="tp-topic-v1-judgement-grid"><div className="tp-topic-v1-judgement-main"><span className="tp-overline">正式狀態</span><strong>{state}</strong><p>{topicHasFormalCurrentState(topic) ? `資料截至 ${topic.dataDate}` : "今日正式 snapshot 尚未完整提供，請以缺口狀態閱讀。"}</p></div><div><span>絕對分類</span><strong>{formalAbsoluteGrade(topic) ? gradeCopy(formalAbsoluteGrade(topic), "ABSOLUTE") : "尚未提供"}</strong></div><div><span>相對分類</span><strong>{formalRelativeGrade(topic) ? gradeCopy(formalRelativeGrade(topic), "RELATIVE") : "尚未提供"}</strong></div><div><span>Lifecycle</span><strong>{lifecycleLabel(lifecycle)}</strong>{candidate && candidate !== lifecycle && <small>候選：{candidate}</small>}</div></div><div className="tp-topic-v1-formal-boundary"><PublicationDisclosure disclosure={publication.snapshot} /><PublicationDisclosure disclosure={publication.grade} /><PublicationDisclosure disclosure={publication.lifecycle} /></div></section>;
}

function TopicKnowledgeSection({ topic }: { topic: TopicDetail }) {
  const knowledge = getTopicKnowledge(topic);
  return <section className="tp-topic-v1-section tp-topic-v1-knowledge" aria-labelledby="topic-v1-knowledge-title"><TopicSectionHeading eyebrow="Canonical topic knowledge" title="題材介紹" description="這一區只承載穩定的題材知識；成員、角色、Strength、Grade、Lifecycle 與建議仍由正式 read model 提供。" />{knowledge ? <div className="tp-topic-v1-knowledge-grid"><div className="tp-topic-v1-knowledge-summary"><h3>{knowledge.displayName}</h3><p>{knowledge.summary}</p><span className="tp-topic-v1-version">{knowledge.contentVersion}</span></div><div><h3>產業路徑</h3><p>{knowledge.industryPath.join(" ／ ")}</p></div><div><h3>應用場景</h3><ul>{(knowledge.applications ?? []).map((item) => <li key={item}>{item}</li>)}</ul></div><div><h3>觀察重點</h3><ul>{(knowledge.industryWatchPoints ?? []).map((item) => <li key={item}>{item}</li>)}</ul></div><div className="tp-topic-v1-knowledge-scope"><h3>範圍邊界</h3><p>{knowledge.scope?.focus ?? "尚未提供"}</p><p>{knowledge.scope?.distinction ?? "尚未提供"}</p></div></div> : <EmptyState title="題材介紹尚未提供" description="目前先保留正式 identity、hierarchy 與 market read model；不以瀏覽器臨時補寫題材知識。" />}</section>;
}

function statusValue(topic: TopicDetail, key: string): string {
  const item = topic.status.find((candidate) => candidate.key === key);
  return item?.state ?? "尚未提供";
}

function TopicStatusSection({ topic, publication }: { topic: TopicDetail; publication: ReturnType<typeof getTopicPublication> }) {
  // Legacy "核心結構三格" is intentionally retired from the primary UI; the formal boundary is now four readable cards.
  const cards = [["題材狀態", topic.readableState || "尚未提供"], ["族群表現", statusValue(topic, "族群表現")], ["領漲核心", statusValue(topic, "領漲核心")], ["動能擴散", statusValue(topic, "動能擴散")]];
  return <section className="tp-topic-v1-section tp-topic-v1-status" aria-labelledby="topic-v1-status-title"><TopicSectionHeading eyebrow="Formal structure" title="強度與結構" description="只呈現 read model 已提供的狀態欄位，不把成員漲跌、排名或缺口在前端合成新分數。" /><div className="tp-topic-v1-status-grid">{cards.map(([label, value]) => <div className="tp-topic-v1-status-card" key={label}><span>{label}</span><strong>{value}</strong></div>)}</div><div className="tp-topic-v1-status-foot"><span>資料覆蓋率：{topic.coveragePct == null ? "尚未提供" : `${topic.coveragePct}%`}</span><span>角色語義：由正式 relation metadata 提供</span><PublicationDisclosure disclosure={publication.participation} /></div></section>;
}

function FormalLifecycle({ lifecycle, publication }: { lifecycle: TopicLifecycle; publication: TopicPublicationDisclosure }) {
  const current = lifecycleStageForDetail(lifecycle.currentStage);
  const history = lifecycle.history ?? [];
  return <section className="tp-topic-v1-section tp-topic-v1-lifecycle-detail" aria-labelledby="topic-v1-lifecycle-detail-title"><TopicSectionHeading eyebrow="Formal lifecycle read model" title="題材生命週期" description="Overview 使用五個市場階段；Detail 另外保留 BASE 為「尚未形成」，不把它誤標成萌芽。" /><div className="tp-topic-v1-formal-boundary"><PublicationDisclosure disclosure={publication} /></div>{current ? <div className="tp-topic-v1-current-stage"><div><span>目前階段</span><strong>{current}</strong></div><div><span>進入日期</span><strong>{lifecycle.currentStageEnteredAt ?? "尚未提供"}</strong></div><div><span>Persistence</span><strong>{lifecycle.currentStageTradingDays == null ? "Day 尚未提供" : `Day ${lifecycle.currentStageTradingDays}`}</strong></div><div><span>轉換判定</span><strong>{lifecycle.transitionDecision ?? "尚未提供"}</strong></div></div> : <div className="tp-topic-v1-unavailable-block"><strong>生命週期尚未可安全呈現</strong><span>{lifecycle.currentStage ? `Backend stage ${lifecycle.currentStage} 尚未有可用的前台語義。` : "目前沒有 current stage。"}</span></div>}<div className="tp-topic-v1-stage-rail">{DETAIL_LIFECYCLE_STAGES.map((stage) => <div className={stage === current ? "is-active" : ""} key={stage}><span>{stage}</span><i /></div>)}</div>{history.length ? <div className="tp-topic-v1-lifecycle-history"><h3>正式階段歷史</h3>{history.map((segment, index) => { const label = lifecycleStageForDetail(segment.stage) ?? "階段尚未對應"; return <div className="tp-topic-v1-history-segment" key={`${segment.stage}-${segment.enteredAt ?? index}-${index}`}><span>{label}</span><small>{segment.enteredAt ?? "—"} → {segment.exitedAt ?? "目前"}</small><b>{segment.tradingDays == null ? "Day 尚未提供" : `Day ${segment.tradingDays}`}</b></div>; })}</div> : <p className="tp-topic-v1-muted">正式 Lifecycle history 尚未提供。</p>}</section>;
}

function pointY(value: number | null): number | null {
  return value == null || !Number.isFinite(value) ? null : 190 - Math.max(0, Math.min(100, value)) * 1.55;
}

function HistoryChart({ points }: { points: TopicHistoryPoint[] }) {
  const absolutePoints = points.map((point, index) => ({ point, index, y: pointY(point.absoluteScore) })).filter((item): item is { point: TopicHistoryPoint; index: number; y: number } => item.y !== null);
  const relativePoints = points.map((point, index) => ({ point, index, y: pointY(point.relativeScore) })).filter((item): item is { point: TopicHistoryPoint; index: number; y: number } => item.y !== null);
  const x = (index: number) => points.length <= 1 ? 56 : 56 + (index / (points.length - 1)) * 640;
  return <div className="tp-topic-v1-chart-wrap"><svg className="tp-topic-v1-history-chart" viewBox="0 0 740 230" role="img" aria-label="正式題材歷史觀測點"><line x1="56" y1="35" x2="56" y2="190" /><line x1="56" y1="190" x2="696" y2="190" /><text x="18" y="42">100</text><text x="31" y="116">50</text><text x="38" y="194">0</text>{absolutePoints.map(({ point, index, y }) => <circle className="tp-topic-v1-chart-point absolute" cx={x(index)} cy={y} r="4" key={`absolute-${point.date}`}><title>絕對強度 {point.date}：{point.absoluteScore}</title></circle>)}{relativePoints.map(({ point, index, y }) => <circle className="tp-topic-v1-chart-point relative" cx={x(index)} cy={y} r="4" key={`relative-${point.date}`}><title>相對市場 {point.date}：{point.relativeScore}</title></circle>)}{points.filter((point) => point.absoluteScore !== null || point.relativeScore !== null).map((point) => <text x={x(points.indexOf(point))} y="214" textAnchor="middle" key={`date-${point.date}`}>{point.date.slice(5)}</text>)}</svg><div className="tp-topic-v1-chart-legend"><span><i className="absolute" />絕對強度正式觀測</span><span><i className="relative" />相對市場正式觀測</span></div></div>;
}

function HistoricalSection({ slug, source }: { slug: string; source: TopicSource }) {
  const [range, setRange] = useState<20 | 60 | 120>(20);
  const [resource, setResource] = useState<TopicResource<TopicHistoryPoint[]> | null>(null);
  const [loadedRange, setLoadedRange] = useState<20 | 60 | 120 | null>(null);
  useEffect(() => { let active = true; fetchTopicHistory(slug, range).then((next) => { if (active) { setResource(next); setLoadedRange(range); } }); return () => { active = false; }; }, [range, slug]);
  const points = resource?.data ?? [];
  const historyReady = loadedRange === range;
  return <section className="tp-topic-v1-section tp-topic-v1-history" aria-labelledby="topic-v1-history-title"><div className="tp-topic-v1-section-heading"><div><p className="tp-overline">Formal history only</p><h2 id="topic-v1-history-title">歷史走勢與輪動</h2><p>只繪製正式 snapshot 觀測點；缺口保留，不使用 Preview、合成序列或相對值代理。</p></div><div className="tp-topic-v1-range-switch" role="group" aria-label="歷史區間">{([20, 60, 120] as const).map((item) => <button type="button" className={range === item ? "is-active" : ""} onClick={() => setRange(item)} key={item}>{item}日</button>)}</div></div>{source === "synthetic-snapshot" && <div className="tp-topic-v1-unavailable-block"><strong>Preview 不提供正式歷史序列</strong><span>請連線正式 API 後再查看。</span></div>}{source !== "synthetic-snapshot" && historyReady && resource?.source === "unavailable" && <div className="tp-topic-v1-unavailable-block"><strong>正式歷史尚未提供</strong><span>{resource.error ?? "目前沒有可繪製的正式觀測點。"}</span></div>}{source !== "synthetic-snapshot" && historyReady && resource?.source === "api" && points.length > 0 && <HistoryChart points={points} />}{source !== "synthetic-snapshot" && historyReady && resource?.source === "api" && points.length === 0 && <EmptyState title="正式歷史觀測點尚未累積" description="沒有資料時不繪製零值，也不把缺口補成連續曲線。" />}<p className="tp-topic-v1-history-footnote">生命週期以獨立 categorical rail 呈現，不轉換成數值線。</p></section>;
}

function MemberDrawer({ topic, onClose }: { topic: TopicDetail; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const members = topic.constituents.filter((member) => `${member.code} ${member.name} ${member.role ?? ""}`.toLocaleLowerCase("zh-TW").includes(query.trim().toLocaleLowerCase("zh-TW")));
  return <div className="tp-topic-v1-drawer-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><aside className="tp-topic-v1-drawer" role="dialog" aria-modal="true" aria-label="完整題材成員"><header className="tp-topic-v1-drawer-header"><div><p className="tp-overline">Formal relations</p><h2>完整成員清單</h2></div><button type="button" className="tp-topic-v1-close" onClick={onClose} aria-label="關閉"><X size={18} /></button></header><label className="tp-topic-v1-drawer-search"><Search size={16} /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜尋股號或股名" /></label><div className="tp-topic-v1-drawer-body">{members.map((member) => <Link href={`/stocks/${member.code}`} className="tp-topic-v1-member-drawer-row" key={member.code}><span><b>{member.code} · {member.name}</b><small>{member.role ?? "角色尚未提供"}</small></span><strong className={`tp-topic-v1-change--${changeTone(member.changePct)}`}>{changeCopy(member.changePct)}</strong></Link>)}</div></aside></div>;
}

function ConstituentsSection({ topic, source, publication, onOpen }: { topic: TopicDetail; source: TopicSource; publication: ReturnType<typeof getTopicPublication>; onOpen: () => void }) {
  const visible = topic.constituents.slice(0, 12);
  return <section className="tp-topic-v1-section tp-topic-v1-constituents" aria-labelledby="topic-v1-members-title"><TopicSectionHeading eyebrow="Formal relation members" title="正式成分與關聯股票" description="角色直接沿用 relation API；不從漲幅推定代表股、核心股或排名。" /><div className="tp-topic-v1-member-heading"><div><h3 id="topic-v1-members-title">題材成員</h3><p>{source === "synthetic-snapshot" && <PreviewBadge />} {topic.constituents.length} 檔 relation rows</p></div>{topic.constituents.length > 12 && <button type="button" className="tp-topic-v1-more-button" onClick={onOpen}>查看全部 {topic.constituents.length} 檔</button>}</div><div className="tp-topic-v1-formal-boundary"><PublicationDisclosure disclosure={publication.relations} /><PublicationDisclosure disclosure={publication.leaderCore} /></div>{topic.constituents.length ? <Table><thead><tr><th>股號</th><th>股名</th><th>角色</th><th>今日漲跌幅</th></tr></thead><tbody>{visible.map((member) => <tr key={member.code}><td><Link href={`/stocks/${member.code}`}>{member.code}</Link></td><td><Link href={`/stocks/${member.code}`}>{member.name}</Link></td><td><RoleChip>{member.role ?? "角色尚未提供"}</RoleChip></td><td><span className={`tp-topic-v1-change--${changeTone(member.changePct)}`}>{changeCopy(member.changePct)}</span></td></tr>)}</tbody></Table> : <EmptyState title="目前沒有正式成分股資料" description="Topic read model 尚未回傳 constituent rows。" />}</section>;
}

function rawValue(value: unknown): string {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  return "尚未提供";
}

function OwnerSeededV0Section({ topic }: { topic: TopicDetail }) {
  const strength = topic.ownerSeededV0;
  const observation = topic.forwardObservation;
  return <details className="tp-topic-v1-diagnostics-block"><summary>工程診斷與 lineage（收合）</summary><div className="tp-topic-v1-diagnostics-grid"><span>ownerSeededV0 status</span><b>{rawValue(strength?.status)}</b><span>Absolute</span><b>{rawValue(strength?.absolute?.grade)} · {rawValue(strength?.absolute?.score)}</b><span>Relative</span><b>{rawValue(strength?.relative?.grade)} · {rawValue(strength?.relative?.score)}</b><span>data-checkpoint-status</span><b>{rawValue(observation?.checkpointStatus ? JSON.stringify(observation.checkpointStatus) : null)}</b><span>SMALL_SAMPLE_X</span><b>{strength?.observationFlags?.includes("SMALL_SAMPLE_X") ? "true" : "尚未提供"}</b><span>leader_change_pct</span><b>{rawValue(topic.lifecycle?.evidence?.leadership?.leaderChangePct)} · PROXY evidence only</b></div><p>Owner-seeded V0、Forward Observation 與 raw evidence 僅作診斷；不覆蓋正式 Strength／Lifecycle authority。</p></details>;
}

function DiagnosticsSection({ topic, source, publication }: { topic: TopicDetail; source: TopicSource; publication: ReturnType<typeof getTopicPublication> }) {
  return <section className="tp-topic-v1-section tp-topic-v1-diagnostics"><details><summary>資料來源、品質與 publication 邊界（收合）</summary><div className="tp-topic-v1-diagnostics-grid"><span>source</span><b>{sourceLabel(source)}</b><span>identity</span><b><PublicationDisclosure disclosure={publication.identity} /></b><span>hierarchy</span><b><PublicationDisclosure disclosure={publication.hierarchy} /></b><span>grade</span><b><PublicationDisclosure disclosure={publication.grade} /></b><span>summary</span><b><PublicationDisclosure disclosure={publication.summary} /></b><span>events</span><b><PublicationDisclosure disclosure={publication.events} /></b><span>opportunity</span><b><PublicationDisclosure disclosure={publication.opportunity} /></b><span>participation</span><b><PublicationDisclosure disclosure={publication.participation} /></b><span>lifecycle status</span><b data-checkpoint-status={topic.lifecycle?.dataStatus}>{lifecycleStatusLabel(topic.lifecycle?.dataStatus)}</b><span>lineage</span><b>{rawValue(topic.lineage ? JSON.stringify(topic.lineage) : null)}</b><span>今日強度</span><b>{rawValue(topic.formalStrength?.absolute.grade)} · {rawValue(topic.formalStrength?.absolute.score)}</b><span>觀察中</span><b>{rawValue(topic.forwardObservation?.status)}</b></div></details><OwnerSeededV0Section topic={topic} /></section>;
}

export default function TopicDetailPage({ slug }: { slug: string }) {
  const [resource, setResource] = useState<TopicResource<TopicDetail> | null>(null);
  const [memberDrawer, setMemberDrawer] = useState(false);
  const { isFavorite, toggle: toggleTopicFavorite } = useTopicFavoritesState();
  useEffect(() => { let active = true; fetchTopic(slug).then((next) => { if (active) setResource(next); }); return () => { active = false; }; }, [slug]);
  useEffect(() => { const handler = (event: KeyboardEvent) => { if (event.key === "Escape") setMemberDrawer(false); }; document.addEventListener("keydown", handler); return () => document.removeEventListener("keydown", handler); }, []);
  const topic = resource?.data;
  const publication = topic && resource ? getTopicPublication(resource.source, topic) : null;
  const source = resource?.source ?? "unavailable";
  return <AppShell currentPath="/topics"><PageContainer className="tp-topic-page tp-topic-v1-page" title={topic?.name ?? slug} hideHeader><div className="tp-topic-v1-detail-page">{!resource && <Card className="tp-topic-data-card"><DataState state="STALE" /><EmptyState title="正在載入題材資料" description="正在讀取 Topic read model。" /></Card>}{resource?.source === "unavailable" && <Card className="tp-topic-data-card"><DataState state="UNAVAILABLE" /><EmptyState title="題材資料目前無法取得" description={resource.error ?? "請確認正式 API 狀態。"} /></Card>}{topic && publication && <><Hero topic={topic} source={source} favorite={isFavorite(slug)} onToggle={() => toggleTopicFavorite(slug, { displayLabel: topic.name })} />{topic.kind === "PARENT" ? <div className="tp-topic-v1-parent-detail"><TodayJudgementSection topic={topic} publication={publication} /><section className="tp-topic-v1-section"><TopicSectionHeading title="題材階層" description="Parent Topic 保留 canonical children；請從下方入口進入 Leaf Detail。" /><div className="tp-topic-v1-child-links">{topic.hierarchy.children.map((child) => <Link href={`/topics/${child.slug}`} key={child.slug}>{child.name}<ChevronRight size={16} /></Link>)}</div></section></div> : <div className="tp-topic-v1-detail-content"><TodayJudgementSection topic={topic} publication={publication} /><TopicKnowledgeSection topic={topic} /><TopicStatusSection topic={topic} publication={publication} />{topic.lifecycle && <FormalLifecycle lifecycle={topic.lifecycle} publication={publication.lifecycle} />}<HistoricalSection slug={slug} source={source} /><ConstituentsSection topic={topic} source={source} publication={publication} onOpen={() => setMemberDrawer(true)} /><DiagnosticsSection topic={topic} source={source} publication={publication} /></div>}{memberDrawer && <MemberDrawer topic={topic} onClose={() => setMemberDrawer(false)} />}</>}</div></PageContainer></AppShell>;
}
