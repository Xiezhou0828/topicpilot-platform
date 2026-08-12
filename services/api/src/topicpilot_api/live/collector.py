"""Retryable, failure-isolating live collector."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from datetime import date, datetime, timezone

from .config import LiveRuntimeConfig
from .contracts import CollectorRunResult, IntradayProvider, LiveProviderError, TrackingInstrument
from .logging import log_event
from .persistence import LivePersistenceError, LiveRepository
from .session import MarketSessionClock, SessionState


class LiveCollector:
    def __init__(
        self,
        repository: LiveRepository,
        provider: IntradayProvider,
        config: LiveRuntimeConfig,
        *,
        clock: Callable[[], datetime] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        logger: logging.Logger | None = None,
        session_clock: MarketSessionClock | None = None,
    ):
        self.repository = repository
        self.provider = provider
        self.config = config
        self.clock = clock or (lambda: datetime.now(timezone.utc))  # noqa: UP017
        self.sleep = sleep
        self.logger = logger or logging.getLogger("topicpilot.live.collector")
        self.session_clock = session_clock or MarketSessionClock(
            config.timezone_name,
            config.session_open,
            config.session_close,
            config.closed_dates,
        )

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None:
            raise ValueError("live collector clock must be timezone-aware")
        return value.astimezone(timezone.utc)  # noqa: UP017

    def _provider_identity(self) -> tuple[str, str]:
        return (
            getattr(self.provider, "source_code", self.config.provider_code),
            getattr(self.provider, "adapter_version", "provider-router.v1"),
        )

    def _provider_health(self) -> list[dict[str, object]]:
        snapshot = getattr(self.provider, "health_snapshot", None)
        return list(snapshot()) if callable(snapshot) else []

    def run_once(
        self,
        *,
        run_type: str = "INTRADAY",
        instruments: list[TrackingInstrument] | None = None,
        session_date: date | None = None,
        enforce_session: bool = True,
    ) -> CollectorRunResult:
        now = self._now()
        session_status = self.session_clock.status(now)
        if run_type == "INTRADAY" and enforce_session and session_status.state != SessionState.OPEN:
            provider_code, adapter_version = self._provider_identity()
            run_id, _ = self.repository.start_run(
                run_type=run_type,
                provider_code=provider_code,
                adapter_version=adapter_version,
                requested_count=0,
                now=now,
            )
            self.repository.finish_run(
                run_id,
                status="MARKET_CLOSED",
                success_count=0,
                failure_count=0,
                retry_count=0,
                latency_ms=0,
                freshness_state="NOT_APPLICABLE",
                provider_status="NOT_CALLED",
                failure_code="MARKET_CLOSED",
                failure_message=session_status.reason,
                now=now,
            )
            log_event(
                self.logger,
                "live_cycle_skipped",
                runId=run_id,
                reason=session_status.reason,
            )
            return CollectorRunResult(
                run_id,
                run_type,
                "MARKET_CLOSED",
                0,
                0,
                0,
                0,
                0,
                "NOT_APPLICABLE",
                "NOT_CALLED",
                ("MARKET_CLOSED",),
            )

        selected = instruments or self.repository.list_tracking(run_type)
        provider_code, adapter_version = self._provider_identity()
        run_id, batch_id = self.repository.start_run(
            run_type=run_type,
            provider_code=provider_code,
            adapter_version=adapter_version,
            requested_count=len(selected),
            now=now,
        )
        if not selected:
            self.repository.finish_run(
                run_id,
                status="WAITING_LIVE_VALIDATION",
                success_count=0,
                failure_count=0,
                retry_count=0,
                latency_ms=0,
                freshness_state="NOT_APPLICABLE",
                provider_status="NOT_CALLED",
                failure_code="EMPTY_UNIVERSE",
                failure_message="live tracking universe is empty; no provider was called",
                metadata_payload={
                    "providerHealth": self._provider_health(),
                    "contract": "EMPTY_UNIVERSE_NOT_SUCCESS",
                },
                now=now,
            )
            return CollectorRunResult(
                run_id,
                run_type,
                "WAITING_LIVE_VALIDATION",
                0,
                0,
                0,
                0,
                0,
                "NOT_APPLICABLE",
                "NOT_CALLED",
                ("EMPTY_UNIVERSE",),
            )
        success = failure = retries = 0
        failure_codes: list[str] = []
        started = time.monotonic()
        for item in selected:
            self.repository.heartbeat(run_id, self._now())
            item_started = self._now()
            completed = False
            for attempt in range(1, self.config.max_retries + 2):
                try:
                    target_date = (
                        session_date or self._now().astimezone(self.session_clock.timezone).date()
                    )
                    routed = getattr(self.provider, "fetch_with_evidence", None)
                    evidence = None
                    if callable(routed):
                        routed_result = routed(
                            item.instrument_code,
                            item.market_code,
                            session_date=target_date,
                        )
                        result = routed_result.resolution.result
                        evidence = routed_result.resolution.evidence
                    else:
                        result = self.provider.fetch_intraday(
                            item.instrument_code,
                            item.market_code,
                            session_date=target_date,
                        )
                    latest = result.latest
                    if latest is None:
                        raise LiveProviderError(
                            "EMPTY_INTRADAY_DATA", "provider returned no latest bar"
                        )
                    families = self.repository.persist_bar(
                        run_id=run_id,
                        batch_id=batch_id,
                        result=result,
                        bar=latest,
                        retrieved_at=result.retrieved_at,
                        canonical_evidence=evidence,
                    )
                    retrieved = result.retrieved_at.astimezone(timezone.utc)  # noqa: UP017
                    updated = self._now()
                    latency_ms = int((updated - item_started).total_seconds() * 1000)
                    self.repository.record_attempt(
                        run_id=run_id,
                        instrument_id=item.instrument_id,
                        instrument_code=item.instrument_code,
                        market_code=item.market_code,
                        attempt_number=attempt,
                        status="SUCCESS",
                        started_at=item_started,
                        retrieved_at=retrieved,
                        updated_at=updated,
                        observed_at=latest.observed_at,
                        latency_ms=latency_ms,
                        retry_count=attempt - 1,
                        provider_status="AVAILABLE",
                        freshness_state="FRESH",
                        payload_hash=None,
                    )
                    success += 1
                    retries += attempt - 1
                    completed = True
                    log_event(
                        self.logger,
                        "live_symbol_success",
                        runId=run_id,
                        instrument=item.instrument_code,
                        market=item.market_code,
                        attempt=attempt,
                        families=families,
                        observedAt=latest.observed_at,
                        retrievedAt=retrieved,
                        updatedAt=updated,
                    )
                    break
                except Exception as exc:
                    rollback = getattr(self.repository, "rollback", None)
                    if callable(rollback):
                        rollback()
                    code = getattr(exc, "code", "LIVE_RUNTIME_ERROR")
                    retryable = getattr(exc, "retryable", isinstance(exc, TimeoutError))
                    message = (
                        str(exc)
                        if isinstance(exc, (LiveProviderError, LivePersistenceError, TimeoutError))
                        else "live runtime operation failed"
                    )
                    retries += 1 if attempt > 1 else 0
                    if attempt <= self.config.max_retries and retryable:
                        self.repository.record_attempt(
                            run_id=run_id,
                            instrument_id=item.instrument_id,
                            instrument_code=item.instrument_code,
                            market_code=item.market_code,
                            attempt_number=attempt,
                            status="RETRYING",
                            started_at=item_started,
                            retrieved_at=None,
                            updated_at=self._now(),
                            observed_at=None,
                            latency_ms=None,
                            retry_count=attempt,
                            provider_status="RETRYING",
                            freshness_state="UNKNOWN",
                            error_code=code,
                            error_message=message,
                        )
                        backoff = self.config.retry_backoff_seconds * (2 ** (attempt - 1))
                        jitter = random.uniform(0, self.config.reconnect_jitter_seconds)
                        self.sleep(backoff + jitter)
                        continue
                    failure += 1
                    failure_codes.append(code)
                    self.repository.record_attempt(
                        run_id=run_id,
                        instrument_id=item.instrument_id,
                        instrument_code=item.instrument_code,
                        market_code=item.market_code,
                        attempt_number=attempt,
                        status="TIMEOUT" if code.endswith("TIMEOUT") else "FAILED",
                        started_at=item_started,
                        retrieved_at=None,
                        updated_at=self._now(),
                        observed_at=None,
                        latency_ms=None,
                        retry_count=attempt - 1,
                        provider_status="ERROR",
                        freshness_state="STALE",
                        error_code=code,
                        error_message=message,
                    )
                    log_event(
                        self.logger,
                        "live_symbol_failure",
                        runId=run_id,
                        instrument=item.instrument_code,
                        market=item.market_code,
                        attempt=attempt,
                        errorCode=code,
                    )
                    break
            if not completed:
                self.repository.heartbeat(run_id, self._now())

        elapsed = int((time.monotonic() - started) * 1000)
        status = "SUCCESS" if failure == 0 else "PARTIAL" if success else "FAILED"
        freshness = "FRESH" if success and failure == 0 else "PARTIAL" if success else "STALE"
        provider_status = "AVAILABLE" if success else "ERROR"
        self.repository.finish_run(
            run_id,
            status=status,
            success_count=success,
            failure_count=failure,
            retry_count=retries,
            latency_ms=elapsed,
            freshness_state=freshness,
            provider_status=provider_status,
            failure_code=failure_codes[0] if failure_codes else None,
            failure_message=";".join(sorted(set(failure_codes))) if failure_codes else None,
            metadata_payload={"providerHealth": self._provider_health()},
            now=self._now(),
        )
        return CollectorRunResult(
            run_id,
            run_type,
            status,
            len(selected),
            success,
            failure,
            retries,
            elapsed,
            freshness,
            provider_status,
            tuple(sorted(set(failure_codes))),
        )


__all__ = ["LiveCollector"]
