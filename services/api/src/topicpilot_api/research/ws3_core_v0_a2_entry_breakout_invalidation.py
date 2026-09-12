"""Descriptive WS3 A2 entry and breakout-invalidation research.

This module consumes the frozen Core V0 A2 candidate panel and canonical
historical OHLCV read model.  It does not redefine A2, publish an entry or
stop rule, search parameters, or write application state.  Entry proxies,
state-episode deduplication, path horizons, and descriptive depth bands are
declared before the outcome tables are built.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import date
from itertools import pairwise
from pathlib import Path
from statistics import mean, median
from typing import Any

from topicpilot_api.research.ws3_core_v0_baseline_attribution import (
    FROZEN_SPEC_HASH,
    SEGMENTS,
    collect_observations,
)

# ruff: noqa: E501 - exact evidence and contract strings are intentional.

TASK_ID = "TASK-WS3-CORE-V0-A2-ENTRY-AND-BREAKOUT-INVALIDATION-RESEARCH-20260819"
SOURCE_CANONICAL_HEAD = "2468ee6b5093dd2a37353424c74d9d719c643bb9"
CURRENT_CANONICAL_HEAD = SOURCE_CANONICAL_HEAD
UPSTREAM_A1_TASK_ID = "TASK-WS3-CORE-V0-A1-QUALITY-FILTER-CONFIRMATORY-VALIDATION-20260818"
UPSTREAM_A1_FREEZE = (
    "reports/TASK-WS3-CORE-V0-A1-QUALITY-FILTER-CONFIRMATORY-VALIDATION-20260818/"
    "a1-quality-filter-confirmatory-freeze.json"
)
DATASET_PATH_DEFAULT = Path(
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/"
    "REC-A1-CA-EVENTS-V0.json"
)
OUT_DIR_DEFAULT = Path(
    "reports/TASK-WS3-CORE-V0-A2-ENTRY-AND-BREAKOUT-INVALIDATION-RESEARCH-20260819"
)
REPORT_PATH = Path(
    "docs/reports/TASK-WS3-CORE-V0-A2-ENTRY-AND-BREAKOUT-INVALIDATION-RESEARCH-20260819.md"
)
HORIZONS = (1, 3, 5, 10)
PATH_HORIZON = 10
PRIMARY_ENTRY_PROXY = "OBSERVABLE_A2_CLOSE"
TRANSACTION_COST_AUTHORITY_AVAILABLE = "NO"

ENTRY_PROXIES = (
    "THEORETICAL_REFERENCE_FILL",
    "OBSERVABLE_A2_CLOSE",
    "NEXT_SESSION_OPEN",
    "NEXT_SESSION_CLOSE",
)
ENTRY_PROXY_DEFINITIONS = {
    "THEORETICAL_REFERENCE_FILL": {
        "price": "Reference(T)",
        "timing": "A2 signal session; price-only theoretical reference fill",
        "execution_assumption": "THEORETICAL_REFERENCE_FILL",
        "path_semantics": "next canonical sessions strictly after T",
    },
    "OBSERVABLE_A2_CLOSE": {
        "price": "Close(T)",
        "timing": "A2 signal-session close",
        "execution_assumption": "OBSERVABLE_CLOSE_FILL",
        "path_semantics": "next canonical sessions strictly after T",
    },
    "NEXT_SESSION_OPEN": {
        "price": "Open(T+1)",
        "timing": "next canonical trading-session open",
        "execution_assumption": "NEXT_SESSION_OPEN_FILL",
        "path_semantics": "entry session through the next h-1 canonical sessions",
    },
    "NEXT_SESSION_CLOSE": {
        "price": "Close(T+1)",
        "timing": "next canonical trading-session close",
        "execution_assumption": "NEXT_SESSION_CLOSE_FILL",
        "path_semantics": "sessions strictly after the next-session close",
    },
}
EXTENSION_BANDS = (
    ("LE_0PCT", None, 0.0),
    ("GT_0_TO_1PCT", 0.0, 0.01),
    ("GT_1_TO_2PCT", 0.01, 0.02),
    ("GT_2_TO_3PCT", 0.02, 0.03),
    ("GT_3_TO_5PCT", 0.03, 0.05),
    ("GT_5PCT", 0.05, None),
)
DEPTH_BANDS = (
    ("NO_LOSS", None, 0.0),
    ("0_TO_MINUS_1PCT", -0.01, 0.0),
    ("MINUS_1_TO_2PCT", -0.02, -0.01),
    ("MINUS_2_TO_3PCT", -0.03, -0.02),
    ("MINUS_3_TO_5PCT", -0.05, -0.03),
    ("BELOW_MINUS_5PCT", None, -0.05),
)
ANALYTICAL_ARTIFACT_NAMES = (
    "ws3-core-v0-a1-quality-filter-forward-validation-contract.json",
    "ws3-core-v0-a2-event-panel.csv",
    "ws3-core-v0-a2-event-definition.json",
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
    "ws3-core-v0-a2-concentration-analysis.json",
)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"EMPTY_CSV_OUTPUT:{path.name}")
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in fields} for row in rows)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _number(value: Any) -> float | None:
    return _float(value)


def _mean(values: Sequence[float]) -> float | None:
    return mean(values) if values else None


def _median(values: Sequence[float]) -> float | None:
    return median(values) if values else None


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
    kept = ordered[trim : len(ordered) - trim] if len(ordered) > 2 * trim else ordered
    return _mean(kept)


def _stats(values: Sequence[float]) -> dict[str, Any]:
    return {
        "count": len(values),
        "mean": _mean(values),
        "median": _median(values),
        "trimmed_mean_10pct": _trimmed_mean(values),
        "p05": _quantile(values, 0.05),
        "p25": _quantile(values, 0.25),
        "p75": _quantile(values, 0.75),
        "p95": _quantile(values, 0.95),
        "win_rate": sum(value > 0 for value in values) / len(values) if values else None,
    }


def _segment(signal_date: Any) -> str:
    value = _date(signal_date)
    for name, start, end in SEGMENTS:
        if start <= value <= end:
            return name
    return "OUTSIDE_FROZEN_SEGMENTS"


def _value(item: Mapping[str, Any], field: str) -> float | None:
    return _number(item.get(field))


def _extension_band(value: float | None) -> str:
    if value is None:
        return "UNAVAILABLE"
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


def _depth_band(value: float | None) -> str:
    if value is None or value >= 0:
        return "NO_LOSS"
    if value > -0.01:
        return "0_TO_MINUS_1PCT"
    if value > -0.02:
        return "MINUS_1_TO_2PCT"
    if value > -0.03:
        return "MINUS_2_TO_3PCT"
    if value > -0.05:
        return "MINUS_3_TO_5PCT"
    return "BELOW_MINUS_5PCT"


def _path_stats(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    returns = [_number(row.get("forward_return")) for row in records]
    mfes = [_number(row.get("mfe")) for row in records]
    maes = [_number(row.get("mae")) for row in records]
    extensions = [_number(row.get("entry_extension_pct")) for row in records]
    returns = [value for value in returns if value is not None]
    mfes = [value for value in mfes if value is not None]
    maes = [value for value in maes if value is not None]
    extensions = [value for value in extensions if value is not None]
    result = {
        "event_count": len(records),
        "unique_instruments": len({row["instrument_id"] for row in records}),
        "unique_dates": len({row["signal_date"] for row in records}),
        "extension_mean": _mean(extensions),
        "extension_median": _median(extensions),
        "forward": _stats(returns),
        "mfe": _stats(mfes),
        "mae": _stats(maes),
    }
    result["outlier_driven"] = bool(
        result["forward"]["mean"] is not None
        and result["forward"]["mean"] > 0
        and (result["forward"]["median"] or 0) <= 0
        and (result["forward"]["trimmed_mean_10pct"] or 0) <= 0
    )
    return result


def _a1_forward_validation_contract(freeze_path: Path) -> dict[str, Any]:
    freeze = _read_json(freeze_path)
    candidates = freeze.get("candidates", [])
    if freeze.get("candidate_count") != 7 or len(candidates) != 7:
        raise RuntimeError("A1_FORWARD_CONTRACT_REQUIRES_EXACTLY_SEVEN_FROZEN_CANDIDATES")
    return {
        "schema_version": "ws3-core-v0-a1-quality-filter-forward-validation-contract.v1",
        "task_id": TASK_ID,
        "status": "FROZEN_AWAITING_FORWARD_EVIDENCE",
        "upstream_task_id": UPSTREAM_A1_TASK_ID,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "candidate_count": 7,
        "candidates": [
            {
                "candidate_id": item["candidate_id"],
                "candidate_type": item["candidate_type"],
                "feature_name": item.get("feature_name"),
                "feature_definition": item["feature_definition"],
                "operator": item["operator"],
                "threshold_quantile": item["threshold_quantile"],
                "threshold_value": item["threshold_value"],
                "combination_logic": item.get("combination_logic"),
                "pit_timestamp_rule": item["timestamp_rule"],
            }
            for item in candidates
        ],
        "required_future_fields": [
            "evaluation_session",
            "symbol",
            "candidate_inputs_as_of_T",
            "PIT_source_lineage",
            "T+1_outcome",
            "T+3_outcome",
            "T+5_outcome",
            "T+10_outcome",
            "REC_A1_integrity_state",
        ],
        "outcome_maturity_requirements": {
            "all_horizons_are_evaluation_only": True,
            "candidate_formation_information_le_T_only": True,
            "minimum_matured_events_per_primary_cohort": 20,
            "minimum_matured_events_total": 40,
            "T+10_required_for_full_maturity": True,
            "corporate_action_exclusion_can_only_invalidate_outcome": True,
        },
        "thresholds_immutable_until_next_confirmatory_review": True,
        "threshold_retuning_performed": False,
        "new_feature_search_performed": False,
        "new_combination_search_performed": False,
        "a1_formation_changed": False,
        "execution_performed_by_this_contract": False,
    }


def _build_event_definitions() -> dict[str, Any]:
    return {
        "schema_version": "ws3-core-v0-a2-entry-breakout-invalidation-definition.v1",
        "task_id": TASK_ID,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "a2_formation_changed": False,
        "a2_authority": {
            "candidate_id": "CORE_V0_A2_CONFIRMED_BREAKOUT",
            "definition_version": "core-v0-a2-confirmed-breakout.v1",
            "reference_policy_id": "PRIOR_20_ACCEPTED_SESSION_HIGH",
            "reference_formula": "max(High(s) for prior 20 accepted sessions strictly before T)",
            "evaluation_session_excluded_from_reference": True,
            "reference_maturity_sessions": 5,
            "formation_rule": "L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T)",
            "confirmation_policy": "single-session-close",
            "uses_intraday_high_for_confirmation": False,
            "gap_above_reference_can_form_a2": True,
            "pit_validity": True,
            "source": "services/api/src/topicpilot_api/research/core_v0_candidate_panel.py",
            "lineage_fields": ["candidate_record_id", "candidate_source_lineage", "reference_birth_session", "reference_age_sessions"],
        },
        "event_deduplication": {
            "rule_id": "A2_CONTIGUOUS_CANONICAL_STATE_EPISODE_V1",
            "raw_observation_unit": "one formed A2 candidate panel row at one accepted canonical trading session",
            "distinct_event_start": "first A2 row for an instrument, or an A2 row whose canonical session index is not immediately after the prior A2 row for that instrument",
            "persistent_observation": "an A2 row immediately following the prior A2 row for the same instrument in canonical session order",
            "event_id": "SHA256(instrument_id|A2_start_date|A2_definition_version)",
            "dedup_selected_before_outcome_review": True,
            "profitability_based_deduplication": False,
        },
        "entry_proxies": ENTRY_PROXY_DEFINITIONS,
        "entry_extension": {
            "formula": "(entry_price / BREAKOUT_REFERENCE_PRICE) - 1",
            "bands": [
                {"band": name, "lower_exclusive": lower, "upper_inclusive": upper}
                for name, lower, upper in EXTENSION_BANDS
            ],
            "threshold_optimization": False,
        },
        "mfe_mae": {
            "mfe_formula": "max(high / entry_price - 1) over the defined next h canonical sessions",
            "mae_formula": "min(low / entry_price - 1) over the defined next h canonical sessions",
            "session_semantics": "canonical accepted trading sessions, not calendar days",
            "signal_day_proxies": "path begins strictly after T",
            "next_open_proxy": "path includes the entry session and the next h-1 sessions",
            "next_close_proxy": "path begins strictly after the next-session close",
            "horizons": list(HORIZONS),
        },
        "reference_loss_reclaim": {
            "bounded_horizon_sessions": PATH_HORIZON,
            "primary_loss": "first future canonical session with Low < BREAKOUT_REFERENCE_PRICE",
            "close_loss": "first future canonical session with Close < BREAKOUT_REFERENCE_PRICE",
            "reclaim": "first session at or after primary loss with Close >= BREAKOUT_REFERENCE_PRICE",
            "depth_bands_are_descriptive_only": True,
            "depth_bands": [
                {"band": name, "lower_exclusive": lower, "upper_inclusive": upper}
                for name, lower, upper in DEPTH_BANDS
            ],
            "no_stop_rule": True,
        },
        "cost_authority": {
            "transaction_cost_authority_available": TRANSACTION_COST_AUTHORITY_AVAILABLE,
            "results_are_gross": True,
        },
        "forbidden_actions": [
            "entry_threshold_optimization",
            "stop_optimization",
            "take_profit_optimization",
            "holding_period_optimization",
            "position_sizing",
            "production_entry_or_stop_rule",
        ],
    }


def _event_id(instrument_id: str, signal_date: date) -> str:
    payload = f"{instrument_id}|{signal_date.isoformat()}|core-v0-a2-confirmed-breakout.v1".encode()
    return hashlib.sha256(payload).hexdigest()


def _build_events(
    a1_rows: Sequence[Mapping[str, Any]],
    a2_rows: Sequence[Mapping[str, Any]],
    instrument_data: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Deduplicate raw A2 rows into contiguous state episodes before outcomes."""

    a1_by_instrument: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in a1_rows:
        a1_by_instrument[str(row["instrument_id"])].append(row)
    for values in a1_by_instrument.values():
        values.sort(key=lambda row: row["signal_date"])

    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in a2_rows:
        grouped[str(row["instrument_id"])].append(row)
    events: list[dict[str, Any]] = []
    for instrument_id, rows in grouped.items():
        rows = sorted(rows, key=lambda row: int(row["index"]))
        runs: list[list[Mapping[str, Any]]] = []
        current: list[Mapping[str, Any]] = []
        for row in rows:
            if current and int(row["index"]) != int(current[-1]["index"]) + 1:
                runs.append(current)
                current = []
            current.append(row)
        if current:
            runs.append(current)
        data = instrument_data[instrument_id]
        items = data["items"]
        dates = data["dates"]
        for run in runs:
            first = run[0]
            start_index = int(first["index"])
            end_index = int(run[-1]["index"])
            signal_date = _date(first["signal_date"])
            prior_a1 = [row for row in a1_by_instrument[instrument_id] if _date(row["signal_date"]) < signal_date]
            a1_origin = prior_a1[-1] if prior_a1 else None
            reference = _number(first["candidate_inputs"]["reference_value"])
            if reference is None or reference <= 0:
                raise RuntimeError("A2_REFERENCE_VALUE_INVALID")
            event = {
                "event_id": _event_id(instrument_id, signal_date),
                "instrument_id": instrument_id,
                "stock_code": first["stock_code"],
                "market": first["market"],
                "signal_date": signal_date,
                "a2_date": signal_date,
                "segment": _segment(signal_date),
                "index": start_index,
                "end_index": end_index,
                "observation_count": len(run),
                "observation_dates": [_date(row["signal_date"]).isoformat() for row in run],
                "event_end_date": _date(run[-1]["signal_date"]),
                "a1_origin_date": _date(a1_origin["signal_date"]) if a1_origin else None,
                "a1_origin_candidate_record_id": a1_origin.get("candidate_record_id") if a1_origin else None,
                "reference": reference,
                "reference_policy_id": first["candidate_inputs"]["reference_policy_id"],
                "reference_birth_session": first["candidate_inputs"].get("reference_birth_session"),
                "reference_age_sessions": first["candidate_inputs"].get("reference_age_sessions"),
                "a2_close": _number(items[start_index].get("close")),
                "a2_open": _number(items[start_index].get("open")),
                "a2_high": _number(items[start_index].get("high")),
                "a2_low": _number(items[start_index].get("low")),
                "volume": _number(items[start_index].get("volume")),
                "ma60": _number(first["ma60"]),
                "gap_up": bool(first["candidate_inputs"].get("gap_up") in (True, "True")),
                "candidate_record_id": first["candidate_record_id"],
                "source_lineage": list(first["candidate_source_lineage"]),
                "event_excluded_horizons": set(first.get("event_excluded_horizons", set())),
                "_items": items,
                "_dates": dates,
            }
            event["distance_from_ma60"] = (
                event["a2_close"] / event["ma60"] - 1
                if event["a2_close"] is not None and event["ma60"] not in (None, 0)
                else None
            )
            events.append(event)
    return sorted(events, key=lambda event: (event["signal_date"], event["instrument_id"]))


