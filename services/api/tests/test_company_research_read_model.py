from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from topicpilot_api.company_research.contract import CompanyResearchReadModel
from topicpilot_api.company_research.store import FileCompanyResearchReadStore
from topicpilot_api.config import Settings
from topicpilot_api.main import create_app


def _record(**overrides: object) -> dict:
    value = {
        "company_code": "1303",
        "research_version": "v3.0.0",
        "effective_date": "2026-10-12",
        "as_of_date": "2026-10-10",
        "publication_status": "PUBLISHED",
        "review_status": "APPROVED",
        "source_rights_status": "APPROVED",
        "reviewer": "owner-1",
        "approval_evidence": {
            "reviewer": "owner-1",
            "approved_at": datetime.now(UTC).isoformat(),
            "decision_id": "decision-1303-v3",
        },
        "company_website": "https://example.invalid/1303",
        "sections": [
            {
                "key": "overview",
                "title_zh_tw": "公司定位",
                "body_zh_tw": "電子材料與化工產品製造商。",
                "status": "VERIFIED",
                "source_ids": ["official-1"],
            }
        ],
        "sources": [
            {
                "source_id": "official-1",
                "source_type": "official_company_website",
                "title_zh_tw": "公司官網",
                "url": "https://example.invalid/1303",
                "published_at": "2026-10-10",
                "content_status": "VERIFIED",
                "rights_status": "APPROVED",
            }
        ],
        "limitations_zh_tw": [],
    }
    value.update(overrides)
    return value


def test_public_projection_is_published_only_after_all_gates_pass(tmp_path) -> None:
    path = tmp_path / "research.json"
    path.write_text(json.dumps({"records": [_record()]}), encoding="utf-8")
    model = CompanyResearchReadModel.model_validate(_record())
    projection = FileCompanyResearchReadStore(str(path)).get_public("1303")
    assert projection.publication_status == "PUBLISHED"
    assert projection.sections[0].title_zh_tw == "公司定位"
    assert projection.official_sources == ["https://example.invalid/1303"]
    assert model.formal_topic_authority_mutation is False


def test_unapproved_record_fails_closed_without_exposing_sections(tmp_path) -> None:
    path = tmp_path / "research.json"
    path.write_text(
        json.dumps({"records": [_record(review_status="PENDING")]}), encoding="utf-8"
    )
    projection = FileCompanyResearchReadStore(str(path)).get_public("1303")
    assert projection.publication_status == "UNPUBLISHED"
    assert projection.sections == []


def test_missing_store_is_not_connected(tmp_path) -> None:
    projection = FileCompanyResearchReadStore(str(tmp_path / "missing.json")).get_public("1314")
    assert projection.publication_status == "NOT_CONNECTED"


def test_api_exposes_read_only_fail_closed_boundary(tmp_path) -> None:
    path = tmp_path / "research.json"
    path.write_text(json.dumps({"records": [_record()]}), encoding="utf-8")
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        research_read_model_path=str(path),
    )
    app = create_app(settings)
    app.state.company_research_read_store = FileCompanyResearchReadStore(str(path))
    response = TestClient(app).get("/api/v2/stocks/1303/research")
    assert response.status_code == 200
    assert response.json()["publication_status"] == "PUBLISHED"
    assert response.json()["official_sources"] == ["https://example.invalid/1303"]
