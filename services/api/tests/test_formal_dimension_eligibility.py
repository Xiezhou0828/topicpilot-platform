from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from topicpilot_api.corporate_action_authority import corporate_action_from_mapping
from topicpilot_api.corporate_action_price_authority import (
    corporate_action_price_authority_from_mapping,
)
from topicpilot_api.formal_eligibility import (
    Dimension,
    DimensionStatus,
    project_return_dimensions,
)
from topicpilot_api.formal_strength_publication import _gate, _return_eligible_facts
from topicpilot_api.lifecycle_formal_publication import _formal_gate
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
from topicpilot_api.topic_daily_state import (
    MembershipMember,
    _calculate_daily_change_pct,
    read_canonical_member_facts,
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


def _resume_price_authority(symbol: str = "9999"):
    return corporate_action_price_authority_from_mapping(
        {
            "symbol": symbol,
            "market": "TPE",
            "actionType": "CAPITAL_REDUCTION_SHARE_EXCHANGE",
            "effectiveFrom": "2026-09-23",
            "effectiveTo": "2026-10-03",
            "resumeDate": "2026-10-05",
            "previousTradedCloseDate": "2026-09-22",
            "previousTradedClose": "5.91",
            "comparisonReferenceDate": "2026-10-05",
            "comparisonReference": "7.06",
            "sourceAuthority": "TWSE_OFFICIAL_REDUCTION",
            "sourceReference": "https://www.twse.com.tw/official/price/9999",
            "sourceResponseHash": "a" * 64,
            "previousTradedCloseSource": "TWSE_OFFICIAL_DAILY",
            "previousTradedCloseSourceReference": "https://www.twse.com.tw/official/daily/9999",
            "previousTradedCloseResponseHash": "b" * 64,
            "detailSourceReference": "https://www.twse.com.tw/official/detail/9999",
            "detailResponseHash": "c" * 64,
            "finality": "FINAL",
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


def test_generic_price_authority_keeps_provenance_distinct_from_comparison_reference():
    resolution = resolve_missing_daily_comparator(
        symbol="9999",
        market="TPE",
        target=date(2026, 10, 5),
        prior=date(2026, 10, 2),
        authorities=(_resume_authority(),),
        price_authorities=(_resume_price_authority(),),
    )
    assert resolution.status == ComparatorStatus.READY
    assert resolution.previous_traded_close == Decimal("5.91")
    assert resolution.previous_traded_close_date == date(2026, 9, 22)
    assert resolution.comparison_reference == Decimal("7.06")
    assert resolution.comparison_reference_date == date(2026, 10, 5)
    assert resolution.previous_traded_close != resolution.comparison_reference


def test_price_authority_conflict_fails_closed_without_selecting_a_value():
    resolution = resolve_missing_daily_comparator(
        symbol="9999",
        market="TPE",
        target=date(2026, 10, 5),
        prior=date(2026, 10, 2),
        authorities=(_resume_authority(),),
        price_authorities=(_resume_price_authority(), _resume_price_authority()),
    )
    assert resolution.status == ComparatorStatus.ERROR
    assert resolution.reason_code == "CORPORATE_ACTION_PRICE_AUTHORITY_CONFLICT"
    assert resolution.comparison_reference is None


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
    assert resolution.status == ComparatorStatus.READY
    assert resolution.reason_code == "AUTHORIZED_CORPORATE_ACTION_COMPARISON_REFERENCE"
    assert resolution.authority_source == "TWSE_OFFICIAL_REDUCTION"
    assert resolution.effective_to == date(2026, 10, 3)
    assert resolution.resume_date == date(2026, 10, 5)
    assert resolution.previous_traded_close == Decimal("5.91")
    assert resolution.comparison_reference == Decimal("7.06")


def test_real_2601_provider_preflight_uses_official_reference_not_bid_side_value():
    from topicpilot_api.previous_close_authority import G2PriceEvidence

    target = date(2026, 10, 5)
    market = G2MarketContext(
        "TPE",
        "TWSE_OFFICIAL_DAILY",
        "twse-official-daily.v2",
        "TWSE",
        "Asia/Taipei",
        "TW_MARKET",
        ("2601",),
        {"2601": "TPE:2601"},
    )
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
                frozenset({"2601"}),
                1,
                prices={
                    "2601": G2PriceEvidence(
                        "TPE:2601", "TPE", "2601", target, Decimal("6.45"), "d" * 64
                    )
                },
            )
        },
    )
    decision = result["markets"][0]["instrumentDecisions"][0]
    assert result["status"] == "PASS"
    assert decision["comparatorStatus"] == "READY"
    assert decision["comparatorAuthority"]["comparisonReference"] == "7.06"
    assert decision["comparatorAuthority"]["previousTradedClose"] == "5.91"
    assert decision["comparatorAuthority"]["comparisonReference"] != "6.44"


def test_resume_day_daily_return_uses_reference_not_last_traded_close():
    comparator = resolve_missing_daily_comparator(
        symbol="2601",
        market="TPE",
        target=date(2026, 10, 5),
        prior=date(2026, 10, 2),
    )
    change = _calculate_daily_change_pct(
        close=Decimal("6.45"), comparator=comparator, previous_close=None
    )
    assert change == (Decimal("6.45") - Decimal("7.06")) / Decimal("7.06") * Decimal("100")


