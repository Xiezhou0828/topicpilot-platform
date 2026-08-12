from datetime import date
from decimal import Decimal
from uuid import uuid4

from topicpilot_api.orm import TopicSnapshot
from topicpilot_api.topic_snapshot_engine import (
    MemberPriceEvidence,
    aggregate_topic_members,
)


def test_topic_snapshot_aggregates_only_observed_evidence_and_marks_stale_as_of():
    first = uuid4()
    second = uuid4()
    result = aggregate_topic_members(
        {first, second},
        {
            first: MemberPriceEvidence(
                first, date(2026, 8, 10), Decimal("107"), Decimal("100")
            ),
            second: MemberPriceEvidence(
                second, date(2026, 8, 10), Decimal("93"), Decimal("100")
            ),
        },
        date(2026, 8, 11),
    )

    assert result.stock_count == 2
    assert result.observed_stock_count == 2
    assert result.average_change == Decimal("0")
    assert result.strong_stock_count == 1
    assert result.weak_stock_count == 1
    assert result.direction == "FLAT"
    assert result.data_status == "STALE_AS_OF"
    assert result.latest_observed_date == date(2026, 8, 10)


def test_topic_snapshot_missing_evidence_is_not_zero_change():
    result = aggregate_topic_members({uuid4()}, {}, date(2026, 8, 11))

    assert result.average_change is None
    assert result.observed_stock_count == 0
    assert result.coverage_pct == Decimal("0")
    assert result.direction == "UNKNOWN"
    assert result.data_status == "NO_CURRENT_DATA"


def test_topic_snapshot_model_is_v2_formal_fact():
    assert TopicSnapshot.__tablename__ == "topic_snapshots"
    assert {
        column.name for column in TopicSnapshot.__table__.columns
    } >= {
        "snapshot_date",
        "topic_id",
        "topic_slug",
        "topic_score",
        "topic_direction",
        "stock_count",
        "average_change",
        "data_status",
        "score_status",
    }
