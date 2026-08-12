from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEMO_BUNDLE = REPOSITORY_ROOT / "fixtures" / "demo"
SCHEMA_PATH = REPOSITORY_ROOT / "fixtures" / "schema" / "enterprise_bundle.v1.schema.json"


@pytest.fixture(scope="session")
def postgres_engine() -> Generator[Engine, None, None]:
    database_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("PostgreSQL integration tests require TEST_DATABASE_URL or DATABASE_URL")

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        engine.dispose()
        pytest.skip(f"PostgreSQL integration database is unavailable: {exc}")

    yield engine
    engine.dispose()


@pytest.fixture
def clean_database(postgres_engine: Engine) -> Engine:
    with postgres_engine.begin() as connection:
        connection.execute(
            text(
                """
                TRUNCATE TABLE
                    news_topic_relations,
                    news_stock_relations,
                    news_articles,
                    data_quality_events,
                    strategy_performance,
                    strategy_candidates,
                    strategy_runs,
                    topic_snapshots,
                    stock_snapshots,
                    market_snapshots,
                    source_artifacts,
                    stock_topic_relations,
                    topic_hierarchy,
                    ingestion_runs,
                    topics,
                    stocks
                RESTART IDENTITY CASCADE
                """
            )
        )
    return postgres_engine


@pytest.fixture
def db_session(postgres_engine: Engine) -> Generator[Session, None, None]:
    with postgres_engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(connection, expire_on_commit=False) as session:
                yield session
        finally:
            transaction.rollback()
