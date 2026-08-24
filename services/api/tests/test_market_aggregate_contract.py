from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from topicpilot_api.market_data.aggregate_contract import (
    fetch_official_market_aggregates,
    parse_tpex_market_aggregate,
    parse_twse_market_aggregate,
)

FIXTURES = Path(__file__).parent / "fixtures" / "market_aggregate"
AS_OF = datetime(2026, 8, 21, 16, tzinfo=UTC)


def _fixture(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_twse_official_aggregate_normalizes_turnover_breadth_and_limits():
    result = parse_twse_market_aggregate(
        _fixture("twse_mi_index_daily_valid.json"), retrieved_at=AS_OF, as_of=AS_OF
    )

    assert result.market == "TPE"
    assert result.trading_date == date(2026, 8, 21)
    assert result.turnover == 711182569693
    assert (result.advancers, result.decliners, result.unchanged) == (589, 381, 104)
    assert (result.limit_up_count, result.limit_down_count) == (14, 2)
    assert result.data_status == "AVAILABLE"


def test_tpex_official_daily_quotes_normalizes_stock_breadth_and_keeps_limits_null():
    result = parse_tpex_market_aggregate(
        _fixture("tpex_daily_quotes_valid.json"), retrieved_at=AS_OF, as_of=AS_OF
    )

    assert result.market == "TWO"
    assert result.turnover == 198448672072
    assert (result.advancers, result.decliners, result.unchanged) == (1, 1, 1)
    assert result.eligible == 5
    assert result.observed == 3
    assert result.limit_up_count is None
    assert result.limit_down_count is None
    assert result.status_reason == "TPEX_LIMIT_COUNTS_NOT_PUBLISHED_BY_DAILY_QUOTES"


def test_official_aggregate_fetch_fails_closed_per_market():
    def transport(url: str, timeout: float) -> bytes:
        if "twse.com.tw" in url:
            return json.dumps(
                _fixture("twse_mi_index_daily_valid.json"), ensure_ascii=False
            ).encode()
        return b"{}"

    results = fetch_official_market_aggregates(
        target_date=date(2026, 8, 21),
        retrieved_at=AS_OF,
        as_of=AS_OF,
        transport=transport,
    )

    assert results[0].data_status == "AVAILABLE"
    assert results[1].data_status == "UNAVAILABLE"
    assert results[1].status_reason == "INVALID_DATE"
