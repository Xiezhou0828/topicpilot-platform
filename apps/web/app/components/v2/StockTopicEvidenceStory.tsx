"use client";

import { ExternalLink, ShieldAlert } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import {
  getTopicStoryEvidence,
  type EvidenceStatus,
  type TopicStoryCollection,
  type TopicStoryEdge,
  type TopicStoryFinancialImpact,
  type TopicStoryNode,
  type TopicStoryView,
} from "../../lib/stock-topic-evidence-preview";

const PATTERN_LABELS: Record<TopicStoryView["storyPattern"], string> = {
  PRODUCT_SUPPLY_CHAIN: "產品與材料關聯",
  PRICE_PROFIT_TRANSMISSION: "價格與損益傳導",
  ASSET_PROJECT_TIMELINE: "資產與策略時間軸",
  EVIDENCE_GAP: "正式關聯與證據缺口",
  GENERAL_OPERATING_RELATIONSHIP: "營運關聯摘要",
};

const STATUS_LABELS: Record<EvidenceStatus, string> = {
  FACT: "已確認事實",
  INFERENCE: "研究推論",
  UNVERIFIED: "待驗證",
  UNDISCLOSED: "尚未揭露",
};

const STATUS_HELP: Record<EvidenceStatus, string> = {
  FACT: "公開資料中可以直接核對的事實。",
  INFERENCE: "根據公開資料整理出的研究判斷，不等同已證實因果。",
  UNVERIFIED: "目前有線索，但尚未完成可核對的確認。",
  UNDISCLOSED: "目前沒有取得公開揭露資料。",
};

const ROLE_LABELS: Record<string, string> = {
  CORE: "核心",
  PRIMARY: "主要",
  SECONDARY: "次要",
  RELATED: "關聯",
  REPRESENTATIVE: "代表性",
};

const RELATION_LABELS: Record<string, string> = {
  PRIMARY: "主要關聯",
  SECONDARY: "次要關聯",
  RELATED: "相關關聯",
  DIRECT: "直接關聯",
  INFERRED: "研究推論",
  SUPPORTS: "支持",
  INFLUENCES: "可能影響",
  LEADS_TO: "可能導向",
  SUPPORTED_APPLICATION: "支持的應用關聯",
  DIRECT_PRODUCT_TO_SEGMENT_CONTEXT: "產品至事業群直接對應",
  DIRECT_APPLICATION: "應用直接關聯",
  DIRECT_BUSINESS_GROUP_CONTEXT: "事業群直接對應",
  SUPPORTED_OPERATING_MECHANISM: "支持的營運機制",
  INFERRED_TO_FINANCIAL_IMPACT: "可能影響財務",
  RESEARCH_SCOPE_ONLY: "研究範圍限定",
  DIRECT_MANAGEMENT_PLAN: "管理層計畫直接揭露",
  RESEARCH_INFERENCE_NOT_FINANCIAL_FACT: "研究推論，非財務事實",
};

const NODE_TYPE_LABELS: Record<string, string> = {
  MATERIAL_OR_INPUT: "原料／投入",
  PRODUCT_OR_RELATION: "產品／公司關聯",
  OPERATING_INDICATOR: "營運指標",
  FINANCIAL_IMPACT: "財務影響",
  APPLICATION_OR_MARKET: "應用／市場",
  BUSINESS_GROUP_OR_FINANCIAL: "事業群／財務",
  ASSET_OR_PROJECT: "資產／專案",
  PRICE_OR_COST: "價格／成本",
};

