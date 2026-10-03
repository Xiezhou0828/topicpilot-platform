"""Official exact-prior-session PRICE-only writer, never a historical run.

Uses the existing raw -> timeline -> canonical normalization transaction.
No Home/Topic/run/tracking writer is imported or called. Provider receipts
live in existing JSON evidence columns; no schema or formula change.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from topicpilot_api.market_data.history import HistoricalBar
from topicpilot_api.market_data.ingestion import (
    HistoricalSourceRegistration,
    _get_or_create_source,
    _load_instrument,
)
from topicpilot_api.market_data.registry import build_historical_provider_registry
from topicpilot_api.normalizer import (
    HISTORICAL_MAPPING_POLICY_VERSION,
    HistoricalDailyBarNormalizer,
    MappingPolicy,
    NormalizationRuntime,
    NormalizerKey,
    NormalizerRegistry,
)
from topicpilot_api.normalizer.contracts import NormalizationResult, stable_hash
from topicpilot_api.orm.models import (
    CanonicalObservation,
    CanonicalPriceObservation,
    ObservationTimelineBatch,
    ObservationTimelineEntry,
    RawMarketObservation,
)
from topicpilot_api.previous_close_authority import valid_close
from topicpilot_api.provider_preflight import (
    PROVIDER_AUTHORITY_BY_MARKET,
    PROVIDER_VERSION_BY_MARKET,
    load_g2_preflight_context,
)
from topicpilot_api.trading_status_authority import read_effective_trading_status_authority

POLICY = "official-comparator-only.v1"


class ComparatorError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ComparatorPoint:
    instrument_id: UUID
    code: str
    market: str
    bar: HistoricalBar
    receipt: Mapping[str, Any]
    retrieved_at: datetime

    def payload(self) -> dict[str, Any]:
        # Retrieval time is stored on rows, not in content identity. A replay
        # of unchanged provider bytes must reuse the same point and hash.
        return {
            **{
                key: None if getattr(self.bar, key) is None else str(getattr(self.bar, key))
                for key in ("open", "high", "low", "close")
            },
            "date": self.bar.trading_date.isoformat(),
            "volume": None,
            "source_symbol": self.code,
            "comparatorProvenance": {
                "policy": POLICY,
                "market": self.market,
                "instrumentCode": self.code,
                "instrumentId": str(self.instrument_id),
                "authority": PROVIDER_AUTHORITY_BY_MARKET[self.market],
                "adapterVersion": PROVIDER_VERSION_BY_MARKET[self.market],
                "targetDate": self.bar.trading_date.isoformat(),
                **dict(self.receipt),
            },
        }

    @property
    def identity(self) -> str:
        return stable_hash({"policy": POLICY, "payload": self.payload()})


@dataclass(frozen=True)
class ComparatorPlan:
    comparator_date: date
    target_date: date
    reference_version: str
    points: tuple[ComparatorPoint, ...]
    unavailable: tuple[dict[str, Any], ...]

    @property
    def key(self) -> str:
        return stable_hash(
            {
                "policy": POLICY,
                "comparator": self.comparator_date.isoformat(),
                "target": self.target_date.isoformat(),
                "reference": self.reference_version,
                "points": sorted(p.identity for p in self.points),
                "unavailable": self.unavailable,
            }
        )

    def summary(self) -> dict[str, Any]:
        return {
            "policy": POLICY,
            "comparatorDate": self.comparator_date.isoformat(),
            "targetDate": self.target_date.isoformat(),
            "idempotencyKey": self.key,
            "priceCount": len(self.points),
            "accountedCount": len(self.points) + len(self.unavailable),
            "markets": [
                {
                    "market": market,
                    "priceCount": sum(p.market == market for p in self.points),
                    "receipt": next(
                        (dict(p.receipt) for p in self.points if p.market == market), {}
                    ),
                }
                for market in ("TPE", "TWO")
            ],
            "legitimateUnavailable": list(self.unavailable),
            "forbiddenWrites": ["Home", "Topic", "Score", "Grade", "Lifecycle", "Run"],
        }


def validate_point(point: ComparatorPoint, comparator_date: date) -> None:
    expected_prefix = {
        "TPE": "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?",
        "TWO": "https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes?",
    }
    receipt = point.receipt
    if (
        point.market not in expected_prefix
        or not point.code
        or point.bar.trading_date != comparator_date
        or point.retrieved_at.tzinfo is None
        or not str(receipt.get("endpoint", "")).startswith(expected_prefix[point.market])
        or receipt.get("responseDate") != comparator_date.strftime("%Y%m%d")
        or str(receipt.get("rawStatus", "")).lower() != "ok"
        or receipt.get("classification") is not None
        or receipt.get("httpStatus") != 200
        or not isinstance(receipt.get("payloadSize"), int)
        or isinstance(receipt.get("payloadSize"), bool)
        or receipt["payloadSize"] <= 0
        or len(str(receipt.get("payloadHash", ""))) != 64
        or any(c not in "0123456789abcdef" for c in str(receipt.get("payloadHash", "")))
    ):
        raise ComparatorError("COMPARATOR_PROVENANCE_INVALID")
    # Preserve the existing accepted PRICE OHLC contract, never synthesize
    # missing OHLC just to publish an accepted comparator.
    if not all(valid_close(getattr(point.bar, key)) for key in ("open", "high", "low", "close")):
        raise ComparatorError("COMPARATOR_PRICE_NOT_ACCEPTED")
    if point.bar.low > min(point.bar.open, point.bar.high, point.bar.close) or point.bar.high < max(
        point.bar.open, point.bar.low, point.bar.close
    ):
        raise ComparatorError("COMPARATOR_OHLC_INVALID")


def prepare_comparator(
    session: Session,
    *,
    comparator_date: date,
    target_date: date,
    reference_version: str,
    transport: Callable[[str, float], bytes] | None = None,
) -> ComparatorPlan:
    context = load_g2_preflight_context(
        session, target_date=target_date, reference_version=reference_version
    )
    prior_context = load_g2_preflight_context(
        session, target_date=comparator_date, reference_version=reference_version
    )
    if (
        not context.context_ready
        or not prior_context.context_ready
        or context.previous_session != comparator_date
    ):
        raise ComparatorError("COMPARATOR_NOT_EXACT_PRIOR_SESSION")
    expected = {m.market_code: m.instrument_ids for m in prior_context.markets}
    ids = [UUID(m.instrument_ids[code]) for m in context.markets for code in m.instrument_codes]
    statuses = {
        str(row["instrumentId"]): row
        for row in read_effective_trading_status_authority(
            session, comparator_date, expected_instrument_ids=ids
        )
    }
    registry = build_historical_provider_registry(
        start_date=comparator_date,
        end_date=comparator_date,
        exchange_transport=transport,
        market_batch=True,
        readiness_max_attempts=1,
        readiness_max_total_wait_seconds=0,
    )
    points, unavailable = [], []
    for market in context.markets:
        registration = registry.for_market(market.market_code)[0]
        if (
            registration.code != PROVIDER_AUTHORITY_BY_MARKET[market.market_code]
            or registration.adapter.adapter_version
            != PROVIDER_VERSION_BY_MARKET[market.market_code]
        ):
            raise ComparatorError("COMPARATOR_PROVIDER_AUTHORITY_MISMATCH")
        retrieved, bars = registration.adapter.fetch_market_day()
        receipt = dict(registration.adapter.response_evidence)
        for code in market.instrument_codes:
            identity = market.instrument_ids[code]
            if expected[market.market_code].get(code) != identity:
                raise ComparatorError("COMPARATOR_INSTRUMENT_DATE_MISMATCH")
            status = statuses.get(identity, {})
            if status.get("isLegitimateUnavailable") and not status.get("blocksPublication", True):
                if valid_close(getattr(bars.get(code), "close", None)):
                    raise ComparatorError("COMPARATOR_STATUS_PRICE_CONFLICT")
                unavailable.append(
                    {
                        key: str(status[key])
                        if isinstance(status.get(key), (UUID, date))
                        else status.get(key)
                        for key in (
                            "instrumentId",
                            "market",
                            "symbol",
                            "resolvedStatus",
                            "authoritySource",
                            "reasonCode",
                            "sourceReference",
                            "effectiveFrom",
                            "effectiveTo",
                            "isLegitimateUnavailable",
                            "blocksPublication",
                        )
                    }
                )
                continue
            bar = bars.get(code)
            if bar is None:
                raise ComparatorError("COMPARATOR_TARGET_MISSING")
            point = ComparatorPoint(
                UUID(identity), code, market.market_code, bar, receipt, retrieved
            )
            validate_point(point, comparator_date)
            points.append(point)
    return ComparatorPlan(
        comparator_date, target_date, reference_version, tuple(points), tuple(unavailable)
    )


class _ComparatorMapper:
    def __call__(self, envelope, reference, policy):
        result = HistoricalDailyBarNormalizer()(envelope, reference, policy)
        prices = tuple(c for c in result.candidates if c.family_code == "PRICE")
        if result.failures or len(prices) != 1 or prices[0].quality_state != "ACCEPTED":
            raise ComparatorError("COMPARATOR_NORMALIZATION_REJECTED")
        return NormalizationResult(prices)


def persist_comparator(session: Session, plan: ComparatorPlan) -> dict[str, Any]:
    """Flush only. All markets validated first; caller commits atomically."""
    if not plan.points or len({p.instrument_id for p in plan.points}) != len(plan.points):
        raise ComparatorError("COMPARATOR_PLAN_INVALID")
    for point in plan.points:
        validate_point(point, plan.comparator_date)
        instrument, _market = _load_instrument(session, point.code, point.market)
        if instrument.id != point.instrument_id:
            raise ComparatorError("COMPARATOR_INSTRUMENT_IDENTITY_MISMATCH")
    if session.get_bind().dialect.name == "postgresql":
        session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key)::bigint)"),
            {"key": f"{POLICY}:{plan.comparator_date}:{plan.reference_version}"},
        )
    policy = MappingPolicy(mapping_policy_version=HISTORICAL_MAPPING_POLICY_VERSION)
    registry = NormalizerRegistry()
    sources, batches = {}, {}
    for market in sorted({p.market for p in plan.points}):
        source = _get_or_create_source(
            session,
            HistoricalSourceRegistration(
                PROVIDER_AUTHORITY_BY_MARKET[market], PROVIDER_VERSION_BY_MARKET[market]
            ),
        )
        sources[market] = source
        registry.register(
            NormalizerKey(
                source.source_code,
                source.adapter_version,
                policy.normalization_contract_version,
                policy.mapping_policy_version,
            ),
            _ComparatorMapper(),
        )
        batch = session.scalar(
            select(ObservationTimelineBatch).where(
                ObservationTimelineBatch.source_id == source.id,
                ObservationTimelineBatch.request_key == plan.key,
            )
        )
        if batch is None:
            anchor = datetime.combine(plan.comparator_date, time.min, tzinfo=UTC)
            batch = ObservationTimelineBatch(
                source_id=source.id,
                request_key=plan.key,
                requested_from=anchor,
                requested_to=anchor,
                status="OPEN",
                coverage_status="UNKNOWN",
                metadata_payload=plan.summary(),
            )
            session.add(batch)
            session.flush()
        elif batch.status != "COMPLETED":
            raise ComparatorError("COMPARATOR_BATCH_NOT_TERMINAL")
        batches[market] = batch
    runtime = NormalizationRuntime(session, registry)
    created = reused = 0
    for point in plan.points:
        source = sources[point.market]
        observed = datetime.combine(plan.comparator_date, time.min, tzinfo=ZoneInfo("Asia/Taipei"))
        raw = session.scalar(
            select(RawMarketObservation).where(
                RawMarketObservation.source_id == source.id,
                RawMarketObservation.content_hash == point.identity,
            )
        )
        if raw is None:
            # Latest active timeline is the predecessor, never an arbitrary
            # nearby trading date. The normalizer preserves supersession.
            prior = session.scalar(
                select(ObservationTimelineEntry)
                .where(
                    ObservationTimelineEntry.source_id == source.id,
                    ObservationTimelineEntry.instrument_id == point.instrument_id,
                    ObservationTimelineEntry.observed_at == observed,
                    ObservationTimelineEntry.entry_status == "ACTIVE",
                )
                .order_by(
                    ObservationTimelineEntry.retrieved_at.desc(), ObservationTimelineEntry.id.desc()
                )
                .limit(1)
            )
            raw = RawMarketObservation(
                source_id=source.id,
                instrument_id=point.instrument_id,
                upstream_observation_id=f"{point.code}:{plan.comparator_date}",
                source_instrument_identifier=point.code,
                observed_at=observed,
                retrieved_at=point.retrieved_at,
                payload=point.payload(),
                content_hash=point.identity,
                quality_status="CAPTURED",
                ingestion_correlation_id=plan.key,
                supersedes_id=prior.raw_observation_id if prior else None,
            )
            session.add(raw)
            session.flush()
            entry = ObservationTimelineEntry(
                source_id=source.id,
                instrument_id=point.instrument_id,
                raw_observation_id=raw.id,
                batch_id=batches[point.market].id,
                observed_at=observed,
                received_at=point.retrieved_at,
                retrieved_at=point.retrieved_at,
                ordering_key=plan.comparator_date.isoformat(),
                payload=raw.payload,
                content_hash=stable_hash({"raw": point.identity, "payload": raw.payload}),
                supersedes_id=prior.id if prior else None,
                entry_status="ACTIVE",
            )
            session.add(entry)
            session.flush()
            if prior:
                prior.entry_status = "SUPERSEDED"
        else:
            if raw.instrument_id != point.instrument_id or raw.payload != point.payload():
                raise ComparatorError("COMPARATOR_RAW_IDENTITY_CONFLICT")
            entry = session.scalar(
                select(ObservationTimelineEntry).where(
                    ObservationTimelineEntry.raw_observation_id == raw.id
                )
            )
            if entry is None or entry.entry_status != "ACTIVE":
                raise ComparatorError("COMPARATOR_STALE_OR_BROKEN_LINEAGE")
        result = runtime.normalize_timeline_entry(entry.id, policy, plan.reference_version)
        created += sum(p.created for p in result.persisted)
        reused += sum(not p.created for p in result.persisted)
    for batch in batches.values():
        batch.status, batch.coverage_status = "COMPLETED", "COMPLETE"
        batch.completed_at = batch.completed_at or datetime.now(UTC)
    session.flush()
    return {**plan.summary(), "status": "PERSISTED", "created": created, "reused": reused}


def read_comparator(session: Session, plan: ComparatorPlan) -> dict[str, Any]:
    """Assert stored PRICE lineage/receipt/count; never infer from a payload probe."""
    rows = session.execute(
        select(
            CanonicalObservation,
            CanonicalPriceObservation,
            RawMarketObservation,
            ObservationTimelineEntry,
        )
        .join(
            CanonicalPriceObservation,
            CanonicalPriceObservation.canonical_observation_id == CanonicalObservation.id,
        )
        .join(
            RawMarketObservation, RawMarketObservation.id == CanonicalObservation.raw_observation_id
        )
        .join(
            ObservationTimelineEntry,
            ObservationTimelineEntry.id == CanonicalObservation.timeline_entry_id,
        )
        .where(
            RawMarketObservation.content_hash.in_([p.identity for p in plan.points]),
            CanonicalObservation.family_code == "PRICE",
            CanonicalObservation.quality_state == "ACCEPTED",
        )
    ).all()
    by_id = {str(co.instrument_id): (co, price, raw, entry) for co, price, raw, entry in rows}
    if len(rows) != len(plan.points) or len(by_id) != len(plan.points):
        raise ComparatorError("COMPARATOR_READBACK_COVERAGE_FAILED")
    evidence = []
    for point in plan.points:
        co, price, raw, entry = by_id[str(point.instrument_id)]
        if (
            price.close != point.bar.close
            or raw.payload != point.payload()
            or co.reference_data_version != plan.reference_version
            or co.source_id != raw.source_id
            or co.instrument_id != raw.instrument_id
            or entry.entry_status != "ACTIVE"
            or not co.idempotency_key
        ):
            raise ComparatorError("COMPARATOR_READBACK_LINEAGE_FAILED")
        evidence.append(
            {
                "instrumentId": str(point.instrument_id),
                "code": point.code,
                "market": point.market,
                "canonicalId": str(co.id),
                "rawId": str(raw.id),
                "timelineId": str(entry.id),
                "supersedesId": str(co.supersedes_id) if co.supersedes_id else None,
                "idempotencyKey": co.idempotency_key,
                "retrievedAt": co.retrieved_at.isoformat(),
                "provenance": raw.payload["comparatorProvenance"],
            }
        )
    return {**plan.summary(), "status": "PASS", "lineage": evidence}
