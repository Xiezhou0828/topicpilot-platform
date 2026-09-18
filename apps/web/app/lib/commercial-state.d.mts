export declare const COMMERCIAL_DATA_STATES: readonly string[];
export declare function commercialDataState(options?: Record<string, unknown>): { state: string; reason: string | null; reasonCode: string | null; retryable: boolean };
export declare function commercialStateLabel(state: string): string;
