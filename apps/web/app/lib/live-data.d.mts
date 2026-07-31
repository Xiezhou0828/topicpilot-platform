export type LiveDataState = "LOADING" | "LIVE" | "SNAPSHOT" | "STALE" | "ERROR" | "UNAVAILABLE";

export const LIVE_REFRESH_INTERVAL_MS: number;

export function evaluateLiveData(
  input: { source: string; dataDate: string | null; generatedAt: string | null; quoteUpdatedAt: string | null; quoteStatus?: string | null; latestTradingDate?: string | null; marketSession?: string | null; rowCount: number },
  today?: string,
): { state: Exclude<LiveDataState, "LOADING" | "ERROR">; delayedTradingDays: number | null; message: string };

export function isTaiwanMarketSession(date?: Date): boolean;
export function canShowTradeJudgement(dataState: LiveDataState, trigger: number | null, dataFreshness?: string | null): boolean;
export function evaluateTriggerState(
  input: { price: number | null; trigger: number | null; invalidation: number | null; distance: number | null },
  actionable: boolean,
): { label: string; detail: string; tone: "disabled" | "invalid" | "hit" | "near" | "waiting" };
