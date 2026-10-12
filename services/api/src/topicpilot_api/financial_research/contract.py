from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FinancialApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


DataStatus = Literal[
    "AVAILABLE",
    "MISSING",
    "NOT_APPLICABLE",
    "INVALID",
    "STALE",
    "PENDING_REVIEW",
    "BLOCKED_RIGHTS",
]
SourceAdapterStatus = Literal[
    "SUCCESS",
    "SOURCE_UNAVAILABLE",
    "ACCESS_DENIED",
    "RATE_LIMITED",
    "PARSER_FAILED",
    "EMPTY_RESULT",
    "SCHEMA_CHANGED",
    "PERIOD_MISMATCH",
    "RIGHTS_UNVERIFIED",
]
StatementType = Literal[
    "income_statement",
    "balance_sheet",
    "cash_flow",
    "equity_statement",
    "kpi_schedule",
    "segment",
    "share_count",
]
PeriodType = Literal[
    "annual",
    "quarterly",
    "monthly",
    "ytd",
    "ltm",
    "forecast",
    "budget",
    "pro_forma",
    "scenario",
]
EvidenceLabel = Literal[
    "fact_source_reported",
    "fact_provider_standardized",
    "derived_calculation",
    "issuer_management_claim",
    "management_adjusted",
    "analyst_adjusted",
    "analyst_interpretation",
    "assumption_user_provided",
    "assumption_inferred",
    "estimate_consensus",
    "stale_source",
    "contradicted_source",
    "missing_required_source",
    "unknown",
]


class FinancialSource(FinancialApiModel):
    source_id: str = Field(min_length=1)
    source_type: str
    owner_or_provider: str
    source_url: str | None = None
    retrieval_timestamp: datetime | None = None
    data_usage_rights: str = "UNVERIFIED"
    redistribution_rights: str = "UNVERIFIED"
    license_review_status: str = "PENDING_REVIEW"


class FinancialFiling(FinancialApiModel):
    filing_id: str = Field(min_length=1)
    company_id: str
    ticker: str
    fiscal_year: int | None = None
    fiscal_quarter: int | None = Field(default=None, ge=1, le=4)
    reporting_period_start: date | None = None
    reporting_period_end: date | None = None
    filing_date: date | None = None
    report_type: str
    consolidation_scope: Literal["consolidated", "separate", "segment", "unknown"]
    filing_version: str = "ORIGINAL"
    amendment_status: str = "ORIGINAL"
    raw_artifact_hash: str | None = None
    source_id: str


class RawFinancialRecord(FinancialApiModel):
    company_id: str
    ticker: str
    source_id: str
    filing_id: str
    period_end: date | None = None
    period_label: str
    period_type: PeriodType
    fiscal_year: int | None = None
    fiscal_quarter: int | None = Field(default=None, ge=1, le=4)
    statement: StatementType
    line_item_original: str
    line_item_standard: str
    numeric_value: Decimal | None = None
    unit: str
    currency: str | None = None
    duration_or_instant: Literal["DURATION", "INSTANT"]
    ytd_or_standalone: Literal["YTD", "STANDALONE", "NOT_APPLICABLE"]
    consolidation_scope: Literal["consolidated", "separate", "segment", "unknown"]
    source_location: str | None = None
    evidence_label: EvidenceLabel = "fact_source_reported"
    confidence: Literal["high", "medium", "low"] = "high"


class FinancialFact(FinancialApiModel):
    fact_id: str
    company_id: str
    ticker: str
    source_id: str
    filing_id: str
    period_end: date | None = None
    period_label: str
    period_type: PeriodType
    fiscal_year: int | None = None
    fiscal_quarter: int | None = None
    statement: StatementType
    line_item_original: str
    line_item_standard: str
    source_value: Decimal | None = None
    normalized_value: Decimal | None = None
    source_unit: str
    normalized_unit: str
    currency: str | None = None
    duration_or_instant: Literal["DURATION", "INSTANT"]
    ytd_or_standalone: Literal["YTD", "STANDALONE", "NOT_APPLICABLE"]
    consolidation_scope: Literal["consolidated", "separate", "segment", "unknown"]
    source_location: str | None = None
    evidence_label: EvidenceLabel
    confidence: Literal["high", "medium", "low"]
    data_quality_status: DataStatus
    normalization_method: str
    normalization_note: str | None = None


