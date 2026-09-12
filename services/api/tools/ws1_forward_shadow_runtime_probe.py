"""Bounded local-only probe for the WS1 forward shadow runtime task.

The probe never selects a research snapshot as formal input.  It is intentionally
limited to the local-only TopicPilot development database and reports the
formal snapshot/member-fact/price/lifecycle chain plus the existing scheduler
hook evidence.
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
from datetime import date
from types import SimpleNamespace
from typing import Any

from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from topicpilot_api.config import Settings
from topicpilot_api.live.post_close import PostCloseUpdater
from topicpilot_api.live.scheduler import LiveScheduler
from topicpilot_api.orm import TopicLifecycleResult, TopicSnapshot, TopicSnapshotMemberFact
from topicpilot_api.topic_lifecycle_engine import TopicLifecycleEngine
from topicpilot_api.topic_snapshot_engine import read_price_evidence


def _local_only_database(settings: Settings) -> tuple[str, dict[str, Any]]:
    database_url = settings.migration_database_url or settings.database_url
    parsed = make_url(database_url)
    local_hosts = {None, "localhost", "127.0.0.1", "::1"}
    if parsed.host not in local_hosts or parsed.database != "topicpilot":
        raise RuntimeError(
            "refusing runtime probe: target is not the local-only topicpilot database"
        )
    return database_url, {
        "host": parsed.host or "local-socket/default",
        "database": parsed.database,
        "explicitDatabaseUrl": bool(os.getenv("DATABASE_URL")),
        "explicitMigrationDatabaseUrl": bool(os.getenv("MIGRATION_DATABASE_URL")),
    }


def _migration_version(session: Session) -> list[str]:
    return [str(row[0]) for row in session.execute(text("select version_num from alembic_version"))]


def _formal_dates(session: Session) -> list[date]:
    return list(
        session.scalars(
            select(TopicSnapshot.snapshot_date)
            .where(
                TopicSnapshot.publication_mode == "FORMAL",
                TopicSnapshot.membership_mode == "PIT_FORMAL",
                TopicSnapshot.publication_state == "PUBLISHED",
                TopicSnapshot.finality_state == "FINAL",
                TopicSnapshot.superseded_by_snapshot_id.is_(None),
            )
            .distinct()
            .order_by(TopicSnapshot.snapshot_date)
        )
    )


def _canonical_price_inventory(session: Session) -> dict[str, Any]:
    row = session.execute(
        text(
            """
            SELECT
              MAX((co.observed_at AT TIME ZONE m.timezone)::date) AS latest_date,
              COUNT(DISTINCT co.instrument_id) AS instruments,
              COUNT(*) AS accepted_daily_bar_rows
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
    ).mappings().one()
    return {
        "latestDate": row["latest_date"].isoformat() if row["latest_date"] else None,
        "instruments": int(row["instruments"] or 0),
        "acceptedDailyBarRows": int(row["accepted_daily_bar_rows"] or 0),
    }


def _chain(session: Session, evaluation_date: date) -> dict[str, Any]:
    snapshots = list(
        session.scalars(
            select(TopicSnapshot).where(
                TopicSnapshot.snapshot_date == evaluation_date,
                TopicSnapshot.publication_mode == "FORMAL",
                TopicSnapshot.membership_mode == "PIT_FORMAL",
                TopicSnapshot.publication_state == "PUBLISHED",
                TopicSnapshot.finality_state == "FINAL",
                TopicSnapshot.superseded_by_snapshot_id.is_(None),
            )
        )
    )
    snapshot_ids = tuple(item.id for item in snapshots)
    facts = (
        list(
            session.scalars(
                select(TopicSnapshotMemberFact).where(
                    TopicSnapshotMemberFact.snapshot_id.in_(snapshot_ids)
                )
            )
        )
        if snapshot_ids
        else []
    )
    evidence = read_price_evidence(session, evaluation_date)
    lineage_complete = sum(
        all(
            getattr(item, field) is not None
            for field in (
                "snapshot_identity",
                "membership_snapshot_id",
                "membership_snapshot_hash",
                "relation_version",
                "source_artifact_id",
                "source_artifact_hash",
                "lineage_hash",
            )
        )
        for item in snapshots
    )
    fact_price_matches = sum(
        item.price_observation_id is not None
        and item.observation_date == evaluation_date
        and item.change_pct is not None
        and item.instrument_id in evidence
        and evidence[item.instrument_id].current_date == evaluation_date
        for item in facts
    )
    return {
        "evaluationDate": evaluation_date.isoformat(),
        "snapshotCount": len(snapshots),
        "memberFactCount": len(facts),
        "priceEvidenceInstrumentCount": len(evidence),
        "snapshotsWithCompleteLineage": lineage_complete,
        "memberFactsWithDateBoundPriceMatch": fact_price_matches,
        "formalChainReady": bool(snapshots)
        and lineage_complete == len(snapshots)
        and fact_price_matches > 0,
    }


def _scheduler_hook_evidence() -> dict[str, Any]:
    source = inspect.getsource(PostCloseUpdater._run_snapshot)
    finish_source = inspect.getsource(PostCloseUpdater._finish)
    scheduler_calls_post_close = []
    scheduler = LiveScheduler(
        collector=SimpleNamespace(run_once=lambda **_: "collector"),
        config=SimpleNamespace(
            timezone_name="Asia/Taipei",
            session_open="09:00",
            session_close="13:30",
            closed_dates=(),
            poll_interval_seconds=1,
        ),
        clock=lambda: __import__("datetime").datetime(2026, 8, 21, 14, 0),
        post_close_runner=lambda: scheduler_calls_post_close.append("POST_CLOSE") or "post-close",
    )
    result = scheduler.run_once("POST_CLOSE", enforce_session=False)
    return {
        "postCloseUpdaterCallsLifecycleEngine": "TopicLifecycleEngine" in source
        and "run_once" in source
        and 'result["lifecycle"]' in source,
        "schedulerInvokedPostCloseHook": result == "post-close"
        and scheduler_calls_post_close == ["POST_CLOSE"],
        "observabilityCarrier": "topicSnapshot" in finish_source
        and "lifecycle" in source,
    }


