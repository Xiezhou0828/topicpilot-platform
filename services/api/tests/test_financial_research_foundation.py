# ruff: noqa: RUF001

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from topicpilot_api.financial_research.contract import (
    FinancialShareData,
    FinancialSource,
    RawFinancialRecord,
)
from topicpilot_api.financial_research.normalization import (
    derive_standalone_quarters,
    normalize_records,
)
from topicpilot_api.financial_research.source_adapter import (
    LocalJsonFilingAdapter,
    MopsSourceAdapter,
    TwseOpenApiSnapshotAdapter,
)
from topicpilot_api.financial_research.store import InMemoryFinancialResearchStore
from topicpilot_api.financial_research.validation import (
    validate_balance_sheet,
    validate_cash_flow,
    validate_eps,
    validate_financial_facts,
    validate_income_statement,
    validate_period_scope_currency_and_units,
    validate_share_data,
)
from topicpilot_api.main import create_app

FIXTURE = Path(__file__).parent / "fixtures" / "financial_research" / "filing_sample.json"


def _raw(
    *,
    quarter: int,
    label: str,
    value: str | None,
    line: str,
    statement: str = "income_statement",
    ytd: str = "YTD",
) -> RawFinancialRecord:
    return RawFinancialRecord(
        company_id="TEST-1303",
        ticker="1303",
        source_id="SRC-TEST",
        filing_id=f"FILING-{label}",
        period_end=date(2026, min(quarter * 3, 12), 28),
        period_label=label,
        period_type="ytd" if ytd == "YTD" else "quarterly",
        fiscal_year=2026,
        fiscal_quarter=quarter,
        statement=statement,
        line_item_original=line,
        line_item_standard=line,
        numeric_value=Decimal(value) if value is not None else None,
        unit="TWD_MILLIONS",
        currency="TWD",
        duration_or_instant="INSTANT" if statement == "balance_sheet" else "DURATION",
        ytd_or_standalone=ytd,
        consolidation_scope="consolidated",
        evidence_label="fact_source_reported" if value is not None else "missing_required_source",
    )


def test_local_adapter_is_explicitly_non_live_and_reproducible() -> None:
    result = LocalJsonFilingAdapter(FIXTURE).retrieve()

    assert result.status == "SUCCESS"
    assert result.live_intake is False
    assert result.rights_checked is True
    assert result.raw_artifact_hash and len(result.raw_artifact_hash) == 64
    assert len(result.records) == 3


def test_local_adapter_distinguishes_empty_source_and_amended_filing(tmp_path: Path) -> None:
    empty = tmp_path / "empty.json"
    empty.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(empty.read_text(encoding="utf-8"))
    payload["facts"] = []
    empty.write_text(json.dumps(payload), encoding="utf-8")

    assert LocalJsonFilingAdapter(empty).retrieve().status == "EMPTY_RESULT"

    amended = tmp_path / "amended.json"
    payload["facts"] = json.loads(FIXTURE.read_text(encoding="utf-8"))["facts"]
    payload["filing"]["filing_id"] = "TEST-FILING-1303-2026Q1-AMENDED"
    payload["filing"]["filing_version"] = "AMENDED"
    payload["filing"]["amendment_status"] = "AMENDED"
    amended.write_text(json.dumps(payload), encoding="utf-8")
    result = LocalJsonFilingAdapter(amended).retrieve()
    assert result.status == "SUCCESS"
    assert result.filing is not None and result.filing.amendment_status == "AMENDED"


def test_mops_adapter_fails_closed_without_live_fetcher() -> None:
    result = MopsSourceAdapter().retrieve("https://mops.twse.com.tw/test")

    assert result.status == "SOURCE_UNAVAILABLE"
    assert result.live_intake is False
    assert result.rights_checked is False


