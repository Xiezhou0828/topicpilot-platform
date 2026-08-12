from datetime import UTC, datetime

from topicpilot_api.normalizer import (
    InputEnvelope,
    MappingPolicy,
    NormalizationFailure,
    ReferenceContext,
    SyntheticReferenceNormalizer,
)


def test_unknown_status_is_explicit_rejection():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    envelope = InputEnvelope({"trading_status": "HALT"}, "i", "s", "t", "r", now, now, now, "k")
    reference = ReferenceContext(
        "reference-data-v1", "UTC", "REGULAR", "TW", "TWD", 2, statuses=frozenset({"OPEN"})
    )
    result = SyntheticReferenceNormalizer()(envelope, reference, MappingPolicy())
    assert result.candidates == ()
    assert result.failures == (
        NormalizationFailure("REJECTED", "UNKNOWN_TRADING_STATUS", evidence={"value": "HALT"}),
    )