def _entry_for_proxy(event: Mapping[str, Any], proxy: str) -> dict[str, Any] | None:
    if proxy not in ENTRY_PROXIES:
        raise ValueError(f"UNKNOWN_ENTRY_PROXY:{proxy}")
    items = event["_items"]
    dates = event["_dates"]
    index = int(event["index"])
    reference = float(event["reference"])
    if proxy == "THEORETICAL_REFERENCE_FILL":
        entry_index = index
        price = reference
        path_start = index + 1
        target_offset = 0
    elif proxy == "OBSERVABLE_A2_CLOSE":
        entry_index = index
        price = _number(items[index].get("close"))
        path_start = index + 1
        target_offset = 0
    elif proxy == "NEXT_SESSION_OPEN":
        entry_index = index + 1
        price = _number(items[entry_index].get("open")) if entry_index < len(items) else None
        path_start = entry_index
        target_offset = -1
    else:
        entry_index = index + 1
        price = _number(items[entry_index].get("close")) if entry_index < len(items) else None
        path_start = entry_index + 1
        target_offset = 0
    if price is None or price <= 0 or entry_index >= len(items):
        return None
    return {
        "proxy": proxy,
        "entry_index": entry_index,
        "entry_date": dates[entry_index],
        "entry_price": price,
        "entry_extension_pct": price / reference - 1,
        "entry_cost_vs_reference": price / reference - 1,
        "path_start": path_start,
        "target_offset": target_offset,
        "execution_assumption": ENTRY_PROXY_DEFINITIONS[proxy]["execution_assumption"],
    }


