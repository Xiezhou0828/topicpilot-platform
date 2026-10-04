from datetime import date

from topicpilot_api.formal_lifecycle_evaluator import evaluate_formal_structural_lifecycle
from topicpilot_api.formal_strength_publication import (
    build_market_context,
    build_structural_derivatives,
)
from topicpilot_api.topic_lifecycle_v1 import (
    BASE,
    DECLINING,
    MAIN_RISE,
    MATURE,
    SPROUTING,
    LifecycleInput,
    LifecycleObservation,
)

TARGET = date(2026, 9, 3)


def _index(market: str, change_pct: float, *, trading_date: date = TARGET, status="AVAILABLE"):
    return {
        "market": market,
        "index_identity": "TWSE:TAIEX" if market == "TPE" else "TPEX:TPEx",
        "trading_date": trading_date,
        "change_pct": change_pct,
        "data_status": status,
    }


def _derivatives(
    *,
    interpretation: str,
    absolute: float = 70.0,
    relative: float = 60.0,
    weakening: int = 0,
    absolute_status: str = "IMPROVING",
) -> dict:
    dimensions = {
        "absoluteStrength": {"currentLevel": absolute, "status": absolute_status},
        "relativeStrength": {"currentLevel": relative, "status": "IMPROVING"},
        "coreParticipation": {"currentLevel": 0.8, "status": "IMPROVING"},
        "breadth": {"currentLevel": 0.8, "status": "IMPROVING"},
        "relatedDiffusion": {"currentLevel": 0.8, "status": "IMPROVING"},
        "leadershipConcentration": {"currentLevel": 0.3, "status": "STABLE"},
    }
    return {
        "status": "AVAILABLE",
        "interpretation": interpretation,
        "dimensions": dimensions,
        "weakeningDimensions": weakening,
    }


def _lifecycle_input(
    *,
    previous_stage: str | None = BASE,
    previous_candidate_stage: str | None = None,
    previous_candidate_streak: int = 0,
    derivatives: dict | None = None,
    absolute: float = 70.0,
    relative: float = 60.0,
    absolute_grade: str = "A",
    relative_grade: str = "A",
    context: str = "NORMAL",
    history: tuple[dict, ...] = (),
) -> LifecycleInput:
    observations = tuple(
        LifecycleObservation(member_id=str(index), change_pct=2.0)
        for index in range(2)
    )
    return LifecycleInput(
        topic_id="topic",
        trading_date=TARGET,
        expected_member_count=2,
        observations=observations,
        previous_stage=previous_stage,
        previous_candidate_stage=previous_candidate_stage,
        previous_candidate_streak=previous_candidate_streak,
        absolute_strength=absolute,
        relative_strength=relative,
        absolute_grade=absolute_grade,
        relative_grade=relative_grade,
        derivative_evidence=derivatives or _derivatives(interpretation="EXPANDING"),
        market_context={"status": context},
        formal_history=history,
    )


def test_market_context_requires_current_published_benchmarks_without_zero_fill():
    missing = build_market_context((_index("TPE", 1.0, status="UNAVAILABLE"),), TARGET)
    assert missing.status == "UNAVAILABLE"
    assert missing.tai_ex_return_pct is None
    assert missing.tpex_return_pct is None

    stale = build_market_context((_index("TPE", 1.0, trading_date=date(2026, 9, 2)),), TARGET)
    assert stale.status == "UNAVAILABLE"

    shock = build_market_context((_index("TPE", -3.0), _index("TWO", -3.1)), TARGET)
    assert shock.status == "SYSTEMIC_SHOCK"
    assert shock.benchmark_ready is True


def test_structural_derivatives_expose_six_independent_dimensions():
    current = {
        "absoluteStrength": 70.0,
        "relativeStrength": 60.0,
        "coreParticipation": 0.8,
        "breadth": 0.75,
        "relatedDiffusion": 0.7,
        "leadershipConcentration": 0.3,
    }
    result = build_structural_derivatives(
        current,
        ({key: value - 5 if "Strength" in key else value - 0.1 for key, value in current.items()},),
    )
    assert set(result["dimensions"]) == {
        "absoluteStrength",
        "relativeStrength",
        "coreParticipation",
        "breadth",
        "relatedDiffusion",
        "leadershipConcentration",
    }
    assert all(
        {"currentLevel", "shortTrajectory", "baseline", "status"}
        <= set(dimension)
        for dimension in result["dimensions"].values()
    )
    assert result["doubleCountingGuard"]


