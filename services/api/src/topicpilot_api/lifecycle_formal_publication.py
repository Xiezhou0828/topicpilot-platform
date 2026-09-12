"""Lifecycle V1.3 formal evaluation, persistence, and readback boundary.

This module consumes only the accepted formal Topic Daily Snapshot authority.
It deliberately has no adapter from the existing SHADOW table: a formal row
is either freshly evaluated from qualified formal inputs or is recorded as a
fail-closed unavailable decision.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, aliased

from topicpilot_api.orm import (
    Topic,
    TopicHierarchy,
    TopicLifecycleFormalResult,
    TopicSnapshot,
    TopicSnapshotMemberFact,
)
from topicpilot_api.topic_lifecycle_engine import (
    _formal_observations,
    _formal_snapshot_lineage,
)
from topicpilot_api.topic_lifecycle_v1 import LifecycleInput, LifecyclePolicy, LifecycleResult
from topicpilot_api.topic_lifecycle_v1_3_formal import (
    BASE,
    FORMAL_EVALUATION_MODE,
    FORMAL_INITIALIZATION_CONTRACT_VERSION,
    LIFECYCLE_CALCULATION_VERSION,
    LIFECYCLE_CONTRACT_VERSION,
    evaluate_formal_lifecycle,
)
from topicpilot_api.topic_snapshot_engine import read_price_evidence

A9_FORMAL_TOPIC_SNAPSHOT_START = date(2026, 8, 24)
FORMAL_SCOPE_CONTRACT_VERSION = "lifecycle-formal-leaf-scope.v1"
FORMAL_SCOPE_EXPECTED_LEAVES = 107
FORMAL_PUBLICATION_STATUS_PUBLISHED = "PUBLISHED"
FORMAL_PUBLICATION_STATUS_UNAVAILABLE = "UNAVAILABLE"
FORMAL_PUBLICATION_STATUS_SUPERSEDED = "SUPERSEDED"
FORMAL_CORRECTION_SUPERSESSION_REASON = "CORRECTED_A9_STRUCTURAL_ROLE_AUTHORITY"


@dataclass(frozen=True)
class FormalLifecycleGate:
    passed: bool
    reason: str | None
    lineage: dict[str, Any]
    input_snapshot_hash: str | None


@dataclass(frozen=True)
class FormalLifecycleRun:
    evaluation_date: date
    status: str
    expected_leaf_date_rows: int
    formal_rows: int
    unavailable_rows: int
    persisted_rows: int
    reason_breakdown: dict[str, int]
    backward_transitions: int
    topic_results: list[dict[str, Any]]
    new_published: int = 0
    new_unavailable: int = 0
    superseded_decisions: int = 0
    idempotent_rows: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "evaluationDate": self.evaluation_date.isoformat(),
            "status": self.status,
            "expectedLeafDateRows": self.expected_leaf_date_rows,
            "formalLifecycleRows": self.formal_rows,
            "unavailableRows": self.unavailable_rows,
            "persistedRows": self.persisted_rows,
            "reasonBreakdown": self.reason_breakdown,
            "backwardTransitions": self.backward_transitions,
            "NEW_PUBLISHED": self.new_published,
            "NEW_UNAVAILABLE": self.new_unavailable,
            "SUPERSEDED_DECISIONS": self.superseded_decisions,
            "IDEMPOTENT": self.idempotent_rows,
            "topicResults": self.topic_results,
            "contractVersion": LIFECYCLE_CONTRACT_VERSION,
            "policyVersion": LifecyclePolicy().version,
            "calculationVersion": LIFECYCLE_CALCULATION_VERSION,
            "evaluationMode": FORMAL_EVALUATION_MODE,
        }


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def input_snapshot_hash(
    snapshot: TopicSnapshot, facts: Iterable[TopicSnapshotMemberFact]
) -> str:
    """Create a stable identity for the exact formal snapshot input set."""

    fact_hashes = sorted(
        (str(fact.instrument_id), str(fact.fact_hash))
        for fact in facts
    )
    return _canonical_hash(
        {
            "snapshotIdentity": snapshot.snapshot_identity,
            "snapshotLineageHash": snapshot.lineage_hash,
            "correctionSequence": snapshot.correction_sequence,
            "memberFactHashes": fact_hashes,
        }
    )


def _active_leaf_topics(session: Session, as_of_date: date) -> list[Topic]:
    """Return the versioned formal Leaf identity scope.

    Formal scope follows active effective hierarchy child identities.  Missing
    observation data never removes an active Leaf, while disabled/retired
    predecessor identities cannot be counted as their canonical replacement.
    """
    topics = list(session.scalars(select(Topic).order_by(Topic.slug)))
    child_ids = set(
        session.scalars(
            select(TopicHierarchy.child_topic_id).where(
                TopicHierarchy.valid_from <= as_of_date,
                (TopicHierarchy.valid_to.is_(None))
                | (TopicHierarchy.valid_to >= as_of_date),
            )
        )
    )
    leaves = [
        topic
        for topic in topics
        if topic.id in child_ids and topic.status not in ("DISABLED", "RETIRED")
    ]
    if len(leaves) != FORMAL_SCOPE_EXPECTED_LEAVES:
        raise ValueError(
            "FORMAL_LEAF_SCOPE_RECONCILIATION_REQUIRED:"
            f"{FORMAL_SCOPE_CONTRACT_VERSION}:"
            f"expected={FORMAL_SCOPE_EXPECTED_LEAVES}:actual={len(leaves)}"
        )
    return leaves


def _formal_snapshots_for_date(
    session: Session, evaluation_date: date
) -> dict[UUID, list[TopicSnapshot]]:
    successor = aliased(TopicSnapshot)
    rows = list(
        session.scalars(
            select(TopicSnapshot)
            .where(
                TopicSnapshot.snapshot_date == evaluation_date,
                TopicSnapshot.publication_mode == "FORMAL",
                TopicSnapshot.membership_mode == "PIT_FORMAL",
                TopicSnapshot.publication_state == "PUBLISHED",
                TopicSnapshot.finality_state == "FINAL",
                TopicSnapshot.superseded_by_snapshot_id.is_(None),
                ~exists().where(successor.supersedes_snapshot_id == TopicSnapshot.id),
            )
            .order_by(TopicSnapshot.topic_slug, TopicSnapshot.id)
        )
    )
    grouped: dict[UUID, list[TopicSnapshot]] = defaultdict(list)
    for row in rows:
        grouped[row.topic_id].append(row)
    return grouped


def _facts_for_snapshot(
    session: Session, snapshot_id: UUID
) -> list[TopicSnapshotMemberFact]:
    return list(
        session.scalars(
            select(TopicSnapshotMemberFact)
            .where(TopicSnapshotMemberFact.snapshot_id == snapshot_id)
            .order_by(
                TopicSnapshotMemberFact.membership_order,
                TopicSnapshotMemberFact.instrument_id,
            )
        )
    )


def _formal_gate(
    snapshot: TopicSnapshot,
    facts: list[TopicSnapshotMemberFact],
) -> FormalLifecycleGate:
    lineage, lineage_reason = _formal_snapshot_lineage(snapshot, facts)
    if lineage is None:
        return FormalLifecycleGate(False, lineage_reason, {}, None)

    if snapshot.data_status != "COMPLETE":
        return FormalLifecycleGate(
            False,
            f"INSUFFICIENT_FORMAL_INPUT:SNAPSHOT_DATA_STATUS_{snapshot.data_status}",
            lineage,
            input_snapshot_hash(snapshot, facts),
        )
    if snapshot.stock_count <= 0:
        return FormalLifecycleGate(
            False,
            "INSUFFICIENT_FORMAL_INPUT:NO_LEAF_MEMBERS",
            lineage,
            input_snapshot_hash(snapshot, facts),
        )
    if snapshot.observed_stock_count != snapshot.stock_count:
        return FormalLifecycleGate(
            False,
            "INSUFFICIENT_FORMAL_INPUT:OBSERVED_COUNT_MISMATCH",
            lineage,
            input_snapshot_hash(snapshot, facts),
        )
    if len(facts) != snapshot.stock_count:
        return FormalLifecycleGate(
            False,
            "INSUFFICIENT_FORMAL_INPUT:MEMBER_FACT_COUNT_MISMATCH",
            lineage,
            input_snapshot_hash(snapshot, facts),
        )
    if any(fact.fact_state != "OBSERVED" for fact in facts):
        return FormalLifecycleGate(
            False,
            "INSUFFICIENT_FORMAL_INPUT:NON_OBSERVED_MEMBER_FACT",
            lineage,
            input_snapshot_hash(snapshot, facts),
        )
    if any(
        not fact.structural_role or not fact.role_source
        for fact in facts
    ):
        return FormalLifecycleGate(
            False,
            "INSUFFICIENT_FORMAL_INPUT:STRUCTURAL_ROLE_AUTHORITY_INCOMPLETE",
            lineage,
            input_snapshot_hash(snapshot, facts),
        )
    return FormalLifecycleGate(
        True,
        None,
        lineage,
        input_snapshot_hash(snapshot, facts),
    )


def _source_reference(snapshot: TopicSnapshot) -> dict[str, Any]:
    return {
        "authority": "topicpilot.topic_snapshots",
        "sourceRunId": snapshot.source_run_id,
        "sourceArtifactId": snapshot.source_artifact_id,
        "sourceArtifactHash": snapshot.source_artifact_hash,
        "referenceRegistryVersion": snapshot.reference_registry_version,
        "mappingPolicyVersion": snapshot.mapping_policy_version,
        "relationVersion": snapshot.relation_version,
        "sessionCode": snapshot.session_code,
        "calendarCode": snapshot.calendar_code,
        "snapshotDate": snapshot.snapshot_date.isoformat(),
    }


def _state_from_row(row: TopicLifecycleFormalResult) -> dict[str, Any]:
    return {
        "final_stage": row.final_stage,
        "stage_entered_at": row.stage_entered_at,
        "stage_trading_days": row.stage_trading_days,
        "candidate_stage": row.candidate_stage,
        "candidate_streak": (row.confirmation_state or {}).get("candidateStreak", 0),
        "state_memory": row.state_memory or {},
    }


def _previous_formal_states(
    session: Session, evaluation_date: date
) -> dict[UUID, dict[str, Any]]:
    successor = aliased(TopicLifecycleFormalResult)
    rows = list(
        session.scalars(
            select(TopicLifecycleFormalResult)
            .where(
                TopicLifecycleFormalResult.evaluation_date < evaluation_date,
                TopicLifecycleFormalResult.contract_version == LIFECYCLE_CONTRACT_VERSION,
                TopicLifecycleFormalResult.publication_status
                == FORMAL_PUBLICATION_STATUS_PUBLISHED,
                TopicLifecycleFormalResult.supersession_state == "ACTIVE",
                ~exists().where(
                    successor.supersedes_decision_id == TopicLifecycleFormalResult.id
                ),
                TopicLifecycleFormalResult.final_stage.is_not(None),
            )
            .order_by(
                TopicLifecycleFormalResult.topic_id,
                TopicLifecycleFormalResult.evaluation_date,
            )
        )
    )
    states: dict[UUID, dict[str, Any]] = {}
    for row in rows:
        states[row.topic_id] = _state_from_row(row)
    return states


def _current_formal_decision_count(session: Session, dates: Iterable[date]) -> int:
    successor = aliased(TopicLifecycleFormalResult)
    values = tuple(dates)
    if not values:
        return 0
    return int(
        session.scalar(
            select(func.count())
            .select_from(TopicLifecycleFormalResult)
            .where(
                TopicLifecycleFormalResult.evaluation_date.in_(values),
                TopicLifecycleFormalResult.contract_version == LIFECYCLE_CONTRACT_VERSION,
                TopicLifecycleFormalResult.publication_status
                != FORMAL_PUBLICATION_STATUS_SUPERSEDED,
                TopicLifecycleFormalResult.supersession_state == "ACTIVE",
                ~exists().where(
                    successor.supersedes_decision_id == TopicLifecycleFormalResult.id
                ),
            )
        )
        or 0
    )


def _prior_or_bootstrap(
    previous: Mapping[UUID, dict[str, Any]], topic_id: UUID, evaluation_date: date
) -> tuple[dict[str, Any], str | None]:
    """Resolve only prior FORMAL state, or the first-eligible BASE bootstrap."""

    prior = previous.get(topic_id)
    if prior is not None:
        return prior, None
    return (
        {
            "final_stage": BASE,
            "stage_entered_at": evaluation_date,
            "stage_trading_days": 0,
            "candidate_stage": None,
            "candidate_streak": 0,
            "state_memory": {},
        },
        FORMAL_INITIALIZATION_CONTRACT_VERSION,
    )


def _unavailable_values(
    *,
    topic: Topic,
    evaluation_date: date,
    snapshot: TopicSnapshot | None,
    facts: list[TopicSnapshotMemberFact],
    gate: FormalLifecycleGate,
    reason: str,
    diagnostic_detail: str | None = None,
) -> dict[str, Any]:
    lineage = gate.lineage
    return {
        "evaluation_date": evaluation_date,
        "topic_id": topic.id,
        "topic_slug": topic.slug,
        "previous_stage": None,
        "candidate_stage": None,
        "final_stage": None,
        "stage_entered_at": None,
        "stage_trading_days": None,
        "evaluation_status": "UNAVAILABLE",
        "data_status": "INSUFFICIENT_FORMAL_HISTORY",
        "transition_decision": "HOLD_FORMAL_GATE",
        "transition_reason": reason,
        "unavailable_reason": reason,
        "publication_status": FORMAL_PUBLICATION_STATUS_UNAVAILABLE,
        "evaluation_mode": FORMAL_EVALUATION_MODE,
        "contract_version": LIFECYCLE_CONTRACT_VERSION,
        "policy_version": LifecyclePolicy().version,
        "calculation_version": LIFECYCLE_CALCULATION_VERSION,
        "leadership_evidence": None,
        "diffusion_evidence": None,
        "group_strength_evidence": None,
        "divergence_decay_evidence": None,
        "persistence_evidence": None,
        "sample_confidence": None,
        "confirmation_state": None,
        "state_memory": None,
        "main_rise_segment": None,
        "segment_entry_date": None,
        "segment_anchor_date": None,
        "days_since_meaningful_expansion": None,
        "drawdown_from_peak_pct": None,
        "average_change": None,
        "coverage_pct": None,
        "input_snapshot_id": snapshot.id if snapshot else None,
        "input_snapshot_identity": lineage.get("snapshotIdentity"),
        "input_snapshot_hash": gate.input_snapshot_hash,
        "membership_snapshot_id": lineage.get("membershipSnapshotId"),
        "membership_snapshot_hash": lineage.get("membershipSnapshotHash"),
        "relation_version": lineage.get("relationVersion"),
        "reference_registry_version": snapshot.reference_registry_version if snapshot else None,
        "mapping_policy_version": snapshot.mapping_policy_version if snapshot else None,
        "session_code": snapshot.session_code if snapshot else None,
        "calendar_code": snapshot.calendar_code if snapshot else None,
        "source_artifact_id": lineage.get("sourceArtifactId"),
        "source_artifact_hash": lineage.get("sourceArtifactHash"),
        "source_reference": _source_reference(snapshot) if snapshot else None,
        "lineage_hash": lineage.get("lineageHash"),
        "member_fact_hashes": lineage.get("memberFactHashes") or None,
        "correction_sequence": lineage.get("correctionSequence"),
        "supersession_state": "ACTIVE",
        "published_at": None,
        "as_of_at": snapshot.as_of_at if snapshot else None,
        "generated_at": datetime.now(UTC),
        "diagnostic_detail": diagnostic_detail or f"facts={len(facts)}",
    }


def _result_values(
    *,
    snapshot: TopicSnapshot,
    result: LifecycleResult,
    lineage: dict[str, Any],
    input_hash: str,
    initialization_mode: str | None = None,
) -> dict[str, Any]:
    source_reference = _source_reference(snapshot)
    source_reference["formalInitialization"] = {
        "mode": initialization_mode or "PRIOR_FORMAL_STATE",
        "version": (
            FORMAL_INITIALIZATION_CONTRACT_VERSION if initialization_mode else None
        ),
        "firstEligibleFormalDate": (
            result.trading_date.isoformat() if initialization_mode else None
        ),
        "logicalPriorState": BASE if initialization_mode else result.previous_stage,
        "logicalPriorEntryDate": (
            result.trading_date.isoformat() if initialization_mode else None
        ),
        "logicalPriorTradingDayCount": 0 if initialization_mode else None,
        "confirmationMemory": "EMPTY_DEFAULT_ZERO" if initialization_mode else None,
    }
    return {
        "evaluation_date": result.trading_date,
        "topic_id": snapshot.topic_id,
        "topic_slug": snapshot.topic_slug,
        "previous_stage": result.previous_stage,
        "candidate_stage": result.candidate_stage,
        "final_stage": result.final_stage,
        "stage_entered_at": result.stage_entered_at,
        "stage_trading_days": result.stage_trading_days,
        "evaluation_status": result.evaluation_status,
        "data_status": "FORMAL" if result.final_stage is not None else "UNAVAILABLE",
        "transition_decision": result.transition_decision,
        "transition_reason": result.transition_reason,
        "unavailable_reason": None if result.final_stage is not None else result.transition_reason,
        "publication_status": (
            FORMAL_PUBLICATION_STATUS_PUBLISHED
            if result.final_stage is not None
            else FORMAL_PUBLICATION_STATUS_UNAVAILABLE
        ),
        "evaluation_mode": FORMAL_EVALUATION_MODE,
        "contract_version": LIFECYCLE_CONTRACT_VERSION,
        "policy_version": result.policy_version,
        "calculation_version": LIFECYCLE_CALCULATION_VERSION,
        "leadership_evidence": result.evidence.leadership,
        "diffusion_evidence": result.evidence.diffusion,
        "group_strength_evidence": result.evidence.group_strength,
        "divergence_decay_evidence": result.evidence.divergence_decay,
        "persistence_evidence": result.evidence.persistence,
        "sample_confidence": result.evidence.sample_confidence,
        "confirmation_state": result.confirmation_state,
        "state_memory": result.state_memory,
        "main_rise_segment": result.main_rise_segment,
        "segment_entry_date": result.segment_entry_date,
        "segment_anchor_date": result.segment_anchor_date,
        "days_since_meaningful_expansion": result.days_since_meaningful_expansion,
        "drawdown_from_peak_pct": _decimal(result.drawdown_from_peak_pct),
        "average_change": _decimal(result.average_change),
        "coverage_pct": _decimal(result.coverage_pct, places=3),
        "input_snapshot_id": snapshot.id,
        "input_snapshot_identity": lineage["snapshotIdentity"],
        "input_snapshot_hash": input_hash,
        "membership_snapshot_id": lineage["membershipSnapshotId"],
        "membership_snapshot_hash": lineage["membershipSnapshotHash"],
        "relation_version": lineage["relationVersion"],
        "reference_registry_version": snapshot.reference_registry_version,
        "mapping_policy_version": snapshot.mapping_policy_version,
        "session_code": snapshot.session_code,
        "calendar_code": snapshot.calendar_code,
        "source_artifact_id": lineage["sourceArtifactId"],
        "source_artifact_hash": lineage["sourceArtifactHash"],
        "source_reference": source_reference,
        "lineage_hash": lineage["lineageHash"],
        "member_fact_hashes": lineage["memberFactHashes"],
        "correction_sequence": lineage["correctionSequence"],
        "supersession_state": "ACTIVE",
        "published_at": datetime.now(UTC) if result.final_stage is not None else None,
        "as_of_at": snapshot.as_of_at,
        "generated_at": datetime.now(UTC),
        "diagnostic_detail": None,
    }


def _decimal(value: float | None, *, places: int = 4) -> Decimal | None:
    if value is None:
        return None
    quantum = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)


def _serialize_result_values(values: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(values)
    result["lineage"] = {
        "inputSnapshotId": str(values["input_snapshot_id"])
        if values.get("input_snapshot_id")
        else None,
        "inputSnapshotIdentity": values.get("input_snapshot_identity"),
        "inputSnapshotHash": values.get("input_snapshot_hash"),
        "membershipSnapshotId": values.get("membership_snapshot_id"),
        "membershipSnapshotHash": values.get("membership_snapshot_hash"),
        "relationVersion": values.get("relation_version"),
        "referenceRegistryVersion": values.get("reference_registry_version"),
        "mappingPolicyVersion": values.get("mapping_policy_version"),
        "sourceArtifactId": values.get("source_artifact_id"),
        "sourceArtifactHash": values.get("source_artifact_hash"),
        "sourceReference": values.get("source_reference") or {},
        "lineageHash": values.get("lineage_hash"),
        "memberFactHashes": values.get("member_fact_hashes") or {},
        "correctionSequence": values.get("correction_sequence"),
        "supersessionState": values.get("supersession_state"),
        "decisionRevision": values.get("decision_revision", 0),
        "supersedesDecisionId": (
            str(values["supersedes_decision_id"])
            if values.get("supersedes_decision_id")
            else None
        ),
        "supersessionReason": values.get("supersession_reason"),
    }
    return result


def _topic_result_payload(
    values: Mapping[str, Any], *, publication_status: str | None = None
) -> dict[str, Any]:
    payload = {
        "topicId": str(values["topic_id"]),
        "topicSlug": values["topic_slug"],
        "evaluationDate": values["evaluation_date"],
        "previousStage": values.get("previous_stage"),
        "candidateStage": values.get("candidate_stage"),
        "finalStage": values.get("final_stage"),
        "stageEnteredAt": values.get("stage_entered_at"),
        "stageTradingDays": values.get("stage_trading_days"),
        "evaluationStatus": values["evaluation_status"],
        "dataStatus": values["data_status"],
        "transitionDecision": values["transition_decision"],
        "transitionReason": values["transition_reason"],
        "unavailableReason": values.get("unavailable_reason"),
        "publicationStatus": publication_status or values["publication_status"],
        "contractVersion": values["contract_version"],
        "policyVersion": values["policy_version"],
        "calculationVersion": values["calculation_version"],
        "evaluationMode": values["evaluation_mode"],
        "asOfAt": values.get("as_of_at"),
        "lineage": _serialize_result_values(values)["lineage"],
    }
    for key in (
        "main_rise_segment",
        "segment_entry_date",
        "segment_anchor_date",
        "days_since_meaningful_expansion",
        "drawdown_from_peak_pct",
        "average_change",
        "coverage_pct",
        "leadership_evidence",
        "diffusion_evidence",
        "group_strength_evidence",
        "divergence_decay_evidence",
        "persistence_evidence",
        "sample_confidence",
        "confirmation_state",
        "state_memory",
    ):
        payload[key] = values.get(key)
    return payload


class FormalLifecyclePublisher:
    """Evaluate and persist formal Lifecycle V1.3 rows from A9 authority."""

    def __init__(
        self,
        session: Session,
        *,
        policy: LifecyclePolicy | None = None,
        writer_context: Mapping[str, str] | None = None,
    ) -> None:
        self.session = session
        self.policy = policy or LifecyclePolicy()
        self.writer_context = dict(writer_context or {})

    def _attach_writer_context(self, values: dict[str, Any]) -> dict[str, Any]:
        if not self.writer_context:
            return values
        values["source_reference"] = {
            **(values.get("source_reference") or {}),
            "publicationWriter": dict(self.writer_context),
        }
        return values

    def run_once(
        self,
        *,
        evaluation_date: date,
        eligible_topic_ids: Collection[UUID] | None = None,
        persist: bool = True,
    ) -> FormalLifecycleRun:
        if evaluation_date < A9_FORMAL_TOPIC_SNAPSHOT_START:
            raise ValueError(
                "FORMAL_LIFECYCLE_DATE_BEFORE_A9_AUTHORITY:"
                f"{A9_FORMAL_TOPIC_SNAPSHOT_START.isoformat()}"
            )
        leaves = _active_leaf_topics(self.session, evaluation_date)
        if eligible_topic_ids is not None:
            allowed = set(eligible_topic_ids)
            leaves = [topic for topic in leaves if topic.id in allowed]
        snapshots = _formal_snapshots_for_date(self.session, evaluation_date)
        evidence = read_price_evidence(self.session, evaluation_date)
        previous = _previous_formal_states(self.session, evaluation_date)
        reason_breakdown: Counter[str] = Counter()
        topic_results: list[dict[str, Any]] = []
        values_to_persist: list[dict[str, Any]] = []
        formal_rows = 0
        unavailable_rows = 0
        backward_transitions = 0
        new_published = 0
        new_unavailable = 0
        superseded_decisions = 0
        idempotent_rows = 0

        for topic in leaves:
            candidates = snapshots.get(topic.id, [])
            snapshot = candidates[0] if len(candidates) == 1 else None
            facts = _facts_for_snapshot(self.session, snapshot.id) if snapshot else []
            if not candidates:
                gate = FormalLifecycleGate(
                    False, "FORMAL_TOPIC_SNAPSHOT_NOT_PUBLISHED", {}, None
                )
            elif len(candidates) > 1:
                gate = FormalLifecycleGate(False, "AMBIGUOUS_FORMAL_SNAPSHOT", {}, None)
            else:
                gate = _formal_gate(snapshot, facts)

            reason = gate.reason
            if gate.passed and snapshot is not None:
                observations, observation_reason = _formal_observations(
                    snapshot,
                    facts,
                    evidence,
                    None,
                    evaluation_date,
                )
                if observation_reason is not None or observations is None:
                    reason = observation_reason or "FORMAL_OBSERVATIONS_UNAVAILABLE"
                else:
                    prior, initialization_mode = _prior_or_bootstrap(
                        previous, topic.id, evaluation_date
                    )
                    result = evaluate_formal_lifecycle(
                        LifecycleInput(
                            str(topic.id),
                            evaluation_date,
                            int(snapshot.stock_count),
                            observations,
                            prior["final_stage"],
                            prior["stage_entered_at"],
                            prior["stage_trading_days"],
                            prior["candidate_stage"],
                            int(prior["candidate_streak"] or 0),
                            prior["state_memory"],
                        ),
                        self.policy,
                    )
                    lineage = gate.lineage
                    input_hash = gate.input_snapshot_hash or input_snapshot_hash(snapshot, facts)
                    values = self._attach_writer_context(
                        _result_values(
                            snapshot=snapshot,
                            result=result,
                            lineage=lineage,
                            input_hash=input_hash,
                            initialization_mode=initialization_mode,
                        )
                    )
                    values_to_persist.append(values)
                    payload = _topic_result_payload(values)
                    topic_results.append(payload)
                    if result.final_stage is not None:
                        formal_rows += 1
                    else:
                        unavailable_rows += 1
                        reason_breakdown[result.transition_reason] += 1
                    if result.transition_reason == "ILLEGAL_BACKWARD_TRANSITION_STATE_PERSISTED":
                        backward_transitions += 1
                    previous[topic.id] = {
                        "final_stage": result.final_stage,
                        "stage_entered_at": result.stage_entered_at,
                        "stage_trading_days": result.stage_trading_days,
                        "candidate_stage": result.candidate_stage,
                        "candidate_streak": result.confirmation_state.get("candidateStreak", 0),
                        "state_memory": result.state_memory,
                    }
                    continue

            unavailable_rows += 1
            reason_value = reason or "FORMAL_LIFECYCLE_GATE_FAILED"
            reason_breakdown[reason_value] += 1
            values = self._attach_writer_context(_unavailable_values(
                topic=topic,
                evaluation_date=evaluation_date,
                snapshot=snapshot,
                facts=facts,
                gate=gate,
                reason=reason_value,
            ))
            values_to_persist.append(values)
            topic_results.append(_topic_result_payload(values))

        if persist:
            for values in values_to_persist:
                persistence_result = self._persist(values)
                if persistence_result == "NEW_PUBLISHED":
                    new_published += 1
                elif persistence_result == "NEW_UNAVAILABLE":
                    new_unavailable += 1
                elif persistence_result == "SUPERSEDED":
                    superseded_decisions += 1
                elif persistence_result == "IDEMPOTENT":
                    idempotent_rows += 1
            self.session.commit()

        return FormalLifecycleRun(
            evaluation_date,
            "SUCCESS" if unavailable_rows == 0 else "FAIL_CLOSED",
            len(leaves),
            formal_rows,
            unavailable_rows,
            len(values_to_persist) if persist else 0,
            dict(sorted(reason_breakdown.items())),
            backward_transitions,
            topic_results,
            new_published,
            new_unavailable,
            superseded_decisions,
            idempotent_rows,
        )

    def run_replay(
        self,
        *,
        persist: bool = True,
        from_date: date = A9_FORMAL_TOPIC_SNAPSHOT_START,
        to_date: date | None = None,
    ) -> dict[str, Any]:
        successor = aliased(TopicSnapshot)
        dates = list(
            self.session.scalars(
                select(TopicSnapshot.snapshot_date)
                .where(
                    TopicSnapshot.snapshot_date >= from_date,
                    TopicSnapshot.publication_mode == "FORMAL",
                    TopicSnapshot.membership_mode == "PIT_FORMAL",
                    TopicSnapshot.publication_state == "PUBLISHED",
                    TopicSnapshot.finality_state == "FINAL",
                    TopicSnapshot.superseded_by_snapshot_id.is_(None),
                    ~exists().where(successor.supersedes_snapshot_id == TopicSnapshot.id),
                )
                .distinct()
                .order_by(TopicSnapshot.snapshot_date)
            )
        )
        if to_date is not None:
            dates = [item for item in dates if item <= to_date]
        original_decisions = _current_formal_decision_count(self.session, dates)
        runs = [self.run_once(evaluation_date=item, persist=persist) for item in dates]
        reason_breakdown: Counter[str] = Counter()
        for run in runs:
            reason_breakdown.update(run.reason_breakdown)
        return {
            "status": "SUCCESS" if runs and all(run.status == "SUCCESS" for run in runs) else (
                "FAIL_CLOSED" if runs else "INSUFFICIENT_FORMAL_HISTORY"
            ),
            "dates": [run.as_dict() for run in runs],
            "formalDates": [item.isoformat() for item in dates],
            "formalLifecycleTradingSessions": len(dates),
            "expectedLeafDateRows": sum(run.expected_leaf_date_rows for run in runs),
            "formalLifecycleRows": sum(run.formal_rows for run in runs),
            "unavailableRows": sum(run.unavailable_rows for run in runs),
            "reasonBreakdown": dict(sorted(reason_breakdown.items())),
            "backwardTransitions": sum(run.backward_transitions for run in runs),
            "ORIGINAL_DECISIONS": original_decisions,
            "NEW_PUBLISHED": sum(run.new_published for run in runs),
            "NEW_UNAVAILABLE": sum(run.new_unavailable for run in runs),
            "SUPERSEDED_DECISIONS": sum(run.superseded_decisions for run in runs),
            "IDEMPOTENT": sum(run.idempotent_rows for run in runs),
            "contractVersion": LIFECYCLE_CONTRACT_VERSION,
            "policyVersion": self.policy.version,
            "calculationVersion": LIFECYCLE_CALCULATION_VERSION,
            "evaluationMode": FORMAL_EVALUATION_MODE,
            "initializationContractVersion": FORMAL_INITIALIZATION_CONTRACT_VERSION,
            "formalScopeContractVersion": FORMAL_SCOPE_CONTRACT_VERSION,
            "formalScopeLeaves": FORMAL_SCOPE_EXPECTED_LEAVES,
        }

    def _persist(self, values: dict[str, Any]) -> str:
        successor = aliased(TopicLifecycleFormalResult)
        existing = self.session.scalar(
            select(TopicLifecycleFormalResult).where(
                TopicLifecycleFormalResult.topic_id == values["topic_id"],
                TopicLifecycleFormalResult.evaluation_date == values["evaluation_date"],
                TopicLifecycleFormalResult.contract_version == LIFECYCLE_CONTRACT_VERSION,
                TopicLifecycleFormalResult.publication_status
                != FORMAL_PUBLICATION_STATUS_SUPERSEDED,
                TopicLifecycleFormalResult.supersession_state == "ACTIVE",
                ~exists().where(
                    successor.supersedes_decision_id == TopicLifecycleFormalResult.id
                ),
            )
            .with_for_update()
        )
        if existing is None:
            values["decision_revision"] = 0
            self.session.add(TopicLifecycleFormalResult(**values))
            return (
                "NEW_PUBLISHED"
                if values["publication_status"] == FORMAL_PUBLICATION_STATUS_PUBLISHED
                else "NEW_UNAVAILABLE"
            )

        immutable_fields = (
            "final_stage",
            "candidate_stage",
            "transition_reason",
            "publication_status",
            "input_snapshot_hash",
            "lineage_hash",
        )
        if all(getattr(existing, field) == values[field] for field in immutable_fields):
            return "IDEMPOTENT"
        values["decision_revision"] = getattr(existing, "decision_revision", 0) + 1
        values["supersedes_decision_id"] = existing.id
        values["supersession_reason"] = FORMAL_CORRECTION_SUPERSESSION_REASON
        self.session.add(TopicLifecycleFormalResult(**values))
        return "SUPERSEDED"


def read_formal_lifecycle(session: Session, topic_id: UUID) -> dict[str, Any] | None:
    """Read the active formal result; raise if the additive table is absent."""

    successor = aliased(TopicLifecycleFormalResult)
    rows = list(
        session.scalars(
            select(TopicLifecycleFormalResult)
            .where(
                TopicLifecycleFormalResult.topic_id == topic_id,
                TopicLifecycleFormalResult.contract_version == LIFECYCLE_CONTRACT_VERSION,
                TopicLifecycleFormalResult.publication_status
                != FORMAL_PUBLICATION_STATUS_SUPERSEDED,
                TopicLifecycleFormalResult.supersession_state == "ACTIVE",
                ~exists().where(
                    successor.supersedes_decision_id == TopicLifecycleFormalResult.id
                ),
            )
            .order_by(TopicLifecycleFormalResult.evaluation_date)
        )
    )
    if not rows:
        return None
    current = rows[-1]
    segments: list[dict[str, Any]] = []
    for row in rows:
        if row.final_stage is None:
            continue
        if not segments or segments[-1]["stage"] != row.final_stage:
            if segments:
                segments[-1]["exitedAt"] = row.evaluation_date
                segments[-1]["current"] = False
            segments.append(
                {
                    "stage": row.final_stage,
                    "enteredAt": row.stage_entered_at,
                    "exitedAt": None,
                    "tradingDays": row.stage_trading_days,
                    "current": True,
                }
            )
        else:
            segments[-1]["tradingDays"] = row.stage_trading_days
    latest_evidence = {
        "leadership": current.leadership_evidence or {},
        "diffusion": current.diffusion_evidence or {},
        "groupStrength": current.group_strength_evidence or {},
        "divergenceDecay": current.divergence_decay_evidence or {},
        "persistence": current.persistence_evidence or {},
    }
    formal_available = (
        current.publication_status == FORMAL_PUBLICATION_STATUS_PUBLISHED
        and current.final_stage is not None
    )
    return {
        "currentStage": current.final_stage,
        "currentStageEnteredAt": current.stage_entered_at,
        "currentStageTradingDays": current.stage_trading_days,
        "mainRiseSegment": current.main_rise_segment,
        "segmentEntryDate": current.segment_entry_date,
        "segmentAnchorDate": current.segment_anchor_date,
        "daysSinceMeaningfulExpansion": current.days_since_meaningful_expansion,
        "drawdownFromPeakPct": (
            float(current.drawdown_from_peak_pct)
            if current.drawdown_from_peak_pct is not None
            else None
        ),
        "history": segments,
        "dataStatus": "FORMAL_AVAILABLE" if formal_available else "NOT_AVAILABLE",
        "evaluationDate": current.evaluation_date,
        "previousStage": current.previous_stage,
        "candidateStage": current.candidate_stage,
        "transitionDecision": current.transition_decision,
        "transitionReason": current.transition_reason,
        "publicationStatus": current.publication_status,
        "contractVersion": current.contract_version,
        "calculationVersion": current.calculation_version,
        "evaluationMode": current.evaluation_mode,
        "asOfAt": current.as_of_at,
        "policyVersion": current.policy_version,
        "evidence": latest_evidence,
        "confidence": current.sample_confidence or {},
        "lineage": {
            "inputSnapshotId": str(current.input_snapshot_id)
            if current.input_snapshot_id
            else None,
            "inputSnapshotIdentity": current.input_snapshot_identity,
            "inputSnapshotHash": current.input_snapshot_hash,
            "membershipSnapshotId": current.membership_snapshot_id,
            "membershipSnapshotHash": current.membership_snapshot_hash,
            "relationVersion": current.relation_version,
            "referenceRegistryVersion": current.reference_registry_version,
            "mappingPolicyVersion": current.mapping_policy_version,
            "sessionCode": current.session_code,
            "calendarCode": current.calendar_code,
            "sourceArtifactId": current.source_artifact_id,
            "sourceArtifactHash": current.source_artifact_hash,
            "sourceReference": current.source_reference or {},
            "lineageHash": current.lineage_hash,
            "memberFactHashes": current.member_fact_hashes or {},
            "correctionSequence": current.correction_sequence,
            "supersessionState": current.supersession_state,
            "decisionRevision": getattr(current, "decision_revision", 0),
            "supersedesDecisionId": (
                str(getattr(current, "supersedes_decision_id", None))
                if getattr(current, "supersedes_decision_id", None)
                else None
            ),
            "supersessionReason": getattr(current, "supersession_reason", None),
        },
    }


def formal_correction_dates(
    session: Session,
    *,
    from_date: date = A9_FORMAL_TOPIC_SNAPSHOT_START,
    to_date: date | None = None,
) -> tuple[date, ...]:
    """Return the current formal A9 dates eligible for correction planning."""

    successor = aliased(TopicSnapshot)
    statement = (
        select(TopicSnapshot.snapshot_date)
        .where(
            TopicSnapshot.snapshot_date >= from_date,
            TopicSnapshot.publication_mode == "FORMAL",
            TopicSnapshot.membership_mode == "PIT_FORMAL",
            TopicSnapshot.publication_state == "PUBLISHED",
            TopicSnapshot.finality_state == "FINAL",
            TopicSnapshot.superseded_by_snapshot_id.is_(None),
            ~exists().where(successor.supersedes_snapshot_id == TopicSnapshot.id),
        )
        .distinct()
        .order_by(TopicSnapshot.snapshot_date)
    )
    if to_date is not None:
        statement = statement.where(TopicSnapshot.snapshot_date <= to_date)
    return tuple(session.scalars(statement))


__all__ = [
    "A9_FORMAL_TOPIC_SNAPSHOT_START",
    "FORMAL_CORRECTION_SUPERSESSION_REASON",
    "FORMAL_PUBLICATION_STATUS_PUBLISHED",
    "FORMAL_PUBLICATION_STATUS_SUPERSEDED",
    "FORMAL_PUBLICATION_STATUS_UNAVAILABLE",
    "FormalLifecycleGate",
    "FormalLifecyclePublisher",
    "FormalLifecycleRun",
    "formal_correction_dates",
    "input_snapshot_hash",
    "read_formal_lifecycle",
]
