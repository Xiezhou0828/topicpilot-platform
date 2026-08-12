from __future__ import annotations

from dataclasses import replace

from test_opportunity_strategies import _bars, _theme, _value

from topicpilot_api.topic_engine import (
    DECISION_STATE_DEFERRED,
    DECISION_STATE_EXCLUDED,
    DECISION_STATE_SELECTED,
    DECISION_STATE_WAITING_CONFIRMATION,
    DECISION_STATE_WAITING_RETEST,
    STRATEGY_CATCH_UP,
    STRATEGY_TREND_CONTINUATION,
    CatchUpRankingProfile,
    OpportunityPolicy,
    TrendContinuationRankingProfile,
    build_calibration_contract,
    build_frontend_opportunity_fixtures,
    evaluate_opportunity_engine,
    project_opportunity_read_model,
    validate_frontend_opportunity_fixtures,
)


def test_ranking_profiles_are_strategy_specific_and_independent() -> None:
    trend = TrendContinuationRankingProfile()
    catch_up = CatchUpRankingProfile()

    assert trend.strategy_id == STRATEGY_TREND_CONTINUATION
    assert catch_up.strategy_id == STRATEGY_CATCH_UP
    assert trend.weights != catch_up.weights
    policy = OpportunityPolicy()
    assert policy.trend_ranking_profile is not policy.catch_up_ranking_profile
    assert policy.as_dict()["rankingProfiles"]["trendContinuation"]["numericParameterStatus"] == (
        "PROVISIONAL_TUNABLE_VERSIONED"
    )


def test_trend_selected_has_decision_contract_state_and_explanation() -> None:
    value = _value()
    result = evaluate_opportunity_engine(value, (STRATEGY_TREND_CONTINUATION,)).for_strategy(
        STRATEGY_TREND_CONTINUATION
    )[0]
    read = project_opportunity_read_model(result, value)

    assert result.opportunity_state == DECISION_STATE_SELECTED
    assert read.opportunity_state == DECISION_STATE_SELECTED
    assert read.explanation.summary_code == "OPPORTUNITY_SELECTED"
    assert read.explanation.positive_factors
    assert read.as_dict()["publicationStatus"] == "SHADOW_ONLY"
    assert read.as_dict()["qualification"]["class"] == "FORMAL_OPPORTUNITY"
    assert result.as_dict()["qualificationClass"] == "FORMAL_OPPORTUNITY"


def test_trend_waiting_retest_is_explainable_without_recommendation_language() -> None:
    value = _value()
    # The builder's support-distance rule is deliberately provisional; this
    # test only asserts the contract mapping, not a frozen distance threshold.
    policy = replace(
        value.policy,
        technical_policy=replace(
            value.policy.technical_policy,
            support_distance_pass_max_pct=0.0,
            support_distance_wait_max_pct=100.0,
        ),
    )
    result = evaluate_opportunity_engine(
        replace(value, policy=policy), (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]
    read = project_opportunity_read_model(result, replace(value, policy=policy))

    assert result.opportunity_state == DECISION_STATE_WAITING_RETEST
    assert read.explanation.waiting_factors
    payload = str(read.as_dict()).upper()
    assert "BUY" not in payload and "SELL" not in payload and "STRONG BUY" not in payload


def test_catch_up_insufficient_activation_waits_for_confirmation() -> None:
    value = _value(
        bars=_bars(latest_volume=1_100.0),
        theme=_theme(returns=17.5),
        gaps=(-10.0, -9.0, -8.0),
    )
    result = evaluate_opportunity_engine(value, (STRATEGY_CATCH_UP,)).for_strategy(
        STRATEGY_CATCH_UP
    )[0]

    assert result.status == "CANDIDATE"
    assert result.opportunity_state == DECISION_STATE_WAITING_CONFIRMATION
    assert "VOLUME_ACTIVATION_BELOW_POLICY" in result.exclusion_codes


def test_b_warming_exception_is_preserved_in_read_and_explainability_contract() -> None:
    value = replace(
        _value(),
        theme=replace(
            _theme(grade="B"),
            warming_candidate=True,
            exception_provenance=("TOPIC_WARMING_SIGNAL",),
        ),
    )
    result = evaluate_opportunity_engine(value, (STRATEGY_TREND_CONTINUATION,)).for_strategy(
        STRATEGY_TREND_CONTINUATION
    )[0]
    read = project_opportunity_read_model(result, value)

    assert result.qualification_class == "EXCEPTION_CANDIDATE"
    assert read.as_dict()["qualification"]["class"] == "EXCEPTION_CANDIDATE"
    assert "TOPIC_GRADE_B_EXCEPTION_CANDIDATE" in result.qualification_reason_codes
    assert result.as_dict()["decision"]["qualificationClass"] == "EXCEPTION_CANDIDATE"


def test_deferred_and_excluded_states_are_deterministic() -> None:
    value = _value()
    deferred_value = replace(value, theme=_theme(grade=None))
    deferred_result = evaluate_opportunity_engine(
        deferred_value, (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]
    excluded_result = evaluate_opportunity_engine(
        value, ("EARLY_STRENGTH",)
    ).for_strategy("EARLY_STRENGTH")[0]

    assert deferred_result.opportunity_state == DECISION_STATE_DEFERRED
    excluded_read = project_opportunity_read_model(value=value, result=excluded_result)
    assert excluded_read.opportunity_state == DECISION_STATE_EXCLUDED
    assert project_opportunity_read_model(
        deferred_result, deferred_value
    ).explanation.summary_code == "OPPORTUNITY_DEFERRED_DATA_INCOMPLETE"


def test_frontend_fixtures_cover_all_states_and_are_schema_ready() -> None:
    fixtures = build_frontend_opportunity_fixtures()
    states = validate_frontend_opportunity_fixtures(fixtures)

    assert set(states) == {
        DECISION_STATE_SELECTED,
        DECISION_STATE_WAITING_RETEST,
        DECISION_STATE_WAITING_CONFIRMATION,
        DECISION_STATE_DEFERRED,
        DECISION_STATE_EXCLUDED,
    }
    assert all(
        item.as_dict()["contractVersion"].startswith("opportunity-read.v1")
        for item in fixtures
    )


def test_calibration_is_a_placeholder_with_required_horizons_and_metrics() -> None:
    payload = build_calibration_contract().as_dict()

    assert payload["evaluationImplemented"] is False
    assert payload["status"] == "PLACEHOLDER_NOT_IMPLEMENTED"
    assert payload["horizons"] == ["forward_1d", "forward_3d", "forward_5d", "forward_10d"]
    assert "forward_return" in payload["metrics"]
    assert "MFE" in payload["metrics"]
    assert "support_hold" in payload["metrics"]
    assert "invalidation_outcome" in payload["metrics"]
    assert "threshold_hit_10pct" in payload["metrics"]
    assert payload["dataContract"] == {
        "requiredSource": "CANONICAL_PRODUCTION_DAILY_OHLCV",
        "syntheticAllowed": False,
        "lookAhead": False,
    }
