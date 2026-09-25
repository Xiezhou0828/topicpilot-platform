"use client";

import Link from "next/link";
import { BarChart3, ChevronRight, FileText, Info, Layers3, Sparkles, Target, Zap } from "lucide-react";
import { useTodayMainlines } from "../../lib/today-mainlines";
import { formatMarketDate } from "../../lib/today-market-fields";
import { Card, PageContainer } from "./V2Foundation";

function EmptyOpportunity({ message }: { message: string }) {
  return <div className="tp-opportunity-empty"><Info size={18} aria-hidden="true" /><span>{message}</span></div>;
}

export default function OpportunityMarketPage() {
  const { loading, resource } = useTodayMainlines();
  const opportunities = resource.opportunities;
  const topics = opportunities.state === "FORMAL" ? opportunities.data : [];
  const stocks = topics.flatMap((topic) => (topic.validatedStocks ?? []).map((stock) => ({ ...stock, topic: topic.topic })));
  const dataDate = opportunities.dataDate ?? resource.dataDate;
  const unavailable = loading || opportunities.state !== "FORMAL";

  return <PageContainer className="tp-opportunity-page" title="今日機會" hideHeader>
    <div className="tp-opportunity-heading"><div><h1>今日機會 <Info size={20} aria-hidden="true" /></h1><p>從今日市場結構與題材表現中，整理值得進一步研究的候選標的。</p></div><div className="tp-opportunity-heading-actions"><span>資料日期：{dataDate ? `${formatMarketDate(dataDate)}（收盤後）` : "尚未提供"}</span><Link href="/opportunities" className="tp-button tp-button--primary">查看全部機會 <ChevronRight size={17} aria-hidden="true" /></Link></div></div>
    <div className="tp-opportunity-summary-grid">
      <Card><FileText size={27} aria-hidden="true" /><strong>{unavailable ? "—" : stocks.length}</strong><span>候選標的</span><small>{unavailable ? "正式機會資料尚未發布" : "來自今日題材強度與技術面篩選"}</small></Card>
      <Card><Layers3 size={27} aria-hidden="true" /><strong>{unavailable ? "—" : topics.length}</strong><span>集中題材</span><small>{unavailable ? "正式機會資料尚未發布" : "機會主要集中於以上題材"}</small></Card>
      <Card><Sparkles size={27} aria-hidden="true" /><strong>{unavailable ? "—" : topics.filter((topic) => (topic.validatedStocks ?? []).some((stock) => stock.dataDate === dataDate)).length}</strong><span>今日新增</span><small>{unavailable ? "正式機會資料尚未發布" : "本交易日新進入候選名單"}</small></Card>
      <Card className="tp-opportunity-distribution"><div className="tp-opportunity-card-title"><BarChart3 size={22} aria-hidden="true" /><h2>機會分布（依題材）</h2></div>{topics.length > 0 ? <div className="tp-opportunity-distribution-list">{topics.slice(0, 5).map((topic) => { const topicStocks = topic.validatedStocks ?? []; return <div key={topic.topic}><span>{topic.topic}</span><i><b style={{ width: `${Math.max(6, Math.min(100, topicStocks.length / Math.max(1, stocks.length) * 100))}%` }} /></i><strong>{topicStocks.length}</strong></div>; })}</div> : <EmptyOpportunity message="正式機會分布尚未提供。" />}</Card>
    </div>
    <div className="tp-opportunity-main-grid">
      <Card className="tp-opportunity-topic-card"><div className="tp-opportunity-card-title"><Target size={22} aria-hidden="true" /><h2>主要機會題材</h2><Link href="/topics">查看題材詳情 <ChevronRight size={15} aria-hidden="true" /></Link></div>{topics.length > 0 ? <div className="tp-opportunity-topic-grid">{topics.slice(0, 3).map((topic) => <article key={topic.topic}><strong>{topic.topic}</strong><span>{(topic.validatedStocks ?? []).length} 檔</span><p>{topic.summary}</p><Link href={`/topics/${topic.topicSlug}`}>查看相關股票 <ChevronRight size={15} aria-hidden="true" /></Link></article>)}</div> : <EmptyOpportunity message="正式機會題材尚未發布。" />}</Card>
      <Card className="tp-opportunity-focus-card"><div className="tp-opportunity-card-title"><Zap size={22} aria-hidden="true" /><h2>機會觀察重點</h2></div><ol><li>今日機會主要集中於已完成正式驗證的題材。</li><li>候選標的需同時檢查題材強度、技術面與風險條件。</li><li>完整名單、入選條件與詳細分析請前往機會頁查看。</li></ol></Card>
    </div>
    <Card className="tp-opportunity-table-card"><div className="tp-opportunity-card-title"><BarChart3 size={22} aria-hidden="true" /><h2>今日機會標的 <small>（前 5 檔）</small></h2><Link href="/opportunities">查看全部機會 <ChevronRight size={15} aria-hidden="true" /></Link></div>{stocks.length > 0 ? <div className="tp-opportunity-table"><div className="tp-opportunity-row tp-opportunity-row-head"><span>#</span><span>股號</span><span>名稱</span><span>主要題材</span><span>今日漲跌幅</span><span>入選原因（摘要）</span><span /></div>{stocks.slice(0, 5).map((stock, index) => <Link className="tp-opportunity-row" href={`/stocks/${stock.code}`} key={`${stock.code}-${index}`}><span className="tp-opportunity-row-rank">{index + 1}</span><span>{stock.code}</span><strong>{stock.name}</strong><span>{stock.topic}</span><b className="is-up">尚未提供</b><span>{stock.reason ?? "正式機會條件已通過"}</span><ChevronRight size={16} aria-hidden="true" /></Link>)}</div> : <EmptyOpportunity message={loading ? "正在讀取正式機會資料。" : "正式機會資料尚未發布。"} />}</Card>
    <div className="tp-opportunity-footer"><span>資料來源：正式資料來源</span><span>資料僅供參考，不構成投資建議。</span></div>
  </PageContainer>;
}
