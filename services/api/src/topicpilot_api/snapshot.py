from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from topicpilot_api.constants import SNAPSHOT_VERSION
from topicpilot_api.models import IngestionRun


def _number(value: Any) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        as_float = float(value)
        return int(as_float) if as_float.is_integer() else as_float
    return value


def assemble_snapshot(session: Session, run: IngestionRun) -> dict[str, Any]:
    """Build a deterministic, frontend-friendly snapshot from one completed import.

    Compatibility is intentionally structural rather than byte-for-byte with private web-data-007:
    this public read model uses MAS/MAV/TMC/BB/PB/KD as strategyId, English normalized relation
    keys, and omits private-only marketDecision, dailyObservation, entrySetups, and licensed source
    metadata. Missing numeric data remains JSON null, including selected strategy candidates.
    """
    params = {"run_id": run.id, "data_date": run.data_date}
    market = (
        session.execute(
            text(
                """
            SELECT * FROM market_snapshots
            WHERE ingestion_run_id = :run_id AND data_date = :data_date
            ORDER BY market LIMIT 1
            """
            ),
            params,
        )
        .mappings()
        .one_or_none()
    )
    stocks = list(
        session.execute(
            text(
                """
                SELECT
                    s.id, s.code, s.name, s.market, s.industry,
                    ss.price, ss.change_pct, ss.volume, ss.ma5, ss.ma20, ss.rs20,
                    ss.technical_state, ss.chip_score, ss.data_freshness, ss.metadata_json
                FROM stocks s
                LEFT JOIN stock_snapshots ss
                  ON ss.stock_id = s.id
                 AND ss.ingestion_run_id = :run_id
                 AND ss.data_date = :data_date
                WHERE s.active = true
                ORDER BY s.code
                """
            ),
            params,
        ).mappings()
    )
    topics = list(
        session.execute(
            text(
                """
                SELECT
                    t.id, t.slug, t.name, t.group_name, t.topic_type,
                    ts.score, ts.grade, ts.strength_state, ts.advance_count,
                    ts.decline_count, ts.unchanged_count, ts.unavailable_count,
                    ts.coverage_pct
                FROM topics t
                LEFT JOIN topic_snapshots ts
                  ON ts.topic_id = t.id
                 AND ts.ingestion_run_id = :run_id
                 AND ts.data_date = :data_date
                WHERE t.enabled = true
                ORDER BY t.slug
                """
            ),
            params,
        ).mappings()
    )
    relations = list(
        session.execute(
            text(
                """
                SELECT
                    s.id AS stock_id, s.code AS stock_code, s.name AS stock_name,
                    t.id AS topic_id, t.slug AS topic_slug, t.name AS topic_name,
                    t.group_name, r.relation_type, r.weight, r.evidence_summary
                FROM stock_topic_relations r
                JOIN stocks s ON s.id = r.stock_id
                JOIN topics t ON t.id = r.topic_id
                ORDER BY s.code, r.relation_type, t.slug
                """
            )
        ).mappings()
    )
    hierarchy = list(
        session.execute(
            text(
                """
                SELECT p.slug AS parent_slug, p.name AS parent_name,
                       c.slug AS child_slug, c.name AS child_name, h.weight
                FROM topic_hierarchy h
                JOIN topics p ON p.id = h.parent_topic_id
                JOIN topics c ON c.id = h.child_topic_id
                WHERE h.enabled = true
                ORDER BY p.slug, c.slug
                """
            )
        ).mappings()
    )
    history = list(
        session.execute(
            text(
                """
                SELECT t.slug, t.name, ts.data_date, ts.score, ts.grade, ts.strength_state
                FROM topic_snapshots ts
                JOIN topics t ON t.id = ts.topic_id
                WHERE ts.ingestion_run_id = :run_id
                ORDER BY t.slug, ts.data_date
                """
            ),
            {"run_id": run.id},
        ).mappings()
    )
    strategy_runs = list(
        session.execute(
            text(
                """
                SELECT * FROM strategy_runs
                WHERE ingestion_run_id = :run_id AND data_date = :data_date
                ORDER BY strategy_key
                """
            ),
            params,
        ).mappings()
    )
    candidates = list(
        session.execute(
            text(
                """
                SELECT sr.strategy_key, sr.model_version, sr.data_date, sc.rank,
                       s.code, s.name, sc.score, sc.reason, sc.price, sc.selected,
                       sc.trigger_price, sc.support_price, sc.invalidation_price
                FROM strategy_candidates sc
                JOIN strategy_runs sr ON sr.id = sc.strategy_run_id
                JOIN stocks s ON s.id = sc.stock_id
                WHERE sr.ingestion_run_id = :run_id AND sr.data_date = :data_date
                ORDER BY sr.strategy_key, sc.rank, s.code
                """
            ),
            params,
        ).mappings()
    )
    performance = list(
        session.execute(
            text(
                """
                SELECT sr.strategy_key, sr.name, sr.model_version, sr.data_date,
                       sr.selected_count, sp.horizon, sp.status, sp.sample_count,
                       sp.win_rate_pct, sp.average_return_pct, sp.reason
                FROM strategy_performance sp
                JOIN strategy_runs sr ON sr.id = sp.strategy_run_id
                WHERE sr.ingestion_run_id = :run_id AND sr.data_date = :data_date
                ORDER BY sr.strategy_key, sp.horizon
                """
            ),
            params,
        ).mappings()
    )

    relations_by_stock: dict[int, list[dict[str, Any]]] = defaultdict(list)
    constituents_by_topic: dict[int, list[str]] = defaultdict(list)
    for relation in relations:
        normalized = {
            "stockCode": relation["stock_code"],
            "stockName": relation["stock_name"],
            "topicSlug": relation["topic_slug"],
            "topicName": relation["topic_name"],
            "groupName": relation["group_name"],
            "relationType": relation["relation_type"],
            "weight": _number(relation["weight"]),
            "evidenceSummary": relation["evidence_summary"],
        }
        relations_by_stock[relation["stock_id"]].append(normalized)
        constituents_by_topic[relation["topic_id"]].append(relation["stock_code"])

    stock_payload: dict[str, dict[str, Any]] = {}
    for stock in stocks:
        stock_relations = relations_by_stock[stock["id"]]
        primary = next(
            (item for item in stock_relations if item["relationType"] == "PRIMARY"), None
        )
        secondary = next(
            (item for item in stock_relations if item["relationType"] == "SECONDARY"), None
        )
        stock_payload[stock["code"]] = {
            "code": stock["code"],
            "name": stock["name"],
            "price": {
                "close": _number(stock["price"]),
                "changePct": _number(stock["change_pct"]),
                "volume": stock["volume"],
                "dataDate": run.data_date.isoformat(),
            },
            "technical": {
                "MA5": _number(stock["ma5"]),
                "MA20": _number(stock["ma20"]),
                "RS20%": _number(stock["rs20"]),
                "state": stock["technical_state"],
            },
            "chip": {"score": _number(stock["chip_score"])},
            "risk": {"dataFreshness": stock["data_freshness"]},
            "topicMain": primary["topicName"] if primary else None,
            "topicSub": secondary["topicName"] if secondary else None,
            "topicMainWeight": primary["weight"] if primary else None,
            "topicSubWeight": secondary["weight"] if secondary else None,
            "topicRelations": stock_relations,
            "quality": stock["metadata_json"],
        }

    topic_payload = [
        {
            "slug": topic["slug"],
            "name": topic["name"],
            "group": topic["group_name"],
            "type": topic["topic_type"],
            "grade": topic["grade"],
            "strengthState": topic["strength_state"],
            "score": _number(topic["score"]),
            "strengthScore": _number(topic["score"]),
            "stockCount": len(set(constituents_by_topic[topic["id"]])),
            "observedCount": (
                None
                if topic["advance_count"] is None
                else topic["advance_count"]
                + (topic["decline_count"] or 0)
                + (topic["unchanged_count"] or 0)
            ),
            "breadthRatio": _number(topic["coverage_pct"]),
            "leaders": sorted(set(constituents_by_topic[topic["id"]]))[:5],
        }
        for topic in topics
    ]

    children_by_parent: dict[str, list[str]] = defaultdict(list)
    for edge in hierarchy:
        children_by_parent[edge["parent_slug"]].append(edge["child_name"])
    topic_groups = [
        {
            "name": edge["parent_name"],
            "children": children_by_parent[edge["parent_slug"]],
            "childCount": len(children_by_parent[edge["parent_slug"]]),
        }
        for edge in hierarchy
        if children_by_parent[edge["parent_slug"]]
        and edge["child_name"] == children_by_parent[edge["parent_slug"]][0]
    ]

    history_by_topic: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for point in history:
        history_by_topic[(point["slug"], point["name"])].append(
            {
                "date": point["data_date"].isoformat(),
                "score": _number(point["score"]),
                "grade": point["grade"],
                "strengthState": point["strength_state"],
            }
        )

    candidates_by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    candidate_payload = []
    for candidate in candidates:
        stock_relation = next(
            (
                item
                for item in relations_by_stock[
                    next(stock["id"] for stock in stocks if stock["code"] == candidate["code"])
                ]
                if item["relationType"] == "PRIMARY"
            ),
            None,
        )
        item = {
            "strategyId": candidate["strategy_key"],
            "strategyKey": "|".join(
                (
                    candidate["data_date"].isoformat(),
                    candidate["strategy_key"],
                    candidate["code"],
                    candidate["model_version"],
                )
            ),
            "modelVersion": candidate["model_version"],
            "batchDate": candidate["data_date"].isoformat(),
            "rank": candidate["rank"],
            "code": candidate["code"],
            "name": candidate["name"],
            "majorGroup": stock_relation["groupName"] if stock_relation else None,
            "fineTopic": stock_relation["topicName"] if stock_relation else None,
            "score": _number(candidate["score"]),
            "reason": candidate["reason"],
            "price": _number(candidate["price"]),
            "dataDate": candidate["data_date"].isoformat(),
            "dataTime": run.generated_at.isoformat(),
            "selected": candidate["selected"],
            "trigger": _number(candidate["trigger_price"]),
            "support": _number(candidate["support_price"]),
            "invalidation": _number(candidate["invalidation_price"]),
        }
        candidate_payload.append(item)
        candidates_by_strategy[candidate["strategy_key"]].append(item)

    performance_by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    performance_identity: dict[str, dict[str, Any]] = {}
    for row in performance:
        performance_identity[row["strategy_key"]] = dict(row)
        performance_by_strategy[row["strategy_key"]].append(dict(row))
    performance_payload = []
    for strategy_run in strategy_runs:
        rows = performance_by_strategy[strategy_run["strategy_key"]]
        horizons = {
            row["horizon"]: {
                "status": row["status"],
                "sampleCount": row["sample_count"],
                "winRate": _number(row["win_rate_pct"]),
                "avgReturnPct": _number(row["average_return_pct"]),
                "reason": row["reason"],
            }
            for row in rows
        }
        available = sum(row["status"] == "AVAILABLE" for row in rows)
        performance_payload.append(
            {
                "strategyId": strategy_run["strategy_key"],
                "strategyKey": strategy_run["strategy_key"],
                "name": strategy_run["name"],
                "modelVersion": strategy_run["model_version"],
                "dataDate": strategy_run["data_date"].isoformat(),
                "status": "AVAILABLE" if available else "SAMPLE_ACCUMULATING",
                "sampleCount": strategy_run["selected_count"],
                "availableHorizonCount": available,
                "horizons": horizons,
                "source": "PostgreSQL synthetic read model",
            }
        )

    missing_price = sorted(stock["code"] for stock in stocks if stock["price"] is None)
    successful = len(stocks) - len(missing_price)
    market_status = market["status"] if market else "NOT_RUN"
    return {
        "snapshotVersion": SNAPSHOT_VERSION,
        "classification": run.classification,
        "generatedAt": run.generated_at,
        "dataDate": run.data_date,
        "compatibilityNotes": [
            "Normalized stable strategy IDs replace private legacy strategy IDs.",
            "Private-only market decision, observation, and licensed-source payloads are omitted.",
            "Unavailable numeric values remain null, including strategy candidate prices.",
        ],
        "contracts": {
            "enterpriseBundle": {"version": run.contract_version},
            "strategyRegistry": {"version": "enterprise-strategy-registry-001"},
            "strategyCandidates": {"version": "enterprise-strategy-candidates-001"},
            "strategyPerformance": {"version": "enterprise-strategy-performance-001"},
        },
        "quoteMeta": {
            "status": market_status,
            "dataDate": run.data_date.isoformat(),
            "updatedAt": run.generated_at,
            "source": run.source_name,
            "totalSymbols": len(stocks),
            "successSymbols": successful,
            "failedSymbols": len(missing_price),
            "failedCodes": missing_price,
        },
        "marketSession": {
            "market": market["market"] if market else None,
            "timezone": "Asia/Taipei",
            "currentDate": run.data_date.isoformat(),
            "latestTradingDate": run.data_date.isoformat(),
            "isTradingDay": True,
            "session": "CLOSED",
            "reason": "Historical enterprise read model",
            "nextTradingDate": None,
        },
        "quality": {
            "priceRows": successful,
            "technicalRows": sum(stock["technical_state"] is not None for stock in stocks),
            "chipRows": sum(stock["chip_score"] is not None for stock in stocks),
            "fundamentalRows": 0,
            "entryRows": 0,
            "dailyObservationRows": 0,
            "dailyObservationSource": None,
            "entrySource": None,
            "universe": len(stocks),
            "missingPrice": missing_price,
            "missingTechnical": sorted(
                stock["code"] for stock in stocks if stock["technical_state"] is None
            ),
            "missingChip": sorted(stock["code"] for stock in stocks if stock["chip_score"] is None),
            "missingFundamental": sorted(stock["code"] for stock in stocks),
            "missingEntry": sorted(stock["code"] for stock in stocks),
            "unavailableTechnicalFields": [],
        },
        "market": {"indices": []},
        "topics": topic_payload,
        "topicGroups": topic_groups,
        "topicRelations": [
            item for stock_items in relations_by_stock.values() for item in stock_items
        ],
        "topicStrengthHistory": [
            {"slug": slug, "topic": name, "points": points}
            for (slug, name), points in sorted(history_by_topic.items())
        ],
        "strategyRegistry": {
            "version": "enterprise-strategy-registry-001",
            "dataDate": run.data_date.isoformat(),
            "strategies": [
                {
                    "strategyId": item["strategy_key"],
                    "name": item["name"],
                    "modelVersion": item["model_version"],
                    "batchDate": item["data_date"].isoformat(),
                    "batchStatus": item["status"],
                    "candidateCount": item["candidate_count"],
                    "selectedCount": item["selected_count"],
                    "rankingCount": item["candidate_count"],
                    "missingReason": None,
                }
                for item in strategy_runs
            ],
        },
        "strategyCandidates": candidate_payload,
        "strategyPerformance": performance_payload,
        "dailyObservation": [],
        "entrySetups": [],
        "stocks": stock_payload,
    }
