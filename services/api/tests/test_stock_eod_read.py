from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from topicpilot_api.production_read_model import STOCK_ROWS_SQL, _stock_eod, _stock_item
from topicpilot_api.schemas import StockEodRead, StockReadModel

OBSERVED_AT = datetime(2026, 8, 13, tzinfo=UTC)


def _row(**overrides):
    row = {
        "instrument_id": "instrument-1",
        "instrument_code": "2330",
        "name": "Example",
        "market_code": "TPE",
        "exchange_code": "TWSE",
        "market_name": "TWSE Listed",
        "is_active": True,
        "update_mode": "POST_CLOSE",
        "moving_average_period": 60,
        "moving_average_state": "ABOVE",
        "moving_average": Decimal("100"),
        "observation_count": 60,
        "as_of_date": date(2026, 8, 13),
        "classification_reason": None,
        "daily_close": Decimal("110"),
        "previous_daily_close": Decimal("100"),
        "intraday_close": None,
        "daily_observed_at": OBSERVED_AT,
        "daily_retrieved_at": OBSERVED_AT,
        "intraday_observed_at": None,
        "intraday_retrieved_at": None,
        "intraday_volume": None,
        "daily_volume": Decimal("1000"),
        "eod_date": date(2026, 8, 13),
        "eod_open": Decimal("105"),
        "eod_high": Decimal("112"),
        "eod_low": Decimal("104"),
        "eod_price_currency_code": "TWD",
        "eod_price_scale": 2,
        "eod_adjustment_state": "UNADJUSTED",
        "eod_price_reference_data_version": "tw-reference-v1",
        "eod_price_normalization_contract_version": "normalization-contract-v1",
        "eod_price_mapping_policy_version": "historical-daily-mapping-v1",
        "eod_price_quality_state": "ACCEPTED",
        "eod_price_source_code": "TWSE_OFFICIAL_DAILY",
        "eod_price_adapter_version": "twse-official-daily.v2",
        "eod_price_observation_semantics": "DAILY_BAR",
        "eod_price_observed_at": OBSERVED_AT,
        "eod_price_retrieved_at": OBSERVED_AT,
        "previous_price_currency_code": "TWD",
        "previous_price_scale": 2,
        "previous_adjustment_state": "UNADJUSTED",
        "volume_observation_id": "volume-1",
        "volume_unit_code": "UNIT",
        "volume_scale": 0,
        "turnover_amount": None,
        "turnover_currency_code": None,
        "turnover_scale": None,
        "volume_aggregation_code": "DAILY_TOTAL",
        "volume_observed_at": OBSERVED_AT,
        "volume_retrieved_at": OBSERVED_AT,
        "volume_reference_data_version": "tw-reference-v1",
        "volume_normalization_contract_version": "normalization-contract-v1",
        "volume_mapping_policy_version": "historical-daily-mapping-v1",
        "volume_quality_state": "ACCEPTED",
        "volume_source_code": "TWSE_OFFICIAL_DAILY",
        "volume_adapter_version": "twse-official-daily.v2",
        "volume_observation_semantics": "DAILY_BAR",
        "eod_status_code": None,
        "eod_status_reason": None,
        "status_observed_at": None,
        "status_retrieved_at": None,
        "quality_conflict": False,
        "value_conflict": False,
    }
    row.update(overrides)
    return row


def test_stock_eod_uses_backend_decimal_change_and_preserves_null_turnover():
    eod = _stock_eod(_row())

    assert eod is not None
    assert eod["tradingDate"] == date(2026, 8, 13)
    assert eod["close"] == 110.0
    assert eod["previousClose"] == 100.0
    assert eod["change"] == 10.0
    assert eod["changePct"] == 10.0
    assert eod["volume"] == 1000.0
    assert eod["turnover"] is None
    assert eod["dataStatus"] == "PARTIAL"
    assert eod["priceSource"]["sourceCode"] == "TWSE_OFFICIAL_DAILY"
    assert eod["volumeSource"]["observationSemantics"] == "DAILY_BAR"


def test_stock_eod_fails_closed_for_unknown_adjustment_state():
    eod = _stock_eod(_row(eod_adjustment_state="UNKNOWN"))

    assert eod is not None
    assert eod["dataStatus"] == "ADJUSTMENT_UNKNOWN"
    assert eod["change"] is None
    assert eod["changePct"] is None
    assert eod["close"] == 110.0


def test_stock_eod_preserves_explicit_no_trade_and_previous_close():
    eod = _stock_eod(
        _row(
            daily_close=None,
            eod_open=None,
            eod_high=None,
            eod_low=None,
            eod_status_code="EXCHANGE_CONFIRMED_NO_DATA",
            status_observed_at=OBSERVED_AT,
            status_retrieved_at=OBSERVED_AT,
            eod_price_source_code=None,
            volume_observation_id=None,
        )
    )

    assert eod is not None
    assert eod["dataStatus"] == "NO_TRADE"
    assert eod["tradingDate"] == date(2026, 8, 13)
    assert eod["previousClose"] == 100.0
    assert eod["close"] is None
    assert eod["volume"] is None
    assert eod["change"] is None
    assert eod["changePct"] is None


def test_intraday_price_does_not_pair_with_top_level_eod_change_pct():
    item = _stock_item(
        _row(
            update_mode="INTRADAY",
            intraday_close=Decimal("112"),
            intraday_observed_at=OBSERVED_AT,
            intraday_retrieved_at=OBSERVED_AT,
        ),
        [],
    )

    assert item["price"] == 112.0
    assert item["changePct"] is None
    assert item["eod"]["close"] == 110.0
    assert item["eod"]["changePct"] == 10.0


def test_stock_eod_schema_is_additive_and_nullable_at_read_model_boundary():
    eod_fields = StockEodRead.model_fields
    assert {"trading_date", "previous_close", "change_pct", "price_source", "data_status"} <= set(
        eod_fields
    )
    assert "eod" in StockReadModel.model_fields
    assert StockReadModel.model_fields["eod"].is_required()

    schema = StockReadModel.model_json_schema()
    eod_schema = schema["properties"]["eod"]
    assert any("StockEodRead" in str(value) for value in eod_schema.get("anyOf", []))


def test_stock_eod_query_is_set_based_and_current_observation_safe():
    sql = STOCK_ROWS_SQL.text

    assert "eod_previous_price" in sql
    assert "NOT EXISTS" in sql
    assert "successor.supersedes_id = co.id" in sql
    assert "cv.aggregation_code = 'DAILY_TOTAL'" in sql
    assert "AT TIME ZONE m.timezone" in sql
    assert "daily_price_by_day" in sql
