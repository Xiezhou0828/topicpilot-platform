"""FUND-C Opportunity institutional-evidence read-model adapter.

This module is deliberately provider-neutral.  FUND-B owns fetching,
normalisation, persistence, rolling windows, streaks, reversals, price-flow,
divergence, and liquidity-relative calculations.  FUND-C only validates the
canonical FUND-B projection, applies Opportunity-date safety, and exposes the
evidence as an optional read-model extension with no selection effect.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import date, datetime
from typing import Any

from ..market_data.stock_institutional_flow import (
    STOCK_FLOW_SCALE,
    STOCK_FLOW_UNIT,
    StockInstitutionalFlowFeatures,
)

OPPORTUNITY_INSTITUTIONAL_EVIDENCE_CONTRACT_VERSION = "opportunity-institutional-evidence.v1"
FUND_B_STOCK_FLOW_CONTRACT_VERSION = "fund-b.stock-institutional-flow.v1"
INSTITUTIONAL_ALIGNMENT_CLASSIFICATION = "POLICY_DECISION_REQUIRED"
INSTITUTIONAL_SELECTION_EFFECT = "NONE"

_ALLOWED_MARKETS = {"TPE", "TWO"}
_ALLOWED_STATUS = {
    "OK",
    "NO_DATA",
    "NOT_TRADING_DAY",
    "PROVIDER_UNAVAILABLE",
    "AUTH_ERROR",
    "RATE_LIMITED",
    "SCHEMA_ERROR",
    "MAPPING_ERROR",
    "PARTIAL",
    "STALE",
    "UNKNOWN",
}
_ALLOWED_FRESHNESS = {"CURRENT", "STALE", "UNKNOWN"}
_WINDOW_REQUIREMENTS = {"oneDay": 1, "fiveDay": 5, "tenDay": 10, "twentyDay": 20}
_STREAK_KEYS = ("foreign", "investmentTrust", "dealer", "total")


def _date_value(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _canonical_mapping(
    flow: StockInstitutionalFlowFeatures | Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if flow is None:
        return None
    if isinstance(flow, StockInstitutionalFlowFeatures):
        return deepcopy(flow.to_dict())
    if isinstance(flow, Mapping):
        return deepcopy(dict(flow))
    return None


def _alignment() -> dict[str, str]:
    return {
        "classification": INSTITUTIONAL_ALIGNMENT_CLASSIFICATION,
        "status": "NOT_EVALUATED",
        "selectionEffect": INSTITUTIONAL_SELECTION_EFFECT,
    }


def _unavailable_window(required_sessions: int) -> dict[str, Any]:
    return {
        "requiredSessions": required_sessions,
        "observedSessions": 0,
        "complete": False,
        "foreignNet": None,
        "investmentTrustNet": None,
        "dealerNet": None,
        "totalNet": None,
        "unit": STOCK_FLOW_UNIT,
        "scale": STOCK_FLOW_SCALE,
    }


def _unavailable_dimensions(reason: str) -> dict[str, Any]:
    return {
        "rolling": {
            key: _unavailable_window(required) for key, required in _WINDOW_REQUIREMENTS.items()
        },
        "streaks": {
            key: {"direction": "UNKNOWN", "sessions": 0, "status": "UNAVAILABLE"}
            for key in _STREAK_KEYS
        },
        "reversal": {
            "state": "UNAVAILABLE",
            "currentDirection": "UNKNOWN",
            "priorDirection": "UNKNOWN",
            "status": "UNAVAILABLE",
        },
        "priceFlow": {
            "state": "UNAVAILABLE",
            "priceDirection": "UNKNOWN",
            "flowDirection": "UNKNOWN",
            "priceChange": None,
            "institutionalNet": None,
            "priceBasis": "RAW_OBSERVED",
            "status": "UNAVAILABLE",
        },
        "divergence": {
            "state": "UNAVAILABLE",
            "condition": reason,
            "status": "UNAVAILABLE",
        },
        "unusualFlow": {
            "state": "POLICY_DECISION_REQUIRED",
            "metric": None,
            "status": "DEFERRED",
            "reason": "NO_OWNER_APPROVED_ABNORMAL_FLOW_FORMULA",
        },
        "liquidityRelative": {
            "state": "UNAVAILABLE",
            "ratio": None,
            "institutionalNet": None,
            "dailyVolume": None,
            "numeratorUnit": STOCK_FLOW_UNIT,
            "denominatorUnit": STOCK_FLOW_UNIT,
            "status": "UNAVAILABLE",
        },
    }


def _base_payload(
    *,
    instrument_id: str | None,
    symbol: str,
    market: str,
    requested_date: date | None,
    availability: str,
    freshness: str,
    reason: str,
) -> dict[str, Any]:
    payload = {
        "contractVersion": OPPORTUNITY_INSTITUTIONAL_EVIDENCE_CONTRACT_VERSION,
        "evidenceType": "STOCK_INSTITUTIONAL_FLOW",
        "instrumentId": instrument_id,
        "symbol": symbol,
        "market": market,
        "requestedDate": requested_date,
        "tradingDate": None,
        "latestAvailableSession": None,
        "availability": availability,
        "freshness": freshness,
        "statusReason": reason,
        "sourceAsOf": None,
        "fetchedAt": None,
        "today": None,
        "sessions": [],
        "source": None,
        "unit": STOCK_FLOW_UNIT,
        "scale": STOCK_FLOW_SCALE,
        "alignment": _alignment(),
        "canonicalEvidence": None,
    }
    payload.update(_unavailable_dimensions(reason))
    return payload


def _error_payload(
    *,
    instrument_id: str | None,
    symbol: str,
    market: str,
    requested_date: date | None,
    availability: str,
    freshness: str,
    reason: str,
) -> dict[str, Any]:
    return _base_payload(
        instrument_id=instrument_id,
        symbol=symbol,
        market=market,
        requested_date=requested_date,
        availability=availability,
        freshness=freshness,
        reason=reason,
    )


def _invalid_mapping(
    *,
    instrument_id: str | None,
    symbol: str,
    market: str,
    requested_date: date | None,
    reason: str,
) -> dict[str, Any]:
    return _error_payload(
        instrument_id=instrument_id,
        symbol=symbol,
        market=market,
        requested_date=requested_date,
        availability="MAPPING_ERROR",
        freshness="UNKNOWN",
        reason=reason,
    )


def _future_dates(payload: Mapping[str, Any], requested_date: date) -> bool:
    candidates: list[date] = []
    for key in ("requestedAsOf", "asOfDate", "latestAvailableDate"):
        value = _date_value(payload.get(key))
        if value is not None:
            candidates.append(value)
    today = payload.get("today")
    if isinstance(today, Mapping):
        value = _date_value(today.get("tradingDate"))
        if value is not None:
            candidates.append(value)
    sessions = payload.get("sessions")
    if isinstance(sessions, list):
        for session in sessions:
            if isinstance(session, Mapping):
                value = _date_value(session.get("tradingDate"))
                if value is not None:
                    candidates.append(value)
    return any(value > requested_date for value in candidates)


def _validated_payload(
    payload: Mapping[str, Any],
    *,
    instrument_id: str | None,
    symbol: str,
    market: str,
    opportunity_as_of: date,
) -> dict[str, Any] | None:
    if payload.get("contractVersion") != FUND_B_STOCK_FLOW_CONTRACT_VERSION:
        return _invalid_mapping(
            instrument_id=instrument_id,
            symbol=symbol,
            market=market,
            requested_date=opportunity_as_of,
            reason="FUND_B_CONTRACT_VERSION_MISMATCH",
        )
    if market not in _ALLOWED_MARKETS:
        return _invalid_mapping(
            instrument_id=instrument_id,
            symbol=symbol,
            market=market,
            requested_date=opportunity_as_of,
            reason="OPPORTUNITY_MARKET_INVALID",
        )
    requested_date = _date_value(payload.get("requestedAsOf"))
    if requested_date is None:
        return _invalid_mapping(
            instrument_id=instrument_id,
            symbol=symbol,
            market=market,
            requested_date=opportunity_as_of,
            reason="FUND_B_REQUESTED_DATE_MISSING",
        )
    if requested_date != opportunity_as_of:
        status = "MAPPING_ERROR" if requested_date > opportunity_as_of else "STALE"
        freshness = "STALE" if status == "STALE" else "UNKNOWN"
        return _error_payload(
            instrument_id=instrument_id,
            symbol=symbol,
            market=market,
            requested_date=opportunity_as_of,
            availability=status,
            freshness=freshness,
            reason=(
                "FUTURE_REQUESTED_DATE_REJECTED"
                if requested_date > opportunity_as_of
                else "OPPORTUNITY_DATE_MISMATCH"
            ),
        )
    canonical_market = payload.get("market")
    canonical_symbol = payload.get("instrumentCode")
    canonical_instrument = payload.get("instrumentId")
    if canonical_market != market or canonical_symbol != symbol:
        return _invalid_mapping(
            instrument_id=instrument_id,
            symbol=symbol,
            market=market,
            requested_date=opportunity_as_of,
            reason="FUND_B_INSTRUMENT_IDENTITY_MISMATCH",
        )
    if (
        instrument_id is not None
        and canonical_instrument is not None
        and canonical_instrument != instrument_id
    ):
        return _invalid_mapping(
            instrument_id=instrument_id,
            symbol=symbol,
            market=market,
            requested_date=opportunity_as_of,
            reason="FUND_B_CANONICAL_INSTRUMENT_ID_MISMATCH",
        )
    if payload.get("unit") != STOCK_FLOW_UNIT or payload.get("scale") != STOCK_FLOW_SCALE:
        return _invalid_mapping(
            instrument_id=instrument_id,
            symbol=symbol,
            market=market,
            requested_date=opportunity_as_of,
            reason="FUND_B_UNIT_SCALE_MISMATCH",
        )
    availability = payload.get("status")
    freshness = payload.get("freshness")
    if availability not in _ALLOWED_STATUS or freshness not in _ALLOWED_FRESHNESS:
        return _invalid_mapping(
            instrument_id=instrument_id,
            symbol=symbol,
            market=market,
            requested_date=opportunity_as_of,
            reason="FUND_B_STATUS_VOCABULARY_INVALID",
        )
    if _future_dates(payload, opportunity_as_of):
        return _invalid_mapping(
            instrument_id=instrument_id,
            symbol=symbol,
            market=market,
            requested_date=opportunity_as_of,
            reason="FUTURE_TRADING_SESSION_REJECTED",
        )
    return None


def adapt_fund_b_institutional_flow(
    flow: StockInstitutionalFlowFeatures | Mapping[str, Any] | None,
    *,
    opportunity_as_of: date | None,
    instrument_id: str | None,
    symbol: str,
    market: str,
) -> dict[str, Any]:
    """Expose FUND-B stock flow evidence in an Opportunity context.

    No provider is called and no FUND-B-derived value is recalculated here.
    A missing Opportunity date, malformed canonical mapping, identity mismatch,
    or future session fails closed with explicit unavailable dimensions.
    """

    if opportunity_as_of is None:
        return _invalid_mapping(
            instrument_id=instrument_id,
            symbol=symbol,
            market=market,
            requested_date=None,
            reason="OPPORTUNITY_AS_OF_UNAVAILABLE",
        )
    canonical = _canonical_mapping(flow)
    if canonical is None:
        return _error_payload(
            instrument_id=instrument_id,
            symbol=symbol,
            market=market,
            requested_date=opportunity_as_of,
            availability="NO_DATA",
            freshness="UNKNOWN",
            reason="NO_FUND_B_INSTITUTIONAL_FLOW_EVIDENCE",
        )
    error = _validated_payload(
        canonical,
        instrument_id=instrument_id,
        symbol=symbol,
        market=market,
        opportunity_as_of=opportunity_as_of,
    )
    if error is not None:
        return error

    availability = str(canonical["status"])
    freshness = str(canonical["freshness"])
    as_of_date = _date_value(canonical.get("asOfDate"))
    latest_available = _date_value(canonical.get("latestAvailableDate"))
    current = canonical.get("today")
    sessions = canonical.get("sessions")
    windows = canonical.get("windows")
    streaks = canonical.get("streaks")
    source = canonical.get("source")
    current_date = _date_value(current.get("tradingDate")) if isinstance(current, Mapping) else None
    current_aligned = current_date == opportunity_as_of
    status_reason = canonical.get("statusReason")

    result = _base_payload(
        instrument_id=instrument_id,
        symbol=symbol,
        market=market,
        requested_date=opportunity_as_of,
        availability=availability,
        freshness=freshness,
        reason=str(status_reason or "FUND_B_EVIDENCE_MAPPED"),
    )
    result.update(
        {
            "tradingDate": as_of_date if current_aligned and freshness != "STALE" else None,
            "latestAvailableSession": latest_available,
            "sourceAsOf": canonical.get("sourceAsOf"),
            "fetchedAt": (current.get("retrievedAt") if isinstance(current, Mapping) else None),
            "source": deepcopy(source) if isinstance(source, Mapping) else None,
            "canonicalEvidence": deepcopy(canonical),
        }
    )
    if isinstance(sessions, list):
        result["sessions"] = deepcopy(sessions)
    if current_aligned and availability in {"OK", "PARTIAL"} and freshness != "STALE":
        result["today"] = deepcopy(current) if isinstance(current, Mapping) else None
        if isinstance(windows, Mapping):
            result["rolling"] = deepcopy(dict(windows))
        if isinstance(streaks, Mapping):
            result["streaks"] = deepcopy(dict(streaks))
        for key in (
            "reversal",
            "priceFlow",
            "divergence",
            "unusualFlow",
            "liquidityRelative",
        ):
            if isinstance(canonical.get(key), Mapping):
                result[key] = deepcopy(canonical[key])
    else:
        result["statusReason"] = str(status_reason or "FUND_B_CURRENT_SESSION_NOT_ALIGNED")
    return result


__all__ = [
    "FUND_B_STOCK_FLOW_CONTRACT_VERSION",
    "INSTITUTIONAL_ALIGNMENT_CLASSIFICATION",
    "INSTITUTIONAL_SELECTION_EFFECT",
    "OPPORTUNITY_INSTITUTIONAL_EVIDENCE_CONTRACT_VERSION",
    "adapt_fund_b_institutional_flow",
]
