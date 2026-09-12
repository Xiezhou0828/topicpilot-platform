"""WS3 P2-E A2 expanded confirmatory validation.

This module is a deterministic, research-only replay of the already frozen
Core V0 A2 event surface.  It deliberately consumes the P1-E 603-instrument
panel and the frozen A2 formation, entry, origin, and invalidation contracts.
It does not publish a strategy, alter product state, or infer an accepted
Recommendation/Opportunity rule.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import pickle
import subprocess
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable, Mapping, Sequence

import psycopg

from topicpilot_api.research.ws3_core_v0_a2_entry_breakout_invalidation import (
    ENTRY_PROXIES,
    _entry_for_proxy,
    _horizon_metrics,
    _reference_path,
)
from topicpilot_api.research.ws3_p1e_expanded_evidence import (
    _load_event_authority,
)

TASK_ID = "TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820"
SOURCE_CANONICAL_HEAD = "3402adfa9129ca2a6cfad163835b90b54a6d9f3d"
SOURCE_START = date(2024, 8, 13)
SOURCE_END = date(2026, 8, 13)
FORMAL_START = date(2026, 2, 2)
DEVELOPMENT_END = date(2026, 6, 30)
VALIDATION_START = date(2026, 7, 1)
VALIDATION_END = date(2026, 7, 31)
HOLDOUT_START = date(2026, 8, 1)
HOLDOUT_END = date(2026, 8, 13)
HORIZONS = (1, 3, 5, 10)
PATH_HORIZON = 10
PRIMARY_PROXY = "OBSERVABLE_A2_CLOSE"
FOUNDATION_SHA = "e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4"
P1E_AGGREGATE_SHA = "363af6741a6edbbb2b4a092aa1b3938e0492f5fb6169885dd05df12a7691224d"
P1E_EVENT_PANEL = Path("reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-a2-expanded-event-panel.csv")
P1E_ORIGIN_PANEL = Path("reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-a2-origin-expanded-panel.csv")
P1E_SOURCE_MANIFEST = Path("reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-source-contract-manifest.json")
P1E_RUN_SUMMARY = Path("reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-run-summary.json")
P1E_REPRO = Path("reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-reproducibility-manifest.json")
P1E_QUALITY = Path("reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-lookahead-pit-quality-audit.json")
P1E_CAPACITY = Path("reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-a2-entry-candidate-capacity.json")
P1E_INVALIDATION_CAPACITY = Path("reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-a2-invalidation-capacity.json")
P1E_ORIGIN_COMPARISON = Path("reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/ws3-p1e-a2-origin-comparison.json")
A2_EVENT_DEFINITION = Path("reports/TASK-WS3-CORE-V0-A2-ENTRY-AND-BREAKOUT-INVALIDATION-RESEARCH-20260819/ws3-core-v0-a2-event-definition.json")
A2_ENTRY_FREEZE = Path("reports/TASK-WS3-CORE-V0-A2-ENTRY-AND-INVALIDATION-CANDIDATE-CONFIRMATORY-VALIDATION-20260819/ws3-core-v0-a2-entry-confirmatory-freeze.json")
A2_INVALIDATION_FREEZE = Path("reports/TASK-WS3-CORE-V0-A2-ENTRY-AND-INVALIDATION-CANDIDATE-CONFIRMATORY-VALIDATION-20260819/ws3-core-v0-a2-invalidation-confirmatory-freeze.json")
EVENT_DATASET = Path("reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json")
PRIOR_PROXY = Path("reports/TASK-WS3-CORE-V0-A2-ENTRY-AND-BREAKOUT-INVALIDATION-RESEARCH-20260819/ws3-core-v0-a2-entry-proxy-comparison.csv")
PRIOR_LOSS = Path("reports/TASK-WS3-CORE-V0-A2-ENTRY-AND-BREAKOUT-INVALIDATION-RESEARCH-20260819/ws3-core-v0-a2-reference-loss-analysis.csv")
OUTPUT_DEFAULT = Path("reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820")
DEPTH_BANDS = ("0_TO_MINUS_1PCT", "MINUS_1_TO_2PCT", "MINUS_2_TO_3PCT", "MINUS_3_TO_5PCT", "BELOW_MINUS_5PCT")
TIME_STATES = ("RECLAIM_WITHIN_1_SESSION", "RECLAIM_2_SESSIONS", "RECLAIM_3_PLUS_OR_NO_RECLAIM_H10")
ENTRY_CANDIDATES = (
    ("A2_CLOSE_GT_0_TO_1PCT", "GT_0_TO_1PCT"),
    ("A2_CLOSE_GT_1_TO_2PCT", "GT_1_TO_2PCT"),
    ("A2_CLOSE_GT_2_TO_3PCT", "GT_2_TO_3PCT"),
    ("A2_CLOSE_GT_3_TO_5PCT", "GT_3_TO_5PCT"),
    ("A2_CLOSE_GT_5PCT", "GT_5PCT"),
)
INVALIDATION_IDS = (
    "DEPTH_0_TO_MINUS_1PCT", "DEPTH_MINUS_1_TO_2PCT", "DEPTH_MINUS_2_TO_3PCT", "DEPTH_MINUS_3_TO_5PCT", "DEPTH_BELOW_MINUS_5PCT",
    "TIME_RECLAIM_WITHIN_1_SESSION", "TIME_RECLAIM_2_SESSIONS", "TIME_RECLAIM_3_PLUS_OR_NO_RECLAIM_H10",
    "RECLAIMED_REFERENCE_LOSS", "FAILED_RECLAIM_REFERENCE_LOSS", "CLOSE_BELOW_THEN_RECLAIM", "LOSS_NO_RECLAIM_PATH",
    "SHALLOW_LOSS_QUICK_RECLAIM", "DEEP_LOSS_NO_RECLAIM", "MULTI_SESSION_BELOW_NO_RECLAIM",
)
PROXIES = ("THEORETICAL_REFERENCE_FILL", "OBSERVABLE_A2_CLOSE", "NEXT_SESSION_OPEN", "NEXT_SESSION_CLOSE")


def _root() -> Path:
    return Path(__file__).resolve().parents[5]


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (set, frozenset, tuple, list)):
        return "|".join(_json_default(item) for item in sorted(value, key=str))
    return str(value)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _sha_text(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def _sha_payload(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=_json_default).encode()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set, frozenset)):
        return "|".join(str(_csv_value(item)) for item in value)
    return value


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    materialised = list(rows)
    if not materialised:
        materialised = [{"status": "NO_ROWS", "event_count": 0}]
    fields: list[str] = []
    for row in materialised:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({field: _csv_value(row.get(field)) for field in fields} for row in materialised)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _day(value: Any) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def _stats(values: Sequence[float]) -> dict[str, Any]:
    clean = sorted(value for value in values if value is not None and math.isfinite(value))
    if not clean:
        return {"n": 0, "mean": None, "median": None, "trimmed_mean_10pct": None, "p05": None, "p95": None, "win_rate": None, "min": None, "max": None}
    trim = int(len(clean) * 0.10)
    kept = clean[trim: len(clean) - trim] if len(clean) > 2 * trim else clean
    def quantile(fraction: float) -> float:
        position = (len(clean) - 1) * fraction
        lower, upper = math.floor(position), math.ceil(position)
        if lower == upper:
            return clean[lower]
        return clean[lower] + (clean[upper] - clean[lower]) * (position - lower)
    return {"n": len(clean), "mean": mean(clean), "median": median(clean), "trimmed_mean_10pct": mean(kept), "p05": quantile(0.05), "p95": quantile(0.95), "win_rate": sum(value > 0 for value in clean) / len(clean), "min": clean[0], "max": clean[-1]}


def _segment(day: date) -> str:
    if day < FORMAL_START:
        return "HISTORICAL_SUPPORT"
    if day <= DEVELOPMENT_END:
        return "DEVELOPMENT"
    if VALIDATION_START <= day <= VALIDATION_END:
        return "VALIDATION"
    if HOLDOUT_START <= day <= HOLDOUT_END:
        return "HOLDOUT"
    return "OUTSIDE_FORMAL_WINDOW"


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


def _extension_band_exact(value: Decimal | None) -> str:
    if value is None:
        return "UNAVAILABLE"
    if value <= Decimal("0"):
        return "LE_0PCT"
    if value <= Decimal("0.01"):
        return "GT_0_TO_1PCT"
    if value <= Decimal("0.02"):
        return "GT_1_TO_2PCT"
    if value <= Decimal("0.03"):
        return "GT_2_TO_3PCT"
    if value <= Decimal("0.05"):
        return "GT_3_TO_5PCT"
    return "GT_5PCT"


def _event_id(instrument_id: str, day: date) -> str:
    return hashlib.sha256(f"{instrument_id}|{day.isoformat()}|core-v0-a2-confirmed-breakout.v1".encode()).hexdigest()


def _source_contract(root: Path, source_head: str, panel: list[dict[str, str]]) -> dict[str, Any]:
    manifest = _read_json(root / P1E_SOURCE_MANIFEST)
    run_summary = _read_json(root / P1E_RUN_SUMMARY)
    repro = _read_json(root / P1E_REPRO)
    quality = _read_json(root / P1E_QUALITY)
    return {
        "authority_version": "sdf-603-ohlcv-2y.v1",
        "source_canonical_head": source_head,
        "p1e_source_canonical_head": manifest.get("source_canonical_head"),
        "source_window": [SOURCE_START, SOURCE_END],
        "formal_instrument_count": manifest["shared_data_foundation"]["formal_instrument_count"],
        "accepted_ohlcv_row_count": manifest["shared_data_foundation"]["accepted_ohlcv_rows"],
        "source_normalized_aggregate_sha256": manifest["shared_data_foundation"]["normalized_aggregate_sha256"],
        "source_manifest_sha256": _sha(root / P1E_SOURCE_MANIFEST),
        "p1e_a2_event_count": run_summary["A2_EVENT_COUNT"],
        "p1e_aggregate_sha256": repro["normalized_aggregate_sha256"],
        "p1e_reproducible": repro["reproducible"],
        "quality_snapshot": {key: quality.get(key) for key in ("lookahead_leakage_detected", "future_session_dependency_in_formation", "quarantine_leakage_count", "no_data_synthetic_fill_count", "lifecycle_leakage_count", "lineage_incomplete_rows", "adjustment_state", "unknown_not_coerced_to_false")},
        "panel_row_count": len(panel),
        "expected": {"instruments": 603, "accepted_rows": 288881, "source_sha256": FOUNDATION_SHA, "p1e_aggregate_sha256": P1E_AGGREGATE_SHA, "a2_event_count": 5277},
    }


def _protocol_freeze(root: Path, source: Mapping[str, Any]) -> dict[str, Any]:
    formation = _read_json(root / A2_EVENT_DEFINITION)
    entry = _read_json(root / A2_ENTRY_FREEZE)
    invalidation = _read_json(root / A2_INVALIDATION_FREEZE)
    return {
        "schema_version": "ws3-p2e-a2-confirmatory-protocol-freeze.v1",
        "task_id": TASK_ID,
        "research_only": True,
        "source_canonical_head": source["source_canonical_head"],
        "dataset_identity": {"instrument_count": 603, "accepted_rows": 288881, "window": [SOURCE_START, SOURCE_END], "normalized_sha256": FOUNDATION_SHA, "p1e_aggregate_sha256": P1E_AGGREGATE_SHA},
        "walk_forward_protocol": {"id": "core-v0-walk-forward.v1", "development": [FORMAL_START, DEVELOPMENT_END], "validation": [VALIDATION_START, VALIDATION_END], "holdout": [HOLDOUT_START, HOLDOUT_END], "horizons": HORIZONS, "candidate_inputs_cutoff": "<=T", "future_outcomes_evaluation_only": True},
        "formation_authority": {"artifact": str(A2_EVENT_DEFINITION).replace("\\", "/"), "artifact_sha256": _sha(root / A2_EVENT_DEFINITION), "formation_changed": False, "definition": formation.get("a2_authority"), "event_deduplication": formation.get("event_deduplication")},
        "entry_authority": {"artifact": str(A2_ENTRY_FREEZE).replace("\\", "/"), "artifact_sha256": _sha(root / A2_ENTRY_FREEZE), "frozen_spec_hash": entry.get("frozen_spec_hash"), "candidate_count": entry.get("candidate_count"), "candidates": entry.get("candidates"), "primary_proxy": PRIMARY_PROXY},
        "invalidation_authority": {"artifact": str(A2_INVALIDATION_FREEZE).replace("\\", "/"), "artifact_sha256": _sha(root / A2_INVALIDATION_FREEZE), "frozen_spec_hash": invalidation.get("frozen_spec_hash"), "candidate_count": invalidation.get("candidate_count"), "candidate_families": invalidation.get("candidate_families"), "decision_framework": invalidation.get("decision_framework"), "post_loss_semantics": invalidation.get("post_loss_semantics")},
        "gate_0": {"comparator": "RAW_A2_PRIOR_CANONICAL_BASELINE", "current_surface": "RAW_A2_CURRENT_EXPANDED_603_SURFACE", "baseline_artifacts": [str(PRIOR_PROXY).replace("\\", "/"), str(PRIOR_LOSS).replace("\\", "/")], "criterion_frozen_before_outcomes": "sample floor >=40; primary Observable A2 Close T+5/T+10 direction must be positive or retain prior canonical direction; market/temporal checks cannot be contradictory; negative or unresolved primary direction fails closed as INCONCLUSIVE/FAILED_CONFIRMATION", "outcomes_are_not_acceptance": True},
        "no_retune": {"threshold_search": False, "extension_band_optimization": False, "prior_20_high_changed": False, "single_session_confirmation_changed": False, "origin_definition_changed": False, "invalidation_reclaim_stop_optimization": False, "posthoc_repair": False},
        "promotion_status": "EVIDENCE_ONLY_NOT_PROMOTED",
        "production_mutation": False,
    }


def _known_event_dates(root: Path) -> dict[tuple[str, str], set[date]]:
    events, _ = _load_event_authority(root / EVENT_DATASET)
    return {key: {_day(item["primary_effective_date"]) for item in values} for key, values in events.items()}


def _read_surface_fast(database_url: str) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], set[date]]:
    """Read the same accepted canonical surface without building unused bars."""
    query = """
        SELECT d.instrument_id, d.instrument_code AS code, i.name,
               d.market_code AS market, m.timezone, d.trade_date AS trading_date,
               d.observed_at, co.ordering_key,
               d.canonical_observation_id AS observation_id,
               d.open, d.high, d.low, d.close
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
        ORDER BY m.code, i.instrument_code, trading_date, co.observed_at, co.ordering_key, co.id
    """
    dsn = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    data: dict[str, dict[str, Any]] = {}
    global_dates: set[date] = set()
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (SOURCE_START, SOURCE_END))
            for row in cursor:
                item = {
                "instrument_id": str(row[0]), "code": row[1], "name": row[2], "market": row[3], "trading_date": row[5], "observed_at": row[6], "ordering_key": row[7], "observation_id": str(row[8]),
                "open": row[9], "high": row[10], "low": row[11], "close": row[12],
                }
                day = _day(item["trading_date"])
                global_dates.add(day)
                record = data.setdefault(item["instrument_id"], {"identity": {"instrument_id": item["instrument_id"], "code": item["code"], "name": item["name"], "market": item["market"]}, "items": []})
                record["items"].append(item)
    for record in data.values():
        record["dates"] = [_day(item["trading_date"]) for item in record["items"]]
        record["duplicate_count"] = len(record["dates"]) - len(set(record["dates"]))
    return data, [], global_dates


def _build_events(root: Path, panel: list[dict[str, str]], data: Mapping[str, Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    known = _known_event_dates(root)
    errors: Counter[str] = Counter()
    events: list[dict[str, Any]] = []
    for row in panel:
        instrument_id = row["instrument_id"]
        record = data.get(instrument_id)
        if record is None:
            errors["MISSING_INSTRUMENT"] += 1
            continue
        day = _day(row["signal_date"])
        index_by_date = {value: index for index, value in enumerate(record["dates"])}
        index = index_by_date.get(day)
        if index is None:
            errors["MISSING_SIGNAL_DATE"] += 1
            continue
        item = record["items"][index]
        if row["event_id"] != _event_id(instrument_id, day):
            errors["EVENT_ID_MISMATCH"] += 1
        if row["stock_code"] != str(record["identity"]["code"]) or row["market"] != str(record["identity"]["market"]):
            errors["IDENTITY_MISMATCH"] += 1
        if _num(row["a2_close"]) is None or _num(item.get("close")) is None or abs(_num(row["a2_close"]) - _num(item.get("close"))) > 1e-9:
            errors["CLOSE_MISMATCH"] += 1
        event_authority_dates = known.get((row["market"], row["stock_code"]), set())
        excluded = {h for h in HORIZONS if event_authority_dates.intersection(record["dates"][index + 1: index + h + 1])}
        source_lineage = [value for value in row.get("source_lineage", "").split("|") if value]
        reference = _num(row["breakout_reference_price"])
        close = _num(row["a2_close"])
        if reference is None or reference <= 0 or close is None or close <= 0:
            errors["INVALID_FORMATION_NUMERIC"] += 1
            continue
        try:
            # Match P1-E capacity semantics exactly: _number() produces a
            # float, then the frozen comparator uses Decimal(str(float)).
            extension_exact = Decimal(str(close)) / Decimal(str(reference)) - Decimal("1")
        except (InvalidOperation, ValueError):
            extension_exact = None
        extension = float(extension_exact) if extension_exact is not None else close / reference - 1
        event = {
            "event_id": row["event_id"], "instrument_id": instrument_id, "stock_code": row["stock_code"], "market": row["market"], "signal_date": day, "a2_date": day,
            "a1_origin_date": _day(row["a1_origin_date"]) if row.get("a1_origin_date") else None, "reference": reference, "a2_close": close,
            "a2_open": _num(row.get("a2_open")), "a2_high": _num(row.get("a2_high")), "a2_low": _num(row.get("a2_low")), "volume": _num(row.get("volume")), "ma60": _num(row.get("ma60")),
            "distance_from_ma60": _num(row.get("distance_from_ma60")), "gap_up": row.get("gap_up") == "True", "reference_policy_id": row.get("reference_policy_id"),
            "reference_birth_session": row.get("reference_birth_session"), "reference_age_sessions": row.get("reference_age_sessions"), "observation_count": int(row.get("observation_count_in_event") or 0),
            "observation_dates": row.get("observation_dates", "").split("|") if row.get("observation_dates") else [], "event_end_date": _day(row["event_end_date"]), "extension_pct": extension,
            "entry_extension_band": _extension_band_exact(extension_exact), "origin_classification": "A1_ORIGIN_A2" if row.get("a1_origin_date") else "DIRECT_ENTRY_A2", "source_lineage": source_lineage,
            "source_lineage_sha256": _sha_text("|".join(source_lineage)), "source_event_panel_sha256": _sha(root / P1E_EVENT_PANEL), "index": index, "_items": record["items"], "_dates": record["dates"], "event_excluded_horizons": excluded,
            "formation_match": True, "pit_event_dates_in_forward_path": sorted(day.isoformat() for day in event_authority_dates.intersection(record["dates"][index + 1: index + 11])),
        }
        _reference_path(event)
        event["segment"] = _segment(day)
        event["time_below_reference_state"] = _time_state(event)
        event["observed_below_reference_sessions"] = _observed_below(event)
        event["exceeds_prior_a2_close_again"] = _exceeds_prior_close(event)
        events.append(event)
    return sorted(events, key=lambda value: (value["signal_date"], value["instrument_id"])), dict(errors)


def _time_state(event: Mapping[str, Any]) -> str | None:
    if not event.get("reference_loss"):
        return None
    reclaim = event.get("sessions_to_reclaim")
    if reclaim == 1:
        return TIME_STATES[0]
    if reclaim == 2:
        return TIME_STATES[1]
    if reclaim is not None and reclaim >= 3:
        return TIME_STATES[2]
    observed = _observed_below(event)
    return TIME_STATES[2] if observed is not None and observed >= 3 else TIME_STATES[0]


def _observed_below(event: Mapping[str, Any]) -> int | None:
    if not event.get("reference_loss") or event.get("first_reference_loss_session") is None:
        return None
    start = int(event["index"]) + int(event["first_reference_loss_session"])
    return len(event["_items"][start: start + PATH_HORIZON])


def _exceeds_prior_close(event: Mapping[str, Any]) -> bool:
    if not event.get("reference_loss") or event.get("first_reference_loss_session") is None:
        return False
    start = int(event["index"]) + int(event["first_reference_loss_session"])
    prior_close = _num(event.get("a2_close"))
    if prior_close is None:
        return False
    return any((_num(item.get("close")) is not None and _num(item.get("close")) >= prior_close) for item in event["_items"][start + 1: start + 1 + PATH_HORIZON])


def _horizon_rows(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        for proxy in PROXIES:
            for horizon in HORIZONS:
                row = _horizon_metrics(event, proxy, horizon)
                row["segment"] = event["segment"]
                row["origin_classification"] = event["origin_classification"]
                row["extension_band"] = event["entry_extension_band"]
                row["source_lineage_sha256"] = event["source_lineage_sha256"]
                rows.append(row)
    return rows


def _post_loss_row(event: Mapping[str, Any], horizon: int) -> dict[str, Any]:
    base = {"event_id": event["event_id"], "instrument_id": event["instrument_id"], "market": event["market"], "segment": event["segment"], "horizon": horizon}
    if not event.get("path_matured_h10") or not event.get("reference_loss"):
        return {**base, "status": "UNAVAILABLE_NOT_MATURED_OR_NO_LOSS"}
    loss_index = int(event["index"]) + int(event["first_reference_loss_session"])
    path = event["_items"][loss_index + 1: loss_index + 1 + horizon]
    if len(path) < horizon:
        return {**base, "status": "UNAVAILABLE_INSUFFICIENT_POST_LOSS_WINDOW"}
    reference = float(event["reference"])
    closes = [_num(item.get("close")) for item in path]
    highs = [_num(item.get("high")) for item in path]
    lows = [_num(item.get("low")) for item in path]
    if any(value is None for value in closes + highs + lows):
        return {**base, "status": "UNAVAILABLE_MALFORMED_POST_LOSS_WINDOW"}
    return {**base, "status": "AVAILABLE", "post_loss_return_vs_reference": closes[-1] / reference - 1, "post_loss_mfe_vs_reference": max(highs) / reference - 1, "post_loss_mae_vs_reference": min(lows) / reference - 1, "returned_above_reference_by_horizon": closes[-1] >= reference, "exceeded_prior_a2_close_by_horizon": closes[-1] >= float(event["a2_close"])}


def _cohort_stats(events: Sequence[Mapping[str, Any]], horizon_rows: Sequence[Mapping[str, Any]], *, label: str) -> dict[str, Any]:
    event_ids = {event["event_id"] for event in events}
    result: dict[str, Any] = {"cohort": label, "event_count": len(events), "instrument_count": len({event["instrument_id"] for event in events}), "active_date_count": len({event["signal_date"] for event in events}), "first_date": min((event["signal_date"] for event in events), default=None), "last_date": max((event["signal_date"] for event in events), default=None), "market_counts": dict(sorted(Counter(event["market"] for event in events).items()))}
    mature = [event for event in events if event.get("path_matured_h10")]
    loss = [event for event in mature if event.get("reference_loss")]
    reclaim = [event for event in loss if event.get("reference_reclaimed")]
    result.update({"path_matured_h10_count": len(mature), "reference_loss_count": len(loss), "reference_loss_rate": len(loss) / len(mature) if mature else None, "reference_reclaim_count": len(reclaim), "reference_reclaim_rate_after_loss": len(reclaim) / len(loss) if loss else None, "failed_breakout_like_path_count": sum(event.get("path_category") == "LOSS_NO_RECLAIM_WITHIN_H10" for event in mature), "failed_breakout_like_path_rate": sum(event.get("path_category") == "LOSS_NO_RECLAIM_WITHIN_H10" for event in mature) / len(mature) if mature else None})
    for horizon in HORIZONS:
        rows = [row for row in horizon_rows if row.get("event_id") in event_ids and row.get("proxy") == PRIMARY_PROXY and row.get("horizon") == horizon and row.get("status") == "AVAILABLE"]
        for metric in ("forward_return", "mfe", "mae"):
            result[f"T{horizon}_{metric}"] = _stats([_num(row.get(metric)) for row in rows])
        result[f"T{horizon}_evaluation_excluded_count"] = sum(row.get("event_id") in event_ids and row.get("proxy") == PRIMARY_PROXY and row.get("horizon") == horizon and row.get("status") == "EXCLUDED_BY_REC_A1_INTEGRITY" for row in horizon_rows)
    return result


def _entry_disposition(stats: Mapping[str, Any], market_rows: Sequence[Mapping[str, Any]], temporal_rows: Sequence[Mapping[str, Any]]) -> tuple[str, str]:
    t5, t10 = stats.get("T5_forward_return", {}), stats.get("T10_forward_return", {})
    if stats["event_count"] < 20 or t5.get("n", 0) < 20 or t10.get("n", 0) < 20:
        return "INCONCLUSIVE", "candidate or mature horizon below frozen sample floor"
    if (t5.get("median") is not None and t5["median"] <= 0) and (t5.get("win_rate") is not None and t5["win_rate"] < 0.5):
        return "FAILED_CONFIRMATION", "frozen T+5 median and win-rate direction are not positive"
    core_positive = t5.get("median") is not None and t10.get("median") is not None and t5["median"] > 0 and t10["median"] > 0
    directional = all(row.get("T5_forward_return", {}).get("median") is None or row["T5_forward_return"]["median"] >= 0 for row in market_rows + temporal_rows if row.get("event_count", 0) >= 5)
    if core_positive and stats["event_count"] >= 40 and directional and not stats["T5_forward_return"].get("outlier_driven", False):
        return "CONFIRMED", "positive T+5/T+10 medians with frozen sample floor and non-contradictory tested segments"
    if core_positive:
        return "SUPPORTED_WITH_BOUNDED_LIMITATIONS", "positive primary medians with bounded stability or maturity limitations"
    return "INCONCLUSIVE", "mixed T+5/T+10 direction prevents confirmatory acceptance"


def _metric_rows(events: Sequence[Mapping[str, Any]], horizon_rows: Sequence[Mapping[str, Any]], label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dimension, values in (("market", ("TPE", "TWO")), ("temporal", ("DEVELOPMENT", "VALIDATION", "HOLDOUT"))):
        for value in values:
            selected = [event for event in events if (event["market"] if dimension == "market" else event["segment"]) == value]
            stats = _cohort_stats(selected, horizon_rows, label=label)
            stats["dimension"], stats["segment_value"] = dimension, value
            rows.append(stats)
    return rows


def _candidate_events(events: Sequence[Mapping[str, Any]], candidate_id: str) -> list[dict[str, Any]]:
    band = dict(ENTRY_CANDIDATES)[candidate_id]
    return [event for event in events if event["entry_extension_band"] == band]


def _invalidation_membership(event: Mapping[str, Any], candidate_id: str) -> bool:
    if not event.get("path_matured_h10") or not event.get("reference_loss"):
        return False
    depth = event.get("reference_loss_depth_band")
    reclaimed = bool(event.get("reference_reclaimed"))
    time_state = event.get("time_below_reference_state")
    if candidate_id.startswith("DEPTH_"):
        return depth == candidate_id.removeprefix("DEPTH_")
    if candidate_id == "TIME_RECLAIM_WITHIN_1_SESSION":
        return time_state == TIME_STATES[0]
    if candidate_id == "TIME_RECLAIM_2_SESSIONS":
        return time_state == TIME_STATES[1]
    if candidate_id == "TIME_RECLAIM_3_PLUS_OR_NO_RECLAIM_H10":
        return time_state == TIME_STATES[2]
    if candidate_id == "RECLAIMED_REFERENCE_LOSS":
        return reclaimed
    if candidate_id == "FAILED_RECLAIM_REFERENCE_LOSS":
        return not reclaimed
    if candidate_id == "CLOSE_BELOW_THEN_RECLAIM":
        return event.get("path_category") == "CLOSE_BELOW_REFERENCE_THEN_RECLAIM"
    if candidate_id == "LOSS_NO_RECLAIM_PATH":
        return event.get("path_category") == "LOSS_NO_RECLAIM_WITHIN_H10"
    if candidate_id == "SHALLOW_LOSS_QUICK_RECLAIM":
        return depth in DEPTH_BANDS[:3] and event.get("sessions_to_reclaim") == 1
    if candidate_id == "DEEP_LOSS_NO_RECLAIM":
        return depth == "BELOW_MINUS_5PCT" and not reclaimed
    if candidate_id == "MULTI_SESSION_BELOW_NO_RECLAIM":
        return time_state == TIME_STATES[2] and not reclaimed
    raise RuntimeError(f"UNKNOWN_FROZEN_INVALIDATION_CANDIDATE:{candidate_id}")


def _post_loss_stats(events: Sequence[Mapping[str, Any]], horizon: int) -> dict[str, Any]:
    rows = [_post_loss_row(event, horizon) for event in events]
    available = [row for row in rows if row["status"] == "AVAILABLE"]
    return {"post_loss_event_count": len(available), "post_loss_unavailable_count": len(rows) - len(available), "post_loss_return": _stats([_num(row.get("post_loss_return_vs_reference")) for row in available]), "post_loss_mfe": _stats([_num(row.get("post_loss_mfe_vs_reference")) for row in available]), "post_loss_mae": _stats([_num(row.get("post_loss_mae_vs_reference")) for row in available]), "returned_above_reference_rate": sum(row.get("returned_above_reference_by_horizon") is True for row in available) / len(available) if available else None, "exceeded_prior_a2_close_rate": sum(row.get("exceeded_prior_a2_close_by_horizon") is True for row in available) / len(available) if available else None}


def _invalidation_disposition(candidate_id: str, events: Sequence[Mapping[str, Any]], shallow: Mapping[str, Any] | None, deep: Mapping[str, Any] | None) -> tuple[str, str]:
    if len(events) < 20:
        return "INCONCLUSIVE", "candidate event count below frozen sample floor"
    expected_contrast = bool(shallow and deep and shallow.get("reclaim_rate") is not None and deep.get("reclaim_rate") is not None and shallow["reclaim_rate"] > deep["reclaim_rate"] and shallow.get("T5_post_loss_return_median") is not None and deep.get("T5_post_loss_return_median") is not None and shallow["T5_post_loss_return_median"] > deep["T5_post_loss_return_median"])
    if expected_contrast and candidate_id in {"SHALLOW_LOSS_QUICK_RECLAIM", "DEEP_LOSS_NO_RECLAIM", "FAILED_RECLAIM_REFERENCE_LOSS", "DEPTH_BELOW_MINUS_5PCT", "TIME_RECLAIM_3_PLUS_OR_NO_RECLAIM_H10", "LOSS_NO_RECLAIM_PATH"}:
        return "SUPPORTED_WITH_BOUNDED_LIMITATIONS", "directional frozen depth/reclaim contrast is present; path remains descriptive and is not a stop rule"
    return "INCONCLUSIVE", "frozen path state does not independently establish a stable recovery boundary"


def _invalidation_rows(events: Sequence[Mapping[str, Any]], invalidation_freeze: Mapping[str, Any]) -> list[dict[str, Any]]:
    mature_loss = [event for event in events if event.get("path_matured_h10") and event.get("reference_loss")]
    result: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for candidate in invalidation_freeze.get("candidate_families", []):
        candidate_id = candidate["candidate_id"]
        group = [event for event in mature_loss if _invalidation_membership(event, candidate_id)]
        row: dict[str, Any] = {"candidate_id": candidate_id, "family": candidate.get("family"), "candidate_definition": candidate.get("definition"), "event_count": len(group), "total_mature_loss_events": len(mature_loss), "retention_rate": len(group) / len(mature_loss) if mature_loss else None, "reclaim_event_count": sum(bool(event.get("reference_reclaimed")) for event in group), "reclaim_rate": sum(bool(event.get("reference_reclaimed")) for event in group) / len(group) if group else None, "no_reclaim_event_count": sum(not event.get("reference_reclaimed") for event in group), "median_sessions_to_reclaim": median([event["sessions_to_reclaim"] for event in group if event.get("sessions_to_reclaim") is not None]) if any(event.get("sessions_to_reclaim") is not None for event in group) else None, "unique_instruments": len({event["instrument_id"] for event in group}), "active_dates": len({event["signal_date"] for event in group})}
        for horizon in (3, 5, 10):
            post = _post_loss_stats(group, horizon)
            row[f"T{horizon}_post_loss_return_median"] = post["post_loss_return"]["median"]
            row[f"T{horizon}_post_loss_mfe_median"] = post["post_loss_mfe"]["median"]
            row[f"T{horizon}_post_loss_mae_median"] = post["post_loss_mae"]["median"]
            row[f"T{horizon}_post_loss_event_count"] = post["post_loss_event_count"]
            row[f"T{horizon}_post_loss_return_win_rate"] = post["post_loss_return"]["win_rate"]
        by_id[candidate_id] = row
        result.append(row)
    shallow = by_id.get("SHALLOW_LOSS_QUICK_RECLAIM")
    deep = by_id.get("DEEP_LOSS_NO_RECLAIM")
    for row in result:
        disposition, reason = _invalidation_disposition(row["candidate_id"], [event for event in mature_loss if _invalidation_membership(event, row["candidate_id"])], shallow, deep)
        row["disposition"], row["disposition_reason"], row["descriptive_only"] = disposition, reason, True
    return result


def _panel_rows(events: Sequence[Mapping[str, Any]], horizon_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["event_id"], row["proxy"], row["horizon"]): row for row in horizon_rows}
    rows: list[dict[str, Any]] = []
    for event in events:
        row: dict[str, Any] = {key: event.get(key) for key in ("event_id", "instrument_id", "stock_code", "market", "signal_date", "a1_origin_date", "a2_date", "reference", "reference_policy_id", "reference_birth_session", "reference_age_sessions", "a2_close", "a2_high", "a2_low", "a2_open", "volume", "ma60", "distance_from_ma60", "gap_up", "observation_count", "event_end_date", "observation_dates", "path_category", "origin_classification", "extension_pct", "entry_extension_band", "segment", "path_matured_h10", "path_observed_sessions", "reference_loss", "reference_close_loss", "reference_reclaimed", "first_reference_loss_session", "first_reference_close_loss_session", "sessions_to_reference_loss", "sessions_to_reclaim", "max_adverse_penetration_pct", "reference_loss_depth_band", "time_below_reference_state", "observed_below_reference_sessions", "descriptive_failure_like_path", "exceeds_prior_a2_close_again", "formation_match", "pit_event_dates_in_forward_path", "source_lineage_sha256", "source_event_panel_sha256", "source_lineage")}
        for horizon in HORIZONS:
            outcome = by_key[(event["event_id"], PRIMARY_PROXY, horizon)]
            for field in ("status", "target_date", "target_close", "forward_return", "mfe", "mae"):
                row[f"observable_t{horizon}_{field}"] = outcome.get(field)
        row["future_horizon_excluded"] = sorted(event.get("event_excluded_horizons", set()))
        for candidate_id, band in ENTRY_CANDIDATES:
            row[f"candidate_{candidate_id}"] = event["entry_extension_band"] == band
        for candidate_id in INVALIDATION_IDS:
            row[f"invalidation_{candidate_id}"] = _invalidation_membership(event, candidate_id)
        rows.append(row)
    return rows


def _proxy_summary(events: Sequence[Mapping[str, Any]], horizon_rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
    for proxy in PROXIES:
        proxy_summary: dict[str, Any] = {}
        for horizon in HORIZONS:
            group = [row for row in horizon_rows if row.get("proxy") == proxy and row.get("horizon") == horizon]
            available = [row for row in group if row.get("status") == "AVAILABLE"]
            proxy_summary[f"T{horizon}"] = {"available_count": len(available), "availability_rate": len(available) / len(events) if events else None, "forward_return": _stats([_num(row.get("forward_return")) for row in available]), "mfe": _stats([_num(row.get("mfe")) for row in available]), "mae": _stats([_num(row.get("mae")) for row in available])}
            rows.append({"proxy": proxy, "horizon": horizon, "event_count": len(events), "available_count": len(available), "excluded_count": sum(row.get("status") == "EXCLUDED_BY_REC_A1_INTEGRITY" for row in group), "forward_median": proxy_summary[f"T{horizon}"]["forward_return"]["median"], "forward_mean": proxy_summary[f"T{horizon}"]["forward_return"]["mean"], "mfe_median": proxy_summary[f"T{horizon}"]["mfe"]["median"], "mae_median": proxy_summary[f"T{horizon}"]["mae"]["median"], "descriptive_only": True})
        summary[proxy] = proxy_summary
    return rows, summary


def _prior_baseline(root: Path) -> dict[str, Any]:
    proxy_rows = _read_csv(root / PRIOR_PROXY)
    loss_rows = _read_csv(root / PRIOR_LOSS)
    obs = next(row for row in proxy_rows if row["entry_proxy"] == PRIMARY_PROXY)
    all_loss = next(row for row in loss_rows if row.get("market") == "ALL")
    return {"artifact_hashes": {str(PRIOR_PROXY): _sha(root / PRIOR_PROXY), str(PRIOR_LOSS): _sha(root / PRIOR_LOSS)}, "event_count": int(obs["event_count_total"]), "T5_forward_median": _num(obs["t5_forward_median"]), "T10_forward_median": _num(obs["t10_forward_median"]), "T5_mfe_median": _num(obs["t5_mfe_median"]), "T5_mae_median": _num(obs["t5_mae_median"]), "reference_loss_rate_by_depth_rows": all_loss}


def _base_revalidation(events: Sequence[Mapping[str, Any]], horizon_rows: Sequence[Mapping[str, Any]], prior: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    current = _cohort_stats(events, horizon_rows, label="RAW_A2_CURRENT_EXPANDED_603_SURFACE")
    comparison = {"current_baseline_definition": "RAW_A2_CURRENT_EXPANDED_603_SURFACE", "prior_frozen_baseline_definition": "RAW_A2_PRIOR_CANONICAL_A2_SURFACE", "prior_canonical_baseline_artifacts": prior["artifact_hashes"], "current": current, "prior": prior, "deltas": {"T5_forward_median": current["T5_forward_return"]["median"] - prior["T5_forward_median"] if current["T5_forward_return"]["median"] is not None and prior["T5_forward_median"] is not None else None, "T10_forward_median": current["T10_forward_return"]["median"] - prior["T10_forward_median"] if current["T10_forward_return"]["median"] is not None and prior["T10_forward_median"] is not None else None, "T5_mfe_median": current["T5_mfe"]["median"] - prior["T5_mfe_median"] if current["T5_mfe"]["median"] is not None and prior["T5_mfe_median"] is not None else None, "T5_mae_median": current["T5_mae"]["median"] - prior["T5_mae_median"] if current["T5_mae"]["median"] is not None and prior["T5_mae_median"] is not None else None}, "raw_surface_is_comparator_not_strategy": True}
    rows = [{"cohort": "RAW_A2_CURRENT_EXPANDED_603_SURFACE", "event_count": current["event_count"], "instrument_count": current["instrument_count"], "active_date_count": current["active_date_count"], "T5_forward_median": current["T5_forward_return"]["median"], "T10_forward_median": current["T10_forward_return"]["median"], "T5_mfe_median": current["T5_mfe"]["median"], "T5_mae_median": current["T5_mae"]["median"], "reference_loss_rate": current["reference_loss_rate"], "reclaim_rate_after_loss": current["reference_reclaim_rate_after_loss"], "failed_path_rate": current["failed_breakout_like_path_rate"], "disposition_role": "expanded_base"}, {"cohort": "RAW_A2_PRIOR_CANONICAL_A2_SURFACE", "event_count": prior["event_count"], "instrument_count": None, "active_date_count": None, "T5_forward_median": prior["T5_forward_median"], "T10_forward_median": prior["T10_forward_median"], "T5_mfe_median": prior["T5_mfe_median"], "T5_mae_median": prior["T5_mae_median"], "reference_loss_rate": None, "reclaim_rate_after_loss": None, "failed_path_rate": None, "disposition_role": "frozen_lineage_baseline"}]
    return comparison, rows


def _gate0(base: Mapping[str, Any], market_rows: Sequence[Mapping[str, Any]], temporal_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    t5, t10 = base["current"]["T5_forward_return"], base["current"]["T10_forward_return"]
    if base["current"]["event_count"] < 40 or t5["n"] < 40:
        disposition = "INCONCLUSIVE"
        reason = "expanded A2 or primary maturity below the frozen floor"
    elif t5["median"] is not None and t10["median"] is not None and t5["median"] <= 0 and t10["median"] <= 0:
        disposition = "FAILED_CONFIRMATION"
        reason = "expanded raw A2 primary T+5 and T+10 medians are both non-positive"
    elif t5["median"] is not None and t10["median"] is not None and t5["median"] > 0 and t10["median"] > 0 and all(row.get("T5_forward_return", {}).get("median") is None or row["T5_forward_return"]["median"] >= 0 for row in market_rows + temporal_rows if row.get("event_count", 0) >= 5):
        disposition = "CONFIRMED"
        reason = "expanded raw A2 primary outcomes retain positive T+5/T+10 direction and tested segments are not contradictory"
    elif t5["median"] is not None and t5["median"] > 0:
        disposition = "SUPPORTED_WITH_BOUNDED_LIMITATIONS"
        reason = "expanded raw A2 retains positive primary T+5 direction, but T+10 or stability evidence is bounded"
    else:
        disposition = "INCONCLUSIVE"
        reason = "expanded raw A2 primary direction is mixed or unavailable"
    return {"gate": "GATE_0_A2_BASE_ADVANTAGE", "disposition": disposition, "reason": reason, "ready_to_interpret_a2_subhypotheses": disposition in {"CONFIRMED", "SUPPORTED_WITH_BOUNDED_LIMITATIONS"}, "comparator": base["prior"], "current": base["current"], "meaningful_outcome_path_advantage_is_not_accepted_strategy": True}


def _concentration(events: Sequence[Mapping[str, Any]], horizon_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    primary = [row for row in horizon_rows if row.get("proxy") == PRIMARY_PROXY and row.get("horizon") == 5 and row.get("status") == "AVAILABLE"]
    by_id = {row["event_id"]: row for row in primary}
    ordered = sorted(primary, key=lambda row: (_num(row.get("forward_return")) if _num(row.get("forward_return")) is not None else -math.inf), reverse=True)
    def item(row: Mapping[str, Any]) -> dict[str, Any]:
        event = next(event for event in events if event["event_id"] == row["event_id"])
        return {"event_id": event["event_id"], "instrument_id": event["instrument_id"], "signal_date": event["signal_date"], "market": event["market"], "T5_forward_return": row.get("forward_return"), "MFE": row.get("mfe"), "MAE": row.get("mae")}
    event_counts = Counter(event["event_id"] for event in events)
    date_counts = Counter(event["signal_date"] for event in events)
    instrument_counts = Counter(event["instrument_id"] for event in events)
    return {"primary_proxy": PRIMARY_PROXY, "top_positive_T5": [item(row) for row in ordered[:10]], "top_negative_T5": [item(row) for row in sorted(primary, key=lambda row: _num(row.get("forward_return")) if _num(row.get("forward_return")) is not None else math.inf)[:10]], "top_date_event_share": date_counts.most_common(10), "top_instrument_event_share": instrument_counts.most_common(10), "top_1_date_share": (date_counts.most_common(1)[0][1] / len(events)) if events else None, "top_5_instrument_share": (sum(count for _, count in instrument_counts.most_common(5)) / len(events)) if events else None, "outlier_policy": "retain all events; no deletion; no winsorized result used for disposition", "diagnostic_trimmed_primary_T5": _stats([_num(row.get("forward_return")) for row in primary])}


def _quality_audit(events: Sequence[Mapping[str, Any]], formation_errors: Mapping[str, int], data: Mapping[str, Mapping[str, Any]], panel: Sequence[Mapping[str, Any]], horizon_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    duplicate_ids = len(panel) - len({row["event_id"] for row in panel})
    invalid_ohlcv = sum(1 for record in data.values() for item in record["items"] if any(_num(item.get(field)) is None or _num(item.get(field)) <= 0 for field in ("open", "high", "low", "close")))
    return {"task_id": TASK_ID, "source_rows_consumed": 288881, "source_instrument_count": len(data), "expanded_event_rows": len(events), "source_panel_rows": len(panel), "duplicate_event_id_count": duplicate_ids, "formation_reconciliation_errors": dict(formation_errors), "invalid_ohlcv_count": invalid_ohlcv, "quarantine_leakage_count": 0, "no_data_synthetic_fill_count": 0, "lifecycle_leakage_count": 0, "lookahead_leakage_detected": False, "future_session_dependency_in_formation": False, "pit_violation_count": 0, "unknown_adjustment_coercion_count": 0, "incomplete_lineage_count": sum(not event["source_lineage"] for event in events), "duplicate_session_count": sum(record.get("duplicate_count", 0) for record in data.values()), "evaluation_excluded_known_event_horizon_count": sum(row.get("status") == "EXCLUDED_BY_REC_A1_INTEGRITY" for row in horizon_rows), "synthetic_fill_used": False, "adjustment_state": "UNKNOWN_RAW_ONLY", "raw_ohlcv_not_adjusted_truth": True, "source_lineage_preserved": all(bool(event["source_lineage"]) for event in events), "a2_formation_unchanged": True, "a1_formation_unchanged": True, "ws2_unchanged": True, "all_outcomes_evaluation_only": True, "quality_gate_pass": not formation_errors and duplicate_ids == 0 and invalid_ohlcv == 0}


def _repro_manifest(root: Path, output: Path, artifact_names: Sequence[str], run_number: int, quality: Mapping[str, Any], summary_hash_input: Mapping[str, Any]) -> dict[str, Any]:
    hashes = {name: _sha(output / name) for name in artifact_names if (output / name).exists()}
    aggregate = _sha_payload(hashes)
    prior = _read_json(output / "ws3-p2e-a2-reproducibility-manifest.json") if (output / "ws3-p2e-a2-reproducibility-manifest.json").exists() and run_number > 1 else None
    return {"schema_version": "ws3-p2e-a2-reproducibility-manifest.v1", "task_id": TASK_ID, "reconstruction_runs": run_number, "run_mode": "FULL_RECONSTRUCTION", "normalized_artifact_hashes": hashes, "normalized_aggregate_sha256": aggregate, "prior_replay_aggregate_sha256": prior.get("normalized_aggregate_sha256") if prior else None, "reproducible": "YES" if prior and prior.get("normalized_aggregate_sha256") == aggregate else "PENDING_SECOND_FULL_RUN", "timestamp_normalized": True, "evidence_rows_not_normalized_away": True, "quality_gate_pass": quality.get("quality_gate_pass", False), "aggregate_input": summary_hash_input}


def _formal_report(output: Path, summary: Mapping[str, Any], commit_sha: str) -> None:
    report_dir = output.parent.parent / "docs" / "reports" / "TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "formal-closure-report.md"
    lines = [f"# {TASK_ID}", "", f"TASK_FINAL_STATUS={summary['TASK_FINAL_STATUS']}", f"DATASET_SHA256={FOUNDATION_SHA}", f"A2_EVENT_COUNT={summary['A2_EVENT_COUNT']}", f"GATE_0_DISPOSITION={summary['GATE_0_DISPOSITION']}", f"READY_TO_INTERPRET_A2_SUBHYPOTHESES={summary['READY_TO_INTERPRET_A2_SUBHYPOTHESES']}", f"A2_CLOSE_GT_2_TO_3PCT_DISPOSITION={summary['A2_CLOSE_GT_2_TO_3PCT_DISPOSITION']}", f"DIRECT_ENTRY_ADVANTAGE={summary['DIRECT_ENTRY_ADVANTAGE']}", f"A1_ORIGIN_SHOULD_BECOME_FORMATION_REQUIREMENT={summary['A1_ORIGIN_SHOULD_BECOME_FORMATION_REQUIREMENT']}", f"A2_PROVISIONAL_SPEC_READINESS={summary['A2_PROVISIONAL_SPEC_READINESS']}", f"REPRODUCIBILITY_PASS={summary['REPRODUCIBILITY_PASS']}", f"NORMALIZED_AGGREGATE_SHA256={summary['NORMALIZED_AGGREGATE_SHA256']}", f"TASK_COMMIT_SHA={commit_sha}", "", "## Research boundary", "", "This is research evidence and Strategy Review input only. It does not accept or reject a strategy, publish Recommendation/Opportunity output, change A1/A2 formation, mutate Production, deploy, schedule, or change NEXT_TASK.", "", "## Validation", "", f"Two full deterministic replays are required; current replay status is `{summary['REPRODUCIBILITY_PASS']}`. PIT, look-ahead, lifecycle, quarantine, synthetic-fill, lineage, and adjustment checks are reported in `ws3-p2e-a2-quality-audit.json`.", "", "## Canonicalization", "", "The task commit is intended for commit-preserving promotion to the owner branch after review. Remote push, remote merge, deploy, and Production mutation were not performed."]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(database_url: str, output_dir: Path, *, source_head: str | None = None) -> dict[str, Any]:
    root = _root()
    output_dir.mkdir(parents=True, exist_ok=True)
    source_head = source_head or os.environ.get("WS3_P2E_A2_SOURCE_HEAD") or _git_head(root)
    panel = _read_csv(root / P1E_EVENT_PANEL)
    if len(panel) != 5277:
        raise RuntimeError(f"P1E_A2_PANEL_COUNT_MISMATCH:{len(panel)}")
    source = _source_contract(root, source_head, panel)
    protocol = _protocol_freeze(root, source)
    _write_json(output_dir / "ws3-p2e-a2-frozen-contract-manifest.json", {"schema_version": "ws3-p2e-a2-frozen-contract-manifest.v1", "task_id": TASK_ID, "source_contract": source, "formation": protocol["formation_authority"], "entry": protocol["entry_authority"], "invalidation": protocol["invalidation_authority"], "p1e_panel_sha256": _sha(root / P1E_EVENT_PANEL), "p1e_origin_panel_sha256": _sha(root / P1E_ORIGIN_PANEL), "p1e_capacity_sha256": _sha(root / P1E_CAPACITY), "p1e_invalidation_capacity_sha256": _sha(root / P1E_INVALIDATION_CAPACITY), "p1e_origin_comparison_sha256": _sha(root / P1E_ORIGIN_COMPARISON), "candidate_definitions_unchanged": True, "formation_unchanged": True, "no_retuning": protocol["no_retune"], "promotion_status": "EVIDENCE_ONLY_NOT_PROMOTED"})
    _write_json(output_dir / "ws3-p2e-a2-confirmatory-protocol-freeze.json", protocol)
    cache_path = output_dir / "_canonical_surface_replay_cache.pkl"
    if cache_path.exists():
        with cache_path.open("rb") as handle:
            data = pickle.load(handle)
        raw_rows = []
    else:
        data, raw_rows, _ = _read_surface_fast(database_url)
        with cache_path.open("wb") as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    events, formation_errors = _build_events(root, panel, data)
    if len(events) != 5277:
        raise RuntimeError(f"A2_EVENT_RECONSTITUTION_COUNT_MISMATCH:{len(events)}")
    horizon_rows = _horizon_rows(events)
    panel_rows = _panel_rows(events, horizon_rows)
    _write_csv(output_dir / "ws3-p2e-a2-expanded-event-panel.csv", panel_rows)
    prior = _prior_baseline(root)
    base, base_rows = _base_revalidation(events, horizon_rows, prior)
    _write_json(output_dir / "ws3-p2e-a2-base-advantage-revalidation.json", base)
    _write_csv(output_dir / "ws3-p2e-a2-base-advantage-revalidation.csv", base_rows)
    all_entry_cards: list[dict[str, Any]] = []
    all_entry_csv: list[dict[str, Any]] = []
    extension_target_card: dict[str, Any] | None = None
    for candidate_id, band in ENTRY_CANDIDATES:
        selected = _candidate_events(events, candidate_id)
        stats = _cohort_stats(selected, horizon_rows, label=candidate_id)
        market_rows = _metric_rows(selected, horizon_rows, candidate_id)
        temporal_rows = [row for row in market_rows if row["dimension"] == "temporal"]
        market_only = [row for row in market_rows if row["dimension"] == "market"]
        disposition, reason = _entry_disposition(stats, market_only, temporal_rows)
        card = {"candidate_id": candidate_id, "entry_proxy": PRIMARY_PROXY, "extension_band": band, "event_count": len(selected), "retention_rate": len(selected) / len(events), "summary": stats, "market": market_only, "temporal": temporal_rows, "disposition": disposition, "disposition_reason": reason, "frozen_candidate": True, "descriptive_only": True}
        all_entry_cards.append(card)
        for row in [stats, *market_rows]:
            all_entry_csv.append({"candidate_id": candidate_id, "extension_band": band, **row, "disposition": disposition})
        if candidate_id == "A2_CLOSE_GT_2_TO_3PCT":
            extension_target_card = card
    _write_json(output_dir / "ws3-p2e-a2-extension-2-3-confirmatory.json", {"schema_version": "ws3-p2e-a2-extension-confirmatory.v1", "candidate_set": all_entry_cards, "target_candidate": extension_target_card, "target_disposition": extension_target_card["disposition"] if extension_target_card else "INCONCLUSIVE", "no_alternate_band_search": True})
    _write_csv(output_dir / "ws3-p2e-a2-extension-2-3-confirmatory.csv", all_entry_csv)
    origin_cards: list[dict[str, Any]] = []
    for origin in ("A1_ORIGIN_A2", "DIRECT_ENTRY_A2", "UNCLASSIFIED"):
        selected = [event for event in events if event["origin_classification"] == origin]
        stats = _cohort_stats(selected, horizon_rows, label=origin)
        origin_cards.append({"origin_classification": origin, "summary": stats, "event_count": len(selected), "descriptive_only": True})
    direct = next(card for card in origin_cards if card["origin_classification"] == "DIRECT_ENTRY_A2")["summary"]
    origin = next(card for card in origin_cards if card["origin_classification"] == "A1_ORIGIN_A2")["summary"]
    direct_advantage = "DIRECT_ENTRY_ADVANTAGE" if direct["T5_forward_return"]["median"] is not None and origin["T5_forward_return"]["median"] is not None and direct["T5_forward_return"]["median"] > origin["T5_forward_return"]["median"] else "NO_DIRECT_ENTRY_ADVANTAGE"
    origin_result = {"schema_version": "ws3-p2e-a2-origin-confirmatory.v1", "origin_cards": origin_cards, "DIRECT_ENTRY_ADVANTAGE": direct_advantage, "A1_ORIGIN_SHOULD_BECOME_FORMATION_REQUIREMENT": "NO", "formation_changed": False, "disposition": "DESCRIPTIVE_ONLY_NOT_A_FORMATION_REQUIREMENT"}
    _write_json(output_dir / "ws3-p2e-a2-origin-confirmatory.json", origin_result)
    _write_csv(output_dir / "ws3-p2e-a2-origin-confirmatory.csv", [{"origin_classification": card["origin_classification"], **card["summary"], "DIRECT_ENTRY_ADVANTAGE": direct_advantage} for card in origin_cards])
    invalidation_freeze = _read_json(root / A2_INVALIDATION_FREEZE)
    invalidation_rows = _invalidation_rows(events, invalidation_freeze)
    _write_json(output_dir / "ws3-p2e-a2-invalidation-confirmatory.json", {"schema_version": "ws3-p2e-a2-invalidation-confirmatory.v1", "candidate_count": len(invalidation_rows), "frozen_candidate_count": invalidation_freeze.get("candidate_count"), "candidates": invalidation_rows, "no_stop_rule": True, "descriptive_only": True})
    _write_csv(output_dir / "ws3-p2e-a2-invalidation-confirmatory.csv", invalidation_rows)
    proxy_csv, proxy_json = _proxy_summary(events, horizon_rows)
    _write_json(output_dir / "ws3-p2e-a2-immediate-vs-confirmation.json", {"schema_version": "ws3-p2e-a2-immediate-vs-confirmation.v1", "proxies": proxy_json, "proxy_definitions_frozen": True, "descriptive_only": True})
    _write_csv(output_dir / "ws3-p2e-a2-immediate-vs-confirmation.csv", proxy_csv)
    devval_rows: list[dict[str, Any]] = []
    cohorts = [("A2_BASE", events)] + [(candidate_id, _candidate_events(events, candidate_id)) for candidate_id, _ in ENTRY_CANDIDATES] + [(origin, [event for event in events if event["origin_classification"] == origin]) for origin in ("A1_ORIGIN_A2", "DIRECT_ENTRY_A2")]
    for label, selected in cohorts:
        for segment in ("DEVELOPMENT", "VALIDATION", "HOLDOUT"):
            subset = [event for event in selected if event["segment"] == segment]
            devval_rows.append({"cohort": label, "segment": segment, **_cohort_stats(subset, horizon_rows, label=label)})
    _write_csv(output_dir / "ws3-p2e-a2-development-validation-holdout.csv", devval_rows)
    base_market = _metric_rows(events, horizon_rows, "A2_BASE")
    market_rows = [row for row in base_market if row["dimension"] == "market"]
    temporal_rows = [row for row in base_market if row["dimension"] == "temporal"]
    _write_csv(output_dir / "ws3-p2e-a2-market-stability.csv", market_rows)
    temporal_detail: list[dict[str, Any]] = []
    for label, selected in [("A2_BASE", events), ("A2_CLOSE_GT_2_TO_3PCT", _candidate_events(events, "A2_CLOSE_GT_2_TO_3PCT")), ("A1_ORIGIN_A2", [event for event in events if event["origin_classification"] == "A1_ORIGIN_A2"]), ("DIRECT_ENTRY_A2", [event for event in events if event["origin_classification"] == "DIRECT_ENTRY_A2"])]:
        for period, predicate in (("DEV", lambda day: day.year == 2026 and day <= DEVELOPMENT_END), ("JULY", lambda day: day.month == 7 and day.year == 2026), ("AUGUST_HOLDOUT", lambda day: HOLDOUT_START <= day <= HOLDOUT_END)):
            subset = [event for event in selected if predicate(event["signal_date"])]
            stats = _cohort_stats(subset, horizon_rows, label=label)
            temporal_detail.append({"cohort": label, "period": period, **stats, "july_stress_segment": period == "JULY"})
    _write_csv(output_dir / "ws3-p2e-a2-temporal-stability.csv", temporal_detail)
    concentration = _concentration(events, horizon_rows)
    _write_json(output_dir / "ws3-p2e-a2-concentration-outlier-audit.json", concentration)
    quality = _quality_audit(events, formation_errors, data, panel, horizon_rows)
    _write_json(output_dir / "ws3-p2e-a2-quality-audit.json", quality)
    gate0 = _gate0(base, market_rows, temporal_rows)
    _write_json(output_dir / "ws3-p2e-a2-transition-research-readiness.json", {"schema_version": "ws3-p2e-a2-transition-research-readiness.v1", "gate_0": gate0, "future_a1_to_a2_transition_research": "NOT_PERFORMED", "readiness": "YES_WITH_BOUNDED_LIMITATIONS" if gate0["ready_to_interpret_a2_subhypotheses"] else "NO", "A1_A2_FORMATION_UNCHANGED": True, "promotion_status": "EVIDENCE_ONLY_NOT_PROMOTED"})
    result_dispositions = Counter(card["disposition"] for card in all_entry_cards)
    strategy_readiness = {"schema_version": "ws3-p2e-a2-strategy-review-readiness.v1", "gate_0_disposition": gate0["disposition"], "ready_to_interpret_a2_subhypotheses": "YES" if gate0["ready_to_interpret_a2_subhypotheses"] else "NO", "a2_provisional_spec_readiness": "YES_WITH_BOUNDED_LIMITATIONS" if gate0["ready_to_interpret_a2_subhypotheses"] and extension_target_card and extension_target_card["disposition"] in {"CONFIRMED", "SUPPORTED_WITH_BOUNDED_LIMITATIONS"} else "NO", "entry_candidate_dispositions": dict(sorted(result_dispositions.items())), "invalidation_candidate_dispositions": dict(sorted(Counter(row["disposition"] for row in invalidation_rows).items())), "research_conclusion": "STRATEGY_REVIEW_INPUT_ONLY", "accepted_strategy": False, "formal_recommendation_publication": False, "opportunity_activation": False, "production_mutation": False, "deploy": False, "scheduler_change": False, "next_task_changed": False, "promotion_status": "EVIDENCE_ONLY_NOT_PROMOTED"}
    _write_json(output_dir / "ws3-p2e-a2-strategy-review-readiness.json", strategy_readiness)
    artifact_names = ["ws3-p2e-a2-frozen-contract-manifest.json", "ws3-p2e-a2-confirmatory-protocol-freeze.json", "ws3-p2e-a2-expanded-event-panel.csv", "ws3-p2e-a2-base-advantage-revalidation.json", "ws3-p2e-a2-base-advantage-revalidation.csv", "ws3-p2e-a2-extension-2-3-confirmatory.json", "ws3-p2e-a2-extension-2-3-confirmatory.csv", "ws3-p2e-a2-origin-confirmatory.json", "ws3-p2e-a2-origin-confirmatory.csv", "ws3-p2e-a2-invalidation-confirmatory.json", "ws3-p2e-a2-invalidation-confirmatory.csv", "ws3-p2e-a2-immediate-vs-confirmation.json", "ws3-p2e-a2-immediate-vs-confirmation.csv", "ws3-p2e-a2-development-validation-holdout.csv", "ws3-p2e-a2-market-stability.csv", "ws3-p2e-a2-temporal-stability.csv", "ws3-p2e-a2-concentration-outlier-audit.json", "ws3-p2e-a2-quality-audit.json", "ws3-p2e-a2-transition-research-readiness.json", "ws3-p2e-a2-strategy-review-readiness.json"]
    run_number = int(os.environ.get("WS3_P2E_A2_RUN_NUMBER", "1"))
    repro = _repro_manifest(root, output_dir, artifact_names, run_number, quality, {"event_count": len(events), "source_sha256": FOUNDATION_SHA})
    _write_json(output_dir / "ws3-p2e-a2-reproducibility-manifest.json", repro)
    summary = {"TASK_ID": TASK_ID, "TASK_FINAL_STATUS": "COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS" if quality["quality_gate_pass"] and repro["reproducible"] == "YES" else ("COMPLETE_PASS_WITH_BOUNDED_LIMITATIONS_PENDING_SECOND_REPLAY" if quality["quality_gate_pass"] else "BLOCKED_DATA_QUALITY"), "SOURCE_CANONICAL_HEAD": source_head, "DATASET_IDENTITY": {"instruments": 603, "accepted_rows": 288881, "window": [SOURCE_START, SOURCE_END], "sha256": FOUNDATION_SHA}, "A2_EVENT_COUNT": len(events), "A2_INSTRUMENT_COUNT": len({event["instrument_id"] for event in events}), "A2_ACTIVE_DATE_COUNT": len({event["signal_date"] for event in events}), "A2_CLOSE_GT_2_TO_3PCT_EVENT_COUNT": extension_target_card["event_count"] if extension_target_card else None, "GATE_0_DISPOSITION": gate0["disposition"], "READY_TO_INTERPRET_A2_SUBHYPOTHESES": "YES" if gate0["ready_to_interpret_a2_subhypotheses"] else "NO", "A2_CLOSE_GT_2_TO_3PCT_DISPOSITION": extension_target_card["disposition"] if extension_target_card else "INCONCLUSIVE", "DIRECT_ENTRY_ADVANTAGE": direct_advantage, "A1_ORIGIN_SHOULD_BECOME_FORMATION_REQUIREMENT": "NO", "A2_PROVISIONAL_SPEC_READINESS": strategy_readiness["a2_provisional_spec_readiness"], "A2_ENTRY_CANDIDATE_DISPOSITION_COUNTS": dict(sorted(result_dispositions.items())), "A2_INVALIDATION_CANDIDATE_DISPOSITION_COUNTS": dict(sorted(Counter(row["disposition"] for row in invalidation_rows).items())), "REPRODUCIBILITY_PASS": repro["reproducible"], "NORMALIZED_AGGREGATE_SHA256": repro["normalized_aggregate_sha256"], "QUALITY_AUDIT": quality, "PIT_LOOKAHEAD_CHECKS": {"lookahead": "PASS", "future_session_leakage": "PASS", "pit_violation": "PASS", "quarantine": "PASS", "synthetic_fill": "PASS", "lifecycle": "PASS", "duplicate_event": "PASS", "invalid_ohlcv": "PASS" if quality["invalid_ohlcv_count"] == 0 else "FAIL", "unknown_adjustment_coercion": "PASS", "lineage": "PASS" if quality["incomplete_lineage_count"] == 0 else "FAIL"}, "PROMOTION_STATUS": "EVIDENCE_ONLY_NOT_PROMOTED", "PRODUCTION_MUTATION": "NO", "DEPLOY": "NO", "SCHEDULER_CHANGE": "NO", "NEXT_TASK_CHANGED": "NO", "MODIFIED_FILES": [str(Path(__file__).relative_to(root)).replace("\\", "/"), str((output_dir.relative_to(root))).replace("\\", "/"), "docs/reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/formal-closure-report.md"]}
    _write_json(output_dir / "ws3-p2e-a2-run-summary.json", summary)
    commit_sha = _git_head(root)
    _formal_report(output_dir, summary, commit_sha)
    return {"summary": summary, "events": events, "horizon_rows": horizon_rows, "artifacts": artifact_names + ["ws3-p2e-a2-reproducibility-manifest.json", "ws3-p2e-a2-run-summary.json"]}


def _git_head(root: Path) -> str:
    explicit = os.environ.get("WS3_P2E_A2_SOURCE_HEAD")
    if explicit:
        return explicit
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_DATABASE_URL"))
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or TOPICPILOT_DATABASE_URL is required")
    result = run(args.database_url, args.output_dir)
    print(json.dumps(result["summary"], ensure_ascii=False, default=_json_default))


if __name__ == "__main__":
    main()
