"""Governance and diagnostic helpers for Owner-seeded V0 observation."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .owner_seeded_v0_policy import DEFAULT_POLICY, POLICY_ID, POLICY_VERSION

ACTIVATION_TASK_ID = (
    "TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-FORWARD-OBSERVATION-ACTIVATION-003"
)
OWNER_REVIEW_ACCEPTED = "OWNER_REVIEW_ACCEPTED_WITH_OBSERVATION_FLAGS"
OWNER_REVIEW_REQUIRED = "OWNER_REVIEW_REQUIRED"
POLICY_HASH = DEFAULT_POLICY.policy_hash()
IMPLEMENTATION_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

ACCEPTED_OBSERVATION_FLAGS = (
    "STRONG_GRADE_WITH_HELD_LIFECYCLE_CANDIDATE",
    "GRADE_D_WHILE_DECLINING_PENDING",
    "ABS_REL_GRADE_DIVERGENCE",
    "MATURE_OR_MAIN_RISE_WITH_GRADE_B",
)

OBSERVATION_FLAG_COPY = {
    "STRONG_GRADE_WITH_HELD_LIFECYCLE_CANDIDATE": (
        "當日強度已達較高等級, 但生命週期仍等待跨期確認。"
    ),
    "GRADE_D_WHILE_DECLINING_PENDING": "今日強度已進入 D, 但 DECLINING 仍需連續條件確認。",
    "ABS_REL_GRADE_DIVERGENCE": "絕對與相對強度方向不同, 兩者將獨立保留觀察。",
    "MATURE_OR_MAIN_RISE_WITH_GRADE_B": (
        "生命週期反映跨期結構, 當日 Grade B 不會自動重置生命週期。"
    ),
}

CHECKPOINTS = (20, 40, 60)
CHECKPOINT_NOT_STARTED = "NOT_STARTED"
CHECKPOINT_IN_PROGRESS = "IN_PROGRESS"
CHECKPOINT_READY = "READY_FOR_OWNER_REVIEW"
CHECKPOINT_REVIEWED = "REVIEWED"


class ForwardObservationActivationError(ValueError):
    """Raised when the Owner-approved activation boundary is not satisfied."""


def assert_owner_review_accepted(status: str) -> None:
    if status != OWNER_REVIEW_ACCEPTED:
        raise ForwardObservationActivationError(
            f"OWNER_REVIEW_NOT_ACCEPTED:{status or OWNER_REVIEW_REQUIRED}"
        )


def validate_implementation_sha(value: Any) -> str:
    if not isinstance(value, str) or not IMPLEMENTATION_SHA_PATTERN.fullmatch(value):
        raise ForwardObservationActivationError("INVALID_IMPLEMENTATION_SHA")
    return value


def _grade_rank(value: str | None) -> int | None:
    return {"D": 0, "B": 1, "A": 2, "S": 3}.get(value)


def derive_observation_flags(
    *,
    absolute_grade: str | None,
    relative_grade: str | None,
    formal_daily_grade: str | None,
    lifecycle_before: str,
    lifecycle_candidate: str | None,
    lifecycle_after: str,
) -> list[str]:
    """Derive accepted diagnostic flags without changing formal outputs."""

    flags: list[str] = []
    if (
        lifecycle_candidate in {"FERMENTING", "MAIN_RISE"}
        and lifecycle_candidate != lifecycle_after
        and (
            absolute_grade in {"A", "S"}
            or relative_grade in {"A", "S"}
        )
    ):
        flags.append("STRONG_GRADE_WITH_HELD_LIFECYCLE_CANDIDATE")
    if (
        formal_daily_grade == "D"
        and lifecycle_candidate == "DECLINING"
        and lifecycle_after != "DECLINING"
    ):
        flags.append("GRADE_D_WHILE_DECLINING_PENDING")
    absolute_rank = _grade_rank(absolute_grade)
    relative_rank = _grade_rank(relative_grade)
    if (
        absolute_rank is not None
        and relative_rank is not None
        and abs(absolute_rank - relative_rank) >= 2
    ):
        flags.append("ABS_REL_GRADE_DIVERGENCE")
    if lifecycle_after in {"MATURE", "MAIN_RISE"} and formal_daily_grade == "B":
        flags.append("MATURE_OR_MAIN_RISE_WITH_GRADE_B")
    return [flag for flag in ACCEPTED_OBSERVATION_FLAGS if flag in flags]


def checkpoint_statuses(
    session_count: int,
    *,
    reviewed: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return checkpoint state; reaching a checkpoint never auto-marks review."""

    if session_count < 0:
        raise ValueError("session_count must be non-negative")
    reviewed = reviewed or {}
    result: dict[str, str] = {}
    for checkpoint in CHECKPOINTS:
        key = f"OBSERVATION_{checkpoint}D"
        if reviewed.get(key) == CHECKPOINT_REVIEWED:
            result[key] = CHECKPOINT_REVIEWED
        elif session_count == 0:
            result[key] = CHECKPOINT_NOT_STARTED
        elif session_count >= checkpoint:
            result[key] = CHECKPOINT_READY
        else:
            result[key] = CHECKPOINT_IN_PROGRESS
    return result


def next_checkpoint(session_count: int) -> int | None:
    return next((checkpoint for checkpoint in CHECKPOINTS if session_count < checkpoint), None)


__all__ = [
    "ACCEPTED_OBSERVATION_FLAGS",
    "ACTIVATION_TASK_ID",
    "CHECKPOINTS",
    "CHECKPOINT_IN_PROGRESS",
    "CHECKPOINT_NOT_STARTED",
    "CHECKPOINT_READY",
    "CHECKPOINT_REVIEWED",
    "IMPLEMENTATION_SHA_PATTERN",
    "OBSERVATION_FLAG_COPY",
    "OWNER_REVIEW_ACCEPTED",
    "OWNER_REVIEW_REQUIRED",
    "POLICY_HASH",
    "POLICY_ID",
    "POLICY_VERSION",
    "ForwardObservationActivationError",
    "assert_owner_review_accepted",
    "checkpoint_statuses",
    "derive_observation_flags",
    "next_checkpoint",
    "validate_implementation_sha",
]
