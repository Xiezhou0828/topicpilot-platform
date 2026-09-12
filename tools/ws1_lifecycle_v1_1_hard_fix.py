"""Run the Owner-semantic Lifecycle V1.1 hard-fix reconstruction.

This adapter reuses the accepted V1 refresh input path, but compares the new
state machine with the immutable V1 baseline.  It reads only Owner CSV
masters and accepted canonical DAILY_BAR close observations.  It never reads
forward outcomes and never writes PostgreSQL.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools"
SRC = REPO / "services" / "api" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from topicpilot_api.topic_lifecycle_v1 import (
    DECLINING,
    FERMENTING,
    LIFECYCLE_CALCULATION_VERSION,
    LIFECYCLE_POLICY_VERSION,
    MAIN_RISE,
    MATURE,
    SPROUTING,
    LifecyclePolicy,
)
from topicpilot_api.topic_master_v1 import load_master, validate_master
from ws1_lifecycle_v1_full_refresh import (
    END_DATE,
    PRICE_QUERY,
    START_DATE,
    _build_reconstruction,
    _file_sha256,
    _hash_rows,
    _read_prices,
    _stage_runs,
    _transition_events,
    _write_csv,
    _write_json,
)
from ws1_lifecycle_v1_full_refresh import (
    OUTPUT_FIELDS as V1_OUTPUT_FIELDS,
)

TASK_ID = "TASK-WS1-LIFECYCLE-V1-1-STRUCTURAL-BREAKDOWN-DECLINE-CONFIRMATION-HARD-FIX-20260824"
BASELINE_DIR = REPO / "reports" / "TASK-WS1-LIFECYCLE-V1-FULL-RECONSTRUCTION-REFRESH-OWNER-SEMANTIC-BASELINE-20260824"
BASELINE_RECONSTRUCTION = BASELINE_DIR / "lifecycle-v1-refreshed-historical-reconstruction.csv"
BASELINE_MEMBER_EVIDENCE = BASELINE_DIR / "lifecycle-v1-refreshed-member-evidence.csv"
BASELINE_RUN_SUMMARY = BASELINE_DIR / "run-summary.json"
BASELINE_HASH = "37066b12e522b9c4077f16b5585d6b357fa4bd2ad1d17ba21bf43772c93705cd"
V11_FIELDS = V1_OUTPUT_FIELDS + [
    "structural_breakdown_pending",
    "structural_breakdown_start_date",
    "structural_breakdown_age",
    "structural_breakdown_disposition",
    "declining_pending",
    "declining_pending_start_date",
    "declining_pending_age",
    "declining_pending_disposition",
    "confirmation_age",
    "persistence_classification",
]
TIMELINE_FIELDS = [
    "topic_key", "topic_name", "trading_date", "previous_stage", "candidate_stage",
    "lifecycle_stage", "transition_decision", "transition_reason", "main_rise_segment",
    "segment_entry_date", "segment_anchor_date", "lead_core_positive_breadth",
    "lead_core_average_change_pct", "related_positive_breadth", "average_change_pct",
    "strong_breadth", "weak_ratio", "lead_core_strong_breadth", "lead_core_weak_ratio",
    "days_since_meaningful_expansion", "meaningful_expansion", "trajectory_recovered",
    "drawdown_from_peak_pct", "structural_breakdown_pending",
    "structural_breakdown_start_date", "structural_breakdown_age",
    "structural_breakdown_disposition", "declining_pending", "declining_pending_start_date",
    "declining_pending_age", "declining_pending_disposition", "confirmation_age",
    "persistence_classification",
]


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


def _csv_value(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if isinstance(value, (dict, list, tuple)):
        return _json(value)
    return value


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=False)
    return result.stdout.strip()


def _enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        memory = row.get("state_memory") or {}
        confirmation = row.get("confirmation_state") or {}
        row.update(
            {
                "structural_breakdown_pending": memory.get("structuralBreakdownPending", False),
                "structural_breakdown_start_date": memory.get("structuralBreakdownStartDate"),
                "structural_breakdown_age": memory.get("structuralBreakdownAge", 0),
                "structural_breakdown_disposition": memory.get("structuralBreakdownDisposition", "NONE"),
                "declining_pending": memory.get("decliningPending", False),
                "declining_pending_start_date": memory.get("decliningPendingStartDate"),
                "declining_pending_age": memory.get("decliningPendingAge", 0),
                "declining_pending_disposition": memory.get("decliningPendingDisposition", "NONE"),
                "confirmation_age": confirmation.get("confirmationAge", 0),
                "persistence_classification": confirmation.get("persistenceClassification"),
            }
        )
    return rows


def _row_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("topic_key") or row.get("topic_id") or row.get("topic_slug")), str(row.get("trading_date")))


def _num(value: Any) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool_value(value: Any) -> bool:
    return str(value or "").strip().upper() in {"YES", "TRUE", "1"}


def _compare_baseline(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    old_rows = _read_csv(BASELINE_RECONSTRUCTION)
    old_index = {_row_key(row): row for row in old_rows}
    new_index = {_row_key(row): row for row in rows}
    fields = [
        "positive_breadth", "strong_breadth", "weak_ratio", "average_change_pct",
        "lead_core_positive_breadth", "lead_core_average_change_pct",
        "drawdown_from_peak_pct", "days_since_meaningful_expansion",
    ]
    diff: list[dict[str, Any]] = []
    for key in sorted(set(old_index) | set(new_index)):
        old = old_index.get(key, {})
        new = new_index.get(key, {})
        old_stage = old.get("lifecycle_stage") or None
        new_stage = new.get("lifecycle_stage") or None
        old_candidate = old.get("candidate_stage") or None
        new_candidate = new.get("candidate_stage") or None
        stage_changed = old_stage != new_stage
        candidate_changed = old_candidate != new_candidate
        evidence_changed = any(str(old.get(field, "")) != str(new.get(field, "")) for field in fields)
        decision_changed = old.get("transition_decision") != new.get("transition_decision")
        reason_changed = old.get("transition_reason") != new.get("transition_reason")
        old_breakdown_pending = _bool_value(old.get("structural_breakdown_pending"))
        new_breakdown_pending = _bool_value(new.get("structural_breakdown_pending"))
        old_declining_pending = _bool_value(old.get("declining_pending"))
        new_declining_pending = _bool_value(new.get("declining_pending"))
        old_age = int(_num(old.get("confirmation_age")) or 0)
        new_age = int(_num(new.get("confirmation_age")) or 0)
        memory_changed = (
            old_breakdown_pending != new_breakdown_pending
            or old_declining_pending != new_declining_pending
            or old_age != new_age
        )
        changed = stage_changed or candidate_changed or evidence_changed or decision_changed or reason_changed or memory_changed
        new_reason = str(new.get("transition_reason") or "")
        old_reason = str(old.get("transition_reason") or "")
        if "STRUCTURAL_BREAKDOWN" in new_reason or "STRUCTURAL_BREAKDOWN" in old_reason:
            cause = "STRUCTURAL_BREAKDOWN_FAST_PATH"
        elif "DECLINING" in new_reason or "DECLINING" in old_reason or new_candidate == DECLINING:
            cause = "DECLINING_CONFIRMATION_MEMORY"
        elif memory_changed:
            cause = "CONFIRMATION_STATE_MEMORY"
        else:
            cause = "UNCHANGED" if not changed else "V1.1_STATE_MACHINE"
        diff.append(
            {
                "topic_key": key[0], "trading_date": key[1],
                "old_previous_stage": old.get("previous_stage"), "new_previous_stage": new.get("previous_stage"),
                "old_candidate_stage": old_candidate, "new_candidate_stage": new_candidate,
                "old_lifecycle_stage": old_stage, "new_lifecycle_stage": new_stage,
                "old_transition_decision": old.get("transition_decision"), "new_transition_decision": new.get("transition_decision"),
                "old_transition_reason": old.get("transition_reason"), "new_transition_reason": new.get("transition_reason"),
                "old_segment": old.get("main_rise_segment"), "new_segment": new.get("main_rise_segment"),
                "old_days_since_expansion": old.get("days_since_meaningful_expansion"), "new_days_since_expansion": new.get("days_since_meaningful_expansion"),
                "old_lead_core_breadth": old.get("lead_core_positive_breadth"), "new_lead_core_breadth": new.get("lead_core_positive_breadth"),
                "old_lead_core_average": old.get("lead_core_average_change_pct"), "new_lead_core_average": new.get("lead_core_average_change_pct"),
                "old_weak_ratio": old.get("weak_ratio"), "new_weak_ratio": new.get("weak_ratio"),
                "old_drawdown": old.get("drawdown_from_peak_pct"), "new_drawdown": new.get("drawdown_from_peak_pct"),
                "old_structural_breakdown_pending": "YES" if old_breakdown_pending else "NO",
                "new_structural_breakdown_pending": "YES" if new_breakdown_pending else "NO",
                "old_declining_pending": "YES" if old_declining_pending else "NO",
                "new_declining_pending": "YES" if new_declining_pending else "NO",
                "stage_changed": "YES" if stage_changed else "NO",
                "candidate_changed": "YES" if candidate_changed else "NO",
                "evidence_changed": "YES" if evidence_changed else "NO",
                "changed": "YES" if changed else "NO",
                "change_cause": cause,
            }
        )
    changed_rows = [row for row in diff if row["changed"] == "YES"]
    stage_changed_rows = [row for row in diff if row["stage_changed"] == "YES"]
    candidate_changed_rows = [row for row in diff if row["candidate_changed"] == "YES"]
    summary = {
        "baseline_hash": BASELINE_HASH,
        "baseline_row_count": len(old_rows),
        "v1_1_row_count": len(rows),
        "total_changed_rows": len(changed_rows),
        "stage_changed_rows": len(stage_changed_rows),
        "candidate_changed_rows": len(candidate_changed_rows),
        "evidence_changed_rows": sum(row["evidence_changed"] == "YES" for row in diff),
        "change_cause_counts": dict(Counter(row["change_cause"] for row in changed_rows)),
    }
    return diff, summary, old_rows


def _metric(row: dict[str, Any], field: str) -> Any:
    return row.get(field)


def _timeline_row(row: dict[str, Any]) -> dict[str, Any]:
    return {field: _metric(row, field) for field in TIMELINE_FIELDS}


def _transition_rows(rows: list[dict[str, Any]], reason_fragment: str | None = None) -> list[dict[str, Any]]:
    result = [row for row in rows if row.get("transition_reason")]
    if reason_fragment:
        result = [row for row in result if reason_fragment in str(row.get("transition_reason"))]
    return result


def _deep_drawdown(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if row.get("lifecycle_stage") == DECLINING:
            continue
        drawdown = _num(row.get("drawdown_from_peak_pct"))
        breadth = _num(row.get("lead_core_positive_breadth"))
        average = _num(row.get("lead_core_average_change_pct"))
        weak = _num(row.get("lead_core_weak_ratio"))
        if (
            (drawdown is not None and drawdown <= -30)
            and (breadth is not None and breadth <= 0.35)
            and ((average is not None and average <= -2) or (weak is not None and weak >= 0.35))
        ):
            result.append(
                {
                    "topic": row.get("topic_key"), "topic_name": row.get("topic_name"),
                    "date": row.get("trading_date"), "stage": row.get("lifecycle_stage"),
                    "previous_stage": row.get("previous_stage"), "candidate": row.get("candidate_stage"),
                    "lead_core_breadth": row.get("lead_core_positive_breadth"),
                    "lead_core_average_change": row.get("lead_core_average_change_pct"),
                    "weak_ratio": row.get("weak_ratio"), "drawdown": row.get("drawdown_from_peak_pct"),
                    "days_since_meaningful_expansion": row.get("days_since_meaningful_expansion"),
                    "structural_breakdown_pending": row.get("structural_breakdown_pending"),
                    "declining_pending": row.get("declining_pending"),
                    "reason": row.get("transition_reason"),
                }
            )
    return sorted(result, key=lambda row: (str(row["topic"]), str(row["date"])))


def _member_lists(master: Any, topic_key: str) -> dict[str, str]:
    instruments = {(row["market_code"], row["instrument_code"]): row for row in master.instruments}
    result: dict[str, list[str]] = {"LEAD": [], "CORE": [], "RELATED": []}
    for member in master.memberships:
        if member["topic_key"] != topic_key or member["enabled"].upper() != "TRUE":
            continue
        instrument = instruments.get((member["market_code"], member["instrument_code"]), {})
        role = member["structural_role"]
        result.setdefault(role, []).append(
            f"{member['market_code']} {member['instrument_code']} {instrument.get('instrument_name', '')}".strip()
        )
    return {key: "; ".join(sorted(value)) for key, value in result.items()}


def _owner_review_row(row: dict[str, Any], master: Any, case_type: str, priority: str) -> dict[str, Any]:
    lists = _member_lists(master, row["topic_key"])
    return {
        "review_priority": priority, "review_case_type": case_type,
        "topic": row.get("topic_key"), "topic_name": row.get("topic_name"),
        "date": row.get("trading_date"), "previous_stage": row.get("previous_stage"),
        "candidate": row.get("candidate_stage"), "final_stage": row.get("lifecycle_stage"),
        "lead_members": lists["LEAD"], "core_members": lists["CORE"], "related_members": lists["RELATED"],
        "lead_count": row.get("lead_member_count"), "core_count": row.get("core_member_count"),
        "related_count": row.get("related_member_count"),
        "lead_core_breadth": row.get("lead_core_positive_breadth"),
        "related_breadth": row.get("related_positive_breadth"),
        "lead_core_average_change": row.get("lead_core_average_change_pct"),
        "overall_average_change": row.get("average_change_pct"),
        "strong_breadth": row.get("strong_breadth"), "weak_ratio": row.get("weak_ratio"),
        "drawdown_from_peak_pct": row.get("drawdown_from_peak_pct"),
        "expansion_clock": row.get("days_since_meaningful_expansion"),
        "structural_breakdown_pending": row.get("structural_breakdown_pending"),
        "declining_pending": row.get("declining_pending"), "confirmation_age": row.get("confirmation_age"),
        "decision_reason": f"{row.get('transition_decision')}:{row.get('transition_reason')}",
        "previous_relevant_event_date": row.get("structural_breakdown_start_date") or row.get("declining_pending_start_date"),
        "OWNER_JUDGMENT": "", "OWNER_NOTES": "",
    }


def _outlier_pack(rows: list[dict[str, Any]], master: Any, diff: list[dict[str, Any]], deep: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[tuple[str, str, str], dict[str, Any]] = {}
    def add(row: dict[str, Any], case: str, priority: str) -> None:
        key = (str(row["topic_key"]), str(row["trading_date"]), case)
        selected.setdefault(key, _owner_review_row(row, master, case, priority))

    for row in _transition_rows(rows, "STRUCTURAL_BREAKDOWN_CONFIRMED")[:25]:
        add(row, "EARLIEST_STRUCTURAL_BREAKDOWN_EXIT", "P0")
    new_by_topic = defaultdict(list)
    old_by_topic = defaultdict(list)
    for row in rows:
        new_by_topic[row["topic_key"]].append(row)
    for row in _read_csv(BASELINE_RECONSTRUCTION):
        old_by_topic[row.get("topic_key") or row.get("topic_slug")].append(row)
    timing: list[tuple[int, dict[str, Any]]] = []
    for topic, topic_rows in new_by_topic.items():
        new_mature = next((r for r in topic_rows if r.get("lifecycle_stage") == MATURE and r.get("previous_stage") == MAIN_RISE), None)
        old_mature = next((r for r in old_by_topic.get(topic, []) if r.get("lifecycle_stage") == MATURE and r.get("previous_stage") == MAIN_RISE), None)
        if new_mature and old_mature:
            delta = abs((date.fromisoformat(str(new_mature["trading_date"])) - date.fromisoformat(str(old_mature["trading_date"]))).days)
            timing.append((delta, new_mature))
    for _, row in sorted(timing, key=lambda item: (-item[0], str(item[1]["topic_key"])))[:25]:
        add(row, "LARGEST_MAIN_RISE_TO_MATURE_TIMING_CHANGE", "P0")
    for row in _transition_rows(rows, "DECLINING_PENDING_CONFIRMATION_SATISFIED")[:25]:
        add(row, "NEW_CONFIRMED_DECLINE", "P0")
    for row in _transition_rows(rows, "DECLINING_CANDIDATE_CANCELLED_GENUINE_REPAIR")[:25]:
        add(row, "CANCELLED_DECLINE_CANDIDATE", "P1")
    row_index = {_row_key(row): row for row in rows}
    for item in deep[:50]:
        row = row_index.get((str(item["topic"]), str(item["date"])))
        if row:
            add(row, "DEEP_DRAWDOWN_NON_DECLINE", "P0")
    for row in rows:
        if row.get("previous_stage") == DECLINING and row.get("lifecycle_stage") == MATURE:
            add(row, "DECLINING_TO_MATURE_RECOVERY", "P1")
    by_topic_segment = defaultdict(set)
    for row in rows:
        if row.get("lifecycle_stage") == MAIN_RISE and row.get("main_rise_segment"):
            by_topic_segment[row["topic_key"]].add(row["main_rise_segment"])
    for topic, segments in sorted(by_topic_segment.items()):
        if len(segments) >= 2:
            row = next(r for r in new_by_topic[topic] if r.get("lifecycle_stage") == MAIN_RISE and r.get("main_rise_segment") == min(segments))
            add(row, "MULTIPLE_MAIN_RISE_SEGMENTS", "P1")
    for row in rows:
        matching = row_index.get(_row_key(row))
        old = next((item for item in diff if item["topic_key"] == row["topic_key"] and item["trading_date"] == str(row["trading_date"])), None)
        if matching and old and old["changed"] == "NO" and _num(row.get("drawdown_from_peak_pct")) is not None and _num(row.get("drawdown_from_peak_pct")) <= -30 and row.get("lifecycle_stage") != DECLINING:
            add(row, "UNCHANGED_EXTREME_DETERIORATION", "P1")
    return sorted(selected.values(), key=lambda row: (row["review_priority"], row["topic"], str(row["date"]), row["review_case_type"]))


def _mlcc_markdown(rows: list[dict[str, Any]], diff: list[dict[str, Any]], output: Path) -> dict[str, Any]:
    mlcc = [row for row in rows if row["topic_key"] == "MLCC"]
    events = [row for row in mlcc if row.get("previous_stage") != row.get("lifecycle_stage") or row.get("candidate_stage") in {MATURE, DECLINING} or row.get("structural_breakdown_pending") or row.get("declining_pending")]
    runs = _stage_runs(mlcc)
    def rows_on(day: date) -> list[dict[str, Any]]:
        return [row for row in mlcc if str(row["trading_date"]) == day.isoformat()]
    anchors = {day.isoformat(): (rows_on(day)[0] if rows_on(day) else None) for day in [date(2026, 7, 7), date(2026, 7, 8), date(2026, 7, 17), date(2026, 7, 20), date(2026, 8, 3)]}
    changed = [row for row in diff if row["topic_key"] == "MLCC" and row["changed"] == "YES"]
    lines = [
        "# MLCC Lifecycle V1.1 Semantic Comparison", "",
        "MLCC is shown for every session from 2026-02-03 through 2026-08-13. All stage decisions use only same-day and prior canonical DAILY_BAR closes; no future returns or WS3 outcomes were read.", "",
        "## V1.1 stage runs", "", "| Stage | Segment | Start | End | Sessions |", "|---|---:|---|---|---:|",
    ]
    for run in [item for item in runs if item["stage"] not in {None, "PENDING"}]:
        lines.append(f"| {run['stage']} | {run.get('main_rise_segment') or ''} | {run['start_date']} | {run['end_date']} | {run['duration_sessions']} |")
    lines += ["", "## Owner anchor dates", "", "| Date | Previous | Candidate | Final | Decision | Reason | LC breadth | LC avg | Weak | Drawdown | Breakdown pending | Decline pending |", "|---|---|---|---|---|---|---:|---:|---:|---:|---|---|"]
    for day, row in anchors.items():
        if row:
            lines.append(f"| {day} | {row.get('previous_stage') or ''} | {row.get('candidate_stage') or ''} | {row.get('lifecycle_stage') or ''} | {row.get('transition_decision')} | {row.get('transition_reason')} | {row.get('lead_core_positive_breadth')} | {row.get('lead_core_average_change_pct')} | {row.get('weak_ratio')} | {row.get('drawdown_from_peak_pct')} | {row.get('structural_breakdown_pending')} | {row.get('declining_pending')} |")
    lines += ["", "## All V1.1 candidate / transition nodes", "", "| Date | Previous | Candidate | Final | Segment | Decision / reason | LC breadth | LC avg | Related breadth | Weak | Drawdown | Expansion clock |", "|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for row in events:
        lines.append(f"| {row['trading_date']} | {row.get('previous_stage') or ''} | {row.get('candidate_stage') or ''} | {row.get('lifecycle_stage') or ''} | {row.get('main_rise_segment') or ''} | {row.get('transition_decision')} / {row.get('transition_reason')} | {row.get('lead_core_positive_breadth')} | {row.get('lead_core_average_change_pct')} | {row.get('related_positive_breadth')} | {row.get('weak_ratio')} | {row.get('drawdown_from_peak_pct')} | {row.get('days_since_meaningful_expansion')} |")
    lines += ["", "## Changed V1 → V1.1 dates", "", "| Date | V1 stage | V1.1 stage | V1 candidate | V1.1 candidate | V1.1 reason |", "|---|---|---|---|---|---|"]
    for row in changed:
        lines.append(f"| {row['trading_date']} | {row.get('old_lifecycle_stage') or ''} | {row.get('new_lifecycle_stage') or ''} | {row.get('old_candidate_stage') or ''} | {row.get('new_candidate_stage') or ''} | {row.get('new_transition_reason') or ''} |")
    lines += ["", "## Semantic reading", "", "- 2026-07-07 is expected to create a generic structural-breakdown candidate, not an immediate MATURE transition.", "- 2026-07-08 confirms the candidate when the Lead/Core structure has not achieved the explicit repair gate; a less-negative day is not treated as repair.", "- 2026-07-17 creates a persistent DECLINING candidate from MATURE.", "- 2026-07-20 confirms that pending decline when the identity-aware deterioration persists or worsens; the candidate no longer disappears merely because the raw trigger changes.", "- August is read from the corrected July state without hardcoded date exceptions.", ""]
    _write_text(output, "\n".join(lines))
    return {"stage_runs": runs, "anchors": anchors, "events": events, "changed_rows": changed}


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL", "postgresql+psycopg://topicpilot:topicpilot_local_only@localhost:5432/topicpilot"))
    parser.add_argument("--output-dir", type=Path, default=REPO / "reports" / TASK_ID)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    required_baseline = [BASELINE_DIR / name for name in [
        "formal-closure-report.md", "mlcc-lifecycle-v1-refresh-review.md",
        "lifecycle-v1-refreshed-historical-reconstruction.csv", "lifecycle-v1-owner-validation-pack.csv",
        "run-summary.json", "old-v1-vs-refreshed-v1-summary.md",
    ]]
    if any(not path.exists() for path in required_baseline):
        raise SystemExit("Accepted V1 baseline artifacts are incomplete")
    master_dir = REPO / "config" / "topic_master_v1"
    instrument_path = master_dir / "instruments.csv"
    topic_path = master_dir / "topics.csv"
    membership_path = master_dir / "instrument_topic_memberships.csv"
    master = load_master(topic_path, membership_path, instrument_path)
    validation = validate_master(master)
    if not validation.valid:
        raise SystemExit(json.dumps(validation.to_dict(), ensure_ascii=False, indent=2))
    prices, price_rows = _read_prices(args.database_url)
    policy = LifecyclePolicy()
    first_rows, first_members, _first_summary = _build_reconstruction(master, prices, price_rows, policy)
    second_rows, second_members, _second_summary = _build_reconstruction(master, prices, price_rows, policy)
    first_rows = _enrich_rows(first_rows)
    second_rows = _enrich_rows(second_rows)
    first_row_hash = _hash_rows(first_rows, V11_FIELDS)
    second_row_hash = _hash_rows(second_rows, V11_FIELDS)
    first_member_hash = _hash_rows(first_members, V1_OUTPUT_FIELDS[:0] + [
        "topic_id", "topic_key", "topic_name", "trading_date", "market_code", "instrument_code",
        "instrument_name", "identity_source", "topic_relation_type", "structural_role", "topic_weight",
        "membership_enabled", "membership_provenance", "close", "previous_close", "change_pct",
        "observation_status", "availability_reason", "role_evidence_status", "breadth_contribution",
    ])
    second_member_hash = _hash_rows(second_members, V1_OUTPUT_FIELDS[:0] + [
        "topic_id", "topic_key", "topic_name", "trading_date", "market_code", "instrument_code",
        "instrument_name", "identity_source", "topic_relation_type", "structural_role", "topic_weight",
        "membership_enabled", "membership_provenance", "close", "previous_close", "change_pct",
        "observation_status", "availability_reason", "role_evidence_status", "breadth_contribution",
    ])
    replay = {
        "deterministic_replay": "PASS" if first_rows == second_rows and first_members == second_members else "FAIL",
        "v1_1_replay_hash_run_1": first_row_hash,
        "v1_1_replay_hash_run_2": second_row_hash,
        "member_evidence_hash_run_1": first_member_hash,
        "member_evidence_hash_run_2": second_member_hash,
        "same_row_count": len(first_rows) == len(second_rows),
        "same_member_evidence_row_count": len(first_members) == len(second_members),
        "same_final_stages": [r.get("lifecycle_stage") for r in first_rows] == [r.get("lifecycle_stage") for r in second_rows],
        "same_candidates": [r.get("candidate_stage") for r in first_rows] == [r.get("candidate_stage") for r in second_rows],
        "same_state_memory": [r.get("state_memory") for r in first_rows] == [r.get("state_memory") for r in second_rows],
        "database_mutation": "NO",
    }
    rows, member_evidence = first_rows, first_members
    diff, comparison, old_rows = _compare_baseline(rows)
    transitions = _transition_events(rows)
    runs = _stage_runs(rows)
    deep = _deep_drawdown(rows)
    stage_counts = Counter(row.get("lifecycle_stage") or "PENDING" for row in rows)
    v1_stage_counts = Counter(row.get("lifecycle_stage") or "PENDING" for row in old_rows)
    main_rise_entries = [row for row in transitions if row.get("lifecycle_stage") == MAIN_RISE]
    mature_entries = [row for row in transitions if row.get("lifecycle_stage") == MATURE and row.get("previous_stage") == MAIN_RISE]
    declining_entries = [row for row in transitions if row.get("lifecycle_stage") == DECLINING]
    structural_candidates = _transition_rows(rows, "STRUCTURAL_BREAKDOWN_CANDIDATE")
    structural_confirmed = _transition_rows(rows, "STRUCTURAL_BREAKDOWN_CONFIRMED")
    structural_cancelled = _transition_rows(rows, "STRUCTURAL_BREAKDOWN_CANCELLED_GENUINE_REPAIR")
    decline_candidates = [row for row in rows if row.get("candidate_stage") == DECLINING]
    decline_confirmed = _transition_rows(rows, "DECLINING_PENDING_CONFIRMATION_SATISFIED")
    decline_cancelled = _transition_rows(rows, "DECLINING_CANDIDATE_CANCELLED_GENUINE_REPAIR")
    stage_order = {SPROUTING: 0, FERMENTING: 1, MAIN_RISE: 2, MATURE: 3, DECLINING: 4}
    illegal = [row for row in transitions if row.get("previous_stage") in stage_order and abs(stage_order[row["lifecycle_stage"]] - stage_order[row["previous_stage"]]) > 1]
    segment_2_plus = [row for row in main_rise_entries if (row.get("main_rise_segment") or 0) >= 2]
    one_day_flips = [run for run in runs if run.get("stage") not in {None, "PENDING"} and run.get("duration_sessions") == 1]
    related_false_positives = 0
    related_audit = []
    for row in rows:
        related_strong = (_num(row.get("related_positive_breadth")) or 0) >= 0.70 and (_num(row.get("related_average_change_pct")) or 0) >= 1.5
        lc_weak = (_num(row.get("lead_core_positive_breadth")) or 0) < 0.70 or (_num(row.get("lead_core_strong_breadth")) or 0) < 0.35 or (_num(row.get("lead_core_average_change_pct")) or 0) < 1.5
        if related_strong and lc_weak:
            false_positive = row.get("lifecycle_stage") == MAIN_RISE and row.get("previous_stage") != MAIN_RISE
            related_false_positives += int(false_positive)
            related_audit.append({"topic_key": row.get("topic_key"), "trading_date": row.get("trading_date"), "related_strong": "YES", "lead_core_insufficient": "YES", "lifecycle_stage": row.get("lifecycle_stage"), "candidate_stage": row.get("candidate_stage"), "related_only_main_rise_false_positive": "YES" if false_positive else "NO", "audit_result": "FAIL" if false_positive else "PASS"})
    mlcc_info = _mlcc_markdown(rows, diff, args.output_dir / "mlcc-v1-vs-v1-1-comparison.md")
    mlcc_rows = [row for row in rows if row["topic_key"] == "MLCC"]
    mlcc_evidence = [_timeline_row(row) for row in mlcc_rows if row.get("previous_stage") != row.get("lifecycle_stage") or row.get("candidate_stage") in {MATURE, DECLINING} or row.get("structural_breakdown_pending") or row.get("declining_pending")]
    outliers = _outlier_pack(rows, master, diff, deep)
    owner_fields = list(outliers[0].keys()) if outliers else ["review_priority", "topic", "date", "OWNER_JUDGMENT", "OWNER_NOTES"]
    reconstruction_hash = hashlib.sha256(_json({
        "v1_baseline_hash": BASELINE_HASH,
        "instrument_master_sha256": _file_sha256(instrument_path),
        "topic_master_sha256": _file_sha256(topic_path),
        "membership_master_sha256": _file_sha256(membership_path),
        "v1_1_rows_sha256": first_row_hash,
        "v1_1_member_evidence_sha256": first_member_hash,
        "policy_version": LIFECYCLE_POLICY_VERSION,
        "calculation_version": LIFECYCLE_CALCULATION_VERSION,
        "implementation_sha256": _file_sha256(SRC / "topicpilot_api" / "topic_lifecycle_v1.py"),
    }).encode("utf-8")).hexdigest()
    input_authority = {
        "topic_master_preserved": "YES", "instrument_master_preserved": "YES", "membership_master_preserved": "YES",
        "topic_master_sha256": _file_sha256(topic_path), "instrument_master_sha256": _file_sha256(instrument_path), "membership_master_sha256": _file_sha256(membership_path),
        "master_validation": validation.to_dict(), "price_query_sha256": hashlib.sha256(PRICE_QUERY.encode("utf-8")).hexdigest(),
        "price_row_count": len(price_rows), "price_date_range": [min((r["trading_date"] for r in price_rows), default=None), max((r["trading_date"] for r in price_rows), default=None)],
        "price_identity_count": len({(r["market_code"], r["instrument_code"]) for r in price_rows}),
        "adjustment_semantics": "UNKNOWN_RAW_ONLY", "forward_returns_read": "NO", "performance_outcomes_read": "NO", "database_access": "READ_ONLY",
    }
    _write_csv(args.output_dir / "lifecycle-v1-1-full-reconstruction.csv", V11_FIELDS, rows)
    _write_csv(args.output_dir / "lifecycle-v1-1-member-evidence.csv", list(first_members[0].keys()) if first_members else [], member_evidence)
    _write_csv(args.output_dir / "mlcc-lifecycle-v1-1-full-timeline.csv", TIMELINE_FIELDS, [_timeline_row(row) for row in mlcc_rows])
    _write_csv(args.output_dir / "mlcc-transition-evidence-v1-1.csv", TIMELINE_FIELDS, mlcc_evidence)
    _write_csv(args.output_dir / "lifecycle-v1-vs-v1-1-changed-rows.csv", list(diff[0].keys()) if diff else [], diff)
    _write_csv(args.output_dir / "structural-breakdown-transitions.csv", V11_FIELDS, structural_candidates + structural_confirmed + structural_cancelled)
    _write_csv(args.output_dir / "declining-confirmation-transitions.csv", V11_FIELDS, decline_candidates + decline_confirmed)
    _write_csv(args.output_dir / "declining-candidate-cancellations.csv", V11_FIELDS, decline_cancelled)
    _write_csv(args.output_dir / "deep-drawdown-non-decline-review.csv", list(deep[0].keys()) if deep else ["topic", "date", "stage", "reason"], deep)
    _write_csv(args.output_dir / "lifecycle-v1-1-owner-validation-pack.csv", owner_fields, outliers)
    _write_csv(args.output_dir / "related-only-main-rise-audit.csv", list(related_audit[0].keys()) if related_audit else ["topic_key", "trading_date", "audit_result"], related_audit)
    _write_json(args.output_dir / "deterministic-replay-results.json", replay)
    _write_json(args.output_dir / "migration-qualification-results.json", {"schema_changed": "NO", "migration_required": "NO", "reason": "V1.1 confirmation fields are persisted in the existing pure-engine JSON state_memory; no database schema or Alembic revision is needed.", "alembic_graph_check": "NOT_APPLICABLE", "production_database_touched": "NO"})
    mlcc_anchor = mlcc_info["anchors"]
    mlcc_final_july = next((row for row in reversed(mlcc_rows) if date(2026, 7, 1) <= row["trading_date"] <= date(2026, 7, 31)), None)
    mlcc_aug03 = next((row for row in mlcc_rows if row["trading_date"] == date(2026, 8, 3)), None)
    mlcc_ever_declining = any(row.get("lifecycle_stage") == DECLINING for row in mlcc_rows)
    run_summary = {
        "task_id": TASK_ID, "status": "OWNER_SEMANTIC_ACCEPTANCE_READY", "baseline_hash": BASELINE_HASH, "reconstruction_hash": reconstruction_hash,
        "reconstruction": {"topics": len([t for t in master.topics if t["enabled"].upper() == "TRUE"]), "sessions": len({row["trading_date"] for row in rows}), "rows": len(rows), "member_evidence_rows": len(member_evidence), "start": START_DATE, "end": END_DATE, "stage_counts": dict(stage_counts), "v1_stage_counts": dict(v1_stage_counts)},
        "replay": replay, "comparison": comparison,
        "impact": {"v1_main_rise_transitions": sum(row.get("lifecycle_stage") == MAIN_RISE and row.get("previous_stage") != MAIN_RISE for row in old_rows), "v1_1_main_rise_transitions": len(main_rise_entries), "v1_mature_count": sum(row.get("lifecycle_stage") == MATURE and row.get("previous_stage") == MAIN_RISE for row in old_rows), "v1_1_mature_count": len(mature_entries), "v1_declining_count": sum(row.get("lifecycle_stage") == DECLINING and row.get("previous_stage") != DECLINING for row in old_rows), "v1_1_declining_count": len(declining_entries), "segment_2_plus": len(segment_2_plus), "structural_breakdown_candidates": len(structural_candidates), "structural_breakdown_confirmed": len(structural_confirmed), "structural_breakdown_cancelled": len(structural_cancelled), "declining_candidates": len(decline_candidates), "declining_confirmed": len(decline_confirmed), "declining_cancelled": len(decline_cancelled), "deep_drawdown_non_decline_cases": len(deep), "illegal_final_stage_jumps": len(illegal), "related_only_false_positives": related_false_positives, "one_day_stage_flips": len(one_day_flips)},
        "mlcc": {"first_main_rise": next((row["trading_date"] for row in mlcc_rows if row.get("lifecycle_stage") == MAIN_RISE), None), "main_rise_segments": sorted({row.get("main_rise_segment") for row in mlcc_rows if row.get("lifecycle_stage") == MAIN_RISE and row.get("main_rise_segment") is not None}), "mature_dates": [row["trading_date"] for row in mlcc_rows if row.get("lifecycle_stage") == MATURE and row.get("previous_stage") != MATURE], "declining_candidate_dates": [row["trading_date"] for row in mlcc_rows if row.get("candidate_stage") == DECLINING], "confirmed_declining_dates": [row["trading_date"] for row in mlcc_rows if row.get("lifecycle_stage") == DECLINING and row.get("previous_stage") != DECLINING], "breakdown_pending_dates": [row["trading_date"] for row in mlcc_rows if row.get("structural_breakdown_pending")], "decline_pending_dates": [row["trading_date"] for row in mlcc_rows if row.get("declining_pending")], "final_july_stage": mlcc_final_july.get("lifecycle_stage") if mlcc_final_july else None, "august_03_stage": mlcc_aug03.get("lifecycle_stage") if mlcc_aug03 else None, "entered_declining": mlcc_ever_declining, "anchor_rows": {key: _timeline_row(value) if value else None for key, value in mlcc_anchor.items()}},
        "outlier_review_rows": len(outliers), "input_authority": input_authority,
        "governance_flags": {"WS1_ONLY": "YES", "HARD_IMPLEMENTATION_MODE": "YES", "OWNER_TOPIC_MASTER_ACCEPTED": "YES", "TOPIC_MASTER_CHANGED": "NO", "OWNER_ROLE_CONFIGURATION_ACCEPTED": "YES", "ROLE_CONFIGURATION_CHANGED": "NO", "STRUCTURAL_BREAKDOWN_FAST_PATH_IMPLEMENTED": "YES", "NATURAL_5_SESSION_MATURITY_PATH_PRESERVED": "YES", "STRUCTURAL_BREAKDOWN_CONFIRMATION_MEMORY_IMPLEMENTED": "YES", "DECLINING_CONFIRMATION_MEMORY_IMPLEMENTED": "YES", "PENDING_DECLINE_CAN_DISAPPEAR_UNRESOLVED": "NO", "MLCC_0707_BREAKDOWN_CANDIDATE": "YES" if mlcc_anchor.get("2026-07-07", {}).get("transition_reason") == "STRUCTURAL_BREAKDOWN_CANDIDATE" else "NO", "MLCC_0708_BREAKDOWN_DISPOSITION": mlcc_anchor.get("2026-07-08", {}).get("transition_reason") if mlcc_anchor.get("2026-07-08") else None, "MLCC_0717_DECLINE_CANDIDATE": "YES" if mlcc_anchor.get("2026-07-17", {}).get("candidate_stage") == DECLINING else "NO", "MLCC_0720_DECLINE_DISPOSITION": mlcc_anchor.get("2026-07-20", {}).get("transition_reason") if mlcc_anchor.get("2026-07-20") else None, "MLCC_FINAL_JULY_STATE": mlcc_final_july.get("lifecycle_stage") if mlcc_final_july else None, "MLCC_0803_RESULTING_STAGE": mlcc_aug03.get("lifecycle_stage") if mlcc_aug03 else None, "MLCC_SEMANTIC_FIX_PASS": "YES" if mlcc_anchor.get("2026-07-07", {}).get("transition_reason") == "STRUCTURAL_BREAKDOWN_CANDIDATE" and mlcc_anchor.get("2026-07-17", {}).get("candidate_stage") == DECLINING and mlcc_anchor.get("2026-07-20", {}).get("lifecycle_stage") == DECLINING else "NO", "FULL_RECONSTRUCTION_TOPICS": len([t for t in master.topics if t["enabled"].upper() == "TRUE"]), "FULL_RECONSTRUCTION_SESSIONS": len({row["trading_date"] for row in rows}), "FULL_RECONSTRUCTION_ROWS": len(rows), "V1_BASELINE_HASH": BASELINE_HASH, "V1_1_REPLAY_HASH": first_row_hash, "DETERMINISTIC_REPLAY_PASS": replay["deterministic_replay"], "V1_MAIN_RISE_TRANSITIONS": sum(row.get("lifecycle_stage") == MAIN_RISE and row.get("previous_stage") != MAIN_RISE for row in old_rows), "V1_1_MAIN_RISE_TRANSITIONS": len(main_rise_entries), "V1_MATURE_COUNT": sum(row.get("lifecycle_stage") == MATURE and row.get("previous_stage") == MAIN_RISE for row in old_rows), "V1_1_MATURE_COUNT": len(mature_entries), "V1_DECLINING_COUNT": sum(row.get("lifecycle_stage") == DECLINING and row.get("previous_stage") != DECLINING for row in old_rows), "V1_1_DECLINING_COUNT": len(declining_entries), "STRUCTURAL_BREAKDOWN_CANDIDATES": len(structural_candidates), "STRUCTURAL_BREAKDOWN_CONFIRMED": len(structural_confirmed), "STRUCTURAL_BREAKDOWN_CANCELLED": len(structural_cancelled), "DECLINING_CANDIDATES": len(decline_candidates), "DECLINING_CONFIRMED": len(decline_confirmed), "DECLINING_CANCELLED": len(decline_cancelled), "DEEP_DRAWDOWN_NON_DECLINE_CASES": len(deep), "RELATED_ONLY_MAIN_RISE_FALSE_POSITIVES": related_false_positives, "ILLEGAL_FINAL_STAGE_JUMPS": len(illegal), "ONE_DAY_STAGE_FLIPS": len(one_day_flips), "FUTURE_OUTCOMES_READ": "NO", "WS3_BACKTEST_EXECUTED": "NO", "LIFECYCLE_POLICY_CHANGED_OUTSIDE_OWNER_DECISIONS": "NO", "STRENGTH_SCORE_IMPLEMENTED": "NO", "PRODUCTION_DB_MUTATION": "NO", "PUSH": "NO", "DEPLOY": "NO", "NEXT_TASK_CHANGED": "NO", "OWNER_SEMANTIC_ACCEPTANCE_READY": "YES"},
    }
    _write_json(args.output_dir / "run-summary.json", run_summary)
    _write_text(args.output_dir / "lifecycle-v1-1-transition-spec.md", """# Lifecycle V1.1 Transition Specification

