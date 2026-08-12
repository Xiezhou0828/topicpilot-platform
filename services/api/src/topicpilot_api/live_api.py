"""Read-only live operations endpoints for V2 operators and future clients."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from topicpilot_api.database import get_db
from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.persistence import read_live_status, read_live_tracking
from topicpilot_api.schemas import LiveStatusResponse, LiveTrackingResponse, Page

router = APIRouter(prefix="/api/v1/operations/live", tags=["live-operations"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/status", response_model=LiveStatusResponse)
def status(session: DbSession) -> dict:
    return read_live_status(session)


@router.get("/tracking", response_model=Page[LiveTrackingResponse])
def tracking(
    session: DbSession,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    items, total = read_live_tracking(session, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/configuration")
def configuration() -> dict:
    config = LiveRuntimeConfig.from_environment()
    return {"status": "CONFIGURED", "configuration": config.as_dict()}


__all__ = ["router"]
