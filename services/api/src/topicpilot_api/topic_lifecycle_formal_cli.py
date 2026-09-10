"""Operator entrypoint for Lifecycle V1.3 formal publication."""

from __future__ import annotations

import argparse
import json
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.lifecycle_formal_publication import FormalLifecyclePublisher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--date", type=date.fromisoformat, help="one formal trading date")
    group.add_argument(
        "--replay",
        action="store_true",
        help="replay formal Topic Snapshot dates from the A9 authority boundary",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="evaluate and report without publishing formal rows",
    )
    parser.add_argument("--database-url", help="explicit protected database URL")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    engine = create_engine(args.database_url or settings.database_url, pool_pre_ping=True)
    with Session(engine, expire_on_commit=False, autoflush=False) as session:
        publisher = FormalLifecyclePublisher(session)
        if args.date:
            result = publisher.run_once(
                evaluation_date=args.date,
                persist=not args.dry_run,
            ).as_dict()
        else:
            result = publisher.run_replay(persist=not args.dry_run)
    print(json.dumps(result, ensure_ascii=False, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
