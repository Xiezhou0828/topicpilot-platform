"""Guarded command-line entrypoint for the Production stock-master add stage."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine

from topicpilot_api.stock_add_master_writer import (
    EXPECTED_MIGRATION_HEAD,
    StockAddWriterError,
    apply_master_add,
    dry_run_master_add,
    validate_master_plan,
    verify_target,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-file", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--expected-host", required=True)
    parser.add_argument("--expected-database", required=True)
    parser.add_argument("--expected-role", required=True)
    parser.add_argument("--expected-runtime-revision", required=True)
    parser.add_argument("--operator", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.environment != "production":
            raise StockAddWriterError("PRODUCTION_ENVIRONMENT_REQUIRED")
        if os.getenv("GITHUB_SHA") != args.expected_runtime_revision:
            raise StockAddWriterError("RUNTIME_REVISION_MISMATCH")
        if args.apply:
            if os.getenv("TOPICPILOT_ALLOW_STOCK_ADD_APPLY") != "1":
                raise StockAddWriterError("PRODUCTION_APPLY_GUARD_MISSING")
            if not args.confirm:
                raise StockAddWriterError("FINAL_CONFIRMATION_REQUIRED")
        database_url = os.getenv("TOPICPILOT_PRODUCTION_STOCK_ADD_DATABASE_URL")
        if not database_url:
            raise StockAddWriterError("STOCK_ADD_DATABASE_URL_MISSING")
        plan = json.loads(Path(args.plan_file).read_text(encoding="utf-8"))
        _, digest, _ = validate_master_plan(plan)
        engine = create_engine(database_url, pool_pre_ping=True)
        try:
            with engine.begin() as connection:
                verify_target(
                    connection,
                    database_url=database_url,
                    expected_host=args.expected_host,
                    expected_database=args.expected_database,
                    expected_role=args.expected_role,
                    expected_migration_head=EXPECTED_MIGRATION_HEAD,
                )
                result = (
                    apply_master_add(
                        connection,
                        plan,
                        confirmation=args.confirm or "",
                        operator=args.operator,
                    )
                    if args.apply
                    else dry_run_master_add(connection, plan)
                )
        finally:
            engine.dispose()
        output = result.to_dict()
        output["planSha256"] = digest
        output["dryRun"] = bool(args.dry_run)
        print(json.dumps(output, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, StockAddWriterError) as exc:
        error = json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False)
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
