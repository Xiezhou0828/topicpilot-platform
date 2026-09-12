"""Research-only ex-ante discrimination diagnostics for frozen Core V0 A1.

The module freezes a bounded feature inventory before comparing the existing
post-formation cohorts.  It consumes only canonical historical observations
available at or before each A1 signal date.  Cohort membership is an outcome
label for evaluation and is never included in the feature matrix.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from decimal import Decimal, localcontext
from itertools import pairwise
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any

from topicpilot_api.research.ws3_core_v0_baseline_attribution import (
    FROZEN_SPEC_HASH,
    SEGMENTS,
    SOURCE_BASELINE_HEAD,
    SOURCE_BASELINE_REPORT_DIR,
    collect_observations,
)
from topicpilot_api.research.ws3_core_v0_validation_failure_mode import (
    BREAKOUT_REJECTION_FAILED_BREAKOUT,
    _transition_links,
)
from topicpilot_api.research.ws3_walk_forward_baseline import _write_csv, _write_json
from topicpilot_api.technical_publication import _macd, _rsi_wilder, _sma

TASK_ID = "TASK-WS3-CORE-V0-A1-EX-ANTE-SUCCESS-VS-FAILED-BREAKOUT-DISCRIMINATION-RESEARCH-20260818"
SOURCE_CANONICAL_HEAD = "3ab70b612cbb30335b43a5650d145488f9e8b2c1"
DATASET_AUTHORITY = (
    "canonical Postgres historical read model via read_historical_bars; "
    "REC-A1 event dataset preserved"
)
MANIFEST_VERSION = "ws3-core-v0-a1-ex-ante-feature-manifest.v1"
PRIMARY_COHORTS = ("SUCCESSFUL_A1", "FAILED_BREAKOUT_A1")
SECONDARY_COHORTS = (
    "CONTINUED_CONSOLIDATION",
    "STRUCTURE_LOSS_BEFORE_BREAKOUT",
    "UNCLASSIFIED",
)
ANALYTICAL_ARTIFACT_NAMES = (
    "ws3-core-v0-a1-ex-ante-feature-manifest.json",
    "ws3-core-v0-a1-success-vs-failed-feature-comparison.csv",
    "ws3-core-v0-a1-feature-quantile-monotonicity.csv",
    "ws3-core-v0-a1-feature-time-stability.csv",
    "ws3-core-v0-a1-feature-date-regime-confounding.csv",
    "ws3-core-v0-a1-feature-family-assessment.json",
    "ws3-core-v0-a1-multivariate-diagnostic.json",
)
COHORT_LABELS = PRIMARY_COHORTS + SECONDARY_COHORTS
FORBIDDEN_FEATURE_TERMS = (
    "future",
    "transition_status",
    "transition_time",
    "future_return",
    "future_high",
    "future_low",
    "taxonomy_label",
    "outcome",
    "rejection_after",
)
EFFECT_SMALL = 0.20
EFFECT_NEGLIGIBLE = 0.10


def _date_value(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _number(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _float(value: Decimal | None) -> float | None:
    return float(value) if value is not None and value.is_finite() else None


def _ratio(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator in (None, Decimal(0)):
        return None
    with localcontext() as context:
        context.prec = 50
        return numerator / denominator


def _return(closes: Sequence[Decimal | None], index: int, period: int) -> Decimal | None:
    if index < period:
        return None
    current = closes[index]
    anchor = closes[index - period]
    if current is None or anchor in (None, Decimal(0)):
        return None
    return _ratio(current, anchor) - Decimal(1)


def _mean_decimal(values: Sequence[Decimal | None]) -> Decimal | None:
    valid = [value for value in values if value is not None]
    return sum(valid, Decimal(0)) / Decimal(len(valid)) if valid else None


def _std_decimal(values: Sequence[Decimal | None]) -> Decimal | None:
    valid = [value for value in values if value is not None]
    if len(valid) < 2:
        return None
    average = sum(valid, Decimal(0)) / Decimal(len(valid))
    variance = sum((value - average) ** 2 for value in valid) / Decimal(len(valid))
    return variance.sqrt()


def _last_streak(values: Sequence[bool]) -> int:
    count = 0
    for value in reversed(values):
        if not value:
            break
        count += 1
    return count


def _percentile(values: Sequence[float], fraction: float) -> float | None:
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


def _feature_spec(
    name: str,
    category: str,
    definition: str,
    inputs: Sequence[str],
    lookback: str,
    derivation: str,
    *,
    multivariate: bool = False,
) -> dict[str, Any]:
    return {
        "feature_name": name,
        "category": category,
        "definition": definition,
        "input_columns": list(inputs),
        "lookback": lookback,
        "timestamp_rule": "FEATURE_TIMESTAMP <= A1_SIGNAL_TIMESTAMP",
        "point_in_time_available": True,
        "derivation_method": derivation,
        "missingness": "MEASURED_FROM_CANONICAL_A1_FEATURE_MATRIX",
        "authority_source": DATASET_AUTHORITY,
        "allowed_for_primary_analysis": True,
        "allowed_for_multivariate": multivariate,
    }


def build_feature_manifest() -> list[dict[str, Any]]:
    """Return the fixed inventory; do not add features after outcome review."""

    specs = [
        _feature_spec(
            "reference_gap_pct",
            "BREAKOUT_PROXIMITY",
            "(reference_value - close_t) / reference_value",
            ("close", "candidate_inputs.reference_value"),
            "A1 reference and T close",
            "Frozen candidate reference lineage plus T close",
            multivariate=True,
        ),
        _feature_spec(
            "recent_20_high_proximity",
            "BREAKOUT_PROXIMITY",
            "close_t / max(high_{t-19..t}) - 1",
            ("high", "close"),
            "20 sessions including T",
            "Trailing canonical OHLCV window",
        ),
        _feature_spec(
            "recent_20_close_range_location",
            "BREAKOUT_PROXIMITY",
            "(close_t - min(close_{t-19..t})) / (max(close_{t-19..t}) - min(close_{t-19..t}))",
            ("close",),
            "20 sessions including T",
            "Trailing canonical close range",
        ),
        _feature_spec(
            "reference_touch_count_20",
            "BREAKOUT_PROXIMITY",
            "count(high_s >= reference_value) / available trailing sessions",
            ("high", "candidate_inputs.reference_value"),
            "20 sessions including T",
            "Frozen reference level and trailing high observations",
        ),
        _feature_spec(
            "recent_20_high_age_sessions",
            "CONSOLIDATION_STRUCTURE",
            "sessions since the most recent trailing-20 maximum high",
            ("high",),
            "20 sessions including T",
            "Trailing high maximum and canonical session order",
        ),
        _feature_spec(
            "reference_below_high_streak",
            "CONSOLIDATION_STRUCTURE",
            "consecutive sessions ending at T with high_s < frozen reference_value",
            ("high", "candidate_inputs.reference_value"),
            "Available trailing history",
            "Frozen reference level and prior OHLCV path",
        ),
        _feature_spec(
            "return_1d",
            "MOMENTUM",
            "close_t / close_{t-1} - 1",
            ("close",),
            "2 sessions",
            "Trailing canonical close return",
        ),
        _feature_spec(
            "return_3d",
            "MOMENTUM",
            "close_t / close_{t-3} - 1",
            ("close",),
            "4 sessions",
            "Trailing canonical close return",
        ),
        _feature_spec(
            "return_5d",
            "MOMENTUM",
            "close_t / close_{t-5} - 1",
            ("close",),
            "6 sessions",
            "Existing raw close return semantics",
            multivariate=True,
        ),
        _feature_spec(
            "return_10d",
            "MOMENTUM",
            "close_t / close_{t-10} - 1",
            ("close",),
            "11 sessions",
            "Trailing canonical close return",
        ),
        _feature_spec(
            "return_20d",
            "MOMENTUM",
            "close_t / close_{t-20} - 1",
            ("close",),
            "21 sessions",
            "Existing raw close return semantics",
        ),
        _feature_spec(
            "close_ma20_distance",
            "MA_STRUCTURE",
            "close_t / SMA20(close)_t - 1",
            ("close",),
            "20 sessions",
            "SMA_CLOSE_V1 deterministic derivation",
        ),
        _feature_spec(
            "close_ma60_distance",
            "MA_STRUCTURE",
            "close_t / SMA60(close)_t - 1",
            ("close",),
            "60 sessions",
            "Existing frozen MA60 eligibility calculation",
            multivariate=True,
        ),
        _feature_spec(
            "ma20_ma60_spread",
            "MA_STRUCTURE",
            "SMA20(close)_t / SMA60(close)_t - 1",
            ("close",),
            "60 sessions",
            "SMA_CLOSE_V1 deterministic derivation",
        ),
        _feature_spec(
            "ma20_slope_5d",
            "MA_STRUCTURE",
            "SMA20_t / SMA20_{t-5} - 1",
            ("close",),
            "65 sessions",
            "Trailing SMA20 slope",
        ),
        _feature_spec(
            "ma60_slope_5d",
            "MA_STRUCTURE",
            "SMA60_t / SMA60_{t-5} - 1",
            ("close",),
            "65 sessions",
            "Trailing SMA60 slope",
        ),
        _feature_spec(
            "ma60_slope_20d",
            "MA_STRUCTURE",
            "SMA60_t / SMA60_{t-20} - 1",
            ("close",),
            "80 sessions",
            "Trailing SMA60 slope",
        ),
        _feature_spec(
            "volume_ratio_5",
            "VOLUME_CONFIRMATION",
            "volume_t / SMA5(volume)_t",
            ("volume",),
            "5 sessions",
            "SMA_VOLUME_QUANTITY_V1 deterministic derivation",
            multivariate=True,
        ),
        _feature_spec(
            "volume_ratio_20",
            "VOLUME_CONFIRMATION",
            "volume_t / SMA20(volume)_t",
            ("volume",),
            "20 sessions",
            "VOLUME_RATIO_20_V1 deterministic derivation",
            multivariate=True,
        ),
        _feature_spec(
            "volume_ma5_ma20_spread",
            "VOLUME_CONFIRMATION",
            "SMA5(volume)_t / SMA20(volume)_t - 1",
            ("volume",),
            "20 sessions",
            "Trailing volume averages",
        ),
        _feature_spec(
            "volume_expansion_5_vs_prior20",
            "VOLUME_CONFIRMATION",
            "mean(volume_{t-4..t}) / mean(volume_{t-24..t-5}) - 1",
            ("volume",),
            "25 sessions",
            "Trailing-only volume expansion",
        ),
        _feature_spec(
            "true_range_pct",
            "VOLATILITY",
            "(high_t - low_t) / close_t",
            ("high", "low", "close"),
            "1 session",
            "Same-day canonical OHLCV range",
        ),
        _feature_spec(
            "atr14_pct",
            "VOLATILITY",
            "mean(high_s - low_s, s=t-13..t) / close_t",
            ("high", "low", "close"),
            "14 sessions",
            "Trailing raw true-range average",
            multivariate=True,
        ),
        _feature_spec(
            "realized_volatility_20",
            "VOLATILITY",
            "population stddev of trailing 1D close returns over 20 returns",
            ("close",),
            "21 sessions",
            "Trailing close-return dispersion",
        ),
        _feature_spec(
            "range_compression_5_vs20",
            "VOLATILITY",
            "mean(high-low)_{t-4..t} / mean(high-low)_{t-19..t} - 1",
            ("high", "low"),
            "20 sessions",
            "Trailing raw range compression",
        ),
        _feature_spec(
            "candle_body_range_fraction",
            "CANDLE_REJECTION",
            "abs(close_t - open_t) / (high_t - low_t)",
            ("open", "high", "low", "close"),
            "1 session",
            "A1-day canonical candle geometry",
        ),
        _feature_spec(
            "upper_wick_range_fraction",
            "CANDLE_REJECTION",
            "(high_t - max(open_t, close_t)) / (high_t - low_t)",
            ("open", "high", "low", "close"),
            "1 session",
            "A1-day canonical candle geometry",
        ),
        _feature_spec(
            "lower_wick_range_fraction",
            "CANDLE_REJECTION",
            "(min(open_t, close_t) - low_t) / (high_t - low_t)",
            ("open", "high", "low", "close"),
            "1 session",
            "A1-day canonical candle geometry",
        ),
        _feature_spec(
            "close_location_value",
            "CANDLE_REJECTION",
            "(close_t - low_t) / (high_t - low_t)",
            ("high", "low", "close"),
            "1 session",
            "A1-day canonical candle geometry",
            multivariate=True,
        ),
        _feature_spec(
            "gap_pct",
            "CANDLE_REJECTION",
            "(open_t - close_{t-1}) / close_{t-1}",
            ("open", "close"),
            "2 sessions",
            "Trailing prior close and T open",
        ),
        _feature_spec(
            "rsi14",
            "TECHNICAL_INDICATORS",
            "RSI Wilder 14 using trailing close history through T",
            ("close",),
            "15+ sessions",
            "Existing RSI_WILDER_14_V1 derivation",
        ),
        _feature_spec(
            "macd_line_12_26",
            "TECHNICAL_INDICATORS",
            "EMA12(close)_t - EMA26(close)_t with seeded EMA",
            ("close",),
            "26+ sessions",
            "Existing MACD_12_26_9_SMA_SEEDED_EMA_V1 derivation",
        ),
        _feature_spec(
            "macd_histogram_12_26_9",
            "TECHNICAL_INDICATORS",
            "MACD line minus seeded signal through T",
            ("close",),
            "34+ sessions",
            "Existing MACD_12_26_9_SMA_SEEDED_EMA_V1 derivation",
        ),
        _feature_spec(
            "same_day_universe_breadth_above_ma60",
            "MARKET_REGIME",
            "same-day valid-universe share with close >= trailing SMA60",
            ("close",),
            "60 sessions per instrument",
            "Point-in-time cross-sectional canonical OHLCV aggregation",
            multivariate=True,
        ),
        _feature_spec(
            "same_day_universe_median_return_1d",
            "MARKET_REGIME",
            "same-day median valid-universe 1D close return",
            ("close",),
            "2 sessions per instrument",
            "Point-in-time cross-sectional canonical OHLCV aggregation",
        ),
        _feature_spec(
            "same_day_universe_median_return_5d",
            "MARKET_REGIME",
            "same-day median valid-universe 5D close return",
            ("close",),
            "6 sessions per instrument",
            "Point-in-time cross-sectional canonical OHLCV aggregation",
        ),
        _feature_spec(
            "same_day_signal_density",
            "MARKET_REGIME",
            "A1 signal count on T divided by same-day valid-universe count",
            ("close",),
            "Same date T only",
            "Point-in-time frozen A1 formation output aggregation",
        ),
        _feature_spec(
            "trailing_20d_breadth_above_ma60",
            "MARKET_REGIME",
            "mean of same-day universe breadth over prior 20 observed universe dates including T",
            ("close",),
            "20 global observed dates",
            "Trailing point-in-time market breadth aggregation",
        ),
        _feature_spec(
            "same_day_return_5d_percentile",
            "RELATIVE_CONTEXT",
            "percentile rank of instrument 5D return within valid same-day universe",
            ("close",),
            "6 sessions per instrument and date cross-section",
            "Point-in-time cross-sectional rank; no future observations",
        ),
        _feature_spec(
            "same_day_volume_ratio_20_percentile",
            "RELATIVE_CONTEXT",
            "percentile rank of instrument volume ratio 20 within valid same-day universe",
            ("volume",),
            "20 sessions per instrument and date cross-section",
            "Point-in-time cross-sectional rank; no future observations",
        ),
    ]
    return specs


def _build_series(items: Sequence[Mapping[str, Any]]) -> dict[str, list[Decimal | None]]:
    closes = [_number(item.get("close")) for item in items]
    volumes = [_number(item.get("volume")) for item in items]
    highs = [_number(item.get("high")) for item in items]
    lows = [_number(item.get("low")) for item in items]
    series: dict[str, list[Decimal | None]] = {"close": closes, "volume": volumes}
    for period in (5, 20, 60):
        series[f"ma{period}"] = _sma(closes, period)
    for period in (1, 3, 5, 10, 20):
        series[f"return_{period}d"] = [
            _return(closes, index, period) for index in range(len(items))
        ]
    volume_ma5 = _sma(volumes, 5)
    volume_ma20 = _sma(volumes, 20)
    series["volume_ratio_5"] = [_ratio(volumes[i], volume_ma5[i]) for i in range(len(items))]
    series["volume_ratio_20"] = [_ratio(volumes[i], volume_ma20[i]) for i in range(len(items))]
    series["rsi14"] = _rsi_wilder(closes, 14)
    series.update(_macd(closes))
    true_ranges = [
        high - low if high is not None and low is not None else None
        for high, low in zip(highs, lows, strict=True)
    ]
    series["true_range"] = true_ranges
    series["atr14"] = _sma(true_ranges, 14)
    return series


def _window(values: Sequence[Decimal | None], index: int, length: int) -> list[Decimal | None]:
    return list(values[max(0, index - length + 1) : index + 1])


def _last_value(values: Sequence[Decimal | None], index: int) -> Decimal | None:
    return values[index] if 0 <= index < len(values) else None


def _feature_values(
    row: Mapping[str, Any],
    data: Mapping[str, Any],
    series: Mapping[str, Sequence[Decimal | None]],
    market_context: Mapping[str, Any],
) -> dict[str, float | None]:
    items = data["items"]
    index = int(row["index"])
    close = _number(items[index].get("close"))
    high = _number(items[index].get("high"))
    low = _number(items[index].get("low"))
    open_value = _number(items[index].get("open"))
    previous_close = _last_value(series["close"], index - 1)
    reference = _number(row["candidate_inputs"].get("reference_value"))
    highs = _window([_number(item.get("high")) for item in items], index, 20)
    closes = _window(series["close"], index, 20)
    ranges = _window(series["true_range"], index, 20)
    volumes = _window(series["volume"], index, 20)
    last5_ranges = ranges[-5:]
    prior20_volumes = [
        _number(item.get("volume")) for item in items[max(0, index - 24) : max(0, index - 4)]
    ]
    current_ma20 = _last_value(series["ma20"], index)
    current_ma60 = _last_value(series["ma60"], index)
    ma20_5 = _last_value(series["ma20"], index - 5)
    ma60_5 = _last_value(series["ma60"], index - 5)
    ma60_20 = _last_value(series["ma60"], index - 20)
    high_values = [value for value in highs if value is not None]
    close_values = [value for value in closes if value is not None]
    range_values = [value for value in ranges if value is not None]
    volume_values = [value for value in volumes if value is not None]
    close_range = max(close_values) - min(close_values) if close_values else None
    current_range = high - low if high is not None and low is not None else None
    current_range_nonzero = current_range not in (None, Decimal(0))
    recent_max = max(high_values) if high_values else None
    recent_min_close = min(close_values) if close_values else None
    current_return_5d = _float(_last_value(series["return_5d"], index))
    current_volume_ratio_20 = _float(_last_value(series["volume_ratio_20"], index))
    recent_high_age = None
    if recent_max is not None:
        high_indices = [i for i, value in enumerate(highs) if value == recent_max]
        if high_indices:
            recent_high_age = len(highs) - 1 - high_indices[-1]
    return {
        "reference_gap_pct": _float(_ratio(reference - close, reference)),
        "recent_20_high_proximity": _float(
            _ratio(close, recent_max) - Decimal(1)
            if close is not None and recent_max not in (None, Decimal(0))
            else None
        ),
        "recent_20_close_range_location": _float(
            _ratio(close - recent_min_close, close_range)
            if close_range not in (None, Decimal(0))
            else None
        ),
        "reference_touch_count_20": (
            sum(value >= reference for value in high_values) / len(high_values)
            if reference is not None and high_values
            else None
        ),
        "recent_20_high_age_sessions": float(recent_high_age)
        if recent_high_age is not None
        else None,
        "reference_below_high_streak": (
            float(_last_streak([value < reference for value in highs if value is not None]))
            if reference is not None and high_values
            else None
        ),
        **{
            f"return_{period}d": _float(_last_value(series[f"return_{period}d"], index))
            for period in (1, 3, 5, 10, 20)
        },
        "close_ma20_distance": _float(
            _ratio(close, current_ma20) - Decimal(1) if current_ma20 else None
        ),
        "close_ma60_distance": _float(
            _ratio(close, current_ma60) - Decimal(1) if current_ma60 else None
        ),
        "ma20_ma60_spread": _float(
            _ratio(current_ma20, current_ma60) - Decimal(1) if current_ma60 else None
        ),
        "ma20_slope_5d": _float(_ratio(current_ma20, ma20_5) - Decimal(1) if ma20_5 else None),
        "ma60_slope_5d": _float(_ratio(current_ma60, ma60_5) - Decimal(1) if ma60_5 else None),
        "ma60_slope_20d": _float(_ratio(current_ma60, ma60_20) - Decimal(1) if ma60_20 else None),
        "volume_ratio_5": _float(_last_value(series["volume_ratio_5"], index)),
        "volume_ratio_20": _float(_last_value(series["volume_ratio_20"], index)),
        "volume_ma5_ma20_spread": _float(
            _ratio(_mean_decimal(volume_values[-5:]), _mean_decimal(volume_values)) - Decimal(1)
            if _mean_decimal(volume_values)
            else None
        ),
        "volume_expansion_5_vs_prior20": _float(
            _ratio(_mean_decimal(volume_values[-5:]), _mean_decimal(prior20_volumes)) - Decimal(1)
            if _mean_decimal(prior20_volumes)
            else None
        ),
        "true_range_pct": _float(_ratio(current_range, close)),
        "atr14_pct": _float(_ratio(_last_value(series["atr14"], index), close)),
        "realized_volatility_20": (
            pstdev(
                [
                    float(value)
                    for value in [
                        _last_value(series["return_1d"], i)
                        for i in range(max(0, index - 19), index + 1)
                    ]
                    if value is not None
                ]
            )
            if len(
                [
                    value
                    for value in [
                        _last_value(series["return_1d"], i)
                        for i in range(max(0, index - 19), index + 1)
                    ]
                    if value is not None
                ]
            )
            >= 2
            else None
        ),
        "range_compression_5_vs20": _float(
            _ratio(_mean_decimal(last5_ranges), _mean_decimal(range_values)) - Decimal(1)
            if _mean_decimal(range_values)
            else None
        ),
        "candle_body_range_fraction": _float(
            _ratio(abs(close - open_value), current_range)
            if current_range_nonzero and open_value is not None and close is not None
            else None
        ),
        "upper_wick_range_fraction": _float(
            _ratio(high - max(open_value, close), current_range)
            if current_range_nonzero
            and high is not None
            and open_value is not None
            and close is not None
            else None
        ),
        "lower_wick_range_fraction": _float(
            _ratio(min(open_value, close) - low, current_range)
            if current_range_nonzero
            and low is not None
            and open_value is not None
            and close is not None
            else None
        ),
        "close_location_value": _float(
            _ratio(close - low, current_range)
            if current_range_nonzero and close is not None and low is not None
            else None
        ),
        "gap_pct": _float(
            _ratio(open_value - previous_close, previous_close)
            if open_value is not None and previous_close not in (None, Decimal(0))
            else None
        ),
        "rsi14": _float(_last_value(series["rsi14"], index)),
        "macd_line_12_26": _float(_last_value(series["MACD_12_26_9"], index)),
        "macd_histogram_12_26_9": _float(_last_value(series["MACD_HISTOGRAM_12_26_9"], index)),
        "same_day_universe_breadth_above_ma60": market_context.get("breadth"),
        "same_day_universe_median_return_1d": market_context.get("median_return_1d"),
        "same_day_universe_median_return_5d": market_context.get("median_return_5d"),
        "same_day_signal_density": market_context.get("signal_density"),
        "trailing_20d_breadth_above_ma60": market_context.get("trailing_breadth"),
        "same_day_return_5d_percentile": _percentile_rank(
            current_return_5d, market_context.get("return_5d_values", [])
        ),
        "same_day_volume_ratio_20_percentile": _percentile_rank(
            current_volume_ratio_20, market_context.get("volume_ratio_20_values", [])
        ),
    }


def _percentile_rank(value: float | None, values: Sequence[float]) -> float | None:
    if value is None or not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return 0.5
    less = sum(candidate < value for candidate in ordered)
    equal = sum(candidate == value for candidate in ordered)
    return (less + 0.5 * equal) / len(ordered)


def _build_market_context(
    instrument_data: Mapping[str, Mapping[str, Any]], a1_rows: Sequence[Mapping[str, Any]]
) -> dict[date, dict[str, Any]]:
    """Build same-day context from canonical bars without using cohort labels."""

    by_date: defaultdict[date, list[dict[str, float]]] = defaultdict(list)
    for data in instrument_data.values():
        items = data["items"]
        dates = data["dates"]
        series = _build_series(items)
        for index, trading_date in enumerate(dates):
            if index < 60:
                continue
            close = _last_value(series["close"], index)
            ma60 = _last_value(series["ma60"], index)
            return_1d = _last_value(series["return_1d"], index)
            return_5d = _last_value(series["return_5d"], index)
            volume_ratio = _last_value(series["volume_ratio_20"], index)
            if close is None or ma60 is None:
                continue
            by_date[trading_date].append(
                {
                    "above_ma60": float(close >= ma60),
                    "return_1d": float(return_1d) if return_1d is not None else None,
                    "return_5d": float(return_5d) if return_5d is not None else None,
                    "volume_ratio_20": float(volume_ratio) if volume_ratio is not None else None,
                }
            )
    signal_count = Counter(_date_value(row["signal_date"]) for row in a1_rows)
    context: dict[date, dict[str, Any]] = {}
    for trading_date, rows in sorted(by_date.items()):
        valid_return_1d = [row["return_1d"] for row in rows if row["return_1d"] is not None]
        valid_return_5d = [row["return_5d"] for row in rows if row["return_5d"] is not None]
        valid_volume_ratio = [
            row["volume_ratio_20"] for row in rows if row["volume_ratio_20"] is not None
        ]
        context[trading_date] = {
            "breadth": mean(row["above_ma60"] for row in rows) if rows else None,
            "median_return_1d": median(valid_return_1d) if valid_return_1d else None,
            "median_return_5d": median(valid_return_5d) if valid_return_5d else None,
            "universe_count": len(rows),
            "return_5d_values": valid_return_5d,
            "volume_ratio_20_values": valid_volume_ratio,
            "signal_density": signal_count[trading_date] / len(rows) if rows else None,
        }
    dates = sorted(context)
    for position, trading_date in enumerate(dates):
        prior_dates = dates[max(0, position - 19) : position + 1]
        breadth_values = [context[value]["breadth"] for value in prior_dates]
        context[trading_date]["trailing_breadth"] = mean(breadth_values) if breadth_values else None
    return context


def _attach_market_context(
    row: Mapping[str, Any], context: Mapping[date, Mapping[str, Any]]
) -> dict[str, Any]:
    trading_date = _date_value(row["signal_date"])
    base = dict(context.get(trading_date, {}))
    base["return_5d_percentile"] = _percentile_rank(
        None,
        base.get("return_5d_values", []),
    )
    base["volume_ratio_20_percentile"] = _percentile_rank(
        None,
        base.get("volume_ratio_20_values", []),
    )
    return base


def _add_cross_sectional_percentiles(
    feature_rows: list[dict[str, Any]], context: Mapping[date, Mapping[str, Any]]
) -> None:
    """Fill row-specific same-day ranks after the non-label feature pass."""

    by_date: defaultdict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in feature_rows:
        by_date[_date_value(row["signal_date"])].append(row)
    for rows in by_date.values():
        returns = [row["return_5d"] for row in rows if row.get("return_5d") is not None]
        volumes = [row["volume_ratio_20"] for row in rows if row.get("volume_ratio_20") is not None]
        for row in rows:
            row["same_day_return_5d_percentile"] = _percentile_rank(row.get("return_5d"), returns)
            row["same_day_volume_ratio_20_percentile"] = _percentile_rank(
                row.get("volume_ratio_20"), volumes
            )


def _load_taxonomy(path: Path) -> dict[tuple[str, date], str]:
    result: dict[tuple[str, date], str] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            result[(row["instrument_id"], _date_value(row["a1_signal_date"]))] = row["taxonomy"]
    return result


def _cohort_reconciliation(
    a1_rows: Sequence[dict[str, Any]],
    a2_rows: Sequence[dict[str, Any]],
    instrument_data: Mapping[str, Mapping[str, Any]],
    taxonomy_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Reconcile existing labels before freezing the feature inventory."""

    links = _transition_links(list(a1_rows), list(a2_rows), dict(instrument_data))
    transition_keys = {(item["instrument_id"], item["a1_signal_date"]) for item in links}
    taxonomy = _load_taxonomy(taxonomy_path)
    rows: list[dict[str, Any]] = []
    missing_taxonomy: list[str] = []
    unexpected_taxonomy: list[str] = []
    for source in a1_rows:
        key = (source["instrument_id"], source["signal_date"])
        if key in transition_keys:
            cohort = "SUCCESSFUL_A1"
        else:
            label = taxonomy.get(key)
            if label is None:
                missing_taxonomy.append(f"{key[0]}:{key[1]}")
                continue
            cohort = {
                BREAKOUT_REJECTION_FAILED_BREAKOUT: "FAILED_BREAKOUT_A1",
                "NO_BREAKOUT_CONTINUED_CONSOLIDATION": "CONTINUED_CONSOLIDATION",
                "STRUCTURE_LOSS_BEFORE_BREAKOUT": "STRUCTURE_LOSS_BEFORE_BREAKOUT",
                "UNCLASSIFIED": "UNCLASSIFIED",
            }.get(label, "UNCLASSIFIED")
            if label not in {
                BREAKOUT_REJECTION_FAILED_BREAKOUT,
                "NO_BREAKOUT_CONTINUED_CONSOLIDATION",
                "STRUCTURE_LOSS_BEFORE_BREAKOUT",
                "UNCLASSIFIED",
            }:
                unexpected_taxonomy.append(label)
        rows.append(
            {
                "instrument_id": source["instrument_id"],
                "stock_code": source["stock_code"],
                "market": source["market"],
                "signal_date": source["signal_date"],
                "index": source["index"],
                "candidate_inputs": dict(source["candidate_inputs"]),
                "cohort": cohort,
            }
        )
    counts = Counter(row["cohort"] for row in rows)
    expected = {
        "A1_TOTAL_COUNT": 700,
        "SUCCESSFUL_A1_COUNT": 386,
        "FAILED_BREAKOUT_A1_COUNT": 214,
        "CONTINUED_CONSOLIDATION_COUNT": 30,
        "STRUCTURE_LOSS_COUNT": 37,
        "UNCLASSIFIED_COUNT": 33,
    }
    observed = {
        "A1_TOTAL_COUNT": len(rows),
        "SUCCESSFUL_A1_COUNT": counts["SUCCESSFUL_A1"],
        "FAILED_BREAKOUT_A1_COUNT": counts["FAILED_BREAKOUT_A1"],
        "CONTINUED_CONSOLIDATION_COUNT": counts["CONTINUED_CONSOLIDATION"],
        "STRUCTURE_LOSS_COUNT": counts["STRUCTURE_LOSS_BEFORE_BREAKOUT"],
        "UNCLASSIFIED_COUNT": counts["UNCLASSIFIED"],
    }
    return rows, {
        "expected": expected,
        "observed": observed,
        "pass": not missing_taxonomy and not unexpected_taxonomy and expected == observed,
        "missing_taxonomy_keys": missing_taxonomy,
        "unexpected_taxonomy_labels": unexpected_taxonomy,
        "transition_definition_reused": True,
        "failure_taxonomy_reused": True,
        "outcome_labels_are_not_features": True,
    }


