from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from sqlalchemy.exc import SQLAlchemyError

from topicpilot_api.database import get_session_factory

from .contract import CompanyResearchV4PublicResponse
from .database_store import DatabaseCompanyProfileV4ReadStore
from .store import FileCompanyProfileV4ReadStore

router = APIRouter(prefix="/api/v2", tags=["company-research-v4"])
_EMPTY_STORE = FileCompanyProfileV4ReadStore(None)
logger = logging.getLogger(__name__)


@router.get(
    "/stocks/{symbol}/research-v4",
    response_model=CompanyResearchV4PublicResponse,
    summary="Read owner-approved Company Research V4 projection",
)
def company_research_v4(symbol: str, request: Request) -> CompanyResearchV4PublicResponse:
    store = getattr(request.app.state, "company_profile_v4_read_store", _EMPTY_STORE)
    if store.path is not None:
        return store.get_public(symbol)
    try:
        with get_session_factory()() as session:
            return DatabaseCompanyProfileV4ReadStore(session).get_public(symbol)
    except SQLAlchemyError:
        logger.exception("Company Research V4 database read failed")
        return CompanyResearchV4PublicResponse(
            stockCode=symbol.strip(),
            publicationStatus="BLOCKED",
            limitationsZhTw=["公司研究資料目前無法讀取，請稍後再試。"],  # noqa: RUF001
        )


__all__ = ["router"]
