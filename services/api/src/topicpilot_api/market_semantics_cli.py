"""Operator command for the read-only G3 market semantics gate."""

from __future__ import annotations

import argparse
import json
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.market_semantics import (
    build_database_failure_result,
    run_market_semantics_check,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-date",
        required=True,
        type=date.fromisoformat,
        help="authoritative Taiwan market date to validate (ISO date)",
    )
    parser.add_argument(
        "--reference-version",
        required=True,
        help="active reference version used for the SELECT-only context check",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = None
    try:
        engine = create_engine(get_settings().database_url, pool_pre_ping=True)
        with Session(engine, expire_on_commit=False) as session:
            result = run_market_semantics_check(
                session,
                target_date=args.run_date,
                reference_version=args.reference_version,
            )
    except Exception:
        result = build_database_failure_result(
            target_date=args.run_date,
            reference_version=args.reference_version,
            error_code="G3_READ_FAILED",
        )
    finally:
        if engine is not None:
            engine.dispose()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
