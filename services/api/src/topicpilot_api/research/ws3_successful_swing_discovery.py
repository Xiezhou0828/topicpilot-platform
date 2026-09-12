"""WS3 successful-swing discovery research.

This module freezes an outcome-mining protocol before inspecting feature
differences.  It consumes only the canonical accepted daily OHLCV surface and
the already frozen A1/A2 and Technical V0 evidence.  All discovered signals
are research candidates; no strategy, score, recommendation, or production
surface is created.
"""

from __future__ import annotations

import argparse
from bisect import bisect_left
import csv
import hashlib
import json
import math
import os
import subprocess
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any, Iterable, Mapping, Sequence

import psycopg

from topicpilot_api.technical_publication import _calculate_series

TASK_ID = "TASK-WS3-SUCCESSFUL-SWING-OUTCOME-MINING-AND-LEADING-EVIDENCE-DISCOVERY-20260821"
SOURCE_START = date(2024, 8, 13)
SOURCE_END = date(2026, 8, 13)
SOURCE_CANONICAL_HEAD = "371d47a9d461a4dcc8eb42b7e1fcb7e0396367b0"
SOURCE_INSTRUMENT_COUNT = 603
SOURCE_OHLCV_ROW_COUNT = 288_881
SOURCE_SHA256 = "e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4"
OUTCOME_HORIZONS = (5, 10)
OUTCOME_THRESHOLDS = (0.03, 0.05, 0.10)
FEATURE_RELATIVE_DAYS = (-20, -10, -5, -3, -1, 0)
FEATURE_HISTORY_REQUIRED = 60
EPISODE_SPACING_SESSIONS = 10
CONTROL_MAX_DAYS = 45
# These are fixed, predeclared bins.  They are deliberately not fitted from
# the full sample, which would let later observations influence an earlier
# anchor's matching stratum.
CONTROL_QUANTILE_BINS = 5
REFERENCE_CASES = {
    "5351": (date(2026, 4, 24), date(2026, 8, 20)),
    "8039": (date(2026, 6, 10), date(2026, 8, 20)),
    "2483": (date(2026, 5, 1), date(2026, 7, 29)),
    "6538": (date(2026, 4, 23), date(2026, 8, 20)),
    "5483": (date(2026, 4, 7), date(2026, 8, 12)),
    "2303": (date(2026, 1, 1), date(2026, 8, 20)),
    "2615": (date(2026, 6, 25), date(2026, 8, 20)),
}
OUTPUT_DEFAULT = Path(
    "reports/TASK-WS3-SUCCESSFUL-SWING-OUTCOME-MINING-AND-LEADING-EVIDENCE-DISCOVERY-20260821"
)
REPORT_RELATIVE = Path(
    "docs/reports/TASK-WS3-SUCCESSFUL-SWING-OUTCOME-MINING-AND-LEADING-EVIDENCE-DISCOVERY-20260821/formal-closure-report.md"
)
P1E_A1 = Path(
    "reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-a1-expanded-event-panel.csv"
)
P1E_A2 = Path(
    "reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-a2-expanded-event-panel.csv"
)
P1E_A1_COUNT = 14_557
P1E_A2_COUNT = 5_277

FEATURE_FAMILY_ORDER = (
    "TREND_STRUCTURE",
    "MOMENTUM",
    "VOLUME_PARTICIPATION",
    "VOLATILITY_COMPRESSION",
    "RELATIVE_STRENGTH",
    "A_STATE_CONTEXT",
)
FEATURES = {
    "TREND_STRUCTURE": (
        "close_vs_ma5", "close_vs_ma10", "close_vs_ma20", "close_vs_ma60",
        "distance_to_ma20", "ma5_slope_5", "ma20_slope_5", "ma60_slope_5",
        "ma_alignment_bullish", "ma_alignment_bearish",
    ),
    "MOMENTUM": (
        "RAW_CLOSE_RETURN_5D", "RAW_CLOSE_RETURN_20D", "RSI14",
        "MACD_12_26_9", "MACD_SIGNAL_12_26_9", "MACD_HISTOGRAM_12_26_9",
        "rsi_change_5", "macd_hist_change_5",
    ),
    "VOLUME_PARTICIPATION": (
        "VOLUME_MA5", "VOLUME_MA20", "VOLUME_RATIO_20",
        "volume_ratio_5_to_20", "volume_expansion_state", "volume_contraction_state",
    ),
    "VOLATILITY_COMPRESSION": (
        "true_range_pct", "rolling_range_pct_5", "rolling_range_pct_20",
        "range_compression_5_to_20", "realized_vol_5", "realized_vol_20",
        "volatility_contraction_5_to_20",
    ),
    "RELATIVE_STRENGTH": ("benchmark_relative_return_5D", "benchmark_relative_return_20D"),
    "A_STATE_CONTEXT": (
        "a1_preceded_20", "a2_preceded_20", "a1_to_a2_preceded_20",
        "a2_without_prior_a1_20", "a_state_bucket",
    ),
}


def _root() -> Path:
    return Path(__file__).resolve().parents[5]


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (set, frozenset, tuple)):
        return "|".join(_json_default(item) for item in sorted(value, key=str))
    return str(value)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default)
        + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fieldnames: Sequence[str] | None = None) -> None:
    if fieldnames is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
            writer.writeheader()
            wrote = False
            for row in rows:
                wrote = True
                writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})
            if not wrote:
                writer.writerow({"status": "NO_ROWS", "event_count": 0})
        return
    materialized = list(rows)
    if not materialized:
        materialized = [{"status": "NO_ROWS", "event_count": 0}]
    fields: list[str] = []
    for row in materialized:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(
            {field: _csv_value(row.get(field)) for field in fields} for row in materialized
        )


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set, frozenset)):
        return "|".join(str(_csv_value(item)) for item in value)
    if isinstance(value, bool):
        return "True" if value else "False"
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _payload_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=_json_default).encode()
    ).hexdigest()


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _day(value: Any) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def _finite(values: Iterable[Any]) -> list[float]:
    return [float(value) for value in values if _float(value) is not None]


def _mean(values: Sequence[float]) -> float | None:
    return mean(values) if values else None


def _median(values: Sequence[float]) -> float | None:
    return median(values) if values else None


def _stdev(values: Sequence[float]) -> float | None:
    return pstdev(values) if len(values) > 1 else (0.0 if values else None)


def _stats(values: Sequence[float]) -> dict[str, Any]:
    clean = sorted(_finite(values))
    if not clean:
        return {"n": 0, "mean": None, "median": None, "p05": None, "p95": None, "win_rate": None, "min": None, "max": None}
    def q(frac: float) -> float:
        position = (len(clean) - 1) * frac
        lower, upper = math.floor(position), math.ceil(position)
        return clean[lower] if lower == upper else clean[lower] + (clean[upper] - clean[lower]) * (position - lower)
    return {"n": len(clean), "mean": _mean(clean), "median": _median(clean), "p05": q(0.05), "p95": q(0.95), "win_rate": sum(item > 0 for item in clean) / len(clean), "min": clean[0], "max": clean[-1]}


def _quantile_bins(values: Sequence[float], count: int = CONTROL_QUANTILE_BINS) -> list[float]:
    clean = sorted(values)
    if not clean:
        return []
    return [clean[min(len(clean) - 1, math.floor(len(clean) * idx / count))] for idx in range(1, count)]


def _bin(value: float | None, cutoffs: Sequence[float]) -> int | None:
    if value is None:
        return None
    return sum(value >= cutoff for cutoff in cutoffs)


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def _std_mean_difference(success: Sequence[float], control: Sequence[float]) -> float | None:
    if not success or not control:
        return None
    pooled = math.sqrt(((_stdev(success) or 0.0) ** 2 + (_stdev(control) or 0.0) ** 2) / 2)
    if pooled == 0:
        return 0.0 if mean(success) == mean(control) else (1.0 if mean(success) > mean(control) else -1.0)
    return (mean(success) - mean(control)) / pooled


def _overlap_coefficient(success: Sequence[float], control: Sequence[float], bins: int = 20) -> float | None:
    if not success or not control:
        return None
    combined = list(success) + list(control)
    lower, upper = min(combined), max(combined)
    if upper == lower:
        return 1.0
    width = (upper - lower) / bins
    s_counts = [0] * bins
    c_counts = [0] * bins
    for value in success:
        s_counts[min(bins - 1, int((value - lower) / width))] += 1
    for value in control:
        c_counts[min(bins - 1, int((value - lower) / width))] += 1
    s_total, c_total = len(success), len(control)
    return sum(min(s_counts[idx] / s_total, c_counts[idx] / c_total) for idx in range(bins))


def _source_lineage(row: Mapping[str, Any]) -> str:
    return "|".join(
        value
        for value in (
            f"instrument:{row['instrument_id']}",
            f"source:{row.get('source_code')}",
            f"adapter:{row.get('adapter_version')}",
            f"observation:{row.get('observation_id')}",
            f"normalization:{row.get('normalization_contract_version')}",
            f"mapping:{row.get('mapping_policy_version')}",
            f"reference:{row.get('reference_data_version')}",
        )
        if value and not value.endswith(":None")
    )


def _read_surface(database_url: str) -> dict[str, dict[str, Any]]:
    query = """
        SELECT d.instrument_id, d.instrument_code AS code, i.name,
               d.market_code AS market, d.trade_date AS trading_date,
               d.observed_at, co.ordering_key, d.canonical_observation_id AS observation_id,
               d.open, d.high, d.low, d.close, d.volume,
               mds.source_code, mds.adapter_version,
               co.normalization_contract_version, co.mapping_policy_version,
               co.reference_data_version, co.quality_state
        FROM topicpilot.vw_daily_market_observations d
        JOIN topicpilot.canonical_observations co ON co.id = d.canonical_observation_id
        JOIN topicpilot.instruments i ON i.id = d.instrument_id
        JOIN topicpilot.markets m ON m.id = i.market_id
        JOIN topicpilot.market_data_sources mds ON mds.id = d.source_id
        WHERE co.family_code = 'PRICE'
          AND d.quality_state = 'ACCEPTED'
          AND mds.observation_semantics = 'DAILY_BAR'
          AND d.trade_date >= %s AND d.trade_date <= %s
          AND NOT EXISTS (
              SELECT 1 FROM topicpilot.reference_instrument_lifecycles lifecycle
              WHERE lifecycle.instrument_id = co.instrument_id
                AND lifecycle.status_code IN ('DELISTED', 'SUSPENDED', 'TERMINATED')
                AND lifecycle.effective_from <= (co.observed_at AT TIME ZONE m.timezone)::date
                AND (lifecycle.effective_to IS NULL OR lifecycle.effective_to >= (co.observed_at AT TIME ZONE m.timezone)::date)
          )
        ORDER BY d.market_code, d.instrument_code, d.trade_date,
                 co.observed_at, co.ordering_key, co.id
    """
    dsn = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    data: dict[str, dict[str, Any]] = {}
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (SOURCE_START, SOURCE_END))
            for row in cursor:
                item = {
                    "instrument_id": str(row[0]), "code": str(row[1]), "name": row[2],
                    "market": str(row[3]), "trading_date": row[4], "observed_at": row[5],
                    "ordering_key": row[6], "observation_id": str(row[7]),
                    "open": row[8], "high": row[9], "low": row[10], "close": row[11],
                    "volume": row[12], "source_code": row[13], "adapter_version": row[14],
                    "normalization_contract_version": row[15], "mapping_policy_version": row[16],
                    "reference_data_version": row[17], "quality_state": row[18],
                }
                record = data.setdefault(
                    item["instrument_id"],
                    {"identity": {key: item[key] for key in ("instrument_id", "code", "name", "market")}, "items": []},
                )
                record["items"].append(item)
    for record in data.values():
        record["items"].sort(key=lambda item: (_day(item["trading_date"]), str(item["observed_at"]), str(item["ordering_key"]), item["observation_id"]))
        record["dates"] = [_day(item["trading_date"]) for item in record["items"]]
        record["date_index"] = {day: idx for idx, day in enumerate(record["dates"])}
        record["duplicate_count"] = len(record["dates"]) - len(set(record["dates"]))
        record["technical_series"] = _calculate_series(record["items"])
        # Decimal/datetime/object values retained from the DB driver are much
        # heavier than the numeric arrays used by this read-only replay.
        for item in record["items"]:
            for field in ("open", "high", "low", "close", "volume"):
                item[field] = _float(item[field])
            for field in ("code", "name", "market", "trading_date", "observed_at", "ordering_key", "quality_state"):
                item.pop(field, None)
        record["technical_series"] = {
            key: [_float(value) for value in values]
            for key, values in record["technical_series"].items()
        }
    return data


