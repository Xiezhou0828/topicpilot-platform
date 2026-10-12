from __future__ import annotations

from fastapi import APIRouter, Request

from .contract import (
    FinancialCoverageResponse,
    FinancialEpsBridgeResponse,
    FinancialResearchStatusResponse,
    FinancialStatementResponse,
    FinancialSummaryResponse,
)
from .store import EmptyFinancialResearchStore, FinancialResearchReadStore

router = APIRouter(prefix="/api/v2", tags=["financial-research"])
_EMPTY_STORE = EmptyFinancialResearchStore()


def _store(request: Request) -> FinancialResearchReadStore:
    return getattr(request.app.state, "financial_research_store", _EMPTY_STORE)


@router.get("/stocks/{symbol}/financial-coverage", response_model=FinancialCoverageResponse)
def financial_coverage(symbol: str, request: Request) -> FinancialCoverageResponse:
    return _store(request).coverage(symbol.strip())


@router.get("/stocks/{symbol}/financial-summary", response_model=FinancialSummaryResponse)
def financial_summary(symbol: str, request: Request) -> FinancialSummaryResponse:
    return _store(request).summary(symbol.strip())


@router.get("/stocks/{symbol}/financial-statements", response_model=FinancialStatementResponse)
def financial_statements(symbol: str, request: Request) -> FinancialStatementResponse:
    return _store(request).statements(symbol.strip())


@router.get(
    "/stocks/{symbol}/financial-research-status", response_model=FinancialResearchStatusResponse
)
def financial_research_status(symbol: str, request: Request) -> FinancialResearchStatusResponse:
    return _store(request).status(symbol.strip())


@router.get("/stocks/{symbol}/eps-bridge", response_model=FinancialEpsBridgeResponse)
def eps_bridge(symbol: str, request: Request) -> FinancialEpsBridgeResponse:
    return _store(request).eps_bridge(symbol.strip())


__all__ = ["router"]
