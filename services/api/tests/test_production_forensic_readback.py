from __future__ import annotations

import re
from datetime import UTC, date, datetime

import pytest

from topicpilot_api.production_forensic_readback import (
    ATTEMPT_GROUP_QUERY,
    ATTEMPT_REPRESENTATIVE_QUERY,
    CHECKPOINT_QUERY,
    CURRENT_DAY_RUN_QUERY,
    ERROR_SUMMARY_QUERY,
    FORENSIC_COMMAND_POST_CLOSE_DATE_READBACK,
    FORENSIC_COMMAND_POST_CLOSE_RUN_READBACK,
    MARKET_SUMMARY_QUERY,
    PRIVILEGE_QUERY,
    PROVIDER_STATUS_SUMMARY_QUERY,
    RUN_QUERY,
    UNAVAILABLE_ATTEMPT_QUERY,
    ForensicReadbackError,
    _read_only_identity,
    _safe_attempt,
    _safe_checkpoint,
    _sanitize_text,
    select_date_bound_run,
    summarize_attempt_rows,
    validate_command,
    validate_forensic_sha,
    validate_run_id,
    validate_trading_date,
)


def test_only_the_fixed_command_is_allowed() -> None:
    assert validate_command(FORENSIC_COMMAND_POST_CLOSE_RUN_READBACK) == (
        FORENSIC_COMMAND_POST_CLOSE_RUN_READBACK
    )
    with pytest.raises(ForensicReadbackError, match="FORENSIC_COMMAND_NOT_ALLOWED"):
        validate_command("SELECT * FROM topicpilot.live_collector_runs")


def test_date_bound_command_accepts_only_canonical_trading_date() -> None:
    assert validate_command(FORENSIC_COMMAND_POST_CLOSE_DATE_READBACK) == (
        FORENSIC_COMMAND_POST_CLOSE_DATE_READBACK
    )
    assert validate_trading_date("2026-09-30") == date(2026, 9, 30)
    with pytest.raises(ForensicReadbackError, match="TRADING_DATE_MUST_BE_ISO_DATE"):
        validate_trading_date("2026-9-30")


def test_date_bound_selection_prefers_explicit_full_run() -> None:
    rows = [
        {
            "id": "legacy",
            "metadata_run_date": None,
            "metadata_scope": "FULL",
            "started_at": datetime(2026, 9, 30, 5, 0, tzinfo=UTC),
        },
        {
            "id": "natural",
            "metadata_run_date": "2026-09-30",
            "metadata_scope": "FULL",
            "started_at": datetime(2026, 9, 30, 5, 1, tzinfo=UTC),
        },
    ]
    selected, basis, candidates = select_date_bound_run(rows, date(2026, 9, 30))
    assert selected is rows[1]
    assert basis == "METADATA_RUN_DATE"
    assert len(candidates) == 2


def test_date_bound_selection_fails_closed_on_ambiguous_runs() -> None:
    rows = [
        {"id": "one", "metadata_run_date": "2026-09-30", "metadata_scope": "FULL"},
        {"id": "two", "metadata_run_date": "2026-09-30", "metadata_scope": "FULL"},
    ]
    with pytest.raises(ForensicReadbackError, match="POST_CLOSE_DATE_AMBIGUOUS"):
        select_date_bound_run(rows, date(2026, 9, 30))


@pytest.mark.parametrize(
    "value",
    ["", "abc", "uuid1,uuid2", "' OR 1=1 --", "*"],
)
def test_run_id_rejects_non_uuid_values(value: str) -> None:
    with pytest.raises(ForensicReadbackError, match="RUN_ID_MUST_BE_UUID"):
        validate_run_id(value)


def test_run_id_and_sha_accept_only_exact_forms() -> None:
    assert str(validate_run_id("30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a")) == (
        "30c4c3b1-5e3d-4402-9f96-5f6fb5ec0f9a"
    )
    assert validate_forensic_sha("A" * 40) == "a" * 40
    with pytest.raises(ForensicReadbackError, match="FORENSIC_TOOL_SHA"):
        validate_forensic_sha("main")


def test_error_text_is_bounded_and_secret_safe() -> None:
    value = "password=topsecret postgres://user:pass@example.invalid/db " + ("x" * 600)
    sanitized = _sanitize_text(value)
    assert sanitized is not None
    assert len(sanitized) == 512
    assert "topsecret" not in sanitized
    assert "postgres://user:pass@example.invalid/db" not in sanitized


def test_grouped_result_formation_is_deterministic() -> None:
    rows = [
        {
            "market_code": "TPE",
            "status": "FAILED",
            "provider_status": "ERROR",
            "error_code": "EXCHANGE_NO_DATA",
            "started_at": datetime(2026, 9, 29, 5, 0, tzinfo=UTC),
            "updated_at": datetime(2026, 9, 29, 5, 1, tzinfo=UTC),
        },
        {
            "market_code": "TPE",
            "status": "FAILED",
            "provider_status": "ERROR",
            "error_code": "EXCHANGE_NO_DATA",
            "started_at": datetime(2026, 9, 29, 5, 2, tzinfo=UTC),
            "updated_at": datetime(2026, 9, 29, 5, 3, tzinfo=UTC),
        },
        {
            "market_code": "TWO",
            "status": "SKIPPED",
            "provider_status": "NO_DATA",
            "error_code": None,
            "started_at": datetime(2026, 9, 29, 5, 4, tzinfo=UTC),
            "updated_at": datetime(2026, 9, 29, 5, 5, tzinfo=UTC),
        },
    ]
    assert summarize_attempt_rows(rows) == [
        {
            "marketCode": "TPE",
            "status": "FAILED",
            "providerStatus": "ERROR",
            "errorCode": "EXCHANGE_NO_DATA",
            "attemptCount": 2,
            "firstStartedAt": "2026-09-29T05:00:00+00:00",
            "lastRetrievedAt": "2026-09-29T05:03:00+00:00",
        },
        {
            "marketCode": "TWO",
            "status": "SKIPPED",
            "providerStatus": "NO_DATA",
            "errorCode": None,
            "attemptCount": 1,
            "firstStartedAt": "2026-09-29T05:04:00+00:00",
            "lastRetrievedAt": "2026-09-29T05:05:00+00:00",
        },
    ]


