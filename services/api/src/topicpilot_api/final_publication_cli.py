"""Bounded operator comparator/normal-publication contract; read-only by default."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from topicpilot_api.comparator import ComparatorError, persist_comparator, prepare_comparator
from topicpilot_api.comparator import read_comparator as read_comparator_lineage
from topicpilot_api.config import get_settings
from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.normal_execution import OwnerNormalExecution
from topicpilot_api.live.post_close import PostClosePreconditionError
from topicpilot_api.market_data.exchange import _read_url
from topicpilot_api.market_data.institutional_flow_contract import (
    fetch_official_market_institutional_flows,
)
from topicpilot_api.provider_preflight import run_provider_preflight
from topicpilot_api.release_provenance import runtime_git_sha


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--operation",
        required=True,
        choices=("comparator-preflight", "comparator-apply", "normal-preflight", "normal-run"),
    )
    parser.add_argument("--target-date", required=True, type=date.fromisoformat)
    parser.add_argument("--comparator-date", type=date.fromisoformat)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--execution-id", type=UUID)
    parser.add_argument("--previous-run-id", type=UUID)
    parser.add_argument("--owner-authorized-once", action="store_true")
    parser.add_argument("--include-lineage", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    write = args.operation in {"comparator-apply", "normal-run"}
    if write and not args.owner_authorized_once:
        raise SystemExit("EXPLICIT_OWNER_AUTHORIZATION_REQUIRED")
    # This operator approval is bounded to the dates in this closure. It is
    # not a general backfill, retry, resume, or scheduler surface.
    if args.target_date != date(2026, 10, 2):
        raise SystemExit("TARGET_DATE_OUTSIDE_APPROVED_CLOSURE")
    revision = runtime_git_sha()
    if revision != args.expected_sha or revision == "UNKNOWN":
        raise SystemExit("RUNTIME_SHA_MISMATCH")
    config = LiveRuntimeConfig.from_environment()
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        with Session(engine, expire_on_commit=False) as session:
            migration = (
                session.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
            )
            if migration != ["0048_task_checkpoint_provider_metric_applicability"]:
                raise PostClosePreconditionError("MIGRATION_HEAD_MISMATCH")
            if args.operation.startswith("comparator"):
                if args.comparator_date != date(2026, 10, 1):
                    raise ComparatorError("COMPARATOR_DATE_OUTSIDE_APPROVED_CLOSURE")
                plan = prepare_comparator(
                    session,
                    comparator_date=args.comparator_date,
                    target_date=args.target_date,
                    reference_version=config.reference_data_version,
                )
                result = {**plan.summary(), "status": "READY", "productionMutated": False}
                if write:
                    result = persist_comparator(session, plan)
                    # Verify before commit and independently after commit. A
                    # failed in-transaction readback rolls back both markets.
                    read_comparator_lineage(session, plan)
                    session.commit()
                    with Session(engine) as readback_session:
                        result["readback"] = read_comparator_lineage(readback_session, plan)
                    result["productionMutated"] = result["created"] > 0
                    if not args.include_lineage:
                        result["readback"].pop("lineage", None)
            else:
                if args.execution_id is None or args.previous_run_id is None:
                    raise PostClosePreconditionError("NORMAL_EXECUTION_IDENTITY_REQUIRED")
                updater = OwnerNormalExecution(
                    session,
                    config,
                    execution_id=args.execution_id,
                    supersedes_run_id=args.previous_run_id,
                )
                result = updater.identity_preflight(args.target_date)
                if result["status"] == "PASS":
                    provider = run_provider_preflight(
                        session,
                        target_date=args.target_date,
                        reference_version=config.reference_data_version,
                    )
                    result["providerPreflight"] = provider
                    now = datetime.now(UTC)
                    flows = fetch_official_market_institutional_flows(
                        target_date=args.target_date,
                        retrieved_at=now,
                        as_of=now,
                        transport=_read_url,
                    )
                    result["institutionalFlow"] = [
                        {
                            "market": f.market,
                            "availability": f.availability,
                            "tradingDate": str(f.trading_date),
                            "reason": f.status_reason,
                            "source": f.source_identity,
                            "lineage": f.lineage_hash,
                        }
                        for f in flows
                    ]
                    if provider["status"] != "PASS":
                        result.update(status="BLOCKED", reasonCodes=["PROVIDER_G2_NOT_READY"])
                    elif (
                        len(flows) != 2
                        or {f.market for f in flows} != {"TPE", "TWO"}
                        or any(
                            f.availability != "AVAILABLE" or f.trading_date != args.target_date
                            for f in flows
                        )
                    ):
                        result.update(
                            status="BLOCKED", reasonCodes=["INSTITUTIONAL_FLOW_NOT_READY"]
                        )
                    if write and result["status"] == "PASS":
                        executed = updater.run_once(
                            run_date=args.target_date, execution_mode="MANUAL"
                        )
                        result["normalRun"] = executed.to_dict()
                        result["status"] = "PASS" if executed.status == "SUCCESS" else "FAILED"
                if not args.include_lineage and "providerPreflight" in result:
                    for market in result["providerPreflight"].get("markets", []):
                        for key in ("instrumentDecisions", "extraIdentityCodes"):
                            market.pop(key, None)
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 0 if result["status"] in {"PASS", "READY", "PERSISTED"} else 1
    except (ComparatorError, PostClosePreconditionError) as exc:
        print(json.dumps({"status": "BLOCKED", "errorCode": exc.code, "operation": args.operation}))
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
