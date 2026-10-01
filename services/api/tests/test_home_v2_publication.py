from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from topicpilot_api import home_read_model
from topicpilot_api.home_v2_publication import (
    SectionResult,
    _aggregate_home_institutional_flow,
    _flow_window,
    _read_home_institutional_flow,
    _turnover_comparison,
    build_daily_focus,
    build_market_distribution,
    build_market_signals,
    calculate_fast_rotation,
    empty_home_v2,
    rank_formal_topics,
    read_latest_home_publication,
    validate_home_gate,
)
from topicpilot_api.market_data.index_contract import (
    IndexDataStatus,
    fetch_official_market_indexes,
)
from topicpilot_api.schemas import HomeResponse


def test_main_topics_rank_is_formal_and_deterministic():
    rows = [
        {
            "topic_slug": "beta",
            "topic_name": "Beta",
            "snapshot_date": date(2026, 8, 21),
            "formal_member_count": 8,
            "formal_daily_grade": "A",
            "absolute_score": 70,
            "relative_score": 60,
            "formal_lifecycle": "FERMENTING",
            "authority_status": "VALID",
            "authority_quality_valid": True,
            "coverage_pct": 80,
        },
        {
            "topic_slug": "alpha",
            "topic_name": "Alpha",
            "snapshot_date": date(2026, 8, 21),
            "formal_member_count": 8,
            "formal_daily_grade": "A",
            "absolute_score": 70,
            "relative_score": 60,
            "formal_lifecycle": "FERMENTING",
            "authority_status": "VALID",
            "authority_quality_valid": True,
            "coverage_pct": 80,
        },
    ]

    result = rank_formal_topics(reversed(rows))

    assert [item["slug"] for item in result] == ["alpha", "beta"]
    assert result[0]["absoluteScore"] == 70
    assert result[0]["rankingEvidence"]["rankingPolicy"].startswith("lifecycle,")


def test_rotation_uses_five_session_absolute_strength_median():
    target = date(2026, 8, 21)
    dates = [target - timedelta(days=offset) for offset in range(5, 0, -1)]
    rows = []
    for index, snapshot_date in enumerate(dates):
        rows.extend(
            [
                {
                    "topic_slug": "heating",
                    "topic_name": "Heating",
                    "snapshot_date": snapshot_date,
                    "formal_member_count": 5,
                    "formal_daily_grade": "A",
                    "absolute_score": 50 + index,
                    "relative_score": 45 + index,
                    "formal_lifecycle": "FERMENTING",
                    "authority_status": "VALID",
                    "authority_quality_valid": True,
                },
                {
                    "topic_slug": "cooling",
                    "topic_name": "Cooling",
                    "snapshot_date": snapshot_date,
                    "formal_member_count": 5,
                    "formal_daily_grade": "B",
                    "absolute_score": 100 - index,
                    "relative_score": 95 - index,
                    "formal_lifecycle": "MATURE",
                    "authority_status": "VALID",
                    "authority_quality_valid": True,
                },
            ]
        )
    rows.extend(
        [
            {**rows[0], "snapshot_date": target, "absolute_score": 62},
            {**rows[1], "snapshot_date": target, "absolute_score": 88},
        ]
    )

    heating, cooling, reason = calculate_fast_rotation(rows, target_date=target)

    assert reason is None
    assert [item["topicSlug"] for item in heating] == ["heating"]
    assert [item["topicSlug"] for item in cooling] == ["cooling"]
    assert heating[0]["strengthDelta"] == 10.0
    assert cooling[0]["strengthDelta"] == -10.0
    assert heating[0]["baselineMedian"] == 52.0
    assert heating[0]["observedStockCount"] == 5
    assert heating[0]["rotationEvidence"]["baselineSessions"] == dates


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


def test_market_signals_use_formal_index_and_breadth_facts_only():
    signals = build_market_signals(
        {
            "indices": [
                {"market": "TPE", "status": "AVAILABLE", "change": 1.2, "changePct": 0.5},
                {"market": "TWO", "status": "AVAILABLE", "change": -0.4, "changePct": -0.2},
            ],
            "turnover": [],
            "marketHealth": {
                "status": "AVAILABLE",
                "advance": 12,
                "decline": 20,
                "flat": 3,
            },
        }
    )

    assert [item["signalId"] for item in signals] == [
        "INDEX_MARKET_DIVERGENCE",
        "BREADTH_RED_INDEX_DISCONNECT",
    ]
    assert all(item["evidence"] for item in signals)


