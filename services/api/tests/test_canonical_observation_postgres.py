from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import Session
from test_observation_timeline_postgres import _batch, _entry, _raw

from topicpilot_api.orm.models import CanonicalObservation, CanonicalPriceObservation
from topicpilot_api.repositories import read_current_canonical_observations

pytestmark = pytest.mark.postgres
T0 = datetime(2026, 1, 2, tzinfo=UTC)


def _canonical(
    cx,
    ids,
    *,
    observation_id=None,
    family="PRICE",
    key=None,
    quality="ACCEPTED",
    supersedes=None,
    observed=T0,
):
    oid = observation_id or uuid.uuid4()
    raw_id = uuid.uuid4()
    entry_id = uuid.uuid4()
    _raw(cx, ids, raw_id=raw_id, content_hash=f"raw-{oid}")
    _entry(
        cx,
        ids,
        entry_id=entry_id,
        raw_id=raw_id,
        content_hash=f"entry-{oid}",
        observed=observed,
        received=observed,
        retrieved=observed,
    )
    cx.execute(
        text("""
        INSERT INTO topicpilot.canonical_observations
        (id, timeline_entry_id, instrument_id, source_id, raw_observation_id,
         session_code, timezone_name, calendar_code, family_code, observed_at,
         received_at, retrieved_at, ordering_key, normalization_contract_version,
         mapping_policy_version, reference_data_version, quality_state, content_hash,
         idempotency_key, supersedes_id)
        VALUES (:id, :entry, :instrument, :source, :raw, 'REGULAR', 'UTC', 'TEST',
                :family, :observed, :observed, :observed, '001', 'v1', 'v1', 'v1',
                :quality, :content, :key, :supersedes)
    """),
        {
            "id": oid,
            "entry": entry_id,
            "instrument": ids["instrument"],
            "source": ids["source"],
            "raw": raw_id,
            "family": family,
            "observed": observed,
            "quality": quality,
            "content": f"content-{oid}",
            "key": key or f"key-{oid}",
            "supersedes": supersedes,
        },
    )
    return oid


@pytest.fixture
def canonical_ids(postgres_engine):
    ids = {name: uuid.uuid4() for name in ("market", "instrument", "source", "batch")}
    with postgres_engine.begin() as cx:
        cx.execute(
            text(
                "TRUNCATE topicpilot.canonical_observations, "
                "topicpilot.observation_timeline_batches, "
                "topicpilot.raw_market_observations, topicpilot.market_data_sources, "
                "topicpilot.instruments, topicpilot.markets RESTART IDENTITY CASCADE"
            )
        )
        cx.execute(
            text(
                "INSERT INTO topicpilot.markets (id, code, name, timezone) "
                "VALUES (:id, 'TEST', 'Test Market', 'UTC')"
            ),
            {"id": ids["market"]},
        )
        cx.execute(
            text(
                "INSERT INTO topicpilot.instruments "
                "(id, market_id, instrument_code, name, instrument_type) "
                "VALUES (:id, :market, 'TEST.EQ', 'Test Equity', 'EQUITY')"
            ),
            {"id": ids["instrument"], "market": ids["market"]},
        )
        cx.execute(
            text(
                "INSERT INTO topicpilot.market_data_sources "
                "(id, source_code, source_category, adapter_version) "
                "VALUES (:id, 'TEST_SOURCE', 'VENDOR', 'v1')"
            ),
            {"id": ids["source"]},
        )
        _batch(cx, ids)
    return ids


def test_postgres_creates_four_detail_families_and_orm_one_to_one(postgres_engine, canonical_ids):
    with postgres_engine.begin() as cx:
        oid = _canonical(cx, canonical_ids)
    with Session(postgres_engine) as session:
        row = session.get(CanonicalObservation, oid)
        row.price = CanonicalPriceObservation(price_currency_code="USD", price_scale=2, close=10)
        session.commit()
        session.refresh(row)
        assert row.price.canonical_observation_id == oid
    with postgres_engine.connect() as cx:
        names = {
            r[0]
            for r in cx.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='topicpilot' "
                    "AND table_name LIKE 'canonical%observations'"
                )
            )
        }
        assert names == {
            "canonical_observations",
            "canonical_price_observations",
            "canonical_volume_observations",
            "canonical_quote_observations",
            "canonical_trading_status_observations",
        }


def test_currency_pair_and_lineage_constraints_are_real_postgres_constraints(
    postgres_engine, canonical_ids
):
    with postgres_engine.begin() as cx:
        oid = _canonical(cx, canonical_ids)
        with pytest.raises(IntegrityError), cx.begin_nested():
            cx.execute(
                text(
                    "INSERT INTO topicpilot.canonical_price_observations "
                    "(canonical_observation_id, price_currency_code, price_scale) "
                    "VALUES (:id, 'US', 2)"
                ),
                {"id": oid},
            )
        with pytest.raises(ProgrammingError), cx.begin_nested():
            cx.execute(
                text(
                    "UPDATE topicpilot.canonical_observations "
                    "SET normalization_contract_version='' WHERE id=:id"
                ),
                {"id": oid},
            )


