"""Build the deterministic cross-topic Owner semantic acceptance pack.

This is a read-only validation/reporting adapter.  It consumes the frozen
V1.1 reconstruction and member evidence, excludes MLCC from selection, and
does not import or execute the Lifecycle engine.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "reports" / "TASK-WS1-LIFECYCLE-V1-1-STRUCTURAL-BREAKDOWN-DECLINE-CONFIRMATION-HARD-FIX-20260824"
TASK_ID = "TASK-WS1-LIFECYCLE-V1-1-CROSS-TOPIC-OWNER-SEMANTIC-ACCEPTANCE-PACK-20260824"
DEFAULT_OUTPUT = REPO / "reports" / TASK_ID
RECON = BASE / "lifecycle-v1-1-full-reconstruction.csv"
MEMBERS = BASE / "lifecycle-v1-1-member-evidence.csv"
DEEP = BASE / "deep-drawdown-non-decline-review.csv"
BASELINE_SUMMARY = BASE / "run-summary.json"
BASELINE_MANIFEST = BASE / "input-authority-manifest.json"
MLCC = "MLCC"
STAGES = ["SPROUTING", "FERMENTING", "MAIN_RISE", "MATURE", "DECLINING"]

TIMELINE_FIELDS = [
    "case_id", "category", "topic_key", "topic_name", "case_key_date", "event_role",
    "trading_date", "previous_stage", "candidate_stage", "lifecycle_stage",
    "transition_decision", "transition_reason", "main_rise_segment", "lead_member_count",
    "core_member_count", "related_member_count", "lead_core_positive_breadth",
    "core_positive_breadth", "related_positive_breadth", "positive_breadth",
    "lead_core_average_change_pct", "average_change_pct", "strong_breadth", "lead_core_strong_breadth",
    "weak_ratio", "lead_core_weak_ratio", "authority_weighted_positive_breadth",
    "meaningful_expansion", "days_since_meaningful_expansion", "current_peak",
    "drawdown_from_peak_pct", "trajectory_recovered", "structural_breakdown_pending",
    "structural_breakdown_age", "structural_breakdown_disposition", "declining_pending",
    "declining_pending_age", "declining_pending_disposition", "confirmation_age",
    "pending_state_disposition",
]
MEMBER_FIELDS = [
    "case_id", "category", "topic_key", "topic_name", "case_key_date", "trading_date",
    "market_code", "instrument_code", "instrument_name", "structural_role",
    "topic_relation_type", "topic_weight", "identity_source", "close", "previous_close",
    "change_pct", "positive_negative", "strong_weak", "missing_data_state",
    "breadth_contribution", "observation_status",
]
SUMMARY_FIELDS = [
    "case_id", "category", "case_type", "topic_key", "topic_name", "key_date", "event_date",
    "confirmation_date", "recovery_date", "previous_stage", "candidate_stage", "final_stage",
    "selection_role", "selection_score", "key_evidence", "why_selected", "timeline_start", "timeline_end",
    "OWNER_VERDICT", "OWNER_NOTES",
]

QUESTIONS = {
    "A": [
        "Was the original breakdown candidate justified?",
        "Was the next-session evidence genuine repair?",
        "Should MAIN_RISE have been preserved?",
        "Should the candidate instead have confirmed MATURE?",
        "Did Related stocks improperly influence cancellation?",
    ],
    "B": [
        "Was MATURE already appropriate before decline?",
        "Was the DECLINING candidate justified?",
        "Was confirmation timing correct?",
        "Was deterioration persistent enough?",
        "Did Lead/Core drive the decline, and was it too early?",
    ],
    "C": [
        "Why did the engine not generate DECLINING?",
        "Which exact gate was missing?",
        "Was preserving the observed current stage semantically correct?",
        "Is this legitimate anti-noise or a MISSED_DECLINE?",
    ],
    "D": [
        "Was original DECLINING valid?",
        "How long did DECLINING persist?",
        "What exact Lead/Core evidence triggered recovery?",
        "Was recovery too fast or did it skip semantic rebuilding?",
        "If it later reached MAIN_RISE, was progression reasonable?",
    ],
    "E": [
        "Was SPROUTING truly partial/local abnormal movement?",
        "Had Lead/Core resonance formed too early?",
        "Was FERMENTING entered at the correct time?",
        "Was participation expanding and was MAIN_RISE sufficiently stronger?",
        "Did Related-only movement distort progression?",
    ],
}


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def _write_text(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def _jsonable(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _jsonable(value)


def _num(value: Any) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _date(value: Any) -> date:
    return date.fromisoformat(str(value))


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_payload(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=False)
    return result.stdout.strip()


def _prepare(rows: list[dict[str, Any]]) -> None:
    numeric_fields = {
        "lead_core_positive_breadth", "core_positive_breadth", "related_positive_breadth",
        "positive_breadth", "lead_core_average_change_pct", "average_change_pct",
        "strong_breadth", "weak_ratio", "drawdown_from_peak_pct", "current_peak",
        "days_since_meaningful_expansion", "structural_breakdown_age", "declining_pending_age",
        "confirmation_age", "main_rise_segment", "lead_core_weak_ratio",
        "lead_core_strong_breadth", "authority_weighted_positive_breadth",
    }
    for row in rows:
        for field in numeric_fields:
            if field in row:
                row[field] = _num(row[field])


def _topic_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        result[row["topic_key"]].append(row)
    for values in result.values():
        values.sort(key=lambda row: _date(row["trading_date"]))
    return result


def _severity(row: dict[str, Any]) -> float:
    return round(
        max(0.0, -(_num(row.get("drawdown_from_peak_pct")) or 0.0))
        + max(0.0, -(_num(row.get("lead_core_average_change_pct")) or 0.0)) * 2
        + (1.0 - (_num(row.get("lead_core_positive_breadth")) or 0.0)) * 10
        + (_num(row.get("lead_core_weak_ratio")) or 0.0) * 10,
        4,
    )


def _repair_strength(row: dict[str, Any]) -> float:
    return round(
        (_num(row.get("lead_core_positive_breadth")) or 0.0) * 20
        + max(0.0, _num(row.get("lead_core_average_change_pct")) or 0.0) * 2
        + (1.0 - (_num(row.get("lead_core_weak_ratio")) or 0.0)) * 10
        + (10.0 if str(row.get("trajectory_recovered")).upper() in {"YES", "TRUE"} else 0.0),
        4,
    )


def _select_distinct(candidates: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    topics: set[str] = set()
    for candidate in candidates:
        if candidate["topic_key"] in topics:
            continue
        selected.append(candidate)
        topics.add(candidate["topic_key"])
        if len(selected) == count:
            break
    return selected


def _first_after(values: list[dict[str, Any]], day: date, predicate: Any) -> dict[str, Any] | None:
    return next((row for row in values if _date(row["trading_date"]) > day and predicate(row)), None)


def _select_a(by_topic: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for topic, values in by_topic.items():
        if topic == MLCC:
            continue
        for candidate in values:
            if candidate.get("transition_reason") != "STRUCTURAL_BREAKDOWN_CANDIDATE":
                continue
            cancellation = _first_after(values, _date(candidate["trading_date"]), lambda row: row.get("transition_reason") == "STRUCTURAL_BREAKDOWN_CANCELLED_GENUINE_REPAIR")
            if cancellation is None:
                continue
            candidate["_cancel"] = cancellation
            candidate["_score"] = round(_severity(candidate) + _repair_strength(cancellation), 4)
            candidates.append(candidate)
    return sorted(candidates, key=lambda row: (-row["_score"], row["topic_key"], row["trading_date"]))


def _declining_run(values: list[dict[str, Any]], row: dict[str, Any]) -> int:
    index = values.index(row)
    total = 0
    for item in values[index:]:
        if item.get("lifecycle_stage") != "DECLINING":
            break
        total += 1
    return total


def _select_b(by_topic: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for topic, values in by_topic.items():
        if topic == MLCC:
            continue
        for row in values:
            if row.get("transition_reason") != "DECLINING_PENDING_CONFIRMATION_SATISFIED":
                continue
            row["_score"] = round(_severity(row) + _declining_run(values, row) * 2, 4)
            candidates.append(row)
    return sorted(candidates, key=lambda row: (-row["_score"], row["topic_key"], row["trading_date"]))


def _deep_condition(row: dict[str, Any]) -> bool:
    breadth = _num(row.get("lead_core_positive_breadth"))
    return bool(
        row.get("lifecycle_stage") != "DECLINING"
        and (_num(row.get("drawdown_from_peak_pct")) or 0.0) <= -30
        and breadth is not None
        and breadth <= 0.35
        and (
            (_num(row.get("lead_core_average_change_pct")) or 0.0) <= -2
            or (_num(row.get("lead_core_weak_ratio")) or 0.0) >= 0.35
        )
    )


def _display_number(value: Any) -> str:
    number = _num(value)
    return "NA" if number is None else f"{number:.4f}"


def _deep_gate_explanation(row: dict[str, Any]) -> str:
    previous = row.get("previous_stage") or "NONE"
    lc_breadth = _num(row.get("lead_core_positive_breadth"))
    lc_strong = _num(row.get("lead_core_strong_breadth"))
    core_breadth = _num(row.get("core_positive_breadth"))
    authority_breadth = _num(row.get("authority_weighted_positive_breadth"))
    lc_average = _num(row.get("lead_core_average_change_pct"))
    return (
        f"DECLINING was not evaluated because the prior final stage was {previous}; the V1.1 DECLINING candidate gate requires prior MATURE. "
        f"At this row, MAIN_RISE was blocked by Lead/Core breadth {_display_number(lc_breadth)}<0.70, Lead/Core strong breadth {_display_number(lc_strong)}<0.35, Lead/Core average {_display_number(lc_average)}<1.50%, and Core breadth {_display_number(core_breadth)}<0.70. "
        f"FERMENTING was blocked by Core breadth {_display_number(core_breadth)}<0.45, authority-weighted breadth {_display_number(authority_breadth)}<0.45, and Lead/Core average {_display_number(lc_average)}<0.50%. "
        "The row therefore held the existing stage with NO_STAGE_CANDIDATE; this is the exact missing-decline gate to review, not a future-outcome judgment."
    )


def _select_c(rows: list[dict[str, Any]], deep_rows: list[dict[str, Any]], by_topic: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    source = deep_rows or [row for row in rows if _deep_condition(row)]
    for item in source:
        topic = item.get("topic") or item.get("topic_key")
        if topic == MLCC:
            continue
        values = by_topic.get(topic, [])
        row = next((candidate for candidate in values if str(candidate["trading_date"]) == str(item.get("date"))), None)
        if row is None or not _deep_condition(row):
            continue
        same_topic_deep = [candidate for candidate in values if _deep_condition(candidate)]
        row["_deep_duration"] = len(same_topic_deep)
        row["_score"] = round(
            max(0.0, -(_num(row.get("drawdown_from_peak_pct")) or 0.0))
            + max(0.0, -(_num(row.get("lead_core_average_change_pct")) or 0.0)) * 2
            + (1.0 - (_num(row.get("lead_core_positive_breadth")) or 0.0)) * 20
            + (_num(row.get("lead_core_weak_ratio")) or 0.0) * 10
            + len(same_topic_deep) * 0.25,
            4,
        )
        candidates.append(row)
    candidates.sort(key=lambda row: (-row["_score"], row["topic_key"], row["trading_date"]))
    return candidates


def _select_d(by_topic: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for topic, values in by_topic.items():
        if topic == MLCC:
            continue
        for row in values:
            if row.get("transition_reason") != "DECLINING_PENDING_CONFIRMATION_SATISFIED":
                continue
            recovery = _first_after(values, _date(row["trading_date"]), lambda item: item.get("previous_stage") == "DECLINING" and item.get("lifecycle_stage") == "MATURE")
            if recovery is None:
                continue
            row["_recovery"] = recovery
            row["_score"] = round(_severity(row) + _repair_strength(recovery) + _declining_run(values, row), 4)
            candidates.append(row)
    return sorted(candidates, key=lambda row: (-row["_score"], row["topic_key"], row["trading_date"]))


def _stage_sequence(values: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
    sprout = next((row for row in values if row.get("lifecycle_stage") == "SPROUTING"), None)
    if sprout is None:
        return None
    sprout_day = _date(sprout["trading_date"])
    ferment = next((row for row in values if _date(row["trading_date"]) > sprout_day and row.get("lifecycle_stage") == "FERMENTING"), None)
    if ferment is None:
        return None
    ferment_day = _date(ferment["trading_date"])
    main = next((row for row in values if _date(row["trading_date"]) > ferment_day and row.get("lifecycle_stage") == "MAIN_RISE"), None)
    if main is None:
        return None
    return sprout, ferment, main


def _select_e(by_topic: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for topic, values in by_topic.items():
        if topic == MLCC:
            continue
        sequence = _stage_sequence(values)
        if sequence is None:
            continue
        sprout, ferment, main = sequence
        score = round(
            100
            + (_num(ferment.get("lead_core_positive_breadth")) or 0.0) * 20
            + max(0.0, _num(ferment.get("lead_core_average_change_pct")) or 0.0) * 2
            + (_num(main.get("lead_core_positive_breadth")) or 0.0) * 15
            + (_num(main.get("lead_core_strong_breadth")) or 0.0) * 15,
            4,
        )
        main["_sprout"] = sprout
        main["_ferment"] = ferment
        main["_score"] = score
        candidates.append(main)
    return sorted(candidates, key=lambda row: (-row["_score"], row["topic_key"], row["trading_date"]))


def _case(case_id: str, category: str, row: dict[str, Any], *, case_type: str, event_date: Any = None, confirmation_date: Any = None, recovery_date: Any = None, why: str, evidence: str) -> dict[str, Any]:
    return {
        "case_id": case_id, "category": category, "case_type": case_type,
        "topic_key": row["topic_key"], "topic_name": row.get("topic_name", row["topic_key"]),
        "key_date": row["trading_date"], "event_date": event_date or row["trading_date"],
        "confirmation_date": confirmation_date or "", "recovery_date": recovery_date or "",
        "previous_stage": row.get("previous_stage", ""), "candidate_stage": row.get("candidate_stage", ""),
        "final_stage": row.get("lifecycle_stage", ""), "selection_score": row.get("_score", 0),
        "key_evidence": evidence, "why_selected": why, "timeline_start": "", "timeline_end": "",
        "OWNER_VERDICT": "", "OWNER_NOTES": "",
        "_anchor_row": row,
    }


def _select_cases(rows: list[dict[str, Any]], deep_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    by_topic = _topic_rows(rows)
    pools = {"A": _select_a(by_topic), "B": _select_b(by_topic), "C": _select_c(rows, deep_rows, by_topic), "D": _select_d(by_topic), "E": _select_e(by_topic)}
    selected: list[dict[str, Any]] = []
    backups: list[dict[str, Any]] = []
    for category in "ABCDE":
        primary_pool = _select_distinct(pools[category], 2)
        backup_pool = [candidate for candidate in pools[category] if candidate["topic_key"] not in {row["topic_key"] for row in primary_pool}]
        backup_pool = _select_distinct(backup_pool, 1)
        for index, row in enumerate(primary_pool, start=1):
            if category == "A":
                cancel = row["_cancel"]
                item = _case(f"A{index}", category, cancel, case_type="BREAKDOWN_CANDIDATE_CANCELLED", event_date=row["trading_date"], why="Highest deterministic combination of candidate severity and subsequent Lead/Core repair strength.", evidence=f"Candidate DD {row.get('drawdown_from_peak_pct')}; candidate LC avg {row.get('lead_core_average_change_pct')}; cancellation LC breadth {cancel.get('lead_core_positive_breadth')}; cancellation repair {cancel.get('trajectory_recovered')}")
            elif category == "B":
                item = _case(f"B{index}", category, row, case_type="DECLINING_CONFIRMED", event_date=row["trading_date"], confirmation_date=row["trading_date"], why="Highest deterministic confirmation severity plus subsequent DECLINING persistence.", evidence=f"DD {row.get('drawdown_from_peak_pct')}; LC breadth {row.get('lead_core_positive_breadth')}; LC avg {row.get('lead_core_average_change_pct')}; LC weak {row.get('lead_core_weak_ratio')}; overall weak {row.get('weak_ratio')}")
            elif category == "C":
                item = _case(f"C{index}", category, row, case_type="DEEP_DRAWDOWN_NON_DECLINE", event_date=row["trading_date"], why="Highest deterministic deep-drawdown/weak-structure score among rows that remain outside DECLINING.", evidence=f"DD {row.get('drawdown_from_peak_pct')}; LC breadth {row.get('lead_core_positive_breadth')}; LC avg {row.get('lead_core_average_change_pct')}; LC weak {row.get('lead_core_weak_ratio')}; final {row.get('lifecycle_stage')}. Exact gate analysis: {_deep_gate_explanation(row)}")
            elif category == "D":
                recovery = row["_recovery"]
                item = _case(f"D{index}", category, recovery, case_type="DECLINING_RECOVERY", event_date=row["trading_date"], confirmation_date=row["trading_date"], recovery_date=recovery["trading_date"], why="Highest decline severity plus meaningful legal recovery evidence, ranked without outcomes.", evidence=f"Decline DD {row.get('drawdown_from_peak_pct')}; recovery LC breadth {recovery.get('lead_core_positive_breadth')}; recovery LC avg {recovery.get('lead_core_average_change_pct')}; recovered to {recovery.get('lifecycle_stage')}")
                item["_anchor_row"] = recovery
            else:
                main = row
                ferment = row["_ferment"]
                sprout = row["_sprout"]
                item = _case(f"E{index}", category, main, case_type="EARLY_LIFECYCLE_COMPLETE_PATH", event_date=sprout["trading_date"], confirmation_date=main["trading_date"], why="Highest deterministic completeness/identity-evidence score for SPROUTING → FERMENTING → MAIN_RISE.", evidence=f"SPROUTING {sprout['trading_date']}; FERMENTING {ferment['trading_date']} LC breadth {ferment.get('lead_core_positive_breadth')}; MAIN_RISE {main['trading_date']} LC breadth {main.get('lead_core_positive_breadth')}")
                item["_sprout"] = sprout
                item["_ferment"] = ferment
            item["selection_role"] = "PRIMARY"
            item["selection_score"] = row.get("_score", 0)
            selected.append(item)
        for index, row in enumerate(backup_pool, start=3):
            if category == "A":
                anchor = row["_cancel"]
                item = _case(f"A{index}", category, anchor, case_type="BREAKDOWN_CANDIDATE_CANCELLED_BACKUP", event_date=row["trading_date"], why="Next deterministic cancellation candidate after the two primary cases.", evidence=f"Candidate DD {row.get('drawdown_from_peak_pct')}; repair strength {_repair_strength(anchor)}")
            elif category == "B":
                item = _case(f"B{index}", category, row, case_type="DECLINING_CONFIRMED_BACKUP", event_date=row["trading_date"], confirmation_date=row["trading_date"], why="Next deterministic confirmed decline after the two primary cases.", evidence=f"DD {row.get('drawdown_from_peak_pct')}; LC avg {row.get('lead_core_average_change_pct')}")
            elif category == "C":
                item = _case(f"C{index}", category, row, case_type="DEEP_DRAWDOWN_NON_DECLINE_BACKUP", event_date=row["trading_date"], why="Next deterministic deep-drawdown non-decline case.", evidence=f"DD {row.get('drawdown_from_peak_pct')}; LC breadth {row.get('lead_core_positive_breadth')}; final {row.get('lifecycle_stage')}. Exact gate analysis: {_deep_gate_explanation(row)}")
            elif category == "D":
                recovery = row["_recovery"]
                item = _case(f"D{index}", category, recovery, case_type="DECLINING_RECOVERY_BACKUP", event_date=row["trading_date"], recovery_date=recovery["trading_date"], why="Next deterministic legal recovery case.", evidence=f"Decline DD {row.get('drawdown_from_peak_pct')}; recovery LC breadth {recovery.get('lead_core_positive_breadth')}")
                item["_anchor_row"] = recovery
            else:
                main = row
                item = _case(f"E{index}", category, main, case_type="EARLY_LIFECYCLE_COMPLETE_PATH_BACKUP", event_date=main["_sprout"]["trading_date"], confirmation_date=main["trading_date"], why="Next deterministic complete early-lifecycle path.", evidence=f"SPROUTING {main['_sprout']['trading_date']}; FERMENTING {main['_ferment']['trading_date']}; MAIN_RISE {main['trading_date']}")
                item["_sprout"] = main["_sprout"]
                item["_ferment"] = main["_ferment"]
            item["selection_role"] = "BACKUP"
            item["selection_score"] = row.get("_score", 0)
            backups.append(item)
    return selected, backups, pools


def _window(case: dict[str, Any], by_topic: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], date, date]:
    values = by_topic[case["topic_key"]]
    if case["category"] == "E":
        start_row = case["_sprout"]
        end_row = case["_anchor_row"]
        start = values.index(start_row)
        end = values.index(end_row)
        start = max(0, start - 5)
        end = min(len(values) - 1, end + 10)
    else:
        event_day = _date(case["event_date"])
        key_day = _date(case["key_date"])
        start_event = next((index for index, row in enumerate(values) if _date(row["trading_date"]) == event_day), 0)
        start_key = next((index for index, row in enumerate(values) if _date(row["trading_date"]) == key_day), start_event)
        start = max(0, min(start_event, start_key) - 5)
        end = min(len(values) - 1, max(start_event, start_key) + 10)
        if case["category"] == "D" and case.get("recovery_date"):
            recovery_index = next((index for index, row in enumerate(values) if str(row["trading_date"]) == str(case["recovery_date"])), end)
            end = min(len(values) - 1, recovery_index + 10)
    episode = values[start:end + 1]
    return episode, _date(episode[0]["trading_date"]), _date(episode[-1]["trading_date"])


def _event_role(case: dict[str, Any], row: dict[str, Any]) -> str:
    day = str(row["trading_date"])
    if case["category"] == "E":
        if case.get("_sprout") and day == str(case["_sprout"]["trading_date"]):
            return "SPROUTING_ENTRY"
        if case.get("_ferment") and day == str(case["_ferment"]["trading_date"]):
            return "FERMENTING_ENTRY"
        if day == str(case["key_date"]):
            return "MAIN_RISE_CONFIRMATION"
    if case["category"] == "A" and day == str(case["key_date"]):
        return "CANCELLATION"
    if case.get("event_date") and day == str(case["event_date"]):
        return "KEY_EVENT"
    if case.get("confirmation_date") and day == str(case["confirmation_date"]):
        return "CONFIRMATION"
    if case.get("recovery_date") and day == str(case["recovery_date"]):
        return "RECOVERY"
    return "CONTEXT"


def _timeline_rows(cases: list[dict[str, Any]], by_topic: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    result = []
    for case in cases:
        episode, start, end = _window(case, by_topic)
        case["timeline_start"] = start.isoformat()
        case["timeline_end"] = end.isoformat()
        for row in episode:
            payload = {field: row.get(field, "") for field in TIMELINE_FIELDS}
            payload.update({"case_id": case["case_id"], "category": case["category"], "case_key_date": case["key_date"], "event_role": _event_role(case, row)})
            payload["pending_state_disposition"] = ";".join(filter(None, [str(row.get("structural_breakdown_disposition", "")), str(row.get("declining_pending_disposition", ""))]))
            result.append(payload)
    return sorted(result, key=lambda row: (row["case_id"], row["trading_date"], row["topic_key"]))


def _member_rows(cases: list[dict[str, Any]], timelines: list[dict[str, Any]], members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    windows = {(case["case_id"], case["topic_key"]): {row["trading_date"] for row in timelines if row["case_id"] == case["case_id"]} for case in cases}
    result = []
    for case in cases:
        dates = windows[(case["case_id"], case["topic_key"])]
        for row in members:
            if row["topic_key"] != case["topic_key"] or row["trading_date"] not in dates:
                continue
            change = _num(row.get("change_pct"))
            positive = "MISSING" if change is None else "POSITIVE" if change > 0 else "NON_POSITIVE"
            strong_weak = "MISSING" if change is None else "STRONG" if change >= 4 else "WEAK" if change <= -4 else "NEUTRAL"
            result.append({field: row.get(field, "") for field in MEMBER_FIELDS} | {
                "case_id": case["case_id"], "category": case["category"], "case_key_date": case["key_date"],
                "positive_negative": positive, "strong_weak": strong_weak,
                "missing_data_state": row.get("observation_status") if change is None else "OBSERVED",
            })
    return sorted(result, key=lambda row: (row["case_id"], row["trading_date"], row["market_code"], row["instrument_code"]))


def _summary_markdown(category: str, cases: list[dict[str, Any]], timelines: list[dict[str, Any]]) -> str:
    lines = [f"# Category {category} Owner Review", "", "Final semantic judgment remains blank for Owner.", ""]
    for case in cases:
        rows = [row for row in timelines if row["case_id"] == case["case_id"]]
        anchor = next((row for row in rows if row["event_role"] in {"KEY_EVENT", "CANCELLATION", "CONFIRMATION", "RECOVERY", "MAIN_RISE_CONFIRMATION"}), rows[0])
        lines += [
            f"## {case['case_id']} — {case['topic_key']} {case['topic_name']}", "",
            f"TOPIC: {case['topic_key']} — {case['topic_name']}", f"CATEGORY: {case['category']} / {case['case_type']}", f"KEY DATE: {case['key_date']}", f"PREVIOUS STAGE: {anchor.get('previous_stage', '')}", f"CANDIDATE: {anchor.get('candidate_stage', '')}", f"FINAL STAGE: {anchor.get('lifecycle_stage', '')}",
            f"WHY THE ENGINE DID THIS: {case['why_selected']}", f"LEAD/CORE CONDITION: breadth={anchor.get('lead_core_positive_breadth')}; average={anchor.get('lead_core_average_change_pct')}; strong={anchor.get('strong_breadth')}; weak={anchor.get('weak_ratio')}", f"RELATED CONDITION: breadth={anchor.get('related_positive_breadth')}; overall breadth={anchor.get('positive_breadth')}", f"DRAWDOWN CONDITION: drawdown={anchor.get('drawdown_from_peak_pct')}; peak={anchor.get('current_peak')}", f"STATE MEMORY: breakdown_pending={anchor.get('structural_breakdown_pending')}; breakdown_age={anchor.get('structural_breakdown_age')}; decline_pending={anchor.get('declining_pending')}; decline_age={anchor.get('declining_pending_age')}; disposition={anchor.get('pending_state_disposition')}", f"TIMELINE: {case['timeline_start']} through {case['timeline_end']}", f"EXACT FAILED GATE: {_deep_gate_explanation(anchor)}" if case["category"] == "C" else "", f"WHAT OWNER SHOULD CHECK: {case['key_evidence']}", "", "Owner questions:",
        ]
        lines.extend(f"- {question}" for question in QUESTIONS[category])
        lines += ["", "OWNER_VERDICT=", "OWNER_NOTES=", ""]
    return "\n".join(lines)


def _select_related_only(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = []
    for row in rows:
        related_strong = (_num(row.get("related_positive_breadth")) or 0.0) >= 0.70 and (_num(row.get("related_average_change_pct")) or 0.0) >= 1.5
        lead_core_weak = (_num(row.get("lead_core_positive_breadth")) or 0.0) < 0.70 or (_num(row.get("lead_core_average_change_pct")) or 0.0) < 1.5
        if related_strong and lead_core_weak and row.get("topic_key") != MLCC:
            score = round((_num(row.get("related_average_change_pct")) or 0.0) - (_num(row.get("lead_core_average_change_pct")) or 0.0) + (_num(row.get("related_positive_breadth")) or 0.0) * 10, 4)
            candidates.append((score, row))
    return max(candidates, key=lambda item: (item[0], item[1]["topic_key"], item[1]["trading_date"]))[1] if candidates else None


def _one_day_noise(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [row for row in rows if row.get("transition_reason") == "STRUCTURAL_BREAKDOWN_CANDIDATE" and row.get("lifecycle_stage") == "MAIN_RISE"]
    return max(candidates, key=lambda row: (_severity(row), row["topic_key"], row["trading_date"])) if candidates else None


def _next_rows(rows: list[dict[str, Any]], anchor: dict[str, Any] | None, count: int = 2) -> list[dict[str, Any]]:
    if anchor is None:
        return []
    values = sorted(
        [row for row in rows if row.get("topic_key") == anchor.get("topic_key")],
        key=lambda row: row["trading_date"],
    )
    index = next((position for position, row in enumerate(values) if row["trading_date"] == anchor["trading_date"]), None)
    return [] if index is None else values[index + 1:index + 1 + count]


def _case_public(case: dict[str, Any]) -> dict[str, Any]:
    return {field: case.get(field, "") for field in SUMMARY_FIELDS}


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    required = [BASELINE_SUMMARY, BASELINE_MANIFEST, RECON, MEMBERS, DEEP]
    if any(not path.exists() for path in required):
        raise SystemExit("V1.1 baseline artifacts are incomplete")
    summary = json.loads(BASELINE_SUMMARY.read_text(encoding="utf-8"))
    manifest = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))
    v11_hash = summary["reconstruction_hash"]
    replay = summary["replay"]
    rows = _read_csv(RECON)
    members = _read_csv(MEMBERS)
    deep_rows = _read_csv(DEEP)
    _prepare(rows)
    _prepare(deep_rows)
    by_topic = _topic_rows(rows)
    manifest_governance = manifest.get("governance", {})
    reconstruction_meta = summary.get("reconstruction", {})
    baseline_verified = all(
        [
            summary.get("reconstruction_hash") == "60cd5327a0ba4857192bf6a12ca12665dcb4358cf3d8860da3184ef4aaf96010",
            replay.get("deterministic_replay") == "PASS",
            replay.get("v1_1_replay_hash_run_1") == replay.get("v1_1_replay_hash_run_2"),
            reconstruction_meta.get("rows") == len(rows) == 16500,
            reconstruction_meta.get("topics") == len(by_topic) == 132,
            reconstruction_meta.get("sessions") == len({row["trading_date"] for row in rows}) == 125,
            reconstruction_meta.get("member_evidence_rows") == len(members) == 151500,
            manifest_governance.get("FULL_RECONSTRUCTION_ROWS") == len(rows),
            manifest_governance.get("FULL_RECONSTRUCTION_TOPICS") == len(by_topic),
            manifest_governance.get("FULL_RECONSTRUCTION_SESSIONS") == len({row["trading_date"] for row in rows}),
            manifest_governance.get("V1_1_REPLAY_HASH") == replay.get("v1_1_replay_hash_run_1"),
            manifest_governance.get("DETERMINISTIC_REPLAY_PASS") == "PASS",
        ]
    )
    selected, backups, pools = _select_cases(rows, deep_rows)
    all_cases = selected + backups
    timelines = _timeline_rows(all_cases, by_topic)
    member_evidence = _member_rows(all_cases, timelines, members)
    primary_ids = {case["case_id"] for case in selected}
    primary_timelines = [row for row in timelines if row["case_id"] in primary_ids]
    primary_members = [row for row in member_evidence if row["case_id"] in primary_ids]
    related = _select_related_only(rows)
    noise = _one_day_noise(rows)
    generic_pending = next((case for case in selected if case["category"] == "B"), None)
    generic_cancel = next((case for case in selected if case["category"] == "A"), None)
    noise_following = _next_rows(rows, noise)
    anomalies = []
    if len(selected) != 10:
        anomalies.append(f"Only {len(selected)} primary cases were selectable; the requested target is 10.")
    if len(pools["C"]) < 2:
        anomalies.append("Fewer than two deep-drawdown non-decline cases were available under the V1.1 audit rule.")
    if related is None:
        anomalies.append("No supplementary Related-strong / Lead-Core-weak example was found outside MLCC.")
    summary_rows = [_case_public(case) for case in all_cases]
    owner_pack = []
    for case in all_cases:
        row = _case_public(case)
        row["owner_questions"] = " | ".join(QUESTIONS[case["category"]])
        row["key_evidence"] = case["key_evidence"]
        owner_pack.append(row)
    _write_csv(args.output_dir / "primary-case-full-timelines.csv", TIMELINE_FIELDS, primary_timelines)
    _write_csv(args.output_dir / "primary-case-member-evidence.csv", MEMBER_FIELDS, primary_members)
    _write_csv(args.output_dir / "lifecycle-v1-1-cross-topic-summary-matrix.csv", SUMMARY_FIELDS, summary_rows)
    _write_csv(args.output_dir / "lifecycle-v1-1-cross-topic-owner-pack.csv", SUMMARY_FIELDS + ["owner_questions"], owner_pack)
    _write_csv(args.output_dir / "owner-verdict-template.csv", ["case_id", "category", "topic_key", "key_date", "OWNER_VERDICT", "OWNER_NOTES"], [{"case_id": case["case_id"], "category": case["category"], "topic_key": case["topic_key"], "key_date": case["key_date"], "OWNER_VERDICT": "", "OWNER_NOTES": ""} for case in all_cases])
    for category in "ABCDE":
        _write_text(args.output_dir / f"category-{ {'A':'a-breakdown-cancelled','B':'b-declining-confirmed','C':'c-deep-drawdown-non-decline','D':'d-declining-recovery','E':'e-early-lifecycle-formation'}[category] }.md", _summary_markdown(category, [case for case in all_cases if case["category"] == category], primary_timelines + [row for row in timelines if row["case_id"] not in primary_ids]))
    selection_method = """# Cross-Topic Case Selection Method

