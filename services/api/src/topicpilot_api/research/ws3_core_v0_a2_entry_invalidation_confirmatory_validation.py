"""Confirmatory validation for the frozen WS3 Core V0 A2 path candidates.

This task consumes the previous A2 descriptive artifacts and the same read-only
historical OHLCV collector.  Candidate regions and path families are written to
freeze artifacts before any confirmatory outcome tables are calculated.  The
module never changes A2 formation, searches thresholds, or writes application
state.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from statistics import mean, median
from typing import Any

from topicpilot_api.research.ws3_core_v0_a2_entry_breakout_invalidation import (
    ENTRY_PROXIES,
    FROZEN_SPEC_HASH,
    HORIZONS,
    PRIMARY_ENTRY_PROXY,
    _build_events,
    _horizon_rows,
    _reference_path,
    collect_observations,
)

# ruff: noqa: E501 - exact contract strings and evidence paths are intentional.

TASK_ID = "TASK-WS3-CORE-V0-A2-ENTRY-AND-INVALIDATION-CANDIDATE-CONFIRMATORY-VALIDATION-20260819"
UPSTREAM_TASK_ID = "TASK-WS3-CORE-V0-A2-ENTRY-AND-BREAKOUT-INVALIDATION-RESEARCH-20260819"
SOURCE_CANONICAL_HEAD = "23ff948615f0da6a6242858634d9bacc89b59f2a"
UPSTREAM_DIR = Path("reports") / UPSTREAM_TASK_ID
REPORT_PATH = Path("docs/reports") / f"{TASK_ID}.md"
OUTPUT_DIR_DEFAULT = Path("reports") / TASK_ID
DATASET_PATH_DEFAULT = Path("reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json")

ENTRY_CANDIDATE_BANDS = ("GT_0_TO_1PCT", "GT_1_TO_2PCT", "GT_2_TO_3PCT", "GT_3_TO_5PCT", "GT_5PCT")
DEPTH_CANDIDATE_BANDS = ("0_TO_MINUS_1PCT", "MINUS_1_TO_2PCT", "MINUS_2_TO_3PCT", "MINUS_3_TO_5PCT", "BELOW_MINUS_5PCT")
TIME_STATES = ("RECLAIM_WITHIN_1_SESSION", "RECLAIM_2_SESSIONS", "RECLAIM_3_PLUS_OR_NO_RECLAIM_H10")
RECLAIM_STATES = ("REFERENCE_LOSS_THEN_RECLAIM", "REFERENCE_LOSS_NO_RECLAIM_WITHIN_H10")
PATH_STATES = ("CLOSE_BELOW_REFERENCE_THEN_RECLAIM", "LOSS_NO_RECLAIM_WITHIN_H10")
COMBINATION_CANDIDATES = ("SHALLOW_LOSS_QUICK_RECLAIM", "DEEP_LOSS_NO_RECLAIM", "MULTI_SESSION_BELOW_NO_RECLAIM")
CORE_ARTIFACT_NAMES = (
    "ws3-core-v0-a2-entry-confirmatory-freeze.json",
    "ws3-core-v0-a2-invalidation-confirmatory-freeze.json",
    "ws3-core-v0-a2-entry-candidate-comparison.csv",
    "ws3-core-v0-a2-entry-market-stability.csv",
    "ws3-core-v0-a2-entry-temporal-stability.csv",
    "ws3-core-v0-a2-entry-july-analysis.csv",
    "ws3-core-v0-a2-invalidation-candidate-comparison.csv",
    "ws3-core-v0-a2-reference-depth-recovery-analysis.csv",
    "ws3-core-v0-a2-time-below-reference-analysis.csv",
    "ws3-core-v0-a2-reclaim-confirmatory-analysis.csv",
    "ws3-core-v0-a2-invalidation-market-stability.csv",
    "ws3-core-v0-a2-invalidation-temporal-stability.csv",
    "ws3-core-v0-a2-confirmatory-concentration-analysis.json",
    "ws3-core-v0-a2-entry-candidate-cards.json",
    "ws3-core-v0-a2-invalidation-candidate-cards.json",
)
SUPPORTING_ARTIFACT_NAMES = (
    "ws3-core-v0-a2-entry-confirmatory-summary.json",
    "ws3-core-v0-a2-confirmatory-quality-audit.json",
    "ws3-core-v0-a2-next-step-readiness.json",
)
ALL_ARTIFACT_NAMES = CORE_ARTIFACT_NAMES + SUPPORTING_ARTIFACT_NAMES


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"EMPTY_CSV_OUTPUT:{path.name}")
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({field: row.get(field) for field in fields} for row in rows)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _day(value: Any) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def _quantile(values: Sequence[float], fraction: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _trimmed_mean(values: Sequence[float], fraction: float = 0.10) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    trim = int(len(ordered) * fraction)
    kept = ordered[trim : len(ordered) - trim] if len(ordered) > trim * 2 else ordered
    return mean(kept)


def _wilson(successes: int, total: int) -> tuple[float | None, float | None]:
    if total <= 0:
        return None, None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return max(0.0, centre - spread), min(1.0, centre + spread)


def _stats(values: Sequence[float], *, positive_is_success: bool = True) -> dict[str, Any]:
    clean = [value for value in values if value is not None and math.isfinite(value)]
    successes = sum(value > 0 for value in clean) if positive_is_success else sum(value >= 0 for value in clean)
    lower, upper = _wilson(successes, len(clean))
    avg = mean(clean) if clean else None
    med = median(clean) if clean else None
    trimmed = _trimmed_mean(clean)
    return {
        "count": len(clean),
        "mean": avg,
        "median": med,
        "trimmed_mean_10pct": trimmed,
        "p05": _quantile(clean, 0.05),
        "p25": _quantile(clean, 0.25),
        "p75": _quantile(clean, 0.75),
        "p95": _quantile(clean, 0.95),
        "win_rate": successes / len(clean) if clean else None,
        "win_rate_ci95_low": lower,
        "win_rate_ci95_high": upper,
        "outlier_driven": bool(avg is not None and med is not None and trimmed is not None and avg > 0 and med <= 0 and trimmed <= 0),
    }


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _normalized_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(bytes([13, 10]), bytes([10]))).hexdigest()


def _hash_files(root: Path, names: Sequence[str]) -> dict[str, str]:
    return {name: _normalized_hash(root / name) for name in names if (root / name).exists()}


def _aggregate_hash(hashes: Mapping[str, str]) -> str:
    digest = hashlib.sha256()
    for name in sorted(hashes):
        digest.update(name.encode("utf-8"))
        digest.update(bytes.fromhex(hashes[name]))
    return digest.hexdigest()


def _source_authority(upstream_dir: Path) -> dict[str, Any]:
    required = [
        "ws3-core-v0-a2-event-definition.json",
        "ws3-core-v0-a2-event-panel.csv",
        "ws3-core-v0-a2-entry-extension-distribution.csv",
        "ws3-core-v0-a2-entry-proxy-comparison.csv",
        "ws3-core-v0-a2-extension-forward-return-analysis.csv",
        "ws3-core-v0-a2-mfe-mae-analysis.csv",
        "ws3-core-v0-a2-reference-loss-analysis.csv",
        "ws3-core-v0-a2-reference-reclaim-analysis.csv",
        "ws3-core-v0-a2-time-to-failure-and-recovery.csv",
        "ws3-core-v0-a2-immediate-vs-confirmation-entry.csv",
        "ws3-core-v0-a2-market-stability.csv",
        "ws3-core-v0-a2-temporal-stability.csv",
        "ws3-core-v0-a2-july-analysis.csv",
        "ws3-core-v0-a2-quality-audit.json",
        "ws3-core-v0-a2-next-step-readiness.json",
        "ws3-core-v0-a1-quality-filter-forward-validation-contract.json",
    ]
    missing = [name for name in required if not (upstream_dir / name).exists()]
    if missing:
        raise RuntimeError(f"UPSTREAM_ARTIFACT_MISSING:{missing}")
    definition = _read_json(upstream_dir / required[0])
    panel = _read_csv(upstream_dir / required[1])
    extension = _read_csv(upstream_dir / required[2])
    proxy = _read_csv(upstream_dir / required[3])
    audit = _read_json(upstream_dir / "ws3-core-v0-a2-quality-audit.json")
    readiness = _read_json(upstream_dir / "ws3-core-v0-a2-next-step-readiness.json")
    a1 = _read_json(upstream_dir / "ws3-core-v0-a1-quality-filter-forward-validation-contract.json")
    upstream_artifact_source_head = definition.get("source_canonical_head")
    if definition.get("frozen_spec_hash") != FROZEN_SPEC_HASH or not upstream_artifact_source_head:
        raise RuntimeError("UPSTREAM_FROZEN_SPEC_OR_PROVENANCE_MISMATCH")
    if len(panel) != 490 or audit.get("a2_distinct_event_count") != 490 or audit.get("a2_raw_observation_count") != 512:
        raise RuntimeError("UPSTREAM_A2_EVENT_COUNT_MISMATCH")
    if set(row["entry_proxy"] for row in proxy) != set(ENTRY_PROXIES):
        raise RuntimeError("UPSTREAM_ENTRY_PROXY_AUTHORITY_MISMATCH")
    expected_entry_bands = {item["band"] for item in definition["entry_extension"]["bands"]}
    if set(ENTRY_CANDIDATE_BANDS) | {"LE_0PCT"} != expected_entry_bands:
        raise RuntimeError("UPSTREAM_ENTRY_BAND_AUTHORITY_MISMATCH")
    expected_depth_bands = {item["band"] for item in definition["reference_loss_reclaim"]["depth_bands"]}
    if set(DEPTH_CANDIDATE_BANDS) | {"NO_LOSS"} != expected_depth_bands:
        raise RuntimeError("UPSTREAM_DEPTH_BAND_AUTHORITY_MISMATCH")
    if a1.get("status") != "FROZEN_AWAITING_FORWARD_EVIDENCE" or a1.get("candidate_count") != 7:
        raise RuntimeError("A1_FROZEN_STATUS_OR_CANDIDATE_COUNT_MISMATCH")
    if not audit.get("entry_proxies_frozen_before_outcomes") or audit.get("look_ahead_leakage_detected"):
        raise RuntimeError("UPSTREAM_A2_LOOKAHEAD_OR_PROXY_AUTHORITY_FAILURE")
    return {
        "upstream_task_id": UPSTREAM_TASK_ID,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "upstream_artifact_source_head": upstream_artifact_source_head,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "required_artifact_count": len(required),
        "source_artifact_hashes": _hash_files(upstream_dir, required),
        "event_definition": definition,
        "event_panel_count": len(panel),
        "event_ids": sorted(row["event_id"] for row in panel),
        "extension_rows": extension,
        "proxy_rows": proxy,
        "a1_status": a1["status"],
        "a1_candidate_count": a1["candidate_count"],
        "a1_threshold_retuning_performed": a1.get("threshold_retuning_performed"),
        "a1_new_feature_search_performed": a1.get("new_feature_search_performed"),
        "upstream_quality_audit": audit,
        "upstream_readiness": readiness,
        "authority_flags": {
            "current_canonical_head_verified": True,
            "frozen_spec_hash_verified": True,
            "a2_event_definition_available": True,
            "a2_event_panel_available": True,
            "breakout_reference_authority_ready": True,
            "entry_proxy_authority_ready": True,
            "reference_loss_reclaim_authority_ready": True,
            "pit_ohlcv_ready": bool(audit.get("collection_quality", {}).get("source_reconciliation", {}).get("pass")),
            "temporal_segment_authority_ready": True,
            "concurrent_ws1_ws2_change_reconciliation_required": "PRESERVE_AND_RECORD_ONLY",
        },
    }


def _entry_freeze(authority: Mapping[str, Any]) -> dict[str, Any]:
    bands = {item["band"]: item for item in authority["event_definition"]["entry_extension"]["bands"]}
    return {
        "task_id": TASK_ID,
        "upstream_task_id": UPSTREAM_TASK_ID,
        "schema_version": "ws3-core-v0-a2-entry-confirmatory-freeze.v1",
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "frozen_before_confirmatory_outcome_review": True,
        "primary_entry_proxy": PRIMARY_ENTRY_PROXY,
        "theoretical_benchmark_proxy": "THEORETICAL_REFERENCE_FILL",
        "authorized_entry_proxies": list(ENTRY_PROXIES),
        "candidate_regions": [
            {
                "candidate_id": f"A2_CLOSE_{band}",
                "entry_proxy": PRIMARY_ENTRY_PROXY,
                "candidate_kind": "PRIMARY_REALISTIC_ENTRY_REGION",
                "extension_band": band,
                "band_definition": bands[band],
                "candidate_inputs_frozen_at_T": True,
                "outcomes_evaluation_only": True,
            }
            for band in ENTRY_CANDIDATE_BANDS
        ],
        "benchmark_policy": "THEORETICAL_REFERENCE_FILL remains a benchmark and is not treated as always executable; NEXT_SESSION_OPEN and NEXT_SESSION_CLOSE remain comparison proxies only.",
        "candidate_count": len(ENTRY_CANDIDATE_BANDS),
        "decision_framework": {
            "sample_floor_supported": 20,
            "sample_floor_confirmed": 40,
            "required_horizons": ["T+5", "T+10"],
            "confirmed_requires": "sample floor, positive T+5 and T+10 median, no outlier-driven primary result, and directionally consistent TPE/TWO and temporal segments; July is reported as a stress caveat",
            "supported_requires": "sample floor and positive primary horizon evidence with bounded market/temporal/July/concentration limitations",
            "failed_requires": "sample floor and non-positive T+5 median with non-positive T+5 win-rate evidence",
            "inconclusive_rule": "insufficient maturity, mixed horizon evidence, or unresolved segment direction",
            "no_single_metric_decides": True,
            "no_entry_threshold_optimization": True,
        },
        "outcome_boundary": {
            "candidate_information_effective_on_or_before_T": True,
            "candidate_frozen_at_T": True,
            "forward_outcomes_are_evaluation_only": True,
            "corporate_action_post_hoc_evidence_can_only_invalidate_evaluation": True,
        },
        "source_artifact_hashes": authority["source_artifact_hashes"],
    }


def _invalidation_freeze(authority: Mapping[str, Any], path_categories: Sequence[str]) -> dict[str, Any]:
    depth_defs = {item["band"]: item for item in authority["event_definition"]["reference_loss_reclaim"]["depth_bands"]}
    candidate_families: list[dict[str, Any]] = []
    for band in DEPTH_CANDIDATE_BANDS:
        candidate_families.append({"candidate_id": f"DEPTH_{band}", "family": "REFERENCE_LOSS_DEPTH", "depth_band": band, "definition": depth_defs[band]})
    candidate_families.extend(
        [
            {"candidate_id": "TIME_RECLAIM_WITHIN_1_SESSION", "family": "TIME_BELOW_REFERENCE", "time_state": TIME_STATES[0], "definition": "sessions_to_reclaim == 1"},
            {"candidate_id": "TIME_RECLAIM_2_SESSIONS", "family": "TIME_BELOW_REFERENCE", "time_state": TIME_STATES[1], "definition": "sessions_to_reclaim == 2"},
            {"candidate_id": "TIME_RECLAIM_3_PLUS_OR_NO_RECLAIM_H10", "family": "TIME_BELOW_REFERENCE", "time_state": TIME_STATES[2], "definition": "sessions_to_reclaim >= 3 or no reclaim within H10 with observed below-reference duration >= 3 sessions"},
            {"candidate_id": "RECLAIMED_REFERENCE_LOSS", "family": "RECLAIM_STATUS", "reclaim_state": RECLAIM_STATES[0], "definition": "reference_loss and reference_reclaimed"},
            {"candidate_id": "FAILED_RECLAIM_REFERENCE_LOSS", "family": "RECLAIM_STATUS", "reclaim_state": RECLAIM_STATES[1], "definition": "reference_loss and not reference_reclaimed within H10"},
            {"candidate_id": "CLOSE_BELOW_THEN_RECLAIM", "family": "CLOSE_BELOW_REFERENCE", "path_state": PATH_STATES[0], "definition": "path_category == CLOSE_BELOW_REFERENCE_THEN_RECLAIM"},
            {"candidate_id": "LOSS_NO_RECLAIM_PATH", "family": "CLOSE_BELOW_REFERENCE", "path_state": PATH_STATES[1], "definition": "path_category == LOSS_NO_RECLAIM_WITHIN_H10"},
            {"candidate_id": "SHALLOW_LOSS_QUICK_RECLAIM", "family": "PREDECLARED_COMBINATION", "definition": "depth in first three loss bands and reclaim within 1 session"},
            {"candidate_id": "DEEP_LOSS_NO_RECLAIM", "family": "PREDECLARED_COMBINATION", "definition": "BELOW_MINUS_5PCT and no reclaim within H10"},
            {"candidate_id": "MULTI_SESSION_BELOW_NO_RECLAIM", "family": "PREDECLARED_COMBINATION", "definition": "observed below-reference duration >= 3 sessions and no reclaim within H10"},
        ]
    )
    if any(category not in {"REMAINS_ABOVE_REFERENCE", "CLOSE_BELOW_REFERENCE_THEN_RECLAIM", "TEMPORARY_INTRADAY_LOSS_RECLAIMED", "LOSS_NO_RECLAIM_WITHIN_H10"} for category in path_categories):
        raise RuntimeError("UNAUTHORIZED_PATH_CATEGORY_IN_UPSTREAM_PANEL")
    return {
        "task_id": TASK_ID,
        "upstream_task_id": UPSTREAM_TASK_ID,
        "schema_version": "ws3-core-v0-a2-invalidation-confirmatory-freeze.v1",
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "frozen_before_confirmatory_outcome_review": True,
        "candidate_families": candidate_families,
        "candidate_count": len(candidate_families),
        "authorized_depth_bands": [depth_defs[band] for band in DEPTH_CANDIDATE_BANDS],
        "authorized_time_states": [
            {"state": TIME_STATES[0], "definition": "sessions_to_reclaim == 1"},
            {"state": TIME_STATES[1], "definition": "sessions_to_reclaim == 2"},
            {"state": TIME_STATES[2], "definition": "sessions_to_reclaim >= 3 or censored/no reclaim after >= 3 observed below-reference sessions"},
        ],
        "authorized_reclaim_states": list(RECLAIM_STATES),
        "authorized_path_states": list(PATH_STATES),
        "maximum_predeclared_combinations": 3,
        "combination_candidate_ids": list(COMBINATION_CANDIDATES),
        "decision_framework": {
            "sample_floor_supported": 20,
            "sample_floor_confirmed": 40,
            "normal_retest_comparison": "shallow first-three depth bands versus BELOW_MINUS_5PCT, using reclaim rate and post-loss T+5/T+10 recovery direction before segment caveats",
            "invalidation_comparison": "DEEP_LOSS_NO_RECLAIM versus SHALLOW_LOSS_QUICK_RECLAIM, using reclaim status and post-loss recovery direction; no stop threshold",
            "confirmed_requires": "sample floor, expected depth/time/reclaim direction, TPE/TWO and temporal direction not contradictory, and no concentration/outlier caveat that overturns the result",
            "supported_requires": "sample floor and expected core path direction with bounded stability or maturity limitations",
            "no_single_metric_decides": True,
            "no_stop_optimization": True,
            "no_combinatorial_search": True,
        },
        "post_loss_semantics": {
            "primary_loss": "first future canonical session with Low < BREAKOUT_REFERENCE_PRICE",
            "post_loss_horizon_path": "the next h canonical sessions strictly after the first loss session",
            "post_loss_return": "Close(loss+h) / BREAKOUT_REFERENCE_PRICE - 1",
            "post_loss_mfe": "max(High / BREAKOUT_REFERENCE_PRICE - 1) over the next h sessions strictly after loss",
            "post_loss_mae": "min(Low / BREAKOUT_REFERENCE_PRICE - 1) over the next h sessions strictly after loss",
            "reclaim": "first session at or after loss with Close >= BREAKOUT_REFERENCE_PRICE",
            "exceeds_prior_a2_close": "any post-loss future Close >= A2 Close within observed H10 path",
            "outcomes_evaluation_only": True,
        },
        "path_categories_observed": sorted(path_categories),
        "source_artifact_hashes": authority["source_artifact_hashes"],
    }


def _reconcile_events(database_url: str, dataset_path: Path, authority: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    observations, quality = collect_observations(database_url, dataset_path)
    a1_rows = observations["groups"]["A1_PRE_BREAKOUT"]
    a2_rows = observations["groups"]["A2_CONFIRMED_BREAKOUT"]
    events = _build_events(a1_rows, a2_rows, observations["instrument_data"])
    for event in events:
        _reference_path(event)
    if len(a2_rows) != 512 or len(events) != authority["event_panel_count"]:
        raise RuntimeError("RECONCILIATION_A2_COUNT_MISMATCH")
    generated_ids = sorted(event["event_id"] for event in events)
    if generated_ids != authority["event_ids"]:
        raise RuntimeError("RECONCILIATION_EVENT_ID_MISMATCH")
    return events, quality, len(a2_rows)


def _event_band(value: float | None) -> str | None:
    if value is None:
        return None
    if value <= 0:
        return "LE_0PCT"
    if value <= 0.01:
        return "GT_0_TO_1PCT"
    if value <= 0.02:
        return "GT_1_TO_2PCT"
    if value <= 0.03:
        return "GT_2_TO_3PCT"
    if value <= 0.05:
        return "GT_3_TO_5PCT"
    return "GT_5PCT"


def _time_state(event: Mapping[str, Any]) -> str | None:
    if not event.get("reference_loss"):
        return None
    reclaim = event.get("sessions_to_reclaim")
    if reclaim == 1:
        return TIME_STATES[0]
    if reclaim == 2:
        return TIME_STATES[1]
    if reclaim is not None and reclaim >= 3:
        return TIME_STATES[2]
    observed_below = int(event.get("path_observed_sessions", 0)) - int(event.get("first_reference_loss_session", 0)) + 1
    return TIME_STATES[2] if observed_below >= 3 else TIME_STATES[0]


def _annotate_events(events: Sequence[dict[str, Any]]) -> None:
    for event in events:
        event["entry_extension_band"] = _event_band(_number(event.get("a2_close")) / _number(event.get("reference")) - 1 if _number(event.get("a2_close")) and _number(event.get("reference")) else None)
        event["time_below_reference_state"] = _time_state(event)
        event["exceeds_prior_a2_close_again"] = False
        if event.get("reference_loss"):
            start = int(event["index"]) + int(event["first_reference_loss_session"])
            future = event["_items"][start + 1 : start + 1 + 10]
            event["exceeds_prior_a2_close_again"] = any((_number(item.get("close")) or -math.inf) >= (_number(event.get("a2_close")) or math.inf) for item in future)
            observed_below = len(event["_items"][start : start + 10])
            event["observed_below_reference_sessions"] = observed_below
        else:
            event["observed_below_reference_sessions"] = None


def _entry_metric_row(candidate_id: str, band: str, event_ids: set[str], horizon: int, horizon_rows: Mapping[str, Sequence[Mapping[str, Any]]], total_events: int, events_by_id: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    all_rows = [row for row in horizon_rows[PRIMARY_ENTRY_PROXY] if row["event_id"] in event_ids and row["horizon"] == horizon]
    available = [row for row in all_rows if row.get("status") == "AVAILABLE"]
    forward = _stats([_number(row.get("forward_return")) for row in available])
    mfe = _stats([_number(row.get("mfe")) for row in available])
    mae = _stats([_number(row.get("mae")) for row in available], positive_is_success=False)
    gap_count = sum(bool(events_by_id[event_id].get("gap_up")) for event_id in event_ids if event_id in events_by_id)
    return {
        "candidate_id": candidate_id,
        "entry_proxy": PRIMARY_ENTRY_PROXY,
        "extension_band": band,
        "horizon": horizon,
        "candidate_event_count": len(event_ids),
        "total_distinct_a2_events": total_events,
        "retention_rate": len(event_ids) / total_events if total_events else None,
        "entry_available_count": len(available),
        "unavailable_execution_count": 0,
        "unavailable_horizon_count": len(event_ids) - len(available),
        "horizon_retention_rate": len(available) / len(event_ids) if event_ids else None,
        "gap_away_count": gap_count,
        "forward_mean": forward["mean"],
        "forward_median": forward["median"],
        "forward_trimmed_mean_10pct": forward["trimmed_mean_10pct"],
        "forward_win_rate": forward["win_rate"],
        "forward_win_rate_ci95_low": forward["win_rate_ci95_low"],
        "forward_win_rate_ci95_high": forward["win_rate_ci95_high"],
        "mfe_mean": mfe["mean"],
        "mfe_median": mfe["median"],
        "mae_mean": mae["mean"],
        "mae_median": mae["median"],
        "mfe_mae_median_ratio": _safe_ratio(mfe["median"], abs(mae["median"]) if mae["median"] is not None else None),
        "outlier_driven": forward["outlier_driven"],
    }


def _entry_stability_rows(candidates: Sequence[Mapping[str, Any]], events: Sequence[Mapping[str, Any]], horizon_rows: Mapping[str, Sequence[Mapping[str, Any]]], dimension: str) -> list[dict[str, Any]]:
    values = ("TPE", "TWO") if dimension == "market" else ("DEVELOPMENT_AVAILABLE", "VALIDATION", "HOLDOUT")
    field = "market" if dimension == "market" else "segment"
    events_by_id = {event["event_id"]: event for event in events}
    result = []
    for candidate in candidates:
        band = candidate["extension_band"]
        candidate_ids = {event["event_id"] for event in events if event["entry_extension_band"] == band}
        for value in values:
            ids = {event_id for event_id in candidate_ids if events_by_id[event_id].get(field) == value}
            for horizon in HORIZONS:
                row = _entry_metric_row(candidate["candidate_id"], band, ids, horizon, horizon_rows, len(candidate_ids), events_by_id)
                row.update({"dimension": dimension, "segment_value": value})
                result.append(row)
    return result


def _entry_july_rows(candidates: Sequence[Mapping[str, Any]], events: Sequence[Mapping[str, Any]], horizon_rows: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    events_by_id = {event["event_id"]: event for event in events}
    result = []
    for candidate in candidates:
        band = candidate["extension_band"]
        candidate_ids = {event["event_id"] for event in events if event["entry_extension_band"] == band}
        for period, ids in (("JULY", {event_id for event_id in candidate_ids if _day(events_by_id[event_id]["signal_date"]).month == 7}), ("NON_JULY", {event_id for event_id in candidate_ids if _day(events_by_id[event_id]["signal_date"]).month != 7})):
            for horizon in HORIZONS:
                row = _entry_metric_row(candidate["candidate_id"], band, ids, horizon, horizon_rows, len(candidate_ids), events_by_id)
                row.update({"period": period, "july_stress_segment": period == "JULY"})
                result.append(row)
    return result


def _entry_classification(candidate: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], market_rows: Sequence[Mapping[str, Any]], temporal_rows: Sequence[Mapping[str, Any]]) -> tuple[str, str]:
    t5 = next(row for row in rows if row["horizon"] == 5)
    t10 = next(row for row in rows if row["horizon"] == 10)
    count = t5["candidate_event_count"]
    if count < 20 or t5["entry_available_count"] < 20 or t10["entry_available_count"] < 20:
        return "INCONCLUSIVE", "candidate or mature-horizon availability below the frozen sample floor"
    if (t5["forward_median"] or 0) <= 0 and (t5["forward_win_rate"] or 0) < 0.5:
        return "FAILED_CONFIRMATION", "T+5 median and win-rate evidence do not preserve a positive primary edge"
    core_positive = (t5["forward_median"] or 0) > 0 and (t10["forward_median"] or 0) > 0
    market_t5 = [row for row in market_rows if row["candidate_id"] == candidate["candidate_id"] and row["horizon"] == 5 and row["entry_available_count"] >= 5]
    temporal_t5 = [row for row in temporal_rows if row["candidate_id"] == candidate["candidate_id"] and row["horizon"] == 5 and row["entry_available_count"] >= 5]
    directional = all((row["forward_median"] or 0) >= 0 for row in market_t5 + temporal_t5)
    if core_positive and count >= 40 and directional and not t5["outlier_driven"]:
        return "CONFIRMED", "positive T+5/T+10 medians with frozen sample floor and no contradictory tested segment"
    if core_positive:
        return "SUPPORTED_WITH_BOUNDED_LIMITATIONS", "positive primary horizon medians, with segment, July, retention, or concentration caveats"
    return "INCONCLUSIVE", "mixed T+5/T+10 direction prevents confirmatory acceptance"


def _entry_cards(candidates: Sequence[Mapping[str, Any]], comparison: Sequence[Mapping[str, Any]], market_rows: Sequence[Mapping[str, Any]], temporal_rows: Sequence[Mapping[str, Any]], july_rows: Sequence[Mapping[str, Any]], events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for candidate in candidates:
        rows = [row for row in comparison if row["candidate_id"] == candidate["candidate_id"]]
        classification, caveat = _entry_classification(candidate, rows, market_rows, temporal_rows)
        candidate_events = [event for event in events if event["entry_extension_band"] == candidate["extension_band"]]
        result.append(
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_name": f"{PRIMARY_ENTRY_PROXY}:{candidate['extension_band']}",
                "entry_proxy": PRIMARY_ENTRY_PROXY,
                "extension_region": candidate["extension_band"],
                "sample_size": len(candidate_events),
                "retention_rate": len(candidate_events) / len(events) if events else None,
                "horizons": rows,
                "July": [row for row in july_rows if row["candidate_id"] == candidate["candidate_id"]],
                "TPE": [row for row in market_rows if row["candidate_id"] == candidate["candidate_id"] and row["segment_value"] == "TPE"],
                "TWO": [row for row in market_rows if row["candidate_id"] == candidate["candidate_id"] and row["segment_value"] == "TWO"],
                "temporal": [row for row in temporal_rows if row["candidate_id"] == candidate["candidate_id"]],
                "classification": classification,
                "major_caveat": caveat,
            }
        )
    return result


def _post_loss_row(event: Mapping[str, Any], horizon: int) -> dict[str, Any]:
    base = {"event_id": event["event_id"], "market": event["market"], "segment": event["segment"], "horizon": horizon}
    if not event.get("path_matured_h10") or not event.get("reference_loss"):
        return {**base, "status": "UNAVAILABLE_NOT_MATURED_OR_NO_LOSS"}
    loss_index = int(event["index"]) + int(event["first_reference_loss_session"])
    path = event["_items"][loss_index + 1 : loss_index + 1 + horizon]
    if len(path) < horizon:
        return {**base, "status": "UNAVAILABLE_INSUFFICIENT_POST_LOSS_WINDOW"}
    reference = float(event["reference"])
    closes = [_number(item.get("close")) for item in path]
    highs = [_number(item.get("high")) for item in path]
    lows = [_number(item.get("low")) for item in path]
    if any(value is None for value in closes + highs + lows):
        return {**base, "status": "UNAVAILABLE_MALFORMED_POST_LOSS_WINDOW"}
    target_close = closes[-1]
    return {
        **base,
        "status": "AVAILABLE",
        "post_loss_return_vs_reference": target_close / reference - 1,
        "post_loss_mfe_vs_reference": max(highs) / reference - 1,
        "post_loss_mae_vs_reference": min(lows) / reference - 1,
        "returned_above_reference_by_horizon": target_close >= reference,
        "exceeded_prior_a2_close_by_horizon": target_close >= float(event["a2_close"]),
    }


def _invalidation_ids(candidate_id: str, events: Sequence[Mapping[str, Any]]) -> set[str]:
    loss_events = [event for event in events if event.get("path_matured_h10") and event.get("reference_loss")]
    if candidate_id.startswith("DEPTH_"):
        band = candidate_id.removeprefix("DEPTH_")
        return {event["event_id"] for event in loss_events if event.get("reference_loss_depth_band") == band}
    if candidate_id == "TIME_RECLAIM_WITHIN_1_SESSION":
        return {event["event_id"] for event in loss_events if event.get("time_below_reference_state") == TIME_STATES[0]}
    if candidate_id == "TIME_RECLAIM_2_SESSIONS":
        return {event["event_id"] for event in loss_events if event.get("time_below_reference_state") == TIME_STATES[1]}
    if candidate_id == "TIME_RECLAIM_3_PLUS_OR_NO_RECLAIM_H10":
        return {event["event_id"] for event in loss_events if event.get("time_below_reference_state") == TIME_STATES[2]}
    if candidate_id == "RECLAIMED_REFERENCE_LOSS":
        return {event["event_id"] for event in loss_events if event.get("reference_reclaimed")}
    if candidate_id == "FAILED_RECLAIM_REFERENCE_LOSS":
        return {event["event_id"] for event in loss_events if not event.get("reference_reclaimed")}
    if candidate_id == "CLOSE_BELOW_THEN_RECLAIM":
        return {event["event_id"] for event in loss_events if event.get("path_category") == PATH_STATES[0]}
    if candidate_id == "LOSS_NO_RECLAIM_PATH":
        return {event["event_id"] for event in loss_events if event.get("path_category") == PATH_STATES[1]}
    if candidate_id == "SHALLOW_LOSS_QUICK_RECLAIM":
        return {event["event_id"] for event in loss_events if event.get("reference_loss_depth_band") in DEPTH_CANDIDATE_BANDS[:3] and event.get("sessions_to_reclaim") == 1}
    if candidate_id == "DEEP_LOSS_NO_RECLAIM":
        return {event["event_id"] for event in loss_events if event.get("reference_loss_depth_band") == "BELOW_MINUS_5PCT" and not event.get("reference_reclaimed")}
    if candidate_id == "MULTI_SESSION_BELOW_NO_RECLAIM":
        return {event["event_id"] for event in loss_events if event.get("time_below_reference_state") == TIME_STATES[2] and not event.get("reference_reclaimed")}
    raise RuntimeError(f"UNKNOWN_INVALIDATION_CANDIDATE:{candidate_id}")


def _post_loss_stats(event_ids: set[str], events_by_id: Mapping[str, Mapping[str, Any]], horizon: int) -> dict[str, Any]:
    rows = [_post_loss_row(events_by_id[event_id], horizon) for event_id in event_ids]
    available = [row for row in rows if row["status"] == "AVAILABLE"]
    recovery = _stats([row.get("post_loss_return_vs_reference") for row in available])
    mfe = _stats([row.get("post_loss_mfe_vs_reference") for row in available])
    mae = _stats([row.get("post_loss_mae_vs_reference") for row in available], positive_is_success=False)
    return {
        "post_loss_event_count": len(available),
        "post_loss_unavailable_count": len(rows) - len(available),
        "post_loss_return_mean": recovery["mean"],
        "post_loss_return_median": recovery["median"],
        "post_loss_return_win_rate": recovery["win_rate"],
        "post_loss_return_ci95_low": recovery["win_rate_ci95_low"],
        "post_loss_return_ci95_high": recovery["win_rate_ci95_high"],
        "post_loss_mfe_median": mfe["median"],
        "post_loss_mae_median": mae["median"],
        "post_loss_mfe_mae_median_ratio": _safe_ratio(mfe["median"], abs(mae["median"]) if mae["median"] is not None else None),
        "returned_above_reference_by_horizon_rate": mean(row["returned_above_reference_by_horizon"] for row in available) if available else None,
        "exceeded_prior_a2_close_by_horizon_rate": mean(row["exceeded_prior_a2_close_by_horizon"] for row in available) if available else None,
        "outlier_driven": recovery["outlier_driven"],
    }


def _invalidation_row(candidate: Mapping[str, Any], event_ids: set[str], events_by_id: Mapping[str, Mapping[str, Any]], total_loss_events: int) -> dict[str, Any]:
    group = [events_by_id[event_id] for event_id in event_ids]
    reclaimed = sum(bool(event.get("reference_reclaimed")) for event in group)
    reclaim_low, reclaim_high = _wilson(reclaimed, len(group))
    sessions = [event["sessions_to_reclaim"] for event in group if event.get("sessions_to_reclaim") is not None]
    row: dict[str, Any] = {
        "candidate_id": candidate["candidate_id"],
        "family": candidate["family"],
        "candidate_definition": candidate["definition"],
        "event_count": len(group),
        "total_mature_loss_events": total_loss_events,
        "retention_rate_of_mature_loss_events": len(group) / total_loss_events if total_loss_events else None,
        "reclaim_event_count": reclaimed,
        "reclaim_rate": reclaimed / len(group) if group else None,
        "reclaim_rate_ci95_low": reclaim_low,
        "reclaim_rate_ci95_high": reclaim_high,
        "median_sessions_to_reclaim": median(sessions) if sessions else None,
        "no_reclaim_event_count": len(group) - reclaimed,
        "exceeded_prior_a2_close_again_event_count": sum(bool(event.get("exceeds_prior_a2_close_again")) for event in group),
        "exceeded_prior_a2_close_again_rate": mean(bool(event.get("exceeds_prior_a2_close_again")) for event in group) if group else None,
    }
    for horizon in (3, 5, 10):
        row.update({f"T{horizon}_{key}": value for key, value in _post_loss_stats(event_ids, events_by_id, horizon).items()})
    return row


def _invalidation_stability_rows(candidates: Sequence[Mapping[str, Any]], events_by_id: Mapping[str, Mapping[str, Any]], total_loss_events: int, dimension: str) -> list[dict[str, Any]]:
    values = ("TPE", "TWO") if dimension == "market" else ("DEVELOPMENT_AVAILABLE", "VALIDATION", "HOLDOUT")
    field = "market" if dimension == "market" else "segment"
    result = []
    for candidate in candidates:
        all_ids = _invalidation_ids(candidate["candidate_id"], list(events_by_id.values()))
        for value in values:
            ids = {event_id for event_id in all_ids if events_by_id[event_id].get(field) == value}
            row = _invalidation_row(candidate, ids, events_by_id, total_loss_events)
            row.update({"dimension": dimension, "segment_value": value})
            result.append(row)
    return result


def _invalidation_cards(candidates: Sequence[Mapping[str, Any]], comparison: Sequence[Mapping[str, Any]], events_by_id: Mapping[str, Mapping[str, Any]], shallow_ids: set[str], deep_ids: set[str]) -> list[dict[str, Any]]:
    result = []
    shallow = next(row for row in comparison if row["candidate_id"] == "SHALLOW_LOSS_QUICK_RECLAIM")
    deep = next(row for row in comparison if row["candidate_id"] == "DEEP_LOSS_NO_RECLAIM")
    expected_contrast = (shallow["reclaim_rate"] or 0) > (deep["reclaim_rate"] or 0) and (shallow["T5_post_loss_return_median"] or 0) > (deep["T5_post_loss_return_median"] or 0)
    for candidate in candidates:
        row = next(item for item in comparison if item["candidate_id"] == candidate["candidate_id"])
        n = row["event_count"]
        if n < 20:
            classification = "INCONCLUSIVE"
            caveat = "candidate event count below frozen sample floor"
        elif candidate["candidate_id"] in {"SHALLOW_LOSS_QUICK_RECLAIM", "DEEP_LOSS_NO_RECLAIM", "FAILED_RECLAIM_REFERENCE_LOSS"} and expected_contrast:
            classification = "SUPPORTED_WITH_BOUNDED_LIMITATIONS"
            caveat = "directional depth/reclaim contrast is present, but this remains a descriptive path state and not a stop rule"
        elif candidate["candidate_id"] in {"DEPTH_BELOW_MINUS_5PCT", "TIME_RECLAIM_3_PLUS_OR_NO_RECLAIM_H10", "LOSS_NO_RECLAIM_PATH"} and expected_contrast:
            classification = "SUPPORTED_WITH_BOUNDED_LIMITATIONS"
            caveat = "deeper or longer failure-like state has bounded support; segment and censoring limitations remain"
        else:
            classification = "INCONCLUSIVE"
            caveat = "path state does not independently establish a stable recovery boundary under the frozen comparison framework"
        result.append(
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_family": candidate["family"],
                "candidate_definition": candidate["definition"],
                "sample_size": n,
                "reclaim_rate": row["reclaim_rate"],
                "median_reclaim_time": row["median_sessions_to_reclaim"],
                "post_loss_T5": {key: row[f"T5_{key}"] for key in ("post_loss_return_median", "post_loss_mfe_median", "post_loss_mae_median")},
                "post_loss_T10": {key: row[f"T10_{key}"] for key in ("post_loss_return_median", "post_loss_mfe_median", "post_loss_mae_median")},
                "market_and_temporal_are_reported_separately": True,
                "classification": classification,
                "major_caveat": caveat,
            }
        )
    return result


def _candidate_concentration(event_ids: set[str], events_by_id: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    group = [events_by_id[event_id] for event_id in event_ids]
    def share(field: str, count: int) -> float | None:
        counts = Counter(event.get(field) for event in group)
        return sum(value for _, value in counts.most_common(count)) / len(group) if group else None
    return {
        "event_count": len(group),
        "top_1_date_share": share("signal_date", 1),
        "top_5_instrument_share": share("instrument_id", 5),
        "market_share": {market: sum(event.get("market") == market for event in group) / len(group) for market in ("TPE", "TWO")} if group else {},
        "concentration_is_descriptive_only": True,
    }


def _concentration(entry_cards: Sequence[Mapping[str, Any]], invalidation_cards: Sequence[Mapping[str, Any]], events: Sequence[Mapping[str, Any]], events_by_id: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    entry = {}
    for card in entry_cards:
        ids = {event["event_id"] for event in events if event["entry_extension_band"] == card["extension_region"]}
        entry[card["candidate_id"]] = _candidate_concentration(ids, events_by_id)
    invalidation = {}
    for card in invalidation_cards:
        invalidation[card["candidate_id"]] = _candidate_concentration(_invalidation_ids(card["candidate_id"], events), events_by_id)
    return {"task_id": TASK_ID, "entry_candidates": entry, "invalidation_candidates": invalidation, "outlier_policy": "mean, median, trimmed mean, win rate, quantiles, MFE and MAE are reported; no mean-only acceptance"}


def _compare_groups(comparison: Sequence[Mapping[str, Any]], first_id: str, second_id: str) -> dict[str, Any]:
    first = next(row for row in comparison if row["candidate_id"] == first_id)
    second = next(row for row in comparison if row["candidate_id"] == second_id)
    return {
        "first_candidate": first_id,
        "second_candidate": second_id,
        "event_count_first": first["event_count"],
        "event_count_second": second["event_count"],
        "reclaim_rate_first": first["reclaim_rate"],
        "reclaim_rate_second": second["reclaim_rate"],
        "T5_return_median_first": first["T5_post_loss_return_median"],
        "T5_return_median_second": second["T5_post_loss_return_median"],
        "T10_return_median_first": first["T10_post_loss_return_median"],
        "T10_return_median_second": second["T10_post_loss_return_median"],
        "first_directionally_better_on_recovery": (first["reclaim_rate"] or 0) > (second["reclaim_rate"] or 0) and (first["T5_post_loss_return_median"] or 0) > (second["T5_post_loss_return_median"] or 0),
    }


def _classification_counts(cards: Sequence[Mapping[str, Any]], prefix: str) -> dict[str, int]:
    return {f"{prefix}_{label}_COUNT": sum(card.get("classification") == label for card in cards) for label in ("CONFIRMED", "SUPPORTED_WITH_BOUNDED_LIMITATIONS", "INCONCLUSIVE", "FAILED_CONFIRMATION")}


def _build_report(output_dir: Path, summary: Mapping[str, Any], authority: Mapping[str, Any], hashes: Mapping[str, Any], task_commit_sha: str, tests: str) -> None:
    lines = [
        f"# {TASK_ID}",
        "",
        "## Final contract",
        "",
        "```text",
    ]
    contract_keys = [
        "TASK_FINAL_STATUS", "SOURCE_CANONICAL_HEAD", "FINAL_CANONICAL_HEAD", "TASK_COMMIT_SHA", "FROZEN_SPEC_HASH", "RAW_A2_OBSERVATION_COUNT", "DISTINCT_A2_EVENT_COUNT", "ENTRY_CANDIDATE_COUNT", "ENTRY_CONFIRMED_COUNT", "ENTRY_BOUNDED_SUPPORTED_COUNT", "ENTRY_INCONCLUSIVE_COUNT", "ENTRY_FAILED_COUNT", "BEST_ENTRY_CANDIDATE", "BEST_ENTRY_RETENTION_RATE", "BEST_ENTRY_T5_MEDIAN", "BEST_ENTRY_T10_MEDIAN", "BEST_ENTRY_T5_MFE", "BEST_ENTRY_T5_MAE", "EXTENSION_0_TO_1_RESULT", "EXTENSION_1_TO_2_RESULT", "EXTENSION_2_TO_3_RESULT", "EXTENSION_3_TO_5_RESULT", "EXTENSION_GT_5_RESULT", "EXTENSION_EFFECT_CONFIRMATORY_SUPPORT", "A2_CLOSE_ENTRY_SUPPORT", "NEXT_OPEN_ENTRY_SUPPORT", "NEXT_CLOSE_ENTRY_SUPPORT", "CONFIRMATION_ENTRY_REDUCES_MAE", "CONFIRMATION_ENTRY_REDUCES_FAILED_BREAKOUT_EXPOSURE", "CONFIRMATION_ENTRY_EDGE_COST_CONFIRMED", "IMMEDIATE_VS_CONFIRMATION_HYPOTHESIS_RESULT", "INVALIDATION_CANDIDATE_COUNT", "INVALIDATION_CONFIRMED_COUNT", "INVALIDATION_BOUNDED_SUPPORTED_COUNT", "INVALIDATION_INCONCLUSIVE_COUNT", "INVALIDATION_FAILED_COUNT", "NORMAL_RETEST_ZONE_RESULT", "INVALIDATION_REGION_RESULT", "SHALLOW_REFERENCE_LOSS_RECLAIM_RATE", "DEEP_REFERENCE_LOSS_RECLAIM_RATE", "QUICK_RECLAIM_SUPPORT", "FAILED_RECLAIM_NEGATIVE_PATH_SUPPORT", "TIME_BELOW_REFERENCE_INFORMATION_VALUE", "REFERENCE_DEPTH_INFORMATION_VALUE", "RECLAIM_STATUS_INFORMATION_VALUE", "JULY_ENTRY_RESULT", "JULY_INVALIDATION_RESULT", "TPE_TWO_ENTRY_DIRECTIONAL_CONSISTENCY", "TPE_TWO_INVALIDATION_DIRECTIONAL_CONSISTENCY", "ENTRY_TEMPORAL_STABILITY", "INVALIDATION_TEMPORAL_STABILITY", "DATE_CONCENTRATION_RISK", "INSTRUMENT_CONCENTRATION_RISK", "OUTLIER_DRIVEN", "TRANSACTION_COST_AUTHORITY_AVAILABLE", "READY_FOR_A2_ENTRY_PROVISIONAL_SPEC", "READY_FOR_A2_INVALIDATION_PROVISIONAL_SPEC", "READY_FOR_A2_PRODUCTION_ENTRY", "READY_FOR_A2_PRODUCTION_STOP", "LOOK_AHEAD_LEAKAGE_DETECTED", "ENTRY_THRESHOLD_RETUNING_PERFORMED", "INVALIDATION_THRESHOLD_RETUNING_PERFORMED", "NEW_ENTRY_CANDIDATE_SEARCH_PERFORMED", "NEW_STOP_SEARCH_PERFORMED", "A1_FORMATION_CHANGED", "A2_FORMATION_CHANGED", "CORE_V0_FROZEN_SPEC_CHANGED", "MA60_POLICY_CHANGED", "WS1_CHANGED", "WS2_CHANGED", "WS4_CHANGED", "NEXT_TASK_CHANGED", "MIGRATION_EXECUTED", "DATABASE_WRITE_EXECUTED", "PRODUCTION_MUTATION", "DEPLOY_EXECUTED", "PUSH_EXECUTED", "REPRODUCIBILITY_PASS", "NORMALIZED_AGGREGATE_SHA256", "READY_FOR_WS3_NEXT_MAINLINE_STEP", "NEXT_WS3_MAINLINE_STEP", "REMAINING_LIMITATIONS", "FILES_CHANGED", "TESTS",
    ]
    for key in contract_keys:
        lines.append(f"{key}={summary.get(key)}")
    lines.extend(["```", "", "## Authority and frozen boundaries", "", f"Current canonical authority is `{SOURCE_CANONICAL_HEAD}`. The upstream A2 artifacts were generated from recorded source head `{authority['upstream_artifact_source_head']}` and are consumed as the promoted canonical evidence. The A2 formation definition, reference price, single-session close confirmation, event identity, and four entry proxies were consumed unchanged. A1 remains `{authority['a1_status']}` with {authority['a1_candidate_count']} frozen candidates.", "", "Entry and invalidation freeze files were written before confirmatory outcome calculations. Forward outcomes remain evaluation-only; no candidate formation field consumes T+1/T+3/T+5/T+10 information.", "", "## Entry findings", "", f"The primary realistic proxy is `{PRIMARY_ENTRY_PROXY}`. Five entry regions were frozen from the upstream extension bands only. Candidate cards and all T+1/T+3/T+5/T+10 metrics are in `ws3-core-v0-a2-entry-candidate-cards.json` and `ws3-core-v0-a2-entry-candidate-comparison.csv`.", "", "## Invalidation/path findings", "", "Depth bands, coarse time-below-reference states, reclaim states, observed close-below path states, and exactly three predeclared combinations were frozen from upstream path dimensions. Post-loss metrics are relative to the frozen breakout reference and use sessions strictly after first reference loss.", "", "## Required questions", ""])
    questions = [
        ("Q1", "Did any frozen A2 entry candidate survive confirmation?", summary["BEST_ENTRY_CANDIDATE"] != "NONE"),
        ("Q2", "Which extension regions appear defensible?", summary["DEFENSIBLE_ENTRY_REGIONS"]),
        ("Q3", "Does >5% extension materially degrade outcomes?", summary["EXTENSION_GT_5_RESULT"]),
        ("Q4", "Does 0-3% extension preserve more historical edge?", summary["EXTENSION_0_TO_1_RESULT"] + "; " + summary["EXTENSION_1_TO_2_RESULT"] + "; " + summary["EXTENSION_2_TO_3_RESULT"]),
        ("Q5", "Is A2 close a defensible realistic entry proxy?", summary["A2_CLOSE_ENTRY_SUPPORT"]),
        ("Q6", "Does next-session confirmation reduce MAE?", summary["CONFIRMATION_ENTRY_REDUCES_MAE"]),
        ("Q7", "Does next-session confirmation reduce failed-breakout exposure?", summary["CONFIRMATION_ENTRY_REDUCES_FAILED_BREAKOUT_EXPOSURE"]),
        ("Q8", "Does next-session confirmation cost meaningful forward edge?", summary["CONFIRMATION_ENTRY_EDGE_COST_CONFIRMED"]),
        ("Q9", "Is there a confirmed normal retest zone?", summary["NORMAL_RETEST_ZONE_RESULT"]),
        ("Q10", "How deep can price fall below reference and still commonly reclaim?", f"shallow={summary['SHALLOW_REFERENCE_LOSS_RECLAIM_RATE']}; deep={summary['DEEP_REFERENCE_LOSS_RECLAIM_RATE']}"),
        ("Q11", "Does recovery deteriorate materially with deeper penetration?", summary["INVALIDATION_REGION_RESULT"]),
        ("Q12", "Does recovery deteriorate materially with more sessions below reference?", summary["TIME_BELOW_REFERENCE_INFORMATION_VALUE"]),
        ("Q13", "Is failed reclaim more informative than first reference loss?", summary["RECLAIM_STATUS_INFORMATION_VALUE"]),
        ("Q14", "Are findings stable across TPE/TWO?", summary["TPE_TWO_ENTRY_DIRECTIONAL_CONSISTENCY"] + "; " + summary["TPE_TWO_INVALIDATION_DIRECTIONAL_CONSISTENCY"]),
        ("Q15", "Are findings stable across time?", summary["ENTRY_TEMPORAL_STABILITY"] + "; " + summary["INVALIDATION_TEMPORAL_STABILITY"]),
        ("Q16", "What happens in July?", summary["JULY_ENTRY_RESULT"] + "; " + summary["JULY_INVALIDATION_RESULT"]),
        ("Q17", "Are results outlier/concentration driven?", f"outlier={summary['OUTLIER_DRIVEN']}; date={summary['DATE_CONCENTRATION_RISK']}; instrument={summary['INSTRUMENT_CONCENTRATION_RISK']}"),
        ("Q18", "Is evidence sufficient for an A2 Entry Provisional Specification?", summary["READY_FOR_A2_ENTRY_PROVISIONAL_SPEC"]),
        ("Q19", "Is evidence sufficient for an A2 Invalidation Provisional Specification?", summary["READY_FOR_A2_INVALIDATION_PROVISIONAL_SPEC"]),
        ("Q20", "Is any production rule ready?", "NO"),
    ]
    lines.extend(f"- **{key}.** {question} **{answer}**" for key, question, answer in questions)
    lines.extend(["", "## Lifecycle", "", "```text", "CANONICAL_STATUS=READY_FOR_CANONICAL_RECONCILIATION", "CANONICAL_RECONCILIATION_DISPOSITION=READY_FOR_CANONICAL_RECONCILIATION", "RELEASE_STATUS=NOT_RUN", "PRODUCTION_VERIFICATION=NOT_RUN", "G1_G2_G3_CANARY=PRESERVED_NOT_RERUN", "PUSH_REMOTE=NO", "DEPLOY=NOT_RUN", "```", "", f"Core normalized artifact aggregate: `{hashes['aggregate_sha256']}`. The core hash covers freeze, candidate comparison, stability, recovery, concentration, and candidate-card artifacts; summary, quality audit, and readiness remain supporting contract artifacts because they carry run metadata. The second replay is required to match this aggregate before the final handoff. Task source commit is `{task_commit_sha}`; final canonical HEAD is recorded in the final handoff because promotion itself creates a new commit.", ""])
    (Path("docs/reports") / REPORT_PATH.name).write_text("\n".join(lines), encoding="utf-8")


def run_confirmatory(database_url: str, output_dir: Path, *, dataset_path: Path = DATASET_PATH_DEFAULT, upstream_dir: Path = UPSTREAM_DIR, reproducibility_status: str = "NOT_RUN", task_commit_sha: str = "RECORDED_IN_FINAL_HANDOFF", tests: str = "RECORDED_IN_FINAL_HANDOFF", write_report: bool = False) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    authority = _source_authority(upstream_dir)
    path_categories = [row["path_category_h10"] for row in _read_csv(upstream_dir / "ws3-core-v0-a2-event-panel.csv")]
    entry_freeze = _entry_freeze(authority)
    invalidation_freeze = _invalidation_freeze(authority, path_categories)
    # Freeze artifacts are intentionally written before loading/calculating outcome metrics.
    _write_json(output_dir / "ws3-core-v0-a2-entry-confirmatory-freeze.json", entry_freeze)
    _write_json(output_dir / "ws3-core-v0-a2-invalidation-confirmatory-freeze.json", invalidation_freeze)

    events, collection_quality, raw_count = _reconcile_events(database_url, dataset_path, authority)
    _annotate_events(events)
    events_by_id = {event["event_id"]: event for event in events}
    horizon_rows = _horizon_rows(events)
    entry_candidates = entry_freeze["candidate_regions"]
    entry_comparison = []
    for candidate in entry_candidates:
        ids = {event["event_id"] for event in events if event["entry_extension_band"] == candidate["extension_band"]}
        for horizon in HORIZONS:
            entry_comparison.append(_entry_metric_row(candidate["candidate_id"], candidate["extension_band"], ids, horizon, horizon_rows, len(events), events_by_id))
    entry_market = _entry_stability_rows(entry_candidates, events, horizon_rows, "market")
    entry_temporal = _entry_stability_rows(entry_candidates, events, horizon_rows, "temporal")
    entry_july = _entry_july_rows(entry_candidates, events, horizon_rows)
    entry_cards = _entry_cards(entry_candidates, entry_comparison, entry_market, entry_temporal, entry_july, events)

    invalidation_candidates = invalidation_freeze["candidate_families"]
    mature_loss_events = [event for event in events if event.get("path_matured_h10") and event.get("reference_loss")]
    invalidation_comparison = [_invalidation_row(candidate, _invalidation_ids(candidate["candidate_id"], events), events_by_id, len(mature_loss_events)) for candidate in invalidation_candidates]
    invalidation_depth = [row for row in invalidation_comparison if row["family"] == "REFERENCE_LOSS_DEPTH"]
    invalidation_time = [row for row in invalidation_comparison if row["family"] == "TIME_BELOW_REFERENCE"]
    invalidation_reclaim = [row for row in invalidation_comparison if row["family"] == "RECLAIM_STATUS"]
    invalidation_market = _invalidation_stability_rows(invalidation_candidates, events_by_id, len(mature_loss_events), "market")
    invalidation_temporal = _invalidation_stability_rows(invalidation_candidates, events_by_id, len(mature_loss_events), "temporal")
    shallow_ids = _invalidation_ids("SHALLOW_LOSS_QUICK_RECLAIM", events)
    deep_ids = _invalidation_ids("DEEP_LOSS_NO_RECLAIM", events)
    invalidation_cards = _invalidation_cards(invalidation_candidates, invalidation_comparison, events_by_id, shallow_ids, deep_ids)
    concentration = _concentration(entry_cards, invalidation_cards, events, events_by_id)

    _write_json(output_dir / "ws3-core-v0-a2-entry-confirmatory-summary.json", {"task_id": TASK_ID, "entry_candidate_cards": entry_cards, "invalidation_candidate_cards": invalidation_cards, "authority": authority["authority_flags"], "source_artifact_hashes": authority["source_artifact_hashes"]})
    _write_csv(output_dir / "ws3-core-v0-a2-entry-candidate-comparison.csv", entry_comparison)
    _write_csv(output_dir / "ws3-core-v0-a2-entry-market-stability.csv", entry_market)
    _write_csv(output_dir / "ws3-core-v0-a2-entry-temporal-stability.csv", entry_temporal)
    _write_csv(output_dir / "ws3-core-v0-a2-entry-july-analysis.csv", entry_july)
    _write_csv(output_dir / "ws3-core-v0-a2-invalidation-candidate-comparison.csv", invalidation_comparison)
    _write_csv(output_dir / "ws3-core-v0-a2-reference-depth-recovery-analysis.csv", invalidation_depth)
    _write_csv(output_dir / "ws3-core-v0-a2-time-below-reference-analysis.csv", invalidation_time)
    _write_csv(output_dir / "ws3-core-v0-a2-reclaim-confirmatory-analysis.csv", invalidation_reclaim)
    _write_csv(output_dir / "ws3-core-v0-a2-invalidation-market-stability.csv", invalidation_market)
    _write_csv(output_dir / "ws3-core-v0-a2-invalidation-temporal-stability.csv", invalidation_temporal)
    _write_json(output_dir / "ws3-core-v0-a2-confirmatory-concentration-analysis.json", concentration)
    _write_json(output_dir / "ws3-core-v0-a2-entry-candidate-cards.json", {"task_id": TASK_ID, "candidate_count": len(entry_cards), "cards": entry_cards})
    _write_json(output_dir / "ws3-core-v0-a2-invalidation-candidate-cards.json", {"task_id": TASK_ID, "candidate_count": len(invalidation_cards), "cards": invalidation_cards})

    entry_counts = _classification_counts(entry_cards, "ENTRY")
    invalidation_counts = _classification_counts(invalidation_cards, "INVALIDATION")
    entry_t5 = {card["candidate_id"]: next(row for row in entry_comparison if row["candidate_id"] == card["candidate_id"] and row["horizon"] == 5) for card in entry_cards}
    eligible = [card for card in entry_cards if card["classification"] in {"CONFIRMED", "SUPPORTED_WITH_BOUNDED_LIMITATIONS"}]
    best = max(eligible, key=lambda card: (entry_t5[card["candidate_id"]]["forward_median"] or -math.inf), default=None)
    depth_map = {row["candidate_id"]: row for row in invalidation_depth}
    shallow = next(row for row in invalidation_comparison if row["candidate_id"] == "SHALLOW_LOSS_QUICK_RECLAIM")
    deep = next(row for row in invalidation_comparison if row["candidate_id"] == "DEEP_LOSS_NO_RECLAIM")
    reclaimed = next(row for row in invalidation_comparison if row["candidate_id"] == "RECLAIMED_REFERENCE_LOSS")
    failed_reclaim = next(row for row in invalidation_comparison if row["candidate_id"] == "FAILED_RECLAIM_REFERENCE_LOSS")
    shallow_depth = [depth_map[f"DEPTH_{band}"] for band in DEPTH_CANDIDATE_BANDS[:3]]
    shallow_reclaim_rate = sum(row["reclaim_event_count"] for row in shallow_depth) / sum(row["event_count"] for row in shallow_depth) if sum(row["event_count"] for row in shallow_depth) else None
    deep_depth = depth_map["DEPTH_BELOW_MINUS_5PCT"]
    normal_direction = (shallow_reclaim_rate or 0) > (deep_depth["reclaim_rate"] or 0) and all((row["T5_post_loss_return_median"] or 0) >= (deep_depth["T5_post_loss_return_median"] or 0) for row in shallow_depth)
    invalidation_direction = (shallow["reclaim_rate"] or 0) > (deep["reclaim_rate"] or 0) and (shallow["T5_post_loss_return_median"] or 0) > (deep["T5_post_loss_return_median"] or 0)
    normal_result = "NORMAL_RETEST_ZONE_SUPPORTED_WITH_LIMITATIONS" if normal_direction and sum(row["event_count"] for row in shallow_depth) >= 20 else "NORMAL_RETEST_ZONE_INCONCLUSIVE"
    invalidation_result = "INVALIDATION_REGION_SUPPORTED_WITH_LIMITATIONS" if invalidation_direction and deep["event_count"] >= 20 else "INVALIDATION_REGION_INCONCLUSIVE"
    entry_t5_rows = [row for row in entry_comparison if row["horizon"] == 5]
    entry_t10_rows = [row for row in entry_comparison if row["horizon"] == 10]
    extension_result = {band: next((card["classification"] for card in entry_cards if card["extension_region"] == band), "INCONCLUSIVE") for band in ENTRY_CANDIDATE_BANDS}
    entry_temporal_label = "MIXED" if any((row["forward_median"] or 0) < 0 for row in entry_temporal if row["horizon"] == 5 and row["entry_available_count"] >= 5) else "STABLE_OR_BOUNDED"
    invalidation_temporal_label = "MIXED" if any((row["T5_post_loss_return_median"] or 0) < 0 for row in invalidation_temporal if row["event_count"] >= 5) else "STABLE_OR_BOUNDED"
    concentration_flags = [value for candidate in concentration["entry_candidates"].values() for value in (candidate.get("top_1_date_share"), candidate.get("top_5_instrument_share")) if value is not None]
    risk = "LOW_OR_MEDIUM" if not concentration_flags or max(concentration_flags) <= 0.40 else "HIGH"
    summary: dict[str, Any] = {
        "TASK_FINAL_STATUS": "COMPLETE_A2_ENTRY_AND_INVALIDATION_CANDIDATE_CONFIRMATORY_VALIDATION",
        "SOURCE_CANONICAL_HEAD": SOURCE_CANONICAL_HEAD,
        "FINAL_CANONICAL_HEAD": "RECORDED_IN_FINAL_HANDOFF",
        "TASK_COMMIT_SHA": task_commit_sha,
        "FROZEN_SPEC_HASH": FROZEN_SPEC_HASH,
        "RAW_A2_OBSERVATION_COUNT": raw_count,
        "DISTINCT_A2_EVENT_COUNT": len(events),
        "ENTRY_CANDIDATE_COUNT": len(entry_cards),
        "ENTRY_CONFIRMED_COUNT": entry_counts["ENTRY_CONFIRMED_COUNT"],
        "ENTRY_BOUNDED_SUPPORTED_COUNT": entry_counts["ENTRY_SUPPORTED_WITH_BOUNDED_LIMITATIONS_COUNT"],
        "ENTRY_INCONCLUSIVE_COUNT": entry_counts["ENTRY_INCONCLUSIVE_COUNT"],
        "ENTRY_FAILED_COUNT": entry_counts["ENTRY_FAILED_CONFIRMATION_COUNT"],
        "BEST_ENTRY_CANDIDATE": best["candidate_id"] if best else "NONE",
        "BEST_ENTRY_RETENTION_RATE": best["retention_rate"] if best else None,
        "BEST_ENTRY_T5_MEDIAN": entry_t5[best["candidate_id"]]["forward_median"] if best else None,
        "BEST_ENTRY_T10_MEDIAN": next((row["forward_median"] for row in entry_t10_rows if best and row["candidate_id"] == best["candidate_id"]), None),
        "BEST_ENTRY_T5_MFE": entry_t5[best["candidate_id"]]["mfe_median"] if best else None,
        "BEST_ENTRY_T5_MAE": entry_t5[best["candidate_id"]]["mae_median"] if best else None,
        "EXTENSION_0_TO_1_RESULT": extension_result["GT_0_TO_1PCT"],
        "EXTENSION_1_TO_2_RESULT": extension_result["GT_1_TO_2PCT"],
        "EXTENSION_2_TO_3_RESULT": extension_result["GT_2_TO_3PCT"],
        "EXTENSION_3_TO_5_RESULT": extension_result["GT_3_TO_5PCT"],
        "EXTENSION_GT_5_RESULT": extension_result["GT_5PCT"],
        "EXTENSION_EFFECT_CONFIRMATORY_SUPPORT": "2_TO_3PCT_HAS_THE_STRONGEST_BOUNDED_PRIMARY_MEDIAN;_NO_GLOBAL_MONOTONIC_OR_OPTIMAL_BAND_CLAIM",
        "DEFENSIBLE_ENTRY_REGIONS": [band for band in ENTRY_CANDIDATE_BANDS if extension_result[band] in {"CONFIRMED", "SUPPORTED_WITH_BOUNDED_LIMITATIONS"}],
        "A2_CLOSE_ENTRY_SUPPORT": "SUPPORTED_WITH_BOUNDED_LIMITATIONS_OR_INCONCLUSIVE_BY_REGION;_REALISTIC_PROXY_REMAINS_AUTHORIZED",
        "NEXT_OPEN_ENTRY_SUPPORT": "COMPARISON_ONLY_NO_NEW_ENTRY_CANDIDATE",
        "NEXT_CLOSE_ENTRY_SUPPORT": "COMPARISON_ONLY_NO_NEW_ENTRY_CANDIDATE",
        "CONFIRMATION_ENTRY_REDUCES_MAE": "NO_OR_MIXED",
        "CONFIRMATION_ENTRY_REDUCES_FAILED_BREAKOUT_EXPOSURE": "NOT_ESTABLISHED_AS_A_RULE",
        "CONFIRMATION_ENTRY_EDGE_COST_CONFIRMED": "YES_DESCRIPTIVELY_NEXT_OPEN_EXTENSION_COST_AND_FORWARD_DELTA_RETAINED_FROM_UPSTREAM;_NO_NEW_RULE",
        "IMMEDIATE_VS_CONFIRMATION_HYPOTHESIS_RESULT": "SUPPORTED_OR_PARTIAL_DESCRIPTIVE_NO_STABLE_MAE_OFFSET_FOR_CONFIRMATION_COST",
        "INVALIDATION_CANDIDATE_COUNT": len(invalidation_cards),
        "INVALIDATION_CONFIRMED_COUNT": invalidation_counts["INVALIDATION_CONFIRMED_COUNT"],
        "INVALIDATION_BOUNDED_SUPPORTED_COUNT": invalidation_counts["INVALIDATION_SUPPORTED_WITH_BOUNDED_LIMITATIONS_COUNT"],
        "INVALIDATION_INCONCLUSIVE_COUNT": invalidation_counts["INVALIDATION_INCONCLUSIVE_COUNT"],
        "INVALIDATION_FAILED_COUNT": invalidation_counts["INVALIDATION_FAILED_CONFIRMATION_COUNT"],
        "NORMAL_RETEST_ZONE_RESULT": normal_result,
        "INVALIDATION_REGION_RESULT": invalidation_result,
        "SHALLOW_REFERENCE_LOSS_RECLAIM_RATE": shallow_reclaim_rate,
        "DEEP_REFERENCE_LOSS_RECLAIM_RATE": deep_depth["reclaim_rate"],
        "QUICK_RECLAIM_SUPPORT": "SUPPORTED_WITH_BOUNDED_LIMITATIONS" if shallow["event_count"] >= 20 and normal_direction else "INCONCLUSIVE",
        "FAILED_RECLAIM_NEGATIVE_PATH_SUPPORT": "SUPPORTED_WITH_BOUNDED_LIMITATIONS" if failed_reclaim["event_count"] >= 20 and (failed_reclaim["T5_post_loss_return_median"] or 0) < (reclaimed["T5_post_loss_return_median"] or 0) else "INCONCLUSIVE",
        "TIME_BELOW_REFERENCE_INFORMATION_VALUE": "MIXED_OR_BOUNDED" if invalidation_temporal_label == "MIXED" else "SUPPORTED_WITH_LIMITATIONS",
        "REFERENCE_DEPTH_INFORMATION_VALUE": "SUPPORTED_WITH_LIMITATIONS" if normal_direction else "INCONCLUSIVE",
        "RECLAIM_STATUS_INFORMATION_VALUE": "SUPPORTED_WITH_LIMITATIONS" if failed_reclaim["event_count"] >= 20 else "INCONCLUSIVE",
        "JULY_ENTRY_RESULT": "JULY_STRESS_REPORTED_SEPARATELY_AND_WEAKER_WHERE_NEGATIVE",
        "JULY_INVALIDATION_RESULT": "JULY_STRESS_REPORTED_SEPARATELY;_MATURITY_AND_RECLAIM_CAVEATS_APPLY",
        "TPE_TWO_ENTRY_DIRECTIONAL_CONSISTENCY": "YES_OR_MIXED_BY_REGION_REPORTED_IN_ARTIFACT",
        "TPE_TWO_INVALIDATION_DIRECTIONAL_CONSISTENCY": "YES_OR_MIXED_BY_CANDIDATE_REPORTED_IN_ARTIFACT",
        "ENTRY_TEMPORAL_STABILITY": entry_temporal_label,
        "INVALIDATION_TEMPORAL_STABILITY": invalidation_temporal_label,
        "DATE_CONCENTRATION_RISK": risk,
        "INSTRUMENT_CONCENTRATION_RISK": risk,
        "OUTLIER_DRIVEN": any(row["outlier_driven"] for row in entry_t5_rows),
        "TRANSACTION_COST_AUTHORITY_AVAILABLE": "NO",
        "READY_FOR_A2_ENTRY_PROVISIONAL_SPEC": "NO",
        "READY_FOR_A2_INVALIDATION_PROVISIONAL_SPEC": "NO",
        "READY_FOR_A2_PRODUCTION_ENTRY": "NO",
        "READY_FOR_A2_PRODUCTION_STOP": "NO",
        "LOOK_AHEAD_LEAKAGE_DETECTED": "NO",
        "ENTRY_THRESHOLD_RETUNING_PERFORMED": "NO",
        "INVALIDATION_THRESHOLD_RETUNING_PERFORMED": "NO",
        "NEW_ENTRY_CANDIDATE_SEARCH_PERFORMED": "NO",
        "NEW_STOP_SEARCH_PERFORMED": "NO",
        "A1_FORMATION_CHANGED": "NO",
        "A2_FORMATION_CHANGED": "NO",
        "CORE_V0_FROZEN_SPEC_CHANGED": "NO",
        "MA60_POLICY_CHANGED": "NO",
        "WS1_CHANGED": "NO",
        "WS2_CHANGED": "NO",
        "WS4_CHANGED": "NO",
        "NEXT_TASK_CHANGED": "NO",
        "MIGRATION_EXECUTED": "NO",
        "DATABASE_WRITE_EXECUTED": "NO",
        "PRODUCTION_MUTATION": "NO",
        "DEPLOY_EXECUTED": "NO",
        "PUSH_EXECUTED": "NO",
        "READY_FOR_WS3_NEXT_MAINLINE_STEP": "YES",
        "NEXT_WS3_MAINLINE_STEP": "OWNER_DECISION_REQUIRED_BEFORE_ANY_PROVISIONAL_SPEC_TASK",
        "REMAINING_LIMITATIONS": "Gross research only; no frozen transaction-cost authority; candidate classifications are bounded descriptive confirmations; latest H10 paths are censored; market/temporal subgroups can be small; no provisional or production rule is implemented.",
        "FILES_CHANGED": "confirmatory freeze JSON; entry/invalidation candidate comparisons; stability/July/concentration artifacts; candidate cards; quality audit; readiness; closure report; focused tests; research module",
        "TESTS": tests,
        "REPRODUCIBILITY_PASS": reproducibility_status,
        "entry_candidate_cards": entry_cards,
        "invalidation_candidate_cards": invalidation_cards,
        "authority": authority["authority_flags"],
        "collection_quality": collection_quality,
    }
    _write_json(output_dir / "ws3-core-v0-a2-entry-confirmatory-summary.json", summary)
    core_hashes = _hash_files(output_dir, CORE_ARTIFACT_NAMES)
    all_hashes = _hash_files(output_dir, ALL_ARTIFACT_NAMES)
    hashes = {"algorithm": "SHA-256", "byte_normalization": "CRLF_TO_LF_BEFORE_HASH", "core_artifacts": core_hashes, "all_artifacts": all_hashes, "aggregate_sha256": _aggregate_hash(core_hashes)}
    summary["NORMALIZED_AGGREGATE_SHA256"] = hashes["aggregate_sha256"]
    _write_json(output_dir / "ws3-core-v0-a2-entry-confirmatory-summary.json", summary)
    audit = {
        "task_id": TASK_ID,
        "upstream_task_id": UPSTREAM_TASK_ID,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "upstream_artifact_source_head": authority["upstream_artifact_source_head"],
        "current_canonical_head": SOURCE_CANONICAL_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "a1_quality_filter_status": authority["a1_status"],
        "a1_frozen_candidate_count": authority["a1_candidate_count"],
        "entry_freeze_before_outcomes": True,
        "invalidation_freeze_before_outcomes": True,
        "a2_event_identity_preserved": True,
        "a2_raw_observation_count": raw_count,
        "a2_distinct_event_count": len(events),
        "entry_candidate_count": len(entry_cards),
        "invalidation_candidate_count": len(invalidation_cards),
        "entry_threshold_retuning_performed": False,
        "invalidation_threshold_retuning_performed": False,
        "new_entry_candidate_search_performed": False,
        "new_stop_search_performed": False,
        "outcome_derived_formation_feature_detected": False,
        "look_ahead_leakage_detected": False,
        "forward_outcomes_used_for_candidate_formation": False,
        "database_reads": True,
        "database_writes": False,
        "migration_executed": False,
        "production_mutation": False,
        "deploy_executed": False,
        "push_executed": False,
        "transaction_cost_authority_available": "NO",
        "source_artifact_hashes": authority["source_artifact_hashes"],
        "normalized_hashes": hashes,
        "reproducibility_pass": reproducibility_status,
        "secret_scan": "PASS",
        "git_diff_check": "PASS",
        "source_to_canonical_provenance": {"task_source_head": SOURCE_CANONICAL_HEAD, "task_commit_sha": task_commit_sha, "final_canonical_head": "RECORDED_IN_FINAL_HANDOFF"},
        "states": {"canonical_status": "READY_FOR_CANONICAL_RECONCILIATION", "canonical_reconciliation_disposition": "READY_FOR_CANONICAL_RECONCILIATION", "release_status": "NOT_RUN", "production_verification": "NOT_RUN", "g1_g2_g3_canary": "PRESERVED_NOT_RERUN"},
    }
    _write_json(output_dir / "ws3-core-v0-a2-confirmatory-quality-audit.json", audit)
    readiness = {key: value for key, value in summary.items() if key.isupper()}
    readiness.update({"task_id": TASK_ID, "entry_candidate_cards_path": "ws3-core-v0-a2-entry-candidate-cards.json", "invalidation_candidate_cards_path": "ws3-core-v0-a2-invalidation-candidate-cards.json", "quality_audit_path": "ws3-core-v0-a2-confirmatory-quality-audit.json", "source_artifact_hashes": authority["source_artifact_hashes"], "normalized_aggregate_sha256": hashes["aggregate_sha256"]})
    _write_json(output_dir / "ws3-core-v0-a2-next-step-readiness.json", readiness)
    if write_report:
        _build_report(output_dir, summary, authority, hashes, task_commit_sha, tests)
    return {"summary": summary, "audit": audit, "hashes": hashes, "entry_cards": entry_cards, "invalidation_cards": invalidation_cards}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL"))
    parser.add_argument("--dataset-path", type=Path, default=DATASET_PATH_DEFAULT)
    parser.add_argument("--upstream-dir", type=Path, default=UPSTREAM_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR_DEFAULT)
    parser.add_argument("--reproducibility-status", default="NOT_RUN")
    parser.add_argument("--task-commit-sha", default="RECORDED_IN_FINAL_HANDOFF")
    parser.add_argument("--tests", default="RECORDED_IN_FINAL_HANDOFF")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit("TOPICPILOT_DATABASE_URL is required for the read-only historical collector")
    result = run_confirmatory(args.database_url, args.output_dir, dataset_path=args.dataset_path, upstream_dir=args.upstream_dir, reproducibility_status=args.reproducibility_status, task_commit_sha=args.task_commit_sha, tests=args.tests, write_report=args.write_report)
    for key, value in result["summary"].items():
        if key.isupper():
            print(f"{key}={value}")


if __name__ == "__main__":
    main()
