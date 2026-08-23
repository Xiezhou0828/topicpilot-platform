"""Extract a bounded human review pack from canonical WS3 discovery artifacts.

This module intentionally performs no research replay.  It reads the existing
CSV/JSON outputs, joins only the rows needed for the review pack, and writes
human-readable evidence with explicit bounded limitations.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "TASK-WS3-SUCCESSFUL-SWING-HUMAN-ASSISTED-OWNER-REVIEW-PACK-EXTRACTION-20260821"
SOURCE_TASK_ID = "TASK-WS3-SUCCESSFUL-SWING-OUTCOME-MINING-AND-LEADING-EVIDENCE-DISCOVERY-20260821"
SOURCE_DIR_NAME = "reports/TASK-WS3-SUCCESSFUL-SWING-OUTCOME-MINING-AND-LEADING-EVIDENCE-DISCOVERY-20260821"
SOURCE_CLOSURE = "docs/reports/TASK-WS3-SUCCESSFUL-SWING-OUTCOME-MINING-AND-LEADING-EVIDENCE-DISCOVERY-20260821/formal-closure-report.md"
OUTPUT_DIR_NAME = "reports/" + TASK_ID
DOC_DIR_NAME = "docs/reports/" + TASK_ID
UNAVAILABLE = "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS"
RANKING_NOTE = (
    "Explicit rank was not persisted in the source artifact. This stable ordering "
    "reconstructs a review order from existing classification, absolute standardized "
    "mean difference, sample count, overlap, relative day, and source-key tie-breakers; "
    "no new search, fit, threshold, or feature was executed."
)

FAMILIES = [
    "TREND_STRUCTURE",
    "VOLATILITY_COMPRESSION",
    "VOLUME_PARTICIPATION",
    "MOMENTUM",
    "A_STATE_CONTEXT",
    "RELATIVE_STRENGTH",
]
FAMILY_LABELS = {"A_STATE_CONTEXT": "A_STATE", **{family: family for family in FAMILIES if family != "A_STATE_CONTEXT"}}
SNAPSHOT_DAYS = [-20, -10, -5, -3, -1, 0]
STRATA_ORDER = ["T5_GE_3", "T5_GE_5", "T5_GE_10", "T10_GE_3", "T10_GE_5", "T10_GE_10"]

# These definitions mirror the already-published source implementation. They
# are displayed as semantics only; this task never recomputes their values.
FEATURE_DEFINITIONS = {
    "close_vs_ma5": "(Close - MA5) / MA5; signed price distance from the five-session moving average.",
    "close_vs_ma10": "(Close - MA10) / MA10; signed price distance from the ten-session moving average.",
    "close_vs_ma20": "(Close - MA20) / MA20; signed price distance from the 20-session moving average.",
    "close_vs_ma60": "(Close - MA60) / MA60; signed price distance from the 60-session moving average.",
    "distance_to_ma20": "(Close - MA20) / MA20; the same 20-session moving-average distance under the frozen V0 semantics.",
    "ma5_slope_5": "(MA5[T] - MA5[T-5]) / MA5[T-5]; five-session slope of the five-session average.",
    "ma20_slope_5": "(MA20[T] - MA20[T-5]) / MA20[T-5]; five-session slope of the 20-session average.",
    "ma60_slope_5": "(MA60[T] - MA60[T-5]) / MA60[T-5]; five-session slope of the 60-session average.",
    "ma_alignment_bullish": "Boolean state Close > MA5 > MA20 > MA60; a strict bullish moving-average ordering.",
    "ma_alignment_bearish": "Boolean state Close < MA5 < MA20 < MA60; a strict bearish moving-average ordering.",
    "RAW_CLOSE_RETURN_5D": "Close[T] / Close[T-5] - 1; raw five-session price return.",
    "RAW_CLOSE_RETURN_20D": "Close[T] / Close[T-20] - 1; raw 20-session price return.",
    "RSI14": "14-session RSI computed from canonical daily close changes.",
    "MACD_12_26_9": "12/26-session exponential-average difference under the frozen technical V0 semantics.",
    "MACD_SIGNAL_12_26_9": "Nine-session signal average of the frozen MACD series.",
    "MACD_HISTOGRAM_12_26_9": "MACD minus its nine-session signal average.",
    "rsi_change_5": "RSI14[T] - RSI14[T-5]; five-session change in RSI.",
    "macd_hist_change_5": "MACD histogram[T] - histogram[T-5]; five-session change in MACD histogram.",
    "VOLUME_MA5": "Five-session moving average of daily volume.",
    "VOLUME_MA20": "20-session moving average of daily volume.",
    "VOLUME_RATIO_20": "Current volume / 20-session average volume.",
    "volume_ratio_5_to_20": "VOLUME_MA5 / VOLUME_MA20; recent average participation relative to the 20-session baseline.",
    "volume_expansion_state": "Boolean state VOLUME_RATIO_20 > 1; current participation above its 20-session baseline.",
    "volume_contraction_state": "Boolean state VOLUME_RATIO_20 < 1; current participation below its 20-session baseline.",
    "true_range_pct": "max(high-low, abs(high-prevClose), abs(low-prevClose)) / prevClose; one-session range relative to prior close.",
    "rolling_range_pct_5": "(rolling five-session high - rolling five-session low) / current close.",
    "rolling_range_pct_20": "(rolling 20-session high - rolling 20-session low) / current close.",
    "range_compression_5_to_20": "rolling_range_pct_5 / rolling_range_pct_20; short-range width relative to the 20-session range.",
    "realized_vol_5": "Population standard deviation of daily close returns over the fixed five-session window.",
    "realized_vol_20": "Population standard deviation of daily close returns over the fixed 20-session window.",
    "volatility_contraction_5_to_20": "realized_vol_5 / realized_vol_20; short-horizon volatility relative to the 20-session baseline.",
    "benchmark_relative_return_5D": "Five-session return relative to a canonical benchmark; unavailable because no canonical benchmark was present.",
    "benchmark_relative_return_20D": "20-session return relative to a canonical benchmark; unavailable because no canonical benchmark was present.",
    "a1_preceded_20": "Frozen P1E A1 context flag observed within the preceding 20 accepted sessions including D0.",
    "a2_preceded_20": "Frozen P1E A2 context flag observed within the preceding 20 accepted sessions including D0.",
    "a1_to_a2_preceded_20": "Frozen A1-to-A2 context flag observed within the preceding 20 accepted sessions including D0.",
    "a2_without_prior_a1_20": "Frozen A2-without-prior-A1 context flag observed within the preceding 20 accepted sessions including D0.",
    "a_state_bucket": "Frozen categorical A1/A2 context bucket; descriptive context only.",
}

FOCUS_FEATURES = {
    "TREND_STRUCTURE": ["close_vs_ma20", "ma20_slope_5", "ma_alignment_bullish", "ma_alignment_bearish"],
    "VOLATILITY_COMPRESSION": ["rolling_range_pct_5", "rolling_range_pct_20", "range_compression_5_to_20", "realized_vol_5", "realized_vol_20", "volatility_contraction_5_to_20"],
    "VOLUME_PARTICIPATION": ["VOLUME_RATIO_20", "volume_ratio_5_to_20", "volume_expansion_state", "volume_contraction_state"],
    "MOMENTUM": ["RAW_CLOSE_RETURN_5D", "RAW_CLOSE_RETURN_20D", "RSI14", "MACD_HISTOGRAM_12_26_9", "rsi_change_5", "macd_hist_change_5"],
    "A_STATE_CONTEXT": ["a1_preceded_20", "a2_preceded_20", "a1_to_a2_preceded_20", "a2_without_prior_a1_20", "a_state_bucket"],
    "RELATIVE_STRENGTH": ["benchmark_relative_return_5D", "benchmark_relative_return_20D"],
}

EXPECTED_SOURCE_ARTIFACTS = [
    "ws3-successful-swing-a-state-relationship.csv",
    "ws3-successful-swing-concentration-outlier-audit.json",
    "ws3-successful-swing-distinct-episode-panel.csv",
    "ws3-successful-swing-feature-manifest.json",
    "ws3-successful-swing-lead-time-analysis.csv",
    "ws3-successful-swing-lookahead-hindsight-audit.json",
    "ws3-successful-swing-market-temporal-stability.csv",
    "ws3-successful-swing-matched-control-panel.csv",
    "ws3-successful-swing-next-research-readiness.json",
    "ws3-successful-swing-outcome-protocol-freeze.json",
    "ws3-successful-swing-outcome-strata-summary.csv",
    "ws3-successful-swing-outcome-strength-gradient.csv",
    "ws3-successful-swing-pre-event-feature-panel.csv",
    "ws3-successful-swing-raw-anchor-panel.csv",
    "ws3-successful-swing-reference-case-cards.json",
    "ws3-successful-swing-reproducibility-manifest.json",
    "ws3-successful-swing-run-summary.json",
    "formal-closure-report.md",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def num(value: Any) -> float | None:
    if value is None or value == "" or value == UNAVAILABLE:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: Any, digits: int = 4) -> str:
    if value is None or value == "":
        return UNAVAILABLE
    n = num(value)
    if n is None:
        return str(value)
    return f"{n:.{digits}g}"


def fmt_pct(value: Any) -> str:
    n = num(value)
    return UNAVAILABLE if n is None else f"{n * 100:.2f}%"


def fmt_bool(value: Any) -> str:
    if value is None or value == "":
        return UNAVAILABLE
    return str(value).upper()


def safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def source_inventory(src: Path) -> list[dict[str, Any]]:
    rows = []
    for name in EXPECTED_SOURCE_ARTIFACTS:
        path = src / name if name != "formal-closure-report.md" else Path(__file__).resolve().parents[1] / SOURCE_CLOSURE
        exists = path.is_file() and path.stat().st_size > 0
        rows.append({"artifact": name, "status": "FOUND" if exists else "MISSING", "size_bytes": path.stat().st_size if exists else "", "path": str(path).replace("\\", "/")})
    return rows


def source_inventory_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# WS3 owner review source artifact inventory",
        "",
        "This inventory is read-only and records the source files consumed from the completed Successful Swing discovery task.",
        "",
        "| Artifact | Status | Size (bytes) |",
        "|---|---:|---:|",
    ]
    for row in rows:
        lines.append(f"| `{row['artifact']}` | {row['status']} | {row.get('size_bytes') or UNAVAILABLE} |")
    lines += ["", "`MISSING` items were not silently reconstructed. The source closure and all 17 expected report artifacts were present at extraction time."]
    return "\n".join(lines)


def ranking_key(row: dict[str, str]) -> tuple[Any, ...]:
    return (
        -(abs(num(row.get("standardized_mean_difference")) or 0.0)),
        -(int(num(row.get("n_success")) or 0)),
        num(row.get("distribution_overlap")) if num(row.get("distribution_overlap")) is not None else 1.0,
        int(num(row.get("relative_day")) or 0),
        row.get("feature_family", ""),
        row.get("feature_id", ""),
        row.get("stratum", ""),
    )


def gradient_map(rows: list[dict[str, str]]) -> dict[tuple[str, str, int], list[dict[str, str]]]:
    grouped: dict[tuple[str, str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (row.get("feature_family", ""), row.get("feature_id", ""), int(num(row.get("relative_day")) or 0))
        grouped[key].append(row)
    return grouped


def gradient_summary(gradients: dict[tuple[str, str, int], list[dict[str, str]]], row: dict[str, str]) -> str:
    key = (row.get("feature_family", ""), row.get("feature_id", ""), int(num(row.get("relative_day")) or 0))
    parts = []
    for item in sorted(gradients.get(key, []), key=lambda value: int(num(value.get("horizon")) or 0)):
        parts.append(f"h{item.get('horizon')}:T3={fmt(item.get('t3_median'))},T5={fmt(item.get('t5_median'))},T10={fmt(item.get('t10_median'))},mono={item.get('monotonicity', UNAVAILABLE)}")
    return "; ".join(parts) if parts else UNAVAILABLE


def interpretation(row: dict[str, str]) -> str:
    feature = row.get("feature_id", "")
    definition = FEATURE_DEFINITIONS.get(feature, UNAVAILABLE)
    direction = "higher" if (num(row.get("mean_difference")) or 0.0) >= 0 else "lower"
    day = int(num(row.get("relative_day")) or 0)
    day_label = "D0" if day == 0 else f"D{day}"
    return f"{definition} Existing discovery evidence shows the successful group had a {direction} mean than matched controls at {day_label}; this is descriptive and is not a trading rule."


def why_promising(row: dict[str, str]) -> str:
    reason = row.get("classification_reason") or UNAVAILABLE
    overlap = num(row.get("distribution_overlap"))
    market = num(row.get("market_direction_consistency"))
    temporal = num(row.get("temporal_direction_consistency"))
    notes = [f"existing classification reason: {reason}"]
    if overlap is not None and overlap >= 0.9:
        notes.append("higher distribution overlap")
    if market is not None and market < 1:
        notes.append("market consistency below the robust boundary")
    if temporal is not None and temporal < 1:
        notes.append("temporal consistency below the robust boundary")
    if abs(num(row.get("standardized_mean_difference")) or 0.0) < 0.2:
        notes.append("weaker standardized effect size")
    notes.append("confirmatory research remained out of scope")
    return "; ".join(notes)


def signal_records(rows: list[dict[str, str]], gradients: dict[tuple[str, str, int], list[dict[str, str]]], lead: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=ranking_key)
    output = []
    for rank, row in enumerate(ordered, 1):
        family = row.get("feature_family", "")
        feature = row.get("feature_id", "")
        rel = int(num(row.get("relative_day")) or 0)
        output.append({
            "rank": rank,
            "feature_family": family,
            "feature_family_label": FAMILY_LABELS.get(family, family),
            "feature_id": feature,
            "feature_definition": FEATURE_DEFINITIONS.get(feature, UNAVAILABLE),
            "relative_day": rel,
            "relative_day_label": "D0" if rel == 0 else f"D{rel}",
            "outcome_stratum": row.get("stratum", UNAVAILABLE),
            "n_success": row.get("n_success", UNAVAILABLE),
            "n_control": row.get("n_control", UNAVAILABLE),
            "successful_median": row.get("success_median", UNAVAILABLE),
            "control_median": row.get("control_median", UNAVAILABLE),
            "absolute_median_difference": abs(num(row.get("median_difference")) or 0.0),
            "median_difference": row.get("median_difference", UNAVAILABLE),
            "mean_difference": row.get("mean_difference", UNAVAILABLE),
            "standardized_mean_difference": row.get("standardized_mean_difference", UNAVAILABLE),
            "distribution_overlap": row.get("distribution_overlap", UNAVAILABLE),
            "market_stability_tpe_two": row.get("market_direction_consistency", UNAVAILABLE),
            "market_stability_detail": "TPE/TWO pooled direction-consistency value from existing artifact; per-market breakdown is " + UNAVAILABLE,
            "temporal_stability": row.get("temporal_direction_consistency", UNAVAILABLE),
            "outlier_dependence": row.get("outlier_dependence", UNAVAILABLE),
            "outcome_strength_gradient": gradient_summary(gradients, row),
            "earliest_useful_lead_time": lead.get(family, {}).get("earliest_useful_label", UNAVAILABLE),
            "classification": row.get("classification", UNAVAILABLE),
            "classification_reason": row.get("classification_reason", UNAVAILABLE),
            "human_interpretation": interpretation(row),
            "why_promising_not_robust": why_promising(row) if row.get("classification") == "PROMISING_DISCOVERY_SIGNAL" else "",
            "ranking_note": RANKING_NOTE,
        })
    return output


SIGNAL_FIELDS = [
    "rank", "feature_family", "feature_family_label", "feature_id", "feature_definition", "relative_day", "relative_day_label", "outcome_stratum", "n_success", "n_control", "successful_median", "control_median", "absolute_median_difference", "median_difference", "mean_difference", "standardized_mean_difference", "distribution_overlap", "market_stability_tpe_two", "market_stability_detail", "temporal_stability", "outlier_dependence", "outcome_strength_gradient", "earliest_useful_lead_time", "classification", "classification_reason", "human_interpretation", "why_promising_not_robust", "ranking_note",
]


def signal_markdown(title: str, rows: list[dict[str, Any]], include_why: bool = False) -> str:
    lines = [f"# {title}", "", "All values below are direct extracts or deterministic joins of the completed discovery artifacts. They are not accepted strategy rules.", "", f"> {RANKING_NOTE}", "", "| Rank | Family | Feature | Day | Stratum | nS/nC | Success median | Control median | SMD | Overlap | Market | Temporal | Classification |", "|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for row in rows:
        lines.append("| " + " | ".join([
            str(row["rank"]), markdown_cell(row["feature_family_label"]), markdown_cell(row["feature_id"]), str(row["relative_day_label"]), markdown_cell(row["outcome_stratum"]), f"{row['n_success']}/{row['n_control']}", fmt(row["successful_median"]), fmt(row["control_median"]), fmt(row["standardized_mean_difference"]), fmt(row["distribution_overlap"]), fmt(row["market_stability_tpe_two"]), fmt(row["temporal_stability"]), markdown_cell(row["classification"])]) + " |")
    lines += ["", "## Definitions and interpretation", ""]
    for row in rows:
        lines += [f"### {row['rank']}. `{row['feature_family']}/{row['feature_id']}` at {row['relative_day_label']} — `{row['outcome_stratum']}`", "", f"- Definition: {row['feature_definition']}", f"- Median difference (success - control): `{fmt(row['median_difference'])}`; mean difference: `{fmt(row['mean_difference'])}`; outlier dependence: `{fmt(row['outlier_dependence'])}`.", f"- Stability: market `{fmt(row['market_stability_tpe_two'])}` (TPE/TWO pooled); temporal `{fmt(row['temporal_stability'])}`; detailed per-segment breakdown: `{UNAVAILABLE}`.", f"- Outcome-strength gradient: `{row['outcome_strength_gradient']}`.", f"- Earliest useful family lead time: `{row['earliest_useful_lead_time']}`.", f"- Interpretation: {row['human_interpretation']}"]
        if include_why:
            lines.append(f"- Why promising rather than robust: {row['why_promising_not_robust']}")
        lines.append("")
    lines += ["This pack preserves discovery classifications only. It does not promote any observation into a rule, score, recommendation, or production feature."]
    return "\n".join(lines)


def load_raw_selected(path: Path, anchor_ids: set[str]) -> dict[str, dict[str, str]]:
    found: dict[str, dict[str, str]] = {}
    if not anchor_ids:
        return found
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            aid = row.get("anchor_id", "")
            if aid in anchor_ids:
                found[aid] = row
                if len(found) == len(anchor_ids):
                    break
    return found


def load_panel_selected(path: Path, anchor_ids: set[str]) -> dict[str, dict[int, dict[str, str]]]:
    selected: dict[str, dict[int, dict[str, str]]] = defaultdict(dict)
    priority = {stratum: index for index, stratum in enumerate(STRATA_ORDER)}
    if not anchor_ids:
        return selected
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            event_id = row.get("event_id", "")
            aid = event_id.rsplit(":", 1)[-1]
            if row.get("event_type") != "SUCCESSFUL_SWING" or aid not in anchor_ids:
                continue
            rel = int(num(row.get("relative_day")) or 0)
            current = selected[aid].get(rel)
            if current is None or priority.get(row.get("stratum", ""), 99) < priority.get(current.get("stratum", ""), 99):
                selected[aid][rel] = row
    return selected


def snapshot_values(panel: dict[str, dict[int, dict[str, str]]], anchor_id: str, rel: int, families: Iterable[str] | None = None) -> dict[str, Any]:
    row = panel.get(anchor_id, {}).get(rel)
    if row is None:
        return {"relative_day": rel, "status": UNAVAILABLE}
    families = list(families or FAMILIES)
    fields: dict[str, Any] = {}
    for family in families:
        for feature in FOCUS_FEATURES[family]:
            fields[feature] = row.get("feature_" + feature, UNAVAILABLE) or UNAVAILABLE
    fields.update({"relative_day": rel, "status": row.get("feature_status_summary", UNAVAILABLE), "pit_status": row.get("pit_status", UNAVAILABLE), "stratum": row.get("stratum", UNAVAILABLE)})
    return fields


def robust_observations_at(panel: dict[str, dict[int, dict[str, str]]], anchor_id: str, rel: int, robust_rows: list[dict[str, Any]]) -> list[str]:
    row = panel.get(anchor_id, {}).get(rel)
    if row is None:
        return []
    found = []
    for signal in robust_rows:
        if int(signal["relative_day"]) != rel:
            continue
        key = "feature_" + str(signal["feature_id"])
        if row.get(key, "") not in ("", None):
            found.append(f"{signal['feature_family']}/{signal['feature_id']}/{signal['outcome_stratum']}")
    return found


def raw_outcome(raw: dict[str, str], horizon: int) -> dict[str, Any]:
    prefix = f"T{horizon}_"
    return {
        "forward_return": raw.get(prefix + "forward_close_return", UNAVAILABLE),
        "MFE": raw.get(prefix + "mfe", UNAVAILABLE),
        "MAE": raw.get(prefix + "mae", UNAVAILABLE),
        "time_to_3pct": raw.get(prefix + "time_to_3pct", UNAVAILABLE),
        "time_to_5pct": raw.get(prefix + "time_to_5pct", UNAVAILABLE),
        "time_to_10pct": raw.get(prefix + "time_to_10pct", UNAVAILABLE),
        "max_close_drawdown": raw.get(prefix + "max_close_drawdown", UNAVAILABLE),
        "one_day_spike_ge_3pct": raw.get(prefix + "one_day_spike_ge_3pct", UNAVAILABLE),
        "sustained_expansion_ge_3pct": raw.get(prefix + "sustained_expansion_ge_3pct", UNAVAILABLE),
    }


def state_from_raw(raw: dict[str, str]) -> dict[str, Any]:
    return {key.removeprefix("a_state_"): raw.get(key, UNAVAILABLE) for key in ["a_state_a1_preceded_20", "a_state_a2_preceded_20", "a_state_a1_to_a2_preceded_20", "a_state_a2_without_prior_a1_20", "a_state_a_state_bucket", "a_state_a1_latest_date", "a_state_a2_latest_date", "a_state_a1_a2_lookback_sessions", "a_state_a1_state_at_d0", "a_state_a2_state_at_d0"]}


def satisfied_strata(raw: dict[str, str]) -> list[str]:
    return [stratum for stratum in STRATA_ORDER if str(raw.get(stratum, "")).lower() == "true"]


def path_description(raw: dict[str, str]) -> str:
    if not raw:
        return UNAVAILABLE
    items = []
    for horizon in (5, 10):
        outcome = raw_outcome(raw, horizon)
        items.append(f"T{horizon}: forward={fmt_pct(outcome['forward_return'])}, MFE={fmt_pct(outcome['MFE'])}, MAE={fmt_pct(outcome['MAE'])}, close-persistence>=3%={fmt(raw.get(f'T{horizon}_close_persistence_ge_3pct'))}, one-day-spike={fmt_bool(outcome['one_day_spike_ge_3pct'])}, sustained-expansion={fmt_bool(outcome['sustained_expansion_ge_3pct'])}")
    return "; ".join(items)


def reference_payload(reference: dict[str, Any], raw: dict[str, dict[str, str]], panel: dict[str, dict[int, dict[str, str]]], robust_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for case in reference.get("cases", []):
        events = []
        for event in case.get("qualifying_events", []):
            aid = event.get("anchor_id", "")
            anchor = raw.get(aid, {})
            snapshots = []
            for rel in SNAPSHOT_DAYS:
                snapshot = snapshot_values(panel, aid, rel)
                snapshot["robust_signal_observations"] = robust_observations_at(panel, aid, rel, robust_rows)
                snapshots.append(snapshot)
            events.append({
                "anchor_id": aid,
                "anchor_date": event.get("anchor_date", UNAVAILABLE),
                "instrument_id": anchor.get("instrument_id", UNAVAILABLE),
                "stock_code": case.get("stock_code", anchor.get("stock_code", UNAVAILABLE)),
                "stock_name": anchor.get("name", UNAVAILABLE),
                "satisfied_outcome_strata": satisfied_strata(anchor),
                "T5": raw_outcome(anchor, 5) if anchor else {key: UNAVAILABLE for key in raw_outcome({}, 5)},
                "T10": raw_outcome(anchor, 10) if anchor else {key: UNAVAILABLE for key in raw_outcome({}, 10)},
                "a_state": state_from_raw(anchor) if anchor else event.get("a_state", UNAVAILABLE),
                "path_description": path_description(anchor),
                "source_lineage": anchor.get("source_lineage", event.get("source_lineage", UNAVAILABLE)),
                "source_pit_status": anchor.get("pit_status", UNAVAILABLE),
                "snapshots": snapshots,
                "robust_signal_observation_note": "Observed means the existing PIT feature row contains a value at that day; no threshold or rule was inferred.",
            })
        result.append({
            "stock_code": case.get("stock_code", UNAVAILABLE),
            "stock_name": (raw.get(events[0]["anchor_id"], {}) if events else {}).get("name", UNAVAILABLE),
            "requested_range": case.get("requested_range", [UNAVAILABLE, UNAVAILABLE]),
            "available_range": case.get("available_range", [UNAVAILABLE, UNAVAILABLE]),
            "objectively_reconstructed": case.get("objectively_reconstructed", UNAVAILABLE),
            "source_end_cap_applied": case.get("source_end_cap_applied", UNAVAILABLE),
            "objective_protocol": case.get("objective_protocol", UNAVAILABLE),
            "qualifying_event_count": case.get("qualifying_event_count", len(events)),
            "events": events,
        })
    return result


def reference_markdown(cases: list[dict[str, Any]]) -> str:
    lines = ["# WS3 Owner reference case cards", "", "These seven cards are reconstructed from the existing owner reference artifact and canonical raw anchor / PIT feature panels. Missing fields remain explicit. The source range ends at 2026-08-13 where the prior artifact applied its end cap.", ""]
    for case in cases:
        lines += [f"## Stock {case['stock_code']} — {case.get('stock_name') or UNAVAILABLE}", "", f"- Owner requested range: `{case['requested_range'][0]} .. {case['requested_range'][1]}`", f"- Existing available range: `{case['available_range'][0]} .. {case['available_range'][1]}`", f"- Objective protocol: `{case['objective_protocol']}`; objectively reconstructed: `{case['objectively_reconstructed']}`", f"- Qualifying anchors: `{case['qualifying_event_count']}`", "", "| Anchor date | Anchor ID | Strata | T+5 | T+10 | MFE T5 | MAE T5 | T+5 time to 3/5/10% | T+10 time to 3/5/10% | A-state |", "|---|---|---|---:|---:|---:|---:|---|---|---|"]
        for event in case["events"]:
            t5, t10 = event["T5"], event["T10"]
            state = event["a_state"].get("a_state_bucket", event["a_state"]) if isinstance(event["a_state"], dict) else event["a_state"]
            lines.append("| " + " | ".join([
                markdown_cell(event["anchor_date"]), f"`{event['anchor_id'][:12]}…`", markdown_cell(", ".join(event["satisfied_outcome_strata"]) or UNAVAILABLE), fmt_pct(t5["forward_return"]), fmt_pct(t10["forward_return"]), fmt_pct(t5["MFE"]), fmt_pct(t5["MAE"]), f"{fmt(t5['time_to_3pct'])}/{fmt(t5['time_to_5pct'])}/{fmt(t5['time_to_10pct'])}", f"{fmt(t10['time_to_3pct'])}/{fmt(t10['time_to_5pct'])}/{fmt(t10['time_to_10pct'])}", markdown_cell(state)]) + " |")
        lines += ["", "### PIT feature snapshots", "", "Robust signal observations below indicate only that the existing PIT row contained the corresponding feature value; they do not indicate an accepted threshold.", ""]
        for event in case["events"]:
            lines += [f"#### {event['anchor_date']} — `{event['anchor_id'][:12]}…`", "", f"Path descriptors: {event['path_description']}", "", "| Day | Trend | Volatility | Volume | Momentum | A-state | Robust observations |", "|---:|---|---|---|---|---|---|"]
            for snap in event["snapshots"]:
                if snap.get("status") == UNAVAILABLE:
                    lines.append(f"| D{snap['relative_day']} | {UNAVAILABLE} | {UNAVAILABLE} | {UNAVAILABLE} | {UNAVAILABLE} | {UNAVAILABLE} | {UNAVAILABLE} |")
                    continue
                def value(name: str) -> str:
                    return fmt(snap.get(name))
                lines.append("| " + " | ".join([
                    "D0" if snap["relative_day"] == 0 else f"D{snap['relative_day']}",
                    f"close/MA20={value('close_vs_ma20')}; MA20 slope={value('ma20_slope_5')}; align B/Bear={value('ma_alignment_bullish')}/{value('ma_alignment_bearish')}",
                    f"range20={value('rolling_range_pct_20')}; comp={value('range_compression_5_to_20')}; vol contraction={value('volatility_contraction_5_to_20')}",
                    f"ratio20={value('VOLUME_RATIO_20')}; 5/20={value('volume_ratio_5_to_20')}; contraction={value('volume_contraction_state')}",
                    f"raw5={value('RAW_CLOSE_RETURN_5D')}; RSI={value('RSI14')}; MACD hist={value('MACD_HISTOGRAM_12_26_9')}",
                    markdown_cell(snap.get("a_state_bucket", UNAVAILABLE)),
                    markdown_cell(", ".join(snap.get("robust_signal_observations", [])) or "none observed"),
                ]) + " |")
            lines.append("")
    return "\n".join(lines)


def sample_evenly(rows: list[dict[str, str]], count: int) -> list[dict[str, str]]:
    if len(rows) <= count:
        return rows[:]
    indices = [round(index * (len(rows) - 1) / (count - 1)) for index in range(count)] if count > 1 else [0]
    return [rows[index] for index in indices]


def choose_pairs(control_rows: list[dict[str, str]]) -> list[tuple[str, dict[str, str]]]:
    ordered = sorted(control_rows, key=lambda row: (row.get("successful_anchor_date", ""), row.get("successful_anchor_id", ""), row.get("control_anchor_id", "")))
    definitions = [
        ("T5_GE_10", lambda row: row.get("stratum") == "T5_GE_10"),
        ("T10_GE_10", lambda row: row.get("stratum") == "T10_GE_10"),
        ("MODERATE_5", lambda row: row.get("stratum") in {"T5_GE_5", "T10_GE_5"}),
        ("WEAKER_3", lambda row: row.get("stratum") in {"T5_GE_3", "T10_GE_3"}),
    ]
    selected: list[tuple[str, dict[str, str]]] = []
    used: set[str] = set()
    for label, predicate in definitions:
        candidates = [row for row in ordered if predicate(row) and row.get("successful_anchor_id") not in used]
        for row in sample_evenly(candidates, 5):
            aid = row.get("successful_anchor_id", "")
            if aid in used:
                continue
            selected.append((label, row))
            used.add(aid)
    return selected


def pair_snapshot_text(panel: dict[str, dict[int, dict[str, str]]], aid: str, rel: int) -> str:
    snap = snapshot_values(panel, aid, rel)
    if snap.get("status") == UNAVAILABLE:
        return UNAVAILABLE
    return safe_json({
        "trend_close_vs_ma20": snap.get("close_vs_ma20", UNAVAILABLE),
        "trend_ma20_slope_5": snap.get("ma20_slope_5", UNAVAILABLE),
        "trend_alignment_bullish": snap.get("ma_alignment_bullish", UNAVAILABLE),
        "trend_alignment_bearish": snap.get("ma_alignment_bearish", UNAVAILABLE),
        "compression_range20": snap.get("rolling_range_pct_20", UNAVAILABLE),
        "compression_ratio": snap.get("range_compression_5_to_20", UNAVAILABLE),
        "compression_volatility_contraction": snap.get("volatility_contraction_5_to_20", UNAVAILABLE),
        "volume_ratio20": snap.get("VOLUME_RATIO_20", UNAVAILABLE),
        "volume_contraction": snap.get("volume_contraction_state", UNAVAILABLE),
        "momentum_raw5": snap.get("RAW_CLOSE_RETURN_5D", UNAVAILABLE),
        "momentum_rsi": snap.get("RSI14", UNAVAILABLE),
        "momentum_macd_hist": snap.get("MACD_HISTOGRAM_12_26_9", UNAVAILABLE),
        "a_state": snap.get("a_state_bucket", UNAVAILABLE),
    })


def pair_payload(chosen: list[tuple[str, dict[str, str]]], raw: dict[str, dict[str, str]], panel: dict[str, dict[int, dict[str, str]]], robust_rows: list[dict[str, Any]], promising_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for index, (sample_bucket, pair) in enumerate(chosen, 1):
        success = raw.get(pair.get("successful_anchor_id", ""), {})
        control = raw.get(pair.get("control_anchor_id", ""), {})
        snapshots = {f"D{rel}" if rel == 0 else f"D{rel}": {"success": pair_snapshot_text(panel, pair.get("successful_anchor_id", ""), rel), "control": UNAVAILABLE} for rel in SNAPSHOT_DAYS}
        robust_presence = {("D0" if rel == 0 else f"D{rel}"): robust_observations_at(panel, pair.get("successful_anchor_id", ""), rel, robust_rows) for rel in SNAPSHOT_DAYS}
        promising_presence = {("D0" if rel == 0 else f"D{rel}"): robust_observations_at(panel, pair.get("successful_anchor_id", ""), rel, promising_rows) for rel in SNAPSHOT_DAYS}
        output.append({
            "pair_index": index,
            "sample_bucket": sample_bucket,
            "stratum": pair.get("stratum", UNAVAILABLE),
            "successful_anchor_id": pair.get("successful_anchor_id", UNAVAILABLE),
            "successful_episode_id": pair.get("successful_episode_id", UNAVAILABLE),
            "successful_instrument_id": pair.get("successful_instrument_id", success.get("instrument_id", UNAVAILABLE)),
            "successful_stock_code": success.get("stock_code", UNAVAILABLE),
            "successful_date": pair.get("successful_anchor_date", success.get("anchor_date", UNAVAILABLE)),
            "successful_market": success.get("market", UNAVAILABLE),
            "successful_T5": pair.get("successful_outcome_T5", UNAVAILABLE),
            "successful_T10": pair.get("successful_outcome_T10", UNAVAILABLE),
            "successful_MFE_T5": success.get("T5_mfe", UNAVAILABLE),
            "successful_MAE_T5": success.get("T5_mae", UNAVAILABLE),
            "control_anchor_id": pair.get("control_anchor_id", UNAVAILABLE),
            "control_instrument_id": pair.get("control_instrument_id", control.get("instrument_id", UNAVAILABLE)),
            "control_stock_code": control.get("stock_code", UNAVAILABLE),
            "control_date": pair.get("control_anchor_date", control.get("anchor_date", UNAVAILABLE)),
            "control_market": pair.get("control_market", control.get("market", UNAVAILABLE)),
            "control_T5": pair.get("control_outcome_T5", UNAVAILABLE),
            "control_T10": pair.get("control_outcome_T10", UNAVAILABLE),
            "control_MFE_T5": UNAVAILABLE,
            "control_MAE_T5": UNAVAILABLE,
            "match_tier": pair.get("control_match_tier", UNAVAILABLE),
            "date_distance_days": pair.get("control_distance_days", UNAVAILABLE),
            "control_liquidity_quintile": pair.get("control_liquidity_quintile", UNAVAILABLE),
            "control_volatility_quintile": pair.get("control_volatility_quintile", UNAVAILABLE),
            "control_price_scale_bucket": pair.get("control_price_scale_bucket", UNAVAILABLE),
            "successful_liquidity_quintile": success.get("liquidity_quintile", UNAVAILABLE),
            "successful_volatility_quintile": success.get("volatility_quintile", UNAVAILABLE),
            "successful_price_scale_bucket": success.get("price_scale_bucket", UNAVAILABLE),
            "successful_ma60_eligible": success.get("ma60_eligible", UNAVAILABLE),
            "control_ma60_eligible": UNAVAILABLE,
            "control_source_lineage": pair.get("control_source_lineage", UNAVAILABLE),
            "successful_source_lineage": pair.get("successful_source_lineage", success.get("source_lineage", UNAVAILABLE)),
            "successful_pit_status": pair.get("successful_pit_status", success.get("pit_status", UNAVAILABLE)),
            "control_pit_status": pair.get("control_pit_status", UNAVAILABLE),
            "pit_snapshots_success_control": safe_json(snapshots),
            "robust_signal_comparison": "Success-side observed robust rows by day: " + safe_json(robust_presence) + "; control-side feature values are " + UNAVAILABLE + ".",
            "promising_signal_comparison": "Success-side observed promising rows by day: " + safe_json(promising_presence) + "; control-side feature values are " + UNAVAILABLE + ".",
            "selection_note": "Deterministic date/instrument-spread sample from existing matched rows; no rematching and no outcome-optimizing feature selection.",
        })
    return output


PAIR_FIELDS = [
    "pair_index", "sample_bucket", "stratum", "successful_anchor_id", "successful_episode_id", "successful_instrument_id", "successful_stock_code", "successful_date", "successful_market", "successful_T5", "successful_T10", "successful_MFE_T5", "successful_MAE_T5", "control_anchor_id", "control_instrument_id", "control_stock_code", "control_date", "control_market", "control_T5", "control_T10", "control_MFE_T5", "control_MAE_T5", "match_tier", "date_distance_days", "control_liquidity_quintile", "control_volatility_quintile", "control_price_scale_bucket", "successful_liquidity_quintile", "successful_volatility_quintile", "successful_price_scale_bucket", "successful_ma60_eligible", "control_ma60_eligible", "control_source_lineage", "successful_source_lineage", "successful_pit_status", "control_pit_status", "pit_snapshots_success_control", "robust_signal_comparison", "promising_signal_comparison", "selection_note",
]


def pair_markdown(pairs: list[dict[str, Any]]) -> str:
    lines = ["# WS3 Successful vs matched-control review pairs", "", "This is a deterministic bounded sample of existing matched rows. It is not a rematch, a similarity optimization, or a causal comparison. The source matched-control panel contains matching context and outcomes, but no control-side pre-event feature rows; therefore control-side PIT feature cells are explicitly unavailable.", ""]
    for pair in pairs:
        lines += [f"## Pair {pair['pair_index']} — {pair['sample_bucket']} — `{pair['stratum']}`", "", "### Success", "", f"- `{pair['successful_stock_code']}` on `{pair['successful_date']}`; market `{pair['successful_market']}`; T+5 `{fmt_pct(pair['successful_T5'])}`; T+10 `{fmt_pct(pair['successful_T10'])}`; MFE T5 `{fmt_pct(pair['successful_MFE_T5'])}`; MAE T5 `{fmt_pct(pair['successful_MAE_T5'])}`.", "", "### Control", "", f"- `{pair['control_stock_code']}` on `{pair['control_date']}`; market `{pair['control_market']}`; T+5 `{fmt_pct(pair['control_T5'])}`; T+10 `{fmt_pct(pair['control_T10'])}`; MFE/MAE `{UNAVAILABLE}`.", "", "### Matching context", "", f"- tier `{pair['match_tier']}`; date distance `{pair['date_distance_days']}` days; liquidity quintile success/control `{pair['successful_liquidity_quintile']}/{pair['control_liquidity_quintile']}`; volatility quintile `{pair['successful_volatility_quintile']}/{pair['control_volatility_quintile']}`; price-scale bucket `{pair['successful_price_scale_bucket']}/{pair['control_price_scale_bucket']}`; MA60 eligibility success/control `{pair['successful_ma60_eligible']}/{pair['control_ma60_eligible']}`.", "", "### PIT side-by-side", "", "| Day | Success | Control |", "|---:|---|---|"]
        snapshots = json.loads(pair["pit_snapshots_success_control"])
        for rel in SNAPSHOT_DAYS:
            label = "D0" if rel == 0 else f"D{rel}"
            lines.append(f"| {label} | `{snapshots[label]['success']}` | `{UNAVAILABLE}` |")
        lines += ["", f"- Robust signal comparison: {pair['robust_signal_comparison']}", f"- Promising signal comparison: {pair['promising_signal_comparison']}", "- Interpretation boundary: differences are descriptive evidence for human review only; no causal interpretation is asserted.", ""]
    return "\n".join(lines)


def extreme_rows(distinct: list[dict[str, str]], raw: dict[str, dict[str, str]], panel: dict[str, dict[int, dict[str, str]]], robust_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates = []
    for episode in distinct:
        aid = episode.get("representative_anchor_id", "")
        anchor = raw.get(aid)
        if not anchor:
            continue
        candidates.append({"episode": episode, "anchor": anchor})
    def select(field: str) -> list[dict[str, Any]]:
        selected = []
        used = set()
        for item in sorted(candidates, key=lambda value: (num(value["anchor"].get(field)) if num(value["anchor"].get(field)) is not None else -math.inf), reverse=True):
            aid = item["anchor"].get("anchor_id", "")
            if aid in used:
                continue
            used.add(aid)
            anchor = item["anchor"]
            selected.append({
                "anchor_id": aid,
                "instrument_id": anchor.get("instrument_id", UNAVAILABLE),
                "stock_code": anchor.get("stock_code", UNAVAILABLE),
                "market": anchor.get("market", UNAVAILABLE),
                "anchor_date": anchor.get("anchor_date", UNAVAILABLE),
                "stratum": item["episode"].get("stratum", UNAVAILABLE),
                "T5": raw_outcome(anchor, 5),
                "T10": raw_outcome(anchor, 10),
                "pre_event_summary": safe_json({rel: snapshot_values(panel, aid, rel) for rel in (-20, -5, 0)}),
                "a_state": state_from_raw(anchor),
                "robust_signal_observations": safe_json({rel: robust_observations_at(panel, aid, rel, robust_rows) for rel in SNAPSHOT_DAYS}),
                "source_lineage": anchor.get("source_lineage", UNAVAILABLE),
            })
            if len(selected) == 10:
                break
        return selected
    return select("T5_forward_close_return"), select("T10_forward_close_return")


def extreme_markdown(t5: list[dict[str, Any]], t10: list[dict[str, Any]]) -> str:
    lines = ["# WS3 extreme successful cases", "", "`EXTREME_CASES_NOT_REPRESENTATIVE`: these are descriptive tails of the existing distinct-episode representatives and must not be treated as typical cases or as a strategy conclusion.", ""]
    for label, rows in (("Highest existing T+5 outcome episodes", t5), ("Highest existing T+10 outcome episodes", t10)):
        lines += [f"## {label}", "", "| Rank | Stock | Date | Anchor | Stratum | T+5 | T+10 | MFE T5 | MAE T5 | A-state | Robust observations |", "|---:|---|---|---|---|---:|---:|---:|---:|---|---|"]
        for rank, row in enumerate(rows, 1):
            lines.append("| " + " | ".join([str(rank), row["stock_code"], row["anchor_date"], f"`{row['anchor_id'][:12]}…`", row["stratum"], fmt_pct(row["T5"]["forward_return"]), fmt_pct(row["T10"]["forward_return"]), fmt_pct(row["T5"]["MFE"]), fmt_pct(row["T5"]["MAE"]), markdown_cell(row["a_state"].get("a_state_bucket", UNAVAILABLE)), markdown_cell(row["robust_signal_observations"])]) + " |")
            summary = json.loads(row["pre_event_summary"])
            compact = []
            for day in (-20, -5, 0):
                snap = summary.get(str(day), {})
                compact.append(f"D{day}: trend close/MA20={fmt(snap.get('close_vs_ma20'))}; compression ratio={fmt(snap.get('range_compression_5_to_20'))}; volume ratio20={fmt(snap.get('VOLUME_RATIO_20'))}")
            lines.append(f"- `{row['stock_code']}` {row['anchor_date']}: " + "; ".join(compact))
        lines += ["", "Pre-event summaries are direct PIT observations from the existing feature panel. Extreme cases are descriptive tails and not representative.", ""]
    return "\n".join(lines)


def family_summary(univariate: list[dict[str, str]], lead_rows: list[dict[str, str]], stability_rows: list[dict[str, str]], gradients: list[dict[str, str]]) -> str:
    lead = {row.get("feature_family", ""): row for row in lead_rows}
    stability = {(row.get("feature_family", ""), row.get("classification", "")): row for row in stability_rows}
    gradient_by_family: dict[str, Counter[str]] = defaultdict(Counter)
    for row in gradients:
        gradient_by_family[row.get("feature_family", "")][row.get("monotonicity", UNAVAILABLE)] += 1
    lines = ["# WS3 feature-family interpretation", "", "This is a compact reading of existing discovery artifacts. Family-level descriptions are hypotheses for owner review only; none is a strategy rule or accepted feature.", ""]
    technical = {
        "TREND_STRUCTURE": "Price location, moving-average ordering, and moving-average slopes describe directional structure and distance from recent reference levels.",
        "VOLATILITY_COMPRESSION": "Range width and realized-volatility ratios describe whether recent movement is tighter or broader than its own recent baseline.",
        "VOLUME_PARTICIPATION": "Volume ratios describe participation relative to recent baselines; contraction and expansion are frozen descriptive states.",
        "MOMENTUM": "Raw returns, RSI, and MACD fields describe recent price impulse and oscillator state under Technical V0 semantics.",
        "A_STATE_CONTEXT": "A1/A2 fields provide frozen event-context labels from the prior P1E work; they are not retuned here.",
        "RELATIVE_STRENGTH": "Relative performance versus a canonical benchmark would compare stock movement with a shared market reference.",
    }
    for family in FAMILIES:
        frows = [row for row in univariate if row.get("feature_family") == family]
        robust = [row for row in frows if row.get("classification") == "ROBUST_DISCOVERY_SIGNAL"]
        promising = [row for row in frows if row.get("classification") == "PROMISING_DISCOVERY_SIGNAL"]
        lead_row = lead.get(family, {})
        strongest = sorted(robust + promising, key=ranking_key)[:3]
        grad = ", ".join(f"{key}={value}" for key, value in sorted(gradient_by_family.get(family, {}).items())) or UNAVAILABLE
        srob = stability.get((family, "ROBUST_DISCOVERY_SIGNAL"), {})
        sprom = stability.get((family, "PROMISING_DISCOVERY_SIGNAL"), {})
        available = "UNAVAILABLE_DUE_TO_NO_CANONICAL_BENCHMARK" if family == "RELATIVE_STRENGTH" else ("YES" if frows else "NO")
        unresolved = ["discovery-only; no confirmatory validation or strategy acceptance", "per-market and per-temporal-split detail is " + UNAVAILABLE]
        if family == "RELATIVE_STRENGTH":
            unresolved.insert(0, "UNAVAILABLE_DUE_TO_NO_CANONICAL_BENCHMARK; this is not a no-signal conclusion")
        strongest_text = ", ".join("`{}` at D{} ({})".format(row.get("feature_id"), row.get("relative_day"), row.get("stratum")) for row in strongest) or UNAVAILABLE
        lines += [f"## {FAMILY_LABELS[family]}", "", f"- Signal available: `{available}`", f"- Robust observations: `{len(robust)}`; Promising observations: `{len(promising)}`", f"- Earliest useful lead time: `{lead_row.get('earliest_useful_label', UNAVAILABLE)}`", f"- Strongest existing observations: {strongest_text}", f"- Existing outcome-strength gradient labels: `{grad}`. This records the source labels; it does not claim monotonic strategy strength.", f"- Stability: robust pooled market value `{srob.get('market_consistency_median', UNAVAILABLE)}` and temporal value `{srob.get('temporal_consistency_median', UNAVAILABLE)}`; promising pooled market `{sprom.get('market_consistency_median', UNAVAILABLE)}` and temporal `{sprom.get('temporal_consistency_median', UNAVAILABLE)}`. Detailed split evidence: `{UNAVAILABLE}`.", f"- Technical interpretation: {technical[family]}", f"- Unresolved: {'; '.join(unresolved)}.", ""]
    return "\n".join(lines)


def question_sheet() -> str:
    return """# WS3 Owner human research question sheet

