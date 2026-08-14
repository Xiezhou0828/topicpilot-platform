"""Explicit operator command for immutable reference-registry rollover."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.reference_data import BundleValidationError, load_bundle
from topicpilot_api.reference_data.bootstrap import ReferenceBootstrapConflict
from topicpilot_api.reference_data.transition import transition_reference_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-reference-version", required=True)
    parser.add_argument("--expected-from-bundle-sha256", required=True)
    parser.add_argument("--bundle-dir", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--activate", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = load_bundle(Path(args.bundle_dir))
        engine = create_engine(get_settings().database_url, pool_pre_ping=True)
        try:
            with Session(engine, expire_on_commit=False) as session:
                result = transition_reference_registry(
                    session,
                    bundle,
                    from_reference_version=args.from_reference_version,
                    expected_from_bundle_sha256=args.expected_from_bundle_sha256,
                    activate=args.activate,
                    dry_run=args.dry_run,
                )
            print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
            return 0
        finally:
            engine.dispose()
    except (BundleValidationError, ReferenceBootstrapConflict, RuntimeError, ValueError) as exc:
        print(
            json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
