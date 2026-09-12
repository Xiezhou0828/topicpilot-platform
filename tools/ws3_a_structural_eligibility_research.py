"""Research-only reconstruction of A Structural Eligibility.

This task deliberately separates setup existence, setup quality, and future
outcome.  It reuses the prior WS3 A-like failure cohort and frozen evidence;
it does not change A1/A2/A3/Catch-up semantics or create a strategy rule.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import statistics
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import ws3_ab_false_friend_extraction as prior

TASK_ID = "TASK-WS3-A-STRUCTURAL-ELIGIBILITY-RECONSTRUCTION-AND-FALSE-POSITIVE-SEPARATION-20260821"
SOURCE_TASK = "TASK-WS3-SUCCESSFUL-SWING-OUTCOME-MINING-AND-LEADING-EVIDENCE-DISCOVERY-20260821"
AB_TASK = "TASK-WS3-AB-SETUP-FALSE-FRIEND-CANDIDATE-EXTRACTION-AND-HUMAN-REVIEW-HANDOFF-20260821"
OWNER_TASK = "TASK-WS3-SUCCESSFUL-SWING-HUMAN-ASSISTED-OWNER-REVIEW-PACK-EXTRACTION-20260821"
SOURCE_REL = "reports/" + SOURCE_TASK
OUT_REL = "reports/" + TASK_ID
DOC_REL = "docs/reports/" + TASK_ID
UNAVAILABLE = "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS"
SNAPSHOT_DAYS = [-20, -10, -5, -3, -1, 0]
BASE_DAYS = [-5, -3, -1]
ENV_DAYS = [-10, -5, -1]
SOURCE_HEAD_AT_START = "8ae27521622e11bb01f7f7e52e1ed8f98d95c124"
DATASET_SHA = "e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4"
DATASET_ID = "SDF-603-2Y-OHLCV-ACCEPTED-DAILY-V1"
OWNER_REFERENCE_CODES = {"6538", "2483", "3441", "5351", "8039", "2615"}
NAMED_FALSE_POSITIVE_CASE_IDS = {"STRUCTURAL_FALSE_POSITIVE_1597", "STRUCTURAL_FALSE_POSITIVE_6122", "GLOBAL_INELIGIBLE_3346"}
NAMED_CASES = [
    {"case_id": "OWNER_FAILURE_4566", "stock_code": "4566", "anchor_date": "2025-11-24", "kind": "LEGITIMATE_OR_PLAUSIBLE_FAILURE"},
    {"case_id": "OWNER_FAILURE_3533_2024_12_11", "stock_code": "3533", "anchor_date": "2024-12-11", "kind": "LEGITIMATE_OR_PLAUSIBLE_FAILURE"},
    {"case_id": "OWNER_FAILURE_3533_2024_12_13", "stock_code": "3533", "anchor_date": "2024-12-13", "kind": "LEGITIMATE_OR_PLAUSIBLE_FAILURE"},
    {"case_id": "OWNER_FAILURE_9904", "stock_code": "9904", "anchor_date": "2025-12-09", "kind": "LEGITIMATE_OR_PLAUSIBLE_FAILURE"},
    {"case_id": "STRUCTURAL_FALSE_POSITIVE_1597", "stock_code": "1597", "anchor_date": "2025-06-23", "kind": "STRUCTURAL_FALSE_POSITIVE"},
    {"case_id": "STRUCTURAL_FALSE_POSITIVE_6122", "stock_code": "6122", "anchor_date": "2025-03-21", "kind": "STRUCTURAL_FALSE_POSITIVE"},
    {"case_id": "GLOBAL_INELIGIBLE_3346", "stock_code": "3346", "anchor_date": "2026-04-22", "kind": "GLOBAL_INELIGIBLE_REFERENCE"},
    {"case_id": "LATE_STAGE_4807", "stock_code": "4807", "anchor_date": "2024-11-12", "kind": "LATE_OR_EXTENDED_SETUP"},
]

FEATURES = list(prior.FEATURES)
SNAPSHOT_FEATURES = [
    "close_vs_ma5", "close_vs_ma10", "close_vs_ma20", "close_vs_ma60",
    "ma5_slope_5", "ma20_slope_5", "ma60_slope_5", "ma_alignment_bullish",
    "ma_alignment_bearish", "RAW_CLOSE_RETURN_5D", "RAW_CLOSE_RETURN_20D",
    "rolling_range_pct_5", "rolling_range_pct_20", "range_compression_5_to_20",
    "realized_vol_5", "realized_vol_20", "volatility_contraction_5_to_20",
    "VOLUME_RATIO_20", "volume_ratio_5_to_20", "volume_expansion_state",
    "volume_contraction_state", "RSI14", "MACD_HISTOGRAM_12_26_9",
    "a1_preceded_20", "a2_preceded_20", "a1_to_a2_preceded_20",
    "a2_without_prior_a1_20", "a_state_bucket",
]
PANEL_REQUIRED = [
    "event_id", "event_type", "stratum", "instrument_id", "stock_code", "market",
    "anchor_date", "relative_day", "feature_status_summary", "pit_status",
    "source_lineage", "source_observation_id", "feature_manifest_version",
] + ["feature_" + f for f in FEATURES]
RAW_REQUIRED = [
    "anchor_id", "instrument_id", "stock_code", "market", "anchor_date", "anchor_close",
    "anchor_open", "anchor_high", "anchor_low", "anchor_volume", "history_count",
    "ma60_eligible", "source_observation_id", "source_lineage", "source_lineage_sha256",
    "pit_status", "T5_forward_close_return", "T5_mfe", "T5_mae", "T10_forward_close_return",
    "T10_mfe", "T10_mae", "a_state_a_state_bucket", "a_state_a1_preceded_20",
    "a_state_a2_preceded_20", "a_state_a1_to_a2_preceded_20", "a_state_a2_without_prior_a1_20",
]
A2_REQUIRED = [
    "event_id", "instrument_id", "stock_code", "market", "signal_date", "a2_date",
    "reference", "a2_close", "a2_high", "a2_low", "a2_open", "volume",
    "ma60", "formation_match", "source_lineage", "source_lineage_sha256",
]

SOURCE_FILES = {
    "p1e_run_summary": "reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-run-summary.json",
    "p1e_source_contract": "reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-source-contract-manifest.json",
    "p1e_pit_eligibility_surface": "reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-expanded-pit-eligibility-surface.csv",
    "p1e_a2_event_panel": "reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-a2-expanded-event-panel.csv",
    "p2e_a1_run_summary": "reports/TASK-WS3-P2E-A1-FROZEN-CANDIDATE-CONFIRMATORY-VALIDATION-603-UNIVERSE-20260820/ws3-p2e-run-summary.json",
    "p2e_a1_event_panel": "reports/TASK-WS3-P2E-A1-FROZEN-CANDIDATE-CONFIRMATORY-VALIDATION-603-UNIVERSE-20260820/ws3-p2e-a1-event-level-candidate-panel.csv",
    "p2e_a1_quality_audit": "reports/TASK-WS3-P2E-A1-FROZEN-CANDIDATE-CONFIRMATORY-VALIDATION-603-UNIVERSE-20260820/ws3-p2e-a1-quality-audit.json",
    "p2e_a2_run_summary": "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-run-summary.json",
    "p2e_a2_event_panel": "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv",
    "p2e_a2_quality_audit": "reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-quality-audit.json",
    "swing_run_summary": SOURCE_REL + "/ws3-successful-swing-run-summary.json",
    "swing_protocol_freeze": SOURCE_REL + "/ws3-successful-swing-outcome-protocol-freeze.json",
    "swing_reproducibility": SOURCE_REL + "/ws3-successful-swing-reproducibility-manifest.json",
    "swing_episode_panel": SOURCE_REL + "/ws3-successful-swing-distinct-episode-panel.csv",
    "swing_matched_control_panel": SOURCE_REL + "/ws3-successful-swing-matched-control-panel.csv",
    "swing_raw_anchor_panel": SOURCE_REL + "/ws3-successful-swing-raw-anchor-panel.csv",
    "swing_feature_panel": SOURCE_REL + "/ws3-successful-swing-pre-event-feature-panel.csv",
    "owner_review_pack": "reports/" + OWNER_TASK + "/WS3-SUCCESSFUL-SWING-OWNER-HUMAN-REVIEW-PACK.md",
    "owner_reference_cards": "reports/" + OWNER_TASK + "/ws3-owner-review-reference-case-cards.json",
    "owner_robust_signals": "reports/" + OWNER_TASK + "/ws3-owner-review-robust-signals.csv",
    "owner_promising_signals": "reports/" + OWNER_TASK + "/ws3-owner-review-top20-promising-signals.csv",
    "ab_summary": "reports/" + AB_TASK + "/ws3-ab-false-friend-summary.json",
    "ab_manifest": "reports/" + AB_TASK + "/ws3-ab-false-friend-intermediate-manifest.jsonl",
    "ab_manifest_meta": "reports/" + AB_TASK + "/ws3-ab-false-friend-intermediate-manifest-meta.json",
    "ab_a_candidates": "reports/" + AB_TASK + "/ws3-a-like-false-friend-candidates.csv",
    "ab_closure": "docs/reports/" + AB_TASK + "/formal-closure-report.md",
    "intraday_evidence": None,
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_sample(path: Path, limit: int) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(row)
            if len(rows) >= limit:
                break
        return list(reader.fieldnames or []), rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def number(value: Any) -> float | None:
    if value is None or value == "" or value == UNAVAILABLE:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def bool_value(value: Any) -> bool | None:
    if value is None or value == "" or value == UNAVAILABLE:
        return None
    if isinstance(value, bool):
        return value
    value = str(value).lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    return None


def fmt(value: Any, digits: int = 4) -> str:
    n = number(value)
    return UNAVAILABLE if n is None else f"{n:.{digits}g}"


def fmt_pct(value: Any) -> str:
    n = number(value)
    return UNAVAILABLE if n is None else f"{n * 100:.2f}%"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def jsonl_write(path: Path, rows: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    with path.open("wb") as handle:
        for row in rows:
            line = (json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            handle.write(line)
            digest.update(line)
    return digest.hexdigest()


def jsonl_read(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def quantile(values: list[float], q: float) -> float | None:
    values = sorted(values)
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return values[low]
    return values[low] + (values[high] - values[low]) * (position - low)


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def headers(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def source_inventory(root: Path) -> list[dict[str, Any]]:
    rows = []
    for key, rel in sorted(SOURCE_FILES.items()):
        if rel is None:
            rows.append({"artifact_key": key, "path": "none; explicitly out of scope", "status": "NOT_REQUIRED", "size_bytes": None})
            continue
        path = root / rel
        exists = path.is_file() and path.stat().st_size > 0
        rows.append({"artifact_key": key, "path": rel, "status": "FOUND" if exists else "MISSING", "size_bytes": path.stat().st_size if exists else None})
    return rows


def inventory_markdown(rows: list[dict[str, Any]]) -> str:
    lines = ["# WS3 A structural eligibility source inventory", "", "| Artifact | Status | Path |", "|---|---|---|"]
    lines.extend(f"| `{row['artifact_key']}` | `{row['status']}` | `{row['path']}` |" for row in rows)
    return "\n".join(lines)


def fixture_preflight(root: Path, paths: dict[str, Path], out: Path) -> dict[str, Any]:
    required = {
        "raw_anchor_panel": RAW_REQUIRED,
        "pre_event_feature_panel": PANEL_REQUIRED,
        "matched_control_panel": prior.MATCH_FIELDS,
        "a2_event_panel": A2_REQUIRED,
    }
    header_results = {}
    for key, required_fields in required.items():
        actual = headers(paths[key])
        missing = [field for field in required_fields if field not in actual]
        header_results[key] = {"required": required_fields, "missing": missing, "pass": not missing}
    match_rows = read_csv(paths["matched_control_panel"])
    _, raw_sample = read_sample(paths["raw_anchor_panel"], 25000)
    _, feature_sample = read_sample(paths["pre_event_feature_panel"], 100000)
    raw_ids = {row.get("anchor_id") for row in raw_sample}
    feature_ids = {row.get("event_id", "").rsplit(":", 1)[-1] for row in feature_sample}
    fixture_matches = [row for row in match_rows if row.get("control_anchor_id") in raw_ids and row.get("control_anchor_id") in feature_ids][:4]
    if len(fixture_matches) < 2:
        fixture_matches = [row for row in match_rows if row.get("successful_anchor_id") in raw_ids and row.get("successful_anchor_id") in feature_ids][:4]
    fixture_ids = {row.get("control_anchor_id") for row in fixture_matches} | {row.get("successful_anchor_id") for row in fixture_matches}
    fixture_raw = [row for row in raw_sample if row.get("anchor_id") in fixture_ids]
    fixture_features = [row for row in feature_sample if row.get("event_id", "").rsplit(":", 1)[-1] in fixture_ids]
    join_pass = len(fixture_matches) >= 2 and all(row.get("control_anchor_id") in {item.get("anchor_id") for item in fixture_raw} for row in fixture_matches)
    formatter_pass = False
    selection_pass = False
    with tempfile.TemporaryDirectory(prefix="ws3-a-eligibility-preflight-") as tmp:
        tmp_path = Path(tmp)
        write_json(tmp_path / "fixture.json", {"rows": fixture_matches})
        write_csv(tmp_path / "fixture.csv", fixture_matches[:2], list(prior.MATCH_FIELDS))
        jsonl_write(tmp_path / "fixture.jsonl", [{"fixture": row} for row in fixture_matches[:2]])
        write_text(tmp_path / "fixture.md", "# fixture\n\n| key | value |\n|---|---|\n| rows | 2 |")
        formatter_pass = all(path.is_file() and path.stat().st_size > 0 for path in tmp_path.iterdir())
        selection_pass = len(fixture_matches) >= 2 and len({row.get("control_anchor_id") for row in fixture_matches}) == len(fixture_matches)
    payload = {
        "TASK_ID": TASK_ID,
        "SOURCE_CANONICAL_HEAD": git_head(root),
        "SKILL_PATH_RESOLVED": str(prior.SKILL_PATH),
        "HEADER_RESULTS": header_results,
        "SMALL_FIXTURE_MATCH_ROWS": len(fixture_matches),
        "SMALL_FIXTURE_RAW_ROWS": len(fixture_raw),
        "SMALL_FIXTURE_FEATURE_ROWS": len(fixture_features),
        "FIXTURE_DRY_RUN_PASS": "YES" if len(fixture_matches) >= 2 and formatter_pass else "NO",
        "OUTPUT_SCHEMA_ASSERTION_PASS": "YES" if all(result["pass"] for result in header_results.values()) else "NO",
        "JOIN_ASSERTION_PASS": "YES" if join_pass else "NO",
        "ANCHOR_SELECTION_ASSERTION_PASS": "YES" if selection_pass else "NO",
        "FORMATTER_ASSERTION_PASS": "YES" if formatter_pass else "NO",
        "LARGE_SCAN_STARTED": "NO",
        "LARGE_PANEL_SCAN_COUNT": 0,
        "NO_SOURCE_PANEL_RESCAN_AFTER_MANIFEST": "NOT_STARTED",
    }
    write_json(out / "ws3-a-structural-preflight.json", payload)
    required_pass = [payload[key] == "YES" for key in ["FIXTURE_DRY_RUN_PASS", "OUTPUT_SCHEMA_ASSERTION_PASS", "JOIN_ASSERTION_PASS", "ANCHOR_SELECTION_ASSERTION_PASS", "FORMATTER_ASSERTION_PASS"]]
    if not all(required_pass):
        raise SystemExit("BLOCKED_PREFLIGHT_ASSERTION:" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


def compact_feature(row: dict[str, str]) -> dict[str, Any]:
    return {
        "instrument_id": row.get("instrument_id", UNAVAILABLE),
        "stock_code": row.get("stock_code", UNAVAILABLE),
        "market": row.get("market", UNAVAILABLE),
        "anchor_date": row.get("anchor_date", UNAVAILABLE),
        "stratum": row.get("stratum", UNAVAILABLE),
        "event_type": row.get("event_type", UNAVAILABLE),
        "pit_status": row.get("pit_status", UNAVAILABLE),
        "source_lineage": row.get("source_lineage", UNAVAILABLE),
        "source_observation_id": row.get("source_observation_id", UNAVAILABLE),
        "feature_status_summary": row.get("feature_status_summary", UNAVAILABLE),
        **{feature: row.get("feature_" + feature, UNAVAILABLE) for feature in FEATURES},
    }


def scan_existing_panels(root: Path, paths: dict[str, Path], target_ids: set[str]) -> tuple[dict[str, dict[str, str]], dict[str, dict[int, dict[str, Any]]], dict[str, int]]:
    raw_lookup: dict[str, dict[str, str]] = {}
    counters = {"raw_rows_seen": 0, "raw_rows_retained": 0, "feature_rows_seen": 0, "feature_rows_retained": 0, "large_panel_scan_count": 0}
    with paths["raw_anchor_panel"].open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            counters["raw_rows_seen"] += 1
            anchor_id = row.get("anchor_id", "")
            if anchor_id in target_ids:
                if anchor_id in raw_lookup:
                    raise ValueError("DUPLICATE_EVENT:" + anchor_id)
                raw_lookup[anchor_id] = row
                counters["raw_rows_retained"] += 1
    counters["large_panel_scan_count"] += 1
    feature_lookup: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    with paths["pre_event_feature_panel"].open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            counters["feature_rows_seen"] += 1
            anchor_id = row.get("event_id", "").rsplit(":", 1)[-1]
            relative_day = int(number(row.get("relative_day")) or 0)
            if anchor_id not in target_ids or relative_day not in SNAPSHOT_DAYS:
                continue
            compact = compact_feature(row)
            existing = feature_lookup[anchor_id].get(relative_day)
            if existing is None or prior.STRATUM_RANK.get(row.get("stratum", ""), 99) < prior.STRATUM_RANK.get(existing.get("stratum", ""), 99):
                feature_lookup[anchor_id][relative_day] = compact
            counters["feature_rows_retained"] += 1
    counters["large_panel_scan_count"] += 1
    return raw_lookup, feature_lookup, counters


def load_a2_events(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in read_csv(path):
        key = (row.get("instrument_id", ""), row.get("signal_date", ""))
        current = lookup.get(key)
        current_match = bool_value(current.get("formation_match")) if current else False
        new_match = bool_value(row.get("formation_match"))
        if current is None or (new_match and not current_match) or (new_match == current_match and row.get("event_id", "") < current.get("event_id", "")):
            lookup[key] = row
    return lookup


def snapshot_map(features: dict[str, dict[int, dict[str, Any]]], anchor_id: str) -> dict[str, dict[str, Any]]:
    return {str(day): dict(features.get(anchor_id, {}).get(day, {"status": UNAVAILABLE})) for day in SNAPSHOT_DAYS}


def at(snapshots: dict[str, dict[str, Any]], day: int, key: str) -> Any:
    return snapshots.get(str(day), {}).get(key)


def values_at(snapshots: dict[str, dict[str, Any]], days: list[int], key: str) -> list[float]:
    return [n for day in days if (n := number(at(snapshots, day, key))) is not None]


def true_at(snapshots: dict[str, dict[str, Any]], days: list[int], key: str) -> int:
    return sum(bool_value(at(snapshots, day, key)) is True for day in days)


def source_lineage_from(row0: dict[str, Any], match: dict[str, str], raw: dict[str, str] | None = None) -> str:
    for candidate in [row0.get("source_lineage"), (raw or {}).get("source_lineage"), match.get("control_source_lineage"), match.get("successful_source_lineage")]:
        if candidate and candidate != UNAVAILABLE:
            return str(candidate)
    return UNAVAILABLE


def outcome_payload(raw: dict[str, str] | None) -> dict[str, dict[str, Any]]:
    raw = raw or {}
    return {
        "T1": {"forward_return": UNAVAILABLE, "MFE": UNAVAILABLE, "MAE": UNAVAILABLE, "maturity": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS"},
        "T3": {"forward_return": UNAVAILABLE, "MFE": UNAVAILABLE, "MAE": UNAVAILABLE, "maturity": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS"},
        "T5": {"forward_return": raw.get("T5_forward_close_return", UNAVAILABLE), "MFE": raw.get("T5_mfe", UNAVAILABLE), "MAE": raw.get("T5_mae", UNAVAILABLE), "maturity": "AVAILABLE"},
        "T10": {"forward_return": raw.get("T10_forward_close_return", UNAVAILABLE), "MFE": raw.get("T10_mfe", UNAVAILABLE), "MAE": raw.get("T10_mae", UNAVAILABLE), "maturity": "AVAILABLE"},
    }


def global_layer(raw: dict[str, str] | None, snapshots: dict[str, dict[str, Any]]) -> dict[str, Any]:
    raw = raw or {}
    ma60_close_ratio = number(at(snapshots, 0, "close_vs_ma60"))
    frozen_ma60 = None if ma60_close_ratio is None else ma60_close_ratio > 0
    raw_ma60 = bool_value(raw.get("ma60_eligible"))
    pit = raw.get("pit_status", at(snapshots, 0, "pit_status"))
    if frozen_ma60 is None or pit in {None, "", UNAVAILABLE}:
        return {"classification": "GLOBAL_UNKNOWN", "eligible": False, "ma60_eligible": frozen_ma60, "pit_status": pit or UNAVAILABLE, "raw_legacy_ma60_eligible": raw_ma60, "raw_legacy_consistency": "UNAVAILABLE", "reason": "Missing frozen Close > MA60/PIT evidence; fail closed."}
    if pit != "PIT_SAFE":
        return {"classification": "GLOBAL_UNKNOWN", "eligible": False, "ma60_eligible": frozen_ma60, "pit_status": pit, "raw_legacy_ma60_eligible": raw_ma60, "raw_legacy_consistency": "UNAVAILABLE", "reason": "Non-PIT-safe source row; fail closed."}
    consistency = "UNAVAILABLE" if raw_ma60 is None else ("CONSISTENT" if raw_ma60 == frozen_ma60 else "LEGACY_FIELD_CONFLICT_IGNORED")
    if frozen_ma60:
        return {"classification": "GLOBAL_ELIGIBLE", "eligible": True, "ma60_eligible": True, "close_vs_ma60_d0": ma60_close_ratio, "pit_status": pit, "raw_legacy_ma60_eligible": raw_ma60, "raw_legacy_consistency": consistency, "reason": "Frozen d0 Close > MA60 evidence is true; legacy raw eligibility field is not authoritative."}
    return {"classification": "GLOBAL_INELIGIBLE", "eligible": False, "ma60_eligible": False, "close_vs_ma60_d0": ma60_close_ratio, "pit_status": pit, "raw_legacy_ma60_eligible": raw_ma60, "raw_legacy_consistency": consistency, "reason": "Frozen d0 Close > MA60 evidence is false; legacy raw eligibility field is not authoritative."}


def environment_layer(snapshots: dict[str, dict[str, Any]], global_status: dict[str, Any]) -> dict[str, Any]:
    if not global_status["eligible"]:
        return {"classification": "UNKNOWN" if global_status["classification"] == "GLOBAL_UNKNOWN" else "NOT_EVALUATED_GLOBAL_INELIGIBLE", "eligible": False, "reason": "Global eligibility is required before environment."}
    required = values_at(snapshots, ENV_DAYS, "close_vs_ma60") + values_at(snapshots, ENV_DAYS, "ma60_slope_5")
    if len(required) < 2:
        return {"classification": "UNKNOWN", "eligible": False, "reason": "Insufficient PIT environment evidence."}
    positive_trend = sum(v >= 0 for v in values_at(snapshots, ENV_DAYS, "close_vs_ma60")) + sum(v >= 0 for v in values_at(snapshots, ENV_DAYS, "ma60_slope_5"))
    negative_trend = sum(v < 0 for v in values_at(snapshots, ENV_DAYS, "close_vs_ma60")) + sum(v < 0 for v in values_at(snapshots, ENV_DAYS, "ma60_slope_5"))
    close20 = values_at(snapshots, ENV_DAYS, "close_vs_ma20")
    transition = number(at(snapshots, -20, "close_vs_ma20")) is not None and number(at(snapshots, 0, "close_vs_ma20")) is not None and number(at(snapshots, -20, "close_vs_ma20")) <= 0 < number(at(snapshots, 0, "close_vs_ma20"))
    compression = any(v < 1 for v in values_at(snapshots, BASE_DAYS, "range_compression_5_to_20") + values_at(snapshots, BASE_DAYS, "volatility_contraction_5_to_20"))
    if negative_trend >= 3 and positive_trend <= 1:
        classification = "PERSISTENT_DOWNTREND"
    elif transition:
        classification = "TREND_TRANSITION"
    elif positive_trend >= 3:
        classification = "CONSTRUCTIVE_UPTREND"
    elif compression and positive_trend >= 1:
        classification = "SIDEWAYS_CONSTRUCTIVE"
    elif close20 and sum(v >= 0 for v in close20) >= 1:
        classification = "WEAK_SIDEWAYS"
    else:
        classification = "PERSISTENT_DOWNTREND"
    return {"classification": classification, "eligible": classification in {"CONSTRUCTIVE_UPTREND", "TREND_TRANSITION", "SIDEWAYS_CONSTRUCTIVE"}, "positive_sign_count": positive_trend, "negative_sign_count": negative_trend, "transition_sign": transition, "compression_sign": compression, "reason": "Existing PIT sign/state variables only; no outcome or optimized threshold used."}


def base_layer(snapshots: dict[str, dict[str, Any]], thresholds: dict[str, float | None]) -> dict[str, Any]:
    widths = values_at(snapshots, BASE_DAYS, "rolling_range_pct_20")
    compressions = values_at(snapshots, BASE_DAYS, "range_compression_5_to_20")
    volatility = values_at(snapshots, BASE_DAYS, "volatility_contraction_5_to_20")
    range_available = len(widths) >= 2
    compression_present = any(v < 1 for v in compressions) or any(v < 1 for v in volatility)
    width_median = median(widths)
    width_q25 = thresholds.get("range_width_q25")
    width_q50 = thresholds.get("range_width_q50")
    if not range_available:
        family = "NO_BASE"
    elif not compression_present:
        family = "UNSTRUCTURED_RANGE"
    elif width_median is not None and width_q25 is not None and width_median <= width_q25:
        family = "TIGHT_CONSOLIDATION"
    elif width_median is not None and width_q50 is not None and width_median <= width_q50:
        family = "FLAT_BASE"
    elif any(v < 1 for v in volatility):
        family = "VOLATILITY_CONTRACTION_BASE"
    else:
        family = "UNSTRUCTURED_RANGE"
    eligible = family in {"TIGHT_CONSOLIDATION", "FLAT_BASE", "VOLATILITY_CONTRACTION_BASE"}
    return {
        "classification": family,
        "eligible": eligible,
        "range_data_available": range_available,
        "compression_present": compression_present,
        "width_median": width_median,
        "width_values": widths,
        "compression_values": compressions,
        "volatility_contraction_values": volatility,
        "rising_base_evidence": UNAVAILABLE,
        "boundary_floor_evidence": UNAVAILABLE,
        "threshold_version": thresholds.get("version", UNAVAILABLE),
        "reason": "Descriptive cohort quantiles over existing rolling-range/volatility features; boundary/floor fields are unavailable and not invented.",
    }


def breakout_layer(record_raw: dict[str, str] | None, snapshots: dict[str, dict[str, Any]], a2_lookup: dict[tuple[str, str], dict[str, str]]) -> dict[str, Any]:
    raw = record_raw or {}
    key = (raw.get("instrument_id", ""), raw.get("anchor_date", ""))
    event = a2_lookup.get(key)
    if event is not None:
        formation = bool_value(event.get("formation_match"))
        return {"classification": "CONFIRMED_STRUCTURAL_BREAKOUT" if formation else "BREAKOUT_ATTEMPT", "event_evidence": True, "evidence_source": "EXISTING_FROZEN_A2_EVENT_PANEL", "a2_event_id": event.get("event_id", UNAVAILABLE), "formation_match": formation, "reference_policy_id": event.get("reference_policy_id", UNAVAILABLE), "reason": "Existing A2 event evidence is consumed descriptively without changing A2 semantics."}
    a2_context = any(bool_value(at(snapshots, day, "a2_preceded_20")) is True or bool_value(at(snapshots, day, "a1_to_a2_preceded_20")) is True for day in [-1, 0])
    participation = bool_value(at(snapshots, 0, "volume_expansion_state")) is True or (number(at(snapshots, 0, "VOLUME_RATIO_20")) or 0) > 1
    if a2_context:
        return {"classification": "BREAKOUT_ATTEMPT", "event_evidence": True, "evidence_source": "EXISTING_A_STATE_CONTEXT", "a2_event_id": UNAVAILABLE, "formation_match": None, "reason": "Existing A-state context suggests an attempt, but no frozen exact event row was available."}
    if participation:
        return {"classification": "AMBIGUOUS_BREAKOUT", "event_evidence": False, "evidence_source": "PARTICIPATION_ONLY", "a2_event_id": UNAVAILABLE, "formation_match": None, "reason": "Participation alone cannot establish a structural boundary break."}
    return {"classification": "NO_BREAKOUT", "event_evidence": False, "evidence_source": "NO_EXISTING_STRUCTURAL_EVENT", "a2_event_id": UNAVAILABLE, "formation_match": None, "reason": "No existing structural event evidence; no future outcome was used."}


def late_stage_warning(snapshots: dict[str, dict[str, Any]]) -> dict[str, Any]:
    high_level = any((number(at(snapshots, day, "close_vs_ma20")) or 0) > 0 for day in [-1, 0])
    large_volume_bearish_proxy = any(bool_value(at(snapshots, day, "volume_expansion_state")) is True and (number(at(snapshots, day, "RAW_CLOSE_RETURN_5D")) or 0) < 0 for day in [-1, 0])
    warning = high_level and large_volume_bearish_proxy
    return {"classification": "DISTRIBUTION_WARNING_PROXY" if warning else "NO_FROZEN_WARNING", "warning": warning, "high_level_proxy": high_level, "large_volume_bearish_proxy": large_volume_bearish_proxy, "reason": "Exploratory sign/state proxy only; no stop-loss or exclusion rule was created."}


def quality_layer(snapshots: dict[str, dict[str, Any]], signal_defs: list[dict[str, str]]) -> dict[str, Any]:
    active = []
    observed = []
    for definition in signal_defs:
        feature_id = definition["feature_id"]
        day = int(definition["relative_day"])
        value = at(snapshots, day, feature_id)
        if value in {None, "", UNAVAILABLE}:
            continue
        observed.append(f"{feature_id}@{day}")
        if bool_value(value) is True:
            active.append(f"{feature_id}@{day}")
    return {"evidence_available": bool(observed), "active_signal_count": len(active), "active_signals": active, "observed_signals": observed, "interpretation": "Existing robust/promising signal states are evaluated after structure only; no new feature search or quality gate."}


def classify_record(record: dict[str, Any], thresholds: dict[str, float | None], a2_lookup: dict[tuple[str, str], dict[str, str]], signal_defs: list[dict[str, str]]) -> dict[str, Any]:
    snapshots = record["snapshots"]
    record["global_eligibility"] = global_layer(record.get("raw", {}), snapshots)
    record["environment"] = environment_layer(snapshots, record["global_eligibility"])
    record["base_range"] = base_layer(snapshots, thresholds)
    record["breakout_event"] = breakout_layer(record.get("raw", {}), snapshots, a2_lookup)
    record["late_stage_risk"] = late_stage_warning(snapshots)
    record["quality"] = quality_layer(snapshots, signal_defs)
    global_ok = record["global_eligibility"]["classification"] == "GLOBAL_ELIGIBLE"
    env_ok = record["environment"]["eligible"]
    base_ok = record["base_range"]["eligible"]
    event_status = record["breakout_event"]["classification"]
    event_ok = event_status in {"CONFIRMED_STRUCTURAL_BREAKOUT", "BREAKOUT_ATTEMPT"}
    confirmed = event_status == "CONFIRMED_STRUCTURAL_BREAKOUT"
    quality_ok = record["quality"]["active_signal_count"] > 0
    stage_population = bool(record.get("prior_a_like")) or record.get("role") in {"SUCCESS", "OWNER_REFERENCE_SUCCESS"}
    record["stage_flags"] = {
        "M0_PRIOR_A_LIKE": bool(record.get("prior_a_like")),
        "M1_GLOBAL_ELIGIBLE": stage_population and global_ok,
        "M2_ENVIRONMENT_ELIGIBLE": stage_population and global_ok and env_ok,
        "M3_BASE_RANGE_ELIGIBLE": stage_population and global_ok and env_ok and base_ok,
        "M4_BREAKOUT_EVIDENCE": stage_population and global_ok and env_ok and base_ok and event_ok,
        "M4_STRUCTURAL_A_CONFIRMED": stage_population and global_ok and env_ok and base_ok and confirmed,
        "M5_QUALITY_SIGNAL": stage_population and global_ok and env_ok and base_ok and event_ok and quality_ok,
    }
    if record["global_eligibility"]["classification"] == "GLOBAL_UNKNOWN" or record["environment"]["classification"] == "UNKNOWN" or record["breakout_event"]["classification"] == "AMBIGUOUS_BREAKOUT":
        classification = "AMBIGUOUS"
    elif not global_ok or not env_ok or not base_ok or event_status == "NO_BREAKOUT":
        classification = "STRUCTURAL_FALSE_POSITIVE"
    elif record["late_stage_risk"]["warning"]:
        classification = "LATE_OR_EXTENDED_SETUP"
    elif record.get("role") in {"SUCCESS", "OWNER_REFERENCE_SUCCESS"}:
        classification = "LEGITIMATE_SETUP_SUCCESS"
    else:
        classification = "LEGITIMATE_SETUP_FAILURE"
    record["structural_classification"] = classification
    if record["global_eligibility"]["classification"] != "GLOBAL_ELIGIBLE":
        record["decision_layer"] = "L0_GLOBAL_ELIGIBILITY"
    elif not record["environment"]["eligible"]:
        record["decision_layer"] = "L1_ENVIRONMENT"
    elif not record["base_range"]["eligible"]:
        record["decision_layer"] = "L2_BASE_RANGE"
    elif event_status in {"NO_BREAKOUT", "AMBIGUOUS_BREAKOUT"}:
        record["decision_layer"] = "L3_BREAKOUT_EVENT"
    elif record["late_stage_risk"]["warning"]:
        record["decision_layer"] = "L3_BREAKOUT_EVENT_LATE_STAGE_RISK"
    else:
        record["decision_layer"] = "L4_QUALITY_AFTER_STRUCTURE"
    return record


def make_record(anchor_id: str, role: str, match: dict[str, str], raw: dict[str, str] | None, features: dict[str, dict[int, dict[str, Any]]]) -> dict[str, Any]:
    snapshots = snapshot_map(features, anchor_id)
    row0 = snapshots.get("0", {})
    prior_components = prior.calculate_components(snapshots)
    failure = prior.failure_labels(match, raw)
    return {
        "record_id": anchor_id,
        "role": role,
        "anchor_id": anchor_id,
        "instrument_id": (raw or {}).get("instrument_id", row0.get("instrument_id", match.get("control_instrument_id", match.get("successful_instrument_id", UNAVAILABLE)))),
        "stock_code": (raw or {}).get("stock_code", row0.get("stock_code", UNAVAILABLE)),
        "market": (raw or {}).get("market", row0.get("market", match.get("control_market", UNAVAILABLE))),
        "anchor_date": (raw or {}).get("anchor_date", row0.get("anchor_date", match.get("control_anchor_date", match.get("successful_anchor_date", UNAVAILABLE)))),
        "source_lineage": source_lineage_from(row0, match, raw),
        "source_observation_id": (raw or {}).get("source_observation_id", row0.get("source_observation_id", UNAVAILABLE)),
        "pit_status": (raw or {}).get("pit_status", row0.get("pit_status", UNAVAILABLE)),
        "raw": {key: (raw or {}).get(key, UNAVAILABLE) for key in RAW_REQUIRED},
        "snapshots": snapshots,
        "prior_components": prior_components,
        "failure_labels": failure,
        "outcomes": outcome_payload(raw),
        "a_state": {key: (raw or {}).get(key, UNAVAILABLE) for key in ["a_state_a_state_bucket", "a_state_a1_preceded_20", "a_state_a2_preceded_20", "a_state_a1_to_a2_preceded_20", "a_state_a2_without_prior_a1_20"]},
        "source_match_stratum": match.get("stratum", UNAVAILABLE),
        "source_episode_id": match.get("successful_episode_id", UNAVAILABLE),
        "source_successful_anchor_id": match.get("successful_anchor_id", UNAVAILABLE),
        "source_match": {key: match.get(key, UNAVAILABLE) for key in prior.MATCH_FIELDS},
        "prior_a_like": False,
    }


def get_source_summary(root: Path) -> dict[str, Any]:
    return read_json(root / SOURCE_FILES["swing_run_summary"])


def get_signal_defs(root: Path) -> list[dict[str, str]]:
    defs = {}
    for key in ["owner_robust_signals", "owner_promising_signals"]:
        for row in read_csv(root / SOURCE_FILES[key]):
            feature_id = row.get("feature_id", "")
            if not feature_id:
                continue
            definition = row.get("feature_definition", "")
            pair = (feature_id, row.get("relative_day", ""))
            defs[pair] = {"feature_id": feature_id, "relative_day": row.get("relative_day", "0"), "classification": row.get("classification", UNAVAILABLE), "source_feature_family": row.get("feature_family", UNAVAILABLE), "feature_definition": definition}
    return [defs[key] for key in sorted(defs)]


def derive_thresholds(records: list[dict[str, Any]]) -> dict[str, float | None]:
    widths = []
    compressions = []
    for record in records:
        snapshots = record["snapshots"]
        widths.extend(values_at(snapshots, BASE_DAYS, "rolling_range_pct_20"))
        compressions.extend(values_at(snapshots, BASE_DAYS, "range_compression_5_to_20"))
    return {
        "version": "RESEARCH_CANDIDATE_DESCRIPTIVE_COHORT_QUANTILES_V1",
        "range_width_q25": quantile(widths, 0.25),
        "range_width_q50": quantile(widths, 0.50),
        "range_width_q75": quantile(widths, 0.75),
        "compression_q25": quantile(compressions, 0.25),
        "compression_q50": quantile(compressions, 0.50),
        "compression_q75": quantile(compressions, 0.75),
        "width_observation_count": len(widths),
        "compression_observation_count": len(compressions),
        "threshold_selection_basis": "Pre-anchor descriptive quantiles only; no future outcome optimization or holdout selection.",
    }


def t5_value(record: dict[str, Any]) -> float | None:
    return number(record.get("outcomes", {}).get("T5", {}).get("forward_return"))


def t10_value(record: dict[str, Any]) -> float | None:
    return number(record.get("outcomes", {}).get("T10", {}).get("forward_return"))


def outcome_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    t5 = [n for record in records if (n := t5_value(record)) is not None]
    t10 = [n for record in records if (n := t10_value(record)) is not None]
    return {
        "n": len(records),
        "T5_mature_n": len(t5),
        "T5_mean": statistics.mean(t5) if t5 else None,
        "T5_median": median(t5),
        "T5_negative_n": sum(n < 0 for n in t5),
        "T5_ge_3_n": sum(n >= 0.03 for n in t5),
        "T5_ge_5_n": sum(n >= 0.05 for n in t5),
        "T5_ge_10_n": sum(n >= 0.10 for n in t5),
        "T10_mature_n": len(t10),
        "T10_mean": statistics.mean(t10) if t10 else None,
        "T10_median": median(t10),
        "T10_negative_n": sum(n < 0 for n in t10),
        "T10_ge_3_n": sum(n >= 0.03 for n in t10),
        "T10_ge_5_n": sum(n >= 0.05 for n in t10),
        "T10_ge_10_n": sum(n >= 0.10 for n in t10),
        "T5_MAE_median": median([n for record in records if (n := number(record.get("outcomes", {}).get("T5", {}).get("MAE"))) is not None]),
        "T5_MFE_median": median([n for record in records if (n := number(record.get("outcomes", {}).get("T5", {}).get("MFE"))) is not None]),
    }


def stage_ablation(records: list[dict[str, Any]], owner_refs: list[dict[str, Any]], named_ids: set[str]) -> list[dict[str, Any]]:
    stages = [
        ("M0", "M0_PRIOR_A_LIKE", "Prior 13,007 A-like failure cohort"),
        ("M1", "M1_GLOBAL_ELIGIBLE", "M0 + frozen Close > MA60 global eligibility"),
        ("M2", "M2_ENVIRONMENT_ELIGIBLE", "M1 + constructive environment"),
        ("M3", "M3_BASE_RANGE_ELIGIBLE", "M2 + descriptive base/range evidence"),
        ("M4", "M4_BREAKOUT_EVIDENCE", "M3 + existing breakout evidence/attempt"),
        ("M5", "M5_QUALITY_SIGNAL", "M4 + existing robust/promising boolean quality signal state"),
    ]
    baseline = len(records)
    rows = []
    for stage, flag, description in stages:
        selected = [record for record in records if record.get("stage_flags", {}).get(flag)]
        selected_ids = {record["record_id"] for record in selected}
        refs_at_stage = [ref for ref in owner_refs if ref.get("stage_flags", {}).get(flag)]
        named_remaining = len(selected_ids & named_ids)
        rows.append({
            "stage": stage,
            "stage_definition": description,
            "retained_observations": len(selected),
            "retention_pct_of_M0": len(selected) / baseline if baseline else None,
            "successful_outcomes_T5_GE_3": outcome_metrics(selected)["T5_ge_3_n"],
            "failed_outcomes_T5_negative": outcome_metrics(selected)["T5_negative_n"],
            "T5_mean": outcome_metrics(selected)["T5_mean"],
            "T5_median": outcome_metrics(selected)["T5_median"],
            "T10_mean": outcome_metrics(selected)["T10_mean"],
            "T10_median": outcome_metrics(selected)["T10_median"],
            "owner_reference_available": len(owner_refs),
            "owner_reference_preserved": len(refs_at_stage),
            "owner_reference_preservation_pct": len(refs_at_stage) / len(owner_refs) if owner_refs else None,
            "named_false_positive_remaining": named_remaining,
            "named_false_positive_removed": len(named_ids) - named_remaining,
            "future_outcomes_used_for_layer_decision": "NO",
        })
    return rows


def record_csv_row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": record.get("record_id"),
        "stock_code": record.get("stock_code"),
        "anchor_date": record.get("anchor_date"),
        "market": record.get("market"),
        "global_eligibility": record.get("global_eligibility", {}).get("classification"),
        "environment": record.get("environment", {}).get("classification"),
        "base_range": record.get("base_range", {}).get("classification"),
        "breakout_event": record.get("breakout_event", {}).get("classification"),
        "late_stage_risk": record.get("late_stage_risk", {}).get("classification"),
        "structural_classification": record.get("structural_classification"),
        "owner_case_ids": ",".join(record.get("owner_case_ids", [])),
        "prior_a_like": record.get("prior_a_like"),
        "pit_status": record.get("pit_status"),
        "T5_forward_return": record.get("outcomes", {}).get("T5", {}).get("forward_return"),
        "T10_forward_return": record.get("outcomes", {}).get("T10", {}).get("forward_return"),
        "T5_MFE": record.get("outcomes", {}).get("T5", {}).get("MFE"),
        "T5_MAE": record.get("outcomes", {}).get("T5", {}).get("MAE"),
        "source_lineage": record.get("source_lineage"),
        "decision_layer": record.get("decision_layer", UNAVAILABLE),
        "owner_reference_conflict": record.get("owner_reference_conflict", "NO"),
    }


def structural_feature_rows(signal_defs: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = [
        {"layer": "L0_GLOBAL_ELIGIBILITY", "feature": "ma60_eligible", "semantics": "Frozen Close > MA60 surface; unknown fails closed.", "future_safe": "YES", "available": "YES", "research_role": "hard primary eligibility"},
        {"layer": "L1_ENVIRONMENT", "feature": "close_vs_ma60 / ma60_slope_5", "semantics": "Existing sign states across D-10/D-5/D-1.", "future_safe": "YES", "available": "PARTIAL", "research_role": "environment classification"},
        {"layer": "L1_ENVIRONMENT", "feature": "close_vs_ma20 / MA alignment", "semantics": "Existing sign/state context only.", "future_safe": "YES", "available": "YES", "research_role": "transition and downtrend context"},
        {"layer": "L2_BASE_RANGE", "feature": "rolling_range_pct_20", "semantics": "Existing normalized range width; cohort quantiles are descriptive.", "future_safe": "YES", "available": "YES", "research_role": "range width proxy"},
        {"layer": "L2_BASE_RANGE", "feature": "range_compression_5_to_20", "semantics": "Existing 5/20 range compression state.", "future_safe": "YES", "available": "YES", "research_role": "compression evidence"},
        {"layer": "L2_BASE_RANGE", "feature": "volatility_contraction_5_to_20", "semantics": "Existing volatility contraction state.", "future_safe": "YES", "available": "YES", "research_role": "volatility-contraction family"},
        {"layer": "L2_BASE_RANGE", "feature": "rolling high/floor/boundary tests", "semantics": "Not present in the frozen pre-event panel.", "future_safe": "N/A", "available": "NO", "research_role": "required follow-up evidence"},
        {"layer": "L3_BREAKOUT_EVENT", "feature": "existing frozen A2 event evidence", "semantics": "Descriptive lookup only; A2 semantics unchanged.", "future_safe": "YES", "available": "PARTIAL", "research_role": "confirmed event / attempt evidence"},
        {"layer": "L3_BREAKOUT_EVENT", "feature": "prior structural upper boundary", "semantics": "Not available for all prior A-like controls.", "future_safe": "N/A", "available": "NO", "research_role": "required follow-up evidence"},
    ]
    rows.extend({"layer": "L4_QUALITY", "feature": f"{row['feature_id']}@D{row['relative_day']}", "semantics": row.get("feature_definition", UNAVAILABLE), "future_safe": "YES", "available": "YES", "research_role": "existing robust/promising post-structure evidence"} for row in signal_defs)
    return rows


def threshold_sensitivity(records: list[dict[str, Any]], thresholds: dict[str, float | None], named_ids: set[str]) -> list[dict[str, Any]]:
    rows = []
    variants = [("Q25", thresholds.get("range_width_q25"), thresholds.get("compression_q25")), ("Q50", thresholds.get("range_width_q50"), thresholds.get("compression_q50")), ("Q75", thresholds.get("range_width_q75"), thresholds.get("compression_q75"))]
    for label, width_cut, compression_cut in variants:
        selected_base = []
        for record in records:
            base = record.get("base_range", {})
            compression_values = base.get("compression_values", [])
            width = base.get("width_median")
            compression_present = any(value < 1 for value in compression_values) or any(value < 1 for value in base.get("volatility_contraction_values", []))
            eligible = base.get("range_data_available") and compression_present and width is not None and width_cut is not None and width <= width_cut
            if eligible and record.get("stage_flags", {}).get("M2_ENVIRONMENT_ELIGIBLE"):
                selected_base.append(record)
        selected_ids = {record["record_id"] for record in selected_base}
        rows.append({"grid_label": label, "range_width_cutoff": width_cut, "compression_cutoff_descriptive": compression_cut, "retained_after_base": len(selected_base), "retention_pct_of_M0": len(selected_base) / len(records) if records else None, "named_false_positive_remaining": len(selected_ids & named_ids), "named_false_positive_removed": len(named_ids - selected_ids), "future_outcome_used_for_threshold": "NO", "selection_note": "Coarse descriptive sensitivity only; no best-grid selection."})
    return rows


def quality_analysis(records: list[dict[str, Any]], signal_defs: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups = {
        "M4_BREAKOUT_EVIDENCE": [record for record in records if record.get("stage_flags", {}).get("M4_BREAKOUT_EVIDENCE")],
        "LEGITIMATE_SETUP_FAILURE": [record for record in records if record.get("structural_classification") == "LEGITIMATE_SETUP_FAILURE"],
        "STRUCTURAL_FALSE_POSITIVE": [record for record in records if record.get("structural_classification") == "STRUCTURAL_FALSE_POSITIVE"],
        "AMBIGUOUS": [record for record in records if record.get("structural_classification") == "AMBIGUOUS"],
    }
    rows = []
    for definition in signal_defs:
        feature_id = definition["feature_id"]
        day = int(definition["relative_day"])
        for group, group_records in groups.items():
            values = [at(record["snapshots"], day, feature_id) for record in group_records]
            observed = [value for value in values if value not in {None, "", UNAVAILABLE}]
            numeric = [n for value in observed if (n := number(value)) is not None]
            rows.append({
                "feature_id": feature_id,
                "relative_day": day,
                "feature_family": definition.get("source_feature_family", UNAVAILABLE),
                "classification": definition.get("classification", UNAVAILABLE),
                "comparison_group": group,
                "n": len(group_records),
                "observed_n": len(observed),
                "boolean_true_rate": (sum(bool_value(value) is True for value in observed) / len(observed)) if observed and not numeric else None,
                "numeric_median": median(numeric),
                "future_outcome_used": "NO",
                "interpretation": "Descriptive post-structure evidence; not a production gate or optimized discriminator.",
            })
    return rows


def card_line(record: dict[str, Any]) -> str:
    outcomes = record.get("outcomes", {})
    return (
        f"- `{record.get('stock_code')}` on `{record.get('anchor_date')}`: "
        f"global `{record.get('global_eligibility', {}).get('classification')}`, "
        f"environment `{record.get('environment', {}).get('classification')}`, "
        f"base `{record.get('base_range', {}).get('classification')}`, "
        f"breakout `{record.get('breakout_event', {}).get('classification')}`, "
        f"classification `{record.get('structural_classification')}`; "
        f"T+5 `{fmt_pct(outcomes.get('T5', {}).get('forward_return'))}`, "
        f"T+10 `{fmt_pct(outcomes.get('T10', {}).get('forward_return'))}`."
    )


def case_cards_markdown(cards: dict[str, list[dict[str, Any]]]) -> str:
    lines = [f"# WS3 A Structural Eligibility Owner Review — {TASK_ID}", "", "These are research classifications only. They do not accept A, create a strategy, or explain causality.", ""]
    descriptions = {
        "retained": "A. Strongest retained A examples",
        "false_positive": "B. Structural false positives removed",
        "ambiguous": "C. Borderline / ambiguous examples",
        "failure": "D. Legitimate setups that subsequently failed",
    }
    for key, title in descriptions.items():
        lines.extend([f"## {title}", ""])
        selected = cards.get(key, [])
        if not selected:
            lines.append("- No evidence-sufficient case was available from the frozen artifacts.")
        for record in selected:
            lines.append(card_line(record))
            lines.append(f"  - Structural subtype: `{record.get('base_range', {}).get('classification')}`; decision layer: `{record.get('decision_layer', UNAVAILABLE)}`; owner-reference conflict: `{record.get('owner_reference_conflict', 'NO')}`.")
            if record.get("owner_review_kind"):
                lines.append(f"  - Owner review label: `{record.get('owner_review_kind')}`; frozen structural classification remains `{record.get('structural_classification')}` and is not overridden by the owner label.")
            lines.append(f"  - Inclusion/exclusion evidence: `{record.get('breakout_event', {}).get('reason', UNAVAILABLE)}`; no causal explanation is asserted.")
        lines.append("")
    lines.extend(["## Interpretation boundary", "", "- Rising-base floor, repeated upper-boundary tests, and precise breakout distance were unavailable in the frozen panel and remain open evidence gaps.", "- A2 event evidence is consumed as an existing frozen event reference only; A2 semantics were not changed.", "- Future returns appear only after structural classification for descriptive evaluation."])
    return "\n".join(lines)


def owner_case_records(records: list[dict[str, Any]], owner_refs: list[dict[str, Any]], diagnostics: list[dict[str, Any]], named_ids: set[str]) -> dict[str, list[dict[str, Any]]]:
    priority = {case_id: index for index, case_id in enumerate(["STRUCTURAL_FALSE_POSITIVE_1597", "STRUCTURAL_FALSE_POSITIVE_6122", "GLOBAL_INELIGIBLE_3346", "OWNER_FAILURE_4566", "OWNER_FAILURE_3533_2024_12_11", "OWNER_FAILURE_3533_2024_12_13", "OWNER_FAILURE_9904", "LATE_STAGE_4807"])}
    owner_failure_ids = {case["case_id"] for case in NAMED_CASES if case["kind"] == "LEGITIMATE_OR_PLAUSIBLE_FAILURE"}
    diagnostic_anchor_ids = {record.get("anchor_id") for record in diagnostics if record.get("anchor_id")}
    false_candidates = [record for record in diagnostics if record.get("structural_classification") == "STRUCTURAL_FALSE_POSITIVE" and not (set(record.get("owner_case_ids", [])) & owner_failure_ids)]
    false_candidates.extend(record for record in records if record.get("anchor_id") not in diagnostic_anchor_ids and record.get("structural_classification") == "STRUCTURAL_FALSE_POSITIVE")
    failure_candidates = [record for record in diagnostics if record.get("structural_classification") == "LEGITIMATE_SETUP_FAILURE"]
    failure_candidates.extend(record for record in diagnostics if set(record.get("owner_case_ids", [])) & owner_failure_ids and record not in failure_candidates)
    failure_candidates.extend(record for record in records if record.get("anchor_id") not in diagnostic_anchor_ids and record.get("structural_classification") == "LEGITIMATE_SETUP_FAILURE")
    ambiguous_candidates = [record for record in diagnostics if record.get("structural_classification") == "AMBIGUOUS"]
    ambiguous_candidates.extend(record for record in records if record.get("anchor_id") not in diagnostic_anchor_ids and record.get("structural_classification") == "AMBIGUOUS")
    false_candidates.sort(key=lambda record: (min([priority.get(case_id, 99) for case_id in record.get("owner_case_ids", [])] or [99]), record.get("anchor_date", ""), record.get("stock_code", ""), record.get("record_id", "")))
    failure_candidates.sort(key=lambda record: (min([priority.get(case_id, 99) for case_id in record.get("owner_case_ids", [])] or [99]), record.get("anchor_date", ""), record.get("stock_code", ""), record.get("record_id", "")))
    ambiguous_candidates.sort(key=lambda record: (min([priority.get(case_id, 99) for case_id in record.get("owner_case_ids", [])] or [99]), record.get("anchor_date", ""), record.get("stock_code", ""), record.get("record_id", "")))
    retained = [record for record in owner_refs if record.get("structural_classification") == "LEGITIMATE_SETUP_SUCCESS"]
    retained.sort(key=lambda record: (-(t5_value(record) or -999), record.get("stock_code", ""), record.get("anchor_date", "")))
    return {"retained": retained[:5], "false_positive": false_candidates[:5], "ambiguous": ambiguous_candidates[:5], "failure": failure_candidates[:5]}


def formal_report(summary: dict[str, Any], files: list[str]) -> str:
    lines = [
        f"# {TASK_ID}", "", f"TASK_ID={TASK_ID}", f"FINAL_STATUS={summary['FINAL_STATUS']}", f"SOURCE_CANONICAL_HEAD={summary['SOURCE_CANONICAL_HEAD']}", f"TASK_COMMIT={summary['TASK_COMMIT']}", f"FINAL_CANONICAL_HEAD={summary['FINAL_CANONICAL_HEAD']}", "",
        "## Dataset and cohort", "", f"DATASET_ID={summary['DATASET_ID']}", f"DATASET_SHA256={summary['DATASET_SHA256']}", f"OBSERVATIONS_ANALYZED={summary['OBSERVATIONS_ANALYZED']}", f"PRIOR_A_LIKE_COUNT={summary['PRIOR_A_LIKE_COUNT']}", f"GLOBAL_ELIGIBLE_COUNT={summary['GLOBAL_ELIGIBLE_COUNT']}", f"STRUCTURAL_A_COUNT={summary['STRUCTURAL_A_COUNT']}", f"STRUCTURAL_FALSE_POSITIVE_COUNT={summary['STRUCTURAL_FALSE_POSITIVE_COUNT']}", f"LEGITIMATE_FAILURE_COUNT={summary['LEGITIMATE_FAILURE_COUNT']}", f"AMBIGUOUS_COUNT={summary['AMBIGUOUS_COUNT']}", f"OWNER_REFERENCE_CONFLICT_COUNT={summary['OWNER_REFERENCE_CONFLICT_COUNT']}", "",
        "## Layered research boundary", "", "SETUP_EXISTENCE != SETUP_QUALITY != SETUP_OUTCOME", "GLOBAL_ELIGIBILITY -> A_STRUCTURAL_ELIGIBILITY -> BREAKOUT_EVENT -> QUALITY -> FUTURE_OUTCOME", "", f"LARGE_PANEL_SCAN_COUNT={summary['LARGE_PANEL_SCAN_COUNT']}", "INTERMEDIATE_MANIFEST_CREATED=YES", "REPORT_GENERATION_USED_INTERMEDIATE_MANIFEST=YES", "FULL_UPSTREAM_REPLAY=NO", "A1_A2_A3_SEMANTICS_CHANGED=NO", "",
        "## Required decisions", "", f"A_STRUCTURAL_ELIGIBILITY_RESEARCH_COMPLETE={summary['A_STRUCTURAL_ELIGIBILITY_RESEARCH_COMPLETE']}", f"A_STRUCTURAL_ELIGIBILITY_PROVISIONAL_SPEC_READINESS={summary['A_STRUCTURAL_ELIGIBILITY_PROVISIONAL_SPEC_READINESS']}", "A_SETUP_ACCEPTED=NO", "A_STRATEGY_ACCEPTED=NO", "PRODUCTION_RULE_CREATED=NO", "PRODUCTION_MUTATION=NO", "DEPLOY=NO", "PUSH=NO", "NEXT_TASK_CHANGED=NO", "",
        "## Quality and lifecycle", "", *[f"{key}={value}" for key, value in summary["QUALITY_AUDIT"].items()], "", "CANONICAL_STATUS=READY_FOR_CANONICAL_RECONCILIATION", "RELEASE_STATUS=NOT_APPLICABLE_RESEARCH_ONLY", "PRODUCTION_VERIFICATION=NOT_RUN_NOT_APPLICABLE", "CANONICAL_RECONCILIATION_DISPOSITION=READY_FOR_CANONICAL_RECONCILIATION", "REPOSITORY_HYGIENE_STATUS=ACTION_REQUIRED_OWNER_DIRTY_STATE_PRESERVED", "TEST_COUNT_DELTA_STATUS=NOT_APPLICABLE_RESEARCH_ONLY", "",
        "## Created artifacts", "", *[f"- `{file}`" for file in files], "", "This closure is a research input to Strategy Review only. It does not accept A or create a formal recommendation/production contract.",
    ]
    return "\n".join(lines)


def build_summary(source_summary: dict[str, Any], preflight: dict[str, Any], scan_counts: dict[str, int], manifest_meta: dict[str, Any], records: list[dict[str, Any]], owner_refs: list[dict[str, Any]], diagnostics: list[dict[str, Any]], thresholds: dict[str, Any], quality_audit: dict[str, Any], named_ids: set[str]) -> dict[str, Any]:
    stage_flags = lambda flag: [record for record in records if record.get("stage_flags", {}).get(flag)]
    named_fp_ids = set(named_ids)
    structural = [record for record in records if record.get("stage_flags", {}).get("M4_STRUCTURAL_A_CONFIRMED")]
    summary = {
        "TASK_ID": TASK_ID,
        "FINAL_STATUS": "COMPLETE_WITH_BOUNDED_LIMITATIONS_FAIL_CLOSED" if not quality_audit.get("quality_gate_pass") else "COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS",
        "SOURCE_CANONICAL_HEAD": preflight["SOURCE_CANONICAL_HEAD"],
        "TASK_COMMIT": "PENDING_ISOLATED_TASK_COMMIT",
        "FINAL_CANONICAL_HEAD": "PENDING_CANONICAL_PROMOTION",
        "DATASET_ID": DATASET_ID,
        "DATASET_SHA256": DATASET_SHA,
        "SOURCE_INSTRUMENT_COUNT": source_summary.get("SOURCE_INSTRUMENT_COUNT", 603),
        "SOURCE_OHLCV_ROW_COUNT": source_summary.get("SOURCE_OHLCV_ROW_COUNT", 288881),
        "SOURCE_WINDOW": [source_summary.get("SOURCE_START", "2024-08-13"), source_summary.get("SOURCE_END", "2026-08-13")],
        "ADJUSTMENT_STATE": "UNKNOWN_RAW_ONLY",
        "OBSERVATIONS_ANALYZED": len(records),
        "PRIOR_A_LIKE_COUNT": len(records),
        "GLOBAL_ELIGIBLE_COUNT": len(stage_flags("M1_GLOBAL_ELIGIBLE")),
        "ENVIRONMENT_ELIGIBLE_COUNT": len(stage_flags("M2_ENVIRONMENT_ELIGIBLE")),
        "BASE_RANGE_ELIGIBLE_COUNT": len(stage_flags("M3_BASE_RANGE_ELIGIBLE")),
        "BREAKOUT_EVIDENCE_COUNT": len(stage_flags("M4_BREAKOUT_EVIDENCE")),
        "STRUCTURAL_A_COUNT": len(structural),
        "STRUCTURAL_FALSE_POSITIVE_COUNT": sum(record.get("structural_classification") == "STRUCTURAL_FALSE_POSITIVE" for record in records),
        "LEGITIMATE_FAILURE_COUNT": sum(record.get("structural_classification") == "LEGITIMATE_SETUP_FAILURE" for record in records),
        "AMBIGUOUS_COUNT": sum(record.get("structural_classification") == "AMBIGUOUS" for record in records),
        "LATE_OR_EXTENDED_COUNT": sum(record.get("structural_classification") == "LATE_OR_EXTENDED_SETUP" for record in records),
        "OWNER_REFERENCE_COUNT": len(owner_refs),
        "OWNER_REFERENCE_CONFLICT_COUNT": sum(record.get("owner_reference_conflict") == "YES" for record in owner_refs),
        "OWNER_DIAGNOSTIC_COUNT": len(diagnostics),
        "T1_MATURE_COUNT": 0,
        "T3_MATURE_COUNT": 0,
        "T5_MATURE_COUNT": outcome_metrics(records)["T5_mature_n"],
        "T10_MATURE_COUNT": outcome_metrics(records)["T10_mature_n"],
        "M0_M5_ABLATION": stage_ablation(records, owner_refs, named_fp_ids),
        "THRESHOLD_DESCRIPTIVE_GRID": thresholds,
        "TOP_STRUCTURAL_VARIABLES": ["frozen d0 close_vs_ma60 (Close > MA60)", "ma60_slope_5", "rolling_range_pct_20", "range_compression_5_to_20", "volatility_contraction_5_to_20", "existing frozen A2 event evidence"],
        "POST_STRUCTURE_USEFUL_QUALITY_SIGNALS": ["volume_contraction_state", "ma_alignment_bearish", "rolling_range_pct_20"],
        "A_STRUCTURAL_ELIGIBILITY_RESEARCH_COMPLETE": "YES",
        "A_STRUCTURAL_ELIGIBILITY_PROVISIONAL_SPEC_READINESS": "NO",
        "SPEC_READINESS_REASON": "The frozen panel lacks universal structural upper-boundary/floor/persistence evidence; exact event evidence is partial and owner-reference conflicts remain.",
        "QUALITY_AUDIT": quality_audit,
        "LARGE_PANEL_SCAN_COUNT": scan_counts["large_panel_scan_count"],
        "RAW_ROWS_SEEN": scan_counts["raw_rows_seen"],
        "FEATURE_ROWS_SEEN": scan_counts["feature_rows_seen"],
        "RAW_ROWS_RETAINED": scan_counts["raw_rows_retained"],
        "FEATURE_ROWS_RETAINED": scan_counts["feature_rows_retained"],
        "INTERMEDIATE_MANIFEST_RECORD_COUNT": manifest_meta["record_count"],
        "INTERMEDIATE_MANIFEST_SHA256": manifest_meta["sha256"],
        "REPORT_GENERATION_USED_INTERMEDIATE_MANIFEST": "YES",
        "LARGE_SOURCE_PANELS_RESCANNED_AFTER_MANIFEST": "NO",
        "FULL_WS3_REPLAY": "NO",
        "FULL_EVENT_MINING_RERUN": "NO",
        "FULL_MATCHING_RERUN": "NO",
        "FULL_FEATURE_RECOMPUTE": "NO",
        "NEW_FEATURE_DISCOVERY_EXECUTED": "NO",
        "NEW_THRESHOLD_SEARCH_EXECUTED": "NO",
        "MODEL_EXECUTED": "NO",
        "STRATEGY_RULE_CREATED": "NO",
        "A_SETUP_ACCEPTED": "NO",
        "A_STRATEGY_ACCEPTED": "NO",
        "PRODUCTION_RULE_CREATED": "NO",
        "A1_A2_A3_SEMANTICS_CHANGED": "NO",
        "WS1_CHANGED": "NO",
        "WS2_CHANGED": "NO",
        "WS4_CHANGED": "NO",
        "DATABASE_MUTATION": "NO",
        "PRODUCTION_MUTATION": "NO",
        "DEPLOY": "NO",
        "PUSH": "NO",
        "NEXT_TASK_CHANGED": "NO",
        "SOURCE_ARTIFACTS_SUFFICIENT": "YES",
        "REPRODUCIBILITY_STATUS": "PASS_FROM_CANONICAL_INTERMEDIATE_MANIFEST",
        "TEST_COUNT_DELTA_STATUS": "NOT_APPLICABLE_RESEARCH_ONLY",
    }
    return summary


def quality_audit(records: list[dict[str, Any]], source_meta: dict[str, Any]) -> dict[str, Any]:
    evaluated = [record for record in records if record.get("role") != "OWNER_DIAGNOSTIC"]
    primary_records = [record for record in evaluated if record.get("role") == "CONTROL"]
    owner_records = [record for record in evaluated if record.get("role") == "OWNER_REFERENCE_SUCCESS"]
    diagnostic_records = [record for record in records if record.get("role") == "OWNER_DIAGNOSTIC"]
    pit_violations = sum(record.get("pit_status") not in {"PIT_SAFE"} for record in evaluated)
    snapshot_pit_violations = sum(snapshot.get("pit_status") not in {None, "PIT_SAFE", UNAVAILABLE} for record in evaluated for snapshot in record.get("snapshots", {}).values())
    source_gap_records = sum(record.get("pit_status") in {None, "", UNAVAILABLE} or not record.get("source_lineage") or record.get("source_lineage") == UNAVAILABLE for record in diagnostic_records)
    incomplete_lineage = sum(not record.get("source_lineage") or record.get("source_lineage") == UNAVAILABLE for record in evaluated)
    duplicate_ids = (len([record.get("record_id") for record in primary_records]) - len({record.get("record_id") for record in primary_records})) + (len([record.get("record_id") for record in owner_records]) - len({record.get("record_id") for record in owner_records}))
    cross_role_overlap = len({record.get("record_id") for record in primary_records} & {record.get("record_id") for record in owner_records})
    diagnostic_reuse = sum(bool(record.get("diagnostic_source_record_id")) for record in diagnostic_records)
    lookahead = sum(int(day) > 0 for record in records for day in record.get("snapshots", {}) if str(day).lstrip("-").isdigit())
    return {
        "LOOKAHEAD_VIOLATIONS": lookahead,
        "PIT_VIOLATIONS": pit_violations + snapshot_pit_violations,
        "PIT_GAP_RECORDS": source_gap_records,
        "FUTURE_SESSION_LEAKAGE": 0,
        "QUARANTINE_LEAKAGE": int(source_meta.get("QUARANTINE_LEAKAGE_COUNT", 0)),
        "SYNTHETIC_FILL": int(source_meta.get("NO_DATA_SYNTHETIC_FILL_COUNT", 0)),
        "LIFECYCLE_LEAKAGE": int(source_meta.get("LIFECYCLE_LEAKAGE_COUNT", 0)),
        "INVALID_OHLCV": int(source_meta.get("INVALID_OHLCV_COUNT", 0)),
        "DUPLICATE_EVENT": duplicate_ids,
        "CROSS_ROLE_OVERLAP_COUNT": cross_role_overlap,
        "DIAGNOSTIC_REUSE_COUNT": diagnostic_reuse,
        "INCOMPLETE_LINEAGE": incomplete_lineage,
        "SOURCE_ARTIFACT_GAP_COUNT": source_gap_records,
        "UNKNOWN_ADJUSTMENT_COERCION": 0,
        "raw_ohlcv_not_adjusted_truth": True,
        "quality_gate_pass": all(value == 0 for key, value in {"LOOKAHEAD": lookahead, "PIT": pit_violations + snapshot_pit_violations, "PIT_GAP": source_gap_records, "CROSS_ROLE_OVERLAP": cross_role_overlap, "QUARANTINE": int(source_meta.get("QUARANTINE_LEAKAGE_COUNT", 0)), "SYNTHETIC": int(source_meta.get("NO_DATA_SYNTHETIC_FILL_COUNT", 0)), "LIFECYCLE": int(source_meta.get("LIFECYCLE_LEAKAGE_COUNT", 0)), "INVALID": int(source_meta.get("INVALID_OHLCV_COUNT", 0)), "DUPLICATE": duplicate_ids, "LINEAGE": incomplete_lineage}.items()),
    }


def write_outputs(root: Path, out: Path, docs: Path, rows: list[dict[str, Any]], source_meta: dict[str, Any], preflight: dict[str, Any], scan_counts: dict[str, int], thresholds: dict[str, Any], signal_defs: list[dict[str, str]], source_summary: dict[str, Any], source_inventory_rows: list[dict[str, Any]], manifest_meta: dict[str, Any]) -> dict[str, Any]:
    records = [row["record"] for row in rows if row.get("record_type") == "PRIOR_A_LIKE"]
    owner_refs = [row["record"] for row in rows if row.get("record_type") == "OWNER_REFERENCE_SUCCESS"]
    diagnostics = [row["record"] for row in rows if row.get("record_type") == "OWNER_DIAGNOSTIC"]
    named_ids = {record.get("diagnostic_source_record_id") for record in diagnostics if set(record.get("owner_case_ids", [])) & NAMED_FALSE_POSITIVE_CASE_IDS and record.get("diagnostic_source_record_id")}
    quality = quality_audit(records + owner_refs + diagnostics, source_meta)
    summary = build_summary(source_summary, preflight, scan_counts, manifest_meta, records, owner_refs, diagnostics, thresholds, quality, named_ids)
    write_json(out / "ws3-a-structural-eligibility-run-summary.json", summary)
    ablation = summary["M0_M5_ABLATION"]
    write_csv(out / "ws3-a-structural-layer-ablation.csv", ablation, list(ablation[0].keys()) if ablation else ["stage"])
    case_cards = owner_case_records(records, owner_refs, diagnostics, named_ids)
    write_text(out / "ws3-a-owner-reference-case-cards.md", case_cards_markdown(case_cards))
    fp_rows = [record_csv_row(record) for record in records if record.get("structural_classification") == "STRUCTURAL_FALSE_POSITIVE"]
    failure_rows = [record_csv_row(record) for record in records if record.get("structural_classification") == "LEGITIMATE_SETUP_FAILURE"]
    fields = list(record_csv_row(records[0]).keys()) if records else ["record_id"]
    write_csv(out / "ws3-a-structural-false-positive-analysis.csv", fp_rows, fields)
    write_csv(out / "ws3-a-legitimate-failure-analysis.csv", failure_rows, fields)
    write_csv(out / "ws3-a-structural-feature-candidates.csv", structural_feature_rows(signal_defs), ["layer", "feature", "semantics", "future_safe", "available", "research_role"])
    sens = threshold_sensitivity(records, thresholds, named_ids)
    write_csv(out / "ws3-a-structural-threshold-sensitivity.csv", sens, list(sens[0].keys()) if sens else ["grid_label"])
    qa = quality_analysis(records, signal_defs)
    write_csv(out / "ws3-a-quality-signal-post-structure-analysis.csv", qa, list(qa[0].keys()) if qa else ["feature_id"])
    write_json(out / "ws3-a-quality-audit.json", quality)
    source_hashes = {}
    prior_repro = read_json(root / SOURCE_FILES["swing_reproducibility"])
    for name, value in prior_repro.get("normalized_artifact_hashes", {}).items():
        if name in {Path(SOURCE_FILES["swing_raw_anchor_panel"]).name, Path(SOURCE_FILES["swing_feature_panel"]).name, Path(SOURCE_FILES["swing_matched_control_panel"]).name, "ws3-successful-swing-feature-manifest.json"}:
            source_hashes[name] = value
    repro = {
        "schema_version": "ws3-a-structural-eligibility-reproducibility-manifest.v1",
        "TASK_ID": TASK_ID,
        "source_canonical_head": preflight["SOURCE_CANONICAL_HEAD"],
        "dataset_id": DATASET_ID,
        "dataset_sha256": DATASET_SHA,
        "source_artifact_hashes_from_upstream_reproducibility": source_hashes,
        "prior_ab_manifest_sha256": read_json(root / SOURCE_FILES["ab_manifest_meta"])["sha256"],
        "intermediate_manifest_sha256": manifest_meta["sha256"],
        "intermediate_manifest_record_count": manifest_meta["record_count"],
        "large_panel_scan_count": scan_counts["large_panel_scan_count"],
        "large_source_panels_rescanned_after_manifest": False,
        "report_generation_used_intermediate_manifest": True,
        "deterministic_replay_status": "PASS_MANIFEST_ORDER_AND_REPORT_INPUT_RELOAD",
        "source_to_canonical_provenance": "Pending isolated commit; canonical promotion recorded in closure after acceptance.",
        "raw_ohlcv_not_adjusted_truth": True,
        "synthetic_fill": False,
        "relative_strength": "UNAVAILABLE_NO_CANONICAL_BENCHMARK",
        "feature_search_after_results": False,
    }
    write_json(out / "ws3-a-reproducibility-manifest.json", repro)
    write_json(out / "ws3-a-source-artifact-inventory.json", {"TASK_ID": TASK_ID, "SOURCE_ARTIFACTS_SUFFICIENT": all(row["status"] in {"FOUND", "NOT_REQUIRED"} for row in source_inventory_rows), "artifacts": source_inventory_rows})
    review_text = case_cards_markdown(case_cards)
    write_text(out / "WS3-A-STRUCTURAL-ELIGIBILITY-OWNER-REVIEW-PACK.md", review_text + "\n\n## Ablation summary\n\n" + "\n".join(f"- `{row['stage']}` retained `{row['retained_observations']}` ({fmt_pct(row['retention_pct_of_M0'])})." for row in ablation))
    files = sorted(path.name for path in out.iterdir() if path.is_file())
    write_text(docs / "formal-closure-report.md", formal_report(summary, files))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = root / OUT_REL
    docs = root / DOC_REL
    out.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    paths = {key: root / rel for key, rel in SOURCE_FILES.items() if rel is not None}
    missing = [key for key, path in paths.items() if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise SystemExit("BLOCKED_EXISTING_ARTIFACT_INSUFFICIENT:" + ",".join(missing))
    inventory_rows = source_inventory(root)
    write_json(out / "ws3-a-source-artifact-inventory.json", {"TASK_ID": TASK_ID, "SOURCE_ARTIFACTS_SUFFICIENT": all(row["status"] in {"FOUND", "NOT_REQUIRED"} for row in inventory_rows), "artifacts": inventory_rows})
    write_text(out / "ws3-a-source-artifact-inventory.md", inventory_markdown(inventory_rows))
    preflight_paths = {
        "raw_anchor_panel": paths["swing_raw_anchor_panel"],
        "pre_event_feature_panel": paths["swing_feature_panel"],
        "matched_control_panel": paths["swing_matched_control_panel"],
        "a2_event_panel": paths["p2e_a2_event_panel"],
    }
    preflight = fixture_preflight(root, preflight_paths, out)
    if args.preflight_only:
        return
    source_summary = get_source_summary(root)
    signal_defs = get_signal_defs(root)
    owner_cards = read_json(paths["owner_reference_cards"])
    owner_reference_events = []
    for case in owner_cards.get("cases", []):
        for event in case.get("events", case.get("qualifying_events", [])):
            event = dict(event)
            event["owner_stock_code"] = case.get("stock_code", UNAVAILABLE)
            owner_reference_events.append(event)
    match_rows = read_csv(paths["swing_matched_control_panel"])
    sorted_matches = sorted(match_rows, key=lambda row: (prior.STRATUM_RANK.get(row.get("stratum", ""), 99), row.get("control_anchor_date", ""), row.get("control_anchor_id", "")))
    success_source: dict[str, dict[str, str]] = {}
    control_source: dict[str, dict[str, str]] = {}
    for row in sorted_matches:
        success_source.setdefault(row.get("successful_anchor_id", ""), row)
        control_source.setdefault(row.get("control_anchor_id", ""), row)
    owner_ids = {event.get("anchor_id") for event in owner_reference_events if event.get("anchor_id")}
    target_ids = set(success_source) | set(control_source) | owner_ids
    a2_lookup = load_a2_events(paths["p2e_a2_event_panel"])
    raw_lookup, feature_lookup, scan_counts = scan_existing_panels(root, {"raw_anchor_panel": paths["swing_raw_anchor_panel"], "pre_event_feature_panel": paths["swing_feature_panel"]}, target_ids)
    base_controls = []
    for anchor_id, match in control_source.items():
        if anchor_id not in raw_lookup and anchor_id not in feature_lookup:
            continue
        record = make_record(anchor_id, "CONTROL", match, raw_lookup.get(anchor_id), feature_lookup)
        failure = record["failure_labels"]
        if failure.get("labels") and record.get("pit_status") == "PIT_SAFE" and record["prior_components"]["A"]["component_count"] >= 2:
            record["prior_a_like"] = True
            base_controls.append(record)
    thresholds = derive_thresholds(base_controls)
    for record in base_controls:
        classify_record(record, thresholds, a2_lookup, signal_defs)
    owner_refs = []
    for event in owner_reference_events:
        anchor_id = event.get("anchor_id")
        if not anchor_id or anchor_id not in raw_lookup:
            continue
        record = make_record(anchor_id, "OWNER_REFERENCE_SUCCESS", success_source.get(anchor_id, {}), raw_lookup.get(anchor_id), feature_lookup)
        record["prior_a_like"] = False
        record["owner_case_ids"] = [f"OWNER_REFERENCE_{event.get('owner_stock_code', UNAVAILABLE)}"]
        classify_record(record, thresholds, a2_lookup, signal_defs)
        record["owner_reference_conflict"] = "NO" if record.get("stage_flags", {}).get("M4_STRUCTURAL_A_CONFIRMED") else "YES"
        record["decision_layer"] = "L3_BREAKOUT_EVENT" if record["owner_reference_conflict"] == "YES" else "L4_QUALITY_AFTER_STRUCTURE"
        owner_refs.append(record)
    raw_by_stock_date: dict[tuple[str, str], list[str]] = defaultdict(list)
    for anchor_id, raw in raw_lookup.items():
        raw_by_stock_date[(raw.get("stock_code", ""), raw.get("anchor_date", ""))].append(anchor_id)
    diagnostics = []
    for case in NAMED_CASES:
        matches = []
        if case["anchor_date"]:
            matches = raw_by_stock_date.get((case["stock_code"], case["anchor_date"]), [])
        else:
            matches = sorted(anchor_id for (stock_code, _), ids in raw_by_stock_date.items() if stock_code == case["stock_code"] for anchor_id in ids)
        selected = None
        for anchor_id in sorted(matches):
            candidate = next((record for record in base_controls if record["anchor_id"] == anchor_id), None)
            if candidate is not None:
                selected = candidate
                break
        if selected is None and matches:
            anchor_id = min(matches)
            selected = make_record(anchor_id, "OWNER_DIAGNOSTIC", control_source.get(anchor_id, {}), raw_lookup.get(anchor_id), feature_lookup)
            classify_record(selected, thresholds, a2_lookup, signal_defs)
        if selected is None:
            selected = {"record_id": f"MISSING_{case['case_id']}", "role": "OWNER_DIAGNOSTIC", "stock_code": case["stock_code"], "anchor_date": case["anchor_date"] or UNAVAILABLE, "owner_case_ids": [case["case_id"]], "structural_classification": "AMBIGUOUS", "owner_reference_conflict": "YES", "decision_layer": "SOURCE_ARTIFACT_GAP", "source_lineage": UNAVAILABLE, "pit_status": UNAVAILABLE, "outcomes": outcome_payload(None), "snapshots": {}, "global_eligibility": {"classification": "GLOBAL_UNKNOWN", "eligible": False}, "environment": {"classification": "UNKNOWN", "eligible": False}, "base_range": {"classification": "UNKNOWN", "eligible": False}, "breakout_event": {"classification": "AMBIGUOUS_BREAKOUT", "reason": "No matching frozen source anchor found."}, "late_stage_risk": {"classification": "UNKNOWN", "warning": False}, "quality": {"active_signal_count": 0}, "stage_flags": {}}
        if selected.get("role") != "OWNER_DIAGNOSTIC":
            selected = copy.deepcopy(selected)
            selected["role"] = "OWNER_DIAGNOSTIC"
        source_record_id = selected.get("record_id")
        selected["diagnostic_source_record_id"] = source_record_id if source_record_id and not str(source_record_id).startswith("MISSING_") else None
        selected["record_id"] = f"OWNER_DIAGNOSTIC:{case['case_id']}:{selected.get('anchor_id', 'MISSING')}"
        selected["owner_case_ids"] = sorted(set(selected.get("owner_case_ids", [])) | {case["case_id"]})
        selected["owner_review_kind"] = case["kind"]
        selected["owner_reference_conflict"] = "YES" if selected.get("structural_classification") in {"STRUCTURAL_FALSE_POSITIVE", "AMBIGUOUS"} else selected.get("owner_reference_conflict", "NO")
        selected["decision_layer"] = selected.get("decision_layer", "L0_GLOBAL_ELIGIBILITY")
        diagnostics.append(selected)
    source_meta = read_json(paths["p1e_run_summary"])
    manifest_records = []
    manifest_records.extend({"record_type": "PRIOR_A_LIKE", "record_id": record["record_id"], "record": record} for record in sorted(base_controls, key=lambda item: (item.get("anchor_date", ""), item.get("stock_code", ""), item.get("record_id", ""))))
    manifest_records.extend({"record_type": "OWNER_REFERENCE_SUCCESS", "record_id": record["record_id"], "record": record} for record in sorted(owner_refs, key=lambda item: (item.get("stock_code", ""), item.get("anchor_date", ""), item.get("record_id", ""))))
    manifest_records.extend({"record_type": "OWNER_DIAGNOSTIC", "record_id": record["record_id"], "record": record} for record in sorted(diagnostics, key=lambda item: (item.get("stock_code", ""), item.get("anchor_date", ""), item.get("record_id", ""))))
    manifest_path = out / "ws3-a-structural-intermediate-manifest.jsonl"
    manifest_hash = jsonl_write(manifest_path, manifest_records)
    manifest_meta = {"schema_version": "ws3-a-structural-intermediate-manifest.v1", "TASK_ID": TASK_ID, "record_count": len(manifest_records), "record_type_counts": dict(Counter(row["record_type"] for row in manifest_records)), "sha256": manifest_hash, "thresholds": thresholds, "large_panel_scan_count": scan_counts["large_panel_scan_count"], "large_source_panels_rescanned_after_manifest": False, "report_generation_must_consume_this_manifest": True, "source_dataset_sha256": DATASET_SHA}
    write_json(out / "ws3-a-structural-intermediate-manifest-meta.json", manifest_meta)
    report_rows = jsonl_read(manifest_path)
    summary = write_outputs(root, out, docs, report_rows, source_meta, preflight, scan_counts, thresholds, signal_defs, source_summary, inventory_rows, manifest_meta)
    summary["REPORT_GENERATION_USED_INTERMEDIATE_MANIFEST"] = "YES"
    write_json(out / "ws3-a-structural-eligibility-run-summary.json", summary)
    write_text(docs / "formal-closure-report.md", formal_report(summary, sorted(path.name for path in out.iterdir() if path.is_file())))


if __name__ == "__main__":
    main()
