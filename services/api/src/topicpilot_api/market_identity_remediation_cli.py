"""Explicit operator command for the known TPE/TWO market identity drift."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.market_identity_remediation import (
    MarketIdentityRemediationConflict,
    remediate_market_identity,
)
from topicpilot_api.reference_data import BundleValidationError, load_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = load_bundle(Path(args.bundle_dir))
        engine = create_engine(get_settings().database_url, pool_pre_ping=True)
        try:
            with Session(engine, expire_on_commit=False) as session:
                result = remediate_market_identity(
                    session,
                    bundle,
                    apply=args.apply,
                    dry_run=args.dry_run,
                )
            print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
            return 0
        finally:
            engine.dispose()
    except (
        BundleValidationError,
        MarketIdentityRemediationConflict,
        RuntimeError,
        ValueError,
    ) as exc:
        print(
            json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
