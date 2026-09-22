"""Read-only coverage audit for the canonical historical OHLCV surface.

The audit consumes the canonical daily projection and reference authority.  It
does not fetch providers, write a database row, or derive Topic/Score/Grade/
Lifecycle/Opportunity history.  A missing row is classified from effective
identity, market-calendar, and lifecycle evidence; it is never forward-filled.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings

MAX_AUDIT_DAYS = 3660
NO_TRADE_CODES = frozenset(
    {"SUSPENDED", "NO_TRADE", "EXCHANGE_CONFIRMED_NO_DATA", "DELISTED", "TERMINATED"}
)
LIFECYCLE_CODES = frozenset({"SUSPENDED", "DELISTED", "TERMINATED"})
MARKET_NO_SESSION_CODES = frozenset({"HOLIDAY", "SUSPENDED"})


class CoverageAuditError(ValueError):
    """Raised for an unsafe or incomplete canonical audit request."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class InstrumentIdentity:
    instrument_id: str
    instrument_code: str
    market_code: str
    calendar_code: str | None
    valid_from: date | None
    valid_to: date | None


@dataclass(frozen=True)
class LifecycleEvent:
    instrument_id: str
    status_code: str
    effective_from: date
    effective_to: date | None


@dataclass(frozen=True)
class CalendarException:
    calendar_code: str
    calendar_date: date
    date_kind: str


@dataclass(frozen=True)
class AuditArtifacts:
    coverage_by_date: tuple[dict[str, Any], ...]
    coverage_by_instrument: tuple[dict[str, Any], ...]
    gap_classification: tuple[dict[str, Any], ...]
    summary: dict[str, Any]


def _parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CoverageAuditError("INVALID_DATE", f"{label} must be YYYY-MM-DD") from exc


def _validate_window(requested_from: date, requested_to: date) -> None:
    if requested_to < requested_from:
        raise CoverageAuditError("INVALID_DATE_WINDOW", "to precedes from")
    if (requested_to - requested_from).days + 1 > MAX_AUDIT_DAYS:
        raise CoverageAuditError(
            "AUDIT_WINDOW_TOO_LARGE", f"audit window cannot exceed {MAX_AUDIT_DAYS} days"
        )


def _date_range(requested_from: date, requested_to: date) -> tuple[date, ...]:
    return tuple(
        requested_from + timedelta(days=offset)
        for offset in range((requested_to - requested_from).days + 1)
    )


def _as_bool(value: object) -> bool:
    return bool(value) if value is not None else False


def _in_effective_range(day: date, valid_from: date | None, valid_to: date | None) -> bool:
    return (valid_from is None or day >= valid_from) and (valid_to is None or day <= valid_to)


def _active_lifecycle(
    instrument_id: str, day: date, events_by_instrument: dict[str, tuple[LifecycleEvent, ...]]
) -> LifecycleEvent | None:
    candidates = [
        event
        for event in events_by_instrument.get(instrument_id, ())
        if event.effective_from <= day
        and (event.effective_to is None or day <= event.effective_to)
    ]
    return max(candidates, key=lambda event: event.effective_from) if candidates else None


def _calendar_kind(
    identity: InstrumentIdentity,
    day: date,
    calendar_by_code: dict[str, dict[date, str]],
) -> str | None:
    if day.weekday() >= 5:
        return "WEEKEND"
    if identity.calendar_code is None:
        return None
    return calendar_by_code.get(identity.calendar_code, {}).get(day)


def _observation_state(row: dict[str, Any]) -> str:
    if row.get("close") is not None:
        return "OBSERVED_PRICED"
    if _as_bool(row.get("covered")) or row.get("status_code") in NO_TRADE_CODES:
        return "OBSERVED_COVERED_NO_TRADE"
    return "OBSERVED_UNEXPLAINED_NO_DATA"


def _missing_state(
    identity: InstrumentIdentity,
    day: date,
    events_by_instrument: dict[str, tuple[LifecycleEvent, ...]],
    calendar_by_code: dict[str, dict[date, str]],
) -> str:
    if not _in_effective_range(day, identity.valid_from, identity.valid_to):
        return "INSTRUMENT_NOT_LISTED"
    lifecycle = _active_lifecycle(identity.instrument_id, day, events_by_instrument)
    if lifecycle is not None and lifecycle.status_code in LIFECYCLE_CODES:
        return f"LIFECYCLE_{lifecycle.status_code}"
    calendar_kind = _calendar_kind(identity, day, calendar_by_code)
    if calendar_kind in MARKET_NO_SESSION_CODES or calendar_kind == "WEEKEND":
        return "MARKET_NO_SESSION"
    return "NO_CANONICAL_OBSERVATION"


