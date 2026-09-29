import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from topicpilot_api.schemas import TopicForwardObservationRead, TopicOwnerSeededV0Read
from topicpilot_api.topic_engine.forward_observation_activation import POLICY_HASH
from topicpilot_api.topic_strength_lifecycle_read_model import (
    OBSERVATION_START_PENDING,
    build_topic_strength_lifecycle_read,
)

IMPLEMENTATION_SHA = "b" * 40


def _artifact(day: date, topic_id: str = "topic-a") -> dict:
    return {
        "activation_task_id": (
            "TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-FORWARD-OBSERVATION-ACTIVATION-003"
        ),
        "owner_review_status": "OWNER_REVIEW_ACCEPTED_WITH_OBSERVATION_FLAGS",
        "as_of_date": day.isoformat(),
        "observation_start_date": "2026-10-01",
        "policy_id": "topic-strength-lifecycle.owner-seeded-v0",
        "policy_version": "v0",
        "policy_hash": POLICY_HASH,
        "implementation_sha": IMPLEMENTATION_SHA,
        "topic_id": topic_id,
        "scores": {
            "absolute_total": 84.0,
            "relative_total": 37.0,
            "absolute_grade": "S",
            "relative_grade": "B",
            "final_daily_grade": "S",
        },
        "lifecycle": {
            "lifecycle_before": "BASE",
            "lifecycle_candidate": "MAIN_RISE",
            "lifecycle_after": "BASE",
            "transition_confirmed": False,
            "transition_reason": "CONFIRMATION_PENDING",
        },
        "observation_flags": ["ABS_REL_GRADE_DIVERGENCE"],
        "observation_flag_copy": {"ABS_REL_GRADE_DIVERGENCE": "絕對與相對強度方向不同。"},
        "quality_flags": {"FAIL_CLOSED_REASON": None},
        "formal_output_boundary": {"diagnostic_only": True},
    }


def _write_artifacts(directory, count: int) -> None:
    for index in range(count):
        day = date(2026, 10, 1) + timedelta(days=index)
        (directory / f"{day.isoformat()}__topic-a.json").write_text(
            json.dumps(_artifact(day)), encoding="utf-8"
        )


def test_read_model_waits_before_first_observation(tmp_path):
    result = build_topic_strength_lifecycle_read("topic-a", tmp_path)
    assert result["ownerSeededV0"]["status"] == "WAITING_FOR_CANONICAL_ACTIVATION"
    assert result["ownerSeededV0"]["policyHash"] == POLICY_HASH
    assert result["forwardObservation"]["observationStartDate"] == OBSERVATION_START_PENDING
    assert result["forwardObservation"]["sessionCount"] == 0
    assert result["forwardObservation"]["checkpointStatus"]["OBSERVATION_20D"] == "NOT_STARTED"


@pytest.mark.parametrize(
    ("count", "status"),
    (
        (1, "IN_PROGRESS"),
        (19, "IN_PROGRESS"),
        (20, "READY_FOR_OWNER_REVIEW"),
        (40, "READY_FOR_OWNER_REVIEW"),
        (60, "READY_FOR_OWNER_REVIEW"),
    ),
)
def test_read_model_counts_unique_governed_dates_and_exposes_checkpoints(tmp_path, count, status):
    _write_artifacts(tmp_path, count)
    result = build_topic_strength_lifecycle_read("topic-a", tmp_path)
    progress = result["forwardObservation"]
    assert progress["sessionCount"] == count
    assert progress["checkpointStatus"]["OBSERVATION_20D"] == status
    assert result["ownerSeededV0"]["policyHash"] == POLICY_HASH
    assert result["ownerSeededV0"]["implementationSha"] == IMPLEMENTATION_SHA
    assert result["ownerSeededV0"]["absolute"]["grade"] == "S"
    assert result["ownerSeededV0"]["relative"]["grade"] == "B"
    assert "ABS_REL_GRADE_DIVERGENCE" in result["ownerSeededV0"]["observationFlags"]


def test_read_model_does_not_merge_other_policy_lineage(tmp_path):
    artifact = _artifact(date(2026, 10, 1))
    artifact["policy_hash"] = "wrong"
    (tmp_path / "2026-10-01__topic-a.json").write_text(json.dumps(artifact), encoding="utf-8")
    result = build_topic_strength_lifecycle_read("topic-a", tmp_path)
    assert result["forwardObservation"]["status"] == "UNAVAILABLE"
    assert "POLICY_HASH_MISMATCH" in result["forwardObservation"]["unavailableReason"]


def test_backend_api_contract_preserves_identity_and_progress_shape(tmp_path):
    _write_artifacts(tmp_path, 1)
    result = build_topic_strength_lifecycle_read("topic-a", tmp_path)
    owner = TopicOwnerSeededV0Read.model_validate(result["ownerSeededV0"])
    progress = TopicForwardObservationRead.model_validate(result["forwardObservation"])
    assert owner.policy_hash == POLICY_HASH
    assert owner.implementation_sha == IMPLEMENTATION_SHA
    assert progress.session_count == 1
    assert progress.checkpoint_status["OBSERVATION_20D"] == "IN_PROGRESS"


def test_policy_hash_is_consistent_across_code_policy_manifest_and_read_model(tmp_path):
    repository = Path(__file__).resolve().parents[3]
    policy_path = (
        repository / "config/topic_strength_policy/topic-strength-lifecycle.owner-seeded-v0.json"
    )
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    manifest_path = (
        repository
        / (
            "docs/reports/"
            "TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-"
            "FORWARD-OBSERVATION-ACTIVATION-003"
        )
        / "forward-observation-manifest.json"
    )
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    assert policy["policyHash"] == POLICY_HASH
    assert manifest["policy_hash"] == POLICY_HASH
    read_model = build_topic_strength_lifecycle_read("topic-a", tmp_path)
    assert read_model["ownerSeededV0"]["policyHash"] == POLICY_HASH
