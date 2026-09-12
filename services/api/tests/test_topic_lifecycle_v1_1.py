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

ROLES = ["REPRESENTATIVE"] + ["CORE"] * 9


def _input(
    changes,
    *,
    trading_date=date(2026, 8, 10),
    roles=None,
    previous=None,
    memory=None,
    closes=None,
    previous_closes=None,
    candidate=None,
    streak=0,
    expected=None,
):
    roles = roles or (["REPRESENTATIVE"] + ["CORE"] * (len(changes) - 1))
    closes = closes or [100.0] * len(changes)
    previous_closes = previous_closes or closes
    return LifecycleInput(
        topic_id="v1.1-test-topic",
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
        "runningPeakDateByMember": {
            str(index): "2026-08-01" for index in range(10)
        },
        "daysSinceMeaningfulExpansion": days,
    }


def _decline_candidate():
    return evaluate_lifecycle(
        _input(
            [-6, -5, -4, -4, -4, -4, 0, 0, 1, 1],
            previous=MATURE,
            memory=_peaks(5),
            closes=[60] * 10,
            previous_closes=[100] * 10,
        )
    )


def test_01_main_rise_normal_expansion():
    first = evaluate_lifecycle(_input([5] * 10, previous=FERMENTING))
    second = evaluate_lifecycle(
        _input(
            [5] * 10,
            previous=FERMENTING,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
        )
    )
    assert first.candidate_stage == MAIN_RISE
    assert second.final_stage == MAIN_RISE


def test_02_main_rise_one_day_ordinary_pullback():
    result = evaluate_lifecycle(
        _input(
            [1] * 10,
            previous=MAIN_RISE,
            memory=_peaks(2),
            closes=[98] * 10,
            previous_closes=[100] * 10,
        )
    )
    assert result.final_stage == MAIN_RISE
    assert result.state_memory["structuralBreakdownPending"] is False
    assert result.confirmation_state["persistenceClassification"] == "NORMAL_PULLBACK"


def test_03_main_rise_severe_breakdown_creates_candidate_only():
    result = evaluate_lifecycle(
        _input(
            [-8] * 10,
            previous=MAIN_RISE,
            memory=_peaks(1),
            closes=[80] * 10,
            previous_closes=[100] * 10,
        )
    )
    assert result.candidate_stage == MATURE
    assert result.final_stage == MAIN_RISE
    assert result.transition_reason == "STRUCTURAL_BREAKDOWN_CANDIDATE"
    assert result.state_memory["structuralBreakdownPending"] is True


def test_04_severe_breakdown_followed_by_genuine_repair_cancels():
    first = evaluate_lifecycle(
        _input(
            [-8] * 10,
            previous=MAIN_RISE,
            memory=_peaks(1),
            closes=[80] * 10,
            previous_closes=[100] * 10,
        )
    )
    repaired = evaluate_lifecycle(
        _input(
            [5] * 10,
            previous=MAIN_RISE,
            memory=first.state_memory,
            closes=[105] * 10,
            previous_closes=[80] * 10,
        )
    )
    assert repaired.final_stage == MAIN_RISE
    assert repaired.transition_reason == "STRUCTURAL_BREAKDOWN_CANCELLED_GENUINE_REPAIR"
    assert repaired.state_memory["structuralBreakdownPending"] is False


def test_05_severe_breakdown_followed_by_persistent_weakness_confirms():
    first = evaluate_lifecycle(
        _input(
            [-8] * 10,
            previous=MAIN_RISE,
            memory=_peaks(1),
            closes=[80] * 10,
            previous_closes=[100] * 10,
        )
    )
    confirmed = evaluate_lifecycle(
        _input(
            [-1] * 10,
            previous=MAIN_RISE,
            memory=first.state_memory,
            closes=[79] * 10,
            previous_closes=[80] * 10,
        )
    )
    assert confirmed.final_stage == MATURE
    assert confirmed.transition_reason == "STRUCTURAL_BREAKDOWN_CONFIRMED"


