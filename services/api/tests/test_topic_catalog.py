from __future__ import annotations

from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from topicpilot_api.database import get_db
from topicpilot_api.main import create_app
from topicpilot_api.topic_catalog import (
    FORMAL_CURRENT_SNAPSHOT_ROWS_SQL,
    FORMAL_MAPPING_EARLIEST_DATE,
    MAX_HISTORY_DAYS,
    read_formal_snapshot_history,
    read_topic_minimum_page,
)
from topicpilot_api.topic_catalog_schemas import TopicMinimumReadPage, TopicSnapshotHistoryReadPage


class _Result:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def mappings(self) -> list[dict]:
        return self.rows


class _Session:
    def __init__(self, *, snapshot_rows: list[dict] | None = None) -> None:
        self.snapshot_rows = snapshot_rows
        self.executed: list[str] = []

    def execute(self, statement, params=None):
        sql = statement.text
        self.executed.append(sql)
        if "FROM topicpilot.topics t" in sql:
            rows = [
                    {
                        "topic_id": "parent-id",
                        "slug": "energy",
                        "name": "Energy",
                        "status": "ACTIVE",
                        "dictionary_version": "topics.v1",
                    },
                    {
                        "topic_id": "leaf-id",
                        "slug": "solar",
                        "name": "Solar",
                        "status": "ACTIVE",
                        "dictionary_version": "topics.v1",
                    },
                ]
            if params and params.get("slug") == "solar":
                rows = rows[1:]
            return _Result(rows)
        if "FROM topicpilot.topic_hierarchy h" in sql:
            return _Result(
                [
                    {
                        "parent_topic_id": "parent-id",
                        "parent_slug": "energy",
                        "parent_name": "Energy",
                        "child_topic_id": "leaf-id",
                        "child_slug": "solar",
                        "child_name": "Solar",
                        "relationship_type": "PARENT",
                        "hierarchy_version": "hierarchy.v1",
                        "valid_from": date(2026, 8, 7),
                        "valid_to": None,
                        "display_order": 1,
                    }
                ]
            )
        if "FROM topicpilot.instrument_topic_relations r" in sql:
            return _Result(
                [
                    {
                        "topic_id": "leaf-id",
                        "instrument_id": "instrument-id",
                        "instrument_code": "2330",
                        "instrument_name": "Synthetic Instrument",
                        "market_code": "TPE",
                        "relation_type": "RELATED",
                        "relation_version": "relations.v1",
                        "valid_from": date(2026, 8, 7),
                        "valid_to": None,
                    }
                ]
            )
        if "FROM topicpilot.topic_snapshots s" in sql:
            if self.snapshot_rows is None:
                raise SQLAlchemyError("snapshot table unavailable")
            return _Result(self.snapshot_rows)
        raise AssertionError(f"unexpected query: {sql}")

    def scalar(self, statement, params=None):
        return len(self.snapshot_rows or [])


def _snapshot_row(topic_id: str = "leaf-id") -> dict:
    return {
        "snapshot_date": date(2026, 8, 13),
        "topic_id": topic_id,
        "topic_slug": "solar",
        "topic_name": "Solar",
        "topic_direction": "WARMING",
        "topic_score": None,
        "market_grade": None,
        "stock_count": 1,
        "observed_stock_count": 1,
        "coverage_pct": 100,
        "average_change": 1.25,
        "data_status": "COMPLETE",
        "score_status": "DEFERRED",
        "calculation_version": "topic-daily-state.v1",
        "as_of_at": datetime(2026, 8, 13, 8, 0),
        "generated_at": datetime(2026, 8, 13, 8, 0),
        "finalized_at": datetime(2026, 8, 13, 8, 0),
        "published_at": datetime(2026, 8, 13, 8, 0),
        "publication_mode": "FORMAL",
        "publication_state": "PUBLISHED",
        "membership_mode": "PIT_FORMAL",
        "generated_state": "GENERATED",
        "finality_state": "FINAL",
        "trading_day_state": "TRADING",
        "freshness_state": "AS_OF_TRADING_DATE",
        "snapshot_identity": "formal:solar:2026-08-13:hash",
        "correction_sequence": 0,
        "relation_version": "relations.v1",
        "mapping_effective_from": date(2026, 8, 7),
        "membership_snapshot_id": "membership:solar:2026-08-13",
        "membership_snapshot_hash": "membership-hash",
        "source_run_id": "run:2026-08-13",
        "source_artifact_id": "artifact:2026-08-13",
        "source_artifact_hash": "artifact-hash",
        "lineage_hash": "lineage-hash",
        "reference_registry_version": "tw-reference-v1",
        "mapping_policy_version": "topic-membership-pit.v1",
    }


