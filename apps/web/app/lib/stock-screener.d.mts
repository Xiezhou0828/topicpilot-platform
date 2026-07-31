import type { StockView } from "./types";
export type ScreenerMode = "AND" | "OR";
export type ScreenerRanges = { rsiMin?: number | null; rsiMax?: number | null; priceMin?: number | null; priceMax?: number | null };
export const SCREENER_GROUPS: Array<{ id: string; label: string; filters: Array<[string, string]> }>;
export function evaluateFilter(stock: StockView, id: string, ranges?: ScreenerRanges): boolean | null;
export function evaluateStockFilters(stock: StockView, activeIds: string[], mode?: ScreenerMode, ranges?: ScreenerRanges): { matches: boolean; missing: number };