def test_06_natural_five_session_expansion_stall_remains():
    memory = None
    result = None
    for index in range(5):
        result = evaluate_lifecycle(
            _input(
                [0] * 10,
                trading_date=date(2026, 8, 10 + index),
                previous=MAIN_RISE,
                memory=memory,
                closes=[100] * 10,
                previous_closes=[100] * 10,
            )
        )
        memory = result.state_memory
    assert result.final_stage == MATURE
    assert result.transition_reason == "MAIN_RISE_EXPANSION_STALLED_5_SESSIONS"


def test_07_structural_fast_path_matures_before_five_session_clock():
    first = evaluate_lifecycle(
        _input(
            [-8] * 10,
            previous=MAIN_RISE,
            memory=_peaks(0),
            closes=[80] * 10,
            previous_closes=[100] * 10,
        )
    )
    second = evaluate_lifecycle(
        _input(
            [-1] * 10,
            previous=MAIN_RISE,
            memory=first.state_memory,
            closes=[79] * 10,
            previous_closes=[80] * 10,
        )
    )
    assert second.final_stage == MATURE
    assert second.days_since_meaningful_expansion < 5


def test_08_related_only_collapse_with_healthy_lead_core_holds_main_rise():
    roles = [*ROLES, "RELATED", "RELATED"]
    result = evaluate_lifecycle(
        _input(
            [2] * 10 + [-10, -10],
            roles=roles,
            expected=12,
            previous=MAIN_RISE,
            memory=_peaks(1),
        )
    )
    assert result.final_stage == MAIN_RISE
    assert result.candidate_stage != MATURE


def test_09_weak_breadth_without_severe_price_damage_holds_main_rise():
    result = evaluate_lifecycle(
        _input(
            [1, 1, 1, 1, 1, -1, -1, -1, -1, -1],
            previous=MAIN_RISE,
            memory=_peaks(1),
            closes=[95] * 10,
            previous_closes=[100] * 10,
        )
    )
    assert result.final_stage == MAIN_RISE
    assert result.state_memory["structuralBreakdownPending"] is False


def test_10_mature_ordinary_weak_day_is_not_declining():
    result = evaluate_lifecycle(
        _input(
            [0] * 10,
            previous=MATURE,
            memory=_peaks(5),
            closes=[95] * 10,
            previous_closes=[100] * 10,
        )
    )
    assert result.final_stage == MATURE
    assert result.candidate_stage != DECLINING


def test_11_mature_declining_candidate_is_pending():
    result = _decline_candidate()
    assert result.candidate_stage == DECLINING
    assert result.final_stage == MATURE
    assert result.state_memory["decliningPending"] is True
    assert result.transition_reason == "DECLINING_CANDIDATE_PENDING_CONFIRMATION"


def test_12_declining_candidate_plus_genuine_repair_cancels():
    first = _decline_candidate()
    result = evaluate_lifecycle(
        _input(
            [5] * 10,
            previous=MATURE,
            memory=first.state_memory,
            closes=[100] * 10,
            previous_closes=[60] * 10,
        )
    )
    assert result.final_stage == MATURE
    assert result.transition_reason == "DECLINING_CANDIDATE_CANCELLED_GENUINE_REPAIR"
    assert result.state_memory["decliningPending"] is False


def test_13_declining_candidate_plus_persistent_deterioration_confirms():
    first = _decline_candidate()
    result = evaluate_lifecycle(
        _input(
            [-1] * 10,
            previous=MATURE,
            memory=first.state_memory,
            closes=[59] * 10,
            previous_closes=[60] * 10,
        )
    )
    assert result.final_stage == DECLINING
    assert result.transition_reason == "DECLINING_PENDING_CONFIRMATION_SATISFIED"


def test_14_declining_candidate_plus_worse_deterioration_confirms():
    first = _decline_candidate()
    result = evaluate_lifecycle(
        _input(
            [-8] * 10,
            previous=MATURE,
            memory=first.state_memory,
            closes=[50] * 10,
            previous_closes=[60] * 10,
        )
    )
    assert result.final_stage == DECLINING
    assert result.state_memory["decliningPending"] is False


