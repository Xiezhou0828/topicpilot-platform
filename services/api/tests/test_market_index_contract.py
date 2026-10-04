from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from topicpilot_api.market_data.index_contract import (
    TAIPEI,
    TPEX_MARKET_AGGREGATE_SOURCE_IDENTITY,
    TPEX_MARKET_INDEX_IDENTITY,
    TWSE_MARKET_AGGREGATE_SOURCE_IDENTITY,
    TWSE_MARKET_INDEX_IDENTITY,
    IndexDataStatus,
    fetch_official_market_indexes,
    parse_tpex_index_crosscheck,
    parse_tpex_market_index,
    parse_twse_market_index,
    parse_twse_market_index_ohlc,
    parse_twse_target_date_market_index,
    unavailable_market_index,
)

FIXTURES = Path(__file__).parent / "fixtures" / "market_index"
RETRIEVED_AT = datetime(2026, 8, 14, 16, 0, tzinfo=TAIPEI)
AS_OF = datetime(2026, 8, 14, 16, 0, tzinfo=TAIPEI)


def _fixture(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_twse_maps_exact_taiex_row_and_derives_previous_close_backend_only():
    result = parse_twse_market_index(
        _fixture("twse_mi_index_valid.json"),
        retrieved_at=RETRIEVED_AT,
        as_of=AS_OF,
    )

    assert result.data_status is IndexDataStatus.AVAILABLE
    assert result.market == "TPE"
    assert result.index_identity == TWSE_MARKET_INDEX_IDENTITY
    assert result.source_identity == TWSE_MARKET_AGGREGATE_SOURCE_IDENTITY
    assert result.trading_date.isoformat() == "2026-08-13"
    assert result.raw_provider_date == "1150813"
    assert result.value == Decimal("46021.48")
    assert result.change == Decimal("503.41")
    assert result.change_pct == Decimal("1.11")
    assert result.previous_close == Decimal("45518.07")
    assert result.source_field_path.endswith(".收盤指數")
    assert result.response_content_hash is not None
    assert result.to_dict()["previousClose"] == "45518.07"
    assert not hasattr(result, "turnover")


def test_twse_ignores_non_target_index_rows():
    payload = _fixture("twse_mi_index_valid.json")
    result = parse_twse_market_index(payload, retrieved_at=RETRIEVED_AT, as_of=AS_OF)

    assert result.display_name == "Taiwan Stock Exchange Capitalization Weighted Stock Index"
    assert result.value != Decimal("51102.16")


def test_twse_target_date_report_preserves_official_date_and_provenance():
    result = parse_twse_target_date_market_index(
        _fixture("twse_after_trading_mi_index_target_valid.json"),
        target_date=date(2026, 8, 14),
        retrieved_at=RETRIEVED_AT,
        as_of=AS_OF,
    )

    assert result.data_status is IndexDataStatus.AVAILABLE
    assert result.trading_date == date(2026, 8, 14)
    assert result.raw_provider_date == "20260814"
    assert result.value == Decimal("46021.48")
    assert result.change == Decimal("503.41")
    assert result.previous_close == Decimal("45518.07")
    assert result.change_pct == Decimal("1.11")
    assert result.source_dataset == "afterTrading.MI_INDEX"
    assert result.source_endpoint.startswith("https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX")
    assert result.adapter_version == "twse-official-taiex-index.v3"
    assert result.response_content_hash is not None


def test_twse_target_date_report_mismatch_fails_closed():
    result = parse_twse_target_date_market_index(
        _fixture("twse_after_trading_mi_index_date_mismatch.json"),
        target_date=date(2026, 8, 14),
        retrieved_at=RETRIEVED_AT,
        as_of=AS_OF,
    )

    assert result.data_status is IndexDataStatus.UNAVAILABLE
    assert result.status_reason == "PROVIDER_DATE_MISMATCH"
    assert result.raw_provider_date == "20260813"
    assert result.value is None
    assert result.previous_close is None


def test_official_index_fetch_uses_target_date_twse_authority():
    payloads = {
        "afterTrading/MI_INDEX": _fixture("twse_after_trading_mi_index_target_valid.json"),
        "MI_5MINS_HIST": _fixture("twse_mi_5mins_hist_valid.json"),
        "tpex_index": _fixture("tpex_index_ohlc_valid.json"),
    }
    calls: list[str] = []

    def transport(url: str, _timeout: float) -> bytes:
        calls.append(url)
        for marker, payload in payloads.items():
            if marker in url:
                return json.dumps(payload).encode("utf-8")
        raise AssertionError(url)

    results = fetch_official_market_indexes(
        target_date=date(2026, 8, 14),
        retrieved_at=RETRIEVED_AT,
        as_of=AS_OF,
        transport=transport,
    )

    taiex = next(item for item in results if item.market == "TPE")
    assert taiex.data_status is IndexDataStatus.AVAILABLE
    assert taiex.trading_date == date(2026, 8, 14)
    assert taiex.value == Decimal("46021.48")
    assert any("afterTrading/MI_INDEX?date=20260814" in url for url in calls)
    assert all("openapi.twse.com.tw/v1/exchangeReport/MI_INDEX" not in url for url in calls)


def test_twse_official_ohlc_history_maps_daily_bar_without_inventing_change():
    result = parse_twse_market_index_ohlc(
        _fixture("twse_mi_5mins_hist_valid.json"),
        retrieved_at=RETRIEVED_AT,
        as_of=AS_OF,
        target_date=date(2026, 9, 24),
    )

    assert result.data_status is IndexDataStatus.AVAILABLE
    assert result.trading_date == date(2026, 9, 24)
    assert result.open == Decimal("48075.39")
    assert result.high == Decimal("48117.54")
    assert result.low == Decimal("47754.72")
    assert result.value == Decimal("48024.60")
    assert result.change is None


def test_tpex_official_index_maps_ohlc_and_derives_previous_close_from_change():
    result = parse_tpex_market_index(
        _fixture("tpex_index_ohlc_valid.json"),
        retrieved_at=RETRIEVED_AT,
        as_of=AS_OF,
        target_date=date(2026, 9, 24),
    )

    assert result.data_status is IndexDataStatus.AVAILABLE
    assert result.trading_date == date(2026, 9, 24)
    assert result.open == Decimal("413.22")
    assert result.high == Decimal("413.61")
    assert result.low == Decimal("410.64")
    assert result.value == Decimal("412.99")
    assert result.previous_close == Decimal("413.76")
    assert result.change_pct is not None and result.change_pct < 0


def test_twse_negative_fixtures_fail_closed_without_zero_or_preview_fallback():
    cases = (
        ("twse_mi_index_missing_target.json", "TARGET_INDEX_ROW_MISSING"),
        ("twse_mi_index_malformed_date.json", "INVALID_DATE"),
        ("twse_mi_index_invalid_sign.json", "INVALID_CHANGE_SIGN"),
        ("twse_mi_index_missing_change_pct.json", "MISSING_CHANGE_PCT"),
    )

    for name, reason in cases:
        result = parse_twse_market_index(_fixture(name), retrieved_at=RETRIEVED_AT, as_of=AS_OF)
        assert result.data_status is IndexDataStatus.UNAVAILABLE
        assert result.status_reason == reason
        assert result.value is None
        assert result.previous_close is None
        assert result.change is None
        assert result.change_pct is None
        assert result.data_status is not IndexDataStatus.PREVIEW


def test_tpex_maps_daily_index_and_keeps_unprovided_fields_null():
    result = parse_tpex_market_index(
        _fixture("tpex_daily_trading_index_valid.json"),
        retrieved_at=RETRIEVED_AT,
        as_of=AS_OF,
    )

    assert result.data_status is IndexDataStatus.AVAILABLE
    assert result.market == "TWO"
    assert result.index_identity == TPEX_MARKET_INDEX_IDENTITY
    assert result.source_identity == TPEX_MARKET_AGGREGATE_SOURCE_IDENTITY
    assert result.trading_date.isoformat() == "2026-08-14"
    assert result.raw_provider_date == "1150814"
    assert result.value == Decimal("400.95")
    assert result.change == Decimal("-5.17")
    assert result.previous_close is None
    assert result.change_pct is None
    assert result.quality_status == "SOURCE_FIELDS_VALID_PREVIOUS_CLOSE_DERIVATION_BLOCKED"
    assert not hasattr(result, "turnover")


def test_tpex_selects_requested_date_from_multi_day_official_response():
    payload = _fixture("tpex_daily_trading_index_valid.json")
    assert isinstance(payload, dict)
    rows = payload["value"]
    assert isinstance(rows, list)
    rows.append(
        {
            "Date": "1150813",
            "TPExIndex": "406.12",
            "Change": "4.10",
        }
    )

    result = parse_tpex_market_index(
        payload,
        retrieved_at=RETRIEVED_AT,
        as_of=AS_OF,
        target_date=date(2026, 8, 14),
    )

    assert result.data_status is IndexDataStatus.AVAILABLE
    assert result.raw_provider_date == "1150814"
    assert result.value == Decimal("400.95")


def test_tpex_negative_fixtures_fail_closed():
    cases = (
        ("tpex_daily_trading_index_missing_value.json", "MISSING_TPEXINDEX"),
        ("tpex_daily_trading_index_malformed_date.json", "INVALID_DATE"),
        ("tpex_daily_trading_index_invalid_change.json", "INVALID_NUMBER"),
    )

    for name, reason in cases:
        result = parse_tpex_market_index(_fixture(name), retrieved_at=RETRIEVED_AT, as_of=AS_OF)
        assert result.data_status is IndexDataStatus.UNAVAILABLE
        assert result.status_reason == reason
        assert result.value is None
        assert result.previous_close is None
        assert result.change is None
        assert result.change_pct is None


def test_tpex_crosscheck_normalizes_gregorian_date_without_string_joining():
    points = parse_tpex_index_crosscheck(_fixture("tpex_index_crosscheck_valid.json"))

    assert len(points) == 1
    assert points[0].data_status is IndexDataStatus.AVAILABLE
    assert points[0].raw_provider_date == "20260814"
    assert points[0].trading_date.isoformat() == "2026-08-14"
    assert points[0].value == Decimal("400.95")
    assert points[0].change == Decimal("-5.17")


def test_tpex_crosscheck_malformed_gregorian_date_is_unavailable():
    points = parse_tpex_index_crosscheck(_fixture("tpex_index_crosscheck_malformed_date.json"))

    assert points[0].data_status is IndexDataStatus.UNAVAILABLE
    assert points[0].status_reason == "INVALID_DATE"
    assert points[0].value is None


def test_provider_failure_is_explicitly_unavailable_not_preview():
    result = unavailable_market_index(
        "TWO",
        retrieved_at=RETRIEVED_AT,
        as_of=AS_OF,
        reason="PROVIDER_ERROR",
    )

    assert result.data_status is IndexDataStatus.UNAVAILABLE
    assert result.status_reason == "PROVIDER_ERROR"
    assert result.value is None
    assert result.data_status is not IndexDataStatus.PREVIEW
