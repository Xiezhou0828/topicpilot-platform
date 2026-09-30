"""Governed, fixed-command, SELECT-only Production forensic readback."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, text

FORENSIC_COMMAND_POST_CLOSE_RUN_READBACK = "POST_CLOSE_RUN_READBACK"
FORENSIC_COMMAND_POST_CLOSE_DATE_READBACK = "POST_CLOSE_DATE_READBACK"
FORENSIC_COMMAND_SCHEMA_PREFLIGHT = "PRODUCTION_READONLY_SCHEMA_PREFLIGHT"
SUPPORTED_FORENSIC_COMMANDS = (
    FORENSIC_COMMAND_POST_CLOSE_RUN_READBACK,
    FORENSIC_COMMAND_POST_CLOSE_DATE_READBACK,
    FORENSIC_COMMAND_SCHEMA_PREFLIGHT,
)
TARGET_TABLE_SCOPE = (
    "topicpilot.live_collector_runs",
    "topicpilot.live_collector_attempts",
    "topicpilot.live_collector_checkpoints",
)
EXPECTED_PREFLIGHT_COLUMNS = {
    "live_collector_runs": frozenset(
        {
            "id",
            "run_type",
            "status",
            "provider_code",
            "adapter_version",
            "started_at",
            "heartbeat_at",
            "completed_at",
            "requested_count",
            "success_count",
            "failure_count",
            "retry_count",
            "latency_ms",
            "freshness_state",
            "provider_status",
            "failure_code",
            "failure_message",
        }
    ),
    "live_collector_attempts": frozenset(
        {
            "run_id",
            "instrument_code",
            "market_code",
            "attempt_number",
            "status",
            "started_at",
            "retrieved_at",
            "updated_at",
            "observed_at",
            "latency_ms",
            "retry_count",
            "provider_status",
            "freshness_state",
            "error_code",
            "error_message",
        }
    ),
    "live_collector_checkpoints": frozenset(
        {
            "run_id",
            "batch_number",
            "batch_key",
            "attempt_number",
            "status",
            "processed_count",
            "succeeded_count",
            "failed_count",
            "skipped_count",
            "retry_count",
            "provider_request_count",
            "provider_failure_count",
            "checkpoint_hash",
            "created_at",
            "metadata",
        }
    ),
}
PREFLIGHT_TABLE_NAMES = tuple(EXPECTED_PREFLIGHT_COLUMNS)
MAX_ATTEMPT_REPRESENTATIVES = 50
MAX_UNAVAILABLE_ATTEMPTS = 200
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SECRET_TEXT_PATTERNS = (
    re.compile(r"(?i)(postgres(?:ql)?(?:\+\w+)?://)[^\s,;]+"),
    re.compile(r"(?i)(authorization|cookie|password|secret|token|api[_-]?key)\s*[:=]\s*[^\s,;]+"),
)


class ForensicReadbackError(RuntimeError):
    """A fail-closed readback validation or execution error."""

    def __init__(self, code: str, message: str | None = None) -> None:
        self.code = code
        super().__init__(message or code)


def validate_command(value: str) -> str:
    """Validate the fixed forensic command allowlist."""

    if value not in SUPPORTED_FORENSIC_COMMANDS:
        raise ForensicReadbackError("FORENSIC_COMMAND_NOT_ALLOWED")
    return value


def validate_run_id(value: str) -> UUID:
    """Validate one canonical hyphenated UUID and reject SQL-like input."""

    if not isinstance(value, str) or not UUID_PATTERN.fullmatch(value):
        raise ForensicReadbackError("RUN_ID_MUST_BE_UUID")
    try:
        return UUID(value)
    except ValueError as exc:
        raise ForensicReadbackError("RUN_ID_MUST_BE_UUID") from exc


def validate_forensic_sha(value: str) -> str:
    """Validate the exact 40-character tool revision used by the workflow."""

    if not isinstance(value, str) or not SHA_PATTERN.fullmatch(value):
        raise ForensicReadbackError("FORENSIC_TOOL_SHA_MUST_BE_EXACT_40_HEX")
    return value.lower()


def validate_trading_date(value: str) -> date:
    """Validate one canonical ISO trading date for date-bound readback."""

    if not isinstance(value, str) or not ISO_DATE_PATTERN.fullmatch(value):
        raise ForensicReadbackError("TRADING_DATE_MUST_BE_ISO_DATE")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ForensicReadbackError("TRADING_DATE_MUST_BE_ISO_DATE") from exc
    if parsed.isoformat() != value:
        raise ForensicReadbackError("TRADING_DATE_MUST_BE_ISO_DATE")
    return parsed


def _sanitize_text(value: Any, *, limit: int = 512) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).split())
    for pattern in _SECRET_TEXT_PATTERNS:
        normalized = pattern.sub("[REDACTED]", normalized)
    return normalized[:limit]


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _sanitize_text(value)


def _row_mapping(row: Any) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    return dict(row)


def _execute_mappings(
    connection: Any,
    statement: str,
    parameters: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    result = connection.execute(text(statement), dict(parameters or {}))
    if hasattr(result, "mappings"):
        return [dict(row) for row in result.mappings()]
    return [_row_mapping(row) for row in result]


def _as_iso(value: Any) -> str | None:
    normalized = _json_value(value)
    return normalized if isinstance(normalized, str) else None


def _safe_run(row: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "id",
        "run_type",
        "status",
        "provider_code",
        "adapter_version",
        "started_at",
        "heartbeat_at",
        "completed_at",
        "requested_count",
        "success_count",
        "failure_count",
        "retry_count",
        "latency_ms",
        "freshness_state",
        "provider_status",
        "failure_code",
    )
    result = {field: _json_value(row.get(field)) for field in fields}
    result["failure_message"] = _sanitize_text(row.get("failure_message"))
    for field in ("started_at", "heartbeat_at", "completed_at"):
        result[field] = _as_iso(row.get(field))
    return result


def _metadata_field(row: Mapping[str, Any], field: str) -> Any:
    direct = row.get(f"metadata_{field}")
    if direct is not None:
        return direct
    raw = row.get("metadata_text")
    if not isinstance(raw, str):
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return None
    json_key = {
        "run_date": "runDate",
        "target_date": "targetDate",
        "execution_mode": "executionMode",
        "session_code": "sessionCode",
        "calendar_code": "calendarCode",
    }.get(field, field)
    return parsed.get(json_key) if isinstance(parsed, dict) else None


def _safe_date_candidate(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": _json_value(row.get("id")),
        "runType": _sanitize_text(row.get("run_type"), limit=32),
        "status": _sanitize_text(row.get("status"), limit=32),
        "startedAt": _as_iso(row.get("started_at")),
        "completedAt": _as_iso(row.get("completed_at")),
        "runDate": _sanitize_text(_metadata_field(row, "run_date"), limit=32),
        "targetDate": _sanitize_text(_metadata_field(row, "target_date"), limit=32),
        "scope": _sanitize_text(_metadata_field(row, "scope"), limit=32),
        "executionMode": _sanitize_text(_metadata_field(row, "execution_mode"), limit=32),
        "timezone": _sanitize_text(_metadata_field(row, "timezone"), limit=64),
        "sessionCode": _sanitize_text(_metadata_field(row, "session_code"), limit=64),
        "calendarCode": _sanitize_text(_metadata_field(row, "calendar_code"), limit=64),
    }


def select_date_bound_run(
    rows: Sequence[Mapping[str, Any]], trading_date: date
) -> tuple[Mapping[str, Any] | None, str, list[dict[str, Any]]]:
    """Select one natural full POST_CLOSE row, failing closed on ambiguity."""

    safe_candidates = [_safe_date_candidate(row) for row in rows]
    explicit = [
        row
        for row in rows
        if str(_metadata_field(row, "run_date") or "") == trading_date.isoformat()
    ]
    candidates = explicit or list(rows)
    full_scope = [
        row
        for row in candidates
        if str(_metadata_field(row, "scope") or "FULL").upper() == "FULL"
    ]
    preferred = full_scope or candidates
    if len(preferred) > 1:
        raise ForensicReadbackError("POST_CLOSE_DATE_AMBIGUOUS")
    if not preferred:
        return None, "NOT_FOUND", safe_candidates
    basis = "METADATA_RUN_DATE" if explicit else "STARTED_AT_ASIA_TAIPEI_DATE"
    return preferred[0], basis, safe_candidates


def _safe_attempt_group(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "marketCode": _sanitize_text(row.get("market_code"), limit=64),
        "status": _sanitize_text(row.get("status"), limit=32),
        "providerStatus": _sanitize_text(row.get("provider_status"), limit=64),
        "errorCode": _sanitize_text(row.get("error_code"), limit=128),
        "attemptCount": int(row.get("attempt_count", 0) or 0),
        "firstStartedAt": _as_iso(row.get("first_started_at")),
        "lastRetrievedAt": _as_iso(row.get("last_retrieved_at")),
    }


def _safe_attempt(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "instrumentCode": _sanitize_text(row.get("instrument_code"), limit=64),
        "marketCode": _sanitize_text(row.get("market_code"), limit=64),
        "attemptNumber": int(row.get("attempt_number", 0) or 0),
        "status": _sanitize_text(row.get("status"), limit=32),
        "startedAt": _as_iso(row.get("started_at")),
        "retrievedAt": _as_iso(row.get("retrieved_at")),
        "observedAt": _as_iso(row.get("observed_at")),
        "latencyMs": row.get("latency_ms"),
        "retryCount": int(row.get("retry_count", 0) or 0),
        "providerStatus": _sanitize_text(row.get("provider_status"), limit=64),
        "freshnessState": _sanitize_text(row.get("freshness_state"), limit=64),
        "errorCode": _sanitize_text(row.get("error_code"), limit=128),
        "errorMessage": _sanitize_text(row.get("error_message")),
    }


def _safe_checkpoint(row: Mapping[str, Any]) -> dict[str, Any]:
    publication_readback = {
        key: _sanitize_text(row.get(key), limit=64)
        for key in (
            "metadata_formal_publication_status",
            "metadata_formal_topic_status",
            "metadata_formal_topic_date",
            "metadata_home_publication_status",
            "metadata_home_publication_state",
            "metadata_formal_readback_status",
            "metadata_formal_readback_topic_status",
            "metadata_formal_readback_topic_date",
            "metadata_formal_readback_home_status",
            "metadata_formal_readback_home_state",
        )
        if row.get(key) is not None
    }
    return {
        "batchNumber": int(row.get("batch_number", 0) or 0),
        "batchKey": _sanitize_text(row.get("batch_key"), limit=128),
        "attemptNumber": int(row.get("attempt_number", 0) or 0),
        "status": _sanitize_text(row.get("status"), limit=32),
        "processedCount": int(row.get("processed_count", 0) or 0),
        "succeededCount": int(row.get("succeeded_count", 0) or 0),
        "failedCount": int(row.get("failed_count", 0) or 0),
        "skippedCount": int(row.get("skipped_count", 0) or 0),
        "retryCount": int(row.get("retry_count", 0) or 0),
        "providerRequestCount": int(row.get("provider_request_count", 0) or 0),
        "providerFailureCount": int(row.get("provider_failure_count", 0) or 0),
        "checkpointHash": _sanitize_text(row.get("checkpoint_hash"), limit=128),
        "createdAt": _as_iso(row.get("created_at")),
        "metadata": {
            key: _sanitize_text(row.get(key))
            for key in (
                "metadata_market",
                "metadata_session_date",
                "metadata_outcome",
                "metadata_reason",
                "metadata_publication",
                "metadata_run_status",
                "metadata_formal_readback",
                "metadata_scope",
            )
            if row.get(key) is not None
        },
        "publicationReadback": publication_readback,
    }


def _safe_distribution(row: Mapping[str, Any], *, key: str) -> dict[str, Any]:
    return {
        key: _sanitize_text(row.get(key), limit=128) or "NONE",
        "count": int(row.get("count", 0) or 0),
    }


def summarize_attempt_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Build deterministic grouped attempt evidence for unit-testable input rows."""

    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        key = (
            row.get("market_code"),
            row.get("status"),
            row.get("provider_status"),
            row.get("error_code"),
        )
        group = groups.setdefault(
            key,
            {
                "market_code": key[0],
                "status": key[1],
                "provider_status": key[2],
                "error_code": key[3],
                "attempt_count": 0,
                "first_started_at": None,
                "last_retrieved_at": None,
            },
        )
        group["attempt_count"] += 1
        started = row.get("started_at")
        retrieved = row.get("retrieved_at") or row.get("updated_at")
        if group["first_started_at"] is None or (
            started is not None and started < group["first_started_at"]
        ):
            group["first_started_at"] = started
        if group["last_retrieved_at"] is None or (
            retrieved is not None and retrieved > group["last_retrieved_at"]
        ):
            group["last_retrieved_at"] = retrieved
    return [
        _safe_attempt_group(groups[key])
        for key in sorted(groups, key=lambda item: tuple(str(v) for v in item))
    ]


