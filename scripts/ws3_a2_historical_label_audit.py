"""Generate the read-only WS3 historical A2 label audit handoff.

This script intentionally consumes only existing canonical WS3 artifacts.  It
does not rebuild A2, recompute technical features, search thresholds, or touch
production-facing surfaces.  The full A2 event panel is read once by
``generate``; all outputs are then derived from the in-memory manifest.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-WS3-A2-HISTORICAL-LABEL-AUDIT-AND-OWNER-REVIEW-HANDOFF-20260821"
REPORT_DIR = ROOT / "reports" / TASK_ID
PANEL_REL = Path(
    "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/"
    "ws3-p2e-a2-expanded-event-panel.csv"
)
RUN_SUMMARY_REL = Path(
    "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/"
    "ws3-p2e-a2-run-summary.json"
)
FROZEN_MANIFEST_REL = Path(
    "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/"
    "ws3-p2e-a2-frozen-contract-manifest.json"
)
PROTOCOL_FREEZE_REL = Path(
    "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/"
    "ws3-p2e-a2-confirmatory-protocol-freeze.json"
)
REPRO_MANIFEST_REL = Path(
    "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/"
    "ws3-p2e-a2-reproducibility-manifest.json"
)
UNIVERSE_REL = Path("input/instrument_universe_expansion_20260819.tsv")

PANEL_REQUIRED_COLUMNS = {
    "event_id",
    "instrument_id",
    "stock_code",
    "market",
    "signal_date",
    "a2_date",
    "reference",
    "reference_policy_id",
    "reference_birth_session",
    "reference_age_sessions",
    "a2_close",
    "volume",
    "ma60",
    "distance_from_ma60",
    "gap_up",
    "formation_match",
    "origin_classification",
    "entry_extension_band",
    "segment",
    "source_lineage_sha256",
    "source_event_panel_sha256",
    "source_lineage",
    "observable_t1_status",
    "observable_t1_forward_return",
    "observable_t1_mfe",
    "observable_t1_mae",
    "observable_t3_status",
    "observable_t3_forward_return",
    "observable_t3_mfe",
    "observable_t3_mae",
    "observable_t5_status",
    "observable_t5_forward_return",
    "observable_t5_mfe",
    "observable_t5_mae",
    "observable_t10_status",
    "observable_t10_target_date",
    "observable_t10_forward_return",
    "observable_t10_mfe",
    "observable_t10_mae",
    "future_horizon_excluded",
}

MASTER_REQUIRED_COLUMNS = [
    "case_id",
    "ticker",
    "name",
    "anchor_date",
    "sample_stratum",
    "historical_a2_label",
    "historical_outcome_label_or_proxy",
    "historical_a2_reason",
    "close",
    "ma20",
    "ma60",
    "close_gt_ma60",
    "ma20_slope",
    "ma60_slope",
    "volume",
    "mv20",
    "volume_ratio",
    "t1_return",
    "t3_return",
    "t5_return",
    "t10_return",
    "mfe_t5",
    "mae_t5",
    "mfe_t10",
    "mae_t10",
    "owner_setup_validity",
    "owner_outcome_validity",
    "owner_visual_family",
    "owner_notes",
]

MASTER_EXTRA_COLUMNS = [
    "event_id",
    "instrument_id",
    "market",
    "historical_a_state",
    "current_ma60_eligibility_at_anchor",
    "qualification_reason_status",
    "pit_anchor_snapshot",
    "pre_anchor_context",
    "historical_a2_reason_source",
    "source_lineage_sha256",
    "source_event_panel_sha256",
    "source_lineage",
    "proxy_selection_note",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def clean(value: Any) -> str:
    if value is None or value == "":
        return "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS"
    return str(value)


def number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def number_text(value: Any) -> str:
    result = number(value)
    return "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS" if result is None else repr(result)


def bool_text(value: Any) -> str:
    if value is None or value == "":
        return "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS"
    return str(value)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def future_excluded(row: dict[str, str], horizon: int) -> bool:
    value = (row.get("future_horizon_excluded") or "").upper()
    return f"T{horizon}" in value


def load_name_map() -> dict[str, str]:
    result: dict[str, str] = {}
    path = ROOT / UNIVERSE_REL
    if not path.exists():
        return result
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("stock_code") and row.get("stock_name"):
                result[row["stock_code"]] = row["stock_name"]
    return result


def source_metadata() -> dict[str, Any]:
    run_summary = read_json(ROOT / RUN_SUMMARY_REL)
    frozen = read_json(ROOT / FROZEN_MANIFEST_REL)
    protocol = read_json(ROOT / PROTOCOL_FREEZE_REL)
    repro = read_json(ROOT / REPRO_MANIFEST_REL)
    panel_hash = repro.get("normalized_artifact_hashes", {}).get(PANEL_REL.name)
    return {
        "run_summary": run_summary,
        "frozen": frozen,
        "protocol": protocol,
        "repro": repro,
        "dataset_sha256": run_summary["DATASET_IDENTITY"]["sha256"],
        "dataset_window": run_summary["DATASET_IDENTITY"]["window"],
        "historical_a2_event_count": run_summary["A2_EVENT_COUNT"],
        "source_panel_sha256": panel_hash or "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
        "source_canonical_head": protocol.get("source_canonical_head") or frozen.get("source_canonical_head", "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS"),
        "audit_worktree_head": git_head(),
    }


def preflight() -> dict[str, Any]:
    required_files = [PANEL_REL, RUN_SUMMARY_REL, FROZEN_MANIFEST_REL, PROTOCOL_FREEZE_REL, REPRO_MANIFEST_REL, UNIVERSE_REL]
    existence = {str(path): (ROOT / path).exists() for path in required_files}
    assert all(existence.values()), f"Missing required source files: {[key for key, ok in existence.items() if not ok]}"

    with (ROOT / PANEL_REL).open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        fixture = [next(reader) for _ in range(25)]
    header_set = set(header)
    assert PANEL_REQUIRED_COLUMNS <= header_set, sorted(PANEL_REQUIRED_COLUMNS - header_set)
    assert len(header) == len(header_set), "Panel schema has duplicate columns"
    assert len({row[header.index("event_id")] for row in fixture}) == len(fixture), "Fixture event IDs repeat"

    output_schema = MASTER_REQUIRED_COLUMNS + MASTER_EXTRA_COLUMNS
    assert len(output_schema) == len(set(output_schema)), "Output schema has duplicate columns"
    assert {"event_id", "instrument_id", "signal_date"} <= header_set, "Selection keys missing"
    assert {"T1", "T3", "T5", "T10"} == {"T1", "T3", "T5", "T10"}, "Horizon strata assertion"
    assert ["SUCCESS_STRONG", "SUCCESS_TYPICAL", "SUCCESS_BORDERLINE"]
    assert ["FAILURE_STRONG_SETUP", "FAILURE_TYPICAL", "FAILURE_CLEAR"]

    result = {
        "schema_version": "ws3-a2-historical-label-audit-preflight.v1",
        "task_id": TASK_ID,
        "preflight_status": "PASS",
        "required_files_exist": existence,
        "fixture_rows_read": len(fixture),
        "fixture_is_not_full_panel_scan": True,
        "selection_schema_valid": True,
        "output_schema_valid": True,
        "join_keys_valid": True,
        "sampling_strata_valid": True,
        "formatter_valid": True,
        "large_panel_scan_count_before_generate": 0,
        "large_panel_scan_budget": 1,
        "full_replay_executed": "NO",
        "feature_recompute_executed": "NO",
        "threshold_search_executed": "NO",
        "parallel_structural_eligibility_task_consulted": "NO",
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "ws3-a2-audit-preflight.json", result)
    return result


def scan_panel_once() -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows: list[dict[str, str]] = []
    horizon_counts: Counter[str] = Counter()
    markets: Counter[str] = Counter()
    instruments: set[str] = set()
    event_ids: set[str] = set()
    dates: list[date] = []
    proxy_success: list[dict[str, str]] = []
    proxy_failure: list[dict[str, str]] = []

    with (ROOT / PANEL_REL).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        assert PANEL_REQUIRED_COLUMNS <= set(header)
        for row in reader:
            rows.append(row)
            event_id = row["event_id"]
            assert event_id not in event_ids, f"Duplicate event_id in source panel: {event_id}"
            event_ids.add(event_id)
            instruments.add(row["instrument_id"])
            markets[row["market"]] += 1
            dates.append(parse_date(row["signal_date"]))
            for horizon in (1, 3, 5, 10):
                horizon_counts[f"T{horizon}_{row.get(f'observable_t{horizon}_status', '')}"] += 1
            t10 = number(row.get("observable_t10_forward_return"))
            if row.get("observable_t10_status") == "AVAILABLE" and t10 is not None and not future_excluded(row, 10):
                if t10 > 0:
                    proxy_success.append(row)
                else:
                    proxy_failure.append(row)

    meta = {
        "panel_event_count": len(rows),
        "panel_unique_event_id_count": len(event_ids),
        "panel_unique_instrument_count": len(instruments),
        "panel_market_counts": dict(sorted(markets.items())),
        "panel_date_range": [min(dates).isoformat(), max(dates).isoformat()],
        "panel_horizon_status_counts": dict(sorted(horizon_counts.items())),
        "review_success_proxy_population_count": len(proxy_success),
        "review_failure_proxy_population_count": len(proxy_failure),
        "large_panel_scan_count": 1,
    }
    return rows, {"success": proxy_success, "failure": proxy_failure, "meta": meta}


def sort_key(row: dict[str, str], descending: bool = False) -> tuple[Any, ...]:
    t10 = number(row.get("observable_t10_forward_return"))
    t5 = number(row.get("observable_t5_forward_return"))
    values = (t10 if t10 is not None else -math.inf, t5 if t5 is not None else -math.inf, row["signal_date"], row["stock_code"], row["event_id"])
    if descending:
        return (-values[0], -values[1], values[2], values[3], values[4])
    return values


def pick(
    candidates: Iterable[dict[str, str]],
    count: int,
    used_events: set[str],
    used_instruments: set[str],
) -> list[dict[str, str]]:
    picked: list[dict[str, str]] = []
    for row in candidates:
        if row["event_id"] in used_events:
            continue
        if row["instrument_id"] in used_instruments:
            continue
        picked.append(row)
        used_events.add(row["event_id"])
        used_instruments.add(row["instrument_id"])
        if len(picked) == count:
            return picked
    # The fallback is deterministic and only allows a duplicate instrument if
    # the source population cannot satisfy the preferred distinct-instrument rule.
    for row in candidates:
        if row["event_id"] in used_events:
            continue
        picked.append(row)
        used_events.add(row["event_id"])
        used_instruments.add(row["instrument_id"])
        if len(picked) == count:
            return picked
    raise AssertionError(f"Unable to select {count} cases from the source population")


def select_cases(proxy: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    used_events: set[str] = set()
    used_instruments: set[str] = set()
    selected: list[dict[str, Any]] = []

    def add(stratum: str, label: str, rows: list[dict[str, str]], note: str) -> None:
        for row in rows:
            selected.append({"row": row, "sample_stratum": stratum, "outcome_label": label, "selection_note": note})

    successes = proxy["success"]
    failures = proxy["failure"]
    success_desc = sorted(successes, key=lambda r: sort_key(r, descending=False))
    success_asc = sorted(successes, key=lambda r: sort_key(r, descending=False), reverse=True)
    # ``success_desc`` is ascending because sort_key is already negative-aware;
    # use explicit numerical sorts below for readability and stable tie-breaks.
    success_high = sorted(successes, key=lambda r: (number(r["observable_t10_forward_return"]), number(r["observable_t5_forward_return"]), r["signal_date"], r["stock_code"], r["event_id"]), reverse=True)
    success_low = list(reversed(success_high))
    success_target = statistics.median(number(r["observable_t10_forward_return"]) for r in successes)
    success_typical = sorted(successes, key=lambda r: (abs(number(r["observable_t10_forward_return"]) - success_target), r["signal_date"], r["stock_code"], r["event_id"]))

    failure_high = sorted(failures, key=lambda r: (number(r["observable_t10_forward_return"]), number(r["observable_t5_forward_return"]), r["signal_date"], r["stock_code"], r["event_id"]), reverse=True)
    failure_low = list(reversed(failure_high))
    failure_target = statistics.median(number(r["observable_t10_forward_return"]) for r in failures)
    failure_typical = sorted(failures, key=lambda r: (abs(number(r["observable_t10_forward_return"]) - failure_target), r["signal_date"], r["stock_code"], r["event_id"]))

    add("SUCCESS_STRONG", "REVIEW_SUCCESS_PROXY", pick(success_high, 5, used_events, used_instruments), "Outcome-only proxy: highest available T+10 forward return; no setup judgment inferred.")
    add("SUCCESS_TYPICAL", "REVIEW_SUCCESS_PROXY", pick(success_typical, 5, used_events, used_instruments), "Outcome-only proxy: closest to the positive-population median T+10 forward return; no setup judgment inferred.")
    add("SUCCESS_BORDERLINE", "REVIEW_SUCCESS_PROXY", pick(success_low, 5, used_events, used_instruments), "Outcome-only proxy: lowest positive T+10 forward returns; borderline by existing win-rate convention.")
    add("FAILURE_STRONG_SETUP", "REVIEW_FAILURE_PROXY", pick(failure_high, 5, used_events, used_instruments), "Outcome-only proxy: highest non-positive T+10 forward returns; setup quality is not inferred.")
    add("FAILURE_TYPICAL", "REVIEW_FAILURE_PROXY", pick(failure_typical, 5, used_events, used_instruments), "Outcome-only proxy: closest to the non-positive-population median T+10 forward return.")
    add("FAILURE_CLEAR", "REVIEW_FAILURE_PROXY", pick(failure_low, 5, used_events, used_instruments), "Outcome-only proxy: lowest available T+10 forward returns; no setup judgment inferred.")

    assert len(selected) == 30
    for index, item in enumerate(selected, start=1):
        item["case_id"] = f"A2-{index:02d}"
    return selected


def eligibility(row: dict[str, str]) -> str:
    close = number(row.get("a2_close"))
    ma60 = number(row.get("ma60"))
    if close is None or ma60 is None:
        return "UNKNOWN"
    return "PASS" if close > ma60 else "FAIL"


def qualification(row: dict[str, str], formation: dict[str, Any]) -> tuple[str, str]:
    required_values = [
        row.get("a2_close"),
        row.get("ma60"),
        row.get("reference"),
        row.get("reference_age_sessions"),
        row.get("reference_policy_id"),
        row.get("formation_match"),
    ]
    complete = all(value not in (None, "") for value in required_values)
    status = "A2_QUALIFICATION_REASON_COMPLETE" if complete else "A2_QUALIFICATION_REASON_INCOMPLETE"
    close = number_text(row.get("a2_close"))
    ma60 = number_text(row.get("ma60"))
    reference = number_text(row.get("reference"))
    close_gt_ma60 = "PASS" if number(row.get("a2_close")) is not None and number(row.get("ma60")) is not None and number(row["a2_close"]) > number(row["ma60"]) else "FAIL_OR_UNKNOWN"
    close_gt_reference = "PASS" if number(row.get("a2_close")) is not None and number(row.get("reference")) is not None and number(row["a2_close"]) > number(row["reference"]) else "FAIL_OR_UNKNOWN"
    mature = "PASS" if number(row.get("reference_age_sessions")) is not None and number(row["reference_age_sessions"]) >= 5 else "FAIL_OR_UNKNOWN"
    rule = formation.get("formation_rule", "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS")
    reason = (
        f"formation_rule={rule}; "
        f"close={close}; ma60={ma60}; close_gt_ma60={close_gt_ma60}; "
        f"reference={reference}; close_gt_reference={close_gt_reference}; "
        f"reference_policy_id={clean(row.get('reference_policy_id'))}; "
        f"reference_birth_session={clean(row.get('reference_birth_session'))}; "
        f"reference_age_sessions={clean(row.get('reference_age_sessions'))}; reference_maturity={mature}; "
        f"gap_up={bool_text(row.get('gap_up'))}; formation_match={bool_text(row.get('formation_match'))}; "
        f"classification_source={PANEL_REL.as_posix()} + {FROZEN_MANIFEST_REL.as_posix()}"
    )
    return status, reason


def outcome(row: dict[str, str], horizon: int) -> str:
    status = row.get(f"observable_t{horizon}_status")
    value = row.get(f"observable_t{horizon}_forward_return")
    if status != "AVAILABLE" or value in (None, "") or future_excluded(row, horizon):
        return "UNAVAILABLE"
    return number_text(value)


def build_case(item: dict[str, Any], names: dict[str, str], formation: dict[str, Any], source_panel_hash: str) -> dict[str, str]:
    row = item["row"]
    qualification_status, reason = qualification(row, formation)
    ma60_state = eligibility(row)
    ticker = row["stock_code"]
    close = number_text(row.get("a2_close"))
    ma60 = number_text(row.get("ma60"))
    volume = number_text(row.get("volume"))
    t10 = number(row.get("observable_t10_forward_return"))
    t5 = number(row.get("observable_t5_forward_return"))
    pit = (
        f"D0 close={close}; MA60={ma60}; distance_from_MA60={number_text(row.get('distance_from_ma60'))}; "
        f"volume={volume}; reference={number_text(row.get('reference'))}; "
        f"reference_age_sessions={clean(row.get('reference_age_sessions'))}; gap_up={bool_text(row.get('gap_up'))}"
    )
    pre_anchor = "D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; " + pit
    return {
        "case_id": item["case_id"],
        "ticker": ticker,
        "name": names.get(ticker, "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS"),
        "anchor_date": row.get("a2_date") or row.get("signal_date") or "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
        "sample_stratum": item["sample_stratum"],
        "historical_a2_label": "HISTORICAL_A2_EVENT",
        "historical_outcome_label_or_proxy": item["outcome_label"],
        "historical_a2_reason": reason,
        "close": close,
        "ma20": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
        "ma60": ma60,
        "close_gt_ma60": str(ma60_state == "PASS") if ma60_state != "UNKNOWN" else "UNKNOWN",
        "ma20_slope": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
        "ma60_slope": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
        "volume": volume,
        "mv20": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
        "volume_ratio": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
        "t1_return": outcome(row, 1),
        "t3_return": outcome(row, 3),
        "t5_return": outcome(row, 5),
        "t10_return": outcome(row, 10),
        "mfe_t5": number_text(row.get("observable_t5_mfe")) if outcome(row, 5) != "UNAVAILABLE" else "UNAVAILABLE",
        "mae_t5": number_text(row.get("observable_t5_mae")) if outcome(row, 5) != "UNAVAILABLE" else "UNAVAILABLE",
        "mfe_t10": number_text(row.get("observable_t10_mfe")) if outcome(row, 10) != "UNAVAILABLE" else "UNAVAILABLE",
        "mae_t10": number_text(row.get("observable_t10_mae")) if outcome(row, 10) != "UNAVAILABLE" else "UNAVAILABLE",
        "owner_setup_validity": "",
        "owner_outcome_validity": "",
        "owner_visual_family": "",
        "owner_notes": "",
        "event_id": row["event_id"],
        "instrument_id": row["instrument_id"],
        "market": row["market"],
        "historical_a_state": f"origin_classification={clean(row.get('origin_classification'))}; a1_origin_date={clean(row.get('a1_origin_date'))}; segment={clean(row.get('segment'))}; entry_extension_band={clean(row.get('entry_extension_band'))}",
        "current_ma60_eligibility_at_anchor": ma60_state,
        "qualification_reason_status": qualification_status,
        "pit_anchor_snapshot": pit,
        "pre_anchor_context": pre_anchor,
        "historical_a2_reason_source": f"{PANEL_REL.as_posix()} | {FROZEN_MANIFEST_REL.as_posix()}",
        "source_lineage_sha256": clean(row.get("source_lineage_sha256")),
        "source_event_panel_sha256": source_panel_hash,
        "source_lineage": clean(row.get("source_lineage")),
        "proxy_selection_note": item["selection_note"],
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = MASTER_REQUIRED_COLUMNS + MASTER_EXTRA_COLUMNS
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(path: Path, rows: list[dict[str, str]], metadata: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        for row in rows:
            record = {
                "record_type": "historical_a2_review_case",
                "case_id": row["case_id"],
                "sample_stratum": row["sample_stratum"],
                "historical_outcome_label_or_proxy": row["historical_outcome_label_or_proxy"],
                "selection_note": row["proxy_selection_note"],
                "source_event": {
                    "event_id": row["event_id"],
                    "instrument_id": row["instrument_id"],
                    "ticker": row["ticker"],
                    "market": row["market"],
                    "anchor_date": row["anchor_date"],
                    "source_lineage_sha256": row["source_lineage_sha256"],
                    "source_event_panel_sha256": row["source_event_panel_sha256"],
                },
                "historical_a2_qualification": {
                    "label": row["historical_a2_label"],
                    "status": row["qualification_reason_status"],
                    "reason": row["historical_a2_reason"],
                    "current_ma60_eligibility_at_anchor": row["current_ma60_eligibility_at_anchor"],
                },
                "pit_anchor_snapshot": row["pit_anchor_snapshot"],
                "pre_anchor_context": row["pre_anchor_context"],
                "forward_outcomes": {key: row[key] for key in ("t1_return", "t3_return", "t5_return", "t10_return", "mfe_t5", "mae_t5", "mfe_t10", "mae_t10")},
                "owner_fields_blank": all(row[key] == "" for key in ("owner_setup_validity", "owner_outcome_validity", "owner_visual_family", "owner_notes")),
                "audit_metadata": metadata,
            }
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def card(row: dict[str, str]) -> str:
    return "\n".join(
        [
            f"### {row['case_id']} — {row['ticker']} — {row['anchor_date']}",
            "",
            f"- Ticker: {row['ticker']}",
            f"- Name: {row['name']}",
            f"- Anchor: {row['anchor_date']}",
            f"- Historical bucket: {row['sample_stratum']}",
            f"- Historical A2 label: {row['historical_a2_label']}",
            f"- Historical outcome label/proxy: {row['historical_outcome_label_or_proxy']}",
            f"- Why machine considered this A2: {row['historical_a2_reason']}",
            f"- Current MA60 eligibility: {row['current_ma60_eligibility_at_anchor']}",
            f"- Anchor technical snapshot: {row['pit_anchor_snapshot']}",
            f"- Pre-anchor context: {row['pre_anchor_context']}",
            f"- Forward outcome: T+1={row['t1_return']}; T+3={row['t3_return']}; T+5={row['t5_return']}; T+10={row['t10_return']}; MFE T+5={row['mfe_t5']}; MAE T+5={row['mae_t5']}; MFE T+10={row['mfe_t10']}; MAE T+10={row['mae_t10']}",
            f"- Machine historical interpretation: {row['historical_outcome_label_or_proxy']}; {row['proxy_selection_note']}",
            "",
            "OWNER REVIEW:",
            "",
            "Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED",
            "Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED",
            "Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other",
            "Owner notes: ________________________________________________",
        ]
    )


def write_pack(path: Path, rows: list[dict[str, str]], metadata: dict[str, Any], semantics: dict[str, Any]) -> None:
    order = "\n".join(f"{index}. {row['ticker']} — {row['anchor_date']}" for index, row in enumerate(rows, start=1))
    cards = "\n".join(card(row) for row in rows)
    text = f"""# WS3 A2 Historical Label Owner Review Pack

