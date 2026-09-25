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
from decimal import Decimal, InvalidOperation
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

MARKET_DISTRIBUTION_SOURCE = "topicpilot.vw_daily_market_observations"
_NO_TRADE_STATUS_CODES = frozenset(
    {"SUSPENDED", "NO_TRADE", "EXCHANGE_CONFIRMED_NO_DATA", "DELISTED", "TERMINATED"}
)
MARKET_DISTRIBUTION_BUCKETS = (
    ("PCT_GE_10", "漲幅 ≥10%（未確認漲停）"),
    ("PCT_7_TO_10", "漲幅 7% 至未滿 10%"),
    ("PCT_3_TO_7", "漲幅 3% 至未滿 7%"),
    ("PCT_0_TO_3", "漲幅 0% 至未滿 3%"),
    ("FLAT", "平盤"),
    ("PCT_NEG_0_TO_3", "跌幅 0% 至未滿 3%"),
    ("PCT_NEG_3_TO_7", "跌幅 3% 至未滿 7%"),
    ("PCT_NEG_7_TO_10", "跌幅 7% 至未滿 10%"),
    ("PCT_LE_NEG_10", "跌幅 ≥10%（未確認跌停）"),
)

MARKET_SIGNAL_CATALOG = (
    {
        "key": "INDEX_DIVERGENCE",
        "name": "大型股／中小型股分化",
        "condition": "TSE 與 TWO 報酬方向相反",
        "direction": "Neutral / Watch",
        "description": "大型股與中小型股走勢分歧。",
    },
    {
        "key": "OTC_VOLUME_PRICE_DIVERGENCE",
        "name": "櫃買量價背離",
        "condition": "TWO 下跌且上櫃成交金額較前一交易日增加",
        "direction": "Bearish / Warning",
        "description": "中小型股成交熱度升高但價格走弱。",
    },
    {
        "key": "INSTITUTION_PRICE_DIVERGENCE",
        "name": "法人與價格背離",
        "condition": "指數上漲且外資淨賣超",
        "direction": "Watch",
        "description": "價格與外資籌碼方向不一致。",
    },
    {
        "key": "BREADTH_DIVERGENCE",
        "name": "市場廣度背離",
        "condition": "指數上漲且下跌家數高於上漲家數",
        "direction": "Watch",
        "description": "指數上漲但市場參與度不足。",
    },
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


def _signal_change_text(item: Mapping[str, Any], label: str) -> str:
    change = item.get("change")
    if not isinstance(change, (int, float)) or isinstance(change, bool):
        return f"{label}漲跌點尚未提供"
    change_text = f"{change:+g} 點"
    change_pct = item.get("changePct")
    if isinstance(change_pct, (int, float)) and not isinstance(change_pct, bool):
        change_text += f"（{change_pct:+g}%）"
    return f"{label} {change_text}"


def build_market_signals(market_overview: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return only triggered signals from formal, published market facts."""

    health = market_overview.get("marketHealth") or {}
    formal_statuses = {"AVAILABLE", "PUBLISHED", "FORMAL"}
    indices = {
        str(item.get("market")): item
        for item in market_overview.get("indices") or []
        if isinstance(item, Mapping)
        and str(item.get("status") or "").upper() in formal_statuses
        and isinstance(item.get("change"), (int, float))
        and not isinstance(item.get("change"), bool)
    }
    signals: list[dict[str, Any]] = []
    tpe = indices.get("TPE")
    two = indices.get("TWO")
    if tpe is not None and two is not None:
        tpe_change = tpe["change"]
        two_change = two["change"]
        if (tpe_change > 0 and two_change < 0) or (tpe_change < 0 and two_change > 0):
            signals.append(
                {
                    "key": "INDEX_DIVERGENCE",
                    "name": "大型股／中小型股分化",
                    "severity": "WATCH",
                    "direction": "Neutral",
                    "evidence": [
                        _signal_change_text(tpe, "加權指數"),
                        _signal_change_text(two, "櫃買指數"),
                    ],
                    "interpretation": "大型股與中小型股走勢明顯分化。",
                }
            )

    turnover = {
        str(item.get("market")): item
        for item in market_overview.get("turnover") or []
        if isinstance(item, Mapping)
    }
    two_turnover = turnover.get("TWO")
    two_change_pct = two_turnover.get("changePct") if isinstance(two_turnover, Mapping) else None
    if (
        two is not None
        and two["change"] < 0
        and two_turnover is not None
        and str(two_turnover.get("status") or "").upper() in formal_statuses
        and isinstance(two_change_pct, (int, float))
        and not isinstance(two_change_pct, bool)
        and two_change_pct > 0
    ):
        signals.append(
            {
                "key": "OTC_VOLUME_PRICE_DIVERGENCE",
                "name": "櫃買量價背離",
                "severity": "WARNING",
                "direction": "Bearish",
                "evidence": [
                    _signal_change_text(two, "櫃買指數"),
                    f"上櫃成交金額 {two_change_pct:+g}%（較前一交易日）",
                ],
                "interpretation": "中小型股成交熱度升高但價格走弱。",
            }
        )

    institution_flows = market_overview.get("institutionFlows")
    tpe_flow = None
    if isinstance(institution_flows, Mapping) and isinstance(institution_flows.get("markets"), list):
        tpe_flow = next(
            (
                item
                for item in institution_flows["markets"]
                if isinstance(item, Mapping) and item.get("market") == "TPE"
            ),
            None,
        )
    current = tpe_flow.get("current") if isinstance(tpe_flow, Mapping) else None
    foreign = current.get("foreign") if isinstance(current, Mapping) else None
    foreign_value = foreign.get("value") if isinstance(foreign, Mapping) else None
    foreign_status = str(foreign.get("status") or "").upper() if isinstance(foreign, Mapping) else ""
    if (
        tpe is not None
        and tpe["change"] > 0
        and foreign_status in formal_statuses
        and isinstance(foreign_value, (int, float))
        and not isinstance(foreign_value, bool)
        and foreign_value < 0
    ):
        signals.append(
            {
                "key": "INSTITUTION_PRICE_DIVERGENCE",
                "name": "法人與價格背離",
                "severity": "WATCH",
                "direction": "Watch",
                "evidence": [
                    _signal_change_text(tpe, "加權指數"),
                    f"外資淨賣超 {foreign_value:g}",
                ],
                "interpretation": "價格與外資籌碼方向不一致。",
            }
        )

    advance = health.get("advance")
    decline = health.get("decline")
    if (
        tpe is not None
        and tpe["change"] > 0
        and str(health.get("status") or "").upper() in formal_statuses
        and isinstance(advance, int)
        and isinstance(decline, int)
        and decline > advance
    ):
        signals.append(
            {
                "key": "BREADTH_DIVERGENCE",
                "name": "市場廣度背離",
                "severity": "WATCH",
                "direction": "Watch",
                "evidence": [
                    _signal_change_text(tpe, "加權指數"),
                    f"上漲家數 {advance}、下跌家數 {decline}",
                ],
                "interpretation": "指數上漲但市場參與度不足。",
            }
        )
    return signals


def build_daily_focus(
    *,
    market_overview: Mapping[str, Any],
    main_topics: Sequence[Mapping[str, Any]],
    heating_topics: Sequence[Mapping[str, Any]],
    cooling_topics: Sequence[Mapping[str, Any]],
    data_date: date | None,
    as_of: datetime | None,
) -> SectionResult:
    """Build formal market signals from published facts only."""

    has_market_evidence = bool(
        (market_overview.get("indices") or [])
        or (market_overview.get("turnover") or [])
        or (market_overview.get("breadth") or [])
        or (market_overview.get("marketHealth") or {}).get("breadthEligible")
    )
    signal_catalog = [dict(item) for item in MARKET_SIGNAL_CATALOG]
    signals = build_market_signals(market_overview) if has_market_evidence else []
    if not has_market_evidence:
        return _status(
            "UNAVAILABLE",
            data_date=data_date,
            as_of=as_of,
            source=DAILY_FOCUS_SOURCE,
            reason_code="DAILY_FOCUS_EVIDENCE_INCOMPLETE",
            detail="formal Home inputs did not contain a meaningful market fact",
            payload={
                "mode": "RULE_BASED_V1",
                "temporary": False,
                "headline": "今日市場訊號尚未完成",
                "bullets": [],
                "signals": [],
                "signalCatalog": signal_catalog,
                "dataDate": data_date,
                "source": DAILY_FOCUS_SOURCE,
                "reasonCode": "DAILY_FOCUS_EVIDENCE_INCOMPLETE",
                "userMessage": USER_MESSAGES["DAILY_FOCUS_EVIDENCE_INCOMPLETE"],
            },
        )
    headline = signals[0]["name"] if signals else "今日無異常訊號"
    return _status(
        "AVAILABLE",
        data_date=data_date,
        as_of=as_of,
        source=DAILY_FOCUS_SOURCE,
        payload={
            "mode": "RULE_BASED_V1",
            "temporary": False,
            "headline": headline,
            "bullets": [item["interpretation"] for item in signals[:4]] or ["目前沒有符合正式規則的市場訊號。"],
            "signals": signals,
            "signalCatalog": signal_catalog,
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


def _distribution_bucket(change_pct: Decimal) -> str:
    if change_pct >= Decimal("10"):
        return "PCT_GE_10"
    if change_pct >= Decimal("7"):
        return "PCT_7_TO_10"
    if change_pct >= Decimal("3"):
        return "PCT_3_TO_7"
    if change_pct > 0:
        return "PCT_0_TO_3"
    if change_pct == 0:
        return "FLAT"
    if change_pct > Decimal("-3"):
        return "PCT_NEG_0_TO_3"
    if change_pct > Decimal("-7"):
        return "PCT_NEG_3_TO_7"
    if change_pct > Decimal("-10"):
        return "PCT_NEG_7_TO_10"
    return "PCT_LE_NEG_10"


def build_market_distribution(
    observations: Iterable[Mapping[str, Any]],
    *,
    eligible_count: int,
    as_of: datetime | None,
    source: str = MARKET_DISTRIBUTION_SOURCE,
) -> dict[str, Any]:
    """Aggregate canonical EOD observations without turning missing data into 0%."""

    counts = {key: 0 for key, _label in MARKET_DISTRIBUTION_BUCKETS}
    for row in observations:
        if row.get("instrument_id") is None:
            continue
        if str(row.get("status_code") or "UNKNOWN").upper() in _NO_TRADE_STATUS_CODES:
            continue
        try:
            close = Decimal(str(row.get("close")))
            previous_close = Decimal(str(row.get("previous_close")))
        except (InvalidOperation, TypeError, ValueError):
            continue
        if not close.is_finite() or not previous_close.is_finite() or previous_close <= 0:
            continue
        change_pct = (close - previous_close) / previous_close * Decimal("100")
        counts[_distribution_bucket(change_pct)] += 1

    eligible = sum(counts.values())
    return {
        "market": "TPE+TWO",
        "status": "AVAILABLE" if eligible else "UNAVAILABLE",
        "eligible": eligible,
        "excluded": max(0, int(eligible_count) - eligible),
        "buckets": [
            {"key": key, "label": label, "count": counts[key]}
            for key, label in MARKET_DISTRIBUTION_BUCKETS
        ],
        "coverage": {
            "denominator": "active date-effective EQUITY instruments in TPE/TWO",
            "eligibleUniverse": int(eligible_count),
            "percentageEligible": round(eligible / int(eligible_count) * 100, 4)
            if int(eligible_count)
            else 0,
        },
        "asOf": as_of,
        "source": source,
        "reasonCode": None if eligible else "NO_PERCENT_CHANGE_OBSERVATIONS",
    }


def _breadth(
    session: Session, trading_date: date
) -> tuple[list[dict[str, Any]], datetime | None, list[dict[str, Any]]]:
    observations = [
        dict(row)
        for row in session.execute(
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
                ), current_observations AS (
                    SELECT DISTINCT ON (current.instrument_id)
                        current.instrument_id, current.close, current.status_code,
                        current.observed_at, previous.close AS previous_close
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
                SELECT u.market, u.id AS universe_instrument_id,
                       o.instrument_id, o.close, o.previous_close,
                       o.status_code, o.observed_at
                FROM universe u
                LEFT JOIN current_observations o ON o.instrument_id = u.id
                ORDER BY u.market, u.id
                """
            ),
            {"trading_date": trading_date},
        ).mappings().all()
    ]
    aggregate: dict[str, dict[str, Any]] = {}
    for row in observations:
        market = str(row["market"])
        item = aggregate.setdefault(
            market,
            {
                "market": market,
                "eligible": 0,
                "observed": 0,
                "priced": 0,
                "advance": 0,
                "decline": 0,
                "flat": 0,
                "unavailable": 0,
                "as_of": None,
            },
        )
        item["eligible"] += 1
        if row["instrument_id"] is None:
            continue
        item["observed"] += 1
        if row["observed_at"] is not None and (
            item["as_of"] is None or row["observed_at"] > item["as_of"]
        ):
            item["as_of"] = row["observed_at"]
        status_code = str(row["status_code"] or "UNKNOWN").upper()
        if status_code in _NO_TRADE_STATUS_CODES:
            item["unavailable"] += 1
            continue
        if row["close"] is not None and row["close"] > 0:
            item["priced"] += 1
        if row["close"] is not None and row["previous_close"] is not None:
            if row["close"] > row["previous_close"]:
                item["advance"] += 1
            elif row["close"] < row["previous_close"]:
                item["decline"] += 1
            else:
                item["flat"] += 1
    as_of = max(
        (row["as_of"] for row in aggregate.values() if row["as_of"] is not None),
        default=None,
    )
    return [aggregate[key] for key in sorted(aggregate)], as_of, observations


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
                  AND NOT EXISTS (
                      SELECT 1 FROM topicpilot.topic_snapshots successor
                      WHERE successor.supersedes_snapshot_id = topic_snapshots.id
                  )
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
                  AND NOT EXISTS (
                      SELECT 1 FROM topicpilot.topic_snapshots successor
                      WHERE successor.supersedes_snapshot_id = topic_snapshots.id
                  )
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


