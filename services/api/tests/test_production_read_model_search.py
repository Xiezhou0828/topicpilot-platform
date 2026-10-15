from __future__ import annotations

from datetime import date

from topicpilot_api import production_read_model
from topicpilot_api.main import create_app
from topicpilot_api.production_read_model import STOCK_ROWS_SQL, normalize_stock_search


def test_stock_search_normalizes_whitespace_and_empty_values() -> None:
    assert normalize_stock_search(" 2330 ") == "2330"
    assert normalize_stock_search("  台積電  ") == "台積電"
    assert normalize_stock_search("") is None
    assert normalize_stock_search("   ") is None
    assert normalize_stock_search(None) is None


def test_stock_rows_sql_owns_case_insensitive_code_and_name_substring_search() -> None:
    sql = str(STOCK_ROWS_SQL)
    assert "CAST(:search AS text) IS NULL" in sql
    assert "POSITION(LOWER(CAST(:search AS text)) IN LOWER(i.instrument_code)) > 0" in sql
    assert "POSITION(LOWER(CAST(:search AS text)) IN LOWER(COALESCE(i.name, ''))) > 0" in sql
    assert "topicRelations" not in sql
    assert "technical" not in sql.lower()


def test_stock_list_openapi_exposes_search_as_a_formal_query_parameter() -> None:
    parameters = create_app().openapi()["paths"]["/api/v2/stocks"]["get"]["parameters"]
    search = next(item for item in parameters if item["name"] == "search")
    assert search["in"] == "query"
    assert "code or name" in search["description"]


def test_strength_read_serializes_snapshot_date_for_string_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        production_read_model,
        "build_topic_strength_lifecycle_read",
        lambda *_: {
            "ownerSeededV0": {
                "status": "WAITING_FOR_CANONICAL_ACTIVATION",
                "policyId": "policy",
                "policyVersion": "v1",
                "policyHash": "hash",
                "implementationSha": None,
                "asOfDate": None,
                "formalDailyGrade": None,
                "absolute": {},
                "relative": {},
                "lifecycle": {},
                "observationFlags": [],
                "observationFlagCopy": {},
                "qualityFlags": {},
                "diagnosticOnly": True,
            }
        },
    )

    result = production_read_model._strength_read(
        None,
        {
            "slug": "topic",
            "snapshot_date": date(2026, 10, 13),
            "formal_strength_publication_status": "PUBLISHED",
            "formal_strength_components": {},
        },
        None,
    )

    assert result["ownerSeededV0"]["asOfDate"] == "2026-10-13"