def test_15_pending_decline_does_not_disappear_on_neutral_session():
    first = _decline_candidate()
    neutral = evaluate_lifecycle(
        _input(
            [1, -1, -1, -1, -1, -1, -1, -1, 1, 1],
            previous=MATURE,
            memory=first.state_memory,
            closes=[60] * 10,
            previous_closes=[60] * 10,
        )
    )
    assert neutral.final_stage == MATURE
    assert neutral.candidate_stage == DECLINING
    assert neutral.state_memory["decliningPending"] is True
    assert neutral.transition_reason == "DECLINING_PENDING_NEUTRAL_BOUNDED"


def test_16_neutral_pending_decline_has_bounded_resolution():
    first = _decline_candidate()
    neutral = evaluate_lifecycle(
        _input(
            [1, -1, -1, -1, -1, -1, -1, -1, 1, 1],
            previous=MATURE,
            memory=first.state_memory,
            closes=[60] * 10,
            previous_closes=[60] * 10,
        )
    )
    resolved = evaluate_lifecycle(
        _input(
            [1, -1, -1, -1, -1, -1, -1, -1, 1, 1],
            previous=MATURE,
            memory=neutral.state_memory,
            closes=[60] * 10,
            previous_closes=[60] * 10,
        )
    )
    assert resolved.final_stage == DECLINING
    assert resolved.state_memory["decliningPending"] is False


def test_17_declining_recovery_is_adjacent_and_confirmed():
    first = evaluate_lifecycle(
        _input([5] * 10, previous=DECLINING, memory=_peaks(5))
    )
    second = evaluate_lifecycle(
        _input(
            [5] * 10,
            previous=DECLINING,
            memory=first.state_memory,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
        )
    )
    assert first.candidate_stage == "BASE"
    assert first.final_stage == DECLINING
    assert second.final_stage == "BASE"


def test_18_declining_cannot_jump_directly_to_main_rise():
    result = evaluate_lifecycle(
        _input([8] * 10, previous=DECLINING, memory=_peaks(5))
    )
    assert result.candidate_stage == "BASE"
    assert result.final_stage == DECLINING
    assert result.transition_reason == "ORDINARY_SIGNAL_PENDING_CONFIRMATION"


def test_19_main_rise_segment_memory_is_deterministic():
    values = [
        _input([5] * 10, previous=FERMENTING),
        _input([5] * 10, previous=FERMENTING, candidate=MAIN_RISE, streak=1),
    ]
    first = [evaluate_lifecycle(value) for value in values]
    second = [evaluate_lifecycle(value) for value in values]
    assert [item.state_memory for item in first] == [item.state_memory for item in second]


def test_20_expansion_clock_reentry_fix_remains():
    memory = {
        **_peaks(7),
        "mainRiseSegment": 1,
        "segmentEntryDate": "2026-08-01",
        "segmentAnchorDate": "2026-08-01",
    }
    first = evaluate_lifecycle(
        _input([8, 7, 6, 5, 5, 4, 4, 3, 3, 2], previous=MATURE, memory=memory)
    )
    second = evaluate_lifecycle(
        _input(
            [8, 7, 6, 5, 5, 4, 4, 3, 3, 2],
            previous=MATURE,
            memory=first.state_memory,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
        )
    )
    assert second.final_stage == MAIN_RISE
    assert second.main_rise_segment == 2
    assert second.days_since_meaningful_expansion == 7


def test_21_missing_price_member_fails_closed():
    result = evaluate_lifecycle(
        _input([5, 5, None], roles=["REPRESENTATIVE", "CORE", "CORE"], expected=5)
    )
    assert result.final_stage is None
    assert result.data_status == "INSUFFICIENT_DATA"


def test_22_related_only_main_rise_remains_impossible():
    result = evaluate_lifecycle(
        _input([8, 7, 6, 5], roles=["RELATED"] * 4)
    )
    assert result.candidate_stage == SPROUTING
    assert result.candidate_stage != MAIN_RISE
