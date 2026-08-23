"""Official daily-data post-close runner for the full V2 instrument universe."""

from __future__ import annotations

import time
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from datetime import time as clock_time
from typing import Any
from urllib.request import Request, urlopen

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from topicpilot_api.daily_market import DailyMarketReconciliation, reconcile_daily_market
from topicpilot_api.market_data.ingestion import HistoricalSourceRegistration, ingest_historical
from topicpilot_api.market_data.rate_limit import RateLimitedTransport
from topicpilot_api.market_data.registry import build_historical_provider_registry
from topicpilot_api.normalizer import HISTORICAL_MAPPING_POLICY_VERSION, MappingPolicy
from topicpilot_api.normalizer.contracts import stable_hash
from topicpilot_api.orm import Instrument, LiveCollectorAttempt, LiveCollectorRun, Market
from topicpilot_api.provider_preflight import load_g2_preflight_context
from topicpilot_api.topic_daily_state import materialize_bounded_formal_dates
from topicpilot_api.topic_lifecycle_engine import TopicLifecycleEngine
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


class PostClosePreconditionError(RuntimeError):
    """Raised before any post-close write when reference eligibility is unsafe."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def expected_post_close_universe(
    session: Session,
    *,
    run_date: date,
    reference_version: str,
) -> Mapping[str, tuple[str, ...]]:
    """Load the existing fail-closed date-effective reference universe."""

    try:
        context = load_g2_preflight_context(
            session,
            target_date=run_date,
            reference_version=reference_version,
        )
    except Exception as exc:
        raise PostClosePreconditionError("REFERENCE_PRECONDITION_FAILED") from exc

    if context.reference_result.get("referenceLoadStatus") != "READY":
        raise PostClosePreconditionError("REFERENCE_CONTEXT_NOT_READY")
    if context.eligibility_error is not None:
        raise PostClosePreconditionError("LIFECYCLE_CONTEXT_INVALID")
    if tuple(sorted(market.market_code for market in context.markets)) != ("TPE", "TWO"):
        raise PostClosePreconditionError("CANONICAL_MARKET_CONTEXT_INCOMPLETE")
    if not all(market.context_ready for market in context.markets):
        raise PostClosePreconditionError("MARKET_CONTEXT_NOT_READY")
    return {
        market.market_code: tuple(market.instrument_codes) for market in context.markets
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

    def _instruments(
        self, expected_by_market: Mapping[str, Collection[str]]
    ) -> list[tuple[Instrument, Market]]:
        predicates = [
            and_(Market.code == market_code, Instrument.instrument_code.in_(tuple(codes)))
            for market_code, codes in expected_by_market.items()
            if codes
        ]
        if not predicates:
            raise PostClosePreconditionError("EMPTY_DATE_EFFECTIVE_UNIVERSE")
        return list(
            self.session.execute(
                select(Instrument, Market)
                .join(Market, Market.id == Instrument.market_id)
                .where(
                    Instrument.is_active.is_(True),
                    Market.is_active.is_(True),
                    Market.code.in_(("TPE", "TWO")),
                    Instrument.instrument_type == "EQUITY",
                    or_(*predicates),
                )
                .order_by(Market.code, Instrument.instrument_code)
            ).all()
        )

    @staticmethod
    def _validate_instruments(
        instruments: Collection[tuple[Instrument, Market]],
        expected_by_market: Mapping[str, Collection[str]],
    ) -> None:
        expected = {
            (market_code, instrument_code)
            for market_code, codes in expected_by_market.items()
            for instrument_code in codes
        }
        actual = {(market.code, instrument.instrument_code) for instrument, market in instruments}
        if len(instruments) != len(actual) or actual != expected:
            raise PostClosePreconditionError("DATE_EFFECTIVE_UNIVERSE_MISMATCH")

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
        expected_by_market = expected_post_close_universe(
            self.session,
            run_date=local_date,
            reference_version=self.config.reference_data_version,
        )
        instruments = self._instruments(expected_by_market)
        self._validate_instruments(instruments, expected_by_market)
        eligible_instrument_ids = tuple(instrument.id for instrument, _market in instruments)
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
            reconciliation = reconcile_daily_market(
                self.session,
                local_date,
                market_closed=True,
                expected_instrument_ids=eligible_instrument_ids,
            )
            snapshot_result = {
                "snapshotDate": local_date.isoformat(),
                "topicCount": 0,
                "status": "NOT_RUN_MARKET_CLOSED",
            }
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
                reconciliation=reconciliation,
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
            start_date=local_date,
            end_date=local_date,
            exchange_transport=transport,
            market_batch=True,
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
                retries_before = transport.retry_count
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
                    if result.covered_count:
                        success_count += 1
                        attempt_status = "SUCCESS"
                        error_code = (
                            "APPROVED_NO_TRADE"
                            if result.instrument_status
                            in {"SUSPENDED", "NO_TRADE", "EXCHANGE_CONFIRMED_NO_DATA"}
                            and result.priced_count == 0
                            else None
                        )
                        error_message = result.status_reason
                    else:
                        skipped_count += 1
                        attempt_status = "SKIPPED"
                        error_code = "UNEXPLAINED_MISSING_DATA"
                        error_message = result.status_reason or (
                            "official provider returned no priced or approved no-trade evidence"
                        )
                except Exception as exc:
                    self.session.rollback()
                    failure_count += 1
                    attempt_status = "FAILED"
                    error_code = getattr(exc, "code", type(exc).__name__)
                    error_message = str(exc)
                    failure_codes.append(error_code)
                completed = self._now()
                item_retry_count = transport.retry_count - retries_before
                retry_count += item_retry_count
                self.session.add(
                    LiveCollectorAttempt(
                        run_id=run_id,
                        instrument_id=instrument.id,
                        instrument_code=instrument.instrument_code,
                        market_code=market.code,
                        attempt_number=item_retry_count + 1,
                        status=attempt_status,
                        started_at=item_started,
                        retrieved_at=completed if attempt_status == "SUCCESS" else None,
                        updated_at=completed,
                        observed_at=None,
                        latency_ms=max(0, int((completed - item_started).total_seconds() * 1000)),
                        retry_count=item_retry_count,
                        provider_status=(
                            result.instrument_status
                            if attempt_status != "FAILED"
                            else "ERROR"
                        ),
                        freshness_state="FRESH" if attempt_status == "SUCCESS" else "UNKNOWN",
                        error_code=error_code,
                        error_message=error_message,
                    )
                )
                self.session.commit()

        reconciliation = reconcile_daily_market(
            self.session,
            local_date,
            expected_instrument_ids=eligible_instrument_ids,
        )
        if failure_count or skipped_count:
            status = "PARTIAL" if success_count else "FAILED"
        else:
            status = "SUCCESS"
        if status == "SUCCESS" and not reconciliation.downstream_ready:
            status = "PARTIAL"
        tracking_count = LiveRepository(self.session, self.config).refresh_tracking_universe(
            now=self._now(), eligible_instrument_ids=eligible_instrument_ids
        )
        snapshot_result = (
            self._run_snapshot(
                local_date,
                eligible_instrument_ids=eligible_instrument_ids,
            )
            if reconciliation.downstream_ready
            else {
                "snapshotDate": local_date.isoformat(),
                "topicCount": 0,
                "status": "BLOCKED_DAILY_MARKET_NOT_READY",
            }
        )
        self._finish(
            run_id,
            status=status,
            success_count=success_count,
            failure_count=failure_count,
            skipped_count=skipped_count,
            retry_count=retry_count,
            point_count=point_count,
            failure_codes=tuple(sorted(set(failure_codes)))
            or reconciliation.reason_codes
            or (("NO_TRADING_DAY_DATA",) if skipped_count else ()),
            snapshot_result=snapshot_result,
            reconciliation=reconciliation,
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
            or reconciliation.reason_codes
            or (("NO_TRADING_DAY_DATA",) if skipped_count else ()),
            snapshot_result.get("topicCount", 0),
            snapshot_result.get("status", "FAILED"),
            local_date.isoformat(),
        )

    def _run_snapshot(
        self,
        snapshot_date: date,
        *,
        market_closed: bool = False,
        eligible_instrument_ids: Collection[Any] | None = None,
    ) -> dict[str, Any]:
        try:
            result = TopicSnapshotEngine(self.session).run_once(
                snapshot_date=snapshot_date,
                market_closed=market_closed,
                eligible_instrument_ids=eligible_instrument_ids,
            )
            if result.get("status") == "SUCCESS" and not market_closed:
                try:
                    formal_state = materialize_bounded_formal_dates(
                        self.session,
                        dates=(snapshot_date,),
                    )
                    result["formalTopicDailyState"] = {
                        "status": "SUCCESS",
                        "rowsBefore": formal_state["rowsBefore"],
                        "rowsAfter": formal_state["rowsAfter"],
                        "writes": formal_state["writes"],
                        "preBoundaryBackfill": formal_state["preBoundaryBackfill"],
                    }
                    result["lifecycle"] = TopicLifecycleEngine(self.session).run_once(
                        evaluation_date=snapshot_date,
                    )
                except Exception as exc:
                    # Formal PIT materialization and lifecycle remain additive
                    # shadow work. A missing authority/migration or transient
                    # failure must not discard the canonical research snapshot
                    # already committed above.
                    self.session.rollback()
                    result["formalTopicDailyState"] = {
                        "status": "FORMAL_STATE_UNAVAILABLE",
                        "error": type(exc).__name__,
                    }
                    result["lifecycle"] = {
                        "status": "WAITING_FOR_FORMAL_SNAPSHOT",
                        "error": type(exc).__name__,
                    }
            elif market_closed:
                result["lifecycle"] = {"status": "MARKET_CLOSED"}
            return result
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
        reconciliation: DailyMarketReconciliation | None = None,
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
                "dailyMarketReconciliation": (
                    reconciliation.to_dict() if reconciliation else {"status": "NOT_RUN"}
                ),
                "downstreamReady": bool(
                    reconciliation and reconciliation.downstream_ready
                ),
                "topicSnapshot": snapshot_result or {"status": "NOT_RUN"},
            }
        )
        run.metadata_payload = metadata
        run.completed_at = now
        run.heartbeat_at = now
        run.updated_at = now
        self.session.commit()


__all__ = [
    "PostClosePreconditionError",
    "PostCloseRunResult",
    "PostCloseUpdater",
    "expected_post_close_universe",
]
