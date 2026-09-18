"""Replayable persistence and read helpers for the FUND-A contract."""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from topicpilot_api.orm.institutional_flow import MarketInstitutionalFlowDaily

from .institutional_flow import (
    TPEX_INSTITUTIONAL_FLOW_SOURCE_IDENTITY,
    TWSE_INSTITUTIONAL_FLOW_SOURCE_IDENTITY,
    FlowAvailability,
    FlowFreshness,
    InstitutionalFlowLeg,
    MarketInstitutionalFlowFact,
    MarketInstitutionalFlowTrend,
    build_market_institutional_flow_trend,
)


def _lineage_hash(lineage: str) -> str:
    return hashlib.sha256(lineage.encode("utf-8")).hexdigest()


def _row_leg(
    row: MarketInstitutionalFlowDaily,
    prefix: str,
    *,
    status: FlowAvailability,
) -> InstitutionalFlowLeg | None:
    buy = getattr(row, f"{prefix}_buy")
    sell = getattr(row, f"{prefix}_sell")
    net = getattr(row, f"{prefix}_net")
    if buy is None or sell is None or net is None:
        return None
    return InstitutionalFlowLeg(
        buy=Decimal(str(buy)),
        sell=Decimal(str(sell)),
        net=Decimal(str(net)),
        unit=row.unit,
        scale=row.scale,
        status=status,
    )


def fact_to_model(
    fact: MarketInstitutionalFlowFact,
    *,
    ingested_at: datetime | None = None,
) -> dict[str, Any]:
    """Convert a typed fact to explicit database columns."""

    def value(leg: InstitutionalFlowLeg | None, field: str) -> Decimal | None:
        return getattr(leg, field) if leg is not None else None

    return {
        "market": fact.market,
        "trading_date": fact.trading_date,
        "source_provider": fact.source_provider,
        "source_identity": fact.source_identity,
        "source_dataset": fact.source_dataset,
        "source_endpoint": fact.source_endpoint,
        "adapter_version": fact.adapter_version,
        "source_as_of": fact.source_as_of,
        "published_at": fact.published_at,
        "retrieved_at": fact.retrieved_at,
        "ingested_at": ingested_at or fact.retrieved_at,
        "unit": "TWD",
        "scale": 0,
        "foreign_buy": value(fact.foreign, "buy"),
        "foreign_sell": value(fact.foreign, "sell"),
        "foreign_net": value(fact.foreign, "net"),
        "investment_trust_buy": value(fact.investment_trust, "buy"),
        "investment_trust_sell": value(fact.investment_trust, "sell"),
        "investment_trust_net": value(fact.investment_trust, "net"),
        "dealer_buy": value(fact.dealer, "buy"),
        "dealer_sell": value(fact.dealer, "sell"),
        "dealer_net": value(fact.dealer, "net"),
        "total_buy": value(fact.total, "buy"),
        "total_sell": value(fact.total, "sell"),
        "total_net": value(fact.total, "net"),
        "availability": fact.availability.value,
        "freshness": fact.freshness.value,
        "status_reason": fact.status_reason,
        "lineage": fact.lineage,
        "lineage_hash": _lineage_hash(fact.lineage),
        "response_content_hash": fact.response_content_hash,
        "raw_payload": fact.raw_payload,
    }


def model_to_fact(row: MarketInstitutionalFlowDaily) -> MarketInstitutionalFlowFact:
    availability = FlowAvailability(row.availability)
    status = availability
    return MarketInstitutionalFlowFact(
        market=row.market,
        trading_date=row.trading_date,
        foreign=_row_leg(row, "foreign", status=status),
        investment_trust=_row_leg(row, "investment_trust", status=status),
        dealer=_row_leg(row, "dealer", status=status),
        total=_row_leg(row, "total", status=status),
        source_provider=row.source_provider,
        source_identity=row.source_identity,
        source_dataset=row.source_dataset,
        source_endpoint=row.source_endpoint,
        adapter_version=row.adapter_version,
        source_as_of=row.source_as_of,
        published_at=row.published_at,
        retrieved_at=row.retrieved_at,
        availability=availability,
        freshness=FlowFreshness(row.freshness),
        status_reason=row.status_reason,
        lineage=row.lineage,
        response_content_hash=row.response_content_hash,
        raw_payload=row.raw_payload,
    )


