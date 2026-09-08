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

    def run_once(
        self,
        *,
        run_date: date | None = None,
        replay: bool = False,
    ) -> DailyForwardRunResult:
        now = self._now()
        local_date = now.astimezone(self.updater.session_clock.timezone).date()
        target_date = run_date or local_date
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
            result = self.updater.run_once(run_date=target_date)
            return DailyForwardRunResult(
                result.status,
                target_date,
                next_session,
                result.failure_codes or (context.target_date_reason or "NON_TRADING_DAY",),
                post_close=result,
                replay=is_replay,
            )

        local_time = now.astimezone(self.updater.session_clock.timezone).time()
        post_close_start = time.fromisoformat(self.config.post_close_start)
        if not is_replay and (target_date != local_date or local_time < post_close_start):
            return DailyForwardRunResult(
                "WAITING_FOR_POST_CLOSE",
                target_date,
                next_session,
                ("POST_CLOSE_WINDOW_NOT_REACHED",),
            )

        result = self.updater.run_once(run_date=target_date)
        return DailyForwardRunResult(
            result.status,
            target_date,
            next_session,
            result.failure_codes,
            post_close=result,
            replay=is_replay,
        )


__all__ = ["DailyForwardRunResult", "DailyForwardRunner"]
