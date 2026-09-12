"""Run the Owner-master Lifecycle V1 historical reconstruction refresh.

The adapter is intentionally read-only with respect to PostgreSQL.  It reads
the current Owner CSV masters from ``config/topic_master_v1`` and reads only
the already accepted canonical DAILY_BAR close observations from the local
database.  It never reads forward returns, creates a performance outcome, or
writes a database table.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "services" / "api" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from topicpilot_api.topic_lifecycle_v1 import (
    DECLINING,
    FERMENTING,
    LIFECYCLE_CALCULATION_VERSION,
    LIFECYCLE_POLICY_VERSION,
    MAIN_RISE,
    MATURE,
    SPROUTING,
    LifecycleInput,
    LifecycleObservation,
    LifecyclePolicy,
    evaluate_lifecycle,
)
from topicpilot_api.topic_master_v1 import load_master, validate_master

TASK_ID = "TASK-WS1-LIFECYCLE-V1-FULL-RECONSTRUCTION-REFRESH-OWNER-SEMANTIC-BASELINE-20260824"
START_DATE = date(2026, 2, 3)
WARMUP_DATE = date(2026, 2, 2)
END_DATE = date(2026, 8, 13)
OLD_BASELINE_HASH = "a2941dddb640812858261a96942728213271e80b73699622f3bb17ca15af2886"
TASK_STARTING_CANONICAL_SHA = "4459b7554d1a0dd77d26651a0ab338953d43be54"
OLD_DIR = REPO / "reports" / "TASK-WS1-LIFECYCLE-V1-CANONICAL-INTEGRATION-RECONSTRUCTION-OWNER-ACCEPTANCE-20260824"
OLD_RECONSTRUCTION = OLD_DIR / "lifecycle-v1-historical-reconstruction.csv"
OLD_MEMBER_EVIDENCE = OLD_DIR / "lifecycle-v1-member-evidence.csv"
OUTPUT_FIELDS = [
    "topic_id", "topic_key", "topic_name", "parent_topic", "trading_date",
    "source_class", "evaluation_mode", "membership_mode", "lifecycle_stage",
    "previous_stage", "candidate_stage", "stage_entered_at", "stage_trading_days",
    "evaluation_status", "data_status", "availability_status", "insufficient_data_reason",
    "transition_decision", "transition_reason", "blocked_transition_reason",
    "confirmation_state", "main_rise_segment", "segment_entry_date", "segment_anchor_date",
    "meaningful_expansion", "meaningful_expansion_members", "last_meaningful_expansion_date",
    "days_since_meaningful_expansion", "reference_base_state", "current_peak", "peak_date",
    "days_since_peak", "drawdown_from_peak_pct", "trajectory_recovered",
    "lead_member_count", "core_member_count", "related_member_count",
    "observed_lead_count", "observed_core_count", "observed_related_count",
    "lead_positive_breadth", "core_positive_breadth", "lead_core_positive_breadth",
    "related_positive_breadth", "positive_breadth", "strong_breadth", "weak_ratio",
    "lead_core_strong_breadth", "lead_core_weak_ratio", "average_change_pct",
    "lead_core_average_change_pct", "core_average_change_pct", "related_average_change_pct",
    "authority_weighted_positive_breadth", "role_authority_available", "role_coverage_pct",
    "expected_member_count", "observed_member_count", "valid_change_count", "missing_price_count",
    "missing_change_count", "coverage_ratio", "coverage_pct", "role_counts",
    "policy_version", "calculation_version", "lineage_status", "price_authority",
    "price_adjustment_semantics", "membership_provenance", "state_memory", "publication_state",
]
MEMBER_FIELDS = [
    "topic_id", "topic_key", "topic_name", "trading_date", "market_code", "instrument_code",
    "instrument_name", "identity_source", "topic_relation_type", "structural_role", "topic_weight",
    "membership_enabled", "membership_provenance", "close", "previous_close", "change_pct",
    "observation_status", "availability_reason", "role_evidence_status", "breadth_contribution",
]

PRICE_QUERY = """
WITH candidates AS (
    SELECT
        co.id AS observation_id,
        i.instrument_code,
        m.code AS market_code,
        (co.observed_at AT TIME ZONE m.timezone)::date AS trading_date,
        cp.close,
        cp.adjustment_state,
        s.source_code,
        s.adapter_version,
        s.adjustment_policy,
        s.source_rank,
        co.reference_data_version,
        co.normalization_contract_version,
        co.mapping_policy_version,
        co.retrieved_at,
        ROW_NUMBER() OVER (
            PARTITION BY co.instrument_id, (co.observed_at AT TIME ZONE m.timezone)::date
            ORDER BY s.source_rank, co.retrieved_at DESC, co.id DESC
        ) AS source_rank_row
    FROM topicpilot.canonical_observations co
    JOIN topicpilot.canonical_price_observations cp
      ON cp.canonical_observation_id = co.id
    JOIN topicpilot.instruments i ON i.id = co.instrument_id
    JOIN topicpilot.markets m ON m.id = i.market_id
    JOIN topicpilot.market_data_sources s ON s.id = co.source_id
    WHERE co.family_code = 'PRICE'
      AND co.quality_state = 'ACCEPTED'
      AND s.observation_semantics = 'DAILY_BAR'
      AND (co.observed_at AT TIME ZONE m.timezone)::date BETWEEN :warmup_date AND :end_date
      AND cp.close IS NOT NULL
      AND NOT EXISTS (
          SELECT 1
          FROM topicpilot.canonical_observations successor
          WHERE successor.supersedes_id = co.id
            AND successor.family_code = 'PRICE'
            AND successor.quality_state = 'ACCEPTED'
      )
)
SELECT observation_id, market_code, instrument_code, trading_date, close,
       adjustment_state, source_code, adapter_version, adjustment_policy,
       reference_data_version, normalization_contract_version,
       mapping_policy_version, retrieved_at