const PARTICIPATION_LABELS: Record<string, string> = {
  CONFIRMED: "公司參與已確認",
  NOT_CONFIRMED: "公司參與尚未確認",
  INFERRED: "公司參與為研究推論",
  CONFIRMED_PRODUCT_AND_SEGMENT_RELATION: "產品與事業群關聯已確認",
  CONFIRMED_PRODUCT_CAPACITY_AND_SEGMENT_RELATION: "產品、產能與事業群關聯已確認",
  CONFIRMED_ASSET_AND_STRATEGY_REFERENCE: "資產與策略關聯已確認",
  CONFIRMED_PRODUCT_RELATION_WITH_PARTIAL_OPERATING_EVIDENCE: "產品關聯已確認，營運證據部分完整",
  CONFIRMED_PRODUCT_RELATION_WITH_UNQUANTIFIED_CONTRIBUTION: "產品關聯已確認，貢獻尚未量化",
  FORMAL_RELATION_WITH_INSUFFICIENT_CURRENT_EVIDENCE: "正式關聯，現有證據不足",
  FORMAL_RELATION_WITH_ASSET_ACTIVATION_EVIDENCE: "正式關聯，具資產活化證據",
  FORMAL_RELATION_WITH_PRODUCT_DEVELOPMENT_EVIDENCE: "正式關聯，具產品開發證據",
  FORMAL_RELATION_WITH_SMART_VEHICLE_PRODUCT_EVIDENCE: "正式關聯，具智慧車用產品證據",
  ASSET_RELATION_CONFIRMED: "資產關聯已確認",
};

const EVIDENCE_TYPE_LABELS: Record<string, string> = {
  OFFICIAL_ANNUAL_REPORT: "公司年報",
  OFFICIAL_Q1_FINANCIAL_REPORT: "第一季財報",
  OFFICIAL_Q2_FINANCIAL_REPORT: "第二季財報",
  OFFICIAL_Q3_FINANCIAL_REPORT: "第三季財報",
  OFFICIAL_Q4_FINANCIAL_REPORT: "第四季財報",
  OFFICIAL_IR_CONFERENCE: "法說會資料",
  OFFICIAL_ANNOUNCEMENT: "公司公告",
  OFFICIAL_PRODUCT_PAGE: "公司產品資料",
};

const UNIT_LABELS: Record<string, string> = {
  TWD: "元",
  TWD_1000: "千元",
  TWD_100_MILLION: "億元",
  USD: "美元",
  USD_MILLION: "百萬美元",
  PERCENT: "%",
};

const SCOPE_LABELS: Record<TopicStoryFinancialImpact["scope"], string> = {
  company: "公司層級",
  segment: "事業群層級",
  product: "產品層級",
  topic: "題材相關參考",
};

const CODE_TOKEN_LABELS: Record<string, string> = {
  CONFIRMED: "已確認",
  NOT: "尚未",
  PRODUCT: "產品",
  PRODUCTS: "產品",
  RELATION: "關聯",
  RELATIONS: "關聯",
  WITH: "，",
  AND: "與",
  PARTIAL: "部分",
  OPERATING: "營運",
  EVIDENCE: "證據",
  UNQUANTIFIED: "尚未量化",
  CONTRIBUTION: "貢獻",
  CAPACITY: "產能",
  SEGMENT: "事業群",
  APPLICATION: "應用",
  SUPPORTED: "支持",
  TO: "至",
  CONTEXT: "對應",
  BUSINESS: "事業群",
  GROUP: "群組",
  DIRECT: "直接",
  INFERRED: "研究推論",
  IMPACT: "影響",
  FINANCIAL: "財務",
  MECHANISM: "機制",
  ASSET: "資產",
  MANAGEMENT: "管理層",
  PLAN: "計畫",
  RESEARCH: "研究",
  SCOPE: "範圍",
  ONLY: "限定",
  FORMAL: "正式",
  INSUFFICIENT: "不足",
  CURRENT: "目前",
  ACTIVATION: "活化",
  NOT_FINANCIAL_FACT: "非財務事實",
  REPRESENTATIVE: "代表性",
};

type FocusKind = "story" | "node" | "edge" | "evidence";

function labelFor(map: Record<string, string>, value: string | null | undefined): string {
  if (!value) return "未揭露";
  const normalized = value.toUpperCase();
  if (map[value]) return map[value];
  if (map[normalized]) return map[normalized];
  return normalized.split("_").map((token) => CODE_TOKEN_LABELS[token] ?? token.toLowerCase()).join("／");
}

