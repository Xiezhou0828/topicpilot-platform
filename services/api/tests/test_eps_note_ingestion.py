# ruff: noqa: RUF001

from __future__ import annotations

from decimal import Decimal

from topicpilot_api.financial_research.contract import EpsNoteExtractionResult
from topicpilot_api.financial_research.eps_bridge import build_eps_bridge
from topicpilot_api.financial_research.eps_note_ingestion import (
    derive_standalone_flow_fields,
    mark_weighted_shares_pending_validation,
    normalize_period_contract,
    parse_eps_note_rows,
    parse_eps_note_text,
)
from topicpilot_api.financial_research.real_preview import build_real_financial_preview_store


def test_text_adapter_parses_chinese_eps_note_with_units_and_page_evidence() -> None:
    period = normalize_period_contract(
        period_label="FY2025",
        period_end="2025-12-31",
        period_type="annual",
        fiscal_year=2025,
        ytd_or_standalone="NOT_APPLICABLE",
    )
    result = parse_eps_note_text(
        """
        附註二十二 每股盈餘（第68頁）
        歸屬於母公司普通股持有人之淨利（仟元） 3,803,810
        基本每股盈餘之普通股加權平均股數（仟股） 591,477
        基本每股盈餘（元） 6.43
        稀釋效果後之普通股加權平均股數（仟股） 591,536
        稀釋每股盈餘（元） 6.43
        """,
        ticker="1319",
        source_id="SRC-TYG",
        source_url="https://issuer.example/annual.pdf",
        period=period,
    )

    assert result.status == "EXTRACTED"
    assert {field.line_item_standard for field in result.fields} == {
        "parent_net_income",
        "weighted_average_basic_shares",
        "weighted_average_diluted_shares",
        "basic_eps",
        "diluted_eps",
    }
    shares = next(
        field
        for field in result.fields
        if field.line_item_standard == "weighted_average_basic_shares"
    )
    assert shares.normalized_value == Decimal("591477000")
    assert shares.normalized_unit == "SHARES"
    assert shares.source_page == "p.68"
    assert shares.raw_field == "weighted_average_basic_shares"


def test_text_adapter_supports_english_note_and_fail_closed_empty_input() -> None:
    period = normalize_period_contract(
        period_label="2026Q1_YTD",
        period_end="2026-03-31",
        period_type="ytd",
        fiscal_year=2026,
        fiscal_quarter=1,
    )
    result = parse_eps_note_text(
        "Net income attributable to owners of parent (thousand dollars) 14,254,717\n"
        "Weighted average common shares for basic EPS (thousand shares) 7,930,822\n"
        "Basic earnings per share 1.80",
        ticker="1303",
        source_id="SRC-NPC",
        source_url="https://issuer.example/q1.pdf",
        period=period,
    )
    assert result.status == "EXTRACTED"
    parent = next(
        field for field in result.fields if field.line_item_standard == "parent_net_income"
    )
    shares = next(
        field
        for field in result.fields
        if field.line_item_standard == "weighted_average_basic_shares"
    )
    assert parent.normalized_value == Decimal("14254717000")
    assert shares.normalized_value == Decimal("7930822000")
    assert parse_eps_note_text(
        None,
        ticker="1303",
        source_id="SRC-MISSING",
        source_url=None,
        period=period,
    ).status == "SOURCE_UNAVAILABLE"


def test_period_contract_and_flow_derivation_preserve_derived_boundary() -> None:
    q1 = normalize_period_contract(
        period_label="2026Q1_YTD",
        period_end="2026-03-31",
        period_type="ytd",
        fiscal_year=2026,
        fiscal_quarter=1,
    )
    h1 = normalize_period_contract(
        period_label="2026Q2_YTD",
        period_end="2026-06-30",
        period_type="half_year",
        fiscal_year=2026,
        fiscal_quarter=2,
    )
    rows = [
        {"line_item_standard": "parent_net_income", "value": "100", "unit": "TWD_1000"},
    ]
    first = parse_eps_note_rows(
        rows,
        ticker="T",
        source_id="SRC",
        source_url=None,
        period=q1,
        extraction_method="STRUCTURED",
    ).fields[0]
    second = parse_eps_note_rows(
        [{"line_item_standard": "parent_net_income", "value": "260", "unit": "TWD_1000"}],
        ticker="T",
        source_id="SRC",
        source_url=None,
        period=h1,
        extraction_method="STRUCTURED",
    ).fields[0]
    derived = derive_standalone_flow_fields(second, first)
    assert derived is not None
    assert derived.period.period_label == "2026Q2_STANDALONE"
    assert derived.normalized_value == Decimal("160000")
    assert derived.data_status == "DERIVED"

    share = parse_eps_note_rows(
        [
            {
                "line_item_standard": "weighted_average_basic_shares",
                "value": "10",
                "unit": "SHARES_1000",
            }
        ],
        ticker="T",
        source_id="SRC",
        source_url=None,
        period=h1,
        extraction_method="STRUCTURED",
    ).fields[0]
    assert derive_standalone_flow_fields(share, share) is None
    assert mark_weighted_shares_pending_validation([share])[0].data_status == "PENDING_VALIDATION"


