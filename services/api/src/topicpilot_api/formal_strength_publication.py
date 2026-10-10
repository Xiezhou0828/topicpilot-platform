"""Formal post-close Topic Strength publication and audit readback.

The existing ``topic_score_formal_results`` table is the append-only Score/
Grade envelope created by migration 0045.  This module supplies the missing
writer for the Owner-seeded V0 Strength views.  Absolute and Relative are
stored together as independent components; the persisted ``score``/``grade``
columns are the Absolute view because Absolute is the formal daily-grade
authority.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from topicpilot_api.formal_eligibility import Dimension
from topicpilot_api.orm import (
    Instrument,
    Market,
    Topic,
    TopicHierarchy,
    TopicScoreFormalResult,
    TopicSnapshot,
    TopicSnapshotMemberFact,
)
from topicpilot_api.previous_close_authority import (
    AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE,
)
from topicpilot_api.release_provenance import runtime_git_sha
from topicpilot_api.topic_engine.owner_seeded_v0_policy import (
    CORE,
    DEFAULT_POLICY,
    POLICY_ID,
    POLICY_VERSION,
    RELATED,
    REPRESENTATIVE,
    MemberObservation,
    StrengthViewResult,
    evaluate_strength_view,
)
from topicpilot_api.topic_engine.score_projection import (
    ScoreProjectionError,
    resolve_score_projection,
)

FORMAL_STRENGTH_CONTRACT_VERSION = "topic-strength-lifecycle.formal.v1"
FORMAL_STRENGTH_CALCULATION_VERSION = "topic-strength-lifecycle.owner-seeded-v0.formal.v1"
FORMAL_PUBLICATION_MODE = "FORMAL"
FORMAL_PUBLICATION_STATUS_PUBLISHED = "PUBLISHED"
FORMAL_PUBLICATION_STATUS_UNAVAILABLE = "UNAVAILABLE"
FORMAL_PUBLICATION_STATUS_SUPERSEDED = "SUPERSEDED"
FORMAL_STRENGTH_START = date(2026, 8, 24)


@dataclass(frozen=True)
class MarketContext:
    """Market regime evidence used only by Lifecycle confirmation."""

    status: str
    tai_ex_return_pct: float | None
    tpex_return_pct: float | None
    benchmark_ready: bool
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "taiexReturnPct": self.tai_ex_return_pct,
            "tpexReturnPct": self.tpex_return_pct,
            "benchmarkReady": self.benchmark_ready,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class FormalStrengthGate:
    passed: bool
    reason: str | None
    input_snapshot_hash: str | None


@dataclass(frozen=True)
class FormalStrengthRun:
    evaluation_date: date
    status: str
    expected_topic_rows: int
    published_rows: int
    unavailable_rows: int
    persisted_rows: int
    reason_breakdown: dict[str, int]
    topic_results: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "evaluationDate": self.evaluation_date.isoformat(),
            "status": self.status,
            "expectedTopicRows": self.expected_topic_rows,
            "publishedRows": self.published_rows,
            "unavailableRows": self.unavailable_rows,
            "persistedRows": self.persisted_rows,
            "reasonBreakdown": self.reason_breakdown,
            "topicResults": self.topic_results,
            "contractVersion": FORMAL_STRENGTH_CONTRACT_VERSION,
            "calculationVersion": FORMAL_STRENGTH_CALCULATION_VERSION,
            "policyId": POLICY_ID,
            "policyVersion": POLICY_VERSION,
        }


def _canonical_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _value(item: Any, *names: str) -> Any:
    for name in names:
        if isinstance(item, Mapping) and name in item:
            return item[name]
        if hasattr(item, name):
            return getattr(item, name)
    return None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and abs(result) != float("inf") else None


def build_market_context(
    market_index_facts: Iterable[Any],
    evaluation_date: date,
) -> MarketContext:
    """Validate close-date benchmark facts without substituting neutral zero."""

    values: dict[str, float | None] = {"TWSE": None, "TPEX": None}
    for fact in market_index_facts:
        market = str(_value(fact, "market") or "").upper()
        trading_date = _value(fact, "trading_date", "tradingDate")
        status = str(_value(fact, "data_status", "dataStatus", "status") or "").upper()
        change = _float_or_none(_value(fact, "change_pct", "changePct"))
        if isinstance(trading_date, str):
            try:
                trading_date = date.fromisoformat(trading_date[:10])
            except ValueError:
                trading_date = None
        if trading_date != evaluation_date or status not in {"AVAILABLE", "PUBLISHED", "FORMAL"}:
            continue
        if change is None:
            continue
        if market == "TPE" or "TAIEX" in str(_value(fact, "index_identity", "indexCode") or ""):
            values["TWSE"] = change
        elif market == "TWO" or "TPEX" in str(_value(fact, "index_identity", "indexCode") or ""):
            values["TPEX"] = change
    available = [value for value in values.values() if value is not None]
    if not available:
        return MarketContext("UNAVAILABLE", None, None, False, "BENCHMARK_FACTS_MISSING")
    if len(available) == 1:
        return MarketContext(
            "ELEVATED_STRESS" if available[0] <= -1.5 else "NORMAL",
            values["TWSE"],
            values["TPEX"],
            False,
            "ONE_BENCHMARK_FACT_MISSING",
        )
    worst = min(available)
    status = (
        "SYSTEMIC_SHOCK"
        if max(available) <= -2.5 or worst <= -5.0
        else ("ELEVATED_STRESS" if worst <= -1.5 or max(available) < 0 else "NORMAL")
    )
    return MarketContext(status, values["TWSE"], values["TPEX"], True)


def build_structural_derivatives(
    current: Mapping[str, float | None],
    history: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Build auditable level/trajectory/baseline structural evidence.

    The dimensions are deliberately normalized within a Topic.  They are
    evidence for Lifecycle interpretation, not a public score or an extra
    Lifecycle state.
    """

    keys = (
        "absoluteStrength",
        "relativeStrength",
        "coreParticipation",
        "breadth",
        "relatedDiffusion",
        "leadershipConcentration",
    )
    dimensions: dict[str, Any] = {}
    improving = weakening = 0
    for key in keys:
        value = _float_or_none(current.get(key))
        prior_values = [
            item.get(key) for item in history[-5:] if _float_or_none(item.get(key)) is not None
        ]
        prior = [float(item) for item in prior_values]
        baseline = sum(prior) / len(prior) if prior else None
        trajectory = None if baseline is None or value is None else value - baseline
        threshold = 3.0 if key.endswith("Strength") else 0.05
        if key == "leadershipConcentration":
            threshold = 0.05
            state = (
                "IMPROVING"
                if trajectory is not None and trajectory <= -threshold
                else (
                    "WEAKENING" if trajectory is not None and trajectory >= threshold else "STABLE"
                )
            )
        else:
            state = (
                "IMPROVING"
                if trajectory is not None and trajectory >= threshold
                else (
                    "WEAKENING" if trajectory is not None and trajectory <= -threshold else "STABLE"
                )
            )
        improving += state == "IMPROVING"
        weakening += state == "WEAKENING"
        dimensions[key] = {
            "currentLevel": value,
            "shortTrajectory": trajectory,
            "baseline": baseline,
            "status": state,
            "historyObservations": len(prior),
        }
    healthy = (current.get("absoluteStrength") or 0.0) >= 62.0
    healthy_relative = (current.get("relativeStrength") or 0.0) >= 55.0
    saturation_dims = sum(
        dimensions[key]["status"] in {"STABLE", "WEAKENING"}
        for key in ("relativeStrength", "coreParticipation", "breadth", "relatedDiffusion")
    )
    if weakening >= 3 or (
        dimensions["absoluteStrength"]["status"] == "WEAKENING"
        and dimensions["relativeStrength"]["status"] == "WEAKENING"
        and weakening >= 2
    ):
        interpretation = "DETERIORATING"
    elif healthy and healthy_relative and saturation_dims >= 3 and weakening <= 2:
        interpretation = "SATURATING"
    elif improving >= 3:
        interpretation = "EXPANDING"
    else:
        interpretation = "STABLE"
    return {
        "status": "AVAILABLE" if current.get("absoluteStrength") is not None else "UNAVAILABLE",
        "interpretation": interpretation,
        "dimensions": dimensions,
        "improvingDimensions": improving,
        "weakeningDimensions": weakening,
        "doubleCountingGuard": "CORE_PARTICIPATION_BREADTH_RELATED_REMAIN_SEPARATE",
    }


