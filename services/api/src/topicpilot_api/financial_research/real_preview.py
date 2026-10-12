"""Explicit non-Production real-financial Preview read model.

This module is intentionally not a database importer and is not the formal
production source.  The values are a bounded, checked-in read model generated
from official MOPS responses and issuer financial-report evidence.  Each
period carries the official artifact hash in ``source_location`` and keeps
the source rights gate as UNVERIFIED.  The application only enables this
model when the explicit ``TOPICPILOT_REAL_FINANCIAL_PREVIEW`` setting is true.
"""

# User-facing Chinese provenance strings intentionally use full-width punctuation.
# ruff: noqa: RUF001

from __future__ import annotations

from datetime import date
from decimal import Decimal
from hashlib import sha256

from .contract import EpsNoteExtractionResult, FinancialFact, FinancialSource
from .eps_note_ingestion import normalize_period_contract, parse_eps_note_rows
from .store import InMemoryFinancialResearchStore

_SOURCE_ID = "SRC-MOPS-LEGACY-HTML-T164"
_SOURCE_URL = "https://mopsov.twse.com.tw/mops/web/ajax_t164sb04"
_NPC_1303_Q1_SOURCE_ID = "SRC-NPC-1303-2026Q1-CONSOLIDATED-REPORT"
_NPC_1303_Q1_SOURCE_URL = (
    "https://www.npc.com.tw/npcfile/public/report/finreport/20260520103714607.pdf"
)
_MOPS_1314_FINANCIAL_INDEX_URL = (
    "https://doc.twse.com.tw/server-java/t57sb01?co_id=1314&colorchg=1&mtype=A&step=1&year=115"
)
_CPDC_Q1_SOURCE_ID = "SRC-MOPS-1314-2026Q1-CONSOLIDATED-REPORT"
_CPDC_Q1_SOURCE_URL = _MOPS_1314_FINANCIAL_INDEX_URL
_CPDC_Q1_EN_SOURCE_ID = "SRC-MOPS-1314-2026Q1-EN-CONSOLIDATED-REPORT"
_CPDC_Q1_EN_SOURCE_URL = _MOPS_1314_FINANCIAL_INDEX_URL
_CPDC_Q2_SOURCE_ID = "SRC-MOPS-1314-2026Q2-CONSOLIDATED-REPORT"
_CPDC_Q2_SOURCE_URL = _MOPS_1314_FINANCIAL_INDEX_URL
_TYG_2025_ANNUAL_SOURCE_ID = "SRC-TYG-1319-2025-ANNUAL-REPORT"
_TYG_2025_ANNUAL_SOURCE_URL = "https://www.tyg.com.tw/assets/data/annual-report114.pdf"
_TYG_IR_SOURCE_ID = "SRC-TYG-1319-IR-FINANCIAL-INDEX"
_TYG_IR_SOURCE_URL = "https://www.tyg.com.tw/en/investor_relations/"
_CPDC_IR_SOURCE_ID = "SRC-CPDC-IR-FINANCIAL-INDEX"
_CPDC_IR_SOURCE_URL = "https://www.cpdc.com.tw/tw/ir_financial"
_ENDPOINTS = {
    "income_statement": "ajax_t164sb04",
    "balance_sheet": "ajax_t164sb03",
    "cash_flow": "ajax_t164sb05",
}

