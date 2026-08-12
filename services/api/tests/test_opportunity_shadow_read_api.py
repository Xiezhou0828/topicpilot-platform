from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from topicpilot_api.main import create_app
from topicpilot_api.opportunity_shadow_api import get_shadow_read_service
from topicpilot_api.opportunity_shadow_read import (
    CanonicalOpportunityReadProvider,
    FixtureOpportunityReadProvider,
    OpportunityShadowReadService,
)
from topicpilot_api.problems import ApiProblem


def _client() -> TestClient:
    return TestClient(create_app())


def test_shadow_list_is_fixture_backed_and_keeps_strategy_local_caps() -> None:
    with _client() as client:
        response = client.get("/api/v1/opportunities/shadow")

    assert response.status_code == 200
    body = response.json()
    assert body["contractVersion"] == "opportunity-shadow-read.v1"
    assert body["publicationStatus"] == "SHADOW"
    assert body["dataStatus"] == "FIXTURE/SYNTHETIC"
    assert body["strategies"]["trendContinuation"]["candidateCount"] >= 3
    assert body["strategies"]["trendContinuation"]["presentedCount"] == 3
    assert body["strategies"]["catchUp"]["presentedCount"] == 2
    assert body["strategies"]["trendContinuation"]["fullRankingRetained"] is True
    assert {item["strategyId"] for item in body["opportunities"]} <= {
        "TREND_CONTINUATION",
        "CATCH_UP",
    }
    assert body["topic"] is None
    assert len(body["topics"]) >= 1
    assert (
        body["strategies"]["trendContinuation"]["backendCandidateCount"]
        == body["strategies"]["trendContinuation"]["candidateCount"]
    )
    assert (
        len(body["strategies"]["trendContinuation"]["backendRanking"])
        == body["strategies"]["trendContinuation"]["candidateCount"]
    )


def test_topic_projection_preserves_b_exception_provenance() -> None:
    with _client() as client:
        response = client.get("/api/v1/topics/topic-warming/opportunities/shadow")

    assert response.status_code == 200
    body = response.json()
    assert body["topic"]["grade"] == "B"
    card = body["opportunities"][0]
    assert card["qualification"]["class"] == "EXCEPTION_CANDIDATE"
    assert card["qualificationProvenance"]["exceptionCandidate"] is True
    assert "TOPIC_WARMING_SIGNAL" in card["qualificationProvenance"]["reasonCodes"]
    assert body["topicId"] == "topic-warming"
    assert body["topicGrade"] == "B"
    assert card["displayKey"] == "OPPORTUNITY_STATE_SELECTED"
    assert card["labelKey"].startswith("opportunity.strategy.")
    assert card["topicId"] == "topic-warming"
    assert card["policyVersion"]
    assert card["parameterVersion"]
    assert card["rankingProfileVersion"]


def test_stock_and_detail_projections_are_read_only_and_versioned() -> None:
    with _client() as client:
        stock_response = client.get("/api/v1/stocks/fixture-7/opportunities/shadow")
        assert stock_response.status_code == 200
        card = stock_response.json()["opportunities"][0]
        detail_response = client.get(f"/api/v1/opportunities/shadow/{card['opportunityId']}")

    assert detail_response.status_code == 200
    detail = detail_response.json()["opportunity"]
    assert detail["publicationStatus"] == "SHADOW"
    assert detail["detail"]["versions"]["policyVersion"]
    assert detail["detail"]["versions"]["parameterVersion"]
    assert detail["detail"]["versions"]["rankingProfileVersion"]
    assert "BUY" not in str(detail).upper()
    assert "SELL" not in str(detail).upper()


def test_filtering_has_empty_and_deferred_semantics() -> None:
    with _client() as client:
        empty = client.get("/api/v1/opportunities/shadow?topicId=missing-topic")
        deferred = client.get("/api/v1/opportunities/shadow?state=DEFERRED")

    assert empty.status_code == 200
    assert empty.json()["status"] == "EMPTY"
    assert deferred.status_code == 200
    assert deferred.json()["status"] == "DEFERRED"