class FinancialShareData(FinancialApiModel):
    ticker: str
    period_end: date | None = None
    issued_shares: Decimal | None = None
    outstanding_shares: Decimal | None = None
    weighted_average_basic_shares: Decimal | None = None
    weighted_average_diluted_shares: Decimal | None = None
    treasury_shares: Decimal | None = None
    capital_change_note: str | None = None
    retrospective_adjustment: str | None = None
    source_id: str | None = None
    status: DataStatus = "PENDING_REVIEW"


EpsBridgeStatus = Literal[
    "SOURCE_NOTE_MISSING",
    "SOURCE_NOTE_NOT_FOUND",
    "SOURCE_NOTE_AVAILABLE_NOT_INGESTED",
    "SHARE_UNIT_MISMATCH",
    "PERIOD_MISMATCH",
    "BRIDGE_INPUT_INCOMPLETE",
    "DERIVED_SHARES_PENDING_VALIDATION",
    "RECOMPUTED_MATCH",
    "RECOMPUTED_MISMATCH",
    "NOT_APPLICABLE",
]

EpsNoteExtractionStatus = Literal[
    "EXTRACTED",
    "SOURCE_UNAVAILABLE",
    "RETRIEVAL_BLOCKED",
    "PARSE_FAILED",
    "NO_EPS_NOTE",
    "MANUAL_REVIEW_REQUIRED",
]
EpsExtractionMethod = Literal["PDF_TEXT", "PDF_TABLE", "STRUCTURED", "MANUAL_REVIEW"]
EpsFieldDataStatus = Literal["DIRECT", "DERIVED", "PENDING_VALIDATION"]


class EpsPeriodContract(FinancialApiModel):
    """Normalized duration contract used by EPS notes and bridge matching."""

    period_label: str
    period_start: date | None = None
    period_end: date | None = None
    period_type: Literal["annual", "quarterly", "half_year", "nine_month", "ytd"]
    fiscal_year: int | None = None
    fiscal_quarter: int | None = Field(default=None, ge=1, le=4)
    ytd_or_standalone: Literal["YTD", "STANDALONE", "NOT_APPLICABLE"]
    comparative_of: str | None = None
    retrospective_adjustment: str | None = None


class EpsNoteField(FinancialApiModel):
    """One directly extracted or explicitly derived EPS-note field."""

    ticker: str
    period: EpsPeriodContract
    line_item_standard: str
    value: Decimal
    source_value: Decimal | None = None
    source_unit: str
    normalized_value: Decimal
    normalized_unit: str
    currency: str | None = None
    source_id: str
    source_url: str | None = None
    source_page: str | None = None
    raw_field: str
    raw_text: str
    extraction_method: EpsExtractionMethod
    data_status: EpsFieldDataStatus = "DIRECT"


class EpsNoteExtractionResult(FinancialApiModel):
    """Auditable result of parsing an official EPS note or structured record."""

    ticker: str
    source_id: str
    source_url: str | None = None
    status: EpsNoteExtractionStatus
    parser_id: str
    periods: list[EpsPeriodContract] = Field(default_factory=list)
    fields: list[EpsNoteField] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    raw_artifact_hash: str | None = None


class FinancialEpsBridgeEvidence(FinancialApiModel):
    source_id: str
    source_url: str | None = None
    source_page: str | None = None
    raw_field: str | None = None
    raw_text: str | None = None
    extraction_method: str | None = None
    data_status: str | None = None


