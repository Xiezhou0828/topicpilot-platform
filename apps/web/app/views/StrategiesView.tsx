"use client";

import { FlaskConical, Info } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { api } from "../lib/api";
import { demoCandidates, demoPerformance, demoStrategies } from "../lib/demo-data";
import { formatCount, formatDate, formatNumber, formatPercent } from "../lib/format";
import type { StrategyKey } from "../lib/types";
import { useApiResource } from "../lib/useApiResource";
import { PageHeader } from "../components/PageHeader";
import { DataOriginNotice, EmptyState, ErrorState, LoadingState } from "../components/ResourceState";
import { MetricCard, StatusPill } from "../components/ProductUi";

export function StrategiesView() {
  const strategies = useApiResource({ key: "strategies", load: (signal) => api.getStrategies(signal), fallback: demoStrategies });
  const performance = useApiResource({ key: "strategy-performance", load: (signal) => api.getStrategyPerformance(signal), fallback: demoPerformance });
  const [selected, setSelected] = useState<StrategyKey>("MAS");
  const activeKey = strategies.data?.some((item) => item.key === selected)
    ? selected
    : strategies.data?.[0]?.key ?? selected;
  const candidates = useApiResource({ key: `strategy-candidates-${activeKey}`, load: (signal) => api.getStrategyCandidates(activeKey, signal), fallback: demoCandidates.filter((item) => item.strategyKey === activeKey) });
  const active = strategies.data?.find((item) => item.key === activeKey) ?? null;
  const activePerformance = useMemo(() => performance.data?.filter((item) => item.strategyKey === activeKey) ?? [], [performance.data, activeKey]);

  return (
    <div className="page-shell">
      <PageHeader eyebrow="STRATEGY LAB" title="策略實驗室" description="六個穩定策略識別碼共用候選與績效契約；結果只用於展示可重現分析流程。" icon={FlaskConical} actions={<span className="record-count">MAS · MAV · TMC · BB · PB · KD</span>} />
      <DataOriginNotice origin={strategies.origin ?? candidates.origin} warning={strategies.warning ?? candidates.warning} />
      {strategies.loading && <LoadingState label="正在讀取策略 registry" />}
      {strategies.error && <ErrorState error={strategies.error} onRetry={strategies.retry} />}
      {strategies.data && strategies.data.length === 0 && <EmptyState title="策略 registry 是空的" description="API 已回應，但尚未提供任何策略定義。" />}
      {strategies.data && strategies.data.length > 0 && <>
        <div className="strategy-tabs" role="tablist" aria-label="策略選擇">{strategies.data.map((strategy) => <button key={strategy.key} type="button" role="tab" aria-selected={activeKey === strategy.key} className={activeKey === strategy.key ? "active" : ""} onClick={() => setSelected(strategy.key)}><code>{strategy.key}</code><span><strong>{strategy.name}</strong><small>{formatCount(strategy.candidateCount)} candidates</small></span></button>)}</div>
        {active && <section className="strategy-hero panel"><div><p className="eyebrow">ACTIVE STRATEGY · {active.key}</p><h2>{active.name}</h2><p>{active.summary}</p></div><div className="strategy-meta"><StatusPill value={active.status} /><span>batch {formatDate(active.dataDate)}</span></div></section>}
        <section className="metric-grid three strategy-metrics">{["5D", "10D"].map((horizon) => { const metric = activePerformance.find((item) => item.horizon === horizon); return <MetricCard key={horizon} label={`${horizon} AVG RETURN`} value={formatPercent(metric?.returnPct ?? null)} meta={`win rate ${formatPercent(metric?.winRatePct ?? null)} · n=${formatCount(metric?.sampleCount ?? null)}`} tone={horizon === "10D" ? "accent" : "default"} />; })}<MetricCard label="CANDIDATE BATCH" value={formatCount(active?.candidateCount ?? null)} meta="同資料日、同策略版本" /></section>
        {candidates.loading && <LoadingState label={`正在讀取 ${activeKey} 候選批次`} />}
        {candidates.error && <ErrorState error={candidates.error} onRetry={candidates.retry} />}
        {candidates.data && candidates.data.length === 0 && <EmptyState title="本批次沒有候選" description="空批次是有效結果，不會被誤判為 API 失敗。" />}
        {candidates.data && candidates.data.length > 0 && <section className="candidate-grid" aria-label={`${activeKey} 策略候選`}>{candidates.data.map((candidate) => <article className="candidate-card" key={`${candidate.strategyKey}-${candidate.code}`}><header><span className="candidate-rank">#{candidate.rank ?? "—"}</span><code>{candidate.strategyKey}</code></header><div><Link href={`/stocks/${candidate.code}`}><h3>{candidate.name}</h3><p>{candidate.code} · {candidate.topic ?? "題材未提供"}</p></Link></div><dl><div><dt>MODEL SCORE</dt><dd>{formatNumber(candidate.score, 1)}</dd></div><div><dt>REFERENCE PRICE</dt><dd>{formatNumber(candidate.price)}</dd></div></dl><p className="candidate-reason"><Info size={15} />{candidate.reason ?? "尚未提供候選原因。"}</p><small>{formatDate(candidate.dataDate)}</small></article>)}</section>}
      </>}
    </div>
  );
}
