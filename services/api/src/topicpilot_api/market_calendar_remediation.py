"""Bundle-derived, calendar-only remediation for existing canonical markets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from topicpilot_api.orm.models import Instrument, Market, ReferenceRegistrySet
from topicpilot_api.reference_data import ReferenceBundle, validate_bundle

MARKET_CALENDAR_REMEDIATION_WRITE_SET = frozenset({"markets.calendar_code"})
NON_CALENDAR_CONTEXT_WRITE_SET = frozenset()


class MarketCalendarRemediationConflict(RuntimeError):
    """Raised when the existing state is unsafe for calendar-only remediation."""


@dataclass(frozen=True)
class MarketCalendarRemediationResult:
    operation: str
    status: str
    dry_run: bool
    semantic_compatibility: str
    market_count: int
    instrument_count: int
    changes: tuple[dict[str, str | None], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "status": self.status,
            "dryRun": self.dry_run,
            "transactional": True,
            "idempotent": True,
            "semanticCompatibility": self.semantic_compatibility,
            "marketCount": self.market_count,
            "instrumentCount": self.instrument_count,
            "changes": list(self.changes),
            "writeSet": sorted(MARKET_CALENDAR_REMEDIATION_WRITE_SET),
            "nonCalendarContextWriteSet": [],
            "instrumentWrites": [],
            "marketPrimaryKeysPreserved": True,
            "marketCodesPreserved": True,
            "marketIdentityFieldsPreserved": True,
        }


def _load_markets(session: Session) -> list[Market]:
    return list(session.scalars(select(Market).order_by(Market.code)))


def _instrument_snapshot(session: Session) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        tuple(row)
        for row in session.execute(
            select(
                Instrument.id,
                Instrument.market_id,
                Instrument.instrument_code,
                Instrument.name,
                Instrument.instrument_type,
                Instrument.currency,
                Instrument.valid_from,
                Instrument.valid_to,
                Instrument.is_active,
            ).order_by(Instrument.id)
        ).all()
    )


def _market_immutable_snapshot(markets: list[Market]) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (
            market.id,
            market.code,
            market.name,
            market.exchange_code,
            market.timezone,
            market.valid_from,
            market.valid_to,
            market.is_active,
        )
        for market in markets
    )


def _validate_instrument_compatibility(
    session: Session, bundle: ReferenceBundle
) -> tuple[tuple[Any, ...], ...]:
    rows = list(
        session.execute(
            select(
                Market.code,
                Instrument.instrument_code,
                Instrument.name,
                Instrument.instrument_type,
                Instrument.currency,
            )
            .select_from(Instrument)
            .outerjoin(Market, Market.id == Instrument.market_id)
        ).all()
    )
    actual_keys = [(row.code, row.instrument_code) for row in rows]
    if any(code is None for code, _ in actual_keys):
        raise MarketCalendarRemediationConflict("orphan instrument market reference")
    if len(actual_keys) != len(set(actual_keys)):
        raise MarketCalendarRemediationConflict("duplicate instrument identity")

    expected = {(row["market_code"], row["instrument_code"]): row for row in bundle.instruments}
    actual = {(row.code, row.instrument_code): row for row in rows}
    if set(actual) != set(expected):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise MarketCalendarRemediationConflict(
            f"instrument identity set mismatch; missing={missing[:5]} extra={extra[:5]}"
        )
    for key, expected_row in expected.items():
        row = actual[key]
        if (row.name, row.instrument_type, row.currency) != (
            expected_row["name"],
            expected_row["instrument_type"],
            expected_row["currency"],
        ):
            raise MarketCalendarRemediationConflict(
                f"bundle/database conflict in instrument {key[0]}:{key[1]} metadata"
            )
    return _instrument_snapshot(session)


def _inspect(
    session: Session, bundle: ReferenceBundle
) -> tuple[list[Market], tuple[dict[str, str | None], ...], tuple[tuple[Any, ...], ...]]:
    validate_bundle(bundle)
    markets = _load_markets(session)
    expected = {row["code"]: row for row in bundle.markets}
    actual_codes = {market.code for market in markets}
    if actual_codes != set(expected):
        raise MarketCalendarRemediationConflict(
            f"unexpected market topology: expected={sorted(expected)} actual={sorted(actual_codes)}"
        )
    if session.scalar(select(func.count()).select_from(ReferenceRegistrySet)) != 0:
        raise MarketCalendarRemediationConflict("reference registry must be empty")

    changes: list[dict[str, str | None]] = []
    for market in markets:
        row = expected[market.code]
        if not market.is_active:
            raise MarketCalendarRemediationConflict(f"market {market.code} is inactive")
        for field, expected_value in (
            ("name", row["name"]),
            ("exchange_code", row.get("exchange_code")),
            ("timezone", row["timezone"]),
        ):
            if getattr(market, field) != expected_value:
                raise MarketCalendarRemediationConflict(
                    f"bundle/database conflict in market {market.code} {field}"
                )
        target = row.get("calendar_code")
        if market.calendar_code is None:
            changes.append(
                {
                    "code": market.code,
                    "oldCalendarCode": None,
                    "newCalendarCode": target,
                }
            )
        elif market.calendar_code != target:
            raise MarketCalendarRemediationConflict(
                f"unexpected non-null calendar for market {market.code}"
            )
    return markets, tuple(changes), _validate_instrument_compatibility(session, bundle)


def remediate_market_calendar(
    session: Session,
    bundle: ReferenceBundle,
    *,
    apply: bool,
    dry_run: bool = False,
) -> MarketCalendarRemediationResult:
    """Plan or atomically apply only bundle-derived ``markets.calendar_code`` values."""

    if apply == dry_run:
        raise ValueError("exactly one of apply or dry_run must be true")
    if not dry_run and session.in_transaction():
        raise RuntimeError("market calendar remediation requires a fresh SQLAlchemy session")

    if dry_run:
        markets, changes, instruments = _inspect(session, bundle)
        canonical = not changes
        return MarketCalendarRemediationResult(
            operation="NOOP" if canonical else "PLAN",
            status="CANONICAL" if canonical else "VALIDATED",
            dry_run=True,
            semantic_compatibility=(
                "CANONICAL" if canonical else "BUNDLE_COMPATIBLE_NULL_CALENDAR"
            ),
            market_count=len(markets),
            instrument_count=len(instruments),
            changes=changes,
        )

    with session.begin():
        markets, changes, instrument_snapshot = _inspect(session, bundle)
        immutable_markets = _market_immutable_snapshot(markets)
        if not changes:
            return MarketCalendarRemediationResult(
                "NOOP",
                "CANONICAL",
                False,
                "CANONICAL",
                len(markets),
                len(instrument_snapshot),
                (),
            )
        expected = {row["code"]: row for row in bundle.markets}
        for market in markets:
            market.calendar_code = expected[market.code].get("calendar_code")
        session.flush()

        verified, remaining, verified_instruments = _inspect(session, bundle)
        if remaining:
            raise MarketCalendarRemediationConflict("calendar remediation postcondition failed")
        if _market_immutable_snapshot(verified) != immutable_markets:
            raise MarketCalendarRemediationConflict("calendar remediation changed market identity")
        if verified_instruments != instrument_snapshot:
            raise MarketCalendarRemediationConflict("calendar remediation changed instrument rows")
        return MarketCalendarRemediationResult(
            "APPLIED",
            "CANONICAL",
            False,
            "CANONICAL",
            len(verified),
            len(verified_instruments),
            changes,
        )


__all__ = [
    "MARKET_CALENDAR_REMEDIATION_WRITE_SET",
    "NON_CALENDAR_CONTEXT_WRITE_SET",
    "MarketCalendarRemediationConflict",
    "MarketCalendarRemediationResult",
    "remediate_market_calendar",
]