# Normalized TWD values from the official MOPS responses.  They are deliberately
# kept as strings to avoid binary floating-point conversion before Decimal.
_PERIODS: dict[str, list[dict[str, object]]] = {
    "1303": [
        {
            "label": "FY2025",
            "end": "2025-12-31",
            "type": "annual",
            "quarter": 4,
            "hash": "efc674e9eb4024b5b2d291475ffdc79a315211563815434dfa3a16d09a3d9808",
            "income": {
                "revenue": "259911744000",
                "gross_profit_reported": "21587080000",
                "gross_profit": "21599221000",
                "operating_income": "3703579000",
                "pretax_income": "6458894000",
                "net_income": "5065640000",
                "basic_eps": "0.57",
                "operating_expenses": "17895642000",
                "cost_of_revenue": "238324664000",
                "income_tax": "1393254000",
                "non_operating_income": "2755315000",
            },
            "balance": {
                "assets": "610598465000",
                "current_assets": "177835621000",
                "non_current_assets": "432762844000",
                "current_liabilities": "134700304000",
                "non_current_liabilities": "104099196000",
                "parent_equity": "355665838000",
                "noncontrolling_interest": "16133127000",
                "cash_and_equivalents": "46149879000",
            },
            "cash": {
                "cash_from_operations": "8649366000",
                "cash_from_investing": "-11332463000",
                "cash_from_financing": "-16751106000",
                "cash_at_beginning": "66445373000",
                "cash_at_end": "46149879000",
                "fx_effect_on_cash": "-861291000",
                "net_change_in_cash": "-20295494000",
            },
        },
        {
            "label": "2026Q1_YTD",
            "end": "2026-03-31",
            "type": "ytd",
            "quarter": 1,
            "hash": "578ae75d62c16a1af6297415770cf9dc81f9d13408dd506b56be5c6a40a9a1d1",
            "income": {
                "revenue": "68596393000",
                "gross_profit_reported": "8188671000",
                "gross_profit": "8186597000",
                "operating_income": "3741833000",
                "pretax_income": "16080166000",
                "net_income": "14674818000",
                "parent_net_income": "14254717000",
                "basic_eps": "1.80",
                "operating_expenses": "4444764000",
                "cost_of_revenue": "60407722000",
                "income_tax": "1405348000",
                "non_operating_income": "12338333000",
            },
            "shares": {
                "weighted_average_basic_shares": "7930822",
            },
            "balance": {
                "assets": "647743623000",
                "current_assets": "193418745000",
                "non_current_assets": "454324878000",
                "current_liabilities": "131197270000",
                "non_current_liabilities": "115971662000",
                "parent_equity": "383826269000",
                "noncontrolling_interest": "16748422000",
                "cash_and_equivalents": "42831248000",
            },
            "cash": {
                "cash_from_operations": "158451000",
                "cash_from_investing": "-7733111000",
                "cash_from_financing": "1175952000",
                "cash_at_beginning": "46149879000",
                "cash_at_end": "42831248000",
                "fx_effect_on_cash": "3080077000",
                "net_change_in_cash": "-3318631000",
            },
        },
        {
            "label": "2026Q2_YTD",
            "end": "2026-06-30",
            "type": "ytd",
            "quarter": 2,
            "hash": "e64843a81706703320cda9e240afe212f87f7ee249f279721930fd03d2c5f0d3",
            "income": {
                "revenue": "152243276000",
                "gross_profit_reported": "24013833000",
                "gross_profit": "23994875000",
                "operating_income": "15099114000",
                "pretax_income": "46844049000",
                "net_income": "42224999000",
                "basic_eps": "5.17",
                "operating_expenses": "8895761000",
                "cost_of_revenue": "128229443000",
                "income_tax": "4619050000",
                "non_operating_income": "31744935000",
            },
            "balance": {
                "assets": "723033450000",
                "current_assets": "208542666000",
                "non_current_assets": "514490784000",
                "current_liabilities": "117261172000",
                "non_current_liabilities": "108117928000",
                "parent_equity": "477747773000",
                "noncontrolling_interest": "19906577000",
                "cash_and_equivalents": "41946162000",
            },
            "cash": {
                "cash_from_operations": "3278205000",
                "cash_from_investing": "-14387540000",
                "cash_from_financing": "3691406000",
                "cash_at_beginning": "46149879000",
                "cash_at_end": "41946162000",
                "fx_effect_on_cash": "3214212000",
                "net_change_in_cash": "-4203717000",
            },
        },
    ],
    "1314": [
        {
            "label": "FY2025",
            "end": "2025-12-31",
            "type": "annual",
            "quarter": 4,
            "hash": "8b27629f4037a84defca2d83e3c45a72e2d02c7caac1a2df6c77a651de31d116",
            "income": {
                "revenue": "19217032000",
                "gross_profit_reported": "-1839312000",
                "gross_profit": "-1839312000",
                "operating_income": "-3567254000",
                "pretax_income": "-2475942000",
                "net_income": "-2989497000",
                "basic_eps": "-0.78",
                "diluted_eps": "-0.78",
                "operating_expenses": "1727942000",
                "cost_of_revenue": "21056344000",
                "income_tax": "266279000",
                "non_operating_income": "1091312000",
            },
            "balance": {
                "assets": "129340251000",
                "current_assets": "57800566000",
                "non_current_assets": "71539685000",
                "current_liabilities": "27880645000",
                "non_current_liabilities": "25138243000",
                "parent_equity": "76264997000",
                "noncontrolling_interest": "56366000",
                "cash_and_equivalents": "1822499000",
            },
            "cash": {
                "cash_from_operations": "-3846385000",
                "cash_from_investing": "3902176000",
                "cash_from_financing": "-4165584000",
                "cash_at_beginning": "6165897000",
                "cash_at_end": "1822499000",
                "fx_effect_on_cash": "-233605000",
                "net_change_in_cash": "-4343398000",
            },
        },
        {
            "label": "2026Q1_YTD",
            "end": "2026-03-31",
            "type": "ytd",
            "quarter": 1,
            "hash": "EEDE9821FB41FCF7CEEDC96A56831B132991A32F90D6CEB4819EB8F14D210E2D",
            "income": {
                "revenue": "6503269000",
                "gross_profit_reported": "-33676000",
                "gross_profit": "-33676000",
                "operating_income": "-539404000",
                "pretax_income": "-257560000",
                "net_income": "-312247000",
                "parent_net_income": "-263381000",
                "basic_eps": "-0.07",
                "diluted_eps": "-0.07",
                "operating_expenses": "505728000",
                "cost_of_revenue": "6536945000",
                "income_tax": "2157000",
                "non_operating_income": "281844000",
            },
            "shares": {
                "weighted_average_basic_shares": "3784850",
                "weighted_average_diluted_shares": "3786318",
            },
            "balance": {
                "assets": "128112754000",
                "current_assets": "57442349000",
                "non_current_assets": "70670405000",
                "current_liabilities": "37332389000",
                "non_current_liabilities": "14479854000",
                "parent_equity": "76248003000",
                "noncontrolling_interest": "52508000",
                "cash_and_equivalents": "1367909000",
            },
            "cash": {
                "cash_from_operations": "-142286000",
                "cash_from_investing": "1287758000",
                "cash_from_financing": "-1550463000",
                "cash_at_beginning": "1822499000",
                "cash_at_end": "1367909000",
                "fx_effect_on_cash": "-49599000",
                "net_change_in_cash": "-454590000",
            },
        },
        {
            "label": "2026Q2_YTD",
            "end": "2026-06-30",
            "type": "ytd",
            "quarter": 2,
            "hash": "95D583A749804C8FB21040B27B433D6281D03C0EFDB23DC63E773FB867DE6636",
            "income": {
                "revenue": "7979691000",
                "gross_profit_reported": "-89641000",
                "gross_profit": "-89641000",
                "operating_income": "-758749000",
                "pretax_income": "-1985639000",
                "net_income": "-1994090000",
                "parent_net_income": "-1986324000",
                "basic_eps": "-0.52",
                "diluted_eps": "-0.52",
                "operating_expenses": "669108000",
                "cost_of_revenue": "8069332000",
                "income_tax": "25000",
                "non_operating_income": "-1226890000",
            },
            "shares": {
                "weighted_average_basic_shares": "3784850",
            },
            "balance": {
                "assets": "124897130000",
                "current_assets": "57411806000",
                "non_current_assets": "67485324000",
                "current_liabilities": "34247882000",
                "non_current_liabilities": "15236258000",
                "parent_equity": "75364344000",
                "noncontrolling_interest": "48646000",
                "cash_and_equivalents": "2243908000",
            },
            "cash": {
                "cash_from_operations": "348987000",
                "cash_from_investing": "3444913000",
                "cash_from_financing": "-3329796000",
                "cash_at_beginning": "1822499000",
                "cash_at_end": "2243908000",
                "fx_effect_on_cash": "-42695000",
                "net_change_in_cash": "421409000",
            },
        },
    ],
    "1319": [
        {
            "label": "FY2025",
            "end": "2025-12-31",
            "type": "annual",
            "quarter": 4,
            "hash": "a273d6fd66028bd27e3d88d9496350979d510bca5fda6040eafe8bad11e50669",
            "income": {
                "revenue": "25094263000",
                "gross_profit_reported": "8427374000",
                "gross_profit": "8427374000",
                "operating_income": "4602192000",
                "pretax_income": "4791376000",
                "net_income": "3902579000",
                "parent_net_income": "3803810000",
                "basic_eps": "6.43",
                "diluted_eps": "6.43",
                "operating_expenses": "3825182000",
                "cost_of_revenue": "16666889000",
                "income_tax": "888797000",
                "non_operating_income": "189184000",
            },
            "shares": {
                "weighted_average_basic_shares": "591477",
                "weighted_average_diluted_shares": "591536",
            },
            "balance": {
                "assets": "38592116000",
                "current_assets": "13192140000",
                "non_current_assets": "25399976000",
                "current_liabilities": "6957545000",
                "non_current_liabilities": "2949745000",
                "parent_equity": "28065768000",
                "noncontrolling_interest": "619058000",
                "cash_and_equivalents": "2661707000",
            },
            "cash": {
                "cash_from_operations": "4417206000",
                "cash_from_investing": "-3163197000",
                "cash_from_financing": "-3341764000",
                "cash_at_beginning": "4736971000",
                "cash_at_end": "2661707000",
                "fx_effect_on_cash": "12491000",
                "net_change_in_cash": "-2075264000",
            },
        },
        {
            "label": "2026Q1_YTD",
            "end": "2026-03-31",
            "type": "ytd",
            "quarter": 1,
            "hash": "1c1e43eb3a6ef0f4a688d36b263af04fd72c11e625f8605381c188920783e10f",
            "income": {
                "revenue": "7290680000",
                "gross_profit_reported": "2776781000",
                "gross_profit": "2776781000",
                "operating_income": "1773688000",
                "pretax_income": "1877772000",
                "net_income": "1503141000",
                "basic_eps": "2.48",
                "diluted_eps": "2.48",
                "operating_expenses": "1003093000",
                "cost_of_revenue": "4513899000",
                "income_tax": "374631000",
                "non_operating_income": "104084000",
            },
            "balance": {
                "assets": "38354471000",
                "current_assets": "13192166000",
                "non_current_assets": "25162305000",
                "current_liabilities": "5670104000",
                "non_current_liabilities": "2910693000",
                "parent_equity": "29156021000",
                "noncontrolling_interest": "617653000",
                "cash_and_equivalents": "4045292000",
            },
            "cash": {
                "cash_from_operations": "2371166000",
                "cash_from_investing": "-446155000",
                "cash_from_financing": "-581433000",
                "cash_at_beginning": "2661707000",
                "cash_at_end": "4045292000",
                "fx_effect_on_cash": "40007000",
                "net_change_in_cash": "1383585000",
            },
        },
        {
            "label": "2026Q2_YTD",
            "end": "2026-06-30",
            "type": "ytd",
            "quarter": 2,
            "hash": "dc1f7d7fb9b971c79cc9e204932cafda17ba9756cc563c90962007d91d386c4d",
            "income": {
                "revenue": "11293727000",
                "gross_profit_reported": "3672242000",
                "gross_profit": "3672242000",
                "operating_income": "1779893000",
                "pretax_income": "2178262000",
                "net_income": "1746455000",
                "basic_eps": "2.98",
                "diluted_eps": "2.98",
                "operating_expenses": "1892349000",
                "cost_of_revenue": "7621485000",
                "income_tax": "431807000",
                "non_operating_income": "398369000",
            },
            "balance": {
                "assets": "39358743000",
                "current_assets": "13853177000",
                "non_current_assets": "25505566000",
                "current_liabilities": "8877716000",
                "non_current_liabilities": "2851468000",
                "parent_equity": "27029077000",
                "noncontrolling_interest": "600482000",
                "cash_and_equivalents": "5265545000",
            },
            "cash": {
                "cash_from_operations": "4436563000",
                "cash_from_investing": "-1212360000",
                "cash_from_financing": "-656195000",
                "cash_at_beginning": "2661707000",
                "cash_at_end": "5265545000",
                "fx_effect_on_cash": "35830000",
                "net_change_in_cash": "2603838000",
            },
        },
    ],
}