def _is_newer(
    incoming: MarketInstitutionalFlowFact, existing: MarketInstitutionalFlowDaily
) -> bool:
    if incoming.source_as_of is None:
        return existing.source_as_of is None
    if existing.source_as_of is None:
        return True
    return incoming.source_as_of > existing.source_as_of


def decide_upsert(
    existing: MarketInstitutionalFlowDaily | None,
    incoming: MarketInstitutionalFlowFact,
) -> str:
    """Return the deterministic conflict decision without mutating a session."""

    if existing is None:
        return "INSERTED"
    if (
        incoming.response_content_hash
        and incoming.response_content_hash == existing.response_content_hash
    ):
        return "REUSED"
    if not _is_newer(incoming, existing):
        if incoming.source_as_of == existing.source_as_of:
            return "REJECTED_DUPLICATE_SOURCE_VERSION"
        return "REJECTED_OLDER_SOURCE_VERSION"
    if (
        existing.availability == FlowAvailability.AVAILABLE.value
        and incoming.availability is not FlowAvailability.AVAILABLE
    ):
        return "PRESERVED_AVAILABLE"
    return "UPDATED"


def upsert_market_institutional_flow(
    session: Session,
    fact: MarketInstitutionalFlowFact,
    *,
    ingested_at: datetime | None = None,
) -> str:
    """Idempotently write one fact and refuse stale or conflicting overwrites."""

    if fact.trading_date is None:
        raise ValueError("FUND-A persistence requires a trading date")
    existing = session.scalar(
        select(MarketInstitutionalFlowDaily)
        .where(
            MarketInstitutionalFlowDaily.market == fact.market,
            MarketInstitutionalFlowDaily.trading_date == fact.trading_date,
            MarketInstitutionalFlowDaily.source_identity == fact.source_identity,
        )
        .with_for_update()
    )
    decision = decide_upsert(existing, fact)
    if decision in {
        "REUSED",
        "PRESERVED_AVAILABLE",
        "REJECTED_DUPLICATE_SOURCE_VERSION",
        "REJECTED_OLDER_SOURCE_VERSION",
    }:
        return decision
    values = fact_to_model(fact, ingested_at=ingested_at)
    if existing is None:
        session.add(MarketInstitutionalFlowDaily(**values))
    else:
        for key, value in values.items():
            setattr(existing, key, value)
    session.flush()
    return decision


def read_market_institutional_flow_history(
    session: Session,
    market: str,
    *,
    as_of_date: date | None = None,
    limit: int = 25,
) -> list[MarketInstitutionalFlowFact]:
    source_identity = {
        "TPE": TWSE_INSTITUTIONAL_FLOW_SOURCE_IDENTITY,
        "TWO": TPEX_INSTITUTIONAL_FLOW_SOURCE_IDENTITY,
    }[market]
    statement: Select[tuple[MarketInstitutionalFlowDaily]] = select(
        MarketInstitutionalFlowDaily
    ).where(
        MarketInstitutionalFlowDaily.market == market,
        MarketInstitutionalFlowDaily.source_identity == source_identity,
    )
    if as_of_date is not None:
        statement = statement.where(MarketInstitutionalFlowDaily.trading_date <= as_of_date)
    rows = session.scalars(
        statement.order_by(desc(MarketInstitutionalFlowDaily.trading_date)).limit(limit)
    ).all()
    return [model_to_fact(row) for row in rows]


def build_market_institutional_flow_trend_from_db(
    session: Session,
    market: str,
    *,
    as_of_date: date | None = None,
    limit: int = 25,
    index_change: Decimal | None = None,
    previous_index_change: Decimal | None = None,
) -> MarketInstitutionalFlowTrend:
    facts = read_market_institutional_flow_history(
        session, market, as_of_date=as_of_date, limit=max(limit, 20)
    )
    return build_market_institutional_flow_trend(
        facts,
        market=market,
        as_of_date=as_of_date,
        index_change=index_change,
        previous_index_change=previous_index_change,
    )


__all__ = [
    "build_market_institutional_flow_trend_from_db",
    "decide_upsert",
    "fact_to_model",
    "model_to_fact",
    "read_market_institutional_flow_history",
    "upsert_market_institutional_flow",
]
