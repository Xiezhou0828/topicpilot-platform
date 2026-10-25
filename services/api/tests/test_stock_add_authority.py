from __future__ import annotations

import json
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

import pytest

import topicpilot_api.stock_add_authority as authority
from topicpilot_api.stock_add_authority import (
    PROTECTED_DB_SOURCE,
    FormalAuthorityReadError,
    read_formal_authority_snapshot,
)


def _stock(code: str, *, name: str | None = None) -> dict:
    return {
        "instrumentId": f"instrument-{code}",
        "code": code,
        "symbol": code,
        "name": name or f"Company {code}",
        "market": "TPE",
        "exchange": "TWSE",
        "listing": "上市",
        "active": True,
        "enabled": True,
    }


def _topic(topic_id: str, *, slug: str | None = None, name: str | None = None) -> dict:
    normalized_slug = slug or f"topic-{topic_id}"
    return {
        "topicId": topic_id,
        "slug": normalized_slug,
        "name": name or normalized_slug,
        "status": "ENABLED",
        "enabled": True,
        "kind": "LEAF",
        "hierarchy": {"parent": None},
    }


def _paged_response(
    items: list[dict], offset: int, limit: int, *, as_of: str | None = None
) -> bytes:
    payload = {
        "items": items[offset : offset + limit],
        "total": len(items),
        "limit": limit,
        "offset": offset,
    }
    if as_of is not None:
        payload["asOf"] = as_of
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _openapi_response(description: str = "Read-only API backed by formal data.") -> bytes:
    return json.dumps({"info": {"description": description}}).encode("utf-8")


def _stable_fetch(stocks: list[dict], topics: list[dict]):
    def fetch(url: str) -> bytes:
        parsed = urlsplit(url)
        if parsed.path == "/openapi.json":
            return _openapi_response()
        query = parse_qs(parsed.query)
        limit = int(query["limit"][0])
        offset = int(query["offset"][0])
        if parsed.path == "/api/v2/stocks":
            return _paged_response(stocks, offset, limit)
        if parsed.path == "/api/v2/topic-catalog":
            return _paged_response(topics, offset, limit, as_of="2026-10-25")
        raise AssertionError(f"unexpected endpoint: {url}")

    return fetch


def test_complete_formal_reads_are_pinned_rechecked_and_hashed(monkeypatch) -> None:
    monkeypatch.setattr(authority, "PAGE_SIZE_STOCKS", 2)
    monkeypatch.setattr(authority, "PAGE_SIZE_TOPICS", 2)
    stocks = [_stock("1303"), _stock("2330"), _stock("3483")]
    topics = [_topic("topic-1"), _topic("topic-2"), _topic("topic-3")]
    calls: list[str] = []
    stable = _stable_fetch(stocks, topics)

    def fetch(url: str) -> bytes:
        calls.append(url)
        return stable(url)

    snapshot = read_formal_authority_snapshot(fetch)

    assert snapshot.stock_status("2468") == "NO_MATCH_CONFIRMED"
    assert snapshot.stock_status("2330") == "MATCH_FOUND"
    assert snapshot.master_evidence.record_count == 3
    assert snapshot.master_evidence.page_count == 2
    assert snapshot.topic_catalog_evidence.record_count == 3
    assert snapshot.topic_catalog_evidence.page_count == 2
    assert snapshot.master_evidence.sha256 != snapshot.topic_catalog_evidence.sha256
    assert len(calls) == 9  # source declaration plus two complete authority passes
    topic_urls = [url for url in calls if "/topic-catalog?" in url]
    assert "asOf=2026-10-25" in topic_urls[-1]


def test_stock_master_lookup_uses_market_and_code_composite_key() -> None:
    stocks = [_stock("2468"), {**_stock("2468"), "market": "TWO"}]
    snapshot = authority.FormalAuthoritySnapshot(
        stock_items=tuple(stocks),
        topic_items=(_topic("topic-1"),),
        master_evidence=authority._read_evidence(
            digest="a" * 64, count=2, page_count=1, scope="test"
        ),
        topic_catalog_evidence=authority._read_evidence(
            digest="b" * 64, count=1, page_count=1, scope="test"
        ),
    )

    assert snapshot.stock_status("2468", "TPE") == "MATCH_FOUND"
    assert snapshot.stock_status("2468", "TWO") == "MATCH_FOUND"
    assert snapshot.stock_status("1357", "TPE") == "NO_MATCH_CONFIRMED"
    assert snapshot.stock_status("2468", "OTC") == "NO_MATCH_CONFIRMED"