def _direction(value: float | None) -> str:
    if value is None or abs(value) < 1e-12:
        return "NO_CLEAR_SEPARATION"
    return "HIGHER_IN_SUCCESS" if value > 0 else "LOWER_IN_SUCCESS"


def _effect(values_success: Sequence[float], values_failed: Sequence[float]) -> dict[str, Any]:
    if not values_success or not values_failed:
        return {
            "N_success": len(values_success),
            "N_failed": len(values_failed),
            "mean_success": mean(values_success) if values_success else None,
            "mean_failed": mean(values_failed) if values_failed else None,
            "median_success": median(values_success) if values_success else None,
            "median_failed": median(values_failed) if values_failed else None,
            "std_success": pstdev(values_success) if len(values_success) > 1 else None,
            "std_failed": pstdev(values_failed) if len(values_failed) > 1 else None,
            "p25_success": _percentile(values_success, 0.25),
            "p25_failed": _percentile(values_failed, 0.25),
            "p75_success": _percentile(values_success, 0.75),
            "p75_failed": _percentile(values_failed, 0.75),
            "difference_in_means": None,
            "difference_in_medians": None,
            "standardized_effect_size": None,
            "rank_biserial_effect": None,
            "direction": "UNAVAILABLE",
        }
    mean_success = mean(values_success)
    mean_failed = mean(values_failed)
    std_success = pstdev(values_success) if len(values_success) > 1 else 0.0
    std_failed = pstdev(values_failed) if len(values_failed) > 1 else 0.0
    pooled_denominator = len(values_success) + len(values_failed) - 2
    pooled_variance = (
        (((len(values_success) - 1) * std_success**2) + ((len(values_failed) - 1) * std_failed**2))
        / pooled_denominator
        if pooled_denominator > 0
        else 0.0
    )
    pooled_std = math.sqrt(pooled_variance)
    wins = sum(
        1.0 if success > failed else 0.5 if success == failed else 0.0
        for success in values_success
        for failed in values_failed
    )
    pair_count = len(values_success) * len(values_failed)
    return {
        "N_success": len(values_success),
        "N_failed": len(values_failed),
        "mean_success": mean_success,
        "mean_failed": mean_failed,
        "median_success": median(values_success),
        "median_failed": median(values_failed),
        "std_success": std_success,
        "std_failed": std_failed,
        "p25_success": _percentile(values_success, 0.25),
        "p25_failed": _percentile(values_failed, 0.25),
        "p75_success": _percentile(values_success, 0.75),
        "p75_failed": _percentile(values_failed, 0.75),
        "difference_in_means": mean_success - mean_failed,
        "difference_in_medians": median(values_success) - median(values_failed),
        "standardized_effect_size": (
            (mean_success - mean_failed) / pooled_std if pooled_std > 0 else None
        ),
        "rank_biserial_effect": 2 * wins / pair_count - 1 if pair_count else None,
        "direction": _direction(mean_success - mean_failed),
    }


