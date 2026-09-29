from datetime import date

import pytest

from topicpilot_api.topic_engine.owner_seeded_v0_policy import (
    CORE,
    DEFAULT_POLICY,
    RELATED,
    REPRESENTATIVE,
    LifecycleDayInput,
    LifecycleState,
    MemberObservation,
    OwnerSeededV0Error,
    advance_lifecycle,
    build_forward_observation_output,
    evaluate_strength_view,
    evaluate_topic,
    policy_document,
)


def members(
    rep: float | None,
    core: tuple[float | None, ...],
    related: tuple[float | None, ...],
    *,
    benchmark: float | None = 0.0,
    market: str | None = "TWSE",
) -> tuple[MemberObservation, ...]:
    result = [MemberObservation("rep-1", REPRESENTATIVE, rep, 1.50, market, benchmark)]
    result.extend(
        MemberObservation(
            f"core-{index}",
            CORE,
            value,
            1.00 if index % 2 == 0 else 0.75,
            market,
            benchmark,
        )
        for index, value in enumerate(core, start=1)
    )
    result.extend(
        MemberObservation(f"related-{index}", RELATED, value, None, market, benchmark)
        for index, value in enumerate(related, start=1)
    )
    return tuple(result)


def evidence(result, role: str):
    return next(item for item in result.role_evidence if item.role == role)


def advance_sequence(state: LifecycleState, sequence: tuple[tuple[MemberObservation, ...], ...]):
    current = state
    rows = []
    for index, observations in enumerate(sequence):
        evaluation = evaluate_topic("unit-topic", date(2026, 9, 1 + index), observations)
        current, row = advance_lifecycle(current, LifecycleDayInput(evaluation, observations))
        rows.append(row)
    return current, rows


def test_policy_identity_and_document_contract_are_stable():
    assert DEFAULT_POLICY.policy_hash() == (
        "5d29d968d9116b3288a288a8c9b15d68e51485ff88e4b58d82c2dfbbc27312ef"
    )
    document = policy_document()
    assert document["policyHash"] == DEFAULT_POLICY.policy_hash()
    policy = document["policy"]
    assert policy["relationWeight"] == "EXCLUDED"
    assert policy["lifecycleAuthority"] == {
        "absolute": "PRIMARY",
        "relative": "CONFIRMATION_ONLY",
        "dynamicLeader": False,
    }


@pytest.mark.parametrize(
    ("curve_name", "value", "expected"),
    (
        ("absolute_rep", -99.0, 0.0),
        ("absolute_rep", -2.5, 4.5),
        ("absolute_rep", 99.0, 30.0),
        ("absolute_core", 0.5, 30.5),
        ("absolute_core", 99.0, 60.0),
        ("relative_rep", 0.25, 17.0),
        ("relative_core", -0.25, 33.5),
    ),
)
def test_curves_have_owner_knots_interpolation_and_endpoint_clamping(
    curve_name: str, value: float, expected: float
):
    curve = {
        "absolute_rep": DEFAULT_POLICY.absolute_representative,
        "absolute_core": DEFAULT_POLICY.absolute_core,
        "relative_rep": DEFAULT_POLICY.relative_representative,
        "relative_core": DEFAULT_POLICY.relative_core,
    }[curve_name]
    assert curve.evaluate(value) == pytest.approx(expected)
    assert curve.evaluate(-1_000.0) == curve.knots[0][1]
    assert curve.evaluate(1_000.0) == curve.knots[-1][1]
    assert all(
        left[1] <= right[1] for left, right in zip(curve.knots, curve.knots[1:], strict=False)
    )


def test_role_caps_and_related_quality_are_explicit():
    result = evaluate_strength_view(
        members(10.0, (10.0, 10.0, 10.0), (10.0, 10.0, 10.0)),
        view="ABSOLUTE",
    )
    assert result.strength == pytest.approx(100.0)
    assert evidence(result, REPRESENTATIVE).contribution == pytest.approx(30.0)
    assert evidence(result, CORE).contribution == pytest.approx(60.0)
    assert evidence(result, RELATED).contribution == pytest.approx(10.0)

    weak_related = evaluate_strength_view(
        members(0.0, (0.0, 0.0, 0.0), (0.1, 0.1, 0.1, 0.1)),
        view="ABSOLUTE",
    )
    assert evidence(weak_related, RELATED).positive_breadth == pytest.approx(1.0)
    assert evidence(weak_related, RELATED).contribution == pytest.approx(2.5)

    no_positive_related = evaluate_strength_view(
        members(0.0, (0.0, 0.0, 0.0), (-5.0, -1.0, 0.0)),
        view="ABSOLUTE",
    )
    assert evidence(no_positive_related, RELATED).contribution == 0.0


