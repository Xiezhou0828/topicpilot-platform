"""Backend read model for Owner-seeded V0 strength and forward observation."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from topicpilot_api.topic_engine.forward_observation_activation import (
    ACTIVATION_TASK_ID,
    POLICY_HASH,
    POLICY_ID,
    POLICY_VERSION,
    checkpoint_statuses,
    next_checkpoint,
)

OBSERVATION_START_PENDING = "PENDING_CANONICAL_ACTIVATION"
OBSERVATION_STATUS_WAITING = "WAITING_FOR_CANONICAL_ACTIVATION"
OBSERVATION_STATUS_AVAILABLE = "AVAILABLE"
OBSERVATION_STATUS_UNAVAILABLE = "UNAVAILABLE"


class ForwardObservationReadError(ValueError):
    """Raised when an observation artifact cannot be trusted by the read model."""


def _empty_progress() -> dict[str, Any]:
    return {
        "status": OBSERVATION_STATUS_WAITING,
        "observationStartDate": OBSERVATION_START_PENDING,
        "sessionCount": 0,
        "nextCheckpoint": 20,
        "checkpointStatus": checkpoint_statuses(0),
        "latestAsOfDate": None,
        "implementationShas": [],
        "diagnosticOnly": True,
    }


def _required_text(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ForwardObservationReadError(f"MISSING_OR_INVALID:{key}")
    return value


def _read_artifact(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ForwardObservationReadError(f"INVALID_ARTIFACT:{path.name}") from exc
    if not isinstance(payload, dict) or "as_of_date" not in payload:
        raise ForwardObservationReadError(f"INVALID_ARTIFACT:{path.name}")
    if _required_text(payload, "activation_task_id") != ACTIVATION_TASK_ID:
        raise ForwardObservationReadError(f"ACTIVATION_TASK_ID_MISMATCH:{path.name}")
    if _required_text(payload, "policy_id") != POLICY_ID:
        raise ForwardObservationReadError(f"POLICY_ID_MISMATCH:{path.name}")
    if _required_text(payload, "policy_version") != POLICY_VERSION:
        raise ForwardObservationReadError(f"POLICY_VERSION_MISMATCH:{path.name}")
    if _required_text(payload, "policy_hash") != POLICY_HASH:
        raise ForwardObservationReadError(f"POLICY_HASH_MISMATCH:{path.name}")
    _required_text(payload, "implementation_sha")
    _required_text(payload, "topic_id")
    as_of = _required_text(payload, "as_of_date")
    start = _required_text(payload, "observation_start_date")
    try:
        date.fromisoformat(as_of)
        date.fromisoformat(start)
    except ValueError as exc:
        raise ForwardObservationReadError(f"INVALID_ARTIFACT_DATE:{path.name}") from exc
    if payload.get("owner_review_status") != "OWNER_REVIEW_ACCEPTED_WITH_OBSERVATION_FLAGS":
        raise ForwardObservationReadError(f"OWNER_REVIEW_NOT_ACCEPTED:{path.name}")
    if payload.get("formal_output_boundary", {}).get("diagnostic_only") is not True:
        raise ForwardObservationReadError(f"FORMAL_BOUNDARY_INVALID:{path.name}")
    if not isinstance(payload.get("observation_flags"), list):
        raise ForwardObservationReadError(f"OBSERVATION_FLAGS_INVALID:{path.name}")
    return payload


def _artifact_paths(observation_dir: str | Path | None) -> list[Path]:
    if observation_dir is None:
        return []
    directory = Path(observation_dir)
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise ForwardObservationReadError("OBSERVATION_STORE_NOT_DIRECTORY")
    return sorted(directory.glob("*.json"))


def _read_valid_artifacts(
    observation_dir: str | Path | None,
) -> tuple[list[dict[str, Any]], str | None]:
    artifacts: list[dict[str, Any]] = []
    for path in _artifact_paths(observation_dir):
        try:
            artifact = _read_artifact(path)
        except ForwardObservationReadError as exc:
            # Manifests and unrelated JSON files are not daily artifacts.  A
            # file that looks like one but is invalid makes the diagnostic
            # read unavailable rather than silently producing a partial view.
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return [], str(exc)
            if isinstance(raw, dict) and "as_of_date" in raw:
                return [], str(exc)
            continue
        artifacts.append(artifact)
    return artifacts, None


def _latest_for_topic(artifacts: list[dict[str, Any]], topic_id: str) -> dict[str, Any] | None:
    candidates = [item for item in artifacts if item.get("topic_id") == topic_id]
    return max(candidates, key=lambda item: item["as_of_date"]) if candidates else None


def _progress(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    if not artifacts:
        return _empty_progress()
    session_dates = sorted({item["as_of_date"] for item in artifacts})
    implementation_shas = sorted({item["implementation_sha"] for item in artifacts})
    start_dates = sorted({item["observation_start_date"] for item in artifacts})
    count = len(session_dates)
    status = checkpoint_statuses(count)
    return {
        "status": OBSERVATION_STATUS_AVAILABLE,
        "observationStartDate": start_dates[0] if len(start_dates) == 1 else "MIXED_START_DATES",
        "sessionCount": count,
        "nextCheckpoint": next_checkpoint(count),
        "checkpointStatus": status,
        "latestAsOfDate": session_dates[-1],
        "implementationShas": implementation_shas,
        "diagnosticOnly": True,
    }


def _strength_view(artifact: dict[str, Any]) -> dict[str, Any]:
    scores = artifact["scores"]
    lifecycle = artifact["lifecycle"]
    return {
        "status": OBSERVATION_STATUS_AVAILABLE,
        "policyId": artifact["policy_id"],
        "policyVersion": artifact["policy_version"],
        "policyHash": artifact["policy_hash"],
        "implementationSha": artifact["implementation_sha"],
        "asOfDate": artifact["as_of_date"],
        "formalDailyGrade": scores["final_daily_grade"],
        "absolute": {
            "score": scores["absolute_total"],
            "grade": scores["absolute_grade"],
        },
        "relative": {
            "score": scores["relative_total"],
            "grade": scores["relative_grade"],
        },
        "lifecycle": {
            "before": lifecycle["lifecycle_before"],
            "candidate": lifecycle["lifecycle_candidate"],
            "after": lifecycle["lifecycle_after"],
            "transitionConfirmed": lifecycle["transition_confirmed"],
            "transitionReason": lifecycle["transition_reason"],
        },
        "observationFlags": artifact["observation_flags"],
        "observationFlagCopy": artifact.get("observation_flag_copy", {}),
        "qualityFlags": artifact["quality_flags"],
        "diagnosticOnly": True,
    }


def build_topic_strength_lifecycle_read(
    topic_id: str,
    observation_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Build a fail-closed additive read model from authorized artifacts."""

    artifacts, error = _read_valid_artifacts(observation_dir)
    if error:
        return {
            "ownerSeededV0": {
                "status": OBSERVATION_STATUS_UNAVAILABLE,
                "policyId": POLICY_ID,
                "policyVersion": POLICY_VERSION,
                "policyHash": POLICY_HASH,
                "implementationSha": None,
                "asOfDate": None,
                "formalDailyGrade": None,
                "absolute": {"score": None, "grade": None},
                "relative": {"score": None, "grade": None},
                "lifecycle": {
                    "before": None,
                    "candidate": None,
                    "after": None,
                    "transitionConfirmed": None,
                    "transitionReason": None,
                },
                "observationFlags": [],
                "observationFlagCopy": {},
                "qualityFlags": {"FAIL_CLOSED_REASON": error},
                "diagnosticOnly": True,
            },
            "forwardObservation": {
                **_empty_progress(),
                "status": OBSERVATION_STATUS_UNAVAILABLE,
                "unavailableReason": error,
            },
        }
    progress = _progress(artifacts)
    latest = _latest_for_topic(artifacts, topic_id)
    if latest is None:
        strength = {
            "status": OBSERVATION_STATUS_WAITING,
            "policyId": POLICY_ID,
            "policyVersion": POLICY_VERSION,
            "policyHash": POLICY_HASH,
            "implementationSha": None,
            "asOfDate": None,
            "formalDailyGrade": None,
            "absolute": {"score": None, "grade": None},
            "relative": {"score": None, "grade": None},
            "lifecycle": {
                "before": None,
                "candidate": None,
                "after": None,
                "transitionConfirmed": None,
                "transitionReason": None,
            },
            "observationFlags": [],
            "observationFlagCopy": {},
            "qualityFlags": {"FAIL_CLOSED_REASON": "NO_FORMAL_OBSERVATION_YET"},
            "diagnosticOnly": True,
        }
    else:
        strength = _strength_view(latest)
    return {"ownerSeededV0": strength, "forwardObservation": progress}


__all__ = [
    "OBSERVATION_START_PENDING",
    "ForwardObservationReadError",
    "build_topic_strength_lifecycle_read",
]
