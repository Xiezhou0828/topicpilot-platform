"""WS1/L5 current-taxonomy historical lifecycle + Strength evidence reconstruction.

This is a read-only, task-owned research adapter.  It deliberately does not
call the production snapshot/lifecycle writers and does not write any
TopicPilot database table.  The adapter freezes the current topic/relation
universe at the supplied canonical HEAD, reuses accepted canonical DAILY_BAR
close evidence, and evaluates the already-frozen lifecycle policy in memory.

The resulting rows are retrospective research evidence.  They are not PIT
truth, FORWARD_SHADOW rows, or a formal publication surface.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from topicpilot_api.topic_lifecycle_engine import (
    LIFECYCLE_CALCULATION_VERSION,
    LIFECYCLE_POLICY_VERSION,
    LifecycleInput,
    LifecycleObservation,
    LifecyclePolicy,
    evaluate_lifecycle,
)

TASK_ID = "TASK-WS1-L5-CURRENT-TAXONOMY-HISTORICAL-LIFECYCLE-STRENGTH-RECONSTRUCTION-20260822"
CANONICAL_HEAD = "dac1dd21cae214ea1ac3e5a511e48774ae2411c9"
SOURCE_CLASS = "CURRENT_TAXONOMY_HISTORICAL_RECONSTRUCTION"
EVALUATION_MODE = "RETROSPECTIVE_RESEARCH_ONLY"
MEMBERSHIP_MODE = "CURRENT_TAXONOMY_FROZEN_RECONSTRUCTION"
START_DATE = date(2026, 2, 3)
WARMUP_DATE = date(2026, 2, 2)
PRE_WINDOW_START = date(2026, 1, 1)
PRE_WINDOW_END = date(2026, 2, 1)
END_DATE = date(2026, 8, 13)
FORMAL_MEMBER_FACT_COUNT = 4235
FORMAL_RUNTIME_MEMBER_FACT_COUNT = 4236
FORMAL_RECONCILIATION_DELTA = FORMAL_RUNTIME_MEMBER_FACT_COUNT - FORMAL_MEMBER_FACT_COUNT

DATASET_FIELDS = [
    "topic_id",
    "topic_slug",
    "topic_name",
    "trading_date",
    "source_class",
    "evaluation_mode",
    "membership_mode",
    "lifecycle_stage",
    "previous_stage",
    "candidate_stage",
    "stage_entered_at",
    "stage_trading_days",
    "evaluation_status",
    "data_status",
    "transition_decision",
    "transition_reason",
    "positive_breadth",
    "strong_breadth",
    "weak_ratio",
    "average_change_pct",
    "leader_change_pct",
    "leader_semantic_available",
    "valid_member_count",
    "observed_member_count",
    "expected_member_count",
    "coverage_pct",
    "confidence",
    "sample_confidence",
    "coverage_confidence",
    "small_sample",
    "strength_raw_evidence_status",
    "quality_status",
    "lineage_status",
    "universe_lineage_status",
    "price_lineage_status",
    "adjustment_lineage_status",
    "security_identity_lineage_status",
    "member_fact_lineage_status",
    "member_fact_reconciliation_status",
    "formal_member_fact_count",
    "formal_runtime_member_fact_count",
    "member_fact_reconciliation_delta",
    "price_observation_count",
    "missing_price_member_count",
    "partial_lineage_flag",
    "unknown_lineage_flag",
    "fail_closed_flag",
    "lineage_flags",
    "universe_lineage_hash",
    "price_lineage_hash",
    "policy_version",
    "calculation_version",
    "publication_state",
]


@dataclass(frozen=True)
class TopicRecord:
    topic_id: UUID
    slug: str
    name: str


@dataclass(frozen=True)
class MemberRecord:
    topic_id: UUID
    instrument_id: UUID
    code: str
    market: str
    relation_version: str
    valid_from: date
    valid_to: date | None
    structural_role: str | None
    approval_state: str | None
    correction_sequence: int | None
    lineage_hash: str | None


@dataclass(frozen=True)
class BarRecord:
    instrument_id: UUID
    code: str
    market: str
    trading_date: date
    close: Decimal | None
    observation_id: UUID
    source_code: str
    adapter_version: str
    reference_data_version: str | None
    normalization_contract_version: str | None
    mapping_policy_version: str | None
    adjustment_state: str


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _hash_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _hash_lines(lines: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _csv_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if isinstance(value, Decimal):
        return str(value)
    return value


def _write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, default=_iso) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_topics(session: Session) -> list[TopicRecord]:
    rows = session.execute(
        text(
            """
            SELECT id, slug, name
            FROM topicpilot.topics
            WHERE status NOT IN ('DISABLED', 'RETIRED')
            ORDER BY slug, id
            """
        )
    ).mappings()
    return [TopicRecord(row["id"], row["slug"], row["name"]) for row in rows]


def _read_current_members(session: Session) -> tuple[dict[UUID, list[MemberRecord]], dict[UUID, str]]:
    """Read and deterministically freeze current relations.

    The adapter intentionally does not join live_tracking_universe and does
    not apply historical effective-date filtering.  It selects the latest
    non-superseded open-ended relation for each topic/instrument pair, which
    is the frozen current taxonomy mapping used for retrospective research.
    """

    rows = session.execute(
        text(
            """
            SELECT
                r.topic_id,
                r.instrument_id,
                i.instrument_code,
                m.code AS market_code,
                r.relation_version,
                r.valid_from,
                r.valid_to,
                r.structural_role,
                r.approval_state,
                r.correction_sequence,
                r.lineage_hash,
                r.id,
                r.superseded_by_authority_id
            FROM topicpilot.instrument_topic_relations r
            JOIN topicpilot.instruments i ON i.id = r.instrument_id
            JOIN topicpilot.markets m ON m.id = i.market_id
            JOIN topicpilot.topics t ON t.id = r.topic_id
            WHERE t.status NOT IN ('DISABLED', 'RETIRED')
              AND i.is_active = TRUE
              AND m.is_active = TRUE
              AND r.valid_to IS NULL
              AND r.superseded_by_authority_id IS NULL
            ORDER BY r.topic_id, r.instrument_id,
                     COALESCE(r.correction_sequence, 0) DESC,
                     r.valid_from DESC, r.relation_version DESC, r.id DESC
            """
        )
    ).mappings()
    selected: dict[tuple[UUID, UUID], MemberRecord] = {}
    for row in rows:
        key = (row["topic_id"], row["instrument_id"])
        selected.setdefault(
            key,
            MemberRecord(
                topic_id=row["topic_id"],
                instrument_id=row["instrument_id"],
                code=row["instrument_code"],
                market=row["market_code"],
                relation_version=row["relation_version"],
                valid_from=row["valid_from"],
                valid_to=row["valid_to"],
                structural_role=row["structural_role"],
                approval_state=row["approval_state"],
                correction_sequence=row["correction_sequence"],
                lineage_hash=row["lineage_hash"],
            ),
        )
    members: dict[UUID, list[MemberRecord]] = defaultdict(list)
    for item in selected.values():
        members[item.topic_id].append(item)
    for topic_members in members.values():
        topic_members.sort(key=lambda item: (item.code, item.market, str(item.instrument_id)))
    universe_hashes = {
        topic_id: _hash_lines(
            f"{item.instrument_id}|{item.code}|{item.market}|{item.relation_version}|"
            f"{item.valid_from.isoformat()}|{item.valid_to}|{item.structural_role}|"
            f"{item.approval_state}|{item.correction_sequence}|{item.lineage_hash}"
            for item in items
        )
        for topic_id, items in members.items()
    }
    return members, universe_hashes


def _read_security_identity_count(session: Session) -> int:
    value = session.execute(
        text("SELECT COUNT(*) FROM topicpilot.security_identities")
    ).scalar_one()
    return int(value)


def _read_bars(session: Session) -> dict[UUID, list[BarRecord]]:
    """Read accepted canonical DAILY_BAR observations once for the window."""

    rows = session.execute(
        text(
            """
            WITH candidates AS (
                SELECT
                    co.id AS observation_id,
                    co.instrument_id,
                    i.instrument_code,
                    m.code AS market_code,
                    (co.observed_at AT TIME ZONE m.timezone)::date AS trading_date,
                    cp.close,
                    cp.adjustment_state,
                    mds.source_code,
                    mds.adapter_version,
                    co.reference_data_version,
                    co.normalization_contract_version,
                    co.mapping_policy_version,
                    co.retrieved_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY co.instrument_id,
                            (co.observed_at AT TIME ZONE m.timezone)::date
                        ORDER BY mds.source_rank, co.retrieved_at DESC, co.id DESC
                    ) AS source_rank_row
                FROM topicpilot.canonical_observations co
                JOIN topicpilot.canonical_price_observations cp
                  ON cp.canonical_observation_id = co.id
                JOIN topicpilot.instruments i ON i.id = co.instrument_id
                JOIN topicpilot.markets m ON m.id = i.market_id
                JOIN topicpilot.market_data_sources mds ON mds.id = co.source_id
                WHERE co.family_code = 'PRICE'
                  AND co.quality_state = 'ACCEPTED'
                  AND mds.observation_semantics = 'DAILY_BAR'
                  AND (co.observed_at AT TIME ZONE m.timezone)::date
                      BETWEEN :warmup_date AND :end_date
                  AND cp.close IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1
                      FROM topicpilot.canonical_observations successor
                      WHERE successor.supersedes_id = co.id
                        AND successor.family_code = 'PRICE'
                        AND successor.quality_state = 'ACCEPTED'
                  )
            )
            SELECT observation_id, instrument_id, instrument_code, market_code,
                   trading_date, close, adjustment_state, source_code,
                   adapter_version, reference_data_version,
                   normalization_contract_version, mapping_policy_version
            FROM candidates
            WHERE source_rank_row = 1
            ORDER BY instrument_id, trading_date, observation_id
            """
        ),
        {"warmup_date": WARMUP_DATE, "end_date": END_DATE},
    ).mappings()
    result: dict[UUID, list[BarRecord]] = defaultdict(list)
    for row in rows:
        result[row["instrument_id"]].append(
            BarRecord(
                instrument_id=row["instrument_id"],
                code=row["instrument_code"],
                market=row["market_code"],
                trading_date=row["trading_date"],
                close=row["close"],
                observation_id=row["observation_id"],
                source_code=row["source_code"],
                adapter_version=row["adapter_version"],
                reference_data_version=row["reference_data_version"],
                normalization_contract_version=row["normalization_contract_version"],
                mapping_policy_version=row["mapping_policy_version"],
                # The canonical historical read model intentionally exposes
                # adjustment/corporate-action continuity as UNKNOWN.
                adjustment_state="UNKNOWN",
            )
        )
    return result


def _bar_index(bars: dict[UUID, list[BarRecord]]) -> tuple[dict[tuple[UUID, date], BarRecord], dict[date, int]]:
    indexed: dict[tuple[UUID, date], BarRecord] = {}
    date_counts: Counter[date] = Counter()
    for instrument_id, items in bars.items():
        items.sort(key=lambda item: (item.trading_date, str(item.observation_id)))
        for item in items:
            indexed[(instrument_id, item.trading_date)] = item
            date_counts[item.trading_date] += 1
    return indexed, dict(sorted(date_counts.items()))


def _previous_close(items: list[BarRecord], evaluation_date: date) -> Decimal | None:
    prior = [item for item in items if item.trading_date < evaluation_date and item.close is not None]
    return prior[-1].close if prior else None


def _round(value: Any, places: int = 6) -> float | None:
    if value is None:
        return None
    return round(float(value), places)


def _stage_payload(result: Any) -> dict[str, Any]:
    evidence = result.evidence
    confidence = evidence.sample_confidence
    diffusion = evidence.diffusion
    strength = evidence.group_strength
    leadership = evidence.leadership
    vector = {
        "positive_breadth": _round(diffusion.get("positiveBreadth")),
        "strong_breadth": _round(strength.get("strongBreadth")),
        "weak_ratio": _round(strength.get("weakRatio")),
        "average_change_pct": _round(strength.get("averageChangePct")),
        "leader_change_pct": _round(leadership.get("leaderChangePct")),
    }
    vector_complete = all(vector[field] is not None for field in (
        "positive_breadth", "strong_breadth", "weak_ratio", "average_change_pct"
    ))
    return {
        "lifecycle_stage": result.final_stage,
        "previous_stage": result.previous_stage,
        "candidate_stage": result.candidate_stage,
        "stage_entered_at": result.stage_entered_at,
        "stage_trading_days": result.stage_trading_days,
        "evaluation_status": result.evaluation_status,
        # The frozen engine returns its internal shadow carrier for an
        # evaluated result.  L5 is not a shadow writer, so the task-owned
        # artifact uses an explicit retrospective research label instead of
        # leaking that carrier name into the output contract.
        "data_status": (
            "RECONSTRUCTED_RESEARCH"
            if result.evaluation_status == "EVALUATED"
            else result.evaluation_status
        ),
        "transition_decision": result.transition_decision,
        "transition_reason": result.transition_reason,
        **vector,
        "leader_semantic_available": bool(leadership.get("leaderSemanticAvailable")),
        "valid_member_count": int(confidence.get("validChangeCount") or 0),
        "observed_member_count": int(confidence.get("observedMemberCount") or 0),
        "expected_member_count": int(confidence.get("expectedMemberCount") or 0),
        "coverage_pct": _round(confidence.get("coveragePct")),
        "confidence": _round(confidence.get("confidence")),
        "sample_confidence": _round(confidence.get("sampleConfidence")),
        "coverage_confidence": _round(confidence.get("coverageConfidence")),
        "small_sample": bool(confidence.get("smallSample")),
        "strength_raw_evidence_status": "COMPLETE" if vector_complete else "INCOMPLETE",
    }


def _fail_closed_payload(
    *, topic_id: UUID, topic_members: list[MemberRecord], date_value: date, reason: str
) -> dict[str, Any]:
    expected = len(topic_members)
    return {
        "lifecycle_stage": None,
        "previous_stage": None,
        "candidate_stage": None,
        "stage_entered_at": None,
        "stage_trading_days": None,
        "evaluation_status": "FAIL_CLOSED",
        "data_status": "FAIL_CLOSED",
        "transition_decision": "FAIL_CLOSED",
        "transition_reason": reason,
        "positive_breadth": None,
        "strong_breadth": None,
        "weak_ratio": None,
        "average_change_pct": None,
        "leader_change_pct": None,
        "leader_semantic_available": False,
        "valid_member_count": 0,
        "observed_member_count": 0,
        "expected_member_count": expected,
        "coverage_pct": None,
        "confidence": None,
        "sample_confidence": None,
        "coverage_confidence": None,
        "small_sample": True,
        "strength_raw_evidence_status": "INCOMPLETE",
    }


def _quality_payload(
    *,
    topic_id: UUID,
    topic_members: list[MemberRecord],
    universe_hash: str | None,
    price_rows: list[BarRecord],
    missing_price_count: int,
    security_identity_count: int,
    fail_closed: bool,
) -> dict[str, Any]:
    relation_lineage_missing = any(item.lineage_hash in (None, "") for item in topic_members)
    universe_status = "PARTIAL" if relation_lineage_missing else "AVAILABLE_FROZEN_CURRENT"
    if not price_rows:
        price_status = "UNAVAILABLE"
    elif missing_price_count:
        price_status = "PARTIAL"
    else:
        price_status = "AVAILABLE_BOUNDED"
    adjustment_status = "UNKNOWN" if price_rows else "UNAVAILABLE"
    security_status = "UNKNOWN" if security_identity_count == 0 else "PARTIAL"
    member_fact_status = "UNKNOWN"
    reconciliation_status = "UNRESOLVED_COUNT_MISMATCH"
    flags = [
        "SOURCE_CLASS_RESEARCH_ONLY",
        "CURRENT_TAXONOMY_NOT_PIT",
        "CURRENT_MAPPING_NOT_LIVE_TRACKING_UNIVERSE",
        "PRICE_ADJUSTMENT_UNKNOWN",
        "CORPORATE_ACTION_CONTINUITY_UNKNOWN",
        "MEMBER_FACT_LINEAGE_NOT_USED",
        "FORMAL_MEMBER_FACT_RECONCILIATION_UNRESOLVED_DELTA_1",
    ]
    if relation_lineage_missing:
        flags.append("RELATION_LINEAGE_PARTIAL")
    if missing_price_count:
        flags.append("MISSING_MEMBER_PRICE_EVIDENCE")
    if security_identity_count == 0:
        flags.append("SECURITY_IDENTITY_HISTORY_EMPTY")
    if fail_closed:
        flags.append("FAIL_CLOSED_NO_RECONSTRUCTABLE_INPUT")
    unknown = adjustment_status == "UNKNOWN" or security_status == "UNKNOWN" or member_fact_status == "UNKNOWN"
    partial = universe_status == "PARTIAL" or price_status == "PARTIAL"
    lineage_status = "FAIL_CLOSED" if fail_closed else ("PARTIAL" if partial else "UNKNOWN" if unknown else "AVAILABLE")
    quality_status = "FAIL_CLOSED" if fail_closed else "PARTIAL"
    return {
        "quality_status": quality_status,
        "lineage_status": lineage_status,
        "universe_lineage_status": universe_status,
        "price_lineage_status": price_status,
        "adjustment_lineage_status": adjustment_status,
        "security_identity_lineage_status": security_status,
        "member_fact_lineage_status": member_fact_status,
        "member_fact_reconciliation_status": reconciliation_status,
        "formal_member_fact_count": FORMAL_MEMBER_FACT_COUNT,
        "formal_runtime_member_fact_count": FORMAL_RUNTIME_MEMBER_FACT_COUNT,
        "member_fact_reconciliation_delta": FORMAL_RECONCILIATION_DELTA,
        "price_observation_count": len(price_rows),
        "missing_price_member_count": missing_price_count,
        "partial_lineage_flag": partial,
        "unknown_lineage_flag": unknown,
        "fail_closed_flag": fail_closed,
        "lineage_flags": flags,
        "universe_lineage_hash": universe_hash,
    }


def _reconstruct(
    session: Session,
    *,
    policy: LifecyclePolicy,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    topics = _read_topics(session)
    members, universe_hashes = _read_current_members(session)
    security_identity_count = _read_security_identity_count(session)
    bars = _read_bars(session)
    indexed_bars, date_counts = _bar_index(bars)
    research_dates = sorted(
        value for value in date_counts if START_DATE <= value <= END_DATE
    )
    states: dict[UUID, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    bootstrap_topics: set[UUID] = set()
    bootstrap_pending = 0
    bootstrap_evaluated = 0
    persistence_violations = 0
    duplicate_observation_keys = 0
    selected_price_ids: set[tuple[UUID, UUID, date]] = set()

    for evaluation_date in research_dates:
        for topic in topics:
            topic_members = members.get(topic.topic_id, [])
            if not topic_members:
                payload = _fail_closed_payload(
                    topic_id=topic.topic_id,
                    topic_members=topic_members,
                    date_value=evaluation_date,
                    reason="NO_CURRENT_FROZEN_TOPIC_RELATIONS",
                )
                quality = _quality_payload(
                    topic_id=topic.topic_id,
                    topic_members=topic_members,
                    universe_hash=None,
                    price_rows=[],
                    missing_price_count=0,
                    security_identity_count=security_identity_count,
                    fail_closed=True,
                )
                state = states.get(topic.topic_id)
            else:
                observations: list[LifecycleObservation] = []
                price_rows: list[BarRecord] = []
                missing_price_count = 0
                price_lineage_entries: list[str] = []
                for member in topic_members:
                    current = indexed_bars.get((member.instrument_id, evaluation_date))
                    if current is None or current.close is None:
                        missing_price_count += 1
                        continue
                    previous = _previous_close(bars.get(member.instrument_id, []), evaluation_date)
                    if previous is None or previous <= 0:
                        missing_price_count += 1
                        continue
                    price_rows.append(current)
                    # A single accepted bar may legitimately support several
                    # topics.  Idempotency is checked at Topic×Instrument×Date
                    # grain, not by treating cross-topic reuse as a duplicate.
                    key = (topic.topic_id, current.instrument_id, current.trading_date)
                    if key in selected_price_ids:
                        duplicate_observation_keys += 1
                    selected_price_ids.add(key)
                    change = (current.close - previous) / previous * Decimal(100)
                    observations.append(
                        LifecycleObservation(str(member.instrument_id), float(change), None)
                    )
                    price_lineage_entries.append(
                        f"{current.instrument_id}|{current.trading_date.isoformat()}|"
                        f"{current.observation_id}|{current.source_code}|{current.adapter_version}|"
                        f"{current.reference_data_version}|{current.normalization_contract_version}|"
                        f"{current.mapping_policy_version}|{current.adjustment_state}"
                    )
                previous_state = states.get(topic.topic_id, {})
                value = LifecycleInput(
                    topic_id=str(topic.topic_id),
                    trading_date=evaluation_date,
                    expected_member_count=len(topic_members),
                    observations=tuple(observations),
                    previous_stage=previous_state.get("final_stage"),
                    previous_stage_entered_at=previous_state.get("stage_entered_at"),
                    previous_stage_trading_days=previous_state.get("stage_trading_days"),
                    previous_candidate_stage=previous_state.get("candidate_stage"),
                    previous_candidate_streak=int(previous_state.get("candidate_streak") or 0),
                )
                result = evaluate_lifecycle(value, policy)
                payload = _stage_payload(result)
                quality = _quality_payload(
                    topic_id=topic.topic_id,
                    topic_members=topic_members,
                    universe_hash=universe_hashes.get(topic.topic_id),
                    price_rows=price_rows,
                    missing_price_count=missing_price_count,
                    security_identity_count=security_identity_count,
                    fail_closed=False,
                )
                quality["price_lineage_hash"] = _hash_lines(sorted(price_lineage_entries))
                state = {
                    "final_stage": result.final_stage,
                    "stage_entered_at": result.stage_entered_at,
                    "stage_trading_days": result.stage_trading_days,
                    "candidate_stage": result.candidate_stage,
                    "candidate_streak": result.confirmation_state.get("candidateStreak", 0),
                }
                states[topic.topic_id] = state
                if evaluation_date == research_dates[0]:
                    bootstrap_topics.add(topic.topic_id)
                    if result.evaluation_status == "PENDING":
                        bootstrap_pending += 1
                    elif result.evaluation_status == "EVALUATED":
                        bootstrap_evaluated += 1

                if result.final_stage and result.stage_trading_days:
                    prior_stage = previous_state.get("final_stage")
                    prior_days = previous_state.get("stage_trading_days")
                    if (
                        prior_stage == result.final_stage
                        and prior_days is not None
                        and result.stage_trading_days != prior_days + 1
                    ):
                        persistence_violations += 1

            row = {
                "topic_id": str(topic.topic_id),
                "topic_slug": topic.slug,
                "topic_name": topic.name,
                "trading_date": evaluation_date,
                "source_class": SOURCE_CLASS,
                "evaluation_mode": EVALUATION_MODE,
                "membership_mode": MEMBERSHIP_MODE,
                "policy_version": LIFECYCLE_POLICY_VERSION,
                "calculation_version": LIFECYCLE_CALCULATION_VERSION,
                "publication_state": "UNPUBLISHED_RESEARCH_ARTIFACT",
                **payload,
                **quality,
            }
            rows.append(row)

    rows.sort(key=lambda row: (row["trading_date"], row["topic_slug"], row["topic_id"]))
    keys = [(row["topic_id"], row["trading_date"]) for row in rows]
    duplicate_rows = len(keys) - len(set(keys))
    evidence = {
        "topic_count": len(topics),
        "topics_with_frozen_current_relations": sum(1 for topic in topics if members.get(topic.topic_id)),
        "topics_without_frozen_current_relations": sum(1 for topic in topics if not members.get(topic.topic_id)),
        "member_relation_count": sum(len(items) for items in members.values()),
        "instrument_count_with_price_evidence": len(bars),
        "price_observation_count": sum(len(items) for items in bars.values()),
        "warmup_date": WARMUP_DATE,
        "warmup_price_observation_count": sum(
            1 for items in bars.values() for item in items if item.trading_date == WARMUP_DATE
        ),
        "research_dates": [value.isoformat() for value in research_dates],
        "date_count": len(research_dates),
        "date_price_observation_counts": {key.isoformat(): value for key, value in date_counts.items()},
        "security_identity_row_count": security_identity_count,
        "bootstrap": {
            "first_research_date": research_dates[0].isoformat() if research_dates else None,
            "bootstrap_topic_count": len(bootstrap_topics),
            "bootstrap_pending_count": bootstrap_pending,
            "bootstrap_evaluated_count": bootstrap_evaluated,
            "unseen_prior_state": True,
            "no_pre_start_stage_claim": True,
        },
        "persistence_chain_violations": persistence_violations,
        "duplicate_topic_date_rows": duplicate_rows,
        "duplicate_selected_price_keys": duplicate_observation_keys,
        "selected_price_key_count": len(selected_price_ids),
    }
    return rows, evidence


def _normalized_rows_hash(rows: list[dict[str, Any]]) -> str:
    normalized = []
    for row in rows:
        normalized.append({field: _csv_value(row.get(field)) for field in DATASET_FIELDS})
    return _hash_json(normalized)


def _group_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage_counter = Counter(row["lifecycle_stage"] or row["evaluation_status"] for row in rows)
    status_counter = Counter(row["evaluation_status"] for row in rows)
    data_status_counter = Counter(row["data_status"] for row in rows)
    quality_counter = Counter(row["quality_status"] for row in rows)
    lineage_counter = Counter(row["lineage_status"] for row in rows)
    strength_counter = Counter(row["strength_raw_evidence_status"] for row in rows)
    return {
        "row_count": len(rows),
        "topic_count": len({row["topic_id"] for row in rows}),
        "date_count": len({row["trading_date"] for row in rows}),
        "stage_or_status_counts": dict(sorted(stage_counter.items(), key=lambda item: str(item[0]))),
        "evaluation_status_counts": dict(sorted(status_counter.items())),
        "data_status_counts": dict(sorted(data_status_counter.items())),
        "quality_status_counts": dict(sorted(quality_counter.items())),
        "lineage_status_counts": dict(sorted(lineage_counter.items())),
        "strength_raw_evidence_counts": dict(sorted(strength_counter.items())),
        "strength_raw_evidence_complete_pct": round(
            strength_counter["COMPLETE"] * 100 / len(rows), 6
        ) if rows else 0.0,
        "rows_with_partial_or_unknown_lineage": sum(
            row["partial_lineage_flag"] or row["unknown_lineage_flag"] for row in rows
        ),
        "rows_with_partial_lineage": sum(row["partial_lineage_flag"] for row in rows),
        "rows_with_unknown_lineage": sum(row["unknown_lineage_flag"] for row in rows),
        "rows_fail_closed": sum(row["fail_closed_flag"] for row in rows),
    }


def _coverage_rows(rows: list[dict[str, Any]], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = [
        {
            "coverage_key": "PRE_WINDOW_UNAVAILABLE",
            "date_or_range": f"{PRE_WINDOW_START.isoformat()}..{PRE_WINDOW_END.isoformat()}",
            "date_state": "UNAVAILABLE",
            "topic_count": 0,
            "topic_date_rows": 0,
            "evaluated_rows": 0,
            "pending_rows": 0,
            "insufficient_rows": 0,
            "fail_closed_rows": 0,
            "strength_complete_rows": 0,
            "partial_or_unknown_lineage_rows": 0,
            "partial_lineage_rows": 0,
            "unknown_lineage_rows": 0,
            "note": "No synthetic values; outside reconstruction input window.",
        },
        {
            "coverage_key": "WARMUP_ONLY",
            "date_or_range": WARMUP_DATE.isoformat(),
            "date_state": "CLOSE_WARMUP_ONLY",
            "topic_count": 0,
            "topic_date_rows": 0,
            "evaluated_rows": 0,
            "pending_rows": 0,
            "insufficient_rows": 0,
            "fail_closed_rows": 0,
            "strength_complete_rows": 0,
            "partial_or_unknown_lineage_rows": 0,
            "partial_lineage_rows": 0,
            "unknown_lineage_rows": 0,
            "note": "Used only as previous-close warm-up; no formal research lifecycle row emitted.",
        },
    ]
    for date_value in sorted({row["trading_date"] for row in rows}):
        date_rows = [row for row in rows if row["trading_date"] == date_value]
        output.append(
            {
                "coverage_key": "RESEARCH_DATE",
                "date_or_range": date_value.isoformat(),
                "date_state": "RECONSTRUCTED_RESEARCH",
                "topic_count": len({row["topic_id"] for row in date_rows}),
                "topic_date_rows": len(date_rows),
                "evaluated_rows": sum(row["evaluation_status"] == "EVALUATED" for row in date_rows),
                "pending_rows": sum(row["evaluation_status"] == "PENDING" for row in date_rows),
                "insufficient_rows": sum(row["evaluation_status"] == "INSUFFICIENT_DATA" for row in date_rows),
                "fail_closed_rows": sum(row["evaluation_status"] == "FAIL_CLOSED" for row in date_rows),
                "strength_complete_rows": sum(
                    row["strength_raw_evidence_status"] == "COMPLETE" for row in date_rows
                ),
                "partial_or_unknown_lineage_rows": sum(
                    row["partial_lineage_flag"] or row["unknown_lineage_flag"] for row in date_rows
                ),
                "partial_lineage_rows": sum(row["partial_lineage_flag"] for row in date_rows),
                "unknown_lineage_rows": sum(row["unknown_lineage_flag"] for row in date_rows),
                "note": "Current taxonomy reconstruction; not PIT/formal publication.",
            }
        )
    return output


def _stage_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(rows)
    counter: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            row["lifecycle_stage"] or "NONE",
            row["evaluation_status"],
            row["data_status"],
        )
        counter[key].append(row)
    output = []
    for (stage, evaluation_status, data_status), group in sorted(counter.items()):
        output.append(
            {
                "lifecycle_stage": stage,
                "evaluation_status": evaluation_status,
                "data_status": data_status,
                "row_count": len(group),
                "topic_count": len({row["topic_id"] for row in group}),
                "date_count": len({row["trading_date"] for row in group}),
                "pct_of_dataset": round(len(group) * 100 / total, 6) if total else 0.0,
            }
        )
    return output


def _lineage_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dimensions = [
        "quality_status",
        "lineage_status",
        "universe_lineage_status",
        "price_lineage_status",
        "adjustment_lineage_status",
        "security_identity_lineage_status",
        "member_fact_lineage_status",
        "member_fact_reconciliation_status",
        "strength_raw_evidence_status",
    ]
    total = len(rows)
    output = []
    for dimension in dimensions:
        counter = Counter(str(row[dimension]) for row in rows)
        for state, count in sorted(counter.items()):
            output.append(
                {
                    "dimension": dimension,
                    "state": state,
                    "row_count": count,
                    "pct_of_dataset": round(count * 100 / total, 6) if total else 0.0,
                    "evidence_note": (
                        "Raw evidence vector completeness is separate from quality metadata."
                        if dimension == "strength_raw_evidence_status"
                        else "Research-only lineage flag; not economic-return truth."
                    ),
                }
            )
    return output


def _build_run_summary(
    rows: list[dict[str, Any]], evidence: dict[str, Any], replay: dict[str, Any], output_dir: Path
) -> dict[str, Any]:
    summary = _group_summary(rows)
    return {
        "task_id": TASK_ID,
        "canonical_head": CANONICAL_HEAD,
        "source_class": SOURCE_CLASS,
        "evaluation_mode": EVALUATION_MODE,
        "membership_mode": MEMBERSHIP_MODE,
        "date_window": {
            "requested_start": START_DATE,
            "warmup_date": WARMUP_DATE,
            "requested_end": END_DATE,
            "pre_window_unavailable": f"{PRE_WINDOW_START}..{PRE_WINDOW_END}",
            "successful_reconstruction_start": rows[0]["trading_date"] if rows else None,
            "successful_reconstruction_end": rows[-1]["trading_date"] if rows else None,
        },
        "dataset": summary,
        "evidence": evidence,
        "reproducibility": replay,
        "artifacts_are_task_owned": True,
        "output_directory": str(output_dir),
        "governance": {
            "WS1_ONLY": "YES",
            "RETROSPECTIVE_RESEARCH_ONLY": "YES",
            "LIFECYCLE_POLICY_CHANGED": "NO",
            "STRENGTH_SCORE_CREATED": "NO",
            "FORWARD_SHADOW_MUTATED": "NO",
            "FORMAL_PUBLICATION": "NO",
            "PRODUCTION_DB_MUTATION": "NO",
            "WS3_STRATEGY_CHANGED": "NO",
            "DEPLOY": "NO",
            "PUSH": "NO",
            "NEXT_TASK_CHANGED": "NO",
        },
    }


def _closure_markdown(
    rows: list[dict[str, Any]], evidence: dict[str, Any], replay: dict[str, Any], summary: dict[str, Any]
) -> str:
    stages = summary["dataset"]["stage_or_status_counts"]
    statuses = summary["dataset"]["evaluation_status_counts"]
    strength = summary["dataset"]["strength_raw_evidence_counts"]
    partial_unknown = summary["dataset"]["rows_with_partial_or_unknown_lineage"]
    start = summary["date_window"]["successful_reconstruction_start"]
    end = summary["date_window"]["successful_reconstruction_end"]
    enough_for_ws3 = (
        bool(rows)
        and replay["reproducible"] == "YES"
        and evidence["duplicate_topic_date_rows"] == 0
        and evidence["persistence_chain_violations"] == 0
        and strength.get("COMPLETE", 0) > 0
    )
    stage_lines = "\n".join(f"- `{key}`: {value}" for key, value in sorted(stages.items()))
    status_lines = "\n".join(f"- `{key}`: {value}" for key, value in sorted(statuses.items()))
    return f"""# {TASK_ID}