def test_all_canonical_tables_are_append_only_and_correction_is_append_only(
    postgres_engine, canonical_ids
):
    detail_tables = [
        "canonical_price_observations",
        "canonical_volume_observations",
        "canonical_quote_observations",
        "canonical_trading_status_observations",
    ]
    with postgres_engine.begin() as cx:
        first = _canonical(cx, canonical_ids, key="append-first")
        cx.execute(
            text(
                    "INSERT INTO topicpilot.canonical_price_observations "
                    "(canonical_observation_id, price_currency_code, price_scale) "
                    "VALUES (:id, 'USD', 2)"
            ),
            {"id": first},
        )
        with pytest.raises(ProgrammingError), cx.begin_nested():
            cx.execute(
                text(
                    "UPDATE topicpilot.canonical_observations "
                    "SET disposition='MUTATED' WHERE id=:id"
                ),
                {"id": first},
            )
        with pytest.raises(ProgrammingError), cx.begin_nested():
            cx.execute(
                text("DELETE FROM topicpilot.canonical_observations WHERE id=:id"), {"id": first}
            )
        with pytest.raises(ProgrammingError), cx.begin_nested():
            cx.execute(
                text(
                    "UPDATE topicpilot.canonical_price_observations "
                    "SET price_scale=3 WHERE canonical_observation_id=:id"
                ),
                {"id": first},
            )
        with pytest.raises(ProgrammingError), cx.begin_nested():
            cx.execute(
                text(
                    "DELETE FROM topicpilot.canonical_price_observations "
                    "WHERE canonical_observation_id=:id"
                ),
                {"id": first},
            )
        for table, columns, values in [
            ("canonical_volume_observations", "aggregation_code", "'DAILY'"),
            ("canonical_quote_observations", "quote_currency_code, price_scale", "'USD', 2"),
            (
                "canonical_trading_status_observations",
                "status_code, session_code, calendar_code, status_catalogue_version",
                "'OPEN', 'REGULAR', 'TEST', 'v1'",
            ),
        ]:
            cx.execute(
                text(
                    f"INSERT INTO topicpilot.{table} "
                    f"(canonical_observation_id, {columns}) VALUES (:id, {values})"
                ),
                {"id": first},
            )
            with pytest.raises(ProgrammingError), cx.begin_nested():
                cx.execute(
                    text(
                        f"UPDATE topicpilot.{table} "
                        f"SET {columns.split(',')[0]}={columns.split(',')[0]} "
                        "WHERE canonical_observation_id=:id"
                    ),
                    {"id": first},
                )
            with pytest.raises(ProgrammingError), cx.begin_nested():
                cx.execute(
                    text(f"DELETE FROM topicpilot.{table} WHERE canonical_observation_id=:id"),
                    {"id": first},
                )
        successor = _canonical(cx, canonical_ids, key="append-successor", supersedes=first)
        cx.execute(
            text(
                "INSERT INTO topicpilot.canonical_price_observations "
                "(canonical_observation_id, price_currency_code, price_scale) "
                "VALUES (:id, 'USD', 2)"
            ),
            {"id": successor},
        )
        assert (
            cx.execute(
                text("SELECT supersedes_id FROM topicpilot.canonical_observations WHERE id=:id"),
                {"id": successor},
            ).scalar_one()
            == first
        )
        trigger_tables = {
            r[0]
            for r in cx.execute(
                text(
                    "SELECT tgrelid::regclass::text FROM pg_trigger "
                    "WHERE tgname LIKE 'trg_canonical_%_append_only' AND NOT tgisinternal"
                )
            )
        }
        assert set([*detail_tables, "canonical_observations"]) <= trigger_tables


def test_search_path_is_not_required_for_compatibility_or_v2_reads(postgres_engine, canonical_ids):
    with postgres_engine.begin() as cx:
        _canonical(cx, canonical_ids, key="hostile-path")
        cx.execute(text("SET LOCAL search_path = pg_catalog"))
        assert cx.execute(text("SELECT count(*) FROM public.stocks")).scalar_one() >= 0
    with Session(postgres_engine) as session:
        session.execute(text("SET LOCAL search_path = pg_catalog"))
        assert read_current_canonical_observations(
            session, canonical_ids["instrument"], T0, T0 + timedelta(hours=1)
        )


def test_idempotency_self_supersession_append_only_and_family_scoped_current_reads(
    postgres_engine, canonical_ids
):
    with postgres_engine.begin() as cx:
        first = _canonical(cx, canonical_ids, key="same-key")
        with pytest.raises(IntegrityError), cx.begin_nested():
            _canonical(cx, canonical_ids, key="same-key")
        with pytest.raises(ProgrammingError), cx.begin_nested():
            cx.execute(
                text("UPDATE topicpilot.canonical_observations SET supersedes_id=id WHERE id=:id"),
                {"id": first},
            )
        successor = _canonical(cx, canonical_ids, key="successor", supersedes=first)
        _canonical(cx, canonical_ids, family="VOLUME", key="volume", supersedes=first)
        _canonical(
            cx,
            canonical_ids,
            quality="QUARANTINED",
            key="quarantined",
            observed=T0 + timedelta(minutes=1),
        )
    with Session(postgres_engine) as session:
        rows = read_current_canonical_observations(
            session, canonical_ids["instrument"], T0, T0 + timedelta(hours=1)
        )
        assert successor in {row.id for row in rows}
        assert len(rows) == 2  # accepted PRICE successor plus independent VOLUME row


def test_metadata_authority_includes_public_and_topicpilot_bases():
    from pathlib import Path

    from topicpilot_api.database import Base
    from topicpilot_api.orm.base import Base as V2Base

    source = (Path(__file__).parents[1] / "alembic" / "env.py").read_text(encoding="utf-8")
    assert "target_metadata = [Base.metadata, V2Base.metadata]" in source
    assert Base.metadata is not V2Base.metadata
    assert V2Base.metadata.schema == "topicpilot"
