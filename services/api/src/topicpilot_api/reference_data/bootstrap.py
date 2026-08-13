"""Atomic, reference-only PostgreSQL bootstrap for a validated bundle."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from topicpilot_api.orm.models import (
    Instrument,
    Market,
    ReferenceAdjustment,
    ReferenceCalendarDate,
    ReferenceCurrency,
    ReferenceRegistrySet,
    ReferenceSession,
    ReferenceTimezone,
    ReferenceTradingStatus,
)

from .bundle import ReferenceBundle, validate_bundle

REFERENCE_WRITE_SET = frozenset(
    {
        "markets",
        "instruments",
        "reference_registry_sets",
        "reference_currencies",
        "reference_timezones",
        "reference_sessions",
        "reference_trading_statuses",
        "reference_adjustments",
        "reference_calendar_dates",
    }
)
NON_REFERENCE_WRITE_SET = frozenset()


class ReferenceBootstrapConflict(RuntimeError):
    """Raised when database state conflicts with the approved bundle."""


@dataclass(frozen=True)
class ReferenceBootstrapResult:
    operation: str
    reference_data_version: str
    bundle_sha256: str
    status: str
    dry_run: bool
    created_markets: int
    created_instruments: int
    created_reference_rows: int
    noop_reference_rows: int
    retired_registry_sets: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "referenceVersion": self.reference_data_version,
            "bundleSha256": self.bundle_sha256,
            "status": self.status,
            "dryRun": self.dry_run,
            "createdMarkets": self.created_markets,
            "createdInstruments": self.created_instruments,
            "createdReferenceRows": self.created_reference_rows,
            "noopReferenceRows": self.noop_reference_rows,
            "retiredRegistrySets": self.retired_registry_sets,
            "writeSet": sorted(REFERENCE_WRITE_SET),
            "nonReferenceWriteSet": [],
            "transactional": True,
            "idempotent": True,
        }


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _source_manifest_hash(bundle: ReferenceBundle) -> str:
    return _canonical_hash(bundle.manifest.get("sourceArtifacts", []))


def _existing_registry(session: Session, bundle: ReferenceBundle) -> ReferenceRegistrySet | None:
    rows = list(
        session.scalars(
            select(ReferenceRegistrySet).where(
                ReferenceRegistrySet.reference_data_version
                == bundle.manifest["referenceDataVersion"]
            )
        )
    )
    if len(rows) > 1:
        raise ReferenceBootstrapConflict("reference version is duplicated in the database")
    return rows[0] if rows else None


def _check_same(expected: Any, actual: Any, label: str) -> None:
    if expected != actual:
        raise ReferenceBootstrapConflict(f"bundle/database conflict in {label}")


def validate_market_context(market: Market, row: dict[str, Any]) -> None:
    """Apply the same fail-closed bundle comparison in plan and activation paths."""

    _check_same(row["code"], market.code, f"market {row['code']} code")
    _check_same(row["name"], market.name, f"market {row['code']} name")
    _check_same(row.get("exchange_code"), market.exchange_code, f"market {row['code']} exchange")
    _check_same(row["timezone"], market.timezone, f"market {row['code']} timezone")
    _check_same(row.get("calendar_code"), market.calendar_code, f"market {row['code']} calendar")


def _ensure_market(session: Session, row: dict[str, Any]) -> tuple[Market, bool]:
    market = session.scalar(select(Market).where(Market.code == row["code"]))
    if market is None:
        market = Market(
            code=row["code"],
            name=row["name"],
            exchange_code=row.get("exchange_code"),
            timezone=row["timezone"],
            calendar_code=row.get("calendar_code"),
            is_active=True,
        )
        session.add(market)
        session.flush()
        return market, True
    validate_market_context(market, row)
    if not market.is_active:
        market.is_active = True
    return market, False


def _ensure_instrument(
    session: Session, market: Market, row: dict[str, Any]
) -> tuple[Instrument, bool]:
    instrument = session.scalar(
        select(Instrument).where(
            Instrument.market_id == market.id,
            Instrument.instrument_code == row["instrument_code"],
        )
    )
    if instrument is None:
        instrument = Instrument(
            market_id=market.id,
            instrument_code=row["instrument_code"],
            name=row["name"],
            instrument_type=row["instrument_type"],
            currency=row["currency"],
            is_active=True,
        )
        session.add(instrument)
        session.flush()
        return instrument, True
    _check_same(row["name"], instrument.name, f"instrument {row['instrument_code']} name")
    _check_same(
        row["instrument_type"],
        instrument.instrument_type,
        f"instrument {row['instrument_code']} type",
    )
    _check_same(
        row["currency"],
        instrument.currency,
        f"instrument {row['instrument_code']} currency",
    )
    if not instrument.is_active:
        instrument.is_active = True
    return instrument, False


def _ensure_reference_row(
    session: Session,
    model: type,
    filters: dict[str, Any],
    values: dict[str, Any],
) -> tuple[Any, bool]:
    row = session.scalar(select(model).filter_by(**filters))
    if row is None:
        row = model(**filters, **values)
        session.add(row)
        session.flush()
        return row, True
    for field, value in values.items():
        _check_same(value, getattr(row, field), f"{model.__tablename__}.{field}")
    return row, False


def _validate_existing_identity_set(session: Session, bundle: ReferenceBundle) -> None:
    expected = {
        (row["market_code"], row["instrument_code"]) for row in bundle.instruments
    }
    actual = {
        tuple(row)
        for row in session.execute(
            select(Market.code, Instrument.instrument_code)
            .join(Instrument, Instrument.market_id == Market.id)
            .where(Market.code.in_([row["code"] for row in bundle.markets]))
        ).all()
    }
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ReferenceBootstrapConflict(
            f"identity set mismatch; missing={missing[:5]} extra={extra[:5]}"
        )


def _validate_registry_rows(session: Session, registry_id, bundle: ReferenceBundle) -> None:
    _validate_existing_identity_set(session, bundle)
    currencies = set(
        session.scalars(
            select(ReferenceCurrency.code).where(ReferenceCurrency.registry_set_id == registry_id)
        )
    )
    _check_same(currencies, {row["code"] for row in bundle.currencies}, "currency catalogue")
    timezones = set(
        session.scalars(
            select(ReferenceTimezone.name).where(ReferenceTimezone.registry_set_id == registry_id)
        )
    )
    _check_same(timezones, {row["name"] for row in bundle.timezones}, "timezone catalogue")
    sessions = {
        tuple(row)
        for row in session.execute(
            select(ReferenceSession.code, ReferenceSession.calendar_code).where(
                ReferenceSession.registry_set_id == registry_id
            )
        ).all()
    }
    _check_same(
        sessions,
        {(row["code"], row["calendar_code"]) for row in bundle.sessions},
        "session catalogue",
    )
    statuses = set(
        session.scalars(
            select(ReferenceTradingStatus.code).where(
                ReferenceTradingStatus.registry_set_id == registry_id
            )
        )
    )
    _check_same(statuses, {row["code"] for row in bundle.trading_statuses}, "status catalogue")
    adjustments = set(
        session.scalars(
            select(ReferenceAdjustment.code).where(
                ReferenceAdjustment.registry_set_id == registry_id
            )
        )
    )
    _check_same(adjustments, {row["code"] for row in bundle.adjustments}, "adjustment catalogue")
    calendar_dates = {
        tuple(row)
        for row in session.execute(
            select(
                ReferenceCalendarDate.calendar_code,
                ReferenceCalendarDate.calendar_date,
                ReferenceCalendarDate.date_kind,
            ).where(ReferenceCalendarDate.registry_set_id == registry_id)
        ).all()
    }
    _check_same(
        calendar_dates,
        {
            (row["calendar_code"], date.fromisoformat(row["calendar_date"]), row["date_kind"])
            for row in bundle.calendar_dates
        },
        "calendar dates",
    )


def _plan(session: Session, bundle: ReferenceBundle) -> ReferenceBootstrapResult:
    registry = _existing_registry(session, bundle)
    if registry and registry.bundle_sha256 == bundle.digest():
        _validate_registry_rows(session, registry.id, bundle)
    for row in bundle.markets:
        market = session.scalar(select(Market).where(Market.code == row["code"]))
        if market is not None:
            validate_market_context(market, row)
    existing_market_codes = set(
        session.scalars(
            select(Market.code).where(Market.code.in_([row["code"] for row in bundle.markets]))
        )
    )
    existing_instrument_keys = {
        tuple(row)
        for row in session.execute(
            select(Market.code, Instrument.instrument_code)
            .join(Instrument, Instrument.market_id == Market.id)
            .where(Market.code.in_([row["code"] for row in bundle.markets]))
        ).all()
    }
    expected_keys = {
        (row["market_code"], row["instrument_code"]) for row in bundle.instruments
    }
    existing_reference_rows = 0
    if registry:
        for model in (
            ReferenceCurrency,
            ReferenceTimezone,
            ReferenceSession,
            ReferenceTradingStatus,
            ReferenceAdjustment,
            ReferenceCalendarDate,
        ):
            existing_reference_rows += session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.registry_set_id == registry.id)
            ) or 0
    return ReferenceBootstrapResult(
        operation="NOOP" if registry and registry.bundle_sha256 == bundle.digest() else "PLAN",
        reference_data_version=bundle.manifest["referenceDataVersion"],
        bundle_sha256=bundle.digest(),
        status=registry.status if registry else "VALIDATED",
        dry_run=True,
        created_markets=len(set(row["code"] for row in bundle.markets) - existing_market_codes),
        created_instruments=len(expected_keys - existing_instrument_keys),
        created_reference_rows=max(0, sum(
            len(getattr(bundle, field))
            for field in (
                "currencies",
                "timezones",
                "sessions",
                "trading_statuses",
                "adjustments",
                "calendar_dates",
            )
        ) - existing_reference_rows),
        noop_reference_rows=existing_reference_rows,
        retired_registry_sets=0,
    )


def bootstrap_reference_bundle(
    session: Session,
    bundle: ReferenceBundle,
    *,
    activate: bool,
    dry_run: bool = False,
) -> ReferenceBootstrapResult:
    """Apply a bundle in one transaction, or produce a no-write plan.

    The caller must pass a fresh ``Session``.  The function owns the only
    commit boundary for the reference bootstrap and never imports or writes
    any non-reference domain models or audit records.
    """

    validate_bundle(bundle)
    if dry_run:
        return _plan(session, bundle)
    if session.in_transaction():
        raise RuntimeError("reference bootstrap requires a fresh SQLAlchemy session")

    version = bundle.manifest["referenceDataVersion"]
    bundle_hash = bundle.digest()
    source_hash = _source_manifest_hash(bundle)
    with session.begin():
        registry = _existing_registry(session, bundle)
        if registry and registry.bundle_sha256 not in (None, bundle_hash):
            raise ReferenceBootstrapConflict(
                "reference version exists with a different bundle hash"
            )
        if registry and registry.status == "ACTIVE" and registry.bundle_sha256 == bundle_hash:
            _validate_registry_rows(session, registry.id, bundle)
            return ReferenceBootstrapResult(
                "NOOP", version, bundle_hash, "ACTIVE", False, 0, 0, 0, 0, 0
            )
        if registry is None:
            registry = ReferenceRegistrySet(
                reference_data_version=version,
                status="VALIDATED",
                description="TASK-DATA-REF-001 canonical reference bundle",
                bundle_sha256=bundle_hash,
                source_manifest_sha256=source_hash,
            )
            session.add(registry)
            session.flush()
        else:
            registry.bundle_sha256 = bundle_hash
            registry.source_manifest_sha256 = source_hash
            registry.status = "VALIDATED"

        markets = {}
        created_markets = 0
        for row in bundle.markets:
            market, created = _ensure_market(session, row)
            markets[row["code"]] = market
            created_markets += int(created)
        created_instruments = 0
        for row in bundle.instruments:
            _, created = _ensure_instrument(session, markets[row["market_code"]], row)
            created_instruments += int(created)
        _validate_existing_identity_set(session, bundle)

        created_reference_rows = 0
        noop_reference_rows = 0
        for row in bundle.currencies:
            _, created = _ensure_reference_row(
                session,
                ReferenceCurrency,
                {"registry_set_id": registry.id, "code": row["code"]},
                {"scale": row["scale"]},
            )
            created_reference_rows += int(created)
            noop_reference_rows += int(not created)
        for row in bundle.timezones:
            _, created = _ensure_reference_row(
                session,
                ReferenceTimezone,
                {"registry_set_id": registry.id, "name": row["name"]},
                {},
            )
            created_reference_rows += int(created)
            noop_reference_rows += int(not created)
        for row in bundle.sessions:
            _, created = _ensure_reference_row(
                session,
                ReferenceSession,
                {"registry_set_id": registry.id, "code": row["code"]},
                {"calendar_code": row["calendar_code"]},
            )
            created_reference_rows += int(created)
            noop_reference_rows += int(not created)
        for model, rows, field in (
            (ReferenceTradingStatus, bundle.trading_statuses, "code"),
            (ReferenceAdjustment, bundle.adjustments, "code"),
        ):
            for row in rows:
                _, created = _ensure_reference_row(
                    session,
                    model,
                    {"registry_set_id": registry.id, field: row[field]},
                    {},
                )
                created_reference_rows += int(created)
                noop_reference_rows += int(not created)
        for row in bundle.calendar_dates:
            _, created = _ensure_reference_row(
                session,
                ReferenceCalendarDate,
                {
                    "registry_set_id": registry.id,
                    "calendar_code": row["calendar_code"],
                    "calendar_date": date.fromisoformat(row["calendar_date"]),
                },
                {"date_kind": row["date_kind"]},
            )
            created_reference_rows += int(created)
            noop_reference_rows += int(not created)
        _validate_registry_rows(session, registry.id, bundle)

        retired = 0
        if activate:
            active_sets = list(
                session.scalars(
                    select(ReferenceRegistrySet).where(
                        ReferenceRegistrySet.status == "ACTIVE",
                        ReferenceRegistrySet.id != registry.id,
                    )
                )
            )
            for active in active_sets:
                active.status = "RETIRED"
                retired += 1
            # PostgreSQL enforces the partial unique ACTIVE index per statement.
            # Flush retirement before promoting this registry so a replacement
            # version never transiently creates two ACTIVE rows in one flush.
            session.flush()
            registry.status = "ACTIVE"
        status = registry.status
        operation = "ACTIVATED" if activate else "VALIDATED"
        return ReferenceBootstrapResult(
            operation,
            version,
            bundle_hash,
            status,
            False,
            created_markets,
            created_instruments,
            created_reference_rows,
            noop_reference_rows,
            retired,
        )


__all__ = [
    "NON_REFERENCE_WRITE_SET",
    "REFERENCE_WRITE_SET",
    "ReferenceBootstrapConflict",
    "ReferenceBootstrapResult",
    "bootstrap_reference_bundle",
    "validate_market_context",
]
