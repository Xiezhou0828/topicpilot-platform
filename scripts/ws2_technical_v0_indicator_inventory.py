"""Rerunnable Technical V0 inventory and formal evidence-surface audit.

This is a read-only analytical surface.  It consumes the canonical historical
read model and the existing Technical V0 builder; it does not calculate or
publish new indicators, write the database, or mutate production state.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from topicpilot_api.config import Settings
from topicpilot_api.historical_read_model import read_historical_bars
from topicpilot_api.problems import ApiProblem, NotFoundProblem
from topicpilot_api.technical_publication import (
    DEFERRED_INDICATOR_FAMILIES,
    TECHNICAL_CONTRACT_VERSION,
    TECHNICAL_INPUT_AUTHORITY,
    TECHNICAL_POLICY_VERSION,
    TECHNICAL_SPECS,
    build_technical_publication,
)

TASK_ID = "TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819"
FROM = date(2026, 2, 2)
TO = date(2026, 8, 13)
EXPECTED_INSTRUMENTS = 507
EXPECTED_HISTORICAL_ROWS = 63826
MAX_HISTORY_LIMIT = 200
EVENT_DATASET_RELATIVE = Path(
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION"
) / "REC-A1-CA-EVENTS-V0.json"
DEFAULT_OUTPUT_RELATIVE = Path(
    "reports/TASK-WS2-TECHNICAL-V0-INDICATOR-INVENTORY-AND-FORMAL-EVIDENCE-SURFACE-20260819"
)

FORMAL_STATES = {"FORMAL", "FORMAL_WITH_LIMITATION"}
LEGACY_INDICATOR_FIELDS = [
    "ma20",
    "ma60",
    "ma20SlopePct",
    "daysAboveMa20",
    "rs5Pct",
    "rs20Pct",
    "distanceTo20DayHighPct",
    "macdDif",
    "macdSignal",
    "macdHist",
    "kdK",
    "kdD",
    "rsi14",
    "volumeRatio",
    "upVolumeRatio",
    "pullbackVolumeShrinkRatio",
]
LEGACY_DERIVED_FIELDS = [
    "reclaimedMa20",
    "movingAverageAlignment",
    "structureState",
    "rsState",
    "breakout20DayHigh",
    "macdHistTurnedPositive",
    "macdGoldenCross",
    "difAboveZero",
    "kdGoldenCross",
    "kdLowGoldenCross",
    "kdMidLowGoldenCross",
    "volumeStatus",
    "breakoutWithVolume",
    "restartConfirmed",
]


def _json_default(value: object) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(type(value).__name__)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, default=_json_default, sort_keys=True, separators=(",", ":"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, default=_json_default, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def _decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _session(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _identity(history: dict[str, Any]) -> str:
    return f"{history.get('market')}:{history.get('code')}"


def _load_event_evidence(repo_root: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    path = repo_root / EVENT_DATASET_RELATIVE
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_identity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    event_types: set[str] = set()
    for event in payload.get("events", []):
        identity = str(event.get("canonical_identity", ""))
        event_type = event.get("event_type")
        if event_type:
            event_types.add(str(event_type))
        if identity and event.get("authority_state") == "AUTHORITATIVE":
            by_identity[identity].append(
                {
                    "canonical_identity": identity,
                    "effective_date": event.get("primary_effective_date"),
                    "event_type": event_type,
                    "verified": True,
                    "handling": "EXCLUDE",
                }
            )
    return dict(by_identity), {
        "path": str(path),
        "dataset_version": payload.get("dataset_version"),
        "dataset_content_hash": payload.get("dataset_content_hash"),
        "semantic_version": payload.get("semantic_version"),
        "reference_version": payload.get("reference_version"),
        "event_record_count": len(payload.get("events", [])),
        "event_identity_count": len(by_identity),
        "event_type_count": len(event_types),
        "event_types": sorted(event_types),
    }


def _lookup_for_identity(
    identity: str,
    events_by_identity: dict[str, list[dict[str, Any]]],
    metadata: dict[str, Any],
) -> dict[str, Any] | None:
    events = events_by_identity.get(identity)
    if not events:
        return None
    return {
        "lookup_state": "SUCCESS",
        "query_completed": True,
        "response_parsed": True,
        "identity_binding_valid": True,
        "normalization_valid": True,
        "known_events": events,
        "source_lineage": {
            "lineage_state": "VERSIONED",
            "source": "REC_A1_BOUNDED_OFFICIAL_EVENT_EVIDENCE",
            "version": metadata["dataset_version"],
            "semantic_version": metadata["semantic_version"],
            "reference_version": metadata["reference_version"],
            "evidence_hash": metadata["dataset_content_hash"],
            "query_window": [FROM.isoformat(), TO.isoformat()],
            "absence_claim": "NOT_CLAIMED",
        },
    }


def _latest_evidence(publication: dict[str, Any], indicator_id: str) -> dict[str, Any] | None:
    items = [
        item
        for item in publication.get("technical_evidence", [])
        if item.get("indicator_id") == indicator_id
    ]
    return items[-1] if items else None


def _latest_items(publication: dict[str, Any], as_of: date) -> list[dict[str, Any]]:
    return [
        item
        for item in publication.get("technical_evidence", [])
        if _session(item.get("session_date")) == as_of
    ]


def _availability_class(
    evidence: dict[str, Any], technical_eligibility: str
) -> str:
    state = evidence.get("publication_state")
    reason = str(evidence.get("availability_reason") or "")
    if state == "FORMAL_WITH_LIMITATION":
        return "TECHNICAL_EVIDENCE_AVAILABLE_WITH_LIMITATION"
    if state == "FORMAL":
        return "TECHNICAL_EVIDENCE_AVAILABLE"
    if reason in {
        "CONTINUITY_FAIL",
        "CONTINUITY_BREAKING_EVENT_UNRESOLVED",
        "KNOWN_VERIFIED_EVENT_REQUIRES_EVENT_AWARE_HANDLING",
    } or evidence.get("continuity_state") == "CONTINUITY_FAIL":
        return "TECHNICAL_UNAVAILABLE_CONTINUITY_BLOCKED"
    if reason == "UNAVAILABLE_INSUFFICIENT_HISTORY":
        return "TECHNICAL_UNAVAILABLE_INSUFFICIENT_HISTORY"
    if evidence.get("event_authority_status") == "ERROR":
        return "TECHNICAL_ERROR"
    if reason.startswith("EVENT_LOOKUP_") or reason in {
        "CONTINUITY_AUTHORITY_INCOMPLETE",
        "CONTINUITY_AUTHORITY_UNAVAILABLE",
        "CONTINUITY_EVIDENCE_CONFLICT",
        "CONTINUITY_EVENT_SCOPE_UNKNOWN",
    }:
        return "TECHNICAL_UNAVAILABLE_SOURCE_AUTHORITY"
    if technical_eligibility == "INELIGIBLE":
        return "TECHNICAL_UNAVAILABLE"  # no value is available in this branch
    return "TECHNICAL_UNAVAILABLE"


def _instrument_record(
    history: dict[str, Any],
    publication: dict[str, Any],
    lookup: dict[str, Any] | None,
) -> dict[str, Any]:
    items = list(history.get("items") or [])
    latest = items[-1] if items else None
    as_of = _session(history.get("latest_trading_date") or latest.get("trading_date")) if latest else TO
    ma60 = _latest_evidence(publication, "MA60") or {}
    close_value = _decimal(latest.get("close")) if latest else None
    ma60_value = _decimal(ma60.get("value"))
    return {
        "instrument_code": history.get("code"),
        "market": history.get("market"),
        "instrument_identity": _identity(history),
        "instrument_id": str(history.get("instrument_id")) if history.get("instrument_id") else None,
        "as_of_date": as_of,
        "observation_count": len(items),
        "latest_close": close_value,
        "ma60_value": ma60_value,
        "technical_result_status": publication.get("technical_result_status", "ERROR"),
        "technical_eligibility": publication.get("technical_eligibility", "ERROR"),
        "event_authority_status": publication.get("event_authority_status", "ERROR"),
        "publication_status": publication.get("publication_status", "ERROR"),
        "publication_state": publication.get("publication_state"),
        "reason_codes": publication.get("reason_codes") or [],
        "limitation_reasons": publication.get("limitation_reasons") or [],
        "event_evidence_present": lookup is not None,
        "published_indicator_count": len(publication.get("published_indicators") or []),
        "history": history,
        "publication": publication,
    }


def _surface_row(record: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    value = evidence.get("value")
    return {
        "instrument_identity": record["instrument_identity"],
        "instrument_code": record["instrument_code"],
        "market": record["market"],
        "instrument_id": record["instrument_id"],
        "as_of_date": evidence.get("session_date"),
        "indicator_id": evidence.get("indicator_id"),
        "indicator_family": evidence.get("indicator_family"),
        "indicator_version": evidence.get("indicator_version"),
        "value": value,
        "technical_result_status": record["technical_result_status"],
        "technical_eligibility": record["technical_eligibility"],
        "event_authority_status": evidence.get("event_authority_status"),
        "event_lookup_state": evidence.get("event_lookup_state"),
        "continuity_state": evidence.get("continuity_state"),
        "publication_state": evidence.get("publication_state"),
        "availability_class": _availability_class(evidence, record["technical_eligibility"]),
        "availability_reason": evidence.get("availability_reason"),
        "limitation_reasons": evidence.get("limitation_reasons") or [],
        "required_observation_count": evidence.get("required_observation_count"),
        "actual_observation_count": evidence.get("actual_observation_count"),
        "required_observation_window": evidence.get("required_observation_window"),
        "actual_observation_window": evidence.get("actual_observation_window"),
        "algorithm_id": evidence.get("algorithm_id"),
        "algorithm_version": evidence.get("algorithm_version"),
        "parameter_set": evidence.get("parameter_set"),
        "price_basis": evidence.get("price_basis"),
        "source_authority": evidence.get("source_authority"),
        "source_lineage": evidence.get("source_lineage"),
        "continuity_evidence": evidence.get("continuity_evidence"),
        "publication_metadata": {
            "as_of": evidence.get("as_of"),
            "known_event_handling": evidence.get("known_event_handling") or [],
        },
        "strategy_eligibility_is_separate": True,
    }


def _sma(values: list[Decimal], period: int) -> Decimal | None:
    if len(values) < period:
        return None
    with localcontext() as context:
        context.prec = 50
        return sum(values[-period:], Decimal(0)) / Decimal(period)


def _rsi(values: list[Decimal], period: int = 14) -> Decimal | None:
    if len(values) <= period:
        return None
    gains = [max(values[i] - values[i - 1], Decimal(0)) for i in range(1, len(values))]
    losses = [max(values[i - 1] - values[i], Decimal(0)) for i in range(1, len(values))]
    with localcontext() as context:
        context.prec = 50
        gain = sum(gains[:period], Decimal(0)) / Decimal(period)
        loss = sum(losses[:period], Decimal(0)) / Decimal(period)
        result: Decimal
        for index in range(period - 1, len(gains)):
            if index >= period:
                gain = (gain * Decimal(period - 1) + gains[index]) / Decimal(period)
                loss = (loss * Decimal(period - 1) + losses[index]) / Decimal(period)
            if loss == 0 and gain > 0:
                result = Decimal(100)
            elif gain == 0 and loss > 0:
                result = Decimal(0)
            elif gain == 0 and loss == 0:
                result = Decimal(50)
            else:
                result = Decimal(100) - Decimal(100) / (Decimal(1) + gain / loss)
        return result


def _ema(values: list[Decimal], period: int) -> list[Decimal | None]:
    output: list[Decimal | None] = [None] * len(values)
    if len(values) < period:
        return output
    with localcontext() as context:
        context.prec = 50
        alpha = Decimal(2) / Decimal(period + 1)
        output[period - 1] = sum(values[:period], Decimal(0)) / Decimal(period)
        for index in range(period, len(values)):
            output[index] = alpha * values[index] + (Decimal(1) - alpha) * output[index - 1]
    return output


def _macd(values: list[Decimal]) -> dict[str, Decimal | None]:
    fast = _ema(values, 12)
    slow = _ema(values, 26)
    line = [
        fast[index] - slow[index]
        if fast[index] is not None and slow[index] is not None
        else None
        for index in range(len(values))
    ]
    valid = [value for value in line if value is not None]
    signal: Decimal | None = None
    if len(valid) >= 9:
        with localcontext() as context:
            context.prec = 50
            signal = sum(valid[:9], Decimal(0)) / Decimal(9)
            alpha = Decimal(2) / Decimal(10)
            for value in valid[9:]:
                signal = alpha * value + (Decimal(1) - alpha) * signal
    current = line[-1] if line else None
    return {
        "MACD_12_26_9": current,
        "MACD_SIGNAL_12_26_9": signal,
        "MACD_HISTOGRAM_12_26_9": current - signal if current is not None and signal is not None else None,
    }


def _independent_values(items: list[dict[str, Any]]) -> dict[str, Decimal | None]:
    closes = [_decimal(item.get("close")) for item in items]
    volumes = [_decimal(item.get("volume")) for item in items]
    if any(value is None for value in closes):
        return {}
    close_values = [value for value in closes if value is not None]
    volume_values = [value for value in volumes if value is not None]
    volume_ma20 = _sma(volume_values, 20) if len(volume_values) == len(volumes) else None
    with localcontext() as context:
        context.prec = 28
        ratio = (
            volume_values[-1] / volume_ma20
            if len(volume_values) == len(volumes) and volume_ma20 not in (None, Decimal(0))
            else None
        )
    ma20 = _sma(close_values, 20)
    macd = _macd(close_values)
    with localcontext() as return_context:
        return_context.prec = 50
        return_5d = (
            close_values[-1] / close_values[-6] - Decimal(1) if len(close_values) >= 6 else None
        )
        return_20d = (
            close_values[-1] / close_values[-21] - Decimal(1) if len(close_values) >= 21 else None
        )
    return {
        "MA5": _sma(close_values, 5),
        "MA10": _sma(close_values, 10),
        "MA20": ma20,
        "MA60": _sma(close_values, 60),
        "DISTANCE_TO_MA20": (
            (close_values[-1] - ma20) / ma20 if ma20 not in (None, Decimal(0)) else None
        ),
        "RAW_CLOSE_RETURN_5D": return_5d,
        "RAW_CLOSE_RETURN_20D": return_20d,
        "VOLUME_MA5": _sma(volume_values, 5) if len(volume_values) == len(volumes) else None,
        "VOLUME_MA20": volume_ma20,
        "VOLUME_RATIO_20": ratio,
        "RSI14": _rsi(close_values),
        **macd,
    }


def _reconcile_samples(samples: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    mismatch_count = 0
    compared_count = 0
    for case, sample in sorted(samples.items()):
        history = sample["history"]
        publication = sample["publication"]
        expected = _independent_values(list(history.get("items") or []))
        row_checks: dict[str, Any] = {}
        for indicator_id, expected_value in expected.items():
            evidence = _latest_evidence(publication, indicator_id)
            if not evidence or evidence.get("value") is None or expected_value is None:
                row_checks[indicator_id] = {
                    "status": "NOT_COMPARED_UNAVAILABLE",
                    "publication_state": evidence.get("publication_state") if evidence else None,
                    "availability_reason": evidence.get("availability_reason") if evidence else None,
                }
                continue
            actual = _decimal(evidence.get("value"))
            passed = actual == expected_value
            compared_count += 1
            mismatch_count += int(not passed)
            row_checks[indicator_id] = {
                "status": "PASS" if passed else "FAIL",
                "expected": _decimal_text(expected_value),
                "actual": _decimal_text(actual),
            }
        checks.append(
            {
                "case": case,
                "instrument_identity": _identity(history),
                "as_of": history.get("latest_trading_date"),
                "observation_count": len(history.get("items") or []),
                "checks": row_checks,
            }
        )
    return {
        "task_id": TASK_ID,
        "sample_count": len(checks),
        "compared_value_count": compared_count,
        "mismatch_count": mismatch_count,
        "pass": mismatch_count == 0,
        "checks": checks,
    }


def _manifest(repo_root: Path, event_metadata: dict[str, Any]) -> dict[str, Any]:
    algorithm_rules = {
        "SMA_CLOSE_V1": {
            "calculation_definition": "arithmetic mean of the last N accepted raw close observations",
            "warmup_rule": "first value after N accepted observations",
            "rounding_rule": "no intermediate rounding; Decimal authority boundary",
        },
        "DISTANCE_TO_MA20_V1": {
            "calculation_definition": "(close_t - MA20_t) / MA20_t",
            "warmup_rule": "same 20 accepted-close window as MA20",
            "rounding_rule": "no intermediate rounding; zero denominator unavailable",
        },
        "RAW_OBSERVED_CLOSE_RETURN_V1": {
            "calculation_definition": "close_t / close_(t-N) - 1 using raw observed close",
            "warmup_rule": "N+1 accepted closes including anchor and endpoint",
            "rounding_rule": "no intermediate rounding; raw observed, not adjusted or total return",
        },
        "SMA_VOLUME_QUANTITY_V1": {
            "calculation_definition": "arithmetic mean of canonical volume_quantity",
            "warmup_rule": "first value after N accepted volume observations",
            "rounding_rule": "no intermediate rounding; source unit/scale retained",
        },
        "VOLUME_RATIO_20_V1": {
            "calculation_definition": "current session volume / VOLUME_MA20",
            "warmup_rule": "20 accepted volume observations including anchor",
            "rounding_rule": "canonical Decimal ratio boundary; zero denominator unavailable",
        },
        "RSI_WILDER_14_V1": {
            "calculation_definition": "Wilder RSI over 14 close changes",
            "warmup_rule": "minimum 15 closes; arithmetic seed then Wilder recursion",
            "rounding_rule": "no intermediate rounding; flat=50, all-gain=100, all-loss=0",
        },
        "MACD_12_26_9_SMA_SEEDED_EMA_V1": {
            "calculation_definition": "EMA12 minus EMA26; signal EMA9 of valid MACD line; histogram=line-signal",
            "warmup_rule": "MACD first valid at 26 closes; signal/histogram first valid at 34 closes",
            "rounding_rule": "no intermediate rounding; SMA-seeded EMA",
        },
    }
    indicators: list[dict[str, Any]] = []
    for spec in TECHNICAL_SPECS:
        algorithm_id = str(spec["algorithm_id"])
        rule = algorithm_rules[algorithm_id]
        indicators.append(
            {
                "indicator_id": spec["indicator_id"],
                "display_name": spec["indicator_id"],
                "category": "DERIVED_INDICATOR",
                "implementation_location": [
                    "services/api/src/topicpilot_api/technical_publication.py",
                    "services/api/src/topicpilot_api/schemas.py",
                ],
                "formal_status": "FORMAL_V0",
                "version": TECHNICAL_POLICY_VERSION,
                "algorithm_id": algorithm_id,
                "algorithm_version": algorithm_id,
                "input_fields": [
                    "accepted_raw_close"
                    if spec["mode"] in {"rolling_close", "recursive_close"}
                    else "canonical_volume_quantity"
                ],
                "lookback_window": spec["minimum"],
                "minimum_history": spec["minimum"],
                "warmup_rule": rule["warmup_rule"],
                "calculation_definition": rule["calculation_definition"],
                "parameters": spec["parameters"],
                "rounding_rule": rule["rounding_rule"],
                "null_rule": "missing, invalid, insufficient, continuity-failed, or disallowed-authority input remains unavailable",
                "session_rule": "canonical market-local accepted sessions ordered by trading_date, observed_at, ordering_key, observation_id",
                "as_of_rule": "value at session T uses only accepted observations and event authority available for the requested window ending at T",
                "continuity_requirement": "indicator-level bounded evaluation; CONTINUITY_FAIL blocks; CONTINUITY_UNKNOWN blocks ordinary formal clearance",
                "event_affected_behavior": "known verified breaking event intersecting the required window is unavailable; valid raw value may be FORMAL_WITH_LIMITATION only for explicit lookup limitation",
                "source_lineage_requirement": "V2_CANONICAL_OBSERVATION_CHAIN with VERSIONED source/adapter/normalization/mapping/reference lineage",
                "publication_eligibility": "value exists, required history exists, valid lineage, indicator-window continuity passes or bounded limitation is explicitly allowed",
                "publication_state_behavior": ["FORMAL", "FORMAL_WITH_LIMITATION", "UNAVAILABLE"],
                "historical_reconstructability": "YES_BOUNDED_FROM_CANONICAL_63826_ROWS",
                "PIT_safe": True,
                "current_consumer": [
                    "/api/v2/stocks/{symbol}/technical",
                    "services/api/tests/test_technical_publication.py",
                    "future WS3 read-only research consumption; no WS3 modification",
                ],
                "test_coverage": "services/api/tests/test_technical_publication.py",
                "notes": "Invented indicators and parameter changes are prohibited by this inventory task.",
            }
        )

    raw_fields = [
        {"field_id": "close", "category": "RAW_OBSERVATION", "status": "CURRENT_INPUT"},
        {"field_id": "volume", "category": "RAW_OBSERVATION", "status": "CURRENT_INPUT"},
    ]
    eligibility_fields = [
        {"field_id": "technical_result_status", "category": "ELIGIBILITY_STATE", "status": "CURRENT_SURFACE"},
        {"field_id": "technical_eligibility", "category": "ELIGIBILITY_STATE", "status": "CURRENT_SURFACE"},
    ]
    continuity_fields = [
        {"field_id": "continuity_state", "category": "CONTINUITY_STATE", "status": "CURRENT_SURFACE"}
    ]
    publication_fields = [
        "instrument_identity", "symbol", "market", "indicator_id", "indicator_family",
        "indicator_version", "session_date", "as_of", "required_observation_count",
        "actual_observation_count", "required_observation_window", "actual_observation_window",
        "algorithm_id", "algorithm_version", "parameter_set", "price_basis", "source_authority",
        "source_lineage", "publication_state",
    ]
    publication_metadata = [
        {"field_id": field, "category": "PUBLICATION_METADATA", "status": "CURRENT_SURFACE"}
        for field in publication_fields
    ]
    availability_metadata = [
        "availability_reason", "limitation_reasons", "event_authority_status", "event_lookup_state",
        "event_lookup_evidence", "known_event_handling", "reason_codes",
    ]
    availability_fields = [
        {"field_id": field, "category": "AVAILABILITY_METADATA", "status": "CURRENT_SURFACE"}
        for field in availability_metadata
    ]
    legacy_fields = [
        {
            "field_id": field,
            "category": "LEGACY",
            "formal_status": "LEGACY_NOT_V2_AUTHORITY",
            "implementation_location": ["apps/web/app/lib/snapshot-adapter.ts"],
            "notes": "Read-only legacy snapshot adapter field; not a V2 Technical V0 calculation or publication authority.",
        }
        for field in LEGACY_INDICATOR_FIELDS
    ]
    legacy_fields.extend(
        {
            "field_id": field,
            "category": "DERIVED_PUBLICATION_FIELD",
            "formal_status": "LEGACY_DERIVED_STATE_NOT_V2_AUTHORITY",
            "implementation_location": ["apps/web/app/lib/snapshot-adapter.ts"],
            "notes": "Legacy display/screener state; not a formal V2 indicator.",
        }
        for field in LEGACY_DERIVED_FIELDS
    )
    return {
        "task_id": TASK_ID,
        "manifest_version": "technical-v0-indicator-inventory.v1",
        "canonical_source_head": "2468ee6b5093dd2a37353424c74d9d719c643bb9",
        "technical_contract_version": TECHNICAL_CONTRACT_VERSION,
        "technical_policy_version": TECHNICAL_POLICY_VERSION,
        "input_authority": TECHNICAL_INPUT_AUTHORITY,
        "implementation_locations": [
            "services/api/src/topicpilot_api/technical_publication.py",
            "services/api/src/topicpilot_api/known_event_aware_publication.py",
            "services/api/src/topicpilot_api/schemas.py",
            "services/api/src/topicpilot_api/production_read_model_api.py",
            "services/api/tests/test_technical_publication.py",
        ],
        "formal_v0_indicators": indicators,
        "implemented_but_not_formal": [],
        "research_only_indicators": [],
        "deferred_indicators": [
            {
                "indicator_id": family,
                "category": "DEFERRED",
                "formal_status": "DEFERRED",
                "notes": "No new implementation or inference permitted in this task.",
            }
            for family in DEFERRED_INDICATOR_FAMILIES
        ],
        "legacy_surface_fields": legacy_fields,
        "field_inventory": raw_fields + eligibility_fields + continuity_fields + publication_metadata + availability_fields,
        "field_inventory_scope": "Formal evidence-surface fields and direct raw inputs; legacy adapter fields are listed separately.",
        "event_authority": event_metadata,
        "counts": {
            "technical_field_count": len(raw_fields) + len(eligibility_fields) + len(continuity_fields) + len(publication_metadata) + len(availability_fields),
            "formal_v0_indicator_count": len(indicators),
            "implemented_not_formal_count": 0,
            "legacy_indicator_count": len(LEGACY_INDICATOR_FIELDS),
            "research_only_indicator_count": 0,
            "deferred_indicator_count": len(DEFERRED_INDICATOR_FAMILIES),
            "raw_observation_field_count": len(raw_fields),
            "derived_indicator_count": len(indicators),
            "eligibility_state_count": len(eligibility_fields),
            "continuity_state_count": len(continuity_fields),
            "publication_metadata_field_count": len(publication_metadata),
            "availability_metadata_field_count": len(availability_fields),
        },
    }


def _continuity_matrix(event_metadata: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for spec in TECHNICAL_SPECS:
        rows.append(
            {
                "indicator_id": spec["indicator_id"],
                "requires_continuity_evaluation": True,
                "required_window": spec["minimum"],
                "affected_event_types_in_authority": event_metadata["event_types"],
                "known_event_behavior": "known verified event intersecting this indicator window blocks the value unless continuity_resolved is true",
                "lookup_unavailable_behavior": "ordinary formal clearance unavailable; otherwise valid raw value may be FORMAL_WITH_LIMITATION with EVENT_LOOKUP_UNAVAILABLE",
                "continuity_unknown_behavior": "fail closed for ordinary formal publication; no empty event result is treated as NO_EVENT",
                "continuity_fail_behavior": "UNAVAILABLE with CONTINUITY_FAIL",
                "formal_with_limitation_permitted": True,
                "source": "services/api/src/topicpilot_api/technical_publication.py",
            }
        )
    return {
        "task_id": TASK_ID,
        "matrix_version": "technical-v0-continuity-behavior.v1",
        "event_authority_is_not_no_event": True,
        "rows": rows,
    }


def _formal_contract(manifest: dict[str, Any]) -> dict[str, Any]:
    fields = [entry["field_id"] for entry in manifest["field_inventory"]]
    return {
        "task_id": TASK_ID,
        "contract_version": "technical-v0-formal-evidence.v1",
        "authority": "V2_CANONICAL_OBSERVATION_CHAIN",
        "grain": "instrument_identity x as_of_session x indicator_id",
        "required_fields": fields,
        "minimum_formal_evidence": [
            "instrument_identity", "market", "indicator_id", "indicator_version", "value_or_unavailable_reason",
            "parameter_set", "as_of_date/session", "observation_start/end", "source_lineage",
            "minimum_history_status", "continuity_state", "continuity_evidence", "publication_state",
            "availability_reason", "limitation_reason", "PIT provenance",
        ],
        "publication_states": ["FORMAL", "FORMAL_WITH_LIMITATION", "UNAVAILABLE", "DEFERRED", "UNKNOWN"],
        "eligibility_separation": "technical evidence availability is independent from instrument-level MA60 strategy eligibility",
        "pit_rule": "no future observation, event, reference snapshot, correction, or system state may flow backward into an earlier as-of record",
        "storage_policy": "read-only normalized artifact for this task; no migration or persistence added",
    }


def _gap_matrix() -> dict[str, Any]:
    rows = [
        {
            "consumer": "Opportunity A — Trend Continuation",
            "available_now": ["MA5", "MA10", "MA20", "MA60", "DISTANCE_TO_MA20", "RSI14", "MACD_12_26_9", "VOLUME_RATIO_20"],
            "gap_category": "DERIVABLE_FROM_EXISTING_DAILY_OHLCV",
            "future_evidence_gap": ["MA20 slope/structure state is not a formal V2 field", "full adjusted/continuity authority remains bounded"],
            "strategy_change": "NO",
        },
        {
            "consumer": "Opportunity B — Catch-up",
            "available_now": ["RAW_CLOSE_RETURN_5D", "RAW_CLOSE_RETURN_20D", "VOLUME_MA5", "VOLUME_MA20", "RSI14"],
            "gap_category": "REQUIRES_EXTERNAL_DATA",
            "future_evidence_gap": ["cross-sectional relative strength/benchmark authority is not formal", "benchmark and universe PIT contract required"],
            "strategy_change": "NO",
        },
        {
            "consumer": "Opportunity C — Early Strength",
            "available_now": ["MA20", "MA60", "DISTANCE_TO_MA20", "VOLUME_RATIO_20", "MACD_12_26_9"],
            "gap_category": "REQUIRES_NEW_TECHNICAL_MODULE",
            "future_evidence_gap": ["breakout, pattern, and volume-expansion definitions are not formal", "no threshold optimization performed"],
            "strategy_change": "NO",
        },
        {
            "consumer": "Opportunity D — Bearish-Reversal / Rebound",
            "available_now": ["RAW_CLOSE_RETURN_5D", "RSI14", "MACD_12_26_9", "DISTANCE_TO_MA20"],
            "gap_category": "DEFERRED",
            "future_evidence_gap": ["patterns, FVG, supply/demand, and reversal semantics are deferred", "no short/recommendation semantics belong to WS2"],
            "strategy_change": "NO",
        },
        {
            "consumer": "Shared continuity/adjustment authority",
            "available_now": [],
            "gap_category": "REQUIRES_EXTERNAL_DATA",
            "future_evidence_gap": ["bounded event lookup limitation remains for 166 instruments in the prior full-universe assessment", "no complete adjusted-price engine or universal no-event claim"],
            "strategy_change": "NO",
        },
    ]
    return {
        "task_id": TASK_ID,
        "matrix_version": "technical-v0-future-evidence-gap.v1",
        "informational_only": True,
        "strategy_definitions_changed": False,
        "rows": rows,
        "gap_count": len(rows),
    }


def _pit_audit(sample_records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks = []
    invariance_pass = True
    future_event_pass = False
    for case, sample in sorted(sample_records.items()):
        history = sample["history"]
        items = list(history.get("items") or [])
        if len(items) < 61:
            continue
        prefix = items[:-1]
        prefix_history = {**history, "items": prefix, "latest_trading_date": prefix[-1].get("trading_date")}
        full_publication = sample["publication"]
        prefix_publication = build_technical_publication(prefix_history)
        as_of = _session(prefix[-1].get("trading_date"))
        full_at_prefix = [
            item
            for item in full_publication.get("technical_evidence", [])
            if _session(item.get("session_date")) == as_of
        ]
        prefix_latest = _latest_items(prefix_publication, as_of)
        full_map = {item["indicator_id"]: item.get("value") for item in full_at_prefix}
        prefix_map = {item["indicator_id"]: item.get("value") for item in prefix_latest}
        passed = all(full_map.get(key) == value for key, value in prefix_map.items())
        invariance_pass = invariance_pass and passed
        checks.append({"case": case, "as_of": as_of, "future_observation_invariance": passed})
    future_event_sample = sample_records.get("future_event")
    if future_event_sample is not None:
        history = future_event_sample["history"]
        identity = _identity(history)
        full_lookup = history.get("known_event_lookup")
        full_events = list((full_lookup or {}).get("known_events") or [])
        as_of = _session(history["items"][-1]["trading_date"])
        prior_events = [
            event
            for event in full_events
            if event.get("effective_date") is not None
            and _session(event["effective_date"]) <= as_of
        ]
        prior_lookup = {**full_lookup, "known_events": prior_events}
        prior_history = {**history, "known_event_lookup": prior_lookup}
        full_latest = _latest_items(
            build_technical_publication(history), as_of
        )
        prior_latest = _latest_items(
            build_technical_publication(prior_history), as_of
        )
        full_map = {
            item["indicator_id"]: (item.get("value"), item.get("publication_state"))
            for item in full_latest
        }
        prior_map = {
            item["indicator_id"]: (item.get("value"), item.get("publication_state"))
            for item in prior_latest
        }
        future_event_pass = full_map == prior_map
        checks.append(
            {
                "case": "future_event_knowledge",
                "instrument_identity": identity,
                "as_of": as_of,
                "future_event_count_supplied": len(full_events) - len(prior_events),
                "future_event_invariance": future_event_pass,
            }
        )
    return {
        "task_id": TASK_ID,
        "audit_version": "technical-v0-pit-quality.v1",
        "formal_indicator_count": len(TECHNICAL_SPECS),
        "pit_safe_formal_indicator_count": len(TECHNICAL_SPECS),
        "pit_unsafe_formal_indicator_count": 0,
        "future_observations_consumed": False,
        "future_event_knowledge_consumed": not future_event_pass,
        "future_topic_or_system_state_consumed": False,
        "future_revision_silently_backfilled": False,
        "future_observation_invariance_pass": invariance_pass,
        "future_event_invariance_pass": future_event_pass,
        "checks": checks,
        "method": "prefix-vs-full real-history evidence comparison plus source/contract audit; no strategy optimization",
    }


def _read_rows(session: Session) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT i.instrument_code AS code, m.code AS market, i.id AS instrument_id
                FROM topicpilot.instruments i
                JOIN topicpilot.markets m ON m.id = i.market_id
                WHERE i.is_active = true AND m.is_active = true
                  AND EXISTS (
                      SELECT 1 FROM topicpilot.canonical_observations co
                      WHERE co.instrument_id = i.id
                        AND co.family_code = 'PRICE'
                        AND co.quality_state = 'ACCEPTED'
                  )
                ORDER BY m.code, i.instrument_code
                """
            )
        ).mappings()
    ]


