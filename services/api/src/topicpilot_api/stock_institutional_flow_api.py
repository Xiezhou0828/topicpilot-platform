"""FastAPI projection for the read-only FUND-B stock flow contract."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from topicpilot_api.database import get_db
from topicpilot_api.problems import ApiProblem
from topicpilot_api.schemas import StockInstitutionalFlowResponse
from topicpilot_api.stock_institutional_flow_persistence import (
    read_stock_institutional_flow_features,
)

router = APIRouter(prefix="/api/v2", tags=["production-read-model"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/stocks/{symbol}/institutional-flow",
    response_model=StockInstitutionalFlowResponse,
    summary="Read formal stock-level institutional-flow evidence",
    responses={503: {"description": "FUND-B storage is unavailable"}},
)
def stock_institutional_flow(
    symbol: str,
    session: DbSession,
    market: str | None = Query(default=None),
    as_of: Annotated[date | None, Query(alias="asOf")] = None,
    limit: int = Query(default=200, ge=1, le=200),
) -> dict:
    requested_as_of = as_of or date.today()
    try:
        features = read_stock_institutional_flow_features(
            session,
            symbol,
            market,
            requested_as_of,
            limit,
        )
    except ApiProblem:
        raise
    except ValueError as exc:
        raise ApiProblem(
            422,
            "Request validation failed",
            str(exc),
            "https://topicpilot.example/problems/validation",
        ) from exc
    except SQLAlchemyError as exc:
        raise ApiProblem(
            503,
            "FUND-B storage unavailable",
            (
                "The stock institutional-flow read model is unavailable or migrations have "
                "not completed."
            ),
            "https://topicpilot.example/problems/not-ready",
        ) from exc
    return features.to_dict()


__all__ = ["router"]
