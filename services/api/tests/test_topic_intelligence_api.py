from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from topicpilot_api.config import Settings
from topicpilot_api.main import create_app
from topicpilot_api.topic_engine import (
    ScoringPolicy,
    TopicScorer,
    build_historical_formula_research_corpus,
    load_historical_evidence_dataset,
    run_topic_intelligence,
)
from topicpilot_api.topic_intelligence_api import (
    get_topic_intelligence_result,
    serialize_topic_intelligence,
)

FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "research"
    / "topic_formula_historical_evidence.v1.json"
)


def _aggregations():
    corpus = build_historical_formula_research_corpus(load_historical_evidence_dataset(FIXTURE))
    return tuple(case.aggregates for case in corpus.cases)


def _deferred_result(index=0):
    return run_topic_intelligence(
        _aggregations()[index],
        TopicScorer("api-test-scorer.v1"),
        ScoringPolicy("deferred-api-test-policy", "v1"),
    )


def _client(result=None):
    app = create_app(Settings(DATABASE_URL="sqlite+pysqlite:///:memory:"))
    if result is not None:
        app.dependency_overrides[get_topic_intelligence_result] = lambda: result
    return TestClient(app)


def test_default_provider_returns_stable_problem_response():
    with _client() as client:
        response = client.get("/api/v1/topic-intelligence/latest")

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json() == {
        "type": "https://topicpilot.example/problems/topic-intelligence-unavailable",
        "title": "Topic Intelligence unavailable",
        "status": 503,
        "detail": "No approved Topic Intelligence runtime provider is configured.",
        "instance": "/api/v1/topic-intelligence/latest",
    }


def test_deferred_result_preserves_nulls_versions_and_evidence():
    result = _deferred_result()
    with _client(result) as client:
        response = client.get("/api/v1/topic-intelligence/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["contractVersion"] == "topic-intelligence-api.v1"
    assert body["mode"] == "EPHEMERAL"
    assert body["status"] == "DEFERRED"
    assert body["versions"] == {
        "featureSet": "synthetic-point-in-time-participation.v1",
        "featureRuntime": "historical-evidence-bridge.v1",
        "aggregation": "synthetic-participation-aggregate.v1",
        "scorerRuntime": "api-test-scorer.v1",
    }
    topic = body["topics"][0]
    assert topic["score"] is None
    assert topic["grade"] is None
    assert topic["confidence"] is None
    assert topic["components"] == [
        {"name": "breadth", "value": None},
        {"name": "leadership", "value": None},
    ]
    feature_by_name = {item["name"]: item for item in topic["evidence"]["features"]}
    assert feature_by_name["synthetic_breadth_participation_counts"]["coverage"] == 0.75
    assert feature_by_name["synthetic_breadth_participation_counts"]["value"] == {
        "positiveCount": 1,
        "unchangedCount": 1,
        "negativeCount": 1,
    }


def test_ineligible_result_remains_null_and_keeps_quality_reason():
    result = _deferred_result(1)
    with _client(result) as client:
        response = client.get("/api/v1/topic-intelligence/latest")

    topic = response.json()["topics"][0]
    assert topic["status"] == "DATA_INSUFFICIENT"
    assert topic["eligibility"] == "INELIGIBLE"
    assert topic["score"] is None
    assert topic["components"] == []
    assert "NO_EXPLICIT_LEADER_SET" in topic["evidence"]["qualityFlags"]


def test_synthetic_scored_result_serializes_without_registering_a_default():
    class TestOnlyAggregation:
        def aggregate(self, components, _policy):
            return (components["breadth"] + components["leadership"]) / 2

    def components(_aggregate):
        return {"leadership": 60.0, "breadth": 40.0}

    result = run_topic_intelligence(
        _aggregations()[0],
        TopicScorer(
            "api-test-scored-runtime.v1",
            component_collector=components,
            aggregation_policy=TestOnlyAggregation(),
        ),
        ScoringPolicy("synthetic-test-only", "v1"),
    )
    with _client(result) as client:
        response = client.get("/api/v1/topic-intelligence/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "AVAILABLE"
    assert body["topics"][0]["score"] == 50.0
    assert body["topics"][0]["grade"] is None


def test_serializer_canonicalizes_topic_component_feature_and_flag_order():
    result = _deferred_result()
    score = result.scores[0]
    evidence = replace(
        score.evidence,
        feature_results=tuple(reversed(score.evidence.feature_results)),
        quality_flags=tuple(reversed(score.evidence.quality_flags)),
    )
    reordered = replace(
        result,
        scores=(
            replace(
                score,
                components=tuple(reversed(score.components)),
                evidence=evidence,
            ),
        ),
    )

    assert serialize_topic_intelligence(result) == serialize_topic_intelligence(reordered)


def test_invalid_provider_output_is_sanitized_and_openapi_documents_route():
    result = _deferred_result()
    invalid_score = replace(result.scores[0], confidence=float("nan"))
    invalid = replace(result, scores=(invalid_score,))
    with _client(invalid) as client:
        response = client.get("/api/v1/topic-intelligence/latest")
        openapi = client.get("/openapi.json").json()

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "invalid evidence" in response.json()["detail"]
    operation = openapi["paths"]["/api/v1/topic-intelligence/latest"]["get"]
    assert operation["responses"].keys() >= {"200", "500", "503"}
