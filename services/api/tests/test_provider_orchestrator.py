from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from topicpilot_api.live.contracts import IntradayBar, IntradayFetchResult, LiveProviderError
from topicpilot_api.live.orchestrator import (
    CanonicalResolver,
    CircuitState,
    PersistentQuoteWorker,
    ProviderBudget,
    ProviderRegistration,
    ProviderRegistry,
    ProviderRouter,
    ProviderSessionState,
)


class StubProvider:
    def __init__(self, code: str, *, fail: bool = False, observed_at: datetime | None = None):
        self.source_code = code
        self.adapter_version = f"{code.lower()}.v1"
        self.fail = fail
        self.observed_at = observed_at or datetime(2026, 8, 10, 2, 0, tzinfo=UTC)
        self.calls = 0
        self.connected = 0
        self.disconnected = 0

    def connect(self):
        self.connected += 1

    def disconnect(self):
        self.disconnected += 1

    def fetch_intraday(self, instrument_code, market_code, *, session_date):
        self.calls += 1
        if self.fail:
            raise LiveProviderError("UPSTREAM_DOWN", self.source_code)
        bar = IntradayBar(
            instrument_code,
            market_code,
            self.observed_at,
            Decimal("100"),
            Decimal("101"),
            Decimal("99"),
            Decimal("100"),
            Decimal("1000"),
            "5m",
            {"close": "100", "volume": "1000"},
        )
        return IntradayFetchResult(
            instrument_code,
            market_code,
            f"{instrument_code}@{market_code}",
            self.source_code,
            self.adapter_version,
            datetime(2026, 8, 10, 2, 1, tzinfo=UTC),
            (bar,),
        )


def _router(*providers, threshold=3, budget=None):
    registry = ProviderRegistry()
    for provider, rank in providers:
        registry.register(
            ProviderRegistration(
                provider.source_code,
                provider,
                budget=budget or ProviderBudget(),
                source_rank=rank,
            )
        )
    return ProviderRouter(
        registry,
        clock=lambda: datetime(2026, 8, 10, 2, 2, tzinfo=UTC),
        circuit_failure_threshold=threshold,
        circuit_open_seconds=60,
    )


def test_router_fails_over_without_collector_provider_change():
    failed = StubProvider("FAILED")
    failed.fail = True
    healthy = StubProvider("HEALTHY")
    router = _router((failed, 1), (healthy, 20), threshold=1)

    routed = router.fetch_with_evidence("2330", "TPE", session_date=date(2026, 8, 10))

    assert routed.resolution.result.source_code == "HEALTHY"
    assert routed.attempted_providers == ("FAILED", "HEALTHY")
    assert router.health["FAILED"].circuit_state == CircuitState.OPEN
    assert router.health["HEALTHY"].availability == "AVAILABLE"


def test_canonical_resolver_uses_source_rank_only_as_final_tie_breaker():
    old = StubProvider("LOW_RANK", observed_at=datetime(2026, 8, 9, 2, 0, tzinfo=UTC))
    current = StubProvider("CURRENT", observed_at=datetime(2026, 8, 10, 2, 0, tzinfo=UTC))
    registry = {
        "LOW_RANK": ProviderRegistration("LOW_RANK", old, source_rank=1),
        "CURRENT": ProviderRegistration("CURRENT", current, source_rank=99),
    }
    health = {
        code: router_health for code, router_health in (("LOW_RANK", None), ("CURRENT", None))
    }
    resolver = CanonicalResolver(
        registry,
        health,
        clock=lambda: datetime(2026, 8, 10, 2, 2, tzinfo=UTC),
    )
    old_result = old.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 10))
    current_result = current.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 10))

    resolution = resolver.resolve(
        (old_result, current_result), session_date=date(2026, 8, 10), market_code="TPE"
    )

    assert resolution.result.source_code == "CURRENT"
    assert resolution.evidence["canonical_reason"] != (
        "VALID_CURRENT_FRESH_HEALTHY_SOURCE_RANK_TIE_BREAK"
    )


def test_budget_and_circuit_breaker_stop_repeated_upstream_calls():
    failed = StubProvider("FAILED")
    failed.fail = True
    router = _router(
        (failed, 1),
        threshold=1,
        budget=ProviderBudget(requests_per_minute=1),
    )

    with pytest.raises(LiveProviderError) as first:
        router.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 10))
    with pytest.raises(LiveProviderError) as second:
        router.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 10))

    assert first.value.code == "UPSTREAM_DOWN"
    assert second.value.code == "NO_PROVIDER_AVAILABLE"
    assert failed.calls == 1


def test_persistent_worker_calls_connect_once_and_disconnects_at_shutdown():
    provider = StubProvider("SESSION")
    router = _router((provider, 1))
    worker = PersistentQuoteWorker(router)

    worker.start()
    router.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 10))
    router.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 10))
    worker.stop()

    assert provider.connected == 1
    assert provider.disconnected == 1
    assert router.health["SESSION"].session_state == ProviderSessionState.DISCONNECTED


def test_persistent_worker_handles_disabled_provider_without_startup_error():
    provider = StubProvider("DISABLED")
    registry = ProviderRegistry()
    registry.register(
        ProviderRegistration(
            "DISABLED",
            provider,
            enabled=False,
        )
    )
    router = ProviderRouter(registry)
    worker = PersistentQuoteWorker(router)

    worker.start()
    worker.stop()

    assert provider.connected == 0
    assert router.health["DISABLED"].last_error_code == "PROVIDER_DISABLED"
    assert router.health["DISABLED"].session_state == ProviderSessionState.DISCONNECTED
