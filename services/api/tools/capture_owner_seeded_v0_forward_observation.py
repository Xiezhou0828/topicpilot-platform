"""Capture one read-only Owner-seeded V0 forward-observation artifact.

The command consumes a date-bound, already-authorized snapshot supplied by a
caller.  It never reads or writes the formal business database and never
changes the canonical policy output.  The same date/topic path is idempotent:
an identical artifact is a NOOP and a different artifact is rejected.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from topicpilot_api.topic_engine.owner_seeded_v0_policy import (
    CORE,
    DEFAULT_POLICY,
    LIFECYCLE_STAGES,
    POLICY_ID,
    POLICY_VERSION,
    RELATED,
    REPRESENTATIVE,
    LifecycleDayInput,
    LifecycleHistoryEntry,
    LifecycleMetrics,
    LifecycleState,
    MemberObservation,
    advance_lifecycle,
    evaluate_topic,
)

TASK_ID = "TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-REVIEW-AND-FORWARD-OBSERVATION-002"
OBSERVATION_SCHEMA_VERSION = "topic-strength-lifecycle.owner-seeded-v0.forward-observation.v1"
POLICY_HASH = DEFAULT_POLICY.policy_hash()


class ForwardObservationCaptureError(ValueError):
    """Raised when a capture input cannot be accepted fail-closed."""


def _required(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping or mapping[key] is None:
        raise ForwardObservationCaptureError(f"MISSING_REQUIRED_FIELD:{key}")
    return mapping[key]


def _text(mapping: dict[str, Any], key: str) -> str:
    value = _required(mapping, key)
    if not isinstance(value, str) or not value.strip():
        raise ForwardObservationCaptureError(f"INVALID_TEXT_FIELD:{key}")
    return value.strip()


def _parse_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str):
        raise ForwardObservationCaptureError(f"INVALID_DATE_FIELD:{field_name}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ForwardObservationCaptureError(f"INVALID_DATE_FIELD:{field_name}") from exc


def _number_or_none(value: Any, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ForwardObservationCaptureError(f"INVALID_NUMBER_FIELD:{field_name}")
    return float(value)


def _member_observations(payload: Any) -> tuple[MemberObservation, ...]:
    if not isinstance(payload, list) or not payload:
        raise ForwardObservationCaptureError("MISSING_FORMAL_MEMBER_SNAPSHOT")
    observations: list[MemberObservation] = []
    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            raise ForwardObservationCaptureError(f"INVALID_MEMBER_ROW:{index}")
        market = row.get("market")
        if market is not None and not isinstance(market, str):
            raise ForwardObservationCaptureError(f"INVALID_MEMBER_ROW:{index}")
        try:
            observations.append(
                MemberObservation(
                    member_id=_text(row, "member_id"),
                    role=_text(row, "role"),
                    absolute_return_pct=_number_or_none(
                        _required(row, "absolute_return_pct"),
                        f"members[{index}].absolute_return_pct",
                    ),
                    score_importance=_number_or_none(
                        row.get("score_importance"), f"members[{index}].score_importance"
                    ),
                    market=market,
                    benchmark_return_pct=_number_or_none(
                        row.get("benchmark_return_pct"),
                        f"members[{index}].benchmark_return_pct",
                    ),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, ForwardObservationCaptureError):
                raise
            raise ForwardObservationCaptureError(f"INVALID_MEMBER_ROW:{index}") from exc
    return tuple(observations)


def _history_metrics(payload: Any, field_name: str) -> LifecycleMetrics:
    if not isinstance(payload, dict):
        raise ForwardObservationCaptureError(f"INVALID_HISTORY_METRICS:{field_name}")
    metric_names = (
        "rep_raw_return",
        "core_median_return",
        "core_positive_breadth",
        "core_strong_breadth",
        "core_weak_ratio",
        "related_positive_breadth",
        "related_positive_median",
    )
    if any(name not in payload for name in metric_names):
        raise ForwardObservationCaptureError(f"MISSING_HISTORY_METRICS:{field_name}")
    return LifecycleMetrics(
        rep_raw_return=_number_or_none(
            payload.get("rep_raw_return"), f"{field_name}.rep_raw_return"
        ),
        core_median_return=_number_or_none(
            payload.get("core_median_return"), f"{field_name}.core_median_return"
        ),
        core_positive_breadth=_number_or_none(
            payload.get("core_positive_breadth"), f"{field_name}.core_positive_breadth"
        ),
        core_strong_breadth=_number_or_none(
            payload.get("core_strong_breadth"), f"{field_name}.core_strong_breadth"
        ),
        core_weak_ratio=_number_or_none(
            payload.get("core_weak_ratio"), f"{field_name}.core_weak_ratio"
        ),
        related_positive_breadth=_number_or_none(
            payload.get("related_positive_breadth"), f"{field_name}.related_positive_breadth"
        ),
        related_positive_median=_number_or_none(
            payload.get("related_positive_median"), f"{field_name}.related_positive_median"
        ),
    )


def _lifecycle_state(payload: Any, as_of_date: date) -> LifecycleState:
    if not isinstance(payload, dict):
        raise ForwardObservationCaptureError("MISSING_LIFECYCLE_STATE")
    stage = _text(payload, "stage")
    if stage not in LIFECYCLE_STAGES:
        raise ForwardObservationCaptureError("INVALID_LIFECYCLE_STAGE")
    main_rise = payload.get("main_rise_occurred_in_cycle")
    if not isinstance(main_rise, bool):
        raise ForwardObservationCaptureError("INVALID_MAIN_RISE_CYCLE_FLAG")
    candidate = payload.get("candidate_stage")
    if candidate is not None and candidate not in LIFECYCLE_STAGES:
        raise ForwardObservationCaptureError("INVALID_CANDIDATE_LIFECYCLE_STAGE")
    candidate_streak = payload.get("candidate_streak", 0)
    if (
        isinstance(candidate_streak, bool)
        or not isinstance(candidate_streak, int)
        or candidate_streak < 0
    ):
        raise ForwardObservationCaptureError("INVALID_CANDIDATE_STREAK")

    history_payload = payload.get("history", [])
    if not isinstance(history_payload, list):
        raise ForwardObservationCaptureError("INVALID_LIFECYCLE_HISTORY")
    history: list[LifecycleHistoryEntry] = []
    previous_date: date | None = None
    for index, row in enumerate(history_payload):
        if not isinstance(row, dict):
            raise ForwardObservationCaptureError(f"INVALID_HISTORY_ROW:{index}")
        history_date = _parse_date(_required(row, "trading_date"), f"history[{index}].trading_date")
        if history_date >= as_of_date or (
            previous_date is not None and history_date <= previous_date
        ):
            raise ForwardObservationCaptureError("HISTORY_NOT_STRICTLY_PRIOR_AND_ORDERED")
        previous_date = history_date
        flags = (
            "fermenting_candidate",
            "main_rise_candidate",
            "meaningful_expansion",
            "mature_candidate",
            "declining_candidate",
        )
        if any(not isinstance(row.get(flag), bool) for flag in flags):
            raise ForwardObservationCaptureError(f"INVALID_HISTORY_FLAGS:{index}")
        history.append(
            LifecycleHistoryEntry(
                trading_date=history_date,
                metrics=_history_metrics(row.get("metrics"), f"history[{index}].metrics"),
                **{flag: row[flag] for flag in flags},
            )
        )
    return LifecycleState(
        stage=stage,
        main_rise_occurred_in_cycle=main_rise,
        candidate_stage=candidate,
        candidate_streak=candidate_streak,
        history=tuple(history),
    )


def _evidence_by_role(evaluation: Any, view: str) -> dict[str, dict[str, Any]]:
    result = evaluation.absolute if view == "ABSOLUTE" else evaluation.relative
    return {item.role: item.as_dict() for item in result.role_evidence}


def _score_inputs(members: tuple[MemberObservation, ...]) -> dict[str, list[dict[str, Any]]]:
    absolute: list[dict[str, Any]] = []
    relative: list[dict[str, Any]] = []
    for member in members:
        absolute.append(
            {
                "member_id": member.member_id,
                "role": member.role,
                "return_pct": member.absolute_return_pct,
            }
        )
        relative.append(
            {
                "member_id": member.member_id,
                "role": member.role,
                "excess_return_pct": member.value_for("RELATIVE"),
            }
        )
    return {"absolute": absolute, "relative": relative}


def _lifecycle_state_dict(state: LifecycleState) -> dict[str, Any]:
    return {
        "stage": state.stage,
        "main_rise_occurred_in_cycle": state.main_rise_occurred_in_cycle,
        "candidate_stage": state.candidate_stage,
        "candidate_streak": state.candidate_streak,
        "history": [
            {
                "trading_date": entry.trading_date.isoformat(),
                "metrics": entry.metrics.as_dict(),
                "fermenting_candidate": entry.fermenting_candidate,
                "main_rise_candidate": entry.main_rise_candidate,
                "meaningful_expansion": entry.meaningful_expansion,
                "mature_candidate": entry.mature_candidate,
                "declining_candidate": entry.declining_candidate,
            }
            for entry in state.history
        ],
    }


def _capture_payload(payload: dict[str, Any]) -> dict[str, Any]:
    as_of_date = _parse_date(_required(payload, "as_of_date"), "as_of_date")
    observation_start_date = _parse_date(
        _required(payload, "observation_start_date"), "observation_start_date"
    )
    if as_of_date < observation_start_date:
        raise ForwardObservationCaptureError("AS_OF_DATE_BEFORE_OBSERVATION_START")
    if _text(payload, "policy_id") != POLICY_ID:
        raise ForwardObservationCaptureError("POLICY_ID_MISMATCH")
    if _text(payload, "policy_version") != POLICY_VERSION:
        raise ForwardObservationCaptureError("POLICY_VERSION_MISMATCH")
    if _text(payload, "policy_hash") != POLICY_HASH:
        raise ForwardObservationCaptureError("POLICY_HASH_MISMATCH")

    session = payload.get("session")
    if not isinstance(session, dict) or session.get("is_governed_trading_session") is not True:
        raise ForwardObservationCaptureError("NOT_A_GOVERNED_TRADING_SESSION")
    session_authority_version = _text(session, "authority_version")
    topic_id = _text(payload, "topic_id")
    topic_name = _text(payload, "topic_name")
    formal_member_authority_version = _text(payload, "formal_member_authority_version")
    structural_role_authority_version = _text(payload, "structural_role_authority_version")
    benchmark_authority = payload.get("benchmark_authority")
    if not isinstance(benchmark_authority, dict):
        raise ForwardObservationCaptureError("MISSING_BENCHMARK_AUTHORITY")
    benchmark_source = _text(benchmark_authority, "source")
    benchmark_version = _text(benchmark_authority, "version")

    members = _member_observations(_required(payload, "members"))
    if any(item.absolute_return_pct is None for item in members):
        raise ForwardObservationCaptureError("PRICE_DATA_INCOMPLETE")
    if any(item.market is None or item.benchmark_return_pct is None for item in members):
        raise ForwardObservationCaptureError("BENCHMARK_DATA_INCOMPLETE")
    state = _lifecycle_state(payload.get("lifecycle_state"), as_of_date)

    evaluation = evaluate_topic(topic_id, as_of_date, members)
    next_state, lifecycle = advance_lifecycle(state, LifecycleDayInput(evaluation, members))
    absolute = _evidence_by_role(evaluation, "ABSOLUTE")
    relative = _evidence_by_role(evaluation, "RELATIVE")
    absolute_result = evaluation.absolute
    relative_result = evaluation.relative
    role_counts = {
        role: sum(member.role == role for member in members)
        for role in (REPRESENTATIVE, CORE, RELATED)
    }
    quality_flags = {
        "FORMAL_MEMBER_COVERAGE_OK": (
            evaluation.observed_member_count == evaluation.formal_member_count
        ),
        "STRUCTURAL_ROLE_AUTHORITY_OK": True,
        "BENCHMARK_READY": True,
        "PRICE_DATA_COMPLETE": True,
        "RELATIVE_SCORE_AVAILABLE": relative_result.status == "EVALUATED",
        "SMALL_SAMPLE_X": absolute_result.grade == "X",
        "FAIL_CLOSED_REASON": None,
    }
    return {
        "observation_schema_version": OBSERVATION_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "as_of_date": as_of_date.isoformat(),
        "observation_start_date": observation_start_date.isoformat(),
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "policy_hash": POLICY_HASH,
        "topic_id": topic_id,
        "topic_name": topic_name,
        "authority": {
            "formal_member_authority_version": formal_member_authority_version,
            "structural_role_authority_version": structural_role_authority_version,
            "benchmark_authority": {
                "source": benchmark_source,
                "version": benchmark_version,
            },
            "trading_session_authority_version": session_authority_version,
        },
        "formal_member_count": len(members),
        "representative_count": role_counts[REPRESENTATIVE],
        "core_count": role_counts[CORE],
        "related_count": role_counts[RELATED],
        "absolute_score_inputs": _score_inputs(members)["absolute"],
        "relative_score_inputs": _score_inputs(members)["relative"],
        "absolute_metrics": {
            "rep_weighted_raw": absolute[REPRESENTATIVE]["weighted_raw_return"],
            "core_median_return": absolute[CORE]["median_return"],
            "core_positive_breadth": absolute[CORE]["positive_breadth"],
            "core_strong_breadth": absolute[CORE]["strong_breadth"],
            "core_weak_ratio": absolute[CORE]["weak_ratio"],
            "related_positive_breadth": absolute[RELATED]["positive_breadth"],
            "related_median_return": absolute[RELATED]["positive_median_return"],
        },
        "relative_metrics": {
            "rep_weighted_raw": relative[REPRESENTATIVE]["weighted_raw_return"],
            "core_median_return": relative[CORE]["median_return"],
            "core_positive_breadth": relative[CORE]["positive_breadth"],
            "core_strong_breadth": relative[CORE]["strong_breadth"],
            "core_weak_ratio": relative[CORE]["weak_ratio"],
            "related_positive_breadth": relative[RELATED]["positive_breadth"],
            "related_median_return": relative[RELATED]["positive_median_return"],
        },
        "contributions": {
            "representative": {
                "absolute": absolute[REPRESENTATIVE]["contribution"],
                "relative": relative[REPRESENTATIVE]["contribution"],
            },
            "core": {
                "absolute": absolute[CORE]["contribution"],
                "relative": relative[CORE]["contribution"],
            },
            "related": {
                "absolute": absolute[RELATED]["contribution"],
                "relative": relative[RELATED]["contribution"],
            },
        },
        "scores": {
            "absolute_total": absolute_result.strength,
            "relative_total": relative_result.strength,
            "absolute_grade": absolute_result.grade,
            "relative_grade": relative_result.grade,
            "final_daily_grade": absolute_result.grade,
            "absolute_d_guard": absolute_result.d_guard,
            "relative_d_guard": relative_result.d_guard,
        },
        "lifecycle": {
            "lifecycle_before": lifecycle.previous_stage,
            "lifecycle_candidate": lifecycle.candidate_stage,
            "lifecycle_after": lifecycle.final_stage,
            "transition_confirmed": lifecycle.final_stage != lifecycle.previous_stage,
            "transition_reason": lifecycle.transition_reason,
            "meaningful_expansion_flag": lifecycle.meaningful_expansion,
            "renewed_expansion_flag": lifecycle.renewed_expansion,
            "relative_deterioration_confirmation": lifecycle.relative_deterioration_confirmation,
            "early_relative_strength_confirmation": lifecycle.early_relative_strength_confirmation,
        },
        "quality_flags": quality_flags,
        "formal_output_boundary": {
            "formal_output_overridden": False,
            "historical_output_mutated": False,
            "production_active": False,
            "diagnostic_only": True,
        },
        "next_lifecycle_state": _lifecycle_state_dict(next_state),
    }


def capture_observation(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and deterministically build one observation artifact."""

    if not isinstance(payload, dict):
        raise ForwardObservationCaptureError("INPUT_MUST_BE_OBJECT")
    return _capture_payload(payload)