def _derived_total_turnover(
    turnover: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Derive a total only from two matching formal TWD close facts."""

    by_market = {str(item.get("market")): item for item in turnover}
    records = [by_market.get("TPE"), by_market.get("TWO")]
    if any(item is None for item in records):
        return None
    if any(
        str(item.get("status") or "").upper() not in {"AVAILABLE", "PUBLISHED", "FORMAL"}
        for item in records
    ):
        return None
    if {str(item.get("currency") or "").strip().upper() for item in records} != {"TWD"}:
        return None
    if {str(item.get("unit") or "").strip().upper() for item in records} != {"TWD"}:
        return None
    if {item.get("scale") for item in records} != {0}:
        return None
    try:
        values = [Decimal(str(item["value"])) for item in records]
    except (KeyError, InvalidOperation, TypeError, ValueError):
        return None
    if any(not value.is_finite() for value in values):
        return None
    first = records[0]
    return {
        "market": "TOTAL",
        "tradingDate": first.get("tradingDate"),
        "session": first.get("session", "CLOSE"),
        "value": _number(values[0] + values[1]),
        "currency": "TWD",
        "unit": "TWD",
        "scale": 0,
        "asOf": max((item.get("asOf") for item in records if item.get("asOf")), default=None),
        "source": "HOME_V2_FORMAL_TURNOVER_TOTAL",
        "lineage": "deterministic sum of matching TPE/TWO formal close facts",
        "status": "AVAILABLE",
        "reasonCode": None,
    }


def _as_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def normalize_home_publication_for_read(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Rebuild persisted Daily Focus from the current formal market facts."""

    result = dict(payload)
    market_overview = result.get("marketOverview")
    if not isinstance(market_overview, Mapping):
        return result
    overview = dict(market_overview)
    health = overview.get("marketHealth")
    if isinstance(health, Mapping):
        health_copy = dict(health)
        advance = health_copy.get("advance")
        decline = health_copy.get("decline")
        flat = health_copy.get("flat")
        if (
            isinstance(advance, (int, float))
            and not isinstance(advance, bool)
            and isinstance(decline, (int, float))
            and not isinstance(decline, bool)
        ):
            health_copy["net"] = advance - decline
            if (
                isinstance(flat, (int, float))
                and not isinstance(flat, bool)
                and health_copy.get("breadthEligible") is None
            ):
                health_copy["breadthEligible"] = advance + decline + flat
            overview["marketHealth"] = health_copy
    turnover = overview.get("turnover")
    if isinstance(turnover, list) and not any(
        isinstance(item, Mapping) and item.get("market") == "TOTAL" for item in turnover
    ):
        total_turnover = _derived_total_turnover(
            [item for item in turnover if isinstance(item, Mapping)]
        )
        if total_turnover is not None:
            overview["turnover"] = [*turnover, total_turnover]
    result["marketOverview"] = overview

    data_date = _as_date(
        overview.get("dataDate")
        or (result.get("publication") or {}).get("tradingDate")
        or result.get("asOf")
    )
    as_of = _as_datetime(
        overview.get("updatedAt")
        or overview.get("latestSnapshotTime")
        or (result.get("publication") or {}).get("asOf")
    )
    normalized = build_daily_focus(
        market_overview=overview,
        main_topics=(),
        heating_topics=(),
        cooling_topics=(),
        data_date=data_date,
        as_of=as_of,
    )
    result["dailyFocus"] = normalized.payload
    statuses = result.get("sectionStatuses")
    if isinstance(statuses, Mapping):
        result["sectionStatuses"] = {
            **statuses,
            "dailyFocus": normalized.status_payload(),
        }
    publication = result.get("publication")
    if isinstance(publication, Mapping) and isinstance(publication.get("completeness"), Mapping):
        publication_copy = dict(publication)
        publication_copy["completeness"] = {
            **publication["completeness"],
            "sectionStatuses": result.get("sectionStatuses", statuses),
        }
        result["publication"] = publication_copy
    return result


def _flow_leg(row: Mapping[str, Any], prefix: str) -> dict[str, Any] | None:
    net = row.get(f"{prefix}_net")
    if net is None:
        return None
    return {
        "buy": _number(row.get(f"{prefix}_buy")),
        "sell": _number(row.get(f"{prefix}_sell")),
        "net": _number(net),
        "value": _number(net),
        "unit": row.get("unit") or "TWD",
        "scale": int(row.get("scale") or 0),
        "status": row.get("availability") or "UNKNOWN",
    }


def _flow_daily_payload(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "market": row.get("market"),
        "tradingDate": row.get("trading_date"),
        "foreign": _flow_leg(row, "foreign"),
        "investmentTrust": _flow_leg(row, "investment_trust"),
        "dealer": _flow_leg(row, "dealer"),
        "total": _flow_leg(row, "total"),
        "sourceProvider": row.get("source_provider"),
        "sourceIdentity": row.get("source_identity"),
        "sourceDataset": row.get("source_dataset"),
        "sourceEndpoint": row.get("source_endpoint"),
        "adapterVersion": row.get("adapter_version"),
        "sourceAsOf": row.get("source_as_of"),
        "publishedAt": row.get("published_at"),
        "retrievedAt": row.get("retrieved_at"),
        "availability": row.get("availability") or "UNKNOWN",
        "freshness": row.get("freshness") or "UNKNOWN",
        "statusReason": row.get("status_reason"),
        "lineage": row.get("lineage") or "formal market institutional flow table",
        "responseContentHash": row.get("response_content_hash"),
    }


def _read_home_institutional_flow(
    session: Session, trading_date: date | None
) -> dict[str, Any] | None:
    if trading_date is None:
        return None
    try:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT DISTINCT ON (market)
                           market, trading_date, source_provider, source_identity,
                           source_dataset, source_endpoint, adapter_version,
                           source_as_of, published_at, retrieved_at, unit, scale,
                           foreign_buy, foreign_sell, foreign_net,
                           investment_trust_buy, investment_trust_sell, investment_trust_net,
                           dealer_buy, dealer_sell, dealer_net,
                           total_buy, total_sell, total_net,
                           availability, freshness, status_reason, lineage,
                           response_content_hash
                    FROM topicpilot.market_institutional_flow_daily
                    WHERE trading_date <= :trading_date
                    ORDER BY market, trading_date DESC, source_as_of DESC NULLS LAST,
                             published_at DESC NULLS LAST, id DESC
                    """
                ),
                {"trading_date": trading_date},
            ).mappings()
        ]
    except SQLAlchemyError:
        session.rollback()
        return None
    if not rows:
        return None

    markets: list[dict[str, Any]] = []
    for row in rows:
        current = _flow_daily_payload(row)
        availability = str(row.get("availability") or "UNKNOWN")
        market = str(row.get("market") or "")
        markets.append(
            {
                "market": market,
                "asOfDate": row.get("trading_date"),
                "availability": availability,
                "freshness": row.get("freshness") or "UNKNOWN",
                "current": current,
                "previous": None,
                "rolling5Session": {
                    "requiredSessions": 5,
                    "observedSessions": 1,
                    "complete": False,
                    "foreignNet": None,
                    "investmentTrustNet": None,
                    "dealerNet": None,
                    "totalNet": None,
                    "unit": row.get("unit") or "TWD",
                    "scale": int(row.get("scale") or 0),
                },
                "rolling20Session": {
                    "requiredSessions": 20,
                    "observedSessions": 1,
                    "complete": False,
                    "foreignNet": None,
                    "investmentTrustNet": None,
                    "dealerNet": None,
                    "totalNet": None,
                    "unit": row.get("unit") or "TWD",
                    "scale": int(row.get("scale") or 0),
                },
                "streaks": {},
                "acceleration": {},
                "priceFlowRelation": {
                    "market": market,
                    "indexChange": None,
                    "flowNet": _number(row.get("total_net")),
                    "marketDirection": "UNKNOWN",
                    "flowDirection": "UNKNOWN",
                    "directionRelation": "UNKNOWN",
                    "availability": availability,
                },
                "sourceAsOf": row.get("source_as_of"),
                "source": row.get("source_provider"),
                "statusReason": row.get("status_reason"),
            }
        )
    available = [item for item in markets if item["availability"] == "AVAILABLE"]
    status = "AVAILABLE" if len(available) == len(markets) else "PARTIAL" if available else "UNAVAILABLE"
    freshness_values = {str(item.get("freshness") or "UNKNOWN") for item in markets}
    freshness = "CURRENT" if freshness_values == {"CURRENT"} else "STALE" if "STALE" in freshness_values else "UNKNOWN"
    return {
        "contractVersion": "market-institutional-flow.formal.v1",
        "asOfDate": max((item.get("asOfDate") for item in markets if item.get("asOfDate")), default=None),
        "status": status,
        "freshness": freshness,
        "markets": markets,
        "sourceAsOf": max((item.get("sourceAsOf") for item in markets if item.get("sourceAsOf")), default=None),
        "source": ";".join(sorted({str(row.get("source_provider")) for row in rows if row.get("source_provider")})) or None,
        "unit": rows[0].get("unit") or "TWD",
        "scale": int(rows[0].get("scale") or 0),
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
    breadth_observations: list[dict[str, Any]] = []
    distribution_as_of: datetime | None = None
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
        try:
            _canonical_rows, distribution_as_of, breadth_observations = _breadth(session, trading_date)
        except SQLAlchemyError:
            session.rollback()
    else:
        breadth_rows, breadth_as_of, breadth_observations = _breadth(session, trading_date)
        distribution_as_of = breadth_as_of
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
    advance = sum(int(item.get("advance") or 0) for item in breadth_payload)
    decline = sum(int(item.get("decline") or 0) for item in breadth_payload)
    flat = sum(int(item.get("flat") or 0) for item in breadth_payload)
    breadth_eligible = advance + decline + flat

    def _percentage(value: int) -> float | None:
        return round(value / breadth_eligible * 100, 4) if breadth_eligible else None

    distribution_payload = build_market_distribution(
        breadth_observations,
        eligible_count=total_eligible,
        as_of=distribution_as_of,
    )
    market_health = {
        "market": "TPE+TWO",
        "status": "AVAILABLE" if total_observed else "UNAVAILABLE",
        "totalStocks": total_eligible,
        "observed": total_observed,
        "breadthEligible": breadth_eligible,
        "advance": advance,
        "decline": decline,
        "flat": flat,
        "net": advance - decline if breadth_eligible else None,
        "advancePct": _percentage(advance),
        "declinePct": _percentage(decline),
        "flatPct": _percentage(flat),
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
    total_turnover = _derived_total_turnover(turnover)
    if total_turnover is not None:
        turnover.append(total_turnover)
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
        "institutionFlows": None,
        "breadth": breadth_payload,
        "distribution": distribution_payload,
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
    if not row:
        return None
    payload = dict(row["payload"])
    market_overview = payload.get("marketOverview")
    if isinstance(market_overview, Mapping):
        enriched_overview = dict(market_overview)
        trading_date = _as_date(enriched_overview.get("dataDate"))
        if not enriched_overview.get("institutionFlows"):
            flow_payload = _read_home_institutional_flow(session, trading_date)
            if flow_payload is not None:
                enriched_overview["institutionFlows"] = flow_payload
        if not enriched_overview.get("distribution") and trading_date is not None:
            try:
                breadth_rows, breadth_as_of, observations = _breadth(session, trading_date)
                eligible_count = sum(int(item.get("eligible") or 0) for item in breadth_rows)
                enriched_overview["distribution"] = build_market_distribution(
                    observations,
                    eligible_count=eligible_count,
                    as_of=breadth_as_of,
                )
            except SQLAlchemyError:
                session.rollback()
        payload["marketOverview"] = enriched_overview
    return normalize_home_publication_for_read(payload)


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
            "institutionFlows": None,
            "breadth": [],
            "distribution": None,
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
    "MARKET_DISTRIBUTION_BUCKETS",
    "MARKET_DISTRIBUTION_SOURCE",
    "MARKET_SIGNAL_CATALOG",
    "MarketTurnoverFact",
    "build_daily_focus",
    "build_market_distribution",
    "build_market_signals",
    "calculate_rotation_14d",
    "empty_home_v2",
    "materialize_home_v2",
    "normalize_home_publication_for_read",
    "rank_formal_topics",
    "read_latest_home_publication",
    "validate_home_gate",
]
