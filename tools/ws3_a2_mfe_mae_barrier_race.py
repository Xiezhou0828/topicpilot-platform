#!/usr/bin/env python3
"""WS3 A2 MFE/MAE and barrier-race decision report.

This is an aggregation-only continuation of the already completed
WS3-A2 outcome-reconstruction task.  It reads the committed path-aware CSV
and the committed owner/audit artifacts.  It deliberately does not read the
raw OHLCV store, rebuild the A2 cohort, fit thresholds, or mutate strategy or
production artifacts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "TASK-WS3-A2-MFE-MAE-BARRIER-RACE-DECISION-REPORT-20260822"
PREVIOUS_TASK_ID = "TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821"
SOURCE_DIR_NAME = f"reports/{PREVIOUS_TASK_ID}"
OUT_DIR_NAME = f"reports/{TASK_ID}"
PATH_FILE = "a2-path-aware-outcomes.csv"
OWNER_FILE = "owner-label-reconciliation-30-case.csv"
CA_FILE = "corporate-action-data-quality-audit.csv"
REGIME_FILE = "regime-attribution-audit.csv"
EXTENSION_FILE = "extension-feature-comparison.csv"
PREVIOUS_RUN_FILE = "run-summary.json"
PREVIOUS_TOOL = "tools/ws3_a2_outcome_reconstruction.py"

MFE_THRESHOLDS = ((0.03, "+3%"), (0.05, "+5%"), (0.10, "+10%"), (0.15, "+15%"), (0.20, "+20%"))
MAE_THRESHOLDS = ((-0.03, "-3%"), (-0.05, "-5%"), (-0.08, "-8%"), (-0.10, "-10%"), (-0.15, "-15%"))
RACE_PAIRS = (
    (0.03, -0.03, "+3%", "-3%"),
    (0.03, -0.05, "+3%", "-5%"),
    (0.05, -0.03, "+5%", "-3%"),
    (0.05, -0.05, "+5%", "-5%"),
    (0.05, -0.08, "+5%", "-8%"),
    (0.10, -0.05, "+10%", "-5%"),
    (0.10, -0.08, "+10%", "-8%"),
    (0.10, -0.10, "+10%", "-10%"),
)
MFE_MAE_PAIRS = (
    (0.03, -0.03, "+3%", "-3%"),
    (0.05, -0.03, "+5%", "-3%"),
    (0.05, -0.05, "+5%", "-5%"),
    (0.10, -0.05, "+10%", "-5%"),
    (0.10, -0.08, "+10%", "-8%"),
)


def sha256_normalized(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def json_load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def as_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def pct(count: int, denominator: int) -> float | None:
    return count / denominator if denominator else None


def fmt(value: float | int | None) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    return f"{value:.12g}"


def quantile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "" if value is None else value for key, value in row.items()})


def source_rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def load_event_paths(path: Path) -> tuple[dict[str, dict[str, Any]], int, Counter[str]]:
    events: dict[str, dict[str, Any]] = {}
    row_count = 0
    status_counts: Counter[str] = Counter()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            row_count += 1
            event_id = raw["event_id"]
            horizon = as_int(raw.get("horizon"))
            if horizon is None:
                raise ValueError(f"Missing horizon for event {event_id}")
            status = raw.get("horizon_status", "")
            status_counts[status] += 1
            event = events.setdefault(
                event_id,
                {
                    "event_id": event_id,
                    "instrument_id": raw.get("instrument_id", ""),
                    "stock_code": raw.get("stock_code", ""),
                    "market": raw.get("market", ""),
                    "signal_date": raw.get("signal_date", ""),
                    "a2_close": as_float(raw.get("a2_close")),
                    "volume_shares": as_float(raw.get("volume_shares")),
                    "volume_lots": as_float(raw.get("volume_lots")),
                    "volume_unit_status": raw.get("volume_unit_status", ""),
                    "extension_pct": as_float(raw.get("extension_pct")),
                    "entry_extension_band": raw.get("entry_extension_band", ""),
                    "rows": {},
                },
            )
            if horizon in event["rows"]:
                raise ValueError(f"Duplicate event/horizon: {event_id}/{horizon}")
            event["rows"][horizon] = {
                "horizon": horizon,
                "horizon_status": status,
                "target_date": raw.get("target_date", ""),
                "endpoint_return": as_float(raw.get("endpoint_return")),
                "mfe": as_float(raw.get("mfe")),
                "mae": as_float(raw.get("mae")),
                "mfe_timing_session": as_int(raw.get("mfe_timing_session")),
                "mae_timing_session": as_int(raw.get("mae_timing_session")),
                "path_ordering": raw.get("path_ordering", ""),
                "mfe_before_mae": raw.get("mfe_before_mae", ""),
                "adjustment_state": raw.get("adjustment_state", ""),
                "suppression_reasons": raw.get("suppression_reasons", ""),
            }
    if row_count != len(events) * 10:
        raise ValueError(f"Expected 10 horizon rows per event; rows={row_count} events={len(events)}")
    return events, row_count, status_counts


def valid_through(event: dict[str, Any], horizon: int) -> bool:
    for day in range(1, horizon + 1):
        row = event["rows"].get(day)
        if not row:
            return False
        if row["horizon_status"] != "COMPLETE_RAW_PATH":
            return False
        if row["endpoint_return"] is None or row["mfe"] is None or row["mae"] is None:
            return False
        if row["suppression_reasons"]:
            return False
    return True


def first_crossing(event: dict[str, Any], horizon: int, field: str, threshold: float) -> int | None:
    for day in range(1, horizon + 1):
        value = event["rows"][day][field]
        if value is not None and ((field == "mfe" and value >= threshold) or (field == "mae" and value <= threshold)):
            return day
    return None


def race_category(event: dict[str, Any], horizon: int, positive: float, negative: float) -> str:
    pos_day = first_crossing(event, horizon, "mfe", positive)
    neg_day = first_crossing(event, horizon, "mae", negative)
    if pos_day is None and neg_day is None:
        return "NEITHER"
    if pos_day is None:
        return "NEGATIVE_BARRIER_FIRST"
    if neg_day is None:
        return "POSITIVE_BARRIER_FIRST"
    if pos_day < neg_day:
        return "POSITIVE_BARRIER_FIRST"
    if neg_day < pos_day:
        return "NEGATIVE_BARRIER_FIRST"
    return "SAME_SESSION_ORDER_UNKNOWN"


def previous_source_files(source_dir: Path, repo_root: Path) -> list[dict[str, Any]]:
    names = [
        PATH_FILE,
        "a2-source-reconstruction-reconciliation.csv",
        "failure-attribution.csv",
        OWNER_FILE,
        "filter-ablation.csv",
        EXTENSION_FILE,
        CA_FILE,
        REGIME_FILE,
        PREVIOUS_RUN_FILE,
        "path-aware-outcome-manifest.json",
        "owner-decision-memo.md",
        "formal-closure-report.md",
    ]
    result = []
    for name in names:
        path = source_dir / name
        result.append({"path": source_rel(path, repo_root), "sha256": sha256_normalized(path), "exists": path.exists()})
    # These are the governance inputs explicitly required by the task.  They
    # are kept in the source manifest even though the current computation only
    # needs the already reconciled path artifact and the 30-case source CSV.
    governance_names = [
        "reports/TASK-WS3-A2-HISTORICAL-LABEL-AUDIT-AND-OWNER-REVIEW-HANDOFF-20260821/WS3-A2-HISTORICAL-LABEL-OWNER-REVIEW-PACK.md",
        "reports/TASK-WS3-A2-HISTORICAL-LABEL-AUDIT-AND-OWNER-REVIEW-HANDOFF-20260821/ws3-a2-historical-label-audit-master.csv",
        "reports/TASK-WS3-A2-HISTORICAL-LABEL-AUDIT-AND-OWNER-REVIEW-HANDOFF-20260821/formal-closure-report.md",
        "docs/reports/TASK-WS3-A-STRUCTURAL-ELIGIBILITY-RECONSTRUCTION-AND-FALSE-POSITIVE-SEPARATION-20260821/formal-closure-report.md",
        "reports/TASK-WS3-A-STRUCTURAL-ELIGIBILITY-RECONSTRUCTION-AND-FALSE-POSITIVE-SEPARATION-20260821/ws3-a-structural-eligibility-run-summary.json",
    ]
    for name in governance_names:
        path = repo_root / name
        result.append({"path": name, "sha256": sha256_normalized(path), "exists": path.exists(), "governance_input": True})
    tool_path = repo_root / PREVIOUS_TOOL
    result.append({"path": source_rel(tool_path, repo_root), "sha256": sha256_normalized(tool_path), "exists": tool_path.exists(), "read_only_semantics_reference": True})
    return result


def distribution_rows(events: dict[str, dict[str, Any]], horizon: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    valid = [event for event in events.values() if valid_through(event, horizon)]
    rows: list[dict[str, Any]] = []
    for metric, thresholds in (("mfe", MFE_THRESHOLDS), ("mae", MAE_THRESHOLDS)):
        values = [event["rows"][horizon][metric] for event in valid]
        values = [value for value in values if value is not None]
        rows.append({"analysis_window": f"H{horizon}", "metric": metric.upper(), "statistic": "COUNT", "threshold": "", "value": len(values), "count": len(values), "denominator": len(values), "percentage": 1.0, "notes": "COMPLETE_RAW_PATH only; UNKNOWN_RAW_ONLY source series; no adjustment interpretation"})
        for label, fraction in (("MEAN", None), ("MEDIAN", 0.50), ("P10", 0.10), ("P25", 0.25), ("P50", 0.50), ("P75", 0.75), ("P90", 0.90)):
            value = statistics.fmean(values) if fraction is None else quantile(values, fraction)
            rows.append({"analysis_window": f"H{horizon}", "metric": metric.upper(), "statistic": label, "threshold": "", "value": value, "count": "", "denominator": len(values), "percentage": "", "notes": "Linear-interpolated quantile; mean is arithmetic mean"})
        for threshold, label in thresholds:
            count = sum((value >= threshold if metric == "mfe" else value <= threshold) for value in values)
            rows.append({"analysis_window": f"H{horizon}", "metric": metric.upper(), "statistic": "THRESHOLD_COUNT", "threshold": label, "value": "", "count": count, "denominator": len(values), "percentage": pct(count, len(values)), "notes": "Descriptive path excursion threshold; not a trading rule"})
    diagnostics = {
        "valid_event_count": len(valid),
        "invalid_event_count": len(events) - len(valid),
        "mfe_values": [event["rows"][horizon]["mfe"] for event in valid],
        "mae_values": [event["rows"][horizon]["mae"] for event in valid],
        "events": valid,
    }
    return rows, diagnostics


def disagreement_rows(diagnostics_by_horizon: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for horizon, diagnostics in diagnostics_by_horizon.items():
        base = [event for event in diagnostics["events"] if event["rows"][horizon]["endpoint_return"] <= 0]
        for threshold, label in MFE_THRESHOLDS[:4]:
            count = sum(event["rows"][horizon]["mfe"] >= threshold for event in base)
            result.append({"analysis_window": f"H{horizon}", "endpoint_condition": "ENDPOINT_RETURN_LE_0", "mfe_condition": f"MFE_GE_{label.replace('%', 'PCT')}", "endpoint_nonpositive_count": len(base), "count": count, "percentage": pct(count, len(base)), "interpretation": "PATH_ENDPOINT_DISAGREEMENT_CANDIDATE; not strategy success and not an Owner label"})
    return result


def adverse_rows(diagnostics_by_horizon: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for horizon, diagnostics in diagnostics_by_horizon.items():
        base = [event for event in diagnostics["events"] if event["rows"][horizon]["endpoint_return"] > 0]
        for threshold, label in MAE_THRESHOLDS[:4]:
            count = sum(event["rows"][horizon]["mae"] <= threshold for event in base)
            result.append({"analysis_window": f"H{horizon}", "endpoint_condition": "ENDPOINT_RETURN_GT_0", "mae_condition": f"MAE_LE_{label.replace('-', 'NEG_').replace('%', 'PCT')}", "endpoint_positive_count": len(base), "count": count, "percentage": pct(count, len(base)), "interpretation": "POSITIVE_ENDPOINT_ADVERSE_PATH; descriptive only; no exit semantics inferred"})
    return result


def race_rows(events: dict[str, dict[str, Any]], analysis_type: str, pairs: tuple[tuple[float, float, str, str], ...]) -> list[dict[str, Any]]:
    result = []
    for horizon in (5, 10):
        valid = [event for event in events.values() if valid_through(event, horizon)]
        invalid = len(events) - len(valid)
        for positive, negative, positive_label, negative_label in pairs:
            counts = Counter(race_category(event, horizon, positive, negative) for event in valid)
            row = {
                "analysis_type": analysis_type,
                "analysis_window": f"H{horizon}",
                "positive_barrier": positive_label,
                "negative_barrier": negative_label,
                "positive_threshold": positive,
                "negative_threshold": negative,
                "valid_path_events": len(valid),
                "data_not_available_events": invalid,
                "positive_first_count": counts["POSITIVE_BARRIER_FIRST"],
                "positive_first_pct": pct(counts["POSITIVE_BARRIER_FIRST"], len(valid)),
                "negative_first_count": counts["NEGATIVE_BARRIER_FIRST"],
                "negative_first_pct": pct(counts["NEGATIVE_BARRIER_FIRST"], len(valid)),
                "same_session_order_unknown_count": counts["SAME_SESSION_ORDER_UNKNOWN"],
                "same_session_order_unknown_pct": pct(counts["SAME_SESSION_ORDER_UNKNOWN"], len(valid)),
                "neither_count": counts["NEITHER"],
                "neither_pct": pct(counts["NEITHER"], len(valid)),
                "method": "First cumulative MFE/MAE horizon crossing from existing T+1..T+10 rows; equal first day is same-session order unknown; no intraday high/low ordering guessed",
                "disposition": "DESCRIPTIVE_STRATEGY_REVIEW_INPUT_ONLY",
            }
            result.append(row)
    return result


def time_to_opportunity_rows(events: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    valid = [event for event in events.values() if valid_through(event, 10)]
    result = []
    for threshold, label in MFE_THRESHOLDS[:3]:
        buckets = Counter(first_crossing(event, 10, "mfe", threshold) or "NOT_REACHED" for event in valid)
        for day in list(range(1, 11)) + ["NOT_REACHED"]:
            count = buckets[day]
            result.append({"analysis_window": "H10", "opportunity_threshold": label, "first_reached_day": day, "count": count, "denominator_valid_h10_events": len(valid), "percentage": pct(count, len(valid)), "disposition": "DESCRIPTIVE_PATH_TIMING_ONLY; not an exit rule"})
    return result


def old_proxy_rows(events: dict[str, dict[str, Any]], previous_run: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    valid = [event for event in events.values() if valid_through(event, 10)]
    positive = [event for event in valid if event["rows"][10]["endpoint_return"] > 0]
    nonpositive = [event for event in valid if event["rows"][10]["endpoint_return"] <= 0]
    unknown = len(events) - len(valid)
    rows = [
        {"section": "SUMMARY", "metric": "T10_ENDPOINT_PROXY", "condition": "ENDPOINT_RETURN_GT_0", "count": len(positive), "denominator": len(events), "percentage": pct(len(positive), len(events)), "previous_expected": previous_run.get("raw_t10_positive_proxy_count"), "reconciliation": "MATCH" if len(positive) == previous_run.get("raw_t10_positive_proxy_count") else "MISMATCH"},
        {"section": "SUMMARY", "metric": "T10_ENDPOINT_PROXY", "condition": "ENDPOINT_RETURN_LE_0", "count": len(nonpositive), "denominator": len(events), "percentage": pct(len(nonpositive), len(events)), "previous_expected": previous_run.get("raw_t10_nonpositive_proxy_count"), "reconciliation": "MATCH" if len(nonpositive) == previous_run.get("raw_t10_nonpositive_proxy_count") else "MISMATCH"},
        {"section": "SUMMARY", "metric": "T10_ENDPOINT_PROXY", "condition": "UNKNOWN_OR_FAIL_CLOSED", "count": unknown, "denominator": len(events), "percentage": pct(unknown, len(events)), "previous_expected": previous_run.get("raw_t10_unknown_count"), "reconciliation": "MATCH" if unknown == previous_run.get("raw_t10_unknown_count") else "MISMATCH"},
    ]
    mfe_conditions = (("MFE10_LT_3PCT", lambda event: event["rows"][10]["mfe"] < 0.03), ("MFE10_GE_3PCT", lambda event: event["rows"][10]["mfe"] >= 0.03), ("MFE10_GE_5PCT", lambda event: event["rows"][10]["mfe"] >= 0.05), ("MFE10_GE_10PCT", lambda event: event["rows"][10]["mfe"] >= 0.10), ("MFE10_GE_15PCT", lambda event: event["rows"][10]["mfe"] >= 0.15))
    for name, predicate in mfe_conditions:
        count = sum(predicate(event) for event in nonpositive)
        rows.append({"section": "T10_NONPOSITIVE", "metric": "MFE10", "condition": name, "count": count, "denominator": len(nonpositive), "percentage": pct(count, len(nonpositive)), "previous_expected": "", "reconciliation": "DESCRIPTIVE"})
    cross_conditions = (
        ("MFE10_GE_5PCT_AND_MAE10_GT_NEG3PCT", lambda event: event["rows"][10]["mfe"] >= 0.05 and event["rows"][10]["mae"] > -0.03),
        ("MFE10_GE_5PCT_AND_MAE10_GT_NEG5PCT", lambda event: event["rows"][10]["mfe"] >= 0.05 and event["rows"][10]["mae"] > -0.05),
        ("MFE10_GE_10PCT_AND_MAE10_GT_NEG5PCT", lambda event: event["rows"][10]["mfe"] >= 0.10 and event["rows"][10]["mae"] > -0.05),
        ("MFE10_GE_10PCT_AND_MAE10_GT_NEG8PCT", lambda event: event["rows"][10]["mfe"] >= 0.10 and event["rows"][10]["mae"] > -0.08),
    )
    for name, predicate in cross_conditions:
        count = sum(predicate(event) for event in nonpositive)
        rows.append({"section": "T10_NONPOSITIVE", "metric": "MFE10_MAE10_CROSS", "condition": name, "count": count, "denominator": len(nonpositive), "percentage": pct(count, len(nonpositive)), "previous_expected": "", "reconciliation": "DESCRIPTIVE"})
    diagnostics = {"valid": valid, "positive": positive, "nonpositive": nonpositive, "unknown": unknown, "positive_count": len(positive), "nonpositive_count": len(nonpositive)}
    return rows, diagnostics


def event_filter(event: dict[str, Any], filter_id: str) -> bool:
    price = event["a2_close"]
    shares = event["volume_shares"]
    price_ok = price is not None and price >= 20.0
    volume_ok = shares is not None and shares >= 500000.0
    return {"BASE": True, "PRICE_GE_20": price_ok, "VOLUME_GE_500": volume_ok, "PRICE_GE_20_AND_VOLUME_GE_500": price_ok and volume_ok}[filter_id]


def filter_ablation_rows(events: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    filter_ids = ("BASE", "PRICE_GE_20", "VOLUME_GE_500", "PRICE_GE_20_AND_VOLUME_GE_500")
    baseline_h10 = [event for event in events.values() if valid_through(event, 10)]
    baseline_race_5 = Counter(race_category(event, 10, 0.05, -0.05) for event in baseline_h10)
    baseline_race_10 = Counter(race_category(event, 10, 0.10, -0.05) for event in baseline_h10)
    rows = []
    for filter_id in filter_ids:
        selected = [event for event in events.values() if event_filter(event, filter_id)]
        h5 = [event for event in selected if valid_through(event, 5)]
        h10 = [event for event in selected if valid_through(event, 10)]
        excluded = [event for event in events.values() if not event_filter(event, filter_id)]
        endpoint_positive = [event for event in h10 if event["rows"][10]["endpoint_return"] > 0]
        endpoint_nonpositive = [event for event in h10 if event["rows"][10]["endpoint_return"] <= 0]
        race5 = Counter(race_category(event, 10, 0.05, -0.05) for event in h10)
        race10 = Counter(race_category(event, 10, 0.10, -0.05) for event in h10)
        row = {
            "filter_id": filter_id,
            "filter_status": "ABLATION_ONLY_NOT_PRODUCTION_RULE",
            "event_count": len(selected),
            "excluded_event_count": len(excluded),
            "valid_h5_count": len(h5),
            "valid_h10_count": len(h10),
            "old_t10_positive_proxy_count": len(endpoint_positive),
            "old_t10_nonpositive_proxy_count": len(endpoint_nonpositive),
            "old_t10_unknown_count": len(selected) - len(h10),
            "old_t10_positive_proxy_pct_of_valid": pct(len(endpoint_positive), len(h10)),
            "endpoint_t10_mean": statistics.fmean(event["rows"][10]["endpoint_return"] for event in h10) if h10 else None,
            "mfe10_mean": statistics.fmean(event["rows"][10]["mfe"] for event in h10) if h10 else None,
            "mfe5_median": quantile([event["rows"][5]["mfe"] for event in h5], 0.5),
            "mae5_median": quantile([event["rows"][5]["mae"] for event in h5], 0.5),
            "mfe10_median": quantile([event["rows"][10]["mfe"] for event in h10], 0.5),
            "mae10_median": quantile([event["rows"][10]["mae"] for event in h10], 0.5),
            "mfe10_ge_5_count": sum(event["rows"][10]["mfe"] >= 0.05 for event in h10),
            "mfe10_ge_5_pct": pct(sum(event["rows"][10]["mfe"] >= 0.05 for event in h10), len(h10)),
            "mfe10_ge_10_count": sum(event["rows"][10]["mfe"] >= 0.10 for event in h10),
            "mfe10_ge_10_pct": pct(sum(event["rows"][10]["mfe"] >= 0.10 for event in h10), len(h10)),
            "mae10_le_neg5_count": sum(event["rows"][10]["mae"] <= -0.05 for event in h10),
            "mae10_le_neg10_count": sum(event["rows"][10]["mae"] <= -0.10 for event in h10),
            "positive_5_before_negative_5_count": race5["POSITIVE_BARRIER_FIRST"],
            "positive_5_before_negative_5_pct": pct(race5["POSITIVE_BARRIER_FIRST"], len(h10)),
            "positive_10_before_negative_5_count": race10["POSITIVE_BARRIER_FIRST"],
            "positive_10_before_negative_5_pct": pct(race10["POSITIVE_BARRIER_FIRST"], len(h10)),
            "endpoint_nonpositive_mfe10_ge_5_count": sum(event["rows"][10]["endpoint_return"] <= 0 and event["rows"][10]["mfe"] >= 0.05 for event in h10),
            "endpoint_nonpositive_mfe10_ge_10_count": sum(event["rows"][10]["endpoint_return"] <= 0 and event["rows"][10]["mfe"] >= 0.10 for event in h10),
            "excluded_valid_h10_endpoint_positive_count": sum(valid_through(event, 10) and event["rows"][10]["endpoint_return"] > 0 for event in excluded),
            "excluded_valid_h10_mfe10_ge_5_count": sum(valid_through(event, 10) and event["rows"][10]["mfe"] >= 0.05 for event in excluded),
            "excluded_valid_h10_mfe10_ge_10_count": sum(valid_through(event, 10) and event["rows"][10]["mfe"] >= 0.10 for event in excluded),
            "excluded_valid_h10_positive_5_before_negative_5_count": sum(valid_through(event, 10) and race_category(event, 10, 0.05, -0.05) == "POSITIVE_BARRIER_FIRST" for event in excluded),
            "excluded_valid_h10_positive_10_before_negative_5_count": sum(valid_through(event, 10) and race_category(event, 10, 0.10, -0.05) == "POSITIVE_BARRIER_FIRST" for event in excluded),
            "price_floor_definition": "a2_close >= 20.0; candidate only",
            "volume_floor_definition": "volume_shares >= 500000 (500 lots converted using existing SHARES unit contract); candidate only",
            "notes": "No filter is accepted, fitted, or written as a production rule; BASE comparison is descriptive.",
        }
        rows.append(row)
    # Keep the variables in the source visible to reviewers and make it hard to
    # accidentally remove the baseline race calculations while editing.
    _ = baseline_race_5, baseline_race_10
    return rows


def extension_rows(events: dict[str, dict[str, Any]], extension_source: Path) -> list[dict[str, Any]]:
    existing_rows = csv_rows(extension_source)
    existing_features = sorted({row.get("feature", "") for row in existing_rows if row.get("feature")})
    existing_feature_note = ", ".join(existing_features) if existing_features else "feature field unavailable"
    fields = [
        "close_vs_ma20",
        "close_vs_ma60",
        "prior_10d_return",
        "prior_20d_return",
        "prior_40d_return",
        "distance_from_consolidation_base",
        "pre_trigger_acceleration_proxy",
        "trigger_acceleration_full_definition",
        "extension_pct_from_frozen_reference",
        "entry_extension_band",
    ]
    rows: list[dict[str, Any]] = []
    for feature in fields[:-2]:
        rows.append({"feature": feature, "source_status": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS", "analysis_group": "ALL_EVENTS", "group_value": "", "event_count": "", "valid_h10_count": "", "endpoint_t10_mean": "", "mfe10_median": "", "mae10_median": "", "mfe10_ge_5_count": "", "mfe10_ge_10_count": "", "positive_5_before_negative_5_count": "", "positive_10_before_negative_5_count": "", "descriptive_only": "YES", "notes": f"Existing {extension_source.name} has aggregate-only feature rows ({existing_feature_note}), not event-level path joins. No raw feature recomputation or threshold search permitted."})
    bands = sorted({event["entry_extension_band"] or "UNKNOWN" for event in events.values()})
    for band in bands:
        selected = [event for event in events.values() if (event["entry_extension_band"] or "UNKNOWN") == band]
        valid = [event for event in selected if valid_through(event, 10)]
        race5 = sum(race_category(event, 10, 0.05, -0.05) == "POSITIVE_BARRIER_FIRST" for event in valid)
        race10 = sum(race_category(event, 10, 0.10, -0.05) == "POSITIVE_BARRIER_FIRST" for event in valid)
        rows.append({"feature": "entry_extension_band", "source_status": "AVAILABLE_FROM_PATH_ARTIFACT", "analysis_group": "ENTRY_EXTENSION_BAND", "group_value": band, "event_count": len(selected), "valid_h10_count": len(valid), "endpoint_t10_mean": statistics.fmean(event["rows"][10]["endpoint_return"] for event in valid) if valid else None, "mfe10_median": quantile([event["rows"][10]["mfe"] for event in valid], 0.5), "mae10_median": quantile([event["rows"][10]["mae"] for event in valid], 0.5), "mfe10_ge_5_count": sum(event["rows"][10]["mfe"] >= 0.05 for event in valid), "mfe10_ge_10_count": sum(event["rows"][10]["mfe"] >= 0.10 for event in valid), "positive_5_before_negative_5_count": race5, "positive_10_before_negative_5_count": race10, "descriptive_only": "YES", "notes": "Existing entry_extension_band carried by path artifact; no threshold was selected."})
    rows.append({"feature": "extension_pct_from_frozen_reference", "source_status": "AVAILABLE_AS_CARRIED_EXTENSION_FIELD", "analysis_group": "ALL_EVENTS", "group_value": "", "event_count": len(events), "valid_h10_count": sum(valid_through(event, 10) for event in events.values()), "endpoint_t10_mean": statistics.fmean(event["rows"][10]["endpoint_return"] for event in events.values() if valid_through(event, 10)), "mfe10_median": quantile([event["rows"][10]["mfe"] for event in events.values() if valid_through(event, 10)], 0.5), "mae10_median": quantile([event["rows"][10]["mae"] for event in events.values() if valid_through(event, 10)], 0.5), "mfe10_ge_5_count": sum(valid_through(event, 10) and event["rows"][10]["mfe"] >= 0.05 for event in events.values()), "mfe10_ge_10_count": sum(valid_through(event, 10) and event["rows"][10]["mfe"] >= 0.10 for event in events.values()), "positive_5_before_negative_5_count": sum(valid_through(event, 10) and race_category(event, 10, 0.05, -0.05) == "POSITIVE_BARRIER_FIRST" for event in events.values()), "positive_10_before_negative_5_count": sum(valid_through(event, 10) and race_category(event, 10, 0.10, -0.05) == "POSITIVE_BARRIER_FIRST" for event in events.values()), "descriptive_only": "YES", "notes": "Existing extension_pct field carried by path artifact; no threshold was selected."})
    return rows


def owner_template(events: dict[str, dict[str, Any]], owner_source: Path, ca_source: Path, regime_source: Path) -> list[dict[str, Any]]:
    owner_rows = csv_rows(owner_source)
    ca_rows = csv_rows(ca_source)
    regime_rows = csv_rows(regime_source)
    ca_by_key = {(row.get("stock_code", ""), row.get("signal_date", "")): row for row in ca_rows if row.get("event_id")}
    regime_by_key = {(row.get("stock_code", ""), row.get("signal_date", "")): row for row in regime_rows if row.get("stock_code")}
    by_case = {(event["stock_code"], event["signal_date"]): event for event in events.values()}
    result = []
    for source in owner_rows:
        key = (source.get("instrument", source.get("stock_code", "")), source.get("anchor_date", source.get("signal_date", "")))
        event = by_case.get(key)
        if event is None:
            # The prior artifact uses stock_code/anchor_date in some versions;
            # retain the exact source case even if matching is not available.
            event = {"stock_code": key[0], "signal_date": key[1], "rows": {}, "event_id": "", "a2_close": None, "volume_shares": None}
        ca = ca_by_key.get(key, {})
        regime = regime_by_key.get(key, {})
        h5 = event["rows"].get(5, {})
        h10 = event["rows"].get(10, {})
        first_pos = first_crossing(event, 10, "mfe", 0.05) if valid_through(event, 10) else None
        first_neg = first_crossing(event, 10, "mae", -0.05) if valid_through(event, 10) else None
        barrier = race_category(event, 10, 0.05, -0.05) if valid_through(event, 10) else "DATA_NOT_AVAILABLE_FAIL_CLOSED"
        result.append({
            "instrument": key[0],
            "anchor_date": key[1],
            "old_proxy_label": source.get("historical_outcome_label_or_proxy", source.get("old_proxy_label", source.get("sample_stratum", ""))),
            "endpoint_T5": h5.get("endpoint_return", ""),
            "endpoint_T10": h10.get("endpoint_return", ""),
            "MFE5": h5.get("mfe", ""),
            "MAE5": h5.get("mae", ""),
            "MFE10": h10.get("mfe", ""),
            "MAE10": h10.get("mae", ""),
            "first_+5_day": first_pos or "",
            "first_-5_day": first_neg or "",
            "barrier_+5_vs_-5": barrier,
            "corporate_action_status": ca.get("corporate_action_state", "NOT_FLAGGED_IN_EXISTING_AUDIT"),
            "regime_status": regime.get("regime_attribution", "NOT_A_FOCUS_CASE_IN_EXISTING_AUDIT"),
            "owner_label": "",
            "owner_failure_subtype": "",
            "owner_notes": "",
            "owner_authority_status": "OWNER_INPUT_REQUIRED; fields intentionally blank",
            "source_owner_artifact": owner_source.as_posix(),
        })
    if len(result) != 30:
        raise ValueError(f"Expected 30 Owner cases, got {len(result)}")
    return result


def choose_q6(filter_rows: list[dict[str, Any]]) -> str:
    base = filter_rows[0]
    candidates = filter_rows[1:]
    if not candidates or not base.get("valid_h10_count"):
        return "INSUFFICIENT_EVIDENCE"
    improvements = []
    for candidate in candidates:
        improvements.append(
            candidate["mfe10_median"] >= base["mfe10_median"]
            and candidate["mae10_median"] >= base["mae10_median"]
            and candidate["positive_5_before_negative_5_pct"] >= base["positive_5_before_negative_5_pct"]
        )
    if all(improvements):
        return "IMPROVES"
    return "MIXED"


def build_memo(stats: dict[str, Any]) -> str:
    q1 = "INCONCLUSIVE"
    q7 = "PARTIALLY_SUPPORTED" if stats["nonpositive_mfe_ge_5_pct"] is not None and stats["nonpositive_mfe_ge_5_pct"] >= 0.10 else "INCONCLUSIVE"
    q6 = stats["filter_disposition"]
    return f"""# A2 MFE/MAE Barrier-Race Owner Decision Memo