Do not answer these questions in this extraction task. Use the linked evidence packs for manual review by Owner + ChatGPT.

1. Do successful swing cases visually/structurally appear to share a common pre-event trend structure?
2. Is volatility compression actually visible as tightening range, stable consolidation, reduced downside volatility, or another form?
3. What does Volume Participation appear to represent: dry-up before breakout, early accumulation, D-5 volume expansion, breakout confirmation, or something else?
4. Do >=10% outcomes look structurally different from >=3% outcomes?
5. Are there multiple successful swing archetypes rather than one?
6. Which Successful vs Control pairs appear nearly indistinguishable?
7. What appears to separate those false friends?
8. Are A1/A2 states an early precursor, late confirmation, useful only for one archetype, or mostly incidental?
9. Which findings appear economically interpretable rather than merely statistically different?
10. Which hypotheses should eventually be frozen for confirmatory research?
11. Does the evidence suggest Relative Strength is worth adding as a future canonical evidence family?
12. Does any unresolved distinction justify future event-bounded 1-minute OHLCV / AVWAP / Volume Profile research?

Boundary: these questions are a human-assisted research handoff, not answers, rules, or an accepted/rejected strategy decision.
"""


def false_friend_markdown() -> str:
    return f"""# WS3 false-friend cases

`FALSE_FRIEND_EXTRACTION=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`