def test_minimum_catalog_keeps_identity_when_formal_snapshot_authority_is_unavailable():
    session = _Session()
    page = read_topic_minimum_page(session, as_of=date(2026, 8, 31), limit=10)
    TopicMinimumReadPage.model_validate(page)

    assert page["total"] == 2
    parent, leaf = page["items"]
    assert parent["kind"] == "PARENT"
    assert parent["members"] == []
    assert parent["currentFormalSnapshot"]["availability"]["state"] == "NOT_APPLICABLE"
    assert leaf["kind"] == "LEAF"
    assert leaf["members"][0]["code"] == "2330"
    assert leaf["currentFormalSnapshot"]["availability"]["state"] == "UNAVAILABLE"
    assert (
        leaf["currentFormalSnapshot"]["availability"]["reasonCode"]
        == "FORMAL_SNAPSHOT_AUTHORITY_UNAVAILABLE"
    )


def test_formal_snapshot_is_consumed_only_after_pit_finality_and_lineage_checks():
    session = _Session(snapshot_rows=[_snapshot_row()])
    page = read_topic_minimum_page(session, as_of=date(2026, 8, 31), limit=10)
    leaf = page["items"][1]

    current = leaf["currentFormalSnapshot"]
    assert current["availability"]["state"] == "AVAILABLE"
    assert current["snapshot"]["publication"]["membershipMode"] == "PIT_FORMAL"
    assert current["snapshot"]["publication"]["finalityState"] == "FINAL"
    assert current["snapshot"]["source"]["lineageHash"] == "lineage-hash"
    TopicMinimumReadPage.model_validate(page)


def test_bounded_history_returns_only_formal_published_leaf_rows():
    session = _Session(snapshot_rows=[_snapshot_row()])
    result = read_formal_snapshot_history(
        session,
        "solar",
        as_of=date(2026, 8, 31),
        from_date=date(2026, 8, 7),
        to_date=date(2026, 8, 13),
        limit=10,
    )

    assert result["availability"]["state"] == "AVAILABLE"
    assert result["total"] == 1
    assert result["items"][0]["snapshotDate"] == date(2026, 8, 13)
    TopicSnapshotHistoryReadPage.model_validate(result)


def test_pre_boundary_history_is_unavailable_and_does_not_read_snapshot_rows():
    session = _Session(snapshot_rows=[_snapshot_row()])
    result = read_formal_snapshot_history(
        session,
        "solar",
        as_of=date(2026, 8, 31),
        from_date=date(2026, 8, 6),
        to_date=date(2026, 8, 13),
        limit=10,
    )

    assert result["items"] == []
    assert result["availability"]["state"] == "UNAVAILABLE"
    assert result["availability"]["reasonCode"] == "PRE_FORMAL_SNAPSHOT_BOUNDARY"
    assert not any(":from_date" in query for query in session.executed)


def test_history_window_is_bounded():
    assert MAX_HISTORY_DAYS == 366
    assert "PUBLISHED" in FORMAL_CURRENT_SNAPSHOT_ROWS_SQL.text
    assert "PIT_FORMAL" in FORMAL_CURRENT_SNAPSHOT_ROWS_SQL.text
    assert date(2026, 8, 7) == FORMAL_MAPPING_EARLIEST_DATE


def test_openapi_documents_minimum_topic_contract():
    paths = create_app().openapi()["paths"]
    assert {
        "/api/v2/topic-catalog",
        "/api/v2/topic-catalog/{slug}",
        "/api/v2/topic-catalog/{slug}/snapshot",
        "/api/v2/topic-catalog/{slug}/snapshots",
    } <= set(paths)
    snapshot_response = paths["/api/v2/topic-catalog/{slug}/snapshot"]["get"]["responses"]["200"]
    assert snapshot_response["content"]["application/json"]["schema"]["$ref"].endswith(
        "/TopicCurrentSnapshotRead"
    )
    assert "post" not in paths["/api/v2/topic-catalog"]


def test_minimum_api_routes_serialize_identity_and_parent_fail_closed_boundary():
    session = _Session()
    app = create_app()

    def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        catalog = client.get("/api/v2/topic-catalog", params={"asOf": "2026-08-31"})
        parent_snapshot = client.get("/api/v2/topic-catalog/energy/snapshot")

    assert catalog.status_code == 200
    assert catalog.json()["items"][1]["members"][0]["code"] == "2330"
    assert parent_snapshot.status_code == 200
    assert parent_snapshot.json()["availability"]["state"] == "NOT_APPLICABLE"