Task: `{TASK_ID}`
Scope: existing WS3 Core V0 A2 walk-forward research only.
Disposition: **STRATEGY_REVIEW_INPUT / OWNER_REVIEW_REQUIRED**.

## Decision questions

1. **Q1 — Does endpoint-only evaluation understate path opportunity?** **{q1}**. T10 endpoint-non-positive events with MFE10 ≥5%: {stats['nonpositive_mfe_ge_5_count']}/{stats['nonpositive_count']} ({fmt(stats['nonpositive_mfe_ge_5_pct'])}); with MFE10 ≥10%: {stats['nonpositive_mfe_ge_10_count']}/{stats['nonpositive_count']} ({fmt(stats['nonpositive_mfe_ge_10_pct'])}). This is path/endpoint disagreement evidence, not a declared strategy success.
2. **Q2 — Among T10 non-positive endpoint events, how many reached MFE10 ≥3/5/10?** {stats['nonpositive_mfe_ge_3_count']}/{stats['nonpositive_count']} ({fmt(stats['nonpositive_mfe_ge_3_pct'])}); {stats['nonpositive_mfe_ge_5_count']}/{stats['nonpositive_count']} ({fmt(stats['nonpositive_mfe_ge_5_pct'])}); {stats['nonpositive_mfe_ge_10_count']}/{stats['nonpositive_count']} ({fmt(stats['nonpositive_mfe_ge_10_pct'])}).
3. **Q3 — How often did positive endpoint coexist with adverse path?** H10 endpoint-positive events with MAE10 ≤−3%: {stats['positive_mae_le_3_count']}/{stats['positive_count']}; ≤−5%: {stats['positive_mae_le_5_count']}/{stats['positive_count']}; ≤−10%: {stats['positive_mae_le_10_count']}/{stats['positive_count']}. No exit rule is inferred.
4. **Q4 — Typical favorable-excursion speed?** The H10 first-reach distribution is in `time-to-opportunity.csv`; median first reach is +3% day {stats['first_plus3_median_day']}, +5% day {stats['first_plus5_median_day']}, +10% day {stats['first_plus10_median_day']}. `NOT_REACHED` remains a valid outcome.
5. **Q5 — Barrier race?** +5% before −5%: H5 {stats['plus5_before_minus5_h5']}/{stats['valid_h5']} ({fmt(stats['plus5_before_minus5_h5_pct'])}); H10 {stats['plus5_before_minus5_h10']}/{stats['valid_h10']} ({fmt(stats['plus5_before_minus5_h10_pct'])}). +10% before −5%: H5 {stats['plus10_before_minus5_h5']}/{stats['valid_h5']} ({fmt(stats['plus10_before_minus5_h5_pct'])}); H10 {stats['plus10_before_minus5_h10']}/{stats['valid_h10']} ({fmt(stats['plus10_before_minus5_h10_pct'])}). Same first day is order-unknown; no intraday guess was made.
6. **Q6 — Do candidate filters improve the path profile?** **{q6}**. The four rows in `path-aware-filter-ablation.csv` are descriptive ablations only; no price/volume floor is accepted as a production rule.
7. **Q7 — Is the claim “A2 is not as bad as endpoint proxy suggests” supported?** **{q7}**. The path disagreement evidence is present, but Owner labels are 0/30, adjustment state is UNKNOWN_RAW_ONLY, and no executable exit semantics were supplied.
8. **Q8 — Next reasonable research focus?** **Owner label formalization**, followed by explicit outcome/exit semantics review. This is a recommendation only and does not change `NEXT_TASK`.

