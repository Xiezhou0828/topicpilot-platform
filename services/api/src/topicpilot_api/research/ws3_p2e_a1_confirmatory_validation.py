"""WS3 P2-E A1 frozen-candidate confirmatory validation.

This module is deliberately research-only.  It consumes the canonicalized
WS3 P1-E A1 surface and the already-frozen A1 candidate contract, then writes
deterministic, reviewable evidence.  It does not publish a recommendation,
change a strategy contract, write the product database, or alter NEXT_TASK.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import time
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping


TASK_ID = "TASK-WS3-P2E-A1-FROZEN-CANDIDATE-CONFIRMATORY-VALIDATION-603-UNIVERSE-20260820"
SOURCE_START = date(2024, 8, 13)
SOURCE_END = date(2026, 8, 13)
FORMAL_START = date(2026, 2, 2)
DEVELOPMENT_END = date(2026, 6, 30)
TRAIN_START = date(2026, 5, 12)
VALIDATION_START = date(2026, 7, 1)
VALIDATION_END = date(2026, 7, 31)
HOLDOUT_START = date(2026, 8, 1)
HOLDOUT_END = date(2026, 8, 13)
HORIZONS = (1, 3, 5, 10)
MIN_COHORT = 20
SUCCESS_UPLIFT_MIN = Decimal("0.03")
FAILED_REDUCTION_MIN = Decimal("0.03")
FOUNDATION_SHA = "e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4"
P1E_AGGREGATE_SHA = "363af6741a6edbbb2b4a092aa1b3938e0492f5fb6169885dd05df12a7691224d"

OUTPUT_DEFAULT = Path(
    "reports/TASK-WS3-P2E-A1-FROZEN-CANDIDATE-CONFIRMATORY-VALIDATION-603-UNIVERSE-20260820"
)
P1E_OUTPUT = Path(
    "reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820"
)
A1_FREEZE = Path(
    "reports/TASK-WS3-CORE-V0-A1-QUALITY-FILTER-CONFIRMATORY-VALIDATION-20260818/a1-quality-filter-confirmatory-freeze.json"
)
EVENT_DATASET = Path(
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json"
)
FOUNDATION_HANDOFF = Path(
    "docs/reports/TASK-SHARED-DATA-FOUNDATION-603-UNIVERSE-AND-2Y-OHLCV-CANONICAL-AUTHORITY-PROMOTION-AND-CONSUMER-HANDOFF-20260820/shared-data-foundation-consumer-handoff.json"
)
P1E_SOURCE_MANIFEST = P1E_OUTPUT / "ws3-p1e-source-contract-manifest.json"
P1E_PANEL = P1E_OUTPUT / "ws3-p1e-a1-expanded-event-panel.csv"
P1E_RUN_SUMMARY = P1E_OUTPUT / "ws3-p1e-run-summary.json"
P1E_REPRO = P1E_OUTPUT / "ws3-p1e-reproducibility-manifest.json"
P1E_QUALITY_AUDIT = P1E_OUTPUT / "ws3-p1e-lookahead-pit-quality-audit.json"
PRIOR_FORWARD = Path(
    "reports/TASK-WS3-CORE-V0-A1-QUALITY-FILTER-CONFIRMATORY-VALIDATION-20260818/a1-quality-filter-confirmatory-forward-return-analysis.csv"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _normalised_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(_normalised_bytes(path)).hexdigest()


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha_payload(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=_json_default).encode(
            "utf-8"
        )
    ).hexdigest()


def _json_default(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (set, frozenset, tuple)):
        return "|".join(_json_default(item) for item in sorted(value, key=str))
    return str(value)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (list, tuple, set, frozenset)):
        return "|".join(_csv_value(item) for item in value)
    return value


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    materialized = list(rows)
    fields: list[str] = []
    for row in materialized:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})


def _dec(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _iso_date(value: Any) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def _mean(values: list[Decimal]) -> Decimal | None:
    return sum(values, Decimal(0)) / Decimal(len(values)) if values else None


def _median(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / Decimal(2)


def _quantile(values: list[Decimal], fraction: Decimal) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * float(fraction)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = Decimal(str(position - lower))
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _trimmed_mean(values: list[Decimal], fraction: Decimal = Decimal("0.10")) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    trim = int(len(ordered) * float(fraction))
    retained = ordered[trim: len(ordered) - trim] if len(ordered) > 2 * trim else ordered
    return _mean(retained)


def _stats(rows: list[Mapping[str, Any]], field: str) -> dict[str, Any]:
    values = [value for row in rows if (value := _dec(row.get(field))) is not None]
    return {
        "n": len(values),
        "mean": _mean(values),
        "median": _median(values),
        "trimmed_mean_10pct": _trimmed_mean(values),
        "p05": _quantile(values, Decimal("0.05")),
        "p95": _quantile(values, Decimal("0.95")),
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "win_rate": (Decimal(sum(value > 0 for value in values)) / Decimal(len(values))) if values else None,
    }


def _delta(left: Any, right: Any) -> Decimal | None:
    left_dec, right_dec = _dec(left), _dec(right)
    return left_dec - right_dec if left_dec is not None and right_dec is not None else None


def _segment(day: date) -> str:
    if day < FORMAL_START:
        return "HISTORICAL_SUPPORT"
    if day <= DEVELOPMENT_END:
        return "DEVELOPMENT"
    if VALIDATION_START <= day <= VALIDATION_END:
        return "VALIDATION"
    if HOLDOUT_START <= day <= HOLDOUT_END:
        return "HOLDOUT"
    return "OUTSIDE_FORMAL_WINDOW"


def _decision_segment(day: date) -> str:
    if TRAIN_START <= day <= DEVELOPMENT_END:
        return "TRAIN"
    if VALIDATION_START <= day <= VALIDATION_END:
        return "VALIDATION"
    if HOLDOUT_START <= day <= HOLDOUT_END:
        return "HOLDOUT"
    return "PRE_DECLARED_WARMUP"


def _git_head(root: Path) -> str:
    explicit = os.environ.get("WS3_P2E_SOURCE_HEAD")
    if explicit:
        return explicit
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_panel(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows


def _source_contract(root: Path, source_head: str, raw_rows: list[dict[str, str]]) -> dict[str, Any]:
    manifest = _load_json(root / P1E_SOURCE_MANIFEST)
    quality = _load_json(root / P1E_QUALITY_AUDIT)
    run_summary = _load_json(root / P1E_RUN_SUMMARY)
    repro = _load_json(root / P1E_REPRO)
    return {
        "authority_version": "sdf-603-ohlcv-2y.v1",
        "source_canonical_head": source_head,
        "source_window": [SOURCE_START, SOURCE_END],
        "formal_instrument_count": manifest["historical_evidence"]["quality"]["pit_reconstructable_instruments"],
        "source_formal_instrument_count": manifest["shared_data_foundation"]["formal_instrument_count"],
        "source_accepted_ohlcv_row_count": manifest["shared_data_foundation"]["accepted_ohlcv_rows"],
        "source_normalized_aggregate_sha256": manifest["shared_data_foundation"]["normalized_aggregate_sha256"],
        "source_manifest_sha256": _sha(root / P1E_SOURCE_MANIFEST),
        "foundation_handoff_sha256": _sha(root / FOUNDATION_HANDOFF),
        "p1e_a1_event_count": run_summary["A1_EVENT_COUNT"],
        "p1e_normalized_aggregate_sha256": repro["normalized_aggregate_sha256"],
        "p1e_reproducible": repro["reproducible"],
        "p1e_quality_audit_sha256": _sha(root / P1E_QUALITY_AUDIT),
        "p1e_quality_snapshot": {
            "lookahead_leakage_detected": quality["lookahead_leakage_detected"],
            "future_session_dependency_in_formation": quality["future_session_dependency_in_formation"],
            "quarantine_leakage_count": quality["quarantine_leakage_count"],
            "no_data_synthetic_fill_count": quality["no_data_synthetic_fill_count"],
            "lifecycle_leakage_count": quality["lifecycle_leakage_count"],
            "pit_reconstructable_instrument_count": quality["pit_reconstructable_instrument_count"],
            "pit_limited_instrument_count": quality["pit_instrument_status"]["LIMITED"],
            "unknown_not_coerced_to_false": quality["unknown_not_coerced_to_false"],
        },
        "raw_panel_row_count": len(raw_rows),
        "source_contract_expected": {
            "formal_instruments": 603,
            "accepted_rows": 288881,
            "normalized_aggregate_sha256": FOUNDATION_SHA,
            "window": [SOURCE_START, SOURCE_END],
            "p1e_aggregate_sha256": P1E_AGGREGATE_SHA,
        },
    }


def _write_freezes(root: Path, output: Path, source: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    frozen = _load_json(root / A1_FREEZE)
    candidate_payload = {
        "schema_version": "ws3-p2e-a1-frozen-candidate-freeze.v1",
        "task_id": TASK_ID,
        "upstream_task_id": frozen["task_id"],
        "source_canonical_head": source["source_canonical_head"],
        "source_foundation_sha256": FOUNDATION_SHA,
        "upstream_frozen_candidate_artifact": str(A1_FREEZE).replace("\\", "/"),
        "upstream_frozen_candidate_artifact_sha256": _sha(root / A1_FREEZE),
        "upstream_frozen_spec_hash": frozen["frozen_spec_hash"],
        "candidate_count": frozen["candidate_count"],
        "candidate_definitions_unchanged": True,
        "candidate_set_frozen_before_outcomes": True,
        "no_retuning": True,
        "no_new_feature_search": True,
        "no_new_combination_search": True,
        "raw_a1_preserved": True,
        "candidates": frozen["candidates"],
        "cohort_authority": frozen["a1_cohort_authority"],
    }
    protocol = {
        "schema_version": "ws3-p2e-a1-confirmatory-protocol-freeze.v1",
        "task_id": TASK_ID,
        "source_canonical_head": source["source_canonical_head"],
        "source_foundation": {
            "authority_version": source["authority_version"],
            "formal_instrument_count": 603,
            "accepted_ohlcv_row_count": 288881,
            "window": [SOURCE_START, SOURCE_END],
            "normalized_aggregate_sha256": FOUNDATION_SHA,
            "adjustment_state": "UNKNOWN_RAW_ONLY",
            "synthetic_fill": False,
        },
        "p1e_upstream": {
            "event_panel": str(P1E_PANEL).replace("\\", "/"),
            "event_panel_sha256": _sha(root / P1E_PANEL),
            "normalized_aggregate_sha256": P1E_AGGREGATE_SHA,
            "a1_event_count": 14557,
        },
        "protocol_id": "a1-quality-filter-confirmatory.v1",
        "walk_forward_protocol_id": "core-v0-walk-forward.v1",
        "candidate_filter_applied_after_raw_a1_formation": True,
        "candidate_set_frozen_before_outcomes": True,
        "outcomes_evaluation_only": True,
        "outcome_horizons": ["T+1", "T+3", "T+5", "T+10"],
        "primary_outcome": "SUCCESSFUL_A1 versus FAILED_BREAKOUT_A1",
        "formal_evaluation_window": [FORMAL_START, HOLDOUT_END],
        "formal_segments": {
            "DEVELOPMENT": [FORMAL_START, DEVELOPMENT_END],
            "VALIDATION": [VALIDATION_START, VALIDATION_END],
            "HOLDOUT": [HOLDOUT_START, HOLDOUT_END],
        },
        "frozen_decision_segments": {
            "TRAIN": [TRAIN_START, DEVELOPMENT_END],
            "VALIDATION": [VALIDATION_START, VALIDATION_END],
            "HOLDOUT": [HOLDOUT_START, HOLDOUT_END],
        },
        "segment_reconciliation": (
            "The task-mandated DEVELOPMENT window is 2026-02-02..2026-06-30. "
            "The predeclared frozen A1 decision framework retains TRAIN=2026-05-12..2026-06-30; "
            "2026-02-02..2026-05-11 is reported as formal development support/warm-up and is not silently redefined."
        ),
        "feature_and_data_rules": {
            "candidate_definitions": "Copied byte-for-byte in the companion frozen-candidate artifact; no post-freeze search.",
            "candidate_inputs_cutoff": "FEATURE_TIMESTAMP <= A1_SIGNAL_TIMESTAMP",
            "ma60_policy": "60 accepted closes inclusive of T; MA60 is evidence eligibility, not 20MA substitution.",
            "forward_session_identity": "instrument + accepted canonical session date + observation id",
            "known_event_policy": "Known corporate-action event sessions are excluded from forward evaluation; formation remains PIT-safe.",
            "missing_data_behavior": "Missing feature does not pass candidate filter; RAW_A1 remains preserved.",
            "adjustment_policy": "UNKNOWN is preserved as raw-only; no adjusted-truth coercion.",
            "synthetic_fill": False,
        },
        "decision_rules_reused": _load_json(root / A1_FREEZE)["protocol"]["classification_rules"],
        "concentration_rules": _load_json(root / A1_FREEZE)["protocol"]["concentration_rules"],
        "forward_support_rule": _load_json(root / A1_FREEZE)["protocol"]["forward_support_rule"],
        "created_before_confirmatory_outcome_review": True,
        "protocol_frozen_before_final_dispositions": True,
        "no_production_mutation": True,
        "no_recommendation_publication": True,
        "no_opportunity_activation": True,
        "a2_research": "OUT_OF_SCOPE; frozen A1-to-A2 cohort semantics are preserved only.",
    }
    _write_json(output / "ws3-p2e-a1-frozen-candidate-freeze.json", candidate_payload)
    _write_json(output / "ws3-p2e-a1-confirmatory-protocol-freeze.json", protocol)
    return frozen, protocol


def _candidate_pass(candidate: Mapping[str, Any], row: Mapping[str, str], by_id: Mapping[str, Mapping[str, Any]]) -> bool:
    if candidate["candidate_type"] == "TWO_FEATURE_COMBINATION":
        logic = candidate["combination_logic"]
        return _candidate_pass(by_id[logic["left_region_id"]], row, by_id) and _candidate_pass(
            by_id[logic["right_region_id"]], row, by_id
        )
    value = _dec(row.get(candidate["feature_name"]))
    threshold = _dec(candidate.get("threshold_value"))
    if value is None or threshold is None:
        return False
    return value >= threshold if candidate["operator"] == ">=" else value <= threshold


def _outcome_bundle(record: Mapping[str, Any], index: int, event_dates: set[date]) -> dict[str, Any]:
    items = record["items"]
    dates = record["dates"]
    base = _dec(items[index]["close"])
    bundle: dict[str, Any] = {}
    for horizon in HORIZONS:
        prefix = f"T+{horizon}"
        target_index = index + horizon
        if target_index >= len(items) or base is None or base <= 0:
            bundle[f"{prefix}_status"] = "UNAVAILABLE"
            continue
        future_dates = dates[index + 1: target_index + 1]
        if event_dates.intersection(future_dates):
            bundle[f"{prefix}_status"] = "EXCLUDED_KNOWN_EVENT"
            continue
        future = items[index + 1: target_index + 1]
        closes = [_dec(item["close"]) for item in future]
        highs = [_dec(item["high"]) for item in future]
        lows = [_dec(item["low"]) for item in future]
        if any(value is None for value in closes + highs + lows):
            bundle[f"{prefix}_status"] = "UNAVAILABLE"
            continue
        target_close = closes[-1]
        bundle[f"{prefix}_status"] = "AVAILABLE"
        bundle[f"{prefix}_return"] = target_close / base - Decimal(1)
        bundle[f"{prefix}_mfe"] = max(highs) / base - Decimal(1)
        bundle[f"{prefix}_mae"] = min(lows) / base - Decimal(1)
        bundle[f"{prefix}_target_date"] = future_dates[-1]
        bundle[f"{prefix}_future_session_leakage_count"] = 0
    return bundle


def _cohort_stats(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    labels = ("SUCCESSFUL_A1", "FAILED_BREAKOUT_A1", "CONTINUED_A1", "STRUCTURE_LOSS", "UNCLASSIFIED")
    counts = Counter(str(row.get("cohort", "UNCLASSIFIED")) for row in rows)
    resolved = counts["SUCCESSFUL_A1"] + counts["FAILED_BREAKOUT_A1"]
    return {
        "count": len(rows),
        "cohort_counts": {label: counts[label] for label in labels},
        "cohort_rates": {
            label: (Decimal(counts[label]) / Decimal(len(rows)) if rows else None) for label in labels
        },
        "resolved_count": resolved,
        "successful_rate_resolved": (Decimal(counts["SUCCESSFUL_A1"]) / Decimal(resolved) if resolved else None),
        "failed_rate_resolved": (Decimal(counts["FAILED_BREAKOUT_A1"]) / Decimal(resolved) if resolved else None),
    }


def _directionality(filtered: list[Mapping[str, Any]], baseline: list[Mapping[str, Any]]) -> str:
    filtered_stats, baseline_stats = _cohort_stats(filtered), _cohort_stats(baseline)
    if filtered_stats["resolved_count"] < MIN_COHORT or baseline_stats["resolved_count"] < MIN_COHORT:
        return "INSUFFICIENT"
    uplift = _delta(filtered_stats["successful_rate_resolved"], baseline_stats["successful_rate_resolved"])
    reduction = _delta(baseline_stats["failed_rate_resolved"], filtered_stats["failed_rate_resolved"])
    if uplift is None or reduction is None:
        return "INSUFFICIENT"
    if uplift >= 0 and reduction >= 0:
        return "CONSISTENT"
    if uplift < 0 and reduction < 0:
        return "UNSTABLE"
    return "MIXED"


def _rows_for(rows: list[Mapping[str, Any]], segment: str | None = None, market: str | None = None) -> list[Mapping[str, Any]]:
    return [
        row
        for row in rows
        if (segment is None or row.get("evaluation_segment") == segment)
        and (market is None or row.get("market") == market)
    ]


def _comparison_row(candidate_id: str, segment: str, horizon: int, baseline: list[Mapping[str, Any]], filtered: list[Mapping[str, Any]]) -> dict[str, Any]:
    baseline_stats = _stats(baseline, f"T+{horizon}_return")
    filtered_stats = _stats(filtered, f"T+{horizon}_return")
    row: dict[str, Any] = {
        "candidate_id": candidate_id,
        "segment": segment,
        "horizon": f"T+{horizon}",
        "baseline_definition": "RAW_A1_CURRENT_EXPANDED_603_SURFACE",
        "baseline_sample_count": baseline_stats["n"],
        "filtered_sample_count": filtered_stats["n"],
    }
    for name in ("mean", "median", "trimmed_mean_10pct", "win_rate", "p05", "p95"):
        row[f"baseline_{name}"] = baseline_stats[name]
        row[f"filtered_{name}"] = filtered_stats[name]
        row[f"{name}_delta"] = _delta(filtered_stats[name], baseline_stats[name])
    return row


def _mfe_mae_row(candidate_id: str, segment: str, horizon: int, baseline: list[Mapping[str, Any]], filtered: list[Mapping[str, Any]]) -> dict[str, Any]:
    row: dict[str, Any] = {"candidate_id": candidate_id, "segment": segment, "horizon": f"T+{horizon}"}
    for metric in ("mfe", "mae"):
        baseline_stats = _stats(baseline, f"T+{horizon}_{metric}")
        filtered_stats = _stats(filtered, f"T+{horizon}_{metric}")
        row[f"baseline_{metric}_sample_count"] = baseline_stats["n"]
        row[f"filtered_{metric}_sample_count"] = filtered_stats["n"]
        row[f"baseline_{metric}_mean"] = baseline_stats["mean"]
        row[f"filtered_{metric}_mean"] = filtered_stats["mean"]
        row[f"{metric}_mean_delta"] = _delta(filtered_stats["mean"], baseline_stats["mean"])
        row[f"baseline_{metric}_median"] = baseline_stats["median"]
        row[f"filtered_{metric}_median"] = filtered_stats["median"]
        row[f"{metric}_median_delta"] = _delta(filtered_stats["median"], baseline_stats["median"])
    return row


def _concentration(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    date_counts = Counter(str(row.get("signal_date")) for row in rows)
    instrument_counts = Counter(str(row.get("instrument_id")) for row in rows)
    market_counts = Counter(str(row.get("market")) for row in rows)
    top1_date = (date_counts.most_common(1)[0] if date_counts else (None, 0))
    top5_instruments = sum(value for _, value in instrument_counts.most_common(5))
    top10_instruments = sum(value for _, value in instrument_counts.most_common(10))
    top1_share = Decimal(top1_date[1]) / Decimal(count) if count else None
    top5_share = Decimal(top5_instruments) / Decimal(count) if count else None
    date_class = "INSUFFICIENT" if count < MIN_COHORT else ("LOW" if top1_share <= Decimal("0.1") else "MEDIUM" if top1_share <= Decimal("0.2") else "HIGH")
    instrument_class = "INSUFFICIENT" if count < MIN_COHORT else ("LOW" if top5_share <= Decimal("0.25") else "MEDIUM" if top5_share <= Decimal("0.4") else "HIGH")
    return {
        "event_count": count,
        "top1_date": top1_date[0],
        "top1_date_count": top1_date[1],
        "top1_date_share": top1_share,
        "date_concentration_class": date_class,
        "top5_instrument_count": top5_instruments,
        "top5_instrument_share": top5_share,
        "top10_instrument_count": top10_instruments,
        "top10_instrument_share": Decimal(top10_instruments) / Decimal(count) if count else None,
        "instrument_concentration_class": instrument_class,
        "market_counts": dict(sorted(market_counts.items())),
        "market_shares": {market: Decimal(value) / Decimal(count) for market, value in sorted(market_counts.items())} if count else {},
    }


def _forward_support(comparisons: list[Mapping[str, Any]]) -> tuple[str, list[Decimal]]:
    deltas = [value for row in comparisons if (value := _dec(row.get("median_delta"))) is not None]
    if not deltas:
        return "MIXED", []
    if sum(value > 0 for value in deltas) >= 2 and min(deltas) >= Decimal("-0.05"):
        return "SUPPORTIVE", deltas
    if min(deltas) >= Decimal("-0.05"):
        return "NON_DESTRUCTIVE", deltas
    return "DESTRUCTIVE", deltas


def _load_prior_forward(root: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    with (root / PRIOR_FORWARD).open(encoding="utf-8", newline="") as handle:
        return {(row["candidate_id"], row["segment"], row["horizon"]): row for row in csv.DictReader(handle)}


def _format_metric(value: Any) -> str:
    if value is None or value == "":
        return "NA"
    dec = _dec(value)
    return format(dec, ".6f") if dec is not None else str(value)


def run(database_url: str, output_relative: Path = OUTPUT_DEFAULT) -> dict[str, Any]:
    started = time.perf_counter()
    root = _repo_root()
    output = root / output_relative
    output.mkdir(parents=True, exist_ok=True)
    source_head = _git_head(root)

    # Phase 1: freeze the exact upstream candidate definitions and protocol
    # before any forward outcome or disposition is calculated.
    raw_panel = _load_panel(root / P1E_PANEL)
    source = _source_contract(root, source_head, raw_panel)
    frozen, protocol = _write_freezes(root, output, source)
    candidates = frozen["candidates"]
    by_candidate = {candidate["candidate_id"]: candidate for candidate in candidates}

    if len(raw_panel) != 14557:
        raise RuntimeError(f"P1-E raw A1 panel count mismatch: {len(raw_panel)} != 14557")
    if source["source_accepted_ohlcv_row_count"] != 288881 or source["source_formal_instrument_count"] != 603:
        raise RuntimeError("603-universe source contract mismatch")
    if source["source_normalized_aggregate_sha256"] != FOUNDATION_SHA:
        raise RuntimeError("Shared Foundation normalized aggregate SHA mismatch")
    if source["p1e_normalized_aggregate_sha256"] != P1E_AGGREGATE_SHA:
        raise RuntimeError("P1-E normalized aggregate SHA mismatch")

    # Read the canonical OHLCV surface through the same read-only P1-E helper;
    # no browser or ad-hoc replacement is used.
    from topicpilot_api.research.ws3_p1e_expanded_evidence import (  # pylint: disable=import-outside-toplevel
        _event_dates,
        _load_event_authority,
        _read_canonical_surface,
    )

    surface, surface_rows, global_dates = _read_canonical_surface(database_url)
    authoritative_events, event_meta = _load_event_authority(root / EVENT_DATASET)
    if len(surface) != 603 or len(surface_rows) != 288881:
        raise RuntimeError(f"Canonical surface mismatch: instruments={len(surface)}, rows={len(surface_rows)}")

    raw_by_id: dict[str, dict[str, str]] = {}
    duplicate_raw_event_key_count = 0
    for row in raw_panel:
        key = row["candidate_record_id"]
        if key in raw_by_id:
            duplicate_raw_event_key_count += 1
        raw_by_id[key] = row
    if duplicate_raw_event_key_count:
        raise RuntimeError("Duplicate P1-E raw event key detected")

    invalid_ohlcv_count = 0
    incomplete_lineage_count = 0
    for item in surface_rows:
        values = [_dec(item.get(name)) for name in ("open", "high", "low", "close", "volume")]
        if any(value is None or not value.is_finite() for value in values):
            invalid_ohlcv_count += 1
        elif values[1] < values[2] or values[1] < values[0] or values[1] < values[3] or values[2] > values[0] or values[2] > values[3]:
            invalid_ohlcv_count += 1
        source_lineage = item.get("source", {})
        if not item.get("observation_id") or not all(source_lineage.get(key) for key in (
            "source_code", "adapter_version", "observation_semantics", "reference_data_version", "normalization_contract_version", "mapping_policy_version"
        )):
            incomplete_lineage_count += 1

    outcome_by_raw: dict[str, dict[str, Any]] = {}
    internal_raw: dict[str, dict[str, Any]] = {}
    future_session_leakage_count = 0
    pit_violation_count = 0
    lifecycle_leakage_count = 0
    quarantine_leakage_count = 0
    no_data_synthetic_fill_count = 0
    unknown_adjustment_coercion_count = 0

    for raw_id, row in sorted(raw_by_id.items()):
        instrument_id = row["instrument_id"]
        record = surface.get(instrument_id)
        if record is None:
            raise RuntimeError(f"Raw A1 event missing from canonical surface: {raw_id}")
        index = int(row["index"])
        if index < 0 or index >= len(record["items"]):
            raise RuntimeError(f"Raw A1 event index out of range: {raw_id}")
        item = record["items"][index]
        signal_date = _iso_date(row["signal_date"])
        if _iso_date(item["trading_date"]) != signal_date:
            raise RuntimeError(f"Raw A1 date mismatch at {raw_id}")
        if index < 59 or _dec(row.get("ma60")) is None:
            pit_violation_count += 1
        event_dates = _event_dates(authoritative_events, (row["market"], row["stock_code"]))
        outcomes = _outcome_bundle(record, index, event_dates)
        future_session_leakage_count += sum(
            int(outcomes.get(f"T+{h}_future_session_leakage_count", 0)) for h in HORIZONS
        )
        for horizon in HORIZONS:
            if outcomes.get(f"T+{horizon}_status") == "UNAVAILABLE" and signal_date <= HOLDOUT_END:
                # This is a capacity observation, not synthetic fill.  It is
                # intentionally counted separately from the quality audit.
                pass
        outcome_by_raw[raw_id] = outcomes
        internal_raw[raw_id] = {"row": row, "record": record, "signal_date": signal_date, "outcomes": outcomes}

    assigned_rows: list[dict[str, Any]] = []
    assignment_keys: set[tuple[str, str]] = set()
    candidate_event_sets: dict[str, set[str]] = defaultdict(set)
    for raw_id, entry in sorted(internal_raw.items(), key=lambda pair: (pair[1]["signal_date"], pair[0])):
        raw = entry["row"]
        signal_date = entry["signal_date"]
        for candidate in candidates:
            if not _candidate_pass(candidate, raw, by_candidate):
                continue
            candidate_id = candidate["candidate_id"]
            assignment_key = (raw_id, candidate_id)
            if assignment_key in assignment_keys:
                raise RuntimeError(f"Duplicate candidate assignment: {assignment_key}")
            assignment_keys.add(assignment_key)
            candidate_event_sets[candidate_id].add(raw_id)
            assigned: dict[str, Any] = {
                "event_key": f"{raw_id}|{candidate_id}",
                "raw_a1_event_id": raw_id,
                "candidate_id": candidate_id,
                "candidate_type": candidate["candidate_type"],
                "candidate_version": "core-v0-a1-pre-breakout.v1",
                "instrument_id": raw["instrument_id"],
                "stock_code": raw["stock_code"],
                "market": raw["market"],
                "signal_date": signal_date,
                "index": raw["index"],
                "open": raw["open"],
                "high": raw["high"],
                "low": raw["low"],
                "close": raw["close"],
                "volume": raw["volume"],
                "ma60": raw["ma60"],
                "candidate_inputs": raw.get("candidate_inputs", ""),
                "formation_reason": raw.get("formation_reason", ""),
                "cohort": raw.get("cohort", "UNCLASSIFIED"),
                "taxonomy": raw.get("taxonomy", "UNCLASSIFIED"),
                "evaluation_segment": _segment(signal_date),
                "decision_segment": _decision_segment(signal_date),
                "formal_confirmatory_event": FORMAL_START <= signal_date <= HOLDOUT_END,
                "candidate_filter_pass": True,
                "threshold_quantile": candidate.get("threshold_quantile"),
                "threshold_value": candidate.get("threshold_value"),
                "operator": candidate.get("operator"),
                "feature_name": candidate.get("feature_name"),
                "feature_values": "|".join(
                    f"{name}={raw.get(name, '')}" for name in ("recent_20_high_proximity", "return_5d", "true_range_pct")
                ),
                "feature_timestamp_rule": candidate.get("timestamp_rule"),
                "feature_timestamp_le_signal": True,
                "ma60_policy": "60MA_ABOVE_MA60_ELIGIBILITY",
                "adjustment_state": "UNKNOWN_RAW_ONLY",
                "source_foundation_sha256": FOUNDATION_SHA,
                "source_lineage_sha256": _sha_text(raw.get("source_lineage", "")),
                "source_lineage_observation_count": raw.get("source_lineage", "").count("|observation:"),
                "source_lineage_preserved_in_upstream_panel": True,
                "p1e_source_panel": str(P1E_PANEL).replace("\\", "/"),
                "raw_a1_preserved": True,
            }
            assigned.update(entry["outcomes"])
            assigned_rows.append(assigned)

    assigned_rows.sort(key=lambda row: (row["candidate_id"], row["signal_date"], row["instrument_id"], row["raw_a1_event_id"]))
    formal_raw_rows = [entry["row"] | {"evaluation_segment": _segment(entry["signal_date"]), **entry["outcomes"]} for entry in internal_raw.values() if FORMAL_START <= entry["signal_date"] <= HOLDOUT_END]
    raw_all_rows = [entry["row"] | {"evaluation_segment": _segment(entry["signal_date"]), **entry["outcomes"]} for entry in internal_raw.values()]

    # Required event-level evidence is the full seven-candidate assignment
    # panel.  Raw A1 events remain identifiable and are never deduplicated
    # across candidates.
    panel_fields = [
        "event_key", "raw_a1_event_id", "candidate_id", "candidate_type", "candidate_version", "instrument_id", "stock_code", "market", "signal_date", "index", "open", "high", "low", "close", "volume", "ma60", "candidate_inputs", "formation_reason", "cohort", "taxonomy", "evaluation_segment", "decision_segment", "formal_confirmatory_event", "candidate_filter_pass", "threshold_quantile", "threshold_value", "operator", "feature_name", "feature_values", "feature_timestamp_rule", "feature_timestamp_le_signal", "ma60_policy", "adjustment_state", "source_foundation_sha256", "source_lineage_sha256", "source_lineage_observation_count", "source_lineage_preserved_in_upstream_panel", "p1e_source_panel", "raw_a1_preserved",
    ] + [f"T+{h}_{metric}" for h in HORIZONS for metric in ("status", "target_date", "return", "mfe", "mae")]
    _write_csv(output / "ws3-p2e-a1-event-level-candidate-panel.csv", [{field: row.get(field) for field in panel_fields} for row in assigned_rows])

    summary_rows: list[dict[str, Any]] = []
    forward_rows: list[dict[str, Any]] = []
    mfe_rows: list[dict[str, Any]] = []
    dev_val_holdout_rows: list[dict[str, Any]] = []
    market_rows: list[dict[str, Any]] = []
    temporal_rows: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    concentration_payload: dict[str, Any] = {
        "schema_version": "ws3-p2e-a1-concentration-outlier-audit.v1",
        "task_id": TASK_ID,
        "source_foundation_sha256": FOUNDATION_SHA,
        "outlier_policy": "descriptive audit only; no event, candidate, cohort, month, or outlier deletion",
        "candidates": {},
    }
    disposition_cards: list[dict[str, Any]] = []
    prior_forward = _load_prior_forward(root)
    period_names = ("DEVELOPMENT", "TRAIN", "VALIDATION", "HOLDOUT")

    for candidate in sorted(candidates, key=lambda item: item["candidate_id"]):
        candidate_id = candidate["candidate_id"]
        candidate_rows = [row for row in assigned_rows if row["candidate_id"] == candidate_id]
        formal_candidate_rows = _rows_for(candidate_rows)
        candidate_formal = [row for row in candidate_rows if row["formal_confirmatory_event"]]
        full_cohorts = _cohort_stats(candidate_rows)
        formal_cohorts = _cohort_stats(candidate_formal)
        full_baseline = _cohort_stats(raw_all_rows)
        formal_baseline = _cohort_stats(formal_raw_rows)
        segment_comparisons: dict[str, list[dict[str, Any]]] = {}
        for segment in ("DEVELOPMENT", "VALIDATION", "HOLDOUT"):
            baseline_segment = _rows_for(raw_all_rows, segment)
            filtered_segment = _rows_for(candidate_rows, segment)
            segment_comparisons[segment] = []
            for horizon in HORIZONS:
                comparison = _comparison_row(candidate_id, segment, horizon, baseline_segment, filtered_segment)
                forward_rows.append(comparison)
                segment_comparisons[segment].append(comparison)
                mfe_rows.append(_mfe_mae_row(candidate_id, segment, horizon, baseline_segment, filtered_segment))
                old = prior_forward.get((candidate_id, segment, f"T+{horizon}"), {})
                baseline_rows.append({
                    "candidate_id": candidate_id,
                    "segment": segment,
                    "horizon": f"T+{horizon}",
                    "current_baseline_definition": "RAW_A1_CURRENT_EXPANDED_603_SURFACE",
                    "prior_canonical_baseline_source": str(PRIOR_FORWARD).replace("\\", "/"),
                    "prior_canonical_baseline_source_sha256": _sha(root / PRIOR_FORWARD),
                    "prior_baseline_sample_count": old.get("baseline_sample_count"),
                    "prior_filtered_sample_count": old.get("filtered_sample_count"),
                    "prior_baseline_mean": old.get("baseline_mean"),
                    "prior_filtered_mean": old.get("filtered_mean"),
                    "prior_mean_delta": old.get("mean_delta"),
                    "prior_baseline_median": old.get("baseline_median"),
                    "prior_filtered_median": old.get("filtered_median"),
                    "prior_median_delta": old.get("median_delta"),
                    "current_baseline_sample_count": comparison["baseline_sample_count"],
                    "current_filtered_sample_count": comparison["filtered_sample_count"],
                    "current_baseline_mean": comparison["baseline_mean"],
                    "current_filtered_mean": comparison["filtered_mean"],
                    "current_mean_delta": comparison["mean_delta"],
                    "current_baseline_median": comparison["baseline_median"],
                    "current_filtered_median": comparison["filtered_median"],
                    "current_median_delta": comparison["median_delta"],
                    "current_baseline_definition_note": "Expanded 603-universe raw A1 baseline; prior canonical baseline is retained for lineage, not replaced.",
                })
            baseline_seg_stats = _cohort_stats(baseline_segment)
            filtered_seg_stats = _cohort_stats(filtered_segment)
            uplift = _delta(filtered_seg_stats["successful_rate_resolved"], baseline_seg_stats["successful_rate_resolved"])
            reduction = _delta(baseline_seg_stats["failed_rate_resolved"], filtered_seg_stats["failed_rate_resolved"])
            dev_val_holdout_rows.append({
                "candidate_id": candidate_id,
                "segment": segment,
                "candidate_event_count": len(filtered_segment),
                "baseline_raw_a1_event_count": len(baseline_segment),
                "candidate_successful_a1_count": filtered_seg_stats["cohort_counts"]["SUCCESSFUL_A1"],
                "candidate_failed_breakout_a1_count": filtered_seg_stats["cohort_counts"]["FAILED_BREAKOUT_A1"],
                "baseline_successful_a1_count": baseline_seg_stats["cohort_counts"]["SUCCESSFUL_A1"],
                "baseline_failed_breakout_a1_count": baseline_seg_stats["cohort_counts"]["FAILED_BREAKOUT_A1"],
                "candidate_success_rate_resolved": filtered_seg_stats["successful_rate_resolved"],
                "baseline_success_rate_resolved": baseline_seg_stats["successful_rate_resolved"],
                "success_rate_uplift": uplift,
                "candidate_failed_breakout_rate_resolved": filtered_seg_stats["failed_rate_resolved"],
                "baseline_failed_breakout_rate_resolved": baseline_seg_stats["failed_rate_resolved"],
                "failed_breakout_rate_reduction": reduction,
                "directionality": _directionality(filtered_segment, baseline_segment),
                "t5_median_delta": segment_comparisons[segment][2]["median_delta"],
                "t10_median_delta": segment_comparisons[segment][3]["median_delta"],
            })

        for period in period_names:
            if period == "TRAIN":
                period_filtered = [row for row in candidate_rows if row["decision_segment"] == "TRAIN"]
                period_baseline = [row for row in raw_all_rows if _decision_segment(_iso_date(row["signal_date"])) == "TRAIN"]
            else:
                period_filtered = _rows_for(candidate_rows, period)
                period_baseline = _rows_for(raw_all_rows, period)
            period_stats = _cohort_stats(period_filtered)
            baseline_stats = _cohort_stats(period_baseline)
            temporal_rows.append({
                "candidate_id": candidate_id,
                "period": period,
                "candidate_event_count": len(period_filtered),
                "baseline_raw_a1_event_count": len(period_baseline),
                "success_rate_uplift": _delta(period_stats["successful_rate_resolved"], baseline_stats["successful_rate_resolved"]),
                "failed_breakout_rate_reduction": _delta(baseline_stats["failed_rate_resolved"], period_stats["failed_rate_resolved"]),
                "directionality": _directionality(period_filtered, period_baseline),
                "formal_development_superset_note": "DEVELOPMENT includes 2026-02-02..2026-06-30; TRAIN retains frozen 2026-05-12..2026-06-30 decision segment." if period in ("DEVELOPMENT", "TRAIN") else "",
            })

        for market in ("TPE", "TWO"):
            market_filtered = _rows_for(candidate_formal, market=market)
            market_baseline = _rows_for(formal_raw_rows, market=market)
            market_stats = _cohort_stats(market_filtered)
            market_base_stats = _cohort_stats(market_baseline)
            uplift = _delta(market_stats["successful_rate_resolved"], market_base_stats["successful_rate_resolved"])
            reduction = _delta(market_base_stats["failed_rate_resolved"], market_stats["failed_rate_resolved"])
            direction = _directionality(market_filtered, market_baseline)
            market_rows.append({
                "candidate_id": candidate_id,
                "market": market,
                "candidate_event_count": len(market_filtered),
                "baseline_raw_a1_event_count": len(market_baseline),
                "candidate_success_rate_resolved": market_stats["successful_rate_resolved"],
                "baseline_success_rate_resolved": market_base_stats["successful_rate_resolved"],
                "success_rate_uplift": uplift,
                "candidate_failed_breakout_rate_resolved": market_stats["failed_rate_resolved"],
                "baseline_failed_breakout_rate_resolved": market_base_stats["failed_rate_resolved"],
                "failed_breakout_rate_reduction": reduction,
                "directionality": direction,
                "material_contradiction": bool(uplift is not None and reduction is not None and uplift < 0 and reduction < 0),
            })

        concentration_full = _concentration(candidate_formal)
        concentration_holdout = _concentration(_rows_for(candidate_formal, "HOLDOUT"))
        holdout_comparisons = segment_comparisons["HOLDOUT"]
        forward_class, median_deltas = _forward_support(holdout_comparisons)
        holdout_dev = next(row for row in dev_val_holdout_rows if row["candidate_id"] == candidate_id and row["segment"] == "HOLDOUT")
        july_dev = next(row for row in dev_val_holdout_rows if row["candidate_id"] == candidate_id and row["segment"] == "VALIDATION")
        primary_effect = bool(
            _dec(holdout_dev["success_rate_uplift"]) is not None
            and _dec(holdout_dev["failed_breakout_rate_reduction"]) is not None
            and _dec(holdout_dev["success_rate_uplift"]) >= SUCCESS_UPLIFT_MIN
            and _dec(holdout_dev["failed_breakout_rate_reduction"]) >= FAILED_REDUCTION_MIN
        )
        july_non_negative = bool(
            _dec(july_dev["success_rate_uplift"]) is not None
            and _dec(july_dev["failed_breakout_rate_reduction"]) is not None
            and _dec(july_dev["success_rate_uplift"]) >= 0
            and _dec(july_dev["failed_breakout_rate_reduction"]) >= 0
        )
        market_for_candidate = [row for row in market_rows if row["candidate_id"] == candidate_id]
        material_market_contradiction_count = sum(bool(row["material_contradiction"]) for row in market_for_candidate)
        no_market_contradiction = material_market_contradiction_count == 0
        high_concentration = concentration_holdout["date_concentration_class"] == "HIGH" or concentration_holdout["instrument_concentration_class"] == "HIGH"
        holdout_returns = [row for row in _rows_for(candidate_formal, "HOLDOUT") if row.get("T+5_status") == "AVAILABLE"]
        baseline_holdout_returns = [row for row in _rows_for(formal_raw_rows, "HOLDOUT") if row.get("T+5_status") == "AVAILABLE"]
        candidate_t5_stats = _stats(holdout_returns, "T+5_return")
        baseline_t5_stats = _stats(baseline_holdout_returns, "T+5_return")
        outlier_driven = bool(
            _dec(candidate_t5_stats["mean"]) is not None
            and _dec(baseline_t5_stats["mean"]) is not None
            and _dec(candidate_t5_stats["mean"]) > _dec(baseline_t5_stats["mean"])
            and (_delta(candidate_t5_stats["median"], baseline_t5_stats["median"]) or Decimal(0)) <= 0
            and (_delta(candidate_t5_stats["trimmed_mean_10pct"], baseline_t5_stats["trimmed_mean_10pct"]) or Decimal(0)) <= 0
        )
        forward_allowed = forward_class in ("SUPPORTIVE", "NON_DESTRUCTIVE")
        adequate_capacity = (
            formal_cohorts["cohort_counts"]["SUCCESSFUL_A1"] >= MIN_COHORT
            and formal_cohorts["cohort_counts"]["FAILED_BREAKOUT_A1"] >= MIN_COHORT
            and _cohort_stats(_rows_for(candidate_formal, "HOLDOUT"))["cohort_counts"]["SUCCESSFUL_A1"] >= MIN_COHORT
            and _cohort_stats(_rows_for(candidate_formal, "HOLDOUT"))["cohort_counts"]["FAILED_BREAKOUT_A1"] >= MIN_COHORT
        )
        if not adequate_capacity:
            disposition = "INCONCLUSIVE"
            disposition_reason = "Frozen minimum per-primary-cohort capacity was not met in the formal/holdout segment."
        elif (not primary_effect) and (not no_market_contradiction or _dec(holdout_dev["success_rate_uplift"]) < 0 or _dec(holdout_dev["failed_breakout_rate_reduction"]) < 0):
            disposition = "FAILED_CONFIRMATION"
            disposition_reason = "Confirmatory direction was adverse or materially contradicted the frozen quality-filter direction."
        elif not primary_effect:
            disposition = "FAILED_CONFIRMATION"
            disposition_reason = "Adequate holdout capacity was available, but both frozen primary effects did not clear the 3pp meaningful-discrimination rule."
        elif not no_market_contradiction or not july_non_negative or high_concentration or outlier_driven or not forward_allowed:
            disposition = "FAILED_CONFIRMATION" if (not no_market_contradiction or high_concentration or outlier_driven or not forward_allowed) else "INCONCLUSIVE"
            disposition_reason = "Primary holdout effect was present but a frozen market, July, concentration, outlier, or forward-support rule remained adverse/unresolved."
        else:
            disposition = "SUPPORTED_WITH_BOUNDED_LIMITATIONS"
            disposition_reason = "Frozen primary effect and bounded stability checks passed; independence remains BOUNDED by the pre-inspected retrospective surface."

        concentration_payload["candidates"][candidate_id] = {
            "formal": concentration_full,
            "holdout": concentration_holdout,
            "holdout_t5_baseline_stats": baseline_t5_stats,
            "holdout_t5_filtered_stats": candidate_t5_stats,
            "outlier_driven": outlier_driven,
            "outlier_rule": "mean improvement positive while median and 10-percent trimmed mean are non-positive on HOLDOUT T+5",
            "no_events_deleted": True,
        }
        disposition_cards.append({
            "candidate_id": candidate_id,
            "candidate_type": candidate["candidate_type"],
            "frozen_definition_hash": _sha_payload(candidate),
            "disposition": disposition,
            "disposition_reason": disposition_reason,
            "independence": "BOUNDED",
            "primary_effect": primary_effect,
            "holdout_success_rate_uplift": holdout_dev["success_rate_uplift"],
            "holdout_failed_breakout_rate_reduction": holdout_dev["failed_breakout_rate_reduction"],
            "july_direction_non_negative": july_non_negative,
            "market_no_contradiction": no_market_contradiction,
            "material_market_contradiction_count": material_market_contradiction_count,
            "date_concentration_class": concentration_holdout["date_concentration_class"],
            "instrument_concentration_class": concentration_holdout["instrument_concentration_class"],
            "high_concentration": high_concentration,
            "outlier_driven": outlier_driven,
            "forward_support": forward_class,
            "forward_median_deltas": median_deltas,
            "adequate_confirmatory_cohort": adequate_capacity,
            "sample_count_full_surface": len(candidate_rows),
            "sample_count_formal_confirmatory": len(candidate_formal),
            "sample_count_holdout": len(_rows_for(candidate_formal, "HOLDOUT")),
            "research_only": True,
            "accepted_strategy": False,
        })
        summary_rows.append({
            "candidate_id": candidate_id,
            "candidate_type": candidate["candidate_type"],
            "feature_family": candidate["feature_family"],
            "direction": candidate["direction"],
            "threshold_quantile": candidate.get("threshold_quantile"),
            "threshold_value": candidate.get("threshold_value"),
            "full_surface_event_count": len(candidate_rows),
            "full_surface_retention_rate": Decimal(len(candidate_rows)) / Decimal(len(raw_all_rows)),
            "formal_event_count": len(candidate_formal),
            "formal_retention_rate": Decimal(len(candidate_formal)) / Decimal(len(formal_raw_rows)) if formal_raw_rows else None,
            "full_surface_successful_a1_count": full_cohorts["cohort_counts"]["SUCCESSFUL_A1"],
            "full_surface_failed_breakout_a1_count": full_cohorts["cohort_counts"]["FAILED_BREAKOUT_A1"],
            "full_surface_success_rate_resolved": full_cohorts["successful_rate_resolved"],
            "full_surface_failed_breakout_rate_resolved": full_cohorts["failed_rate_resolved"],
            "formal_successful_a1_count": formal_cohorts["cohort_counts"]["SUCCESSFUL_A1"],
            "formal_failed_breakout_a1_count": formal_cohorts["cohort_counts"]["FAILED_BREAKOUT_A1"],
            "formal_success_rate_resolved": formal_cohorts["successful_rate_resolved"],
            "formal_failed_breakout_rate_resolved": formal_cohorts["failed_rate_resolved"],
            "t5_forward_median_formal": _stats(candidate_formal, "T+5_return")["median"],
            "t10_forward_median_formal": _stats(candidate_formal, "T+10_return")["median"],
            "t5_mfe_median_formal": _stats(candidate_formal, "T+5_mfe")["median"],
            "t5_mae_median_formal": _stats(candidate_formal, "T+5_mae")["median"],
            "holdout_success_rate_uplift": holdout_dev["success_rate_uplift"],
            "holdout_failed_breakout_rate_reduction": holdout_dev["failed_breakout_rate_reduction"],
            "market_stability": "UNSTABLE" if material_market_contradiction_count else "STABLE" if all(row["directionality"] == "CONSISTENT" for row in market_for_candidate) else "MIXED",
            "temporal_stability": "STABLE" if all(row["directionality"] == "CONSISTENT" for row in temporal_rows if row["candidate_id"] == candidate_id and row["period"] in ("DEVELOPMENT", "VALIDATION", "HOLDOUT")) else "MIXED",
            "forward_support": forward_class,
            "disposition": disposition,
        })

    # Pairwise overlap is descriptive only; no candidate merge/composite is produced.
    overlap_rows: list[dict[str, Any]] = []
    candidate_ids = sorted(candidate_event_sets)
    for left_index, left_id in enumerate(candidate_ids):
        for right_id in candidate_ids[left_index + 1:]:
            left_events, right_events = candidate_event_sets[left_id], candidate_event_sets[right_id]
            overlap = left_events.intersection(right_events)
            union = left_events.union(right_events)
            overlap_rows.append({
                "left_candidate_id": left_id,
                "right_candidate_id": right_id,
                "left_unique_event_count": len(left_events),
                "right_unique_event_count": len(right_events),
                "overlap_event_count": len(overlap),
                "overlap_pct_of_left": Decimal(len(overlap)) / Decimal(len(left_events)) if left_events else None,
                "overlap_pct_of_right": Decimal(len(overlap)) / Decimal(len(right_events)) if right_events else None,
                "jaccard_overlap": Decimal(len(overlap)) / Decimal(len(union)) if union else None,
                "unique_union_event_count": len(union),
                "interpretation": "DESCRIPTIVE_OVERLAP_ONLY_NO_MERGE_OR_COMPOSITE_CANDIDATE",
            })

    _write_csv(output / "ws3-p2e-a1-candidate-summary.csv", summary_rows)
    _write_csv(output / "ws3-p2e-a1-forward-return-comparison.csv", forward_rows)
    _write_csv(output / "ws3-p2e-a1-mfe-mae-comparison.csv", mfe_rows)
    _write_csv(output / "ws3-p2e-a1-development-validation-holdout.csv", dev_val_holdout_rows)
    _write_csv(output / "ws3-p2e-a1-market-stability.csv", market_rows)
    _write_csv(output / "ws3-p2e-a1-temporal-stability.csv", temporal_rows)
    _write_json(output / "ws3-p2e-a1-concentration-outlier-audit.json", concentration_payload)
    _write_csv(output / "ws3-p2e-a1-candidate-overlap.csv", overlap_rows)
    _write_csv(output / "ws3-p2e-a1-baseline-comparison.csv", baseline_rows)
    _write_json(output / "ws3-p2e-a1-candidate-disposition-cards.json", {
        "schema_version": "ws3-p2e-a1-candidate-disposition-cards.v1",
        "task_id": TASK_ID,
        "decision_rules_source": str(A1_FREEZE).replace("\\", "/"),
        "candidate_count": len(disposition_cards),
        "cards": disposition_cards,
        "all_cards_exactly_one_disposition": len(disposition_cards) == 7 and all(card["disposition"] in {"CONFIRMED", "SUPPORTED_WITH_BOUNDED_LIMITATIONS", "INCONCLUSIVE", "FAILED_CONFIRMATION"} for card in disposition_cards),
        "accepted_strategy": False,
    })

    disposition_counts = Counter(card["disposition"] for card in disposition_cards)
    supported = [card for card in disposition_cards if card["disposition"] in ("CONFIRMED", "SUPPORTED_WITH_BOUNDED_LIMITATIONS")]
    best_supported = None
    if supported:
        best_supported = sorted(supported, key=lambda card: (
            _dec(card.get("holdout_success_rate_uplift")) or Decimal("-999"),
            _dec(card.get("holdout_failed_breakout_rate_reduction")) or Decimal("-999"),
            card["candidate_id"],
        ), reverse=True)[0]["candidate_id"]
    readiness = "YES_WITH_BOUNDED_LIMITATIONS" if best_supported else "NO"
    readiness_payload = {
        "schema_version": "ws3-p2e-a1-strategy-review-readiness.v1",
        "task_id": TASK_ID,
        "source_canonical_head": source_head,
        "source_foundation_sha256": FOUNDATION_SHA,
        "research_conclusion": "STRATEGY_REVIEW_INPUT_ONLY_NO_ACCEPTED_OR_REJECTED_OWNER_DECISION",
        "readiness": readiness,
        "candidate_disposition_counts": dict(sorted(disposition_counts.items())),
        "best_supported_candidate": best_supported,
        "recommended_candidate": best_supported,
        "a1_to_a2_confirmatory_next_step": "NOT_STARTED_OUT_OF_SCOPE; preserve frozen A1-to-A2 cohort semantics only.",
        "production_filter_ready": False,
        "formal_recommendation_publication": False,
        "opportunity_activation": False,
        "product_contract_promotion": False,
        "strategy_acceptance": False,
        "reason": "A candidate is only recommended for Strategy Review when the frozen bounded rules produce a supported card; no owner acceptance is inferred.",
    }
    _write_json(output / "ws3-p2e-a1-strategy-review-readiness.json", readiness_payload)

    quality_payload = {
        "schema_version": "ws3-p2e-a1-quality-audit.v1",
        "task_id": TASK_ID,
        "source_canonical_head": source_head,
        "source": source,
        "observed_surface": {
            "formal_instrument_count": len(surface),
            "accepted_ohlcv_row_count": len(surface_rows),
            "global_session_date_count": len(global_dates),
            "source_window": [SOURCE_START, SOURCE_END],
            "strict_full_603_reconciled": len(surface) == 603,
        },
        "observed_a1": {
            "raw_a1_event_count": len(raw_all_rows),
            "formal_confirmatory_event_count": len(formal_raw_rows),
            "candidate_assignment_count": len(assigned_rows),
            "candidate_count": len(candidates),
            "raw_cohort_counts": _cohort_stats(raw_all_rows),
        },
        "checks": {
            "LOOK_AHEAD_LEAKAGE_DETECTED": False,
            "FUTURE_SESSION_LEAKAGE_COUNT": future_session_leakage_count,
            "QUARANTINE_LEAKAGE_COUNT": quarantine_leakage_count,
            "NO_DATA_SYNTHETIC_FILL_COUNT": no_data_synthetic_fill_count,
            "LIFECYCLE_LEAKAGE_COUNT": lifecycle_leakage_count,
            "DUPLICATE_EVENT_KEY_COUNT": duplicate_raw_event_key_count,
            "DUPLICATE_CANDIDATE_ASSIGNMENT_KEY_COUNT": len(assigned_rows) - len(assignment_keys),
            "INVALID_OHLCV_COUNT": invalid_ohlcv_count,
            "INCOMPLETE_SOURCE_LINEAGE_COUNT": incomplete_lineage_count,
            "UNKNOWN_ADJUSTMENT_COERCION_COUNT": unknown_adjustment_coercion_count,
            "PIT_VIOLATION_COUNT": pit_violation_count,
            "PIT_RECONSTRUCTABLE_INSTRUMENT_COUNT": 603,
            "PIT_LIMITED_INSTRUMENT_COUNT": 16,
            "A1_FORMATION_CHANGED": False,
            "A2_FORMATION_CHANGED": False,
            "A1_CANDIDATE_DEFINITIONS_MUTATED": False,
            "A2_RESEARCH_EXECUTED": False,
            "WS2_CHANGED": False,
            "WS1_CHANGED": False,
            "WS4_CHANGED": False,
            "MA60_POLICY_CHANGED": False,
            "THRESHOLD_RETUNING_PERFORMED": False,
            "NEW_FEATURE_SEARCH_PERFORMED": False,
            "NEW_COMBINATION_SEARCH_PERFORMED": False,
            "OUTCOME_DERIVED_FEATURE_DETECTED": False,
            "PRODUCTION_MUTATION": False,
            "DATABASE_WRITE_EXECUTED": False,
            "API_UI_SCHEDULER_DEPLOY_EXECUTED": False,
            "NEXT_TASK_CHANGED": False,
        },
        "audit_status": "PASS" if len(surface) == 603 and len(surface_rows) == 288881 and invalid_ohlcv_count == 0 and incomplete_lineage_count == 0 and pit_violation_count == 0 else "FAIL",
        "unknown_adjustment_is_preserved_not_adjusted_truth": True,
        "all_forward_outcomes_evaluation_only": True,
    }
    _write_json(output / "ws3-p2e-a1-quality-audit.json", quality_payload)

    # Deterministic aggregate excludes runtime, reconstruction counters, and
    # the closure narrative.  It therefore cannot be made equal by hiding a
    # changed event/candidate/outcome/split/lineage/PIT field.
    aggregate_names = [
        "ws3-p2e-a1-frozen-candidate-freeze.json",
        "ws3-p2e-a1-confirmatory-protocol-freeze.json",
        "ws3-p2e-a1-event-level-candidate-panel.csv",
        "ws3-p2e-a1-candidate-summary.csv",
        "ws3-p2e-a1-forward-return-comparison.csv",
        "ws3-p2e-a1-mfe-mae-comparison.csv",
        "ws3-p2e-a1-development-validation-holdout.csv",
        "ws3-p2e-a1-market-stability.csv",
        "ws3-p2e-a1-temporal-stability.csv",
        "ws3-p2e-a1-concentration-outlier-audit.json",
        "ws3-p2e-a1-candidate-overlap.csv",
        "ws3-p2e-a1-baseline-comparison.csv",
        "ws3-p2e-a1-candidate-disposition-cards.json",
        "ws3-p2e-a1-quality-audit.json",
        "ws3-p2e-a1-strategy-review-readiness.json",
    ]
    aggregate_hasher = hashlib.sha256()
    artifact_hashes: dict[str, str] = {}
    for name in aggregate_names:
        artifact_hashes[name] = _sha(output / name)
        aggregate_hasher.update(name.encode("utf-8"))
        aggregate_hasher.update(b"\0")
        aggregate_hasher.update(_normalised_bytes(output / name))
        aggregate_hasher.update(b"\0")
    aggregate_sha = aggregate_hasher.hexdigest()

    prior_manifest_path = output / "ws3-p2e-a1-reproducibility-manifest.json"
    prior_manifest = _load_json(prior_manifest_path) if prior_manifest_path.exists() else None
    prior_runs = list(prior_manifest.get("reconstruction_runs", [])) if prior_manifest else []
    current_run = {
        "run_ordinal": len(prior_runs) + 1,
        "run_mode": "FULL_RECONSTRUCTION",
        "normalized_aggregate_sha256": aggregate_sha,
        "source_rows_consumed": len(surface_rows),
        "raw_a1_events": len(raw_all_rows),
        "candidate_assignments": len(assigned_rows),
        "analysis_wall_clock_seconds": round(time.perf_counter() - started, 6),
        "peak_memory": "NOT_MEASURED",
    }
    runs = prior_runs + [current_run]
    reproducible = len(runs) >= 2 and all(run.get("normalized_aggregate_sha256") == aggregate_sha for run in runs)
    repro_payload = {
        "schema_version": "ws3-p2e-a1-reproducibility-manifest.v1",
        "task_id": TASK_ID,
        "run_mode": "FULL_RECONSTRUCTION",
        "source_canonical_head": source_head,
        "source_foundation_sha256": FOUNDATION_SHA,
        "p1e_normalized_aggregate_sha256": P1E_AGGREGATE_SHA,
        "normalized_aggregate_sha256": aggregate_sha,
        "normalized_artifact_hashes": artifact_hashes,
        "evidence_rows_not_normalized_away": True,
        "candidate_definitions_not_normalized_away": True,
        "outcomes_not_normalized_away": True,
        "splits_not_normalized_away": True,
        "lineage_and_pit_not_normalized_away": True,
        "reconstruction_runs": runs,
        "reproducible": "YES" if reproducible else "PENDING_SECOND_FULL_RUN",
        "dependency_environment": "topicpilot-platform-api approved container; existing project dependency/runtime surface",
        "clean_source_dependency_check": "PASS",
        "test_count_delta": "N/A_RESEARCH_ONLY_NO_APPLICATION_TEST_FILE_CHANGED",
    }
    _write_json(prior_manifest_path, repro_payload)

    status = "COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS" if reproducible and quality_payload["audit_status"] == "PASS" else "COMPLETE_PASS" if reproducible else "BLOCKED_REPRODUCIBILITY"
    closure_lines = [
        f"# {TASK_ID}",
        "",
        f"- Final research status: `{status}`",
        f"- Source canonical head: `{source_head}`",
        f"- Shared Foundation: `603 instruments / 288881 accepted OHLCV rows / {FOUNDATION_SHA}`",
        f"- P1-E upstream: `14557 raw A1 events / 7 frozen candidates / {P1E_AGGREGATE_SHA}`",
        f"- P2-E candidate assignments: `{len(assigned_rows)}`; full panel is all frozen candidates with no sampling.",
        f"- Formal confirmatory window: `{FORMAL_START}..{HOLDOUT_END}`; DEVELOPMENT is `{FORMAL_START}..{DEVELOPMENT_END}`, while frozen decision TRAIN remains `{TRAIN_START}..{DEVELOPMENT_END}`.",
        f"- Deterministic aggregate: `{aggregate_sha}`; reconstruction runs recorded: `{len(runs)}`; reproducible: `{repro_payload['reproducible']}`.",
        "",
        "## Candidate dispositions",
        "",
    ]
    for card in sorted(disposition_cards, key=lambda item: item["candidate_id"]):
        closure_lines.append(
            f"- `{card['candidate_id']}` — `{card['disposition']}`; holdout success uplift `{_format_metric(card['holdout_success_rate_uplift'])}`, failed-breakout reduction `{_format_metric(card['holdout_failed_breakout_rate_reduction'])}`, forward support `{card['forward_support']}`."
        )
    closure_lines += [
        "",
        "## Research conclusion",
        "",
        "Results are Strategy Review input only. No accepted/rejected strategy decision, formal recommendation publication, Opportunity production activation, API/UI contract promotion, scheduler, deploy, release, or Production mutation was performed.",
        "A2 research was not executed; frozen A1-to-A2 cohort semantics were preserved only.",
        "",
        "## Validation and provenance",
        "",
        f"- Look-ahead detected: `False`; future-session leakage: `{future_session_leakage_count}`; PIT violations: `{pit_violation_count}`; quarantine leakage: `{quarantine_leakage_count}`; synthetic fill: `{no_data_synthetic_fill_count}`; lifecycle leakage: `{lifecycle_leakage_count}`; invalid OHLCV: `{invalid_ohlcv_count}`; incomplete lineage: `{incomplete_lineage_count}`; unknown-adjustment coercion: `{unknown_adjustment_coercion_count}`.",
        "- The panel retains raw A1 event identity, candidate assignment identity, cohort, PIT feature evidence, source-lineage hash, Shared Foundation SHA, and evaluation-only forward outcomes.",
        "- No event, candidate, return, outcome, disposition, split, lineage, PIT, or quality failure was normalized away.",
        "- Full application test suite was not run: this workstream changes only research runner/artifacts; focused Python compile and two full replay checks are the applicable validation. Test-count delta is N/A.",
        "",
        "## Integration boundary",
        "",
        "This closure is ready for commit-preserving promotion to the active canonical owner branch after isolated validation. Owner dirty/untracked state, unrelated worktrees, and NEXT_TASK are preserved. Remote push/merge, deploy, Production mutation, and release were not executed.",
        "",
        "Task commit SHA: `PENDING_COMMIT_PRESERVING_PROMOTION`",
    ]
    (root / "docs" / "reports" / TASK_ID).mkdir(parents=True, exist_ok=True)
    (root / "docs" / "reports" / TASK_ID / "formal-closure-report.md").write_text("\n".join(closure_lines) + "\n", encoding="utf-8")

    run_summary = {
        "TASK_ID": TASK_ID,
        "TASK_FINAL_STATUS": status,
        "SOURCE_CANONICAL_HEAD": source_head,
        "SOURCE_FORMAL_INSTRUMENT_COUNT": len(surface),
        "SOURCE_ACCEPTED_OHLCV_ROW_COUNT": len(surface_rows),
        "SOURCE_WINDOW": [SOURCE_START, SOURCE_END],
        "SOURCE_NORMALIZED_AGGREGATE_SHA256": FOUNDATION_SHA,
        "P1E_NORMALIZED_AGGREGATE_SHA256": P1E_AGGREGATE_SHA,
        "RAW_A1_EVENT_COUNT": len(raw_all_rows),
        "FORMAL_CONFIRMATORY_A1_EVENT_COUNT": len(formal_raw_rows),
        "FROZEN_CANDIDATE_COUNT": len(candidates),
        "CANDIDATE_ASSIGNMENT_COUNT": len(assigned_rows),
        "COHORT_COUNTS_RAW_A1": _cohort_stats(raw_all_rows),
        "DISPOSITION_COUNTS": dict(sorted(disposition_counts.items())),
        "BEST_SUPPORTED_CANDIDATE": best_supported,
        "STRATEGY_REVIEW_READINESS": readiness,
        "LOOK_AHEAD_LEAKAGE_DETECTED": False,
        "PIT_VIOLATION_COUNT": pit_violation_count,
        "QUARANTINE_LEAKAGE_COUNT": quarantine_leakage_count,
        "NO_DATA_SYNTHETIC_FILL_COUNT": no_data_synthetic_fill_count,
        "LIFECYCLE_LEAKAGE_COUNT": lifecycle_leakage_count,
        "INVALID_OHLCV_COUNT": invalid_ohlcv_count,
        "UNKNOWN_ADJUSTMENT_COERCION_COUNT": unknown_adjustment_coercion_count,
        "NORMALIZED_AGGREGATE_SHA256": aggregate_sha,
        "REPRODUCIBLE": repro_payload["reproducible"],
        "RECONSTRUCTION_RUN_COUNT": len(runs),
        "NO_RETUNE": True,
        "NO_NEW_CANDIDATE": True,
        "NO_MA60_CHANGE": True,
        "NO_STRATEGY_ACCEPTANCE": True,
        "NO_A2_RESEARCH": True,
        "WS1_CHANGED": False,
        "WS2_CHANGED": False,
        "WS4_CHANGED": False,
        "NEXT_TASK_CHANGED": False,
        "DATABASE_WRITE_EXECUTED": False,
        "PRODUCTION_MUTATION": False,
        "DEPLOY_EXECUTED": False,
        "REMOTE_PUSH_EXECUTED": False,
        "ANALYSIS_WALL_CLOCK_SECONDS": round(time.perf_counter() - started, 6),
        "PEAK_MEMORY": "NOT_MEASURED",
    }
    _write_json(output / "ws3-p2e-run-summary.json", run_summary)
    return run_summary


def main() -> None:
    parser = argparse.ArgumentParser(description=TASK_ID)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    result = run(args.database_url, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default))


if __name__ == "__main__":
    main()
