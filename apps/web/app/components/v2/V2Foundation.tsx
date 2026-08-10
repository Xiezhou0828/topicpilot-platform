"use client";

import Link from "next/link";
import { Bell, CircleHelp, Menu, Search, Settings, Star } from "lucide-react";
import { useState } from "react";

export const navItems = [
  ["今日市場", "/"], ["題材", "/topics"], ["股票", "/stocks"],
  ["收藏", "/favorites"], ["機會", "/opportunities"], ["AI研究室", "/ai-studio"],
] as const;

export function Surface({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`tp-surface ${className}`}>{children}</section>;
}

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <Surface className={`tp-card ${className}`}>{children}</Surface>;
}

export function Button({ children, variant = "primary", ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "quiet" }) {
  return <button className={`tp-button tp-button--${variant}`} {...props}>{children}</button>;
}

export function IconButton({ label, children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return <button className="tp-icon-button" aria-label={label} title={label} {...props}>{children}</button>;
}

export function SearchInput({ placeholder = "搜尋題材、股票", ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return <label className="tp-search-input"><Search size={18} aria-hidden="true" /><input {...props} placeholder={placeholder} /></label>;
}

export function GlobalSearchShell() {
  const [open, setOpen] = useState(false);
  return <div className="tp-global-search"><button className="tp-search-trigger" onClick={() => setOpen(true)}><Search size={18} /><span>搜尋題材、股票</span><kbd>⌘ K</kbd></button>{open && <div className="tp-search-popover"><SearchInput autoFocus placeholder="搜尋尚未啟用" /><p className="tp-muted">全域搜尋介面已就緒，搜尋資料串接將於後續階段加入。</p><button className="tp-close" onClick={() => setOpen(false)}>關閉</button></div>}</div>;
}

export function UtilityBar() {
  return <div className="tp-utility"><GlobalSearchShell /><div className="tp-utility-actions"><IconButton label="通知"><Bell size={18} /></IconButton><IconButton label="設定"><Settings size={18} /></IconButton><IconButton label="說明"><CircleHelp size={18} /></IconButton></div></div>;
}

export function PrimaryNav({ currentPath }: { currentPath: string }) {
  return <nav className="tp-primary-nav" aria-label="主要導覽"><Link href="/" className="tp-wordmark"><span className="tp-mark">T</span><span>TopicPilot</span></Link><div className="tp-nav-links">{navItems.map(([label, href]) => <Link key={href} href={href} className={currentPath === href ? "is-active" : ""}>{label}</Link>)}</div><IconButton label="開啟導覽"><Menu size={20} /></IconButton></nav>;
}

export function AppShell({ children, currentPath }: { children: React.ReactNode; currentPath: string }) {
  return <div className="tp-v2-shell"><PrimaryNav currentPath={currentPath} /><UtilityBar /><main className="tp-main">{children}</main></div>;
}

export function PageContainer({ eyebrow, title, description, children }: { eyebrow?: string; title: string; description?: string; children?: React.ReactNode }) {
  return <div className="tp-page-container"><header className="tp-page-header">{eyebrow && <p className="tp-eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description && <p className="tp-page-description">{description}</p>}</header>{children}</div>;
}

export function DataState({ state = "AVAILABLE" }: { state?: "AVAILABLE" | "STALE" | "UNAVAILABLE" | "PROVIDER_ERROR" | "盤中更新" | "盤後更新" | "資料待更新" }) {
  return <span className={`tp-data-state tp-state-${state === "AVAILABLE" ? "available" : state === "STALE" ? "stale" : "unavailable"}`}>{state === "AVAILABLE" ? "資料可用" : state === "STALE" ? "資料稍舊" : state === "UNAVAILABLE" ? "資料暫不可用" : state === "PROVIDER_ERROR" ? "資料來源異常" : state}</span>;
}

export function Freshness({ state = "盤中更新", asOf = "尚未連接資料" }: { state?: "盤中更新" | "盤後更新" | "資料待更新"; asOf?: string }) {
  return <span className="tp-freshness"><span className="tp-freshness-dot" />{state} · {asOf}</span>;
}

export function Skeleton({ className = "" }: { className?: string }) { return <span className={`tp-skeleton ${className}`} aria-hidden="true" />; }
export function EmptyState({ title = "這裡會顯示內容", description = "目前尚未接入本頁資料。" }: { title?: string; description?: string }) { return <div className="tp-empty-state"><div className="tp-empty-icon"><Search size={20} /></div><h2>{title}</h2><p>{description}</p></div>; }
export function FavoriteStar({ active = false }: { active?: boolean }) { return <IconButton label={active ? "取消收藏" : "加入收藏"}><Star size={18} fill={active ? "currentColor" : "none"} /></IconButton>; }
export function GradeChip({ grade = "—" }: { grade?: string }) { return <span className="tp-chip tp-grade-chip">{grade}</span>; }
export function RoleChip({ children }: { children: React.ReactNode }) { return <span className="tp-chip tp-role-chip">{children}</span>; }
export function Tabs({ items }: { items: string[] }) { return <div className="tp-tabs" role="tablist">{items.map((item, i) => <button key={item} className={i === 0 ? "is-active" : ""} role="tab">{item}</button>)}</div>; }
export function SegmentedControl({ items }: { items: string[] }) { return <div className="tp-segmented">{items.map((item, i) => <button key={item} className={i === 0 ? "is-active" : ""}>{item}</button>)}</div>; }
export function Tooltip({ children, label }: { children: React.ReactNode; label: string }) { return <span className="tp-tooltip" title={label}>{children}</span>; }
export function Table({ children }: { children: React.ReactNode }) { return <div className="tp-table-wrap"><table className="tp-table">{children}</table></div>; }
