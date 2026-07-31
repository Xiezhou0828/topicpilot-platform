// 型別宣告：對應 trading-day.mjs（純函式交易日過期判斷）。
export const TAIPEI_TIMEZONE: string;
export const STALE_THRESHOLDS: { quoteTradingDays: number; institutionalTradingDays: number };

export function toISO(date: Date): string;
export function parseDateOnly(input: unknown): Date | null;
export function isWeekend(date: Date): boolean;
export function isTradingDay(date: Date, holidays?: Set<string>): boolean;
export function latestTradingDayOnOrBefore(date: Date, holidays?: Set<string>): Date;
export function tradingDaysBetween(from: Date, to: Date, holidays?: Set<string>): number;

export type StalenessResult = {
  valid: boolean;
  stale: boolean;
  gapTradingDays: number | null;
  date: string | null;
  latestTradingDay: string | null;
};
export function evaluateStaleness(args: {
  date: unknown;
  today: unknown;
  thresholdDays: number;
  holidays?: Set<string>;
}): StalenessResult;

export function taipeiToday(now?: Date): string;

export type FreshnessDates = {
  dataDate?: string | null;
  institutionalAsOf?: string | null;
  tdccAsOf?: string | null;
  fundamentalYm?: string | null;
};
export type FreshnessItem = {
  key: string;
  label: string;
  date: string | null;
  stale: boolean;
  reason: string | null;
  note: string | null;
};
export function evaluateFreshness(
  freshness: FreshnessDates | null | undefined,
  today: string,
  holidays?: Set<string>,
): { anyStale: boolean; items: FreshnessItem[] };
