import type { components } from "./generated-api";

export type HomeMarketOverview = components["schemas"]["HomeMarketOverview"];
export type HomeMarketIndex = components["schemas"]["HomeMarketIndex"];
export type HomeMarketTurnover = components["schemas"]["HomeMarketTurnover"];
export type HomeMarketTurnoverPreviousSession = components["schemas"]["HomeMarketTurnoverPreviousSession"];
export type HomeMarketDistribution = components["schemas"]["HomeMarketDistribution"];

export type MarketDistributionDisplayMeta = {
  scope: "COVERED_STOCKS" | "WHOLE_MARKET";
  title: string;
  completeCount: number;
  universeCount: number | null;
  coveragePct: number | null;
  excludedCount: number;
  denominator: string;
};

export type MarketFactState = "AVAILABLE" | "PARTIAL" | "UNAVAILABLE";

const AVAILABLE_STATUSES = new Set(["AVAILABLE", "PUBLISHED", "FORMAL"]);

function normalizedStatus(status: string | null | undefined): string {
  return typeof status === "string" ? status.trim().toUpperCase() : "";
}

function finiteNumber(value: unknown): value is number {
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

export function marketIndexDisplayName(index: HomeMarketIndex): string {
  if (index.market === "TPE") return "加權指數";
  if (index.market === "TWO") return "櫃買指數";
  return index.indexName;
}

export function formatTurnoverHundredMillion(fact: HomeMarketTurnover): string {
  return formatTurnoverHundredMillionValue(fact.value, fact.currency, fact.unit, fact.status);
}

export function formatTurnoverHundredMillionValue(
  value: number | null | undefined,
  currency: string | null | undefined,
  unit: string | null | undefined,
  status: string | null | undefined,
): string {
  if (!marketFactIsAvailable(status, value) || !finiteNumber(value)) return "尚未提供";
  if (currency?.trim().toUpperCase() !== "TWD" || unit?.trim().toUpperCase() !== "TWD") return "單位尚未確認";
  return `${formatMarketNumber(value / 100_000_000)} 億`;
}

export function marketBreadthNet(
  health: HomeMarketOverview["marketHealth"],
): number | null {
  if (!health || !finiteNumber(health.advance) || !finiteNumber(health.decline)) return null;
  return health.advance - health.decline;
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

export function marketDistributionDisplayMeta(
  distribution: HomeMarketDistribution | null,
): MarketDistributionDisplayMeta {
  const coverage = distribution?.coverage ?? {};
  const wholeMarket = coverage.scope === "WHOLE_MARKET";
  const universeCount = finiteNumber(coverage.eligibleUniverse) ? coverage.eligibleUniverse : null;
  const completeCount = finiteNumber(coverage.observedComplete)
    ? coverage.observedComplete
    : distribution?.eligible ?? 0;
  const coveragePct = finiteNumber(coverage.coveragePct)
    ? coverage.coveragePct
    : universeCount !== null && universeCount > 0
      ? completeCount / universeCount * 100
      : null;
  return {
    scope: wholeMarket ? "WHOLE_MARKET" : "COVERED_STOCKS",
    title: wholeMarket ? "漲跌幅分布（上市＋上櫃全市場）" : "已覆蓋股票漲跌幅分布",
    completeCount,
    universeCount,
    coveragePct,
    excludedCount: finiteNumber(coverage.excludedCount)
      ? coverage.excludedCount
      : distribution?.excluded ?? 0,
    denominator: typeof coverage.distributionDenominator === "string"
      ? coverage.distributionDenominator
      : "COMPLETE_CLOSE_PREVIOUS_CLOSE",
  };
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

export function formatInstitutionalAmount(value: number | null | undefined): string {
  if (!finiteNumber(value)) return "尚未提供";
  const sign = value < 0 ? "-" : "";
  const absolute = Math.abs(value);
  if (absolute >= 100_000_000) {
    let billions = Math.floor(absolute / 100_000_000);
    let tenThousands = Math.round((absolute - billions * 100_000_000) / 10_000);
    if (tenThousands >= 10_000) {
      billions += 1;
      tenThousands = 0;
    }
    return tenThousands > 0
      ? `${sign}${formatMarketNumber(billions)} 億 ${formatMarketNumber(tenThousands)} 萬`
      : `${sign}${formatMarketNumber(billions)} 億`;
  }
  if (absolute >= 10_000) return `${sign}${formatMarketNumber(absolute / 10_000)} 萬`;
  return `${sign}${formatMarketNumber(absolute)} 元`;
}

export function formatMarketPercent(value: number | null | undefined): string {
  return finiteNumber(value) ? `${formatSignedMarketNumber(value)}%` : "尚未提供";
}

export function formatMarketShare(value: number | null | undefined): string {
  return finiteNumber(value) ? `${value.toFixed(1)}%` : "尚未提供";
}

export function formatMarketDistributionLabel(key: string, fallback: string): string {
  return {
    PCT_GE_10: "漲停",
    PCT_7_TO_10: "+7~10%",
    PCT_3_TO_7: "+3~7%",
    PCT_0_TO_3: "0~3%",
    FLAT: "平盤",
    PCT_NEG_0_TO_3: "-3~0%",
    PCT_NEG_3_TO_7: "-7~-3%",
    PCT_NEG_7_TO_10: "-10~-7%",
    PCT_LE_NEG_10: "跌停",
  }[key] ?? fallback;
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