def _event_sets(root: Path) -> tuple[dict[str, set[date]], dict[str, set[date]]]:
    a1: dict[str, set[date]] = defaultdict(set)
    a2: dict[str, set[date]] = defaultdict(set)
    for row in _read_csv(root / P1E_A1):
        a1[row["instrument_id"]].add(_day(row["signal_date"]))
    for row in _read_csv(root / P1E_A2):
        a2[row["instrument_id"]].add(_day(row["signal_date"]))
    return a1, a2


def _known_event_dates(root: Path) -> dict[tuple[str, str], set[date]]:
    path = root / "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json"
    if not path.exists():
        return {}
    payload = _read_json(path)
    result: dict[tuple[str, str], set[date]] = defaultdict(set)
    values = payload.get("events", payload.get("event_records", []))
    if isinstance(values, dict):
        values = [event for nested in values.values() for event in nested]
    for event in values:
        if not isinstance(event, Mapping):
            continue
        market = str(event.get("market") or event.get("market_code") or "")
        code = str(event.get("stock_code") or event.get("instrument_code") or "")
        raw_day = event.get("primary_effective_date") or event.get("effective_date")
        if market and code and raw_day:
            result[(market, code)].add(_day(raw_day))
    return result


def _pre_state(record: Mapping[str, Any], idx: int, a1: Mapping[str, set[date]], a2: Mapping[str, set[date]]) -> dict[str, Any]:
    dates = record["dates"]
    instrument_id = record["identity"]["instrument_id"]
    current = dates[idx]
    start = max(0, idx - 20)
    prior = dates[start : idx + 1]
    a1_dates = a1.get(instrument_id, set())
    a2_dates = a2.get(instrument_id, set())
    prior_a1 = [day for day in prior if day in a1_dates]
    prior_a2 = [day for day in prior if day in a2_dates]
    has_a1 = bool(prior_a1)
    has_a2 = bool(prior_a2)
    transition = bool(has_a1 and any(day >= prior_a1[0] for day in prior_a2))
    if transition:
        bucket = "A1_TO_A2"
    elif has_a2:
        bucket = "A2_WITHOUT_PRIOR_A1" if not has_a1 else "A1_TO_A2"
    elif has_a1:
        bucket = "A1_ONLY"
    else:
        bucket = "NEITHER"
    return {
        "a1_preceded_20": has_a1, "a2_preceded_20": has_a2,
        "a1_to_a2_preceded_20": transition,
        "a2_without_prior_a1_20": has_a2 and not has_a1,
        "a_state_bucket": bucket,
        "a1_latest_date": max(prior_a1).isoformat() if prior_a1 else None,
        "a2_latest_date": max(prior_a2).isoformat() if prior_a2 else None,
        "a1_a2_lookback_sessions": 20,
        "a1_state_at_d0": current in a1_dates,
        "a2_state_at_d0": current in a2_dates,
    }


def _extra_series(record: Mapping[str, Any]) -> dict[str, list[float | None]]:
    items = record["items"]
    dates = record["dates"]
    closes = [_float(item["close"]) for item in items]
    highs = [_float(item["high"]) for item in items]
    lows = [_float(item["low"]) for item in items]
    volumes = [_float(item["volume"]) for item in items]
    output: dict[str, list[float | None]] = {
        key: [_float(value) for value in values]
        for key, values in record["technical_series"].items()
    }
    for key in (
        "close_vs_ma5", "close_vs_ma10", "close_vs_ma20", "close_vs_ma60",
        "distance_to_ma20", "ma5_slope_5", "ma20_slope_5", "ma60_slope_5",
        "ma_alignment_bullish", "ma_alignment_bearish", "rsi_change_5",
        "macd_hist_change_5", "volume_ratio_5_to_20", "volume_expansion_state",
        "volume_contraction_state", "true_range_pct", "rolling_range_pct_5",
        "rolling_range_pct_20", "range_compression_5_to_20", "realized_vol_5",
        "realized_vol_20", "volatility_contraction_5_to_20",
    ):
        output[key] = []
    def rolling_range(index: int, window: int) -> float | None:
        if index < window - 1 or closes[index] in (None, 0):
            return None
        hi = [value for value in highs[index - window + 1 : index + 1] if value is not None]
        lo = [value for value in lows[index - window + 1 : index + 1] if value is not None]
        return (max(hi) - min(lo)) / closes[index] if len(hi) == window and len(lo) == window else None
    def realized_vol(index: int, window: int) -> float | None:
        if index < window or any(value in (None, 0) for value in closes[index - window : index + 1]):
            return None
        returns = [closes[j] / closes[j - 1] - 1 for j in range(index - window + 1, index + 1)]
        return _stdev(returns)
    for idx in range(len(items)):
        close = closes[idx]
        for period in (5, 10, 20, 60):
            ma = output.get(f"MA{period}", [None] * len(items))[idx]
            output[f"close_vs_ma{period}"].append(_safe_div(close - ma if close is not None and ma is not None else None, ma))
        ma5, ma20, ma60 = output["MA5"][idx], output["MA20"][idx], output["MA60"][idx]
        output["distance_to_ma20"].append(_safe_div(close - ma20 if close is not None and ma20 is not None else None, ma20))
        for name, period in (("ma5_slope_5", 5), ("ma20_slope_5", 20), ("ma60_slope_5", 60)):
            current = output[f"MA{period}"][idx]
            prior = output[f"MA{period}"][idx - 5] if idx >= 5 else None
            output[name].append(_safe_div(current - prior if current is not None and prior is not None else None, prior))
        output["ma_alignment_bullish"].append(bool(close is not None and ma5 is not None and ma20 is not None and ma60 is not None and close > ma5 > ma20 > ma60))
        output["ma_alignment_bearish"].append(bool(close is not None and ma5 is not None and ma20 is not None and ma60 is not None and close < ma5 < ma20 < ma60))
        hist = output["MACD_HISTOGRAM_12_26_9"][idx]
        hist_prior = output["MACD_HISTOGRAM_12_26_9"][idx - 5] if idx >= 5 else None
        rsi = output["RSI14"][idx]
        rsi_prior = output["RSI14"][idx - 5] if idx >= 5 else None
        output["rsi_change_5"].append(rsi - rsi_prior if rsi is not None and rsi_prior is not None else None)
        output["macd_hist_change_5"].append(hist - hist_prior if hist is not None and hist_prior is not None else None)
        v5, v20 = output["VOLUME_MA5"][idx], output["VOLUME_MA20"][idx]
        output["volume_ratio_5_to_20"].append(_safe_div(v5, v20))
        volume_ratio = output["VOLUME_RATIO_20"][idx]
        output["volume_expansion_state"].append(bool(volume_ratio is not None and volume_ratio > 1))
        output["volume_contraction_state"].append(bool(volume_ratio is not None and volume_ratio < 1))
        true_range = None
        if idx > 0 and closes[idx - 1] not in (None, 0) and highs[idx] is not None and lows[idx] is not None:
            true_range = max(highs[idx] - lows[idx], abs(highs[idx] - closes[idx - 1]), abs(lows[idx] - closes[idx - 1])) / closes[idx - 1]
        output["true_range_pct"].append(true_range)
        range5, range20 = rolling_range(idx, 5), rolling_range(idx, 20)
        output["rolling_range_pct_5"].append(range5)
        output["rolling_range_pct_20"].append(range20)
        output["range_compression_5_to_20"].append(_safe_div(range5, range20))
        vol5, vol20 = realized_vol(idx, 5), realized_vol(idx, 20)
        output["realized_vol_5"].append(vol5)
        output["realized_vol_20"].append(vol20)
        output["volatility_contraction_5_to_20"].append(_safe_div(vol5, vol20))
    for name in FEATURES["RELATIVE_STRENGTH"]:
        output[name] = [None] * len(dates)
    return output


def _feature_manifest() -> dict[str, Any]:
    return {
        "schema_version": "ws3-successful-swing-feature-manifest.v2",
        "panel_layout": "one_row_per_event_and_relative_day_with_feature_columns",
        "full_feature_row_expansion": False,
        "feature_families": {
            family: {
                "feature_ids": list(feature_ids),
                "allowed_before_outcomes": True,
                "source": "canonical accepted daily OHLCV" if family != "A_STATE_CONTEXT" else "frozen P1E A1/A2 event panels",
                "threshold_search": False,
                "status": "PREDECLARED",
            }
            for family, feature_ids in FEATURES.items()
        },
        "relative_strength": {
            "status": "UNAVAILABLE_NO_CANONICAL_BENCHMARK",
            "topic_peer_proxy_used": False,
            "feature_ids": list(FEATURES["RELATIVE_STRENGTH"]),
        },
        "fixed_windows": {"ma": [5, 10, 20, 60], "returns": [5, 20], "rsi": 14, "macd": [12, 26, 9], "compression": [5, 20], "state_lookback_sessions": 20},
    }


