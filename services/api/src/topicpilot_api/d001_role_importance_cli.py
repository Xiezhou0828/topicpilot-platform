"""Governed operator entrypoint for DEC-04 D001 materialization/readback."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.d001_role_importance_authority import (
    D001RoleImportanceAuthorityError,
    load_artifact,
    materialize_d001_projections,
    readback_d001_projections,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--materialize", action="store_true")
    mode.add_argument("--readback", action="store_true")
    parser.add_argument("--environment", required=False, default="production")
    parser.add_argument("--expected-database", required=False)
    parser.add_argument("--expected-runtime-revision", required=False)
    parser.add_argument("--operator", required=False, default="")
    parser.add_argument("--confirm")
    parser.add_argument("--as-of", type=date.fromisoformat)
    parser.add_argument("--read-mode", choices=("CURRENT", "HISTORICAL"), default="CURRENT")
    return parser


def _require_runtime_args(args: argparse.Namespace) -> None:
    if args.environment != "production":
        raise D001RoleImportanceAuthorityError("D001 runtime commands require production")
    if not args.expected_database:
        raise D001RoleImportanceAuthorityError("--expected-database is required")
    if not args.operator.strip():
        raise D001RoleImportanceAuthorityError("--operator is required")
    if args.expected_runtime_revision:
        runtime_revision = os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_SHA")
        if runtime_revision != args.expected_runtime_revision:
            raise D001RoleImportanceAuthorityError(
                "deployed runtime revision does not match operator expectation"
            )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        artifact = load_artifact(args.artifact)
        if args.validate_only:
            print(
                json.dumps(
                    {
                        "operation": "D001_VALIDATION_PASS",
                        "authorityVersion": artifact.authority_version,
                        "artifactSha256": artifact.artifact_sha256,
                        "topicCount": artifact.payload["expectedTopicCount"],
                        "memberCount": artifact.payload["expectedMemberCount"],
                    },
                    sort_keys=True,
                )
            )
            return 0

        _require_runtime_args(args)
        engine = create_engine(get_settings().database_url, pool_pre_ping=True)
        try:
            with Session(engine, expire_on_commit=False, autoflush=False) as session:
                if args.readback:
                    result = readback_d001_projections(
                        session,
                        artifact,
                        expected_database=args.expected_database,
                        as_of=args.as_of,
                        read_mode=args.read_mode,
                    )
                else:
                    result = materialize_d001_projections(
                        session,
                        artifact,
                        dry_run=args.dry_run,
                        expected_database=args.expected_database,
                        operator=args.operator,
                        confirmation=args.confirm
                        or os.getenv("TOPICPILOT_D001_MATERIALIZE_CONFIRM"),
                    )
        finally:
            engine.dispose()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (D001RoleImportanceAuthorityError, RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
