from __future__ import annotations

from topicpilot_api.main import create_app


def test_home_market_overview_data_status_is_the_backend_owned_closed_set() -> None:
    schema = create_app().openapi()["components"]["schemas"]["HomeMarketOverview"]["properties"]["dataStatus"]

    assert schema == {
        "enum": ["PARTIAL", "UNAVAILABLE"],
        "title": "Datastatus",
        "type": "string",
    }
