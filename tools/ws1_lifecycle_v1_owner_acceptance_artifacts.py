"""Build read-only comparison and Owner review artifacts for Lifecycle V1.

This tool consumes the already reconstructed V1 rows and member evidence.  It
does not query or mutate a TopicPilot database, and it never uses future
returns or other look-ahead information to choose a case.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

STAGES = ("SPROUTING", "FERMENTING", "MAIN_RISE", "MATURE", "DECLINING")
STAGE_SET = set(STAGES)
OLD_L5_HASH = "17faa9be1189d6fab1bdfe518a1faf9e90d9be1ec994008ed59beef8bf6ecb95"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _date(row: dict[str, str]) -> date:
    return date.fromisoformat(row["trading_date"])


def _state(row: dict[str, str]) -> str:
    return (row.get("lifecycle_stage") or row.get("evaluation_status") or "").strip()


def _number(row: dict[str, str], field: str) -> float | None:
    value = row.get(field, "")
    if value in {"", "None", "null"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _int(row: dict[str, str], field: str) -> int:
    value = row.get(field, "")
    try:
        return int(float(value)) if value else 0
    except ValueError:
        return 0


def _role_counts(row: dict[str, str]) -> dict[str, int]:
    try:
        value = json.loads(row.get("role_counts") or "{}")
    except json.JSONDecodeError:
        value = {}
    return {str(key): int(number) for key, number in value.items()}


def _known(value: str | None) -> bool:
    return value in STAGE_SET


def _transition_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row for row in rows
        if _known(row.get("previous_stage"))
        and _known(row.get("lifecycle_stage"))
        and row["previous_stage"] != row["lifecycle_stage"]
    ]


def _flip_count(rows: list[dict[str, str]]) -> int:
    by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_topic[row["topic_id"]].append(row)
    count = 0
    for sequence in by_topic.values():
        sequence.sort(key=_date)
        for before, middle, after in zip(sequence, sequence[1:], sequence[2:]):
            first, second, third = _state(before), _state(middle), _state(after)
            if first in STAGE_SET and second in STAGE_SET and third in STAGE_SET and first == third and first != second:
                count += 1
    return count


def _transition_counts(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(f"{row['previous_stage']}->{row['lifecycle_stage']}" for row in _transition_rows(rows))


def _case_row(
    case_id: str,
    row: dict[str, str] | None,
    evidence: dict[tuple[str, str], list[dict[str, str]]],
    not_found_reason: str = "",
) -> dict[str, Any]:
    if row is None:
        return {
            "case_id": case_id,
            "topic": "",
            "date": "",
            "previous_stage": "",
            "new_stage": "",
            "segment": "",
            "transition_decision": "NOT_FOUND_IN_RECONSTRUCTION",
            "transition_reason": not_found_reason,
            "stage_entered_at": "",
            "stage_trading_days": "",
            "lead_summary": "",
            "core_summary": "",
            "related_summary": "",
            "participation_summary": "",
            "intensity_summary": "",
            "progression_summary": "",
            "trajectory_summary": "",
            "engine_decision": "NOT_FOUND_IN_RECONSTRUCTION",
            "owner_label": "",
            "owner_comment": "",
        }
    key = (row["topic_id"], row["trading_date"])
    members = evidence.get(key, [])

    def member_summary(role: str) -> str:
        selected = [
            {
                "code": item.get("member_code", ""),
                "change_pct": item.get("change_pct", ""),
                "close": item.get("close", ""),
                "previous_close": item.get("previous_close", ""),
                "status": item.get("observation_status", ""),
            }
            for item in members if item.get("role") == role
        ]
        return json.dumps(selected, ensure_ascii=False, separators=(",", ":"))

    roles = _role_counts(row)
    return {
        "case_id": case_id,
        "topic": row.get("topic_slug", ""),
        "date": row.get("trading_date", ""),
        "previous_stage": row.get("previous_stage", ""),
        "new_stage": row.get("lifecycle_stage", "") or row.get("evaluation_status", ""),
        "segment": row.get("main_rise_segment", ""),
        "transition_decision": row.get("transition_decision", ""),
        "transition_reason": row.get("transition_reason", ""),
        "stage_entered_at": row.get("stage_entered_at", ""),
        "stage_trading_days": row.get("stage_trading_days", ""),
        "lead_summary": member_summary("LEAD"),
        "core_summary": member_summary("CORE"),
        "related_summary": member_summary("RELATED"),
        "participation_summary": json.dumps({
            "lead_core_positive_breadth": row.get("lead_core_positive_breadth", ""),
            "core_positive_breadth": row.get("core_positive_breadth", ""),
            "related_positive_breadth": row.get("related_positive_breadth", ""),
            "role_counts": roles,
            "coverage_pct": row.get("coverage_pct", ""),
        }, ensure_ascii=False, separators=(",", ":")),
        "intensity_summary": json.dumps({
            "average_change_pct": row.get("average_change_pct", ""),
            "lead_core_average_change_pct": row.get("lead_core_average_change_pct", ""),
            "strong_breadth": row.get("strong_breadth", ""),
            "weak_ratio": row.get("weak_ratio", ""),
        }, ensure_ascii=False, separators=(",", ":")),
        "progression_summary": json.dumps({
            "meaningful_expansion": row.get("meaningful_expansion", ""),
            "main_rise_segment": row.get("main_rise_segment", ""),
            "segment_entry_date": row.get("segment_entry_date", ""),
            "segment_anchor_date": row.get("segment_anchor_date", ""),
            "days_since_meaningful_expansion": row.get("days_since_meaningful_expansion", ""),
        }, ensure_ascii=False, separators=(",", ":")),
        "trajectory_summary": json.dumps({
            "trajectory_recovered": row.get("trajectory_recovered", ""),
            "drawdown_from_peak_pct": row.get("drawdown_from_peak_pct", ""),
            "role_authority_available": row.get("role_authority_available", ""),
            "lineage_status": row.get("lineage_status", ""),
        }, ensure_ascii=False, separators=(",", ":")),
        "engine_decision": row.get("transition_decision", "") or row.get("evaluation_status", ""),
        "owner_label": "",
        "owner_comment": "",
    }


def _first(rows: list[dict[str, str]], predicate: Callable[[dict[str, str]], bool], used: set[tuple[str, str]]) -> dict[str, str] | None:
    for row in rows:
        key = (row["topic_id"], row["trading_date"])
        if key not in used and predicate(row):
            used.add(key)
            return row
    return None


def _build_cases(rows: list[dict[str, str]], evidence: dict[tuple[str, str], list[dict[str, str]]]) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: (_date(row), row.get("topic_slug", ""), row.get("topic_id", "")))
    used: set[tuple[str, str]] = set()
    cases: list[tuple[str, dict[str, str] | None, str]] = []
    cases.append(("01_SPROUTING", _first(ordered, lambda r: r.get("lifecycle_stage") == "SPROUTING", used), "No SPROUTING row in reconstruction"))
    cases.append(("02_SPROUTING_TO_FERMENTING", _first(ordered, lambda r: r.get("previous_stage") == "SPROUTING" and r.get("lifecycle_stage") == "FERMENTING", used), "No SPROUTING to FERMENTING transition in reconstruction"))
    cases.append(("03_FERMENTING_TO_MAIN_RISE", _first(ordered, lambda r: r.get("previous_stage") == "FERMENTING" and r.get("lifecycle_stage") == "MAIN_RISE", used), "No FERMENTING to MAIN_RISE transition in reconstruction"))
    cases.append(("04_DIRECT_CORE_DRIVEN_MAIN_RISE", _first(ordered, lambda r: r.get("lifecycle_stage") == "MAIN_RISE" and r.get("previous_stage") not in {"MAIN_RISE", "MATURE"} and _role_counts(r).get("CORE", 0) > 0, used), "No direct Core-driven MAIN_RISE transition in reconstruction"))
    cases.append(("05_SUSTAINED_MAIN_RISE", _first(ordered, lambda r: r.get("lifecycle_stage") == "MAIN_RISE" and r.get("previous_stage") == "MAIN_RISE" and _int(r, "stage_trading_days") >= 5, used), "No sustained MAIN_RISE row in reconstruction"))
    cases.append(("06_ONE_DAY_PULLBACK_REMAINS_MAIN_RISE", _first(ordered, lambda r: r.get("lifecycle_stage") == "MAIN_RISE" and r.get("previous_stage") == "MAIN_RISE" and (_number(r, "average_change_pct") or 0) < 0, used), "No MAIN_RISE pullback row in reconstruction"))
    cases.append(("07_MAIN_RISE_TO_MATURE_5_SESSION_STALL", _first(ordered, lambda r: r.get("transition_reason") == "MAIN_RISE_EXPANSION_STALLED_5_SESSIONS", used), "No five-session stalled-expansion maturity event in reconstruction"))
    cases.append(("08_MATURE_TO_MAIN_RISE_SEGMENT_2", _first(ordered, lambda r: r.get("previous_stage") == "MATURE" and r.get("lifecycle_stage") == "MAIN_RISE" and _int(r, "main_rise_segment") >= 2, used), "No segment-2 MATURE to MAIN_RISE re-entry in reconstruction"))
    cases.append(("09_SEGMENT_3_IF_REAL", _first(ordered, lambda r: r.get("lifecycle_stage") == "MAIN_RISE" and _int(r, "main_rise_segment") >= 3, used), "No real segment-3 MAIN_RISE episode in reconstruction window"))
    cases.append(("10_MATURE_TO_DECLINING", _first(ordered, lambda r: r.get("previous_stage") == "MATURE" and r.get("lifecycle_stage") == "DECLINING", used), "No MATURE to DECLINING transition in reconstruction"))
    cases.append(("11_RELATED_ONLY_RALLY_REJECTED", _first(ordered, lambda r: r.get("lifecycle_stage") != "MAIN_RISE" and _role_counts(r).get("RELATED", 0) > 0 and _role_counts(r).get("CORE", 0) == 0 and _role_counts(r).get("LEAD", 0) == 0, used), "No related-only rally rejection row in reconstruction"))
    cases.append(("12_LEADER_ONLY_RALLY_REJECTED", _first(ordered, lambda r: r.get("lifecycle_stage") != "MAIN_RISE" and _role_counts(r).get("LEAD", 0) > 0 and _role_counts(r).get("CORE", 0) == 0 and _role_counts(r).get("RELATED", 0) == 0, used), "No leader-only rally rejection row in reconstruction"))
    cases.append(("13_BROAD_CORE_WITHOUT_STRONG_LEAD", _first(ordered, lambda r: r.get("lifecycle_stage") == "MAIN_RISE" and _role_counts(r).get("CORE", 0) > 0 and (_number(r, "core_positive_breadth") or 0) >= 0.7 and (_number(r, "strong_breadth") or 0) < 0.35, used), "No broad Core activation without strong aggregate intensity in reconstruction"))
    cases.append(("14_ANTI_WHIPSAW", _first(ordered, lambda r: r.get("lifecycle_stage") == "MAIN_RISE" and r.get("previous_stage") == "MAIN_RISE" and (_number(r, "average_change_pct") or 0) <= 0, used), "No anti-whipsaw MAIN_RISE hold row in reconstruction"))
    return [_case_row(case_id, row, evidence, reason) for case_id, row, reason in cases]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v1-dir", type=Path, required=True)
    parser.add_argument("--old-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    v1_rows = _read_csv(args.v1_dir / "lifecycle-v1-historical-reconstruction.csv")
    old_rows = _read_csv(args.old_csv)
    evidence_rows = _read_csv(args.v1_dir / "lifecycle-v1-member-evidence.csv")
    evidence: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in evidence_rows:
        evidence[(row["topic_id"], row["trading_date"])].append(row)

    old_map = {(row["topic_id"], row["trading_date"]): row for row in old_rows}
    v1_map = {(row["topic_id"], row["trading_date"]): row for row in v1_rows}
    diff_rows: list[dict[str, Any]] = []
    for key in sorted(set(old_map) | set(v1_map), key=lambda item: (item[1], item[0])):
        old = old_map.get(key, {})
        v1 = v1_map.get(key, {})
        old_state, v1_state = _state(old), _state(v1)
        diff_rows.append({
            "topic_id": key[0], "trading_date": key[1],
            "topic_slug": v1.get("topic_slug", old.get("topic_slug", "")),
            "old_state": old_state, "v1_state": v1_state,
            "old_lifecycle_stage": old.get("lifecycle_stage", ""),
            "v1_lifecycle_stage": v1.get("lifecycle_stage", ""),
            "old_evaluation_status": old.get("evaluation_status", ""),
            "v1_evaluation_status": v1.get("evaluation_status", ""),
            "stage_changed": "YES" if old_state != v1_state else "NO",
            "old_transition_reason": old.get("transition_reason", ""),
            "v1_transition_reason": v1.get("transition_reason", ""),
            "v1_main_rise_segment": v1.get("main_rise_segment", ""),
            "v1_transition_decision": v1.get("transition_decision", ""),
        })

    stage_counts_v1 = Counter(_state(row) for row in v1_rows)
    stage_counts_old = Counter(_state(row) for row in old_rows)
    _write_csv(args.output_dir / "lifecycle-v1-stage-distribution.csv", ["stage", "old_l5_rows", "v1_rows", "v1_pct"], [
        {"stage": stage, "old_l5_rows": stage_counts_old.get(stage, 0), "v1_rows": stage_counts_v1.get(stage, 0), "v1_pct": round(stage_counts_v1.get(stage, 0) * 100 / len(v1_rows), 4)}
        for stage in sorted(set(stage_counts_old) | set(stage_counts_v1))
    ])

    transitions_v1 = _transition_rows(v1_rows)
    transition_counts = _transition_counts(v1_rows)
    _write_csv(args.output_dir / "lifecycle-v1-transition-distribution.csv", ["from_stage", "to_stage", "transition_count"], [
        {"from_stage": key.split("->", 1)[0], "to_stage": key.split("->", 1)[1], "transition_count": value}
        for key, value in sorted(transition_counts.items())
    ])
    diff_fields = [
        "topic_id", "topic_slug", "trading_date", "old_state", "v1_state", "old_lifecycle_stage", "v1_lifecycle_stage",
        "old_evaluation_status", "v1_evaluation_status", "stage_changed", "old_transition_reason", "v1_transition_reason",
        "v1_main_rise_segment", "v1_transition_decision",
    ]
    _write_csv(args.output_dir / "old-l5-vs-v1-diff.csv", diff_fields, diff_rows)

    changed = sum(row["stage_changed"] == "YES" for row in diff_rows)
    old_transitions = _transition_counts(old_rows)
    old_flips, v1_flips = _flip_count(old_rows), _flip_count(v1_rows)
    segment2_rows = sum(_int(row, "main_rise_segment") >= 2 and row.get("lifecycle_stage") == "MAIN_RISE" for row in v1_rows)
    segment2_transitions = sum(_int(row, "main_rise_segment") >= 2 and row.get("lifecycle_stage") == "MAIN_RISE" for row in transitions_v1)
    segment3_rows = sum(_int(row, "main_rise_segment") >= 3 and row.get("lifecycle_stage") == "MAIN_RISE" for row in v1_rows)
    segment3_transitions = sum(_int(row, "main_rise_segment") >= 3 and row.get("lifecycle_stage") == "MAIN_RISE" for row in transitions_v1)
    main_rise_transitions = sum(row.get("lifecycle_stage") == "MAIN_RISE" for row in transitions_v1)
    maturity_events = [row for row in v1_rows if row.get("transition_reason") == "MAIN_RISE_EXPANSION_STALLED_5_SESSIONS"]
    mature_reentry = [row for row in transitions_v1 if row.get("previous_stage") == "MATURE" and row.get("lifecycle_stage") == "MAIN_RISE"]
    mature_decline = [row for row in transitions_v1 if row.get("previous_stage") == "MATURE" and row.get("lifecycle_stage") == "DECLINING"]
    related_only_main_rise = [row for row in v1_rows if row.get("lifecycle_stage") == "MAIN_RISE" and _role_counts(row).get("RELATED", 0) > 0 and _role_counts(row).get("CORE", 0) == 0 and _role_counts(row).get("LEAD", 0) == 0]
    leader_only_main_rise = [row for row in v1_rows if row.get("lifecycle_stage") == "MAIN_RISE" and _role_counts(row).get("LEAD", 0) > 0 and _role_counts(row).get("CORE", 0) == 0 and _role_counts(row).get("RELATED", 0) == 0]
    core_without_strong_lead = [row for row in v1_rows if row.get("lifecycle_stage") == "MAIN_RISE" and _role_counts(row).get("CORE", 0) > 0 and (_number(row, "core_positive_breadth") or 0) >= 0.7 and (_number(row, "strong_breadth") or 0) < 0.35]

    summary_lines = [
        "# Old L5 vs Lifecycle V1 summary",
        "",
        "This is a semantic state comparison only. No investment returns or future outcomes were evaluated.",
        "",
        f"- Old L5 preserved hash: `{OLD_L5_HASH}`.",
        f"- Old rows / V1 rows: **{len(old_rows)} / {len(v1_rows)}**.",
        f"- Changed effective state rows: **{changed}**; unchanged: **{len(diff_rows) - changed}**.",
        f"- Old known-stage transitions: **{sum(old_transitions.values())}**; V1 known-stage transitions: **{sum(transition_counts.values())}**.",
        f"- One-day A→B→A flips: old **{old_flips}**, V1 **{v1_flips}**, decreased: **{'YES' if v1_flips < old_flips else 'NO'}**.",
        f"- MAIN_RISE transitions: **{main_rise_transitions}**; segment-2+ rows **{segment2_rows}**, segment-2+ transitions **{segment2_transitions}**; segment-3+ rows **{segment3_rows}**, transitions **{segment3_transitions}**.",
        f"- MAIN_RISE→MATURE five-session stall events: **{len(maturity_events)}**.",
        f"- MATURE→MAIN_RISE re-entry events: **{len(mature_reentry)}**.",
        f"- MATURE→DECLINING events: **{len(mature_decline)}**.",
        f"- Related-only MAIN_RISE rows: **{len(related_only_main_rise)}**; leader-only MAIN_RISE rows: **{len(leader_only_main_rise)}**.",
        f"- Core-driven MAIN_RISE rows without strong aggregate breadth: **{len(core_without_strong_lead)}**.",
        "",
        "## Stage distributions",
        "",
        "| Stage/status | Old L5 | V1 |",
        "|---|---:|---:|",
    ]
    summary_lines.extend(f"| {stage} | {stage_counts_old.get(stage, 0)} | {stage_counts_v1.get(stage, 0)} |" for stage in sorted(set(stage_counts_old) | set(stage_counts_v1)))
    summary_lines.extend([
        "",
        "The V1 rows are `RETROSPECTIVE_RESEARCH_ONLY` and use the current taxonomy projected backward. A missing segment-3 case is reported as not found rather than invented.",
        "",
    ])
    (args.output_dir / "old-l5-vs-v1-summary.md").write_text("\n".join(summary_lines), encoding="utf-8", newline="\n")

    cases = _build_cases(v1_rows, evidence)
    case_fields = [
        "case_id", "topic", "date", "previous_stage", "new_stage", "segment", "transition_decision", "transition_reason",
        "stage_entered_at", "stage_trading_days", "lead_summary", "core_summary", "related_summary", "participation_summary",
        "intensity_summary", "progression_summary", "trajectory_summary", "engine_decision", "owner_label", "owner_comment",
    ]
    _write_csv(args.output_dir / "lifecycle-v1-owner-validation-pack.csv", case_fields, cases)
    guide = [
        "# Lifecycle V1 Owner validation guide",
        "",
        "Review each row against the raw Lead/Core/Related member summaries and the four evidence dimensions. `owner_label` and `owner_comment` are intentionally blank for manual acceptance.",
        "",
        "Case selection is deterministic and based only on same-day and prior-state evidence. No future return or outcome was used.",
        "",
        "Suggested labels: `CORRECT`, `TOO_EARLY`, `TOO_LATE`, `FALSE_MAIN_RISE`, `MISSED_MAIN_RISE`, `WHIPSAW`, `MATURITY_TOO_EARLY`, `MATURITY_TOO_LATE`, `DECLINE_TOO_EARLY`, `DECLINE_TOO_LATE`, `IDENTITY_PROBLEM`, `OTHER`.",
        "",
        "A case with `NOT_FOUND_IN_RECONSTRUCTION` is an honest absence in this date window, not a fabricated example. In particular, Segment 3 is only populated when a real segment-3 row exists.",
        "",
        "Evidence fields: participation = breadth/coverage; intensity = average/strong/weak movement; progression = expansion and segment clock; trajectory = recovery, peak drawdown, and lineage context.",
        "",
        "The reconstruction is retrospective and current-taxonomy projected backward, not PIT history and not production Forward Shadow publication.",
    ]
    (args.output_dir / "lifecycle-v1-owner-validation-guide.md").write_text("\n".join(guide) + "\n", encoding="utf-8", newline="\n")

    # D-1 is the immediately preceding reconstructed trading row for the same topic.
    by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in v1_rows:
        by_topic[row["topic_id"]].append(row)
    d1_rows: list[dict[str, Any]] = []
    for sequence in by_topic.values():
        sequence.sort(key=_date)
        for index, row in enumerate(sequence):
            if row.get("lifecycle_stage") != "MAIN_RISE" or row.get("previous_stage") == "MAIN_RISE":
                continue
            prior = sequence[index - 1] if index else {}
            d1_rows.append({
                "topic_id": row.get("topic_id", ""), "topic_slug": row.get("topic_slug", ""),
                "d0_date": row.get("trading_date", ""), "d0_previous_stage": row.get("previous_stage", ""), "d0_stage": row.get("lifecycle_stage", ""),
                "d1_date": prior.get("trading_date", ""), "d1_stage": prior.get("lifecycle_stage", "") or prior.get("evaluation_status", ""),
                "d1_candidate_stage": prior.get("candidate_stage", ""), "d1_evaluation_status": prior.get("evaluation_status", ""),
                "d1_transition_reason": prior.get("transition_reason", ""),
            })
    _write_csv(args.output_dir / "lifecycle-v1-d1-context-preview.csv", [
        "topic_id", "topic_slug", "d0_date", "d0_previous_stage", "d0_stage", "d1_date", "d1_stage", "d1_candidate_stage", "d1_evaluation_status", "d1_transition_reason",
    ], d1_rows)

    manifest_path = args.v1_dir / "lifecycle-v1-reconstruction-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    replay = {
        "main_dataset_replay": manifest.get("replay", {}),
        "member_evidence_rows": len(evidence_rows),
        "owner_artifacts_recomputed_from_same_dataset": True,
        "database_mutation": "NO",
        "lookahead": "NO",
    }
    _write_json(args.output_dir / "lifecycle-v1-deterministic-replay.json", replay)
    _write_json(args.output_dir / "analysis-summary.json", {
        "old_l5_hash": OLD_L5_HASH,
        "old_rows": len(old_rows), "v1_rows": len(v1_rows), "changed_state_rows": changed,
        "unchanged_state_rows": len(diff_rows) - changed,
        "old_stage_distribution": dict(sorted(stage_counts_old.items())),
        "v1_stage_distribution": dict(sorted(stage_counts_v1.items())),
        "old_transition_count": sum(old_transitions.values()), "v1_transition_count": sum(transition_counts.values()),
        "old_one_day_flips": old_flips, "v1_one_day_flips": v1_flips,
        "main_rise_transitions": main_rise_transitions,
        "segment_2_plus_rows": segment2_rows, "segment_2_plus_transitions": segment2_transitions,
        "segment_3_plus_rows": segment3_rows, "segment_3_plus_transitions": segment3_transitions,
        "main_rise_to_mature_5_session_events": len(maturity_events),
        "mature_to_main_rise_events": len(mature_reentry), "mature_to_declining_events": len(mature_decline),
        "related_only_main_rise_rows": len(related_only_main_rise), "leader_only_main_rise_rows": len(leader_only_main_rise),
        "core_without_strong_lead_rows": len(core_without_strong_lead), "d1_main_rise_context_rows": len(d1_rows),
    })
    print(json.dumps({"changed_state_rows": changed, "v1_rows": len(v1_rows), "owner_cases": len(cases), "d1_rows": len(d1_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
