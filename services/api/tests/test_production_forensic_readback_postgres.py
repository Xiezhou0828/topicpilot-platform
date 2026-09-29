from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import DBAPIError

from topicpilot_api.production_forensic_readback import read_post_close_run


def _disposable_database_url() -> URL:
    raw = os.getenv("TEST_DATABASE_URL")
    if not raw:
        pytest.skip("disposable PostgreSQL requires TEST_DATABASE_URL")
    url = make_url(raw)
    if url.host not in {"localhost", "127.0.0.1", "::1", "postgres"}:
        pytest.skip("forensic privilege test refuses non-disposable database hosts")
    return url


@pytest.fixture()
def forensic_fixture() -> Iterator[tuple[str, str, str]]:
    admin_url = _disposable_database_url()
    admin_engine = create_engine(admin_url, pool_pre_ping=True)
    role = f"tp_forensic_{uuid4().hex[:12]}"
    password = uuid4().hex
    run_id = uuid4()
    role_ident = f'"{role}"'
    role_engine = None
    try:
        with admin_engine.begin() as connection:
            connection.exec_driver_sql(f"CREATE ROLE {role_ident} LOGIN PASSWORD '{password}'")
            connection.exec_driver_sql(f"GRANT USAGE ON SCHEMA topicpilot TO {role_ident}")
            for table in (
                "live_collector_runs",
                "live_collector_attempts",
                "live_collector_checkpoints",
            ):
                connection.exec_driver_sql(
                    f"GRANT SELECT ON TABLE topicpilot.{table} TO {role_ident}"
                )
            now = datetime(2026, 9, 29, 5, 40, tzinfo=UTC)
            connection.execute(
                text(
                    """
                    INSERT INTO topicpilot.live_collector_runs
                    (id, run_type, status, provider_code, adapter_version, config_hash,
                     started_at, heartbeat_at, completed_at, requested_count,
                     success_count, failure_count, retry_count, latency_ms,
                     freshness_state, provider_status, failure_code, failure_message)
                    VALUES
                    (:id, 'POST_CLOSE', 'FAILED', 'TWSE_OFFICIAL_DAILY',
                     'twse-official-daily.v2', 'fixture', :started_at, :heartbeat_at,
                     :completed_at, 2, 1, 1, 0, 1200, 'PARTIAL', 'ERROR',
                     'EXCHANGE_NO_DATA', 'fixture failure')
                    """
                ),
                {
                    "id": run_id,
                    "started_at": now,
                    "heartbeat_at": now,
                    "completed_at": now,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO topicpilot.live_collector_attempts
                    (id, run_id, instrument_code, market_code, attempt_number, status,
                     started_at, retrieved_at, updated_at, latency_ms, retry_count,
                     provider_status, freshness_state, error_code, error_message)
                    VALUES
                    (:id, :run_id, '2330', 'TPE', 1, 'FAILED', :started_at,
                     :retrieved_at, :updated_at, 500, 0, 'ERROR', 'PARTIAL',
                     'EXCHANGE_NO_DATA', 'fixture failure')
                    """
                ),
                {
                    "id": uuid4(),
                    "run_id": run_id,
                    "started_at": now,
                    "retrieved_at": now,
                    "updated_at": now,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO topicpilot.live_collector_checkpoints
                    (id, run_id, batch_number, batch_key, attempt_number, status,
                     processed_count, succeeded_count, failed_count, skipped_count,
                     retry_count, provider_request_count, provider_failure_count,
                     checkpoint_hash, metadata, created_at)
                    VALUES
                    (:id, :run_id, 100, 'FORMAL_MARKET_FACTS:TPE:1', 1, 'FAILED',
                     1, 0, 1, 0, 0, 1, 1, 'fixture-hash',
                     '{"market":"TPE","reason":"fixture"}'::jsonb, :created_at)
                    """
                ),
                {"id": uuid4(), "run_id": run_id, "created_at": now},
            )
        role_url = admin_url.set(username=role, password=password).render_as_string(
            hide_password=False
        )
        role_engine = create_engine(role_url, pool_pre_ping=True)
        yield role_url, role, str(run_id)
    finally:
        if role_engine is not None:
            role_engine.dispose()
        with admin_engine.begin() as connection:
            connection.exec_driver_sql(f"DROP OWNED BY {role_ident}")
            connection.exec_driver_sql(f"DROP ROLE IF EXISTS {role_ident}")
        admin_engine.dispose()


@pytest.mark.postgres
def test_disposable_readonly_role_can_read_and_cannot_mutate(forensic_fixture) -> None:
    role_url, role, run_id = forensic_fixture
    payload = read_post_close_run(
        database_url=role_url,
        run_id=run_id,
        expected_role=role,
        forensic_tool_sha="a" * 40,
    )
    assert payload["databaseRole"] == role
    assert payload["transactionReadOnly"] is True
    assert payload["mutationPrivilegesPresent"] == "NO"
    assert payload["run"]["status"] == "FAILED"
    assert payload["marketSummary"] == [
        {
            "marketCode": "TPE",
            "attemptCount": 1,
            "successCount": 0,
            "failureCount": 1,
            "skippedCount": 0,
            "timeoutCount": 0,
            "instrumentCount": 1,
            "firstStartedAt": "2026-09-29T05:40:00+00:00",
            "lastRetrievedAt": "2026-09-29T05:40:00+00:00",
        }
    ]
    assert payload["firstFailedCheckpoint"]["batchKey"] == "FORMAL_MARKET_FACTS:TPE:1"

    engine = create_engine(role_url, pool_pre_ping=True)
    try:
        for statement in (
            "INSERT INTO topicpilot.live_collector_runs (id) VALUES (:id)",
            "UPDATE topicpilot.live_collector_runs SET status = 'FAILED' WHERE false",
            "DELETE FROM topicpilot.live_collector_runs WHERE false",
        ):
            with engine.connect() as connection:
                transaction = connection.begin()
                try:
                    with pytest.raises(DBAPIError):
                        connection.execute(text(statement), {"id": uuid4()})
                finally:
                    transaction.rollback()
    finally:
        engine.dispose()
