"""Provider-neutral live orchestration primitives.

The collector owns persistence and scheduling.  This module owns provider
selection, budgets, health, canonical selection, and provider lifecycle.  A
new market-data provider is therefore an adapter registration, not a change
to the collector loop.
"""

from __future__ import annotations

import random
import time
from collections import deque
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta, timezone
from enum import StrEnum
from typing import Any, Protocol

from .contracts import IntradayFetchResult, IntradayProvider, LiveProviderError


class ProviderSessionState(StrEnum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    RECONNECTING = "RECONNECTING"


class CircuitState(StrEnum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class SessionProvider(Protocol):
    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def health_check(self) -> bool: ...


@dataclass(frozen=True)
class ProviderBudget:
    """Provider limits supplied by registration/configuration, not the collector."""

    requests_per_minute: int = 60
    symbols_per_request: int = 1
    cooldown_seconds: float = 0.0
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.requests_per_minute < 1 or self.symbols_per_request < 1:
            raise ValueError("provider budget limits must be positive")
        if self.cooldown_seconds < 0 or self.timeout_seconds <= 0:
            raise ValueError("provider budget timing is invalid")


@dataclass(frozen=True)
class ProviderRegistration:
    """All provider-specific policy required by the router."""

    code: str
    adapter: IntradayProvider
    budget: ProviderBudget = field(default_factory=ProviderBudget)
    supported_markets: frozenset[str] = frozenset()
    source_rank: int = 100
    enabled: bool = True

    def supports(self, market_code: str) -> bool:
        return not self.supported_markets or market_code in self.supported_markets


@dataclass
class ProviderHealth:
    session_state: ProviderSessionState = ProviderSessionState.DISCONNECTED
    circuit_state: CircuitState = CircuitState.AVAILABLE
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    total_latency_ms: int = 0
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error_code: str | None = None

    @property
    def average_latency_ms(self) -> float | None:
        total = self.success_count
        return self.total_latency_ms / total if total else None

    @property
    def availability(self) -> str:
        if self.circuit_state == CircuitState.OPEN:
            return "OPEN"
        if self.session_state in {
            ProviderSessionState.DEGRADED,
            ProviderSessionState.RECONNECTING,
        }:
            return "DEGRADED"
        return "AVAILABLE"

    def as_dict(self, code: str) -> dict[str, Any]:
        def iso(value: datetime | None) -> str | None:
            return value.isoformat() if value is not None else None

        return {
            "provider": code,
            "sessionState": self.session_state.value,
            "circuitState": self.circuit_state.value,
            "availability": self.availability,
            "successCount": self.success_count,
            "failureCount": self.failure_count,
            "averageLatencyMs": self.average_latency_ms,
            "lastSuccessAt": iso(self.last_success_at),
            "lastFailureAt": iso(self.last_failure_at),
            "lastErrorCode": self.last_error_code,
        }


class ProviderRegistry:
    """Runtime registry.  Collector code never imports a concrete adapter."""

    def __init__(self) -> None:
        self._registrations: dict[str, ProviderRegistration] = {}

    def register(self, registration: ProviderRegistration) -> None:
        if not registration.code.strip():
            raise ValueError("provider code must be non-empty")
        if getattr(registration.adapter, "source_code", None) != registration.code:
            raise ValueError("provider registration code must match adapter source_code")
        if registration.code in self._registrations:
            raise ValueError(f"provider is already registered: {registration.code}")
        self._registrations[registration.code] = registration

    def get(self, code: str) -> ProviderRegistration:
        try:
            registration = self._registrations[code]
        except KeyError as exc:
            raise LiveProviderError("PROVIDER_NOT_REGISTERED", code, retryable=False) from exc
        if not registration.enabled:
            raise LiveProviderError("PROVIDER_DISABLED", code, retryable=True)
        return registration

    def all(self) -> tuple[ProviderRegistration, ...]:
        return tuple(self._registrations.values())


class _CircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int,
        open_seconds: float,
        clock: Callable[[], datetime],
    ) -> None:
        if failure_threshold < 1 or open_seconds <= 0:
            raise ValueError("circuit breaker configuration is invalid")
        self.failure_threshold = failure_threshold
        self.open_seconds = open_seconds
        self.clock = clock
        self.state = CircuitState.AVAILABLE
        self.consecutive_failures = 0
        self.opened_at: datetime | None = None
        self._probe_in_flight = False

    def allow(self) -> bool:
        if self.state != CircuitState.OPEN:
            if self.state == CircuitState.HALF_OPEN and self._probe_in_flight:
                return False
            self._probe_in_flight = self.state == CircuitState.HALF_OPEN
            return True
        now = self.clock()
        if self.opened_at is None or now - self.opened_at < timedelta(seconds=self.open_seconds):
            return False
        self.state = CircuitState.HALF_OPEN
        self._probe_in_flight = True
        return True

    def success(self) -> None:
        self.state = CircuitState.AVAILABLE
        self.consecutive_failures = 0
        self.opened_at = None
        self._probe_in_flight = False

    def failure(self) -> None:
        self.consecutive_failures += 1
        self._probe_in_flight = False
        if self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = self.clock()
        elif self.state != CircuitState.HALF_OPEN:
            self.state = CircuitState.DEGRADED


class _RequestBudget:
    def __init__(self, budget: ProviderBudget, clock: Callable[[], datetime]) -> None:
        self.budget = budget
        self.clock = clock
        self._requests: deque[datetime] = deque()
        self._last_request: datetime | None = None

    def available(self) -> bool:
        now = self.clock()
        cutoff = now - timedelta(minutes=1)
        while self._requests and self._requests[0] <= cutoff:
            self._requests.popleft()
        if len(self._requests) >= self.budget.requests_per_minute:
            return False
        return not (
            self._last_request is not None
            and now - self._last_request < timedelta(seconds=self.budget.cooldown_seconds)
        )

    def consume(self) -> None:
        if not self.available():
            raise LiveProviderError("PROVIDER_BUDGET_EXHAUSTED", "provider budget is unavailable")
        now = self.clock()
        self._requests.append(now)
        self._last_request = now


@dataclass(frozen=True)
class CanonicalResolution:
    result: IntradayFetchResult
    evidence: Mapping[str, Any]


class CanonicalResolver:
    """Choose valid/current/fresh observations before provider priority.

    Provider source rank is deliberately the final tie-breaker.  It is never
    allowed to override a newer, valid, or healthier observation.
    """

    def __init__(
        self,
        registrations: Mapping[str, ProviderRegistration],
        health: Mapping[str, ProviderHealth],
        *,
        timezone_name: str = "Asia/Taipei",
        freshness_seconds: int = 900,
        timestamp_future_tolerance_seconds: int = 300,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        from zoneinfo import ZoneInfo

        self.registrations = registrations
        self.health = health
        self.timezone = ZoneInfo(timezone_name)
        self.freshness_seconds = freshness_seconds
        self.timestamp_future_tolerance_seconds = timestamp_future_tolerance_seconds
        self.clock = clock or (lambda: datetime.now(timezone.utc))  # noqa: UP017

    def resolve(
        self,
        results: Iterable[IntradayFetchResult],
        *,
        session_date: date,
        market_code: str,
    ) -> CanonicalResolution:
        candidates: list[
            tuple[
                tuple[int, int, int, int, datetime, datetime, int],
                IntradayFetchResult,
                dict[str, Any],
            ]
        ] = []
        rejected: list[dict[str, Any]] = []
        now = self.clock()
        for result in results:
            latest = result.latest
            reasons: list[str] = []
            if result.market_code != market_code:
                reasons.append("MARKET_MISMATCH")
            if latest is None:
                reasons.append("EMPTY_RESULT")
            elif latest.market_code != market_code:
                reasons.append("BAR_MARKET_MISMATCH")
            elif latest.close is None:
                reasons.append("MISSING_CLOSE")
            elif any(
                value is not None and value < 0
                for value in (latest.open, latest.high, latest.low, latest.close, latest.volume)
            ):
                reasons.append("NEGATIVE_VALUE")
            if latest is not None and latest.high is not None and latest.low is not None:
                values = tuple(
                    value
                    for value in (latest.open, latest.high, latest.low, latest.close)
                    if value is not None
                )
                if values and (latest.low > min(values) or latest.high < max(values)):
                    reasons.append("INVALID_OHLC")
            current = False
            fresh = False
            retrieved_valid = False
            future_skew_seconds = 0
            timestamp_quality = "UNKNOWN"
            observed_at = (
                latest.observed_at if latest is not None else datetime.min.replace(tzinfo=UTC)
            )
            if latest is not None:
                current = latest.observed_at.astimezone(self.timezone).date() == session_date
                retrieved_valid = result.retrieved_at <= now + timedelta(seconds=1)
                age = max(0.0, (now - latest.observed_at.astimezone(UTC)).total_seconds())
                fresh = age <= self.freshness_seconds
                future_skew_seconds = max(
                    0,
                    round((latest.observed_at - result.retrieved_at).total_seconds()),
                )
                timestamp_quality = (
                    "VALID"
                    if future_skew_seconds <= self.timestamp_future_tolerance_seconds
                    else "OBSERVED_AFTER_RETRIEVED"
                )
                if timestamp_quality != "VALID":
                    reasons.append("OBSERVED_AFTER_RETRIEVED")
            if reasons:
                rejected.append({"provider": result.source_code, "reasons": reasons})
                continue
            registration = self.registrations.get(result.source_code)
            rank = registration.source_rank if registration else 100
            provider_health = self.health.get(result.source_code)
            healthy = int(provider_health is None or provider_health.availability == "AVAILABLE")
            score = (
                int(current),
                int(fresh),
                int(retrieved_valid),
                healthy,
                observed_at,
                result.retrieved_at,
                -rank,
            )
            candidates.append(
                (
                    score,
                    result,
                    {
                        "provider": result.source_code,
                        "observed_at": latest.observed_at.isoformat(),
                        "retrieved_at": result.retrieved_at.isoformat(),
                        "fresh": fresh,
                        "current": current,
                        "source_rank": rank,
                        "timestampSemantics": {
                            "observedAt": "UPSTREAM_EVENT_TIME",
                            "retrievedAt": "LOCAL_RECEIPT_TIME",
                            "futureSkewSeconds": future_skew_seconds,
                            "quality": timestamp_quality,
                        },
                    },
                )
            )
        if not candidates:
            raise LiveProviderError(
                "NO_VALID_CANONICAL_OBSERVATION", "all provider results were rejected"
            )
        candidates.sort(key=lambda item: item[0], reverse=True)
        _, result, selected = candidates[0]
        tie_break = len(candidates) > 1 and candidates[0][0][:-1] == candidates[1][0][:-1]
        selected["canonical_reason"] = (
            "VALID_CURRENT_FRESH_HEALTHY_SOURCE_RANK_TIE_BREAK"
            if tie_break
            else "VALIDITY_CURRENTNESS_FRESHNESS_HEALTH"
        )
        selected["rejected_candidates"] = rejected
        selected["candidate_count"] = len(candidates)
        return CanonicalResolution(result, selected)


@dataclass(frozen=True)
class RoutedFetch:
    resolution: CanonicalResolution
    attempted_providers: tuple[str, ...]


class ProviderRouter:
    """Failover router with budget, health, circuit breaker and resolution."""

    source_code = "PROVIDER_ROUTER"
    adapter_version = "provider-router.v1"

    def __init__(
        self,
        registry: ProviderRegistry,
        *,
        timezone_name: str = "Asia/Taipei",
        freshness_seconds: int = 900,
        timestamp_future_tolerance_seconds: int = 300,
        circuit_failure_threshold: int = 3,
        circuit_open_seconds: float = 60.0,
        reconnect_initial_seconds: float = 1.0,
        reconnect_max_seconds: float = 30.0,
        reconnect_jitter_seconds: float = 0.25,
        clock: Callable[[], datetime] | None = None,
        random_source: random.Random | None = None,
    ) -> None:
        self.registry = registry
        self.clock = clock or (lambda: datetime.now(timezone.utc))  # noqa: UP017
        self.random = random_source or random.Random()
        self.reconnect_initial_seconds = reconnect_initial_seconds
        self.reconnect_max_seconds = reconnect_max_seconds
        self.reconnect_jitter_seconds = reconnect_jitter_seconds
        self.health: dict[str, ProviderHealth] = {
            item.code: ProviderHealth() for item in registry.all()
        }
        self._budgets = {
            item.code: _RequestBudget(item.budget, self.clock) for item in registry.all()
        }
        self._breakers = {
            item.code: _CircuitBreaker(
                failure_threshold=circuit_failure_threshold,
                open_seconds=circuit_open_seconds,
                clock=self.clock,
            )
            for item in registry.all()
        }
        self._resolver = CanonicalResolver(
            {item.code: item for item in registry.all()},
            self.health,
            timezone_name=timezone_name,
            freshness_seconds=freshness_seconds,
            timestamp_future_tolerance_seconds=timestamp_future_tolerance_seconds,
            clock=self.clock,
        )

    def _candidates(self, market_code: str) -> list[ProviderRegistration]:
        values = []
        for registration in self.registry.all():
            health = self.health[registration.code]
            if (
                registration.enabled
                and registration.supports(market_code)
                and self._breakers[registration.code].allow()
                and self._budgets[registration.code].available()
            ):
                values.append(registration)
                continue
            health.circuit_state = self._breakers[registration.code].state
        values.sort(
            key=lambda item: (
                self.health[item.code].average_latency_ms
                if self.health[item.code].average_latency_ms is not None
                else float("inf"),
                item.source_rank,
            )
        )
        return values

    def _record_failure(self, registration: ProviderRegistration, exc: Exception) -> None:
        health = self.health[registration.code]
        health.failure_count += 1
        health.consecutive_failures += 1
        health.last_failure_at = self.clock()
        health.last_error_code = getattr(exc, "code", "LIVE_PROVIDER_ERROR")
        self._breakers[registration.code].failure()
        health.circuit_state = self._breakers[registration.code].state
        health.session_state = ProviderSessionState.DEGRADED

    def _record_success(self, registration: ProviderRegistration, latency_ms: int) -> None:
        health = self.health[registration.code]
        health.success_count += 1
        health.consecutive_failures = 0
        health.total_latency_ms += latency_ms
        health.last_success_at = self.clock()
        health.last_error_code = None
        self._breakers[registration.code].success()
        health.circuit_state = CircuitState.AVAILABLE
        health.session_state = ProviderSessionState.READY

    def _ensure_session(self, registration: ProviderRegistration) -> None:
        health = self.health[registration.code]
        check = getattr(registration.adapter, "health_check", None)
        if health.session_state == ProviderSessionState.READY and callable(check) and not check():
            health.session_state = ProviderSessionState.DEGRADED
        if health.session_state not in {
            ProviderSessionState.DEGRADED,
            ProviderSessionState.RECONNECTING,
        }:
            return
        connect = getattr(registration.adapter, "connect", None)
        if not callable(connect):
            health.session_state = ProviderSessionState.READY
            return
        health.session_state = ProviderSessionState.RECONNECTING
        try:
            if health.consecutive_failures:
                attempt = max(0, health.consecutive_failures - 1)
                delay = min(
                    self.reconnect_max_seconds,
                    self.reconnect_initial_seconds * (2**attempt),
                )
                delay += self.random.uniform(0, self.reconnect_jitter_seconds)
                if delay > 0:
                    time.sleep(delay)
            connect()
            if callable(check) and not check():
                raise LiveProviderError("PROVIDER_HEALTH_CHECK_FAILED", registration.code)
            health.session_state = ProviderSessionState.READY
        except Exception:
            health.session_state = ProviderSessionState.DEGRADED
            raise

    def fetch_with_evidence(
        self, instrument_code: str, market_code: str, *, session_date: date
    ) -> RoutedFetch:
        attempted: list[str] = []
        results: list[IntradayFetchResult] = []
        first_error: Exception | None = None
        for registration in self._candidates(market_code):
            attempted.append(registration.code)
            try:
                self._ensure_session(registration)
                self._budgets[registration.code].consume()
                started = time.monotonic()
                result = registration.adapter.fetch_intraday(
                    instrument_code, market_code, session_date=session_date
                )
                self._record_success(registration, int((time.monotonic() - started) * 1000))
                results.append(result)
                # One result is sufficient in the normal case.  Additional
                # providers are used after a failure or by an explicit caller
                # that supplies multiple results to CanonicalResolver.
                break
            except Exception as exc:
                first_error = first_error or exc
                self._record_failure(registration, exc)
                continue
        if not results:
            if first_error is not None:
                raise first_error
            raise LiveProviderError("NO_PROVIDER_AVAILABLE", "no healthy provider fits the market")
        resolution = self._resolver.resolve(
            results, session_date=session_date, market_code=market_code
        )
        return RoutedFetch(resolution, tuple(attempted))

    def fetch_intraday(
        self, instrument_code: str, market_code: str, *, session_date: date
    ) -> IntradayFetchResult:
        return self.fetch_with_evidence(
            instrument_code, market_code, session_date=session_date
        ).resolution.result

    def connect_all(
        self, *, max_attempts: int = 3, backoff_seconds: float = 1.0, jitter_seconds: float = 0.25
    ) -> None:
        for registration in self.registry.all():
            health = self.health[registration.code]
            if not registration.enabled:
                health.session_state = ProviderSessionState.DISCONNECTED
                health.circuit_state = CircuitState.AVAILABLE
                health.last_error_code = "PROVIDER_DISABLED"
                continue
            connect = getattr(registration.adapter, "connect", None)
            if not callable(connect):
                health.session_state = ProviderSessionState.READY
                continue
            health.session_state = ProviderSessionState.CONNECTING
            last_error: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    connect()
                    check = getattr(registration.adapter, "health_check", None)
                    if callable(check) and not check():
                        raise LiveProviderError("PROVIDER_HEALTH_CHECK_FAILED", registration.code)
                    health.session_state = ProviderSessionState.READY
                    break
                except Exception as exc:
                    last_error = exc
                    health.session_state = (
                        ProviderSessionState.RECONNECTING
                        if attempt + 1 < max_attempts
                        else ProviderSessionState.DEGRADED
                    )
                    if attempt + 1 < max_attempts:
                        delay = backoff_seconds * (2**attempt) + self.random.uniform(
                            0, jitter_seconds
                        )
                        time.sleep(delay)
            if last_error is not None and health.session_state == ProviderSessionState.DEGRADED:
                self._record_failure(registration, last_error)

    def disconnect_all(self) -> None:
        for registration in self.registry.all():
            disconnect = getattr(registration.adapter, "disconnect", None)
            if callable(disconnect):
                try:
                    disconnect()
                finally:
                    self.health[registration.code].session_state = ProviderSessionState.DISCONNECTED
            else:
                self.health[registration.code].session_state = ProviderSessionState.DISCONNECTED

    def health_snapshot(self) -> list[dict[str, Any]]:
        return [self.health[item.code].as_dict(item.code) for item in self.registry.all()]


class PersistentQuoteWorker:
    """Own provider session lifecycle around a long-running scheduler."""

    def __init__(self, router: ProviderRouter, *, config: Any | None = None) -> None:
        self.router = router
        self.config = config

    def start(self) -> None:
        config = self.config
        self.router.connect_all(
            max_attempts=getattr(config, "max_retries", 2) + 1,
            backoff_seconds=getattr(config, "reconnect_initial_seconds", 1.0),
            jitter_seconds=getattr(config, "reconnect_jitter_seconds", 0.25),
        )

    def stop(self) -> None:
        self.router.disconnect_all()


__all__ = [
    "CanonicalResolution",
    "CanonicalResolver",
    "CircuitState",
    "PersistentQuoteWorker",
    "ProviderBudget",
    "ProviderHealth",
    "ProviderRegistration",
    "ProviderRegistry",
    "ProviderRouter",
    "ProviderSessionState",
    "RoutedFetch",
]