def test_output_sanitizes_attempt_and_checkpoint_details() -> None:
    attempt = _safe_attempt(
        {
            "instrument_code": "2330",
            "market_code": "TPE",
            "attempt_number": 1,
            "status": "FAILED",
            "error_code": "EXCHANGE_NO_DATA",
            "error_message": "token=secret-value",
        }
    )
    checkpoint = _safe_checkpoint(
        {
            "batch_number": 100,
            "batch_key": "FORMAL_MARKET_FACTS:TPE:1",
            "attempt_number": 1,
            "status": "FAILED",
            "metadata_reason": "safe operational reason",
            "metadata_secret": "must not be read",
        }
    )
    assert attempt["errorMessage"] == "[REDACTED]"
    assert checkpoint["metadata"] == {"metadata_reason": "safe operational reason"}


def test_checkpoint_provider_na_is_not_reported_as_zero_and_nested_failure_is_preserved():
    checkpoint = _safe_checkpoint(
        {
            "batch_number": 150,
            "batch_key": "FORMAL_MARKET_FACTS:OFFICIAL",
            "attempt_number": 1,
            "status": "FAILED",
            "provider_request_count": 0,
            "metadata_provider_metrics_applicable": "false",
            "metadata_provider_request_count": None,
            "metadata_checkpoint_semantics": "FORMAL_MARKET_FACTS_PUBLICATION",
            "metadata_failure_readback_status": "FAIL",
            "metadata_failure_reason_code": "FORMAL_MARKET_FACTS_PUBLICATION_NOT_READY",
            "metadata_failure_institutional_flow_status": "FAIL",
            "metadata_failure_market_facts_status": "UNAVAILABLE",
            "metadata_failure_failed_section": "FORMAL_MARKET_FACTS_PUBLICATION",
            "metadata_failure_classification": "PUBLICATION_CHECKPOINT",
        }
    )

    assert checkpoint["providerRequestCount"] is None
    assert checkpoint["metadata"]["metadata_checkpoint_semantics"] == (
        "FORMAL_MARKET_FACTS_PUBLICATION"
    )
    assert checkpoint["failureReason"] == {
        "readbackStatus": "FAIL",
        "reasonCode": "FORMAL_MARKET_FACTS_PUBLICATION_NOT_READY",
        "institutionalFlowStatus": "FAIL",
        "marketFactsPublicationStatus": "UNAVAILABLE",
        "failedSection": "FORMAL_MARKET_FACTS_PUBLICATION",
        "failureClassification": "PUBLICATION_CHECKPOINT",
    }


class _ScalarResult:
    def __init__(self, value: str) -> None:
        self.value = value

    def scalar_one(self) -> str:
        return self.value


class _MappingResult:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self.rows = rows

    def mappings(self) -> list[dict[str, str]]:
        return self.rows


class _ReadOnlyConnection:
    def __init__(self, read_only: str = "on") -> None:
        self.read_only = read_only
        self.statements: list[str] = []

    def execute(self, statement, parameters=None):
        sql = str(statement)
        self.statements.append(sql)
        if "SHOW transaction_read_only" in sql:
            return _ScalarResult(self.read_only)
        if "current_user AS current_user" in sql:
            return _MappingResult(
                [
                    {
                        "current_user": "topicpilot_forensic_readonly",
                        "session_user": "topicpilot_forensic_readonly",
                        "transaction_read_only": self.read_only,
                    }
                ]
            )
        return _MappingResult([])


def test_read_only_transaction_is_asserted_before_identity_use() -> None:
    connection = _ReadOnlyConnection()
    assert _read_only_identity(connection, "topicpilot_forensic_readonly") == (
        "topicpilot_forensic_readonly",
        "topicpilot_forensic_readonly",
        True,
    )
    assert "SET TRANSACTION READ ONLY" in connection.statements[0]
    assert "SHOW transaction_read_only" in connection.statements[1]


def test_writable_transaction_fails_closed() -> None:
    with pytest.raises(ForensicReadbackError, match="BLOCKED_READONLY_TRANSACTION_NOT_ENFORCED"):
        _read_only_identity(_ReadOnlyConnection("off"), "topicpilot_forensic_readonly")


def test_query_surface_has_no_mutation_statement() -> None:
    statements = (
        RUN_QUERY,
        CURRENT_DAY_RUN_QUERY,
        ATTEMPT_GROUP_QUERY,
        ATTEMPT_REPRESENTATIVE_QUERY,
        UNAVAILABLE_ATTEMPT_QUERY,
        CHECKPOINT_QUERY,
        MARKET_SUMMARY_QUERY,
        ERROR_SUMMARY_QUERY,
        PROVIDER_STATUS_SUMMARY_QUERY,
        PRIVILEGE_QUERY,
    )
    for statement in statements:
        assert re.match(r"^\s*SELECT\b", statement)
        assert not re.match(
            r"^\s*(INSERT|UPDATE|DELETE|MERGE|TRUNCATE|CREATE|ALTER|DROP|"
            r"GRANT|REVOKE|COPY|CALL)\b",
            statement,
        )
