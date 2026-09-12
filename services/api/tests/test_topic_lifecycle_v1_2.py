from datetime import date

from topicpilot_api.topic_lifecycle_v1 import (
    BASE,
    DECLINING,
    FERMENTING,
    MAIN_RISE,
    MATURE,
    SPROUTING,
    LifecycleInput,
    LifecycleObservation,
    evaluate_lifecycle,
)


def _input(
    changes,
    *,
    previous=None,
    memory=None,
    closes=None,
    previous_closes=None,
    candidate=None,
    streak=0,
    roles=None,
    expected=None,
    trading_date=date(2026, 8, 10),
):
    roles = roles or (["REPRESENTATIVE"] + ["CORE"] * (len(changes) - 1))
    closes = closes or [100.0] * len(changes)
    previous_closes = previous_closes or closes
    return LifecycleInput(
        topic_id="v1.2-test-topic",
        trading_date=trading_date,
        expected_member_count=expected or len(changes),
        observations=tuple(
            LifecycleObservation(
                str(index),
                float(change) if change is not None else None,
                roles[index],
                "TEST_OWNER_ROLE",
                closes[index],
                previous_closes[index],
            )
            for index, change in enumerate(changes)
        ),
        previous_stage=previous,
        previous_candidate_stage=candidate,
        previous_candidate_streak=streak,
        state_memory=memory,
    )


def _peaks(days=0):
    return {
        "runningPeakCloseByMember": {str(index): 100 for index in range(10)},
        "runningPeakDateByMember": {str(index): "2026-08-01" for index in range(10)},
        "daysSinceMeaningfulExpansion": days,
    }


def test_declining_recovery_is_base_candidate_and_confirmation():
    first = evaluate_lifecycle(_input([5] * 10, previous=DECLINING, memory=_peaks(5)))
    second = evaluate_lifecycle(
        _input(
            [5] * 10,
            previous=DECLINING,
            memory=first.state_memory,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
        )
    )
    assert first.candidate_stage == BASE
    assert first.final_stage == DECLINING
    assert second.final_stage == BASE
    assert second.state_memory["cycleEnded"] is True
    assert second.state_memory["mainRiseAncestry"] is False


def test_base_recovery_candidate_can_be_cancelled_by_bounded_repair():
    first = evaluate_lifecycle(
        _input(
            [-6] * 10, previous=BASE, memory=_peaks(5), closes=[60] * 10, previous_closes=[100] * 10
        )
    )
    second = evaluate_lifecycle(
        _input(
            [5] * 10,
            previous=BASE,
            memory=first.state_memory,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
            closes=[100] * 10,
            previous_closes=[60] * 10,
        )
    )
    assert first.candidate_stage == DECLINING
    assert first.final_stage == BASE
    assert second.final_stage == BASE
    assert second.transition_reason == "DECLINING_CANDIDATE_CANCELLED_GENUINE_REPAIR"


def test_base_persists_through_ordinary_noise():
    result = evaluate_lifecycle(_input([0] * 10, previous=BASE, memory=_peaks(3)))
    assert result.final_stage == BASE
    assert result.candidate_stage is None


def test_base_to_declining_is_legal_after_confirmed_deterioration():
    first = evaluate_lifecycle(
        _input(
            [-6] * 10, previous=BASE, memory=_peaks(5), closes=[60] * 10, previous_closes=[100] * 10
        )
    )
    second = evaluate_lifecycle(
        _input(
            [-1] * 10,
            previous=BASE,
            memory=first.state_memory,
            candidate=DECLINING,
            streak=first.confirmation_state["candidateStreak"],
            closes=[59] * 10,
            previous_closes=[60] * 10,
        )
    )
    assert second.final_stage == DECLINING
    assert second.transition_reason == "DECLINING_PENDING_CONFIRMATION_SATISFIED"


def test_base_to_sprouting_uses_existing_local_leader_gate():
    changes = [5, -1, -1, -1, -1, -1, -1, -1, -1, -1]
    first = evaluate_lifecycle(_input(changes, previous=BASE, memory=_peaks(2)))
    second = evaluate_lifecycle(
        _input(changes, previous=BASE, memory=first.state_memory, candidate=SPROUTING, streak=1)
    )
    assert first.candidate_stage == SPROUTING
    assert second.final_stage == SPROUTING


