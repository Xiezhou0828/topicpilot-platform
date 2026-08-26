"""Transactional historical-provider ingestion into the V2 observation chain."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from topicpilot_api.normalizer import (
    HISTORICAL_MAPPING_POLICY_VERSION,
    HistoricalDailyBarNormalizer,
    MappingPolicy,
    NormalizationRuntime,
    NormalizerKey,
    NormalizerRegistry,
)
from topicpilot_api.normalizer.contracts import stable_hash
from topicpilot_api.normalizer.runtime import RuntimeLoadError
from topicpilot_api.orm.models import (
    Instrument,
    Market,
    MarketDataSource,
    ObservationTimelineBatch,
    ObservationTimelineEntry,
    RawMarketObservation,
    ReferenceInstrumentLifecycle,
    ReferenceRegistrySet,
)

from .history import (
    COVERED_NO_TRADE_STATUS_CODES,
    HistoricalBar,
    HistoricalFetchResult,
    HistoricalProvider,
)


class HistoricalIngestionError(ValueError):
    """A deterministic, caller-visible ingestion failure."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class HistoricalSourceRegistration:
    source_code: str
    adapter_version: str
    source_category: str = "HISTORICAL_DAILY"
    observation_semantics: str = "DAILY_BAR"
    adjustment_policy: str = "UNKNOWN"
    calendar_policy: str = "MARKET_CALENDAR"
    licensing_classification: str = "PRIVATE_RUNTIME"
    status: str = "REGISTERED"


@dataclass(frozen=True)
class HistoricalIngestionResult:
    batch_id: UUID
    request_key: str
    instrument_count: int
    provider_point_count: int
    raw_created: int
    raw_reused: int
    timeline_created: int
    timeline_reused: int
    canonical_created: int
    canonical_reused: int
    incomplete_canonical_count: int
    instrument_status: str = "UNKNOWN"
    status_reason: str | None = None
    observed_count: int = 0
    priced_count: int = 0
    covered_count: int = 0
    unexplained_missing_count: int = 0

    @property
    def is_noop(self) -> bool:
        return self.raw_created == 0 and self.timeline_created == 0 and self.canonical_created == 0

    def to_dict(self) -> dict[str, int | str | bool]:
        return {
            "batchId": str(self.batch_id),
            "requestKey": self.request_key,
            "instrumentCount": self.instrument_count,
            "providerPointCount": self.provider_point_count,
            "rawCreated": self.raw_created,
            "rawReused": self.raw_reused,
            "timelineCreated": self.timeline_created,
            "timelineReused": self.timeline_reused,
            "canonicalCreated": self.canonical_created,
            "canonicalReused": self.canonical_reused,
            "incompleteCanonicalCount": self.incomplete_canonical_count,
            "instrumentStatus": self.instrument_status,
            "statusReason": self.status_reason,
            "observedCount": self.observed_count,
            "pricedCount": self.priced_count,
            "coveredCount": self.covered_count,
            "unexplainedMissingCount": self.unexplained_missing_count,
            "noop": self.is_noop,
        }


def _as_utc_midnight(value: date | None) -> datetime | None:
    return datetime.combine(value, time.min, tzinfo=timezone.utc) if value is not None else None  # noqa: UP017


def _observed_at(trading_date: date, timezone_name: str) -> datetime:
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise HistoricalIngestionError("INVALID_MARKET_TIMEZONE", timezone_name) from exc
    # Daily providers return a trading date rather than an event timestamp.
    # Midnight is an explicit date anchor; it must not be interpreted as the
    # close timestamp by downstream consumers.
    return datetime.combine(trading_date, time.min, tzinfo=timezone)


def _text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    normalized = value.normalize()
    return "0" if normalized == 0 else format(normalized, "f")


def _bar_payload(result: HistoricalFetchResult, bar: HistoricalBar) -> dict[str, str | None]:
    payload: dict[str, str | None] = {
        "date": bar.trading_date.isoformat(),
        "open": _text(bar.open),
        "high": _text(bar.high),
        "low": _text(bar.low),
        "close": _text(bar.close),
        "volume": _text(bar.volume),
        "source_symbol": result.source_symbol,
    }
    if result.status_explicit:
        payload["instrument_status"] = result.instrument_status
        payload["status_reason"] = result.status_reason
    return payload


