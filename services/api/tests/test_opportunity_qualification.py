from __future__ import annotations

from dataclasses import replace

from test_opportunity_strategies import (
    _bars,
    _policy,
    _theme,
    _value,
)

from topicpilot_api.topic_engine import (
    CALIBRATION_PROVENANCE_FIELDS,
    FAIL,
    LIFECYCLE_CONFIRMATION_REQUIRED,
    LIFECYCLE_HARD_EXCLUDE,
    LIFECYCLE_HIGH_FIT,
    LIFECYCLE_LOW_FIT,
    LIFECYCLE_MEDIUM_HIGH_FIT,
    LIFECYCLE_STRICTER_GATES,
    QUALIFICATION_DEFERRED,
    QUALIFICATION_EXCEPTION,
    QUALIFICATION_EXCLUDED,
    QUALIFICATION_FORMAL,
    QUALIFICATION_WAITING_CONFIRMATION,
    STRATEGY_CATCH_UP,
    STRATEGY_TREND_CONTINUATION,
    Evidence,
    OpportunityQualificationPolicy,
    StageAssessment,
    StrategyReplayCase,
    apply_qualification_policy,
    build_calibration_contract,
    build_technical_evidence,
    evaluate_opportunity_engine,
    presentation_candidates,
    project_opportunity_read_model,
    qualify_opportunity,
    rank_strategy_results,
    replay_opportunity_strategies,
)


def _result(*, theme=None, strategy: str = STRATEGY_TREND_CONTINUATION):
    return evaluate_opportunity_engine(
        _value(theme=theme or _theme()), (strategy,)
    ).for_strategy(strategy)[0]


def test_policy_freezes_grade_lifecycle_order_caps_and_cadence() -> None:
    value = _value()
    result = _result()

    assert result.qualification_status == QUALIFICATION_FORMAL
    assert result.qualification_policy_version == "opportunity-qualification-policy.v1"
    assert build_calibration_contract().as_dict()["provenanceFields"] == list(
        CALIBRATION_PROVENANCE_FIELDS
    )
    placeholder = build_calibration_contract().as_dict()
    assert set(placeholder["provenanceFields"]) == {
        "lifecycle_at_selection",
        "topic_grade_at_selection",
        "opportunity_state_at_selection",
        "ranking_profile_version",
        "policy_version",
        "parameter_version",
    }
    read = project_opportunity_read_model(result, value).as_dict()
    assert read["qualification"]["policyVersion"] == "opportunity-qualification-policy.v1"
    assert read["qualification"]["parameterVersion"] == (
        "opportunity-qualification-parameters.v1.provisional"
    )


def test_s_and_a_are_formal_and_b_requires_warming_provenance() -> None:
    for grade in ("S", "A"):
        assert _result(theme=_theme(grade=grade)).qualification_status == QUALIFICATION_FORMAL

    blocked = _result(theme=_theme(grade="B"))
    assert blocked.qualification_status == QUALIFICATION_EXCLUDED
    assert not blocked.qualification_exception

    no_provenance = _result(theme=replace(_theme(grade="B"), warming_candidate=True))
    assert no_provenance.qualification_status == QUALIFICATION_EXCLUDED

    evidence_without_provenance = _result(
        theme=replace(
            _theme(grade="B"),
            warming_candidate=True,
            warming_evidence=(
                Evidence("WARMING_SIGNAL", "OBSERVED", "improving"),
            ),
        )
    )
    assert evidence_without_provenance.qualification_status == QUALIFICATION_EXCLUDED

    evidence_with_provenance = _result(
        theme=replace(
            _theme(grade="B"),
            warming_evidence=(Evidence("WARMING_SIGNAL", "OBSERVED", "improving"),),
            exception_provenance=("TOPIC_WARMING_SIGNAL",),
        )
    )
    assert evidence_with_provenance.qualification_status == QUALIFICATION_EXCEPTION

    warming = replace(
        _theme(grade="B"),
        warming_candidate=True,
        exception_provenance=("TOPIC_WARMING_SIGNAL",),
    )
    exception = _result(theme=warming)
    assert exception.status == "CANDIDATE"
    assert exception.qualification_status == QUALIFICATION_EXCEPTION
    assert exception.qualification_exception

    warming_without_reason = _result(theme=replace(_theme(grade="B"), warming_candidate=True))
    assert warming_without_reason.qualification_status == QUALIFICATION_EXCLUDED
    assert (
        "TOPIC_GRADE_B_EXCEPTION_PROVENANCE_MISSING"
        in warming_without_reason.qualification_reason_codes
    )


def test_d_and_declining_are_hard_excluded() -> None:
    assert _result(theme=_theme(grade="D")).qualification_status == QUALIFICATION_EXCLUDED
    assert (
        _result(theme=_theme(lifecycle="DECLINING")).qualification_status
        == QUALIFICATION_EXCLUDED
    )


def test_mature_catch_up_requires_confirmation_but_trend_can_continue() -> None:
    mature = _theme(lifecycle="MATURE")
    assert _result(theme=mature).qualification_status == QUALIFICATION_FORMAL
    value = _value(theme=mature)
    trend_result = _result(theme=mature)
    catch_up_result = replace(trend_result, strategy_id=STRATEGY_CATCH_UP)
    assert qualify_opportunity(catch_up_result, value).status == QUALIFICATION_WAITING_CONFIRMATION


