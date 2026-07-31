import type { DataStatus, StockSummary, StrategySummary, TopicSummary } from "./types";

export function nullableNumber(value: unknown): number | null;
export function nullableString(value: unknown): string | null;
export function readValue(source: Record<string, unknown> | null | undefined, ...keys: string[]): unknown;
export function unwrapItems(payload: unknown): unknown[];
export function mapStock(raw: Record<string, unknown>): StockSummary;
export function mapTopic(raw: Record<string, unknown>): TopicSummary;
export function mapStrategy(raw: Record<string, unknown>): StrategySummary;
export function mapDataStatus(raw: Record<string, unknown>): DataStatus;
