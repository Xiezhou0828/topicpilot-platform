"""Local-only promotion of HIST-002B evidence into the V2 observation chain.

This module is deliberately separate from live provider ingestion.  It reads
the predecessor evidence table, preserves its source lineage in the raw
observation payload, and reuses the repository's historical normalizer and
market-date anchor.  It never updates or deletes the legacy table.
"""

from __future__ import annotations

import argparse
import json
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from ipaddress import ip_address
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import sqlalchemy as sa
from sqlalchemy import MetaData, insert, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from topicpilot_api.config import get_settings
from topicpilot_api.normalizer import (
    HistoricalDailyBarNormalizer,
    InputEnvelope,
    MappingPolicy,
    ReferenceContext,
    ReferenceContextRequest,
)
from topicpilot_api.normalizer.contracts import ensure_utc, stable_hash
from topicpilot_api.normalizer.runtime import DatabaseReferenceContextLoader
from topicpilot_api.orm.models import (
    CanonicalObservation,
    CanonicalPriceObservation,
    CanonicalVolumeObservation,
    Instrument,
    Market,
    MarketDataSource,
    ObservationTimelineBatch,
    ObservationTimelineEntry,
    RawMarketObservation,
    ReferenceInstrumentLifecycle,
    ReferenceRegistrySet,
)

TASK_ID = "TASK-DATA-HIST-PERSISTENCE-AUTHORITY-PROMOTION"
LEGACY_TABLE = "topicpilot.market_data_ohlcv"
REFERENCE_VERSION = "tw-reference-v1"
BRIDGE_CONTRACT_VERSION = "hist-002b-legacy-to-v2.v1"
BRIDGE_MAPPING_POLICY_VERSION = "hist-002b-promotion-mapping.v1"
NORMALIZATION_CONTRACT_VERSION = "normalization-contract-v1"
BRIDGE_RECEIVED_AT_POLICY = "LEGACY_CREATED_AT_AS_BRIDGE_RECEIPT_ONLY"
BRIDGE_NAMESPACE = uuid.UUID("b1cc6a1e-4cbb-5d0e-8f4d-7f9c4b6ec2c4")
EXPECTED_REPOSITORY_HEAD = "0029_task_data_ref_006e_instrument_lifecycle"
EXPECTED_LEGACY_ROWS = 63_826
EXPECTED_LEGACY_SECURITIES = 507
EXPECTED_DATE_MIN = date(2026, 2, 2)
EXPECTED_DATE_MAX = date(2026, 8, 13)

PHYSICAL_TO_CANONICAL_MARKET = {"TWSE": "TPE", "TPEX": "TWO"}
PROVIDER_TO_SOURCE = {
    "TWSE": ("TWSE_OFFICIAL_DAILY", "twse-official-daily.v1"),
    "TPEx": ("TPEX_OFFICIAL_DAILY", "tpex-official-daily.v1"),
}
REQUIRED_LINEAGE_KEYS = frozenset(
    {
        "normalizer",
        "provider",
        "request_params",
        "response_sha256",
        "retrieved_at",
        "source_kind",
        "source_url",
    }
)


class HistoricalPromotionError(RuntimeError):
    """Raised when a promotion precondition or reconciliation check fails."""


@dataclass(frozen=True)
class LegacyManifest:
    row_count: int
    security_count: int
    date_min: date
    date_max: date
    twse_rows: int
    twse_securities: int
    tpex_rows: int
    tpex_securities: int
    duplicate_excess: int
    invalid_ohlcv: int
    missing_required_lineage: int
    manifest_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rowCount": self.row_count,
            "securityCount": self.security_count,
            "dateMin": self.date_min.isoformat(),
            "dateMax": self.date_max.isoformat(),
            "twseRows": self.twse_rows,
            "twseSecurities": self.twse_securities,
            "tpexRows": self.tpex_rows,
            "tpexSecurities": self.tpex_securities,
            "duplicateExcess": self.duplicate_excess,
            "invalidOhlcv": self.invalid_ohlcv,
            "missingRequiredLineage": self.missing_required_lineage,
            "manifestSha256": self.manifest_sha256,
        }


@dataclass(frozen=True)
class PromotionResult:
    manifest: LegacyManifest
    raw_created: int
    raw_reused: int
    timeline_created: int
    timeline_reused: int
    canonical_created: dict[str, int]
    canonical_reused: dict[str, int]
    status_rows_created: int
    rejected_rows: int
    quarantined_rows: int
    noop: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "taskId": TASK_ID,
            "bridgeContractVersion": BRIDGE_CONTRACT_VERSION,
            "bridgeMappingPolicyVersion": BRIDGE_MAPPING_POLICY_VERSION,
            "referenceDataVersion": REFERENCE_VERSION,
            "manifest": self.manifest.to_dict(),
            "rawCreated": self.raw_created,
            "rawReused": self.raw_reused,
            "timelineCreated": self.timeline_created,
            "timelineReused": self.timeline_reused,
            "canonicalCreated": self.canonical_created,
            "canonicalReused": self.canonical_reused,
            "statusRowsCreated": self.status_rows_created,
            "rejectedRows": self.rejected_rows,
            "quarantinedRows": self.quarantined_rows,
            "noop": self.noop,
        }