def _active_leaf_topics(session: Session, as_of_date: date) -> list[Topic]:
    topics = list(session.scalars(select(Topic).order_by(Topic.slug)))
    child_ids = set(
        session.scalars(
            select(TopicHierarchy.child_topic_id).where(
                TopicHierarchy.valid_from <= as_of_date,
                (TopicHierarchy.valid_to.is_(None)) | (TopicHierarchy.valid_to >= as_of_date),
            )
        )
    )
    return [
        topic
        for topic in topics
        if topic.id in child_ids
        and topic.status not in {"DISABLED", "RETIRED"}
        and (topic.valid_from is None or topic.valid_from <= as_of_date)
        and (topic.valid_to is None or topic.valid_to >= as_of_date)
    ]


def _active_snapshots(session: Session, evaluation_date: date) -> dict[UUID, list[TopicSnapshot]]:
    successor = aliased(TopicSnapshot)
    rows = list(
        session.scalars(
            select(TopicSnapshot).where(
                TopicSnapshot.snapshot_date == evaluation_date,
                TopicSnapshot.publication_mode == "FORMAL",
                TopicSnapshot.membership_mode == "PIT_FORMAL",
                TopicSnapshot.publication_state == "PUBLISHED",
                TopicSnapshot.finality_state == "FINAL",
                ~select(successor.id)
                .where(successor.supersedes_snapshot_id == TopicSnapshot.id)
                .exists(),
            )
        )
    )
    grouped: dict[UUID, list[TopicSnapshot]] = defaultdict(list)
    for row in rows:
        grouped[row.topic_id].append(row)
    return grouped


