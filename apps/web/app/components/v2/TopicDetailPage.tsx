"use client";

import Link from "next/link";
import { ChevronRight, Star } from "lucide-react";
import { useEffect, useState } from "react";
import {
  fetchTopic,
  getTopicPublication,
  lifecycleStageAvailable,
  lifecycleStatusLabel,
  scoreLabel,
  sourceLabel,
  type TopicConstituent,
  type TopicDetail as TopicData,
  type TopicLifecycle,
  type TopicPublicationDisclosure,
  type TopicResource,
  type TopicStatus,
} from "../../lib/topic-api";
import { getTopicPreview, PREVIEW_LABEL, type TopicPreview } from "../../lib/topic-preview";
import { ownerStageFromBackend } from "../../lib/topic-lifecycle-contract";
import { useTopicFavoritesState } from "../FavoriteButton";
import { AppShell, Card, DataState, EmptyState, GradeChip, PageContainer, RoleChip, Table } from "./V2Foundation";
import { StockEncyclopediaDrawer, type StockDrawerItem } from "./StockEncyclopediaDrawer";

const LIFECYCLE_STAGES = ["萌芽", "發酵", "主升", "成熟", "衰退"] as const;
const CORE_STRUCTURE_KEYS: TopicStatus["key"][] = ["族群表現", "領漲核心", "動能擴散"];

function TopicSectionHeading({
  title,
  description,
  preview = false,
}: {
  title: string;
  description?: string;
  preview?: boolean;
}) {
  return <div className="tp-topic-section-heading"><div><h2>{title}</h2>{description && <p>{description}</p>}</div>{preview && <PreviewBadge />}</div>;
}

function PreviewBadge() {
  return <span className="tp-preview-badge">{PREVIEW_LABEL}</span>;
}

const PUBLICATION_FIELD_LABELS: Record<TopicPublicationDisclosure["field"], string> = {
  identity: "Identity",
  hierarchy: "Hierarchy",
  relations: "Relations",
  score: "Score",
  grade: "Grade",
  snapshot: "Snapshot",
  participation: "Participation",
  lifecycle: "Lifecycle",
  leaderCore: "Leader/Core",
  technicalRelative: "Technical/Relative",
  events: "Events",
  news: "News",
  heatmap: "Heatmap",
  summary: "Summary",
  opportunity: "Opportunity",
  source: "Source",
};

function PublicationDisclosure({ disclosure }: { disclosure: TopicPublicationDisclosure }) {
  return <span className="tp-chip tp-topic-publication-state" data-publication-field={disclosure.field} data-publication-state={disclosure.state} aria-label={`${PUBLICATION_FIELD_LABELS[disclosure.field]}: ${disclosure.state}`} title={disclosure.note}>{PUBLICATION_FIELD_LABELS[disclosure.field]}: {disclosure.state}</span>;
}

function previewDisclosure(field: TopicPublicationDisclosure["field"], note: string): TopicPublicationDisclosure {
  return { field, state: "PREVIEW", note };
}

function changeTone(value: number | null): "up" | "down" | null {
  return value === null ? null : value >= 0 ? "up" : "down";
}

function formalLifecycleStage(stage: string | null): (typeof LIFECYCLE_STAGES)[number] | null {
  return ownerStageFromBackend(stage);
}

function ResearchValue({
  label,
  value,
  disclosure,
  note,
}: {
  label: string;
  value: string | null;
  disclosure: TopicPublicationDisclosure;
  note?: string;
}) {
  const hasValue = value !== null && value !== "";
  return <div className="tp-topic-research-value"><span>{label}</span>{hasValue ? <strong data-publication-state={disclosure.state}>{value}</strong> : <div className="tp-topic-research-value-pending"><PublicationDisclosure disclosure={disclosure} /><strong>尚未提供</strong></div>}{note && <small>{note}</small>}</div>;
}

