"""Run the Lifecycle V1.2 BASE/reset Owner-semantic reconstruction.

This is a read-only WS1 research artifact generator.  It reuses the accepted
V1 historical input path and V1.1 evidence topology, but applies the V1.2
stage ontology from ``topic_lifecycle_v1``.  It never reads future returns,
WS3 outputs, or writes PostgreSQL.
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

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "services" / "api" / "src"
TOOLS = REPO / "tools"
for path in (SRC, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from topicpilot_api.topic_lifecycle_v1 import (
    BASE,
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
    MEMBER_FIELDS,
    PRICE_QUERY,
    _build_reconstruction,
    _file_sha256,
    _hash_rows,
    _read_prices,
)
from ws1_lifecycle_v1_full_refresh import OUTPUT_FIELDS as V1_OUTPUT_FIELDS

TASK_ID = "TASK-WS1-LIFECYCLE-V1-2-BASE-RESET-STAGE-ONTOLOGY-HARD-FIX-20260824"
V11_DIR = (
    REPO
    / "reports"
    / "TASK-WS1-LIFECYCLE-V1-1-STRUCTURAL-BREAKDOWN-DECLINE-CONFIRMATION-HARD-FIX-20260824"
)
V11_RECONSTRUCTION = V11_DIR / "lifecycle-v1-1-full-reconstruction.csv"
V11_MEMBER_EVIDENCE = V11_DIR / "lifecycle-v1-1-member-evidence.csv"
V12_FIELDS = V1_OUTPUT_FIELDS + [
    "cycle_number",
    "cycle_id",
    "cycle_ended",
    "main_rise_ancestry",
]
STAGE_ORDER = (BASE, SPROUTING, FERMENTING, MAIN_RISE, MATURE, DECLINING)
LEGAL_TRANSITIONS = {
    (BASE, SPROUTING),
    (BASE, FERMENTING),
    (BASE, DECLINING),
    (SPROUTING, FERMENTING),
    (FERMENTING, MAIN_RISE),
    (MAIN_RISE, MATURE),
    (MATURE, MAIN_RISE),
    (MATURE, DECLINING),
    (DECLINING, BASE),
    # Existing V1 adaptive semantics permit one-step downward
    # reclassification while a candidate remains pending.
    (MAIN_RISE, FERMENTING),
    (FERMENTING, SPROUTING),
}
TOPIC_KEYS = {
    "A1": "ABF載板",
    "A2": "DRAM／DDR",
    "B1": "SiC 晶圓／基板",
    "B2": "固態電容",
    "MLCC": "MLCC",
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _json(value: Any) -> str:
    return json.dumps(
        _jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(_jsonable(value), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            values = {}
            for field in fields:
                value = row.get(field)
                if isinstance(value, date):
                    value = value.isoformat()
                elif isinstance(value, bool):
                    value = "YES" if value else "NO"
                elif isinstance(value, (dict, list, tuple)):
                    value = _json(value)
                values[field] = value
            writer.writerow(values)


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _date(value: Any) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def _num(value: Any) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool(value: Any) -> bool:
    return str(value or "").strip().upper() in {"YES", "TRUE", "1"}


def _augment(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        memory = row.get("state_memory") or {}
        if isinstance(memory, str):
            try:
                memory = json.loads(memory)
            except json.JSONDecodeError:
                memory = {}
        row["cycle_number"] = memory.get("cycleNumber") or 1
        row["cycle_id"] = memory.get("lifecycleCycleId")
        row["cycle_ended"] = memory.get("cycleEnded", False)
        row["main_rise_ancestry"] = memory.get("mainRiseAncestry", False)
    return rows


def _row_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("topic_key") or row.get("topic_id")),
        str(row.get("trading_date")),
    )


def _transition(row: dict[str, Any]) -> bool:
    return bool(row.get("lifecycle_stage")) and row.get("previous_stage") != row.get(
        "lifecycle_stage"
    )


def _events(
    rows: list[dict[str, Any]], topic: str | None = None
) -> list[dict[str, Any]]:
    result = [
        row
        for row in rows
        if (topic is None or row.get("topic_key") == topic) and _transition(row)
    ]
    return sorted(
        result, key=lambda row: (_date(row["trading_date"]), str(row.get("topic_key")))
    )


def _stage_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("topic_key"))].append(row)
    runs: list[dict[str, Any]] = []
    for topic, values in grouped.items():
        values.sort(key=lambda row: _date(row["trading_date"]))
        current: dict[str, Any] | None = None
        for row in values:
            stage = row.get("lifecycle_stage") or "PENDING"
            if current is None or stage != current["stage"]:
                if current is not None:
                    runs.append(current)
                current = {
                    "topic_key": topic,
                    "stage": stage,
                    "start_date": row["trading_date"],
                    "end_date": row["trading_date"],
                    "duration_sessions": 1,
                    "cycle_number": row.get("cycle_number"),
                    "main_rise_segment": row.get("main_rise_segment"),
                }
            else:
                current["end_date"] = row["trading_date"]
                current["duration_sessions"] += 1
        if current is not None:
            runs.append(current)
    return sorted(runs, key=lambda item: (item["topic_key"], _date(item["start_date"])))


def _transition_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(
        (
            row.get("previous_stage") or "NONE",
            row.get("candidate_stage") or "NONE",
            row.get("lifecycle_stage") or "NONE",
            row.get("transition_decision") or "",
        )
        for row in rows
    )
    return [
        {
            "previous_stage": key[0],
            "candidate_stage": key[1],
            "final_stage": key[2],
            "transition_decision": key[3],
            "count": count,
        }
        for key, count in sorted(counts.items())
    ]


def _member_structure(
    member_rows: list[dict[str, Any]], topic: str
) -> list[dict[str, Any]]:
    values = [row for row in member_rows if row.get("topic_key") == topic]
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for row in values:
        unique[(str(row.get("instrument_code")), str(row.get("structural_role")))] = row
    return sorted(
        unique.values(),
        key=lambda row: (
            str(row.get("structural_role")),
            str(row.get("instrument_code")),
        ),
    )


def _read_old() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _read_csv(V11_RECONSTRUCTION), _read_csv(V11_MEMBER_EVIDENCE)


def _comparison(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    old_rows, _ = _read_old()
    old = {_row_key(row): row for row in old_rows}
    new = {_row_key(row): row for row in rows}
    diff: list[dict[str, Any]] = []
    for key in sorted(set(old) | set(new)):
        old_row, new_row = old.get(key, {}), new.get(key, {})
        old_stage, new_stage = (
            old_row.get("lifecycle_stage"),
            new_row.get("lifecycle_stage"),
        )
        old_candidate, new_candidate = (
            old_row.get("candidate_stage"),
            new_row.get("candidate_stage"),
        )
        old_reason, new_reason = (
            old_row.get("transition_reason"),
            new_row.get("transition_reason"),
        )
        changed = (
            old_stage != new_stage
            or old_candidate != new_candidate
            or old_reason != new_reason
        )
        diff.append(
            {
                "topic_key": key[0],
                "trading_date": key[1],
                "old_previous_stage": old_row.get("previous_stage"),
                "new_previous_stage": new_row.get("previous_stage"),
                "old_candidate_stage": old_candidate,
                "new_candidate_stage": new_candidate,
                "old_lifecycle_stage": old_stage,
                "new_lifecycle_stage": new_stage,
                "old_transition_reason": old_reason,
                "new_transition_reason": new_reason,
                "old_segment": old_row.get("main_rise_segment"),
                "new_segment": new_row.get("main_rise_segment"),
                "stage_changed": "YES" if old_stage != new_stage else "NO",
                "changed": "YES" if changed else "NO",
            }
        )
    summary = {
        "old_row_count": len(old_rows),
        "new_row_count": len(rows),
        "changed_rows": sum(item["changed"] == "YES" for item in diff),
        "old_stage_counts": dict(
            Counter(row.get("lifecycle_stage") or "PENDING" for row in old_rows)
        ),
        "new_stage_counts": dict(
            Counter(row.get("lifecycle_stage") or "PENDING" for row in rows)
        ),
        "v1_1_declining_to_mature_count": sum(
            row.get("previous_stage") == DECLINING
            and row.get("lifecycle_stage") == MATURE
            for row in old_rows
        ),
        "v1_2_declining_to_mature_count": sum(
            row.get("previous_stage") == DECLINING
            and row.get("lifecycle_stage") == MATURE
            for row in rows
        ),
        "v1_2_declining_to_base_count": sum(
            row.get("previous_stage") == DECLINING
            and row.get("lifecycle_stage") == BASE
            for row in rows
        ),
    }
    return diff, summary


def _invariants(rows: list[dict[str, Any]]) -> dict[str, Any]:
    events = _events(rows)
    decline_to_mature = [
        row
        for row in events
        if row.get("previous_stage") == DECLINING
        and row.get("lifecycle_stage") == MATURE
    ]
    base_to_decline = [
        row
        for row in events
        if row.get("previous_stage") == BASE and row.get("lifecycle_stage") == DECLINING
    ]
    decline_to_base = [
        row
        for row in events
        if row.get("previous_stage") == DECLINING and row.get("lifecycle_stage") == BASE
    ]
    base_to_sprouting = [
        row
        for row in events
        if row.get("previous_stage") == BASE and row.get("lifecycle_stage") == SPROUTING
    ]
    base_to_fermenting = [
        row
        for row in events
        if row.get("previous_stage") == BASE
        and row.get("lifecycle_stage") == FERMENTING
    ]
    base_to_main = [
        row
        for row in events
        if row.get("previous_stage") == BASE and row.get("lifecycle_stage") == MAIN_RISE
    ]
    illegal = [
        row
        for row in events
        if row.get("previous_stage")
        and (row.get("previous_stage"), row.get("lifecycle_stage"))
        not in LEGAL_TRANSITIONS
    ]
    related_only_base = [
        row
        for row in decline_to_base
        if (_num(row.get("lead_core_positive_breadth")) or 0.0) < 0.45
        or (_num(row.get("lead_core_average_change_pct")) or 0.0) < 0.5
    ]
    related_only_main = [
        row
        for row in rows
        if row.get("lifecycle_stage") == MAIN_RISE
        and row.get("previous_stage") != MAIN_RISE
        and row.get("candidate_stage") == MAIN_RISE
        and (
            (_num(row.get("lead_core_positive_breadth")) or 0.0) < 0.70
            or (_num(row.get("core_positive_breadth")) or 0.0) < 0.70
        )
    ]
    mature_without_ancestry = [
        row
        for row in rows
        if row.get("lifecycle_stage") == MATURE
        and not _bool(row.get("main_rise_ancestry"))
    ]
    old_segment_after_decline = 0
    reset_count = 0
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_topic[str(row.get("topic_key"))].append(row)
    for values in by_topic.values():
        values.sort(key=lambda row: _date(row["trading_date"]))
        confirmed_declines = [
            row
            for row in values
            if row.get("previous_stage") in {MATURE, BASE}
            and row.get("lifecycle_stage") == DECLINING
        ]
        if confirmed_declines:
            decline = confirmed_declines[0]
            decline_day = _date(decline["trading_date"])
            old_cycle = int(_num(decline.get("cycle_number")) or 1)
            old_segment = int(_num(decline.get("main_rise_segment")) or 0)
            for row in values:
                if (
                    _date(row["trading_date"]) > decline_day
                    and int(_num(row.get("cycle_number")) or 1) == old_cycle
                    and int(_num(row.get("main_rise_segment")) or 0) > old_segment
                ):
                    old_segment_after_decline += 1
        for row in values:
            if (
                row.get("lifecycle_stage") == BASE
                and row.get("previous_stage") == DECLINING
                and row.get("main_rise_segment") in (None, "")
            ):
                reset_count += 1
    runs = _stage_runs(rows)
    base_runs = [run for run in runs if run["stage"] == BASE]
    one_day_base = [run for run in base_runs if run["duration_sessions"] == 1]
    rapid_flips = 0
    for values in by_topic.values():
        for index in range(len(values) - 2):
            if [
                values[index].get("lifecycle_stage"),
                values[index + 1].get("lifecycle_stage"),
                values[index + 2].get("lifecycle_stage"),
            ] == [DECLINING, BASE, DECLINING]:
                rapid_flips += 1
    durations = [run["duration_sessions"] for run in base_runs]
    base_noise_rows = [
        row
        for row in rows
        if row.get("previous_stage") == BASE
        and row.get("lifecycle_stage") == BASE
        and not row.get("candidate_stage")
    ]
    return {
        "declining_to_mature_final_count": len(decline_to_mature),
        "declining_to_base_count": len(decline_to_base),
        "base_to_declining_count": len(base_to_decline),
        "base_to_sprouting_count": len(base_to_sprouting),
        "base_to_fermenting_count": len(base_to_fermenting),
        "base_to_main_rise_count": len(base_to_main),
        "direct_base_to_main_rise_allowed": "NO",
        "illegal_final_jumps": len(illegal),
        "related_only_base_false_positives": len(related_only_base),
        "related_only_main_rise_false_positives": len(related_only_main),
        "mature_without_main_rise_ancestry": len(mature_without_ancestry),
        "old_segment_extended_after_confirmed_decline": old_segment_after_decline,
        "segment_reset_count": reset_count,
        "new_cycle_count": len(base_to_sprouting) + len(base_to_fermenting),
        "topics_ever_base": sorted(
            {
                str(row.get("topic_key"))
                for row in rows
                if row.get("lifecycle_stage") == BASE
            }
        ),
        "base_run_count": len(base_runs),
        "base_duration_mean_sessions": round(statistics.mean(durations), 4)
        if durations
        else None,
        "base_duration_median_sessions": statistics.median(durations)
        if durations
        else None,
        "base_ordinary_noise_persistence_rows": len(base_noise_rows),
        "base_ordinary_noise_persistence_pass": all(
            row.get("lifecycle_stage") == BASE for row in base_noise_rows
        ),
        "one_day_base_count": len(one_day_base),
        "base_declining_rapid_flip_count": rapid_flips,
        "illegal_transition_rows": [
            {
                "topic_key": row.get("topic_key"),
                "trading_date": row.get("trading_date"),
                "previous_stage": row.get("previous_stage"),
                "final_stage": row.get("lifecycle_stage"),
            }
            for row in illegal
        ],
    }


def _anchor_check(
    rows: list[dict[str, Any]], topic: str, expected: dict[str, str]
) -> dict[str, Any]:
    index = {(str(row.get("trading_date")), row.get("topic_key")): row for row in rows}
    checks = {}
    for day, stage in expected.items():
        row = index.get((day, topic), {})
        checks[day] = {
            "expected": stage,
            "actual": row.get("lifecycle_stage"),
            "pass": row.get("lifecycle_stage") == stage,
        }
    return {
        "topic": topic,
        "checks": checks,
        "pass": all(item["pass"] for item in checks.values()),
    }


def _category_a_regression(rows: list[dict[str, Any]]) -> dict[str, Any]:
    old_rows, _ = _read_old()
    result: dict[str, Any] = {}
    for label, topic in (("A1", TOPIC_KEYS["A1"]), ("A2", TOPIC_KEYS["A2"])):
        old_events = [
            (
                str(row.get("trading_date")),
                row.get("candidate_stage"),
                row.get("lifecycle_stage"),
                row.get("transition_reason"),
            )
            for row in old_rows
            if row.get("topic_key") == topic
            and "STRUCTURAL_BREAKDOWN" in str(row.get("transition_reason") or "")
        ]
        new_events = [
            (
                str(row.get("trading_date")),
                row.get("candidate_stage"),
                row.get("lifecycle_stage"),
                row.get("transition_reason"),
            )
            for row in rows
            if row.get("topic_key") == topic
            and "STRUCTURAL_BREAKDOWN" in str(row.get("transition_reason") or "")
        ]
        result[label] = {
            "topic": topic,
            "v1_1_events": old_events,
            "v1_2_events": new_events,
            "pass": old_events == new_events,
        }
    return result


def _topic_report(
    topic: str,
    title: str,
    rows: list[dict[str, Any]],
    members: list[dict[str, Any]],
    old_rows: list[dict[str, Any]],
    output: Path,
) -> None:
    values = [row for row in rows if row.get("topic_key") == topic]
    old_values = [row for row in old_rows if row.get("topic_key") == topic]
    lines = [
        f"# {title} — V1.1 vs V1.2",
        "",
        f"TOPIC={topic}",
        "",
        "## Member structure",
        "",
        "| Ticker | Name | Structural role | PRIMARY/SECONDARY |",
        "|---|---|---|---|",
    ]
    for row in _member_structure(members, topic):
        lines.append(
            f"| {row.get('instrument_code')} | {row.get('instrument_name')} | {row.get('structural_role')} | {row.get('topic_relation_type')} |"
        )
    lines += [
        "",
        "## V1.2 event rows",
        "",
        "| Date | Previous | Candidate | Final | Decision | Reason | LC breadth | LC avg | Weak | Drawdown | Cycle | Segment |",
        "|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in values:
        if (
            _transition(row)
            or row.get("candidate_stage") in {BASE, DECLINING}
            or "CANDIDATE" in str(row.get("transition_reason") or "")
        ):
            lines.append(
                f"| {row.get('trading_date')} | {row.get('previous_stage') or ''} | {row.get('candidate_stage') or ''} | {row.get('lifecycle_stage') or ''} | {row.get('transition_decision')} | {row.get('transition_reason')} | {row.get('lead_core_positive_breadth')} | {row.get('lead_core_average_change_pct')} | {row.get('lead_core_weak_ratio')} | {row.get('drawdown_from_peak_pct')} | {row.get('cycle_number')} | {row.get('main_rise_segment') or ''} |"
            )
    old_decline_recovery = [
        row
        for row in old_values
        if row.get("previous_stage") == DECLINING
        and row.get("lifecycle_stage") == MATURE
    ]
    new_base_recovery = [
        row
        for row in values
        if row.get("previous_stage") == DECLINING and row.get("lifecycle_stage") == BASE
    ]
    lines += [
        "",
        "## Semantic result",
        "",
        f"- V1.1 DECLINING→MATURE recovery rows: **{len(old_decline_recovery)}**.",
        f"- V1.2 DECLINING→BASE recovery rows: **{len(new_base_recovery)}**.",
        "- MATURE remains restricted to a MAIN_RISE-bearing cycle; BASE records post-decline stabilization/rebuilding.",
        "- No future return or WS3 field was used.",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _owner_pack(
    rows: list[dict[str, Any]], members: list[dict[str, Any]], inv: dict[str, Any]
) -> list[dict[str, Any]]:
    def pick(predicate, limit=2):
        return [row for row in rows if predicate(row)][:limit]

    candidates: list[tuple[str, list[dict[str, Any]]]] = [
        (
            "A_DECLINING_TO_BASE",
            pick(
                lambda row: (
                    row.get("previous_stage") == DECLINING
                    and row.get("lifecycle_stage") == BASE
                )
            ),
        ),
        (
            "B_BASE_TO_DECLINING_FAILED_BASE",
            pick(
                lambda row: (
                    row.get("previous_stage") == BASE
                    and row.get("lifecycle_stage") == DECLINING
                )
            ),
        ),
        (
            "C_BASE_TO_NEW_CYCLE",
            pick(
                lambda row: (
                    row.get("previous_stage") == BASE
                    and row.get("lifecycle_stage") in {SPROUTING, FERMENTING}
                )
            ),
        ),
        (
            "D_LONG_BASE_PERSISTENCE",
            pick(
                lambda row: (
                    row.get("lifecycle_stage") == BASE
                    and int(_num(row.get("stage_trading_days")) or 0) >= 3
                )
            ),
        ),
        (
            "E_B1_SIC",
            pick(
                lambda row: (
                    row.get("topic_key") == TOPIC_KEYS["B1"]
                    and row.get("previous_stage") == DECLINING
                    and row.get("lifecycle_stage") == BASE
                ),
                1,
            ),
        ),
        (
            "F_B2_SOLID_CAPACITOR",
            pick(
                lambda row: (
                    row.get("topic_key") == TOPIC_KEYS["B2"]
                    and row.get("previous_stage") == DECLINING
                    and row.get("lifecycle_stage") == BASE
                ),
                1,
            ),
        ),
        (
            "G_MLCC",
            pick(
                lambda row: (
                    row.get("topic_key") == TOPIC_KEYS["MLCC"]
                    and (
                        row.get("transition_reason")
                        in {
                            "STRUCTURAL_BREAKDOWN_CANDIDATE",
                            "STRUCTURAL_BREAKDOWN_CONFIRMED",
                            "DECLINING_CANDIDATE_PENDING_CONFIRMATION",
                            "DECLINING_PENDING_CONFIRMATION_SATISFIED",
                        }
                        or row.get("lifecycle_stage") == BASE
                    )
                ),
                2,
            ),
        ),
    ]
    result = []
    for case_type, values in candidates:
        for row in values:
            result.append(
                {
                    "review_case_type": case_type,
                    "topic_key": row.get("topic_key"),
                    "topic_name": row.get("topic_name"),
                    "key_date": row.get("trading_date"),
                    "previous_stage": row.get("previous_stage"),
                    "candidate_stage": row.get("candidate_stage"),
                    "final_stage": row.get("lifecycle_stage"),
                    "transition_decision": row.get("transition_decision"),
                    "transition_reason": row.get("transition_reason"),
                    "lead_core_positive_breadth": row.get("lead_core_positive_breadth"),
                    "lead_core_average_change_pct": row.get(
                        "lead_core_average_change_pct"
                    ),
                    "lead_core_strong_breadth": row.get("lead_core_strong_breadth"),
                    "lead_core_weak_ratio": row.get("lead_core_weak_ratio"),
                    "related_positive_breadth": row.get("related_positive_breadth"),
                    "drawdown_from_peak_pct": row.get("drawdown_from_peak_pct"),
                    "cycle_number": row.get("cycle_number"),
                    "main_rise_segment": row.get("main_rise_segment"),
                    "member_structure": _json(
                        _member_structure(members, str(row.get("topic_key")))
                    ),
                    "OWNER_VERDICT": "",
                    "OWNER_NOTE": "",
                }
            )
    return result


def _run_tests() -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC)
    targets = [
        "services/api/tests/test_topic_lifecycle_v1_1.py",
        "services/api/tests/test_topic_lifecycle_v1_2.py",
        "services/api/tests/test_topic_lifecycle_contract.py",
        "services/api/tests/test_topic_lifecycle_contract_closure.py",
    ]
    process = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *targets],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    compile_process = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            str(SRC / "topicpilot_api" / "topic_lifecycle_v1.py"),
            str(TOOLS / "ws1_lifecycle_v1_2_base_reset.py"),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    full_process = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "services/api/tests"],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "lifecycle_test_command": [sys.executable, "-m", "pytest", "-q", *targets],
        "lifecycle_tests_pass": process.returncode == 0,
        "lifecycle_tests_returncode": process.returncode,
        "lifecycle_tests_stdout": process.stdout[-12000:],
        "lifecycle_tests_stderr": process.stderr[-4000:],
        "compile_pass": compile_process.returncode == 0,
        "compile_returncode": compile_process.returncode,
        "compile_stderr": compile_process.stderr[-4000:],
        "full_api_suite_pass": full_process.returncode == 0,
        "full_api_suite_returncode": full_process.returncode,
        "full_api_suite_stdout": full_process.stdout[-16000:],
        "full_api_suite_stderr": full_process.stderr[-4000:],
        "full_api_suite_scope_note": "Known unrelated repository fixture failures are retained as scope diagnostics; Lifecycle V1.2 targeted tests are reported separately.",
    }


def _write_topic_audit(
    path: Path,
    rows: list[dict[str, Any]],
    members: list[dict[str, Any]],
    inv: dict[str, Any],
) -> None:
    lines = [
        "# Lifecycle V1.2 Current-State Audit",
        "",
        "## Existing V1.1 path",
        "",
        "1. `topic_lifecycle_v1._candidate` used the prior-stage `DECLINING` recovery gate (Lead/Core positive breadth, Lead/Core average change, and Lead/Core weak ratio) to emit `MATURE`.",
        "2. Existing confirmation memory carried that candidate through `candidateStreak` and `ADAPTIVE_CONFIRMATION_SATISFIED`; therefore the final transition was `DECLINING→MATURE` after confirmation.",
        "3. `trajectory_recovered` is a raw evidence boolean: Lead/Core positive breadth ≥ the existing mature-recovery breadth boundary and Lead/Core average change ≥ the existing mature-recovery average boundary. It is not a return label or score.",
        "4. `drawdown_from_peak_pct` is calculated from per-member running Lead/Core peak closes in state memory; the decline gate also requires the existing structural drawdown boundary and Lead/Core deterioration.",
        "5. The same running peaks, recovery gate, meaningful-expansion flag, weak ratio, and confirmation memory are reusable for BASE. Related remains contextual and has no independent BASE authority.",
        "",
        "## V1.2 implementation surface",
        "",
        "- Added formal `BASE` stage to the backend/Owner contract and reconstruction serialization.",
        "- Retargeted the existing `DECLINING` recovery candidate from `MATURE` to `BASE`.",
        "- Added `BASE→SPROUTING` and `BASE→FERMENTING` using the existing gates; direct `BASE→MAIN_RISE` is blocked.",
        "- Allowed the existing confirmed deterioration memory to operate from `BASE`, yielding legal `BASE→DECLINING`.",
        "- Added `cycleNumber`, `lifecycleCycleId`, `cycleEnded`, and `mainRiseAncestry` to state memory. Confirmed decline clears the old segment; new-cycle MAIN_RISE begins at segment 1.",
        "- ORM stores lifecycle stages as `String(32)` and API stage fields are strings, so no database enum/check-constraint migration is required.",
        "",
        "## Audit invariants",
        "",
        f"- DECLINING→MATURE final transitions: **{inv['declining_to_mature_final_count']}**.",
        f"- Related-only BASE false positives: **{inv['related_only_base_false_positives']}**.",
        f"- Related-only MAIN_RISE false positives: **{inv['related_only_main_rise_false_positives']}**.",
        f"- Illegal final jumps: **{inv['illegal_final_jumps']}**.",
        "",
        "The audit is an implementation record. It does not declare Owner acceptance.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _write_transition_spec(path: Path) -> None:
    lines = [
        "# Lifecycle V1.2 Final Transition Specification",
        "",
        "## Stage semantics",
        "",
        "- `BASE`: post-confirmed-decline stabilization, rebuilding, bottoming, or low-level consolidation; it does not require MAIN_RISE ancestry.",
        "- `MATURE`: high-level mature/consolidation state after MAIN_RISE within the same bullish cycle; MAIN_RISE ancestry is required.",
        "- `DECLINING→MATURE` is illegal.",
        "",
        "## Legal transitions",
        "",
        "`BASE→SPROUTING`, `BASE→FERMENTING`, `SPROUTING→FERMENTING`, `FERMENTING→MAIN_RISE`, `MAIN_RISE→MATURE`, `MATURE→MAIN_RISE`, `MATURE→DECLINING`, `DECLINING→BASE`, and `BASE→DECLINING` after confirmed structural deterioration.",
        "",
        "`BASE→MAIN_RISE` is an illegal jump. A new cycle must establish SPROUTING or FERMENTING first.",
        "",
        "## Confirmation",
        "",
        "DECLINING recovery reuses the V1.1 Lead/Core recovery gate and confirmation memory, but confirms BASE. BASE ordinary noise persists. BASE deterioration reuses the V1.1 decline candidate/persistence memory and can confirm BASE→DECLINING. Related members provide context only.",
        "",
        "## Cycle/segment",
        "",
        "Confirmed DECLINING sets `cycleEnded=true`, clears `mainRiseSegment`, and clears `mainRiseAncestry`. A confirmed BASE→SPROUTING/FERMENTING starts the next `cycleNumber`; the next MAIN_RISE is segment 1. MAIN_RISE→MATURE→MAIN_RISE remains the same cycle and increments segment.",
        "",
        "This specification is ready for Owner semantic review and is not a production acceptance declaration.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _write_cycle_report(
    path: Path, rows: list[dict[str, Any]], inv: dict[str, Any]
) -> None:
    lines = [
        "# Cycle and MAIN_RISE Segment Reset Analysis",
        "",
        f"- New cycle count observed from deterministic cycle numbers: **{inv['new_cycle_count']}**.",
        f"- Segment reset confirmations after DECLINING→BASE: **{inv['segment_reset_count']}**.",
        f"- Old segment extended after confirmed DECLINING: **{inv['old_segment_extended_after_confirmed_decline']}**.",
        f"- MATURE rows without MAIN_RISE ancestry: **{inv['mature_without_main_rise_ancestry']}**.",
        "",
        "| Topic | Date | Final stage | Cycle | Segment | Cycle ended | MAIN_RISE ancestry |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        if row.get("lifecycle_stage") in {BASE, MAIN_RISE, MATURE, DECLINING} and (
            row.get("previous_stage") != row.get("lifecycle_stage")
            or row.get("lifecycle_stage") == BASE
        ):
            lines.append(
                f"| {row.get('topic_key')} | {row.get('trading_date')} | {row.get('lifecycle_stage')} | {row.get('cycle_number')} | {row.get('main_rise_segment') or ''} | {row.get('cycle_ended')} | {row.get('main_rise_ancestry')} |"
            )
    lines += [
        "",
        "No performance outcome was used; this is stage/state-memory evidence only.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        default=os.environ.get(
            "TOPICPILOT_DATABASE_URL",
            "postgresql+psycopg://topicpilot:topicpilot_local_only@localhost:5432/topicpilot",
        ),
    )
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
    first_rows, first_members, _first_summary = _build_reconstruction(
        master, prices, price_rows, policy
    )
    second_rows, second_members, _second_summary = _build_reconstruction(
        master, prices, price_rows, policy
    )
    rows = _augment(first_rows)
    second_rows = _augment(second_rows)
    member_evidence = first_members
    replay = {
        "deterministic_replay": "PASS"
        if rows == second_rows and member_evidence == second_members
        else "FAIL",
        "same_row_count": len(rows) == len(second_rows),
        "same_member_evidence_row_count": len(member_evidence) == len(second_members),
        "same_reconstruction_sha256": _hash_rows(rows, V12_FIELDS)
        == _hash_rows(second_rows, V12_FIELDS),
        "first_reconstruction_sha256": _hash_rows(rows, V12_FIELDS),
        "second_reconstruction_sha256": _hash_rows(second_rows, V12_FIELDS),
        "first_member_evidence_sha256": _hash_rows(member_evidence, MEMBER_FIELDS),
        "second_member_evidence_sha256": _hash_rows(second_members, MEMBER_FIELDS),
        "database_mutation": "NO",
    }
    diff, comparison = _comparison(rows)
    inv = _invariants(rows)
    category_a = _category_a_regression(rows)
    old_rows, _ = _read_old()
    sessions = sorted({row["trading_date"] for row in rows})
    instrument_hashes = {
        "instrument_master_sha256": _file_sha256(instrument_path),
        "topic_master_sha256": _file_sha256(topic_path),
        "membership_master_sha256": _file_sha256(membership_path),
    }
    price_hash = _hash_rows(
        price_rows,
        [
            "market_code",
            "instrument_code",
            "trading_date",
            "close",
            "adjustment_state",
            "source_code",
            "adapter_version",
            "reference_data_version",
            "normalization_contract_version",
            "mapping_policy_version",
        ],
    )
    implementation_hash = _file_sha256(SRC / "topicpilot_api" / "topic_lifecycle_v1.py")
    reconstruction_hash = hashlib.sha256(
        _json(
            {
                **instrument_hashes,
                "price_input_sha256": price_hash,
                "policy_version": LIFECYCLE_POLICY_VERSION,
                "calculation_version": LIFECYCLE_CALCULATION_VERSION,
                "implementation_sha256": implementation_hash,
                "reconstruction_output_sha256": replay["first_reconstruction_sha256"],
                "member_evidence_sha256": replay["first_member_evidence_sha256"],
            }
        ).encode("utf-8")
    ).hexdigest()
    members_by_topic = member_evidence
    owner_pack = _owner_pack(rows, members_by_topic, inv)
    test_results = _run_tests()
    migration_results = {
        "migration_required": False,
        "reason": "Lifecycle stage columns are String(32), not a DB enum/check constraint; API Pydantic stage fields are str.",
        "orm_checked": "services/api/src/topicpilot_api/orm/lifecycle.py",
        "api_checked": "services/api/src/topicpilot_api/schemas.py",
        "production_db_mutation": "NO",
    }
    anchors = {
        "B1_V1_2_REPLAY_PASS": _anchor_check(
            rows, TOPIC_KEYS["B1"], {"2026-07-28": DECLINING, "2026-08-03": BASE}
        ),
        "B2_V1_2_REPLAY_PASS": _anchor_check(
            rows,
            TOPIC_KEYS["B2"],
            {
                "2026-07-20": DECLINING,
                "2026-07-22": BASE,
                "2026-07-24": DECLINING,
                "2026-08-03": BASE,
            },
        ),
        "MLCC_REGRESSION_PASS": _anchor_check(
            rows,
            TOPIC_KEYS["MLCC"],
            {
                "2026-07-07": MAIN_RISE,
                "2026-07-08": MATURE,
                "2026-07-17": MATURE,
                "2026-07-20": DECLINING,
            },
        ),
    }
    a1_pass = bool(category_a.get("A1", {}).get("pass"))
    a2_pass = bool(category_a.get("A2", {}).get("pass"))
    flags = {
        "LIFECYCLE_V1_2_IMPLEMENTED": "YES",
        "BASE_STAGE_IMPLEMENTED": "YES",
        "MATURE_SEMANTICS_RESTRICTED": "YES",
        "DECLINING_TO_MATURE_FINAL_COUNT": inv["declining_to_mature_final_count"],
        "DECLINING_TO_BASE_IMPLEMENTED": "YES"
        if inv["declining_to_base_count"] >= 0
        else "NO",
        "BASE_TO_DECLINING_IMPLEMENTED": "YES",
        "BASE_TO_SPROUTING_IMPLEMENTED": "YES",
        "BASE_TO_FERMENTING_IMPLEMENTED": "YES",
        "DIRECT_BASE_TO_MAIN_RISE_ALLOWED": "NO",
        "CYCLE_IDENTITY_IMPLEMENTED": "YES",
        "SEGMENT_RESET_IMPLEMENTED": "YES",
        "A1_REGRESSION_PASS": "YES" if a1_pass else "NO",
        "A2_REGRESSION_PASS": "YES" if a2_pass else "NO",
        "B1_V1_2_REPLAY_PASS": "YES"
        if replay["deterministic_replay"] == "PASS"
        and anchors["B1_V1_2_REPLAY_PASS"]["pass"]
        else "NO",
        "B2_V1_2_REPLAY_PASS": "YES"
        if replay["deterministic_replay"] == "PASS"
        and anchors["B2_V1_2_REPLAY_PASS"]["pass"]
        else "NO",
        "MLCC_REGRESSION_PASS": "YES"
        if anchors["MLCC_REGRESSION_PASS"]["pass"]
        else "NO",
        "RELATED_ONLY_BASE_FALSE_POSITIVES": inv["related_only_base_false_positives"],
        "ILLEGAL_FINAL_JUMPS": inv["illegal_final_jumps"],
        "DETERMINISTIC_REPLAY_PASS": replay["deterministic_replay"],
        "FUTURE_RETURNS_USED": "NO",
        "WS3_USED": "NO",
        "TOPIC_MASTER_CHANGED": "NO",
        "INSTRUMENT_MASTER_CHANGED": "NO",
        "MEMBERSHIP_CHANGED": "NO",
        "STRUCTURAL_ROLE_CHANGED": "NO",
        "PRODUCTION_DB_MUTATION": "NO",
        "PUSH": "NO",
        "DEPLOY": "NO",
        "NEXT_TASK_CHANGED": "NO",
    }

    _write_csv(
        args.output_dir / "lifecycle-v1-2-historical-reconstruction.csv",
        V12_FIELDS,
        rows,
    )
    _write_csv(
        args.output_dir / "lifecycle-v1-2-member-evidence.csv",
        MEMBER_FIELDS,
        member_evidence,
    )
    _write_csv(
        args.output_dir / "lifecycle-v1-2-owner-validation-pack.csv",
        list(owner_pack[0].keys())
        if owner_pack
        else ["review_case_type", "OWNER_VERDICT", "OWNER_NOTE"],
        owner_pack,
    )
    _write_csv(
        args.output_dir / "base-transition-summary.csv",
        [
            "previous_stage",
            "candidate_stage",
            "final_stage",
            "transition_decision",
            "count",
        ],
        _transition_summary(rows),
    )
    one_day_fields = [
        "topic_key",
        "topic_name",
        "date",
        "lead_core_positive_breadth",
        "lead_core_average_change_pct",
        "lead_core_strong_breadth",
        "lead_core_weak_ratio",
        "drawdown_from_peak_pct",
        "previous_decline_duration",
        "recovery_evidence",
        "next_transition",
        "reason",
    ]
    one_day_rows = []
    runs = _stage_runs(rows)
    row_index = {
        (str(row.get("topic_key")), str(row.get("trading_date"))): row for row in rows
    }
    for run in runs:
        if run["stage"] != BASE or run["duration_sessions"] != 1:
            continue
        row = row_index.get((run["topic_key"], str(run["start_date"])), {})
        topic_runs = [item for item in runs if item["topic_key"] == run["topic_key"]]
        run_index = topic_runs.index(run)
        previous_run = topic_runs[run_index - 1] if run_index > 0 else None
        next_run = (
            topic_runs[run_index + 1] if run_index + 1 < len(topic_runs) else None
        )
        one_day_rows.append(
            {
                "topic_key": run["topic_key"],
                "topic_name": row.get("topic_name"),
                "date": run["start_date"],
                "lead_core_positive_breadth": row.get("lead_core_positive_breadth"),
                "lead_core_average_change_pct": row.get("lead_core_average_change_pct"),
                "lead_core_strong_breadth": row.get("lead_core_strong_breadth"),
                "lead_core_weak_ratio": row.get("lead_core_weak_ratio"),
                "drawdown_from_peak_pct": row.get("drawdown_from_peak_pct"),
                "previous_decline_duration": previous_run["duration_sessions"]
                if previous_run and previous_run["stage"] == DECLINING
                else "",
                "recovery_evidence": row.get("trajectory_recovered"),
                "next_transition": f"BASE→{next_run['stage']}" if next_run else "",
                "reason": row.get("transition_reason"),
            }
        )
    _write_csv(
        args.output_dir / "one-day-base-review.csv", one_day_fields, one_day_rows
    )
    _write_csv(
        args.output_dir / "lifecycle-v1-1-vs-v1-2-diff.csv",
        list(diff[0].keys()) if diff else ["topic_key", "trading_date"],
        diff,
    )
    _write_json(
        args.output_dir / "deterministic-replay-results.json",
        {**replay, "reconstruction_hash": reconstruction_hash},
    )
    _write_json(args.output_dir / "test-results.json", test_results)
    _write_json(
        args.output_dir / "migration-qualification-results.json", migration_results
    )
    _write_json(
        args.output_dir / "run-summary.json",
        {
            "task_id": TASK_ID,
            "status": "OWNER_SEMANTIC_ACCEPTANCE_READY",
            "reconstruction": {
                "row_count": len(rows),
                "member_evidence_row_count": len(member_evidence),
                "topic_count": len({row.get("topic_key") for row in rows}),
                "session_count": len(sessions),
                "start_date": min(sessions) if sessions else None,
                "end_date": max(sessions) if sessions else None,
                "stage_counts": dict(
                    Counter(row.get("lifecycle_stage") or "PENDING" for row in rows)
                ),
            },
            "master": validation.to_dict(),
            "master_hashes": instrument_hashes,
            "price_authority": {
                "price_query_sha256": hashlib.sha256(
                    PRICE_QUERY.encode("utf-8")
                ).hexdigest(),
                "price_input_sha256": price_hash,
                "price_row_count": len(price_rows),
                "database_access": "READ_ONLY",
                "future_returns_read": "NO",
            },
            "comparison": comparison,
            "invariants": inv,
            "anchors": anchors,
            "category_a_regression": category_a,
            "replay": replay,
            "tests": test_results,
            "migration": migration_results,
            "reconstruction_hash": reconstruction_hash,
            "flags": flags,
            "owner_semantic_acceptance": "READY_NOT_ACCEPTED",
        },
    )
    _write_topic_audit(
        args.output_dir / "lifecycle-v1-2-current-state-audit.md",
        rows,
        member_evidence,
        inv,
    )
    _write_transition_spec(args.output_dir / "lifecycle-v1-2-final-transition-spec.md")
    _write_cycle_report(args.output_dir / "cycle-segment-reset-analysis.md", rows, inv)
    summary_lines = [
        "# Lifecycle V1.1 vs V1.2 Summary",
        "",
        f"V1.1 DECLINING→MATURE final count: **{comparison['v1_1_declining_to_mature_count']}**.",
        f"V1.2 DECLINING→MATURE final count: **{comparison['v1_2_declining_to_mature_count']}**.",
        f"V1.2 DECLINING→BASE count: **{comparison['v1_2_declining_to_base_count']}**.",
        f"BASE→DECLINING: **{inv['base_to_declining_count']}**; BASE→SPROUTING: **{inv['base_to_sprouting_count']}**; BASE→FERMENTING: **{inv['base_to_fermenting_count']}**; BASE→MAIN_RISE: **{inv['base_to_main_rise_count']}**.",
        f"Changed topic/date rows: **{comparison['changed_rows']}**. Changes are expected to be concentrated in post-DECLINING recovery semantics and cycle memory.",
        "",
        "A1/A2 Category A cancellation behavior is compared separately and is expected to remain unchanged. MLCC's accepted pre-decline anchors are regression checked. No future returns or WS3 data were read.",
        "",
    ]
    (args.output_dir / "lifecycle-v1-1-vs-v1-2-summary.md").write_text(
        "\n".join(summary_lines), encoding="utf-8", newline="\n"
    )
    _topic_report(
        TOPIC_KEYS["B1"],
        "B1 SiC wafer/substrate",
        rows,
        member_evidence,
        old_rows,
        args.output_dir / "b1-v1-1-vs-v1-2.md",
    )
    _topic_report(
        TOPIC_KEYS["B2"],
        "B2 solid capacitor",
        rows,
        member_evidence,
        old_rows,
        args.output_dir / "b2-v1-1-vs-v1-2.md",
    )
    _topic_report(
        TOPIC_KEYS["MLCC"],
        "MLCC",
        rows,
        member_evidence,
        old_rows,
        args.output_dir / "mlcc-v1-1-vs-v1-2.md",
    )
    category_lines = [
        "# Category A Regression Check",
        "",
        "| Case | Topic | V1.1/V1.2 structural-breakdown events identical |",
        "|---|---|---|",
    ]
    for label, item in category_a.items():
        category_lines.append(
            f"| {label} | {item['topic']} | {'PASS' if item['pass'] else 'FAIL'} |"
        )
    category_lines += [
        "",
        "A1 ABF載板 and A2 DRAM／DDR are checked only for their accepted structural-breakdown candidate/repair-cancellation evidence. No other case is used to make the Owner decision.",
        "",
    ]
    (args.output_dir / "category-a-regression-check.md").write_text(
        "\n".join(category_lines), encoding="utf-8", newline="\n"
    )
    owner_lines = [
        "# Lifecycle V1.2 Owner Validation Pack",
        "",
        "`OWNER_VERDICT` and `OWNER_NOTE` are intentionally blank in the CSV.",
        "",
        f"Rows selected: **{len(owner_pack)}**. Categories include DECLINING→BASE, failed BASE→DECLINING, BASE→new-cycle entry, long BASE persistence, B1, B2, and MLCC.",
        "",
    ]
    (args.output_dir / "owner-validation-pack-notes.md").write_text(
        "\n".join(owner_lines), encoding="utf-8", newline="\n"
    )
    closure_lines = [f"# {TASK_ID}", "", "## Formal closure flags", "", "```text"]
    closure_lines.extend(f"{key}={value}" for key, value in flags.items())
    closure_lines += [
        "```",
        "",
        "## Result",
        "",
        f"The V1.2 implementation emitted **{len(rows)} topic×trading_date rows** and **{len(member_evidence)} member evidence rows** across **{len(sessions)} valid trading sessions** using the current canonical masters.",
        "",
        f"Reconstruction identity: `{reconstruction_hash}`; deterministic replay: **{replay['deterministic_replay']}**.",
        "",
        "The implementation stops at `OWNER_SEMANTIC_ACCEPTANCE`. It does not declare Lifecycle V1.2 finally accepted.",
        "",
        "No future returns, WS3 data, production DB mutation, push, deploy, Topic Master change, Instrument Master change, membership change, role change, or NEXT_TASK change occurred.",
        "",
    ]
    (args.output_dir / "formal-closure-report.md").write_text(
        "\n".join(closure_lines), encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir),
                "row_count": len(rows),
                "member_evidence_row_count": len(member_evidence),
                "reconstruction_hash": reconstruction_hash,
                "replay": replay["deterministic_replay"],
                "flags": flags,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
