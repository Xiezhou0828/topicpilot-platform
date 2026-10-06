"""Read-only G2 official TWSE/TPEx provider and data preflight."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date
from hashlib import sha256
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from topicpilot_api.formal_eligibility import dimension_payload, project_return_dimensions
from topicpilot_api.instrument_universe import (
    InstrumentLifecycle,
    InstrumentUniverseRow,
    LifecycleValidationError,
    build_date_effective_instrument_universe,
)
from topicpilot_api.market_data.availability import LEGITIMATE_UNAVAILABLE_CODES
from topicpilot_api.market_data.lineage import (
    EXPECTED_TPEX_ADAPTER_VERSION,
    EXPECTED_TWSE_ADAPTER_VERSION,
)
from topicpilot_api.market_data.readiness import (
    OperationalReadiness,
    classify_eod_readiness,
    classify_provider_error,
    parse_reported_session,
)
from topicpilot_api.market_data.registry import build_historical_provider_registry
from topicpilot_api.orm.models import (
    Instrument,
    Market,
    ReferenceCalendarDate,
    ReferenceInstrumentLifecycle,
    ReferenceRegistrySet,
)
from topicpilot_api.previous_close_authority import (
    ComparatorResolution,
    ComparatorStatus,
    ComparatorType,
    G2PriceEvidence,
    PreviousCloseEvidence,
    previous_session_date,
    resolve_missing_daily_comparator,
    valid_close,
)
from topicpilot_api.reference_check import inspect_reference_preflight
from topicpilot_api.trading_status_authority import TradingStatusResolution

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
    instrument_ids: Mapping[str, str] = field(default_factory=dict)

    @property
    def context_ready(self) -> bool:
        return (
            self.exchange_code == EXCHANGE_CODE_BY_MARKET[self.market_code]
            and self.timezone == TIMEZONE_BY_MARKET[self.market_code]
            and self.calendar_code == REQUIRED_CALENDAR_CODE
            and bool(self.instrument_codes)
            and len(self.instrument_codes) == len(set(self.instrument_codes))
            and all(self.instrument_ids.get(code) for code in self.instrument_codes)
            and len({self.instrument_ids.get(code) for code in self.instrument_codes})
                == len(self.instrument_codes)
        )


@dataclass(frozen=True)
class G2PreflightContext:
    reference_result: dict[str, Any]
    target_date: date
    target_date_is_session: bool
    target_date_reason: str | None
    markets: tuple[G2MarketContext, ...]
    eligibility_error: str | None = None
    universe_rows: tuple[InstrumentUniverseRow, ...] = ()
    previous_session: date | None = None

    @property
    def context_ready(self) -> bool:
        return (
            self.reference_result.get("referenceLoadStatus") == "READY"
            and self.target_date_is_session
            and self.eligibility_error is None
            and self.previous_session is not None
            and self.previous_session < self.target_date
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
    prices: Mapping[str, G2PriceEvidence] = field(default_factory=dict)
    statuses: Mapping[str, TradingStatusResolution] = field(default_factory=dict)


@dataclass(frozen=True)
class G2MarketFailure:
    error_code: str
    provider_version: str | None = None
    reachable: bool = False
    payload_parsed: bool = False
    target_date_matched: bool = False
    served_session: date | None = None


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
    readiness_state: OperationalReadiness = OperationalReadiness.BLOCKED,
    readiness_reason_code: str | None = None,
) -> dict[str, Any]:
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
        "status": (
            "PASS"
            if readiness_state is OperationalReadiness.READY
            else "WAIT"
            if readiness_state is OperationalReadiness.WAIT
            else "FAIL"
        ),
        "readinessState": readiness_state.value,
        "readinessReasonCode": readiness_reason_code,
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
            decision = classify_provider_error(
                result.error_code,
                target_session=context.target_date,
                served_session=result.served_session,
                previous_session=context.previous_session,
            )
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
                    readiness_state=decision.state,
                    readiness_reason_code=decision.reason_code,
                )
            )
            continue

        codes = set(result.record_codes)
        expected_codes = set(market.instrument_codes)
        decisions = []
        priced_codes, legitimate_codes = set(), set()
        comparator_codes = set()
        comparator_unavailable_codes = set()
        for code in sorted(expected_codes):
            price = result.prices.get(code)
            identity = market.instrument_ids.get(code)
            status = result.statuses.get(identity or "")
            close_ok = (
                code in codes and price is not None and identity is not None
                and (price.instrument_id, price.market_code, price.instrument_code)
                == (identity, market.market_code, code)
                and price.trading_date == context.target_date
                and isinstance(price.response_hash, str)
                and len(price.response_hash) == 64
                and all(c in "0123456789abcdef" for c in price.response_hash)
                and valid_close(price.close)
            )
            legitimate = (
                not close_ok and (price is None or price.close is None)
                and status is not None and status.resolved
                and status.is_legitimate_unavailable and not status.blocks_publication
                and status.status in LEGITIMATE_UNAVAILABLE_CODES
                and bool(status.authority_source)
                and not status.is_manual_override
                and status.authority_class in {
                    "OFFICIAL_EXCHANGE", "CORPORATE_ACTION", "REFERENCE_LIFECYCLE"
                }
                and bool(status.source_reference) and status.effective_from is not None
                and status.effective_from <= context.target_date
                and (status.effective_to is None or status.effective_to >= context.target_date)
                and identity is not None
            )
            reason = None
            previous = price.previous() if price is not None else None
            comparator = None
            if legitimate:
                legitimate_codes.add(code)
                comparator = ComparatorResolution(
                    ComparatorStatus.ACCOUNTED_UNAVAILABLE,
                    None,
                    status.reason_code or status.status,
                    status.authority_source,
                    status.source_reference,
                )
            elif not close_ok:
                reason = "CURRENT_OFFICIAL_CLOSE_INVALID"
            else:
                priced_codes.add(code)
                if context.previous_session is None:
                    reason = "PREVIOUS_FORMAL_SESSION_NOT_RESOLVED"
                    comparator = ComparatorResolution(ComparatorStatus.ERROR, None, reason)
                elif previous is None:
                    comparator = resolve_missing_daily_comparator(
                        symbol=code,
                        market=market.market_code,
                        target=context.target_date,
                        prior=context.previous_session,
                    )
                    if comparator.status == ComparatorStatus.READY:
                        comparator_codes.add(code)
                    elif comparator.status == ComparatorStatus.ACCOUNTED_UNAVAILABLE:
                        comparator_unavailable_codes.add(code)
                    else:
                        reason = comparator.reason_code or "MISSING_PREVIOUS_FORMAL_CLOSE"
                else:
                    reason = previous.rejection_reason(
                        instrument_id=identity, market=market.market_code, code=code,
                        target=context.target_date, prior=context.previous_session,
                    )
                    if (
                        reason is None and price.provider_previous is not None
                        and previous.lineage != price.response_hash
                    ):
                        reason = "PREVIOUS_CLOSE_PAYLOAD_LINEAGE_MISMATCH"
                    comparator = (
                        ComparatorResolution(
                            ComparatorStatus.READY,
                            ComparatorType.PREVIOUS_FORMAL_CLOSE,
                            authority_source=previous.source,
                            source_reference=previous.lineage,
                            previous_traded_close=previous.value,
                            previous_traded_close_date=previous.as_of_date,
                            previous_traded_close_authority=previous.authority,
                            previous_traded_close_lineage=previous.lineage,
                            comparison_reference=previous.value,
                            comparison_reference_date=previous.as_of_date,
                            comparison_reference_authority=previous.authority,
                            comparison_reference_lineage=previous.lineage,
                        )
                        if reason is None
                        else ComparatorResolution(
                            ComparatorStatus.ERROR,
                            None,
                            reason,
                            previous.source,
                            previous.lineage,
                        )
                    )
                if reason is None and comparator is not None and comparator.ready:
                    comparator_codes.add(code)
            if comparator is None:
                comparator_status = (
                    ComparatorStatus.READY
                    if code in comparator_codes
                    else ComparatorStatus.ERROR
                )
                comparator_reason = reason
                comparator_source = previous.source if previous else None
                comparator_reference = previous.lineage if previous else None
                comparator_type = None
            else:
                comparator_status = comparator.status
                comparator_reason = comparator.reason_code or reason
                comparator_source = comparator.authority_source
                comparator_reference = comparator.source_reference
                comparator_type = (
                    comparator.comparator_type.value
                    if comparator.comparator_type is not None
                    else None
                )
            if comparator is None:
                comparator = ComparatorResolution(
                    ComparatorStatus.ERROR,
                    None,
                    comparator_reason,
                    comparator_source,
                    comparator_reference,
                )
            dimensions = project_return_dimensions(comparator, current_price_ready=close_ok)
            decisions.append({
                "instrumentCode": code, "instrumentId": identity,
                "closeValid": bool(close_ok), "legitimateUnavailable": bool(legitimate),
                "status": status.status if status is not None else None,
                "statusSource": status.authority_source if status is not None else None,
                "statusLineage": status.source_reference if status is not None else None,
                "previousClose": previous.price_free_metadata() if previous else None,
                "previousCloseValid": code in comparator_codes,
                "comparatorStatus": comparator_status.value,
                "comparatorType": comparator_type,
                "comparatorReasonCode": comparator_reason,
                "comparatorAuthority": comparator.to_dict(),
                "dimensionEligibility": dimension_payload(dimensions),
                "errorCode": reason,
                "responseHash": price.response_hash if price else None,
                "syntheticOrFillUsed": False,
            })
        accounted_codes = priced_codes | legitimate_codes
        covered_count = len(accounted_codes)
        missing_codes = tuple(sorted(expected_codes - accounted_codes))
        extra_codes = tuple(sorted(codes - expected_codes))
        target_date_matched = result.target_date == context.target_date
        # The official market-level endpoint may include securities outside
        # the date-effective formal EQUITY universe (for example ETFs,
        # warrants, or other exchange-listed products).  G2 coverage is an
        # expected-universe contract: every expected identity must be present.
        # Preserve out-of-scope provider codes in the evidence, but do not let
        # them turn complete expected-EQUITY coverage into a failure.
        coverage_complete = (
            bool(expected_codes)
            and not missing_codes
            and (comparator_codes | comparator_unavailable_codes) == priced_codes
        )
        authority_ok = (
            result.provider_authority == market.provider_authority
            and result.market_code == market.market_code
        )
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
        elif (comparator_codes | comparator_unavailable_codes) != priced_codes:
            error_code = "PREVIOUS_CLOSE_AUTHORITY_NOT_READY"
        readiness = (
            classify_eod_readiness(
                source_official=authority_ok and version_ok,
                retrieval_succeeded=result.reachable,
                target_session=context.target_date,
                served_session=result.target_date,
                payload_valid=result.payload_parsed,
                required_rows_present=result.record_count > 0,
                required_ohlcv_parseable=bool(priced_codes | legitimate_codes),
                minimum_coverage=coverage_complete,
                previous_session=context.previous_session,
            )
            if error_code is None
            else classify_provider_error(
                error_code,
                target_session=context.target_date,
                served_session=result.target_date,
                previous_session=context.previous_session,
            )
        )
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
                readiness_state=readiness.state,
                readiness_reason_code=readiness.reason_code,
            )
        )
        evidence[-1].update({
            "priceCandidateCount": len(priced_codes),
            "legitimateUnavailableCount": len(legitimate_codes),
            "accountedTargetCount": covered_count,
            "previousCloseCoveredCount": len(comparator_codes),
            "previousCloseRequiredCount": len(priced_codes),
            "comparatorAccountedUnavailableCount": len(comparator_unavailable_codes),
            "previousSessionDate": (
                context.previous_session.isoformat() if context.previous_session else None
            ),
            "instrumentDecisions": decisions,
        })

    context_ok = context.context_ready
    states = [item["readinessState"] for item in evidence]
    readiness_state = (
        OperationalReadiness.BLOCKED
        if not context_ok or OperationalReadiness.BLOCKED.value in states
        else OperationalReadiness.WAIT
        if OperationalReadiness.WAIT.value in states
        else OperationalReadiness.READY
    )
    status = (
        "PASS"
        if readiness_state is OperationalReadiness.READY
        else "WAIT"
        if readiness_state is OperationalReadiness.WAIT
        else "FAIL"
    )
    return {
        "gate": G2_GATE,
        "status": status,
        "readinessState": readiness_state.value,
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
    closed_dates = set()
    calendar_kind = None
    if registry_id is not None:
        calendar_kind = session.scalar(
            select(ReferenceCalendarDate.date_kind).where(
                ReferenceCalendarDate.registry_set_id == registry_id,
                ReferenceCalendarDate.calendar_code == REQUIRED_CALENDAR_CODE,
                ReferenceCalendarDate.calendar_date == target_date,
            )
        )
        closed_dates = set(session.scalars(
            select(ReferenceCalendarDate.calendar_date).where(
                ReferenceCalendarDate.registry_set_id == registry_id,
                ReferenceCalendarDate.calendar_code == REQUIRED_CALENDAR_CODE,
            )
        ).all())

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
            instrument_ids={
                str(row.instrument_code): str(row.id)
                for row in instrument_rows if row.code == market_code
            },
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
        universe_rows=tuple(universe_rows),
        previous_session=previous_session_date(target_date, closed_dates) if registry_id else None,
    )


def _provider_failure(
    exc: Exception,
    evidence: Mapping[str, Any] | None = None,
) -> G2MarketFailure:
    code = getattr(exc, "code", None)
    if not isinstance(code, str) or not code:
        code = "PROVIDER_REQUEST_FAILED"
    parsed_codes = {
        "EXCHANGE_NO_DATA",
        "EXCHANGE_NOT_READY",
        "EXCHANGE_EMPTY_PAYLOAD",
        "INVALID_PAYLOAD",
        "DUPLICATE_INSTRUMENT_ROW",
        "INVALID_OHLC",
        "INVALID_VOLUME",
        "INVALID_NUMBER",
        "PROVIDER_DATE_MISMATCH",
    }
    raw_evidence = evidence if evidence is not None else getattr(exc, "evidence", None)
    receipt = raw_evidence or {}
    decoded = raw_evidence is None or receipt.get("stage") == "DATASET_PARSE"
    reported_dates = receipt.get("rawResponseDates") or ()
    if isinstance(reported_dates, str):
        reported_dates = (reported_dates,)
    served_session = None
    if len(reported_dates) == 1:
        served_session = parse_reported_session(reported_dates[0])
    return G2MarketFailure(
        error_code=code,
        reachable=code in parsed_codes or bool(receipt and receipt.get("payloadHash")),
        payload_parsed=decoded and code in parsed_codes,
        target_date_matched=decoded and code in parsed_codes and code != "PROVIDER_DATE_MISMATCH",
        served_session=served_session,
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

    from topicpilot_api.daily_market import read_daily_market_rows
    from topicpilot_api.market_data.exchange import _read_url
    from topicpilot_api.trading_status_authority import read_effective_trading_status_authority

    ids = [UUID(market.instrument_ids[code])
           for market in context.markets for code in market.instrument_codes]
    formal_rows = {(row["market"], row["symbol"]): row for row in read_daily_market_rows(
        session, target_date, expected_instrument_ids=ids,
    )}
    status_rows = {(row["market"], row["symbol"]): row
                   for row in read_effective_trading_status_authority(
        session, target_date, expected_instrument_ids=ids,
    )}
    response_hashes: dict[str, str] = {}

    def observed_transport(url: str, timeout: float) -> bytes:
        raw = (transport or _read_url)(url, timeout)
        response_hashes[url] = sha256(raw).hexdigest()
        return raw

    registry = build_historical_provider_registry(
        start_date=target_date,
        end_date=target_date,
        exchange_transport=observed_transport,
        market_batch=True,
    )
    market_results: dict[str, G2MarketFetch | G2MarketFailure] = {}
    response_evidence: dict[str, dict[str, Any]] = {}
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
            response_hashes.clear()
            _, bars = fetch_market_day()
            payload_hash = next(iter(response_hashes.values())) if len(response_hashes) == 1 else ""
            prices, statuses = {}, {}
            for code in market.instrument_codes:
                identity = market.instrument_ids[code]
                row = formal_rows.get((market.market_code, code), {})
                prior = None
                if row.get("previous_close_lineage") is not None:
                    prior = PreviousCloseEvidence(
                        str(row.get("previous_close_instrument_id")), market.market_code, code,
                        row["previous_close_date"], row.get("previous_close"),
                        row["previous_close_source"], "FORMAL_CANONICAL_CLOSE",
                        str(row["previous_close_lineage"]),
                        quality_state=row["previous_close_quality"],
                    )
                bar = bars.get(code)
                if bar is not None:
                    provider_previous = None
                    if bar.previous_close is not None and context.previous_session is not None:
                        provider_previous = PreviousCloseEvidence(
                            identity, market.market_code, code, context.previous_session,
                            bar.previous_close, registration.code,
                            "PROVIDER_EXPLICIT_PREVIOUS_CLOSE", payload_hash, target_date,
                        )
                    prices[code] = G2PriceEvidence(
                        identity, market.market_code, code, bar.trading_date,
                        bar.close, payload_hash, provider_previous, prior,
                    )
                status_row = status_rows.get((market.market_code, code))
                if status_row is not None and str(status_row["instrumentId"]) == identity:
                    statuses[identity] = TradingStatusResolution(
                        status_row["resolvedStatus"], status_row["authoritySource"],
                        status_row["reasonCode"], status_row["effectiveFrom"],
                        status_row["effectiveTo"], status_row["sourceReference"],
                        status_row["resolutionState"], status_row["blocksPublication"],
                        status_row["isLegitimateUnavailable"], status_row["authorityClass"],
                    )
            market_results[market.market_code] = G2MarketFetch(
                market_code=market.market_code,
                provider_authority=registration.code,
                provider_version=registration_version,
                target_date=target_date,
                record_codes=frozenset(bars),
                record_count=len(bars),
                prices=prices,
                statuses=statuses,
            )
        except Exception as exc:
            receipt = dict(getattr(registration.adapter, "response_evidence", {}))
            receipt.update(
                errorCode=getattr(exc, "code", "PROVIDER_REQUEST_FAILED"),
                exceptionClass=type(exc).__name__,
            )
            if not receipt.get("classification"):
                code = receipt["errorCode"]
                receipt["classification"] = (
                    "PROVIDER_DATE_MISMATCH"
                    if code == "PROVIDER_DATE_MISMATCH"
                    else "PROVIDER_ENDPOINT_EMPTY"
                    if code == "EXCHANGE_EMPTY_PAYLOAD"
                    else "PROVIDER_NOT_READY"
                    if code in {"EXCHANGE_NOT_READY", "EXCHANGE_NO_DATA"}
                    else "PROVIDER_PARSER_REJECTION"
                )
            market_results[market.market_code] = _provider_failure(exc, receipt)
            response_evidence[market.market_code] = receipt
        else:
            response_evidence[market.market_code] = dict(registration.adapter.response_evidence)
    result = evaluate_provider_preflight(context, market_results)
    for market in result["markets"]:
        market["responseEvidence"] = response_evidence.get(market["marketCode"], {})
    return result


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
        "readinessState": OperationalReadiness.BLOCKED.value,
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
                "readinessState": OperationalReadiness.BLOCKED.value,
                "readinessReasonCode": error_code,
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