function TodayStatusSection({
  topic,
  preview,
  publication,
}: {
  topic: TopicData;
  preview: TopicPreview | null;
  publication: ReturnType<typeof getTopicPublication>;
}) {
  // Formal null copy remains explicit: resource.source === "api" ? "資料日期待補" : "Preview".
  const snapshotDisclosure = preview
    ? previewDisclosure("snapshot", "目前為明確開啟的 Preview 題材資料。")
    : publication.snapshot;
  const stateDisclosure = preview
    ? previewDisclosure("snapshot", "Preview 狀態不代表正式 Topic Snapshot。")
    : publication.snapshot;
  const dateDisclosure = preview
    ? previewDisclosure("snapshot", "Preview 沒有正式資料日期。")
    : publication.snapshot;

  return <Card className="tp-topic-detail-card tp-topic-today-status-card"><TopicSectionHeading title="今日狀態" description="先確認目前能由 Topic read model 支持的結論；缺少正式欄位時保留明確狀態。" preview={Boolean(preview)} /><div className="tp-topic-research-grid tp-topic-research-grid--summary">
    <ResearchValue label="題材狀態" value={preview || topic.strengthState ? topic.readableState : null} disclosure={stateDisclosure} note={preview ? "Explicit Preview" : undefined} />
    <ResearchValue label="今日方向" value={topic.direction} disclosure={snapshotDisclosure} note={preview ? "Explicit Preview field" : undefined} />
    <ResearchValue label="資料日期" value={topic.dataDate} disclosure={dateDisclosure} />
    <ResearchValue label="覆蓋率" value={topic.coveragePct === null ? null : `${topic.coveragePct}%`} disclosure={snapshotDisclosure} />
  </div></Card>;
}

function TopicStatusSection({
  topic,
  preview,
  publication,
}: {
  topic: TopicData;
  preview: TopicPreview | null;
  publication: ReturnType<typeof getTopicPublication>;
}) {
  const previewValues: Record<TopicStatus["key"], string> = {
    族群表現: preview?.metrics.participation ?? "",
    領漲核心: preview?.metrics.leaderDrive ?? "",
    動能擴散: preview?.metrics.leaderConsistency ?? "",
  };

  return <Card className="tp-topic-detail-card tp-topic-status-card"><TopicSectionHeading title="核心結構三格" description="沿用現有 Topic status 欄位；本頁不計算 score、breadth、concentration 或 leadership。" preview={Boolean(preview)} /><div className="tp-topic-publication-row"><PublicationDisclosure disclosure={preview ? previewDisclosure("participation", "三格內容為明確 Preview，不代表正式結構指標。") : publication.participation} /></div><div className="tp-topic-status-grid">{CORE_STRUCTURE_KEYS.map((key) => {
    const item = topic.status.find((status) => status.key === key);
    const value = preview ? previewValues[key] || null : item?.state ?? null;
    const disclosure = preview
      ? previewDisclosure("participation", "Preview value is not promoted to formal metric.")
      : item?.state
        ? { field: "participation" as const, state: "FORMAL" as const, note: "由 Topic API status 欄位提供。" }
        : publication.participation;
    const note = item?.state ? "正式 API status 欄位" : typeof item?.evidence?.reason === "string" ? item.evidence.reason : undefined;
    return <ResearchValue key={key} label={key} value={value} disclosure={disclosure} note={note} />;
  })}</div></Card>;
}

function rawValue(value: unknown): string | null {
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  if (typeof value === "string" && value.trim()) return value;
  return null;
}

function lifecycleUnavailableCopy(status: TopicLifecycle["dataStatus"], hasUnknownStage: boolean): string {
  if (hasUnknownStage) return "Backend 回傳的 current stage 不是目前核准的五階段；前端 fail closed，不自行映射。";
  switch (status) {
    case "INSUFFICIENT_DATA": return "目前觀測資料不足以支持 Lifecycle stage；不顯示任何五階段。";
    case "PENDING": return "Lifecycle 尚在等待 backend 評估；不由前端推導 stage。";
    case "WAITING_FOR_FORMAL_LINEAGE": return "Lifecycle 等待正式 lineage；目前只保留狀態與品質揭露。";
    case "FAIL_CLOSED": return "Backend 已 fail closed；前端不補值、不推導 stage。";
    case "NOT_AVAILABLE": return "目前沒有可用的 Lifecycle read-model 資料。";
    case "PREVIEW": return "Preview lifecycle 不代表正式或 Forward Shadow 資料。";
    default: return "目前沒有可供前端安全呈現的 Lifecycle stage。";
  }
}

