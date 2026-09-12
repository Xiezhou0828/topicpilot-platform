"use client";

import { useEffect, useState } from "react";
import type { CatalogTopic } from "../../lib/topic-catalog";
import { historyWindow, loadTopicHistory, type FormalSnapshot, type HistoryResource } from "../../lib/topic-history";
import { Button, Card, Table } from "./V2Foundation";

export function SnapshotMetadata({ snapshot }: { snapshot: FormalSnapshot }) {
  return <details><summary>來源與發布紀錄</summary>{Object.entries({
    identity: { topicId: snapshot.topicId, topicSlug: snapshot.topicSlug, topicName: snapshot.topicName, snapshotDate: snapshot.snapshotDate, asOfAt: snapshot.asOfAt, dataStatus: snapshot.dataStatus, calculationVersion: snapshot.calculationVersion },
    source: snapshot.source, publication: snapshot.publication,
  }).map(([section, values]) => <section key={section}><h4>{section}</h4><dl style={{ overflowWrap: "anywhere" }}>{Object.entries(values).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value === null || value === undefined || value === "" ? "未提供" : String(value)}</dd></div>)}</dl></section>)}</details>;
}

export function SnapshotTable({ snapshots }: { snapshots: FormalSnapshot[] }) {
  return <Table><thead><tr><th>交易日期 / asOfAt</th><th>已觀測 / 成員數</th><th>平均日漲跌 (%)</th><th>資料 / 發布狀態</th><th>來源與紀錄</th></tr></thead><tbody>{snapshots.map((row) => <tr key={row.publication.snapshotIdentity}>
    <td>{row.snapshotDate}<p className="tp-muted">{row.asOfAt ?? "asOfAt 未提供"}</p></td>
    <td>{row.observedStockCount ?? "未提供"} / {row.stockCount ?? "未提供"}</td>
    <td>{row.averageChange === null || row.averageChange === undefined ? "未提供" : `${row.averageChange}%`}</td>
    <td>{row.dataStatus} · {row.publication.mode} / {row.publication.state} / {row.publication.membershipMode} / {row.publication.finalityState}</td>
    <td><SnapshotMetadata snapshot={row} /></td>
  </tr>)}</tbody></Table>;
}

export function HistoryContent({ resource, retry, onPage }: { resource: HistoryResource; retry: () => void; onPage: (offset: number) => void }) {
  if (resource.state === "LOADING") return <p role="status" data-history-state="LOADING">正式歷史載入中…</p>;
  if (!resource.data) return <div role={resource.state === "ERROR" ? "alert" : "status"} data-history-state={resource.state}><p>{resource.state} · {resource.reason}</p>{resource.state === "ERROR" && <Button onClick={retry}>重新載入題材</Button>}</div>;
  const page = resource.data;
  return <div data-history-state={resource.state}>
    <p>asOf {page.asOf} · {page.availability.state}</p>
    {page.availability.reason && <p>{page.availability.reason}</p>}
    {page.availability.reasonCode && <p className="tp-muted">{page.availability.reasonCode}</p>}
    {resource.state === "NOT_APPLICABLE" && <p>NOT_APPLICABLE · Parent 不適用 Leaf 正式歷史。</p>}
    {resource.state === "UNAVAILABLE" && <p>正式歷史來源目前不可用。</p>}
    {resource.state === "EMPTY" && <p>{page.total === 0 ? "此範圍尚無正式歷史紀錄。" : "此頁沒有正式歷史紀錄。"}</p>}
    {resource.state === "AVAILABLE" && <><p>此頁 {page.items.length} 筆 / 範圍內共 {page.total} 筆正式紀錄；依後端順序呈現。</p><SnapshotTable snapshots={page.items} /></>}
    {(resource.state === "AVAILABLE" || resource.state === "EMPTY") && (page.offset > 0 || page.total > page.limit) && <div className="tp-page-tools"><Button disabled={page.offset === 0} onClick={() => onPage(Math.max(0, page.offset - page.limit))}>上一頁歷史</Button><Button disabled={page.limit <= 0 || page.offset + page.limit >= page.total} onClick={() => onPage(page.offset + page.limit)}>下一頁歷史</Button></div>}
  </div>;
}

function LeafHistory({ topic, retry }: { topic: CatalogTopic; retry: () => void }) {
  const [offset, setOffset] = useState(0);
  const [resource, setResource] = useState<HistoryResource>({ state: "LOADING", data: null });
  useEffect(() => {
    const controller = new AbortController();
    loadTopicHistory(topic, offset, { signal: controller.signal }).then((next) => {
      if (!controller.signal.aborted) setResource(next);
    });
    return () => controller.abort();
  }, [topic, offset]);
  const window = historyWindow(topic.asOf);
  return <><p>範圍 {window.from} ～ {window.to}（最多 366 日區間）。只顯示已正式發布的紀錄；資料日期可能早於查詢日期。</p><HistoryContent resource={resource} retry={retry} onPage={(next) => { setResource({ state: "LOADING", data: null }); setOffset(next); }} /></>;
}

export function TopicSnapshotHistory({ topic, retry }: { topic: CatalogTopic; retry: () => void }) {
  return <Card><h2>正式 Snapshot 歷史</h2>{topic.kind === "PARENT" ? <p data-history-state="NOT_APPLICABLE">NOT_APPLICABLE · Parent 僅供階層導航，正式歷史屬於 Leaf。asOf {topic.asOf}</p> : <LeafHistory key={`${topic.topicId}:${topic.slug}:${topic.asOf}`} topic={topic} retry={retry} />}</Card>;
}
