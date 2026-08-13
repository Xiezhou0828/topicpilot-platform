"""Operator command for the read-only G2 official provider preflight."""

from __future__ import annotations

import argparse
import json
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.provider_preflight import (
    REFERENCE_VERSION,
    build_database_failure_result,
    run_provider_preflight,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-date",
        required=True,
        type=date.fromisoformat,
        help="authoritative Taiwan market date to preflight (ISO date)",
    )
    parser.add_argument(
        "--reference-version",
        default=REFERENCE_VERSION,
        help="active reference version used for the SELECT-only context check",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = None
    try:
        engine = create_engine(get_settings().database_url, pool_pre_ping=True)
        with Session(engine, expire_on_commit=False) as session:
            result = run_provider_preflight(
                session,
                target_date=args.run_date,
                reference_version=args.reference_version,
            )
    except Exception:
        result = build_database_failure_result(
            target_date=args.run_date,
            reference_version=args.reference_version,
            error_code="PREFLIGHT_READ_FAILED",
        )
    finally:
        if engine is not None:
            engine.dispose()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