def test_corporate_action_price_authority_must_match_the_authorized_resume_interval():
    resolution = resolve_missing_daily_comparator(
        symbol="9999",
        market="TPE",
        target=date(2026, 10, 6),
        prior=date(2026, 10, 5),
        authorities=(_resume_authority(),),
        price_authorities=(_resume_price_authority(),),
    )
    assert resolution.status == ComparatorStatus.ERROR
    assert resolution.reason_code == "MISSING_PREVIOUS_FORMAL_CLOSE"


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


class _EmptyCanonicalSession:
    """Minimal read-only session fixture for the authority fallback test."""

    def execute(self, _statement, _params):
        return self

    def mappings(self):
        return self

    def all(self):
        return []

    def __iter__(self):
        return iter(())


def test_6173_suspension_authority_is_formally_accounted_without_a_fake_price():
    from uuid import uuid4

    member = MembershipMember(
        instrument_id=uuid4(),
        instrument_code="6173",
        market_code="TWO",
        relation_type="RELATED",
        relation_version="test-v1",
        identity_continuity="FORMAL_TEST",
    )
    fact = read_canonical_member_facts(
        _EmptyCanonicalSession(), date(2026, 10, 7), (member,)
    )[0]

    assert fact.fact_state == "NO_TRADE"
    assert fact.close is None
    assert fact.change_pct is None
    assert fact.raw_fact_payload["tradingStatus"] == "SUSPENDED"
    assert fact.raw_fact_payload["tradingStatusReason"] == "CAPITAL_REDUCTION_TRADING_SUSPENSION"
    assert fact.raw_fact_payload["dimensionEligibility"]["DAILY_RETURN"] == {
        "dimension": "DAILY_RETURN",
        "status": "ACCOUNTED_UNAVAILABLE",
        "reasonCode": "AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE",
        "authoritySource": "TPEX_OFFICIAL_REDUCTION",
        "sourceReference": "https://mops.twse.com.tw/mops/web/t05st01",
        "comparatorType": "CAPITAL_REDUCTION_REFERENCE",
    }
    assert fact.raw_fact_payload["close"] is None


def _authorized_no_trade_fact(instrument_id: str = "no-trade"):
    return SimpleNamespace(
        instrument_id=instrument_id,
        fact_state="NO_TRADE",
        change_pct=None,
        fact_identity="fact:no-trade",
        fact_hash="f" * 64,
        structural_role="RELATED",
        role_source="FORMAL_TEST",
        raw_fact_payload={
            "dimensionEligibility": {
                "DAILY_RETURN": {
                    "status": "ACCOUNTED_UNAVAILABLE",
                    "reasonCode": "AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE",
                }
            }
        },
    )


def _formal_snapshot(stock_count: int = 2):
    return SimpleNamespace(
        id="snapshot-6173",
        snapshot_identity="formal:test:2026-10-07:hash",
        lineage_hash="l" * 64,
        correction_sequence=0,
        membership_snapshot_id="membership:test",
        membership_snapshot_hash="m" * 64,
        relation_version="test-v1",
        source_artifact_id="artifact:test",
        source_artifact_hash="a" * 64,
        supersedes_snapshot_id=None,
        superseded_by_snapshot_id=None,
        data_status="COMPLETE",
        stock_count=stock_count,
        observed_stock_count=stock_count - 1,
    )


def test_strength_and_lifecycle_gates_accept_authorized_no_trade_dimension_gap():
    observed = SimpleNamespace(
        instrument_id="observed",
        fact_state="OBSERVED",
        change_pct=Decimal("1"),
        fact_identity="fact:observed",
        fact_hash="o" * 64,
        structural_role="RELATED",
        role_source="FORMAL_TEST",
        raw_fact_payload={"dimensionEligibility": {"DAILY_RETURN": {"status": "READY"}}},
    )
    no_trade = _authorized_no_trade_fact()
    snapshot = _formal_snapshot()

    assert _gate(snapshot, [observed, no_trade]).passed is True
    assert _formal_gate(snapshot, [observed, no_trade]).passed is True


def test_unexplained_no_trade_does_not_pass_formal_gates():
    observed = SimpleNamespace(
        instrument_id="observed",
        fact_state="OBSERVED",
        change_pct=Decimal("1"),
        fact_identity="fact:observed",
        fact_hash="o" * 64,
        structural_role="RELATED",
        role_source="FORMAL_TEST",
        raw_fact_payload={"dimensionEligibility": {"DAILY_RETURN": {"status": "READY"}}},
    )
    unexplained = SimpleNamespace(
        **{
            **_authorized_no_trade_fact().__dict__,
            "raw_fact_payload": {"dimensionEligibility": {}},
        }
    )
    snapshot = _formal_snapshot()

    assert _gate(snapshot, [observed, unexplained]).passed is False
    assert _formal_gate(snapshot, [observed, unexplained]).passed is False
