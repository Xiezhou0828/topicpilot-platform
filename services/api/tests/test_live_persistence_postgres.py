from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from db_fixture_support import (
    restore_active_reference_registries,
    suspend_active_reference_registries,
)
from sqlalchemy import text
from sqlalchemy.orm import Session

from topicpilot_api.live.config import LiveRuntimeConfig
from topicpilot_api.live.contracts import IntradayBar, IntradayFetchResult
from topicpilot_api.live.persistence import LiveRepository, read_live_status, read_live_tracking

pytestmark = pytest.mark.postgres


def _seed_live_fixture(engine):
    token = uuid4().hex[:10]
    ids = {name: uuid4() for name in ("market", "instrument", "reference")}
    ids.update(
        {name: uuid4() for name in ("currency", "timezone", "session", "status", "adjustment")}
    )
    ids.update(
        {
            "market_code": f"LIVE-{token}",
            "instrument_code": f"LIVE.EQ.{token}",
            "reference_version": f"live-test-{token}",
        }
    )
    with engine.begin() as cx:
        ids["previous_active"] = suspend_active_reference_registries(cx)
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.markets
                    (id, code, name, timezone, calendar_code)
                VALUES (:id, :code, 'Live Test Market', 'Asia/Taipei', 'TW_MARKET')
                """
            ),
            {"id": ids["market"], "code": ids["market_code"]},
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.instruments
                    (id, market_id, instrument_code, name, instrument_type, currency)
                VALUES (:id, :market, :code, 'Live Test Equity', 'EQUITY', 'TWD')
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
                INSERT INTO topicpilot.reference_registry_sets
                    (id, reference_data_version, status, description)
                VALUES (:id, :version, 'ACTIVE', 'live persistence integration fixture')
                """
            ),
            {"id": ids["reference"], "version": ids["reference_version"]},
        )
        for table, columns, values, key in (
            ("reference_currencies", "code, scale", "'TWD', 2", "currency"),
            ("reference_timezones", "name", "'Asia/Taipei'", "timezone"),
            ("reference_sessions", "code, calendar_code", "'REGULAR', 'TW_MARKET'", "session"),
            ("reference_trading_statuses", "code", "'OPEN'", "status"),
            ("reference_adjustments", "code", "'UNKNOWN'", "adjustment"),
        ):
            cx.execute(
                text(
                    f"INSERT INTO topicpilot.{table} (id, registry_set_id, {columns}) "
                    f"VALUES (:id, :registry, {values})"
                ),
                {"id": ids[key], "registry": ids["reference"]},
            )
    return ids


def _cleanup_live_fixture(engine, ids):
    with engine.begin() as cx:
        cx.execute(
            text(
                """
                DELETE FROM topicpilot.live_collector_attempts
                WHERE instrument_id = :instrument
                """
            ),
            {"instrument": ids["instrument"]},
        )
        cx.execute(
            text(
                """
                DELETE FROM topicpilot.live_collector_runs
                WHERE id NOT IN (SELECT run_id FROM topicpilot.live_collector_attempts)
                  AND metadata->>'sourceId' IN (
                    SELECT id::text FROM topicpilot.market_data_sources
                    WHERE source_code = 'LIVE_TEST'
                  )
                """
            )
        )
        cx.execute(
            text("DELETE FROM topicpilot.live_tracking_universe WHERE instrument_id=:instrument"),
            {"instrument": ids["instrument"]},
        )
        for table in (
            "canonical_trading_status_observations",
            "canonical_quote_observations",
            "canonical_volume_observations",
            "canonical_price_observations",
            "canonical_observations",
        ):
            cx.execute(text(f"ALTER TABLE topicpilot.{table} DISABLE TRIGGER USER"))
        try:
            cx.execute(
                text(
                    "DELETE FROM topicpilot.canonical_observations "
                    "WHERE instrument_id = :instrument"
                ),
                {"instrument": ids["instrument"]},
            )
            cx.execute(
                text(
                    "DELETE FROM topicpilot.observation_timeline_entries "
                    "WHERE instrument_id=:instrument"
                ),
                {"instrument": ids["instrument"]},
            )
            cx.execute(
                text(
                    "DELETE FROM topicpilot.raw_market_observations "
                    "WHERE instrument_id=:instrument"
                ),
                {"instrument": ids["instrument"]},
            )
        finally:
            for table in (
                "canonical_trading_status_observations",
                "canonical_quote_observations",
                "canonical_volume_observations",
                "canonical_price_observations",
                "canonical_observations",
            ):
                cx.execute(text(f"ALTER TABLE topicpilot.{table} ENABLE TRIGGER USER"))
        cx.execute(
            text(
                "DELETE FROM topicpilot.observation_timeline_batches "
                "WHERE request_key LIKE 'live:%' AND source_id IN "
                "(SELECT id FROM topicpilot.market_data_sources WHERE source_code='LIVE_TEST')"
            )
        )
        cx.execute(text("DELETE FROM topicpilot.market_data_sources WHERE source_code='LIVE_TEST'"))
        for table, key in (
            ("reference_adjustments", "adjustment"),
            ("reference_trading_statuses", "status"),
            ("reference_sessions", "session"),
            ("reference_timezones", "timezone"),
            ("reference_currencies", "currency"),
            ("reference_registry_sets", "reference"),
            ("instruments", "instrument"),
            ("markets", "market"),
        ):
            cx.execute(text(f"DELETE FROM topicpilot.{table} WHERE id=:id"), {"id": ids[key]})
        restore_active_reference_registries(cx, ids["previous_active"])


