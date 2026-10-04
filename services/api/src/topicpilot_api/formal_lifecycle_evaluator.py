"""Formal structural Lifecycle evaluator used by the post-close publisher.

The compatibility/shadow evaluator remains available for calibration tests.
This evaluator is selected only when formal Strength/derivative inputs are
bound to a formal Topic snapshot.  It uses target-state evidence, not a
mechanical adjacent-stage ladder or elapsed-stage duration.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from topicpilot_api.topic_lifecycle_v1 import (
    BASE,
    DECLINING,
    FERMENTING,
    MAIN_RISE,
    MATURE,
    SPROUTING,
    LifecycleEvidence,
    LifecycleInput,
    LifecycleResult,
)

FORMAL_STRUCTURAL_CALCULATION_VERSION = "topic-lifecycle-formal-structural.v1"


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and abs(result) != float("inf") else None


def _dimension_status(derivatives: Mapping[str, Any], name: str) -> str:
    return str(((derivatives.get("dimensions") or {}).get(name) or {}).get("status") or "UNKNOWN")


def _current_metrics(value: LifecycleInput) -> dict[str, Any]:
    derivatives = value.derivative_evidence or {}
    dimensions = derivatives.get("dimensions") or {}
    return {
        "absoluteStrength": value.absolute_strength,
        "relativeStrength": value.relative_strength,
        "absoluteGrade": value.absolute_grade,
        "relativeGrade": value.relative_grade,
        "coreParticipation": ((dimensions.get("coreParticipation") or {}).get("currentLevel")),
        "breadth": ((dimensions.get("breadth") or {}).get("currentLevel")),
        "relatedDiffusion": ((dimensions.get("relatedDiffusion") or {}).get("currentLevel")),
        "leadershipConcentration": (
            (dimensions.get("leadershipConcentration") or {}).get("currentLevel")
        ),
        "interpretation": derivatives.get("interpretation"),
    }


def _healthy(metrics: Mapping[str, Any]) -> bool:
    return bool(
        (_number(metrics.get("absoluteStrength")) or 0.0) >= 62.0
        and (
            (_number(metrics.get("relativeStrength")) or 0.0) >= 55.0
            or metrics.get("relativeGrade") in {"A", "S"}
        )
    )


def _structural_break(metrics: Mapping[str, Any], derivatives: Mapping[str, Any]) -> bool:
    weakening = int(derivatives.get("weakeningDimensions") or 0)
    return bool(
        derivatives.get("interpretation") == "DETERIORATING"
        and weakening >= 3
        and (
            metrics.get("absoluteGrade") == "D"
            or metrics.get("relativeGrade") == "D"
            or (_number(metrics.get("absoluteStrength")) or 100.0) < 45.0
        )
    )


def _recovered(metrics: Mapping[str, Any], derivatives: Mapping[str, Any]) -> bool:
    return bool(
        derivatives.get("interpretation") in {"EXPANDING", "STABLE"}
        and (_number(metrics.get("coreParticipation")) or 0.0) >= 0.45
        and (_number(metrics.get("breadth")) or 0.0) >= 0.45
        and metrics.get("absoluteGrade") in {"A", "S", "B"}
    )


def _target_stage(value: LifecycleInput) -> tuple[str | None, str]:
    metrics = _current_metrics(value)
    derivatives = value.derivative_evidence or {}
    context = value.market_context or {}
    interpretation = derivatives.get("interpretation")
    if value.previous_stage == DECLINING and _recovered(metrics, derivatives):
        return BASE, "DECLINE_RECOVERY_RESETS_TO_BASE"
    if _structural_break(metrics, derivatives):
        return DECLINING, "STRUCTURAL_BREAKDOWN_EVIDENCE"
    if value.previous_stage in {MAIN_RISE, FERMENTING, SPROUTING}:
        if (
            value.previous_stage == MAIN_RISE
            and interpretation == "SATURATING"
            and _healthy(metrics)
        ):
            return MATURE, "HEALTHY_LEVEL_WITH_STRUCTURAL_SATURATION"
        if interpretation == "EXPANDING" and len(value.formal_history) >= 2:
            return MAIN_RISE, "MULTI_OBSERVATION_STRUCTURAL_EXPANSION"
        if interpretation == "EXPANDING":
            return FERMENTING, "STRUCTURAL_DIFFUSION_EXPANDING"
        return None, "CURRENT_STATE_EVIDENCE_PERSISTS"
    if value.previous_stage == MATURE:
        if interpretation == "EXPANDING" and len(value.formal_history) >= 2:
            return MAIN_RISE, "RENEWED_MULTI_OBSERVATION_EXPANSION"
        if interpretation == "SATURATING" and _healthy(metrics):
            return MATURE, "MATURE_HEALTHY_SATURATION_PERSISTS"
    if (
        metrics.get("absoluteGrade") == "S"
        and metrics.get("relativeGrade") == "S"
        and interpretation in {"EXPANDING", "STABLE"}
    ):
        return SPROUTING, "STRONG_ABSOLUTE_RELATIVE_FORMATION"
    if interpretation == "EXPANDING":
        return SPROUTING, "FORMAL_FORMATION_CANDIDATE"
    if context.get("status") == "SYSTEMIC_SHOCK" and _structural_break(metrics, derivatives):
        return DECLINING, "SYSTEMIC_SHOCK_STRUCTURAL_BREAK_CANDIDATE"
    return None, "NO_TARGET_STATE_EVIDENCE"


def evaluate_formal_structural_lifecycle(value: LifecycleInput) -> LifecycleResult:
    """Evaluate one formal day with asymmetric candidate confirmation."""

    metrics = _current_metrics(value)
    derivatives = dict(value.derivative_evidence or {})
    if (
        metrics["absoluteStrength"] is None
        or metrics["relativeStrength"] is None
        or derivatives.get("status") != "AVAILABLE"
    ):
        empty = LifecycleEvidence(
            leadership={"status": "UNAVAILABLE"},
            diffusion={"status": "UNAVAILABLE"},
            group_strength={"status": "UNAVAILABLE"},
            divergence_decay={"status": "UNAVAILABLE"},
            persistence={"status": "UNAVAILABLE"},
            sample_confidence={"status": "UNAVAILABLE"},
        )
        return LifecycleResult(
            value.topic_id,
            value.trading_date,
            value.previous_stage,
            None,
            None,
            None,
            None,
            "UNAVAILABLE",
            "UNAVAILABLE",
            "HOLD_FORMAL_GATE",
            "FORMAL_STRENGTH_OR_RELATIVE_OR_DERIVATIVES_UNAVAILABLE",
            empty,
            {"candidateStreak": 0, "transitionConfirmed": False},
            "topic-lifecycle-formal-policy.v1",
            FORMAL_STRUCTURAL_CALCULATION_VERSION,
            "FORMAL",
        )

    previous = value.previous_stage or BASE
    target, target_reason = _target_stage(value)
    prior_candidate = value.previous_candidate_stage
    streak = (
        value.previous_candidate_streak + 1
        if target and target == prior_candidate
        else 1
        if target
        else 0
    )
    context_status = str((value.market_context or {}).get("status") or "NORMAL")
    required = 1
    if target == DECLINING:
        required = 3 if context_status == "SYSTEMIC_SHOCK" else 2
        if prior_candidate == DECLINING and not _recovered(metrics, derivatives):
            required = 1
    elif (
        target == SPROUTING
        and metrics.get("absoluteGrade") == "S"
        and metrics.get("relativeGrade") == "S"
    ):
        required = 1
    elif target in {FERMENTING, MAIN_RISE, MATURE}:
        required = 2
    confirmed = target is not None and streak >= required
    final = previous
    transition_reason = target_reason
    stage_entered = value.previous_stage_entered_at
    stage_days = (value.previous_stage_trading_days or 0) + 1 if value.previous_stage else 1
    if confirmed and target != previous:
        final = target
        stage_entered = value.trading_date
        stage_days = 1
        transition_reason = f"CONFIRMED_{target}_{target_reason}"
    elif target is None:
        transition_reason = "CANDIDATE_CLEARED_OR_STATE_PERSISTS"

    history = [dict(item) for item in value.formal_history[-4:]]
    history.append(
        {
            "asOfDate": value.trading_date.isoformat(),
            **metrics,
            "interpretation": derivatives.get("interpretation"),
        }
    )
    gap_dates = list((value.state_memory or {}).get("observationGapDates") or [])
    evidence = LifecycleEvidence(
        leadership={
            "status": "AVAILABLE",
            "concentration": metrics.get("leadershipConcentration"),
            "dimension": _dimension_status(derivatives, "leadershipConcentration"),
        },
        diffusion={
            "status": "AVAILABLE",
            "breadth": metrics.get("breadth"),
            "coreParticipation": metrics.get("coreParticipation"),
            "relatedDiffusion": metrics.get("relatedDiffusion"),
            "dimensions": {
                key: _dimension_status(derivatives, key)
                for key in ("coreParticipation", "breadth", "relatedDiffusion")
            },
        },
        group_strength={
            "absoluteStrength": metrics.get("absoluteStrength"),
            "relativeStrength": metrics.get("relativeStrength"),
            "absoluteGrade": metrics.get("absoluteGrade"),
            "relativeGrade": metrics.get("relativeGrade"),
        },
        divergence_decay={
            "marketContext": context_status,
            "relativeStatus": _dimension_status(derivatives, "relativeStrength"),
        },
        persistence={
            "formalHistoryObservations": len(history),
            "requiredConfirmationObservations": required,
            "observationGapDates": gap_dates,
            "interpretation": derivatives.get("interpretation"),
        },
        sample_confidence={
            "status": "COMPLETE",
            "topicSizeIsNotConfidencePenalty": True,
            "observedMemberCount": len(value.observations),
            "expectedMemberCount": value.expected_member_count,
        },
    )
    memory = {
        **dict(value.state_memory or {}),
        "formal": True,
        "derivativeHistory": history[-5:],
        "marketContext": dict(value.market_context or {}),
        "observationGapDates": gap_dates,
        "candidateStreak": streak if target else 0,
        "candidateStage": target,
    }
    return LifecycleResult(
        value.topic_id,
        value.trading_date,
        previous,
        target,
        final,
        stage_entered,
        stage_days,
        "SUCCESS",
        "FORMAL",
        "CONFIRMED_TRANSITION"
        if confirmed and target != previous
        else "HOLD_CANDIDATE"
        if target
        else "HOLD_CURRENT_STATE",
        transition_reason,
        evidence,
        {
            "candidateStreak": streak,
            "required": required,
            "transitionConfirmed": bool(confirmed and target != previous),
            "marketContext": context_status,
        },
        "topic-lifecycle-formal-policy.v1",
        FORMAL_STRUCTURAL_CALCULATION_VERSION,
        "FORMAL",
        average_change=None,
        coverage_pct=100.0,
        state_memory=memory,
    )


__all__ = ["FORMAL_STRUCTURAL_CALCULATION_VERSION", "evaluate_formal_structural_lifecycle"]
