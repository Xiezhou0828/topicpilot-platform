"use client";

import { ArrowRight, Braces, CircleGauge, Database, Layers3, Workflow } from "lucide-react";
import Link from "next/link";
import { api } from "../lib/api";
import { demoPerformance, demoRotation, demoStatus, demoStocks } from "../lib/demo-data";
import { formatCount, formatDate, formatDateTime, formatNumber } from "../lib/format";
import { useApiResource } from "../lib/useApiResource";
import { DataOriginNotice, ErrorState, LoadingState } from "../components/ResourceState";
import { Delta, Grade, InlineLink, MetricCard, StatusPill } from "../components/ProductUi";

const demoStockList = { items: demoStocks, total: demoStocks.length, limit: 100, offset: 0 };

export function OverviewView() {
  const status = useApiResource({ key: "overview-status", load: (signal) => api.getDataStatus(signal), fallback: demoStatus });
  const stocks = useApiResource({ key: "overview-stocks", load: (signal) => api.getStocks(signal), fallback: demoStockList });
  const rotation = useApiResource({ key: "overview-rotation", load: (signal) => api.getTopicRotation(signal), fallback: demoRotation });
  const performance = useApiResource({ key: "overview-performance", load: (signal) => api.getStrategyPerformance(signal), fallback: demoPerformance });

  const warm = rotation.data?.filter((item) => item.direction === "warming").slice(0, 3) ?? [];
  const cool = rotation.data?.filter((item) => item.direction === "cooling").slice(0, 3) ?? [];
  const perf10d = performance.data?.filter((item) => item.horizon === "10D").slice(0, 6) ?? [];

  return (
    <div className="page-shell overview-page">
      <section className="overview-hero">
        <div className="hero-copy">
          <p className="eyebrow"><CircleGauge size={14} />FINANCIAL DATA READ PLATFORM</p>
          <h1>把市場資料，轉成<br /><em>可驗證的研究流程。</em></h1>
          <p>TopicPilot Platform 將既有 Snapshot 映射至 PostgreSQL，透過 FastAPI 提供一致契約，再由 React 呈現題材、個股與策略研究證據。</p>
          <div className="hero-actions">
            <Link className="button primary" href="/topics">探索題材輪動<ArrowRight size={16} /></Link>
            <Link className="button ghost" href="/data-status">查看資料架構</Link>
          </div>
        </div>
        <aside className="hero-terminal" aria-label="平台資料狀態摘要">
          <div className="terminal-head"><span><i /> PLATFORM STATUS</span><small>READ ONLY</small></div>
          {status.loading && <div className="terminal-loading">Connecting to runtime API…</div>}
          {status.error && <div className="terminal-error"><strong>API UNAVAILABLE</strong><span>{status.error.message}</span><button type="button" onClick={status.retry}>Retry</button></div>}
          {status.data && <>
            <div className="terminal-row"><span>api.gateway</span><StatusPill value={status.data.apiStatus} /></div>
            <div className="terminal-row"><span>postgres.read_model</span><StatusPill value={status.data.databaseStatus} /></div>
            <div className="terminal-row"><span>contract</span><code>{status.data.bundleVersion ?? "—"}</code></div>
            <div className="terminal-row"><span>data_date</span><code>{formatDate(status.data.dataDate)}</code></div>
            <div className="terminal-footer"><span>last sync</span><time>{formatDateTime(status.data.updatedAt)}</time></div>
          </>}
        </aside>
      </section>

      <DataOriginNotice origin={status.origin ?? stocks.origin} warning={status.warning ?? stocks.warning} />

      <section className="metric-grid" aria-label="資料集摘要">
        <MetricCard label="STOCK UNIVERSE" value={formatCount(status.data?.counts.stocks ?? null)} meta="已正規化標的" />
        <MetricCard label="TOPIC TAXONOMY" value={formatCount(status.data?.counts.topics ?? null)} meta="可追溯題材節點" tone="accent" />
        <MetricCard label="STRATEGY CANDIDATES" value={formatCount(status.data?.counts.strategyCandidates ?? null)} meta="六策略同批次候選" />
        <MetricCard label="QUALITY CHECKS" value={formatCount(status.data?.quality.passed ?? null)} meta={`${formatCount(status.data?.quality.warnings ?? null)} warning · ${formatCount(status.data?.quality.failed ?? null)} failed`} tone="quality" />
      </section>

      <section className="dashboard-grid">
        <article className="panel topic-pulse-panel">
          <div className="section-heading"><div><p className="eyebrow"><Layers3 size={14} />14-DAY ROTATION</p><h2>題材溫度差</h2></div><InlineLink href="/topics">查看全部</InlineLink></div>
          {rotation.loading && <LoadingState label="正在計算題材輪動" />}
          {rotation.error && <ErrorState error={rotation.error} onRetry={rotation.retry} />}
          {rotation.data && <div className="rotation-columns">
            <div><h3><span className="pulse warm" />正在升溫</h3>{warm.length ? warm.map((topic) => <Link className="rotation-row" href={`/topics/${topic.slug}`} key={topic.slug}><Grade value={topic.grade} /><span><strong>{topic.name}</strong><small>{topic.parentName ?? "未分類"}</small></span><Delta value={topic.change14d} /></Link>) : <p className="compact-empty">目前沒有升溫題材。</p>}</div>
            <div><h3><span className="pulse cool" />正在降溫</h3>{cool.length ? cool.map((topic) => <Link className="rotation-row" href={`/topics/${topic.slug}`} key={topic.slug}><Grade value={topic.grade} /><span><strong>{topic.name}</strong><small>{topic.parentName ?? "未分類"}</small></span><Delta value={topic.change14d} /></Link>) : <p className="compact-empty">目前沒有降溫題材。</p>}</div>
          </div>}
        </article>

        <article className="panel stock-focus-panel">
          <div className="section-heading"><div><p className="eyebrow">RESEARCH UNIVERSE</p><h2>資料焦點</h2></div><InlineLink href="/stocks">股票宇宙</InlineLink></div>
          {stocks.loading && <LoadingState label="正在讀取個股摘要" />}
          {stocks.error && <ErrorState error={stocks.error} onRetry={stocks.retry} />}
          {stocks.data && <div className="focus-list">{stocks.data.items.slice(0, 4).map((stock, index) => <Link href={`/stocks/${stock.code}`} key={stock.code} className="focus-row"><span className="focus-rank">0{index + 1}</span><span className="focus-identity"><strong>{stock.name}</strong><small>{stock.code} · {stock.group ?? "未分類"}</small></span><span className="focus-price"><strong>{formatNumber(stock.price)}</strong><Delta value={stock.changePct} /></span></Link>)}</div>}
        </article>
      </section>

      <section className="panel strategy-strip">
        <div className="section-heading"><div><p className="eyebrow">REPRODUCIBLE RESEARCH</p><h2>六策略，同一套績效契約</h2></div><InlineLink href="/strategies">開啟策略實驗室</InlineLink></div>
        {performance.loading && <LoadingState label="正在讀取策略績效" />}
        {performance.error && <ErrorState error={performance.error} onRetry={performance.retry} />}
        {perf10d.length > 0 && <div className="performance-grid">{perf10d.map((item) => <article key={`${item.strategyKey}-${item.horizon}`}><span>{item.strategyKey}</span><strong>{item.returnPct === null ? "—" : `${item.returnPct > 0 ? "+" : ""}${item.returnPct.toFixed(2)}%`}</strong><small>{item.horizon} · n={formatCount(item.sampleCount)}</small></article>)}</div>}
      </section>

      <section className="engineering-callout">
        <div><p className="eyebrow"><Workflow size={14} />ENGINEERING CASE STUDY</p><h2>不是一張漂亮的 Dashboard，<br />而是一條能被追蹤的資料路徑。</h2></div>
        <div className="engineering-points">
          <span><Database size={18} /><strong>Normalized read model</strong><small>PostgreSQL · SQL Views</small></span>
          <span><Braces size={18} /><strong>Contract-first API</strong><small>FastAPI · OpenAPI</small></span>
          <span><Layers3 size={18} /><strong>Explicit UI states</strong><small>Loading · Empty · Error</small></span>
        </div>
      </section>
    </div>
  );
}
