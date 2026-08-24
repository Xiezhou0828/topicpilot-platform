# ruff: noqa: RUF001, E501
"""Deterministic V2 Today/Home materialization and publication policy.

The request path reads the persisted envelope produced here.  This module is
deliberately provider-neutral: official index/aggregate adapters hand in
typed facts, while canonical daily observations remain a compatibility
fallback only when the established post-close path has not supplied an
official whole-market aggregate result.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from topicpilot_api.orm import HomeMarketFact, HomePublication, HomePublicationSection

HOME_PUBLICATION_VERSION = "home-v2.formal.v1"
HOME_SOURCE = "HOME_V2_FORMAL_PUBLICATION"
DAILY_FOCUS_SOURCE = "HOME_V2_DAILY_FOCUS_RULE_V1"
MAIN_TOPICS_SOURCE = "HOME_V2_FORMAL_TOPIC_PUBLICATION"
ROTATION_SOURCE = "HOME_V2_ROTATION_14_TRADING_SESSIONS"
SECTION_KEYS = (
    "marketOverview",
    "dailyFocus",
    "mainTopics",
    "heatingTopics",
    "coolingTopics",
    "marketEvents",
    "opportunities",
)

USER_MESSAGES = {
    "NO_PUBLISHED_MARKET_FACTS": "市場資料尚未完整。",
    "NO_FORMAL_TOPIC_PUBLICATION": "題材資料尚未完成發布。",
    "INSUFFICIENT_ROTATION_HISTORY": "目前累積的交易日資料不足，尚無法計算 14 日變化。",
    "DAILY_FOCUS_EVIDENCE_INCOMPLETE": "今日市場重點尚未完成。",
    "UPSTREAM_SOURCE_UNAVAILABLE": "這項市場資料目前無法提供。",
    "NO_FORMAL_MARKET_BREADTH": "市場廣度資料目前無法提供。",
    "PARTIAL_MARKET_FACTS": "部分市場資料目前無法提供。",
    "OPTIONAL_SECTION_NOT_FORMAL": "此區塊目前尚未建立正式資料來源。",
}


@dataclass(frozen=True)
class MarketTurnoverFact:
    market: str
    trading_date: date
    value: Decimal | None
    currency: str | None
    unit: str | None
    scale: int | None
    as_of: datetime | None
    source: str
    lineage: str
    status: str = "AVAILABLE"
    reason_code: str | None = None


@dataclass(frozen=True)
class SectionResult:
    status: str
    data_date: date | None
    as_of: datetime | None
    source: str | None
    reason_code: str | None
    user_message: str | None
    payload: Any
    diagnostic_detail: str | None = None

    def status_payload(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "dataDate": self.data_date,
            "asOf": self.as_of,
            "source": self.source,
            "reasonCode": self.reason_code,
            "userMessage": self.user_message,
        }


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value) if value.is_finite() else None
    return value


def _hash(value: Any) -> str:
    encoded = json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _number(value: Any) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _reason(code: str | None) -> str | None:
    return USER_MESSAGES.get(code) if code else None


def _status(
    status: str,
    *,
    data_date: date | None,
    as_of: datetime | None,
    source: str | None,
    reason_code: str | None = None,
    detail: str | None = None,
    payload: Any,
) -> SectionResult:
    return SectionResult(
        status=status,
        data_date=data_date,
        as_of=as_of,
        source=source,
        reason_code=reason_code,
        user_message=_reason(reason_code),
        payload=payload,
        diagnostic_detail=detail,
    )


def rank_formal_topics(rows: Iterable[Mapping[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    """Return the transparent V2 Main Topics ordering tuple.

    The tuple is: complete evidence first, observed participation, coverage,
    positive progression (average daily change), then stable slug.  No score
    is created; all displayed evidence remains raw or directly aggregated.
    """

    def key(row: Mapping[str, Any]) -> tuple[Any, ...]:
        complete = 0 if row.get("data_status") == "COMPLETE" else 1
        observed = -(int(row.get("observed_stock_count") or 0))
        coverage = -(float(row.get("coverage_pct") or 0))
        positive = -(int(row.get("positive_count") or 0))
        progression = -(float(row.get("average_change") or 0))
        return complete, observed, coverage, positive, progression, str(row.get("topic_slug") or "")

    result: list[dict[str, Any]] = []
    for row in sorted(rows, key=key)[:limit]:
        average = _number(row.get("average_change"))
        result.append(
            {
                "slug": row["topic_slug"],
                "name": row["topic_name"],
                "grade": row.get("market_grade"),
                "strength": None,
                "currentState": row.get("topic_direction"),
                "stockCount": int(row.get("stock_count") or 0),
                "summary": (
                    f"觀測 {int(row.get('observed_stock_count') or 0)} / "
                    f"{int(row.get('stock_count') or 0)} 檔，平均日變化 "
                    f"{average if average is not None else '無資料'}。"
                ),
                "favorite": False,
                "dataDate": row.get("snapshot_date"),
                "rankingEvidence": {
                    "availability": row.get("data_status"),
                    "observedStockCount": int(row.get("observed_stock_count") or 0),
                    "coveragePct": _number(row.get("coverage_pct")),
                    "positiveCount": int(row.get("positive_count") or 0),
                    "averageChange": average,
                    "rankingPolicy": "availability,observedParticipation,coverage,positiveProgression,slug",
                },
            }
        )
    return result


def calculate_rotation_14d(
    rows: Iterable[Mapping[str, Any]], *, target_date: date, limit: int = 3
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None]:
    """Compare current topic activity with the 14th prior trading session."""

    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    dates: set[date] = set()
    for row in rows:
        row_date = row.get("snapshot_date")
        if row_date is None or row_date > target_date:
            continue
        if (row.get("average_change") is None) or not int(row.get("observed_stock_count") or 0):
            continue
        grouped[str(row["topic_slug"])].append(row)
        dates.add(row_date)
    sessions = sorted(dates)
    if len(sessions) < 15:
        return [], [], "INSUFFICIENT_ROTATION_HISTORY"
    current_date = sessions[-1]
    reference_date = sessions[-15]
    if current_date != target_date:
        return [], [], "INSUFFICIENT_ROTATION_HISTORY"

    heating: list[dict[str, Any]] = []
    cooling: list[dict[str, Any]] = []
    for topic_rows in grouped.values():
        by_date = {row["snapshot_date"]: row for row in topic_rows}
        current = by_date.get(current_date)
        reference = by_date.get(reference_date)
        if current is None or reference is None:
            continue
        delta = float(current["average_change"]) - float(reference["average_change"])
        if delta == 0:
            continue
        item = {
            "topic": current["topic_name"],
            "topicSlug": current["topic_slug"],
            "strengthDelta": delta,
            "currentGrade": current.get("market_grade"),
            "summary": (
                f"近 14 個交易日的平均日變化差異為 {_number(delta)}。"
            ),
            "dataDate": current_date,
            "asOf": current.get("as_of_at"),
            "rotationEvidence": {
                "currentDate": current_date,
                "referenceDate": reference_date,
                "measure": "topic average daily canonical PRICE change",
            },
        }
        (heating if delta > 0 else cooling).append(item)
    heating.sort(key=lambda item: (-item["strengthDelta"], item["topicSlug"]))
    cooling.sort(key=lambda item: (item["strengthDelta"], item["topicSlug"]))
    return heating[:limit], cooling[:limit], None


def build_daily_focus(
    *,
    market_overview: Mapping[str, Any],
    main_topics: Sequence[Mapping[str, Any]],
    heating_topics: Sequence[Mapping[str, Any]],
    cooling_topics: Sequence[Mapping[str, Any]],
    data_date: date | None,
    as_of: datetime | None,
) -> SectionResult:
    """Build formal Daily Focus from published facts only."""

    health = market_overview.get("marketHealth") or {}
    breadth = market_overview.get("breadth") or []
    evidence: list[str] = []
    if health.get("advance") is not None and health.get("decline") is not None:
        evidence.append(
            f"市場上漲 {health['advance']} 家、下跌 {health['decline']} 家，"
            f"平盤 {health.get('flat', '—')} 家。"
        )
    elif breadth:
        observed = sum(int(item.get("observed") or 0) for item in breadth)
        evidence.append(f"目前已觀測 {observed} 家上市櫃股票的市場廣度。")
    if market_overview.get("indices"):
        available = [item for item in market_overview["indices"] if item.get("value") is not None]
        if available:
            first = available[0]
            direction = "上漲" if (first.get("change") or 0) > 0 else "下跌" if (first.get("change") or 0) < 0 else "持平"
            evidence.append(f"{first['indexName']} {direction}，收盤 {first['value']}。")
    if main_topics:
        evidence.append(f"目前主線為 {main_topics[0]['name']}。")
    if heating_topics:
        evidence.append(f"升溫題材以 {heating_topics[0]['topic']} 為首。")
    if cooling_topics:
        evidence.append(f"降溫題材以 {cooling_topics[0]['topic']} 為首。")
    if not evidence:
        return _status(
            "UNAVAILABLE",
            data_date=data_date,
            as_of=as_of,
            source=DAILY_FOCUS_SOURCE,
            reason_code="DAILY_FOCUS_EVIDENCE_INCOMPLETE",
            detail="formal Home inputs did not contain a meaningful market or topic fact",
            payload={
                "mode": "RULE_BASED_V1",
                "temporary": False,
                "headline": "今日市場重點尚未完成",
                "bullets": [],
                "dataDate": data_date,
                "source": DAILY_FOCUS_SOURCE,
                "reasonCode": "DAILY_FOCUS_EVIDENCE_INCOMPLETE",
                "userMessage": USER_MESSAGES["DAILY_FOCUS_EVIDENCE_INCOMPLETE"],
            },
        )
    headline = (
        "市場偏強，今日主線值得留意。"
        if (health.get("advance") or 0) > (health.get("decline") or 0)
        else "市場偏弱，今日主線仍需觀察。"
        if (health.get("decline") or 0) > (health.get("advance") or 0)
        else f"今日市場焦點：{main_topics[0]['name']}。"
    )
    return _status(
        "AVAILABLE",
        data_date=data_date,
        as_of=as_of,
        source=DAILY_FOCUS_SOURCE,
        payload={
            "mode": "RULE_BASED_V1",
            "temporary": False,
            "headline": headline,
            "bullets": evidence[:4],
            "dataDate": data_date,
            "source": DAILY_FOCUS_SOURCE,
        },
    )


def validate_home_gate(
    *, market_overview: SectionResult, main_topics: SectionResult, daily_focus: SectionResult
) -> tuple[str, str | None]:
    """Return the core Home finality gate.

    Market/session authority is the only section-level data requirement for a
    publishable envelope.  Main Topics and Daily Focus are independently
    typed sections: they are published when evidence exists and remain
    unavailable when it does not, without poisoning the whole Home envelope.
    """

    market_payload = market_overview.payload if isinstance(market_overview.payload, Mapping) else {}
    health = market_payload.get("marketHealth") or {}
    breadth = market_payload.get("breadth") or []
    market_minimum = bool(
        any(int(item.get("observed") or 0) > 0 for item in breadth)
        or health.get("advance") is not None
        or any(item.get("value") is not None for item in market_payload.get("indices", []))
    )
    if market_minimum and market_overview.status in {"AVAILABLE", "PARTIAL"}:
        return "PUBLISHED", None
    if not market_minimum:
        return "UNAVAILABLE", "NO_PUBLISHED_MARKET_FACTS"
    return "UNAVAILABLE", "NO_PUBLISHED_MARKET_FACTS"


def _latest_canonical_date(session: Session) -> date | None:
    return session.execute(
        text(
            """
            SELECT max((co.observed_at AT TIME ZONE m.timezone)::date)
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
            """
        )
    ).scalar_one_or_none()


def _breadth(session: Session, trading_date: date) -> tuple[list[dict[str, Any]], datetime | None]:
    rows = session.execute(
        text(
            """
            WITH universe AS (
                SELECT i.id, m.code AS market
                FROM topicpilot.instruments i
                JOIN topicpilot.markets m ON m.id = i.market_id
                WHERE i.is_active = true AND m.is_active = true
                  AND i.instrument_type = 'EQUITY'
                  AND m.code IN ('TPE', 'TWO')
                  AND (i.valid_from IS NULL OR i.valid_from <= :trading_date)
                  AND (i.valid_to IS NULL OR i.valid_to >= :trading_date)
                  AND (m.valid_from IS NULL OR m.valid_from <= :trading_date)
                  AND (m.valid_to IS NULL OR m.valid_to >= :trading_date)
            ), observations AS (
                SELECT DISTINCT ON (current.instrument_id)
                    current.instrument_id, current.market_code, current.close,
                    current.status_code, current.observed_at, previous.close AS previous_close
                FROM topicpilot.vw_daily_market_observations current
                LEFT JOIN LATERAL (
                    SELECT prior.close
                    FROM topicpilot.vw_daily_market_observations prior
                    WHERE prior.instrument_id = current.instrument_id
                      AND prior.trade_date < current.trade_date
                    ORDER BY prior.trade_date DESC, prior.observed_at DESC,
                             prior.canonical_observation_id DESC
                    LIMIT 1
                ) previous ON true
                WHERE current.trade_date = :trading_date
                ORDER BY current.instrument_id, current.observed_at DESC,
                         current.canonical_observation_id DESC
            )
            SELECT
                u.market,
                count(*)::integer AS eligible,
                count(o.instrument_id)::integer AS observed,
                count(o.instrument_id) FILTER (WHERE o.close IS NOT NULL AND o.close > 0)::integer AS priced,
                count(o.instrument_id) FILTER (WHERE o.close IS NOT NULL AND o.previous_close IS NOT NULL AND o.close > o.previous_close)::integer AS advance,
                count(o.instrument_id) FILTER (WHERE o.close IS NOT NULL AND o.previous_close IS NOT NULL AND o.close < o.previous_close)::integer AS decline,
                count(o.instrument_id) FILTER (WHERE o.close IS NOT NULL AND o.previous_close IS NOT NULL AND o.close = o.previous_close)::integer AS flat,
                count(o.instrument_id) FILTER (WHERE o.close IS NULL AND o.status_code IN ('NO_TRADE', 'SUSPENDED', 'EXCHANGE_CONFIRMED_NO_DATA'))::integer AS unavailable,
                max(o.observed_at) AS as_of
            FROM universe u
            LEFT JOIN observations o ON o.instrument_id = u.id
            GROUP BY u.market
            ORDER BY u.market
            """
        ),
        {"trading_date": trading_date},
    ).mappings().all()
    as_of = max((row["as_of"] for row in rows if row["as_of"] is not None), default=None)
    return [dict(row) for row in rows], as_of


def _formal_topic_rows(session: Session, trading_date: date) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT DISTINCT ON (topic_id)
                    topic_id, topic_slug, topic_name, snapshot_date,
                    market_grade, topic_direction, stock_count,
                    observed_stock_count, coverage_pct, average_change,
                    data_status, positive_count, as_of_at, published_at,
                    source_artifact_hash
                FROM topicpilot.topic_snapshots
                WHERE snapshot_date = :trading_date
                  AND publication_mode = 'FORMAL'
                  AND publication_state = 'PUBLISHED'
                  AND superseded_by_snapshot_id IS NULL
                ORDER BY topic_id, correction_sequence DESC, published_at DESC NULLS LAST, id DESC
                """
            ),
            {"trading_date": trading_date},
        ).mappings()
    ]