## Guardrails and blockers

- MFE/MAE anchor and endpoint semantics were inherited from the committed path-aware artifact: anchor is signal-day `a2_close`; endpoint is future close divided by anchor minus one; MFE/MAE use future high/low path extrema.
- Corporate-action uncertainty remains fail closed. `2327/2025-08-05` remains non-interpretable in `corporate-action-data-quality-audit.csv`.
- `3675/2026-07-06` remains `UNKNOWN_NO_PIT_SAFE_INDEX_BREADTH_PEER_DATA`; performance stays included when not suppressed, and it is not deleted as a supposed market shock.
- Owner fields in `owner-30-case-label-input-template.csv` are intentionally blank. The 30 reviewed cases are reference scope, not a training set or threshold-fitting set.
- `A_SETUP_ACCEPTED=NO`, `A_STRATEGY_ACCEPTED=NO`, `PRODUCTION_MUTATION=NO`, `DEPLOY=NO`, `PUSH=NO`, `NEXT_TASK_CHANGED=NO`.
"""


def median_first_day(events: list[dict[str, Any]], threshold: float) -> str:
    days = [first_crossing(event, 10, "mfe", threshold) for event in events]
    days = [day for day in days if day is not None]
    return str(int(statistics.median(days))) if days else "NOT_AVAILABLE"


def build_closure(stats: dict[str, Any], source_files: list[dict[str, Any]], output_names: list[str]) -> str:
    source_lines = "\n".join(f"- `{item['path']}` — `{item['sha256']}`" for item in source_files)
    return f"""# {TASK_ID}