def test_lifecycle_matrix_is_explicit_and_consumes_upstream_stage() -> None:
    policy = OpportunityQualificationPolicy()
    assert policy.lifecycle_status(STRATEGY_TREND_CONTINUATION, "SPROUTING") == (
        LIFECYCLE_CONFIRMATION_REQUIRED
    )
    assert policy.lifecycle_status(STRATEGY_TREND_CONTINUATION, "FERMENTING") == LIFECYCLE_HIGH_FIT
    assert policy.lifecycle_status(STRATEGY_TREND_CONTINUATION, "MATURE") == LIFECYCLE_LOW_FIT
    assert policy.lifecycle_status(STRATEGY_CATCH_UP, "FERMENTING") == LIFECYCLE_MEDIUM_HIGH_FIT
    assert policy.lifecycle_status(STRATEGY_CATCH_UP, "MATURE") == LIFECYCLE_STRICTER_GATES
    assert policy.lifecycle_status(STRATEGY_CATCH_UP, "DECLINING") == LIFECYCLE_HARD_EXCLUDE

    sprouting = _result(theme=_theme(lifecycle="SPROUTING"))
    assert sprouting.qualification_status == QUALIFICATION_WAITING_CONFIRMATION
    assert sprouting.opportunity_state == "WAITING_CONFIRMATION"
    assert any(stage.name == "LIFECYCLE_FIT" for stage in sprouting.stages)


def test_20ma_is_hard_gate_and_missing_20ma_defers() -> None:
    rows = list(_bars(latest_volume=2_000.0))
    latest = rows[-1]
    rows[-1] = replace(latest, open=95.0, high=96.0, low=93.0, close=94.0)
    below = _result()
    below = evaluate_opportunity_engine(
        _value(bars=tuple(rows)), (STRATEGY_TREND_CONTINUATION,)
    ).for_strategy(STRATEGY_TREND_CONTINUATION)[0]
    assert below.qualification_status == QUALIFICATION_EXCLUDED
    assert "CLOSE_BELOW_20MA_HARD_EXCLUDE" in below.qualification_reason_codes

    value = _value()
    technical = build_technical_evidence(
        value.stock.bars, value.policy.technical_policy, as_of=value.as_of
    )
    missing = replace(technical, ma20=replace(technical.ma20, status="UNKNOWN", value=None))
    decision = qualify_opportunity(_result(), value, technical=missing)
    assert decision.status == QUALIFICATION_DEFERRED


def test_below_60ma_is_recovery_context_not_automatic_exclusion() -> None:
    value = _value()
    technical = build_technical_evidence(
        value.stock.bars, value.policy.technical_policy, as_of=value.as_of
    )
    below_60 = replace(technical, ma60=replace(technical.ma60, value=200.0))
    decision = qualify_opportunity(_result(), value, technical=below_60)
    assert decision.status == QUALIFICATION_FORMAL
    assert decision.sixty_ma_status == "RECOVERY"


def test_close_equal_to_20ma_passes_and_60ma_is_not_a_hard_gate() -> None:
    value = _value()
    technical = build_technical_evidence(
        value.stock.bars, value.policy.technical_policy, as_of=value.as_of
    )
    assert technical.ma20.value is not None
    equal = replace(
        technical,
        price_volume=replace(technical.price_volume, price=technical.ma20.value),
    )
    decision = qualify_opportunity(_result(), value, technical=equal)
    assert decision.status == QUALIFICATION_FORMAL
    assert decision.twenty_ma_status == "PASS"
    assert decision.sixty_ma_status in {"PASS", "RECOVERY", "UNKNOWN"}


def test_hard_risk_is_applied_before_ranking() -> None:
    value = _value()
    technical = build_technical_evidence(
        value.stock.bars, value.policy.technical_policy, as_of=value.as_of
    )
    hard_break = replace(
        technical.bearish_break,
        assessment=StageAssessment(FAIL, ("TEST_CONFIRMED_BREAK",), ()),
    )
    decision = qualify_opportunity(
        _result(), value, technical=replace(technical, bearish_break=hard_break)
    )
    assert decision.status == QUALIFICATION_EXCLUDED

    ranked_then_invalidated = replace(
        _result(),
        status="EXCLUDED",
        eligibility=FAIL,
        exclusion_codes=("CONFIRMED_SUPPORT_OR_STRUCTURAL_BREAK_HARD_EXCLUDE",),
        rank_score=99.0,
    )
    final = apply_qualification_policy(ranked_then_invalidated, value)
    assert final.rank_score is None
    assert final.ranking_status == "UNAVAILABLE"


def test_presentation_caps_are_strategy_local_and_backend_rank_is_retained() -> None:
    base = _result()
    trend = tuple(
        replace(base, instrument_id=f"trend-{index}", rank_score=float(index))
        for index in range(5)
    )
    catch_up = tuple(
        replace(
            base,
            strategy_id=STRATEGY_CATCH_UP,
            instrument_id=f"catch-{index}",
            rank_score=float(index),
        )
        for index in range(4)
    )
    assert len(presentation_candidates(trend)) == 3
    assert len(presentation_candidates(catch_up)) == 2
    assert len(rank_strategy_results(trend)) == 5


def test_cross_strategy_global_ranking_remains_blocked() -> None:
    base = _result()
    try:
        rank_strategy_results((base, replace(base, strategy_id=STRATEGY_CATCH_UP)))
    except ValueError as exc:
        assert "one strategy" in str(exc)
    else:  # pragma: no cover - assertion makes the contract explicit
        raise AssertionError("cross-strategy ranking must remain unavailable")


def test_replay_applies_qualification_and_preserves_no_lookahead() -> None:
    value = _value()
    replay = replay_opportunity_strategies(
        (
            StrategyReplayCase(
                value.theme,
                value.stock,
                (value.as_of,),
            ),
        ),
        _policy(),
        (STRATEGY_TREND_CONTINUATION,),
    )
    assert replay.no_lookahead
    assert replay.observations[0].result.qualification_status != "NOT_EVALUATED"
