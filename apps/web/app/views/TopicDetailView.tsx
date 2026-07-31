"use client";

import { ArrowLeft, GitBranch, History } from "lucide-react";
import Link from "next/link";
import { api } from "../lib/api";
import { demoTopicDetails } from "../lib/demo-data";
import { formatCount, formatNumber } from "../lib/format";
import { useApiResource } from "../lib/useApiResource";
import { DataOriginNotice, EmptyState, ErrorState, LoadingState } from "../components/ResourceState";
import { Delta, Grade, StatusPill, TrendBars } from "../components/ProductUi";

export function TopicDetailView({ slug }: { slug: string }) {
  const fallback = demoTopicDetails.find((item) => item.slug === slug);
  const resource = useApiResource({ key: `topic-${slug}`, load: (signal) => api.getTopic(slug, signal), fallback });
  const topic = resource.data;
  return (
    <div className="page-shell detail-page">
      <Link className="back-link" href="/topics"><ArrowLeft size={15} />返回題材輪動</Link>
      {resource.loading && <LoadingState label="正在展開題材資料" />}
      {resource.error && <ErrorState error={resource.error} onRetry={resource.retry} />}
      {!resource.loading && !resource.error && !topic && <EmptyState title="找不到這個題材" description="API 沒有回傳對應 slug，展示 fallback 也不包含此節點。" />}
      {topic && <>
        <header className="topic-detail-hero">
          <div><p className="eyebrow">TOPIC NODE · {topic.parentName ?? "UNCLASSIFIED"}</p><div className="detail-title"><Grade value={topic.grade} /><h1>{topic.name}</h1></div><p>{topic.description ?? "尚未提供題材說明。"}</p></div>
          <div className="topic-hero-score"><span>14D CHANGE</span><Delta value={topic.change14d} /><strong>{formatNumber(topic.score, 1)}</strong><small>strength score</small></div>
        </header>
        <DataOriginNotice origin={resource.origin} warning={resource.warning} />
        <section className="detail-grid topic-detail-grid">
          <article className="panel trend-panel">
            <div className="section-heading"><div><p className="eyebrow"><History size={14} />STRENGTH HISTORY</p><h2>14 日強度軌跡</h2></div><StatusPill value={topic.state} /></div>
            {topic.trend.length ? <><TrendBars points={topic.trend} label={`${topic.name} 14 日強度軌跡`} /><div className="chart-axis"><span>{topic.trend[0]?.date ?? "—"}</span><span>{topic.trend.at(-1)?.date ?? "—"}</span></div></> : <EmptyState title="沒有歷史資料" description="題材節點存在，但 API 尚未提供強度歷史。" />}
          </article>
          <article className="panel lineage-panel">
            <div className="section-heading"><div><p className="eyebrow"><GitBranch size={14} />LINEAGE</p><h2>階層與覆蓋</h2></div></div>
            <div className="lineage-flow"><span>ROOT</span><i /><strong>{topic.parentName ?? "未分類"}</strong><i /><b>{topic.name}</b></div>
            <dl className="evidence-list"><div><dt>題材評級</dt><dd>{topic.grade ?? "—"}</dd></div><div><dt>成分標的</dt><dd>{formatCount(topic.memberCount)}</dd></div><div><dt>目前狀態</dt><dd>{topic.state ?? "—"}</dd></div></dl>
          </article>
        </section>
        <section className="data-table-panel">
          <div className="section-heading table-heading"><div><p className="eyebrow">CONSTITUENTS</p><h2>題材成分標的</h2></div><span>{topic.stocks.length} records</span></div>
          {topic.stocks.length ? <div className="table-scroll"><table><thead><tr><th>標的</th><th>群組</th><th>參考價格</th><th>漲跌幅</th><th>資料狀態</th></tr></thead><tbody>{topic.stocks.map((stock) => <tr key={stock.code}><th><Link className="stock-identity" href={`/stocks/${stock.code}`}><strong>{stock.name}</strong><small>{stock.code}</small></Link></th><td>{stock.group ?? "—"}</td><td className="numeric strong">{formatNumber(stock.price)}</td><td><Delta value={stock.changePct} /></td><td><StatusPill value={stock.signal} /></td></tr>)}</tbody></table></div> : <EmptyState title="沒有可顯示的成分標的" description="題材節點已建立，但目前沒有通過關聯驗證的標的。" />}
        </section>
      </>}
    </div>
  );
}