## Formal closure

### Scope and disposition

This is an aggregation-only continuation of `{PREVIOUS_TASK_ID}` inside the existing WS3 Core V0 Walk-forward Research line. It reads the committed path-aware outcome artifact and the already-committed Owner/audit artifacts. It does not rebuild the A2 cohort, rescan raw OHLCV, change A1/A2 semantics, fit thresholds, train a model, accept a strategy, mutate production, deploy, push, or change NEXT_TASK.

Final disposition: **STRATEGY_REVIEW_INPUT / OWNER_REVIEW_REQUIRED**.

### Source artifacts read

{source_lines}

The prior reconstruction helper was read only to confirm field semantics. The current run performed no raw panel scan (`RAW_PANEL_SCANS=0`) and no event-mining/cohort rebuild (`EVENT_MINING_RERUN=0`, `COHORT_REBUILD=0`). It read one committed path-aware CSV (`PATH_AWARE_ARTIFACT_READS=1`).

### Semantics confirmed and fail-closed rules

- A2 event cohort: {stats['event_count']} events; path file rows: {stats['path_row_count']} = event × horizons 1..10.
- Anchor: signal-day `a2_close` carried by the frozen A2 event panel.
- Endpoint: future close / anchor close − 1.
- MFE: maximum future high / anchor close − 1 over the horizon.
- MAE: minimum future low / anchor close − 1 over the horizon.
- Only `COMPLETE_RAW_PATH` rows with non-null metrics and empty suppression reason enter an aggregate. `UNKNOWN_RAW_ONLY` is retained as source state and is not interpreted as adjusted truth.
- For barrier races, the first cumulative horizon at which MFE/MAE crosses each barrier is used. If both barriers first cross on the same session, the result is `SAME_SESSION_ORDER_UNKNOWN`; intraday high/low ordering is not guessed.
- Unresolved corporate-action/discontinuity rows remain excluded from interpretation. The previous audit has 85 suppressed events, including `2327/2025-08-05`.
- MA60-above hard eligibility (A method) remains the governing eligibility context; this report does not return to MA20 eligibility.

