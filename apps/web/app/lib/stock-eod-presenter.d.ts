import type { StockEodRead } from "./stock-api";

export type StockQuotePresentation = {
  source: "INTRADAY_SOURCE" | "EOD_SOURCE" | "PREVIEW" | "UNAVAILABLE";
  price: number | null;
  change: number | null;
  changePct: number | null;
  volume: number | null;
  dataStatus: StockEodRead["dataStatus"] | "PREVIEW" | "UNAVAILABLE";
};

type StockQuoteInput = {
  isPreview?: boolean;
  updateMode?: string | null;
  price: number | null;
  changePct: number | null;
  volume?: number | null;
  eod?: StockEodRead | null;
};

export function isIntradayUpdateMode(updateMode: string | null | undefined): boolean;
export function selectStockQuote(item: StockQuoteInput): StockQuotePresentation;
