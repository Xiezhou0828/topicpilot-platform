from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from topicpilot_api.bundle import LoadedBundle
from topicpilot_api.models import (
    DataQualityEvent,
    IngestionRun,
    MarketSnapshot,
    SourceArtifact,
    Stock,
    StockSnapshot,
    StockTopicRelation,
    StrategyCandidate,
    StrategyPerformance,
    StrategyRun,
    Topic,
    TopicHierarchy,
    TopicSnapshot,
)


class ImportConflictError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImportResult:
    status: str
    ingestion_run_id: int
    bundle_version: str
    bundle_hash: str
    row_counts: dict[str, int]


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp must include an offset: {value}")
    return parsed.astimezone(UTC)


def _date(value: str) -> date:
    return date.fromisoformat(value)


def _upsert_stocks(session: Session, rows: list[dict[str, Any]]) -> dict[str, Stock]:
    existing = {
        row.code: row
        for row in session.scalars(
            select(Stock).where(Stock.code.in_([item["code"] for item in rows]))
        )
    }
    for item in rows:
        row = existing.get(item["code"])
        if row is None:
            row = Stock(code=item["code"], name=item["name"], market=item["market"])
            session.add(row)
            existing[item["code"]] = row
        row.name = item["name"]
        row.market = item["market"]
        row.industry = item["industry"]
        row.active = item["active"]
        row.metadata_json = item["metadata"]
    session.flush()
    return existing


def _upsert_topics(session: Session, rows: list[dict[str, Any]]) -> dict[str, Topic]:
    existing = {
        row.slug: row
        for row in session.scalars(
            select(Topic).where(Topic.slug.in_([item["slug"] for item in rows]))
        )
    }
    for item in rows:
        row = existing.get(item["slug"])
        if row is None:
            row = Topic(slug=item["slug"], name=item["name"], topic_type=item["topicType"])
            session.add(row)
            existing[item["slug"]] = row
        row.name = item["name"]
        row.group_name = item["groupName"]
        row.topic_type = item["topicType"]
        row.enabled = item["enabled"]
        row.metadata_json = item["metadata"]
    session.flush()
    return existing


