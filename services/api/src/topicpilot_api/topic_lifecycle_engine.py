"""Configurable, explainable V2 topic lifecycle shadow engine.

This module owns the five PM-frozen lifecycle semantics.  Numeric values are
explicitly provisional and tunable; they are not score/grade rules and are
never used as a frontend-derived semantic.  The DB runner reads only formal
V2 snapshots, effective topic relations, and accepted canonical daily bars.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from topicpilot_api.orm import (
    InstrumentTopicRelation,
    LiveTrackingUniverse,
    TopicLifecycleResult,
    TopicSnapshot,
)
from topicpilot_api.topic_snapshot_engine import MemberPriceEvidence, read_price_evidence

SPROUTING = "SPROUTING"
FERMENTING = "FERMENTING"
MAIN_RISE = "MAIN_RISE"
MATURE = "MATURE"
DECLINING = "DECLINING"
LIFECYCLE_STAGES = (SPROUTING, FERMENTING, MAIN_RISE, MATURE, DECLINING)
LIFECYCLE_CALCULATION_VERSION = "topic-lifecycle-shadow.v1"
LIFECYCLE_POLICY_VERSION = "topic-lifecycle-policy.provisional.1"


@dataclass(frozen=True)
class LifecyclePolicy:
    """Central policy bundle; every numeric field is PROVISIONAL/TUNABLE."""

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
    strong_jump_min_confidence: float = 0.70
    strong_jump_min_positive_breadth: float = 0.82
    strong_jump_min_strong_breadth: float = 0.45
    strong_jump_min_average_change_pct: float = 3.0
    strong_decline_min_confidence: float = 0.70
    strong_decline_min_weak_ratio: float = 0.60
    strong_decline_max_average_change_pct: float = -2.0
    minimum_transition_confidence: float = 0.30


@dataclass(frozen=True)
class LifecycleObservation:
    member_id: str
    change_pct: float | None
    role: str | None = None


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


@dataclass
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


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


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
    }


def _metrics(value: LifecycleInput, policy: LifecyclePolicy) -> _Metrics:
    valid = [item for item in value.observations if item.change_pct is not None]
    observed = len(valid)
    expected = max(0, value.expected_member_count)
    changes = [float(item.change_pct) for item in valid]
    positive = sum(item > 0 for item in changes)
    strong = sum(item >= policy.strong_member_change_pct for item in changes)
    weak = sum(item <= policy.weak_member_change_pct for item in changes)
    role_leaders = [
        item
        for item in valid
        if (item.role or "").upper() in {"LEADER", "PRIMARY", "REPRESENTATIVE"}
    ]
    leader = max(role_leaders or valid, key=lambda item: float(item.change_pct)) if valid else None
    positive_abs = sum(item for item in changes if item > 0)
    return _Metrics(
        expected,
        observed,
        observed,
        round(observed * 100 / expected, 4) if expected else None,
        round(sum(changes) / observed, 4) if observed else None,
        _ratio(positive, observed),
        _ratio(strong, observed),
        _ratio(weak, observed),
        float(leader.change_pct) if leader else None,
        leader.member_id if leader else None,
        leader.role if leader else None,
        round(float(leader.change_pct) / positive_abs, 4) if leader and positive_abs else None,
    )


def _candidate(
    metrics: _Metrics, previous_stage: str | None, policy: LifecyclePolicy
) -> str | None:
    positive = metrics.positive_breadth
    strong = metrics.strong_breadth
    weak = metrics.weak_ratio
    average = metrics.average_change
    if None in (positive, strong, weak, average):
        return None
    if (
        positive <= policy.declining_max_positive_breadth
        and weak >= policy.declining_min_weak_ratio
        and average <= policy.declining_max_average_change_pct
    ):
        return DECLINING
    if (
        positive >= policy.main_rise_min_positive_breadth
        and strong >= policy.main_rise_min_strong_breadth
        and average >= policy.main_rise_min_average_change_pct
    ):
        return MAIN_RISE
    if (
        previous_stage in {MAIN_RISE, MATURE}
        and policy.mature_min_positive_breadth <= positive <= policy.mature_max_positive_breadth
        and strong <= policy.mature_max_strong_breadth
        and average >= policy.mature_min_average_change_pct
    ):
        return MATURE
    if (
        policy.fermenting_min_positive_breadth <= positive < policy.fermenting_max_positive_breadth
        and average >= policy.fermenting_min_average_change_pct
    ):
        return FERMENTING
    if (
        metrics.leader_change is not None
        and metrics.leader_change >= policy.sprouting_leader_change_pct
        and positive <= policy.sprouting_max_positive_breadth
    ):
        return SPROUTING
    return None


def _transition_distance(previous_stage: str | None, candidate_stage: str | None) -> int:
    """Return the ordinal distance between stages for jump guardrails."""

    if previous_stage is None or candidate_stage is None:
        return 0
    try:
        return abs(LIFECYCLE_STAGES.index(candidate_stage) - LIFECYCLE_STAGES.index(previous_stage))
    except ValueError:
        return 0


def evaluate_lifecycle(
    value: LifecycleInput, policy: LifecyclePolicy | None = None
) -> LifecycleResult:
    """Evaluate one trading day with adaptive confirmation/hysteresis."""

    active_policy = policy or LifecyclePolicy()
    metrics = _metrics(value, active_policy)
    confidence = _confidence(metrics, active_policy)
    leader_semantic_available = any(
        (item.role or "").upper() in {"LEADER", "PRIMARY", "REPRESENTATIVE"}
        for item in value.observations
    )
    evidence = LifecycleEvidence(
        leadership={
            "leaderSemanticAvailable": leader_semantic_available,
            "leaderProxy": (
                "maxObservedChange"
                if not leader_semantic_available
                else "roleAwareObservedChange"
            ),
            "leaderId": metrics.leader_id,
            "leaderRole": metrics.leader_role,
            "leaderChangePct": metrics.leader_change,
            "positiveContributionShare": metrics.positive_contribution_share,
        },
        diffusion={
            "positiveBreadth": metrics.positive_breadth,
            "observedMemberCount": metrics.observed_count,
            "expectedMemberCount": metrics.expected_count,
            "coveragePct": metrics.coverage_pct,
        },
        group_strength={
            "averageChangePct": metrics.average_change,
            "strongBreadth": metrics.strong_breadth,
            "weakRatio": metrics.weak_ratio,
        },
        divergence_decay={
            "weakRatio": metrics.weak_ratio,
            "positiveBreadth": metrics.positive_breadth,
            "averageChangePct": metrics.average_change,
            "divergenceSignal": bool(
                metrics.positive_breadth is not None
                and metrics.strong_breadth is not None
                and metrics.positive_breadth < active_policy.main_rise_min_positive_breadth
                and metrics.strong_breadth < active_policy.main_rise_min_strong_breadth
            ),
        },
        persistence={
            "previousStage": value.previous_stage,
            "previousCandidateStage": value.previous_candidate_stage,
            "previousCandidateStreak": value.previous_candidate_streak,
            "tradingDate": value.trading_date.isoformat(),
        },
        sample_confidence=confidence,
    )
    insufficient = (
        metrics.expected_count == 0
        or metrics.valid_change_count < active_policy.minimum_observed_members
        or (metrics.coverage_pct or 0.0) < active_policy.minimum_coverage_pct
    )
    if insufficient:
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
            "INSUFFICIENT_DATA",
            evidence,
            {
                "state": "INSUFFICIENT_DATA",
                "requiredCoveragePct": active_policy.minimum_coverage_pct,
            },
            active_policy.version,
            average_change=metrics.average_change,
            coverage_pct=metrics.coverage_pct,
        )

    candidate = _candidate(metrics, value.previous_stage, active_policy)
    confidence_value = float(confidence["confidence"])
    strong_jump = (
        candidate == MAIN_RISE
        and confidence_value >= active_policy.strong_jump_min_confidence
        and (metrics.positive_breadth or 0.0) >= active_policy.strong_jump_min_positive_breadth
        and (metrics.strong_breadth or 0.0) >= active_policy.strong_jump_min_strong_breadth
        and (metrics.average_change or 0.0) >= active_policy.strong_jump_min_average_change_pct
    )
    strong_decline = (
        candidate == DECLINING
        and confidence_value >= active_policy.strong_decline_min_confidence
        and (metrics.weak_ratio or 0.0) >= active_policy.strong_decline_min_weak_ratio
        and (metrics.average_change or 0.0) <= active_policy.strong_decline_max_average_change_pct
    )
    streak = (
        value.previous_candidate_streak + 1
        if candidate and candidate == value.previous_candidate_stage
        else 1
    )
    required = (
        active_policy.decline_confirmation_days
        if candidate == DECLINING
        else active_policy.normal_confirmation_days
    )
    transition = False
    decision = "HOLD_CONFIRMATION"
    reason = "ORDINARY_SIGNAL_PENDING_CONFIRMATION"
    final_stage = value.previous_stage
    if candidate is None:
        decision, reason = "HOLD", "NO_STAGE_CANDIDATE"
        streak = 0
    elif candidate == value.previous_stage:
        decision, reason = "HOLD_CURRENT_STAGE", "CURRENT_STAGE_EVIDENCE_PERSISTS"
        streak = 0
    elif strong_jump or strong_decline:
        transition = True
        decision = "JUMP_TRANSITION"
        reason = "STRONG_STRUCTURE_SIGNAL"
    elif confidence_value < active_policy.minimum_transition_confidence:
        decision, reason = "HOLD_LOW_CONFIDENCE", "SAMPLE_CONFIDENCE_BELOW_TRANSITION_MINIMUM"
    elif value.previous_stage and _transition_distance(value.previous_stage, candidate) > 1:
        # A normal signal may only move one adjacent stage at a time.  This
        # prevents a noisy observation from silently skipping the diffusion
        # and consolidation semantics; strong structure signals are handled
        # by the explicit jump branches above.
        decision, reason = "HOLD_ILLEGAL_TRANSITION", "JUMP_REQUIRES_STRONG_EVIDENCE"
    elif streak >= required:
        transition = True
        decision = "CONFIRMED_TRANSITION"
        reason = "ADAPTIVE_CONFIRMATION_SATISFIED"
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
            "strongSignal": strong_jump or strong_decline,
        },
        active_policy.version,
        average_change=metrics.average_change,
        coverage_pct=metrics.coverage_pct,
    )


def _date_rows(session: Session, evaluation_date: date) -> list[TopicSnapshot]:
    return list(
        session.scalars(
            select(TopicSnapshot)
            .where(TopicSnapshot.snapshot_date == evaluation_date)
            .order_by(TopicSnapshot.topic_slug)
        )
    )


class TopicLifecycleEngine:
    """Persistence adapter for V2 shadow lifecycle evaluations."""

    def __init__(
        self,
        session: Session,
        *,
        policy: LifecyclePolicy | None = None,
        calculation_version: str = LIFECYCLE_CALCULATION_VERSION,
    ) -> None:
        self.session = session
        self.policy = policy or LifecyclePolicy()
        self.calculation_version = calculation_version

    def run_once(self, *, evaluation_date: date) -> dict[str, Any]:
        snapshots = _date_rows(self.session, evaluation_date)
        if not snapshots:
            return {
                "evaluationDate": evaluation_date.isoformat(),
                "status": "WAITING_FOR_FORMAL_OBSERVATIONS",
                "topicCount": 0,
                "policyVersion": self.policy.version,
            }
        evidence = read_price_evidence(self.session, evaluation_date)
        tracking_ids = set(
            self.session.scalars(select(LiveTrackingUniverse.instrument_id)).all()
        )
        relation_rows = list(
            self.session.execute(
                select(
                    InstrumentTopicRelation.topic_id,
                    InstrumentTopicRelation.instrument_id,
                    InstrumentTopicRelation.relationship_metadata,
                ).where(
                    InstrumentTopicRelation.valid_from <= evaluation_date,
                    (InstrumentTopicRelation.valid_to.is_(None))
                    | (InstrumentTopicRelation.valid_to >= evaluation_date),
                    InstrumentTopicRelation.instrument_id.in_(tracking_ids),
                )
            ).all()
        )
        members: dict[UUID, list[tuple[UUID, str | None]]] = defaultdict(list)
        for topic_id, instrument_id, metadata in relation_rows:
            role = None
            if metadata:
                role = metadata.get("topicRole") or metadata.get("role")
            members[topic_id].append((instrument_id, role))
        previous = self._previous_states(evaluation_date)
        persisted = 0
        status_counts: dict[str, int] = defaultdict(int)
        topic_results: list[dict[str, Any]] = []
        for snapshot in snapshots:
            member_rows = members.get(snapshot.topic_id, [])
            observations = tuple(
                LifecycleObservation(str(instrument_id), _change(item), role)
                for instrument_id, role in member_rows
                if (item := evidence.get(instrument_id)) is not None
                and item.current_date == evaluation_date
            )
            state = previous.get(snapshot.topic_id, {})
            value = LifecycleInput(
                str(snapshot.topic_id),
                evaluation_date,
                int(snapshot.stock_count),
                observations,
                state.get("final_stage"),
                state.get("stage_entered_at"),
                state.get("stage_trading_days"),
                state.get("candidate_stage"),
                int(state.get("candidate_streak") or 0),
            )
            result = evaluate_lifecycle(self._with_calculation(value), self.policy)
            self._persist(snapshot, result)
            persisted += 1
            status_counts[result.data_status] += 1
            topic_results.append(
                {
                    "topicId": result.topic_id,
                    "tradingDate": result.trading_date.isoformat(),
                    "previousStage": result.previous_stage,
                    "candidateStage": result.candidate_stage,
                    "finalStage": result.final_stage,
                    "stageEnteredAt": (
                        result.stage_entered_at.isoformat()
                        if result.stage_entered_at
                        else None
                    ),
                    "stageTradingDays": result.stage_trading_days,
                    "evaluationStatus": result.evaluation_status,
                    "dataStatus": result.data_status,
                    "transitionDecision": result.transition_decision,
                    "transitionReason": result.transition_reason,
                    "evidence": asdict(result.evidence),
                    "confirmationState": result.confirmation_state,
                    "policyVersion": result.policy_version,
                    "calculationVersion": result.calculation_version,
                    "evaluationMode": result.evaluation_mode,
                }
            )
            previous[snapshot.topic_id] = {
                "final_stage": result.final_stage,
                "stage_entered_at": result.stage_entered_at,
                "stage_trading_days": result.stage_trading_days,
                "candidate_stage": result.candidate_stage,
                "candidate_streak": result.confirmation_state.get("candidateStreak", 0),
            }
        self.session.commit()
        return {
            "evaluationDate": evaluation_date.isoformat(),
            "status": "SUCCESS",
            "topicCount": persisted,
            "dataStatusCounts": dict(sorted(status_counts.items())),
            "policyVersion": self.policy.version,
            "calculationVersion": self.calculation_version,
            "evaluationMode": "SHADOW",
            "topicResults": topic_results,
        }

    def _with_calculation(self, value: LifecycleInput) -> LifecycleInput:
        return value

    def _previous_states(self, evaluation_date: date) -> dict[UUID, dict[str, Any]]:
        rows = list(
            self.session.scalars(
                select(TopicLifecycleResult)
                .where(
                    TopicLifecycleResult.evaluation_date < evaluation_date,
                    TopicLifecycleResult.policy_version == self.policy.version,
                    TopicLifecycleResult.evaluation_mode == "SHADOW",
                )
                .order_by(TopicLifecycleResult.topic_id, TopicLifecycleResult.evaluation_date)
            )
        )
        states: dict[UUID, dict[str, Any]] = {}
        for row in rows:
            states[row.topic_id] = {
                "final_stage": row.final_stage,
                "stage_entered_at": row.stage_entered_at,
                "stage_trading_days": row.stage_trading_days,
                "candidate_stage": row.candidate_stage,
                "candidate_streak": (row.confirmation_state or {}).get("candidateStreak", 0),
            }
        return states

    def _persist(self, snapshot: TopicSnapshot, result: LifecycleResult) -> None:
        existing = self.session.scalar(
            select(TopicLifecycleResult).where(
                TopicLifecycleResult.topic_id == snapshot.topic_id,
                TopicLifecycleResult.evaluation_date == result.trading_date,
                TopicLifecycleResult.policy_version == self.policy.version,
                TopicLifecycleResult.evaluation_mode == "SHADOW",
            )
        )
        values = {
            "evaluation_date": result.trading_date,
            "topic_id": snapshot.topic_id,
            "topic_slug": snapshot.topic_slug,
            "previous_stage": result.previous_stage,
            "candidate_stage": result.candidate_stage,
            "final_stage": result.final_stage,
            "stage_entered_at": result.stage_entered_at,
            "stage_trading_days": result.stage_trading_days,
            "evaluation_status": result.evaluation_status,
            "data_status": result.data_status,
            "transition_decision": result.transition_decision,
            "transition_reason": result.transition_reason,
            "leadership_evidence": result.evidence.leadership,
            "diffusion_evidence": result.evidence.diffusion,
            "group_strength_evidence": result.evidence.group_strength,
            "divergence_decay_evidence": result.evidence.divergence_decay,
            "persistence_evidence": result.evidence.persistence,
            "sample_confidence": result.evidence.sample_confidence,
            "confirmation_state": result.confirmation_state,
            "policy_version": result.policy_version,
            "calculation_version": self.calculation_version,
            "evaluation_mode": "SHADOW",
            "snapshot_date": snapshot.snapshot_date,
            "average_change": _decimal(result.average_change),
            "coverage_pct": _decimal(result.coverage_pct, places=3),
        }
        if existing is None:
            self.session.add(TopicLifecycleResult(**values))
            return
        # Retry-safe: deterministic same-key rows are left intact.  This keeps
        # the as-of evidence immutable even if a worker is retried.
        immutable_keys = (
            "final_stage",
            "candidate_stage",
            "transition_reason",
            "calculation_version",
        )
        if any(getattr(existing, key) != values[key] for key in immutable_keys):
            raise ValueError(
                f"lifecycle result conflict for {snapshot.topic_slug} {result.trading_date} "
                f"policy {self.policy.version}; use a new policy version for recalibration"
            )


def _change(item: MemberPriceEvidence) -> float | None:
    value = item.change_pct
    return float(value) if value is not None else None


def _decimal(value: float | None, *, places: int = 4) -> Decimal | None:
    if value is None:
        return None
    quantum = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)


__all__ = [
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
    "TopicLifecycleEngine",
    "evaluate_lifecycle",
]
