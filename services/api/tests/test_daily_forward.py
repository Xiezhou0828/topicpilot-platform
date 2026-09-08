from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.daily_forward import DailyForwardRunner
from topicpilot_api.live.post_close import PostCloseRunResult, PostCloseUpdater
from topicpilot_api.live.session import MarketSessionClock


def _context(target_date: date):
    closed = {date(2026, 9, 25), date(2026, 9, 28)}
    is_session = target_date.weekday() < 5 and target_date not in closed
    return SimpleNamespace(
        reference_result={"referenceLoadStatus": "READY"},
        eligibility_error=None,
        target_date_is_session=is_session,
        target_date_reason=None if is_session else "TARGET_DATE_CLOSED_HOLIDAY",
        markets=[SimpleNamespace(context_ready=True), SimpleNamespace(context_ready=True)],
    )


class FakeUpdater:
    def __init__(self, config: LiveRuntimeConfig, result_status: str = "SUCCESS"):
        self.session_clock = MarketSessionClock(
            config.timezone_name,
            config.session_open,
            config.session_close,
            config.closed_dates,
        )
        self.result_status = result_status
        self.calls: list[date] = []

    def run_once(self, *, run_date: date):
        self.calls.append(run_date)
        return PostCloseRunResult(
            "run-1",
            self.result_status,
            2,
            2 if self.result_status == "SUCCESS" else 0,
            0,
            0,
            1,
            2,
            0,
            () if self.result_status == "SUCCESS" else ("MARKET_CLOSED",),
            1 if self.result_status == "SUCCESS" else 0,
            "SUCCESS" if self.result_status == "SUCCESS" else "NOT_RUN_MARKET_CLOSED",
            run_date.isoformat(),
        )


def _runner(clock_value: datetime, *, result_status: str = "SUCCESS"):
    config = LiveRuntimeConfig()
    updater = FakeUpdater(config, result_status=result_status)
    runner = DailyForwardRunner(
        None,
        config,
        clock=lambda: clock_value,
        updater=updater,
        context_loader=lambda _session, **kwargs: _context(kwargs["target_date"]),
    )
    return runner, updater


def test_daily_forward_waits_until_configured_post_close_start():
    runner, updater = _runner(datetime(2026, 8, 31, 4, 0, tzinfo=UTC))

    result = runner.run_once()

    assert result.status == "WAITING_FOR_POST_CLOSE"
    assert result.target_date == date(2026, 8, 31)
    assert result.next_session_date == date(2026, 9, 1)
    assert updater.calls == []


def test_daily_forward_marks_reference_calendar_holiday_closed_without_provider_call():
    runner, updater = _runner(
        datetime(2026, 9, 25, 8, 0, tzinfo=UTC), result_status="MARKET_CLOSED"
    )

    result = runner.run_once()

    assert result.status == "MARKET_CLOSED"
    assert result.target_date == date(2026, 9, 25)
    assert result.next_session_date == date(2026, 9, 29)
    assert updater.calls == [date(2026, 9, 25)]


def test_daily_forward_replay_is_bounded_and_uses_existing_post_close_chain():
    runner, updater = _runner(datetime(2026, 8, 31, 4, 0, tzinfo=UTC))

    result = runner.run_once(run_date=date(2026, 8, 28), replay=True)

    assert result.status == "SUCCESS"
    assert result.replay is True
    assert result.target_date == date(2026, 8, 28)
    assert updater.calls == [date(2026, 8, 28)]


def test_daily_forward_preserves_fail_closed_updater_failure():
    runner, updater = _runner(
        datetime(2026, 8, 31, 8, 0, tzinfo=UTC), result_status="PARTIAL"
    )

    result = runner.run_once()

    assert result.status == "PARTIAL"
    assert result.reason_codes == ("MARKET_CLOSED",)
    assert updater.calls == [date(2026, 8, 31)]


def test_daily_forward_result_is_deterministically_serializable():
    runner, _updater = _runner(datetime(2026, 8, 31, 4, 0, tzinfo=UTC))

    first = runner.run_once().to_dict()
    second = runner.run_once().to_dict()

    assert first == second
    assert first["targetDate"] == "2026-08-31"
    assert first["nextSessionDate"] == "2026-09-01"


def test_post_close_success_is_reused_by_the_forward_run_key():
    config = LiveRuntimeConfig()
    updater = object.__new__(PostCloseUpdater)
    updater.config = config
    run = SimpleNamespace(
        id="existing-run",
        requested_count=2,
        success_count=2,
        failure_count=0,
        retry_count=1,
        metadata_payload={
            "forwardRunKey": "post-close:tw-reference-v1:TW_MARKET:2026-08-28",
            "providerPointCount": 2,
            "skippedCount": 0,
            "topicSnapshot": {"topicCount": 107, "status": "SUCCESS"},
            "forwardAutomation": {"status": "SUCCESS"},
        },
    )

    class FakeSession:
        def scalars(self, _query):
            return SimpleNamespace(all=lambda: [run])

    updater.session = FakeSession()

    result = updater._idempotent_result(date(2026, 8, 28))

    assert result is not None
    assert result.idempotent_reuse is True
    assert result.run_id == "existing-run"
    assert result.snapshot_count == 107


def test_formal_snapshot_gate_requires_published_pit_readback():
    ready = {
        "status": "SUCCESS",
        "formalTopicDailyState": {"status": "SUCCESS"},
        "formalTopicSnapshotReadback": {"status": "PASS"},
    }
    blocked = {
        "status": "SUCCESS",
        "formalTopicDailyState": {"status": "FORMAL_STATE_UNAVAILABLE"},
        "formalTopicSnapshotReadback": {"status": "FAIL"},
    }

    assert PostCloseUpdater._formal_snapshot_ready(ready) is True
    assert PostCloseUpdater._formal_snapshot_ready(blocked) is False
