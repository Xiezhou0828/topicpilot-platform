import pytest

from tools.capture_owner_seeded_v0_forward_observation import (
    OBSERVATION_SCHEMA_VERSION,
    POLICY_HASH,
    ForwardObservationCaptureError,
    capture_observation,
)
from topicpilot_api.topic_engine.owner_seeded_v0_policy import (
    CORE,
    DEFAULT_POLICY,
    RELATED,
    REPRESENTATIVE,
)


def _payload() -> dict[str, object]:
    return {
        "as_of_date": "2026-09-29",
        "observation_start_date": "2026-09-29",
        "policy_id": "topic-strength-lifecycle.owner-seeded-v0",
        "policy_version": "v0",
        "policy_hash": POLICY_HASH,
        "session": {
            "is_governed_trading_session": True,
            "authority_version": "calendar-v1",
        },
        "topic_id": "topic-forward-test",
        "topic_name": "Forward test topic",
        "formal_member_authority_version": "formal-members-v1",
        "structural_role_authority_version": "roles-v1",
        "benchmark_authority": {"source": "official-index", "version": "bench-v1"},
        "members": [
            {
                "member_id": "rep-1",
                "role": REPRESENTATIVE,
                "absolute_return_pct": 1.0,
                "score_importance": 1.5,
                "market": "TWSE",
                "benchmark_return_pct": 0.0,
            },
            {
                "member_id": "core-1",
                "role": CORE,
                "absolute_return_pct": 2.0,
                "score_importance": 1.0,
                "market": "TWSE",
                "benchmark_return_pct": 0.0,
            },
            {
                "member_id": "related-1",
                "role": RELATED,
                "absolute_return_pct": 1.0,
                "score_importance": None,
                "market": "TWSE",
                "benchmark_return_pct": 0.0,
            },
        ],
        "lifecycle_state": {
            "stage": "BASE",
            "main_rise_occurred_in_cycle": False,
            "candidate_stage": None,
            "candidate_streak": 0,
            "history": [],
        },
    }


def test_capture_is_hash_bound_and_contains_required_daily_fields():
    result = capture_observation(_payload())
    assert result["observation_schema_version"] == OBSERVATION_SCHEMA_VERSION
    assert result["policy_hash"] == DEFAULT_POLICY.policy_hash() == POLICY_HASH
    assert result["formal_member_count"] == 3
    assert result["representative_count"] == 1
    assert result["core_count"] == 1
    assert result["related_count"] == 1
    assert result["quality_flags"]["FAIL_CLOSED_REASON"] is None
    assert result["formal_output_boundary"]["formal_output_overridden"] is False


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("policy_hash", "wrong", "POLICY_HASH_MISMATCH"),
        ("observation_start_date", "2026-09-30", "AS_OF_DATE_BEFORE_OBSERVATION_START"),
    ),
)
def test_capture_rejects_unbound_or_unauthorized_input(field, value, error):
    payload = _payload()
    payload[field] = value
    with pytest.raises(ForwardObservationCaptureError, match=error):
        capture_observation(payload)


def test_capture_rejects_non_trading_session_and_missing_benchmark():
    payload = _payload()
    payload["session"]["is_governed_trading_session"] = False
    with pytest.raises(ForwardObservationCaptureError, match="NOT_A_GOVERNED_TRADING_SESSION"):
        capture_observation(payload)

    payload = _payload()
    payload["members"][0]["benchmark_return_pct"] = None
    with pytest.raises(ForwardObservationCaptureError, match="BENCHMARK_DATA_INCOMPLETE"):
        capture_observation(payload)


def test_capture_keeps_small_sample_as_explicit_x_without_scoring_it():
    payload = _payload()
    payload["members"] = payload["members"][:2]
    result = capture_observation(payload)
    assert result["scores"]["absolute_grade"] == "X"
    assert result["scores"]["absolute_total"] is None
    assert result["quality_flags"]["SMALL_SAMPLE_X"] is True