def _status_payload(
    result: HistoricalFetchResult, trading_date: date
) -> dict[str, str | None]:
    """Represent exchange-confirmed no-trade as evidence, not a fabricated bar."""

    return {
        "date": trading_date.isoformat(),
        "open": None,
        "high": None,
        "low": None,
        "close": None,
        "volume": None,
        "source_symbol": result.source_symbol,
        "instrument_status": result.instrument_status if result.status_explicit else "UNKNOWN",
        "status_reason": result.status_reason,
    }


def _load_instrument(session: Session, code: str, market_code: str) -> tuple[Instrument, Market]:
    row = session.execute(
        select(Instrument, Market)
        .join(Market, Market.id == Instrument.market_id)
        .where(
            Instrument.instrument_code == code,
            Market.code == market_code,
            Instrument.is_active.is_(True),
            Market.is_active.is_(True),
        )
    ).one_or_none()
    if row is None:
        raise HistoricalIngestionError(
            "INSTRUMENT_NOT_FOUND", f"active V2 identity not found: {market_code}/{code}"
        )
    return row[0], row[1]


def _effective_lifecycle_status(
    session: Session,
    *,
    instrument_id: UUID,
    reference_data_version: str,
    trading_date: date,
) -> str | None:
    """Resolve the authoritative instrument state for one date."""

    registry_id = session.scalar(
        select(ReferenceRegistrySet.id).where(
            ReferenceRegistrySet.reference_data_version == reference_data_version,
            ReferenceRegistrySet.status == "ACTIVE",
        )
    )
    if registry_id is None:
        return None
    return session.scalar(
        select(ReferenceInstrumentLifecycle.status_code)
        .where(
            ReferenceInstrumentLifecycle.registry_set_id == registry_id,
            ReferenceInstrumentLifecycle.instrument_id == instrument_id,
            ReferenceInstrumentLifecycle.effective_from <= trading_date,
            or_(
                ReferenceInstrumentLifecycle.effective_to.is_(None),
                ReferenceInstrumentLifecycle.effective_to >= trading_date,
            ),
        )
        .order_by(
            ReferenceInstrumentLifecycle.effective_from.desc(),
            ReferenceInstrumentLifecycle.id.desc(),
        )
        .limit(1)
    )


def classify_authoritative_no_trade_result(
    result: HistoricalFetchResult,
    *,
    lifecycle_status: str | None,
    trading_date: date | None,
) -> HistoricalFetchResult:
    """Separate lifecycle-authorized no-trade from active missing data."""

    if trading_date is None:
        return result
    if lifecycle_status in {"SUSPENDED", "DELISTED", "TERMINATED"}:
        if result.bars:
            raise HistoricalIngestionError(
                "LIFECYCLE_PROVIDER_CONFLICT",
                f"{lifecycle_status} instrument returned an observation on "
                f"{trading_date.isoformat()}",
            )
        return replace(
            result,
            instrument_status=lifecycle_status,
            status_reason=(
                result.status_reason
                or f"reference lifecycle authorizes {lifecycle_status} on "
                f"{trading_date.isoformat()}"
            ),
            status_explicit=True,
        )
    if result.has_priced_observation:
        return result
    return replace(
        result,
        instrument_status="UNKNOWN",
        status_reason=(
            f"MISSING_MARKET_DATA: no priced bar for active instrument on "
            f"{trading_date.isoformat()}"
        ),
        status_explicit=True,
    )


def _apply_authoritative_no_trade_state(
    session: Session,
    result: HistoricalFetchResult,
    *,
    instrument_id: UUID,
    reference_data_version: str,
    trading_date: date | None,
) -> HistoricalFetchResult:
    lifecycle_status = (
        _effective_lifecycle_status(
            session,
            instrument_id=instrument_id,
            reference_data_version=reference_data_version,
            trading_date=trading_date,
        )
        if trading_date is not None
        else None
    )
    return classify_authoritative_no_trade_result(
        result,
        lifecycle_status=lifecycle_status,
        trading_date=trading_date,
    )


