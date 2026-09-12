export type CommercialDataState = "LOADING" | "ERROR" | "AVAILABLE" | "PUBLISHED" | "EMPTY" | "PARTIAL" | "STALE" | "UNAVAILABLE" | "NOT_APPLICABLE";
export type CommercialStateResult = Readonly<{ state: CommercialDataState; reason: string | null; reasonCode: string | null; retryable: boolean }>;
export declare const COMMERCIAL_DATA_STATES: readonly CommercialDataState[];
export declare function commercialDataState(input?: { transport?: string | null; status?: string | null; publication?: string | null; freshness?: string | null; rowCount?: number; reason?: string | null; reasonCode?: string | null }): CommercialStateResult;
export declare function commercialStateLabel(state: CommercialDataState | string): string;
