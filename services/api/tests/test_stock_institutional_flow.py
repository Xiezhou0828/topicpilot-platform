from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from topicpilot_api.market_data.stock_institutional_flow import (
    StockFlowContractError,
    StockFlowLeg,
    StockFlowStatus,
    StockPriceObservation,
    TpexStockInstitutionalFlowProvider,
    TwseStockInstitutionalFlowProvider,
    build_stock_institutional_flow_features,
    expected_weekday_sessions,
    map_provider_facts,
    parse_tpex_stock_institutional_flow,
    parse_twse_stock_institutional_flow,
)
from topicpilot_api.schemas import StockInstitutionalFlowResponse

FIXTURES = Path(__file__).parent / "fixtures"
RETRIEVED_AT = datetime(2026, 9, 16, 8, 0, tzinfo=UTC)


def _payload(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _flip(leg: StockFlowLeg) -> StockFlowLeg:
    return StockFlowLeg(leg.sell, leg.buy, -leg.net)


def test_official_tpe_and_two_payloads_are_normalized_to_share_facts() -> None:
    tpe = parse_twse_stock_institutional_flow(
        _payload("twse_t86_stock_flow.json"), retrieved_at=RETRIEVED_AT
    )[0]
    two = parse_tpex_stock_institutional_flow(
        _payload("tpex_3insti_daily_trading.json"), retrieved_at=RETRIEVED_AT
    )[0]

    assert tpe.market == "TPE"
    assert tpe.foreign.net == Decimal("600")
    assert tpe.dealer.net == Decimal("-160")
    assert tpe.total.net == Decimal("540")
    assert tpe.dealer_self and tpe.dealer_hedge
    assert tpe.total.unit == "SHARES"
    assert two.market == "TWO"
    assert two.trading_date == date(2026, 9, 16)
    assert two.foreign.net == Decimal("500")
    assert two.dealer.net == Decimal("-10")
    assert two.total.net == Decimal("510")
    assert two.foreign_dealer and two.foreign_dealer.net == Decimal("15")


def test_parser_fails_closed_on_net_mismatch() -> None:
    payload = _payload("twse_t86_stock_flow.json")
    assert isinstance(payload, dict)
    payload["data"][0][-1] = "541"

    with pytest.raises(StockFlowContractError, match="TOTAL_MISMATCH"):
        parse_twse_stock_institutional_flow(payload, retrieved_at=RETRIEVED_AT)


def test_mapping_requires_market_and_code_identity() -> None:
    fact = parse_twse_stock_institutional_flow(
        _payload("twse_t86_stock_flow.json"), retrieved_at=RETRIEVED_AT
    )[0]
    mapped, errors = map_provider_facts((fact,), {("TPE", "2330"): "instrument-1"})
    assert mapped[0].instrument_id == "instrument-1"
    assert errors == ()
    unmapped, errors = map_provider_facts((fact,), {})
    assert unmapped == ()
    assert errors == ("MAPPING_ERROR:TPE:2330",)


def test_provider_quality_and_tpex_current_snapshot_are_observable() -> None:
    tpe_provider = TwseStockInstitutionalFlowProvider(
        target_date=date(2026, 9, 16),
        transport=lambda _url, _timeout: json.dumps(_payload("twse_t86_stock_flow.json")).encode(),
        clock=lambda: RETRIEVED_AT,
    )
    tpe_batch = tpe_provider.fetch()
    assert tpe_batch.status is StockFlowStatus.OK
    assert tpe_batch.facts[0].freshness.value == "CURRENT"

    two_provider = TpexStockInstitutionalFlowProvider(
        target_date=date(2026, 9, 17),
        transport=lambda _url, _timeout: json.dumps(
            _payload("tpex_3insti_daily_trading.json")
        ).encode(),
        clock=lambda: RETRIEVED_AT,
    )
    two_batch = two_provider.fetch()
    assert two_batch.status is StockFlowStatus.STALE
    assert two_batch.status_reason == "TPEx_OPENAPI_IS_CURRENT_SNAPSHOT_ONLY"
    assert two_batch.facts[0].freshness.value == "STALE"


def test_windows_use_sessions_and_missing_rows_never_become_zero() -> None:
    base = parse_twse_stock_institutional_flow(
        _payload("twse_t86_stock_flow.json"), retrieved_at=RETRIEVED_AT
    )[0]
    expected = expected_weekday_sessions(date(2026, 8, 20), date(2026, 9, 16))[:20]
    facts = tuple(replace(base, trading_date=day, instrument_id="instrument-1") for day in expected)
    prices = {
        day: StockPriceObservation(day, Decimal(index + 100), Decimal("100000"), "TEST", "ACCEPTED")
        for index, day in enumerate(reversed(expected))
    }
    features = build_stock_institutional_flow_features(
        facts,
        market="TPE",
        instrument_code="2330",
        requested_as_of=expected[0],
        instrument_id="instrument-1",
        expected_sessions=expected,
        prices=prices,
    )
    assert features.five_day.complete
    assert features.five_day.total_net == Decimal("2700")
    assert features.twenty_day.complete
    assert features.streaks["total"].direction == "BUY"
    assert features.streaks["total"].sessions == 20
    assert features.price_flow.price_direction == "UP"
    assert features.price_flow.flow_direction == "BUY"
    assert features.divergence.state == "CONFIRMING"
    assert features.liquidity_relative.state == "AVAILABLE"
    assert not hasattr(features, "institutional_strength_score")

    missing = tuple(fact for index, fact in enumerate(facts) if index != 3)
    incomplete = build_stock_institutional_flow_features(
        missing,
        market="TPE",
        instrument_code="2330",
        requested_as_of=expected[0],
        instrument_id="instrument-1",
        expected_sessions=expected,
    )
    assert incomplete.status is StockFlowStatus.PARTIAL
    assert incomplete.five_day.complete is False
    assert incomplete.five_day.total_net is None
    assert incomplete.streaks["total"].sessions == 3


def test_zero_streak_and_reversal_states_are_explicit() -> None:
    base = parse_twse_stock_institutional_flow(
        _payload("twse_t86_stock_flow.json"), retrieved_at=RETRIEVED_AT
    )[0]
    flat_leg = StockFlowLeg(Decimal(0), Decimal(0), Decimal(0))
    flat = replace(
        base,
        trading_date=date(2026, 9, 16),
        foreign=flat_leg,
        investment_trust=flat_leg,
        dealer=flat_leg,
        total=flat_leg,
    )
    assert (
        build_stock_institutional_flow_features(
            (flat,),
            market="TPE",
            instrument_code="2330",
            requested_as_of=flat.trading_date,
        )
        .streaks["total"]
        .direction
        == "FLAT"
    )

    prior = replace(
        base,
        trading_date=date(2026, 9, 15),
        foreign=_flip(base.foreign),
        investment_trust=_flip(base.investment_trust),
        dealer=_flip(base.dealer),
        total=_flip(base.total),
        foreign_dealer=_flip(base.foreign_dealer) if base.foreign_dealer else None,
        dealer_self=_flip(base.dealer_self) if base.dealer_self else None,
        dealer_hedge=_flip(base.dealer_hedge) if base.dealer_hedge else None,
    )
    current = replace(base, trading_date=date(2026, 9, 16))
    features = build_stock_institutional_flow_features(
        (current, prior),
        market="TPE",
        instrument_code="2330",
        requested_as_of=current.trading_date,
    )
    assert features.reversal.state == "SELL_TO_BUY"


def test_formal_response_schema_accepts_feature_projection() -> None:
    fact = parse_twse_stock_institutional_flow(
        _payload("twse_t86_stock_flow.json"), retrieved_at=RETRIEVED_AT
    )[0]
    features = build_stock_institutional_flow_features(
        (replace(fact, instrument_id="instrument-1"),),
        market="TPE",
        instrument_code="2330",
        requested_as_of=fact.trading_date,
        instrument_id="instrument-1",
    )
    response = StockInstitutionalFlowResponse.model_validate(features.to_dict())
    assert response.unit == "SHARES"
    assert response.today and response.today.instrument_code == "2330"
