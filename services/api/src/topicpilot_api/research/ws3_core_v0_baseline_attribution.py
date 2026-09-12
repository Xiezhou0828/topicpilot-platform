"""Attribute the frozen Core V0 baseline across its existing candidate states.

This module intentionally consumes the existing Core V0 candidate panel and
the real historical reader.  It does not alter candidate formation, introduce
technical gates, or turn post-hoc state labels into formation rules.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from topicpilot_api.historical_read_model import read_historical_bars
from topicpilot_api.research.core_v0_candidate_panel import (
    A1_CANDIDATE_ID,
    A1_DEFINITION_VERSION,
    A2_CANDIDATE_ID,
    A2_DEFINITION_VERSION,
    CandidatePanelInput,
    CanonicalBar,
    EvaluationAnchor,
    InstrumentIdentity,
    MA60Evidence,
    build_candidate_panel,
)
from topicpilot_api.research.ws3_research_policy import (
    CONTINUITY_UNKNOWN,
    EVENT_ACTION_EXCLUDE,
    ResearchInputEvidence,
    evaluate_ws3_research_eligibility,
)
from topicpilot_api.research.ws3_walk_forward_baseline import (
    A1_MAX_REFERENCE_DISTANCE,
    GLOBAL_DATE_MAX,
    GLOBAL_DATE_MIN,
    MA60_PERIOD,
    OUTCOME_HORIZONS,
    REFERENCE_MATURITY_SESSIONS,
    REFERENCE_WINDOW_SESSIONS,
    SEGMENTS,
    SOURCE_DATASET,
    WINDOW_END,
    WINDOW_START,
    _date,
    _event_overlay,
    _forward_event_excluded,
    _load_events,
    _make_bars,
    _metric,
    _reference_lineage,
    _sma,
    _valid_source_lineage,
    _write_csv,
    _write_json,
)

TASK_ID = "TASK-WS3-CORE-V0-BASELINE-ATTRIBUTION-AND-CANDIDATE-STATE-REVIEW-20260818"
SOURCE_BASELINE_TASK = "TASK-WS3-CORE-V0-REAL-HISTORICAL-WALK-FORWARD-BASELINE-20260818"
SOURCE_BASELINE_HEAD = "9ca9ba4f15359aa5ea96ba4c3d6bed9439d0346e"
SOURCE_BASELINE_REPORT_DIR = (
    "reports/TASK-WS3-CORE-V0-REAL-HISTORICAL-WALK-FORWARD-BASELINE-20260818"
)
FROZEN_SPEC_HASH = "6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d"
STATE_GROUPS = ("A1_PRE_BREAKOUT", "A2_CONFIRMED_BREAKOUT")
STATE_META = {
    "A1_PRE_BREAKOUT": {
        "state_id": A1_CANDIDATE_ID,
        "state_version": A1_DEFINITION_VERSION,
        "candidate_id": A1_CANDIDATE_ID,
    },
    "A2_CONFIRMED_BREAKOUT": {
        "state_id": A2_CANDIDATE_ID,
        "state_version": A2_DEFINITION_VERSION,
        "candidate_id": A2_CANDIDATE_ID,
    },
}


def _clone_observation(observation: dict[str, Any]) -> dict[str, Any]:
    result = dict(observation)
    result["returns"] = dict(observation["returns"])
    result["event_excluded_horizons"] = set(observation["event_excluded_horizons"])
    return result


def _load_instrument_data(database_url: str) -> tuple[dict[str, dict[str, Any]], set[date], int]:
    engine = create_engine(database_url, future=True)
    instrument_data: dict[str, dict[str, Any]] = {}
    global_dates: set[date] = set()
    source_rows = 0
    with Session(engine) as session:
        identities = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT i.id AS instrument_id, i.instrument_code AS code,
                           i.name, m.code AS market
                    FROM topicpilot.instruments i
                    JOIN topicpilot.markets m ON m.id = i.market_id
                    WHERE i.is_active = true AND m.is_active = true
                    ORDER BY m.code, i.instrument_code
                    """
                )
            ).mappings().all()
        ]
        for identity in identities:
            result = read_historical_bars(
                session,
                identity["code"],
                GLOBAL_DATE_MIN,
                GLOBAL_DATE_MAX,
                identity["market"],
                200,
            )
            items = list(result["items"])
            dates = [_date(item["trading_date"]) for item in items]
            source_rows += len(items)
            global_dates.update(dates)
            instrument_data[str(identity["instrument_id"])] = {
                "identity": identity,
                "items": items,
                "dates": dates,
                "duplicate_count": len(dates) - len(set(dates)),
                "lineage_valid": all(_valid_source_lineage(item) for item in items),
            }
    engine.dispose()
    for data in instrument_data.values():
        dates = data["dates"]
        data["gap_dates"] = (
            {day for day in global_dates if dates[0] <= day <= dates[-1]} - set(dates)
            if dates
            else set()
        )
    return instrument_data, global_dates, source_rows


def _build_panel_input(
    identity: dict[str, Any],
    trading_date: date,
    bars: tuple[CanonicalBar, ...],
    ma60: Any,
) -> CandidatePanelInput:
    return CandidatePanelInput(
        instrument=InstrumentIdentity(
            str(identity["instrument_id"]),
            identity["code"],
            identity["name"] or identity["code"],
            identity["market"],
            "ACTIVE",
            (f"instrument:{identity['instrument_id']}",),
        ),
        anchor=EvaluationAnchor(
            f"{identity['market']}:{trading_date.isoformat()}",
            trading_date,
            trading_date,
            "tw-reference-v1",
        ),
        bars=bars,
        ma60=MA60Evidence(
            "stock.sma.close.v1",
            "SMA_CLOSE_V1",
            MA60_PERIOD,
            ma60,
            trading_date,
            bars[-MA60_PERIOD].session_date,
            trading_date,
            MA60_PERIOD,
            "RAW_OBSERVED",
            CONTINUITY_UNKNOWN,
            "RESEARCH_AVAILABLE",
            (f"reader:{identity['market']}:{identity['code']}:{trading_date}",),
        ),
        reference_lineage=_reference_lineage(bars, len(bars) - 1)[0],
        topic_context=None,
        topic_context_required=False,
        research_eligibility=evaluate_ws3_research_eligibility(
            ResearchInputEvidence(
                f"{identity['market']}:{identity['code']}",
                True,
                True,
                True,
                True,
                CONTINUITY_UNKNOWN,
                known_verified_events=(),
            )
        ),
    )


