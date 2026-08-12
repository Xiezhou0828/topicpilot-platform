from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.contracts import IntradayBar, IntradayFetchResult, LiveProviderError
from topicpilot_api.live.orchestrator import (
    CanonicalResolver,
    ProviderBudget,
    ProviderRegistration,
    ProviderRegistry,
    ProviderRouter,
)
from topicpilot_api.market_data.registry import (
    build_historical_provider_registry,
    build_live_provider_registry,
)
from topicpilot_api.market_data.yahoo_quote import YahooQuoteProvider


def _chart_payload(observed_at: datetime) -> bytes:
    timestamp = int(observed_at.timestamp())
    return json.dumps(
        {
            "chart": {
                "result": [
                    {
                        "meta": {
                            "regularMarketPrice": 100,
                            "regularMarketTime": timestamp,
                            "regularMarketOpen": 99,
                            "regularMarketDayHigh": 101,
                            "regularMarketDayLow": 98,
                            "regularMarketVolume": 1200,
                        }
                    }
                ]
            }
        }
    ).encode("utf-8")


def test_yahoo_quote_adapter_normalizes_v1_fallback_shape():
    urls: list[str] = []
    observed_at = datetime(2026, 8, 10, 2, 0, tzinfo=UTC)
    provider = YahooQuoteProvider(
        transport=lambda url, _timeout: (urls.append(url) or _chart_payload(observed_at)),
        clock=lambda: datetime(2026, 8, 10, 2, 1, tzinfo=UTC),
    )

    result = provider.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 10))

    assert result.source_code == "YAHOO_QUOTE_INTRADAY"
    assert result.source_symbol == "2330.TW"
    assert result.latest is not None
    assert result.latest.close == Decimal("100")
    assert result.latest.source_payload["provider_semantics"] == "V1_YAHOO_QUOTE_FALLBACK"
    assert urls == ["https://query1.finance.yahoo.com/v8/finance/chart/2330.TW?range=1d&interval=1m"]


def test_yahoo_quote_adapter_rejects_stale_session_date():
    provider = YahooQuoteProvider(
        transport=lambda _url, _timeout: _chart_payload(datetime(2026, 8, 7, 5, 30, tzinfo=UTC)),
        clock=lambda: datetime(2026, 8, 10, 2, 1, tzinfo=UTC),
    )

    with pytest.raises(LiveProviderError) as error:
        provider.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 10))

    assert error.value.code == "YAHOO_STALE_QUOTE"


class _TaishinFallbackStub:
    source_code = "TAISHIN_TECH_ANALYSIS_INTRADAY"
    adapter_version = "taishin-tech-analysis-intraday.test"

    def fetch_intraday(self, instrument_code, market_code, *, session_date):
        observed_at = datetime(2026, 8, 10, 2, 0, tzinfo=UTC)
        bar = IntradayBar(
            instrument_code,
            market_code,
            observed_at,
            Decimal("99"),
            Decimal("101"),
            Decimal("98"),
            Decimal("100"),
            Decimal("1000"),
            "5m",
            {"provider_semantics": "TAISHIN_INTRADAY"},
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


def test_yahoo_adapter_failure_routes_to_taishin_slot():
    def failed_transport(_url, _timeout):
        raise OSError("down")

    yahoo = YahooQuoteProvider(transport=failed_transport)
    registry = ProviderRegistry()
    registry.register(
        ProviderRegistration(
            yahoo.source_code,
            yahoo,
            budget=ProviderBudget(cooldown_seconds=0),
            source_rank=10,
        )
    )
    taishin = _TaishinFallbackStub()
    registry.register(ProviderRegistration(taishin.source_code, taishin, source_rank=20))
    router = ProviderRouter(
        registry,
        clock=lambda: datetime(2026, 8, 10, 2, 2, tzinfo=UTC),
        circuit_failure_threshold=1,
        reconnect_initial_seconds=0,
    )

    routed = router.fetch_with_evidence("2330", "TPE", session_date=date(2026, 8, 10))

    assert routed.attempted_providers == ("YAHOO_QUOTE_INTRADAY", "TAISHIN_TECH_ANALYSIS_INTRADAY")
    assert routed.resolution.result.source_code == "TAISHIN_TECH_ANALYSIS_INTRADAY"
    assert router.health["YAHOO_QUOTE_INTRADAY"].failure_count == 1


def test_live_registry_keeps_taishin_visible_when_credentials_are_absent(monkeypatch):
    monkeypatch.delenv("TOPICPILOT_TA_API_USER", raising=False)
    monkeypatch.delenv("TOPICPILOT_TA_API_PASSWORD", raising=False)

    registrations = build_live_provider_registry(LiveRuntimeConfig())

    assert [item.code for item in registrations.all()] == [
        "YAHOO_QUOTE_INTRADAY",
        "TAISHIN_TECH_ANALYSIS_INTRADAY",
    ]
    assert registrations.all()[0].enabled is True
    assert registrations.all()[1].enabled is False


def test_historical_registry_keeps_official_exchange_ownership():
    registry = build_historical_provider_registry(
        start_date=date(2026, 5, 1), end_date=date(2026, 8, 7)
    )

    assert [item.code for item in registry.for_market("TPE")] == ["TWSE_OFFICIAL_DAILY"]
    assert [item.code for item in registry.for_market("TWO")] == ["TPEX_OFFICIAL_DAILY"]
    assert [item.code for item in registry.for_market("TPE", include_verification=True)] == [
        "TWSE_OFFICIAL_DAILY",
        "YAHOO_CHART_DAILY",
    ]


def test_canonical_resolver_rejects_observation_far_after_retrieval():
    provider = _TaishinFallbackStub()
    registration = ProviderRegistration(provider.source_code, provider, source_rank=20)
    result = provider.fetch_intraday("2330", "TPE", session_date=date(2026, 8, 10))
    late = IntradayFetchResult(
        result.instrument_code,
        result.market_code,
        result.source_symbol,
        result.source_code,
        result.adapter_version,
        datetime(2026, 8, 10, 1, 0, tzinfo=UTC),
        result.bars,
    )
    resolver = CanonicalResolver(
        {provider.source_code: registration},
        {provider.source_code: None},
        clock=lambda: datetime(2026, 8, 10, 2, 2, tzinfo=UTC),
        timestamp_future_tolerance_seconds=300,
    )

    with pytest.raises(LiveProviderError) as error:
        resolver.resolve((late,), session_date=date(2026, 8, 10), market_code="TPE")

    assert error.value.code == "NO_VALID_CANONICAL_OBSERVATION"
