from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from topicpilot_api.orm.models import (
    Instrument,
    Market,
    MarketDataSource,
    ObservationTimelineEntry,
    RawMarketObservation,
    ReferenceAdjustment,
    ReferenceCurrency,
    ReferenceRegistrySet,
    ReferenceSession,
    ReferenceTimezone,
    ReferenceTradingStatus,
)

from .contracts import (
    InputEnvelope,
    MappingPolicy,
    ReferenceContext,
    ReferenceContextRequest,
    ensure_utc,
)
from .registry import NormalizerKey, NormalizerRegistry
from .results import RuntimeResult
from .service import NormalizationService
from .synthetic import SyntheticReferenceNormalizer


class RuntimeLoadError(ValueError):
    pass


class TimelineInputLoader:
    def __init__(self, session: Session):
        self.session = session

    def load(self, entry_id: Any) -> InputEnvelope:
        entry = self.session.scalar(
            select(ObservationTimelineEntry).where(ObservationTimelineEntry.id == entry_id)
        )
        if entry is None:
            raise RuntimeLoadError("timeline entry not found")
        raw = self.session.scalar(
            select(RawMarketObservation).where(RawMarketObservation.id == entry.raw_observation_id)
        )
        source = self.session.scalar(
            select(MarketDataSource).where(MarketDataSource.id == entry.source_id)
        )
        instrument = self.session.scalar(
            select(Instrument).where(Instrument.id == entry.instrument_id)
        )
        market = (
            self.session.scalar(select(Market).where(Market.id == instrument.market_id))
            if instrument
            else None
        )
        if not raw or not source or not instrument or not market:
            raise RuntimeLoadError("incomplete observation lineage")
        if raw.source_id != entry.source_id or raw.instrument_id != entry.instrument_id:
            raise RuntimeLoadError("inconsistent raw/timeline lineage")
        if (
            source.status not in ("REGISTERED", "ACTIVE")
            or not instrument.is_active
            or not market.is_active
        ):
            raise RuntimeLoadError("inactive source, instrument, or market")
        if entry.payload != raw.payload or ensure_utc(entry.observed_at) != ensure_utc(
            raw.observed_at
        ):
            raise RuntimeLoadError("timeline/raw observation mismatch")
        return InputEnvelope(
            dict(entry.payload),
            instrument.id,
            source.id,
            entry.id,
            raw.id,
            entry.observed_at,
            entry.received_at,
            entry.retrieved_at,
            entry.ordering_key,
        )


class DatabaseReferenceContextLoader:
    def __init__(self, session: Session):
        self.session = session

    def load_reference_context(self, request: ReferenceContextRequest) -> ReferenceContext:
        sets = list(
            self.session.scalars(
                select(ReferenceRegistrySet).where(
                    ReferenceRegistrySet.reference_data_version == request.reference_data_version
                )
            )
        )
        if len(sets) != 1 or sets[0].status != "ACTIVE":
            raise RuntimeLoadError("reference registry set is missing, duplicate, or inactive")
        registry_id = sets[0].id

        def one(model, **filters):
            rows = list(
                self.session.scalars(
                    select(model).filter_by(registry_set_id=registry_id, **filters)
                )
            )
            if len(rows) != 1:
                raise RuntimeLoadError(
                    f"reference data is missing or duplicate: {model.__tablename__}"
                )
            return rows[0]

        currency = one(ReferenceCurrency, code=request.currency_code)
        timezone_row = one(ReferenceTimezone, name=request.timezone_name)
        session_row = one(ReferenceSession, code=request.session_code)
        if request.calendar_code is not None and session_row.calendar_code != request.calendar_code:
            raise RuntimeLoadError("reference session/calendar mismatch")
        statuses = list(
            self.session.scalars(
                select(ReferenceTradingStatus).where(
                    ReferenceTradingStatus.registry_set_id == registry_id
                )
            )
        )
        adjustments = list(
            self.session.scalars(
                select(ReferenceAdjustment).where(
                    ReferenceAdjustment.registry_set_id == registry_id
                )
            )
        )
        if not statuses or not adjustments:
            raise RuntimeLoadError("reference status or adjustment catalogue is empty")
        return ReferenceContext(
            request.reference_data_version,
            timezone_row.name,
            session_row.code,
            session_row.calendar_code,
            currency.code,
            currency.scale,
            request.reference_data_version,
            frozenset(row.code for row in statuses),
        )


class NormalizationRuntime:
    def __init__(self, session: Session, registry: NormalizerRegistry | None = None):
        self.session = session
        self.registry = registry or NormalizerRegistry()
        if len(self.registry) == 0:
            self.registry.register(
                NormalizerKey(
                    "SYNTHETIC", "v1", "normalization-contract-v1", "synthetic-mapping-v1"
                ),
                SyntheticReferenceNormalizer(),
            )

    def normalize_timeline_entry(
        self, entry_id: Any, policy: MappingPolicy, reference_data_version: str
    ) -> RuntimeResult:
        """Run in the caller-owned transaction; never commits."""
        envelope = TimelineInputLoader(self.session).load(entry_id)
        instrument = self.session.get(Instrument, envelope.instrument_id)
        market = self.session.get(Market, instrument.market_id) if instrument else None
        if (
            not instrument
            or not market
            or not instrument.currency
            or not market.timezone
            or not market.calendar_code
        ):
            raise RuntimeLoadError("instrument/market reference context is incomplete")
        request = ReferenceContextRequest(
            reference_data_version,
            instrument.currency,
            market.timezone,
            policy.session_code,
            policy.calendar_code or market.calendar_code,
        )
        reference = DatabaseReferenceContextLoader(self.session).load_reference_context(request)
        source = self.session.scalar(
            select(MarketDataSource).where(MarketDataSource.id == envelope.source_id)
        )
        if source is None:
            raise RuntimeLoadError("source disappeared during normalization")
        mapper = self.registry.resolve(
            NormalizerKey(
                source.source_code,
                source.adapter_version,
                policy.normalization_contract_version,
                policy.mapping_policy_version,
            )
        )
        normalization = mapper(envelope, reference, policy)
        service = NormalizationService(self.session, mapper)
        return service.persist(envelope, reference, policy, normalization)

    def normalize_timeline_entry_atomic(
        self, session_factory, entry_id: Any, policy: MappingPolicy, reference_data_version: str
    ) -> RuntimeResult:
        """Own an atomic transaction using a dedicated session from ``session_factory``."""
        with session_factory() as session, session.begin():
            return NormalizationRuntime(session, self.registry).normalize_timeline_entry(
                entry_id, policy, reference_data_version
            )
