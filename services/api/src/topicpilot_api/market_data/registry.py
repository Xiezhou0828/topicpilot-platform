"""Composition root for live provider registrations.

Concrete adapters are registered here.  The live collector and scheduler
depend only on :class:`ProviderRouter`, so adding another adapter is limited
to this composition layer plus its adapter implementation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.contracts import LiveProviderError
from topicpilot_api.live.orchestrator import (
    ProviderBudget,
    ProviderRegistration,
    ProviderRegistry,
    ProviderRouter,
)

from .exchange import TpexOfficialDailyProvider, TwseOfficialDailyProvider
from .history import HistoricalProvider, YahooChartHistoricalProvider
from .taishin import TaishinIntradayProvider
from .yahoo_quote import YahooQuoteProvider


@dataclass(frozen=True)
class HistoricalProviderRegistration:
    code: str
    adapter: HistoricalProvider
    supported_markets: frozenset[str]
    source_rank: int
    verification_only: bool = False


class HistoricalProviderRegistry:
    """Explicit daily-data responsibilities; no daily provider is used for quotes."""

    def __init__(self) -> None:
        self._registrations: list[HistoricalProviderRegistration] = []

    def register(self, registration: HistoricalProviderRegistration) -> None:
        if any(item.code == registration.code for item in self._registrations):
            raise ValueError(f"historical provider is already registered: {registration.code}")
        self._registrations.append(registration)

    def for_market(
        self, market_code: str, *, include_verification: bool = False
    ) -> tuple[HistoricalProviderRegistration, ...]:
        return tuple(
            item
            for item in sorted(self._registrations, key=lambda value: value.source_rank)
            if market_code in item.supported_markets
            and (include_verification or not item.verification_only)
        )

    def all(self) -> tuple[HistoricalProviderRegistration, ...]:
        return tuple(self._registrations)


class _UnavailableTaishinIntradayProvider:
    """Keeps the V1-validated slot visible when Windows credentials are absent."""

    source_code = "TAISHIN_TECH_ANALYSIS_INTRADAY"
    adapter_version = "taishin-tech-analysis-intraday.v1"

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def connect(self) -> None:
        return None

    def disconnect(self) -> None:
        return None

    def health_check(self) -> bool:
        return False

    def fetch_intraday(self, instrument_code: str, market_code: str, *, session_date: date):
        raise LiveProviderError("TAISHIN_PROVIDER_UNAVAILABLE", self.reason, retryable=False)


def build_live_provider_registry(
    config: LiveRuntimeConfig,
) -> ProviderRegistry:
    registry = ProviderRegistry()
    taishin = _build_taishin_provider()
    registry.register(
        ProviderRegistration(
            code=YahooQuoteProvider.source_code,
            adapter=YahooQuoteProvider(timeout=config.yahoo_timeout_seconds),
            budget=ProviderBudget(
                requests_per_minute=config.yahoo_requests_per_minute,
                symbols_per_request=1,
                cooldown_seconds=config.yahoo_cooldown_seconds,
                timeout_seconds=config.yahoo_timeout_seconds,
            ),
            source_rank=config.yahoo_source_rank,
            supported_markets=frozenset({"TPE", "TWO"}),
        )
    )
    registry.register(
        ProviderRegistration(
            code=TaishinIntradayProvider.source_code,
            adapter=taishin,
            budget=ProviderBudget(
                requests_per_minute=config.provider_requests_per_minute,
                symbols_per_request=config.provider_symbols_per_request,
                cooldown_seconds=config.provider_cooldown_seconds,
                timeout_seconds=config.provider_timeout_seconds,
            ),
            source_rank=config.taishin_source_rank,
            supported_markets=frozenset({"TPE", "TWO"}),
            enabled=not isinstance(taishin, _UnavailableTaishinIntradayProvider),
        )
    )
    return registry


def _build_taishin_provider() -> TaishinIntradayProvider | _UnavailableTaishinIntradayProvider:
    try:
        return TaishinIntradayProvider.from_environment()
    except LiveProviderError as exc:
        if exc.code != "TAISHIN_CREDENTIALS_UNAVAILABLE":
            raise
        return _UnavailableTaishinIntradayProvider(str(exc))


def build_historical_provider_registry(
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    exchange_transport: Callable[[str, float], bytes] | None = None,
    market_batch: bool = False,
) -> HistoricalProviderRegistry:
    end = end_date or (date.today() - timedelta(days=1))
    start = start_date or (end - timedelta(days=180))
    if end < start:
        raise ValueError("historical provider window is invalid")
    registry = HistoricalProviderRegistry()
    registry.register(
        HistoricalProviderRegistration(
            "TWSE_OFFICIAL_DAILY",
            TwseOfficialDailyProvider(
                start_date=start,
                end_date=end,
                transport=exchange_transport,
                market_batch=market_batch,
            )
            if exchange_transport is not None
            else TwseOfficialDailyProvider(
                start_date=start, end_date=end, market_batch=market_batch
            ),
            frozenset({"TPE"}),
            30,
        )
    )
    registry.register(
        HistoricalProviderRegistration(
            "TPEX_OFFICIAL_DAILY",
            TpexOfficialDailyProvider(
                start_date=start,
                end_date=end,
                transport=exchange_transport,
                market_batch=market_batch,
            )
            if exchange_transport is not None
            else TpexOfficialDailyProvider(
                start_date=start, end_date=end, market_batch=market_batch
            ),
            frozenset({"TWO"}),
            40,
        )
    )
    # V1 Yahoo daily history remains available for validation and the existing
    # TA path. It is deliberately not allowed to displace official daily data.
    registry.register(
        HistoricalProviderRegistration(
            "YAHOO_CHART_DAILY",
            YahooChartHistoricalProvider(period="6mo"),
            frozenset({"TPE", "TWO"}),
            50,
            verification_only=True,
        )
    )
    return registry


def canonical_daily_market_codes() -> tuple[str, ...]:
    """Return markets owned by the non-verification daily providers.

    The composition registry is the authority for daily market ownership.  A
    caller must not duplicate ``TPE``/``TWO`` as a second identity or provider
    routing list when deriving a preflight expectation.
    """

    registry = build_historical_provider_registry(
        start_date=date.today(), end_date=date.today(), market_batch=True
    )
    return tuple(
        sorted(
            {
                market
                for registration in registry.all()
                if not registration.verification_only
                for market in registration.supported_markets
            }
        )
    )


def build_live_provider_router(config: LiveRuntimeConfig) -> ProviderRouter:
    return ProviderRouter(
        build_live_provider_registry(config),
        timezone_name=config.timezone_name,
        freshness_seconds=config.freshness_window_seconds,
        timestamp_future_tolerance_seconds=config.timestamp_future_tolerance_seconds,
        circuit_failure_threshold=config.circuit_failure_threshold,
        circuit_open_seconds=config.circuit_open_seconds,
        reconnect_initial_seconds=config.reconnect_initial_seconds,
        reconnect_max_seconds=config.reconnect_max_seconds,
        reconnect_jitter_seconds=config.reconnect_jitter_seconds,
    )


__all__ = [
    "HistoricalProviderRegistration",
    "HistoricalProviderRegistry",
    "build_historical_provider_registry",
    "build_live_provider_registry",
    "build_live_provider_router",
    "canonical_daily_market_codes",
]