def test_weighted_core_breadth_beats_single_outlier():
    one_outlier = evaluate_strength_view(members(1.0, (9.0, 0.0, 0.0), (0.0,)), view="ABSOLUTE")
    broad_three = evaluate_strength_view(
        members(1.0, (3.0, 3.0, 3.0, 3.0), (0.0,)), view="ABSOLUTE"
    )
    assert evidence(one_outlier, CORE).contribution < evidence(broad_three, CORE).contribution


@pytest.mark.parametrize(
    ("role", "importance"),
    ((REPRESENTATIVE, 1.00), (CORE, 1.25)),
)
def test_invalid_score_importance_is_rejected(role: str, importance: float):
    base = members(0.0, (0.0, 0.0, 0.0), ())
    if role == REPRESENTATIVE:
        observations = (
            MemberObservation("rep-1", role, 0.0, importance, "TWSE", 0.0),
            *base[1:],
        )
    else:
        observations = (
            base[0],
            MemberObservation("core-1", role, 0.0, importance, "TWSE", 0.0),
            *base[2:],
        )
    with pytest.raises(OwnerSeededV0Error, match="Score Importance"):
        evaluate_strength_view(tuple(observations), view="ABSOLUTE")


def test_related_must_not_carry_score_importance():
    observations = (
        *members(0.0, (0.0, 0.0, 0.0), ()),
        MemberObservation("related-1", RELATED, 0.0, 1.0, "TWSE", 0.0),
    )
    with pytest.raises(OwnerSeededV0Error, match="RELATED"):
        evaluate_strength_view(observations, view="ABSOLUTE")


def test_absolute_d_guard_precedes_grade_boundaries():
    guarded = evaluate_strength_view(
        members(-1.0, (-2.0, -2.0, -2.0, -2.0), (0.0,)), view="ABSOLUTE"
    )
    assert guarded.d_guard is True
    assert guarded.grade == "D"

    unguarded = evaluate_strength_view(
        members(0.0, (-2.0, -2.0, -2.0, -2.0), (0.0,)), view="ABSOLUTE"
    )
    assert unguarded.d_guard is False
    assert unguarded.grade != "D"


def test_deep_core_d_guard_and_declining_do_not_require_representative():
    core_only = tuple(
        MemberObservation(
            f"core-{index}", CORE, -3.0, 1.00 if index % 2 else 0.75, "TWSE", 0.0
        )
        for index in range(1, 4)
    )

    absolute = evaluate_strength_view(core_only, view="ABSOLUTE")
    relative = evaluate_strength_view(core_only, view="RELATIVE")
    assert absolute.d_guard is True
    assert absolute.grade == "D"
    assert relative.d_guard is True
    assert relative.grade == "D"

    state, rows = advance_sequence(
        LifecycleState(stage="MATURE", main_rise_occurred_in_cycle=True),
        (core_only, core_only),
    )
    assert state.stage == "DECLINING"
    assert rows[-1].candidate_stage == "DECLINING"


def test_relative_d_guard_requires_total_score_gate():
    guarded = evaluate_strength_view(
        members(-2.0, (-3.0, -3.0, -3.0, -3.0), (0.0,)), view="RELATIVE"
    )
    assert guarded.d_guard is True
    assert guarded.grade == "D"

    unguarded = evaluate_strength_view(
        members(-0.5, (-1.5, -1.5, -1.5, -1.5), (0.0,)), view="RELATIVE"
    )
    assert unguarded.d_guard is False


def test_relative_uses_each_member_market_benchmark_and_neutral_center():
    observations = members(1.0, (1.0, 1.0, 1.0), (), benchmark=1.0)
    result = evaluate_strength_view(observations, view="RELATIVE")
    assert result.strength == pytest.approx(50.0)
    assert dict(result.benchmark_by_market) == {"TWSE": "TAIEX"}

    tpex = members(2.0, (2.0, 2.0, 2.0), (), benchmark=2.0, market="TPEX")
    tpex_result = evaluate_strength_view(tpex, view="RELATIVE")
    assert dict(tpex_result.benchmark_by_market) == {"TPEX": "TPEX_INDEX"}
    assert tpex_result.strength == pytest.approx(50.0)


def test_missing_inputs_fail_closed_and_minimum_count_is_not_evaluable():
    two_members = members(0.0, (0.0,), ())
    result = evaluate_strength_view(two_members, view="ABSOLUTE")
    assert result.status == "NOT_EVALUABLE"
    assert result.grade == "X"

    missing_return = evaluate_strength_view(members(None, (0.0, 0.0, 0.0), ()), view="ABSOLUTE")
    assert missing_return.status == "INSUFFICIENT_DATA"
    assert missing_return.strength is None

    missing_benchmark = evaluate_strength_view(
        members(0.0, (0.0, 0.0, 0.0), (), benchmark=None), view="RELATIVE"
    )
    assert missing_benchmark.status == "INSUFFICIENT_DATA"
    assert missing_benchmark.strength is None


