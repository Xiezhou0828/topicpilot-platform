from __future__ import annotations

from datetime import date, timedelta

import pytest

from topicpilot_api.topic_engine import (
    PASS,
    UNKNOWN,
    CanonicalOHLCVBar,
    ChipConfirmationFacts,
    OpportunityEvidencePolicy,
    OpportunityShadowInputBuilder,
    OpportunityShadowReplayCase,
    StageAssessment,
    StockOpportunityContext,
    TopicOpportunityContext,
    build_entry_quality,
    build_moving_average_evidence,
    build_ohlcv_sufficiency,
    build_price_volume_evidence,
    build_technical_evidence,
    replay_historical_shadow,
)
from topicpilot_api.topic_engine.opportunity_shadow import EVIDENCE_UNAVAILABLE


def _bars(count: int = 70) -> list[CanonicalOHLCVBar]:
    result: list[CanonicalOHLCVBar] = []
    for index in range(count):
        close = 100.0 + index * 0.25
        result.append(
            CanonicalOHLCVBar(
                date(2025, 1, 1) + timedelta(days=index),
                close - 0.5,
                close + 1.0,
                close - 1.0,
                close,
                1000.0 + index * 10,
            )
        )
    return result


def _policy() -> OpportunityEvidencePolicy:
    return OpportunityEvidencePolicy(
        min_ohlcv_observations=20,
        ma20_window=20,
        ma60_window=20,
        ma_slope_lookback=3,
        support_lookback=20,
    )


def _topic() -> TopicOpportunityContext:
    return TopicOpportunityContext("topic-1", "AI", StageAssessment(PASS), grade="A")


def _stock() -> StockOpportunityContext:
    return StockOpportunityContext(
        "instrument-1", "2330", "Example", "TPE", "topic-1", None, None, None, None
    )


def test_policy_is_versioned_and_numeric_parameters_are_provisional() -> None:
    policy = _policy()
    payload = policy.as_dict()

    assert payload["policyStatus"] == "PROVISIONAL"
    assert payload["numericParameterStatus"] == "PROVISIONAL_TUNABLE"
    assert payload["numericParameters"]["ma20_window"] == 20


def test_sufficiency_counts_only_complete_ohlcv_and_keeps_missing_as_missing() -> None:
    bars = _bars(20)
    bars[-1] = CanonicalOHLCVBar(
        bars[-1].trading_date, bars[-1].open, bars[-1].high, bars[-1].low, None, bars[-1].volume
    )

    result = build_ohlcv_sufficiency(bars, _policy())

    assert result.available_count == 19
    assert result.assessment.status != PASS
    assert any(
        item.code == "OHLCV_MISSING_BAR_COUNT" and item.value == 1
        for item in result.assessment.evidence
    )


def test_moving_averages_use_trading_observations_and_mark_short_windows_unknown() -> None:
    ma20, ma60 = build_moving_average_evidence(_bars(19), _policy())

    assert ma20.status == UNKNOWN
    assert ma60.status == UNKNOWN
    assert ma20.value is None


def test_price_volume_preserves_observed_and_derived_facts() -> None:
    result = build_price_volume_evidence(_bars(), _policy())

    assert result.price_change_pct is not None
    assert result.volume is not None
    assert result.average_volume is not None
    assert result.range_position is not None
    assert {item.code for item in result.assessment.evidence} >= {
        "PRICE",
        "VOLUME",
        "RELATIVE_VOLUME",
    }


def test_support_selection_is_deterministic_and_not_lowest_candidate() -> None:
    technical = build_technical_evidence(_bars(), _policy())
    primary = technical.support.primary_support

    assert technical.support.assessment.status == PASS
    assert primary is not None
    assert primary.price == max(
        candidate.price
        for candidate in technical.support.candidates
        if candidate.price and candidate.price <= technical.price_volume.price
    )
    assert "highest_valid_support_below_price" in technical.support.selection_reason


def test_entry_quality_waits_when_provisional_support_distance_is_too_far() -> None:
    technical = build_technical_evidence(_bars(), _policy())
    entry = build_entry_quality(200.0, technical.support, _policy())

    assert entry.status == "WAIT"
    assert entry.support_distance_pct is not None
    assert "ENTRY_TOO_FAR_FROM_SUPPORT" in entry.reason_codes


def test_input_builder_composes_existing_shadow_input_without_chip_gate() -> None:
    built = OpportunityShadowInputBuilder(_policy()).build(
        topic=_topic(), stock=_stock(), bars=_bars()
    )

    assert built.input.stock.price == pytest.approx(built.technical.price_volume.price)
    assert built.input.stock.ma20 == pytest.approx(built.technical.ma20.value)
    assert built.input.chip.assessment.status == UNKNOWN
    assert built.policy.policy_status == "PROVISIONAL"


def test_historical_replay_excludes_future_bars() -> None:
    bars = tuple(_bars())
    case = OpportunityShadowReplayCase(
        "instrument-1",
        _topic(),
        _stock(),
        bars,
        ChipConfirmationFacts(StageAssessment(UNKNOWN, ("CHIP_NOT_AVAILABLE",))),
    )
    evaluation_date = bars[30].trading_date

    result = replay_historical_shadow((case,), (evaluation_date,), _policy())

    assert result.no_lookahead is True
    assert result.observations[0].latest_input_date == evaluation_date
    assert result.observations[0].latest_input_date < bars[-1].trading_date


def test_missing_chip_confirmation_is_explicitly_unavailable() -> None:
    built = OpportunityShadowInputBuilder(_policy()).build(
        topic=_topic(), stock=_stock(), bars=_bars()
    )

    assert built.input.chip.assessment.status == UNKNOWN
    assert built.input.chip.assessment.evidence[0].kind == EVIDENCE_UNAVAILABLE
