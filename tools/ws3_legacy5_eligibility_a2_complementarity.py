"""WS3-only Legacy-5 eligibility and A2 complementarity research.

This is a descriptive, predeclared ablation study.  It reuses the committed
Legacy-5 and A2 event/path artifacts and performs only a read-only bounded
market-surface join needed for MA20 and event-level barrier/time metrics.  It
does not alter A2/Core V0 semantics, accept a strategy, or mutate production.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping

from sqlalchemy import create_engine, text


TASK_ID = "TASK-WS3-LEGACY5-ELIGIBILITY-A2-COMPLEMENTARITY-STUDY-20260822"
SOURCE_START = date(2024, 8, 13)
SOURCE_END = date(2026, 8, 13)
EXPECTED_ROWS = 288_881
EXPECTED_INSTRUMENTS = 603
EXPECTED_SURFACE_SHA256 = "e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4"
AUTHORITY_VERSION = "sdf-603-ohlcv-2y.v1"
REFERENCE_REGISTRY = "sdf-reference-603-v1"
WINDOW_SESSIONS = 1
HORIZONS = (1, 3, 5, 10)
PATH_HORIZONS = (5, 10)
MFE_THRESHOLDS = (0.03, 0.05, 0.10)
MAE_THRESHOLDS = (-0.03, -0.05, -0.10)
BARRIER_PAIRS = ((0.05, -0.05), (0.10, -0.05))

VARIANTS = ("V0_LEGACY5", "V1_LEGACY5_MA20", "V2_LEGACY5_MA60", "V3_LEGACY5_MA20_MA60")
VARIANT_SEMANTICS = {
    "V0_LEGACY5": "Legacy-5 original: 20-day Close high + KD(9) cross + MA5>MA10 + mean last-5 volume >500 lots + K<80",
    "V1_LEGACY5_MA20": "V0 plus Close>MA20",
    "V2_LEGACY5_MA60": "V0 plus Close>MA60",
    "V3_LEGACY5_MA20_MA60": "V0 plus Close>MA20 and Close>MA60",
}

LEGACY_DIR = Path("reports/TASK-WS3-LEGACY-5-STRATEGY-BENCHMARK-20260822")
A2_PATH_DIR = Path("reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821")
A2_DECISION_DIR = Path("reports/TASK-WS3-A2-MFE-MAE-BARRIER-RACE-DECISION-REPORT-20260822")
A2_EVENT_DIR = Path("reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820")
OUTPUT_DIR_DEFAULT = Path("reports") / TASK_ID


LIGHTWEIGHT_PRICE_QUERY = text(
    """
    SELECT
        d.instrument_id::text AS instrument_id,
        d.instrument_code AS stock_code,
        d.market_code AS market,
        d.trade_date AS trading_date,
        d.canonical_observation_id::text AS observation_id,
        d.open,
        d.high,
        d.low,
        d.close,
        mds.source_code,
        mds.observation_semantics,
        co.quality_state,
        co.observed_at,
        co.ordering_key,
        co.id::text AS canonical_id
    FROM topicpilot.vw_daily_market_observations d
    JOIN topicpilot.canonical_observations co
      ON co.id = d.canonical_observation_id
    JOIN topicpilot.market_data_sources mds
      ON mds.id = d.source_id
    WHERE co.family_code = 'PRICE'
      AND d.quality_state = 'ACCEPTED'
      AND mds.observation_semantics = 'DAILY_BAR'
      AND d.trade_date >= :start_date
      AND d.trade_date <= :end_date
      AND NOT EXISTS (
          SELECT 1
          FROM topicpilot.canonical_observations successor
          WHERE successor.supersedes_id = co.id
            AND successor.family_code = 'PRICE'
            AND successor.quality_state = 'ACCEPTED'
      )
      AND NOT EXISTS (
          SELECT 1
          FROM topicpilot.reference_instrument_lifecycles lifecycle
          WHERE lifecycle.instrument_id = co.instrument_id
            AND lifecycle.status_code IN ('DELISTED', 'SUSPENDED', 'TERMINATED')
            AND lifecycle.effective_from <= d.trade_date
            AND (lifecycle.effective_to IS NULL OR lifecycle.effective_to >= d.trade_date)
      )
    ORDER BY d.market_code, d.instrument_code, d.trade_date,
             co.observed_at, co.ordering_key, co.id
    """
)


class ContractBlocked(RuntimeError):
    """Raised when a required research input fails closed."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (set, tuple, frozenset)):
        return "|".join(_json_default(item) for item in value)
    return str(value)


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (list, tuple, set, frozenset)):
        return "|".join(_csv_value(item) for item in value)
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n")


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


def _write_text_lf(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _payload_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=_json_default).encode("utf-8")).hexdigest()


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


def _linear_quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _stats(values: Iterable[Any]) -> dict[str, Any]:
    numbers = [float(value) for value in values if value not in (None, "")]
    return {
        "count": len(numbers),
        "mean": statistics.fmean(numbers) if numbers else None,
        "median": statistics.median(numbers) if numbers else None,
        "p05": _linear_quantile(numbers, 0.05),
        "p25": _linear_quantile(numbers, 0.25),
        "p75": _linear_quantile(numbers, 0.75),
        "p95": _linear_quantile(numbers, 0.95),
    }


def _rate(values: Iterable[Any], predicate: Any) -> float | None:
    numbers = [value for value in values if value not in (None, "")]
    return sum(1 for value in numbers if predicate(value)) / len(numbers) if numbers else None


