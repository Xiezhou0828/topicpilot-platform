"""FastAPI routes for the formal V2 stock and topic read models."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from topicpilot_api.database import get_db
from topicpilot_api.historical_read_model import read_historical_bars
from topicpilot_api.problems import ApiProblem
from topicpilot_api.production_read_model import read_stock, read_stocks, read_topic, read_topics
from topicpilot_api.schemas import (
    HistoricalPriceHistoryResponse,
    StockReadModel,
    StockReadModelPage,
    StockTechnicalPublicationRead,
    TopicReadModel,
    TopicReadModelPage,
)
from topicpilot_api.technical_publication import build_technical_publication

router = APIRouter(prefix="/api/v2", tags=["production-read-model"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/stocks", response_model=StockReadModelPage, summary="Read the formal TPE/TWO stock universe"
)
def stocks(
    session: DbSession,
    market: str | None = Query(default=None),
    topic: str | None = Query(default=None, description="Formal topic slug"),
    update_mode: str | None = Query(default=None, alias="updateMode"),
    search: str | None = Query(
        default=None,
        description="Case-insensitive deterministic substring search over stock code or name",
    ),
    sort: str = Query(default="symbolAsc"),
    limit: int = Query(default=1000, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict:
    try:
        return read_stocks(
            session,
            market=market,
            topic=topic,
            update_mode=update_mode,
            search=search,
            sort=sort,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise ApiProblem(
            422,
            "Request validation failed",
            str(exc),
            "https://topicpilot.example/problems/validation",
        ) from exc


@router.get(
    "/stocks/{symbol}/price-history",
    response_model=HistoricalPriceHistoryResponse,
    summary="Read bounded canonical daily price history",
)
def stock_price_history(
    symbol: str,
    session: DbSession,
    from_date: Annotated[date, Query(alias="from")],
    to_date: Annotated[date, Query(alias="to")],
    market_code: Annotated[str | None, Query(alias="market")] = None,
    limit: int = Query(default=200, ge=1, le=200),
) -> dict:
    if to_date < from_date:
        raise ApiProblem(
            422,
            "Request validation failed",
            "to must be on or after from",
            "https://topicpilot.example/problems/validation",
        )
    try:
        return read_historical_bars(
            session,
            symbol,
            from_date,
            to_date,
            market_code,
            limit,
        )
    except ValueError as exc:
        raise ApiProblem(
            422,
            "Request validation failed",
            str(exc),
            "https://topicpilot.example/problems/validation",
        ) from exc


@router.get(
    "/stocks/{symbol}/technical",
    response_model=StockTechnicalPublicationRead,
    summary="Read Stock Technical V0 evidence and bounded publication status",
)
def stock_technical(
    symbol: str,
    session: DbSession,
    from_date: Annotated[date, Query(alias="from")],
    to_date: Annotated[date, Query(alias="to")],
    market_code: Annotated[str | None, Query(alias="market")] = None,
    limit: int = Query(default=200, ge=1, le=200),
) -> dict:
    if to_date < from_date:
        raise ApiProblem(
            422,
            "Request validation failed",
            "to must be on or after from",
            "https://topicpilot.example/problems/validation",
        )
    try:
        history = read_historical_bars(
            session,
            symbol,
            from_date,
            to_date,
            market_code,
            limit,
        )
        return build_technical_publication(history)
    except ValueError as exc:
        raise ApiProblem(
            422,
            "Request validation failed",
            str(exc),
            "https://topicpilot.example/problems/validation",
        ) from exc


@router.get("/stocks/{symbol}", response_model=StockReadModel, summary="Read one formal stock")
def stock(symbol: str, session: DbSession) -> dict:
    return read_stock(session, symbol)


@router.get(
    "/topics", response_model=TopicReadModelPage, summary="Read the formal topic read model"
)
def topics(
    session: DbSession,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    return read_topics(session, limit=limit, offset=offset)


@router.get("/topics/{slug}", response_model=TopicReadModel, summary="Read one formal topic")
def topic(slug: str, session: DbSession) -> dict:
    return read_topic(session, slug)


__all__ = ["router"]
