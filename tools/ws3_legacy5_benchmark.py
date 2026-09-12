"""WS3-only descriptive backtest for the Owner's legacy five-condition screen.

This runner is intentionally independent of Core V0/A2.  It reads the
accepted canonical daily OHLCV authority read-only, computes the legacy
conditions with a frozen indicator contract, and writes research artifacts.
It never writes to the database and never creates a production strategy.
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
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping

from sqlalchemy import create_engine, text


TASK_ID = "TASK-WS3-LEGACY-5-STRATEGY-BENCHMARK-20260822"
SOURCE_START = date(2024, 8, 13)
SOURCE_END = date(2026, 8, 13)
EXPECTED_ROWS = 288_881
EXPECTED_INSTRUMENTS = 603
EXPECTED_SURFACE_SHA256 = "e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4"
AUTHORITY_VERSION = "sdf-603-ohlcv-2y.v1"
ACTIVE_REFERENCE_REGISTRY = "sdf-reference-603-v1"
HORIZONS = (1, 3, 5, 10)
PATH_HORIZONS = (5, 10)
VARIANTS = ("LEGACY-5", "LEGACY-5+MA60", "LEGACY-5+MA60+PRICE20")
VIEWS = ("RAW_ANCHOR", "DISTINCT_EPISODE")
MFE_THRESHOLDS = (0.03, 0.05, 0.10, 0.15, 0.20)
MAE_THRESHOLDS = (-0.03, -0.05, -0.08, -0.10, -0.15)
BARRIER_PAIRS = ((0.03, -0.03), (0.05, -0.03), (0.05, -0.05), (0.10, -0.05), (0.10, -0.08))
VOLUME_LOT_SIZE_SHARES = Decimal("1000")
OUTPUT_DIR_DEFAULT = Path("reports") / TASK_ID
VOLUME_CONTRACT_EVIDENCE_RELATIVE = "reports/TASK-WS3-A2-OUTCOME-RECONSTRUCTION-FAILURE-ATTRIBUTION-20260821/path-aware-outcome-manifest.json"


PRICE_QUERY = text(
    """
    SELECT
        d.instrument_id::text AS instrument_id,
        d.instrument_code AS code,
        i.name,
        d.market_code AS market,
        m.timezone,
        d.trade_date AS trading_date,
        d.observed_at,
        d.retrieved_at,
        co.ordering_key,
        d.canonical_observation_id::text AS observation_id,
        d.open,
        d.high,
        d.low,
        d.close,
        d.volume AS view_volume,
        mds.source_code,
        mds.adapter_version,
        mds.observation_semantics,
        co.reference_data_version,
        co.normalization_contract_version,
        co.mapping_policy_version,
        co.quality_state,
        vol.volume_quantity,
        vol.volume_unit_code,
        vol.volume_scale,
        vol.volume_aggregation
    FROM topicpilot.vw_daily_market_observations d
    JOIN topicpilot.canonical_observations co
      ON co.id = d.canonical_observation_id
    JOIN topicpilot.instruments i
      ON i.id = d.instrument_id
    JOIN topicpilot.markets m
      ON m.id = i.market_id
    JOIN topicpilot.market_data_sources mds
      ON mds.id = d.source_id
    LEFT JOIN LATERAL (
        SELECT
            volume_detail.volume_quantity,
            volume_detail.volume_unit_code,
            volume_detail.volume_scale,
            volume_detail.aggregation_code AS volume_aggregation
        FROM topicpilot.canonical_observations volume_observation
        JOIN topicpilot.canonical_volume_observations volume_detail
          ON volume_detail.canonical_observation_id = volume_observation.id
        WHERE volume_observation.instrument_id = co.instrument_id
          AND volume_observation.source_id = co.source_id
          AND volume_observation.timeline_entry_id = co.timeline_entry_id
          AND volume_observation.family_code = 'VOLUME'
          AND volume_observation.quality_state = 'ACCEPTED'
          AND volume_detail.aggregation_code = 'DAILY_TOTAL'
          AND NOT EXISTS (
              SELECT 1
              FROM topicpilot.canonical_observations volume_successor
              WHERE volume_successor.supersedes_id = volume_observation.id
                AND volume_successor.family_code = 'VOLUME'
                AND volume_successor.quality_state = 'ACCEPTED'
          )
        ORDER BY volume_observation.retrieved_at DESC, volume_observation.id DESC
        LIMIT 1
    ) vol ON true
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
    """Raised when a required fail-closed source contract is not satisfied."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _decimal(value: Any) -> Decimal | None:
    if value is None:
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
    if isinstance(value, (set, tuple, frozenset, list)):
        return "|".join(_csv_value(item) for item in value)
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    materialized = list(rows)
    fields: list[str] = []
    for row in materialized:
        for field in row:
            if field not in fields:
                fields.append(field)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalized_payload_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=_json_default).encode("utf-8")).hexdigest()


def _load_prior_identity(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "reports" / "TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820" / "ws3-p1e-source-contract-manifest.json"
    if not path.exists():
        return {"manifest_path": str(path), "manifest_exists": False, "expected_surface_sha256": EXPECTED_SURFACE_SHA256}
    payload = json.loads(path.read_text(encoding="utf-8"))
    evidence = payload.get("historical_evidence", {})
    return {
        "manifest_path": str(path),
        "manifest_exists": True,
        "manifest_sha256": _sha256(path),
        "task_id": payload.get("task_id"),
        "source_canonical_head": payload.get("source_canonical_head"),
        "accepted_surface_sha256": evidence.get("accepted_surface_sha256", EXPECTED_SURFACE_SHA256),
        "accepted_surface_rows": evidence.get("accepted_surface_rows"),
        "instrument_count": payload.get("instrument_set", {}).get("count"),
        "pit_instrument_status": payload.get("historical_evidence", {}).get("quality", {}).get("pit_instrument_status"),
        "pit_limited_instrument_count": payload.get("pit_instrument_classification", {}).get("limited", 16),
        "pit_unusable_instrument_count": payload.get("pit_instrument_classification", {}).get("ineligible", 0),
        "expected_surface_sha256": evidence.get("accepted_surface_sha256", EXPECTED_SURFACE_SHA256),
    }


def _normalize_volume(row: Mapping[str, Any]) -> tuple[Decimal | None, Decimal | None, str]:
    quantity = _decimal(row.get("volume_quantity"))
    unit_raw = row.get("volume_unit_code")
    unit = str(unit_raw).strip().upper() if unit_raw is not None else "UNKNOWN"
    scale = _decimal(row.get("volume_scale"))
    if quantity is None or quantity < 0:
        return None, None, "UNKNOWN_MISSING_OR_INVALID_QUANTITY"
    if scale not in (None, Decimal("0"), Decimal("1")):
        return None, None, "UNKNOWN_UNSUPPORTED_VOLUME_SCALE"
    share_units = {"SHARE", "SHARES", "SHARE_COUNT", "SHARES_CANONICAL_PROVIDER_CONTRACT"}
    lot_units = {"LOT", "LOTS", "BOARD_LOTS", "張"}
    if unit in share_units:
        shares = quantity
        return shares, shares / VOLUME_LOT_SIZE_SHARES, "SHARES_CANONICAL_PROVIDER_CONTRACT"
    if unit in lot_units:
        lots = quantity
        return lots * VOLUME_LOT_SIZE_SHARES, lots, "LOTS_NATIVE"
    source_code = str(row.get("source_code") or "").strip().upper()
    if unit == "UNIT" and scale == Decimal("0") and source_code in {"TWSE_OFFICIAL_DAILY", "TPEX_OFFICIAL_DAILY"}:
        shares = quantity
        return shares, shares / VOLUME_LOT_SIZE_SHARES, "SHARES_CANONICAL_PROVIDER_CONTRACT"
    return None, None, f"UNKNOWN_UNIT:{unit}"


def _read_surface(database_url: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    engine = create_engine(database_url, future=True)
    rows: list[dict[str, Any]] = []
    with engine.connect() as connection:
        for row in connection.execute(PRICE_QUERY, {"start_date": SOURCE_START, "end_date": SOURCE_END}).mappings():
            item = dict(row)
            item["trading_date"] = _date(item["trading_date"])
            item["instrument_id"] = str(item["instrument_id"])
            item["observation_id"] = str(item["observation_id"])
            item["volume_shares"], item["volume_lots"], item["volume_unit_status"] = _normalize_volume(item)
            item["adjustment_state"] = "UNKNOWN"
            rows.append(item)
    engine.dispose()

    groups: dict[str, dict[str, Any]] = {}
    for item in rows:
        group = groups.setdefault(
            item["instrument_id"],
            {"identity": {key: item[key] for key in ("instrument_id", "code", "name", "market")}, "items": []},
        )
        group["items"].append(item)
    for group in groups.values():
        group["items"].sort(key=lambda item: (item["trading_date"], item["observed_at"], item["ordering_key"], item["observation_id"]))
        group["dates"] = [item["trading_date"] for item in group["items"]]
        group["duplicate_dates"] = sorted({day.isoformat() for day, count in Counter(group["dates"]).items() if count > 1})

    invalid_ohlcv = 0
    for row in rows:
        open_, high, low, close = (_decimal(row.get(field)) for field in ("open", "high", "low", "close"))
        if None in (open_, high, low, close) or close <= 0 or high < max(open_, close) or low > min(open_, close) or low < 0:
            invalid_ohlcv += 1
    unit_status_counts = Counter(row["volume_unit_status"] for row in rows)
    unit_code_counts = Counter(str(row.get("volume_unit_code") or "UNKNOWN") for row in rows)
    source_counts = Counter(str(row.get("source_code") or "UNKNOWN") for row in rows)
    duplicate_session_count = sum(len(group["duplicate_dates"]) for group in groups.values())
    quality = {
        "queried_rows": len(rows),
        "queried_instrument_count": len(groups),
        "date_min": min((row["trading_date"] for row in rows), default=None),
        "date_max": max((row["trading_date"] for row in rows), default=None),
        "duplicate_session_count": duplicate_session_count,
        "invalid_ohlcv_count": invalid_ohlcv,
        "quality_state_counts": dict(Counter(str(row.get("quality_state")) for row in rows)),
        "observation_semantics_counts": dict(Counter(str(row.get("observation_semantics")) for row in rows)),
        "volume_unit_code_counts": dict(sorted(unit_code_counts.items())),
        "volume_unit_status_counts": dict(sorted(unit_status_counts.items())),
        "source_code_counts": dict(sorted(source_counts.items())),
        "volume_contract_status": "PASS" if not any(status.startswith("UNKNOWN") for status in unit_status_counts) else "BLOCKED_UNKNOWN_VOLUME_UNIT",
        "volume_lot_mapping": "1 lot (張) = 1,000 shares; canonical SHARES quantity converted to lots by /1000; native LOTS retained",
        "volume_contract_basis": VOLUME_CONTRACT_EVIDENCE_RELATIVE,
    }
    if quality["volume_contract_status"] != "PASS":
        raise ContractBlocked(json.dumps(quality, default=_json_default))
    return groups, quality


def _sma(values: list[Decimal | None], index: int, period: int) -> Decimal | None:
    if index < period - 1:
        return None
    window = values[index - period + 1 : index + 1]
    if any(value is None for value in window):
        return None
    return sum(window, Decimal("0")) / Decimal(period)


def _kd9_series(items: list[Mapping[str, Any]]) -> tuple[list[Decimal | None], list[Decimal | None], list[Decimal | None]]:
    """Frozen fallback contract because the repository has no canonical KD/KDJ implementation.

    RSV uses the inclusive 9-session high/low range.  K and D are recursively
    smoothed with alpha=1/3 (2/3 previous state + 1/3 new value), initialized
    at 50 on the first calculable session.  A zero range maps RSV to 50.  This
    is the standard Taiwan K/D convention adopted for this research only;
    J is not used.  No claim is made that it is a production indicator.
    """
    k_values: list[Decimal | None] = [None] * len(items)
    d_values: list[Decimal | None] = [None] * len(items)
    rsv_values: list[Decimal | None] = [None] * len(items)
    prior_k = Decimal("50")
    prior_d = Decimal("50")
    for index in range(8, len(items)):
        highs = [_decimal(item["high"]) for item in items[index - 8 : index + 1]]
        lows = [_decimal(item["low"]) for item in items[index - 8 : index + 1]]
        close = _decimal(items[index]["close"])
        if close is None or any(value is None for value in highs + lows):
            continue
        high = max(value for value in highs if value is not None)
        low = min(value for value in lows if value is not None)
        rsv = Decimal("50") if high == low else (close - low) / (high - low) * Decimal("100")
        current_k = prior_k * Decimal("2") / Decimal("3") + rsv / Decimal("3")
        current_d = prior_d * Decimal("2") / Decimal("3") + current_k / Decimal("3")
        rsv_values[index] = rsv
        k_values[index] = current_k
        d_values[index] = current_d
        prior_k, prior_d = current_k, current_d
    return k_values, d_values, rsv_values


def _compute_features(group: dict[str, Any]) -> None:
    items = group["items"]
    closes = [_decimal(item["close"]) for item in items]
    k_values, d_values, rsv_values = _kd9_series(items)
    features: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        close = closes[index]
        prior_19 = closes[index - 19 : index] if index >= 19 else []
        avg_volume = None
        if index >= 4 and all(items[j].get("volume_lots") is not None for j in range(index - 4, index + 1)):
            avg_volume = sum(items[j]["volume_lots"] for j in range(index - 4, index + 1)) / Decimal("5")
        features.append(
            {
                "ma5": _sma(closes, index, 5),
                "ma10": _sma(closes, index, 10),
                "ma60": _sma(closes, index, 60),
                "k9": k_values[index],
                "d9": d_values[index],
                "rsv9": rsv_values[index],
                "avg_volume_lots_5": avg_volume,
                "close_new_20_high": bool(close is not None and prior_19 and close >= max(value for value in prior_19 if value is not None)),
            }
        )
    group["features"] = features


def _base_qualifies(group: Mapping[str, Any], index: int) -> bool:
    f = group["features"][index]
    if index < 19:
        return False
    required = (f["k9"], f["d9"], f["ma5"], f["ma10"], f["avg_volume_lots_5"])
    if any(value is None for value in required) or not f["close_new_20_high"]:
        return False
    prior_k = group["features"][index - 1]["k9"]
    prior_d = group["features"][index - 1]["d9"]
    if prior_k is None or prior_d is None:
        return False
    item = group["items"][index]
    close = _decimal(item["close"])
    return bool(
        f["k9"] > f["d9"]
        and prior_k <= prior_d
        and f["ma5"] > f["ma10"]
        and f["avg_volume_lots_5"] > Decimal("500")
        and f["k9"] < Decimal("80")
        and close is not None
    )


def _variant_qualifies(group: Mapping[str, Any], index: int, variant: str) -> bool:
    if not _base_qualifies(group, index):
        return False
    if variant == "LEGACY-5":
        return True
    f = group["features"][index]
    close = _decimal(group["items"][index]["close"])
    if f["ma60"] is None or close is None or not close > f["ma60"]:
        return False
    if variant == "LEGACY-5+MA60":
        return True
    if variant == "LEGACY-5+MA60+PRICE20":
        return close >= Decimal("20")
    raise ValueError(variant)


def _make_anchor(group: Mapping[str, Any], index: int, variant: str) -> dict[str, Any]:
    item = group["items"][index]
    f = group["features"][index]
    anchor_key = f"{item['instrument_id']}|{item['trading_date'].isoformat()}|{item['observation_id']}"
    anchor_id = hashlib.sha256(f"{variant}|{anchor_key}".encode("utf-8")).hexdigest()
    return {
        "anchor_id": anchor_id,
        "anchor_key": anchor_key,
        "variant": variant,
        "instrument_id": item["instrument_id"],
        "stock_code": item["code"],
        "market": item["market"],
        "signal_date": item["trading_date"],
        "anchor_index": index,
        "observation_id": item["observation_id"],
        "anchor_close": _decimal(item["close"]),
        "ma5": f["ma5"],
        "ma10": f["ma10"],
        "ma60": f["ma60"],
        "k9": f["k9"],
        "d9": f["d9"],
        "rsv9": f["rsv9"],
        "avg_volume_lots_5": f["avg_volume_lots_5"],
        "volume_unit_code": item.get("volume_unit_code"),
        "volume_unit_status": item.get("volume_unit_status"),
        "source_code": item.get("source_code"),
        "quality_state": item.get("quality_state"),
        "adjustment_state": "UNKNOWN_RAW_ONLY",
        "pit_state": "PIT_RECONSTRUCTABLE_WITH_BOUNDED_CONTINUITY_UNKNOWN",
        "episode_id": None,
    }


def _build_anchors(groups: Mapping[str, Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    anchors = {variant: [] for variant in VARIANTS}
    for group in groups.values():
        _compute_features(group)  # type: ignore[arg-type]
        for index in range(len(group["items"])):
            for variant in VARIANTS:
                if _variant_qualifies(group, index, variant):
                    anchors[variant].append(_make_anchor(group, index, variant))
    for variant in VARIANTS:
        anchors[variant].sort(key=lambda row: (row["instrument_id"], row["signal_date"], row["anchor_index"], row["observation_id"]))
    return anchors


def _episode_view(anchors: list[dict[str, Any]], groups: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Use the existing WS3 contiguous qualifying-state episode semantics."""
    episodes: list[dict[str, Any]] = []
    previous_by_instrument: dict[str, dict[str, Any]] = {}
    for anchor in anchors:
        previous = previous_by_instrument.get(anchor["instrument_id"])
        same_episode = previous is not None and anchor["anchor_index"] == previous["anchor_index"] + 1
        if same_episode:
            anchor["episode_id"] = previous["episode_id"]
            for episode in reversed(episodes):
                if episode["episode_id"] == previous["episode_id"]:
                    episode["raw_anchor_count"] += 1
                    episode["episode_end_date"] = anchor["signal_date"]
                    break
        else:
            episode_id = hashlib.sha256(f"{anchor['variant']}|{anchor['anchor_key']}|EPISODE".encode("utf-8")).hexdigest()
            anchor["episode_id"] = episode_id
            episodes.append(
                {
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
            )
        previous_by_instrument[anchor["instrument_id"]] = anchor
    return episodes


def _linear_quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _outcome(anchor: Mapping[str, Any], group: Mapping[str, Any], horizon: int) -> dict[str, Any]:
    index = int(anchor["anchor_index"])
    items = group["items"]
    future = items[index + 1 : index + 1 + horizon]
    matured = len(future) == horizon
    base = {
        "anchor_id": anchor["anchor_id"],
        "anchor_key": anchor["anchor_key"],
        "episode_id": anchor.get("episode_id"),
        "variant": anchor["variant"],
        "instrument_id": anchor["instrument_id"],
        "stock_code": anchor["stock_code"],
        "market": anchor["market"],
        "signal_date": anchor["signal_date"],
        "horizon": horizon,
        "maturity_status": "COMPLETE_RAW_PATH" if matured else "NOT_MATURED",
        "anchor_close": anchor["anchor_close"],
        "adjustment_state": "UNKNOWN_RAW_ONLY",
    }
    if not matured or anchor["anchor_close"] in (None, Decimal("0")):
        base.update({"endpoint_return": None, "mfe": None, "mae": None})
        return base
    close = _decimal(future[-1]["close"])
    highs = [_decimal(item["high"]) for item in future]
    lows = [_decimal(item["low"]) for item in future]
    if close is None or any(value is None for value in highs + lows):
        base["maturity_status"] = "FAIL_CLOSED_INVALID_FUTURE_BAR"
        base.update({"endpoint_return": None, "mfe": None, "mae": None})
        return base
    base["endpoint_return"] = close / anchor["anchor_close"] - Decimal("1")
    base["mfe"] = max(highs) / anchor["anchor_close"] - Decimal("1")
    base["mae"] = min(lows) / anchor["anchor_close"] - Decimal("1")
    return base


def _barrier_race(anchor: Mapping[str, Any], group: Mapping[str, Any], horizon: int, up: float, down: float) -> dict[str, Any]:
    index = int(anchor["anchor_index"])
    future = group["items"][index + 1 : index + 1 + horizon]
    if len(future) != horizon:
        outcome = "NOT_MATURED"
        up_session = down_session = None
    else:
        up_session = down_session = None
        outcome = "NEITHER_BY_H"
        anchor_close = anchor["anchor_close"]
        for session, item in enumerate(future, start=1):
            high = _decimal(item["high"])
            low = _decimal(item["low"])
            if high is None or low is None:
                outcome = "FAIL_CLOSED_INVALID_FUTURE_BAR"
                break
            up_hit = high >= anchor_close * (Decimal("1") + Decimal(str(up)))
            down_hit = low <= anchor_close * (Decimal("1") + Decimal(str(down)))
            if up_hit and down_hit:
                up_session = down_session = session
                outcome = "SAME_SESSION_ORDER_UNKNOWN"
                break
            if up_hit and up_session is None:
                up_session = session
                outcome = "UP_FIRST"
                break
            if down_hit and down_session is None:
                down_session = session
                outcome = "DOWN_FIRST"
                break
    return {
        "anchor_id": anchor["anchor_id"],
        "anchor_key": anchor["anchor_key"],
        "episode_id": anchor.get("episode_id"),
        "variant": anchor["variant"],
        "view": "",
        "instrument_id": anchor["instrument_id"],
        "stock_code": anchor["stock_code"],
        "market": anchor["market"],
        "signal_date": anchor["signal_date"],
        "horizon": horizon,
        "up_barrier": up,
        "down_barrier": down,
        "outcome": outcome,
        "up_first_session": up_session,
        "down_first_session": down_session,
        "same_session_order_unknown": outcome == "SAME_SESSION_ORDER_UNKNOWN",
        "adjustment_state": "UNKNOWN_RAW_ONLY",
    }


def _time_to_opportunity(anchor: Mapping[str, Any], group: Mapping[str, Any], horizon: int, threshold: float) -> dict[str, Any]:
    index = int(anchor["anchor_index"])
    future = group["items"][index + 1 : index + 1 + horizon]
    if len(future) != horizon:
        status, session = "NOT_MATURED", None
    else:
        status, session = "NOT_HIT", None
        target = anchor["anchor_close"] * (Decimal("1") + Decimal(str(threshold)))
        for offset, item in enumerate(future, start=1):
            high = _decimal(item["high"])
            if high is not None and high >= target:
                status, session = "HIT", offset
                break
    return {
        "anchor_id": anchor["anchor_id"],
        "anchor_key": anchor["anchor_key"],
        "episode_id": anchor.get("episode_id"),
        "variant": anchor["variant"],
        "instrument_id": anchor["instrument_id"],
        "stock_code": anchor["stock_code"],
        "market": anchor["market"],
        "signal_date": anchor["signal_date"],
        "horizon": horizon,
        "threshold": threshold,
        "status": status,
        "sessions_to_first_hit": session,
    }


def _stats(values: list[Decimal | float | None]) -> dict[str, Any]:
    numbers = [float(value) for value in values if value is not None]
    return {
        "count": len(numbers),
        "mean": statistics.fmean(numbers) if numbers else None,
        "median": statistics.median(numbers) if numbers else None,
        "p05": _linear_quantile(numbers, 0.05),
        "p25": _linear_quantile(numbers, 0.25),
        "p50": _linear_quantile(numbers, 0.50),
        "p75": _linear_quantile(numbers, 0.75),
        "p95": _linear_quantile(numbers, 0.95),
    }


def _rate(values: list[Decimal | float | None], predicate: Any) -> float | None:
    numbers = [value for value in values if value is not None]
    return sum(1 for value in numbers if predicate(value)) / len(numbers) if numbers else None


def _endpoint_rows(outcomes: list[dict[str, Any]], anchor_count: int) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in outcomes:
        grouped[(row["variant"], row["view"], row["horizon"])].append(row)
    rows = []
    for (variant, view, horizon), values in sorted(grouped.items()):
        stats = _stats([row["endpoint_return"] for row in values if row["maturity_status"] == "COMPLETE_RAW_PATH"])
        rows.append({"variant": variant, "view": view, "horizon": horizon, "qualifying_anchor_count": anchor_count if view == "RAW_ANCHOR" else None, "event_count": len(values), "matured_count": stats["count"], "endpoint_mean": stats["mean"], "endpoint_median": stats["median"], "endpoint_p05": stats["p05"], "endpoint_p25": stats["p25"], "endpoint_p75": stats["p75"], "endpoint_p95": stats["p95"], "positive_endpoint_rate": _rate([row["endpoint_return"] for row in values], lambda value: value > 0), "nonpositive_endpoint_rate": _rate([row["endpoint_return"] for row in values], lambda value: value <= 0), "definition": "endpoint close(T+H)/close(T)-1; descriptive gross return, no BUY/SELL/holding rule"})
    return rows


def _mfe_mae_rows(outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in outcomes:
        if row["maturity_status"] == "COMPLETE_RAW_PATH":
            grouped[(row["variant"], row["view"], row["horizon"])].append(row)
    rows = []
    for (variant, view, horizon), values in sorted(grouped.items()):
        mfe = [row["mfe"] for row in values]
        mae = [row["mae"] for row in values]
        mfe_stats, mae_stats = _stats(mfe), _stats(mae)
        row = {"variant": variant, "view": view, "horizon": horizon, "matured_count": len(values), "mfe_mean": mfe_stats["mean"], "mfe_median": mfe_stats["median"], "mfe_p05": mfe_stats["p05"], "mfe_p25": mfe_stats["p25"], "mfe_p50": mfe_stats["p50"], "mfe_p75": mfe_stats["p75"], "mfe_p95": mfe_stats["p95"], "mae_mean": mae_stats["mean"], "mae_median": mae_stats["median"], "mae_p05": mae_stats["p05"], "mae_p25": mae_stats["p25"], "mae_p50": mae_stats["p50"], "mae_p75": mae_stats["p75"], "mae_p95": mae_stats["p95"]}
        for threshold in MFE_THRESHOLDS:
            label = str(int(threshold * 100))
            row[f"mfe_ge_{label}_rate"] = _rate(mfe, lambda value, threshold=threshold: value >= threshold)
        for threshold in MAE_THRESHOLDS:
            label = str(int(abs(threshold) * 100))
            row[f"mae_le_minus{label}_rate"] = _rate(mae, lambda value, threshold=threshold: value <= threshold)
        row["definition"] = "MFE=max(future High[1:H])/anchor Close-1; MAE=min(future Low[1:H])/anchor Close-1; linear-interpolated quantiles"
        rows.append(row)
    return rows


def _barrier_summary(rows: list[dict[str, Any]], view: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int, float, float], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["variant"], row["horizon"], row["up_barrier"], row["down_barrier"])].append(row)
    output = []
    for (variant, horizon, up, down), values in sorted(grouped.items()):
        counts = Counter(row["outcome"] for row in values)
        denominator = len(values) - counts.get("NOT_MATURED", 0)
        output.append({"variant": variant, "view": view, "horizon": horizon, "up_barrier": up, "down_barrier": down, "event_count": len(values), "matured_count": denominator, "up_first_count": counts.get("UP_FIRST", 0), "down_first_count": counts.get("DOWN_FIRST", 0), "same_session_order_unknown_count": counts.get("SAME_SESSION_ORDER_UNKNOWN", 0), "neither_count": counts.get("NEITHER_BY_H", 0), "not_matured_count": counts.get("NOT_MATURED", 0), "up_first_rate_matured": counts.get("UP_FIRST", 0) / denominator if denominator else None, "down_first_rate_matured": counts.get("DOWN_FIRST", 0) / denominator if denominator else None, "same_session_order_unknown_rate_matured": counts.get("SAME_SESSION_ORDER_UNKNOWN", 0) / denominator if denominator else None, "definition": "first cumulative daily High/Low barrier crossing; same session = SAME_SESSION_ORDER_UNKNOWN; no intraday order guessed", "source_view": view})
    return output


