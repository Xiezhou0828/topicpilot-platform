from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from topicpilot_api.live.collector import LiveCollector
from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.contracts import (
    IntradayBar,
    IntradayFetchResult,
    LiveProviderError,
    TrackingInstrument,
)
from topicpilot_api.live.scheduler import LiveScheduler


class FakeRepository:
    def __init__(self, item):
        self.item = item
        self.next_id = uuid4()
        self.attempts = []
        self.finished = None
        self.persisted = []

    def start_run(self, **_kwargs):
        return self.next_id, uuid4()

    def list_tracking(self, _mode):
        return [self.item]

    def heartbeat(self, *_args):
        return None

    def persist_bar(self, **kwargs):
        self.persisted.append(kwargs)
        return ("PRICE", "VOLUME")

    def record_attempt(self, **values):
        self.attempts.append(values)
        return uuid4()

    def finish_run(self, run_id, **values):
        self.finished = (run_id, values)


class RetryProvider:
    source_code = "TEST_LIVE"
    adapter_version = "test-live.v1"

    def __init__(self):
        self.calls = 0

    def fetch_intraday(self, instrument_code, market_code, *, session_date):
        self.calls += 1
        if self.calls == 1:
            raise LiveProviderError("TEMPORARY", "try again")
        now = datetime(2026, 8, 10, 2, 0, tzinfo=UTC)
        bar = IntradayBar(
            instrument_code,
            market_code,
            now,
            Decimal("100"),
            Decimal("101"),
            Decimal("99"),
            Decimal("100.5"),
            Decimal("1200"),
            "5m",
            {"close": "100.5", "volume": "1200"},
        )
        return IntradayFetchResult(
            instrument_code,
            market_code,
            f"{instrument_code}@{market_code}",
            self.source_code,
            self.adapter_version,
            now,
            (bar,),
        )


def _item():
    return TrackingInstrument(
        uuid4(), "2330", "TPE", "INTRADAY", "ABOVE", Decimal("100"), Decimal("99")
    )


def _config():
    return LiveRuntimeConfig(max_retries=1, retry_backoff_seconds=0, poll_interval_seconds=60)


def test_live_collector_isolates_retry_and_persists_success():
    repository = FakeRepository(_item())
    provider = RetryProvider()
    collector = LiveCollector(
        repository,
        provider,
        _config(),
        clock=lambda: datetime(2026, 8, 10, 2, 0, tzinfo=UTC),
        sleep=lambda _seconds: None,
    )

    result = collector.run_once(
        instruments=[repository.item],
        session_date=date(2026, 8, 10),
        enforce_session=False,
    )

    assert result.status == "SUCCESS"
    assert result.success_count == 1
    assert result.retry_count == 1
    assert provider.calls == 2
    assert len(repository.persisted) == 1
    assert [attempt["status"] for attempt in repository.attempts] == ["RETRYING", "SUCCESS"]
    assert repository.finished[1]["status"] == "SUCCESS"


def test_scheduler_decides_wait_intraday_and_post_close():
    repository = FakeRepository(_item())
    collector = LiveCollector(
        repository,
        RetryProvider(),
        _config(),
        clock=lambda: datetime(2026, 8, 10, 1, 0, tzinfo=UTC),
    )
    scheduler = LiveScheduler(
        collector,
        _config(),
        clock=lambda: datetime(2026, 8, 10, 1, 0, tzinfo=UTC),
    )

    assert scheduler.decide(datetime(2026, 8, 10, 1, 0, tzinfo=UTC)) == "INTRADAY"
    assert scheduler.decide(datetime(2026, 8, 10, 6, 0, tzinfo=UTC)) == "POST_CLOSE"
    assert scheduler.decide(datetime(2026, 8, 9, 1, 0, tzinfo=UTC)) == "WAIT"


def test_scheduler_routes_post_close_to_official_update_runner():
    repository = FakeRepository(_item())
    collector = LiveCollector(
        repository,
        RetryProvider(),
        _config(),
        clock=lambda: datetime(2026, 8, 10, 6, 0, tzinfo=UTC),
    )
    calls = []
    scheduler = LiveScheduler(
        collector,
        _config(),
        post_close_runner=lambda: calls.append("POST_CLOSE") or "official-result",
    )

    result = scheduler.run_once("POST_CLOSE", enforce_session=False)

    assert result == "official-result"
    assert calls == ["POST_CLOSE"]


def test_configured_closed_date_is_not_treated_as_an_open_session():
    config = LiveRuntimeConfig(closed_dates=frozenset({date(2026, 8, 10)}))
    collector = LiveCollector(
        FakeRepository(_item()),
        RetryProvider(),
        config,
        clock=lambda: datetime(2026, 8, 10, 1, 0, tzinfo=UTC),
    )

    result = collector.run_once(enforce_session=True)

    assert result.status == "MARKET_CLOSED"


def test_empty_intraday_universe_is_waiting_validation_not_success():
    repository = FakeRepository(_item())
    repository.list_tracking = lambda _mode: []
    collector = LiveCollector(
        repository,
        RetryProvider(),
        _config(),
        clock=lambda: datetime(2026, 8, 10, 2, 0, tzinfo=UTC),
    )

    result = collector.run_once(
        run_type="INTRADAY",
        enforce_session=False,
    )

    assert result.status == "WAITING_LIVE_VALIDATION"
    assert result.failure_codes == ("EMPTY_UNIVERSE",)
    assert repository.finished[1]["provider_status"] == "NOT_CALLED"


def test_scheduler_starts_worker_at_open_and_stops_before_post_close():
    class Worker:
        def __init__(self):
            self.events = []

        def start(self):
            self.events.append("start")

        def stop(self):
            self.events.append("stop")

    class Collector:
        repository = object()

        def __init__(self):
            self.modes = []

        def run_once(self, **kwargs):
            self.modes.append(kwargs["run_type"])

    class TimelineEvent:
        def __init__(self):
            self.cycles = 0

        def is_set(self):
            return self.cycles >= 2

        def wait(self, _seconds):
            self.cycles += 1

    config = _config()
    collector = Collector()
    worker = Worker()
    timeline = TimelineEvent()
    scheduler = LiveScheduler(
        collector,
        config,
        worker=worker,
        clock=lambda: datetime(
            2026,
            8,
            10,
            1 if timeline.cycles == 0 else 5,
            0 if timeline.cycles == 0 else 30,
            tzinfo=UTC,
        ),
    )

    scheduler.run_forever(timeline)

    assert worker.events == ["start", "stop"]
    assert collector.modes == ["INTRADAY", "POST_CLOSE"]
