from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from topicpilot_api.home_v2_publication import (
    SectionResult,
    build_daily_focus,
    calculate_rotation_14d,
    empty_home_v2,
    rank_formal_topics,
    validate_home_gate,
)
from topicpilot_api.market_data.index_contract import (
    IndexDataStatus,
    fetch_official_market_indexes,
)
from topicpilot_api.schemas import HomeResponse


def test_main_topics_rank_is_deterministic_and_exposes_evidence_not_a_new_score():
    rows = [
        {
            "topic_slug": "beta",
            "topic_name": "Beta",
            "data_status": "COMPLETE",
            "observed_stock_count": 8,
            "coverage_pct": 80,
            "positive_count": 5,
            "average_change": 1.0,
            "stock_count": 10,
        },
        {
            "topic_slug": "alpha",
            "topic_name": "Alpha",
            "data_status": "COMPLETE",
            "observed_stock_count": 8,
            "coverage_pct": 80,
            "positive_count": 5,
            "average_change": 1.0,
            "stock_count": 10,
        },
        {
            "topic_slug": "incomplete",
            "topic_name": "Incomplete",
            "data_status": "PARTIAL",
            "observed_stock_count": 99,
            "coverage_pct": 99,
            "positive_count": 99,
            "average_change": 99.0,
            "stock_count": 100,
        },
    ]

    result = rank_formal_topics(reversed(rows))

    assert [item["slug"] for item in result] == ["alpha", "beta", "incomplete"]
    assert all(item["strength"] is None for item in result)
    assert result[0]["rankingEvidence"]["rankingPolicy"].startswith("availability,")
    assert result[0]["rankingEvidence"]["averageChange"] == 1.0


def test_rotation_requires_fifteen_sessions_and_excludes_zero_change():
    target = date(2026, 8, 21)
    dates = [target - timedelta(days=offset) for offset in range(14, -1, -1)]
    rows = []
    for snapshot_date in dates:
        rows.extend(
            [
                {
                    "topic_slug": "heating",
                    "topic_name": "Heating",
                    "snapshot_date": snapshot_date,
                    "average_change": 1.0 if snapshot_date != target else 4.0,
                    "observed_stock_count": 5,
                    "market_grade": "A",
                    "as_of_at": datetime(2026, 8, 21, 16, tzinfo=UTC),
                },
                {
                    "topic_slug": "cooling",
                    "topic_name": "Cooling",
                    "snapshot_date": snapshot_date,
                    "average_change": 3.0 if snapshot_date != target else 1.0,
                    "observed_stock_count": 5,
                    "market_grade": "B",
                    "as_of_at": datetime(2026, 8, 21, 16, tzinfo=UTC),
                },
                {
                    "topic_slug": "flat",
                    "topic_name": "Flat",
                    "snapshot_date": snapshot_date,
                    "average_change": 2.0,
                    "observed_stock_count": 5,
                    "market_grade": "B",
                    "as_of_at": datetime(2026, 8, 21, 16, tzinfo=UTC),
                },
            ]
        )

    heating, cooling, reason = calculate_rotation_14d(rows, target_date=target)

    assert reason is None
    assert [item["topicSlug"] for item in heating] == ["heating"]
    assert [item["topicSlug"] for item in cooling] == ["cooling"]
    assert heating[0]["strengthDelta"] == 3.0
    assert cooling[0]["strengthDelta"] == -2.0
    assert heating[0]["rotationEvidence"]["referenceDate"] == dates[0]

    short_rows = [row for row in rows if row["snapshot_date"] != dates[0]]
    short_heating, short_cooling, short_reason = calculate_rotation_14d(
        short_rows, target_date=target, limit=3
    )
    assert (short_heating, short_cooling, short_reason) == (
        [],
        [],
        "INSUFFICIENT_ROTATION_HISTORY",
    )


def test_daily_focus_is_rule_based_and_fail_closed_without_evidence():
    overview = {
        "marketHealth": {"advance": 12, "decline": 4, "flat": 2},
        "breadth": [],
        "indices": [{"indexName": "TWSE", "value": 100, "change": 1}],
    }
    focus = build_daily_focus(
        market_overview=overview,
        main_topics=[{"name": "AI"}],
        heating_topics=[],
        cooling_topics=[],
        data_date=date(2026, 8, 21),
        as_of=datetime(2026, 8, 21, 16, tzinfo=UTC),
    )

    assert focus.status == "AVAILABLE"
    assert focus.payload["temporary"] is False
    assert focus.payload["mode"] == "RULE_BASED_V1"
    assert focus.payload["bullets"]
    assert build_daily_focus(
        market_overview={},
        main_topics=[],
        heating_topics=[],
        cooling_topics=[],
        data_date=date(2026, 8, 21),
        as_of=None,
    ).status == "UNAVAILABLE"


def test_home_gate_requires_market_and_formal_topics_but_not_optional_sections():
    market = SectionResult(
        "AVAILABLE",
        date(2026, 8, 21),
        None,
        "canonical",
        None,
        None,
        {"breadth": [{"observed": 1}]},
    )
    topics = SectionResult(
        "AVAILABLE", date(2026, 8, 21), None, "formal", None, None, [{"slug": "ai"}]
    )
    focus = SectionResult(
        "UNAVAILABLE", date(2026, 8, 21), None, "rule", "NO_EVIDENCE", "尚未完成", {}
    )

    assert validate_home_gate(market_overview=market, main_topics=topics, daily_focus=focus) == (
        "PUBLISHED",
        None,
    )


def test_empty_home_is_typed_and_product_safe_before_first_publication():
    payload = empty_home_v2(datetime(2026, 8, 21, 16, tzinfo=UTC), tracked_stock_count=507)

    assert HomeResponse.model_validate(payload).publication.state == "UNAVAILABLE"
    assert payload["marketOverview"]["dataStatus"] == "UNAVAILABLE"
    assert payload["dailyFocus"]["temporary"] is False
    assert payload["dailyFocus"]["bullets"] == []
    assert payload["sectionStatuses"]["marketEvents"]["status"] == "UNAVAILABLE"


def test_official_index_fetch_transport_failure_is_typed_unavailable():
    retrieved_at = datetime(2026, 8, 21, 16, tzinfo=UTC)

    def failing_transport(url: str, timeout: float) -> bytes:
        raise OSError(url)

    results = fetch_official_market_indexes(
        target_date=date(2026, 8, 21),
        retrieved_at=retrieved_at,
        as_of=retrieved_at,
        transport=failing_transport,
    )

    assert {item.market for item in results} == {"TPE", "TWO"}
    assert all(item.data_status is IndexDataStatus.UNAVAILABLE for item in results)
    assert all(item.value is None for item in results)
