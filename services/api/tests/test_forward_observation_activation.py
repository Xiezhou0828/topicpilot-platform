import pytest

from topicpilot_api.topic_engine.forward_observation_activation import (
    ACCEPTED_OBSERVATION_FLAGS,
    OWNER_REVIEW_ACCEPTED,
    ForwardObservationActivationError,
    checkpoint_statuses,
    derive_observation_flags,
)


def _flags(**overrides: object) -> list[str]:
    values: dict[str, object] = {
        "absolute_grade": "B",
        "relative_grade": "B",
        "formal_daily_grade": "B",
        "lifecycle_before": "BASE",
        "lifecycle_candidate": None,
        "lifecycle_after": "BASE",
    }
    values.update(overrides)
    return derive_observation_flags(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    (
        (
            {
                "absolute_grade": "A",
                "relative_grade": "S",
                "formal_daily_grade": "A",
                "lifecycle_candidate": "MAIN_RISE",
            },
            {"STRONG_GRADE_WITH_HELD_LIFECYCLE_CANDIDATE"},
        ),
        (
            {
                "absolute_grade": "D",
                "relative_grade": "D",
                "formal_daily_grade": "D",
                "lifecycle_candidate": "DECLINING",
            },
            {"GRADE_D_WHILE_DECLINING_PENDING"},
        ),
        (
            {"absolute_grade": "S", "relative_grade": "B", "formal_daily_grade": "S"},
            {"ABS_REL_GRADE_DIVERGENCE"},
        ),
        (
            {
                "absolute_grade": "B",
                "relative_grade": "B",
                "formal_daily_grade": "B",
                "lifecycle_before": "MAIN_RISE",
                "lifecycle_after": "MATURE",
            },
            {"MATURE_OR_MAIN_RISE_WITH_GRADE_B"},
        ),
    ),
)
def test_accepted_flags_are_diagnostic_and_deterministic(kwargs, expected):
    assert set(_flags(**kwargs)) == expected
    assert set(_flags(**kwargs)).issubset(set(ACCEPTED_OBSERVATION_FLAGS))


@pytest.mark.parametrize("count", [0, 1, 19, 20, 21, 39, 40, 59, 60])
def test_checkpoint_progress_contract(count: int):
    statuses = checkpoint_statuses(count)
    if count == 0:
        assert set(statuses.values()) == {"NOT_STARTED"}
    else:
        assert statuses["OBSERVATION_20D"] in {"IN_PROGRESS", "READY_FOR_OWNER_REVIEW"}
        assert statuses["OBSERVATION_40D"] in {"IN_PROGRESS", "READY_FOR_OWNER_REVIEW"}
        assert statuses["OBSERVATION_60D"] in {"IN_PROGRESS", "READY_FOR_OWNER_REVIEW"}
    if count >= 20:
        assert statuses["OBSERVATION_20D"] == "READY_FOR_OWNER_REVIEW"
    if count >= 40:
        assert statuses["OBSERVATION_40D"] == "READY_FOR_OWNER_REVIEW"
    if count >= 60:
        assert statuses["OBSERVATION_60D"] == "READY_FOR_OWNER_REVIEW"
    assert "REVIEWED" not in statuses.values()


def test_owner_acceptance_is_required_for_activation():
    from topicpilot_api.topic_engine.forward_observation_activation import (
        assert_owner_review_accepted,
    )

    assert_owner_review_accepted(OWNER_REVIEW_ACCEPTED)
    with pytest.raises(ForwardObservationActivationError, match="OWNER_REVIEW_NOT_ACCEPTED"):
        assert_owner_review_accepted("OWNER_REVIEW_REQUIRED")