The existing matched-control artifact provides pair identity, matching tier, date distance, market, liquidity, volatility, price-scale context, and outcomes. It does not persist a feature-space similarity score or control-side pre-event feature panel. Producing the requested up-to-10 false-friend ranking would therefore require a new feature join, similarity computation, or rematching, all outside this task boundary.

`FALSE_FRIEND_CASE_COUNT=0`

No false-friend cases were recomputed or inferred.
"""


def master_markdown(summary: dict[str, Any], files: list[str], robust: list[dict[str, Any]], promising: list[dict[str, Any]], family_md: str, reference_md: str, pair_md: str, false_md: str, extreme_md: str, questions_md: str) -> str:
    robust_table = ["| Rank | Family | Feature | Day | Stratum | SMD | Overlap |", "|---:|---|---|---:|---|---:|---:|"]
    for row in robust:
        robust_table.append(f"| {row['rank']} | {row['feature_family_label']} | `{row['feature_id']}` | {row['relative_day_label']} | {row['outcome_stratum']} | {fmt(row['standardized_mean_difference'])} | {fmt(row['distribution_overlap'])} |")
    promising_table = ["| Rank | Family | Feature | Day | Stratum | SMD | Why not robust |", "|---:|---|---|---:|---|---:|---|"]
    for row in promising:
        promising_table.append(f"| {row['rank']} | {row['feature_family_label']} | `{row['feature_id']}` | {row['relative_day_label']} | {row['outcome_stratum']} | {fmt(row['standardized_mean_difference'])} | {markdown_cell(row['why_promising_not_robust'])} |")
    sections = [
        "# WS3 Successful Swing Owner Human Review Pack",
        "",
        "This is an evidence-only, human-assisted review handoff. It consumes the completed canonical Successful Swing discovery artifacts and does not rerun research, create rules, or accept/reject a strategy.",
        "",
        "## Section 1 — Research context",
        "",
        f"- Source task: `{SOURCE_TASK_ID}`; source canonical head: `{summary['SOURCE_CANONICAL_HEAD']}`.",
        f"- Dataset: `{summary['SOURCE_INSTRUMENT_COUNT']}` instruments; `{summary['SOURCE_OHLCV_ROW_COUNT']}` accepted OHLCV rows; `{summary['SOURCE_START']} .. {summary['SOURCE_END']}`; SHA256 `{summary['SOURCE_SHA256']}`.",
        f"- Existing discovery: `{summary['RAW_ELIGIBLE_ANCHOR_COUNT']}` eligible anchors; `{summary['DISTINCT_SWING_EPISODE_COUNT']}` distinct episodes; `{summary['MATCHED_CONTROL_COUNT']}` matched controls; robust `{summary['ROBUST_DISCOVERY_SIGNAL_COUNT']}`; promising `{summary['PROMISING_DISCOVERY_SIGNAL_COUNT']}`.",
        f"- A-state context: A1-only `{fmt_pct(summary['SUCCESSFUL_SWING_PRECEDED_BY_A1_RATE'])}`; A2-related `{fmt_pct(summary['SUCCESSFUL_SWING_PRECEDED_BY_A2_RATE'])}`; A1→A2 `{fmt_pct(summary['SUCCESSFUL_SWING_PRECEDED_BY_A1_TO_A2_RATE'])}`; neither `{fmt_pct(summary['SUCCESSFUL_SWING_WITH_NO_A_STATE_RATE'])}`.",
        "- Relative Strength: `UNAVAILABLE_DUE_TO_NO_CANONICAL_BENCHMARK`; this is not a no-signal conclusion.",
        "- This pack is discovery evidence only. A1/A2, definitions, thresholds, feature families, confirmatory validation, production, and NEXT_TASK were not changed.",
        "",
        "## Section 2 — 11 Robust signals",
        "",
        *robust_table,
        "",
        "Full definitions, medians, stability, gradient labels, and interpretations: [ws3-owner-review-robust-signals.md](ws3-owner-review-robust-signals.md).",
        "",
        "## Section 3 — Top 20 Promising signals",
        "",
        *promising_table,
        "",
        "Full machine-readable fields: [ws3-owner-review-top20-promising-signals.csv](ws3-owner-review-top20-promising-signals.csv). Ranking is the stable source-evidence reconstruction described in the robust-signals pack; it is not a new search.",
        "",
        "## Section 4 — Feature-family summary",
        "",
        "See [ws3-owner-review-feature-family-summary.md](ws3-owner-review-feature-family-summary.md). The family summary preserves discovery-only and benchmark limitations.",
        "",
        "## Section 5 — Seven Owner reference cases",
        "",
        "See [ws3-owner-review-reference-case-cards.md](ws3-owner-review-reference-case-cards.md) and [ws3-owner-review-reference-case-cards.json](ws3-owner-review-reference-case-cards.json).",
        "",
        "## Section 6 — 20 Successful vs matched-control pairs",
        "",
        "See [ws3-owner-review-success-control-pairs.md](ws3-owner-review-success-control-pairs.md) and [ws3-owner-review-success-control-pairs.csv](ws3-owner-review-success-control-pairs.csv). Control-side PIT feature values are not persisted in the source artifacts and remain explicitly unavailable.",
        "",
        "## Section 7 — False-friend cases",
        "",
        "See [ws3-owner-review-false-friend-cases.md](ws3-owner-review-false-friend-cases.md). `FALSE_FRIEND_EXTRACTION=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.",
        "",
        "## Section 8 — Extreme success cases",
        "",
        "See [ws3-owner-review-extreme-success-cases.md](ws3-owner-review-extreme-success-cases.md). `EXTREME_CASES_NOT_REPRESENTATIVE`.",
        "",
        "## Section 9 — Human research question sheet",
        "",
        "See [ws3-owner-human-research-question-sheet.md](ws3-owner-human-research-question-sheet.md). Questions are intentionally unanswered.",
        "",
        "## Section 10 — Artifact index",
        "",
        "| Artifact | Purpose |",
        "|---|---|",
        *[f"| [{name}]({name}) | Supporting owner-review artifact |" for name in files],
        "",
        "### Stop boundary",
        "",
        "No new research conclusion is made. This pack is returned to Owner for human review and Strategy Review input only; no accepted/rejected owner decision is made here.",
    ]
    return "\n".join(sections)


def make_summary(source_summary: dict[str, Any], inventory: list[dict[str, Any]], robust: list[dict[str, Any]], promising: list[dict[str, Any]], cases: list[dict[str, Any]], pairs: list[dict[str, Any]], t5: list[dict[str, Any]], t10: list[dict[str, Any]], task_commit: str, final_head: str) -> dict[str, Any]:
    family_counts = Counter(row["feature_family"] for row in robust)
    return {
        "TASK_ID": TASK_ID,
        "TASK_FINAL_STATUS": "COMPLETE_PASS",
        "SOURCE_SUCCESSFUL_SWING_TASK": SOURCE_TASK_ID,
        "SOURCE_CANONICAL_HEAD": source_summary.get("FINAL_CANONICAL_HEAD", UNAVAILABLE),
        "TASK_COMMIT": task_commit,
        "FINAL_CANONICAL_HEAD": final_head,
        "SOURCE_ARTIFACTS_FOUND": sum(row["status"] == "FOUND" for row in inventory),
        "SOURCE_ARTIFACTS_MISSING": [row["artifact"] for row in inventory if row["status"] == "MISSING"],
        "SOURCE_ARTIFACTS_NOT_REQUIRED": [],
        "FULL_REPLAY_EXECUTED": "NO",
        "EVENT_MINING_RERUN": "NO",
        "FEATURE_COMPUTATION_RERUN": "NO",
        "MATCHING_RERUN": "NO",
        "ROBUST_SIGNAL_COUNT_EXTRACTED": len(robust),
        "PROMISING_SIGNAL_COUNT_EXTRACTED": len(promising),
        "ROBUST_FAMILY_COUNTS": {family: family_counts.get(family, 0) for family in FAMILIES},
        "TREND_STRUCTURE_ROBUST_COUNT": family_counts.get("TREND_STRUCTURE", 0),
        "VOLATILITY_COMPRESSION_ROBUST_COUNT": family_counts.get("VOLATILITY_COMPRESSION", 0),
        "VOLUME_PARTICIPATION_ROBUST_COUNT": family_counts.get("VOLUME_PARTICIPATION", 0),
        "MOMENTUM_ROBUST_COUNT": family_counts.get("MOMENTUM", 0),
        "A_STATE_ROBUST_COUNT": family_counts.get("A_STATE_CONTEXT", 0),
        "RELATIVE_STRENGTH_STATUS": "UNAVAILABLE_DUE_TO_NO_CANONICAL_BENCHMARK",
        "OWNER_REFERENCE_CASES_EXTRACTED": len(cases),
        "SUCCESS_CONTROL_PAIR_COUNT": len(pairs),
        "FALSE_FRIEND_EXTRACTION": "NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS",
        "FALSE_FRIEND_CASE_COUNT": 0,
        "EXTREME_T5_CASE_COUNT": len(t5),
        "EXTREME_T10_CASE_COUNT": len(t10),
        "MASTER_OWNER_REVIEW_PACK_CREATED": "YES",
        "NEW_FEATURE_DISCOVERY_EXECUTED": "NO",
        "NEW_THRESHOLD_SEARCH_EXECUTED": "NO",
        "CONFIRMATORY_RESEARCH_EXECUTED": "NO",
        "A1_CHANGED": "NO",
        "A2_CHANGED": "NO",
        "DATABASE_MUTATION": "NO",
        "PRODUCTION_MUTATION": "NO",
        "WS1_CHANGED": "NO",
        "WS2_CHANGED": "NO",
        "WS4_CHANGED": "NO",
        "NEXT_TASK_CHANGED": "NO",
        "PUSH_REMOTE": "NO",
        "DEPLOY": "NO",
        "SCHEDULER_CHANGE": "NO",
        "READY_FOR_OWNER_HUMAN_REVIEW": "YES_WITH_BOUNDED_LIMITATIONS",
        "LIMITATIONS": [
            "control-side PIT feature snapshots are " + UNAVAILABLE,
            "false-friend similarity ranking is " + UNAVAILABLE,
            "per-market and per-temporal split detail is " + UNAVAILABLE,
            "relative strength is unavailable due to no canonical benchmark",
        ],
    }


def formal_report(summary: dict[str, Any], inventory: list[dict[str, Any]], files: list[str]) -> str:
    found = [row["artifact"] for row in inventory if row["status"] == "FOUND"]
    missing = [row["artifact"] for row in inventory if row["status"] == "MISSING"]
    lines = [
        f"# {TASK_ID}", "", f"TASK_ID={TASK_ID}", "TASK_FINAL_STATUS=COMPLETE_PASS", f"SOURCE_SUCCESSFUL_SWING_TASK={SOURCE_TASK_ID}", f"SOURCE_CANONICAL_HEAD={summary['SOURCE_CANONICAL_HEAD']}", f"TASK_COMMIT={summary['TASK_COMMIT']}", f"FINAL_CANONICAL_HEAD={summary['FINAL_CANONICAL_HEAD']}", "", "## Source artifact inventory", "", f"SOURCE_ARTIFACTS_FOUND={len(found)}", f"SOURCE_ARTIFACTS_MISSING={','.join(missing) if missing else 'NONE'}", f"SOURCE_ARTIFACTS_NOT_REQUIRED={','.join(summary['SOURCE_ARTIFACTS_NOT_REQUIRED']) if summary['SOURCE_ARTIFACTS_NOT_REQUIRED'] else 'NONE'}", "", "## Extraction boundary", "", "FULL_REPLAY_EXECUTED=NO", "EVENT_MINING_RERUN=NO", "FEATURE_COMPUTATION_RERUN=NO", "MATCHING_RERUN=NO", "NEW_FEATURE_DISCOVERY_EXECUTED=NO", "NEW_THRESHOLD_SEARCH_EXECUTED=NO", "CONFIRMATORY_RESEARCH_EXECUTED=NO", "A1_CHANGED=NO", "A2_CHANGED=NO", "", "## Extracted review pack", "", f"ROBUST_SIGNAL_COUNT_EXTRACTED={summary['ROBUST_SIGNAL_COUNT_EXTRACTED']}", f"PROMISING_SIGNAL_COUNT_EXTRACTED={summary['PROMISING_SIGNAL_COUNT_EXTRACTED']}", f"TREND_STRUCTURE_ROBUST_COUNT={summary['TREND_STRUCTURE_ROBUST_COUNT']}", f"VOLATILITY_COMPRESSION_ROBUST_COUNT={summary['VOLATILITY_COMPRESSION_ROBUST_COUNT']}", f"VOLUME_PARTICIPATION_ROBUST_COUNT={summary['VOLUME_PARTICIPATION_ROBUST_COUNT']}", f"MOMENTUM_ROBUST_COUNT={summary['MOMENTUM_ROBUST_COUNT']}", f"A_STATE_ROBUST_COUNT={summary['A_STATE_ROBUST_COUNT']}", f"RELATIVE_STRENGTH_STATUS={summary['RELATIVE_STRENGTH_STATUS']}", f"OWNER_REFERENCE_CASES_EXTRACTED={summary['OWNER_REFERENCE_CASES_EXTRACTED']}", f"SUCCESS_CONTROL_PAIR_COUNT={summary['SUCCESS_CONTROL_PAIR_COUNT']}", f"FALSE_FRIEND_EXTRACTION={summary['FALSE_FRIEND_EXTRACTION']}", f"FALSE_FRIEND_CASE_COUNT={summary['FALSE_FRIEND_CASE_COUNT']}", f"EXTREME_T5_CASE_COUNT={summary['EXTREME_T5_CASE_COUNT']}", f"EXTREME_T10_CASE_COUNT={summary['EXTREME_T10_CASE_COUNT']}", "MASTER_OWNER_REVIEW_PACK_CREATED=YES", "", "## Safety and readiness", "", "DATABASE_MUTATION=NO", "PRODUCTION_MUTATION=NO", "WS1_CHANGED=NO", "WS2_CHANGED=NO", "WS4_CHANGED=NO", "NEXT_TASK_CHANGED=NO", "PUSH_REMOTE=NO", "DEPLOY=NO", "SCHEDULER_CHANGE=NO", "READY_FOR_OWNER_HUMAN_REVIEW=YES_WITH_BOUNDED_LIMITATIONS", "", "## Bounded limitations", "", *[f"- {item}" for item in summary["LIMITATIONS"]], "", "## Created artifacts", "", *[f"- `{file}`" for file in files], "", "The pack is a Strategy Review input only. It does not make an accepted/rejected owner decision and this task stops here."]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-commit", default="PENDING_ISOLATED_TASK_COMMIT")
    parser.add_argument("--final-canonical-head", default="PENDING_CANONICAL_PROMOTION")
    parser.add_argument("--source-canonical-head", default="PENDING_SOURCE_CANONICAL_HEAD")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    src = root / SOURCE_DIR_NAME
    out = root / OUTPUT_DIR_NAME
    docs = root / DOC_DIR_NAME
    out.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)

    inventory = source_inventory(src)
    if any(row["status"] == "MISSING" for row in inventory):
        raise SystemExit("Source artifact inventory contains MISSING items; fail closed without reconstruction.")

    source_summary = read_json(src / "ws3-successful-swing-run-summary.json")
    feature_manifest = read_json(src / "ws3-successful-swing-feature-manifest.json")
    reference = read_json(src / "ws3-successful-swing-reference-case-cards.json")
    audit = read_json(src / "ws3-successful-swing-lookahead-hindsight-audit.json")
    repro = read_json(src / "ws3-successful-swing-reproducibility-manifest.json")
    univariate = read_csv(src / "ws3-successful-swing-univariate-discrimination.csv")
    gradients = read_csv(src / "ws3-successful-swing-outcome-strength-gradient.csv")
    lead_rows = read_csv(src / "ws3-successful-swing-lead-time-analysis.csv")
    stability_rows = read_csv(src / "ws3-successful-swing-market-temporal-stability.csv")
    distinct = read_csv(src / "ws3-successful-swing-distinct-episode-panel.csv")
    matched = read_csv(src / "ws3-successful-swing-matched-control-panel.csv")

    if audit.get("quality_gate_pass") not in (True, "YES") or repro.get("reproducible") != "YES":
        raise SystemExit("Existing source quality/reproducibility gate is not passing; fail closed.")
    if audit.get("future_session_dependency_in_features") not in (False, "NO") or audit.get("post_event_feature_leakage") not in (0, "0", False):
        raise SystemExit("Existing source look-ahead audit is not clean; fail closed.")

    lead = {row.get("feature_family", ""): row for row in lead_rows}
    robust_source = sorted([row for row in univariate if row.get("classification") == "ROBUST_DISCOVERY_SIGNAL"], key=ranking_key)
    promising_source = sorted([row for row in univariate if row.get("classification") == "PROMISING_DISCOVERY_SIGNAL"], key=ranking_key)[:20]
    gradients_grouped = gradient_map(gradients)
    robust = signal_records(robust_source, gradients_grouped, lead)
    promising = signal_records(promising_source, gradients_grouped, lead)
    # signal_records ranks within the passed slice; retain review-local ranks.
    for index, row in enumerate(robust, 1):
        row["rank"] = index
    for index, row in enumerate(promising, 1):
        row["rank"] = index

    # Determine all anchor IDs needed before streaming the two large panels.
    reference_anchor_ids = {event.get("anchor_id", "") for case in reference.get("cases", []) for event in case.get("qualifying_events", [])}
    chosen_pairs = choose_pairs(matched)
    pair_anchor_ids = {row.get("successful_anchor_id", "") for _, row in chosen_pairs} | {row.get("control_anchor_id", "") for _, row in chosen_pairs}
    extreme_candidates = {row.get("representative_anchor_id", "") for row in distinct}
    selected_anchor_ids = reference_anchor_ids | pair_anchor_ids | extreme_candidates
    raw = load_raw_selected(src / "ws3-successful-swing-raw-anchor-panel.csv", selected_anchor_ids)
    panel = load_panel_selected(src / "ws3-successful-swing-pre-event-feature-panel.csv", selected_anchor_ids - {row.get("control_anchor_id", "") for _, row in chosen_pairs})
    # The control IDs are not expected in the successful-only feature panel;
    # only controls are excluded, while selected successful pair anchors remain available.
    cases = reference_payload(reference, raw, panel, robust)
    pairs = pair_payload(chosen_pairs, raw, panel, robust, promising)
    t5, t10 = extreme_rows(distinct, raw, panel, robust)

    inventory_csv = [{"artifact": row["artifact"], "status": row["status"], "size_bytes": row.get("size_bytes", ""), "source_path": row["path"]} for row in inventory]
    write_csv(out / "ws3-owner-review-source-artifact-inventory.csv", inventory_csv, ["artifact", "status", "size_bytes", "source_path"])
    write_text(out / "ws3-owner-review-source-artifact-inventory.md", source_inventory_markdown(inventory))
    write_csv(out / "ws3-owner-review-robust-signals.csv", robust, SIGNAL_FIELDS)
    write_text(out / "ws3-owner-review-robust-signals.md", signal_markdown("WS3 robust discovery signals", robust))
    write_csv(out / "ws3-owner-review-top20-promising-signals.csv", promising, SIGNAL_FIELDS)
    write_text(out / "ws3-owner-review-feature-family-summary.md", family_summary(univariate, lead_rows, stability_rows, gradients))
    write_text(out / "ws3-owner-review-reference-case-cards.md", reference_markdown(cases))
    write_json(out / "ws3-owner-review-reference-case-cards.json", {"schema_version": "ws3-owner-review-reference-case-cards.v1", "source_task": SOURCE_TASK_ID, "cases": cases})
    write_csv(out / "ws3-owner-review-success-control-pairs.csv", pairs, PAIR_FIELDS)
    write_text(out / "ws3-owner-review-success-control-pairs.md", pair_markdown(pairs))
    write_text(out / "ws3-owner-review-false-friend-cases.md", false_friend_markdown())
    write_text(out / "ws3-owner-review-extreme-success-cases.md", extreme_markdown(t5, t10))
    questions = question_sheet()
    write_text(out / "ws3-owner-human-research-question-sheet.md", questions)

    summary = make_summary(source_summary, inventory, robust, promising, cases, pairs, t5, t10, args.task_commit, args.final_canonical_head)
    summary["SOURCE_CANONICAL_HEAD"] = args.source_canonical_head
    write_json(out / "ws3-owner-review-pack-summary.json", summary)
    # Retain a compact machine-readable extraction manifest alongside the review pack.
    write_json(out / "ws3-owner-review-extraction-manifest.json", {
        "task_id": TASK_ID,
        "source_task": SOURCE_TASK_ID,
        "source_artifacts_found": len([row for row in inventory if row["status"] == "FOUND"]),
        "feature_manifest_schema_version": feature_manifest.get("schema_version", UNAVAILABLE),
        "source_quality_gate": audit.get("quality_gate_pass", UNAVAILABLE),
        "source_reproducible": repro.get("reproducible", UNAVAILABLE),
        "full_replay_executed": False,
        "selected_reference_anchor_count": len(reference_anchor_ids),
        "selected_pair_count": len(pairs),
        "selected_extreme_t5_count": len(t5),
        "selected_extreme_t10_count": len(t10),
        "control_side_feature_panel": UNAVAILABLE,
        "false_friend_extraction": UNAVAILABLE,
    })
    supporting_files = sorted(path.name for path in out.iterdir() if path.is_file() and path.name != "WS3-SUCCESSFUL-SWING-OWNER-HUMAN-REVIEW-PACK.md")
    master_summary = dict(source_summary)
    master_summary.update(summary)
    master = master_markdown(master_summary, supporting_files, robust, promising, "", "", "", "", "", "")
    write_text(out / "WS3-SUCCESSFUL-SWING-OWNER-HUMAN-REVIEW-PACK.md", master)
    report_files = sorted(path.name for path in out.iterdir() if path.is_file())
    write_text(docs / "formal-closure-report.md", formal_report(summary, inventory, report_files))


if __name__ == "__main__":
    main()
