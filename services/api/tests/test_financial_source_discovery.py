from __future__ import annotations

from topicpilot_api.financial_research.source_discovery import (
    classify_financial_document,
    validate_source_gate,
)


def test_material_announcement_with_eps_is_not_a_full_report() -> None:
    classification = classify_financial_document(
        title="公告本公司董事會決議通過115年第二季合併財務報告",
        text="財務報告或年度自結財務資訊報導期間 2026/01/01~2026/06/30 基本每股盈餘 (0.52)",
        filename="20260812_C1(31).pdf",
        source_url="https://www.cpdc.com.tw/uploads/0_MI/20260812_C1(31).pdf",
        declared_official=True,
    )

    decision = validate_source_gate(classification, expected_period="2026Q2")
    assert classification.document_type == "MATERIAL_ANNOUNCEMENT"
    assert decision.status == "WRONG_DOCUMENT_TYPE"


def test_full_report_with_line_broken_eps_note_passes_content_gate() -> None:
    classification = classify_financial_document(
        title="Consolidated Financial Statements",
        text=(
            "For the three months ended March 31, 2026. "
            "Consolidated statements of comprehensive income. "
            "Earnings per share. Weighted average number of ordinary shares outstanding."
        ),
        filename="202601_1314_AIA.pdf",
        source_url="https://doc.twse.com.tw/server-java/t57sb01?co_id=1314&year=115",
        declared_official=True,
    )

    decision = validate_source_gate(classification, expected_period="2026Q1")
    assert classification.document_type == "FULL_FINANCIAL_STATEMENT"
    assert classification.has_eps_note is True
    assert classification.has_weighted_average_shares is True
    assert decision.status == "PASS"


def test_full_report_without_note_is_explicitly_incomplete() -> None:
    classification = classify_financial_document(
        title="IFRSs合併財報",
        text="115年第一季 合併資產負債表 合併綜合損益表 合併現金流量表",
        source_url="https://doc.twse.com.tw/server-java/t57sb01?co_id=1314&year=115",
        declared_official=True,
    )

    decision = validate_source_gate(classification, expected_period="115年第一季")
    assert decision.status == "FULL_REPORT_FOUND_NOTE_NOT_LOCATED"


def test_non_official_index_is_not_upgraded_by_matching_filename() -> None:
    classification = classify_financial_document(
        title="Consolidated Financial Statements",
        text="Earnings per share weighted average number of ordinary shares outstanding",
        filename="202602_1314_AI1.pdf",
        source_url="https://example.com/202602_1314_AI1.pdf",
    )

    decision = validate_source_gate(classification)
    assert decision.status == "OFFICIAL_SOURCE_NOT_FOUND"


def test_not_yet_available_is_distinct_from_source_not_found() -> None:
    classification = classify_financial_document(
        title="Investor relations financial reports",
        text="2026 Q1 attachment pending upload",
        source_url="https://issuer.example/ir",
        declared_official=True,
    )

    decision = validate_source_gate(classification, disclosure_not_yet_available=True)
    assert decision.status == "OFFICIAL_DISCLOSURE_NOT_YET_AVAILABLE"


def test_note_parse_failure_does_not_upgrade_weighted_shares() -> None:
    classification = classify_financial_document(
        title="Consolidated Financial Statements",
        text="2026 Q1 consolidated statements Earnings per share weighted average ordinary shares",
        source_url="https://doc.twse.com.tw/server-java/t57sb01?co_id=1314&year=115",
        declared_official=True,
    )

    decision = validate_source_gate(classification, parse_failed=True)
    assert decision.status == "NOTE_FOUND_PARSE_FAILED"


def test_unit_normalization_failure_is_preserved_after_document_gate() -> None:
    classification = classify_financial_document(
        title="Consolidated Financial Statements",
        text="2026 Q1 consolidated statements Earnings per share weighted average ordinary shares",
        source_url="https://doc.twse.com.tw/server-java/t57sb01?co_id=1314&year=115",
        declared_official=True,
    )

    decision = validate_source_gate(classification, unit_normalization_failed=True)
    assert decision.status == "UNIT_NORMALIZATION_FAILED"


def test_eps_bridge_mismatch_is_not_relabelled_as_source_failure() -> None:
    classification = classify_financial_document(
        title="Consolidated Financial Statements",
        text="2026 Q1 consolidated statements Earnings per share weighted average ordinary shares",
        source_url="https://doc.twse.com.tw/server-java/t57sb01?co_id=1314&year=115",
        declared_official=True,
    )

    decision = validate_source_gate(classification, bridge_mismatch=True)
    assert decision.status == "EPS_BRIDGE_MISMATCH"


def test_annual_report_is_not_a_quarterly_financial_report() -> None:
    classification = classify_financial_document(
        title="114 年股東會年報",
        text="Annual report and corporate governance information",
        source_url="https://issuer.example/annual-report.pdf",
        declared_official=True,
    )

    decision = validate_source_gate(classification, expected_period="2026Q1")
    assert classification.document_type == "ANNUAL_REPORT"
    assert decision.status == "WRONG_DOCUMENT_TYPE"


def test_eps_note_without_current_share_column_remains_incomplete() -> None:
    classification = classify_financial_document(
        title="Earnings per share note",
        text="2026 Q2 earnings per share, amount after tax, in dollars",
        source_url="https://doc.twse.com.tw/server-java/t57sb01?co_id=1314&year=115",
        declared_official=True,
    )

    decision = validate_source_gate(classification, require_weighted_average_shares=True)
    assert decision.status == "WRONG_DOCUMENT_TYPE"
