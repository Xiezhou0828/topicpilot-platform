import { getFormalApiBaseUrl } from "./stock-api";

export type FinancialApiStatus = "AVAILABLE" | "MISSING" | "BLOCKED_RIGHTS" | "UNAVAILABLE" | "ERROR";

export type FinancialResearchStatusRead = {
  ticker: string;
  historical_data_readiness: "READY" | "PARTIAL" | "BLOCKED";
  model_readiness: "READY" | "PARTIAL" | "BLOCKED";
  forecast_available: boolean;
  publication_status: "PUBLISHED" | "UNPUBLISHED" | "NOT_PUBLISHED" | "BLOCKED";
  source_rights_status: string;
  missing_prerequisites: string[];
  quality_status: string;
  as_of: string | null;
};

export type FinancialSummaryRead = {
  ticker: string;
  status: FinancialApiStatus;
  metrics: Array<{
    metric: string;
    statement: string | null;
    period_label: string;
    period_type: string | null;
    period_end: string | null;
    value: string | number | null;
    unit: string;
    currency: string | null;
    source_id: string | null;
    source_location: string | null;
    evidence_label: string;
    status: string;
    validation_status: string;
    validation_note: string | null;
  }>;
  missing_fields: string[];
  source_rights_status: string;
};

export type FinancialCoverageRead = {
  ticker: string;
  status: string;
  available_periods: Array<{
    period_label: string;
    period_end: string | null;
    period_type: string;
    statements: string[];
  }>;
  statement_coverage: Record<string, string[]>;
  eps_coverage: string[];
  share_count_coverage: string[];
  missing_fields: string[];
  amendment_status: string[];
  source_rights_status: string;
  source_ids: string[];
};

export type FinancialStatementLineRead = {
  line_item: string;
  period_label: string;
  period_type: string | null;
  period_end: string | null;
  value: string | number | null;
  unit: string;
  currency: string | null;
  source_id: string | null;
  source_location: string | null;
  status: string;
  validation_status: string;
  validation_note: string | null;
};

export type FinancialStatementsRead = {
  ticker: string;
  status: string;
  annual: FinancialStatementLineRead[];
  quarterly: FinancialStatementLineRead[];
  ytd: FinancialStatementLineRead[];
  source_rights_status: string;
  missing_fields: string[];
};

export type FinancialEpsBridgeRecordRead = {
  ticker: string;
  period_label: string;
  period_type: "annual" | "quarterly" | "half_year" | "nine_month" | "ytd" | null;
  period_end: string | null;
  parent_net_income: string | number | null;
  weighted_average_basic_shares: string | number | null;
  weighted_average_diluted_shares: string | number | null;
  reported_basic_eps: string | number | null;
  reported_diluted_eps: string | number | null;
  recomputed_basic_eps: string | number | null;
  recomputed_diluted_eps: string | number | null;
  basic_difference: string | number | null;
  diluted_difference: string | number | null;
  status: string;
  source_ids: string[];
  source_locations: string[];
  evidence: Array<{
    source_id: string;
    source_url: string | null;
    source_page: string | null;
    raw_field: string | null;
    raw_text: string | null;
    extraction_method: string | null;
    data_status: string | null;
  }>;
  source_note_status: string | null;
  source_pages: string[];
  raw_fields: string[];
  note: string;
};

export type FinancialEpsBridgeRead = {
  ticker: string;
  status: FinancialApiStatus | "PENDING_REVIEW";
  records: FinancialEpsBridgeRecordRead[];
  missing_fields: string[];
  source_rights_status: string;
};

export type FinancialResearchReadout = {
  source: "api" | "unavailable";
  status: FinancialApiStatus;
  summary: FinancialSummaryRead | null;
  coverage: FinancialCoverageRead | null;
  statements: FinancialStatementsRead | null;
  epsBridge: FinancialEpsBridgeRead | null;
  readiness: FinancialResearchStatusRead | null;
  error: string | null;
};

export async function fetchFinancialResearchReadout(
  symbol: string,
  options: { signal?: AbortSignal } = {},
): Promise<FinancialResearchReadout> {
  const previewFinancialBase = process.env.NEXT_PUBLIC_FINANCIAL_RESEARCH_API_BASE_URL?.trim().replace(/\/+$/, "");
  const base = previewFinancialBase || getFormalApiBaseUrl();
  if (!base) {
    return {
      source: "unavailable",
      status: "UNAVAILABLE",
      summary: null,
      coverage: null,
      statements: null,
      epsBridge: null,
      readiness: null,
      error: "正式財務唯讀 API 尚未設定。",
    };
  }

  try {
    const encoded = encodeURIComponent(symbol);
    const [summaryResponse, coverageResponse, statementsResponse, statusResponse, epsBridgeResponse] = await Promise.all([
      fetch(`${base}/api/v2/stocks/${encoded}/financial-summary`, { cache: "no-store", signal: options.signal }),
      fetch(`${base}/api/v2/stocks/${encoded}/financial-coverage`, { cache: "no-store", signal: options.signal }),
      fetch(`${base}/api/v2/stocks/${encoded}/financial-statements`, { cache: "no-store", signal: options.signal }),
      fetch(`${base}/api/v2/stocks/${encoded}/financial-research-status`, { cache: "no-store", signal: options.signal }),
      fetch(`${base}/api/v2/stocks/${encoded}/eps-bridge`, { cache: "no-store", signal: options.signal }),
    ]);
    if (!summaryResponse.ok || !coverageResponse.ok || !statementsResponse.ok || !statusResponse.ok || !epsBridgeResponse.ok) {
      throw new Error(`正式財務唯讀 API returned HTTP ${summaryResponse.status}/${coverageResponse.status}/${statementsResponse.status}/${statusResponse.status}/${epsBridgeResponse.status}`);
    }
    const summary = await summaryResponse.json() as FinancialSummaryRead;
    const coverage = await coverageResponse.json() as FinancialCoverageRead;
    const statements = await statementsResponse.json() as FinancialStatementsRead;
    const readiness = await statusResponse.json() as FinancialResearchStatusRead;
    const epsBridge = await epsBridgeResponse.json() as FinancialEpsBridgeRead;
    return {
      source: "api",
      status: summary.status,
      summary,
      coverage,
      statements,
      epsBridge,
      readiness,
      error: null,
    };
  } catch (error) {
    if (options.signal?.aborted) {
      return { source: "unavailable", status: "UNAVAILABLE", summary: null, coverage: null, statements: null, epsBridge: null, readiness: null, error: "財務唯讀 API 請求已取消。" };
    }
    return {
      source: "unavailable",
      status: "UNAVAILABLE",
      summary: null,
      coverage: null,
      statements: null,
      epsBridge: null,
      readiness: null,
      error: error instanceof Error ? error.message : "財務唯讀 API 無法取得。",
    };
  }
}
