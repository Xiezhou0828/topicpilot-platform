"""Frozen Lifecycle V1.3 evaluator boundary for formal publication.

The existing ``topic_lifecycle_v1`` module remains the compatibility/shadow
evaluator.  This module binds the accepted V1.3 forward-persistent semantics
to the formal publication lane without changing the shadow contract or its
historical rows.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from topicpilot_api.topic_lifecycle_v1 import (
    BASE,
    DECLINING,
    FERMENTING,
    LIFECYCLE_STAGES,
    MAIN_RISE,
    MATURE,
    SPROUTING,
    LifecycleInput,
    LifecyclePolicy,
    LifecycleResult,
    evaluate_lifecycle,
)

LIFECYCLE_CONTRACT_VERSION = "topic-lifecycle-v1.3-formal.v2"
LIFECYCLE_CALCULATION_VERSION = "topic-lifecycle-v1.3-formal-evaluator.v1"
FORMAL_EVALUATION_MODE = "FORMAL"
FORMAL_INITIALIZATION_CONTRACT_VERSION = "FORMAL_BASE_BOOTSTRAP_V1"


def _stage_index(stage: str | None) -> int | None:
    if stage is None:
        return None
    try:
        return LIFECYCLE_STAGES.index(stage)
    except ValueError:
        return None


def _is_backward_transition(previous: str | None, candidate: str | None) -> bool:
    previous_index = _stage_index(previous)
    candidate_index = _stage_index(candidate)
    if previous_index is None or candidate_index is None:
        return False
    # A confirmed decline-to-BASE is the explicit true-cycle-reset exception.
    if previous == DECLINING and candidate == BASE:
        return False
    return candidate_index < previous_index


def _reset_memory(value: LifecycleInput, result: LifecycleResult) -> dict[str, Any]:
    """Close the failed fermentation cycle without importing shadow memory."""

    memory = dict(value.state_memory or result.state_memory or {})
    cycle_number = int(memory.get("cycleNumber") or result.cycle_number or 1)
    return {
        **memory,
        "lifecycleCycleId": f"{value.topic_id}:cycle:{cycle_number}",
        "cycleNumber": cycle_number,
        "cycleEnded": True,
        "activeBullishCycle": False,
        "mainRiseAncestry": False,
        "mainRiseSegment": None,
        "segmentEntryDate": None,
        "segmentAnchorDate": None,
        "daysSinceMeaningfulExpansion": 0,
        "lastMeaningfulExpansionDate": None,
        "memoryVersion": "topic-lifecycle-v1.3.formal.state-memory.1",
    }


def _persist_current_state(value: LifecycleInput, result: LifecycleResult) -> LifecycleResult:
    """Keep the prior state when V1.3 rejects an illegal backward candidate."""

    previous = value.previous_stage
    if previous is None:
        return result
    return replace(
        result,
        final_stage=previous,
        stage_entered_at=value.previous_stage_entered_at,
        stage_trading_days=(
            value.previous_stage_trading_days + 1
            if value.previous_stage_trading_days is not None
            else result.stage_trading_days
        ),
        transition_decision="HOLD_STATE_PERSISTENCE",
        transition_reason="ILLEGAL_BACKWARD_TRANSITION_STATE_PERSISTED",
        state_memory=dict(value.state_memory or result.state_memory or {}),
        main_rise_segment=(value.state_memory or {}).get("mainRiseSegment")
        or result.main_rise_segment,
        segment_entry_date=(
            value.previous_stage_entered_at
            if previous == MAIN_RISE and value.previous_stage_entered_at
            else result.segment_entry_date
        ),
        segment_anchor_date=(
            value.previous_stage_entered_at
            if previous == MAIN_RISE and value.previous_stage_entered_at
            else result.segment_anchor_date
        ),
    )


def evaluate_formal_lifecycle(
    value: LifecycleInput, policy: LifecyclePolicy | None = None
) -> LifecycleResult:
    """Evaluate one qualified formal observation using frozen V1.3 semantics.

    Numeric policy values and evidence calculations come from the accepted V1
    evaluator.  The formal adapter only applies the accepted V1.3 persistence
    guardrails: optional SPROUTING, FERMENTING failure-to-BASE, and suppression
    of backward candidates.  It never consults SHADOW rows.
    """

    result = evaluate_lifecycle(value, policy)
    if result.data_status == "INSUFFICIENT_DATA":
        # The compatibility evaluator keeps the prior stage visible for its
        # shadow read model.  A formal publication must instead fail closed:
        # no current stage is published when this date lacks qualified input.
        return replace(
            result,
            final_stage=None,
            stage_entered_at=None,
            stage_trading_days=None,
            evaluation_status="UNAVAILABLE",
            data_status="UNAVAILABLE",
            transition_decision="HOLD_FORMAL_GATE",
            transition_reason=f"INSUFFICIENT_FORMAL_INPUT:{result.transition_reason}",
            calculation_version=LIFECYCLE_CALCULATION_VERSION,
            evaluation_mode=FORMAL_EVALUATION_MODE,
        )

    candidate = result.candidate_stage
    if value.previous_stage == FERMENTING and candidate == SPROUTING:
        result = replace(
            result,
            final_stage=BASE,
            stage_entered_at=value.trading_date,
            stage_trading_days=1,
            transition_decision="CONFIRMED_TRANSITION",
            transition_reason="CONFIRMED_FERMENTATION_FAILURE_TO_BASE",
            state_memory=_reset_memory(value, result),
            main_rise_segment=None,
            segment_entry_date=None,
            segment_anchor_date=None,
            days_since_meaningful_expansion=0,
            drawdown_from_peak_pct=None,
            cycle_number=int((value.state_memory or {}).get("cycleNumber") or 1),
        )
    elif value.previous_stage == MATURE and candidate == MAIN_RISE:
        # V1.3 keeps renewed strength inside MATURE.  Only a future explicit
        # true-cycle-reset path can create a new MAIN_RISE state.
        result = _persist_current_state(value, result)
        result = replace(
            result,
            transition_reason="MATURE_RENEWED_STRENGTH_PERSISTS",
            confirmation_state={
                **result.confirmation_state,
                "state": "CURRENT",
                "v13Persistence": "MATURE_RENEWED_STRENGTH",
            },
        )
    elif _is_backward_transition(value.previous_stage, candidate):
        result = _persist_current_state(value, result)

    return replace(
        result,
        data_status="FORMAL" if result.final_stage is not None else "UNAVAILABLE",
        calculation_version=LIFECYCLE_CALCULATION_VERSION,
        evaluation_mode=FORMAL_EVALUATION_MODE,
    )


__all__ = [
    "BASE",
    "DECLINING",
    "FERMENTING",
    "FORMAL_EVALUATION_MODE",
    "FORMAL_INITIALIZATION_CONTRACT_VERSION",
    "LIFECYCLE_CALCULATION_VERSION",
    "LIFECYCLE_CONTRACT_VERSION",
    "LIFECYCLE_STAGES",
    "MAIN_RISE",
    "MATURE",
    "SPROUTING",
    "LifecycleInput",
    "LifecyclePolicy",
    "LifecycleResult",
    "evaluate_formal_lifecycle",
]
