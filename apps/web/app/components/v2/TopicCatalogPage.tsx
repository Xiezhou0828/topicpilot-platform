"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { catalogHref, loadCatalog, type CatalogAvailability, type CatalogPage, type CatalogResource, type CatalogTopic } from "../../lib/topic-catalog";
import { AppShell, Button, Card, EmptyState, PageContainer, Table } from "./V2Foundation";
import { currentSnapshot } from "../../lib/topic-history";
import { SnapshotTable, TopicSnapshotHistory } from "./TopicSnapshotHistory";

const unknown = "未提供";

function Availability({ value }: { value: CatalogAvailability }) {
  const labels = { AVAILABLE: "資料可用", UNAVAILABLE: "資料不可用", NOT_APPLICABLE: "不適用" };
  return <div data-availability={value.state}><p>{labels[value.state]} · {value.state} · asOf {value.asOf}</p>{value.reason && <p>{value.reason}</p>}{value.reasonCode && <p className="tp-muted">{value.reasonCode}</p>}</div>;
}

function Metadata({ values }: { values: object }) {
  return <dl style={{ overflowWrap: "anywhere" }}>{Object.entries(values).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value === null || value === undefined || value === "" ? unknown : String(value)}</dd></div>)}</dl>;
}

function Hierarchy({ topic }: { topic: CatalogTopic }) {
  return <div>{(["parents", "children"] as const).map((key) => {
    const nodes = topic.hierarchy[key];
    return <div key={key}><h3>{key === "parents" ? "上層題材" : "下層題材"}</h3>{!nodes ? <p>階層資料未提供</p> : nodes.length === 0 ? <p>無{key === "parents" ? "上層" : "下層"}關係</p> : <ul>{nodes.map((node) => <li key={node.topicId}><Link href={catalogHref(node.slug, topic.asOf)}>{node.name}</Link> <span className="tp-muted">{node.slug} · {node.topicId}</span></li>)}</ul>}</div>;
  })}</div>;
}

export function TopicCatalogDetail({ topic, retry = () => {} }: { topic: CatalogTopic; retry?: () => void }) {
  const parent = topic.kind === "PARENT";
  const snapshot = topic.currentFormalSnapshot;
  const formal = currentSnapshot(topic);
  return <>
    <Card><h2>{topic.name}</h2><Metadata values={{ 類型: topic.kind, 發布狀態: topic.status, asOf: topic.asOf }} /><Availability value={topic.availability} /><Hierarchy topic={topic} /></Card>
    <Card><h2>有效 Leaf 成員</h2>{parent ? <><p data-availability="NOT_APPLICABLE">NOT_APPLICABLE · Parent 僅提供階層導航，成員屬於 Leaf。</p><Metadata values={{ asOf: topic.membersAvailability.asOf, reason: topic.membersAvailability.reason, reasonCode: topic.membersAvailability.reasonCode }} /></> : <>
      <Availability value={topic.membersAvailability} />
      {topic.membersAvailability.state === "AVAILABLE" && (!topic.members ? <p data-members-state="UNKNOWN">成員清單未提供，數量未知。</p> : topic.members.length === 0 ? <p data-members-state="EMPTY">此日期沒有有效成員。</p> : <><p>依後端 asOf {topic.asOf} 的有效成員；選擇股票可開啟相同市場身份的正式讀取頁。</p><Table><thead><tr><th>股票</th><th>市場</th><th>關係</th><th>有效起日</th><th>有效迄日</th></tr></thead><tbody>{topic.members.map((member, index) => <tr key={`${member.instrumentId}-${member.relationVersion}-${index}`}><td><Link href={`/stocks/${encodeURIComponent(member.code)}?${new URLSearchParams({ market: member.market })}`}>{member.code} {member.name ?? unknown}</Link></td><td>{member.market}</td><td>{member.relationType}</td><td>{member.validFrom}</td><td>{member.validTo ?? "未設結束日"}</td></tr>)}</tbody></Table></>)}
    </>}</Card>
    <Card><h2>目前正式 Snapshot</h2>{parent ? <><p data-availability="NOT_APPLICABLE">NOT_APPLICABLE · Parent 不適用正式 Snapshot。</p><Metadata values={{ asOf: snapshot.availability.asOf, reason: snapshot.availability.reason, reasonCode: snapshot.availability.reasonCode }} /></> : <><Availability value={snapshot.availability} />{formal ? <SnapshotTable snapshots={[formal]} /> : snapshot.availability.state === "AVAILABLE" && <p role="alert">目前 Snapshot 缺少正式資料或識別不一致，請重新載入題材。</p>}</>}</Card>
    <TopicSnapshotHistory topic={topic} retry={retry} />
    <Card><h2>來源與參考版本</h2>{Object.entries(topic.source).map(([key, value]) => <section key={key}><h3>{key}</h3>{value ? <Metadata values={value} /> : <p>{parent && key === "members" ? "NOT_APPLICABLE" : unknown}</p>}</section>)}</Card>
  </>;
}

