"""Owner-approved V1 identity-aware lifecycle state machine.

The five lifecycle stages are intentionally unchanged.  This module owns the
deterministic, read-only evaluation semantics; it does not create a Strength
score and it never writes production data by itself.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from topicpilot_api.topic_lifecycle_contract import BACKEND_LIFECYCLE_STAGES

BASE, SPROUTING, FERMENTING, MAIN_RISE, MATURE, DECLINING = BACKEND_LIFECYCLE_STAGES
LIFECYCLE_STAGES = BACKEND_LIFECYCLE_STAGES
LIFECYCLE_CALCULATION_VERSION = "topic-lifecycle-v1-shadow.v1.2"
# Numeric policy and thresholds are unchanged; V1.2 ontology is carried by
# the calculation/state-memory versions instead of pretending this is a new
# calibration policy.
LIFECYCLE_POLICY_VERSION = "topic-lifecycle-policy.v1"

ROLE_LEAD = "LEAD"
ROLE_CORE = "CORE"
ROLE_RELATED = "RELATED"
KNOWN_ROLES = frozenset({ROLE_LEAD, ROLE_CORE, ROLE_RELATED})


@dataclass(frozen=True)
class LifecyclePolicy:
    """The single V1 policy bundle.

    These values retain the previously approved provisional numeric boundaries
    where applicable.  V1 changes the evidence topology and state memory, not
    the stage vocabulary or a Strength score.
    """

    version: str = LIFECYCLE_POLICY_VERSION
    minimum_observed_members: int = 3
    minimum_coverage_pct: float = 60.0
    sample_confidence_full_count: int = 10
    strong_member_change_pct: float = 4.0
    weak_member_change_pct: float = -4.0
    sprouting_leader_change_pct: float = 4.0
    sprouting_max_positive_breadth: float = 0.45
    fermenting_min_positive_breadth: float = 0.45
    fermenting_max_positive_breadth: float = 0.78
    fermenting_min_average_change_pct: float = 0.5
    main_rise_min_positive_breadth: float = 0.70
    main_rise_min_strong_breadth: float = 0.35
    main_rise_min_average_change_pct: float = 1.5
    mature_min_positive_breadth: float = 0.40
    mature_max_positive_breadth: float = 0.75
    mature_max_strong_breadth: float = 0.35
    mature_min_average_change_pct: float = 0.25
    declining_max_positive_breadth: float = 0.35
    declining_min_weak_ratio: float = 0.35
    declining_max_average_change_pct: float = -0.5
    normal_confirmation_days: int = 2
    decline_confirmation_days: int = 2
    minimum_transition_confidence: float = 0.30
    lead_core_authority_weight: float = 0.70
    related_authority_weight: float = 0.30
    meaningful_expansion_pct: float = 4.0
    mature_stalled_expansion_sessions: int = 5
    mature_recovery_min_positive_breadth: float = 0.45
    mature_recovery_min_average_change_pct: float = 0.5
    declining_drawdown_from_peak_pct: float = -8.0
    # A MATURE decline candidate must show full structural destruction, not
    # merely the lighter MATURE drawdown warning.  This keeps the V1.1
    # confirmation memory focused on the Owner's deep-deterioration cases.
    declining_structural_drawdown_from_peak_pct: float = -35.0
    # V1.1 Owner decision: a MAIN_RISE structural breakdown requires a
    # conjunction of identity-aware breadth, price damage, and weak breadth.
    # These are deliberately explicit gates, not an opaque score.
    structural_breakdown_min_drawdown_from_peak_pct: float = -15.0
    structural_breakdown_max_lead_core_positive_breadth: float = 0.20
    structural_breakdown_max_lead_core_average_change_pct: float = -4.0
    structural_breakdown_min_lead_core_weak_ratio: float = 0.60
    structural_breakdown_repair_min_positive_breadth: float = 0.70
    structural_breakdown_repair_min_average_change_pct: float = 1.5
    structural_breakdown_repair_min_strong_breadth: float = 0.35
    structural_breakdown_repair_max_weak_ratio: float = 0.35
    structural_breakdown_confirmation_days: int = 1
    declining_confirmation_window_days: int = 1


@dataclass(frozen=True)
class LifecycleObservation:
    member_id: str
    change_pct: float | None
    role: str | None = None
    role_source: str | None = None
    close: float | None = None
    previous_close: float | None = None


@dataclass(frozen=True)
class LifecycleInput:
    topic_id: str
    trading_date: date
    expected_member_count: int
    observations: tuple[LifecycleObservation, ...]
    previous_stage: str | None = None
    previous_stage_entered_at: date | None = None
    previous_stage_trading_days: int | None = None
    previous_candidate_stage: str | None = None
    previous_candidate_streak: int = 0
    state_memory: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class LifecycleEvidence:
    leadership: dict[str, Any]
    diffusion: dict[str, Any]
    group_strength: dict[str, Any]
    divergence_decay: dict[str, Any]
    persistence: dict[str, Any]
    sample_confidence: dict[str, Any]


@dataclass(frozen=True)
class LifecycleResult:
    topic_id: str
    trading_date: date
    previous_stage: str | None
    candidate_stage: str | None
    final_stage: str | None
    stage_entered_at: date | None
    stage_trading_days: int | None
    evaluation_status: str
    data_status: str
    transition_decision: str
    transition_reason: str
    evidence: LifecycleEvidence
    confirmation_state: dict[str, Any]
    policy_version: str
    calculation_version: str = LIFECYCLE_CALCULATION_VERSION
    evaluation_mode: str = "SHADOW"
    average_change: float | None = None
    coverage_pct: float | None = None
    main_rise_segment: int | None = None
    segment_entry_date: date | None = None
    segment_anchor_date: date | None = None
    days_since_meaningful_expansion: int | None = None
    drawdown_from_peak_pct: float | None = None
    state_memory: dict[str, Any] | None = None
    cycle_number: int | None = None


@dataclass(frozen=True)
class _GroupMetrics:
    count: int
    average_change: float | None
    positive_breadth: float | None
    strong_breadth: float | None
    weak_ratio: float | None
    leader_change: float | None
    leader_id: str | None


@dataclass(frozen=True)
class _Metrics:
    expected_count: int
    observed_count: int
    valid_change_count: int
    coverage_pct: float | None
    average_change: float | None
    positive_breadth: float | None
    strong_breadth: float | None
    weak_ratio: float | None
    leader_change: float | None
    leader_id: str | None
    leader_role: str | None
    positive_contribution_share: float | None
    groups: dict[str, _GroupMetrics]
    role_coverage_pct: float | None
    role_authority_available: bool
    authority_weighted_positive_breadth: float | None
    authority_weighted_strong_breadth: float | None
    lead_core_average_change: float | None
    lead_core_positive_breadth: float | None
    lead_core_strong_breadth: float | None
    lead_core_weak_ratio: float | None
    core_positive_breadth: float | None
    core_average_change: float | None
    related_positive_breadth: float | None


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _role(value: str | None) -> str | None:
    normalized = str(value or "").strip().upper()
    if normalized in {"REPRESENTATIVE", "LEADER", "PRIMARY", "LEAD"}:
        return ROLE_LEAD
    if normalized in {"CORE"}:
        return ROLE_CORE
    if normalized in {"RELATED", "SECONDARY"}:
        return ROLE_RELATED
    return None


def _group(items: list[LifecycleObservation], policy: LifecyclePolicy) -> _GroupMetrics:
    changes = [float(item.change_pct) for item in items if item.change_pct is not None]
    positive = sum(value > 0 for value in changes)
    strong = sum(value >= policy.strong_member_change_pct for value in changes)
    weak = sum(value <= policy.weak_member_change_pct for value in changes)
    leader = max(items, key=lambda item: float(item.change_pct)) if items else None
    return _GroupMetrics(
        count=len(changes),
        average_change=round(sum(changes) / len(changes), 4) if changes else None,
        positive_breadth=_ratio(positive, len(changes)),
        strong_breadth=_ratio(strong, len(changes)),
        weak_ratio=_ratio(weak, len(changes)),
        leader_change=(
            float(leader.change_pct)
            if leader and leader.change_pct is not None
            else None
        ),
        leader_id=leader.member_id if leader else None,
    )


def _metrics(value: LifecycleInput, policy: LifecyclePolicy) -> _Metrics:
    valid = [item for item in value.observations if item.change_pct is not None]
    changes = [float(item.change_pct) for item in valid]
    positive = sum(item > 0 for item in changes)
    strong = sum(item >= policy.strong_member_change_pct for item in changes)
    weak = sum(item <= policy.weak_member_change_pct for item in changes)
    role_items: dict[str, list[LifecycleObservation]] = {key: [] for key in KNOWN_ROLES}
    known_count = 0
    for item in valid:
        normalized = _role(item.role)
        if normalized is not None:
            role_items[normalized].append(item)
            known_count += 1
    groups = {key: _group(items, policy) for key, items in role_items.items()}
    core = groups[ROLE_CORE]
    related = groups[ROLE_RELATED]
    lead_core_items = role_items[ROLE_LEAD] + role_items[ROLE_CORE]
    lead_core = _group(lead_core_items, policy)
    leader_pool = role_items[ROLE_LEAD] or lead_core_items or valid
    leader = max(leader_pool, key=lambda item: float(item.change_pct)) if leader_pool else None
    positive_abs = sum(item for item in changes if item > 0)
    weighted_positive = (
        policy.lead_core_authority_weight * (lead_core.positive_breadth or 0.0)
        + policy.related_authority_weight * (related.positive_breadth or 0.0)
        if valid
        else None
    )
    weighted_strong = (
        policy.lead_core_authority_weight * (lead_core.strong_breadth or 0.0)
        + policy.related_authority_weight * (related.strong_breadth or 0.0)
        if valid
        else None
    )
    return _Metrics(
        expected_count=max(0, value.expected_member_count),
        observed_count=len(valid),
        valid_change_count=len(valid),
        coverage_pct=round(len(valid) * 100 / value.expected_member_count, 4)
        if value.expected_member_count
        else None,
        average_change=round(sum(changes) / len(changes), 4) if changes else None,
        positive_breadth=_ratio(positive, len(changes)),
        strong_breadth=_ratio(strong, len(changes)),
        weak_ratio=_ratio(weak, len(changes)),
        leader_change=float(leader.change_pct) if leader else None,
        leader_id=leader.member_id if leader else None,
        leader_role=_role(leader.role) if leader else None,
        positive_contribution_share=round(float(leader.change_pct) / positive_abs, 4)
        if leader and positive_abs
        else None,
        groups=groups,
        role_coverage_pct=round(known_count * 100 / len(valid), 4) if valid else None,
        role_authority_available=bool(valid) and known_count == len(valid),
        authority_weighted_positive_breadth=round(weighted_positive, 4)
        if weighted_positive is not None
        else None,
        authority_weighted_strong_breadth=round(weighted_strong, 4)
        if weighted_strong is not None
        else None,
        lead_core_average_change=lead_core.average_change,
        lead_core_positive_breadth=lead_core.positive_breadth,
        lead_core_strong_breadth=lead_core.strong_breadth,
        lead_core_weak_ratio=lead_core.weak_ratio,
        core_positive_breadth=core.positive_breadth,
        core_average_change=core.average_change,
        related_positive_breadth=related.positive_breadth,
    )


def _confidence(metrics: _Metrics, policy: LifecyclePolicy) -> dict[str, Any]:
    coverage = (metrics.coverage_pct or 0.0) / 100.0
    sample = min(1.0, metrics.valid_change_count / policy.sample_confidence_full_count)
    confidence = round(min(coverage, sample), 4)
    return {
        "confidence": confidence,
        "coveragePct": metrics.coverage_pct,
        "observedMemberCount": metrics.observed_count,
        "validChangeCount": metrics.valid_change_count,
        "expectedMemberCount": metrics.expected_count,
        "coverageConfidence": round(coverage, 4),
        "sampleConfidence": round(sample, 4),
        "smallSample": metrics.valid_change_count < policy.sample_confidence_full_count,
        "minimumObservedMembers": policy.minimum_observed_members,
        "roleCoveragePct": metrics.role_coverage_pct,
        "roleAuthorityAvailable": metrics.role_authority_available,
    }


def _previous_memory(value: LifecycleInput) -> dict[str, Any]:
    return dict(value.state_memory or {})


def _has_mature_ancestry(value: LifecycleInput) -> bool:
    """Return whether MATURE belongs to a MAIN_RISE-bearing bullish cycle."""

    memory = _previous_memory(value)
    return (
        bool(memory.get("mainRiseAncestry"))
        or int(memory.get("mainRiseSegment") or 0) > 0
        or value.previous_stage == MAIN_RISE
    )


def _float_map(value: Any) -> dict[str, float]:
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, float] = {}
    for key, item in value.items():
        try:
            result[str(key)] = float(item)
        except (TypeError, ValueError):
            continue
    return result


def _date_map(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): str(item) for key, item in value.items() if item}


def _progression(
    value: LifecycleInput, metrics: _Metrics, policy: LifecyclePolicy
) -> dict[str, Any]:
    memory = _previous_memory(value)
    prior_peaks = _float_map(memory.get("runningPeakCloseByMember"))
    prior_peak_dates = _date_map(memory.get("runningPeakDateByMember"))
    current_peaks = dict(prior_peaks)
    current_peak_dates = dict(prior_peak_dates)
    expansion_members: list[str] = []
    drawdowns: list[float] = []
    for item in value.observations:
        if _role(item.role) not in {ROLE_LEAD, ROLE_CORE} or item.close is None:
            continue
        close = float(item.close)
        prior_peak = prior_peaks.get(item.member_id)
        if prior_peak is None:
            prior_peak = (
                float(item.previous_close)
                if item.previous_close and item.previous_close > 0
                else close
            )
        current_peak = max(prior_peak, close)
        current_peaks[item.member_id] = round(current_peak, 8)
        if close >= current_peak or item.member_id not in current_peak_dates:
            current_peak_dates[item.member_id] = value.trading_date.isoformat()
        if prior_peak > 0 and close >= prior_peak * (1 + policy.meaningful_expansion_pct / 100):
            expansion_members.append(item.member_id)
        if current_peak > 0:
            drawdowns.append((close / current_peak - 1) * 100)
    drawdown = round(sum(drawdowns) / len(drawdowns), 4) if drawdowns else None
    meaningful = bool(expansion_members) and bool(
        (metrics.lead_core_positive_breadth or 0.0) >= policy.fermenting_min_positive_breadth
    )
    prior_days = int(memory.get("daysSinceMeaningfulExpansion") or 0)
    if value.previous_stage == MAIN_RISE:
        days = 0 if meaningful else prior_days + 1
    else:
        days = prior_days
    recovery = bool(
        (metrics.lead_core_positive_breadth or 0.0) >= policy.mature_recovery_min_positive_breadth
        and (metrics.lead_core_average_change or 0.0)
        >= policy.mature_recovery_min_average_change_pct
    )
    return {
        "meaningfulExpansion": meaningful,
        "meaningfulExpansionMembers": sorted(expansion_members),
        "daysSinceMeaningfulExpansion": days,
        "drawdownFromPeakPct": drawdown,
        "runningPeakCloseByMember": current_peaks,
        "runningPeakDateByMember": current_peak_dates,
        "trajectoryRecovered": recovery,
    }


def _main_rise_gate(metrics: _Metrics, policy: LifecyclePolicy) -> bool:
    # A Related-only or Leader-only group cannot enter MAIN_RISE.  Broad Core
    # can compensate for a weak/missing Lead through the Lead/Core gate.
    return bool(
        metrics.groups[ROLE_CORE].count > 0
        and (metrics.lead_core_positive_breadth or 0.0) >= policy.main_rise_min_positive_breadth
        and (metrics.lead_core_strong_breadth or 0.0) >= policy.main_rise_min_strong_breadth
        and (metrics.lead_core_average_change or 0.0) >= policy.main_rise_min_average_change_pct
        and (metrics.core_positive_breadth or 0.0) >= policy.main_rise_min_positive_breadth
    )


def _candidate(
    metrics: _Metrics,
    value: LifecycleInput,
    policy: LifecyclePolicy,
    progression: Mapping[str, Any],
) -> str | None:
    if not metrics.role_authority_available:
        return None
    positive = metrics.positive_breadth
    strong = metrics.strong_breadth
    weak = metrics.weak_ratio
    average = metrics.average_change
    if None in (positive, strong, weak, average):
        return None
    if value.previous_stage in {MATURE, BASE} and (
        (progression.get("drawdownFromPeakPct") or 0.0)
        <= policy.declining_structural_drawdown_from_peak_pct
        and (metrics.lead_core_positive_breadth or 0.0) <= policy.declining_max_positive_breadth
        and (metrics.lead_core_weak_ratio or 0.0) >= policy.declining_min_weak_ratio
    ):
        return DECLINING
    if (
        value.previous_stage == MAIN_RISE
        and int(progression.get("daysSinceMeaningfulExpansion") or 0)
        >= policy.mature_stalled_expansion_sessions
        and not progression.get("trajectoryRecovered")
    ):
        return MATURE
    if value.previous_stage == DECLINING and (
        (metrics.lead_core_positive_breadth or 0.0)
        >= policy.mature_recovery_min_positive_breadth
        and (metrics.lead_core_average_change or 0.0)
        >= policy.mature_recovery_min_average_change_pct
        and (metrics.lead_core_weak_ratio or 0.0)
        <= policy.structural_breakdown_repair_max_weak_ratio
    ):
        # A broad recovery from DECLINING is post-decline rebuilding.  It
        # must confirm BASE before any new bullish-cycle evidence is used.
        return BASE
    if value.previous_stage == DECLINING:
        # A decline cannot bypass the reset stage on an ordinary positive day.
        return None
    if value.previous_stage == MATURE and (
        _has_mature_ancestry(value)
        and
        policy.mature_min_positive_breadth <= (metrics.lead_core_positive_breadth or 0.0)
        and (metrics.lead_core_strong_breadth or 0.0) <= policy.mature_max_strong_breadth
        and (metrics.lead_core_average_change or 0.0) >= policy.mature_min_average_change_pct
    ):
        # Recovery from DECLINING is deliberately adjacent: DECLINING ->
        # MATURE must confirm before a later MATURE -> MAIN_RISE re-entry.
        return MATURE
    main = _main_rise_gate(metrics, policy)
    if main and value.previous_stage != BASE:
        return MAIN_RISE
    if value.previous_stage == MATURE and (
        _has_mature_ancestry(value)
        and
        policy.mature_min_positive_breadth <= (metrics.lead_core_positive_breadth or 0.0)
        and (metrics.lead_core_strong_breadth or 0.0) <= policy.mature_max_strong_breadth
        and (metrics.lead_core_average_change or 0.0) >= policy.mature_min_average_change_pct
    ):
        return MATURE
    fermenting = bool(
        metrics.groups[ROLE_CORE].count > 0
        and (metrics.core_positive_breadth or 0.0) >= policy.fermenting_min_positive_breadth
        and (metrics.authority_weighted_positive_breadth or 0.0)
        >= policy.fermenting_min_positive_breadth
        and (metrics.lead_core_average_change or 0.0) >= policy.fermenting_min_average_change_pct
    )
    if fermenting:
        return FERMENTING
    if (
        metrics.leader_change is not None
        and metrics.leader_change >= policy.sprouting_leader_change_pct
        and (
            (positive or 0.0) <= policy.sprouting_max_positive_breadth
            or not metrics.groups[ROLE_CORE].count
        )
    ):
        # Explicitly preserve the Owner distinction: one Leader can sprout,
        # but cannot satisfy the Main Rise Core gate.
        return SPROUTING
    return None


def _structural_breakdown_trigger(
    metrics: _Metrics,
    value: LifecycleInput,
    progression: Mapping[str, Any],
    policy: LifecyclePolicy,
) -> bool:
    """Return whether a MAIN_RISE date creates a severe breakdown candidate."""

    if value.previous_stage != MAIN_RISE:
        return False
    return bool(
        (metrics.lead_core_positive_breadth or 0.0)
        <= policy.structural_breakdown_max_lead_core_positive_breadth
        and (metrics.lead_core_average_change or 0.0)
        <= policy.structural_breakdown_max_lead_core_average_change_pct
        and (metrics.lead_core_weak_ratio or 0.0)
        >= policy.structural_breakdown_min_lead_core_weak_ratio
        and (progression.get("drawdownFromPeakPct") or 0.0)
        <= policy.structural_breakdown_min_drawdown_from_peak_pct
    )


def _structural_breakdown_repaired(
    metrics: _Metrics,
    value: LifecycleInput,
    progression: Mapping[str, Any],
    policy: LifecyclePolicy,
) -> bool:
    """Return whether a pending MAIN_RISE breakdown has genuinely repaired."""

    if value.previous_stage != MAIN_RISE:
        return False
    # A less-negative day is not repair.  Repair requires the existing
    # MAIN_RISE identity gate, normalized weak breadth, and a trajectory or
    # fresh-expansion signal.
    return bool(
        (metrics.lead_core_positive_breadth or 0.0)
        >= policy.structural_breakdown_repair_min_positive_breadth
        and (metrics.lead_core_average_change or 0.0)
        >= policy.structural_breakdown_repair_min_average_change_pct
        and (metrics.lead_core_strong_breadth or 0.0)
        >= policy.structural_breakdown_repair_min_strong_breadth
        and (metrics.lead_core_weak_ratio or 0.0)
        <= policy.structural_breakdown_repair_max_weak_ratio
        and bool(
            progression.get("trajectoryRecovered")
            or progression.get("meaningfulExpansion")
        )
    )


def _declining_repaired(
    metrics: _Metrics,
    value: LifecycleInput,
    progression: Mapping[str, Any],
    policy: LifecyclePolicy,
) -> bool:
    """Return whether a pending DECLINING candidate has genuine repair."""

    return bool(
        value.previous_stage in {MATURE, BASE}
        and (metrics.lead_core_positive_breadth or 0.0)
        >= policy.mature_recovery_min_positive_breadth
        and (metrics.lead_core_average_change or 0.0)
        >= policy.mature_recovery_min_average_change_pct
        and (metrics.lead_core_weak_ratio or 0.0)
        <= policy.structural_breakdown_repair_max_weak_ratio
        and bool(
            progression.get("trajectoryRecovered")
            or progression.get("meaningfulExpansion")
        )
    )


def _declining_deteriorated_since_pending(
    metrics: _Metrics,
    progression: Mapping[str, Any],
    prior_memory: Mapping[str, Any],
    policy: LifecyclePolicy,
) -> bool:
    """Return whether the pending decline has persisted or worsened."""

    evidence = prior_memory.get("decliningPendingEvidence")
    if not isinstance(evidence, Mapping):
        return False
    prior_drawdown = evidence.get("drawdownFromPeakPct")
    prior_breadth = evidence.get("leadCorePositiveBreadth")
    prior_average = evidence.get("leadCoreAverageChangePct")
    prior_weak = evidence.get("leadCoreWeakRatio")
    current_drawdown = progression.get("drawdownFromPeakPct")
    current_breadth = metrics.lead_core_positive_breadth
    current_average = metrics.lead_core_average_change
    current_weak = metrics.lead_core_weak_ratio
    comparisons = []
    if prior_drawdown is not None and current_drawdown is not None:
        comparisons.append(float(current_drawdown) < float(prior_drawdown))
    if prior_breadth is not None and current_breadth is not None:
        comparisons.append(float(current_breadth) < float(prior_breadth))
    if prior_average is not None and current_average is not None:
        comparisons.append(float(current_average) < float(prior_average))
    if prior_weak is not None and current_weak is not None:
        comparisons.append(float(current_weak) > float(prior_weak))
    # A still-active decline gate is also persistence even when the rounded
    # dimensions are equal. Equality outside the decline gate is neutral and
    # receives the bounded pending disposition below.
    still_structural = bool(
        (current_drawdown or 0.0) <= policy.declining_structural_drawdown_from_peak_pct
        and (current_breadth or 0.0) <= policy.declining_max_positive_breadth
        and (current_weak or 0.0) >= policy.declining_min_weak_ratio
        and (current_average or 0.0) <= policy.declining_max_average_change_pct
    )
    return still_structural or any(comparisons)


def _transition_distance(previous_stage: str | None, candidate_stage: str | None) -> int:
    if previous_stage is None or candidate_stage is None:
        return 0
    if previous_stage == candidate_stage:
        return 0
    if (previous_stage, candidate_stage) in {
        (BASE, SPROUTING),
        (BASE, FERMENTING),
        (SPROUTING, FERMENTING),
        (FERMENTING, MAIN_RISE),
        (MAIN_RISE, MATURE),
        (MATURE, MAIN_RISE),
        (MATURE, DECLINING),
        (BASE, DECLINING),
        (DECLINING, BASE),
    }:
        return 1
    try:
        return abs(LIFECYCLE_STAGES.index(candidate_stage) - LIFECYCLE_STAGES.index(previous_stage))
    except ValueError:
        return 0


def _state_memory(
    value: LifecycleInput,
    metrics: _Metrics,
    progression: Mapping[str, Any],
    final_stage: str | None,
    entered_at: date | None,
    policy: LifecyclePolicy,
) -> dict[str, Any]:
    prior = _previous_memory(value)
    segment = int(prior.get("mainRiseSegment") or 0)
    cycle_number = int(prior.get("cycleNumber") or 1)
    cycle_ended = bool(prior.get("cycleEnded"))
    main_rise_ancestry = bool(prior.get("mainRiseAncestry")) or segment > 0
    segment_entry = prior.get("segmentEntryDate")
    segment_anchor = prior.get("segmentAnchorDate")
    days = int(progression.get("daysSinceMeaningfulExpansion") or 0)
    if final_stage == DECLINING and value.previous_stage != DECLINING:
        # A confirmed decline ends the prior bullish cycle.  Segment memory is
        # cleared now; recovery through BASE starts a new cycle.
        segment = 0
        cycle_ended = True
        main_rise_ancestry = False
    elif final_stage == BASE and value.previous_stage == DECLINING:
        cycle_ended = True
        main_rise_ancestry = False
        segment = 0
    elif final_stage == MATURE and value.previous_stage == MAIN_RISE:
        # MATURE is only a high-level continuation of a MAIN_RISE-bearing
        # cycle; record that ancestry explicitly even when segment memory was
        # not initialized by a hand-built caller.
        cycle_ended = False
        main_rise_ancestry = True
    elif final_stage in {SPROUTING, FERMENTING} and value.previous_stage == BASE:
        if cycle_ended:
            cycle_number += 1
        cycle_ended = False
        main_rise_ancestry = False
        segment = 0
    elif final_stage == MAIN_RISE and value.previous_stage != MAIN_RISE:
        if value.previous_stage == MATURE and main_rise_ancestry:
            segment = segment + 1 if segment else 1
        else:
            if cycle_ended:
                cycle_number += 1
            cycle_ended = False
            segment = 1
        main_rise_ancestry = True
        segment_entry = value.trading_date.isoformat()
        segment_anchor = (
            value.previous_stage_entered_at.isoformat()
            if value.previous_stage_entered_at
            else value.trading_date.isoformat()
        )
        # A segment entry is not itself a meaningful expansion.  Preserve the
        # elapsed expansion clock when a MATURE -> MAIN_RISE re-entry is
        # confirmed without a fresh Lead/Core expansion on that date.
        days = 0 if progression.get("meaningfulExpansion") else days
    elif final_stage != MAIN_RISE and value.previous_stage != MAIN_RISE:
        days = int(prior.get("daysSinceMeaningfulExpansion") or 0)
    last_expansion = prior.get("lastMeaningfulExpansionDate")
    if progression.get("meaningfulExpansion"):
        last_expansion = value.trading_date.isoformat()
    return {
        "lifecycleCycleId": f"{value.topic_id}:cycle:{cycle_number}",
        "cycleNumber": cycle_number,
        "cycleEnded": cycle_ended,
        "activeBullishCycle": not cycle_ended,
        "mainRiseAncestry": main_rise_ancestry,
        "mainRiseSegment": segment or None,
        "segmentEntryDate": segment_entry,
        "segmentAnchorDate": segment_anchor,
        "daysSinceMeaningfulExpansion": days,
        "lastMeaningfulExpansionDate": last_expansion,
        "drawdownFromPeakPct": progression.get("drawdownFromPeakPct"),
        "runningPeakCloseByMember": dict(progression.get("runningPeakCloseByMember") or {}),
        "runningPeakDateByMember": dict(progression.get("runningPeakDateByMember") or {}),
        "trajectoryRecovered": progression.get("trajectoryRecovered"),
        "lastAuthorityWeightedPositiveBreadth": metrics.authority_weighted_positive_breadth,
        "lastLeadCoreAverageChangePct": metrics.lead_core_average_change,
        "memoryVersion": "topic-lifecycle-v1.2.state-memory.2",
    }


def _with_confirmation_memory(
    memory: dict[str, Any],
    prior: Mapping[str, Any],
    *,
    breakdown_pending: bool,
    breakdown_start_date: str | None,
    breakdown_age: int,
    breakdown_evidence: Mapping[str, Any] | None,
    breakdown_disposition: str,
    decline_pending: bool,
    decline_start_date: str | None,
    decline_age: int,
    decline_evidence: Mapping[str, Any] | None,
    decline_disposition: str,
) -> dict[str, Any]:
    """Persist V1.1 confirmation state in the existing JSON state memory."""

    memory.update(
        {
            "structuralBreakdownPending": bool(breakdown_pending),
            "structuralBreakdownStartDate": breakdown_start_date,
            "structuralBreakdownAge": int(breakdown_age),
            "structuralBreakdownEvidence": dict(breakdown_evidence or {}),
            "structuralBreakdownDisposition": breakdown_disposition,
            "decliningPending": bool(decline_pending),
            "decliningPendingStartDate": decline_start_date,
            "decliningPendingAge": int(decline_age),
            "decliningPendingEvidence": dict(decline_evidence or {}),
            "decliningPendingDisposition": decline_disposition,
            "confirmationMemoryVersion": "topic-lifecycle-v1.2.confirmation-memory.2",
        }
    )
    return memory


def evaluate_lifecycle(
    value: LifecycleInput, policy: LifecyclePolicy | None = None
) -> LifecycleResult:
    """Evaluate one date using identity-aware evidence and persistent memory."""

    active_policy = policy or LifecyclePolicy()
    metrics = _metrics(value, active_policy)
    confidence = _confidence(metrics, active_policy)
    progression = _progression(value, metrics, active_policy)
    groups = metrics.groups
    evidence = LifecycleEvidence(
        leadership={
            "leaderSemanticAvailable": bool(groups[ROLE_LEAD].count),
            "roleAuthorityAvailable": metrics.role_authority_available,
            "roleCoveragePct": metrics.role_coverage_pct,
            "roleCounts": {key: item.count for key, item in groups.items()},
            "leaderId": metrics.leader_id,
            "leaderRole": metrics.leader_role,
            "leaderChangePct": metrics.leader_change,
            "positiveContributionShare": metrics.positive_contribution_share,
            "authorityWeights": {
                "leadCore": active_policy.lead_core_authority_weight,
                "related": active_policy.related_authority_weight,
            },
        },
        diffusion={
            "positiveBreadth": metrics.positive_breadth,
            "observedMemberCount": metrics.observed_count,
            "expectedMemberCount": metrics.expected_count,
            "coveragePct": metrics.coverage_pct,
            "leadCorePositiveBreadth": metrics.lead_core_positive_breadth,
            "corePositiveBreadth": metrics.core_positive_breadth,
            "relatedPositiveBreadth": metrics.related_positive_breadth,
            "authorityWeightedPositiveBreadth": metrics.authority_weighted_positive_breadth,
        },
        group_strength={
            "averageChangePct": metrics.average_change,
            "strongBreadth": metrics.strong_breadth,
            "weakRatio": metrics.weak_ratio,
            "leadCoreAverageChangePct": metrics.lead_core_average_change,
            "leadCoreStrongBreadth": metrics.lead_core_strong_breadth,
            "coreAverageChangePct": metrics.core_average_change,
            "rawEvidenceOnly": True,
            "strengthScoreCreated": False,
        },
        divergence_decay={
            "weakRatio": metrics.weak_ratio,
            "positiveBreadth": metrics.positive_breadth,
            "averageChangePct": metrics.average_change,
            "drawdownFromPeakPct": progression.get("drawdownFromPeakPct"),
            "declineDrawdownThresholdPct": active_policy.declining_drawdown_from_peak_pct,
            "declineStructuralDrawdownThresholdPct": (
                active_policy.declining_structural_drawdown_from_peak_pct
            ),
            "daysSinceMeaningfulExpansion": progression.get("daysSinceMeaningfulExpansion"),
            "meaningfulExpansion": progression.get("meaningfulExpansion"),
            "trajectoryRecovered": progression.get("trajectoryRecovered"),
            "declineDualConfirmation": {
                "priceDeterioration": (
                    (progression.get("drawdownFromPeakPct") or 0.0)
                    <= active_policy.declining_structural_drawdown_from_peak_pct
                ),
                "participationDeterioration": (
                    (metrics.lead_core_positive_breadth or 0.0)
                    <= active_policy.declining_max_positive_breadth
                    and (metrics.lead_core_weak_ratio or 0.0)
                    >= active_policy.declining_min_weak_ratio
                ),
            },
        },
        persistence={
            "previousStage": value.previous_stage,
            "previousCandidateStage": value.previous_candidate_stage,
            "previousCandidateStreak": value.previous_candidate_streak,
            "tradingDate": value.trading_date.isoformat(),
            "stateMemoryVersion": "topic-lifecycle-v1.2.state-memory.2",
            "cycleNumber": (value.state_memory or {}).get("cycleNumber", 1),
            "mainRiseAncestry": bool((value.state_memory or {}).get("mainRiseAncestry")),
        },
        sample_confidence=confidence,
    )
    insufficient = (
        metrics.expected_count == 0
        or metrics.valid_change_count < active_policy.minimum_observed_members
        or (metrics.coverage_pct or 0.0) < active_policy.minimum_coverage_pct
        or not metrics.role_authority_available
    )
    if insufficient:
        reason = (
            "STRUCTURAL_ROLE_AUTHORITY_UNAVAILABLE"
            if metrics.valid_change_count >= active_policy.minimum_observed_members
            and (metrics.coverage_pct or 0.0) >= active_policy.minimum_coverage_pct
            and not metrics.role_authority_available
            else "INSUFFICIENT_DATA"
        )
        return LifecycleResult(
            value.topic_id,
            value.trading_date,
            value.previous_stage,
            None,
            value.previous_stage,
            value.previous_stage_entered_at,
            value.previous_stage_trading_days,
            "INSUFFICIENT_DATA",
            "INSUFFICIENT_DATA",
            "HOLD_INSUFFICIENT_DATA",
            reason,
            evidence,
            {
                "state": "INSUFFICIENT_DATA",
                "requiredCoveragePct": active_policy.minimum_coverage_pct,
                "candidateStreak": 0,
            },
            active_policy.version,
            average_change=metrics.average_change,
            coverage_pct=metrics.coverage_pct,
            main_rise_segment=(value.state_memory or {}).get("mainRiseSegment"),
            segment_entry_date=_date_or_none((value.state_memory or {}).get("segmentEntryDate")),
            segment_anchor_date=_date_or_none((value.state_memory or {}).get("segmentAnchorDate")),
            days_since_meaningful_expansion=(value.state_memory or {}).get(
                "daysSinceMeaningfulExpansion"
            ),
            drawdown_from_peak_pct=(value.state_memory or {}).get("drawdownFromPeakPct"),
            state_memory=dict(value.state_memory or {}),
            cycle_number=int((value.state_memory or {}).get("cycleNumber") or 1),
        )

    prior_memory = _previous_memory(value)
    prior_breakdown_pending = bool(prior_memory.get("structuralBreakdownPending"))
    prior_decline_pending = bool(prior_memory.get("decliningPending"))
    breakdown_now = _structural_breakdown_trigger(
        metrics, value, progression, active_policy
    )
    breakdown_repaired = _structural_breakdown_repaired(
        metrics, value, progression, active_policy
    )
    decline_repaired = _declining_repaired(
        metrics, value, progression, active_policy
    )
    candidate = _candidate(metrics, value, active_policy, progression)
    breakdown_created = breakdown_now and not prior_breakdown_pending
    breakdown_confirmed = prior_breakdown_pending and not breakdown_repaired
    breakdown_cancelled = prior_breakdown_pending and breakdown_repaired
    decline_created = (
        value.previous_stage in {MATURE, BASE}
        and candidate == DECLINING
        and not prior_decline_pending
    )
    decline_deteriorated = _declining_deteriorated_since_pending(
        metrics, progression, prior_memory, active_policy
    )
    prior_decline_age = int(prior_memory.get("decliningPendingAge") or 0)
    decline_neutral_pending = (
        prior_decline_pending
        and not decline_repaired
        and not decline_deteriorated
        and prior_decline_age < active_policy.declining_confirmation_window_days + 1
    )
    decline_confirmed = (
        prior_decline_pending
        and not decline_repaired
        and (decline_deteriorated or not decline_neutral_pending)
    )
    decline_cancelled = prior_decline_pending and decline_repaired
    if breakdown_created or breakdown_confirmed or breakdown_cancelled:
        # Structural breakdown is a MATURE candidate, but the first severe day
        # is only a persistent candidate.  Confirmation is evaluated on the
        # next valid session and can be cancelled by genuine repair.
        candidate = MATURE
    if decline_confirmed or decline_cancelled or decline_neutral_pending:
        # Keep the historical candidate visible on the disposition date even
        # when the raw trigger no longer independently fires.
        candidate = DECLINING
    confidence_value = float(confidence["confidence"])
    streak = (
        value.previous_candidate_streak + 1
        if candidate and candidate == value.previous_candidate_stage
        else 1
    )
    mature_stall = (
        candidate == MATURE
        and value.previous_stage == MAIN_RISE
        and not (breakdown_created or breakdown_confirmed or breakdown_cancelled)
    )
    required = (
        1
        if mature_stall
        else active_policy.decline_confirmation_days
        if candidate == DECLINING
        else active_policy.normal_confirmation_days
    )
    transition = False
    decision = "HOLD_CONFIRMATION"
    reason = "ORDINARY_SIGNAL_PENDING_CONFIRMATION"
    final_stage = value.previous_stage
    if breakdown_cancelled:
        decision, reason = "HOLD_CONFIRMATION", "STRUCTURAL_BREAKDOWN_CANCELLED_GENUINE_REPAIR"
        streak = 0
    elif breakdown_confirmed:
        transition = True
        decision, reason = "CONFIRMED_TRANSITION", "STRUCTURAL_BREAKDOWN_CONFIRMED"
        streak = 1
    elif breakdown_created:
        decision, reason = "HOLD_CONFIRMATION", "STRUCTURAL_BREAKDOWN_CANDIDATE"
        streak = 1
    elif decline_cancelled:
        decision, reason = "HOLD_CONFIRMATION", "DECLINING_CANDIDATE_CANCELLED_GENUINE_REPAIR"
        streak = 0
    elif decline_confirmed:
        transition = True
        decision, reason = "CONFIRMED_TRANSITION", "DECLINING_PENDING_CONFIRMATION_SATISFIED"
        streak = 1
    elif decline_created:
        decision, reason = "HOLD_CONFIRMATION", "DECLINING_CANDIDATE_PENDING_CONFIRMATION"
        streak = 1
    elif decline_neutral_pending:
        decision, reason = "HOLD_CONFIRMATION", "DECLINING_PENDING_NEUTRAL_BOUNDED"
        streak = 1
    elif candidate is None:
        decision, reason = "HOLD", "NO_STAGE_CANDIDATE"
        if value.previous_stage == MAIN_RISE:
            reason = "MAIN_RISE_PERSISTENCE_NORMAL_PULLBACK"
        streak = 0
    elif candidate == value.previous_stage:
        decision, reason = "HOLD_CURRENT_STAGE", "CURRENT_STAGE_EVIDENCE_PERSISTS"
        streak = 0
    elif confidence_value < active_policy.minimum_transition_confidence:
        decision, reason = "HOLD_LOW_CONFIDENCE", "SAMPLE_CONFIDENCE_BELOW_TRANSITION_MINIMUM"
    elif value.previous_stage and _transition_distance(value.previous_stage, candidate) > 1:
        decision, reason = "HOLD_ILLEGAL_TRANSITION", "JUMP_REQUIRES_ADJACENT_STAGE_CONFIRMATION"
    elif mature_stall:
        transition = True
        decision, reason = "CONFIRMED_TRANSITION", "MAIN_RISE_EXPANSION_STALLED_5_SESSIONS"
    elif streak >= required:
        transition = True
        decision, reason = "CONFIRMED_TRANSITION", "ADAPTIVE_CONFIRMATION_SATISFIED"
    if transition:
        final_stage = candidate
    if final_stage is None:
        entered_at = None
        trading_days = None
    elif final_stage == value.previous_stage and value.previous_stage_trading_days is not None:
        entered_at = value.previous_stage_entered_at
        trading_days = value.previous_stage_trading_days + 1
    else:
        entered_at = value.trading_date
        trading_days = 1
    memory = _state_memory(value, metrics, progression, final_stage, entered_at, active_policy)
    prior_breakdown_start = prior_memory.get("structuralBreakdownStartDate")
    prior_breakdown_age = int(prior_memory.get("structuralBreakdownAge") or 0)
    if breakdown_created:
        breakdown_pending = True
        breakdown_start = value.trading_date.isoformat()
        breakdown_age = 1
        breakdown_evidence = {
            "leadCorePositiveBreadth": metrics.lead_core_positive_breadth,
            "leadCoreAverageChangePct": metrics.lead_core_average_change,
            "leadCoreWeakRatio": metrics.lead_core_weak_ratio,
            "drawdownFromPeakPct": progression.get("drawdownFromPeakPct"),
            "meaningfulExpansion": progression.get("meaningfulExpansion"),
            "trajectoryRecovered": progression.get("trajectoryRecovered"),
        }
        breakdown_disposition = "PENDING_NEXT_VALID_SESSION"
    elif breakdown_confirmed:
        breakdown_pending = False
        breakdown_start = prior_breakdown_start
        breakdown_age = prior_breakdown_age + 1
        breakdown_evidence = prior_memory.get("structuralBreakdownEvidence")
        breakdown_disposition = "CONFIRMED"
    elif breakdown_cancelled:
        breakdown_pending = False
        breakdown_start = prior_breakdown_start
        breakdown_age = prior_breakdown_age + 1
        breakdown_evidence = prior_memory.get("structuralBreakdownEvidence")
        breakdown_disposition = "CANCELLED_GENUINE_REPAIR"
    else:
        breakdown_pending = prior_breakdown_pending
        breakdown_start = prior_breakdown_start
        breakdown_age = prior_breakdown_age + (1 if prior_breakdown_pending else 0)
        breakdown_evidence = prior_memory.get("structuralBreakdownEvidence")
        breakdown_disposition = (
            "PENDING_NEXT_VALID_SESSION" if prior_breakdown_pending else "NONE"
        )

    prior_decline_start = prior_memory.get("decliningPendingStartDate")
    if decline_created:
        decline_pending = True
        decline_start = value.trading_date.isoformat()
        decline_age = 1
        decline_evidence = {
            "leadCorePositiveBreadth": metrics.lead_core_positive_breadth,
            "leadCoreAverageChangePct": metrics.lead_core_average_change,
            "leadCoreWeakRatio": metrics.lead_core_weak_ratio,
            "drawdownFromPeakPct": progression.get("drawdownFromPeakPct"),
            "meaningfulExpansion": progression.get("meaningfulExpansion"),
            "trajectoryRecovered": progression.get("trajectoryRecovered"),
        }
        decline_disposition = "PENDING_NEXT_VALID_SESSION"
    elif decline_confirmed:
        decline_pending = False
        decline_start = prior_decline_start
        decline_age = prior_decline_age + 1
        decline_evidence = prior_memory.get("decliningPendingEvidence")
        decline_disposition = "CONFIRMED"
    elif decline_cancelled:
        decline_pending = False
        decline_start = prior_decline_start
        decline_age = prior_decline_age + 1
        decline_evidence = prior_memory.get("decliningPendingEvidence")
        decline_disposition = "CANCELLED_GENUINE_REPAIR"
    else:
        decline_pending = prior_decline_pending
        decline_start = prior_decline_start
        decline_age = prior_decline_age + (1 if prior_decline_pending else 0)
        decline_evidence = prior_memory.get("decliningPendingEvidence")
        decline_disposition = "PENDING_NEXT_VALID_SESSION" if prior_decline_pending else "NONE"
    memory = _with_confirmation_memory(
        memory,
        prior_memory,
        breakdown_pending=breakdown_pending,
        breakdown_start_date=breakdown_start,
        breakdown_age=breakdown_age,
        breakdown_evidence=breakdown_evidence,
        breakdown_disposition=breakdown_disposition,
        decline_pending=decline_pending,
        decline_start_date=decline_start,
        decline_age=decline_age,
        decline_evidence=decline_evidence,
        decline_disposition=decline_disposition,
    )
    persistence_classification = (
        "STRUCTURAL_BREAKDOWN"
        if breakdown_created or breakdown_confirmed or breakdown_cancelled
        else "NORMAL_PULLBACK"
        if value.previous_stage == MAIN_RISE
        else None
    )
    confirmation_age = max(
        breakdown_age if breakdown_created or breakdown_confirmed or breakdown_cancelled else 0,
        decline_age if decline_created or decline_confirmed or decline_cancelled else 0,
    )
    return LifecycleResult(
        value.topic_id,
        value.trading_date,
        value.previous_stage,
        candidate,
        final_stage,
        entered_at,
        trading_days,
        "EVALUATED" if final_stage else "PENDING",
        "SHADOW" if final_stage else "PENDING",
        decision,
        reason,
        evidence,
        {
            "state": "CONFIRMED" if transition else ("CURRENT" if final_stage else "PENDING"),
            "candidateStage": candidate,
            "candidateStreak": streak,
            "requiredTradingDays": required,
            "meaningfulExpansion": progression.get("meaningfulExpansion"),
            "daysSinceMeaningfulExpansion": progression.get("daysSinceMeaningfulExpansion"),
            "structuralBreakdownPending": breakdown_pending,
            "structuralBreakdownDisposition": breakdown_disposition,
            "decliningPending": decline_pending,
            "decliningPendingDisposition": decline_disposition,
            "confirmationAge": confirmation_age,
            "persistenceClassification": persistence_classification,
        },
        active_policy.version,
        average_change=metrics.average_change,
        coverage_pct=metrics.coverage_pct,
        main_rise_segment=memory.get("mainRiseSegment"),
        segment_entry_date=_date_or_none(memory.get("segmentEntryDate")),
        segment_anchor_date=_date_or_none(memory.get("segmentAnchorDate")),
        days_since_meaningful_expansion=memory.get("daysSinceMeaningfulExpansion"),
        drawdown_from_peak_pct=memory.get("drawdownFromPeakPct"),
        state_memory=memory,
        cycle_number=memory.get("cycleNumber"),
    )


def _date_or_none(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


__all__ = [
    "BASE",
    "DECLINING",
    "FERMENTING",
    "LIFECYCLE_CALCULATION_VERSION",
    "LIFECYCLE_POLICY_VERSION",
    "LIFECYCLE_STAGES",
    "MAIN_RISE",
    "MATURE",
    "SPROUTING",
    "LifecycleEvidence",
    "LifecycleInput",
    "LifecycleObservation",
    "LifecyclePolicy",
    "LifecycleResult",
    "evaluate_lifecycle",
]
