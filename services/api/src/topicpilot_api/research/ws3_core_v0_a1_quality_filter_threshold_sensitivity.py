"""Research-only coarse threshold sensitivity for the frozen Core V0 A1 cohort.

This module consumes the prior WS3 ex-ante feature implementation and prior
evidence artifacts.  It deliberately freezes a small, prior-evidence-derived
feature set and train-only coarse quantile cut points before evaluating any
forward outcomes.  It is not a strategy optimizer and never writes a
production filter.
"""

# ruff: noqa: E501  # Exact task, artifact, and report contract strings are intentional.

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from itertools import combinations
from pathlib import Path
from statistics import mean, median
from typing import Any

from topicpilot_api.research.ws3_core_v0_a1_ex_ante_discrimination import (
    FROZEN_SPEC_HASH as PRIOR_FROZEN_SPEC_HASH,
)
from topicpilot_api.research.ws3_core_v0_a1_ex_ante_discrimination import (
    SOURCE_BASELINE_HEAD,
    _build_feature_rows,
    _cohort_reconciliation,
    _date_value,
    _segment_name,
    build_feature_manifest,
    collect_observations,
)

TASK_ID = "TASK-WS3-CORE-V0-A1-QUALITY-FILTER-THRESHOLD-AND-SENSITIVITY-RESEARCH-20260818"
PRIOR_TASK_ID = (
    "TASK-WS3-CORE-V0-A1-EX-ANTE-SUCCESS-VS-FAILED-BREAKOUT-DISCRIMINATION-RESEARCH-20260818"
)
SOURCE_CANONICAL_HEAD = "035587e4f263447e778f9384971885e03a53ecc2"
PRIOR_RESEARCH_SOURCE_HEAD = "3ab70b612cbb30335b43a5650d145488f9e8b2c1"
FROZEN_SPEC_HASH = PRIOR_FROZEN_SPEC_HASH
DATASET_AUTHORITY = (
    "canonical Postgres historical read model via read_historical_bars; "
    "REC-A1 event-aware research dataset preserved"
)
PRIOR_REPORT_DIR = Path(
    "reports/TASK-WS3-CORE-V0-A1-EX-ANTE-SUCCESS-VS-FAILED-BREAKOUT-DISCRIMINATION-RESEARCH-20260818"
)
PRIOR_COMPARISON_PATH = "ws3-core-v0-a1-success-vs-failed-feature-comparison.csv"
PRIOR_TIME_STABILITY_PATH = "ws3-core-v0-a1-feature-time-stability.csv"
PRIOR_DATE_REGIME_PATH = "ws3-core-v0-a1-feature-date-regime-confounding.csv"
DATASET_PATH_DEFAULT = Path(
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json"
)
TAXONOMY_PATH_DEFAULT = Path(
    "reports/TASK-WS3-CORE-V0-A1-A2-VALIDATION-STABILITY-AND-FAILURE-MODE-REVIEW-20260818/ws3-core-v0-a1-nontransition-taxonomy.csv"
)
PRIMARY_SELECTED_FEATURES = (
    "recent_20_high_proximity",
    "recent_20_high_age_sessions",
    "return_5d",
    "close_ma20_distance",
    "volume_ratio_5",
    "true_range_pct",
    "same_day_volume_ratio_20_percentile",
)
PRIMARY_FEATURE_SELECTION_RATIONALE = {
    "recent_20_high_proximity": (
        "Prior robust BREAKOUT_PROXIMITY evidence, directionally consistent in "
        "Development/Validation/Holdout, and prior date-centered stock-level signal."
    ),
    "recent_20_high_age_sessions": (
        "Prior robust CONSOLIDATION_STRUCTURE evidence with a large stable effect and "
        "no prior date-regime flag."
    ),
    "return_5d": (
        "Prior robust MOMENTUM evidence, stable lower-in-success direction, and no prior "
        "date-regime flag."
    ),
    "close_ma20_distance": (
        "Prior robust MA_STRUCTURE evidence, stable lower-in-success direction, and "
        "stock-level date-centered signal."
    ),
    "volume_ratio_5": (
        "Prior robust VOLUME_CONFIRMATION evidence with stable direction and no prior "
        "date-regime flag."
    ),
    "true_range_pct": (
        "Prior top robust VOLATILITY evidence, stable direction, and the strongest prior "
        "stock-level effect among the selected families."
    ),
    "same_day_volume_ratio_20_percentile": (
        "Prior robust RELATIVE_CONTEXT evidence, stable direction, and a distinct "
        "cross-sectional participation interpretation."
    ),
}
QUANTILE_GRID = (0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80)
QUANTILE_LABELS = tuple(f"Q{int(value * 100)}" for value in QUANTILE_GRID)
SEGMENT_LABELS = (
    ("TRAIN", "DEVELOPMENT_AVAILABLE"),
    ("VALIDATION", "VALIDATION"),
    ("HOLDOUT", "HOLDOUT"),
)
OUTCOME_HORIZONS = (1, 3, 5, 10)
PRIMARY_COHORTS = ("SUCCESSFUL_A1", "FAILED_BREAKOUT_A1")
LOW_SAMPLE_PER_COHORT = 20
QUALITY_DELTA_GUIDE = 0.05
PLATEAU_DELTA_TOLERANCE = 0.05
HIGH_REDUNDANCY_ABS_SPEARMAN = 0.80
MAX_COMBINATIONS = 3
PAIR_CANDIDATES = (
    ("recent_20_high_proximity", "true_range_pct"),
    ("recent_20_high_age_sessions", "volume_ratio_5"),
    ("return_5d", "close_ma20_distance"),
)
ANALYTICAL_ARTIFACT_NAMES = (
    "ws3-core-v0-a1-threshold-sensitivity-summary.json",
    "ws3-core-v0-a1-single-feature-threshold-surface.csv",
    "ws3-core-v0-a1-threshold-stability-by-segment.csv",
    "ws3-core-v0-a1-quality-retention-tradeoff.csv",
    "ws3-core-v0-a1-threshold-concentration-analysis.json",
    "ws3-core-v0-a1-two-feature-combination-diagnostic.csv",
    "ws3-core-v0-a1-filter-candidate-cards.json",
)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _date_text(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _percentile(values: Sequence[float], fraction: float) -> float | None:
    ordered = sorted(value for value in values if value is not None and math.isfinite(value))
    if not ordered:
        return None
    position = fraction * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + weight * (ordered[upper] - ordered[lower])


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _rank(values: Sequence[float]) -> list[float]:
    ordered = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][0] == ordered[cursor][0]:
            end += 1
        average_rank = (cursor + 1 + end) / 2.0
        for _, index in ordered[cursor:end]:
            ranks[index] = average_rank
        cursor = end
    return ranks


def _spearman(values_left: Sequence[float], values_right: Sequence[float]) -> float | None:
    pairs = [(left, right) for left, right in zip(values_left, values_right, strict=True)]
    if len(pairs) < 3:
        return None
    left_rank = _rank([pair[0] for pair in pairs])
    right_rank = _rank([pair[1] for pair in pairs])
    left_mean = mean(left_rank)
    right_mean = mean(right_rank)
    numerator = sum(
        (left - left_mean) * (right - right_mean)
        for left, right in zip(left_rank, right_rank, strict=True)
    )
    denominator_left = math.sqrt(sum((value - left_mean) ** 2 for value in left_rank))
    denominator_right = math.sqrt(sum((value - right_mean) ** 2 for value in right_rank))
    denominator = denominator_left * denominator_right
    return numerator / denominator if denominator else 0.0