def test_twse_openapi_adapter_maps_official_snapshot_without_claiming_rights() -> None:
    income = [
        {
            "年度": "115",
            "季別": "2",
            "公司代號": "1303",
            "營業收入": "152243276.00",
            "營業利益（損失）": "15099114.00",
            "基本每股盈餘（元）": "5.17",
        }
    ]
    balance = [
        {
            "年度": "115",
            "季別": "2",
            "公司代號": "1303",
            "資產總計": "723033450.00",
            "負債總計": "225379100.00",
            "權益總計": "497654350.00",
            "每股參考淨值": "60.24",
        }
    ]
    payloads = {
        TwseOpenApiSnapshotAdapter.income_url: json.dumps(income).encode("utf-8"),
        TwseOpenApiSnapshotAdapter.balance_url: json.dumps(balance).encode("utf-8"),
    }
    result = TwseOpenApiSnapshotAdapter(payloads.__getitem__).retrieve("1303")

    assert result.status == "RIGHTS_UNVERIFIED"
    assert result.live_intake is True
    assert result.rights_checked is True
    assert result.source is not None
    assert result.source.owner_or_provider == "臺灣證券交易所"
    assert result.filing is not None and result.filing.reporting_period_end == date(2026, 6, 30)
    assert {record.line_item_standard for record in result.records} == {
        "revenue",
        "operating_income",
        "basic_eps",
        "assets",
        "liabilities",
        "equity",
        "book_value_per_share",
    }
    assert (
        next(record for record in result.records if record.line_item_standard == "revenue").unit
        == "TWD_1000"
    )
    assert (
        next(record for record in result.records if record.line_item_standard == "basic_eps").unit
        == "TWD_PER_SHARE"
    )


def test_normalization_preserves_zero_and_missing_separately() -> None:
    result = normalize_records(
        [
            _raw(quarter=1, label="Q1-2026", value="0", line="basic_eps"),
            _raw(quarter=1, label="Q1-2026", value=None, line="product_profit"),
        ]
    )

    zero, missing = result.facts
    assert zero.normalized_value == Decimal("0")
    assert zero.data_quality_status == "AVAILABLE"
    assert missing.normalized_value is None
    assert missing.data_quality_status == "MISSING"
    assert any(issue.issue_type == "MISSING_CURRENCY" for issue in result.issues) is False


def test_normalization_scales_source_unit_and_is_idempotent() -> None:
    records = [_raw(quarter=1, label="Q1-2026", value="1.5", line="revenue")]
    first = normalize_records(records)
    second = normalize_records(records)

    assert first.facts[0].normalized_value == Decimal("1500000.0")
    assert first.facts[0].fact_id == second.facts[0].fact_id


def test_ytd_conversion_only_derives_flow_statements() -> None:
    facts = normalize_records(
        [
            _raw(quarter=1, label="Q1-2026", value="100", line="revenue"),
            _raw(quarter=2, label="H1-2026", value="260", line="revenue"),
            _raw(
                quarter=1,
                label="Q1-2026",
                value="500",
                line="total_assets",
                statement="balance_sheet",
            ),
            _raw(
                quarter=2,
                label="H1-2026",
                value="550",
                line="total_assets",
                statement="balance_sheet",
            ),
        ]
    ).facts

    derived = derive_standalone_quarters(facts)

    assert {(fact.period_label, fact.normalized_value) for fact in derived} == {
        ("Q1-2026", Decimal("100000000")),
        ("H1-2026", Decimal("160000000")),
    }
    assert all(fact.line_item_standard != "total_assets" for fact in derived)
    assert all(fact.evidence_label == "derived_calculation" for fact in derived)


def test_validation_covers_tieouts_and_not_testable_states() -> None:
    assert (
        validate_balance_sheet(
            assets=Decimal("100"), liabilities=Decimal("40"), equity=Decimal("60")
        ).validation_result
        == "PASS"
    )
    assert (
        validate_balance_sheet(
            assets=Decimal("101"), liabilities=Decimal("40"), equity=Decimal("60")
        ).validation_result
        == "FAIL"
    )
    assert (
        validate_cash_flow(
            beginning_cash=Decimal("10"),
            operating_cash_flow=Decimal("5"),
            investing_cash_flow=Decimal("-2"),
            financing_cash_flow=Decimal("0"),
            fx_other=Decimal("0"),
            ending_cash=Decimal("13"),
        ).validation_result
        == "PASS"
    )
    assert (
        validate_eps(
            parent_net_income=Decimal("10"),
            weighted_average_shares=Decimal("5"),
            reported_eps=Decimal("2"),
        ).validation_result
        == "PASS"
    )
    assert (
        validate_eps(
            parent_net_income=None, weighted_average_shares=Decimal("5"), reported_eps=Decimal("2")
        ).validation_result
        == "NOT_TESTABLE"
    )
    assert (
        validate_share_data(
            FinancialShareData(
                ticker="1303", weighted_average_basic_shares=Decimal("5"), status="AVAILABLE"
            )
        ).validation_result
        == "PASS"
    )
    assert (
        validate_share_data(FinancialShareData(ticker="1303", status="MISSING")).validation_result
        == "NOT_TESTABLE"
    )

    income = validate_income_statement(
        revenue=Decimal("100"),
        cogs=Decimal("60"),
        gross_profit=Decimal("40"),
        operating_expenses=Decimal("10"),
        operating_income=Decimal("30"),
        pretax_income=Decimal("35"),
        non_operating=Decimal("5"),
        net_income=Decimal("28"),
        income_tax=Decimal("7"),
    )
    assert all(item.validation_result == "PASS" for item in income)