function LifecycleQuality({ lifecycle, disclosure }: { lifecycle: TopicLifecycle; disclosure: TopicPublicationDisclosure }) {
  const confidence = lifecycle.confidence ?? {};
  const lineage = lifecycle.lineage ?? {};
  const observed = rawValue(confidence.observedMemberCount);
  const expected = rawValue(confidence.expectedMemberCount);
  const sampleSize = rawValue(confidence.sampleSize) ?? (observed !== null || expected !== null ? `${observed ?? "—"} / ${expected ?? "—"}` : null);
  const lineageValue = rawValue(lineage.lineageHash) ?? (Object.keys(lineage).length ? "Backend lineage metadata" : null);
  const qualityDisclosure = { field: "lifecycle" as const, state: disclosure.state, note: "quality metadata 由 canonical Lifecycle API 提供；不納入 Strength vector。" };
  return <div className="tp-topic-lifecycle-quality"><div className="tp-topic-publication-row"><span className="tp-chip" data-lifecycle-status={lifecycle.dataStatus}>資料狀態: {lifecycleStatusLabel(lifecycle.dataStatus)}</span><span className="tp-chip">Authority: {disclosure.state === "SHADOW" ? "Forward Shadow backend" : "canonical API"}</span></div><div className="tp-topic-research-grid tp-topic-research-grid--quality">
    <ResearchValue label="coverage" value={rawValue(confidence.coveragePct)} disclosure={qualityDisclosure} />
    <ResearchValue label="confidence" value={rawValue(confidence.confidence)} disclosure={qualityDisclosure} />
    <ResearchValue label="sample size" value={sampleSize} disclosure={qualityDisclosure} note="observed / expected member count；不由前端估算。" />
    <ResearchValue label="lineage" value={lineageValue} disclosure={qualityDisclosure} />
  </div></div>;
}

function FormalLifecycle({ lifecycle, disclosure }: { lifecycle: TopicLifecycle; disclosure: TopicPublicationDisclosure }) {
  const current = formalLifecycleStage(lifecycle.currentStage);
  const hasUnknownStage = Boolean(lifecycle.currentStage) && current === null;
  const canRenderStage = lifecycleStageAvailable(lifecycle.dataStatus) && current !== null;
  const statusDescription = lifecycleUnavailableCopy(lifecycle.dataStatus, hasUnknownStage);
  return <Card className="tp-topic-detail-card tp-topic-detail-lifecycle-card"><TopicSectionHeading title="題材生命週期" description="current stage、transition 與 persistence 只由 canonical backend Lifecycle read model 提供；前端不自行計算。" /><div className="tp-topic-publication-row"><PublicationDisclosure disclosure={disclosure} /></div>{canRenderStage ? <><div className="tp-topic-detail-lifecycle-current"><span>目前階段</span><strong>{current}</strong><b>{lifecycle.currentStageEnteredAt ?? "—"}</b><span>{lifecycle.currentStageTradingDays === null ? "Persistence 待提供" : `Day ${lifecycle.currentStageTradingDays}`}</span></div><div className="tp-topic-lifecycle-transition"><span>Previous stage</span><strong>{formalLifecycleStage(lifecycle.previousStage ?? null) ?? "—"}</strong><span>Transition</span><strong>{lifecycle.transitionDecision ?? "—"}</strong><span>Reason</span><strong>{lifecycle.transitionReason ?? "—"}</strong></div><ol className="tp-topic-detail-lifecycle-track">{LIFECYCLE_STAGES.map((stage) => { const segment = lifecycle.history.find((item) => formalLifecycleStage(item.stage) === stage); const active = current === stage; return <li className={active ? "is-active" : ""} key={stage}><span className="tp-topic-detail-lifecycle-dot" aria-hidden="true" /><strong>{stage}</strong><small>{segment?.enteredAt ?? "—"}</small><em>{segment?.tradingDays === null || segment?.tradingDays === undefined ? "—" : `Day ${segment.tradingDays}`}</em></li>; })}</ol></> : <><div className="tp-topic-lifecycle-status" data-lifecycle-status={lifecycle.dataStatus}><strong>{lifecycleStatusLabel(lifecycle.dataStatus)}</strong><span>{lifecycle.currentStage ? `Backend stage ${lifecycle.currentStage} 未能安全呈現` : "目前沒有 current stage"}</span></div><EmptyState title="生命週期階段尚未可用" description={statusDescription} />{(lifecycle.transitionDecision || lifecycle.transitionReason) && <div className="tp-topic-lifecycle-transition"><span>Transition</span><strong>{lifecycle.transitionDecision ?? "—"}</strong><span>Reason</span><strong>{lifecycle.transitionReason ?? "—"}</strong></div>}</>}<LifecycleQuality lifecycle={lifecycle} disclosure={disclosure} /></Card>;
}