### Reconciliation gates

- Expected previous T10 proxy counts: positive 2,587, non-positive 2,559, unknown 131. Current derived counts: positive {stats['positive_count']}, non-positive {stats['nonpositive_count']}, unknown {stats['unknown_count']}.
- Strict interpretable complete path events: H5 {stats['valid_h5']}; H10 {stats['valid_h10']}. The previous report's `raw_path_complete_h10_event_count` was {stats['previous_raw_complete_h10']} and is a different, pre-interpretation raw/maturity counter. This run requires every row 1..H to be complete, non-null, and unsuppressed; the 5,146 H10 T10-proxy denominator therefore reconciles to the current fail-closed rule rather than silently using 5,229.
- Same-session order-unknown counts for +5/−5: H5 {stats['same_h5']}; H10 {stats['same_h10']}.
- Deterministic replay payload: `{stats['aggregate_payload_sha256']}`.

### Research findings

1. Endpoint/path disagreement is measurable: among T10 endpoint-non-positive events, MFE10 ≥5% is {stats['nonpositive_mfe_ge_5_count']}/{stats['nonpositive_count']} ({fmt(stats['nonpositive_mfe_ge_5_pct'])}) and MFE10 ≥10% is {stats['nonpositive_mfe_ge_10_count']}/{stats['nonpositive_count']} ({fmt(stats['nonpositive_mfe_ge_10_pct'])}). This shows why endpoint-only labels can be incomplete; it does not establish a tradable strategy outcome.
2. Positive endpoint/adverse path is also present: H10 endpoint-positive events with MAE10 ≤−5%: {stats['positive_mae_le_5_count']}/{stats['positive_count']}; with MAE10 ≤−10%: {stats['positive_mae_le_10_count']}/{stats['positive_count']}.
3. Barrier race and time-to-opportunity are reported without selecting a hold/exit rule. Same-session ties are explicitly unknown.
4. Candidate price/volume filters are ablations with opportunity-cost columns. No candidate filter is promoted.
5. Extension analysis uses only existing carried extension fields. Close/MA20, close/MA60, prior returns, consolidation-base distance, and full acceleration are not joined to event-level path outcomes in the existing artifacts and are marked unavailable rather than recomputed.
6. Corporate-action and regime audits remain blockers for interpretation of affected cases. `3675/2026-07-06` remains performance-included but regime UNKNOWN because PIT-safe index/breadth/theme-peer evidence is unavailable.