def test_fact_validation_flags_duplicate_and_missing_without_coercion() -> None:
    result = normalize_records(
        [
            _raw(quarter=1, label="Q1-2026", value=None, line="revenue"),
            _raw(quarter=1, label="Q1-2026", value=None, line="revenue"),
        ]
    )
    receipts = validate_financial_facts(result.facts)

    assert any(receipt.validation_result == "FAIL" for receipt in receipts)
    assert any(receipt.validation_result == "PARTIAL" for receipt in receipts)


def test_period_scope_currency_and_unit_mismatches_fail_closed() -> None:
    first = normalize_records(
        [_raw(quarter=1, label="Q1-2026", value="100", line="revenue")]
    ).facts[0]
    wrong_period = first.model_copy(
        update={
            "period_label": "Q2-2026",
            "period_type": "quarterly",
            "ytd_or_standalone": "STANDALONE",
            "fiscal_quarter": 1,
        }
    )
    wrong_currency = first.model_copy(update={"currency": "USD"})
    wrong_scope = first.model_copy(update={"consolidation_scope": "separate"})
    wrong_unit = first.model_copy(update={"normalized_unit": "PERCENT"})

    receipts = validate_period_scope_currency_and_units(
        [first, wrong_period, wrong_currency, wrong_scope, wrong_unit]
    )

    assert any("fiscal_period_label" in receipt.validation_rule for receipt in receipts)
    assert any("currency" in receipt.validation_rule for receipt in receipts)
    assert any("scope" in receipt.validation_rule for receipt in receipts)
    assert any("unit" in receipt.validation_rule for receipt in receipts)


def test_read_only_api_exposes_readiness_but_not_unapproved_values() -> None:
    app = create_app()
    client = TestClient(app)

    coverage = client.get("/api/v2/stocks/1303/financial-coverage")
    status = client.get("/api/v2/stocks/1303/financial-research-status")
    summary = client.get("/api/v2/stocks/1303/financial-summary")

    assert coverage.status_code == 200
    assert coverage.json()["status"] == "MISSING"
    assert status.json()["forecast_available"] is False
    assert summary.json()["metrics"] == []


def test_read_only_api_blocks_values_when_rights_are_unverified() -> None:
    source = FinancialSource(
        source_id="SRC-TEST",
        source_type="filing",
        owner_or_provider="TEST",
        redistribution_rights="UNVERIFIED",
    )
    fact = normalize_records([_raw(quarter=1, label="Q1-2026", value="100", line="revenue")]).facts[
        0
    ]
    app = create_app()
    app.state.financial_research_store = InMemoryFinancialResearchStore([fact], [source])
    response = TestClient(app).get("/api/v2/stocks/1303/financial-summary")

    assert response.status_code == 200
    assert response.json()["status"] == "BLOCKED_RIGHTS"
    assert response.json()["metrics"] == []


def test_read_only_api_allows_values_only_for_explicitly_approved_source() -> None:
    source = FinancialSource(
        source_id="SRC-TEST",
        source_type="filing",
        owner_or_provider="TEST",
        redistribution_rights="APPROVED",
    )
    fact = normalize_records([_raw(quarter=1, label="Q1-2026", value="100", line="revenue")]).facts[
        0
    ]
    app = create_app()
    app.state.financial_research_store = InMemoryFinancialResearchStore([fact], [source])
    response = TestClient(app).get("/api/v2/stocks/1303/financial-summary")

    assert response.status_code == 200
    assert response.json()["status"] == "AVAILABLE"
    assert response.json()["metrics"][0]["value"] == "100000000"


def test_existing_read_api_routes_remain_in_openapi() -> None:
    paths = create_app().openapi()["paths"]

    assert "/api/v2/stocks" in paths
    assert "/api/v2/topics" in paths
    assert "/api/v2/stocks/{symbol}/financial-coverage" in paths
