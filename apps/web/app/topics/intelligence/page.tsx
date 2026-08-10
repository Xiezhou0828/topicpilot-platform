"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppNav } from "../../components/AppNav";
import { EmptyState } from "../../components/EmptyState";
import { useSnapshot } from "../../lib/snapshot-store";
import { fetchTopicIntelligence, TopicIntelligenceApiError, type TopicIntelligenceResponse, type TopicIntelligenceTopic } from "../../lib/topic-intelligence";

const display = (n: number | null) => n === null ? "—" : String(n);

export default function TopicIntelligencePage() {
  const { bundle } = useSnapshot();
  const [data, setData] = useState<TopicIntelligenceResponse | null>(null);
  const [error, setError] = useState<TopicIntelligenceApiError | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const load = () => { setError(null); void fetchTopicIntelligence().then(setData).catch((e) => setError(e instanceof TopicIntelligenceApiError ? e : new TopicIntelligenceApiError(503, "Topic Intelligence is unavailable."))); };
  useEffect(() => {
    let active = true;
    void fetchTopicIntelligence()
      .then((result) => { if (active) setData(result); })
      .catch((e) => {
        if (active) setError(e instanceof TopicIntelligenceApiError ? e : new TopicIntelligenceApiError(503, "Topic Intelligence is unavailable."));
      });
    return () => { active = false; };
  }, []);
  const selected = useMemo(() => data?.topics.find((x) => x.topicId === selectedId) ?? data?.topics[0] ?? null, [data, selectedId]);
  const topicName = (topic: TopicIntelligenceTopic) => bundle.topics.find((x) => x.name === topic.topicId)?.name ?? topic.topicId;
  return <main><AppNav /><div className="appShell"><header className="topbar"><div><p className="eyebrow">Customer Topic Dashboard</p><h1>Topic Intelligence</h1></div><Link className="button" href="/topics">Existing topic view</Link></header>
    {error ? <section className="panel"><EmptyState title={error.status === 503 ? "Topic Intelligence service unavailable" : "Topic Intelligence could not be loaded"} description="No legacy snapshot score, browser calculation, or synthetic research candidate is shown as production intelligence." onRetry={load} actions={[{ href: "/topics", label: "View topic read model" }]} /></section> : !data ? <section className="panel"><p className="emptyText">Loading approved Topic Intelligence output…</p></section> : <>
      <section className="panel"><div className="sectionHead"><div><p className="eyebrow">Runtime status</p><h2>{data.status}</h2></div><span>{data.mode} · as of {data.asOf}</span></div><p className="muted">Scores and components are displayed only when supplied by the Topic Intelligence API. Eligibility and evidence quality remain separate from Market Strength.</p></section>
      <section className="topicSplit"><section className="panel childTopicPanel"><div className="sectionHead compact"><div><p className="eyebrow">Available topics</p><h2>{data.topics.length}</h2></div></div><div className="childTopicList">{data.topics.map((topic) => <button className={`childTopicRow ${selected?.topicId === topic.topicId ? "active" : ""}`} key={topic.topicId} onClick={() => setSelectedId(topic.topicId)} type="button"><span className={`grade grade${topic.grade ?? "NA"}`}>{topic.grade ?? "—"}</span><span className="childTopicBody"><span className="childTopicHead"><strong>{topicName(topic)}</strong><em>{display(topic.score)}</em></span><small>{topic.status} · eligibility {topic.eligibility}</small></span></button>)}</div></section>
        {selected ? <section className="topicDetailColumn"><section className="panel topicDetail"><p className="eyebrow">Topic detail</p><h2>{topicName(selected)}</h2><div className="miniStats"><article><span>Topic Score</span><strong>{display(selected.score)}</strong></article><article><span>Grade</span><strong>{selected.grade ?? "—"}</strong></article><article><span>Confidence</span><strong>{display(selected.confidence)}</strong></article><article><span>Eligibility</span><strong>{selected.eligibility}</strong></article></div></section><section className="panel"><div className="sectionHead compact"><div><p className="eyebrow">Explainable evidence</p><h2>Components</h2></div><span>{selected.evidence.aggregateStatus}</span></div><div className="miniStats">{selected.components.map((c) => <article key={c.name}><span>{c.name}</span><strong>{display(c.value)}</strong></article>)}</div><p className="muted">Breadth and Leadership are shown as API-provided components. No browser-side formula, normalization, threshold, or Leader Set derivation is applied.</p></section><section className="panel"><p className="eyebrow">Evidence quality</p><h2>Coverage and constituent context</h2><div className="checkList"><span>Ready features: {selected.evidence.quality.readyFeatureCount}</span><span>Insufficient features: {selected.evidence.quality.insufficientFeatureCount}</span><span>Invalid features: {selected.evidence.quality.invalidFeatureCount}</span><span>Coverage min / mean: {display(selected.evidence.quality.coverageMin)} / {display(selected.evidence.quality.coverageMean)}</span><span>{selected.evidence.qualityFlags.length ? `Quality flags: ${selected.evidence.qualityFlags.join(", ")}` : "No quality flags supplied"}</span></div><p className="muted">Constituents and core-member identity remain owned by the existing topic read model. This view does not invent CORE or leader membership from demo data.</p></section></section> : <section className="panel"><p className="emptyText">No Topic Intelligence topics are available.</p></section>}
      </section></>}</div></main>;
}
