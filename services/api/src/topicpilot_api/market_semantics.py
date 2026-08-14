"""Read-only G3 market/lifecycle semantics validation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from topicpilot_api.instrument_universe import (
    LifecycleValidationError,
    evaluate_instrument_eligibility,
)
from topicpilot_api.market_data.registry import build_historical_provider_registry
from topicpilot_api.provider_preflight import (
    CANONICAL_MARKETS,
    EXCHANGE_CODE_BY_MARKET,
    REQUIRED_CALENDAR_CODE,
    TIMEZONE_BY_MARKET,
    G2PreflightContext,
    load_g2_preflight_context,
)

G3_GATE = "G3"
PRODUCTION_WRITE_SET: tuple[str, ...] = ()
Transport = Callable[[str, float], bytes]


@dataclass(frozen=True)
class G3MarketContext:
    market_code: str
    provider_authority: str
    provider_version: str
    exchange_code: str | None
    timezone: str | None
    calendar_code: str | None
    expected_instrument_codes: tuple[str, ...]
    invalid_lifecycle_identity_codes: tuple[str, ...] = ()
    duplicate_expected_identity_codes: tuple[str, ...] = ()
    unexpected_market_codes: tuple[str, ...] = ()

    @property
    def context_ready(self) -> bool:
        return (
            self.exchange_code == EXCHANGE_CODE_BY_MARKET[self.market_code]
            and self.timezone == TIMEZONE_BY_MARKET[self.market_code]
            and self.calendar_code == REQUIRED_CALENDAR_CODE
            and bool(self.expected_instrument_codes)
            and not self.invalid_lifecycle_identity_codes
            and not self.duplicate_expected_identity_codes
            and not self.unexpected_market_codes
        )


@dataclass(frozen=True)
class G3PreflightContext:
    reference_result: dict[str, Any]
    target_date: date
    target_date_is_session: bool
    target_date_reason: str | None
    markets: tuple[G3MarketContext, ...]
    fallback_used: bool = False

    @property
    def context_ready(self) -> bool:
        return (
            self.reference_result.get("referenceLoadStatus") == "READY"
            and self.target_date_is_session
            and not self.fallback_used
            and all(market.context_ready for market in self.markets)
        )


@dataclass(frozen=True)
class G3MarketFetch:
    market_code: str
    provider_authority: str
    provider_version: str
    data_date: date | None
    record_codes: frozenset[str]
    record_count: int
    payload_parsed: bool = True
    reachable: bool = True


@dataclass(frozen=True)
class G3MarketFailure:
    error_code: str
    provider_version: str | None = None
    reachable: bool = False
    payload_parsed: bool = False
    data_date: date | None = None


def _market_contexts(context: G2PreflightContext) -> tuple[G3MarketContext, ...]:
    grouped: dict[str, set[str]] = defaultdict(set)
    invalid_by_market: dict[str, set[str]] = defaultdict(set)
    duplicates_by_market: dict[str, set[str]] = defaultdict(set)
    unexpected_markets: set[str] = set()
    seen: set[tuple[str, str]] = set()

    for row in context.universe_rows:
        identity = (row.market_code, row.instrument_code)
        if row.market_code not in CANONICAL_MARKETS:
            unexpected_markets.add(row.market_code)
            continue
        if identity in seen:
            duplicates_by_market[row.market_code].add(row.instrument_code)
            continue
        seen.add(identity)
        try:
            eligible = evaluate_instrument_eligibility(row, context.target_date).eligible
        except LifecycleValidationError:
            invalid_by_market[row.market_code].add(row.instrument_code)
            continue
        if eligible:
            grouped[row.market_code].add(row.instrument_code)

    markets: list[G3MarketContext] = []
    for market in context.markets:
        markets.append(
            G3MarketContext(
                market_code=market.market_code,
                provider_authority=market.provider_authority,
                provider_version=market.provider_version,
                exchange_code=market.exchange_code,
                timezone=market.timezone,
                calendar_code=market.calendar_code,
                expected_instrument_codes=tuple(sorted(grouped.get(market.market_code, set()))),
                invalid_lifecycle_identity_codes=tuple(
                    sorted(invalid_by_market.get(market.market_code, set()))
                ),
                duplicate_expected_identity_codes=tuple(
                    sorted(duplicates_by_market.get(market.market_code, set()))
                ),
                unexpected_market_codes=tuple(sorted(unexpected_markets)),
            )
        )
    return tuple(markets)


def build_g3_preflight_context(
    context: G2PreflightContext,
) -> G3PreflightContext:
    """Adapt the shared SELECT-only reference context to the G3 contract."""

    return G3PreflightContext(
        reference_result=context.reference_result,
        target_date=context.target_date,
        target_date_is_session=context.target_date_is_session,
        target_date_reason=context.target_date_reason,
        markets=_market_contexts(context),
    )


def _failure_reasons_for_context(context: G3PreflightContext) -> list[str]:
    reasons: set[str] = set()
    if context.reference_result.get("referenceLoadStatus") != "READY":
        reasons.add("REFERENCE_CONTEXT_NOT_READY")
    if not context.target_date_is_session:
        reasons.add(context.target_date_reason or "TARGET_DATE_NOT_SESSION")
    if context.fallback_used:
        reasons.add("FALLBACK_USED")
    for market in context.markets:
        if not market.context_ready:
            reasons.add(f"{market.market_code}:MARKET_CONTEXT_INVALID")
        reasons.update(
            f"{market.market_code}:INVALID_LIFECYCLE:{code}"
            for code in market.invalid_lifecycle_identity_codes
        )
        reasons.update(
            f"{market.market_code}:DUPLICATE_EXPECTED_IDENTITY:{code}"
            for code in market.duplicate_expected_identity_codes
        )
        reasons.update(
            f"{market.market_code}:UNEXPECTED_MARKET:{code}"
            for code in market.unexpected_market_codes
        )
    return sorted(reasons)


def _market_result(
    context: G3MarketContext,
    result: G3MarketFetch | G3MarketFailure,
    *,
    target_date: date,
) -> tuple[dict[str, Any], list[str]]:
    expected = set(context.expected_instrument_codes)
    reasons: set[str] = set()
    if isinstance(result, G3MarketFailure):
        reasons.add(result.error_code)
        market = {
            "status": "FAIL",
            "provider": context.provider_authority,
            "providerVersion": result.provider_version or context.provider_version,
            "dataDate": result.data_date.isoformat() if result.data_date else None,
            "expectedEligibleCount": len(expected),
            "semanticEligibleCount": 0,
            "missingEligibleIdentityCodes": sorted(expected),
            "invalidLifecycleIdentityCodes": list(context.invalid_lifecycle_identity_codes),
            "duplicateExpectedIdentityCodes": list(context.duplicate_expected_identity_codes),
            "outOfScopeProviderIdentityCount": 0,
            "reachable": result.reachable,
            "payloadParsed": result.payload_parsed,
            "errorCode": result.error_code,
        }
        return market, sorted(reasons)

    if result.market_code != context.market_code:
        reasons.add("MARKET_IDENTITY_MISMATCH")
    if result.provider_authority != context.provider_authority:
        reasons.add("PROVIDER_AUTHORITY_MISMATCH")
    if result.provider_version != context.provider_version:
        reasons.add("PROVIDER_VERSION_MISMATCH")
    if result.data_date != target_date:
        reasons.add("PROVIDER_DATE_MISMATCH")
    if not result.reachable:
        reasons.add("PROVIDER_UNREACHABLE")
    if not result.payload_parsed:
        reasons.add("PROVIDER_PAYLOAD_INVALID")
    if result.record_count <= 0:
        reasons.add("PROVIDER_DATA_UNAVAILABLE")

    covered = expected & set(result.record_codes)
    missing = sorted(expected - set(result.record_codes))
    if missing:
        reasons.add("MISSING_EXPECTED_IDENTITIES")
    reasons.update(f"INVALID_LIFECYCLE:{code}" for code in context.invalid_lifecycle_identity_codes)
    reasons.update(
        f"DUPLICATE_EXPECTED_IDENTITY:{code}" for code in context.duplicate_expected_identity_codes
    )
    reasons.update(f"UNEXPECTED_MARKET:{code}" for code in context.unexpected_market_codes)
    market = {
        "status": "PASS" if not reasons else "FAIL",
        "provider": result.provider_authority,
        "providerVersion": result.provider_version,
        "dataDate": result.data_date.isoformat() if result.data_date else None,
        "expectedEligibleCount": len(expected),
        "semanticEligibleCount": len(covered),
        "missingEligibleIdentityCodes": missing,
        "invalidLifecycleIdentityCodes": list(context.invalid_lifecycle_identity_codes),
        "duplicateExpectedIdentityCodes": list(context.duplicate_expected_identity_codes),
        "outOfScopeProviderIdentityCount": len(set(result.record_codes) - expected),
        "reachable": result.reachable,
        "payloadParsed": result.payload_parsed,
        "errorCode": sorted(reasons)[0] if reasons else None,
    }
    return market, sorted(reasons)


def evaluate_market_semantics(
    context: G3PreflightContext,
    market_results: Mapping[str, G3MarketFetch | G3MarketFailure],
) -> dict[str, Any]:
    """Evaluate lifecycle-aware official data without persistence or fallback."""

    markets: dict[str, dict[str, Any]] = {}
    failure_reasons = set(_failure_reasons_for_context(context))
    for market_context in context.markets:
        result = market_results.get(market_context.market_code)
        if result is None:
            result = G3MarketFailure("PROVIDER_RESULT_MISSING")
        market, reasons = _market_result(
            market_context,
            result,
            target_date=context.target_date,
        )
        markets[market_context.market_code] = market
        failure_reasons.update(f"{market_context.market_code}:{reason}" for reason in reasons)

    status = "PASS" if not failure_reasons and context.context_ready else "FAIL"
    return {
        "operation": "G3_MARKET_SEMANTICS_CHECK",
        "gate": G3_GATE,
        "runDate": context.target_date.isoformat(),
        "referenceVersion": context.reference_result.get("referenceVersion"),
        "status": status,
        "readOnly": True,
        "markets": markets,
        "fallbackUsed": context.fallback_used,
        "productionWriteSet": list(PRODUCTION_WRITE_SET),
        "failureReasons": sorted(failure_reasons),
    }


def _provider_failure(exc: Exception) -> G3MarketFailure:
    code = getattr(exc, "code", None)
    if not isinstance(code, str) or not code:
        code = "PROVIDER_REQUEST_FAILED"
    return G3MarketFailure(error_code=code)


def load_g3_preflight_context(
    session,
    *,
    target_date: date,
    reference_version: str,
) -> G3PreflightContext:
    """Load the G3 context through the existing SELECT-only reference path."""

    return build_g3_preflight_context(
        load_g2_preflight_context(
            session,
            target_date=target_date,
            reference_version=reference_version,
        )
    )


def run_market_semantics_check(
    session,
    *,
    target_date: date,
    reference_version: str,
    transport: Transport | None = None,
) -> dict[str, Any]:
    """Run the official-provider G3 check with no writes or fallback."""

    context = load_g3_preflight_context(
        session,
        target_date=target_date,
        reference_version=reference_version,
    )
    market_results: dict[str, G3MarketFetch | G3MarketFailure] = {}
    if not context.context_ready:
        for market in context.markets:
            market_results[market.market_code] = G3MarketFailure(
                "G3_REFERENCE_OR_SESSION_CONTEXT_NOT_READY"
            )
        return evaluate_market_semantics(context, market_results)

    registry = build_historical_provider_registry(
        start_date=target_date,
        end_date=target_date,
        exchange_transport=transport,
        market_batch=True,
    )
    for market in context.markets:
        registrations = registry.for_market(market.market_code)
        if len(registrations) != 1:
            market_results[market.market_code] = G3MarketFailure("PROVIDER_AUTHORITY_MISMATCH")
            continue
        registration = registrations[0]
        registration_version = getattr(registration.adapter, "adapter_version", None)
        if (
            registration.code != market.provider_authority
            or registration_version != market.provider_version
            or not getattr(registration.adapter, "market_batch", False)
        ):
            market_results[market.market_code] = G3MarketFailure(
                "PROVIDER_AUTHORITY_MISMATCH",
                provider_version=registration_version,
            )
            continue
        fetch_market_day = getattr(registration.adapter, "fetch_market_day", None)
        if not callable(fetch_market_day):
            market_results[market.market_code] = G3MarketFailure(
                "MARKET_BATCH_CAPABILITY_MISSING",
                provider_version=registration_version,
            )
            continue
        try:
            _, bars = fetch_market_day()
            data_dates = {bar.trading_date for bar in bars.values()}
            data_date = next(iter(data_dates)) if len(data_dates) == 1 else None
            error = "PROVIDER_MIXED_DATA_DATES" if len(data_dates) > 1 else None
            if error:
                market_results[market.market_code] = G3MarketFailure(
                    error,
                    provider_version=registration_version,
                    reachable=True,
                    payload_parsed=True,
                )
            else:
                market_results[market.market_code] = G3MarketFetch(
                    market_code=market.market_code,
                    provider_authority=registration.code,
                    provider_version=registration_version,
                    data_date=data_date,
                    record_codes=frozenset(bars),
                    record_count=len(bars),
                )
        except Exception as exc:
            market_results[market.market_code] = _provider_failure(exc)
    return evaluate_market_semantics(context, market_results)


def build_database_failure_result(
    *,
    target_date: date,
    reference_version: str,
    error_code: str = "G3_REFERENCE_CONTEXT_READ_FAILED",
) -> dict[str, Any]:
    """Return a secret-safe fail result when SELECT-only loading fails."""

    return {
        "operation": "G3_MARKET_SEMANTICS_CHECK",
        "gate": G3_GATE,
        "runDate": target_date.isoformat(),
        "referenceVersion": reference_version,
        "status": "FAIL",
        "readOnly": True,
        "markets": {},
        "fallbackUsed": False,
        "productionWriteSet": [],
        "failureReasons": [error_code],
    }


__all__ = [
    "G3MarketContext",
    "G3MarketFailure",
    "G3MarketFetch",
    "G3PreflightContext",
    "build_database_failure_result",
    "build_g3_preflight_context",
    "evaluate_market_semantics",
    "load_g3_preflight_context",
    "run_market_semantics_check",
]
