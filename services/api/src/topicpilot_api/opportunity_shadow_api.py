"""Shadow-only Opportunity read API for TASK-BE-024C."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from topicpilot_api.opportunity_shadow_read import (
    OpportunityShadowReadService,
    get_shadow_read_service,
)
from topicpilot_api.schemas import OpportunityShadowResponse

router = APIRouter(prefix="/api/v1", tags=["opportunity-shadow"])
ShadowService = Annotated[OpportunityShadowReadService, Depends(get_shadow_read_service)]
OptionalStrategy = Annotated[str | None, Query()]
OptionalState = Annotated[str | None, Query()]
OptionalTopic = Annotated[str | None, Query(alias="topicId")]
OptionalInstrument = Annotated[str | None, Query(alias="instrumentId")]
OptionalGrade = Annotated[str | None, Query()]
OptionalLifecycle = Annotated[str | None, Query()]
Limit = Annotated[int, Query(ge=1, le=100)]
Page = Annotated[int, Query(ge=1)]
Cursor = Annotated[str | None, Query()]


def _filters(
    strategy: str | None,
    state: str | None,
    topic_id: str | None,
    instrument_id: str | None,
    grade: str | None,
    lifecycle: str | None,
) -> dict[str, str | None]:
    return {
        "strategy": strategy,
        "state": state,
        "topic_id": topic_id,
        "instrument_id": instrument_id,
        "grade": grade,
        "lifecycle": lifecycle,
    }


@router.get(
    "/opportunities/shadow",
    response_model=OpportunityShadowResponse,
    summary="Read deterministic shadow Opportunity projections",
)
def list_shadow_opportunities(
    service: ShadowService,
    strategy: OptionalStrategy = None,
    state: OptionalState = None,
    topic_id: OptionalTopic = None,
    instrument_id: OptionalInstrument = None,
    grade: OptionalGrade = None,
    lifecycle: OptionalLifecycle = None,
    limit: Limit = 50,
    page: Page = 1,
    cursor: Cursor = None,
) -> dict:
    return service.list_opportunities(
        **_filters(strategy, state, topic_id, instrument_id, grade, lifecycle),
        limit=limit,
        page=page,
        cursor=cursor,
    )


@router.get(
    "/topics/{topic_id}/opportunities/shadow",
    response_model=OpportunityShadowResponse,
    summary="Read a topic-oriented shadow Opportunity projection",
)
def topic_shadow_opportunities(
    topic_id: str,
    service: ShadowService,
    strategy: OptionalStrategy = None,
    state: OptionalState = None,
    grade: OptionalGrade = None,
    lifecycle: OptionalLifecycle = None,
    limit: Limit = 50,
    page: Page = 1,
    cursor: Cursor = None,
) -> dict:
    return service.topic_opportunities(
        topic_id,
        strategy=strategy,
        state=state,
        grade=grade,
        lifecycle=lifecycle,
        limit=limit,
        page=page,
        cursor=cursor,
    )


@router.get(
    "/stocks/{instrument_id}/opportunities/shadow",
    response_model=OpportunityShadowResponse,
    summary="Read a stock-oriented shadow Opportunity projection",
)
def stock_shadow_opportunities(
    instrument_id: str,
    service: ShadowService,
    strategy: OptionalStrategy = None,
    state: OptionalState = None,
    topic_id: OptionalTopic = None,
    grade: OptionalGrade = None,
    lifecycle: OptionalLifecycle = None,
    limit: Limit = 50,
    page: Page = 1,
    cursor: Cursor = None,
) -> dict:
    return service.stock_opportunities(
        instrument_id,
        strategy=strategy,
        state=state,
        topic_id=topic_id,
        grade=grade,
        lifecycle=lifecycle,
        limit=limit,
        page=page,
        cursor=cursor,
    )


@router.get(
    "/opportunities/shadow/{opportunity_id:path}",
    response_model=OpportunityShadowResponse,
    summary="Read one shadow Opportunity detail projection",
)
def shadow_opportunity_detail(opportunity_id: str, service: ShadowService) -> dict:
    return service.detail(opportunity_id)


__all__ = ["router"]