def test_market_distribution_excludes_missing_price_pairs_without_zero_filling():
    distribution = build_market_distribution(
        [
            {"instrument_id": "a", "status_code": "NORMAL", "close": 110, "previous_close": 100},
            {"instrument_id": "b", "status_code": "NORMAL", "close": 100, "previous_close": 100},
            {"instrument_id": "c", "status_code": "NO_TRADE", "close": None, "previous_close": 100},
        ],
        eligible_count=3,
        as_of=None,
    )

    assert distribution["status"] == "AVAILABLE"
    assert distribution["eligible"] == 2
    assert distribution["excluded"] == 1
    assert sum(bucket["count"] for bucket in distribution["buckets"]) == 2
    assert sum(bucket["percentage"] for bucket in distribution["buckets"]) == 100.0
    assert distribution["coverage"]["reconciliationStatus"] == "PASS"
    assert distribution["coverage"]["breadthEligible"] == 2
    assert distribution["coverage"]["scope"] == "COVERED_STOCKS"
    assert distribution["coverage"]["universeLabel"].startswith("已覆蓋股票")
    assert distribution["coverage"]["universeLabel"].endswith("正式收盤與前收完整者")
    assert distribution["coverage"]["observedComplete"] == 2
    assert distribution["coverage"]["excludedCount"] == 1
    assert distribution["coverage"]["distributionDenominator"] == "COMPLETE_CLOSE_PREVIOUS_CLOSE"


def test_home_institutional_flow_aggregate_requires_matching_exchange_facts():
    def market(market_code: str, offset: int) -> dict:
        current = {
            "market": market_code,
            "tradingDate": date(2026, 8, 21),
            "sourceProvider": market_code,
            "sourceIdentity": f"{market_code}_FLOW",
            "sourceDataset": f"{market_code} dataset",
            "sourceEndpoint": f"https://example.test/{market_code}",
            "adapterVersion": "test.v1",
            "sourceAsOf": datetime(2026, 8, 21, 8, tzinfo=UTC),
            "publishedAt": datetime(2026, 8, 21, 8, tzinfo=UTC),
            "retrievedAt": datetime(2026, 8, 21, 8, tzinfo=UTC),
            "availability": "AVAILABLE",
            "freshness": "CURRENT",
            "statusReason": None,
            "lineage": "test",
            "responseContentHash": None,
        }
        for key, base in (("foreign", 10), ("investmentTrust", 20), ("dealer", 30), ("total", 60)):
            current[key] = {
                "buy": base + offset,
                "sell": base,
                "net": offset,
                "value": offset,
                "unit": "TWD",
                "scale": 0,
                "status": "AVAILABLE",
            }
        return {
            "market": market_code,
            "asOfDate": date(2026, 8, 21),
            "availability": "AVAILABLE",
            "current": current,
        }

    aggregate = _aggregate_home_institutional_flow([market("TPE", 1), market("TWO", -2)])

    assert aggregate is not None
    assert aggregate["market"] == "TPE+TWO"
    assert aggregate["foreign"]["buy"] == 19
    assert aggregate["foreign"]["sell"] == 20
    assert aggregate["foreign"]["net"] == -1
    assert aggregate["total"]["net"] == -1


def test_institutional_flow_windows_sum_only_complete_official_sessions():
    rows = [
        {
            "availability": "AVAILABLE",
            "foreign_net": 10,
            "investment_trust_net": 20,
            "dealer_net": 30,
            "total_net": 60,
            "unit": "TWD",
            "scale": 0,
        }
        for _ in range(5)
    ]

    rolling = _flow_window(rows, 5)

    assert rolling["complete"] is True
    assert rolling["observedSessions"] == 5
    assert rolling["foreignNet"] == 50
    assert rolling["investmentTrustNet"] == 100
    assert rolling["dealerNet"] == 150
    assert rolling["totalNet"] == 300


def test_home_institutional_flow_does_not_carry_forward_when_exchange_is_missing():
    target = date(2026, 8, 21)

    class _MappingsResult:
        def mappings(self):
            return iter(
                [
                    {"market": "TPE", "trading_date": target, "availability": "AVAILABLE"},
                    {
                        "market": "TWO",
                        "trading_date": date(2026, 8, 20),
                        "availability": "AVAILABLE",
                    },
                ]
            )

    class _Session:
        def execute(self, *_args, **_kwargs):
            return _MappingsResult()

    assert _read_home_institutional_flow(_Session(), target) is None