def _facts(session: Session, snapshot_id: UUID) -> list[TopicSnapshotMemberFact]:
    return list(
        session.scalars(
            select(TopicSnapshotMemberFact)
            .where(TopicSnapshotMemberFact.snapshot_id == snapshot_id)
            .order_by(
                TopicSnapshotMemberFact.membership_order, TopicSnapshotMemberFact.instrument_id
            )
        )
    )


def _input_hash(snapshot: TopicSnapshot, facts: Iterable[TopicSnapshotMemberFact]) -> str:
    return _canonical_hash(
        {
            "snapshotIdentity": snapshot.snapshot_identity,
            "snapshotLineageHash": snapshot.lineage_hash,
            "correctionSequence": snapshot.correction_sequence,
            "memberFactHashes": sorted((str(fact.instrument_id), fact.fact_hash) for fact in facts),
        }
    )


def is_authorized_return_unavailable_fact(fact: Any) -> bool:
    """Return whether one formal member is valid but unavailable for returns."""

    if _value(fact, "fact_state") != "NO_TRADE":
        return False
    eligibility = (_value(fact, "raw_fact_payload") or {}).get("dimensionEligibility") or {}
    daily_return = eligibility.get(Dimension.DAILY_RETURN.value) or {}
    return (
        daily_return.get("status") == "ACCOUNTED_UNAVAILABLE"
        and daily_return.get("reasonCode") == AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE
    )


def _gate(
    snapshot: TopicSnapshot | None, facts: list[TopicSnapshotMemberFact]
) -> FormalStrengthGate:
    if snapshot is None:
        return FormalStrengthGate(False, "FORMAL_TOPIC_SNAPSHOT_NOT_PUBLISHED", None)
    input_hash = _input_hash(snapshot, facts)
    required = (
        snapshot.snapshot_identity,
        snapshot.membership_snapshot_id,
        snapshot.membership_snapshot_hash,
        snapshot.relation_version,
        snapshot.source_artifact_hash,
        snapshot.lineage_hash,
    )
    if any(value is None for value in required):
        return FormalStrengthGate(False, "MISSING_FORMAL_SNAPSHOT_LINEAGE", input_hash)
    if snapshot.data_status != "COMPLETE":
        return FormalStrengthGate(False, f"SNAPSHOT_DATA_STATUS_{snapshot.data_status}", input_hash)
    if snapshot.stock_count <= 0 or len(facts) != snapshot.stock_count:
        return FormalStrengthGate(False, "FORMAL_MEMBER_COUNT_MISMATCH", input_hash)
    if any(
        fact.fact_state != "OBSERVED" and not is_authorized_return_unavailable_fact(fact)
        for fact in facts
    ):
        return FormalStrengthGate(False, "FORMAL_MEMBER_OBSERVATION_UNAVAILABLE", input_hash)
    for fact in facts:
        if fact.change_pct is not None:
            continue
        eligibility = (fact.raw_fact_payload or {}).get("dimensionEligibility") or {}
        daily_return = eligibility.get(Dimension.DAILY_RETURN.value) or {}
        if not (
            daily_return.get("status") == "ACCOUNTED_UNAVAILABLE"
            and daily_return.get("reasonCode")
            == AUTHORIZED_CORPORATE_ACTION_COMPARATOR_UNAVAILABLE
        ):
            return FormalStrengthGate(False, "FORMAL_MEMBER_OBSERVATION_UNAVAILABLE", input_hash)
    if any(not fact.structural_role or not fact.role_source for fact in facts):
        return FormalStrengthGate(False, "STRUCTURAL_ROLE_AUTHORITY_INCOMPLETE", input_hash)
    return FormalStrengthGate(True, None, input_hash)


