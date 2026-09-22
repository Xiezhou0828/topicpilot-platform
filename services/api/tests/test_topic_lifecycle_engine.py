from datetime import date

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
    roles=None,
    expected=None,
    previous=None,
    entered=None,
    days=None,
    candidate=None,
    streak=0,
    state_memory=None,
    closes=None,
    previous_closes=None,
):
    roles = roles or ["REPRESENTATIVE"] + ["CORE"] * (len(changes) - 1)
    closes = closes or [100.0] * len(changes)
    previous_closes = previous_closes or closes
    return LifecycleInput(
        topic_id="topic-1",
        trading_date=date(2026, 8, 10),
        expected_member_count=expected or len(changes),
        observations=tuple(
            LifecycleObservation(
                str(index),
                value,
                roles[index],
                "TEST_STRUCTURAL_ROLE",
                closes[index],
                previous_closes[index],
            )
            for index, value in enumerate(changes)
        ),
        previous_stage=previous,
        previous_stage_entered_at=entered,
        previous_stage_trading_days=days,
        previous_candidate_stage=candidate,
        previous_candidate_streak=streak,
        state_memory=state_memory,
    )


def test_leader_only_is_sprouting_and_requires_confirmation():
    roles = ["REPRESENTATIVE", "RELATED", "RELATED"]
    first = evaluate_lifecycle(_day([6, 0, -0.2], roles=roles, expected=3))
    second = evaluate_lifecycle(
        _day(
            [6, 0, -0.2],
            roles=roles,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
        )
    )
    assert first.candidate_stage == SPROUTING
    assert first.final_stage is None
    assert second.final_stage == SPROUTING
    assert second.evidence.leadership["roleAuthorityAvailable"] is True


def test_related_only_cannot_enter_main_rise():
    result = evaluate_lifecycle(_day([8, 7, 6, 5], roles=["RELATED"] * 4))
    assert result.candidate_stage == SPROUTING
    assert result.candidate_stage != MAIN_RISE


def test_core_resonance_is_fermenting_not_main_rise():
    roles = ["REPRESENTATIVE", "CORE", "CORE", "RELATED", "RELATED"]
    first = evaluate_lifecycle(_day([5, 3, 1, 0, -1], roles=roles))
    second = evaluate_lifecycle(
        _day(
            [5, 3, 1, 0, -1],
            roles=roles,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
        )
    )
    assert first.candidate_stage == FERMENTING
    assert second.final_stage == FERMENTING


def test_broad_core_can_compensate_for_weak_lead_and_main_rise_confirms():
    roles = ["REPRESENTATIVE"] + ["CORE"] * 9
    changes = [0.5, 8, 7, 6, 5, 4, 3, 3, 2, 1]
    first = evaluate_lifecycle(_day(changes, roles=roles))
    second = evaluate_lifecycle(
        _day(
            changes,
            roles=roles,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
        )
    )
    assert first.candidate_stage == MAIN_RISE
    assert second.final_stage == MAIN_RISE
    assert second.main_rise_segment == 1
    assert second.segment_entry_date == date(2026, 8, 10)


def test_main_rise_to_mature_after_five_sessions_without_expansion_or_recovery():
    roles = ["REPRESENTATIVE"] + ["CORE"] * 9
    memory = None
    candidate = None
    streak = 0
    result = None
    for _ in range(5):
        result = evaluate_lifecycle(
            _day(
                [0] * 10,
                roles=roles,
                previous=MAIN_RISE,
                entered=date(2026, 8, 1),
                days=10,
                candidate=candidate,
                streak=streak,
                state_memory=memory,
                closes=[100] * 10,
            )
        )
        memory = result.state_memory
        candidate = result.candidate_stage
        streak = result.confirmation_state["candidateStreak"]
    assert result is not None
    assert result.days_since_meaningful_expansion == 5
    assert result.candidate_stage == MATURE
    assert result.final_stage == MATURE
    assert result.transition_reason == "MAIN_RISE_EXPANSION_STALLED_5_SESSIONS"