def test_turnover_comparison_uses_formal_prior_session_and_fails_closed_for_missing_data():
    current = {
        "tradingDate": date(2026, 8, 24),
        "value": 1_000,
        "currency": "TWD",
        "unit": "TWD",
        "scale": 0,
        "status": "AVAILABLE",
    }
    previous = {
        "tradingDate": date(2026, 8, 21),
        "session": "CLOSE",
        "value": 800,
        "currency": "TWD",
        "unit": "TWD",
        "scale": 0,
        "status": "AVAILABLE",
    }

    comparison = _turnover_comparison(current, previous)

    assert comparison is not None
    assert comparison["tradingDate"] == date(2026, 8, 21)
    assert comparison["value"] == 800
    assert comparison["absoluteChange"] == 200
    assert comparison["changePct"] == 25
    assert _turnover_comparison(current, None) is None


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
    assert payload["sectionStatuses"]["marketEvents"]["status"] == "UNAVAILABLE"


def test_empty_home_exposes_downstream_reason_codes_and_backend_owned_messages():
    payload = empty_home_v2(
        datetime(2026, 8, 21, 16, tzinfo=UTC),
        stale_formal_publication=True,
    )

    statuses = payload["sectionStatuses"]
    assert statuses["marketOverview"]["reasonCode"] == "STALE_FORMAL_PUBLICATION"
    assert statuses["mainTopics"]["reasonCode"] == "FORMAL_TOPIC_PUBLICATION_NOT_READY"
    assert statuses["marketEvents"]["reasonCode"] == "FORMAL_TOPIC_PUBLICATION_NOT_READY"
    assert statuses["heatingTopics"]["reasonCode"] == "CURRENT_FORMAL_TOPIC_STRENGTH_NOT_PUBLISHED"
    assert statuses["coolingTopics"]["reasonCode"] == "CURRENT_FORMAL_TOPIC_STRENGTH_NOT_PUBLISHED"
    assert statuses["opportunities"]["reasonCode"] == "FORMAL_OPPORTUNITY_PROVIDER_NOT_IMPLEMENTED"
    assert statuses["mainTopics"]["userMessage"] == "今日主線尚未完成正式發布。"
    assert statuses["marketEvents"]["userMessage"] == "題材動態尚未完成正式發布。"
    assert statuses["heatingTopics"]["userMessage"].startswith("快速升溫暫無法評估")
    assert statuses["coolingTopics"]["userMessage"].startswith("快速降溫暫無法評估")
    assert payload["dataQuality"]["notes"]


def test_read_latest_home_publication_filters_to_requested_trading_date():
    target = date(2026, 9, 30)

    class _Result:
        def mappings(self):
            return self

        def one_or_none(self):
            return None

    class _Session:
        statement = None
        params = None

        def execute(self, statement, params):
            self.statement = str(statement)
            self.params = params
            return _Result()

    session = _Session()
    assert read_latest_home_publication(session, trading_date=target) is None
    assert "trading_date = :trading_date" in session.statement
    assert session.params == {"trading_date": target}


def test_home_read_model_does_not_return_prior_published_envelope_as_today(
    monkeypatch,
):
    target = date(2026, 9, 30)

    class _Session:
        def execute(self, *_args, **_kwargs):
            return object()

        def scalar(self, *_args, **_kwargs):
            return 0

        def rollback(self):
            return None

    monkeypatch.setattr(home_read_model, "latest_canonical_trading_date", lambda _session: target)
    monkeypatch.setattr(
        home_read_model,
        "read_latest_home_publication",
        lambda _session, *, trading_date: None,
    )
    monkeypatch.setattr(home_read_model, "has_prior_home_publication", lambda _session, _date: True)

    payload = home_read_model.build_home_read_model(
        _Session(), now=datetime(2026, 9, 30, 16, tzinfo=UTC)
    )

    assert payload["publication"]["state"] == "UNAVAILABLE"
    assert payload["dataQuality"]["diagnosticCodes"]["marketOverview"] == "STALE_FORMAL_PUBLICATION"
    assert payload["mainTopics"] == []


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
