from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from topicpilot_api.home_v2_publication import (
    SectionResult,
    build_daily_focus,
    build_market_signals,
    calculate_rotation_14d,
    empty_home_v2,
    normalize_home_publication_for_read,
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


def test_daily_focus_is_fail_closed_when_formal_signal_dependencies_are_incomplete():
    overview = {
        "marketHealth": {"status": "AVAILABLE", "advance": 12, "decline": 4, "flat": 2},
        "breadth": [],
        "indices": [
            {
                "market": "TPE",
                "indexName": "TWSE",
                "value": 100,
                "change": 1,
                "status": "AVAILABLE",
            }
        ],
    }
    focus = build_daily_focus(
        market_overview=overview,
        main_topics=[{"name": "AI"}],
        heating_topics=[],
        cooling_topics=[],
        data_date=date(2026, 8, 21),
        as_of=datetime(2026, 8, 21, 16, tzinfo=UTC),
    )

    assert focus.status == "PARTIAL"
    assert focus.payload["temporary"] is False
    assert focus.payload["mode"] == "RULE_BASED_V1"
    assert focus.payload["headline"] == "今日市場訊號尚未完成"
    assert focus.payload["bullets"] == []
    assert focus.payload["signals"] == []
    assert focus.payload["formalDependenciesComplete"] is False
    assert "INDEX_DIVERGENCE" in focus.payload["formalDependencyStatus"]["missing"]
    assert [item["key"] for item in focus.payload["signalCatalog"]] == [
        "INDEX_DIVERGENCE",
        "OTC_VOLUME_PRICE_DIVERGENCE",
        "INSTITUTION_PRICE_DIVERGENCE",
        "BREADTH_DIVERGENCE",
    ]
    assert build_daily_focus(
        market_overview={},
        main_topics=[],
        heating_topics=[],
        cooling_topics=[],
        data_date=date(2026, 8, 21),
        as_of=None,
    ).status == "UNAVAILABLE"


def test_daily_focus_reports_no_signal_only_after_all_formal_dependencies_are_ready():
    focus = build_daily_focus(
        market_overview={
            "dataStatus": "AVAILABLE",
            "marketHealth": {"status": "AVAILABLE", "advance": 12, "decline": 4, "flat": 2},
            "breadth": [
                {
                    "market": market,
                    "advance": 6,
                    "decline": 2,
                    "coverage": {"status": "AVAILABLE"},
                }
                for market in ("TPE", "TWO")
            ],
            "indices": [
                {"market": "TPE", "change": 1, "status": "AVAILABLE"},
                {"market": "TWO", "change": 0.5, "status": "AVAILABLE"},
            ],
            "turnover": [
                {"market": "TPE", "value": 100, "status": "AVAILABLE"},
                {"market": "TWO", "value": 80, "changePct": -1, "status": "AVAILABLE"},
            ],
            "institutionFlows": {
                "markets": [
                    {
                        "market": "TPE",
                        "availability": "AVAILABLE",
                        "current": {"foreign": {"value": 10, "status": "AVAILABLE"}},
                    }
                ]
            },
        },
        main_topics=[],
        heating_topics=[],
        cooling_topics=[],
        data_date=date(2026, 8, 21),
        as_of=None,
    )

    assert focus.status == "AVAILABLE"
    assert focus.payload["formalDependenciesComplete"] is True
    assert focus.payload["headline"] == "今日無異常訊號"
    assert focus.payload["signals"] == []


def test_market_signals_emit_index_and_breadth_divergence_in_catalog_order():
    focus = build_daily_focus(
        market_overview={
            "marketHealth": {
                "status": "AVAILABLE",
                "advance": 2,
                "decline": 5,
                "flat": 1,
                "breadthEligible": 8,
            },
            "indices": [
                {
                    "market": "TPE",
                    "indexName": "TWSE",
                    "value": 100,
                    "status": "AVAILABLE",
                    "change": 1,
                    "changePct": 1.0,
                },
                {
                    "market": "TWO",
                    "indexName": "TPEx",
                    "value": 80,
                    "status": "AVAILABLE",
                    "change": -0.5,
                },
            ],
        },
        main_topics=[{"name": "不要出現在重點中的題材"}],
        heating_topics=[],
        cooling_topics=[],
        data_date=date(2026, 8, 21),
        as_of=None,
    )

    assert focus.status == "PARTIAL"
    assert focus.payload["signals"] == []
    assert focus.payload["formalDependenciesComplete"] is False
    assert focus.payload["headline"] == "今日市場訊號尚未完成"
    assert "不要出現在重點中的題材" not in " ".join(focus.payload["bullets"])


def test_market_signals_are_fail_closed_for_missing_and_non_formal_inputs():
    assert build_market_signals(
        {
            "indices": [
                {"market": "TPE", "change": 1, "status": "AVAILABLE"},
                {"market": "TWO", "change": -1, "status": "AVAILABLE"},
            ],
            "turnover": [{"market": "TWO", "status": "AVAILABLE", "value": 10}],
        }
    ) == [
        {
            "key": "INDEX_DIVERGENCE",
            "name": "大型股／中小型股分化",  # noqa: RUF001
            "severity": "WATCH",
            "direction": "Neutral",
            "evidence": ["加權指數 +1 點", "櫃買指數 -1 點"],
            "interpretation": "大型股與中小型股走勢明顯分化。",
        }
    ]
    assert build_market_signals(
        {
            "indices": [
                {"market": "TPE", "change": 1, "status": "PREVIEW"},
                {"market": "TWO", "change": -1, "status": "PREVIEW"},
            ],
            "marketHealth": {"status": "PREVIEW", "advance": 1, "decline": 5},
        }
    ) == []
    assert build_market_signals(
        {
            "indices": [{"market": "TPE", "change": 1, "status": "AVAILABLE"}],
            "marketHealth": {"status": "AVAILABLE", "advance": 5, "decline": 4},
        }
    ) == []


def test_read_normalization_replaces_persisted_legacy_focus_without_changing_facts():
    payload = {
        "asOf": "2026-09-09",
        "publication": {
            "tradingDate": "2026-09-09",
            "asOf": "2026-09-09T13:35:00+08:00",
            "completeness": {"sectionStatuses": {"dailyFocus": {"status": "AVAILABLE"}}},
        },
        "marketOverview": {
            "dataDate": "2026-09-09",
            "updatedAt": "2026-09-09T13:35:00+08:00",
            "marketHealth": {"status": "AVAILABLE", "advance": 1, "decline": 1, "flat": 0},
            "indices": [{"market": "TPE", "change": 1, "status": "AVAILABLE"}],
        },
        "dailyFocus": {"headline": "目前主線為 網通。", "bullets": ["legacy narrative"]},
        "sectionStatuses": {"dailyFocus": {"status": "AVAILABLE"}},
    }

    result = normalize_home_publication_for_read(payload)

    assert result["dailyFocus"]["headline"] == "今日市場訊號尚未完成"
    assert result["dailyFocus"]["signals"] == []
    assert result["dailyFocus"]["formalDependenciesComplete"] is False
    assert result["marketOverview"] == payload["marketOverview"]
    assert result["sectionStatuses"]["dailyFocus"]["source"] == "HOME_V2_DAILY_FOCUS_RULE_V1"
    assert (
        result["publication"]["completeness"]["sectionStatuses"]["dailyFocus"]["source"]
        == "HOME_V2_DAILY_FOCUS_RULE_V1"
    )


def test_home_gate_requires_formal_market_facts_but_topics_and_focus_are_section_level():
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
    no_topics = SectionResult(
        "UNAVAILABLE",
        date(2026, 8, 21),
        None,
        "formal",
        "NO_FORMAL_TOPIC_PUBLICATION",
        "尚未完成",
        [],
    )
    assert validate_home_gate(market_overview=market, main_topics=no_topics, daily_focus=focus) == (
        "PUBLISHED",
        None,
    )


def test_home_gate_rejects_missing_market_even_when_topic_evidence_exists():
    market = SectionResult(
        "UNAVAILABLE",
        date(2026, 8, 21),
        None,
        "formal",
        "NO_PUBLISHED_MARKET_FACTS",
        "尚未完成",
        {},
    )
    topics = SectionResult(
        "AVAILABLE", date(2026, 8, 21), None, "formal", None, None, [{"slug": "ai"}]
    )

    assert validate_home_gate(market_overview=market, main_topics=topics, daily_focus=topics) == (
        "UNAVAILABLE",
        "NO_PUBLISHED_MARKET_FACTS",
    )


def test_empty_home_is_typed_and_product_safe_before_first_publication():
    payload = empty_home_v2(datetime(2026, 8, 21, 16, tzinfo=UTC), tracked_stock_count=507)

    assert HomeResponse.model_validate(payload).publication.state == "UNAVAILABLE"
    assert payload["marketOverview"]["dataStatus"] == "UNAVAILABLE"
    assert payload["dailyFocus"]["temporary"] is False
    assert payload["dailyFocus"]["bullets"] == []
    assert payload["dailyFocus"]["signals"] == []
    assert [item["key"] for item in payload["dailyFocus"]["signalCatalog"]] == [
        "INDEX_DIVERGENCE",
        "OTC_VOLUME_PRICE_DIVERGENCE",
        "INSTITUTION_PRICE_DIVERGENCE",
        "BREADTH_DIVERGENCE",
    ]
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
