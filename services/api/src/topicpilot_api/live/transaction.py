"""Safe transaction recovery for long-lived live-runtime sessions."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .logging import log_event


@dataclass(frozen=True)
class SessionRecoveryResult:
    """Outcome of recovering a session after a failed job transaction."""

    rollback_attempted: bool
    rollback_succeeded: bool
    close_attempted: bool
    close_succeeded: bool
    session_usable: bool
    rollback_error: str | None = None
    close_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rollbackAttempted": self.rollback_attempted,
            "rollbackSucceeded": self.rollback_succeeded,
            "sessionCloseAttempted": self.close_attempted,
            "sessionCloseSucceeded": self.close_succeeded,
            "sessionUsable": self.session_usable,
            "rollbackErrorType": self.rollback_error,
            "sessionCloseErrorType": self.close_error,
        }


class SessionRecoveryError(RuntimeError):
    """Raised only when rollback and session reset both fail."""

    def __init__(
        self,
        job_name: str,
        original_exception: Exception,
        recovery: SessionRecoveryResult,
    ) -> None:
        self.job_name = job_name
        self.original_exception = original_exception
        self.recovery = recovery
        super().__init__(
            f"{job_name} failed and its database session could not be recovered "
            f"after {type(original_exception).__name__}"
        )


def recover_session(
    session: object | None,
    *,
    job_name: str,
    original_exception: Exception,
    logger: logging.Logger | None = None,
    run_id: object | None = None,
    rollback: Callable[[], object] | None = None,
) -> SessionRecoveryResult:
    """Rollback and reset a failed session without hiding the original error.

    ``Session.close()`` is a reusable SQLAlchemy session reset: it releases the
    current transaction/connection and expunges state while allowing the owner
    to begin a clean transaction on the next job.  If rollback itself fails,
    close is the recovery fallback.  If neither operation succeeds, callers
    must fail closed rather than continue with unknown transaction state.
    """

    logger = logger or logging.getLogger("topicpilot.live.transaction")
    rollback_fn = rollback or getattr(session, "rollback", None)
    close_fn = getattr(session, "close", None)
    rollback_attempted = callable(rollback_fn)
    rollback_succeeded = False
    close_attempted = callable(close_fn)
    close_succeeded = False
    rollback_error: str | None = None
    close_error: str | None = None

    if rollback_attempted:
        try:
            rollback_fn()
            rollback_succeeded = True
        except Exception as exc:  # pragma: no cover - exact DBAPI errors vary
            rollback_error = type(exc).__name__
    else:
        rollback_error = "ROLLBACK_UNAVAILABLE"

    if close_attempted:
        try:
            close_fn()
        except Exception as exc:  # pragma: no cover - exact DBAPI errors vary
            close_error = type(exc).__name__
        else:
            close_succeeded = True

    # A session-less scheduler fake is valid for non-DB tests. A real session
    # is usable when rollback succeeds or close resets it after rollback fails.
    session_usable = session is None or rollback_succeeded or close_succeeded
    recovery = SessionRecoveryResult(
        rollback_attempted=rollback_attempted,
        rollback_succeeded=rollback_succeeded,
        close_attempted=close_attempted,
        close_succeeded=close_succeeded,
        session_usable=session_usable,
        rollback_error=rollback_error,
        close_error=close_error,
    )
    fields: dict[str, Any] = {
        "jobName": job_name,
        "exceptionType": type(original_exception).__name__,
        "recoveryResult": "USABLE" if session_usable else "FAILED",
        **recovery.to_dict(),
    }
    if run_id is not None:
        fields["runId"] = str(run_id)
    log_event(logger, "live_session_recovery", **fields)
    return recovery


__all__ = ["SessionRecoveryError", "SessionRecoveryResult", "recover_session"]
