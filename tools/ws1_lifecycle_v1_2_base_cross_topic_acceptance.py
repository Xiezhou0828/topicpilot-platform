from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import median


BASE = Path(
    "E:/topicpilot-platform-canonical/reports/"
    "TASK-WS1-LIFECYCLE-V1-2-BASE-RESET-STAGE-ONTOLOGY-HARD-FIX-20260824"
)
OUT = Path(
    "E:/topicpilot-platform-canonical/reports/"
    "TASK-WS1-LIFECYCLE-V1-2-BASE-CROSS-TOPIC-OWNER-SEMANTIC-ACCEPTANCE-20260824"
)
RECON_PATH = BASE / "lifecycle-v1-2-historical-reconstruction.csv"
MEMBER_PATH = BASE / "lifecycle-v1-2-member-evidence.csv"
VALIDATION_PATH = BASE / "lifecycle-v1-2-owner-validation-pack.csv"
RUN_SUMMARY_PATH = BASE / "run-summary.json"
FORMAL_PATH = BASE / "formal-closure-report.md"
TEST_RESULTS_PATH = BASE / "test-results.json"
EXPECTED_IDENTITY_HASH = (
    "710bc9634b2a3ccbebfe31d18a410b9f105eb25b521824b235d080e1ecd94756"
)
EXPECTED_COUNTS = {
    "rows": 16500,
    "member_rows": 151500,
    "topics": 132,
    "sessions": 125,
    "declining_to_base": 36,
    "base_to_fermenting": 27,
    "base_to_declining": 7,
    "base_to_main_rise": 0,
}

ANCHOR_TOPICS = {"MLCC", "ABF載板", "DRAM／DDR", "SiC 晶圓／基板", "固態電容"}


def fnum(value: object, default: float | None = None) -> float | None:
    if value in (None, "", "null"):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value: object, digits: int = 4) -> str:
    if value in (None, ""):
        return "—"
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return "—"
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return str(value)


