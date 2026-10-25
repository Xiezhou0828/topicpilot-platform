from __future__ import annotations

from fastapi import APIRouter, Request

from .contract import CompanyResearchV4PublicResponse
from .store import FileCompanyResearchV4ReadStore

router = APIRouter(prefix="/api/v2", tags=["company-research-v4"])
_EMPTY_STORE = FileCompanyResearchV4ReadStore(None)


@router.get(
    "/stocks/{symbol}/research-v4",
    response_model=CompanyResearchV4PublicResponse,
    summary="Read owner-approved Company Research V4 projection",
)
def company_research_v4(symbol: str, request: Request) -> CompanyResearchV4PublicResponse:
    store = getattr(request.app.state, "company_research_v4_read_store", _EMPTY_STORE)
    return store.get_public(symbol)


__all__ = ["router"]
