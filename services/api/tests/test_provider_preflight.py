from __future__ import annotations

import inspect
from datetime import date

import pytest

from topicpilot_api.provider_preflight import (
    G2MarketContext,
    G2MarketFailure,
    G2MarketFetch,
    G2PreflightContext,
    evaluate_provider_preflight,
)
from topicpilot_api.provider_preflight_cli import build_parser


def _context(*, target_date_is_session: bool = True) -> G2PreflightContext:
    markets = (
        G2MarketContext(
            "TPE",
            "TWSE_OFFICIAL_DAILY",
            "twse-official-daily.v2",
            "TWSE",
            "Asia/Taipei",
            "TW_MARKET",
            ("2330", "2317"),
        ),
        G2MarketContext(
            "TWO",
            "TPEX_OFFICIAL_DAILY",
            "tpex-official-daily.v2",
            "TPEx",
            "Asia/Taipei",
            "TW_MARKET",
            ("4979", "6510"),
        ),
    )
    return G2PreflightContext(
        reference_result={
            "referenceVersion": "tw-reference-v1",
            "referenceLoadStatus": "READY",
            "referenceActive": "YES",
            "marketCount": 2,
            "instrumentCount": 4,
            "missingMarkets": [],
            "missingInstruments": [],
            "duplicateIdentities": [],
            "missingReferenceContexts": [],
            "calendarDateCount": 24,
        },
        target_date=date(2026, 8, 7),
        target_date_is_session=target_date_is_session,
        target_date_reason=None if target_date_is_session else "TARGET_DATE_WEEKEND",
        markets=markets,
    )


def _pass_results() -> dict[str, G2MarketFetch]:
    return {
        "TPE": G2MarketFetch(
            "TPE",
            "TWSE_OFFICIAL_DAILY",
            "twse-official-daily.v2",
            date(2026, 8, 7),
            frozenset({"2330", "2317"}),
            2,
        ),
        "TWO": G2MarketFetch(
            "TWO",
            "TPEX_OFFICIAL_DAILY",
            "tpex-official-daily.v2",
            date(2026, 8, 7),
            frozenset({"4979", "6510"}),
            2,
        ),
    }


def test_provider_preflight_passes_only_with_official_full_market_coverage():
    result = evaluate_provider_preflight(_context(), _pass_results())

    assert result["gate"] == "G2"
    assert result["status"] == "PASS"
    assert result["readOnly"] is True
    assert result["productionWriteSet"] == []
    assert result["nonReferenceWriteSet"] == []
    assert [market["status"] for market in result["markets"]] == ["PASS", "PASS"]
    assert [market["recordCount"] for market in result["markets"]] == [2, 2]


def test_provider_failure_on_one_market_fails_overall_without_fallback():
    results = _pass_results()
    results["TPE"] = G2MarketFailure("PROVIDER_REQUEST_FAILED")

    result = evaluate_provider_preflight(_context(), results)

    assert result["status"] == "FAIL"
    assert result["fallbackAllowed"] is False
    assert result["markets"][0]["errorCode"] == "PROVIDER_REQUEST_FAILED"
    assert result["markets"][0]["reachable"] is False
    assert result["markets"][1]["status"] == "PASS"


def test_partial_provider_coverage_fails_even_when_payload_is_parsed():
    results = _pass_results()
    results["TWO"] = G2MarketFetch(
        "TWO",
        "TPEX_OFFICIAL_DAILY",
        "tpex-official-daily.v2",
        date(2026, 8, 7),
        frozenset({"4979"}),
        1,
    )

    result = evaluate_provider_preflight(_context(), results)

    market = result["markets"][1]
    assert result["status"] == "FAIL"
    assert market["payloadParsed"] is True
    assert market["dataAvailable"] is True
    assert market["coverageComplete"] is False
    assert market["errorCode"] == "PARTIAL_PROVIDER_COVERAGE"
    assert market["missingInstrumentCount"] == 1
    assert market["missingIdentityCodes"] == ["6510"]
    assert market["extraIdentityCodes"] == []


