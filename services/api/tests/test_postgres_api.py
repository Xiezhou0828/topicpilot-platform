from __future__ import annotations

import copy

import pytest
from conftest import DEMO_BUNDLE, SCHEMA_PATH
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from topicpilot_api.bundle import load_bundle
from topicpilot_api.config import Settings
from topicpilot_api.database import get_db
from topicpilot_api.importer import ImportConflictError, import_bundle
from topicpilot_api.main import create_app
from topicpilot_api.models import IngestionRun

pytestmark = pytest.mark.postgres


def imported_engine(clean_database: Engine) -> Engine:
    bundle = load_bundle(DEMO_BUNDLE, SCHEMA_PATH)
    with Session(clean_database) as session:
        result = import_bundle(session, bundle)
    assert result.status == "IMPORTED"
    return clean_database


def test_import_is_atomic_idempotent_and_queryable(clean_database: Engine) -> None:
    bundle = load_bundle(DEMO_BUNDLE, SCHEMA_PATH)
    with Session(clean_database) as session:
        first = import_bundle(session, bundle)
        second = import_bundle(session, bundle)

        assert first.status == "IMPORTED"
        assert second.status == "NO_OP"
        assert first.ingestion_run_id == second.ingestion_run_id
        assert session.scalar(select(func.count()).select_from(IngestionRun)) == 1

        quality = session.execute(text("SELECT * FROM vw_data_quality_daily")).mappings().one()
        assert quality["artifact_count"] == 8
        assert quality["warning_count"] == 1

        rotation = session.execute(
            text("SELECT * FROM vw_topic_rotation_14d ORDER BY topic_slug")
        ).mappings()
        assert len(list(rotation)) == 3


def test_same_version_with_different_hash_is_rejected(clean_database: Engine) -> None:
    bundle = load_bundle(DEMO_BUNDLE, SCHEMA_PATH)
    with Session(clean_database) as session:
        import_bundle(session, bundle)

    conflicting = copy.deepcopy(bundle)
    conflicting.data["stocks"][0]["name"] = "Changed after validation"
    object.__setattr__(conflicting, "bundle_hash", "f" * 64)

    with (
        Session(clean_database) as session,
        pytest.raises(ImportConflictError, match="different SHA-256"),
    ):
        import_bundle(session, conflicting)


def test_failed_import_rolls_back_every_table(clean_database: Engine) -> None:
    bundle = copy.deepcopy(load_bundle(DEMO_BUNDLE, SCHEMA_PATH))
    duplicate = copy.deepcopy(bundle.data["strategyCandidates"]["candidates"][0])
    bundle.data["strategyCandidates"]["candidates"].append(duplicate)

    with Session(clean_database) as session, pytest.raises(IntegrityError):
        import_bundle(session, bundle)

    with Session(clean_database) as session:
        assert session.scalar(select(func.count()).select_from(IngestionRun)) == 0
        assert session.scalar(text("SELECT count(*) FROM stocks")) == 0


def test_read_api_contract_pagination_nulls_and_problem_json(clean_database: Engine) -> None:
    engine = imported_engine(clean_database)
    settings = Settings(
        DATABASE_URL=str(engine.url),
        cors_origins=("https://demo.example",),
        freshness_days=30,
    )
    app = create_app(settings)

    def override_db():
        with Session(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.get("/readyz").json() == {"status": "ready"}

        status = client.get("/api/v1/meta/data-status")
        assert status.status_code == 200
        assert status.json()["classification"] == "PUBLIC_SYNTHETIC"

        stocks = client.get("/api/v1/stocks", params={"limit": 2, "offset": 1})
        assert stocks.status_code == 200
        assert stocks.json()["total"] == 4
        assert len(stocks.json()["items"]) == 2

        null_stock = client.get("/api/v1/stocks/DEMO-D4")
        assert null_stock.status_code == 200
        assert null_stock.json()["price"] is None

        topic = client.get("/api/v1/topics/edge-ai")
        assert topic.status_code == 200
        assert topic.json()["constituentCount"] == 2

        candidates = client.get("/api/v1/strategies/KD/candidates")
        assert candidates.status_code == 200
        assert candidates.json()["items"][0]["price"] is None

        rotation = client.get("/api/v1/analytics/topic-rotation", params={"days": 14})
        assert rotation.status_code == 200
        assert rotation.json()["total"] == 3

        performance = client.get(
            "/api/v1/analytics/strategy-performance",
            params={"strategy_key": "MAS", "horizon": "T+5"},
        )
        assert performance.status_code == 200
        assert performance.json()["total"] == 1

        snapshot = client.get("/api/v1/snapshot/latest")
        assert snapshot.status_code == 200
        assert snapshot.json()["snapshotVersion"] == "enterprise-db-001"
        assert len(snapshot.json()["strategyRegistry"]["strategies"]) == 6

        missing = client.get("/api/v1/stocks/UNKNOWN")
        assert missing.status_code == 404
        assert missing.headers["content-type"].startswith("application/problem+json")
        assert missing.json()["type"].endswith("/not-found")

        invalid_page = client.get("/api/v1/stocks", params={"limit": 0})
        assert invalid_page.status_code == 422
        assert invalid_page.headers["content-type"].startswith("application/problem+json")


def test_empty_database_returns_problem_json(clean_database: Engine) -> None:
    app = create_app(Settings(DATABASE_URL=str(clean_database.url)))

    def override_db():
        with Session(clean_database) as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        response = client.get("/api/v1/meta/data-status")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
