"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppShell, Card, EmptyState, FavoriteStar, PageContainer, RoleChip } from "./V2Foundation";
import { fetchFormalStock, fetchFormalStockTechnical, listingLabel, marketLabel, topicRoleLabel, type StockApiItem, type StockTechnicalPublicationRead } from "../../lib/stock-api";
import { useFavoritesState } from "../FavoriteButton";
import { useSnapshot } from "../../lib/snapshot-store";
import type { StockView } from "../../lib/types";
import { StockResearchCards } from "./StockResearchCards";
import { getPreviewStockResearch } from "../../lib/stock-research-preview";
import { fetchFinancialResearchReadout, type FinancialResearchReadout } from "../../lib/financial-research-api";
import { getPreviewStockTopicStories, getTopicStoryRelationPreview } from "../../lib/stock-topic-evidence-preview";
import { StockTopicEvidenceStory } from "./StockTopicEvidenceStory";
import { StockOverviewV1, type OverviewTopic } from "./StockOverviewV1";

type DetailTab = "overview" | "technical" | "chip" | "fundamental" | "topics";
type DetailResource = { code: string; source: "formal" | "preview" | "unavailable"; stock: StockApiItem | StockView | null; error: string | null };

const TABS: Array<{ id: DetailTab; label: string }> = [
  { id: "overview", label: "總覽" },
  { id: "technical", label: "技術分析" },
  { id: "chip", label: "籌碼面" },
  { id: "fundamental", label: "公司研究" },
  { id: "topics", label: "題材關聯" },
];