function StrengthEvidenceSection({ lifecycle, disclosure }: { lifecycle: TopicLifecycle; disclosure: TopicPublicationDisclosure }) {
  const evidence = lifecycle.evidence ?? {};
  const positiveBreadth = rawValue(evidence.diffusion?.positiveBreadth);
  const strongBreadth = rawValue(evidence.groupStrength?.strongBreadth);
  const weakRatio = rawValue(evidence.groupStrength?.weakRatio);
  const averageChange = rawValue(evidence.groupStrength?.averageChangePct);
  const leaderChange = rawValue(evidence.leadership?.leaderChangePct);
  const evidenceDisclosure = { field: "lifecycle" as const, state: disclosure.state, note: "Raw Evidence Vector 由 canonical Lifecycle API 提供；前端不合成 Strength score。" };
  return <Card className="tp-topic-detail-card tp-topic-strength-evidence-card"><TopicSectionHeading title="Strength Raw Evidence V0" description="只呈現 backend raw evidence vector；不建立 dimension label、overall strength level 或 0–100 score。" /><div className="tp-topic-publication-row"><PublicationDisclosure disclosure={disclosure} /></div><div className="tp-topic-research-grid"><ResearchValue label="positive_breadth" value={positiveBreadth} disclosure={evidenceDisclosure} note="raw API evidence" /><ResearchValue label="strong_breadth" value={strongBreadth} disclosure={evidenceDisclosure} note="raw API evidence" /><ResearchValue label="weak_ratio" value={weakRatio} disclosure={evidenceDisclosure} note="raw API evidence" /><ResearchValue label="average_change_pct" value={averageChange} disclosure={evidenceDisclosure} note="raw API evidence" /><ResearchValue label="leader_change_pct" value={leaderChange} disclosure={evidenceDisclosure} note="PROXY evidence only；不是正式 Leader Set truth" /></div><p className="tp-topic-strength-evidence-note">coverage、confidence、sample size、data status、lineage 與 authority 保持為 quality metadata，不納入 Strength vector。</p></Card>;
}