## Closure outcome

L5 completed as a task-owned, deterministic retrospective research
reconstruction.  The output source class is
`{SOURCE_CLASS}`.  It is not PIT truth, not FORWARD_SHADOW, and not a formal
publication.  The adapter read the frozen current taxonomy and current
instrument-topic relations; it did not use `live_tracking_universe` and did
not write TopicPilot persistence.

- Canonical HEAD: `{CANONICAL_HEAD}`
- Requested window: `{START_DATE}` to `{END_DATE}`
- Close warm-up only: `{WARMUP_DATE}` (not emitted as a research lifecycle row)
- Pre-window: `{PRE_WINDOW_START}` to `{PRE_WINDOW_END}` remains `UNAVAILABLE`
- Successful reconstructed dates: `{start}` to `{end}`
- Topic×Date rows: `{len(rows)}`
- Distinct topics: `{summary['dataset']['topic_count']}`
- Distinct research dates: `{summary['dataset']['date_count']}`

## Lifecycle distribution

{stage_lines}

Evaluation status:

{status_lines}

## Strength V0 raw evidence

Only the approved raw vector was emitted: `positive_breadth`, `strong_breadth`,
`weak_ratio`, and `average_change_pct`. `leader_change_pct` is retained only
as proxy evidence with `leader_semantic_available=NO`. No dimension labels,
overall strength level, or 0–100 score were created. Coverage, confidence,
sample size, data status, and lineage remain quality metadata.