def test_base_to_fermenting_is_allowed_without_sprouting():
    changes = [1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
    first = evaluate_lifecycle(_input(changes, previous=BASE, memory=_peaks(2)))
    second = evaluate_lifecycle(
        _input(changes, previous=BASE, memory=first.state_memory, candidate=FERMENTING, streak=1)
    )
    assert first.candidate_stage == FERMENTING
    assert second.final_stage == FERMENTING


def test_base_direct_main_rise_is_blocked():
    result = evaluate_lifecycle(_input([8] * 10, previous=BASE, memory=_peaks(2)))
    assert result.candidate_stage != MAIN_RISE
    assert result.final_stage == BASE


def test_related_only_recovery_has_no_base_authority():
    result = evaluate_lifecycle(
        _input([8] * 4, previous=DECLINING, memory=_peaks(2), roles=["RELATED"] * 4, expected=4)
    )
    assert result.candidate_stage is None
    assert result.final_stage == DECLINING


def test_mature_requires_main_rise_ancestry():
    result = evaluate_lifecycle(_input([2] * 10, previous=MATURE, memory=_peaks(2)))
    assert result.candidate_stage != MATURE
    assert result.final_stage == MATURE


def test_cycle_reset_clears_old_segment_and_new_cycle_starts_at_one():
    first = evaluate_lifecycle(_input([5] * 10, previous=FERMENTING))
    rise = evaluate_lifecycle(
        _input(
            [5] * 10, previous=FERMENTING, candidate=MAIN_RISE, streak=1, memory=first.state_memory
        )
    )
    assert rise.final_stage == MAIN_RISE
    assert rise.main_rise_segment == 1
    breakdown = evaluate_lifecycle(
        _input(
            [-8] * 10,
            previous=MAIN_RISE,
            memory=rise.state_memory,
            closes=[80] * 10,
            previous_closes=[100] * 10,
        )
    )
    mature = evaluate_lifecycle(
        _input(
            [-1] * 10,
            previous=MAIN_RISE,
            memory=breakdown.state_memory,
            closes=[79] * 10,
            previous_closes=[80] * 10,
        )
    )
    decline_candidate = evaluate_lifecycle(
        _input(
            [-6] * 10,
            previous=MATURE,
            memory=mature.state_memory,
            closes=[60] * 10,
            previous_closes=[100] * 10,
        )
    )
    decline = evaluate_lifecycle(
        _input(
            [-1] * 10,
            previous=MATURE,
            memory=decline_candidate.state_memory,
            candidate=DECLINING,
            streak=1,
            closes=[59] * 10,
            previous_closes=[60] * 10,
        )
    )
    base_candidate = evaluate_lifecycle(
        _input([5] * 10, previous=DECLINING, memory=decline.state_memory)
    )
    base = evaluate_lifecycle(
        _input(
            [5] * 10,
            previous=DECLINING,
            memory=base_candidate.state_memory,
            candidate=BASE,
            streak=1,
        )
    )
    ferment_candidate = evaluate_lifecycle(
        _input([1, 1, 1, 1, 1, 1, 1, 0, 0, 0], previous=BASE, memory=base.state_memory)
    )
    ferment = evaluate_lifecycle(
        _input(
            [1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
            previous=BASE,
            memory=ferment_candidate.state_memory,
            candidate=FERMENTING,
            streak=1,
        )
    )
    new_main = evaluate_lifecycle(
        _input(
            [5] * 10,
            previous=FERMENTING,
            memory=ferment.state_memory,
            candidate=MAIN_RISE,
            streak=1,
        )
    )
    assert decline.final_stage == DECLINING
    assert base.final_stage == BASE
    assert base.main_rise_segment is None
    assert new_main.final_stage == MAIN_RISE
    assert new_main.main_rise_segment == 1
    assert new_main.cycle_number == 2
