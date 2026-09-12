"""Operator entrypoint for Lifecycle V1.3 formal publication."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.lifecycle_formal_publication import (
    FormalLifecyclePublisher,
    formal_correction_dates,
)
from topicpilot_api.topic_daily_state import materialize_formal_correction, plan_formal_correction


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--date", type=date.fromisoformat, help="one formal trading date")
    group.add_argument(
        "--replay",
        action="store_true",
        help="replay formal Topic Snapshot dates from the A9 authority boundary",
    )
    group.add_argument(
        "--a9-correction",
        action="store_true",
        help="preflight and append-only correct the current formal A9 snapshot dates",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="evaluate and report without publishing formal rows",
    )
    parser.add_argument("--database-url", help="explicit protected database URL")
    parser.add_argument("--environment", help="must be the exact production target for writes")
    parser.add_argument("--expected-database", help="exact PostgreSQL database name for writes")
    parser.add_argument(
        "--expected-runtime-revision", help="exact deployed source revision for writes"
    )
    parser.add_argument("--operator", help="audited operator identity for writes")
    parser.add_argument(
        "--confirm",
        help="exact confirmation: A9-B2-FORMAL-REPLAY:<expected-runtime-revision>",
    )
    return parser


def _validate_write_target(session: Session, args: argparse.Namespace) -> tuple[str, str]:
    if args.environment != "production":
        raise ValueError("formal replay writes require --environment production")
    if not args.expected_database:
        raise ValueError("formal replay writes require --expected-database")
    if not args.expected_runtime_revision:
        raise ValueError("formal replay writes require --expected-runtime-revision")
    if not args.operator or not args.operator.strip():
        raise ValueError("formal replay writes require --operator")
    runtime_revision = os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_SHA")
    if runtime_revision != args.expected_runtime_revision:
        raise ValueError("deployed runtime revision does not match operator expectation")
    required_confirmation = f"A9-B2-FORMAL-REPLAY:{args.expected_runtime_revision}"
    if args.confirm != required_confirmation:
        raise ValueError("exact formal replay confirmation is required")
    if session.bind is None or session.bind.dialect.name != "postgresql":
        raise ValueError("formal replay writer requires PostgreSQL")
    actual_database = session.execute(text("select current_database()")).scalar_one()
    if actual_database != args.expected_database:
        raise ValueError("database identity does not match operator expectation")
    revision = session.execute(
        text("SELECT version_num FROM topicpilot.alembic_version LIMIT 1")
    ).scalar_one_or_none()
    if revision != "0039_task_a9_b2_formal_correction_supersession":
        raise ValueError("formal correction supersession migration is not active")
    return runtime_revision, required_confirmation


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = get_settings()
        engine = create_engine(args.database_url or settings.database_url, pool_pre_ping=True)
        with Session(engine, expire_on_commit=False, autoflush=False) as session:
            writer_context: dict[str, str] = {}
            if not args.dry_run:
                runtime_revision, _ = _validate_write_target(session, args)
                writer_context = {
                    "environment": args.environment,
                    "database": args.expected_database,
                    "runtimeRevision": runtime_revision,
                    "operator": args.operator.strip(),
                    "operation": "A9_B2_FORMAL_REPLAY",
                }
            publisher = FormalLifecyclePublisher(session, writer_context=writer_context)
            if args.a9_correction:
                dates = formal_correction_dates(session)
                correction_plan = plan_formal_correction(session, dates)
                result = (
                    {**correction_plan.as_dict(), "status": "DRY_RUN", "writes": []}
                    if args.dry_run
                    else materialize_formal_correction(
                        session, correction_plan, writer_context=writer_context
                    )
                )
            elif args.date:
                result = publisher.run_once(
                    evaluation_date=args.date,
                    persist=not args.dry_run,
                ).as_dict()
            else:
                result = publisher.run_replay(persist=not args.dry_run)
        print(json.dumps(result, ensure_ascii=False, default=str, sort_keys=True))
        return 0
    except (RuntimeError, ValueError) as exc:
        print(
            json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=True),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
