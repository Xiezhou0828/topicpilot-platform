from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from topicpilot_api.normalizer import (
    MappingPolicy,
    NormalizationCandidate,
    NormalizationResult,
    NormalizationRuntime,
    NormalizerKey,
    NormalizerRegistry,
    SyntheticReferenceNormalizer,
)
from topicpilot_api.normalizer.runtime import RuntimeLoadError

pytestmark = pytest.mark.postgres

T0 = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def runtime_ids(postgres_engine):
    token = uuid.uuid4().hex[:10]
    ids = {
        "market": uuid.uuid4(),
        "instrument": uuid.uuid4(),
        "source": uuid.uuid4(),
        "batch": uuid.uuid4(),
        "raw": uuid.uuid4(),
        "entry": uuid.uuid4(),
        "reference": uuid.uuid4(),
        "currency": uuid.uuid4(),
        "timezone": uuid.uuid4(),
        "session": uuid.uuid4(),
        "status": uuid.uuid4(),
        "adjustment": uuid.uuid4(),
        "version": f"runtime-test-{token}",
        "market_code": f"NORM-{token}",
        "instrument_code": f"NORM.EQ.{token}",
        "source_code": f"SYNTHETIC_{token}",
    }
    with postgres_engine.begin() as cx:
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.markets
                    (id, code, name, timezone, calendar_code)
                VALUES (:id, :code, 'Normalizer Test Market', 'UTC', 'TW')
                """
            ),
            {"id": ids["market"], "code": ids["market_code"]},
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.instruments
                    (id, market_id, instrument_code, name, instrument_type, currency)
                VALUES (:id, :market, :code, 'Normalizer Test Equity', 'EQUITY', 'TWD')
                """
            ),
            {
                "id": ids["instrument"],
                "market": ids["market"],
                "code": ids["instrument_code"],
            },
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.market_data_sources
                    (id, source_code, source_category, adapter_version, status)
                VALUES (:id, :source_code, 'SYNTHETIC', 'v1', 'ACTIVE')
                """
            ),
            {"id": ids["source"], "source_code": ids["source_code"]},
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.observation_timeline_batches
                    (id, source_id, requested_instrument_id, requested_from,
                     requested_to, status, coverage_status)
                VALUES (:id, :source, :instrument, :observed, :observed, 'OPEN', 'UNKNOWN')
                """
            ),
            {
                "id": ids["batch"],
                "source": ids["source"],
                "instrument": ids["instrument"],
                "observed": T0,
            },
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.reference_registry_sets
                    (id, reference_data_version, status, description)
                VALUES (:id, :version, 'ACTIVE', 'Normalizer runtime integration fixture')
                """
            ),
            {"id": ids["reference"], "version": ids["version"]},
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.reference_currencies (id, registry_set_id, code, scale)
                VALUES (:id, :registry, 'TWD', 2)
                """
            ),
            {"id": ids["currency"], "registry": ids["reference"]},
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.reference_timezones (id, registry_set_id, name)
                VALUES (:id, :registry, 'UTC')
                """
            ),
            {"id": ids["timezone"], "registry": ids["reference"]},
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.reference_sessions
                    (id, registry_set_id, code, calendar_code)
                VALUES (:id, :registry, 'REGULAR', 'TW')
                """
            ),
            {"id": ids["session"], "registry": ids["reference"]},
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.reference_trading_statuses (id, registry_set_id, code)
                VALUES (:id, :registry, 'OPEN')
                """
            ),
            {"id": ids["status"], "registry": ids["reference"]},
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.reference_adjustments (id, registry_set_id, code)
                VALUES (:id, :registry, 'UNKNOWN')
                """
            ),
            {"id": ids["adjustment"], "registry": ids["reference"]},
        )
    try:
        yield ids
    finally:
        with postgres_engine.begin() as cx:
            cx.execute(text("ALTER TABLE topicpilot.canonical_observations DISABLE TRIGGER USER"))
            cx.execute(
                text("ALTER TABLE topicpilot.canonical_price_observations DISABLE TRIGGER USER")
            )
            cx.execute(
                text("ALTER TABLE topicpilot.canonical_volume_observations DISABLE TRIGGER USER")
            )
            cx.execute(
                text("ALTER TABLE topicpilot.canonical_quote_observations DISABLE TRIGGER USER")
            )
            cx.execute(
                text(
                    "ALTER TABLE topicpilot.canonical_trading_status_observations "
                    "DISABLE TRIGGER USER"
                )
            )
            cx.execute(
                text("DELETE FROM topicpilot.canonical_observations WHERE instrument_id=:id"),
                {"id": ids["instrument"]},
            )
            cx.execute(
                text(
                    "ALTER TABLE topicpilot.canonical_trading_status_observations "
                    "ENABLE TRIGGER USER"
                )
            )
            cx.execute(
                text("ALTER TABLE topicpilot.canonical_quote_observations ENABLE TRIGGER USER")
            )
            cx.execute(
                text("ALTER TABLE topicpilot.canonical_volume_observations ENABLE TRIGGER USER")
            )
            cx.execute(
                text("ALTER TABLE topicpilot.canonical_price_observations ENABLE TRIGGER USER")
            )
            cx.execute(text("ALTER TABLE topicpilot.canonical_observations ENABLE TRIGGER USER"))
            cx.execute(
                text("DELETE FROM topicpilot.observation_timeline_entries WHERE instrument_id=:id"),
                {"id": ids["instrument"]},
            )
            cx.execute(
                text("DELETE FROM topicpilot.raw_market_observations WHERE instrument_id=:id"),
                {"id": ids["instrument"]},
            )
            cx.execute(
                text("DELETE FROM topicpilot.reference_adjustments WHERE id=:id"),
                {"id": ids["adjustment"]},
            )
            cx.execute(
                text("DELETE FROM topicpilot.reference_trading_statuses WHERE id=:id"),
                {"id": ids["status"]},
            )
            cx.execute(
                text("DELETE FROM topicpilot.reference_sessions WHERE id=:id"),
                {"id": ids["session"]},
            )
            cx.execute(
                text("DELETE FROM topicpilot.reference_timezones WHERE id=:id"),
                {"id": ids["timezone"]},
            )
            cx.execute(
                text("DELETE FROM topicpilot.reference_currencies WHERE id=:id"),
                {"id": ids["currency"]},
            )
            cx.execute(
                text("DELETE FROM topicpilot.reference_registry_sets WHERE id=:id"),
                {"id": ids["reference"]},
            )
            cx.execute(
                text("DELETE FROM topicpilot.observation_timeline_batches WHERE id=:id"),
                {"id": ids["batch"]},
            )
            cx.execute(
                text("DELETE FROM topicpilot.market_data_sources WHERE id=:id"),
                {"id": ids["source"]},
            )
            cx.execute(
                text("DELETE FROM topicpilot.instruments WHERE id=:id"),
                {"id": ids["instrument"]},
            )
            cx.execute(
                text("DELETE FROM topicpilot.markets WHERE id=:id"),
                {"id": ids["market"]},
            )


