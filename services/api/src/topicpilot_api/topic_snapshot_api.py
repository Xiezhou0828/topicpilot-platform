"""Read API for the formal V2 topic snapshot history."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from topicpilot_api.database import get_db
from topicpilot_api.orm import TopicSnapshot
from topicpilot_api.schemas import TopicSnapshotPage

router = APIRouter(prefix="/api/v2", tags=["topic-snapshots"])
DbSession = Annotated[Session, Depends(get_db)]
SnapshotDate = Annotated[date | None, Query(alias="date")]
Latest = Annotated[bool, Query()]
TopicFilter = Annotated[str | None, Query(description="Topic slug")]
Limit = Annotated[int, Query(ge=1, le=500)]
Offset = Annotated[int, Query(ge=0)]


def _serialize(row: TopicSnapshot) -> dict:
    return {
        "snapshotDate": row.snapshot_date,
        "topicId": str(row.topic_id),
        "topicSlug": row.topic_slug,
        "topicName": row.topic_name,
        "parentTopic": row.parent_topic,
        "marketGrade": row.market_grade,
        "topicScore": row.topic_score,
        "topicDirection": row.topic_direction,
        "stockCount": row.stock_count,
        "strongStockCount": row.strong_stock_count,
        "weakStockCount": row.weak_stock_count,
        "averageChange": row.average_change,
        "observedStockCount": row.observed_stock_count,
        "coveragePct": row.coverage_pct,
        "dataStatus": row.data_status,
        "scoreStatus": row.score_status,
        "calculationVersion": row.calculation_version,
        "updatedAt": row.updated_at,
    }


@router.get(
    "/topic-snapshots",
    response_model=TopicSnapshotPage,
    summary="Read V2 topic snapshots by date or history",
)
def list_topic_snapshots(
    session: DbSession,
    snapshot_date: SnapshotDate = None,
    latest: Latest = True,
    topic: TopicFilter = None,
    limit: Limit = 200,
    offset: Offset = 0,
) -> dict:
    filters = []
    if snapshot_date is not None:
        filters.append(TopicSnapshot.snapshot_date == snapshot_date)
    if topic:
        filters.append(TopicSnapshot.topic_slug == topic)
    if latest and snapshot_date is None:
        latest_dates = (
            select(
                TopicSnapshot.topic_id,
                func.max(TopicSnapshot.snapshot_date).label("latest_date"),
            )
            .group_by(TopicSnapshot.topic_id)
            .subquery()
        )
        query = select(TopicSnapshot).join(
            latest_dates,
            (latest_dates.c.topic_id == TopicSnapshot.topic_id)
            & (latest_dates.c.latest_date == TopicSnapshot.snapshot_date),
        )
        count_query = None
    else:
        query = select(TopicSnapshot)
        count_query = select(func.count()).select_from(TopicSnapshot)
    if filters:
        query = query.where(*filters)
    if count_query is None:
        count_query = select(func.count()).select_from(query.subquery())
    else:
        count_query = count_query.where(*filters)
    rows = list(
        session.scalars(
            query.order_by(TopicSnapshot.snapshot_date.desc(), TopicSnapshot.topic_slug)
            .limit(limit)
            .offset(offset)
        )
    )
    total = int(session.scalar(count_query) or 0)
    return {
        "items": [_serialize(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "query": {
            "date": snapshot_date,
            "latest": latest,
            "topic": topic,
        },
    }


__all__ = ["router"]