class FinancialEpsBridgeRecord(FinancialApiModel):
    """A period-scoped, auditable EPS recomputation result.

    This is a validation record, not a replacement for the issuer-reported EPS.
    All monetary values use the same normalized base unit as the underlying
    facts; share counts are explicit so a thousand-share/unit mistake cannot be
    silently hidden.
    """

    ticker: str
    period_label: str
    period_type: Literal["annual", "quarterly", "half_year", "nine_month", "ytd"] | None = None
    period_end: date | None = None
    consolidation_scope: str = "consolidated"
    parent_net_income: Decimal | None = None
    weighted_average_basic_shares: Decimal | None = None
    weighted_average_diluted_shares: Decimal | None = None
    reported_basic_eps: Decimal | None = None
    reported_diluted_eps: Decimal | None = None
    recomputed_basic_eps: Decimal | None = None
    recomputed_diluted_eps: Decimal | None = None
    basic_difference: Decimal | None = None
    diluted_difference: Decimal | None = None
    status: EpsBridgeStatus
    source_ids: list[str] = Field(default_factory=list)
    source_locations: list[str] = Field(default_factory=list)
    evidence: list[FinancialEpsBridgeEvidence] = Field(default_factory=list)
    source_note_status: EpsNoteExtractionStatus | None = None
    source_pages: list[str] = Field(default_factory=list)
    raw_fields: list[str] = Field(default_factory=list)
    note: str


class FinancialEpsBridgeResponse(FinancialApiModel):
    ticker: str
    status: DataStatus
    records: list[FinancialEpsBridgeRecord] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    source_rights_status: str = "UNVERIFIED"


class ForecastState(FinancialApiModel):
    state: Literal["DRAFT", "CALCULATED", "VALIDATED", "REVIEW_PENDING", "APPROVED"]


class ForecastAssumption(FinancialApiModel):
    key: str
    value: Decimal | None = None
    unit: str
    source: Literal["owner_input", "issuer_guidance", "derived_history", "consensus"]
    status: Literal["REQUIRED", "AVAILABLE", "BLOCKED"] = "REQUIRED"


class ForecastOutput(FinancialApiModel):
    ticker: str
    scenario: Literal["BASE", "BEAR", "BULL"]
    period_label: str
    revenue: Decimal | None = None
    gross_profit: Decimal | None = None
    operating_income: Decimal | None = None
    net_income: Decimal | None = None
    basic_eps: Decimal | None = None
    status: Literal["AVAILABLE", "BLOCKED"]
    note: str


class ForecastRun(FinancialApiModel):
    run_id: str
    ticker: str
    state: Literal["DRAFT", "CALCULATED", "VALIDATED", "REVIEW_PENDING", "APPROVED"]
    assumptions: list[ForecastAssumption] = Field(default_factory=list)
    outputs: list[ForecastOutput] = Field(default_factory=list)
    missing_prerequisites: list[str] = Field(default_factory=list)


class ResearchEvidence(FinancialApiModel):
    evidence_id: str
    source_id: str
    source_url: str | None = None
    source_title: str
    published_at: date | None = None
    retrieved_at: datetime | None = None
    claim_scope: str
    status: Literal["VERIFIED", "PENDING_REVIEW", "CONTRADICTED", "UNAVAILABLE"]
    rights_status: Literal["APPROVED", "UNVERIFIED", "BLOCKED"] = "UNVERIFIED"


class ResearchClaim(FinancialApiModel):
    claim_id: str
    text_zh_tw: str
    evidence_ids: list[str] = Field(default_factory=list)
    review_status: Literal["DRAFT", "REVIEW_PENDING", "APPROVED", "REJECTED"] = "DRAFT"
    is_formal_topic_authority: bool = False


class ResearchVersion(FinancialApiModel):
    research_id: str
    ticker: str
    version: str
    status: Literal["DRAFT", "REVIEW_PENDING", "APPROVED", "PUBLISHED", "UNPUBLISHED"]
    created_at: datetime
    claims: list[ResearchClaim] = Field(default_factory=list)
    evidence: list[ResearchEvidence] = Field(default_factory=list)