def _artifact_name(observation: dict[str, Any]) -> str:
    topic = re.sub(r"[^A-Za-z0-9._-]+", "-", observation["topic_id"]).strip("-") or "topic"
    return f"{observation['as_of_date']}__{topic}.json"


def _read_input(path: str) -> dict[str, Any]:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ForwardObservationCaptureError("INPUT_JSON_INVALID") from exc
    if not isinstance(parsed, dict):
        raise ForwardObservationCaptureError("INPUT_MUST_BE_OBJECT")
    return parsed


def _write_idempotent(output_dir: Path, observation: dict[str, Any]) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / _artifact_name(observation)
    if destination.exists():
        try:
            existing = json.loads(destination.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ForwardObservationCaptureError("EXISTING_ARTIFACT_INVALID") from exc
        if existing != observation:
            raise ForwardObservationCaptureError("EXISTING_ARTIFACT_CONFLICT")
        return "NOOP_IDENTICAL_ARTIFACT"
    destination.write_text(
        json.dumps(observation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return "CREATED"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON snapshot path, or '-' for stdin")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional artifact directory; omit for a no-write dry run to stdout",
    )
    args = parser.parse_args()
    try:
        observation = capture_observation(_read_input(args.input))
        status = "DRY_RUN"
        artifact_path: str | None = None
        if args.output_dir is not None:
            status = _write_idempotent(args.output_dir, observation)
            artifact_path = str(args.output_dir / _artifact_name(observation))
        print(
            json.dumps(
                {"status": status, "artifact_path": artifact_path, "observation": observation}
                if args.output_dir is None
                else {"status": status, "artifact_path": artifact_path},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except (ForwardObservationCaptureError, OSError) as exc:
        print(f"FAIL_CLOSED:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