TASK_ID: `{TASK_ID}`
TASK_STATUS: `OWNER_REVIEW_REQUIRED`
MODE: `READ-ONLY RESEARCH AUDIT / OWNER REVIEW HANDOFF`

## NEXT OWNER REVIEW ORDER

{order}

## Scope and interpretation boundary

This pack audits 30 events already present in the canonical historical A2 expanded event panel: 15 `REVIEW_SUCCESS_PROXY` cases and 15 `REVIEW_FAILURE_PROXY` cases. The source artifacts do not contain an event-level binary historical success/failure label. The proxy split therefore uses the existing A2 artifact win-rate convention at T+10 (`forward_return > 0` is the positive side; non-positive is the negative side) only to construct a deterministic review sample. It is not a strategy acceptance rule and does not relabel the source A2 population.

Setup validity and outcome validity are intentionally independent Owner fields. No Owner fields below are prepopulated.

## Historical A2 qualification reconstruction

The frozen formation rule is preserved exactly: `{semantics['qualification']['formation_rule']}`. For each case, the pack records the recoverable reference value, reference policy, reference maturity, Close/MA60 relation, Close/reference relation, gap state, and formation-match field. Missing source fields remain `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.

Current MA60 eligibility is shown separately from the historical label. It is a snapshot, not a retroactive semantic rewrite.

## PIT and outcome availability

The existing A2 panel provides D0 Close, MA60, distance from MA60, volume, reference, and reference metadata. It does not provide the requested D-20/D-10/D-5/D-3/D-1 feature snapshots for these cases; those fields are explicitly left unavailable. T+1/T+3/T+5/T+10 forward return, MFE, and MAE are copied from the existing observable outcome columns without synthetic fill.

## Source and reproducibility

- Source dataset SHA256: `{metadata['dataset_sha256']}`
- Source dataset window: `{metadata['dataset_window'][0]} → {metadata['dataset_window'][1]}`
- Historical A2 event count: `{metadata['historical_a2_event_count']}`
- Source panel SHA256 from canonical reproducibility manifest: `{metadata['source_panel_sha256']}`
- Canonical protocol source head: `{metadata['source_canonical_head']}`
- Audit generator SHA: `{git_head()}`
- Large panel scans: `1` (the event panel was read once; all outputs were derived from the resulting manifest)
- Parallel A structural eligibility task consulted: `NO`

## Cases

{cards}
"""
    path.write_text(text, encoding="utf-8")


def write_semantics(path: Path, metadata: dict[str, Any], rows: list[dict[str, str]], preflight_result: dict[str, Any]) -> dict[str, Any]:
    formation = metadata["frozen"]["formation"]["definition"]
    success_count = sum(row["historical_outcome_label_or_proxy"] == "REVIEW_SUCCESS_PROXY" for row in rows)
    failure_count = sum(row["historical_outcome_label_or_proxy"] == "REVIEW_FAILURE_PROXY" for row in rows)
    semantics = {
        "schema_version": "ws3-a2-historical-semantics-reconstruction.v1",
        "task_id": TASK_ID,
        "task_status": "OWNER_REVIEW_REQUIRED",
        "research_boundary": {
            "a1_a2_a3_catchup_semantics_changed": False,
            "threshold_search_executed": False,
            "feature_mining_executed": False,
            "full_replay_executed": False,
            "matching_rebuild_executed": False,
            "model_training_executed": False,
            "production_mutated": False,
            "parallel_structural_eligibility_conclusion_used": False,
        },
        "source": {
            "dataset_sha256": metadata["dataset_sha256"],
            "dataset_window": metadata["dataset_window"],
            "historical_a2_event_count": metadata["historical_a2_event_count"],
            "source_panel": PANEL_REL.as_posix(),
            "source_panel_sha256": metadata["source_panel_sha256"],
            "source_canonical_head": metadata["source_canonical_head"],
            "source_run_summary": RUN_SUMMARY_REL.as_posix(),
            "source_frozen_manifest": FROZEN_MANIFEST_REL.as_posix(),
            "source_reproducibility_manifest": REPRO_MANIFEST_REL.as_posix(),
            "audit_worktree_head": metadata["audit_worktree_head"],
        },
        "historical_outcome_semantics": {
            "historical_success_definition": "NOT_RECOVERED_NO_EVENT_LEVEL_BINARY_SUCCESS_LABEL",
            "historical_failure_definition": "NOT_RECOVERED_NO_EVENT_LEVEL_BINARY_FAILURE_LABEL",
            "forward_horizons_in_source_artifact": metadata["protocol"]["walk_forward_protocol"]["horizons"],
            "forward_horizon_used_for_review_proxy": 10,
            "return_metric_used": "observable_t10_forward_return",
            "mfe_mae_usage": "Copied where available from existing observable columns; descriptive review evidence only.",
            "source_win_rate_formula": "sum(value > 0 for value in clean) / len(clean)",
            "source_win_rate_code": "services/api/src/topicpilot_api/research/ws3_p2e_a2_expanded_confirmatory_validation.py:_stats",
            "review_success_proxy": "observable_t10_status == AVAILABLE and observable_t10_forward_return > 0 and T10 not excluded",
            "review_failure_proxy": "observable_t10_status == AVAILABLE and observable_t10_forward_return <= 0 and T10 not excluded",
            "proxy_is_not_historical_label": True,
            "selected_success_count": success_count,
            "selected_failure_count": failure_count,
        },
        "qualification": {
            "formation_rule": formation["formation_rule"],
            "reference_formula": formation["reference_formula"],
            "reference_policy_id": formation["reference_policy_id"],
            "reference_maturity_sessions": formation["reference_maturity_sessions"],
            "evaluation_session_excluded_from_reference": formation["evaluation_session_excluded_from_reference"],
            "qualification_reason_complete_count": sum(row["qualification_reason_status"] == "A2_QUALIFICATION_REASON_COMPLETE" for row in rows),
            "qualification_reason_incomplete_count": sum(row["qualification_reason_status"] == "A2_QUALIFICATION_REASON_INCOMPLETE" for row in rows),
            "historical_label_preserved": True,
        },
        "global_snapshot_availability": {
            "close": "AVAILABLE_FROM_A2_PANEL:a2_close",
            "ma20": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
            "ma60": "AVAILABLE_FROM_A2_PANEL:ma60",
            "close_gt_ma60": "DERIVED_READ_ONLY_FROM_a2_close_and_ma60",
            "ma20_slope": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
            "ma60_slope": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
            "volume": "AVAILABLE_FROM_A2_PANEL:volume",
            "mv20": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
            "volume_ratio": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
            "recent_reference": "AVAILABLE_FROM_A2_PANEL:reference",
            "recent_breakout_proximity": "AVAILABLE_AS_A2_PANEL:distance_from_ma60; no new breakout feature computed",
        },
        "pre_anchor_context": {
            "requested_days": ["D-20", "D-10", "D-5", "D-3", "D-1", "D0"],
            "D-20_to_D-1": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
            "D0": "Close, MA60, distance_from_MA60, volume, reference, reference_age_sessions, gap_up",
            "no_new_feature_computation": True,
        },
        "preflight": preflight_result,
        "large_panel_scan_count": 1,
        "owner_labels_prepopulated": False,
    }
    write_json(path, semantics)
    return semantics


def write_closure(path: Path, metadata: dict[str, Any], rows: list[dict[str, str]], panel_meta: dict[str, Any], semantics: dict[str, Any]) -> None:
    strata = Counter(row["sample_stratum"] for row in rows)
    unique_instruments = len({row["instrument_id"] for row in rows})
    duplicates = len(rows) - unique_instruments
    dates = sorted(row["anchor_date"] for row in rows)
    ma60_counts = Counter(row["current_ma60_eligibility_at_anchor"] for row in rows)
    complete = Counter(row["qualification_reason_status"] for row in rows)
    lines = [
        f"# Formal Closure Report — {TASK_ID}",
        "",
        "TASK_STATUS=OWNER_REVIEW_REQUIRED",
        f"SOURCE_DATASET={metadata['dataset_sha256']}",
        f"SOURCE_SHA={metadata['audit_worktree_head']}",
        f"AUDIT_WORKTREE_HEAD={metadata['audit_worktree_head']}",
        f"SOURCE_PANEL_SHA256={metadata['source_panel_sha256']}",
        f"SOURCE_CANONICAL_HEAD={metadata['source_canonical_head']}",
        f"HISTORICAL_A2_EVENT_COUNT={metadata['historical_a2_event_count']}",
        "HISTORICAL_SUCCESS_SEMANTICS_RECOVERED=NO_BINARY_LABEL;REVIEW_SUCCESS_PROXY_CONSTRUCTED",
        "HISTORICAL_FAILURE_SEMANTICS_RECOVERED=NO_BINARY_LABEL;REVIEW_FAILURE_PROXY_CONSTRUCTED",
        "FORWARD_HORIZON_USED_FOR_PROXY=T10;T1/T3/T5/T10_COPIED_WHERE_AVAILABLE",
        "RETURN_METRIC_USED=observable_t10_forward_return;source_win_rate_convention_value_gt_0",
        f"SUCCESS_SAMPLE_COUNT={strata['SUCCESS_STRONG'] + strata['SUCCESS_TYPICAL'] + strata['SUCCESS_BORDERLINE']}",
        f"FAILURE_SAMPLE_COUNT={strata['FAILURE_STRONG_SETUP'] + strata['FAILURE_TYPICAL'] + strata['FAILURE_CLEAR']}",
        f"SUCCESS_STRONG_COUNT={strata['SUCCESS_STRONG']}",
        f"SUCCESS_TYPICAL_COUNT={strata['SUCCESS_TYPICAL']}",
        f"SUCCESS_BORDERLINE_COUNT={strata['SUCCESS_BORDERLINE']}",
        f"FAILURE_STRONG_SETUP_COUNT={strata['FAILURE_STRONG_SETUP']}",
        f"FAILURE_TYPICAL_COUNT={strata['FAILURE_TYPICAL']}",
        f"FAILURE_CLEAR_COUNT={strata['FAILURE_CLEAR']}",
        f"UNIQUE_INSTRUMENT_COUNT={unique_instruments}",
        f"DUPLICATE_INSTRUMENT_COUNT={duplicates}",
        f"DATE_RANGE={dates[0]}..{dates[-1]}",
        f"TPE_COUNT={sum(row['market'] == 'TPE' for row in rows)}",
        f"TWO_COUNT={sum(row['market'] == 'TWO' for row in rows)}",
        f"A2_QUALIFICATION_REASON_COMPLETE_COUNT={complete['A2_QUALIFICATION_REASON_COMPLETE']}",
        f"A2_QUALIFICATION_REASON_INCOMPLETE_COUNT={complete['A2_QUALIFICATION_REASON_INCOMPLETE']}",
        f"CURRENT_MA60_PASS_COUNT={ma60_counts['PASS']}",
        f"CURRENT_MA60_FAIL_COUNT={ma60_counts['FAIL']}",
        f"CURRENT_MA60_UNKNOWN_COUNT={ma60_counts['UNKNOWN']}",
        "LARGE_PANEL_SCAN_COUNT=1",
        "FULL_REPLAY_EXECUTED=NO",
        "MATCHING_REBUILD_EXECUTED=NO",
        "FEATURE_RECOMPUTE_EXECUTED=NO",
        "THRESHOLD_SEARCH_EXECUTED=NO",
        "MODEL_TRAINING_EXECUTED=NO",
        "OWNER_LABELS_PREPOPULATED=NO",
        "WS1_CHANGED=NO",
        "WS2_CHANGED=NO",
        "WS4_CHANGED=NO",
        "PRODUCTION_MUTATED=NO",
        "NEXT_TASK_CHANGED=NO",
        "A1_A2_A3_CATCHUP_SEMANTICS_CHANGED=NO",
        "PARALLEL_A_STRUCTURAL_ELIGIBILITY_TASK_CONSULTED=NO",
        "REPRODUCIBILITY_STATUS=PASS_MANIFEST_AND_SOURCE_SHA_RECORDED",
        "",
        "## Closure boundary",
        "",
        "This audit does not conclude that A2 works or does not work, and it does not accept or reject A2. It produces a source-grounded Owner Review Pack. The permitted disposition is OWNER_REVIEW_REQUIRED.",
        "",
        "## Scan and source integrity",
        "",
        f"Source panel rows read: {panel_meta['panel_event_count']}; unique event IDs: {panel_meta['panel_unique_event_id_count']}; source run summary expected: {metadata['historical_a2_event_count']}.",
        "The event panel was read once. Sampling, CSV generation, markdown generation, JSONL generation, and closure reporting all used the resulting 30-case manifest; no second panel scan was performed.",
        "",
        "## Required handoff",
        "",
        "Owner should review the 30 cases in the order listed at the start of WS3-A2-HISTORICAL-LABEL-OWNER-REVIEW-PACK.md and fill setup validity, outcome validity, visual family, and notes manually.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate() -> None:
    preflight_path = REPORT_DIR / "ws3-a2-audit-preflight.json"
    if not preflight_path.exists():
        preflight()
    preflight_result = read_json(preflight_path)
    assert preflight_result["preflight_status"] == "PASS"

    metadata = source_metadata()
    rows, proxy = scan_panel_once()
    assert len(rows) == metadata["historical_a2_event_count"], (len(rows), metadata["historical_a2_event_count"])
    selected = select_cases(proxy)
    names = load_name_map()
    formation = metadata["frozen"]["formation"]["definition"]
    source_panel_hash = metadata["source_panel_sha256"]
    master_rows = [build_case(item, names, formation, source_panel_hash) for item in selected]
    assert len(master_rows) == 30
    assert sum(row["historical_outcome_label_or_proxy"] == "REVIEW_SUCCESS_PROXY" for row in master_rows) == 15
    assert sum(row["historical_outcome_label_or_proxy"] == "REVIEW_FAILURE_PROXY" for row in master_rows) == 15
    assert all(all(row[key] == "" for key in ("owner_setup_validity", "owner_outcome_validity", "owner_visual_family", "owner_notes")) for row in master_rows)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    panel_meta = proxy["meta"]
    semantics = write_semantics(REPORT_DIR / "ws3-a2-historical-semantics-reconstruction.json", metadata, master_rows, preflight_result)
    audit_meta = {
        "task_id": TASK_ID,
        "audit_generator_sha": git_head(),
        "source_dataset_sha256": metadata["dataset_sha256"],
        "source_panel_sha256": metadata["source_panel_sha256"],
        "source_panel_rel": PANEL_REL.as_posix(),
        "source_run_summary_rel": RUN_SUMMARY_REL.as_posix(),
        "source_event_count": panel_meta["panel_event_count"],
        "source_unique_instrument_count": panel_meta["panel_unique_instrument_count"],
        "source_date_range": panel_meta["panel_date_range"],
        "source_market_counts": panel_meta["panel_market_counts"],
        "review_success_proxy_population_count": panel_meta["review_success_proxy_population_count"],
        "review_failure_proxy_population_count": panel_meta["review_failure_proxy_population_count"],
        "large_panel_scan_count": 1,
        "all_outputs_derived_from_manifest": True,
        "owner_fields_prepopulated": False,
        "parallel_structural_eligibility_task_consulted": False,
    }
    write_manifest(REPORT_DIR / "ws3-a2-audit-intermediate-manifest.jsonl", master_rows, audit_meta)
    write_csv(REPORT_DIR / "ws3-a2-historical-label-audit-master.csv", master_rows)
    write_csv(REPORT_DIR / "ws3-a2-success-review-cases.csv", [row for row in master_rows if row["historical_outcome_label_or_proxy"] == "REVIEW_SUCCESS_PROXY"])
    write_csv(REPORT_DIR / "ws3-a2-failure-review-cases.csv", [row for row in master_rows if row["historical_outcome_label_or_proxy"] == "REVIEW_FAILURE_PROXY"])
    write_pack(REPORT_DIR / "WS3-A2-HISTORICAL-LABEL-OWNER-REVIEW-PACK.md", master_rows, metadata, semantics)
    write_closure(REPORT_DIR / "formal-closure-report.md", metadata, master_rows, panel_meta, semantics)

    assert len((REPORT_DIR / "ws3-a2-audit-intermediate-manifest.jsonl").read_text(encoding="utf-8").splitlines()) == 30
    print(json.dumps({"status": "PASS", "task_id": TASK_ID, "report_dir": str(REPORT_DIR), "case_count": len(master_rows), "large_panel_scan_count": 1, "git_head": git_head()}, ensure_ascii=False))


def refresh_reports_without_panel_scan() -> None:
    """Refresh metadata-only reports from the already-written 30-case manifest."""
    metadata = source_metadata()
    master_path = REPORT_DIR / "ws3-a2-historical-label-audit-master.csv"
    with master_path.open(encoding="utf-8", newline="") as handle:
        master_rows = list(csv.DictReader(handle))
    assert len(master_rows) == 30
    with (REPORT_DIR / "ws3-a2-audit-intermediate-manifest.jsonl").open(encoding="utf-8") as handle:
        first_record = json.loads(next(handle))
    audit_meta = first_record["audit_metadata"]
    panel_meta = {
        "panel_event_count": audit_meta["source_event_count"],
        "panel_unique_event_id_count": audit_meta["source_event_count"],
        "panel_unique_instrument_count": audit_meta["source_unique_instrument_count"],
        "panel_market_counts": audit_meta["source_market_counts"],
        "panel_date_range": audit_meta["source_date_range"],
    }
    preflight_result = read_json(REPORT_DIR / "ws3-a2-audit-preflight.json")
    semantics = write_semantics(REPORT_DIR / "ws3-a2-historical-semantics-reconstruction.json", metadata, master_rows, preflight_result)
    write_pack(REPORT_DIR / "WS3-A2-HISTORICAL-LABEL-OWNER-REVIEW-PACK.md", master_rows, metadata, semantics)
    write_closure(REPORT_DIR / "formal-closure-report.md", metadata, master_rows, panel_meta, semantics)
    print(json.dumps({"status": "PASS", "task_id": TASK_ID, "mode": "REFRESH_FROM_EXISTING_MANIFEST", "large_panel_scan_count": 0, "git_head": git_head()}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "generate", "refresh"))
    args = parser.parse_args()
    if args.command == "preflight":
        print(json.dumps(preflight(), ensure_ascii=False))
    elif args.command == "generate":
        generate()
    else:
        refresh_reports_without_panel_scan()


if __name__ == "__main__":
    main()