function formatAmount(value: number | null, unit: string | null): string {
  if (value === null || value === undefined) return "尚未揭露";
  return `${value.toLocaleString("zh-TW", { maximumFractionDigits: 2 })} ${UNIT_LABELS[unit ?? ""] ?? unit ?? ""}`.trim();
}

function formatPeriod(period: string | null): string {
  if (!period) return "期間未揭露";
  return period
    .replace("-H1", " 上半年")
    .replace("-H2", " 下半年")
    .replace("-Q1", " 第一季")
    .replace("-Q2", " 第二季")
    .replace("-Q3", " 第三季")
    .replace("-Q4", " 第四季");
}

function safePublicUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? parsed.toString() : null;
  } catch {
    return null;
  }
}

function EvidenceStatusBadge({ status }: { status: EvidenceStatus }) {
  return <span className={`tp-topic-story-status tp-topic-story-status--${status.toLowerCase()}`}>{STATUS_LABELS[status]}</span>;
}

function TopicStorySelector({ collection, selectedTopicId, onSelect }: { collection: TopicStoryCollection; selectedTopicId: string; onSelect: (topicId: string) => void }) {
  return <div className="tp-topic-story-selector" role="tablist" aria-label="正式題材故事選擇">
    {collection.stories.map((story) => <button key={story.topicId} type="button" role="tab" aria-selected={story.topicId === selectedTopicId} className={story.topicId === selectedTopicId ? "is-active" : ""} onClick={() => onSelect(story.topicId)}>
      <strong>{story.canonicalTopicName}</strong>
      <span>{labelFor(ROLE_LABELS, story.structuralRoleReference.structuralRole)} · {labelFor(RELATION_LABELS, story.formalAssociationReference.relationType)}</span>
      <small>{labelFor(PARTICIPATION_LABELS, story.companyParticipationSummary)}</small>
    </button>)}
  </div>;
}

function TopicStoryHeader({ story }: { story: TopicStoryView }) {
  return <header className="tp-topic-story-header">
    <div>
      <p className="tp-overline">正式題材研究故事</p>
      <h2>{story.storyTitle}</h2>
      <p>{story.storySummary}</p>
    </div>
    <div className="tp-topic-story-header-meta">
      <span className="tp-topic-story-pattern">{PATTERN_LABELS[story.storyPattern]}</span>
      <span>{labelFor(ROLE_LABELS, story.structuralRoleReference.structuralRole)} · {labelFor(RELATION_LABELS, story.formalAssociationReference.relationType)}</span>
      <span>{labelFor({ READY: "研究完成", READY_WITH_LIMITATIONS: "研究完成，仍有資料限制", PARTIAL_READY: "研究資料尚不完整", NOT_READY: "研究尚未完成" }, story.researchStatus)}</span>
      <span>研究截至 {story.researchAsOfDate}</span>
    </div>
  </header>;
}

function NodeButton({ node, active, onClick }: { node: TopicStoryNode; active: boolean; onClick: () => void }) {
  return <button type="button" data-node-id={node.nodeId} className={`tp-topic-story-node ${active ? "is-active" : ""}`} aria-pressed={active} aria-label={`選取節點：${node.label}`} onClick={onClick}>
    <span className="tp-topic-story-node-type">{labelFor(NODE_TYPE_LABELS, node.nodeType)}</span>
    <strong>{node.label}</strong>
    <span className="tp-topic-story-node-description">{node.description}</span>
    <span className="tp-topic-story-node-participation">{labelFor(PARTICIPATION_LABELS, node.companyParticipation)}</span>
    <span className="tp-topic-story-node-footer"><EvidenceStatusBadge status={node.evidenceStatus} /><small>{node.evidenceRefs.length ? `${node.evidenceRefs.length} 筆支持資料` : "尚無對應引用"}</small></span>
  </button>;
}

