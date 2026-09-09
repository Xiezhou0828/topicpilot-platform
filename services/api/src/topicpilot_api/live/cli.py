"""Command-line entry point for live runtime operations."""

from __future__ import annotations

import argparse
import logging
import signal
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.live.collector import LiveCollector
from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.daily_forward import DailyForwardRunner
from topicpilot_api.live.logging import log_event
from topicpilot_api.live.orchestrator import PersistentQuoteWorker
from topicpilot_api.live.persistence import LiveRepository
from topicpilot_api.live.post_close import PostClosePreconditionError, PostCloseUpdater
from topicpilot_api.live.scheduler import LiveScheduler
from topicpilot_api.live.session import MarketSessionClock
from topicpilot_api.market_data.registry import build_live_provider_router


def _symbols_argument(value: str) -> tuple[str, ...]:
    """Parse a comma-separated targeted symbol list for post-close recovery."""

    symbols = tuple(item.strip() for item in value.split(",") if item.strip())
    if not symbols:
        raise argparse.ArgumentTypeError("at least one symbol is required")
    for symbol in symbols:
        if (
            symbol.count(":") > 1
            or symbol.startswith(":")
            or symbol.endswith(":")
        ):
            raise argparse.ArgumentTypeError(
                "symbols must be CODE or MARKET:CODE values"
            )
    return symbols


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("auto", "intraday", "post-close", "daily-forward"),
        default="auto",
    )
    parser.add_argument("--once", action="store_true", help="execute one decision and exit")
    parser.add_argument(
        "--run-date",
        type=date.fromisoformat,
        help=(
            "override the official POST_CLOSE trading date (ISO date; "
            "required for targeted symbols)"
        ),
    )
    parser.add_argument(
        "--recover",
        action="store_true",
        help="explicitly rerun a terminal FAILED/PARTIAL POST_CLOSE date",
    )
    parser.add_argument(
        "--symbols",
        "--codes",
        dest="symbols",
        type=_symbols_argument,
        metavar="CODE[,CODE...]",
        help=(
            "capture only selected post-close symbols; use CODE or MARKET:CODE "
            "(for example TWO:1584,TWO:6129)"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print scheduler decision without provider call",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.symbols is not None and args.mode != "post-close":
        parser.error("--symbols requires --mode post-close")
    if args.symbols is not None and not args.once:
        parser.error("--symbols requires --once")
    if args.symbols is not None and args.run_date is None:
        parser.error("--symbols requires --run-date YYYY-MM-DD")
    if args.recover and args.run_date is None:
        raise SystemExit("--recover requires --run-date YYYY-MM-DD")
    if args.recover and args.mode != "post-close":
        raise SystemExit("--recover requires --mode post-close")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    config = LiveRuntimeConfig.from_environment()
    scheduler_clock = MarketSessionClock(
        config.timezone_name,
        config.session_open,
        config.session_close,
        config.closed_dates,
    )
    decision = args.mode.upper().replace("-", "_")
    if decision == "DAILY_FORWARD":
        decision = "POST_CLOSE"
    if decision == "AUTO":
        state = scheduler_clock.status()
        decision = (
            "INTRADAY"
            if state.state == "OPEN"
            else "POST_CLOSE"
            if state.reason not in {"WEEKEND", "CONFIGURED_CLOSED_DATE"}
            and state.local_time.time() >= scheduler_clock.close_time
            else "WAIT"
        )
    log_event(
        logging.getLogger("topicpilot.live.cli"),
        "scheduler_decision",
        mode=decision,
        config=config.as_dict(),
    )
    if args.dry_run:
        return 0

    provider_router = build_live_provider_router(config)
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    with Session(engine, expire_on_commit=False) as session:
        repository = LiveRepository(session, config)
        # POST_CLOSE derives its date-effective universe before its first
        # write. Refreshing the generic active universe here would mutate
        # tracking state before that precondition and could reintroduce a
        # date-ineligible identity such as TPE:6806.
        if decision != "POST_CLOSE":
            repository.refresh_tracking_universe()
            session.commit()
        collector = LiveCollector(repository, provider_router, config)
        post_close = PostCloseUpdater(session, config)
        daily_forward = DailyForwardRunner(session, config, updater=post_close)
        worker = PersistentQuoteWorker(provider_router, config=config)
        if args.recover or args.symbols is not None:
            def post_close_runner() -> object:
                return post_close.run_once(
                    run_date=args.run_date,
                    allow_terminal_recovery=args.recover,
                    target_symbols=args.symbols,
                    execution_mode="RECOVERY" if args.recover else "MANUAL",
                )
        else:
            def post_close_runner() -> object:
                return daily_forward.run_once(
                    run_date=args.run_date,
                    replay=args.run_date is not None,
                    execution_mode="MANUAL" if args.once else "SCHEDULED",
                )
        scheduler = LiveScheduler(
            collector,
            config,
            worker=worker,
            post_close_runner=post_close_runner,
        )
        try:
            if args.once:
                if decision == "INTRADAY":
                    worker.start()
                result = scheduler.run_once(decision, enforce_session=decision == "INTRADAY")
                result_payload = (
                    result.to_dict() if callable(getattr(result, "to_dict", None)) else result
                )
                log_event(
                    logging.getLogger("topicpilot.live.cli"),
                    "scheduler_complete",
                    result=result_payload,
                    providerHealth=provider_router.health_snapshot(),
                )
                return (
                    0
                    if result is None or result.status in {"SUCCESS", "PARTIAL", "MARKET_CLOSED"}
                    else 1
                )

            stop = __import__("threading").Event()
            signal.signal(signal.SIGTERM, lambda *_: stop.set())
            if hasattr(signal, "SIGINT"):
                signal.signal(signal.SIGINT, lambda *_: stop.set())
            scheduler.run_forever(stop)
        except PostClosePreconditionError as exc:
            log_event(
                logging.getLogger("topicpilot.live.cli"),
                "post_close_precondition_failed",
                errorCode=exc.code,
            )
            return 1
        finally:
            worker.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
