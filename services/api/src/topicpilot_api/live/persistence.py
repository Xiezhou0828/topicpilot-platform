"""PostgreSQL persistence and read queries for live operations."""

from __future__ import annotations

from collections.abc import Collection
from datetime import UTC, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import bindparam, func, select, text
from sqlalchemy.orm import Session

from topicpilot_api.normalizer import (
    MappingPolicy,
    NormalizationRuntime,
    NormalizerKey,
    NormalizerRegistry,
)
from topicpilot_api.normalizer.contracts import stable_hash
from topicpilot_api.orm import (
    Instrument,
    LiveCollectorAttempt,
    LiveCollectorRun,
    LiveTrackingUniverse,
    Market,
    MarketDataSource,
    ObservationTimelineBatch,
    ObservationTimelineEntry,
    RawMarketObservation,
)

from .config import LiveRuntimeConfig
from .contracts import IntradayBar, IntradayFetchResult, TrackingInstrument
from .normalizer import LiveIntradayNormalizer


def _now() -> datetime:
    return datetime.now(timezone.utc)  # noqa: UP017


def _classification_freshness(
    observed_at: datetime | None, now: datetime, *, threshold_seconds: int = 900
) -> str:
    if observed_at is None:
        return "UNKNOWN"
    delay = max(0.0, (now - observed_at.astimezone(UTC)).total_seconds())
    return "FRESH" if delay <= threshold_seconds else "STALE"


def _decimal_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.normalize(), "f")


class LivePersistenceError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