def _formal_topic_history(session: Session, trading_date: date) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT topic_id, topic_slug, topic_name, snapshot_date,
                       market_grade, average_change, observed_stock_count,
                       data_status, as_of_at
                FROM topicpilot.topic_snapshots
                WHERE snapshot_date <= :trading_date
                  AND publication_mode = 'FORMAL'
                  AND publication_state = 'PUBLISHED'
                  AND superseded_by_snapshot_id IS NULL
                  AND average_change IS NOT NULL
                  AND observed_stock_count > 0
                ORDER BY snapshot_date, topic_slug, correction_sequence DESC, id DESC
                """
            ),
            {"trading_date": trading_date},
        ).mappings()
    ]


def _market_index_payload(fact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "market": fact.get("market"),
        "indexCode": fact.get("indexCode"),
        "indexName": fact.get("indexName"),
        "tradingDate": fact.get("tradingDate"),
        "session": fact.get("session"),
        "value": _number(fact.get("value")),
        "previousClose": _number(fact.get("previousClose")),
        "change": _number(fact.get("change")),
        "changePct": _number(fact.get("changePct")),
        "asOf": fact.get("asOf"),
        "source": fact.get("source"),
        "lineage": fact.get("lineage"),
        "status": fact.get("status", "AVAILABLE"),
        "reasonCode": fact.get("reasonCode"),
    }


def _index_fact_input(item: Any) -> dict[str, Any]:
    if hasattr(item, "to_dict"):
        # Keep typed date/time/numeric values for SQLAlchemy persistence.  The
        # public ``to_dict`` shape is intentionally JSON-safe and therefore
        # contains ISO strings, which are not suitable for DateTime columns.
        status = getattr(item, "data_status", "UNAVAILABLE")
        status = getattr(status, "value", status)
        return {
            "market": getattr(item, "market", None),
            "indexCode": getattr(item, "index_identity", None),
            "indexName": getattr(item, "display_name", None),
            "tradingDate": getattr(item, "trading_date", None),
            "session": "CLOSE",
            "value": getattr(item, "value", None),
            "previousClose": getattr(item, "previous_close", None),
            "change": getattr(item, "change", None),
            "changePct": getattr(item, "change_pct", None),
            "asOf": getattr(item, "as_of", None),
            "source": getattr(item, "source_identity", None),
            "lineage": getattr(item, "lineage", None),
            "status": status,
            "reasonCode": getattr(item, "status_reason", None),
        }
    return dict(item)


def _turnover_payload(item: MarketTurnoverFact | Mapping[str, Any]) -> dict[str, Any]:
    raw = item if isinstance(item, Mapping) else item.__dict__
    return {
        "market": raw.get("market"),
        "tradingDate": raw.get("trading_date", raw.get("tradingDate")),
        "session": raw.get("session", "CLOSE"),
        "value": _number(raw.get("value")),
        "currency": raw.get("currency"),
        "unit": raw.get("unit"),
        "scale": raw.get("scale"),
        "asOf": raw.get("as_of", raw.get("asOf")),
        "source": raw.get("source"),
        "lineage": raw.get("lineage"),
        "status": raw.get("status", "AVAILABLE"),
        "reasonCode": raw.get("reason_code", raw.get("reasonCode")),
    }


def _aggregate_fact_input(item: Any) -> dict[str, Any]:
    """Map a typed official aggregate result without losing NULL evidence."""

    if hasattr(item, "to_dict"):
        status = getattr(item, "data_status", "UNAVAILABLE")
        status = getattr(status, "value", status)
        return {
            "market": getattr(item, "market", None),
            "tradingDate": getattr(item, "trading_date", None),
            "turnover": getattr(item, "turnover", None),
            "currency": getattr(item, "currency", None),
            "turnoverUnit": getattr(item, "turnover_unit", None),
            "turnoverScale": getattr(item, "turnover_scale", None),
            "eligible": getattr(item, "eligible", None),
            "observed": getattr(item, "observed", None),
            "advancers": getattr(item, "advancers", None),
            "decliners": getattr(item, "decliners", None),
            "unchanged": getattr(item, "unchanged", None),
            "unavailable": getattr(item, "unavailable", None),
            "limitUpCount": getattr(item, "limit_up_count", None),
            "limitDownCount": getattr(item, "limit_down_count", None),
            "source": getattr(item, "source", None),
            "sourceEndpoint": getattr(item, "source_endpoint", None),
            "lineage": getattr(item, "lineage", None),
            "asOf": getattr(item, "as_of", None),
            "status": status,
            "reasonCode": getattr(item, "status_reason", None),
        }
    raw = dict(item)
    return {
        "market": raw.get("market"),
        "tradingDate": raw.get("trading_date", raw.get("tradingDate")),
        "turnover": raw.get("turnover", raw.get("value")),
        "currency": raw.get("currency", "TWD"),
        "turnoverUnit": raw.get("turnover_unit", raw.get("turnoverUnit", raw.get("unit", "TWD"))),
        "turnoverScale": raw.get("turnover_scale", raw.get("turnoverScale", raw.get("scale", 0))),
        "eligible": raw.get("eligible"),
        "observed": raw.get("observed"),
        "advancers": raw.get("advancers", raw.get("advance")),
        "decliners": raw.get("decliners", raw.get("decline")),
        "unchanged": raw.get("unchanged", raw.get("flat")),
        "unavailable": raw.get("unavailable"),
        "limitUpCount": raw.get("limit_up_count", raw.get("limitUpCount", raw.get("limitUp"))),
        "limitDownCount": raw.get("limit_down_count", raw.get("limitDownCount", raw.get("limitDown"))),
        "source": raw.get("source"),
        "sourceEndpoint": raw.get("source_endpoint", raw.get("sourceEndpoint")),
        "lineage": raw.get("lineage"),
        "asOf": raw.get("as_of", raw.get("asOf")),
        "status": raw.get("status", raw.get("dataStatus", "UNAVAILABLE")),
        "reasonCode": raw.get("reason_code", raw.get("reasonCode", raw.get("statusReason"))),
    }


def materialize_home_v2(
    session: Session,
    *,
    trading_date: date | None = None,
    source_run_id: str | None = None,
    market_index_facts: Sequence[Any] = (),
    turnover_facts: Sequence[MarketTurnoverFact | Mapping[str, Any]] = (),
    market_aggregate_facts: Sequence[Any] = (),
    now: datetime | None = None,
) -> dict[str, Any]:
    """Materialize and persist one deterministic Home envelope."""

    generated_at = (now or datetime.now(UTC)).astimezone(UTC)
    trading_date = trading_date or _latest_canonical_date(session)
    if trading_date is None:
        raise ValueError("HOME_SOURCE_DATE_UNAVAILABLE")
    index_inputs = [_index_fact_input(item) for item in market_index_facts]
    turnover_inputs = [_turnover_payload(item) for item in turnover_facts]
    aggregate_inputs = [_aggregate_fact_input(item) for item in market_aggregate_facts]
    aggregate_by_market = {item.get("market"): item for item in aggregate_inputs}
    if aggregate_inputs:
        breadth_payload = []
        for market in ("TPE", "TWO"):
            fact = aggregate_by_market.get(market) or {}
            available = fact.get("status") == "AVAILABLE"
            breadth_payload.append(
                {
                    "market": market,
                    "eligible": int(fact["eligible"] or 0) if available else 0,
                    "observed": int(fact["observed"] or 0) if available else 0,
                    "advance": int(fact["advancers"]) if available and fact.get("advancers") is not None else None,
                    "decline": int(fact["decliners"]) if available and fact.get("decliners") is not None else None,
                    "flat": int(fact["unchanged"]) if available and fact.get("unchanged") is not None else None,
                    "unavailable": int(fact["unavailable"] or 0) if available else 0,
                    "coverage": {
                        "denominator": "official whole-market stock aggregate",
                        "eligible": fact.get("eligible"),
                        "observed": fact.get("observed"),
                        "authority": fact.get("source"),
                        "endpoint": fact.get("sourceEndpoint"),
                        "status": fact.get("status", "UNAVAILABLE"),
                        "reasonCode": fact.get("reasonCode"),
                    },
                    "asOf": fact.get("asOf"),
                    "source": fact.get("source") or "official market aggregate provider",
                }
            )
        breadth_as_of = max(
            (item["asOf"] for item in breadth_payload if item.get("asOf")),
            default=None,
        )
        breadth_rows = []
    else:
        breadth_rows, breadth_as_of = _breadth(session, trading_date)
        breadth_payload = [
            {
                "market": row["market"],
                "eligible": int(row["eligible"] or 0),
                "observed": int(row["observed"] or 0),
                "advance": int(row["advance"] or 0),
                "decline": int(row["decline"] or 0),
                "flat": int(row["flat"] or 0),
                "unavailable": int(row["unavailable"] or 0),
                "coverage": {
                    "denominator": "active date-effective EQUITY instruments in TPE/TWO",
                    "eligible": int(row["eligible"] or 0),
                    "observed": int(row["observed"] or 0),
                },
                "asOf": row["as_of"],
                "source": "topicpilot.vw_daily_market_observations",
            }
            for row in breadth_rows
        ]
        for item, row in zip(breadth_payload, breadth_rows, strict=True):
            item["advance"] = int(row["advance"] or 0)
            item["decline"] = int(row["decline"] or 0)
            item["flat"] = int(row["flat"] or 0)
            item["unavailable"] = int(row["unavailable"] or 0)
            item["coverage"]["priceObserved"] = int(row["priced"] or 0)

    total_eligible = sum(item["eligible"] for item in breadth_payload)
    total_observed = sum(item["observed"] for item in breadth_payload)
    total_unavailable = sum(item["unavailable"] for item in breadth_payload)
    market_health = {
        "market": "TPE+TWO",
        "status": "AVAILABLE" if total_observed else "UNAVAILABLE",
        "totalStocks": total_eligible,
        "advance": sum(int(item.get("advance") or 0) for item in breadth_payload),
        "decline": sum(int(item.get("decline") or 0) for item in breadth_payload),
        "flat": sum(int(item.get("flat") or 0) for item in breadth_payload),
        "unavailable": total_unavailable,
    }
    indices = [_market_index_payload(item) for item in index_inputs]
    by_market_index = {item.get("market"): item for item in indices}
    for market, code, name in (
        ("TPE", "TWSE:TAIEX", "TWSE 加權指數"),
        ("TWO", "TPEX:TPEx", "TPEx 櫃買指數"),
    ):
        by_market_index.setdefault(
            market,
            {
                "market": market,
                "indexCode": code,
                "indexName": name,
                "tradingDate": trading_date,
                "session": "CLOSE",
                "value": None,
                "previousClose": None,
                "change": None,
                "changePct": None,
                "asOf": breadth_as_of,
                "source": "official market aggregate provider",
                "lineage": "awaiting typed official market-index fact",
                "status": "UNAVAILABLE",
                "reasonCode": "UPSTREAM_SOURCE_UNAVAILABLE",
            },
        )
    indices = [by_market_index[market] for market in ("TPE", "TWO")]
    if aggregate_inputs:
        turnover_inputs = [
            {
                "market": item.get("market"),
                "tradingDate": item.get("tradingDate"),
                "session": "CLOSE",
                "value": _number(item.get("turnover")),
                "currency": item.get("currency"),
                "unit": item.get("turnoverUnit"),
                "scale": item.get("turnoverScale"),
                "asOf": item.get("asOf"),
                "source": item.get("source"),
                "lineage": item.get("lineage"),
                "status": item.get("status", "UNAVAILABLE"),
                "reasonCode": item.get("reasonCode"),
            }
            for item in aggregate_inputs
        ]
    turnover = [_turnover_payload(item) for item in turnover_inputs]
    turnover_by_market = {item.get("market"): item for item in turnover}
    for market in ("TPE", "TWO"):
        turnover_by_market.setdefault(
            market,
            {
                "market": market,
                "tradingDate": trading_date,
                "session": "CLOSE",
                "value": None,
                "currency": "TWD",
                "unit": None,
                "scale": None,
                "asOf": breadth_as_of,
                "source": "official market aggregate provider",
                "lineage": "turnover source/units not supplied to Home materializer",
                "status": "UNAVAILABLE",
                "reasonCode": "UPSTREAM_SOURCE_UNAVAILABLE",
            },
        )
    turnover = [turnover_by_market[market] for market in ("TPE", "TWO")]
    available_indices = [item for item in indices if item.get("status") == "AVAILABLE" and item.get("value") is not None]
    available_turnover = [item for item in turnover if item.get("status") == "AVAILABLE" and item.get("value") is not None]
    if aggregate_inputs:
        market_data_status = (
            "AVAILABLE"
            if all(aggregate_by_market.get(market, {}).get("status") == "AVAILABLE" for market in ("TPE", "TWO"))
            else "PARTIAL"
            if aggregate_inputs and (available_indices or available_turnover or total_observed)
            else "UNAVAILABLE"
        )
    else:
        market_data_status = "AVAILABLE" if total_observed else "UNAVAILABLE"
    aggregate_limits = [item for item in aggregate_inputs if item.get("status") == "AVAILABLE"]
    limit_up_values = [item.get("limitUpCount") for item in aggregate_limits]
    limit_down_values = [item.get("limitDownCount") for item in aggregate_limits]
    limits_complete = len(aggregate_limits) == 2 and all(value is not None for value in limit_up_values + limit_down_values)
    limits_payload = {
        "limitUp": sum(int(value) for value in limit_up_values) if limits_complete else None,
        "limitDown": sum(int(value) for value in limit_down_values) if limits_complete else None,
        "reasonCode": None if limits_complete else "PARTIAL_LIMIT_AUTHORITY" if aggregate_limits else "UPSTREAM_SOURCE_UNAVAILABLE",
        "source": ";".join(sorted({str(item.get("source")) for item in aggregate_inputs if item.get("source")})) or "official market aggregate provider",
    }
    market_overview_payload = {
        "dataDate": trading_date,
        "updatedAt": breadth_as_of,
        "dataStatus": market_data_status,
        "trackedStockCount": sum(int(item.get("eligible") or 0) for item in breadth_payload) if aggregate_inputs else total_eligible,
        "trackedTopicCount": 0,
        "latestSnapshotTime": breadth_as_of,
        "marketHealth": market_health,
        "breadth": breadth_payload,
        "indices": indices,
        "turnover": turnover,
        "limits": limits_payload,
        "source": HOME_SOURCE,
    }
    market_status = market_data_status
    market_reason = None if market_status == "AVAILABLE" else "PARTIAL_MARKET_FACTS" if market_status == "PARTIAL" else "NO_PUBLISHED_MARKET_FACTS"
    market_section = _status(
        market_status,
        data_date=trading_date,
        as_of=breadth_as_of,
        source=HOME_SOURCE,
        reason_code=market_reason,
        detail=("official whole-market aggregate facts are available" if aggregate_inputs and market_status == "AVAILABLE" else "official whole-market aggregate facts are partial" if aggregate_inputs else "canonical breadth is available" if total_observed else "no canonical daily breadth rows"),
        payload=market_overview_payload,
    )

    topic_rows = _formal_topic_rows(session, trading_date)
    main_topics_payload = rank_formal_topics(topic_rows)
    main_section = _status(
        "AVAILABLE" if main_topics_payload else "UNAVAILABLE",
        data_date=trading_date,
        as_of=max((row["as_of_at"] for row in topic_rows if row.get("as_of_at")), default=None),
        source=MAIN_TOPICS_SOURCE,
        reason_code=None if main_topics_payload else "NO_FORMAL_TOPIC_PUBLICATION",
        detail=f"formal topic rows selected: {len(topic_rows)}",
        payload=main_topics_payload,
    )
    market_overview_payload["trackedTopicCount"] = len(topic_rows)

    rotation_rows = _formal_topic_history(session, trading_date)
    heating, cooling, rotation_reason = calculate_rotation_14d(rotation_rows, target_date=trading_date)
    rotation_as_of = max((row["as_of_at"] for row in rotation_rows if row.get("as_of_at")), default=None)
    heating_section = _status(
        "AVAILABLE" if heating else "UNAVAILABLE",
        data_date=trading_date,
        as_of=rotation_as_of,
        source=ROTATION_SOURCE,
        reason_code=None if heating else rotation_reason or "INSUFFICIENT_ROTATION_HISTORY",
        detail=f"formal topic sessions available: {len({row['snapshot_date'] for row in rotation_rows})}",
        payload=heating,
    )
    cooling_section = _status(
        "AVAILABLE" if cooling else "UNAVAILABLE",
        data_date=trading_date,
        as_of=rotation_as_of,
        source=ROTATION_SOURCE,
        reason_code=None if cooling else rotation_reason or "INSUFFICIENT_ROTATION_HISTORY",
        detail=f"formal topic sessions available: {len({row['snapshot_date'] for row in rotation_rows})}",
        payload=cooling,
    )
    daily_section = build_daily_focus(
        market_overview=market_overview_payload,
        main_topics=main_topics_payload,
        heating_topics=heating,
        cooling_topics=cooling,
        data_date=trading_date,
        as_of=max((item for item in (breadth_as_of, rotation_as_of) if item), default=None),
    )
    events_section = _status(
        "UNAVAILABLE",
        data_date=trading_date,
        as_of=None,
        source="HOME_V2_FORMAL_EVENT_AUTHORITY",
        reason_code="OPTIONAL_SECTION_NOT_FORMAL",
        detail="temporary topic snapshot diff events do not participate in the formal gate",
        payload=[],
    )
    opportunities_section = _status(
        "UNAVAILABLE",
        data_date=trading_date,
        as_of=None,
        source="HOME_V2_FORMAL_OPPORTUNITY_AUTHORITY",
        reason_code="OPTIONAL_SECTION_NOT_FORMAL",
        detail="temporary opportunity bridge does not participate in the formal gate",
        payload=[],
    )
    sections = {
        "marketOverview": market_section,
        "dailyFocus": daily_section,
        "mainTopics": main_section,
        "heatingTopics": heating_section,
        "coolingTopics": cooling_section,
        "marketEvents": events_section,
        "opportunities": opportunities_section,
    }
    publication_state, gate_reason = validate_home_gate(
        market_overview=market_section,
        main_topics=main_section,
        daily_focus=daily_section,
    )
    section_statuses = {key: sections[key].status_payload() for key in SECTION_KEYS}
    generated_at = generated_at
    published_at = generated_at if publication_state == "PUBLISHED" else None
    publication_input = {
        "tradingDate": trading_date,
        "sourceRunId": source_run_id,
        "marketOverview": market_overview_payload,
        "dailyFocus": daily_section.payload,
        "mainTopics": main_topics_payload,
        "heatingTopics": heating,
        "coolingTopics": cooling,
        "sectionStatuses": section_statuses,
    }
    source_dataset_id = f"home-input:{trading_date.isoformat()}:{_hash(publication_input)}"
    publication_payload = {
        "contractVersion": "v2.home-read-model.v2",
        # Preserve the existing HomeResponse top-level date contract.  The
        # publication envelope and section statuses carry timestamp-level
        # ``asOf`` values for freshness/provenance.
        "asOf": trading_date,
        "generatedAt": generated_at,
        "publication": {
            "tradingDate": trading_date,
            "asOf": max((item for item in (breadth_as_of, rotation_as_of) if item), default=None),
            "generatedAt": generated_at,
            "publishedAt": published_at,
            "state": publication_state,
            "version": HOME_PUBLICATION_VERSION,
            "sourceRunId": source_run_id,
            "sourceDatasetId": source_dataset_id,
            "lineage": {
                "canonicalDailyMarket": "topicpilot.vw_daily_market_observations",
                "formalTopics": "topicpilot.topic_snapshots",
            },
            "completeness": {
                "required": ["marketOverview"],
                "sectionAvailableWhenEvidenceExists": ["dailyFocus", "mainTopics"],
                "optional": ["heatingTopics", "coolingTopics", "marketEvents", "opportunities"],
                "sectionStatuses": section_statuses,
            },
        },
        "marketOverview": market_overview_payload,
        "dailyFocus": daily_section.payload,
        "mainTopics": main_topics_payload,
        "marketPulse": [],
        "heatingTopics": heating,
        "coolingTopics": cooling,
        "opportunities": [],
        "sectionStatuses": section_statuses,
        "dataQuality": {
            "status": "AVAILABLE" if publication_state == "PUBLISHED" and market_section.status == "AVAILABLE" and all(
                item.status != "UNAVAILABLE" for key, item in sections.items() if key in {"marketOverview"}
            ) else "PARTIAL" if publication_state == "PUBLISHED" else "UNAVAILABLE",
            "source": HOME_SOURCE,
            "classification": "FORMAL",
            "temporarySections": ["marketEvents", "opportunities"],
            "missingSections": [key for key, item in sections.items() if item.status == "UNAVAILABLE"],
            "notes": ["Market Events 與 Opportunities 不參與 Today V1 正式發布 gate。"],
            "diagnosticCodes": {
                key: item.reason_code for key, item in sections.items() if item.reason_code
            },
        },
    }
    lineage_hash = _hash(
        {
            "publicationVersion": HOME_PUBLICATION_VERSION,
            "sourceDatasetId": source_dataset_id,
            "sectionStatuses": section_statuses,
        }
    )
    existing = session.scalar(
        text(
            """
            SELECT id FROM topicpilot.home_publications
            WHERE trading_date = :trading_date
              AND source_dataset_id = :source_dataset_id
              AND publication_version = :publication_version
            """
        ),
        {
            "trading_date": trading_date,
            "source_dataset_id": source_dataset_id,
            "publication_version": HOME_PUBLICATION_VERSION,
        },
    )
    if existing is not None:
        return {
            "status": "IDEMPOTENT",
            "publicationId": str(existing),
            "tradingDate": trading_date.isoformat(),
            "publicationState": publication_state,
            "sourceDatasetId": source_dataset_id,
            "sectionStatuses": section_statuses,
        }
    publication = HomePublication(
        trading_date=trading_date,
        as_of_at=max((item for item in (breadth_as_of, rotation_as_of) if item), default=None),
        generated_at=generated_at,
        published_at=published_at,
        publication_state=publication_state,
        publication_version=HOME_PUBLICATION_VERSION,
        source_run_id=source_run_id,
        source_dataset_id=source_dataset_id,
        lineage_hash=lineage_hash,
        completeness=_json_safe(publication_payload["publication"]["completeness"]),
        payload=_json_safe(publication_payload),
        diagnostic_reason=gate_reason,
    )
    session.add(publication)
    session.flush()
    for key in SECTION_KEYS:
        item = sections[key]
        session.add(
            HomePublicationSection(
                publication_id=publication.id,
                section_key=key,
                status=item.status,
                data_date=item.data_date,
                as_of_at=item.as_of,
                source=item.source,
                reason_code=item.reason_code,
                user_message=item.user_message,
                diagnostic_detail=item.diagnostic_detail,
                payload=_json_safe(item.payload) if isinstance(item.payload, Mapping) else {"items": _json_safe(item.payload)},
            )
        )
    for item in indices:
        session.add(
            HomeMarketFact(
                publication_id=publication.id,
                fact_type="INDEX",
                market=item["market"],
                index_code=item["indexCode"],
                index_name=item["indexName"],
                trading_date=trading_date,
                session=item.get("session"),
                value=item.get("value"),
                previous_close=item.get("previousClose"),
                change=item.get("change"),
                change_pct=item.get("changePct"),
                as_of_at=item.get("asOf"),
                source=item.get("source") or "official market aggregate provider",
                lineage=item.get("lineage") or "typed market index input",
                publication_state="PUBLISHED" if item.get("value") is not None else "UNAVAILABLE",
                reason_code=item.get("reasonCode"),
            )
        )
    for item in turnover:
        session.add(
            HomeMarketFact(
                publication_id=publication.id,
                fact_type="TURNOVER",
                market=item["market"],
                index_code=None,
                index_name=None,
                trading_date=trading_date,
                session=item.get("session"),
                value=item.get("value"),
                currency=item.get("currency"),
                unit=item.get("unit"),
                scale=item.get("scale"),
                as_of_at=item.get("asOf"),
                source=item.get("source") or "official market aggregate provider",
                lineage=item.get("lineage") or "typed market turnover input",
                publication_state="PUBLISHED" if item.get("value") is not None else "UNAVAILABLE",
                reason_code=item.get("reasonCode"),
            )
        )
    for item in breadth_payload:
        session.add(
            HomeMarketFact(
                publication_id=publication.id,
                fact_type="BREADTH",
                market=item["market"],
                index_code=None,
                index_name=None,
                trading_date=trading_date,
                session="CLOSE",
                as_of_at=item.get("asOf"),
                source=item["source"],
                lineage="active date-effective equity denominator; accepted canonical daily observations",
                publication_state="PUBLISHED" if item["observed"] else "UNAVAILABLE",
                reason_code=None if item["observed"] else "NO_FORMAL_MARKET_BREADTH",
                coverage=item["coverage"],
            )
        )
    session.add(
        HomeMarketFact(
            publication_id=publication.id,
            fact_type="LIMITS",
            market="TPE+TWO",
            index_code=None,
            index_name=None,
            trading_date=trading_date,
            session="CLOSE",
            as_of_at=breadth_as_of,
            source=limits_payload["source"],
            lineage="official whole-market limit-count authority; missing market values remain NULL",
            publication_state="PUBLISHED"
            if limits_payload["limitUp"] is not None or limits_payload["limitDown"] is not None
            else "UNAVAILABLE",
            reason_code=limits_payload["reasonCode"],
            coverage={
                "limitUp": limits_payload["limitUp"],
                "limitDown": limits_payload["limitDown"],
                "markets": [
                    {
                        "market": item.get("market"),
                        "limitUp": item.get("limitUpCount"),
                        "limitDown": item.get("limitDownCount"),
                        "source": item.get("source"),
                        "reasonCode": item.get("reasonCode"),
                    }
                    for item in aggregate_inputs
                ],
            },
        )
    )
    session.commit()
    return {
        "status": "SUCCESS",
        "publicationId": str(publication.id),
        "tradingDate": trading_date.isoformat(),
        "publicationState": publication_state,
        "sourceDatasetId": source_dataset_id,
        "sectionStatuses": section_statuses,
    }


def read_latest_home_publication(session: Session) -> dict[str, Any] | None:
    """Read the latest V2 envelope; no legacy completed-run gate is used."""

    try:
        row = session.execute(
            text(
                """
                SELECT payload
                FROM topicpilot.home_publications
                WHERE publication_state IN ('PUBLISHED', 'UNAVAILABLE')
                ORDER BY trading_date DESC, published_at DESC NULLS LAST, generated_at DESC, id DESC
                LIMIT 1
                """
            )
        ).mappings().one_or_none()
    except SQLAlchemyError:
        return None
    return dict(row["payload"]) if row else None


def empty_home_v2(now: datetime, *, tracked_stock_count: int = 0) -> dict[str, Any]:
    """Return a typed, product-safe fail-closed envelope before first publish."""

    statuses = {
        key: {
            "status": "UNAVAILABLE",
            "dataDate": None,
            "asOf": None,
            "source": HOME_SOURCE,
            "reasonCode": "NO_PUBLISHED_MARKET_FACTS"
            if key == "marketOverview"
            else "NO_FORMAL_TOPIC_PUBLICATION"
            if key == "mainTopics"
            else "DAILY_FOCUS_EVIDENCE_INCOMPLETE"
            if key == "dailyFocus"
            else "INSUFFICIENT_ROTATION_HISTORY"
            if key in {"heatingTopics", "coolingTopics"}
            else "OPTIONAL_SECTION_NOT_FORMAL",
            "userMessage": USER_MESSAGES["NO_PUBLISHED_MARKET_FACTS"]
            if key == "marketOverview"
            else USER_MESSAGES["NO_FORMAL_TOPIC_PUBLICATION"]
            if key == "mainTopics"
            else USER_MESSAGES["DAILY_FOCUS_EVIDENCE_INCOMPLETE"]
            if key == "dailyFocus"
            else USER_MESSAGES["INSUFFICIENT_ROTATION_HISTORY"]
            if key in {"heatingTopics", "coolingTopics"}
            else USER_MESSAGES["OPTIONAL_SECTION_NOT_FORMAL"],
        }
        for key in SECTION_KEYS
    }
    return {
        "contractVersion": "v2.home-read-model.v2",
        "asOf": None,
        "generatedAt": now,
        "publication": {
            "tradingDate": None,
            "asOf": None,
            "generatedAt": now,
            "publishedAt": None,
            "state": "UNAVAILABLE",
            "version": HOME_PUBLICATION_VERSION,
            "sourceRunId": None,
            "sourceDatasetId": None,
            "lineage": {},
            "completeness": {"sectionStatuses": statuses},
        },
        "marketOverview": {
            "dataDate": None,
            "updatedAt": None,
            "dataStatus": "UNAVAILABLE",
            "trackedStockCount": tracked_stock_count,
            "trackedTopicCount": 0,
            "latestSnapshotTime": None,
            "marketHealth": None,
            "breadth": [],
            "indices": [],
            "turnover": [],
            "limits": None,
            "source": HOME_SOURCE,
        },
        "dailyFocus": {
            "mode": "RULE_BASED_V1",
            "temporary": False,
            "headline": "今日市場重點尚未完成",
            "bullets": [],
            "dataDate": None,
            "source": DAILY_FOCUS_SOURCE,
            "reasonCode": "DAILY_FOCUS_EVIDENCE_INCOMPLETE",
            "userMessage": USER_MESSAGES["DAILY_FOCUS_EVIDENCE_INCOMPLETE"],
        },
        "mainTopics": [],
        "marketPulse": [],
        "heatingTopics": [],
        "coolingTopics": [],
        "opportunities": [],
        "sectionStatuses": statuses,
        "dataQuality": {
            "status": "UNAVAILABLE",
            "source": HOME_SOURCE,
            "classification": "FORMAL",
            "temporarySections": ["marketEvents", "opportunities"],
            "missingSections": [key for key in SECTION_KEYS if statuses[key]["status"] == "UNAVAILABLE"],
            "notes": [],
            "diagnosticCodes": {
                key: statuses[key]["reasonCode"] for key in SECTION_KEYS
            },
        },
    }


__all__ = [
    "DAILY_FOCUS_SOURCE",
    "HOME_PUBLICATION_VERSION",
    "MarketTurnoverFact",
    "build_daily_focus",
    "calculate_rotation_14d",
    "empty_home_v2",
    "materialize_home_v2",
    "rank_formal_topics",
    "read_latest_home_publication",
    "validate_home_gate",
]