def test_lifecycle_owner_seeded_transitions_and_confirmation():
    sprout = members(1.0, (0.2, -0.2, 0.0), (0.0,))
    ferment = members(0.0, (1.0, 1.0, 2.0, 2.0), (-1.0,))
    main = members(1.0, (2.0, 2.0, 3.0, 3.0), (1.0, 1.0, 1.0))

    state, rows = advance_sequence(LifecycleState(), (sprout,))
    assert state.stage == "SPROUTING"
    assert rows[-1].candidate_stage == "SPROUTING"

    state, rows = advance_sequence(LifecycleState(), (ferment, ferment))
    assert state.stage == "FERMENTING"
    assert rows[-1].candidate_stage == "FERMENTING"

    state, _ = advance_sequence(LifecycleState(), (ferment, ferment, main, main))
    assert state.stage == "MAIN_RISE"


def test_lifecycle_mature_pullback_decline_and_reset():
    main = members(1.0, (2.0, 2.0, 3.0, 3.0), (1.0, 1.0, 1.0))
    stable = members(0.0, (1.0, 1.0, 1.0, 1.0), (0.0, 0.0))
    decline = members(-2.0, (-2.0, -2.0, -3.0), (-1.0, -1.0))
    reset = members(0.0, (0.5, 0.0, 0.0), (-1.0, 0.0))

    mature_state, mature_rows = advance_sequence(
        LifecycleState(stage="MAIN_RISE", main_rise_occurred_in_cycle=True),
        (main, main, stable, stable, stable, stable),
    )
    assert mature_state.stage == "MATURE"
    assert mature_rows[-1].candidate_stage == "MATURE"

    hold_state, _ = advance_sequence(
        LifecycleState(stage="MAIN_RISE", main_rise_occurred_in_cycle=True),
        (main, main, members(0.0, (0.5, 0.5, 0.5), (0.0,))),
    )
    assert hold_state.stage == "MAIN_RISE"

    decline_state, _ = advance_sequence(
        LifecycleState(stage="MATURE", main_rise_occurred_in_cycle=True),
        (decline, decline),
    )
    assert decline_state.stage == "DECLINING"

    reset_state, _ = advance_sequence(
        LifecycleState(stage="DECLINING", main_rise_occurred_in_cycle=True),
        (decline, decline, reset, reset, reset),
    )
    assert reset_state.stage == "BASE"
    assert reset_state.main_rise_occurred_in_cycle is False
    assert reset_state.history == ()


def test_relative_evidence_cannot_transition_lifecycle_and_backward_is_held():
    relative_only = members(0.0, (0.0, 0.0, 0.0), (), benchmark=-3.0)
    state, rows = advance_sequence(LifecycleState(), (relative_only,))
    assert state.stage == "BASE"
    assert rows[-1].early_relative_strength_confirmation is True

    sprout = members(1.0, (0.2, -0.2, 0.0), (0.0,))
    mature_state, rows = advance_sequence(
        LifecycleState(stage="MATURE", main_rise_occurred_in_cycle=True), (sprout,)
    )
    assert mature_state.stage == "MATURE"
    assert rows[-1].transition_reason == "ILLEGAL_BACKWARD_OR_SKIPPED_TRANSITION_HELD"


def test_forward_observation_output_has_owner_review_shape():
    observations = members(1.0, (2.0, 2.0, 3.0, 3.0), (1.0, 1.0, 1.0))
    evaluation = evaluate_topic("topic-forward", date(2026, 9, 1), observations)
    _, lifecycle = advance_lifecycle(LifecycleState(), LifecycleDayInput(evaluation, observations))
    output = build_forward_observation_output("topic-forward", evaluation, lifecycle).as_dict()

    assert {
        "trading_date",
        "topic",
        "policy_version",
        "formal_member_count",
        "observed_member_count",
        "rep_evidence",
        "core_evidence",
        "related_evidence",
        "absolute_strength",
        "absolute_grade",
        "absolute_d_guard",
        "relative_strength",
        "relative_grade",
        "relative_d_guard",
        "previous_lifecycle",
        "candidate_lifecycle",
        "final_lifecycle",
        "transition_reason",
        "coverage",
        "authority_state",
        "PM_EXPECTED_ABSOLUTE_GRADE",
        "PM_EXPECTED_RELATIVE_GRADE",
        "PM_EXPECTED_LIFECYCLE",
        "PM_RESULT",
        "PM_NOTE",
    } <= output.keys()
    assert output["authority_state"]["production_active"] is False
    assert output["PM_RESULT"] is None
