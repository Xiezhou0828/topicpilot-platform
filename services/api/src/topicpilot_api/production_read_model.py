"""Formal V2 Stock and Topic read models.

This module is deliberately read-only.  It composes the V2 identity, relation,
tracking, canonical observation, and topic snapshot tables without borrowing
the legacy public demo tables or inferring business semantics in the client.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from topicpilot_api.orm import TopicLifecycleResult
from topicpilot_api.problems import NotFoundProblem
from topicpilot_api.topic_lifecycle_engine import LIFECYCLE_POLICY_VERSION

TAIPEI = ZoneInfo("Asia/Taipei")
VALID_MARKETS = {"TPE", "TWO"}
VALID_UPDATE_MODES = {"INTRADAY", "POST_CLOSE", "UNKNOWN"}
VALID_SORTS = {"symbolAsc", "changePctDesc", "priceDesc", "volumeDesc"}
ROLE_VALUES = {"代表股", "核心股", "關聯股", "PRIMARY", "REPRESENTATIVE", "LEADER", "CORE", "SECONDARY", "RELATED"}


STOCK_ROWS_SQL = text(
    """
    WITH universe AS (
        SELECT i.id AS instrument_id, i.instrument_code, i.name, i.is_active,
               m.code AS market_code, m.exchange_code, m.name AS market_name,
               ltu.update_mode, ltu.moving_average_state, ltu.latest_close AS tracking_close,
               ltu.moving_average, ltu.moving_average_period, ltu.observation_count,
               ltu.reference_observed_at, ltu.as_of_date, ltu.classification_reason
        FROM topicpilot.instruments i
        JOIN topicpilot.markets m ON m.id = i.market_id
        LEFT JOIN topicpilot.live_tracking_universe ltu ON ltu.instrument_id = i.id
        WHERE i.is_active = true
          AND i.instrument_type = 'EQUITY'
          AND m.is_active = true
          AND m.code IN ('TPE', 'TWO')
          AND (CAST(:market_code AS text) IS NULL OR m.code = CAST(:market_code AS text))
          AND (CAST(:update_mode AS text) IS NULL OR COALESCE(ltu.update_mode, 'UNKNOWN') = CAST(:update_mode AS text))
    ),
    daily_price_by_day AS (
        SELECT co.instrument_id,
               (co.observed_at AT TIME ZONE 'Asia/Taipei')::date AS trading_date,
               cp.close, co.observed_at, co.retrieved_at,
               ROW_NUMBER() OVER (
                   PARTITION BY co.instrument_id, (co.observed_at AT TIME ZONE 'Asia/Taipei')::date
                   ORDER BY co.observed_at DESC, co.retrieved_at DESC, co.id DESC
               ) AS same_day_rank
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_price_observations cp
          ON cp.canonical_observation_id = co.id
        JOIN topicpilot.market_data_sources src ON src.id = co.source_id
        WHERE co.family_code = 'PRICE'
          AND co.quality_state = 'ACCEPTED'
          AND src.observation_semantics = 'DAILY_BAR'
    ),
    daily_price_ranked AS (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY instrument_id ORDER BY trading_date DESC, observed_at DESC, retrieved_at DESC
        ) AS date_rank
        FROM daily_price_by_day
        WHERE same_day_rank = 1
    ),
    daily AS (
        SELECT current_row.instrument_id,
               current_row.close AS daily_close,
               previous_row.close AS previous_daily_close,
               current_row.trading_date AS daily_date,
               current_row.observed_at AS daily_observed_at,
               current_row.retrieved_at AS daily_retrieved_at
        FROM daily_price_ranked current_row
        LEFT JOIN daily_price_ranked previous_row
          ON previous_row.instrument_id = current_row.instrument_id
         AND previous_row.date_rank = 2
        WHERE current_row.date_rank = 1
    ),
    intraday AS (
        SELECT co.instrument_id, cp.close AS intraday_close, co.observed_at AS intraday_observed_at,
               co.retrieved_at AS intraday_retrieved_at,
               ROW_NUMBER() OVER (
                   PARTITION BY co.instrument_id ORDER BY co.observed_at DESC, co.retrieved_at DESC, co.id DESC
               ) AS row_rank
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_price_observations cp
          ON cp.canonical_observation_id = co.id
        JOIN topicpilot.market_data_sources src ON src.id = co.source_id
        WHERE co.family_code = 'PRICE'
          AND co.quality_state = 'ACCEPTED'
          AND src.observation_semantics = 'INTRADAY_BAR'
    ),
    daily_volume_by_day AS (
        SELECT co.instrument_id,
               (co.observed_at AT TIME ZONE 'Asia/Taipei')::date AS trading_date,
               cv.volume_quantity,
               ROW_NUMBER() OVER (
                   PARTITION BY co.instrument_id, (co.observed_at AT TIME ZONE 'Asia/Taipei')::date
                   ORDER BY co.observed_at DESC, co.retrieved_at DESC, co.id DESC
               ) AS same_day_rank
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_volume_observations cv
          ON cv.canonical_observation_id = co.id
        JOIN topicpilot.market_data_sources src ON src.id = co.source_id
        WHERE co.family_code = 'VOLUME'
          AND co.quality_state = 'ACCEPTED'
          AND src.observation_semantics = 'DAILY_BAR'
    ),
    daily_volume AS (
        SELECT instrument_id, volume_quantity,
               ROW_NUMBER() OVER (PARTITION BY instrument_id ORDER BY trading_date DESC) AS date_rank
        FROM daily_volume_by_day
        WHERE same_day_rank = 1
    ),
    intraday_volume AS (
        SELECT co.instrument_id, cv.volume_quantity,
               ROW_NUMBER() OVER (
                   PARTITION BY co.instrument_id ORDER BY co.observed_at DESC, co.retrieved_at DESC, co.id DESC
               ) AS row_rank
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_volume_observations cv
          ON cv.canonical_observation_id = co.id
        JOIN topicpilot.market_data_sources src ON src.id = co.source_id
        WHERE co.family_code = 'VOLUME'
          AND co.quality_state = 'ACCEPTED'
          AND src.observation_semantics = 'INTRADAY_BAR'
    )
    SELECT u.*, d.daily_close, d.previous_daily_close, d.daily_date, d.daily_observed_at,
           d.daily_retrieved_at, intr.intraday_close, intr.intraday_observed_at,
           intr.intraday_retrieved_at, dv.volume_quantity AS daily_volume,
           iv.volume_quantity AS intraday_volume
    FROM universe u
    LEFT JOIN daily d ON d.instrument_id = u.instrument_id
    LEFT JOIN intraday intr ON intr.instrument_id = u.instrument_id AND intr.row_rank = 1
    LEFT JOIN daily_volume dv ON dv.instrument_id = u.instrument_id AND dv.date_rank = 1
    LEFT JOIN intraday_volume iv ON iv.instrument_id = u.instrument_id AND iv.row_rank = 1
    ORDER BY u.market_code, u.instrument_code
    """
)

TOPIC_RELATIONS_SQL = text(
    """
    SELECT r.instrument_id, t.id AS topic_id, t.slug AS topic_slug, t.name AS topic_name,
           r.relation_type, r.relationship_metadata,
           CASE
             WHEN COALESCE(r.relationship_metadata ->> 'topicRole', r.relationship_metadata ->> 'role') IN
                  ('代表股', 'PRIMARY', 'REPRESENTATIVE', 'LEADER') THEN '代表股'
             WHEN COALESCE(r.relationship_metadata ->> 'topicRole', r.relationship_metadata ->> 'role') IN
                  ('核心股', 'CORE', 'SECONDARY') THEN '核心股'
             WHEN COALESCE(r.relationship_metadata ->> 'topicRole', r.relationship_metadata ->> 'role') IN
                  ('關聯股', 'RELATED') THEN '關聯股'
             ELSE NULL
           END AS topic_role,
           CASE
             WHEN (r.relationship_metadata ->> 'relationWeight') ~ '^-?[0-9]+(\\.[0-9]+)?$'
               THEN (r.relationship_metadata ->> 'relationWeight')::numeric
             WHEN (r.relationship_metadata ->> 'weight') ~ '^-?[0-9]+(\\.[0-9]+)?$'
               THEN (r.relationship_metadata ->> 'weight')::numeric
             ELSE NULL
           END AS relation_weight
    FROM topicpilot.instrument_topic_relations r
    JOIN topicpilot.topics t ON t.id = r.topic_id
    WHERE r.valid_from <= :as_of_date
      AND (r.valid_to IS NULL OR r.valid_to >= :as_of_date)
      AND t.status NOT IN ('DISABLED', 'RETIRED')
    ORDER BY r.instrument_id, t.slug
    """
)

TOPIC_ROWS_SQL = text(
    """
    WITH latest AS (
        SELECT DISTINCT ON (topic_id) *
        FROM topicpilot.topic_snapshots
        ORDER BY topic_id, snapshot_date DESC, updated_at DESC
    )
    SELECT t.id AS topic_id, t.slug, t.name, t.description, t.status, t.display_metadata,
           parent.name AS parent_name, latest.snapshot_date, latest.market_grade,
           latest.topic_score, latest.topic_direction, latest.stock_count,
           latest.observed_stock_count, latest.coverage_pct, latest.data_status,
           latest.score_status
    FROM topicpilot.topics t
    LEFT JOIN LATERAL (
        SELECT p.name
        FROM topicpilot.topic_hierarchy h
        JOIN topicpilot.topics p ON p.id = h.parent_topic_id
        WHERE h.child_topic_id = t.id
          AND h.valid_from <= :as_of_date
          AND (h.valid_to IS NULL OR h.valid_to >= :as_of_date)
        ORDER BY h.display_order NULLS LAST, p.slug
        LIMIT 1
    ) parent ON true
    LEFT JOIN latest ON latest.topic_id = t.id
    WHERE t.status NOT IN ('DISABLED', 'RETIRED')
      AND (CAST(:slug AS text) IS NULL OR t.slug = CAST(:slug AS text))
    ORDER BY t.slug
    """
)


def _float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _date_now() -> date:
    return datetime.now(TAIPEI).date()


def _freshness(update_mode: str, has_price: bool) -> str:
    if not has_price or update_mode == "UNKNOWN":
        return "資料待更新"
    return "盤中更新" if update_mode == "INTRADAY" else "盤後更新"


def _read_relations(session: Session, as_of_date: date) -> dict[str, list[dict[str, Any]]]:
    rows = session.execute(TOPIC_RELATIONS_SQL, {"as_of_date": as_of_date}).mappings()
    result: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        result.setdefault(str(row["instrument_id"]), []).append(
            {
                "topicId": str(row["topic_id"]),
                "topicSlug": row["topic_slug"],
                "topicName": row["topic_name"],
                "topicRole": row["topic_role"],
                "relationType": row["relation_type"],
                "relationWeight": _float(row["relation_weight"]),
            }
        )
    return result


def _stock_item(row: Any, relations: list[dict[str, Any]]) -> dict[str, Any]:
    update_mode = row["update_mode"] or "UNKNOWN"
    daily_close = row["daily_close"]
    intraday_close = row["intraday_close"]
    use_intraday = update_mode == "INTRADAY" and intraday_close is not None
    price_value = intraday_close if use_intraday else daily_close
    observed_at = row["intraday_observed_at"] if use_intraday else row["daily_observed_at"]
    retrieved_at = row["intraday_retrieved_at"] if use_intraday else row["daily_retrieved_at"]
    previous_close = row["previous_daily_close"]
    change_pct = None
    if daily_close is not None and previous_close is not None and previous_close > 0:
        change_pct = (Decimal(daily_close) - Decimal(previous_close)) / Decimal(previous_close) * 100
    tracking_period = row["moving_average_period"]
    tracking_state = row["moving_average_state"] if row["moving_average"] is not None else None
    return {
        "instrumentId": str(row["instrument_id"]),
        "symbol": row["instrument_code"],
        "code": row["instrument_code"],
        "name": row["name"],
        "market": row["market_code"],
        "exchange": row["exchange_code"],
        "listing": row["market_name"],
        "active": bool(row["is_active"]),
        "enabled": bool(row["is_active"]),
        "price": _float(price_value),
        "changePct": _float(change_pct),
        "volume": _float(row["intraday_volume"] if use_intraday and row["intraday_volume"] is not None else row["daily_volume"]),
        "observedAt": observed_at,
        "retrievedAt": retrieved_at,
        "dataFreshness": _freshness(update_mode, price_value is not None),
        "updateMode": update_mode,
        "marketStatus": _freshness(update_mode, price_value is not None),
        "mainTopic": None,
        "topicRelations": relations,
        "trackingMode": update_mode,
        "trackingReason": row["classification_reason"],
        "ma20State": None,
        "ma60State": tracking_state if tracking_period == 60 else None,
        "historyCoverage": {
            "observedDays": int(row["observation_count"] or 0),
            "requiredDays": 60,
            "state": tracking_state or "UNKNOWN",
            "asOfDate": row["as_of_date"],
        },
        "favorite": None,
        "opportunity": None,
        "technicalEvidence": {
            "above20MA": None,
            "above60MA": tracking_state == "ABOVE" if tracking_period == 60 else None,
            "ma20": None,
            "ma60": _float(row["moving_average"]) if tracking_period == 60 else None,
            "breakoutState": None,
            "technicalState": None,
        },
        "institutionFlows": None,
        "summary": None,
    }


def read_stocks(
    session: Session,
    *,
    market: str | None = None,
    topic: str | None = None,
    update_mode: str | None = None,
    sort: str = "symbolAsc",
    limit: int = 1000,
    offset: int = 0,
) -> dict[str, Any]:
    normalized_market = market.upper() if market and market.upper() != "ALL" else None
    normalized_mode = update_mode.upper() if update_mode else None
    if normalized_market and normalized_market not in VALID_MARKETS:
        raise ValueError("market must be ALL, TPE, or TWO")
    if normalized_mode and normalized_mode not in VALID_UPDATE_MODES:
        raise ValueError("updateMode must be INTRADAY, POST_CLOSE, or UNKNOWN")
    if sort not in VALID_SORTS:
        raise ValueError(f"sort must be one of {sorted(VALID_SORTS)}")
    as_of_date = _date_now()
    relation_map = _read_relations(session, as_of_date)
    rows = session.execute(
        STOCK_ROWS_SQL,
        {"market_code": normalized_market, "update_mode": normalized_mode},
    ).mappings()
    all_items = [
        _stock_item(row, relation_map.get(str(row["instrument_id"]), []))
        for row in rows
    ]
    items = all_items
    if topic:
        items = [item for item in items if any(rel["topicSlug"] == topic for rel in item["topicRelations"])]
    if sort == "changePctDesc":
        items.sort(key=lambda item: (item["changePct"] is not None, item["changePct"] or -float("inf")), reverse=True)
    elif sort == "priceDesc":
        items.sort(key=lambda item: (item["price"] is not None, item["price"] or -float("inf")), reverse=True)
    elif sort == "volumeDesc":
        items.sort(key=lambda item: (item["volume"] is not None, item["volume"] or -float("inf")), reverse=True)
    else:
        items.sort(key=lambda item: (item["market"], item["symbol"]))
    total = len(items)
    universe = {
        "total": len(all_items),
        "priced": sum(item["price"] is not None for item in all_items),
        "missingPrice": sum(item["price"] is None for item in all_items),
        "intraday": sum(item["updateMode"] == "INTRADAY" for item in all_items),
        "postClose": sum(item["updateMode"] == "POST_CLOSE" for item in all_items),
        "unknown": sum(item["updateMode"] == "UNKNOWN" for item in all_items),
        "tpe": sum(item["market"] == "TPE" for item in all_items),
        "two": sum(item["market"] == "TWO" for item in all_items),
    }
    return {
        "items": items[offset : offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "query": {"market": normalized_market or "ALL", "topic": topic, "updateMode": normalized_mode or "ALL", "sort": sort},
        "universe": universe,
    }


def read_stock(session: Session, symbol: str) -> dict[str, Any]:
    result = read_stocks(session, sort="symbolAsc", limit=1000)
    item = next((row for row in result["items"] if row["symbol"].upper() == symbol.upper()), None)
    if item is None:
        raise NotFoundProblem(f"Stock {symbol!r} was not found in the formal TPE/TWO universe")
    return item


def _topic_state_label(direction: str | None) -> str:
    return {
        "WARMING": "升溫",
        "COOLING": "降溫",
        "FLAT": "盤整",
    }.get(direction or "", "資料待更新")


def _status_items(topic_row: Any, constituents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if constituents:
        changes = [row["changePct"] for row in constituents if row["changePct"] is not None]
        rising: int | None = sum(value > 0 for value in changes)
        falling: int | None = sum(value < 0 for value in changes)
        flat: int | None = sum(value == 0 for value in changes)
        observed = sum(row["price"] is not None for row in constituents)
        total = len(constituents)
        participation = round(observed * 100 / total, 3) if total else None
    else:
        rising = falling = flat = None
        observed = topic_row["observed_stock_count"] or 0
        total = topic_row["stock_count"] or 0
        participation = _float(topic_row["coverage_pct"])
    direction = topic_row["topic_direction"]
    return [
        {
            "key": "族群表現",
            "state": _topic_state_label(direction),
            "evidence": {
                "observedStockCount": observed,
                "totalStockCount": total,
                "risingCount": rising,
                "fallingCount": falling,
                "flatCount": flat,
                "participationPct": participation,
                "semantic": "TopicSnapshot direction uses average accepted daily close-to-close change.",
            },
        },
        {
            "key": "領漲核心",
            "state": None,
            "evidence": {"status": "NOT_AVAILABLE", "reason": "正式領漲核心判定規則尚未核准。"},
        },
        {
            "key": "動能擴散",
            "state": None,
            "evidence": {"status": "NOT_AVAILABLE", "reason": "正式動能擴散判定規則尚未核准。"},
        },
    ]


def _topic_read_item(
    topic_row: Any,
    constituents: list[dict[str, Any]],
    lifecycle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    direction = topic_row["topic_direction"]
    stock_count = topic_row["stock_count"]
    return {
        "topicId": str(topic_row["topic_id"]),
        "slug": topic_row["slug"],
        "name": topic_row["name"],
        "groupName": topic_row["parent_name"],
        "topicType": "TOPIC",
        "enabled": topic_row["status"] not in {"DISABLED", "RETIRED"},
        "dataDate": topic_row["snapshot_date"],
        "score": _float(topic_row["topic_score"]),
        "grade": topic_row["market_grade"],
        "direction": direction,
        "strengthState": direction,
        "readableState": _topic_state_label(direction),
        "coveragePct": _float(topic_row["coverage_pct"]),
        "constituentCount": int(stock_count if stock_count is not None else len(constituents)),
        "status": _status_items(topic_row, constituents),
        "lifecycle": lifecycle or _lifecycle_unavailable(),
        "constituents": constituents,
    }


def _lifecycle_unavailable() -> dict[str, Any]:
    return {
        "currentStage": None,
        "currentStageEnteredAt": None,
        "currentStageTradingDays": None,
        "history": [],
        "dataStatus": "NOT_AVAILABLE",
        "evaluationDate": None,
        "previousStage": None,
        "candidateStage": None,
        "transitionDecision": None,
        "transitionReason": None,
        "policyVersion": None,
        "evidence": {},
        "confidence": {},
    }


def _read_lifecycle(session: Session, topic_id: Any) -> dict[str, Any]:
    try:
        rows = list(
            session.scalars(
                select(TopicLifecycleResult)
                .where(
                    TopicLifecycleResult.topic_id == topic_id,
                    TopicLifecycleResult.evaluation_mode == "SHADOW",
                    TopicLifecycleResult.policy_version == LIFECYCLE_POLICY_VERSION,
                )
                .order_by(TopicLifecycleResult.evaluation_date)
            )
        )
    except SQLAlchemyError:
        # During additive migration rollout, keep the formal catalog readable
        # while lifecycle remains explicitly unavailable.
        return _lifecycle_unavailable()
    if not rows:
        return _lifecycle_unavailable()
    current = rows[-1]
    segments: list[dict[str, Any]] = []
    for row in rows:
        if row.final_stage is None:
            continue
        if not segments or segments[-1]["stage"] != row.final_stage:
            if segments:
                segments[-1]["exitedAt"] = row.evaluation_date
                segments[-1]["current"] = False
            segments.append(
                {
                    "stage": row.final_stage,
                    "enteredAt": row.stage_entered_at,
                    "exitedAt": None,
                    "tradingDays": row.stage_trading_days,
                    "current": True,
                }
            )
        else:
            segments[-1]["tradingDays"] = row.stage_trading_days
    data_status = (
        "SHADOW_AVAILABLE"
        if current.final_stage is not None and current.data_status == "SHADOW"
        else current.data_status
    )
    latest_evidence = {
        "leadership": current.leadership_evidence or {},
        "diffusion": current.diffusion_evidence or {},
        "groupStrength": current.group_strength_evidence or {},
        "divergenceDecay": current.divergence_decay_evidence or {},
        "persistence": current.persistence_evidence or {},
    }
    return {
        "currentStage": current.final_stage,
        "currentStageEnteredAt": current.stage_entered_at,
        "currentStageTradingDays": current.stage_trading_days,
        "history": segments,
        "dataStatus": data_status,
        "evaluationDate": current.evaluation_date,
        "previousStage": current.previous_stage,
        "candidateStage": current.candidate_stage,
        "transitionDecision": current.transition_decision,
        "transitionReason": current.transition_reason,
        "policyVersion": current.policy_version,
        "evidence": latest_evidence,
        "confidence": current.sample_confidence or {},
    }


def _topic_constituents(session: Session, slug: str, as_of_date: date) -> list[dict[str, Any]]:
    stocks = read_stocks(session, topic=slug, sort="symbolAsc", limit=1000)["items"]
    return [
        {
            "instrumentId": stock["instrumentId"],
            "symbol": stock["symbol"],
            "code": stock["code"],
            "name": stock["name"],
            "role": next((rel["topicRole"] for rel in stock["topicRelations"] if rel["topicSlug"] == slug), None),
            "relationWeight": next((rel["relationWeight"] for rel in stock["topicRelations"] if rel["topicSlug"] == slug), None),
            "price": stock["price"],
            "changePct": stock["changePct"],
            "observedAt": stock["observedAt"],
            "updateMode": stock["updateMode"],
            "freshness": stock["dataFreshness"],
            "technicalState": None,
            "relativeTopicState": None,
        }
        for stock in stocks
    ]


def read_topics(session: Session, *, slug: str | None = None, limit: int = 200, offset: int = 0) -> dict[str, Any]:
    as_of_date = _date_now()
    rows = session.execute(TOPIC_ROWS_SQL, {"as_of_date": as_of_date, "slug": slug}).mappings()
    items = [_topic_read_item(row, [], _read_lifecycle(session, row["topic_id"])) for row in rows]
    total = len(items)
    return {
        "items": items[offset : offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "query": {"slug": slug},
    }


def read_topic(session: Session, slug: str) -> dict[str, Any]:
    as_of_date = _date_now()
    row = session.execute(TOPIC_ROWS_SQL, {"as_of_date": as_of_date, "slug": slug}).mappings().first()
    if row is None:
        raise NotFoundProblem(f"Topic {slug!r} was not found in the formal topic read model")
    constituents = _topic_constituents(session, slug, as_of_date)
    return _topic_read_item(row, constituents, _read_lifecycle(session, row["topic_id"]))


__all__ = ["read_stock", "read_stocks", "read_topic", "read_topics"]
