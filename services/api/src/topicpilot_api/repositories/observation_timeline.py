"""Observation-timeline read queries."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from topicpilot_api.orm.observation_timeline import ObservationTimelineEntry


def replay_observation_timeline(
    session: Session,
    instrument_id: UUID,
    from_: datetime,
    to: datetime,
    *,
    include_non_active: bool = False,
):
    stmt = (
        select(ObservationTimelineEntry)
        .where(
            ObservationTimelineEntry.instrument_id == instrument_id,
            ObservationTimelineEntry.observed_at >= from_,
            ObservationTimelineEntry.observed_at < to,
        )
        .order_by(
            ObservationTimelineEntry.instrument_id,
            ObservationTimelineEntry.observed_at,
            ObservationTimelineEntry.ordering_key,
            ObservationTimelineEntry.id,
        )
    )
    if not include_non_active:
        stmt = stmt.where(ObservationTimelineEntry.entry_status == "ACTIVE")
    return list(session.scalars(stmt))