def test_structured_adapter_retains_comparative_and_reviewable_statuses() -> None:
    period = normalize_period_contract(
        period_label="2025_COMPARATIVE",
        period_end="2025-03-31",
        period_type="quarterly",
        fiscal_year=2025,
        fiscal_quarter=1,
        ytd_or_standalone="YTD",
        comparative_of="2026Q1_YTD",
        retrospective_adjustment="因股份分割追溯調整",
    )
    result = parse_eps_note_rows(
        [{
            "line_item": "weighted_average_basic_shares",
            "value": "7,930,822",
            "unit": "SHARES_1000",
            "page": "40",
            "raw_text": "比較期欄位",
        }],
        ticker="1303",
        source_id="SRC-NPC",
        source_url="https://issuer.example/report.pdf",
        period=period,
    )
    assert result.fields[0].period.comparative_of == "2026Q1_YTD"
    assert result.fields[0].period.retrospective_adjustment == "因股份分割追溯調整"
    assert result.fields[0].source_page == "40"


def test_bridge_classifies_missing_note_and_rejects_bad_or_derived_share_units() -> None:
    store = build_real_financial_preview_store()
    source_facts = [
        fact
        for fact in store.facts
        if fact.ticker == "1303" and fact.period_label == "2026Q1_YTD"
    ]
    period = normalize_period_contract(
        period_label="2026Q1_YTD",
        period_end="2026-03-31",
        period_type="ytd",
        fiscal_year=2026,
        fiscal_quarter=1,
    )
    missing_note = EpsNoteExtractionResult(
        ticker="1303",
        source_id="SRC-NO-EPS-NOTE",
        status="NO_EPS_NOTE",
        parser_id="eps-note-adapter-v1",
        periods=[period],
    )
    wrong_unit_facts = [
        fact.model_copy(update={"normalized_unit": "BASE_CURRENCY"})
        if fact.line_item_standard == "weighted_average_basic_shares"
        else fact
        for fact in source_facts
    ]
    derived_facts = [
        fact.model_copy(update={"evidence_label": "derived_calculation"})
        if fact.line_item_standard == "weighted_average_basic_shares"
        else fact
        for fact in source_facts
    ]
    no_share_facts = [
        fact
        for fact in source_facts
        if fact.line_item_standard != "weighted_average_basic_shares"
    ]

    assert (
        build_eps_bridge(no_share_facts, "1303", [missing_note])[0].status
        == "SOURCE_NOTE_NOT_FOUND"
    )
    assert build_eps_bridge(wrong_unit_facts, "1303")[0].status == "SHARE_UNIT_MISMATCH"
    assert (
        build_eps_bridge(derived_facts, "1303")[0].status
        == "DERIVED_SHARES_PENDING_VALIDATION"
    )


def test_pdf_text_adapter_handles_line_broken_official_eps_table() -> None:
    period = normalize_period_contract(
        period_label="2026Q1_YTD",
        period_start="2026-01-01",
        period_end="2026-03-31",
        period_type="ytd",
    )
    official_excerpt = """Page 69
(33) Earnings per share
The calculation of earnings per share and weighted average number of common stock is as follows:
For the three months ended March 31, 2026
Amount after tax
Weighted average number of ordinary shares outstanding (in thousands)
Earnings per share (in dollars)
Basic earnings per share
Continuing operations ( $ 259,298 ) 3,784,850 ( $ 0.07 )
Net loss for the year attributable to the
parent company's ordinary
shareholders ( $ 263,381 ) ( $ 0.07 )
Diluted earnings per share
Continuing operations ( 259,298 ) 3,786,318 ( $ 0.07 )
"""

    result = parse_eps_note_text(
        official_excerpt,
        ticker="1314",
        source_id="MOPS_202601_1314_AIA",
        source_url="https://doc.twse.com.tw/server-java/t57sb01?co_id=1314&year=115",
        period=period,
    )

    values = {field.line_item_standard: field.normalized_value for field in result.fields}
    assert result.status == "EXTRACTED"
    assert values["parent_net_income"] == Decimal("-263381000")
    assert values["weighted_average_basic_shares"] == Decimal("3784850000")
    assert values["weighted_average_diluted_shares"] == Decimal("3786318000")
    assert values["basic_eps"] == Decimal("-0.07")
    assert values["diluted_eps"] == Decimal("-0.07")
    assert all(field.source_page == "p.69" for field in result.fields)