function ConstituentsSection({
  stocks,
  publication,
  onSelect,
}: {
  stocks: TopicConstituent[];
  publication: ReturnType<typeof getTopicPublication>;
  onSelect: (stock: TopicConstituent) => void;
}) {
  return <section aria-labelledby="stocks-title"><TopicSectionHeading title="正式成分與關聯股票" description="依 current relation API 的既有順序呈現；這裡不把任意前幾檔命名為領漲股。" /><Card className="tp-topic-role-card tp-topic-stock-table-card"><div className="tp-topic-role-heading"><div><p className="tp-overline">Topic constituents</p><h3 id="stocks-title">研究股票清單</h3></div><RoleChip>{stocks.length} 檔</RoleChip></div><div className="tp-topic-publication-row"><PublicationDisclosure disclosure={publication.relations} /><PublicationDisclosure disclosure={publication.leaderCore} /></div><p className="tp-topic-constituent-note">「後端關係角色」只顯示 API 已提供的 relation metadata；正式 Leader Set / 領漲排名尚未發布。</p>{stocks.length ? <Table><thead><tr><th>股票／股號</th><th>後端關係角色</th><th>今日漲跌</th><th>題材表現</th><th>技術狀態</th><th>更新狀態</th><th>Action</th></tr></thead><tbody>{stocks.map((stock) => { const tone = changeTone(stock.changePct); const open = () => onSelect(stock); return <tr key={stock.code} className="tp-topic-stock-table-row" role="button" tabIndex={0} onClick={open} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(); } }} aria-label={`查看${stock.name}股票圖鑑`}><td><span className="tp-topic-stock-identity"><b>{stock.name}</b><small>{stock.code}</small></span></td><td><RoleChip>{stock.role ?? "角色尚未提供"}</RoleChip></td><td>{stock.changePct === null ? <span className="tp-muted">—</span> : <span className={`tp-topic-change tp-topic-change--${tone}`}>{stock.changePct >= 0 ? "+" : ""}{stock.changePct.toFixed(2)}%</span>}</td><td>{stock.relativeTopicState ? <span>{stock.relativeTopicState}</span> : <span className="tp-topic-field-pending">尚未提供</span>}</td><td>{stock.technicalState ? <span>{stock.technicalState}</span> : <span className="tp-topic-field-pending">尚未提供</span>}</td><td>{stock.dataFreshness ?? "資料待更新"}</td><td><span className="tp-topic-row-action">查看 <ChevronRight size={16} aria-hidden="true" /></span></td></tr>; })}</tbody></Table> : <EmptyState title="目前沒有正式成分股資料" description="Topic read model 尚未回傳 constituent rows。" />}</Card></section>;
}

function DescriptionSection({ preview, publication }: { preview: TopicPreview | null; publication: ReturnType<typeof getTopicPublication> }) {
  return <Card className="tp-topic-detail-card tp-topic-description-card"><TopicSectionHeading title="題材說明" description="正式 narrative 只在 current authority 有提供時顯示；其餘狀態保留清楚的資料邊界。" preview={Boolean(preview)} />{preview ? <div className="tp-topic-preview-copy"><PreviewBadge /><p>{preview.summary}</p></div> : <><PublicationDisclosure disclosure={publication.summary} /><EmptyState title="正式題材說明尚未提供" description="Production 不以 Preview 內容覆蓋正式題材 identity；目前只有 identity、hierarchy 與 relation read path。" /></>}</Card>;
}

function RelatedTopicsSection({ preview, publication }: { preview: TopicPreview | null; publication: ReturnType<typeof getTopicPublication> }) {
  return <Card className="tp-topic-detail-card tp-topic-related-section"><TopicSectionHeading title="層級與相關題材" description="Hierarchy 只來自 formal identity/group；相關題材沒有 formal relations contract 時不由名稱相似度推導。" preview={Boolean(preview)} />{preview ? <div className="tp-topic-related-grid">{preview.related.map((related) => <Link href={`/topics/${related.slug}`} className="tp-topic-related-card" key={related.slug}><span className="tp-topic-related-strength">Preview</span><div><strong>{related.name}</strong><span>{related.state}</span></div><span className="tp-chip tp-grade-chip">{related.grade}</span><ChevronRight size={18} aria-hidden="true" /></Link>)}</div> : <><PublicationDisclosure disclosure={publication.relations} /><EmptyState title="相關題材尚未發布" description="目前沒有 formal related-topic read model；不由瀏覽器自行建立關聯。" /></>}</Card>;
}