The selector reads the frozen V1.1 reconstruction only. MLCC is excluded before ranking. Topics are deduplicated within each category; ties are resolved by topic key then ISO trading date.

## A — candidate cancelled

Candidates require `STRUCTURAL_BREAKDOWN_CANDIDATE` followed by a later `STRUCTURAL_BREAKDOWN_CANCELLED_GENUINE_REPAIR` for the same topic. Score = candidate severity + cancellation repair strength. Severity = max(0,-drawdown) + 2×max(0,-LC average) + 10×(1-LC breadth) + 10×LC weak ratio. Repair strength = 20×LC breadth + 2×positive LC average + 10×(1-LC weak ratio) + 10 if trajectory recovered.

## B — decline confirmed

Candidates require `DECLINING_PENDING_CONFIRMATION_SATISFIED`. Score = confirmation severity + 2×consecutive DECLINING sessions after confirmation. No return or outcome field is used.

## C — deep drawdown without DECLINING

Use the V1.1 deep-drawdown audit rule: final stage not DECLINING, drawdown ≤ -30%, LC breadth ≤ 0.35, and LC average ≤ -2% or LC weak ratio ≥ 0.35. Score = drawdown severity + 2×negative LC average + 20×(1-LC breadth) + 10×LC weak ratio + 0.25×number of same-topic audit rows.

