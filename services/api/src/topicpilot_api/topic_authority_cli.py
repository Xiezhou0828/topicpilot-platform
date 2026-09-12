"""Protected operator entrypoint for Topic Authority Activation V1."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.topic_authority_activation import (
    TopicAuthorityActivationError,
    activate_topic_authority,
    load_activation_artifact,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--activate", action="store_true")
    parser.add_argument("--environment", required=True)
    parser.add_argument("--expected-database", required=True)
    parser.add_argument("--expected-runtime-revision")
    parser.add_argument("--operator", required=True)
    parser.add_argument("--confirm")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        artifact = load_activation_artifact(args.artifact)
        if args.validate_only:
            print(
                json.dumps(
                    {
                        "operation": "VALIDATION_PASS",
                        "activationVersion": artifact.activation_version,
                        "artifactSha256": artifact.artifact_sha256,
                        "topicCount": len(artifact.topics),
                        "hierarchyCount": len(artifact.hierarchy),
                        "lifecycleScopeCount": len(artifact.lifecycle_scope),
                    },
                    ensure_ascii=True,
                    sort_keys=True,
                )
            )
            return 0
        database_url = get_settings().database_url
        runtime_revision = os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_SHA")
        if (
            not args.expected_runtime_revision
            or runtime_revision != args.expected_runtime_revision
        ):
            raise TopicAuthorityActivationError(
                "deployed runtime revision does not match operator expectation"
            )
        engine = create_engine(database_url, pool_pre_ping=True)
        try:
            with Session(engine, expire_on_commit=False, autoflush=False) as session:
                result = activate_topic_authority(
                    session,
                    artifact,
                    dry_run=args.dry_run,
                    runtime_environment=args.environment,
                    expected_database=args.expected_database,
                    runtime_revision=runtime_revision,
                    operator_id=args.operator,
                    confirmation=args.confirm or os.getenv("TOPICPILOT_TOPIC_AUTHORITY_CONFIRM"),
                )
            print(json.dumps(result.to_dict(), ensure_ascii=True, sort_keys=True))
            return 0
        finally:
            engine.dispose()
    except (TopicAuthorityActivationError, RuntimeError, ValueError) as exc:
        print(
            json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=True),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