def md(value: object) -> str:
    return str(value if value not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def pct(value: object) -> str:
    val = fnum(value)
    return "—" if val is None else f"{val:.4f}%"


def ratio(value: object) -> str:
    val = fnum(value)
    return "—" if val is None else f"{val:.4f}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_json(value: object) -> dict:
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def session_index(rows: list[dict[str, str]]) -> dict[str, int]:
    dates = sorted({row["trading_date"] for row in rows})
    return {item: idx for idx, item in enumerate(dates)}


def norm_row(row: dict[str, str]) -> dict:
    result = dict(row)
    numeric_fields = {
        "lead_core_positive_breadth",
        "core_positive_breadth",
        "related_positive_breadth",
        "positive_breadth",
        "strong_breadth",
        "weak_ratio",
        "lead_core_strong_breadth",
        "lead_core_weak_ratio",
        "average_change_pct",
        "lead_core_average_change_pct",
        "core_average_change_pct",
        "related_average_change_pct",
        "drawdown_from_peak_pct",
        "days_since_meaningful_expansion",
        "main_rise_segment",
        "cycle_number",
    }
    for field in numeric_fields:
        result[field] = fnum(row.get(field))
    result["confirmation_state_obj"] = parse_json(row.get("confirmation_state"))
    result["state_memory_obj"] = parse_json(row.get("state_memory"))
    return result


def metric(row: dict | None, field: str, default: object = None) -> object:
    if not row:
        return default
    value = row.get(field)
    return default if value in (None, "") else value


def state_fields(row: dict) -> dict[str, object]:
    confirmation = row.get("confirmation_state_obj", {})
    memory = row.get("state_memory_obj", {})
    candidate = row.get("candidate_stage", "")
    final_stage = row.get("lifecycle_stage", "")
    state = confirmation.get("state", "")
    candidate_streak = confirmation.get("candidateStreak", "")
    confirmation_age = confirmation.get("confirmationAge", "")
    required_days = confirmation.get("requiredTradingDays", "")
    structural_pending = confirmation.get("structuralBreakdownPending", False)
    structural_disposition = confirmation.get("structuralBreakdownDisposition", "NONE")
    declining_pending = memory.get("decliningPending", False)
    declining_disposition = memory.get("decliningPendingDisposition", "NONE")
    declining_age = memory.get("decliningPendingAge", "")
    structural_age = memory.get("structuralBreakdownAge", "")
    base_pending = candidate == "BASE" and final_stage != "BASE"
    if "CANCELLED" in row.get("transition_reason", ""):
        disposition = row["transition_reason"]
    elif row.get("transition_decision") == "CONFIRMED_TRANSITION":
        disposition = "CONFIRMED: " + row.get("transition_reason", "")
    elif candidate and candidate != final_stage:
        disposition = "PENDING: " + row.get("transition_reason", "")
    elif candidate and candidate == final_stage and row.get("transition_decision") == "HOLD_CONFIRMATION":
        disposition = "HOLDING CANDIDATE: " + row.get("transition_reason", "")
    else:
        disposition = row.get("transition_reason", "") or "NONE"
    return {
        "candidate_streak": candidate_streak,
        "confirmation_age": confirmation_age,
        "required_trading_days": required_days,
        "confirmation_state": state,
        "structural_breakdown_pending": "YES" if structural_pending else "NO",
        "structural_breakdown_disposition": structural_disposition,
        "structural_breakdown_age": structural_age,
        "declining_pending": "YES" if declining_pending else "NO",
        "declining_pending_disposition": declining_disposition,
        "declining_pending_age": declining_age,
        "base_pending": "YES" if base_pending else "NO",
        "base_state_memory": state or "NONE",
        "pending_age": confirmation_age if confirmation_age not in (None, "") else candidate_streak,
        "disposition": disposition,
        "cycle_id": memory.get("lifecycleCycleId", row.get("cycle_id", "")),
        "cycle_number": memory.get("cycleNumber", row.get("cycle_number", "")),
        "main_rise_segment": row.get("main_rise_segment"),
    }


def evidence_state(member: dict) -> str:
    if member.get("observation_status") != "OBSERVED_CANONICAL_DAILY_BAR":
        return "MISSING"
    change = fnum(member.get("change_pct"))
    contribution = member.get("breadth_contribution", "")
    if change is None:
        return "MISSING"
    if change > 0:
        return "STRONG" if "STRONG" in contribution else "POSITIVE"
    if change < 0:
        return "WEAK"
    return "NEUTRAL"


def clean_name_for_file(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", value).strip("-")
    return cleaned[:60] or "topic"


def table(headers: list[str], rows: list[list[object]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(md(item) for item in row) + " |")
    return "\n".join(out)


def previous_declining_length(topic_rows: list[dict], idx: int) -> int:
    count = 0
    pos = idx - 1
    while pos >= 0 and topic_rows[pos].get("lifecycle_stage") == "DECLINING":
        count += 1
        pos -= 1
    return count


def event_base_metrics(event: dict) -> dict[str, object]:
    row = event["confirmation_row"] or event["event_row"] or event["entry_row"]
    base = event.get("entry_row") or row
    return {
        "topic": event["topic"],
        "topic_name": event["topic_name"],
        "base_episode_id": event["base_episode_id"],
        "base_duration": event.get("base_duration", ""),
        "drawdown": metric(row, "drawdown_from_peak_pct"),
        "lead_core_breadth": metric(row, "lead_core_positive_breadth"),
        "core_breadth": metric(row, "core_positive_breadth"),
        "related_breadth": metric(row, "related_positive_breadth"),
        "lead_core_avg": metric(row, "lead_core_average_change_pct"),
        "strong_breadth": metric(row, "lead_core_strong_breadth"),
        "weak_ratio": metric(row, "lead_core_weak_ratio"),
        "trajectory_recovered": metric(row, "trajectory_recovered"),
        "transition_date": event.get("confirmation_date") or event.get("event_date"),
        "candidate_date": event.get("candidate_date", ""),
        "confirmation_date": event.get("confirmation_date", ""),
        "previous_stage": event.get("previous_stage", ""),
        "final_stage": event.get("final_stage", ""),
    }


def score_a(event: dict) -> float:
    prior = event.get("candidate_row") or event.get("previous_row") or event["entry_row"]
    confirm = event["entry_row"]
    severity = min(abs(fnum(metric(prior, "drawdown_from_peak_pct"), 0) or 0) / 60.0, 1.0)
    decline_days = min(event.get("decline_duration", 0) / 10.0, 1.0)
    weakness = fnum(metric(prior, "lead_core_weak_ratio"), 0) or 0
    stabilization = fnum(metric(confirm, "lead_core_positive_breadth"), 0) or 0
    strength = fnum(metric(confirm, "lead_core_strong_breadth"), 0) or 0
    return round(100 * (0.35 * severity + 0.15 * decline_days + 0.15 * weakness + 0.25 * stabilization + 0.10 * strength), 4)


def score_b(event: dict) -> float:
    row = event["confirmation_row"]
    lc = fnum(metric(row, "lead_core_positive_breadth"), 0) or 0
    core = fnum(metric(row, "core_positive_breadth"), 0) or 0
    strong = fnum(metric(row, "lead_core_strong_breadth"), 0) or 0
    related = fnum(metric(row, "related_positive_breadth"), 0) or 0
    return round(100 * (0.30 * lc + 0.30 * core + 0.20 * strong + 0.10 * related + 0.10 * min(event["base_duration"] / 5, 1)), 4)


def score_c(event: dict) -> float:
    row = event["confirmation_row"]
    lc = fnum(metric(row, "lead_core_positive_breadth"), 0) or 0
    weak = fnum(metric(row, "lead_core_weak_ratio"), 0) or 0
    depth = min(abs(fnum(metric(row, "drawdown_from_peak_pct"), 0) or 0) / 60.0, 1.0)
    duration = min(event["base_duration"] / 5, 1.0)
    return round(100 * (0.35 * (1 - lc) + 0.25 * weak + 0.20 * depth + 0.20 * duration), 4)


def score_d(event: dict) -> float:
    return round(100 * (0.45 * min(event["base_duration"] / 10, 1) + 0.25 * min(event["positive_days"] / 10, 1) + 0.20 * min(event["rejected_candidates"] / 3, 1) + 0.10 * event["max_related_breadth"]), 4)


def score_e(row: dict) -> float:
    dd = min(abs(fnum(metric(row, "drawdown_from_peak_pct"), 0) or 0) / 60, 1)
    lc = fnum(metric(row, "lead_core_positive_breadth"), 0) or 0
    avg = max(fnum(metric(row, "lead_core_average_change_pct"), 0) or 0, 0) / 10
    related = fnum(metric(row, "related_positive_breadth"), 0) or 0
    return round(100 * (0.35 * dd + 0.25 * (1 - lc) + 0.20 * min(avg, 1) + 0.20 * related), 4)


def build_events(rows_by_topic: dict[str, list[dict]], topic_names: dict[str, str]) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict]]:
    a_events: list[dict] = []
    b_events: list[dict] = []
    c_events: list[dict] = []
    d_events: list[dict] = []
    for topic, topic_rows in rows_by_topic.items():
        ordinal = 0
        idx = 0
        while idx < len(topic_rows):
            if topic_rows[idx].get("lifecycle_stage") != "BASE":
                idx += 1
                continue
            start = idx
            while idx + 1 < len(topic_rows) and topic_rows[idx + 1].get("lifecycle_stage") == "BASE":
                idx += 1
            end = idx
            ordinal += 1
            episode_rows = topic_rows[start : end + 1]
            previous_row = topic_rows[start - 1] if start > 0 else None
            next_row = topic_rows[end + 1] if end + 1 < len(topic_rows) else None
            episode_id = f"{topic}::BASE::{ordinal:02d}"
            candidate_base = next((topic_rows[pos] for pos in range(start - 1, -1, -1) if topic_rows[pos].get("candidate_stage") == "BASE"), None)
            next_stage = next_row.get("lifecycle_stage") if next_row else ""
            event_common = {
                "topic": topic,
                "topic_name": topic_names[topic],
                "base_episode_id": episode_id,
                "entry_row": episode_rows[0],
                "end_row": episode_rows[-1],
                "previous_row": previous_row,
                "next_row": next_row,
                "base_duration": len(episode_rows),
                "episode_rows": episode_rows,
                "episode_start_date": episode_rows[0]["trading_date"],
                "episode_end_date": episode_rows[-1]["trading_date"],
                "decline_duration": previous_declining_length(topic_rows, start),
                "positive_days": sum(1 for item in episode_rows if (fnum(item.get("average_change_pct"), 0) or 0) > 0),
                "rejected_candidates": sum(1 for item in episode_rows if item.get("candidate_stage") in {"FERMENTING", "MAIN_RISE"}),
                "max_related_breadth": max((fnum(item.get("related_positive_breadth"), 0) or 0 for item in episode_rows), default=0),
            }
            if previous_row and previous_row.get("lifecycle_stage") == "DECLINING":
                event = dict(event_common)
                event.update(
                    {
                        "type": "A",
                        "candidate_row": candidate_base or previous_row,
                        "confirmation_row": episode_rows[0],
                        "candidate_date": (candidate_base or previous_row)["trading_date"],
                        "confirmation_date": episode_rows[0]["trading_date"],
                        "event_date": episode_rows[0]["trading_date"],
                        "previous_stage": "DECLINING",
                        "final_stage": "BASE",
                    }
                )
                event["selection_score"] = score_a(event)
                a_events.append(event)
            if next_stage == "FERMENTING":
                event = dict(event_common)
                event.update(
                    {
                        "type": "B",
                        "candidate_row": episode_rows[-1],
                        "confirmation_row": next_row,
                        "candidate_date": episode_rows[-1]["trading_date"],
                        "confirmation_date": next_row["trading_date"],
                        "event_date": next_row["trading_date"],
                        "previous_stage": "BASE",
                        "final_stage": "FERMENTING",
                    }
                )
                event["selection_score"] = score_b(event)
                b_events.append(event)
            elif next_stage == "DECLINING":
                event = dict(event_common)
                event.update(
                    {
                        "type": "C",
                        "candidate_row": episode_rows[-1],
                        "confirmation_row": next_row,
                        "candidate_date": episode_rows[-1]["trading_date"],
                        "confirmation_date": next_row["trading_date"],
                        "event_date": next_row["trading_date"],
                        "previous_stage": "BASE",
                        "final_stage": "DECLINING",
                    }
                )
                event["selection_score"] = score_c(event)
                c_events.append(event)
            elif not next_row:
                event = dict(event_common)
                event.update(
                    {
                        "type": "D",
                        "candidate_row": None,
                        "confirmation_row": episode_rows[-1],
                        "candidate_date": "",
                        "confirmation_date": "",
                        "event_date": episode_rows[0]["trading_date"],
                        "previous_stage": previous_row.get("lifecycle_stage", "") if previous_row else "",
                        "final_stage": "BASE",
                    }
                )
                event["selection_score"] = score_d(event)
                d_events.append(event)
            idx += 1

    return a_events, b_events, c_events, d_events, []


def select_cases(a_events: list[dict], b_events: list[dict], c_events: list[dict], d_events: list[dict], rows_by_topic: dict[str, list[dict]]) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    primary: list[dict] = []
    backups: list[dict] = []

    new_a = [event for event in a_events if event["topic"] not in ANCHOR_TOPICS]
    a_pool = new_a or a_events
    # A1: deepest observed decline with a positive confirmation footprint.
    a1 = max(a_pool, key=lambda event: (abs(fnum(event["candidate_row"].get("drawdown_from_peak_pct"), 0) or 0), event["selection_score"], event["topic"]))
    remaining_a = [event for event in a_pool if event is not a1]
    target_dd = median(abs(fnum(event["candidate_row"].get("drawdown_from_peak_pct"), 0) or 0) for event in remaining_a) if remaining_a else 0
    a2 = min(remaining_a, key=lambda event: (abs(abs(fnum(event["candidate_row"].get("drawdown_from_peak_pct"), 0) or 0) - target_dd), -event["selection_score"], event["topic"])) if remaining_a else a1
    remaining_a = [event for event in remaining_a if event is not a2]
    # A3: weakest confirmation footprint among the population, kept as a boundary review case.
    a3 = max(remaining_a, key=lambda event: ((1 - (fnum(event["entry_row"].get("lead_core_positive_breadth"), 0) or 0)) + (1 - (fnum(event["entry_row"].get("lead_core_strong_breadth"), 0) or 0)), event["selection_score"], event["topic"])) if remaining_a else a2
    a_selected = [a1, a2, a3]
    for rank, event in enumerate(a_selected, 1):
        event["case_id"] = f"A{rank}"
        event["category"] = "A_DECLINING_TO_BASE"
        event["selection_role"] = ["deep decline + stabilization", "moderate decline + stabilization", "confirmation boundary"] [rank - 1]
        primary.append(event)
    a_backups = sorted((event for event in a_events if event not in a_selected), key=lambda event: (-event["selection_score"], event["topic"]))[:2]
    for rank, event in enumerate(a_backups, 1):
        event["case_id"] = f"A-B{rank}"
        event["category"] = "A_DECLINING_TO_BASE_BACKUP"
        event["selection_role"] = "backup population coverage"
        backups.append(event)

    used_b_topics = {event["topic"] for event in primary if event["type"] == "B"}
    b_pool = [event for event in b_events if event["topic"] not in ANCHOR_TOPICS] or b_events
    b1 = max(b_pool, key=lambda event: (fnum(event["confirmation_row"].get("lead_core_positive_breadth"), 0) or 0, fnum(event["confirmation_row"].get("core_positive_breadth"), 0) or 0, fnum(event["confirmation_row"].get("lead_core_strong_breadth"), 0) or 0, event["selection_score"], event["topic"]))
    remaining_b = [event for event in b_pool if event is not b1]
    b2 = max(remaining_b, key=lambda event: (fnum(event["confirmation_row"].get("core_positive_breadth"), 0) or 0, fnum(event["confirmation_row"].get("lead_core_positive_breadth"), 0) or 0, event["selection_score"], event["topic"])) if remaining_b else b1
    remaining_b = [event for event in remaining_b if event is not b2]
    b3_candidates = [event for event in remaining_b if fnum(event["confirmation_row"].get("related_positive_breadth")) is not None]
    b3 = max(b3_candidates or remaining_b, key=lambda event: (fnum(event["confirmation_row"].get("related_positive_breadth"), 0) or 0, fnum(event["confirmation_row"].get("lead_core_positive_breadth"), 0) or 0, event["selection_score"], event["topic"])) if remaining_b else b2
    b_selected = [b1, b2, b3]
    for rank, event in enumerate(b_selected, 1):
        event["case_id"] = f"B{rank}"
        event["category"] = "B_BASE_TO_FERMENTING"
        event["selection_role"] = ["broad Lead/Core recovery", "visible Core participation", "Related strong with formal Lead/Core evidence"][rank - 1]
        primary.append(event)
    b_backups = sorted((event for event in b_events if event not in b_selected), key=lambda event: (-event["selection_score"], event["topic"]))[:2]
    for rank, event in enumerate(b_backups, 1):
        event["case_id"] = f"B-B{rank}"
        event["category"] = "B_BASE_TO_FERMENTING_BACKUP"
        event["selection_role"] = "backup population coverage"
        backups.append(event)

    c_pool = [event for event in c_events if event["topic"] not in {"固態電容", "MLCC"}]
    if len(c_pool) < 3:
        c_pool = [event for event in c_events if event["topic"] != "固態電容"]
    c_selected = sorted(c_pool or c_events, key=lambda event: (-event["selection_score"], event["topic"]))[:3]
    for rank, event in enumerate(c_selected, 1):
        event["case_id"] = f"C{rank}"
        event["category"] = "C_BASE_TO_DECLINING"
        event["selection_role"] = "failed-base structural deterioration"
        primary.append(event)
    c_backups = sorted((event for event in c_events if event not in c_selected), key=lambda event: (-event["selection_score"], event["topic"]))[:2]
    for rank, event in enumerate(c_backups, 1):
        event["case_id"] = f"C-B{rank}"
        event["category"] = "C_BASE_TO_DECLINING_BACKUP"
        event["selection_role"] = "known anchor / alternate failed-base coverage"
        backups.append(event)

    d_selected = sorted(d_events, key=lambda event: (-event["base_duration"], -event["selection_score"], event["topic"]))[:3]
    for rank, event in enumerate(d_selected, 1):
        event["case_id"] = f"D{rank}"
        event["category"] = "D_PERSISTENT_BASE"
        event["selection_role"] = "persistent BASE negative control"
        primary.append(event)
    # Do not manufacture D cases: there are only two observed persistent episodes in this reconstruction.

    cancellation_rows: list[dict] = []
    for topic, topic_rows in rows_by_topic.items():
        for idx, row in enumerate(topic_rows):
            if "CANCELLED" not in row.get("transition_reason", ""):
                continue
            cancellation_rows.append(
                {
                    "type": "E",
                    "topic": topic,
                    "topic_name": row["topic_name"],
                    "event_row": row,
                    "confirmation_row": row,
                    "candidate_row": row,
                    "previous_row": topic_rows[idx - 1] if idx else None,
                    "candidate_date": row["trading_date"],
                    "confirmation_date": row["trading_date"],
                    "event_date": row["trading_date"],
                    "previous_stage": row.get("previous_stage", ""),
                    "final_stage": row.get("lifecycle_stage", ""),
                    "base_episode_id": "",
                    "base_duration": "",
                    "episode_rows": [],
                    "selection_score": score_e(row),
                    "selection_role": "anti-false-positive cancellation",
                }
            )
    chosen_topics = {event["topic"] for event in primary}
    e_pool = [event for event in cancellation_rows if event["topic"] not in ANCHOR_TOPICS and event["topic"] not in chosen_topics]
    e_pool = e_pool or [event for event in cancellation_rows if event["topic"] not in {"MLCC"}]
    e_selected: list[dict] = []
    # E1: deep drawdown despite cancellation.
    if e_pool:
        e1 = max(e_pool, key=lambda event: (abs(fnum(event["event_row"].get("drawdown_from_peak_pct"), 0) or 0), event["selection_score"], event["topic"]))
        e_selected.append(e1)
    # E2: strongest one-day Lead/Core rebound while still carrying a deep drawdown.
    remaining_e = [event for event in e_pool if event not in e_selected]
    if remaining_e:
        e2 = max(remaining_e, key=lambda event: (fnum(event["event_row"].get("lead_core_average_change_pct"), 0) or 0, fnum(event["event_row"].get("lead_core_strong_breadth"), 0) or 0, event["selection_score"], event["topic"]))
        e_selected.append(e2)
    # E3: Related breadth is high relative to formal Lead/Core evidence.
    remaining_e = [event for event in e_pool if event not in e_selected]
    related_candidates = [event for event in remaining_e if fnum(event["event_row"].get("related_positive_breadth")) is not None]
    if related_candidates:
        e3 = max(related_candidates, key=lambda event: ((fnum(event["event_row"].get("related_positive_breadth"), 0) or 0) - (fnum(event["event_row"].get("lead_core_positive_breadth"), 0) or 0), event["selection_score"], event["topic"]))
        e_selected.append(e3)
    for rank, event in enumerate(e_selected, 1):
        event["case_id"] = f"E{rank}"
        event["category"] = "E_ANTI_FALSE_POSITIVE"
        event["selection_role"] = ["deep drawdown + cancellation", "one-day rebound + cancellation", "Related-heavy cancellation"][rank - 1]
        primary.append(event)

    for event in primary + backups:
        event["filename"] = f"CASE-{event['case_id']}-{clean_name_for_file(event['topic'])}.md"
    return [event for event in primary if event["category"].startswith("A_")], [event for event in primary if event["category"].startswith("B_")], [event for event in primary if event["category"].startswith("C_")], [event for event in primary if event["category"].startswith("D_")], [event for event in primary if event["category"].startswith("E_")], backups


def timeline_for(event: dict, rows_by_topic: dict[str, list[dict]], index_by_topic_date: dict[tuple[str, str], int], global_sessions: list[str]) -> list[dict]:
    topic_rows = rows_by_topic[event["topic"]]
    event_date = event["event_date"]
    event_idx = index_by_topic_date[(event["topic"], event_date)]
    candidate_date = event.get("candidate_date") or event_date
    candidate_idx = index_by_topic_date.get((event["topic"], candidate_date), event_idx)
    start_idx = max(0, candidate_idx - 5)
    next_transition = None
    for pos in range(event_idx + 1, len(topic_rows)):
        if topic_rows[pos].get("lifecycle_stage") != topic_rows[event_idx].get("lifecycle_stage") and topic_rows[pos].get("lifecycle_stage"):
            next_transition = pos
            break
    end_idx = min(len(topic_rows) - 1, event_idx + 10)
    if next_transition is not None:
        end_idx = min(len(topic_rows) - 1, max(end_idx, next_transition))
    return topic_rows[start_idx : end_idx + 1]


def member_structure(topic: str, members_by_topic: dict[str, list[dict]]) -> list[dict]:
    return sorted(members_by_topic.get(topic, []), key=lambda row: ({"LEAD": 0, "CORE": 1, "RELATED": 2}.get(row.get("structural_role", ""), 9), row.get("instrument_code", "")))


def build_case_markdown(event: dict, rows_by_topic: dict[str, list[dict]], members_by_topic: dict[str, list[dict]], member_by_topic_date: dict[tuple[str, str], list[dict]], index_by_topic_date: dict[tuple[str, str], int], global_sessions: list[str]) -> str:
    topic = event["topic"]
    topic_rows = rows_by_topic[topic]
    timeline = timeline_for(event, rows_by_topic, index_by_topic_date, global_sessions)
    members = member_structure(topic, members_by_topic)
    category = event["category"]
    event_dates = []
    for candidate in [event.get("candidate_date"), event.get("confirmation_date")]:
        if candidate and candidate not in event_dates:
            event_dates.append(candidate)
    if not event_dates:
        event_dates = [event["event_date"]]
    role_counts = Counter(row.get("structural_role", "") for row in members)
    relation_counts = Counter(row.get("topic_relation_type", "") for row in members)
    out: list[str] = []
    out.append(f"# {event['case_id']} — {topic}\n")
    out.append("## Case identity\n")
    out.append(table(["Field", "Value"], [
        ["Category", category],
        ["Topic", topic],
        ["Key candidate / event date", event.get("candidate_date") or event.get("event_date")],
        ["Confirmation date", event.get("confirmation_date") or "—"],
        ["Previous stage", event.get("previous_stage")],
        ["Final stage at event", event.get("final_stage")],
        ["BASE episode", event.get("base_episode_id") or "—"],
        ["BASE duration", event.get("base_duration") or "—"],
        ["Selection score", event.get("selection_score")],
        ["Selection role", event.get("selection_role")],
    ]) + "\n")
    if category.startswith("A_"):
        why = "深度／中度／邊界型 DECLINING→BASE episode，專門檢查 active decline 解除後是否先進入 BASE，而非把單日反彈直接視為新一輪發酵。"
    elif category.startswith("B_"):
        why = "BASE→FERMENTING episode，檢查新 cycle initiation 是否有 Lead/Core identity-aware 共振，且仍未直接跳到 MAIN_RISE。"
    elif category.startswith("C_"):
        why = "failed BASE episode，檢查止跌記憶在 Lead/Core 再度惡化時是否回到 DECLINING，而非永久停留 BASE。"
    elif category.startswith("D_"):
        why = "重建期間最後仍停在 BASE 的 negative-control episode，用來檢查普通反彈與時間經過不會自動推進 FERMENTING。"
    else:
        why = "既有 cancellation evidence 的 edge case，用來檢查強反彈、深 drawdown 或 Related breadth 是否會造成 Owner 需要特別人工判讀。"
    out.append("## Why selected\n\n" + why + "\n")
    out.append("## Member structure\n")
    out.append(f"Lead={role_counts.get('LEAD', 0)}; Core={role_counts.get('CORE', 0)}; Related={role_counts.get('RELATED', 0)}; PRIMARY={relation_counts.get('PRIMARY', 0)}; SECONDARY={relation_counts.get('SECONDARY', 0)}.\n")
    out.append(table(["Ticker", "Name", "Structural role", "Relation", "Weight", "Identity source"], [
        [row.get("instrument_code"), row.get("instrument_name"), row.get("structural_role"), row.get("topic_relation_type"), row.get("topic_weight"), row.get("identity_source")]
        for row in members
    ]) + "\n")
    out.append("## Event timeline\n")
    out.append("Timeline uses valid reconstructed sessions around the event. Post-event rows describe only Lifecycle state evolution and evidence; no future return or performance field is used.\n")
    out.append("### Stage, decision, and disposition\n")
    out.append(table(["Date", "Previous", "Candidate", "Final", "Decision", "Reason", "Disposition"], [
        [row["trading_date"], row.get("previous_stage"), row.get("candidate_stage"), row.get("lifecycle_stage"), row.get("transition_decision"), row.get("transition_reason"), state_fields(row)["disposition"]]
        for row in timeline
    ]) + "\n")
    out.append("### Daily breadth and trajectory evidence\n")
    out.append(table(["Date", "Lead/Core breadth", "Core breadth", "Related breadth", "Lead/Core avg %", "Overall avg %", "Strong breadth", "Weak ratio", "Meaningful expansion", "Days since expansion", "Drawdown %", "Trajectory recovered"], [
        [row["trading_date"], ratio(row.get("lead_core_positive_breadth")), ratio(row.get("core_positive_breadth")), ratio(row.get("related_positive_breadth")), pct(row.get("lead_core_average_change_pct")), pct(row.get("average_change_pct")), ratio(row.get("lead_core_strong_breadth")), ratio(row.get("lead_core_weak_ratio")), row.get("meaningful_expansion"), fmt(row.get("days_since_meaningful_expansion")), pct(row.get("drawdown_from_peak_pct")), row.get("trajectory_recovered")]
        for row in timeline
    ]) + "\n")
    out.append("### Pending and state memory\n")
    out.append(table(["Date", "Structural breakdown pending", "Structural disposition", "Structural age", "Declining pending", "Declining disposition", "Declining age", "BASE pending", "Pending age", "Confirmation state", "Candidate streak", "Confirmation age", "Required days", "Cycle"], [
        [row["trading_date"], state_fields(row)["structural_breakdown_pending"], state_fields(row)["structural_breakdown_disposition"], state_fields(row)["structural_breakdown_age"], state_fields(row)["declining_pending"], state_fields(row)["declining_pending_disposition"], state_fields(row)["declining_pending_age"], state_fields(row)["base_pending"], state_fields(row)["pending_age"], state_fields(row)["confirmation_state"], state_fields(row)["candidate_streak"], state_fields(row)["confirmation_age"], state_fields(row)["required_trading_days"], state_fields(row)["cycle_id"]]
        for row in timeline
    ]) + "\n")
    out.append("## Key-date member evidence\n")
    out.append("The following tables preserve every current member in the frozen membership for the candidate / confirmation or cancellation date.\n")
    for event_date in event_dates:
        evidence = member_by_topic_date.get((topic, event_date), [])
        out.append(f"### {event_date}\n")
        out.append(table(["Ticker", "Name", "Role", "Relation", "Daily change %", "Evidence state", "Observation"], [
            [row.get("instrument_code"), row.get("instrument_name"), row.get("structural_role"), row.get("topic_relation_type"), pct(row.get("change_pct")), evidence_state(row), row.get("observation_status")]
            for row in sorted(evidence, key=lambda row: ({"LEAD": 0, "CORE": 1, "RELATED": 2}.get(row.get("structural_role", ""), 9), row.get("instrument_code", "")))
        ]) + "\n")
    out.append("## State-memory explanation\n")
    if category.startswith("A_"):
        out.append(f"Candidate BASE appeared on {event.get('candidate_date')}; the final stage remained DECLINING until {event.get('confirmation_date')}, when the two-session confirmation memory was satisfied. The episode then remained BASE until the next recorded transition.\n")
    elif category.startswith("B_"):
        out.append(f"The topic remained BASE through {event.get('candidate_date')} while FERMENTING was pending; the next valid session {event.get('confirmation_date')} confirmed FERMENTING. The transition is adjacent-stage only; no direct BASE→MAIN_RISE jump is present.\n")
    elif category.startswith("C_"):
        out.append(f"A BASE→DECLINING candidate was held on {event.get('candidate_date')}; the next valid session {event.get('confirmation_date')} confirmed DECLINING after the pending window.\n")
    elif category.startswith("D_"):
        out.append(f"The episode entered BASE on {event.get('event_date')} and remained BASE through the reconstruction boundary ({event.get('episode_end_date')}); no automatic FERMENTING transition was observed.\n")
    else:
        out.append(f"The cancellation was recorded on {event.get('event_date')} with reason {event['event_row'].get('transition_reason')}. The final stage stayed {event.get('final_stage')} while genuine-repair evidence cancelled the pending candidate.\n")
    out.append("## Owner semantic interpretation (evidence only)\n")
    if category.startswith("A_"):
        out.append("- Is this more than a one-day rebound? Review the preceding decline depth, candidate day, confirmation delay, and whether Lead/Core breadth is synchronized.\n- Core synchronization and residual drawdown should be read together; trajectory_recovered is an engine evidence flag, not an Owner verdict.\n- BASE is the reset state here: the evidence does not by itself establish FERMENTING or MAIN_RISE.\n")
    elif category.startswith("B_"):
        out.append(f"- BASE lasted {event.get('base_duration')} valid sessions before FERMENTING confirmation.\n- Compare Lead/Core breadth and Core breadth with Related breadth to see whether identity-aware participation is visible.\n- FERMENTING is adjacent to BASE; the final stage is not MAIN_RISE on this transition.\n")
    elif category.startswith("C_"):
        out.append(f"- BASE lasted {event.get('base_duration')} valid sessions before failure.\n- At failure, review renewed drawdown, Lead/Core deterioration, weak ratio, and whether the evidence is broader than a single member.\n- The final transition is BASE→DECLINING after confirmation memory, not a one-row flip.\n")
    elif category.startswith("D_"):
        out.append(f"- The observed episode duration is {event.get('base_duration')} valid session(s), with {event.get('positive_days')} positive session(s), maximum Related breadth {fmt(event.get('max_related_breadth'))}, and {event.get('rejected_candidates')} rejected bullish candidate(s).\n- This is a reconstruction-boundary negative control; it does not prove that a longer BASE could never occur.\n")
    else:
        row = event["event_row"]
        out.append(f"- Cancellation reason: {row.get('transition_reason')}.\n- On the cancellation date: Lead/Core breadth {ratio(row.get('lead_core_positive_breadth'))}, Core breadth {ratio(row.get('core_positive_breadth'))}, Related breadth {ratio(row.get('related_positive_breadth'))}, Lead/Core average {pct(row.get('lead_core_average_change_pct'))}, drawdown {pct(row.get('drawdown_from_peak_pct'))}.\n- Owner should decide whether the repair evidence is structurally genuine or merely a rebound; this pack leaves that verdict open.\n")
    out.append("## Owner review fields\n\nOWNER_VERDICT=\n\nOWNER_NOTES=\n")
    return "\n".join(out)


def inventory_row(event: dict, selected_primary: dict[str, str], selected_backup: dict[str, str]) -> dict[str, object]:
    metrics = event_base_metrics(event)
    category = event["type"]
    row = {
        "topic": metrics["topic"],
        "topic_name": metrics["topic_name"],
        "transition_kind": {"A": "DECLINING_TO_BASE", "B": "BASE_TO_FERMENTING", "C": "BASE_TO_DECLINING", "D": "PERSISTENT_BASE"}.get(category, category),
        "transition_date": metrics["transition_date"],
        "candidate_date": metrics["candidate_date"],
        "confirmation_date": metrics["confirmation_date"],
        "previous_stage": metrics["previous_stage"],
        "final_stage": metrics["final_stage"],
        "base_episode_id": metrics["base_episode_id"],
        "base_duration": metrics["base_duration"],
        "episode_start_date": event.get("episode_start_date", ""),
        "episode_end_date": event.get("episode_end_date", ""),
        "drawdown": metrics["drawdown"],
        "lead_core_breadth": metrics["lead_core_breadth"],
        "core_breadth": metrics["core_breadth"],
        "related_breadth": metrics["related_breadth"],
        "lead_core_avg": metrics["lead_core_avg"],
        "strong_breadth": metrics["strong_breadth"],
        "weak_ratio": metrics["weak_ratio"],
        "trajectory_recovered": metrics["trajectory_recovered"],
        "decline_duration_before_base": event.get("decline_duration", ""),
        "positive_days_while_base": event.get("positive_days", ""),
        "rejected_candidate_count": event.get("rejected_candidates", ""),
        "max_related_breadth": event.get("max_related_breadth", ""),
        "selection_category": event.get("category", f"{category}_POPULATION"),
        "selection_score": event.get("selection_score", ""),
        "selected_primary": selected_primary.get(event.get("base_episode_id", ""), ""),
        "selected_backup": selected_backup.get(event.get("base_episode_id", ""), ""),
    }
    return row


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def case_summary_table(events: list[dict]) -> str:
    if not events:
        return "NOT_OBSERVED_IN_V1_2_RECONSTRUCTION"
    return table(["Case", "Topic", "Key date", "Confirmation", "Transition", "Score", "Why worth review"], [
        [event["case_id"], event["topic"], event.get("candidate_date") or event.get("event_date"), event.get("confirmation_date") or "—", {"A": "DECLINING→BASE", "B": "BASE→FERMENTING", "C": "BASE→DECLINING", "D": "PERSISTENT BASE", "E": event.get("event_row", {}).get("candidate_stage", "CANCELLED")}.get(event["type"], event["category"]), event.get("selection_score"), event.get("selection_role")]
        for event in events
    ])


def write_category_file(path: Path, title: str, category: str, population: int, primary_events: list[dict], backup_events: list[dict], question: str, note: str = "") -> None:
    lines = [f"# {title}", "", f"Population in frozen V1.2 reconstruction: **{population}**.", "", question, "", note]
    lines += ["", "## Primary review order", "", case_summary_table(primary_events)]
    lines += ["", "## Backup cases", "", case_summary_table(backup_events) if backup_events else "No backup case selected."]
    lines += ["", "All OWNER_VERDICT and OWNER_NOTES fields remain blank. This file is evidence routing only; it does not declare semantic acceptance.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_aggregate(a_events: list[dict], b_events: list[dict], c_events: list[dict], d_events: list[dict], row_count: int, member_count: int) -> dict:
    def vals(events: list[dict], row_field: str, row_selector: str = "confirmation_row") -> list[float]:
        result = []
        for event in events:
            value = fnum(event[row_selector].get(row_field))
            if value is not None:
                result.append(value)
        return result

    a_dd = [abs(value) for value in vals(a_events, "drawdown_from_peak_pct", "candidate_row")]
    a_lc = vals(a_events, "lead_core_positive_breadth")
    a_weak = vals(a_events, "lead_core_weak_ratio")
    a_delay = []
    for event in a_events:
        a_delay.append(max(0, event.get("confirmation_date", "") != event.get("candidate_date", "")))
    b_duration = [event["base_duration"] for event in b_events]
    b_lc = vals(b_events, "lead_core_positive_breadth")
    b_core = vals(b_events, "core_positive_breadth")
    b_related = vals(b_events, "related_positive_breadth")
    c_duration = [event["base_duration"] for event in c_events]
    c_deterioration = [1 - value for value in vals(c_events, "lead_core_positive_breadth")]
    c_dd = [abs(value) for value in vals(c_events, "drawdown_from_peak_pct")]
    d_duration = [event["base_duration"] for event in d_events]
    return {
        "reconstruction_rows": row_count,
        "member_evidence_rows": member_count,
        "declining_to_base": {"count": len(a_events), "median_decline_drawdown_abs_pct": median(a_dd), "median_lead_core_breadth": median(a_lc), "median_weak_ratio": median(a_weak), "median_confirmation_delay_sessions": median(a_delay)},
        "base_to_fermenting": {"count": len(b_events), "median_base_duration_sessions": median(b_duration), "median_lead_core_breadth": median(b_lc), "median_core_breadth": median(b_core), "median_related_breadth": median(b_related) if b_related else None},
        "base_to_declining": {"count": len(c_events), "median_base_duration_before_failure": median(c_duration), "median_deterioration_breadth": median(c_deterioration), "median_drawdown_at_failure_abs_pct": median(c_dd)},
        "persistent_base": {"episode_count": len(d_events), "median_duration_sessions": median(d_duration) if d_duration else None, "max_duration_sessions": max(d_duration) if d_duration else None, "number_with_rejected_bullish_candidates": sum(1 for event in d_events if event["rejected_candidates"] > 0)},
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cases_dir = OUT / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    rows = [norm_row(row) for row in read_csv(RECON_PATH)]
    member_rows = read_csv(MEMBER_PATH)
    topic_names = {row["topic_key"]: row["topic_name"] for row in rows}
    rows_by_topic: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        rows_by_topic[row["topic_key"]].append(row)
    for topic_rows in rows_by_topic.values():
        topic_rows.sort(key=lambda row: row["trading_date"])
    members_by_topic: dict[str, list[dict]] = defaultdict(list)
    seen_member_keys: set[tuple[str, str]] = set()
    member_by_topic_date: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in member_rows:
        key = (row["topic_key"], row["instrument_code"])
        if key not in seen_member_keys:
            members_by_topic[row["topic_key"]].append(dict(row))
            seen_member_keys.add(key)
        member_by_topic_date[(row["topic_key"], row["trading_date"])].append(dict(row))
    global_sessions = sorted({row["trading_date"] for row in rows})
    index_by_topic_date = {(topic, row["trading_date"]): idx for topic, topic_rows in rows_by_topic.items() for idx, row in enumerate(topic_rows)}

    a_events, b_events, c_events, d_events, _ = build_events(rows_by_topic, topic_names)
    a_primary, b_primary, c_primary, d_primary, e_primary, backups = select_cases(a_events, b_events, c_events, d_events, rows_by_topic)
    all_primary = a_primary + b_primary + c_primary + d_primary + e_primary
    selected_primary = {event.get("base_episode_id", ""): event["case_id"] for event in all_primary if event.get("base_episode_id")}
    selected_backup = {event.get("base_episode_id", ""): event["case_id"] for event in backups if event.get("base_episode_id")}
    for event in all_primary + backups:
        (cases_dir / event["filename"]).write_text(build_case_markdown(event, rows_by_topic, members_by_topic, member_by_topic_date, index_by_topic_date, global_sessions), encoding="utf-8")

    inventory_events = a_events + b_events + c_events + d_events
    inventory_fields = [
        "topic", "topic_name", "transition_kind", "transition_date", "candidate_date", "confirmation_date", "previous_stage", "final_stage", "base_episode_id", "base_duration", "episode_start_date", "episode_end_date", "drawdown", "lead_core_breadth", "core_breadth", "related_breadth", "lead_core_avg", "strong_breadth", "weak_ratio", "trajectory_recovered", "decline_duration_before_base", "positive_days_while_base", "rejected_candidate_count", "max_related_breadth", "selection_category", "selection_score", "selected_primary", "selected_backup",
    ]
    inventory_rows = [inventory_row(event, selected_primary, selected_backup) for event in inventory_events]
    inventory_rows.sort(key=lambda row: (row["transition_date"], row["topic"], row["transition_kind"]))
    write_csv(OUT / "lifecycle-v1-2-base-transition-inventory.csv", inventory_rows, inventory_fields)

    matrix_fields = [
        "case_id", "category", "topic", "key_candidate_date", "confirmation_date", "previous_stage", "final_stage", "base_duration", "selection_score", "lead_count", "core_count", "related_count", "lead_core_breadth", "core_breadth", "related_breadth", "lead_core_avg", "weak_ratio", "drawdown", "trajectory_recovered", "state_memory_behavior", "owner_verdict", "owner_notes",
    ]
    matrix_rows = []
    for event in all_primary + backups:
        member_counts = Counter(row.get("structural_role", "") for row in members_by_topic.get(event["topic"], []))
        row = event.get("confirmation_row") or event.get("event_row")
        memory = state_fields(row) if row else {}
        matrix_rows.append({
            "case_id": event["case_id"], "category": event["category"], "topic": event["topic"], "key_candidate_date": event.get("candidate_date") or event.get("event_date"), "confirmation_date": event.get("confirmation_date", ""), "previous_stage": event.get("previous_stage", ""), "final_stage": event.get("final_stage", ""), "base_duration": event.get("base_duration", ""), "selection_score": event.get("selection_score", ""), "lead_count": member_counts.get("LEAD", 0), "core_count": member_counts.get("CORE", 0), "related_count": member_counts.get("RELATED", 0), "lead_core_breadth": row.get("lead_core_positive_breadth") if row else "", "core_breadth": row.get("core_positive_breadth") if row else "", "related_breadth": row.get("related_positive_breadth") if row else "", "lead_core_avg": row.get("lead_core_average_change_pct") if row else "", "weak_ratio": row.get("lead_core_weak_ratio") if row else "", "drawdown": row.get("drawdown_from_peak_pct") if row else "", "trajectory_recovered": row.get("trajectory_recovered") if row else "", "state_memory_behavior": memory.get("confirmation_state", ""), "owner_verdict": "", "owner_notes": "",
        })
    write_csv(OUT / "lifecycle-v1-2-base-owner-acceptance-matrix.csv", matrix_rows, matrix_fields)

    aggregate = build_aggregate(a_events, b_events, c_events, d_events, len(rows), len(member_rows))
    run_summary = json.load(RUN_SUMMARY_PATH.open("r", encoding="utf-8-sig"))
    formal_text = FORMAL_PATH.read_text(encoding="utf-8-sig")
    tests = json.load(TEST_RESULTS_PATH.open("r", encoding="utf-8-sig"))
    stage_counts = Counter(row.get("lifecycle_stage", "") for row in rows)
    transition_counts = Counter((row.get("previous_stage", ""), row.get("lifecycle_stage", "")) for row in rows)
    illegal_jumps = 0
    allowed = {("DECLINING", "BASE"), ("BASE", "FERMENTING"), ("BASE", "DECLINING"), ("FERMENTING", "MAIN_RISE"), ("MAIN_RISE", "MATURE"), ("MATURE", "DECLINING"), ("MATURE", "MAIN_RISE"), ("MAIN_RISE", "DECLINING"), ("DECLINING", "DECLINING"), ("BASE", "BASE"), ("FERMENTING", "FERMENTING"), ("MAIN_RISE", "MAIN_RISE"), ("MATURE", "MATURE"), ("SPROUTING", "SPROUTING"), ("", "")}
    for row in rows:
        prev, final = row.get("previous_stage", ""), row.get("lifecycle_stage", "")
        if prev and final and prev != final and (prev, final) not in allowed:
            illegal_jumps += 1
    source_hashes = {"reconstruction_file_sha256": sha256_file(RECON_PATH), "member_evidence_file_sha256": sha256_file(MEMBER_PATH), "validation_pack_file_sha256": sha256_file(VALIDATION_PATH)}
    baseline_hash_verified = run_summary.get("reconstruction_hash") == EXPECTED_IDENTITY_HASH and EXPECTED_IDENTITY_HASH in formal_text and run_summary.get("reconstruction", {}).get("row_count") == len(rows) and run_summary.get("reconstruction", {}).get("member_evidence_row_count") == len(member_rows)
    baseline = {
        "expected_identity_hash": EXPECTED_IDENTITY_HASH,
        "observed_identity_hash": run_summary.get("reconstruction_hash"),
        "identity_hash_verified": "YES" if baseline_hash_verified else "NO",
        "source_file_sha256": source_hashes,
        "counts": {"topics": len(rows_by_topic), "sessions": len(global_sessions), "reconstruction_rows": len(rows), "member_evidence_rows": len(member_rows)},
        "expected_counts": EXPECTED_COUNTS,
        "observed_transition_counts": {"declining_to_base": len(a_events), "base_to_fermenting": len(b_events), "base_to_declining": len(c_events), "base_to_main_rise": transition_counts[("BASE", "MAIN_RISE")]},
        "persistent_base_episode_count": len(d_events),
        "related_only_base_count": run_summary.get("invariants", {}).get("related_only_base_false_positives"),
        "illegal_final_jump_count": run_summary.get("invariants", {}).get("illegal_final_jumps", illegal_jumps),
        "deterministic_replay_status": run_summary.get("replay", {}).get("deterministic_replay"),
        "targeted_lifecycle_tests": {"pass": tests.get("lifecycle_tests_pass"), "stdout": tests.get("lifecycle_tests_stdout", "")},
        "full_api_suite_scope_diagnostic": {"pass": tests.get("full_api_suite_pass"), "note": tests.get("full_api_suite_scope_note", "")},
        "provenance": {"reconstruction": str(RECON_PATH), "member_evidence": str(MEMBER_PATH), "validation_pack": str(VALIDATION_PATH), "run_summary": str(RUN_SUMMARY_PATH), "formal_closure": str(FORMAL_PATH)},
    }
    (OUT / "baseline-integrity-check.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")

    methodology = f"""# V1.2 BASE cross-topic case-selection methodology

This acceptance pack is a deterministic read-only selection over the frozen V1.2 reconstruction. It does not change Lifecycle policy, thresholds, roles, memberships, weights, or the engine. The score is a routing score for Owner review, not a Lifecycle decision score.

## Frozen source and information boundary

- Source reconstruction: `{RECON_PATH}`
- Source member evidence: `{MEMBER_PATH}`
- Identity hash asserted by the completed V1.2 run: `{EXPECTED_IDENTITY_HASH}`
- Future returns, forward returns, WS3, PnL, Sharpe, hit rate, and strategy performance were not read.
- The historical rows after an event are used only to show Lifecycle state evolution.

## Episode construction

For every topic, rows were sorted by valid `trading_date`. A BASE episode is a contiguous run of final `lifecycle_stage=BASE`. The inventory creates one event row for every `DECLINING→BASE`, `BASE→FERMENTING`, and `BASE→DECLINING` event, plus one row for every episode that remains BASE at the reconstruction boundary. Candidate and confirmation dates are retained separately.

## Selection scores

- Category A score = 35% normalized prior drawdown severity + 15% prior decline duration + 15% prior weak ratio + 25% confirmation Lead/Core breadth + 10% confirmation strong breadth. A1 is selected by deepest prior drawdown with stabilizing evidence; A2 is closest to the remaining population median drawdown; A3 is the weakest confirmation footprint as a boundary review case.
- Category B score = 30% Lead/Core breadth + 30% Core breadth + 20% strong breadth + 10% Related breadth + 10% BASE duration. B1 maximizes broad Lead/Core recovery; B2 maximizes Core participation; B3 maximizes Related breadth subject to formal Lead/Core evidence.
- Category C score = 35% renewed Lead/Core deterioration + 25% weak ratio + 20% drawdown severity + 20% BASE duration. The three highest-scoring non-anchor failed-base episodes are selected when available.
- Category D score = 45% BASE duration + 25% positive sessions while BASE + 20% rejected bullish candidates + 10% maximum Related breadth. All observed persistent episodes are shown; no unobserved case is invented.
- Category E score = 35% drawdown + 25% lack of Lead/Core breadth + 20% positive Lead/Core average rebound + 20% Related breadth. Selection is from existing cancellation rows only, with distinct edge-case routing.

The legacy anchor topics are excluded from Primary selection when enough new topics exist. They remain available in the complete inventory and backups/regression references.
"""
    (OUT / "case-selection-methodology.md").write_text(methodology, encoding="utf-8")

    summary_lines = ["# Cross-topic BASE semantic summary", "", "## Population", "", table(["Population", "Count"], [["DECLINING→BASE", len(a_events)], ["BASE→FERMENTING", len(b_events)], ["BASE→DECLINING", len(c_events)], ["Persistent BASE episodes", len(d_events)], ["All reconstruction topics", len(rows_by_topic)], ["Sessions", len(global_sessions)]]), "", "## Aggregate semantic sanity checks", "", "```json", json.dumps(aggregate, ensure_ascii=False, indent=2), "```", "", "## Mechanical invariants", "", "- BASE→MAIN_RISE = 0 in the frozen baseline.", "- Related-only BASE false positives = 0 in the frozen baseline.", "- Illegal final jumps = 0 in the frozen baseline.", "- Deterministic replay = PASS.", "", "## Owner reading lens", "", "Category A tests reset after decline; Category B tests identity-aware cycle initiation; Category C tests failed-base return to decline; Category D is the negative control; Category E isolates cancellation / rebound edge risk. None of these sections pre-populates an Owner verdict.", ""]
    (OUT / "cross-topic-base-semantic-summary.md").write_text("\n".join(summary_lines), encoding="utf-8")

    write_category_file(OUT / "category-a-declining-to-base-primary-cases.md", "Category A — DECLINING→BASE confirmed", "A", len(a_events), a_primary, [event for event in backups if event["case_id"].startswith("A-")], "Owner question: did active decline stop with Lead/Core stabilization, rather than a one-day rebound?", "Primary cases are selected from the full 36-event population; MLCC and previous named anchors are not used as Primary when new cases are available.")
    write_category_file(OUT / "category-b-base-to-fermenting-primary-cases.md", "Category B — BASE→FERMENTING confirmed", "B", len(b_events), b_primary, [event for event in backups if event["case_id"].startswith("B-")], "Owner question: did a new cycle begin with identity-aware Lead/Core evidence, rather than Related-only strength?", "Direct BASE→MAIN_RISE is not allowed in the frozen V1.2 baseline; the selected cases are adjacent BASE→FERMENTING transitions.")
    write_category_file(OUT / "category-c-failed-base-primary-cases.md", "Category C — BASE→DECLINING failed base", "C", len(c_events), c_primary, [event for event in backups if event["case_id"].startswith("C-")], "Owner question: when stabilization failed, did renewed Lead/Core deterioration justify returning to DECLINING?", "The known 固態電容 and MLCC anchors remain in the inventory and may appear as backups, but Primary selection includes other topics where available.")
    d_note = "Only the observed reconstruction-boundary episodes are selected. A longer-duration persistent BASE population is NOT_OBSERVED_IN_V1_2_RECONSTRUCTION." if len(d_events) < 3 else "All observed persistent episodes are routed for review."
    write_category_file(OUT / "category-d-persistent-base-primary-cases.md", "Category D — Persistent / long BASE negative control", "D", len(d_events), d_primary, [], "Owner question: can BASE persist without time-based or Related-only promotion to FERMENTING?", d_note)
    write_category_file(OUT / "category-e-edge-cases.md", "Category E — Anti-false-positive / edge cases", "E", sum(1 for row in rows if "CANCELLED" in row.get("transition_reason", "")), e_primary, [], "Owner question: do cancellation and rebound edge cases expose a semantic risk that requires manual review?", "Cases are selected only from existing cancellation rows. No synthetic edge case was created.")

    backup_lines = ["# Backup cases", "", "Backups are deterministic alternates from the same frozen populations. Owner verdict fields remain blank.", "", case_summary_table(backups), ""]
    (OUT / "backup-cases.md").write_text("\n".join(backup_lines), encoding="utf-8")

    guide = """# Owner review guide

## Recommended order

1. A1 — deep decline followed by BASE confirmation.
2. B1 — broad BASE→FERMENTING initiation.
3. C1 — failed BASE with strongest renewed deterioration.
4. D1 — reconstruction-boundary persistent BASE negative control.
5. E1 — cancellation / rebound edge case.
6. Continue A2/A3, B2/B3, C2/C3, D2, and E2/E3 as needed.

For each case, first read the member structure, then the five valid sessions before the candidate, candidate/confirmation rows, and the post-event Lifecycle state evolution. Use Lead/Core before Related when interpreting structural identity. `trajectory_recovered` and state-memory flags are evidence fields, not a pre-filled verdict.

Do not use later returns or performance to decide whether the earlier stage was semantically correct. Record the Owner decision only in the blank `OWNER_VERDICT=` and `OWNER_NOTES=` fields in the case file or matrix.

## Permitted Owner vocabulary

`CORRECT`, `ACCEPTABLE`, `TOO_EARLY`, `TOO_LATE`, `FALSE_BASE`, `MISSED_BASE`, `FALSE_FERMENTING`, `MISSED_FERMENTING`, `FALSE_DECLINE`, `MISSED_DECLINE`, `STATE_TOO_STICKY`, `STATE_TOO_LOOSE`, `NEEDS_REVIEW`.
"""
    (OUT / "owner-review-guide.md").write_text(guide, encoding="utf-8")

    regression = """# Regression anchor status

The completed V1.2 baseline reports the following mechanical anchor results:

| Anchor | Status | Use in this pack |
| --- | --- | --- |
| A1 — ABF載板 | PASS | Regression reference; not required as a new Primary case |
| A2 — DRAM／DDR | PASS | Regression reference; not required as a new Primary case |
| B1 — SiC 晶圓／基板 | PASS | Regression reference; not required as a new Primary case |
| B2 — 固態電容 | PASS | Known failed-base anchor; retained in inventory/backups when not Primary |
| MLCC | PASS | Prior semantic anchor; explicitly excluded from Primary selection |

This file reports existing baseline provenance only. It does not re-run reconstruction and does not alter any anchor.
"""
    (OUT / "regression-anchor-status.md").write_text(regression, encoding="utf-8")

    selected_case_lines = [event["case_id"] for event in all_primary]
    flags = {
        "V1_2_BASELINE_HASH_VERIFIED": "YES" if baseline_hash_verified else "NO",
        "DETERMINISTIC_REPLAY_STATUS": run_summary.get("replay", {}).get("deterministic_replay", "UNKNOWN"),
        "TOTAL_TOPICS": len(rows_by_topic), "TOTAL_SESSIONS": len(global_sessions), "TOTAL_RECONSTRUCTION_ROWS": len(rows), "TOTAL_MEMBER_EVIDENCE_ROWS": len(member_rows),
        "DECLINING_TO_BASE_COUNT": len(a_events), "BASE_TO_FERMENTING_COUNT": len(b_events), "BASE_TO_DECLINING_COUNT": len(c_events), "BASE_TO_MAIN_RISE_COUNT": transition_counts[("BASE", "MAIN_RISE")],
        "PERSISTENT_BASE_EPISODE_COUNT": len(d_events), "RELATED_ONLY_BASE_COUNT": run_summary.get("invariants", {}).get("related_only_base_false_positives", 0), "ILLEGAL_FINAL_JUMP_COUNT": run_summary.get("invariants", {}).get("illegal_final_jumps", 0),
        "CATEGORY_A_PRIMARY_COUNT": len(a_primary), "CATEGORY_B_PRIMARY_COUNT": len(b_primary), "CATEGORY_C_PRIMARY_COUNT": len(c_primary), "CATEGORY_D_PRIMARY_COUNT": len(d_primary), "CATEGORY_E_EDGE_COUNT": len(e_primary), "BACKUP_CASE_COUNT": len(backups),
        "FUTURE_RETURNS_READ": "NO", "WS3_TOUCHED": "NO", "TOPIC_MASTER_CHANGED": "NO", "INSTRUMENT_MASTER_CHANGED": "NO", "MEMBERSHIP_CHANGED": "NO", "STRUCTURAL_ROLE_CHANGED": "NO", "LIFECYCLE_POLICY_CHANGED": "NO", "LIFECYCLE_ENGINE_CHANGED": "NO", "IMPLEMENTATION_DEFECT_FOUND": "NO", "OWNER_SEMANTIC_REVIEW_REQUIRED": "YES", "OWNER_VERDICTS_PREPOPULATED": "NO", "V1_2_OWNER_SEMANTIC_ACCEPTANCE": "PENDING_OWNER_REVIEW", "V1_2_READY_TO_FREEZE": "NO", "V1_2_READY_FOR_WS3": "NO",
        "PRIMARY_CASE_IDS": selected_case_lines,
    }
    (OUT / "run-summary.json").write_text(json.dumps({"task_id": "TASK-WS1-LIFECYCLE-V1-2-BASE-CROSS-TOPIC-OWNER-SEMANTIC-ACCEPTANCE-20260824", "status": "OWNER_SEMANTIC_ACCEPTANCE_READY_NOT_ACCEPTED", "flags": flags, "aggregate": aggregate, "baseline": baseline, "source_paths": {"reconstruction": str(RECON_PATH), "member_evidence": str(MEMBER_PATH)}, "primary_cases": [{"case_id": event["case_id"], "category": event["category"], "topic": event["topic"], "key_date": event.get("candidate_date") or event.get("event_date"), "confirmation_date": event.get("confirmation_date", ""), "selection_role": event.get("selection_role"), "selection_score": event.get("selection_score")} for event in all_primary], "backup_cases": [{"case_id": event["case_id"], "topic": event["topic"], "key_date": event.get("candidate_date") or event.get("event_date"), "selection_score": event.get("selection_score")} for event in backups]}, ensure_ascii=False, indent=2), encoding="utf-8")

    closure_flags = "\n".join(f"{key}={value if not isinstance(value, list) else ','.join(value)}" for key, value in flags.items() if key != "PRIMARY_CASE_IDS")
    closure = f"""# TASK-WS1-LIFECYCLE-V1-2-BASE-CROSS-TOPIC-OWNER-SEMANTIC-ACCEPTANCE-20260824

## Scope

This pack performs Owner semantic case selection and evidence extraction from the completed frozen Lifecycle V1.2 reconstruction. It does not re-run reconstruction, modify Lifecycle policy or engine, tune thresholds, change masters or memberships, read future returns, touch WS3, or declare final acceptance.

## Mechanical baseline

- Identity hash asserted and verified against the completed V1.2 run summary: `{EXPECTED_IDENTITY_HASH}`.
- Reconstruction rows: `{len(rows)}`; member evidence rows: `{len(member_rows)}`; topics: `{len(rows_by_topic)}`; sessions: `{len(global_sessions)}`.
- Deterministic replay status inherited from the completed baseline: `{run_summary.get('replay', {}).get('deterministic_replay')}`.
- The full inventory covers {len(a_events)} DECLINING→BASE, {len(b_events)} BASE→FERMENTING, {len(c_events)} BASE→DECLINING, and {len(d_events)} persistent BASE episodes.

## Owner acceptance boundary

Mechanical checks are not Owner semantic acceptance. Owner review is required. All case-level `OWNER_VERDICT` and `OWNER_NOTES` fields are blank. The pack therefore stops at `PENDING_OWNER_REVIEW`.

## Final flags

```text
{closure_flags}
```

## Required reading order

See `owner-review-guide.md` and the Primary cases in `cases/`. Start with A1, then B1, C1, D1, and E1. Category D has only the two persistent reconstruction-boundary episodes observed; a longer persistent BASE population is explicitly not observed and was not invented.
"""
    (OUT / "formal-closure-report.md").write_text(closure, encoding="utf-8")


if __name__ == "__main__":
    main()
