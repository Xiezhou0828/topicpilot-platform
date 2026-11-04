"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell, PageContainer } from "./V2Foundation";
import { StockEncyclopediaDrawer, type StockDetailSection, type StockDrawerItem } from "./StockEncyclopediaDrawer";

const STOCK_SECTIONS: Array<{ id: StockDetailSection; label: string }> = [
  { id: "overview", label: "個股總覽" },
  { id: "technical", label: "技術分析" },
  { id: "chip", label: "籌碼面" },
  { id: "company", label: "公司研究" },
  { id: "topics", label: "題材關聯" },
];

function sectionFromLocation(): StockDetailSection {
  if (typeof window === "undefined") return "overview";
  const tab = new URLSearchParams(window.location.search).get("tab");
  if (tab === "fundamental") return "company";
  return STOCK_SECTIONS.some((section) => section.id === tab) ? tab as StockDetailSection : "overview";
}

function stockSeed(code: string): StockDrawerItem {
  return {
    code,
    name: code,
    market: null,
    exchange: null,
    listing: null,
    price: null,
    changePct: null,
    volume: null,
    eod: null,
    updateMode: null,
    dataFreshness: null,
    updatedAt: null,
    dataDate: null,
    topics: [],
    mainTopic: null,
    technicalEvidence: null,
    institutionFlows: null,
    summary: null,
    opportunity: null,
    isPreview: false,
  };
}

export default function StockDetailRoute({ code }: { code: string }) {
  const [activeSection, setActiveSection] = useState<StockDetailSection>(sectionFromLocation);

  useEffect(() => {
    const sync = () => setActiveSection(sectionFromLocation());
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  const selectSection = (section: StockDetailSection) => {
    const url = new URL(window.location.href);
    if (section === "overview") url.searchParams.delete("tab");
    else url.searchParams.set("tab", section);
    window.history.pushState({}, "", url);
    setActiveSection(section);
  };

  return <AppShell currentPath="/stocks">
    <PageContainer title="個股研究" hideHeader className="tp-stock-detail-route">
      <Link className="tp-stock-detail-back" href="/stocks">← 股票圖鑑</Link>
      <div className="tp-stock-detail-layout">
        <aside className="tp-stock-detail-sidebar" aria-label="個股功能導覽">
          <p>個股功能</p>
          <h2>研究導覽</h2>
          <nav aria-label="個股研究分頁">
            {STOCK_SECTIONS.map((section) => <button
              type="button"
              key={section.id}
              className={activeSection === section.id ? "is-active" : ""}
              aria-current={activeSection === section.id ? "page" : undefined}
              onClick={() => selectSection(section.id)}
            >{section.label}</button>)}
          </nav>
        </aside>
        <main className="tp-stock-detail-main">
          <StockEncyclopediaDrawer
            stock={stockSeed(code)}
            presentation="page"
            activeSection={activeSection}
            onClose={() => { window.location.href = "/stocks"; }}
          />
        </main>
      </div>
    </PageContainer>
  </AppShell>;
}
