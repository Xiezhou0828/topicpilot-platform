"use client";

import Link from "next/link";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchFormalStock, type StockApiItem } from "../../lib/stock-api";
import { useFavoritesState } from "../FavoriteButton";
import { FavoriteStar, Freshness, RoleChip } from "./V2Foundation";

export type StockDrawerTopic = { name: string; role: string | null };

export type StockDrawerTechnicalEvidence = {
  above20MA: boolean | null;
  above60MA: boolean | null;
  ma20: number | null;
  ma60: number | null;
  breakoutState: string | null;
  technicalState: string | null;
};

export type StockDrawerItem = {
  code: string;
  name: string;
  market?: string | null;
  exchange?: string | null;
  listing?: string | null;
  industry?: string | null;
  price: number | null;
  changePct: number | null;
  dataFreshness: string | null;
  updatedAt?: string | null;
  dataDate?: string | null;
  topics: StockDrawerTopic[];
  mainTopic?: { name: string; grade?: string | null; state?: string | null; lifecycle?: string | null } | null;
  technicalEvidence?: StockDrawerTechnicalEvidence | null;
  institutionFlows?: Record<string, unknown> | null;
  summary?: string | null;
  opportunity?: Record<string, unknown> | null;
  isPreview?: boolean;
};

const label = (value: string | null) => {
  const v = (value ?? "").trim().toUpperCase();
  if (["代表股", "PRIMARY", "REPRESENTATIVE", "LEADER"].includes(v)) return "代表股";
  if (["核心股", "CORE", "SECONDARY"].includes(v)) return "核心股";
  if (["關聯股", "RELATED"].includes(v)) return "關聯股";
  return "尚未提供";
};

const fresh = (value: string | null): "盤中更新" | "盤後更新" | "資料待更新" => {
  const v = (value ?? "").toUpperCase();
  if (/CURRENT|LIVE|INTRADAY/.test(v)) return "盤中更新";
  if (/EOD|POST|AFTER/.test(v)) return "盤後更新";
  return "資料待更新";
};

function formalDrawerItem(base: StockDrawerItem, detail: StockApiItem): StockDrawerItem {
  const asOfDate = typeof detail.historyCoverage?.asOfDate === "string" ? detail.historyCoverage.asOfDate : null;
  return {
    ...base,
    code: detail.code,
    name: detail.name ?? detail.code,
    market: detail.market,
    exchange: detail.exchange,
    listing: detail.listing,
    price: detail.price,
    changePct: detail.changePct,
    dataFreshness: detail.dataFreshness,
    updatedAt: detail.retrievedAt,
    dataDate: asOfDate,
    topics: detail.topicRelations.map((topic) => ({ name: topic.topicName, role: topic.topicRole })),
    mainTopic: detail.mainTopic,
    technicalEvidence: detail.technicalEvidence,
    institutionFlows: detail.institutionFlows,
    summary: detail.summary,
    opportunity: detail.opportunity,
    isPreview: false,
  };
}

function displayValue(value: string | number | boolean | null | undefined): string {
  if (value === null || value === undefined || value === "") return "尚未提供";
  if (typeof value === "boolean") return value ? "是" : "否";
  if (typeof value === "number") return value.toLocaleString("zh-TW", { maximumFractionDigits: 2 });
  return value;
}

function EvidenceGrid({ rows }: { rows: Array<[string, string | number | boolean | null | undefined]> }) {
  return <dl className="tp-stock-encyclopedia-evidence-grid">{rows.map(([name, value]) => <div key={name}><dt>{name}</dt><dd>{displayValue(value)}</dd></div>)}</dl>;
}