def test_strong_absolute_relative_signal_can_enter_sprouting_immediately():
    result = evaluate_formal_structural_lifecycle(
        _lifecycle_input(
            absolute_grade="S",
            relative_grade="S",
            derivatives=_derivatives(interpretation="EXPANDING"),
        )
    )
    assert result.candidate_stage == SPROUTING
    assert result.final_stage == SPROUTING
    assert result.evidence.sample_confidence["topicSizeIsNotConfidencePenalty"] is True


def test_one_expanding_observation_does_not_auto_confirm_main_rise():
    result = evaluate_formal_structural_lifecycle(
        _lifecycle_input(
            previous_stage=SPROUTING,
            derivatives=_derivatives(interpretation="EXPANDING"),
            history=({"absoluteStrength": 68.0}, {"absoluteStrength": 69.0}),
        )
    )
    assert result.candidate_stage == MAIN_RISE
    assert result.final_stage == SPROUTING
    assert result.confirmation_state["transitionConfirmed"] is False


def test_mature_requires_healthy_level_and_saturation():
    result = evaluate_formal_structural_lifecycle(
        _lifecycle_input(
            previous_stage=MAIN_RISE,
            derivatives=_derivatives(interpretation="SATURATING"),
            history=({"absoluteStrength": 70.0},),
        )
    )
    assert result.candidate_stage == MATURE
    assert result.final_stage == MAIN_RISE


def test_main_rise_can_move_directly_to_declining_after_structural_break():
    derivatives = _derivatives(
        interpretation="DETERIORATING",
        absolute=40.0,
        relative=35.0,
        weakening=4,
        absolute_status="WEAKENING",
    )
    candidate = evaluate_formal_structural_lifecycle(
        _lifecycle_input(
            previous_stage=MAIN_RISE,
            derivatives=derivatives,
            absolute=40.0,
            relative=35.0,
            absolute_grade="D",
            relative_grade="D",
        )
    )
    assert candidate.candidate_stage == DECLINING
    assert candidate.final_stage == MAIN_RISE

    confirmed = evaluate_formal_structural_lifecycle(
        _lifecycle_input(
            previous_stage=MAIN_RISE,
            previous_candidate_stage=DECLINING,
            previous_candidate_streak=1,
            derivatives=derivatives,
            absolute=40.0,
            relative=35.0,
            absolute_grade="D",
            relative_grade="D",
        )
    )
    assert confirmed.final_stage == DECLINING


def test_systemic_shock_increases_decline_confirmation_burden_and_recovery_clears():
    derivatives = _derivatives(
        interpretation="DETERIORATING",
        absolute=40.0,
        relative=35.0,
        weakening=4,
        absolute_status="WEAKENING",
    )
    result = evaluate_formal_structural_lifecycle(
        _lifecycle_input(
            previous_stage=MAIN_RISE,
            derivatives=derivatives,
            absolute=40.0,
            relative=35.0,
            absolute_grade="D",
            relative_grade="D",
            context="SYSTEMIC_SHOCK",
        )
    )
    assert result.candidate_stage == DECLINING
    assert result.final_stage == MAIN_RISE
    assert result.confirmation_state["required"] == 3

    recovered = evaluate_formal_structural_lifecycle(
        _lifecycle_input(
            previous_stage=DECLINING,
            previous_candidate_stage=DECLINING,
            previous_candidate_streak=1,
            derivatives=_derivatives(interpretation="STABLE", absolute=70.0, relative=60.0),
            context="NORMAL",
        )
    )
    assert recovered.final_stage == BASE


def test_missing_relative_benchmark_blocks_lifecycle_but_not_absolute_input():
    derivatives = _derivatives(interpretation="STABLE")
    derivatives["dimensions"]["relativeStrength"]["currentLevel"] = None
    result = evaluate_formal_structural_lifecycle(
        _lifecycle_input(
            relative=None,
            derivatives=derivatives,
        )
    )
    assert result.evaluation_status == "UNAVAILABLE"
    assert result.transition_reason == "FORMAL_STRENGTH_OR_RELATIVE_OR_DERIVATIVES_UNAVAILABLE"
