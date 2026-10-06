"""Minimum-sufficient operational readiness for official EOD data.

The exchange does not need to promise that a daily response can never be
revised.  This contract separates temporary publication lag from evidence
that is materially invalid or contradictory, while keeping the existing
fail-closed data-integrity checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class OperationalReadiness(StrEnum):
    """Primary state used by the bounded EOD readiness decision."""

    READY = "READY"
    WAIT = "WAIT"
    BLOCKED = "BLOCKED"


WAIT_PROVIDER_NOT_READY = "WAIT_PROVIDER_NOT_READY"
WAIT_PROVIDER_PUBLICATION_LAG = "WAIT_PROVIDER_PUBLICATION_LAG"
WAIT_PROVIDER_TEMPORARY_UNAVAILABLE = "WAIT_PROVIDER_TEMPORARY_UNAVAILABLE"
BLOCKED_PROVIDER_DATE_AUTHORITY = "BLOCKED_PROVIDER_DATE_AUTHORITY"
BLOCKED_PROVIDER_EVIDENCE = "BLOCKED_PROVIDER_EVIDENCE"
BLOCKED_AUTHORITY_CONFLICT = "BLOCKED_AUTHORITY_CONFLICT"
BLOCKED_REQUIRED_DATA = "BLOCKED_REQUIRED_DATA"

_WAITING_PROVIDER_CODES = frozenset(
    {
        "EXCHANGE_NOT_READY",
        "EXCHANGE_EMPTY_PAYLOAD",
        "PROVIDER_REQUEST_FAILED",
    }
)


@dataclass(frozen=True)
class ReadinessDecision:
    """A small, serializable decision for one official EOD evidence path."""

    state: OperationalReadiness
    reason_code: str

    @property
    def ready(self) -> bool:
        return self.state is OperationalReadiness.READY

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "state": self.state.value,
            "reasonCode": self.reason_code,
            "ready": self.ready,
        }


def classify_eod_readiness(
    *,
    source_official: bool,
    retrieval_succeeded: bool,
    target_session: date,
    served_session: date | None,
    payload_valid: bool,
    required_rows_present: bool,
    required_ohlcv_parseable: bool,
    minimum_coverage: bool,
    explicit_not_ready: bool = False,
    authority_conflict: bool = False,
    previous_session: date | None = None,
    temporary_retrieval_failure: bool = False,
) -> ReadinessDecision:
    """Evaluate the minimum operational EOD contract.

    ``explicit_finality`` is intentionally absent.  Later source correction is
    handled by the existing append-only correction/supersession path.
    """

    if not source_official:
        return ReadinessDecision(OperationalReadiness.BLOCKED, BLOCKED_PROVIDER_EVIDENCE)
    if authority_conflict:
        return ReadinessDecision(OperationalReadiness.BLOCKED, BLOCKED_AUTHORITY_CONFLICT)
    if temporary_retrieval_failure or not retrieval_succeeded or explicit_not_ready:
        return ReadinessDecision(OperationalReadiness.WAIT, WAIT_PROVIDER_NOT_READY)
    if served_session != target_session:
        if previous_session is not None and served_session == previous_session:
            return ReadinessDecision(
                OperationalReadiness.WAIT,
                WAIT_PROVIDER_PUBLICATION_LAG,
            )
        return ReadinessDecision(
            OperationalReadiness.BLOCKED,
            BLOCKED_PROVIDER_DATE_AUTHORITY,
        )
    if not payload_valid or not required_rows_present or not required_ohlcv_parseable:
        return ReadinessDecision(OperationalReadiness.BLOCKED, BLOCKED_REQUIRED_DATA)
    if not minimum_coverage:
        return ReadinessDecision(OperationalReadiness.BLOCKED, BLOCKED_REQUIRED_DATA)
    return ReadinessDecision(OperationalReadiness.READY, "OPERATIONAL_EOD_READY")


def classify_provider_error(
    error_code: str,
    *,
    target_session: date | None = None,
    served_session: date | None = None,
    previous_session: date | None = None,
) -> ReadinessDecision:
    """Map a sanitized provider error to READY/WAIT/BLOCKED semantics."""

    if error_code == "PROVIDER_DATE_MISMATCH":
        if (
            target_session is not None
            and previous_session is not None
            and served_session == previous_session
            and previous_session < target_session
        ):
            return ReadinessDecision(OperationalReadiness.WAIT, WAIT_PROVIDER_PUBLICATION_LAG)
        return ReadinessDecision(
            OperationalReadiness.BLOCKED,
            BLOCKED_PROVIDER_DATE_AUTHORITY,
        )
    if error_code in {"EXCHANGE_NOT_READY", "EXCHANGE_EMPTY_PAYLOAD"}:
        return ReadinessDecision(OperationalReadiness.WAIT, WAIT_PROVIDER_NOT_READY)
    if error_code == "PROVIDER_REQUEST_FAILED":
        return ReadinessDecision(
            OperationalReadiness.WAIT,
            WAIT_PROVIDER_TEMPORARY_UNAVAILABLE,
        )
    return ReadinessDecision(OperationalReadiness.BLOCKED, BLOCKED_PROVIDER_EVIDENCE)


def parse_reported_session(value: object) -> date | None:
    """Parse an exchange ISO/ROC date without guessing a missing date."""

    text = str(value or "").strip().replace("/", "-")
    try:
        if len(text) == 8 and text.isdigit():
            return date.fromisoformat(f"{text[:4]}-{text[4:6]}-{text[6:]}")
        if len(text) == 7 and text.isdigit():
            return date(int(text[:3]) + 1911, int(text[3:5]), int(text[5:]))
        return date.fromisoformat(text)
    except ValueError:
        return None


__all__ = [
    "BLOCKED_AUTHORITY_CONFLICT",
    "BLOCKED_PROVIDER_DATE_AUTHORITY",
    "BLOCKED_PROVIDER_EVIDENCE",
    "BLOCKED_REQUIRED_DATA",
    "WAIT_PROVIDER_NOT_READY",
    "WAIT_PROVIDER_PUBLICATION_LAG",
    "WAIT_PROVIDER_TEMPORARY_UNAVAILABLE",
    "OperationalReadiness",
    "ReadinessDecision",
    "classify_eod_readiness",
    "classify_provider_error",
    "parse_reported_session",
]
