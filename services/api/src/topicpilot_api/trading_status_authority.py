"""Formal daily trading-status authority and bounded resolution.

This module deliberately keeps authority resolution independent from the
frontend and from price-gap heuristics.  The database already stores accepted
canonical trading-status observations and date-effective lifecycle evidence;
this module gives those inputs one deterministic, typed interpretation.

There is no standalone TWSE/TPEx status endpoint contract in this repository.
The supported source boundary is therefore the explicit status evidence
already carried by the proven official daily provider contract.  Anything
ambiguous or unsupported remains fail-closed.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .market_data.availability import (
    LEGITIMATE_UNAVAILABLE_CODES,
    MarketAvailability,
)
from .orm import ReferenceInstrumentLifecycle, ReferenceRegistrySet

OFFICIAL_DAILY_SOURCES = frozenset({"TWSE_OFFICIAL_DAILY", "TPEX_OFFICIAL_DAILY"})
CANONICAL_STATUS_SOURCES = OFFICIAL_DAILY_SOURCES | {"CANONICAL_STATUS_AUTHORITY"}
LIFECYCLE_STATUS_CODES = frozenset({"SUSPENDED", "DELISTED", "TERMINATED"})
KNOWN_STATUS_CODES = frozenset(item.value for item in MarketAvailability)


class TradingStatusAuthorityError(ValueError):
    """Raised when authority evidence cannot be safely normalized."""


class AuthorityClass(StrEnum):
    OFFICIAL_EXCHANGE = "OFFICIAL_EXCHANGE"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    REFERENCE_LIFECYCLE = "REFERENCE_LIFECYCLE"
    MANUAL_GOVERNED = "MANUAL_GOVERNED"
    PRICE_SESSION = "PRICE_SESSION"
    NONE = "NONE"


_AUTHORITY_PRECEDENCE = {
    AuthorityClass.OFFICIAL_EXCHANGE.value: 3,
    AuthorityClass.CORPORATE_ACTION.value: 2,
    AuthorityClass.REFERENCE_LIFECYCLE.value: 1,
    AuthorityClass.MANUAL_GOVERNED.value: 0,
}


class ResolutionState(StrEnum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"


@dataclass(frozen=True)
class TradingStatusAuthorityRecord:
    """One date-effective status event or governed override."""

    status_code: str
    effective_from: date
    effective_to: date | None
    source: str
    source_reference: str
    reason_code: str | None = None
    observed_at: datetime | None = None
    published_at: datetime | None = None
    authority_class: str = AuthorityClass.OFFICIAL_EXCHANGE.value
    is_manual_override: bool = False
    supersedes: str | None = None
    superseded_by: str | None = None
    expires_at: date | None = None

    def __post_init__(self) -> None:
        status = self.status_code.upper()
        if status not in KNOWN_STATUS_CODES:
            raise TradingStatusAuthorityError(f"UNKNOWN_SOURCE_STATUS:{self.status_code}")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise TradingStatusAuthorityError("INVALID_EFFECTIVE_RANGE")
        if not self.source.strip() or not self.source_reference.strip():
            raise TradingStatusAuthorityError("MISSING_AUTHORITY_PROVENANCE")

    @property
    def normalized_status(self) -> str:
        return self.status_code.upper()

    def is_effective_on(self, trading_date: date) -> bool:
        if trading_date < self.effective_from:
            return False
        if self.effective_to is not None and trading_date > self.effective_to:
            return False
        return self.expires_at is None or trading_date <= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "statusCode": self.normalized_status,
            "effectiveFrom": self.effective_from,
            "effectiveTo": self.effective_to,
            "source": self.source,
            "sourceReference": self.source_reference,
            "reasonCode": self.reason_code,
            "observedAt": self.observed_at,
            "publishedAt": self.published_at,
            "authorityClass": str(self.authority_class),
            "isManualOverride": self.is_manual_override,
            "supersedes": self.supersedes,
            "supersededBy": self.superseded_by,
            "expiresAt": self.expires_at,
        }


@dataclass(frozen=True)
class ManualTradingStatusOverride(TradingStatusAuthorityRecord):
    """Validated, non-persisting boundary for future governed manual writes.

    The current repository has no secure authority-write API or dedicated
    manual audit table.  This object can be supplied to the resolver and is
    intentionally not a mutation endpoint or an implicit patch table.
    """

    operator_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_class", AuthorityClass.MANUAL_GOVERNED.value)
        object.__setattr__(self, "is_manual_override", True)
        super().__post_init__()
        if not self.operator_id.strip():
            raise TradingStatusAuthorityError("MISSING_OVERRIDE_OPERATOR")
        if not (self.reason_code or "").strip():
            raise TradingStatusAuthorityError("MISSING_OVERRIDE_REASON")


@dataclass(frozen=True)
class TradingStatusResolution:
    """The one effective daily status consumed by POST_CLOSE."""

    status: str
    authority_source: str | None
    reason_code: str
    effective_from: date | None
    effective_to: date | None
    source_reference: str | None
    resolution_state: str
    blocks_publication: bool
    is_legitimate_unavailable: bool
    authority_class: str = AuthorityClass.NONE.value
    is_manual_override: bool = False
    preserved_event_status: str | None = None
    preserved_event_source: str | None = None

    @property
    def resolved(self) -> bool:
        return self.resolution_state == ResolutionState.RESOLVED.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "authoritySource": self.authority_source,
            "reasonCode": self.reason_code,
            "effectiveFrom": self.effective_from,
            "effectiveTo": self.effective_to,
            "sourceReference": self.source_reference,
            "resolutionState": self.resolution_state,
            "blocksPublication": self.blocks_publication,
            "isLegitimateUnavailable": self.is_legitimate_unavailable,
            "authorityClass": self.authority_class,
            "isManualOverride": self.is_manual_override,
            "preservedEventStatus": self.preserved_event_status,
            "preservedEventSource": self.preserved_event_source,
        }


@dataclass
class StatusResolutionMetrics:
    """Structured status-resolution counters persisted in live metadata."""

    lookup_count: int = 0
    hit_count: int = 0
    miss_count: int = 0
    provider_failure_count: int = 0
    manual_override_count: int = 0
    retry_count: int = 0
    unresolved_unavailable_count: int = 0
    legitimate_unavailable_count: int = 0
    total_wait_seconds: float = 0.0

    def to_dict(self) -> dict[str, int | float]:
        return {
            "STATUS_AUTHORITY_LOOKUP_COUNT": self.lookup_count,
            "STATUS_AUTHORITY_HIT_COUNT": self.hit_count,
            "STATUS_AUTHORITY_MISS_COUNT": self.miss_count,
            "STATUS_AUTHORITY_PROVIDER_FAILURE_COUNT": self.provider_failure_count,
            "STATUS_AUTHORITY_MANUAL_OVERRIDE_COUNT": self.manual_override_count,
            "STATUS_RESOLUTION_RETRY_COUNT": self.retry_count,
            "UNRESOLVED_UNAVAILABLE_COUNT": self.unresolved_unavailable_count,
            "LEGITIMATE_UNAVAILABLE_COUNT": self.legitimate_unavailable_count,
            "STATUS_RESOLUTION_TOTAL_WAIT_SECONDS": round(self.total_wait_seconds, 3),
        }


@dataclass(frozen=True)
class BoundedStatusResolution:
    resolutions: tuple[TradingStatusResolution, ...]
    metrics: StatusResolutionMetrics


def normalize_source_status(value: object, *, source: str) -> str:
    """Normalize only explicit, contract-backed status tokens.

    The mapping is intentionally exact.  Free-text descriptions and unknown
    source tokens never become a guessed suspension or no-trade state.
    """

    if not isinstance(value, str):
        return MarketAvailability.UNKNOWN.value
    raw = value.strip().upper()
    explicit = {
        "NORMAL": MarketAvailability.AVAILABLE.value,
        "TRADING": MarketAvailability.AVAILABLE.value,
        "AVAILABLE": MarketAvailability.AVAILABLE.value,
        "NO_TRADE": MarketAvailability.NO_TRADE.value,
        "SUSPENDED": MarketAvailability.SUSPENDED.value,
        "HALTED": MarketAvailability.HALTED.value,
        "DELISTED": MarketAvailability.DELISTED.value,
        "TERMINATED": MarketAvailability.TERMINATED.value,
        "EXCHANGE_CONFIRMED_NO_DATA": MarketAvailability.EXCHANGE_CONFIRMED_NO_DATA.value,
        "MISSING_MARKET_DATA": MarketAvailability.MISSING_MARKET_DATA.value,
        "PROVIDER_ERROR": MarketAvailability.PROVIDER_ERROR.value,
        "DATE_MISMATCH": MarketAvailability.DATE_MISMATCH.value,
        "UNKNOWN": MarketAvailability.UNKNOWN.value,
    }
    if source not in CANONICAL_STATUS_SOURCES:
        return MarketAvailability.UNKNOWN.value
    return explicit.get(raw, MarketAvailability.UNKNOWN.value)


def authority_from_official_daily_result(
    result: Any,
    *,
    trading_date: date,
    source_reference: str | None = None,
) -> TradingStatusAuthorityRecord | None:
    """Convert an explicit status carried by a proven official daily result.

    An empty price row without an explicit status is not promoted here.  The
    existing ingestion policy will consequently leave it unresolved.
    """

    source = str(getattr(result, "source_code", ""))
    if source not in OFFICIAL_DAILY_SOURCES:
        raise TradingStatusAuthorityError(f"UNSUPPORTED_STATUS_SOURCE:{source or 'EMPTY'}")
    if not bool(getattr(result, "status_explicit", False)):
        return None
    raw_status = getattr(result, "instrument_status", None)
    normalized = normalize_source_status(raw_status, source=source)
    reference = source_reference or (
        f"{source}:{getattr(result, 'instrument_code', 'UNKNOWN')}:{trading_date.isoformat()}"
    )
    try:
        return TradingStatusAuthorityRecord(
            status_code=normalized,
            effective_from=trading_date,
            effective_to=trading_date,
            source=source,
            source_reference=reference,
            reason_code=getattr(result, "status_reason", None) or normalized,
            observed_at=getattr(result, "retrieved_at", None),
            authority_class=AuthorityClass.OFFICIAL_EXCHANGE.value,
        )
    except TradingStatusAuthorityError:
        # Unknown values are explicit evidence of an unresolved source, not a
        # reason to fail open.  Preserve provenance while returning UNKNOWN.
        return TradingStatusAuthorityRecord(
            status_code=MarketAvailability.UNKNOWN.value,
            effective_from=trading_date,
            effective_to=trading_date,
            source=source,
            source_reference=reference,
            reason_code="UNKNOWN_SOURCE_STATUS",
            observed_at=getattr(result, "retrieved_at", None),
            authority_class=AuthorityClass.OFFICIAL_EXCHANGE.value,
        )


def _active_records(
    records: Iterable[TradingStatusAuthorityRecord], trading_date: date
) -> tuple[TradingStatusAuthorityRecord, ...]:
    candidates = [
        item
        for item in records
        if item.is_effective_on(trading_date) and item.superseded_by is None
    ]
    # Same source/reference duplicate delivery is idempotent.  Conflicting
    # effective records remain visible to the resolver as ambiguity.
    unique: dict[tuple[str, str, date, date | None], TradingStatusAuthorityRecord] = {}
    for item in candidates:
        unique.setdefault(
            (item.source, item.source_reference, item.effective_from, item.effective_to),
            item,
        )
    return tuple(unique.values())


def _choose_official(
    records: Sequence[TradingStatusAuthorityRecord],
) -> TradingStatusAuthorityRecord | None:
    official = [
        item
        for item in records
        if item.authority_class
        in {
            AuthorityClass.OFFICIAL_EXCHANGE.value,
            AuthorityClass.CORPORATE_ACTION.value,
            AuthorityClass.REFERENCE_LIFECYCLE.value,
            AuthorityClass.MANUAL_GOVERNED.value,
        }
    ]
    if not official:
        return None
    highest = max(_AUTHORITY_PRECEDENCE.get(item.authority_class, -1) for item in official)
    official = [
        item
        for item in official
        if _AUTHORITY_PRECEDENCE.get(item.authority_class, -1) == highest
    ]
    statuses = {item.normalized_status for item in official}
    if len(statuses) > 1:
        return None

    def _timestamp(value: datetime | None) -> str:
        return value.isoformat() if value is not None else ""

    return sorted(
        official,
        key=lambda item: (
            item.authority_class != AuthorityClass.OFFICIAL_EXCHANGE.value,
            _timestamp(item.observed_at),
            _timestamp(item.published_at),
            item.source_reference,
        ),
        reverse=True,
    )[0]


def resolve_effective_trading_status(
    instrument: object,
    trading_date: date,
    *,
    same_session_close: Decimal | int | float | None = None,
    official_authority: Iterable[TradingStatusAuthorityRecord] = (),
    manual_overrides: Iterable[ManualTradingStatusOverride] = (),
    provider_failure: bool = False,
    price_source: str = "CANONICAL_DAILY_PRICE",
) -> TradingStatusResolution:
    """Resolve one effective status without deriving authority from absence.

    ``instrument`` is accepted as an identity object for the public contract;
    resolution is intentionally independent of its ORM implementation.
    """

    del instrument
    official = _active_records(official_authority, trading_date)
    manual = _active_records(manual_overrides, trading_date)
    selected_official = _choose_official(official)
    selected_manual = _choose_official(manual)

    if same_session_close is not None:
        preserved = selected_official
        return TradingStatusResolution(
            status=MarketAvailability.AVAILABLE.value,
            authority_source=price_source,
            reason_code="VALID_SAME_SESSION_CLOSE",
            effective_from=trading_date,
            effective_to=trading_date,
            source_reference=None,
            resolution_state=ResolutionState.RESOLVED.value,
            blocks_publication=False,
            is_legitimate_unavailable=False,
            authority_class=AuthorityClass.PRICE_SESSION.value,
            preserved_event_status=preserved.normalized_status if preserved else None,
            preserved_event_source=preserved.source if preserved else None,
        )

    selected_official_records = [
        item
        for item in official
        if item.authority_class
        in {
            AuthorityClass.OFFICIAL_EXCHANGE.value,
            AuthorityClass.CORPORATE_ACTION.value,
            AuthorityClass.REFERENCE_LIFECYCLE.value,
            AuthorityClass.MANUAL_GOVERNED.value,
        }
    ]
    highest_precedence = max(
        (_AUTHORITY_PRECEDENCE.get(item.authority_class, -1) for item in selected_official_records),
        default=-1,
    )
    selected_precedence_records = [
        item
        for item in selected_official_records
        if _AUTHORITY_PRECEDENCE.get(item.authority_class, -1) == highest_precedence
    ]
    if len({item.normalized_status for item in selected_precedence_records}) > 1:
        return TradingStatusResolution(
            status=MarketAvailability.UNKNOWN.value,
            authority_source=None,
            reason_code="AMBIGUOUS_AUTHORITY",
            effective_from=None,
            effective_to=None,
            source_reference=None,
            resolution_state=ResolutionState.UNRESOLVED.value,
            blocks_publication=True,
            is_legitimate_unavailable=False,
        )

    if selected_official is not None:
        status = selected_official.normalized_status
        if status in LEGITIMATE_UNAVAILABLE_CODES:
            return TradingStatusResolution(
                status=status,
                authority_source=selected_official.source,
                reason_code=selected_official.reason_code or status,
                effective_from=selected_official.effective_from,
                effective_to=selected_official.effective_to,
                source_reference=selected_official.source_reference,
                resolution_state=ResolutionState.RESOLVED.value,
                blocks_publication=False,
                is_legitimate_unavailable=True,
                authority_class=selected_official.authority_class,
                is_manual_override=selected_official.is_manual_override,
            )
        if status == MarketAvailability.AVAILABLE.value:
            return TradingStatusResolution(
                status=MarketAvailability.MISSING_MARKET_DATA.value,
                authority_source=selected_official.source,
                reason_code="OFFICIAL_STATUS_EXPECTS_PRICE",
                effective_from=selected_official.effective_from,
                effective_to=selected_official.effective_to,
                source_reference=selected_official.source_reference,
                resolution_state=ResolutionState.UNRESOLVED.value,
                blocks_publication=True,
                is_legitimate_unavailable=False,
                authority_class=selected_official.authority_class,
            )
        return TradingStatusResolution(
            status=MarketAvailability.UNKNOWN.value,
            authority_source=selected_official.source,
            reason_code="AMBIGUOUS_OR_UNSUPPORTED_AUTHORITY",
            effective_from=selected_official.effective_from,
            effective_to=selected_official.effective_to,
            source_reference=selected_official.source_reference,
            resolution_state=ResolutionState.UNRESOLVED.value,
            blocks_publication=True,
            is_legitimate_unavailable=False,
            authority_class=selected_official.authority_class,
        )

    if selected_manual is not None:
        status = selected_manual.normalized_status
        if status in LEGITIMATE_UNAVAILABLE_CODES:
            return TradingStatusResolution(
                status=status,
                authority_source=selected_manual.source,
                reason_code=selected_manual.reason_code or status,
                effective_from=selected_manual.effective_from,
                effective_to=selected_manual.effective_to,
                source_reference=selected_manual.source_reference,
                resolution_state=ResolutionState.RESOLVED.value,
                blocks_publication=False,
                is_legitimate_unavailable=True,
                authority_class=AuthorityClass.MANUAL_GOVERNED.value,
                is_manual_override=True,
            )

    if provider_failure:
        return TradingStatusResolution(
            status=MarketAvailability.PROVIDER_ERROR.value,
            authority_source=None,
            reason_code=MarketAvailability.PROVIDER_ERROR.value,
            effective_from=None,
            effective_to=None,
            source_reference=None,
            resolution_state=ResolutionState.PROVIDER_FAILURE.value,
            blocks_publication=True,
            is_legitimate_unavailable=False,
        )

    return TradingStatusResolution(
        status=MarketAvailability.MISSING_MARKET_DATA.value,
        authority_source=None,
        reason_code=MarketAvailability.MISSING_MARKET_DATA.value,
        effective_from=None,
        effective_to=None,
        source_reference=None,
        resolution_state=ResolutionState.UNRESOLVED.value,
        blocks_publication=True,
        is_legitimate_unavailable=False,
    )


def resolve_missing_statuses_with_budget(
    lookup: Callable[[], Sequence[TradingStatusResolution]],
    *,
    candidate_count: int = 0,
    max_attempts: int,
    max_total_wait_seconds: float,
    backoff_seconds: float,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> BoundedStatusResolution:
    """Retry status authority only for unresolved price gaps, with a hard cap."""

    if max_attempts < 1 or max_total_wait_seconds < 0 or backoff_seconds < 0:
        raise ValueError("invalid status-resolution budget")
    metrics = StatusResolutionMetrics()
    started = clock()
    resolutions: tuple[TradingStatusResolution, ...] = ()
    for attempt in range(1, max_attempts + 1):
        metrics.lookup_count += 1
        try:
            resolutions = tuple(lookup())
        except TradingStatusAuthorityError:
            metrics.provider_failure_count += 1
            resolutions = tuple(
                TradingStatusResolution(
                    status=MarketAvailability.PROVIDER_ERROR.value,
                    authority_source=None,
                    reason_code=MarketAvailability.PROVIDER_ERROR.value,
                    effective_from=None,
                    effective_to=None,
                    source_reference=None,
                    resolution_state=ResolutionState.PROVIDER_FAILURE.value,
                    blocks_publication=True,
                    is_legitimate_unavailable=False,
                )
                for _ in range(candidate_count)
            )
        if len(resolutions) < candidate_count:
            resolutions = resolutions + tuple(
                TradingStatusResolution(
                    status=MarketAvailability.MISSING_MARKET_DATA.value,
                    authority_source=None,
                    reason_code=MarketAvailability.MISSING_MARKET_DATA.value,
                    effective_from=None,
                    effective_to=None,
                    source_reference=None,
                    resolution_state=ResolutionState.UNRESOLVED.value,
                    blocks_publication=True,
                    is_legitimate_unavailable=False,
                )
                for _ in range(candidate_count - len(resolutions))
            )
        metrics.hit_count += sum(
            item.authority_source is not None
            and item.resolution_state == ResolutionState.RESOLVED.value
            for item in resolutions
        )
        metrics.manual_override_count += sum(item.is_manual_override for item in resolutions)
        unresolved = tuple(
            item for item in resolutions if item.resolution_state != ResolutionState.RESOLVED.value
        )
        if not unresolved:
            break
        metrics.miss_count += len(unresolved)
        if attempt >= max_attempts:
            break
        elapsed = max(0.0, clock() - started)
        remaining = max_total_wait_seconds - elapsed
        if remaining <= 0:
            break
        delay = min(backoff_seconds * (2 ** (attempt - 1)), remaining)
        if delay <= 0:
            break
        metrics.retry_count += 1
        metrics.total_wait_seconds += delay
        sleep(delay)

    metrics.legitimate_unavailable_count = sum(
        item.is_legitimate_unavailable for item in resolutions
    )
    metrics.unresolved_unavailable_count = sum(
        item.resolution_state != ResolutionState.RESOLVED.value for item in resolutions
    )
    return BoundedStatusResolution(resolutions=resolutions, metrics=metrics)


def _lifecycle_records(
    session: Session, *, instrument_ids: Sequence[Any], trading_date: date
) -> dict[Any, tuple[TradingStatusAuthorityRecord, ...]]:
    if not instrument_ids:
        return {}
    registry_ids = session.scalars(
        select(ReferenceRegistrySet.id).where(ReferenceRegistrySet.status == "ACTIVE")
    ).all()
    if not registry_ids:
        return {}
    rows = session.execute(
        select(ReferenceInstrumentLifecycle).where(
            ReferenceInstrumentLifecycle.registry_set_id.in_(registry_ids),
            ReferenceInstrumentLifecycle.instrument_id.in_(tuple(instrument_ids)),
            ReferenceInstrumentLifecycle.effective_from <= trading_date,
            (ReferenceInstrumentLifecycle.effective_to.is_(None))
            | (ReferenceInstrumentLifecycle.effective_to >= trading_date),
        )
    ).scalars()
    result: dict[Any, list[TradingStatusAuthorityRecord]] = {}
    for row in rows:
        if row.status_code not in LIFECYCLE_STATUS_CODES:
            continue
        result.setdefault(row.instrument_id, []).append(
            TradingStatusAuthorityRecord(
                status_code=row.status_code,
                effective_from=row.effective_from,
                effective_to=row.effective_to,
                source="REFERENCE_INSTRUMENT_LIFECYCLE",
                source_reference=row.evidence_id,
                reason_code=row.reason or row.status_code,
                authority_class=AuthorityClass.REFERENCE_LIFECYCLE.value,
            )
        )
    return {key: tuple(value) for key, value in result.items()}


def read_effective_trading_status_authority(
    session: Session,
    trading_date: date,
    *,
    expected_instrument_ids: Sequence[Any] | None = None,
    provider_failure_instrument_ids: Iterable[Any] = (),
    market: str | None = None,
    status: str | None = None,
    resolved: bool | None = None,
    blocking: bool | None = None,
) -> list[dict[str, Any]]:
    """Build the operator-only read model from existing canonical evidence."""

    from .daily_market import read_daily_market_rows

    rows = read_daily_market_rows(
        session,
        trading_date,
        expected_instrument_ids=expected_instrument_ids,
    )
    ids = [row.get("instrument_id") for row in rows if row.get("instrument_id") is not None]
    lifecycle = _lifecycle_records(session, instrument_ids=ids, trading_date=trading_date)
    from .corporate_action_authority import corporate_action_authorities_for
    failed = set(provider_failure_instrument_ids)
    output: list[dict[str, Any]] = []
    for row in rows:
        status_id = row.get("status_observation_id")
        official: tuple[TradingStatusAuthorityRecord, ...] = ()
        if status_id is not None:
            source = str(row.get("status_source") or "")
            if source in CANONICAL_STATUS_SOURCES:
                official = (
                    TradingStatusAuthorityRecord(
                        status_code=normalize_source_status(row.get("status_code"), source=source),
                        effective_from=trading_date,
                        effective_to=trading_date,
                        source=source,
                        source_reference=str(status_id),
                        reason_code=row.get("status_reason"),
                        observed_at=row.get("status_observed_at"),
                        authority_class=AuthorityClass.OFFICIAL_EXCHANGE.value,
                    ),
                )
        resolution = resolve_effective_trading_status(
            row.get("instrument_id"),
            trading_date,
            same_session_close=row.get("close"),
            official_authority=(
                *official,
                *(
                    item.to_trading_status_record()
                    for item in corporate_action_authorities_for(
                        symbol=str(row.get("symbol") or ""),
                        market=str(row.get("market") or ""),
                        trading_date=trading_date,
                    )
                ),
                *lifecycle.get(row.get("instrument_id"), ()),
            ),
            provider_failure=row.get("instrument_id") in failed,
            price_source=str(row.get("source_code") or "CANONICAL_DAILY_PRICE"),
        )
        if market and str(row.get("market")) != market:
            continue
        if status and resolution.status != status.upper():
            continue
        if resolved is not None and resolution.resolved != resolved:
            continue
        if blocking is not None and resolution.blocks_publication != blocking:
            continue
        output.append(
            {
                "tradingDate": trading_date,
                "instrumentId": row.get("instrument_id"),
                "symbol": str(row.get("symbol") or ""),
                "name": row.get("name"),
                "market": str(row.get("market") or ""),
                "resolvedStatus": resolution.status,
                "reasonCode": resolution.reason_code,
                "authoritySource": resolution.authority_source,
                "sourceReference": resolution.source_reference,
                "effectiveFrom": resolution.effective_from,
                "effectiveTo": resolution.effective_to,
                "lastValidPriceDate": row.get("last_valid_price_date"),
                "lastValidClose": row.get("last_valid_close"),
                "resolutionState": resolution.resolution_state,
                "authorityClass": resolution.authority_class,
                "isLegitimateUnavailable": resolution.is_legitimate_unavailable,
                "blocksPublication": resolution.blocks_publication,
                "affectedTopicCount": int(row.get("formal_topic_membership_count") or 0),
                "affectedTopicSlugs": list(row.get("affected_topic_slugs") or ()),
            }
        )
    return sorted(output, key=lambda item: (item["market"], item["symbol"]))


__all__ = [
    "CANONICAL_STATUS_SOURCES",
    "OFFICIAL_DAILY_SOURCES",
    "AuthorityClass",
    "BoundedStatusResolution",
    "ManualTradingStatusOverride",
    "ResolutionState",
    "StatusResolutionMetrics",
    "TradingStatusAuthorityError",
    "TradingStatusAuthorityRecord",
    "TradingStatusResolution",
    "authority_from_official_daily_result",
    "normalize_source_status",
    "read_effective_trading_status_authority",
    "resolve_effective_trading_status",
    "resolve_missing_statuses_with_budget",
]