function EdgeButton({ edge, sourceLabel, targetLabel, active, onClick }: { edge: TopicStoryEdge; sourceLabel: string; targetLabel: string; active: boolean; onClick: () => void }) {
  return <button type="button" data-edge-id={edge.edgeId} className={`tp-topic-story-edge ${active ? "is-active" : ""}`} aria-pressed={active} aria-label={`選取關係：${sourceLabel} 到 ${targetLabel}`} onClick={onClick}>
    <span className="tp-topic-story-edge-flow"><strong>{sourceLabel}</strong><span aria-hidden="true">→</span><strong>{targetLabel}</strong></span>
    <span className="tp-topic-story-edge-meta"><span>{labelFor(RELATION_LABELS, edge.relationType)}</span><EvidenceStatusBadge status={edge.evidenceStatus} /><small>{edge.evidenceRefs.length ? `${edge.evidenceRefs.length} 筆支持資料` : "尚無對應引用"}</small></span>
    <span className="tp-topic-story-edge-description">{edge.relationDescription && edge.relationDescription !== edge.relationType ? edge.relationDescription : STATUS_HELP[edge.evidenceStatus]}</span>
  </button>;
}

function StoryFlow({ story, selectedNodeId, selectedEdgeId, onNode, onEdge }: { story: TopicStoryView; selectedNodeId: string | null; selectedEdgeId: string | null; onNode: (nodeId: string) => void; onEdge: (edgeId: string) => void }) {
  const nodeLabels = new Map(story.nodes.map((node) => [node.nodeId, node.label]));
  return <div className="tp-topic-story-visual tp-topic-story-visual--story-flow">
    <div className="tp-topic-story-flow-intro"><span>公司如何參與</span><strong>{labelFor(PARTICIPATION_LABELS, story.companyParticipationSummary)}</strong><p>{story.storySummary}</p></div>
    <div className="tp-topic-story-legend" aria-label="研究故事圖例"><span><i className="is-fact" />已確認事實</span><span><i className="is-inference" />研究推論</span><span>點擊節點或關係查看各自證據</span></div>
    <div className="tp-topic-story-graph" aria-label="題材研究故事圖">
      <div className="tp-topic-story-graph-heading"><h3>研究節點</h3><span>{story.nodes.length} 個節點</span></div>
      <div className="tp-topic-story-flow-nodes">
        {story.nodes.map((node) => <NodeButton key={node.nodeId} node={node} active={node.nodeId === selectedNodeId} onClick={() => onNode(node.nodeId)} />)}
      </div>
      <div className="tp-topic-story-graph-heading tp-topic-story-graph-heading--edges"><h3>關係與方向</h3><span>{story.edges.length} 條</span></div>
      {story.edges.length ? <div className="tp-topic-story-edge-list">
        {story.edges.map((edge) => <EdgeButton key={edge.edgeId} edge={edge} sourceLabel={nodeLabels.get(edge.sourceNodeId) ?? "未對應起點"} targetLabel={nodeLabels.get(edge.targetNodeId) ?? "未對應終點"} active={edge.edgeId === selectedEdgeId} onClick={() => onEdge(edge.edgeId)} />)}
      </div> : <div className="tp-topic-story-no-edge"><strong>目前沒有可安全繪製的關係線</strong><span>研究資料仍可閱讀，但不能由節點排列自行推導關係。</span></div>}
    </div>
    <p className="tp-topic-story-visual-note">關係方向只代表研究包明確提供的 source／target 與語義；不自動等同供貨、交易或獲利因果。</p>
  </div>;
}