class LiveRepository:
    """Persistence boundary owned by the live collector, not the provider."""

    def __init__(self, session: Session, config: LiveRuntimeConfig):
        self.session = session
        self.config = config

    def refresh_tracking_universe(
        self,
        *,
        now: datetime | None = None,
        eligible_instrument_ids: Collection[Any] | None = None,
    ) -> int:
        """Classify the supplied date-effective universe from accepted prices."""

        period = self.config.moving_average_period
        eligible_filter = ""
        params: dict[str, Any] = {"period": period}
        if eligible_instrument_ids is not None:
            eligible_filter = "\n                AND i.id IN :eligible_instrument_ids"
            params["eligible_instrument_ids"] = tuple(eligible_instrument_ids)
        query = text(
            f"""
                WITH candidate_prices AS (
                    SELECT
                        co.id,
                        co.instrument_id,
                        co.source_id,
                        co.observed_at,
                        cp.close,
                        mds.source_code,
                        row_number() OVER (
                            PARTITION BY co.instrument_id, co.observed_at
                            ORDER BY
                                mds.source_rank,
                                co.created_at DESC,
                                co.id DESC
                        ) AS same_observation_rank
                    FROM topicpilot.canonical_observations co
                    JOIN topicpilot.canonical_price_observations cp
                      ON cp.canonical_observation_id = co.id
                    JOIN topicpilot.market_data_sources mds
                      ON mds.id = co.source_id
                    WHERE co.family_code = 'PRICE'
                      AND co.quality_state = 'ACCEPTED'
                      AND cp.close IS NOT NULL
                      AND cp.price_context->>'source_semantics' = 'DAILY_BAR'
                      AND NOT EXISTS (
                          SELECT 1
                          FROM topicpilot.canonical_observations successor
                          WHERE successor.supersedes_id = co.id
                            AND successor.family_code = 'PRICE'
                            AND successor.quality_state = 'ACCEPTED'
                      )
                ), current_prices AS (
                    SELECT
                        instrument_id,
                        id,
                        source_id,
                        observed_at,
                        close,
                        row_number() OVER (
                            PARTITION BY co.instrument_id ORDER BY co.observed_at DESC, co.id DESC
                        ) AS row_number
                    FROM candidate_prices co
                    WHERE same_observation_rank = 1
                )
                SELECT
                    i.id AS instrument_id,
                    i.instrument_code,
                    m.code AS market_code,
                    latest.close AS latest_close,
                    latest.observed_at AS latest_observed_at,
                    latest.source_id,
                    avg(windowed.close) AS moving_average,
                    count(windowed.close)::integer AS observation_count
                FROM topicpilot.instruments i
                JOIN topicpilot.markets m ON m.id = i.market_id
                LEFT JOIN current_prices latest
                  ON latest.instrument_id = i.id AND latest.row_number = 1
                LEFT JOIN current_prices windowed
                  ON windowed.instrument_id = i.id AND windowed.row_number <= :period
                WHERE i.is_active = true AND m.is_active = true
                {eligible_filter}
                GROUP BY i.id, i.instrument_code, m.code,
                         latest.close, latest.observed_at, latest.source_id
                ORDER BY m.code, i.instrument_code
                """
        )
        if eligible_instrument_ids is not None:
            query = query.bindparams(bindparam("eligible_instrument_ids", expanding=True))
        rows = self.session.execute(query, params).mappings().all()
        current = {row["instrument_id"]: row for row in rows}
        existing = {
            item.instrument_id: item
            for item in self.session.scalars(select(LiveTrackingUniverse)).all()
        }
        for instrument_id, row in current.items():
            count = int(row["observation_count"] or 0)
            latest = row["latest_close"]
            moving_average = row["moving_average"]
            if count < period or latest is None or moving_average is None:
                ma_state, update_mode = "UNKNOWN", "UNKNOWN"
                reason = f"INSUFFICIENT_ACCEPTED_PRICE_HISTORY:{count}/{period}"
            elif latest >= moving_average:
                ma_state, update_mode = "ABOVE", "INTRADAY"
                reason = "LATEST_CLOSE_AT_OR_ABOVE_60MA"
            else:
                ma_state, update_mode = "BELOW", "POST_CLOSE"
                reason = "LATEST_CLOSE_BELOW_60MA"
            item = existing.get(instrument_id)
            values = {
                "market_code": row["market_code"],
                "instrument_code": row["instrument_code"],
                "moving_average_period": period,
                "moving_average_state": ma_state,
                "update_mode": update_mode,
                "latest_close": latest,
                "moving_average": moving_average,
                "observation_count": count,
                "reference_observed_at": row["latest_observed_at"],
                "as_of_date": row["latest_observed_at"].astimezone(
                    ZoneInfo(self.config.timezone_name)
                ).date()
                if row["latest_observed_at"]
                else None,
                "classification_reason": reason,
                "source_id": row["source_id"],
                "updated_at": now or _now(),
            }
            if item is None:
                self.session.add(LiveTrackingUniverse(instrument_id=instrument_id, **values))
            else:
                for key, value in values.items():
                    setattr(item, key, value)
        self.session.flush()
        return len(current)

    def list_tracking(self, mode: str) -> list[TrackingInstrument]:
        if mode == "POST_CLOSE":
            rows = self.session.execute(
                select(Instrument, Market)
                .join(Market, Market.id == Instrument.market_id)
                .where(Instrument.is_active.is_(True), Market.is_active.is_(True))
                .order_by(Market.code, Instrument.instrument_code)
            ).all()
            return [
                TrackingInstrument(
                    instrument_id=instrument.id,
                    instrument_code=instrument.instrument_code,
                    market_code=market.code,
                    update_mode="POST_CLOSE",
                    moving_average_state="UNKNOWN",
                    latest_close=None,
                    moving_average=None,
                )
                for instrument, market in rows
            ]
        rows = self.session.scalars(
            select(LiveTrackingUniverse)
            .where(LiveTrackingUniverse.update_mode == "INTRADAY")
            .order_by(LiveTrackingUniverse.market_code, LiveTrackingUniverse.instrument_code)
        ).all()
        return [
            TrackingInstrument(
                item.instrument_id,
                item.instrument_code,
                item.market_code,
                item.update_mode,
                item.moving_average_state,
                item.latest_close,
                item.moving_average,
            )
            for item in rows
        ]

    def _source(
        self, provider_code: str, adapter_version: str, *, source_rank: int | None = None
    ) -> MarketDataSource:
        source = self.session.scalar(
            select(MarketDataSource).where(
                MarketDataSource.source_code == provider_code,
                MarketDataSource.adapter_version == adapter_version,
            )
        )
        if source is None:
            source = MarketDataSource(
                source_code=provider_code,
                source_category=self.config.source_category,
                adapter_version=adapter_version,
                observation_semantics="INTRADAY_BAR",
                adjustment_policy="UNKNOWN",
                calendar_policy=self.config.calendar_code,
                licensing_classification="PRIVATE_RUNTIME",
                source_rank=source_rank if source_rank is not None else 100,
                status="REGISTERED",
            )
            self.session.add(source)
            self.session.flush()
        elif source.status not in ("REGISTERED", "ACTIVE"):
            raise LivePersistenceError("SOURCE_NOT_ACTIVE", provider_code)
        elif source_rank is not None:
            source.source_rank = source_rank
        return source

    def start_run(
        self,
        *,
        run_type: str,
        provider_code: str,
        adapter_version: str,
        requested_count: int,
        now: datetime,
    ) -> tuple[UUID, UUID]:
        source = self._source(provider_code, adapter_version)
        config_hash = stable_hash(self.config.as_hash_dict())
        run = LiveCollectorRun(
            run_type=run_type,
            status="RUNNING",
            provider_code=provider_code,
            adapter_version=adapter_version,
            config_hash=config_hash,
            started_at=now,
            heartbeat_at=now,
            requested_count=requested_count,
            freshness_state="UNKNOWN",
            provider_status="CONNECTING",
            metadata_payload={"interval": self.config.interval, "sourceId": str(source.id)},
        )
        self.session.add(run)
        self.session.flush()
        batch = ObservationTimelineBatch(
            source_id=source.id,
            requested_instrument_id=None,
            requested_from=None,
            requested_to=None,
            request_key=f"live:{run.id}",
            status="OPEN",
            coverage_status="UNKNOWN",
            metadata_payload={"runId": str(run.id), "runType": run_type},
        )
        self.session.add(batch)
        self.session.commit()
        return run.id, batch.id

    def heartbeat(self, run_id: UUID, now: datetime) -> None:
        run = self.session.get(LiveCollectorRun, run_id)
        if run is not None:
            run.heartbeat_at = now
            run.updated_at = now
            self.session.commit()

    def rollback(self) -> None:
        """Clear a failed symbol transaction before the next retry."""

        self.session.rollback()

    def record_attempt(self, **values: Any) -> UUID:
        attempt = LiveCollectorAttempt(**values)
        self.session.add(attempt)
        self.session.commit()
        return attempt.id

    def persist_bar(
        self,
        *,
        run_id: UUID,
        batch_id: UUID,
        result: IntradayFetchResult,
        bar: IntradayBar,
        retrieved_at: datetime,
        canonical_evidence: dict[str, Any] | None = None,
    ) -> tuple[str, ...]:
        instrument = self.session.scalar(
            select(Instrument)
            .join(Market, Market.id == Instrument.market_id)
            .where(
                Instrument.instrument_code == result.instrument_code,
                Market.code == result.market_code,
                Instrument.is_active.is_(True),
                Market.is_active.is_(True),
            )
        )
        if instrument is None:
            raise LivePersistenceError(
                "INSTRUMENT_NOT_FOUND", f"{result.market_code}/{result.instrument_code}"
            )
        evidence = dict(canonical_evidence or {})
        evidence.setdefault("provider", result.source_code)
        evidence.setdefault("observed_at", bar.observed_at.isoformat())
        evidence.setdefault("retrieved_at", retrieved_at.isoformat())
        evidence.setdefault("canonical_reason", "SINGLE_PROVIDER_ADAPTER")
        source = self._source(
            result.source_code,
            result.adapter_version,
            source_rank=int(evidence.get("source_rank", 100)),
        )
        payload = {
            **dict(bar.source_payload),
            "last": _decimal_text(bar.last),
            "retrieved_at": retrieved_at.isoformat(),
            "source_evidence": evidence,
        }
        raw_hash = stable_hash(
            {
                "source": result.source_code,
                "adapter": result.adapter_version,
                "instrument": result.instrument_code,
                "market": result.market_code,
                "observedAt": bar.observed_at,
                "payload": payload,
            }
        )
        raw = self.session.scalar(
            select(RawMarketObservation).where(
                RawMarketObservation.source_id == source.id,
                RawMarketObservation.content_hash == raw_hash,
            )
        )
        prior = self.session.scalar(
            select(ObservationTimelineEntry)
            .where(
                ObservationTimelineEntry.instrument_id == instrument.id,
                ObservationTimelineEntry.source_id == source.id,
                ObservationTimelineEntry.observed_at == bar.observed_at,
                ObservationTimelineEntry.entry_status == "ACTIVE",
            )
            .order_by(ObservationTimelineEntry.id.desc())
        )
        if raw is None:
            raw = RawMarketObservation(
                source_id=source.id,
                instrument_id=instrument.id,
                upstream_observation_id=f"{result.source_symbol}:{bar.observed_at.isoformat()}",
                source_instrument_identifier=result.source_symbol,
                observed_at=bar.observed_at,
                retrieved_at=retrieved_at,
                payload=payload,
                content_hash=raw_hash,
                quality_status="CAPTURED",
                ingestion_correlation_id=str(run_id),
                supersedes_id=prior.raw_observation_id if prior else None,
            )
            self.session.add(raw)
            self.session.flush()
        entry = self.session.scalar(
            select(ObservationTimelineEntry).where(
                ObservationTimelineEntry.raw_observation_id == raw.id
            )
        )
        if entry is None:
            entry = ObservationTimelineEntry(
                instrument_id=instrument.id,
                source_id=source.id,
                raw_observation_id=raw.id,
                batch_id=batch_id,
                observed_at=bar.observed_at,
                received_at=retrieved_at,
                retrieved_at=retrieved_at,
                ordering_key=bar.observed_at.isoformat(),
                payload=payload,
                content_hash=stable_hash({"raw": raw_hash, "payload": payload}),
                supersedes_id=prior.id if prior and prior.raw_observation_id != raw.id else None,
                entry_status="ACTIVE",
            )
            self.session.add(entry)
            self.session.flush()
        else:
            entry.retrieved_at = retrieved_at
            entry.received_at = retrieved_at

        registry = NormalizerRegistry()
        registry.register(
            NormalizerKey(
                result.source_code,
                result.adapter_version,
                self.config.normalization_contract_version,
                self.config.mapping_policy_version,
            ),
            LiveIntradayNormalizer(),
        )
        policy = MappingPolicy(
            normalization_contract_version=self.config.normalization_contract_version,
            mapping_policy_version=self.config.mapping_policy_version,
            session_code=self.config.session_code,
            calendar_code=self.config.calendar_code,
        )
        normalized = NormalizationRuntime(self.session, registry).normalize_timeline_entry(
            entry.id, policy, self.config.reference_data_version
        )
        self.session.commit()
        return tuple(item.family_code for item in normalized.persisted)

    def finish_run(
        self,
        run_id: UUID,
        *,
        status: str,
        success_count: int,
        failure_count: int,
        retry_count: int,
        latency_ms: int | None,
        freshness_state: str,
        provider_status: str,
        failure_code: str | None = None,
        failure_message: str | None = None,
        metadata_payload: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> None:
        run = self.session.get(LiveCollectorRun, run_id)
        if run is None:
            return
        run.status = status
        run.success_count = success_count
        run.failure_count = failure_count
        run.retry_count = retry_count
        run.latency_ms = latency_ms
        run.freshness_state = freshness_state
        run.provider_status = provider_status
        run.failure_code = failure_code
        run.failure_message = failure_message
        if metadata_payload is not None:
            run.metadata_payload = metadata_payload
        run.completed_at = now or _now()
        run.heartbeat_at = run.completed_at
        run.updated_at = run.completed_at
        self.session.commit()


def read_live_status(session: Session) -> dict[str, Any]:
    run = session.scalar(
        select(LiveCollectorRun).order_by(LiveCollectorRun.started_at.desc()).limit(1)
    )
    if run is None:
        return {
            "status": "NO_RUN",
            "lastRun": None,
            "providerStatus": "UNKNOWN",
            "freshnessState": "UNKNOWN",
            "heartbeatAt": None,
            "successCount": 0,
            "failureCount": 0,
            "retryCount": 0,
            "skippedCount": 0,
            "universeCounts": read_live_universe_counts(session),
            "providerHealth": [],
        }
    metadata = run.metadata_payload or {}
    return {
        "status": run.status,
        "lastRun": {
            "id": str(run.id),
            "type": run.run_type,
            "startedAt": run.started_at,
            "completedAt": run.completed_at,
            "latencyMs": run.latency_ms,
            "requestedCount": run.requested_count,
        },
        "providerStatus": run.provider_status,
        "freshnessState": run.freshness_state,
        "heartbeatAt": run.heartbeat_at,
        "successCount": run.success_count,
        "failureCount": run.failure_count,
        "retryCount": run.retry_count,
        "skippedCount": int(metadata.get("skippedCount", 0)),
        "universeCounts": read_live_universe_counts(session),
        "failureCode": run.failure_code,
        "failureMessage": run.failure_message,
        "providerHealth": metadata.get("providerHealth", []),
    }


def read_live_universe_counts(session: Session) -> dict[str, int]:
    """Return operational counts without requiring clients to page tracking rows."""

    rows = session.execute(
        select(LiveTrackingUniverse.update_mode, func.count()).group_by(
            LiveTrackingUniverse.update_mode
        )
    ).all()
    counts = {"INTRADAY": 0, "POST_CLOSE": 0, "UNKNOWN": 0, "TOTAL": 0}
    for update_mode, count in rows:
        key = update_mode if update_mode in counts else "UNKNOWN"
        counts[key] += int(count)
        counts["TOTAL"] += int(count)
    return counts


def read_live_tracking(
    session: Session, limit: int, offset: int, *, freshness_window_seconds: int = 900
) -> tuple[list[dict[str, Any]], int]:
    total = session.scalar(select(func.count()).select_from(LiveTrackingUniverse)) or 0
    now = _now()
    rows = session.scalars(
        select(LiveTrackingUniverse)
        .order_by(LiveTrackingUniverse.market_code, LiveTrackingUniverse.instrument_code)
        .offset(offset)
        .limit(limit)
    ).all()
    return [
        {
            "instrumentCode": row.instrument_code,
            "market": row.market_code,
            "updateMode": row.update_mode,
            "movingAverageState": row.moving_average_state,
            "movingAveragePeriod": row.moving_average_period,
            "latestClose": row.latest_close,
            "movingAverage": row.moving_average,
            "observationCount": row.observation_count,
            "observedAt": row.reference_observed_at,
            "updatedAt": row.updated_at,
            # This endpoint reports classification/reference freshness.  It
            # must not be interpreted as the live provider observation state
            # returned by read_live_status.
            "freshnessState": _classification_freshness(
                row.reference_observed_at, now, threshold_seconds=freshness_window_seconds
            ),
            "reason": row.classification_reason,
        }
        for row in rows
    ], int(total)


__all__ = [
    "LivePersistenceError",
    "LiveRepository",
    "read_live_status",
    "read_live_tracking",
    "read_live_universe_counts",
]
