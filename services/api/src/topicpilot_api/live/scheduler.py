"""Portable scheduler loop and one-shot execution modes."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone

from .collector import LiveCollector
from .config import LiveRuntimeConfig
from .logging import log_event
from .session import MarketSessionClock, SessionState


class LiveScheduler:
    """Run the same collector from a service, cron, Task Scheduler, or worker."""

    def __init__(
        self,
        collector: LiveCollector,
        config: LiveRuntimeConfig,
        *,
        clock: Callable[[], datetime] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        logger: logging.Logger | None = None,
        worker: object | None = None,
        post_close_runner: Callable[[], object] | None = None,
    ):
        self.collector = collector
        self.config = config
        self.clock = clock or (lambda: datetime.now(timezone.utc))  # noqa: UP017
        self.sleep = sleep
        self.logger = logger or logging.getLogger("topicpilot.live.scheduler")
        self.worker = worker
        self.post_close_runner = post_close_runner
        self.session_clock = MarketSessionClock(
            config.timezone_name,
            config.session_open,
            config.session_close,
            config.closed_dates,
        )

    def decide(self, now: datetime | None = None) -> str:
        status = self.session_clock.status(now or self.clock())
        if status.state == SessionState.OPEN:
            return "INTRADAY"
        if status.reason in {"WEEKEND", "CONFIGURED_CLOSED_DATE"}:
            return "WAIT"
        local = status.local_time
        if local.time() >= self.session_clock.close_time and local.weekday() < 5:
            return "POST_CLOSE"
        return "WAIT"

    def run_once(self, mode: str = "AUTO", *, enforce_session: bool = True):
        normalized = mode.upper()
        if normalized == "AUTO":
            normalized = self.decide()
        if normalized == "WAIT":
            log_event(self.logger, "scheduler_wait", reason="MARKET_NOT_OPEN_OR_POST_CLOSE_WINDOW")
            return None
        if normalized not in {"INTRADAY", "POST_CLOSE"}:
            raise ValueError("mode must be AUTO, INTRADAY, or POST_CLOSE")
        if normalized == "POST_CLOSE" and self.post_close_runner is not None:
            return self.post_close_runner()
        return self.collector.run_once(
            run_type=normalized,
            enforce_session=enforce_session and normalized == "INTRADAY",
        )

    def run_forever(self, stop_event: threading.Event | None = None) -> None:
        event = stop_event or threading.Event()
        completed_post_close_date = None
        tracking_refresh_date = None
        worker_started = False
        try:
            while not event.is_set():
                mode = self.decide()
                if mode == "POST_CLOSE":
                    if worker_started:
                        self.worker.stop()
                        worker_started = False
                    local_date = self.session_clock.status(self.clock()).local_time.date()
                    if completed_post_close_date != local_date:
                        try:
                            self.run_once("POST_CLOSE", enforce_session=False)
                        except Exception as exc:
                            error_code = getattr(exc, "code", type(exc).__name__)
                            log_event(
                                self.logger,
                                "post_close_run_failed",
                                errorCode=error_code,
                            )
                            # Keep the worker alive after a run-level failure.
                            # A restarted process must inspect the existing
                            # date-keyed run before it can start another one.
                        else:
                            self._refresh_tracking()
                            completed_post_close_date = local_date
                elif mode == "INTRADAY":
                    if not worker_started and self.worker is not None:
                        self.worker.start()
                        worker_started = True
                    local_date = self.session_clock.status(self.clock()).local_time.date()
                    if tracking_refresh_date != local_date:
                        self._refresh_tracking()
                        tracking_refresh_date = local_date
                    self.run_once("INTRADAY")
                else:
                    if worker_started:
                        self.worker.stop()
                        worker_started = False
                    log_event(self.logger, "scheduler_wait", reason="MARKET_CLOSED")
                event.wait(self.config.poll_interval_seconds)
        finally:
            if worker_started and self.worker is not None:
                self.worker.stop()

    def _refresh_tracking(self) -> None:
        refresh = getattr(self.collector.repository, "refresh_tracking_universe", None)
        if not callable(refresh):
            return
        count = refresh(now=self.clock())
        session = getattr(self.collector.repository, "session", None)
        commit = getattr(session, "commit", None)
        if callable(commit):
            commit()
        log_event(self.logger, "tracking_universe_refreshed", instrumentCount=count)


__all__ = ["LiveScheduler"]