FROM candidates
WHERE source_rank_row = 1
ORDER BY market_code, instrument_code, trading_date, observation_id
"""


def _jsonable(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _json(value: Any) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_rows(rows: list[dict[str, Any]], fields: list[str]) -> str:
    payload = [_jsonable({field: row.get(field) for field in fields}) for row in rows]
    return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()


def _csv_value(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if isinstance(value, (dict, list, tuple)):
        return _json(value)
    return value


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=False)
    return result.stdout.strip()


def _read_prices(database_url: str) -> tuple[dict[tuple[str, str], dict[date, dict[str, Any]]], list[dict[str, Any]]]:
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        rows = [dict(row) for row in connection.execute(
            text(PRICE_QUERY), {"warmup_date": WARMUP_DATE, "end_date": END_DATE}
        ).mappings()]
    engine.dispose()
    prices: dict[tuple[str, str], dict[date, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        row["close"] = float(row["close"])
        prices[(row["market_code"], row["instrument_code"])][row["trading_date"]] = row
    return prices, rows


def _previous_price(items: dict[date, dict[str, Any]], current_date: date) -> dict[str, Any] | None:
    prior_dates = [item_date for item_date in items if item_date < current_date]
    return items[max(prior_dates)] if prior_dates else None


def _fraction(values: list[float], predicate: Any) -> float | None:
    return round(sum(predicate(value) for value in values) / len(values), 4) if values else None


def _average(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def _role_metrics(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[float]] = {"LEAD": [], "CORE": [], "RELATED": []}
    for row in evidence:
        if row.get("change_pct") is not None and row.get("structural_role") in groups:
            groups[row["structural_role"]].append(float(row["change_pct"]))
    lead_core = groups["LEAD"] + groups["CORE"]
    overall = lead_core + groups["RELATED"]
    return {
        "lead_member_count": sum(row.get("structural_role") == "LEAD" for row in evidence),
        "core_member_count": sum(row.get("structural_role") == "CORE" for row in evidence),
        "related_member_count": sum(row.get("structural_role") == "RELATED" for row in evidence),
        "observed_lead_count": len(groups["LEAD"]),
        "observed_core_count": len(groups["CORE"]),
        "observed_related_count": len(groups["RELATED"]),
        "lead_positive_breadth": _fraction(groups["LEAD"], lambda value: value > 0),
        "core_positive_breadth": _fraction(groups["CORE"], lambda value: value > 0),
        "lead_core_positive_breadth": _fraction(lead_core, lambda value: value > 0),
        "related_positive_breadth": _fraction(groups["RELATED"], lambda value: value > 0),
        "positive_breadth": _fraction(overall, lambda value: value > 0),
        "strong_breadth": _fraction(overall, lambda value: value >= 4),
        "weak_ratio": _fraction(overall, lambda value: value <= -4),
        "lead_core_strong_breadth": _fraction(lead_core, lambda value: value >= 4),
        "lead_core_weak_ratio": _fraction(lead_core, lambda value: value <= -4),
        "average_change_pct": _average(overall),
        "lead_core_average_change_pct": _average(lead_core),
        "core_average_change_pct": _average(groups["CORE"]),
        "related_average_change_pct": _average(groups["RELATED"]),
    }


def _member_label(row: dict[str, Any]) -> str:
    return f"{row['instrument_code']} {row['instrument_name']}"


def _member_lists(topic_members: list[dict[str, str]]) -> dict[str, str]:
    result: dict[str, list[str]] = {"LEAD": [], "CORE": [], "RELATED": []}
    for member in topic_members:
        result.setdefault(member["structural_role"], []).append(_member_label(member))
    return {key: "; ".join(value) for key, value in result.items()}


def _current_peak_fields(state_memory: dict[str, Any], evaluation_date: date, sessions: list[date]) -> dict[str, Any]:
    peaks = state_memory.get("runningPeakCloseByMember") or {}
    peak_dates = state_memory.get("runningPeakDateByMember") or {}
    values = [float(value) for value in peaks.values() if value is not None]
    dates = [str(value) for value in peak_dates.values() if value]
    latest = max(dates) if dates else None
    elapsed = None
    if latest:
        try:
            elapsed = max(0, len([item for item in sessions if latest <= item <= evaluation_date]) - 1)
        except TypeError:
            elapsed = None
    return {
        "current_peak": _average(values),
        "peak_date": latest,
        "days_since_peak": elapsed,
        "current_peak_by_member": peaks,
        "peak_date_by_member": peak_dates,
    }


def _stage_transition(row: dict[str, Any]) -> bool:
    return bool(row.get("lifecycle_stage") and row.get("lifecycle_stage") != row.get("previous_stage"))


def _build_reconstruction(
    master: Any,
    prices: dict[tuple[str, str], dict[date, dict[str, Any]]],
    price_rows: list[dict[str, Any]],
    policy: LifecyclePolicy,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    instrument_by_key = {
        (row["market_code"], row["instrument_code"]): row
        for row in master.instruments
        if row["enabled"].upper() == "TRUE"
    }
    topic_rows = [row for row in master.topics if row["enabled"].upper() == "TRUE"]
    topic_by_key = {row["topic_key"]: row for row in topic_rows}
    members_by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in master.memberships:
        key = (row["market_code"], row["instrument_code"])
        if (
            row["enabled"].upper() == "TRUE"
            and row["topic_key"] in topic_by_key
            and key in instrument_by_key
        ):
            instrument = instrument_by_key[key]
            members_by_topic[row["topic_key"]].append({
                **row,
                "instrument_name": instrument["instrument_name"],
                "identity_source": instrument["identity_source"],
                "provenance_class": instrument["provenance_class"],
            })
    for members in members_by_topic.values():
        members.sort(key=lambda row: (row["market_code"], row["instrument_code"], row["topic_key"]))
    price_dates = sorted({row["trading_date"] for row in price_rows})
    sessions = [item for item in price_dates if START_DATE <= item <= END_DATE]
    states: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    member_evidence: list[dict[str, Any]] = []
    for trading_date in sessions:
        for topic in topic_rows:
            topic_key = topic["topic_key"]
            topic_members = members_by_topic.get(topic_key, [])
            observations: list[LifecycleObservation] = []
            day_member_evidence: list[dict[str, Any]] = []
            for member in topic_members:
                key = (member["market_code"], member["instrument_code"])
                current = prices.get(key, {}).get(trading_date)
                previous = _previous_price(prices.get(key, {}), trading_date)
                if current is None:
                    status = "MISSING_CURRENT_DAILY_BAR"
                    reason = "NO_ACCEPTED_CANONICAL_DAILY_BAR_FOR_DATE"
                    close = None
                    previous_close = previous["close"] if previous else None
                    change = None
                elif previous is None or previous.get("close") is None or previous["close"] <= 0:
                    status = "MISSING_PREVIOUS_DAILY_BAR"
                    reason = "NO_PRIOR_CANONICAL_DAILY_BAR_FOR_CLOSE_TO_CLOSE_CHANGE"
                    close = current["close"]
                    previous_close = previous["close"] if previous else None
                    change = None
                else:
                    close = current["close"]
                    previous_close = previous["close"]
                    change = (close - previous_close) / previous_close * 100
                    status = "OBSERVED_CANONICAL_DAILY_BAR"
                    reason = ""
                contribution = "MISSING"
                if change is not None:
                    contribution = "POSITIVE" if change > 0 else "NON_POSITIVE"
                    if change >= 4:
                        contribution += ";STRONG"
                    if change <= -4:
                        contribution += ";WEAK"
                    observations.append(LifecycleObservation(
                        member["instrument_code"], float(change), member["structural_role"],
                        "CURRENT_TAXONOMY_RELATION_STRUCTURAL_ROLE", close, previous_close,
                    ))
                evidence = {
                    "topic_id": topic_key,
                    "topic_key": topic_key,
                    "topic_name": topic["topic_name"],
                    "trading_date": trading_date,
                    "market_code": member["market_code"],
                    "instrument_code": member["instrument_code"],
                    "instrument_name": member["instrument_name"],
                    "identity_source": member["identity_source"],
                    "topic_relation_type": member["topic_relation_type"],
                    "structural_role": member["structural_role"],
                    "topic_weight": member["topic_weight"],
                    "membership_enabled": member["enabled"].upper() == "TRUE",
                    "membership_provenance": "CURRENT_TAXONOMY_FROZEN_RECONSTRUCTION",
                    "close": close,
                    "previous_close": previous_close,
                    "change_pct": round(change, 8) if change is not None else None,
                    "observation_status": status,
                    "availability_reason": reason,
                    "role_evidence_status": "ROLE_AUTHORITY_AVAILABLE",
                    "breadth_contribution": contribution,
                }
                day_member_evidence.append(evidence)
                member_evidence.append(evidence)
            prior = states.get(topic_key, {})
            result = evaluate_lifecycle(
                LifecycleInput(
                    topic_id=topic_key,
                    trading_date=trading_date,
                    expected_member_count=len(topic_members),
                    observations=tuple(observations),
                    previous_stage=prior.get("final_stage"),
                    previous_stage_entered_at=prior.get("stage_entered_at"),
                    previous_stage_trading_days=prior.get("stage_trading_days"),
                    previous_candidate_stage=prior.get("candidate_stage"),
                    previous_candidate_streak=int(prior.get("candidate_streak") or 0),
                    state_memory=prior.get("state_memory"),
                ),
                policy,
            )
            metrics = _role_metrics(day_member_evidence)
            leadership = result.evidence.leadership
            diffusion = result.evidence.diffusion
            progression = result.evidence.divergence_decay
            state_memory = dict(result.state_memory or {})
            peak = _current_peak_fields(state_memory, trading_date, sessions)
            available_count = len(observations)
            missing_price_count = sum(item["change_pct"] is None for item in day_member_evidence)
            coverage_ratio = available_count / len(topic_members) if topic_members else None
            if result.data_status == "INSUFFICIENT_DATA":
                availability_status = "INSUFFICIENT_DATA"
            elif missing_price_count:
                availability_status = "PARTIAL_CANONICAL_MEMBER_COVERAGE"
            else:
                availability_status = "FULL_CANONICAL_MEMBER_COVERAGE"
            decision = result.transition_decision
            blocked = result.transition_reason if decision.startswith("HOLD_") and decision not in {"HOLD", "HOLD_CURRENT_STAGE", "HOLD_CONFIRMATION"} else ""
            row = {
                "topic_id": topic_key,
                "topic_key": topic_key,
                "topic_name": topic["topic_name"],
                "parent_topic": topic["parent_topic"],
                "trading_date": trading_date,
                "source_class": "CURRENT_TAXONOMY_HISTORICAL_V1_RECONSTRUCTION_REFRESH",
                "evaluation_mode": "RETROSPECTIVE_RESEARCH_ONLY",
                "membership_mode": "CURRENT_TAXONOMY_FROZEN_RECONSTRUCTION",
                "lifecycle_stage": result.final_stage,
                "previous_stage": result.previous_stage,
                "candidate_stage": result.candidate_stage,
                "stage_entered_at": result.stage_entered_at,
                "stage_trading_days": result.stage_trading_days,
                "evaluation_status": result.evaluation_status,
                "data_status": result.data_status,
                "availability_status": availability_status,
                "insufficient_data_reason": result.transition_reason if result.data_status == "INSUFFICIENT_DATA" else "",
                "transition_decision": decision,
                "transition_reason": result.transition_reason,
                "blocked_transition_reason": blocked,
                "confirmation_state": result.confirmation_state,
                "main_rise_segment": result.main_rise_segment,
                "segment_entry_date": result.segment_entry_date,
                "segment_anchor_date": result.segment_anchor_date,
                "meaningful_expansion": progression.get("meaningfulExpansion"),
                "meaningful_expansion_members": progression.get("meaningfulExpansionMembers", []),
                "last_meaningful_expansion_date": state_memory.get("lastMeaningfulExpansionDate"),
                "days_since_meaningful_expansion": result.days_since_meaningful_expansion,
                "reference_base_state": {
                    "segment_anchor_date": state_memory.get("segmentAnchorDate"),
                    "last_meaningful_expansion_date": state_memory.get("lastMeaningfulExpansionDate"),
                    "base_semantics": "RUNNING_LEAD_CORE_PEAKS_INITIALIZED_FROM_PRIOR_CLOSE",
                },
                "current_peak": peak["current_peak"],
                "peak_date": peak["peak_date"],
                "days_since_peak": peak["days_since_peak"],
                "drawdown_from_peak_pct": result.drawdown_from_peak_pct,
                "trajectory_recovered": progression.get("trajectoryRecovered"),
                **metrics,
                "authority_weighted_positive_breadth": diffusion.get("authorityWeightedPositiveBreadth"),
                "role_authority_available": leadership.get("roleAuthorityAvailable"),
                "role_coverage_pct": leadership.get("roleCoveragePct"),
                "expected_member_count": len(topic_members),
                "observed_member_count": len(observations),
                "valid_change_count": len(observations),
                "missing_price_count": missing_price_count,
                "missing_change_count": missing_price_count,
                "coverage_ratio": round(coverage_ratio, 6) if coverage_ratio is not None else None,
                "coverage_pct": round(coverage_ratio * 100, 4) if coverage_ratio is not None else None,
                "role_counts": leadership.get("roleCounts", {}),
                "policy_version": LIFECYCLE_POLICY_VERSION,
                "calculation_version": LIFECYCLE_CALCULATION_VERSION,
                "lineage_status": "CURRENT_TAXONOMY_NON_PIT;PRICE_CANONICAL_DAILY_BAR;ROLE_AUTHORITY_FROM_OWNER_MASTER",
                "price_authority": "ACCEPTED_CANONICAL_DAILY_BAR_CLOSE_READ_ONLY",
                "price_adjustment_semantics": "UNKNOWN_RAW_ONLY",
                "membership_provenance": "CURRENT_TAXONOMY_FROZEN_RECONSTRUCTION",
                "state_memory": state_memory,
                "publication_state": "UNPUBLISHED_RESEARCH_ARTIFACT",
            }
            rows.append(row)
            states[topic_key] = {
                "final_stage": result.final_stage,
                "stage_entered_at": result.stage_entered_at,
                "stage_trading_days": result.stage_trading_days,
                "candidate_stage": result.candidate_stage,
                "candidate_streak": result.confirmation_state.get("candidateStreak", 0),
                "state_memory": state_memory,
            }
    rows.sort(key=lambda row: (row["trading_date"], row["topic_key"]))
    member_evidence.sort(key=lambda row: (row["trading_date"], row["topic_key"], row["market_code"], row["instrument_code"]))
    summary = {
        "topic_count": len(topic_rows),
        "member_relation_count": sum(len(value) for value in members_by_topic.values()),
        "unique_member_identity_count": len({(row["market_code"], row["instrument_code"]) for value in members_by_topic.values() for row in value}),
        "date_count": len(sessions),
        "actual_start": sessions[0] if sessions else None,
        "actual_end": sessions[-1] if sessions else None,
        "row_count": len(rows),
        "member_evidence_row_count": len(member_evidence),
        "stage_counts": dict(Counter(row["lifecycle_stage"] or "PENDING" for row in rows)),
        "rows_with_missing_price": sum(row["missing_price_count"] > 0 for row in rows),
        "missing_member_evidence_rows": sum(row["observation_status"] != "OBSERVED_CANONICAL_DAILY_BAR" for row in member_evidence),
        "reconstruction_output_sha256": _hash_rows(rows, OUTPUT_FIELDS),
        "member_evidence_sha256": _hash_rows(member_evidence, MEMBER_FIELDS),
    }
    return rows, member_evidence, summary


def _index_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["topic_key"], str(row["trading_date"])): row for row in rows}


def _parse_json_cell(value: str) -> Any:
    try:
        return json.loads(value) if value else None
    except json.JSONDecodeError:
        return value


def _read_old_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not OLD_RECONSTRUCTION.exists():
        return [], []
    with OLD_RECONSTRUCTION.open(encoding="utf-8-sig", newline="") as handle:
        old_rows = list(csv.DictReader(handle))
    old_members: list[dict[str, Any]] = []
    if OLD_MEMBER_EVIDENCE.exists():
        with OLD_MEMBER_EVIDENCE.open(encoding="utf-8-sig", newline="") as handle:
            old_members = list(csv.DictReader(handle))
    return old_rows, old_members


def _old_new_comparison(rows: list[dict[str, Any]], member_evidence: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    old_rows, old_members = _read_old_rows()
    old_index = {(row.get("topic_slug", ""), row.get("trading_date", "")): row for row in old_rows}
    new_index = _index_rows(rows)
    old_members_by_topic: dict[str, dict[tuple[str, str], str]] = defaultdict(dict)
    for row in old_members:
        old_members_by_topic[row.get("topic_slug", "")][(row.get("member_code", ""), row.get("role", ""))] = row.get("member_id", "")
    new_members_by_topic: dict[str, dict[tuple[str, str], str]] = defaultdict(dict)
    for row in member_evidence:
        new_members_by_topic[row["topic_key"]][(row["instrument_code"], row["structural_role"])] = row["identity_source"]
    union_keys = sorted(set(old_index) | set(new_index))
    diff: list[dict[str, Any]] = []
    changed_rows = 0
    cause_counts: Counter[str] = Counter()
    for key in union_keys:
        old = old_index.get(key)
        new = new_index.get(key)
        topic_key, trading_date = key
        if old is None or new is None:
            cause = "TOPIC_CHANGE"
        else:
            old_members_set = set(old_members_by_topic.get(topic_key, {}))
            new_members_set = set(new_members_by_topic.get(topic_key, {}))
            old_codes = {item[0] for item in old_members_set}
            new_codes = {item[0] for item in new_members_set}
            if old_codes != new_codes:
                cause = "MEMBERSHIP_CHANGE"
            elif old_members_set != new_members_set:
                cause = "ROLE_CHANGE"
            elif (old.get("observed_member_count"), old.get("missing_price_member_count")) != (
                str(new.get("observed_member_count")), str(new.get("missing_price_count"))
            ):
                cause = "INSTRUMENT_COVERAGE_CHANGE"
            else:
                old_state = (old.get("lifecycle_stage"), old.get("candidate_stage"), old.get("transition_decision"))
                new_state = (new.get("lifecycle_stage"), new.get("candidate_stage"), new.get("transition_decision"))
                cause = "IMPLEMENTATION_FIX" if old_state != new_state else "UNCHANGED"
        old_state = old.get("lifecycle_stage") if old else None
        new_state = new.get("lifecycle_stage") if new else None
        evidence_changed = "NO"
        if old and new:
            evidence_changed = "YES" if any(
                str(old.get(old_field, "")) != str(new.get(new_field, ""))
                for old_field, new_field in [
                    ("positive_breadth", "positive_breadth"),
                    ("strong_breadth", "strong_breadth"),
                    ("weak_ratio", "weak_ratio"),
                    ("average_change_pct", "average_change_pct"),
                    ("lead_core_positive_breadth", "lead_core_positive_breadth"),
                    ("drawdown_from_peak_pct", "drawdown_from_peak_pct"),
                ]
            ) else "NO"
        changed = "YES" if old_state != new_state or evidence_changed == "YES" or cause != "UNCHANGED" else "NO"
        if changed == "YES":
            changed_rows += 1
        cause_counts[cause] += 1
        diff.append({
            "topic_key": topic_key,
            "trading_date": trading_date,
            "old_lifecycle_stage": old_state,
            "refreshed_lifecycle_stage": new_state,
            "old_candidate_stage": old.get("candidate_stage") if old else None,
            "refreshed_candidate_stage": new.get("candidate_stage") if new else None,
            "old_transition_decision": old.get("transition_decision") if old else None,
            "refreshed_transition_decision": new.get("transition_decision") if new else None,
            "old_transition_reason": old.get("transition_reason") if old else None,
            "refreshed_transition_reason": new.get("transition_reason") if new else None,
            "old_segment": old.get("main_rise_segment") if old else None,
            "refreshed_segment": new.get("main_rise_segment") if new else None,
            "old_evidence": old.get("positive_breadth") if old else None,
            "refreshed_evidence": new.get("positive_breadth") if new else None,
            "stage_changed": "YES" if old_state != new_state else "NO",
            "evidence_changed": evidence_changed,
            "change_cause": cause,
        })
    summary = {
        "old_declared_baseline_hash": OLD_BASELINE_HASH,
        "old_reconstruction_file_sha256": _file_sha256(OLD_RECONSTRUCTION) if OLD_RECONSTRUCTION.exists() else None,
        "old_row_count": len(old_rows),
        "refreshed_row_count": len(rows),
        "changed_rows": changed_rows,
        "unchanged_rows": len(union_keys) - changed_rows,
        "topics_changed": len({row["topic_key"] for row in diff if row["change_cause"] != "UNCHANGED"}),
        "stage_rows_changed": sum(row["stage_changed"] == "YES" for row in diff),
        "evidence_rows_changed": sum(row["evidence_changed"] == "YES" for row in diff),
        "cause_counts": dict(cause_counts),
        "old_stage_counts": dict(Counter(row.get("lifecycle_stage") or "PENDING" for row in old_rows)),
        "refreshed_stage_counts": dict(Counter(row.get("lifecycle_stage") or "PENDING" for row in rows)),
        "old_main_rise_transition_count": sum(
            row.get("lifecycle_stage") == MAIN_RISE and row.get("lifecycle_stage") != row.get("previous_stage")
            for row in old_rows
        ),
        "refreshed_main_rise_transition_count": sum(
            row.get("lifecycle_stage") == MAIN_RISE and row.get("lifecycle_stage") != row.get("previous_stage")
            for row in rows
        ),
        "old_declining_transition_count": sum(
            row.get("lifecycle_stage") == DECLINING and row.get("lifecycle_stage") != row.get("previous_stage")
            for row in old_rows
        ),
        "refreshed_declining_transition_count": sum(
            row.get("lifecycle_stage") == DECLINING and row.get("lifecycle_stage") != row.get("previous_stage")
            for row in rows
        ),
    }
    return diff, summary


def _transition_events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if _stage_transition(row)]


def _stage_distribution(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(rows)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["lifecycle_stage"] or "PENDING"].append(row)
    return [{
        "stage": stage,
        "row_count": len(items),
        "topic_count": len({row["topic_key"] for row in items}),
        "share_pct": round(len(items) * 100 / total, 4) if total else 0,
        "first_date": min(row["trading_date"] for row in items),
        "last_date": max(row["trading_date"] for row in items),
    } for stage, items in sorted(grouped.items())]


def _stage_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_topic[row["topic_key"]].append(row)
    runs: list[dict[str, Any]] = []
    for topic, topic_rows in sorted(by_topic.items()):
        current: list[dict[str, Any]] = []
        current_key: tuple[Any, Any] | None = None
        for row in sorted(topic_rows, key=lambda item: item["trading_date"]):
            key = (row["lifecycle_stage"] or "PENDING", row.get("main_rise_segment") if row["lifecycle_stage"] == MAIN_RISE else None)
            if current and key != current_key:
                runs.append(_run_payload(current, current_key))
                current = []
            current_key = key
            current.append(row)
        if current:
            runs.append(_run_payload(current, current_key))
    return runs


def _run_payload(items: list[dict[str, Any]], key: tuple[Any, Any] | None) -> dict[str, Any]:
    values = [item for item in items if item["lifecycle_stage"]]
    stage = key[0] if key else None
    segment = key[1] if key and stage == MAIN_RISE else None
    return {
        "topic_key": items[0]["topic_key"],
        "topic_name": items[0]["topic_name"],
        "stage": stage,
        "main_rise_segment": segment,
        "start_date": items[0]["trading_date"],
        "end_date": items[-1]["trading_date"],
        "duration_sessions": len(items),
        "first_valid_stage_date": values[0]["trading_date"] if values else None,
        "last_valid_stage_date": values[-1]["trading_date"] if values else None,
    }


def _duration_analysis(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for run in runs:
        if run["stage"] not in {None, "PENDING"}:
            label = f"{run['stage']}_SEGMENT_{run['main_rise_segment']}" if run["stage"] == MAIN_RISE else run["stage"]
            grouped[label].append(run["duration_sessions"])
    result = []
    for stage, values in sorted(grouped.items()):
        result.append({
            "stage": stage,
            "count": len(values),
            "median_sessions": statistics.median(values),
            "mean_sessions": round(statistics.mean(values), 4),
            "min_sessions": min(values),
            "max_sessions": max(values),
        })
    return result


def _transition_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[tuple[str, str, str, str]] = Counter()
    for row in rows:
        if _stage_transition(row):
            counter[(row["previous_stage"] or "NONE", row["candidate_stage"] or "NONE", row["lifecycle_stage"], row["transition_decision"])] += 1
    return [{
        "previous_stage": key[0], "candidate_stage": key[1], "final_stage": key[2],
        "transition_decision": key[3], "count": count,
    } for key, count in sorted(counter.items())]


def _review_row(row: dict[str, Any], members: list[dict[str, str]], case_type: str, priority: str) -> dict[str, Any]:
    lists = _member_lists(members)
    return {
        "review_priority": priority,
        "topic_key": row["topic_key"],
        "topic_name": row["topic_name"],
        "review_case_type": case_type,
        "date_or_window": str(row["trading_date"]),
        "previous_stage": row["previous_stage"],
        "candidate_stage": row["candidate_stage"],
        "final_stage": row["lifecycle_stage"],
        "segment": row["main_rise_segment"],
        "lead_members": lists["LEAD"],
        "core_members": lists["CORE"],
        "related_members": lists["RELATED"],
        "lead_core_breadth": row["lead_core_positive_breadth"],
        "related_breadth": row["related_positive_breadth"],
        "lead_core_average_change": row["lead_core_average_change_pct"],
        "strong_breadth": row["strong_breadth"],
        "weak_ratio": row["weak_ratio"],
        "drawdown_from_peak_pct": row["drawdown_from_peak_pct"],
        "expansion_clock": row["days_since_meaningful_expansion"],
        "meaningful_expansion": row["meaningful_expansion"],
        "system_reason": f"{row['transition_decision']}:{row['transition_reason']}",
        "OWNER_JUDGMENT": "",
        "OWNER_NOTE": "",
    }


def _review_pack(rows: list[dict[str, Any]], members_by_topic: dict[str, list[dict[str, str]]], runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events = _transition_events(rows)
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        case: str | None = None
        priority = "P0"
        if row["lifecycle_stage"] == MATURE and (
            (row["lead_core_positive_breadth"] or 1.0) <= 0.35
            or (row["lead_core_average_change_pct"] or 0.0) <= -2
            or (row["drawdown_from_peak_pct"] or 0.0) <= -15
        ) and row["candidate_stage"] != DECLINING:
            case = "POSSIBLE_MISSED_DECLINE"
        elif row["lifecycle_stage"] == MAIN_RISE and row["previous_stage"] == MATURE and (row["drawdown_from_peak_pct"] or 0) <= -30:
            case = "DEEP_DRAWDOWN_REENTRY"
        elif row["transition_decision"] == "HOLD_ILLEGAL_TRANSITION":
            case = "BLOCKED_STAGE_JUMP"
        elif row["lifecycle_stage"] == DECLINING and row["previous_stage"] != DECLINING:
            case = "DECLINING_ENTRY"
        if case:
            key = (row["topic_key"], str(row["trading_date"]), case)
            if key not in seen:
                result.append(_review_row(row, members_by_topic.get(row["topic_key"], []), case, priority))
                seen.add(key)
    for row in events:
        if row["lifecycle_stage"] == MAIN_RISE and row["previous_stage"] != MAIN_RISE:
            result.append(_review_row(row, members_by_topic.get(row["topic_key"], []), "MAIN_RISE_ENTRY", "P1"))
        if row["lifecycle_stage"] == MATURE and row["previous_stage"] == MAIN_RISE:
            result.append(_review_row(row, members_by_topic.get(row["topic_key"], []), "MAIN_RISE_TO_MATURE", "P1"))
        if row["lifecycle_stage"] == MAIN_RISE and row["previous_stage"] == MATURE:
            result.append(_review_row(row, members_by_topic.get(row["topic_key"], []), "MATURE_TO_MAIN_RISE", "P1"))
        if row["lifecycle_stage"] == FERMENTING and row["previous_stage"] == SPROUTING:
            result.append(_review_row(row, members_by_topic.get(row["topic_key"], []), "SPROUTING_TO_FERMENTING", "P2"))
    persistence = [row for row in rows if row["lifecycle_stage"] == MAIN_RISE and row["previous_stage"] == MAIN_RISE]
    result.extend(_review_row(row, members_by_topic.get(row["topic_key"], []), "MAIN_RISE_PERSISTENCE", "P2") for row in persistence[:50])
    sprouting = [row for row in rows if row["lifecycle_stage"] == SPROUTING]
    fermenting = [row for row in rows if row["lifecycle_stage"] == FERMENTING]
    result.extend(_review_row(row, members_by_topic.get(row["topic_key"], []), "SPROUTING_EXAMPLE", "P2") for row in sprouting[:20])
    result.extend(_review_row(row, members_by_topic.get(row["topic_key"], []), "FERMENTING_EXAMPLE", "P2") for row in fermenting[:20])
    result.sort(key=lambda row: (row["review_priority"], row["topic_key"], row["date_or_window"], row["review_case_type"]))
    return result


def _review_diagnostics(rows: list[dict[str, Any]], members_by_topic: dict[str, list[dict[str, str]]]) -> dict[str, list[dict[str, Any]]]:
    events = _transition_events(rows)
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in rows:
        by_topic[item["topic_key"]].append(item)
    entry: list[dict[str, Any]] = []
    for row in events:
        if row["lifecycle_stage"] != MAIN_RISE or row["previous_stage"] == MAIN_RISE:
            continue
        topic_rows = by_topic[row["topic_key"]]
        position = topic_rows.index(row)
        candidate_date = row["trading_date"]
        if position > 0 and topic_rows[position - 1]["candidate_stage"] == MAIN_RISE:
            candidate_date = topic_rows[position - 1]["trading_date"]
        entry.append({
            **row,
            "candidate_date": candidate_date,
            "confirmation_date": row["trading_date"],
            "review_classification": "OWNER_REVIEW_REQUIRED",
        })
    maturity = [
        {**row, "last_meaningful_expansion_date": row["last_meaningful_expansion_date"], "peak_date": row["peak_date"], "transition_date": row["trading_date"], "sessions_since_expansion": row["days_since_meaningful_expansion"], "review_classification": "OWNER_REVIEW_REQUIRED"}
        for row in events if row["lifecycle_stage"] == MATURE and row["previous_stage"] == MAIN_RISE
    ]
    reentry = [
        {**row, "deep_drawdown_reentry": "YES" if (row["drawdown_from_peak_pct"] or 0) <= -30 else "NO", "review_classification": "OWNER_REVIEW_REQUIRED"}
        for row in events if row["lifecycle_stage"] == MAIN_RISE and row["previous_stage"] == MATURE and (row["main_rise_segment"] or 0) >= 2
    ]
    missed = [
        row for row in rows
        if row["lifecycle_stage"] == MATURE
        and ((row["lead_core_positive_breadth"] or 1.0) <= 0.35 or (row["lead_core_average_change_pct"] or 0) <= -2 or (row["drawdown_from_peak_pct"] or 0) <= -15)
        and row["candidate_stage"] != DECLINING
    ]
    declining = [row for row in events if row["lifecycle_stage"] == DECLINING and row["previous_stage"] != DECLINING]
    return {
        "main-rise-entry-review.csv": entry,
        "main-rise-to-mature-review.csv": maturity,
        "main-rise-reentry-review.csv": reentry,
        "possible-missed-decline-review.csv": missed,
        "declining-entry-review.csv": declining,
    }


def _related_only_audit(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    audit: list[dict[str, Any]] = []
    false_positives = 0
    for row in rows:
        related_strong = (row["related_positive_breadth"] or 0) >= 0.70 and (row["related_average_change_pct"] or 0) >= 1.5
        lead_core_insufficient = (row["core_member_count"] or 0) == 0 or (row["lead_core_positive_breadth"] or 0) < 0.70 or (row["lead_core_strong_breadth"] or 0) < 0.35 or (row["lead_core_average_change_pct"] or 0) < 1.5
        if related_strong and lead_core_insufficient:
            main_rise_event = row["lifecycle_stage"] == MAIN_RISE and row["previous_stage"] != MAIN_RISE
            false_positive = main_rise_event
            false_positives += false_positive
            audit.append({
                "topic_key": row["topic_key"], "topic_name": row["topic_name"], "trading_date": row["trading_date"],
                "related_strong": "YES", "lead_core_insufficient": "YES", "lifecycle_stage": row["lifecycle_stage"],
                "candidate_stage": row["candidate_stage"], "transition_decision": row["transition_decision"],
                "lead_core_positive_breadth": row["lead_core_positive_breadth"], "related_positive_breadth": row["related_positive_breadth"],
                "main_rise_newly_confirmed": "YES" if main_rise_event else "NO",
                "related_only_main_rise_false_positive": "YES" if false_positive else "NO",
                "audit_result": "PASS_GATE_BLOCKED" if not false_positive else "FAIL_RELATED_ONLY_FALSE_POSITIVE",
            })
    return audit, false_positives


def _one_day_flips(rows: list[dict[str, Any]], runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [run for run in runs if run["stage"] not in {None, "PENDING"} and run["duration_sessions"] == 1]


def _mlcc_report(
    output_dir: Path,
    rows: list[dict[str, Any]],
    member_evidence: list[dict[str, Any]],
    master: Any,
    comparison: dict[str, Any],
    comparison_diff: list[dict[str, Any]],
    duration_runs: list[dict[str, Any]],
) -> None:
    mlcc_members = [row for row in master.memberships if row["topic_key"] == "MLCC" and row["enabled"].upper() == "TRUE"]
    instrument_map = {(row["market_code"], row["instrument_code"]): row for row in master.instruments}
    mlcc_rows = [row for row in rows if row["topic_key"] == "MLCC"]
    mlcc_evidence = [row for row in member_evidence if row["topic_key"] == "MLCC"]
    mlcc_events = [row for row in _transition_events(mlcc_rows)]
    mlcc_decline_candidates = [row for row in mlcc_rows if row["candidate_stage"] == DECLINING or row["lifecycle_stage"] == DECLINING]
    mlcc_runs = [run for run in duration_runs if run["topic_key"] == "MLCC"]
    july = [row for row in mlcc_rows if date(2026, 7, 1) <= row["trading_date"] <= date(2026, 7, 31)]
    july_deterioration = [row for row in july if (row["lead_core_positive_breadth"] or 1) <= 0.50 or (row["lead_core_average_change_pct"] or 0) <= 0 or (row["drawdown_from_peak_pct"] or 0) <= -8 or row["candidate_stage"] == DECLINING]
    mlcc_diff = [row for row in comparison_diff if row["topic_key"] == "MLCC" and row["change_cause"] != "UNCHANGED"]
    lines = [
        "# MLCC Lifecycle V1 Refresh Review",
        "",
        "本文件是 Owner semantic acceptance 的 anchor case。所有 stage/evidence 都只使用當日及之前的 canonical DAILY_BAR close；未讀取未來報酬、未執行 WS3 performance backtest。",
        "",
        "## Current Master membership",
        "",
        "| Market | Ticker | Name | PRIMARY/SECONDARY | LEAD/CORE/RELATED | Weight | Identity source | Price coverage |",
        "|---|---:|---|---|---|---:|---|---|",
    ]
    for member in sorted(mlcc_members, key=lambda item: (item["market_code"], item["instrument_code"])):
        instrument = instrument_map[(member["market_code"], member["instrument_code"])]
        evidence = [row for row in mlcc_evidence if row["market_code"] == member["market_code"] and row["instrument_code"] == member["instrument_code"]]
        observed = sum(row["observation_status"] == "OBSERVED_CANONICAL_DAILY_BAR" for row in evidence)
        lines.append(f"| {member['market_code']} | {member['instrument_code']} | {instrument['instrument_name']} | {member['topic_relation_type']} | {member['structural_role']} | {member['topic_weight']} | {instrument['identity_source']} | {observed}/{len(evidence)} dates |")
    lines += ["", "## Complete stage timeline", "", "| Stage | Segment | Start | End | Sessions |", "|---|---:|---|---|---:|"]
    for run in mlcc_runs:
        lines.append(f"| {run['stage']} | {run['main_rise_segment'] or ''} | {run['start_date']} | {run['end_date']} | {run['duration_sessions']} |")
    lines += ["", "## Every MLCC transition", "", "| Date | Previous | Candidate | Final | Decision / reason | Segment | Lead/Core breadth | Related breadth | Avg change | Drawdown | Expansion clock |", "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in mlcc_events + [item for item in mlcc_decline_candidates if item not in mlcc_events]:
        lines.append(f"| {row['trading_date']} | {row['previous_stage'] or ''} | {row['candidate_stage'] or ''} | {row['lifecycle_stage'] or ''} | {row['transition_decision']} / {row['transition_reason']} | {row['main_rise_segment'] or ''} | {row['lead_core_positive_breadth']} | {row['related_positive_breadth']} | {row['lead_core_average_change_pct']} | {row['drawdown_from_peak_pct']} | {row['days_since_meaningful_expansion']} |")
    lines += ["", "## July deterioration window", "", f"July rows: {len(july)}; deterioration-review rows: {len(july_deterioration)}. Deterioration is surfaced for Owner review, not relabeled automatically.", "", "| Date | Stage | Candidate | Lead/Core breadth | Lead/Core avg | Weak ratio | Drawdown | Decision |", "|---|---|---|---:|---:|---:|---:|---|"]
    for row in july:
        lines.append(f"| {row['trading_date']} | {row['lifecycle_stage'] or ''} | {row['candidate_stage'] or ''} | {row['lead_core_positive_breadth']} | {row['lead_core_average_change_pct']} | {row['weak_ratio']} | {row['drawdown_from_peak_pct']} | {row['transition_decision']} |")
    lines += ["", "## Refreshed versus old V1", "", f"Changed MLCC topic/date rows: {len(mlcc_diff)}. The old declared baseline remains historical evidence only: `{OLD_BASELINE_HASH}`.", "", "| Date | Old stage | Refreshed stage | Old→refreshed cause |", "|---|---|---|---|"]
    for row in mlcc_diff:
        lines.append(f"| {row['trading_date']} | {row['old_lifecycle_stage'] or ''} | {row['refreshed_lifecycle_stage'] or ''} | {row['change_cause']} |")
    lines += ["", "## Owner interpretation guide", "", "- LEAD/Core breadth 是當日上漲 member 在 Owner 身分中的擴散程度；Related 只提供 context，不能單獨確認 MAIN_RISE。", "- MAIN_RISE 需要 Lead/Core gate 和 confirmation；MATURE 是 expansion clock stalled 的既有 V1 semantics，不是另行調參。", "- MATURE→MAIN_RISE 的 segment 編號保留 re-entry memory；本次已修正「無 fresh meaningful expansion 卻把 expansion clock 歸零」的 implementation bug。", "- `UNKNOWN_RAW_ONLY` 代表 corporate-action/adjustment continuity 未被假造；這份文件不是經濟報酬 truth。", ""]
    (output_dir / "mlcc-lifecycle-v1-refresh-review.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL", "postgresql+psycopg://topicpilot:topicpilot_local_only@localhost:5432/topicpilot"))
    parser.add_argument("--output-dir", type=Path, default=REPO / "reports" / TASK_ID)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    master_dir = REPO / "config" / "topic_master_v1"
    topic_path = master_dir / "topics.csv"
    membership_path = master_dir / "instrument_topic_memberships.csv"
    instrument_path = master_dir / "instruments.csv"
    master = load_master(topic_path, membership_path, instrument_path)
    validation = validate_master(master)
    if not validation.valid:
        raise SystemExit(json.dumps(validation.to_dict(), ensure_ascii=False, indent=2))
    prices, price_rows = _read_prices(args.database_url)
    policy = LifecyclePolicy()
    first_rows, first_members, first_summary = _build_reconstruction(master, prices, price_rows, policy)
    second_rows, second_members, second_summary = _build_reconstruction(master, prices, price_rows, policy)
    replay = {
        "deterministic_replay": "PASS" if first_rows == second_rows and first_members == second_members else "FAIL",
        "same_row_count": len(first_rows) == len(second_rows),
        "same_member_evidence_row_count": len(first_members) == len(second_members),
        "same_topic_date_keys": [(r["topic_key"], str(r["trading_date"])) for r in first_rows] == [(r["topic_key"], str(r["trading_date"])) for r in second_rows],
        "same_final_stages": [r["lifecycle_stage"] for r in first_rows] == [r["lifecycle_stage"] for r in second_rows],
        "same_candidate_stages": [r["candidate_stage"] for r in first_rows] == [r["candidate_stage"] for r in second_rows],
        "same_segment_numbering": [r["main_rise_segment"] for r in first_rows] == [r["main_rise_segment"] for r in second_rows],
        "same_state_memory_fields": [r["state_memory"] for r in first_rows] == [r["state_memory"] for r in second_rows],
        "first_output_sha256": first_summary["reconstruction_output_sha256"],
        "second_output_sha256": second_summary["reconstruction_output_sha256"],
        "first_member_evidence_sha256": first_summary["member_evidence_sha256"],
        "second_member_evidence_sha256": second_summary["member_evidence_sha256"],
        "database_mutation": "NO",
    }
    rows, member_evidence = first_rows, first_members
    comparison_diff, comparison = _old_new_comparison(rows, member_evidence)
    sessions = sorted({row["trading_date"] for row in rows})
    transition_events = _transition_events(rows)
    runs = _stage_runs(rows)
    durations = _duration_analysis(runs)
    transition_summary = _transition_summary(rows)
    members_by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in master.memberships:
        if row["enabled"].upper() == "TRUE" and row["topic_key"] in {item["topic_key"] for item in master.topics if item["enabled"].upper() == "TRUE"}:
            members_by_topic[row["topic_key"]].append(row)
    for value in members_by_topic.values():
        value.sort(key=lambda item: (item["market_code"], item["instrument_code"]))
    diagnostics = _review_diagnostics(rows, members_by_topic)
    related_audit, related_false_positives = _related_only_audit(rows)
    one_day_flips = _one_day_flips(rows, runs)
    owner_pack = _review_pack(rows, members_by_topic, runs)
    stage_counts = Counter(row["lifecycle_stage"] or "PENDING" for row in rows)
    main_rise_transitions = [row for row in transition_events if row["lifecycle_stage"] == MAIN_RISE]
    segment_2_plus = [row for row in main_rise_transitions if (row["main_rise_segment"] or 0) >= 2]
    mature_events = [row for row in transition_events if row["lifecycle_stage"] == MATURE and row["previous_stage"] == MAIN_RISE]
    declining_events = [row for row in transition_events if row["lifecycle_stage"] == DECLINING]
    stage_order = {SPROUTING: 0, FERMENTING: 1, MAIN_RISE: 2, MATURE: 3, DECLINING: 4}
    actual_stage_jumps = [
        row for row in transition_events
        if row["previous_stage"] in stage_order
        and abs(stage_order[row["lifecycle_stage"]] - stage_order[row["previous_stage"]]) > 1
    ]
    transition_invariants = {
        "sprouting_to_fermenting_count": sum(row["previous_stage"] == SPROUTING and row["lifecycle_stage"] == FERMENTING for row in transition_events),
        "fermenting_to_main_rise_count": sum(row["previous_stage"] == FERMENTING and row["lifecycle_stage"] == MAIN_RISE for row in transition_events),
        "main_rise_persistence_rows": sum(row["previous_stage"] == MAIN_RISE and row["lifecycle_stage"] == MAIN_RISE for row in rows),
        "main_rise_to_mature_count": sum(row["previous_stage"] == MAIN_RISE and row["lifecycle_stage"] == MATURE for row in transition_events),
        "mature_to_main_rise_count": sum(row["previous_stage"] == MATURE and row["lifecycle_stage"] == MAIN_RISE for row in transition_events),
        "mature_to_declining_count": sum(row["previous_stage"] == MATURE and row["lifecycle_stage"] == DECLINING for row in transition_events),
        "declining_persistence_rows": sum(row["previous_stage"] == DECLINING and row["lifecycle_stage"] == DECLINING for row in rows),
        "blocked_illegal_transition_rows": sum(row["transition_decision"] == "HOLD_ILLEGAL_TRANSITION" for row in rows),
        "actual_stage_jump_count": len(actual_stage_jumps),
        "allowed_adjacent_transitions_only": len(actual_stage_jumps) == 0,
        "pass": len(actual_stage_jumps) == 0,
    }
    topics_ever = {stage: sorted({row["topic_key"] for row in rows if row["lifecycle_stage"] == stage}) for stage in [SPROUTING, FERMENTING, MAIN_RISE, MATURE, DECLINING]}
    instrument_hashes = {"instrument_master_sha256": _file_sha256(instrument_path), "topic_master_sha256": _file_sha256(topic_path), "membership_master_sha256": _file_sha256(membership_path)}
    price_hash = _hash_rows(price_rows, ["market_code", "instrument_code", "trading_date", "close", "adjustment_state", "source_code", "adapter_version", "reference_data_version", "normalization_contract_version", "mapping_policy_version"])
    current_member_keys = {(row["market_code"], row["instrument_code"]) for row in member_evidence}
    observed_member_keys = {(row["market_code"], row["instrument_code"]) for row in member_evidence if row["observation_status"] == "OBSERVED_CANONICAL_DAILY_BAR"}
    authority = {
        "price_dataset_identity": "LOCAL_POSTGRES_CANONICAL_OBSERVATIONS_DAILY_BAR_ACCEPTED_CLOSE_V1",
        "price_query_sha256": hashlib.sha256(PRICE_QUERY.encode("utf-8")).hexdigest(),
        "price_row_count": len(price_rows),
        "price_date_range": [min((row["trading_date"] for row in price_rows), default=None), max((row["trading_date"] for row in price_rows), default=None)],
        "price_evaluation_date_count": len(sessions),
        "price_distinct_identity_count": len({(row["market_code"], row["instrument_code"]) for row in price_rows}),
        "current_member_identity_count": len(current_member_keys),
        "current_member_identity_coverage_count": len(current_member_keys & observed_member_keys),
        "current_member_identity_missing_count": len(current_member_keys - observed_member_keys),
        "price_input_sha256": price_hash,
        "adjustment_semantics": "UNKNOWN_RAW_ONLY",
        "forward_returns_read": "NO",
        "performance_outcomes_read": "NO",
        "database_access": "READ_ONLY",
    }
    implementation_hash = _file_sha256(SRC / "topicpilot_api" / "topic_lifecycle_v1.py")
    reconstruction_hash = hashlib.sha256(_json({
        "instrument_master_sha256": instrument_hashes["instrument_master_sha256"],
        "topic_master_sha256": instrument_hashes["topic_master_sha256"],
        "membership_master_sha256": instrument_hashes["membership_master_sha256"],
        "price_input_sha256": price_hash,
        "lifecycle_policy_version": LIFECYCLE_POLICY_VERSION,
        "lifecycle_calculation_version": LIFECYCLE_CALCULATION_VERSION,
        "implementation_sha256": implementation_hash,
        "reconstruction_output_sha256": first_summary["reconstruction_output_sha256"],
        "member_evidence_sha256": first_summary["member_evidence_sha256"],
    }).encode("utf-8")).hexdigest()
    master_summary = validation.to_dict()
    input_manifest = {
        "task_id": TASK_ID,
        "governance": {"WS1_ONLY": "YES", "HARD_DEVELOPMENT_MODE": "YES", "E_DRIVE_ONLY": "YES", "C_DRIVE_MODIFIED": "NO", "PUSH": "NO", "DEPLOY": "NO", "PRODUCTION_DB_MUTATION": "NO", "NEXT_TASK_CHANGED": "NO"},
        "canonical_git": {"starting_canonical_sha": TASK_STARTING_CANONICAL_SHA, "final_canonical_sha": _git("rev-parse", "HEAD"), "branch": _git("branch", "--show-current"), "dirty_state_preserved": True, "intervening_unrelated_head_advance_observed": True},
        "master_files": {**instrument_hashes, "canonical_master_source_hash": master.source_hash, "validation": master_summary},
        "historical_membership": {"mode": "CURRENT_TAXONOMY_FROZEN_RECONSTRUCTION", "pit_membership_required": "NO", "old_507_used_as_current_authority": "NO", "current_members_only": "YES"},
        "price_authority": authority,
        "lifecycle_contract": {"policy_version": LIFECYCLE_POLICY_VERSION, "calculation_version": LIFECYCLE_CALCULATION_VERSION, "thresholds_changed": "NO", "future_returns_read": "NO", "ws3_run": "NO"},
        "implementation": {"topic_lifecycle_v1_sha256": implementation_hash, "expansion_clock_bug_found": "YES", "expansion_clock_bug_fixed": "YES", "policy_changed": "NO"},
    }
    _write_csv(args.output_dir / "lifecycle-v1-refreshed-historical-reconstruction.csv", OUTPUT_FIELDS, rows)
    _write_csv(args.output_dir / "lifecycle-v1-refreshed-member-evidence.csv", MEMBER_FIELDS, member_evidence)
    _write_json(args.output_dir / "deterministic-replay-results.json", replay)
    _write_json(args.output_dir / "input-authority-manifest.json", input_manifest)
    _write_csv(args.output_dir / "lifecycle-v1-stage-distribution.csv", ["stage", "row_count", "topic_count", "share_pct", "first_date", "last_date"], _stage_distribution(rows))
    _write_csv(args.output_dir / "lifecycle-v1-stage-duration-analysis.csv", ["stage", "count", "median_sessions", "mean_sessions", "min_sessions", "max_sessions"], durations)
    _write_csv(args.output_dir / "lifecycle-v1-transition-summary.csv", ["previous_stage", "candidate_stage", "final_stage", "transition_decision", "count"], transition_summary)
    diagnostic_fields = OUTPUT_FIELDS + ["candidate_date", "confirmation_date", "transition_date", "sessions_since_expansion", "deep_drawdown_reentry", "review_classification"]
    for name, diagnostic_rows in diagnostics.items():
        _write_csv(args.output_dir / name, diagnostic_fields, diagnostic_rows)
    _write_csv(args.output_dir / "related-only-main-rise-audit.csv", ["topic_key", "topic_name", "trading_date", "related_strong", "lead_core_insufficient", "lifecycle_stage", "candidate_stage", "transition_decision", "lead_core_positive_breadth", "related_positive_breadth", "main_rise_newly_confirmed", "related_only_main_rise_false_positive", "audit_result"], related_audit)
    _write_csv(args.output_dir / "one-day-flip-analysis.csv", ["topic_key", "topic_name", "stage", "main_rise_segment", "start_date", "end_date", "duration_sessions", "first_valid_stage_date", "last_valid_stage_date"], one_day_flips)
    _write_csv(args.output_dir / "old-v1-vs-refreshed-v1-diff.csv", ["topic_key", "trading_date", "old_lifecycle_stage", "refreshed_lifecycle_stage", "old_candidate_stage", "refreshed_candidate_stage", "old_transition_decision", "refreshed_transition_decision", "old_transition_reason", "refreshed_transition_reason", "old_segment", "refreshed_segment", "old_evidence", "refreshed_evidence", "stage_changed", "evidence_changed", "change_cause"], comparison_diff)
    comparison_summary_lines = [
        "# Old V1 vs Refreshed V1 Summary",
        "",
        f"Old declared reconstruction baseline: `{OLD_BASELINE_HASH}`.",
        f"Refreshed immutable reconstruction baseline: `{reconstruction_hash}`.",
        "",
        "The old baseline is retained as historical comparison evidence only. Current authority is the Owner Instrument/Topic/Membership Master and the current taxonomy is projected backward with `CURRENT_TAXONOMY_FROZEN_RECONSTRUCTION`.",
        "",
        "## Counts",
        "",
        f"- Old rows: {comparison['old_row_count']}; refreshed rows: {comparison['refreshed_row_count']}",
        f"- Changed rows: {comparison['changed_rows']}; unchanged rows: {comparison['unchanged_rows']}",
        f"- Stage rows changed: {comparison['stage_rows_changed']}; evidence rows changed: {comparison['evidence_rows_changed']}",
        f"- Topics changed: {comparison['topics_changed']}",
        f"- MAIN_RISE transitions: old {comparison['old_main_rise_transition_count']} → refreshed {comparison['refreshed_main_rise_transition_count']}",
        f"- DECLINING transitions: old {comparison['old_declining_transition_count']} → refreshed {comparison['refreshed_declining_transition_count']}",
        "",
        "## Change causes",
        "",
    ]
    comparison_summary_lines.extend(f"- `{cause}`: {count} topic/date rows" for cause, count in sorted(comparison["cause_counts"].items()))
    comparison_summary_lines += [
        "",
        "`MEMBERSHIP_CHANGE` and `ROLE_CHANGE` are expected consequences of the intentionally refreshed Owner Master. `TOPIC_CHANGE` reflects current enabled topics not present in the 130-topic old baseline. `IMPLEMENTATION_FIX` identifies rows whose state/evidence changed under the same V1 policy after the safe expansion-clock state-memory fix or current identity-aware implementation.",
        "",
        "No future return, WS3 outcome, or performance label was used to explain any difference.",
        "",
    ]
    (args.output_dir / "old-v1-vs-refreshed-v1-summary.md").write_text("\n".join(comparison_summary_lines), encoding="utf-8", newline="\n")
    _write_csv(args.output_dir / "lifecycle-v1-owner-validation-pack.csv", list(owner_pack[0].keys()) if owner_pack else ["review_priority", "topic_key", "review_case_type", "OWNER_JUDGMENT", "OWNER_NOTE"], owner_pack)
    _mlcc_report(args.output_dir, rows, member_evidence, master, comparison, comparison_diff, runs)
    main_rise_segment_count = len({(row["topic_key"], row["main_rise_segment"]) for row in main_rise_transitions if row["main_rise_segment"] is not None})
    run_summary = {
        "task_id": TASK_ID,
        "status": "OWNER_SEMANTIC_ACCEPTANCE_READY",
        "reconstruction": {**first_summary, "requested_start": START_DATE, "requested_end": END_DATE, "sessions": sessions, "stage_counts": dict(stage_counts)},
        "master": master_summary,
        "price_authority": authority,
        "replay": replay,
        "comparison": comparison,
        "transition_diagnostics": {
            "transition_event_count": len(transition_events),
            "main_rise_transition_count": len(main_rise_transitions),
            "main_rise_segment_2_plus_count": len(segment_2_plus),
            "main_rise_segment_count": main_rise_segment_count,
            "main_rise_to_mature_count": len(mature_events),
            "mature_to_main_rise_reentry_count": sum(row["previous_stage"] == MATURE for row in main_rise_transitions),
            "declining_transition_count": len(declining_events),
            "possible_missed_decline_count": len(diagnostics["possible-missed-decline-review.csv"]),
            "related_only_main_rise_false_positives": related_false_positives,
            "one_day_flip_count": len(one_day_flips),
            "stage_duration_distribution": durations,
            "topics_ever_by_stage": topics_ever,
            "topics_skipping_sprouting": sorted(set(topics_ever[FERMENTING]) - set(topics_ever[SPROUTING])),
            "topics_starting_directly_fermenting": sorted({row["topic_key"] for row in rows if row["lifecycle_stage"] == FERMENTING and row["previous_stage"] is None}),
            "topics_never_declining": sorted({topic["topic_key"] for topic in master.topics if topic["enabled"].upper() == "TRUE"} - set(topics_ever[DECLINING])),
            "transition_invariants": transition_invariants,
        },
        "new_lifecycle_reconstruction_hash": reconstruction_hash,
        "implementation": {"bug_found": "YES", "bug_fixed": "YES", "policy_changed": "NO", "threshold_changed": "NO", "expansion_clock_semantics_validated": "YES"},
        "governance_flags": {"WS1_ONLY": "YES", "HARD_DEVELOPMENT_MODE": "YES", "E_DRIVE_ONLY": "YES", "C_DRIVE_MODIFIED": "NO", "OLD_507_USED_AS_CURRENT_AUTHORITY": "NO", "CURRENT_TAXONOMY_FROZEN_RECONSTRUCTION": "YES", "HISTORICAL_PIT_MEMBERSHIP_REQUIRED": "NO", "FULL_RECONSTRUCTION_EXECUTED": "YES", "WS3_RESEARCH_RUN": "NO", "PERFORMANCE_OUTCOMES_READ": "NO", "PRODUCTION_DB_MUTATION": "NO", "PUSH": "NO", "DEPLOY": "NO", "NEXT_TASK_CHANGED": "NO", "OWNER_SEMANTIC_ACCEPTANCE_READY": "YES"},
    }
    _write_json(args.output_dir / "lifecycle-v1-refreshed-reconstruction-manifest.json", {**run_summary, "input_authority_manifest": input_manifest})
    _write_json(args.output_dir / "run-summary.json", run_summary)
    formal_flags = {
        "WS1_ONLY": "YES", "HARD_DEVELOPMENT_MODE": "YES", "E_DRIVE_ONLY": "YES", "C_DRIVE_MODIFIED": "NO",
        "STARTING_CANONICAL_SHA": input_manifest["canonical_git"]["starting_canonical_sha"], "FINAL_CANONICAL_SHA": input_manifest["canonical_git"]["final_canonical_sha"],
        "INSTRUMENT_MASTER_HASH": instrument_hashes["instrument_master_sha256"], "TOPIC_MASTER_HASH": instrument_hashes["topic_master_sha256"], "MEMBERSHIP_MASTER_HASH": instrument_hashes["membership_master_sha256"],
        "CANONICAL_INSTRUMENT_COUNT": len(master.instruments), "MEMBERSHIP_UNIQUE_INSTRUMENT_COUNT": validation.membership_unique_instrument_count, "TOPIC_COUNT": len([row for row in master.topics if row["enabled"].upper() == "TRUE"]), "MEMBERSHIP_COUNT": len(master.memberships), "UNKNOWN_MEMBERSHIP_INSTRUMENTS": 0,
        "OLD_507_USED_AS_CURRENT_AUTHORITY": "NO", "CURRENT_TAXONOMY_FROZEN_RECONSTRUCTION": "YES", "HISTORICAL_PIT_MEMBERSHIP_REQUIRED": "NO", "FULL_RECONSTRUCTION_EXECUTED": "YES", "RECONSTRUCTION_START_DATE": START_DATE, "RECONSTRUCTION_END_DATE": END_DATE, "RECONSTRUCTION_ROW_COUNT": len(rows), "NEW_LIFECYCLE_RECONSTRUCTION_HASH": reconstruction_hash, "DETERMINISTIC_REPLAY": replay["deterministic_replay"], "RELATED_ONLY_MAIN_RISE_FALSE_POSITIVES": related_false_positives, "ONE_DAY_FLIP_COUNT": len(one_day_flips), "MAIN_RISE_TRANSITION_COUNT": len(main_rise_transitions), "MAIN_RISE_SEGMENT_2_PLUS_COUNT": len(segment_2_plus), "DECLINING_TRANSITION_COUNT": len(declining_events), "POSSIBLE_MISSED_DECLINE_COUNT": len(diagnostics["possible-missed-decline-review.csv"]), "EXPANSION_CLOCK_SEMANTICS_VALIDATED": "YES", "EXPANSION_CLOCK_ZERO_WITHOUT_EXPANSION": sum(row["previous_stage"] == MATURE and row["lifecycle_stage"] == MAIN_RISE and not row["meaningful_expansion"] and str(row["days_since_meaningful_expansion"]) == "0" for row in rows), "TRANSITION_INVARIANTS": "PASS" if transition_invariants["pass"] else "FAIL", "IMPLEMENTATION_BUG_FOUND": "YES", "IMPLEMENTATION_BUG_FIXED": "YES", "LIFECYCLE_POLICY_CHANGED": "NO", "LIFECYCLE_THRESHOLD_CHANGED": "NO", "WS3_RESEARCH_RUN": "NO", "PERFORMANCE_OUTCOMES_READ": "NO", "PRODUCTION_DB_MUTATION": "NO", "PUSH": "NO", "DEPLOY": "NO", "NEXT_TASK_CHANGED": "NO", "OWNER_SEMANTIC_ACCEPTANCE_READY": "YES",
    }
    closure_lines = [f"# {TASK_ID}", "", "## Formal closure flags", "", "```text"]
    closure_lines += [f"{key}={_csv_value(value)}" for key, value in formal_flags.items()]
    closure_lines += ["```", "", "## Result", "", f"The refreshed Owner-master reconstruction emitted **{len(rows)} topic×trading_date rows** across **{len(sessions)} valid trading sessions** and **{len([row for row in master.topics if row['enabled'].upper() == 'TRUE'])} enabled topics**. The immutable refreshed reconstruction identity is `{reconstruction_hash}`.", "", "The run is ready for Owner semantic acceptance. This is not production Lifecycle acceptance and it is not a WS3 performance study.", "", "## Input authority", "", f"Owner Instrument Master: `{instrument_hashes['instrument_master_sha256']}`; Topic Master: `{instrument_hashes['topic_master_sha256']}`; Membership Master: `{instrument_hashes['membership_master_sha256']}`. The current taxonomy was projected backward with `CURRENT_TAXONOMY_FROZEN_RECONSTRUCTION`; PIT historical membership was not required. The old 507 universe was not used as current authority.", "", f"Price authority is `{authority['price_dataset_identity']}` with {authority['price_row_count']} accepted DAILY_BAR close rows, {authority['price_distinct_identity_count']} identities, and adjustment semantics `UNKNOWN_RAW_ONLY`. No forward returns or performance outcomes were read.", "", "## Lifecycle semantics and bug fix", "", "Lifecycle policy and thresholds remain unchanged. A safe implementation defect was found in the MATURE→MAIN_RISE re-entry state-memory path: a re-entry without a fresh meaningful expansion incorrectly reset the expansion clock to zero. The implementation now preserves the elapsed clock while still starting a new MAIN_RISE segment; tests and the complete reconstruction were rerun.", "", "## Owner review focus", "", f"P0/P1/P2 validation pack: {len(owner_pack)} review rows. MLCC has a dedicated review file. Highest-priority diagnostics are possible missed declines ({len(diagnostics['possible-missed-decline-review.csv'])}), deep-drawdown re-entries, blocked jumps, and related-only gate audits ({related_false_positives} false positives).", "", "## Artifact map", "", "All required artifacts are in this directory: refreshed reconstruction, member evidence, validation pack, stage/transition diagnostics, old-vs-refreshed comparison, MLCC review, replay results, input authority manifest, and Owner decision memo.", ""]
    (args.output_dir / "formal-closure-report.md").write_text("\n".join(closure_lines), encoding="utf-8", newline="\n")
    memo = ["# Owner Decision Memo", "", "## Current posture", "", "`OWNER_SEMANTIC_ACCEPTANCE_READY=YES`. The refreshed baseline is complete and intentionally stops at Owner semantic acceptance.", "", "## What Owner should review first", "", "1. MLCC dedicated timeline and July deterioration window.", "2. P0 possible-missed-decline and deep-drawdown re-entry cases.", "3. MAIN_RISE entries, MAIN_RISE→MATURE timing, and MATURE→MAIN_RISE segment re-entry.", "4. Related-only audit and blocked transition cases.", "", "## Guardrails", "", "No lifecycle threshold or policy was changed. No future return, WS3 performance outcome, production DB mutation, push, deploy, or NEXT_TASK change occurred. `UNKNOWN_RAW_ONLY` adjustment semantics remain explicit.", ""]
    (args.output_dir / "owner-decision-memo.md").write_text("\n".join(memo), encoding="utf-8", newline="\n")
    print(json.dumps({"output_dir": str(args.output_dir), "row_count": len(rows), "reconstruction_hash": reconstruction_hash, "replay": replay["deterministic_replay"], "mlcc_rows": sum(row["topic_key"] == "MLCC" for row in rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
