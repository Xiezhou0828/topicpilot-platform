from datetime import UTC, datetime
from decimal import Decimal

from topicpilot_api.normalizer.contracts import InputEnvelope, MappingPolicy, ReferenceContext
from topicpilot_api.normalizer.synthetic import SyntheticReferenceNormalizer


def env(payload):
    t = datetime(2026, 1, 1, tzinfo=UTC)
    return InputEnvelope(payload, "i", "s", "t", "r", t, t, t, "k")


def ref():
    return ReferenceContext(
        "reference-data-v1", "UTC", "REGULAR", "TW", "TWD", 2, statuses=frozenset({"OPEN"})
    )


def test_multi_family_decimal_and_paths():
    result = SyntheticReferenceNormalizer()(
        env(
            {"last": "123.4500", "volume": "5", "quote": {"bid": "123.4"}, "trading_status": "OPEN"}
        ),
        ref(),
        MappingPolicy(),
    )
    assert [c.family_code for c in result.candidates] == [
        "PRICE",
        "VOLUME",
        "QUOTE",
        "TRADING_STATUS",
    ]
    assert result.candidates[0].values["last"] == Decimal("123.4500")
    assert result.candidates[2].source_field_path == "/quote/bid"


def test_invalid_time_rejects_without_candidate():
    e = env({"last": 1})
    e = e.__class__(**{**e.__dict__, "observed_at": datetime(2026, 1, 1)})
    result = SyntheticReferenceNormalizer()(e, ref(), MappingPolicy())
    assert not result.candidates and result.failures[0].code == "INVALID_OBSERVED_TIME"