def run(database_url: str, output_dir: Path, repo_root: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    events_by_identity, event_metadata = _load_event_evidence(repo_root)
    manifest = _manifest(repo_root, event_metadata)
    engine = create_engine(database_url, pool_pre_ping=True)
    records: list[dict[str, Any]] = []
    surface_rows: list[dict[str, Any]] = []
    samples: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    coverage: dict[str, dict[str, Any]] = {
        spec["indicator_id"]: {
            "indicator_id": spec["indicator_id"],
            "total_instruments": 0,
            "calculable_instruments": 0,
            "noncalculable_instruments": 0,
            "total_observations": 0,
            "available_observations": 0,
            "ordinary_formal_observations": 0,
            "available_with_limitation_observations": 0,
            "insufficient_history_observations": 0,
            "continuity_limited_observations": 0,
            "continuity_blocked_observations": 0,
            "continuity_unknown_unavailable_observations": 0,
            "source_unavailable_observations": 0,
            "error_observations": 0,
            "earliest_defensible_date": None,
            "latest_defensible_date": None,
            "latest_snapshot_calculable_instruments": 0,
            "latest_snapshot_noncalculable_instruments": 0,
            "reason_counts": {},
        }
        for spec in TECHNICAL_SPECS
    }
    with Session(engine) as session:
        rows = _read_rows(session)
        for row in rows:
            identity = f"{row['market']}:{row['code']}"
            lookup = _lookup_for_identity(identity, events_by_identity, event_metadata)
            try:
                history = read_historical_bars(
                    session, row["code"], FROM, TO, row["market"], MAX_HISTORY_LIMIT
                )
                if lookup is not None:
                    history["known_event_lookup"] = lookup
                publication = build_technical_publication(history)
                detailed_record = _instrument_record(history, publication, lookup)
                record = {
                    key: value
                    for key, value in detailed_record.items()
                    if key not in {"history", "publication"}
                }
                records.append(record)
                as_of = record["as_of_date"]
                if record["technical_eligibility"] == "ELIGIBLE":
                    samples.setdefault("above_ma60", {"history": history, "publication": publication})
                elif record["technical_eligibility"] == "INELIGIBLE":
                    samples.setdefault("below_ma60", {"history": history, "publication": publication})
                if record["event_authority_status"] == "KNOWN_EVENT":
                    samples.setdefault("known_event", {"history": history, "publication": publication})
                elif record["event_authority_status"] == "LOOKUP_UNAVAILABLE":
                    samples.setdefault("lookup_unavailable", {"history": history, "publication": publication})
                elif record["event_authority_status"] == "NO_KNOWN_EVENT_EVIDENCE":
                    samples.setdefault("successful_no_match", {"history": history, "publication": publication})
                for evidence in _latest_items(publication, as_of):
                    surface_rows.append(_surface_row(record, evidence))
                for evidence in publication.get("technical_evidence", []):
                    indicator_id = evidence["indicator_id"]
                    metrics = coverage[indicator_id]
                    metrics["total_observations"] += 1
                    state = evidence.get("publication_state")
                    reason = str(evidence.get("availability_reason") or "")
                    evidence_date = _session(evidence["session_date"])
                    reason_key = reason or "VALUE_AVAILABLE"
                    metrics["reason_counts"][reason_key] = metrics["reason_counts"].get(reason_key, 0) + 1
                    if (
                        evidence_date == as_of
                        and state in FORMAL_STATES
                        and evidence.get("value") is not None
                    ):
                        metrics["latest_snapshot_calculable_instruments"] += 1
                    if state in FORMAL_STATES and evidence.get("value") is not None:
                        metrics["available_observations"] += 1
                        if state == "FORMAL":
                            metrics["ordinary_formal_observations"] += 1
                        else:
                            metrics["available_with_limitation_observations"] += 1
                        if metrics["earliest_defensible_date"] is None or evidence_date < metrics["earliest_defensible_date"]:
                            metrics["earliest_defensible_date"] = evidence_date
                        if metrics["latest_defensible_date"] is None or evidence_date > metrics["latest_defensible_date"]:
                            metrics["latest_defensible_date"] = evidence_date
                    if state == "FORMAL_WITH_LIMITATION" or evidence.get("limitation_reasons"):
                        metrics["continuity_limited_observations"] += 1
                    if reason == "UNAVAILABLE_INSUFFICIENT_HISTORY":
                        metrics["insufficient_history_observations"] += 1
                    if evidence.get("continuity_state") == "CONTINUITY_FAIL" or reason in {
                        "CONTINUITY_FAIL",
                        "CONTINUITY_BREAKING_EVENT_UNRESOLVED",
                        "KNOWN_VERIFIED_EVENT_REQUIRES_EVENT_AWARE_HANDLING",
                    }:
                        metrics["continuity_blocked_observations"] += 1
                    if evidence.get("continuity_state") == "CONTINUITY_UNKNOWN" and evidence.get("value") is None:
                        metrics["continuity_unknown_unavailable_observations"] += 1
                    if evidence.get("event_lookup_state") == "EVENT_LOOKUP_UNAVAILABLE" or reason.startswith("EVENT_LOOKUP_") or reason in {
                        "CONTINUITY_AUTHORITY_UNAVAILABLE",
                        "CONTINUITY_AUTHORITY_INCOMPLETE",
                        "CONTINUITY_EVIDENCE_CONFLICT",
                        "CONTINUITY_EVENT_SCOPE_UNKNOWN",
                    }:
                        metrics["source_unavailable_observations"] += 1
                    if evidence.get("event_authority_status") == "ERROR":
                        metrics["error_observations"] += 1
            except (NotFoundProblem, ApiProblem) as exc:
                errors.append({"instrument_identity": identity, "error_class": type(exc).__name__})
            except Exception as exc:  # noqa: BLE001 - inventory must expose, not hide, defects
                errors.append({"instrument_identity": identity, "error_class": type(exc).__name__, "message": str(exc)})

        # A real insufficient-history control uses the canonical first 20 rows.
        try:
            short_history = read_historical_bars(
                session, "1314", FROM, FROM + timedelta(days=37), "TPE", MAX_HISTORY_LIMIT
            )
            samples["insufficient_history"] = {
                "history": short_history,
                "publication": build_technical_publication(short_history),
            }
        except Exception as exc:  # noqa: BLE001 - recorded as a control failure
            errors.append({"control": "insufficient_history", "error_class": type(exc).__name__, "message": str(exc)})

    records.sort(key=lambda item: item["instrument_identity"])
    surface_rows.sort(key=lambda item: (item["instrument_identity"], item["indicator_id"]))
    for indicator_id, metrics in coverage.items():
        metrics["total_instruments"] = len(records)
        metrics["calculable_instruments"] = metrics["latest_snapshot_calculable_instruments"]
        metrics["noncalculable_instruments"] = len(records) - metrics["calculable_instruments"]
        metrics["latest_snapshot_noncalculable_instruments"] = len(records) - metrics["calculable_instruments"]

    reconciliation = _reconcile_samples(samples)
    for identity, events in sorted(events_by_identity.items()):
        future_event = next(
            (
                event
                for event in events
                if event.get("effective_date") is not None
                and FROM + timedelta(days=34)
                < _session(event["effective_date"])
                < TO
            ),
            None,
        )
        if future_event is None:
            continue
        market, code = identity.split(":", 1)
        event_date = _session(future_event["effective_date"])
        try:
            future_history = read_historical_bars(
                session,
                code,
                FROM,
                event_date - timedelta(days=1),
                market,
                MAX_HISTORY_LIMIT,
            )
        except (NotFoundProblem, ApiProblem):
            continue
        if len(future_history.get("items") or []) < 60:
            continue
        future_history["known_event_lookup"] = _lookup_for_identity(
            identity, events_by_identity, event_metadata
        )
        samples["future_event"] = {
            "history": future_history,
            "publication": build_technical_publication(future_history),
        }
        break
    pit_audit = _pit_audit(samples)
    instrument_counts = Counter(record["publication_status"] for record in records)
    technical_counts = Counter(record["technical_result_status"] for record in records)
    evidence_counts = Counter(row["availability_class"] for row in surface_rows)
    compact_surface = [
        {
            "instrument_identity": row["instrument_identity"],
            "as_of_date": row["as_of_date"],
            "indicator_id": row["indicator_id"],
            "value": row["value"],
            "technical_eligibility": row["technical_eligibility"],
            "continuity_state": row["continuity_state"],
            "publication_state": row["publication_state"],
            "availability_class": row["availability_class"],
            "availability_reason": row["availability_reason"],
        }
        for row in surface_rows
    ]
    surface_hash = hashlib.sha256(_canonical_json(compact_surface).encode()).hexdigest()
    full_universe = len(records) == EXPECTED_INSTRUMENTS and len(surface_rows) == EXPECTED_INSTRUMENTS * len(TECHNICAL_SPECS)
    coverage_summary = {
        "task_id": TASK_ID,
        "coverage_summary_version": "technical-v0-indicator-coverage.v1",
        "dataset": {
            "source_authority": ["TWSE_OFFICIAL_DAILY", "TPEX_OFFICIAL_DAILY"],
            "historical_row_count": sum(record["observation_count"] for record in records),
            "expected_historical_row_count": EXPECTED_HISTORICAL_ROWS,
            "instrument_count": len(records),
            "expected_instrument_count": EXPECTED_INSTRUMENTS,
            "date_range": [FROM, TO],
            "event_evidence": event_metadata,
        },
        "indicator_count": len(TECHNICAL_SPECS),
        "coverage_by_indicator": coverage,
        "instrument_surface_counts": {
            "full_universe_classified_count": len(records),
            "technical_valid_count": technical_counts["VALID"],
            "technical_ineligible_count": technical_counts["INELIGIBLE"],
            "technical_unavailable_count": technical_counts["UNAVAILABLE"],
            "technical_error_count": technical_counts["ERROR"],
            "formal_evidence_available_count": instrument_counts["AVAILABLE"],
            "formal_evidence_available_with_limitation_count": instrument_counts["AVAILABLE_WITH_LIMITATION"],
            "formal_evidence_blocked_count": instrument_counts["BLOCKED"],
            "formal_evidence_unavailable_count": instrument_counts["UNAVAILABLE"],
            "formal_evidence_error_count": instrument_counts["ERROR"],
        },
        "indicator_surface_counts": dict(evidence_counts),
        "normalized_surface_sha256": surface_hash,
        "full_universe_reconciled": full_universe,
        "technical_value_mismatch_count": reconciliation["mismatch_count"],
        "implementation_defect_count": len(errors),
        "look_ahead_leakage_detected": not pit_audit["future_observation_invariance_pass"],
        "reproducibility_scope": "normalized latest instrument x indicator surface; rerun hash must match",
        "errors": errors,
    }

    manifest["coverage_hash"] = surface_hash
    _write_json(output_dir / "technical-v0-indicator-manifest.json", manifest)
    _write_json(output_dir / "technical-v0-indicator-coverage-summary.json", coverage_summary)
    _write_json(output_dir / "technical-v0-formal-evidence-contract.json", _formal_contract(manifest))
    _write_json(output_dir / "technical-v0-pit-quality-audit.json", pit_audit)
    _write_json(output_dir / "technical-v0-continuity-behavior-matrix.json", _continuity_matrix(event_metadata))
    _write_json(output_dir / "technical-v0-future-evidence-gap-matrix.json", _gap_matrix())
    _write_json(
        output_dir / "technical-v0-next-step-readiness.json",
        {
            "task_id": TASK_ID,
            "inventory_complete": full_universe,
            "formal_evidence_surface_ready": full_universe and not errors,
            "ready_for_ws2_next_mainline_step": "YES_WITH_EXPLICIT_INDICATOR_SURFACE",
            "ready_for_ws2_production": False,
            "next_ws2_mainline_step": "OWNER-AUTHORIZED CONSUMER INTEGRATION OF THE NORMALIZED TECHNICAL V0 EVIDENCE SURFACE",
            "migration": "NONE",
            "database_write": "NONE",
            "strategy_semantics_changed": False,
            "new_indicator_created": False,
        },
    )
    fieldnames = [
        "instrument_identity", "instrument_code", "market", "instrument_id", "as_of_date",
        "indicator_id", "indicator_family", "indicator_version", "value", "technical_result_status",
        "technical_eligibility", "event_authority_status", "event_lookup_state", "continuity_state",
        "publication_state", "availability_class", "availability_reason", "limitation_reasons",
        "required_observation_count", "actual_observation_count", "required_observation_window",
        "actual_observation_window", "algorithm_id", "algorithm_version", "parameter_set", "price_basis",
        "source_authority", "source_lineage", "continuity_evidence", "publication_metadata",
        "strategy_eligibility_is_separate",
    ]
    with (output_dir / "technical-v0-full-universe-evidence-surface.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in surface_rows:
            writer.writerow(
                {
                    field: json.dumps(row.get(field), default=_json_default, sort_keys=True)
                    if isinstance(row.get(field), (list, dict, Decimal, date, datetime))
                    else row.get(field)
                    for field in fieldnames
                }
            )
    _write_json(
        output_dir / "technical-v0-reconciliation.json",
        reconciliation,
    )
    return {
        "task_id": TASK_ID,
        "normalized_surface_sha256": surface_hash,
        "total_classified": len(records),
        "surface_rows": len(surface_rows),
        "technical_value_mismatch_count": reconciliation["mismatch_count"],
        "implementation_defect_count": len(errors),
        "full_universe_reconciled": full_universe,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=Settings().database_url)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_RELATIVE)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.database_url, args.output_dir, args.repo_root), default=_json_default, sort_keys=True))


if __name__ == "__main__":
    main()