def import_bundle(session: Session, bundle: LoadedBundle) -> ImportResult:
    manifest = bundle.manifest
    bundle_version = manifest["bundleVersion"]

    with session.begin():
        existing = session.scalar(
            select(IngestionRun)
            .where(IngestionRun.bundle_version == bundle_version)
            .with_for_update()
        )
        if existing is not None:
            if existing.bundle_hash != bundle.bundle_hash:
                raise ImportConflictError(
                    f"Bundle version {bundle_version!r} already exists with a different SHA-256; "
                    "publication is rejected. Publish a new bundleVersion for corrected data."
                )
            if existing.status != "COMPLETED":
                raise ImportConflictError(
                    f"Bundle version {bundle_version!r} already exists "
                    f"with status {existing.status}"
                )
            return ImportResult(
                status="NO_OP",
                ingestion_run_id=existing.id,
                bundle_version=bundle_version,
                bundle_hash=bundle.bundle_hash,
                row_counts=dict(existing.row_counts),
            )

        source = manifest["source"]
        run = IngestionRun(
            contract_version=manifest["contractVersion"],
            bundle_version=bundle_version,
            data_date=_date(manifest["dataDate"]),
            bundle_hash=bundle.bundle_hash,
            source_kind=source["kind"],
            source_name=source["name"],
            classification=source["classification"],
            generated_at=_dt(manifest["generatedAt"]),
            status="IMPORTING",
            row_counts=bundle.row_counts,
        )
        session.add(run)
        session.flush()

        for artifact in bundle.artifacts:
            session.add(
                SourceArtifact(
                    ingestion_run_id=run.id,
                    artifact_name=artifact.name,
                    file_name=artifact.file_name,
                    sha256=artifact.sha256,
                    row_count=artifact.row_count,
                    byte_size=artifact.byte_size,
                    metadata_json={"contractVersion": manifest["contractVersion"]},
                )
            )

        stocks = _upsert_stocks(session, bundle.data["stocks"])
        topics = _upsert_topics(session, bundle.data["topics"])

        # These are current dimensions, not historical facts. Replacing them in this transaction
        # keeps the read model aligned while preserving rollback on any later failure.
        session.execute(delete(StockTopicRelation))
        session.execute(delete(TopicHierarchy))
        for item in bundle.data["topicHierarchy"]:
            session.add(
                TopicHierarchy(
                    parent_topic_id=topics[item["parentSlug"]].id,
                    child_topic_id=topics[item["childSlug"]].id,
                    weight=item["weight"],
                    enabled=item["enabled"],
                    metadata_json=item["metadata"],
                )
            )
        for item in bundle.data["stockTopicRelations"]:
            session.add(
                StockTopicRelation(
                    stock_id=stocks[item["stockCode"]].id,
                    topic_id=topics[item["topicSlug"]].id,
                    relation_type=item["relationType"],
                    weight=item["weight"],
                    evidence_summary=item["evidenceSummary"],
                    metadata_json=item["metadata"],
                )
            )

        daily = bundle.data["dailySnapshots"]
        for item in daily["marketSnapshots"]:
            session.add(
                MarketSnapshot(
                    ingestion_run_id=run.id,
                    data_date=_date(item["dataDate"]),
                    generated_at=_dt(item["generatedAt"]),
                    market=item["market"],
                    status=item["status"],
                    total_stocks=item["totalStocks"],
                    advance_count=item["advanceCount"],
                    decline_count=item["declineCount"],
                    unchanged_count=item["unchangedCount"],
                    unavailable_count=item["unavailableCount"],
                    metadata_json=item["metadata"],
                )
            )
        for item in daily["stockSnapshots"]:
            session.add(
                StockSnapshot(
                    ingestion_run_id=run.id,
                    data_date=_date(item["dataDate"]),
                    stock_id=stocks[item["stockCode"]].id,
                    price=item["price"],
                    change_pct=item["changePct"],
                    volume=item["volume"],
                    ma5=item["ma5"],
                    ma20=item["ma20"],
                    rs20=item["rs20"],
                    technical_state=item["technicalState"],
                    chip_score=item["chipScore"],
                    data_freshness=item["dataFreshness"],
                    metadata_json=item["metadata"],
                )
            )
        for item in daily["topicSnapshots"]:
            session.add(
                TopicSnapshot(
                    ingestion_run_id=run.id,
                    data_date=_date(item["dataDate"]),
                    topic_id=topics[item["topicSlug"]].id,
                    score=item["score"],
                    grade=item["grade"],
                    strength_state=item["strengthState"],
                    advance_count=item["advanceCount"],
                    decline_count=item["declineCount"],
                    unchanged_count=item["unchangedCount"],
                    unavailable_count=item["unavailableCount"],
                    coverage_pct=item["coveragePct"],
                    metadata_json=item["metadata"],
                )
            )
        for item in daily["dataQualityEvents"]:
            session.add(
                DataQualityEvent(
                    ingestion_run_id=run.id,
                    data_date=_date(item["dataDate"]),
                    severity=item["severity"],
                    event_code=item["eventCode"],
                    message=item["message"],
                    entity_type=item["entityType"],
                    entity_key=item["entityKey"],
                    metadata_json=item["metadata"],
                )
            )

        strategy_runs: dict[tuple[str, date, str], StrategyRun] = {}
        for item in bundle.data["strategyCandidates"]["strategyRuns"]:
            strategy_run = StrategyRun(
                ingestion_run_id=run.id,
                strategy_key=item["strategyKey"],
                name=item["name"],
                model_version=item["modelVersion"],
                data_date=_date(item["dataDate"]),
                status=item["status"],
                candidate_count=item["candidateCount"],
                selected_count=item["selectedCount"],
                metadata_json=item["metadata"],
            )
            session.add(strategy_run)
            strategy_runs[(item["strategyKey"], _date(item["dataDate"]), item["modelVersion"])] = (
                strategy_run
            )
        session.flush()

        for item in bundle.data["strategyCandidates"]["candidates"]:
            strategy_run = strategy_runs[
                (item["strategyKey"], _date(item["dataDate"]), item["modelVersion"])
            ]
            session.add(
                StrategyCandidate(
                    strategy_run_id=strategy_run.id,
                    stock_id=stocks[item["stockCode"]].id,
                    rank=item["rank"],
                    score=item["score"],
                    reason=item["reason"],
                    price=item["price"],
                    selected=item["selected"],
                    trigger_price=item["triggerPrice"],
                    support_price=item["supportPrice"],
                    invalidation_price=item["invalidationPrice"],
                    metadata_json=item["metadata"],
                )
            )
        for item in bundle.data["strategyPerformance"]:
            strategy_run = strategy_runs[
                (item["strategyKey"], _date(item["dataDate"]), item["modelVersion"])
            ]
            session.add(
                StrategyPerformance(
                    strategy_run_id=strategy_run.id,
                    horizon=item["horizon"],
                    status=item["status"],
                    sample_count=item["sampleCount"],
                    win_rate_pct=item["winRatePct"],
                    average_return_pct=item["averageReturnPct"],
                    reason=item["reason"],
                    metadata_json=item["metadata"],
                )
            )

        run.status = "COMPLETED"
        run.completed_at = datetime.now(UTC)
        session.flush()

        return ImportResult(
            status="IMPORTED",
            ingestion_run_id=run.id,
            bundle_version=bundle_version,
            bundle_hash=bundle.bundle_hash,
            row_counts=bundle.row_counts,
        )
