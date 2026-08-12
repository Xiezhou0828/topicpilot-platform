from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from topicpilot_api.config import Settings
from topicpilot_api.main import create_app
from topicpilot_api.topic_engine import RecommendationCandidateFact, build_recommendations
from topicpilot_api.topic_engine.scoring_contracts import TopicScore
from topicpilot_api.topic_recommendation_api import get_recommendation_result

AS_OF = date(2026, 8, 9)


def _runtime():
    return SimpleNamespace(
        as_of=AS_OF,
        feature_set_version="features.v1",
        feature_runtime_version="runtime.v1",
        aggregation_version="aggregation.v1",
        scorer_runtime_version="scorer.v1",
        policy_id="policy",
        policy_version="policy.v1",
        scores=(
            TopicScore(
                "t1",
                AS_OF,
                "policy",
                "policy.v1",
                "features.v1",
                "runtime.v1",
                "aggregation.v1",
                "SCORED",
                score=7.5,
                grade="A",
                strength="STRONG",
                components=(("breadth", 7.5),),
                eligibility="ELIGIBLE",
            ),
        ),
    )


def _client(result=None):
    app = create_app(Settings(DATABASE_URL="sqlite+pysqlite:///:memory:"))
    if result is not None:
        app.dependency_overrides[get_recommendation_result] = lambda: result
    return TestClient(app)


def test_default_recommendation_provider_is_fail_closed():
    with _client() as client:
        response = client.get("/api/v1/recommendations/latest")

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["type"].endswith("/recommendation-unavailable")


def test_recommendation_api_preserves_downstream_context_and_evidence():
    result = build_recommendations(
        _runtime(),
        (RecommendationCandidateFact("candidate-1", "t1", "Topic One", ("manual",)),),
    )
    with _client(result) as client:
        response = client.get("/api/v1/recommendations/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["contractVersion"] == "recommendation-api.v1"
    assert body["status"] == "AVAILABLE"
    assert body["items"] == [
        {
            "candidateId": "candidate-1",
            "topicId": "t1",
            "label": "Topic One",
            "status": "AVAILABLE",
            "reason": "TOPIC_INTELLIGENCE_AVAILABLE",
            "topicContext": {
                "asOf": "2026-08-09",
                "scorerRuntimeVersion": "scorer.v1",
                "featureSetVersion": "features.v1",
                "featureRuntimeVersion": "runtime.v1",
                "aggregationVersion": "aggregation.v1",
                "policyId": "policy",
                "policyVersion": "policy.v1",
                "eligibility": "ELIGIBLE",
                "score": 7.5,
                "grade": "A",
                "confidence": None,
                "components": [{"name": "breadth", "value": 7.5}],
                "evidenceReference": [],
            },
            "evidence": ["manual"],
        }
    ]


def test_recommendation_route_is_documented_in_openapi():
    with _client() as client:
        operation = client.get("/openapi.json").json()["paths"][
            "/api/v1/recommendations/latest"
        ]["get"]

    assert operation["responses"].keys() >= {"200", "503"}