class _Result:
    def __init__(self, *, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def mappings(self):
        return self

    def __iter__(self):
        return iter(self._rows)

    def scalar_one(self):
        return self._scalar


class _ProtectedConnection:
    def __init__(
        self,
        *,
        mutation_privilege=False,
        identity_overrides=None,
        database_name="topicpilot_test",
        unexpected_relation_privilege=False,
        sequence_privilege=False,
        column_mutation_privilege=False,
        public_schema_create=False,
        topicpilot_schema_create=False,
    ):
        self.mutation_privilege = mutation_privilege
        self.identity_overrides = identity_overrides or {}
        self.database_name = database_name
        self.unexpected_relation_privilege = unexpected_relation_privilege
        self.sequence_privilege = sequence_privilege
        self.column_mutation_privilege = column_mutation_privilege
        self.public_schema_create = public_schema_create
        self.topicpilot_schema_create = topicpilot_schema_create
        self.statements: list[str] = []

    def execute(self, statement, _parameters=None):
        sql = str(statement)
        self.statements.append(sql)
        if sql.startswith("SET TRANSACTION"):
            return _Result()
        if "SHOW transaction_read_only" in sql:
            return _Result(scalar="on")
        if "SHOW transaction_isolation" in sql:
            return _Result(scalar="repeatable read")
        if "SELECT current_database()" in sql:
            return _Result(scalar=self.database_name)
        if "FROM pg_catalog.pg_roles" in sql:
            return _Result(
                rows=[
                    {
                        "current_user": "topicpilot_catalog_readonly",
                        "session_user": "topicpilot_catalog_readonly",
                        "rolname": "topicpilot_catalog_readonly",
                        "rolsuper": False,
                        "rolcreatedb": False,
                        "rolcreaterole": False,
                        "rolreplication": False,
                        "rolbypassrls": False,
                        "rolinherit": False,
                        "rolcanlogin": True,
                        "granted_role_count": 0,
                        "is_database_owner": False,
                        "can_create_database_objects": False,
                        "effective_temporary_privilege": True,
                        "direct_database_mutation_privilege": False,
                        **self.identity_overrides,
                    }
                ]
            )
        if "AS required(table_name)" in sql:
            return _Result(
                rows=[
                    {
                        "table_name": table,
                        "can_select": True,
                        "can_insert": self.mutation_privilege,
                        "can_update": False,
                        "can_delete": False,
                        "can_truncate": False,
                        "can_reference": False,
                        "can_insert_column": self.column_mutation_privilege,
                        "can_update_column": False,
                        "can_reference_column": False,
                        "can_trigger": False,
                    }
                    for table in authority._CATALOG_TABLES
                ]
            )
        if "pg_catalog.pg_class relation" in sql:
            return _Result(rows=[{"privilege_count": int(self.unexpected_relation_privilege)}])
        if "pg_catalog.pg_class sequence" in sql:
            return _Result(rows=[{"privilege_count": int(self.sequence_privilege)}])
        if "has_schema_privilege" in sql:
            return _Result(
                rows=[
                    {
                        "public_create": self.public_schema_create,
                        "topicpilot_create": self.topicpilot_schema_create,
                    }
                ]
            )
        raise AssertionError(f"unexpected query: {sql}")


def test_protected_database_role_is_verified_before_catalog_queries() -> None:
    connection = _ProtectedConnection()

    controls = authority._verify_protected_read_connection(
        connection, "topicpilot_catalog_readonly", "topicpilot_test"
    )

    assert controls["transactionReadOnly"] is True
    assert controls["transactionIsolation"] == "repeatable read"
    assert controls["allowedTables"] == list(authority._CATALOG_TABLES)
    assert controls["mutationPrivilegesObserved"] is False
    assert connection.statements[0].startswith("SET TRANSACTION ISOLATION LEVEL")


def test_protected_database_role_with_any_mutation_privilege_is_blocked() -> None:
    with pytest.raises(FormalAuthorityReadError, match="UNSAFE_TABLE_PRIVILEGES"):
        authority._verify_protected_read_connection(
            _ProtectedConnection(mutation_privilege=True),
            "topicpilot_catalog_readonly",
            "topicpilot_test",
        )


def test_protected_database_role_with_column_level_mutation_privilege_is_blocked() -> None:
    with pytest.raises(FormalAuthorityReadError, match="UNSAFE_TABLE_PRIVILEGES"):
        authority._verify_protected_read_connection(
            _ProtectedConnection(column_mutation_privilege=True),
            "topicpilot_catalog_readonly",
            "topicpilot_test",
        )


def test_protected_database_role_allows_public_default_temp_privilege() -> None:
    controls = authority._verify_protected_read_connection(
        _ProtectedConnection(
            identity_overrides={
                "effective_temporary_privilege": True,
                "direct_database_mutation_privilege": False,
            }
        ),
        "topicpilot_catalog_readonly",
        "topicpilot_test",
    )

    assert controls["effectiveTemporaryPrivilegeObserved"] is True
    assert controls["directDatabaseMutationPrivilegeObserved"] is False


def test_protected_database_role_with_direct_temporary_database_grant_is_blocked() -> None:
    with pytest.raises(FormalAuthorityReadError, match="READ_ONLY_IDENTITY_CHECK_FAILED"):
        authority._verify_protected_read_connection(
            _ProtectedConnection(identity_overrides={"direct_database_mutation_privilege": True}),
            "topicpilot_catalog_readonly",
            "topicpilot_test",
        )


@pytest.mark.parametrize(
    "identity_override",
    [
        {"is_database_owner": True},
        {"can_create_database_objects": True},
        {"granted_role_count": 1},
        {"rolinherit": True},
        {"rolcreatedb": True},
    ],
)
def test_protected_database_rejects_owner_or_elevated_role(identity_override) -> None:
    with pytest.raises(FormalAuthorityReadError, match="IDENTITY_CHECK_FAILED"):
        authority._verify_protected_read_connection(
            _ProtectedConnection(identity_overrides=identity_override),
            "topicpilot_catalog_readonly",
            "topicpilot_test",
        )


def test_protected_database_rejects_unexpected_database_name() -> None:
    with pytest.raises(FormalAuthorityReadError, match="TARGET_MISMATCH"):
        authority._verify_protected_read_connection(
            _ProtectedConnection(database_name="staging"),
            "topicpilot_catalog_readonly",
            "production",
        )


@pytest.mark.parametrize(
    ("connection_options", "error_code"),
    [
        ({"unexpected_relation_privilege": True}, "UNEXPECTED_RELATION_PRIVILEGE"),
        ({"sequence_privilege": True}, "SEQUENCE_PRIVILEGE"),
        ({"public_schema_create": True}, "SCHEMA_CREATE_PRIVILEGE"),
        ({"topicpilot_schema_create": True}, "SCHEMA_CREATE_PRIVILEGE"),
    ],
)
def test_protected_database_rejects_privileges_outside_read_scope(
    connection_options, error_code
) -> None:
    with pytest.raises(FormalAuthorityReadError, match=error_code):
        authority._verify_protected_read_connection(
            _ProtectedConnection(**connection_options),
            "topicpilot_catalog_readonly",
            "topicpilot_test",
        )


def test_protected_database_read_path_is_not_available_locally(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    with pytest.raises(FormalAuthorityReadError, match="REQUIRES_GITHUB_ACTIONS"):
        authority._require_protected_workflow_context()


def test_protected_database_requires_explicit_expected_target(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "Xiezhou0828/topicpilot-platform")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv(
        "GITHUB_WORKFLOW_REF",
        "Xiezhou0828/topicpilot-platform/.github/workflows/"
        "stock-add-authority-readback.yml@refs/heads/main",
    )
    monkeypatch.setenv(
        "TOPICPILOT_PRODUCTION_CATALOG_READONLY_DATABASE_URL",
        "postgresql://reader:fake-password@db.example.test/topicpilot",
    )
    monkeypatch.setenv("TOPICPILOT_PRODUCTION_CATALOG_READONLY_ROLE", "topicpilot_catalog_readonly")
    monkeypatch.setenv("TOPICPILOT_PRODUCTION_CATALOG_READONLY_EXPECTED_HOST", "db.example.test")
    monkeypatch.setenv("TOPICPILOT_PRODUCTION_CATALOG_READONLY_EXPECTED_DATABASE", "topicpilot")

    assert authority._require_protected_workflow_context() == (
        "postgresql://reader:fake-password@db.example.test/topicpilot",
        "topicpilot_catalog_readonly",
        "topicpilot",
    )

    monkeypatch.setenv("GITHUB_REF", "refs/heads/unreviewed-branch")
    with pytest.raises(FormalAuthorityReadError, match="REQUIRES_CANONICAL_MAIN"):
        authority._require_protected_workflow_context()

    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_WORKFLOW_REF", "other.yml@refs/heads/main")
    with pytest.raises(FormalAuthorityReadError, match="WRONG_WORKFLOW"):
        authority._require_protected_workflow_context()


def test_protected_database_read_evidence_is_current_authority() -> None:
    evidence = authority.AuthorityReadEvidence(
        source=PROTECTED_DB_SOURCE,
        environment="PRODUCTION_READ_ONLY",
        read_at=datetime.now(UTC).isoformat(),
        complete=True,
        sha256="a" * 64,
    )
    assert evidence.verified_current_read is True


def test_partial_page_is_blocked_instead_of_confirming_absence(monkeypatch) -> None:
    monkeypatch.setattr(authority, "PAGE_SIZE_STOCKS", 2)

    def fetch(url: str) -> bytes:
        parsed = urlsplit(url)
        if parsed.path == "/openapi.json":
            return _openapi_response()
        if parsed.path == "/api/v2/stocks":
            return json.dumps(
                {
                    "items": [_stock("1303")],
                    "total": 2,
                    "limit": 2,
                    "offset": 0,
                }
            ).encode()
        raise AssertionError("topic catalog should not be read after a blocked stock page")

    with pytest.raises(FormalAuthorityReadError, match="SHORT_NONFINAL_PAGE"):
        read_formal_authority_snapshot(fetch)


def test_changed_stock_universe_between_rechecks_is_blocked(monkeypatch) -> None:
    stocks_first = [_stock("1303")]
    stocks_second = [_stock("1303", name="Changed name")]
    stock_passes = 0

    def fetch(url: str) -> bytes:
        nonlocal stock_passes
        parsed = urlsplit(url)
        if parsed.path == "/openapi.json":
            return _openapi_response()
        query = parse_qs(parsed.query)
        if parsed.path == "/api/v2/stocks":
            if query["offset"] == ["0"]:
                stock_passes += 1
            items = stocks_first if stock_passes == 1 else stocks_second
            return _paged_response(items, int(query["offset"][0]), int(query["limit"][0]))
        raise AssertionError("topic catalog should not be read after unstable stocks")

    with pytest.raises(FormalAuthorityReadError, match="STOCK_UNIVERSE_CHANGED"):
        read_formal_authority_snapshot(fetch)


def test_duplicate_formal_stock_identity_is_blocked() -> None:
    fetch = _stable_fetch([_stock("1303"), _stock("1303")], [_topic("topic-1")])
    with pytest.raises(FormalAuthorityReadError, match="STOCK_IDENTITY_DUPLICATE"):
        read_formal_authority_snapshot(fetch)


def test_duplicate_topic_slug_is_blocked() -> None:
    topics = [_topic("topic-1", slug="duplicate"), _topic("topic-2", slug="duplicate")]
    fetch = _stable_fetch([_stock("1303")], topics)
    with pytest.raises(FormalAuthorityReadError, match="TOPIC_IDENTITY_DUPLICATE"):
        read_formal_authority_snapshot(fetch)


def test_mismatched_total_across_pages_is_blocked(monkeypatch) -> None:
    monkeypatch.setattr(authority, "PAGE_SIZE_STOCKS", 1)

    def fetch(url: str) -> bytes:
        parsed = urlsplit(url)
        if parsed.path == "/openapi.json":
            return _openapi_response()
        query = parse_qs(parsed.query)
        offset = int(query["offset"][0])
        payload = {
            "items": [_stock("1303")] if offset == 0 else [_stock("2330")],
            "total": 2 if offset == 0 else 3,
            "limit": 1,
            "offset": offset,
        }
        return json.dumps(payload).encode()

    with pytest.raises(FormalAuthorityReadError, match="TOTAL_CHANGED"):
        read_formal_authority_snapshot(fetch)


def test_untrusted_origin_is_rejected_before_network_access() -> None:
    with pytest.raises(FormalAuthorityReadError, match="UNTRUSTED_FORMAL_API_ORIGIN"):
        authority._fetch_formal_api("http://topicpilot-api.onrender.com/api/v2/stocks")


def test_declared_synthetic_public_data_is_not_accepted_as_formal_authority() -> None:
    def fetch(url: str) -> bytes:
        assert url.endswith("/openapi.json")
        return _openapi_response(
            "Read-only API. The public deployment contains synthetic data only."
        )

    with pytest.raises(FormalAuthorityReadError, match="DECLARED_SYNTHETIC_DATA"):
        read_formal_authority_snapshot(fetch)


def test_missing_data_mode_declaration_is_blocked() -> None:
    with pytest.raises(FormalAuthorityReadError, match="DATA_MODE_UNDECLARED"):
        read_formal_authority_snapshot(lambda _: json.dumps({"info": {}}).encode())


def test_missing_topic_as_of_is_blocked() -> None:
    def fetch(url: str) -> bytes:
        parsed = urlsplit(url)
        if parsed.path == "/openapi.json":
            return _openapi_response()
        query = parse_qs(parsed.query)
        if parsed.path == "/api/v2/stocks":
            return _paged_response(
                [_stock("1303")],
                int(query["offset"][0]),
                int(query["limit"][0]),
            )
        return json.dumps(
            {"items": [_topic("topic-1")], "total": 1, "limit": 500, "offset": 0}
        ).encode()

    with pytest.raises(FormalAuthorityReadError, match="MISSING_AS_OF"):
        read_formal_authority_snapshot(fetch)
