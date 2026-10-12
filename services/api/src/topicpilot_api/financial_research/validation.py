from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:  # pragma: no cover - Python 3.10 compatibility
    UTC = timezone.utc  # noqa: UP017
from decimal import Decimal
from hashlib import sha256

from .contract import FinancialFact, FinancialShareData, FinancialValidationReceipt


def _receipt(
    rule: str,
    result: str,
    *,
    reason: str | None = None,
    expected=None,
    observed=None,
    variance=None,
) -> FinancialValidationReceipt:
    return FinancialValidationReceipt(
        validation_run_id=f"VAL-{sha256(f'{rule}-{datetime.now(UTC).isoformat()}'.encode()).hexdigest()[:16]}",
        source_version="financial-foundation.v1",
        validation_rule=rule,
        validation_result=result,
        error_reason=reason,
        run_timestamp=datetime.now(UTC),
        expected_value=expected,
        observed_value=observed,
        variance=variance,
    )


def validate_financial_facts(facts: Iterable[FinancialFact]) -> list[FinancialValidationReceipt]:
    facts = list(facts)
    receipts: list[FinancialValidationReceipt] = []
    keys: set[tuple[str, str, str, str, str, str]] = set()
    for fact in facts:
        key = (
            fact.ticker,
            fact.period_label,
            fact.statement,
            fact.line_item_standard,
            fact.consolidation_scope,
            fact.source_id,
        )
        if key in keys:
            receipts.append(_receipt("duplicate_fact", "FAIL", reason=f"重複事實: {key}"))
        keys.add(key)
        if fact.data_quality_status == "MISSING":
            receipts.append(
                _receipt(
                    "missing_vs_zero",
                    "PARTIAL",
                    reason=(
                        f"{fact.ticker} {fact.period_label} {fact.line_item_standard} "
                        "保留為 missing, 不得轉 0。"
                    ),
                )
            )
        elif fact.data_quality_status == "INVALID":
            receipts.append(
                _receipt(
                    "normalized_value_valid",
                    "FAIL",
                    reason=f"{fact.ticker} {fact.period_label} 使用了無法正規化的單位。",
                )
            )
    if not receipts:
        receipts.append(_receipt("fact_processing_smoke", "PASS"))
    return receipts


def validate_period_scope_currency_and_units(
    facts: Iterable[FinancialFact],
) -> list[FinancialValidationReceipt]:
    """Check that comparable series do not silently mix periods or scopes."""

    facts = list(facts)
    receipts: list[FinancialValidationReceipt] = []
    by_series: dict[tuple[str, str, str, str], list[FinancialFact]] = {}
    for fact in facts:
        key = (fact.ticker, fact.statement, fact.line_item_standard, fact.period_label)
        by_series.setdefault(key, []).append(fact)
        if fact.period_type == "quarterly" and fact.fiscal_quarter is not None:
            label = fact.period_label.upper()
            if (
                label.startswith("Q")
                and label[1:2].isdigit()
                and int(label[1:2]) != fact.fiscal_quarter
            ):
                receipts.append(
                    _receipt(
                        "fiscal_period_label_matches_quarter",
                        "FAIL",
                        reason=(
                            f"{fact.ticker} {fact.period_label} 與 "
                            f"fiscal_quarter={fact.fiscal_quarter} 不一致。"
                        ),
                    )
                )
    for key, series in by_series.items():
        scopes = {fact.consolidation_scope for fact in series}
        currencies = {fact.currency for fact in series if fact.currency is not None}
        units = {fact.normalized_unit for fact in series}
        if len(scopes) > 1:
            receipts.append(
                _receipt(
                    "consolidation_scope_consistency",
                    "FAIL",
                    reason=f"{key} 混用 consolidation scope: {sorted(scopes)}",
                )
            )
        if len(currencies) > 1:
            receipts.append(
                _receipt(
                    "currency_consistency", "FAIL", reason=f"{key} 混用幣別: {sorted(currencies)}"
                )
            )
        if len(units) > 1:
            receipts.append(
                _receipt(
                    "normalized_unit_consistency",
                    "FAIL",
                    reason=f"{key} 混用正規化單位: {sorted(units)}",
                )
            )
    if not receipts:
        receipts.append(_receipt("period_scope_currency_unit_consistency", "PASS"))
    return receipts


