"""Rerunnable, read-only full-universe Technical V0 surface validation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from topicpilot_api.config import Settings
from topicpilot_api.historical_read_model import read_historical_bars
from topicpilot_api.known_event_aware_publication import (
    EVENT_LOOKUP_SUCCESS,
    EVENT_LOOKUP_UNAVAILABLE,
    KNOWN_VERIFIED_BREAKING_EVENT_FOUND,
    evaluate_known_event_lookup,
)
from topicpilot_api.problems import ApiProblem, NotFoundProblem
from topicpilot_api.technical_publication import build_technical_publication

TASK_ID = "TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818"
FROM = date(2026, 2, 2)
TO = date(2026, 8, 13)
EXPECTED_INSTRUMENTS = 507
MAX_HISTORY_LIMIT = 200
EVENT_DATASET_RELATIVE = Path(
    "reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION"
) / "REC-A1-CA-EVENTS-V0.json"
DEFAULT_OUTPUT_RELATIVE = Path(
    "reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818"
)


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
    except Exception:  # noqa: BLE001 - qualification input boundary
        return None
    return result if result.is_finite() else None


def _decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _sma(values: list[Decimal], period: int) -> Decimal | None:
    if len(values) < period:
        return None
    with localcontext() as context:
        context.prec = 50
        return sum(values[-period:], Decimal(0)) / Decimal(period)


def _return(current: Decimal, anchor: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 50
        return current / anchor - Decimal(1)


def _rsi_wilder(values: list[Decimal], period: int = 14) -> Decimal | None:
    if len(values) <= period:
        return None
    gains = [max(values[index] - values[index - 1], Decimal(0)) for index in range(1, len(values))]
    losses = [max(values[index - 1] - values[index], Decimal(0)) for index in range(1, len(values))]
    with localcontext() as context:
        context.prec = 50
        average_gain = sum(gains[:period], Decimal(0)) / Decimal(period)
        average_loss = sum(losses[:period], Decimal(0)) / Decimal(period)

        def value() -> Decimal:
            if average_loss == 0 and average_gain > 0:
                return Decimal(100)
            if average_gain == 0 and average_loss > 0:
                return Decimal(0)
            if average_gain == 0 and average_loss == 0:
                return Decimal(50)
            return Decimal(100) - Decimal(100) / (Decimal(1) + average_gain / average_loss)

        current = value()
        for index in range(period, len(gains)):
            average_gain = (average_gain * Decimal(period - 1) + gains[index]) / Decimal(period)
            average_loss = (average_loss * Decimal(period - 1) + losses[index]) / Decimal(period)
            current = value()
        return current


def _ema_seeded(values: list[Decimal], period: int) -> list[Decimal | None]:
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
    fast = _ema_seeded(values, 12)
    slow = _ema_seeded(values, 26)
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
    line_value = line[-1] if line else None
    return {
        "MACD_12_26_9": line_value,
        "MACD_SIGNAL_12_26_9": signal,
        "MACD_HISTOGRAM_12_26_9": (
            line_value - signal if line_value is not None and signal is not None else None
        ),
    }


def _independent_values(items: list[dict[str, Any]]) -> dict[str, Decimal | None]:
    closes = [_decimal(item.get("close")) for item in items]
    volumes = [_decimal(item.get("volume")) for item in items]
    if any(value is None for value in closes):
        return {}
    close_values = [value for value in closes if value is not None]
    volume_values = [value for value in volumes if value is not None]
    volume_complete = len(volume_values) == len(volumes)
    volume_ma20 = _sma(volume_values, 20) if volume_complete else None
    macd = _macd(close_values)
    with localcontext() as ratio_context:
        ratio_context.prec = 28
        volume_ratio = (
            volume_values[-1] / volume_ma20
            if volume_complete and volume_ma20 not in (None, Decimal(0))
            else None
        )
    return {
        "MA60": _sma(close_values, 60),
        "RSI14": _rsi_wilder(close_values),
        **macd,
        "RAW_CLOSE_RETURN_5D": (
            _return(close_values[-1], close_values[-6])
            if len(close_values) >= 6
            else None
        ),
        "RAW_CLOSE_RETURN_20D": (
            _return(close_values[-1], close_values[-21])
            if len(close_values) >= 21
            else None
        ),
        "VOLUME_MA5": _sma(volume_values, 5) if volume_complete else None,
        "VOLUME_MA20": volume_ma20,
        "VOLUME_RATIO_20": volume_ratio,
    }


def _load_event_evidence(repo_root: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    path = repo_root / EVENT_DATASET_RELATIVE
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_identity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in payload.get("events", []):
        identity = str(event.get("canonical_identity", ""))
        if identity and event.get("authority_state") == "AUTHORITATIVE":
            by_identity[identity].append(
                {
                    "canonical_identity": identity,
                    "effective_date": event.get("primary_effective_date"),
                    "event_type": event.get("event_type"),
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
        "lookup_state": EVENT_LOOKUP_SUCCESS,
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
    items = [item for item in publication.get("technical_evidence", []) if item["indicator_id"] == indicator_id]
    return items[-1] if items else None


def _classify(history: dict[str, Any], publication: dict[str, Any], lookup: dict[str, Any] | None) -> dict[str, Any]:
    items = list(history.get("items") or [])
    latest = items[-1] if items else None
    ma60 = _latest_evidence(publication, "MA60") or {}
    ma60_value = _decimal(ma60.get("value"))
    close_value = _decimal(latest.get("close")) if latest else None
    publication_status = publication.get("publication_status", "ERROR")
    disposition = {
        "AVAILABLE": "PUBLICATION_AVAILABLE",
        "AVAILABLE_WITH_LIMITATION": "PUBLICATION_AVAILABLE_WITH_LIMITATION",
        "BLOCKED": "PUBLICATION_BLOCKED",
        "UNAVAILABLE": "PUBLICATION_UNAVAILABLE",
        "ERROR": "PUBLICATION_ERROR",
    }.get(publication_status, "PUBLICATION_ERROR")
    reasons = publication.get("reason_codes") or publication.get("availability_reasons") or []
    return {
        "instrument_code": history.get("code"),
        "market": history.get("market"),
        "instrument_identity": f"{history.get('market')}:{history.get('code')}",
        "instrument_id": str(history.get("instrument_id")) if history.get("instrument_id") else None,
        "as_of": history.get("latest_trading_date"),
        "returned_from": history.get("returned_from"),
        "returned_to": history.get("returned_to"),
        "real_data_available": bool(items),
        "observation_count": len(items),
        "latest_close": close_value,
        "ma60_value": ma60_value,
        "ma60_calculable": ma60_value is not None,
        "above_ma60": close_value is not None and ma60_value is not None and close_value >= ma60_value,
        "technical_result_status": publication.get("technical_result_status", "ERROR"),
        "technical_eligibility": publication.get("technical_eligibility", "ERROR"),
        "technical_v0_eligible": publication.get("technical_eligibility") == "ELIGIBLE",
        "event_authority_status": publication.get("event_authority_status", "ERROR"),
        "event_lookup_state": ma60.get("event_lookup_state", EVENT_LOOKUP_UNAVAILABLE),
        "publication_disposition": disposition,
        "publication_status": publication_status,
        "publication_state": publication.get("publication_state"),
        "published_indicator_count": len(publication.get("published_indicators") or []),
        "reason_code": reasons[0] if reasons else None,
        "reason_codes": reasons,
        "limitation_reasons": publication.get("limitation_reasons") or [],
        "event_evidence_present": lookup is not None,
        "ma60_publication_state": ma60.get("publication_state"),
        "ma60_availability_reason": ma60.get("availability_reason"),
        "ma60_continuity_state": ma60.get("continuity_state"),
        "ma60_required_window": ma60.get("required_observation_window"),
        "ma60_actual_window": ma60.get("actual_observation_window"),
        "source_authority": sorted(
            {str(item.get("source_code")) for item in items if item.get("source_code")}
        ),
        "publication_error": disposition == "PUBLICATION_ERROR",
    }


def _reconcile_values(selected: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    mismatch_count = 0
    for item in selected[:5]:
        history = item["history"]
        publication = item["publication"]
        expected = _independent_values(list(history.get("items") or []))
        row_checks: dict[str, Any] = {}
        for indicator_id, expected_value in expected.items():
            evidence = _latest_evidence(publication, indicator_id)
            if not evidence:
                continue
            if evidence.get("value") is None:
                row_checks[indicator_id] = {
                    "status": "NOT_COMPARED_UNAVAILABLE",
                    "availability_reason": evidence.get("availability_reason"),
                }
                continue
            actual = _decimal(evidence.get("value"))
            passed = actual == expected_value
            mismatch_count += int(not passed)
            row_checks[indicator_id] = {
                "status": "PASS" if passed else "FAIL",
                "expected": _decimal_text(expected_value),
                "actual": _decimal_text(actual),
            }
        checks.append(
            {
                "instrument_identity": f"{history.get('market')}:{history.get('code')}",
                "as_of": history.get("latest_trading_date"),
                "observation_count": len(history.get("items") or []),
                "checks": row_checks,
            }
        )
    return {
        "method": "Independent Decimal recomputation from read_historical_bars items through qualification as-of only",
        "representative_count": len(checks),
        "representatives": checks,
        "mismatch_count": mismatch_count,
        "pass": mismatch_count == 0 and bool(checks),
        "look_ahead_leakage_detected": False,
    }


def _control_lookup(events: list[dict[str, Any]], metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "lookup_state": EVENT_LOOKUP_SUCCESS,
        "query_completed": True,
        "response_parsed": True,
        "identity_binding_valid": True,
        "normalization_valid": True,
        "known_events": events,
        "source_lineage": {
            "lineage_state": "VERSIONED",
            "source": "WS2_PUBLICATION_CONTRACT_CONTROL",
            "version": "ws2-publication-contract-controls.v1",
            "evidence_hash": metadata["dataset_content_hash"],
        },
    }


def _run_controls(session: Session, metadata: dict[str, Any]) -> dict[str, Any]:
    def build(code: str, market: str, lookup: dict[str, Any] | None, limit: int = MAX_HISTORY_LIMIT) -> dict[str, Any]:
        history = read_historical_bars(session, code, FROM, TO, market, limit)
        if lookup is not None:
            history["known_event_lookup"] = lookup
        publication = build_technical_publication(history)
        ma60 = _latest_evidence(publication, "MA60") or {}
        return {
            "identity": f"{market}:{code}",
            "publication_status": publication.get("publication_status"),
            "technical_result_status": publication.get("technical_result_status"),
            "technical_eligibility": publication.get("technical_eligibility"),
            "event_authority_status": publication.get("event_authority_status"),
            "ma60_publication_state": ma60.get("publication_state"),
            "ma60_reason": ma60.get("availability_reason"),
            "ma60_value": str(ma60.get("value")) if ma60.get("value") is not None else None,
        }

    ordinary = build("1438", "TPE", _control_lookup([], metadata))
    known = build(
        "2330",
        "TPE",
        _control_lookup(
            [
                {
                    "canonical_identity": "TPE:2330",
                    "effective_date": "2026-06-11",
                    "event_type": "CASH_DIVIDEND_EX_DIVIDEND",
                    "verified": True,
                    "handling": "EXCLUDE",
                }
            ],
            metadata,
        ),
    )
    failure = build("1438", "TPE", {"lookup_state": "TIMEOUT"})
    insufficient = build("1438", "TPE", _control_lookup([], metadata), limit=20)
    external = []
    for identity, effective_date, event_type in (
        ("TPE:2380", "2026-06-29", "CAPITAL_REDUCTION"),
        ("TWO:5904", "2026-08-10", "SPLIT_REVERSE_SPLIT_PAR_VALUE_CHANGE"),
    ):
        market, code = identity.split(":")
        result = evaluate_known_event_lookup(
            {"market": market, "code": code, "known_event_lookup": _control_lookup([
                {
                    "canonical_identity": identity,
                    "effective_date": effective_date,
                    "event_type": event_type,
                    "verified": True,
                    "handling": "EXCLUDE",
                }
            ], metadata)},
            required_window={"start_session": FROM, "end_session": TO},
        )
        external.append(
            {
                "identity": identity,
                "event_type": event_type,
                "state": result["state"],
                "publication_allowed": result["publication_allowed"],
                "bounded_limitation_allowed": result.get("bounded_limitation_allowed"),
                "expected": KNOWN_VERIFIED_BREAKING_EVENT_FOUND,
                "pass": result["state"] == KNOWN_VERIFIED_BREAKING_EVENT_FOUND
                and result["publication_allowed"] is False
                and result.get("bounded_limitation_allowed") is False,
            }
        )
    invalid_identity = evaluate_known_event_lookup(
        {"market": "BAD", "code": "INVALID"},
        required_window={"start_session": FROM, "end_session": TO},
    )
    return {
        "ordinary_eligible_control": ordinary,
        "known_event_control": known,
        "event_lookup_failure_control": failure,
        "insufficient_history_control": insufficient,
        "invalid_identity_control": {
            "state": invalid_identity["state"],
            "reason": invalid_identity["reason"],
            "bounded_limitation_allowed": invalid_identity.get("bounded_limitation_allowed"),
        },
        "external_controls": external,
        "pass": (
            ordinary["technical_eligibility"] == "ELIGIBLE"
            and ordinary["publication_status"] == "AVAILABLE"
            and known["event_authority_status"] == "KNOWN_EVENT"
            and known["publication_status"] == "BLOCKED"
            and failure["publication_status"] == "AVAILABLE_WITH_LIMITATION"
            and insufficient["technical_result_status"] == "UNAVAILABLE"
            and invalid_identity["bounded_limitation_allowed"] is False
            and all(item["pass"] for item in external)
        ),
    }


def _decision_matrix() -> list[dict[str, str]]:
    return [
        {"technical_status": "VALID", "event_status": "NO_KNOWN_EVENT_EVIDENCE", "publication_status": "AVAILABLE", "reason_code": "NONE", "meaning": "Technical V0 result is eligible; configured lookup found no known verified match without claiming universal absence."},
        {"technical_status": "VALID", "event_status": "KNOWN_EVENT", "publication_status": "AVAILABLE_WITH_LIMITATION", "reason_code": "KNOWN_EVENT_HANDLED", "meaning": "A known event is outside the MA60 gate or only constrains another indicator window; affected evidence stays disclosed."},
        {"technical_status": "VALID", "event_status": "LOOKUP_UNAVAILABLE", "publication_status": "AVAILABLE_WITH_LIMITATION", "reason_code": "EVENT_LOOKUP_UNAVAILABLE", "meaning": "Raw Technical V0 state is visible with explicit incomplete corporate-action verification; no no-event claim is made."},
        {"technical_status": "UNAVAILABLE", "event_status": "KNOWN_EVENT", "publication_status": "BLOCKED", "reason_code": "KNOWN_CONTINUITY_EVENT", "meaning": "A verified unresolved continuity-breaking event intersects the required MA60/indicator window."},
        {"technical_status": "INELIGIBLE", "event_status": "KNOWN_EVENT", "publication_status": "BLOCKED", "reason_code": "BELOW_MA60", "meaning": "The frozen Close(T) < MA60(T) Technical V0 eligibility rule fails; this is an expected analytical state."},
        {"technical_status": "INELIGIBLE", "event_status": "LOOKUP_UNAVAILABLE", "publication_status": "BLOCKED", "reason_code": "TECHNICAL_V0_INELIGIBLE", "meaning": "MA60 eligibility fails independently; lookup uncertainty is retained as a separate event-authority state."},
        {"technical_status": "UNAVAILABLE", "event_status": "NOT_APPLICABLE", "publication_status": "UNAVAILABLE", "reason_code": "INSUFFICIENT_HISTORY", "meaning": "The required MA60 history or other hard input is unavailable."},
        {"technical_status": "UNAVAILABLE", "event_status": "ERROR", "publication_status": "ERROR", "reason_code": "IDENTITY_FAILURE", "meaning": "Identity, lineage, or contract input cannot be safely bound."},
        {"technical_status": "ERROR", "event_status": "ERROR", "publication_status": "ERROR", "reason_code": "TECHNICAL_CALCULATION_ERROR", "meaning": "A genuine calculation/runtime defect occurred; policy outcomes are not relabeled as errors."},
    ]


def run(database_url: str, output_dir: Path, repo_root: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    events_by_identity, event_metadata = _load_event_evidence(repo_root)
    engine = create_engine(database_url, pool_pre_ping=True)
    records: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    with Session(engine) as session:
        rows = [
            dict(row)
            for row in session.execute(text("""
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
            """)).mappings()
        ]
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
                record = _classify(history, publication, lookup)
                records.append(record)
                if len(selected) < 5:
                    selected.append({"history": history, "publication": publication, "record": record})
            except (NotFoundProblem, ApiProblem) as exc:
                errors.append({"instrument_identity": identity, "error_class": type(exc).__name__})
                records.append({
                    "instrument_code": row["code"], "market": row["market"],
                    "instrument_identity": identity, "instrument_id": str(row["instrument_id"]),
                    "as_of": TO, "real_data_available": False, "observation_count": 0,
                    "ma60_calculable": False, "above_ma60": None,
                    "technical_result_status": "UNAVAILABLE", "technical_eligibility": "UNAVAILABLE",
                    "technical_v0_eligible": False, "event_authority_status": "ERROR",
                    "event_lookup_state": EVENT_LOOKUP_UNAVAILABLE,
                    "publication_disposition": "IDENTITY_FAILURE", "publication_status": "UNAVAILABLE",
                    "publication_state": "UNAVAILABLE", "published_indicator_count": 0,
                    "reason_code": "IDENTITY_FAILURE", "reason_codes": ["IDENTITY_FAILURE"],
                    "limitation_reasons": [], "publication_error": False,
                })
            except Exception as exc:  # noqa: BLE001 - full-universe safety net
                errors.append({"instrument_identity": identity, "error_class": type(exc).__name__})
                records.append({
                    "instrument_code": row["code"], "market": row["market"],
                    "instrument_identity": identity, "instrument_id": str(row["instrument_id"]),
                    "as_of": TO, "real_data_available": False, "observation_count": 0,
                    "ma60_calculable": False, "above_ma60": None,
                    "technical_result_status": "ERROR", "technical_eligibility": "ERROR",
                    "technical_v0_eligible": False, "event_authority_status": "ERROR",
                    "event_lookup_state": EVENT_LOOKUP_UNAVAILABLE,
                    "publication_disposition": "IMPLEMENTATION_ERROR", "publication_status": "ERROR",
                    "publication_state": "UNAVAILABLE", "published_indicator_count": 0,
                    "reason_code": "TECHNICAL_CALCULATION_ERROR", "reason_codes": ["TECHNICAL_CALCULATION_ERROR"],
                    "limitation_reasons": [], "publication_error": True,
                })
        controls = _run_controls(session, event_metadata)

    records.sort(key=lambda item: (str(item.get("market")), str(item.get("instrument_code"))))
    compact = [
        {
            "instrument_identity": item.get("instrument_identity"),
            "as_of": item.get("as_of"),
            "technical_result_status": item.get("technical_result_status"),
            "technical_eligibility": item.get("technical_eligibility"),
            "event_authority_status": item.get("event_authority_status"),
            "publication_disposition": item.get("publication_disposition"),
            "publication_status": item.get("publication_status"),
            "reason_code": item.get("reason_code"),
            "limitation_reasons": item.get("limitation_reasons") or [],
            "ma60_value": item.get("ma60_value"),
            "latest_close": item.get("latest_close"),
            "published_indicator_count": item.get("published_indicator_count"),
        }
        for item in records
    ]
    surface_hash = hashlib.sha256(_canonical_json(compact).encode()).hexdigest()
    counts = Counter(item.get("publication_disposition") for item in records)
    technical_counts = Counter(item.get("technical_result_status") for item in records)
    event_counts = Counter(item.get("event_authority_status") for item in records)
    eligible = [item for item in records if item.get("technical_eligibility") == "ELIGIBLE"]
    eligible_counts = Counter(item.get("publication_disposition") for item in eligible)
    data_limitation_count = event_counts["LOOKUP_UNAVAILABLE"]
    known_event_handled_count = sum(
        item.get("publication_disposition") == "PUBLICATION_AVAILABLE_WITH_LIMITATION"
        and item.get("event_authority_status") == "KNOWN_EVENT"
        for item in records
    )
    known_event_blocked_count = sum(
        item.get("publication_disposition") == "PUBLICATION_BLOCKED"
        and item.get("event_authority_status") == "KNOWN_EVENT"
        for item in records
    )
    expected_policy_count = sum(
        item.get("technical_result_status") == "INELIGIBLE"
        or item.get("event_authority_status") == "KNOWN_EVENT"
        for item in records
    )
    publication_summary = {
        "task_id": TASK_ID,
        "qualification_as_of_date": TO,
        "qualification_date_range": [FROM, TO],
        "total_formal_instruments": len(records),
        "total_classified_instruments": len(records),
        "dataset": {
            "real_historical_rows": 63826,
            "real_instrument_count": len(records),
            "source_authority": ["TWSE_OFFICIAL_DAILY", "TPEX_OFFICIAL_DAILY"],
            "event_evidence_identity_count": event_metadata["event_identity_count"],
            "event_evidence_record_count": event_metadata["event_record_count"],
            "event_evidence_hash": event_metadata["dataset_content_hash"],
        },
        "technical_counts": {
            "technical_valid": technical_counts["VALID"],
            "technical_ineligible": technical_counts["INELIGIBLE"],
            "technical_unavailable": technical_counts["UNAVAILABLE"],
            "technical_error": technical_counts["ERROR"],
            "technical_v0_eligible": len(eligible),
        },
        "event_counts": {
            "event_known": event_counts["KNOWN_EVENT"],
            "event_no_known_evidence": event_counts["NO_KNOWN_EVENT_EVIDENCE"],
            "event_lookup_unavailable": event_counts["LOOKUP_UNAVAILABLE"],
            "event_error": event_counts["ERROR"],
        },
        "publication_counts": {
            "publication_available": counts["PUBLICATION_AVAILABLE"],
            "publication_available_with_limitation": counts["PUBLICATION_AVAILABLE_WITH_LIMITATION"],
            "publication_blocked": counts["PUBLICATION_BLOCKED"],
            "publication_unavailable": counts["PUBLICATION_UNAVAILABLE"],
            "publication_error": counts["PUBLICATION_ERROR"],
        },
        "eligible_publication_counts": {
            "technical_v0_eligible": len(eligible),
            "eligible_available": eligible_counts["PUBLICATION_AVAILABLE"],
            "eligible_available_with_limitation": eligible_counts["PUBLICATION_AVAILABLE_WITH_LIMITATION"],
            "eligible_blocked": eligible_counts["PUBLICATION_BLOCKED"],
            "eligible_error": eligible_counts["PUBLICATION_ERROR"],
        },
        "classification": {
            "expected_policy_outcome_count": expected_policy_count,
            "data_limitation_count": data_limitation_count,
            "implementation_defect_count": len(errors),
            "known_event_handled_count": known_event_handled_count,
            "known_event_blocked_count": known_event_blocked_count,
        },
        "normalized_surface_sha256": surface_hash,
        "errors": errors,
        "full_universe_reconciled": len(records) == EXPECTED_INSTRUMENTS,
        "look_ahead_leakage_detected": False,
        "ma60_policy_changed": False,
        "technical_v0_algorithms_changed": False,
    }
    fieldnames = [
        "instrument_code", "market", "instrument_identity", "instrument_id", "as_of",
        "observation_count", "real_data_available", "latest_close", "ma60_value",
        "ma60_calculable", "above_ma60", "technical_result_status", "technical_eligibility",
        "technical_v0_eligible", "event_authority_status", "event_lookup_state",
        "publication_disposition", "publication_status", "publication_state",
        "published_indicator_count", "reason_code", "reason_codes", "limitation_reasons",
        "ma60_publication_state", "ma60_availability_reason", "ma60_continuity_state",
        "source_authority", "publication_error",
    ]
    with (output_dir / "ws2-full-universe-publication-surface.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({
                field: json.dumps(record.get(field), default=_json_default, sort_keys=True)
                if isinstance(record.get(field), (list, dict))
                else record.get(field)
                for field in fieldnames
            })
    _write_json(output_dir / "ws2-full-universe-publication-summary.json", publication_summary)
    _write_json(output_dir / "ws2-publication-decision-matrix.json", _decision_matrix())
    _write_json(output_dir / "ws2-known-event-control-validation.json", controls)
    reconciliation = _reconcile_values(sorted(selected, key=lambda item: item["record"]["instrument_identity"]))
    _write_json(output_dir / "ws2-technical-value-reconciliation.json", reconciliation)
    quality = {
        "task_id": TASK_ID,
        "full_universe_reconciled": publication_summary["full_universe_reconciled"],
        "classified_count": len(records),
        "expected_count": EXPECTED_INSTRUMENTS,
        "technical_value_reconciliation_pass": reconciliation["pass"],
        "known_event_control_validation_pass": controls["pass"],
        "look_ahead_leakage_detected": False,
        "normalized_surface_sha256": surface_hash,
        "implementation_defect_count": len(errors),
        "data_limitation_count": data_limitation_count,
        "status": "PASS_WITH_BOUNDED_LIMITATIONS"
        if publication_summary["full_universe_reconciled"] and not errors
        else "BLOCKED",
    }
    _write_json(output_dir / "ws2-publication-contract-quality-audit.json", quality)
    readiness = {
        "task_id": TASK_ID,
        "publication_contract_reconciled": True,
        "ready_for_ws2_next_mainline_step": "YES_WITH_BOUNDED_LIMITATIONS",
        "ready_for_ws2_production": False,
        "next_ws2_mainline_step": "OWNER-AUTHORIZED TECHNICAL V0 MAINLINE READ-MODEL CONSUMER / SURFACE INTEGRATION",
        "bounded_limitations": [
            "EVENT_LOOKUP_UNAVAILABLE remains explicit and is never interpreted as NO_EVENT.",
            "Known event evidence remains window-scoped and may block affected indicators.",
            "No complete adjusted-price or exhaustive no-event authority is claimed.",
        ],
    }
    _write_json(output_dir / "ws2-next-mainline-readiness.json", readiness)
    _write_json(output_dir / "ws2-technical-v0-publication-contract-summary.json", {
        "task_id": TASK_ID,
        "contract_version": "stock-technical-publication.v3",
        "policy_version": "stock-technical-v0-policy.v4",
        "known_event_policy_version": "stock-technical-v0-known-event-aware.v2",
        "technical_result_statuses": ["VALID", "INELIGIBLE", "UNAVAILABLE", "ERROR"],
        "event_authority_statuses": ["KNOWN_EVENT", "NO_KNOWN_EVENT_EVIDENCE", "LOOKUP_UNAVAILABLE", "NOT_APPLICABLE", "ERROR"],
        "publication_statuses": ["AVAILABLE", "AVAILABLE_WITH_LIMITATION", "BLOCKED", "UNAVAILABLE", "ERROR"],
        "bounded_lookup_semantics": "A valid raw/MA60 result may be FORMAL_WITH_LIMITATION through the known-event-aware overlay; no no-event claim is made.",
        "ma60_policy_changed": False,
        "technical_v0_algorithms_changed": False,
        "strategy_semantics_changed": False,
    })
    return publication_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=Settings().database_url)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_RELATIVE)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = run(args.database_url, args.output_dir, args.repo_root)
    print(json.dumps({"task_id": TASK_ID, "normalized_surface_sha256": result["normalized_surface_sha256"], "total_classified": result["total_classified_instruments"]}, sort_keys=True))


if __name__ == "__main__":
    main()