def _prior_context(prior_dir: Path) -> dict[str, Any]:
    manifest = json.loads(
        (prior_dir / "ws3-core-v0-a1-ex-ante-feature-manifest.json").read_text(encoding="utf-8")
    )
    quality = json.loads(
        (prior_dir / "ws3-core-v0-a1-ex-ante-quality-audit.json").read_text(encoding="utf-8")
    )
    readiness = json.loads(
        (prior_dir / "ws3-core-v0-a1-ex-ante-next-step-readiness.json").read_text(encoding="utf-8")
    )
    family = json.loads(
        (prior_dir / "ws3-core-v0-a1-feature-family-assessment.json").read_text(encoding="utf-8")
    )
    if manifest["task_id"] != PRIOR_TASK_ID or quality["task_id"] != PRIOR_TASK_ID:
        raise RuntimeError("PRIOR_TASK_ARTIFACT_ID_MISMATCH")
    if (
        manifest["frozen_spec_hash"] != FROZEN_SPEC_HASH
        or quality["frozen_spec_hash"] != FROZEN_SPEC_HASH
    ):
        raise RuntimeError("PRIOR_FROZEN_SPEC_MISMATCH")
    if manifest["feature_count"] != 40 or manifest["point_in_time_valid_feature_count"] != 40:
        raise RuntimeError("PRIOR_MANIFEST_RECONCILIATION_FAILED")
    if quality["cohort_counts"] != {
        "A1_TOTAL_COUNT": 700,
        "SUCCESSFUL_A1_COUNT": 386,
        "FAILED_BREAKOUT_A1_COUNT": 214,
        "CONTINUED_CONSOLIDATION_COUNT": 30,
        "STRUCTURE_LOSS_COUNT": 37,
        "UNCLASSIFIED_COUNT": 33,
    }:
        raise RuntimeError("PRIOR_COHORT_RECONCILIATION_FAILED")
    top_findings = {row["feature_name"]: row for row in family["top_findings"]}
    comparison_rows = {
        row["feature_name"]: row
        for row in _read_csv_rows(prior_dir / PRIOR_COMPARISON_PATH)
    }
    stability_rows = {
        row["feature_name"]: row
        for row in _read_csv_rows(prior_dir / PRIOR_TIME_STABILITY_PATH)
    }
    regime_rows = {
        row["feature_name"]: row
        for row in _read_csv_rows(prior_dir / PRIOR_DATE_REGIME_PATH)
    }
    evidence_sources = {}
    for name in PRIMARY_SELECTED_FEATURES:
        if name in top_findings:
            evidence_sources[name] = "FEATURE_FAMILY_ASSESSMENT_TOP_FINDINGS"
            continue
        comparison = comparison_rows.get(name)
        stability = stability_rows.get(name)
        regime = regime_rows.get(name)
        if not comparison or not stability or not regime:
            continue
        if not (
            comparison["allowed_for_primary_analysis"].upper() == "TRUE"
            and stability["DIRECTION_CONSISTENT"] == "YES"
            and stability["VALIDATION_SAMPLE_STATUS"] == "ADEQUATE"
            and regime["FEATURE_DATE_REGIME_CONFOUNDED"] == "NO"
        ):
            continue
        top_findings[name] = {
            "feature_name": name,
            "category": comparison["category"],
            "classification": "ROBUST_CANDIDATE",
            "direction": comparison["direction"],
            "standardized_effect_size": float(comparison["standardized_effect_size"]),
            "validation_consistent": stability["DIRECTION_CONSISTENT"],
            "date_regime_confounding": regime["FEATURE_DATE_REGIME_CONFOUNDED"],
        }
        evidence_sources[name] = (
            "SUCCESS_VS_FAILED_COMPARISON+FEATURE_TIME_STABILITY+"
            "FEATURE_DATE_REGIME_CONFOUNDING"
        )
    missing = [name for name in PRIMARY_SELECTED_FEATURES if name not in top_findings]
    if missing or any(
        top_findings[name]["classification"] != "ROBUST_CANDIDATE"
        for name in PRIMARY_SELECTED_FEATURES
    ):
        raise RuntimeError(f"PRIMARY_FEATURE_PROVENANCE_FAILED:{missing}")
    return {
        "manifest": manifest,
        "quality": quality,
        "readiness": readiness,
        "family": family,
        "top_findings": top_findings,
        "feature_evidence_sources": evidence_sources,
        "primary_robust_count": quality["classification_counts"]["ROBUST_CANDIDATE"],
    }


