# ruff: noqa: RUF001
"""PostgreSQL-backed Home Dashboard read model.

This module composes the single Home contract from existing read-model tables.
It deliberately contains no provider, scheduler, or frontend concerns.  The
derived sections are labelled in ``dataQuality`` until their formal source
tables are available.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from topicpilot_api.home_v2_publication import (
    empty_home_v2,
    read_latest_home_publication,
)

GRADE_RANK = {"S": 5, "A": 4, "B": 3, "D": 2, "X": 0}


def _number(value: Any) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _row_dict(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _topic_summary(row: Mapping[str, Any]) -> str:
    if row.get("score") is None:
        return "目前缺少有效評分，暫不解讀強弱。"
    grade = row.get("grade") or "未分級"
    state = row.get("strength_state") or "未定義"
    return f"目前為 {grade} 級，強度 {state}，分數 {_number(row['score'])}。"


def _score_text(value: Any) -> str:
    return "無資料" if value is None else str(_number(value))


def _event_for_pair(
    current: Mapping[str, Any], previous: Mapping[str, Any]
) -> dict[str, Any] | None:
    current_grade = current.get("grade")
    previous_grade = previous.get("grade")
    current_score = current.get("score")
    previous_score = previous.get("score")
    event_type: str | None = None
    severity = "MEDIUM"

    if current_grade and previous_grade and current_grade != previous_grade:
        current_rank = GRADE_RANK.get(current_grade, 0)
        previous_rank = GRADE_RANK.get(previous_grade, 0)
        event_type = "UPGRADE" if current_rank > previous_rank else "DOWNGRADE"
        severity = "HIGH"
    elif current_score is not None and previous_score is not None:
        delta = float(current_score) - float(previous_score)
        if delta > 0:
            event_type = "HEATING"
        elif delta < 0:
            event_type = "COOLING"

    if event_type is None:
        return None

    grade_change = ""
    if current_grade != previous_grade:
        grade_change = f"，級別由 {previous_grade or '無'} 變為 {current_grade or '無'}"
    description = (
        f"{current['topic_name']} 分數由 {_score_text(previous_score)}"
        f" 變為 {_score_text(current_score)}{grade_change}。"
    )
    return {
        "eventTime": current["generated_at"],
        "topic": current["topic_name"],
        "eventType": event_type,
        "description": description,
        "severity": severity,
        "topicSlug": current["topic_slug"],
        "source": "DERIVED_FROM_TOPIC_SNAPSHOT",
    }


def _rotation_summary(row: Mapping[str, Any], direction: str) -> str:
    delta = _number(row["change_14d"])
    verb = "升溫" if direction == "heating" else "降溫"
    return f"近 14 日{verb} {_number(delta)}，目前為 {row['latest_grade']} 級。"


def _empty_home(now: datetime, tracked_stock_count: int = 0) -> dict[str, Any]:
    return {
        "contractVersion": "v2.home-read-model.v1",
        "asOf": None,
        "generatedAt": now,
        "marketOverview": {
            "dataDate": None,
            "updatedAt": None,
            "dataStatus": "UNAVAILABLE",
            "trackedStockCount": tracked_stock_count,
            "trackedTopicCount": 0,
            "latestSnapshotTime": None,
            "marketHealth": None,
            "source": "POSTGRESQL_READ_MODEL",
        },
        "dailyFocus": {
            "mode": "RULE_BASED",
            "temporary": True,
            "headline": "目前沒有可用的市場快照。",
            "bullets": [],
            "dataDate": None,
            "source": "POSTGRES_TOPIC_SNAPSHOT_RULE",
        },
        "mainTopics": [],
        "marketPulse": [],
        "heatingTopics": [],
        "coolingTopics": [],
        "opportunities": [],
        "dataQuality": {
            "status": "UNAVAILABLE",
            "source": "POSTGRESQL",
            "classification": None,
            "temporarySections": ["dailyFocus", "marketPulse", "opportunities"],
            "missingSections": ["marketOverview", "mainTopics", "heatingTopics", "coolingTopics"],
            "notes": ["沒有可用的 public COMPLETED ingestion run。"],
        },
    }


def build_home_read_model(session: Session, now: datetime | None = None) -> dict[str, Any]:
    """Build the stable Home response from the current PostgreSQL read model."""

    generated_now = now or datetime.now(UTC)
    # V2 is the formal authority.  The legacy bridge is consulted only when
    # the additive V2 migration is not present, which keeps older compatibility
    # databases readable without making public.ingestion_runs a Home gate.
    try:
        session.execute(text("SELECT 1 FROM topicpilot.home_publications LIMIT 0"))
        v2_table_present = True
    except SQLAlchemyError:
        # A missing table on a pre-V2 compatibility database aborts the
        # current transaction in PostgreSQL; clear it before the legacy read.
        session.rollback()
        v2_table_present = False
    if v2_table_present:
        publication = read_latest_home_publication(session)
        if publication is not None:
            return publication
        tracked_stock_count = int(
            session.scalar(
                text(
                    """
                    SELECT count(*)
                    FROM topicpilot.instruments i
                    JOIN topicpilot.markets m ON m.id = i.market_id
                    WHERE i.is_active = true AND m.is_active = true
                    """
                )
            )
            or 0
        )
        return empty_home_v2(generated_now, tracked_stock_count=tracked_stock_count)
    run = _row_dict(
        session.execute(
            text(
                """
                SELECT id, contract_version, data_date, source_kind, source_name,
                       classification, generated_at, completed_at
                FROM public.ingestion_runs
                WHERE status = 'COMPLETED'
                ORDER BY data_date DESC, completed_at DESC NULLS LAST, id DESC
                LIMIT 1
                """
            )
        )
        .mappings()
        .one_or_none()
    )
    tracked_stock_count = int(
        session.scalar(
            text(
                """
                SELECT count(*)
                FROM topicpilot.live_tracking_universe ltu
                JOIN topicpilot.instruments i ON i.id = ltu.instrument_id
                JOIN topicpilot.markets m ON m.id = i.market_id
                WHERE i.is_active = true AND m.is_active = true
                """
            )
        )
        or 0
    )
    if run is None:
        return _empty_home(generated_now, tracked_stock_count)

    market = _row_dict(
        session.execute(
            text(
                """
                SELECT market, status, total_stocks, advance_count, decline_count,
                       unchanged_count, unavailable_count, generated_at
                FROM public.market_snapshots
                WHERE ingestion_run_id = :run_id AND data_date = :data_date
                ORDER BY total_stocks DESC NULLS LAST, id DESC
                LIMIT 1
                """
            ),
            {"run_id": run["id"], "data_date": run["data_date"]},
        )
        .mappings()
        .one_or_none()
    )
    latest_live = session.execute(
        text(
            """
            SELECT max(completed_at) AS completed_at
            FROM topicpilot.live_collector_runs
            WHERE status IN ('SUCCESS', 'PARTIAL', 'MARKET_CLOSED')
              AND completed_at IS NOT NULL
            """
        )
    ).scalar_one_or_none()
    source_times = [value for value in (run["generated_at"], latest_live) if value is not None]
    latest_snapshot_time = max(source_times) if source_times else None
    updated_at = latest_snapshot_time

    current_topics = [
        dict(row)
        for row in session.execute(
            text(
                """
                WITH ranked AS (
                    SELECT
                        t.slug, t.name, ts.data_date, ts.score, ts.grade,
                        ts.strength_state, ts.coverage_pct,
                        row_number() OVER (
                            PARTITION BY ts.topic_id
                            ORDER BY ts.data_date DESC, ir.completed_at DESC NULLS LAST, ts.id DESC
                        ) AS row_num
                    FROM public.topic_snapshots ts
                    JOIN public.topics t ON t.id = ts.topic_id AND t.enabled = true
                    JOIN public.ingestion_runs ir
                      ON ir.id = ts.ingestion_run_id AND ir.status = 'COMPLETED'
                )
                SELECT r.slug, r.name, r.data_date, r.score, r.grade,
                       r.strength_state, r.coverage_pct,
                       (
                           SELECT count(*)
                           FROM public.stock_topic_relations str
                           JOIN public.stocks s ON s.id = str.stock_id AND s.active = true
                           JOIN public.topics topic ON topic.id = str.topic_id
                           WHERE topic.slug = r.slug
                       ) AS stock_count
                FROM ranked r
                WHERE r.row_num = 1
                ORDER BY r.score DESC NULLS LAST, r.slug
                """
            )
        ).mappings()
    ]
    tracked_topic_count = len(current_topics)

    main_topics = [
        {
            "slug": row["slug"],
            "name": row["name"],
            "grade": row["grade"],
            "strength": _number(row["score"]),
            "currentState": row["strength_state"],
            "stockCount": int(row["stock_count"] or 0),
            "summary": _topic_summary(row),
            "favorite": False,
            "dataDate": row["data_date"],
        }
        for row in current_topics[:3]
    ]

    history_rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                WITH ranked AS (
                    SELECT
                        t.slug AS topic_slug, t.name AS topic_name,
                        ts.data_date, ts.score, ts.grade,
                        ts.strength_state, ir.generated_at,
                        row_number() OVER (
                            PARTITION BY ts.topic_id
                            ORDER BY ts.data_date DESC, ir.completed_at DESC NULLS LAST, ts.id DESC
                        ) AS row_num
                    FROM public.topic_snapshots ts
                    JOIN public.topics t ON t.id = ts.topic_id AND t.enabled = true
                    JOIN public.ingestion_runs ir
                      ON ir.id = ts.ingestion_run_id AND ir.status = 'COMPLETED'
                )
                SELECT topic_slug, topic_name, data_date, score, grade,
                       strength_state, generated_at
                FROM ranked
                WHERE row_num <= 2
                ORDER BY topic_slug, row_num
                """
            )
        ).mappings()
    ]
    topic_history: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in history_rows:
        topic_history[row["topic_slug"]].append(row)
    market_pulse: list[dict[str, Any]] = []
    for rows in topic_history.values():
        if len(rows) >= 2:
            event = _event_for_pair(rows[0], rows[1])
            if event:
                market_pulse.append(event)
        elif rows:
            market_pulse.append(
                {
                    "eventTime": rows[0]["generated_at"],
                    "topic": rows[0]["topic_name"],
                    "eventType": "NEW_TOPIC",
                    "description": f"{rows[0]['topic_name']} 首次出現在可用題材快照。",
                    "severity": "LOW",
                    "topicSlug": rows[0]["topic_slug"],
                    "source": "DERIVED_FROM_TOPIC_SNAPSHOT",
                }
            )
    market_pulse.sort(key=lambda item: item["eventTime"], reverse=True)

    rotation_rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT topic_slug, topic_name, change_14d, latest_grade
                FROM public.vw_topic_rotation_14d
                WHERE change_14d IS NOT NULL
                  AND latest_grade IS NOT NULL
                  AND latest_grade <> 'X'
                  AND change_14d > 0
                ORDER BY change_14d DESC, topic_slug
                LIMIT 3
                """
            )
        ).mappings()
    ]
    cooling_rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT topic_slug, topic_name, change_14d, latest_grade
                FROM public.vw_topic_rotation_14d
                WHERE change_14d IS NOT NULL
                  AND latest_grade IS NOT NULL
                  AND latest_grade <> 'X'
                  AND change_14d < 0
                ORDER BY change_14d ASC, topic_slug
                LIMIT 3
                """
            )
        ).mappings()
    ]

    def rotation_items(rows: list[dict[str, Any]], direction: str) -> list[dict[str, Any]]:
        return [
            {
                "topic": row["topic_name"],
                "topicSlug": row["topic_slug"],
                "strengthDelta": _number(row["change_14d"]),
                "currentGrade": row["latest_grade"],
                "summary": _rotation_summary(row, direction),
            }
            for row in rows
        ]

    opportunity_rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                WITH latest_runs AS (
                    SELECT DISTINCT ON (sr.strategy_key)
                        sr.id, sr.strategy_key, sr.data_date
                    FROM public.strategy_runs sr
                    JOIN public.ingestion_runs ir
                      ON ir.id = sr.ingestion_run_id AND ir.status = 'COMPLETED'
                    WHERE sr.status = 'COMPLETE'
                    ORDER BY sr.strategy_key, sr.data_date DESC,
                             ir.completed_at DESC NULLS LAST, sr.id DESC
                ),
                latest_topics AS (
                    SELECT DISTINCT ON (ts.topic_id)
                        ts.topic_id, ts.score, ts.grade, ts.strength_state
                    FROM public.topic_snapshots ts
                    JOIN public.ingestion_runs ir
                      ON ir.id = ts.ingestion_run_id AND ir.status = 'COMPLETED'
                    ORDER BY ts.topic_id, ts.data_date DESC,
                             ir.completed_at DESC NULLS LAST, ts.id DESC
                )
                SELECT
                    t.slug AS topic_slug, t.name AS topic_name,
                    lt.score AS topic_score, lt.grade AS topic_grade,
                    lt.strength_state AS topic_strength_state,
                    s.code, s.name AS stock_name, sc.score, sc.reason,
                    lr.strategy_key, lr.data_date
                FROM latest_runs lr
                JOIN public.strategy_candidates sc
                  ON sc.strategy_run_id = lr.id AND sc.selected = true AND sc.score IS NOT NULL
                JOIN public.stocks s ON s.id = sc.stock_id AND s.active = true
                JOIN public.stock_topic_relations str ON str.stock_id = s.id
                JOIN public.topics t ON t.id = str.topic_id AND t.enabled = true
                LEFT JOIN latest_topics lt ON lt.topic_id = t.id
                ORDER BY sc.score DESC, t.slug, s.code, lr.strategy_key
                """
            )
        ).mappings()
    ]
    opportunity_groups: dict[str, dict[str, Any]] = {}
    for row in opportunity_rows:
        topic = opportunity_groups.setdefault(
            row["topic_slug"],
            {
                "topic": row["topic_name"],
                "topicSlug": row["topic_slug"],
                "grade": row["topic_grade"],
                "strength": _number(row["topic_score"]),
                "currentState": row["topic_strength_state"],
                "summary": (
                    f"{row['topic_name']} 目前有策略候選股，候選資格來源為已完成策略執行。"
                ),
                "validatedStocks": [],
                "temporary": True,
            },
        )
        stocks_by_code = {stock["code"]: stock for stock in topic["validatedStocks"]}
        stock = stocks_by_code.get(row["code"])
        if stock is None:
            stock = {
                "code": row["code"],
                "name": row["stock_name"],
                "strategyKeys": [],
                "score": _number(row["score"]),
                "reason": row["reason"],
                "dataDate": row["data_date"],
            }
            topic["validatedStocks"].append(stock)
        if row["strategy_key"] not in stock["strategyKeys"]:
            stock["strategyKeys"].append(row["strategy_key"])
    opportunities = sorted(
        opportunity_groups.values(),
        key=lambda item: (
            -max((stock["score"] or 0) for stock in item["validatedStocks"]),
            item["topicSlug"],
        ),
    )[:3]

    temporary_sections = ["dailyFocus", "marketPulse", "opportunities"]
    missing_sections: list[str] = []
    notes = [
        "Market Pulse 目前由相鄰的每日 topic_snapshots 差異推導，尚無獨立事件表。",
        "Favorite 尚未有使用者偏好資料來源，目前固定回傳 false。",
    ]
    if run["source_kind"] == "synthetic":
        notes.append(
            "目前 public ingestion run 的 source_kind 為 synthetic，不能視為正式市場資料。"
        )
    notes.append(
        "目前 topicpilot V2 topic domain 尚無資料，題材區先以 public 題材快照與關聯資料橋接。"
    )
    if market is None:
        missing_sections.append("marketHealth")
        notes.append("目前 ingestion run 沒有可用的 market_snapshots。")
    missing_sections.extend(["marketIndices", "turnover", "v2TopicDomain"])
    return {
        "contractVersion": "v2.home-read-model.v1",
        "asOf": run["data_date"],
        "generatedAt": generated_now,
        "marketOverview": {
            "dataDate": run["data_date"],
            "updatedAt": updated_at,
            "dataStatus": "PARTIAL",
            "trackedStockCount": tracked_stock_count,
            "trackedTopicCount": tracked_topic_count,
            "latestSnapshotTime": latest_snapshot_time,
            "marketHealth": (
                {
                    "market": market["market"],
                    "status": market["status"],
                    "totalStocks": market["total_stocks"],
                    "advance": market["advance_count"],
                    "decline": market["decline_count"],
                    "flat": market["unchanged_count"],
                    "unavailable": market["unavailable_count"],
                }
                if market
                else None
            ),
            "source": "POSTGRESQL_READ_MODEL",
        },
        "dailyFocus": {
            "mode": "RULE_BASED",
            "temporary": True,
            "headline": (
                f"今日焦點：{main_topics[0]['name']}" if main_topics else "今日沒有可用的題材焦點。"
            ),
            "bullets": [
                f"主題排名依最新有效分數排序，共 {len(current_topics)} 個題材快照。",
                f"近 14 日升溫題材 {len(rotation_rows)} 個，降溫題材 {len(cooling_rows)} 個。",
            ],
            "dataDate": run["data_date"],
            "source": "POSTGRES_TOPIC_SNAPSHOT_RULE",
        },
        "mainTopics": main_topics,
        "marketPulse": market_pulse[:10],
        "heatingTopics": rotation_items(rotation_rows, "heating"),
        "coolingTopics": rotation_items(cooling_rows, "cooling"),
        "opportunities": opportunities,
        "dataQuality": {
            "status": "PARTIAL",
            "source": "POSTGRESQL",
            "classification": run["classification"],
            "temporarySections": temporary_sections,
            "missingSections": sorted(set(missing_sections)),
            "notes": notes,
        },
    }
