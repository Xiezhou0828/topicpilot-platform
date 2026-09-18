"""Read/write boundary for the FUND-B stock institutional-flow contract."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from topicpilot_api.historical_read_model import read_historical_bars
from topicpilot_api.market_data.stock_institutional_flow import (
    STOCK_FLOW_SCALE,
    STOCK_FLOW_UNIT,
    StockFlowFreshness,
    StockFlowLeg,
    StockFlowStatus,
    StockInstitutionalFlowFact,
    StockInstitutionalFlowFeatures,
    StockPriceObservation,
    build_stock_institutional_flow_features,
    expected_weekday_sessions,
    map_provider_facts,
)
from topicpilot_api.orm.stock_institutional_flow import StockInstitutionalFlowDaily
from topicpilot_api.problems import ApiProblem, NotFoundProblem


def resolve_stock_identity(
    session: Session, instrument_code: str, market: str | None
) -> dict[str, Any]:
    """Resolve a stock only by market + instrument code, failing on ambiguity."""

    normalized_market = market.strip().upper() if market else None
    rows = list(
        session.execute(
            text(
                """
                SELECT i.id, i.instrument_code, m.code AS market_code
                FROM topicpilot.instruments i
                JOIN topicpilot.markets m ON m.id = i.market_id
                WHERE i.instrument_code = :instrument_code
                  AND i.is_active = true
                  AND m.is_active = true
                  AND (:market_code IS NULL OR m.code = :market_code)
                ORDER BY m.code
                """
            ),
            {"instrument_code": instrument_code, "market_code": normalized_market},
        )
        .mappings()
        .all()
    )
    if not rows:
        raise NotFoundProblem(f"Stock {instrument_code!r} was not found")
    if len(rows) > 1:
        raise ApiProblem(
            409,
            "Ambiguous instrument",
            "The stock code exists in more than one market; specify market.",
            "https://topicpilot.example/problems/ambiguous-instrument",
        )
    row = rows[0]
    return {
        "id": row["id"],
        "instrument_code": row["instrument_code"],
        "market": row["market_code"],
    }


def _leg_values(prefix: str, fact: StockInstitutionalFlowFact) -> dict[str, Any]:
    leg = getattr(fact, prefix)
    return {
        f"{prefix}_buy": leg.buy,
        f"{prefix}_sell": leg.sell,
        f"{prefix}_net": leg.net,
    }


def fact_to_persistence_values(
    fact: StockInstitutionalFlowFact, *, instrument_id: UUID | str | None = None
) -> dict[str, Any]:
    resolved_id = instrument_id or fact.instrument_id
    if resolved_id is None:
        raise ValueError("canonical instrument_id is required before persistence")
    values: dict[str, Any] = {
        "instrument_id": resolved_id,
        "market": fact.market,
        "instrument_code": fact.instrument_code,
        "trading_date": fact.trading_date,
        "source_provider": fact.source_provider,
        "source_identity": fact.source_identity,
        "source_dataset": fact.source_dataset,
        "source_endpoint": fact.source_endpoint,
        "adapter_version": fact.adapter_version,
        "source_as_of": fact.source_as_of,
        "retrieved_at": fact.retrieved_at,
        "unit": STOCK_FLOW_UNIT,
        "scale": STOCK_FLOW_SCALE,
        "status": fact.status.value,
        "freshness": fact.freshness.value,
        "status_reason": fact.status_reason,
        "lineage": fact.lineage,
        "response_content_hash": fact.response_content_hash,
        "raw_payload": fact.raw_payload,
    }
    for prefix in ("foreign", "investment_trust", "dealer", "total"):
        values.update(_leg_values(prefix, fact))
    for prefix, leg in (
        ("foreign_dealer", fact.foreign_dealer),
        ("dealer_self", fact.dealer_self),
        ("dealer_hedge", fact.dealer_hedge),
    ):
        values.update(
            {
                f"{prefix}_{field}": getattr(leg, field) if leg else None
                for field in ("buy", "sell", "net")
            }
        )
    return values


def upsert_stock_institutional_flow(
    session: Session, fact: StockInstitutionalFlowFact, *, instrument_id: UUID | str | None = None
) -> None:
    """Idempotently persist a fact, refusing an older source snapshot."""

    values = fact_to_persistence_values(fact, instrument_id=instrument_id)
    table = StockInstitutionalFlowDaily.__table__
    statement = pg_insert(table).values(**values)
    excluded = statement.excluded
    statement = statement.on_conflict_do_update(
        index_elements=[table.c.instrument_id, table.c.trading_date, table.c.source_identity],
        set_={key: getattr(excluded, key) for key in values if key != "instrument_id"},
        where=(
            table.c.source_as_of.is_(None)
            | excluded.source_as_of.is_(None)
            | (excluded.source_as_of >= table.c.source_as_of)
        ),
    )
    session.execute(statement)


def persist_stock_institutional_flow_batch(
    session: Session,
    facts: tuple[StockInstitutionalFlowFact, ...] | list[StockInstitutionalFlowFact],
    canonical_instruments: dict[tuple[str, str], str],
) -> dict[str, Any]:
    mapped, mapping_errors = map_provider_facts(facts, canonical_instruments)
    for fact in mapped:
        upsert_stock_institutional_flow(session, fact)
    return {"persisted": len(mapped), "mappingErrors": list(mapping_errors)}


def _decimal_or_none(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _row_fact(row: Any) -> StockInstitutionalFlowFact:
    def leg(prefix: str) -> StockFlowLeg:
        return StockFlowLeg(
            Decimal(str(row[f"{prefix}_buy"])),
            Decimal(str(row[f"{prefix}_sell"])),
            Decimal(str(row[f"{prefix}_net"])),
        )

    def optional_leg(prefix: str) -> StockFlowLeg | None:
        if row[f"{prefix}_buy"] is None:
            return None
        return leg(prefix)

    return StockInstitutionalFlowFact(
        market=row["market"],
        instrument_code=row["instrument_code"],
        trading_date=row["trading_date"],
        foreign=leg("foreign"),
        investment_trust=leg("investment_trust"),
        dealer=leg("dealer"),
        total=leg("total"),
        source_provider=row["source_provider"],
        source_identity=row["source_identity"],
        source_dataset=row["source_dataset"],
        source_endpoint=row["source_endpoint"],
        adapter_version=row["adapter_version"],
        source_as_of=row["source_as_of"],
        retrieved_at=row["retrieved_at"],
        status=StockFlowStatus(row["status"]),
        freshness=StockFlowFreshness(row["freshness"]),
        status_reason=row["status_reason"],
        lineage=row["lineage"],
        response_content_hash=row["response_content_hash"],
        raw_payload=row["raw_payload"],
        foreign_dealer=optional_leg("foreign_dealer"),
        dealer_self=optional_leg("dealer_self"),
        dealer_hedge=optional_leg("dealer_hedge"),
        instrument_id=str(row["instrument_id"]),
    )


def read_stock_flow_facts(
    session: Session, instrument_id: UUID | str, *, as_of: date, limit: int = 200
) -> list[StockInstitutionalFlowFact]:
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200")
    rows = session.execute(
        select(StockInstitutionalFlowDaily)
        .where(
            StockInstitutionalFlowDaily.instrument_id == instrument_id,
            StockInstitutionalFlowDaily.trading_date <= as_of,
        )
        .order_by(
            StockInstitutionalFlowDaily.trading_date.desc(),
            StockInstitutionalFlowDaily.source_as_of.desc().nullslast(),
            StockInstitutionalFlowDaily.id.desc(),
        )
        .limit(limit)
    ).all()
    return [_row_fact(row[0]) for row in rows]


def read_market_holidays(
    session: Session, *, start_date: date, end_date: date, calendar_code: str = "TW_MARKET"
) -> tuple[date, ...]:
    rows = session.execute(
        text(
            """
            SELECT calendar_date
            FROM topicpilot.reference_calendar_dates
            WHERE calendar_code = :calendar_code
              AND date_kind IN ('HOLIDAY', 'SUSPENDED')
              AND calendar_date >= :start_date
              AND calendar_date <= :end_date
            ORDER BY calendar_date
            """
        ),
        {"calendar_code": calendar_code, "start_date": start_date, "end_date": end_date},
    ).all()
    return tuple(row[0] for row in rows)


def _read_price_observations(
    session: Session,
    code: str,
    market: str,
    as_of: date,
) -> dict[date, StockPriceObservation]:
    try:
        result = read_historical_bars(session, code, as_of - timedelta(days=90), as_of, market, 200)
    except (ApiProblem, NotFoundProblem):
        return {}
    return {
        item["trading_date"]: StockPriceObservation(
            trading_date=item["trading_date"],
            close=_decimal_or_none(item.get("close")),
            volume=_decimal_or_none(item.get("volume")),
            source_code=item.get("source_code"),
            quality_state=item.get("quality_state"),
        )
        for item in result.get("items", [])
    }


def read_stock_institutional_flow_features(
    session: Session,
    instrument_code: str,
    market: str | None,
    as_of: date,
    limit: int = 200,
) -> StockInstitutionalFlowFeatures:
    identity = resolve_stock_identity(session, instrument_code, market)
    start_date = as_of - timedelta(days=90)
    facts = read_stock_flow_facts(session, identity["id"], as_of=as_of, limit=limit)
    holidays = read_market_holidays(session, start_date=start_date, end_date=as_of)
    expected = expected_weekday_sessions(start_date, as_of, holidays)
    prices = _read_price_observations(
        session, identity["instrument_code"], identity["market"], as_of
    )
    return build_stock_institutional_flow_features(
        facts,
        market=identity["market"],
        instrument_code=identity["instrument_code"],
        requested_as_of=as_of,
        instrument_id=str(identity["id"]),
        expected_sessions=expected,
        prices=prices,
    )


__all__ = [
    "fact_to_persistence_values",
    "persist_stock_institutional_flow_batch",
    "read_market_holidays",
    "read_stock_flow_facts",
    "read_stock_institutional_flow_features",
    "resolve_stock_identity",
    "upsert_stock_institutional_flow",
]