def _tieout(
    rule: str, lhs: Decimal | None, rhs: Decimal | None, tolerance: Decimal = Decimal("0.01")
) -> FinancialValidationReceipt:
    if lhs is None or rhs is None:
        return _receipt(rule, "NOT_TESTABLE", reason="必要科目缺漏, 未以 0 補值。")
    variance = lhs - rhs
    return _receipt(
        rule,
        "PASS" if abs(variance) <= tolerance else "FAIL",
        expected=rhs,
        observed=lhs,
        variance=variance,
        reason=None if abs(variance) <= tolerance else "勾稽差異超過容許值。",
    )


def validate_balance_sheet(
    *, assets: Decimal | None, liabilities: Decimal | None, equity: Decimal | None
) -> FinancialValidationReceipt:
    rhs = liabilities + equity if liabilities is not None and equity is not None else None
    return _tieout("balance_sheet_assets_equals_liabilities_plus_equity", assets, rhs)


def validate_income_statement(
    *,
    revenue: Decimal | None,
    cogs: Decimal | None,
    gross_profit: Decimal | None,
    operating_expenses: Decimal | None,
    operating_income: Decimal | None,
    pretax_income: Decimal | None,
    non_operating: Decimal | None,
    net_income: Decimal | None,
    income_tax: Decimal | None,
    gross_profit_reported: Decimal | None = None,
) -> list[FinancialValidationReceipt]:
    return [
        _tieout(
            "income_revenue_minus_cogs_equals_gross_profit",
            revenue - cogs if revenue is not None and cogs is not None else None,
            gross_profit_reported if gross_profit_reported is not None else gross_profit,
        ),
        _tieout(
            "income_gross_minus_opex_equals_operating_income",
            gross_profit - operating_expenses
            if gross_profit is not None and operating_expenses is not None
            else None,
            operating_income,
        ),
        _tieout(
            "income_operating_plus_non_operating_equals_pretax",
            operating_income + non_operating
            if operating_income is not None and non_operating is not None
            else None,
            pretax_income,
        ),
        _tieout(
            "income_pretax_minus_tax_equals_net_income",
            pretax_income - income_tax
            if pretax_income is not None and income_tax is not None
            else None,
            net_income,
        ),
    ]


def validate_cash_flow(
    *,
    beginning_cash: Decimal | None,
    operating_cash_flow: Decimal | None,
    investing_cash_flow: Decimal | None,
    financing_cash_flow: Decimal | None,
    fx_other: Decimal | None,
    ending_cash: Decimal | None,
) -> FinancialValidationReceipt:
    lhs = (
        beginning_cash + operating_cash_flow + investing_cash_flow + financing_cash_flow + fx_other
        if all(
            value is not None
            for value in (
                beginning_cash,
                operating_cash_flow,
                investing_cash_flow,
                financing_cash_flow,
                fx_other,
            )
        )
        else None
    )
    return _tieout("cash_flow_beginning_plus_flows_equals_ending", lhs, ending_cash)


def validate_eps(
    *,
    parent_net_income: Decimal | None,
    weighted_average_shares: Decimal | None,
    reported_eps: Decimal | None,
    tolerance: Decimal = Decimal("0.02"),
) -> FinancialValidationReceipt:
    if parent_net_income is None or weighted_average_shares is None or reported_eps is None:
        return _receipt(
            "eps_reconciliation", "NOT_TESTABLE", reason="歸母淨利、加權平均股數或公告 EPS 缺漏。"
        )
    if weighted_average_shares == 0:
        return _receipt("eps_reconciliation", "FAIL", reason="加權平均股數不可為 0。")
    computed = parent_net_income / weighted_average_shares
    return _tieout("eps_reconciliation", computed, reported_eps, tolerance)


def validate_share_data(share_data: FinancialShareData) -> FinancialValidationReceipt:
    if share_data.weighted_average_basic_shares is None:
        return _receipt(
            "weighted_average_shares_present", "NOT_TESTABLE", reason="缺少加權平均基本股數。"
        )
    if share_data.weighted_average_basic_shares <= 0:
        return _receipt(
            "weighted_average_shares_positive", "FAIL", reason="加權平均基本股數必須大於 0。"
        )
    return _receipt("weighted_average_shares_present", "PASS")
