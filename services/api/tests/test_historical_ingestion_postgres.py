from __future__ import annotations

import os
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from topicpilot_api.config import Settings
from topicpilot_api.database import get_db
from topicpilot_api.main import create_app
from topicpilot_api.market_data import (
    HistoricalFetchResult,
    HistoricalIngestionError,
    ingest_historical,
)
from topicpilot_api.market_data.history import HistoricalBar
from topicpilot_api.normalizer import MappingPolicy


@pytest.fixture(scope="module")
def ingestion_engine():
    url = os.getenv("TOPICPILOT_INGEST_TEST_DATABASE_URL")
    if not url:
        pytest.skip("historical ingestion integration requires TOPICPILOT_INGEST_TEST_DATABASE_URL")
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        engine.dispose()
        pytest.skip(f"historical ingestion database is unavailable: {exc}")
    yield engine
    engine.dispose()


@pytest.fixture
def seeded_database(ingestion_engine):
    ids = {name: uuid.uuid4() for name in ("market", "instrument", "reference")}
    with ingestion_engine.begin() as cx:
        cx.execute(
            text(
                """
                TRUNCATE TABLE
                    topicpilot.canonical_trading_status_observations,
                    topicpilot.canonical_quote_observations,
                    topicpilot.canonical_volume_observations,
                    topicpilot.canonical_price_observations,
                    topicpilot.canonical_observations,
                    topicpilot.observation_timeline_quality_events,
                    topicpilot.observation_timeline_entries,
                    topicpilot.observation_timeline_batches,
                    topicpilot.raw_market_observations,
                    topicpilot.market_data_sources,
                    topicpilot.reference_adjustments,
                    topicpilot.reference_trading_statuses,
                    topicpilot.reference_sessions,
                    topicpilot.reference_timezones,
                    topicpilot.reference_currencies,
                    topicpilot.reference_registry_sets,
                    topicpilot.instruments,
                    topicpilot.markets
                RESTART IDENTITY CASCADE
                """
            )
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.markets
                    (id, code, name, timezone, calendar_code)
                VALUES (:id, 'TPE', 'Test Taiwan Market', 'Asia/Taipei', 'TW_MARKET')
                """
            ),
            {"id": ids["market"]},
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.instruments
                    (id, market_id, instrument_code, name, instrument_type, currency)
                VALUES (:id, :market, '2330', 'Test Taiwan Equity', 'EQUITY', 'TWD')
                """
            ),
            {"id": ids["instrument"], "market": ids["market"]},
        )
        cx.execute(
            text(
                """
                INSERT INTO topicpilot.reference_registry_sets
                    (id, reference_data_version, status, description)
                VALUES (:id, 'tw-reference-v1', 'ACTIVE',
                        'historical ingestion integration fixture')
                """
            ),
            {"id": ids["reference"]},
        )
        for table, columns, values in (
            ("reference_currencies", "code, scale", "'TWD', 2"),
            ("reference_timezones", "name", "'Asia/Taipei'"),
            ("reference_sessions", "code, calendar_code", "'REGULAR', 'TW_MARKET'"),
            ("reference_trading_statuses", "code", "'OPEN'"),
            ("reference_adjustments", "code", "'UNKNOWN'"),
        ):
            cx.execute(
                text(
                    f"INSERT INTO topicpilot.{table} (id, registry_set_id, {columns}) "
                    f"VALUES (:id, :registry, {values})"
                ),
                {"id": uuid.uuid4(), "registry": ids["reference"]},
            )
    return ingestion_engine


class StubHistoricalProvider:
    source_code = "TAISHIN_TECH_ANALYSIS"
    adapter_version = "taishin-tech-analysis.v1"

    def __init__(self, *, missing_close: bool = False):
        self.calls = 0
        self.missing_close = missing_close

    def fetch_daily(self, instrument_code: str, market_code: str) -> HistoricalFetchResult:
        self.calls += 1
        assert (instrument_code, market_code) == ("2330", "TPE")
        retrieved = datetime(2026, 8, 10, 9, tzinfo=UTC)
        bars = (
            HistoricalBar(
                date(2026, 8, 6),
                Decimal("100"),
                Decimal("103"),
                Decimal("99"),
                None if self.missing_close else Decimal("102"),
                Decimal("1000"),
            ),
            HistoricalBar(
                date(2026, 8, 7),
                Decimal("102"),
                Decimal("104"),
                Decimal("101"),
                None if self.missing_close else Decimal("103"),
                Decimal("1100"),
            ),
        )
        return HistoricalFetchResult(
            "2330",
            "TPE",
            "2330@TPE",
            self.source_code,
            self.adapter_version,
            retrieved,
            bars,
            len(bars),
        )


