"""Read-only ``tw-reference-v1`` and formal identity preflight."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IdentityContextRow:
    instrument_code: str
    market_code: str | None
    market_active: bool
    instrument_type: str
    currency: str | None
    timezone: str | None
    calendar_code: str | None


@dataclass(frozen=True)
class ReferenceRegistrySummary:
    version: str
    set_count: int
    active: bool
    currencies: tuple[str, ...]
    timezones: tuple[str, ...]
    sessions: tuple[tuple[str, str], ...]
    trading_status_count: int
    adjustment_count: int
    # SQL inspection supplies the persisted count from reference_calendar_dates.
    calendar_date_count: int = 0


def evaluate_reference_preflight(
    *,
    requested_version: str,
    expected_market_codes: Iterable[str],
    active_market_codes: Iterable[str],
    identity_rows: Iterable[IdentityContextRow],
    duplicate_identities: Iterable[str],
    registry: ReferenceRegistrySummary,
    required_session_code: str,
    required_calendar_code: str,
) -> dict[str, Any]:
    """Evaluate only read data; no expected count is hard-coded.

    ``instrument_count`` is the count of active EQUITY identities attached to
    an active canonical market.  ``missing_instruments`` therefore means an
    identity lacks a valid market/context row, not that a provider failed to
    return a daily bar.  Daily provider coverage belongs to DATA-022
    reconciliation and is intentionally not conflated with this check.
    """

    expected_markets = tuple(sorted(set(expected_market_codes)))
    active_markets = set(active_market_codes)
    missing_markets = sorted(set(expected_markets) - active_markets)
    rows = tuple(identity_rows)
    missing_instruments: list[str] = []
    valid_instruments = 0
    required_contexts: set[tuple[str, str, str]] = set()
    for row in rows:
        label = f"{row.market_code or 'UNKNOWN'}:{row.instrument_code}"
        valid = (
            row.instrument_type == "EQUITY"
            and row.market_code in expected_markets
            and row.market_active
            and bool(row.currency)
            and bool(row.timezone)
            and bool(row.calendar_code)
        )
        if not valid:
            missing_instruments.append(label)
            continue
        valid_instruments += 1
        required_contexts.add((row.currency or "", row.timezone or "", row.calendar_code or ""))

    available_contexts = {
        (currency, timezone, calendar)
        for currency in registry.currencies
        for timezone in registry.timezones
        for session, calendar in registry.sessions
        if session == required_session_code
        if calendar == required_calendar_code
    }
    missing_contexts = sorted(required_contexts - available_contexts)
    registry_ready = (
        registry.version == requested_version
        and registry.set_count == 1
        and registry.active
        and bool(registry.currencies)
        and bool(registry.timezones)
        and bool(registry.sessions)
        and registry.trading_status_count > 0
        and registry.adjustment_count > 0
        and registry.calendar_date_count > 0
    )
    duplicate_values = sorted(set(duplicate_identities))
    ready = bool(expected_markets) and (
        registry_ready
        and not missing_markets
        and not missing_instruments
        and not duplicate_values
        and not missing_contexts
        and valid_instruments > 0
    )
    result = {
        "referenceVersion": requested_version,
        "referenceActive": "YES" if registry_ready else "NO",
        "expectedMarketCodes": list(expected_markets),
        "marketCount": len(active_markets & set(expected_markets)),
        "instrumentCount": valid_instruments,
        "missingMarkets": missing_markets,
        "missingInstruments": sorted(missing_instruments),
        "duplicateIdentities": duplicate_values,
        "requiredContextCount": len(required_contexts),
        "missingReferenceContexts": [
            {
                "currency": currency,
                "timezone": timezone,
                "calendarCode": calendar,
            }
            for currency, timezone, calendar in missing_contexts
        ],
        "registrySetCount": registry.set_count,
        "tradingStatusCatalogueCount": registry.trading_status_count,
        "adjustmentCatalogueCount": registry.adjustment_count,
        "calendarDateCount": registry.calendar_date_count,
        "referenceLoadStatus": "READY" if ready else "NOT_READY",
    }
    # Keep the fixed operator handoff field names alongside the API-style
    # camelCase keys so shell output can be checked without interpretation.
    result.update(
        {
            "REFERENCE_VERSION": result["referenceVersion"],
            "REFERENCE_ACTIVE": result["referenceActive"],
            "MARKET_COUNT": result["marketCount"],
            "INSTRUMENT_COUNT": result["instrumentCount"],
            "MISSING_MARKETS": result["missingMarkets"],
            "MISSING_INSTRUMENTS": result["missingInstruments"],
            "DUPLICATE_IDENTITIES": result["duplicateIdentities"],
            "REFERENCE_LOAD_STATUS": result["referenceLoadStatus"],
            "REFERENCE_CALENDAR_DATE_COUNT": result["calendarDateCount"],
        }
    )
    return result


def inspect_reference_preflight(
    session,
    *,
    requested_version: str,
    expected_market_codes: Iterable[str],
    required_session_code: str,
    required_calendar_code: str,
) -> dict[str, Any]:
    """Read the formal tables through the existing ORM; never commits."""

    from sqlalchemy import func, select

    from topicpilot_api.orm.models import (
        Instrument,
        Market,
        ReferenceAdjustment,
        ReferenceCalendarDate,
        ReferenceCurrency,
        ReferenceRegistrySet,
        ReferenceSession,
        ReferenceTimezone,
        ReferenceTradingStatus,
        SecurityIdentity,
    )

    sets = list(
        session.scalars(
            select(ReferenceRegistrySet).where(
                ReferenceRegistrySet.reference_data_version == requested_version
            )
        )
    )
    registry_id = sets[0].id if len(sets) == 1 else None
    currencies = timezones = sessions = ()
    statuses = adjustments = calendar_dates = 0
    if registry_id is not None:
        currencies = tuple(
            sorted(
                session.scalars(
                    select(ReferenceCurrency.code).where(
                        ReferenceCurrency.registry_set_id == registry_id
                    )
                ).all()
            )
        )
        timezones = tuple(
            sorted(
                session.scalars(
                    select(ReferenceTimezone.name).where(
                        ReferenceTimezone.registry_set_id == registry_id
                    )
                ).all()
            )
        )
        sessions = tuple(
            sorted(
                session.execute(
                    select(ReferenceSession.code, ReferenceSession.calendar_code).where(
                        ReferenceSession.registry_set_id == registry_id
                    )
                ).all()
            )
        )
        statuses = int(
            session.scalar(
                select(func.count())
                .select_from(ReferenceTradingStatus)
                .where(ReferenceTradingStatus.registry_set_id == registry_id)
            )
            or 0
        )
        adjustments = int(
            session.scalar(
                select(func.count())
                .select_from(ReferenceAdjustment)
                .where(ReferenceAdjustment.registry_set_id == registry_id)
            )
            or 0
        )
        calendar_dates = int(
            session.scalar(
                select(func.count())
                .select_from(ReferenceCalendarDate)
                .where(ReferenceCalendarDate.registry_set_id == registry_id)
            )
            or 0
        )
    identity_rows = [
        IdentityContextRow(
            instrument_code=row.instrument_code,
            market_code=row.market_code,
            market_active=bool(row.market_active),
            instrument_type=row.instrument_type,
            currency=row.currency,
            timezone=row.timezone,
            calendar_code=row.calendar_code,
        )
        for row in session.execute(
            select(
                Instrument.instrument_code,
                Market.code.label("market_code"),
                Market.is_active.label("market_active"),
                Instrument.instrument_type,
                Instrument.currency,
                Market.timezone,
                Market.calendar_code,
            )
            .join(Market, Market.id == Instrument.market_id)
            .where(Instrument.is_active.is_(True))
        ).all()
    ]
    expected = tuple(sorted(set(expected_market_codes)))
    active_market_codes = tuple(
        session.scalars(
            select(Market.code).where(Market.is_active.is_(True), Market.code.in_(expected))
        ).all()
    )
    duplicate_rows = session.execute(
        select(Market.code, Instrument.instrument_code)
        .join(Market, Market.id == Instrument.market_id)
        .where(Instrument.is_active.is_(True))
        .group_by(Market.code, Instrument.instrument_code)
        .having(func.count() > 1)
    ).all()
    duplicate_values = [f"{market}:{code}" for market, code in duplicate_rows]
    duplicate_security_rows = session.execute(
        select(
            SecurityIdentity.market_id,
            SecurityIdentity.identifier_namespace,
            SecurityIdentity.identifier_value,
            SecurityIdentity.valid_from,
        )
        .group_by(
            SecurityIdentity.market_id,
            SecurityIdentity.identifier_namespace,
            SecurityIdentity.identifier_value,
            SecurityIdentity.valid_from,
        )
        .having(func.count() > 1)
    ).all()
    duplicate_values.extend(
        f"security:{market_id}:{namespace}:{value}:{valid_from}"
        for market_id, namespace, value, valid_from in duplicate_security_rows
    )
    return evaluate_reference_preflight(
        requested_version=requested_version,
        expected_market_codes=expected,
        active_market_codes=active_market_codes,
        identity_rows=identity_rows,
        duplicate_identities=duplicate_values,
        registry=ReferenceRegistrySummary(
            version=requested_version,
            set_count=len(sets),
            active=len(sets) == 1 and sets[0].status == "ACTIVE",
            currencies=currencies,
            timezones=timezones,
            sessions=sessions,
            trading_status_count=statuses,
            adjustment_count=adjustments,
            calendar_date_count=calendar_dates,
        ),
        required_session_code=required_session_code,
        required_calendar_code=required_calendar_code,
    )


__all__ = [
    "IdentityContextRow",
    "ReferenceRegistrySummary",
    "evaluate_reference_preflight",
    "inspect_reference_preflight",
]
