from __future__ import annotations

from topicpilot_api.market_data.lineage import build_provider_lineage
from topicpilot_api.reference_check import (
    IdentityContextRow,
    ReferenceRegistrySummary,
    evaluate_reference_preflight,
)


def _registry() -> ReferenceRegistrySummary:
    return ReferenceRegistrySummary(
        version="tw-reference-v1",
        set_count=1,
        active=True,
        currencies=("TWD",),
        timezones=("Asia/Taipei",),
        sessions=(("REGULAR", "TW_MARKET"),),
        trading_status_count=4,
        adjustment_count=2,
        calendar_date_count=24,
    )


def _rows() -> tuple[IdentityContextRow, ...]:
    return (
        IdentityContextRow("2330", "TPE", True, "EQUITY", "TWD", "Asia/Taipei", "TW_MARKET"),
        IdentityContextRow("4979", "TWO", True, "EQUITY", "TWD", "Asia/Taipei", "TW_MARKET"),
    )


def test_reference_preflight_is_ready_without_hard_coded_instrument_count():
    result = evaluate_reference_preflight(
        requested_version="tw-reference-v1",
        expected_market_codes=("TPE", "TWO"),
        active_market_codes=("TPE", "TWO"),
        identity_rows=_rows(),
        duplicate_identities=(),
        registry=_registry(),
        required_session_code="REGULAR",
        required_calendar_code="TW_MARKET",
    )

    assert result["referenceLoadStatus"] == "READY"
    assert result["marketCount"] == 2
    assert result["instrumentCount"] == 2
    assert result["missingInstruments"] == []
    assert result["REFERENCE_VERSION"] == "tw-reference-v1"
    assert result["REFERENCE_LOAD_STATUS"] == "READY"


def test_reference_preflight_fails_closed_for_incomplete_context_and_duplicates():
    result = evaluate_reference_preflight(
        requested_version="tw-reference-v1",
        expected_market_codes=("TPE", "TWO"),
        active_market_codes=("TPE",),
        identity_rows=(
            *_rows(),
            IdentityContextRow("BAD", "TPE", True, "ETF", None, None, None),
        ),
        duplicate_identities=("TPE:2330",),
        registry=_registry(),
        required_session_code="REGULAR",
        required_calendar_code="TW_MARKET",
    )

    assert result["referenceLoadStatus"] == "NOT_READY"
    assert result["missingMarkets"] == ["TWO"]
    assert "TPE:BAD" in result["missingInstruments"]
    assert result["duplicateIdentities"] == ["TPE:2330"]


def test_provider_lineage_reports_adapter_v2_and_authority_without_http():
    result = build_provider_lineage()

    assert result["status"] == "READY"
    assert result["postClose"]["marketBatch"] is True
    official = {item["sourceCode"]: item for item in result["providers"]}
    assert official["TWSE_OFFICIAL_DAILY"]["adapterVersion"] == "twse-official-daily.v2"
    assert official["TPEX_OFFICIAL_DAILY"]["adapterVersion"] == "tpex-official-daily.v2"
    assert official["TWSE_OFFICIAL_DAILY"]["marketBatch"] is True
    assert official["TPEX_OFFICIAL_DAILY"]["marketBatch"] is True
    assert official["YAHOO_CHART_DAILY"]["role"] == "VERIFICATION_ONLY"
    assert official["TAISHIN_TECH_ANALYSIS_INTRADAY"]["role"] == "INTRADAY_ONLY"