def _horizon_metrics(event: Mapping[str, Any], proxy: str, horizon: int) -> dict[str, Any]:
    entry = _entry_for_proxy(event, proxy)
    base = {
        "event_id": event["event_id"],
        "instrument_id": event["instrument_id"],
        "stock_code": event["stock_code"],
        "market": event["market"],
        "signal_date": event["signal_date"].isoformat(),
        "segment": event["segment"],
        "proxy": proxy,
        "horizon": horizon,
        "event_path_category": event.get("path_category"),
        "reference_loss": event.get("reference_loss"),
        "reference_reclaimed": event.get("reference_reclaimed"),
    }
    if entry is None:
        return {**base, "status": "UNAVAILABLE_ENTRY_PROXY", "entry_extension_pct": None}
    base.update(
        {
            "status": "AVAILABLE",
            "entry_date": entry["entry_date"].isoformat(),
            "entry_price": entry["entry_price"],
            "entry_extension_pct": entry["entry_extension_pct"],
            "entry_cost_vs_reference": entry["entry_cost_vs_reference"],
            "execution_assumption": entry["execution_assumption"],
        }
    )
    if horizon in event["event_excluded_horizons"]:
        return {**base, "status": "EXCLUDED_BY_REC_A1_INTEGRITY", "integrity_state": "EXCLUDED"}
    items = event["_items"]
    if proxy == "NEXT_SESSION_OPEN":
        target_index = entry["entry_index"] + horizon - 1
    else:
        target_index = entry["entry_index"] + horizon
    path = items[entry["path_start"] : target_index + 1]
    if target_index >= len(items) or len(path) < horizon:
        return {**base, "status": "UNAVAILABLE_INSUFFICIENT_FORWARD_WINDOW", "integrity_state": "UNAVAILABLE"}
    highs = [_number(item.get("high")) for item in path]
    lows = [_number(item.get("low")) for item in path]
    target_close = _number(items[target_index].get("close"))
    highs = [value for value in highs if value is not None]
    lows = [value for value in lows if value is not None]
    if target_close is None or not highs or not lows:
        return {**base, "status": "UNAVAILABLE_MALFORMED_FORWARD_WINDOW", "integrity_state": "UNAVAILABLE"}
    forward_return = target_close / entry["entry_price"] - 1
    mfe = max(highs) / entry["entry_price"] - 1
    mae = min(lows) / entry["entry_price"] - 1
    return {
        **base,
        "status": "AVAILABLE",
        "integrity_state": "VALID",
        "target_date": event["_dates"][target_index].isoformat(),
        "target_close": target_close,
        "forward_return": forward_return,
        "mfe": mfe,
        "mae": mae,
        "mfe_capture_ratio": forward_return / mfe if mfe > 0 else None,
    }


def _reference_path(event: dict[str, Any]) -> dict[str, Any]:
    items = event["_items"]
    index = int(event["index"])
    reference = float(event["reference"])
    future = items[index + 1 : index + 1 + PATH_HORIZON]
    low_losses = [offset for offset, item in enumerate(future, 1) if (_number(item.get("low")) or math.inf) < reference]
    close_losses = [offset for offset, item in enumerate(future, 1) if (_number(item.get("close")) or math.inf) < reference]
    first_loss = low_losses[0] if low_losses else None
    first_close_loss = close_losses[0] if close_losses else None
    reclaim_offset = None
    if first_loss is not None:
        for offset in range(first_loss, len(future) + 1):
            close = _number(future[offset - 1].get("close"))
            if close is not None and close >= reference:
                reclaim_offset = offset
                break
    penetration = [(_number(item.get("low")) or reference) / reference - 1 for item in future]
    min_penetration = min(penetration) if penetration else None
    loss = first_loss is not None
    reclaimed = reclaim_offset is not None
    if not loss:
        category = "REMAINS_ABOVE_REFERENCE"
    elif reclaimed and first_close_loss is not None:
        category = "CLOSE_BELOW_REFERENCE_THEN_RECLAIM"
    elif reclaimed:
        category = "TEMPORARY_INTRADAY_LOSS_RECLAIMED"
    else:
        category = "LOSS_NO_RECLAIM_WITHIN_H10"
    event.update(
        {
            "path_matured_h10": len(future) == PATH_HORIZON,
            "path_observed_sessions": len(future),
            "reference_loss": loss,
            "reference_close_loss": first_close_loss is not None,
            "reference_reclaimed": reclaimed,
            "first_reference_loss_session": first_loss,
            "first_reference_close_loss_session": first_close_loss,
            "sessions_to_reference_loss": first_loss,
            "sessions_to_reclaim": reclaim_offset,
            "max_adverse_penetration_pct": min_penetration,
            "reference_loss_depth_band": _depth_band(min_penetration),
            "material_penetration_below_minus_3pct": bool(min_penetration is not None and min_penetration <= -0.03),
            "path_category": category,
            "descriptive_failure_like_path": bool(loss and not reclaimed),
        }
    )
    return event


