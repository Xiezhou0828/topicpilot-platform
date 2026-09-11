from topicpilot_api.reference_data.bootstrap import canonical_instrument_id


def test_canonical_instrument_uuid_is_stable_and_market_aware():
    assert str(canonical_instrument_id("TPE", "1717")) == (
        "76a95d00-3b82-5fc1-b856-4f07a9b37ef4"
    )
    assert canonical_instrument_id("TPE", "1717") != canonical_instrument_id("TWO", "1717")