function TimelineStory({ story, selectedEvidenceIds, onEvidence }: { story: TopicStoryView; selectedEvidenceIds: string[]; onEvidence: (ids: string[]) => void }) {
  return <div className="tp-topic-story-visual tp-topic-story-visual--timeline">
    <div className="tp-topic-story-flow-intro"><span>公司如何參與</span><strong>{labelFor(PARTICIPATION_LABELS, story.companyParticipationSummary)}</strong><p>{story.storySummary}</p></div>
    <div className="tp-topic-story-legend"><span>已公開事件與管理層計畫分開閱讀</span></div>
    <ol className="tp-topic-story-timeline">
      {story.timeline.map((event) => <li key={event.eventId} className={event.evidenceRefs.some((id) => selectedEvidenceIds.includes(id)) ? "is-active" : ""}>
        <button type="button" onClick={() => onEvidence(event.evidenceRefs)}>
          <span>{event.eventDate ?? "日期未揭露"} · {labelFor({ PUBLIC_EVENT: "公開事件", MANAGEMENT_PLAN: "管理層計畫", ANNOUNCEMENT: "公司公告" }, event.eventType)}</span>
          <strong>{event.eventTitle}</strong>
          <small>{labelFor({ CONFIRMED: "已確認", PLANNED: "計畫中", UNVERIFIED: "待驗證", DISCLOSED: "已揭露" }, event.milestoneStatus)}</small>
        </button>
      </li>)}
    </ol>
    {!story.timeline.length && <div className="tp-topic-story-empty">目前沒有可核對的公開事件時間軸，保留研究限制。</div>}
    <p className="tp-topic-story-visual-note">管理層計畫與已公開事件分開標示；尚未驗證的專案進度不會被畫成已完成。</p>
  </div>;
}

function EvidenceGapStory({ story, onEvidence }: { story: TopicStoryView; onEvidence: (ids: string[]) => void }) {
  const direct = story.evidence.filter((item) => item.evidenceStatus === "FACT");
  return <div className="tp-topic-story-visual tp-topic-story-visual--gap">
    <div className="tp-topic-story-flow-intro"><span>公司如何參與</span><strong>{labelFor(PARTICIPATION_LABELS, story.companyParticipationSummary)}</strong><p>{story.storySummary}</p></div>
    <div className="tp-topic-story-gap-card is-formal"><span>正式題材關聯</span><strong>{story.canonicalTopicName}</strong><small>{labelFor(ROLE_LABELS, story.structuralRoleReference.structuralRole)} · {labelFor(RELATION_LABELS, story.formalAssociationReference.relationType)}</small></div>
    <div className="tp-topic-story-gap-connector" aria-hidden="true">↓</div>
    <div className="tp-topic-story-gap-card is-missing"><ShieldAlert size={18} aria-hidden="true" /><span>目前證據邊界</span><strong>尚未取得足以確認的題材專案收入或獲利</strong><small>證據缺口不代表正式關聯不存在。</small></div>
    <div className="tp-topic-story-gap-evidence"><strong>目前可確認的資料</strong>{direct.slice(0, 3).map((item) => <button type="button" key={item.evidenceId} onClick={() => onEvidence([item.evidenceId])}>{item.title}</button>)}{!direct.length && <span>目前沒有可展示的獨立引用。</span>}</div>
  </div>;
}

function TopicStoryRenderer({ story, selectedNodeId, selectedEdgeId, selectedEvidenceIds, onNode, onEdge, onEvidence }: { story: TopicStoryView; selectedNodeId: string | null; selectedEdgeId: string | null; selectedEvidenceIds: string[]; onNode: (nodeId: string) => void; onEdge: (edgeId: string) => void; onEvidence: (ids: string[]) => void }) {
  if (story.storyPattern === "ASSET_PROJECT_TIMELINE") return <TimelineStory story={story} selectedEvidenceIds={selectedEvidenceIds} onEvidence={onEvidence} />;
  if (story.storyPattern === "EVIDENCE_GAP") return <EvidenceGapStory story={story} onEvidence={onEvidence} />;
  return <StoryFlow story={story} selectedNodeId={selectedNodeId} selectedEdgeId={selectedEdgeId} onNode={onNode} onEdge={onEdge} />;
}