def _return_eligible_facts(
    facts: Iterable[TopicSnapshotMemberFact],
) -> tuple[TopicSnapshotMemberFact, ...]:
    """Project formal members into the daily-return calculation dimension."""

    return tuple(
        fact
        for fact in facts
        if (
            ((fact.raw_fact_payload or {}).get("dimensionEligibility") or {})
            .get(Dimension.DAILY_RETURN.value, {})
            .get("status")
            == "READY"
        )
    )


def _market_map(session: Session, facts: Iterable[TopicSnapshotMemberFact]) -> dict[UUID, str]:
    ids = tuple(fact.instrument_id for fact in facts)
    if not ids:
        return {}
    rows = session.execute(
        select(Instrument.id, Market.code)
        .join(Market, Market.id == Instrument.market_id)
        .where(Instrument.id.in_(ids))
    ).all()
    return {row[0]: str(row[1]) for row in rows}


def _market_code(value: str) -> str:
    normalized = value.upper()
    if normalized == "TPE":
        return "TWSE"
    if normalized == "TWO":
        return "TPEX"
    return normalized


def _topic_history(session: Session, topic_id: UUID, evaluation_date: date) -> list[dict[str, Any]]:
    successor = aliased(TopicScoreFormalResult)
    rows = list(
        session.scalars(
            select(TopicScoreFormalResult)
            .where(
                TopicScoreFormalResult.topic_id == topic_id,
                TopicScoreFormalResult.evaluation_date < evaluation_date,
                TopicScoreFormalResult.publication_status == FORMAL_PUBLICATION_STATUS_PUBLISHED,
                ~select(successor.id)
                .where(successor.supersedes_decision_id == TopicScoreFormalResult.id)
                .exists(),
            )
            .order_by(TopicScoreFormalResult.evaluation_date)
        )
    )
    result: list[dict[str, Any]] = []
    for row in rows:
        components = row.components or {}
        derivatives = components.get("derivatives") or {}
        values = {
            key: derivatives.get("dimensions", {}).get(key, {}).get("currentLevel")
            for key in (
                "absoluteStrength",
                "relativeStrength",
                "coreParticipation",
                "breadth",
                "relatedDiffusion",
                "leadershipConcentration",
            )
        }
        result.append(values)
    return result


def _decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _view_payload(result: StrengthViewResult) -> dict[str, Any]:
    return result.as_dict()


def _state_metrics(
    members: tuple[MemberObservation, ...], absolute: StrengthViewResult
) -> dict[str, float | None]:
    def values(role: str) -> list[float]:
        return [
            float(member.absolute_return_pct)
            for member in members
            if member.role == role and member.absolute_return_pct is not None
        ]

    all_values = values(REPRESENTATIVE) + values(CORE) + values(RELATED)
    core = values(CORE)
    related = values(RELATED)
    concentration_items = [
        abs(float(member.absolute_return_pct or 0.0)) * float(member.score_importance or 1.0)
        for member in members
        if member.role in {REPRESENTATIVE, CORE} and member.absolute_return_pct is not None
    ]
    total_contribution = sum(concentration_items)
    concentration = max(concentration_items) / total_contribution if total_contribution else None
    return {
        "absoluteStrength": absolute.strength,
        "relativeStrength": None,
        "coreParticipation": sum(item > 0 for item in core) / len(core) if core else None,
        "breadth": sum(item > 0 for item in all_values) / len(all_values) if all_values else None,
        "relatedDiffusion": sum(item > 0 for item in related) / len(related) if related else None,
        "leadershipConcentration": concentration,
    }


