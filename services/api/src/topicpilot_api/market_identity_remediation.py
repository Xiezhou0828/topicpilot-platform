"""Fail-closed remediation for the known legacy TPE/TWO market metadata drift."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from topicpilot_api.orm.models import Instrument, Market, ReferenceRegistrySet
from topicpilot_api.reference_data.bundle import ReferenceBundle, validate_bundle

MARKET_IDENTITY_REMEDIATION_WRITE_SET = frozenset({"markets.name", "markets.exchange_code"})
NON_MARKET_IDENTITY_WRITE_SET = frozenset()
EXPECTED_MARKET_CODES = frozenset({"TPE", "TWO"})

LEGACY_MARKET_METADATA: dict[str, dict[str, str]] = {
    "TPE": {"name": "Taiwan Stock Exchange", "exchange_code": "TPE"},
    "TWO": {"name": "Taipei Exchange", "exchange_code": "TWO"},
}

CANONICAL_MARKET_METADATA: dict[str, dict[str, str]] = {
    "TPE": {"name": "TWSE Listed", "exchange_code": "TWSE"},
    "TWO": {"name": "TPEx OTC", "exchange_code": "TPEx"},
}


class MarketIdentityRemediationConflict(RuntimeError):
    """Raised when the exact known legacy state is not present."""


@dataclass(frozen=True)
class MarketIdentityRemediationResult:
    operation: str
    status: str
    dry_run: bool
    transactional: bool
    idempotent: bool
    market_count: int
    instrument_count: int
    instrument_compatibility: str
    reference_registry_count: int
    changes: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "status": self.status,
            "dryRun": self.dry_run,
            "transactional": self.transactional,
            "idempotent": self.idempotent,
            "marketCount": self.market_count,
            "instrumentCount": self.instrument_count,
            "existingInstrumentCount": self.instrument_count,
            "instrumentCompatibility": self.instrument_compatibility,
            "referenceRegistryCount": self.reference_registry_count,
            "changes": list(self.changes),
            "writeSet": sorted(MARKET_IDENTITY_REMEDIATION_WRITE_SET),
            "nonMarketIdentityWriteSet": sorted(NON_MARKET_IDENTITY_WRITE_SET),
            "marketPrimaryKeysPreserved": True,
            "marketCodesPreserved": True,
        }


def _assert_supported_bundle(bundle: ReferenceBundle) -> dict[str, dict[str, str]]:
    validate_bundle(bundle)
    if bundle.manifest.get("referenceDataVersion") != "tw-reference-v1":
        raise MarketIdentityRemediationConflict(
            "market identity remediation requires reference version tw-reference-v1"
        )
    rows = {row["code"]: row for row in bundle.markets}
    if set(rows) != EXPECTED_MARKET_CODES:
        raise MarketIdentityRemediationConflict(
            f"canonical market code set mismatch: expected={sorted(EXPECTED_MARKET_CODES)} "
            f"actual={sorted(rows)}"
        )
    for code, expected in CANONICAL_MARKET_METADATA.items():
        actual = {
            "name": rows[code].get("name"),
            "exchange_code": rows[code].get("exchange_code"),
        }
        if actual != expected:
            raise MarketIdentityRemediationConflict(
                f"canonical bundle market {code} metadata is not approved: "
                f"expected={expected} actual={actual}"
            )
    return rows


def _count(session: Session, model: type) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


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


def _validate_instrument_compatibility(session: Session, bundle: ReferenceBundle) -> str:
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
    if not rows:
        return "EMPTY"

    actual_keys = [(row.code, row.instrument_code) for row in rows]
    if any(market_code is None for market_code, _ in actual_keys):
        raise MarketIdentityRemediationConflict("orphan instrument market reference")
    if len(actual_keys) != len(set(actual_keys)):
        raise MarketIdentityRemediationConflict("duplicate instrument identity")

    expected = {
        (row["market_code"], row["instrument_code"]): row for row in bundle.instruments
    }
    actual = {(row.code, row.instrument_code): row for row in rows}
    if set(actual) != set(expected):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise MarketIdentityRemediationConflict(
            f"instrument identity set mismatch; missing={missing[:5]} extra={extra[:5]}"
        )

    for key, expected_row in expected.items():
        actual_row = actual[key]
        actual_metadata = (
            actual_row.name,
            actual_row.instrument_type,
            actual_row.currency,
        )
        expected_metadata = (
            expected_row["name"],
            expected_row["instrument_type"],
            expected_row["currency"],
        )
        if actual_metadata != expected_metadata:
            raise MarketIdentityRemediationConflict(
                f"bundle/database conflict in instrument {key[0]}:{key[1]} metadata"
            )
    return "CANONICAL_BUNDLE_COMPATIBLE"


def _changes(markets: list[Market]) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "code": market.code,
            "oldName": market.name,
            "newName": CANONICAL_MARKET_METADATA[market.code]["name"],
            "oldExchangeCode": market.exchange_code or "",
            "newExchangeCode": CANONICAL_MARKET_METADATA[market.code]["exchange_code"],
        }
        for market in markets
    )


def _assert_exact_shape(
    markets: list[Market],
) -> None:
    if len(markets) != len(EXPECTED_MARKET_CODES):
        raise MarketIdentityRemediationConflict(
            f"unexpected market count: expected=2 actual={len(markets)}"
        )
    actual_codes = {market.code for market in markets}
    if actual_codes != EXPECTED_MARKET_CODES:
        raise MarketIdentityRemediationConflict(
            f"unexpected market code set: expected={sorted(EXPECTED_MARKET_CODES)} "
            f"actual={sorted(actual_codes)}"
        )
    if any(not market.is_active for market in markets):
        raise MarketIdentityRemediationConflict("unexpected inactive TPE/TWO market")


def _assert_legacy_precondition(*, reference_registry_count: int) -> None:
    if reference_registry_count != 0:
        raise MarketIdentityRemediationConflict(
            "unexpected reference registry state: expected=0 rows"
        )


def _classify_state(markets: list[Market]) -> str:
    if all(
        market.name == CANONICAL_MARKET_METADATA[market.code]["name"]
        and market.exchange_code == CANONICAL_MARKET_METADATA[market.code]["exchange_code"]
        for market in markets
    ):
        return "CANONICAL"
    if all(
        market.name == LEGACY_MARKET_METADATA[market.code]["name"]
        and market.exchange_code == LEGACY_MARKET_METADATA[market.code]["exchange_code"]
        for market in markets
    ):
        return "LEGACY"
    raise MarketIdentityRemediationConflict(
        "market identity state is neither the exact approved legacy state nor the "
        "complete canonical state"
    )


def _inspect(
    session: Session, bundle: ReferenceBundle
) -> tuple[str, list[Market], tuple[tuple[Any, ...], ...], str, int]:
    _assert_supported_bundle(bundle)
    markets = _load_markets(session)
    _assert_exact_shape(markets)
    instrument_snapshot = _instrument_snapshot(session)
    instrument_compatibility = _validate_instrument_compatibility(session, bundle)
    reference_registry_count = _count(session, ReferenceRegistrySet)
    state = _classify_state(markets)
    if state == "LEGACY":
        _assert_legacy_precondition(
            reference_registry_count=reference_registry_count,
        )
    return (
        state,
        markets,
        instrument_snapshot,
        instrument_compatibility,
        reference_registry_count,
    )


def remediate_market_identity(
    session: Session,
    bundle: ReferenceBundle,
    *,
    apply: bool,
    dry_run: bool = False,
) -> MarketIdentityRemediationResult:
    """Plan or atomically apply only the approved TPE/TWO metadata reconciliation."""

    if apply == dry_run:
        raise ValueError("exactly one of apply or dry_run must be true")
    if not dry_run and session.in_transaction():
        raise RuntimeError("market identity remediation requires a fresh SQLAlchemy session")

    if dry_run:
        state, markets, instrument_snapshot, compatibility, registry_count = _inspect(
            session, bundle
        )
        return MarketIdentityRemediationResult(
            operation="NOOP" if state == "CANONICAL" else "PLAN",
            status="CANONICAL" if state == "CANONICAL" else "VALIDATED",
            dry_run=True,
            transactional=True,
            idempotent=True,
            market_count=len(markets),
            instrument_count=len(instrument_snapshot),
            instrument_compatibility=compatibility,
            reference_registry_count=registry_count,
            changes=() if state == "CANONICAL" else _changes(markets),
        )

    with session.begin():
        state, markets, instrument_snapshot, compatibility, registry_count = _inspect(
            session, bundle
        )
        if state == "CANONICAL":
            return MarketIdentityRemediationResult(
                operation="NOOP",
                status="CANONICAL",
                dry_run=False,
                transactional=True,
                idempotent=True,
                market_count=len(markets),
                instrument_count=len(instrument_snapshot),
                instrument_compatibility=compatibility,
                reference_registry_count=registry_count,
                changes=(),
            )

        changes = _changes(markets)
        for market in markets:
            target = CANONICAL_MARKET_METADATA[market.code]
            market.name = target["name"]
            market.exchange_code = target["exchange_code"]
        session.flush()

        verified = _load_markets(session)
        if _classify_state(verified) != "CANONICAL":
            raise MarketIdentityRemediationConflict(
                "market identity remediation postcondition failed"
            )
        if _instrument_snapshot(session) != instrument_snapshot:
            raise MarketIdentityRemediationConflict(
                "market identity remediation changed instrument rows"
            )
        if _count(session, ReferenceRegistrySet) != registry_count:
            raise MarketIdentityRemediationConflict(
                "market identity remediation changed reference registry state"
            )
        return MarketIdentityRemediationResult(
            operation="APPLIED",
            status="CANONICAL",
            dry_run=False,
            transactional=True,
            idempotent=True,
            market_count=len(verified),
            instrument_count=len(instrument_snapshot),
            instrument_compatibility=compatibility,
            reference_registry_count=registry_count,
            changes=changes,
        )


__all__ = [
    "CANONICAL_MARKET_METADATA",
    "EXPECTED_MARKET_CODES",
    "LEGACY_MARKET_METADATA",
    "MARKET_IDENTITY_REMEDIATION_WRITE_SET",
    "NON_MARKET_IDENTITY_WRITE_SET",
    "MarketIdentityRemediationConflict",
    "MarketIdentityRemediationResult",
    "remediate_market_identity",
]
