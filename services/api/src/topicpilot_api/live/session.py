"""Taiwan session clock used only for runtime scheduling decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo


class SessionState:
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SessionStatus:
    state: str
    local_time: datetime
    reason: str


def _parse_time(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid session time: {value}") from exc


class MarketSessionClock:
    def __init__(
        self,
        timezone_name: str,
        session_open: str,
        session_close: str,
        closed_dates: frozenset[date] | set[date] = frozenset(),
    ):
        self.timezone = ZoneInfo(timezone_name)
        self.open_time = _parse_time(session_open)
        self.close_time = _parse_time(session_close)
        self.closed_dates = frozenset(closed_dates)
        if self.open_time >= self.close_time:
            raise ValueError("session_open must precede session_close")

    def status(self, now: datetime | None = None) -> SessionStatus:
        local = (now or datetime.now(self.timezone)).astimezone(self.timezone)
        if local.weekday() >= 5:
            return SessionStatus(SessionState.CLOSED, local, "WEEKEND")
        if local.date() in self.closed_dates:
            return SessionStatus(SessionState.CLOSED, local, "CONFIGURED_CLOSED_DATE")
        if self.open_time <= local.time() < self.close_time:
            return SessionStatus(SessionState.OPEN, local, "SESSION_OPEN")
        return SessionStatus(SessionState.CLOSED, local, "OUTSIDE_SESSION")


__all__ = ["MarketSessionClock", "SessionState", "SessionStatus"]
