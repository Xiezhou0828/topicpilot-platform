from __future__ import annotations

import inspect
from datetime import date

import pytest

from topicpilot_api.instrument_universe import (
    InstrumentLifecycle,
    InstrumentUniverseRow,
)
from topicpilot_api.market_semantics import (
    G3MarketContext,
    G3MarketFetch,
    G3PreflightContext,
    build_g3_preflight_context,
    evaluate_market_semantics,
)
from topicpilot_api.market_semantics_cli import build_parser
from topicpilot_api.provider_preflight import (
    G2MarketContext,
    G2PreflightContext,
)

RUN_DATE = date(2026, 8, 13)


def _market(
    code: str,
    expected: tuple[str, ...],
    *,
    invalid: tuple[str, ...] = (),
    duplicates: tuple[str, ...] = (),
    unexpected: tuple[str, ...] = (),
) -> G3MarketContext:
    return G3MarketContext(
        market_code=code,
        provider_authority=("TWSE_OFFICIAL_DAILY" if code == "TPE" else "TPEX_OFFICIAL_DAILY"),
        provider_version=("twse-official-daily.v2" if code == "TPE" else "tpex-official-daily.v2"),
        exchange_code=("TWSE" if code == "TPE" else "TPEx"),
        timezone="Asia/Taipei",
        calendar_code="TW_MARKET",
        expected_instrument_codes=expected,
        invalid_lifecycle_identity_codes=invalid,
        duplicate_expected_identity_codes=duplicates,
        unexpected_market_codes=unexpected,
    )


def _context(
    *,
    tpe: tuple[str, ...] = ("2330", "2317"),
    two: tuple[str, ...] = ("4979", "6510"),
    fallback_used: bool = False,
) -> G3PreflightContext:
    return G3PreflightContext(
        reference_result={
            "referenceVersion": "tw-reference-v1-rollover",
            "referenceLoadStatus": "READY",
        },
        target_date=RUN_DATE,
        target_date_is_session=True,
        target_date_reason=None,
        markets=(_market("TPE", tpe), _market("TWO", two)),
        fallback_used=fallback_used,
    )


def _fetch(context: G3MarketContext, codes: set[str], *, data_date: date = RUN_DATE):
    return G3MarketFetch(
        market_code=context.market_code,
        provider_authority=context.provider_authority,
        provider_version=context.provider_version,
        data_date=data_date,
        record_codes=frozenset(codes),
        record_count=len(codes),
    )


def _pass_results(context: G3PreflightContext):
    return {
        market.market_code: _fetch(market, set(market.expected_instrument_codes))
        for market in context.markets
    }


def test_canonical_20260813_case_passes_with_expected_313_and_193():
    context = _context(
        tpe=tuple(f"TPE{i}" for i in range(313)),
        two=tuple(f"TWO{i}" for i in range(193)),
    )
    result = evaluate_market_semantics(context, _pass_results(context))

    assert result["operation"] == "G3_MARKET_SEMANTICS_CHECK"
    assert result["status"] == "PASS"
    assert result["readOnly"] is True
    assert result["productionWriteSet"] == []
    assert result["markets"]["TPE"]["expectedEligibleCount"] == 313
    assert result["markets"]["TPE"]["semanticEligibleCount"] == 313
    assert result["markets"]["TWO"]["expectedEligibleCount"] == 193


def test_6806_delisted_on_20260813_is_not_expected_but_physical_row_is_preserved():
    g2_context = G2PreflightContext(
        reference_result={"referenceVersion": "tw-reference-v1", "referenceLoadStatus": "READY"},
        target_date=RUN_DATE,
        target_date_is_session=True,
        target_date_reason=None,
        markets=(
            G2MarketContext(
                "TPE",
                "TWSE_OFFICIAL_DAILY",
                "twse-official-daily.v2",
                "TWSE",
                "Asia/Taipei",
                "TW_MARKET",
                (),
            ),
            G2MarketContext(
                "TWO",
                "TPEX_OFFICIAL_DAILY",
                "tpex-official-daily.v2",
                "TPEx",
                "Asia/Taipei",
                "TW_MARKET",
                (),
            ),
        ),
        universe_rows=(
            InstrumentUniverseRow(
                "TPE",
                "6806",
                "EQUITY",
                True,
                lifecycle_events=(
                    InstrumentLifecycle("DELISTED", date(2026, 6, 23), evidence_id="evidence-6806"),
                ),
            ),
            InstrumentUniverseRow("TPE", "2330", "EQUITY", True),
            InstrumentUniverseRow("TWO", "4979", "EQUITY", True),
        ),
    )
    context = build_g3_preflight_context(g2_context)
    result = evaluate_market_semantics(context, _pass_results(context))

    assert result["status"] == "PASS"
    assert result["markets"]["TPE"]["expectedEligibleCount"] == 1
    assert result["markets"]["TPE"]["missingEligibleIdentityCodes"] == []
    assert "6806" not in context.markets[0].expected_instrument_codes


