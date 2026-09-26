from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal

from topicpilot_api.market_data.institutional_flow_contract import (
    fetch_official_market_institutional_flows,
    parse_tpex_institutional_flow,
    parse_twse_institutional_flow,
)

AS_OF = datetime(2026, 8, 21, 16, tzinfo=UTC)


def _payload(date_value: str = "20260821") -> dict[str, object]:
    return {
        "date": date_value,
        "tables": [
            {
                "title": "三大法人買賣金額彙總表",
                "data": [
                    ["外資及陸資合計", "61,148,148,214", "64,136,352,440", "-2,988,204,226"],
                    [
                        "　外資及陸資(不含自營商)",
                        "61,148,148,214",
                        "64,136,352,440",
                        "-2,988,204,226",
                    ],
                    ["投信", "2,784,757,015", "6,200,779,571", "-3,416,022,556"],
                    ["自營商合計", "5,944,867,710", "5,732,056,289", "212,811,421"],
                    ["三大法人合計*", "69,877,772,939", "76,069,188,300", "-6,191,415,361"],
                ],
            }
        ],
    }


def _twse_payload(date_value: str = "20260821") -> dict[str, object]:
    return {
        "date": date_value,
        "data": [
            ["自營商(自行買賣)", "1,924,532,074", "1,772,515,889", "152,016,185"],
            ["自營商(避險)", "4,020,335,636", "3,959,540,400", "60,795,236"],
            ["投信", "2,784,757,015", "6,200,779,571", "-3,416,022,556"],
            ["外資及陸資(不含外資自營商)", "61,148,148,214", "64,136,352,440", "-2,988,204,226"],
            ["外資自營商", "0", "0", "0"],
            ["合計", "69,877,772,939", "76,069,188,300", "-6,191,415,361"],
        ],
    }


def test_twse_institutional_flow_parser_normalizes_formal_values():
    result = parse_twse_institutional_flow(
        _twse_payload(), retrieved_at=AS_OF, as_of=AS_OF
    )

    assert result.market == "TPE"
    assert result.trading_date == date(2026, 8, 21)
    assert result.availability == "AVAILABLE"
    assert result.unit == "TWD"
    assert result.foreign_net == Decimal("-2988204226")
    assert result.investment_trust_net == Decimal("-3416022556")
    assert result.dealer_net == Decimal("212811421")
    assert result.total_net == Decimal("-6191415361")


def test_tpex_institutional_flow_parser_accepts_roc_table_date_when_needed():
    payload = _payload()
    payload["date"] = "115/08/21"
    result = parse_tpex_institutional_flow(payload, retrieved_at=AS_OF, as_of=AS_OF)

    assert result.market == "TWO"
    assert result.trading_date == date(2026, 8, 21)
    assert result.source_identity == "TPEX_INSTI_SUMMARY"


def test_institutional_flow_fetch_is_date_bound_and_fails_closed_per_market():
    def transport(url: str, timeout: float) -> bytes:
        if "twse.com.tw" in url:
            return json.dumps(_twse_payload()).encode()
        return json.dumps(_payload("20260820")).encode()

    results = fetch_official_market_institutional_flows(
        target_date=date(2026, 8, 21),
        retrieved_at=AS_OF,
        as_of=AS_OF,
        transport=transport,
    )

    assert results[0].availability == "AVAILABLE"
    assert results[1].availability == "SOURCE_UNAVAILABLE"
    assert results[1].trading_date == date(2026, 8, 21)
    assert results[1].status_reason == "PROVIDER_DATE_MISMATCH"


def test_institutional_flow_fetch_keeps_provider_failure_as_targeted_unavailable():
    def transport(url: str, timeout: float) -> bytes:
        raise OSError("provider unavailable")

    results = fetch_official_market_institutional_flows(
        target_date=date(2026, 8, 21),
        retrieved_at=AS_OF,
        as_of=AS_OF,
        transport=transport,
    )

    assert [result.availability for result in results] == [
        "SOURCE_UNAVAILABLE",
        "SOURCE_UNAVAILABLE",
    ]
    assert all(result.trading_date == date(2026, 8, 21) for result in results)
