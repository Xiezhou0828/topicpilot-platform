"""Official daily-data post-close runner for the full V2 instrument universe."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from datetime import time as clock_time
from typing import Any
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from topicpilot_api.market_data.ingestion import HistoricalSourceRegistration, ingest_historical
from topicpilot_api.market_data.rate_limit import RateLimitedTransport
from topicpilot_api.market_data.registry import build_historical_provider_registry
from topicpilot_api.normalizer import HISTORICAL_MAPPING_POLICY_VERSION, MappingPolicy
from topicpilot_api.normalizer.contracts import stable_hash
from topicpilot_api.orm import Instrument, LiveCollectorAttempt, LiveCollectorRun, Market
from topicpilot_api.topic_snapshot_engine import TopicSnapshotEngine

from .config import LiveRuntimeConfig
from .persistence import LiveRepository
from .session import MarketSessionClock


def _official_transport(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": "TopicPilot-V2/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


@dataclass(frozen=True)
class PostCloseRunResult:
    run_id: str
    status: str
    requested_count: int
    success_count: int
    failure_count: int
    skipped_count: int
    retry_count: int
    provider_point_count: int
    tracking_count: int
    failure_codes: tuple[str, ...]
    snapshot_count: int = 0
    snapshot_status: str = "NOT_RUN"
    snapshot_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "runId": self.run_id,
            "runType": "POST_CLOSE",
            "status": self.status,
            "requestedCount": self.requested_count,
            "successCount": self.success_count,
            "failureCount": self.failure_count,
            "skippedCount": self.skipped_count,
            "retryCount": self.retry_count,
            "providerPointCount": self.provider_point_count,
            "trackingCount": self.tracking_count,
            "failureCodes": list(self.failure_codes),
            "snapshotCount": self.snapshot_count,
            "snapshotStatus": self.snapshot_status,
            "snapshotDate": self.snapshot_date,
        }


class PostCloseUpdater:
    """Run official TWSE/TPEx daily updates without fabricating closed data."""

    def __init__(
        self,
        session: Session,
        config: LiveRuntimeConfig,
        *,
        clock: Callable[[], datetime] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.session = session
        self.config = config
        self.clock = clock or (lambda: datetime.now(UTC))
        self.sleep = sleep
        self.session_clock = MarketSessionClock(
            config.timezone_name,
            config.session_open,
            config.session_close,
            config.closed_dates,
        )

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None:
            raise ValueError("post-close clock must be timezone-aware")
        return value.astimezone(UTC)

    def _instruments(self) -> list[tuple[Instrument, Market]]:
        return list(
            self.session.execute(
                select(Instrument, Market)
                .join(Market, Market.id == Instrument.market_id)
                .where(
                    Instrument.is_active.is_(True),
                    Market.is_active.is_(True),
                    Market.code.in_(("TPE", "TWO")),
                    Instrument.instrument_type == "EQUITY",
                )
                .order_by(Market.code, Instrument.instrument_code)
            ).all()
        )

    def _create_run(self, requested_count: int, started_at: datetime) -> LiveCollectorRun:
        run = LiveCollectorRun(
            run_type="POST_CLOSE",
            status="RUNNING",
            provider_code="OFFICIAL_DAILY_ROUTER",
            adapter_version="official-daily-router.v1",
            config_hash=stable_hash(
                {
                    "historyBatchSize": self.config.history_batch_size,
                    "historyRequestsPerMinute": self.config.history_requests_per_minute,
                    "historyMinRequestIntervalSeconds": (
                        str(self.config.history_min_request_interval_seconds)
                    ),
                    "historyMaxRetries": self.config.history_max_retries,
                    "historyRetryBackoffSeconds": str(self.config.history_retry_backoff_seconds),
                }
            ),
            started_at=started_at,
            heartbeat_at=started_at,
            requested_count=requested_count,
            freshness_state="UNKNOWN",
            provider_status="CONNECTING",
            metadata_payload={
                "runType": "POST_CLOSE",
                "batchSize": self.config.history_batch_size,
                "skippedCount": 0,
                "sourceProviders": {"TPE": "TWSE_OFFICIAL_DAILY", "TWO": "TPEX_OFFICIAL_DAILY"},
            },
        )
        self.session.add(run)
        self.session.flush()
        self.session.commit()
        return run

    def run_once(self, *, run_date: date | None = None) -> PostCloseRunResult:
        now = self._now()
        if run_date is None:
            local_date = now.astimezone(self.session_clock.timezone).date()
        else:
            local_date = run_date
        instruments = self._instruments()
        run = self._create_run(len(instruments), now)
        run_id = run.id
        failure_codes: list[str] = []
        success_count = failure_count = skipped_count = retry_count = point_count = 0

        session_status = self.session_clock.status(
            datetime.combine(local_date, clock_time(13, 30), tzinfo=self.session_clock.timezone)
        )
        if session_status.reason in {"WEEKEND", "CONFIGURED_CLOSED_DATE"}:
            skipped_count = len(instruments)
            status = "MARKET_CLOSED"
            snapshot_result = self._run_snapshot(local_date, market_closed=True)
            self._finish(
                run_id,
                status=status,
                success_count=0,
                failure_count=0,
                skipped_count=skipped_count,
                retry_count=0,
                point_count=0,
                failure_codes=("MARKET_CLOSED",),
                snapshot_result=snapshot_result,
                now=now,
            )
            return PostCloseRunResult(
                str(run_id),
                status,
                len(instruments),
                0,
                0,
                skipped_count,
                0,
                0,
                0,
                ("MARKET_CLOSED",),
                snapshot_result.get("topicCount", 0),
                snapshot_result.get("status", "FAILED"),
                local_date.isoformat(),
            )

        transport = RateLimitedTransport(
            _official_transport,
            requests_per_minute=self.config.history_requests_per_minute,
            min_interval_seconds=self.config.history_min_request_interval_seconds,
            max_retries=self.config.history_max_retries,
            retry_backoff_seconds=self.config.history_retry_backoff_seconds,
            sleep=self.sleep,
        )
        registry = build_historical_provider_registry(
            start_date=local_date, end_date=local_date, exchange_transport=transport
        )
        policy = MappingPolicy(
            mapping_policy_version=HISTORICAL_MAPPING_POLICY_VERSION,
            session_code=self.config.session_code,
            calendar_code=self.config.calendar_code,
        )

        for batch_start in range(0, len(instruments), self.config.history_batch_size):
            batch = instruments[batch_start : batch_start + self.config.history_batch_size]
            for instrument, market in batch:
                registration = registry.for_market(market.code)[0]
                item_started = self._now()
                attempt_status = "SUCCESS"
                error_code = None
                error_message = None
                try:
                    result = ingest_historical(
                        self.session,
                        registration.adapter,
                        [(instrument.instrument_code, market.code)],
                        reference_data_version=self.config.reference_data_version,
                        requested_from=local_date,
                        requested_to=local_date,
                        policy=policy,
                        registration=HistoricalSourceRegistration(
                            registration.code,
                            registration.adapter.adapter_version,
                            licensing_classification="OFFICIAL_PUBLIC",
                        ),
                    )
                    self.session.commit()
                    point_count += result.provider_point_count
                    if result.provider_point_count:
                        success_count += 1
                    else:
                        skipped_count += 1
                        attempt_status = "SKIPPED"
                        error_code = "NO_TRADING_DAY_DATA"
                        error_message = "official provider returned no bar for requested date"
                except Exception as exc:
                    self.session.rollback()
                    failure_count += 1
                    attempt_status = "FAILED"
                    error_code = getattr(exc, "code", type(exc).__name__)
                    error_message = str(exc)
                    failure_codes.append(error_code)
                completed = self._now()
                self.session.add(
                    LiveCollectorAttempt(
                        run_id=run_id,
                        instrument_id=instrument.id,
                        instrument_code=instrument.instrument_code,
                        market_code=market.code,
                        attempt_number=1,
                        status=attempt_status,
                        started_at=item_started,
                        retrieved_at=completed if attempt_status == "SUCCESS" else None,
                        updated_at=completed,
                        observed_at=None,
                        latency_ms=max(0, int((completed - item_started).total_seconds() * 1000)),
                        retry_count=0,
                        provider_status="AVAILABLE" if attempt_status != "FAILED" else "ERROR",
                        freshness_state="FRESH" if attempt_status == "SUCCESS" else "UNKNOWN",
                        error_code=error_code,
                        error_message=error_message,
                    )
                )
                self.session.commit()

        if failure_count:
            status = "PARTIAL" if success_count else "FAILED"
        elif skipped_count:
            status = "PARTIAL" if success_count else "MARKET_CLOSED"
        else:
            status = "SUCCESS"
        tracking_count = LiveRepository(self.session, self.config).refresh_tracking_universe(
            now=self._now()
        )
        snapshot_result = self._run_snapshot(local_date)
        self._finish(
            run_id,
            status=status,
            success_count=success_count,
            failure_count=failure_count,
            skipped_count=skipped_count,
            retry_count=retry_count,
            point_count=point_count,
            failure_codes=tuple(sorted(set(failure_codes)))
            or (("NO_TRADING_DAY_DATA",) if skipped_count else ()),
            snapshot_result=snapshot_result,
            now=self._now(),
        )
        return PostCloseRunResult(
            str(run_id),
            status,
            len(instruments),
            success_count,
            failure_count,
            skipped_count,
            retry_count,
            point_count,
            tracking_count,
            tuple(sorted(set(failure_codes)))
            or (("NO_TRADING_DAY_DATA",) if skipped_count else ()),
            snapshot_result.get("topicCount", 0),
            snapshot_result.get("status", "FAILED"),
            local_date.isoformat(),
        )

    def _run_snapshot(self, snapshot_date: date, *, market_closed: bool = False) -> dict[str, Any]:
        try:
            return TopicSnapshotEngine(self.session).run_once(
                snapshot_date=snapshot_date,
                market_closed=market_closed,
            )
        except Exception as exc:
            self.session.rollback()
            return {
                "snapshotDate": snapshot_date.isoformat(),
                "topicCount": 0,
                "status": "FAILED",
                "error": type(exc).__name__,
            }

    def _finish(
        self,
        run_id: Any,
        *,
        status: str,
        success_count: int,
        failure_count: int,
        skipped_count: int,
        retry_count: int,
        point_count: int,
        failure_codes: tuple[str, ...],
        snapshot_result: dict[str, Any] | None = None,
        now: datetime,
    ) -> None:
        run = self.session.get(LiveCollectorRun, run_id)
        if run is None:
            return
        run.status = status
        run.success_count = success_count
        run.failure_count = failure_count
        run.retry_count = retry_count
        run.latency_ms = max(0, int((now - run.started_at).total_seconds() * 1000))
        run.freshness_state = (
            "FRESH"
            if status == "SUCCESS"
            else "NOT_APPLICABLE"
            if status == "MARKET_CLOSED"
            else "PARTIAL"
        )
        run.provider_status = (
            "AVAILABLE"
            if status in {"SUCCESS", "PARTIAL"}
            else "NOT_CALLED"
            if status == "MARKET_CLOSED" and not failure_codes
            else "ERROR"
        )
        run.failure_code = failure_codes[0] if failure_codes else None
        run.failure_message = ";".join(failure_codes) if failure_codes else None
        metadata = dict(run.metadata_payload or {})
        metadata.update(
            {
                "skippedCount": skipped_count,
                "providerPointCount": point_count,
                "failureCodes": list(failure_codes),
                "topicSnapshot": snapshot_result or {"status": "NOT_RUN"},
            }
        )
        run.metadata_payload = metadata
        run.completed_at = now
        run.heartbeat_at = now
        run.updated_at = now
        self.session.commit()


__all__ = ["PostCloseRunResult", "PostCloseUpdater"]
