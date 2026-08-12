from datetime import date

from topicpilot_api.topic_engine import EvaluationBundle, evaluate


def test_topic_engine_is_deterministic_and_versioned() -> None:
    bundle = EvaluationBundle(
        "topic-state-v0", date(2026, 8, 8), topics=({"id": "b"}, {"id": "a"}),
        memberships=({"topic_id": "a", "instrument_id": "i1"},),
        observations=({"topic_id": "a", "instrument_id": "i1"},),
    )
    first = evaluate(bundle)
    assert [state.topic_id for state in first] == ["a", "b"]
    assert first[0].status == "READY_UNSCORED" and first[0].coverage == 1
    assert first[0].calculation_version == "topic-state-v0"
    assert evaluate(bundle) == first


def test_hierarchy_rolls_up_membership_and_supports_multiple_parents() -> None:
    bundle = EvaluationBundle(
        "v0", date(2026, 8, 8), topics=({"id": "root"}, {"id": "left"}, {"id": "right"}),
        hierarchy=(
            {"parent_id": "root", "child_id": "left"},
            {"parent_id": "root", "child_id": "right"},
        ),
        memberships=(
            {"topic_id": "left", "instrument_id": "i1"},
            {"topic_id": "right", "instrument_id": "i2"},
        ),
        observations=({"topic_id": "left", "instrument_id": "i1"},),
    )
    states = {state.topic_id: state for state in evaluate(bundle)}
    assert states["root"].member_count == 2 and states["root"].observed_member_count == 1
    assert states["root"].coverage == 0.5


def test_empty_and_invalid_inputs_are_explicit() -> None:
    empty = evaluate(EvaluationBundle("v0", date(2026, 8, 8), topics=({"id": "a"},)))[0]
    assert empty.status == "DATA_INSUFFICIENT" and empty.coverage is None
    invalid = evaluate(
        EvaluationBundle(
            "v0", date(2026, 8, 8), topics=({"id": "a"},),
            hierarchy=({"parent_id": "a", "child_id": "missing"},),
        )
    )[0]
    assert invalid.status == "INVALID_INPUT"
