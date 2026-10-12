from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256

from .contract import (
    FinancialFact,
    NormalizationIssue,
    NormalizationResult,
    RawFinancialRecord,
)

_UNIT_SCALE: dict[str, Decimal] = {
    "TWD": Decimal("1"),
    "TWD_ONES": Decimal("1"),
    "元": Decimal("1"),
    "TWD_THOUSANDS": Decimal("1000"),
    # Official MOPS legacy tables label monetary values as TWD_1000 in the
    # adapter contract. Keep this explicit so live historical records do not
    # fall into UNKNOWN_UNIT during normalization.
    "TWD_1000": Decimal("1000"),
    "千元": Decimal("1000"),
    "TWD_MILLIONS": Decimal("1000000"),
    "TWD_MILLION": Decimal("1000000"),
    "百萬元": Decimal("1000000"),
    "TWD_HUNDRED_MILLIONS": Decimal("100000000"),
    "TWD_100_MILLION": Decimal("100000000"),
    "億元": Decimal("100000000"),
    "TWD_PER_SHARE": Decimal("1"),
    "%": Decimal("1"),
    "PERCENT": Decimal("1"),
    "SHARES": Decimal("1"),
    "千股": Decimal("1000"),
}


def _fact_id(record: RawFinancialRecord, suffix: str = "reported") -> str:
    key = "|".join(
        [
            record.ticker,
            record.filing_id,
            record.period_label,
            record.statement,
            record.line_item_standard,
            record.consolidation_scope,
            suffix,
        ]
    )
    return f"FACT-{sha256(key.encode('utf-8')).hexdigest()[:20]}"


def normalize_records(records: Iterable[RawFinancialRecord]) -> NormalizationResult:
    """Normalize supplied records without inventing missing values.

    The function is intentionally source-agnostic.  It can consume a future
    MOPS/XBRL adapter result, a reviewed export, or a test fixture while
    keeping the raw value, original unit and provenance beside the normalized
    value.
    """

    facts: list[FinancialFact] = []
    issues: list[NormalizationIssue] = []
    seen: set[tuple[str, str, str, str, str, str]] = set()
    for index, record in enumerate(records, start=1):
        if not record.source_id.strip() or record.source_id == "SRC-UNSPECIFIED":
            issues.append(
                NormalizationIssue(
                    issue_id=f"NORM-SOURCE-{index}",
                    source_id=record.source_id or None,
                    ticker=record.ticker,
                    issue_type="MISSING_SOURCE_ID",
                    message="每筆財務事實都必須有可回溯的 source_id。",
                )
            )
        if record.currency is None and record.unit not in {"%", "PERCENT", "SHARES", "千股"}:
            issues.append(
                NormalizationIssue(
                    issue_id=f"NORM-CURRENCY-{index}",
                    source_id=record.source_id or None,
                    ticker=record.ticker,
                    issue_type="MISSING_CURRENCY",
                    message="金額資料缺少 currency, 保留資料但阻擋決策級模型載入。",
                )
            )

        key = (
            record.ticker,
            record.filing_id,
            record.period_label,
            record.statement,
            record.line_item_standard,
            record.consolidation_scope,
        )
        duplicate = key in seen
        seen.add(key)
        if duplicate:
            issues.append(
                NormalizationIssue(
                    issue_id=f"NORM-DUPLICATE-{index}",
                    source_id=record.source_id,
                    ticker=record.ticker,
                    issue_type="DUPLICATE_FACT_KEY",
                    message="同一公司、文件、期間、科目與 scope 重複; 不得靜默覆蓋。",
                )
            )

        scale = _UNIT_SCALE.get(record.unit)
        normalized_value = None
        status = "AVAILABLE"
        method = "as_reported"
        note = None
        if record.numeric_value is None:
            status = "MISSING"
            method = "missing_preserved"
            note = "來源未提供數值; 不可轉換為 0。"
        elif scale is None:
            status = "INVALID"
            method = "not_normalized"
            note = f"不支援的來源單位: {record.unit}。"
            issues.append(
                NormalizationIssue(
                    issue_id=f"NORM-UNIT-{index}",
                    source_id=record.source_id,
                    ticker=record.ticker,
                    issue_type="UNKNOWN_UNIT",
                    message=note,
                )
            )
        else:
            normalized_value = record.numeric_value * scale
            method = "scaled_to_base_unit" if scale != 1 else "as_reported"

        facts.append(
            FinancialFact(
                fact_id=_fact_id(record),
                company_id=record.company_id,
                ticker=record.ticker,
                source_id=record.source_id,
                filing_id=record.filing_id,
                period_end=record.period_end,
                period_label=record.period_label,
                period_type=record.period_type,
                fiscal_year=record.fiscal_year,
                fiscal_quarter=record.fiscal_quarter,
                statement=record.statement,
                line_item_original=record.line_item_original,
                line_item_standard=record.line_item_standard,
                source_value=record.numeric_value,
                normalized_value=normalized_value,
                source_unit=record.unit,
                normalized_unit="BASE_CURRENCY"
                if record.unit not in {"%", "PERCENT", "SHARES", "千股", "TWD_PER_SHARE"}
                else record.unit,
                currency=record.currency,
                duration_or_instant=record.duration_or_instant,
                ytd_or_standalone=record.ytd_or_standalone,
                consolidation_scope=record.consolidation_scope,
                source_location=record.source_location,
                evidence_label=record.evidence_label,
                confidence=record.confidence,
                data_quality_status=status,
                normalization_method=method,
                normalization_note=note,
            )
        )

    return NormalizationResult(facts=facts, issues=issues)


def derive_standalone_quarters(facts: Iterable[FinancialFact]) -> list[FinancialFact]:
    """Derive flow statement standalone quarters from explicit YTD facts.

    Balance-sheet instant facts are never differenced.  Q1 is the reported
    YTD value; Q2/Q3/Q4 use the immediately prior YTD value for the same
    metric, company and scope.  Missing inputs remain absent.
    """

    facts = list(facts)
    flow_statements = {"income_statement", "cash_flow", "kpi_schedule", "segment"}
    groups: dict[tuple[str, str, str, str], list[FinancialFact]] = defaultdict(list)
    for fact in facts:
        if fact.statement in flow_statements and fact.ytd_or_standalone == "YTD":
            groups[
                (fact.ticker, fact.statement, fact.line_item_standard, fact.consolidation_scope)
            ].append(fact)

    derived: list[FinancialFact] = []
    for grouped in groups.values():
        by_quarter = {
            fact.fiscal_quarter: fact
            for fact in grouped
            if fact.fiscal_year is not None and fact.fiscal_quarter is not None
        }
        for quarter, current in sorted(by_quarter.items()):
            if current.normalized_value is None:
                continue
            if quarter == 1:
                value = current.normalized_value
                note = "Q1 standalone equals Q1 YTD。"
            else:
                prior = by_quarter.get(quarter - 1)
                if prior is None or prior.normalized_value is None:
                    continue
                value = current.normalized_value - prior.normalized_value
                note = f"由 {current.period_label} 減 {prior.period_label} 的同口徑 YTD 差分取得。"
            clone = deepcopy(current)
            clone.fact_id = f"{current.fact_id}-Q{quarter}-STANDALONE"
            clone.period_type = "quarterly"
            clone.ytd_or_standalone = "STANDALONE"
            clone.normalized_value = value
            clone.source_value = value
            clone.source_unit = current.normalized_unit
            clone.normalization_method = "derived_from_ytd"
            clone.evidence_label = "derived_calculation"
            clone.normalization_note = note
            derived.append(clone)
    return derived