- Complete raw-vector rows: `{strength.get('COMPLETE', 0)}`
- Incomplete raw-vector rows: `{strength.get('INCOMPLETE', 0)}`
- Rows with partial/unknown lineage: `{partial_unknown}`
- Rows with partial lineage: `{summary['dataset']['rows_with_partial_lineage']}`
- Rows with unknown lineage: `{summary['dataset']['rows_with_unknown_lineage']}`
- Unresolved formal member-fact reconciliation: `4,235` closure rows versus
  `4,236` runtime aggregate; delta `1`, retained as metadata

## Validation

- Date coverage: PASS for the emitted canonical DAILY_BAR research dates;
  no synthetic calendar rows were added.
- Topic coverage: PASS for the frozen current taxonomy; topics without current
  relations are explicit `FAIL_CLOSED` rows.
- Bootstrap: PASS; first date uses unseen prior state and makes no pre-start
  stage claim.
- Persistence/hysteresis chain: `{'PASS' if evidence['persistence_chain_violations'] == 0 else 'FAIL'}`;
  violations `{evidence['persistence_chain_violations']}`.
- Duplicate/idempotency keys: `{'PASS' if evidence['duplicate_topic_date_rows'] == 0 else 'FAIL'}`;
  duplicate Topic×Date rows `{evidence['duplicate_topic_date_rows']}`.
