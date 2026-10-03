"""Internal price-gap diagnostics must not impersonate official status events."""

from dataclasses import replace
from datetime import date, datetime
from uuid import NAMESPACE_URL, uuid5

import pytest

from topicpilot_api.corporate_action_authority import corporate_action_authorities_for
from topicpilot_api.daily_market import build_unavailable_instruments
from topicpilot_api.market_data.exchange import TwseOfficialDailyProvider
from topicpilot_api.market_data.history import INTERNAL_MISSING_PRICE_ORIGIN
from topicpilot_api.market_data.ingestion import (
    _status_payload,
    classify_authoritative_no_trade_result,
)
from topicpilot_api.normalizer.contracts import InputEnvelope, MappingPolicy, ReferenceContext
from topicpilot_api.normalizer.historical import HistoricalDailyBarNormalizer
from topicpilot_api.trading_status_authority import (
    authority_from_official_daily_result,
    read_effective_trading_status_authority,
    resolve_effective_trading_status,
)

DAY = date(2026, 10, 2)
NOW = datetime.fromisoformat("2026-10-02T00:00:00+08:00")
ID = uuid5(NAMESPACE_URL, "synthetic-no-price-id")


def classified_gap():
    from test_target_universe_readiness_replay import payload

    provider = TwseOfficialDailyProvider(
        start_date=DAY,
        end_date=DAY,
        market_batch=True,
        readiness_max_attempts=1,
        transport=lambda _url, _timeout: payload("TPE", ["2330"]),
        clock=lambda: NOW,
    )
    return classify_authoritative_no_trade_result(
        provider.fetch_daily("2601", "TPE"),
        lifecycle_status=None,
        trading_date=DAY,
    )


def normalize(point):
    envelope = InputEnvelope(point, ID, ID, ID, ID, NOW, NOW, NOW, "synthetic-test-only")
    reference = ReferenceContext("synthetic-test", "Asia/Taipei", "REGULAR", "TW_MARKET", "TWD", 2)
    return HistoricalDailyBarNormalizer()(envelope, reference, MappingPolicy())


def canonical_row(symbol="2601", origin=INTERNAL_MISSING_PRICE_ORIGIN):
    result = normalize(_status_payload(classified_gap(), DAY))
    status = next(c for c in result.candidates if c.family_code == "TRADING_STATUS")
    context = dict(status.values["status_context"])
    if origin is None:
        context.pop("authorityOrigin")
    else:
        context["authorityOrigin"] = origin
    return {
        "instrument_id": ID,
        "symbol": symbol,
        "market": "TPE",
        "close": None,
        "status_observation_id": ID,
        "status_code": "UNKNOWN",
        "status_source": "TWSE_OFFICIAL_DAILY",
        "status_reason": status.values["status_reason"],
        "status_context": context,
    }


def test_classifier_origin_is_explicit_idempotent_and_never_a_no_trade_exemption():
    result = classified_gap()
    assert result.instrument_status == "UNKNOWN"
    assert result.status_authority_origin == INTERNAL_MISSING_PRICE_ORIGIN
    assert result.covered_no_trade is False
    assert result.bars == ()
    assert (
        classify_authoritative_no_trade_result(
            result,
            lifecycle_status=None,
            trading_date=DAY,
        )
        == result
    )
    assert authority_from_official_daily_result(result, trading_date=DAY) is None


def test_origin_survives_mapper_existing_json_context_without_price_creation():
    result = normalize(_status_payload(classified_gap(), DAY))
    assert result.failures == ()
    price, status = result.candidates
    assert price.quality_state == "INCOMPLETE"
    assert all(price.values[key] is None for key in ("open", "high", "low", "close"))
    assert status.values["status_code"] == "UNKNOWN"
    assert status.values["status_context"]["authorityOrigin"] == INTERNAL_MISSING_PRICE_ORIGIN
    assert status.values["status_context"]["coverageMeaning"] == "UNEXPLAINED_MISSING"


def test_existing_corporate_authority_is_reached_after_tagged_status_roundtrip():
    item = build_unavailable_instruments([canonical_row()], trade_date=DAY)[0]
    assert item.status == "SUSPENDED"
    assert item.source == "TWSE_OFFICIAL_REDUCTION"
    assert item.reason_code == "CAPITAL_REDUCTION_TRADING_SUSPENSION"
    assert item.is_legitimate_unavailable is True
    assert item.blocks_formal_publication is False