def _get_or_create_source(
    session: Session, registration: HistoricalSourceRegistration
) -> MarketDataSource:
    source = session.scalar(
        select(MarketDataSource).where(
            MarketDataSource.source_code == registration.source_code,
            MarketDataSource.adapter_version == registration.adapter_version,
        )
    )
    if source is None:
        source = MarketDataSource(
            source_code=registration.source_code,
            source_category=registration.source_category,
            adapter_version=registration.adapter_version,
            observation_semantics=registration.observation_semantics,
            adjustment_policy=registration.adjustment_policy,
            calendar_policy=registration.calendar_policy,
            licensing_classification=registration.licensing_classification,
            status=registration.status,
        )
        session.add(source)
        session.flush()
        return source
    expected = {
        "source_category": registration.source_category,
        "observation_semantics": registration.observation_semantics,
        "adjustment_policy": registration.adjustment_policy,
        "calendar_policy": registration.calendar_policy,
        "licensing_classification": registration.licensing_classification,
    }
    actual = {key: getattr(source, key) for key in expected}
    if actual != expected:
        raise HistoricalIngestionError(
            "SOURCE_METADATA_CONFLICT", "registered source metadata does not match the adapter"
        )
    if source.status not in ("REGISTERED", "ACTIVE"):
        raise HistoricalIngestionError("SOURCE_NOT_ACTIVE", "historical source is not active")
    return source


def _request_key(
    registration: HistoricalSourceRegistration,
    instruments: Sequence[tuple[str, str]],
    requested_from: date | None,
    requested_to: date | None,
    policy: MappingPolicy,
) -> str:
    return stable_hash(
        {
            "source": registration.source_code,
            "adapter": registration.adapter_version,
            "instruments": [f"{market}:{code}" for code, market in instruments],
            "from": requested_from.isoformat() if requested_from else None,
            "to": requested_to.isoformat() if requested_to else None,
            "normalization": policy.normalization_contract_version,
            "mapping": policy.mapping_policy_version,
            "request_version": "historical-ingestion-v1",
        }
    )


