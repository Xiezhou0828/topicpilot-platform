from __future__ import annotations

from fastapi.testclient import TestClient

from topicpilot_api.main import create_app


def test_formal_market_flow_route_is_read_only_and_documented() -> None:
    app = create_app()
    operation = app.openapi()["paths"]["/api/v2/market/institutional-flow"]["get"]
    assert "MarketInstitutionalFlowResponse" in str(operation["responses"])
    assert {parameter["name"] for parameter in operation["parameters"]} >= {
        "market",
        "asOf",
        "from",
        "to",
        "limit",
    }
    assert not any(
        getattr(route, "path", None) == "/api/v2/market/institutional-flow"
        and "POST" in getattr(route, "methods", set())
        for route in app.routes
    )


def test_formal_market_flow_invalid_market_fails_before_database_read() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v2/market/institutional-flow?market=FUND-B")
    assert response.status_code == 422
    assert "market must be TPE or TWO" in response.json()["detail"]
