import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import Link from "next/link";
import { formatNumber, formatPercent, valueTone } from "../lib/format";
import type { TopicTrendPoint } from "../lib/types";

export function MetricCard({ label, value, meta, tone = "default" }: { label: string; value: React.ReactNode; meta: string; tone?: string }) {
  return <article className={`metric-card ${tone}`}><span>{label}</span><strong>{value}</strong><small>{meta}</small></article>;
}

export function Delta({ value }: { value: number | null }) {
  const tone = valueTone(value);
  return (
    <span className={`delta ${tone}`}>
      {tone === "positive" ? <ArrowUpRight size={14} /> : tone === "negative" ? <ArrowDownRight size={14} /> : <Minus size={14} />}
      {formatPercent(value)}
    </span>
  );
}

export function Grade({ value }: { value: string | null }) {
  return <span className={`grade-badge grade-${(value ?? "na").toLowerCase()}`}>{value ?? "—"}</span>;
}

export function StatusPill({ value }: { value: string | null }) {
  const normalized = value?.toLowerCase() ?? "unknown";
  const tone = normalized.includes("強") || normalized.includes("升") || normalized === "healthy" || normalized === "complete"
    ? "good"
    : normalized.includes("待") || normalized.includes("盤") || normalized === "degraded"
      ? "warn"
      : normalized === "unavailable" ? "bad" : "neutral";
  return <span className={`status-pill ${tone}`}><i aria-hidden="true" />{value ?? "資料未提供"}</span>;
}

export function TrendBars({ points, label }: { points: TopicTrendPoint[]; label: string }) {
  const values = points.map((point) => point.score).filter((value): value is number => value !== null);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 0;
  return (
    <div className="trend-bars" role="img" aria-label={label}>
      {points.map((point) => {
        const height = point.score === null ? 8 : max === min ? 56 : 18 + ((point.score - min) / (max - min)) * 70;
        return <span key={point.date} className={point.score === null ? "missing" : ""} style={{ height: `${height}%` }} title={`${point.date}：${formatNumber(point.score)}`} />;
      })}
    </div>
  );
}

export function InlineLink({ href, children }: { href: string; children: React.ReactNode }) {
  return <Link className="inline-link" href={href}>{children}<ArrowUpRight size={14} aria-hidden="true" /></Link>;
}