def _chunks(values: list[Any], size: int = 500) -> Iterable[list[Any]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _text_number(value: Any) -> str | None:
    if value is None:
        return None
    normalized = Decimal(str(value)).normalize()
    return "0" if normalized == 0 else format(normalized, "f")


def _as_datetime(value: Any, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise HistoricalPromotionError(f"{field} is not a timestamp")
    if parsed.tzinfo is None:
        raise HistoricalPromotionError(f"{field} is timezone-naive")
    return ensure_utc(parsed)


def _market_date_anchor(trading_date: date, timezone_name: str) -> datetime:
    try:
        market_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise HistoricalPromotionError(f"unknown market timezone: {timezone_name}") from exc
    # This is the same explicit market-date anchor used by live historical
    # ingestion. It is not a close-time or a synthetic timestamp.
    return datetime.combine(trading_date, time.min, tzinfo=market_timezone)


def _deterministic_id(kind: str, legacy_id: Any, family: str | None = None) -> uuid.UUID:
    suffix = f":{family}" if family else ""
    return uuid.uuid5(BRIDGE_NAMESPACE, f"{kind}:{legacy_id}{suffix}")


def _legacy_table(bind: Any) -> sa.Table:
    metadata = MetaData()
    return sa.Table("market_data_ohlcv", metadata, schema="topicpilot", autoload_with=bind)


def _assert_local_target(engine: Engine, *, local_only: bool) -> dict[str, str]:
    if not local_only:
        raise HistoricalPromotionError("promotion requires the explicit local-only guard")
    host = (engine.url.host or "").lower()
    if host not in {"localhost", "127.0.0.1", "::1"}:
        raise HistoricalPromotionError(f"database host is not local: {host or '<empty>'}")
    if engine.url.database != "topicpilot":
        raise HistoricalPromotionError("promotion target database must be topicpilot")
    with engine.connect() as connection:
        tx = connection.begin()
        try:
            server_ip = connection.execute(text("select inet_server_addr()::text")).scalar_one()
            database = connection.execute(text("select current_database()")).scalar_one()
            current_user = connection.execute(text("select current_user")).scalar_one()
            server = ip_address(str(server_ip).split("/", 1)[0])
            if not (server.is_private or server.is_loopback):
                raise HistoricalPromotionError(
                    f"database server address is not private/local: {server_ip}"
                )
            if database != "topicpilot":
                raise HistoricalPromotionError("connected database is not topicpilot")
            return {
                "urlHost": host,
                "serverAddress": server_ip,
                "database": database,
                "user": current_user,
                "target": "LOCAL_DEVELOPMENT_ONLY",
            }
        finally:
            tx.rollback()


def _assert_schema(session: Session) -> None:
    version = session.execute(text("select version_num from alembic_version")).scalar_one_or_none()
    if version != EXPECTED_REPOSITORY_HEAD:
        raise HistoricalPromotionError(
            "canonical schema is not at repository head: "
            f"{version!r} != {EXPECTED_REPOSITORY_HEAD!r}"
        )
    required = {
        "observation_timeline_batches",
        "observation_timeline_entries",
        "canonical_observations",
        "canonical_price_observations",
        "canonical_volume_observations",
        "canonical_trading_status_observations",
        "reference_registry_sets",
        "reference_calendar_dates",
        "reference_instrument_lifecycles",
    }
    found = set(
        session.execute(
            text(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'topicpilot'
                """
            )
        ).scalars()
    )
    missing = sorted(required - found)
    if missing:
        raise HistoricalPromotionError(f"canonical schema relations are missing: {missing}")


def _load_reference_context(session: Session) -> ReferenceContext:
    registry = session.scalar(
        select(ReferenceRegistrySet).where(
            ReferenceRegistrySet.reference_data_version == REFERENCE_VERSION,
            ReferenceRegistrySet.status == "ACTIVE",
        )
    )
    if registry is None:
        raise HistoricalPromotionError("active tw-reference-v1 registry is missing")
    try:
        return DatabaseReferenceContextLoader(session).load_reference_context(
            ReferenceContextRequest(
                reference_data_version=REFERENCE_VERSION,
                currency_code="TWD",
                timezone_name="Asia/Taipei",
                session_code="REGULAR",
                calendar_code="TW_MARKET",
            )
        )
    except Exception as exc:
        raise HistoricalPromotionError(f"reference context is incomplete: {exc}") from exc


def _load_identity_map(
    session: Session,
) -> tuple[dict[tuple[str, str], tuple[Instrument, Market]], dict[uuid.UUID, dict[str, Any]]]:
    rows = session.execute(
        select(Instrument, Market)
        .join(Market, Market.id == Instrument.market_id)
        .where(
            Market.code.in_(["TPE", "TWO"]),
            Market.is_active.is_(True),
            Instrument.is_active.is_(True),
        )
    ).all()
    identity_map: dict[tuple[str, str], tuple[Instrument, Market]] = {}
    for instrument, market in rows:
        key = (market.code, instrument.instrument_code)
        if key in identity_map:
            raise HistoricalPromotionError(f"ambiguous canonical identity: {key}")
        identity_map[key] = (instrument, market)
    if len(identity_map) != EXPECTED_LEGACY_SECURITIES:
        raise HistoricalPromotionError(
            "approved canonical identity count is "
            f"{len(identity_map)}, expected {EXPECTED_LEGACY_SECURITIES}"
        )

    lifecycle_rows = session.execute(
        select(
            ReferenceInstrumentLifecycle.instrument_id,
            ReferenceInstrumentLifecycle.status_code,
            ReferenceInstrumentLifecycle.effective_from,
            ReferenceInstrumentLifecycle.effective_to,
        )
    ).mappings()
    lifecycles: dict[uuid.UUID, dict[str, Any]] = {}
    for row in lifecycle_rows:
        if row["instrument_id"] in lifecycles:
            raise HistoricalPromotionError("duplicate lifecycle authority for an instrument")
        lifecycles[row["instrument_id"]] = dict(row)
    return identity_map, lifecycles


def _load_sources(session: Session) -> dict[str, MarketDataSource]:
    result: dict[str, MarketDataSource] = {}
    for provider, (source_code, adapter_version) in PROVIDER_TO_SOURCE.items():
        source = session.scalar(
            select(MarketDataSource).where(
                MarketDataSource.source_code == source_code,
                MarketDataSource.adapter_version == adapter_version,
            )
        )
        if source is None:
            raise HistoricalPromotionError(
                f"approved source registration is missing: {source_code}/{adapter_version}"
            )
        expected = {
            "source_category": "HISTORICAL_DAILY",
            "observation_semantics": "DAILY_BAR",
            "adjustment_policy": "UNKNOWN",
            "calendar_policy": "MARKET_CALENDAR",
            "status": source.status,
        }
        actual = {key: getattr(source, key) for key in expected}
        if actual["status"] not in {"REGISTERED", "ACTIVE"}:
            raise HistoricalPromotionError(f"source registration is not active: {actual}")
        for key in (
            "source_category",
            "observation_semantics",
            "adjustment_policy",
            "calendar_policy",
        ):
            if actual[key] != expected[key]:
                raise HistoricalPromotionError(
                    "source registration contract mismatch for "
                    f"{source_code}: {key}={actual[key]!r}"
                )
        result[provider] = source
    return result


def _manifest_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = [
        {
            "id": row["id"],
            "market": row["market"],
            "security_code": row["security_code"],
            "trading_date": row["trading_date"].isoformat(),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
            "provider": row["provider"],
            "source_url": row["source_url"],
            "provider_lineage": row["provider_lineage"],
            "lifecycle_status": row["lifecycle_status"],
        }
        for row in rows
    ]
    return sorted(
        normalized,
        key=lambda row: (
            row["market"],
            row["security_code"],
            row["trading_date"],
            row["provider"],
            row["id"],
        ),
    )


def _validate_legacy_rows(
    rows: list[dict[str, Any]],
    identity_map: dict[tuple[str, str], tuple[Instrument, Market]],
    lifecycles: dict[uuid.UUID, dict[str, Any]],
) -> LegacyManifest:
    if not rows:
        raise HistoricalPromotionError("legacy evidence table is empty")
    securities = {(row["market"], row["security_code"]) for row in rows}
    if len(rows) != EXPECTED_LEGACY_ROWS or len(securities) != EXPECTED_LEGACY_SECURITIES:
        raise HistoricalPromotionError(
            f"legacy evidence totals changed: rows={len(rows)} securities={len(securities)}"
        )
    dates = [row["trading_date"] for row in rows]
    if min(dates) != EXPECTED_DATE_MIN or max(dates) != EXPECTED_DATE_MAX:
        raise HistoricalPromotionError(f"legacy date range changed: {min(dates)}..{max(dates)}")
    duplicate_excess = len(rows) - len(
        {
            (row["market"], row["security_code"], row["trading_date"], row["provider"])
            for row in rows
        }
    )
    invalid_ohlcv = 0
    missing_lineage = 0
    for row in rows:
        provider = row["provider"]
        physical_market = row["market"]
        if (
            provider not in PROVIDER_TO_SOURCE
            or PHYSICAL_TO_CANONICAL_MARKET.get(physical_market) is None
        ):
            raise HistoricalPromotionError(
                f"unsupported legacy provider/market: {provider}/{physical_market}"
            )
        expected_market = PHYSICAL_TO_CANONICAL_MARKET[physical_market]
        if (expected_market, row["security_code"]) not in identity_map:
            raise HistoricalPromotionError(
                "legacy identity is outside the approved universe: "
                f"{physical_market}/{row['security_code']}"
            )
        instrument = identity_map[(expected_market, row["security_code"])][0]
        lifecycle = lifecycles.get(instrument.id)
        if lifecycle and row["trading_date"] >= lifecycle["effective_from"]:
            raise HistoricalPromotionError(
                "legacy row crosses canonical lifecycle boundary: "
                f"{physical_market}/{row['security_code']}/{row['trading_date']}"
            )
        lineage = row["provider_lineage"]
        if not isinstance(lineage, dict) or not REQUIRED_LINEAGE_KEYS.issubset(lineage):
            missing_lineage += 1
        else:
            if lineage["provider"] != provider or lineage["source_url"] != row["source_url"]:
                raise HistoricalPromotionError("legacy lineage/provider or source URL mismatch")
            if lineage["normalizer"] != "topicpilot.official_ohlcv.v1":
                raise HistoricalPromotionError(
                    f"unexpected legacy normalizer marker: {lineage['normalizer']}"
                )
            _as_datetime(lineage["retrieved_at"], "provider_lineage.retrieved_at")
            if not isinstance(lineage["request_params"], dict) or not lineage["response_sha256"]:
                missing_lineage += 1
        if row["created_at"] is None:
            missing_lineage += 1
        try:
            numbers = [Decimal(str(row[field])) for field in ("open", "high", "low", "close")]
            if (
                any(value < 0 for value in numbers)
                or numbers[2] > min(numbers)
                or numbers[1] < max(numbers)
            ):
                invalid_ohlcv += 1
            if row["volume"] is not None and Decimal(str(row["volume"])) < 0:
                invalid_ohlcv += 1
        except (TypeError, ValueError, ArithmeticError):
            invalid_ohlcv += 1
    if duplicate_excess or invalid_ohlcv or missing_lineage:
        raise HistoricalPromotionError(
            "legacy controls failed: "
            f"duplicates={duplicate_excess} invalid={invalid_ohlcv} "
            f"missing_lineage={missing_lineage}"
        )
    return LegacyManifest(
        row_count=len(rows),
        security_count=len(securities),
        date_min=min(dates),
        date_max=max(dates),
        twse_rows=sum(row["market"] == "TWSE" for row in rows),
        twse_securities=len({row["security_code"] for row in rows if row["market"] == "TWSE"}),
        tpex_rows=sum(row["market"] == "TPEX" for row in rows),
        tpex_securities=len({row["security_code"] for row in rows if row["market"] == "TPEX"}),
        duplicate_excess=duplicate_excess,
        invalid_ohlcv=invalid_ohlcv,
        missing_required_lineage=missing_lineage,
        manifest_sha256=stable_hash(_manifest_rows(rows)),
    )


def read_legacy_manifest(engine: Engine) -> LegacyManifest:
    """Read and validate the legacy table without writing any database state."""

    with Session(engine) as session:
        table = _legacy_table(session.connection())
        rows = [dict(row) for row in session.execute(select(table).order_by(table.c.id)).mappings()]
        identity_map, lifecycles = _load_identity_map(session)
        return _validate_legacy_rows(rows, identity_map, lifecycles)


def _read_rows(session: Session) -> list[dict[str, Any]]:
    table = _legacy_table(session.connection())
    return [
        dict(row)
        for row in session.execute(
            select(table).order_by(
                table.c.market,
                table.c.security_code,
                table.c.trading_date,
                table.c.provider,
                table.c.id,
            )
        ).mappings()
    ]


def _ensure_batch(
    session: Session,
    source: MarketDataSource,
    manifest: LegacyManifest,
    started_at: datetime,
) -> ObservationTimelineBatch:
    request_key = stable_hash(
        {
            "taskId": TASK_ID,
            "legacyTable": LEGACY_TABLE,
            "manifest": manifest.manifest_sha256,
            "bridgeContract": BRIDGE_CONTRACT_VERSION,
            "mappingPolicy": BRIDGE_MAPPING_POLICY_VERSION,
            "referenceDataVersion": REFERENCE_VERSION,
            "sourceCode": source.source_code,
            "adapterVersion": source.adapter_version,
        }
    )
    batch_id = _deterministic_id("batch", f"{source.id}:{manifest.manifest_sha256}")
    metadata_payload = {
        "taskId": TASK_ID,
        "legacyTable": LEGACY_TABLE,
        "legacyManifestSha256": manifest.manifest_sha256,
        "bridgeContractVersion": BRIDGE_CONTRACT_VERSION,
        "bridgeMappingPolicyVersion": BRIDGE_MAPPING_POLICY_VERSION,
        "normalizationContractVersion": NORMALIZATION_CONTRACT_VERSION,
        "referenceDataVersion": REFERENCE_VERSION,
        "sourceCode": source.source_code,
        "adapterVersion": source.adapter_version,
        "receivedAtPolicy": BRIDGE_RECEIVED_AT_POLICY,
        "tradingStatusPolicy": "LEGACY_LIFECYCLE_STATUS_NOT_PROMOTED",
        "rowCount": manifest.row_count,
    }
    batch = session.scalar(
        select(ObservationTimelineBatch).where(ObservationTimelineBatch.id == batch_id)
    )
    if batch is not None:
        if batch.request_key != request_key or batch.metadata_payload != metadata_payload:
            raise HistoricalPromotionError(
                "existing promotion batch conflicts with the bridge contract"
            )
        if batch.status != "COMPLETED" or batch.coverage_status != "COMPLETE":
            raise HistoricalPromotionError("existing promotion batch is not complete")
        return batch
    batch = session.scalar(
        select(ObservationTimelineBatch).where(
            ObservationTimelineBatch.source_id == source.id,
            ObservationTimelineBatch.request_key == request_key,
        )
    )
    if batch is not None:
        raise HistoricalPromotionError("promotion batch request key has an unexpected identity")
    batch = ObservationTimelineBatch(
        id=batch_id,
        source_id=source.id,
        requested_instrument_id=None,
        requested_from=datetime.combine(manifest.date_min, time.min, tzinfo=UTC),
        requested_to=datetime.combine(manifest.date_max, time.min, tzinfo=UTC),
        status="COMPLETED",
        coverage_status="COMPLETE",
        request_key=request_key,
        metadata_payload=metadata_payload,
        started_at=started_at,
        completed_at=started_at,
        created_at=started_at,
        updated_at=started_at,
    )
    session.add(batch)
    session.flush()
    return batch


def _payload(
    row: dict[str, Any], source: MarketDataSource, manifest: LegacyManifest
) -> dict[str, Any]:
    lineage = dict(row["provider_lineage"])
    return {
        "date": row["trading_date"].isoformat(),
        "open": _text_number(row["open"]),
        "high": _text_number(row["high"]),
        "low": _text_number(row["low"]),
        "close": _text_number(row["close"]),
        "volume": _text_number(row["volume"]),
        "source_symbol": row["security_code"],
        "legacy_evidence": {
            "table": LEGACY_TABLE,
            "row_id": str(row["id"]),
            "market": row["market"],
            "security_code": row["security_code"],
            "provider": row["provider"],
            "source_code": source.source_code,
            "adapter_version": source.adapter_version,
            "source_url": row["source_url"],
            "provider_lineage": lineage,
            "legacy_normalizer": lineage.get("normalizer"),
            "manifest_sha256": manifest.manifest_sha256,
            "bridge_contract_version": BRIDGE_CONTRACT_VERSION,
            "bridge_mapping_policy_version": BRIDGE_MAPPING_POLICY_VERSION,
            "raw_provider_payload_available": False,
            "received_at_policy": BRIDGE_RECEIVED_AT_POLICY,
        },
    }


def _select_by_ids(
    session: Session, table: sa.Table, ids: list[uuid.UUID], id_column: sa.Column
) -> dict[uuid.UUID, dict[str, Any]]:
    rows: dict[uuid.UUID, dict[str, Any]] = {}
    for chunk in _chunks(ids):
        for row in session.execute(select(table).where(id_column.in_(chunk))).mappings():
            rows[row[id_column]] = dict(row)
    return rows


def _verify_field(existing: dict[str, Any], expected: dict[str, Any], field: str) -> None:
    if existing.get(field) != expected.get(field):
        raise HistoricalPromotionError(
            f"idempotence conflict in {field}: {existing.get(field)!r} != {expected.get(field)!r}"
        )


def _insert_missing(
    session: Session,
    table: sa.Table,
    expected_rows: list[dict[str, Any]],
    existing_rows: dict[uuid.UUID, dict[str, Any]],
    compare_fields: tuple[str, ...],
    key_field: str = "id",
) -> int:
    missing: list[dict[str, Any]] = []
    for expected in expected_rows:
        existing = existing_rows.get(expected[key_field])
        if existing is None:
            missing.append(expected)
            continue
        for field in compare_fields:
            _verify_field(existing, expected, field)
    for chunk in _chunks(missing):
        session.execute(insert(table), chunk)
    if missing:
        session.flush()
    return len(missing)


def _assert_unique_existing(
    session: Session,
    table: sa.Table,
    source_ids: list[uuid.UUID],
    unique_column: sa.Column,
    expected_by_unique: dict[Any, uuid.UUID],
) -> None:
    for row in session.execute(
        select(table.c.id, unique_column).where(table.c.source_id.in_(source_ids))
    ).mappings():
        expected_id = expected_by_unique.get(row[unique_column])
        if expected_id is not None and expected_id != row[table.c.id]:
            raise HistoricalPromotionError(
                f"existing unique-key collision in {table.name}: {row[unique_column]}"
            )


def _prepare_specs(
    session: Session,
    rows: list[dict[str, Any]],
    manifest: LegacyManifest,
    identity_map: dict[tuple[str, str], tuple[Instrument, Market]],
    sources: dict[str, MarketDataSource],
    reference: ReferenceContext,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    policy = MappingPolicy(
        normalization_contract_version=NORMALIZATION_CONTRACT_VERSION,
        mapping_policy_version=BRIDGE_MAPPING_POLICY_VERSION,
        persist_quarantined=False,
        session_code="REGULAR",
        calendar_code="TW_MARKET",
    )
    normalizer = HistoricalDailyBarNormalizer()
    batch_started_at = datetime.now(UTC)
    batches = [
        _ensure_batch(session, sources[provider], manifest, batch_started_at)
        for provider in ("TWSE", "TPEx")
    ]
    batches_by_source = {batch.source_id: batch for batch in batches}
    raw_specs: list[dict[str, Any]] = []
    timeline_specs: list[dict[str, Any]] = []
    canonical_specs: list[dict[str, Any]] = []
    price_specs: list[dict[str, Any]] = []
    volume_specs: list[dict[str, Any]] = []
    for row in rows:
        canonical_market = PHYSICAL_TO_CANONICAL_MARKET[row["market"]]
        instrument, market = identity_map[(canonical_market, row["security_code"])]
        source = sources[row["provider"]]
        payload = _payload(row, source, manifest)
        observed_at = _market_date_anchor(row["trading_date"], market.timezone)
        retrieved_at = _as_datetime(
            row["provider_lineage"]["retrieved_at"], "provider_lineage.retrieved_at"
        )
        received_at = _as_datetime(row["created_at"], "legacy created_at / bridge received_at")
        raw_id = _deterministic_id("raw", row["id"])
        timeline_id = _deterministic_id("timeline", row["id"])
        batch = batches_by_source[source.id]
        raw_specs.append(
            {
                "id": raw_id,
                "source_id": source.id,
                "instrument_id": instrument.id,
                "upstream_observation_id": (
                    f"hist-002b:{row['market']}:{row['security_code']}"
                    f":{row['trading_date']}:{row['id']}"
                ),
                "source_instrument_identifier": row["security_code"],
                "observed_at": observed_at,
                "retrieved_at": retrieved_at,
                "payload": payload,
                "content_hash": stable_hash(payload),
                "quality_status": "CAPTURED",
                "ingestion_correlation_id": batch.request_key,
                "supersedes_id": None,
                "created_at": batch_started_at,
            }
        )
        timeline_payload_hash = stable_hash({"raw": stable_hash(payload), "payload": payload})
        timeline_specs.append(
            {
                "id": timeline_id,
                "instrument_id": instrument.id,
                "source_id": source.id,
                "raw_observation_id": raw_id,
                "batch_id": batch.id,
                "observed_at": observed_at,
                "received_at": received_at,
                "retrieved_at": retrieved_at,
                "ordering_key": row["trading_date"].isoformat(),
                "payload": payload,
                "content_hash": timeline_payload_hash,
                "supersedes_id": None,
                "entry_status": "ACTIVE",
                "created_at": batch_started_at,
            }
        )
        normalized = normalizer(
            InputEnvelope(
                payload=payload,
                instrument_id=instrument.id,
                source_id=source.id,
                timeline_entry_id=timeline_id,
                raw_observation_id=raw_id,
                observed_at=observed_at,
                received_at=received_at,
                retrieved_at=retrieved_at,
                ordering_key=row["trading_date"].isoformat(),
            ),
            reference,
            policy,
        )
        if normalized.failures:
            raise HistoricalPromotionError(
                f"normalizer rejected legacy row {row['id']}: "
                f"{[failure.code for failure in normalized.failures]}"
            )
        families = {candidate.family_code for candidate in normalized.candidates}
        if "PRICE" not in families or any(
            candidate.quality_state != "ACCEPTED" for candidate in normalized.candidates
        ):
            raise HistoricalPromotionError(
                f"legacy row {row['id']} has no accepted PRICE disposition"
            )
        for candidate in normalized.candidates:
            if candidate.family_code not in {"PRICE", "VOLUME"}:
                raise HistoricalPromotionError(
                    f"legacy row {row['id']} produced an unauthorized family: "
                    f"{candidate.family_code}"
                )
            content_hash = stable_hash(
                {
                    "family": candidate.family_code,
                    "values": candidate.values,
                    "paths": candidate.source_paths,
                }
            )
            idempotency_key = stable_hash(
                {
                    "entry": timeline_id,
                    "family": candidate.family_code,
                    "content": content_hash,
                    "contract": policy.normalization_contract_version,
                    "mapping": policy.mapping_policy_version,
                    "reference": reference.reference_data_version,
                }
            )
            canonical_id = _deterministic_id("canonical", row["id"], candidate.family_code)
            validation_summary = {
                **candidate.validation,
                "bridgeContractVersion": BRIDGE_CONTRACT_VERSION,
                "bridgeMappingPolicyVersion": BRIDGE_MAPPING_POLICY_VERSION,
                "legacyTable": LEGACY_TABLE,
                "legacyRowId": str(row["id"]),
                "legacyNormalizer": row["provider_lineage"]["normalizer"],
                "receivedAtPolicy": BRIDGE_RECEIVED_AT_POLICY,
            }
            canonical_specs.append(
                {
                    "id": canonical_id,
                    "timeline_entry_id": timeline_id,
                    "instrument_id": instrument.id,
                    "source_id": source.id,
                    "raw_observation_id": raw_id,
                    "session_code": reference.session_code,
                    "timezone_name": reference.timezone_name,
                    "calendar_code": reference.calendar_code,
                    "family_code": candidate.family_code,
                    "observed_at": ensure_utc(observed_at),
                    "received_at": received_at,
                    "retrieved_at": retrieved_at,
                    "source_field_path": candidate.source_field_path,
                    "ordering_key": row["trading_date"].isoformat(),
                    "normalization_contract_version": policy.normalization_contract_version,
                    "mapping_policy_version": policy.mapping_policy_version,
                    "reference_data_version": reference.reference_data_version,
                    "quality_state": candidate.quality_state,
                    "quality_warnings": {"warnings": list(candidate.warnings)},
                    "validation_summary": validation_summary,
                    "disposition": "PROMOTED_FROM_HIST_002B",
                    "supersedes_id": None,
                    "content_hash": content_hash,
                    "idempotency_key": idempotency_key,
                    "created_at": batch_started_at,
                    "updated_at": batch_started_at,
                }
            )
            if candidate.family_code == "PRICE":
                price_specs.append({"canonical_observation_id": canonical_id, **candidate.values})
            elif candidate.family_code == "VOLUME":
                volume_specs.append({"canonical_observation_id": canonical_id, **candidate.values})
    return raw_specs, timeline_specs, canonical_specs, price_specs, volume_specs


def promote(engine: Engine, *, local_only: bool) -> PromotionResult:
    """Promote all HIST-002B rows in one transaction and return write counts."""

    _assert_local_target(engine, local_only=local_only)
    with Session(engine) as session, session.begin():
        _assert_schema(session)
        rows = _read_rows(session)
        identity_map, lifecycles = _load_identity_map(session)
        manifest = _validate_legacy_rows(rows, identity_map, lifecycles)
        sources = _load_sources(session)
        reference = _load_reference_context(session)
        raw_specs, timeline_specs, canonical_specs, price_specs, volume_specs = _prepare_specs(
            session, rows, manifest, identity_map, sources, reference
        )

        source_ids = [source.id for source in sources.values()]
        raw_table = RawMarketObservation.__table__
        timeline_table = ObservationTimelineEntry.__table__
        canonical_table = CanonicalObservation.__table__
        price_table = CanonicalPriceObservation.__table__
        volume_table = CanonicalVolumeObservation.__table__

        _assert_unique_existing(
            session,
            raw_table,
            source_ids,
            raw_table.c.content_hash,
            {row["content_hash"]: row["id"] for row in raw_specs},
        )
        raw_existing = _select_by_ids(
            session, raw_table, [row["id"] for row in raw_specs], raw_table.c.id
        )
        raw_created = _insert_missing(
            session,
            raw_table,
            raw_specs,
            raw_existing,
            (
                "source_id",
                "instrument_id",
                "upstream_observation_id",
                "source_instrument_identifier",
                "observed_at",
                "retrieved_at",
                "payload",
                "content_hash",
                "quality_status",
                "ingestion_correlation_id",
                "supersedes_id",
            ),
        )
        _assert_unique_existing(
            session,
            timeline_table,
            source_ids,
            timeline_table.c.raw_observation_id,
            {row["raw_observation_id"]: row["id"] for row in timeline_specs},
        )
        timeline_existing = _select_by_ids(
            session, timeline_table, [row["id"] for row in timeline_specs], timeline_table.c.id
        )
        timeline_created = _insert_missing(
            session,
            timeline_table,
            timeline_specs,
            timeline_existing,
            (
                "instrument_id",
                "source_id",
                "raw_observation_id",
                "batch_id",
                "observed_at",
                "received_at",
                "retrieved_at",
                "ordering_key",
                "payload",
                "content_hash",
                "supersedes_id",
                "entry_status",
            ),
        )
        _assert_unique_existing(
            session,
            canonical_table,
            source_ids,
            canonical_table.c.idempotency_key,
            {row["idempotency_key"]: row["id"] for row in canonical_specs},
        )
        canonical_existing = _select_by_ids(
            session,
            canonical_table,
            [row["id"] for row in canonical_specs],
            canonical_table.c.id,
        )
        canonical_missing_ids = {
            row["id"] for row in canonical_specs if row["id"] not in canonical_existing
        }
        canonical_created = _insert_missing(
            session,
            canonical_table,
            canonical_specs,
            canonical_existing,
            (
                "timeline_entry_id",
                "instrument_id",
                "source_id",
                "raw_observation_id",
                "session_code",
                "timezone_name",
                "calendar_code",
                "family_code",
                "observed_at",
                "received_at",
                "retrieved_at",
                "source_field_path",
                "ordering_key",
                "normalization_contract_version",
                "mapping_policy_version",
                "reference_data_version",
                "quality_state",
                "quality_warnings",
                "validation_summary",
                "disposition",
                "supersedes_id",
                "content_hash",
                "idempotency_key",
            ),
        )
        price_existing = _select_by_ids(
            session,
            price_table,
            [row["canonical_observation_id"] for row in price_specs],
            price_table.c.canonical_observation_id,
        )
        price_created = _insert_missing(
            session,
            price_table,
            price_specs,
            price_existing,
            (
                "open",
                "high",
                "low",
                "close",
                "last",
                "vwap",
                "price_currency_code",
                "price_scale",
                "adjustment_state",
                "price_context",
            ),
            key_field="canonical_observation_id",
        )
        volume_existing = _select_by_ids(
            session,
            volume_table,
            [row["canonical_observation_id"] for row in volume_specs],
            volume_table.c.canonical_observation_id,
        )
        volume_created = _insert_missing(
            session,
            volume_table,
            volume_specs,
            volume_existing,
            (
                "volume_quantity",
                "volume_unit_code",
                "volume_scale",
                "turnover_amount",
                "turnover_currency_code",
                "turnover_scale",
                "aggregation_code",
                "volume_context",
            ),
            key_field="canonical_observation_id",
        )
        session.flush()
        return PromotionResult(
            manifest=manifest,
            raw_created=raw_created,
            raw_reused=len(raw_specs) - raw_created,
            timeline_created=timeline_created,
            timeline_reused=len(timeline_specs) - timeline_created,
            canonical_created={
                "PRICE": sum(
                    row["family_code"] == "PRICE" and row["id"] in canonical_missing_ids
                    for row in canonical_specs
                ),
                "VOLUME": volume_created,
            },
            canonical_reused={
                "PRICE": len(price_specs) - price_created,
                "VOLUME": len(volume_specs) - volume_created,
            },
            status_rows_created=0,
            rejected_rows=0,
            quarantined_rows=0,
            noop=(
                raw_created == 0
                and timeline_created == 0
                and canonical_created == 0
                and price_created == 0
                and volume_created == 0
            ),
        )


def _engine_from_settings() -> Engine:
    from sqlalchemy import create_engine

    settings = get_settings()
    return create_engine(
        settings.migration_database_url or settings.database_url, pool_pre_ping=True
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Promote HIST-002B evidence into V2 canonical observations"
    )
    parser.add_argument("--local-only", action="store_true", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    engine = _engine_from_settings()
    try:
        _assert_local_target(engine, local_only=args.local_only)
        if args.dry_run:
            with Session(engine) as session:
                _assert_schema(session)
                identity_map, lifecycles = _load_identity_map(session)
                rows = _read_rows(session)
                manifest = _validate_legacy_rows(rows, identity_map, lifecycles)
                print(json.dumps(manifest.to_dict(), ensure_ascii=False, sort_keys=True))
            return 0
        first = promote(engine, local_only=args.local_only)
        second = promote(engine, local_only=args.local_only)
        if not second.noop:
            raise HistoricalPromotionError("exact rerun was not a no-op")
        print(
            json.dumps(
                {"first": first.to_dict(), "rerun": second.to_dict()},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except HistoricalPromotionError as exc:
        print(
            json.dumps({"taskId": TASK_ID, "error": str(exc)}, ensure_ascii=False, sort_keys=True)
        )
        return 2
    finally:
        engine.dispose()


__all__ = [
    "BRIDGE_CONTRACT_VERSION",
    "BRIDGE_MAPPING_POLICY_VERSION",
    "HistoricalPromotionError",
    "LegacyManifest",
    "PromotionResult",
    "main",
    "promote",
    "read_legacy_manifest",
]


if __name__ == "__main__":
    raise SystemExit(main())