def build_audit_artifacts(
    *,
    requested_from: date,
    requested_to: date,
    identities: tuple[InstrumentIdentity, ...],
    observations: tuple[dict[str, Any], ...],
    lifecycle_events: tuple[LifecycleEvent, ...] = (),
    calendar_exceptions: tuple[CalendarException, ...] = (),
) -> AuditArtifacts:
    """Build deterministic audit rows from already-read canonical evidence."""

    _validate_window(requested_from, requested_to)
    identities_by_id = {item.instrument_id: item for item in identities}
    events_by_instrument: dict[str, list[LifecycleEvent]] = defaultdict(list)
    for event in lifecycle_events:
        events_by_instrument[event.instrument_id].append(event)
    frozen_events = {
        instrument_id: tuple(sorted(events, key=lambda item: item.effective_from))
        for instrument_id, events in events_by_instrument.items()
    }
    calendar_by_code: dict[str, dict[date, str]] = defaultdict(dict)
    for item in calendar_exceptions:
        calendar_by_code[item.calendar_code][item.calendar_date] = item.date_kind

    observations_by_key: dict[tuple[str, date], dict[str, Any]] = {}
    for row in observations:
        instrument_id = str(row["instrument_id"])
        trading_date = row["trade_date"]
        if isinstance(trading_date, str):
            trading_date = date.fromisoformat(trading_date)
        if instrument_id not in identities_by_id:
            raise CoverageAuditError(
                "UNKNOWN_INSTRUMENT", f"observation references {instrument_id}"
            )
        key = (instrument_id, trading_date)
        if key in observations_by_key:
            raise CoverageAuditError(
                "DUPLICATE_CANONICAL_KEY",
                f"multiple canonical rows for {instrument_id} on {trading_date.isoformat()}",
            )
        observations_by_key[key] = dict(row)

    expected_by_date: dict[date, int] = Counter()
    priced_by_date: dict[date, int] = Counter()
    covered_by_date: dict[date, int] = Counter()
    observed_by_date: dict[date, int] = Counter()
    no_session_by_date: dict[date, int] = Counter()
    gaps: list[dict[str, Any]] = []
    instrument_rows: list[dict[str, Any]] = []
    dates = _date_range(requested_from, requested_to)

    for identity in sorted(identities, key=lambda item: (item.market_code, item.instrument_code)):
        instrument_observations = {
            day: row
            for (instrument_id, day), row in observations_by_key.items()
            if instrument_id == identity.instrument_id
        }
        counters: Counter[str] = Counter()
        first_observation: date | None = None
        last_observation: date | None = None
        source_codes: set[str] = set()
        for day in dates:
            effective = _in_effective_range(day, identity.valid_from, identity.valid_to)
            calendar_kind = _calendar_kind(identity, day, calendar_by_code)
            lifecycle = _active_lifecycle(identity.instrument_id, day, frozen_events)
            expected_session = (
                effective
                and lifecycle is None
                and calendar_kind not in (*MARKET_NO_SESSION_CODES, "WEEKEND")
            )
            row = instrument_observations.get(day)
            if expected_session:
                expected_by_date[day] += 1
            if row is not None:
                state = _observation_state(row)
                counters[state] += 1
                observed_by_date[day] += 1
                if row.get("close") is not None:
                    priced_by_date[day] += 1
                if _as_bool(row.get("covered")) or row.get("status_code") in NO_TRADE_CODES:
                    covered_by_date[day] += 1
                source_code = row.get("source_code")
                if source_code:
                    source_codes.add(str(source_code))
                first_observation = (
                    day if first_observation is None else min(first_observation, day)
                )
                last_observation = day if last_observation is None else max(last_observation, day)
                if expected_session and state == "OBSERVED_UNEXPLAINED_NO_DATA":
                    gaps.append(
                        _gap_row(identity, day, state, row=row, expected_session=True)
                    )
            elif expected_session:
                expected_by_date[day] += 1
                state = _missing_state(identity, day, frozen_events, calendar_by_code)
                counters[state] += 1
                gaps.append(_gap_row(identity, day, state, row=None, expected_session=True))
            elif lifecycle is not None and lifecycle.status_code in LIFECYCLE_CODES:
                counters[f"LIFECYCLE_{lifecycle.status_code}"] += 1
                gaps.append(
                    _gap_row(
                        identity,
                        day,
                        f"LIFECYCLE_{lifecycle.status_code}",
                        row=None,
                        expected_session=False,
                    )
                )
            elif effective:
                counters["MARKET_NO_SESSION"] += 1
                no_session_by_date[day] += 1
                gaps.append(
                    _gap_row(
                        identity, day, "MARKET_NO_SESSION", row=None, expected_session=False
                    )
                )
            else:
                counters["INSTRUMENT_NOT_LISTED"] += 1
                gaps.append(
                    _gap_row(
                        identity,
                        day,
                        "INSTRUMENT_NOT_LISTED",
                        row=None,
                        expected_session=False,
                    )
                )

        expected_sessions = sum(
            1
            for day in dates
            if _in_effective_range(day, identity.valid_from, identity.valid_to)
            and _active_lifecycle(identity.instrument_id, day, frozen_events) is None
            and _calendar_kind(identity, day, calendar_by_code)
            not in (*MARKET_NO_SESSION_CODES, "WEEKEND")
        )
        priced_count = counters["OBSERVED_PRICED"]
        covered_count = priced_count + counters["OBSERVED_COVERED_NO_TRADE"]
        missing_count = sum(
            count
            for state, count in counters.items()
            if state in {"NO_CANONICAL_OBSERVATION", "OBSERVED_UNEXPLAINED_NO_DATA"}
        )
        gap_candidates = {
            state: count
            for state, count in counters.items()
            if state not in {"OBSERVED_PRICED", "OBSERVED_COVERED_NO_TRADE", "MARKET_NO_SESSION"}
            and count
        }
        primary_gap = max(
            gap_candidates, key=lambda state: (-gap_candidates[state], state), default="NONE"
        )
        instrument_rows.append(
            {
                "market_code": identity.market_code,
                "instrument_code": identity.instrument_code,
                "instrument_id": identity.instrument_id,
                "requested_from": requested_from.isoformat(),
                "requested_to": requested_to.isoformat(),
                "expected_session_count": expected_sessions,
                "observed_count": sum(
                    counters[state]
                    for state in (
                        "OBSERVED_PRICED",
                        "OBSERVED_COVERED_NO_TRADE",
                        "OBSERVED_UNEXPLAINED_NO_DATA",
                    )
                ),
                "priced_count": priced_count,
                "covered_count": covered_count,
                "missing_count": missing_count,
                "market_no_session_count": counters["MARKET_NO_SESSION"],
                "first_observation": first_observation.isoformat() if first_observation else None,
                "last_observation": last_observation.isoformat() if last_observation else None,
                "source_codes": ";".join(sorted(source_codes)),
                "ma20_ready": "YES" if priced_count >= 20 else "NO",
                "ma60_ready": "YES" if priced_count >= 60 else "NO",
                "coverage_state": (
                    "NO_EXPECTED_SESSIONS"
                    if expected_sessions == 0
                    else "COMPLETE"
                    if missing_count == 0
                    else "PARTIAL"
                    if covered_count
                    else "EMPTY"
                ),
                "primary_gap_class": primary_gap,
            }
        )

    date_rows: list[dict[str, Any]] = []
    for day in dates:
        expected = expected_by_date[day]
        observed = observed_by_date[day]
        covered = covered_by_date[day]
        priced = priced_by_date[day]
        missing = max(expected - covered, 0)
        date_rows.append(
            {
                "trade_date": day.isoformat(),
                "expected_instrument_count": expected,
                "observed_instrument_count": observed,
                "priced_instrument_count": priced,
                "covered_instrument_count": covered,
                "missing_instrument_count": missing,
                "market_no_session_instrument_count": no_session_by_date[day],
                "coverage_state": (
                    "NO_MARKET_SESSION" if expected == 0 and no_session_by_date[day] else
                    "COMPLETE" if missing == 0 else
                    "PARTIAL" if covered else "EMPTY"
                ),
            }
        )

    gap_rows = tuple(
        sorted(
            gaps,
            key=lambda row: (row["market_code"], row["instrument_code"], row["trade_date"]),
        )
    )
    gap_counts = Counter(row["gap_class"] for row in gap_rows)
    summary = {
        "requested_from": requested_from.isoformat(),
        "requested_to": requested_to.isoformat(),
        "identity_count": len(identities),
        "observation_count": len(observations),
        "coverage_by_date_rows": len(date_rows),
        "coverage_by_instrument_rows": len(instrument_rows),
        "gap_rows": len(gap_rows),
        "gap_counts": dict(sorted(gap_counts.items())),
        "raw_data_foundation_only": True,
        "formal_derived_history_read": False,
        "adjustment_state_policy": "UNKNOWN_UNLESS_AUTHORIZED",
    }
    return AuditArtifacts(tuple(date_rows), tuple(instrument_rows), gap_rows, summary)


