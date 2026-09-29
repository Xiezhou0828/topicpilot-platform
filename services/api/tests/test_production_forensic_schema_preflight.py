from __future__ import annotations

from pathlib import Path

import pytest

from topicpilot_api.production_forensic_readback import (
    EXPECTED_PREFLIGHT_COLUMNS,
    FORENSIC_COMMAND_SCHEMA_PREFLIGHT,
    PREFLIGHT_COLUMN_QUERY,
    PREFLIGHT_TABLE_QUERY,
    PRIVILEGE_QUERY,
    ForensicReadbackError,
    run_schema_preflight,
    validate_command,
)


class _ScalarResult:
    def __init__(self, value: str) -> None:
        self.value = value

    def scalar_one(self) -> str:
        return self.value


class _MappingResult:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    def mappings(self) -> list[dict[str, object]]:
        return self.rows


class _Connection:
    def __init__(self, *, current_user: str = "topicpilot_forensic_readonly") -> None:
        self.current_user = current_user
        self.statements: list[str] = []

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def begin(self) -> _Connection:
        return self

    def execute(self, statement, parameters=None):
        sql = str(statement)
        self.statements.append(sql)
        if "SHOW transaction_read_only" in sql:
            return _ScalarResult("on")
        if "current_database()" in sql:
            return _MappingResult(
                [
                    {
                        "database_name": "neondb",
                        "current_user": self.current_user,
                        "session_user": self.current_user,
                    }
                ]
            )
        if "information_schema.tables" in sql:
            return _MappingResult(
                [
                    {"table_name": table, "table_exists": True}
                    for table in EXPECTED_PREFLIGHT_COLUMNS
                ]
            )
        if "information_schema.columns" in sql:
            return _MappingResult(
                [
                    {
                        "table_name": table,
                        "column_name": column,
                        "data_type": "text",
                        "is_nullable": "YES",
                    }
                    for table, columns in EXPECTED_PREFLIGHT_COLUMNS.items()
                    for column in sorted(columns)
                ]
            )
        if "has_table_privilege" in sql:
            return _MappingResult(
                [
                    {
                        "table_name": table,
                        "select_allowed": True,
                        "insert_allowed": False,
                        "update_allowed": False,
                        "delete_allowed": False,
                        "truncate_allowed": False,
                    }
                    for table in EXPECTED_PREFLIGHT_COLUMNS
                ]
            )
        return _MappingResult([])


class _Engine:
    def __init__(self, connection: _Connection) -> None:
        self.connection = connection

    def connect(self) -> _Connection:
        return self.connection

    def dispose(self) -> None:
        return None


def test_schema_preflight_is_a_fixed_command() -> None:
    assert validate_command(FORENSIC_COMMAND_SCHEMA_PREFLIGHT) == (
        FORENSIC_COMMAND_SCHEMA_PREFLIGHT
    )


def test_schema_preflight_returns_only_sanitized_metadata() -> None:
    connection = _Connection()
    payload = run_schema_preflight(
        database_url="postgresql://redacted.invalid/neondb",
        expected_role="topicpilot_forensic_readonly",
        forensic_tool_sha="a" * 40,
        engine_factory=lambda *_args, **_kwargs: _Engine(connection),
    )

    assert payload["databaseName"] == "neondb"
    assert payload["databaseRole"] == "topicpilot_forensic_readonly"
    assert payload["transactionReadOnly"] == "on"
    assert payload["mutationPrivilegesPresent"] == "NO"
    assert payload["primaryFailureLayer"] == "UNKNOWN_PREFLIGHT_PASSED"
    assert all(
        payload[key]
        for key in ("runsSchemaMatch", "attemptsSchemaMatch", "checkpointsSchemaMatch")
    )
    assert all(not values for values in payload["missingColumns"].values())
    assert all(not values for values in payload["unexpectedRelevantColumns"].values())
    assert not any("FROM topicpilot.live_collector_" in sql for sql in connection.statements)
    assert not any(
        sql.lstrip().upper().startswith(
            (
                "INSERT",
                "UPDATE",
                "DELETE",
                "TRUNCATE",
                "CREATE",
                "ALTER",
                "DROP",
                "GRANT",
                "REVOKE",
            )
        )
        for sql in connection.statements
    )


def test_schema_preflight_fails_closed_on_role_mismatch() -> None:
    with pytest.raises(ForensicReadbackError, match="PRODUCTION_READONLY_ROLE_MISMATCH"):
        run_schema_preflight(
            database_url="postgresql://redacted.invalid/neondb",
            expected_role="topicpilot_forensic_readonly",
            forensic_tool_sha="a" * 40,
            engine_factory=lambda *_args, **_kwargs: _Engine(
                _Connection(current_user="wrong_role")
            ),
        )


def test_schema_preflight_workflow_is_separate_and_protected() -> None:
    workflow = (
        Path(__file__).parents[3]
        / ".github"
        / "workflows"
        / "production-forensic-schema-preflight.yml"
    )
    source = workflow.read_text(encoding="utf-8")
    assert "environment: production-readonly" in source
    assert "required_reviewers" in source
    assert "PRODUCTION_READONLY_SCHEMA_PREFLIGHT" in source
    assert "TOPICPILOT_PRODUCTION_READONLY_DATABASE_URL" in source
    assert "TOPICPILOT_PRODUCTION_READONLY_ROLE" in source
    assert "POST_CLOSE_RUN_READBACK" not in source
    assert "--run-id" not in source
    assert "psql" not in source.lower()


def test_preflight_query_constants_are_metadata_only() -> None:
    for statement in (PREFLIGHT_TABLE_QUERY, PREFLIGHT_COLUMN_QUERY, PRIVILEGE_QUERY):
        normalized = statement.lstrip().upper()
        assert normalized.startswith("SELECT")
        assert not any(
            normalized.startswith(keyword)
            for keyword in (
                "INSERT",
                "UPDATE",
                "DELETE",
                "TRUNCATE",
                "CREATE",
                "ALTER",
                "DROP",
                "GRANT",
                "REVOKE",
            )
        )