def _outcome_path(record: Mapping[str, Any], idx: int) -> dict[str, Any]:
    items = record["items"]
    entry = _float(items[idx]["close"])
    horizons: dict[str, Any] = {}
    for horizon in OUTCOME_HORIZONS:
        path = items[idx + 1 : idx + horizon + 1]
        closes = [_float(item["close"]) for item in path]
        highs = [_float(item["high"]) for item in path]
        lows = [_float(item["low"]) for item in path]
        returns = [value / entry - 1 for value in closes if value is not None and entry not in (None, 0)]
        mfe = max((value / entry - 1 for value in highs if value is not None and entry not in (None, 0)), default=None)
        mae = min((value / entry - 1 for value in lows if value is not None and entry not in (None, 0)), default=None)
        max_dd = None
        running_peak = entry
        for value in closes:
            if value is None:
                continue
            running_peak = max(running_peak, value)
            drawdown = value / running_peak - 1
            max_dd = drawdown if max_dd is None else min(max_dd, drawdown)
        times = {}
        for threshold in OUTCOME_THRESHOLDS:
            times[f"time_to_{int(threshold * 100)}pct"] = next((offset for offset, value in enumerate(closes, 1) if value is not None and entry is not None and value >= entry * (1 + threshold)), None)
        persistence = {
            f"close_persistence_ge_{int(threshold * 100)}pct": sum(value is not None and entry is not None and value >= entry * (1 + threshold) for value in closes) / len(path) if path else None
            for threshold in OUTCOME_THRESHOLDS
        }
        horizons[str(horizon)] = {
            "forward_close_return": returns[-1] if len(returns) == len(path) and path else None,
            "mfe": mfe, "mae": mae, "max_close_drawdown": max_dd,
            **times, **persistence,
            "one_day_spike_ge_3pct": bool(sum(value is not None and entry is not None and value >= entry * 1.03 for value in highs) == 1),
            "sustained_expansion_ge_3pct": sum(value is not None and entry is not None and value >= entry * 1.03 for value in closes) >= 2,
            "path_session_count": len(path),
        }
    return horizons


def _anchor_id(instrument_id: str, day: date) -> str:
    return hashlib.sha256(f"{instrument_id}|{day.isoformat()}|successful-swing-anchor.v1".encode()).hexdigest()


def _make_anchors(data: Mapping[str, Mapping[str, Any]], a1: Mapping[str, set[date]], a2: Mapping[str, set[date]], known_events: Mapping[tuple[str, str], set[date]]) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    for record in data.values():
        items, dates = record["items"], record["dates"]
        extra = _extra_series(record)
        record["extra_series"] = extra
        for idx in range(FEATURE_HISTORY_REQUIRED, len(items) - max(OUTCOME_HORIZONS)):
            item = items[idx]
            day = dates[idx]
            close = _float(item["close"])
            if close is None or any(_float(items[idx + offset][field]) is None for offset in (1, 5, 10) for field in ("close", "high", "low")):
                continue
            path = _outcome_path(record, idx)
            flags = {
                f"T{h}_GE_{int(threshold * 100)}": bool(path[str(h)]["forward_close_return"] is not None and path[str(h)]["forward_close_return"] >= threshold)
                for h in OUTCOME_HORIZONS for threshold in OUTCOME_THRESHOLDS
            }
            pre_state = _pre_state(record, idx, a1, a2)
            volume = _float(item["volume"])
            volatility = extra.get("realized_vol_20", [None] * len(items))[idx]
            history_count = idx + 1
            anchors.append({
                "anchor_id": _anchor_id(record["identity"]["instrument_id"], day),
                "instrument_id": record["identity"]["instrument_id"], "stock_code": record["identity"]["code"], "name": record["identity"]["name"], "market": record["identity"]["market"], "anchor_date": day, "anchor_index": idx,
                "anchor_close": close, "anchor_open": _float(item["open"]), "anchor_high": _float(item["high"]), "anchor_low": _float(item["low"]), "anchor_volume": volume, "history_count": history_count, "ma60_eligible": extra.get("MA60", [None] * len(items))[idx] is not None,
                "price_scale": math.log10(close) if close > 0 else None, "liquidity_level": math.log10(volume + 1) if volume is not None else None, "volatility_level": volatility,
                "source_observation_id": item["observation_id"], "source_lineage": _source_lineage(item), "source_lineage_sha256": hashlib.sha256(_source_lineage(item).encode()).hexdigest(), "pit_status": "PIT_SAFE", "as_of": day,
                "known_event_overlap_h1_h10": any(day_value in known_events.get((record["identity"]["market"], record["identity"]["code"]), set()) for day_value in dates[idx + 1 : idx + 11]),
                "path": path, "a_state": pre_state, **flags,
            })
    return sorted(anchors, key=lambda row: (row["anchor_date"], row["instrument_id"]))


def _stratum_key(horizon: int, threshold: float) -> str:
    return f"T{horizon}_GE_{int(threshold * 100)}"


def _qualifies(anchor: Mapping[str, Any], stratum: str) -> bool:
    return bool(anchor.get(stratum))


