"""Read API for the formal V2 topic snapshot history."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
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


def _formal_published_filter():
    return and_(
        TopicSnapshot.publication_mode == "FORMAL",
        TopicSnapshot.publication_state == "PUBLISHED",
        TopicSnapshot.superseded_by_snapshot_id.is_(None),
    )


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
        "publicationMode": row.publication_mode,
        "membershipMode": row.membership_mode,
        "relationVersion": row.relation_version,
        "mappingEffectiveFrom": row.mapping_effective_from,
        "membershipSnapshotId": row.membership_snapshot_id,
        "membershipSnapshotHash": row.membership_snapshot_hash,
        "sessionCode": row.session_code,
        "calendarCode": row.calendar_code,
        "tradingDayState": row.trading_day_state,
        "generatedState": row.generated_state,
        "finalityState": row.finality_state,
        "publicationState": row.publication_state,
        "generatedAt": row.generated_at,
        "asOfAt": row.as_of_at,
        "finalizedAt": row.finalized_at,
        "publishedAt": row.published_at,
        "expectedCount": row.expected_count,
        "eligibleCount": row.eligible_count,
        "noTradeCount": row.no_trade_count,
        "unknownCount": row.unknown_count,
        "excludedCount": row.excluded_count,
        "positiveCount": row.positive_count,
        "flatCount": row.flat_count,
        "negativeCount": row.negative_count,
        "freshnessState": row.freshness_state,
        "unavailableReason": row.unavailable_reason,
        "qualityFlags": row.quality_flags,
        "referenceRegistryVersion": row.reference_registry_version,
        "mappingPolicyVersion": row.mapping_policy_version,
        "sourceRunId": row.source_run_id,
        "sourceArtifactId": row.source_artifact_id,
        "sourceArtifactHash": row.source_artifact_hash,
        "lineageHash": row.lineage_hash,
        "snapshotIdentity": row.snapshot_identity,
        "correctionSequence": row.correction_sequence,
        "supersedesSnapshotId": str(row.supersedes_snapshot_id)
        if row.supersedes_snapshot_id
        else None,
        "supersessionReason": row.supersession_reason,
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
    filters = [_formal_published_filter()]
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
            .where(_formal_published_filter())
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
            "availability": (
                "UNAVAILABLE_PRE_FORMAL_BOUNDARY"
                if snapshot_date is not None and snapshot_date < date(2026, 8, 7)
                else "FORMAL_PUBLISHED_ONLY"
            ),
        },
    }


__all__ = ["router"]
