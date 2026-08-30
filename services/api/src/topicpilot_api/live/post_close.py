"""Official daily-data post-close runner for the full V2 instrument universe."""

from __future__ import annotations

import time
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from datetime import time as clock_time
from typing import Any
from urllib.request import Request, urlopen

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from topicpilot_api.daily_market import DailyMarketReconciliation, reconcile_daily_market
from topicpilot_api.home_v2_publication import materialize_home_v2
from topicpilot_api.market_data.aggregate_contract import fetch_official_market_aggregates
from topicpilot_api.market_data.index_contract import fetch_official_market_indexes
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

    def _find_existing_run(self, run_date: date) -> LiveCollectorRun | None:
        """Find the latest POST_CLOSE run for the local market date.

        The run table predates an explicit run-date column, so the existing
        started-at timestamp is used as the compatibility key. New rows also
        carry ``runDate`` in metadata for operator visibility.
        """

        local_start = datetime.combine(
            run_date,
            clock_time.min,
            tzinfo=self.session_clock.timezone,
        ).astimezone(UTC)
        local_end = local_start + timedelta(days=1)
        return self.session.scalar(
            select(LiveCollectorRun)
            .where(
                LiveCollectorRun.run_type == "POST_CLOSE",
                LiveCollectorRun.started_at >= local_start,
                LiveCollectorRun.started_at < local_end,
            )
            .order_by(LiveCollectorRun.started_at.desc())
            .limit(1)
        )

    def _completed_attempt_summary(
        self,
        run_id: Any,
        expected_instrument_ids: Collection[Any],
    ) -> dict[str, Any] | None:
        """Return terminal per-instrument counts only for a complete run."""

        attempts = self.session.scalars(
            select(LiveCollectorAttempt)
            .where(LiveCollectorAttempt.run_id == run_id)
            .order_by(
                LiveCollectorAttempt.instrument_id,
                LiveCollectorAttempt.updated_at,
                LiveCollectorAttempt.id,
            )
        ).all()
        latest_by_instrument: dict[Any, LiveCollectorAttempt] = {}
        for attempt in attempts:
            if attempt.instrument_id is None:
                return None
            latest_by_instrument[attempt.instrument_id] = attempt

        expected = set(expected_instrument_ids)
        if set(latest_by_instrument) != expected:
            return None
        latest = tuple(latest_by_instrument.values())
        if any(
            attempt.status not in {"SUCCESS", "FAILED", "TIMEOUT", "SKIPPED"}
            for attempt in latest
        ):
            return None
        failure_codes = tuple(
            sorted(
                {
                    attempt.error_code
                    for attempt in latest
                    if attempt.error_code
                }
            )
        )
        return {
            "success_count": sum(attempt.status == "SUCCESS" for attempt in latest),
            "failure_count": sum(
                attempt.status in {"FAILED", "TIMEOUT"} for attempt in latest
            ),
            "skipped_count": sum(attempt.status == "SKIPPED" for attempt in latest),
            "retry_count": sum(attempt.retry_count for attempt in latest),
            "failure_codes": failure_codes,
        }

    @staticmethod
    def _is_recent_run(run: LiveCollectorRun, now: datetime, *, stale_after: int) -> bool:
        heartbeat = run.heartbeat_at
        if heartbeat.tzinfo is None:
            heartbeat = heartbeat.replace(tzinfo=UTC)
        return now - heartbeat.astimezone(UTC) <= timedelta(seconds=stale_after)

    def _existing_result(
        self,
        run: LiveCollectorRun,
        *,
        run_date: date,
    ) -> PostCloseRunResult:
        metadata = dict(run.metadata_payload or {})
        snapshot = metadata.get("topicSnapshot")
        if not isinstance(snapshot, dict):
            snapshot = {}
        codes = metadata.get("failureCodes")
        if not isinstance(codes, list):
            codes = [run.failure_code] if run.failure_code else []
        return PostCloseRunResult(
            str(run.id),
            run.status,
            run.requested_count,
            run.success_count,
            run.failure_count,
            int(metadata.get("skippedCount", 0) or 0),
            run.retry_count,
            int(metadata.get("providerPointCount", 0) or 0),
            0,
            tuple(str(code) for code in codes),
            int(snapshot.get("topicCount", 0) or 0),
            str(snapshot.get("status", "ALREADY_COMPLETED")),
            str(snapshot.get("snapshotDate", run_date.isoformat())),
        )

    def _create_run(
        self,
        requested_count: int,
        started_at: datetime,
        *,
        run_date: date,
    ) -> LiveCollectorRun:
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
                "runDate": run_date.isoformat(),
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
        existing_run = self._find_existing_run(local_date)
        if existing_run is not None:
            if existing_run.status in {"SUCCESS", "PARTIAL", "FAILED", "MARKET_CLOSED"}:
                return self._existing_result(existing_run, run_date=local_date)
            attempt_summary = self._completed_attempt_summary(
                existing_run.id,
                eligible_instrument_ids,
            )
            if attempt_summary is not None and not self._is_recent_run(
                existing_run,
                now,
                stale_after=max(
                    self.config.poll_interval_seconds * 2,
                    int(self.config.provider_timeout_seconds)
                    * max(1, self.config.history_batch_size)
                    * (self.config.history_max_retries + 1),
                ),
            ):
                return self._finalize_collected_run(
                    run_id=existing_run.id,
                    local_date=local_date,
                    eligible_instrument_ids=eligible_instrument_ids,
                    success_count=attempt_summary["success_count"],
                    failure_count=attempt_summary["failure_count"],
                    skipped_count=attempt_summary["skipped_count"],
                    retry_count=attempt_summary["retry_count"],
                    point_count=int(
                        (existing_run.metadata_payload or {}).get("providerPointCount", 0)
                        or 0
                    ),
                    failure_codes=attempt_summary["failure_codes"],
                )
            raise PostClosePreconditionError("POST_CLOSE_RUN_IN_PROGRESS")

        run = self._create_run(
            len(instruments),
            now,
            run_date=local_date,
        )
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
                            in {
                                "SUSPENDED",
                                "NO_TRADE",
                                "EXCHANGE_CONFIRMED_NO_DATA",
                                "DELISTED",
                                "TERMINATED",
                            }
                            and result.priced_count == 0
                            else None
                        )
                        error_message = result.status_reason
                    else:
                        skipped_count += 1
                        attempt_status = "SKIPPED"
                        error_code = "MISSING_MARKET_DATA"
                        error_message = result.status_reason or (
                            "official provider returned no priced bar and no "
                            "lifecycle-authorized no-trade evidence"
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
            self._heartbeat(run_id, self._now())

        return self._finalize_collected_run(
            run_id=run_id,
            local_date=local_date,
            eligible_instrument_ids=eligible_instrument_ids,
            success_count=success_count,
            failure_count=failure_count,
            skipped_count=skipped_count,
            retry_count=retry_count,
            point_count=point_count,
            failure_codes=tuple(sorted(set(failure_codes))),
        )

    def _heartbeat(self, run_id: Any, now: datetime) -> None:
        run = self.session.get(LiveCollectorRun, run_id)
        if run is None or run.status != "RUNNING":
            return
        run.heartbeat_at = now
        run.updated_at = now
        self.session.commit()

    def _refresh_tracking_universe_with_retry(
        self,
        *,
        now: datetime,
        eligible_instrument_ids: Collection[Any],
    ) -> int:
        repository = LiveRepository(self.session, self.config)
        try:
            return repository.refresh_tracking_universe(
                now=now,
                eligible_instrument_ids=eligible_instrument_ids,
            )
        except DBAPIError:
            # A provider-sized post-close run can outlive a database backend
            # connection. Roll back the invalid transaction and let
            # pool_pre_ping acquire a fresh connection for the bounded retry.
            self.session.rollback()
            return repository.refresh_tracking_universe(
                now=now,
                eligible_instrument_ids=eligible_instrument_ids,
            )

    def _finish_with_retry(self, run_id: Any, **values: Any) -> None:
        try:
            self._finish(run_id, **values)
        except DBAPIError:
            self.session.rollback()
            self._finish(run_id, **values)

    def _mark_finalization_failure(self, run_id: Any, exc: Exception) -> None:
        """Best-effort terminal audit write after an unhandled finalization error."""

        try:
            self.session.rollback()
            bind = self.session.get_bind()
        except Exception:
            return

        try:
            with Session(bind=bind, expire_on_commit=False) as recovery_session:
                run = recovery_session.get(LiveCollectorRun, run_id)
                if run is None or run.status != "RUNNING":
                    return
                now = self._now()
                run.status = "FAILED"
                run.freshness_state = "PARTIAL"
                run.provider_status = "ERROR"
                run.failure_code = "POST_CLOSE_FINALIZATION_FAILED"
                run.failure_message = f"{type(exc).__name__}: {str(exc)[:500]}"
                metadata = dict(run.metadata_payload or {})
                metadata["finalizationError"] = {
                    "status": "FAILED",
                    "errorCode": "POST_CLOSE_FINALIZATION_FAILED",
                    "exceptionType": type(exc).__name__,
                }
                run.metadata_payload = metadata
                run.completed_at = now
                run.heartbeat_at = now
                run.updated_at = now
                recovery_session.commit()
        except Exception:
            # If the database itself is unavailable, preserve the original
            # exception. The next process can recover from persisted attempts.
            return

    def _finalize_collected_run(
        self,
        *,
        run_id: Any,
        local_date: date,
        eligible_instrument_ids: Collection[Any],
        success_count: int,
        failure_count: int,
        skipped_count: int,
        retry_count: int,
        point_count: int,
        failure_codes: Collection[str],
    ) -> PostCloseRunResult:
        try:
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

            tracking_count = self._refresh_tracking_universe_with_retry(
                now=self._now(),
                eligible_instrument_ids=eligible_instrument_ids,
            )
            snapshot_result = (
                self._run_snapshot(
                    local_date,
                    eligible_instrument_ids=eligible_instrument_ids,
                    source_run_id=str(run_id),
                    market_index_facts=fetch_official_market_indexes(
                        target_date=local_date,
                        retrieved_at=self._now(),
                        as_of=self._now(),
                        transport=_official_transport,
                    ),
                    market_aggregate_facts=fetch_official_market_aggregates(
                        target_date=local_date,
                        retrieved_at=self._now(),
                        as_of=self._now(),
                        transport=_official_transport,
                    ),
                )
                if reconciliation.downstream_ready
                else {
                    "snapshotDate": local_date.isoformat(),
                    "topicCount": 0,
                    "status": "BLOCKED_DAILY_MARKET_NOT_READY",
                }
            )
            final_failure_codes = tuple(sorted(set(failure_codes))) or reconciliation.reason_codes
            if not final_failure_codes and skipped_count:
                final_failure_codes = ("NO_TRADING_DAY_DATA",)
            self._finish_with_retry(
                run_id,
                status=status,
                success_count=success_count,
                failure_count=failure_count,
                skipped_count=skipped_count,
                retry_count=retry_count,
                point_count=point_count,
                failure_codes=final_failure_codes,
                snapshot_result=snapshot_result,
                reconciliation=reconciliation,
                now=self._now(),
            )
        except Exception as exc:
            self._mark_finalization_failure(run_id, exc)
            raise

        return PostCloseRunResult(
            str(run_id),
            status,
            len(eligible_instrument_ids),
            success_count,
            failure_count,
            skipped_count,
            retry_count,
            point_count,
            tracking_count,
            final_failure_codes,
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
        source_run_id: str | None = None,
        market_index_facts: Collection[Any] = (),
        market_aggregate_facts: Collection[Any] = (),
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
                except Exception as exc:
                    # Formal PIT materialization remains additive shadow work.
                    # A missing authority/migration or transient failure must
                    # not discard the canonical research snapshot already
                    # committed above.
                    self.session.rollback()
                    result["formalTopicDailyState"] = {
                        "status": "FORMAL_STATE_UNAVAILABLE",
                        "error": type(exc).__name__,
                    }
                if result["formalTopicDailyState"]["status"] == "SUCCESS":
                    try:
                        result["lifecycle"] = TopicLifecycleEngine(self.session).run_once(
                            evaluation_date=snapshot_date,
                        )
                    except Exception as exc:
                        # Lifecycle V1.1 is a parallel acceptance boundary.
                        # Its failure is recorded without making the core
                        # Home publication depend on an unaccepted policy
                        # engine.
                        self.session.rollback()
                        result["lifecycle"] = {
                            "status": "LIFECYCLE_UNAVAILABLE",
                            "error": type(exc).__name__,
                        }
                else:
                    result["lifecycle"] = {"status": "WAITING_FOR_FORMAL_SNAPSHOT"}
                try:
                    result["homePublication"] = materialize_home_v2(
                        self.session,
                        trading_date=snapshot_date,
                        source_run_id=source_run_id,
                        market_index_facts=tuple(market_index_facts),
                        market_aggregate_facts=tuple(market_aggregate_facts),
                    )
                except Exception as exc:
                    # Home publication has its own typed gate.  A Home
                    # persistence failure must not rewrite a successfully
                    # materialized formal topic state as unavailable.
                    self.session.rollback()
                    result["homePublication"] = {
                        "status": "HOME_PUBLICATION_UNAVAILABLE",
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
