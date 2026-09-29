from datetime import date

import pytest

from topicpilot_api.topic_engine import (
    ABSOLUTE,
    CALIBRATION_REQUIRED,
    CORE,
    PROVISIONAL,
    RELATED,
    RELATIVE,
    REPRESENTATIVE,
    GradePolicy,
    ResponseCurve,
    RoleMemberObservation,
    RoleResponseCurves,
    TopicStrengthPolicy,
    benchmark_for_market,
    evaluate_topic_strength,
)
from topicpilot_api.topic_lifecycle_role_evidence import (
    LifecycleRoleEvidenceError,
    LifecycleRoleObservation,
    RoleDiffusionThresholds,
    build_role_diffusion_evidence,
)

AS_OF = date(2026, 8, 7)


def _curve(version: str) -> ResponseCurve:
    return ResponseCurve(
        version,
        ((-10.0, 0.0), (-2.0, 0.1), (0.0, 0.5), (1.0, 0.7), (3.0, 0.95), (10.0, 1.0)),
    )


def _policy() -> TopicStrengthPolicy:
    curves = RoleResponseCurves(_curve("rep"), _curve("core"), _curve("related"))
    return TopicStrengthPolicy(
        policy_version="topic-strength-fixture.v1.provisional",
        calculation_version="topic-strength-fixture-calc.v1",
        status=PROVISIONAL,
        absolute_curves=curves,
        relative_curves=curves,
        grade_policy=GradePolicy("grade-fixture.v1", 85.0, 65.0, 0.60, -0.5),
    )


def _member(
    member_id: str,
    role: str,
    value: float,
    *,
    market: str = "TWSE",
    benchmark: float | None = 0.0,
    importance: float | None = None,
) -> RoleMemberObservation:
    return RoleMemberObservation(
        member_id,
        role,
        value,
        market,
        benchmark,
        importance
        if importance is not None
        else 1.0
        if role == CORE
        else 1.5
        if role == REPRESENTATIVE
        else None,
    )


def test_role_caps_prevent_rep_and_related_from_rescuing_weak_core():
    result = evaluate_topic_strength(
        "topic-1",
        AS_OF,
        (
            _member("rep", REPRESENTATIVE, 8.0),
            _member("core", CORE, -1.0),
            _member("related", RELATED, 8.0),
        ),
        view=ABSOLUTE,
        policy=_policy(),
    )

    contributions = {item.role: item.contribution for item in result.role_evidence}
    assert contributions[CORE] < 30.0
    assert result.strength is not None and result.strength < 65.0
    assert result.grade == "B"


def test_broad_core_strength_outranks_one_core_outlier():
    outlier = evaluate_topic_strength(
        "topic-1",
        AS_OF,
        tuple(
            [_member("rep", REPRESENTATIVE, 1.0)]
            + [_member(f"c{i}", CORE, 9.0 if i == 0 else 0.0) for i in range(4)]
        ),
        view=ABSOLUTE,
        policy=_policy(),
    )
    broad = evaluate_topic_strength(
        "topic-1",
        AS_OF,
        tuple(
            [_member("rep", REPRESENTATIVE, 1.0)]
            + [_member(f"c{i}", CORE, 3.0) for i in range(4)]
        ),
        view=ABSOLUTE,
        policy=_policy(),
    )
    assert broad.strength is not None and outlier.strength is not None
    assert broad.strength > outlier.strength


def test_related_tiny_moves_are_not_near_max_diffusion_credit():
    result = evaluate_topic_strength(
        "topic-1",
        AS_OF,
        (
            _member("rep", REPRESENTATIVE, 0.0),
            _member("core", CORE, 0.0),
            _member("r1", RELATED, 0.1),
            _member("r2", RELATED, 0.1),
        ),
        view=ABSOLUTE,
        policy=_policy(),
    )
    related = next(item for item in result.role_evidence if item.role == RELATED)
    assert related.contribution is not None and related.contribution < 8.0


def test_relative_view_uses_each_member_market_benchmark():
    assert benchmark_for_market("TWSE") == "TAIEX"
    assert benchmark_for_market("TPEx") == "TPEX_INDEX"
    result = evaluate_topic_strength(
        "topic-1",
        AS_OF,
        (
            _member("twse", CORE, 1.0, market="TWSE", benchmark=-5.0),
            _member("tpex", CORE, 1.0, market="TPEX", benchmark=-4.0),
        ),
        view=RELATIVE,
        policy=_policy(),
    )
    assert result.relative_strength is not None and result.relative_strength > 50.0
    assert dict(result.benchmark_by_market) == {"TPEX": "TPEX_INDEX", "TWSE": "TAIEX"}


def test_relative_weakness_does_not_change_absolute_contract():
    absolute = evaluate_topic_strength(
        "topic-1",
        AS_OF,
        (_member("core", CORE, 2.0, benchmark=5.0),),
        view=ABSOLUTE,
        policy=_policy(),
    )
    relative = evaluate_topic_strength(
        "topic-1",
        AS_OF,
        (_member("core", CORE, 2.0, benchmark=5.0),),
        view=RELATIVE,
        policy=_policy(),
    )
    assert absolute.absolute_strength is not None and relative.relative_strength is not None
    assert absolute.absolute_strength > relative.relative_strength


def test_no_curve_is_bounded_as_calibration_required():
    result = evaluate_topic_strength(
        "topic-1",
        AS_OF,
        (_member("core", CORE, 3.0),),
        view=ABSOLUTE,
        policy=TopicStrengthPolicy(),
    )
    assert result.status == CALIBRATION_REQUIRED
    assert result.strength is None
    assert result.grade is None


def test_role_diffusion_evidence_has_no_dynamic_leader_or_role_blend():
    thresholds = RoleDiffusionThresholds(1.0, 0.5, 1.0, 0.5, 1.0, 0.6)
    evidence = build_role_diffusion_evidence(
        (
            LifecycleRoleObservation("rep", REPRESENTATIVE, 0.0),
            LifecycleRoleObservation("c1", CORE, 3.0),
            LifecycleRoleObservation("c2", CORE, 3.0),
            LifecycleRoleObservation("r1", RELATED, 2.0),
            LifecycleRoleObservation("r2", RELATED, 2.0),
        ),
        thresholds=thresholds,
    )
    assert evidence.dynamic_leader_authority is False
    assert evidence.role_blend_authority is False
    assert evidence.fermenting_candidate is False
    assert evidence.main_rise_evidence is True
    assert evidence.relative_authority == "CONFIRMATION_ONLY"


def test_lifecycle_rejects_a_fourth_dynamic_leader_role():
    with pytest.raises(LifecycleRoleEvidenceError):
        build_role_diffusion_evidence(
            (LifecycleRoleObservation("x", "LEADER", 9.0),),
            thresholds=RoleDiffusionThresholds(1.0, 0.5, 1.0, 0.5, 1.0, 0.6),
        )