def _fact_id(ticker: str, period: str, statement: str, line: str, source_id: str) -> str:
    value = f"{ticker}|{period}|{statement}|{line}|{source_id}"
    return f"PREVIEW-{sha256(value.encode('utf-8')).hexdigest()[:20]}"


def _make_fact(
    *,
    ticker: str,
    period: dict[str, object],
    statement: str,
    line: str,
    value: str,
    source_unit: str = "TWD_1000",
    source_id: str = _SOURCE_ID,
    source_url: str | None = None,
) -> FinancialFact:
    period_label = str(period["label"])
    amount = Decimal(value)
    source_value = amount / Decimal("1000") if source_unit == "TWD_1000" else amount
    normalized_amount = amount * Decimal("1000") if source_unit == "SHARES_1000" else amount
    period_type = str(period["type"])
    end = date.fromisoformat(str(period["end"]))
    quarter = int(period["quarter"])
    source_location = (
        f"{source_url}#period={period_label}"
        if source_url
        else f"https://mopsov.twse.com.tw/mops/web/{_ENDPOINTS[statement]}"
        f"#artifact_hash={period['hash']}"
    )
    return FinancialFact(
        fact_id=_fact_id(ticker, period_label, statement, line, source_id),
        company_id=ticker,
        ticker=ticker,
        source_id=source_id,
        filing_id=f"MOPS-{ticker}-{end.year}-Q{quarter}-CONSOLIDATED",
        period_end=end,
        period_label=period_label,
        period_type="annual" if period_type == "annual" else "ytd",
        fiscal_year=end.year,
        fiscal_quarter=quarter,
        statement=statement,
        line_item_original=line,
        line_item_standard=line,
        source_value=source_value,
        normalized_value=normalized_amount,
        source_unit=source_unit,
        normalized_unit=(
            "BASE_CURRENCY"
            if source_unit == "TWD_1000"
            else "SHARES"
            if source_unit == "SHARES_1000"
            else source_unit
        ),
        currency="TWD" if source_unit != "SHARES_1000" else None,
        duration_or_instant="INSTANT" if statement == "balance_sheet" else "DURATION",
        ytd_or_standalone="NOT_APPLICABLE" if statement == "balance_sheet" else "YTD",
        consolidation_scope="consolidated",
        source_location=source_location,
        evidence_label="fact_source_reported",
        confidence="high",
        data_quality_status="AVAILABLE",
        normalization_method="adapter_normalized_twd_1000",
        normalization_note=(
            "官方報表 response；non-Production Preview read model，來源權利仍未確認。"
        ),
    )


