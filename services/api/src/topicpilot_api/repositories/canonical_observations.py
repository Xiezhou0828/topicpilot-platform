"""Canonical-observation read queries."""

from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased, selectinload

from topicpilot_api.orm.canonical_observations import (
    CanonicalObservation,
    CanonicalPriceObservation,
)


def read_current_canonical_observations(
    session: Session, instrument_id: UUID, from_: datetime, to: datetime
):
    outer = CanonicalObservation
    successor_row = aliased(CanonicalObservation)
    successor = (
        select(successor_row.id)
        .where(
            successor_row.supersedes_id == outer.id,
            successor_row.family_code == outer.family_code,
            successor_row.quality_state == "ACCEPTED",
        )
        .correlate(outer)
        .exists()
    )
    stmt = (
        select(outer)
        .where(
            outer.instrument_id == instrument_id,
            outer.observed_at >= from_,
            outer.observed_at < to,
            outer.quality_state == "ACCEPTED",
            ~successor,
        )
        .order_by(outer.instrument_id, outer.observed_at, outer.family_code, outer.id)
    )
    return list(session.scalars(stmt))


def read_approved_price_observations_for_as_of(
    session: Session,
    instrument_ids: tuple[UUID, ...],
    *,
    as_of: date,
    timezone_name: str,
    session_code: str,
    source_id: UUID,
) -> list[CanonicalObservation]:
    """Read accepted, current PRICE observations for an explicit session.

    There is intentionally no ``latest`` inference, stale fallback, V1
    fallback, or zero coercion. Callers must provide the approved source,
    session, timezone, and as-of date. An empty result remains empty evidence
    and must be handled by the caller's Eligibility Audit.
    """

    if not instrument_ids:
        raise ValueError("instrument_ids must be non-empty")
    if not session_code.strip():
        raise ValueError("session_code must be non-empty")
    if not timezone_name.strip():
        raise ValueError("timezone_name must be non-empty")
    try:
        timezone = ZoneInfo(timezone_name)
    except KeyError as exc:
        raise ValueError("timezone_name must be a valid IANA timezone") from exc
    start = datetime.combine(as_of, time.min, tzinfo=timezone)
    end = start + timedelta(days=1)

    outer = CanonicalObservation
    successor_row = aliased(CanonicalObservation)
    successor = (
        select(successor_row.id)
        .where(
            successor_row.supersedes_id == outer.id,
            successor_row.family_code == "PRICE",
            successor_row.quality_state == "ACCEPTED",
        )
        .correlate(outer)
        .exists()
    )
    stmt = (
        select(outer)
        .join(
            CanonicalPriceObservation,
            CanonicalPriceObservation.canonical_observation_id == outer.id,
        )
        .options(selectinload(outer.price))
        .where(
            outer.instrument_id.in_(instrument_ids),
            outer.source_id == source_id,
            outer.family_code == "PRICE",
            outer.quality_state == "ACCEPTED",
            outer.session_code == session_code,
            outer.observed_at >= start,
            outer.observed_at < end,
            ~successor,
        )
        .order_by(outer.instrument_id, outer.observed_at, outer.ordering_key, outer.id)
    )
    return list(session.scalars(stmt))


__all__ = [
    "read_approved_price_observations_for_as_of",
    "read_current_canonical_observations",
]
