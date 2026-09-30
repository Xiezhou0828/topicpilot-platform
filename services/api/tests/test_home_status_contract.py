from __future__ import annotations

from topicpilot_api.main import create_app
from topicpilot_api.schemas import MarketFlowLegRead, MarketFlowWindowRead


def test_home_market_overview_data_status_is_the_backend_owned_closed_set() -> None:
    schema = create_app().openapi()["components"]["schemas"]["HomeMarketOverview"]["properties"][
        "dataStatus"
    ]

    assert schema == {
        "enum": ["AVAILABLE", "PARTIAL", "UNAVAILABLE"],
        "title": "Datastatus",
        "type": "string",
    }


def test_home_institutional_flow_unavailable_units_are_typed_nullable() -> None:
    leg = MarketFlowLegRead.model_validate(
        {
            "buy": None,
            "sell": None,
            "net": None,
            "value": None,
            "unit": None,
            "scale": None,
            "status": "UNAVAILABLE",
        }
    )
    window = MarketFlowWindowRead.model_validate(
        {
            "requiredSessions": 5,
            "observedSessions": 0,
            "complete": False,
            "foreignNet": None,
            "investmentTrustNet": None,
            "dealerNet": None,
            "totalNet": None,
            "unit": None,
            "scale": None,
        }
    )

    assert leg.unit is None
    assert leg.scale is None
    assert window.unit is None
    assert window.scale is None