def build_real_financial_preview_store() -> InMemoryFinancialResearchStore:
    facts: list[FinancialFact] = []
    source_overrides = {
        ("1303", "2026Q1_YTD"): (_NPC_1303_Q1_SOURCE_ID, _NPC_1303_Q1_SOURCE_URL),
        ("1314", "2026Q1_YTD"): (_CPDC_Q1_SOURCE_ID, _CPDC_Q1_SOURCE_URL),
        ("1314", "2026Q2_YTD"): (_CPDC_Q2_SOURCE_ID, _CPDC_Q2_SOURCE_URL),
        ("1319", "FY2025"): (_TYG_2025_ANNUAL_SOURCE_ID, _TYG_2025_ANNUAL_SOURCE_URL),
    }
    for ticker, periods in _PERIODS.items():
        for period in periods:
            fact_source_id, fact_source_url = source_overrides.get(
                (ticker, str(period["label"])), (_SOURCE_ID, None)
            )
            for statement_key in ("income", "balance", "cash"):
                statement = {
                    "income": "income_statement",
                    "balance": "balance_sheet",
                    "cash": "cash_flow",
                }[statement_key]
                for line, value in dict(period[statement_key]).items():
                    unit = "TWD_PER_SHARE" if line in {"basic_eps", "diluted_eps"} else "TWD_1000"
                    line_source_id = fact_source_id
                    line_source_url = fact_source_url
                    if ticker == "1314" and period["label"] == "2026Q1_YTD" and line not in {
                        "parent_net_income",
                        "basic_eps",
                        "diluted_eps",
                    }:
                        line_source_id = _SOURCE_ID
                        line_source_url = None
                    facts.append(
                        _make_fact(
                            ticker=ticker,
                            period=period,
                            statement=statement,
                            line=line,
                            value=str(value),
                            source_unit=unit,
                            source_id=line_source_id,
                            source_url=line_source_url,
                        )
                    )
            if "shares" in period:
                for line, value in dict(period["shares"]).items():
                    facts.append(
                        _make_fact(
                            ticker=ticker,
                            period=period,
                            statement="share_count",
                            line=line,
                            value=str(value),
                            source_unit="SHARES_1000",
                            source_id=fact_source_id,
                            source_url=fact_source_url,
                        )
                    )
    source = FinancialSource(
        source_id=_SOURCE_ID,
        source_type="official_mops_historical_html",
        owner_or_provider="臺灣證券交易所公開資訊觀測站 MOPS",
        source_url=_SOURCE_URL,
        data_usage_rights="INTERNAL_NON_PRODUCTION_PREVIEW_ONLY",
        redistribution_rights="UNVERIFIED",
        license_review_status="PENDING_REVIEW",
    )
    npc_source = FinancialSource(
        source_id=_NPC_1303_Q1_SOURCE_ID,
        source_type="official_issuer_financial_report_pdf",
        owner_or_provider="南亞塑膠工業股份有限公司",
        source_url=_NPC_1303_Q1_SOURCE_URL,
        data_usage_rights="INTERNAL_NON_PRODUCTION_PREVIEW_ONLY",
        redistribution_rights="UNVERIFIED",
        license_review_status="PENDING_REVIEW",
    )
    cpdc_q1_source = FinancialSource(
        source_id=_CPDC_Q1_SOURCE_ID,
        source_type="official_mops_full_consolidated_financial_report_pdf",
        owner_or_provider="中國石油化學工業開發股份有限公司",
        source_url=_CPDC_Q1_SOURCE_URL,
        data_usage_rights="INTERNAL_NON_PRODUCTION_PREVIEW_ONLY",
        redistribution_rights="UNVERIFIED",
        license_review_status="PENDING_REVIEW",
    )
    cpdc_q2_source = cpdc_q1_source.model_copy(
        update={"source_id": _CPDC_Q2_SOURCE_ID, "source_url": _CPDC_Q2_SOURCE_URL}
    )
    cpdc_q1_en_source = cpdc_q1_source.model_copy(
        update={"source_id": _CPDC_Q1_EN_SOURCE_ID, "source_url": _CPDC_Q1_EN_SOURCE_URL}
    )
    tyg_annual_source = FinancialSource(
        source_id=_TYG_2025_ANNUAL_SOURCE_ID,
        source_type="official_issuer_annual_report_pdf",
        owner_or_provider="東陽實業廠股份有限公司",
        source_url=_TYG_2025_ANNUAL_SOURCE_URL,
        data_usage_rights="INTERNAL_NON_PRODUCTION_PREVIEW_ONLY",
        redistribution_rights="UNVERIFIED",
        license_review_status="PENDING_REVIEW",
    )
    tyg_ir_source = FinancialSource(
        source_id=_TYG_IR_SOURCE_ID,
        source_type="official_issuer_investor_relations_index",
        owner_or_provider="東陽實業廠股份有限公司",
        source_url=_TYG_IR_SOURCE_URL,
        data_usage_rights="INTERNAL_NON_PRODUCTION_PREVIEW_ONLY",
        redistribution_rights="UNVERIFIED",
        license_review_status="PENDING_REVIEW",
    )
    cpdc_ir_source = FinancialSource(
        source_id=_CPDC_IR_SOURCE_ID,
        source_type="official_issuer_investor_relations_index",
        owner_or_provider="中國石油化學工業開發股份有限公司",
        source_url=_CPDC_IR_SOURCE_URL,
        data_usage_rights="INTERNAL_NON_PRODUCTION_PREVIEW_ONLY",
        redistribution_rights="UNVERIFIED",
        license_review_status="PENDING_REVIEW",
    )
    eps_note_results = _build_eps_note_results()
    return InMemoryFinancialResearchStore(
        facts=facts,
        sources=[
            source,
            npc_source,
            cpdc_q1_source,
            cpdc_q1_en_source,
            cpdc_q2_source,
            tyg_annual_source,
            tyg_ir_source,
            cpdc_ir_source,
        ],
        eps_note_results=eps_note_results,
        allow_public_values=True,
        preview_only=True,
    )