export function StockEncyclopediaDrawer({ stock, onClose, presentation = "overlay", isClosing = false }: { stock: StockDrawerItem; onClose: () => void; presentation?: "overlay" | "inline" | "push"; isClosing?: boolean }) {
  const { codes: favoriteCodes, toggle: toggleFavorite } = useFavoritesState();
  const [formalDetailState, setFormalDetailState] = useState<{ symbol: string; data: StockApiItem | null; status: "available" | "unavailable"; error: string | null } | null>(null);

  useEffect(() => {
    let active = true;
    if (stock.isPreview === true) {
      return () => { active = false; };
    }
    fetchFormalStock(stock.code).then((result) => {
      if (!active) return;
      if (result.source === "api" && result.data) {
        setFormalDetailState({ symbol: stock.code, data: result.data, status: "available", error: null });
      } else {
        setFormalDetailState({ symbol: stock.code, data: null, status: "unavailable", error: result.error });
      }
    });
    return () => { active = false; };
  }, [stock.code, stock.isPreview]);

  const formalDetail = formalDetailState?.symbol === stock.code ? formalDetailState.data : null;
  const detailState = stock.isPreview === true ? "idle" : formalDetailState?.symbol === stock.code ? formalDetailState.status : "loading";
  const detailError = formalDetailState?.symbol === stock.code ? formalDetailState.error : null;
  const displayStock = formalDetail ? formalDrawerItem(stock, formalDetail) : stock;
  const tone = displayStock.changePct === null ? "flat" : displayStock.changePct >= 0 ? "up" : "down";
  const technical = displayStock.technicalEvidence;
  const institutionEntries = Object.entries(displayStock.institutionFlows ?? {}).filter(([, value]) => value !== null && value !== undefined);
  const presentationClass = presentation === "inline"
    ? "tp-stock-encyclopedia-drawer--inline"
    : presentation === "push"
      ? `tp-stock-encyclopedia-drawer--push${isClosing ? " is-closing" : ""}`
      : "";
  const drawer = <aside className={`tp-stock-encyclopedia-drawer ${presentationClass}`} role="dialog" aria-modal={presentation === "overlay" ? true : undefined} aria-labelledby="stock-encyclopedia-title" onClick={(event) => event.stopPropagation()}>
    <header className="tp-stock-encyclopedia-header">
      <div>
        <p className="tp-eyebrow">股票圖鑑</p>
        <h2 id="stock-encyclopedia-title">{displayStock.name}</h2>
        <span>{displayStock.code}{displayStock.market ? ` · ${displayStock.market}` : ""}{displayStock.exchange ? ` · ${displayStock.exchange}` : ""}</span>
      </div>
      <div className="tp-stock-encyclopedia-actions"><FavoriteStar active={favoriteCodes.includes(displayStock.code)} onClick={() => toggleFavorite(displayStock.code)} /><button type="button" className="tp-stock-close" aria-label="Close stock drawer" title="Close" onClick={onClose}><X size={18} aria-hidden="true" /></button></div>
    </header>
    <div className="tp-stock-encyclopedia-body">
      <div className="tp-stock-encyclopedia-freshness"><Freshness state={fresh(displayStock.dataFreshness)} asOf={displayStock.updatedAt ?? displayStock.dataDate ?? "資料日期待補"} />{displayStock.isPreview && <span className="tp-stock-preview-label">Preview</span>}{detailState === "loading" && <span className="tp-muted">正在讀取正式 detail</span>}{detailState === "unavailable" && !displayStock.isPreview && <span className="tp-muted">正式 detail 暫不可用</span>}</div>
      {detailError && !displayStock.isPreview && <p className="tp-stock-encyclopedia-muted">{detailError}</p>}
      <div className="tp-stock-encyclopedia-price"><strong>{displayStock.price === null ? "—" : displayStock.price.toLocaleString("zh-TW", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>{displayStock.changePct === null ? <span className="tp-muted">漲跌資料待更新</span> : <span className={`tp-topic-change tp-topic-change--${tone}`}>{displayStock.changePct >= 0 ? "+" : ""}{displayStock.changePct.toFixed(2)}%</span>}</div>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>股票身份</h3><span>{displayStock.listing ?? displayStock.industry ?? "正式欄位待補"}</span></div><EvidenceGrid rows={[["市場", displayStock.market], ["交易所", displayStock.exchange], ["產業／類別", displayStock.industry], ["資料日期", displayStock.dataDate]]} /></section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>題材歸屬</h3><span>{displayStock.topics.length} 個關係</span></div>{displayStock.topics.length ? <div className="tp-stock-encyclopedia-topics">{displayStock.topics.map((topic) => <div className="tp-stock-encyclopedia-topic" key={`${topic.name}-${topic.role ?? "unknown"}`}><strong>{topic.name}</strong><RoleChip>{label(topic.role)}</RoleChip></div>)}</div> : <p className="tp-stock-encyclopedia-muted">正式題材關係尚未提供</p>}</section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>主要題材</h3><span>正式欄位優先</span></div>{displayStock.mainTopic ? <div className="tp-stock-encyclopedia-main-topic"><div><strong>{displayStock.mainTopic.name}</strong><p>{displayStock.mainTopic.state ?? "狀態尚未提供"}{displayStock.mainTopic.lifecycle ? ` · ${displayStock.mainTopic.lifecycle}` : ""}</p></div>{displayStock.mainTopic.grade && <RoleChip>{displayStock.mainTopic.grade}</RoleChip>}</div> : <p className="tp-stock-encyclopedia-muted">正式主題欄位尚未提供</p>}</section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>摘要</h3><span>正式 read model</span></div><p className="tp-stock-encyclopedia-muted">{displayStock.summary ?? "正式摘要尚未提供；未由前端生成。"}</p></section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>技術證據</h3><span>20MA / 60MA</span></div>{technical ? <EvidenceGrid rows={[["站上 20MA", technical.above20MA], ["站上 60MA", technical.above60MA], ["20MA", technical.ma20], ["60MA", technical.ma60], ["突破狀態", technical.breakoutState], ["技術狀態", technical.technicalState]]} /> : <p className="tp-stock-encyclopedia-muted">正式 technical read model 尚未提供</p>}</section>
      <section className="tp-stock-encyclopedia-section"><div className="tp-stock-encyclopedia-section-heading"><h3>法人流向</h3><span>provider evidence</span></div>{institutionEntries.length ? <EvidenceGrid rows={institutionEntries.map(([key, value]) => [key, typeof value === "object" ? JSON.stringify(value) : value as string | number | boolean])} /> : <p className="tp-stock-encyclopedia-muted">正式法人資料尚未提供</p>}</section>
      <div className="tp-stock-encyclopedia-note">{displayStock.isPreview ? "此區塊目前為 Preview；正式 API 可用時才顯示正式欄位。" : "沒有正式 evidence 的欄位保持尚未提供，不由前端推導。"}</div>
      {displayStock.opportunity ? <Link href="/opportunities" className="tp-button tp-button--secondary tp-stock-encyclopedia-cta">進入機會頁</Link> : <span className="tp-button tp-button--secondary tp-stock-encyclopedia-cta" aria-disabled="true">機會資料尚未提供</span>}
    </div>
  </aside>;
  return presentation === "inline" || presentation === "push" ? drawer : <div className="tp-stock-encyclopedia-layer" role="presentation" onClick={onClose}>{drawer}</div>;
}