class FormalStrengthPublisher:
    """Materialize one formal Strength result per active formal Topic leaf."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def run_once(
        self,
        *,
        evaluation_date: date,
        eligible_topic_ids: Collection[UUID] | None = None,
        market_index_facts: Iterable[Any] = (),
        persist: bool = True,
    ) -> FormalStrengthRun:
        if evaluation_date < FORMAL_STRENGTH_START:
            raise ValueError(
                f"FORMAL_STRENGTH_DATE_BEFORE_AUTHORITY:{FORMAL_STRENGTH_START.isoformat()}"
            )
        leaves = _active_leaf_topics(self.session, evaluation_date)
        if eligible_topic_ids is not None:
            allowed = set(eligible_topic_ids)
            leaves = [topic for topic in leaves if topic.id in allowed]
        snapshots = _active_snapshots(self.session, evaluation_date)
        context = build_market_context(market_index_facts, evaluation_date)
        reasons: Counter[str] = Counter()
        payloads: list[dict[str, Any]] = []
        topic_results: list[dict[str, Any]] = []
        published = unavailable = 0
        for topic in leaves:
            candidates = snapshots.get(topic.id, [])
            snapshot = candidates[0] if len(candidates) == 1 else None
            facts = _facts(self.session, snapshot.id) if snapshot else []
            gate = _gate(snapshot, facts)
            if len(candidates) > 1:
                gate = FormalStrengthGate(False, "AMBIGUOUS_FORMAL_SNAPSHOT", None)
            values: dict[str, Any]
            if not gate.passed or snapshot is None:
                reason = gate.reason or "FORMAL_STRENGTH_GATE_FAILED"
                reasons[reason] += 1
                unavailable += 1
                values = self._unavailable_values(topic, evaluation_date, snapshot, gate, reason)
            else:
                try:
                    values = self._evaluate_topic(
                        topic,
                        snapshot,
                        facts,
                        evaluation_date,
                        context,
                        _topic_history(self.session, topic.id, evaluation_date),
                    )
                    published += 1
                except (ScoreProjectionError, ValueError, KeyError) as exc:
                    reason = f"FORMAL_STRENGTH_UNAVAILABLE:{type(exc).__name__}:{str(exc)[:160]}"
                    reasons[reason] += 1
                    unavailable += 1
                    values = self._unavailable_values(
                        topic, evaluation_date, snapshot, gate, reason
                    )
            payloads.append(values)
            topic_results.append(self._payload(values))
        if persist:
            for values in payloads:
                self._persist(values)
            self.session.commit()
        return FormalStrengthRun(
            evaluation_date,
            "SUCCESS" if unavailable == 0 else "FAIL_CLOSED",
            len(leaves),
            published,
            unavailable,
            len(payloads) if persist else 0,
            dict(sorted(reasons.items())),
            topic_results,
        )

    def _evaluate_topic(
        self,
        topic: Topic,
        snapshot: TopicSnapshot,
        facts: list[TopicSnapshotMemberFact],
        evaluation_date: date,
        context: MarketContext,
        history: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        resolution = resolve_score_projection(self.session, topic.id, evaluation_date)
        eligible_facts = _return_eligible_facts(facts)
        importance = {
            UUID(member.instrument_id): float(member.score_importance)
            for member in resolution.selected_score_members
        }
        markets = _market_map(self.session, eligible_facts)
        benchmark_values = {"TWSE": context.tai_ex_return_pct, "TPEX": context.tpex_return_pct}
        observations: list[MemberObservation] = []
        for fact in eligible_facts:
            role = str(fact.structural_role)
            market = _market_code(markets[fact.instrument_id])
            observations.append(
                MemberObservation(
                    str(fact.instrument_id),
                    role,
                    float(fact.change_pct) if fact.change_pct is not None else None,
                    importance.get(fact.instrument_id),
                    market,
                    benchmark_values.get(market),
                )
            )
        members = tuple(observations)
        absolute = evaluate_strength_view(
            members, view="ABSOLUTE", policy=DEFAULT_POLICY, minimum_formal_member_count=0
        )
        relative = evaluate_strength_view(
            members, view="RELATIVE", policy=DEFAULT_POLICY, minimum_formal_member_count=0
        )
        if absolute.status != "EVALUATED":
            raise ValueError("ABSOLUTE_STRENGTH_UNAVAILABLE")
        metrics = _state_metrics(members, absolute)
        metrics["relativeStrength"] = relative.strength
        derivatives = build_structural_derivatives(metrics, history)
        role_lineage = {
            str(fact.instrument_id): {
                "role": fact.structural_role,
                "roleSource": fact.role_source,
                "roleAuthorityVersion": (fact.raw_fact_payload or {}).get("roleAuthorityVersion"),
                "roleAuthorityHash": (fact.raw_fact_payload or {}).get("roleAuthorityHash"),
            }
            for fact in facts
        }
        lineage = {
            "implementationSha": runtime_git_sha(),
            "policyHash": DEFAULT_POLICY.policy_hash(),
            "asOfDate": evaluation_date.isoformat(),
            "topicAuthority": {
                "topicId": str(topic.id),
                "topicSlug": topic.slug,
                "topicStatus": topic.status,
            },
            "snapshot": {
                "id": str(snapshot.id),
                "identity": snapshot.snapshot_identity,
                "inputHash": _input_hash(snapshot, facts),
                "correctionSequence": snapshot.correction_sequence,
            },
            "membershipAuthority": {
                "snapshotId": snapshot.membership_snapshot_id,
                "snapshotHash": snapshot.membership_snapshot_hash,
            },
            "structuralRoleAuthority": role_lineage,
            "scoreProjection": {
                "projectionId": resolution.record.projection_id,
                "projectionVersion": resolution.record.projection_version,
                "lineageHash": resolution.record.lineage_hash,
            },
            "benchmarkAuthority": context.as_dict(),
        }
        quality_flags = {
            "relativeStatus": relative.status,
            "relativeUnavailableReason": (
                None if relative.status == "EVALUATED" else "BENCHMARK_FACTS_MISSING_OR_STALE"
            ),
            "smallFormalTopic": len(members) < 3,
            "formalDailyGradeAuthority": "ABSOLUTE",
            "marketContextDoesNotModifyStrength": True,
        }
        return {
            "evaluation_date": evaluation_date,
            "topic_id": topic.id,
            "topic_slug": topic.slug,
            "evaluation_status": "PUBLISHED",
            "eligibility": "ELIGIBLE",
            "score": _decimal(absolute.strength),
            "grade": absolute.grade,
            "components": {
                "absolute": _view_payload(absolute),
                "relative": _view_payload(relative),
                "formalDailyGrade": absolute.grade,
                "marketContext": context.as_dict(),
                "derivatives": derivatives,
                "availability": {
                    "absolute": absolute.status,
                    "relative": relative.status,
                },
            },
            "eligibility_audit": {
                "formalMemberCount": len(facts),
                "eligibleMemberCount": len(eligible_facts),
                "accountedUnavailableMemberCount": len(facts) - len(eligible_facts),
                "observedMemberCount": len(eligible_facts),
                "coveragePct": (
                    len(eligible_facts) * 100.0 / len(facts) if facts else 0.0
                ),
                "roleAuthorityComplete": True,
            },
            "quality_flags": quality_flags,
            "publication_status": FORMAL_PUBLICATION_STATUS_PUBLISHED,
            "publication_mode": FORMAL_PUBLICATION_MODE,
            "contract_version": FORMAL_STRENGTH_CONTRACT_VERSION,
            "calculation_version": FORMAL_STRENGTH_CALCULATION_VERSION,
            "policy_id": POLICY_ID,
            "policy_version": POLICY_VERSION,
            "d001_projection_id": resolution.record.projection_id,
            "d001_projection_version": resolution.record.projection_version,
            "input_snapshot_id": snapshot.id,
            "input_snapshot_identity": snapshot.snapshot_identity,
            "input_snapshot_hash": _input_hash(snapshot, facts),
            "membership_snapshot_id": snapshot.membership_snapshot_id,
            "membership_snapshot_hash": snapshot.membership_snapshot_hash,
            "relation_version": snapshot.relation_version,
            "reference_registry_version": snapshot.reference_registry_version,
            "mapping_policy_version": snapshot.mapping_policy_version,
            "session_code": snapshot.session_code,
            "calendar_code": snapshot.calendar_code,
            "source_artifact_id": snapshot.source_artifact_id,
            "source_artifact_hash": snapshot.source_artifact_hash,
            "lineage": lineage,
            "lineage_hash": _canonical_hash(lineage),
            "member_fact_hashes": {str(fact.instrument_id): fact.fact_hash for fact in facts},
            "decision_revision": 0,
            "supersession_state": "ACTIVE",
            "published_at": datetime.now(UTC),
            "as_of_at": snapshot.as_of_at,
            "generated_at": datetime.now(UTC),
            "diagnostic_detail": None,
        }

    @staticmethod
    def _unavailable_values(
        topic: Topic,
        evaluation_date: date,
        snapshot: TopicSnapshot | None,
        gate: FormalStrengthGate,
        reason: str,
    ) -> dict[str, Any]:
        return {
            "evaluation_date": evaluation_date,
            "topic_id": topic.id,
            "topic_slug": topic.slug,
            "evaluation_status": "UNAVAILABLE",
            "eligibility": "UNAVAILABLE",
            "score": None,
            "grade": None,
            "components": {
                "absolute": {"status": "UNAVAILABLE", "score": None, "grade": None},
                "relative": {"status": "UNAVAILABLE", "score": None, "grade": None},
                "formalDailyGrade": None,
                "derivatives": {"status": "UNAVAILABLE"},
            },
            "eligibility_audit": {
                "formalGate": gate.reason,
                "inputSnapshotHash": gate.input_snapshot_hash,
            },
            "quality_flags": {"unavailableReason": reason},
            "publication_status": FORMAL_PUBLICATION_STATUS_UNAVAILABLE,
            "publication_mode": FORMAL_PUBLICATION_MODE,
            "contract_version": FORMAL_STRENGTH_CONTRACT_VERSION,
            "calculation_version": FORMAL_STRENGTH_CALCULATION_VERSION,
            "policy_id": POLICY_ID,
            "policy_version": POLICY_VERSION,
            "d001_projection_id": None,
            "d001_projection_version": None,
            "input_snapshot_id": snapshot.id if snapshot else None,
            "input_snapshot_identity": snapshot.snapshot_identity if snapshot else None,
            "input_snapshot_hash": gate.input_snapshot_hash,
            "membership_snapshot_id": snapshot.membership_snapshot_id if snapshot else None,
            "membership_snapshot_hash": snapshot.membership_snapshot_hash if snapshot else None,
            "relation_version": snapshot.relation_version if snapshot else None,
            "reference_registry_version": snapshot.reference_registry_version if snapshot else None,
            "mapping_policy_version": snapshot.mapping_policy_version if snapshot else None,
            "session_code": snapshot.session_code if snapshot else None,
            "calendar_code": snapshot.calendar_code if snapshot else None,
            "source_artifact_id": snapshot.source_artifact_id if snapshot else None,
            "source_artifact_hash": snapshot.source_artifact_hash if snapshot else None,
            "lineage": {
                "implementationSha": runtime_git_sha(),
                "policyHash": DEFAULT_POLICY.policy_hash(),
                "asOfDate": evaluation_date.isoformat(),
                "inputSnapshotHash": gate.input_snapshot_hash,
                "unavailableReason": reason,
            },
            "lineage_hash": _canonical_hash(
                {"inputSnapshotHash": gate.input_snapshot_hash, "reason": reason}
            ),
            "member_fact_hashes": None,
            "decision_revision": 0,
            "supersession_state": "ACTIVE",
            "published_at": None,
            "as_of_at": snapshot.as_of_at if snapshot else None,
            "generated_at": datetime.now(UTC),
            "diagnostic_detail": reason,
        }

    @staticmethod
    def _payload(values: Mapping[str, Any]) -> dict[str, Any]:
        components = values.get("components") or {}
        absolute = components.get("absolute") or {}
        relative = components.get("relative") or {}
        return {
            "topicId": str(values["topic_id"]),
            "topicSlug": values["topic_slug"],
            "evaluationDate": values["evaluation_date"],
            "status": values["evaluation_status"],
            "publicationStatus": values["publication_status"],
            "absolute": absolute,
            "relative": relative,
            "formalDailyGrade": values.get("grade"),
            "marketContext": components.get("marketContext"),
            "derivatives": components.get("derivatives"),
            "qualityFlags": values.get("quality_flags") or {},
            "lineage": values.get("lineage") or {},
        }

    def run_replay(
        self,
        *,
        from_date: date = FORMAL_STRENGTH_START,
        to_date: date | None = None,
        market_index_facts_by_date: Mapping[date, Iterable[Any]] | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Replay Strength from the earliest affected formal date forward.

        The caller supplies the correction's earliest affected date.  Every
        active formal snapshot on or after that date is re-evaluated, and a
        changed result is appended as a superseding decision rather than
        overwriting the prior receipt.
        """

        successor = aliased(TopicSnapshot)
        dates = list(
            self.session.scalars(
                select(TopicSnapshot.snapshot_date)
                .where(
                    TopicSnapshot.snapshot_date >= from_date,
                    TopicSnapshot.publication_mode == FORMAL_PUBLICATION_MODE,
                    TopicSnapshot.membership_mode == "PIT_FORMAL",
                    TopicSnapshot.publication_state == "PUBLISHED",
                    TopicSnapshot.finality_state == "FINAL",
                    ~select(successor.id)
                    .where(successor.supersedes_snapshot_id == TopicSnapshot.id)
                    .exists(),
                )
                .distinct()
                .order_by(TopicSnapshot.snapshot_date)
            )
        )
        if to_date is not None:
            dates = [item for item in dates if item <= to_date]
        runs = [
            self.run_once(
                evaluation_date=item,
                market_index_facts=(market_index_facts_by_date or {}).get(item, ()),
                persist=persist,
            )
            for item in dates
        ]
        return {
            "status": (
                "SUCCESS"
                if runs and all(run.status == "SUCCESS" for run in runs)
                else "FAIL_CLOSED"
                if runs
                else "INSUFFICIENT_FORMAL_HISTORY"
            ),
            "formalDates": [item.isoformat() for item in dates],
            "formalStrengthTradingSessions": len(dates),
            "publishedRows": sum(run.published_rows for run in runs),
            "unavailableRows": sum(run.unavailable_rows for run in runs),
            "contractVersion": FORMAL_STRENGTH_CONTRACT_VERSION,
            "calculationVersion": FORMAL_STRENGTH_CALCULATION_VERSION,
            "policyId": POLICY_ID,
            "policyVersion": POLICY_VERSION,
            "runs": [run.as_dict() for run in runs],
        }

    def _persist(self, values: dict[str, Any]) -> None:
        successor = aliased(TopicScoreFormalResult)
        existing = self.session.scalar(
            select(TopicScoreFormalResult).where(
                TopicScoreFormalResult.topic_id == values["topic_id"],
                TopicScoreFormalResult.evaluation_date == values["evaluation_date"],
                TopicScoreFormalResult.contract_version == FORMAL_STRENGTH_CONTRACT_VERSION,
                ~select(successor.id)
                .where(successor.supersedes_decision_id == TopicScoreFormalResult.id)
                .exists(),
            )
        )
        if existing is not None:
            same = all(
                getattr(existing, field) == values[field]
                for field in (
                    "score",
                    "grade",
                    "evaluation_status",
                    "publication_status",
                    "input_snapshot_hash",
                    "lineage_hash",
                )
            )
            if same:
                return
            values["decision_revision"] = int(getattr(existing, "decision_revision", 0)) + 1
            values["supersedes_decision_id"] = existing.id
            values["supersession_reason"] = "CORRECTED_FORMAL_STRENGTH_INPUT"
        self.session.add(TopicScoreFormalResult(**values))