def _post_close_runtime(session: Session, evaluation_date: date) -> dict[str, Any]:
    snapshots = list(
        session.scalars(
            select(TopicSnapshot).where(
                TopicSnapshot.snapshot_date == evaluation_date,
                TopicSnapshot.publication_mode == "FORMAL",
                TopicSnapshot.membership_mode == "PIT_FORMAL",
                TopicSnapshot.publication_state == "PUBLISHED",
                TopicSnapshot.finality_state == "FINAL",
                TopicSnapshot.superseded_by_snapshot_id.is_(None),
            )
        )
    )
    snapshot_ids = tuple(item.id for item in snapshots)
    eligible_ids = tuple(
        session.scalars(
            select(TopicSnapshotMemberFact.instrument_id).where(
                TopicSnapshotMemberFact.snapshot_id.in_(snapshot_ids)
            )
        ).unique()
    )
    updater = object.__new__(PostCloseUpdater)
    updater.session = session
    result = updater._run_snapshot(
        evaluation_date,
        eligible_instrument_ids=eligible_ids,
    )
    lifecycle = result.get("lifecycle") or {}
    formal_state = result.get("formalTopicDailyState") or {}
    formal_write = (formal_state.get("writes") or [{}])[0]
    return {
        "snapshotStatus": result.get("status"),
        "formalStateStatus": formal_state.get("status"),
        "formalRowsBefore": formal_state.get("rowsBefore"),
        "formalRowsAfter": formal_state.get("rowsAfter"),
        "formalWriteCount": len(formal_state.get("writes") or []),
        "formalRowsWritten": formal_write.get("rowsWritten", 0),
        "formalIdempotentRows": formal_write.get("idempotentRows", 0),
        "lifecycleStatus": lifecycle.get("status"),
        "lifecycleTopicCount": lifecycle.get("topicCount"),
        "lifecycleBlockedTopicCount": lifecycle.get("blockedTopicCount"),
        "lifecycleDataStatusCounts": lifecycle.get("dataStatusCounts", {}),
        "lifecycleEvaluationMode": lifecycle.get("evaluationMode"),
        "noFormalLifecyclePublication": lifecycle.get("evaluationMode") == "SHADOW",
    }


def _lifecycle_summary(result: dict[str, Any]) -> dict[str, Any]:
    topic_results = result.get("topicResults") or []
    return {
        key: result.get(key)
        for key in (
            "status",
            "evaluationDate",
            "evaluationMode",
            "topicCount",
            "blockedTopicCount",
            "dataStatusCounts",
            "policyVersion",
            "calculationVersion",
        )
    } | {
        "topicResultCount": len(topic_results),
        "lineageBoundTopicCount": sum(bool(item.get("lineage")) for item in topic_results),
        "stageCounts": {
            str(stage): sum(item.get("finalStage") == stage for item in topic_results)
            for stage in sorted(
                {item.get("finalStage") for item in topic_results if item.get("finalStage")}
            )
        },
        "blockedTopics": [
            {
                "topicId": item.get("topicId"),
                "reason": item.get("transitionReason"),
            }
            for item in topic_results
            if item.get("evaluationStatus") == "BLOCKED"
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=date.fromisoformat)
    parser.add_argument("--execute-shadow", action="store_true")
    args = parser.parse_args()

    settings = Settings()
    database_url, target = _local_only_database(settings)
    engine = create_engine(database_url, pool_pre_ping=True)
    with Session(engine, expire_on_commit=False, autoflush=False) as session:
        formal_dates = _formal_dates(session)
        selected_date = args.date or (formal_dates[-1] if formal_dates else None)
        payload: dict[str, Any] = {
            "target": target,
            "alembicVersions": _migration_version(session),
            "formalDates": [item.isoformat() for item in formal_dates],
            "canonicalPriceInventory": _canonical_price_inventory(session),
            "schedulerHook": _scheduler_hook_evidence(),
        }
        if selected_date is None:
            payload["status"] = "BLOCKED_NO_FORMAL_FORWARD_DATE"
        else:
            payload["chainBefore"] = _chain(session, selected_date)
            if args.execute_shadow and payload["chainBefore"]["formalChainReady"]:
                payload["shadowRun"] = _lifecycle_summary(
                    TopicLifecycleEngine(session).run_once(evaluation_date=selected_date)
                )
                session.expire_all()
                persisted = list(
                    session.scalars(
                        select(TopicLifecycleResult).where(
                            TopicLifecycleResult.evaluation_date == selected_date,
                            TopicLifecycleResult.evaluation_mode == "SHADOW",
                        )
                    )
                )
                payload["shadowPersistence"] = {
                    "resultCount": len(persisted),
                    "lineageBoundResultCount": sum(
                        item.lineage_hash is not None for item in persisted
                    ),
                    "noFormalPublication": all(
                        item.evaluation_mode == "SHADOW" for item in persisted
                    ),
                }
                payload["chainAfter"] = _chain(session, selected_date)
                payload["postCloseRuntime"] = _post_close_runtime(session, selected_date)
            elif not payload["chainBefore"]["formalChainReady"]:
                payload["status"] = "BLOCKED_FORMAL_CHAIN_NOT_READY"
        if "status" not in payload:
            payload["status"] = "SUCCESS"
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if payload["status"] == "SUCCESS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