def _gap_row(
    identity: InstrumentIdentity,
    day: date,
    gap_class: str,
    *,
    row: dict[str, Any] | None,
    expected_session: bool,
) -> dict[str, Any]:
    return {
        "trade_date": day.isoformat(),
        "market_code": identity.market_code,
        "instrument_code": identity.instrument_code,
        "instrument_id": identity.instrument_id,
        "gap_class": gap_class,
        "expected_session": "YES" if expected_session else "NO",
        "observed": "YES" if row is not None else "NO",
        "status_code": row.get("status_code") if row else None,
        "source_code": row.get("source_code") if row else None,
        "adjustment_state": "UNKNOWN",
        "lineage_state": "CANONICAL_VIEW" if row else "REFERENCE_CLASSIFIED_GAP",
    }


def _fetch_rows(session: Session, requested_from: date, requested_to: date) -> tuple[
    tuple[InstrumentIdentity, ...],
    tuple[dict[str, Any], ...],
    tuple[LifecycleEvent, ...],
    tuple[CalendarException, ...],
]:
    identities = tuple(
        InstrumentIdentity(
            instrument_id=str(row["instrument_id"]),
            instrument_code=str(row["instrument_code"]),
            market_code=str(row["market_code"]),
            calendar_code=row["calendar_code"],
            valid_from=row["valid_from"],
            valid_to=row["valid_to"],
        )
        for row in session.execute(
            text(
                """
                SELECT i.id AS instrument_id, i.instrument_code, m.code AS market_code,
                       m.calendar_code, i.valid_from, i.valid_to
                FROM topicpilot.instruments i
                JOIN topicpilot.markets m ON m.id = i.market_id
                WHERE i.is_active = true AND m.is_active = true
                ORDER BY m.code, i.instrument_code
                """
            )
        ).mappings()
    )
    observations = tuple(
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT instrument_id, market_code, instrument_code, trade_date,
                       close, quality_state, covered, status_code, source_code,
                       adapter_version, retrieved_at
                FROM topicpilot.vw_daily_market_observations
                WHERE trade_date >= :requested_from AND trade_date <= :requested_to
                ORDER BY market_code, instrument_code, trade_date
                """
            ),
            {"requested_from": requested_from, "requested_to": requested_to},
        ).mappings()
    )
    lifecycle_events = tuple(
        LifecycleEvent(
            instrument_id=str(row["instrument_id"]),
            status_code=str(row["status_code"]),
            effective_from=row["effective_from"],
            effective_to=row["effective_to"],
        )
        for row in session.execute(
            text(
                """
                SELECT l.instrument_id, l.status_code, l.effective_from, l.effective_to
                FROM topicpilot.reference_instrument_lifecycles l
                JOIN topicpilot.reference_registry_sets r ON r.id = l.registry_set_id
                WHERE r.status = 'ACTIVE'
                  AND l.effective_from <= :requested_to
                  AND (l.effective_to IS NULL OR l.effective_to >= :requested_from)
                """
            ),
            {"requested_from": requested_from, "requested_to": requested_to},
        ).mappings()
    )
    calendar_exceptions = tuple(
        CalendarException(
            calendar_code=str(row["calendar_code"]),
            calendar_date=row["calendar_date"],
            date_kind=str(row["date_kind"]),
        )
        for row in session.execute(
            text(
                """
                SELECT c.calendar_code, c.calendar_date, c.date_kind
                FROM topicpilot.reference_calendar_dates c
                JOIN topicpilot.reference_registry_sets r ON r.id = c.registry_set_id
                WHERE r.status = 'ACTIVE'
                  AND c.calendar_date >= :requested_from
                  AND c.calendar_date <= :requested_to
                """
            ),
            {"requested_from": requested_from, "requested_to": requested_to},
        ).mappings()
    )
    return identities, observations, lifecycle_events, calendar_exceptions


@contextmanager
def _read_only_session(engine: Engine) -> Iterator[Session]:
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            with Session(bind=connection) as session:
                yield session
        finally:
            transaction.rollback()


DATE_FIELDS = (
    "trade_date",
    "expected_instrument_count",
    "observed_instrument_count",
    "priced_instrument_count",
    "covered_instrument_count",
    "missing_instrument_count",
    "market_no_session_instrument_count",
    "coverage_state",
)
INSTRUMENT_FIELDS = (
    "market_code",
    "instrument_code",
    "instrument_id",
    "requested_from",
    "requested_to",
    "expected_session_count",
    "observed_count",
    "priced_count",
    "covered_count",
    "missing_count",
    "market_no_session_count",
    "first_observation",
    "last_observation",
    "source_codes",
    "ma20_ready",
    "ma60_ready",
    "coverage_state",
    "primary_gap_class",
)
GAP_FIELDS = (
    "trade_date",
    "market_code",
    "instrument_code",
    "instrument_id",
    "gap_class",
    "expected_session",
    "observed",
    "status_code",
    "source_code",
    "adjustment_state",
    "lineage_state",
)


def _write_csv(path: Path, rows: tuple[dict[str, Any], ...], fieldnames: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_artifacts(output_dir: Path, artifacts: AuditArtifacts) -> None:
    """Write the three required CSV artifacts and a compact JSON summary."""

    _write_csv(
        output_dir / "historical-coverage-by-date.csv",
        artifacts.coverage_by_date,
        DATE_FIELDS,
    )
    _write_csv(
        output_dir / "historical-coverage-by-instrument.csv",
        artifacts.coverage_by_instrument,
        INSTRUMENT_FIELDS,
    )
    _write_csv(output_dir / "gap-classification.csv", artifacts.gap_classification, GAP_FIELDS)
    (output_dir / "audit-summary.json").write_text(
        json.dumps(artifacts.summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def audit_database(
    *,
    engine: Engine,
    requested_from: date,
    requested_to: date,
    output_dir: Path,
) -> AuditArtifacts:
    """Run the audit in a read-only transaction and write its artifacts."""

    with _read_only_session(engine) as session:
        identities, observations, lifecycle_events, calendar_exceptions = _fetch_rows(
            session, requested_from, requested_to
        )
        artifacts = build_audit_artifacts(
            requested_from=requested_from,
            requested_to=requested_to,
            identities=identities,
            observations=observations,
            lifecycle_events=lifecycle_events,
            calendar_exceptions=calendar_exceptions,
        )
    write_artifacts(output_dir, artifacts)
    return artifacts


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only canonical historical OHLCV coverage audit"
    )
    parser.add_argument("--database-url", help="explicit non-Production/read-only PostgreSQL URL")
    parser.add_argument("--from", dest="from_date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        requested_from = _parse_date(args.from_date, "--from")
        requested_to = _parse_date(args.to_date, "--to")
        _validate_window(requested_from, requested_to)
        database_url = args.database_url or get_settings().database_url
        engine = create_engine(database_url, pool_pre_ping=True)
        try:
            artifacts = audit_database(
                engine=engine,
                requested_from=requested_from,
                requested_to=requested_to,
                output_dir=args.output_dir,
            )
        finally:
            engine.dispose()
        print(json.dumps(artifacts.summary, ensure_ascii=False, sort_keys=True))
        return 0
    except CoverageAuditError as exc:
        print(json.dumps({"error": str(exc), "code": exc.code}, ensure_ascii=False))
        return 2
    except Exception as exc:
        print(
            json.dumps(
                {"error": "AUDIT_READ_FAILED", "detail": str(exc)}, ensure_ascii=False
            )
        )
        return 3


__all__ = [
    "MAX_AUDIT_DAYS",
    "AuditArtifacts",
    "CalendarException",
    "CoverageAuditError",
    "InstrumentIdentity",
    "LifecycleEvent",
    "audit_database",
    "build_audit_artifacts",
    "main",
    "write_artifacts",
]


if __name__ == "__main__":
    raise SystemExit(main())
