"""Build the approved, synthetic PostgreSQL integration fixture.

This module is intentionally test-only plumbing.  It uses the committed
``tw-reference-v1`` bundle and creates a small deterministic canonical-history
sample for the historical read contract.  It never connects to a provider and
never targets Production.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from topicpilot_api.reference_data import load_bundle
from topicpilot_api.reference_data.bootstrap import bootstrap_reference_bundle

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BUNDLE_PATH = (
    REPOSITORY_ROOT
    / "services"
    / "api"
    / "src"
    / "topicpilot_api"
    / "reference_data"
    / "bundles"
    / "tw-reference-v1"
)
FIXTURE_ID = "topicpilot-db-integration-v1"
REFERENCE_VERSION = "tw-reference-v1"
NORMALIZATION_VERSION = "normalization-contract-v1"
MAPPING_POLICY_VERSION = "hist-002b-synthetic-fixture-v1"
NAMESPACE = uuid.UUID("f2c8b1db-7f2d-5d75-b1e4-0f70e5cc1c20")
TAIPEI = ZoneInfo("Asia/Taipei")

SPECS: tuple[dict[str, Any], ...] = (
    {
        "market": "TPE",
        "code": "2330",
        "source_code": "TWSE_OFFICIAL_DAILY",
        "adapter_version": "twse-official-daily.v1",
        "count": 126,
        "end": date(2026, 8, 13),
        "price_base": Decimal(100),
    },
    {
        "market": "TWO",
        "code": "6488",
        "source_code": "TPEX_OFFICIAL_DAILY",
        "adapter_version": "tpex-official-daily.v1",
        "count": 126,
        "end": date(2026, 8, 13),
        "price_base": Decimal(200),
    },
    {
        "market": "TPE",
        "code": "6806",
        "source_code": "TWSE_OFFICIAL_DAILY",
        "adapter_version": "twse-official-daily.v1",
        "count": 88,
        "end": date(2026, 6, 22),
        "price_base": Decimal(300),
    },
)


def _stable_uuid(kind: str, value: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"{kind}:{value}")


def _dates(count: int, end: date) -> tuple[date, ...]:
    start = date(2026, 2, 2)
    candidates: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            candidates.append(current)
        current += timedelta(days=1)
    if len(candidates) < count:
        raise ValueError(f"fixture date range cannot provide {count} weekdays")
    selected = candidates[: count - 1]
    if end not in selected:
        selected.append(end)
    return tuple(selected)


def _json_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _ensure_source(session: Session, spec: dict[str, Any]) -> uuid.UUID:
    row = session.execute(
        text(
            """
            SELECT id FROM topicpilot.market_data_sources
            WHERE source_code=:source_code AND adapter_version=:adapter_version
            """
        ),
        spec,
    ).scalar_one_or_none()
    if row is not None:
        return row
    source_id = _stable_uuid("source", spec["source_code"])
    session.execute(
        text(
            """
            INSERT INTO topicpilot.market_data_sources
                (id, source_code, source_category, adapter_version,
                 observation_semantics, adjustment_policy, calendar_policy,
                 licensing_classification, status)
            VALUES
                (:id, :source_code, 'SYNTHETIC_TEST', :adapter_version,
                 'DAILY_BAR', 'UNKNOWN', 'tw-reference-v1',
                 'PUBLIC_SYNTHETIC_TEST', 'REGISTERED')
            ON CONFLICT (source_code, adapter_version) DO NOTHING
            """
        ),
        {**spec, "id": source_id},
    )
    return session.execute(
        text(
            """
            SELECT id FROM topicpilot.market_data_sources
            WHERE source_code=:source_code AND adapter_version=:adapter_version
            """
        ),
        spec,
    ).scalar_one()


def _instrument_id(session: Session, market: str, code: str) -> uuid.UUID:
    row = session.execute(
        text(
            """
            SELECT i.id
            FROM topicpilot.instruments i
            JOIN topicpilot.markets m ON m.id=i.market_id
            WHERE m.code=:market AND i.instrument_code=:code AND i.is_active=true
            """
        ),
        {"market": market, "code": code},
    ).scalar_one_or_none()
    if row is None:
        raise RuntimeError(f"approved reference bundle did not create {market}:{code}")
    return row


def _seed_spec(session: Session, spec: dict[str, Any]) -> int:
    source_id = _ensure_source(session, spec)
    instrument_id = _instrument_id(session, spec["market"], spec["code"])
    dates = _dates(spec["count"], spec["end"])
    batch_id = _stable_uuid("batch", f"{spec['market']}:{spec['code']}")
    request_key = f"{FIXTURE_ID}:{spec['market']}:{spec['code']}"
    requested_from = datetime.combine(dates[0], time.min, tzinfo=TAIPEI)
    requested_to = datetime.combine(dates[-1], time.min, tzinfo=TAIPEI)
    session.execute(
        text(
            """
            INSERT INTO topicpilot.observation_timeline_batches
                (id, source_id, requested_instrument_id, requested_from,
                 requested_to, status, coverage_status, request_key, metadata,
                 completed_at)
            VALUES
                (:id, :source_id, :instrument_id, :requested_from,
                 :requested_to, 'COMPLETED', 'COMPLETE', :request_key,
                 CAST(:metadata AS jsonb), :completed_at)
            ON CONFLICT (source_id, request_key) DO NOTHING
            """
        ),
        {
            "id": batch_id,
            "source_id": source_id,
            "instrument_id": instrument_id,
            "requested_from": requested_from,
            "requested_to": requested_to,
            "request_key": request_key,
            "metadata": json.dumps(
                {
                    "fixtureId": FIXTURE_ID,
                    "fixtureTestOnly": True,
                    "referenceVersion": REFERENCE_VERSION,
                    "historicalSource": "synthetic-representative",
                    "sourceTask": "TASK-DATA-HIST-002B",
                }
            ),
            "completed_at": datetime(2026, 8, 13, 9, 0, tzinfo=UTC),
        },
    )

    inserted = 0
    for index, trading_date in enumerate(dates):
        observed_at = datetime.combine(trading_date, time.min, tzinfo=TAIPEI)
        retrieved_at = datetime(2026, 8, 13, 9, 0, tzinfo=UTC) + timedelta(minutes=index)
        close = spec["price_base"] + Decimal(index) / Decimal(10)
        payload = {
            "fixtureId": FIXTURE_ID,
            "fixtureTestOnly": True,
            "market": spec["market"],
            "instrumentCode": spec["code"],
            "tradingDate": trading_date.isoformat(),
            "open": str(close - Decimal(1)),
            "high": str(close + Decimal(1)),
            "low": str(close - Decimal(2)),
            "close": str(close),
            "volume": str(1000 + index),
            "referenceDataVersion": REFERENCE_VERSION,
        }
        content_hash = _json_hash(payload)
        raw_id = _stable_uuid("raw", f"{spec['market']}:{spec['code']}:{trading_date}")
        entry_id = _stable_uuid("timeline", f"{spec['market']}:{spec['code']}:{trading_date}")
        session.execute(
            text(
                """
                INSERT INTO topicpilot.raw_market_observations
                    (id, source_id, instrument_id, source_instrument_identifier,
                     observed_at, retrieved_at, payload, content_hash,
                     quality_status, ingestion_correlation_id)
                VALUES
                    (:id, :source_id, :instrument_id, :identifier,
                     :observed_at, :retrieved_at, CAST(:payload AS jsonb),
                     :content_hash, 'CAPTURED', :correlation)
                ON CONFLICT (source_id, content_hash) DO NOTHING
                """
            ),
            {
                "id": raw_id,
                "source_id": source_id,
                "instrument_id": instrument_id,
                "identifier": f"{spec['market']}:{spec['code']}",
                "observed_at": observed_at,
                "retrieved_at": retrieved_at,
                "payload": json.dumps(payload),
                "content_hash": content_hash,
                "correlation": f"{FIXTURE_ID}:{spec['market']}:{spec['code']}",
            },
        )
        session.execute(
            text(
                """
                INSERT INTO topicpilot.observation_timeline_entries
                    (id, instrument_id, source_id, raw_observation_id, batch_id,
                     observed_at, received_at, retrieved_at, ordering_key,
                     payload, content_hash, entry_status)
                VALUES
                    (:id, :instrument_id, :source_id, :raw_id, :batch_id,
                     :observed_at, :received_at, :retrieved_at, :ordering_key,
                     CAST(:payload AS jsonb), :content_hash, 'ACTIVE')
                ON CONFLICT (raw_observation_id) DO NOTHING
                """
            ),
            {
                "id": entry_id,
                "instrument_id": instrument_id,
                "source_id": source_id,
                "raw_id": raw_id,
                "batch_id": batch_id,
                "observed_at": observed_at,
                "received_at": retrieved_at,
                "retrieved_at": retrieved_at,
                "ordering_key": f"{trading_date.isoformat()}:{index:04d}",
                "payload": json.dumps(payload),
                "content_hash": content_hash,
            },
        )
        for family in ("PRICE", "VOLUME"):
            canonical_id = _stable_uuid(
                "canonical", f"{spec['market']}:{spec['code']}:{trading_date}:{family}"
            )
            idempotency_key = f"{FIXTURE_ID}:{spec['market']}:{spec['code']}:{trading_date}:{family}"
            session.execute(
                text(
                    """
                    INSERT INTO topicpilot.canonical_observations
                        (id, timeline_entry_id, instrument_id, source_id,
                         raw_observation_id, session_code, timezone_name,
                         calendar_code, family_code, observed_at, received_at,
                         retrieved_at, source_field_path, ordering_key,
                         normalization_contract_version, mapping_policy_version,
                         reference_data_version, quality_state, validation_summary,
                         disposition, content_hash, idempotency_key)
                    VALUES
                        (:id, :entry_id, :instrument_id, :source_id, :raw_id,
                         'REGULAR', 'Asia/Taipei', 'TWSE_TPEX', :family,
                         :observed_at, :received_at, :retrieved_at, :field_path,
                         :ordering_key, :normalization_version, :mapping_version,
                         :reference_version, 'ACCEPTED', CAST(:validation AS jsonb),
                         'ACCEPTED', :content_hash, :idempotency_key)
                    ON CONFLICT (idempotency_key) DO NOTHING
                    """
                ),
                {
                    "id": canonical_id,
                    "entry_id": entry_id,
                    "instrument_id": instrument_id,
                    "source_id": source_id,
                    "raw_id": raw_id,
                    "family": family,
                    "observed_at": observed_at,
                    "received_at": retrieved_at,
                    "retrieved_at": retrieved_at,
                    "field_path": "/close" if family == "PRICE" else "/volume",
                    "ordering_key": f"{trading_date.isoformat()}:{index:04d}:{family}",
                    "normalization_version": NORMALIZATION_VERSION,
                    "mapping_version": MAPPING_POLICY_VERSION,
                    "reference_version": REFERENCE_VERSION,
                    "validation": json.dumps(
                        {"fixtureId": FIXTURE_ID, "synthetic": True, "family": family}
                    ),
                    "content_hash": f"{content_hash}:{family}",
                    "idempotency_key": idempotency_key,
                },
            )
            if family == "PRICE":
                session.execute(
                    text(
                        """
                        INSERT INTO topicpilot.canonical_price_observations
                            (canonical_observation_id, open, high, low, close, last,
                             price_currency_code, price_scale, adjustment_state,
                             price_context)
                        VALUES
                            (:id, :open, :high, :low, :close, :close,
                             'TWD', 2, 'UNKNOWN', CAST(:context AS jsonb))
                        ON CONFLICT (canonical_observation_id) DO NOTHING
                        """
                    ),
                    {
                        "id": canonical_id,
                        "open": close - Decimal(1),
                        "high": close + Decimal(1),
                        "low": close - Decimal(2),
                        "close": close,
                        "context": json.dumps({"fixtureId": FIXTURE_ID, "synthetic": True}),
                    },
                )
            else:
                session.execute(
                    text(
                        """
                        INSERT INTO topicpilot.canonical_volume_observations
                            (canonical_observation_id, volume_quantity,
                             volume_unit_code, volume_scale, aggregation_code,
                             volume_context)
                        VALUES
                            (:id, :volume, 'UNIT', 0, 'DAILY_TOTAL',
                             CAST(:context AS jsonb))
                        ON CONFLICT (canonical_observation_id) DO NOTHING
                        """
                    ),
                    {
                        "id": canonical_id,
                        "volume": Decimal(1000 + index),
                        "context": json.dumps({"fixtureId": FIXTURE_ID, "synthetic": True}),
                    },
                )
        inserted += 1
    return inserted


def build_fixture(database_url: str) -> dict[str, Any]:
    if not database_url:
        raise ValueError("TEST_DATABASE_URL is required")
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        if connection.execute(text("select current_database()" )).scalar_one() in {
            "postgres",
            "template0",
            "template1",
        }:
            raise ValueError("fixture refuses system databases")
        migration = connection.execute(
            text("select version_num from alembic_version")
        ).scalar_one_or_none()
    if migration != "0030_task_topic_daily_state_formal_authority":
        raise ValueError(f"fixture requires migration 0030, got {migration!r}")

    bundle = load_bundle(BUNDLE_PATH)
    with Session(engine) as session:
        bootstrap_reference_bundle(session, bundle, activate=True)
    with Session(engine) as session, session.begin():
        seeded = sum(_seed_spec(session, spec) for spec in SPECS)
    with engine.connect() as connection:
        counts = {
            "referenceRegistrySets": connection.execute(
                text(
                    "select count(*) from topicpilot.reference_registry_sets "
                    "where reference_data_version=:version and status='ACTIVE'"
                ),
                {"version": REFERENCE_VERSION},
            ).scalar_one(),
            "instruments": connection.execute(
                text("select count(*) from topicpilot.instruments")
            ).scalar_one(),
            "rawRows": connection.execute(
                text("select count(*) from topicpilot.raw_market_observations "
                     "where payload->>'fixtureId'=:fixture")
                , {"fixture": FIXTURE_ID},
            ).scalar_one(),
            "timelineRows": connection.execute(
                text("select count(*) from topicpilot.observation_timeline_entries "
                     "where payload->>'fixtureId'=:fixture")
                , {"fixture": FIXTURE_ID},
            ).scalar_one(),
            "canonicalPriceRows": connection.execute(
                text("select count(*) from topicpilot.canonical_observations "
                     "where idempotency_key like :prefix and family_code='PRICE'")
                , {"prefix": f"{FIXTURE_ID}:%"},
            ).scalar_one(),
            "canonicalVolumeRows": connection.execute(
                text("select count(*) from topicpilot.canonical_observations "
                     "where idempotency_key like :prefix and family_code='VOLUME'")
                , {"prefix": f"{FIXTURE_ID}:%"},
            ).scalar_one(),
        }
    engine.dispose()
    return {
        "fixtureId": FIXTURE_ID,
        "fixtureTestOnly": True,
        "referenceVersion": REFERENCE_VERSION,
        "bundleSha256": bundle.digest(),
        "migration": migration,
        "seedCalls": len(SPECS),
        "seededRepresentativeSessions": seeded,
        "expectedRepresentativeSessions": sum(spec["count"] for spec in SPECS),
        "counts": counts,
        "idempotent": True,
        "productionMutation": False,
        "providerCalls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.getenv("TEST_DATABASE_URL"))
    args = parser.parse_args()
    print(json.dumps(build_fixture(args.database_url), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