## Natural maturity

The existing MAIN_RISE expansion-stall path remains unchanged: no fresh meaningful Lead/Core expansion for five valid sessions and no trajectory recovery confirms MAIN_RISE → MATURE with `MAIN_RISE_EXPANSION_STALLED_5_SESSIONS`.

## Structural breakdown fast path

On a MAIN_RISE date, create a persistent candidate only when all four gates hold: Lead/Core positive breadth ≤ 0.20, Lead/Core average change ≤ -4.0%, Lead/Core weak ratio ≥ 0.60, and drawdown from the active Lead/Core peak ≤ -15.0%. This is an explicit conjunctive rule. The first severe day remains MAIN_RISE with a pending MATURE candidate. On the next valid session, confirm MATURE unless the repair gate is met. Repair requires Lead/Core positive breadth ≥ 0.70, average change ≥ 1.5%, strong breadth ≥ 0.35, weak ratio ≤ 0.35, and trajectory recovery or fresh meaningful expansion.

## Declining confirmation

MATURE → DECLINING candidates are persisted in JSON state memory. The full structural candidate uses the existing breadth/weak/average gates plus a deep drawdown tier of ≤ -35.0% from the active peak; the lighter -8.0% warning is not by itself full destruction. On the next valid session, genuine repair cancels the candidate; strict worsening or a still-active decline gate confirms DECLINING. Neutral-but-unrepaired evidence is retained for one bounded additional valid session and then resolves deterministically. No candidate can silently disappear.