def test_out_of_scope_provider_identity_is_reported_without_failing_expected_coverage():
    results = _pass_results()
    results["TPE"] = G2MarketFetch(
        "TPE",
        "TWSE_OFFICIAL_DAILY",
        "twse-official-daily.v2",
        date(2026, 8, 7),
        frozenset({"2330", "2317", "6806"}),
        3,
    )

    result = evaluate_provider_preflight(_context(), results)

    market = result["markets"][0]
    assert result["status"] == "PASS"
    assert market["coverageComplete"] is True
    assert market["missingIdentityCodes"] == []
    assert market["extraIdentityCodes"] == ["6806"]
    assert market["extraInstrumentCount"] == 1
    assert market["errorCode"] is None


def test_missing_expected_identity_still_fails_when_provider_has_out_of_scope_identity():
    results = _pass_results()
    results["TPE"] = G2MarketFetch(
        "TPE",
        "TWSE_OFFICIAL_DAILY",
        "twse-official-daily.v2",
        date(2026, 8, 7),
        frozenset({"2330", "6806"}),
        2,
    )

    result = evaluate_provider_preflight(_context(), results)

    market = result["markets"][0]
    assert result["status"] == "FAIL"
    assert market["coverageComplete"] is False
    assert market["missingIdentityCodes"] == ["2317"]
    assert market["extraIdentityCodes"] == ["6806"]
    assert market["errorCode"] == "PARTIAL_PROVIDER_COVERAGE"


def test_empty_market_payload_fails_even_when_provider_is_reachable():
    results = _pass_results()
    results["TPE"] = G2MarketFetch(
        "TPE",
        "TWSE_OFFICIAL_DAILY",
        "twse-official-daily.v2",
        date(2026, 8, 7),
        frozenset(),
        0,
    )

    result = evaluate_provider_preflight(_context(), results)

    market = result["markets"][0]
    assert result["status"] == "FAIL"
    assert market["reachable"] is True
    assert market["payloadParsed"] is True
    assert market["dataAvailable"] is False
    assert market["errorCode"] == "EMPTY_MARKET_PAYLOAD"


def test_parse_failure_is_reported_without_provider_fallback():
    results = _pass_results()
    results["TWO"] = G2MarketFailure(
        "INVALID_PAYLOAD",
        provider_version="tpex-official-daily.v2",
        reachable=True,
        payload_parsed=False,
    )

    result = evaluate_provider_preflight(_context(), results)

    market = result["markets"][1]
    assert result["status"] == "FAIL"
    assert market["reachable"] is True
    assert market["payloadParsed"] is False
    assert market["errorCode"] == "INVALID_PAYLOAD"
    assert result["fallbackAllowed"] is False


def test_target_date_mismatch_and_provider_authority_mismatch_fail_closed():
    results = _pass_results()
    results["TPE"] = G2MarketFetch(
        "TPE",
        "YAHOO_CHART_DAILY",
        "yahoo-chart-daily.v1",
        date(2026, 8, 6),
        frozenset({"2330", "2317"}),
        2,
    )

    result = evaluate_provider_preflight(_context(), results)

    assert result["status"] == "FAIL"
    assert result["markets"][0]["targetDateMatched"] is False
    assert result["markets"][0]["errorCode"] == "PROVIDER_AUTHORITY_MISMATCH"


def test_non_session_context_fails_without_provider_evidence():
    result = evaluate_provider_preflight(
        _context(target_date_is_session=False),
        {
            "TPE": G2MarketFailure("TARGET_DATE_NOT_SESSION"),
            "TWO": G2MarketFailure("TARGET_DATE_NOT_SESSION"),
        },
    )

    assert result["status"] == "FAIL"
    assert result["targetDateIsSession"] is False
    assert all(item["errorCode"] == "TARGET_DATE_NOT_SESSION" for item in result["markets"])


def test_preflight_module_has_no_persistence_or_live_runner_dependency():
    import topicpilot_api.provider_preflight as module

    source = inspect.getsource(module)
    for forbidden in (
        "PostCloseUpdater",
        "LiveCollectorRun",
        "LiveCollectorAttempt",
        "ingest_historical",
        "TopicSnapshotEngine",
        "TopicLifecycleEngine",
        ".commit(",
        ".flush(",
        "session.add(",
    ):
        assert forbidden not in source


def test_provider_preflight_cli_has_only_read_only_arguments():
    parser = build_parser()
    args = parser.parse_args(["--run-date", "2026-08-07"])
    assert args.run_date == date(2026, 8, 7)
    with pytest.raises(SystemExit):
        parser.parse_args(["--run-date", "2026-08-07", "--apply"])
