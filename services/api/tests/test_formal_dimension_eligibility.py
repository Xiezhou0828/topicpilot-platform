from datetime import date
from types import SimpleNamespace

from topicpilot_api.corporate_action_authority import corporate_action_from_mapping
from topicpilot_api.formal_eligibility import (
    Dimension,
    DimensionStatus,
    project_return_dimensions,
)
from topicpilot_api.formal_strength_publication import _return_eligible_facts
from topicpilot_api.previous_close_authority import (
    ComparatorResolution,
    ComparatorStatus,
    ComparatorType,
    resolve_missing_daily_comparator,
)
from topicpilot_api.provider_preflight import (
    G2MarketContext,
    G2MarketFetch,
    G2PreflightContext,
    evaluate_provider_preflight,
)


def _resume_authority(symbol: str = "9999"):
    return corporate_action_from_mapping(
        {
            "symbol": symbol,
            "market": "TPE",
            "actionType": "CAPITAL_REDUCTION_SHARE_EXCHANGE",
            "effectiveFrom": "2026-09-23",
            "effectiveTo": "2026-10-03",
            "resumeDate": "2026-10-05",
            "sourceAuthority": "TWSE_OFFICIAL_REDUCTION",
            "sourceReference": "https://www.twse.com.tw/official/9999",
            "statusMapping": "SUSPENDED",
            "reasonCode": "CAPITAL_REDUCTION_TRADING_SUSPENSION",
            "expectedClose": False,
        }
    )


def test_generic_resume_authority_accounts_only_the_missing_comparator():
    resolution = resolve_missing_daily_comparator(
        symbol="9999",
        market="TPE",
        target=date(2026, 10, 5),
        prior=date(2026, 10, 2),
        authorities=(_resume_authority(),),
    )
    assert resolution.status == ComparatorStatus.ACCOUNTED_UNAVAILABLE
    assert resolution.comparator_type == ComparatorType.CAPITAL_REDUCTION_REFERENCE
    assert resolution.reason_code == "AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE"
    assert resolution.source_reference.endswith("9999")


def test_g2_resume_day_accounts_one_missing_comparator_without_batch_failure(monkeypatch):
    import topicpilot_api.previous_close_authority as comparator_authority

    monkeypatch.setattr(
        comparator_authority,
        "load_corporate_action_authorities",
        lambda: (_resume_authority(),),
    )
    target = date(2026, 10, 5)
    market = G2MarketContext(
        "TPE",
        "TWSE_OFFICIAL_DAILY",
        "twse-official-daily.v2",
        "TWSE",
        "Asia/Taipei",
        "TW_MARKET",
        ("9999", "2330"),
        {"9999": "TPE:9999", "2330": "TPE:2330"},
    )
    from topicpilot_api.previous_close_authority import G2PriceEvidence, PreviousCloseEvidence

    normal_previous = PreviousCloseEvidence(
        "TPE:2330",
        "TPE",
        "2330",
        date(2026, 10, 2),
        9,
        "TWSE_OFFICIAL_DAILY",
        "FORMAL_CANONICAL_CLOSE",
        "canonical-2330",
    )
    prices = {
        "9999": G2PriceEvidence("TPE:9999", "TPE", "9999", target, 10, "a" * 64),
        "2330": G2PriceEvidence(
            "TPE:2330", "TPE", "2330", target, 10, "b" * 64, formal_previous=normal_previous
        ),
    }
    result = evaluate_provider_preflight(
        G2PreflightContext(
            {"referenceLoadStatus": "READY"},
            target,
            True,
            None,
            (market,),
            previous_session=date(2026, 10, 2),
        ),
        {
            "TPE": G2MarketFetch(
                "TPE",
                "TWSE_OFFICIAL_DAILY",
                "twse-official-daily.v2",
                target,
                frozenset(prices),
                2,
                prices=prices,
            )
        },
    )
    assert result["status"] == "PASS"
    evidence = result["markets"][0]
    assert evidence["comparatorAccountedUnavailableCount"] == 1
    assert evidence["previousCloseCoveredCount"] == 1
    decision = next(
        item for item in evidence["instrumentDecisions"] if item["instrumentCode"] == "9999"
    )
    assert decision["comparatorStatus"] == "ACCOUNTED_UNAVAILABLE"
    assert decision["previousClose"] is None
    assert decision["syntheticOrFillUsed"] is False


def test_no_resume_authority_stays_an_unresolved_error():
    resolution = resolve_missing_daily_comparator(
        symbol="9999",
        market="TPE",
        target=date(2026, 10, 5),
        prior=date(2026, 10, 2),
        authorities=(),
    )
    assert resolution.status == ComparatorStatus.ERROR
    assert resolution.reason_code == "MISSING_PREVIOUS_FORMAL_CLOSE"


def test_real_2601_resume_date_is_the_generic_regression_fixture():
    resolution = resolve_missing_daily_comparator(
        symbol="2601",
        market="TPE",
        target=date(2026, 10, 5),
        prior=date(2026, 10, 2),
    )
    assert resolution.status == ComparatorStatus.ACCOUNTED_UNAVAILABLE
    assert resolution.authority_source == "TWSE_OFFICIAL_REDUCTION"
    assert resolution.effective_to == date(2026, 10, 3)
    assert resolution.resume_date == date(2026, 10, 5)


def test_return_dimensions_are_independent_of_benchmark():
    resolution = ComparatorResolution(
        ComparatorStatus.ACCOUNTED_UNAVAILABLE,
        ComparatorType.CAPITAL_REDUCTION_REFERENCE,
        "AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE",
        "TWSE_OFFICIAL_REDUCTION",
        "https://www.twse.com.tw/official",
    )
    dimensions = project_return_dimensions(resolution, current_price_ready=True)
    assert dimensions[Dimension.EOD_PRICE].status == DimensionStatus.READY
    assert dimensions[Dimension.DAILY_COMPARATOR].status == DimensionStatus.ACCOUNTED_UNAVAILABLE
    assert dimensions[Dimension.DAILY_RETURN].status == DimensionStatus.ACCOUNTED_UNAVAILABLE
    assert dimensions[Dimension.BENCHMARK_RETURN].status == DimensionStatus.READY
    assert dimensions[Dimension.RELATIVE_RETURN].status == DimensionStatus.ACCOUNTED_UNAVAILABLE


def test_topic_projection_excludes_only_accounted_return_unavailable_facts():
    allowed = SimpleNamespace(
        raw_fact_payload={
            "dimensionEligibility": {"DAILY_RETURN": {"status": "READY"}}
        }
    )
    excluded = SimpleNamespace(
        raw_fact_payload={
            "dimensionEligibility": {
                "DAILY_RETURN": {
                    "status": "ACCOUNTED_UNAVAILABLE",
                    "reasonCode": "AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE",
                }
            }
        }
    )
    assert _return_eligible_facts((allowed, excluded)) == (allowed,)
