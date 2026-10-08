"""Time-window and market-stage policy for the daily publication flow.

The worker remains a five-minute polling loop.  These helpers therefore
describe eligibility windows, not exact cron timestamps.  They are kept
side-effect free so the orchestration and its tests can reason about stage
boundaries without touching provider or database state.
"""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from .config import LiveRuntimeConfig

TWSE_MARKET = "TPE"
TPEX_MARKET = "TWO"


def _clock(value: str | time) -> time:
    return time.fromisoformat(value) if isinstance(value, str) else value


def local_time(now: datetime, config: LiveRuntimeConfig) -> time:
    if now.tzinfo is None:
        raise ValueError("staged publication clock must be timezone-aware")
    return now.astimezone(ZoneInfo(config.timezone_name)).time()


def eligible_markets(now: datetime, config: LiveRuntimeConfig) -> tuple[str, ...]:
    """Return market providers eligible in this polling cycle.

    TPE is eligible from the TWSE target onward.  TWO is independently
    eligible from the TPEx target onward, even when TPE is still waiting.
    """

    current = local_time(now, config)
    if current < _clock(config.twse_ingestion_start):
        return ()
    if current < _clock(config.tpex_ingestion_start):
        return (TWSE_MARKET,)
    return (TWSE_MARKET, TPEX_MARKET)


def tpex_retry_window_open(now: datetime, config: LiveRuntimeConfig) -> bool:
    """Return whether the bounded early TPEx retry window has opened."""

    return local_time(now, config) >= _clock(config.tpex_retry_start)


def stage_for(now: datetime, config: LiveRuntimeConfig) -> str:
    """Resolve an observability state without asserting data readiness."""

    current = local_time(now, config)
    if current < _clock(config.post_close_start):
        return "PRE_POST_CLOSE"
    if current < _clock(config.twse_ingestion_start):
        return "WAITING_TWSE_WINDOW"
    if current < _clock(config.tpex_ingestion_start):
        return "TWSE_WINDOW"
    if current < _clock(config.soft_target):
        return "MARKET_INGESTION"
    if current < _clock(config.hard_deadline):
        return "COMBINED_RECONCILIATION"
    if current < _clock(config.late_data_target):
        return "PRICE_BASED_FORMAL"
    if current < _clock(config.late_data_hard_deadline):
        return "LATE_DATA_ENRICHMENT"
    return "LATE_DATA_DEADLINE"


__all__ = [
    "TPEX_MARKET",
    "TWSE_MARKET",
    "eligible_markets",
    "local_time",
    "stage_for",
    "tpex_retry_window_open",
]
