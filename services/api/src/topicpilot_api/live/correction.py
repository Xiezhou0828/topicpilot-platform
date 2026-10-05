"""Explicit, bounded correction/replay orchestration for daily publication."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from topicpilot_api.lifecycle_formal_publication import FormalLifecyclePublisher

from .config import LiveRuntimeConfig
from .receipt import (
    append_correction_receipt,
    receipt_to_dict,
)


@dataclass(frozen=True)
class CorrectionReplayResult:
    status: str
    earliest_affected_date: date
    replay_end_date: date
    execution_key: str
    replay: dict[str, Any]
    receipt: dict[str, Any]


class DailyFormalCorrectionReplayer:
    """Run an explicitly requested path-dependent Lifecycle replay.

    This service is intentionally never called by the scheduler.  It replays
    only the formal Lifecycle chain from the earliest affected date through a
    caller-supplied bound and records a superseding immutable receipt.  Home
    is not part of the correction path.
    """

    def __init__(
        self,
        session: Session,
        config: LiveRuntimeConfig,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.session = session
        self.config = config
        self.clock = clock or (lambda: datetime.now(UTC))

    def run_once(
        self,
        *,
        earliest_affected_date: date,
        replay_end_date: date,
        reason_code: str,
        execution_key: str | None = None,
    ) -> CorrectionReplayResult:
        if replay_end_date < earliest_affected_date:
            raise ValueError("replay_end_date must be on or after earliest_affected_date")
        if not reason_code.strip():
            raise ValueError("reason_code is required")

        stable_key = execution_key or (
            f"correction:{self.config.reference_data_version}:"
            f"{self.config.calendar_code}:{earliest_affected_date.isoformat()}:"
            f"{replay_end_date.isoformat()}:{reason_code.strip()}"
        )
        replay = FormalLifecyclePublisher(self.session).run_replay(
            persist=True,
            from_date=earliest_affected_date,
            to_date=replay_end_date,
        )
        receipt = append_correction_receipt(
            self.session,
            config=self.config,
            trading_date=replay_end_date,
            earliest_affected_date=earliest_affected_date,
            replay_end_date=replay_end_date,
            execution_key=stable_key,
            replay_result=replay,
            reason_code=reason_code.strip(),
            now=self.clock(),
            commit=True,
        )
        status = (
            "CORRECTION_COMPLETE"
            if replay.get("status") == "SUCCESS"
            else "CORRECTION_FAILED"
        )
        return CorrectionReplayResult(
            status=status,
            earliest_affected_date=earliest_affected_date,
            replay_end_date=replay_end_date,
            execution_key=stable_key,
            replay=replay,
            receipt=receipt_to_dict(receipt),
        )


__all__ = ["CorrectionReplayResult", "DailyFormalCorrectionReplayer"]
