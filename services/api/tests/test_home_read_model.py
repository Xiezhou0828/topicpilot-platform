from __future__ import annotations

import pytest
from conftest import DEMO_BUNDLE, SCHEMA_PATH
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from topicpilot_api.bundle import load_bundle
from topicpilot_api.config import Settings
from topicpilot_api.database import get_db
from topicpilot_api.importer import import_bundle
from topicpilot_api.main import create_app

pytestmark = pytest.mark.postgres


def test_home_endpoint_is_one_postgres_backed_contract(clean_database: Engine) -> None:
    bundle = load_bundle(DEMO_BUNDLE, SCHEMA_PATH)
    with Session(clean_database) as session:
        import_bundle(session, bundle)

    app = create_app(Settings(DATABASE_URL=str(clean_database.url)))

    def override_db():
        with Session(clean_database, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        response = client.get("/api/v2/home")

    assert response.status_code == 200
    payload = response.json()
    assert set(
        (
            "marketOverview",
            "dailyFocus",
            "mainTopics",
            "marketPulse",
            "heatingTopics",
            "coolingTopics",
            "opportunities",
            "dataQuality",
        )
    ).issubset(payload)
    assert payload["marketOverview"]["dataStatus"] == "PARTIAL"
    assert payload["marketOverview"]["trackedTopicCount"] == 3
    assert len(payload["mainTopics"]) == 3
    assert all(item["currentGrade"] != "X" for item in payload["heatingTopics"])
    assert all(item["currentGrade"] != "X" for item in payload["coolingTopics"])
    assert payload["dataQuality"]["source"] == "POSTGRESQL"