def test_missing_expected_identity_fails():
    context = _context()
    results = _pass_results(context)
    results["TPE"] = _fetch(context.markets[0], {"2330"})

    result = evaluate_market_semantics(context, results)

    assert result["status"] == "FAIL"
    assert result["markets"]["TPE"]["missingEligibleIdentityCodes"] == ["2317"]


def test_wrong_market_mapping_fails():
    context = _context()
    results = _pass_results(context)
    results["TPE"] = G3MarketFetch(
        market_code="TWO",
        provider_authority="TPEX_OFFICIAL_DAILY",
        provider_version="tpex-official-daily.v2",
        data_date=RUN_DATE,
        record_codes=frozenset(context.markets[0].expected_instrument_codes),
        record_count=2,
    )

    result = evaluate_market_semantics(context, results)

    assert result["status"] == "FAIL"
    assert "TPE:MARKET_IDENTITY_MISMATCH" in result["failureReasons"]


def test_duplicate_expected_identity_fails_closed():
    context = _context()
    duplicate_market = _market("TPE", ("2330", "2317"), duplicates=("2330",))
    context = G3PreflightContext(
        context.reference_result,
        context.target_date,
        context.target_date_is_session,
        context.target_date_reason,
        (duplicate_market, context.markets[1]),
    )

    result = evaluate_market_semantics(context, _pass_results(context))

    assert result["status"] == "FAIL"
    assert "TPE:DUPLICATE_EXPECTED_IDENTITY:2330" in result["failureReasons"]


def test_provider_data_date_mismatch_fails():
    context = _context()
    results = _pass_results(context)
    results["TPE"] = _fetch(
        context.markets[0],
        set(context.markets[0].expected_instrument_codes),
        data_date=date(2026, 8, 12),
    )

    result = evaluate_market_semantics(context, results)

    assert result["status"] == "FAIL"
    assert result["markets"]["TPE"]["dataDate"] == "2026-08-12"
    assert "TPE:PROVIDER_DATE_MISMATCH" in result["failureReasons"]


def test_fallback_used_fails_even_with_complete_official_coverage():
    context = _context(fallback_used=True)

    result = evaluate_market_semantics(context, _pass_results(context))

    assert result["status"] == "FAIL"
    assert result["fallbackUsed"] is True
    assert "FALLBACK_USED" in result["failureReasons"]


def test_provider_extras_are_diagnostic_only():
    context = _context()
    results = _pass_results(context)
    results["TPE"] = _fetch(context.markets[0], {"2330", "2317", "ETF-1", "WARRANT-1"})

    result = evaluate_market_semantics(context, results)

    assert result["status"] == "PASS"
    assert result["markets"]["TPE"]["outOfScopeProviderIdentityCount"] == 2


def test_malformed_lifecycle_fails_closed():
    context = _context()
    invalid_market = _market("TPE", ("2330", "2317"), invalid=("2330",))
    context = G3PreflightContext(
        context.reference_result,
        context.target_date,
        context.target_date_is_session,
        context.target_date_reason,
        (invalid_market, context.markets[1]),
    )

    result = evaluate_market_semantics(context, _pass_results(context))

    assert result["status"] == "FAIL"
    assert "TPE:INVALID_LIFECYCLE:2330" in result["failureReasons"]


def test_repeated_evaluation_is_deterministic_and_has_zero_write_set():
    context = _context()
    results = _pass_results(context)

    first = evaluate_market_semantics(context, results)
    second = evaluate_market_semantics(context, results)

    assert first == second
    assert first["productionWriteSet"] == []


def test_g3_cli_requires_explicit_reference_version_and_has_no_mutation_flags():
    args = build_parser().parse_args(
        ["--run-date", "2026-08-13", "--reference-version", "tw-reference-v1"]
    )
    assert args.run_date == RUN_DATE
    assert args.reference_version == "tw-reference-v1"
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            ["--run-date", "2026-08-13", "--reference-version", "tw-reference-v1", "--apply"]
        )


def test_g3_module_has_no_persistence_or_live_runner_dependency():
    import topicpilot_api.market_semantics as module

    source = inspect.getsource(module)
    for forbidden in (
        "PostCloseUpdater",
        "LiveCollectorRun",
        "TopicSnapshotEngine",
        "TopicLifecycleEngine",
        "session.add(",
        ".commit(",
        ".flush(",
    ):
        assert forbidden not in source
