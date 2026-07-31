"use client";

import { Search, TableProperties } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { api } from "../lib/api";
import { demoStocks } from "../lib/demo-data";
import { formatDateTime, formatNumber } from "../lib/format";
import { useApiResource } from "../lib/useApiResource";
import { PageHeader } from "../components/PageHeader";
import { DataOriginNotice, EmptyState, ErrorState, LoadingState } from "../components/ResourceState";
import { Delta, StatusPill } from "../components/ProductUi";

const demoList = { items: demoStocks, total: demoStocks.length, limit: 100, offset: 0 };

export function StocksView() {
  const resource = useApiResource({ key: "stocks", load: (signal) => api.getStocks(signal), fallback: demoList });
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("全部");
  const rows = useMemo(() => (resource.data?.items ?? []).filter((stock) => {
    const matchesQuery = `${stock.code} ${stock.name} ${stock.group ?? ""} ${stock.topicNames.join(" ")}`.toLowerCase().includes(query.toLowerCase());
    const matchesFilter = filter === "全部" || (filter === "資料完整" ? stock.price !== null && stock.updatedAt !== null : stock.price === null || stock.updatedAt === null);
    return matchesQuery && matchesFilter;
  }), [resource.data, query, filter]);

  return (
    <div className="page-shell">
      <PageHeader eyebrow="STOCK UNIVERSE" title="股票宇宙" description="以一致欄位查看匿名標的、題材關聯與資料完整度；缺值保留為空，不以 0 代替。" icon={TableProperties} actions={<span className="record-count">{resource.data?.total ?? "—"} records</span>} />
      <DataOriginNotice origin={resource.origin} warning={resource.warning} />
      <section className="toolbar-panel" aria-label="股票篩選工具">
        <label className="search-field"><Search size={17} aria-hidden="true" /><span className="sr-only">搜尋股票</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜尋代碼、名稱、題材…" /></label>
        <div className="segmented" role="group" aria-label="資料完整度篩選">{["全部", "資料完整", "含缺值"].map((item) => <button type="button" key={item} className={filter === item ? "active" : ""} aria-pressed={filter === item} onClick={() => setFilter(item)}>{item}</button>)}</div>
      </section>
      {resource.loading && <LoadingState label="正在建立股票宇宙" />}
      {resource.error && <ErrorState error={resource.error} onRetry={resource.retry} />}
      {resource.data && rows.length === 0 && <EmptyState title="找不到符合條件的資料" description="請調整關鍵字或篩選條件；資料缺值不會被視為 0。" />}
      {rows.length > 0 && <section className="data-table-panel" aria-label="股票資料列表">
        <div className="table-scroll"><table><thead><tr><th scope="col">標的</th><th scope="col">資料狀態</th><th scope="col">收盤價</th><th scope="col">漲跌幅</th><th scope="col">量比</th><th scope="col">題材關聯</th><th scope="col">更新時間</th></tr></thead><tbody>{rows.map((stock) => <tr key={stock.code}><th scope="row"><Link className="stock-identity" href={`/stocks/${stock.code}`}><strong>{stock.name}</strong><small>{stock.code} · {stock.market ?? "—"}</small></Link></th><td><StatusPill value={stock.signal} /></td><td className="numeric strong">{formatNumber(stock.price)}</td><td><Delta value={stock.changePct} /></td><td className="numeric">{stock.volumeRatio === null ? "—" : `${stock.volumeRatio.toFixed(2)}×`}</td><td><div className="tag-row">{stock.topicNames.length ? stock.topicNames.slice(0, 2).map((topic) => <span className="data-tag" key={topic}>{topic}</span>) : <span className="missing-value">未提供</span>}</div></td><td className="timestamp">{formatDateTime(stock.updatedAt)}</td></tr>)}</tbody></table></div>
      </section>}
    </div>
  );
}
