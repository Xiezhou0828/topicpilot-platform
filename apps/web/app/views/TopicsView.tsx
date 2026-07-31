"use client";

import { Layers3, Search } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { api } from "../lib/api";
import { demoTopics } from "../lib/demo-data";
import { formatCount, formatNumber } from "../lib/format";
import { useApiResource } from "../lib/useApiResource";
import { PageHeader } from "../components/PageHeader";
import { DataOriginNotice, EmptyState, ErrorState, LoadingState } from "../components/ResourceState";
import { Delta, Grade, StatusPill } from "../components/ProductUi";

const demoList = { items: demoTopics, total: demoTopics.length, limit: 100, offset: 0 };

export function TopicsView() {
  const resource = useApiResource({ key: "topics", load: (signal) => api.getTopics(signal), fallback: demoList });
  const [query, setQuery] = useState("");
  const topics = useMemo(() => (resource.data?.items ?? [])
    .filter((topic) => `${topic.name} ${topic.parentName ?? ""}`.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => (b.score ?? -Infinity) - (a.score ?? -Infinity)), [resource.data, query]);

  return (
    <div className="page-shell">
      <PageHeader eyebrow="TOPIC TAXONOMY" title="題材輪動" description="從階層資料與 14 日強度變化觀察題材擴散；評級代表資料模型輸出，不構成投資建議。" icon={Layers3} actions={<span className="record-count">{resource.data?.total ?? "—"} topic nodes</span>} />
      <DataOriginNotice origin={resource.origin} warning={resource.warning} />
      <section className="toolbar-panel compact-toolbar"><label className="search-field"><Search size={17} /><span className="sr-only">搜尋題材</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜尋題材或父層分類…" /></label><p>依強度分數排序 · null 永遠排在最後</p></section>
      {resource.loading && <LoadingState label="正在讀取題材階層" />}
      {resource.error && <ErrorState error={resource.error} onRetry={resource.retry} />}
      {resource.data && topics.length === 0 && <EmptyState title="找不到符合條件的題材" description="請調整搜尋條件，或確認 API 是否已匯入題材節點。" />}
      {topics.length > 0 && <section className="topic-matrix" aria-label="題材強度矩陣">{topics.map((topic, index) => <Link className={`topic-tile tile-${index < 2 ? "feature" : "standard"}`} href={`/topics/${topic.slug}`} key={topic.slug}>
        <div className="topic-tile-head"><Grade value={topic.grade} /><StatusPill value={topic.state} /></div>
        <div><small>{topic.parentName ?? "未分類"}</small><h2>{topic.name}</h2></div>
        <div className="topic-score"><strong>{formatNumber(topic.score, 1)}</strong><span>STRENGTH SCORE</span></div>
        <div className="topic-tile-foot"><Delta value={topic.change14d} /><span>{formatCount(topic.memberCount)} constituents</span></div>
      </Link>)}</section>}
    </div>
  );
}