function selectionEmptyMessage(kind: FocusKind, node: TopicStoryNode | undefined, edge: TopicStoryEdge | undefined): { title: string; body: string } {
  if (kind === "story") return { title: "先從故事節點開始閱讀", body: "本故事目前沒有指定預設焦點；左側的故事摘要與研究限制仍然有效。" };
  if (kind === "edge" && edge?.evidenceStatus === "INFERENCE") return { title: "目前沒有支持此推論的可展示引用", body: "這條關係保留為研究推論，不會因為兩端節點已確認就升格為事實。" };
  if (node?.evidenceStatus === "UNDISCLOSED" || edge?.evidenceStatus === "UNDISCLOSED") return { title: "資料缺漏，尚未取得公開揭露", body: "研究包保留這個資料邊界，不補造文件、數字或來源。" };
  if (node?.evidenceStatus === "INFERENCE" || edge?.evidenceStatus === "INFERENCE") return { title: "研究判斷尚未映射獨立引用", body: "目前只保留研究判斷與限制，不能把它當成已確認事實。" };
  return { title: "目前選取項目沒有獨立可展示引用", body: "可先查看故事摘要、其他節點或關係；此處不會生成不存在的來源。" };
}

function EvidencePanel({ story, evidenceIds, focusKind, selectedNode, selectedEdge, onToggle }: { story: TopicStoryView; evidenceIds: string[]; focusKind: FocusKind; selectedNode?: TopicStoryNode; selectedEdge?: TopicStoryEdge; onToggle: (id: string) => void }) {
  const evidence = getTopicStoryEvidence(story, evidenceIds);
  const sourceNode = selectedEdge ? story.nodes.find((node) => node.nodeId === selectedEdge.sourceNodeId) : undefined;
  const targetNode = selectedEdge ? story.nodes.find((node) => node.nodeId === selectedEdge.targetNodeId) : undefined;
  const emptyMessage = selectionEmptyMessage(focusKind, selectedNode, selectedEdge);
  const focusTitle = selectedNode?.label ?? (selectedEdge ? `${sourceNode?.label ?? "未對應起點"} → ${targetNode?.label ?? "未對應終點"}` : focusKind === "evidence" ? "選取的公開資料" : "故事摘要");
  return <aside className="tp-topic-story-evidence-panel" aria-label="題材研究證據">
    <div className="tp-topic-story-panel-heading"><div><p className="tp-overline">研究證據</p><h3>{focusTitle}</h3></div><span>{evidence.length ? `${evidence.length} 筆` : "尚未選取可展示來源"}</span></div>
    {selectedNode && <div className="tp-topic-story-focus-summary"><span>{labelFor(NODE_TYPE_LABELS, selectedNode.nodeType)} · {STATUS_LABELS[selectedNode.evidenceStatus]}</span><strong>{selectedNode.description}</strong><p>{STATUS_HELP[selectedNode.evidenceStatus]}</p></div>}
    {selectedEdge && <div className="tp-topic-story-focus-summary"><span>{sourceNode?.label ?? "未對應起點"} → {targetNode?.label ?? "未對應終點"}</span><strong>{labelFor(RELATION_LABELS, selectedEdge.relationType)}</strong><p>{selectedEdge.relationDescription && selectedEdge.relationDescription !== selectedEdge.relationType ? selectedEdge.relationDescription : STATUS_HELP[selectedEdge.evidenceStatus]}</p></div>}
    {evidence.length ? <div className="tp-topic-story-evidence-list">{evidence.map((item) => {
      const sourceUrl = safePublicUrl(item.sourceUrl);
      return <details key={item.evidenceId} open={evidence.length === 1}>
        <summary><span>{item.title}</span><EvidenceStatusBadge status={item.evidenceStatus} /></summary>
        <div className="tp-topic-story-evidence-body"><p>{item.claim}</p><dl><div><dt>資料日期</dt><dd>{item.sourceDate ?? "未揭露"}</dd></div><div><dt>資料類型</dt><dd>{labelFor(EVIDENCE_TYPE_LABELS, item.evidenceType)}</dd></div><div><dt>發布單位</dt><dd>{item.documentLocator}</dd></div><div><dt>研究限制</dt><dd>{item.limitations || "目前沒有補充限制。"}</dd></div></dl>{sourceUrl ? <a href={sourceUrl} target="_blank" rel="noreferrer">查看官方來源 <ExternalLink size={13} aria-hidden="true" /></a> : <span className="tp-topic-story-muted">目前只有文件定位，沒有可直接開啟的公開連結。</span>}<button type="button" className="tp-topic-story-evidence-clear" onClick={() => onToggle(item.evidenceId)}>收起此證據</button></div>
      </details>;
    })}</div> : <div className="tp-topic-story-evidence-empty"><strong>{emptyMessage.title}</strong><span>{emptyMessage.body}</span></div>}
  </aside>;
}