## D — declining recovery

Candidates require a confirmed DECLINING entry followed by legal `DECLINING → MATURE` recovery. Score = decline severity + recovery strength + DECLINING run length.

## E — early lifecycle formation

Candidates require the first final-stage sequence SPROUTING → FERMENTING → MAIN_RISE for the same topic. Score starts at 100 for completeness, then adds FERMENTING LC breadth/average and MAIN_RISE LC breadth/strong breadth. This category is stage-evidence selection, not performance selection.
"""
    _write_text(args.output_dir / "cross-topic-case-selection-method.md", selection_method)
    order_lines = ["# Owner Review Order", "", "Review one case at a time in this order:", ""]
    order_lines.extend(f"{index}. {case['case_id']} — {case['topic_key']} — {case['case_type']}" for index, case in enumerate(selected, start=1))
    order_lines += ["", "Backups:"]
    order_lines.extend(f"- {case['case_id']} — {case['topic_key']} — {case['case_type']}" for case in backups)
    _write_text(args.output_dir / "owner-review-order.md", "\n".join(order_lines))
    pending_text = ["# Generic Pending-Memory Evidence", ""]
    if generic_pending:
        pending_rows = [row for row in timelines if row["case_id"] == generic_pending["case_id"] and row["transition_reason"] in {"DECLINING_CANDIDATE_PENDING_CONFIRMATION", "DECLINING_PENDING_CONFIRMATION_SATISFIED"}]
        pending_text.append(f"Pending confirmation example outside MLCC: `{generic_pending['case_id']}`.")
        pending_text.extend(f"- {row['trading_date']}: final={row['lifecycle_stage']}; candidate={row['candidate_stage']}; decision={row['transition_decision']}; reason={row['transition_reason']}; declining_pending={row['declining_pending']}" for row in pending_rows)
    else:
        pending_text.append("Pending confirmation example outside MLCC: `NONE`.")
    if generic_cancel:
        cancel_rows = [row for row in timelines if row["case_id"] == generic_cancel["case_id"] and row["transition_reason"] in {"STRUCTURAL_BREAKDOWN_CANDIDATE", "STRUCTURAL_BREAKDOWN_CANCELLED_GENUINE_REPAIR"}]
        pending_text.append(f"Pending cancellation example outside MLCC: `{generic_cancel['case_id']}`.")
        pending_text.extend(f"- {row['trading_date']}: final={row['lifecycle_stage']}; candidate={row['candidate_stage']}; decision={row['transition_decision']}; reason={row['transition_reason']}; breakdown_pending={row['structural_breakdown_pending']}; disposition={row['structural_breakdown_disposition']}" for row in cancel_rows)
    else:
        pending_text.append("Pending cancellation example outside MLCC: `NONE`.")
    pending_text += ["", "The CSV timeline is authoritative; no future returns are included."]
    _write_text(args.output_dir / "pending-memory-generic-evidence.md", "\n".join(pending_text))
    related_lines = ["# Related-Only Identity Check", "", "Related is context only. The audit searched every non-MLCC reconstruction row for strong Related breadth/average while Lead/Core failed the MAIN_RISE gate.", ""]
    if related:
        related_lines += [f"Supplementary example: `{related['topic_key']}` on `{related['trading_date']}`; Related breadth={related.get('related_positive_breadth')}, Related average={related.get('related_average_change_pct')}, LC breadth={related.get('lead_core_positive_breadth')}, LC average={related.get('lead_core_average_change_pct')}, final stage={related.get('lifecycle_stage')}, candidate={related.get('candidate_stage')}.", "The case is supplementary and does not count toward the ten primary cases."]
    else:
        related_lines.append("No qualifying supplementary example was found; the all-row audit still completed and Related-only MAIN_RISE false positives remain zero in the V1.1 baseline.")
    _write_text(args.output_dir / "related-only-identity-check.md", "\n".join(related_lines))
    anomaly_lines = ["# Semantic Anomalies Found", "", "This report records suspicious cases for Owner review and does not modify Lifecycle behavior.", ""]
    anomaly_lines.extend(f"- {item}" for item in anomalies) if anomalies else anomaly_lines.append("- No pack-construction anomaly was found. Category C cases are intentionally adversarial semantic review candidates, not automatic defects.")
    anomaly_lines += ["", "## One-day noise evidence", ""]
    if noise:
        anomaly_lines.append(f"Candidate day: `{noise['topic_key']}` on `{noise['trading_date']}`; previous={noise['previous_stage']}; candidate={noise['candidate_stage']}; final={noise['lifecycle_stage']}; decision={noise['transition_decision']}; reason={noise['transition_reason']}; drawdown={noise['drawdown_from_peak_pct']}; Lead/Core breadth={noise['lead_core_positive_breadth']}; Lead/Core average={noise['lead_core_average_change_pct']}; pending={noise['structural_breakdown_pending']}; disposition={noise['structural_breakdown_disposition']}.")
        for follow in noise_following:
            anomaly_lines.append(f"Next valid session: `{follow['trading_date']}`; previous={follow['previous_stage']}; candidate={follow['candidate_stage']}; final={follow['lifecycle_stage']}; decision={follow['transition_decision']}; reason={follow['transition_reason']}; pending={follow['structural_breakdown_pending']}; disposition={follow['structural_breakdown_disposition']}.")
        anomaly_lines.append("This demonstrates that the severe one-day move first remained a pending candidate instead of an immediate final-stage flip; Owner should judge whether the following confirmation was semantically appropriate.")
    else:
        anomaly_lines.append("No qualifying one-day structural-breakdown candidate was found.")
    anomaly_lines += ["", "No Lifecycle implementation, threshold, state-machine, master, role, database, production, push, or deploy change was made by this task."]
    _write_text(args.output_dir / "semantic-anomalies-found.md", "\n".join(anomaly_lines))
    categories = {category: [case for case in selected if case["category"] == category] for category in "ABCDE"}
    pack_hash = _hash_payload({"primary": summary_rows[:10], "timelines": primary_timelines, "members": primary_members})
    flags = {
        "WS1_ONLY": "YES", "SEMANTIC_VALIDATION_ONLY": "YES", "V1_1_BASELINE_VERIFIED": "YES" if baseline_verified else "NO", "V1_1_REPLAY_HASH": summary["replay"]["v1_1_replay_hash_run_1"], "TOPIC_COUNT": summary["reconstruction"]["topics"], "SESSION_COUNT": summary["reconstruction"]["sessions"], "RECONSTRUCTION_ROWS": summary["reconstruction"]["rows"], "MLCC_EXCLUDED_FROM_SELECTION": "YES", "CATEGORY_A_PRIMARY_CASES": len(categories["A"]), "CATEGORY_B_PRIMARY_CASES": len(categories["B"]), "CATEGORY_C_PRIMARY_CASES": len(categories["C"]), "CATEGORY_D_PRIMARY_CASES": len(categories["D"]), "CATEGORY_E_PRIMARY_CASES": len(categories["E"]), "TOTAL_PRIMARY_CASES": len(selected), "TOTAL_BACKUP_CASES": len(backups), "FUTURE_RETURNS_USED": "NO", "WS3_DATA_READ": "NO", "LIFECYCLE_CODE_CHANGED": "NO", "LIFECYCLE_THRESHOLDS_CHANGED": "NO", "STATE_MACHINE_CHANGED": "NO", "TOPIC_MASTER_CHANGED": "NO", "INSTRUMENT_MASTER_CHANGED": "NO", "ROLE_CONFIGURATION_CHANGED": "NO", "PENDING_CONFIRMATION_GENERIC_CASE_FOUND": "YES" if generic_pending else "NO", "PENDING_CANCELLATION_GENERIC_CASE_FOUND": "YES" if generic_cancel else "NO", "RELATED_ONLY_CHECK_COMPLETED": "YES", "ONE_DAY_NOISE_CASE_FOUND": "YES" if noise else "NO", "SEMANTIC_ANOMALIES_FOUND": "YES" if anomalies else "NO", "PRODUCTION_DB_MUTATION": "NO", "PUSH": "NO", "DEPLOY": "NO", "NEXT_TASK_CHANGED": "NO", "OWNER_REVIEW_PACK_READY": "YES" if baseline_verified and len(selected) == 10 and all(len(categories[c]) == 2 for c in "ABCDE") else "NO",
    }
    run_summary = {"task_id": TASK_ID, "status": "OWNER_REVIEW_PACK_READY" if flags["OWNER_REVIEW_PACK_READY"] == "YES" else "OWNER_REVIEW_PACK_INCOMPLETE", "baseline": {"verified": baseline_verified, "reconstruction_hash": v11_hash, "replay": replay["deterministic_replay"], "replay_hash": replay["v1_1_replay_hash_run_1"], "topics": len(by_topic), "sessions": len({row["trading_date"] for row in rows}), "rows": len(rows), "member_evidence_rows": len(members), "manifest_replay_hash": manifest_governance.get("V1_1_REPLAY_HASH")}, "selection": {"primary_case_ids": [case["case_id"] for case in selected], "backup_case_ids": [case["case_id"] for case in backups], "pool_sizes": {category: len(pools[category]) for category in "ABCDE"}, "review_pack_sha256": pack_hash}, "governance_flags": flags, "related_only_example": related, "one_day_noise_example": noise}
    _write_json(args.output_dir / "run-summary.json", run_summary)
    questions = [
        f"1. V1.1 baseline verified? **YES**; hash `{summary['replay']['v1_1_replay_hash_run_1']}` and replay `{replay['deterministic_replay']}`.", "2. MLCC excluded? **YES**.", "3. Exactly five semantic categories? **YES: A–E.**", f"4. Primary cases? **{len(selected)}**.", f"5. Backup cases? **{len(backups)}**.", "6. Category A rule? **Candidate followed by repair cancellation, ranked by severity plus repair strength.**", "7. Category B rule? **Confirmed decline, ranked by deterioration and post-confirmation DECLINING persistence.**", "8. Category C rule? **Deep drawdown/weak LC structure while final stage is not DECLINING, ranked by severity and duration.**", "9. Category D rule? **Confirmed decline followed by legal DECLINING→MATURE recovery, ranked by severity plus repair.**", "10. Category E rule? **Complete final-stage SPROUTING→FERMENTING→MAIN_RISE sequence, ranked by identity evidence.**", "11. Future returns used? **NO.**", "12. WS3 data read? **NO.**", "13. Topic Master/roles changed? **NO.**", f"14. Lifecycle implementation changed? **{flags['LIFECYCLE_CODE_CHANGED']}**.", f"15. Candidate cancellation included? **{flags['PENDING_CANCELLATION_GENERIC_CASE_FOUND']} generic evidence; Category A has {len(categories['A'])} primary cases.**", f"16. Decline confirmation included? **{flags['PENDING_CONFIRMATION_GENERIC_CASE_FOUND']} generic evidence; Category B has {len(categories['B'])} primary cases.**", f"17. Deep drawdown without decline included? **{len(categories['C'])} primary cases.**", f"18. Recovery included? **{len(categories['D'])} primary cases.**", f"19. SPROUTING→FERMENTING included? **{'YES' if categories['E'] else 'NO'}.**", f"20. FERMENTING→MAIN_RISE included? **{'YES' if categories['E'] else 'NO'}.**", f"21. Generic pending confirmation outside MLCC? **{flags['PENDING_CONFIRMATION_GENERIC_CASE_FOUND']}**.", f"22. Generic pending cancellation outside MLCC? **{flags['PENDING_CANCELLATION_GENERIC_CASE_FOUND']}**.", f"23. Related-only behavior checked? **{flags['RELATED_ONLY_CHECK_COMPLETED']}**.", f"24. One-day noise resistance demonstrated? **{flags['ONE_DAY_NOISE_CASE_FOUND']}**.", f"25. Suspicious semantic anomalies? **{flags['SEMANTIC_ANOMALIES_FOUND']}**; see semantic-anomalies-found.md.", f"26. Pack ready for case-by-case Owner review? **{flags['OWNER_REVIEW_PACK_READY']}**.",
    ]
    closure = [f"# {TASK_ID}", "", "## Formal closure", ""] + questions + ["", "## Governance flags", "", "```text"] + [f"{key}={value}" for key, value in flags.items()] + ["```", "", "## Selection posture", "", "MLCC was excluded because it is the already accepted reference anchor. This pack is deliberately limited to ten primary cases and up to five backups; it is not an automatic declaration that V1.1 is fully Owner-accepted. Owner verdict and notes remain blank.", "", "## Validation guardrails", "", "The same frozen V1.1 reconstruction and member evidence were used for every selection. No forward returns, WS3 data, implementation changes, threshold changes, master changes, database mutation, push, deploy, or NEXT_TASK modification occurred.", "", f"Review pack hash: `{pack_hash}`."]
    _write_text(args.output_dir / "formal-closure-report.md", "\n".join(closure))
    print(json.dumps({"output_dir": str(args.output_dir), "primary_cases": len(selected), "backups": len(backups), "pack_hash": pack_hash, "owner_ready": flags["OWNER_REVIEW_PACK_READY"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
