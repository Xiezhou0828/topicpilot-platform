"use client"; /* eslint-disable @next/next/no-html-link-for-pages */

import { useEffect, useState } from "react";

const API = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
type Data = { counts: Record<string, number>; latest_import: { status: string; created_at: string } | null; alembic_revision: string | null; api_ready: boolean };

async function get<T>(path: string): Promise<T> { const res = await fetch(`${API}${path}`); if (!res.ok) throw new Error(`${res.status}`); return res.json(); }

export default function AdminPage() {
  const [data, setData] = useState<Data | null>(null); const [error, setError] = useState("");
  useEffect(() => { get<Data>("/api/v1/admin/dashboard").then(setData).catch(() => setError("無法連線到 Admin API")); }, []);
  const cards = [["markets", "Markets"], ["instruments", "Instruments"], ["topics", "Topics"], ["topic_hierarchy_relations", "Topic hierarchy"], ["instrument_topic_relations", "Instrument-topic"], ["legacy_import_runs", "Legacy imports"]];
  return <main className="adminShell"><header><div><p className="eyebrow">TOPICPILOT / OPERATOR SURFACE</p><h1>Admin / Data Explorer</h1><p className="muted">Read-only inspection of the V2 PostgreSQL master data.</p></div><span className="adminBadge">READ ONLY</span></header>
    {error && <div className="adminError">{error}</div>}
    <section className="adminGrid">{cards.map(([key, label]) => <article className="adminCard" key={key}><span>{label}</span><strong>{data?.counts[key] ?? "—"}</strong></article>)}</section>
    <section className="adminPanel"><div><p className="eyebrow">SYSTEM HEALTH</p><h2>Runtime readiness</h2></div><div className="healthRows"><div><span>API / database</span><b className={data?.api_ready ? "ok" : "bad"}>{data?.api_ready ? "READY" : "—"}</b></div><div><span>Current Alembic revision</span><b>{data?.alembic_revision || "—"}</b></div><div><span>Latest import</span><b>{data?.latest_import ? `${data.latest_import.status} · ${new Date(data.latest_import.created_at).toLocaleString()}` : "No run"}</b></div></div></section>
    <section className="adminPanel"><p className="eyebrow">EXPLORERS</p><h2>Read-only areas</h2><div className="adminLinks"><a href="/admin/schema">Schema / ERD →</a><a href="/admin/instruments">Instruments →</a><a href="/admin/topics">Topics →</a><a href="/admin/markets">Markets →</a><a href="/admin/imports">Legacy imports →</a></div></section>
  </main>;
}