def _privilege_status(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    privileges: list[dict[str, Any]] = []
    mutation_present = False
    for row in rows:
        item = {
            "table": _sanitize_text(row.get("table_name"), limit=128),
            "select": bool(row.get("select_allowed")),
            "insert": bool(row.get("insert_allowed")),
            "update": bool(row.get("update_allowed")),
            "delete": bool(row.get("delete_allowed")),
            "truncate": bool(row.get("truncate_allowed")),
        }
        mutation_present = mutation_present or any(
            item[field] for field in ("insert", "update", "delete", "truncate")
        )
        privileges.append(item)
    return privileges, "YES" if mutation_present else "NO"


RUN_QUERY = """
SELECT id, run_type, status, provider_code, adapter_version,
       started_at, heartbeat_at, completed_at, requested_count,
       success_count, failure_count, retry_count, latency_ms,
       freshness_state, provider_status, failure_code, failure_message
FROM topicpilot.live_collector_runs
WHERE id = :run_id
  AND run_type = 'POST_CLOSE'
"""

CURRENT_DAY_RUN_QUERY = """
SELECT id, run_type, status, provider_code, adapter_version,
       started_at, completed_at,
       CAST(metadata AS TEXT) AS metadata_text
FROM topicpilot.live_collector_runs
WHERE run_type = 'POST_CLOSE'
  AND started_at >= :local_start
  AND started_at < :local_end
ORDER BY
    started_at DESC,
    id DESC
"""

ATTEMPT_GROUP_QUERY = """
SELECT market_code, status, provider_status, error_code,
       COUNT(*) AS attempt_count,
       MIN(started_at) AS first_started_at,
       MAX(COALESCE(retrieved_at, updated_at)) AS last_retrieved_at
FROM topicpilot.live_collector_attempts
WHERE run_id = :run_id
GROUP BY market_code, status, provider_status, error_code
ORDER BY market_code, status, provider_status, error_code
"""

ATTEMPT_REPRESENTATIVE_QUERY = """
SELECT instrument_code, market_code, attempt_number, status,
       started_at, retrieved_at, observed_at, latency_ms, retry_count,
       provider_status, freshness_state, error_code, error_message
FROM topicpilot.live_collector_attempts
WHERE run_id = :run_id
ORDER BY started_at, market_code, instrument_code, attempt_number
LIMIT 50
"""

UNAVAILABLE_ATTEMPT_QUERY = """
SELECT instrument_code, market_code, attempt_number, status,
       started_at, retrieved_at, observed_at, latency_ms, retry_count,
       provider_status, freshness_state, error_code, error_message
FROM topicpilot.live_collector_attempts
WHERE run_id = :run_id
  AND status = 'SKIPPED'
ORDER BY started_at, market_code, instrument_code, attempt_number
LIMIT 200
"""

CHECKPOINT_QUERY = """
SELECT batch_number, batch_key, attempt_number, status,
       processed_count, succeeded_count, failed_count, skipped_count,
       retry_count, provider_request_count, provider_failure_count,
       checkpoint_hash, created_at,
       metadata->>'market' AS metadata_market,
       metadata->>'sessionDate' AS metadata_session_date,
       metadata->>'outcome' AS metadata_outcome,
       metadata->>'reason' AS metadata_reason,
       metadata->>'publication' AS metadata_publication,
       metadata->>'runStatus' AS metadata_run_status,
       metadata->>'formalReadback' AS metadata_formal_readback,
       metadata->>'scope' AS metadata_scope,
       metadata->'formalPublication'->>'status' AS metadata_formal_publication_status,
       metadata->'formalPublication'->'topicSnapshot'->>'status'
           AS metadata_formal_topic_status,
       metadata->'formalPublication'->'topicSnapshot'->>'tradingDate'
           AS metadata_formal_topic_date,
       metadata->'formalPublication'->'homePublication'->>'status'
           AS metadata_home_publication_status,
       metadata->'formalPublication'->'homePublication'->>'publicationState'
           AS metadata_home_publication_state,
       metadata->'formalReadback'->>'status' AS metadata_formal_readback_status,
       metadata->'formalReadback'->'topicSnapshot'->>'status'
           AS metadata_formal_readback_topic_status,
       metadata->'formalReadback'->'topicSnapshot'->>'tradingDate'
           AS metadata_formal_readback_topic_date,
       metadata->'formalReadback'->'homePublication'->>'status'
           AS metadata_formal_readback_home_status,
       metadata->'formalReadback'->'homePublication'->>'publicationState'
           AS metadata_formal_readback_home_state
FROM topicpilot.live_collector_checkpoints
WHERE run_id = :run_id
ORDER BY created_at, batch_number, attempt_number
"""

MARKET_SUMMARY_QUERY = """
SELECT market_code,
       COUNT(*) AS attempt_count,
       COUNT(*) FILTER (WHERE status = 'SUCCESS') AS success_count,
       COUNT(*) FILTER (WHERE status = 'FAILED') AS failure_count,
       COUNT(*) FILTER (WHERE status = 'SKIPPED') AS skipped_count,
       COUNT(*) FILTER (WHERE status = 'TIMEOUT') AS timeout_count,
       COUNT(DISTINCT instrument_code) AS instrument_count,
       MIN(started_at) AS first_started_at,
       MAX(COALESCE(retrieved_at, updated_at)) AS last_retrieved_at
FROM topicpilot.live_collector_attempts
WHERE run_id = :run_id
GROUP BY market_code
ORDER BY market_code
"""

ERROR_SUMMARY_QUERY = """
SELECT COALESCE(error_code, 'NONE') AS error_code, COUNT(*) AS count
FROM topicpilot.live_collector_attempts
WHERE run_id = :run_id
GROUP BY COALESCE(error_code, 'NONE')
ORDER BY error_code
"""

PROVIDER_STATUS_SUMMARY_QUERY = """
SELECT COALESCE(provider_status, 'NONE') AS provider_status, COUNT(*) AS count
FROM topicpilot.live_collector_attempts
WHERE run_id = :run_id
GROUP BY COALESCE(provider_status, 'NONE')
ORDER BY provider_status
"""

PRIVILEGE_QUERY = """
SELECT table_name,
       has_table_privilege(
           current_user, format('%I.%I', 'topicpilot', table_name), 'SELECT'
       ) AS select_allowed,
       has_table_privilege(
           current_user, format('%I.%I', 'topicpilot', table_name), 'INSERT'
       ) AS insert_allowed,
       has_table_privilege(
           current_user, format('%I.%I', 'topicpilot', table_name), 'UPDATE'
       ) AS update_allowed,
       has_table_privilege(
           current_user, format('%I.%I', 'topicpilot', table_name), 'DELETE'
       ) AS delete_allowed,
       has_table_privilege(
           current_user, format('%I.%I', 'topicpilot', table_name), 'TRUNCATE'
       ) AS truncate_allowed
FROM unnest(
    ARRAY['live_collector_runs', 'live_collector_attempts', 'live_collector_checkpoints']
) AS scoped(table_name)
ORDER BY table_name
"""

PREFLIGHT_TABLE_QUERY = """
SELECT table_name,
       EXISTS (
           SELECT 1
           FROM information_schema.tables AS tables
           WHERE tables.table_schema = 'topicpilot'
             AND tables.table_name = scoped.table_name
       ) AS table_exists
FROM unnest(
    ARRAY['live_collector_runs', 'live_collector_attempts',
          'live_collector_checkpoints']
) AS scoped(table_name)
ORDER BY table_name
"""

PREFLIGHT_COLUMN_QUERY = """
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'topicpilot'
  AND table_name IN (
      'live_collector_runs',
      'live_collector_attempts',
      'live_collector_checkpoints'
  )
ORDER BY table_name, ordinal_position
"""


def _read_only_identity(connection: Any, expected_role: str) -> tuple[str, str, bool]:
    connection.execute(text("SET TRANSACTION READ ONLY"))
    read_only_value = str(
        connection.execute(text("SHOW transaction_read_only")).scalar_one()
    ).lower()
    transaction_read_only = read_only_value in {"on", "true", "1"}
    if not transaction_read_only:
        raise ForensicReadbackError("BLOCKED_READONLY_TRANSACTION_NOT_ENFORCED")
    identity_rows = _execute_mappings(
        connection,
        """
        SELECT current_user AS current_user,
               session_user AS session_user,
               current_setting('transaction_read_only') AS transaction_read_only
        """,
    )
    if not identity_rows:
        raise ForensicReadbackError("DATABASE_IDENTITY_UNAVAILABLE")
    identity = identity_rows[0]
    current_user = str(identity.get("current_user") or "")
    session_user = str(identity.get("session_user") or "")
    if current_user != expected_role:
        raise ForensicReadbackError("PRODUCTION_READONLY_ROLE_MISMATCH")
    if str(identity.get("transaction_read_only", "")).lower() not in {"on", "true", "1"}:
        raise ForensicReadbackError("BLOCKED_READONLY_TRANSACTION_NOT_ENFORCED")
    return current_user, session_user, True


def _connection_failure_class(exc: Exception) -> str:
    """Classify only the connection layer without exposing driver details."""

    message = str(exc).lower()
    if "password authentication failed" in message or "authentication" in message:
        return "AUTHENTICATION_FAILED"
    if "ssl" in message or "certificate" in message:
        return "SSL_FAILED"
    if (
        "could not translate host name" in message
        or "name or service not known" in message
        or "nodename nor servname" in message
        or "temporary failure in name resolution" in message
    ):
        return "DNS_FAILED"
    if "invalid dsn" in message or "malformed" in message or "no such file" in message:
        return "CONNECTION_FAILED"
    return "OTHER_CONNECTION_FAILED"


def _preflight_schema_inventory(column_rows: Sequence[Mapping[str, Any]]) -> tuple[
    dict[str, list[dict[str, str | None]]],
    dict[str, list[str]],
    dict[str, list[str]],
]:
    inventory = {table: [] for table in PREFLIGHT_TABLE_NAMES}
    actual_columns = {table: set() for table in PREFLIGHT_TABLE_NAMES}
    for row in column_rows:
        table_name = str(row.get("table_name") or "")
        column_name = str(row.get("column_name") or "")
        if table_name not in inventory or not column_name:
            continue
        actual_columns[table_name].add(column_name)
        inventory[table_name].append(
            {
                "columnName": column_name,
                "dataType": _sanitize_text(row.get("data_type"), limit=128),
                "isNullable": _sanitize_text(row.get("is_nullable"), limit=16),
            }
        )
    missing = {
        table: sorted(EXPECTED_PREFLIGHT_COLUMNS[table] - actual_columns[table])
        for table in PREFLIGHT_TABLE_NAMES
    }
    unexpected = {
        table: sorted(actual_columns[table] - EXPECTED_PREFLIGHT_COLUMNS[table])
        for table in PREFLIGHT_TABLE_NAMES
    }
    return inventory, missing, unexpected


def run_schema_preflight(
    *,
    database_url: str,
    expected_role: str,
    forensic_tool_sha: str,
    engine_factory: Callable[..., Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run only the fixed connection, schema, and privilege preflight."""

    if not database_url:
        raise ForensicReadbackError("CONNECTION_URL_INVALID")
    if not expected_role:
        raise ForensicReadbackError("PRODUCTION_READONLY_ROLE_EXPECTATION_MISSING")
    tool_sha = validate_forensic_sha(forensic_tool_sha)
    engine = None
    try:
        engine = (engine_factory or create_engine)(database_url, pool_pre_ping=True)
        with engine.connect() as connection, connection.begin():
            connection.execute(text("SET TRANSACTION READ ONLY"))
            transaction_read_only = str(
                connection.execute(text("SHOW transaction_read_only")).scalar_one()
            ).lower()
            if transaction_read_only not in {"on", "true", "1"}:
                raise ForensicReadbackError("READONLY_TRANSACTION_FAILURE")
            identity_rows = _execute_mappings(
                connection,
                """
                SELECT current_database() AS database_name,
                       current_user AS current_user,
                       session_user AS session_user
                """,
            )
            if not identity_rows:
                raise ForensicReadbackError("DATABASE_IDENTITY_UNAVAILABLE")
            identity = identity_rows[0]
            database_name = _sanitize_text(identity.get("database_name"), limit=128)
            current_user = _sanitize_text(identity.get("current_user"), limit=128)
            session_user = _sanitize_text(identity.get("session_user"), limit=128)
            if current_user != expected_role:
                raise ForensicReadbackError("PRODUCTION_READONLY_ROLE_MISMATCH")

            table_rows = _execute_mappings(connection, PREFLIGHT_TABLE_QUERY)
            table_exists = {
                str(row.get("table_name")): bool(row.get("table_exists"))
                for row in table_rows
                if str(row.get("table_name")) in PREFLIGHT_TABLE_NAMES
            }
            if not all(table_exists.get(table, False) for table in PREFLIGHT_TABLE_NAMES):
                raise ForensicReadbackError("TARGET_TABLE_MISSING")

            column_rows = _execute_mappings(connection, PREFLIGHT_COLUMN_QUERY)
            inventory, missing, unexpected = _preflight_schema_inventory(column_rows)
            if any(missing.values()):
                raise ForensicReadbackError("TARGET_COLUMN_SCHEMA_MISMATCH")

            privilege_rows = _execute_mappings(connection, PRIVILEGE_QUERY)
            privileges, mutation_status = _privilege_status(privilege_rows)
            if any(not item["select"] for item in privileges):
                raise ForensicReadbackError("TARGET_SELECT_PRIVILEGE_MISSING")
            if mutation_status != "NO":
                raise ForensicReadbackError("MUTATION_PRIVILEGES_PRESENT")
    except ForensicReadbackError:
        raise
    except Exception as exc:
        raise ForensicReadbackError(_connection_failure_class(exc)) from exc
    finally:
        if engine is not None:
            engine.dispose()

    generated_at = now or datetime.now(UTC)
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=UTC)
    return {
        "forensicToolSha": tool_sha,
        "databaseName": database_name,
        "databaseRole": current_user,
        "sessionUser": session_user,
        "transactionReadOnly": transaction_read_only,
        "tableExistence": table_exists,
        "columnInventory": inventory,
        "runsSchemaMatch": not missing["live_collector_runs"],
        "attemptsSchemaMatch": not missing["live_collector_attempts"],
        "checkpointsSchemaMatch": not missing["live_collector_checkpoints"],
        "missingColumns": missing,
        "unexpectedRelevantColumns": unexpected,
        "targetPrivileges": privileges,
        "mutationPrivilegesPresent": mutation_status,
        "primaryFailureLayer": "UNKNOWN_PREFLIGHT_PASSED",
        "generatedAt": generated_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
    }


def read_post_close_run(
    *,
    database_url: str,
    run_id: str,
    expected_role: str,
    forensic_tool_sha: str,
    engine_factory: Callable[..., Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Read one POST_CLOSE run through the fixed, bounded forensic surface."""

    if not database_url:
        raise ForensicReadbackError("BLOCKED_PRODUCTION_READONLY_SECRET_MISSING")
    if not expected_role:
        raise ForensicReadbackError("PRODUCTION_READONLY_ROLE_EXPECTATION_MISSING")
    run_uuid = validate_run_id(run_id)
    tool_sha = validate_forensic_sha(forensic_tool_sha)
    engine = (engine_factory or create_engine)(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection, connection.begin():
            current_user, session_user, transaction_read_only = _read_only_identity(
                connection, expected_role
            )
            run_rows = _execute_mappings(connection, RUN_QUERY, {"run_id": run_uuid})
            if not run_rows:
                raise ForensicReadbackError("POST_CLOSE_RUN_NOT_FOUND")
            run = run_rows[0]
            attempt_groups = _execute_mappings(
                connection, ATTEMPT_GROUP_QUERY, {"run_id": run_uuid}
            )
            representatives = _execute_mappings(
                connection, ATTEMPT_REPRESENTATIVE_QUERY, {"run_id": run_uuid}
            )
            unavailable_attempts = _execute_mappings(
                connection, UNAVAILABLE_ATTEMPT_QUERY, {"run_id": run_uuid}
            )
            checkpoints = _execute_mappings(connection, CHECKPOINT_QUERY, {"run_id": run_uuid})
            market_rows = _execute_mappings(connection, MARKET_SUMMARY_QUERY, {"run_id": run_uuid})
            error_rows = _execute_mappings(connection, ERROR_SUMMARY_QUERY, {"run_id": run_uuid})
            provider_rows = _execute_mappings(
                connection, PROVIDER_STATUS_SUMMARY_QUERY, {"run_id": run_uuid}
            )
            privilege_rows = _execute_mappings(connection, PRIVILEGE_QUERY)
            privileges, mutation_status = _privilege_status(privilege_rows)

    except ForensicReadbackError:
        raise
    except Exception as exc:
        raise ForensicReadbackError("FORENSIC_QUERY_FAILED", type(exc).__name__) from exc
    finally:
        engine.dispose()

    safe_checkpoints = [_safe_checkpoint(row) for row in checkpoints]
    failed_checkpoints = [row for row in safe_checkpoints if row["status"] == "FAILED"]
    safe_market = []
    for row in market_rows:
        safe_market.append(
            {
                "marketCode": _sanitize_text(row.get("market_code"), limit=64),
                "attemptCount": int(row.get("attempt_count", 0) or 0),
                "successCount": int(row.get("success_count", 0) or 0),
                "failureCount": int(row.get("failure_count", 0) or 0),
                "skippedCount": int(row.get("skipped_count", 0) or 0),
                "timeoutCount": int(row.get("timeout_count", 0) or 0),
                "instrumentCount": int(row.get("instrument_count", 0) or 0),
                "firstStartedAt": _as_iso(row.get("first_started_at")),
                "lastRetrievedAt": _as_iso(row.get("last_retrieved_at")),
            }
        )
    generated_at = now or datetime.now(UTC)
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=UTC)
    return {
        "forensicToolSha": tool_sha,
        "databaseRole": current_user,
        "sessionUser": session_user,
        "transactionReadOnly": transaction_read_only,
        "targetTableScope": list(TARGET_TABLE_SCOPE),
        "targetPrivileges": privileges,
        "mutationPrivilegesPresent": mutation_status,
        "run": _safe_run(run),
        "attemptSummary": [_safe_attempt_group(row) for row in attempt_groups],
        "attemptRepresentatives": [
            _safe_attempt(row) for row in representatives[:MAX_ATTEMPT_REPRESENTATIVES]
        ],
        "unavailableAttempts": [
            _safe_attempt(row) for row in unavailable_attempts[:MAX_UNAVAILABLE_ATTEMPTS]
        ],
        "checkpointTimeline": safe_checkpoints,
        "firstFailedCheckpoint": failed_checkpoints[0] if failed_checkpoints else None,
        "marketSummary": safe_market,
        "errorSummary": [_safe_distribution(row, key="error_code") for row in error_rows],
        "providerStatusSummary": [
            _safe_distribution(row, key="provider_status") for row in provider_rows
        ],
        "generatedAt": generated_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
    }


def read_post_close_date(
    *,
    database_url: str,
    trading_date: str,
    expected_role: str,
    forensic_tool_sha: str,
    engine_factory: Callable[..., Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Locate and read one natural POST_CLOSE run for an exact trading date."""

    if not database_url:
        raise ForensicReadbackError("BLOCKED_PRODUCTION_READONLY_SECRET_MISSING")
    if not expected_role:
        raise ForensicReadbackError("PRODUCTION_READONLY_ROLE_EXPECTATION_MISSING")
    parsed_date = validate_trading_date(trading_date)
    tool_sha = validate_forensic_sha(forensic_tool_sha)
    timezone = ZoneInfo("Asia/Taipei")
    local_start = datetime.combine(parsed_date, time.min, tzinfo=timezone).astimezone(UTC)
    local_end = local_start + timedelta(days=1)
    engine = (engine_factory or create_engine)(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection, connection.begin():
            current_user, session_user, transaction_read_only = _read_only_identity(
                connection, expected_role
            )
            try:
                candidate_rows = _execute_mappings(
                    connection,
                    CURRENT_DAY_RUN_QUERY,
                    {"local_start": local_start, "local_end": local_end},
                )
            except Exception as exc:
                raise ForensicReadbackError("CURRENT_DAY_RUN_LOCATOR_QUERY_FAILED") from exc
            try:
                privilege_rows = _execute_mappings(connection, PRIVILEGE_QUERY)
            except Exception as exc:
                raise ForensicReadbackError("CURRENT_DAY_PRIVILEGE_READBACK_FAILED") from exc
            privileges, mutation_status = _privilege_status(privilege_rows)
            selected, selection_basis, safe_candidates = select_date_bound_run(
                candidate_rows, parsed_date
            )
    except ForensicReadbackError:
        raise
    except Exception as exc:
        raise ForensicReadbackError("FORENSIC_QUERY_FAILED", type(exc).__name__) from exc
    finally:
        engine.dispose()

    if selected is None:
        generated_at = now or datetime.now(UTC)
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=UTC)
        return {
            "forensicToolSha": tool_sha,
            "databaseRole": current_user,
            "sessionUser": session_user,
            "transactionReadOnly": transaction_read_only,
            "targetTableScope": list(TARGET_TABLE_SCOPE),
            "targetPrivileges": privileges,
            "mutationPrivilegesPresent": mutation_status,
            "requestedTradingDate": parsed_date.isoformat(),
            "postCloseRunFound": False,
            "runSelection": {
                "selectionBasis": selection_basis,
                "candidateCount": len(safe_candidates),
                "candidates": safe_candidates,
                "selectedCandidate": None,
            },
            "run": None,
            "attemptSummary": [],
            "attemptRepresentatives": [],
            "checkpointTimeline": [],
            "firstFailedCheckpoint": None,
            "marketSummary": [],
            "errorSummary": [],
            "providerStatusSummary": [],
            "generatedAt": generated_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        }

    payload = read_post_close_run(
        database_url=database_url,
        run_id=str(selected["id"]),
        expected_role=expected_role,
        forensic_tool_sha=tool_sha,
        engine_factory=engine_factory,
        now=now,
    )
    payload["requestedTradingDate"] = parsed_date.isoformat()
    payload["postCloseRunFound"] = True
    payload["runSelection"] = {
        "selectionBasis": selection_basis,
        "candidateCount": len(safe_candidates),
        "candidates": safe_candidates,
        "selectedCandidate": _safe_date_candidate(selected),
    }
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", choices=SUPPORTED_FORENSIC_COMMANDS, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--trading-date")
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        validate_command(args.command)
        database_url = os.environ.get("TOPICPILOT_PRODUCTION_READONLY_DATABASE_URL", "")
        expected_role = os.environ.get("TOPICPILOT_PRODUCTION_READONLY_ROLE", "")
        forensic_tool_sha = os.environ.get("TOPICPILOT_FORENSIC_TOOL_SHA", "")
        if args.command == FORENSIC_COMMAND_SCHEMA_PREFLIGHT:
            payload = run_schema_preflight(
                database_url=database_url,
                expected_role=expected_role,
                forensic_tool_sha=forensic_tool_sha,
            )
        elif args.command == FORENSIC_COMMAND_POST_CLOSE_DATE_READBACK:
            if not args.trading_date:
                raise ForensicReadbackError("TRADING_DATE_REQUIRED")
            payload = read_post_close_date(
                database_url=database_url,
                trading_date=args.trading_date,
                expected_role=expected_role,
                forensic_tool_sha=forensic_tool_sha,
            )
        else:
            if not args.run_id:
                raise ForensicReadbackError("RUN_ID_REQUIRED")
            payload = read_post_close_run(
                database_url=database_url,
                run_id=args.run_id,
                expected_role=expected_role,
                forensic_tool_sha=forensic_tool_sha,
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "command": args.command,
                    "runId": (payload.get("run") or {}).get("id"),
                    "output": str(args.output),
                    "databaseRole": payload["databaseRole"],
                    "transactionReadOnly": payload["transactionReadOnly"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except ForensicReadbackError as exc:
        print(json.dumps({"status": "BLOCKED", "code": exc.code}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