export function CatalogContent({ resource, retry }: { resource: CatalogResource<CatalogTopic | CatalogPage>; retry: () => void }) {
  if (resource.state === "LOADING") return <Card><p role="status" data-state="LOADING">題材資料載入中…</p></Card>;
  if (resource.state !== "AVAILABLE") return <Card><div role={resource.state === "ERROR" ? "alert" : "status"} data-state={resource.state}><p>{resource.state === "ERROR" ? "讀取失敗" : "正式資料尚未提供"} · {resource.reason}</p>{resource.state === "ERROR" && <Button onClick={retry}>重試</Button>}</div></Card>;
  if (!("items" in resource.data)) return <TopicCatalogDetail topic={resource.data} retry={retry} />;
  const page = resource.data;
  return <Card><p>asOf {page.asOf} · 共 {page.total} 個題材</p>{page.items.length === 0 ? <EmptyState title="沒有題材" description="此日期或分頁沒有符合條件的題材。" /> : <Table><thead><tr><th>題材名稱</th><th>類型</th><th>發布狀態</th><th>階層</th></tr></thead><tbody>{page.items.map((topic) => <tr key={topic.topicId}><td><Link href={catalogHref(topic.slug, topic.asOf)}>{topic.name}</Link><p>asOf {topic.asOf}</p></td><td>{topic.kind}</td><td>{topic.status}<Availability value={topic.availability} /></td><td><Hierarchy topic={topic} /></td></tr>)}</tbody></Table>}</Card>;
}

export default function TopicCatalogPage({ slug, asOf }: { slug?: string; asOf?: string }) {
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [resource, setResource] = useState<CatalogResource<CatalogTopic | CatalogPage>>({ state: "LOADING", data: null });
  const [resolvedAsOf, setResolvedAsOf] = useState(asOf);
  const requestAsOf = useRef(asOf);
  useEffect(() => {
    const controller = new AbortController();
    setResource({ state: "LOADING", data: null });
    loadCatalog({ slug, asOf: requestAsOf.current, offset }, { signal: controller.signal }).then((next) => {
      if (!controller.signal.aborted) {
        setResource(next);
        if (next.state === "AVAILABLE") {
          requestAsOf.current = next.data.asOf;
          setResolvedAsOf(next.data.asOf);
        }
      }
    });
    return () => controller.abort();
  }, [slug, offset, revision]);
  const page = resource.state === "AVAILABLE" && "items" in resource.data ? resource.data : null;
  return <AppShell currentPath="/topics"><PageContainer eyebrow="題材探索" title={slug ? "題材詳情" : "題材"} description="依指定日期查看題材身份、階層與有效成員。">
    {slug && <p><Link href={catalogHref(null, resolvedAsOf)}>返回題材清單</Link></p>}
    <CatalogContent resource={resource} retry={() => setRevision((value) => value + 1)} />
    {page && <div className="tp-page-tools"><Button disabled={page.offset === 0} onClick={() => setOffset(Math.max(0, page.offset - page.limit))}>上一頁</Button><span>{page.items.length ? `第 ${page.offset + 1}–${page.offset + page.items.length} 筆 / ${page.total}` : `此頁 0 筆 / ${page.total}`}</span><Button disabled={page.offset + page.limit >= page.total} onClick={() => setOffset(page.offset + page.limit)}>下一頁</Button></div>}
  </PageContainer></AppShell>;
}