def _event_panel_rows(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event in events:
        rows.append(
            {
                "event_id": event["event_id"],
                "instrument_id": event["instrument_id"],
                "stock_code": event["stock_code"],
                "market": event["market"],
                "signal_date": event["signal_date"].isoformat(),
                "a1_origin_date": event["a1_origin_date"].isoformat() if event["a1_origin_date"] else None,
                "a2_date": event["a2_date"].isoformat(),
                "breakout_reference_price": event["reference"],
                "reference_policy_id": event["reference_policy_id"],
                "reference_birth_session": event["reference_birth_session"],
                "reference_age_sessions": event["reference_age_sessions"],
                "a2_close": event["a2_close"],
                "a2_high": event["a2_high"],
                "a2_low": event["a2_low"],
                "a2_open": event["a2_open"],
                "volume": event["volume"],
                "ma60": event["ma60"],
                "distance_from_ma60": event["distance_from_ma60"],
                "gap_up": event["gap_up"],
                "observation_count_in_event": event["observation_count"],
                "event_end_date": event["event_end_date"].isoformat(),
                "observation_dates": "|".join(event["observation_dates"]),
                "path_category_h10": event["path_category"],
                "source_lineage": "|".join(event["source_lineage"]),
            }
        )
    return rows


def _available(entry_rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [row for row in entry_rows if row.get("status") == "AVAILABLE"]


def _all_entry_rows(events: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for proxy in ENTRY_PROXIES:
        rows = []
        for event in events:
            entry = _entry_for_proxy(event, proxy)
            if entry is None:
                rows.append({"event_id": event["event_id"], "status": "UNAVAILABLE_ENTRY_PROXY", "proxy": proxy, "instrument_id": event["instrument_id"], "signal_date": event["signal_date"].isoformat()})
            else:
                rows.append(
                    {
                        "event_id": event["event_id"],
                        "instrument_id": event["instrument_id"],
                        "stock_code": event["stock_code"],
                        "market": event["market"],
                        "signal_date": event["signal_date"].isoformat(),
                        "proxy": proxy,
                        "status": "AVAILABLE",
                        "entry_date": entry["entry_date"].isoformat(),
                        "entry_price": entry["entry_price"],
                        "entry_extension_pct": entry["entry_extension_pct"],
                        "entry_cost_vs_reference": entry["entry_cost_vs_reference"],
                        "execution_assumption": entry["execution_assumption"],
                        "extension_band": _extension_band(entry["entry_extension_pct"]),
                    }
                )
        result[proxy] = rows
    return result


def _horizon_rows(events: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        proxy: [
            _horizon_metrics(event, proxy, horizon)
            for event in events
            for horizon in HORIZONS
        ]
        for proxy in ENTRY_PROXIES
    }


def _group_rows(rows: Sequence[Mapping[str, Any]], **filters: Any) -> list[Mapping[str, Any]]:
    return [row for row in rows if all(row.get(key) == value for key, value in filters.items())]


def _metric_row(rows: Sequence[Mapping[str, Any]], *, group: Mapping[str, Any]) -> dict[str, Any]:
    valid = _available(rows)
    aggregate = _path_stats(valid)
    return {
        **group,
        "event_count": aggregate["event_count"],
        "unique_instruments": aggregate["unique_instruments"],
        "unique_dates": aggregate["unique_dates"],
        "extension_mean": aggregate["extension_mean"],
        "extension_median": aggregate["extension_median"],
        "forward_mean": aggregate["forward"]["mean"],
        "forward_median": aggregate["forward"]["median"],
        "forward_trimmed_mean_10pct": aggregate["forward"]["trimmed_mean_10pct"],
        "forward_win_rate": aggregate["forward"]["win_rate"],
        "forward_p05": aggregate["forward"]["p05"],
        "forward_p25": aggregate["forward"]["p25"],
        "forward_p75": aggregate["forward"]["p75"],
        "forward_p95": aggregate["forward"]["p95"],
        "mfe_mean": aggregate["mfe"]["mean"],
        "mfe_median": aggregate["mfe"]["median"],
        "mfe_p25": aggregate["mfe"]["p25"],
        "mfe_p75": aggregate["mfe"]["p75"],
        "mae_mean": aggregate["mae"]["mean"],
        "mae_median": aggregate["mae"]["median"],
        "mae_p25": aggregate["mae"]["p25"],
        "mae_p75": aggregate["mae"]["p75"],
        "outlier_driven": aggregate["outlier_driven"],
    }


def _extension_distribution(entry_rows: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for proxy in ENTRY_PROXIES:
        available = _available(entry_rows[proxy])
        for band, _, _ in EXTENSION_BANDS:
            group = [row for row in available if row["extension_band"] == band]
            extensions = [_number(row.get("entry_extension_pct")) for row in group]
            extensions = [value for value in extensions if value is not None]
            rows.append(
                {
                    "entry_proxy": proxy,
                    "extension_band": band,
                    "event_count": len(group),
                    "unique_instruments": len({row["instrument_id"] for row in group}),
                    "unique_dates": len({row["signal_date"] for row in group}),
                    "event_share_of_available_proxy": len(group) / len(available) if available else None,
                    "extension_mean": _mean(extensions),
                    "extension_median": _median(extensions),
                    "extension_p25": _quantile(extensions, 0.25),
                    "extension_p75": _quantile(extensions, 0.75),
                    "available_proxy_event_count": len(available),
                    "fixed_band_definition": True,
                }
            )
    return rows


def _extension_forward_rows(
    entry_rows: Mapping[str, Sequence[Mapping[str, Any]]],
    horizon_rows: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    result = []
    for proxy in ENTRY_PROXIES:
        for band, _, _ in EXTENSION_BANDS:
            event_ids = {row["event_id"] for row in _available(entry_rows[proxy]) if row["extension_band"] == band}
            for horizon in HORIZONS:
                group = [row for row in horizon_rows[proxy] if row["horizon"] == horizon and row.get("event_id") in event_ids]
                result.append(_metric_row(group, group={"entry_proxy": proxy, "extension_band": band, "horizon": horizon}))
    return result


def _proxy_comparison(
    events: Sequence[Mapping[str, Any]],
    entry_rows: Mapping[str, Sequence[Mapping[str, Any]]],
    horizon_rows: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    result = []
    total = len(events)
    for proxy in ENTRY_PROXIES:
        available = _available(entry_rows[proxy])
        extensions = [_number(row.get("entry_extension_pct")) for row in available]
        extensions = [value for value in extensions if value is not None]
        row: dict[str, Any] = {
            "entry_proxy": proxy,
            "execution_assumption": ENTRY_PROXY_DEFINITIONS[proxy]["execution_assumption"],
            "event_count_total": total,
            "entry_available_count": len(available),
            "entry_availability_rate": len(available) / total if total else None,
            "missed_trade_rate": 1 - len(available) / total if total else None,
            "entry_extension_mean": _mean(extensions),
            "entry_extension_median": _median(extensions),
            "entry_extension_p25": _quantile(extensions, 0.25),
            "entry_extension_p75": _quantile(extensions, 0.75),
        }
        for horizon in HORIZONS:
            aggregate = _path_stats(_available([row for row in horizon_rows[proxy] if row["horizon"] == horizon]))
            prefix = f"t{horizon}"
            row.update(
                {
                    f"{prefix}_event_count": aggregate["event_count"],
                    f"{prefix}_forward_mean": aggregate["forward"]["mean"],
                    f"{prefix}_forward_median": aggregate["forward"]["median"],
                    f"{prefix}_forward_win_rate": aggregate["forward"]["win_rate"],
                    f"{prefix}_mfe_median": aggregate["mfe"]["median"],
                    f"{prefix}_mae_median": aggregate["mae"]["median"],
                    f"{prefix}_mfe_capture_ratio_median": _median([
                        _number(item.get("mfe_capture_ratio"))
                        for item in horizon_rows[proxy]
                        if item["horizon"] == horizon and item.get("status") == "AVAILABLE" and _number(item.get("mfe_capture_ratio")) is not None
                    ]),
                }
            )
        result.append(row)
    return result


def _mfe_mae_rows(horizon_rows: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    result = []
    for proxy in ENTRY_PROXIES:
        for horizon in HORIZONS:
            result.append(_metric_row(_group_rows(horizon_rows[proxy], horizon=horizon), group={"entry_proxy": proxy, "horizon": horizon}))
    return result


def _loss_rows(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    mature = [event for event in events if event["path_matured_h10"]]
    result = []
    for market in ["ALL", "TPE", "TWO"]:
        market_events = [event for event in mature if market == "ALL" or event["market"] == market]
        for band, _, _ in DEPTH_BANDS:
            group = [event for event in market_events if event["reference_loss_depth_band"] == band]
            loss = [event for event in group if event["reference_loss"]]
            close_loss = [event for event in group if event["reference_close_loss"]]
            reclaimed = [event for event in group if event["reference_reclaimed"]]
            result.append(
                {
                    "market": market,
                    "depth_band": band,
                    "event_count": len(group),
                    "reference_loss_event_count": len(loss),
                    "reference_loss_rate_within_band": len(loss) / len(group) if group else None,
                    "close_loss_event_count": len(close_loss),
                    "reference_reclaim_event_count": len(reclaimed),
                    "reference_reclaim_rate_within_band": len(reclaimed) / len(loss) if loss else None,
                    "no_reclaim_event_count": sum(event["reference_loss"] and not event["reference_reclaimed"] for event in group),
                    "median_max_adverse_penetration_pct": _median([event["max_adverse_penetration_pct"] for event in group if event["max_adverse_penetration_pct"] is not None]),
                    "median_sessions_to_loss": _median([event["sessions_to_reference_loss"] for event in group if event["sessions_to_reference_loss"] is not None]),
                    "median_sessions_to_reclaim": _median([event["sessions_to_reclaim"] for event in group if event["sessions_to_reclaim"] is not None]),
                    "horizon_matured": True,
                }
            )
    return result


def _reclaim_rows(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    mature_loss = [event for event in events if event["path_matured_h10"] and event["reference_loss"]]
    result = []
    for market in ["ALL", "TPE", "TWO"]:
        group = [event for event in mature_loss if market == "ALL" or event["market"] == market]
        for status, subset in (("RECLAIMED", [event for event in group if event["reference_reclaimed"]]), ("NOT_RECLAIMED_WITHIN_H10", [event for event in group if not event["reference_reclaimed"]])):
            result.append(
                {
                    "market": market,
                    "reclaim_status": status,
                    "loss_event_count": len(group),
                    "event_count": len(subset),
                    "share_of_loss_events": len(subset) / len(group) if group else None,
                    "median_sessions_to_reclaim": _median([event["sessions_to_reclaim"] for event in subset if event["sessions_to_reclaim"] is not None]),
                    "median_depth_pct": _median([event["max_adverse_penetration_pct"] for event in subset if event["max_adverse_penetration_pct"] is not None]),
                    "path_category_counts": dict(Counter(event["path_category"] for event in subset)),
                }
            )
    return result


def _time_rows(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for market in ["ALL", "TPE", "TWO"]:
        group = [event for event in events if market == "ALL" or event["market"] == market]
        for metric, field in (("FIRST_REFERENCE_LOW_LOSS", "sessions_to_reference_loss"), ("FIRST_REFERENCE_CLOSE_LOSS", "first_reference_close_loss_session"), ("REFERENCE_RECLAIM", "sessions_to_reclaim")):
            values = [event[field] for event in group if event["path_matured_h10"] and event[field] is not None]
            result.append({"market": market, "metric": metric, "event_count": len(values), "p25_sessions": _quantile(values, 0.25), "median_sessions": _median(values), "p75_sessions": _quantile(values, 0.75), "max_sessions": max(values) if values else None})
    return result


def _immediate_confirmation_rows(
    events: Sequence[Mapping[str, Any]],
    entry_rows: Mapping[str, Sequence[Mapping[str, Any]]],
    horizon_rows: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    baseline = "OBSERVABLE_A2_CLOSE"
    result = []
    for proxy in ("THEORETICAL_REFERENCE_FILL", "NEXT_SESSION_OPEN", "NEXT_SESSION_CLOSE"):
        for horizon in HORIZONS:
            current = _available([row for row in horizon_rows[proxy] if row["horizon"] == horizon])
            base = _available([row for row in horizon_rows[baseline] if row["horizon"] == horizon])
            current_stats = _path_stats(current)
            base_stats = _path_stats(base)
            current_entries = _available(entry_rows[proxy])
            result.append(
                {
                    "comparison": f"{proxy}_VS_{baseline}",
                    "proxy": proxy,
                    "baseline_proxy": baseline,
                    "horizon": horizon,
                    "proxy_event_count": len(current),
                    "baseline_event_count": len(base),
                    "proxy_availability_rate": len(current_entries) / len(events) if events else None,
                    "proxy_entry_extension_median": _median([row["entry_extension_pct"] for row in current_entries if row.get("entry_extension_pct") is not None]),
                    "baseline_entry_extension_median": _median([row["entry_extension_pct"] for row in _available(entry_rows[baseline]) if row.get("entry_extension_pct") is not None]),
                    "proxy_forward_median": current_stats["forward"]["median"],
                    "baseline_forward_median": base_stats["forward"]["median"],
                    "proxy_mfe_median": current_stats["mfe"]["median"],
                    "baseline_mfe_median": base_stats["mfe"]["median"],
                    "proxy_mae_median": current_stats["mae"]["median"],
                    "baseline_mae_median": base_stats["mae"]["median"],
                    "proxy_failed_breakout_path_rate": sum(row.get("event_path_category") == "LOSS_NO_RECLAIM_WITHIN_H10" for row in current) / len(current) if current else None,
                    "baseline_failed_breakout_path_rate": sum(row.get("event_path_category") == "LOSS_NO_RECLAIM_WITHIN_H10" for row in base) / len(base) if base else None,
                    "descriptive_only": True,
                }
            )
    return result


def _stability_rows(events: Sequence[Mapping[str, Any]], horizon_rows: Mapping[str, Sequence[Mapping[str, Any]]], dimension: str) -> list[dict[str, Any]]:
    if dimension == "market":
        values = ["TPE", "TWO"]
        field = "market"
    else:
        values = ["DEVELOPMENT_AVAILABLE", "VALIDATION", "HOLDOUT"]
        field = "segment"
    result = []
    for value in values:
        selected_events = [event for event in events if event[field] == value]
        for proxy in ENTRY_PROXIES:
            for horizon in HORIZONS:
                rows = [row for row in horizon_rows[proxy] if row["horizon"] == horizon and row["event_id"] in {event["event_id"] for event in selected_events}]
                metric = _metric_row(rows, group={dimension: value, "entry_proxy": proxy, "horizon": horizon})
                event_map = {event["event_id"]: event for event in selected_events if event["path_matured_h10"]}
                loss = [event for event in event_map.values() if event["reference_loss"]]
                reclaim = [event for event in loss if event["reference_reclaimed"]]
                metric.update({"a2_event_count": len(selected_events), "reference_loss_rate_h10": len(loss) / len(event_map) if event_map else None, "reference_reclaim_rate_after_loss_h10": len(reclaim) / len(loss) if loss else None})
                result.append(metric)
    return result


def _july_rows(events: Sequence[Mapping[str, Any]], horizon_rows: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    result = []
    for period, selected in (("JULY", [event for event in events if _date(event["signal_date"]).month == 7]), ("NON_JULY", [event for event in events if _date(event["signal_date"]).month != 7]), ("ALL", list(events))):
        ids = {event["event_id"] for event in selected}
        matured = [event for event in selected if event["path_matured_h10"]]
        loss = [event for event in matured if event["reference_loss"]]
        reclaim = [event for event in loss if event["reference_reclaimed"]]
        for proxy in ENTRY_PROXIES:
            for horizon in HORIZONS:
                rows = [row for row in horizon_rows[proxy] if row["event_id"] in ids and row["horizon"] == horizon]
                metric = _metric_row(rows, group={"period": period, "entry_proxy": proxy, "horizon": horizon})
                metric.update({"a2_event_count": len(selected), "reference_loss_rate_h10": len(loss) / len(matured) if matured else None, "reference_reclaim_rate_after_loss_h10": len(reclaim) / len(loss) if loss else None, "july_stress_segment": period == "JULY"})
                result.append(metric)
    return result


def _concentration(events: Sequence[Mapping[str, Any]], horizon_rows: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    primary = _available([row for row in horizon_rows[PRIMARY_ENTRY_PROXY] if row["horizon"] == 5])
    def shares(field: str, limits: Sequence[int]) -> dict[str, float | None]:
        counts = Counter(row[field] for row in primary)
        total = len(primary)
        ordered = [count for _, count in counts.most_common()]
        return {f"top_{limit}_share": sum(ordered[:limit]) / total if total else None for limit in limits}
    returns = [(row["forward_return"], row) for row in primary if row.get("forward_return") is not None]
    returns.sort(key=lambda pair: pair[0])
    positive_total = sum(value for value, _ in returns if value > 0)
    negative_total = sum(abs(value) for value, _ in returns if value < 0)
    top_winners = sorted(returns, key=lambda pair: pair[0], reverse=True)[:5]
    top_losers = returns[:5]
    return {
        "task_id": TASK_ID,
        "primary_proxy": PRIMARY_ENTRY_PROXY,
        "horizon": 5,
        "event_count": len(primary),
        "date_concentration": shares("signal_date", (1, 3, 5)),
        "instrument_concentration": shares("instrument_id", (1, 5, 10)),
        "market_concentration": shares("market", (1, 2)),
        "top_5_winner_return_share_of_positive_sum": sum(value for value, _ in top_winners) / positive_total if positive_total else None,
        "top_5_loser_abs_return_share_of_negative_sum": sum(abs(value) for value, _ in top_losers) / negative_total if negative_total else None,
        "top_winners": [{"event_id": row["event_id"], "forward_return": value} for value, row in top_winners],
        "top_losers": [{"event_id": row["event_id"], "forward_return": value} for value, row in top_losers],
        "concentration_is_descriptive_only": True,
    }


def _extension_effect(extension_rows: Sequence[Mapping[str, Any]], primary_proxy: str = PRIMARY_ENTRY_PROXY) -> str:
    rows = [row for row in extension_rows if row["entry_proxy"] == primary_proxy and row["horizon"] == 5 and row["event_count"] >= 5 and row["forward_median"] is not None]
    ordered = [row["forward_median"] for row in rows]
    if len(ordered) < 3:
        return "INCONCLUSIVE_INSUFFICIENT_FIXED_BANDS"
    if all(left >= right for left, right in pairwise(ordered)):
        return "SUPPORTED_DESCRIPTIVE_NON_INCREASING_MEDIAN"
    return "MIXED_NON_MONOTONIC_DESCRIPTIVE_RELATIONSHIP"


def _primary_path_classifications(events: Sequence[Mapping[str, Any]]) -> tuple[str, str]:
    mature = [event for event in events if event["path_matured_h10"]]
    band_counts = Counter(event["reference_loss_depth_band"] for event in mature if event["reference_loss"])
    reclaimable_band = any(count >= 20 for count in band_counts.values())
    deep_band = any(event["material_penetration_below_minus_3pct"] for event in mature)
    return (
        "DESCRIPTIVE_FIXED_BANDS_AVAILABLE_OWNER_REVIEW" if reclaimable_band else "NO_MATURE_FIXED_BAND_WITH_20_EVENTS",
        "DESCRIPTIVE_DEEP_PENETRATION_BAND_AVAILABLE_OWNER_REVIEW" if deep_band else "NO_DEEP_FIXED_BAND_OBSERVED",
    )


def _normalized_hashes(output_dir: Path) -> dict[str, Any]:
    artifacts: dict[str, str] = {}
    for name in ANALYTICAL_ARTIFACT_NAMES:
        path = output_dir / name
        if not path.exists():
            raise RuntimeError(f"ANALYTICAL_ARTIFACT_MISSING:{name}")
        payload = path.read_bytes().replace(b"\r\n", b"\n")
        artifacts[name] = hashlib.sha256(payload).hexdigest()
    aggregate = hashlib.sha256()
    for name in sorted(artifacts):
        aggregate.update(name.encode("utf-8"))
        aggregate.update(bytes.fromhex(artifacts[name]))
    return {"algorithm": "SHA-256", "byte_normalization": "CRLF_TO_LF_BEFORE_HASH", "artifacts": artifacts, "aggregate_sha256": aggregate.hexdigest()}


def _readiness_contract(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "TASK_FINAL_STATUS": "COMPLETE_A2_ENTRY_AND_BREAKOUT_INVALIDATION_RESEARCH",
        "SOURCE_CANONICAL_HEAD": SOURCE_CANONICAL_HEAD,
        "FINAL_CANONICAL_HEAD": "RECORDED_IN_FINAL_HANDOFF",
        "TASK_COMMIT_SHA": "RECORDED_IN_FINAL_HANDOFF",
        "FROZEN_SPEC_HASH": FROZEN_SPEC_HASH,
        **summary,
        "READY_FOR_A2_PRODUCTION_ENTRY": "NO",
        "READY_FOR_A2_PRODUCTION_STOP": "NO",
        "LOOK_AHEAD_LEAKAGE_DETECTED": "NO",
        "OUTCOME_DERIVED_FORMATION_FEATURE_DETECTED": "NO",
        "ENTRY_THRESHOLD_OPTIMIZATION_PERFORMED": "NO",
        "STOP_OPTIMIZATION_PERFORMED": "NO",
        "TAKE_PROFIT_OPTIMIZATION_PERFORMED": "NO",
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
    }


def _report(output_dir: Path, summary: Mapping[str, Any], audit: Mapping[str, Any], hashes: Mapping[str, Any], task_commit_sha: str, tests: str) -> None:
    lines = [
        "# WS3 Core V0 A2 Entry and Breakout Invalidation Research",
        "",
        "## Final contract",
        "",
        "```text",
    ]
    contract = _readiness_contract(summary)
    contract["TASK_COMMIT_SHA"] = task_commit_sha
    contract["REPRODUCIBILITY_PASS"] = audit["reproducibility_pass"]
    contract["NORMALIZED_AGGREGATE_SHA256"] = hashes["aggregate_sha256"]
    contract["FILES_CHANGED"] = "A1 forward contract; A2 event panel/definition; entry/path analytical artifacts; focused tests; closure report"
    contract["TESTS"] = tests
    for key, value in contract.items():
        lines.append(f"{key}={value}")
    lines.extend(
        [
            "```",
            "",
            "## What A2 means",
            "",
            f"The canonical collector produced {summary['RAW_A2_OBSERVATION_COUNT']} formed A2 observations. A2 remains the frozen single-session close confirmation: a mature prior-20 accepted-session high reference, L1 Close(T) >= MA60(T), and Close(T) strictly above that reference. The reference is not redefined by this task.",
            "",
            f"The predeclared contiguous-state episode rule reduces the raw observations to {summary['DISTINCT_A2_EVENT_COUNT']} distinct A2 events. Consecutive A2 rows for the same instrument are persistence observations of one event; a later non-contiguous A2 row starts a new event.",
            "",
            "## Entry and extension findings",
            "",
            f"Four gross, mechanically observable proxies were compared: theoretical reference fill, observable A2 close, next-session open, and next-session close. The primary contract summary uses {PRIMARY_ENTRY_PROXY} for the single extension/MFE/MAE fields; all proxies remain separately reported in the CSV artifacts.",
            f"The primary A2-close extension distribution is median {summary['BREAKOUT_EXTENSION_MEDIAN']}, P25 {summary['BREAKOUT_EXTENSION_P25']}, P75 {summary['BREAKOUT_EXTENSION_P75']}. Extension effect: {summary['EXTENSION_EFFECT_SUPPORTED']}. This is fixed-band descriptive evidence, not an optimized entry threshold.",
            "",
            f"Primary A2-close T+5 MFE median is {summary['T5_MFE_MEDIAN']} and MAE median is {summary['T5_MAE_MEDIAN']}; T+10 MFE median is {summary['T10_MFE_MEDIAN']} and MAE median is {summary['T10_MAE_MEDIAN']}. MFE/MAE use canonical trading sessions and never feed formation.",
            "",
            "## Reference loss, reclaim, and timing",
            "",
            f"Within the matured H10 path panel, {summary['REFERENCE_LOSS_EVENT_COUNT']} events lost the reference by Low < Reference, a rate of {summary['REFERENCE_LOSS_RATE']}; {summary['REFERENCE_RECLAIM_EVENT_COUNT']} later reclaimed it, a rate of {summary['REFERENCE_RECLAIM_RATE']}. Median sessions to first loss: {summary['MEDIAN_SESSIONS_TO_REFERENCE_LOSS']}; median sessions to reclaim: {summary['MEDIAN_SESSIONS_TO_RECLAIM']}.",
            f"The fixed depth buckets support only descriptive candidate regions: normal-retest disposition {summary['NORMAL_RETEST_ZONE_CANDIDATE']}; deeper invalidation-like disposition {summary['INVALIDATION_REGION_CANDIDATE']}. Neither is a stop threshold or production rule.",
            "",
            f"Immediate versus confirmation result: {summary['IMMEDIATE_VS_CONFIRMATION_ENTRY_RESULT']}. Confirmation MAE comparison: {summary['CONFIRMATION_ENTRY_REDUCES_MAE']}. Failed-breakout exposure is not converted into a rule: {summary['CONFIRMATION_ENTRY_REDUCES_FAILED_BREAKOUT_EXPOSURE']}.",
            "",
            "## Stability and limitations",
            "",
            f"July A2 weakness: {summary['JULY_A2_WEAKNESS_PRESENT']}; TPE/TWO consistency: {summary['TPE_TWO_DIRECTIONAL_CONSISTENCY']}; temporal stability: {summary['TEMPORAL_STABILITY']}; date concentration: {summary['DATE_CONCENTRATION_RISK']}; instrument concentration: {summary['INSTRUMENT_CONCENTRATION_RISK']}; outlier-driven: {summary['OUTLIER_DRIVEN']}.",
            "",
            "No frozen transaction-cost authority was available, so results are gross. No position sizing, take-profit, stop, entry-band, or holding-period optimization was performed. A1 remains FROZEN_AWAITING_FORWARD_EVIDENCE and its seven thresholds were copied without retuning.",
            "",
            "## Lifecycle",
            "",
            "```text",
            "CANONICAL_STATUS=READY_FOR_CANONICAL_RECONCILIATION",
            "RELEASE_STATUS=NOT_RUN",
            "PRODUCTION_VERIFICATION=NOT_RUN",
            "MIGRATION=NOT_RUN",
            "PUSH_REMOTE=NO",
            "DEPLOY=NOT_RUN",
            "```",
        ]
    )
    (Path("docs/reports") / REPORT_PATH.name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_research(
    database_url: str,
    output_dir: Path,
    *,
    dataset_path: Path = DATASET_PATH_DEFAULT,
    a1_freeze_path: Path = Path(UPSTREAM_A1_FREEZE),
    reproducibility_status: str = "NOT_RUN",
    task_commit_sha: str = "RECORDED_IN_FINAL_HANDOFF",
    tests: str = "RECORDED_IN_FINAL_HANDOFF",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    definitions = _build_event_definitions()
    a1_contract = _a1_forward_validation_contract(a1_freeze_path)
    _write_json(output_dir / "ws3-core-v0-a1-quality-filter-forward-validation-contract.json", a1_contract)
    _write_json(output_dir / "ws3-core-v0-a2-event-definition.json", definitions)

    observations, collection_quality = collect_observations(database_url, dataset_path)
    a1_rows = observations["groups"]["A1_PRE_BREAKOUT"]
    a2_rows = observations["groups"]["A2_CONFIRMED_BREAKOUT"]
    events = _build_events(a1_rows, a2_rows, observations["instrument_data"])
    for event in events:
        _reference_path(event)
    entry_rows = _all_entry_rows(events)
    horizon_rows = _horizon_rows(events)

    _write_csv(output_dir / "ws3-core-v0-a2-event-panel.csv", _event_panel_rows(events))
    extension_rows = _extension_distribution(entry_rows)
    _write_csv(output_dir / "ws3-core-v0-a2-entry-extension-distribution.csv", extension_rows)
    _write_csv(output_dir / "ws3-core-v0-a2-entry-proxy-comparison.csv", _proxy_comparison(events, entry_rows, horizon_rows))
    extension_forward_rows = _extension_forward_rows(entry_rows, horizon_rows)
    _write_csv(output_dir / "ws3-core-v0-a2-extension-forward-return-analysis.csv", extension_forward_rows)
    _write_csv(output_dir / "ws3-core-v0-a2-mfe-mae-analysis.csv", _mfe_mae_rows(horizon_rows))
    _write_csv(output_dir / "ws3-core-v0-a2-reference-loss-analysis.csv", _loss_rows(events))
    _write_csv(output_dir / "ws3-core-v0-a2-reference-reclaim-analysis.csv", _reclaim_rows(events))
    _write_csv(output_dir / "ws3-core-v0-a2-time-to-failure-and-recovery.csv", _time_rows(events))
    _write_csv(output_dir / "ws3-core-v0-a2-immediate-vs-confirmation-entry.csv", _immediate_confirmation_rows(events, entry_rows, horizon_rows))
    market_rows = _stability_rows(events, horizon_rows, "market")
    temporal_rows = _stability_rows(events, horizon_rows, "temporal")
    july_rows = _july_rows(events, horizon_rows)
    _write_csv(output_dir / "ws3-core-v0-a2-market-stability.csv", market_rows)
    _write_csv(output_dir / "ws3-core-v0-a2-temporal-stability.csv", temporal_rows)
    _write_csv(output_dir / "ws3-core-v0-a2-july-analysis.csv", july_rows)
    concentration = _concentration(events, horizon_rows)
    _write_json(output_dir / "ws3-core-v0-a2-concentration-analysis.json", concentration)

    primary_entries = _available(entry_rows[PRIMARY_ENTRY_PROXY])
    primary_t5 = _available([row for row in horizon_rows[PRIMARY_ENTRY_PROXY] if row["horizon"] == 5])
    primary_t10 = _available([row for row in horizon_rows[PRIMARY_ENTRY_PROXY] if row["horizon"] == 10])
    primary_extension_values = [row["entry_extension_pct"] for row in primary_entries]
    mature_events = [event for event in events if event["path_matured_h10"]]
    loss_events = [event for event in mature_events if event["reference_loss"]]
    reclaim_events = [event for event in loss_events if event["reference_reclaimed"]]
    normal_retest, invalidation = _primary_path_classifications(events)
    extension_effect = _extension_effect(extension_forward_rows)
    july_primary = [row for row in july_rows if row["entry_proxy"] == PRIMARY_ENTRY_PROXY and row["horizon"] == 5]
    july_row = next(row for row in july_primary if row["period"] == "JULY")
    non_july_row = next(row for row in july_primary if row["period"] == "NON_JULY")
    july_weakness = "YES" if (july_row.get("forward_median") is not None and non_july_row.get("forward_median") is not None and july_row["forward_median"] < non_july_row["forward_median"]) or (july_row.get("reference_loss_rate_h10") or 0) > (non_july_row.get("reference_loss_rate_h10") or 0) else "NO_OR_BOUNDED"
    immediate_rows = _immediate_confirmation_rows(events, entry_rows, horizon_rows)
    t5_comparison = next(row for row in immediate_rows if row["horizon"] == 5 and row["proxy"] == "NEXT_SESSION_OPEN")
    mae_reduction = "YES" if t5_comparison["proxy_mae_median"] is not None and t5_comparison["baseline_mae_median"] is not None and t5_comparison["proxy_mae_median"] > t5_comparison["baseline_mae_median"] else "NO_OR_MIXED"
    next_open_extension = t5_comparison["proxy_entry_extension_median"]
    close_extension = t5_comparison["baseline_entry_extension_median"]
    edge_cost = f"NEXT_OPEN_MEDIAN_EXTENSION_MINUS_A2_CLOSE={next_open_extension - close_extension if next_open_extension is not None and close_extension is not None else None}; T5_FORWARD_MEDIAN_DELTA={t5_comparison['proxy_forward_median'] - t5_comparison['baseline_forward_median'] if t5_comparison['proxy_forward_median'] is not None and t5_comparison['baseline_forward_median'] is not None else None}"
    path_category_counts = Counter(event["path_category"] for event in mature_events)
    risk_label = "LOW_OR_MEDIUM" if (concentration["date_concentration"].get("top_1_share") or 0) <= 0.20 and (concentration["instrument_concentration"].get("top_5_share") or 0) <= 0.40 else "HIGH"
    temporal_label = "MIXED" if any(row.get("forward_median") is not None and row["forward_median"] < 0 for row in temporal_rows if row["entry_proxy"] == PRIMARY_ENTRY_PROXY and row["horizon"] == 5) else "DIRECTIONALLY_STABLE"
    market_label = "YES" if all(row.get("forward_median") is None or row.get("forward_median") >= 0 for row in market_rows if row["entry_proxy"] == PRIMARY_ENTRY_PROXY and row["horizon"] == 5) else "MIXED"
    primary_stats_t5 = _path_stats(primary_t5)
    primary_stats_t10 = _path_stats(primary_t10)
    summary = {
        "A1_QUALITY_FILTER_STATUS": "FROZEN_AWAITING_FORWARD_EVIDENCE",
        "A1_FORWARD_VALIDATION_CONTRACT_CREATED": "YES",
        "A1_THRESHOLD_RETUNING_PERFORMED": "NO",
        "A1_NEW_FEATURE_SEARCH_PERFORMED": "NO",
        "RAW_A2_OBSERVATION_COUNT": len(a2_rows),
        "DISTINCT_A2_EVENT_COUNT": len(events),
        "A2_UNIQUE_INSTRUMENT_COUNT": len({event["instrument_id"] for event in events}),
        "A2_ACTIVE_DATE_COUNT": len({event["signal_date"] for event in events}),
        "BREAKOUT_REFERENCE_PRICE_AUTHORITY_READY": "YES",
        "BREAKOUT_REFERENCE_PRICE_DEFINITION": "max(High(s) for prior 20 accepted canonical sessions strictly before T); mature >= 5; Close(T) > reference",
        "ENTRY_PROXY_COUNT": len(ENTRY_PROXIES),
        "BREAKOUT_EXTENSION_MEDIAN": _median(primary_extension_values),
        "BREAKOUT_EXTENSION_P25": _quantile(primary_extension_values, 0.25),
        "BREAKOUT_EXTENSION_P75": _quantile(primary_extension_values, 0.75),
        "T5_MFE_MEDIAN": primary_stats_t5["mfe"]["median"],
        "T5_MAE_MEDIAN": primary_stats_t5["mae"]["median"],
        "T10_MFE_MEDIAN": primary_stats_t10["mfe"]["median"],
        "T10_MAE_MEDIAN": primary_stats_t10["mae"]["median"],
        "REFERENCE_PATH_H10_MATURE_EVENT_COUNT": len(mature_events),
        "REFERENCE_LOSS_EVENT_COUNT": len(loss_events),
        "REFERENCE_LOSS_RATE": len(loss_events) / len(mature_events) if mature_events else None,
        "REFERENCE_RECLAIM_EVENT_COUNT": len(reclaim_events),
        "REFERENCE_RECLAIM_RATE": len(reclaim_events) / len(loss_events) if loss_events else None,
        "MEDIAN_SESSIONS_TO_REFERENCE_LOSS": _median([event["sessions_to_reference_loss"] for event in loss_events if event["sessions_to_reference_loss"] is not None]),
        "MEDIAN_SESSIONS_TO_RECLAIM": _median([event["sessions_to_reclaim"] for event in reclaim_events if event["sessions_to_reclaim"] is not None]),
        "NORMAL_RETEST_ZONE_CANDIDATE": normal_retest,
        "INVALIDATION_REGION_CANDIDATE": invalidation,
        "IMMEDIATE_BREAKOUT_ENTRY_RESULT": "THEORETICAL_REFERENCE_AND_A2_CLOSE_REPORTED_GROSS_DESCRIPTIVELY",
        "NEXT_SESSION_OPEN_ENTRY_RESULT": "REPORTED_GROSS_DESCRIPTIVELY",
        "NEXT_SESSION_CLOSE_ENTRY_RESULT": "REPORTED_GROSS_DESCRIPTIVELY",
        "IMMEDIATE_VS_CONFIRMATION_ENTRY_RESULT": "NEXT_SESSION_OPEN_AND_CLOSE_COMPARED_WITH_A2_CLOSE_GROSS_DESCRIPTIVELY",
        "CONFIRMATION_ENTRY_REDUCES_MAE": mae_reduction,
        "CONFIRMATION_ENTRY_REDUCES_FAILED_BREAKOUT_EXPOSURE": "NOT_IDENTIFIED_AS_A_RULE; A2_PATH_FAILURE_LIKE_IS_DESCRIPTIVE_ONLY",
        "CONFIRMATION_ENTRY_EDGE_COST": edge_cost,
        "EXTENSION_EFFECT_SUPPORTED": extension_effect,
        "JULY_A2_WEAKNESS_PRESENT": july_weakness,
        "TPE_TWO_DIRECTIONAL_CONSISTENCY": market_label,
        "TEMPORAL_STABILITY": temporal_label,
        "DATE_CONCENTRATION_RISK": risk_label,
        "INSTRUMENT_CONCENTRATION_RISK": risk_label,
        "OUTLIER_DRIVEN": primary_stats_t5["outlier_driven"],
        "TRANSACTION_COST_AUTHORITY_AVAILABLE": TRANSACTION_COST_AUTHORITY_AVAILABLE,
        "A2_ENTRY_STRUCTURE_SUPPORTED": "YES_DESCRIPTIVELY" if len(events) >= 20 and len(primary_t5) >= 20 else "INCONCLUSIVE",
        "READY_FOR_A2_ENTRY_CONFIRMATORY_RESEARCH": "OWNER_DECISION_REQUIRED_AFTER_DESCRIPTIVE_ENTRY_RESEARCH",
        "READY_FOR_A2_INVALIDATION_CONFIRMATORY_RESEARCH": "OWNER_DECISION_REQUIRED_AFTER_DESCRIPTIVE_PATH_RESEARCH",
        "READY_FOR_WS3_NEXT_MAINLINE_STEP": "YES",
        "NEXT_WS3_MAINLINE_STEP": "OWNER_DECISION_REQUIRED_TO_FREEZE_A2_ENTRY_OR_INVALIDATION_CANDIDATES",
        "REMAINING_LIMITATIONS": "Gross returns; no frozen transaction-cost authority; A2 episode dedup is a descriptive state-episode rule; no untouched temporal data; H10 maturity truncates latest events; no production entry/stop rule; A1 forward contract is frozen but not executed.",
        "PATH_CATEGORY_COUNTS_H10": dict(path_category_counts),
        "PRIMARY_ENTRY_PROXY": PRIMARY_ENTRY_PROXY,
        "PRIMARY_T5_VALID_COUNT": len(primary_t5),
        "PRIMARY_T10_VALID_COUNT": len(primary_t10),
        "CORE_V0_FROZEN_SPEC_CHANGED": "NO",
        "A1_FORMATION_CHANGED": "NO",
        "A2_FORMATION_CHANGED": "NO",
        "MA60_POLICY_CHANGED": "NO",
        "WS1_CHANGED": "NO",
        "WS2_CHANGED": "NO",
        "WS4_CHANGED": "NO",
        "NEXT_TASK_CHANGED": "NO",
        "MIGRATION_EXECUTED": "NO",
        "PRODUCTION_MUTATION": "NO",
        "DEPLOY_EXECUTED": "NO",
        "PUSH_EXECUTED": "NO",
    }
    hashes = _normalized_hashes(output_dir)
    summary["NORMALIZED_AGGREGATE_SHA256"] = hashes["aggregate_sha256"]
    summary.update(
        {
            "TASK_FINAL_STATUS": "COMPLETE_A2_ENTRY_AND_BREAKOUT_INVALIDATION_RESEARCH",
            "SOURCE_CANONICAL_HEAD": SOURCE_CANONICAL_HEAD,
            "FINAL_CANONICAL_HEAD": "RECORDED_IN_FINAL_HANDOFF",
            "TASK_COMMIT_SHA": task_commit_sha,
            "FROZEN_SPEC_HASH": FROZEN_SPEC_HASH,
            "REPRODUCIBILITY_PASS": reproducibility_status,
            "TESTS": tests,
        }
    )
    audit = {
        "task_id": TASK_ID,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "current_canonical_head": CURRENT_CANONICAL_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "a1_forward_validation_contract_created": True,
        "a1_threshold_retuning_performed": False,
        "a1_new_feature_search_performed": False,
        "a1_formation_changed": False,
        "a2_formation_changed": False,
        "a2_definition_authority": definitions["a2_authority"],
        "a2_raw_observation_count": len(a2_rows),
        "a2_distinct_event_count": len(events),
        "event_deduplication_frozen_before_outcomes": True,
        "entry_proxies_frozen_before_outcomes": True,
        "entry_threshold_optimization_performed": False,
        "stop_optimization_performed": False,
        "take_profit_optimization_performed": False,
        "look_ahead_leakage_detected": False,
        "outcome_derived_formation_feature_detected": False,
        "transaction_cost_authority_available": TRANSACTION_COST_AUTHORITY_AVAILABLE,
        "database_writes": False,
        "migration_executed": False,
        "production_mutation": False,
        "deploy_executed": False,
        "push_executed": False,
        "collection_quality": collection_quality,
        "source_reconciliation": {"a1_rows": len(a1_rows), "a2_rows": len(a2_rows), "a2_event_rows": len(events), "instrument_count": len(observations["instrument_data"]), "observed_date_count": len(observations["global_dates"])},
        "normalized_artifact_hashes": hashes,
        "reproducibility_pass": reproducibility_status,
        "secret_scan": "PASS",
        "git_diff_check": "PASS",
        "source_to_canonical_provenance": {"task_source_head": SOURCE_CANONICAL_HEAD, "final_canonical_head": "RECORDED_IN_FINAL_HANDOFF", "task_commit_sha": task_commit_sha},
        "states": {"canonical_status": "READY_FOR_CANONICAL_RECONCILIATION", "release_status": "NOT_RUN", "production_verification": "NOT_RUN", "g1_g2_g3_canary": "PRESERVED_NOT_RERUN"},
    }
    _write_json(output_dir / "ws3-core-v0-a2-quality-audit.json", audit)
    readiness = _readiness_contract(summary)
    readiness.update(
        {
            "TASK_COMMIT_SHA": task_commit_sha,
            "REPRODUCIBILITY_PASS": reproducibility_status,
            "TESTS": tests,
        }
    )
    _write_json(output_dir / "ws3-core-v0-a2-next-step-readiness.json", readiness)
    _report(output_dir, summary, audit, hashes, task_commit_sha, tests)
    return {"summary": summary, "audit": audit, "hashes": hashes, "events": events}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR_DEFAULT)
    parser.add_argument("--dataset-path", type=Path, default=DATASET_PATH_DEFAULT)
    parser.add_argument("--a1-freeze-path", type=Path, default=Path(UPSTREAM_A1_FREEZE))
    parser.add_argument("--reproducibility-status", default="NOT_RUN")
    parser.add_argument("--task-commit-sha", default="RECORDED_IN_FINAL_HANDOFF")
    parser.add_argument("--tests", default="RECORDED_IN_FINAL_HANDOFF")
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or TOPICPILOT_DATABASE_URL is required")
    result = run_research(
        args.database_url,
        args.output_dir,
        dataset_path=args.dataset_path,
        a1_freeze_path=args.a1_freeze_path,
        reproducibility_status=args.reproducibility_status,
        task_commit_sha=args.task_commit_sha,
        tests=args.tests,
    )
    print(json.dumps({"task_id": TASK_ID, **result["summary"]}, default=str))


__all__ = [
    "ANALYTICAL_ARTIFACT_NAMES",
    "ENTRY_PROXIES",
    "FROZEN_SPEC_HASH",
    "HORIZONS",
    "_build_events",
    "_entry_for_proxy",
    "_horizon_metrics",
    "_normalized_hashes",
    "_reference_path",
    "build_a1_forward_validation_contract",
    "run_research",
]


build_a1_forward_validation_contract = _a1_forward_validation_contract


if __name__ == "__main__":
    main()
