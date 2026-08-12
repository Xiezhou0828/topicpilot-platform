"""Operator entrypoint for deterministic V2 lifecycle shadow evaluation."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.orm import TopicSnapshot
from topicpilot_api.topic_lifecycle_calibration import (
    build_review_payload,
    export_csv,
    export_json,
    export_markdown,
    load_calibration_records,
)
from topicpilot_api.topic_lifecycle_engine import TopicLifecycleEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=date.fromisoformat, help="one trading date (YYYY-MM-DD)")
    parser.add_argument(
        "--replay",
        action="store_true",
        help="replay every available formal topic snapshot date in ascending order",
    )
    parser.add_argument("--topic", help="limit calibration output to one topic slug")
    parser.add_argument(
        "--export",
        action="store_true",
        help="export the persisted shadow evidence using the calibration review contract",
    )
    parser.add_argument(
        "--format",
        choices=("json", "csv", "markdown"),
        default="json",
        help="calibration export format",
    )
    parser.add_argument("--summary", action="store_true", help="include replay summary in export")
    parser.add_argument(
        "--representatives",
        action="store_true",
        help="include deterministic representative PM review cases",
    )
    parser.add_argument("--output", type=Path, help="write export to a file instead of stdout")
    parser.add_argument("--database-url", help="explicit protected database URL")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.date and not args.replay:
        raise SystemExit("provide --date or --replay")
    settings = get_settings()
    engine = create_engine(args.database_url or settings.database_url, pool_pre_ping=True)
    with Session(engine, expire_on_commit=False, autoflush=False) as session:
        runner = TopicLifecycleEngine(session)
        evaluated_dates: list[date] = []
        if args.date:
            result = runner.run_once(evaluation_date=args.date)
            evaluated_dates = [args.date] if result.get("status") == "SUCCESS" else []
        else:
            dates = list(
                session.scalars(
                    select(TopicSnapshot.snapshot_date)
                    .distinct()
                    .order_by(TopicSnapshot.snapshot_date)
                )
            )
            result = {
                "status": "SUCCESS" if dates else "BLOCKED_BY_DATA",
                "evaluationMode": "SHADOW",
                "dates": [runner.run_once(evaluation_date=item) for item in dates],
            }
            evaluated_dates = dates
        if args.export or args.summary or args.representatives or args.format != "json":
            records = load_calibration_records(
                session,
                evaluation_dates=evaluated_dates,
                topic_key=args.topic,
            )
            payload = build_review_payload(
                records,
                include_representatives=args.representatives or args.format == "markdown",
            )
            if args.format == "csv":
                output = export_csv(records)
            elif args.format == "markdown":
                output = export_markdown(payload)
            else:
                output = export_json(payload)
        else:
            output = json.dumps(result, ensure_ascii=False, default=str, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output.rstrip() + "\n", encoding="utf-8", newline="\n")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