def read_formal_strength(
    session: Session,
    topic_id: UUID,
    evaluation_date: date | None = None,
) -> dict[str, Any] | None:
    """Read the active formal Strength envelope, never a shadow fallback."""

    successor = aliased(TopicScoreFormalResult)
    statement = (
        select(TopicScoreFormalResult)
        .where(
            TopicScoreFormalResult.topic_id == topic_id,
            TopicScoreFormalResult.contract_version == FORMAL_STRENGTH_CONTRACT_VERSION,
            ~select(successor.id)
            .where(successor.supersedes_decision_id == TopicScoreFormalResult.id)
            .exists(),
        )
        .order_by(TopicScoreFormalResult.evaluation_date.desc(), TopicScoreFormalResult.id.desc())
    )
    if evaluation_date is not None:
        statement = statement.where(TopicScoreFormalResult.evaluation_date == evaluation_date)
    row = session.scalar(statement)
    if row is None:
        return None
    components = row.components or {}
    return {
        "status": row.publication_status,
        "evaluationStatus": row.evaluation_status,
        "evaluationDate": row.evaluation_date,
        "formalDailyGrade": row.grade,
        "absolute": components.get("absolute")
        or {"status": "UNAVAILABLE", "score": None, "grade": None},
        "relative": components.get("relative")
        or {"status": "UNAVAILABLE", "score": None, "grade": None},
        "marketContext": components.get("marketContext"),
        "derivatives": components.get("derivatives"),
        "qualityFlags": row.quality_flags or {},
        "lineage": row.lineage or {},
        "policyId": row.policy_id,
        "policyVersion": row.policy_version,
        "calculationVersion": row.calculation_version,
        "publicationStatus": row.publication_status,
        "unavailableReason": (row.quality_flags or {}).get("unavailableReason"),
    }


__all__ = [
    "FORMAL_PUBLICATION_STATUS_PUBLISHED",
    "FORMAL_PUBLICATION_STATUS_SUPERSEDED",
    "FORMAL_PUBLICATION_STATUS_UNAVAILABLE",
    "FORMAL_STRENGTH_CALCULATION_VERSION",
    "FORMAL_STRENGTH_CONTRACT_VERSION",
    "FORMAL_STRENGTH_START",
    "FormalStrengthGate",
    "FormalStrengthPublisher",
    "FormalStrengthRun",
    "MarketContext",
    "build_market_context",
    "build_structural_derivatives",
    "read_formal_strength",
]