def test_fixture_provider_covers_all_states_for_both_strategy_sections() -> None:
    with _client() as client:
        body = client.get("/api/v1/opportunities/shadow").json()

    for key in ("trendContinuation", "catchUp"):
        states = {item["opportunityState"] for item in body["strategies"][key]["backendRanking"]}
        assert states == {
            "SELECTED",
            "WAITING_RETEST",
            "WAITING_CONFIRMATION",
            "DEFERRED",
            "EXCLUDED",
        }


def test_known_empty_topic_and_stock_are_not_confused_with_missing_resources() -> None:
    with _client() as client:
        topic = client.get("/api/v1/topics/topic-empty/opportunities/shadow")
        stock = client.get("/api/v1/stocks/fixture-empty-stock/opportunities/shadow")
        missing = client.get("/api/v1/topics/not-a-topic/opportunities/shadow")

    assert topic.status_code == 200
    assert topic.json()["status"] == "EMPTY"
    assert topic.json()["topicGrade"] == "S"
    assert stock.status_code == 200
    assert stock.json()["status"] == "EMPTY"
    assert missing.status_code == 404


def test_same_stock_can_have_multiple_topics_and_strategies() -> None:
    with _client() as client:
        response = client.get("/api/v1/stocks/fixture-shared/opportunities/shadow")

    assert response.status_code == 200
    cards = response.json()["opportunities"]
    assert {card["topicId"] for card in cards} == {"topic-shared-a", "topic-shared-b"}
    assert {card["strategyId"] for card in cards} == {"TREND_CONTINUATION", "CATCH_UP"}


def test_openapi_documents_additive_shadow_contract_without_recommendation_queries() -> None:
    with _client() as client:
        openapi = client.get("/openapi.json").json()
        operation = openapi["paths"]["/api/v1/opportunities/shadow"]["get"]

    assert {
        "/api/v1/opportunities/shadow",
        "/api/v1/topics/{topic_id}/opportunities/shadow",
        "/api/v1/stocks/{instrument_id}/opportunities/shadow",
        "/api/v1/opportunities/shadow/{opportunity_id}",
    } <= set(openapi["paths"])
    names = {parameter["name"] for parameter in operation["parameters"]}
    assert {
        "strategy",
        "state",
        "topicId",
        "instrumentId",
        "grade",
        "lifecycle",
        "limit",
        "page",
        "cursor",
    } <= names
    assert not {"minimumOpportunityScore", "buy", "expectedReturn"} & names


def test_provider_interface_has_canonical_unavailable_placeholder() -> None:
    fixture = FixtureOpportunityReadProvider()
    assert fixture.data_status == "FIXTURE/SYNTHETIC"
    service = OpportunityShadowReadService(CanonicalOpportunityReadProvider())
    with pytest.raises(ApiProblem) as error:
        service.list_opportunities()
    assert error.value.status == 503


def test_shadow_api_fail_closes_when_canonical_provider_is_not_available() -> None:
    app = create_app()
    app.dependency_overrides[get_shadow_read_service] = lambda: OpportunityShadowReadService(
        CanonicalOpportunityReadProvider()
    )
    with TestClient(app) as client:
        response = client.get("/api/v1/opportunities/shadow")

    assert response.status_code == 503
    assert response.json()["type"].endswith("/opportunity-shadow-unavailable")


def test_shadow_payload_has_no_fake_performance_or_trading_instruction_fields() -> None:
    with _client() as client:
        payload = client.get("/api/v1/opportunities/shadow").json()

    serialized = str(payload).upper()
    assert "WIN_RATE" not in serialized
    assert "EXPECTED_RETURN" not in serialized
    assert "TARGET_PRICE" not in serialized
    assert "STOP_LOSS" not in serialized
    assert "STRONG_BUY" not in serialized
