from datetime import date

import pytest

from topicpilot_api.corporate_action_authority import (
    CorporateActionAuthorityError,
    corporate_action_authorities_for,
    corporate_action_from_mapping,
    load_corporate_action_authorities,
    parse_corporate_action_authorities,
)
from topicpilot_api.market_data.availability import MarketAvailability


def test_sanitized_official_twse_reduction_record_is_generic_and_date_effective():
    records = load_corporate_action_authorities()
    record = next(item for item in records if item.symbol == "2601")

    assert record.market == "TPE"
    assert record.action_type == "CAPITAL_REDUCTION_SHARE_EXCHANGE"
    assert record.source_authority == "TWSE_OFFICIAL_REDUCTION"
    assert record.status_mapping == MarketAvailability.SUSPENDED.value
    assert record.reason_code == "CAPITAL_REDUCTION_TRADING_SUSPENSION"
    assert record.expected_close is False
    assert str(record.reduction_ratio_pct) == "16.2949753"

    assert corporate_action_authorities_for(
        symbol="2601", market="TPE", trading_date=date(2026, 9, 22)
    ) == ()
    for trading_date in (
        date(2026, 9, 23),
        date(2026, 9, 30),
        date(2026, 10, 3),
    ):
        assert corporate_action_authorities_for(
            symbol="2601", market="TPE", trading_date=trading_date
        ) == (record,)
    assert corporate_action_authorities_for(
        symbol="2601", market="TPE", trading_date=date(2026, 10, 5)
    ) == ()


def test_corporate_action_input_requires_official_provenance_and_safe_dates():
    payload = {
        "symbol": "1234",
        "market": "TPE",
        "actionType": "CAPITAL_REDUCTION_SHARE_EXCHANGE",
        "effectiveFrom": "2026-09-23",
        "effectiveTo": "2026-10-03",
        "resumeDate": "2026-10-05",
        "sourceAuthority": "TWSE_OFFICIAL_REDUCTION",
        "sourceReference": "https://www.twse.com.tw/official",
        "statusMapping": "SUSPENDED",
        "reasonCode": "CAPITAL_REDUCTION_TRADING_SUSPENSION",
        "expectedClose": False,
    }
    record = corporate_action_from_mapping(payload)
    assert record.to_dict()["expectedClose"] is False

    with pytest.raises(CorporateActionAuthorityError, match="UNSUPPORTED_CORPORATE_ACTION_SOURCE"):
        corporate_action_from_mapping({**payload, "sourceAuthority": "YAHOO"})
    with pytest.raises(CorporateActionAuthorityError, match="INVALID_RESUME_BOUNDARY"):
        corporate_action_from_mapping({**payload, "resumeDate": "2026-10-03"})


def test_conflicting_overlapping_corporate_action_inputs_are_not_silently_merged():
    base = {
        "symbol": "1234",
        "market": "TPE",
        "effectiveFrom": "2026-09-23",
        "effectiveTo": "2026-10-03",
        "resumeDate": "2026-10-05",
        "sourceAuthority": "TWSE_OFFICIAL_REDUCTION",
        "sourceReference": "https://www.twse.com.tw/official",
        "statusMapping": "SUSPENDED",
        "reasonCode": "CAPITAL_REDUCTION_TRADING_SUSPENSION",
    }
    with pytest.raises(CorporateActionAuthorityError, match="DUPLICATE_CORPORATE_ACTION_RECORD"):
        parse_corporate_action_authorities(
            {
                "records": [
                    {**base, "actionType": "CAPITAL_REDUCTION_SHARE_EXCHANGE"},
                    {**base, "actionType": "CAPITAL_REDUCTION_SHARE_EXCHANGE"},
                ]
            }
        )