def test_live_repository_persists_intraday_raw_timeline_canonical_and_read_status(
    postgres_engine,
):
    ids = _seed_live_fixture(postgres_engine)
    try:
        config = LiveRuntimeConfig(
            reference_data_version=ids["reference_version"],
            provider_code="LIVE_TEST",
            mapping_policy_version="live-intraday-mapping-v1",
        )
        observed_at = datetime(2026, 8, 7, 5, 20, tzinfo=UTC)
        result = IntradayFetchResult(
            ids["instrument_code"],
            ids["market_code"],
            f"{ids['instrument_code']}@{ids['market_code']}",
            "LIVE_TEST",
            "live-test.v1",
            datetime(2026, 8, 7, 5, 22, tzinfo=UTC),
            (
                IntradayBar(
                    ids["instrument_code"],
                    ids["market_code"],
                    observed_at,
                    Decimal("100"),
                    Decimal("103"),
                    Decimal("99"),
                    Decimal("102"),
                    Decimal("1200"),
                    "5m",
                    {"close": "102", "volume": "1200", "interval": "5m"},
                ),
            ),
        )
        with Session(postgres_engine, expire_on_commit=False) as session:
            repository = LiveRepository(session, config)
            run_id, batch_id = repository.start_run(
                run_type="INTRADAY",
                provider_code="LIVE_TEST",
                adapter_version="live-test.v1",
                requested_count=1,
                now=result.retrieved_at,
            )
            families = repository.persist_bar(
                run_id=run_id,
                batch_id=batch_id,
                result=result,
                bar=result.latest,
                retrieved_at=result.retrieved_at,
            )
            repository.persist_bar(
                run_id=run_id,
                batch_id=batch_id,
                result=result,
                bar=result.latest,
                retrieved_at=result.retrieved_at,
            )
            repository.finish_run(
                run_id,
                status="SUCCESS",
                success_count=1,
                failure_count=0,
                retry_count=0,
                latency_ms=100,
                freshness_state="FRESH",
                provider_status="AVAILABLE",
                now=result.retrieved_at,
            )
            assert families == ("PRICE", "VOLUME")
            assert read_live_status(session)["status"] == "SUCCESS"

            refreshed = repository.refresh_tracking_universe(now=result.retrieved_at)
            items, total = read_live_tracking(session, 10, 0)
            assert refreshed >= 1
            assert total >= 1
            tracked = next(
                item for item in items if item["instrumentCode"] == ids["instrument_code"]
            )
            assert tracked["updateMode"] == "UNKNOWN"
            assert tracked["observationCount"] == 0

        with postgres_engine.connect() as cx:
            assert (
                cx.execute(
                    text(
                        "SELECT count(*) FROM topicpilot.raw_market_observations "
                        "WHERE instrument_id=:id"
                    ),
                    {"id": ids["instrument"]},
                ).scalar_one()
                == 1
            )
            assert (
                cx.execute(
                    text(
                        "SELECT count(*) FROM topicpilot.observation_timeline_entries "
                        "WHERE instrument_id=:id"
                    ),
                    {"id": ids["instrument"]},
                ).scalar_one()
                == 1
            )
            assert (
                cx.execute(
                    text(
                        "SELECT count(*) FROM topicpilot.canonical_observations "
                        "WHERE instrument_id=:id"
                    ),
                    {"id": ids["instrument"]},
                ).scalar_one()
                == 2
            )
    finally:
        _cleanup_live_fixture(postgres_engine, ids)
