"""Protected operator entrypoint for Structural Role Authority V1."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.structural_role_authority import (
    StructuralRoleAuthorityError,
    activate,
    load_artifact,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--activate", action="store_true")
    parser.add_argument("--environment", required=True)
    parser.add_argument("--expected-database", required=True)
    parser.add_argument("--expected-runtime-revision", required=True)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--confirm")
    args = parser.parse_args(argv)
    try:
        artifact = load_artifact(args.artifact)
        if args.validate_only:
            print(json.dumps({
                "operation": "VALIDATION_PASS",
                "authorityVersion": artifact.authority_version,
                "artifactSha256": artifact.artifact_sha256,
                "relationCount": len(artifact.rows),
            }, sort_keys=True))
            return 0
        runtime_revision = os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_SHA")
        if runtime_revision != args.expected_runtime_revision:
            raise StructuralRoleAuthorityError(
                "deployed runtime revision does not match operator expectation"
            )
        engine = create_engine(get_settings().database_url, pool_pre_ping=True)
        try:
            with Session(engine, expire_on_commit=False, autoflush=False) as session:
                result = activate(
                    session,
                    artifact,
                    dry_run=args.dry_run,
                    environment=args.environment,
                    expected_database=args.expected_database,
                    operator=args.operator,
                    confirmation=args.confirm or os.getenv("TOPICPILOT_ROLE_AUTHORITY_CONFIRM"),
                )
            print(json.dumps(result, sort_keys=True))
            return 0
        finally:
            engine.dispose()
    except (StructuralRoleAuthorityError, RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
