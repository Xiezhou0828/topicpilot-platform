import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from services.api.tools.capture_owner_seeded_v0_forward_observation import (
    OBSERVATION_SCHEMA_VERSION,
    POLICY_HASH,
    ForwardObservationCaptureError,
    _write_idempotent,
    capture_observation,
)

from topicpilot_api.topic_engine.forward_observation_activation import ACTIVATION_TASK_ID
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
        "activation_task_id": ACTIVATION_TASK_ID,
        "owner_review_status": "OWNER_REVIEW_ACCEPTED_WITH_OBSERVATION_FLAGS",
        "implementation_sha": "a" * 40,
        "session": {
            "is_governed_trading_session": True,
            "status": "POST_CLOSE",
            "evaluable": True,
            "timezone": "Asia/Taipei",
            "post_close_at": "2026-09-29T13:35:00+08:00",
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
    assert result["implementation_sha"] == "a" * 40
    assert result["owner_review_status"] == "OWNER_REVIEW_ACCEPTED_WITH_OBSERVATION_FLAGS"


def test_activation_schema_accepts_capture_output():
    schema_path = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "reports"
        / "TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-FORWARD-OBSERVATION-ACTIVATION-003"
        / "forward-observation-schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(capture_observation(_payload()))


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

    payload = _payload()
    payload["session"]["status"] = "MARKET_CLOSED"
    with pytest.raises(ForwardObservationCaptureError, match="MARKET_CLOSED"):
        capture_observation(payload)

    payload = _payload()
    payload["as_of_date"] = "2026-10-03"
    payload["observation_start_date"] = "2026-10-03"
    payload["session"]["post_close_at"] = "2026-10-03T13:35:00+08:00"
    with pytest.raises(ForwardObservationCaptureError, match="MARKET_CLOSED"):
        capture_observation(payload)


def test_capture_requires_owner_acceptance_and_post_close_boundary():
    payload = _payload()
    payload["owner_review_status"] = "OWNER_REVIEW_REQUIRED"
    with pytest.raises(ForwardObservationCaptureError, match="OWNER_REVIEW_NOT_ACCEPTED"):
        capture_observation(payload)

    payload = _payload()
    payload["session"]["post_close_at"] = "2026-09-29T13:34:59+08:00"
    with pytest.raises(ForwardObservationCaptureError, match="POST_CLOSE_BOUNDARY_NOT_REACHED"):
        capture_observation(payload)

    payload = _payload()
    payload["session"]["evaluable"] = False
    with pytest.raises(ForwardObservationCaptureError, match="NOT_EVALUABLE"):
        capture_observation(payload)


def test_capture_keeps_small_sample_as_explicit_x_without_scoring_it():
    payload = _payload()
    payload["members"] = payload["members"][:2]
    result = capture_observation(payload)
    assert result["scores"]["absolute_grade"] == "X"
    assert result["scores"]["absolute_total"] is None
    assert result["quality_flags"]["SMALL_SAMPLE_X"] is True


def test_capture_artifact_is_idempotent_and_conflicts_fail_closed(tmp_path):
    observation = capture_observation(_payload())
    assert _write_idempotent(tmp_path, observation) == "CREATED"
    assert _write_idempotent(tmp_path, observation) == "NOOP_IDENTICAL_ARTIFACT"
    conflicting = dict(observation)
    conflicting["implementation_sha"] = "b" * 40
    with pytest.raises(ForwardObservationCaptureError, match="EXISTING_ARTIFACT_CONFLICT"):
        _write_idempotent(tmp_path, conflicting)
