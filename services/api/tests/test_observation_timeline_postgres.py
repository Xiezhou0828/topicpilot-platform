from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command

# SQL statements are intentionally kept close to the assertion they exercise.
# ruff: noqa: E501
pytestmark = pytest.mark.postgres

ROOT = Path(__file__).resolve().parents[1]
T0 = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)


@pytest.fixture
def timeline_ids(postgres_engine):
    ids = {name: uuid.uuid4() for name in ("market", "instrument", "source", "batch", "raw", "entry")}
    with postgres_engine.begin() as cx:
        cx.execute(text("TRUNCATE topicpilot.observation_timeline_quality_events, topicpilot.observation_timeline_entries, topicpilot.observation_timeline_batches, topicpilot.raw_market_observations, topicpilot.market_data_sources, topicpilot.instruments, topicpilot.markets RESTART IDENTITY CASCADE"))
        cx.execute(text("INSERT INTO topicpilot.markets (id, code, name, timezone) VALUES (:id, 'TEST', 'Test Market', 'UTC')"), {"id": ids["market"]})
        cx.execute(text("INSERT INTO topicpilot.instruments (id, market_id, instrument_code, name, instrument_type) VALUES (:id, :market, 'TEST.EQ', 'Test Equity', 'EQUITY')"), {"id": ids["instrument"], "market": ids["market"]})
        cx.execute(text("INSERT INTO topicpilot.market_data_sources (id, source_code, source_category, adapter_version) VALUES (:id, 'TEST_SOURCE', 'VENDOR', 'v1')"), {"id": ids["source"]})
    return ids


def _batch(cx, ids, **overrides):
    values = {"id": ids["batch"], "source": ids["source"], "instrument": ids["instrument"], "from_": T0, "to_": T0, "status": "OPEN", "coverage": "UNKNOWN", "completed": None}
    values.update(overrides)
    cx.execute(text("INSERT INTO topicpilot.observation_timeline_batches (id, source_id, requested_instrument_id, requested_from, requested_to, status, coverage_status, completed_at) VALUES (:id, :source, :instrument, :from_, :to_, :status, :coverage, :completed)"), values)


def _raw(cx, ids, *, raw_id=None, instrument=None, content_hash="raw-hash"):
    cx.execute(text("INSERT INTO topicpilot.raw_market_observations (id, source_id, instrument_id, source_instrument_identifier, observed_at, payload, content_hash) VALUES (:id, :source, :instrument, 'TEST.EQ', :observed, '{}'::jsonb, :hash)"), {"id": raw_id or ids["raw"], "source": ids["source"], "instrument": instrument if instrument is not None else ids["instrument"], "observed": T0, "hash": content_hash})


def _entry(cx, ids, *, entry_id=None, raw_id=None, content_hash="entry-hash", **overrides):
    values = {"id": entry_id or ids["entry"], "instrument": ids["instrument"], "source": ids["source"], "raw": raw_id or ids["raw"], "batch": ids["batch"], "observed": T0, "received": T0, "retrieved": T0, "ordering": "001", "hash": content_hash, "status": "ACTIVE", "supersedes": None}
    values.update(overrides)
    cx.execute(text("INSERT INTO topicpilot.observation_timeline_entries (id, instrument_id, source_id, raw_observation_id, batch_id, observed_at, received_at, retrieved_at, ordering_key, payload, content_hash, entry_status, supersedes_id) VALUES (:id, :instrument, :source, :raw, :batch, :observed, :received, :retrieved, :ordering, '{}'::jsonb, :hash, :status, :supersedes)"), values)


def _reject(engine, statement, params):
    with pytest.raises(IntegrityError), engine.begin() as cx:
        cx.execute(text(statement), params)


def test_upgrade_downgrade_reupgrade(postgres_engine):
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL", ""))
    command.downgrade(cfg, "0017_phase3_4_005_market_data_source_and_raw_observations")
    with postgres_engine.connect() as cx:
        assert cx.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0017_phase3_4_005_market_data_source_and_raw_observations"
    command.upgrade(cfg, "0018_phase3_4_006_observation_timeline")
    with postgres_engine.connect() as cx:
        assert cx.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0018_phase3_4_006_observation_timeline"
    command.upgrade(cfg, "head")
    with postgres_engine.connect() as cx:
        assert cx.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0022_task_live_002_runtime"
        triggers = {r[0] for r in cx.execute(text("SELECT tgname FROM pg_trigger WHERE tgname LIKE 'trg_canonical_%_append_only' AND NOT tgisinternal"))}
        assert triggers == {f"trg_canonical_{table}_append_only" for table in ["observations", "price_observations", "volume_observations", "quote_observations", "trading_status_observations"]}


