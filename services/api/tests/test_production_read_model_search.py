from __future__ import annotations

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
