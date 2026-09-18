from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from topicpilot_api.home_v2_publication import build_market_signals
from topicpilot_api.market_data.institutional_flow import (
    FlowAvailability,
    FlowFreshness,
    InstitutionalFlowLeg,
    build_market_institutional_flow_trend,
    build_price_flow_relation,
    fetch_official_market_institutional_flows,
    parse_tpex_institutional_flow,
    parse_twse_institutional_flow,
    resolve_freshness,
    to_home_institutional_flow_payload,
)
from topicpilot_api.market_data.institutional_flow_persistence import decide_upsert

FIXTURES = Path(__file__).parent / "fixtures" / "institutional_flow"
RETRIEVED_AT = datetime(2026, 9, 15, 14, 0, tzinfo=UTC)
SESSION = date(2026, 9, 15)


def fixture(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_twse_bfi82u_parser_preserves_official_twd_whole_yuan_semantics() -> None:
    fact = parse_twse_institutional_flow(
        fixture("twse_bfi82u_valid.json"),
        retrieved_at=RETRIEVED_AT,
        target_date=SESSION,
    )

    assert fact.market == "TPE"
    assert fact.availability is FlowAvailability.AVAILABLE
    assert fact.source_dataset == "fund.BFI82U"
    assert fact.foreign and fact.foreign.net == Decimal("-300")
    assert fact.dealer and fact.dealer.net == Decimal("0")
    assert fact.total and fact.total.net == Decimal("-200")
    assert fact.total.unit == "TWD"
    assert fact.total.scale == 0
    assert fact.published_at is None


def test_tpex_openapi_parser_handles_roc_date_and_reconciles_total() -> None:
    fact = parse_tpex_institutional_flow(
        fixture("tpex_3insti_summary_valid.json"),
        retrieved_at=RETRIEVED_AT,
        target_date=SESSION,
    )

    assert fact.market == "TWO"
    assert fact.trading_date == SESSION
    assert fact.availability is FlowAvailability.AVAILABLE
    assert fact.source_dataset == "tpex_3insti_summary"
    assert fact.foreign and fact.foreign.net == Decimal("-300")
    assert fact.total and fact.total.buy == Decimal("1400")


def test_parsers_fail_closed_for_missing_fields_and_reconciliation_errors() -> None:
    payload = fixture("twse_bfi82u_valid.json")
    assert isinstance(payload, dict)
    payload["data"] = payload["data"][:-1]
    missing = parse_twse_institutional_flow(payload, retrieved_at=RETRIEVED_AT, target_date=SESSION)
    assert missing.availability is FlowAvailability.INGESTION_FAILED
    assert missing.status_reason == "MISSING_PROVIDER_FIELD"

    invalid = fixture("twse_bfi82u_valid.json")
    invalid["data"][-1][-1] = "-201"
    mismatch = parse_twse_institutional_flow(
        invalid, retrieved_at=RETRIEVED_AT, target_date=SESSION
    )
    assert mismatch.availability is FlowAvailability.INGESTION_FAILED
    assert mismatch.status_reason == "NET_MISMATCH"


def test_not_yet_published_and_market_independent_fetch_are_explicit() -> None:
    not_published = parse_twse_institutional_flow(
        {"stat": "目前尚無資料"},
        retrieved_at=RETRIEVED_AT,
        target_date=SESSION,
    )
    assert not_published.availability is FlowAvailability.NOT_YET_PUBLISHED

    responses = {
        "twse": fixture("twse_bfi82u_valid.json"),
        "tpex": fixture("tpex_3insti_summary_valid.json"),
    }

    def transport(url: str, timeout: float) -> bytes:
        del timeout
        return json.dumps(
            responses["twse" if "twse.com.tw" in url else "tpex"], ensure_ascii=False
        ).encode()

    facts = fetch_official_market_institutional_flows(
        target_date=SESSION,
        retrieved_at=RETRIEVED_AT,
        transport=transport,
    )
    assert [fact.market for fact in facts] == ["TPE", "TWO"]
    assert all(fact.availability is FlowAvailability.AVAILABLE for fact in facts)

    non_trading = fetch_official_market_institutional_flows(
        target_date=SESSION,
        retrieved_at=RETRIEVED_AT,
        transport=transport,
        trading_day_by_market={"TPE": False, "TWO": True},
    )
    assert non_trading[0].availability is FlowAvailability.NON_TRADING_DAY
    assert non_trading[1].availability is FlowAvailability.AVAILABLE

    def failing_transport(url: str, timeout: float) -> bytes:
        del url, timeout
        raise OSError("offline")

    unavailable = fetch_official_market_institutional_flows(
        target_date=SESSION,
        retrieved_at=RETRIEVED_AT,
        transport=failing_transport,
    )
    assert all(fact.availability is FlowAvailability.SOURCE_UNAVAILABLE for fact in unavailable)


def test_freshness_and_price_flow_relation_never_infer_missing_as_neutral() -> None:
    assert resolve_freshness(SESSION, RETRIEVED_AT, as_of_date=SESSION) is FlowFreshness.CURRENT
    assert (
        resolve_freshness(SESSION - timedelta(days=1), RETRIEVED_AT, as_of_date=SESSION)
        is FlowFreshness.STALE
    )
    assert resolve_freshness(SESSION, None, as_of_date=SESSION) is FlowFreshness.UNKNOWN
    assert (
        build_price_flow_relation(
            market="TPE", index_change=None, flow_net=Decimal("0")
        ).direction_relation
        == "UNKNOWN"
    )
    assert (
        build_price_flow_relation(
            market="TPE", index_change=Decimal("1"), flow_net=Decimal("-1")
        ).direction_relation
        == "DIVERGENCE"
    )
    assert (
        build_price_flow_relation(
            market="TPE", index_change=Decimal("-1"), flow_net=Decimal("-1")
        ).direction_relation
        == "ALIGNED_NEGATIVE"
    )
    assert (
        build_price_flow_relation(
            market="TPE", index_change=Decimal("0"), flow_net=Decimal("1")
        ).direction_relation
        == "NO_DIRECTION"
    )


def test_trend_windows_streaks_acceleration_and_home_serialization() -> None:
    base = parse_twse_institutional_flow(
        fixture("twse_bfi82u_valid.json"),
        retrieved_at=RETRIEVED_AT,
        target_date=SESSION,
    )
    facts = [
        replace(
            base,
            trading_date=SESSION - timedelta(days=index),
            source_as_of=RETRIEVED_AT - timedelta(days=index),
        )
        for index in range(20)
    ]
    trend = build_market_institutional_flow_trend(
        facts,
        market="TPE",
        as_of_date=SESSION,
        index_change=Decimal("1"),
    )
    assert trend.current and trend.current.trading_date == SESSION
    assert trend.previous and trend.previous.trading_date == SESSION - timedelta(days=1)
    assert trend.rolling_5_session.complete
    assert trend.rolling_20_session.complete
    assert trend.streaks["foreign"] == {"direction": "SELL", "sessions": 20}
    assert trend.acceleration["available"] is True
    assert trend.price_flow_relation.direction_relation == "DIVERGENCE"

    home = to_home_institutional_flow_payload(
        facts,
        index_changes={"TPE": Decimal("1"), "TWO": None},
        as_of_date=SESSION,
    )
    assert home and home["status"] == "PARTIAL"
    assert home["unit"] == "TWD"
    assert home["markets"][0]["current"]["total"]["value"] == -200


def test_zero_streak_resets_and_upsert_conflicts_are_deterministic() -> None:
    base = parse_twse_institutional_flow(
        fixture("twse_bfi82u_valid.json"),
        retrieved_at=RETRIEVED_AT,
        target_date=SESSION,
    )
    zero_total = replace(
        base,
        total=InstitutionalFlowLeg(Decimal("0"), Decimal("0"), Decimal("0")),
    )
    trend = build_market_institutional_flow_trend(
        [base, zero_total], market="TPE", as_of_date=SESSION
    )
    assert trend.streaks["total"] == {"direction": "SELL", "sessions": 1}

    existing = SimpleNamespace(
        response_content_hash="old",
        source_as_of=RETRIEVED_AT,
        availability=FlowAvailability.AVAILABLE.value,
    )
    assert decide_upsert(existing, base) == "REJECTED_DUPLICATE_SOURCE_VERSION"
    newer = replace(base, source_as_of=RETRIEVED_AT + timedelta(minutes=1))
    assert decide_upsert(existing, newer) == "UPDATED"
    older_unavailable = replace(
        base,
        availability=FlowAvailability.SOURCE_UNAVAILABLE,
        source_as_of=RETRIEVED_AT + timedelta(minutes=2),
    )
    assert decide_upsert(existing, older_unavailable) == "PRESERVED_AVAILABLE"


def test_today_signal_adapter_consumes_formal_nested_flow_without_changing_label_policy() -> None:
    signals = build_market_signals(
        {
            "indices": [
                {"market": "TPE", "status": "AVAILABLE", "change": 1},
                {"market": "TWO", "status": "AVAILABLE", "change": 0.2},
            ],
            "institutionFlows": {
                "markets": [
                    {
                        "market": "TPE",
                        "availability": "AVAILABLE",
                        "current": {
                            "availability": "AVAILABLE",
                            "foreign": {"net": -300, "value": -300, "status": "AVAILABLE"},
                        },
                    }
                ]
            },
        }
    )
    assert [signal["key"] for signal in signals] == ["INSTITUTION_PRICE_DIVERGENCE"]