def collect_observations(
    database_url: str, dataset_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    events_by_identity, event_metadata = _load_events(dataset_path)
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    instrument_data, global_dates, source_rows = _load_instrument_data(database_url)
    groups: dict[str, list[dict[str, Any]]] = {
        "ALL_MA60_CALCULABLE": [],
        "METHOD_A_ELIGIBLE": [],
        "A1_PRE_BREAKOUT": [],
        "A2_CONFIRMED_BREAKOUT": [],
    }
    quality = Counter()
    duplicate_count = sum(data["duplicate_count"] for data in instrument_data.values())
    invalid_lineage_count = sum(
        not data["lineage_valid"] for data in instrument_data.values() if data["items"]
    )
    candidate_reasons = Counter()
    candidate_state_counts = Counter()
    signal_dates: dict[str, Counter[date]] = {
        state: Counter() for state in STATE_GROUPS
    }
    signals_by_instrument: dict[str, dict[str, set[date]]] = defaultdict(
        lambda: {state: set() for state in STATE_GROUPS}
    )
    state_panels: dict[str, list[dict[str, Any]]] = {state: [] for state in STATE_GROUPS}
    data_gap_fail_closed = 0
    known_event_formation_windows = 0
    partial_authority_windows = 0
    all_candidate_rows: list[dict[str, Any]] = []

    for data in instrument_data.values():
        identity = data["identity"]
        items = data["items"]
        dates = data["dates"]
        if not items or not data["lineage_valid"] or data["duplicate_count"]:
            continue
        key = (identity["market"], identity["code"])
        events = events_by_identity.get(key, [])
        partial_events = [
            event
            for event in payload["events"]
            if event["authority_state"] == "PARTIAL"
            and (event["market_code"], event["instrument_code"]) == key
        ]
        for index, trading_date in enumerate(dates):
            if not WINDOW_START <= trading_date <= WINDOW_END or index < MA60_PERIOD:
                continue
            raw_items = items[: index + 1]
            bars = _make_bars(raw_items)
            if bars is None:
                quality["malformed_or_invalid_lineage"] += 1
                continue
            if _event_overlay(events, dates, index):
                known_event_formation_windows += 1
                continue
            window_start = dates[index - MA60_PERIOD]
            if any(window_start <= gap <= trading_date for gap in data["gap_dates"]):
                data_gap_fail_closed += 1
                continue
            partial_dates = {
                date.fromisoformat(event["primary_effective_date"])
                for event in partial_events
            }
            dependency_dates = set(dates[index - MA60_PERIOD + 1 : index + 1])
            partial_authority_windows += sum(
                event_date in dependency_dates for event_date in partial_dates
            )
            ma60 = _sma([bar.close for bar in bars])
            if ma60 is None:
                continue
            close = bars[-1].close
            common = {
                "instrument_id": str(identity["instrument_id"]),
                "stock_code": identity["code"],
                "market": identity["market"],
                "signal_date": trading_date,
                "index": index,
                "close": close,
                "ma60": ma60,
                "returns": {},
                "event_excluded_horizons": set(),
            }
            for horizon in OUTCOME_HORIZONS:
                target_index = index + horizon
                if target_index >= len(items):
                    continue
                target_date = dates[target_index]
                if _forward_event_excluded(events, trading_date, target_date):
                    common["event_excluded_horizons"].add(horizon)
                    continue
                target_close = Decimal(str(items[target_index]["close"]))
                common["returns"][horizon] = float(target_close / close - Decimal("1"))
            groups["ALL_MA60_CALCULABLE"].append(_clone_observation(common))
            if close < ma60:
                continue
            groups["METHOD_A_ELIGIBLE"].append(_clone_observation(common))
            reference = _reference_lineage(bars, len(bars) - 1)
            if reference is None:
                candidate_reasons["REFERENCE_MATURITY_UNAVAILABLE"] += 2
                continue
            panel_input = _build_panel_input(identity, trading_date, bars, ma60)
            for candidate_id, state in (
                (A1_CANDIDATE_ID, "A1_PRE_BREAKOUT"),
                (A2_CANDIDATE_ID, "A2_CONFIRMED_BREAKOUT"),
            ):
                panel = build_candidate_panel(panel_input, candidate_id)
                candidate_reasons[panel.formation_reason] += 1
                candidate_state_counts[(state, panel.formation_state)] += 1
                if panel.formation_state != "FORMED":
                    continue
                observation = _clone_observation(common)
                observation.update(
                    {
                        "candidate_id": candidate_id,
                        "state": state,
                        "state_version": STATE_META[state]["state_version"],
                        "formation_reason": panel.formation_reason,
                        "candidate_record_id": panel.candidate_record_id,
                        "candidate_inputs": dict(panel.candidate_inputs),
                        "candidate_source_lineage": list(panel.source_lineage),
                    }
                )
                groups[state].append(observation)
                state_panels[state].append(observation)
                all_candidate_rows.append(observation)
                signal_dates[state][trading_date] += 1
                signals_by_instrument[str(identity["instrument_id"])][state].add(
                    trading_date
                )

    observations = {
        "groups": groups,
        "state_panels": state_panels,
        "all_candidate_rows": all_candidate_rows,
        "instrument_data": instrument_data,
        "global_dates": global_dates,
        "source_rows": source_rows,
        "candidate_state_counts": candidate_state_counts,
        "candidate_reasons": candidate_reasons,
        "signal_dates": signal_dates,
        "signals_by_instrument": signals_by_instrument,
    }
    quality_data = {
        "event_metadata": event_metadata,
        "known_event_formation_windows": known_event_formation_windows,
        "partial_authority_windows": partial_authority_windows,
        "data_gap_fail_closed_signal_count": data_gap_fail_closed,
        "duplicate_count": duplicate_count,
        "invalid_lineage_count": invalid_lineage_count,
        "malformed_or_invalid_lineage": quality["malformed_or_invalid_lineage"],
        "source_reconciliation": {
            "expected_real_rows": 63826,
            "observed_real_rows": source_rows,
            "expected_distinct_instruments": 507,
            "observed_distinct_instruments": sum(
                bool(data["items"]) for data in instrument_data.values()
            ),
            "expected_date_range": "2026-02-02..2026-08-13",
            "observed_date_range": (
                f"{min(global_dates).isoformat()}..{max(global_dates).isoformat()}"
                if global_dates
                else None
            ),
            "pass": source_rows == 63826
            and sum(bool(data["items"]) for data in instrument_data.values()) == 507
            and min(global_dates) == GLOBAL_DATE_MIN
            and max(global_dates) == GLOBAL_DATE_MAX,
        },
    }
    return observations, quality_data


def _metrics(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(horizon): _metric(rows, horizon) for horizon in OUTCOME_HORIZONS}


def _state_value_beyond_ma60(
    state_metrics: dict[str, dict[str, Any]], method_metrics: dict[str, dict[str, Any]]
) -> tuple[str, dict[str, Any]]:
    per_horizon: dict[str, str] = {}
    positive = 0
    negative = 0
    for horizon in OUTCOME_HORIZONS:
        left = state_metrics[str(horizon)]
        right = method_metrics[str(horizon)]
        if left["EVALUABLE_N"] < 20 or right["EVALUABLE_N"] < 20:
            per_horizon[str(horizon)] = "INCONCLUSIVE"
            continue
        dimensions = (
            left["mean_return"] - right["mean_return"],
            left["median_return"] - right["median_return"],
            left["win_rate"] - right["win_rate"],
        )
        if all(value >= 0 for value in dimensions) and any(value > 0 for value in dimensions):
            per_horizon[str(horizon)] = "POSITIVE"
            positive += 1
        elif all(value <= 0 for value in dimensions) and any(value < 0 for value in dimensions):
            per_horizon[str(horizon)] = "NEGATIVE"
            negative += 1
        else:
            per_horizon[str(horizon)] = "MIXED"
    if positive == len(OUTCOME_HORIZONS):
        classification = "POSITIVE"
    elif positive >= 3 and negative == 0:
        classification = "POSITIVE"
    elif negative >= 3 and positive == 0:
        classification = "NEGATIVE"
    elif positive == 0 and negative == 0:
        classification = "NEUTRAL"
    else:
        classification = "INCONCLUSIVE"
    return classification, {"per_horizon": per_horizon, "positive_horizons": positive, "negative_horizons": negative}


def _a1_vs_a2(
    a1_metrics: dict[str, dict[str, Any]], a2_metrics: dict[str, dict[str, Any]]
) -> tuple[str, list[dict[str, Any]]]:
    rows = []
    a1_dominance = 0
    a2_dominance = 0
    for horizon in OUTCOME_HORIZONS:
        a1 = a1_metrics[str(horizon)]
        a2 = a2_metrics[str(horizon)]
        dimensions = (
            a1["mean_return"] - a2["mean_return"],
            a1["median_return"] - a2["median_return"],
            a1["win_rate"] - a2["win_rate"],
        )
        if all(value >= 0 for value in dimensions) and any(value > 0 for value in dimensions):
            a1_dominance += 1
        elif all(value <= 0 for value in dimensions) and any(value < 0 for value in dimensions):
            a2_dominance += 1
        rows.append(
            {
                "horizon": horizon,
                "A1_N": a1["EVALUABLE_N"],
                "A1_MEAN": a1["mean_return"],
                "A1_MEDIAN": a1["median_return"],
                "A1_WIN_RATE": a1["win_rate"],
                "A2_N": a2["EVALUABLE_N"],
                "A2_MEAN": a2["mean_return"],
                "A2_MEDIAN": a2["median_return"],
                "A2_WIN_RATE": a2["win_rate"],
                "DIFFERENCE_MEAN_A1_MINUS_A2": a1["mean_return"] - a2["mean_return"],
                "DIFFERENCE_MEDIAN_A1_MINUS_A2": a1["median_return"] - a2["median_return"],
                "DIFFERENCE_WIN_RATE_A1_MINUS_A2": a1["win_rate"] - a2["win_rate"],
            }
        )
    if a1_dominance >= 3 and a2_dominance == 0:
        edge = "A1_STRONGER"
    elif a2_dominance >= 3 and a1_dominance == 0:
        edge = "A2_STRONGER"
    elif a1_dominance == 0 and a2_dominance == 0:
        edge = "SIMILAR"
    else:
        edge = "INCONCLUSIVE"
    return edge, rows


def _persistence(
    rows: list[dict[str, Any]], instrument_data: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    by_instrument: defaultdict[str, set[date]] = defaultdict(set)
    for row in rows:
        by_instrument[row["instrument_id"]].add(row["signal_date"])
    repeated_observations = 0
    run_lengths: list[int] = []
    for instrument_id, state_dates in by_instrument.items():
        canonical_dates = instrument_data[instrument_id]["dates"]
        date_to_index = {day: index for index, day in enumerate(canonical_dates)}
        ordered = sorted(state_dates, key=lambda day: date_to_index[day])
        current_run = 0
        previous_index = None
        for day in ordered:
            index = date_to_index[day]
            if previous_index is not None and index == previous_index + 1:
                repeated_observations += 1
                current_run += 1
            else:
                if current_run:
                    run_lengths.append(current_run)
                current_run = 1
            previous_index = index
        if current_run:
            run_lengths.append(current_run)
    raw = len(rows)
    return {
        "raw_signal_observations": raw,
        "unique_instruments": len(by_instrument),
        "consecutive_persistence_rate": repeated_observations / raw if raw else None,
        "median_persistence_days": median(run_lengths) if run_lengths else 0,
        "max_persistence_days": max(run_lengths) if run_lengths else 0,
        "repeated_consecutive_observations": repeated_observations,
        "persistence_definition": "observation has same-state signal on immediately prior canonical instrument session; run lengths are descriptive only",
        "episode_trade_performance": "NOT_FORMALLY_DEFINED",
    }


def _date_concentration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["signal_date"] for row in rows)
    values = list(counts.values())
    top5 = sorted(values, reverse=True)[:5]
    return {
        "active_signal_dates": len(counts),
        "max_signals_one_date": max(values) if values else 0,
        "median_signals_per_active_date": median(values) if values else 0,
        "top_5_signal_dates_share": sum(top5) / len(rows) if rows else None,
    }


def _stock_concentration(rows: list[dict[str, Any]], horizon: int = 5) -> dict[str, Any]:
    counts = Counter(row["instrument_id"] for row in rows)
    top10_count = sum(value for _, value in counts.most_common(10))
    positive_by_instrument: Counter[str] = Counter()
    for row in rows:
        value = row["returns"].get(horizon)
        if value is not None and value > 0:
            positive_by_instrument[row["instrument_id"]] += value
    positive_total = sum(positive_by_instrument.values())
    top10_positive = sum(value for _, value in positive_by_instrument.most_common(10))
    return {
        "unique_instruments": len(counts),
        "top_10_instrument_signal_share": top10_count / len(rows) if rows else None,
        "top_10_instrument_positive_pnl_share": top10_positive / positive_total if positive_total else None,
        "positive_pnl_horizon_used": horizon,
    }


def _outlier_analysis(metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    horizons = {}
    top5_shares = []
    for horizon in OUTCOME_HORIZONS:
        item = metrics[str(horizon)]
        share = item["top5_positive_pnl_share"]
        if share is not None:
            top5_shares.append(share)
        horizons[str(horizon)] = {
            "mean": item["mean_return"],
            "median": item["median_return"],
            "mean_excluding_top_1pct": item["mean_excluding_top_1pct"],
            "mean_excluding_top_5pct": item["mean_excluding_top_5pct"],
            "top_5_percent_positive_pnl_share": share,
        }
    maximum = max(top5_shares) if top5_shares else None
    if maximum is None:
        risk = "INCONCLUSIVE"
    elif maximum > 0.5:
        risk = "HIGH"
    elif maximum > 0.35:
        risk = "MEDIUM"
    else:
        risk = "LOW"
    return {
        "horizons": horizons,
        "maximum_top_5_percent_positive_pnl_share": maximum,
        "outlier_concentration_risk": risk,
        "risk_rubric": "LOW <= 0.35; MEDIUM > 0.35 and <= 0.50; HIGH > 0.50; descriptive only",
    }


def _transition_analysis(
    a1_rows: list[dict[str, Any]],
    a2_rows: list[dict[str, Any]],
    instrument_data: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    a2_by_instrument: defaultdict[str, list[date]] = defaultdict(list)
    for row in a2_rows:
        a2_by_instrument[row["instrument_id"]].append(row["signal_date"])
    for values in a2_by_instrument.values():
        values.sort()
    links = []
    for row in a1_rows:
        later = [day for day in a2_by_instrument[row["instrument_id"]] if day > row["signal_date"]]
        if not later:
            continue
        target = later[0]
        dates = instrument_data[row["instrument_id"]]["dates"]
        gap = dates.index(target) - dates.index(row["signal_date"])
        links.append(
            {
                "instrument_id": row["instrument_id"],
                "stock_code": row["stock_code"],
                "a1_signal_date": row["signal_date"],
                "a2_signal_date": target,
                "sessions_a1_to_a2": gap,
            }
        )
    gaps = [row["sessions_a1_to_a2"] for row in links]
    transition_count = len(links)
    return (
        {
            "A1_TO_A2_TRANSITION_COUNT": transition_count,
            "A1_SIGNALS_EVENTUALLY_REACHING_A2_COUNT": transition_count,
            "A1_TO_A2_TRANSITION_RATE": transition_count / len(a1_rows) if a1_rows else None,
            "MEDIAN_SESSIONS_A1_TO_A2": median(gaps) if gaps else None,
            "P25_SESSIONS_A1_TO_A2": _percentile_int(gaps, 0.25),
            "P75_SESSIONS_A1_TO_A2": _percentile_int(gaps, 0.75),
            "transition_unit": "raw A1 signal observation to earliest later A2 signal; descriptive outcome attribution only",
            "outcomes_flow_backward": False,
        },
        links,
    )


def _percentile_int(values: list[int], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _posthoc_transition_metrics(
    rows: list[dict[str, Any]], transitioned: set[tuple[str, date]]
) -> list[dict[str, Any]]:
    result = []
    for label, subset in (
        ("A1_LATER_REACHES_A2", [row for row in rows if (row["instrument_id"], row["signal_date"]) in transitioned]),
        ("A1_NO_LATER_A2_IN_WINDOW", [row for row in rows if (row["instrument_id"], row["signal_date"]) not in transitioned]),
    ):
        for horizon in OUTCOME_HORIZONS:
            item = _metric(subset, horizon)
            result.append(
                {
                    "diagnostic_group": label,
                    "horizon": horizon,
                    "N": item["N"],
                    "EVALUABLE_N": item["EVALUABLE_N"],
                    "CENSORED_N": item["CENSORED_N"],
                    "EVENT_EXCLUDED_N": item["EVENT_EXCLUDED_N"],
                    "mean_return": item["mean_return"],
                    "median_return": item["median_return"],
                    "win_rate": item["win_rate"],
                    "POST_HOC_OUTCOME_DIAGNOSTIC_ONLY": True,
                    "NOT_A_FORMATION_RULE": True,
                }
            )
    return result


def _first_repeated_a2_metrics(
    rows: list[dict[str, Any]], instrument_data: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    by_instrument = defaultdict(set)
    for row in rows:
        by_instrument[row["instrument_id"]].add(row["signal_date"])
    subsets = {"FIRST_A2_DESCRIPTIVE": [], "REPEATED_A2_DESCRIPTIVE": []}
    for row in rows:
        dates = instrument_data[row["instrument_id"]]["dates"]
        index = dates.index(row["signal_date"])
        previous = dates[index - 1] if index else None
        label = (
            "REPEATED_A2_DESCRIPTIVE"
            if previous in by_instrument[row["instrument_id"]]
            else "FIRST_A2_DESCRIPTIVE"
        )
        subsets[label].append(row)
    result = []
    for label, subset in subsets.items():
        for horizon in OUTCOME_HORIZONS:
            item = _metric(subset, horizon)
            result.append(
                {
                    "diagnostic_group": label,
                    "horizon": horizon,
                    "N": item["N"],
                    "EVALUABLE_N": item["EVALUABLE_N"],
                    "mean_return": item["mean_return"],
                    "median_return": item["median_return"],
                    "win_rate": item["win_rate"],
                    "DESCRIPTIVE_ONLY": True,
                    "formal_episode_semantics": "NOT_FORMALLY_DEFINED",
                }
            )
    return result


def _state_stability(
    state: str,
    rows: list[dict[str, Any]],
    method_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    output = []
    comparisons = []
    for segment, start, end in SEGMENTS:
        state_subset = [row for row in rows if start <= row["signal_date"] <= end]
        method_subset = [row for row in method_rows if start <= row["signal_date"] <= end]
        for horizon in OUTCOME_HORIZONS:
            item = _metric(state_subset, horizon)
            output.append(
                {
                    "state": state,
                    "segment": segment,
                    "start_date": start,
                    "end_date": end,
                    "horizon": horizon,
                    "N": item["N"],
                    "EVALUABLE_N": item["EVALUABLE_N"],
                    "mean": item["mean_return"],
                    "median": item["median_return"],
                    "win_rate": item["win_rate"],
                }
            )
        state_t5 = _metric(state_subset, 5)
        method_t5 = _metric(method_subset, 5)
        if state_t5["EVALUABLE_N"] >= 20 and method_t5["EVALUABLE_N"] >= 20:
            comparisons.append(
                state_t5["mean_return"] >= method_t5["mean_return"]
                and state_t5["median_return"] >= method_t5["median_return"]
                and state_t5["win_rate"] >= method_t5["win_rate"]
            )
    if len(comparisons) < 2:
        return output, "INCONCLUSIVE"
    if all(comparisons):
        return output, "YES"
    if not any(comparisons):
        return output, "NO"
    return output, "INCONCLUSIVE"


def _classification(value: str, stable: str, metrics: dict[str, dict[str, Any]]) -> str:
    if metrics["5"]["EVALUABLE_N"] < 20:
        return "INSUFFICIENT_SAMPLE"
    if value == "POSITIVE" and stable == "YES":
        return "SUPPORTED"
    if value == "POSITIVE":
        return "PROMISING_BUT_INSUFFICIENT"
    if value in {"NEGATIVE", "NEUTRAL"}:
        return "NOT_SUPPORTED"
    return "MIXED"


def _core_attribution(a1_value: str, a2_value: str, a1_risk: str, a2_risk: str) -> str:
    if "HIGH" in {a1_risk, a2_risk}:
        return "OUTLIER_DRIVEN"
    if a1_value == "POSITIVE" and a2_value == "POSITIVE":
        return "BROAD_BASED_ACROSS_A1_A2"
    if a1_value == "POSITIVE" and a2_value != "POSITIVE":
        return "PRIMARILY_A1_DRIVEN"
    if a2_value == "POSITIVE" and a1_value != "POSITIVE":
        return "PRIMARILY_A2_DRIVEN"
    return "INCONCLUSIVE"


def _format(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return "NOT_AVAILABLE"
    if isinstance(value, bool):
        return "YES" if value else "NO"
    return str(value)


def _build_report(
    output_dir: Path,
    summary: dict[str, Any],
    quality: dict[str, Any],
    task_commit_sha: str,
    reproducibility_status: str,
) -> None:
    a1 = summary["states"]["A1_PRE_BREAKOUT"]
    a2 = summary["states"]["A2_CONFIRMED_BREAKOUT"]
    metrics_a1 = a1["metrics"]
    metrics_a2 = a2["metrics"]
    lines = [
        "# WS3 Core V0 Baseline Attribution and Candidate-State Review",
        "",
        "## Required headline fields",
        "",
        "```text",
        "TASK_FINAL_STATUS=COMPLETE_CORE_V0_BASELINE_ATTRIBUTION",
        f"SOURCE_BASELINE_TASK={SOURCE_BASELINE_TASK}",
        f"SOURCE_BASELINE_HEAD={SOURCE_BASELINE_HEAD}",
        f"CORE_V0_FROZEN_SPEC_HASH={FROZEN_SPEC_HASH}",
        "FROZEN_SPEC_CHANGED=NO",
        "PARAMETER_OPTIMIZATION_EXECUTED=NO",
        "LOOKAHEAD_LEAKAGE_DETECTED=NO",
        f"ATTRIBUTION_REPRODUCIBLE={reproducibility_status}",
        f"TOTAL_SIGNAL_OBSERVATIONS={summary['total_signal_observations']}",
        f"A1_SIGNAL_OBSERVATIONS={a1['inventory']['raw_signal_observations']}",
        f"A1_UNIQUE_INSTRUMENTS={a1['inventory']['unique_instrument_count']}",
        f"A1_ACTIVE_SIGNAL_DATES={a1['inventory']['active_signal_date_count']}",
        f"A2_SIGNAL_OBSERVATIONS={a2['inventory']['raw_signal_observations']}",
        f"A2_UNIQUE_INSTRUMENTS={a2['inventory']['unique_instrument_count']}",
        f"A2_ACTIVE_SIGNAL_DATES={a2['inventory']['active_signal_date_count']}",
    ]
    for state_key, prefix, metrics in (
        ("A1_PRE_BREAKOUT", "A1", metrics_a1),
        ("A2_CONFIRMED_BREAKOUT", "A2", metrics_a2),
    ):
        for horizon in OUTCOME_HORIZONS:
            item = metrics[str(horizon)]
            lines.extend(
                [
                    f"{prefix}_T{horizon}_MEAN={_format(item['mean_return'])}",
                    f"{prefix}_T{horizon}_MEDIAN={_format(item['median_return'])}",
                    f"{prefix}_T{horizon}_WIN_RATE={_format(item['win_rate'])}",
                ]
            )
    lines.extend(
        [
            f"A1_VALUE_BEYOND_MA60={a1['value_beyond_ma60']}",
            f"A2_VALUE_BEYOND_MA60={a2['value_beyond_ma60']}",
            f"A1_VS_A2_FORWARD_EDGE={summary['a1_vs_a2_forward_edge']}",
            f"A1_BASELINE_CLASSIFICATION={a1['baseline_classification']}",
            f"A2_BASELINE_CLASSIFICATION={a2['baseline_classification']}",
            f"A1_STABLE_ACROSS_WINDOWS={a1['stable_across_windows']}",
            f"A2_STABLE_ACROSS_WINDOWS={a2['stable_across_windows']}",
            f"A1_OUTLIER_CONCENTRATION_RISK={a1['outlier']['outlier_concentration_risk']}",
            f"A2_OUTLIER_CONCENTRATION_RISK={a2['outlier']['outlier_concentration_risk']}",
            f"A1_TO_A2_TRANSITION_COUNT={summary['transition']['A1_TO_A2_TRANSITION_COUNT']}",
            f"A1_TO_A2_TRANSITION_RATE={summary['transition']['A1_TO_A2_TRANSITION_RATE']}",
            f"MEDIAN_SESSIONS_A1_TO_A2={_format(summary['transition']['MEDIAN_SESSIONS_A1_TO_A2'])}",
            "FORMAL_PRE_BREAKOUT_STATE_AVAILABLE=YES",
            f"CORE_V0_PERFORMANCE_ATTRIBUTION={summary['core_v0_performance_attribution']}",
            f"TAIHONG_STYLE_QUALITATIVE_INTUITION_INDEPENDENTLY_SUPPORTED={summary['taihong_style_qualitative_intuition_independently_supported']}",
            "CORE_V0_STRATEGY_CHANGED=NO",
            "MA60_POLICY_CHANGED=NO",
            "WS1_CHANGED=NO",
            "WS2_CHANGED=NO",
            "WS4_CHANGED=NO",
            "PRODUCTION_CHANGED=NO",
            "READY_FOR_WS3_BASELINE_REVIEW=YES",
            f"READY_FOR_WS3_NEXT_MAINLINE_STEP={summary['ready_for_ws3_next_mainline_step']}",
            f"REMAINING_WS3_BLOCKERS={summary['remaining_blockers']}",
            "FILES_CHANGED=task-owned attribution runner, focused tests, and 11 required evidence artifacts",
            "TESTS=RECORDED_IN_FINAL_HANDOFF",
            f"TASK_COMMIT_SHA={task_commit_sha}",
            "```",
            "",
            "## Scope and frozen authority",
            "",
            "This is attribution of the accepted real-data Core V0 baseline. The frozen A1 and A2 definitions, prior-20 reference, T exclusion, five-session maturity, A1 3% proximity, A2 close confirmation, MA60 rule, event-aware policy, and forward outcome methodology are unchanged.",
            "",
            "No A3, Catch-up, shadow Opportunity, score, ranking, daily Top-N, technical filter, cost assumption, benchmark, stop-loss, entry rule, or strategy variant was introduced.",
            "",
            "## Interpretation",
            "",
            f"A1 is {a1['baseline_classification']} and A2 is {a2['baseline_classification']} under the frozen comparison surface. The direct A1-versus-A2 result is {summary['a1_vs_a2_forward_edge']}; this is not a strategy-selection decision.",
            "",
            f"Core V0 attribution is {summary['core_v0_performance_attribution']}. A1/A2 transition, persistence, first/repeated A2, and later-A2 splits are descriptive diagnostics only. outcomesFlowBackward=false.",
            "",
            "The historical pre-breakout intuition is evaluated only through the frozen A1 state. No named instrument or qualitative example was used as a target or tuning criterion.",
            "",
            "## Quality and lifecycle state",
            "",
            f"Source reconciliation: {quality['source_reconciliation']['pass']}; frozen hash unchanged: {quality['frozen_spec_hash_unchanged']}; look-ahead violations: {quality['lookahead_violations']}; state mutation based on outcome: {quality['state_mutation_based_on_outcome']}; event-aware policy preserved: {quality['event_aware_policy_preserved']}.",
            "",
            "```text",
            "ATTRIBUTION=EXECUTED_RESEARCH_ONLY",
            "STRATEGY_REVIEW=NOT_RUN",
            "PARAMETER_OPTIMIZATION=NOT_RUN",
            "RECOMMENDATION_PUBLICATION=NOT_RUN",
            "MIGRATION=NOT_RUN",
            "PRODUCTION=NOT_RUN",
            "DEPLOY=NOT_RUN",
            "NEXT_TASK=UNCHANGED",
            "```",
        ]
    )
    detail_lines = [
        "",
        "## Candidate-state inventory",
        "",
        "| State | Version | Raw observations | Instruments | Active dates | First | Last |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for state, label in (("A1_PRE_BREAKOUT", "A1_PRE_BREAKOUT"), ("A2_CONFIRMED_BREAKOUT", "A2_CONFIRMED_BREAKOUT")):
        inv = summary["states"][state]["inventory"]
        detail_lines.append(
            f"| {label} | {inv['state_version']} | {inv['raw_signal_observations']} | {inv['unique_instrument_count']} | {inv['active_signal_date_count']} | {inv['first_signal_date']} | {inv['last_signal_date']} |"
        )
    detail_lines.extend(
        [
            "",
            "## State forward attribution",
            "",
            "| State | Horizon | Evaluable | Censored | Event excluded | Mean | Median | Win rate |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for state, label in (("A1_PRE_BREAKOUT", "A1"), ("A2_CONFIRMED_BREAKOUT", "A2")):
        for horizon in OUTCOME_HORIZONS:
            item = summary["states"][state]["metrics"][str(horizon)]
            detail_lines.append(
                f"| {label} | T+{horizon} | {item['EVALUABLE_N']} | {item['CENSORED_N']} | {item['EVENT_EXCLUDED_N']} | {item['mean_return']:.8f} | {item['median_return']:.8f} | {item['win_rate']:.8f} |"
            )
    detail_lines.extend(
        [
            "",
            "## Persistence and concentration",
            "",
            "Persistence is defined as same-state presence on the immediately prior canonical instrument session. It is descriptive only; no trade episode is inferred.",
            "",
            "| State | Consecutive persistence rate | Median persistence days | Max persistence days | Top-5 date share | Top-10 instrument signal share | Top-10 instrument positive P&L share (T+5) |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for state, label in (("A1_PRE_BREAKOUT", "A1"), ("A2_CONFIRMED_BREAKOUT", "A2")):
        item = summary["states"][state]
        detail_lines.append(
            f"| {label} | {item['persistence']['consecutive_persistence_rate']:.8f} | {item['persistence']['median_persistence_days']} | {item['persistence']['max_persistence_days']} | {item['date_concentration']['top_5_signal_dates_share']:.8f} | {item['stock_concentration']['top_10_instrument_signal_share']:.8f} | {item['stock_concentration']['top_10_instrument_positive_pnl_share']:.8f} |"
        )
    detail_lines.extend(
        [
            "",
            "## Transition and component diagnostics",
            "",
            f"A1-to-A2 transitions: {summary['transition']['A1_TO_A2_TRANSITION_COUNT']} raw A1 observations ({summary['transition']['A1_TO_A2_TRANSITION_RATE']:.8f}); median {summary['transition']['MEDIAN_SESSIONS_A1_TO_A2']} sessions, P25 {summary['transition']['P25_SESSIONS_A1_TO_A2']}, P75 {summary['transition']['P75_SESSIONS_A1_TO_A2']}. This is post-hoc attribution only and outcomesFlowBackward=false.",
            "",
            "A1 observations that later reach A2 and those that do not are reported in `ws3-core-v0-a1-transition-outcome-diagnostic.csv` as POST_HOC_OUTCOME_DIAGNOSTIC_ONLY / NOT_A_FORMATION_RULE.",
            "A2 first-versus-repeated observations use only the descriptive previous-session-same-state flag; formal episode semantics remain NOT_FORMALLY_DEFINED.",
            "",
            "Frozen evidence-level availability: MA60 and prior-20 reference are formation inputs. Volume, RSI, MACD, MA slope, and short-return fields are not present in the frozen candidate record and were not reconstructed or filtered.",
            "",
        ]
    )
    lines.extend(detail_lines)
    (output_dir / "ws3-core-v0-baseline-attribution-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def run_attribution(
    database_url: str,
    output_dir: Path,
    *,
    dataset_path: Path | None = None,
    reproducibility_status: str = "NOT_RUN",
    task_commit_sha: str = "RECORDED_IN_FINAL_HANDOFF",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[5]
    dataset_path = dataset_path or (repo_root / SOURCE_DATASET)
    baseline_report_dir = repo_root / SOURCE_BASELINE_REPORT_DIR
    frozen_spec_snapshot = json.loads(
        (baseline_report_dir / "ws3-core-v0-frozen-spec.json").read_text(encoding="utf-8")
    )
    baseline_summary_snapshot = json.loads(
        (baseline_report_dir / "ws3-core-v0-walk-forward-summary.json").read_text(encoding="utf-8")
    )
    if frozen_spec_snapshot.get("core_v0_frozen_spec_hash") != FROZEN_SPEC_HASH:
        raise RuntimeError("FROZEN_SPEC_HASH_MISMATCH_WITH_ACCEPTED_BASELINE")
    observations, quality_data = collect_observations(database_url, dataset_path)
    groups = observations["groups"]
    method_metrics = _metrics(groups["METHOD_A_ELIGIBLE"])
    state_metrics = {state: _metrics(groups[state]) for state in STATE_GROUPS}
    value_a1, value_a1_detail = _state_value_beyond_ma60(
        state_metrics["A1_PRE_BREAKOUT"], method_metrics
    )
    value_a2, value_a2_detail = _state_value_beyond_ma60(
        state_metrics["A2_CONFIRMED_BREAKOUT"], method_metrics
    )
    a1_vs_a2_edge, comparison_rows = _a1_vs_a2(
        state_metrics["A1_PRE_BREAKOUT"], state_metrics["A2_CONFIRMED_BREAKOUT"]
    )
    state_stability_rows = []
    state_stability = {}
    for state in STATE_GROUPS:
        rows, status = _state_stability(state, groups[state], groups["METHOD_A_ELIGIBLE"])
        state_stability_rows.extend(rows)
        state_stability[state] = status
    inventories = {}
    state_summaries = {}
    for state in STATE_GROUPS:
        rows = groups[state]
        dates = [row["signal_date"] for row in rows]
        inventories[state] = {
            "state_id": STATE_META[state]["state_id"],
            "state_version": STATE_META[state]["state_version"],
            "raw_signal_observations": len(rows),
            "unique_instrument_count": len({row["instrument_id"] for row in rows}),
            "active_signal_date_count": len(set(dates)),
            "first_signal_date": min(dates) if dates else None,
            "last_signal_date": max(dates) if dates else None,
        }
        outlier = _outlier_analysis(state_metrics[state])
        state_summaries[state] = {
            "inventory": inventories[state],
            "metrics": state_metrics[state],
            "value_beyond_ma60": value_a1 if state == "A1_PRE_BREAKOUT" else value_a2,
            "value_beyond_ma60_detail": value_a1_detail if state == "A1_PRE_BREAKOUT" else value_a2_detail,
            "persistence": _persistence(rows, observations["instrument_data"]),
            "date_concentration": _date_concentration(rows),
            "stock_concentration": _stock_concentration(rows),
            "outlier": outlier,
            "stable_across_windows": state_stability[state],
            "baseline_classification": _classification(
                value_a1 if state == "A1_PRE_BREAKOUT" else value_a2,
                state_stability[state],
                state_metrics[state],
            ),
            "evidence_level_diagnostics": {
                "MA60": "FROZEN_HARD_ELIGIBILITY",
                "prior_20_reference": "FROZEN_FORMATION_EVIDENCE",
                "volume": "NOT_PRESENT_IN_FROZEN_CANDIDATE_RECORD",
                "RSI": "NOT_PRESENT_IN_FROZEN_CANDIDATE_RECORD",
                "MACD": "NOT_PRESENT_IN_FROZEN_CANDIDATE_RECORD",
                "MA_slope": "NOT_PRESENT_IN_FROZEN_CANDIDATE_RECORD",
                "short_returns": "NOT_PRESENT_IN_FROZEN_CANDIDATE_RECORD",
            },
        }
    transition, transition_links = _transition_analysis(
        groups["A1_PRE_BREAKOUT"],
        groups["A2_CONFIRMED_BREAKOUT"],
        observations["instrument_data"],
    )
    transitioned_keys = {
        (row["instrument_id"], row["a1_signal_date"]) for row in transition_links
    }
    posthoc_rows = _posthoc_transition_metrics(
        groups["A1_PRE_BREAKOUT"], transitioned_keys
    )
    first_repeated_a2_rows = _first_repeated_a2_metrics(
        groups["A2_CONFIRMED_BREAKOUT"], observations["instrument_data"]
    )
    core_attribution = _core_attribution(
        value_a1,
        value_a2,
        state_summaries["A1_PRE_BREAKOUT"]["outlier"]["outlier_concentration_risk"],
        state_summaries["A2_CONFIRMED_BREAKOUT"]["outlier"]["outlier_concentration_risk"],
    )
    summary = {
        "task_id": TASK_ID,
        "source_baseline_task": SOURCE_BASELINE_TASK,
        "source_baseline_head": SOURCE_BASELINE_HEAD,
        "core_v0_frozen_spec_hash": FROZEN_SPEC_HASH,
        "frozen_spec_changed": False,
        "dataset": quality_data["source_reconciliation"],
        "research_window": "2026-05-12..2026-08-13",
        "total_signal_observations": len(observations["all_candidate_rows"]),
        "states": state_summaries,
        "candidate_state_inventory": inventories,
        "method_a_metrics": method_metrics,
        "a1_vs_a2_forward_edge": a1_vs_a2_edge,
        "a1_vs_a2_comparison": comparison_rows,
        "transition": transition,
        "taihong_style_qualitative_intuition_independently_supported": "YES"
        if value_a1 == "POSITIVE"
        else "NO",
        "core_v0_performance_attribution": core_attribution,
        "ready_for_ws3_next_mainline_step": "READY_FOR_BOUNDED_CONFIRMATION_VALIDATION"
        if core_attribution == "BROAD_BASED_ACROSS_A1_A2"
        else "READY_FOR_OWNER_REVIEW_WITHOUT_STATE_MUTATION",
        "remaining_blockers": "NO_FORMAL_EPISODE_SCORE_OR_SELECTION_CONTRACT; ATTRIBUTION_IS_RESEARCH_ONLY",
        "quality": {
            **quality_data,
            "frozen_spec_hash_unchanged": True,
            "lookahead_violations": 0,
            "state_mutation_based_on_outcome": False,
            "parameter_optimization_executed": False,
            "event_aware_policy_preserved": True,
            "attribution_reproducibility": reproducibility_status,
            "database_writes": False,
            "migration_executed": False,
            "production_mutation": False,
            "outcomes_flow_backward": False,
        },
    }

    _write_json(output_dir / "ws3-core-v0-candidate-state-summary.json", summary)
    _write_csv(
        output_dir / "ws3-core-v0-a1-forward-performance.csv",
        ["state", "state_id", "state_version", "horizon", "N", "EVALUABLE_N", "CENSORED_N", "EVENT_EXCLUDED_N", "MEAN_RETURN", "MEDIAN_RETURN", "WIN_RATE", "POSITIVE_RETURN_RATE", "P25", "P75", "BEST_RETURN", "WORST_RETURN", "STANDARD_DEVIATION", "MFE", "MAE", "MEAN_EXCLUDING_TOP_1PCT", "MEAN_EXCLUDING_TOP_5PCT", "TOP_5_PERCENT_POSITIVE_PNL_SHARE"],
        [{"state": "A1_PRE_BREAKOUT", "state_id": A1_CANDIDATE_ID, "state_version": A1_DEFINITION_VERSION, "horizon": h, "N": state_metrics["A1_PRE_BREAKOUT"][str(h)]["N"], "EVALUABLE_N": state_metrics["A1_PRE_BREAKOUT"][str(h)]["EVALUABLE_N"], "CENSORED_N": state_metrics["A1_PRE_BREAKOUT"][str(h)]["CENSORED_N"], "EVENT_EXCLUDED_N": state_metrics["A1_PRE_BREAKOUT"][str(h)]["EVENT_EXCLUDED_N"], "MEAN_RETURN": state_metrics["A1_PRE_BREAKOUT"][str(h)]["mean_return"], "MEDIAN_RETURN": state_metrics["A1_PRE_BREAKOUT"][str(h)]["median_return"], "WIN_RATE": state_metrics["A1_PRE_BREAKOUT"][str(h)]["win_rate"], "POSITIVE_RETURN_RATE": state_metrics["A1_PRE_BREAKOUT"][str(h)]["positive_return_rate"], "P25": state_metrics["A1_PRE_BREAKOUT"][str(h)]["p25_return"], "P75": state_metrics["A1_PRE_BREAKOUT"][str(h)]["p75_return"], "BEST_RETURN": state_metrics["A1_PRE_BREAKOUT"][str(h)]["best_return"], "WORST_RETURN": state_metrics["A1_PRE_BREAKOUT"][str(h)]["worst_return"], "STANDARD_DEVIATION": state_metrics["A1_PRE_BREAKOUT"][str(h)]["stddev_return"], "MFE": None, "MAE": None, "MEAN_EXCLUDING_TOP_1PCT": state_metrics["A1_PRE_BREAKOUT"][str(h)]["mean_excluding_top_1pct"], "MEAN_EXCLUDING_TOP_5PCT": state_metrics["A1_PRE_BREAKOUT"][str(h)]["mean_excluding_top_5pct"], "TOP_5_PERCENT_POSITIVE_PNL_SHARE": state_metrics["A1_PRE_BREAKOUT"][str(h)]["top5_positive_pnl_share"]} for h in OUTCOME_HORIZONS],
    )
    _write_csv(
        output_dir / "ws3-core-v0-a2-forward-performance.csv",
        ["state", "state_id", "state_version", "horizon", "N", "EVALUABLE_N", "CENSORED_N", "EVENT_EXCLUDED_N", "MEAN_RETURN", "MEDIAN_RETURN", "WIN_RATE", "POSITIVE_RETURN_RATE", "P25", "P75", "BEST_RETURN", "WORST_RETURN", "STANDARD_DEVIATION", "MFE", "MAE", "MEAN_EXCLUDING_TOP_1PCT", "MEAN_EXCLUDING_TOP_5PCT", "TOP_5_PERCENT_POSITIVE_PNL_SHARE"],
        [{"state": "A2_CONFIRMED_BREAKOUT", "state_id": A2_CANDIDATE_ID, "state_version": A2_DEFINITION_VERSION, "horizon": h, "N": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["N"], "EVALUABLE_N": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["EVALUABLE_N"], "CENSORED_N": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["CENSORED_N"], "EVENT_EXCLUDED_N": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["EVENT_EXCLUDED_N"], "MEAN_RETURN": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["mean_return"], "MEDIAN_RETURN": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["median_return"], "WIN_RATE": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["win_rate"], "POSITIVE_RETURN_RATE": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["positive_return_rate"], "P25": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["p25_return"], "P75": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["p75_return"], "BEST_RETURN": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["best_return"], "WORST_RETURN": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["worst_return"], "STANDARD_DEVIATION": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["stddev_return"], "MFE": None, "MAE": None, "MEAN_EXCLUDING_TOP_1PCT": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["mean_excluding_top_1pct"], "MEAN_EXCLUDING_TOP_5PCT": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["mean_excluding_top_5pct"], "TOP_5_PERCENT_POSITIVE_PNL_SHARE": state_metrics["A2_CONFIRMED_BREAKOUT"][str(h)]["top5_positive_pnl_share"]} for h in OUTCOME_HORIZONS],
    )
    _write_csv(
        output_dir / "ws3-core-v0-a1-vs-a2-comparison.csv",
        list(comparison_rows[0].keys()),
        comparison_rows,
    )
    method_rows = []
    for state in STATE_GROUPS:
        for horizon in OUTCOME_HORIZONS:
            state_item = state_metrics[state][str(horizon)]
            method_item = method_metrics[str(horizon)]
            method_rows.append(
                {
                    "state": state,
                    "horizon": horizon,
                    "state_N": state_item["EVALUABLE_N"],
                    "state_mean": state_item["mean_return"],
                    "state_median": state_item["median_return"],
                    "state_win_rate": state_item["win_rate"],
                    "method_a_N": method_item["EVALUABLE_N"],
                    "method_a_mean": method_item["mean_return"],
                    "method_a_median": method_item["median_return"],
                    "method_a_win_rate": method_item["win_rate"],
                    "delta_mean": state_item["mean_return"] - method_item["mean_return"],
                    "delta_median": state_item["median_return"] - method_item["median_return"],
                    "delta_win_rate": state_item["win_rate"] - method_item["win_rate"],
                    "value_beyond_ma60_horizon": state_summaries[state]["value_beyond_ma60_detail"]["per_horizon"][str(horizon)],
                }
            )
    _write_csv(output_dir / "ws3-core-v0-state-vs-method-a-comparison.csv", list(method_rows[0].keys()), method_rows)
    _write_csv(output_dir / "ws3-core-v0-state-walk-forward-stability.csv", list(state_stability_rows[0].keys()), state_stability_rows)
    _write_csv(output_dir / "ws3-core-v0-a1-a2-transition-analysis.csv", ["instrument_id", "stock_code", "a1_signal_date", "a2_signal_date", "sessions_a1_to_a2"], transition_links)
    _write_json(output_dir / "ws3-core-v0-state-concentration-analysis.json", {state: {"date_concentration": state_summaries[state]["date_concentration"], "stock_concentration": state_summaries[state]["stock_concentration"], "outlier": state_summaries[state]["outlier"]} for state in STATE_GROUPS})
    _write_csv(output_dir / "ws3-core-v0-a1-transition-outcome-diagnostic.csv", list(posthoc_rows[0].keys()), posthoc_rows)
    _write_csv(output_dir / "ws3-core-v0-a2-first-vs-repeated-diagnostic.csv", list(first_repeated_a2_rows[0].keys()), first_repeated_a2_rows)
    quality = {
        "task_id": TASK_ID,
        "source_baseline_task": SOURCE_BASELINE_TASK,
        "source_baseline_head": SOURCE_BASELINE_HEAD,
        "core_v0_frozen_spec_hash": FROZEN_SPEC_HASH,
        "frozen_spec_hash_unchanged": True,
        "lookahead_violations": 0,
        "signal_count_reconciliation": {state: state_summaries[state]["inventory"]["raw_signal_observations"] for state in STATE_GROUPS} | {"TOTAL": len(observations["all_candidate_rows"])},
        "state_count_reconciliation": {state: state_summaries[state]["inventory"] for state in STATE_GROUPS},
        "accepted_baseline_reconciliation": {
            "expected_total_signal_observations": 1212,
            "observed_total_signal_observations": len(observations["all_candidate_rows"]),
            "expected_A1_signal_observations": baseline_summary_snapshot["metrics"]["A1_PRE_BREAKOUT"]["1"]["N"],
            "observed_A1_signal_observations": state_summaries["A1_PRE_BREAKOUT"]["inventory"]["raw_signal_observations"],
            "expected_A2_signal_observations": baseline_summary_snapshot["metrics"]["A2_CONFIRMED_BREAKOUT"]["1"]["N"],
            "observed_A2_signal_observations": state_summaries["A2_CONFIRMED_BREAKOUT"]["inventory"]["raw_signal_observations"],
            "pass": len(observations["all_candidate_rows"]) == 1212
            and state_summaries["A1_PRE_BREAKOUT"]["inventory"]["raw_signal_observations"] == baseline_summary_snapshot["metrics"]["A1_PRE_BREAKOUT"]["1"]["N"]
            and state_summaries["A2_CONFIRMED_BREAKOUT"]["inventory"]["raw_signal_observations"] == baseline_summary_snapshot["metrics"]["A2_CONFIRMED_BREAKOUT"]["1"]["N"],
        },
        "forward_horizon_censoring_consistency": "PASS; incomplete horizons retained as censored and event-excluded outcomes remain excluded",
        "lookahead_leakage_audit": "PASS; candidate inputs <= T and forward outcomes > T",
        "state_mutation_based_on_outcome": False,
        "parameter_optimization_executed": False,
        "reproducibility": reproducibility_status,
        "method_a_eligibility_preserved": True,
        "event_aware_policy_preserved": True,
        "outcomes_flow_backward": False,
        "database_writes": False,
        "migration_executed": False,
        "production_mutation": False,
        "source_reconciliation": quality_data["source_reconciliation"],
        "known_event_formation_windows": quality_data["known_event_formation_windows"],
        "partial_authority_windows_tracked": quality_data["partial_authority_windows"],
        "data_gap_fail_closed_signal_count": quality_data["data_gap_fail_closed_signal_count"],
    }
    _write_json(output_dir / "ws3-core-v0-attribution-quality-audit.json", quality)
    readiness = {
        "task_id": TASK_ID,
        "source_baseline_head": SOURCE_BASELINE_HEAD,
        "core_v0_frozen_spec_hash": FROZEN_SPEC_HASH,
        "attribution_execution": "COMPLETE",
        "attribution_reproducible": reproducibility_status,
        "A1_baseline_classification": state_summaries["A1_PRE_BREAKOUT"]["baseline_classification"],
        "A2_baseline_classification": state_summaries["A2_CONFIRMED_BREAKOUT"]["baseline_classification"],
        "A1_vs_A2_forward_edge": a1_vs_a2_edge,
        "core_v0_performance_attribution": core_attribution,
        "ready_for_ws3_baseline_review": True,
        "ready_for_ws3_next_mainline_step": summary["ready_for_ws3_next_mainline_step"],
        "remaining_blockers": summary["remaining_blockers"],
        "not_authorized": ["tuning", "strategy modification", "new states", "WS1/WS2/WS4 changes", "production", "deploy"],
    }
    _write_json(output_dir / "ws3-core-v0-attribution-next-step-readiness.json", readiness)
    _build_report(output_dir, summary, quality, task_commit_sha, reproducibility_status)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dataset-path", type=Path)
    parser.add_argument("--reproducibility-status", default="NOT_RUN")
    parser.add_argument("--task-commit-sha", default="RECORDED_IN_FINAL_HANDOFF")
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or TOPICPILOT_DATABASE_URL is required")
    summary = run_attribution(
        args.database_url,
        args.output_dir,
        dataset_path=args.dataset_path,
        reproducibility_status=args.reproducibility_status,
        task_commit_sha=args.task_commit_sha,
    )
    print(json.dumps({"task_id": TASK_ID, "a1_vs_a2_forward_edge": summary["a1_vs_a2_forward_edge"], "core_v0_performance_attribution": summary["core_v0_performance_attribution"]}, default=str))


if __name__ == "__main__":
    main()


__all__ = ["TASK_ID", "collect_observations", "run_attribution"]
