"""Calendar-aware bounded single-session daily forward automation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy.orm import Session

from topicpilot_api.provider_preflight import load_g2_preflight_context

from .config import LiveRuntimeConfig
from .post_close import PostCloseRunResult, PostCloseUpdater
from .receipt import (
    RECEIPT_COMPLETE,
    RECEIPT_CORRECTION_COMPLETE,
    RECEIPT_DEADLINE_EXCEEDED,
    RECEIPT_FAILED_CLOSED,
    RECEIPT_MARKET_CLOSED,
    RECEIPT_WAITING_FOR_DATA,
    append_operational_receipt,
    read_latest_receipt,
)


@dataclass(frozen=True)
class DailyForwardRunResult:
    """Outcome of one bounded calendar/session decision or execution."""

    status: str
    target_date: date | None
    next_session_date: date | None
    reason_codes: tuple[str, ...] = ()
    post_close: PostCloseRunResult | None = None
    replay: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "runType": "DAILY_FORWARD",
            "status": self.status,
            "targetDate": self.target_date.isoformat() if self.target_date else None,
            "nextSessionDate": (
                self.next_session_date.isoformat() if self.next_session_date else None
            ),
            "reasonCodes": list(self.reason_codes),
            "replay": self.replay,
            "postClose": self.post_close.to_dict() if self.post_close else None,
        }


class DailyForwardRunner:
    """Route one post-close session through the existing official chain."""

    def __init__(
        self,
        session: Session,
        config: LiveRuntimeConfig,
        *,
        clock: Callable[[], datetime] | None = None,
        updater: PostCloseUpdater | None = None,
        context_loader: Callable[..., Any] = load_g2_preflight_context,
    ) -> None:
        self.session = session
        self.config = config
        self.clock = clock or (lambda: datetime.now(UTC))
        self.updater = updater or PostCloseUpdater(session, config, clock=self.clock)
        self.context_loader = context_loader

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None:
            raise ValueError("daily forward clock must be timezone-aware")
        return value

    def _context(self, target_date: date) -> Any:
        return self.context_loader(
            self.session,
            target_date=target_date,
            reference_version=self.config.reference_data_version,
        )

    @staticmethod
    def _context_ready(context: Any) -> bool:
        return (
            context.reference_result.get("referenceLoadStatus") == "READY"
            and context.eligibility_error is None
            and len(context.markets) == 2
            and all(market.context_ready for market in context.markets)
        )

    def _next_session(self, target_date: date) -> date | None:
        for offset in range(1, 15):
            candidate = target_date + timedelta(days=offset)
            try:
                context = self._context(candidate)
            except Exception:
                return None
            if self._context_ready(context) and context.target_date_is_session:
                return candidate
        return None

    def _latest_receipt(self, target_date: date) -> Any | None:
        if self.session is None:
            return None
        return read_latest_receipt(self.session, target_date)

    def _terminal_receipt_result(
        self,
        *,
        target_date: date,
        next_session: date | None,
        replay: bool,
        fallback: PostCloseRunResult | None = None,
    ) -> DailyForwardRunResult | None:
        receipt = self._latest_receipt(target_date)
        if receipt is None:
            return None
        status = receipt.receipt_status
        mapped = {
            RECEIPT_COMPLETE: "SUCCESS",
            RECEIPT_CORRECTION_COMPLETE: "SUCCESS",
            RECEIPT_MARKET_CLOSED: "MARKET_CLOSED",
            RECEIPT_WAITING_FOR_DATA: "WAITING_FOR_DATA",
            RECEIPT_FAILED_CLOSED: "FAILED_CLOSED",
            RECEIPT_DEADLINE_EXCEEDED: "DEADLINE_EXCEEDED",
        }.get(status)
        if mapped is None:
            return None
        if mapped == "WAITING_FOR_DATA" and fallback is None:
            return None
        return DailyForwardRunResult(
            mapped,
            target_date,
            next_session,
            tuple(
                dict.fromkeys(
                    [
                        *(fallback.failure_codes if fallback is not None else ()),
                        *(
                            [receipt.reason_code]
                            if receipt.reason_code is not None
                            else []
                        ),
                    ]
                )
            ),
            post_close=fallback,
            replay=replay,
        )

    def _deadline_result(
        self,
        *,
        target_date: date,
        next_session: date | None,
        now: datetime,
    ) -> DailyForwardRunResult:
        if self.session is not None:
            append_operational_receipt(
                self.session,
                trading_date=target_date,
                config=self.config,
                execution_key=(
                    f"post-close-deadline:{self.config.reference_data_version}:"
                    f"{self.config.calendar_code}:{target_date.isoformat()}"
                ),
                receipt_status=RECEIPT_DEADLINE_EXCEEDED,
                reason_code="HARD_DEADLINE_EXCEEDED",
                now=now,
                calendar_decision={
                    "authority": "G2_REFERENCE_CALENDAR",
                    "calendarCode": self.config.calendar_code,
                    "referenceDataVersion": self.config.reference_data_version,
                    "targetDate": target_date.isoformat(),
                },
            )
        return DailyForwardRunResult(
            "DEADLINE_EXCEEDED",
            target_date,
            next_session,
            ("HARD_DEADLINE_EXCEEDED",),
        )

    def _map_post_close_result(
        self,
        result: PostCloseRunResult,
        *,
        target_date: date,
        next_session: date | None,
        replay: bool,
    ) -> DailyForwardRunResult:
        receipt_result = self._terminal_receipt_result(
            target_date=target_date,
            next_session=next_session,
            replay=replay,
            fallback=result,
        )
        if receipt_result is not None and receipt_result.status != "WAITING_FOR_DATA":
            return receipt_result
        return DailyForwardRunResult(
            result.status,
            target_date,
            next_session,
            result.failure_codes,
            post_close=result,
            replay=replay,
        )

    def _latest_closed_session(self, now: datetime) -> tuple[date | None, tuple[str, ...]]:
        local_now = now.astimezone(self.updater.session_clock.timezone)
        close_time = time.fromisoformat(self.config.session_close)
        latest_possible = local_now.date()
        if local_now.time() < close_time:
            latest_possible -= timedelta(days=1)

        for offset in range(0, 15):
            candidate = latest_possible - timedelta(days=offset)
            try:
                context = self._context(candidate)
            except Exception as exc:
                return None, (f"REFERENCE_PREFLIGHT_{type(exc).__name__}",)
            if not self._context_ready(context):
                return None, ("REFERENCE_PREFLIGHT_FAILED",)
            if context.target_date_is_session:
                return candidate, ()
        return None, ("NO_ELIGIBLE_CLOSED_SESSION",)

    def run_once(
        self,
        *,
        run_date: date | None = None,
        replay: bool = False,
        execution_mode: str = "MANUAL",
    ) -> DailyForwardRunResult:
        now = self._now()
        local_date = now.astimezone(self.updater.session_clock.timezone).date()
        if run_date is None:
            if execution_mode == "SCHEDULED":
                # The scheduler owns wake-up timing only.  The current local
                # date is passed to G2 so a canonical holiday becomes a
                # successful MARKET_CLOSED no-op rather than silently running
                # the prior session.
                target_date, resolution_reasons = local_date, ()
            else:
                target_date, resolution_reasons = self._latest_closed_session(now)
                if target_date is None:
                    return DailyForwardRunResult(
                        "BLOCKED",
                        None,
                        None,
                        resolution_reasons,
                    )
        else:
            target_date = run_date
        is_replay = replay or (run_date is not None and target_date != local_date)

        try:
            context = self._context(target_date)
        except Exception as exc:
            return DailyForwardRunResult(
                "BLOCKED",
                target_date,
                None,
                (f"REFERENCE_PREFLIGHT_{type(exc).__name__}",),
                replay=is_replay,
            )

        if not self._context_ready(context):
            reasons = []
            if context.reference_result.get("referenceLoadStatus") != "READY":
                reasons.append("REFERENCE_CONTEXT_NOT_READY")
            if context.eligibility_error is not None:
                reasons.append("LIFECYCLE_CONTEXT_INVALID")
            if not all(market.context_ready for market in context.markets):
                reasons.append("MARKET_CONTEXT_NOT_READY")
            return DailyForwardRunResult(
                "BLOCKED",
                target_date,
                None,
                tuple(dict.fromkeys(reasons)) or ("REFERENCE_PREFLIGHT_FAILED",),
                replay=is_replay,
            )

        next_session = self._next_session(target_date)
        if not context.target_date_is_session:
            result = self.updater.run_once(
                run_date=target_date,
                allow_terminal_recovery=execution_mode == "SCHEDULED",
                execution_mode=execution_mode,
            )
            mapped = self._map_post_close_result(
                result,
                target_date=target_date,
                next_session=next_session,
                replay=is_replay,
            )
            if not mapped.reason_codes:
                return DailyForwardRunResult(
                    mapped.status,
                    mapped.target_date,
                    mapped.next_session_date,
                    (context.target_date_reason or "NON_TRADING_DAY",),
                    post_close=mapped.post_close,
                    replay=mapped.replay,
                )
            return mapped

        local_time = now.astimezone(self.updater.session_clock.timezone).time()
        post_close_start = time.fromisoformat(self.config.post_close_start)
        if not is_replay and local_time < post_close_start:
            return DailyForwardRunResult(
                "WAITING_FOR_POST_CLOSE",
                target_date,
                next_session,
                ("POST_CLOSE_WINDOW_NOT_REACHED",),
            )

        if not is_replay:
            existing = self._terminal_receipt_result(
                target_date=target_date,
                next_session=next_session,
                replay=False,
            )
            if existing is not None and existing.status != "WAITING_FOR_DATA":
                return existing
            # 15:00 is a hard operational alert threshold, not a permanent
            # same-session publication boundary.  The updater records WAIT
            # and the existing scheduler cadence retries without sleeping a
            # worker indefinitely.  A later READY result may still publish
            # this same session through the normal idempotent path.

        result = self.updater.run_once(
            run_date=target_date,
            allow_terminal_recovery=execution_mode == "SCHEDULED",
            execution_mode=execution_mode,
        )
        return self._map_post_close_result(
            result,
            target_date=target_date,
            next_session=next_session,
            replay=is_replay,
        )


__all__ = ["DailyForwardRunResult", "DailyForwardRunner"]
