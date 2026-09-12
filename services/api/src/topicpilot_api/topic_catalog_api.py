"""FastAPI routes for the minimum Topic read model."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from topicpilot_api.database import get_db
from topicpilot_api.problems import ApiProblem
from topicpilot_api.topic_catalog import (
    MAX_HISTORY_DAYS,
    TopicCatalogUnavailable,
    read_current_formal_snapshot,
    read_formal_snapshot_history,
    read_topic_minimum,
    read_topic_minimum_page,
)
from topicpilot_api.topic_catalog_schemas import (
    TopicCurrentSnapshotRead,
    TopicMinimumRead,
    TopicMinimumReadPage,
    TopicSnapshotHistoryReadPage,
)

router = APIRouter(prefix="/api/v2/topic-catalog", tags=["topic-catalog"])
DbSession = Annotated[Session, Depends(get_db)]
AsOfDate = Annotated[date | None, Query(alias="asOf")]


def _unavailable(exc: TopicCatalogUnavailable) -> ApiProblem:
    return ApiProblem(
        503,
        "Topic catalog unavailable",
        str(exc),
        "https://topicpilot.example/problems/not-ready",
    )


@router.get("", response_model=TopicMinimumReadPage, summary="Read the minimum Topic catalog")
def topic_catalog(
    session: DbSession,
    as_of: AsOfDate = None,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    try:
        return read_topic_minimum_page(session, as_of=as_of, limit=limit, offset=offset)
    except TopicCatalogUnavailable as exc:
        raise _unavailable(exc) from exc


@router.get(
    "/{slug}", response_model=TopicMinimumRead, summary="Read one minimum Topic catalog entry"
)
def topic_catalog_detail(slug: str, session: DbSession, as_of: AsOfDate = None) -> dict:
    try:
        return read_topic_minimum(session, slug, as_of=as_of)
    except TopicCatalogUnavailable as exc:
        raise _unavailable(exc) from exc


@router.get(
    "/{slug}/snapshot",
    response_model=TopicCurrentSnapshotRead,
    summary="Read the current formal leaf Topic Snapshot",
)
def current_topic_snapshot(
    slug: str, session: DbSession, as_of: AsOfDate = None
) -> dict:
    try:
        return read_current_formal_snapshot(session, slug, as_of=as_of)
    except TopicCatalogUnavailable as exc:
        raise _unavailable(exc) from exc


@router.get(
    "/{slug}/snapshots",
    response_model=TopicSnapshotHistoryReadPage,
    summary="Read bounded formal leaf Topic Snapshot history",
)
def topic_snapshot_history(
    slug: str,
    session: DbSession,
    as_of: AsOfDate = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    try:
        return read_formal_snapshot_history(
            session,
            slug,
            as_of=as_of,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )
    except TopicCatalogUnavailable as exc:
        raise _unavailable(exc) from exc
    except ValueError as exc:
        raise ApiProblem(
            422,
            "Request validation failed",
            str(exc),
            "https://topicpilot.example/problems/validation",
        ) from exc


__all__ = ["MAX_HISTORY_DAYS", "router"]
