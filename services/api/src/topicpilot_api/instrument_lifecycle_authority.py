"""Canonical, date-effective instrument lifecycle and trading expectation reads.

This module is deliberately read-only.  It turns the repository's existing
reference lifecycle rows into one market-aware resolver contract; it does not
publish a registry, mutate a database, or infer legal no-trade from a missing
price or from a corporate-action record alone.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from topicpilot_api.instrument_universe import KNOWN_LIFECYCLE_STATUSES
from topicpilot_api.orm.models import (
    Instrument,
    Market,
    ReferenceInstrumentLifecycle,
    ReferenceRegistrySet,
)

if TYPE_CHECKING:
    from topicpilot_api.reference_data.bundle import ReferenceBundle


Identity = tuple[str, str]


class TradingExpectation(StrEnum):
    """The consumer-facing answer for one instrument and one date."""

    EXPECTED_TO_TRADE = "EXPECTED_TO_TRADE"
    LEGAL_NO_TRADE = "LEGAL_NO_TRADE"
    NOT_YET_LISTED = "NOT_YET_LISTED"
    TERMINATED = "TERMINATED"
    INACTIVE = "INACTIVE"
    UNKNOWN = "UNKNOWN"


PUBLICATION_STATE_VALIDATED_FILE = "VALIDATED_FILE_NOT_FORMALLY_PUBLISHED"
PUBLICATION_STATE_ACTIVE_DB_READ = "ACTIVE_REFERENCE_REGISTRY_READ_ONLY"
NO_TRADE_STATUSES = frozenset({"SUSPENDED", "DELISTED", "TERMINATED"})
LISTED_STATUSES = frozenset({"ACTIVE", "LISTED"})


class LifecycleAuthorityError(ValueError):
    """Raised when an authority input cannot be safely resolved."""


def _value(row: Any, name: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(name, default)
    return getattr(row, name, default)


def _as_date(value: date | str | None, *, field_name: str) -> date | None:
    if value is None or isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise LifecycleAuthorityError(f"invalid {field_name}: {value!r}") from exc


def _identity(market_code: str, instrument_code: str) -> Identity:
    market = str(market_code).strip().upper()
    code = str(instrument_code).strip()
    if not market or not code:
        raise LifecycleAuthorityError("market_code and instrument_code are required")
    return market, code


def _range_contains(start: date, end: date | None, as_of_date: date) -> bool:
    return start <= as_of_date and (end is None or as_of_date <= end)


@dataclass(frozen=True)
class LifecycleEventRecord:
    """One validated, date-effective lifecycle row and its lineage."""

    market_code: str
    instrument_code: str
    status_code: str
    effective_from: date
    effective_to: date | None = None
    evidence_id: str | None = None
    source_url: str | None = None
    reason: str | None = None
    authority_state: str = "VALIDATED"
    event_type: str | None = None
    source_record_id: str | None = None

    def __post_init__(self) -> None:
        market, code = _identity(self.market_code, self.instrument_code)
        status = str(self.status_code).strip().upper()
        if status not in KNOWN_LIFECYCLE_STATUSES:
            raise LifecycleAuthorityError(f"unsupported lifecycle status: {status}")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise LifecycleAuthorityError(
                f"invalid lifecycle range for {market}:{code}: "
                f"{self.effective_from}>{self.effective_to}"
            )
        object.__setattr__(self, "market_code", market)
        object.__setattr__(self, "instrument_code", code)
        object.__setattr__(self, "status_code", status)

    @property
    def identity(self) -> Identity:
        return self.market_code, self.instrument_code

    @property
    def key(self) -> tuple[str, str, str, date, str | None]:
        return (
            self.market_code,
            self.instrument_code,
            self.status_code,
            self.effective_from,
            self.evidence_id,
        )

    @property
    def has_formal_lineage(self) -> bool:
        return bool(self.evidence_id and self.source_url)

    @classmethod
    def from_reference_row(
        cls,
        row: Any,
        *,
        market_code: str | None = None,
        instrument_code: str | None = None,
        authority_state: str = "VALIDATED",
    ) -> LifecycleEventRecord:
        market = market_code or _value(row, "market_code")
        code = instrument_code or _value(row, "instrument_code")
        if not market or not code:
            raise LifecycleAuthorityError("reference lifecycle row lacks market-aware identity")
        effective_from = _as_date(
            _value(row, "effective_from"), field_name="effective_from"
        )
        if effective_from is None:
            raise LifecycleAuthorityError("reference lifecycle row lacks effective_from")
        return cls(
            market_code=market,
            instrument_code=code,
            status_code=_value(row, "status_code"),
            effective_from=effective_from,
            effective_to=_as_date(_value(row, "effective_to"), field_name="effective_to"),
            evidence_id=_value(row, "evidence_id"),
            source_url=_value(row, "source_url"),
            reason=_value(row, "reason"),
            authority_state=authority_state,
            event_type=_value(row, "event_type"),
            source_record_id=_value(row, "source_record_id"),
        )


@dataclass(frozen=True)
class TradingExpectationResolution:
    """Deterministic resolver output with the applicable authority lineage."""

    market_code: str
    instrument_code: str
    as_of_date: date
    expectation: TradingExpectation
    lifecycle_status: str | None = None
    reason: str = ""
    event_type: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    evidence_id: str | None = None
    source_url: str | None = None
    source_record_id: str | None = None
    authority_version: str | None = None
    authority_state: str = PUBLICATION_STATE_VALIDATED_FILE

    def __post_init__(self) -> None:
        market, code = _identity(self.market_code, self.instrument_code)
        object.__setattr__(self, "market_code", market)
        object.__setattr__(self, "instrument_code", code)
        if isinstance(self.expectation, str):
            object.__setattr__(self, "expectation", TradingExpectation(self.expectation))

    @property
    def identity(self) -> Identity:
        return self.market_code, self.instrument_code

    @property
    def is_non_trading(self) -> bool:
        return self.expectation in {
            TradingExpectation.LEGAL_NO_TRADE,
            TradingExpectation.NOT_YET_LISTED,
            TradingExpectation.TERMINATED,
            TradingExpectation.INACTIVE,
        }

    def to_dict(self) -> dict[str, str | None]:
        return {
            "market_code": self.market_code,
            "instrument_code": self.instrument_code,
            "as_of_date": self.as_of_date.isoformat(),
            "expectation": self.expectation.value,
            "lifecycle_status": self.lifecycle_status,
            "reason": self.reason,
            "event_type": self.event_type,
            "effective_from": self.effective_from.isoformat()
            if self.effective_from
            else None,
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "evidence_id": self.evidence_id,
            "source_url": self.source_url,
            "source_record_id": self.source_record_id,
            "authority_version": self.authority_version,
            "authority_state": self.authority_state,
        }


@dataclass(frozen=True)
class MissingBarDecision:
    """Shared disposition for a provider result with or without a priced bar."""

    disposition: str
    status_code: str
    status_reason: str
    covered: bool
    provider_conflict: bool = False


def resolution_from_lifecycle_status(
    *,
    market_code: str,
    instrument_code: str,
    as_of_date: date,
    lifecycle_status: str | None,
) -> TradingExpectationResolution:
    """Adapt an already-resolved status for legacy provider call sites.

    The status is deliberately an input to this compatibility adapter, not an
    inference from provider absence. New consumers should resolve from the
    authority source before calling :func:`decide_missing_bar`.
    """

    status = lifecycle_status.strip().upper() if lifecycle_status else None
    if status in NO_TRADE_STATUSES:
        expectation = TradingExpectation.LEGAL_NO_TRADE
        reason = f"resolved lifecycle status {status}"
    else:
        expectation = TradingExpectation.EXPECTED_TO_TRADE
        reason = "no lifecycle status resolved"
    return TradingExpectationResolution(
        market_code=market_code,
        instrument_code=instrument_code,
        as_of_date=as_of_date,
        expectation=expectation,
        lifecycle_status=status,
        reason=reason,
        authority_state="LEGACY_RESOLVED_STATUS_ADAPTER",
    )


class InstrumentLifecycleAuthority:
    """Read-only authority over market-aware, date-effective lifecycle events."""

    def __init__(
        self,
        *,
        known_identities: Iterable[Identity],
        lifecycle_events: Iterable[LifecycleEventRecord] = (),
        authority_version: str | None = None,
        publication_state: str = PUBLICATION_STATE_VALIDATED_FILE,
        instrument_bounds: Mapping[Identity, tuple[bool, date | None, date | None]] | None = None,
        corporate_events: Sequence[Any] = (),
    ) -> None:
        self.known_identities = frozenset(
            _identity(market, code) for market, code in known_identities
        )
        self.authority_version = authority_version
        self.publication_state = publication_state
        self.instrument_bounds = {
            _identity(*identity): bounds
            for identity, bounds in (instrument_bounds or {}).items()
        }
        self.corporate_events = tuple(corporate_events)

        deduplicated: dict[tuple[str, str, str, date, str | None], LifecycleEventRecord] = {}
        for event in lifecycle_events:
            if event.identity not in self.known_identities:
                raise LifecycleAuthorityError(
                    "lifecycle event identity is not in authority: "
                    f"{event.market_code}:{event.instrument_code}"
                )
            prior = deduplicated.get(event.key)
            if prior is not None and prior != event:
                raise LifecycleAuthorityError(f"conflicting duplicate lifecycle event: {event.key}")
            deduplicated[event.key] = event
        self.lifecycle_events = tuple(
            sorted(
                deduplicated.values(),
                key=lambda event: (
                    event.market_code,
                    event.instrument_code,
                    event.effective_from,
                    event.effective_to or date.max,
                    event.status_code,
                    event.evidence_id or "",
                ),
            )
        )
        self._validate_no_conflicting_ranges()

    @classmethod
    def from_bundle(
        cls,
        bundle: ReferenceBundle,
        *,
        authority_version: str | None = None,
        publication_state: str = PUBLICATION_STATE_VALIDATED_FILE,
        corporate_events: Sequence[Any] = (),
    ) -> InstrumentLifecycleAuthority:
        known = {
            _identity(row["market_code"], row["instrument_code"])
            for row in bundle.instruments
        }
        events = tuple(
            LifecycleEventRecord.from_reference_row(
                row,
                authority_state=publication_state,
            )
            for row in bundle.instrument_lifecycles
        )
        return cls(
            known_identities=known,
            lifecycle_events=events,
            authority_version=authority_version
            or str(
                bundle.manifest.get("referenceDataVersion")
                or bundle.manifest.get("reference_data_version")
                or bundle.manifest.get("version")
                or ""
            ),
            publication_state=publication_state,
            corporate_events=corporate_events,
        )

    @classmethod
    def from_bundle_path(
        cls,
        bundle_path: str | Path,
        *,
        corporate_event_path: str | Path | None = None,
        authority_version: str | None = None,
    ) -> InstrumentLifecycleAuthority:
        from topicpilot_api.reference_data.bundle import load_bundle

        corporate_events = (
            load_corporate_action_events(corporate_event_path)
            if corporate_event_path is not None
            else ()
        )
        return cls.from_bundle(
            load_bundle(Path(bundle_path)),
            authority_version=authority_version,
            corporate_events=corporate_events,
        )

    @classmethod
    def from_reference_rows(
        cls,
        *,
        known_identities: Iterable[Identity],
        rows: Iterable[Any],
        identity: Identity | None = None,
        authority_version: str | None = None,
        publication_state: str = PUBLICATION_STATE_ACTIVE_DB_READ,
        instrument_bounds: Mapping[Identity, tuple[bool, date | None, date | None]] | None = None,
    ) -> InstrumentLifecycleAuthority:
        return cls(
            known_identities=known_identities,
            lifecycle_events=tuple(
                LifecycleEventRecord.from_reference_row(
                    row,
                    market_code=identity[0] if identity else None,
                    instrument_code=identity[1] if identity else None,
                    authority_state=publication_state,
                )
                for row in rows
            ),
            authority_version=authority_version,
            publication_state=publication_state,
            instrument_bounds=instrument_bounds,
        )

    def _validate_no_conflicting_ranges(self) -> None:
        by_identity: dict[Identity, list[LifecycleEventRecord]] = {}
        for event in self.lifecycle_events:
            by_identity.setdefault(event.identity, []).append(event)
        for identity, events in by_identity.items():
            for index, left in enumerate(events):
                for right in events[index + 1 :]:
                    if left.effective_from > (right.effective_to or date.max):
                        continue
                    if right.effective_from > (left.effective_to or date.max):
                        continue
                    if left.status_code != right.status_code:
                        raise LifecycleAuthorityError(
                            "overlapping lifecycle statuses are ambiguous for "
                            f"{identity[0]}:{identity[1]}: {left.status_code}/{right.status_code}"
                        )

    def _resolution(
        self,
        identity: Identity,
        as_of_date: date,
        expectation: TradingExpectation,
        *,
        reason: str,
        event: LifecycleEventRecord | None = None,
        lifecycle_status: str | None = None,
    ) -> TradingExpectationResolution:
        return TradingExpectationResolution(
            market_code=identity[0],
            instrument_code=identity[1],
            as_of_date=as_of_date,
            expectation=expectation,
            lifecycle_status=lifecycle_status or (event.status_code if event else None),
            reason=reason,
            event_type=event.event_type if event else None,
            effective_from=event.effective_from if event else None,
            effective_to=event.effective_to if event else None,
            evidence_id=event.evidence_id if event else None,
            source_url=event.source_url if event else None,
            source_record_id=event.source_record_id if event else None,
            authority_version=self.authority_version,
            authority_state=event.authority_state if event else self.publication_state,
        )

    def resolve_trading_expectation(
        self,
        market_code: str,
        instrument_code: str,
        as_of_date: date,
    ) -> TradingExpectationResolution:
        identity = _identity(market_code, instrument_code)
        if identity not in self.known_identities:
            return self._resolution(
                identity,
                as_of_date,
                TradingExpectation.UNKNOWN,
                reason="INSTRUMENT_IDENTITY_NOT_IN_AUTHORITY",
            )

        bounds = self.instrument_bounds.get(identity)
        if bounds is not None:
            is_active, valid_from, valid_to = bounds
            if not is_active:
                return self._resolution(
                    identity,
                    as_of_date,
                    TradingExpectation.INACTIVE,
                    reason="INSTRUMENT_INACTIVE",
                )
            if valid_from is not None and as_of_date < valid_from:
                return self._resolution(
                    identity,
                    as_of_date,
                    TradingExpectation.NOT_YET_LISTED,
                    reason="INSTRUMENT_VALID_FROM_NOT_REACHED",
                )
            if valid_to is not None and as_of_date > valid_to:
                return self._resolution(
                    identity,
                    as_of_date,
                    TradingExpectation.INACTIVE,
                    reason="INSTRUMENT_VALID_TO_EXPIRED",
                )

        events = [event for event in self.lifecycle_events if event.identity == identity]
        applicable = [
            event
            for event in events
            if _range_contains(event.effective_from, event.effective_to, as_of_date)
        ]
        if not applicable:
            future_listing = [
                event
                for event in events
                if event.status_code in LISTED_STATUSES and event.effective_from > as_of_date
            ]
            if future_listing:
                event = min(future_listing, key=lambda candidate: candidate.effective_from)
                return self._resolution(
                    identity,
                    as_of_date,
                    TradingExpectation.NOT_YET_LISTED,
                    reason="NEXT_LISTING_EVENT_NOT_YET_EFFECTIVE",
                    event=event,
                )
            return self._resolution(
                identity,
                as_of_date,
                TradingExpectation.EXPECTED_TO_TRADE,
                reason="NO_EFFECTIVE_NO_TRADE_AUTHORITY",
            )

        event = max(
            applicable,
            key=lambda candidate: (
                candidate.effective_from,
                candidate.status_code,
                candidate.evidence_id or "",
            ),
        )
        if event.status_code == "SUSPENDED":
            if not event.has_formal_lineage:
                return self._resolution(
                    identity,
                    as_of_date,
                    TradingExpectation.UNKNOWN,
                    reason="LIFECYCLE_AUTHORITY_LINEAGE_INCOMPLETE",
                    event=event,
                )
            return self._resolution(
                identity,
                as_of_date,
                TradingExpectation.LEGAL_NO_TRADE,
                reason=event.reason or "LIFECYCLE_SUSPENDED",
                event=event,
            )
        if event.status_code in {"DELISTED", "TERMINATED"}:
            if not event.has_formal_lineage:
                return self._resolution(
                    identity,
                    as_of_date,
                    TradingExpectation.UNKNOWN,
                    reason="LIFECYCLE_AUTHORITY_LINEAGE_INCOMPLETE",
                    event=event,
                )
            return self._resolution(
                identity,
                as_of_date,
                TradingExpectation.TERMINATED,
                reason=event.reason or f"LIFECYCLE_{event.status_code}",
                event=event,
            )
        return self._resolution(
            identity,
            as_of_date,
            TradingExpectation.EXPECTED_TO_TRADE,
            reason=event.reason or f"LIFECYCLE_{event.status_code}",
            event=event,
        )

    def corporate_events_for(self, market_code: str, instrument_code: str) -> tuple[Any, ...]:
        identity = _identity(market_code, instrument_code)
        return tuple(
            event
            for event in self.corporate_events
            if _identity(event.market_code, event.instrument_code) == identity
        )


def decide_missing_bar(
    resolution: TradingExpectationResolution,
    *,
    has_observation: bool,
    has_priced_bar: bool,
) -> MissingBarDecision:
    """Apply the shared fail-closed missing-bar policy to a resolver output."""

    if resolution.is_non_trading:
        if has_observation:
            return MissingBarDecision(
                disposition="LIFECYCLE_PROVIDER_CONFLICT",
                status_code=resolution.lifecycle_status or resolution.expectation.value,
                status_reason=(
                    "provider returned an observation during an authoritative "
                    "no-trade interval"
                ),
                covered=False,
                provider_conflict=True,
            )
        if resolution.expectation == TradingExpectation.LEGAL_NO_TRADE:
            status_code = resolution.lifecycle_status or "NO_TRADE"
        else:
            status_code = resolution.expectation.value
        return MissingBarDecision(
            disposition="COVERED_BY_LIFECYCLE_AUTHORITY",
            status_code=status_code,
            status_reason=resolution.reason,
            covered=True,
        )
    if has_priced_bar:
        return MissingBarDecision(
            disposition="PRICED_BAR_PRESENT",
            status_code="AVAILABLE",
            status_reason="official priced bar present",
            covered=True,
        )
    return MissingBarDecision(
        disposition="MISSING_MARKET_DATA",
        status_code="UNKNOWN",
        status_reason=f"MISSING_MARKET_DATA: no priced bar for {resolution.expectation.value}",
        covered=False,
    )


def load_corporate_action_events(path: str | Path) -> tuple[Any, ...]:
    """Validate an existing corporate-action artifact without promoting it."""

    from topicpilot_api.research.corporate_action_dataset import CorporateActionEvent

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    records = payload.get("events", payload) if isinstance(payload, Mapping) else payload
    if not isinstance(records, list):
        raise LifecycleAuthorityError(f"corporate event artifact is not a list: {path}")
    return tuple(CorporateActionEvent.from_dict(record) for record in records)


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_sqlalchemy_trading_expectation(
    session: Session,
    *,
    market_code: str,
    instrument_code: str,
    as_of_date: date,
    reference_data_version: str,
) -> TradingExpectationResolution:
    """Read the active reference set and resolve one DB identity, read-only."""

    identity = _identity(market_code, instrument_code)
    registry = session.scalar(
        select(ReferenceRegistrySet).where(
            ReferenceRegistrySet.reference_data_version == reference_data_version,
            ReferenceRegistrySet.status == "ACTIVE",
        )
    )
    if registry is None:
        return TradingExpectationResolution(
            market_code=identity[0],
            instrument_code=identity[1],
            as_of_date=as_of_date,
            expectation=TradingExpectation.UNKNOWN,
            reason="REFERENCE_AUTHORITY_UNAVAILABLE",
            authority_version=reference_data_version,
            authority_state="NO_ACTIVE_REFERENCE_REGISTRY",
        )

    pair = session.execute(
        select(Instrument, Market)
        .join(Market, Market.id == Instrument.market_id)
        .where(
            Instrument.instrument_code == identity[1],
            Market.code == identity[0],
        )
    ).one_or_none()
    if pair is None:
        return TradingExpectationResolution(
            market_code=identity[0],
            instrument_code=identity[1],
            as_of_date=as_of_date,
            expectation=TradingExpectation.UNKNOWN,
            reason="INSTRUMENT_IDENTITY_NOT_IN_AUTHORITY",
            authority_version=reference_data_version,
            authority_state=PUBLICATION_STATE_ACTIVE_DB_READ,
        )

    instrument, market = pair
    bounds = {
        identity: (
            bool(instrument.is_active and market.is_active),
            instrument.valid_from,
            instrument.valid_to,
        )
    }
    rows = session.scalars(
        select(ReferenceInstrumentLifecycle).where(
            ReferenceInstrumentLifecycle.registry_set_id == registry.id,
            ReferenceInstrumentLifecycle.instrument_id == instrument.id,
        )
    ).all()
    authority = InstrumentLifecycleAuthority.from_reference_rows(
        known_identities=(identity,),
        rows=rows,
        identity=identity,
        authority_version=reference_data_version,
        publication_state=PUBLICATION_STATE_ACTIVE_DB_READ,
        instrument_bounds=bounds,
    )
    return authority.resolve_trading_expectation(*identity, as_of_date)


def resolve_trading_expectation(
    authority: InstrumentLifecycleAuthority,
    market_code: str,
    instrument_code: str,
    as_of_date: date,
) -> TradingExpectationResolution:
    """Small stable function contract for consumers that do not need a class."""

    return authority.resolve_trading_expectation(market_code, instrument_code, as_of_date)
