from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta

import pytest

from topicpilot_api.topic_engine import (
    EVIDENCE_UNAVAILABLE,
    PASS,
    STRATEGY_CATCH_UP,
    STRATEGY_EARLY_STRENGTH,
    STRATEGY_TREND_CONTINUATION,
    CanonicalOHLCVBar,
    OpportunityEngine,
    OpportunityEvidencePolicy,
    OpportunityPolicy,
    OpportunityStrategyInput,
    StrategyReplayCase,
    StrategyStockContext,
    ThemeContext,
    build_pm_calibration_report,
    evaluate_opportunity_engine,
    rank_strategy_results,
    replay_opportunity_strategies,
)


def _bars(count: int = 85, *, latest_volume: float | None = None) -> tuple[CanonicalOHLCVBar, ...]:
    rows: list[CanonicalOHLCVBar] = []
    for index in range(count):
        close = 100.0 + index * 0.35
        volume = latest_volume if latest_volume is not None and index == count - 1 else 1_000.0
        rows.append(
            CanonicalOHLCVBar(
                date(2025, 1, 1) + timedelta(days=index),
                close - 0.5,
                close + 1.0,
                close - 1.0,
                close,
                volume,
            )
        )
    return tuple(rows)


def _policy() -> OpportunityPolicy:
    return OpportunityPolicy(
        technical_policy=OpportunityEvidencePolicy(
            min_ohlcv_observations=60,
            volume_confirmation_ratio=1.10,
            range_position_min=0.40,
        ),
        trend_relative_window=20,
        trend_relative_min_pct=0.0,
        catch_up_relative_window=20,
        catch_up_lag_min_pct=-12.0,
        catch_up_lag_max_pct=-2.0,
        catch_up_inflection_lookback=2,
    )


def _theme(
    *, grade: str | None = "A", lifecycle: str | None = "MAIN_RISE", returns: float = 5.0
) -> ThemeContext:
    return ThemeContext(
        "topic-1",
        "AI servers",
        grade,
        lifecycle,
        80.0,
        ((),)[0],
        date(2025, 3, 26),
        {20: returns},
        False,
    )


def _value(
    *,
    bars: tuple[CanonicalOHLCVBar, ...] | None = None,
    theme: ThemeContext | None = None,
    gaps: tuple[float, ...] = (),
) -> OpportunityStrategyInput:
    stock = StrategyStockContext(
        "instrument-1",
        "2330",
        "Example",
        "topic-1",
        bars or _bars(latest_volume=2_000.0),
        True,
        False,
        True,
        "CORE",
        gaps,
    )
    return OpportunityStrategyInput(theme or _theme(), stock, date(2025, 3, 26), _policy())


def test_policy_serializes_version_and_provisional_status() -> None:
    payload = _policy().as_dict()

    assert payload["policyVersion"] == "topic-opportunity-policy.provisional.1"
    assert payload["policyStatus"] == "PROVISIONAL"
    assert payload["numericParameterStatus"] == "PROVISIONAL_TUNABLE"
    assert payload["rankingWeights"]


