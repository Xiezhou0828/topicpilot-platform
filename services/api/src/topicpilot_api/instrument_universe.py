"""Date-effective instrument universe and lifecycle eligibility contracts.

This module is deliberately independent of SQLAlchemy and provider adapters.
Callers supply the already validated identity and reference lifecycle rows, so
the same fail-closed rules are used by offline validation and G2 preflight.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date

KNOWN_LIFECYCLE_STATUSES = frozenset(
    {"ACTIVE", "LISTED", "DELISTED", "SUSPENDED", "TERMINATED"}
)
INELIGIBLE_LIFECYCLE_STATUSES = frozenset({"DELISTED", "SUSPENDED", "TERMINATED"})


class LifecycleValidationError(ValueError):
    """Raised when lifecycle metadata cannot safely determine eligibility."""


@dataclass(frozen=True)
class InstrumentLifecycle:
    status_code: str
    effective_from: date
    effective_to: date | None = None
    evidence_id: str | None = None


@dataclass(frozen=True)
class InstrumentUniverseRow:
    market_code: str
    instrument_code: str
    instrument_type: str
    is_active: bool
    valid_from: date | None = None
    valid_to: date | None = None
    market_is_active: bool = True
    market_valid_from: date | None = None
    market_valid_to: date | None = None
    lifecycle_events: tuple[InstrumentLifecycle, ...] = ()


@dataclass(frozen=True)
class InstrumentEligibility:
    eligible: bool
    reason_code: str


def _validate_range(
    *,
    valid_from: date | None,
    valid_to: date | None,
    label: str,
) -> None:
    if valid_from is not None and valid_to is not None and valid_from > valid_to:
        raise LifecycleValidationError(f"INVALID_{label.upper()}_VALID_RANGE")


def _date_in_range(
    run_date: date,
    *,
    effective_from: date,
    effective_to: date | None,
) -> bool:
    return effective_from <= run_date and (effective_to is None or run_date <= effective_to)


def evaluate_instrument_eligibility(
    row: InstrumentUniverseRow,
    run_date: date,
) -> InstrumentEligibility:
    """Return a deterministic eligibility decision or fail closed."""

    _validate_range(valid_from=row.valid_from, valid_to=row.valid_to, label="instrument")
    _validate_range(
        valid_from=row.market_valid_from,
        valid_to=row.market_valid_to,
        label="market",
    )
    if row.instrument_type != "EQUITY":
        return InstrumentEligibility(False, "INSTRUMENT_TYPE_NOT_ELIGIBLE")
    if not row.is_active:
        return InstrumentEligibility(False, "INSTRUMENT_INACTIVE")
    if not row.market_is_active:
        return InstrumentEligibility(False, "MARKET_INACTIVE")
    if row.valid_from is not None and run_date < row.valid_from:
        return InstrumentEligibility(False, "INSTRUMENT_NOT_YET_VALID")
    if row.valid_to is not None and run_date > row.valid_to:
        return InstrumentEligibility(False, "INSTRUMENT_VALIDITY_EXPIRED")
    if row.market_valid_from is not None and run_date < row.market_valid_from:
        return InstrumentEligibility(False, "MARKET_NOT_YET_VALID")
    if row.market_valid_to is not None and run_date > row.market_valid_to:
        return InstrumentEligibility(False, "MARKET_VALIDITY_EXPIRED")

    latest = resolve_lifecycle_status(row, run_date)
    if latest is not None and latest in INELIGIBLE_LIFECYCLE_STATUSES:
        return InstrumentEligibility(False, f"LIFECYCLE_{latest}")
    return InstrumentEligibility(True, "ELIGIBLE")


def resolve_lifecycle_status(
    row: InstrumentUniverseRow,
    run_date: date,
) -> str | None:
    """Return the latest evidenced lifecycle status effective on a date."""

    _validate_range(valid_from=row.valid_from, valid_to=row.valid_to, label="instrument")
    _validate_range(
        valid_from=row.market_valid_from,
        valid_to=row.market_valid_to,
        label="market",
    )
    applicable: list[InstrumentLifecycle] = []
    for event in row.lifecycle_events:
        if event.status_code not in KNOWN_LIFECYCLE_STATUSES:
            raise LifecycleValidationError(
                f"UNKNOWN_LIFECYCLE_STATUS:{row.market_code}:{row.instrument_code}:"
                f"{event.status_code}"
            )
        if not event.evidence_id:
            raise LifecycleValidationError(
                f"LIFECYCLE_EVIDENCE_ID_MISSING:{row.market_code}:{row.instrument_code}"
            )
        _validate_range(
            valid_from=event.effective_from,
            valid_to=event.effective_to,
            label="lifecycle",
        )
        if _date_in_range(
            run_date,
            effective_from=event.effective_from,
            effective_to=event.effective_to,
        ):
            applicable.append(event)

    if not applicable:
        return None
    latest = max(applicable, key=lambda event: (event.effective_from, event.evidence_id or ""))
    return latest.status_code


def is_instrument_eligible_on_date(row: InstrumentUniverseRow, run_date: date) -> bool:
    """Boolean convenience wrapper around the fail-closed eligibility contract."""

    return evaluate_instrument_eligibility(row, run_date).eligible


def build_date_effective_instrument_universe(
    rows: Iterable[InstrumentUniverseRow],
    run_date: date,
    *,
    expected_markets: Iterable[str] = ("TPE", "TWO"),
) -> Mapping[str, tuple[str, ...]]:
    """Build sorted eligible identities grouped by market.

    Duplicate identities and identities outside the canonical market set are
    rejected rather than silently deduplicated.
    """

    market_set = tuple(expected_markets)
    if len(market_set) != len(set(market_set)):
        raise LifecycleValidationError("DUPLICATE_EXPECTED_MARKETS")
    grouped: dict[str, set[str]] = defaultdict(set)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        identity = (row.market_code, row.instrument_code)
        if row.market_code not in market_set:
            raise LifecycleValidationError(f"UNEXPECTED_MARKET:{row.market_code}")
        if identity in seen:
            raise LifecycleValidationError(
                f"DUPLICATE_INSTRUMENT_IDENTITY:{row.market_code}:{row.instrument_code}"
            )
        seen.add(identity)
        if evaluate_instrument_eligibility(row, run_date).eligible:
            grouped[row.market_code].add(row.instrument_code)
    return {market: tuple(sorted(grouped.get(market, set()))) for market in market_set}


__all__ = [
    "KNOWN_LIFECYCLE_STATUSES",
    "InstrumentEligibility",
    "InstrumentLifecycle",
    "InstrumentUniverseRow",
    "LifecycleValidationError",
    "build_date_effective_instrument_universe",
    "evaluate_instrument_eligibility",
    "is_instrument_eligible_on_date",
    "resolve_lifecycle_status",
]