function formatMoney(value: number | null | undefined): string {
  return typeof value === "number" ? value.toLocaleString("zh-TW", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—";
}

function formatPercent(value: number | null | undefined): string {
  return typeof value === "number" ? `${value >= 0 ? "+" : ""}${value.toFixed(2)}%` : "—";
}

function initials(name: string, code: string): string {
  const compact = name.replace(/\s+/g, "");
  return (compact.slice(0, 2) || code.slice(0, 2)).toUpperCase();
}

function isFormal(stock: DetailResource["stock"]): stock is StockApiItem {
  return Boolean(stock && "eod" in stock);
}

function isPreview(stock: DetailResource["stock"]): stock is StockView {
  return Boolean(stock && "relations" in stock);
}

function stateLabel(value: string | null | undefined): string {
  const labels: Record<string, string> = {
    FORMAL: "可用",
    FORMAL_WITH_LIMITATION: "可用 · 有限制",
    AVAILABLE_WITH_LIMITATION: "可用 · 有限制",
    UNAVAILABLE: "尚未提供",
    CONTINUITY_FAIL: "資料連續性異常",
    CONTINUITY_UNKNOWN: "狀態未知",
    INSUFFICIENT_HISTORY: "歷史資料不足",
    DEFERRED: "暫不提供",
  };
  return value ? labels[value] ?? "狀態待補" : "狀態待補";
}

function Unavailable({ title, description }: { title: string; description: string }) {
  return <div className="tp-stock-unavailable" data-state="unavailable"><strong>{title}</strong><p>{description}</p></div>;
}

function EvidenceGrid({ rows }: { rows: Array<[string, string]> }) {
  return <dl className="tp-stock-detail-evidence">{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>;
}

function TechnicalGroups({ publication }: { publication: StockTechnicalPublicationRead | null }) {
  if (!publication || publication.publicationStatus === "UNAVAILABLE" || publication.status === "UNAVAILABLE") {
    return <Unavailable title="技術資料尚未提供" description="目前沒有可顯示的技術資料。" />;
  }
  const groups = new Map<string, typeof publication.technicalEvidence>();
  publication.technicalEvidence.forEach((evidence) => {
    const family = evidence.indicatorFamily || "OTHER";
    groups.set(family, [...(groups.get(family) ?? []), evidence]);
  });
  const labels: Record<string, string> = { TREND: "趨勢", MOMENTUM: "動能", VOLUME: "量能", OTHER: "其他指標" };
  return <div className="tp-stock-technical-groups">
    {Array.from(groups.entries()).map(([family, evidence]) => <section className="tp-stock-detail-section" key={family}>
      <div className="tp-stock-section-heading"><h3>{labels[family] ?? "技術指標"}</h3><span>{evidence.length} 項</span></div>
      <div className="tp-stock-technical-list">{evidence.map((item) => <div key={`${item.indicatorId}-${item.sessionDate}`}><span>{item.indicatorId}</span><strong>{item.value ?? "—"}</strong><small>{item.asOf ?? item.sessionDate} · {stateLabel(item.publicationState)}</small></div>)}</div>
    </section>)}
    <section className="tp-stock-detail-section tp-stock-detail-section--muted"><div className="tp-stock-section-heading"><h3>資料狀態</h3><span>{stateLabel(publication.publicationState)}</span></div><EvidenceGrid rows={[["資料日期", publication.asOf ?? "—"], ["資料範圍", `${publication.requestedFrom} → ${publication.requestedTo}`], ["指標數", String(publication.publishedIndicators.length)], ["限制", publication.limitationReasons.join("；") || "—"]]} /></section>
  </div>;
}

export default function StockDetailPage({ code }: { code: string }) {
  const { bundle } = useSnapshot();
  const { isFavorite, toggle: toggleFavorite } = useFavoritesState();
  const [resource, setResource] = useState<DetailResource | null>(null);
  const [technical, setTechnical] = useState<StockTechnicalPublicationRead | null>(null);
  const [technicalError, setTechnicalError] = useState<string | null>(null);
  const [technicalCode, setTechnicalCode] = useState<string | null>(null);
  const [financialReadout, setFinancialReadout] = useState<FinancialResearchReadout | null>(null);
  const [tab, setTab] = useState<DetailTab>(() => {
    if (typeof window === "undefined") return "overview";
    const queryTab = new URLSearchParams(window.location.search).get("tab") as DetailTab | null;
    return queryTab && TABS.some((item) => item.id === queryTab) ? queryTab : "overview";
  });

  const previewStock = useMemo(() => bundle.stockUniverse.find((item) => item.code === code) ?? null, [bundle.stockUniverse, code]);

  useEffect(() => {
    let active = true;
    void fetchFormalStock(code).then((result) => {
      if (!active) return;
      if (result.source === "api" && result.data) {
        setResource({ code, source: "formal", stock: result.data, error: null });
        return;
      }
      if (result.source === "synthetic-snapshot" && previewStock) {
        setResource({ code, source: "preview", stock: previewStock, error: result.error });
      } else {
        setResource({ code, source: "unavailable", stock: null, error: result.error });
      }
    });
    return () => { active = false; };
  }, [code, previewStock]);

  const currentResource = resource?.code === code ? resource : null;
  const stock = currentResource?.stock ?? null;
  const formal = isFormal(stock) ? stock : null;
  const preview = isPreview(stock) ? stock : null;
  const topicStoryCollection = getPreviewStockTopicStories(code);
  const previewTopicRelations = getTopicStoryRelationPreview(topicStoryCollection);
  const displayedTopicRelations = topicStoryCollection ? previewTopicRelations : (formal?.topicRelations ?? []);
  const relationCount = displayedTopicRelations.length;
  const identityName = formal?.name ?? preview?.name ?? code;
  const isPreviewState = currentResource?.source === "preview";
  const researchBundle = getPreviewStockResearch(code);

  useEffect(() => {
    const controller = new AbortController();
    void fetchFinancialResearchReadout(code, { signal: controller.signal }).then((result) => {
      if (!controller.signal.aborted) setFinancialReadout(result);
    });
    return () => controller.abort();
  }, [code]);

  useEffect(() => {
    if (!formal) return;
    const controller = new AbortController();
    void fetchFormalStockTechnical(code, { market: formal.market, signal: controller.signal }).then((result) => {
      if (result.source === "api" && result.data) {
        setTechnical(result.data);
        setTechnicalError(null);
        setTechnicalCode(code);
      } else {
        setTechnicalError(result.error);
        setTechnicalCode(code);
      }
    });
    return () => controller.abort();
  }, [code, formal]);

  const selectTab = (next: DetailTab) => {
    setTab(next);
    const url = new URL(window.location.href);
    if (next === "overview") url.searchParams.delete("tab");
    else url.searchParams.set("tab", next);
    window.history.replaceState({}, "", url);
  };

  const eod = formal?.eod ?? null;
  const currentTechnical = technicalCode === code ? technical : null;
  const currentTechnicalError = technicalCode === code ? technicalError : null;
  const formalTopicRelations = displayedTopicRelations;
  const overviewTopicRelations = formal?.topicRelations ?? (isPreviewState ? (preview?.relations ?? []) : []);
  const overviewTopics: OverviewTopic[] = overviewTopicRelations.map((relation) => {
    if ("topicName" in relation) {
      return {
        name: relation.topicName,
        href: relation.topicSlug ? `/topics/${relation.topicSlug}` : null,
        role: relation.topicRole ? topicRoleLabel(relation.topicRole) : null,
        weight: relation.relationWeight,
      };
    }
    return { name: relation.topic, href: null, role: relation.role, weight: relation.weight };
  });

  if (currentResource === null) {
    return <AppShell currentPath="/stocks"><PageContainer title="股票圖鑑"><Card><EmptyState title="正在讀取個股資料" description="資料正在準備中，請稍候。" /></Card></PageContainer></AppShell>;
  }
  if (currentResource.source === "unavailable" || !stock) {
    return <AppShell currentPath="/stocks"><PageContainer title="股票圖鑑"><Card><EmptyState title="個股資料暫時無法載入" description="資料連線或內容驗證目前異常，請稍後再試。" /></Card></PageContainer></AppShell>;
  }

  const quotePrice = formal ? (eod?.close ?? formal.price) : null;
  const quoteChange = formal ? (eod?.changePct ?? formal.changePct) : null;
  const quoteDate = eod?.tradingDate ?? formal?.retrievedAt ?? null;
  const favorite = isFavorite(code, formal?.market ?? null);

  return <AppShell currentPath="/stocks">
    <PageContainer hideHeader title="股票圖鑑" className="tp-stock-detail-page">
      <Link className="tp-stock-detail-back" href="/stocks">← 股票圖鑑　/　{identityName} {code}</Link>
      <section className="tp-stock-detail-hero" data-preview={isPreviewState ? "true" : "false"} data-active-tab={tab}>
        <div className="tp-stock-detail-identity"><div className="tp-stock-company-mark" aria-label="公司標誌尚未提供">{initials(identityName, code)}</div><div><p className="tp-eyebrow">公司／股票</p><div className="tp-stock-detail-name-line"><h1>{identityName}</h1><span>{code}{listingLabel(formal?.listing) ?? marketLabel(formal?.market) ? ` · ${listingLabel(formal?.listing) ?? marketLabel(formal?.market)}` : ""}</span></div></div></div>
        <div className="tp-stock-detail-actions"><button type="button" className="tp-stock-share-button" onClick={() => { void navigator.clipboard?.writeText(window.location.href); }}>⌯　分享</button><div className="tp-stock-favorite-button"><FavoriteStar active={favorite} onClick={() => toggleFavorite(code, { market: formal?.market ?? null, displayLabel: identityName })} /> <span>{favorite ? "已加入自選" : "加入自選"}</span></div></div>
        <div className="tp-stock-detail-freshness"><span>最後更新：{researchBundle?.researchAsOf ?? "日期待補"}（研究）</span><i aria-hidden="true" /> <span>市場資料：{quoteDate ?? "日期待補"}</span></div>
        <div className="tp-stock-detail-quote"><strong>{formatMoney(quotePrice)}</strong><span className={quoteChange === null ? "tp-muted" : quoteChange >= 0 ? "tp-stock-up" : "tp-stock-down"}>{formatPercent(quoteChange)}</span><small>{isPreviewState ? "預覽資料" : `${quoteDate ?? "日期待補"} 收盤`}</small></div>
      </section>

      <nav className="tp-stock-detail-tabs" aria-label="個股分頁" role="tablist">{TABS.map((item) => <button key={item.id} type="button" role="tab" aria-selected={tab === item.id} className={tab === item.id ? "is-active" : ""} onClick={() => selectTab(item.id)}>{item.label}{item.id === "topics" && relationCount > 0 ? <small>{relationCount}</small> : null}</button>)}</nav>

      <div className="tp-stock-detail-content" data-active-tab={tab}>
        {tab === "overview" && <StockOverviewV1 symbol={code} formal={formal} preview={preview} technical={currentTechnical} topics={overviewTopics} onOpenTechnical={() => selectTab("technical")} onOpenTopics={() => selectTab("topics")} />}
        {tab === "technical" && <section className="tp-stock-detail-section"><div className="tp-stock-section-heading"><h2>技術分析</h2><span>{currentTechnicalError ? "資料暫時無法載入" : isPreviewState ? "資料待補" : "既有技術資料"}</span></div>{currentTechnical ? <TechnicalGroups publication={currentTechnical} /> : <Unavailable title={isPreviewState ? "預覽資料沒有技術判讀" : "技術資料尚未提供"} description={currentTechnicalError ? "技術資料目前無法載入，請稍後再試。" : "目前沒有可供此頁展示的技術資料。"} />}</section>}
        {tab === "chip" && <section className="tp-stock-detail-section"><div className="tp-stock-section-heading"><h2>籌碼面</h2><span>資料待補</span></div><Unavailable title="籌碼資料尚未提供" description="目前沒有可供此頁使用的正式籌碼資料。" /></section>}
        {tab === "fundamental" && <section className="tp-stock-research-tab" aria-label="公司研究"><StockResearchCards companyName={identityName} research={researchBundle} financialReadout={financialReadout} /></section>}
         {tab === "topics" && (topicStoryCollection ? <StockTopicEvidenceStory key={code} collection={topicStoryCollection} /> : <section className="tp-stock-detail-section"><div className="tp-stock-section-heading"><h2>題材關聯</h2><span>{relationCount} 個題材</span></div>{formalTopicRelations.length ? <div className="tp-stock-topic-list">{formalTopicRelations.map((relation) => <Link href={`/topics/${relation.topicSlug}`} key={`${relation.topicSlug}-${relation.relationType}`}><div><strong>{relation.topicName}</strong></div><RoleChip>{topicRoleLabel(relation.topicRole) ?? "關聯"}</RoleChip></Link>)}</div> : <Unavailable title="題材資料尚未提供" description="此頁只呈現已提供的正式關係，不替股票推導主要題材。" />}</section>)}
      </div>
    </PageContainer>
  </AppShell>;
}