function financialTitle(item: TopicStoryFinancialImpact): string {
  if (item.scope === "topic") return "題材相關參考";
  if (item.scope === "segment") return `${item.metricName}參考`;
  if (item.metricName.includes("題材可對應")) return "相關產品收入參考";
  return item.metricName;
}

function FinancialEvidence({ story }: { story: TopicStoryView }) {
  if (!story.financialImpact.length) return <section className="tp-topic-story-support-card"><div className="tp-topic-story-support-heading"><h3>營運與財務影響</h3><span>資料待補</span></div><p>目前沒有可安全展示的財務參考；不由研究故事自行推算題材收入或獲利。</p></section>;
  const evidenceById = new Map(story.evidence.map((item) => [item.evidenceId, item]));
  return <section className="tp-topic-story-support-card"><div className="tp-topic-story-support-heading"><h3>營運與財務影響</h3><span>依資料層級閱讀</span></div><div className="tp-topic-story-financial-grid">{story.financialImpact.map((item) => {
    const source = item.sourceRef ? evidenceById.get(item.sourceRef) : undefined;
    const sourceUrl = safePublicUrl(source?.sourceUrl);
    return <article key={`${item.metricName}-${item.period}`}><span>{financialTitle(item)}</span><strong>{formatAmount(item.metricValue, item.unit)}</strong><small>{formatPeriod(item.period)} · {SCOPE_LABELS[item.scope]}</small><p>{item.attributionLimitations}</p>{source && <div className="tp-topic-story-financial-source">來源：{source.title}{sourceUrl && <a href={sourceUrl} target="_blank" rel="noreferrer">官方來源 <ExternalLink size={12} aria-hidden="true" /></a>}</div>}<details className="tp-topic-story-raw-details"><summary>查看資料範圍</summary><span>原始數值：{item.metricValue ?? "null"} · 原始單位：{item.unit ?? "null"} · 期間：{item.period ?? "null"} · 層級：{item.scope}</span></details></article>;
  })}</div></section>;
}

function WatchIndicators({ story }: { story: TopicStoryView }) {
  return <section className="tp-topic-story-support-card"><div className="tp-topic-story-support-heading"><h3>後續觀察重點</h3><span>{story.watchIndicators.length} 項</span></div>{story.watchIndicators.length ? <ul className="tp-topic-story-watch-list">{story.watchIndicators.map((item) => <li key={item}>{item}</li>)}</ul> : <p>目前沒有額外的後續觀察項目。</p>}</section>;
}

function ResearchLimitations({ story }: { story: TopicStoryView }) {
  return <section className="tp-topic-story-support-card tp-topic-story-limitations"><div className="tp-topic-story-support-heading"><h3>研究限制與資料缺口</h3><span>{story.limitations.length} 項</span></div>{story.limitations.length ? <ul>{story.limitations.map((item) => <li key={item}>{item}</li>)}</ul> : <p>目前沒有額外限制。</p>}</section>;
}

function EmergingResearchObservations({ story }: { story: TopicStoryView }) {
  return <section className="tp-topic-story-support-card tp-topic-story-observations"><div className="tp-topic-story-support-heading"><h3>其他研究觀察</h3><span>不等同正式題材</span></div><p>{story.researchStatus === "READY_WITH_LIMITATIONS" ? "本區只保留研究觀察與資料邊界，不會把尚未核准的概念升格為正式題材。" : "本故事目前沒有額外的非正式研究觀察。"}</p></section>;
}

function defaultNodeFor(story: TopicStoryView | undefined): TopicStoryNode | undefined {
  return story?.nodes.find((node) => node.evidenceStatus === "FACT" && node.evidenceRefs.length > 0) ?? story?.nodes[0];
}