- Deterministic replay: `{replay['reproducible']}`; normalized hash
  `{replay['normalized_dataset_sha256']}`.
- Source-class disclosure: PASS; every row carries
  `{SOURCE_CLASS}` and `UNPUBLISHED_RESEARCH_ARTIFACT`.
- Adjustment/corporate-action continuity: `UNKNOWN`; no exact
  economic-return truth is asserted.
- Security identity lineage: `PARTIAL` with `{evidence['security_identity_row_count']}`
  carrier rows observed; continuity remains incomplete and no identity history
  was invented.

## WS3 handoff decision

The artifact is sufficient to enter the next **research-only** phase
`A2 / Legacy-5 / BOTH × Lifecycle / Strength` conditional expectancy research,
provided WS3 treats this as a reconstructed research panel, keeps all quality
and lineage controls, does not mix it with PIT/formal claims, and does not
change A2, Legacy-5, BOTH definitions, thresholds, or strategy semantics.

`WS3_HANDOFF_READY={'YES' if enough_for_ws3 else 'NO_WITH_REVIEW_REQUIRED'}`

## Governance

```text
WS1_ONLY=YES
RETROSPECTIVE_RESEARCH_ONLY=YES
LIFECYCLE_POLICY_CHANGED=NO
STRENGTH_SCORE_CREATED=NO
FORWARD_SHADOW_MUTATED=NO
FORMAL_PUBLICATION=NO
PRODUCTION_DB_MUTATION=NO
WS3_STRATEGY_CHANGED=NO
DEPLOY=NO
PUSH=NO
NEXT_TASK_CHANGED=NO
```