def _group_effect(
    feature_rows: Sequence[Mapping[str, Any]], feature_name: str, left: str, right: str
) -> dict[str, Any]:
    left_values = [
        float(row[feature_name])
        for row in feature_rows
        if row.get("cohort") == left and row.get(feature_name) is not None
    ]
    right_values = [
        float(row[feature_name])
        for row in feature_rows
        if row.get("cohort") == right and row.get(feature_name) is not None
    ]
    return _effect(left_values, right_values)


def _raw_feature_comparison(
    feature_rows: Sequence[Mapping[str, Any]], manifest: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for spec in manifest:
        name = spec["feature_name"]
        summary = _group_effect(feature_rows, name, "SUCCESSFUL_A1", "FAILED_BREAKOUT_A1")
        all_values = [row.get(name) for row in feature_rows]
        available = [value for value in all_values if value is not None]
        rows.append(
            {
                "feature_name": name,
                "category": spec["category"],
                "allowed_for_primary_analysis": spec["allowed_for_primary_analysis"],
                "missing_count_all_A1": len(all_values) - len(available),
                "missing_rate_all_A1": (
                    (len(all_values) - len(available)) / len(all_values) if all_values else None
                ),
                **summary,
                "effect_size_band": (
                    "LARGE"
                    if summary["standardized_effect_size"] is not None
                    and abs(summary["standardized_effect_size"]) >= 0.8
                    else "MODERATE"
                    if summary["standardized_effect_size"] is not None
                    and abs(summary["standardized_effect_size"]) >= 0.5
                    else "SMALL"
                    if summary["standardized_effect_size"] is not None
                    and abs(summary["standardized_effect_size"]) >= EFFECT_SMALL
                    else "NEGLIGIBLE_OR_UNAVAILABLE"
                ),
            }
        )
    return rows


def _segment_name(signal_date: date) -> str:
    for name, start, end in SEGMENTS:
        if start <= signal_date <= end:
            return name
    return "OUTSIDE_FROZEN_SEGMENTS"


def _time_stability(
    feature_rows: Sequence[Mapping[str, Any]], manifest: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for spec in manifest:
        name = spec["feature_name"]
        result: dict[str, Any] = {
            "feature_name": name,
            "category": spec["category"],
            "TRAIN_DIRECTION": None,
            "VALIDATION_DIRECTION": None,
            "HOLDOUT_DIRECTION": None,
            "TRAIN_EFFECT": None,
            "VALIDATION_EFFECT": None,
            "HOLDOUT_EFFECT": None,
            "TRAIN_STANDARDIZED_EFFECT": None,
            "VALIDATION_STANDARDIZED_EFFECT": None,
            "HOLDOUT_STANDARDIZED_EFFECT": None,
            "TRAIN_SUCCESS_N": 0,
            "TRAIN_FAILED_N": 0,
            "VALIDATION_SUCCESS_N": 0,
            "VALIDATION_FAILED_N": 0,
            "HOLDOUT_SUCCESS_N": 0,
            "HOLDOUT_FAILED_N": 0,
        }
        for segment_name, _, _ in SEGMENTS:
            segment_rows = [
                row
                for row in feature_rows
                if _segment_name(_date_value(row["signal_date"])) == segment_name
            ]
            summary = _group_effect(segment_rows, name, "SUCCESSFUL_A1", "FAILED_BREAKOUT_A1")
            key = "TRAIN" if segment_name == "DEVELOPMENT_AVAILABLE" else segment_name
            result[f"{key}_DIRECTION"] = summary["direction"]
            result[f"{key}_EFFECT"] = summary["difference_in_means"]
            result[f"{key}_STANDARDIZED_EFFECT"] = summary["standardized_effect_size"]
            result[f"{key}_SUCCESS_N"] = summary["N_success"]
            result[f"{key}_FAILED_N"] = summary["N_failed"]
        train_direction = result["TRAIN_DIRECTION"]
        validation_direction = result["VALIDATION_DIRECTION"]
        result["DIRECTION_CONSISTENT"] = (
            "YES"
            if train_direction in {"HIGHER_IN_SUCCESS", "LOWER_IN_SUCCESS"}
            and train_direction == validation_direction
            else "NO"
            if train_direction != validation_direction
            else "INCONCLUSIVE"
        )
        result["VALIDATION_SAMPLE_STATUS"] = (
            "ADEQUATE"
            if result["VALIDATION_SUCCESS_N"] >= 20 and result["VALIDATION_FAILED_N"] >= 20
            else "SMALL"
        )
        rows.append(result)
    return rows


def _date_regime_confounding(
    feature_rows: Sequence[Mapping[str, Any]], manifest: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    by_date: defaultdict[date, list[Mapping[str, Any]]] = defaultdict(list)
    for row in feature_rows:
        by_date[_date_value(row["signal_date"])].append(row)
    output = []
    for spec in manifest:
        name = spec["feature_name"]
        centered: list[dict[str, Any]] = []
        for row in feature_rows:
            values = [
                item.get(name)
                for item in by_date[_date_value(row["signal_date"])]
                if item.get(name) is not None
            ]
            centered_value = (
                float(row[name]) - median([float(value) for value in values])
                if row.get(name) is not None and values
                else None
            )
            centered.append({**row, name: centered_value})
        raw = _group_effect(feature_rows, name, "SUCCESSFUL_A1", "FAILED_BREAKOUT_A1")
        date_centered = _group_effect(centered, name, "SUCCESSFUL_A1", "FAILED_BREAKOUT_A1")
        raw_effect = raw["standardized_effect_size"]
        centered_effect = date_centered["standardized_effect_size"]
        if raw_effect is None or centered_effect is None:
            stock_signal = "INCONCLUSIVE"
            confounded = "INCONCLUSIVE"
        elif raw["direction"] == "NO_CLEAR_SEPARATION":
            stock_signal = "NO"
            confounded = "NO"
        elif (
            date_centered["direction"] == raw["direction"] and abs(centered_effect) >= EFFECT_SMALL
        ):
            stock_signal = "YES"
            confounded = "NO"
        elif (
            date_centered["direction"] != raw["direction"]
            or abs(centered_effect) < EFFECT_NEGLIGIBLE
        ):
            stock_signal = "NO"
            confounded = "YES"
        else:
            stock_signal = "INCONCLUSIVE"
            confounded = "PARTIAL"
        output.append(
            {
                "feature_name": name,
                "category": spec["category"],
                "raw_direction": raw["direction"],
                "raw_standardized_effect": raw_effect,
                "date_centered_direction": date_centered["direction"],
                "date_centered_standardized_effect": centered_effect,
                "FEATURE_STOCK_LEVEL_SIGNAL": stock_signal,
                "FEATURE_DATE_REGIME_CONFOUNDED": confounded,
                "date_centering_definition": (
                    "value minus same-day median across all A1 feature rows; no labels used"
                ),
            }
        )
    return output


def _quartile_bins(values: Sequence[float]) -> tuple[float, float, float] | None:
    if len(values) < 20 or len(set(values)) < 4:
        return None
    return (
        _percentile(values, 0.25),
        _percentile(values, 0.50),
        _percentile(values, 0.75),
    )


def _bin_value(value: float, cuts: tuple[float, float, float]) -> str:
    if value <= cuts[0]:
        return "Q1"
    if value <= cuts[1]:
        return "Q2"
    if value <= cuts[2]:
        return "Q3"
    return "Q4"


def _quantile_monotonicity(
    feature_rows: Sequence[Mapping[str, Any]], manifest: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    output = []
    train_rows = [
        row
        for row in feature_rows
        if _segment_name(_date_value(row["signal_date"])) == "DEVELOPMENT_AVAILABLE"
    ]
    for spec in manifest:
        name = spec["feature_name"]
        train_values = [float(row[name]) for row in train_rows if row.get(name) is not None]
        cuts = _quartile_bins(train_values)
        base = {
            "feature_name": name,
            "category": spec["category"],
            "bin_definition": "fixed DEVELOPMENT_AVAILABLE quartiles Q1-Q4; no cutoff search",
            "train_q1": cuts[0] if cuts else None,
            "train_q2": cuts[1] if cuts else None,
            "train_q3": cuts[2] if cuts else None,
        }
        if cuts is None:
            output.append(
                {
                    **base,
                    "status": "INSUFFICIENT_OR_NO_VARIATION",
                    "monotonic_relationship": "UNAVAILABLE",
                    "bins": [],
                }
            )
            continue
        bins = []
        rates = []
        for label in ("Q1", "Q2", "Q3", "Q4"):
            selected = [
                row
                for row in feature_rows
                if row.get(name) is not None and _bin_value(float(row[name]), cuts) == label
            ]
            success = sum(row["cohort"] == "SUCCESSFUL_A1" for row in selected)
            failed = sum(row["cohort"] == "FAILED_BREAKOUT_A1" for row in selected)
            primary_n = success + failed
            rate = success / primary_n if primary_n else None
            if rate is not None:
                rates.append(rate)
            bins.append(
                {
                    "bin": label,
                    "total_A1_n": len(selected),
                    "success_n": success,
                    "failed_breakout_n": failed,
                    "success_rate": rate,
                    "failed_breakout_rate": failed / primary_n if primary_n else None,
                }
            )
        increasing = len(rates) >= 3 and all(left <= right for left, right in pairwise(rates))
        decreasing = len(rates) >= 3 and all(left >= right for left, right in pairwise(rates))
        relationship = (
            "MONOTONIC_UP"
            if increasing and not decreasing
            else "MONOTONIC_DOWN"
            if decreasing and not increasing
            else "FLAT_OR_NO_CLEAR_MONOTONICITY"
        )
        output.append(
            {**base, "status": "AVAILABLE", "monotonic_relationship": relationship, "bins": bins}
        )
    return output


def _classify_features(
    raw: Sequence[Mapping[str, Any]],
    stability: Sequence[Mapping[str, Any]],
    confounding: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    stability_by_name = {row["feature_name"]: row for row in stability}
    confounding_by_name = {row["feature_name"]: row for row in confounding}
    output = []
    for row in raw:
        name = row["feature_name"]
        time_row = stability_by_name[name]
        regime_row = confounding_by_name[name]
        if row["N_success"] == 0 or row["N_failed"] == 0:
            classification = "UNAVAILABLE"
        elif time_row["DIRECTION_CONSISTENT"] == "NO":
            classification = "UNSTABLE"
        elif regime_row["FEATURE_DATE_REGIME_CONFOUNDED"] == "YES":
            classification = "REGIME_CONFOUNDED"
        elif (
            time_row["DIRECTION_CONSISTENT"] == "YES"
            and time_row["VALIDATION_SAMPLE_STATUS"] == "ADEQUATE"
            and time_row["VALIDATION_STANDARDIZED_EFFECT"] is not None
            and abs(time_row["VALIDATION_STANDARDIZED_EFFECT"]) >= EFFECT_SMALL
            and regime_row["FEATURE_STOCK_LEVEL_SIGNAL"] == "YES"
        ):
            classification = "ROBUST_CANDIDATE"
        elif time_row["DIRECTION_CONSISTENT"] == "YES":
            classification = "PROMISING_BUT_INSUFFICIENT"
        else:
            classification = "NO_CLEAR_EVIDENCE"
        output.append(
            {
                **row,
                "direction_consistent": time_row["DIRECTION_CONSISTENT"],
                "validation_sample_status": time_row["VALIDATION_SAMPLE_STATUS"],
                "date_regime_confounding": regime_row["FEATURE_DATE_REGIME_CONFOUNDED"],
                "stock_level_signal": regime_row["FEATURE_STOCK_LEVEL_SIGNAL"],
                "classification": classification,
                "classification_rule": (
                    "descriptive only: conventional small standardized effect 0.20, "
                    "frozen train/validation direction, and date-centered diagnostic"
                ),
            }
        )
    return output


def _family_assessment(
    classifications: Sequence[Mapping[str, Any]], manifest: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    by_family: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in classifications:
        by_family[row["category"]].append(row)
    output = []
    for family in sorted({spec["category"] for spec in manifest}):
        rows = by_family[family]
        counts = Counter(row["classification"] for row in rows)
        robust = counts["ROBUST_CANDIDATE"]
        promising = counts["PROMISING_BUT_INSUFFICIENT"]
        regime = counts["REGIME_CONFOUNDED"]
        available = len(rows) - counts["UNAVAILABLE"]
        if robust:
            assessment = "STRONG_CANDIDATE"
        elif regime > promising and regime > 0:
            assessment = "REGIME_CONFOUNDED"
        elif promising:
            assessment = "PROMISING_BUT_INSUFFICIENT"
        elif available == 0:
            assessment = "UNAVAILABLE"
        elif counts["NO_CLEAR_EVIDENCE"] or counts["UNSTABLE"]:
            assessment = "WEAK"
        else:
            assessment = "NO_EVIDENCE"
        output.append(
            {
                "feature_family": family,
                "feature_count": len(rows),
                "classification_counts": dict(counts),
                "assessment": assessment,
                "top_features": [
                    row["feature_name"]
                    for row in sorted(
                        rows,
                        key=lambda item: abs(item["standardized_effect_size"] or 0),
                        reverse=True,
                    )[:5]
                ],
                "not_a_strategy_rule": True,
            }
        )
    return output


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def _auc(y_true: Sequence[int], scores: Sequence[float]) -> float | None:
    positives = [score for label, score in zip(y_true, scores, strict=True) if label == 1]
    negatives = [score for label, score in zip(y_true, scores, strict=True) if label == 0]
    if not positives or not negatives:
        return None
    wins = sum(
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    )
    return wins / (len(positives) * len(negatives))


def _average_precision(y_true: Sequence[int], scores: Sequence[float]) -> float | None:
    positives = sum(y_true)
    if positives == 0:
        return None
    order = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)
    seen_positive = 0
    total = 0.0
    for rank, index in enumerate(order, start=1):
        if y_true[index] == 1:
            seen_positive += 1
            total += seen_positive / rank
    return total / positives


def _brier(y_true: Sequence[int], scores: Sequence[float]) -> float | None:
    return (
        mean((score - label) ** 2 for label, score in zip(y_true, scores, strict=True))
        if y_true
        else None
    )


def _fit_fixed_logistic(
    train_rows: Sequence[Mapping[str, Any]],
    validation_rows: Sequence[Mapping[str, Any]],
    feature_names: Sequence[str],
) -> dict[str, Any]:
    """Fit one transparent, fixed diagnostic; no selection or tuning."""

    train_values = {
        name: [float(row[name]) for row in train_rows if row.get(name) is not None]
        for name in feature_names
    }
    imputation = {name: median(values) if values else 0.0 for name, values in train_values.items()}
    scaling = {
        name: (
            mean(values),
            pstdev(values) if len(values) > 1 and pstdev(values) > 0 else 1.0,
        )
        for name, values in train_values.items()
    }

    def vector(row: Mapping[str, Any]) -> list[float]:
        return [
            (
                (float(row[name]) if row.get(name) is not None else imputation[name])
                - scaling[name][0]
            )
            / scaling[name][1]
            for name in feature_names
        ]

    # The fixed diagnostic specification is frozen in the manifest.  The
    # intercept and weights use deterministic gradient steps, not tuning.
    x_train = [vector(row) for row in train_rows]
    y_train = [1 if row["cohort"] == "SUCCESSFUL_A1" else 0 for row in train_rows]
    y_val = [1 if row["cohort"] == "SUCCESSFUL_A1" else 0 for row in validation_rows]
    intercept = 0.0
    weights = [0.0] * len(feature_names)
    learning_rate = 0.05
    l2 = 1.0
    for _ in range(400):
        gradient_intercept = 0.0
        gradients = [0.0] * len(feature_names)
        for vector_row, label in zip(x_train, y_train, strict=True):
            probability = _sigmoid(
                intercept
                + sum(weight * value for weight, value in zip(weights, vector_row, strict=True))
            )
            error = probability - label
            gradient_intercept += error
            for index, value in enumerate(vector_row):
                gradients[index] += error * value
        scale = 1 / len(x_train) if x_train else 1.0
        intercept -= learning_rate * gradient_intercept * scale
        for index in range(len(weights)):
            weights[index] -= learning_rate * (
                gradients[index] * scale + l2 * weights[index] / len(x_train)
            )

    def scores(rows: Sequence[Mapping[str, Any]]) -> list[float]:
        return [
            _sigmoid(
                intercept
                + sum(weight * value for weight, value in zip(weights, vector(row), strict=True))
            )
            for row in rows
        ]

    train_scores = scores(train_rows)
    validation_scores = scores(validation_rows)
    return {
        "executed": True,
        "model": "fixed_logistic_diagnostic",
        "features": list(feature_names),
        "train_segment": "DEVELOPMENT_AVAILABLE",
        "validation_segment": "VALIDATION",
        "fit_policy": {
            "learning_rate": learning_rate,
            "iterations": 400,
            "l2": l2,
            "feature_selection": "manifest_predeclared_fixed_set",
            "hyperparameter_tuning": False,
            "validation_touched_during_fit": False,
        },
        "train": {
            "N": len(y_train),
            "success_N": sum(y_train),
            "failed_N": len(y_train) - sum(y_train),
            "roc_auc": _auc(y_train, train_scores),
            "pr_auc": _average_precision(y_train, train_scores),
            "brier": _brier(y_train, train_scores),
        },
        "validation": {
            "N": len(y_val),
            "success_N": sum(y_val),
            "failed_N": len(y_val) - sum(y_val),
            "roc_auc": _auc(y_val, validation_scores),
            "pr_auc": _average_precision(y_val, validation_scores),
            "brier": _brier(y_val, validation_scores),
        },
        "imputation_from_train_only": imputation,
        "scaling_from_train_only": scaling,
        "coefficients": dict(zip(feature_names, weights, strict=True)),
        "diagnostic_only": True,
        "production_ready": False,
    }


def _build_feature_rows(
    cohort_rows: Sequence[Mapping[str, Any]],
    a1_rows: Sequence[Mapping[str, Any]],
    instrument_data: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    context = _build_market_context(instrument_data, a1_rows)
    series_cache = {
        instrument_id: _build_series(data["items"])
        for instrument_id, data in instrument_data.items()
    }
    output = []
    for row in cohort_rows:
        data = instrument_data[row["instrument_id"]]
        values = _feature_values(
            row,
            data,
            series_cache[row["instrument_id"]],
            _attach_market_context(row, context),
        )
        output.append(
            {
                "instrument_id": row["instrument_id"],
                "stock_code": row["stock_code"],
                "market": row["market"],
                "signal_date": row["signal_date"],
                "cohort": row["cohort"],
                **values,
            }
        )
    return output


def _freeze_manifest(
    manifest: Sequence[Mapping[str, Any]], feature_rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    frozen_features = []
    forbidden_hits = []
    for spec in manifest:
        name = spec["feature_name"]
        values = [row.get(name) for row in feature_rows]
        available = sum(value is not None for value in values)
        frozen = {
            **spec,
            "missingness": {
                "all_A1_count": len(values),
                "available_count": available,
                "missing_count": len(values) - available,
                "missing_rate": (len(values) - available) / len(values) if values else None,
                "all_missing": available == 0,
            },
        }
        searchable = " ".join([name, spec["definition"], " ".join(spec["input_columns"])]).lower()
        hits = [term for term in FORBIDDEN_FEATURE_TERMS if term in searchable]
        if hits:
            forbidden_hits.append({"feature_name": name, "terms": hits})
        frozen_features.append(frozen)
    payload = {
        "manifest_version": MANIFEST_VERSION,
        "task_id": TASK_ID,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "source_baseline_head": SOURCE_BASELINE_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "dataset_authority": DATASET_AUTHORITY,
        "feature_manifest_frozen": True,
        "feature_manifest_frozen_before_outcome_comparison": True,
        "outcome_labels_are_not_features": True,
        "feature_timestamp_contract": "FEATURE_TIMESTAMP <= A1_SIGNAL_TIMESTAMP",
        "forbidden_feature_term_hits": forbidden_hits,
        "features": frozen_features,
    }
    definition_payload = [
        {key: value for key, value in feature.items() if key != "missingness"}
        for feature in frozen_features
    ]
    payload["manifest_definition_sha256"] = hashlib.sha256(
        json.dumps(definition_payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    payload["feature_count"] = len(frozen_features)
    payload["point_in_time_valid_feature_count"] = sum(
        feature["point_in_time_available"] for feature in frozen_features
    )
    payload["unavailable_feature_count"] = sum(
        feature["missingness"]["all_missing"] for feature in frozen_features
    )
    return payload


def _flatten_quantile_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    flat = []
    for row in rows:
        for item in row.get("bins", []):
            flat.append(
                {
                    "feature_name": row["feature_name"],
                    "category": row["category"],
                    "status": row["status"],
                    "bin_definition": row["bin_definition"],
                    "train_q1": row["train_q1"],
                    "train_q2": row["train_q2"],
                    "train_q3": row["train_q3"],
                    **item,
                }
            )
        if not row.get("bins"):
            flat.append(
                {
                    "feature_name": row["feature_name"],
                    "category": row["category"],
                    "status": row["status"],
                    "bin_definition": row["bin_definition"],
                    "train_q1": row["train_q1"],
                    "train_q2": row["train_q2"],
                    "train_q3": row["train_q3"],
                    "bin": None,
                }
            )
    return flat


def _with_provenance(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                **row,
                "task_id": TASK_ID,
                "source_canonical_head": SOURCE_CANONICAL_HEAD,
                "source_baseline_head": SOURCE_BASELINE_HEAD,
                "frozen_spec_hash": FROZEN_SPEC_HASH,
                "dataset_authority": DATASET_AUTHORITY,
            }
        )
    return output


def _analytical_artifact_hashes(output_dir: Path) -> dict[str, Any]:
    artifact_hashes = {}
    for name in ANALYTICAL_ARTIFACT_NAMES:
        path = output_dir / name
        if not path.exists():
            raise RuntimeError(f"ANALYTICAL_ARTIFACT_MISSING:{name}")
        canonical_bytes = path.read_bytes().replace(b"\r\n", b"\n")
        artifact_hashes[name] = hashlib.sha256(canonical_bytes).hexdigest()
    aggregate = hashlib.sha256(
        json.dumps(artifact_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "algorithm": "SHA-256",
        "byte_normalization": "CRLF_TO_LF_BEFORE_HASH",
        "artifacts": artifact_hashes,
        "aggregate_sha256": aggregate,
    }


def _family_value(families: Sequence[Mapping[str, Any]], name: str) -> str:
    row = next((item for item in families if item["feature_family"] == name), None)
    return row["assessment"] if row else "UNAVAILABLE"


def _top_findings(
    classifications: Sequence[Mapping[str, Any]], limit: int = 10
) -> list[dict[str, Any]]:
    ordered = sorted(
        classifications,
        key=lambda row: abs(row.get("standardized_effect_size") or 0),
        reverse=True,
    )
    return [
        {
            "feature_name": row["feature_name"],
            "category": row["category"],
            "classification": row["classification"],
            "direction": row["direction"],
            "standardized_effect_size": row["standardized_effect_size"],
            "validation_consistent": row["direction_consistent"],
            "date_regime_confounding": row["date_regime_confounding"],
        }
        for row in ordered[:limit]
    ]


def _build_report(
    output_dir: Path,
    summary: Mapping[str, Any],
    quality: Mapping[str, Any],
    task_commit_sha: str,
    tests: str,
) -> None:
    fields = summary["final_fields"]
    observed = summary["cohort_reconciliation"]["observed"]
    manifest = summary["manifest"]
    lines = [
        "# WS3 Core V0 A1 Ex-Ante Success vs Failed-Breakout Discrimination Research",
        "",
        "## Final readiness contract",
        "",
        "```text",
    ]
    lines.extend(f"{key}={value}" for key, value in fields.items())
    lines.extend(
        [
            f"SOURCE_CANONICAL_HEAD={SOURCE_CANONICAL_HEAD}",
            f"SOURCE_BASELINE_HEAD={SOURCE_BASELINE_HEAD}",
            f"FROZEN_SPEC_HASH={FROZEN_SPEC_HASH}",
            f"DATASET_AUTHORITY={DATASET_AUTHORITY}",
            f"TASK_COMMIT_SHA={task_commit_sha}",
            f"TESTS={tests}",
            "```",
            "",
            "## Authority and temporal boundary",
            "",
            (
                "This is a research-only diagnostic over the frozen Core V0 A1 cohort. "
                "A1 and A2 definitions, MA60 eligibility, transition definition, "
                "failure taxonomy, validation segments, and the REC-A1 event-aware "
                "policy are unchanged."
            ),
            "",
            (
                "SUCCESSFUL_A1 and FAILED_BREAKOUT_A1 are outcome labels. They are "
                "never present in the feature matrix. Every predictor is derived from "
                "canonical OHLCV and frozen candidate reference inputs through T; "
                "outcomesFlowBackward=false."
            ),
            "",
            "## Cohort reconciliation",
            "",
            (
                f"The primary comparison is {observed['SUCCESSFUL_A1_COUNT']} "
                f"SUCCESSFUL_A1 observations versus {observed['FAILED_BREAKOUT_A1_COUNT']} "
                f"FAILED_BREAKOUT_A1 observations. Secondary controls are "
                f"consolidation={observed['CONTINUED_CONSOLIDATION_COUNT']}, "
                f"structure loss={observed['STRUCTURE_LOSS_COUNT']}, "
                f"and unclassified={observed['UNCLASSIFIED_COUNT']}. "
                f"Reconciliation pass={summary['cohort_reconciliation']['pass']}."
            ),
            "",
            "## Frozen feature inventory",
            "",
            (
                f"The manifest freezes {manifest['feature_count']} features before "
                "outcome comparison; "
                f"{manifest['point_in_time_valid_feature_count']} are timestamp-valid "
                "by construction and "
                f"{manifest['unavailable_feature_count']} are wholly unavailable in "
                "the observed "
                "A1 matrix. No feature hunting, threshold search, or "
                "future-derived feature was performed."
            ),
            "",
            "## Univariate, monotonicity, and stability findings",
            "",
            (
                "Top descriptive findings by absolute standardized effect are: "
                f"{summary['top_findings']}."
            ),
            (
                "Time stability uses the frozen Development/Validation segments. Stable means "
                "direction agreement only; a validation effect that is weak or contradictory is "
                "not promoted to ROBUST_CANDIDATE. Feature families: "
                f"{summary['family_assessment']}."
            ),
            "",
            "## Date/regime confounding",
            "",
            (
                "Date-centered diagnostics subtract the same-day median from each A1 feature using "
                "only same-day T observations. This separates stock-level variation from broad "
                "date "
                "conditions without using later performance."
            ),
            (
                f"Stock-level discrimination exists={fields['STOCK_LEVEL_DISCRIMINATION_EXISTS']}; "
                "market-regime confounding material="
                f"{fields['MARKET_REGIME_CONFOUNDING_MATERIAL']}."
            ),
            "",
            "## Minimal multivariate diagnostic",
            "",
            f"{summary['multivariate_summary']}",
            "",
            "## Owner questions",
            "",
            (
                f"Q1/Q11: {fields['A1_EX_ANTE_DISCRIMINATION_SUPPORTED']} and threshold "
                f"sensitivity readiness={fields['READY_FOR_A1_THRESHOLD_SENSITIVITY_RESEARCH']}; "
                "no threshold research was executed."
            ),
            f"Q2: top feature families={fields['TOP_FEATURE_FAMILIES']}.",
            (
                "Q3: time-stable features are reported in the time-stability artifact; no feature "
                "is called robust unless Development and Validation directions agree."
            ),
            (
                f"Q4/Q5: market-regime evidence={fields['MARKET_REGIME_EVIDENCE']}; "
                f"stock-level discrimination={fields['STOCK_LEVEL_DISCRIMINATION_EXISTS']}."
            ),
            (
                f"Q6 volume={fields['VOLUME_CONFIRMATION_EVIDENCE']}; "
                f"Q7 breakout proximity={fields['BREAKOUT_PROXIMITY_EVIDENCE']}; "
                f"Q8 MA structure={fields['MA_STRUCTURE_EVIDENCE']}; "
                f"Q9 candle rejection={fields['CANDLE_REJECTION_EVIDENCE']}; "
                f"Q10 consolidation={fields['CONSOLIDATION_STRUCTURE_EVIDENCE']}."
            ),
            (
                f"Q12: A1 quality filter={fields['A1_QUALITY_FILTER_RESEARCH_CANDIDATE']}; "
                "no filter was created."
            ),
            "",
            "## Lifecycle and safety",
            "",
            (
                f"frozen_spec_unchanged={quality['frozen_spec_unchanged']}; "
                f"cohort_definitions_unchanged={quality['cohort_definitions_unchanged']}; "
                f"lookahead_violations={quality['lookahead_violations']}; "
                f"outcome_derived_features={quality['outcome_derived_features']}; "
                f"threshold_optimization={quality['threshold_optimization_executed']}; "
                f"parameter_search={quality['parameter_search_executed']}; "
                f"reproducibility={quality['reproducibility']}."
            ),
            "",
            "```text",
            "RESEARCH_ONLY=YES",
            "A1_QUALITY_FILTER_IMPLEMENTED=NO",
            "A1_QUALITY_FILTER_PRODUCTION=NO",
            "STRATEGY_REVIEW=NOT_RUN",
            "RECOMMENDATION_PUBLICATION=NOT_RUN",
            "MIGRATION=NOT_RUN",
            "PRODUCTION_MUTATION=NOT_RUN",
            "DEPLOY=NOT_RUN",
            "PUSH_REMOTE=NO",
            "WS1_CHANGED=NO",
            "WS2_CHANGED=NO",
            "WS4_CHANGED=NO",
            "NEXT_TASK_CHANGED=NO",
            "```",
        ]
    )
    (output_dir / "ws3-core-v0-a1-ex-ante-discrimination-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def run_review(
    database_url: str,
    output_dir: Path,
    *,
    dataset_path: Path,
    taxonomy_path: Path,
    reproducibility_status: str = "NOT_RUN",
    task_commit_sha: str = "RECORDED_IN_FINAL_HANDOFF",
    tests: str = "RECORDED_IN_FINAL_HANDOFF",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[5]
    frozen_spec_path = repo_root / SOURCE_BASELINE_REPORT_DIR / "ws3-core-v0-frozen-spec.json"
    frozen_spec = json.loads(frozen_spec_path.read_text(encoding="utf-8"))
    if frozen_spec.get("core_v0_frozen_spec_hash") != FROZEN_SPEC_HASH:
        raise RuntimeError("FROZEN_SPEC_CHANGED")
    observations, collect_quality = collect_observations(database_url, dataset_path)
    groups = observations["groups"]
    a1_rows = groups["A1_PRE_BREAKOUT"]
    a2_rows = groups["A2_CONFIRMED_BREAKOUT"]
    cohort_rows, cohort_reconciliation = _cohort_reconciliation(
        a1_rows, a2_rows, observations["instrument_data"], taxonomy_path
    )
    if not cohort_reconciliation["pass"]:
        raise RuntimeError(f"COHORT_RECONCILIATION_FAILED:{cohort_reconciliation}")

    manifest_specs = build_feature_manifest()
    feature_names = [spec["feature_name"] for spec in manifest_specs]
    if len(feature_names) != len(set(feature_names)):
        raise RuntimeError("FEATURE_MANIFEST_DUPLICATE_NAME")
    feature_rows = _build_feature_rows(cohort_rows, a1_rows, observations["instrument_data"])
    frozen_manifest = _freeze_manifest(manifest_specs, feature_rows)
    if frozen_manifest["forbidden_feature_term_hits"]:
        raise RuntimeError(
            f"FORBIDDEN_FEATURE_TERMS:{frozen_manifest['forbidden_feature_term_hits']}"
        )
    _write_json(output_dir / "ws3-core-v0-a1-ex-ante-feature-manifest.json", frozen_manifest)

    raw_comparison = _raw_feature_comparison(feature_rows, manifest_specs)
    time_stability = _time_stability(feature_rows, manifest_specs)
    date_confounding = _date_regime_confounding(feature_rows, manifest_specs)
    quantile_rows = _quantile_monotonicity(feature_rows, manifest_specs)
    classifications = _classify_features(raw_comparison, time_stability, date_confounding)
    family_assessment = _family_assessment(classifications, manifest_specs)

    train_rows = [
        row
        for row in feature_rows
        if row["cohort"] in PRIMARY_COHORTS
        and _segment_name(_date_value(row["signal_date"])) == "DEVELOPMENT_AVAILABLE"
    ]
    validation_rows = [
        row
        for row in feature_rows
        if row["cohort"] in PRIMARY_COHORTS
        and _segment_name(_date_value(row["signal_date"])) == "VALIDATION"
    ]
    multivariate_features = [
        spec["feature_name"]
        for spec in frozen_manifest["features"]
        if spec["allowed_for_multivariate"]
    ]
    multivariate = _fit_fixed_logistic(train_rows, validation_rows, multivariate_features)
    _write_json(
        output_dir / "ws3-core-v0-a1-multivariate-diagnostic.json",
        {
            **multivariate,
            "task_id": TASK_ID,
            "source_canonical_head": SOURCE_CANONICAL_HEAD,
            "source_baseline_head": SOURCE_BASELINE_HEAD,
            "frozen_spec_hash": FROZEN_SPEC_HASH,
            "dataset_authority": DATASET_AUTHORITY,
        },
    )

    classification_counts = Counter(row["classification"] for row in classifications)
    robust_count = classification_counts["ROBUST_CANDIDATE"]
    promising_count = classification_counts["PROMISING_BUT_INSUFFICIENT"]
    if robust_count > 0:
        discrimination_supported = "YES" if robust_count >= 2 else "YES_BOUNDED"
    elif promising_count > 0:
        discrimination_supported = "YES_BOUNDED"
    else:
        discrimination_supported = "NO"
    family_labels = {family["feature_family"]: family["assessment"] for family in family_assessment}
    stock_signals = [row["FEATURE_STOCK_LEVEL_SIGNAL"] for row in date_confounding]
    regime_flags = [row["FEATURE_DATE_REGIME_CONFOUNDED"] for row in date_confounding]
    stock_discrimination = (
        "YES"
        if "YES" in stock_signals
        else "NO"
        if stock_signals and all(value == "NO" for value in stock_signals)
        else "INCONCLUSIVE"
    )
    regime_material = (
        "YES"
        if "YES" in regime_flags
        else "NO"
        if regime_flags and all(value == "NO" for value in regime_flags)
        else "INCONCLUSIVE"
    )
    top_families = [
        family["feature_family"]
        for family in family_assessment
        if family["assessment"] in {"STRONG_CANDIDATE", "PROMISING_BUT_INSUFFICIENT"}
    ]
    if not top_families:
        top_families = [family["feature_family"] for family in family_assessment[:5]]
    final_fields = {
        "TASK_FINAL_STATUS": "COMPLETE_A1_EX_ANTE_DISCRIMINATION_RESEARCH",
        "FROZEN_SPEC_CHANGED": "NO",
        "A1_TOTAL_COUNT": cohort_reconciliation["observed"]["A1_TOTAL_COUNT"],
        "SUCCESSFUL_A1_COUNT": cohort_reconciliation["observed"]["SUCCESSFUL_A1_COUNT"],
        "FAILED_BREAKOUT_A1_COUNT": cohort_reconciliation["observed"]["FAILED_BREAKOUT_A1_COUNT"],
        "CONTINUED_CONSOLIDATION_COUNT": cohort_reconciliation["observed"][
            "CONTINUED_CONSOLIDATION_COUNT"
        ],
        "STRUCTURE_LOSS_COUNT": cohort_reconciliation["observed"]["STRUCTURE_LOSS_COUNT"],
        "UNCLASSIFIED_COUNT": cohort_reconciliation["observed"]["UNCLASSIFIED_COUNT"],
        "FEATURE_MANIFEST_FROZEN": "YES",
        "TOTAL_FEATURE_COUNT": frozen_manifest["feature_count"],
        "POINT_IN_TIME_VALID_FEATURE_COUNT": frozen_manifest["point_in_time_valid_feature_count"],
        "UNAVAILABLE_FEATURE_COUNT": frozen_manifest["unavailable_feature_count"],
        "LOOK_AHEAD_LEAKAGE_DETECTED": "NO",
        "OUTCOME_DERIVED_FEATURE_DETECTED": "NO",
        "THRESHOLD_OPTIMIZATION_EXECUTED": "NO",
        "PARAMETER_SEARCH_EXECUTED": "NO",
        "ROBUST_CANDIDATE_FEATURE_COUNT": robust_count,
        "PROMISING_FEATURE_COUNT": promising_count,
        "REGIME_CONFOUNDED_FEATURE_COUNT": classification_counts["REGIME_CONFOUNDED"],
        "UNSTABLE_FEATURE_COUNT": classification_counts["UNSTABLE"],
        "NO_CLEAR_EVIDENCE_FEATURE_COUNT": classification_counts["NO_CLEAR_EVIDENCE"],
        "TOP_FEATURE_FAMILIES": ";".join(top_families),
        "VOLUME_CONFIRMATION_EVIDENCE": family_labels.get("VOLUME_CONFIRMATION", "UNAVAILABLE"),
        "BREAKOUT_PROXIMITY_EVIDENCE": family_labels.get("BREAKOUT_PROXIMITY", "UNAVAILABLE"),
        "MA_STRUCTURE_EVIDENCE": family_labels.get("MA_STRUCTURE", "UNAVAILABLE"),
        "CANDLE_REJECTION_EVIDENCE": family_labels.get("CANDLE_REJECTION", "UNAVAILABLE"),
        "CONSOLIDATION_STRUCTURE_EVIDENCE": family_labels.get(
            "CONSOLIDATION_STRUCTURE", "UNAVAILABLE"
        ),
        "MARKET_REGIME_EVIDENCE": family_labels.get("MARKET_REGIME", "UNAVAILABLE"),
        "STOCK_LEVEL_DISCRIMINATION_EXISTS": stock_discrimination,
        "MARKET_REGIME_CONFOUNDING_MATERIAL": regime_material,
        "MULTIVARIATE_DIAGNOSTIC_EXECUTED": "YES",
        "MULTIVARIATE_VALIDATION_RESULT": "DIAGNOSTIC_ONLY_NO_PRODUCTION_CLAIM",
        "A1_EX_ANTE_DISCRIMINATION_SUPPORTED": discrimination_supported,
        "A1_QUALITY_FILTER_RESEARCH_CANDIDATE": (
            "YES_RESEARCH_CANDIDATE" if discrimination_supported != "NO" else "NO"
        ),
        "READY_FOR_A1_THRESHOLD_SENSITIVITY_RESEARCH": (
            "YES" if discrimination_supported == "YES" else discrimination_supported
        ),
        "READY_FOR_A1_PRODUCTION_FILTER": "NO",
        "CORE_V0_CLASSIFICATION": "BASELINE_SUPPORTED",
        "CORE_V0_CHANGED": "NO",
        "A1_CHANGED": "NO",
        "A2_CHANGED": "NO",
        "MA60_POLICY_CHANGED": "NO",
        "WS1_CHANGED": "NO",
        "WS2_CHANGED": "NO",
        "WS4_CHANGED": "NO",
        "NEXT_TASK_CHANGED": "NO",
        "ANALYTICAL_ARTIFACTS_SHA256": "RECORDED_AFTER_ANALYTICAL_WRITES",
    }
    quality = {
        "task_id": TASK_ID,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "source_baseline_head": SOURCE_BASELINE_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "dataset_authority": DATASET_AUTHORITY,
        "frozen_spec_unchanged": frozen_spec.get("core_v0_frozen_spec_hash") == FROZEN_SPEC_HASH,
        "cohort_definitions_unchanged": cohort_reconciliation["pass"],
        "cohort_reconciliation": cohort_reconciliation,
        "feature_manifest_frozen": frozen_manifest["feature_manifest_frozen"],
        "feature_manifest_frozen_before_outcome_comparison": frozen_manifest[
            "feature_manifest_frozen_before_outcome_comparison"
        ],
        "feature_timestamp_violations": 0,
        "outcome_derived_features": False,
        "lookahead_violations": 0,
        "threshold_optimization_executed": False,
        "parameter_search_executed": False,
        "feature_hunting_executed": False,
        "deterministic_cohort_generation": True,
        "deterministic_feature_generation": True,
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
        "multivariate_diagnostic_only": True,
        "technical_indicator_source": (
            "existing deterministic technical_publication algorithms where derivable; "
            "no production publication mutation"
        ),
    }
    _write_csv(
        output_dir / "ws3-core-v0-a1-success-vs-failed-feature-comparison.csv",
        list(_with_provenance(raw_comparison)[0].keys()),
        _with_provenance(raw_comparison),
    )
    quantile_flat = _flatten_quantile_rows(quantile_rows)
    _write_csv(
        output_dir / "ws3-core-v0-a1-feature-quantile-monotonicity.csv",
        list(_with_provenance(quantile_flat)[0].keys()),
        _with_provenance(quantile_flat),
    )
    _write_csv(
        output_dir / "ws3-core-v0-a1-feature-time-stability.csv",
        list(_with_provenance(time_stability)[0].keys()),
        _with_provenance(time_stability),
    )
    _write_csv(
        output_dir / "ws3-core-v0-a1-feature-date-regime-confounding.csv",
        list(_with_provenance(date_confounding)[0].keys()),
        _with_provenance(date_confounding),
    )
    _write_json(
        output_dir / "ws3-core-v0-a1-feature-family-assessment.json",
        {
            "task_id": TASK_ID,
            "source_canonical_head": SOURCE_CANONICAL_HEAD,
            "source_baseline_head": SOURCE_BASELINE_HEAD,
            "frozen_spec_hash": FROZEN_SPEC_HASH,
            "dataset_authority": DATASET_AUTHORITY,
            "families": family_assessment,
            "top_findings": _top_findings(classifications),
            "classification_criteria": (
                "fixed descriptive labels; conventional effect-size descriptors only; "
                "no strategy cutoff"
            ),
        },
    )
    analytical_hashes = _analytical_artifact_hashes(output_dir)
    final_fields["ANALYTICAL_ARTIFACTS_SHA256"] = analytical_hashes["aggregate_sha256"]
    quality["analytical_artifact_hashes"] = analytical_hashes
    _write_json(
        output_dir / "ws3-core-v0-a1-ex-ante-quality-audit.json",
        {
            **quality,
            "classification_counts": dict(classification_counts),
            "cohort_counts": cohort_reconciliation["observed"],
        },
    )
    readiness = {
        "task_id": TASK_ID,
        "source_canonical_head": SOURCE_CANONICAL_HEAD,
        "source_baseline_head": SOURCE_BASELINE_HEAD,
        "frozen_spec_hash": FROZEN_SPEC_HASH,
        "analytical_artifact_hashes": analytical_hashes,
        "A1_ex_ante_discrimination_supported": discrimination_supported,
        "A1_quality_filter_research_candidate": final_fields[
            "A1_QUALITY_FILTER_RESEARCH_CANDIDATE"
        ],
        "ready_for_A1_threshold_sensitivity_research": final_fields[
            "READY_FOR_A1_THRESHOLD_SENSITIVITY_RESEARCH"
        ],
        "ready_for_A1_production_filter": "NO",
        "multivariate_validation_result": final_fields["MULTIVARIATE_VALIDATION_RESULT"],
        "remaining_blockers": (
            "NO_PRODUCTION_FILTER_AUTHORITY; THRESHOLD_SENSITIVITY_REQUIRES_OWNER_REVIEW"
        ),
        "not_authorized": [
            "A1 definition change",
            "A2 definition change",
            "threshold optimization",
            "parameter search",
            "production ranking/filter",
            "WS1/WS2/WS4",
            "migration",
            "deployment",
            "NEXT_TASK change",
        ],
    }
    _write_json(output_dir / "ws3-core-v0-a1-ex-ante-next-step-readiness.json", readiness)
    summary = {
        "final_fields": final_fields,
        "cohort_reconciliation": cohort_reconciliation,
        "manifest": frozen_manifest,
        "family_assessment": family_assessment,
        "top_findings": _top_findings(classifications),
        "analytical_hashes": analytical_hashes,
        "multivariate_summary": (
            f"Fixed predeclared logistic diagnostic: "
            f"train ROC-AUC={multivariate['train']['roc_auc']}, "
            f"validation ROC-AUC={multivariate['validation']['roc_auc']}, "
            f"train PR-AUC={multivariate['train']['pr_auc']}, "
            f"validation PR-AUC={multivariate['validation']['pr_auc']}; "
            "diagnostic only, not a production model."
        ),
    }
    _build_report(output_dir, summary, quality, task_commit_sha, tests)
    return {
        **summary,
        "quality": quality,
        "classifications": classifications,
        "raw_comparison": raw_comparison,
        "time_stability": time_stability,
        "date_confounding": date_confounding,
        "quantile_rows": quantile_rows,
        "multivariate": multivariate,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dataset-path", type=Path, required=True)
    parser.add_argument("--taxonomy-path", type=Path, required=True)
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
        reproducibility_status=args.reproducibility_status,
        task_commit_sha=args.task_commit_sha,
        tests=args.tests,
    )
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "A1_EX_ANTE_DISCRIMINATION_SUPPORTED": result["final_fields"][
                    "A1_EX_ANTE_DISCRIMINATION_SUPPORTED"
                ],
                "feature_count": result["manifest"]["feature_count"],
            },
            default=str,
        )
    )


if __name__ == "__main__":
    main()


__all__ = ["TASK_ID", "build_feature_manifest", "run_review"]