def _insert_entry(cx, ids, *, entry_id, raw_id, payload, observed_at, ordering, supersedes=None):
    content_hash = f"entry-{entry_id}"
    cx.execute(
        text(
            """
            INSERT INTO topicpilot.raw_market_observations
                (id, source_id, instrument_id, source_instrument_identifier,
                 observed_at, retrieved_at, payload, content_hash)
            VALUES (:raw, :source, :instrument, :identifier, :observed, :observed,
                    CAST(:payload AS jsonb), :raw_hash)
            """
        ),
        {
            "raw": raw_id,
            "source": ids["source"],
            "instrument": ids["instrument"],
            "identifier": ids["instrument_code"],
            "observed": observed_at,
            "payload": json.dumps(payload),
            "raw_hash": f"raw-{raw_id}",
        },
    )
    cx.execute(
        text(
            """
            INSERT INTO topicpilot.observation_timeline_entries
                (id, instrument_id, source_id, raw_observation_id, batch_id,
                 observed_at, received_at, retrieved_at, ordering_key, payload,
                 content_hash, entry_status, supersedes_id)
            VALUES (:entry, :instrument, :source, :raw, :batch, :observed, :observed,
                    :observed, :ordering, CAST(:payload AS jsonb), :content_hash,
                    'ACTIVE', :supersedes)
            """
        ),
        {
            "entry": entry_id,
            "instrument": ids["instrument"],
            "source": ids["source"],
            "raw": raw_id,
            "batch": ids["batch"],
            "observed": observed_at,
            "ordering": ordering,
            "payload": json.dumps(payload),
            "content_hash": content_hash,
            "supersedes": supersedes,
        },
    )


def _create_entry(
    postgres_engine, ids, *, payload, observed_at=T0, ordering="001", supersedes=None
):
    entry_id, raw_id = uuid.uuid4(), uuid.uuid4()
    with postgres_engine.begin() as cx:
        _insert_entry(
            cx,
            ids,
            entry_id=entry_id,
            raw_id=raw_id,
            payload=payload,
            observed_at=observed_at,
            ordering=ordering,
            supersedes=supersedes,
        )
    return entry_id


