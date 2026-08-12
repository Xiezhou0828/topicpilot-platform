from datetime import date, timedelta

from topicpilot_api.topic_lifecycle_engine import (
    DECLINING,
    FERMENTING,
    MAIN_RISE,
    MATURE,
    SPROUTING,
    LifecycleInput,
    LifecycleObservation,
    evaluate_lifecycle,
)


def _day(
    changes,
    *,
    expected=None,
    previous=None,
    entered=None,
    days=None,
    candidate=None,
    streak=0,
):
    return LifecycleInput(
        topic_id="topic-1",
        trading_date=date(2026, 8, 10),
        expected_member_count=expected or len(changes),
        observations=tuple(
            LifecycleObservation(str(index), value) for index, value in enumerate(changes)
        ),
        previous_stage=previous,
        previous_stage_entered_at=entered,
        previous_stage_trading_days=days,
        previous_candidate_stage=candidate,
        previous_candidate_streak=streak,
    )


def test_sprouting_requires_confirmation_and_uses_leader_proxy():
    first = evaluate_lifecycle(_day([6, 0, -0.2], expected=5))
    second = evaluate_lifecycle(
        _day(
            [6, 0, -0.2],
            expected=5,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
        )
    )
    assert first.candidate_stage == SPROUTING
    assert first.final_stage is None
    assert second.final_stage == SPROUTING
    assert second.evidence.leadership["leaderSemanticAvailable"] is False


def test_fermenting_is_partial_diffusion_not_main_rise():
    first = evaluate_lifecycle(_day([5, 3, 1, 0, -1]))
    second = evaluate_lifecycle(
        _day(
            [5, 3, 1, 0, -1],
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
        )
    )
    assert first.candidate_stage == FERMENTING
    assert second.final_stage == FERMENTING


def test_main_rise_strong_structure_can_jump_without_two_day_confirmation():
    result = evaluate_lifecycle(_day([8, 7, 6, 5, 4, 3, 3, 2, 1, 1]))
    assert result.candidate_stage == MAIN_RISE
    assert result.final_stage == MAIN_RISE
    assert result.transition_decision == "JUMP_TRANSITION"
    assert result.confirmation_state["strongSignal"] is True


def test_mature_requires_prior_main_rise_and_persistent_divergence():
    changes = [2, 2, 1, 1, 0.5, 0.5, 0, 0, -0.2, -0.2]
    first = evaluate_lifecycle(
        _day(changes, previous=MAIN_RISE, entered=date(2026, 8, 1), days=5)
    )
    second = evaluate_lifecycle(
        _day(
            changes,
            previous=MAIN_RISE,
            entered=date(2026, 8, 1),
            days=6,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
        )
    )
    assert first.candidate_stage == MATURE
    assert first.final_stage == MAIN_RISE
    assert second.final_stage == MATURE
    assert second.stage_entered_at == date(2026, 8, 10)
    assert second.stage_trading_days == 1


def test_declining_strong_structural_weakening_can_jump():
    result = evaluate_lifecycle(
        _day([-6, -5, -4, -4, -4, -4, 0, 0, 1, 1], previous=MATURE, days=4)
    )
    assert result.candidate_stage == DECLINING
    assert result.final_stage == DECLINING
    assert result.transition_reason == "STRONG_STRUCTURE_SIGNAL"


def test_small_sample_and_low_coverage_are_not_promoted_to_sprouting():
    result = evaluate_lifecycle(_day([10, 10], expected=2))
    assert result.final_stage is None
    assert result.candidate_stage is None
    assert result.data_status == "INSUFFICIENT_DATA"
    assert result.evidence.sample_confidence["smallSample"] is True


def test_insufficient_data_holds_previous_stage_without_advancing_day_n():
    result = evaluate_lifecycle(
        _day([], expected=10, previous=MATURE, entered=date(2026, 8, 1), days=3)
    )
    assert result.final_stage == MATURE
    assert result.stage_trading_days == 3
    assert result.transition_decision == "HOLD_INSUFFICIENT_DATA"


def test_reentry_resets_day_n_for_new_main_rise():
    result = evaluate_lifecycle(
        _day([8, 7, 6, 5, 4, 3, 3, 2, 1, 1], previous=MATURE, days=3)
    )
    assert result.final_stage == MAIN_RISE
    assert result.stage_trading_days == 1


def test_trading_day_arithmetic_is_date_sequence_driven():
    prior_date = date(2026, 8, 7)
    result = evaluate_lifecycle(
        LifecycleInput(
            topic_id="topic-1",
            trading_date=prior_date + timedelta(days=3),
            expected_member_count=10,
            observations=tuple(
                LifecycleObservation(str(index), 2.0) for index in range(10)
            ),
            previous_stage=MAIN_RISE,
            previous_stage_entered_at=date(2026, 8, 1),
            previous_stage_trading_days=2,
        )
    )
    assert result.final_stage == MAIN_RISE
    assert result.stage_trading_days == 3


def test_ordinary_signal_cannot_skip_adjacent_lifecycle_stage():
    result = evaluate_lifecycle(
        _day(
            [4, 4, 4, 4, 2, 1, 1, 0, -1, -1],
            previous=SPROUTING,
            days=3,
        )
    )
    assert result.candidate_stage == MAIN_RISE
    assert result.final_stage == SPROUTING
    assert result.transition_decision == "HOLD_ILLEGAL_TRANSITION"
    assert result.transition_reason == "JUMP_REQUIRES_STRONG_EVIDENCE"


def test_same_input_is_deterministic_for_replay_and_calibration():
    value = _day([5, 3, 1, 0, -1])
    first = evaluate_lifecycle(value)
    second = evaluate_lifecycle(value)
    assert first == second