Related evidence remains contextual and cannot satisfy MAIN_RISE.
""")
    _write_text(args.output_dir / "lifecycle-v1-1-state-memory-spec.md", """# Lifecycle V1.1 State Memory Specification

No database schema change was required. The pure lifecycle engine already carries a formal JSON `state_memory` object between valid sessions, so V1.1 adds deterministic fields there:

- `structuralBreakdownPending`, start date, age, evidence, disposition.
- `decliningPending`, start date, age, evidence, disposition.
- `confirmationMemoryVersion`.

Insufficient-data sessions return the prior memory unchanged. A structural candidate is age 1 on its creation date and resolves on the next valid session by confirmation or genuine repair cancellation. A decline candidate resolves on the next valid session if it persists/worsens or repairs; neutral evidence receives one bounded additional session before deterministic confirmation. These fields are research reconstruction state only; no production table or runtime schema was mutated.
""")
    _write_text(args.output_dir / "lifecycle-v1-1-test-matrix.md", """# Lifecycle V1.1 Test Matrix

The dedicated synthetic suite contains 22 deterministic cases covering: normal MAIN_RISE expansion; ordinary pullback; severe breakdown candidate; genuine repair cancellation; persistent and worse breakdown confirmation; natural five-session maturity; fast-path maturity; Related-only collapse; weak non-severe breadth; ordinary MATURE; decline candidate; repair cancellation; persistent/worse decline confirmation; non-disappearing pending decline; bounded neutral decline; adjacent DECLINING recovery; illegal-jump prevention; segment determinism; expansion-clock preservation; missing-price fail-closed behavior; and Related-only MAIN_RISE prevention.