def ingest_historical(
    session: Session,
    provider: HistoricalProvider,
    instruments: Iterable[tuple[str, str]],
    *,
    reference_data_version: str,
    requested_from: date | None = None,
    requested_to: date | None = None,
    policy: MappingPolicy | None = None,
    registration: HistoricalSourceRegistration | None = None,
    clock: Callable[[], datetime] | None = None,
) -> HistoricalIngestionResult:
    """Fetch first, then persist and normalize in the caller's transaction.

    The function never commits.  A caller can wrap it in ``session.begin()``
    and any provider-shape, identity, reference, or normalization error will
    roll back the entire raw/timeline/canonical write set.
    """

    if not reference_data_version:
        raise HistoricalIngestionError(
            "REFERENCE_VERSION_REQUIRED",
            "reference data version is required",
        )
    if requested_from and requested_to and requested_to < requested_from:
        raise HistoricalIngestionError(
            "INVALID_DATE_WINDOW",
            "requested_to precedes requested_from",
        )
    normalized_instruments = sorted(set(instruments), key=lambda item: (item[1], item[0]))
    if not normalized_instruments:
        raise HistoricalIngestionError(
            "INSTRUMENTS_REQUIRED",
            "at least one instrument is required",
        )
    policy = policy or MappingPolicy(mapping_policy_version=HISTORICAL_MAPPING_POLICY_VERSION)
    registration = registration or HistoricalSourceRegistration(
        provider.source_code, provider.adapter_version
    )
    if (registration.source_code, registration.adapter_version) != (
        provider.source_code,
        provider.adapter_version,
    ):
        raise HistoricalIngestionError(
            "SOURCE_IDENTITY_MISMATCH",
            "provider and source registration differ",
        )

    fetched: list[tuple[tuple[str, str], HistoricalFetchResult, tuple[HistoricalBar, ...]]] = []
    for code, market_code in normalized_instruments:
        result = provider.fetch_daily(code, market_code)
        selected = tuple(
            bar
            for bar in result.bars
            if (requested_from is None or bar.trading_date >= requested_from)
            and (requested_to is None or bar.trading_date <= requested_to)
        )
        fetched.append(((code, market_code), result, selected))

    source = _get_or_create_source(session, registration)
    request_key = _request_key(
        registration,
        normalized_instruments,
        requested_from,
        requested_to,
        policy,
    )
    batch = session.scalar(
        select(ObservationTimelineBatch).where(
            ObservationTimelineBatch.source_id == source.id,
            ObservationTimelineBatch.request_key == request_key,
        )
    )
    if batch is None:
        batch = ObservationTimelineBatch(
            source_id=source.id,
            requested_instrument_id=None,
            requested_from=_as_utc_midnight(requested_from),
            requested_to=_as_utc_midnight(requested_to),
            request_key=request_key,
            status="OPEN",
            coverage_status="UNKNOWN",
            metadata_payload={
                "sourceCode": registration.source_code,
                "adapterVersion": registration.adapter_version,
                "normalizationContractVersion": policy.normalization_contract_version,
                "mappingPolicyVersion": policy.mapping_policy_version,
                "instrumentCount": len(normalized_instruments),
            },
        )
        session.add(batch)
        session.flush()
    elif batch.status == "FAILED":
        raise HistoricalIngestionError(
            "PREVIOUS_BATCH_FAILED",
            "request key belongs to a failed batch",
        )

    registry = NormalizerRegistry()
    registry.register(
        NormalizerKey(
            registration.source_code,
            registration.adapter_version,
            policy.normalization_contract_version,
            policy.mapping_policy_version,
        ),
        HistoricalDailyBarNormalizer(),
    )
    runtime = NormalizationRuntime(session, registry)
    counts = {
        "provider": 0,
        "raw_created": 0,
        "raw_reused": 0,
        "timeline_created": 0,
        "timeline_reused": 0,
        "canonical_created": 0,
        "canonical_reused": 0,
        "incomplete": 0,
        "observed": 0,
        "priced": 0,
        "covered": 0,
        "unexplained": 0,
    }
    all_covered = True
    result_statuses: list[str] = []
    result_reasons: list[str] = []
    for (code, market_code), result, bars in fetched:
        instrument, market = _load_instrument(session, code, market_code)
        status_date = requested_from if requested_from == requested_to else None
        result = _apply_authoritative_no_trade_state(
            session,
            result,
            instrument_id=instrument.id,
            reference_data_version=reference_data_version,
            trading_date=status_date,
        )
        observations: list[tuple[date, HistoricalBar | None, dict[str, str | None]]] = [
            (bar.trading_date, bar, _bar_payload(result, bar)) for bar in bars
        ]
        if not observations and status_date is not None:
            observations.append((status_date, None, _status_payload(result, status_date)))
        result_status = result.instrument_status if result.status_explicit else (
            "AVAILABLE" if any(bar.close is not None for bar in bars) else "UNKNOWN"
        )
        result_statuses.append(result_status)
        if result.status_reason:
            result_reasons.append(result.status_reason)
        if not observations:
            all_covered = False
        counts["provider"] += len(bars)
        for trading_date, _bar, payload in observations:
            observed_at = _observed_at(trading_date, market.timezone)
            close_present = payload.get("close") is not None
            status_code = payload.get("instrument_status")
            covered = close_present or status_code in COVERED_NO_TRADE_STATUS_CODES
            counts["observed"] += 1
            counts["priced"] += int(close_present)
            counts["covered"] += int(covered)
            counts["unexplained"] += int(not covered)
            all_covered = all_covered and covered
            prior_entry = session.scalar(
                select(ObservationTimelineEntry)
                .where(
                    ObservationTimelineEntry.instrument_id == instrument.id,
                    ObservationTimelineEntry.source_id == source.id,
                    ObservationTimelineEntry.observed_at == observed_at,
                    ObservationTimelineEntry.entry_status == "ACTIVE",
                )
                .order_by(ObservationTimelineEntry.id.desc())
            )
            raw_hash = stable_hash(
                {
                    "sourceCode": result.source_code,
                    "adapterVersion": result.adapter_version,
                    "instrumentCode": code,
                    "marketCode": market_code,
                    "bar": payload,
                }
            )
            raw = session.scalar(
                select(RawMarketObservation).where(
                    RawMarketObservation.source_id == source.id,
                    RawMarketObservation.content_hash == raw_hash,
                )
            )
            if raw is None:
                raw = RawMarketObservation(
                    source_id=source.id,
                    instrument_id=instrument.id,
                    # A legitimate no-trade observation has no HistoricalBar.
                    # Its stable identity is anchored to the requested date.
                    upstream_observation_id=f"{result.source_symbol}:{trading_date.isoformat()}",
                    source_instrument_identifier=result.source_symbol,
                    observed_at=observed_at,
                    retrieved_at=result.retrieved_at,
                    payload=payload,
                    content_hash=raw_hash,
                    quality_status="CAPTURED",
                    ingestion_correlation_id=request_key,
                    supersedes_id=prior_entry.raw_observation_id if prior_entry else None,
                )
                session.add(raw)
                session.flush()
                counts["raw_created"] += 1
            else:
                counts["raw_reused"] += 1
                if raw.instrument_id != instrument.id:
                    raise HistoricalIngestionError(
                        "RAW_IDENTITY_CONFLICT",
                        "raw observation identity differs",
                    )

            entry = session.scalar(
                select(ObservationTimelineEntry).where(
                    ObservationTimelineEntry.raw_observation_id == raw.id
                )
            )
            if entry is None:
                entry = ObservationTimelineEntry(
                    instrument_id=instrument.id,
                    source_id=source.id,
                    raw_observation_id=raw.id,
                    batch_id=batch.id,
                    observed_at=raw.observed_at,
                    received_at=result.retrieved_at,
                    retrieved_at=result.retrieved_at,
                    ordering_key=trading_date.isoformat(),
                    payload=payload,
                    content_hash=stable_hash({"raw": raw_hash, "payload": payload}),
                    supersedes_id=prior_entry.id if prior_entry else None,
                    entry_status="ACTIVE",
                )
                session.add(entry)
                session.flush()
                counts["timeline_created"] += 1
            else:
                counts["timeline_reused"] += 1

            try:
                normalized = runtime.normalize_timeline_entry(
                    entry.id, policy, reference_data_version
                )
            except RuntimeLoadError as exc:
                raise HistoricalIngestionError(
                    "REFERENCE_DATA_UNAVAILABLE",
                    f"reference data context unavailable: {exc}",
                ) from exc
            for persisted in normalized.persisted:
                if persisted.created:
                    counts["canonical_created"] += 1
                else:
                    counts["canonical_reused"] += 1
                if persisted.quality_state == "INCOMPLETE":
                    counts["incomplete"] += 1

    batch.status = "COMPLETED"
    batch.coverage_status = "COMPLETE" if all_covered else "SPARSE"
    # Keep Python 3.10 compatibility for the private provider runtime.
    batch.completed_at = (clock or (lambda: datetime.now(timezone.utc)))()  # noqa: UP017
    session.flush()
    return HistoricalIngestionResult(
        batch_id=batch.id,
        request_key=request_key,
        instrument_count=len(normalized_instruments),
        provider_point_count=counts["provider"],
        raw_created=counts["raw_created"],
        raw_reused=counts["raw_reused"],
        timeline_created=counts["timeline_created"],
        timeline_reused=counts["timeline_reused"],
        canonical_created=counts["canonical_created"],
        canonical_reused=counts["canonical_reused"],
        incomplete_canonical_count=counts["incomplete"],
        instrument_status=(
            result_statuses[0]
            if len(set(result_statuses)) == 1 and result_statuses
            else "UNKNOWN"
        ),
        status_reason=(
            result_reasons[0]
            if len(set(result_reasons)) == 1 and result_reasons
            else None
        ),
        observed_count=counts["observed"],
        priced_count=counts["priced"],
        covered_count=counts["covered"],
        unexplained_missing_count=counts["unexplained"],
    )
