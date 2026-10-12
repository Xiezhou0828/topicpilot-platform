from __future__ import annotations

from fastapi import APIRouter, Request

from .contract import PublicCompanyResearchProjection
from .store import CompanyResearchReadStore, EmptyCompanyResearchReadStore

router = APIRouter(prefix="/api/v2", tags=["company-research"])
_EMPTY_STORE = EmptyCompanyResearchReadStore()


def _store(request: Request) -> CompanyResearchReadStore:
    return getattr(request.app.state, "company_research_read_store", _EMPTY_STORE)


@router.get(
    "/stocks/{symbol}/research",
    response_model=PublicCompanyResearchProjection,
)
def company_research(symbol: str, request: Request) -> PublicCompanyResearchProjection:
    return _store(request).get_public(symbol)
