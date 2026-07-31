"use client";

import { ArrowLeft, CircleCheck, CircleDashed, FileSearch, Gauge, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { api } from "../lib/api";
import { demoStockDetails } from "../lib/demo-data";
import { formatDateTime, formatNumber, formatPercent } from "../lib/format";
import { useApiResource } from "../lib/useApiResource";
import { DataOriginNotice, EmptyState, ErrorState, LoadingState } from "../components/ResourceState";
import { Delta, MetricCard, StatusPill } from "../components/ProductUi";

export function StockDetailView({ code }: { code: string }) {
  const fallback = demoStockDetails.find((item) => item.code === code);
  const resource = useApiResource({ key: `stock-${code}`, load: (signal) => api.getStock(code, signal), fallback });
  const stock = resource.data;
  return (
    <div className="page-shell detail-page">
      <Link className="back-link" href="/stocks"><ArrowLeft size={15} />返回股票宇宙</Link>
      {resource.loading && <LoadingState label="正在讀取個股資料輪廓" />}
      {resource.error && <ErrorState error={resource.error} onRetry={resource.retry} />}
      {!resource.loading && !resource.error && !stock && <EmptyState title="找不到這筆標的" description="API 沒有回傳對應代碼，展示 fallback 也不包含此項目。" />}
      {stock && <>
        <header className="detail-hero">
          <div><p className="eyebrow">STOCK DATA PROFILE</p><div className="detail-title"><h1>{stock.name}</h1><code>{stock.code}</code></div><p>{stock.description ?? "尚未提供公司輪廓。"}</p><div className="tag-row">{stock.topicNames.map((topic) => <span className="data-tag" key={topic}>{topic}</span>)}</div></div>
          <div className="quote-block"><span>REFERENCE CLOSE</span><strong>{formatNumber(stock.price)}</strong><Delta value={stock.changePct} /><small>{formatDateTime(stock.updatedAt)}</small></div>
        </header>
        <DataOriginNotice origin={resource.origin} warning={resource.warning} />
        <section className="metric-grid three">
          <MetricCard label="RELATIVE STRENGTH 20" value={formatNumber(stock.technical.relativeStrength20, 1)} meta="跨標的相對位置" tone="accent" />
          <MetricCard label="VOLUME RATIO" value={stock.volumeRatio === null ? "—" : `${stock.volumeRatio.toFixed(2)}×`} meta="缺值不以 0 取代" />
          <MetricCard label="VOLATILITY 20" value={stock.technical.volatility20 === null ? "—" : `${stock.technical.volatility20.toFixed(2)}%`} meta="20 日觀察值" />
        </section>
        <section className="detail-grid">
          <article className="panel evidence-panel">
            <div className="section-heading"><div><p className="eyebrow"><Gauge size={14} />TECHNICAL EVIDENCE</p><h2>技術資料摘要</h2></div><StatusPill value={stock.technical.trend} /></div>
            <dl className="evidence-list"><div><dt>20 日均線位置</dt><dd>{stock.technical.aboveMa20 === null ? <><CircleDashed size={16} />資料未提供</> : stock.technical.aboveMa20 ? <><CircleCheck size={16} />位於均線上方</> : <><ShieldAlert size={16} />位於均線下方</>}</dd></div><div><dt>相對強度 RS20</dt><dd>{formatNumber(stock.technical.relativeStrength20, 1)}</dd></div><div><dt>20 日波動度</dt><dd>{formatPercent(stock.technical.volatility20)}</dd></div><div><dt>量能比率</dt><dd>{stock.volumeRatio === null ? "—" : `${stock.volumeRatio.toFixed(2)}×`}</dd></div></dl>
          </article>
          <article className="panel evidence-panel">
            <div className="section-heading"><div><p className="eyebrow"><FileSearch size={14} />FUNDAMENTAL SNAPSHOT</p><h2>營運資料摘要</h2></div></div>
            <dl className="evidence-list"><div><dt>營收年增率</dt><dd>{formatPercent(stock.fundamental.revenueYoy)}</dd></div><div><dt>營收月增率</dt><dd>{formatPercent(stock.fundamental.revenueMom)}</dd></div><div><dt>毛利率</dt><dd>{formatPercent(stock.fundamental.grossMargin)}</dd></div><div><dt>主要群組</dt><dd>{stock.group ?? "—"}</dd></div></dl>
          </article>
          <article className="panel quality-panel">
            <div className="section-heading"><div><p className="eyebrow">DATA QUALITY</p><h2>欄位品質說明</h2></div></div>
            <ul>{stock.qualityNotes.length ? stock.qualityNotes.map((note) => <li key={note}><CircleCheck size={16} />{note}</li>) : <li><CircleDashed size={16} />沒有額外品質註記。</li>}</ul>
          </article>
        </section>
      </>}
    </div>
  );
}
