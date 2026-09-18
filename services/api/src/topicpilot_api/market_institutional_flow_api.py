"""Read-only API for the formal FUND-A market flow capability."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from topicpilot_api.database import get_db
from topicpilot_api.market_data.institutional_flow import (
    FlowFreshness,
    build_market_institutional_flow_trend,
)
from topicpilot_api.market_data.institutional_flow_persistence import (
    read_market_institutional_flow_history,
)
from topicpilot_api.problems import ApiProblem
from topicpilot_api.schemas import MarketInstitutionalFlowResponse

router = APIRouter(tags=["market-data"])

DbSession = Annotated[Session, Depends(get_db)]
OptionalMarket = Annotated[str | None, Query()]
OptionalAsOf = Annotated[date | None, Query(alias="asOf")]
OptionalFrom = Annotated[date | None, Query(alias="from")]
OptionalTo = Annotated[date | None, Query(alias="to")]
FlowLimit = Annotated[int, Query(ge=1, le=200)]


def _status(trends: list[dict]) -> str:
    available = [item["availability"] == "AVAILABLE" for item in trends]
    if all(available):
        return "AVAILABLE"
    if any(available):
        return "PARTIAL"
    return "UNAVAILABLE"


def _freshness(trends: list[dict]) -> str:
    values = {item["freshness"] for item in trends}
    if values == {FlowFreshness.CURRENT.value}:
        return FlowFreshness.CURRENT.value
    if FlowFreshness.STALE.value in values:
        return FlowFreshness.STALE.value
    return FlowFreshness.UNKNOWN.value


@router.get(
    "/api/v2/market/institutional-flow",
    response_model=MarketInstitutionalFlowResponse,
    summary="Read formal daily institutional flows for TPE and TWO",
)
def market_institutional_flow(
    session: DbSession,
    market: OptionalMarket = None,
    as_of: OptionalAsOf = None,
    from_date: OptionalFrom = None,
    to_date: OptionalTo = None,
    limit: FlowLimit = 25,
) -> dict:
    """Return current, previous, rolling-window, and evidence relations.

    ``from`` is accepted as a consumer-side window assertion.  The endpoint
    returns one trend envelope, bounded by ``to``/``asOf``; historical rows
    remain available through the same formal persistence contract.
    """

    if market is not None:
        market = market.upper()
        if market not in {"TPE", "TWO"}:
            raise ApiProblem(
                422,
                "Request validation failed",
                "market must be TPE or TWO",
                "https://topicpilot.example/problems/validation",
            )
    effective_as_of = to_date or as_of
    if from_date is not None and effective_as_of is not None and from_date > effective_as_of:
        raise ApiProblem(
            422,
            "Request validation failed",
            "from must be on or before to/asOf",
            "https://topicpilot.example/problems/validation",
        )

    markets = [market] if market else ["TPE", "TWO"]
    trends: list[dict] = []
    for market_code in markets:
        try:
            facts = read_market_institutional_flow_history(
                session,
                market_code,
                as_of_date=effective_as_of,
                limit=max(limit, 20),
            )
            trend = build_market_institutional_flow_trend(
                facts,
                market=market_code,
                as_of_date=effective_as_of,
            )
        except SQLAlchemyError:
            session.rollback()
            trend = build_market_institutional_flow_trend(
                (),
                market=market_code,
                as_of_date=effective_as_of,
            )
        trends.append(trend.to_dict())

    as_of_values = [item["asOfDate"] for item in trends if item["asOfDate"]]
    source_as_of_values = [item["sourceAsOf"] for item in trends if item["sourceAsOf"]]
    return {
        "contractVersion": "fund-a-market-institutional-flow.v1",
        "asOfDate": max(as_of_values)
        if as_of_values
        else (effective_as_of.isoformat() if effective_as_of else None),
        "status": _status(trends),
        "freshness": _freshness(trends),
        "markets": trends,
        "sourceAsOf": max(source_as_of_values) if source_as_of_values else None,
        "source": "TWSE BFI82U / TPEx tpex_3insti_summary",
        "unit": "TWD",
        "scale": 0,
    }


__all__ = ["router"]