function HistoricalSection({ preview, publication }: { preview: TopicPreview | null; publication: ReturnType<typeof getTopicPublication> }) {
  return <Card className="tp-topic-detail-card tp-topic-history-placeholder"><TopicSectionHeading title="歷史走勢與輪動" description="Historical/timeline read model 尚未接入；L5 retrospective reconstruction artifact 不直接發布到 production frontend。" preview={Boolean(preview)} /><div className="tp-topic-publication-row"><PublicationDisclosure disclosure={preview ? previewDisclosure("events", "Preview 不提供正式歷史序列。") : publication.events} /><PublicationDisclosure disclosure={preview ? previewDisclosure("heatmap", "Preview 不提供正式 rotation visualization。") : publication.heatmap} /><PublicationDisclosure disclosure={preview ? previewDisclosure("opportunity", "Preview 不提供正式 opportunity。") : publication.opportunity} /></div><EmptyState title="歷史資料待接入／累積中" description="目前只保留未來 history/timeline read-model 介面；不把 retrospective reconstruction 顯示成 Forward Shadow 或 PIT historical truth。" /></Card>;
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
  const { isFavorite, toggle: toggleTopicFavorite } = useTopicFavoritesState();
  const [selectedStock, setSelectedStock] = useState<TopicConstituent | null>(null);
  const favorite = isFavorite(slug);

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
  const publication = topic && resource ? getTopicPublication(resource.source, topic) : null;

  return <AppShell currentPath="/topics"><PageContainer className="tp-topic-page" title={topic?.name ?? slug} hideHeader><div className="tp-topic-detail-page">
    {!resource && <Card className="tp-topic-data-card"><DataState state="STALE" /><EmptyState title="正在載入題材資料" description="正在讀取 Topic read model。" /></Card>}
    {resource?.source === "unavailable" && <Card className="tp-topic-data-card"><DataState state="UNAVAILABLE" /><EmptyState title="題材資料目前無法取得" description={resource.error ?? "請確認 FastAPI read model 是否已啟動。"} /></Card>}
    {topic && publication && <>
      <header className="tp-topic-identity">
        <nav className="tp-topic-breadcrumb" aria-label="題材階層"><Link href="/topics">題材</Link><span aria-hidden="true">›</span>{topic.groupName && <><span>{topic.groupName}</span><span aria-hidden="true">›</span></>}<strong>{topic.name}</strong></nav>
        <div className="tp-topic-title-row"><div><p className="tp-overline">題材研究工作台 · {sourceLabel(resource.source)} <PublicationDisclosure disclosure={publication.source} /></p><h1>{topic.name}</h1></div><button type="button" className={`tp-topic-favorite ${favorite ? "is-active" : ""}`} aria-label={favorite ? `取消收藏 ${topic.name}` : `收藏 ${topic.name}`} aria-pressed={favorite} onClick={() => toggleTopicFavorite(slug, { displayLabel: topic.name })}><Star size={18} fill={favorite ? "currentColor" : "none"} aria-hidden="true" />{favorite ? "已收藏題材" : "收藏題材"}</button></div>
        <div className="tp-topic-meta-row"><span className="tp-topic-identity-disclosure"><PublicationDisclosure disclosure={publication.identity} /><PublicationDisclosure disclosure={publication.hierarchy} /></span>{topic.grade ? <GradeChip grade={topic.grade} /> : <PublicationDisclosure disclosure={publication.grade} />}<span><b>題材強度</b> {topic.score === null ? <PublicationDisclosure disclosure={publication.score} /> : scoreLabel(topic.score)}</span><span><b>目前狀態</b> {topic.strengthState ? topic.readableState : <PublicationDisclosure disclosure={publication.snapshot} />}</span><span><b>股票數</b> {topic.constituentCount} 檔</span></div>
      </header>

      <div className="tp-topic-content tp-topic-research-workspace">
        <TodayStatusSection topic={topic} preview={preview} publication={publication} />
        <TopicStatusSection topic={topic} preview={preview} publication={publication} />
        <ConstituentsSection stocks={stocks} publication={publication} onSelect={setSelectedStock} />
        {selectedStock && <StockEncyclopediaDrawer presentation="inline" stock={stockDrawerItem(topic, selectedStock, resource)} onClose={() => setSelectedStock(null)} />}
        <FormalLifecycle lifecycle={topic.lifecycle} disclosure={publication?.lifecycle ?? { field: "lifecycle", state: "UNAVAILABLE", note: "正式 Lifecycle 尚未提供。" }} />
        <StrengthEvidenceSection lifecycle={topic.lifecycle} disclosure={publication?.lifecycle ?? { field: "lifecycle", state: "UNAVAILABLE", note: "Strength raw evidence 尚未提供。" }} />
        <DescriptionSection preview={preview} publication={publication} />
        <RelatedTopicsSection preview={preview} publication={publication} />
        <HistoricalSection preview={preview} publication={publication} />
      </div>
    </>}
  </div></PageContainer></AppShell>;
}
