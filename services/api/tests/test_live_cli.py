from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from topicpilot_api.live.cli import resolve_decision, result_exit_code
from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.session import MarketSessionClock


def _clock(config: LiveRuntimeConfig) -> MarketSessionClock:
    return MarketSessionClock(
        config.timezone_name,
        config.session_open,
        config.session_close,
        config.closed_dates,
    )


def test_cli_auto_uses_inclusive_1345_boundary():
    config = LiveRuntimeConfig()
    clock = _clock(config)
    taipei = ZoneInfo("Asia/Taipei")

    assert resolve_decision(
        "auto", config, clock, now=datetime(2026, 8, 10, 13, 44, 59, tzinfo=taipei)
    ) == "WAIT"
    assert resolve_decision(
        "auto", config, clock, now=datetime(2026, 8, 10, 13, 45, tzinfo=taipei)
    ) == "POST_CLOSE"


def test_cli_auto_keeps_configured_closed_date_out_of_post_close():
    config = LiveRuntimeConfig(closed_dates=frozenset({date(2026, 8, 10)}))

    assert resolve_decision(
        "auto",
        config,
        _clock(config),
        now=datetime(2026, 8, 10, 13, 45, tzinfo=ZoneInfo("Asia/Taipei")),
    ) == "WAIT"


def test_one_shot_cli_does_not_report_partial_or_waiting_as_success():
    class Result:
        def __init__(self, status: str):
            self.status = status

    assert result_exit_code(None) == 0
    assert result_exit_code(Result("SUCCESS")) == 0
    assert result_exit_code(Result("MARKET_CLOSED")) == 0
    for status in ("PARTIAL", "WAITING_LIVE_VALIDATION", "WAITING", "SKIPPED", "FAILED"):
        assert result_exit_code(Result(status)) == 1


def test_runtime_defaults_keep_the_frozen_trigger_boundary(monkeypatch):
    monkeypatch.delenv("TOPICPILOT_LIVE_POST_CLOSE_START", raising=False)

    assert LiveRuntimeConfig().post_close_start == "13:45"
    assert LiveRuntimeConfig.from_environment().post_close_start == "13:45"


def test_deployment_schedule_surfaces_are_frozen_to_1345():
    root = Path(__file__).resolve().parents[3]

    assert 'value: "13:45"' in (root / "render.yaml").read_text(encoding="utf-8")
    assert "TOPICPILOT_LIVE_POST_CLOSE_START=13:45" in (
        root / "services" / "api" / ".env.example"
    ).read_text(encoding="utf-8")
    compose = (root / "compose.yaml").read_text(encoding="utf-8")
    assert "TOPICPILOT_LIVE_POST_CLOSE_START: ${TOPICPILOT_LIVE_POST_CLOSE_START:-13:45}" in compose