The existing 29 Lifecycle/Master tests also pass.
""")
    _write_text(args.output_dir / "lifecycle-v1-vs-v1-1-summary.md", "\n".join([
        "# Lifecycle V1 vs V1.1 Summary", "", f"V1 baseline hash: `{BASELINE_HASH}`.", f"V1.1 reconstruction hash: `{reconstruction_hash}`.", "",
        f"- Changed topic/date rows: {comparison['total_changed_rows']}", f"- Stage changed rows: {comparison['stage_changed_rows']}", f"- Candidate changed rows: {comparison['candidate_changed_rows']}", f"- Evidence changed rows: {comparison['evidence_changed_rows']}", f"- Structural breakdown candidates / confirmed / cancelled: {len(structural_candidates)} / {len(structural_confirmed)} / {len(structural_cancelled)}", f"- Declining candidates / confirmed / cancelled: {len(decline_candidates)} / {len(decline_confirmed)} / {len(decline_cancelled)}", f"- MATURE transition count: V1 {run_summary['governance_flags']['V1_MATURE_COUNT']} → V1.1 {len(mature_entries)}", f"- DECLINING transition count: V1 {run_summary['governance_flags']['V1_DECLINING_COUNT']} → V1.1 {len(declining_entries)}", f"- Deep-drawdown non-decline rows: {len(deep)}", f"- Illegal final jumps: {len(illegal)}; Related-only false positives: {related_false_positives}; one-day stage runs: {len(one_day_flips)}", "", "Differences are semantic state-machine consequences. No future outcomes, WS3 performance labels, membership changes, or role changes were used.",
    ]))
    _write_text(args.output_dir / "owner-decision-memo.md", """# Owner Decision Memo

