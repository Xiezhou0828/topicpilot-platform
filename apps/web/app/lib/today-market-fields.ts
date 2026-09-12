import type { components } from "./generated-api";

export type HomeMarketOverview = components["schemas"]["HomeMarketOverview"];
export type HomeMarketIndex = components["schemas"]["HomeMarketIndex"];
export type HomeMarketTurnover = components["schemas"]["HomeMarketTurnover"];
export type HomeMarketDistribution = components["schemas"]["HomeMarketDistribution"];

export type MarketFactState = "AVAILABLE" | "PARTIAL" | "UNAVAILABLE";

const AVAILABLE_STATUSES = new Set(["AVAILABLE", "PUBLISHED", "FORMAL"]);

function normalizedStatus(status: string | null | undefined): string {
  return typeof status === "string" ? status.trim().toUpperCase() : "";
}

function finiteNumber(value: number | null | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

export function marketFactIsAvailable(
  status: string | null | undefined,
  value: number | null | undefined,
): boolean {
  return AVAILABLE_STATUSES.has(normalizedStatus(status)) && finiteNumber(value);
}

export function marketFactState(
  records: ReadonlyArray<{ status: string; value: number | null }>,
): MarketFactState {
  if (records.length === 0) return "UNAVAILABLE";
  const available = records.filter((record) => marketFactIsAvailable(record.status, record.value)).length;
  if (available === 0) return "UNAVAILABLE";
  return available === records.length ? "AVAILABLE" : "PARTIAL";
}

export function marketIndices(overview: HomeMarketOverview | null): HomeMarketIndex[] {
  return overview && Array.isArray(overview.indices)
    ? overview.indices.filter((value): value is HomeMarketIndex => Boolean(
      value
        && typeof value.market === "string"
        && typeof value.indexCode === "string"
        && typeof value.indexName === "string"
        && (value.tradingDate === null || typeof value.tradingDate === "string")
        && (value.asOf === null || typeof value.asOf === "string")
        && typeof value.status === "string",
    ))
    : [];
}

export function marketTurnover(overview: HomeMarketOverview | null): HomeMarketTurnover[] {
  return overview && Array.isArray(overview.turnover)
    ? overview.turnover.filter((value): value is HomeMarketTurnover => Boolean(
      value
        && typeof value.market === "string"
        && (value.tradingDate === null || typeof value.tradingDate === "string")
        && (value.asOf === null || typeof value.asOf === "string")
        && (value.currency === null || typeof value.currency === "string")
        && (value.unit === null || typeof value.unit === "string")
        && (value.scale === null || (typeof value.scale === "number" && Number.isFinite(value.scale)))
        && typeof value.status === "string",
    ))
    : [];
}

export function marketDistribution(overview: HomeMarketOverview | null): HomeMarketDistribution | null {
  const value = overview?.distribution;
  if (!value
    || typeof value.market !== "string"
    || typeof value.status !== "string"
    || !finiteNumber(value.eligible)
    || !finiteNumber(value.excluded)
    || !Array.isArray(value.buckets)
    || !value.buckets.every((bucket) => Boolean(
      bucket
        && typeof bucket.key === "string"
        && typeof bucket.label === "string"
        && finiteNumber(bucket.count),
    ))) {
    return null;
  }
  return value;
}

export function formatMarketNumber(value: number | null | undefined): string {
  return finiteNumber(value)
    ? new Intl.NumberFormat("zh-TW", { maximumFractionDigits: 2 }).format(value)
    : "尚未提供";
}

export function formatSignedMarketNumber(value: number | null | undefined): string {
  if (!finiteNumber(value)) return "尚未提供";
  const formatted = formatMarketNumber(Math.abs(value));
  return value > 0 ? `+${formatted}` : value < 0 ? `-${formatted}` : formatted;
}

export function formatMarketPercent(value: number | null | undefined): string {
  return finiteNumber(value) ? `${formatSignedMarketNumber(value)}%` : "尚未提供";
}

export function formatMarketDate(value: string | null | undefined): string {
  return typeof value === "string" && value.trim().length > 0 ? value : "尚未提供";
}

export function formatMarketAsOf(value: string | null | undefined): string {
  if (typeof value !== "string" || value.trim().length === 0) return "尚未提供";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("zh-TW", {
    timeZone: "Asia/Taipei",
    dateStyle: "medium",
    timeStyle: "short",
    hour12: false,
  }).format(parsed);
}

export function formatTurnoverUnit(fact: HomeMarketTurnover): string {
  const parts = [fact.currency, fact.unit].filter(
    (value): value is string => typeof value === "string" && value.trim().length > 0,
  );
  if (fact.scale !== null && typeof fact.scale === "number" && Number.isFinite(fact.scale)) {
    parts.push(`scale ${fact.scale}`);
  }
  return parts.length > 0 ? parts.join(" · ") : "單位尚未提供";
}

export function marketDataStatusLabel(value: string | null | undefined): string {
  const status = normalizedStatus(value);
  if (status === "AVAILABLE") return "資料可用";
  if (status === "PARTIAL") return "部分資料";
  return "資料尚未提供";
}
