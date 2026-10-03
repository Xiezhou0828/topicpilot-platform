"""Exercise comparator preparation through the real registry and parsers."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from hashlib import sha256
from uuid import NAMESPACE_URL, uuid5

import pytest

import topicpilot_api.comparator as comparator
from topicpilot_api.market_data.exchange import (
    TpexOfficialDailyProvider,
    TwseOfficialDailyProvider,
)
from topicpilot_api.market_data.history import HistoricalProviderError
from topicpilot_api.market_data.receipt import ResponseBytes
from topicpilot_api.market_data.registry import build_historical_provider_registry
from topicpilot_api.provider_preflight import (
    EXCHANGE_CODE_BY_MARKET,
    PROVIDER_AUTHORITY_BY_MARKET,
    PROVIDER_VERSION_BY_MARKET,
    G2MarketContext,
    G2PreflightContext,
)

PRIOR = date(2026, 10, 1)
TARGET = date(2026, 10, 2)


@pytest.fixture
def real_registry_inputs(monkeypatch):
    codes = {
        "TPE": (*(str(6000 + i) for i in range(346)), "2601"),
        "TWO": tuple(str(7000 + i) for i in range(206)),
    }
    markets = tuple(
        G2MarketContext(
            market,
            PROVIDER_AUTHORITY_BY_MARKET[market],
            PROVIDER_VERSION_BY_MARKET[market],
            EXCHANGE_CODE_BY_MARKET[market],
            "Asia/Taipei",
            "TW_MARKET",
            codes[market],
            {
                code: str(uuid5(NAMESPACE_URL, f"test-comparator:{market}:{code}"))
                for code in codes[market]
            },
        )
        for market in ("TPE", "TWO")
    )
    target = G2PreflightContext(
        {"referenceLoadStatus": "READY"},
        TARGET,
        True,
        None,
        markets,
        previous_session=PRIOR,
    )
    prior = replace(target, target_date=PRIOR, previous_session=date(2026, 9, 30))
    monkeypatch.setattr(
        comparator,
        "load_g2_preflight_context",
        lambda _session, *, target_date, reference_version: (
            target if target_date == TARGET else prior
        ),
    )
    status = {
        "instrumentId": markets[0].instrument_ids["2601"],
        "market": "TPE",
        "symbol": "2601",
        "resolvedStatus": "SUSPENDED",
        "authoritySource": "TWSE_OFFICIAL_REDUCTION",
        "reasonCode": "LEGITIMATE_UNAVAILABLE",
        "sourceReference": "official-test-authority",
        "effectiveFrom": date(2026, 9, 22),
        "effectiveTo": date(2026, 10, 5),
        "isLegitimateUnavailable": True,
        "blocksPublication": False,
    }
    monkeypatch.setattr(
        comparator, "read_effective_trading_status_authority", lambda *a, **kw: [status]
    )
    payloads = {
        "TPE": {
            "stat": "OK",
            "date": "20261001",
            "tables": [
                {
                    "fields": ["證券代號"],
                    "data": [
                        [c, "controlled fixture", "1000", "1", "102000", "100", "103", "99", "102"]
                        for c in codes["TPE"]
                        if c != "2601"
                    ],
                }
            ],
        },
        "TWO": {
            "stat": "ok",
            "date": "20261001",
            "tables": [
                {
                    "title": "上櫃股票行情",
                    "fields": ["代號"],
                    "data": [
                        [c, "controlled fixture", "102", "2", "100", "103", "99", "102", "1000"]
                        for c in codes["TWO"]
                    ],
                }
            ],
        },
    }
    calls = []

    def transport(url, timeout):
        market = "TPE" if "/MI_INDEX?" in url else "TWO"
        assert "date=20261001" in url if market == "TPE" else "date=2026%2F10%2F01" in url
        calls.append((market, url))
        result = ResponseBytes(json.dumps(payloads[market], ensure_ascii=False).encode())
        result.http_status = 200
        return result

    return markets, payloads, transport, calls


def test_prepare_comparator_real_registry_full_coverage_and_receipt(real_registry_inputs):
    markets, payloads, transport, calls = real_registry_inputs
    registry = build_historical_provider_registry(start_date=PRIOR, end_date=PRIOR)
    for market in ("TPE", "TWO"):
        registration = registry.for_market(market)[0]
        assert not hasattr(registration, "adapter_version")
        assert registration.adapter.adapter_version == PROVIDER_VERSION_BY_MARKET[market]
    # Do not replace the registry, registration, or adapter with permissive mocks.
    plan = comparator.prepare_comparator(
        object(),
        comparator_date=PRIOR,
        target_date=TARGET,
        reference_version="test",
        transport=transport,
    )
    assert len(plan.points) == 552 and plan.summary()["accountedCount"] == 553
    assert [p["priceCount"] for p in plan.summary()["markets"]] == [346, 206]
    assert [c[0] for c in calls] == ["TPE", "TWO"]
    assert plan.unavailable[0]["symbol"] == "2601"
    assert plan.unavailable[0]["resolvedStatus"] == "SUSPENDED"
    assert plan.unavailable[0]["reasonCode"] == "LEGITIMATE_UNAVAILABLE"
    assert not any(p.code == "2601" for p in plan.points)
    by_market = {m.market_code: m for m in markets}
    for point in plan.points:
        receipt = point.receipt
        assert point.bar.trading_date == PRIOR and point.bar.close > 0
        assert str(point.instrument_id) == by_market[point.market].instrument_ids[point.code]
        assert receipt["responseDate"] == "20261001" and receipt["httpStatus"] == 200
        raw = json.dumps(payloads[point.market], ensure_ascii=False).encode()
        assert receipt["payloadSize"] == len(raw)
        assert receipt["payloadHash"] == sha256(raw).hexdigest()
        assert (
            point.payload()["comparatorProvenance"]["adapterVersion"]
            == (PROVIDER_VERSION_BY_MARKET[point.market])
        )


@pytest.mark.parametrize("adapter", [TwseOfficialDailyProvider, TpexOfficialDailyProvider])
def test_real_adapter_version_mismatch_still_fails_closed(
    real_registry_inputs, monkeypatch, adapter
):
    _, _, transport, _ = real_registry_inputs
    monkeypatch.setattr(adapter, "adapter_version", "wrong-version")
    with pytest.raises(comparator.ComparatorError, match="PROVIDER_AUTHORITY_MISMATCH"):
        comparator.prepare_comparator(
            object(),
            comparator_date=PRIOR,
            target_date=TARGET,
            reference_version="test",
            transport=transport,
        )


@pytest.mark.parametrize("market", ["TPE", "TWO"])
def test_real_comparator_parser_date_mismatch_never_passes(real_registry_inputs, market):
    _, payloads, transport, _ = real_registry_inputs
    payloads[market]["date"] = "20260930"
    with pytest.raises(HistoricalProviderError, match="PROVIDER_DATE_MISMATCH"):
        comparator.prepare_comparator(
            object(),
            comparator_date=PRIOR,
            target_date=TARGET,
            reference_version="test",
            transport=transport,
        )