def test_mature_to_main_rise_reentry_without_expansion_preserves_clock():
    roles = ["REPRESENTATIVE"] + ["CORE"] * 9
    memory = {
        "mainRiseSegment": 1,
        "segmentEntryDate": "2026-08-01",
        "segmentAnchorDate": "2026-08-01",
        "runningPeakCloseByMember": {str(index): 100 for index in range(10)},
        "runningPeakDateByMember": {str(index): "2026-08-01" for index in range(10)},
        "daysSinceMeaningfulExpansion": 7,
    }
    first = evaluate_lifecycle(
        _day(
            [8, 7, 6, 5, 5, 4, 4, 3, 3, 2],
            roles=roles,
            previous=MATURE,
            state_memory=memory,
            closes=[90] * 10,
            previous_closes=[90] * 10,
        )
    )
    assert first.candidate_stage == MAIN_RISE
    assert first.final_stage is MATURE
    second = evaluate_lifecycle(
        _day(
            [8, 7, 6, 5, 5, 4, 4, 3, 3, 2],
            roles=roles,
            previous=MATURE,
            state_memory=first.state_memory,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
            closes=[90] * 10,
            previous_closes=[90] * 10,
        )
    )
    assert second.final_stage == MAIN_RISE
    assert second.main_rise_segment == 2
    assert second.confirmation_state["meaningfulExpansion"] is False
    assert second.days_since_meaningful_expansion == 7


def test_mature_to_declining_requires_peak_drawdown_and_two_day_confirmation():
    roles = ["REPRESENTATIVE"] + ["CORE"] * 9
    memory = {
        "mainRiseSegment": 1,
        "segmentEntryDate": "2026-08-01",
        "segmentAnchorDate": "2026-08-01",
        "runningPeakCloseByMember": {str(index): 100 for index in range(10)},
        "runningPeakDateByMember": {str(index): "2026-08-01" for index in range(10)},
        "daysSinceMeaningfulExpansion": 5,
    }
    first = evaluate_lifecycle(
        _day(
            [-6, -5, -4, -4, -4, -4, 0, 0, 1, 1],
            roles=roles,
            previous=MATURE,
            days=4,
            state_memory=memory,
            closes=[60] * 10,
            previous_closes=[100] * 10,
        )
    )
    second = evaluate_lifecycle(
        _day(
            [-6, -5, -4, -4, -4, -4, 0, 0, 1, 1],
            roles=roles,
            previous=MATURE,
            days=4,
            state_memory=first.state_memory,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
            closes=[60] * 10,
            previous_closes=[100] * 10,
        )
    )
    assert first.candidate_stage == DECLINING
    assert first.final_stage == MATURE
    assert second.final_stage == DECLINING
    assert second.drawdown_from_peak_pct == -40.0


def test_one_day_pullback_does_not_mature_or_decline_without_dual_gate():
    roles = ["REPRESENTATIVE"] + ["CORE"] * 9
    memory = {
        "runningPeakCloseByMember": {str(index): 100 for index in range(10)},
        "runningPeakDateByMember": {str(index): "2026-08-01" for index in range(10)},
        "daysSinceMeaningfulExpansion": 2,
    }
    result = evaluate_lifecycle(
        _day(
            [1, 1, 1, 1, 0, 0, 0, 0, -1, -1],
            roles=roles,
            previous=MAIN_RISE,
            state_memory=memory,
            closes=[98] * 10,
            previous_closes=[100] * 10,
        )
    )
    assert result.final_stage == MAIN_RISE
    assert result.candidate_stage is None


def test_missing_role_authority_is_fail_closed_not_a_stage_signal():
    result = evaluate_lifecycle(
        LifecycleInput(
            topic_id="topic-1",
            trading_date=date(2026, 8, 10),
            expected_member_count=5,
            observations=tuple(LifecycleObservation(str(index), 8.0) for index in range(5)),
        )
    )
    assert result.final_stage is None
    assert result.data_status == "INSUFFICIENT_DATA"
    assert result.transition_reason == "STRUCTURAL_ROLE_AUTHORITY_UNAVAILABLE"


def test_insufficient_data_holds_previous_stage_and_memory():
    memory = {"mainRiseSegment": 2, "daysSinceMeaningfulExpansion": 3}
    result = evaluate_lifecycle(
        LifecycleInput(
            topic_id="topic-1",
            trading_date=date(2026, 8, 10),
            expected_member_count=10,
            observations=(),
            previous_stage=MATURE,
            previous_stage_entered_at=date(2026, 8, 1),
            previous_stage_trading_days=3,
            state_memory=memory,
        )
    )
    assert result.final_stage == MATURE
    assert result.stage_trading_days == 3
    assert result.state_memory == memory


def test_same_input_is_deterministic_for_replay():
    value = _day([5, 3, 1, 0, -1])
    assert evaluate_lifecycle(value) == evaluate_lifecycle(value)
