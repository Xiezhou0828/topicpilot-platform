"use client";

import Link from "next/link";
import { ChevronRight, Layers3, Star, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchTopic, roleRank, scoreLabel, sourceLabel, type TopicConstituent, type TopicDetail as TopicData, type TopicResource } from "../../lib/topic-api";
import { AppShell, Card, DataState, EmptyState, GradeChip, PageContainer, RoleChip, Table } from "./V2Foundation";

function TopicSectionHeading({ title, description }: { title: string; description?: string }) {
  return <div className="tp-topic-section-heading"><div><h2>{title}</h2>{description && <p>{description}</p>}</div></div>;
}

function priceLabel(value: number | null): string {
  return value === null ? "—" : value.toLocaleString("zh-TW", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function changeTone(value: number | null): "up" | "down" | null {
  return value === null ? null : value >= 0 ? "up" : "down";
}

function StockDrawer({ topic, stock, onClose }: { topic: TopicData; stock: TopicConstituent; onClose: () => void }) {
  const tone = changeTone(stock.changePct);
  return <div className="tp-topic-drawer-layer" role="presentation" onClick={onClose}><aside className="tp-topic-stock-drawer" role="dialog" aria-modal="true" aria-labelledby="stock-drawer-title" onClick={(event) => event.stopPropagation()}>
    <div className="tp-topic-drawer-header"><div><p className="tp-overline">STOCK DETAIL · SHARED DRAWER</p><h2 id="stock-drawer-title">{stock.name}</h2><span>{stock.code}</span></div><button type="button" className="tp-icon-button" aria-label="關閉股票詳情" onClick={onClose}><X size={20} aria-hidden="true" /></button></div>
    <div className="tp-topic-drawer-price"><strong>{priceLabel(stock.price)}</strong>{stock.changePct === null ? <DataState state="資料待更新" /> : <span className={`tp-topic-change tp-topic-change--${tone}`}>{stock.changePct >= 0 ? "+" : ""}{stock.changePct.toFixed(2)}%</span>}</div>
    <div className="tp-topic-drawer-grid"><div><span>所屬題材</span><b>{topic.name}</b></div><div><span>題材角色</span><b><RoleChip>{stock.role}</RoleChip></b></div><div><span>資料日期</span><b>{stock.dataDate ?? "—"}</b></div><div><span>更新狀態</span><b>{stock.dataFreshness ?? "資料待更新"}</b></div></div>
    <div className="tp-topic-drawer-note"><Layers3 size={18} aria-hidden="true" /><p>股票價格、漲跌幅與即時更新狀態尚未包含在 Topic Detail read model；本抽屜保留正式資料接入口，不以題材資料推估個股價格。</p></div>
    <Link href={`/stocks/${stock.code}`} className="tp-topic-drawer-link">前往股票頁 <ChevronRight size={16} aria-hidden="true" /></Link>
  </aside></div>;
}

function MissingTopicSection({ title, description }: { title: string; description: string }) {
  return <Card className="tp-topic-missing-card"><TopicSectionHeading title={title} description={description} /><div className="tp-topic-missing-state"><DataState state="資料待更新" /><p>目前 Backend 尚未提供此區塊的正式 read model，本階段不以瀏覽器推導或新增假資料。</p></div></Card>;
}

export default function TopicDetailPage({ slug }: { slug: string }) {
  const [resource, setResource] = useState<TopicResource<TopicData> | null>(null);
  const [favorite, setFavorite] = useState(false);
  const [selectedStock, setSelectedStock] = useState<TopicConstituent | null>(null);

  useEffect(() => {
    let active = true;
    fetchTopic(slug).then((next) => { if (active) setResource(next); });
    return () => { active = false; };
  }, [slug]);

  const stocks = useMemo(() => [...(resource?.data?.constituents ?? [])].sort((a, b) => roleRank(a.role) - roleRank(b.role) || a.code.localeCompare(b.code)), [resource]);
  const topic = resource?.data;

  return <AppShell currentPath="/topics"><PageContainer className="tp-topic-page" title={topic?.name ?? slug} hideHeader>
    <div className="tp-topic-detail-page">
      {!resource && <Card className="tp-topic-data-card"><DataState state="STALE" /><EmptyState title="正在載入題材資料" description="正在讀取 Topic read model。" /></Card>}
      {resource?.source === "unavailable" && <Card className="tp-topic-data-card"><DataState state="UNAVAILABLE" /><EmptyState title="題材資料目前無法取得" description={resource.error ?? "請確認 FastAPI read model 是否已啟動。"} /></Card>}
      {topic && <>
        <header className="tp-topic-identity">
          <nav className="tp-topic-breadcrumb" aria-label="題材階層"><Link href="/topics">題材</Link><span aria-hidden="true">›</span>{topic.groupName && <><span>{topic.groupName}</span><span aria-hidden="true">›</span></>}<strong>{topic.name}</strong></nav>
          <div className="tp-topic-title-row"><div><p className="tp-overline">TOPIC DETAIL · {sourceLabel(resource.source)}</p><h1>{topic.name}</h1></div><button type="button" className={`tp-topic-favorite ${favorite ? "is-active" : ""}`} aria-pressed={favorite} onClick={() => setFavorite((value) => !value)}><Star size={18} fill={favorite ? "currentColor" : "none"} aria-hidden="true" />{favorite ? "已收藏題材" : "收藏題材"}</button></div>
          <div className="tp-topic-meta-row"><GradeChip grade={topic.grade ?? "—"} /><span><b>題材強度</b> {scoreLabel(topic.score)}</span><span><b>目前狀態</b> {topic.readableState}</span><span><b>股票數</b> {topic.constituentCount} 檔</span><span><b>資料日期</b> {topic.dataDate ?? "—"}</span></div>
          <div className="tp-topic-summary-placeholder"><DataState state={resource.source === "api" ? "AVAILABLE" : "STALE"} /><p>正式 Topic read model 目前提供強度、等級、狀態與成分股；題材摘要文字尚未在 API 契約中提供。</p></div>
        </header>

        <div className="tp-topic-content">
          <MissingTopicSection title="題材生命圖" description="生命階段、進入日期、完成日期與交易日持續天數。" />
          <MissingTopicSection title="題材歷程" description="只保留影響研究判斷的重要狀態轉換。" />
          <section aria-labelledby="stocks-title"><TopicSectionHeading title="題材內股票" description="依代表股、核心股、關聯股排序；點擊股票開啟共用 Stock Drawer。" />
            <Card className="tp-topic-role-card tp-topic-stock-table-card"><div className="tp-topic-role-heading"><div><p className="tp-overline">TOPIC CONSTITUENTS</p><h3 id="stocks-title">正式成分股清單</h3></div><RoleChip>{stocks.length} 檔</RoleChip></div>
              {stocks.length ? <Table><thead><tr><th>股票／股號</th><th>題材角色</th><th>現價</th><th>漲跌幅</th><th>更新狀態</th><th /></tr></thead><tbody>{stocks.map((stock) => { const tone = changeTone(stock.changePct); return <tr key={stock.code}><td><button type="button" className="tp-topic-stock-row" onClick={() => setSelectedStock(stock)}><span className="tp-topic-stock-identity"><b>{stock.name}</b><small>{stock.code}</small></span><ChevronRight size={16} aria-hidden="true" /></button></td><td><RoleChip>{stock.role}</RoleChip></td><td>{priceLabel(stock.price)}</td><td>{stock.changePct === null ? "—" : <span className={`tp-topic-change tp-topic-change--${tone}`}>{stock.changePct >= 0 ? "+" : ""}{stock.changePct.toFixed(2)}%</span>}</td><td>{stock.dataFreshness ?? "資料待更新"}</td><td><ChevronRight size={16} aria-hidden="true" /></td></tr>; })}</tbody></Table> : <EmptyState title="目前沒有成分股資料" description="Topic read model 尚未回傳 constituent rows。" />}
            </Card>
          </section>
          <MissingTopicSection title="相關題材" description="相鄰題材與關聯強度的 downstream read model。" />
          <MissingTopicSection title="題材新聞與近期事件" description="限定的相關脈絡與證據摘要，不建立通用新聞流。" />
        </div>
      </>}
    </div>
    {topic && selectedStock && <StockDrawer topic={topic} stock={selectedStock} onClose={() => setSelectedStock(null)} />}
  </PageContainer></AppShell>;
}
