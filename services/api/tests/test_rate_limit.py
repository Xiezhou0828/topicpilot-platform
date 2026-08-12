from __future__ import annotations

from topicpilot_api.market_data.rate_limit import RateLimitedTransport


def test_rate_limited_transport_retries_transient_transport_error() -> None:
    calls: list[str] = []
    sleeps: list[float] = []

    def transport(url: str, _timeout: float) -> bytes:
        calls.append(url)
        if len(calls) == 1:
            raise OSError("temporary network failure")
        return b"ok"

    result = RateLimitedTransport(
        transport,
        requests_per_minute=100,
        max_retries=1,
        retry_backoff_seconds=2.0,
        sleep=sleeps.append,
    )("https://example.test", 1.0)

    assert result == b"ok"
    assert calls == ["https://example.test", "https://example.test"]
    assert sleeps == [2.0]


def test_rate_limited_transport_enforces_interval_and_rolling_budget() -> None:
    now = 0.0
    request_times: list[float] = []

    def clock() -> float:
        return now

    def sleep(seconds: float) -> None:
        nonlocal now
        now += seconds

    transport = RateLimitedTransport(
        lambda _url, _timeout: request_times.append(now) or b"ok",
        requests_per_minute=2,
        min_interval_seconds=1.0,
        max_retries=0,
        sleep=sleep,
        clock=clock,
    )

    transport("one", 1.0)
    transport("two", 1.0)
    transport("three", 1.0)

    assert request_times == [0.0, 1.0, 60.0]
