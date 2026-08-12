from fastapi.testclient import TestClient

from topicpilot_api.main import create_app


def test_admin_schema_is_metadata_derived_and_covers_frozen_domains():
    response = TestClient(create_app()).get("/api/v1/admin/schema")
    assert response.status_code == 200
    payload = response.json()
    names = {table["name"] for table in payload["tables"]}
    assert payload["source"] == "SQLAlchemy Base.metadata"
    assert {
        "markets",
        "topics",
        "instrument_topic_relations",
        "raw_market_observations",
        "observation_timeline_entries",
        "canonical_observations",
        "reference_registry_sets",
        "legacy_import_runs",
    } <= names


def test_admin_routes_are_read_only():
    def walk(routes):
        for route in routes:
            if hasattr(route, "path"):
                yield route
            if hasattr(route, "routes"):
                yield from walk(route.routes)

    app = create_app()
    routes = set(app.openapi()["paths"])
    assert "/api/v1/admin/dashboard" in routes
    assert "/api/v1/admin/schema" in routes
    assert all(
        set(methods) <= {"get"}
        for path, methods in (
            (path, spec)
            for path, spec in app.openapi()["paths"].items()
            if path.startswith("/api/v1/admin")
            for methods in [spec]
        )
    )