def _ingest(engine, provider):
    with Session(engine, expire_on_commit=False) as session, session.begin():
        return ingest_historical(
            session,
            provider,
            [("2330", "TPE")],
            reference_data_version="tw-reference-v1",
            requested_from=date(2026, 8, 1),
            requested_to=date(2026, 8, 10),
            policy=MappingPolicy(mapping_policy_version="historical-daily-mapping-v1"),
        )


def test_historical_ingestion_persists_timeline_canonical_and_is_idempotent(seeded_database):
    provider = StubHistoricalProvider()
    first = _ingest(seeded_database, provider)
    second = _ingest(seeded_database, provider)

    assert first.provider_point_count == 2
    assert first.raw_created == 2
    assert first.timeline_created == 2
    assert first.canonical_created == 4
    assert second.is_noop
    assert second.raw_reused == 2
    assert second.timeline_reused == 2
    assert second.canonical_reused == 4
    assert provider.calls == 2

    with seeded_database.connect() as cx:
        assert (
            cx.execute(text("SELECT count(*) FROM topicpilot.raw_market_observations")).scalar_one()
            == 2
        )
        assert (
            cx.execute(
                text("SELECT count(*) FROM topicpilot.observation_timeline_entries")
            ).scalar_one()
            == 2
        )
        assert (
            cx.execute(text("SELECT count(*) FROM topicpilot.canonical_observations")).scalar_one()
            == 4
        )
        assert (
            cx.execute(
                text(
                    "SELECT count(*) FROM topicpilot.canonical_observations "
                    "WHERE quality_state='ACCEPTED'"
                )
            ).scalar_one()
            == 4
        )
        assert cx.execute(
            text("SELECT close FROM topicpilot.canonical_price_observations ORDER BY close")
        ).all() == [
            (Decimal("102.000000000000000000"),),
            (Decimal("103.000000000000000000"),),
        ]

    app = create_app(Settings(database_url=str(seeded_database.url)))
    factory = sessionmaker(bind=seeded_database, expire_on_commit=False)

    def get_test_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as client:
        response = client.get("/api/v1/stocks/2330/price-history?from=2026-08-06&to=2026-08-07")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "AVAILABLE"
    assert body["pointCount"] == 2
    assert [row["close"] for row in body["items"]] == [102.0, 103.0]


def test_historical_ingestion_persists_incomplete_price_without_zero(seeded_database):
    result = _ingest(seeded_database, StubHistoricalProvider(missing_close=True))
    assert result.incomplete_canonical_count == 2
    with seeded_database.connect() as cx:
        row = cx.execute(
            text(
                "SELECT quality_state, close FROM topicpilot.canonical_observations co "
                "JOIN topicpilot.canonical_price_observations cp "
                "ON cp.canonical_observation_id=co.id "
                "ORDER BY co.observed_at LIMIT 1"
            )
        ).one()
    assert row[0] == "INCOMPLETE"
    assert row[1] is None


def test_historical_ingestion_rolls_back_when_reference_is_missing(seeded_database):
    provider = StubHistoricalProvider()
    with (
        Session(seeded_database, expire_on_commit=False) as session,
        pytest.raises(HistoricalIngestionError, match="reference data"),
        session.begin(),
    ):
        ingest_historical(
            session,
            provider,
            [("2330", "TPE")],
            reference_data_version="missing-reference",
            requested_from=date(2026, 8, 1),
            requested_to=date(2026, 8, 10),
            policy=MappingPolicy(mapping_policy_version="historical-daily-mapping-v1"),
        )
    with seeded_database.connect() as cx:
        assert (
            cx.execute(text("SELECT count(*) FROM topicpilot.market_data_sources")).scalar_one()
            == 0
        )
        assert (
            cx.execute(text("SELECT count(*) FROM topicpilot.raw_market_observations")).scalar_one()
            == 0
        )
        assert (
            cx.execute(
                text("SELECT count(*) FROM topicpilot.observation_timeline_entries")
            ).scalar_one()
            == 0
        )
