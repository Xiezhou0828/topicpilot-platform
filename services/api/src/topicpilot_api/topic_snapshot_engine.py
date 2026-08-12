"""Daily V2 topic snapshot aggregation and persistence."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from topicpilot_api.orm import (
    InstrumentTopicRelation,
    LiveTrackingUniverse,
    Topic,
    TopicHierarchy,
    TopicSnapshot,
)
from topicpilot_api.topic_engine.production_policy import (
    STRONG_NEGATIVE,
    STRONG_POSITIVE,
    classify_participation,
)

SNAPSHOT_CALCULATION_VERSION = "topic-snapshot.v1"
SCORE_STATUS_DEFERRED = "DEFERRED"


@dataclass(frozen=True)
class MemberPriceEvidence:
    instrument_id: UUID
    current_date: date | None
    current_close: Decimal | None
    previous_close: Decimal | None

    @property
    def change_pct(self) -> Decimal | None:
        if self.current_close is None or self.previous_close is None:
            return None
        if self.previous_close <= 0:
            return None
        return (self.current_close - self.previous_close) / self.previous_close * Decimal("100")


@dataclass(frozen=True)
class TopicAggregation:
    stock_count: int
    observed_stock_count: int
    strong_stock_count: int
    weak_stock_count: int
    average_change: Decimal | None
    coverage_pct: Decimal | None
    direction: str
    data_status: str
    latest_observed_date: date | None


def aggregate_topic_members(
    member_ids: set[UUID],
    evidence: dict[UUID, MemberPriceEvidence],
    snapshot_date: date,
    *,
    market_closed: bool = False,
) -> TopicAggregation:
    """Aggregate one topic without turning missing observations into zero."""

    stock_count = len(member_ids)
    if market_closed:
        return TopicAggregation(
            stock_count,
            0,
            0,
            0,
            None,
            Decimal("0") if stock_count else None,
            "UNKNOWN",
            "MARKET_CLOSED",
            None,
        )

    changes: list[Decimal] = []
    observed_count = 0
    strong_count = 0
    weak_count = 0
    observed_dates: list[date] = []
    for instrument_id in member_ids:
        item = evidence.get(instrument_id)
        if item is None or item.current_date is None or item.current_close is None:
            continue
        if item.current_date is not None:
            observed_count += 1
            observed_dates.append(item.current_date)
        change = item.change_pct
        if change is None:
            continue
        changes.append(change)
        state = classify_participation(float(change))
        if state == STRONG_POSITIVE:
            strong_count += 1
        elif state == STRONG_NEGATIVE:
            weak_count += 1

    average = sum(changes, Decimal("0")) / Decimal(len(changes)) if changes else None
    if average is None:
        direction = "UNKNOWN"
    elif average > 0:
        direction = "WARMING"
    elif average < 0:
        direction = "COOLING"
    else:
        direction = "FLAT"

    coverage = Decimal(observed_count * 100) / Decimal(stock_count) if stock_count else None
    if stock_count == 0:
        data_status = "NO_MEMBERS"
    latest_observed_date = max(observed_dates) if observed_dates else None
    if observed_count == stock_count and latest_observed_date == snapshot_date:
        data_status = "COMPLETE"
    elif observed_count and latest_observed_date and latest_observed_date < snapshot_date:
        data_status = "STALE_AS_OF"
    elif observed_count:
        data_status = "PARTIAL"
    else:
        data_status = "NO_CURRENT_DATA"
    return TopicAggregation(
        stock_count,
        observed_count,
        strong_count,
        weak_count,
        average,
        coverage,
        direction,
        data_status,
        latest_observed_date,
    )


class TopicSnapshotEngine:
    """Build one immutable-as-of-date row per active V2 topic.

    The engine writes only the new V2 ``topicpilot.topic_snapshots`` table.
    Scores and grades remain nullable until the approved V2 scorer/as-of gate
    is activated; the engine records that fact as ``score_status`` instead of
    substituting a zero.
    """

    def __init__(
        self, session: Session, *, calculation_version: str = SNAPSHOT_CALCULATION_VERSION
    ):
        self.session = session
        self.calculation_version = calculation_version

    def run_once(
        self,
        *,
        snapshot_date: date,
        market_closed: bool = False,
    ) -> dict[str, Any]:
        topics = list(
            self.session.scalars(
                select(Topic)
                .where(Topic.status.not_in(("DISABLED", "RETIRED")))
                .order_by(Topic.slug)
            )
        )
        if not topics:
            return {
                "snapshotDate": snapshot_date.isoformat(),
                "topicCount": 0,
                "status": "NO_TOPIC_MASTER",
                "calculationVersion": self.calculation_version,
            }

        tracking_ids = set(self.session.scalars(select(LiveTrackingUniverse.instrument_id)).all())
        relation_rows = list(
            self.session.execute(
                select(
                    InstrumentTopicRelation.topic_id, InstrumentTopicRelation.instrument_id
                ).where(
                    InstrumentTopicRelation.valid_from <= snapshot_date,
                    (InstrumentTopicRelation.valid_to.is_(None))
                    | (InstrumentTopicRelation.valid_to >= snapshot_date),
                    InstrumentTopicRelation.instrument_id.in_(tracking_ids)
                    if tracking_ids
                    else text("false"),
                )
            ).all()
        )
        members: dict[UUID, set[UUID]] = defaultdict(set)
        for topic_id, instrument_id in relation_rows:
            members[topic_id].add(instrument_id)

        parent_rows = list(
            self.session.execute(
                select(TopicHierarchy.child_topic_id, Topic.name)
                .join(Topic, Topic.id == TopicHierarchy.parent_topic_id)
                .where(
                    TopicHierarchy.valid_from <= snapshot_date,
                    (TopicHierarchy.valid_to.is_(None))
                    | (TopicHierarchy.valid_to >= snapshot_date),
                )
                .order_by(TopicHierarchy.child_topic_id, TopicHierarchy.display_order, Topic.slug)
            ).all()
        )
        parents: dict[UUID, str] = {}
        for child_id, parent_name in parent_rows:
            parents.setdefault(child_id, parent_name)

        evidence = {} if market_closed else self._read_price_evidence(snapshot_date)
        rows: list[TopicSnapshot] = []
        status_counts: dict[str, int] = defaultdict(int)
        for topic in topics:
            aggregate = aggregate_topic_members(
                members.get(topic.id, set()),
                evidence,
                snapshot_date,
                market_closed=market_closed,
            )
            values = {
                "snapshot_date": snapshot_date,
                "topic_id": topic.id,
                "topic_slug": topic.slug,
                "topic_name": topic.name,
                "parent_topic": parents.get(topic.id),
                "market_grade": None,
                "topic_score": None,
                "topic_direction": aggregate.direction,
                "stock_count": aggregate.stock_count,
                "strong_stock_count": aggregate.strong_stock_count,
                "weak_stock_count": aggregate.weak_stock_count,
                "average_change": self._quantize(aggregate.average_change),
                "observed_stock_count": aggregate.observed_stock_count,
                "coverage_pct": self._quantize(aggregate.coverage_pct, places=3),
                "data_status": aggregate.data_status,
                "score_status": SCORE_STATUS_DEFERRED,
                "calculation_version": self.calculation_version,
                "metadata_payload": {
                    "source": "topicpilot.canonical_observations",
                    "sourceFamily": "PRICE",
                    "sourceSemantics": "DAILY_BAR",
                    "trackingUniverse": "topicpilot.live_tracking_universe",
                    "marketClosed": market_closed,
                    "observedAsOfDate": (
                        aggregate.latest_observed_date.isoformat()
                        if aggregate.latest_observed_date
                        else None
                    ),
                    "scoreStatus": SCORE_STATUS_DEFERRED,
                    "strongStockDefinition": "STRONG_POSITIVE",
                    "weakStockDefinition": "STRONG_NEGATIVE",
                    "directionDefinition": "average accepted daily close-to-close change",
                },
            }
            existing = self.session.scalar(
                select(TopicSnapshot).where(
                    TopicSnapshot.topic_id == topic.id,
                    TopicSnapshot.snapshot_date == snapshot_date,
                )
            )
            if existing is None:
                existing = TopicSnapshot(**values)
                self.session.add(existing)
            else:
                for key, value in values.items():
                    setattr(existing, key, value)
            rows.append(existing)
            status_counts[aggregate.data_status] += 1

        self.session.commit()
        return {
            "snapshotDate": snapshot_date.isoformat(),
            "topicCount": len(rows),
            "status": "SUCCESS",
            "dataStatusCounts": dict(sorted(status_counts.items())),
            "scoreStatus": SCORE_STATUS_DEFERRED,
            "calculationVersion": self.calculation_version,
        }

    def _read_price_evidence(self, snapshot_date: date) -> dict[UUID, MemberPriceEvidence]:
        sql = text(
            """
            WITH candidates AS (
                SELECT
                    co.id,
                    co.instrument_id,
                    co.observed_at,
                    (co.observed_at AT TIME ZONE m.timezone)::date AS trading_date,
                    cp.close,
                    ROW_NUMBER() OVER (
                        PARTITION BY co.instrument_id,
                            (co.observed_at AT TIME ZONE m.timezone)::date
                        ORDER BY mds.source_rank, co.retrieved_at DESC, co.id DESC
                    ) AS source_rank_row
                FROM topicpilot.canonical_observations co
                JOIN topicpilot.canonical_price_observations cp
                  ON cp.canonical_observation_id = co.id
                JOIN topicpilot.instruments i ON i.id = co.instrument_id
                JOIN topicpilot.markets m ON m.id = i.market_id
                JOIN topicpilot.market_data_sources mds ON mds.id = co.source_id
                WHERE co.family_code = 'PRICE'
                  AND co.quality_state = 'ACCEPTED'
                  AND mds.observation_semantics = 'DAILY_BAR'
                  AND (co.observed_at AT TIME ZONE m.timezone)::date <= :snapshot_date
                  AND cp.close IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1
                      FROM topicpilot.canonical_observations successor
                      WHERE successor.supersedes_id = co.id
                        AND successor.family_code = 'PRICE'
                        AND successor.quality_state = 'ACCEPTED'
                  )
            ), daily AS (
                SELECT *
                FROM candidates
                WHERE source_rank_row = 1
            ), ranked AS (
                SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY instrument_id
                    ORDER BY trading_date DESC, observed_at DESC, id DESC
                ) AS date_rank
                FROM daily
            )
            SELECT instrument_id, trading_date, close, date_rank
            FROM ranked
            WHERE date_rank <= 2
            ORDER BY instrument_id, date_rank
            """
        )
        rows = self.session.execute(sql, {"snapshot_date": snapshot_date}).mappings().all()
        by_instrument: dict[UUID, dict[int, Any]] = defaultdict(dict)
        for row in rows:
            by_instrument[row["instrument_id"]][int(row["date_rank"])] = row
        return {
            instrument_id: MemberPriceEvidence(
                instrument_id,
                values.get(1, {}).get("trading_date"),
                values.get(1, {}).get("close"),
                values.get(2, {}).get("close"),
            )
            for instrument_id, values in by_instrument.items()
        }

    @staticmethod
    def _quantize(value: Decimal | None, *, places: int = 4) -> Decimal | None:
        if value is None:
            return None
        quantum = Decimal("1").scaleb(-places)
        return value.quantize(quantum, rounding=ROUND_HALF_UP)


__all__ = [
    "SNAPSHOT_CALCULATION_VERSION",
    "MemberPriceEvidence",
    "TopicAggregation",
    "TopicSnapshotEngine",
    "aggregate_topic_members",
]
