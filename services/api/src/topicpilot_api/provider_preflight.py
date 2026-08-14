"""Read-only G2 official TWSE/TPEx provider and data preflight."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from topicpilot_api.instrument_universe import (
    InstrumentLifecycle,
    InstrumentUniverseRow,
    LifecycleValidationError,
    build_date_effective_instrument_universe,
)
from topicpilot_api.market_data.lineage import (
    EXPECTED_TPEX_ADAPTER_VERSION,
    EXPECTED_TWSE_ADAPTER_VERSION,
)
from topicpilot_api.market_data.registry import build_historical_provider_registry
from topicpilot_api.orm.models import (
    Instrument,
    Market,
    ReferenceCalendarDate,
    ReferenceInstrumentLifecycle,
    ReferenceRegistrySet,
)
from topicpilot_api.reference_check import inspect_reference_preflight

G2_GATE = "G2"
REFERENCE_VERSION = "tw-reference-v1"
REQUIRED_SESSION_CODE = "REGULAR"
REQUIRED_CALENDAR_CODE = "TW_MARKET"
CANONICAL_MARKETS = ("TPE", "TWO")
PRODUCTION_WRITE_SET: tuple[str, ...] = ()

PROVIDER_AUTHORITY_BY_MARKET = {
    "TPE": "TWSE_OFFICIAL_DAILY",
    "TWO": "TPEX_OFFICIAL_DAILY",
}
PROVIDER_VERSION_BY_MARKET = {
    "TPE": EXPECTED_TWSE_ADAPTER_VERSION,
    "TWO": EXPECTED_TPEX_ADAPTER_VERSION,
}
EXCHANGE_CODE_BY_MARKET = {"TPE": "TWSE", "TWO": "TPEx"}
TIMEZONE_BY_MARKET = {"TPE": "Asia/Taipei", "TWO": "Asia/Taipei"}

Transport = Callable[[str, float], bytes]


@dataclass(frozen=True)
class G2MarketContext:
    market_code: str
    provider_authority: str
    provider_version: str
    exchange_code: str | None
    timezone: str | None
    calendar_code: str | None
    instrument_codes: tuple[str, ...]

    @property
    def context_ready(self) -> bool:
        return (
            self.exchange_code == EXCHANGE_CODE_BY_MARKET[self.market_code]
            and self.timezone == TIMEZONE_BY_MARKET[self.market_code]
            and self.calendar_code == REQUIRED_CALENDAR_CODE
            and bool(self.instrument_codes)
        )


@dataclass(frozen=True)
class G2PreflightContext:
    reference_result: dict[str, Any]
    target_date: date
    target_date_is_session: bool
    target_date_reason: str | None
    markets: tuple[G2MarketContext, ...]
    eligibility_error: str | None = None

    @property
    def context_ready(self) -> bool:
        return (
            self.reference_result.get("referenceLoadStatus") == "READY"
            and self.target_date_is_session
            and self.eligibility_error is None
            and all(market.context_ready for market in self.markets)
        )


@dataclass(frozen=True)
class G2MarketFetch:
    market_code: str
    provider_authority: str
    provider_version: str
    target_date: date
    record_codes: frozenset[str]
    record_count: int
    payload_parsed: bool = True
    reachable: bool = True


@dataclass(frozen=True)
class G2MarketFailure:
    error_code: str
    provider_version: str | None = None
    reachable: bool = False
    payload_parsed: bool = False
    target_date_matched: bool = False


def _reference_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "referenceVersion": result.get("referenceVersion"),
        "referenceActive": result.get("referenceActive"),
        "referenceLoadStatus": result.get("referenceLoadStatus"),
        "marketCount": result.get("marketCount"),
        "instrumentCount": result.get("instrumentCount"),
        "missingMarkets": result.get("missingMarkets", []),
        "missingInstruments": result.get("missingInstruments", []),
        "duplicateIdentities": result.get("duplicateIdentities", []),
        "missingReferenceContexts": result.get("missingReferenceContexts", []),
        "calendarDateCount": result.get("calendarDateCount", 0),
    }


def _market_evidence(
    context: G2MarketContext,
    *,
    reachable: bool,
    payload_parsed: bool,
    target_date_matched: bool,
    data_available: bool,
    coverage_complete: bool,
    record_count: int,
    covered_instrument_count: int,
    error_code: str | None,
    provider_version: str | None = None,
    missing_identity_codes: tuple[str, ...] = (),
    extra_identity_codes: tuple[str, ...] = (),
) -> dict[str, Any]:
    status = (
        "PASS"
        if (
            reachable
            and payload_parsed
            and target_date_matched
            and data_available
            and coverage_complete
            and provider_version == context.provider_version
        )
        else "FAIL"
    )
    expected_count = len(context.instrument_codes)
    return {
        "marketCode": context.market_code,
        "providerAuthority": context.provider_authority,
        "providerVersion": provider_version or context.provider_version,
        "expectedAdapterVersion": context.provider_version,
        "reachable": reachable,
        "payloadParsed": payload_parsed,
        "targetDateMatched": target_date_matched,
        "dataAvailable": data_available,
        "recordCount": record_count,
        "expectedInstrumentCount": expected_count,
        "coveredInstrumentCount": covered_instrument_count,
        "missingInstrumentCount": max(0, expected_count - covered_instrument_count),
        "missingIdentityCodes": list(sorted(missing_identity_codes)),
        "extraIdentityCodes": list(sorted(extra_identity_codes)),
        "extraInstrumentCount": len(extra_identity_codes),
        "coverageComplete": coverage_complete,
        "status": status,
        "errorCode": error_code,
    }


def evaluate_provider_preflight(
    context: G2PreflightContext,
    market_results: Mapping[str, G2MarketFetch | G2MarketFailure],
) -> dict[str, Any]:
    """Evaluate sanitized market evidence without database or persistence access."""

    evidence: list[dict[str, Any]] = []
    for market in context.markets:
        result = market_results.get(
            market.market_code,
            G2MarketFailure("PROVIDER_RESULT_MISSING"),
        )
        if isinstance(result, G2MarketFailure):
            evidence.append(
                _market_evidence(
                    market,
                    reachable=result.reachable,
                    payload_parsed=result.payload_parsed,
                    target_date_matched=result.target_date_matched,
                    data_available=False,
                    coverage_complete=False,
                    record_count=0,
                    covered_instrument_count=0,
                    error_code=result.error_code,
                    provider_version=result.provider_version,
                    missing_identity_codes=tuple(market.instrument_codes),
                )
            )
            continue

        codes = set(result.record_codes)
        expected_codes = set(market.instrument_codes)
        covered_count = len(expected_codes & codes)
        missing_codes = tuple(sorted(expected_codes - codes))
        extra_codes = tuple(sorted(codes - expected_codes))
        target_date_matched = result.target_date == context.target_date
        # The official market-level endpoint may include securities outside
        # the date-effective formal EQUITY universe (for example ETFs,
        # warrants, or other exchange-listed products).  G2 coverage is an
        # expected-universe contract: every expected identity must be present.
        # Preserve out-of-scope provider codes in the evidence, but do not let
        # them turn complete expected-EQUITY coverage into a failure.
        coverage_complete = bool(expected_codes) and not missing_codes
        authority_ok = result.provider_authority == market.provider_authority
        version_ok = result.provider_version == market.provider_version
        error_code = None
        if not authority_ok or not version_ok:
            error_code = "PROVIDER_AUTHORITY_MISMATCH"
        elif not target_date_matched:
            error_code = "PROVIDER_DATE_MISMATCH"
        elif result.record_count == 0:
            error_code = "EMPTY_MARKET_PAYLOAD"
        elif missing_codes:
            error_code = "PARTIAL_PROVIDER_COVERAGE"
        evidence.append(
            _market_evidence(
                market,
                reachable=result.reachable,
                payload_parsed=result.payload_parsed,
                target_date_matched=target_date_matched,
                data_available=result.record_count > 0,
                coverage_complete=coverage_complete,
                record_count=result.record_count,
                covered_instrument_count=covered_count,
                error_code=error_code,
                provider_version=result.provider_version,
                missing_identity_codes=missing_codes,
                extra_identity_codes=extra_codes,
            )
        )

    context_ok = context.context_ready
    status = "PASS" if context_ok and all(item["status"] == "PASS" for item in evidence) else "FAIL"
    return {
        "gate": G2_GATE,
        "status": status,
        "referenceVersion": context.reference_result.get("referenceVersion"),
        "targetDate": context.target_date.isoformat(),
        "targetDateIsSession": context.target_date_is_session,
        "targetDateReason": context.target_date_reason,
        "eligibilityError": context.eligibility_error,
        "readOnly": True,
        "productionWriteSet": list(PRODUCTION_WRITE_SET),
        "nonReferenceWriteSet": [],
        "fallbackAllowed": False,
        "reference": _reference_summary(context.reference_result),
        "markets": evidence,
    }


def load_g2_preflight_context(
    session: Session,
    *,
    target_date: date,
    reference_version: str = REFERENCE_VERSION,
) -> G2PreflightContext:
    """Load reference/calendar/identity context through SELECT-only queries."""

    reference_result = inspect_reference_preflight(
        session,
        requested_version=reference_version,
        expected_market_codes=CANONICAL_MARKETS,
        required_session_code=REQUIRED_SESSION_CODE,
        required_calendar_code=REQUIRED_CALENDAR_CODE,
    )
    registry_sets = list(
        session.scalars(
            select(ReferenceRegistrySet).where(
                ReferenceRegistrySet.reference_data_version == reference_version
            )
        )
    )
    registry_id = registry_sets[0].id if len(registry_sets) == 1 else None
    calendar_kind = None
    if registry_id is not None:
        calendar_kind = session.scalar(
            select(ReferenceCalendarDate.date_kind).where(
                ReferenceCalendarDate.registry_set_id == registry_id,
                ReferenceCalendarDate.calendar_code == REQUIRED_CALENDAR_CODE,
                ReferenceCalendarDate.calendar_date == target_date,
            )
        )

    market_rows = {
        row.code: row
        for row in session.scalars(select(Market).where(Market.code.in_(CANONICAL_MARKETS))).all()
    }
    instrument_rows = session.execute(
        select(
            Instrument.id,
            Instrument.instrument_code,
            Market.code,
            Instrument.instrument_type,
            Instrument.is_active.label("instrument_is_active"),
            Instrument.valid_from.label("instrument_valid_from"),
            Instrument.valid_to.label("instrument_valid_to"),
            Market.is_active.label("market_is_active"),
            Market.valid_from.label("market_valid_from"),
            Market.valid_to.label("market_valid_to"),
        )
        .join(Market, Market.id == Instrument.market_id)
        .where(
            Market.code.in_(CANONICAL_MARKETS),
        )
    ).all()
    lifecycle_by_instrument: dict[Any, list[InstrumentLifecycle]] = defaultdict(list)
    if registry_id is not None:
        lifecycle_rows = session.execute(
            select(
                ReferenceInstrumentLifecycle.instrument_id,
                ReferenceInstrumentLifecycle.status_code,
                ReferenceInstrumentLifecycle.effective_from,
                ReferenceInstrumentLifecycle.effective_to,
                ReferenceInstrumentLifecycle.evidence_id,
            ).where(ReferenceInstrumentLifecycle.registry_set_id == registry_id)
        ).all()
        for row in lifecycle_rows:
            lifecycle_by_instrument[row.instrument_id].append(
                InstrumentLifecycle(
                    status_code=row.status_code,
                    effective_from=row.effective_from,
                    effective_to=row.effective_to,
                    evidence_id=row.evidence_id,
                )
            )

    universe_rows = [
        InstrumentUniverseRow(
            market_code=str(row.code),
            instrument_code=str(row.instrument_code),
            instrument_type=row.instrument_type,
            is_active=row.instrument_is_active,
            valid_from=row.instrument_valid_from,
            valid_to=row.instrument_valid_to,
            market_is_active=row.market_is_active,
            market_valid_from=row.market_valid_from,
            market_valid_to=row.market_valid_to,
            lifecycle_events=tuple(lifecycle_by_instrument.get(row.id, ())),
        )
        for row in instrument_rows
    ]
    eligibility_error = None
    try:
        instruments_by_market = build_date_effective_instrument_universe(
            universe_rows,
            target_date,
            expected_markets=CANONICAL_MARKETS,
        )
    except LifecycleValidationError as exc:
        eligibility_error = str(exc)
        instruments_by_market = {market_code: () for market_code in CANONICAL_MARKETS}

    if eligibility_error is not None:
        target_reason = "LIFECYCLE_CONTEXT_INVALID"
    elif reference_result.get("referenceLoadStatus") != "READY":
        target_reason = "REFERENCE_CONTEXT_NOT_READY"
    elif target_date.weekday() >= 5:
        target_reason = "TARGET_DATE_WEEKEND"
    elif calendar_kind is not None:
        target_reason = f"TARGET_DATE_CLOSED_{calendar_kind}"
    else:
        target_reason = None

    markets = tuple(
        G2MarketContext(
            market_code=market_code,
            provider_authority=PROVIDER_AUTHORITY_BY_MARKET[market_code],
            provider_version=PROVIDER_VERSION_BY_MARKET[market_code],
            exchange_code=getattr(market_rows.get(market_code), "exchange_code", None),
            timezone=getattr(market_rows.get(market_code), "timezone", None),
            calendar_code=getattr(market_rows.get(market_code), "calendar_code", None),
            instrument_codes=tuple(sorted(instruments_by_market.get(market_code, ()))),
        )
        for market_code in CANONICAL_MARKETS
    )
    return G2PreflightContext(
        reference_result=reference_result,
        target_date=target_date,
        target_date_is_session=target_reason is None,
        target_date_reason=target_reason,
        markets=markets,
        eligibility_error=eligibility_error,
    )


def _provider_failure(exc: Exception) -> G2MarketFailure:
    code = getattr(exc, "code", None)
    if not isinstance(code, str) or not code:
        code = "PROVIDER_REQUEST_FAILED"
    parsed_codes = {
        "EXCHANGE_NO_DATA",
        "INVALID_PAYLOAD",
        "DUPLICATE_INSTRUMENT_ROW",
        "INVALID_OHLC",
        "INVALID_VOLUME",
        "INVALID_NUMBER",
        "PROVIDER_DATE_MISMATCH",
    }
    return G2MarketFailure(
        error_code=code,
        reachable=code in parsed_codes,
        payload_parsed=code in parsed_codes,
        target_date_matched=code != "PROVIDER_DATE_MISMATCH",
    )


def run_provider_preflight(
    session: Session,
    *,
    target_date: date,
    reference_version: str = REFERENCE_VERSION,
    transport: Transport | None = None,
) -> dict[str, Any]:
    """Run the official market-batch preflight without writes or fallback."""

    context = load_g2_preflight_context(
        session,
        target_date=target_date,
        reference_version=reference_version,
    )
    if not context.context_ready:
        market_results = {
            market.market_code: G2MarketFailure(
                "LIFECYCLE_CONTEXT_INVALID"
                if context.eligibility_error is not None
                else "TARGET_DATE_NOT_SESSION"
                if not context.target_date_is_session
                else "REFERENCE_OR_MARKET_CONTEXT_NOT_READY"
            )
            for market in context.markets
        }
        return evaluate_provider_preflight(context, market_results)

    registry = build_historical_provider_registry(
        start_date=target_date,
        end_date=target_date,
        exchange_transport=transport,
        market_batch=True,
    )
    market_results: dict[str, G2MarketFetch | G2MarketFailure] = {}
    for market in context.markets:
        registrations = registry.for_market(market.market_code)
        if len(registrations) != 1:
            market_results[market.market_code] = G2MarketFailure("PROVIDER_AUTHORITY_MISMATCH")
            continue
        registration = registrations[0]
        registration_version = getattr(registration.adapter, "adapter_version", None)
        if (
            registration.code != market.provider_authority
            or registration_version != market.provider_version
            or not getattr(registration.adapter, "market_batch", False)
        ):
            market_results[market.market_code] = G2MarketFailure(
                "PROVIDER_AUTHORITY_MISMATCH",
                provider_version=registration_version,
            )
            continue
        fetch_market_day = getattr(registration.adapter, "fetch_market_day", None)
        if not callable(fetch_market_day):
            market_results[market.market_code] = G2MarketFailure(
                "MARKET_BATCH_CAPABILITY_MISSING",
                provider_version=registration.adapter_version,
            )
            continue
        try:
            _, bars = fetch_market_day()
            market_results[market.market_code] = G2MarketFetch(
                market_code=market.market_code,
                provider_authority=registration.code,
                provider_version=registration_version,
                target_date=target_date,
                record_codes=frozenset(bars),
                record_count=len(bars),
            )
        except Exception as exc:
            market_results[market.market_code] = _provider_failure(exc)
    return evaluate_provider_preflight(context, market_results)


def build_database_failure_result(
    *,
    target_date: date,
    reference_version: str,
    error_code: str = "REFERENCE_CONTEXT_READ_FAILED",
) -> dict[str, Any]:
    """Return a secret-safe fail result when SELECT-only context loading fails."""

    return {
        "gate": G2_GATE,
        "status": "FAIL",
        "referenceVersion": reference_version,
        "targetDate": target_date.isoformat(),
        "targetDateIsSession": False,
        "targetDateReason": "REFERENCE_CONTEXT_READ_FAILED",
        "eligibilityError": None,
        "readOnly": True,
        "productionWriteSet": [],
        "nonReferenceWriteSet": [],
        "fallbackAllowed": False,
        "reference": {
            "referenceVersion": reference_version,
            "referenceLoadStatus": "NOT_READY",
            "errorCode": error_code,
        },
        "markets": [
            {
                "marketCode": market_code,
                "providerAuthority": PROVIDER_AUTHORITY_BY_MARKET[market_code],
                "providerVersion": PROVIDER_VERSION_BY_MARKET[market_code],
                "expectedAdapterVersion": PROVIDER_VERSION_BY_MARKET[market_code],
                "reachable": False,
                "payloadParsed": False,
                "targetDateMatched": False,
                "dataAvailable": False,
                "recordCount": 0,
                "expectedInstrumentCount": 0,
                "coveredInstrumentCount": 0,
                "missingInstrumentCount": 0,
                "missingIdentityCodes": [],
                "extraIdentityCodes": [],
                "extraInstrumentCount": 0,
                "coverageComplete": False,
                "status": "FAIL",
                "errorCode": error_code,
            }
            for market_code in CANONICAL_MARKETS
        ],
    }


__all__ = [
    "CANONICAL_MARKETS",
    "PRODUCTION_WRITE_SET",
    "G2MarketContext",
    "G2MarketFailure",
    "G2MarketFetch",
    "G2PreflightContext",
    "build_database_failure_result",
    "evaluate_provider_preflight",
    "load_g2_preflight_context",
    "run_provider_preflight",
]
