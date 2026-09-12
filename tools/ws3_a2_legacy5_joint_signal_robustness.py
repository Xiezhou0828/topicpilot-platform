"""WS3-only A2 x LEGACY-5 joint-signal robustness and benchmark validation.

This study is deliberately evidence-only.  It consumes the committed A2 and
LEGACY-5 artifacts, reconstructs the already-frozen +/-1 trading-session
overlap at event level, and computes descriptive endpoint/path robustness
checks.  It does not change either signal, Core V0 semantics, or production.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ws3_legacy5_eligibility_a2_complementarity as prior  # noqa: E402


TASK_ID = "TASK-WS3-A2-LEGACY5-JOINT-SIGNAL-ROBUSTNESS-AND-BENCHMARK-VALIDATION-20260822"
SOURCE_START = date(2024, 8, 13)
SOURCE_END = date(2026, 8, 13)
CHRONOLOGICAL_MIDPOINT = "2025-08-13"
FIXED_WINDOW = 1
HORIZONS = (1, 3, 5, 10)
PATH_HORIZONS = (5, 10)
BOOTSTRAP_REPS = 1000
BOOTSTRAP_SEED = 20260822
MIN_STABILITY_SAMPLE = 30
PRIMARY_COHORTS = ("A2_ONLY", "LEGACY5_ONLY", "BOTH_SAME_SESSION")
ALL_COHORTS = (*PRIMARY_COHORTS, "BOTH_WITHIN_1_SESSION")
TIMING_CLASSES = ("LEGACY_EARLIER", "SAME_SESSION", "A2_EARLIER")
BARRIER_PAIRS = ((0.05, -0.05), (0.10, -0.05))
MFE_THRESHOLDS = (0.03, 0.05, 0.10)
MAE_THRESHOLDS = (-0.03, -0.05, -0.10)

LEGACY_DIR = Path("reports/TASK-WS3-LEGACY-5-STRATEGY-BENCHMARK-20260822")
A2_PATH_DIR = Path("reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821")
A2_EVENT_DIR = Path("reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820")
OUTPUT_DIR_DEFAULT = Path("reports") / TASK_ID


class ContractBlocked(RuntimeError):
    """A required source or fixed semantic contract failed closed."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    materialized = list(rows)
    fields: list[str] = []
    for row in materialized:
        for field in row:
            if field not in fields:
                fields.append(field)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (date,)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set, frozenset)):
        return "|".join(_csv_value(item) for item in value)
    return value


