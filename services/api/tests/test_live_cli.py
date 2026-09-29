from datetime import date, datetime
from zoneinfo import ZoneInfo

from topicpilot_api.live.cli import resolve_decision
from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.session import MarketSessionClock


def _clock(config: LiveRuntimeConfig) -> MarketSessionClock:
    return MarketSessionClock(
        config.timezone_name,
        config.session_open,
        config.session_close,
        config.closed_dates,
    )


def test_cli_auto_uses_inclusive_1335_boundary():
    config = LiveRuntimeConfig()
    clock = _clock(config)
    taipei = ZoneInfo("Asia/Taipei")

    assert resolve_decision(
        "auto", config, clock, now=datetime(2026, 8, 10, 13, 34, 59, tzinfo=taipei)
    ) == "WAIT"
    assert resolve_decision(
        "auto", config, clock, now=datetime(2026, 8, 10, 13, 35, tzinfo=taipei)
    ) == "POST_CLOSE"


def test_cli_auto_keeps_configured_closed_date_out_of_post_close():
    config = LiveRuntimeConfig(closed_dates=frozenset({date(2026, 8, 10)}))

    assert resolve_decision(
        "auto",
        config,
        _clock(config),
        now=datetime(2026, 8, 10, 13, 35, tzinfo=ZoneInfo("Asia/Taipei")),
    ) == "WAIT"


def test_runtime_defaults_keep_the_frozen_trigger_boundary(monkeypatch):
    monkeypatch.delenv("TOPICPILOT_LIVE_POST_CLOSE_START", raising=False)

    assert LiveRuntimeConfig().post_close_start == "13:35"
    assert LiveRuntimeConfig.from_environment().post_close_start == "13:35"