def test_objects_and_constraints_exist(postgres_engine):
    with postgres_engine.connect() as cx:
        tables = {r[0] for r in cx.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='topicpilot' AND table_name LIKE 'observation_timeline%'")).all()}
        assert tables == {"observation_timeline_batches", "observation_timeline_entries", "observation_timeline_quality_events"}
        indexes = {r[0] for r in cx.execute(text("SELECT indexname FROM pg_indexes WHERE schemaname='topicpilot' AND indexname LIKE 'ix_timeline%'")).all()}
        assert {"ix_timeline_entries_replay", "ix_timeline_entries_source_time", "ix_timeline_entries_batch_time", "ix_timeline_quality_entry_time", "ix_timeline_quality_batch_time"} <= indexes


def test_batch_constraints(postgres_engine, timeline_ids):
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_batches (id, source_id, requested_from) VALUES (:id, :source, :from_)", {"id": uuid.uuid4(), "source": timeline_ids["source"], "from_": T0})
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_batches (id, source_id, requested_from, requested_to) VALUES (:id, :source, :from_, :to_)", {"id": uuid.uuid4(), "source": timeline_ids["source"], "from_": T0, "to_": datetime(2026, 1, 1, tzinfo=UTC)})
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_batches (id, source_id, status, completed_at) VALUES (:id, :source, 'BOGUS', :completed)", {"id": uuid.uuid4(), "source": timeline_ids["source"], "completed": T0})
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_batches (id, source_id, coverage_status) VALUES (:id, :source, 'BOGUS')", {"id": uuid.uuid4(), "source": timeline_ids["source"]})
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_batches (id, source_id, status) VALUES (:id, :source, 'FAILED')", {"id": uuid.uuid4(), "source": timeline_ids["source"]})


def test_timeline_lineage_dedup_supersession_and_quality(postgres_engine, timeline_ids):
    with postgres_engine.begin() as cx:
        _batch(cx, timeline_ids)
        _raw(cx, timeline_ids)
        _entry(cx, timeline_ids)
        cx.execute(text("INSERT INTO topicpilot.observation_timeline_quality_events (id, entry_id, event_code, severity) VALUES (:id, :entry, 'LATE', 'WARNING')"), {"id": uuid.uuid4(), "entry": timeline_ids["entry"]})
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_quality_events (id, entry_id, event_code, severity) VALUES (:id, :entry, 'X', 'BOGUS')", {"id": uuid.uuid4(), "entry": timeline_ids["entry"]})
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_quality_events (id, event_code, severity) VALUES (:id, 'X', 'INFO')", {"id": uuid.uuid4()})
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_entries (id, instrument_id, source_id, raw_observation_id, batch_id, observed_at, received_at, retrieved_at, ordering_key, payload, content_hash, entry_status) SELECT :id, instrument_id, source_id, raw_observation_id, batch_id, observed_at, received_at, retrieved_at, '004', payload, 'invalid-status', 'BOGUS' FROM topicpilot.observation_timeline_entries WHERE id=:entry", {"id": uuid.uuid4(), "entry": timeline_ids["entry"]})


def test_duplicate_raw_observation_rejected(postgres_engine, timeline_ids):
    with postgres_engine.begin() as cx:
        _batch(cx, timeline_ids); _raw(cx, timeline_ids); _entry(cx, timeline_ids)
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_entries (id, instrument_id, source_id, raw_observation_id, batch_id, observed_at, received_at, retrieved_at, ordering_key, payload, content_hash) SELECT :id, instrument_id, source_id, raw_observation_id, batch_id, observed_at, received_at, retrieved_at, '002', payload, 'different-hash' FROM topicpilot.observation_timeline_entries WHERE id=:entry", {"id": uuid.uuid4(), "entry": timeline_ids["entry"]})


def test_business_dedup_rejected(postgres_engine, timeline_ids):
    with postgres_engine.begin() as cx:
        _batch(cx, timeline_ids); _raw(cx, timeline_ids); _entry(cx, timeline_ids)
        duplicate_raw = uuid.uuid4(); _raw(cx, timeline_ids, raw_id=duplicate_raw, content_hash="different-raw")
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_entries (id, instrument_id, source_id, raw_observation_id, batch_id, observed_at, received_at, retrieved_at, ordering_key, payload, content_hash) SELECT :id, instrument_id, source_id, :raw, batch_id, observed_at, received_at, retrieved_at, '002', payload, content_hash FROM topicpilot.observation_timeline_entries WHERE id=:entry", {"id": uuid.uuid4(), "entry": timeline_ids["entry"], "raw": duplicate_raw})


def test_self_supersession_rejected_by_check(postgres_engine, timeline_ids):
    with postgres_engine.begin() as cx:
        _batch(cx, timeline_ids); _raw(cx, timeline_ids)
        raw_id = uuid.uuid4(); entry_id = uuid.uuid4()
        _raw(cx, timeline_ids, raw_id=raw_id, content_hash="self-raw")
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_entries (id, instrument_id, source_id, raw_observation_id, batch_id, observed_at, received_at, retrieved_at, ordering_key, payload, content_hash, supersedes_id) VALUES (:id, :instrument, :source, :raw, :batch, :observed, :observed, :observed, '002', '{}'::jsonb, 'self-entry', :id)", {"id": entry_id, "instrument": timeline_ids["instrument"], "source": timeline_ids["source"], "raw": raw_id, "batch": timeline_ids["batch"], "observed": datetime(2026, 1, 2, 0, 1, tzinfo=UTC)})


def test_valid_correction_and_unresolved_lineage_rejected(postgres_engine, timeline_ids):
    with postgres_engine.begin() as cx:
        _batch(cx, timeline_ids)
        _raw(cx, timeline_ids)
        _entry(cx, timeline_ids)
        correction_raw = uuid.uuid4()
        correction_entry = uuid.uuid4()
        _raw(cx, timeline_ids, raw_id=correction_raw, content_hash="raw-correction")
        _entry(cx, timeline_ids, entry_id=correction_entry, raw_id=correction_raw, content_hash="entry-correction", supersedes=timeline_ids["entry"], ordering="002")
        row = cx.execute(text("SELECT supersedes_id FROM topicpilot.observation_timeline_entries WHERE id=:id"), {"id": correction_entry}).scalar_one()
        assert row == timeline_ids["entry"]
        assert cx.execute(text("SELECT entry_status FROM topicpilot.observation_timeline_entries WHERE id=:id"), {"id": timeline_ids["entry"]}).scalar_one() == "ACTIVE"
    unresolved_raw = uuid.uuid4()
    with pytest.raises(IntegrityError), postgres_engine.begin() as cx:
        cx.execute(text("INSERT INTO topicpilot.raw_market_observations (id, source_id, instrument_id, source_instrument_identifier, observed_at, payload, content_hash) VALUES (:id, :source, NULL, 'UNRESOLVED', :observed, '{}'::jsonb, 'unresolved')"), {"id": unresolved_raw, "source": timeline_ids["source"], "observed": T0})
        _entry(cx, timeline_ids, raw_id=unresolved_raw)


def test_raw_lineage_mismatch_rejected(postgres_engine, timeline_ids):
    other_instrument = uuid.uuid4()
    other_raw = uuid.uuid4()
    with postgres_engine.begin() as cx:
        _batch(cx, timeline_ids)
        cx.execute(text("INSERT INTO topicpilot.instruments (id, market_id, instrument_code, name, instrument_type) VALUES (:id, :market, 'OTHER.EQ', 'Other Equity', 'EQUITY')"), {"id": other_instrument, "market": timeline_ids["market"]})
        _raw(cx, timeline_ids, raw_id=other_raw, instrument=other_instrument, content_hash="other-raw")
    _reject(postgres_engine, "INSERT INTO topicpilot.observation_timeline_entries (id, instrument_id, source_id, raw_observation_id, batch_id, observed_at, received_at, retrieved_at, ordering_key, payload, content_hash) VALUES (:id, :instrument, :source, :raw, :batch, :observed, :observed, :observed, '001', '{}'::jsonb, 'mismatch')", {"id": uuid.uuid4(), "instrument": timeline_ids["instrument"], "source": timeline_ids["source"], "raw": other_raw, "batch": timeline_ids["batch"], "observed": T0})


def test_replay_query_semantics(postgres_engine, timeline_ids):
    from topicpilot_api.repositories import replay_observation_timeline

    with postgres_engine.begin() as cx:
        _batch(cx, timeline_ids)
        tie_break_ids = (uuid.UUID("00000000-0000-0000-0000-000000000002"), uuid.UUID("00000000-0000-0000-0000-000000000001"))
        cases = (
            (T0, "002", "ACTIVE", uuid.uuid4()),
            (T0, "001", "ACTIVE", uuid.uuid4()),
            (T0, "001", "ACTIVE", tie_break_ids[0]),
            (T0, "001", "ACTIVE", tie_break_ids[1]),
            (T0.replace(minute=1), "001", "QUARANTINED", uuid.uuid4()),
            (T0.replace(minute=2), "001", "SUPERSEDED", uuid.uuid4()),
            (T0.replace(minute=3), "001", "ACTIVE", uuid.uuid4()),
        )
        for n, (observed, ordering, status, entry_id) in enumerate(cases):
            raw_id = uuid.uuid4(); _raw(cx, timeline_ids, raw_id=raw_id, content_hash=f"raw-{n}")
            _entry(cx, timeline_ids, entry_id=entry_id, raw_id=raw_id, content_hash=f"entry-{n}", observed=observed, received=observed, retrieved=observed, ordering=ordering, status=status)
    with Session(postgres_engine) as session:
        rows = replay_observation_timeline(session, timeline_ids["instrument"], T0, T0.replace(minute=3))
        assert [(r.observed_at, r.ordering_key, r.id) for r in rows] == [
            (T0, "001", tie_break_ids[1]),
            (T0, "001", tie_break_ids[0]),
            (T0, "001", rows[2].id),
            (T0, "002", rows[3].id),
        ]
        assert {r.entry_status for r in rows} == {"ACTIVE"}
        assert len(replay_observation_timeline(session, timeline_ids["instrument"], T0, T0.replace(minute=4), include_non_active=True)) == 7
        assert replay_observation_timeline(session, uuid.uuid4(), T0, T0.replace(minute=4)) == []
