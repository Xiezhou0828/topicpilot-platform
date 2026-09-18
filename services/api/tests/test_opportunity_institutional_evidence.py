from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from topicpilot_api.market_data.stock_institutional_flow import (
    StockFlowLeg,
    StockPriceObservation,
    build_stock_institutional_flow_features,
    expected_weekday_sessions,
    parse_tpex_stock_institutional_flow,
    parse_twse_stock_institutional_flow,
)
from topicpilot_api.opportunity_shadow_read import (
    FixtureOpportunityReadProvider,
    OpportunityShadowReadService,
)
from topicpilot_api.schemas import OpportunityInstitutionalEvidenceRead
from topicpilot_api.topic_engine.opportunity_contract import (
    build_frontend_opportunity_fixtures,
)
from topicpilot_api.topic_engine.opportunity_evidence import (
    CanonicalOHLCVBar,
    build_breakout_evidence,
)
from topicpilot_api.topic_engine.opportunity_institutional_evidence import (
    adapt_fund_b_institutional_flow,
)

FIXTURES = Path(__file__).parent / "fixtures"
RETRIEVED_AT = datetime(2026, 9, 16, 8, 0, tzinfo=UTC)
TARGET_DATE = date(2026, 9, 16)


def _payload(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _tpe_features(*, complete: bool = True, target: date = TARGET_DATE):
    base = parse_twse_stock_institutional_flow(
        _payload("twse_t86_stock_flow.json"), retrieved_at=RETRIEVED_AT
    )[0]
    expected = expected_weekday_sessions(date(2026, 7, 15), target)[:20]
    facts = tuple(
        replace(base, trading_date=day, instrument_id="instrument-1")
        for index, day in enumerate(expected)
        if complete or index != 3
    )
    prices = {
        day: StockPriceObservation(day, Decimal(index + 100), Decimal("100000"), "TEST", "ACCEPTED")
        for index, day in enumerate(reversed(expected))
    }
    return build_stock_institutional_flow_features(
        facts,
        market="TPE",
        instrument_code="2330",
        requested_as_of=target,
        instrument_id="instrument-1",
        expected_sessions=expected,
        prices=prices,
    )


def _adapt(flow, *, symbol: str = "2330", instrument_id: str | None = "instrument-1"):
    return adapt_fund_b_institutional_flow(
        flow,
        opportunity_as_of=TARGET_DATE,
        instrument_id=instrument_id,
        symbol=symbol,
        market="TPE",
    )


def test_complete_tpe_evidence_is_serializable_and_preserves_fund_b_dimensions() -> None:
    evidence = _adapt(_tpe_features())
    model = OpportunityInstitutionalEvidenceRead.model_validate(evidence)

    assert model.availability == "OK"
    assert model.requested_date == TARGET_DATE
    assert model.trading_date == TARGET_DATE
    assert model.today and model.today.total.net == Decimal("540")
    assert model.rolling["fiveDay"].complete is True
    assert model.rolling["twentyDay"].complete is True
    assert model.streaks["total"].direction == "BUY"
    assert model.reversal.state == "NONE"
    assert model.price_flow.flow_direction == "BUY"
    assert model.divergence.state == "CONFIRMING"
    assert model.liquidity_relative.state == "AVAILABLE"
    assert model.alignment.classification == "POLICY_DECISION_REQUIRED"
    assert model.alignment.selection_effect == "NONE"
    assert "institutionalStrengthScore" not in evidence


def test_two_current_snapshot_keeps_canonical_partial_semantics() -> None:
    base = parse_tpex_stock_institutional_flow(
        _payload("tpex_3insti_daily_trading.json"), retrieved_at=RETRIEVED_AT
    )[0]
    features = build_stock_institutional_flow_features(
        (replace(base, instrument_id="instrument-2"),),
        market="TWO",
        instrument_code=base.instrument_code,
        requested_as_of=TARGET_DATE,
        instrument_id="instrument-2",
    )
    canonical = features.to_dict()
    canonical["status"] = "PARTIAL"
    canonical["statusReason"] = (
        "Provider is current-snapshot-only; historical session windows cannot be claimed "
        "without a persisted capture series."
    )
    evidence = adapt_fund_b_institutional_flow(
        canonical,
        opportunity_as_of=TARGET_DATE,
        instrument_id="instrument-2",
        symbol=base.instrument_code,
        market="TWO",
    )

    assert evidence["availability"] == "PARTIAL"
    assert evidence["statusReason"].startswith("Provider is current-snapshot-only")
    assert evidence["today"]["total"]["net"] == 510
    assert evidence["rolling"]["fiveDay"]["complete"] is False
    assert evidence["rolling"]["fiveDay"]["totalNet"] is None
    assert OpportunityInstitutionalEvidenceRead.model_validate(evidence).market == "TWO"


def test_unavailable_states_are_explicit_and_missing_is_not_zero() -> None:
    no_data = _adapt(None)
    assert no_data["availability"] == "NO_DATA"
    assert no_data["today"] is None
    assert no_data["rolling"]["fiveDay"]["totalNet"] is None

    stale_features = build_stock_institutional_flow_features(
        (
            replace(
                parse_twse_stock_institutional_flow(
                    _payload("twse_t86_stock_flow.json"), retrieved_at=RETRIEVED_AT
                )[0],
                trading_date=date(2026, 9, 15),
                instrument_id="instrument-1",
            ),
        ),
        market="TPE",
        instrument_code="2330",
        requested_as_of=TARGET_DATE,
        instrument_id="instrument-1",
        expected_sessions=(TARGET_DATE,),
    )
    stale = _adapt(stale_features)
    assert stale["availability"] == "STALE"
    assert stale["freshness"] == "STALE"
    assert stale["today"] is None

    explicit_zero = replace(
        parse_twse_stock_institutional_flow(
            _payload("twse_t86_stock_flow.json"), retrieved_at=RETRIEVED_AT
        )[0],
        trading_date=TARGET_DATE,
        instrument_id="instrument-1",
        foreign=StockFlowLeg(Decimal(0), Decimal(0), Decimal(0)),
        investment_trust=StockFlowLeg(Decimal(0), Decimal(0), Decimal(0)),
        dealer=StockFlowLeg(Decimal(0), Decimal(0), Decimal(0)),
        total=StockFlowLeg(Decimal(0), Decimal(0), Decimal(0)),
    )
    zero = _adapt(
        build_stock_institutional_flow_features(
            (explicit_zero,),
            market="TPE",
            instrument_code="2330",
            requested_as_of=TARGET_DATE,
            instrument_id="instrument-1",
        )
    )
    assert zero["today"]["total"]["net"] == 0
    assert zero["availability"] == "PARTIAL"


def test_mapping_future_and_source_errors_fail_closed_without_collapsing_status() -> None:
    malformed = _adapt({})
    assert malformed["availability"] == "MAPPING_ERROR"
    assert malformed["canonicalEvidence"] is None

    future = _tpe_features().to_dict()
    future["today"]["tradingDate"] = date(2026, 9, 17)
    rejected = _adapt(future)
    assert rejected["availability"] == "MAPPING_ERROR"
    assert rejected["statusReason"] == "FUTURE_TRADING_SESSION_REJECTED"
    assert rejected["today"] is None
    assert rejected["canonicalEvidence"] is None

    provider_error = _tpe_features().to_dict()
    provider_error.update(
        {
            "status": "PROVIDER_UNAVAILABLE",
            "freshness": "UNKNOWN",
            "statusReason": "upstream timeout",
            "today": None,
            "sessions": [],
        }
    )
    error = _adapt(provider_error)
    assert error["availability"] == "PROVIDER_UNAVAILABLE"
    assert error["statusReason"] == "upstream timeout"
    assert error["availability"] != "NO_DATA"


def test_incomplete_history_preserves_canonical_null_windows_and_derived_states() -> None:
    evidence = _adapt(_tpe_features(complete=False))
    assert evidence["availability"] == "PARTIAL"
    assert evidence["rolling"]["twentyDay"]["complete"] is False
    assert evidence["rolling"]["twentyDay"]["totalNet"] is None
    assert evidence["streaks"]["total"]["status"] == "OK"
    assert evidence["priceFlow"]["status"] == "OK"


def test_opportunity_enrichment_does_not_change_candidate_set_rank_or_eligibility() -> None:
    canonical = _tpe_features(target=build_frontend_opportunity_fixtures()[0].as_of).to_dict()
    fixtures = build_frontend_opportunity_fixtures()
    candidate = fixtures[0]
    for item in (canonical.get("today"), *(canonical.get("sessions") or ())):
        if isinstance(item, dict):
            item["instrumentId"] = candidate.instrument_id
            item["instrumentCode"] = candidate.symbol
    canonical["instrumentId"] = candidate.instrument_id
    canonical["instrumentCode"] = candidate.symbol
    evidence = adapt_fund_b_institutional_flow(
        canonical,
        opportunity_as_of=candidate.as_of,
        instrument_id=candidate.instrument_id,
        symbol=candidate.symbol,
        market="TPE",
    )
    enriched = replace(candidate, institutional_evidence=evidence)
    baseline_service = OpportunityShadowReadService(FixtureOpportunityReadProvider(fixtures))
    enriched_service = OpportunityShadowReadService(
        FixtureOpportunityReadProvider((enriched, *fixtures[1:]))
    )
    baseline = baseline_service.list_opportunities(limit=100)
    after = enriched_service.list_opportunities(limit=100)

    def identity(rows: dict) -> list[tuple[object, ...]]:
        return [
            (
                card["opportunityId"],
                card["rank"],
                card["rankScore"],
                card["eligibility"],
                card["opportunityState"],
            )
            for card in rows["opportunities"]
        ]

    assert identity(after) == identity(baseline)
    enriched_card = next(
        card for card in after["opportunities"] if card["instrumentId"] == candidate.instrument_id
    )
    assert enriched_card["institutionalEvidence"]["availability"] == "OK"
    assert enriched_card["institutionalEvidence"]["alignment"]["selectionEffect"] == "NONE"


def test_frozen_breakout_regression_for_two_6173_uses_close_not_intraday_high() -> None:
    start = date(2026, 8, 17)
    prior = tuple(
        CanonicalOHLCVBar(
            start + timedelta(days=index),
            320,
            321,
            319,
            320,
            100000,
        )
        for index in range(20)
    )
    current_date = start + timedelta(days=20)
    current = CanonicalOHLCVBar(current_date, 320, 323, 314, 315, 100000)
    breakout = build_breakout_evidence((*prior, current), as_of=current_date)

    assert breakout.assessment.reason_codes == ("NO_BREAKOUT",)
    assert breakout.reference_price == 321
    assert breakout.current_price == 315
    assert not 315 > 321


def test_institutional_evidence_is_only_a_read_model_extension() -> None:
    original = build_frontend_opportunity_fixtures()[0]
    payload = original.as_dict()
    assert payload["institutionalEvidence"] is None
    enriched = replace(original, institutional_evidence=_adapt(_tpe_features()))
    assert enriched.as_dict()["institutionalEvidence"]["alignment"]["classification"] == (
        "POLICY_DECISION_REQUIRED"
    )
    assert enriched.opportunity_state == original.opportunity_state
    assert enriched.eligibility == original.eligibility
    assert enriched.rank_score == original.rank_score