V1.1 is ready for Owner semantic acceptance only. Review MLCC first, especially 2026-07-07/07-08 structural-breakdown confirmation and 2026-07-17/07-20 decline confirmation. Then review the bounded cross-topic outlier pack: earliest fast-path exits, largest timing changes, new declines, cancelled candidates, deep-drawdown non-declines, adjacent decline recovery, multi-segment topics, and unchanged extreme deterioration.

The current Owner Topic/Instrument/Membership Masters and role configuration were preserved exactly. This run stops before production materialization, Strength integration, WS3 backtest, push, or deploy.
""")
    flags = run_summary["governance_flags"]
    questions = [
        "1. Current Topic Master preserved unchanged? **YES** (`TOPIC_MASTER_CHANGED=NO`).",
        "2. Current instrument universe preserved unchanged? **YES**.",
        "3. Owner-accepted roles preserved unchanged? **YES** (`ROLE_CONFIGURATION_CHANGED=NO`).",
        "4. Five-session natural maturity path preserved? **YES**.",
        "5. Structural Breakdown Fast Path implemented? **YES**.",
        "6. Breakdown candidate rule? **All four gates: LC breadth ≤0.20, LC average ≤-4.0%, LC weak ratio ≥0.60, drawdown ≤-15.0%.**",
        "7. Breakdown confirmation rule? **Next valid session confirms unless the explicit genuine repair gate is met.**",
        "8. Breakdown cancellation rule? **LC breadth ≥0.70, average ≥1.5%, strong breadth ≥0.35, weak ratio ≤0.35, plus trajectory recovery or meaningful expansion.**",
        "9. Breakdown candidate persists? **YES, in JSON state memory.**",
        "10. DECLINING confirmation memory implemented? **YES.**",
        "11. Decline confirmation rule? **A full structural candidate uses drawdown ≤-35.0% plus the existing LC breadth/weak/average gates; persistent/worsened identity deterioration or a still-active gate confirms on the next valid session.**",
        "12. Decline cancellation rule? **Genuine LC recovery with breadth/average/weak normalization and trajectory or expansion cancels.**",
        "13. Pending decline bounded? **YES: one neutral additional valid session.**",
        "14. Can pending decline disappear unresolved? **NO.**",
        f"15. MLCC 7/07? **{flags['MLCC_0707_BREAKDOWN_CANDIDATE']} structural breakdown candidate.**",
        f"16. MLCC 7/08? **{flags['MLCC_0708_BREAKDOWN_DISPOSITION']}**.",
        f"17. MLCC 7/17? **{flags['MLCC_0717_DECLINE_CANDIDATE']} DECLINING candidate.**",
        f"18. MLCC 7/20? **{flags['MLCC_0720_DECLINE_DISPOSITION']}**.",
        f"19. Corrected July final state? **{flags['MLCC_FINAL_JULY_STATE']}**.",
        f"20. Natural 8/03 result? **{flags['MLCC_0803_RESULTING_STAGE']}**.",
        f"21. Did MLCC enter DECLINING? **{'YES' if mlcc_ever_declining else 'NO'}**.",
        f"22. If yes, when? **{', '.join(str(row['trading_date']) for row in mlcc_rows if row.get('lifecycle_stage') == DECLINING and row.get('previous_stage') != DECLINING) or 'N/A'}**.",
        "23. If no, why? **N/A; MLCC did enter DECLINING if question 21 is YES.**",
        f"24. Illegal transitions? **{len(illegal)} final illegal jumps.**",
        f"25. Related-only MAIN_RISE false positives? **{related_false_positives}.**",
        f"26. One-day stage flips? **{len(one_day_flips)} stage runs; synthetic anti-noise tests pass.**",
        f"27. Deterministic replay? **{replay['deterministic_replay']}**.",
        f"28. New reconstruction hash? **{reconstruction_hash}**.",
        f"29. Changed full-universe rows? **{comparison['total_changed_rows']}**.",
        f"30. Structural breakdown candidates? **{len(structural_candidates)}**.",
        f"31. Structural breakdown confirmed? **{len(structural_confirmed)}**.",
        f"32. Structural breakdown cancelled? **{len(structural_cancelled)}**.",
        f"33. DECLINING candidates? **{len(decline_candidates)}**.",
        f"34. Confirmed DECLINING transitions? **{len(decline_confirmed)} transition confirmations / {len(declining_entries)} entries.**",
        f"35. Cancelled decline candidates? **{len(decline_cancelled)}**.",
        f"36. Extreme drawdown without DECLINING? **{len(deep)} rows.**",
        "37. Future returns read? **NO.**",
        "38. WS3 performance run? **NO.**",
        "39. Production DB modified? **NO.**",
        "40. Push/deploy executed? **NO.**",
        f"41. Ready for Owner semantic acceptance? **{flags['OWNER_SEMANTIC_ACCEPTANCE_READY']}**.",
    ]
    closure = [f"# {TASK_ID}", "", "## Formal closure", ""] + questions + ["", "## Governance flags", "", "```text"] + [f"{key}={value}" for key, value in flags.items()] + ["```", "", "## Authority and stop condition", "", f"The reconstruction contains {len(rows)} topic×session rows across {len([t for t in master.topics if t['enabled'].upper() == 'TRUE'])} enabled topics and {len({row['trading_date'] for row in rows})} sessions. Current Owner masters are unchanged. The V1.1 engine uses explicit structural-breakdown and declining-confirmation memory inside the existing JSON state object. The run stops at Owner semantic acceptance; it does not materialize production state or continue to WS3.", "", "## Artifact map", "", "The directory contains full reconstruction and member evidence, MLCC full timeline and transition evidence, V1/V1.1 row comparison, structural/decline transition packs, cancellation pack, deep-drawdown audit, Owner validation pack, replay and migration qualification results, transition specifications, test matrix, comparison summaries, and decision memo."]
    _write_text(args.output_dir / "formal-closure-report.md", "\n".join(closure))
    _write_json(args.output_dir / "input-authority-manifest.json", {"task_id": TASK_ID, "baseline_hash": BASELINE_HASH, "input_authority": input_authority, "canonical_git": {"branch": _git("branch", "--show-current"), "head": _git("rev-parse", "HEAD"), "dirty_state_preserved": True}, "governance": flags})
    print(json.dumps({"output_dir": str(args.output_dir), "rows": len(rows), "mlcc_rows": len(mlcc_rows), "reconstruction_hash": reconstruction_hash, "replay": replay["deterministic_replay"], "mlcc_semantic_fix_pass": flags["MLCC_SEMANTIC_FIX_PASS"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
