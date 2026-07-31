"use client";

import { ArrowDown, Braces, Database, FileCheck2, Network, ServerCog, ShieldCheck, Workflow } from "lucide-react";
import { api } from "../lib/api";
import { demoStatus } from "../lib/demo-data";
import { formatCount, formatDate, formatDateTime, formatNumber } from "../lib/format";
import { useApiResource } from "../lib/useApiResource";
import { PageHeader } from "../components/PageHeader";
import { DataOriginNotice, ErrorState, LoadingState } from "../components/ResourceState";
import { MetricCard, StatusPill } from "../components/ProductUi";

const endpoints = [
  ["GET", "/api/v1/meta/data-status", "資料新鮮度與服務健康"],
  ["GET", "/api/v1/stocks", "標的列表與分頁"],
  ["GET", "/api/v1/stocks/{code}", "個股資料輪廓"],
  ["GET", "/api/v1/topics", "題材階層節點"],
  ["GET", "/api/v1/topics/{slug}", "題材趨勢與成分"],
  ["GET", "/api/v1/strategies", "策略 registry"],
  ["GET", "/api/v1/analytics/topic-rotation", "14 日題材輪動"],
  ["GET", "/api/v1/analytics/strategy-performance", "策略績效分析"],
];

export function DataStatusView() {
  const resource = useApiResource({ key: "data-status", load: (signal) => api.getDataStatus(signal), fallback: demoStatus });
  const status = resource.data;
  return (
    <div className="page-shell data-platform-page">
      <PageHeader eyebrow="DATA PLATFORM" title="資料狀態與系統架構" description="公開展示站只讀取 FastAPI；正式 Google Sheets 與私人流程不在瀏覽器中連線，也不會被此平台寫入。" icon={Network} actions={<span className="read-only-badge"><ShieldCheck size={15} />READ ONLY</span>} />
      <DataOriginNotice origin={resource.origin} warning={resource.warning} />
      {resource.loading && <LoadingState label="正在檢查平台健康狀態" />}
      {resource.error && <ErrorState error={resource.error} onRetry={resource.retry} />}
      {status && <>
        <section className="service-status-grid">
          <article><span>API GATEWAY</span><StatusPill value={status.apiStatus} /><small>{status.latencyMs === null ? "latency unavailable" : `${formatNumber(status.latencyMs, 0)} ms`}</small></article>
          <article><span>POSTGRES READ MODEL</span><StatusPill value={status.databaseStatus} /><small>runtime connection</small></article>
          <article><span>DATA FRESHNESS</span><strong>{formatDate(status.dataDate)}</strong><small>updated {formatDateTime(status.updatedAt)}</small></article>
          <article><span>CONTRACT</span><code>{status.bundleVersion ?? "—"}</code><small>{status.sourceMode ?? "source unavailable"}</small></article>
        </section>
        <section className="metric-grid three">
          <MetricCard label="QUALITY PASSED" value={formatCount(status.quality.passed)} meta="contract & relation checks" tone="quality" />
          <MetricCard label="WARNINGS" value={formatCount(status.quality.warnings)} meta="visible, never suppressed" />
          <MetricCard label="FAILED" value={formatCount(status.quality.failed)} meta="publish-blocking checks" />
        </section>
      </>}

      <section id="architecture" className="panel architecture-panel">
        <div className="section-heading"><div><p className="eyebrow"><Workflow size={14} />PARALLEL READ MODEL</p><h2>Strangler migration，不做一次性搬家</h2></div><span className="contract-chip">enterprise_bundle.v1</span></div>
        <div className="architecture-flow" aria-label="TopicPilot 平行讀取架構">
          <article className="architecture-node source"><span>FORMAL SOURCE</span><FileCheck2 size={24} /><strong>Validated Snapshot</strong><small>現有 Sheet 與分析引擎維持不變</small></article>
          <ArrowDown className="flow-arrow" aria-hidden="true" />
          <article className="architecture-node transform"><span>INGESTION</span><Braces size={24} /><strong>Versioned Adapter</strong><small>hash · validate · transaction</small></article>
          <ArrowDown className="flow-arrow" aria-hidden="true" />
          <div className="architecture-split">
            <article className="architecture-node"><span>READ MODEL</span><Database size={24} /><strong>PostgreSQL 16</strong><small>normalized schema · SQL views</small></article>
            <article className="architecture-node"><span>PUBLIC INPUT</span><ShieldCheck size={24} /><strong>Synthetic Fixtures</strong><small>匿名資料 · 無正式憑證</small></article>
          </div>
          <ArrowDown className="flow-arrow" aria-hidden="true" />
          <div className="architecture-split">
            <article className="architecture-node api"><span>READ API</span><ServerCog size={24} /><strong>FastAPI</strong><small>OpenAPI · problem+json</small></article>
            <article className="architecture-node ui"><span>CLIENT</span><Network size={24} /><strong>React UI</strong><small>typed mapper · explicit states</small></article>
          </div>
        </div>
      </section>

      <section className="platform-detail-grid">
        <article className="panel endpoint-panel">
          <div className="section-heading"><div><p className="eyebrow">PUBLIC INTERFACE</p><h2>Read-only API surface</h2></div></div>
          <div className="endpoint-list">{endpoints.map(([method, path, note]) => <div key={path}><span>{method}</span><code>{path}</code><small>{note}</small></div>)}</div>
        </article>
        <article className="panel principles-panel">
          <div className="section-heading"><div><p className="eyebrow">ENGINEERING PRINCIPLES</p><h2>可驗證，而非看起來有資料</h2></div></div>
          <ol><li><span>01</span><div><strong>Null stays null</strong><p>缺值不被安靜地轉成 0，介面明確顯示「—」。</p></div></li><li><span>02</span><div><strong>Failure stays visible</strong><p>正式預設不啟用合成 fallback，API 錯誤有清楚的 retry 狀態。</p></div></li><li><span>03</span><div><strong>Source stays traceable</strong><p>資料日期、契約版本與來源模式都能被使用者查閱。</p></div></li><li><span>04</span><div><strong>Formal data stays private</strong><p>公開版本不含憑證、真實持倉、授權不明行情或新聞全文。</p></div></li></ol>
        </article>
      </section>
    </div>
  );
}
