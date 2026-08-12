"""Small synchronous rate-limit/retry boundary for official exchange calls."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable


class RateLimitedTransport:
    """Apply a request-per-minute budget and retry transient transport errors.

    The wrapped exchange adapter remains responsible for payload validation and
    source semantics.  This class only controls request pacing and transport
    retries, which keeps the official daily adapters deterministic in tests.
    """

    def __init__(
        self,
        transport: Callable[[str, float], bytes],
        *,
        requests_per_minute: int = 60,
        min_interval_seconds: float = 0.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if requests_per_minute < 1:
            raise ValueError("requests_per_minute must be positive")
        if min_interval_seconds < 0 or retry_backoff_seconds < 0:
            raise ValueError("rate-limit timing must be non-negative")
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        self.transport = transport
        self.requests_per_minute = requests_per_minute
        self.min_interval_seconds = min_interval_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.sleep = sleep
        self.clock = clock
        self._requests: deque[float] = deque()
        self._last_request: float | None = None

    def _wait_for_budget(self) -> None:
        while True:
            now = self.clock()
            cutoff = now - 60.0
            while self._requests and self._requests[0] <= cutoff:
                self._requests.popleft()
            waits = [0.0]
            if self._requests and len(self._requests) >= self.requests_per_minute:
                waits.append(self._requests[0] + 60.0 - now)
            if self._last_request is not None:
                waits.append(self._last_request + self.min_interval_seconds - now)
            delay = max(waits)
            if delay <= 0:
                current = self.clock()
                self._requests.append(current)
                self._last_request = current
                return
            self.sleep(delay)

    def __call__(self, url: str, timeout: float) -> bytes:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self._wait_for_budget()
            try:
                return self.transport(url, timeout)
            except (OSError, TimeoutError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise
                self.sleep(self.retry_backoff_seconds * (2**attempt))
        assert last_error is not None
        raise last_error


__all__ = ["RateLimitedTransport"]
