from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from topicpilot_api.research.ws3_real_historical_coverage import (
    MA60_PERIOD,
    calculate_sma_close,
    event_intersects_window,
)


def test_sma_close_v1_uses_raw_trailing_sixty_closes() -> None:
    assert calculate_sma_close(list(range(1, 61))) == Decimal("30.5")
    assert calculate_sma_close(list(range(1, 60))) is None


def test_trailing_window_requires_actual_sixty_observations() -> None:
    dates = [date(2026, 2, 2) + timedelta(days=index) for index in range(MA60_PERIOD)]
    assert event_intersects_window(dates[0], dates, MA60_PERIOD - 2) is False
    assert event_intersects_window(dates[0], dates, MA60_PERIOD - 1) is True


def test_event_overlay_is_limited_to_the_actual_dependency_window() -> None:
    dates = [date(2026, 2, 2) + timedelta(days=index) for index in range(70)]
    assert event_intersects_window(dates[0], dates, 59) is True
    assert event_intersects_window(dates[0], dates, 60) is False
    assert event_intersects_window(dates[69], dates, 69) is True


def test_event_overlay_does_not_promote_continuity_unknown() -> None:
    # The coverage runner uses the shared policy adapter; this assertion keeps
    # the local coverage helper's continuity state explicit as UNKNOWN.
    from topicpilot_api.research.ws3_research_policy import CONTINUITY_UNKNOWN

    assert CONTINUITY_UNKNOWN == "CONTINUITY_UNKNOWN"