def _policy(mapping_policy_version="synthetic-mapping-v1"):
    return MappingPolicy(mapping_policy_version=mapping_policy_version)


def _registry(ids, mapping_policy_version="synthetic-mapping-v1", mapper=None):
    return NormalizerRegistry(
        {
            NormalizerKey(
                ids["source_code"],
                "v1",
                "normalization-contract-v1",
                mapping_policy_version,
            ): mapper or SyntheticReferenceNormalizer()
        }
    )


def _run(postgres_engine, entry_id, ids, *, policy=None, registry=None):
    factory = sessionmaker(bind=postgres_engine, expire_on_commit=False)
    with factory() as session, session.begin():
        effective_policy = policy or _policy()
        effective_registry = registry or _registry(ids, effective_policy.mapping_policy_version)
        return NormalizationRuntime(session, effective_registry).normalize_timeline_entry(
            entry_id, effective_policy, ids["version"]
        )


def test_runtime_persists_all_synthetic_families_and_idempotent_rerun(postgres_engine, runtime_ids):
    entry_id = _create_entry(
        postgres_engine,
        runtime_ids,
        payload={"last": "123.4500", "volume": "5", "trading_status": "OPEN"},
    )

    first = _run(postgres_engine, entry_id, runtime_ids)
    assert {row.family_code for row in first.persisted} == {"PRICE", "VOLUME", "TRADING_STATUS"}
    assert all(row.created for row in first.persisted)
    assert first.existing == ()

    second = _run(postgres_engine, entry_id, runtime_ids)
    assert len(second.persisted) == 3
    assert all(not row.created for row in second.persisted)
    assert len(second.existing) == 3

    with postgres_engine.connect() as cx:
        count = cx.execute(
            text(
                "SELECT count(*) FROM topicpilot.canonical_observations "
                "WHERE timeline_entry_id=:entry"
            ),
            {"entry": entry_id},
        ).scalar_one()
    assert count == 3


def test_runtime_correction_supersedes_current_family_outputs(postgres_engine, runtime_ids):
    first_entry = _create_entry(
        postgres_engine,
        runtime_ids,
        payload={"last": "100", "volume": "5", "trading_status": "OPEN"},
    )
    first = _run(postgres_engine, first_entry, runtime_ids)
    first_by_family = {row.family_code: row.id for row in first.persisted}

    correction_entry = _create_entry(
        postgres_engine,
        runtime_ids,
        payload={"last": "101", "volume": "5", "trading_status": "OPEN"},
        observed_at=T0 + timedelta(minutes=1),
        ordering="002",
        supersedes=first_entry,
    )
    correction = _run(postgres_engine, correction_entry, runtime_ids)

    assert {row.family_code for row in correction.persisted} == set(first_by_family)
    assert {row.supersedes_id for row in correction.persisted} == set(first_by_family.values())
    with postgres_engine.connect() as cx:
        assert (
            cx.execute(
                text(
                    "SELECT count(*) FROM topicpilot.canonical_observations "
                    "WHERE timeline_entry_id IN (:first, :correction)"
                ),
                {"first": first_entry, "correction": correction_entry},
            ).scalar_one()
            == 6
        )


def test_runtime_fails_closed_when_reference_version_is_missing(postgres_engine, runtime_ids):
    entry_id = _create_entry(postgres_engine, runtime_ids, payload={"last": "1"})
    with (
        Session(postgres_engine) as session,
        pytest.raises(RuntimeLoadError, match="reference registry set"),
    ):
        NormalizationRuntime(session).normalize_timeline_entry(
            entry_id, _policy(), "missing-reference-version"
        )


def test_atomic_runtime_rolls_back_persistence_failure(postgres_engine, runtime_ids):
    entry_id = _create_entry(postgres_engine, runtime_ids, payload={"last": "1"})

    def broken_mapper(envelope, reference, policy):
        return NormalizationResult(
            (NormalizationCandidate("UNSUPPORTED_FAMILY", {"value": 1}, ("/value",)),)
        )

    mapping_version = "broken-mapping-v1"
    registry = _registry(runtime_ids, mapping_version, broken_mapper)
    factory = sessionmaker(bind=postgres_engine, expire_on_commit=False)
    with pytest.raises(IntegrityError):
        NormalizationRuntime(None, registry).normalize_timeline_entry_atomic(
            factory, entry_id, _policy(mapping_version), runtime_ids["version"]
        )

    with postgres_engine.connect() as cx:
        assert (
            cx.execute(
                text(
                    "SELECT count(*) FROM topicpilot.canonical_observations "
                    "WHERE timeline_entry_id=:entry"
                ),
                {"entry": entry_id},
            ).scalar_one()
            == 0
        )