class PublicSafeCompanyResearchProjection(FinancialApiModel):
    """Public-safe shape: approved evidence only and no valuation outputs."""

    ticker: str
    version: str
    publication_status: Literal["PUBLISHED", "UNPUBLISHED", "NOT_CONNECTED"]
    overview_zh_tw: str | None = None
    approved_claims: list[ResearchClaim] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class FinancialValidationReceipt(FinancialApiModel):
    validation_run_id: str
    source_version: str
    input_hash: str | None = None
    validation_rule: str
    validation_result: Literal["PASS", "FAIL", "PARTIAL", "NOT_TESTABLE"]
    error_reason: str | None = None
    missing_data_status: DataStatus | None = None
    run_timestamp: datetime
    expected_value: Decimal | None = None
    observed_value: Decimal | None = None
    variance: Decimal | None = None


class NormalizationIssue(FinancialApiModel):
    issue_id: str
    source_id: str | None = None
    ticker: str | None = None
    issue_type: str
    message: str
    blocking: bool = True


class NormalizationResult(FinancialApiModel):
    source_index: list[FinancialSource] = Field(default_factory=list)
    filings: list[FinancialFiling] = Field(default_factory=list)
    facts: list[FinancialFact] = Field(default_factory=list)
    issues: list[NormalizationIssue] = Field(default_factory=list)


class FinancialPeriodCoverage(FinancialApiModel):
    period_label: str
    period_end: date | None = None
    period_type: PeriodType
    statements: list[StatementType] = Field(default_factory=list)


class FinancialCoverageResponse(FinancialApiModel):
    ticker: str
    status: DataStatus
    available_periods: list[FinancialPeriodCoverage] = Field(default_factory=list)
    statement_coverage: dict[str, list[str]] = Field(default_factory=dict)
    eps_coverage: list[str] = Field(default_factory=list)
    share_count_coverage: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    amendment_status: list[str] = Field(default_factory=list)
    source_rights_status: str = "UNVERIFIED"
    source_ids: list[str] = Field(default_factory=list)


class FinancialSummaryMetric(FinancialApiModel):
    metric: str
    statement: str | None = None
    period_label: str
    period_type: PeriodType | None = None
    period_end: date | None = None
    value: Decimal | None = None
    unit: str
    currency: str | None = None
    source_id: str | None = None
    source_location: str | None = None
    evidence_label: EvidenceLabel
    status: DataStatus
    validation_status: str = "NOT_ASSESSED"
    validation_note: str | None = None


class FinancialSummaryResponse(FinancialApiModel):
    ticker: str
    status: DataStatus
    metrics: list[FinancialSummaryMetric] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    source_rights_status: str = "UNVERIFIED"


class FinancialStatementLine(FinancialApiModel):
    line_item: str
    period_label: str
    period_type: PeriodType | None = None
    period_end: date | None = None
    value: Decimal | None = None
    unit: str
    currency: str | None = None
    source_id: str | None = None
    source_location: str | None = None
    status: DataStatus
    validation_status: str = "NOT_ASSESSED"
    validation_note: str | None = None


class FinancialStatementResponse(FinancialApiModel):
    ticker: str
    status: DataStatus
    annual: list[FinancialStatementLine] = Field(default_factory=list)
    quarterly: list[FinancialStatementLine] = Field(default_factory=list)
    ytd: list[FinancialStatementLine] = Field(default_factory=list)
    source_rights_status: str = "UNVERIFIED"
    missing_fields: list[str] = Field(default_factory=list)


class FinancialResearchStatusResponse(FinancialApiModel):
    ticker: str
    historical_data_readiness: Literal["READY", "PARTIAL", "BLOCKED"]
    model_readiness: Literal["READY", "PARTIAL", "BLOCKED"]
    forecast_available: bool
    publication_status: Literal["PUBLISHED", "UNPUBLISHED", "NOT_PUBLISHED", "BLOCKED"]
    source_rights_status: str
    missing_prerequisites: list[str] = Field(default_factory=list)
    quality_status: str
    as_of: date | None = None


class SourceAdapterResult(FinancialApiModel):
    adapter_id: str
    status: SourceAdapterStatus
    source: FinancialSource | None = None
    filing: FinancialFiling | None = None
    raw_artifact_hash: str | None = None
    records: list[RawFinancialRecord] = Field(default_factory=list)
    error_reason: str | None = None
    live_intake: bool = False
    rights_checked: bool = False


class ApiUnavailableDetail(FinancialApiModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