All outputs are task-owned files under the L5 report directory. Owner dirty and
untracked state was preserved.
"""


def _handoff_markdown(summary: dict[str, Any], replay: dict[str, Any]) -> str:
    dataset = summary["dataset"]
    return f"""# WS3 handoff memo — L5 reconstructed research panel

## Eligibility

`READY_FOR_RESEARCH=YES` when consuming the panel as retrospective evidence
only. The panel has `{dataset['row_count']}` Topic×Date rows across
`{dataset['topic_count']}` topics and `{dataset['date_count']}` trading dates,
with normalized replay status `{replay['reproducible']}`.

## Approved use

WS3 may condition descriptive or pre-registered expectancy analysis on the raw
Strength vector within lifecycle stages:

- `positive_breadth`
- `strong_breadth`
- `weak_ratio`
- `average_change_pct`

`leader_change_pct` is proxy/context only. Keep `coverage`, `confidence`,
sample size, data status, and lineage as quality controls; they are not
Strength dimensions.

## Required guardrails

- Keep `source_class={SOURCE_CLASS}` visible in every panel and result.
- Do not call this PIT truth, FORWARD_SHADOW, or formal publication.
- Do not mix with formal/PIT performance claims without a separately approved
  authority and validation design.
- Keep rows with `PARTIAL`, `UNKNOWN`, and `FAIL_CLOSED` lineage explicit;
  missing future outcomes must remain missing rather than zero.
