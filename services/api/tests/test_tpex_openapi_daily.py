"""Independent synthetic fixtures; no real price history or production writes."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from urllib.error import URLError

import pytest

from topicpilot_api.comparator import COMPARATOR_PROVIDER_VERSION_BY_MARKET
from topicpilot_api.corporate_action_authority import corporate_action_authorities_for
from topicpilot_api.market_data.exchange import (
    TPEX_OPENAPI_DAILY_ADAPTER_VERSION,
    TPEX_OPENAPI_DAILY_ENDPOINT,
    TpexOfficialDailyProvider,
    TpexOpenApiDailyProvider,
)
from topicpilot_api.market_data.history import HistoricalProviderError
from topicpilot_api.market_data.receipt import ResponseBytes, read_json_receipt
from topicpilot_api.market_data.registry import build_historical_provider_registry
from topicpilot_api.previous_close_authority import G2PriceEvidence, PreviousCloseEvidence
from topicpilot_api.provider_preflight import (
    EXCHANGE_CODE_BY_MARKET,
    PROVIDER_AUTHORITY_BY_MARKET,
    PROVIDER_VERSION_BY_MARKET,
    G2MarketContext,
    G2MarketFetch,
    G2PreflightContext,
    evaluate_provider_preflight,
)
from topicpilot_api.trading_status_authority import resolve_effective_trading_status

DAY = date(2026, 10, 2)
PRIOR = date(2026, 10, 1)


def row(code="7000", **changes):
    return {
        "Date": "1151002", "SecuritiesCompanyCode": code, "CompanyName": "Synthetic fixture",
        "Open": "100", "High": "105", "Low": "99", "Close": "104",
        "TradingShares": "3,000", "Change": "+4", "NextReferencePrice": "104",
        **changes,
    }


def response(payload):
    raw = ResponseBytes(json.dumps(payload, ensure_ascii=False).encode())
    raw.http_status = 200
    return raw


def provider(payload, calls=None, **changes):
    def transport(url, _timeout):
        if calls is not None:
            calls.append(url)
        return response(payload)

    return TpexOpenApiDailyProvider(
        start_date=DAY, end_date=DAY, transport=transport,
        clock=lambda: datetime(2026, 10, 2, 9, tzinfo=UTC),
        readiness_max_attempts=1, **changes,
    )


def test_openapi_exact_date_mapping_receipt_volume_and_single_request_cache():
    payload = [row(), row("7001")]
    calls = []
    adapter = provider(payload, calls)
    first = adapter.fetch_daily("7000", "TWO")
    second = adapter.fetch_daily("7001", "TWO")
    assert calls == [TPEX_OPENAPI_DAILY_ENDPOINT]  # No invented date query.
    assert first.source_code == "TPEX_OFFICIAL_DAILY"
    assert first.adapter_version == TPEX_OPENAPI_DAILY_ADAPTER_VERSION
    assert first.bars == second.bars
    bar = first.bars[0]
    assert (bar.trading_date, bar.close, bar.volume) == (DAY, Decimal("104"), Decimal("3000"))
    assert (bar.open, bar.high, bar.low) == (Decimal("100"), Decimal("105"), Decimal("99"))
    assert bar.previous_close is None  # Neither Change nor NextReferencePrice is a comparator.
    evidence = adapter.response_evidence
    assert evidence["endpoint"] == TPEX_OPENAPI_DAILY_ENDPOINT
    assert evidence["httpStatus"] == 200
    assert evidence["payloadHash"] == sha256(response(payload)).hexdigest()
    assert evidence["payloadSize"] == len(response(payload))
    assert evidence["rawResponseDates"] == ["1151002"]
    assert evidence["responseDate"] == "20261002"
    assert evidence["targetDate"] == DAY.isoformat()
    assert evidence["adapterVersion"] == TPEX_OPENAPI_DAILY_ADAPTER_VERSION
    assert evidence["rawStatus"] is None  # OpenAPI did not report an OK status.


@pytest.mark.parametrize("payload", [
    [row(Date="1151001")], [row(Date="1151005")], [row(Date="20261002")],
    [row(Date=None)], [row(), row("7001", Date="1151001")],
])
def test_wrong_or_mixed_snapshot_date_is_terminal_not_retagged_or_filled(payload):
    calls = []
    adapter = provider(payload, calls)
    for code in ("7000", "7001"):
        with pytest.raises(HistoricalProviderError, match="PROVIDER_DATE_MISMATCH"):
            adapter.fetch_daily(code, "TWO")
    assert calls == [TPEX_OPENAPI_DAILY_ENDPOINT]
    assert adapter.response_evidence["responseDate"] is None
    assert adapter.readiness_retry_count == 0


@pytest.mark.parametrize("payload", [{"stat": "ok", "date": "20261002"}, [None], [{}], ["row"]])
def test_schema_changes_fail_closed(payload):
    with pytest.raises(HistoricalProviderError, match="INVALID_PAYLOAD"):
        provider(payload).fetch_market_day()


def test_array_support_does_not_relax_existing_object_provider_boundary():
    with pytest.raises(HistoricalProviderError, match="response must be an object"):
        read_json_receipt(lambda *_: response([row()]), "https://test.example/object", 5, {})


def test_duplicate_instrument_is_not_last_row_wins():
    with pytest.raises(HistoricalProviderError, match="DUPLICATE_INSTRUMENT_ROW"):
        provider([row(), row(Close="103")]).fetch_market_day()


@pytest.mark.parametrize("identity", [None, 7000, "", "bad/code"])
def test_invalid_instrument_identity_fails_closed(identity):
    with pytest.raises(HistoricalProviderError, match="INVALID_IDENTITY"):
        provider([row(SecuritiesCompanyCode=identity)]).fetch_market_day()


@pytest.mark.parametrize("value", [None, "", "--", "---"])
def test_missing_prices_remain_null_no_ohlc_or_close_fill(value):
    result = provider([row(Open=value, High=value, Low=value, Close=value)]).fetch_daily(
        "7000", "TWO"
    )
    bar = result.bars[0]
    assert (bar.open, bar.high, bar.low, bar.close, bar.previous_close) == (None,) * 5


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-1", "price"])
def test_invalid_numeric_price_is_rejected(value):
    with pytest.raises(HistoricalProviderError, match="INVALID_NUMBER"):
        provider([row(Close=value)]).fetch_market_day()


def test_absent_instrument_returns_no_price_not_synthetic_history():
    result = provider([row()]).fetch_daily("7001", "TWO")
    assert result.bars == () and result.instrument_status == "EXCHANGE_CONFIRMED_NO_DATA"


def test_transport_failure_is_cached_without_legacy_endpoint_or_retry():
    calls = []

    def transport(url, _timeout):
        calls.append(url)
        raise URLError("controlled transport failure")

    adapter = TpexOpenApiDailyProvider(start_date=DAY, end_date=DAY, transport=transport)
    for code in ("7000", "7001"):
        with pytest.raises(HistoricalProviderError, match="PROVIDER_REQUEST_FAILED"):
            adapter.fetch_daily(code, "TWO")
    assert calls == [TPEX_OPENAPI_DAILY_ENDPOINT]
    assert adapter.response_evidence["classification"] == "PROVIDER_TRANSPORT_FAILURE"
    assert adapter.readiness_retry_count == 0


def test_empty_payload_cannot_supply_prices():
    with pytest.raises(HistoricalProviderError, match="EXCHANGE_EMPTY_PAYLOAD"):
        provider([]).fetch_market_day()


def test_multi_day_window_cannot_fall_back_to_monthly_history():
    calls = []
    adapter = TpexOpenApiDailyProvider(
        start_date=PRIOR, end_date=DAY, transport=lambda url, _: calls.append(url),
    )
    with pytest.raises(HistoricalProviderError, match="MARKET_BATCH_DATE_WINDOW"):
        adapter.fetch_daily("7000", "TWO")
    assert calls == []


def test_registry_uses_date_addressable_official_source_for_normal_and_comparator_lineage():
    normal = build_historical_provider_registry(start_date=DAY, end_date=DAY, market_batch=True)
    prior = build_historical_provider_registry(
        start_date=PRIOR, end_date=PRIOR, market_batch=True, tpex_target_date_batch=True,
    )
    history = build_historical_provider_registry(start_date=PRIOR, end_date=DAY)
    for registry in (normal, prior, history):
        adapter = registry.for_market("TWO")[0].adapter
        assert type(adapter) is TpexOfficialDailyProvider
        assert adapter.adapter_version == COMPARATOR_PROVIDER_VERSION_BY_MARKET["TWO"]
    assert COMPARATOR_PROVIDER_VERSION_BY_MARKET["TWO"] == "tpex-official-daily.v2"
    assert normal.for_market("TWO")[0].adapter.adapter_version == PROVIDER_VERSION_BY_MARKET["TWO"]
    assert not any(item.verification_only for item in normal.for_market("TWO"))


def gate(*, changes=None, omit=None, prior_changes=None, status_kind="official"):
    """Real registry/adapter -> unchanged G2 with exact-prior synthetic authority."""
    codes = {"TPE": (*[str(6000 + i) for i in range(346)], "2601"),
             "TWO": tuple(str(7000 + i) for i in range(206))}
    tpex_fields = [
        "代號", "名稱", "收盤", "漲跌", "開盤", "最高", "最低", "均價", "成交股數",
        "成交金額(元)", "成交筆數", "最後買價", "最後買量(張數)", "最後賣價",
        "最後賣量(張數)", "發行股數", "次日參考價", "次日漲停價", "次日跌停價",
    ]

    def tpex_row(code):
        value = row(code, **(changes or {})) if code == "7000" else row(code)
        return [
            value["SecuritiesCompanyCode"], value["CompanyName"], value["Close"], value["Change"],
            value["Open"], value["High"], value["Low"], value.get("Average", "50"),
            value["TradingShares"], "0", "0", "0", "0", "0", "0", "0",
            value["NextReferencePrice"], "0", "0",
        ]

    payloads = {
        "TPE": {"stat": "OK", "date": "20261002", "tables": [{"fields": ["證券代號"],
                "data": [[c, "Synthetic fixture", "1000", "1", "100000", "100", "105", "99", "104"]
                         for c in codes["TPE"] if c != "2601"]}]},
        "TWO": {"stat": "ok", "date": "20261002", "tables": [{
            "title": "上櫃股票行情", "fields": tpex_fields,
            "data": [tpex_row(c) for c in codes["TWO"] if c != omit],
        }]},
    }
    registry = build_historical_provider_registry(
        start_date=DAY, end_date=DAY, market_batch=True,
        exchange_transport=lambda url, _: response(payloads["TPE" if "MI_INDEX" in url else "TWO"]),
    )
    contexts, results = [], {}
    for market, expected in codes.items():
        registration = registry.for_market(market)[0]
        contexts.append(G2MarketContext(
            market, registration.code, registration.adapter.adapter_version,
            EXCHANGE_CODE_BY_MARKET[market], "Asia/Taipei", "TW_MARKET", expected,
            {c: f"{market}:{c}" for c in expected},
        ))
        _, bars = registration.adapter.fetch_market_day()
        prices = {}
        for code, bar in bars.items():
            prior = PreviousCloseEvidence(
                instrument_id=f"{market}:{code}", market_code=market, instrument_code=code,
                as_of_date=PRIOR, value=Decimal("100"), source=PROVIDER_AUTHORITY_BY_MARKET[market],
                authority="FORMAL_CANONICAL_CLOSE", lineage=f"synthetic-prior:{market}:{code}",
            )
            if code == "7000" and prior_changes:
                prior = replace(prior, **prior_changes)
            prices[code] = G2PriceEvidence(
                f"{market}:{code}", market, code, bar.trading_date, bar.close,
                registration.adapter.response_evidence["payloadHash"], formal_previous=prior,
            )
        statuses = {}
        if market == "TPE":
            authority = tuple(
                a.to_trading_status_record() for a in corporate_action_authorities_for(
                    symbol="2601", market="TPE", trading_date=DAY,
                )
            )
            statuses["TPE:2601"] = resolve_effective_trading_status(
                "TPE:2601", DAY, official_authority=authority if status_kind == "official" else (),
            )
        results[market] = G2MarketFetch(
            market, registration.code, registration.adapter.adapter_version,
            DAY, frozenset(bars), len(bars), prices=prices, statuses=statuses,
        )
    context = G2PreflightContext(
        {"referenceLoadStatus": "READY"}, DAY, True, None, tuple(contexts), previous_session=PRIOR,
    )
    return evaluate_provider_preflight(context, results)


def test_real_openapi_206_prices_and_2601_precedence_account_for_all_553():
    result = gate()
    assert result["status"] == "PASS"
    tpe, two = result["markets"]
    assert (tpe["priceCandidateCount"], tpe["legitimateUnavailableCount"]) == (346, 1)
    assert (two["priceCandidateCount"], two["previousCloseCoveredCount"]) == (206, 206)
    assert sum(m["accountedTargetCount"] for m in result["markets"]) == 553
    assert all(d["previousClose"]["asOfDate"] == PRIOR.isoformat()
               for d in two["instrumentDecisions"])


@pytest.mark.parametrize("changes", [{"Close": "0", "Low": "0"}, {"Close": None}, {"Close": ""}])
def test_zero_or_missing_close_does_not_pass_g2_using_prior_price(changes):
    assert gate(changes=changes)["status"] == "FAIL"


@pytest.mark.parametrize("prior_changes", [
    {"value": None}, {"value": 0}, {"instrument_id": "wrong"},
    {"as_of_date": date(2026, 9, 30)}, {"lineage": ""}, {"source": "SHADOW"},
])
def test_previous_close_authority_requirements_are_unchanged(prior_changes):
    assert gate(prior_changes=prior_changes)["status"] == "FAIL"


def test_missing_target_and_unknown_status_still_block_g2():
    assert gate(omit="7000")["status"] == "FAIL"
    assert gate(status_kind="unknown")["status"] == "FAIL"