def select_primary_features(prior: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the fixed feature set selected from prior artifacts only."""
    selected = []
    for name in PRIMARY_SELECTED_FEATURES:
        prior_row = prior["top_findings"][name]
        selected.append(
            {
                "feature_name": name,
                "category": prior_row["category"],
                "prior_classification": prior_row["classification"],
                "prior_direction": prior_row["direction"],
                "prior_standardized_effect_size": prior_row["standardized_effect_size"],
                "prior_validation_consistent": prior_row["validation_consistent"],
                "prior_date_regime_confounding": prior_row["date_regime_confounding"],
                "prior_evidence_source": prior.get("feature_evidence_sources", {}).get(
                    name, "FEATURE_FAMILY_ASSESSMENT_TOP_FINDINGS"
                ),
                "selection_rationale": PRIMARY_FEATURE_SELECTION_RATIONALE[name],
            }
        )
    return selected


def _build_reverse_dependencies(
    selected: Sequence[Mapping[str, Any]], manifest: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    feature_dependencies = []
    input_columns = set()
    for row in selected:
        spec = manifest[row["feature_name"]]
        input_columns.update(spec["input_columns"])
        feature_dependencies.append(
            {
                "feature_name": row["feature_name"],
                "category": spec["category"],
                "required_input_columns": spec["input_columns"],
                "lookback": spec["lookback"],
                "timestamp_rule": spec["timestamp_rule"],
                "point_in_time_available": spec["point_in_time_available"],
                "source_lineage": spec["authority_source"],
            }
        )
    return {
        "scope": "A1 quality-filter threshold research only; no global WS3 readiness gate",
        "candidate_type": "A1_PRE_BREAKOUT",
        "minimum_panel": {
            "evaluation_context": [
                "evaluation_session",
                "signal_date",
                "instrument_id",
                "market (TPE/TWO)",
                "as_of_timestamp <= signal_date",
            ],
            "pit_membership_and_candidate_context": [
                "A1_PRE_BREAKOUT membership/context at T",
                "candidate_inputs.reference_value as observed at T",
                "canonical cohort/source lineage",
            ],
            "canonical_ohlcv_fields": sorted(input_columns),
            "technical_evidence_fields": [],
            "selected_feature_dependencies": feature_dependencies,
            "forward_outcomes_evaluation_only": [
                "T+1",
                "T+3",
                "T+5",
                "T+10",
                "REC-A1 event-aware outcome exclusion metadata",
            ],
            "formation_boundary": (
                "Candidate formation consumes only information effective/observable <= T; "
                "candidate state is frozen at T. Forward outcomes cannot alter eligibility."
            ),
        },
        "source_lineage": {
            "research_read_model": DATASET_AUTHORITY,
            "prior_research_source_head": PRIOR_RESEARCH_SOURCE_HEAD,
            "frozen_spec_hash": FROZEN_SPEC_HASH,
            "event_dataset_is_evaluation_integrity_only": True,
        },
        "ws1_ws2_implication": (
            "No complete Historical Topic/System State or WS2 technical publication is "
            "required for this A1 panel; only the listed candidate-specific fields are a "
            "dependency for this research lane."
        ),
    }


def _attach_outcomes(
    feature_rows: Sequence[Mapping[str, Any]],
    a1_rows: Sequence[Mapping[str, Any]],
    cohort_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    source_by_key = {(row["instrument_id"], row["signal_date"]): row for row in a1_rows}
    index_by_key = {(row["instrument_id"], row["signal_date"]): row["index"] for row in cohort_rows}
    output = []
    for row in feature_rows:
        key = (row["instrument_id"], row["signal_date"])
        source = source_by_key[key]
        output.append(
            {
                **row,
                "source_index": index_by_key[key],
                "returns": {
                    str(horizon): source["returns"].get(horizon) for horizon in OUTCOME_HORIZONS
                },
                "event_excluded_horizons": sorted(source.get("event_excluded_horizons", set())),
            }
        )
    return output


def _segment_rows(rows: Sequence[Mapping[str, Any]], segment: str) -> list[Mapping[str, Any]]:
    if segment == "FULL_SAMPLE":
        return list(rows)
    expected = dict(SEGMENT_LABELS)[segment]
    return [row for row in rows if _segment_name(_date_value(row["signal_date"])) == expected]


def _baseline_rates(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    success = sum(row["cohort"] == "SUCCESSFUL_A1" for row in rows)
    failed = sum(row["cohort"] == "FAILED_BREAKOUT_A1" for row in rows)
    resolved = success + failed
    return {
        "unfiltered_a1_count": len(rows),
        "unfiltered_resolved_primary_count": resolved,
        "unfiltered_success_count": success,
        "unfiltered_failed_breakout_count": failed,
        "unfiltered_a1_success_rate": success / resolved if resolved else None,
        "unfiltered_a1_failed_breakout_rate": failed / resolved if resolved else None,
    }


def _outcome_diagnostics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    output = {}
    for horizon in OUTCOME_HORIZONS:
        values = []
        for row in rows:
            if row["cohort"] not in PRIMARY_COHORTS or horizon in row.get(
                "event_excluded_horizons", []
            ):
                continue
            value = _float(row.get("returns", {}).get(str(horizon)))
            if value is not None:
                values.append(value)
        output[f"T+{horizon}"] = {
            "N": len(values),
            "mean": mean(values) if values else None,
            "median": median(values) if values else None,
            "win_rate": sum(value > 0 for value in values) / len(values) if values else None,
        }
    return output


def _region_metrics(
    selected_rows: Sequence[Mapping[str, Any]],
    baseline_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    baseline = _baseline_rates(baseline_rows)
    success = sum(row["cohort"] == "SUCCESSFUL_A1" for row in selected_rows)
    failed = sum(row["cohort"] == "FAILED_BREAKOUT_A1" for row in selected_rows)
    resolved = success + failed
    success_rate = success / resolved if resolved else None
    failed_rate = failed / resolved if resolved else None
    return {
        "observation_count": len(selected_rows),
        "retained_a1_count": len(selected_rows),
        "retention_rate": len(selected_rows) / baseline["unfiltered_a1_count"]
        if baseline["unfiltered_a1_count"]
        else None,
        "resolved_primary_count": resolved,
        "primary_retention_rate": resolved / baseline["unfiltered_resolved_primary_count"]
        if baseline["unfiltered_resolved_primary_count"]
        else None,
        "success_count": success,
        "failed_breakout_count": failed,
        "filtered_success_rate": success_rate,
        "filtered_failed_breakout_rate": failed_rate,
        "unfiltered_a1_success_rate": baseline["unfiltered_a1_success_rate"],
        "unfiltered_a1_failed_breakout_rate": baseline["unfiltered_a1_failed_breakout_rate"],
        "success_rate_delta": success_rate - baseline["unfiltered_a1_success_rate"]
        if success_rate is not None and baseline["unfiltered_a1_success_rate"] is not None
        else None,
        "failed_breakout_rate_delta": failed_rate - baseline["unfiltered_a1_failed_breakout_rate"]
        if failed_rate is not None and baseline["unfiltered_a1_failed_breakout_rate"] is not None
        else None,
        "low_sample_region": success < LOW_SAMPLE_PER_COHORT or failed < LOW_SAMPLE_PER_COHORT,
        "outcome_diagnostics": _outcome_diagnostics(selected_rows),
    }


def _directionally_improves(metrics: Mapping[str, Any]) -> bool:
    return (
        metrics.get("success_rate_delta") is not None
        and metrics.get("failed_breakout_rate_delta") is not None
        and metrics["success_rate_delta"] >= 0
        and metrics["failed_breakout_rate_delta"] <= 0
    )


def _strongly_improves(metrics: Mapping[str, Any]) -> bool:
    return (
        metrics.get("success_rate_delta") is not None
        and metrics.get("failed_breakout_rate_delta") is not None
        and metrics["success_rate_delta"] >= QUALITY_DELTA_GUIDE
        and metrics["failed_breakout_rate_delta"] <= -QUALITY_DELTA_GUIDE
    )


def _region_passes(
    row: Mapping[str, Any], feature_name: str, feature_rows: Sequence[Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    threshold = row["threshold_value"]
    direction = row["expected_direction"]
    return [
        source
        for source in feature_rows
        if source.get(feature_name) is not None
        and (
            (source[feature_name] >= threshold)
            if direction == "HIGHER_IN_SUCCESS"
            else (source[feature_name] <= threshold)
        )
    ]


def _concentration(selected_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    primary = [row for row in selected_rows if row["cohort"] in PRIMARY_COHORTS]
    resolved_count = len(primary)
    dates = Counter(_date_text(row["signal_date"]) for row in primary)
    weeks = Counter(
        f"{row['signal_date'].isocalendar().year}-W{row['signal_date'].isocalendar().week:02d}"
        for row in primary
        if isinstance(row["signal_date"], date)
    )
    instruments = Counter(row["instrument_id"] for row in primary)
    markets = Counter(row["market"] for row in primary)
    top_date_share = max(dates.values(), default=0) / resolved_count if resolved_count else None
    top_week_share = max(weeks.values(), default=0) / resolved_count if resolved_count else None
    top_instrument_share = (
        max(instruments.values(), default=0) / resolved_count if resolved_count else None
    )
    top_five_instrument_share = (
        sum(value for _, value in instruments.most_common(5)) / resolved_count
        if resolved_count
        else None
    )
    if resolved_count < LOW_SAMPLE_PER_COHORT * 2:
        date_risk = instrument_risk = "INCONCLUSIVE"
    else:
        date_risk = (
            "HIGH"
            if (top_date_share or 0) >= 0.30 or (top_week_share or 0) >= 0.70
            else "MEDIUM"
            if (top_date_share or 0) >= 0.20 or (top_week_share or 0) >= 0.55
            else "LOW"
        )
        instrument_risk = (
            "HIGH"
            if (top_instrument_share or 0) >= 0.10 or (top_five_instrument_share or 0) >= 0.30
            else "MEDIUM"
            if (top_instrument_share or 0) >= 0.05 or (top_five_instrument_share or 0) >= 0.20
            else "LOW"
        )
    return {
        "resolved_primary_count": resolved_count,
        "top_dates": dates.most_common(5),
        "top_weeks": weeks.most_common(5),
        "top_instruments": instruments.most_common(10),
        "market_counts": dict(markets),
        "top_date_share": top_date_share,
        "top_week_share": top_week_share,
        "top_instrument_share": top_instrument_share,
        "top_five_instrument_share": top_five_instrument_share,
        "DATE_CONCENTRATION_RISK": date_risk,
        "INSTRUMENT_CONCENTRATION_RISK": instrument_risk,
    }


def _market_split(
    selected_rows: Sequence[Mapping[str, Any]], baseline_rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    output = {}
    for market in ("TPE", "TWO"):
        region = [row for row in selected_rows if row["market"] == market]
        baseline = [row for row in baseline_rows if row["market"] == market]
        if (
            len([row for row in baseline if row["cohort"] in PRIMARY_COHORTS])
            < LOW_SAMPLE_PER_COHORT * 2
        ):
            output[market] = {"status": "INSUFFICIENT_SAMPLE"}
            continue
        output[market] = _region_metrics(region, baseline)
    valid = [row for row in output.values() if "success_rate_delta" in row]
    consistent = bool(valid) and all(_directionally_improves(row) for row in valid)
    output["TPE_TWO_DIRECTIONALLY_CONSISTENT"] = (
        "YES" if consistent else "NO" if valid else "INCONCLUSIVE"
    )
    return output


def _build_redundancy(
    feature_rows: Sequence[Mapping[str, Any]], selected: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    pairs = []
    for left, right in combinations(selected, 2):
        complete = [
            (float(row[left["feature_name"]]), float(row[right["feature_name"]]))
            for row in feature_rows
            if row.get(left["feature_name"]) is not None
            and row.get(right["feature_name"]) is not None
        ]
        correlation = _spearman([pair[0] for pair in complete], [pair[1] for pair in complete])
        pairs.append(
            {
                "feature_left": left["feature_name"],
                "feature_right": right["feature_name"],
                "N_complete": len(complete),
                "spearman_rho": correlation,
                "HIGH_REDUNDANCY": correlation is not None
                and abs(correlation) >= HIGH_REDUNDANCY_ABS_SPEARMAN,
            }
        )
    return {
        "method": "pairwise Spearman rank correlation on all A1 PIT feature rows; no outcomes used",
        "high_redundancy_threshold_abs_spearman": HIGH_REDUNDANCY_ABS_SPEARMAN,
        "pairs": pairs,
        "high_redundancy_pair_count": sum(pair["HIGH_REDUNDANCY"] for pair in pairs),
    }


def _threshold_rows(
    feature_rows: Sequence[Mapping[str, Any]],
    selected: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    train_rows = _segment_rows(feature_rows, "TRAIN")
    full_baseline = _baseline_rates(feature_rows)
    output = []
    for feature in selected:
        name = feature["feature_name"]
        direction = feature["prior_direction"]
        train_values = [float(row[name]) for row in train_rows if row.get(name) is not None]
        cuts = [_percentile(train_values, fraction) for fraction in QUANTILE_GRID]
        if any(cut is None for cut in cuts):
            raise RuntimeError(f"THRESHOLD_GRID_UNAVAILABLE:{name}")
        for quantile_label, quantile_fraction, threshold in zip(
            QUANTILE_LABELS, QUANTILE_GRID, cuts, strict=True
        ):
            assert threshold is not None
            region_id = (
                f"{name}__UPPER_GE_{quantile_label}"
                if direction == "HIGHER_IN_SUCCESS"
                else f"{name}__LOWER_LE_{quantile_label}"
            )
            selected_rows = _region_passes(
                {"threshold_value": threshold, "expected_direction": direction}, name, feature_rows
            )
            full = _region_metrics(selected_rows, feature_rows)
            train_selected = _region_passes(
                {"threshold_value": threshold, "expected_direction": direction}, name, train_rows
            )
            validation_rows = _segment_rows(feature_rows, "VALIDATION")
            holdout_rows = _segment_rows(feature_rows, "HOLDOUT")
            validation_selected = _region_passes(
                {"threshold_value": threshold, "expected_direction": direction},
                name,
                validation_rows,
            )
            holdout_selected = _region_passes(
                {"threshold_value": threshold, "expected_direction": direction}, name, holdout_rows
            )
            row = {
                "feature_name": name,
                "category": feature["category"],
                "expected_direction": direction,
                "region_id": region_id,
                "threshold_quantile": quantile_label,
                "threshold_fraction": quantile_fraction,
                "threshold_value": threshold,
                "train_cutpoint_source": "A1 feature distribution in TRAIN only; no cohort labels or outcomes",
                "full": full,
                "TRAIN": _region_metrics(train_selected, train_rows),
                "VALIDATION": _region_metrics(validation_selected, validation_rows),
                "HOLDOUT": _region_metrics(holdout_selected, holdout_rows),
                "_selected_rows": selected_rows,
                "_feature_selection": feature,
                "_baseline": full_baseline,
            }
            output.append(row)
    return output


def _july_status(validation: Mapping[str, Any]) -> str:
    if validation["low_sample_region"]:
        return "INCONCLUSIVE"
    if (
        validation["success_rate_delta"] >= QUALITY_DELTA_GUIDE
        and validation["failed_breakout_rate_delta"] <= -QUALITY_DELTA_GUIDE
    ):
        return "YES"
    if _directionally_improves(validation):
        return "PARTIAL"
    if validation["success_rate_delta"] < 0 and validation["failed_breakout_rate_delta"] > 0:
        return "NO"
    return "INCONCLUSIVE"


def _add_stability_and_classification(
    rows: list[dict[str, Any]], feature_rows: Sequence[Mapping[str, Any]]
) -> None:
    by_feature: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_feature.setdefault(row["feature_name"], []).append(row)
    for feature_regions in by_feature.values():
        feature_regions.sort(key=lambda row: row["threshold_fraction"])
        for index, row in enumerate(feature_regions):
            neighbors = []
            for neighbor_index in (index - 1, index + 1):
                if 0 <= neighbor_index < len(feature_regions):
                    neighbor = feature_regions[neighbor_index]
                    if (
                        _directionally_improves(neighbor["full"])
                        and abs(
                            neighbor["full"]["success_rate_delta"]
                            - row["full"]["success_rate_delta"]
                        )
                        <= PLATEAU_DELTA_TOLERANCE
                        and abs(
                            neighbor["full"]["failed_breakout_rate_delta"]
                            - row["full"]["failed_breakout_rate_delta"]
                        )
                        <= PLATEAU_DELTA_TOLERANCE
                    ):
                        neighbors.append(neighbor)
            row["THRESHOLD_PLATEAU_PRESENT"] = (
                "YES" if len(neighbors) >= 2 else "PARTIAL" if neighbors else "NO"
            )
            row["THRESHOLD_CLIFF_RISK"] = (
                "HIGH" if not neighbors and _directionally_improves(row["full"]) else "LOW"
            )
            train = row["TRAIN"]
            validation = row["VALIDATION"]
            holdout = row["HOLDOUT"]
            row["TRAIN_DIRECTIONALLY_IMPROVES"] = _directionally_improves(train)
            row["VALIDATION_DIRECTIONALLY_IMPROVES"] = _directionally_improves(validation)
            row["HOLDOUT_DIRECTIONALLY_IMPROVES"] = _directionally_improves(holdout)
            row["TEMPORAL_DIRECTIONALLY_CONSISTENT"] = (
                "YES"
                if row["TRAIN_DIRECTIONALLY_IMPROVES"] and row["VALIDATION_DIRECTIONALLY_IMPROVES"]
                else "NO"
            )
            row["JULY_VALIDATION_IMPROVEMENT"] = _july_status(validation)
            row["concentration"] = _concentration(row["_selected_rows"])
            row["market_split"] = _market_split(row["_selected_rows"], feature_rows)
            row["TPE_TWO_DIRECTIONALLY_CONSISTENT"] = row["market_split"][
                "TPE_TWO_DIRECTIONALLY_CONSISTENT"
            ]
            row["DATE_CONCENTRATION_RISK"] = row["concentration"]["DATE_CONCENTRATION_RISK"]
            row["INSTRUMENT_CONCENTRATION_RISK"] = row["concentration"][
                "INSTRUMENT_CONCENTRATION_RISK"
            ]
            if row["full"]["low_sample_region"]:
                classification = "INSUFFICIENT_SAMPLE"
            elif (
                _strongly_improves(row["full"])
                and row["TEMPORAL_DIRECTIONALLY_CONSISTENT"] == "YES"
                and row["THRESHOLD_PLATEAU_PRESENT"] == "YES"
                and row["JULY_VALIDATION_IMPROVEMENT"] == "YES"
                and row["DATE_CONCENTRATION_RISK"] != "HIGH"
                and row["INSTRUMENT_CONCENTRATION_RISK"] != "HIGH"
                and row["TPE_TWO_DIRECTIONALLY_CONSISTENT"] == "YES"
            ):
                classification = "ROBUST_THRESHOLD_REGION"
            elif (
                _strongly_improves(row["full"])
                and row["TEMPORAL_DIRECTIONALLY_CONSISTENT"] == "YES"
                and row["THRESHOLD_PLATEAU_PRESENT"] in {"YES", "PARTIAL"}
                and row["JULY_VALIDATION_IMPROVEMENT"] in {"YES", "PARTIAL"}
            ):
                classification = "PROMISING_THRESHOLD_REGION"
            elif _directionally_improves(row["full"]) and (
                row["TEMPORAL_DIRECTIONALLY_CONSISTENT"] == "NO"
                or row["JULY_VALIDATION_IMPROVEMENT"] == "NO"
            ):
                classification = "REGIME_DEPENDENT"
            else:
                classification = "NO_DEFENSIBLE_THRESHOLD_REGION"
            row["threshold_classification"] = classification


def _public_surface_row(row: Mapping[str, Any]) -> dict[str, Any]:
    full = row["full"]
    validation = row["VALIDATION"]
    return {
        "feature_name": row["feature_name"],
        "category": row["category"],
        "expected_direction": row["expected_direction"],
        "region_id": row["region_id"],
        "threshold_quantile": row["threshold_quantile"],
        "threshold_fraction": row["threshold_fraction"],
        "threshold_value": row["threshold_value"],
        "OBSERVATION_COUNT": full["observation_count"],
        "RETAINED_A1_COUNT": full["retained_a1_count"],
        "RETENTION_RATE": full["retention_rate"],
        "RESOLVED_PRIMARY_COUNT": full["resolved_primary_count"],
        "SUCCESS_COUNT": full["success_count"],
        "FAILED_BREAKOUT_COUNT": full["failed_breakout_count"],
        "SUCCESS_RATE": full["filtered_success_rate"],
        "FAILED_BREAKOUT_RATE": full["filtered_failed_breakout_rate"],
        "UNFILTERED_A1_SUCCESS_RATE": full["unfiltered_a1_success_rate"],
        "UNFILTERED_A1_FAILED_BREAKOUT_RATE": full["unfiltered_a1_failed_breakout_rate"],
        "SUCCESS_RATE_DELTA": full["success_rate_delta"],
        "FAILED_BREAKOUT_RATE_DELTA": full["failed_breakout_rate_delta"],
        "LOW_SAMPLE_REGION": full["low_sample_region"],
        "TRAIN_DIRECTIONALLY_IMPROVES": row["TRAIN_DIRECTIONALLY_IMPROVES"],
        "VALIDATION_DIRECTIONALLY_IMPROVES": row["VALIDATION_DIRECTIONALLY_IMPROVES"],
        "HOLDOUT_DIRECTIONALLY_IMPROVES": row["HOLDOUT_DIRECTIONALLY_IMPROVES"],
        "TEMPORAL_DIRECTIONALLY_CONSISTENT": row["TEMPORAL_DIRECTIONALLY_CONSISTENT"],
        "JULY_VALIDATION_IMPROVEMENT": row["JULY_VALIDATION_IMPROVEMENT"],
        "THRESHOLD_PLATEAU_PRESENT": row["THRESHOLD_PLATEAU_PRESENT"],
        "THRESHOLD_CLIFF_RISK": row["THRESHOLD_CLIFF_RISK"],
        "DATE_CONCENTRATION_RISK": row["DATE_CONCENTRATION_RISK"],
        "INSTRUMENT_CONCENTRATION_RISK": row["INSTRUMENT_CONCENTRATION_RISK"],
        "TPE_TWO_DIRECTIONALLY_CONSISTENT": row["TPE_TWO_DIRECTIONALLY_CONSISTENT"],
        "THRESHOLD_CLASSIFICATION": row["threshold_classification"],
        "VALIDATION_SUCCESS_RATE": validation["filtered_success_rate"],
        "VALIDATION_FAILED_BREAKOUT_RATE": validation["filtered_failed_breakout_rate"],
        "VALIDATION_SUCCESS_RATE_DELTA": validation["success_rate_delta"],
        "VALIDATION_FAILED_BREAKOUT_RATE_DELTA": validation["failed_breakout_rate_delta"],
        "FORWARD_OUTCOMES_USED_FOR_SELECTION": "NO",
    }


def _stability_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        for segment in ("TRAIN", "VALIDATION", "HOLDOUT", "FULL_SAMPLE"):
            metrics = row[segment] if segment != "FULL_SAMPLE" else row["full"]
            output.append(
                {
                    "feature_name": row["feature_name"],
                    "region_id": row["region_id"],
                    "threshold_quantile": row["threshold_quantile"],
                    "segment": segment,
                    "OBSERVATION_COUNT": metrics["observation_count"],
                    "RETAINED_A1_COUNT": metrics["retained_a1_count"],
                    "RETENTION_RATE": metrics["retention_rate"],
                    "RESOLVED_PRIMARY_COUNT": metrics["resolved_primary_count"],
                    "SUCCESS_COUNT": metrics["success_count"],
                    "FAILED_BREAKOUT_COUNT": metrics["failed_breakout_count"],
                    "SUCCESS_RATE": metrics["filtered_success_rate"],
                    "FAILED_BREAKOUT_RATE": metrics["filtered_failed_breakout_rate"],
                    "UNFILTERED_A1_SUCCESS_RATE": metrics["unfiltered_a1_success_rate"],
                    "UNFILTERED_A1_FAILED_BREAKOUT_RATE": metrics[
                        "unfiltered_a1_failed_breakout_rate"
                    ],
                    "SUCCESS_RATE_DELTA": metrics["success_rate_delta"],
                    "FAILED_BREAKOUT_RATE_DELTA": metrics["failed_breakout_rate_delta"],
                    "LOW_SAMPLE_REGION": metrics["low_sample_region"],
                    "DIRECTIONALLY_IMPROVES": _directionally_improves(metrics),
                    "JULY_VALIDATION_IMPROVEMENT": row["JULY_VALIDATION_IMPROVEMENT"]
                    if segment == "VALIDATION"
                    else None,
                }
            )
    return output


def _tradeoff_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        full = row["full"]
        output.append(
            {
                "feature_name": row["feature_name"],
                "region_id": row["region_id"],
                "threshold_quantile": row["threshold_quantile"],
                "threshold_value": row["threshold_value"],
                "quality_improvement_success_rate_delta": full["success_rate_delta"],
                "quality_improvement_failed_breakout_rate_reduction": -full[
                    "failed_breakout_rate_delta"
                ]
                if full["failed_breakout_rate_delta"] is not None
                else None,
                "retention_rate": full["retention_rate"],
                "resolved_primary_count": full["resolved_primary_count"],
                "threshold_classification": row["threshold_classification"],
                "july_validation_improvement": row["JULY_VALIDATION_IMPROVEMENT"],
                "date_concentration_risk": row["DATE_CONCENTRATION_RISK"],
                "instrument_concentration_risk": row["INSTRUMENT_CONCENTRATION_RISK"],
            }
        )
    return output


def _preferred_region(
    rows: Sequence[Mapping[str, Any]], feature_name: str
) -> dict[str, Any] | None:
    candidates = [
        row
        for row in rows
        if row["feature_name"] == feature_name
        and row["threshold_classification"]
        in {"ROBUST_THRESHOLD_REGION", "PROMISING_THRESHOLD_REGION"}
    ]
    if not candidates:
        candidates = [
            row
            for row in rows
            if row["feature_name"] == feature_name and _directionally_improves(row["full"])
        ]
    if not candidates:
        return None
    class_rank = {
        "ROBUST_THRESHOLD_REGION": 4,
        "PROMISING_THRESHOLD_REGION": 3,
        "REGIME_DEPENDENT": 1,
    }
    plateau_rank = {"YES": 3, "PARTIAL": 2, "NO": 0}
    july_rank = {"YES": 3, "PARTIAL": 2, "INCONCLUSIVE": 1, "NO": 0}
    return sorted(
        candidates,
        key=lambda row: (
            class_rank.get(row["threshold_classification"], 0),
            plateau_rank.get(row["THRESHOLD_PLATEAU_PRESENT"], 0),
            july_rank.get(row["JULY_VALIDATION_IMPROVEMENT"], 0),
            row["TEMPORAL_DIRECTIONALLY_CONSISTENT"] == "YES",
            row["full"]["retention_rate"] or 0,
        ),
        reverse=True,
    )[0]


def _combination_rows(
    feature_rows: Sequence[Mapping[str, Any]],
    baseline_rows: Sequence[Mapping[str, Any]],
    single_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    preferred = {name: _preferred_region(single_rows, name) for name in PRIMARY_SELECTED_FEATURES}
    output = []
    for left, right in PAIR_CANDIDATES[:MAX_COMBINATIONS]:
        left_region = preferred.get(left)
        right_region = preferred.get(right)
        base = {
            "combination_id": f"{left}__AND__{right}",
            "feature_left": left,
            "feature_right": right,
            "tested": bool(left_region and right_region),
            "max_features": 2,
            "candidate_selection": "bounded non-redundant-family diagnostic after single-feature research; no all-pairs search",
        }
        if not left_region or not right_region:
            output.append({**base, "status": "NOT_TESTED_NO_SINGLE_REGION"})
            continue
        selected = [
            row
            for row in feature_rows
            if row.get(left) is not None
            and row.get(right) is not None
            and (
                (row[left] >= left_region["threshold_value"])
                if left_region["expected_direction"] == "HIGHER_IN_SUCCESS"
                else (row[left] <= left_region["threshold_value"])
            )
            and (
                (row[right] >= right_region["threshold_value"])
                if right_region["expected_direction"] == "HIGHER_IN_SUCCESS"
                else (row[right] <= right_region["threshold_value"])
            )
        ]
        full = _region_metrics(selected, baseline_rows)
        train = _region_metrics(
            _segment_rows(selected, "TRAIN"), _segment_rows(baseline_rows, "TRAIN")
        )
        validation = _region_metrics(
            _segment_rows(selected, "VALIDATION"), _segment_rows(baseline_rows, "VALIDATION")
        )
        better_single = max(
            left_region["full"]["filtered_success_rate"] or 0,
            right_region["full"]["filtered_success_rate"] or 0,
        )
        better_single_retention = max(
            left_region["full"]["retention_rate"] or 0, right_region["full"]["retention_rate"] or 0
        )
        incremental_success = (full["filtered_success_rate"] or 0) - better_single
        retention_change = (full["retention_rate"] or 0) - better_single_retention
        status = (
            "COMPLEXITY_NOT_JUSTIFIED"
            if incremental_success < QUALITY_DELTA_GUIDE / 2 or retention_change <= -0.20
            else "PROMISING_COMBINATION_DIAGNOSTIC"
        )
        output.append(
            {
                **base,
                "status": status,
                "left_region_id": left_region["region_id"],
                "right_region_id": right_region["region_id"],
                "left_region": left_region["threshold_quantile"],
                "right_region": right_region["threshold_quantile"],
                "full": full,
                "TRAIN": train,
                "VALIDATION": validation,
                "JULY_VALIDATION_IMPROVEMENT": _july_status(validation),
                "DATE_CONCENTRATION_RISK": _concentration(selected)["DATE_CONCENTRATION_RISK"],
                "INSTRUMENT_CONCENTRATION_RISK": _concentration(selected)[
                    "INSTRUMENT_CONCENTRATION_RISK"
                ],
                "TPE_TWO_DIRECTIONALLY_CONSISTENT": _market_split(selected, baseline_rows)[
                    "TPE_TWO_DIRECTIONALLY_CONSISTENT"
                ],
                "incremental_success_rate_vs_better_single": incremental_success,
                "retention_rate_change_vs_better_single": retention_change,
                "forward_outcomes_used_for_selection": "NO",
            }
        )
    return output


def _combination_csv_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        full = row.get("full", {})
        validation = row.get("VALIDATION", {})
        output.append(
            {
                "combination_id": row["combination_id"],
                "feature_left": row["feature_left"],
                "feature_right": row["feature_right"],
                "tested": row["tested"],
                "status": row["status"],
                "left_region_id": row.get("left_region_id"),
                "right_region_id": row.get("right_region_id"),
                "observation_count": full.get("observation_count"),
                "retention_rate": full.get("retention_rate"),
                "success_count": full.get("success_count"),
                "failed_breakout_count": full.get("failed_breakout_count"),
                "success_rate": full.get("filtered_success_rate"),
                "failed_breakout_rate": full.get("filtered_failed_breakout_rate"),
                "success_rate_delta": full.get("success_rate_delta"),
                "failed_breakout_rate_delta": full.get("failed_breakout_rate_delta"),
                "validation_success_rate": validation.get("filtered_success_rate"),
                "validation_failed_breakout_rate": validation.get("filtered_failed_breakout_rate"),
                "validation_success_rate_delta": validation.get("success_rate_delta"),
                "validation_failed_breakout_rate_delta": validation.get(
                    "failed_breakout_rate_delta"
                ),
                "july_validation_improvement": row.get("JULY_VALIDATION_IMPROVEMENT"),
                "date_concentration_risk": row.get("DATE_CONCENTRATION_RISK"),
                "instrument_concentration_risk": row.get("INSTRUMENT_CONCENTRATION_RISK"),
                "TPE_TWO_DIRECTIONALLY_CONSISTENT": row.get("TPE_TWO_DIRECTIONALLY_CONSISTENT"),
                "incremental_success_rate_vs_better_single": row.get(
                    "incremental_success_rate_vs_better_single"
                ),
                "retention_rate_change_vs_better_single": row.get(
                    "retention_rate_change_vs_better_single"
                ),
                "forward_outcomes_used_for_selection": row.get(
                    "forward_outcomes_used_for_selection", "NO"
                ),
            }
        )
    return output


def _candidate_cards(
    single_rows: Sequence[Mapping[str, Any]], combination_rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    preferred = [_preferred_region(single_rows, name) for name in PRIMARY_SELECTED_FEATURES]
    preferred = [row for row in preferred if row is not None]
    class_rank = {"ROBUST_THRESHOLD_REGION": 3, "PROMISING_THRESHOLD_REGION": 2}
    preferred.sort(
        key=lambda row: (
            class_rank.get(row["threshold_classification"], 0),
            row["THRESHOLD_PLATEAU_PRESENT"] == "YES",
            row["JULY_VALIDATION_IMPROVEMENT"] == "YES",
            row["full"]["retention_rate"] or 0,
        ),
        reverse=True,
    )
    single_cards = []
    for row in preferred[:3]:
        single_cards.append(
            {
                "candidate_type": "SINGLE_FEATURE",
                "candidate_id": row["region_id"],
                "feature_or_combination": row["feature_name"],
                "market_interpretation": row["_feature_selection"]["selection_rationale"],
                "defensible_threshold_region": row["region_id"],
                "threshold_value_not_a_production_cut": row["threshold_value"],
                "full_sample_success_rate_delta": row["full"]["success_rate_delta"],
                "validation_success_rate_delta": row["VALIDATION"]["success_rate_delta"],
                "failed_breakout_reduction": -row["full"]["failed_breakout_rate_delta"]
                if row["full"]["failed_breakout_rate_delta"] is not None
                else None,
                "retention_rate": row["full"]["retention_rate"],
                "july_behavior": row["JULY_VALIDATION_IMPROVEMENT"],
                "threshold_plateau": row["THRESHOLD_PLATEAU_PRESENT"],
                "date_concentration": row["DATE_CONCENTRATION_RISK"],
                "instrument_concentration": row["INSTRUMENT_CONCENTRATION_RISK"],
                "forward_return_diagnostics": row["full"]["outcome_diagnostics"],
                "major_caveat": "Research candidate only; no production filter authority and no exact optimal cutoff claimed.",
                "research_classification": "STRONG_RESEARCH_CANDIDATE"
                if row["threshold_classification"] == "ROBUST_THRESHOLD_REGION"
                else "PROMISING_RESEARCH_CANDIDATE",
            }
        )
    combo_cards = []
    for row in combination_rows:
        if row.get("status") != "PROMISING_COMBINATION_DIAGNOSTIC":
            continue
        combo_cards.append(
            {
                "candidate_type": "TWO_FEATURE_COMBINATION",
                "candidate_id": row["combination_id"],
                "feature_or_combination": f"{row['feature_left']} AND {row['feature_right']}",
                "defensible_threshold_region": f"{row['left_region_id']} AND {row['right_region_id']}",
                "full_sample_success_rate_delta": row["full"]["success_rate_delta"],
                "validation_success_rate_delta": row["VALIDATION"]["success_rate_delta"],
                "failed_breakout_reduction": -row["full"]["failed_breakout_rate_delta"],
                "retention_rate": row["full"]["retention_rate"],
                "july_behavior": row["JULY_VALIDATION_IMPROVEMENT"],
                "threshold_plateau": "INHERITED_FROM_SINGLE_REGIONS",
                "date_concentration": row["DATE_CONCENTRATION_RISK"],
                "instrument_concentration": row["INSTRUMENT_CONCENTRATION_RISK"],
                "forward_return_diagnostics": row["full"]["outcome_diagnostics"],
                "major_caveat": "Bounded two-feature diagnostic only; complexity must be confirmed out of sample.",
                "research_classification": "PROMISING_RESEARCH_CANDIDATE",
            }
        )
    return {
        "top_single_feature_candidates": single_cards,
        "top_two_feature_combination_candidates": combo_cards[:2],
        "production_filter_created": False,
    }


def _artifact_hashes(output_dir: Path) -> dict[str, Any]:
    artifact_hashes = {}
    for name in ANALYTICAL_ARTIFACT_NAMES:
        path = output_dir / name
        if not path.exists():
            raise RuntimeError(f"ANALYTICAL_ARTIFACT_MISSING:{name}")
        artifact_hashes[name] = hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
    aggregate = hashlib.sha256(
        json.dumps(artifact_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "algorithm": "SHA-256",
        "byte_normalization": "CRLF_TO_LF_BEFORE_HASH",
        "artifacts": artifact_hashes,
        "aggregate_sha256": aggregate,
    }


def _report(
    output_dir: Path,
    final_fields: Mapping[str, Any],
    prior: Mapping[str, Any],
    selected: Sequence[Mapping[str, Any]],
    redundancy: Mapping[str, Any],
    cards: Mapping[str, Any],
    reverse_dependencies: Mapping[str, Any],
    audit: Mapping[str, Any],
    hashes: Mapping[str, Any],
    task_commit_sha: str,
    tests: str,
) -> None:
    lines = [
        "# WS3 Core V0 A1 Quality-Filter Threshold and Sensitivity Research",
        "",
        "## Final contract",
        "",
        "```text",
    ]
    lines.extend(f"{key}={value}" for key, value in final_fields.items())
    lines.extend(
        [
            f"SOURCE_CANONICAL_HEAD={SOURCE_CANONICAL_HEAD}",
            f"PRIOR_RESEARCH_SOURCE_HEAD={PRIOR_RESEARCH_SOURCE_HEAD}",
            f"SOURCE_BASELINE_HEAD={SOURCE_BASELINE_HEAD}",
            f"FROZEN_SPEC_HASH={FROZEN_SPEC_HASH}",
            f"ANALYTICAL_ARTIFACTS_SHA256={hashes['aggregate_sha256']}",
            f"TASK_COMMIT_SHA={task_commit_sha}",
            f"TESTS={tests}",
            "```",
            "",
            "## Authority and selection provenance",
            "",
            f"The prior task is {PRIOR_TASK_ID}; its committed evidence remains the only feature-selection authority. The prior manifest has {prior['manifest']['feature_count']} PIT-valid features, with {prior['primary_robust_count']} prior ROBUST_CANDIDATE features. This task selected exactly {len(selected)} features before threshold evaluation.",
            "",
            "Selected features and reasons:",
        ]
    )
    lines.extend(
        f"- {row['feature_name']} ({row['category']}): {row['selection_rationale']}"
        for row in selected
    )
    lines.extend(
        [
            "",
            "## Reverse dependency for WS1/WS2 planning",
            "",
            "This task closes only the A1 candidate-specific minimum panel. It does not require complete Historical Topic/System State or WS2 technical publication; the exact bounded dependency is recorded in the summary JSON.",
            json.dumps(reverse_dependencies, sort_keys=True),
        ]
    )
    lines.extend(
        [
            "",
            "## Method boundary",
            "",
            "Thresholds are train-derived Q20/Q30/Q40/Q50/Q60/Q70/Q80 regions, applied unchanged to Validation, Holdout, and Full Sample. The expected direction comes from the prior success-versus-failed evidence. No dense numeric search, return optimization, or exact optimal cutoff was used.",
            "",
            "The primary target is successful A1 versus failed-breakout A1. Retention includes all A1 observations, while success/failure rates use resolved primary cohorts. T+1/T+3/T+5/T+10 are post-selection diagnostic outcomes only.",
            "",
            f"Redundancy used pairwise Spearman rank correlation without labels; {redundancy['high_redundancy_pair_count']} high-redundancy pairs were identified. They were not silently removed or treated as independent confirmation.",
            "",
            "## Results",
            "",
            f"Top single-feature research candidates: {cards['top_single_feature_candidates']}.",
            f"Top two-feature research candidates: {cards['top_two_feature_combination_candidates']}.",
            "",
            "The trade-off artifact reports every tested region's quality delta against unfiltered A1 alongside A1 retention. Any low-sample region is explicitly marked INSUFFICIENT_SAMPLE; no production minimum was introduced.",
            "",
            "## July validation and concentration",
            "",
            "July is reported as the frozen Validation segment separately. A region is not promoted to robust merely because its full-sample aggregate is attractive; temporal direction, July behavior, date concentration, instrument concentration, and TPE/TWO split are all included in the classification.",
            "",
            "## Safety and lifecycle",
            "",
            "This is discrimination research only. Core V0, A1, A2, MA60, baseline formation, labels, WS1/WS2/WS4, NEXT_TASK, production persistence, API/UI/provider/scheduler/deploy surfaces were not changed. No production filter or trading rule was created.",
            "",
            f"reproducible={audit['reproducible']}; threshold_leakage={audit['threshold_leakage']}; outcome_derived_feature_used={audit['outcome_derived_feature_used']}; return_optimization_used={audit['return_optimization_used']}; parameter_search_used={audit['parameter_search_used']}; database_writes={audit['database_writes']}; production_filter_created={audit['production_filter_created']}.",
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
    (output_dir / "ws3-core-v0-a1-quality-filter-threshold-sensitivity-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def run_review(
    database_url: str,
    output_dir: Path,
    *,
    dataset_path: Path = DATASET_PATH_DEFAULT,
    taxonomy_path: Path = TAXONOMY_PATH_DEFAULT,
    prior_dir: Path = PRIOR_REPORT_DIR,
    reproducibility_status: str = "NOT_RUN",
    task_commit_sha: str = "RECORDED_IN_FINAL_HANDOFF",
    tests: str = "RECORDED_IN_FINAL_HANDOFF",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prior = _prior_context(prior_dir)
    selected = select_primary_features(prior)
    manifest = {row["feature_name"]: row for row in build_feature_manifest()}
    for row in selected:
        spec = manifest[row["feature_name"]]
        if not spec["point_in_time_available"] or not spec["allowed_for_primary_analysis"]:
            raise RuntimeError(f"SELECTED_FEATURE_NOT_PIT_VALID:{row['feature_name']}")
        searchable = json.dumps(spec, sort_keys=True).lower()
        if any(
            term in searchable
            for term in (
                "future_return",
                "future_high",
                "future_low",
                "outcome_return",
                "outcome_label",
                "transition_label",
                "rejection_after",
            )
        ):
            raise RuntimeError(f"SELECTED_FEATURE_FORBIDDEN_TERM:{row['feature_name']}")
    reverse_dependencies = _build_reverse_dependencies(selected, manifest)
    observations, collection_quality = collect_observations(database_url, dataset_path)
    a1_rows = observations["groups"]["A1_PRE_BREAKOUT"]
    a2_rows = observations["groups"]["A2_CONFIRMED_BREAKOUT"]
    cohort_rows, cohort_reconciliation = _cohort_reconciliation(
        a1_rows, a2_rows, observations["instrument_data"], taxonomy_path
    )
    if not cohort_reconciliation["pass"]:
        raise RuntimeError(f"COHORT_RECONCILIATION_FAILED:{cohort_reconciliation}")
    feature_rows = _attach_outcomes(
        _build_feature_rows(cohort_rows, a1_rows, observations["instrument_data"]),
        a1_rows,
        cohort_rows,
    )
    redundancy = _build_redundancy(feature_rows, selected)
    single_rows = _threshold_rows(feature_rows, selected)
    _add_stability_and_classification(single_rows, feature_rows)
    combination_rows = _combination_rows(feature_rows, feature_rows, single_rows)
    cards = _candidate_cards(single_rows, combination_rows)
    public_rows = [_public_surface_row(row) for row in single_rows]
    stability_rows = _stability_rows(single_rows)
    tradeoff_rows = _tradeoff_rows(single_rows)
    concentration = {
        "task_id": TASK_ID,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "prior_research_source_head": PRIOR_RESEARCH_SOURCE_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "method": "full-sample date/week/instrument/market concentration on resolved primary cohorts; no outcomes used for threshold selection",
        "regions": [
            {
                "feature_name": row["feature_name"],
                "region_id": row["region_id"],
                "threshold_classification": row["threshold_classification"],
                "concentration": row["concentration"],
                "market_split": row["market_split"],
            }
            for row in single_rows
        ],
    }
    summary = {
        "task_id": TASK_ID,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "prior_research_source_head": PRIOR_RESEARCH_SOURCE_HEAD,
        "source_baseline_head": SOURCE_BASELINE_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "dataset_authority": DATASET_AUTHORITY,
        "prior_task_id": PRIOR_TASK_ID,
        "cohort_reconciliation": cohort_reconciliation,
        "collection_quality": collection_quality,
        "primary_robust_feature_count": prior["primary_robust_count"],
        "primary_selected_feature_count": len(selected),
        "primary_selected_features": selected,
        "reverse_dependencies": reverse_dependencies,
        "quantile_grid": list(QUANTILE_GRID),
        "threshold_grid_source": "TRAIN A1 feature distribution only; labels/outcomes not used",
        "redundancy": redundancy,
        "single_feature_threshold_region_count": len(single_rows),
        "threshold_classification_counts": dict(
            Counter(row["threshold_classification"] for row in single_rows)
        ),
        "threshold_plateau_candidate_count": sum(
            row["THRESHOLD_PLATEAU_PRESENT"] in {"YES", "PARTIAL"} for row in single_rows
        ),
        "combination_rows": _combination_csv_rows(combination_rows),
        "candidate_cards": cards,
        "no_production_filter": True,
    }
    _write_json(output_dir / "ws3-core-v0-a1-threshold-sensitivity-summary.json", summary)
    _write_csv(
        output_dir / "ws3-core-v0-a1-single-feature-threshold-surface.csv",
        list(public_rows[0]),
        public_rows,
    )
    _write_csv(
        output_dir / "ws3-core-v0-a1-threshold-stability-by-segment.csv",
        list(stability_rows[0]),
        stability_rows,
    )
    _write_csv(
        output_dir / "ws3-core-v0-a1-quality-retention-tradeoff.csv",
        list(tradeoff_rows[0]),
        tradeoff_rows,
    )
    _write_json(output_dir / "ws3-core-v0-a1-threshold-concentration-analysis.json", concentration)
    combo_public = _combination_csv_rows(combination_rows)
    _write_csv(
        output_dir / "ws3-core-v0-a1-two-feature-combination-diagnostic.csv",
        list(combo_public[0]),
        combo_public,
    )
    _write_json(
        output_dir / "ws3-core-v0-a1-filter-candidate-cards.json",
        {
            **cards,
            "task_id": TASK_ID,
            "source_canonical_head": SOURCE_CANONICAL_HEAD,
            "frozen_spec_hash": FROZEN_SPEC_HASH,
        },
    )
    hashes = _artifact_hashes(output_dir)
    classification_counts = Counter(row["threshold_classification"] for row in single_rows)
    robust_regions = [
        row for row in single_rows if row["threshold_classification"] == "ROBUST_THRESHOLD_REGION"
    ]
    promising_regions = [
        row
        for row in single_rows
        if row["threshold_classification"] == "PROMISING_THRESHOLD_REGION"
    ]
    defensible_regions = robust_regions + promising_regions
    best = (
        _preferred_region(
            single_rows, cards["top_single_feature_candidates"][0]["feature_or_combination"]
        )
        if cards["top_single_feature_candidates"]
        else None
    )
    best_full = best["full"] if best else {}
    failed_support = (
        "YES"
        if best and (best_full.get("failed_breakout_rate_delta") or 0) <= -QUALITY_DELTA_GUIDE
        else "PARTIAL"
        if best and (best_full.get("failed_breakout_rate_delta") or 0) < 0
        else "NO"
    )
    retention_support = (
        "YES"
        if best and (best_full.get("retention_rate") or 0) >= 0.30
        else "PARTIAL"
        if best
        else "INCONCLUSIVE"
    )
    july_support = (
        "YES"
        if any(row["JULY_VALIDATION_IMPROVEMENT"] == "YES" for row in defensible_regions)
        else "PARTIAL"
        if any(row["JULY_VALIDATION_IMPROVEMENT"] == "PARTIAL" for row in defensible_regions)
        else "NO"
        if defensible_regions
        else "INCONCLUSIVE"
    )
    date_acceptable = (
        "YES"
        if defensible_regions
        and all(row["DATE_CONCENTRATION_RISK"] != "HIGH" for row in defensible_regions)
        else "NO"
        if defensible_regions
        else "INCONCLUSIVE"
    )
    instrument_acceptable = (
        "YES"
        if defensible_regions
        and all(row["INSTRUMENT_CONCENTRATION_RISK"] != "HIGH" for row in defensible_regions)
        else "NO"
        if defensible_regions
        else "INCONCLUSIVE"
    )
    tpe_two = (
        "YES"
        if defensible_regions
        and all(row["TPE_TWO_DIRECTIONALLY_CONSISTENT"] == "YES" for row in defensible_regions)
        else "PARTIAL"
        if defensible_regions
        else "INCONCLUSIVE"
    )
    if robust_regions:
        threshold_supported = "YES"
        confirmatory = (
            "YES_WITH_BOUNDED_LIMITATIONS"
            if july_support != "YES" or date_acceptable != "YES" or instrument_acceptable != "YES"
            else "YES"
        )
    elif promising_regions:
        threshold_supported = "YES_BOUNDED"
        confirmatory = "YES_WITH_BOUNDED_LIMITATIONS"
    else:
        threshold_supported = "NO"
        confirmatory = (
            "NO_OVERFIT_RISK"
            if any(row["THRESHOLD_CLIFF_RISK"] == "HIGH" for row in single_rows)
            else "NO"
        )
    final_fields = {
        "TASK_FINAL_STATUS": "COMPLETE_A1_QUALITY_FILTER_THRESHOLD_SENSITIVITY_RESEARCH",
        "SOURCE_CANONICAL_HEAD": SOURCE_CANONICAL_HEAD,
        "FINAL_CANONICAL_HEAD": "RECORDED_IN_FINAL_HANDOFF",
        "FROZEN_SPEC_HASH": FROZEN_SPEC_HASH,
        "A1_TOTAL_COUNT": 700,
        "A1_SUCCESSFUL_COUNT": 386,
        "A1_FAILED_BREAKOUT_COUNT": 214,
        "PRIMARY_ROBUST_FEATURE_COUNT": prior["primary_robust_count"],
        "PRIMARY_SELECTED_FEATURE_COUNT": len(selected),
        "PRIMARY_SELECTED_FEATURES": ";".join(PRIMARY_SELECTED_FEATURES),
        "HIGH_REDUNDANCY_PAIR_COUNT": redundancy["high_redundancy_pair_count"],
        "SINGLE_FEATURE_THRESHOLD_REGION_COUNT": len(single_rows),
        "ROBUST_THRESHOLD_REGION_COUNT": classification_counts["ROBUST_THRESHOLD_REGION"],
        "PROMISING_THRESHOLD_REGION_COUNT": classification_counts["PROMISING_THRESHOLD_REGION"],
        "NO_DEFENSIBLE_THRESHOLD_REGION_COUNT": classification_counts[
            "NO_DEFENSIBLE_THRESHOLD_REGION"
        ],
        "THRESHOLD_PLATEAU_CANDIDATE_COUNT": sum(
            row["THRESHOLD_PLATEAU_PRESENT"] in {"YES", "PARTIAL"} for row in single_rows
        ),
        "TOP_SINGLE_FEATURE_CANDIDATES": ";".join(
            card["candidate_id"] for card in cards["top_single_feature_candidates"]
        ),
        "TWO_FEATURE_COMBINATIONS_TESTED": sum(row["tested"] for row in combination_rows),
        "TOP_TWO_FEATURE_COMBINATION_CANDIDATES": ";".join(
            card["candidate_id"] for card in cards["top_two_feature_combination_candidates"]
        ),
        "UNFILTERED_A1_SUCCESS_RATE": _baseline_rates(feature_rows)["unfiltered_a1_success_rate"],
        "BEST_DEFENSIBLE_FILTERED_SUCCESS_RATE": best_full.get("filtered_success_rate")
        if best
        else None,
        "BEST_DEFENSIBLE_FAILED_BREAKOUT_RATE": best_full.get("filtered_failed_breakout_rate")
        if best
        else None,
        "BEST_DEFENSIBLE_RETENTION_RATE": best_full.get("retention_rate") if best else None,
        "FAILED_BREAKOUT_REDUCTION_SUPPORTED": failed_support,
        "SUCCESSFUL_A1_RETENTION_SUPPORTED": retention_support,
        "JULY_VALIDATION_IMPROVEMENT_SUPPORTED": july_support,
        "DATE_CONCENTRATION_ACCEPTABLE": date_acceptable,
        "INSTRUMENT_CONCENTRATION_ACCEPTABLE": instrument_acceptable,
        "TPE_TWO_DIRECTIONALLY_CONSISTENT": tpe_two,
        "LOOK_AHEAD_LEAKAGE_DETECTED": "NO",
        "OUTCOME_DERIVED_FEATURE_USED": "NO",
        "THRESHOLD_DENSE_OPTIMIZATION_USED": "NO",
        "RETURN_OPTIMIZATION_USED": "NO",
        "PARAMETER_SEARCH_USED": "NO",
        "CORE_V0_CHANGED": "NO",
        "A1_DEFINITION_CHANGED": "NO",
        "A2_DEFINITION_CHANGED": "NO",
        "MA60_POLICY_CHANGED": "NO",
        "WS1_CHANGED": "NO",
        "WS2_CHANGED": "NO",
        "WS4_CHANGED": "NO",
        "NEXT_TASK_CHANGED": "NO",
        "REPRODUCIBLE": reproducibility_status,
        "A1_QUALITY_FILTER_THRESHOLD_RESEARCH_SUPPORTED": threshold_supported,
        "READY_FOR_A1_FILTER_CONFIRMATORY_VALIDATION": confirmatory,
        "READY_FOR_A1_PRODUCTION_FILTER": "NO",
        "REMAINING_RESEARCH_RISKS": "NO_PRODUCTION_AUTHORITY; CONFIRMATORY_OUT_OF_SAMPLE_VALIDATION_REQUIRED; JULY_ENVIRONMENT_REMAINS_WEAK",
        "FILES_CHANGED": "research module; focused tests; 10 research artifacts",
        "TESTS": tests,
        "TASK_COMMIT_SHA": task_commit_sha,
        "ANALYTICAL_ARTIFACTS_SHA256": hashes["aggregate_sha256"],
    }
    audit = {
        "task_id": TASK_ID,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "prior_research_source_head": PRIOR_RESEARCH_SOURCE_HEAD,
        "source_baseline_head": SOURCE_BASELINE_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "prior_feature_selection_preserved": True,
        "primary_feature_count": len(selected),
        "primary_feature_selection_provenance": selected,
        "reverse_dependencies": reverse_dependencies,
        "pit_validity": True,
        "no_lookahead": True,
        "outcome_derived_feature_used": False,
        "label_leakage": False,
        "threshold_leakage": False,
        "threshold_grid_provenance": "train-only feature distribution Q20/Q30/Q40/Q50/Q60/Q70/Q80; no labels/outcomes",
        "threshold_dense_optimization_used": False,
        "return_optimization_used": False,
        "parameter_search_used": False,
        "frozen_segments_preserved": True,
        "sample_size_integrity": True,
        "duplicate_handling": "one canonical A1 row per instrument/date; cohort reconciliation reused",
        "date_concentration_measured": True,
        "instrument_concentration_measured": True,
        "market_split_measured": True,
        "combination_cap": {
            "maximum_combinations": MAX_COMBINATIONS,
            "maximum_features_per_combination": 2,
            "tested": sum(row["tested"] for row in combination_rows),
        },
        "forward_outcomes_used_for_selection": False,
        "reproducible": reproducibility_status == "PASS",
        "reproducibility": reproducibility_status,
        "analytical_artifact_hashes": hashes,
        "production_filter_created": False,
        "database_writes": False,
        "migration_executed": False,
        "deployment_executed": False,
        "secret_scan": "PENDING_FINAL_VALIDATION",
        "git_diff_check": "PENDING_FINAL_VALIDATION",
    }
    _write_json(output_dir / "ws3-core-v0-a1-threshold-quality-audit.json", audit)
    _write_json(
        output_dir / "ws3-core-v0-a1-filter-confirmatory-readiness.json",
        {
            "task_id": TASK_ID,
            **final_fields,
            "candidate_cards": cards,
            "remaining_research_risks": final_fields["REMAINING_RESEARCH_RISKS"],
        },
    )
    _report(
        output_dir,
        final_fields,
        prior,
        selected,
        redundancy,
        cards,
        reverse_dependencies,
        audit,
        hashes,
        task_commit_sha,
        tests,
    )
    return {
        "final_fields": final_fields,
        "summary": summary,
        "audit": audit,
        "single_rows": single_rows,
        "combination_rows": combination_rows,
        "cards": cards,
        "hashes": hashes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dataset-path", type=Path, default=DATASET_PATH_DEFAULT)
    parser.add_argument("--taxonomy-path", type=Path, default=TAXONOMY_PATH_DEFAULT)
    parser.add_argument("--prior-dir", type=Path, default=PRIOR_REPORT_DIR)
    parser.add_argument("--reproducibility-status", default="NOT_RUN")
    parser.add_argument("--task-commit-sha", default="RECORDED_IN_FINAL_HANDOFF")
    parser.add_argument("--tests", default="RECORDED_IN_FINAL_HANDOFF")
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or TOPICPILOT_DATABASE_URL is required")
    result = run_review(
        args.database_url,
        args.output_dir,
        dataset_path=args.dataset_path,
        taxonomy_path=args.taxonomy_path,
        prior_dir=args.prior_dir,
        reproducibility_status=args.reproducibility_status,
        task_commit_sha=args.task_commit_sha,
        tests=args.tests,
    )
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                **{
                    key: result["final_fields"][key]
                    for key in (
                        "ROBUST_THRESHOLD_REGION_COUNT",
                        "PROMISING_THRESHOLD_REGION_COUNT",
                        "READY_FOR_A1_FILTER_CONFIRMATORY_VALIDATION",
                        "READY_FOR_A1_PRODUCTION_FILTER",
                    )
                },
            },
            default=str,
        )
    )


if __name__ == "__main__":
    main()


__all__ = ["PRIMARY_SELECTED_FEATURES", "TASK_ID", "run_review", "select_primary_features"]
