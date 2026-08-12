from __future__ import annotations

import pytest

from topicpilot_api.topic_engine import (
    EVALUATION_BLOCKED,
    EVALUATION_DEFERRED,
    EVALUATION_READY,
    FAIL,
    PASS,
    SHADOW_ONLY,
    STATE_INVALIDATED,
    STATE_SELECTED,
    STATE_STRENGTHENING,
    STATE_WAITING_RETEST,
    STATE_WARMING,
    UNKNOWN,
    WAIT,
    ChipConfirmationFacts,
    EntryQualityFacts,
    OpportunityShadowError,
    OpportunityShadowInput,
    RiskGateFacts,
    StageAssessment,
    StockOpportunityContext,
    TechnicalStructureFacts,
    TopicOpportunityContext,
    build_opportunity_shadow,
)


def _input(
    *,
    price: float | None = 102.0,
    ma20: float | None = 100.0,
    sufficient_ohlcv: bool | None = True,
    technical: TechnicalStructureFacts | None = None,
    risk: StageAssessment | None = None,
    entry: EntryQualityFacts | None = None,
    topic: StageAssessment | None = None,
    warming: bool = False,
    previous: str | None = None,
) -> OpportunityShadowInput:
    return OpportunityShadowInput(
        topic=TopicOpportunityContext(
            "topic-1",
            "AI servers",
            topic or StageAssessment(PASS),
            grade="A",
            lifecycle="主升",
            warming_candidate=warming,
        ),
        stock=StockOpportunityContext(
            "instrument-1",
            "2330",
            "Example",
            "TPE",
            "topic-1",
            price,
            ma20,
            98.0,
            sufficient_ohlcv,
        ),
        technical=technical
        or TechnicalStructureFacts(True, True, True, True, True, True, True, True),
        risk=RiskGateFacts(risk or StageAssessment(PASS)),
        entry=entry or EntryQualityFacts(PASS, price, 100.0),
        chip=ChipConfirmationFacts(StageAssessment(UNKNOWN, ("CHIP_NOT_AVAILABLE",))),
        previously_tracked_state=previous,
    )


def test_shadow_selected_with_structured_evidence_and_support_distance() -> None:
    result = build_opportunity_shadow(_input())

    assert result.publication_status == SHADOW_ONLY
    assert result.evaluation_status == EVALUATION_READY
    assert result.state == STATE_SELECTED
    assert "OPPORTUNITY_SHADOW_SELECTED" in result.reason_codes
    payload = result.as_dict()
    assert payload["evidence"]["whySelected"]
    support = next(
        item
        for item in payload["evidence"]["whySelected"]
        if item["code"] == "SUPPORT_DISTANCE_PCT"
    )
    assert support["value"] == pytest.approx(2.0)


def test_price_below_20ma_is_a_shadow_hard_gate() -> None:
    result = build_opportunity_shadow(_input(price=99.0))

    assert result.evaluation_status == EVALUATION_BLOCKED
    assert result.state is None
    assert result.reason_codes == ("PRICE_BELOW_20MA",)
    assert any(item.code == "PRICE_AT_OR_ABOVE_20MA" for item in result.evidence.risks)


def test_topic_failure_invalidates_a_previously_tracked_shadow() -> None:
    result = build_opportunity_shadow(
        _input(topic=StageAssessment(FAIL, ("TOPIC_NO_LONGER_QUALIFIED",)), previous=STATE_SELECTED)
    )

    assert result.evaluation_status == EVALUATION_BLOCKED
    assert result.state == STATE_INVALIDATED


def test_tracked_candidate_becomes_invalidated_when_20ma_gate_fails() -> None:
    result = build_opportunity_shadow(_input(price=99.0, previous=STATE_SELECTED))

    assert result.state == STATE_INVALIDATED
    assert result.evaluation_status == EVALUATION_BLOCKED


def test_missing_ohlcv_or_20ma_fails_closed_without_inventing_values() -> None:
    missing_ohlcv = build_opportunity_shadow(_input(sufficient_ohlcv=None))
    missing_ma = build_opportunity_shadow(_input(ma20=None))

    assert missing_ohlcv.evaluation_status == EVALUATION_DEFERRED
    assert missing_ohlcv.reason_codes == ("STOCK_OHLCV_SUFFICIENCY_UNAVAILABLE",)
    assert missing_ma.evaluation_status == EVALUATION_DEFERRED
    assert missing_ma.reason_codes == ("STOCK_20MA_UNAVAILABLE",)


def test_technical_failure_preserves_warming_exception_without_direct_selection() -> None:
    facts = TechnicalStructureFacts(True, True, True, False, True, True, True, True)

    regular = build_opportunity_shadow(_input(technical=facts))
    warming = build_opportunity_shadow(_input(technical=facts, warming=True))

    assert regular.state == STATE_STRENGTHENING
    assert warming.state == STATE_WARMING
    assert regular.evaluation_status == EVALUATION_READY
    assert regular.state != STATE_SELECTED


def test_entry_wait_routes_to_retest_without_a_frozen_distance_threshold() -> None:
    result = build_opportunity_shadow(
        _input(entry=EntryQualityFacts(WAIT, 120.0, 100.0, reason_codes=("CHASE_RISK",)))
    )

    assert result.state == STATE_WAITING_RETEST
    assert result.evaluation_status == EVALUATION_READY
    assert any(
        item.code == "SUPPORT_DISTANCE_PCT" and item.value == 20.0
        for item in result.evidence.why_selected
    )


def test_risk_failure_is_blocking_and_uses_previous_state_for_invalidation() -> None:
    result = build_opportunity_shadow(
        _input(
            risk=StageAssessment(FAIL, ("MAJOR_SUPPORT_BROKEN",)),
            previous=STATE_WAITING_RETEST,
        )
    )

    assert result.evaluation_status == EVALUATION_BLOCKED
    assert result.state == STATE_INVALIDATED
    assert "MAJOR_SUPPORT_BROKEN" in result.reason_codes


def test_chip_confirmation_is_not_a_primary_gate() -> None:
    value = _input()
    value = OpportunityShadowInput(
        value.topic,
        value.stock,
        value.technical,
        value.risk,
        value.entry,
        ChipConfirmationFacts(StageAssessment(FAIL, ("CHIP_NOT_CONFIRMED",))),
    )

    result = build_opportunity_shadow(value)

    assert result.state == STATE_SELECTED
    assert result.evaluation_status == EVALUATION_READY


def test_topic_and_stock_identity_must_match() -> None:
    value = _input()
    with pytest.raises(OpportunityShadowError, match="topic_id"):
        OpportunityShadowInput(
            value.topic,
            StockOpportunityContext(
                value.stock.instrument_id,
                value.stock.symbol,
                value.stock.name,
                value.stock.market,
                "other-topic",
                value.stock.price,
                value.stock.ma20,
                value.stock.ma60,
                value.stock.sufficient_ohlcv,
            ),
            value.technical,
            value.risk,
            value.entry,
            value.chip,
        )