def _build_eps_note_results() -> list[EpsNoteExtractionResult]:
    def period(label: str, end: str, kind: str, quarter: int | None) -> object:
        return normalize_period_contract(
            period_label=label,
            period_end=end,
            period_type=kind,
            fiscal_year=int(end[:4]),
            fiscal_quarter=quarter,
            ytd_or_standalone="NOT_APPLICABLE" if kind == "annual" else "YTD",
        )

    npc_period = period("2026Q1_YTD", "2026-03-31", "ytd", 1)
    tyg_annual_period = period("FY2025", "2025-12-31", "annual", None)
    results = [
        parse_eps_note_rows(
            [
                {
                    "line_item_standard": "parent_net_income",
                    "value": "14254717",
                    "unit": "TWD_1000",
                },
                {
                    "line_item_standard": "weighted_average_basic_shares",
                    "value": "7930822",
                    "unit": "SHARES_1000",
                },
                {"line_item_standard": "basic_eps", "value": "1.80", "unit": "TWD_PER_SHARE"},
            ],
            ticker="1303",
            source_id=_NPC_1303_Q1_SOURCE_ID,
            source_url=_NPC_1303_Q1_SOURCE_URL,
            period=npc_period,
            extraction_method="STRUCTURED",
        ),
        parse_eps_note_rows(
            [
                {
                    "line_item_standard": "parent_net_income",
                    "value": "3803810",
                    "unit": "TWD_1000",
                },
                {
                    "line_item_standard": "weighted_average_basic_shares",
                    "value": "591477",
                    "unit": "SHARES_1000",
                },
                {
                    "line_item_standard": "weighted_average_diluted_shares",
                    "value": "591536",
                    "unit": "SHARES_1000",
                },
                {"line_item_standard": "basic_eps", "value": "6.43", "unit": "TWD_PER_SHARE"},
                {"line_item_standard": "diluted_eps", "value": "6.43", "unit": "TWD_PER_SHARE"},
            ],
            ticker="1319",
            source_id=_TYG_2025_ANNUAL_SOURCE_ID,
            source_url=_TYG_2025_ANNUAL_SOURCE_URL,
            period=tyg_annual_period,
            extraction_method="PDF_TABLE",
        ),
    ]
    q1_cpdc_period = period("2026Q1_YTD", "2026-03-31", "ytd", 1)
    results.append(
        parse_eps_note_rows(
            [
                {
                    "line_item_standard": "parent_net_income",
                    "value": "-263381",
                    "unit": "TWD_1000",
                    "page": "p.69",
                    "raw_text": (
                        "Net loss attributable to ordinary shareholders of the parent company "
                        "(263,381)"
                    ),
                },
                {
                    "line_item_standard": "weighted_average_basic_shares",
                    "value": "3784850",
                    "unit": "SHARES_1000",
                    "page": "p.69",
                    "raw_text": "Continuing operations (259,298) 3,784,850 (0.07)",
                },
                {
                    "line_item_standard": "weighted_average_diluted_shares",
                    "value": "3786318",
                    "unit": "SHARES_1000",
                    "page": "p.69",
                    "raw_text": "Continuing operations (259,298) 3,786,318 (0.07)",
                },
                {
                    "line_item_standard": "basic_eps",
                    "value": "-0.07",
                    "unit": "TWD_PER_SHARE",
                    "page": "p.69",
                },
                {
                    "line_item_standard": "diluted_eps",
                    "value": "-0.07",
                    "unit": "TWD_PER_SHARE",
                    "page": "p.69",
                },
            ],
            ticker="1314",
            source_id=_CPDC_Q1_EN_SOURCE_ID,
            source_url=_CPDC_Q1_EN_SOURCE_URL,
            period=q1_cpdc_period,
            extraction_method="PDF_TABLE",
        )
    )
    q2_cpdc_period = period("2026Q2_YTD", "2026-06-30", "half_year", 2)
    q2_cpdc_note = parse_eps_note_rows(
        [
            {
                "line_item_standard": "parent_net_income",
                "value": "-1986324",
                "unit": "TWD_1000",
                "page": "p.55",
                "raw_text": "歸屬於母公司之本期淨損 (1,986,324)",
            },
            {
                "line_item_standard": "weighted_average_basic_shares",
                "value": "3784850",
                "unit": "SHARES_1000",
                "page": "p.55",
                "raw_text": "基本每股損失：3,784,850 仟股",
            },
            {
                "line_item_standard": "basic_eps",
                "value": "-0.52",
                "unit": "TWD_PER_SHARE",
                "page": "p.55",
            },
        ],
        ticker="1314",
        source_id=_CPDC_Q2_SOURCE_ID,
        source_url=_CPDC_Q2_SOURCE_URL,
        period=q2_cpdc_period,
        extraction_method="MANUAL_REVIEW",
    ).model_copy(
        update={
            "status": "MANUAL_REVIEW_REQUIRED",
            "limitations": [
                (
                    "Q2 中文 PDF 文字層的字型編碼無法可靠還原標籤；股數、EPS、期間與頁碼"
                    "已由官方原件人工覆核。"
                ),
                "未將半年累計 EPS 當成單季 EPS；單季數值仍待獨立期間資料接入。",
            ],
        }
    )
    results.append(q2_cpdc_note)
    for label, end, quarter in (
        ("2026Q1_YTD", "2026-03-31", 1),
        ("2026Q2_YTD", "2026-06-30", 2),
    ):
        results.append(
            EpsNoteExtractionResult(
                ticker="1319",
                source_id=_TYG_IR_SOURCE_ID,
                source_url=_TYG_IR_SOURCE_URL,
                status="SOURCE_UNAVAILABLE",
                parser_id="eps-note-adapter-v1",
                periods=[period(label, end, "ytd", quarter)],
                limitations=[
                    "公司投資人專區目前將 2026 Q1／Q2 財報附件標示為待上傳，"
                    "不能沿用 2025 股數。"
                ],
            )
        )
    for label, end in (("FY2025", "2025-12-31"),):
        results.append(
            EpsNoteExtractionResult(
                ticker="1314",
                source_id=_CPDC_IR_SOURCE_ID,
                source_url=_CPDC_IR_SOURCE_URL,
                status="MANUAL_REVIEW_REQUIRED",
                parser_id="eps-note-adapter-v1",
                periods=[period(label, end, "annual", None)],
                limitations=[
                    "官方財報索引已定位，但 FY2025 EPS 附註仍待從正式合併財報 PDF 完成解析。"
                ],
            )
        )
    return results


__all__ = ["build_real_financial_preview_store"]