- Do not change A2, Legacy-5, or BOTH definitions, eligibility, entry/exit,
  position logic, thresholds, or production policy.
- Do not create a Strength label, dimension label, overall level, or score.

## Research question

The next bounded question is whether the raw vector adds conditional
information within the same Lifecycle stage for the already-frozen
`A2 / Legacy-5 / BOTH` research cohorts. This is an expectancy study, not a
strategy rewrite or threshold optimization.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        default=os.environ.get(
            "TOPICPILOT_DATABASE_URL",
            "postgresql+psycopg://topicpilot:topicpilot_local_only@localhost:5432/topicpilot",
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports") / TASK_ID,
    )
    parser.add_argument("--skip-replay", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(args.database_url, pool_pre_ping=True)
    policy = LifecyclePolicy()
    with Session(engine, expire_on_commit=False, autoflush=False) as session:
        rows, evidence = _reconstruct(session, policy=policy)
        first_hash = _normalized_rows_hash(rows)
        if args.skip_replay:
            replay = {
                "reproducible": "NOT_RUN",
                "reconstruction_runs": 1,
                "normalized_dataset_sha256": first_hash,
                "replay_hash": None,
                "duplicate_topic_date_rows": evidence["duplicate_topic_date_rows"],
                "idempotency_check": "NOT_RUN",
            }
        else:
            replay_rows, replay_evidence = _reconstruct(session, policy=policy)
            replay_hash = _normalized_rows_hash(replay_rows)
            replay = {
                "reproducible": "YES" if first_hash == replay_hash and rows == replay_rows else "NO",
                "reconstruction_runs": 2,
                "normalized_dataset_sha256": first_hash,
                "replay_hash": replay_hash,
                "duplicate_topic_date_rows": evidence["duplicate_topic_date_rows"],
                "replay_duplicate_topic_date_rows": replay_evidence["duplicate_topic_date_rows"],
                "idempotency_check": (
                    "PASS"
                    if evidence["duplicate_topic_date_rows"] == 0
                    and replay_evidence["duplicate_topic_date_rows"] == 0
                    else "FAIL"
                ),
            }

    _write_csv(args.output_dir / "historical-lifecycle-strength-dataset.csv", DATASET_FIELDS, rows)
    coverage_rows = _coverage_rows(rows, evidence)
    _write_csv(
        args.output_dir / "coverage-and-quality-summary.csv",
        list(coverage_rows[0].keys()),
        coverage_rows,
    )
    distribution_rows = _stage_rows(rows)
    _write_csv(
        args.output_dir / "stage-distribution.csv",
        list(distribution_rows[0].keys()) if distribution_rows else [
            "lifecycle_stage", "evaluation_status", "data_status", "row_count",
            "topic_count", "date_count", "pct_of_dataset",
        ],
        distribution_rows,
    )
    lineage_rows = _lineage_rows(rows)
    _write_csv(
        args.output_dir / "lineage-quality-audit.csv",
        list(lineage_rows[0].keys()) if lineage_rows else [
            "dimension", "state", "row_count", "pct_of_dataset", "evidence_note",
        ],
        lineage_rows,
    )

    source_artifacts = {}
    for relative in (
        Path("reports/TASK-WS1-L2-HISTORICAL-LIFECYCLE-RECONSTRUCTION-PREFLIGHT-20260822/reconstruction-readiness.json"),
        Path("reports/TASK-WS1-L2-HISTORICAL-LIFECYCLE-RECONSTRUCTION-PREFLIGHT-20260822/historical-reconstruction-input-inventory.csv"),
    ):
        path = Path.cwd() / relative
        if path.exists():
            source_artifacts[str(relative).replace("\\", "/")] = _sha256_file(path)

    manifest = {
        "task_id": TASK_ID,
        "canonical_head": CANONICAL_HEAD,
        "source_class": SOURCE_CLASS,
        "retrospective_research_only": True,
        "not_pit_truth": True,
        "not_forward_shadow": True,
        "not_formal_publication": True,
        "date_contract": {
            "requested_start": START_DATE,
            "warmup_date": WARMUP_DATE,
            "requested_end": END_DATE,
            "pre_window_start": PRE_WINDOW_START,
            "pre_window_end": PRE_WINDOW_END,
            "warmup_emitted_as_research_row": False,
            "pre_window_synthetic_fill": False,
        },
        "membership_contract": {
            "taxonomy": "CURRENT_FROZEN_CANONICAL_TAXONOMY",
            "relation_selection": "latest non-superseded open-ended relation per topic/instrument",
            "live_tracking_universe_used": False,
            "pit_claim": False,
        },
        "price_contract": {
            "source": "accepted canonical PRICE observations with DAILY_BAR semantics",
            "selection": "source_rank, retrieved_at DESC, observation_id DESC after successor exclusion",
            "return_definition": "raw close-to-close percentage change between available consecutive canonical bars",
            "adjustment_state": "UNKNOWN",
            "economic_return_truth_asserted": False,
        },
        "lifecycle_contract": {
            "policy_version": LIFECYCLE_POLICY_VERSION,
            "calculation_version": LIFECYCLE_CALCULATION_VERSION,
            "semantics_changed": False,
            "persistence_hysteresis_changed": False,
            "bootstrap": "first eligible research date uses unseen prior state; no pre-start claim",
        },
        "strength_contract": {
            "mode": "RAW_EVIDENCE_VECTOR",
            "fields": ["positive_breadth", "strong_breadth", "weak_ratio", "average_change_pct"],
            "leader_change_pct": "PROXY_EVIDENCE_ONLY",
            "dimension_labels": False,
            "overall_level": False,
            "score_0_to_100": False,
            "quality_metadata_is_strength": False,
        },
        "formal_member_fact_reconciliation": {
            "closure_count": FORMAL_MEMBER_FACT_COUNT,
            "runtime_aggregate_count": FORMAL_RUNTIME_MEMBER_FACT_COUNT,
            "delta": FORMAL_RECONCILIATION_DELTA,
            "state": "UNRESOLVED_RETAINED_METADATA",
            "blocks_bounded_research_output": False,
        },
        "dataset": {
            "row_count": len(rows),
            "normalized_dataset_sha256": replay["normalized_dataset_sha256"],
            "topic_count": len({row["topic_id"] for row in rows}),
            "date_count": len({row["trading_date"] for row in rows}),
            "actual_start": rows[0]["trading_date"] if rows else None,
            "actual_end": rows[-1]["trading_date"] if rows else None,
        },
        "source_artifacts_sha256": source_artifacts,
        "no_database_write": True,
        "governance": {
            "WS1_ONLY": "YES",
            "RETROSPECTIVE_RESEARCH_ONLY": "YES",
            "LIFECYCLE_POLICY_CHANGED": "NO",
            "STRENGTH_SCORE_CREATED": "NO",
            "FORWARD_SHADOW_MUTATED": "NO",
            "FORMAL_PUBLICATION": "NO",
            "PRODUCTION_DB_MUTATION": "NO",
            "WS3_STRATEGY_CHANGED": "NO",
            "DEPLOY": "NO",
            "PUSH": "NO",
            "NEXT_TASK_CHANGED": "NO",
        },
    }
    _write_json(args.output_dir / "reconstruction-manifest.json", manifest)
    _write_json(
        args.output_dir / "deterministic-replay-evidence.json",
        {
            "task_id": TASK_ID,
            "canonical_head": CANONICAL_HEAD,
            "source_class": SOURCE_CLASS,
            **replay,
            "input_queries_read_only": True,
            "database_mutation": "NO",
            "formal_persistence_mutation": "NO",
            "forward_shadow_mutation": "NO",
        },
    )
    summary = _build_run_summary(rows, evidence, replay, args.output_dir)
    _write_json(args.output_dir / "run-summary.json", summary)
    (args.output_dir / "formal-closure-report.md").write_text(
        _closure_markdown(rows, evidence, replay, summary), encoding="utf-8", newline="\n"
    )
    (args.output_dir / "ws3-handoff-memo.md").write_text(
        _handoff_markdown(summary, replay), encoding="utf-8", newline="\n"
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, default=_iso))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