export function StockTopicEvidenceStory({ collection }: { collection: TopicStoryCollection }) {
  const titleRef = useRef<HTMLDivElement | null>(null);
  const initialStory = collection.stories[0];
  const initialNode = defaultNodeFor(initialStory);
  const [selectedTopicId, setSelectedTopicId] = useState(initialStory?.topicId ?? "");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(initialNode?.nodeId ?? null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<string[]>(initialNode?.evidenceRefs ?? []);
  const [focusKind, setFocusKind] = useState<FocusKind>(initialNode ? "node" : "story");
  const story = useMemo(() => collection.stories.find((item) => item.topicId === selectedTopicId) ?? collection.stories[0] ?? null, [collection.stories, selectedTopicId]);

  const selectTopic = (topicId: string) => {
    const nextStory = collection.stories.find((item) => item.topicId === topicId) ?? collection.stories[0];
    const nextNode = defaultNodeFor(nextStory);
    setSelectedTopicId(topicId);
    setSelectedNodeId(nextNode?.nodeId ?? null);
    setSelectedEdgeId(null);
    setSelectedEvidenceIds(nextNode?.evidenceRefs ?? []);
    setFocusKind(nextNode ? "node" : "story");
    requestAnimationFrame(() => titleRef.current?.scrollIntoView({ block: "start", behavior: "smooth" }));
  };

  if (!story) return <div className="tp-topic-story-unavailable">目前沒有可呈現的正式題材研究故事。</div>;
  const toggleEvidence = (ids: string[]) => {
    setFocusKind("evidence");
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
    setSelectedEvidenceIds((current) => current.length === ids.length && current.every((id) => ids.includes(id)) ? [] : ids);
  };
  const selectNode = (nodeId: string) => {
    const node = story.nodes.find((item) => item.nodeId === nodeId);
    setFocusKind("node");
    setSelectedNodeId(nodeId);
    setSelectedEdgeId(null);
    setSelectedEvidenceIds(node?.evidenceRefs ?? []);
  };
  const selectEdge = (edgeId: string) => {
    const edge = story.edges.find((item) => item.edgeId === edgeId);
    setFocusKind("edge");
    setSelectedEdgeId(edgeId);
    setSelectedNodeId(null);
    setSelectedEvidenceIds(edge?.evidenceRefs ?? []);
  };
  const selectedNode = selectedNodeId ? story.nodes.find((node) => node.nodeId === selectedNodeId) : undefined;
  const selectedEdge = selectedEdgeId ? story.edges.find((edge) => edge.edgeId === selectedEdgeId) : undefined;

  return <section className="tp-topic-story-section" aria-label="正式題材證據故事">
    <div className="tp-topic-story-boundary-note"><strong>正式題材研究故事</strong><span>題材清單沿用現行正式權威；本頁只呈現研究證據與限制，不會修改正式題材關聯。</span></div>
    <TopicStorySelector collection={collection} selectedTopicId={story.topicId} onSelect={selectTopic} />
    <div ref={titleRef} className="tp-topic-story-reading-anchor"><TopicStoryHeader story={story} /></div>
    <div className="tp-topic-story-main-grid">
      <TopicStoryRenderer story={story} selectedNodeId={selectedNodeId} selectedEdgeId={selectedEdgeId} selectedEvidenceIds={selectedEvidenceIds} onNode={selectNode} onEdge={selectEdge} onEvidence={toggleEvidence} />
      <EvidencePanel story={story} evidenceIds={selectedEvidenceIds} focusKind={focusKind} selectedNode={selectedNode} selectedEdge={selectedEdge} onToggle={(id) => setSelectedEvidenceIds((current) => current.filter((value) => value !== id))} />
    </div>
    <div className="tp-topic-story-support-grid"><FinancialEvidence story={story} /><WatchIndicators story={story} /><ResearchLimitations story={story} /><EmergingResearchObservations story={story} /></div>
  </section>;
}
