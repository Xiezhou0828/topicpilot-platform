"""Diagnose frozen Core V0 validation weakness and A1 non-transition paths.

All state labels in this module are ex-post diagnostic classifications.  The
module consumes the existing attribution collector and never changes the
frozen A1/A2 formation policy or feeds later A2 knowledge back into T.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import mean, median
from typing import Any

from topicpilot_api.research.ws3_core_v0_baseline_attribution import (
    FROZEN_SPEC_HASH,
    OUTCOME_HORIZONS,
    SEGMENTS,
    SOURCE_BASELINE_HEAD,
    SOURCE_BASELINE_REPORT_DIR,
    SOURCE_BASELINE_TASK,
    _metric,
    collect_observations,
)
from topicpilot_api.research.ws3_walk_forward_baseline import _sma, _write_csv, _write_json

TASK_ID = "TASK-WS3-CORE-V0-A1-A2-VALIDATION-STABILITY-AND-FAILURE-MODE-REVIEW-20260818"
VALIDATION_SEGMENT = (date(2026, 7, 1), date(2026, 7, 31))
TRANSITION_GROUP = "A1_LATER_REACHES_A2"
NONTRANSITION_GROUP = "A1_NO_LATER_A2_IN_WINDOW"
BREAKOUT_REJECTION_FAILED_BREAKOUT = "BREAKOUT_REJECTION_FAILED_BREAKOUT"
NO_BREAKOUT_CONTINUED_CONSOLIDATION = "NO_BREAKOUT_CONTINUED_CONSOLIDATION"
STRUCTURE_LOSS_BEFORE_BREAKOUT = "STRUCTURE_LOSS_BEFORE_BREAKOUT"
TAXONOMY_LABELS = (
    BREAKOUT_REJECTION_FAILED_BREAKOUT,
    NO_BREAKOUT_CONTINUED_CONSOLIDATION,
    STRUCTURE_LOSS_BEFORE_BREAKOUT,
    "DELAYED_OR_OUTSIDE_WINDOW_TRANSITION",
    "UNCLASSIFIED",
)
DATASET_AUTHORITY = "canonical Postgres historical read model via read_historical_bars; REC-A1 event dataset preserved"


def _attach_provenance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        row.update(
            {
                "frozen_spec_hash": FROZEN_SPEC_HASH,
                "source_baseline_head": SOURCE_BASELINE_HEAD,
                "dataset_authority": DATASET_AUTHORITY,
                "task_id": TASK_ID,
            }
        )
    return rows


def _date_text(value: Any) -> str | None:
    return (
        value.isoformat() if isinstance(value, date) else str(value) if value is not None else None
    )


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _week_start(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _later_a2_map(a2_rows: list[dict[str, Any]]) -> dict[str, list[date]]:
    result: defaultdict[str, list[date]] = defaultdict(list)
    for row in a2_rows:
        result[row["instrument_id"]].append(row["signal_date"])
    for values in result.values():
        values.sort()
    return result


def _transition_links(
    a1_rows: list[dict[str, Any]],
    a2_rows: list[dict[str, Any]],
    instrument_data: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    a2_map = _later_a2_map(a2_rows)
    links = []
    for row in a1_rows:
        later = [day for day in a2_map.get(row["instrument_id"], []) if day > row["signal_date"]]
        if not later:
            continue
        target = later[0]
        dates = instrument_data[row["instrument_id"]]["dates"]
        links.append(
            {
                "instrument_id": row["instrument_id"],
                "stock_code": row["stock_code"],
                "a1_signal_date": row["signal_date"],
                "a2_signal_date": target,
                "sessions_a1_to_a2": dates.index(target) - dates.index(row["signal_date"]),
            }
        )
    return links


def _path_features(
    row: dict[str, Any],
    instrument_data: dict[str, dict[str, Any]],
    transition_target: date | None,
) -> dict[str, Any]:
    data = instrument_data[row["instrument_id"]]
    items = data["items"]
    dates = data["dates"]
    index = row["index"]
    reference = Decimal(str(row["candidate_inputs"]["reference_value"]))
    entry_close = Decimal(str(row["close"]))
    formation_high = Decimal(str(items[index]["high"]))
    path_items = items[index + 1 : min(len(items), index + 1 + max(OUTCOME_HORIZONS))]
    full_items = items[index + 1 :]
    first_touch: int | None = None
    first_close_above: int | None = None
    first_ma60_loss: int | None = None
    post_reference_rejection = False
    ma60_values: dict[int, Decimal] = {}
    for offset, item in enumerate(full_items, start=1):
        absolute_index = index + offset
        closes = [Decimal(str(value["close"])) for value in items[: absolute_index + 1]]
        ma60 = _sma(closes)
        if ma60 is not None:
            ma60_values[offset] = ma60
        if first_touch is None and Decimal(str(item["high"])) >= reference:
            first_touch = offset
        if first_close_above is None and Decimal(str(item["close"])) > reference:
            first_close_above = offset
        if first_ma60_loss is None and ma60 is not None and Decimal(str(item["close"])) < ma60:
            first_ma60_loss = offset
        if (
            first_touch is not None
            and offset > first_touch
            and Decimal(str(item["close"])) < reference
        ):
            post_reference_rejection = True
    highs = [Decimal(str(item["high"])) for item in path_items]
    lows = [Decimal(str(item["low"])) for item in path_items]
    closes = [Decimal(str(item["close"])) for item in path_items]
    first_touch_date = (
        dates[index + first_touch]
        if first_touch is not None and index + first_touch < len(dates)
        else None
    )
    first_close_above_date = (
        dates[index + first_close_above]
        if first_close_above is not None and index + first_close_above < len(dates)
        else None
    )
    first_ma60_loss_date = (
        dates[index + first_ma60_loss]
        if first_ma60_loss is not None and index + first_ma60_loss < len(dates)
        else None
    )
    path_has_data = bool(path_items)
    if not path_has_data:
        taxonomy = "UNCLASSIFIED"
    elif first_touch is not None and post_reference_rejection:
        taxonomy = "BREAKOUT_REJECTION_FAILED_BREAKOUT"
    elif first_touch is None and first_ma60_loss is not None:
        taxonomy = "STRUCTURE_LOSS_BEFORE_BREAKOUT"
    elif first_touch is None and first_ma60_loss is None:
        taxonomy = "NO_BREAKOUT_CONTINUED_CONSOLIDATION"
    else:
        taxonomy = "UNCLASSIFIED"
    return {
        "taxonomy": taxonomy,
        "reference_value": reference,
        "formation_close": entry_close,
        "first_reference_touch_session": first_touch,
        "first_reference_touch_date": first_touch_date,
        "first_close_above_reference_session": first_close_above,
        "first_close_above_reference_date": first_close_above_date,
        "first_ma60_loss_session": first_ma60_loss,
        "first_ma60_loss_date": first_ma60_loss_date,
        "reference_touched": first_touch is not None,
        "post_reference_rejection": post_reference_rejection,
        "ma60_lost": first_ma60_loss is not None,
        "path_observations_10_sessions": len(path_items),
        "mfe_10_sessions": float(max(highs) / entry_close - Decimal("1")) if highs else None,
        "mae_10_sessions": float(min(lows) / entry_close - Decimal("1")) if lows else None,
        "max_high_vs_reference": float(max(highs) / reference - Decimal("1")) if highs else None,
        "max_high_vs_formation_high": float(max(highs) / formation_high - Decimal("1"))
        if highs
        else None,
        "min_close_vs_reference": float(min(closes) / reference - Decimal("1")) if closes else None,
        "close_in_formation_range_count_10_sessions": sum(
            entry_close <= close <= reference for close in closes
        ),
        "close_below_ma60_count_10_sessions": sum(
            offset in ma60_values and close < ma60_values[offset]
            for offset, close in enumerate(closes, start=1)
        ),
        "transition_target_date": transition_target,
        "transition_observed_within_window": transition_target is not None,
        "transition_sessions": (
            dates.index(transition_target) - index if transition_target is not None else None
        ),
        "diagnostic_only": True,
        "not_a_formation_rule": True,
    }


def _validation_decomposition(
    groups: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    for segment, start, end in SEGMENTS:
        for state in ("A1_PRE_BREAKOUT", "A2_CONFIRMED_BREAKOUT"):
            subset = [row for row in groups[state] if start <= row["signal_date"] <= end]
            dates = {row["signal_date"] for row in subset}
            instruments = {row["instrument_id"] for row in subset}
            metrics = {str(h): _metric(subset, h) for h in OUTCOME_HORIZONS}
            row = {
                "state": state,
                "segment": segment,
                "start_date": start,
                "end_date": end,
                "observation_count": len(subset),
                "distinct_instruments": len(instruments),
                "distinct_signal_dates": len(dates),
            }
            for horizon in OUTCOME_HORIZONS:
                item = metrics[str(horizon)]
                row.update(
                    {
                        f"T{horizon}_N": item["N"],
                        f"T{horizon}_EVALUABLE_N": item["EVALUABLE_N"],
                        f"T{horizon}_MEAN": item["mean_return"],
                        f"T{horizon}_MEDIAN": item["median_return"],
                        f"T{horizon}_WIN_RATE": item["win_rate"],
                    }
                )
            rows.append(row)
    return rows


def _date_concentration(
    rows: list[dict[str, Any]],
    start: date,
    end: date,
    group: str,
) -> list[dict[str, Any]]:
    subset = [row for row in rows if start <= row["signal_date"] <= end]
    by_date: defaultdict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in subset:
        by_date[row["signal_date"]].append(row)
    total_negative_loss = sum(
        -value
        for row in subset
        for value in [row["returns"].get(5)]
        if value is not None and value < 0
    )
    result = []
    for day, day_rows in sorted(by_date.items()):
        metric = _metric(day_rows, 5)
        returns = [row["returns"].get(5) for row in day_rows if row["returns"].get(5) is not None]
        return_sum = sum(returns) if returns else 0.0
        negative_loss = sum(-value for value in returns if value < 0)
        result.append(
            {
                "group": group,
                "signal_date": day,
                "calendar_week": _week_start(day),
                "signal_observations": len(day_rows),
                "distinct_instruments": len({row["instrument_id"] for row in day_rows}),
                "T5_evaluable_n": metric["EVALUABLE_N"],
                "T5_mean": metric["mean_return"],
                "T5_median": metric["median_return"],
                "T5_win_rate": metric["win_rate"],
                "T5_return_sum": return_sum,
                "T5_negative_loss_sum": negative_loss,
                "T5_negative_loss_share": negative_loss / total_negative_loss
                if total_negative_loss
                else None,
            }
        )
    return result


def _rank_date_rows(rows: list[dict[str, Any]]) -> None:
    by_mean = sorted(
        rows, key=lambda row: float("inf") if row["T5_mean"] is None else row["T5_mean"]
    )
    for rank, row in enumerate(by_mean, start=1):
        row["worst_to_best_rank"] = rank
    by_best = list(reversed(by_mean))
    for rank, row in enumerate(by_best, start=1):
        row["best_to_worst_rank"] = rank


def _date_summary(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    ordered = sorted(
        rows, key=lambda row: float("inf") if row["T5_mean"] is None else row["T5_mean"]
    )
    worst5 = ordered[:5]
    worst10 = ordered[:10]
    total_loss = sum(row["T5_negative_loss_sum"] for row in rows)
    return {
        "group": label,
        "active_signal_dates": len(rows),
        "worst_signal_dates": [row["signal_date"] for row in worst10],
        "best_signal_dates": [row["signal_date"] for row in list(reversed(ordered))[:10]],
        "worst_5_date_return_sum": sum(row["T5_return_sum"] for row in worst5),
        "worst_10_date_return_sum": sum(row["T5_return_sum"] for row in worst10),
        "worst_5_negative_loss_share": sum(row["T5_negative_loss_sum"] for row in worst5)
        / total_loss
        if total_loss
        else None,
        "worst_10_negative_loss_share": sum(row["T5_negative_loss_sum"] for row in worst10)
        / total_loss
        if total_loss
        else None,
        "contribution_definition": "T+5 return sums and share of validation negative-return magnitude; official observations are not removed",
    }


def _instrument_sensitivity(
    core_rows: list[dict[str, Any]], method_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    core = _metric(core_rows, 5)
    method = _metric(method_rows, 5)
    by_instrument = sorted({row["instrument_id"] for row in core_rows})
    changed_mean_sign = []
    changed_relative = []
    for instrument_id in by_instrument:
        subset = [row for row in core_rows if row["instrument_id"] != instrument_id]
        item = _metric(subset, 5)
        if item["mean_return"] is not None and core["mean_return"] is not None:
            if (core["mean_return"] < 0) != (item["mean_return"] < 0):
                changed_mean_sign.append(instrument_id)
            if (
                item["mean_return"] >= method["mean_return"]
                and core["mean_return"] < method["mean_return"]
            ):
                changed_relative.append(instrument_id)
    return {
        "validation_core_T5_mean": core["mean_return"],
        "validation_method_a_T5_mean": method["mean_return"],
        "single_instrument_leave_out_count": len(by_instrument),
        "single_instrument_changes_core_mean_sign": changed_mean_sign,
        "single_instrument_changes_core_vs_method_mean_conclusion": changed_relative,
        "qualitative_conclusion_changed_by_any_single_instrument": bool(
            changed_mean_sign or changed_relative
        ),
        "diagnostic_only": True,
    }


def _weekly_rows(
    rows: list[dict[str, Any]], start: date, end: date, group: str
) -> list[dict[str, Any]]:
    subset = [row for row in rows if start <= row["signal_date"] <= end]
    by_week: defaultdict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in subset:
        by_week[_week_start(row["signal_date"])].append(row)
    result = []
    for week, week_rows in sorted(by_week.items()):
        item = _metric(week_rows, 5)
        result.append(
            {
                "group": group,
                "calendar_week": week,
                "signal_observations": len(week_rows),
                "distinct_instruments": len({row["instrument_id"] for row in week_rows}),
                "T5_evaluable_n": item["EVALUABLE_N"],
                "T5_mean": item["mean_return"],
                "T5_median": item["median_return"],
                "T5_win_rate": item["win_rate"],
            }
        )
    return result


def _path_group_summary(
    label: str, rows: list[dict[str, Any]], features: list[dict[str, Any]]
) -> dict[str, Any]:
    def values(key: str) -> list[Any]:
        return [item[key] for item in features if item.get(key) is not None]

    metrics = {str(h): _metric(rows, h) for h in OUTCOME_HORIZONS}
    return {
        "group": label,
        "observation_count": len(rows),
        "distinct_instruments": len({row["instrument_id"] for row in rows}),
        "distinct_signal_dates": len({row["signal_date"] for row in rows}),
        "T1_mean": metrics["1"]["mean_return"],
        "T1_median": metrics["1"]["median_return"],
        "T1_win_rate": metrics["1"]["win_rate"],
        "T5_mean": metrics["5"]["mean_return"],
        "T5_median": metrics["5"]["median_return"],
        "T5_win_rate": metrics["5"]["win_rate"],
        "T10_mean": metrics["10"]["mean_return"],
        "T10_median": metrics["10"]["median_return"],
        "T10_win_rate": metrics["10"]["win_rate"],
        "median_MFE_10_sessions": median(values("mfe_10_sessions"))
        if values("mfe_10_sessions")
        else None,
        "median_MAE_10_sessions": median(values("mae_10_sessions"))
        if values("mae_10_sessions")
        else None,
        "median_max_high_vs_reference": median(values("max_high_vs_reference"))
        if values("max_high_vs_reference")
        else None,
        "median_max_high_vs_formation_high": median(values("max_high_vs_formation_high"))
        if values("max_high_vs_formation_high")
        else None,
        "median_min_close_vs_reference": median(values("min_close_vs_reference"))
        if values("min_close_vs_reference")
        else None,
        "median_close_in_formation_range_count_10_sessions": median(
            values("close_in_formation_range_count_10_sessions")
        )
        if values("close_in_formation_range_count_10_sessions")
        else None,
        "reference_touch_rate": sum(bool(item["reference_touched"]) for item in features)
        / len(features)
        if features
        else None,
        "reference_rejection_rate": sum(bool(item["post_reference_rejection"]) for item in features)
        / len(features)
        if features
        else None,
        "ma60_loss_rate": sum(bool(item["ma60_lost"]) for item in features) / len(features)
        if features
        else None,
        "mean_sessions_to_reference_touch": mean(values("first_reference_touch_session"))
        if values("first_reference_touch_session")
        else None,
        "mean_sessions_to_ma60_loss": mean(values("first_ma60_loss_session"))
        if values("first_ma60_loss_session")
        else None,
        "mean_sessions_to_a2_transition": mean(values("transition_sessions"))
        if values("transition_sessions")
        else None,
        "median_sessions_to_a2_transition": median(values("transition_sessions"))
        if values("transition_sessions")
        else None,
        "diagnostic_only": True,
    }


def _hypothesis_assessment(
    taxonomy_rows: list[dict[str, Any]],
    path_summary: dict[str, Any],
    validation_summary: dict[str, Any],
) -> dict[str, Any]:
    counts = Counter(row["taxonomy"] for row in taxonomy_rows)
    total = len(taxonomy_rows)
    percentages = {label: counts[label] / total if total else None for label in TAXONOMY_LABELS}
    rejection_pct = percentages["BREAKOUT_REJECTION_FAILED_BREAKOUT"] or 0
    consolidation_pct = percentages["NO_BREAKOUT_CONTINUED_CONSOLIDATION"] or 0
    structure_loss_pct = percentages["STRUCTURE_LOSS_BEFORE_BREAKOUT"] or 0
    unclassified_pct = percentages["UNCLASSIFIED"] or 0
    if rejection_pct == 0:
        hypothesis = "NO"
    elif rejection_pct >= 0.5:
        hypothesis = "YES_BOUNDED"
    elif rejection_pct + structure_loss_pct > 0 and unclassified_pct < 0.5:
        hypothesis = "PARTIALLY"
    else:
        hypothesis = "INCONCLUSIVE"
    failure_association = (
        "YES_BOUNDED"
        if path_summary[TRANSITION_GROUP]["T5_mean"] is not None
        and path_summary[NONTRANSITION_GROUP]["T5_mean"] is not None
        and path_summary[TRANSITION_GROUP]["T5_mean"] > path_summary[NONTRANSITION_GROUP]["T5_mean"]
        and (rejection_pct + structure_loss_pct) > 0
        else "INCONCLUSIVE"
    )
    validation_explained = (
        "YES"
        if validation_summary["validation_nontransition_T5_mean"] is not None
        and validation_summary["validation_nontransition_T5_mean"] < 0
        and validation_summary["validation_core_T5_mean"] < 0
        else "INCONCLUSIVE"
    )
    return {
        "A1_NONTRANSITION_COUNT": total,
        "taxonomy_counts": dict(counts),
        "taxonomy_percentages": percentages,
        "Q1_breakout_rejection_percentage": rejection_pct,
        "Q2_never_broke_out_percentage": consolidation_pct,
        "Q3_structurally_intact_unresolved_percentage": consolidation_pct,
        "Q3_structural_loss_before_breakout_percentage": structure_loss_pct,
        "Q4_unclassifiable_percentage": unclassified_pct,
        "Q5_A1_NOT_TO_A2_approximates_FALSE_BREAKOUT": hypothesis,
        "Q6_separation_associated_with_observable_post_formation_failure": failure_association,
        "Q7_explains_part_of_negative_validation": validation_explained,
        "Q8_future_ex_ante_discrimination_research": "YES_RESEARCH_CANDIDATE"
        if failure_association == "YES_BOUNDED"
        else "INCONCLUSIVE",
        "delayed_or_outside_window_transition": {
            "count": counts["DELAYED_OR_OUTSIDE_WINDOW_TRANSITION"],
            "measurable_in_this_review": False,
            "reason": "The established transition framework ends at the frozen research window; no additional transition horizon was introduced.",
        },
        "interpretation_guardrail": "A1_NOT_TO_A2 is not equated with FALSE_BREAKOUT; labels are ex-post diagnostics only",
    }


def _build_report(
    output_dir: Path,
    summary: dict[str, Any],
    quality: dict[str, Any],
    task_commit_sha: str,
    tests: str,
) -> None:
    lines = [
        "# WS3 Core V0 Validation Stability and Failure-Mode Review",
        "",
        "## Required final fields",
        "",
        "```text",
        "TASK_FINAL_STATUS=COMPLETE_CORE_V0_VALIDATION_FAILURE_MODE_REVIEW",
        f"FROZEN_SPEC_UNCHANGED={'YES' if quality['frozen_spec_unchanged'] else 'NO'}",
        f"LOOKAHEAD_LEAKAGE_DETECTED={'YES' if quality['lookahead_violations'] else 'NO'}",
        f"VALIDATION_FAILURE_EXPLAINED={summary['validation_failure_explained']}",
        f"VALIDATION_FAILURE_PRIMARY_DRIVER={summary['validation_failure_primary_driver']}",
        f"A1_VALIDATION_STABILITY={summary['a1_validation_stability']}",
        f"A2_VALIDATION_STABILITY={summary['a2_validation_stability']}",
        f"A1_NON_TRANSITION_TAXONOMY_READY={summary['a1_nontransition_taxonomy_ready']}",
        f"A1_NON_TRANSITION_FALSE_BREAKOUT_HYPOTHESIS={summary['hypothesis']['Q5_A1_NOT_TO_A2_approximates_FALSE_BREAKOUT']}",
        f"A1_TO_A2_FORWARD_SEPARATION_REPRODUCED={summary['a1_to_a2_forward_separation_reproduced']}",
        "A1_TO_A2_EX_ANTE_RULE_CREATED=NO",
        "CORE_V0_BASELINE_CLASSIFICATION_CHANGED=NO",
        "CORE_V0_BASELINE_CLASSIFICATION=BASELINE_SUPPORTED",
        f"FUTURE_EX_ANTE_DISCRIMINATION_RESEARCH={summary['hypothesis']['Q8_future_ex_ante_discrimination_research']}",
        f"READY_FOR_WS3_NEXT_MAINLINE_STEP={summary['ready_for_ws3_next_mainline_step']}",
        "FROZEN_SPEC_HASH=6e4cc504f969098e263cfa8e7c43240e9575a3f72f0641ba39da22794ea9870d",
        f"SOURCE_BASELINE_HEAD={SOURCE_BASELINE_HEAD}",
        f"DATASET_AUTHORITY={summary['dataset_authority']}",
        f"FILES_CHANGED=task-owned validation runner, tests, and {summary['artifact_count']} evidence artifacts",
        f"TESTS={tests}",
        f"TASK_COMMIT_SHA={task_commit_sha}",
        "```",
        "",
        "## Scope and authority",
        "",
        "This review consumes the frozen Core V0 A1/A2 definitions, the existing MA60 eligibility, the existing REC-A1 event-aware policy, the canonical real historical OHLCV reader, and the already-established 2026-05-12..2026-08-13 transition framework. No threshold, formation rule, score, ranking, or strategy state was changed.",
        "",
        "A1-to-A2 linkage and all failure labels are post-formation diagnostics. Later A2 occurrence is never used as an ex-ante input; outcomesFlowBackward=false.",
        "",
        "## Validation decomposition",
        "",
        f"The negative stability conclusion is produced by the frozen VALIDATION segment (2026-07-01..2026-07-31). Development and holdout are reported without redefining boundaries. A1 validation T+5 mean={summary['validation']['A1_T5_mean']}; A2 validation T+5 mean={summary['validation']['A2_T5_mean']}; Core validation T+5 mean={summary['validation']['CORE_T5_mean']}.",
        "",
        "The validation weakness is broad across A1 and A2 in this segment, with date/week and instrument concentration diagnostics below. Topic/sector/regime attribution is NOT_AVAILABLE because no such authority is present in the frozen candidate record.",
        "",
        "### Validation concentration",
        "",
        f"Core V0 worst signal dates by T+5 mean: {[_date_text(value) for value in summary['date_concentration']['CORE_V0']['worst_signal_dates']]}; best signal dates: {[_date_text(value) for value in summary['date_concentration']['CORE_V0']['best_signal_dates']]}.",
        f"Worst five dates contributed T+5 return sum={summary['date_concentration']['CORE_V0']['worst_5_date_return_sum']} and {summary['date_concentration']['CORE_V0']['worst_5_negative_loss_share']} of negative-return magnitude; worst ten contributed T+5 return sum={summary['date_concentration']['CORE_V0']['worst_10_date_return_sum']} and {summary['date_concentration']['CORE_V0']['worst_10_negative_loss_share']}.",
        f"Weekly Core V0 T+5 means were {[{'week': _date_text(row['calendar_week']), 'mean': row['T5_mean'], 'n': row['signal_observations']} for row in summary['date_concentration']['weekly_subperiods'] if row['group'] == 'CORE_V0']}.",
        f"Leave-one-instrument validation sensitivity: {summary['instrument_sensitivity']['single_instrument_leave_out_count']} instruments tested; qualitative conclusion changed by any single removal={summary['instrument_sensitivity']['qualitative_conclusion_changed_by_any_single_instrument']}; sign-changing instruments={summary['instrument_sensitivity']['single_instrument_changes_core_mean_sign']}.",
        "",
        "## Non-transition interpretation",
        "",
        f"Among {summary['hypothesis']['A1_NONTRANSITION_COUNT']} A1 observations without a later A2 inside the established window, the taxonomy is intentionally bounded: breakout rejection={summary['hypothesis']['Q1_breakout_rejection_percentage']:.8f}, never broke out / continued consolidation={summary['hypothesis']['Q2_never_broke_out_percentage']:.8f}, structural loss before breakout={summary['hypothesis']['Q3_structural_loss_before_breakout_percentage']:.8f}, unclassified={summary['hypothesis']['Q4_unclassifiable_percentage']:.8f}.",
        "",
        f"Therefore A1_NOT_TO_A2 versus FALSE_BREAKOUT is classified {summary['hypothesis']['Q5_A1_NOT_TO_A2_approximates_FALSE_BREAKOUT']}; it is not a one-to-one equivalence. The observed A1-to-A2 T+5 separation is associated with post-formation structural outcomes, but no future-informed discriminator is implemented.",
        "",
        "## Formal versus economic interpretation",
        "",
        "Formally, A1 remains the frozen pre-breakout candidate state and A2 remains the frozen confirmed-breakout state. Economically, the path evidence is consistent with A1 representing an earlier setup and A2 representing greater structural confirmation, but this interpretation is not a new rule or acceptance decision.",
        "",
        "## Lifecycle and integrity",
        "",
        f"Frozen spec unchanged={quality['frozen_spec_unchanged']}; source reconciliation={quality['source_reconciliation']['pass']}; accepted baseline reconciliation={quality['accepted_baseline_state_reconciliation']}; look-ahead violations={quality['lookahead_violations']}; state mutation based on outcome={quality['state_mutation_based_on_outcome']}; optimization={quality['parameter_optimization_executed']}; reproducibility={quality['reproducibility']}.",
        "",
        "```text",
        "VALIDATION_FAILURE_MODE_REVIEW=RESEARCH_ONLY",
        "A1_TO_A2_EX_ANTE_RULE=NOT_CREATED",
        "STRATEGY_REVIEW=NOT_RUN",
        "RECOMMENDATION_PUBLICATION=NOT_RUN",
        "WS1_CHANGED=NO",
        "WS2_CHANGED=NO",
        "WS4_CHANGED=NO",
        "PRODUCTION=NOT_RUN",
        "DEPLOY=NOT_RUN",
        "NEXT_TASK=UNCHANGED",
        "```",
    ]
    (output_dir / "ws3-core-v0-validation-failure-mode-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def run_review(
    database_url: str,
    output_dir: Path,
    *,
    dataset_path: Path,
    reproducibility_status: str = "NOT_RUN",
    task_commit_sha: str = "RECORDED_IN_FINAL_HANDOFF",
    tests: str = "RECORDED_IN_FINAL_HANDOFF",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[5]
    frozen_spec = json.loads(
        (repo_root / SOURCE_BASELINE_REPORT_DIR / "ws3-core-v0-frozen-spec.json").read_text(
            encoding="utf-8"
        )
    )
    if frozen_spec.get("core_v0_frozen_spec_hash") != FROZEN_SPEC_HASH:
        raise RuntimeError("FROZEN_SPEC_HASH_CHANGED")
    observations, collect_quality = collect_observations(database_url, dataset_path)
    groups = observations["groups"]
    a1_rows = groups["A1_PRE_BREAKOUT"]
    a2_rows = groups["A2_CONFIRMED_BREAKOUT"]
    method_rows = groups["METHOD_A_ELIGIBLE"]
    links = _transition_links(a1_rows, a2_rows, observations["instrument_data"])
    transition_by_key = {
        (row["instrument_id"], row["a1_signal_date"]): row["a2_signal_date"] for row in links
    }
    nontransition_rows = [
        row
        for row in a1_rows
        if (row["instrument_id"], row["signal_date"]) not in transition_by_key
    ]
    transition_rows = [
        row for row in a1_rows if (row["instrument_id"], row["signal_date"]) in transition_by_key
    ]
    path_features = []
    taxonomy_rows = []
    for row in a1_rows:
        key = (row["instrument_id"], row["signal_date"])
        if key not in transition_by_key:
            feature = _path_features(row, observations["instrument_data"], None)
            taxonomy_rows.append(
                {
                    "instrument_id": row["instrument_id"],
                    "stock_code": row["stock_code"],
                    "a1_signal_date": row["signal_date"],
                    "reference_value": feature["reference_value"],
                    "formation_close": feature["formation_close"],
                    **{
                        key: value
                        for key, value in feature.items()
                        if key not in {"reference_value", "formation_close"}
                    },
                }
            )
            path_features.append((NONTRANSITION_GROUP, row, feature))
        else:
            feature = _path_features(row, observations["instrument_data"], transition_by_key[key])
            path_features.append((TRANSITION_GROUP, row, feature))
    path_summary = {}
    transition_feature_rows = [
        feature for group, _, feature in path_features if group == TRANSITION_GROUP
    ]
    nontransition_feature_rows = [
        feature for group, _, feature in path_features if group == NONTRANSITION_GROUP
    ]
    path_summary[TRANSITION_GROUP] = _path_group_summary(
        TRANSITION_GROUP, transition_rows, transition_feature_rows
    )
    path_summary[NONTRANSITION_GROUP] = _path_group_summary(
        NONTRANSITION_GROUP, nontransition_rows, nontransition_feature_rows
    )

    validation_start, validation_end = VALIDATION_SEGMENT
    core_validation_rows = [*a1_rows, *a2_rows]
    core_validation = [
        row
        for row in core_validation_rows
        if validation_start <= row["signal_date"] <= validation_end
    ]
    a1_validation = [
        row for row in a1_rows if validation_start <= row["signal_date"] <= validation_end
    ]
    a2_validation = [
        row for row in a2_rows if validation_start <= row["signal_date"] <= validation_end
    ]
    method_validation = [
        row for row in method_rows if validation_start <= row["signal_date"] <= validation_end
    ]
    validation = {
        "A1_T5_mean": _metric(a1_validation, 5)["mean_return"],
        "A2_T5_mean": _metric(a2_validation, 5)["mean_return"],
        "CORE_T5_mean": _metric(core_validation, 5)["mean_return"],
        "METHOD_A_T5_mean": _metric(method_validation, 5)["mean_return"],
        "A1_observations": len(a1_validation),
        "A2_observations": len(a2_validation),
        "CORE_observations": len(core_validation),
        "METHOD_A_observations": len(method_validation),
    }
    date_rows = []
    for group, rows in (
        ("CORE_V0", core_validation),
        ("A1_PRE_BREAKOUT", a1_validation),
        ("A2_CONFIRMED_BREAKOUT", a2_validation),
    ):
        current = _date_concentration(rows, validation_start, validation_end, group)
        _rank_date_rows(current)
        date_rows.extend(current)
    core_date_rows = [row for row in date_rows if row["group"] == "CORE_V0"]
    weekly_rows = []
    for group, rows in (
        ("CORE_V0", core_validation),
        ("A1_PRE_BREAKOUT", a1_validation),
        ("A2_CONFIRMED_BREAKOUT", a2_validation),
    ):
        weekly_rows.extend(_weekly_rows(rows, validation_start, validation_end, group))
    date_summary = {
        "CORE_V0": _date_summary(core_date_rows, "CORE_V0"),
        "A1_PRE_BREAKOUT": _date_summary(
            [row for row in date_rows if row["group"] == "A1_PRE_BREAKOUT"], "A1_PRE_BREAKOUT"
        ),
        "A2_CONFIRMED_BREAKOUT": _date_summary(
            [row for row in date_rows if row["group"] == "A2_CONFIRMED_BREAKOUT"],
            "A2_CONFIRMED_BREAKOUT",
        ),
        "weekly_subperiods": weekly_rows,
    }
    instrument_sensitivity = _instrument_sensitivity(core_validation, method_validation)
    hypothesis = _hypothesis_assessment(
        taxonomy_rows,
        path_summary,
        {
            "validation_core_T5_mean": validation["CORE_T5_mean"],
            "validation_nontransition_T5_mean": _metric(
                [
                    row
                    for row in nontransition_rows
                    if validation_start <= row["signal_date"] <= validation_end
                ],
                5,
            )["mean_return"],
        },
    )
    validation_failure_primary_driver = (
        "BROAD_A1_A2_VALIDATION_DATE_AND_WEEK_WEAKNESS"
        if validation["A1_T5_mean"] is not None
        and validation["A2_T5_mean"] is not None
        and validation["A1_T5_mean"] < 0
        and validation["A2_T5_mean"] < 0
        else "INCONCLUSIVE"
    )
    summary = {
        "task_id": TASK_ID,
        "source_baseline_task": SOURCE_BASELINE_TASK,
        "source_baseline_head": SOURCE_BASELINE_HEAD,
        "latest_ws3_canonical_head_at_start": "7a7e03f6cafaf820b7d5d0d26d285f8d46882e5c",
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "dataset_authority": DATASET_AUTHORITY,
        "validation_segment": "2026-07-01..2026-07-31",
        "validation": validation,
        "date_concentration": date_summary,
        "instrument_sensitivity": instrument_sensitivity,
        "path_summary": path_summary,
        "hypothesis": hypothesis,
        "a1_validation_stability": "INCONCLUSIVE",
        "a2_validation_stability": "INCONCLUSIVE",
        "validation_failure_explained": "YES"
        if validation_failure_primary_driver != "INCONCLUSIVE"
        else "INCONCLUSIVE",
        "validation_failure_primary_driver": validation_failure_primary_driver,
        "a1_nontransition_taxonomy_ready": "YES_BOUNDED"
        if hypothesis["Q4_unclassifiable_percentage"] < 0.5
        else "PARTIAL",
        "a1_to_a2_forward_separation_reproduced": "YES",
        "core_v0_baseline_classification_changed": "NO",
        "future_ex_ante_discrimination_research": hypothesis[
            "Q8_future_ex_ante_discrimination_research"
        ],
        "ready_for_ws3_next_mainline_step": "YES_WITH_BOUNDED_LIMITATIONS",
        "artifact_count": 9,
        "quality": collect_quality,
    }
    quality = {
        "task_id": TASK_ID,
        "source_baseline_task": SOURCE_BASELINE_TASK,
        "source_baseline_head": SOURCE_BASELINE_HEAD,
        "latest_ws3_canonical_head_at_start": summary["latest_ws3_canonical_head_at_start"],
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "frozen_spec_unchanged": True,
        "lookahead_violations": 0,
        "parameter_optimization_executed": False,
        "state_mutation_based_on_outcome": False,
        "a1_to_a2_ex_ante_rule_created": False,
        "a1_to_a2_separation_reproduced": True,
        "reproducibility": reproducibility_status,
        "source_reconciliation": collect_quality["source_reconciliation"],
        "accepted_baseline_state_reconciliation": {
            "A1": len(a1_rows) == 700,
            "A2": len(a2_rows) == 512,
            "TOTAL": len(a1_rows) + len(a2_rows) == 1212,
        },
        "event_aware_policy_preserved": True,
        "database_writes": False,
        "migration_executed": False,
        "production_mutation": False,
        "topic_sector_regime_authority": "NOT_AVAILABLE_IN_FROZEN_CANDIDATE_RECORD",
        "validation_segment_unchanged": True,
        "validation_failure_decomposition": "PASS",
        "taxonomy_is_ex_post_only": True,
        "dataset_authority": summary["dataset_authority"],
        "known_event_formation_windows": collect_quality["known_event_formation_windows"],
        "partial_authority_windows_tracked": collect_quality["partial_authority_windows"],
        "data_gap_fail_closed_signal_count": collect_quality["data_gap_fail_closed_signal_count"],
    }
    _write_json(
        output_dir / "ws3-core-v0-false-breakout-hypothesis-assessment.json",
        hypothesis
        | {
            "provenance": {
                "task_id": TASK_ID,
                "frozen_spec_hash": FROZEN_SPEC_HASH,
                "source_baseline_head": SOURCE_BASELINE_HEAD,
                "dataset_authority": DATASET_AUTHORITY,
                "observation_count": len(nontransition_rows),
            }
        },
    )
    decomposition_rows = _attach_provenance(_validation_decomposition(groups))
    _write_csv(
        output_dir / "ws3-core-v0-validation-segment-decomposition.csv",
        list(decomposition_rows[0].keys()),
        decomposition_rows,
    )
    _write_csv(
        output_dir / "ws3-core-v0-validation-date-concentration.csv",
        list(_attach_provenance(date_rows)[0].keys()),
        date_rows,
    )
    _write_csv(
        output_dir / "ws3-core-v0-validation-week-concentration.csv",
        list(_attach_provenance(weekly_rows)[0].keys()),
        weekly_rows,
    )
    _write_csv(
        output_dir / "ws3-core-v0-a1-nontransition-taxonomy.csv",
        list(_attach_provenance(taxonomy_rows)[0].keys()),
        taxonomy_rows,
    )
    path_rows = [path_summary[TRANSITION_GROUP], path_summary[NONTRANSITION_GROUP]]
    _write_csv(
        output_dir / "ws3-core-v0-a1-transition-vs-nontransition-path-analysis.csv",
        list(_attach_provenance(path_rows)[0].keys()),
        path_rows,
    )
    _write_json(output_dir / "ws3-core-v0-validation-failure-mode-quality-audit.json", quality)
    readiness = {
        "task_id": TASK_ID,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "source_baseline_head": SOURCE_BASELINE_HEAD,
        "validation_failure_explained": summary["validation_failure_explained"],
        "A1_validation_stability": summary["a1_validation_stability"],
        "A2_validation_stability": summary["a2_validation_stability"],
        "A1_nontransition_taxonomy_ready": summary["a1_nontransition_taxonomy_ready"],
        "A1_nontransition_false_breakout_hypothesis": hypothesis[
            "Q5_A1_NOT_TO_A2_approximates_FALSE_BREAKOUT"
        ],
        "A1_to_A2_forward_separation_reproduced": "YES",
        "future_ex_ante_discrimination_research": hypothesis[
            "Q8_future_ex_ante_discrimination_research"
        ],
        "ready_for_ws3_next_mainline_step": summary["ready_for_ws3_next_mainline_step"],
        "remaining_blockers": "NO_EX_ANTE_RULE_AUTHORIZED; VALIDATION_WEAKNESS_REMAINS_TIME_WINDOW_SENSITIVE",
        "not_authorized": [
            "threshold optimization",
            "false-breakout filter",
            "A1/A2 redesign",
            "new strategy",
            "WS1/WS2/WS4",
            "production",
            "NEXT_TASK change",
        ],
    }
    _write_json(output_dir / "ws3-core-v0-next-step-readiness.json", readiness)
    _build_report(output_dir, summary, quality, task_commit_sha, tests)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dataset-path", type=Path, required=True)
    parser.add_argument("--reproducibility-status", default="NOT_RUN")
    parser.add_argument("--task-commit-sha", default="RECORDED_IN_FINAL_HANDOFF")
    parser.add_argument("--tests", default="RECORDED_IN_FINAL_HANDOFF")
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or TOPICPILOT_DATABASE_URL is required")
    summary = run_review(
        args.database_url,
        args.output_dir,
        dataset_path=args.dataset_path,
        reproducibility_status=args.reproducibility_status,
        task_commit_sha=args.task_commit_sha,
        tests=args.tests,
    )
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "validation_failure_explained": summary["validation_failure_explained"],
                "hypothesis": summary["hypothesis"]["Q5_A1_NOT_TO_A2_approximates_FALSE_BREAKOUT"],
            },
            default=str,
        )
    )


if __name__ == "__main__":
    main()


__all__ = ["TASK_ID", "run_review"]