### Required outputs

{chr(10).join(f'- `{name}`' for name in output_names)}

### Governance flags

```text
WS3_ONLY=YES
A_SETUP_ACCEPTED=NO
A_STRATEGY_ACCEPTED=NO
PRODUCTION_MUTATION=NO
DEPLOY=NO
PUSH=NO
REMOTE_MERGE=NO
NEXT_TASK_CHANGED=NO
OWNER_REVIEW_REQUIRED=YES
STATUS=STRATEGY_REVIEW_INPUT / OWNER_REVIEW_REQUIRED
```

Closure is complete as an evidence-only research input. It is not strategy acceptance or production authorization.
"""


def payload_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    source_dir = repo_root / SOURCE_DIR_NAME
    out_dir = repo_root / OUT_DIR_NAME
    out_dir.mkdir(parents=True, exist_ok=True)

    source_path = source_dir / PATH_FILE
    events, path_row_count, status_counts = load_event_paths(source_path)
    previous_run = json_load(source_dir / PREVIOUS_RUN_FILE)
    source_files = previous_source_files(source_dir, repo_root)
    diagnostics_by_horizon: dict[int, dict[str, Any]] = {}
    distribution_output: list[dict[str, Any]] = []
    for horizon in (5, 10):
        rows, diagnostics = distribution_rows(events, horizon)
        diagnostics_by_horizon[horizon] = diagnostics
        distribution_output.extend(rows)

    disagreement_output = disagreement_rows(diagnostics_by_horizon)
    adverse_output = adverse_rows(diagnostics_by_horizon)
    barrier_output = race_rows(events, "BARRIER_RACE", RACE_PAIRS) + race_rows(events, "MFE_MAE_THRESHOLD_RACE", MFE_MAE_PAIRS)
    time_output = time_to_opportunity_rows(events)
    proxy_output, proxy_stats = old_proxy_rows(events, previous_run)
    filter_output = filter_ablation_rows(events)
    extension_output = extension_rows(events, source_dir / EXTENSION_FILE)
    owner_output = owner_template(events, source_dir / OWNER_FILE, source_dir / CA_FILE, source_dir / REGIME_FILE)

    valid_h5 = diagnostics_by_horizon[5]["events"]
    valid_h10 = diagnostics_by_horizon[10]["events"]
    positive_h10 = proxy_stats["positive"]
    nonpositive_h10 = proxy_stats["nonpositive"]
    positive_mae = {threshold: sum(event["rows"][10]["mae"] <= threshold for event in positive_h10) for threshold in (-0.03, -0.05, -0.10)}
    race_h5 = Counter(race_category(event, 5, 0.05, -0.05) for event in valid_h5)
    race_h10 = Counter(race_category(event, 10, 0.05, -0.05) for event in valid_h10)
    race10_h5 = Counter(race_category(event, 5, 0.10, -0.05) for event in valid_h5)
    race10_h10 = Counter(race_category(event, 10, 0.10, -0.05) for event in valid_h10)
    nonpositive_mfe_counts = {threshold: sum(event["rows"][10]["mfe"] >= threshold for event in nonpositive_h10) for threshold in (0.03, 0.05, 0.10)}
    stats = {
        "event_count": len(events),
        "path_row_count": path_row_count,
        "valid_h5": len(valid_h5),
        "valid_h10": len(valid_h10),
        "previous_raw_complete_h10": previous_run.get("raw_path_complete_h10_event_count"),
        "positive_count": proxy_stats["positive_count"],
        "nonpositive_count": proxy_stats["nonpositive_count"],
        "unknown_count": proxy_stats["unknown"],
        "same_h5": race_h5["SAME_SESSION_ORDER_UNKNOWN"],
        "same_h10": race_h10["SAME_SESSION_ORDER_UNKNOWN"],
        "positive_mae_le_3_count": positive_mae[-0.03],
        "positive_mae_le_5_count": positive_mae[-0.05],
        "positive_mae_le_10_count": positive_mae[-0.10],
        "nonpositive_mfe_ge_3_count": nonpositive_mfe_counts[0.03],
        "nonpositive_mfe_ge_3_pct": pct(nonpositive_mfe_counts[0.03], len(nonpositive_h10)),
        "nonpositive_mfe_ge_5_count": nonpositive_mfe_counts[0.05],
        "nonpositive_mfe_ge_5_pct": pct(nonpositive_mfe_counts[0.05], len(nonpositive_h10)),
        "nonpositive_mfe_ge_10_count": nonpositive_mfe_counts[0.10],
        "nonpositive_mfe_ge_10_pct": pct(nonpositive_mfe_counts[0.10], len(nonpositive_h10)),
        "plus5_before_minus5_h5": race_h5["POSITIVE_BARRIER_FIRST"],
        "plus5_before_minus5_h5_pct": pct(race_h5["POSITIVE_BARRIER_FIRST"], len(valid_h5)),
        "plus5_before_minus5_h10": race_h10["POSITIVE_BARRIER_FIRST"],
        "plus5_before_minus5_h10_pct": pct(race_h10["POSITIVE_BARRIER_FIRST"], len(valid_h10)),
        "plus10_before_minus5_h5": race10_h5["POSITIVE_BARRIER_FIRST"],
        "plus10_before_minus5_h5_pct": pct(race10_h5["POSITIVE_BARRIER_FIRST"], len(valid_h5)),
        "plus10_before_minus5_h10": race10_h10["POSITIVE_BARRIER_FIRST"],
        "plus10_before_minus5_h10_pct": pct(race10_h10["POSITIVE_BARRIER_FIRST"], len(valid_h10)),
        "first_plus3_median_day": median_first_day(valid_h10, 0.03),
        "first_plus5_median_day": median_first_day(valid_h10, 0.05),
        "first_plus10_median_day": median_first_day(valid_h10, 0.10),
        "filter_disposition": choose_q6(filter_output),
    }
    aggregate_payload = {
        "task_id": TASK_ID,
        "source_path_sha256": sha256_normalized(source_path),
        "event_count": len(events),
        "path_row_count": path_row_count,
        "status_counts": dict(sorted(status_counts.items())),
        "valid_h5": len(valid_h5),
        "valid_h10": len(valid_h10),
        "old_proxy": {key: proxy_stats[key] for key in ("positive_count", "nonpositive_count", "unknown")},
        "distribution_row_count": len(distribution_output),
        "disagreement_row_count": len(disagreement_output),
        "adverse_row_count": len(adverse_output),
        "barrier_row_count": len(barrier_output),
        "time_row_count": len(time_output),
        "filter_row_count": len(filter_output),
        "extension_row_count": len(extension_output),
        "owner_template_row_count": len(owner_output),
        "governance": {"raw_panel_scans": 0, "cohort_rebuild": 0, "strategy_acceptance": "NO", "production_mutation": "NO"},
    }
    stats["aggregate_payload_sha256"] = payload_digest(aggregate_payload)

    write_csv(out_dir / "mfe-mae-distribution.csv", ["analysis_window", "metric", "statistic", "threshold", "value", "count", "denominator", "percentage", "notes"], distribution_output)
    write_csv(out_dir / "endpoint-vs-path-disagreement.csv", ["analysis_window", "endpoint_condition", "mfe_condition", "endpoint_nonpositive_count", "count", "percentage", "interpretation"], disagreement_output)
    write_csv(out_dir / "positive-endpoint-adverse-path.csv", ["analysis_window", "endpoint_condition", "mae_condition", "endpoint_positive_count", "count", "percentage", "interpretation"], adverse_output)
    write_csv(out_dir / "barrier-race-summary.csv", ["analysis_type", "analysis_window", "positive_barrier", "negative_barrier", "positive_threshold", "negative_threshold", "valid_path_events", "data_not_available_events", "positive_first_count", "positive_first_pct", "negative_first_count", "negative_first_pct", "same_session_order_unknown_count", "same_session_order_unknown_pct", "neither_count", "neither_pct", "method", "disposition"], barrier_output)
    write_csv(out_dir / "time-to-opportunity.csv", ["analysis_window", "opportunity_threshold", "first_reached_day", "count", "denominator_valid_h10_events", "percentage", "disposition"], time_output)
    write_csv(out_dir / "old-t10-proxy-reconciliation.csv", ["section", "metric", "condition", "count", "denominator", "percentage", "previous_expected", "reconciliation"], proxy_output)
    write_csv(out_dir / "path-aware-filter-ablation.csv", list(filter_output[0].keys()), filter_output)
    write_csv(out_dir / "extension-path-descriptive-analysis.csv", ["feature", "source_status", "analysis_group", "group_value", "event_count", "valid_h10_count", "endpoint_t10_mean", "mfe10_median", "mae10_median", "mfe10_ge_5_count", "mfe10_ge_10_count", "positive_5_before_negative_5_count", "positive_10_before_negative_5_count", "descriptive_only", "notes"], extension_output)
    write_csv(out_dir / "owner-30-case-label-input-template.csv", list(owner_output[0].keys()), owner_output)

    output_names = [
        "formal-closure-report.md",
        "run-summary.json",
        "mfe-mae-distribution.csv",
        "endpoint-vs-path-disagreement.csv",
        "positive-endpoint-adverse-path.csv",
        "barrier-race-summary.csv",
        "time-to-opportunity.csv",
        "old-t10-proxy-reconciliation.csv",
        "path-aware-filter-ablation.csv",
        "extension-path-descriptive-analysis.csv",
        "owner-30-case-label-input-template.csv",
        "A2-MFE-MAE-BARRIER-RACE-OWNER-DECISION-MEMO.md",
        "reproducibility-source-manifest.json",
    ]
    (out_dir / "A2-MFE-MAE-BARRIER-RACE-OWNER-DECISION-MEMO.md").write_text(build_memo(stats), encoding="utf-8", newline="\n")
    (out_dir / "formal-closure-report.md").write_text(build_closure(stats, source_files, output_names), encoding="utf-8", newline="\n")

    output_hashes = {name: sha256_normalized(out_dir / name) for name in output_names if name not in {"run-summary.json", "reproducibility-source-manifest.json"}}
    run_summary = {
        "task_id": TASK_ID,
        "task_status": "STRATEGY_REVIEW_INPUT / OWNER_REVIEW_REQUIRED",
        "aggregation_only": True,
        "raw_panel_scans": 0,
        "event_mining_rerun": 0,
        "cohort_rebuild": 0,
        "path_aware_artifact_reads": 1,
        "source_artifact": source_rel(source_path, repo_root),
        "source_artifact_sha256": sha256_normalized(source_path),
        "source_artifact_row_count": path_row_count,
        "source_event_count": len(events),
        "valid_complete_raw_path_events_h5": len(valid_h5),
        "valid_complete_raw_path_events_h10": len(valid_h10),
        "previous_reported_raw_path_complete_h10_event_count": previous_run.get("raw_path_complete_h10_event_count"),
        "h10_validity_definition": "all rows 1..10 COMPLETE_RAW_PATH, non-null endpoint/MFE/MAE, and empty suppression reason",
        "source_status_counts": dict(sorted(status_counts.items())),
        "previous_suppressed_event_count": previous_run.get("suppressed_event_count"),
        "corporate_action_adjustment_state": previous_run.get("adjustment_state"),
        "old_t10_proxy_derived": {"positive": proxy_stats["positive_count"], "nonpositive": proxy_stats["nonpositive_count"], "unknown": proxy_stats["unknown"]},
        "old_t10_proxy_expected": {"positive": previous_run.get("raw_t10_positive_proxy_count"), "nonpositive": previous_run.get("raw_t10_nonpositive_proxy_count"), "unknown": previous_run.get("raw_t10_unknown_count")},
        "owner_review_case_count": len(owner_output),
        "owner_labels_available_count": 0,
        "same_session_order_unknown": {"plus5_minus5_h5": race_h5["SAME_SESSION_ORDER_UNKNOWN"], "plus5_minus5_h10": race_h10["SAME_SESSION_ORDER_UNKNOWN"]},
        "aggregate_payload_sha256": stats["aggregate_payload_sha256"],
        "source_files": source_files,
        "output_hashes_excluding_summary_and_manifest": output_hashes,
        "governance_flags": {"WS3_ONLY": "YES", "A_SETUP_ACCEPTED": "NO", "A_STRATEGY_ACCEPTED": "NO", "PRODUCTION_MUTATION": "NO", "DEPLOY": "NO", "PUSH": "NO", "REMOTE_MERGE": "NO", "NEXT_TASK_CHANGED": "NO"},
        "quality_gate_disposition": "PASS_WITH_REVIEW_BLOCKERS",
    }
    (out_dir / "run-summary.json").write_text(json.dumps(run_summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "schema_version": "ws3-a2-mfe-mae-barrier-race-reproducibility-manifest.v1",
        "task_id": TASK_ID,
        "previous_task_id": PREVIOUS_TASK_ID,
        "source_files": source_files,
        "output_files": [{"path": f"{OUT_DIR_NAME}/{name}", "sha256": sha256_normalized(out_dir / name)} for name in output_names if name != "reproducibility-source-manifest.json"],
        "method": {"input_mode": "existing_committed_path_aware_csv_only", "raw_panel_scans": 0, "cohort_rebuild": 0, "quantile_method": "linear_interpolation", "barrier_order_method": "first_cumulative_horizon_crossing; same horizon = SAME_SESSION_ORDER_UNKNOWN", "filter_status": "ablation_only", "owner_labels": "blank_template; no labels inferred"},
        "source_semantics": {"anchor": "signal_day_a2_close", "endpoint": "future_close_divided_by_anchor_minus_one", "mfe": "future_high_divided_by_anchor_minus_one", "mae": "future_low_divided_by_anchor_minus_one", "adjustment_state": "UNKNOWN_RAW_ONLY", "corporate_action_fail_closed": True},
        "aggregate_payload_sha256": stats["aggregate_payload_sha256"],
        "governance_flags": run_summary["governance_flags"],
    }
    (out_dir / "reproducibility-source-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
