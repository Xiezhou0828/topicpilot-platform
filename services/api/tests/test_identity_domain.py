from datetime import date

from sqlalchemy import inspect

from topicpilot_api.orm import Instrument, Market, SecurityIdentity


def test_identity_domain_models_define_expected_schema():
    assert Market.__tablename__ == "markets"
    assert Instrument.__tablename__ == "instruments"
    assert SecurityIdentity.__tablename__ == "security_identities"
    assert {column.name for column in inspect(Market).columns} >= {
        "code", "exchange_code", "timezone", "calendar_code", "valid_from", "valid_to", "is_active"
    }
    assert {column.name for column in inspect(Instrument).columns} >= {
        "market_id", "instrument_code", "instrument_type", "valid_from", "valid_to"
    }


def test_security_identity_history_is_separate_from_stable_instrument_identity():
    market = Market(code="TSE", name="Tokyo Stock Exchange", timezone="Asia/Tokyo")
    instrument = Instrument(market=market, instrument_code="JP0000000001", instrument_type="EQUITY")
    symbol = SecurityIdentity(
        instrument=instrument,
        market=market,
        identifier_namespace="TICKER",
        identifier_value="OLD",
        valid_from=date(2010, 1, 1),
        valid_to=date(2020, 12, 31),
    )
    assert symbol.instrument is instrument
    assert symbol.market is market
    assert instrument.market is market
    assert instrument.security_identities == [symbol]