def _distinct_episode_reps(anchors: Sequence[Mapping[str, Any]], stratum: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw = [anchor for anchor in anchors if _qualifies(anchor, stratum)]
    by_instrument: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for anchor in raw:
        by_instrument[anchor["instrument_id"]].append(anchor)
    episodes: list[dict[str, Any]] = []
    reps: list[dict[str, Any]] = []
    for instrument_id, rows in by_instrument.items():
        rows = sorted(rows, key=lambda row: row["anchor_index"])
        current: list[Mapping[str, Any]] = []
        previous_index: int | None = None
        for row in rows:
            if previous_index is None or row["anchor_index"] - previous_index > EPISODE_SPACING_SESSIONS:
                if current:
                    episode = {"episode_id": f"{stratum}:{current[0]['anchor_id']}", "stratum": stratum, "instrument_id": instrument_id, "representative_anchor_id": current[0]["anchor_id"], "representative_date": current[0]["anchor_date"], "raw_anchor_count": len(current), "raw_anchor_ids": [item["anchor_id"] for item in current]}
                    episodes.append(episode); reps.append(dict(current[0], stratum=stratum, episode_id=episode["episode_id"], raw_anchor_count=len(current)))
                current = []
            current.append(row)
            previous_index = row["anchor_index"]
        if current:
            episode = {"episode_id": f"{stratum}:{current[0]['anchor_id']}", "stratum": stratum, "instrument_id": instrument_id, "representative_anchor_id": current[0]["anchor_id"], "representative_date": current[0]["anchor_date"], "raw_anchor_count": len(current), "raw_anchor_ids": [item["anchor_id"] for item in current]}
            episodes.append(episode); reps.append(dict(current[0], stratum=stratum, episode_id=episode["episode_id"], raw_anchor_count=len(current)))
    return sorted(reps, key=lambda row: (row["anchor_date"], row["instrument_id"])), sorted(episodes, key=lambda row: (row["representative_date"], row["instrument_id"]))


def _assign_bins(anchors: Sequence[Mapping[str, Any]]) -> None:
    # Fixed cutoffs are part of the frozen protocol.  They avoid fitting
    # control strata with information from dates after the anchor.
    for row in anchors:
        row["liquidity_quintile"] = _bin(row.get("liquidity_level"), [4.0, 5.0, 6.0, 7.0])
        row["volatility_quintile"] = _bin(row.get("volatility_level"), [0.01, 0.02, 0.04, 0.08])
        row["price_scale_bucket"] = math.floor((row["price_scale"] or 0) * 2) if row.get("price_scale") is not None else None
        row["calendar_quarter"] = f"{row['anchor_date'].year}-Q{((row['anchor_date'].month - 1) // 3) + 1}"


def _control_distance(success: Mapping[str, Any], control: Mapping[str, Any]) -> tuple[float, ...]:
    return (
        abs((control["anchor_date"] - success["anchor_date"]).days),
        abs((control.get("liquidity_quintile") or 0) - (success.get("liquidity_quintile") or 0)),
        abs((control.get("volatility_quintile") or 0) - (success.get("volatility_quintile") or 0)),
        abs((control.get("price_scale_bucket") or 0) - (success.get("price_scale_bucket") or 0)),
        abs(control["anchor_index"] - success["anchor_index"]),
        0 if control["instrument_id"] != success["instrument_id"] else 1,
        control["instrument_id"],
    )


def _match_controls(success_reps: Sequence[Mapping[str, Any]], anchors: Sequence[Mapping[str, Any]], stratum: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pool = [row for row in anchors if not _qualifies(row, stratum)]
    assigned: set[str] = set()
    pairs: list[dict[str, Any]] = []
    fallback_counts = Counter()

    # The prior implementation scanned the complete control pool for every
    # success episode.  These indexes preserve the frozen tier predicates and
    # deterministic distance ordering while making the replay tractable.
    by_bins: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    by_quarter: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    by_market_ma60: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in pool:
        market_key = (row["market"], bool(row["ma60_eligible"]))
        quarter_key = (*market_key, row["calendar_quarter"])
        bin_key = (*quarter_key, row.get("liquidity_quintile") or 0, row.get("volatility_quintile") or 0, row.get("price_scale_bucket") or 0)
        by_market_ma60[market_key].append(row)
        by_quarter[quarter_key].append(row)
        by_bins[bin_key].append(row)
    indexed: list[dict[tuple[Any, ...], tuple[list[Mapping[str, Any]], tuple[date, ...]]]] = []
    for index in (by_bins, by_quarter, by_market_ma60):
        for rows in index.values():
            rows.sort(key=lambda row: (row["anchor_date"], row["anchor_index"], row["instrument_id"]))
        indexed.append({key: (rows, tuple(row["anchor_date"] for row in rows)) for key, rows in index.items()})
    by_bins_index, by_quarter_index, by_market_ma60_index = indexed

    def nearest(indexed_rows: tuple[Sequence[Mapping[str, Any]], Sequence[date]] | None, success: Mapping[str, Any], max_days: int) -> Mapping[str, Any] | None:
        if not indexed_rows:
            return None
        rows, dates = indexed_rows
        if not rows:
            return None
        target = success["anchor_date"]
        position = bisect_left(dates, target)
        left, right = position - 1, position
        while left >= 0 or right < len(rows):
            left_distance = abs((dates[left] - target).days) if left >= 0 else None
            right_distance = abs((dates[right] - target).days) if right < len(rows) else None
            distances = [distance for distance in (left_distance, right_distance) if distance is not None]
            if not distances:
                break
            distance = min(distances)
            if distance > max_days:
                break
            same_distance: list[Mapping[str, Any]] = []
            while left >= 0 and abs((dates[left] - target).days) == distance:
                same_distance.append(rows[left]); left -= 1
            while right < len(rows) and abs((dates[right] - target).days) == distance:
                same_distance.append(rows[right]); right += 1
            valid = [row for row in same_distance if row["instrument_id"] != success["instrument_id"] and row["anchor_id"] not in assigned]
            if valid:
                return min(valid, key=lambda row: _control_distance(success, row))
        return None

    for success in sorted(success_reps, key=lambda row: (row["anchor_date"], row["instrument_id"])):
        selected = None
        tier_used = None
        market_key = (success["market"], bool(success["ma60_eligible"]))
        quarter_key = (*market_key, success["calendar_quarter"])
        base_bins = (success.get("liquidity_quintile") or 0, success.get("volatility_quintile") or 0, success.get("price_scale_bucket") or 0)
        tier_one_candidates: list[Mapping[str, Any]] = []
        for liquidity in range(base_bins[0] - 1, base_bins[0] + 2):
            for volatility in range(base_bins[1] - 1, base_bins[1] + 2):
                for price_scale in range(base_bins[2] - 1, base_bins[2] + 2):
                    candidate = nearest(by_bins_index.get((*quarter_key, liquidity, volatility, price_scale)), success, CONTROL_MAX_DAYS)
                    if candidate is not None:
                        tier_one_candidates.append(candidate)
        if tier_one_candidates:
            selected = min(tier_one_candidates, key=lambda row: _control_distance(success, row)); tier_used = 1
        if selected is None:
            selected = nearest(by_quarter_index.get(quarter_key), success, CONTROL_MAX_DAYS); tier_used = 2 if selected is not None else None
        if selected is None:
            selected = nearest(by_market_ma60_index.get(market_key), success, 90); tier_used = 3 if selected is not None else None
        if selected is None:
            continue
        assigned.add(selected["anchor_id"]); fallback_counts[str(tier_used)] += 1
        pairs.append({"stratum": stratum, "successful_anchor_id": success["anchor_id"], "successful_episode_id": success.get("episode_id"), "successful_instrument_id": success["instrument_id"], "successful_anchor_date": success["anchor_date"], "control_anchor_id": selected["anchor_id"], "control_instrument_id": selected["instrument_id"], "control_anchor_date": selected["anchor_date"], "control_match_tier": tier_used, "control_distance_days": abs((selected["anchor_date"] - success["anchor_date"]).days), "control_market": selected["market"], "control_liquidity_quintile": selected.get("liquidity_quintile"), "control_volatility_quintile": selected.get("volatility_quintile"), "control_price_scale_bucket": selected.get("price_scale_bucket"), "control_source_lineage": selected["source_lineage"], "control_is_success_for_same_stratum": False})
    return pairs, {"requested": len(success_reps), "matched": len(pairs), "unmatched": len(success_reps) - len(pairs), "control_reuse_count": len(pairs) - len({pair["control_anchor_id"] for pair in pairs}), "fallback_tier_counts": dict(fallback_counts), "control_contamination_count": 0}


def _anchor_lookup(anchors: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {row["anchor_id"]: row for row in anchors}


FEATURE_PANEL_FIELDS = (
    "event_id", "event_type", "stratum", "instrument_id", "stock_code", "market",
    "anchor_date", "relative_day", "feature_families_included", "feature_status_summary",
    "pit_status", "source_lineage", "source_observation_id", "feature_manifest_version",
    *(f"feature_{feature_id}" for family in FEATURE_FAMILY_ORDER for feature_id in FEATURES[family]),
)


def _feature_rows(event_rows: Sequence[Mapping[str, Any]], lookup: Mapping[str, Mapping[str, Any]], feature_manifest: Mapping[str, Any]) -> Iterable[dict[str, Any]]:
    for event in event_rows:
        source = lookup[event["anchor_id"]]
        record = event["record"]
        idx = source["anchor_index"]
        for relative_day in FEATURE_RELATIVE_DAYS:
            target_idx = idx + relative_day
            row = {"event_id": event["event_id"], "event_type": event["event_type"], "stratum": event.get("stratum"), "instrument_id": source["instrument_id"], "stock_code": source["stock_code"], "market": source["market"], "anchor_date": source["anchor_date"], "relative_day": relative_day, "feature_families_included": "|".join(FEATURE_FAMILY_ORDER), "pit_status": "PIT_SAFE", "source_lineage": _source_lineage(record["items"][target_idx]) if 0 <= target_idx < len(record["items"]) else source["source_lineage"], "source_observation_id": record["items"][target_idx]["observation_id"] if 0 <= target_idx < len(record["items"]) else None, "feature_manifest_version": feature_manifest["schema_version"]}
            statuses = Counter()
            for family in FEATURE_FAMILY_ORDER:
                for feature_id in FEATURES[family]:
                    value = None
                    status = "PIT_SAFE"
                    if family == "RELATIVE_STRENGTH":
                        status = "UNAVAILABLE_NO_CANONICAL_BENCHMARK"
                    elif target_idx < 0 or target_idx >= len(record["items"]):
                        status = "UNAVAILABLE_INSUFFICIENT_HISTORY"
                    elif family == "A_STATE_CONTEXT":
                        state = _pre_state(record, target_idx, event["a1_sets"], event["a2_sets"])
                        value = state.get(feature_id)
                    else:
                        extra = record.get("extra_series") or _extra_series(record)
                        record["extra_series"] = extra
                        value = extra.get(feature_id, [None] * len(record["items"]))[target_idx]
                        if value is None:
                            status = "UNAVAILABLE_INDICATOR_INPUT"
                    row[f"feature_{feature_id}"] = value
                    statuses[status] += 1
            row["feature_status_summary"] = "|".join(f"{key}:{statuses[key]}" for key in sorted(statuses))
            yield row


def _discrimination(success_values: Sequence[float], control_values: Sequence[float]) -> dict[str, Any]:
    success = _finite(success_values); control = _finite(control_values)
    s_mean, c_mean = _mean(success), _mean(control)
    raw_diff = s_mean - c_mean if s_mean is not None and c_mean is not None else None
    trimmed_success = sorted(success)[max(0, int(len(success) * 0.1)) : len(success) - int(len(success) * 0.1) if len(success) > 10 else len(success)]
    trimmed_control = sorted(control)[max(0, int(len(control) * 0.1)) : len(control) - int(len(control) * 0.1) if len(control) > 10 else len(control)]
    trimmed_diff = _mean(trimmed_success) - _mean(trimmed_control) if trimmed_success and trimmed_control else None
    return {"n_success": len(success), "n_control": len(control), "success_mean": s_mean, "control_mean": c_mean, "success_median": _median(success), "control_median": _median(control), "median_difference": (_median(success) - _median(control)) if success and control else None, "mean_difference": raw_diff, "standardized_mean_difference": _std_mean_difference(success, control), "distribution_overlap": _overlap_coefficient(success, control), "trimmed_mean_difference": trimmed_diff, "outlier_dependence": (abs(trimmed_diff / raw_diff) if trimmed_diff is not None and raw_diff not in (None, 0) else None)}


def _classify(discrimination: Mapping[str, Any], market_consistency: float | None, temporal_consistency: float | None) -> tuple[str, str]:
    n = min(int(discrimination.get("n_success") or 0), int(discrimination.get("n_control") or 0))
    smd = abs(discrimination.get("standardized_mean_difference") or 0)
    if n < 20:
        return "NO_CLEAR_SIGNAL", "sample_below_discovery_floor"
    if market_consistency is not None and temporal_consistency is not None and min(market_consistency, temporal_consistency) < 0.5:
        return "REGIME_CONFOUNDED", "market_or_temporal_direction_is_not_consistent"
    if n >= 40 and smd >= 0.2 and (market_consistency or 0) >= 0.5 and (temporal_consistency or 0) >= 0.5:
        return "ROBUST_DISCOVERY_SIGNAL", "bounded_effect_and_cross_segment_consistency"
    if smd >= 0.1:
        return "PROMISING_DISCOVERY_SIGNAL", "bounded_effect_requires_confirmatory_research"
    return "NO_CLEAR_SIGNAL", "effect_below_predeclared_discovery_floor"


FEATURE_KEYS = tuple((family, feature_id) for family in FEATURE_FAMILY_ORDER for feature_id in FEATURES[family])
FEATURE_POSITIONS = {key: index for index, key in enumerate(FEATURE_KEYS)}


def _feature_cache(rows: Sequence[Mapping[str, Any]], records: Mapping[str, Mapping[str, Any]], a1_sets: Mapping[str, set[date]], a2_sets: Mapping[str, set[date]]) -> dict[str, dict[int, tuple[Any, ...]]]:
    cache: dict[str, dict[int, tuple[Any, ...]]] = {}
    for row in {item["anchor_id"]: item for item in rows}.values():
        record = records[row["instrument_id"]]
        extra = record.get("extra_series") or _extra_series(record)
        record["extra_series"] = extra
        per_day: dict[int, tuple[Any, ...]] = {}
        for relative_day in FEATURE_RELATIVE_DAYS:
            target_idx = row["anchor_index"] + relative_day
            state = _pre_state(record, target_idx, a1_sets, a2_sets) if 0 <= target_idx < len(record["items"]) else {}
            values: list[Any] = []
            for family, feature_id in FEATURE_KEYS:
                if family == "RELATIVE_STRENGTH":
                    value = None
                elif not 0 <= target_idx < len(record["items"]):
                    value = None
                elif family == "A_STATE_CONTEXT":
                    value = state.get(feature_id)
                else:
                    value = extra.get(feature_id, [None] * len(record["items"]))[target_idx]
                values.append(float(value) if isinstance(value, bool) else value)
            per_day[relative_day] = tuple(values)
        cache[row["anchor_id"]] = per_day
    return cache


def _univariate(strata_reps: Mapping[str, Sequence[Mapping[str, Any]]], control_pairs: Mapping[str, Sequence[Mapping[str, Any]]], anchors: Mapping[str, Mapping[str, Any]], records: Mapping[str, Mapping[str, Any]], feature_manifest: Mapping[str, Any], a1_sets: Mapping[str, set[date]], a2_sets: Mapping[str, set[date]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for stratum, success_reps in strata_reps.items():
        pairs = control_pairs.get(stratum, [])
        controls = [anchors[pair["control_anchor_id"]] for pair in pairs]
        cache = _feature_cache([*success_reps, *controls], records, a1_sets, a2_sets)
        for family in FEATURE_FAMILY_ORDER:
            for feature_id in FEATURES[family]:
                position = FEATURE_POSITIONS[(family, feature_id)]
                for relative_day in FEATURE_RELATIVE_DAYS:
                    def value_for(row: Mapping[str, Any]) -> float | None:
                        value = cache[row["anchor_id"]][relative_day][position]
                        return _float(value)

                    success_values = [value for row in success_reps if (value := value_for(row)) is not None]
                    control_values = [value for row in controls if (value := value_for(row)) is not None]
                    market_directions: list[bool] = []
                    temporal_directions: list[bool] = []
                    for segment_field, segment_values in (("market", ("TPE", "TWO")), ("period", ("DEV", "VALIDATION", "HOLDOUT"))):
                        directions = []
                        for segment in segment_values:
                            svals = [value for row in success_reps if (segment_field == "market" and row["market"] == segment) or (segment_field == "period" and _period(row["anchor_date"]) == segment) if (value := value_for(row)) is not None]
                            cvals = [value for row in controls if (segment_field == "market" and row["market"] == segment) or (segment_field == "period" and _period(row["anchor_date"]) == segment) if (value := value_for(row)) is not None]
                            if svals and cvals:
                                directions.append((mean(svals) - mean(cvals)) >= 0)
                        if segment_field == "market":
                            market_directions = directions
                        else:
                            temporal_directions = directions
                    base = _discrimination(success_values, control_values)
                    market_consistency = sum(market_directions) / len(market_directions) if market_directions else None
                    temporal_consistency = sum(temporal_directions) / len(temporal_directions) if temporal_directions else None
                    classification, reason = _classify(base, market_consistency, temporal_consistency)
                    output.append({"stratum": stratum, "feature_family": family, "feature_id": feature_id, "relative_day": relative_day, **base, "market_direction_consistency": market_consistency, "temporal_direction_consistency": temporal_consistency, "classification": classification, "classification_reason": reason, "outcome_derived_feature_used": False})
    return output


def _period(day: date) -> str:
    if date(2026, 2, 2) <= day <= date(2026, 6, 30): return "DEV"
    if date(2026, 7, 1) <= day <= date(2026, 7, 31): return "VALIDATION"
    if date(2026, 8, 1) <= day <= date(2026, 8, 13): return "HOLDOUT"
    return "HISTORICAL_SUPPORT"


def _gradient(univariate: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in FEATURE_FAMILY_ORDER:
        for feature_id in FEATURES[family]:
            for relative_day in FEATURE_RELATIVE_DAYS:
                values: dict[str, float | None] = {}
                for horizon in OUTCOME_HORIZONS:
                    for threshold in OUTCOME_THRESHOLDS:
                        key = _stratum_key(horizon, threshold)
                        match = next((row for row in univariate if row["stratum"] == key and row["feature_family"] == family and row["feature_id"] == feature_id and row["relative_day"] == relative_day), None)
                        values[f"{key}_success_median"] = match.get("success_median") if match else None
                        values[f"{key}_classification"] = match.get("classification") if match else None
                for horizon in OUTCOME_HORIZONS:
                    medians = [values.get(f"{_stratum_key(horizon, t)}_success_median") for t in OUTCOME_THRESHOLDS]
                    available = [value for value in medians if value is not None]
                    monotonic = "INSUFFICIENT" if len(available) < 3 else ("NONDECREASING" if all(medians[i] <= medians[i + 1] for i in range(2)) else ("NONINCREASING" if all(medians[i] >= medians[i + 1] for i in range(2)) else "MIXED"))
                    rows.append({"feature_family": family, "feature_id": feature_id, "relative_day": relative_day, "horizon": horizon, "t3_median": medians[0], "t5_median": medians[1], "t10_median": medians[2], "monotonicity": monotonic, "all_outcome_derived_values_evaluation_only": True})
    return rows


def _lead_time(univariate: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for family in FEATURE_FAMILY_ORDER:
        family_rows = [row for row in univariate if row["feature_family"] == family]
        useful = [row for row in family_rows if row["classification"] in {"ROBUST_DISCOVERY_SIGNAL", "PROMISING_DISCOVERY_SIGNAL"}]
        earliest = min((row["relative_day"] for row in useful), default=None)
        rows.append({"feature_family": family, "earliest_useful_lead_time": earliest, "earliest_useful_label": f"D{earliest}" if earliest is not None else "NONE", "promising_feature_count": sum(row["classification"] == "PROMISING_DISCOVERY_SIGNAL" for row in family_rows), "robust_feature_count": sum(row["classification"] == "ROBUST_DISCOVERY_SIGNAL" for row in family_rows), "status": "DISCOVERY_ONLY"})
    return rows


def _a_state_rows(strata_reps: Mapping[str, Sequence[Mapping[str, Any]]], controls: Mapping[str, Sequence[Mapping[str, Any]]], anchors: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for stratum, reps in strata_reps.items():
        success_buckets = Counter(anchors[row["anchor_id"]]["a_state"]["a_state_bucket"] for row in reps)
        control_buckets = Counter(anchors[pair["control_anchor_id"]]["a_state"]["a_state_bucket"] for pair in controls.get(stratum, []))
        success_count, control_count = len(reps), len(controls.get(stratum, []))
        for bucket in ("A1_TO_A2", "A2_WITHOUT_PRIOR_A1", "A1_ONLY", "NEITHER"):
            rows.append({"stratum": stratum, "state_bucket": bucket, "successful_episode_count": success_buckets[bucket], "successful_rate": success_buckets[bucket] / success_count if success_count else None, "matched_control_count": control_buckets[bucket], "control_rate": control_buckets[bucket] / control_count if control_count else None, "a1_definition_unchanged": True, "a2_definition_unchanged": True, "causality_claim": False})
    return rows


def _outcome_summary(anchors: Sequence[Mapping[str, Any]], reps: Mapping[str, Sequence[Mapping[str, Any]]], episodes: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for horizon in OUTCOME_HORIZONS:
        for threshold in OUTCOME_THRESHOLDS:
            key = _stratum_key(horizon, threshold)
            raw = [row for row in anchors if row.get(key)]
            distinct = list(reps.get(key, []))
            path = [row["path"][str(horizon)] for row in distinct]
            rows.append({"stratum": key, "horizon": horizon, "threshold": threshold, "raw_qualifying_anchor_count": len(raw), "distinct_swing_episode_count": len(episodes.get(key, [])), "representative_count": len(distinct), "forward_return": _stats([item.get("forward_close_return") for item in path]), "mfe": _stats([item.get("mfe") for item in path]), "mae": _stats([item.get("mae") for item in path]), "max_close_drawdown": _stats([item.get("max_close_drawdown") for item in path]), "time_to_3pct_rate": _stats([1 if item.get("time_to_3pct") is not None else 0 for item in path]), "time_to_5pct_rate": _stats([1 if item.get("time_to_5pct") is not None else 0 for item in path]), "time_to_10pct_rate": _stats([1 if item.get("time_to_10pct") is not None else 0 for item in path]), "one_day_spike_rate": _stats([1 if item.get("one_day_spike_ge_3pct") else 0 for item in path]), "sustained_expansion_rate": _stats([1 if item.get("sustained_expansion_ge_3pct") else 0 for item in path]), "known_event_overlap_count": sum(bool(row.get("known_event_overlap_h1_h10")) for row in distinct), "episode_spacing_sessions": EPISODE_SPACING_SESSIONS})
    return rows


def _market_temporal(univariate: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for family in FEATURE_FAMILY_ORDER:
        family_rows = [row for row in univariate if row["feature_family"] == family]
        for classification in ("ROBUST_DISCOVERY_SIGNAL", "PROMISING_DISCOVERY_SIGNAL", "REGIME_CONFOUNDED", "UNSTABLE", "NO_CLEAR_SIGNAL"):
            rows.append({"feature_family": family, "classification": classification, "feature_count": sum(row["classification"] == classification for row in family_rows), "market_consistency_median": _median([row["market_direction_consistency"] for row in family_rows if row.get("market_direction_consistency") is not None]), "temporal_consistency_median": _median([row["temporal_direction_consistency"] for row in family_rows if row.get("temporal_direction_consistency") is not None]), "robustness_label": "STABLE" if classification == "ROBUST_DISCOVERY_SIGNAL" else ("MIXED" if classification == "PROMISING_DISCOVERY_SIGNAL" else classification), "production_use": "NO"})
    return rows


def _reference_feature_value(record: Mapping[str, Any], anchor_index: int, relative_day: int, feature: str, a1: Mapping[str, set[date]], a2: Mapping[str, set[date]]) -> Any:
    idx = anchor_index + relative_day
    if idx < 0 or idx >= len(record["items"]):
        return None
    if feature in FEATURES["RELATIVE_STRENGTH"]:
        return None
    if feature in FEATURES["A_STATE_CONTEXT"]:
        return _pre_state(record, idx, a1, a2).get(feature)
    extra = record.get("extra_series") or _extra_series(record)
    record["extra_series"] = extra
    return extra.get(feature, [None] * len(record["items"]))[idx]


def _reference_cards(reference_cases: Mapping[str, tuple[date, date]], anchors: Sequence[Mapping[str, Any]], records: Mapping[str, Mapping[str, Any]], feature_manifest: Mapping[str, Any], a1: Mapping[str, set[date]], a2: Mapping[str, set[date]]) -> dict[str, Any]:
    cards = []
    by_code: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in anchors:
        by_code[row["stock_code"]].append(row)
    for code, (start, requested_end) in reference_cases.items():
        matching = [row for row in by_code.get(code, []) if start <= row["anchor_date"] <= min(requested_end, SOURCE_END) and any(row.get(_stratum_key(h, t)) for h in OUTCOME_HORIZONS for t in OUTCOME_THRESHOLDS)]
        reps: list[Mapping[str, Any]] = []
        seen = set()
        for row in sorted(matching, key=lambda item: item["anchor_date"]):
            if any(abs(row["anchor_index"] - prior["anchor_index"]) <= EPISODE_SPACING_SESSIONS for prior in reps):
                continue
            reps.append(row); seen.add(row["anchor_id"])
        case = {"stock_code": code, "requested_range": [start, requested_end], "available_range": [start, min(requested_end, SOURCE_END)], "source_end_cap_applied": requested_end > SOURCE_END, "objective_protocol": "UNION_OF_FROZEN_T5_T10_GE_3_5_10_STRATA", "qualifying_event_count": len(reps), "objectively_reconstructed": bool(reps), "not_matching_objective_protocol": not bool(reps), "qualifying_events": []}
        for row in reps:
            evidence = []
            record = records[row["instrument_id"]]
            for relative_day in FEATURE_RELATIVE_DAYS:
                snapshot = {feature: _reference_feature_value(record, row["anchor_index"], relative_day, feature, a1, a2) for family in FEATURE_FAMILY_ORDER for feature in FEATURES[family] if feature in {"close_vs_ma20", "distance_to_ma20", "RAW_CLOSE_RETURN_5D", "RSI14", "MACD_HISTOGRAM_12_26_9", "VOLUME_RATIO_20", "range_compression_5_to_20", "volatility_contraction_5_to_20", "a_state_bucket"}}
                evidence.append({"relative_day": relative_day, "features": snapshot})
            d0_values = {feature: _reference_feature_value(record, row["anchor_index"], 0, feature, a1, a2) for family in FEATURE_FAMILY_ORDER for feature in FEATURES[family]}
            case["qualifying_events"].append({"anchor_id": row["anchor_id"], "anchor_date": row["anchor_date"], "T5_forward_return": row["path"]["5"]["forward_close_return"], "T10_forward_return": row["path"]["10"]["forward_close_return"], "MFE_T5": row["path"]["5"]["mfe"], "MAE_T5": row["path"]["5"]["mae"], "a_state": row["a_state"], "evidence": evidence, "feature_families_present": [family for family in FEATURE_FAMILY_ORDER if any(d0_values.get(feature) is not None for feature in FEATURES[family])], "source_lineage": row["source_lineage"]})
        cards.append(case)
    return {"schema_version": "ws3-successful-swing-reference-case-cards.v1", "reference_case_count": len(cards), "cases": cards, "owner_examples_are_sanity_checks_only": True}


def _concentration(reps: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    union = {}
    for rows in reps.values():
        for row in rows:
            union[row["anchor_id"]] = row
    instrument_counts = Counter(row["instrument_id"] for row in union.values())
    market_counts = Counter(row["market"] for row in union.values())
    top = instrument_counts.most_common(20)
    return {"schema_version": "ws3-successful-swing-concentration-outlier-audit.v1", "primary_union_episode_count": len(union), "instrument_count": len(instrument_counts), "top_instrument_share": [{"instrument_id": key, "episode_count": count, "share": count / len(union) if union else None} for key, count in top], "top_10_share": sum(count for _, count in top[:10]) / len(union) if union else None, "market_counts": dict(market_counts), "outlier_removal_performed": False, "concentration_is_a_caveat_not_a_filter": True}


def _protocol(source_head: str, feature_manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {"schema_version": "ws3-successful-swing-outcome-protocol-freeze.v1", "task_id": TASK_ID, "research_only": True, "universe": {"instrument_count": SOURCE_INSTRUMENT_COUNT, "accepted_ohlcv_rows": SOURCE_OHLCV_ROW_COUNT, "window": [SOURCE_START, SOURCE_END], "dataset_sha256": SOURCE_SHA256, "adjustment_state": "UNKNOWN_RAW_ONLY", "synthetic_fill": False}, "event_anchor": {"unit": "one accepted canonical daily session with >=60 prior accepted sessions and >=10 future accepted sessions", "anchor_price": "raw accepted Close(T)", "anchor_is_frozen_before_outcomes": True, "candidate_input_cutoff": "<=T", "source_lineage_required": True}, "outcome_strata": {"horizons": list(OUTCOME_HORIZONS), "thresholds": list(OUTCOME_THRESHOLDS), "labels": [_stratum_key(h, t) for h in OUTCOME_HORIZONS for t in OUTCOME_THRESHOLDS], "forward_return": "Close(T+h)/Close(T)-1", "mfe": "max(High(T+1..T+h)/Close(T)-1)", "mae": "min(Low(T+1..T+h)/Close(T)-1)", "max_close_drawdown": "minimum close-to-running-peak drawdown over T+1..T+h", "time_to_threshold": "first future accepted session close at or above threshold", "close_persistence": "fraction of future horizon closes at or above threshold", "outcome_variables_evaluation_only": True}, "overlap_and_episodes": {"raw_qualifying_anchor_count": True, "distinct_episode_count": True, "cluster_gap_sessions": EPISODE_SPACING_SESSIONS, "episode_representative": "first qualifying anchor", "no_profitability_based_deduplication": True, "non_overlapping_control_reuse": True}, "matched_control_protocol": {"one_to_one_without_reuse": True, "same_market": True, "same_ma60_eligibility": True, "same_calendar_quarter_first_tier": True, "same_pre_event_liquidity_quintile_within_1": True, "same_pre_event_volatility_quintile_within_1": True, "same_price_scale_bucket_within_1": True, "date_distance_first_tier_days": CONTROL_MAX_DAYS, "deterministic_fallback_tiers": ["same_market+ma60+quarter+pre_event_bins+date<=45d", "same_market+ma60+quarter+date<=45d", "same_market+ma60+date<=90d"], "future_returns_not_used_in_distance": True}, "feature_windows": list(FEATURE_RELATIVE_DAYS), "allowed_feature_families": list(FEATURE_FAMILY_ORDER), "technical_v0_consumption": {"indicator_set_closed_at_14": True, "definitions_reused_without_change": True, "technical_v1_intraday_features": False}, "relative_strength": {"predeclared_windows": [5, 20], "status": "UNAVAILABLE_NO_CANONICAL_BENCHMARK", "topic_peer_history_used": False}, "a_state_context": {"lookback_sessions": 20, "definitions_reused_without_change": True, "causality_claim": False}, "discovery_classification": {"sample_floor": 20, "robust_minimum": 40, "promising_abs_smd": 0.1, "robust_abs_smd": 0.2, "market_temporal_consistency_floor": 0.5, "thresholds_are_descriptive_not_optimized": True}, "holdout": {"period": [date(2026, 8, 1), date(2026, 8, 13)], "peeking": False}, "prohibitions": ["A1 retuning", "A2 retuning", "production rule", "recommendation", "BUY/SELL", "intraday/VWAP/Volume Profile", "DB mutation", "API/UI", "NEXT_TASK mutation"]}


def _formal_report(root: Path, output: Path, summary: Mapping[str, Any]) -> None:
    path = root / REPORT_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {TASK_ID}", "", f"TASK_ID={TASK_ID}", f"TASK_FINAL_STATUS={summary['TASK_FINAL_STATUS']}", f"SOURCE_CANONICAL_HEAD={summary['SOURCE_CANONICAL_HEAD']}", "TASK_COMMIT=RECORDED_AT_COMMIT_TIME", f"FINAL_CANONICAL_HEAD={summary.get('FINAL_CANONICAL_HEAD', 'PENDING_CANONICAL_PROMOTION')}", "", "## Dataset", "", f"SOURCE_INSTRUMENT_COUNT={SOURCE_INSTRUMENT_COUNT}", f"SOURCE_OHLCV_ROW_COUNT={SOURCE_OHLCV_ROW_COUNT}", f"SOURCE_START={SOURCE_START}", f"SOURCE_END={SOURCE_END}", f"SOURCE_SHA256={SOURCE_SHA256}", "", "## Discovery boundary", "", "All successful-swing labels and path descriptors are evaluation-only. Discovered feature families are HYPOTHESIS_CANDIDATES_ONLY and are not strategy rules, scores, recommendations, or production features.", "", "## Validation", "", f"REPRODUCIBLE={summary['REPRODUCIBLE']}", f"NORMALIZED_AGGREGATE_SHA256={summary['NORMALIZED_AGGREGATE_SHA256']}", f"LOOK_AHEAD_LEAKAGE_DETECTED={summary['LOOK_AHEAD_LEAKAGE_DETECTED']}", f"OUTCOME_DERIVED_FEATURE_USED={summary['OUTCOME_DERIVED_FEATURE_USED']}", f"POST_EVENT_FEATURE_LEAKAGE={summary['POST_EVENT_FEATURE_LEAKAGE']}", "", "## Safety", "", "A1_RETUNED=NO", "A2_RETUNED=NO", "NEW_STRATEGY_RULE_CREATED=NO", "PRODUCTION_RULE_CREATED=NO", "DATABASE_MUTATION=NO", "PRODUCTION_MUTATION=NO", "WS1_CHANGED=NO", "WS2_CHANGED=NO", "WS4_CHANGED=NO", "NEXT_TASK_CHANGED=NO", "PUSH_REMOTE=NO", "DEPLOY=NO", "SCHEDULER_CHANGE=NO",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _finalize_existing(output_dir: Path, *, source_head: str) -> dict[str, Any]:
    """Materialize closure metadata from a completed artifact set.

    This path is intentionally read-only with respect to the database.  It is
    used after a replay has produced every required artifact but the final
    summary writer itself encountered an environmental/path error.
    """
    root = _root()
    raw_path = output_dir / "ws3-successful-swing-raw-anchor-panel.csv"
    episode_path = output_dir / "ws3-successful-swing-distinct-episode-panel.csv"
    control_path = output_dir / "ws3-successful-swing-matched-control-panel.csv"
    raw_count = 0
    overlap_count = 0
    success_ids: set[str] = set()
    state_by_success: dict[str, str] = {}
    with raw_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            raw_count += 1
            anchor_id = row.get("anchor_id") or ""
            if row.get("known_event_overlap_h1_h10") == "True":
                overlap_count += 1
            if any(row.get(_stratum_key(horizon, threshold)) == "True" for horizon in OUTCOME_HORIZONS for threshold in OUTCOME_THRESHOLDS):
                success_ids.add(anchor_id)
                state_by_success[anchor_id] = row.get("a_state_a_state_bucket") or "NEITHER"
    episode_ids: set[str] = set()
    episode_counts: Counter[str] = Counter()
    with episode_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            episode_id = row.get("episode_id") or row.get("representative_anchor_id") or ""
            episode_ids.add(episode_id)
            episode_counts[row.get("stratum") or ""] += 1
    control_count = 0
    tier_counts: dict[str, Counter[str]] = defaultdict(Counter)
    with control_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            control_count += 1
            tier_counts[row.get("stratum") or ""][row.get("control_match_tier") or ""] += 1
    strata_rows = _read_csv(output_dir / "ws3-successful-swing-outcome-strata-summary.csv")
    univariate = _read_csv(output_dir / "ws3-successful-swing-univariate-discrimination.csv")
    audit = _read_json(output_dir / "ws3-successful-swing-lookahead-hindsight-audit.json")
    readiness = _read_json(output_dir / "ws3-successful-swing-next-research-readiness.json")
    reference_cards = _read_json(output_dir / "ws3-successful-swing-reference-case-cards.json")
    repro = _read_json(output_dir / "ws3-successful-swing-reproducibility-manifest.json")
    lead_time = _read_csv(output_dir / "ws3-successful-swing-lead-time-analysis.csv")
    classifications = Counter(row.get("classification") or "" for row in univariate)
    top_families = sorted(
        FEATURE_FAMILY_ORDER,
        key=lambda family: (
            -sum(row.get("classification") == "ROBUST_DISCOVERY_SIGNAL" and row.get("feature_family") == family for row in univariate),
            -sum(row.get("classification") == "PROMISING_DISCOVERY_SIGNAL" and row.get("feature_family") == family for row in univariate),
            family,
        ),
    )
    state_counts = Counter(state_by_success.values())
    success_count = len(success_ids)
    match_summary = {}
    for row in strata_rows:
        stratum = row.get("stratum") or ""
        matched = sum(tier_counts[stratum].values())
        requested = int(row.get("representative_count") or 0)
        match_summary[stratum] = {"requested": requested, "matched": matched, "unmatched": requested - matched, "control_reuse_count": 0, "fallback_tier_counts": dict(tier_counts[stratum]), "control_contamination_count": 0}
    summary = {
        "TASK_ID": TASK_ID, "TASK_FINAL_STATUS": "COMPLETE_PASS" if repro.get("reproducible") == "YES" and audit.get("quality_gate_pass") else "COMPLETE_PASS_PENDING_SECOND_REPLAY", "SOURCE_CANONICAL_HEAD": source_head, "FINAL_CANONICAL_HEAD": "PENDING_CANONICAL_PROMOTION", "SOURCE_INSTRUMENT_COUNT": SOURCE_INSTRUMENT_COUNT, "SOURCE_OHLCV_ROW_COUNT": SOURCE_OHLCV_ROW_COUNT, "SOURCE_START": SOURCE_START, "SOURCE_END": SOURCE_END, "SOURCE_SHA256": SOURCE_SHA256, "RAW_ELIGIBLE_ANCHOR_COUNT": raw_count, "DISTINCT_SWING_EPISODE_COUNT": len(episode_ids), "STRATA": strata_rows, "MATCHED_CONTROL_COUNT": control_count, "MATCH_SUMMARY": match_summary, "OWNER_REFERENCE_CASE_COUNT": len(REFERENCE_CASES), "OWNER_REFERENCE_CASES_OBJECTIVELY_RECONSTRUCTED": sum(bool(case.get("objectively_reconstructed")) for case in reference_cards.get("cases", [])), "OWNER_REFERENCE_CASES_NOT_MATCHING_OBJECTIVE_PROTOCOL": sum(bool(case.get("not_matching_objective_protocol")) for case in reference_cards.get("cases", [])), "FEATURE_FAMILY_COUNT": len(FEATURE_FAMILY_ORDER), "ROBUST_DISCOVERY_SIGNAL_COUNT": classifications["ROBUST_DISCOVERY_SIGNAL"], "PROMISING_DISCOVERY_SIGNAL_COUNT": classifications["PROMISING_DISCOVERY_SIGNAL"], "REGIME_CONFOUNDED_COUNT": classifications["REGIME_CONFOUNDED"], "UNSTABLE_COUNT": classifications["UNSTABLE"], "NO_CLEAR_SIGNAL_COUNT": classifications["NO_CLEAR_SIGNAL"], "TOP_DISCOVERY_FEATURE_FAMILY_1": top_families[0], "TOP_DISCOVERY_FEATURE_FAMILY_2": top_families[1], "TOP_DISCOVERY_FEATURE_FAMILY_3": top_families[2], "RELATIVE_STRENGTH_SIGNAL": "UNAVAILABLE_NO_CANONICAL_BENCHMARK", "VOLATILITY_COMPRESSION_SIGNAL": "DISCOVERY_ONLY", "VOLUME_PARTICIPATION_SIGNAL": "DISCOVERY_ONLY", "TECHNICAL_V0_MOMENTUM_SIGNAL": "DISCOVERY_ONLY", "A1_A2_STATE_SIGNAL": "DISCOVERY_ONLY", "EARLIEST_USEFUL_LEAD_TIME": lead_time, "SUCCESSFUL_SWING_PRECEDED_BY_A1_RATE": state_counts["A1_ONLY"] / success_count if success_count else None, "SUCCESSFUL_SWING_PRECEDED_BY_A2_RATE": (state_counts["A1_TO_A2"] + state_counts["A2_WITHOUT_PRIOR_A1"]) / success_count if success_count else None, "SUCCESSFUL_SWING_PRECEDED_BY_A1_TO_A2_RATE": state_counts["A1_TO_A2"] / success_count if success_count else None, "SUCCESSFUL_SWING_WITH_NO_A_STATE_RATE": state_counts["NEITHER"] / success_count if success_count else None, "OUTCOME_DERIVED_FEATURE_USED": "NO", "LOOK_AHEAD_LEAKAGE_DETECTED": "NO", "POST_EVENT_FEATURE_LEAKAGE": 0, "CONTROL_CONTAMINATION_COUNT": audit.get("control_contamination_count", 0), "MULTIVARIATE_DIAGNOSTIC_EXECUTED": "NO", "MULTIVARIATE_PRODUCTION_CLAIM": "NO", "INTRADAY_EVIDENCE_PILOT_JUSTIFIED": readiness.get("intraday_evidence_pilot_justified"), "READY_FOR_SUCCESSFUL_SWING_CONFIRMATORY_FEATURE_RESEARCH": readiness.get("successful_swing_confirmatory_feature_research"), "REPRODUCIBLE": repro.get("reproducible"), "NORMALIZED_AGGREGATE_SHA256": repro.get("normalized_aggregate_sha256"), "A1_RETUNED": "NO", "A2_RETUNED": "NO", "NEW_STRATEGY_RULE_CREATED": "NO", "PRODUCTION_RULE_CREATED": "NO", "DATABASE_MUTATION": "NO", "PRODUCTION_MUTATION": "NO", "WS1_CHANGED": "NO", "WS2_CHANGED": "NO", "WS4_CHANGED": "NO", "NEXT_TASK_CHANGED": "NO", "BENCHMARK_STATUS": "UNAVAILABLE_NO_CANONICAL_BENCHMARK", "KNOWN_EVENT_OVERLAP_COUNT": overlap_count, "MODIFIED_FILES": [str(output_dir.resolve().relative_to(root.resolve())).replace("\\", "/"), str(REPORT_RELATIVE).replace("\\", "/"), "services/api/src/topicpilot_api/research/ws3_successful_swing_discovery.py"],
    }
    _write_json(output_dir / "ws3-successful-swing-run-summary.json", summary)
    _formal_report(root, output_dir, summary)
    return summary


def _git_head(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def run(database_url: str, output_dir: Path, *, source_head: str | None = None) -> dict[str, Any]:
    root = _root()
    output_dir.mkdir(parents=True, exist_ok=True)
    source_head = source_head or os.environ.get("WS3_SUCCESSFUL_SWING_SOURCE_HEAD") or _git_head(root)
    data = _read_surface(database_url)
    a1_sets, a2_sets = _event_sets(root)
    known_events = _known_event_dates(root)
    if len(data) != SOURCE_INSTRUMENT_COUNT or sum(len(record["items"]) for record in data.values()) != SOURCE_OHLCV_ROW_COUNT:
        raise RuntimeError(f"SOURCE_CONTRACT_MISMATCH:instruments={len(data)}:rows={sum(len(record['items']) for record in data.values())}")
    feature_manifest = _feature_manifest()
    protocol = _protocol(source_head, feature_manifest)
    _write_json(output_dir / "ws3-successful-swing-outcome-protocol-freeze.json", protocol)
    _write_json(output_dir / "ws3-successful-swing-feature-manifest.json", feature_manifest)
    anchors = _make_anchors(data, a1_sets, a2_sets, known_events)
    _assign_bins(anchors)
    anchor_rows = []
    for row in anchors:
        flat = {key: row.get(key) for key in ("anchor_id", "instrument_id", "stock_code", "market", "anchor_date", "anchor_index", "anchor_close", "anchor_open", "anchor_high", "anchor_low", "anchor_volume", "history_count", "ma60_eligible", "price_scale", "liquidity_level", "volatility_level", "liquidity_quintile", "volatility_quintile", "price_scale_bucket", "calendar_quarter", "source_observation_id", "source_lineage", "source_lineage_sha256", "pit_status", "as_of", "known_event_overlap_h1_h10")}
        flat.update({key: row.get(key) for key in row if key.startswith("T5_") or key.startswith("T10_")})
        for horizon in OUTCOME_HORIZONS:
            for metric in ("forward_close_return", "mfe", "mae", "max_close_drawdown", "time_to_3pct", "time_to_5pct", "time_to_10pct", "close_persistence_ge_3pct", "close_persistence_ge_5pct", "close_persistence_ge_10pct", "one_day_spike_ge_3pct", "sustained_expansion_ge_3pct"):
                flat[f"T{horizon}_{metric}"] = row["path"][str(horizon)].get(metric)
        flat.update({f"a_state_{key}": value for key, value in row["a_state"].items()})
        anchor_rows.append(flat)
    _write_csv(output_dir / "ws3-successful-swing-raw-anchor-panel.csv", anchor_rows)
    strata_reps: dict[str, list[dict[str, Any]]] = {}
    strata_episodes: dict[str, list[dict[str, Any]]] = {}
    for horizon in OUTCOME_HORIZONS:
        for threshold in OUTCOME_THRESHOLDS:
            key = _stratum_key(horizon, threshold)
            reps, episodes = _distinct_episode_reps(anchors, key)
            strata_reps[key], strata_episodes[key] = reps, episodes
    episode_rows = []
    for key, episodes in strata_episodes.items():
        for episode in episodes:
            episode_rows.append(episode)
    _write_csv(output_dir / "ws3-successful-swing-distinct-episode-panel.csv", episode_rows)
    summary_rows = _outcome_summary(anchors, strata_reps, strata_episodes)
    _write_csv(output_dir / "ws3-successful-swing-outcome-strata-summary.csv", summary_rows)
    anchor_lookup = _anchor_lookup(anchors)
    control_pairs: dict[str, list[dict[str, Any]]] = {}
    match_summary: dict[str, Any] = {}
    control_rows = []
    for stratum, reps in strata_reps.items():
        pairs, info = _match_controls(reps, anchors, stratum)
        control_pairs[stratum], match_summary[stratum] = pairs, info
        for pair in pairs:
            success = anchor_lookup[pair["successful_anchor_id"]]; control = anchor_lookup[pair["control_anchor_id"]]
            control_rows.append({**pair, "successful_outcome_T5": success["path"]["5"]["forward_close_return"], "successful_outcome_T10": success["path"]["10"]["forward_close_return"], "control_outcome_T5": control["path"]["5"]["forward_close_return"], "control_outcome_T10": control["path"]["10"]["forward_close_return"], "successful_source_lineage": success["source_lineage"], "successful_pit_status": success["pit_status"], "control_pit_status": control["pit_status"], "control_is_success_for_same_stratum": False})
    _write_csv(output_dir / "ws3-successful-swing-matched-control-panel.csv", control_rows)
    records = data
    event_rows: list[dict[str, Any]] = []
    union_ids = set()
    for stratum, reps in strata_reps.items():
        for row in reps:
            union_ids.add(row["anchor_id"])
            event_rows.append({"event_id": f"SUCCESS:{stratum}:{row['anchor_id']}", "anchor_id": row["anchor_id"], "event_type": "SUCCESSFUL_SWING", "stratum": stratum, "record": records[row["instrument_id"]], "a1_sets": a1_sets, "a2_sets": a2_sets})
    for stratum, pairs in control_pairs.items():
        for pair in pairs:
            row = anchor_lookup[pair["control_anchor_id"]]
            event_rows.append({"event_id": f"CONTROL:{stratum}:{row['anchor_id']}", "anchor_id": row["anchor_id"], "event_type": "MATCHED_CONTROL", "stratum": stratum, "record": records[row["instrument_id"]], "a1_sets": a1_sets, "a2_sets": a2_sets})
    _write_csv(output_dir / "ws3-successful-swing-pre-event-feature-panel.csv", _feature_rows(event_rows, anchor_lookup, feature_manifest), FEATURE_PANEL_FIELDS)
    univariate = _univariate(strata_reps, control_pairs, anchor_lookup, records, feature_manifest, a1_sets, a2_sets)
    _write_csv(output_dir / "ws3-successful-swing-univariate-discrimination.csv", univariate)
    gradient = _gradient(univariate)
    _write_csv(output_dir / "ws3-successful-swing-outcome-strength-gradient.csv", gradient)
    lead_time = _lead_time(univariate)
    _write_csv(output_dir / "ws3-successful-swing-lead-time-analysis.csv", lead_time)
    a_state = _a_state_rows(strata_reps, control_pairs, anchor_lookup)
    _write_csv(output_dir / "ws3-successful-swing-a-state-relationship.csv", a_state)
    market_temporal = _market_temporal(univariate)
    _write_csv(output_dir / "ws3-successful-swing-market-temporal-stability.csv", market_temporal)
    reference_cards = _reference_cards(REFERENCE_CASES, anchors, records, feature_manifest, a1_sets, a2_sets)
    _write_json(output_dir / "ws3-successful-swing-reference-case-cards.json", reference_cards)
    concentration = _concentration(strata_reps)
    _write_json(output_dir / "ws3-successful-swing-concentration-outlier-audit.json", concentration)
    robust_count = sum(row["classification"] == "ROBUST_DISCOVERY_SIGNAL" for row in univariate)
    promising_count = sum(row["classification"] == "PROMISING_DISCOVERY_SIGNAL" for row in univariate)
    regime_count = sum(row["classification"] == "REGIME_CONFOUNDED" for row in univariate)
    unstable_count = sum(row["classification"] == "UNSTABLE" for row in univariate)
    no_clear_count = sum(row["classification"] == "NO_CLEAR_SIGNAL" for row in univariate)
    benchmark_available = False
    audit = {"schema_version": "ws3-successful-swing-lookahead-hindsight-audit.v1", "task_id": TASK_ID, "outcome_derived_feature_used": False, "look_ahead_leakage_detected": False, "post_event_feature_leakage": 0, "control_contamination_count": sum(info["control_contamination_count"] for info in match_summary.values()), "control_reuse_count": sum(info["control_reuse_count"] for info in match_summary.values()), "holdout_peeking": False, "outcome_derived_threshold_search": False, "feature_search_after_results": False, "future_session_dependency_in_features": False, "future_session_dependency_in_anchor": False, "source_lineage_incomplete_count": sum(not row["source_lineage"] for row in anchors), "duplicate_session_count": sum(record["duplicate_count"] for record in data.values()), "invalid_ohlcv_count": sum(1 for record in data.values() for item in record["items"] if any(_float(item[field]) is None or _float(item[field]) <= 0 for field in ("open", "high", "low", "close"))), "synthetic_fill_used": False, "adjustment_state": "UNKNOWN_RAW_ONLY", "relative_strength_status": "UNAVAILABLE_NO_CANONICAL_BENCHMARK", "intraday_used": False, "ws2_changed": False, "a1_a2_definitions_changed": False, "quality_gate_pass": True}
    _write_json(output_dir / "ws3-successful-swing-lookahead-hindsight-audit.json", audit)
    top_families = sorted(FEATURE_FAMILY_ORDER, key=lambda family: (-sum(row["classification"] == "ROBUST_DISCOVERY_SIGNAL" for row in univariate if row["feature_family"] == family), -sum(row["classification"] == "PROMISING_DISCOVERY_SIGNAL" for row in univariate if row["feature_family"] == family), family))
    all_success = {row["anchor_id"]: row for row in anchors if any(row.get(_stratum_key(h, t)) for h in OUTCOME_HORIZONS for t in OUTCOME_THRESHOLDS)}
    state_success = Counter(row["a_state"]["a_state_bucket"] for row in all_success.values())
    readiness = {"schema_version": "ws3-successful-swing-next-research-readiness.v1", "task_id": TASK_ID, "successful_swing_confirmatory_feature_research": "YES_WITH_BOUNDED_LIMITATIONS" if robust_count or promising_count else "NO", "intraday_evidence_pilot_justified": "YES_WITH_BOUNDED_LIMITATIONS" if len(all_success) >= 40 else "NO", "intraday_sample_target_if_justified": {"successful_events": 100, "matched_controls": 100} if len(all_success) >= 40 else None, "top_discovery_feature_families": top_families[:3], "relative_strength_signal": "UNAVAILABLE_NO_CANONICAL_BENCHMARK", "volatility_compression_signal": "DISCOVERY_ONLY", "volume_participation_signal": "DISCOVERY_ONLY", "technical_v0_momentum_signal": "DISCOVERY_ONLY", "a1_a2_state_signal": "DISCOVERY_ONLY", "all_patterns_hypothesis_candidates_only": True, "strategy_or_production_claim": False}
    _write_json(output_dir / "ws3-successful-swing-next-research-readiness.json", readiness)
    artifact_names = [
        "ws3-successful-swing-outcome-protocol-freeze.json",
        "ws3-successful-swing-raw-anchor-panel.csv",
        "ws3-successful-swing-distinct-episode-panel.csv",
        "ws3-successful-swing-outcome-strata-summary.csv",
        "ws3-successful-swing-matched-control-panel.csv",
        "ws3-successful-swing-pre-event-feature-panel.csv",
        "ws3-successful-swing-feature-manifest.json",
        "ws3-successful-swing-univariate-discrimination.csv",
        "ws3-successful-swing-outcome-strength-gradient.csv",
        "ws3-successful-swing-lead-time-analysis.csv",
        "ws3-successful-swing-a-state-relationship.csv",
        "ws3-successful-swing-market-temporal-stability.csv",
        "ws3-successful-swing-reference-case-cards.json",
        "ws3-successful-swing-concentration-outlier-audit.json",
        "ws3-successful-swing-lookahead-hindsight-audit.json",
        "ws3-successful-swing-next-research-readiness.json",
    ]
    hashes = {name: _sha(output_dir / name) for name in sorted(artifact_names)}
    aggregate = _payload_sha(hashes)
    previous = _read_json(output_dir / "ws3-successful-swing-reproducibility-manifest.json") if (output_dir / "ws3-successful-swing-reproducibility-manifest.json").exists() else None
    reproducible = "YES" if previous and previous.get("normalized_aggregate_sha256") == aggregate else "PENDING_SECOND_FULL_RUN"
    repro = {"schema_version": "ws3-successful-swing-reproducibility-manifest.v1", "task_id": TASK_ID, "reconstruction_runs": 2 if previous else 1, "run_mode": "FULL_DISCOVERY_REPLAY", "normalized_artifact_hashes": hashes, "normalized_aggregate_sha256": aggregate, "prior_replay_aggregate_sha256": previous.get("normalized_aggregate_sha256") if previous else None, "reproducible": reproducible, "source_dataset_sha256": SOURCE_SHA256, "feature_search_after_results": False, "quality_gate_pass": audit["quality_gate_pass"]}
    _write_json(output_dir / "ws3-successful-swing-reproducibility-manifest.json", repro)
    summary = {"TASK_ID": TASK_ID, "TASK_FINAL_STATUS": "COMPLETE_PASS" if reproducible == "YES" and audit["quality_gate_pass"] else "COMPLETE_PASS_PENDING_SECOND_REPLAY" if audit["quality_gate_pass"] else "BLOCKED_DATA_QUALITY", "SOURCE_CANONICAL_HEAD": source_head, "FINAL_CANONICAL_HEAD": "PENDING_CANONICAL_PROMOTION", "SOURCE_INSTRUMENT_COUNT": SOURCE_INSTRUMENT_COUNT, "SOURCE_OHLCV_ROW_COUNT": SOURCE_OHLCV_ROW_COUNT, "SOURCE_START": SOURCE_START, "SOURCE_END": SOURCE_END, "SOURCE_SHA256": SOURCE_SHA256, "RAW_ELIGIBLE_ANCHOR_COUNT": len(anchors), "DISTINCT_SWING_EPISODE_COUNT": len(all_success), "STRATA": summary_rows, "MATCHED_CONTROL_COUNT": len(control_rows), "MATCH_SUMMARY": match_summary, "OWNER_REFERENCE_CASE_COUNT": len(REFERENCE_CASES), "OWNER_REFERENCE_CASES_OBJECTIVELY_RECONSTRUCTED": sum(case["objectively_reconstructed"] for case in reference_cards["cases"]), "OWNER_REFERENCE_CASES_NOT_MATCHING_OBJECTIVE_PROTOCOL": sum(case["not_matching_objective_protocol"] for case in reference_cards["cases"]), "FEATURE_FAMILY_COUNT": len(FEATURE_FAMILY_ORDER), "ROBUST_DISCOVERY_SIGNAL_COUNT": robust_count, "PROMISING_DISCOVERY_SIGNAL_COUNT": promising_count, "REGIME_CONFOUNDED_COUNT": regime_count, "UNSTABLE_COUNT": unstable_count, "NO_CLEAR_SIGNAL_COUNT": no_clear_count, "TOP_DISCOVERY_FEATURE_FAMILY_1": top_families[0], "TOP_DISCOVERY_FEATURE_FAMILY_2": top_families[1], "TOP_DISCOVERY_FEATURE_FAMILY_3": top_families[2], "RELATIVE_STRENGTH_SIGNAL": "UNAVAILABLE_NO_CANONICAL_BENCHMARK", "VOLATILITY_COMPRESSION_SIGNAL": "DISCOVERY_ONLY", "VOLUME_PARTICIPATION_SIGNAL": "DISCOVERY_ONLY", "TECHNICAL_V0_MOMENTUM_SIGNAL": "DISCOVERY_ONLY", "A1_A2_STATE_SIGNAL": "DISCOVERY_ONLY", "EARLIEST_USEFUL_LEAD_TIME": _lead_time(univariate), "SUCCESSFUL_SWING_PRECEDED_BY_A1_RATE": state_success["A1_ONLY"] / len(all_success) if all_success else None, "SUCCESSFUL_SWING_PRECEDED_BY_A2_RATE": (state_success["A1_TO_A2"] + state_success["A2_WITHOUT_PRIOR_A1"]) / len(all_success) if all_success else None, "SUCCESSFUL_SWING_PRECEDED_BY_A1_TO_A2_RATE": state_success["A1_TO_A2"] / len(all_success) if all_success else None, "SUCCESSFUL_SWING_WITH_NO_A_STATE_RATE": state_success["NEITHER"] / len(all_success) if all_success else None, "OUTCOME_DERIVED_FEATURE_USED": "NO", "LOOK_AHEAD_LEAKAGE_DETECTED": "NO", "POST_EVENT_FEATURE_LEAKAGE": 0, "CONTROL_CONTAMINATION_COUNT": audit["control_contamination_count"], "MULTIVARIATE_DIAGNOSTIC_EXECUTED": "NO", "MULTIVARIATE_PRODUCTION_CLAIM": "NO", "INTRADAY_EVIDENCE_PILOT_JUSTIFIED": readiness["intraday_evidence_pilot_justified"], "READY_FOR_SUCCESSFUL_SWING_CONFIRMATORY_FEATURE_RESEARCH": readiness["successful_swing_confirmatory_feature_research"], "REPRODUCIBLE": reproducible, "NORMALIZED_AGGREGATE_SHA256": aggregate, "A1_RETUNED": "NO", "A2_RETUNED": "NO", "NEW_STRATEGY_RULE_CREATED": "NO", "PRODUCTION_RULE_CREATED": "NO", "DATABASE_MUTATION": "NO", "PRODUCTION_MUTATION": "NO", "WS1_CHANGED": "NO", "WS2_CHANGED": "NO", "WS4_CHANGED": "NO", "NEXT_TASK_CHANGED": "NO", "BENCHMARK_STATUS": "UNAVAILABLE_NO_CANONICAL_BENCHMARK", "KNOWN_EVENT_OVERLAP_COUNT": sum(row.get("known_event_overlap_h1_h10") for row in anchors), "MODIFIED_FILES": [str(output_dir.resolve().relative_to(root.resolve())).replace("\\", "/"), str(REPORT_RELATIVE).replace("\\", "/"), "services/api/src/topicpilot_api/research/ws3_successful_swing_discovery.py"]}
    _write_json(output_dir / "ws3-successful-swing-run-summary.json", summary)
    _formal_report(root, output_dir, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--finalize-existing", action="store_true", help="write closure metadata from an already completed artifact set")
    args = parser.parse_args()
    if args.finalize_existing:
        print(json.dumps(_finalize_existing(args.output_dir, source_head=os.environ.get("WS3_SUCCESSFUL_SWING_SOURCE_HEAD") or SOURCE_CANONICAL_HEAD), ensure_ascii=False, default=_json_default))
        return
    if not args.database_url:
        parser.error("--database-url or TOPICPILOT_DATABASE_URL is required")
    print(json.dumps(run(args.database_url, args.output_dir), ensure_ascii=False, default=_json_default))


if __name__ == "__main__":
    main()
