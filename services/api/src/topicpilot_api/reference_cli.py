"""Operator command for a read-only ``tw-reference-v1`` preflight."""

from __future__ import annotations

import argparse
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.market_data.registry import canonical_daily_market_codes
from topicpilot_api.reference_check import inspect_reference_preflight


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-version", default=None)
    parser.add_argument("--session-code", default=None)
    parser.add_argument("--calendar-code", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = LiveRuntimeConfig.from_environment()
    version = args.reference_version or config.reference_data_version
    session_code = args.session_code or config.session_code
    calendar_code = args.calendar_code or config.calendar_code
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            result = inspect_reference_preflight(
                session,
                requested_version=version,
                expected_market_codes=canonical_daily_market_codes(),
                required_session_code=session_code,
                required_calendar_code=calendar_code,
            )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["referenceLoadStatus"] == "READY" else 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
