"""Read-only historical V1 reconstruction using the frozen current taxonomy.

This adapter deliberately reuses the existing bounded canonical-bar input
reader but evaluates the new identity-aware state machine.  It never writes a
TopicPilot table and labels every row retrospective/non-PIT.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from topicpilot_api.topic_lifecycle_engine import (
    LIFECYCLE_CALCULATION_VERSION,
    LIFECYCLE_POLICY_VERSION,
    LifecycleInput,
    LifecycleObservation,
    LifecyclePolicy,
    evaluate_lifecycle,
)
from ws1_l5_historical_reconstruction import (
    END_DATE,
    START_DATE,
    _bar_index,
    _previous_close,
    _read_bars,
    _read_current_members,
    _read_topics,
)

TASK_ID = "TASK-WS1-LIFECYCLE-V1-CANONICAL-INTEGRATION-RECONSTRUCTION-OWNER-ACCEPTANCE-20260824"
SOURCE_CLASS = "CURRENT_TAXONOMY_HISTORICAL_V1_RECONSTRUCTION"
EVALUATION_MODE = "RETROSPECTIVE_RESEARCH_ONLY"
MEMBERSHIP_MODE = "CURRENT_TAXONOMY_FROZEN_RECONSTRUCTION"

DATASET_FIELDS = [
    "topic_id", "topic_slug", "trading_date", "source_class", "evaluation_mode",
    "membership_mode", "lifecycle_stage", "previous_stage", "candidate_stage",
    "stage_entered_at", "stage_trading_days", "evaluation_status", "data_status",
    "transition_decision", "transition_reason", "main_rise_segment", "segment_entry_date",
    "segment_anchor_date", "days_since_meaningful_expansion", "drawdown_from_peak_pct",
    "positive_breadth", "strong_breadth", "weak_ratio", "average_change_pct",
    "lead_core_positive_breadth", "core_positive_breadth", "related_positive_breadth",
    "authority_weighted_positive_breadth", "lead_core_average_change_pct",
    "meaningful_expansion", "trajectory_recovered", "role_authority_available",
    "role_coverage_pct", "expected_member_count", "observed_member_count", "coverage_pct",
    "lineage_status", "price_observation_count", "missing_price_member_count",
    "role_counts", "policy_version", "calculation_version", "publication_state",
]

MEMBER_EVIDENCE_FIELDS = [
    "topic_id", "topic_slug", "trading_date", "member_id", "member_code",
    "role", "role_source", "close", "previous_close", "change_pct",
    "observation_status", "membership_provenance",
]


def _csv(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return value


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv(row.get(field)) for field in fields})


def _hash_rows(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        [{field: _csv(row.get(field)) for field in DATASET_FIELDS} for row in rows],
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _reconstruct(session: Session, policy: LifecyclePolicy) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    topics = _read_topics(session)
    members, universe_hashes = _read_current_members(session)
    bars = _read_bars(session)
    indexed, date_counts = _bar_index(bars)
    dates = sorted(value for value in date_counts if START_DATE <= value <= END_DATE)
    states: dict[Any, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    member_evidence: list[dict[str, Any]] = []
    missing_role_rows = 0
    missing_price_rows = 0
    for trading_date in dates:
        for topic in topics:
            topic_members = members.get(topic.topic_id, [])
            observations: list[LifecycleObservation] = []
            missing_price = 0
            price_count = 0
            for member in topic_members:
                current = indexed.get((member.instrument_id, trading_date))
                previous = _previous_close(bars.get(member.instrument_id, []), trading_date)
                member_role = (
                    "LEAD" if str(member.structural_role or "").upper() in {"REPRESENTATIVE", "LEADER", "PRIMARY", "LEAD"}
                    else str(member.structural_role or "").upper() or None
                )
                if current is None or current.close is None or previous is None or previous <= 0:
                    member_evidence.append({
                        "topic_id": str(topic.topic_id),
                        "topic_slug": topic.slug,
                        "trading_date": trading_date,
                        "member_id": str(member.instrument_id),
                        "member_code": member.code,
                        "role": member_role,
                        "role_source": "CURRENT_TAXONOMY_RELATION_STRUCTURAL_ROLE" if member.structural_role else "ROLE_AUTHORITY_UNAVAILABLE",
                        "close": current.close if current is not None else None,
                        "previous_close": previous,
                        "change_pct": None,
                        "observation_status": "MISSING_CANONICAL_PRICE_EVIDENCE",
                        "membership_provenance": MEMBERSHIP_MODE,
                    })
                    missing_price += 1
                    continue
                change = (current.close - previous) / previous * 100
                member_evidence.append({
                    "topic_id": str(topic.topic_id),
                    "topic_slug": topic.slug,
                    "trading_date": trading_date,
                    "member_id": str(member.instrument_id),
                    "member_code": member.code,
                    "role": member_role,
                    "role_source": "CURRENT_TAXONOMY_RELATION_STRUCTURAL_ROLE" if member.structural_role else "ROLE_AUTHORITY_UNAVAILABLE",
                    "close": current.close,
                    "previous_close": previous,
                    "change_pct": change,
                    "observation_status": "OBSERVED_CANONICAL_DAILY_BAR",
                    "membership_provenance": MEMBERSHIP_MODE,
                })
                observations.append(
                    LifecycleObservation(
                        str(member.instrument_id),
                        float(change),
                        member.structural_role,
                        "CURRENT_TAXONOMY_RELATION_STRUCTURAL_ROLE" if member.structural_role else "ROLE_AUTHORITY_UNAVAILABLE",
                        float(current.close),
                        float(previous),
                    )
                )
                price_count += 1
            if any(item.role is None for item in observations) or (observations and not any(item.role for item in observations)):
                missing_role_rows += 1
            if missing_price:
                missing_price_rows += 1
            prior = states.get(topic.topic_id, {})
            result = evaluate_lifecycle(
                LifecycleInput(
                    topic_id=str(topic.topic_id),
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
            leadership = result.evidence.leadership
            diffusion = result.evidence.diffusion
            strength = result.evidence.group_strength
            progression = result.evidence.divergence_decay
            row = {
                "topic_id": str(topic.topic_id),
                "topic_slug": topic.slug,
                "trading_date": trading_date,
                "source_class": SOURCE_CLASS,
                "evaluation_mode": EVALUATION_MODE,
                "membership_mode": MEMBERSHIP_MODE,
                "lifecycle_stage": result.final_stage,
                "previous_stage": result.previous_stage,
                "candidate_stage": result.candidate_stage,
                "stage_entered_at": result.stage_entered_at,
                "stage_trading_days": result.stage_trading_days,
                "evaluation_status": result.evaluation_status,
                "data_status": result.data_status,
                "transition_decision": result.transition_decision,
                "transition_reason": result.transition_reason,
                "main_rise_segment": result.main_rise_segment,
                "segment_entry_date": result.segment_entry_date,
                "segment_anchor_date": result.segment_anchor_date,
                "days_since_meaningful_expansion": result.days_since_meaningful_expansion,
                "drawdown_from_peak_pct": result.drawdown_from_peak_pct,
                "positive_breadth": diffusion.get("positiveBreadth"),
                "strong_breadth": strength.get("strongBreadth"),
                "weak_ratio": strength.get("weakRatio"),
                "average_change_pct": strength.get("averageChangePct"),
                "lead_core_positive_breadth": diffusion.get("leadCorePositiveBreadth"),
                "core_positive_breadth": diffusion.get("corePositiveBreadth"),
                "related_positive_breadth": diffusion.get("relatedPositiveBreadth"),
                "authority_weighted_positive_breadth": diffusion.get("authorityWeightedPositiveBreadth"),
                "lead_core_average_change_pct": strength.get("leadCoreAverageChangePct"),
                "meaningful_expansion": progression.get("meaningfulExpansion"),
                "trajectory_recovered": progression.get("trajectoryRecovered"),
                "role_authority_available": leadership.get("roleAuthorityAvailable"),
                "role_coverage_pct": leadership.get("roleCoveragePct"),
                "expected_member_count": len(topic_members),
                "observed_member_count": len(observations),
                "coverage_pct": result.coverage_pct,
                "lineage_status": "CURRENT_TAXONOMY_NON_PIT;PRICE_CANONICAL;ROLE_AUTHORITY_PARTIAL" if not leadership.get("roleAuthorityAvailable") else "CURRENT_TAXONOMY_NON_PIT;PRICE_CANONICAL;ROLE_AUTHORITY_AVAILABLE",
                "price_observation_count": price_count,
                "missing_price_member_count": missing_price,
                "role_counts": leadership.get("roleCounts", {}),
                "policy_version": LIFECYCLE_POLICY_VERSION,
                "calculation_version": LIFECYCLE_CALCULATION_VERSION,
                "publication_state": "UNPUBLISHED_RESEARCH_ARTIFACT",
            }
            rows.append(row)
            states[topic.topic_id] = {
                "final_stage": result.final_stage,
                "stage_entered_at": result.stage_entered_at,
                "stage_trading_days": result.stage_trading_days,
                "candidate_stage": result.candidate_stage,
                "candidate_streak": result.confirmation_state.get("candidateStreak", 0),
                "state_memory": result.state_memory,
            }
    rows.sort(key=lambda row: (row["trading_date"], row["topic_slug"], row["topic_id"]))
    summary = {
        "topic_count": len(topics),
        "member_relation_count": sum(len(items) for items in members.values()),
        "date_count": len(dates),
        "actual_start": dates[0] if dates else None,
        "actual_end": dates[-1] if dates else None,
        "row_count": len(rows),
        "stage_or_status_counts": dict(Counter(row["lifecycle_stage"] or row["evaluation_status"] for row in rows)),
        "role_authority_unavailable_rows": missing_role_rows,
        "rows_with_missing_price": missing_price_rows,
        "universe_hash_count": len(universe_hashes),
        "normalized_dataset_sha256": _hash_rows(rows),
    }
    return rows, member_evidence, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL", "postgresql+psycopg://topicpilot:topicpilot_local_only@localhost:5432/topicpilot"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports") / TASK_ID)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(args.database_url, pool_pre_ping=True)
    with Session(engine, expire_on_commit=False, autoflush=False) as session:
        first_rows, first_member_evidence, first_summary = _reconstruct(session, LifecyclePolicy())
        second_rows, second_member_evidence, second_summary = _reconstruct(session, LifecyclePolicy())
    first_hash = first_summary["normalized_dataset_sha256"]
    second_hash = second_summary["normalized_dataset_sha256"]
    replay = {"reproducible": first_rows == second_rows and first_member_evidence == second_member_evidence and first_hash == second_hash, "first_sha256": first_hash, "second_sha256": second_hash, "database_mutation": "NO"}
    _write_csv(args.output_dir / "lifecycle-v1-historical-reconstruction.csv", DATASET_FIELDS, first_rows)
    _write_csv(args.output_dir / "lifecycle-v1-member-evidence.csv", MEMBER_EVIDENCE_FIELDS, first_member_evidence)
    coverage = [{"date": key, "row_count": sum(row["trading_date"] == key for row in first_rows), "status": "RECONSTRUCTED_RESEARCH"} for key in sorted({row["trading_date"] for row in first_rows})]
    _write_csv(args.output_dir / "lifecycle-v1-coverage.csv", ["date", "row_count", "status"], coverage)
    stage = [{"stage": stage, "row_count": count} for stage, count in sorted(first_summary["stage_or_status_counts"].items())]
    _write_csv(args.output_dir / "lifecycle-v1-stage-summary.csv", ["stage", "row_count"], stage)
    lineage_counter = Counter(row["lineage_status"] for row in first_rows)
    lineage = [{"lineage_status": key, "row_count": value} for key, value in sorted(lineage_counter.items())]
    _write_csv(args.output_dir / "lifecycle-v1-lineage.csv", ["lineage_status", "row_count"], lineage)
    manifest = {
        "task_id": TASK_ID,
        "source_class": SOURCE_CLASS,
        "evaluation_mode": EVALUATION_MODE,
        "membership_mode": MEMBERSHIP_MODE,
        "date_contract": {"requested_start": START_DATE, "requested_end": END_DATE, "historical_taxonomy_projection": True, "pit_claim": False},
        "lifecycle_contract": {"policy_version": LIFECYCLE_POLICY_VERSION, "calculation_version": LIFECYCLE_CALCULATION_VERSION, "five_stages_unchanged": True, "strength_score_created": False},
        "dataset": first_summary,
        "replay": replay,
        "database_write": "NO",
        "production_mutation": "NO",
        "governance": {"WS1_ONLY": "YES", "E_DRIVE_ONLY": "YES", "HISTORICAL_RECONSTRUCTION": "YES", "LOOKAHEAD": "NO", "WS3_FULL_BACKTEST": "NO", "PRODUCTION_DB_MUTATION": "NO", "DEPLOY": "NO", "PUSH": "NO", "NEXT_TASK_CHANGED": "NO"},
    }
    (args.output_dir / "lifecycle-v1-reconstruction-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=lambda value: value.isoformat() if isinstance(value, date) else value) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, default=lambda value: value.isoformat() if isinstance(value, date) else value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