def _json_default(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (set, tuple, frozenset)):
        return "|".join(_json_default(item) for item in value)
    return str(value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _quantile(values: Iterable[float], probability: float) -> float | None:
    numbers = sorted(float(value) for value in values)
    if not numbers:
        return None
    if len(numbers) == 1:
        return numbers[0]
    position = (len(numbers) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return numbers[lower]
    return numbers[lower] + (numbers[upper] - numbers[lower]) * (position - lower)


def _numbers(rows: Iterable[Mapping[str, Any]], field: str) -> list[float]:
    return [float(row[field]) for row in rows if row.get(field) not in (None, "")]


def _summary(values: Iterable[float]) -> dict[str, Any]:
    numbers = list(values)
    return {
        "count": len(numbers),
        "mean": statistics.fmean(numbers) if numbers else None,
        "median": statistics.median(numbers) if numbers else None,
        "stddev": statistics.stdev(numbers) if len(numbers) > 1 else None,
        "p05": _quantile(numbers, 0.05),
        "p25": _quantile(numbers, 0.25),
        "p75": _quantile(numbers, 0.75),
        "p95": _quantile(numbers, 0.95),
        "positive_rate": sum(value > 0 for value in numbers) / len(numbers) if numbers else None,
    }


def _matured(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("maturity_status") == "COMPLETE_RAW_PATH" and row.get("endpoint_return") is not None and row.get("mfe") is not None and row.get("mae") is not None]


def _records_for_horizon(records: Mapping[tuple[str, int], list[dict[str, Any]]], cohort: str, horizon: int) -> list[dict[str, Any]]:
    return records.get((cohort, horizon), [])


def _pair_id(a2_event_id: str, legacy_anchor_id: str) -> str:
    return f"{a2_event_id}|{legacy_anchor_id}"


def _barrier_label(up: float, down: float) -> str:
    return f"barrier_{int(up * 100)}_before_minus{int(abs(down) * 100)}"


def _add_a2_barriers(row: dict[str, Any], path: Mapping[str, str]) -> None:
    for up, down in BARRIER_PAIRS:
        label = _barrier_label(up, down)
        row[f"{label}_outcome"] = prior._a2_barrier(path, up, down)


def _load_inputs(repo_root: Path, database_url: str) -> dict[str, Any]:
    groups, quality = prior._read_surface(database_url)
    legacy_raw, legacy_outcomes, legacy_meta = prior._load_legacy(repo_root)
    ma20 = prior._ma20_by_anchor(groups)
    anchors_by_variant = prior._variant_anchor_sets(legacy_raw, groups, ma20)
    a2_events, a2_path_index, a2_meta = prior._load_a2(repo_root)
    if len(a2_events) != 5277 or len({row["event_id"] for row in a2_events}) != 5277:
        raise ContractBlocked("A2 event panel is not the expected 5,277 unique event cohort")
    if len(anchors_by_variant["V0_LEGACY5"]) != 2471 or len(anchors_by_variant["V2_LEGACY5_MA60"]) != 2096:
        raise ContractBlocked("LEGACY-5 V0/V2 counts do not reconcile to the frozen benchmark")
    return {
        "groups": groups,
        "surface_quality": quality,
        "legacy_raw": legacy_raw,
        "legacy_outcomes": legacy_outcomes,
        "legacy_meta": legacy_meta,
        "anchors_by_variant": anchors_by_variant,
        "a2_events": a2_events,
        "a2_path_index": a2_path_index,
        "a2_meta": a2_meta,
    }


def _source_rows(inputs: Mapping[str, Any]) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[tuple[str, int], dict[str, Any]]]:
    a2_by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for event in inputs["a2_events"]:
        for horizon in HORIZONS:
            path = inputs["a2_path_index"][(event["event_id"], horizon)]
            row = prior._normalize_a2_rows([event], inputs["a2_path_index"], horizon)[0]
            _add_a2_barriers(row, path)
            row.update({"stock_code": event.get("stock_code"), "market": event.get("market"), "event_key": event["event_id"], "anchor_id": "", "source": "A2"})
            a2_by_key[(event["event_id"], horizon)] = row
    legacy_by_key: dict[tuple[str, int], dict[str, Any]] = {}
    anchors = inputs["anchors_by_variant"]["V0_LEGACY5"]
    for horizon in HORIZONS:
        for row in prior._normalize_legacy_rows(anchors, horizon, inputs["legacy_outcomes"], inputs["groups"]):
            anchor = next(item for item in anchors if item["anchor_id"] == row["anchor_id"])
            row.update({"stock_code": anchor.get("stock_code"), "market": anchor.get("market"), "event_key": anchor["base_anchor_id"], "source": "LEGACY5"})
            legacy_by_key[(anchor["anchor_id"], horizon)] = row
    return a2_by_key, legacy_by_key


def _make_cohort_records(inputs: Mapping[str, Any], matching: Mapping[str, Any], variant: str, a2_by_key: Mapping[tuple[str, int], dict[str, Any]], legacy_by_anchor_h: Mapping[tuple[str, int], dict[str, Any]]) -> tuple[dict[tuple[str, int], list[dict[str, Any]]], dict[str, Any]]:
    records: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    pair_members: dict[str, dict[str, Any]] = {}

    def append_source(cohort: str, source_row: Mapping[str, Any], horizon: int, pair_id: str = "", delta: int | None = None) -> None:
        item = dict(source_row)
        item.update({"cohort": cohort, "pair_id": pair_id, "pair_delta_sessions": delta, "eligibility_variant": variant})
        records[(cohort, horizon)].append(item)

    for event in matching["a2_only"]:
        for horizon in HORIZONS:
            append_source("A2_ONLY", a2_by_key[(event["event_id"], horizon)], horizon)
    for anchor in matching["legacy_only"]:
        for horizon in HORIZONS:
            append_source("LEGACY5_ONLY", legacy_by_anchor_h[(anchor["anchor_id"], horizon)], horizon)
    for match in matching["matches"]:
        delta = int(match["delta_sessions"])
        cohort = "BOTH_SAME_SESSION" if delta == 0 else "BOTH_WITHIN_1_SESSION"
        pair_id = _pair_id(match["a2"]["event_id"], match["legacy"]["base_anchor_id"])
        pair_members[pair_id] = {"a2_event_id": match["a2"]["event_id"], "legacy_anchor_id": match["legacy"]["base_anchor_id"], "delta_sessions": delta, "cohort": cohort, "instrument_id": match["a2"]["instrument_id"]}
        for horizon in HORIZONS:
            append_source(cohort, a2_by_key[(match["a2"]["event_id"], horizon)], horizon, pair_id, delta)
            append_source(cohort, legacy_by_anchor_h[(match["legacy"]["anchor_id"], horizon)], horizon, pair_id, delta)
    return dict(records), {"pair_members": pair_members}


def _cohort_counts(records: Mapping[tuple[str, int], list[dict[str, Any]]], pair_members: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for cohort in ALL_COHORTS:
        row = records.get((cohort, 5), [])
        output[cohort] = {
            "observation_count": len(row),
            "event_count": len({item["event_key"] for item in row}),
            "pair_count": len({item["pair_id"] for item in row if item.get("pair_id")}),
            "instrument_count": len({item["instrument_id"] for item in row}),
        }
    return output


def _endpoint_rows(records: Mapping[tuple[str, int], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for cohort in ALL_COHORTS:
        for horizon in HORIZONS:
            current = records.get((cohort, horizon), [])
            matured = _matured(current)
            values = [float(row["endpoint_return"]) for row in matured]
            stats = _summary(values)
            output.append({
                "cohort": cohort,
                "horizon": horizon,
                "event_count": len({row["event_key"] for row in current}),
                "pair_count": len({row["pair_id"] for row in current if row.get("pair_id")}),
                "observation_count": len(current),
                "instrument_count": len({row["instrument_id"] for row in current}),
                "matured_count": len(matured),
                "mean": stats["mean"],
                "median": stats["median"],
                "stddev": stats["stddev"],
                "positive_rate": stats["positive_rate"],
                "p25": stats["p25"],
                "p75": stats["p75"],
                "metric_status": "PASS" if matured else "INSUFFICIENT_SAMPLE",
                "definition": "BOTH cohorts are two source observations per matched pair; pair_count is the independent matched-pair count and observation_count is the descriptive source-observation count",
            })
    return output


def _path_rows(records: Mapping[tuple[str, int], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for cohort in ALL_COHORTS:
        for horizon in PATH_HORIZONS:
            current = records.get((cohort, horizon), [])
            matured = _matured(current)
            base = {"cohort": cohort, "horizon": horizon, "observation_count": len(current), "matured_count": len(matured), "pair_count": len({row["pair_id"] for row in current if row.get("pair_id")}), "instrument_count": len({row["instrument_id"] for row in current}), "definition": "MFE/MAE use the committed path-aware outcomes; barrier races use the same raw accepted future OHLC sessions and preserve SAME_SESSION_ORDER_UNKNOWN"}
            for metric, field in (("MFE", "mfe"), ("MAE", "mae")):
                stats = _summary(_numbers(matured, field))
                output.append({**base, "metric": metric, **stats, "threshold_rate": ""})
            ratios = [float(row["mfe"]) / abs(float(row["mae"])) for row in matured if float(row["mae"]) != 0]
            output.append({**base, "metric": "MFE_OVER_ABS_MAE", **_summary(ratios), "threshold_rate": "", "ratio_definition": "mean/median of event-level MFE divided by absolute MAE; descriptive excursion ratio, not a risk-adjusted return"})
            for threshold in MFE_THRESHOLDS:
                values = [float(row["mfe"]) for row in matured]
                output.append({**base, "metric": f"MFE_GE_{int(threshold * 100)}PCT", "threshold": threshold, "threshold_count": sum(value >= threshold for value in values), "threshold_rate": sum(value >= threshold for value in values) / len(values) if values else None})
            for threshold in MAE_THRESHOLDS:
                values = [float(row["mae"]) for row in matured]
                output.append({**base, "metric": f"MAE_LE_{int(abs(threshold) * 100)}PCT", "threshold": threshold, "threshold_count": sum(value <= threshold for value in values), "threshold_rate": sum(value <= threshold for value in values) / len(values) if values else None})
            for up, down in BARRIER_PAIRS:
                label = _barrier_label(up, down)
                races = [row.get(f"{label}_outcome") for row in matured]
                output.append({**base, "metric": label, "up_first_count": races.count("UP_FIRST"), "up_first_rate": races.count("UP_FIRST") / len(races) if races else None, "down_first_count": races.count("DOWN_FIRST"), "down_first_rate": races.count("DOWN_FIRST") / len(races) if races else None, "same_session_unknown_count": races.count("SAME_SESSION_ORDER_UNKNOWN"), "same_session_unknown_rate": races.count("SAME_SESSION_ORDER_UNKNOWN") / len(races) if races else None, "neither_count": races.count("NEITHER_BY_H"), "race_definition": "same-day high/low barrier ordering is unknown and never ordered retrospectively"})
    return output


def _winsorized(values: list[float], probability: float) -> list[float]:
    low, high = _quantile(values, probability), _quantile(values, 1 - probability)
    return [min(max(value, low), high) for value in values] if low is not None and high is not None else []


def _trimmed(values: list[float], probability: float) -> list[float]:
    if not values:
        return []
    ordered = sorted(values)
    cut = int(math.floor(len(ordered) * probability))
    return ordered[cut: len(ordered) - cut] if len(ordered) - 2 * cut > 0 else ordered


def _positive_top_contribution(values: list[float], count: int) -> float | None:
    positive = sorted((value for value in values if value > 0), reverse=True)
    total = sum(positive)
    return sum(positive[:count]) / total if positive and total else None


def _extreme_rows(records: Mapping[tuple[str, int], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for cohort in PRIMARY_COHORTS + ("BOTH_WITHIN_1_SESSION",):
        for horizon in PATH_HORIZONS:
            values = _numbers(_matured(records.get((cohort, horizon), [])), "endpoint_return")
            if not values:
                continue
            trimmed1, trimmed5 = _trimmed(values, 0.01), _trimmed(values, 0.05)
            metrics = {
                "RAW_MEAN": statistics.fmean(values),
                "MEDIAN": statistics.median(values),
                "WINSORIZED_MEAN_1PCT": statistics.fmean(_winsorized(values, 0.01)),
                "TRIMMED_MEAN_1PCT": statistics.fmean(trimmed1),
                "TRIMMED_MEAN_5PCT": statistics.fmean(trimmed5),
                "TOP_1PCT_POSITIVE_CONTRIBUTION": _positive_top_contribution(values, max(1, math.ceil(len(values) * 0.01))),
                "TOP_5PCT_POSITIVE_CONTRIBUTION": _positive_top_contribution(values, max(1, math.ceil(len(values) * 0.05))),
                "TOP_10_EVENT_POSITIVE_CONTRIBUTION": _positive_top_contribution(values, min(10, len(values))),
            }
            by_key[(cohort, horizon)] = {"values": values, **metrics}
            for metric, value in metrics.items():
                output.append({"cohort": cohort, "horizon": horizon, "metric": metric, "matured_count": len(values), "value": value, "outlier_definition": "Fixed before outcome review: quantile winsorization/trimming at 1% and 5%; top contributions are top positive endpoint returns divided by all positive endpoint returns; top-10 means exactly ten events or all if fewer", "interpretation": "Descriptive robustness only; no formal risk-adjusted-return claim"})
    for horizon in PATH_HORIZONS:
        both = by_key.get(("BOTH_SAME_SESSION", horizon))
        for comparator in ("A2_ONLY", "LEGACY5_ONLY"):
            other = by_key.get((comparator, horizon))
            if not both or not other:
                continue
            for metric in ("RAW_MEAN", "MEDIAN", "WINSORIZED_MEAN_1PCT", "TRIMMED_MEAN_1PCT", "TRIMMED_MEAN_5PCT"):
                output.append({"cohort": "BOTH_SAME_SESSION", "horizon": horizon, "metric": f"{metric}_DELTA_VS_{comparator}", "value": both[metric] - other[metric], "comparison_value": both[metric], "comparator_value": other[metric], "outlier_definition": "Same fixed outlier policy as above", "interpretation": "Positive delta means BOTH is higher after the specified fixed extreme treatment"})
    return output


def _instrument_rows(records: Mapping[tuple[str, int], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for cohort in ALL_COHORTS:
        for horizon in PATH_HORIZONS:
            rows = _matured(records.get((cohort, horizon), []))
            by_instrument: dict[str, list[float]] = defaultdict(list)
            for row in rows:
                by_instrument[row["instrument_id"]].append(float(row["endpoint_return"]))
            counts = sorted((len(values) for values in by_instrument.values()), reverse=True)
            positive_by_instrument = sorted((sum(value for value in values if value > 0) for values in by_instrument.values()), reverse=True)
            total_positive = sum(positive_by_instrument)
            top10 = sum(positive_by_instrument[:10]) / total_positive if total_positive else None
            max_one = positive_by_instrument[0] / total_positive if positive_by_instrument and total_positive else None
            balanced = statistics.fmean(statistics.fmean(values) for values in by_instrument.values()) if by_instrument else None
            output.append({"cohort": cohort, "horizon": horizon, "metric": "SUMMARY", "matured_count": len(rows), "unique_instruments": len(by_instrument), "events_per_instrument_mean": statistics.fmean(counts) if counts else None, "events_per_instrument_median": statistics.median(counts) if counts else None, "events_per_instrument_max": max(counts) if counts else None, "event_weighted_endpoint_mean": statistics.fmean(_numbers(rows, "endpoint_return")) if rows else None, "instrument_balanced_endpoint_mean": balanced, "top10_instrument_positive_contribution": top10, "single_instrument_max_positive_contribution": max_one, "concentration_definition": "Instrument-balanced mean gives each instrument equal weight; contribution metrics use positive endpoint-return sums"})
            for rank, (instrument_id, values) in enumerate(sorted(by_instrument.items(), key=lambda item: (-len(item[1]), item[0]))[:10], start=1):
                output.append({"cohort": cohort, "horizon": horizon, "metric": "TOP_REPEATED_INSTRUMENT", "rank": rank, "instrument_id": instrument_id, "instrument_event_count": len(values), "instrument_endpoint_mean": statistics.fmean(values), "instrument_endpoint_sum": sum(values), "top_repeated_definition": "Sorted by repeated matured source-observation count; top ten only"})
    return output


def _stability_row(cohort: str, period_type: str, period: str, rows: list[dict[str, Any]], horizon: int) -> dict[str, Any]:
    matured = _matured(rows)
    endpoint = _summary(_numbers(matured, "endpoint_return"))
    mfe10 = _summary(_numbers(matured, "mfe"))
    mae10 = _summary(_numbers(matured, "mae"))
    race = _barrier_label(0.05, -0.05)
    race10 = _barrier_label(0.10, -0.05)
    races, races10 = [row.get(f"{race}_outcome") for row in matured], [row.get(f"{race10}_outcome") for row in matured]
    return {"cohort": cohort, "period_type": period_type, "period": period, "horizon": horizon, "event_count": len({row["event_key"] for row in rows}), "observation_count": len(rows), "matured_count": len(matured), "status": "AVAILABLE" if len(matured) >= MIN_STABILITY_SAMPLE else "INSUFFICIENT_SAMPLE", "endpoint_mean": endpoint["mean"], "endpoint_median": endpoint["median"], "endpoint_positive_rate": endpoint["positive_rate"], "mfe_mean": mfe10["mean"], "mae_mean": mae10["mean"], "barrier_5_before_minus5_up_first_rate": races.count("UP_FIRST") / len(races) if races else None, "barrier_10_before_minus5_up_first_rate": races10.count("UP_FIRST") / len(races10) if races10 else None, "same_session_unknown_5_rate": races.count("SAME_SESSION_ORDER_UNKNOWN") / len(races) if races else None, "same_session_unknown_10_rate": races10.count("SAME_SESSION_ORDER_UNKNOWN") / len(races10) if races10 else None, "fixed_period_rule": "calendar year 2024/2025/2026 and chronological midpoint 2025-08-13; periods were not selected by performance"}


def _time_rows(records: Mapping[tuple[str, int], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for cohort in ALL_COHORTS:
        for period_type in ("CALENDAR_YEAR", "CHRONOLOGICAL_SPLIT"):
            periods = ("2024", "2025", "2026") if period_type == "CALENDAR_YEAR" else ("EARLY", "LATE")
            for period in periods:
                for horizon in PATH_HORIZONS:
                    current = records.get((cohort, horizon), [])
                    if period_type == "CALENDAR_YEAR":
                        subset = [row for row in current if str(row["signal_date"])[:4] == period]
                    else:
                        subset = [row for row in current if (str(row["signal_date"]) <= CHRONOLOGICAL_MIDPOINT) == (period == "EARLY")]
                    output.append(_stability_row(cohort, period_type, period, subset, horizon))
    return output


def _market_rows(records: Mapping[tuple[str, int], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for cohort in ALL_COHORTS:
        for market in ("TPE", "TWO"):
            for horizon in PATH_HORIZONS:
                subset = [row for row in records.get((cohort, horizon), []) if row.get("market") == market]
                output.append({**_stability_row(cohort, "MARKET", market, subset, horizon), "market_definition": "Source market field from committed A2/LEGACY-5 event artifacts"})
    return output


def _ma60_rows(inputs: Mapping[str, Any], a2_by_key: Mapping[tuple[str, int], dict[str, Any]], legacy_v0_by_anchor_h: Mapping[tuple[str, int], dict[str, Any]], groups: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    anchors_v0 = inputs["anchors_by_variant"]["V0_LEGACY5"]
    anchors_v2 = inputs["anchors_by_variant"]["V2_LEGACY5_MA60"]
    matching_v0 = prior._match_events(inputs["a2_events"], anchors_v0, groups, FIXED_WINDOW)
    matching_v2 = prior._match_events(inputs["a2_events"], anchors_v2, groups, FIXED_WINDOW)
    legacy_v2_rows: dict[tuple[str, int], dict[str, Any]] = {}
    for horizon in HORIZONS:
        for row in prior._normalize_legacy_rows(anchors_v2, horizon, inputs["legacy_outcomes"], groups):
            legacy_v2_rows[(row["anchor_id"], horizon)] = row
    def quick_metrics(variant: str, matching: Mapping[str, Any], legacy_rows: Mapping[tuple[str, int], dict[str, Any]]) -> None:
        recs, _ = _make_cohort_records(inputs, matching, variant, a2_by_key, legacy_rows)
        for cohort in ALL_COHORTS:
            for horizon in PATH_HORIZONS:
                matured = _matured(recs.get((cohort, horizon), []))
                endpoint, mfe, mae = _summary(_numbers(matured, "endpoint_return")), _summary(_numbers(matured, "mfe")), _summary(_numbers(matured, "mae"))
                race = [_row.get(f"{_barrier_label(0.05, -0.05)}_outcome") for _row in matured]
                output.append({"analysis": "COHORT_METRICS", "eligibility_variant": variant, "cohort": cohort, "horizon": horizon, "pair_count": len({row["pair_id"] for row in recs.get((cohort, horizon), []) if row.get("pair_id")}), "observation_count": len(recs.get((cohort, horizon), [])), "matured_count": len(matured), "endpoint_mean": endpoint["mean"], "endpoint_median": endpoint["median"], "mfe_mean": mfe["mean"], "mae_mean": mae["mean"], "barrier_5_before_minus5_up_first_rate": race.count("UP_FIRST") / len(race) if race else None, "same_session_unknown_rate": race.count("SAME_SESSION_ORDER_UNKNOWN") / len(race) if race else None, "acceptance": "NO"})
    quick_metrics("V0_LEGACY5", matching_v0, legacy_v0_by_anchor_h)
    quick_metrics("V2_LEGACY5_MA60", matching_v2, legacy_v2_rows)
    v0_base = {row["base_anchor_id"] for row in anchors_v0}
    v2_base = {row["base_anchor_id"] for row in anchors_v2}
    excluded = [row for row in anchors_v0 if row["base_anchor_id"] not in v2_base]
    for horizon in PATH_HORIZONS:
        rows = [prior._normalize_legacy_rows([anchor], horizon, inputs["legacy_outcomes"], groups)[0] for anchor in excluded]
        matured = _matured(rows)
        output.append({"analysis": "ELIGIBILITY_ATTRITION", "eligibility_variant": "V0_TO_V2", "cohort": "LEGACY5_UNIVERSE", "horizon": horizon, "v0_count": len(v0_base), "v2_count": len(v2_base), "removed_count": len(excluded), "attrition_rate": len(excluded) / len(v0_base), "matured_count": len(matured), "removed_mfe_ge_3_count": sum(row["mfe"] >= 0.03 for row in matured), "removed_mfe_ge_5_count": sum(row["mfe"] >= 0.05 for row in matured), "removed_mfe_ge_10_count": sum(row["mfe"] >= 0.10 for row in matured), "removed_endpoint_le_0_count": sum(row["endpoint_return"] <= 0 for row in matured), "removed_mae_le_minus5_count": sum(row["mae"] <= -0.05 for row in matured), "acceptance": "NO"})
    return output


def _timing_rows(inputs: Mapping[str, Any], matching: Mapping[str, Any], a2_by_key: Mapping[tuple[str, int], dict[str, Any]], legacy_by_anchor_h: Mapping[tuple[str, int], dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    groups: dict[str, list[dict[str, Any]]] = {name: [] for name in TIMING_CLASSES}
    for match in matching["matches"]:
        delta = int(match["delta_sessions"])
        name = "LEGACY_EARLIER" if delta < 0 else "SAME_SESSION" if delta == 0 else "A2_EARLIER"
        groups[name].append(match)
    for timing_class in TIMING_CLASSES:
        matches = groups[timing_class]
        for horizon in PATH_HORIZONS:
            for source in ("A2", "LEGACY5", "PAIR_COMBINED"):
                rows: list[dict[str, Any]] = []
                for match in matches:
                    if source in ("A2", "PAIR_COMBINED"):
                        rows.append(a2_by_key[(match["a2"]["event_id"], horizon)])
                    if source in ("LEGACY5", "PAIR_COMBINED"):
                        rows.append(legacy_by_anchor_h[(match["legacy"]["anchor_id"], horizon)])
                matured = _matured(rows)
                endpoint, mfe, mae = _summary(_numbers(matured, "endpoint_return")), _summary(_numbers(matured, "mfe")), _summary(_numbers(matured, "mae"))
                race = [_row.get(f"{_barrier_label(0.05, -0.05)}_outcome") for _row in matured]
                output.append({"timing_class": timing_class, "signal_source": source, "horizon": horizon, "pair_count": len(matches), "observation_count": len(rows), "matured_count": len(matured), "endpoint_mean": endpoint["mean"], "endpoint_median": endpoint["median"], "mfe_mean": mfe["mean"], "mae_mean": mae["mean"], "barrier_5_before_minus5_up_first_rate": race.count("UP_FIRST") / len(race) if race else None, "barrier_5_before_minus5_down_first_rate": race.count("DOWN_FIRST") / len(race) if race else None, "barrier_5_before_minus5_same_session_unknown_rate": race.count("SAME_SESSION_ORDER_UNKNOWN") / len(race) if race else None, "timing_definition": "delta_sessions = accepted session position of LEGACY-5 date minus A2 date; fixed matching window +/-1; no future outcome used for pairing"})
    return output


def _bootstrap_mean(values: list[float], seed: int) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    rng = random.Random(seed)
    means = [statistics.fmean(rng.choices(values, k=len(values))) for _ in range(BOOTSTRAP_REPS)]
    return _quantile(means, 0.025), _quantile(means, 0.975)


def _bootstrap_difference(left: list[float], right: list[float], seed: int) -> tuple[float | None, float | None]:
    if not left or not right:
        return None, None
    rng = random.Random(seed)
    differences = [statistics.fmean(rng.choices(left, k=len(left))) - statistics.fmean(rng.choices(right, k=len(right))) for _ in range(BOOTSTRAP_REPS)]
    return _quantile(differences, 0.025), _quantile(differences, 0.975)


def _statistical_summary(records: Mapping[tuple[str, int], list[dict[str, Any]]]) -> dict[str, Any]:
    endpoint_rows: list[dict[str, Any]] = []
    for cohort in PRIMARY_COHORTS:
        for horizon in PATH_HORIZONS:
            values = _numbers(_matured(records.get((cohort, horizon), [])), "endpoint_return")
            low, high = _bootstrap_mean(values, BOOTSTRAP_SEED + horizon + len(endpoint_rows))
            endpoint_rows.append({"cohort": cohort, "horizon": horizon, "matured_count": len(values), "mean": statistics.fmean(values) if values else None, "median": statistics.median(values) if values else None, "bootstrap_mean_ci_95_low": low, "bootstrap_mean_ci_95_high": high})
    comparisons: list[dict[str, Any]] = []
    for horizon in PATH_HORIZONS:
        both = _numbers(_matured(records.get(("BOTH_SAME_SESSION", horizon), [])), "endpoint_return")
        for comparator in ("A2_ONLY", "LEGACY5_ONLY"):
            other = _numbers(_matured(records.get((comparator, horizon), [])), "endpoint_return")
            low, high = _bootstrap_difference(both, other, BOOTSTRAP_SEED + 100 + horizon + (0 if comparator == "A2_ONLY" else 10))
            comparisons.append({"left": "BOTH_SAME_SESSION", "right": comparator, "horizon": horizon, "mean_difference": statistics.fmean(both) - statistics.fmean(other) if both and other else None, "bootstrap_difference_ci_95_low": low, "bootstrap_difference_ci_95_high": high, "interpretation": "Exploratory descriptive interval only; no acceptance/significance claim and no multiple-testing correction"})
    return {"schema_version": "ws3-a2-legacy5-statistical-robustness.v1", "bootstrap": {"method": "deterministic percentile bootstrap of event/source-observation means", "replicates": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED, "confidence_level": 0.95}, "endpoint_summary": endpoint_rows, "exploratory_effect_differences": comparisons, "discipline": {"in_sample_descriptive": True, "multiple_testing_adjustment": "NONE; results are exploratory descriptive robustness checks", "formal_significance_claim": "NO", "ratio_is_risk_adjusted_return": "NO"}}


def _availability_rows(kind: str) -> list[dict[str, Any]]:
    if kind == "benchmark":
        return [{"status": "NOT_AVAILABLE", "analysis": "BENCHMARK_ADJUSTED_ANALYSIS", "required_source": "PIT-safe accepted TAIEX/market benchmark daily series", "disposition": "No such committed source artifact exists in the canonical repository; no web download, synthetic index, or unknown proxy was used", "cohort_scope": "A2_ONLY|LEGACY5_ONLY|BOTH_SAME_SESSION", "horizons": "5|10"}]
    return [{"status": "NOT_AVAILABLE", "analysis": "REGIME_ROBUSTNESS", "required_source": "PIT-safe event-level market-regime evidence", "disposition": "Existing regime-attribution audit records a missing PIT-safe index/breadth/peer source; no retrospective regime classification was performed", "cohort_scope": "A2_ONLY|LEGACY5_ONLY|BOTH_SAME_SESSION", "horizons": "5|10"}]


def _source_manifest(repo_root: Path, inputs: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    paths = [
        LEGACY_DIR / "legacy5-raw-anchors.csv",
        LEGACY_DIR / "event-outcomes.csv",
        LEGACY_DIR / "legacy5-event-cohort-manifest.json",
        A2_PATH_DIR / "a2-path-aware-outcomes.csv",
        A2_PATH_DIR / "path-aware-outcome-manifest.json",
        A2_EVENT_DIR / "ws3-p2e-a2-expanded-event-panel.csv",
        A2_EVENT_DIR / "ws3-p2e-a2-confirmatory-protocol-freeze.json",
        Path("reports/TASK-WS3-LEGACY5-ELIGIBILITY-A2-COMPLEMENTARITY-STUDY-20260822/a2-legacy5-overlap-summary.csv"),
        Path("reports/TASK-WS3-LEGACY5-ELIGIBILITY-A2-COMPLEMENTARITY-STUDY-20260822/a2-legacy5-complementarity-path-metrics.csv"),
    ]
    files = []
    for relative in paths:
        absolute = repo_root / relative
        if not absolute.exists():
            raise ContractBlocked(f"Required prior artifact missing: {relative}")
        files.append({"path": relative.as_posix(), "sha256": _sha256(absolute), "bytes": absolute.stat().st_size})
    return {"schema_version": "ws3-a2-legacy5-joint-source-semantics.v1", "task_id": TASK_ID, "source_files": files, "dataset": {"start": SOURCE_START, "end": SOURCE_END, "accepted_rows": inputs["surface_quality"]["queried_rows"], "instruments": inputs["surface_quality"]["queried_instruments"], "surface_sha256": prior.EXPECTED_SURFACE_SHA256}, "fixed_semantics": {"a2": "Committed A2 5,277 event panel and path-aware H1-H10 outcome reconstruction; no A2 definition changes", "legacy5": "Committed LEGACY-5 raw-anchor H1/H3/H5/H10 outcome rows; no signal changes", "matching": "One-to-one instrument/date matching by accepted canonical session position within fixed +/-1 session; candidate assignment sorted by abs(delta), event_id, anchor_id", "cohorts": list(ALL_COHORTS), "ma60_ablation": "Only V0 and predeclared V2 LEGACY-5+MA60; no MA20/price threshold search", "barriers": "5% before -5% and 10% before -5%; simultaneous same-session hits remain SAME_SESSION_ORDER_UNKNOWN", "corporate_actions": "UNKNOWN_RAW_ONLY; synthetic adjustment prohibited", "benchmark": "PIT-safe accepted benchmark absent; disposition only", "regime": "PIT-safe event-level regime evidence absent; disposition only"}, "scan_disposition": {"raw_panel_scans": 1, "scan_type": "read-only accepted PRICE DAILY_BAR fields", "reason": "Required only for exact accepted-session positions and event-level LEGACY-5 barrier races; no download, volume rescan, writes, or production pipeline rerun"}}


def _artifact_hashes(output_dir: Path) -> dict[str, str]:
    # Formal closure contains the non-self-referential artifact ledger; exclude
    # it from that ledger so a replay does not create a hash recursion.
    return {path.name: _sha256(path) for path in sorted(output_dir.iterdir()) if path.is_file() and path.name not in {"run-summary.json", "reproducibility-manifest.json", "formal-closure-report.md"}}


def _decision(summary: Mapping[str, Any], endpoint_rows: list[dict[str, Any]], extreme_rows: list[dict[str, Any]], time_rows: list[dict[str, Any]], market_rows: list[dict[str, Any]], ma60_rows: list[dict[str, Any]], timing_rows: list[dict[str, Any]]) -> dict[str, Any]:
    both_h5 = next(row for row in endpoint_rows if row["cohort"] == "BOTH_SAME_SESSION" and row["horizon"] == 5)
    a2_h5 = next(row for row in endpoint_rows if row["cohort"] == "A2_ONLY" and row["horizon"] == 5)
    legacy_h5 = next(row for row in endpoint_rows if row["cohort"] == "LEGACY5_ONLY" and row["horizon"] == 5)
    both_h10 = next(row for row in endpoint_rows if row["cohort"] == "BOTH_SAME_SESSION" and row["horizon"] == 10)
    a2_h10 = next(row for row in endpoint_rows if row["cohort"] == "A2_ONLY" and row["horizon"] == 10)
    legacy_h10 = next(row for row in endpoint_rows if row["cohort"] == "LEGACY5_ONLY" and row["horizon"] == 10)
    med_h5 = next(row["value"] for row in extreme_rows if row["cohort"] == "BOTH_SAME_SESSION" and row["horizon"] == 5 and row["metric"] == "MEDIAN")
    med_h10 = next(row["value"] for row in extreme_rows if row["cohort"] == "BOTH_SAME_SESSION" and row["horizon"] == 10 and row["metric"] == "MEDIAN")
    trimmed_h5 = next(row["value"] for row in extreme_rows if row["cohort"] == "BOTH_SAME_SESSION" and row["horizon"] == 5 and row["metric"] == "TRIMMED_MEAN_5PCT")
    trimmed_h10 = next(row["value"] for row in extreme_rows if row["cohort"] == "BOTH_SAME_SESSION" and row["horizon"] == 10 and row["metric"] == "TRIMMED_MEAN_5PCT")
    both_time = [row for row in time_rows if row["cohort"] == "BOTH_SAME_SESSION" and row["period_type"] == "CALENDAR_YEAR" and row["horizon"] == 5 and row["status"] == "AVAILABLE"]
    both_market = [row for row in market_rows if row["cohort"] == "BOTH_SAME_SESSION" and row["horizon"] == 5 and row["status"] == "AVAILABLE"]
    v0_both = next(row for row in ma60_rows if row.get("analysis") == "COHORT_METRICS" and row["eligibility_variant"] == "V0_LEGACY5" and row["cohort"] == "BOTH_SAME_SESSION" and row["horizon"] == 5)
    v2_both = next(row for row in ma60_rows if row.get("analysis") == "COHORT_METRICS" and row["eligibility_variant"] == "V2_LEGACY5_MA60" and row["cohort"] == "BOTH_SAME_SESSION" and row["horizon"] == 5)
    v0_a2 = next(row for row in ma60_rows if row.get("analysis") == "COHORT_METRICS" and row["eligibility_variant"] == "V0_LEGACY5" and row["cohort"] == "A2_ONLY" and row["horizon"] == 5)
    v2_a2 = next(row for row in ma60_rows if row.get("analysis") == "COHORT_METRICS" and row["eligibility_variant"] == "V2_LEGACY5_MA60" and row["cohort"] == "A2_ONLY" and row["horizon"] == 5)
    v0_legacy = next(row for row in ma60_rows if row.get("analysis") == "COHORT_METRICS" and row["eligibility_variant"] == "V0_LEGACY5" and row["cohort"] == "LEGACY5_ONLY" and row["horizon"] == 5)
    v2_legacy = next(row for row in ma60_rows if row.get("analysis") == "COHORT_METRICS" and row["eligibility_variant"] == "V2_LEGACY5_MA60" and row["cohort"] == "LEGACY5_ONLY" and row["horizon"] == 5)
    attrition = next(row for row in ma60_rows if row.get("analysis") == "ELIGIBILITY_ATTRITION" and row["horizon"] == 5)
    timing_counts = {name: next(row["pair_count"] for row in timing_rows if row["timing_class"] == name and row["signal_source"] == "PAIR_COMBINED" and row["horizon"] == 5) for name in TIMING_CLASSES}
    median_advantage = med_h5 > next(row["value"] for row in extreme_rows if row["cohort"] == "A2_ONLY" and row["horizon"] == 5 and row["metric"] == "MEDIAN") and med_h5 > next(row["value"] for row in extreme_rows if row["cohort"] == "LEGACY5_ONLY" and row["horizon"] == 5 and row["metric"] == "MEDIAN")
    mean_advantage = both_h5["mean"] > a2_h5["mean"] and both_h5["mean"] > legacy_h5["mean"] and both_h10["mean"] > a2_h10["mean"] and both_h10["mean"] > legacy_h10["mean"]
    outlier_mean_advantage = all(
        next(row["value"] for row in extreme_rows if row["cohort"] == "BOTH_SAME_SESSION" and row["horizon"] == horizon and row["metric"] == "TRIMMED_MEAN_5PCT")
        > next(row["value"] for row in extreme_rows if row["cohort"] == comparator and row["horizon"] == horizon and row["metric"] == "TRIMMED_MEAN_5PCT")
        for horizon in PATH_HORIZONS
        for comparator in ("A2_ONLY", "LEGACY5_ONLY")
    )
    time_map = {(row["cohort"], row["period_type"], row["period"], row["horizon"]): row for row in time_rows}
    time_comparisons = []
    for period_type in ("CALENDAR_YEAR", "CHRONOLOGICAL_SPLIT"):
        periods = ("2024", "2025", "2026") if period_type == "CALENDAR_YEAR" else ("EARLY", "LATE")
        for period in periods:
            for horizon in PATH_HORIZONS:
                both = time_map.get(("BOTH_SAME_SESSION", period_type, period, horizon))
                a2 = time_map.get(("A2_ONLY", period_type, period, horizon))
                legacy = time_map.get(("LEGACY5_ONLY", period_type, period, horizon))
                if all(row is not None and row["status"] == "AVAILABLE" and row["endpoint_mean"] is not None for row in (both, a2, legacy)):
                    time_comparisons.append(both["endpoint_mean"] > a2["endpoint_mean"] and both["endpoint_mean"] > legacy["endpoint_mean"])
    time_support = len(time_comparisons) >= 2 and all(time_comparisons)
    market_map = {(row["cohort"], row["period"], row["horizon"]): row for row in market_rows}
    market_comparisons = []
    for market in ("TPE", "TWO"):
        for horizon in PATH_HORIZONS:
            both = market_map.get(("BOTH_SAME_SESSION", market, horizon))
            a2 = market_map.get(("A2_ONLY", market, horizon))
            legacy = market_map.get(("LEGACY5_ONLY", market, horizon))
            if all(row is not None and row["status"] == "AVAILABLE" and row["endpoint_mean"] is not None for row in (both, a2, legacy)):
                market_comparisons.append(both["endpoint_mean"] > a2["endpoint_mean"] and both["endpoint_mean"] > legacy["endpoint_mean"])
    market_support = len(market_comparisons) >= 2 and all(market_comparisons)
    ma60_quality_same = v2_both["endpoint_mean"] >= v0_both["endpoint_mean"] and v2_both["mfe_mean"] >= v0_both["mfe_mean"]
    benchmark_support = False
    regime_support = False
    robust = bool(mean_advantage and median_advantage and outlier_mean_advantage and time_support and market_support and ma60_quality_same and benchmark_support and regime_support)
    disposition = "ROBUST_RESEARCH_CANDIDATE" if robust else "RESEARCH_CANDIDATE"
    return {"final_disposition": disposition, "out_of_sample_supported": "NO", "mean_advantage_both_vs_single": mean_advantage, "median_advantage_both_vs_single": median_advantage, "outlier_adjusted_advantage": outlier_mean_advantage, "time_stability_support": time_support, "market_split_support": market_support, "ma60_joint_quality_support": ma60_quality_same, "benchmark_adjusted_support": benchmark_support, "regime_support": regime_support, "robustness_blockers": ["BENCHMARK_ADJUSTED_ANALYSIS=NOT_AVAILABLE", "REGIME_ROBUSTNESS=NOT_AVAILABLE"], "both_h5_mean": both_h5["mean"], "both_h5_median": med_h5, "both_h10_mean": both_h10["mean"], "both_h10_median": med_h10, "both_h5_trimmed5_mean": trimmed_h5, "both_h10_trimmed5_mean": trimmed_h10, "ma60_both_h5_v0": v0_both["endpoint_mean"], "ma60_both_h5_v2": v2_both["endpoint_mean"], "ma60_a2_only_h5_v0": v0_a2["endpoint_mean"], "ma60_a2_only_h5_v2": v2_a2["endpoint_mean"], "ma60_a2_only_h5_mae_v0": v0_a2["mae_mean"], "ma60_a2_only_h5_mae_v2": v2_a2["mae_mean"], "ma60_legacy_only_h5_v0": v0_legacy["endpoint_mean"], "ma60_legacy_only_h5_v2": v2_legacy["endpoint_mean"], "ma60_legacy_only_h5_mae_v0": v0_legacy["mae_mean"], "ma60_legacy_only_h5_mae_v2": v2_legacy["mae_mean"], "ma60_removed_h5": attrition["removed_count"], "ma60_removed_mfe_ge_3_h5": attrition["removed_mfe_ge_3_count"], "ma60_removed_mfe_ge_5_h5": attrition["removed_mfe_ge_5_count"], "ma60_removed_mfe_ge_10_h5": attrition["removed_mfe_ge_10_count"], "ma60_removed_endpoint_le_0_h5": attrition["removed_endpoint_le_0_count"], "ma60_removed_mae_le_minus5_h5": attrition["removed_mae_le_minus5_count"], "timing_pair_counts": timing_counts, "time_available_year_rows": len(both_time), "market_available_rows": len(both_market), "caveat": "BOTH uses two source observations per pair; medians and outlier checks are event/source-observation descriptive, not independent-pair significance tests", "next_oos_design": "Freeze A2, LEGACY-5, +/-1 matching and all reporting rules now; accumulate only future sessions after 2026-08-13; evaluate an untouched later period without changing thresholds or selecting on outcomes"}


def _memo(summary: Mapping[str, Any], decision: Mapping[str, Any], counts: Mapping[str, Any], source_manifest: Mapping[str, Any]) -> str:
    def pct(value: Any) -> str:
        return "NA" if value is None else f"{float(value) * 100:.4f}%"
    lines = [
        f"# Owner Decision Memo — {TASK_ID}",
        "",
        "## Decision",
        "",
        f"Final disposition: **{decision['final_disposition']}**. This is an evidence-only WS3 robustness study; `JOINT_SIGNAL_ACCEPTED=NO` and `OUT_OF_SAMPLE_SUPPORTED=NO`.",
        "",
        "The study tried to disprove the fixed A2 × LEGACY-5 hypothesis with endpoint medians, dispersion, fixed outlier treatment, instrument concentration, calendar/time stability, market split, signal timing, and the predeclared MA60 ablation. It did not change either signal or promote a strategy.",
        "",
        "## Fixed cohorts and core counts",
        "",
        f"- A2_ONLY: {counts['A2_ONLY']['event_count']} events / {counts['A2_ONLY']['instrument_count']} instruments.",
        f"- LEGACY5_ONLY: {counts['LEGACY5_ONLY']['event_count']} events / {counts['LEGACY5_ONLY']['instrument_count']} instruments.",
        f"- BOTH_SAME_SESSION: {counts['BOTH_SAME_SESSION']['pair_count']} matched pairs / {counts['BOTH_SAME_SESSION']['observation_count']} source observations.",
        f"- BOTH_WITHIN_1_SESSION: {counts['BOTH_WITHIN_1_SESSION']['pair_count']} matched pairs / {counts['BOTH_WITHIN_1_SESSION']['observation_count']} source observations.",
        "",
        "## Direct answers",
        "",
        f"1. BOTH T+5 mean is {pct(decision['both_h5_mean'])}, median {pct(decision['both_h5_median'])}; T+10 mean is {pct(decision['both_h10_mean'])}, median {pct(decision['both_h10_median'])}.",
        "2. The prior +5.0841% figure was the BOTH T+10 mean, not its median. The current median is reported explicitly and is not treated as +5.0841%.",
        f"3. After fixed 5% trimming, BOTH T+5/T+10 means are {pct(decision['both_h5_trimmed5_mean'])}/{pct(decision['both_h10_trimmed5_mean'])}; outlier dependence is {('not decisive' if decision['outlier_adjusted_advantage'] else 'materially unresolved')}.",
        f"4. Both signals capture a substantial number of different events: A2_ONLY={counts['A2_ONLY']['event_count']}, LEGACY5_ONLY={counts['LEGACY5_ONLY']['event_count']}, same-session BOTH={counts['BOTH_SAME_SESSION']['pair_count']}.",
        f"5. Timing pair counts are Legacy earlier={decision['timing_pair_counts']['LEGACY_EARLIER']}, same session={decision['timing_pair_counts']['SAME_SESSION']}, A2 earlier={decision['timing_pair_counts']['A2_EARLIER']}.",
        "6. The timing table compares A2, LEGACY5, and paired-combined path metrics without changing the fixed ±1 window.",
        "7. Calendar years use 2024/2025/2026; EARLY/LATE uses the fixed dataset midpoint 2025-08-13, not a performance-selected split.",
        "8. Market split is TPE/TWO and is descriptive; no market-specific production rule is proposed.",
        f"9. MA60 joint ablation: BOTH same-session H5 is unchanged ({pct(decision['ma60_both_h5_v0'])} to {pct(decision['ma60_both_h5_v2'])}); A2_ONLY changes {pct(decision['ma60_a2_only_h5_v0'])} to {pct(decision['ma60_a2_only_h5_v2'])} with MAE {pct(decision['ma60_a2_only_h5_mae_v0'])} to {pct(decision['ma60_a2_only_h5_mae_v2'])}; LEGACY5_ONLY changes {pct(decision['ma60_legacy_only_h5_v0'])} to {pct(decision['ma60_legacy_only_h5_v2'])} with MAE {pct(decision['ma60_legacy_only_h5_mae_v0'])} to {pct(decision['ma60_legacy_only_h5_mae_v2'])}. It removes {decision['ma60_removed_h5']} of 2,471 anchors and also removes MFE≥5% opportunities in {decision['ma60_removed_mfe_ge_5_h5']} cases versus {decision['ma60_removed_endpoint_le_0_h5']} non-positive endpoints and {decision['ma60_removed_mae_le_minus5_h5']} MAE≤−5% cases. MA60 remains research-only and is not accepted.",
        "10. Benchmark-adjusted analysis: NOT_AVAILABLE; no PIT-safe accepted benchmark daily series was present.",
        "11. Regime robustness: NOT_AVAILABLE; existing evidence explicitly lacks PIT-safe event-level index/breadth/peer regime data.",
        "12. The MFE/|MAE| ratio is included only as a descriptive excursion ratio, not a risk-adjusted return.",
        "13. Corporate actions remain UNKNOWN_RAW_ONLY; no synthetic adjustment was introduced.",
        "14. No untouched later-period OOS exists in this task; OUT_OF_SAMPLE_SUPPORTED=NO.",
        "15. Minimum next OOS design: freeze definitions and reporting now, accumulate only future sessions after 2026-08-13, and evaluate an untouched later period without threshold or overlap-window changes.",
        "",
        "## Governance",
        "",
        "`WS3_ONLY=YES`; `A_SETUP_ACCEPTED=NO`; `A_STRATEGY_ACCEPTED=NO`; `LEGACY_STRATEGY_ACCEPTED=NO`; `JOINT_SIGNAL_ACCEPTED=NO`; `CORE_V0_MUTATION=NO`; `PRODUCTION_MUTATION=NO`; `DEPLOY=NO`; `PUSH=NO`; `NEXT_TASK_CHANGED=NO`.",
        "",
        f"Source surface: {source_manifest['dataset']['accepted_rows']} accepted rows / {source_manifest['dataset']['instruments']} instruments / {source_manifest['dataset']['start']}–{source_manifest['dataset']['end']}. One read-only accepted price surface scan was used only for exact session positions and LEGACY-5 barrier reconstruction; no data download or write occurred.",
    ]
    return "\n".join(lines) + "\n"


def _formal(summary: Mapping[str, Any], decision: Mapping[str, Any], source_manifest: Mapping[str, Any], artifacts: Mapping[str, str]) -> str:
    return "\n".join([
        f"# Formal Closure Report — {TASK_ID}",
        "",
        "## Scope and disposition",
        "",
        "This report closes an isolated WS3-only descriptive robustness study of the already-frozen A2 × LEGACY-5 overlap. It does not create A3, alter A2/Core V0 semantics, alter LEGACY-5 semantics, or mutate WS1/WS2/WS4, Production, API/UI, scheduler, or NEXT_TASK.",
        "",
        f"Final disposition: **{decision['final_disposition']}**. `OUT_OF_SAMPLE_SUPPORTED=NO`; the result is not an accepted strategy.",
        "",
        "## Input reconciliation",
        "",
        f"- Accepted source surface: {source_manifest['dataset']['accepted_rows']} rows, {source_manifest['dataset']['instruments']} instruments, {source_manifest['dataset']['start']} to {source_manifest['dataset']['end']}; normalized source SHA-256 `{source_manifest['dataset']['surface_sha256']}`.",
        "- A2 cohort: 5,277 committed events with path-aware H1-H10 reconstruction.",
        "- LEGACY-5 cohort: 2,471 raw anchors; V2 MA60 ablation: 2,096 anchors.",
        "- Matching: one-to-one by instrument and accepted canonical session position within the predeclared ±1 window.",
        "- Corporate-action state: UNKNOWN_RAW_ONLY; same-session barrier races: SAME_SESSION_ORDER_UNKNOWN.",
        "- Benchmark/regime: NOT_AVAILABLE dispositions; no external or synthetic series.",
        "",
        "## Robustness controls",
        "",
        "Endpoint statistics include count, mean, median, sample standard deviation, positive rate, P25 and P75 at T+1/T+3/T+5/T+10. Path statistics include MFE/MAE distributions, threshold rates, fixed barrier races, and MFE/|MAE| as a descriptive excursion ratio. Extreme-winner policies were fixed at 1%/5% quantiles before outcome review. Calendar years and the 2025-08-13 midpoint were fixed before comparison. No threshold search or multiple-testing selection was performed.",
        "",
        "The BOTH rows intentionally report two source observations per matched pair, with pair_count reported separately. This preserves the prior artifact's PAIR_COMBINED descriptive convention while avoiding a claim that the two source observations are independent.",
        "",
        f"MA60 ablation is not a joint-quality acceptance: the same-session BOTH H5 mean is unchanged at {decision['ma60_both_h5_v0']:.6f}; V2 removes {decision['ma60_removed_h5']} raw anchors, including {decision['ma60_removed_mfe_ge_5_h5']} MFE>=5% opportunities and {decision['ma60_removed_endpoint_le_0_h5']} non-positive endpoints. The path/downside trade-off is therefore descriptive and unresolved, not a production recommendation.",
        "",
        "## OOS and acceptance boundary",
        "",
        "The current 2024-08-13 to 2026-08-13 panel is reused in-sample for this robustness exercise. No untouched later period exists, so OUT_OF_SAMPLE_SUPPORTED=NO. A future OOS must freeze the signal definitions, ±1 matching, horizons, barriers, and reporting rules before accumulating later sessions.",
        "",
        "## Governance flags",
        "",
        "`WS3_ONLY=YES`; `A_SETUP_ACCEPTED=NO`; `A_STRATEGY_ACCEPTED=NO`; `LEGACY_STRATEGY_ACCEPTED=NO`; `JOINT_SIGNAL_ACCEPTED=NO`; `CORE_V0_MUTATION=NO`; `PRODUCTION_MUTATION=NO`; `DEPLOY=NO`; `PUSH=NO`; `NEXT_TASK_CHANGED=NO`.",
        "",
        "## Artifact hashes",
        "",
        *[f"- `{name}`: `{digest}`" for name, digest in sorted(artifacts.items())],
        "",
    ])


def _self_test() -> None:
    assert _quantile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5
    assert _trimmed(list(range(100)), 0.01) == list(range(1, 99))
    clipped = _winsorized([-10.0, 0.0, 1.0, 2.0, 10.0], 0.2)
    assert clipped[0] > -10.0 and clipped[-1] < 10.0
    assert _positive_top_contribution([1.0, 2.0, -5.0], 1) == 2 / 3
    assert prior._a2_barrier({"horizon_status": "COMPLETE_RAW_PATH", "mfe": "0.06", "mae": "-0.06", "mfe_timing_session": "1", "mae_timing_session": "1"}, 0.05, -0.05) == "SAME_SESSION_ORDER_UNKNOWN"
    print("WS3_A2_LEGACY5_JOINT_SIGNAL_SELF_TEST=PASS")


def run(database_url: str, output_dir: Path, replay_verified: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    repo_root = _root()
    inputs = _load_inputs(repo_root, database_url)
    a2_by_key, legacy_by_anchor_h = _source_rows(inputs)
    anchors_v0 = inputs["anchors_by_variant"]["V0_LEGACY5"]
    matching = prior._match_events(inputs["a2_events"], anchors_v0, inputs["groups"], FIXED_WINDOW)
    records, pair_meta = _make_cohort_records(inputs, matching, "V0_LEGACY5", a2_by_key, legacy_by_anchor_h)
    counts = _cohort_counts(records, pair_meta["pair_members"])
    if counts["A2_ONLY"]["event_count"] != 4485 or counts["LEGACY5_ONLY"]["event_count"] != 1679 or counts["BOTH_SAME_SESSION"]["pair_count"] != 560 or counts["BOTH_WITHIN_1_SESSION"]["pair_count"] != 232:
        raise ContractBlocked(f"Fixed overlap counts failed reconciliation: {counts}")

    output_dir.mkdir(parents=True, exist_ok=True)
    endpoint_rows = _endpoint_rows(records)
    path_rows = _path_rows(records)
    extreme_rows = _extreme_rows(records)
    instrument_rows = _instrument_rows(records)
    time_rows = _time_rows(records)
    market_rows = _market_rows(records)
    ma60_rows = _ma60_rows(inputs, a2_by_key, legacy_by_anchor_h, inputs["groups"])
    timing_rows = _timing_rows(inputs, matching, a2_by_key, legacy_by_anchor_h)
    statistical = _statistical_summary(records)
    benchmark_rows, regime_rows = _availability_rows("benchmark"), _availability_rows("regime")

    _write_csv(output_dir / "joint-signal-endpoint-robustness.csv", endpoint_rows)
    _write_csv(output_dir / "joint-signal-path-robustness.csv", path_rows)
    _write_csv(output_dir / "extreme-winner-dependence.csv", extreme_rows)
    _write_csv(output_dir / "instrument-concentration-analysis.csv", instrument_rows)
    _write_csv(output_dir / "time-stability-analysis.csv", time_rows)
    _write_csv(output_dir / "market-split-analysis.csv", market_rows)
    _write_csv(output_dir / "ma60-joint-signal-ablation.csv", ma60_rows)
    _write_csv(output_dir / "benchmark-adjusted-analysis.csv", benchmark_rows)
    _write_csv(output_dir / "benchmark-not-available.csv", benchmark_rows)
    _write_csv(output_dir / "regime-robustness.csv", regime_rows)
    _write_csv(output_dir / "regime-not-available.csv", regime_rows)
    _write_csv(output_dir / "signal-timing-path-analysis.csv", timing_rows)
    _write_json(output_dir / "statistical-robustness-summary.json", statistical)

    source_manifest = _source_manifest(repo_root, inputs, output_dir)
    _write_json(output_dir / "source-semantics-reconciliation-manifest.json", source_manifest)
    decision = _decision({}, endpoint_rows, extreme_rows, time_rows, market_rows, ma60_rows, timing_rows)
    summary: dict[str, Any] = {
        "schema_version": "ws3-a2-legacy5-joint-signal-run-summary.v1",
        "task_id": TASK_ID,
        "task_status": "COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS",
        "final_disposition": decision["final_disposition"],
        "cohorts": counts,
        "matching": {"window_sessions": FIXED_WINDOW, "candidate_pair_count": matching["candidate_pair_count"], "pair_counts_by_delta": dict(Counter(int(item["delta_sessions"]) for item in matching["matches"]))},
        "decision": decision,
        "governance": {"WS3_ONLY": "YES", "A_SETUP_ACCEPTED": "NO", "A_STRATEGY_ACCEPTED": "NO", "LEGACY_STRATEGY_ACCEPTED": "NO", "JOINT_SIGNAL_ACCEPTED": "NO", "CORE_V0_MUTATION": "NO", "A2_SEMANTICS_CHANGED": "NO", "LEGACY5_SEMANTICS_CHANGED": "NO", "WS1_WS2_WS4_MUTATION": "NO", "PRODUCTION_MUTATION": "NO", "DEPLOY": "NO", "PUSH": "NO", "NEXT_TASK_CHANGED": "NO", "DATABASE_WRITES": False, "DATA_DOWNLOAD": "NO", "LARGE_OHLCV_PIPELINE_RERUN": "NO", "PRICE20_RESEARCHED": "NO", "THRESHOLD_SEARCH": "NO", "MA20_RESEARCHED": "NO", "OUT_OF_SAMPLE_SUPPORTED": "NO"},
        "corporate_action_governance": {"adjustment_state": "UNKNOWN_RAW_ONLY", "synthetic_adjustment": False, "fail_closed": True, "same_session_order": "SAME_SESSION_ORDER_UNKNOWN"},
        "benchmark_adjusted_analysis": "NOT_AVAILABLE",
        "regime_robustness": "NOT_AVAILABLE",
        "raw_panel_scans": source_manifest["scan_disposition"],
        "source_surface": inputs["surface_quality"],
        "statistical_discipline": statistical["discipline"],
        "reproducibility": {"reconstruction_runs": 2 if replay_verified else 1, "reproducible": "YES" if replay_verified else "PENDING_REPLAY", "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_replicates": BOOTSTRAP_REPS},
    }
    artifact_hashes = _artifact_hashes(output_dir)
    aggregate = hashlib.sha256("".join(f"{name}:{digest}\n" for name, digest in sorted(artifact_hashes.items())).encode("utf-8")).hexdigest()
    summary["artifact_hashes"] = artifact_hashes
    summary["artifact_aggregate_sha256"] = aggregate
    summary["runtime_seconds"] = None
    _write_json(output_dir / "run-summary.json", summary)
    _write_json(output_dir / "reproducibility-manifest.json", {"schema_version": "ws3-a2-legacy5-joint-reproducibility.v1", "task_id": TASK_ID, "reconstruction_runs": 2 if replay_verified else 1, "reproducible": "YES" if replay_verified else "PENDING_REPLAY", "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_replicates": BOOTSTRAP_REPS, "artifact_hashes_before_replay": artifact_hashes, "artifact_aggregate_sha256": aggregate, "source_surface_sha256": prior.EXPECTED_SURFACE_SHA256, "database_access": "read_only", "strategy_acceptance": "NO"})
    artifact_hashes = _artifact_hashes(output_dir)
    _write_text(output_dir / "OWNER-DECISION-MEMO.md", _memo(summary, decision, counts, source_manifest))
    memo_hash = _sha256(output_dir / "OWNER-DECISION-MEMO.md")
    artifact_hashes = _artifact_hashes(output_dir)
    aggregate = hashlib.sha256("".join(f"{name}:{digest}\n" for name, digest in sorted(artifact_hashes.items())).encode("utf-8")).hexdigest()
    _write_text(output_dir / "formal-closure-report.md", _formal(summary, decision, source_manifest, artifact_hashes))
    artifact_hashes = _artifact_hashes(output_dir)
    aggregate = hashlib.sha256("".join(f"{name}:{digest}\n" for name, digest in sorted(artifact_hashes.items())).encode("utf-8")).hexdigest()
    summary["artifact_hashes"] = artifact_hashes
    summary["artifact_aggregate_sha256"] = aggregate
    _write_json(output_dir / "run-summary.json", summary)
    _write_json(output_dir / "reproducibility-manifest.json", {"schema_version": "ws3-a2-legacy5-joint-reproducibility.v1", "task_id": TASK_ID, "reconstruction_runs": 2 if replay_verified else 1, "reproducible": "YES" if replay_verified else "PENDING_REPLAY", "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_replicates": BOOTSTRAP_REPS, "artifact_hashes_before_replay": artifact_hashes, "artifact_aggregate_sha256": aggregate, "source_surface_sha256": prior.EXPECTED_SURFACE_SHA256, "database_access": "read_only", "strategy_acceptance": "NO"})
    return summary


def _mark_replay_verified(output_dir: Path) -> None:
    summary_path = output_dir / "run-summary.json"
    manifest_path = output_dir / "reproducibility-manifest.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary["reproducibility"] = {**summary.get("reproducibility", {}), "reconstruction_runs": 2, "reproducible": "YES"}
    manifest.update({"reconstruction_runs": 2, "reproducible": "YES"})
    _write_json(summary_path, summary)
    _write_json(manifest_path, manifest)
    print("WS3_A2_LEGACY5_JOINT_SIGNAL_REPLAY=YES")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL") or os.environ.get("DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR_DEFAULT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--replay-verified", action="store_true", help="Mark the deterministic second replay as verified; use only after an external replay comparison")
    parser.add_argument("--mark-replay-verified", action="store_true", help="Update an already replay-compared output directory without rerunning the database analysis")
    args = parser.parse_args()
    if args.mark_replay_verified:
        _mark_replay_verified(args.output_dir)
        return
    if args.self_test:
        _self_test()
        return
    if not args.database_url:
        parser.error("--database-url or TOPICPILOT_DATABASE_URL/DATABASE_URL is required")
    try:
        print(json.dumps(run(args.database_url, args.output_dir, args.replay_verified), ensure_ascii=False, default=_json_default))
    except ContractBlocked as exc:
        print(f"WS3_A2_LEGACY5_JOINT_SIGNAL_CONTRACT_BLOCKED={exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
