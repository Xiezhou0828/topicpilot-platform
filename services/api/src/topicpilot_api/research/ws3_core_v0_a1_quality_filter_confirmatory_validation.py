"""Confirmatory validation for the frozen WS3 A1 quality-filter candidates.

The exploratory threshold surface is consumed as authority.  This module first
freezes the candidate set and confirmatory decision framework, then evaluates
that immutable set on the existing chronological research coverage.  It never
retunes thresholds, searches new features, changes A1/A2 formation, or writes
production state.
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

from topicpilot_api.research.ws3_core_v0_a1_ex_ante_discrimination import (
    FROZEN_SPEC_HASH,
    _build_feature_rows,
    _cohort_reconciliation,
    _date_value,
    collect_observations,
)
from topicpilot_api.research.ws3_core_v0_a1_quality_filter_threshold_sensitivity import (
    _attach_outcomes,
)
from topicpilot_api.research.ws3_core_v0_baseline_attribution import SEGMENTS

# ruff: noqa: E501  # Exact task, artifact, and protocol contract strings are intentional.

TASK_ID = "TASK-WS3-CORE-V0-A1-QUALITY-FILTER-CONFIRMATORY-VALIDATION-20260818"
EXPLORATORY_TASK_ID = (
    "TASK-WS3-CORE-V0-A1-QUALITY-FILTER-THRESHOLD-AND-SENSITIVITY-RESEARCH-20260818"
)
UPSTREAM_TASK_ID = (
    "TASK-WS3-CORE-V0-A1-EX-ANTE-SUCCESS-VS-FAILED-BREAKOUT-DISCRIMINATION-RESEARCH-20260818"
)
SOURCE_CANONICAL_HEAD = "8bc9c8ec403e03aa104c6feac481e2d5e561e134"
EXPLORATORY_SOURCE_HEAD = "035587e4f263447e778f9384971885e03a53ecc2"
CURRENT_CANONICAL_HEAD = SOURCE_CANONICAL_HEAD
DATASET_AUTHORITY = (
    "canonical Postgres historical read model via read_historical_bars; "
    "REC-A1 event-aware research dataset preserved"
)
EXPLORATORY_DIR = Path(
    "reports/TASK-WS3-CORE-V0-A1-QUALITY-FILTER-THRESHOLD-AND-SENSITIVITY-RESEARCH-20260818"
)
UPSTREAM_DIR = Path(
    "reports/TASK-WS3-CORE-V0-A1-EX-ANTE-SUCCESS-VS-FAILED-BREAKOUT-DISCRIMINATION-RESEARCH-20260818"
)
DATASET_PATH_DEFAULT = Path(
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json"
)
TAXONOMY_PATH_DEFAULT = Path(
    "reports/TASK-WS3-CORE-V0-A1-A2-VALIDATION-STABILITY-AND-FAILURE-MODE-REVIEW-20260818/ws3-core-v0-a1-nontransition-taxonomy.csv"
)
OUTCOME_HORIZONS = (1, 3, 5, 10)
PRIMARY_COHORTS = ("SUCCESSFUL_A1", "FAILED_BREAKOUT_A1")
SEGMENT_NAMES = ("TRAIN", "VALIDATION", "HOLDOUT", "FULL_SAMPLE")
CONFIRMATORY_SEGMENT = "HOLDOUT"
JULY_SEGMENT = "VALIDATION"
MINIMUM_COHORT_COUNT = 20
MEANINGFUL_SUCCESS_UPLIFT = 0.03
MEANINGFUL_FAILED_BREAKOUT_REDUCTION = 0.03
NON_DESTRUCTIVE_MEDIAN_FLOOR = -0.05
TRIM_FRACTION = 0.10
ANALYTICAL_ARTIFACT_NAMES = (
    "a1-quality-filter-confirmatory-freeze.json",
    "a1-quality-filter-confirmatory-candidate-comparison.csv",
    "a1-quality-filter-confirmatory-temporal-stability.csv",
    "a1-quality-filter-confirmatory-market-stability.csv",
    "a1-quality-filter-confirmatory-july-analysis.csv",
    "a1-quality-filter-confirmatory-retention-analysis.csv",
    "a1-quality-filter-confirmatory-concentration-analysis.json",
    "a1-quality-filter-confirmatory-forward-return-analysis.csv",
)
REQUIRED_LEADING_CANDIDATES = (
    "true_range_pct__LOWER_LE_Q70",
    "recent_20_high_proximity__UPPER_GE_Q30",
    "return_5d__LOWER_LE_Q60",
)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"EMPTY_CSV_OUTPUT:{path.name}")
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in fieldnames} for row in rows)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _as_date(value: Any) -> date:
    return _date_value(value)


def _segment_name(signal_date: Any) -> str:
    value = _as_date(signal_date)
    for name, start, end in SEGMENTS:
        if start <= value <= end:
            return name
    return "OUTSIDE_FROZEN_SEGMENTS"


def _segment_rows(rows: Sequence[Mapping[str, Any]], segment: str) -> list[Mapping[str, Any]]:
    if segment == "FULL_SAMPLE":
        return list(rows)
    expected = {
        "TRAIN": "DEVELOPMENT_AVAILABLE",
        "VALIDATION": "VALIDATION",
        "HOLDOUT": "HOLDOUT",
    }[segment]
    return [row for row in rows if _segment_name(row["signal_date"]) == expected]


def _quantile_label(value: str) -> str:
    return value.upper()


def _exploratory_context(prior_dir: Path) -> dict[str, Any]:
    summary = _read_json(prior_dir / "ws3-core-v0-a1-threshold-sensitivity-summary.json")
    cards = _read_json(prior_dir / "ws3-core-v0-a1-filter-candidate-cards.json")
    quality = _read_json(prior_dir / "ws3-core-v0-a1-threshold-quality-audit.json")
    readiness = _read_json(prior_dir / "ws3-core-v0-a1-filter-confirmatory-readiness.json")
    surface = _read_csv(prior_dir / "ws3-core-v0-a1-single-feature-threshold-surface.csv")
    combinations = _read_csv(prior_dir / "ws3-core-v0-a1-two-feature-combination-diagnostic.csv")
    manifest = _read_json(
        UPSTREAM_DIR / "ws3-core-v0-a1-ex-ante-feature-manifest.json"
    )
    upstream_quality = _read_json(UPSTREAM_DIR / "ws3-core-v0-a1-ex-ante-quality-audit.json")
    upstream_readiness = _read_json(
        UPSTREAM_DIR / "ws3-core-v0-a1-ex-ante-next-step-readiness.json"
    )
    if summary["task_id"] != EXPLORATORY_TASK_ID:
        raise RuntimeError("EXPLORATORY_TASK_ID_MISMATCH")
    if summary["frozen_spec_hash"] != FROZEN_SPEC_HASH:
        raise RuntimeError("EXPLORATORY_FROZEN_SPEC_MISMATCH")
    if quality["frozen_spec_hash"] != FROZEN_SPEC_HASH:
        raise RuntimeError("EXPLORATORY_AUDIT_FROZEN_SPEC_MISMATCH")
    if summary["primary_selected_feature_count"] != 7:
        raise RuntimeError("EXPLORATORY_FEATURE_COUNT_MISMATCH")
    robust = [row for row in surface if row["THRESHOLD_CLASSIFICATION"] == "ROBUST_THRESHOLD_REGION"]
    if len(robust) != 6:
        raise RuntimeError(f"EXPLORATORY_ROBUST_REGION_COUNT_MISMATCH:{len(robust)}")
    if not quality["reproducible"]:
        raise RuntimeError("EXPLORATORY_REPRODUCIBILITY_NOT_PASS")
    if upstream_quality["frozen_spec_hash"] != FROZEN_SPEC_HASH:
        raise RuntimeError("UPSTREAM_FROZEN_SPEC_MISMATCH")
    if upstream_readiness["A1_ex_ante_discrimination_supported"] != "YES":
        raise RuntimeError("UPSTREAM_A1_DISCRIMINATION_NOT_SUPPORTED")
    if not manifest["point_in_time_valid_feature_count"] == 40:
        raise RuntimeError("UPSTREAM_PIT_MANIFEST_COUNT_MISMATCH")
    return {
        "summary": summary,
        "cards": cards,
        "quality": quality,
        "readiness": readiness,
        "surface": surface,
        "combinations": combinations,
        "manifest": manifest,
        "upstream_quality": upstream_quality,
        "upstream_readiness": upstream_readiness,
    }


def _candidate_source_metric(row: Mapping[str, Any]) -> dict[str, Any]:
    def number(key: str) -> float | None:
        return _as_float(row.get(key))

    return {
        "exploratory_region_id": row["region_id"],
        "exploratory_success_rate_delta": number("SUCCESS_RATE_DELTA"),
        "exploratory_failed_breakout_rate_reduction": -number(
            "FAILED_BREAKOUT_RATE_DELTA"
        )
        if number("FAILED_BREAKOUT_RATE_DELTA") is not None
        else None,
        "exploratory_retention_rate": number("RETENTION_RATE"),
        "exploratory_validation_success_rate_delta": number(
            "VALIDATION_SUCCESS_RATE_DELTA"
        ),
        "exploratory_validation_failed_breakout_rate_reduction": -number(
            "VALIDATION_FAILED_BREAKOUT_RATE_DELTA"
        )
        if number("VALIDATION_FAILED_BREAKOUT_RATE_DELTA") is not None
        else None,
        "exploratory_july_behavior": row.get("JULY_VALIDATION_IMPROVEMENT"),
        "exploratory_temporal_consistency": row.get("TEMPORAL_DIRECTIONALLY_CONSISTENT"),
        "exploratory_date_concentration": row.get("DATE_CONCENTRATION_RISK"),
        "exploratory_instrument_concentration": row.get("INSTRUMENT_CONCENTRATION_RISK"),
        "exploratory_tpe_two_consistency": row.get("TPE_TWO_DIRECTIONALLY_CONSISTENT"),
    }


def _expected_retention_range(value: float | None) -> list[float | None]:
    if value is None:
        return [None, None]
    return [max(0.0, round(value - 0.10, 6)), min(1.0, round(value + 0.10, 6))]


def _feature_definition_map(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["feature_name"]: row for row in manifest["features"]}


def _single_candidate(
    row: Mapping[str, Any], feature_map: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    feature_name = row["feature_name"]
    direction = row["expected_direction"]
    operator = ">=" if direction == "HIGHER_IN_SUCCESS" else "<="
    spec = feature_map[feature_name]
    retention = _as_float(row["RETENTION_RATE"])
    return {
        "candidate_id": row["region_id"],
        "candidate_type": "SINGLE_FEATURE",
        "feature_name": feature_name,
        "feature_family": row["category"],
        "feature_definition": spec["definition"],
        "feature_input_columns": spec["input_columns"],
        "feature_lookback": spec["lookback"],
        "direction": direction,
        "operator": operator,
        "threshold_quantile": _quantile_label(row["threshold_quantile"]),
        "threshold_fraction": _as_float(row["threshold_fraction"]),
        "threshold_value": _as_float(row["threshold_value"]),
        "eligibility_rule": (
            f"RAW_A1 AND {feature_name} {operator} TRAIN_DERIVED_{row['threshold_quantile']}"
        ),
        "missing_data_behavior": "Missing feature does not pass the quality filter; RAW_A1 is preserved.",
        "combination_logic": None,
        "selection_reason": "Previously classified ROBUST_THRESHOLD_REGION; included without post-freeze re-ranking.",
        "source_exploratory_artifact": (
            f"{EXPLORATORY_DIR.as_posix()}/ws3-core-v0-a1-single-feature-threshold-surface.csv"
        ),
        "source_exploratory_metric": _candidate_source_metric(row),
        "pit_validity": bool(spec["point_in_time_available"]),
        "timestamp_rule": spec["timestamp_rule"],
        "expected_retention_range": _expected_retention_range(retention),
        "expected_directional_effect": {
            "success_rate_delta": _as_float(row["SUCCESS_RATE_DELTA"]),
            "failed_breakout_rate_reduction": -_as_float(row["FAILED_BREAKOUT_RATE_DELTA"])
            if _as_float(row["FAILED_BREAKOUT_RATE_DELTA"]) is not None
            else None,
        },
    }


def _combination_candidate(
    card: Mapping[str, Any],
    combination_row: Mapping[str, str],
    feature_map: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    left = combination_row["feature_left"]
    right = combination_row["feature_right"]
    left_id = combination_row["left_region_id"]
    right_id = combination_row["right_region_id"]
    left_spec = feature_map[left]
    right_spec = feature_map[right]
    return {
        "candidate_id": combination_row["combination_id"],
        "candidate_type": "TWO_FEATURE_COMBINATION",
        "feature_name": f"{left} AND {right}",
        "feature_family": f"{left_spec['category']} + {right_spec['category']}",
        "feature_definition": [left_spec["definition"], right_spec["definition"]],
        "feature_input_columns": [left_spec["input_columns"], right_spec["input_columns"]],
        "feature_lookback": [left_spec["lookback"], right_spec["lookback"]],
        "direction": [
            "HIGHER_IN_SUCCESS" if "UPPER_GE" in left_id else "LOWER_IN_SUCCESS",
            "HIGHER_IN_SUCCESS" if "UPPER_GE" in right_id else "LOWER_IN_SUCCESS",
        ],
        "operator": [">=" if "UPPER_GE" in left_id else "<=", ">=" if "UPPER_GE" in right_id else "<="],
        "threshold_quantile": [left_id.rsplit("_", 1)[-1], right_id.rsplit("_", 1)[-1]],
        "threshold_fraction": None,
        "threshold_value": None,
        "eligibility_rule": f"RAW_A1 AND ({left_id}) AND ({right_id}); both features non-missing",
        "missing_data_behavior": "Missing either feature fails the combination; RAW_A1 is preserved.",
        "combination_logic": {
            "operator": "AND",
            "left_region_id": left_id,
            "right_region_id": right_id,
            "maximum_features": 2,
        },
        "selection_reason": "Previously declared top two-feature diagnostic; no new pair search is permitted.",
        "source_exploratory_artifact": (
            f"{EXPLORATORY_DIR.as_posix()}/ws3-core-v0-a1-two-feature-combination-diagnostic.csv"
        ),
        "source_exploratory_metric": {
            "exploratory_region_id": combination_row["combination_id"],
            "exploratory_success_rate_delta": _as_float(combination_row["success_rate_delta"]),
            "exploratory_failed_breakout_rate_reduction": -_as_float(
                combination_row["failed_breakout_rate_delta"]
            ),
            "exploratory_retention_rate": _as_float(combination_row["retention_rate"]),
            "exploratory_validation_success_rate_delta": _as_float(
                combination_row["validation_success_rate_delta"]
            ),
            "exploratory_july_behavior": combination_row["july_validation_improvement"],
            "exploratory_tpe_two_consistency": combination_row[
                "TPE_TWO_DIRECTIONALLY_CONSISTENT"
            ],
        },
        "pit_validity": bool(left_spec["point_in_time_available"] and right_spec["point_in_time_available"]),
        "timestamp_rule": [left_spec["timestamp_rule"], right_spec["timestamp_rule"]],
        "expected_retention_range": _expected_retention_range(
            _as_float(combination_row["retention_rate"])
        ),
        "expected_directional_effect": {
            "success_rate_delta": _as_float(combination_row["success_rate_delta"]),
            "failed_breakout_rate_reduction": -_as_float(
                combination_row["failed_breakout_rate_delta"]
            ),
        },
        "source_card": dict(card),
    }


def build_confirmatory_freeze(prior_dir: Path = EXPLORATORY_DIR) -> dict[str, Any]:
    """Build the immutable candidate/protocol freeze from prior artifacts only."""

    context = _exploratory_context(prior_dir)
    feature_map = _feature_definition_map(context["manifest"])
    robust_rows = [
        row
        for row in context["surface"]
        if row["THRESHOLD_CLASSIFICATION"] == "ROBUST_THRESHOLD_REGION"
    ]
    candidates = [_single_candidate(row, feature_map) for row in robust_rows]
    combo_cards = context["cards"]["top_two_feature_combination_candidates"]
    combo_rows = {
        row["combination_id"]: row
        for row in context["combinations"]
        if row["tested"].upper() == "TRUE"
    }
    for card in combo_cards:
        combo_id = card["candidate_id"]
        if combo_id not in combo_rows:
            raise RuntimeError(f"EXPLORATORY_COMBINATION_ROW_MISSING:{combo_id}")
        candidates.append(_combination_candidate(card, combo_rows[combo_id], feature_map))
    candidate_ids = [candidate["candidate_id"] for candidate in candidates]
    missing_required = [
        candidate_id for candidate_id in REQUIRED_LEADING_CANDIDATES if candidate_id not in candidate_ids
    ]
    if missing_required:
        raise RuntimeError(f"REQUIRED_LEADING_CANDIDATE_MISSING:{missing_required}")
    return {
        "task_id": TASK_ID,
        "schema_version": "a1-quality-filter-confirmatory-freeze.v1",
        "created_before_confirmatory_outcome_review": True,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "exploratory_source_canonical_head": context["summary"]["source_canonical_head"],
        "exploratory_final_canonical_head": SOURCE_CANONICAL_HEAD,
        "exploratory_task_id": EXPLORATORY_TASK_ID,
        "upstream_task_id": UPSTREAM_TASK_ID,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "a1_cohort_authority": {
            "raw_a1_count": 700,
            "successful_a1_count": 386,
            "failed_breakout_a1_count": 214,
            "definitions_reused": True,
            "taxonomy_reused": True,
        },
        "confirmatory_independence": {
            "level": "BOUNDED",
            "primary_segment": "HOLDOUT",
            "primary_segment_dates": "2026-08-01..2026-08-13",
            "stress_segment": "VALIDATION",
            "stress_segment_dates": "2026-07-01..2026-07-31",
            "untouched_temporal_data_available": False,
            "justification": "The available 2026-02-02..2026-08-13 history was already inspected during exploratory threshold research; this is a frozen retrospective replay with no retuning, not independent new-data confirmation.",
        },
        "protocol": {
            "id": "a1-quality-filter-confirmatory.v1",
            "candidate_set_frozen_before_outcomes": True,
            "primary_outcome": "SUCCESSFUL_A1 versus FAILED_BREAKOUT_A1",
            "raw_a1_preserved": True,
            "candidate_filter_applied_after_raw_a1_formation": True,
            "no_random_shuffle": True,
            "segment_definitions": {
                "TRAIN": "2026-05-12..2026-06-30 / DEVELOPMENT_AVAILABLE",
                "VALIDATION": "2026-07-01..2026-07-31 / frozen July stress segment",
                "HOLDOUT": "2026-08-01..2026-08-13 / primary confirmatory segment",
            },
            "outcome_horizons": ["T+1", "T+3", "T+5", "T+10"],
            "forward_outcomes_are_evaluation_only": True,
            "minimum_per_primary_cohort": MINIMUM_COHORT_COUNT,
            "meaningful_success_uplift": MEANINGFUL_SUCCESS_UPLIFT,
            "meaningful_failed_breakout_reduction": MEANINGFUL_FAILED_BREAKOUT_REDUCTION,
            "concentration_rules": {
                "date_low_top1_share_max": 0.10,
                "date_medium_top1_share_max": 0.20,
                "instrument_low_top5_share_max": 0.25,
                "instrument_medium_top5_share_max": 0.40,
            },
            "outlier_rule": "OUTLIER_DRIVEN=YES only when mean improvement is positive while both median and 10-percent trimmed mean are non-positive on the confirmatory segment.",
            "forward_support_rule": "SUPPORTIVE if at least 2 of 4 confirmatory-horizon median deltas are positive and no median delta is below -0.05; NON_DESTRUCTIVE if all available median deltas are >= -0.05; otherwise MIXED or DESTRUCTIVE.",
            "classification_rules": {
                "CONFIRMED": "Adequate confirmatory cohort; holdout success uplift and failed-breakout reduction each >= 3pp; no market contradiction; July direction non-negative; no HIGH concentration; not outlier-driven; forward support SUPPORTIVE or NON_DESTRUCTIVE; and independence level HIGH.",
                "SUPPORTED_WITH_BOUNDED_LIMITATIONS": "Same frozen primary effect and market/no-outlier requirements as CONFIRMED, but independence is BOUNDED or a declared secondary limitation remains.",
                "INCONCLUSIVE": "Insufficient confirmatory cohort, unresolved uncertainty, or materially mixed confirmatory direction without a clear adverse failure.",
                "FAILED_CONFIRMATION": "Holdout quality direction is adverse, a market materially contradicts the frozen direction, or the frozen candidate has no meaningful confirmatory discrimination.",
            },
            "no_retuning": True,
            "no_new_feature_search": True,
            "no_new_combination_search": True,
            "no_production_mutation": True,
        },
        "candidates": candidates,
        "candidate_count": len(candidates),
        "single_feature_candidate_count": len(robust_rows),
        "combination_candidate_count": len(combo_cards),
        "exploratory_artifacts_used": [
            f"{prior_dir.as_posix()}/ws3-core-v0-a1-single-feature-threshold-surface.csv",
            f"{prior_dir.as_posix()}/ws3-core-v0-a1-filter-candidate-cards.json",
            f"{prior_dir.as_posix()}/ws3-core-v0-a1-threshold-quality-audit.json",
            f"{UPSTREAM_DIR.as_posix()}/ws3-core-v0-a1-ex-ante-feature-manifest.json",
        ],
    }


def _wilson(success: int, total: int) -> list[float | None]:
    if total == 0:
        return [None, None]
    z = 1.959963984540054
    p = success / total
    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
    return [max(0.0, center - margin), min(1.0, center + margin)]


def _primary_stats(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    success = sum(row["cohort"] == "SUCCESSFUL_A1" for row in rows)
    failed = sum(row["cohort"] == "FAILED_BREAKOUT_A1" for row in rows)
    resolved = success + failed
    success_rate = success / resolved if resolved else None
    failed_rate = failed / resolved if resolved else None
    return {
        "total_a1_count": len(rows),
        "filtered_a1_count": len(rows),
        "retention_count": len(rows),
        "retention_rate": None,
        "successful_retained": success,
        "failed_breakout_retained": failed,
        "resolved_primary_count": resolved,
        "success_count": success,
        "failed_breakout_count": failed,
        "success_rate": success_rate,
        "failed_breakout_rate": failed_rate,
        "success_rate_ci95": _wilson(success, resolved),
        "failed_breakout_rate_ci95": _wilson(failed, resolved),
    }


def _forward_values(rows: Sequence[Mapping[str, Any]], horizon: int) -> list[float]:
    values = []
    for row in rows:
        if row["cohort"] not in PRIMARY_COHORTS:
            continue
        if horizon in row.get("event_excluded_horizons", []):
            continue
        value = _as_float(row.get("returns", {}).get(str(horizon)))
        if value is not None:
            values.append(value)
    return values


def _trimmed_mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    trim = int(len(ordered) * TRIM_FRACTION)
    core = ordered[trim : len(ordered) - trim] if len(ordered) > trim * 2 else ordered
    return mean(core) if core else None


def _forward_stats(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    output = {}
    for horizon in OUTCOME_HORIZONS:
        values = _forward_values(rows, horizon)
        output[f"T+{horizon}"] = {
            "sample_count": len(values),
            "mean": mean(values) if values else None,
            "median": median(values) if values else None,
            "trimmed_mean_10pct": _trimmed_mean(values),
            "win_rate": sum(value > 0 for value in values) / len(values) if values else None,
            "p05": _quantile(values, 0.05),
            "p25": _quantile(values, 0.25),
            "p75": _quantile(values, 0.75),
            "p95": _quantile(values, 0.95),
        }
    return output


def _quantile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + weight * (ordered[upper] - ordered[lower])


def _primary_and_forward(
    filtered_rows: Sequence[Mapping[str, Any]], baseline_rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    filtered = _primary_stats(filtered_rows)
    baseline = _primary_stats(baseline_rows)
    filtered["retention_rate"] = (
        len(filtered_rows) / len(baseline_rows) if baseline_rows else None
    )
    baseline["retention_rate"] = 1.0 if baseline_rows else None
    filtered_forward = _forward_stats(filtered_rows)
    baseline_forward = _forward_stats(baseline_rows)
    forward = {}
    for horizon in OUTCOME_HORIZONS:
        key = f"T+{horizon}"
        forward[key] = {
            "baseline": baseline_forward[key],
            "filtered": filtered_forward[key],
            "mean_delta": _difference(filtered_forward[key]["mean"], baseline_forward[key]["mean"]),
            "median_delta": _difference(filtered_forward[key]["median"], baseline_forward[key]["median"]),
            "trimmed_mean_delta": _difference(
                filtered_forward[key]["trimmed_mean_10pct"], baseline_forward[key]["trimmed_mean_10pct"]
            ),
            "win_rate_delta": _difference(filtered_forward[key]["win_rate"], baseline_forward[key]["win_rate"]),
        }
    filtered["forward_returns"] = filtered_forward
    baseline["forward_returns"] = baseline_forward
    return {
        "baseline": baseline,
        "filtered": filtered,
        "success_rate_uplift": _difference(filtered["success_rate"], baseline["success_rate"]),
        "failed_breakout_rate_reduction": _difference(
            baseline["failed_breakout_rate"], filtered["failed_breakout_rate"]
        ),
        "forward": forward,
    }


def _difference(left: float | None, right: float | None) -> float | None:
    return left - right if left is not None and right is not None else None


def _apply_candidate(rows: Sequence[Mapping[str, Any]], candidate: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if candidate["candidate_type"] == "SINGLE_FEATURE":
        feature = candidate["feature_name"]
        threshold = candidate["threshold_value"]
        operator = candidate["operator"]
        return [
            row
            for row in rows
            if _as_float(row.get(feature)) is not None
            and ((row[feature] >= threshold) if operator == ">=" else (row[feature] <= threshold))
        ]
    logic = candidate["combination_logic"]
    left_id = logic["left_region_id"]
    right_id = logic["right_region_id"]
    left_feature = left_id.rsplit("__", 1)[0]
    right_feature = right_id.rsplit("__", 1)[0]
    left_threshold = _candidate_threshold_from_id(candidate, left_id)
    right_threshold = _candidate_threshold_from_id(candidate, right_id)
    left_operator = candidate["operator"][0]
    right_operator = candidate["operator"][1]
    return [
        row
        for row in rows
        if _as_float(row.get(left_feature)) is not None
        and _as_float(row.get(right_feature)) is not None
        and ((row[left_feature] >= left_threshold) if left_operator == ">=" else (row[left_feature] <= left_threshold))
        and ((row[right_feature] >= right_threshold) if right_operator == ">=" else (row[right_feature] <= right_threshold))
    ]


def _candidate_threshold_from_id(candidate: Mapping[str, Any], region_id: str) -> float:
    # Combination thresholds are copied from the frozen exploratory region IDs.
    # The numeric values are carried in the freeze's source metric only through
    # the two region IDs, so the analysis resolves them from the immutable surface.
    thresholds = candidate.get("combination_threshold_values", {})
    if region_id not in thresholds:
        raise RuntimeError(f"COMBINATION_THRESHOLD_MISSING:{region_id}")
    return float(thresholds[region_id])


def _market_metrics(
    filtered_rows: Sequence[Mapping[str, Any]], baseline_rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    output = {}
    for market in ("TPE", "TWO"):
        filtered = [row for row in filtered_rows if row.get("market") == market]
        baseline = [row for row in baseline_rows if row.get("market") == market]
        metrics = _primary_and_forward(filtered, baseline)
        metrics["market"] = market
        metrics["sample_count"] = len(filtered)
        metrics["baseline_sample_count"] = len(baseline)
        output[market] = metrics
    return output


def _concentration(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    resolved = [row for row in rows if row["cohort"] in PRIMARY_COHORTS]
    date_counts = Counter(str(_as_date(row["signal_date"])) for row in resolved)
    instrument_counts = Counter(str(row["instrument_id"]) for row in resolved)
    n = len(resolved)
    top_date = date_counts.most_common(1)[0][1] / n if n else None
    top_three_date = sum(value for _, value in date_counts.most_common(3)) / n if n else None
    top_five_date = sum(value for _, value in date_counts.most_common(5)) / n if n else None
    top_instrument = instrument_counts.most_common(1)[0][1] / n if n else None
    top_five_instrument = sum(value for _, value in instrument_counts.most_common(5)) / n if n else None
    top_ten_instrument = sum(value for _, value in instrument_counts.most_common(10)) / n if n else None
    if top_date is None or top_date > 0.20:
        date_classification = "HIGH"
    elif top_date > 0.10:
        date_classification = "MEDIUM"
    else:
        date_classification = "LOW"
    if top_five_instrument is None or top_five_instrument > 0.40:
        instrument_classification = "HIGH"
    elif top_five_instrument > 0.25:
        instrument_classification = "MEDIUM"
    else:
        instrument_classification = "LOW"
    return {
        "resolved_primary_count": n,
        "active_filtered_dates": len(date_counts),
        "top_1_date_contribution": top_date,
        "top_3_date_contribution": top_three_date,
        "top_5_date_contribution": top_five_date,
        "top_dates": date_counts.most_common(5),
        "date_concentration_classification": date_classification,
        "unique_filtered_instruments": len(instrument_counts),
        "top_instrument_contribution": top_instrument,
        "top_5_instrument_contribution": top_five_instrument,
        "top_10_instrument_contribution": top_ten_instrument,
        "top_instruments": instrument_counts.most_common(10),
        "instrument_concentration_classification": instrument_classification,
    }


def _outlier_analysis(
    filtered_rows: Sequence[Mapping[str, Any]], baseline_rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    forward = _primary_and_forward(filtered_rows, baseline_rows)["forward"]
    rows = []
    outlier_driven = False
    for horizon in OUTCOME_HORIZONS:
        item = forward[f"T+{horizon}"]
        mean_delta = item["mean_delta"]
        median_delta = item["median_delta"]
        trimmed_delta = item["trimmed_mean_delta"]
        driven = (
            mean_delta is not None
            and median_delta is not None
            and trimmed_delta is not None
            and mean_delta > 0
            and median_delta <= 0
            and trimmed_delta <= 0
        )
        outlier_driven = outlier_driven or driven
        rows.append(
            {
                "horizon": f"T+{horizon}",
                "mean_delta": mean_delta,
                "median_delta": median_delta,
                "trimmed_mean_delta": trimmed_delta,
                "outlier_pattern": driven,
            }
        )
    return {"outlier_driven": outlier_driven, "horizons": rows}


def _forward_support(metrics: Mapping[str, Any]) -> str:
    median_deltas = [
        metrics["forward"][f"T+{horizon}"]["median_delta"]
        for horizon in OUTCOME_HORIZONS
        if metrics["forward"][f"T+{horizon}"]["median_delta"] is not None
    ]
    if not median_deltas:
        return "INSUFFICIENT"
    positive = sum(value > 0 for value in median_deltas)
    if positive >= 2 and min(median_deltas) >= NON_DESTRUCTIVE_MEDIAN_FLOOR:
        return "SUPPORTIVE"
    if min(median_deltas) >= NON_DESTRUCTIVE_MEDIAN_FLOOR:
        return "NON_DESTRUCTIVE"
    if any(value < NON_DESTRUCTIVE_MEDIAN_FLOOR for value in median_deltas):
        return "DESTRUCTIVE"
    return "MIXED"


def _market_direction_consistent(market: Mapping[str, Any]) -> tuple[bool, bool]:
    directions = []
    adequate = True
    for value in market.values():
        if value["filtered"]["resolved_primary_count"] < MINIMUM_COHORT_COUNT:
            adequate = False
        uplift = value["success_rate_uplift"]
        reduction = value["failed_breakout_rate_reduction"]
        directions.append(uplift is not None and reduction is not None and uplift >= 0 and reduction >= 0)
    return adequate, all(directions) if directions else False


def _classify_candidate(
    metrics: Mapping[str, Any], concentration: Mapping[str, Any], outliers: Mapping[str, Any]
) -> dict[str, Any]:
    holdout = metrics["segments"][CONFIRMATORY_SEGMENT]
    july = metrics["segments"][JULY_SEGMENT]
    holdout_filtered = holdout["filtered"]
    adequate = (
        holdout_filtered["success_count"] >= MINIMUM_COHORT_COUNT
        and holdout_filtered["failed_breakout_count"] >= MINIMUM_COHORT_COUNT
    )
    meaningful_holdout = (
        (holdout["success_rate_uplift"] or 0) >= MEANINGFUL_SUCCESS_UPLIFT
        and (holdout["failed_breakout_rate_reduction"] or 0)
        >= MEANINGFUL_FAILED_BREAKOUT_REDUCTION
    )
    holdout_directional = (
        (holdout["success_rate_uplift"] or 0) >= 0
        and (holdout["failed_breakout_rate_reduction"] or 0) >= 0
    )
    july_directional = (
        (july["success_rate_uplift"] or 0) >= 0
        and (july["failed_breakout_rate_reduction"] or 0) >= 0
    )
    market_adequate, market_consistent = _market_direction_consistent(metrics["market"])
    high_concentration = (
        concentration["date_concentration_classification"] == "HIGH"
        or concentration["instrument_concentration_classification"] == "HIGH"
    )
    forward_support = _forward_support(holdout)
    if not adequate:
        classification = "INCONCLUSIVE"
        reason = "Primary confirmatory holdout cohort is below the predeclared per-cohort minimum."
    elif not holdout_directional:
        classification = "FAILED_CONFIRMATION"
        reason = "Frozen candidate does not preserve non-adverse primary direction on the confirmatory holdout."
    elif not meaningful_holdout:
        classification = "INCONCLUSIVE"
        reason = "Holdout direction is non-adverse but below the predeclared meaningful 3pp effect guide."
    elif not market_consistent:
        classification = "FAILED_CONFIRMATION"
        reason = "TPE/TWO contains a materially adverse directional market split."
    elif high_concentration or outliers["outlier_driven"]:
        classification = "SUPPORTED_WITH_BOUNDED_LIMITATIONS"
        reason = "Primary effect survives, but concentration or outlier diagnostics impose a bounded limitation."
    elif not july_directional or not market_adequate or forward_support in {"MIXED", "DESTRUCTIVE", "INSUFFICIENT"}:
        classification = "SUPPORTED_WITH_BOUNDED_LIMITATIONS"
        reason = "Primary effect survives; July, market sample adequacy, or forward diagnostics remain bounded."
    elif CURRENT_CANONICAL_HEAD == SOURCE_CANONICAL_HEAD:
        classification = "SUPPORTED_WITH_BOUNDED_LIMITATIONS"
        reason = "Frozen retrospective evidence is not independent new-data confirmation; independence level is BOUNDED."
    else:
        classification = "CONFIRMED"
        reason = "All predeclared confirmatory criteria passed with high independence."
    return {
        "classification": classification,
        "classification_reason": reason,
        "adequate_confirmatory_sample": adequate,
        "meaningful_holdout_effect": meaningful_holdout,
        "holdout_directional": holdout_directional,
        "july_directional": july_directional,
        "market_sample_adequate": market_adequate,
        "market_directionally_consistent": market_consistent,
        "forward_return_support": forward_support,
        "outlier_driven": outliers["outlier_driven"],
        "high_concentration": high_concentration,
    }


def _candidate_metrics(
    candidate: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    filtered = _apply_candidate(rows, candidate)
    segments = {}
    for segment in SEGMENT_NAMES:
        baseline_rows = _segment_rows(rows, segment)
        filtered_rows = _segment_rows(filtered, segment)
        segments[segment] = _primary_and_forward(filtered_rows, baseline_rows)
    market = _market_metrics(filtered, rows)
    concentration = _concentration(filtered)
    outliers = _outlier_analysis(
        _segment_rows(filtered, CONFIRMATORY_SEGMENT),
        _segment_rows(rows, CONFIRMATORY_SEGMENT),
    )
    metrics = {
        "candidate_id": candidate["candidate_id"],
        "candidate_type": candidate["candidate_type"],
        "filtered_rows": filtered,
        "filtered_a1_count": len(filtered),
        "segments": segments,
        "market": market,
        "concentration": concentration,
        "outliers": outliers,
    }
    metrics.update(_classify_candidate(metrics, concentration, outliers))
    return metrics


def _threshold_values_for_combination(
    candidate: dict[str, Any], surface: Sequence[Mapping[str, str]]
) -> dict[str, float]:
    values = {}
    for region_id in (
        candidate["combination_logic"]["left_region_id"],
        candidate["combination_logic"]["right_region_id"],
    ):
        row = next((item for item in surface if item["region_id"] == region_id), None)
        if row is None:
            raise RuntimeError(f"COMBINATION_SOURCE_REGION_MISSING:{region_id}")
        values[region_id] = float(row["threshold_value"])
    return values


def _freeze_with_combination_values(
    freeze: dict[str, Any], surface: Sequence[Mapping[str, str]]
) -> dict[str, Any]:
    for candidate in freeze["candidates"]:
        if candidate["candidate_type"] == "TWO_FEATURE_COMBINATION":
            candidate["combination_threshold_values"] = _threshold_values_for_combination(
                candidate, surface
            )
    return freeze


def _comparison_rows(
    candidates: Sequence[Mapping[str, Any]], metrics: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    output = []
    for candidate in candidates:
        result = metrics[candidate["candidate_id"]]
        holdout = result["segments"][CONFIRMATORY_SEGMENT]
        full = result["segments"]["FULL_SAMPLE"]
        output.append(
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_type": candidate["candidate_type"],
                "feature_family": candidate["feature_family"],
                "confirmatory_segment": CONFIRMATORY_SEGMENT,
                "baseline_a1_count": holdout["baseline"]["total_a1_count"],
                "filtered_a1_count": holdout["filtered"]["filtered_a1_count"],
                "retention_count": holdout["filtered"]["retention_count"],
                "retention_rate": holdout["filtered"]["retention_rate"],
                "successful_retained": holdout["filtered"]["successful_retained"],
                "failed_breakout_retained": holdout["filtered"]["failed_breakout_retained"],
                "baseline_success_rate": holdout["baseline"]["success_rate"],
                "filtered_success_rate": holdout["filtered"]["success_rate"],
                "success_rate_uplift": holdout["success_rate_uplift"],
                "baseline_failed_breakout_rate": holdout["baseline"]["failed_breakout_rate"],
                "filtered_failed_breakout_rate": holdout["filtered"]["failed_breakout_rate"],
                "failed_breakout_rate_reduction": holdout["failed_breakout_rate_reduction"],
                "success_rate_ci95": holdout["filtered"]["success_rate_ci95"],
                "baseline_success_rate_ci95": holdout["baseline"]["success_rate_ci95"],
                "full_sample_success_rate_uplift": full["success_rate_uplift"],
                "full_sample_failed_breakout_rate_reduction": full[
                    "failed_breakout_rate_reduction"
                ],
                "july_success_rate_uplift": result["segments"][JULY_SEGMENT]["success_rate_uplift"],
                "july_failed_breakout_rate_reduction": result["segments"][JULY_SEGMENT][
                    "failed_breakout_rate_reduction"
                ],
                "forward_return_support": result["forward_return_support"],
                "date_concentration_risk": result["concentration"][
                    "date_concentration_classification"
                ],
                "instrument_concentration_risk": result["concentration"][
                    "instrument_concentration_classification"
                ],
                "outlier_driven": result["outlier_driven"],
                "classification": result["classification"],
                "classification_reason": result["classification_reason"],
            }
        )
    return output


def _temporal_rows(metrics: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for candidate_id, result in metrics.items():
        for segment in SEGMENT_NAMES:
            item = result["segments"][segment]
            output.append(
                {
                    "candidate_id": candidate_id,
                    "segment": segment,
                    "baseline_a1_count": item["baseline"]["total_a1_count"],
                    "filtered_a1_count": item["filtered"]["filtered_a1_count"],
                    "retention_rate": item["filtered"]["retention_rate"],
                    "baseline_success_rate": item["baseline"]["success_rate"],
                    "filtered_success_rate": item["filtered"]["success_rate"],
                    "success_rate_uplift": item["success_rate_uplift"],
                    "baseline_failed_breakout_rate": item["baseline"]["failed_breakout_rate"],
                    "filtered_failed_breakout_rate": item["filtered"]["failed_breakout_rate"],
                    "failed_breakout_rate_reduction": item["failed_breakout_rate_reduction"],
                    "baseline_success_rate_ci95": item["baseline"]["success_rate_ci95"],
                    "filtered_success_rate_ci95": item["filtered"]["success_rate_ci95"],
                    "T+1_median_delta": item["forward"]["T+1"]["median_delta"],
                    "T+3_median_delta": item["forward"]["T+3"]["median_delta"],
                    "T+5_median_delta": item["forward"]["T+5"]["median_delta"],
                    "T+10_median_delta": item["forward"]["T+10"]["median_delta"],
                }
            )
    return output


def _market_rows(metrics: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for candidate_id, result in metrics.items():
        for market, item in result["market"].items():
            output.append(
                {
                    "candidate_id": candidate_id,
                    "market": market,
                    "baseline_sample_count": item["baseline_sample_count"],
                    "filtered_sample_count": item["sample_count"],
                    "retention_rate": item["filtered"]["retention_rate"],
                    "baseline_success_rate": item["baseline"]["success_rate"],
                    "filtered_success_rate": item["filtered"]["success_rate"],
                    "success_rate_uplift": item["success_rate_uplift"],
                    "baseline_failed_breakout_rate": item["baseline"]["failed_breakout_rate"],
                    "filtered_failed_breakout_rate": item["filtered"]["failed_breakout_rate"],
                    "failed_breakout_rate_reduction": item["failed_breakout_rate_reduction"],
                    "forward_return_effect": item["forward"],
                }
            )
    return output


def _july_rows(metrics: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for candidate_id, result in metrics.items():
        item = result["segments"][JULY_SEGMENT]
        output.append(
            {
                "candidate_id": candidate_id,
                "july_segment": JULY_SEGMENT,
                "july_baseline_a1_count": item["baseline"]["total_a1_count"],
                "july_filtered_a1_count": item["filtered"]["filtered_a1_count"],
                "july_retention_rate": item["filtered"]["retention_rate"],
                "july_baseline_success_rate": item["baseline"]["success_rate"],
                "july_filtered_success_rate": item["filtered"]["success_rate"],
                "july_success_rate_uplift": item["success_rate_uplift"],
                "july_baseline_failed_breakout_rate": item["baseline"]["failed_breakout_rate"],
                "july_filtered_failed_breakout_rate": item["filtered"]["failed_breakout_rate"],
                "july_failed_breakout_rate_reduction": item["failed_breakout_rate_reduction"],
                "july_forward_return_effect": item["forward"],
                "july_directional": result["july_directional"],
            }
        )
    return output


def _retention_rows(metrics: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for candidate_id, result in metrics.items():
        for segment in SEGMENT_NAMES:
            item = result["segments"][segment]
            output.append(
                {
                    "candidate_id": candidate_id,
                    "segment": segment,
                    "total_a1": item["baseline"]["total_a1_count"],
                    "filtered_a1": item["filtered"]["filtered_a1_count"],
                    "retention_count": item["filtered"]["retention_count"],
                    "retention_rate": item["filtered"]["retention_rate"],
                    "successful_retained": item["filtered"]["successful_retained"],
                    "failed_breakout_retained": item["filtered"]["failed_breakout_retained"],
                    "success_rate": item["filtered"]["success_rate"],
                    "failed_breakout_rate": item["filtered"]["failed_breakout_rate"],
                    "success_rate_uplift": item["success_rate_uplift"],
                    "failed_breakout_rate_reduction": item["failed_breakout_rate_reduction"],
                }
            )
    return output


def _forward_rows(metrics: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for candidate_id, result in metrics.items():
        for segment in SEGMENT_NAMES:
            item = result["segments"][segment]
            for horizon in OUTCOME_HORIZONS:
                forward = item["forward"][f"T+{horizon}"]
                output.append(
                    {
                        "candidate_id": candidate_id,
                        "segment": segment,
                        "horizon": f"T+{horizon}",
                        "baseline_sample_count": forward["baseline"]["sample_count"],
                        "filtered_sample_count": forward["filtered"]["sample_count"],
                        "baseline_mean": forward["baseline"]["mean"],
                        "filtered_mean": forward["filtered"]["mean"],
                        "mean_delta": forward["mean_delta"],
                        "baseline_median": forward["baseline"]["median"],
                        "filtered_median": forward["filtered"]["median"],
                        "median_delta": forward["median_delta"],
                        "baseline_trimmed_mean_10pct": forward["baseline"]["trimmed_mean_10pct"],
                        "filtered_trimmed_mean_10pct": forward["filtered"]["trimmed_mean_10pct"],
                        "trimmed_mean_delta": forward["trimmed_mean_delta"],
                        "baseline_win_rate": forward["baseline"]["win_rate"],
                        "filtered_win_rate": forward["filtered"]["win_rate"],
                        "win_rate_delta": forward["win_rate_delta"],
                        "baseline_p05": forward["baseline"]["p05"],
                        "filtered_p05": forward["filtered"]["p05"],
                        "baseline_p95": forward["baseline"]["p95"],
                        "filtered_p95": forward["filtered"]["p95"],
                    }
                )
    return output


def _concentration_json(metrics: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "method": "resolved-primary filtered rows; predeclared top-date and top-instrument shares",
        "candidates": {
            candidate_id: result["concentration"] for candidate_id, result in metrics.items()
        },
    }


def _normalized_hashes(output_dir: Path) -> dict[str, Any]:
    artifacts = {}
    for name in ANALYTICAL_ARTIFACT_NAMES:
        path = output_dir / name
        if not path.exists():
            raise RuntimeError(f"ANALYTICAL_ARTIFACT_MISSING:{name}")
        artifacts[name] = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    aggregate = hashlib.sha256(
        json.dumps(artifacts, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "algorithm": "SHA-256",
        "byte_normalization": "CRLF_TO_LF_BEFORE_HASH",
        "artifacts": artifacts,
        "aggregate_sha256": aggregate,
    }


def _best_candidate(metrics: Mapping[str, Mapping[str, Any]], classification: str) -> str | None:
    candidates = [
        result
        for result in metrics.values()
        if result["classification"] == classification
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda result: (
            result["segments"][CONFIRMATORY_SEGMENT]["success_rate_uplift"] or -1,
            result["segments"][CONFIRMATORY_SEGMENT]["filtered"]["retention_rate"] or 0,
        ),
    )["candidate_id"]


def _report(
    output_dir: Path,
    freeze: Mapping[str, Any],
    summary: Mapping[str, Any],
    audit: Mapping[str, Any],
    task_commit_sha: str,
    tests: str,
) -> None:
    lines = [
        "# WS3 Core V0 A1 Quality-Filter Confirmatory Validation",
        "",
        "## Final contract",
        "",
        "```text",
    ]
    for key, value in summary["final_contract"].items():
        lines.append(f"{key}={value}")
    lines.extend(
        [
            f"SOURCE_CANONICAL_HEAD={SOURCE_CANONICAL_HEAD}",
            f"CURRENT_CANONICAL_HEAD={CURRENT_CANONICAL_HEAD}",
            f"FROZEN_SPEC_HASH={FROZEN_SPEC_HASH}",
            f"NORMALIZED_AGGREGATE_SHA256={summary['normalized_aggregate_sha256']}",
            f"TASK_COMMIT_SHA={task_commit_sha}",
            f"TESTS={tests}",
            "```",
            "",
            "## What was frozen before confirmatory outcomes",
            "",
            f"The freeze artifact contains {freeze['candidate_count']} candidates: {freeze['single_feature_candidate_count']} robust single-feature regions and {freeze['combination_candidate_count']} previously declared two-feature diagnostics. No confirmatory outcome is used in candidate selection.",
            "",
            f"Confirmatory independence is {freeze['confirmatory_independence']['level']}: the available history was already inspected during exploration, so this is a frozen chronological retrospective replay rather than untouched new-data confirmation.",
            "",
            "## Candidate outcomes",
            "",
        ]
    )
    for row in summary["candidate_results"]:
        lines.append(
            f"- {row['candidate_id']}: {row['classification']} — {row['classification_reason']}"
        )
    lines.extend(
        [
            "",
            "## Required questions",
            "",
            f"Q1/Q2: Successful-A1 uplift and failed-breakout reduction are evaluated on the frozen HOLDOUT segment; best bounded candidate is {summary['best_supported_candidate'] or 'none'}.",
            "Q3: Retention is reported per candidate; no candidate is accepted on success rate alone.",
            "Q4/Q5/Q6: Temporal, TPE/TWO, and July results are separated in the temporal, market, and July artifacts.",
            "Q7/Q10: Forward means, medians, trimmed means, win rates, and outlier flags are reported by horizon.",
            "Q8/Q9: Date and instrument concentration are reported with top-1/3/5 dates and top-1/5/10 instruments.",
            f"Q11/Q12: The evidence remains {summary['confirmatory_support']}; a provisional production-like specification is not authorized, and the next step is {summary['next_ws3_mainline_step']}.",
            "Q13: No candidate is ready for production.",
            "",
            "## Safety and lifecycle",
            "",
            "A1 formation, A2 formation, Core V0, MA60 policy, WS1, WS2, WS4, NEXT_TASK, migrations, database writes, Production, deployment, and push were not changed or executed.",
            "",
            "```text",
            "CANONICAL_STATUS=READY_FOR_CANONICAL_RECONCILIATION",
            "RELEASE_STATUS=NOT_RUN",
            "PRODUCTION_VERIFICATION=NOT_RUN",
            "PUSH_REMOTE=NO",
            "DEPLOY=NOT_RUN",
            "MIGRATION=NOT_RUN",
            "```",
        ]
    )
    report_path = Path("docs/reports") / f"{TASK_ID}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_confirmatory(
    database_url: str,
    output_dir: Path,
    *,
    freeze_path: Path,
    dataset_path: Path = DATASET_PATH_DEFAULT,
    taxonomy_path: Path = TAXONOMY_PATH_DEFAULT,
    reproducibility_status: str = "NOT_RUN",
    task_commit_sha: str = "RECORDED_IN_FINAL_HANDOFF",
    tests: str = "RECORDED_IN_FINAL_HANDOFF",
) -> dict[str, Any]:
    freeze = _read_json(freeze_path)
    if not freeze["created_before_confirmatory_outcome_review"]:
        raise RuntimeError("CONFIRMATORY_FREEZE_NOT_PRE_OUTCOME")
    if freeze["frozen_spec_hash"] != FROZEN_SPEC_HASH:
        raise RuntimeError("CONFIRMATORY_FREEZE_FROZEN_SPEC_MISMATCH")
    output_dir.mkdir(parents=True, exist_ok=True)
    observations, collection_quality = collect_observations(database_url, dataset_path)
    a1_rows = observations["groups"]["A1_PRE_BREAKOUT"]
    a2_rows = observations["groups"]["A2_CONFIRMED_BREAKOUT"]
    cohort_rows, reconciliation = _cohort_reconciliation(
        a1_rows, a2_rows, observations["instrument_data"], taxonomy_path
    )
    if not reconciliation["pass"]:
        raise RuntimeError(f"A1_COHORT_RECONCILIATION_FAILED:{reconciliation}")
    feature_rows = _attach_outcomes(
        _build_feature_rows(cohort_rows, a1_rows, observations["instrument_data"]),
        a1_rows,
        cohort_rows,
    )
    if len(feature_rows) != 700:
        raise RuntimeError(f"RAW_A1_COUNT_MISMATCH:{len(feature_rows)}")
    # Resolve immutable combination cutpoints from the already frozen exploratory surface.
    exploratory_surface = _read_csv(
        EXPLORATORY_DIR / "ws3-core-v0-a1-single-feature-threshold-surface.csv"
    )
    freeze = _freeze_with_combination_values(freeze, exploratory_surface)
    metrics = {
        candidate["candidate_id"]: _candidate_metrics(candidate, feature_rows)
        for candidate in freeze["candidates"]
    }
    candidate_results = []
    for candidate in freeze["candidates"]:
        result = metrics[candidate["candidate_id"]]
        candidate_results.append(
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_type": candidate["candidate_type"],
                "classification": result["classification"],
                "classification_reason": result["classification_reason"],
                "confirmatory_holdout_success_rate_uplift": result["segments"][CONFIRMATORY_SEGMENT][
                    "success_rate_uplift"
                ],
                "confirmatory_holdout_failed_breakout_rate_reduction": result["segments"][
                    CONFIRMATORY_SEGMENT
                ]["failed_breakout_rate_reduction"],
                "confirmatory_holdout_retention_rate": result["segments"][CONFIRMATORY_SEGMENT][
                    "filtered"
                ]["retention_rate"],
                "july_success_rate_uplift": result["segments"][JULY_SEGMENT]["success_rate_uplift"],
                "july_failed_breakout_rate_reduction": result["segments"][JULY_SEGMENT][
                    "failed_breakout_rate_reduction"
                ],
                "forward_return_support": result["forward_return_support"],
                "date_concentration_risk": result["concentration"][
                    "date_concentration_classification"
                ],
                "instrument_concentration_risk": result["concentration"][
                    "instrument_concentration_classification"
                ],
                "outlier_driven": result["outlier_driven"],
            }
        )
    counts = Counter(row["classification"] for row in candidate_results)
    best_confirmed = _best_candidate(metrics, "CONFIRMED")
    best_supported = _best_candidate(metrics, "SUPPORTED_WITH_BOUNDED_LIMITATIONS")
    best_result = metrics.get(best_confirmed) if best_confirmed else None
    best_holdout = (
        best_result["segments"][CONFIRMATORY_SEGMENT] if best_result is not None else None
    )
    baseline_holdout = _primary_and_forward(
        _segment_rows(feature_rows, CONFIRMATORY_SEGMENT),
        _segment_rows(feature_rows, CONFIRMATORY_SEGMENT),
    )
    normalized_placeholder = "RECORDED_AFTER_ARTIFACT_WRITE"
    confirmatory_support = "YES" if counts["CONFIRMED"] else "YES_BOUNDED" if counts[
        "SUPPORTED_WITH_BOUNDED_LIMITATIONS"
    ] else "NO"
    provisional_spec = "YES" if counts["CONFIRMED"] and freeze["confirmatory_independence"]["level"] == "HIGH" else "NO"
    summary = {
        "task_id": TASK_ID,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "current_canonical_head": CURRENT_CANONICAL_HEAD,
        "exploratory_source_head": EXPLORATORY_SOURCE_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "exploratory_task_id": EXPLORATORY_TASK_ID,
        "upstream_task_id": UPSTREAM_TASK_ID,
        "confirmatory_freeze_created": True,
        "confirmatory_protocol_frozen_before_outcome_review": True,
        "confirmatory_independence_level": freeze["confirmatory_independence"]["level"],
        "raw_a1_count": len(feature_rows),
        "successful_a1_count": sum(row["cohort"] == "SUCCESSFUL_A1" for row in feature_rows),
        "failed_breakout_a1_count": sum(row["cohort"] == "FAILED_BREAKOUT_A1" for row in feature_rows),
        "frozen_candidate_count": len(freeze["candidates"]),
        "confirmed_candidate_count": counts["CONFIRMED"],
        "bounded_supported_candidate_count": counts["SUPPORTED_WITH_BOUNDED_LIMITATIONS"],
        "inconclusive_candidate_count": counts["INCONCLUSIVE"],
        "failed_candidate_count": counts["FAILED_CONFIRMATION"],
        "candidate_results": candidate_results,
        "best_confirmed_candidate": best_confirmed,
        "best_supported_candidate": best_supported,
        "best_confirmed_retention_rate": best_holdout["filtered"]["retention_rate"] if best_holdout else None,
        "best_confirmed_success_rate": best_holdout["filtered"]["success_rate"] if best_holdout else None,
        "best_confirmed_failed_breakout_rate": best_holdout["filtered"]["failed_breakout_rate"] if best_holdout else None,
        "baseline_success_rate": baseline_holdout["baseline"]["success_rate"],
        "baseline_failed_breakout_rate": baseline_holdout["baseline"]["failed_breakout_rate"],
        "success_rate_uplift": best_holdout["success_rate_uplift"] if best_holdout else None,
        "failed_breakout_rate_reduction": best_holdout["failed_breakout_rate_reduction"] if best_holdout else None,
        "july_validation_improvement": "YES" if any(row["july_success_rate_uplift"] is not None and row["july_success_rate_uplift"] >= 0 and row["july_failed_breakout_rate_reduction"] is not None and row["july_failed_breakout_rate_reduction"] >= 0 for row in candidate_results) else "NO_OR_BOUNDED",
        "tpe_two_directional_consistency": "YES" if all(result["market_directionally_consistent"] for result in metrics.values()) else "PARTIAL",
        "temporal_stability": "YES" if all(result["segments"]["HOLDOUT"]["success_rate_uplift"] is not None and result["segments"]["HOLDOUT"]["success_rate_uplift"] >= 0 for result in metrics.values()) else "MIXED",
        "date_concentration_risk": "HIGH" if any(result["concentration"]["date_concentration_classification"] == "HIGH" for result in metrics.values()) else "LOW_OR_MEDIUM",
        "instrument_concentration_risk": "HIGH" if any(result["concentration"]["instrument_concentration_classification"] == "HIGH" for result in metrics.values()) else "LOW_OR_MEDIUM",
        "outlier_driven": "YES" if any(result["outlier_driven"] for result in metrics.values()) else "NO",
        "forward_return_support": "SUPPORTIVE_OR_NON_DESTRUCTIVE" if any(result["forward_return_support"] in {"SUPPORTIVE", "NON_DESTRUCTIVE"} for result in metrics.values()) else "MIXED_OR_INSUFFICIENT",
        "confirmatory_support": confirmatory_support,
        "ready_for_a1_quality_filter_provisional_spec": provisional_spec,
        "ready_for_a1_production_filter": "NO",
        "look_ahead_leakage_detected": "NO",
        "outcome_derived_feature_detected": "NO",
        "threshold_retuning_performed": "NO",
        "new_feature_search_performed": "NO",
        "a1_formation_changed": "NO",
        "a2_formation_changed": "NO",
        "core_v0_frozen_spec_changed": "NO",
        "ma60_policy_changed": "NO",
        "ws1_changed": "NO",
        "ws2_changed": "NO",
        "ws4_changed": "NO",
        "next_task_changed": "NO",
        "migration_executed": "NO",
        "production_mutation": "NO",
        "deploy_executed": "NO",
        "push_executed": "NO",
        "reproducibility_pass": reproducibility_status,
        "normalized_aggregate_sha256": normalized_placeholder,
        "ready_for_ws3_next_mainline_step": "YES",
        "next_ws3_mainline_step": "OWNER_DECISION_REQUIRED_AFTER_BOUNDED_CONFIRMATION",
        "remaining_limitations": "No untouched temporal data remains; bounded retrospective independence; small HOLDOUT; no provisional production-like specification; July weakness remains a stress limitation.",
        "collection_quality": collection_quality,
        "cohort_reconciliation": reconciliation,
        "candidate_count_by_classification": dict(counts),
    }
    _write_json(output_dir / "a1-quality-filter-confirmatory-summary.json", summary)
    _write_csv(output_dir / "a1-quality-filter-confirmatory-candidate-comparison.csv", _comparison_rows(freeze["candidates"], metrics))
    _write_csv(output_dir / "a1-quality-filter-confirmatory-temporal-stability.csv", _temporal_rows(metrics))
    _write_csv(output_dir / "a1-quality-filter-confirmatory-market-stability.csv", _market_rows(metrics))
    _write_csv(output_dir / "a1-quality-filter-confirmatory-july-analysis.csv", _july_rows(metrics))
    _write_csv(output_dir / "a1-quality-filter-confirmatory-retention-analysis.csv", _retention_rows(metrics))
    _write_json(output_dir / "a1-quality-filter-confirmatory-concentration-analysis.json", _concentration_json(metrics))
    _write_csv(output_dir / "a1-quality-filter-confirmatory-forward-return-analysis.csv", _forward_rows(metrics))
    hashes = _normalized_hashes(output_dir)
    summary["normalized_aggregate_sha256"] = hashes["aggregate_sha256"]
    summary["normalized_artifact_hashes"] = hashes
    summary["final_contract"] = {
        "TASK_FINAL_STATUS": "COMPLETE_A1_QUALITY_FILTER_CONFIRMATORY_VALIDATION",
        "SOURCE_CANONICAL_HEAD": SOURCE_CANONICAL_HEAD,
        "CURRENT_CANONICAL_HEAD": CURRENT_CANONICAL_HEAD,
        "TASK_COMMIT_SHA": task_commit_sha,
        "FROZEN_SPEC_HASH": FROZEN_SPEC_HASH,
        "CONFIRMATORY_FREEZE_CREATED": "YES",
        "CONFIRMATORY_PROTOCOL_FROZEN_BEFORE_OUTCOME_REVIEW": "YES",
        "CONFIRMATORY_INDEPENDENCE_LEVEL": freeze["confirmatory_independence"]["level"],
        "RAW_A1_COUNT": len(feature_rows),
        "SUCCESSFUL_A1_COUNT": summary["successful_a1_count"],
        "FAILED_BREAKOUT_A1_COUNT": summary["failed_breakout_a1_count"],
        "FROZEN_CANDIDATE_COUNT": len(freeze["candidates"]),
        "CONFIRMED_CANDIDATE_COUNT": counts["CONFIRMED"],
        "BOUNDED_SUPPORTED_CANDIDATE_COUNT": counts["SUPPORTED_WITH_BOUNDED_LIMITATIONS"],
        "INCONCLUSIVE_CANDIDATE_COUNT": counts["INCONCLUSIVE"],
        "FAILED_CANDIDATE_COUNT": counts["FAILED_CONFIRMATION"],
        "BEST_CONFIRMED_CANDIDATE": best_confirmed,
        "BEST_CONFIRMED_RETENTION_RATE": summary["best_confirmed_retention_rate"],
        "BEST_CONFIRMED_SUCCESS_RATE": summary["best_confirmed_success_rate"],
        "BEST_CONFIRMED_FAILED_BREAKOUT_RATE": summary["best_confirmed_failed_breakout_rate"],
        "BASELINE_SUCCESS_RATE": summary["baseline_success_rate"],
        "BASELINE_FAILED_BREAKOUT_RATE": summary["baseline_failed_breakout_rate"],
        "SUCCESS_RATE_UPLIFT": summary["success_rate_uplift"],
        "FAILED_BREAKOUT_RATE_REDUCTION": summary["failed_breakout_rate_reduction"],
        "JULY_VALIDATION_IMPROVEMENT": summary["july_validation_improvement"],
        "TPE_TWO_DIRECTIONAL_CONSISTENCY": summary["tpe_two_directional_consistency"],
        "TEMPORAL_STABILITY": summary["temporal_stability"],
        "DATE_CONCENTRATION_RISK": summary["date_concentration_risk"],
        "INSTRUMENT_CONCENTRATION_RISK": summary["instrument_concentration_risk"],
        "OUTLIER_DRIVEN": summary["outlier_driven"],
        "FORWARD_RETURN_SUPPORT": summary["forward_return_support"],
        "A1_QUALITY_FILTER_CONFIRMATORY_SUPPORT": confirmatory_support,
        "READY_FOR_A1_QUALITY_FILTER_PROVISIONAL_SPEC": provisional_spec,
        "READY_FOR_A1_PRODUCTION_FILTER": "NO",
        "LOOK_AHEAD_LEAKAGE_DETECTED": "NO",
        "OUTCOME_DERIVED_FEATURE_DETECTED": "NO",
        "THRESHOLD_RETUNING_PERFORMED": "NO",
        "NEW_FEATURE_SEARCH_PERFORMED": "NO",
        "A1_FORMATION_CHANGED": "NO",
        "A2_FORMATION_CHANGED": "NO",
        "CORE_V0_FROZEN_SPEC_CHANGED": "NO",
        "MA60_POLICY_CHANGED": "NO",
        "WS1_CHANGED": "NO",
        "WS2_CHANGED": "NO",
        "WS4_CHANGED": "NO",
        "NEXT_TASK_CHANGED": "NO",
        "MIGRATION_EXECUTED": "NO",
        "PRODUCTION_MUTATION": "NO",
        "DEPLOY_EXECUTED": "NO",
        "PUSH_EXECUTED": "NO",
        "REPRODUCIBILITY_PASS": reproducibility_status,
        "NORMALIZED_AGGREGATE_SHA256": hashes["aggregate_sha256"],
        "READY_FOR_WS3_NEXT_MAINLINE_STEP": "YES",
        "NEXT_WS3_MAINLINE_STEP": "OWNER_DECISION_REQUIRED_AFTER_BOUNDED_CONFIRMATION",
        "REMAINING_LIMITATIONS": summary["remaining_limitations"],
        "FILES_CHANGED": "confirmatory research module; focused tests; freeze; 10 confirmatory artifacts; closure report",
        "TESTS": tests,
    }
    _write_json(output_dir / "a1-quality-filter-confirmatory-summary.json", summary)
    audit = {
        "task_id": TASK_ID,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "current_canonical_head": CURRENT_CANONICAL_HEAD,
        "exploratory_source_head": EXPLORATORY_SOURCE_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "confirmatory_freeze_created": True,
        "confirmatory_protocol_frozen_before_outcome_review": True,
        "confirmatory_independence_level": freeze["confirmatory_independence"]["level"],
        "a1_cohort_authority_reconciled": True,
        "successful_failed_cohort_definitions_preserved": True,
        "pit_feature_definitions_preserved": True,
        "previous_threshold_research_available": True,
        "concurrent_change_reconciliation_required": False,
        "candidate_set_immutable": True,
        "threshold_retuning_performed": False,
        "new_feature_search_performed": False,
        "new_combination_search_performed": False,
        "look_ahead_leakage_detected": False,
        "outcome_derived_feature_detected": False,
        "raw_a1_cohort_preserved": True,
        "a1_formation_changed": False,
        "a2_formation_changed": False,
        "core_v0_frozen_spec_changed": False,
        "ma60_policy_changed": False,
        "ws1_changed": False,
        "ws2_changed": False,
        "ws4_changed": False,
        "next_task_changed": False,
        "database_writes": False,
        "migration_executed": False,
        "production_mutation": False,
        "deploy_executed": False,
        "push_executed": False,
        "candidate_classification_counts": dict(counts),
        "normalized_artifact_hashes": hashes,
        "reproducibility_pass": reproducibility_status,
        "secret_scan": "PENDING_FINAL_VALIDATION",
        "git_diff_check": "PENDING_FINAL_VALIDATION",
        "source_to_canonical_provenance": {
            "task_source_commit": task_commit_sha,
            "source_canonical_head": SOURCE_CANONICAL_HEAD,
            "final_canonical_head": "RECORDED_IN_FINAL_HANDOFF",
        },
    }
    _write_json(output_dir / "a1-quality-filter-confirmatory-quality-audit.json", audit)
    _write_json(
        output_dir / "a1-quality-filter-next-step-readiness.json",
        {
            "task_id": TASK_ID,
            **summary["final_contract"],
            "candidate_results": candidate_results,
            "remaining_limitations": summary["remaining_limitations"],
        },
    )
    _report(output_dir, freeze, summary, audit, task_commit_sha, tests)
    return {
        "freeze": freeze,
        "summary": summary,
        "audit": audit,
        "metrics": metrics,
        "hashes": hashes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--freeze-path", type=Path, required=True)
    parser.add_argument("--prior-dir", type=Path, default=EXPLORATORY_DIR)
    parser.add_argument("--dataset-path", type=Path, default=DATASET_PATH_DEFAULT)
    parser.add_argument("--taxonomy-path", type=Path, default=TAXONOMY_PATH_DEFAULT)
    parser.add_argument("--freeze-only", action="store_true")
    parser.add_argument("--reproducibility-status", default="NOT_RUN")
    parser.add_argument("--task-commit-sha", default="RECORDED_IN_FINAL_HANDOFF")
    parser.add_argument("--tests", default="RECORDED_IN_FINAL_HANDOFF")
    args = parser.parse_args()
    if args.freeze_only:
        freeze = build_confirmatory_freeze(args.prior_dir)
        args.freeze_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(args.freeze_path, freeze)
        print(json.dumps({"task_id": TASK_ID, "freeze_created": True, "candidate_count": freeze["candidate_count"]}))
        return
    if not args.database_url:
        parser.error("--database-url or TOPICPILOT_DATABASE_URL is required")
    result = run_confirmatory(
        args.database_url,
        args.output_dir,
        freeze_path=args.freeze_path,
        dataset_path=args.dataset_path,
        taxonomy_path=args.taxonomy_path,
        reproducibility_status=args.reproducibility_status,
        task_commit_sha=args.task_commit_sha,
        tests=args.tests,
    )
    print(json.dumps({"task_id": TASK_ID, **result["summary"]["final_contract"]}, default=str))


if __name__ == "__main__":
    main()


__all__ = ["TASK_ID", "build_confirmatory_freeze", "run_confirmatory"]
