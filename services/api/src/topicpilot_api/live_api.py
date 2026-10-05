"""Read-only live operations endpoints for V2 operators and future clients."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from topicpilot_api.database import get_db
from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.persistence import read_live_status, read_live_tracking
from topicpilot_api.live.receipt import read_latest_receipt, read_receipts, receipt_to_dict
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


@router.get("/publication-receipt")
def publication_receipt(
    session: DbSession,
    trading_date: date | None = Query(None, alias="tradingDate"),  # noqa: B008
) -> dict:
    """Return the latest immutable daily formal publication receipt."""
    config = LiveRuntimeConfig.from_environment()
    target = trading_date or datetime.now(ZoneInfo(config.timezone_name)).date()
    receipt = read_latest_receipt(session, target)
    return {
        "status": "FOUND" if receipt is not None else "NOT_FOUND",
        "tradingDate": target.isoformat(),
        "receipt": receipt_to_dict(receipt) if receipt is not None else None,
    }


@router.get("/publication-receipts")
def publication_receipts(
    session: DbSession,
    trading_date: date | None = Query(None, alias="tradingDate"),  # noqa: B008
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """Return immutable receipt history for one operator-selected date."""
    config = LiveRuntimeConfig.from_environment()
    target = trading_date or datetime.now(ZoneInfo(config.timezone_name)).date()
    receipts = read_receipts(session, target, limit=limit)
    return {
        "tradingDate": target.isoformat(),
        "items": [receipt_to_dict(item) for item in receipts],
        "total": len(receipts),
        "limit": limit,
    }


__all__ = ["router"]
