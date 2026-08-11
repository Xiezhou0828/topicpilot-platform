from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from topicpilot_api.admin import router as admin_router
from topicpilot_api.config import Settings, get_settings
from topicpilot_api.constants import STRATEGY_HORIZONS, STRATEGY_KEYS
from topicpilot_api.database import get_db
from topicpilot_api.home_read_model import build_home_read_model
from topicpilot_api.live_api import router as live_router
from topicpilot_api.problems import ApiProblem, NotFoundProblem, install_problem_handlers
from topicpilot_api.repository import (
    data_status,
    get_stock,
    get_topic,
    latest_completed_run,
    list_candidates,
    list_price_history,
    list_stocks,
    list_strategies,
    list_topics,
    strategy_performance,
    topic_rotation,
)
from topicpilot_api.schemas import (
    CandidateResponse,
    DataStatus,
    HealthResponse,
    HistoricalPriceHistoryResponse,
    HomeResponse,
    Page,
    SnapshotResponse,
    StockResponse,
    StockSummary,
    StrategyPerformanceResponse,
    StrategyResponse,
    TopicResponse,
    TopicRotationResponse,
    TopicSummary,
)
from topicpilot_api.snapshot import assemble_snapshot
from topicpilot_api.topic_intelligence_api import router as topic_intelligence_router
from topicpilot_api.topic_recommendation_api import router as recommendation_router
from topicpilot_api.production_read_model_api import router as production_read_model_router
from topicpilot_api.topic_snapshot_api import router as topic_snapshot_router

DbSession = Annotated[Session, Depends(get_db)]
Limit = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0)]
OptionalDataDate = Annotated[date | None, Query()]
HistoryFrom = Annotated[date, Query(alias="from")]
HistoryTo = Annotated[date, Query(alias="to")]
OptionalMarketCode = Annotated[str | None, Query(alias="market")]


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    application = FastAPI(
        title="TopicPilot Enterprise Read API",
        version="0.1.0",
        description=(
            "Read-only API backed by a rebuildable PostgreSQL read model. "
            "The public deployment contains synthetic data only."
        ),
    )
    application.state.settings = app_settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(app_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
    )
    install_problem_handlers(application)
    application.include_router(admin_router)
    application.include_router(topic_intelligence_router)
    application.include_router(recommendation_router)
    application.include_router(production_read_model_router)
    application.include_router(topic_snapshot_router)
    application.include_router(live_router)

    @application.get("/healthz", response_model=HealthResponse, tags=["operations"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @application.get(
        "/readyz",
        response_model=HealthResponse,
        tags=["operations"],
        responses={503: {"description": "Database unavailable"}},
    )
    def readyz(session: DbSession) -> dict[str, str]:
        try:
            session.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise ApiProblem(
                503,
                "Service not ready",
                "PostgreSQL is unavailable or migrations have not completed.",
                "https://topicpilot.example/problems/not-ready",
            ) from exc
        return {"status": "ready"}

    @application.get("/api/v1/meta/data-status", response_model=DataStatus, tags=["metadata"])
    def api_data_status(session: DbSession, request: Request) -> dict:
        run = latest_completed_run(session)
        if run is None:
            raise NotFoundProblem("No completed bundle has been imported")
        return data_status(run, request.app.state.settings.freshness_days)

    @application.get("/api/v2/home", response_model=HomeResponse, tags=["home"])
    def home(session: DbSession) -> dict:
        return build_home_read_model(session)

    @application.get(
        "/api/v1/snapshot/latest", response_model=SnapshotResponse, tags=["compatibility"]
    )
    def snapshot_latest(session: DbSession) -> dict:
        run = latest_completed_run(session)
        if run is None:
            raise NotFoundProblem("No completed bundle has been imported")
        return assemble_snapshot(session, run)

    @application.get("/api/v1/stocks", response_model=Page[StockSummary], tags=["stocks"])
    def stocks(session: DbSession, limit: Limit = 50, offset: Offset = 0) -> dict:
        items, total = list_stocks(session, limit, offset)
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    @application.get("/api/v1/stocks/{code}", response_model=StockResponse, tags=["stocks"])
    def stock(code: str, session: DbSession) -> dict:
        return get_stock(session, code)

    @application.get(
        "/api/v1/stocks/{code}/price-history",
        response_model=HistoricalPriceHistoryResponse,
        tags=["market-data"],
        responses={409: {"description": "Ambiguous instrument identity"}},
    )
    def stock_price_history(
        code: str,
        session: DbSession,
        from_date: HistoryFrom,
        to_date: HistoryTo,
        market_code: OptionalMarketCode = None,
        limit: Limit = 200,
    ) -> dict:
        if to_date < from_date:
            raise ApiProblem(
                422,
                "Request validation failed",
                "to must be on or after from",
                "https://topicpilot.example/problems/validation",
            )
        return list_price_history(session, code, from_date, to_date, market_code, limit)

    @application.get("/api/v1/topics", response_model=Page[TopicSummary], tags=["topics"])
    def topics(session: DbSession, limit: Limit = 50, offset: Offset = 0) -> dict:
        items, total = list_topics(session, limit, offset)
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    @application.get("/api/v1/topics/{slug}", response_model=TopicResponse, tags=["topics"])
    def topic(slug: str, session: DbSession) -> dict:
        return get_topic(session, slug)

    @application.get(
        "/api/v1/strategies", response_model=Page[StrategyResponse], tags=["strategies"]
    )
    def strategies(session: DbSession, limit: Limit = 50, offset: Offset = 0) -> dict:
        items, total = list_strategies(session, limit, offset)
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    @application.get(
        "/api/v1/strategies/{key}/candidates",
        response_model=Page[CandidateResponse],
        tags=["strategies"],
    )
    def candidates(
        key: str,
        session: DbSession,
        data_date: OptionalDataDate = None,
        limit: Limit = 50,
        offset: Offset = 0,
    ) -> dict:
        normalized_key = key.upper()
        if normalized_key not in STRATEGY_KEYS:
            raise NotFoundProblem(f"Strategy {key!r} was not found")
        items, total = list_candidates(session, normalized_key, data_date, limit, offset)
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    @application.get(
        "/api/v1/analytics/topic-rotation",
        response_model=Page[TopicRotationResponse],
        tags=["analytics"],
    )
    def rotation(
        session: DbSession,
        days: int = Query(default=14, ge=2, le=60),
        limit: Limit = 50,
        offset: Offset = 0,
    ) -> dict:
        items, total = topic_rotation(session, days, limit, offset)
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    @application.get(
        "/api/v1/analytics/strategy-performance",
        response_model=Page[StrategyPerformanceResponse],
        tags=["analytics"],
    )
    def performance(
        session: DbSession,
        strategy_key: str | None = Query(default=None),
        horizon: str | None = Query(default=None),
        data_date: OptionalDataDate = None,
        limit: Limit = 50,
        offset: Offset = 0,
    ) -> dict:
        normalized_key = strategy_key.upper() if strategy_key else None
        if normalized_key is not None and normalized_key not in STRATEGY_KEYS:
            raise NotFoundProblem(f"Strategy {strategy_key!r} was not found")
        if horizon is not None and horizon not in STRATEGY_HORIZONS:
            raise ApiProblem(
                422,
                "Request validation failed",
                f"horizon must be one of {list(STRATEGY_HORIZONS)}",
                "https://topicpilot.example/problems/validation",
            )
        items, total = strategy_performance(
            session, normalized_key, horizon, data_date, limit, offset
        )
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    return application


app = create_app()
