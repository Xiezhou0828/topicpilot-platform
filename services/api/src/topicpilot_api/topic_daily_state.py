"""Formal PIT Topic Daily State resolver and bounded materializer.

The existing TopicSnapshotEngine remains available to legacy/research callers.
This module is the formal authority path: it resolves effective membership,
selects accepted canonical observations, writes immutable snapshot revisions,
and keeps research/shadow modes out of formal readers.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import bindparam, func, or_, select, text
from sqlalchemy.orm import Session

from topicpilot_api.orm import (
    Instrument,
    InstrumentTopicRelation,
    Market,
    ReferenceCalendarDate,
    ReferenceInstrumentLifecycle,
    ReferenceRegistrySet,
    ReferenceSession,
    SecurityIdentity,
    Topic,
    TopicSnapshot,
    TopicSnapshotMemberFact,
)

FORMAL_MAPPING_EARLIEST_DATE = date(2026, 8, 7)
FORMAL_PUBLICATION_MODE = "FORMAL"
FORMAL_MEMBERSHIP_MODE = "PIT_FORMAL"
RESEARCH_PUBLICATION_MODE = "RESEARCH_ONLY"
SHADOW_PUBLICATION_MODE = "SHADOW"
MAPPING_POLICY_VERSION = "topic-membership-pit.v1"
CALCULATION_VERSION = "topic-daily-state.v1"
NO_TRADE_STATUS_CODES = frozenset({"NO_TRADE", "EXCHANGE_CONFIRMED_NO_DATA"})


class FormalAuthorityUnavailable(ValueError):
    """Raised when a date cannot be safely represented as a formal state."""


@dataclass(frozen=True)
class MembershipMember:
    instrument_id: UUID
    instrument_code: str
    market_code: str
    relation_type: str
    relation_version: str
    identity_continuity: str


@dataclass(frozen=True)
class MembershipSnapshot:
    topic_id: UUID
    trading_date: date
    relation_version: str
    mapping_effective_from: date
    membership_snapshot_id: str
    membership_snapshot_hash: str
    reference_registry_version: str
    session_code: str
    calendar_code: str
    trading_day_state: str
    expected_count: int
    eligible_count: int
    excluded_count: int
    excluded_reasons: tuple[tuple[str, str], ...]
    members: tuple[MembershipMember, ...]


@dataclass(frozen=True)
class SelectedMemberFact:
    instrument_id: UUID
    trading_date: date
    fact_state: str
    price_observation_id: UUID | None
    volume_observation_id: UUID | None
    trading_status_observation_id: UUID | None
    close: Decimal | None
    previous_close: Decimal | None
    change_pct: Decimal | None
    observed_classification: str | None
    observed_at: datetime | None
    retrieved_at: datetime | None
    raw_fact_payload: dict[str, Any]
    fact_identity: str
    fact_hash: str


@dataclass(frozen=True)
class TopicMaterializationPlan:
    trading_date: date
    topic_id: UUID
    topic_slug: str
    topic_name: str
    status: str
    reason: str | None
    membership: MembershipSnapshot | None
    facts: tuple[SelectedMemberFact, ...]


@dataclass(frozen=True)
class DateMaterializationPlan:
    trading_date: date
    status: str
    reason: str | None
    topics: tuple[TopicMaterializationPlan, ...]


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(
        _canonicalize(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _canonicalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return _json_value(value)


def _canonical_row_value(row: Any, key: str) -> Any:
    value = row[key]
    return _json_value(value)


def _effective_filter(column: Any, trading_date: date):
    return or_(column.is_(None), column <= trading_date)


def _end_filter(column: Any, trading_date: date):
    return or_(column.is_(None), column >= trading_date)


def _member_sort_key(item: MembershipMember):
    return item.market_code, item.instrument_code, str(item.instrument_id)


def _active_reference_binding(
    session: Session, trading_date: date
) -> tuple[ReferenceRegistrySet, dict[str, str], dict[str, str], str]:
    registries = list(
        session.scalars(
            select(ReferenceRegistrySet)
            .where(ReferenceRegistrySet.status == "ACTIVE")
            .order_by(ReferenceRegistrySet.reference_data_version)
        )
    )
    if len(registries) != 1:
        raise FormalAuthorityUnavailable(
            f"expected exactly one ACTIVE reference registry, found {len(registries)}"
        )
    registry = registries[0]
    sessions = list(
        session.scalars(
            select(ReferenceSession)
            .where(ReferenceSession.registry_set_id == registry.id)
            .order_by(ReferenceSession.calendar_code, ReferenceSession.code)
        )
    )
    session_by_calendar: dict[str, list[str]] = defaultdict(list)
    for item in sessions:
        session_by_calendar[item.calendar_code].append(item.code)
    dates = list(
        session.scalars(
            select(ReferenceCalendarDate).where(
                ReferenceCalendarDate.registry_set_id == registry.id,
                ReferenceCalendarDate.calendar_date == trading_date,
            )
        )
    )
    non_trading_calendars = {item.calendar_code for item in dates}
    return (
        registry,
        {calendar: "+".join(sorted(codes)) for calendar, codes in session_by_calendar.items()},
        {
            calendar: ("NON_TRADING" if calendar in non_trading_calendars else "TRADING")
            for calendar in session_by_calendar
        },
        registry.reference_data_version,
    )


def resolve_formal_membership(
    session: Session,
    topic_id: UUID,
    trading_date: date,
    *,
    mapping_effective_from: date = FORMAL_MAPPING_EARLIEST_DATE,
) -> MembershipSnapshot:
    """Resolve one deterministic point-in-time member set.

    The resolver never falls back to current mapping.  It uses immutable
    instrument IDs as the bounded identity even when no date-valid symbol
    identity exists, and excludes date-effective lifecycle failures.
    """

    if trading_date < FORMAL_MAPPING_EARLIEST_DATE:
        raise FormalAuthorityUnavailable("pre-boundary date is UNKNOWN / NOT_AUTHORIZED_AS_PIT")
    if mapping_effective_from != FORMAL_MAPPING_EARLIEST_DATE:
        raise FormalAuthorityUnavailable("formal mapping boundary is fixed at 2026-08-07")

    registry, sessions_by_calendar, day_state_by_calendar, reference_version = (
        _active_reference_binding(session, trading_date)
    )
    candidates = list(
        session.execute(
            select(
                InstrumentTopicRelation.instrument_id,
                InstrumentTopicRelation.topic_id,
                InstrumentTopicRelation.relation_type,
                InstrumentTopicRelation.relation_version,
                InstrumentTopicRelation.valid_from,
                Instrument.instrument_code,
                Instrument.valid_from.label("instrument_valid_from"),
                Instrument.valid_to.label("instrument_valid_to"),
                Market.code.label("market_code"),
                Market.calendar_code,
                Market.valid_from.label("market_valid_from"),
                Market.valid_to.label("market_valid_to"),
                Topic.valid_from.label("topic_valid_from"),
                Topic.valid_to.label("topic_valid_to"),
            )
            .join(Instrument, Instrument.id == InstrumentTopicRelation.instrument_id)
            .join(Market, Market.id == Instrument.market_id)
            .join(Topic, Topic.id == InstrumentTopicRelation.topic_id)
            .where(
                InstrumentTopicRelation.topic_id == topic_id,
                InstrumentTopicRelation.valid_from <= trading_date,
                _end_filter(InstrumentTopicRelation.valid_to, trading_date),
                _effective_filter(Instrument.valid_from, trading_date),
                _end_filter(Instrument.valid_to, trading_date),
                _effective_filter(Market.valid_from, trading_date),
                _end_filter(Market.valid_to, trading_date),
                _effective_filter(Topic.valid_from, trading_date),
                _end_filter(Topic.valid_to, trading_date),
                Topic.status.not_in(("DISABLED", "RETIRED")),
                Instrument.instrument_type == "EQUITY",
                Market.code.in_(("TPE", "TWO")),
            )
            .order_by(
                Market.code,
                Instrument.instrument_code,
                InstrumentTopicRelation.instrument_id,
                InstrumentTopicRelation.valid_from,
                InstrumentTopicRelation.relation_version,
            )
        )
    )
    if not candidates:
        raise FormalAuthorityUnavailable("topic has no date-valid effective relations")

    by_member: dict[tuple[UUID, UUID], list[Any]] = defaultdict(list)
    for row in candidates:
        by_member[(row.instrument_id, row.topic_id)].append(row)
    duplicate_keys = [key for key, rows in by_member.items() if len(rows) != 1]
    if duplicate_keys:
        rendered = ", ".join(f"{instrument}/{topic}" for instrument, topic in duplicate_keys)
        raise FormalAuthorityUnavailable(f"overlapping or duplicate relation authority: {rendered}")

    instrument_ids = tuple(sorted({row.instrument_id for row in candidates}, key=str))
    lifecycle_rows = list(
        session.execute(
            select(
                ReferenceInstrumentLifecycle.instrument_id,
                ReferenceInstrumentLifecycle.status_code,
                ReferenceInstrumentLifecycle.effective_from,
                ReferenceInstrumentLifecycle.effective_to,
                ReferenceInstrumentLifecycle.evidence_id,
            ).where(
                ReferenceInstrumentLifecycle.registry_set_id == registry.id,
                ReferenceInstrumentLifecycle.instrument_id.in_(instrument_ids),
                ReferenceInstrumentLifecycle.status_code.in_(
                    ("DELISTED", "TERMINATED", "SUSPENDED")
                ),
                ReferenceInstrumentLifecycle.effective_from <= trading_date,
                _end_filter(ReferenceInstrumentLifecycle.effective_to, trading_date),
            )
        )
    )
    lifecycle_by_instrument: dict[UUID, list[Any]] = defaultdict(list)
    for row in lifecycle_rows:
        lifecycle_by_instrument[row.instrument_id].append(row)

    identity_rows = session.execute(
        select(SecurityIdentity.instrument_id).where(
            SecurityIdentity.instrument_id.in_(instrument_ids),
            SecurityIdentity.valid_from <= trading_date,
            _end_filter(SecurityIdentity.valid_to, trading_date),
        )
    ).all()
    identity_instruments = {row.instrument_id for row in identity_rows}

    excluded: list[tuple[str, str]] = []
    members: list[MembershipMember] = []
    calendars: set[str] = set()
    sessions: set[str] = set()
    relation_versions: set[str] = set()
    for row in candidates:
        lifecycle = lifecycle_by_instrument.get(row.instrument_id, [])
        if lifecycle:
            reason = ";".join(
                sorted(f"{item.status_code}:{item.evidence_id}" for item in lifecycle)
            )
            excluded.append((str(row.instrument_id), reason))
            continue
        if not row.calendar_code or row.calendar_code not in sessions_by_calendar:
            raise FormalAuthorityUnavailable(
                f"missing active session/calendar binding for market {row.market_code}"
            )
        calendars.add(row.calendar_code)
        sessions.add(sessions_by_calendar[row.calendar_code])
        relation_versions.add(row.relation_version)
        members.append(
            MembershipMember(
                instrument_id=row.instrument_id,
                instrument_code=row.instrument_code,
                market_code=row.market_code,
                relation_type=row.relation_type,
                relation_version=row.relation_version,
                identity_continuity=(
                    "DATE_VALID_SECURITY_IDENTITY"
                    if row.instrument_id in identity_instruments
                    else "BOUNDED_IMMUTABLE_INSTRUMENT_ID_ONLY"
                ),
            )
        )

    if not members:
        raise FormalAuthorityUnavailable("all date-valid relation members are lifecycle-ineligible")
    member_order = tuple(sorted(members, key=_member_sort_key))
    calendar_states = {day_state_by_calendar[calendar] for calendar in calendars}
    trading_day_state = next(iter(calendar_states)) if len(calendar_states) == 1 else "MIXED"
    relation_version = "+".join(sorted(relation_versions))
    excluded_reasons = tuple(sorted(excluded))
    membership_payload = {
        "topicId": str(topic_id),
        "tradingDate": trading_date.isoformat(),
        "mappingEffectiveFrom": mapping_effective_from.isoformat(),
        "relationVersion": relation_version,
        "referenceRegistryVersion": reference_version,
        "sessionCode": "+".join(sorted(sessions)),
        "calendarCode": "+".join(sorted(calendars)),
        "members": [
            {
                "instrumentId": str(member.instrument_id),
                "instrumentCode": member.instrument_code,
                "marketCode": member.market_code,
                "relationType": member.relation_type,
                "relationVersion": member.relation_version,
                "identityContinuity": member.identity_continuity,
            }
            for member in member_order
        ],
        "excluded": list(excluded_reasons),
    }
    membership_hash = _hash_payload(membership_payload)
    return MembershipSnapshot(
        topic_id=topic_id,
        trading_date=trading_date,
        relation_version=relation_version,
        mapping_effective_from=mapping_effective_from,
        membership_snapshot_id=f"membership:{membership_hash}",
        membership_snapshot_hash=membership_hash,
        reference_registry_version=reference_version,
        session_code="+".join(sorted(sessions)),
        calendar_code="+".join(sorted(calendars)),
        trading_day_state=trading_day_state,
        expected_count=len(candidates),
        eligible_count=len(member_order),
        excluded_count=len(excluded_reasons),
        excluded_reasons=excluded_reasons,
        members=member_order,
    )


_PRICE_FACTS_SQL = text(
    """
    WITH candidates AS (
        SELECT co.id, co.instrument_id, co.observed_at, co.retrieved_at,
               co.content_hash, cp.close,
               (co.observed_at AT TIME ZONE m.timezone)::date AS trading_date,
               ROW_NUMBER() OVER (
                   PARTITION BY co.instrument_id,
                       (co.observed_at AT TIME ZONE m.timezone)::date
                   ORDER BY source.source_rank, co.retrieved_at DESC,
                            co.observed_at DESC, co.id DESC
               ) AS same_day_rank
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_price_observations cp
          ON cp.canonical_observation_id = co.id
        JOIN topicpilot.instruments i ON i.id = co.instrument_id
        JOIN topicpilot.markets m ON m.id = i.market_id
        JOIN topicpilot.market_data_sources source ON source.id = co.source_id
        WHERE co.instrument_id IN :instrument_ids
          AND co.family_code = 'PRICE'
          AND co.quality_state = 'ACCEPTED'
          AND source.observation_semantics = 'DAILY_BAR'
          AND cp.close IS NOT NULL
          AND (co.observed_at AT TIME ZONE m.timezone)::date <= :trading_date
          AND NOT EXISTS (
              SELECT 1 FROM topicpilot.canonical_observations successor
              WHERE successor.supersedes_id = co.id
                AND successor.family_code = 'PRICE'
                AND successor.quality_state = 'ACCEPTED'
          )
    ), daily AS (
        SELECT * FROM candidates WHERE same_day_rank = 1
    ), ranked AS (
        SELECT daily.*, ROW_NUMBER() OVER (
            PARTITION BY instrument_id
            ORDER BY trading_date DESC, observed_at DESC, retrieved_at DESC, id DESC
        ) AS date_rank
        FROM daily
    )
    SELECT * FROM ranked WHERE date_rank <= 2
    ORDER BY instrument_id, date_rank
    """
).bindparams(bindparam("instrument_ids", expanding=True))

_VOLUME_FACTS_SQL = text(
    """
    SELECT co.id, co.instrument_id, co.observed_at, co.retrieved_at, co.content_hash,
           cv.volume_quantity, cv.turnover_amount
    FROM topicpilot.canonical_observations co
    JOIN topicpilot.canonical_volume_observations cv
      ON cv.canonical_observation_id = co.id
    JOIN topicpilot.instruments i ON i.id = co.instrument_id
    JOIN topicpilot.markets m ON m.id = i.market_id
    JOIN topicpilot.market_data_sources source ON source.id = co.source_id
    WHERE co.instrument_id IN :instrument_ids
      AND co.family_code = 'VOLUME'
      AND co.quality_state = 'ACCEPTED'
      AND source.observation_semantics = 'DAILY_BAR'
      AND cv.aggregation_code = 'DAILY_TOTAL'
      AND (co.observed_at AT TIME ZONE m.timezone)::date = :trading_date
      AND NOT EXISTS (
          SELECT 1 FROM topicpilot.canonical_observations successor
          WHERE successor.supersedes_id = co.id
            AND successor.family_code = 'VOLUME'
            AND successor.quality_state = 'ACCEPTED'
      )
    ORDER BY source.source_rank, co.retrieved_at DESC, co.observed_at DESC, co.id DESC
    """
).bindparams(bindparam("instrument_ids", expanding=True))

_STATUS_FACTS_SQL = text(
    """
    SELECT co.id, co.instrument_id, co.observed_at, co.retrieved_at, co.content_hash,
           status.status_code, status.status_reason
    FROM topicpilot.canonical_observations co
    JOIN topicpilot.canonical_trading_status_observations status
      ON status.canonical_observation_id = co.id
    JOIN topicpilot.instruments i ON i.id = co.instrument_id
    JOIN topicpilot.markets m ON m.id = i.market_id
    JOIN topicpilot.market_data_sources source ON source.id = co.source_id
    WHERE co.instrument_id IN :instrument_ids
      AND co.family_code = 'TRADING_STATUS'
      AND co.quality_state = 'ACCEPTED'
      AND source.observation_semantics = 'DAILY_BAR'
      AND (co.observed_at AT TIME ZONE m.timezone)::date = :trading_date
      AND NOT EXISTS (
          SELECT 1 FROM topicpilot.canonical_observations successor
          WHERE successor.supersedes_id = co.id
            AND successor.family_code = 'TRADING_STATUS'
            AND successor.quality_state = 'ACCEPTED'
      )
    ORDER BY source.source_rank, co.retrieved_at DESC, co.observed_at DESC, co.id DESC
    """
).bindparams(bindparam("instrument_ids", expanding=True))


def read_canonical_member_facts(
    session: Session, trading_date: date, members: Sequence[MembershipMember]
) -> tuple[SelectedMemberFact, ...]:
    """Select exact-date accepted facts; absence is never converted to zero."""

    if not members:
        return ()
    instrument_ids = [member.instrument_id for member in members]
    params = {"instrument_ids": instrument_ids, "trading_date": trading_date}
    price_rows = session.execute(_PRICE_FACTS_SQL, params).mappings().all()
    price_by_instrument: dict[UUID, dict[int, Any]] = defaultdict(dict)
    for row in price_rows:
        price_by_instrument[row["instrument_id"]][int(row["date_rank"])] = row
    volume_by_instrument: dict[UUID, Any] = {}
    for row in session.execute(_VOLUME_FACTS_SQL, params).mappings():
        volume_by_instrument.setdefault(row["instrument_id"], row)
    status_by_instrument: dict[UUID, Any] = {}
    for row in session.execute(_STATUS_FACTS_SQL, params).mappings():
        status_by_instrument.setdefault(row["instrument_id"], row)

    facts: list[SelectedMemberFact] = []
    for member in sorted(members, key=_member_sort_key):
        price = price_by_instrument.get(member.instrument_id, {}).get(1)
        previous = price_by_instrument.get(member.instrument_id, {}).get(2)
        volume = volume_by_instrument.get(member.instrument_id)
        status = status_by_instrument.get(member.instrument_id)
        close = price["close"] if price is not None else None
        previous_close = previous["close"] if previous is not None else None
        change_pct = None
        if close is not None and previous_close is not None and previous_close > 0:
            change_pct = (close - previous_close) / previous_close * Decimal("100")
        if change_pct is None:
            classification = None
        elif change_pct > 0:
            classification = "POSITIVE"
        elif change_pct < 0:
            classification = "NEGATIVE"
        else:
            classification = "FLAT"
        status_code = status["status_code"] if status is not None else None
        fact_state = (
            "OBSERVED"
            if close is not None
            else "NO_TRADE"
            if status_code in NO_TRADE_STATUS_CODES
            else "UNKNOWN"
        )
        observed_at = (
            price["observed_at"]
            if price is not None
            else status["observed_at"]
            if status
            else None
        )
        retrieved_at = (
            price["retrieved_at"]
            if price is not None
            else status["retrieved_at"]
            if status
            else None
        )
        raw = {
            "instrumentId": str(member.instrument_id),
            "tradingDate": trading_date.isoformat(),
            "factState": fact_state,
            "priceObservationId": str(price["id"]) if price is not None else None,
            "volumeObservationId": str(volume["id"]) if volume is not None else None,
            "tradingStatusObservationId": str(status["id"]) if status is not None else None,
            "close": _json_value(close),
            "previousClose": _json_value(previous_close),
            "changePct": _json_value(change_pct),
            "observedClassification": classification,
            "tradingStatus": status_code,
            "tradingStatusReason": status["status_reason"] if status is not None else None,
            "priceContentHash": price["content_hash"] if price is not None else None,
            "volumeContentHash": volume["content_hash"] if volume is not None else None,
            "statusContentHash": status["content_hash"] if status is not None else None,
            "identityAuthority": member.identity_continuity,
        }
        fact_hash = _hash_payload(raw)
        facts.append(
            SelectedMemberFact(
                instrument_id=member.instrument_id,
                trading_date=trading_date,
                fact_state=fact_state,
                price_observation_id=price["id"] if price is not None else None,
                volume_observation_id=volume["id"] if volume is not None else None,
                trading_status_observation_id=status["id"] if status is not None else None,
                close=close,
                previous_close=previous_close,
                change_pct=change_pct,
                observed_classification=classification,
                observed_at=observed_at,
                retrieved_at=retrieved_at,
                raw_fact_payload=raw,
                fact_identity=f"fact:{fact_hash}",
                fact_hash=fact_hash,
            )
        )
    return tuple(facts)


def enumerate_formal_dates(
    session: Session,
    *,
    from_date: date = FORMAL_MAPPING_EARLIEST_DATE,
    to_date: date | None = None,
) -> tuple[date, ...]:
    """Enumerate only bounded dates with accepted canonical PRICE evidence."""

    if from_date < FORMAL_MAPPING_EARLIEST_DATE:
        raise FormalAuthorityUnavailable("date enumeration cannot cross the formal boundary")
    to_date = to_date or date.today()
    if to_date < from_date:
        return ()
    rows = session.execute(
        text(
            """
            SELECT DISTINCT (co.observed_at AT TIME ZONE m.timezone)::date AS trading_date
            FROM topicpilot.canonical_observations co
            JOIN topicpilot.canonical_price_observations cp
              ON cp.canonical_observation_id = co.id
            JOIN topicpilot.instruments i ON i.id = co.instrument_id
            JOIN topicpilot.markets m ON m.id = i.market_id
            JOIN topicpilot.market_data_sources source ON source.id = co.source_id
            WHERE co.family_code = 'PRICE'
              AND co.quality_state = 'ACCEPTED'
              AND source.observation_semantics = 'DAILY_BAR'
              AND cp.close IS NOT NULL
              AND (co.observed_at AT TIME ZONE m.timezone)::date >= :from_date
              AND (co.observed_at AT TIME ZONE m.timezone)::date <= :to_date
            ORDER BY trading_date
            """
        ),
        {"from_date": from_date, "to_date": to_date},
    ).scalars()
    return tuple(row for row in rows if row >= FORMAL_MAPPING_EARLIEST_DATE)


def plan_formal_materialization(
    session: Session, dates: Iterable[date]
) -> tuple[DateMaterializationPlan, ...]:
    """Dry-run the bounded authority gates without writing database rows."""

    topics = list(
        session.scalars(
            select(Topic).where(Topic.status.not_in(("DISABLED", "RETIRED"))).order_by(Topic.slug)
        )
    )
    plans: list[DateMaterializationPlan] = []
    for trading_date in sorted(set(dates)):
        if trading_date < FORMAL_MAPPING_EARLIEST_DATE:
            plans.append(
                DateMaterializationPlan(
                    trading_date, "UNAVAILABLE", "PRE_BOUNDARY_NOT_AUTHORIZED", ()
                )
            )
            continue
        topic_plans: list[TopicMaterializationPlan] = []
        for topic in topics:
            try:
                membership = resolve_formal_membership(session, topic.id, trading_date)
                facts = read_canonical_member_facts(session, trading_date, membership.members)
            except FormalAuthorityUnavailable as exc:
                topic_plans.append(
                    TopicMaterializationPlan(
                        trading_date,
                        topic.id,
                        topic.slug,
                        topic.name,
                        "UNAVAILABLE",
                        str(exc),
                        None,
                        (),
                    )
                )
                continue
            if not any(fact.fact_state in {"OBSERVED", "NO_TRADE"} for fact in facts):
                topic_plans.append(
                    TopicMaterializationPlan(
                        trading_date,
                        topic.id,
                        topic.slug,
                        topic.name,
                        "UNAVAILABLE",
                        "NO_ACCEPTED_MEMBER_OBSERVATION_EVIDENCE",
                        membership,
                        facts,
                    )
                )
                continue
            topic_plans.append(
                TopicMaterializationPlan(
                    trading_date, topic.id, topic.slug, topic.name, "READY", None, membership, facts
                )
            )
        ready = any(item.status == "READY" for item in topic_plans)
        plans.append(
            DateMaterializationPlan(
                trading_date,
                "READY" if ready else "UNAVAILABLE",
                None if ready else "NO_TOPIC_WITH_ACCEPTED_MEMBER_EVIDENCE",
                tuple(topic_plans),
            )
        )
    return tuple(plans)


def _topic_artifact_hash(
    membership: MembershipSnapshot, facts: Sequence[SelectedMemberFact]
) -> str:
    return _hash_payload(
        {
            "membershipHash": membership.membership_snapshot_hash,
            "facts": [fact.fact_hash for fact in facts],
            "calculationVersion": CALCULATION_VERSION,
            "mappingPolicyVersion": MAPPING_POLICY_VERSION,
        }
    )


def _snapshot_values(
    plan: TopicMaterializationPlan,
    *,
    now: datetime,
    correction_sequence: int,
    supersedes_snapshot_id: UUID | None,
) -> dict[str, Any]:
    assert plan.membership is not None
    membership = plan.membership
    facts = plan.facts
    observed = [fact for fact in facts if fact.fact_state == "OBSERVED"]
    no_trade = [fact for fact in facts if fact.fact_state == "NO_TRADE"]
    unknown = [fact for fact in facts if fact.fact_state == "UNKNOWN"]
    changes = [fact.change_pct for fact in observed if fact.change_pct is not None]
    average_change = sum(changes, Decimal("0")) / Decimal(len(changes)) if changes else None
    direction = (
        "WARMING"
        if average_change is not None and average_change > 0
        else "COOLING"
        if average_change is not None and average_change < 0
        else "FLAT"
        if average_change is not None
        else "UNKNOWN"
    )
    artifact_hash = _topic_artifact_hash(membership, facts)
    source_artifact_id = f"topic-daily-state-artifact:{artifact_hash}"
    lineage = {
        "referenceRegistryVersion": membership.reference_registry_version,
        "calculationVersion": CALCULATION_VERSION,
        "mappingPolicyVersion": MAPPING_POLICY_VERSION,
        "sourceRunId": f"topic-daily-state:{plan.trading_date.isoformat()}",
        "sourceArtifactId": source_artifact_id,
        "sourceArtifactHash": artifact_hash,
        "membershipSnapshotId": membership.membership_snapshot_id,
        "membershipSnapshotHash": membership.membership_snapshot_hash,
    }
    lineage_hash = _hash_payload(lineage)
    snapshot_identity = f"formal:{plan.topic_id}:{plan.trading_date.isoformat()}:{artifact_hash}"
    return {
        "snapshot_date": plan.trading_date,
        "topic_id": plan.topic_id,
        "topic_slug": plan.topic_slug,
        "topic_name": plan.topic_name,
        "parent_topic": None,
        "market_grade": None,
        "topic_score": None,
        "topic_direction": direction,
        "stock_count": membership.eligible_count,
        "strong_stock_count": None,
        "weak_stock_count": None,
        "average_change": average_change,
        "observed_stock_count": len(observed),
        "coverage_pct": (
            Decimal(len(observed) * 100) / Decimal(membership.eligible_count)
            if membership.eligible_count
            else None
        ),
        "data_status": "COMPLETE" if not unknown else "PARTIAL",
        "score_status": "DEFERRED",
        "calculation_version": CALCULATION_VERSION,
        "metadata_payload": {"authority": "FORMAL_PIT_TOPIC_DAILY_STATE"},
        "publication_mode": FORMAL_PUBLICATION_MODE,
        "membership_mode": FORMAL_MEMBERSHIP_MODE,
        "relation_version": membership.relation_version,
        "mapping_effective_from": membership.mapping_effective_from,
        "membership_snapshot_id": membership.membership_snapshot_id,
        "membership_snapshot_hash": membership.membership_snapshot_hash,
        "session_code": membership.session_code,
        "calendar_code": membership.calendar_code,
        "trading_day_state": membership.trading_day_state,
        "generated_state": "GENERATED",
        "finality_state": "FINAL",
        "publication_state": "PUBLISHED",
        "generated_at": now,
        "as_of_at": max((fact.retrieved_at for fact in facts if fact.retrieved_at), default=now),
        "finalized_at": now,
        "published_at": now,
        "expected_count": membership.expected_count,
        "eligible_count": membership.eligible_count,
        "no_trade_count": len(no_trade),
        "unknown_count": len(unknown),
        "excluded_count": membership.excluded_count,
        "positive_count": sum(fact.observed_classification == "POSITIVE" for fact in observed),
        "flat_count": sum(fact.observed_classification == "FLAT" for fact in observed),
        "negative_count": sum(fact.observed_classification == "NEGATIVE" for fact in observed),
        "freshness_state": "AS_OF_TRADING_DATE",
        "unavailable_reason": None,
        "quality_flags": {
            "scoreGrade": "DEFERRED",
            "participation": "RAW_COUNTS_AND_COVERAGE_ONLY",
            "breadth": "DEFERRED",
            "leadership": "UNAVAILABLE",
            "concentration": "DEFERRED",
            "ranking": "DEFERRED",
            "lifecycle": "SHADOW_ONLY_UNPUBLISHED",
            "unknownSemantics": "ABSENCE_IS_UNKNOWN",
            "noTradeSemantics": "EXPLICIT_ACCEPTED_TRADING_STATUS_ONLY",
            "identityAuthority": "IMMUTABLE_INSTRUMENT_ID",
            "excludedMembers": dict(membership.excluded_reasons),
            "strongWeak": "DEFERRED_NO_APPROVED_CLASSIFIER",
        },
        "reference_registry_version": membership.reference_registry_version,
        "mapping_policy_version": MAPPING_POLICY_VERSION,
        "source_run_id": lineage["sourceRunId"],
        "source_artifact_id": source_artifact_id,
        "source_artifact_hash": artifact_hash,
        "lineage_hash": lineage_hash,
        "snapshot_identity": snapshot_identity,
        "correction_sequence": correction_sequence,
        "supersedes_snapshot_id": supersedes_snapshot_id,
        "supersession_reason": "CORRECTION" if supersedes_snapshot_id else None,
    }


def materialize_formal_plan(session: Session, plan: DateMaterializationPlan) -> dict[str, Any]:
    """Write only READY plan items with immutable correction semantics."""

    if plan.status != "READY":
        return {
            "tradingDate": plan.trading_date.isoformat(),
            "status": "UNAVAILABLE",
            "reason": plan.reason,
            "rowsWritten": 0,
            "idempotentRows": 0,
        }
    now = datetime.now(UTC)
    rows_written = 0
    idempotent_rows = 0
    for item in plan.topics:
        if item.status != "READY" or item.membership is None:
            continue
        artifact_hash = _topic_artifact_hash(item.membership, item.facts)
        identity = f"formal:{item.topic_id}:{item.trading_date.isoformat()}:{artifact_hash}"
        existing_identity = session.scalar(
            select(TopicSnapshot).where(TopicSnapshot.snapshot_identity == identity)
        )
        if existing_identity is not None:
            idempotent_rows += 1
            continue
        current_rows = list(
            session.scalars(
                select(TopicSnapshot)
                .where(
                    TopicSnapshot.topic_id == item.topic_id,
                    TopicSnapshot.snapshot_date == item.trading_date,
                    TopicSnapshot.publication_mode == FORMAL_PUBLICATION_MODE,
                    TopicSnapshot.publication_state == "PUBLISHED",
                    TopicSnapshot.superseded_by_snapshot_id.is_(None),
                )
                .order_by(TopicSnapshot.correction_sequence.desc(), TopicSnapshot.updated_at.desc())
            )
        )
        if len(current_rows) > 1:
            raise FormalAuthorityUnavailable(
                "multiple current formal snapshots require reconciliation"
            )
        previous = current_rows[0] if current_rows else None
        values = _snapshot_values(
            item,
            now=now,
            correction_sequence=(previous.correction_sequence + 1 if previous else 0),
            supersedes_snapshot_id=previous.id if previous else None,
        )
        row = TopicSnapshot(**values)
        session.add(row)
        session.flush()
        for order, (member, fact) in enumerate(
            zip(item.membership.members, item.facts, strict=True), start=1
        ):
            session.add(
                TopicSnapshotMemberFact(
                    snapshot_id=row.id,
                    instrument_id=member.instrument_id,
                    membership_order=order,
                    fact_identity=fact.fact_identity,
                    fact_hash=fact.fact_hash,
                    fact_state=fact.fact_state,
                    observation_date=fact.trading_date,
                    price_observation_id=fact.price_observation_id,
                    volume_observation_id=fact.volume_observation_id,
                    trading_status_observation_id=fact.trading_status_observation_id,
                    close=fact.close,
                    previous_close=fact.previous_close,
                    change_pct=fact.change_pct,
                    observed_classification=fact.observed_classification,
                    strength_classification=None,
                    classifier_version=None,
                    observed_at=fact.observed_at,
                    retrieved_at=fact.retrieved_at,
                    raw_fact_payload=fact.raw_fact_payload,
                    source_artifact_id=f"canonical-fact:{fact.fact_hash}",
                    source_artifact_hash=fact.fact_hash,
                )
            )
        if previous is not None:
            previous.publication_state = "SUPERSEDED"
            previous.superseded_by_snapshot_id = row.id
            previous.superseded_at = now
            previous.supersession_reason = "CORRECTION"
        rows_written += 1
    session.commit()
    return {
        "tradingDate": plan.trading_date.isoformat(),
        "status": "SUCCESS",
        "rowsWritten": rows_written,
        "idempotentRows": idempotent_rows,
        "memberFactRows": sum(len(item.facts) for item in plan.topics if item.status == "READY"),
    }


def materialize_bounded_formal_dates(
    session: Session,
    *,
    dates: Iterable[date] | None = None,
    from_date: date = FORMAL_MAPPING_EARLIEST_DATE,
    to_date: date | None = None,
) -> dict[str, Any]:
    """Enumerate, dry-run, then write only bounded formal dates."""

    materialization_dates = (
        tuple(dates)
        if dates is not None
        else enumerate_formal_dates(session, from_date=from_date, to_date=to_date)
    )
    plans = plan_formal_materialization(session, materialization_dates)
    before = int(
        session.scalar(
            select(func.count())
            .select_from(TopicSnapshot)
            .where(
                TopicSnapshot.publication_mode == FORMAL_PUBLICATION_MODE,
                TopicSnapshot.publication_state == "PUBLISHED",
                TopicSnapshot.superseded_by_snapshot_id.is_(None),
            )
        )
        or 0
    )
    writes = [materialize_formal_plan(session, plan) for plan in plans if plan.status == "READY"]
    after = int(
        session.scalar(
            select(func.count())
            .select_from(TopicSnapshot)
            .where(
                TopicSnapshot.publication_mode == FORMAL_PUBLICATION_MODE,
                TopicSnapshot.publication_state == "PUBLISHED",
                TopicSnapshot.superseded_by_snapshot_id.is_(None),
            )
        )
        or 0
    )
    return {
        "dates": [plan.trading_date.isoformat() for plan in plans],
        "plan": [
            {
                "tradingDate": plan.trading_date.isoformat(),
                "status": plan.status,
                "reason": plan.reason,
                "topics": [
                    {
                        "topicId": str(item.topic_id),
                        "topicSlug": item.topic_slug,
                        "status": item.status,
                        "reason": item.reason,
                        "memberFactCount": len(item.facts),
                    }
                    for item in plan.topics
                ],
            }
            for plan in plans
        ],
        "rowsBefore": before,
        "rowsAfter": after,
        "writes": writes,
        "preBoundaryBackfill": "NO",
    }


__all__ = [
    "CALCULATION_VERSION",
    "FORMAL_MAPPING_EARLIEST_DATE",
    "MAPPING_POLICY_VERSION",
    "DateMaterializationPlan",
    "FormalAuthorityUnavailable",
    "MembershipMember",
    "MembershipSnapshot",
    "SelectedMemberFact",
    "TopicMaterializationPlan",
    "enumerate_formal_dates",
    "materialize_bounded_formal_dates",
    "materialize_formal_plan",
    "plan_formal_materialization",
    "read_canonical_member_facts",
    "resolve_formal_membership",
]