def test_theme_context_accepts_explicit_topic_return_alias() -> None:
    theme = ThemeContext(
        "topic-1",
        "AI servers",
        "A",
        "MAIN_RISE",
        80.0,
        topic_returns_pct={20: 5.0},
        no_trade=False,
    )

    result = evaluate_opportunity_engine(
        _value(theme=theme), (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]

    assert result.status == "CANDIDATE"


def test_engine_facade_binds_one_policy_and_returns_shadow_result() -> None:
    engine = OpportunityEngine(_policy())
    result = engine.evaluate(_value())

    assert result.policy == _policy()
    assert result.as_dict()["publicationStatus"] == "SHADOW_ONLY"


def test_trend_continuation_requires_strong_theme_and_healthy_structure() -> None:
    result = evaluate_opportunity_engine(_value(), (STRATEGY_TREND_CONTINUATION,)).for_strategy(
        STRATEGY_TREND_CONTINUATION
    )[0]

    assert result.status == "CANDIDATE"
    assert result.eligibility == PASS
    assert result.rank_score is not None
    assert any(stage.name == "RELATIVE_STRENGTH" for stage in result.stages)


def test_trend_continuation_excludes_below_20ma() -> None:
    rows = list(_bars(latest_volume=2_000.0))
    latest = rows[-1]
    rows[-1] = CanonicalOHLCVBar(
        latest.trading_date,
        95.0,
        96.0,
        93.0,
        94.0,
        2_000.0,
    )

    result = evaluate_opportunity_engine(
        _value(bars=tuple(rows)), (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]

    assert result.status == "EXCLUDED"
    assert "PRICE_NOT_ABOVE_20MA" in result.exclusion_codes


def test_grade_b_and_unapproved_lifecycle_are_excluded_by_policy() -> None:
    grade_result = evaluate_opportunity_engine(
        _value(theme=_theme(grade="B")), (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]
    lifecycle_result = evaluate_opportunity_engine(
        _value(theme=_theme(lifecycle="DECLINING")), (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]

    assert "THEME_GRADE_NOT_ELIGIBLE" in grade_result.exclusion_codes
    assert "THEME_LIFECYCLE_NOT_ELIGIBLE" in lifecycle_result.exclusion_codes


def test_formal_no_trade_excludes_and_unknown_liquidity_defers() -> None:
    no_trade_value = replace(_value(), stock=replace(_value().stock, no_trade=True))
    unknown_liquidity = replace(_value(), stock=replace(_value().stock, liquidity_available=None))

    no_trade_result = evaluate_opportunity_engine(
        no_trade_value, (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]
    unknown_result = evaluate_opportunity_engine(
        unknown_liquidity, (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]

    assert "FORMAL_NO_TRADE" in no_trade_result.exclusion_codes
    assert unknown_result.status == "DEFERRED"


def test_negative_relative_strength_excludes_trend_continuation() -> None:
    result = evaluate_opportunity_engine(
        _value(theme=_theme(returns=30.0)), (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]

    assert result.status == "EXCLUDED"
    assert "RELATIVE_STRENGTH_BELOW_POLICY" in result.exclusion_codes


def test_missing_theme_context_defers_without_inventing_grade() -> None:
    result = evaluate_opportunity_engine(
        _value(theme=_theme(grade=None)), (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]

    assert result.status == "DEFERRED"
    assert result.eligibility == "UNKNOWN"
    assert any(item.kind == EVIDENCE_UNAVAILABLE for item in result.evidence)


def test_catch_up_requires_lag_in_window_and_improving_relative_strength() -> None:
    result = evaluate_opportunity_engine(
        _value(theme=_theme(returns=17.5), gaps=(-10.0, -9.0, -8.0)), (STRATEGY_CATCH_UP,)
    ).for_strategy(STRATEGY_CATCH_UP)[0]

    assert result.status == "CANDIDATE"
    assert result.eligibility == PASS
    assert any("CATCHUP_LAG_IN_WINDOW" in stage.assessment.reason_codes for stage in result.stages)
    assert any("CATCHUP_RS_IMPROVING" in stage.assessment.reason_codes for stage in result.stages)


def test_catch_up_lag_too_small_is_not_a_catch_up_candidate() -> None:
    result = evaluate_opportunity_engine(
        _value(theme=_theme(returns=5.0), gaps=(-1.0, 0.0, 1.0)), (STRATEGY_CATCH_UP,)
    ).for_strategy(STRATEGY_CATCH_UP)[0]

    assert result.status == "EXCLUDED"
    assert "CATCHUP_LAG_OUTSIDE_WINDOW" in result.exclusion_codes


def test_catch_up_lag_too_large_and_rs_deterioration_are_excluded() -> None:
    lag_result = evaluate_opportunity_engine(
        _value(theme=_theme(returns=30.0), gaps=(-10.0, -9.0, -8.0)), (STRATEGY_CATCH_UP,)
    ).for_strategy(STRATEGY_CATCH_UP)[0]
    deterioration_result = evaluate_opportunity_engine(
        _value(theme=_theme(returns=17.5), gaps=(-8.0, -9.0, -10.0)), (STRATEGY_CATCH_UP,)
    ).for_strategy(STRATEGY_CATCH_UP)[0]

    assert "CATCHUP_LAG_OUTSIDE_WINDOW" in lag_result.exclusion_codes
    assert "CATCHUP_RS_DETERIORATING" in deterioration_result.exclusion_codes


def test_volume_activation_alone_cannot_create_a_trend_candidate() -> None:
    rows = list(_bars(latest_volume=2_000.0))
    latest = rows[-1]
    previous = rows[-2]
    rows[-1] = CanonicalOHLCVBar(
        latest.trading_date,
        previous.close - 0.8,
        previous.close + 0.2,
        previous.close - 1.2,
        previous.close - 0.5,
        2_000.0,
    )

    result = evaluate_opportunity_engine(
        _value(bars=tuple(rows)), (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]

    assert result.status == "EXCLUDED"
    assert "PRICE_VOLUME_NOT_CONFIRMED" in result.exclusion_codes


def test_strategy_rank_is_independent_and_cross_strategy_ranking_is_rejected() -> None:
    engine = evaluate_opportunity_engine(_value())
    trend = engine.for_strategy(STRATEGY_TREND_CONTINUATION)
    catch_up = engine.for_strategy(STRATEGY_CATCH_UP)

    assert rank_strategy_results(trend)[0].strategy_id == STRATEGY_TREND_CONTINUATION
    with pytest.raises(ValueError, match="one strategy"):
        rank_strategy_results((*trend, *catch_up))
    assert engine.as_dict()["globalCrossStrategyRanking"] is None


def test_future_strategies_are_explicitly_not_implemented() -> None:
    result = evaluate_opportunity_engine(_value(), (STRATEGY_EARLY_STRENGTH,)).for_strategy(
        STRATEGY_EARLY_STRENGTH
    )[0]

    assert result.status == "FUTURE_NOT_IMPLEMENTED"
    assert result.eligibility == "UNKNOWN"
    assert "STRATEGY_NOT_IMPLEMENTED" in result.exclusion_codes


def test_strategy_result_is_shadow_only_and_confidence_is_not_probability() -> None:
    result = evaluate_opportunity_engine(_value()).for_strategy(STRATEGY_TREND_CONTINUATION)[0]

    assert result.publication_status == "SHADOW_ONLY"
    assert result.confidence in {"HIGH", "MEDIUM", "LOW"}
    assert not isinstance(result.confidence, (int, float))


def test_reason_codes_are_deterministic_for_identical_inputs() -> None:
    value = _value()
    first = evaluate_opportunity_engine(value).as_dict()
    second = evaluate_opportunity_engine(value).as_dict()

    assert first == second


def test_replay_is_deterministic_and_excludes_future_bars() -> None:
    bars = _bars(latest_volume=2_000.0)
    evaluation_date = bars[65].trading_date
    replay = replay_opportunity_strategies(
        (StrategyReplayCase(_theme(), _value().stock, (evaluation_date,)),),
        _policy(),
    )

    assert replay.no_lookahead is True
    assert len(replay.observations) == 2
    assert all(item.latest_bar_date == evaluation_date for item in replay.observations)
    assert all(item.result.as_of == evaluation_date for item in replay.observations)


def test_replay_defers_future_theme_snapshot_without_lookahead() -> None:
    future_theme = ThemeContext(
        "topic-1",
        "AI servers",
        "A",
        "MAIN_RISE",
        80.0,
        (),
        date(2025, 4, 1),
        {20: 5.0},
        False,
    )
    evaluation_date = date(2025, 3, 1)
    case = StrategyReplayCase(future_theme, _value().stock, (evaluation_date,))

    replay = replay_opportunity_strategies((case,), _policy())

    assert replay.no_lookahead is True
    assert all(item.result.status == "DEFERRED" for item in replay.observations)


def test_pm_calibration_report_is_shadow_only_and_contains_strategy_rows() -> None:
    case = StrategyReplayCase(_theme(), _value().stock, (date(2025, 3, 26),))
    report = build_pm_calibration_report(replay_opportunity_strategies((case,), _policy()))

    payload = report.as_dict()
    assert payload["publicationStatus"] == "SHADOW_ONLY"
    assert {row["strategyId"] for row in payload["rows"]} == {
        STRATEGY_TREND_CONTINUATION,
        STRATEGY_CATCH_UP,
    }
    assert all(
        set(row["selectionProvenance"]) == {
            "lifecycleAtSelection",
            "topicGradeAtSelection",
            "opportunityStateAtSelection",
            "rankingProfileVersion",
            "policyVersion",
            "parameterVersion",
        }
        for row in payload["rows"]
    )