def test_tag_without_independent_authority_remains_missing_and_blocking():
    item = build_unavailable_instruments([canonical_row("2330")], trade_date=DAY)[0]
    assert item.status == "MISSING_MARKET_DATA"
    assert item.is_legitimate_unavailable is False
    assert item.blocks_formal_publication is True


@pytest.mark.parametrize("origin", [None, "UNKNOWN_ORIGIN", {"malformed": True}])
def test_legacy_or_unrecognized_origin_unknown_is_not_reinterpreted(origin):
    item = build_unavailable_instruments([canonical_row(origin=origin)], trade_date=DAY)[0]
    assert item.status == "UNKNOWN"
    assert item.blocks_formal_publication is True
    assert item.is_legitimate_unavailable is False


@pytest.mark.parametrize(
    "symbol,origin,provider_failed,status",
    [
        ("2601", INTERNAL_MISSING_PRICE_ORIGIN, False, "SUSPENDED"),
        ("2330", INTERNAL_MISSING_PRICE_ORIGIN, False, "MISSING_MARKET_DATA"),
        ("2330", INTERNAL_MISSING_PRICE_ORIGIN, True, "PROVIDER_ERROR"),
        ("2601", None, False, "UNKNOWN"),
    ],
)
def test_operator_read_model_and_formal_read_model_share_boundary(
    monkeypatch,
    symbol,
    origin,
    provider_failed,
    status,
):
    import topicpilot_api.daily_market as daily
    import topicpilot_api.trading_status_authority as authority

    monkeypatch.setattr(
        daily,
        "read_daily_market_rows",
        lambda *_args, **_kwargs: [
            canonical_row(symbol, origin),
        ],
    )
    monkeypatch.setattr(authority, "_lifecycle_records", lambda *_args, **_kwargs: {})
    rows = read_effective_trading_status_authority(
        object(),
        DAY,
        expected_instrument_ids=(ID,),
        provider_failure_instrument_ids=(ID,) if provider_failed else (),
    )
    assert rows[0]["resolvedStatus"] == status
    assert rows[0]["blocksPublication"] is (status != "SUSPENDED")


def test_genuine_explicit_provider_unknown_still_overrides_lower_priority_corporate_record():
    original = replace(
        classified_gap(),
        status_authority_origin=None,
        status_reason="explicit unsupported provider status",
    )
    classified = classify_authoritative_no_trade_result(
        original,
        lifecycle_status=None,
        trading_date=DAY,
    )
    assert classified == original
    daily = authority_from_official_daily_result(classified, trading_date=DAY)
    assert daily is not None
    corporate = tuple(
        a.to_trading_status_record()
        for a in corporate_action_authorities_for(
            symbol="2601",
            market="TPE",
            trading_date=DAY,
        )
    )
    decision = resolve_effective_trading_status(ID, DAY, official_authority=(*corporate, daily))
    assert decision.status == "UNKNOWN"
    assert decision.blocks_publication is True


@pytest.mark.parametrize(
    "origin,status",
    [
        ("UNKNOWN_ORIGIN", "UNKNOWN"),
        (INTERNAL_MISSING_PRICE_ORIGIN, "SUSPENDED"),
        (INTERNAL_MISSING_PRICE_ORIGIN, "NO_TRADE"),
        (INTERNAL_MISSING_PRICE_ORIGIN, "AVAILABLE"),
    ],
)
def test_invalid_origin_cannot_grant_price_or_status_eligibility(origin, status):
    point = _status_payload(classified_gap(), DAY)
    point.update(status_authority_origin=origin, instrument_status=status)
    result = normalize(point)
    assert result.candidates == ()
    assert [f.code for f in result.failures] == ["INVALID_STATUS_AUTHORITY_ORIGIN"]


def test_existing_lifecycle_resolution_does_not_carry_internal_unknown_origin():
    classified = classify_authoritative_no_trade_result(
        classified_gap(),
        lifecycle_status="SUSPENDED",
        trading_date=DAY,
    )
    assert classified.instrument_status == "SUSPENDED"
    assert classified.status_authority_origin is None
    assert normalize(_status_payload(classified, DAY)).failures == ()