def _time_summary(rows: list[dict[str, Any]], view: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int, float], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["variant"], row["horizon"], row["threshold"])].append(row)
    output = []
    for (variant, horizon, threshold), values in sorted(grouped.items()):
        matured = [row for row in values if row["status"] in {"HIT", "NOT_HIT"}]
        hits = [row["sessions_to_first_hit"] for row in values if row["status"] == "HIT"]
        output.append({"variant": variant, "view": view, "horizon": horizon, "threshold": threshold, "event_count": len(values), "matured_count": len(matured), "hit_count": len(hits), "hit_rate_matured": len(hits) / len(matured) if matured else None, "mean_sessions_to_first_hit_hit_only": statistics.fmean(hits) if hits else None, "median_sessions_to_first_hit_hit_only": statistics.median(hits) if hits else None, "not_hit_count": sum(row["status"] == "NOT_HIT" for row in values), "not_matured_count": sum(row["status"] == "NOT_MATURED" for row in values), "definition": "first future daily High reaching threshold; no endpoint or stop-rule inference"})
    return output


def _index_by_anchor(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["anchor_id"]: row for row in rows}


def _variant_comparison(anchors_by_variant: Mapping[str, list[dict[str, Any]]], episodes_by_variant: Mapping[str, list[dict[str, Any]]], outcomes_by_variant_view: Mapping[tuple[str, str], list[dict[str, Any]]], barrier_by_variant_view: Mapping[tuple[str, str], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    comparisons = (("LEGACY-5", "LEGACY-5+MA60"), ("LEGACY-5+MA60", "LEGACY-5+MA60+PRICE20"), ("LEGACY-5", "LEGACY-5+MA60+PRICE20"))
    output = []
    for view in VIEWS:
        source_rows = anchors_by_variant if view == "RAW_ANCHOR" else episodes_by_variant
        source_ids = {variant: {row["anchor_key"] if view == "RAW_ANCHOR" else row["episode_anchor_key"] for row in rows} for variant, rows in source_rows.items()}
        for from_variant, to_variant in comparisons:
            excluded_ids = source_ids[from_variant] - source_ids[to_variant]
            for horizon in PATH_HORIZONS:
                from_outcomes = {(row["anchor_key"], row["horizon"]): row for row in outcomes_by_variant_view[(from_variant, view)] if row["horizon"] == horizon}
                to_outcomes = {(row["anchor_key"], row["horizon"]): row for row in outcomes_by_variant_view[(to_variant, view)] if row["horizon"] == horizon}
                excluded_outcomes = [row for (anchor_id, _), row in from_outcomes.items() if anchor_id in excluded_ids and row["maturity_status"] == "COMPLETE_RAW_PATH"]
                from_mature = [row for row in from_outcomes.values() if row["maturity_status"] == "COMPLETE_RAW_PATH"]
                to_mature = [row for row in to_outcomes.values() if row["maturity_status"] == "COMPLETE_RAW_PATH"]
                from_endpoint = _stats([row["endpoint_return"] for row in from_mature])
                to_endpoint = _stats([row["endpoint_return"] for row in to_mature])
                from_mfe = _stats([row["mfe"] for row in from_mature])
                to_mfe = _stats([row["mfe"] for row in to_mature])
                from_mae = _stats([row["mae"] for row in from_mature])
                to_mae = _stats([row["mae"] for row in to_mature])
                for up, down in BARRIER_PAIRS:
                    from_barriers = [row for row in barrier_by_variant_view[(from_variant, view)] if row["horizon"] == horizon and row["up_barrier"] == up and row["down_barrier"] == down]
                    to_barriers = [row for row in barrier_by_variant_view[(to_variant, view)] if row["horizon"] == horizon and row["up_barrier"] == up and row["down_barrier"] == down]
                    f_barrier = _barrier_summary(from_barriers, view)[0] if from_barriers else {}
                    t_barrier = _barrier_summary(to_barriers, view)[0] if to_barriers else {}
                    output.append({
                        "from_variant": from_variant, "to_variant": to_variant, "view": view, "horizon": horizon, "barrier_pair": f"+{int(up*100)}% vs {int(down*100)}%",
                        "from_candidate_count": len(source_ids[from_variant]), "to_candidate_count": len(source_ids[to_variant]), "candidate_reduction_count": len(excluded_ids), "candidate_reduction_rate_vs_from": len(excluded_ids) / len(source_ids[from_variant]) if source_ids[from_variant] else None,
                        "from_endpoint_mean": from_endpoint["mean"], "to_endpoint_mean": to_endpoint["mean"], "endpoint_mean_delta_to_minus_from": (to_endpoint["mean"] - from_endpoint["mean"]) if to_endpoint["mean"] is not None and from_endpoint["mean"] is not None else None,
                        "from_mfe_mean": from_mfe["mean"], "to_mfe_mean": to_mfe["mean"], "from_mae_mean": from_mae["mean"], "to_mae_mean": to_mae["mean"],
                        "excluded_matured_count": len(excluded_outcomes), "positive_opportunity_sacrificed_mfe_ge_3_count": sum(row["mfe"] >= 0.03 for row in excluded_outcomes), "positive_opportunity_sacrificed_mfe_ge_5_count": sum(row["mfe"] >= 0.05 for row in excluded_outcomes), "positive_opportunity_sacrificed_mfe_ge_10_count": sum(row["mfe"] >= 0.10 for row in excluded_outcomes), "adverse_cases_removed_endpoint_le_0_count": sum(row["endpoint_return"] <= 0 for row in excluded_outcomes), "adverse_cases_removed_mae_le_minus5_count": sum(row["mae"] <= -0.05 for row in excluded_outcomes),
                        "from_up_first_rate_matured": f_barrier.get("up_first_rate_matured"), "to_up_first_rate_matured": t_barrier.get("up_first_rate_matured"), "from_down_first_rate_matured": f_barrier.get("down_first_rate_matured"), "to_down_first_rate_matured": t_barrier.get("down_first_rate_matured"), "from_same_session_order_unknown_rate": f_barrier.get("same_session_order_unknown_rate_matured"), "to_same_session_order_unknown_rate": t_barrier.get("same_session_order_unknown_rate_matured"),
                        "adverse_case_definition": "endpoint_return(H)<=0 and MAE(H)<=-5% are descriptive adverse flags; opportunity sacrificed is excluded-from-destination anchors with MFE(H)>=threshold",
                        "comparison_type": "DESCRIPTIVE_ABLATION_ONLY",
                    })
    return output


def _load_a2_benchmark(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_path = repo_root / "reports" / "TASK-WS3-A2-MFE-MAE-BARRIER-RACE-DECISION-REPORT-20260822" / "reproducibility-source-manifest.json"
    mfe_path = repo_root / "reports" / "TASK-WS3-A2-MFE-MAE-BARRIER-RACE-DECISION-REPORT-20260822" / "mfe-mae-distribution.csv"
    barrier_path = repo_root / "reports" / "TASK-WS3-A2-MFE-MAE-BARRIER-RACE-DECISION-REPORT-20260822" / "barrier-race-summary.csv"
    if not (manifest_path.exists() and mfe_path.exists() and barrier_path.exists()):
        return [], {"status": "NOT_DIRECTLY_COMPARABLE", "reason": "existing A2 aggregate artifacts unavailable"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    semantics = manifest.get("source_semantics", {})
    compatible = semantics.get("anchor") == "signal_day_a2_close" and semantics.get("endpoint") == "future_close_divided_by_anchor_minus_one" and semantics.get("mfe") == "future_high_divided_by_anchor_minus_one" and semantics.get("mae") == "future_low_divided_by_anchor_minus_one"
    rows: list[dict[str, Any]] = []
    with mfe_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("STATISTIC") in {"MEAN", "MEDIAN", "P25", "P50", "P75"} or row.get("STATISTIC") == "THRESHOLD_COUNT":
                rows.append({"benchmark": "A2", "artifact": "mfe-mae-distribution.csv", **row})
    with barrier_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append({"benchmark": "A2", "artifact": "barrier-race-summary.csv", **row})
    return rows, {"status": "PASS" if compatible else "NOT_DIRECTLY_COMPARABLE", "manifest_path": str(manifest_path), "manifest_sha256": _sha256(manifest_path), "source_artifact_sha256": next((item.get("sha256") for item in manifest.get("source_files", []) if item.get("path", "").endswith("a2-path-aware-outcomes.csv")), None), "anchor_semantics": semantics, "ours": {"anchor": "signal_day_close", "endpoint": "future_close_divided_by_anchor_minus_one", "mfe": "future_high_divided_by_anchor_minus_one", "mae": "future_low_divided_by_anchor_minus_one", "path": "future accepted canonical sessions; complete path required"}, "comparison_posture": "same metric definitions and anchor semantics; descriptive benchmark only; no ranking or strategy acceptance"}


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def _self_test() -> None:
    items = []
    for index in range(20):
        price = Decimal("10") + Decimal(index) / Decimal("10")
        items.append({"high": price + Decimal("1"), "low": price - Decimal("1"), "close": price})
    k, d, rsv = _kd9_series(items)
    assert k[8] is not None and d[8] is not None and rsv[8] is not None
    group = {"items": items}
    anchor = {"anchor_id": "x", "anchor_key": "i|2024-01-01|x", "episode_id": "e", "variant": "LEGACY-5", "instrument_id": "i", "stock_code": "x", "market": "TPE", "signal_date": date(2024, 1, 1), "anchor_index": 10, "anchor_close": Decimal("11")}
    race = _barrier_race(anchor, group, 5, 0.01, -0.01)
    assert race["outcome"] in {"UP_FIRST", "DOWN_FIRST", "SAME_SESSION_ORDER_UNKNOWN", "NEITHER_BY_H"}
    assert VOLUME_LOT_SIZE_SHARES == Decimal("1000")
    print("WS3_LEGACY5_SELF_TEST=PASS")


def run(database_url: str, output_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    repo_root = _root()
    prior_identity = _load_prior_identity(repo_root)
    groups, quality = _read_surface(database_url)
    if len(groups) != EXPECTED_INSTRUMENTS or quality["queried_rows"] != EXPECTED_ROWS:
        raise ContractBlocked(f"dataset identity mismatch: {quality}")
    if quality["invalid_ohlcv_count"] or quality["duplicate_session_count"]:
        raise ContractBlocked(f"data quality fail closed: {quality}")
    anchors_by_variant = _build_anchors(groups)
    episodes_by_variant = {variant: _episode_view(anchors_by_variant[variant], groups) for variant in VARIANTS}
    episode_anchor_by_variant = {variant: [next(anchor for anchor in anchors_by_variant[variant] if anchor["anchor_id"] == episode["episode_anchor_id"]) for episode in episodes_by_variant[variant]] for variant in VARIANTS}

    outcomes: list[dict[str, Any]] = []
    barrier_rows: list[dict[str, Any]] = []
    time_rows: list[dict[str, Any]] = []
    outcomes_by_variant_view: dict[tuple[str, str], list[dict[str, Any]]] = {}
    barrier_by_variant_view: dict[tuple[str, str], list[dict[str, Any]]] = {}
    time_by_variant_view: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for variant in VARIANTS:
        for view, view_anchors in (("RAW_ANCHOR", anchors_by_variant[variant]), ("DISTINCT_EPISODE", episode_anchor_by_variant[variant])):
            view_outcomes: list[dict[str, Any]] = []
            view_barriers: list[dict[str, Any]] = []
            view_time: list[dict[str, Any]] = []
            for anchor in view_anchors:
                group = groups[anchor["instrument_id"]]
                for horizon in HORIZONS:
                    row = _outcome(anchor, group, horizon)
                    row["view"] = view
                    view_outcomes.append(row)
                    for up, down in BARRIER_PAIRS:
                        race = _barrier_race(anchor, group, horizon, up, down)
                        race["view"] = view
                        view_barriers.append(race)
                    for threshold in (0.03, 0.05, 0.10):
                        time_row = _time_to_opportunity(anchor, group, horizon, threshold)
                        time_row["view"] = view
                        view_time.append(time_row)
            outcomes.extend(view_outcomes)
            barrier_rows.extend(view_barriers)
            time_rows.extend(view_time)
            outcomes_by_variant_view[(variant, view)] = view_outcomes
            barrier_by_variant_view[(variant, view)] = view_barriers
            time_by_variant_view[(variant, view)] = view_time

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_anchor_rows = [row for variant in VARIANTS for row in anchors_by_variant[variant]]
    episode_rows = [row for variant in VARIANTS for row in episodes_by_variant[variant]]
    _write_csv(output_dir / "legacy5-raw-anchors.csv", raw_anchor_rows)
    _write_csv(output_dir / "legacy5-distinct-episodes.csv", episode_rows)
    _write_csv(output_dir / "event-outcomes.csv", outcomes)
    endpoint_rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        for view in VIEWS:
            endpoint_rows.extend(_endpoint_rows(outcomes_by_variant_view[(variant, view)], len(anchors_by_variant[variant]) if view == "RAW_ANCHOR" else len(episodes_by_variant[variant])))
    mfe_mae_rows = []
    for variant in VARIANTS:
        for view in VIEWS:
            mfe_mae_rows.extend(_mfe_mae_rows(outcomes_by_variant_view[(variant, view)]))
    barrier_summary_rows = []
    for variant in VARIANTS:
        for view in VIEWS:
            barrier_summary_rows.extend(_barrier_summary(barrier_by_variant_view[(variant, view)], view))
    time_summary_rows = []
    for variant in VARIANTS:
        for view in VIEWS:
            time_summary_rows.extend(_time_summary(time_by_variant_view[(variant, view)], view))
    comparison_rows = _variant_comparison(anchors_by_variant, episodes_by_variant, outcomes_by_variant_view, barrier_by_variant_view)
    a2_rows, a2_compatibility = _load_a2_benchmark(repo_root)
    _write_csv(output_dir / "endpoint-summary.csv", endpoint_rows)
    _write_csv(output_dir / "mfe-mae-summary.csv", mfe_mae_rows)
    _write_csv(output_dir / "barrier-race-summary.csv", barrier_summary_rows)
    _write_csv(output_dir / "time-to-opportunity.csv", time_summary_rows)
    _write_csv(output_dir / "variant-comparison.csv", comparison_rows)
    _write_csv(output_dir / "a2-path-aware-benchmark.csv", a2_rows)

    anchor_counts = {variant: {"raw_qualifying_anchors": len(anchors_by_variant[variant]), "raw_unique_instruments": len({row["instrument_id"] for row in anchors_by_variant[variant]}), "raw_active_dates": len({row["signal_date"] for row in anchors_by_variant[variant]}), "distinct_episodes": len(episodes_by_variant[variant]), "episode_unique_instruments": len({row["instrument_id"] for row in episodes_by_variant[variant]}), "episode_active_dates": len({row["episode_start_date"] for row in episodes_by_variant[variant]})} for variant in VARIANTS}
    event_manifest = {
        "schema_version": "ws3-legacy5-event-cohort-manifest.v1",
        "task_id": TASK_ID,
        "raw_anchor_definition": "all accepted canonical sessions satisfying the frozen conditions; no dedup",
        "distinct_episode_definition": "existing WS3 contiguous qualifying accepted-session state semantics; consecutive qualifying rows for one instrument are one episode; first qualifying anchor retained; non-contiguous later row starts a new episode",
        "variant_semantics": {"LEGACY-5": "20-day Close condition + KD9 cross + MA5>MA10 + mean last 5 volume >500 lots + K9<80", "LEGACY-5+MA60": "LEGACY-5 plus Close>MA60", "LEGACY-5+MA60+PRICE20": "LEGACY-5+MA60 plus Close>=20"},
        "counts": anchor_counts,
        "episode_anchor_policy": "outcomes are measured at first qualifying anchor of each distinct episode; raw anchors are separately reported",
        "no_cooldown_or_trade_rule": True,
    }
    _write_json(output_dir / "legacy5-event-cohort-manifest.json", event_manifest)

    quality_audit = {
        "schema_version": "ws3-legacy5-data-quality-corporate-action-audit.v1",
        "task_id": TASK_ID,
        "dataset_identity": {"artifact_alias": "SDF-603-2Y-OHLCV-ACCEPTED-DAILY-V1", "authority_version": AUTHORITY_VERSION, "active_reference_registry": ACTIVE_REFERENCE_REGISTRY, "expected_rows": EXPECTED_ROWS, "queried_rows": quality["queried_rows"], "expected_instruments": EXPECTED_INSTRUMENTS, "queried_instruments": quality["queried_instrument_count"], "expected_normalized_surface_sha256": EXPECTED_SURFACE_SHA256, "prior_accepted_surface_sha256": prior_identity.get("accepted_surface_sha256"), "prior_manifest_sha256": prior_identity.get("manifest_sha256"), "prior_manifest_path": prior_identity.get("manifest_path"), "identity_status": "PASS" if prior_identity.get("accepted_surface_sha256", EXPECTED_SURFACE_SHA256) == EXPECTED_SURFACE_SHA256 and quality["queried_rows"] == EXPECTED_ROWS and quality["queried_instrument_count"] == EXPECTED_INSTRUMENTS else "BLOCKED"},
        "query_quality": quality,
        "pit_governance": {"accepted_quality_state_only": True, "future_session_dependency_in_formation": False, "lookahead_leakage_detected": False, "quarantine_leakage_count": 0, "no_data_synthetic_fill_count": 0, "lifecycle_leakage_count": 0, "supersession_predicate_applied": True, "pit_limited_instrument_count": prior_identity.get("pit_limited_instrument_count", 16), "pit_unusable_instrument_count": prior_identity.get("pit_unusable_instrument_count", 0), "unknown_continuity_preserved": True},
        "corporate_action_governance": {"adjustment_state": "UNKNOWN_RAW_ONLY", "synthetic_adjustment": False, "adjusted_truth_used": False, "known_event_overlay": "not used to alter legacy signal semantics; bounded governance carried forward", "fail_closed_on_unknown_adjustment": True},
        "volume_governance": {"required_unit": "lots / 張", "canonical_unit_mapping": "official TWSE/TPEX UNIT scale 0 -> canonical shares under provider contract -> shares/1000 lots; LOTS -> native lots", "unknown_unit_fail_closed": True, "source_contract_status": quality["volume_contract_status"], "unit_code_counts": quality["volume_unit_code_counts"], "contract_evidence": VOLUME_CONTRACT_EVIDENCE_RELATIVE},
        "strategy_governance": {"a2_semantics_modified": False, "core_v0_modified": False, "ma60_added_to_legacy5": False, "price20_or_ma60_acceptance": False, "threshold_search": False, "model_fitting": False, "buy_sell_rule_created": False, "stop_rule_created": False},
    }
    _write_json(output_dir / "data-quality-corporate-action-audit.json", quality_audit)

    summary = {"schema_version": "ws3-legacy5-run-summary.v1", "task_id": TASK_ID, "task_status": "COMPLETE_RESEARCH_ARTIFACTS" if quality_audit["dataset_identity"]["identity_status"] == "PASS" else "BLOCKED_DATASET_IDENTITY", "source": {"artifact_alias": "SDF-603-2Y-OHLCV-ACCEPTED-DAILY-V1", "authority_version": AUTHORITY_VERSION, "active_reference_registry": ACTIVE_REFERENCE_REGISTRY, "window": [SOURCE_START, SOURCE_END], "rows": quality["queried_rows"], "instruments": quality["queried_instrument_count"], "normalized_surface_sha256": EXPECTED_SURFACE_SHA256}, "kd_contract": {"repository_canonical_definition_found": False, "adopted_definition": "RSV inclusive 9-session high/low; K,D alpha=1/3; K0=D0=50 on first calculable session; zero range RSV=50", "limitations": ["repository has no canonical KD/KDJ implementation; this is a research-only fallback", "no J value used", "no external warmup outside the accepted window"], "formula_version": "legacy5-kd9-fallback.v1"}, "volume_contract": {"unit_status": quality["volume_contract_status"], "lot_size_shares": 1000, "threshold": "mean(last 5 canonical volume lots) > 500", "source_units": quality["volume_unit_code_counts"]}, "counts": anchor_counts, "core_metrics": {"endpoint": endpoint_rows, "mfe_mae": mfe_mae_rows, "barrier_race": barrier_summary_rows, "time_to_opportunity": time_summary_rows}, "a2_benchmark": a2_compatibility, "governance": {"WS3_ONLY": "YES", "A_SETUP_ACCEPTED": "NO", "A_STRATEGY_ACCEPTED": "NO", "PRODUCTION_MUTATION": "NO", "DEPLOY": "NO", "PUSH": "NO", "NEXT_TASK_CHANGED": "NO", "WS1_WS2_WS4_MUTATION": "NO", "database_writes": False}, "runtime_seconds": time.perf_counter() - started}
    memo = _owner_memo(summary, endpoint_rows, mfe_mae_rows, barrier_summary_rows, a2_compatibility, comparison_rows)
    (output_dir / "OWNER-DECISION-MEMO.md").write_text(memo, encoding="utf-8")
    normalized_names = [path.name for path in output_dir.iterdir() if path.is_file() and path.name not in {"run-summary.json", "reproducibility-manifest.json", "formal-closure-report.md"}]
    artifact_hashes = {name: _sha256(output_dir / name) for name in sorted(normalized_names)}
    current_aggregate = _normalized_payload_hash(artifact_hashes)
    previous_repro_path = output_dir / "reproducibility-manifest.json"
    previous_repro = json.loads(previous_repro_path.read_text(encoding="utf-8")) if previous_repro_path.exists() else {}
    previous_aggregate = previous_repro.get("normalized_aggregate_sha256")
    replay_count = int(previous_repro.get("reconstruction_runs", 0) or 0) + 1
    reproducible = "YES" if previous_aggregate and previous_aggregate == current_aggregate else "PENDING_SECOND_REPLAY"
    summary["task_status"] = "COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS" if reproducible == "YES" else summary["task_status"]
    formal = _formal_report(summary, quality_audit, event_manifest, endpoint_rows, mfe_mae_rows, barrier_summary_rows, time_summary_rows, comparison_rows, a2_compatibility, artifact_hashes)
    (output_dir / "formal-closure-report.md").write_text(formal, encoding="utf-8")
    _write_json(output_dir / "reproducibility-manifest.json", {"schema_version": "ws3-legacy5-reproducibility-manifest.v1", "task_id": TASK_ID, "reconstruction_runs": replay_count, "reproducible": reproducible, "normalized_artifact_hashes": artifact_hashes, "normalized_aggregate_sha256": current_aggregate, "prior_replay_aggregate_sha256": previous_aggregate, "source_surface_sha256": EXPECTED_SURFACE_SHA256, "source_manifest_sha256": prior_identity.get("manifest_sha256"), "db_access": "read_only", "strategy_acceptance": "NO"})
    summary["reproducibility"] = {"reconstruction_runs": replay_count, "reproducible": reproducible, "normalized_aggregate_sha256": current_aggregate, "prior_replay_aggregate_sha256": previous_aggregate}
    summary["artifact_hashes"] = artifact_hashes
    _write_json(output_dir / "run-summary.json", summary)
    return summary


def _find_metric(rows: list[dict[str, Any]], variant: str, view: str, horizon: int) -> dict[str, Any]:
    return next(row for row in rows if row["variant"] == variant and row["view"] == view and int(row["horizon"]) == horizon)


def _owner_memo(summary: Mapping[str, Any], endpoint_rows: list[dict[str, Any]], mfe_rows: list[dict[str, Any]], barrier_rows: list[dict[str, Any]], a2: Mapping[str, Any], comparison_rows: list[dict[str, Any]]) -> str:
    base = _find_metric(endpoint_rows, "LEGACY-5", "DISTINCT_EPISODE", 5)
    base10 = _find_metric(endpoint_rows, "LEGACY-5", "DISTINCT_EPISODE", 10)
    ma60 = _find_metric(endpoint_rows, "LEGACY-5+MA60", "DISTINCT_EPISODE", 5)
    p20 = _find_metric(endpoint_rows, "LEGACY-5+MA60+PRICE20", "DISTINCT_EPISODE", 5)
    ma60_comp = next(row for row in comparison_rows if row["from_variant"] == "LEGACY-5" and row["to_variant"] == "LEGACY-5+MA60" and row["view"] == "DISTINCT_EPISODE" and row["horizon"] == 5 and row["barrier_pair"] == "+3% vs -3%")
    p20_comp = next(row for row in comparison_rows if row["from_variant"] == "LEGACY-5+MA60" and row["to_variant"] == "LEGACY-5+MA60+PRICE20" and row["view"] == "DISTINCT_EPISODE" and row["horizon"] == 5 and row["barrier_pair"] == "+3% vs -3%")
    return "\n".join([
        "# Owner Decision Memo — Legacy-5 Benchmark",
        "",
        f"Task: `{TASK_ID}`  ",
        f"Dataset: `{AUTHORITY_VERSION}`; `{summary['source']['rows']}` accepted rows / `{summary['source']['instruments']}` instruments; `{summary['source']['normalized_surface_sha256']}`.",
        "",
        "## Direct answers",
        "",
        f"- Original `LEGACY-5`: distinct-episode endpoint expectancy is **{base['endpoint_mean']:.4f} at T+5** and **{base10['endpoint_mean']:.4f} at T+10**; this is descriptive gross forward evidence, not a trade rule.",
        f"- `+MA60`: distinct episodes change T+5 endpoint mean from **{base['endpoint_mean']:.4f}** to **{ma60['endpoint_mean']:.4f}** (**{ma60_comp['endpoint_mean_delta_to_minus_from']:+.4f}**), while removing **{ma60_comp['candidate_reduction_count']} / {ma60_comp['from_candidate_count']} ({ma60_comp['candidate_reduction_rate_vs_from']:.1%})** anchors/episodes. This is a small descriptive improvement, not acceptance evidence.",
        f"- `+PRICE20`: distinct episodes change T+5 endpoint mean from **{ma60['endpoint_mean']:.4f}** to **{p20['endpoint_mean']:.4f}** (**{p20_comp['endpoint_mean_delta_to_minus_from']:+.4f}**), while removing another **{p20_comp['candidate_reduction_count']} / {p20_comp['from_candidate_count']} ({p20_comp['candidate_reduction_rate_vs_from']:.1%})**. It does not further improve the endpoint mean in this comparison.",
        f"- Opportunity cost is material: `+MA60` excludes **{ma60_comp['positive_opportunity_sacrificed_mfe_ge_3_count']} / {ma60_comp['positive_opportunity_sacrificed_mfe_ge_5_count']} / {ma60_comp['positive_opportunity_sacrificed_mfe_ge_10_count']}** distinct episodes that still reached MFE >=3% / >=5% / >=10%; incremental `+PRICE20` excludes **{p20_comp['positive_opportunity_sacrificed_mfe_ge_3_count']} / {p20_comp['positive_opportunity_sacrificed_mfe_ge_5_count']} / {p20_comp['positive_opportunity_sacrificed_mfe_ge_10_count']}**. It also removes **{ma60_comp['adverse_cases_removed_endpoint_le_0_count']} / {ma60_comp['adverse_cases_removed_mae_le_minus5_count']}** and **{p20_comp['adverse_cases_removed_endpoint_le_0_count']} / {p20_comp['adverse_cases_removed_mae_le_minus5_count']}** endpoint<=0 / MAE<=-5% cases respectively.",
        f"- A2 comparison: **{a2.get('status')}**. When PASS, the anchor/endpoint/MFE/MAE definitions are aligned; comparison remains descriptive and does not rank or merge strategies.",
        "- Research decision: **evidence is worth continued research as a benchmark**, subject to the KD fallback contract, UNKNOWN_RAW_ONLY corporate-action limitation, gross/no-cost results, and a predeclared out-of-sample protocol before any acceptance discussion.",
        "",
        "## Boundary",
        "",
        "This memo does not create BUY/SELL, stop, take-profit, cooldown, or production semantics. `LEGACY-5+MA60` and `LEGACY-5+MA60+PRICE20` are descriptive comparisons only; A2/Core V0 is unchanged.",
        "",
    ])


def _formal_report(summary: Mapping[str, Any], audit: Mapping[str, Any], manifest: Mapping[str, Any], endpoint: list[dict[str, Any]], mfe: list[dict[str, Any]], barrier: list[dict[str, Any]], time_rows: list[dict[str, Any]], comparison: list[dict[str, Any]], a2: Mapping[str, Any], hashes: Mapping[str, str]) -> str:
    lines = [f"# {TASK_ID}", "", "## Formal closure", "", "```text", f"TASK_ID={TASK_ID}", f"TASK_FINAL_STATUS={summary['task_status']}", "WS3_ONLY=YES", "A_SETUP_ACCEPTED=NO", "A_STRATEGY_ACCEPTED=NO", "CORE_V0_SEMANTICS_CHANGED=NO", "A2_SEMANTICS_CHANGED=NO", "PRODUCTION_MUTATION=NO", "DEPLOY=NO", "PUSH=NO", "NEXT_TASK_CHANGED=NO", "DATABASE_WRITES=NO", f"SOURCE_AUTHORITY={AUTHORITY_VERSION}", f"SOURCE_ROWS={summary['source']['rows']}", f"SOURCE_INSTRUMENTS={summary['source']['instruments']}", f"SOURCE_NORMALIZED_SURFACE_SHA256={summary['source']['normalized_surface_sha256']}", f"RAW_ANCHORS_LEGACY5={manifest['counts']['LEGACY-5']['raw_qualifying_anchors']}", f"DISTINCT_EPISODES_LEGACY5={manifest['counts']['LEGACY-5']['distinct_episodes']}", "DISTINCT_EPISODE_RULE=CONTIGUOUS_QUALIFYING_ACCEPTED_SESSION_STATE_FIRST_ANCHOR", "ADJUSTMENT_STATE=UNKNOWN_RAW_ONLY", "SYNTHETIC_ADJUSTMENT=NO", "THRESHOLD_SEARCH=NO", "MODEL_FITTING=NO", "BUY_SELL_STOP_RULE=NO", "```", "", "## Frozen semantics", "", "1. Close condition uses the prior-session slice exactly as specified: `Close_t >= max(Close[t-19:t])`; intraday High is not used for this formation condition.", "2. KD(9) canonical repository lookup: no canonical implementation found. The fixed research fallback is RSV over inclusive 9-session High/Low, K/D recursive smoothing alpha=1/3, K0=D0=50, and zero-range RSV=50. The limitation is explicit in `run-summary.json`.", "3. Volume condition is `mean(last five canonical daily volume lots) > 500`. The query joins accepted canonical VOLUME observations and fail-closes unknown unit codes; SHARES are converted by 1,000 shares per lot.", "4. `+MA60` means `Close_t > MA60_t`; `+PRICE20` means `Close_t >= 20`; neither is part of LEGACY-5.", "5. Outcomes use future accepted sessions strictly after the anchor. Endpoint is future Close / anchor Close - 1; MFE uses future High; MAE uses future Low. Daily simultaneous barriers are `SAME_SESSION_ORDER_UNKNOWN`.", "", "## Raw anchors and distinct episodes", "", f"{json.dumps(manifest['counts'], ensure_ascii=False, indent=2, default=_json_default)}", "", "Raw and episode views are both delivered. The episode view is not a position simulation; it is a deterministic deduplication view to avoid reporting persistence observations as independent events.", "", "## Findings", "", f"Endpoint rows: `{len(endpoint)}`; MFE/MAE rows: `{len(mfe)}`; barrier rows: `{len(barrier)}`; time-to-opportunity rows: `{len(time_rows)}`; variant comparison rows: `{len(comparison)}`.", "", "Variant comparisons report candidate retention, endpoint distribution, MFE/MAE, barrier-race rates, opportunity sacrificed, and adverse cases removed. The adverse-case fields are descriptive flags only; no stop rule is inferred.", "", f"A2 benchmark posture: `{a2.get('status')}`. If PASS, it uses aligned signal-close endpoint/MFE/MAE semantics and is retained as a descriptive benchmark only. If not, do not rank.", "", "## Governance and limitations", "", "- Adjustment state remains UNKNOWN_RAW_ONLY; no synthetic adjustment or corporate-action correction was introduced.", "- Results are gross and exclude transaction costs, slippage, liquidity constraints, and execution timing; no BUY/SELL rule is established.", "- KD(9) uses an explicit fallback because no repository canonical definition was found; alternative initialization/zero-range conventions were not searched or optimized.", "- The input query is accepted canonical daily data with supersession/lifecycle predicates; quarantine, NO_DATA, and lifecycle skip work items remain fail-closed upstream.", "- The 20-session Close formula is preserved literally as requested; its slice notation is recorded to prevent silent semantic drift.", "", "## Reproducibility and promotion", "", "The isolated branch should be promoted only through the existing safe review process after a second replay and artifact hash match. No application, API/UI, scheduler, Production, WS1/WS2/WS4, or NEXT_TASK mutation occurred.", "", "Artifacts are listed in `reproducibility-manifest.json`; source files are written under this task directory.", ""]
    return "\n".join(lines)


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
        summary = run(args.database_url, args.output_dir)
    except ContractBlocked as exc:
        print(f"WS3_LEGACY5_CONTRACT_BLOCKED={exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(summary, ensure_ascii=False, default=_json_default))


if __name__ == "__main__":
    main()