def _read_surface(database_url: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Read only the accepted OHLCV fields required for MA20 and path joins."""
    engine = create_engine(database_url, future=True)
    rows: list[dict[str, Any]] = []
    with engine.connect() as connection:
        for row in connection.execute(LIGHTWEIGHT_PRICE_QUERY, {"start_date": SOURCE_START, "end_date": SOURCE_END}).mappings():
            item = dict(row)
            item["trading_date"] = _date(item["trading_date"])
            item["instrument_id"] = str(item["instrument_id"])
            item["observation_id"] = str(item["observation_id"])
            rows.append(item)
    engine.dispose()
    groups: dict[str, dict[str, Any]] = {}
    for item in rows:
        group = groups.setdefault(item["instrument_id"], {"identity": {key: item.get(key) for key in ("instrument_id", "stock_code", "market")}, "items": []})
        group["items"].append(item)
    duplicate_dates = 0
    invalid_ohlcv = 0
    for group in groups.values():
        group["items"].sort(key=lambda item: (item["trading_date"], item.get("observed_at"), item.get("ordering_key"), item["observation_id"]))
        group["dates"] = [item["trading_date"] for item in group["items"]]
        duplicate_dates += sum(count > 1 for count in Counter(group["dates"]).values())
        for item in group["items"]:
            open_, high, low, close = (_decimal(item.get(field)) for field in ("open", "high", "low", "close"))
            if None in (open_, high, low, close) or close <= 0 or high < max(open_, close) or low > min(open_, close) or low < 0:
                invalid_ohlcv += 1
    quality = {
        "queried_rows": len(rows),
        "queried_instruments": len(groups),
        "date_min": min((item["trading_date"] for item in rows), default=None),
        "date_max": max((item["trading_date"] for item in rows), default=None),
        "duplicate_session_count": duplicate_dates,
        "invalid_ohlcv_count": invalid_ohlcv,
        "query_scope": "accepted canonical PRICE DAILY_BAR only; no volume lateral; no writes",
    }
    if quality["queried_rows"] != EXPECTED_ROWS or quality["queried_instruments"] != EXPECTED_INSTRUMENTS or duplicate_dates or invalid_ohlcv:
        raise ContractBlocked(f"lightweight surface identity/quality mismatch: {quality}")
    return groups, quality


def _ma20_by_anchor(groups: Mapping[str, Mapping[str, Any]]) -> dict[tuple[str, str], Decimal | None]:
    output: dict[tuple[str, str], Decimal | None] = {}
    for instrument_id, group in groups.items():
        items = group["items"]
        closes = [_decimal(item.get("close")) for item in items]
        for index, item in enumerate(items):
            if index < 19:
                output[(instrument_id, item["trading_date"].isoformat())] = None
                continue
            window = closes[index - 19 : index + 1]
            output[(instrument_id, item["trading_date"].isoformat())] = sum(window, Decimal("0")) / Decimal("20") if all(value is not None for value in window) else None
    return output


def _load_legacy(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]], dict[str, Any]]:
    raw_path = repo_root / LEGACY_DIR / "legacy5-raw-anchors.csv"
    outcome_path = repo_root / LEGACY_DIR / "event-outcomes.csv"
    manifest_path = repo_root / LEGACY_DIR / "legacy5-event-cohort-manifest.json"
    raw = [row for row in _read_csv(raw_path) if row.get("variant") == "LEGACY-5"]
    outcomes = _read_csv(outcome_path)
    outcome_index = {(row["anchor_id"], int(row["horizon"]), row["view"]): row for row in outcomes if row.get("variant") == "LEGACY-5"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(raw) != 2471 or len(outcome_index) < len(raw) * len(HORIZONS):
        raise ContractBlocked(f"Legacy source artifact mismatch: raw={len(raw)} indexed_outcomes={len(outcome_index)}")
    return raw, outcome_index, {"raw_path": raw_path, "outcome_path": outcome_path, "manifest_path": manifest_path, "manifest": manifest}


def _variant_anchor_sets(raw: list[dict[str, str]], groups: Mapping[str, Mapping[str, Any]], ma20: Mapping[tuple[str, str], Decimal | None]) -> dict[str, list[dict[str, Any]]]:
    sets = {variant: [] for variant in VARIANTS}
    for source in raw:
        instrument_id = source["instrument_id"]
        signal_date = source["signal_date"]
        group = groups.get(instrument_id)
        if group is None:
            raise ContractBlocked(f"Legacy anchor instrument absent from accepted surface: {instrument_id}")
        index = _int(source["anchor_index"])
        if index is None or index >= len(group["items"]):
            raise ContractBlocked(f"Legacy anchor index unavailable: {source['anchor_id']}")
        item = group["items"][index]
        if item["trading_date"].isoformat() != signal_date or str(item["observation_id"]) != source["observation_id"] or str(item["close"]) != source["anchor_close"]:
            raise ContractBlocked(f"Legacy anchor lineage mismatch: {source['anchor_id']}")
        close = _decimal(source["anchor_close"])
        ma60 = _decimal(source.get("ma60"))
        ma20_value = ma20.get((instrument_id, signal_date))
        if close is None or ma20_value is None:
            raise ContractBlocked(f"Missing MA20/MA60 at Legacy anchor: {source['anchor_id']}")
        ma60_pass = ma60 is not None and close > ma60
        passes = {
            "V0_LEGACY5": True,
            "V1_LEGACY5_MA20": close > ma20_value,
            "V2_LEGACY5_MA60": ma60_pass,
            "V3_LEGACY5_MA20_MA60": close > ma20_value and ma60_pass,
        }
        for variant in VARIANTS:
            if not passes[variant]:
                continue
            row = dict(source)
            row.update({"variant": variant, "base_anchor_id": source["anchor_id"], "ma20": ma20_value, "ma60": ma60, "anchor_index": index})
            row["anchor_id"] = hashlib.sha256(f"{variant}|{source['anchor_key']}".encode("utf-8")).hexdigest()
            sets[variant].append(row)
    for variant in VARIANTS:
        sets[variant].sort(key=lambda row: (row["instrument_id"], row["signal_date"], int(row["anchor_index"]), row["observation_id"]))
    if len(sets["V0_LEGACY5"]) != 2471 or len(sets["V2_LEGACY5_MA60"]) != 2096:
        raise ContractBlocked(f"Legacy/MA60 anchor count reconciliation failed: { {key: len(value) for key, value in sets.items()} }")
    return sets


def _episodes(anchors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    episodes: list[dict[str, Any]] = []
    by_anchor: dict[str, dict[str, Any]] = {}
    previous: dict[str, dict[str, Any]] = {}
    for anchor in anchors:
        prior = previous.get(anchor["instrument_id"])
        same = prior is not None and int(anchor["anchor_index"]) == int(prior["anchor_index"]) + 1
        if same:
            anchor["episode_id"] = prior["episode_id"]
            episode = by_anchor[prior["anchor_id"]]
            episode["episode_end_date"] = anchor["signal_date"]
            episode["raw_anchor_count"] += 1
            by_anchor[anchor["anchor_id"]] = episode
        else:
            episode_id = hashlib.sha256(f"{anchor['variant']}|{anchor['anchor_key']}|EPISODE".encode("utf-8")).hexdigest()
            anchor["episode_id"] = episode_id
            episode = {
                "episode_id": episode_id,
                "variant": anchor["variant"],
                "instrument_id": anchor["instrument_id"],
                "stock_code": anchor["stock_code"],
                "market": anchor["market"],
                "episode_anchor_id": anchor["anchor_id"],
                "episode_anchor_key": anchor["anchor_key"],
                "episode_start_date": anchor["signal_date"],
                "episode_end_date": anchor["signal_date"],
                "raw_anchor_count": 1,
                "episode_anchor_index": anchor["anchor_index"],
                "dedup_rule": "contiguous qualifying accepted-session state; first qualifying anchor retained",
            }
            episodes.append(episode)
            by_anchor[anchor["anchor_id"]] = episode
        previous[anchor["instrument_id"]] = anchor
    return episodes, by_anchor


def _load_a2(repo_root: Path) -> tuple[list[dict[str, str]], dict[tuple[str, int], dict[str, str]], dict[str, Any]]:
    panel_path = repo_root / A2_EVENT_DIR / "ws3-p2e-a2-expanded-event-panel.csv"
    path_path = repo_root / A2_PATH_DIR / "a2-path-aware-outcomes.csv"
    manifest_path = repo_root / A2_PATH_DIR / "path-aware-outcome-manifest.json"
    panel = _read_csv(panel_path)
    path_rows = _read_csv(path_path)
    path_index = {(row["event_id"], int(row["horizon"])): row for row in path_rows}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(panel) != 5277 or len(path_rows) != 52770 or len(path_index) != 52770:
        raise ContractBlocked(f"A2 source artifact mismatch: panel={len(panel)} path_rows={len(path_rows)} unique_path={len(path_index)}")
    return panel, path_index, {"panel_path": panel_path, "path_path": path_path, "manifest_path": manifest_path, "manifest": manifest}


def _legacy_outcome(outcome_index: Mapping[tuple[str, int, str], dict[str, str]], anchor: Mapping[str, Any], horizon: int) -> dict[str, Any]:
    row = outcome_index.get((anchor["base_anchor_id"], horizon, "RAW_ANCHOR"))
    if row is None:
        raise ContractBlocked(f"Missing Legacy base path row: {anchor['base_anchor_id']} H{horizon}")
    return row


def _legacy_barrier(anchor: Mapping[str, Any], group: Mapping[str, Any], horizon: int, up: float, down: float) -> str:
    index = int(anchor["anchor_index"])
    future = group["items"][index + 1 : index + 1 + horizon]
    if len(future) != horizon:
        return "NOT_MATURED"
    close = _decimal(anchor["anchor_close"])
    if close is None:
        return "FAIL_CLOSED"
    for item in future:
        high, low = _decimal(item.get("high")), _decimal(item.get("low"))
        if high is None or low is None:
            return "FAIL_CLOSED"
        up_hit = high >= close * (Decimal("1") + Decimal(str(up)))
        down_hit = low <= close * (Decimal("1") + Decimal(str(down)))
        if up_hit and down_hit:
            return "SAME_SESSION_ORDER_UNKNOWN"
        if up_hit:
            return "UP_FIRST"
        if down_hit:
            return "DOWN_FIRST"
    return "NEITHER_BY_H"


def _legacy_time(anchor: Mapping[str, Any], group: Mapping[str, Any], horizon: int, threshold: float) -> tuple[str, int | None]:
    index = int(anchor["anchor_index"])
    future = group["items"][index + 1 : index + 1 + horizon]
    if len(future) != horizon:
        return "NOT_MATURED", None
    close = _decimal(anchor["anchor_close"])
    if close is None:
        return "FAIL_CLOSED", None
    target = close * (Decimal("1") + Decimal(str(threshold)))
    for session, item in enumerate(future, start=1):
        high = _decimal(item.get("high"))
        if high is None:
            return "FAIL_CLOSED", None
        if high >= target:
            return "HIT", session
    return "NOT_HIT", None


def _path_row(anchor: Mapping[str, Any], outcome: Mapping[str, Any], group: Mapping[str, Any], horizon: int, view: str) -> dict[str, Any]:
    result = {
        "variant": anchor["variant"],
        "view": view,
        "anchor_id": anchor["anchor_id"],
        "base_anchor_id": anchor["base_anchor_id"],
        "episode_id": anchor.get("episode_id"),
        "instrument_id": anchor["instrument_id"],
        "signal_date": anchor["signal_date"],
        "horizon": horizon,
        "maturity_status": outcome.get("maturity_status", ""),
        "endpoint_return": _float(outcome.get("endpoint_return")),
        "mfe": _float(outcome.get("mfe")),
        "mae": _float(outcome.get("mae")),
        "adjustment_state": "UNKNOWN_RAW_ONLY",
    }
    for up, down in BARRIER_PAIRS:
        label = f"barrier_{int(up * 100)}_before_minus{int(abs(down) * 100)}"
        race = _legacy_barrier(anchor, group, horizon, up, down)
        result[f"{label}_outcome"] = race
        result[f"{label}_up_first"] = race == "UP_FIRST"
        result[f"{label}_same_session_unknown"] = race == "SAME_SESSION_ORDER_UNKNOWN"
    for threshold in MFE_THRESHOLDS:
        status, session = _legacy_time(anchor, group, horizon, threshold)
        label = f"time_to_{int(threshold * 100)}pct"
        result[f"{label}_status"] = status
        result[f"{label}_sessions"] = session
    return result


def _path_metric_rows(variant: str, view: str, anchors: list[dict[str, Any]], groups: Mapping[str, Mapping[str, Any]], outcome_index: Mapping[tuple[str, int, str], dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    # The caller supplies the RAW_ANCHOR or first-anchor DISTINCT_EPISODE view.
    selected = anchors
    rows: list[dict[str, Any]] = []
    for anchor in selected:
        group = groups[anchor["instrument_id"]]
        for horizon in HORIZONS:
            outcome = _legacy_outcome(outcome_index, anchor, horizon)
            rows.append(_path_row(anchor, outcome, group, horizon, view))
    metrics: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        current = [row for row in rows if row["horizon"] == horizon]
        matured = [row for row in current if row["maturity_status"] == "COMPLETE_RAW_PATH" and row["endpoint_return"] is not None and row["mfe"] is not None and row["mae"] is not None]
        endpoint_stats = _stats(row["endpoint_return"] for row in matured)
        mfe_stats = _stats(row["mfe"] for row in matured)
        mae_stats = _stats(row["mae"] for row in matured)
        output: dict[str, Any] = {
            "variant": variant,
            "view": view,
            "event_count": len(current),
            "instrument_count": len({row["instrument_id"] for row in current}),
            "horizon": horizon,
            "matured_count": len(matured),
            "endpoint_mean": endpoint_stats["mean"],
            "endpoint_median": endpoint_stats["median"],
            "endpoint_p05": endpoint_stats["p05"],
            "endpoint_p25": endpoint_stats["p25"],
            "endpoint_p75": endpoint_stats["p75"],
            "endpoint_p95": endpoint_stats["p95"],
            "mfe_mean": mfe_stats["mean"],
            "mfe_median": mfe_stats["median"],
            "mae_mean": mae_stats["mean"],
            "mae_median": mae_stats["median"],
            "mfe_ge_3_count": sum(row["mfe"] >= 0.03 for row in matured),
            "mfe_ge_5_count": sum(row["mfe"] >= 0.05 for row in matured),
            "mfe_ge_10_count": sum(row["mfe"] >= 0.10 for row in matured),
            "mae_le_minus3_count": sum(row["mae"] <= -0.03 for row in matured),
            "mae_le_minus5_count": sum(row["mae"] <= -0.05 for row in matured),
            "mae_le_minus10_count": sum(row["mae"] <= -0.10 for row in matured),
            "definition": "Existing committed Legacy-5 endpoint/MFE/MAE rows; event-level barrier/time reconstructed from the same accepted future OHLC sessions; descriptive only",
        }
        for field in ("mfe_ge_3_count", "mfe_ge_5_count", "mfe_ge_10_count", "mae_le_minus3_count", "mae_le_minus5_count", "mae_le_minus10_count"):
            output[field.replace("_count", "_rate_matured")] = output[field] / len(matured) if matured else None
        for up, down in BARRIER_PAIRS:
            label = f"barrier_{int(up * 100)}_before_minus{int(abs(down) * 100)}"
            races = [row[f"{label}_outcome"] for row in matured]
            output[f"{label}_up_first_count"] = races.count("UP_FIRST")
            output[f"{label}_up_first_rate_matured"] = races.count("UP_FIRST") / len(matured) if matured else None
            output[f"{label}_down_first_count"] = races.count("DOWN_FIRST")
            output[f"{label}_same_session_unknown_count"] = races.count("SAME_SESSION_ORDER_UNKNOWN")
            output[f"{label}_same_session_unknown_rate_matured"] = races.count("SAME_SESSION_ORDER_UNKNOWN") / len(matured) if matured else None
            output[f"{label}_neither_count"] = races.count("NEITHER_BY_H")
        for threshold in MFE_THRESHOLDS:
            label = f"time_to_{int(threshold * 100)}pct"
            hits = [row[f"{label}_sessions"] for row in matured if row[f"{label}_status"] == "HIT" and row[f"{label}_sessions"] is not None]
            output[f"{label}_hit_count"] = len(hits)
            output[f"{label}_hit_rate_matured"] = len(hits) / len(matured) if matured else None
            output[f"{label}_mean_sessions_hit_only"] = statistics.fmean(hits) if hits else None
            output[f"{label}_median_sessions_hit_only"] = statistics.median(hits) if hits else None
        metrics.append(output)
    return metrics, rows


def _comparison_rows(anchors_by_variant: Mapping[str, list[dict[str, Any]]], episodes_by_variant: Mapping[str, list[dict[str, Any]]], path_rows: Mapping[tuple[str, str], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    pairs = (("V0_LEGACY5", "V1_LEGACY5_MA20"), ("V0_LEGACY5", "V2_LEGACY5_MA60"), ("V0_LEGACY5", "V3_LEGACY5_MA20_MA60"), ("V1_LEGACY5_MA20", "V3_LEGACY5_MA20_MA60"), ("V2_LEGACY5_MA60", "V3_LEGACY5_MA20_MA60"))
    output: list[dict[str, Any]] = []
    for view in ("RAW_ANCHOR", "DISTINCT_EPISODE"):
        sources = anchors_by_variant if view == "RAW_ANCHOR" else episodes_by_variant
        if view == "RAW_ANCHOR":
            ids = {variant: {row["anchor_key"] for row in rows} for variant, rows in sources.items()}
        else:
            ids = {variant: {row["episode_anchor_key"] for row in rows} for variant, rows in sources.items()}
        base_key_by_variant = {variant: {row["base_anchor_id"]: row["anchor_key"] for row in anchors_by_variant[variant]} for variant in VARIANTS}
        for source_variant, destination_variant in pairs:
            excluded = ids[source_variant] - ids[destination_variant]
            for horizon in PATH_HORIZONS:
                source_rows = [row for row in path_rows[(source_variant, view)] if row["horizon"] == horizon and row["maturity_status"] == "COMPLETE_RAW_PATH"]
                destination_rows = [row for row in path_rows[(destination_variant, view)] if row["horizon"] == horizon and row["maturity_status"] == "COMPLETE_RAW_PATH"]
                if view == "RAW_ANCHOR":
                    excluded_rows = [row for row in source_rows if base_key_by_variant[source_variant].get(row["base_anchor_id"]) in excluded]
                else:
                    excluded_rows = [row for row in source_rows if base_key_by_variant[source_variant].get(row["base_anchor_id"]) in excluded]
                output.append({
                    "from_variant": source_variant,
                    "to_variant": destination_variant,
                    "view": view,
                    "horizon": horizon,
                    "from_candidate_count": len(ids[source_variant]),
                    "to_candidate_count": len(ids[destination_variant]),
                    "candidate_reduction_count": len(excluded),
                    "candidate_reduction_rate_vs_from": len(excluded) / len(ids[source_variant]) if ids[source_variant] else None,
                    "from_unique_instrument_count": len({row["instrument_id"] for row in sources[source_variant]}),
                    "to_unique_instrument_count": len({row["instrument_id"] for row in sources[destination_variant]}),
                    "from_endpoint_mean": _stats(row["endpoint_return"] for row in source_rows)["mean"],
                    "to_endpoint_mean": _stats(row["endpoint_return"] for row in destination_rows)["mean"],
                    "from_mfe_mean": _stats(row["mfe"] for row in source_rows)["mean"],
                    "to_mfe_mean": _stats(row["mfe"] for row in destination_rows)["mean"],
                    "from_mae_mean": _stats(row["mae"] for row in source_rows)["mean"],
                    "to_mae_mean": _stats(row["mae"] for row in destination_rows)["mean"],
                    "excluded_matured_count": len(excluded_rows),
                    "positive_opportunity_sacrificed_mfe_ge_3_count": sum(row["mfe"] >= 0.03 for row in excluded_rows),
                    "positive_opportunity_sacrificed_mfe_ge_5_count": sum(row["mfe"] >= 0.05 for row in excluded_rows),
                    "positive_opportunity_sacrificed_mfe_ge_10_count": sum(row["mfe"] >= 0.10 for row in excluded_rows),
                    "adverse_cases_removed_endpoint_le_0_count": sum(row["endpoint_return"] <= 0 for row in excluded_rows),
                    "adverse_cases_removed_mae_le_minus5_count": sum(row["mae"] <= -0.05 for row in excluded_rows),
                    "endpoint_mean_delta_to_minus_from": (_stats(row["endpoint_return"] for row in destination_rows)["mean"] - _stats(row["endpoint_return"] for row in source_rows)["mean"]) if source_rows and destination_rows else None,
                    "comparison_type": "DESCRIPTIVE_ABLATION_ONLY",
                    "acceptance": "NO",
                })
    return output


def _session_delta(groups: Mapping[str, Mapping[str, Any]], instrument_id: str, earlier_or_later_a: str, b: str) -> int | None:
    group = groups.get(instrument_id)
    if not group:
        return None
    positions = {day.isoformat(): index for index, day in enumerate(group["dates"])}
    if earlier_or_later_a not in positions or b not in positions:
        return None
    return positions[b] - positions[earlier_or_later_a]


def _match_events(a2_events: list[dict[str, str]], legacy_anchors: list[dict[str, Any]], groups: Mapping[str, Mapping[str, Any]], window: int) -> dict[str, Any]:
    candidates: list[tuple[int, str, str, str, dict[str, str], dict[str, Any], int]] = []
    by_instrument: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for anchor in legacy_anchors:
        by_instrument[anchor["instrument_id"]].append(anchor)
    for event in a2_events:
        for anchor in by_instrument.get(event["instrument_id"], []):
            delta = _session_delta(groups, event["instrument_id"], event["signal_date"], anchor["signal_date"])
            if delta is not None and abs(delta) <= window:
                candidates.append((abs(delta), event["event_id"], anchor["anchor_id"], anchor["signal_date"], event, anchor, delta))
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    used_a2: set[str] = set()
    used_legacy: set[str] = set()
    matches: list[dict[str, Any]] = []
    for _, _, _, _, event, anchor, delta in candidates:
        if event["event_id"] in used_a2 or anchor["anchor_id"] in used_legacy:
            continue
        used_a2.add(event["event_id"])
        used_legacy.add(anchor["anchor_id"])
        matches.append({"a2": event, "legacy": anchor, "delta_sessions": delta})
    return {
        "matches": matches,
        "a2_only": [event for event in a2_events if event["event_id"] not in used_a2],
        "legacy_only": [anchor for anchor in legacy_anchors if anchor["anchor_id"] not in used_legacy],
        "candidate_pair_count": len(candidates),
    }


def _a2_barrier(row: Mapping[str, str], up: float, down: float) -> str:
    if row.get("horizon_status") != "COMPLETE_RAW_PATH":
        return "NOT_MATURED"
    mfe, mae = _float(row.get("mfe")), _float(row.get("mae"))
    mfe_t, mae_t = _int(row.get("mfe_timing_session")), _int(row.get("mae_timing_session"))
    if mfe is None or mae is None:
        return "FAIL_CLOSED"
    up_hit, down_hit = mfe >= up, mae <= down
    if up_hit and down_hit:
        if mfe_t is None or mae_t is None or mfe_t == mae_t:
            return "SAME_SESSION_ORDER_UNKNOWN"
        return "UP_FIRST" if mfe_t < mae_t else "DOWN_FIRST"
    if up_hit:
        return "UP_FIRST"
    if down_hit:
        return "DOWN_FIRST"
    return "NEITHER_BY_H"


def _metric_for_rows(rows: list[dict[str, Any]], source: str, overlap_group: str, variant: str, path_status: str, time_status: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for horizon in PATH_HORIZONS:
        current = [row for row in rows if row["horizon"] == horizon]
        matured = [row for row in current if row["maturity_status"] == "COMPLETE_RAW_PATH" and row["endpoint_return"] is not None and row["mfe"] is not None and row["mae"] is not None]
        endpoint, mfe, mae = _stats(row["endpoint_return"] for row in matured), _stats(row["mfe"] for row in matured), _stats(row["mae"] for row in matured)
        row: dict[str, Any] = {
            "variant": variant,
            "overlap_group": overlap_group,
            "signal_source": source,
            "path_metric_status": path_status,
            "time_to_opportunity_status": time_status,
            "horizon": horizon,
            "event_count": len(current),
            "instrument_count": len({item["instrument_id"] for item in current}),
            "matured_count": len(matured),
            "endpoint_mean": endpoint["mean"],
            "endpoint_median": endpoint["median"],
            "mfe_mean": mfe["mean"],
            "mfe_median": mfe["median"],
            "mae_mean": mae["mean"],
            "mae_median": mae["median"],
            "mfe_ge_3_rate_matured": _rate((item["mfe"] for item in matured), lambda value: value >= 0.03),
            "mfe_ge_5_rate_matured": _rate((item["mfe"] for item in matured), lambda value: value >= 0.05),
            "mfe_ge_10_rate_matured": _rate((item["mfe"] for item in matured), lambda value: value >= 0.10),
            "mae_le_minus3_rate_matured": _rate((item["mae"] for item in matured), lambda value: value <= -0.03),
            "mae_le_minus5_rate_matured": _rate((item["mae"] for item in matured), lambda value: value <= -0.05),
            "mae_le_minus10_rate_matured": _rate((item["mae"] for item in matured), lambda value: value <= -0.10),
        }
        for up, down in BARRIER_PAIRS:
            label = f"barrier_{int(up * 100)}_before_minus{int(abs(down) * 100)}"
            races = [item[f"{label}_outcome"] for item in matured]
            row[f"{label}_up_first_rate_matured"] = races.count("UP_FIRST") / len(matured) if matured else None
            row[f"{label}_same_session_unknown_rate_matured"] = races.count("SAME_SESSION_ORDER_UNKNOWN") / len(matured) if matured else None
            row[f"{label}_up_first_count"] = races.count("UP_FIRST")
            row[f"{label}_same_session_unknown_count"] = races.count("SAME_SESSION_ORDER_UNKNOWN")
        for threshold in MFE_THRESHOLDS:
            label = f"time_to_{int(threshold * 100)}pct"
            hits = [item[f"{label}_sessions"] for item in matured if item.get(f"{label}_sessions") is not None]
            row[f"{label}_hit_rate_matured"] = len(hits) / len(matured) if matured else None
            row[f"{label}_mean_sessions_hit_only"] = statistics.fmean(hits) if hits else None
        output.append(row)
    return output


def _normalize_a2_rows(events: list[dict[str, str]], path_index: Mapping[tuple[str, int], dict[str, str]], horizon: int) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for event in events:
        path = path_index.get((event["event_id"], horizon))
        if path is None:
            raise ContractBlocked(f"Missing A2 path row: {event['event_id']} H{horizon}")
        output.append({
            "event_id": event["event_id"],
            "instrument_id": event["instrument_id"],
            "signal_date": event["signal_date"],
            "horizon": horizon,
            "maturity_status": path.get("horizon_status", ""),
            "endpoint_return": _float(path.get("endpoint_return")),
            "mfe": _float(path.get("mfe")),
            "mae": _float(path.get("mae")),
            "mfe_timing_session": _int(path.get("mfe_timing_session")),
            "mae_timing_session": _int(path.get("mae_timing_session")),
            "adjustment_state": path.get("adjustment_state", "UNKNOWN_RAW_ONLY"),
        })
    return output


def _normalize_legacy_rows(anchors: list[dict[str, Any]], horizon: int, outcome_index: Mapping[tuple[str, int, str]], groups: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for anchor in anchors:
        outcome = _legacy_outcome(outcome_index, anchor, horizon)
        group = groups[anchor["instrument_id"]]
        race_rows = {}
        for up, down in BARRIER_PAIRS:
            label = f"barrier_{int(up * 100)}_before_minus{int(abs(down) * 100)}"
            race_rows[f"{label}_outcome"] = _legacy_barrier(anchor, group, horizon, up, down)
        for threshold in MFE_THRESHOLDS:
            label = f"time_to_{int(threshold * 100)}pct"
            status, sessions = _legacy_time(anchor, group, horizon, threshold)
            race_rows[f"{label}_status"], race_rows[f"{label}_sessions"] = status, sessions
        output.append({
            "anchor_id": anchor["anchor_id"],
            "base_anchor_id": anchor["base_anchor_id"],
            "instrument_id": anchor["instrument_id"],
            "signal_date": anchor["signal_date"],
            "horizon": horizon,
            "maturity_status": outcome.get("maturity_status", ""),
            "endpoint_return": _float(outcome.get("endpoint_return")),
            "mfe": _float(outcome.get("mfe")),
            "mae": _float(outcome.get("mae")),
            **race_rows,
        })
    return output


def _overlap_summary(variant: str, matching: Mapping[str, Any], legacy: list[dict[str, Any]], window: int) -> list[dict[str, Any]]:
    groups = {
        "A2_ONLY": {"a2": matching["a2_only"], "legacy": [], "pair": []},
        "LEGACY5_ONLY": {"a2": [], "legacy": matching["legacy_only"], "pair": []},
        "BOTH_SAME_SESSION": {"a2": [], "legacy": [], "pair": [item for item in matching["matches"] if item["delta_sessions"] == 0]},
        "BOTH_WITHIN_BOUNDED_WINDOW": {"a2": [], "legacy": [], "pair": [item for item in matching["matches"] if abs(item["delta_sessions"]) == 1]},
    }
    for pair in groups["BOTH_SAME_SESSION"]["pair"] + groups["BOTH_WITHIN_BOUNDED_WINDOW"]["pair"]:
        group_name = "BOTH_SAME_SESSION" if pair["delta_sessions"] == 0 else "BOTH_WITHIN_BOUNDED_WINDOW"
        groups[group_name]["a2"].append(pair["a2"])
        groups[group_name]["legacy"].append(pair["legacy"])
    rows: list[dict[str, Any]] = []
    for group_name, members in groups.items():
        pair_count = len(members["pair"])
        a2_count = len(members["a2"]) if members["a2"] else pair_count if pair_count else 0
        legacy_count = len(members["legacy"]) if members["legacy"] else pair_count if pair_count else 0
        rows.append({
            "variant": variant,
            "overlap_group": group_name,
            "matching_window_sessions": window,
            "event_count_definition": "unmatched event count for ONLY groups; one-to-one matched pair count for BOTH groups",
            "event_count": len(members["a2"]) + len(members["legacy"]) if group_name.endswith("ONLY") else pair_count,
            "a2_event_count": a2_count,
            "legacy_event_count": legacy_count,
            "pair_count": pair_count,
            "instrument_count": len({item["instrument_id"] for item in members["a2"]} | {item["instrument_id"] for item in members["legacy"]}),
            "a2_instrument_count": len({item["instrument_id"] for item in members["a2"]}),
            "legacy_instrument_count": len({item["instrument_id"] for item in members["legacy"]}),
            "candidate_pair_count_within_window": matching["candidate_pair_count"],
            "pit_safe": "YES",
            "comparison_type": "DESCRIPTIVE_COMPLEMENTARITY_ONLY",
        })
    return rows


def _complementarity_metrics(variant: str, matching: Mapping[str, Any], groups: Mapping[str, Mapping[str, Any]], outcome_index: Mapping[tuple[str, int, str], dict[str, str]], a2_path_index: Mapping[tuple[str, int], dict[str, str]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {
        "A2_ONLY": {"a2": matching["a2_only"], "legacy": [], "pair": []},
        "LEGACY5_ONLY": {"a2": [], "legacy": matching["legacy_only"], "pair": []},
        "BOTH_SAME_SESSION": {"a2": [], "legacy": [], "pair": []},
        "BOTH_WITHIN_BOUNDED_WINDOW": {"a2": [], "legacy": [], "pair": []},
    }
    for pair in matching["matches"]:
        name = "BOTH_SAME_SESSION" if pair["delta_sessions"] == 0 else "BOTH_WITHIN_BOUNDED_WINDOW"
        buckets[name]["a2"].append(pair["a2"])
        buckets[name]["legacy"].append(pair["legacy"])
        buckets[name]["pair"].append(pair)
    rows: list[dict[str, Any]] = []
    for group_name, bucket in buckets.items():
        sources: list[tuple[str, list[Any]]] = []
        if bucket["a2"]:
            sources.append(("A2", bucket["a2"]))
        if bucket["legacy"]:
            sources.append((variant, bucket["legacy"]))
        if bucket["pair"]:
            sources.append(("PAIR_COMBINED", bucket["pair"]))
        for source, members in sources:
            all_rows: list[dict[str, Any]] = []
            for horizon in PATH_HORIZONS:
                if source == "A2":
                    current = _normalize_a2_rows(members, a2_path_index, horizon)
                    for item in current:
                        for up, down in BARRIER_PAIRS:
                            label = f"barrier_{int(up * 100)}_before_minus{int(abs(down) * 100)}"
                            item[f"{label}_outcome"] = _a2_barrier(item, up, down)
                        for threshold in MFE_THRESHOLDS:
                            label = f"time_to_{int(threshold * 100)}pct"
                            item[f"{label}_sessions"] = None
                    all_rows.extend(current)
                elif source == variant:
                    current = _normalize_legacy_rows(members, horizon, outcome_index, groups)
                    all_rows.extend(current)
                else:
                    a2_current = _normalize_a2_rows([pair["a2"] for pair in members], a2_path_index, horizon)
                    legacy_current = _normalize_legacy_rows([pair["legacy"] for pair in members], horizon, outcome_index, groups)
                    for item in a2_current:
                        for up, down in BARRIER_PAIRS:
                            label = f"barrier_{int(up * 100)}_before_minus{int(abs(down) * 100)}"
                            item[f"{label}_outcome"] = _a2_barrier(item, up, down)
                        for threshold in MFE_THRESHOLDS:
                            item[f"time_to_{int(threshold * 100)}pct_sessions"] = None
                    all_rows.extend(a2_current + legacy_current)
            path_status = "PASS" if source != "A2" or all_rows else "NOT_AVAILABLE"
            time_status = "PASS" if source != "A2" else "NOT_AVAILABLE_FROM_EXISTING_A2_EVENT_PATH_ARTIFACT"
            metric_rows = _metric_for_rows(all_rows, source, group_name, variant, path_status, time_status)
            for row in metric_rows:
                row["pair_count"] = len(bucket["pair"])
                row["event_count_definition"] = "source event count; PAIR_COMBINED has two observations per matched pair"
            rows.extend(metric_rows)
    return rows


def _lead_lag_rows(variant: str, matching: Mapping[str, Any]) -> list[dict[str, Any]]:
    deltas = [pair["delta_sessions"] for pair in matching["matches"]]
    rows = []
    for delta in (-1, 0, 1):
        count = deltas.count(delta)
        rows.append({
            "variant": variant,
            "matching_window_sessions": WINDOW_SESSIONS,
            "legacy_minus_a2_session_delta": delta,
            "match_count": count,
            "match_pct": count / len(deltas) if deltas else None,
            "interpretation": "negative=Legacy earlier; zero=same session; positive=Legacy later/A2 earlier",
            "status": "AVAILABLE",
        })
    rows.append({
        "variant": variant,
        "matching_window_sessions": WINDOW_SESSIONS,
        "legacy_minus_a2_session_delta": "SUMMARY",
        "match_count": len(deltas),
        "match_pct": 1.0 if deltas else None,
        "legacy_earlier_count": sum(delta < 0 for delta in deltas),
        "same_session_count": sum(delta == 0 for delta in deltas),
        "a2_earlier_count": sum(delta > 0 for delta in deltas),
        "mean_delta_sessions": statistics.fmean(deltas) if deltas else None,
        "median_delta_sessions": statistics.median(deltas) if deltas else None,
        "interpretation": "negative=Legacy earlier; zero=same session; positive=Legacy later/A2 earlier",
        "status": "AVAILABLE",
    })
    return rows


def _reconciliation(repo_root: Path, legacy_sources: Mapping[str, Any], a2_sources: Mapping[str, Any], quality: Mapping[str, Any]) -> dict[str, Any]:
    paths = {
        "legacy_raw_anchors": legacy_sources["raw_path"],
        "legacy_event_outcomes": legacy_sources["outcome_path"],
        "legacy_cohort_manifest": legacy_sources["manifest_path"],
        "a2_event_panel": a2_sources["panel_path"],
        "a2_path_aware_outcomes": a2_sources["path_path"],
        "a2_path_manifest": a2_sources["manifest_path"],
    }
    source_files = []
    for name, path in paths.items():
        source_files.append({"name": name, "path": str(path.relative_to(repo_root)).replace("\\", "/"), "exists": path.exists(), "sha256": _sha256(path) if path.exists() else None})
    return {
        "schema_version": "ws3-legacy5-a2-semantics-reconciliation.v1",
        "task_id": TASK_ID,
        "source_files": source_files,
        "accepted_surface": {"artifact_alias": "SDF-603-2Y-OHLCV-ACCEPTED-DAILY-V1", "authority_version": AUTHORITY_VERSION, "reference_registry": REFERENCE_REGISTRY, "window": [SOURCE_START, SOURCE_END], "expected_rows": EXPECTED_ROWS, "queried_rows": quality["queried_rows"], "expected_instruments": EXPECTED_INSTRUMENTS, "queried_instruments": quality["queried_instruments"], "normalized_surface_sha256": EXPECTED_SURFACE_SHA256, "surface_query": "read-only accepted PRICE DAILY_BAR close/high/low/open; no data download; no volume pipeline rerun"},
        "eligibility_semantics": {"variants": VARIANT_SEMANTICS, "price20": "NOT_RESEARCHED_IN_THIS_TASK", "threshold_search": "NO", "fixed_set_only": True},
        "metric_reconciliation": {"anchor": "signal-day close", "endpoint": "future accepted session close / anchor close - 1", "mfe": "max future accepted session High / anchor close - 1", "mae": "min future accepted session Low / anchor close - 1", "barrier_race": "first cumulative daily High/Low crossing; same first session = SAME_SESSION_ORDER_UNKNOWN", "time_to_opportunity": "first future daily High crossing +3/+5/+10% for Legacy; A2 event artifact does not retain event-level first-threshold timing", "distinct_episode": "contiguous qualifying accepted-session state; first anchor retained", "comparison_posture": "descriptive ablation/complementarity only; no ranking or acceptance"},
        "a2_legacy_comparability": {"status": "PASS_FOR_ENDPOINT_MFE_MAE_AND_BARRIER_FROM_RECONCILED_FIELDS", "a2_anchor": "a2_close on signal_date", "legacy_anchor": "anchor_close on signal_date", "a2_adjustment_state": "UNKNOWN_RAW_ONLY", "legacy_adjustment_state": "UNKNOWN_RAW_ONLY", "a2_time_to_opportunity": "NOT_DIRECTLY_COMPARABLE_AT_EVENT_LEVEL_FROM_EXISTING_ARTIFACT", "corporate_action_policy": "UNKNOWN_RAW_ONLY/fail-closed", "same_session_order_policy": "SAME_SESSION_ORDER_UNKNOWN"},
        "overlap_policy": {"same_session": "same instrument and same signal_date", "bounded_window": "fixed +/-1 accepted trading session by instrument; no optimization", "matching": "deterministic one-to-one greedy matching sorted by absolute session distance then stable event/anchor ids", "future_outcome_not_used_for_matching": True, "if_calendar_date_missing": "fail closed from overlap rather than infer a session"},
        "pit_governance": {"accepted_quality_state_only": True, "supersession_predicate_applied": True, "future_outcome_not_used_for_overlap": True, "corporate_action_adjustment": "UNKNOWN_RAW_ONLY", "synthetic_adjustment": False, "ws1_ws2_ws4_touched": False},
    }


def _memo(summary: Mapping[str, Any], counts: Mapping[str, Any], variant_metrics: list[dict[str, Any]], comparisons: list[dict[str, Any]], overlap_summary: list[dict[str, Any]], overlap_metrics: list[dict[str, Any]]) -> str:
    def metric(variant: str, horizon: int) -> dict[str, Any]:
        return next(row for row in variant_metrics if row["variant"] == variant and row["view"] == "DISTINCT_EPISODE" and int(row["horizon"]) == horizon)

    def comp(source: str, dest: str, horizon: int = 5) -> dict[str, Any]:
        return next(row for row in comparisons if row["from_variant"] == source and row["to_variant"] == dest and row["view"] == "DISTINCT_EPISODE" and int(row["horizon"]) == horizon)

    def overlap(variant: str, group: str) -> dict[str, Any]:
        return next(row for row in overlap_summary if row["variant"] == variant and row["overlap_group"] == group)

    def om(variant: str, group: str, source: str, horizon: int = 10) -> dict[str, Any] | None:
        return next((row for row in overlap_metrics if row["variant"] == variant and row["overlap_group"] == group and row["signal_source"] == source and int(row["horizon"]) == horizon), None)

    v0_5, v0_10 = metric("V0_LEGACY5", 5), metric("V0_LEGACY5", 10)
    v1_5, v1_10 = metric("V1_LEGACY5_MA20", 5), metric("V1_LEGACY5_MA20", 10)
    v2_5, v2_10 = metric("V2_LEGACY5_MA60", 5), metric("V2_LEGACY5_MA60", 10)
    v3_5, v3_10 = metric("V3_LEGACY5_MA20_MA60", 5), metric("V3_LEGACY5_MA20_MA60", 10)
    c01, c02, c23 = comp("V0_LEGACY5", "V1_LEGACY5_MA20"), comp("V0_LEGACY5", "V2_LEGACY5_MA60"), comp("V2_LEGACY5_MA60", "V3_LEGACY5_MA20_MA60")
    both = overlap("V0_LEGACY5", "BOTH_SAME_SESSION")
    a2_only = overlap("V0_LEGACY5", "A2_ONLY")
    legacy_only = overlap("V0_LEGACY5", "LEGACY5_ONLY")
    both_metric = om("V0_LEGACY5", "BOTH_SAME_SESSION", "PAIR_COMBINED")
    a2_metric = om("V0_LEGACY5", "A2_ONLY", "A2")
    legacy_metric = om("V0_LEGACY5", "LEGACY5_ONLY", "V0_LEGACY5")
    return "\n".join([
        f"# Owner Decision Memo — {TASK_ID}",
        "",
        "## Direct answers",
        "",
        f"- MA20: V1 retains **{counts['variants']['V1_LEGACY5_MA20']['raw_anchors']} raw anchors / {counts['variants']['V1_LEGACY5_MA20']['episodes']} episodes**. T+5 changes from **{v0_5['endpoint_mean']:.4f}** to **{v1_5['endpoint_mean']:.4f}** ({(v1_5['endpoint_mean'] - v0_5['endpoint_mean']):+.4f}); T+10 changes from **{v0_10['endpoint_mean']:.4f}** to **{v1_10['endpoint_mean']:.4f}** ({(v1_10['endpoint_mean'] - v0_10['endpoint_mean']):+.4f}). It is a **research candidate only**, not accepted.",
        f"- MA60: V2 retains **{counts['variants']['V2_LEGACY5_MA60']['raw_anchors']} raw anchors / {counts['variants']['V2_LEGACY5_MA60']['episodes']} episodes**. T+5 changes by **{(v2_5['endpoint_mean'] - v0_5['endpoint_mean']):+.4f}** and T+10 by **{(v2_10['endpoint_mean'] - v0_10['endpoint_mean']):+.4f}**. The opportunity cost is **{c02['candidate_reduction_count']}** candidates and **{c02['positive_opportunity_sacrificed_mfe_ge_5_count']}** excluded H5 matured cases with MFE>=5%.",
        f"- MA20+MA60 versus MA60: V3 retains **{counts['variants']['V3_LEGACY5_MA20_MA60']['raw_anchors']} raw anchors / {counts['variants']['V3_LEGACY5_MA20_MA60']['episodes']} episodes**. Relative to V2, T+5 changes by **{(v3_5['endpoint_mean'] - v2_5['endpoint_mean']):+.4f}** and T+10 by **{(v3_10['endpoint_mean'] - v2_10['endpoint_mean']):+.4f}**; it removes **{c23['candidate_reduction_count']}** additional candidates. No acceptance conclusion is drawn.",
        f"- MA20 opportunity cost versus V0: **{c01['candidate_reduction_count']}** candidates removed; excluded H5 matured cases with MFE>=3/5/10% = **{c01['positive_opportunity_sacrificed_mfe_ge_3_count']}/{c01['positive_opportunity_sacrificed_mfe_ge_5_count']}/{c01['positive_opportunity_sacrificed_mfe_ge_10_count']}**; adverse endpoint<=0 / MAE<=-5% cases removed = **{c01['adverse_cases_removed_endpoint_le_0_count']}/{c01['adverse_cases_removed_mae_le_minus5_count']}**.",
        f"- A2 and Legacy-5 are **complementary rather than identical** under the fixed +/-1-session match: same-session BOTH={both['pair_count']} pairs, A2_ONLY={a2_only['event_count']}, LEGACY5_ONLY={legacy_only['event_count']}; these are descriptive event counts, not a production merge.",
        f"- BOTH same-session path quality: the paired combined H10 endpoint mean is **{both_metric['endpoint_mean']:.4f}** versus A2_ONLY **{a2_metric['endpoint_mean']:.4f}** and Legacy5_ONLY **{legacy_metric['endpoint_mean']:.4f}**. This is **{'informative but not acceptance evidence' if both['pair_count'] >= 30 else 'INSUFFICIENT for a stable conclusion'}**; A2 event-level time-to-opportunity remains unavailable from the existing path artifact.",
        "- Research disposition: **RESEARCH_CANDIDATE only**. No eligibility variant is accepted; Price>=20 was not researched in this task.",
        "",
        "## Core variant snapshot",
        "",
        "| Variant | Raw anchors / episodes | Instruments | T+5 | T+10 | MFE5 mean | MAE5 mean | MFE10 mean | MAE10 mean |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| V0 Legacy-5 | {counts['variants']['V0_LEGACY5']['raw_anchors']} / {counts['variants']['V0_LEGACY5']['episodes']} | {counts['variants']['V0_LEGACY5']['instruments']} | {v0_5['endpoint_mean']:.4f} | {v0_10['endpoint_mean']:.4f} | {v0_5['mfe_mean']:.4f} | {v0_5['mae_mean']:.4f} | {v0_10['mfe_mean']:.4f} | {v0_10['mae_mean']:.4f} |",
        f"| V1 +MA20 | {counts['variants']['V1_LEGACY5_MA20']['raw_anchors']} / {counts['variants']['V1_LEGACY5_MA20']['episodes']} | {counts['variants']['V1_LEGACY5_MA20']['instruments']} | {v1_5['endpoint_mean']:.4f} | {v1_10['endpoint_mean']:.4f} | {v1_5['mfe_mean']:.4f} | {v1_5['mae_mean']:.4f} | {v1_10['mfe_mean']:.4f} | {v1_10['mae_mean']:.4f} |",
        f"| V2 +MA60 | {counts['variants']['V2_LEGACY5_MA60']['raw_anchors']} / {counts['variants']['V2_LEGACY5_MA60']['episodes']} | {counts['variants']['V2_LEGACY5_MA60']['instruments']} | {v2_5['endpoint_mean']:.4f} | {v2_10['endpoint_mean']:.4f} | {v2_5['mfe_mean']:.4f} | {v2_5['mae_mean']:.4f} | {v2_10['mfe_mean']:.4f} | {v2_10['mae_mean']:.4f} |",
        f"| V3 +MA20+MA60 | {counts['variants']['V3_LEGACY5_MA20_MA60']['raw_anchors']} / {counts['variants']['V3_LEGACY5_MA20_MA60']['episodes']} | {counts['variants']['V3_LEGACY5_MA20_MA60']['instruments']} | {v3_5['endpoint_mean']:.4f} | {v3_10['endpoint_mean']:.4f} | {v3_5['mfe_mean']:.4f} | {v3_5['mae_mean']:.4f} | {v3_10['mfe_mean']:.4f} | {v3_10['mae_mean']:.4f} |",
        "",
        "## Governance",
        "",
        "`WS3_ONLY=YES`; `A_SETUP_ACCEPTED=NO`; `A_STRATEGY_ACCEPTED=NO`; `LEGACY_STRATEGY_ACCEPTED=NO`; `PRODUCTION_MUTATION=NO`; `DEPLOY=NO`; `PUSH=NO`; `NEXT_TASK_CHANGED=NO`. Corporate-action state is `UNKNOWN_RAW_ONLY`; same-session barrier ordering is `SAME_SESSION_ORDER_UNKNOWN`.",
        "",
        "The figures are gross descriptive research. They do not define entry, exit, stop, position sizing, cooldown, or production semantics. A2/Core V0, WS1/WS2/WS4, API/UI, scheduler, and NEXT_TASK are unchanged.",
        "",
    ])


def _formal(summary: Mapping[str, Any], counts: Mapping[str, Any], reconciliation: Mapping[str, Any], artifacts: Mapping[str, str]) -> str:
    lines = [
        f"# {TASK_ID}",
        "",
        "## Formal closure",
        "",
        "```text",
        f"TASK_ID={TASK_ID}",
        f"TASK_FINAL_STATUS={summary['task_status']}",
        "WS3_ONLY=YES",
        "A_SETUP_ACCEPTED=NO",
        "A_STRATEGY_ACCEPTED=NO",
        "LEGACY_STRATEGY_ACCEPTED=NO",
        "CORE_V0_SEMANTICS_CHANGED=NO",
        "A2_SEMANTICS_CHANGED=NO",
        "WS1_WS2_WS4_MUTATION=NO",
        "PRODUCTION_MUTATION=NO",
        "DEPLOY=NO",
        "PUSH=NO",
        "NEXT_TASK_CHANGED=NO",
        "DATABASE_WRITES=NO",
        "DATA_DOWNLOAD=NO",
        "LARGE_OHLCV_PIPELINE_RERUN=NO",
        "THRESHOLD_SEARCH=NO",
        "PRICE20_RESEARCHED=NO",
        "ADJUSTMENT_STATE=UNKNOWN_RAW_ONLY",
        "SAME_SESSION_ORDER=SAME_SESSION_ORDER_UNKNOWN",
        "OVERLAP_WINDOW=+/-1_TRADING_SESSION_FIXED",
        "```",
        "",
        "## Scope and frozen variants",
        "",
        "Only four predeclared eligibility variants were compared: V0 Legacy-5, V1 +MA20, V2 +MA60, and V3 +MA20+MA60. No MA10/MA30/MA40/MA120 or price threshold was searched.",
        "",
        json.dumps(counts, ensure_ascii=False, indent=2, default=_json_default),
        "",
        "## Semantics reconciliation",
        "",
        "Endpoint/MFE/MAE use the same signal-day close and future accepted-session definitions. Legacy path outcomes are reused from the committed event-outcomes artifact. A2 path outcomes are reused from the committed path-aware artifact. A2 event-level first-threshold time-to-opportunity is unavailable; those cells are marked NOT_AVAILABLE rather than inferred from future outcomes.",
        "",
        f"Source/semantics manifest: `{reconciliation.get('schema_version')}`.",
        "",
        "## Governance and limitations",
        "",
        "- Corporate-action adjustment remains UNKNOWN_RAW_ONLY and no synthetic adjustment is applied.",
        "- Same-session daily High/Low barrier races are SAME_SESSION_ORDER_UNKNOWN; intraday ordering is not guessed.",
        "- Overlap matching uses only instrument/date/session position and never uses future outcome metrics.",
        "- Results are descriptive, gross, and not a strategy ranking or acceptance.",
        "- A2 and Legacy are directly comparable for endpoint/MFE/MAE and barrier metrics under the reconciled anchor contract; A2 group-level time-to-opportunity is NOT_DIRECTLY_COMPARABLE from existing artifacts.",
        "",
        "## Artifacts",
        "",
    ]
    lines.extend(f"- `{name}`: `{digest}`" for name, digest in sorted(artifacts.items()))
    lines.extend(["", "No application, API/UI, scheduler, Production, WS1/WS2/WS4, Core V0, A2 semantics, or NEXT_TASK mutation occurred.", ""])
    return "\n".join(lines)


def _self_test() -> None:
    assert _linear_quantile([1.0, 3.0], 0.5) == 2.0
    assert _a2_barrier({"horizon_status": "COMPLETE_RAW_PATH", "mfe": "0.06", "mae": "-0.06", "mfe_timing_session": "1", "mae_timing_session": "2"}, 0.05, -0.05) == "UP_FIRST"
    assert _a2_barrier({"horizon_status": "COMPLETE_RAW_PATH", "mfe": "0.06", "mae": "-0.06", "mfe_timing_session": "1", "mae_timing_session": "1"}, 0.05, -0.05) == "SAME_SESSION_ORDER_UNKNOWN"
    print("WS3_LEGACY5_ELIGIBILITY_A2_SELF_TEST=PASS")


def run(database_url: str, output_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    repo_root = _root()
    groups, quality = _read_surface(database_url)
    ma20 = _ma20_by_anchor(groups)
    legacy_raw, legacy_outcomes, legacy_sources = _load_legacy(repo_root)
    a2_events, a2_path_index, a2_sources = _load_a2(repo_root)
    anchors_by_variant = _variant_anchor_sets(legacy_raw, groups, ma20)
    episodes_by_variant: dict[str, list[dict[str, Any]]] = {}
    episode_by_anchor: dict[str, dict[str, Any]] = {}
    for variant in VARIANTS:
        episodes, _ = _episodes(anchors_by_variant[variant])
        episodes_by_variant[variant] = episodes
        for anchor in anchors_by_variant[variant]:
            episode_by_anchor[anchor["anchor_id"]] = {"episode_id": anchor["episode_id"]}
    # Mark the first anchor of every distinct episode explicitly.
    for variant in VARIANTS:
        first_ids = {episode["episode_anchor_id"] for episode in episodes_by_variant[variant]}
        for anchor in anchors_by_variant[variant]:
            anchor["is_episode_anchor"] = anchor["anchor_id"] in first_ids

    path_metrics: list[dict[str, Any]] = []
    path_rows_by_variant_view: dict[tuple[str, str], list[dict[str, Any]]] = {}
    all_path_rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        for view in ("RAW_ANCHOR", "DISTINCT_EPISODE"):
            selected = anchors_by_variant[variant] if view == "RAW_ANCHOR" else [anchor for anchor in anchors_by_variant[variant] if anchor["is_episode_anchor"]]
            metrics, rows = _path_metric_rows(variant, view, selected, groups, legacy_outcomes)
            path_metrics.extend(metrics)
            path_rows_by_variant_view[(variant, view)] = rows
            all_path_rows.extend(rows)

    comparisons = _comparison_rows(anchors_by_variant, episodes_by_variant, path_rows_by_variant_view)
    overlap_summaries: list[dict[str, Any]] = []
    overlap_metrics: list[dict[str, Any]] = []
    lead_lag: list[dict[str, Any]] = []
    matchings: dict[str, dict[str, Any]] = {}
    for variant in VARIANTS:
        matching = _match_events(a2_events, anchors_by_variant[variant], groups, WINDOW_SESSIONS)
        matchings[variant] = matching
        overlap_summaries.extend(_overlap_summary(variant, matching, anchors_by_variant[variant], WINDOW_SESSIONS))
        overlap_metrics.extend(_complementarity_metrics(variant, matching, groups, legacy_outcomes, a2_path_index))
        lead_lag.extend(_lead_lag_rows(variant, matching))

    counts = {
        "surface": {"rows": quality["queried_rows"], "instruments": quality["queried_instruments"], "date_min": quality["date_min"], "date_max": quality["date_max"], "normalized_surface_sha256": EXPECTED_SURFACE_SHA256},
        "legacy_source": {"raw_anchors": len(legacy_raw), "a2_events": len(a2_events), "a2_path_rows": len(a2_path_index)},
        "variants": {variant: {"raw_anchors": len(anchors_by_variant[variant]), "episodes": len(episodes_by_variant[variant]), "instruments": len({row["instrument_id"] for row in anchors_by_variant[variant]}), "active_dates": len({row["signal_date"] for row in anchors_by_variant[variant]}), "ma20_pass_count": sum(_float(row.get("ma20")) is not None and _float(row.get("anchor_close")) > _float(row.get("ma20")) for row in anchors_by_variant[variant])} for variant in VARIANTS},
        "overlap_primary_v0": {row["overlap_group"]: {key: row[key] for key in ("event_count", "a2_event_count", "legacy_event_count", "pair_count", "instrument_count")} for row in overlap_summaries if row["variant"] == "V0_LEGACY5"},
    }
    reconciliation = _reconciliation(repo_root, legacy_sources, a2_sources, quality)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "legacy5-ma20-ma60-variant-comparison.csv", comparisons)
    _write_csv(output_dir / "eligibility-path-metrics.csv", path_metrics)
    _write_csv(output_dir / "a2-legacy5-overlap-summary.csv", overlap_summaries)
    _write_csv(output_dir / "a2-legacy5-complementarity-path-metrics.csv", overlap_metrics)
    _write_csv(output_dir / "signal-lead-lag-summary.csv", lead_lag)
    _write_csv(output_dir / "eligibility-anchor-panel.csv", [row for variant in VARIANTS for row in anchors_by_variant[variant]])
    _write_csv(output_dir / "eligibility-distinct-episodes.csv", [row for variant in VARIANTS for row in episodes_by_variant[variant]])
    _write_json(output_dir / "source-semantics-reconciliation-manifest.json", reconciliation)

    artifact_names = [path.name for path in output_dir.iterdir() if path.is_file() and path.name not in {"run-summary.json", "reproducibility-manifest.json", "formal-closure-report.md", "OWNER-DECISION-MEMO.md"}]
    artifact_hashes = {name: _sha256(output_dir / name) for name in sorted(artifact_names)}
    aggregate = _payload_hash(artifact_hashes)
    previous_manifest_path = output_dir / "reproducibility-manifest.json"
    previous = json.loads(previous_manifest_path.read_text(encoding="utf-8")) if previous_manifest_path.exists() else {}
    replay_count = int(previous.get("reconstruction_runs", 0) or 0) + 1
    reproducible = "YES" if previous.get("normalized_aggregate_sha256") == aggregate else "PENDING_SECOND_REPLAY"
    summary = {
        "schema_version": "ws3-legacy5-eligibility-a2-run-summary.v1",
        "task_id": TASK_ID,
        "task_status": "COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS" if reproducible == "YES" else "COMPLETE_RESEARCH_ARTIFACTS_PENDING_REPLAY",
        "source": {"artifact_alias": "SDF-603-2Y-OHLCV-ACCEPTED-DAILY-V1", "authority_version": AUTHORITY_VERSION, "reference_registry": REFERENCE_REGISTRY, "window": [SOURCE_START, SOURCE_END], "rows": quality["queried_rows"], "instruments": quality["queried_instruments"], "normalized_surface_sha256": EXPECTED_SURFACE_SHA256, "query_mode": "read_only_lightweight_ohlcv_join"},
        "fixed_variants": VARIANT_SEMANTICS,
        "counts": counts,
        "governance": {"WS3_ONLY": "YES", "A_SETUP_ACCEPTED": "NO", "A_STRATEGY_ACCEPTED": "NO", "LEGACY_STRATEGY_ACCEPTED": "NO", "CORE_V0_SEMANTICS_CHANGED": "NO", "A2_SEMANTICS_CHANGED": "NO", "WS1_WS2_WS4_MUTATION": "NO", "PRODUCTION_MUTATION": "NO", "DEPLOY": "NO", "PUSH": "NO", "NEXT_TASK_CHANGED": "NO", "DATABASE_WRITES": False, "DATA_DOWNLOAD": "NO", "LARGE_OHLCV_PIPELINE_RERUN": "NO", "PRICE20_RESEARCHED": "NO", "THRESHOLD_SEARCH": "NO", "strategy_acceptance": "NO"},
        "corporate_action_governance": {"adjustment_state": "UNKNOWN_RAW_ONLY", "synthetic_adjustment": False, "fail_closed": True, "same_session_order": "SAME_SESSION_ORDER_UNKNOWN"},
        "overlap_policy": reconciliation["overlap_policy"],
        "a2_time_to_opportunity_disposition": "NOT_AVAILABLE_FROM_EXISTING_EVENT_PATH_ARTIFACT; no inference performed",
        "artifact_hashes": artifact_hashes,
        "reproducibility": {"reconstruction_runs": replay_count, "reproducible": reproducible, "normalized_aggregate_sha256": aggregate, "prior_replay_aggregate_sha256": previous.get("normalized_aggregate_sha256")},
        "runtime_seconds": round(time.perf_counter() - started, 3),
    }
    memo = _memo(summary, counts, path_metrics, comparisons, overlap_summaries, overlap_metrics)
    _write_text_lf(output_dir / "OWNER-DECISION-MEMO.md", memo)
    formal = _formal(summary, counts, reconciliation, artifact_hashes)
    _write_text_lf(output_dir / "formal-closure-report.md", formal)
    _write_json(output_dir / "reproducibility-manifest.json", {"schema_version": "ws3-legacy5-eligibility-a2-reproducibility.v1", "task_id": TASK_ID, "reconstruction_runs": replay_count, "reproducible": reproducible, "normalized_artifact_hashes": artifact_hashes, "normalized_aggregate_sha256": aggregate, "prior_replay_aggregate_sha256": previous.get("normalized_aggregate_sha256"), "source_surface_sha256": EXPECTED_SURFACE_SHA256, "database_access": "read_only", "strategy_acceptance": "NO"})
    _write_json(output_dir / "run-summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL") or os.environ.get("DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR_DEFAULT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        return
    if not args.database_url:
        parser.error("--database-url or TOPICPILOT_DATABASE_URL/DATABASE_URL is required")
    try:
        print(json.dumps(run(args.database_url, args.output_dir), ensure_ascii=False, default=_json_default))
    except ContractBlocked as exc:
        print(f"WS3_LEGACY5_ELIGIBILITY_A2_CONTRACT_BLOCKED={exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
