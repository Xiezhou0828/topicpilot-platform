"use client";

import Link from "next/link";
import { X } from "lucide-react";
import { useState } from "react";
import { FavoriteStar, Freshness, RoleChip } from "./V2Foundation";

export type StockDrawerTopic = {
  name: string;
  role: string | null;
};

export type StockDrawerItem = {
  code: string;
  name: string;
  price: number | null;
  changePct: number | null;
  dataFreshness: string | null;
  updatedAt?: string | null;
  dataDate?: string | null;
  topics: StockDrawerTopic[];
  mainTopic?: {
    name: string;
    grade?: string | null;
    state?: string | null;
    lifecycle?: string | null;
  } | null;
  isPreview?: boolean;
};

function priceLabel(value: number | null): string {
  return value === null ? "—" : value.toLocaleString("zh-TW", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function freshnessState(value: string | null): "盤中更新" | "盤後更新" | "資料待更新" {
  const normalized = (value ?? "").toUpperCase();
  if (/CURRENT|LIVE|INTRADAY|盤中/.test(normalized)) return "盤中更新";
  if (/EOD|POST|AFTER|盤後/.test(normalized)) return "盤後更新";
  return "資料待更新";
}

function roleLabel(value: string | null): string {
  const normalized = (value ?? "").trim().toUpperCase();
  if (["代表股", "PRIMARY", "REPRESENTATIVE", "LEADER"].includes(normalized)) return "代表股";
  if (["核心股", "CORE", "SECONDARY"].includes(normalized)) return "核心股";
  if (["關聯股", "RELATED"].includes(normalized)) return "關聯股";
  return "—";
}

export function StockEncyclopediaDrawer({ stock, onClose, presentation = "overlay" }: { stock: StockDrawerItem; onClose: () => void; presentation?: "overlay" | "inline" }) {
  const [favorite, setFavorite] = useState(false);
  const tone = stock.changePct === null ? null : stock.changePct >= 0 ? "up" : "down";
  const freshness = freshnessState(stock.dataFreshness);
  const asOf = stock.updatedAt ?? stock.dataDate ?? "尚未提供";

  const drawer = <aside className={`tp-stock-encyclopedia-drawer ${presentation === "inline" ? "tp-stock-encyclopedia-drawer--inline" : ""}`} role="dialog" aria-modal="true" aria-labelledby="stock-encyclopedia-title" onClick={(event) => event.stopPropagation()}>
      <header className="tp-stock-encyclopedia-header">
        <div>
          <p className="tp-eyebrow">個股圖鑑</p>
          <h2 id="stock-encyclopedia-title">{stock.name}</h2>
          <span>{stock.code}</span>
        </div>
        <div className="tp-stock-encyclopedia-actions">
          <FavoriteStar active={favorite} onClick={() => setFavorite((value) => !value)} />
          <button type="button" className="tp-stock-close" aria-label="關閉股票 Drawer" title="關閉" onClick={onClose}><X size={18} aria-hidden="true" /></button>
        </div>
      </header>

      <div className="tp-stock-encyclopedia-freshness"><Freshness state={freshness} asOf={asOf} />{stock.isPreview && <span className="tp-stock-preview-label">Preview</span>}</div>
      <div className="tp-stock-encyclopedia-price"><strong>{priceLabel(stock.price)}</strong>{stock.changePct === null ? <span className="tp-muted">漲跌幅尚未提供</span> : <span className={`tp-topic-change tp-topic-change--${tone}`}>{stock.changePct >= 0 ? "+" : ""}{stock.changePct.toFixed(2)}%</span>}</div>

      <section className="tp-stock-encyclopedia-section" aria-labelledby="stock-topics-title">
        <div className="tp-stock-encyclopedia-section-heading"><h3 id="stock-topics-title">題材身分</h3><span>共 {stock.topics.length} 個題材</span></div>
        {stock.topics.length ? <div className="tp-stock-encyclopedia-topics">{stock.topics.map((topic) => <div className="tp-stock-encyclopedia-topic" key={`${topic.name}-${topic.role ?? "unknown"}`}><strong>{topic.name}</strong><RoleChip>{roleLabel(topic.role)}</RoleChip></div>)}</div> : <p className="tp-stock-encyclopedia-muted">尚未提供題材身分。</p>}
      </section>

      <section className="tp-stock-encyclopedia-section" aria-labelledby="stock-main-topic-title">
        <div className="tp-stock-encyclopedia-section-heading"><h3 id="stock-main-topic-title">主要題材摘要</h3><span>研究入口</span></div>
        {stock.mainTopic ? <div className="tp-stock-encyclopedia-main-topic"><div><strong>{stock.mainTopic.name}</strong><p>{stock.mainTopic.state ?? "狀態尚未提供"}{stock.mainTopic.lifecycle ? ` · ${stock.mainTopic.lifecycle}` : ""}</p></div>{stock.mainTopic.grade && <RoleChip>{stock.mainTopic.grade}</RoleChip>}</div> : <p className="tp-stock-encyclopedia-muted">尚未提供主要題材摘要。</p>}
      </section>

      <div className="tp-stock-encyclopedia-note">價格與漲跌幅只在有正式行情欄位時呈現；缺少的題材研究欄位保留為尚未提供。</div>
      <Link href="/opportunities" className="tp-button tp-button--secondary tp-stock-encyclopedia-cta">查看機會 →</Link>
    </aside>;
  return presentation === "inline" ? drawer : <div className="tp-stock-encyclopedia-layer" role="presentation" onClick={onClose}>{drawer}</div>;
}
