from __future__ import annotations

from datetime import date

import pytest

from topicpilot_api.parity import (
    PARITY_FAIL,
    PARITY_PASS,
    ParityDailyRecord,
    ParityValidationError,
    build_parity_report,
)

HASH = "a" * 64


def _record(day: date, **overrides) -> ParityDailyRecord:
    values = {
        "trading_date": day,
        "source_data_date": day,
        "bundle_version": "enterprise.v1",
        "bundle_sha256": HASH,
        "source_snapshot_version": "private-2026-08-01",
        "source_snapshot_sha256": "b" * 64,
        "application_revision": "app-001",
        "migration_head": "0021_phase3_6_001b_import_audit",
        "parity_query_revision": "parity-query.v1",
        "target_environment_alias": "private-v2",
        "operator_id": "operator-private",
        "artifact_row_counts": {"stocks": 10, "topics": 3},
        "blocking_mismatch_count": 0,
        "null_mismatch_count": 0,
        "value_mismatch_count": 0,
        "replay_noop": True,
        "compatibility_pass": True,
        "error_quality_event_count": 0,
        "warning_quality_event_count": 1,
        "result": PARITY_PASS,
    }
    values.update(overrides)
    return ParityDailyRecord(**values)


def _ten_records(**overrides) -> tuple[ParityDailyRecord, ...]:
    dates = (
        date(2026, 8, 3),
        date(2026, 8, 4),
        date(2026, 8, 5),
        date(2026, 8, 6),
        date(2026, 8, 7),
        date(2026, 8, 10),
        date(2026, 8, 11),
        date(2026, 8, 12),
        date(2026, 8, 13),
        date(2026, 8, 14),
    )
    return tuple(_record(day, **overrides) for day in dates)


def test_ten_pass_records_produce_deterministic_sanitized_pass_report():
    records = _ten_records()
    first = build_parity_report(records).to_dict()
    second = build_parity_report(records).to_dict()

    assert first == second
    assert first["contractVersion"] == "private-parity.v1"
    assert first["status"] == PARITY_PASS
    assert first["dayCount"] == 10
    assert first["passedDayCount"] == 10
    assert first["consecutivePassCount"] == 10
    assert first["reasonCodes"] == []
    assert all("operatorId" not in day for day in first["days"])
    assert all("sourceRows" not in day and "discrepancy" not in day for day in first["days"])


def test_failed_day_yields_sanitized_fail_reason_without_raw_details():
    records = list(_ten_records())
    records[4] = _record(
        date(2026, 8, 7),
        blocking_mismatch_count=2,
        result=PARITY_FAIL,
    )

    report = build_parity_report(records).to_dict()

    assert report["status"] == PARITY_FAIL
    assert report["passedDayCount"] == 9
    assert report["reasonCodes"] == ["BLOCKING_MISMATCH"]
    assert report["days"][4]["reasonCodes"] == ["BLOCKING_MISMATCH"]
    assert "operator-private" not in str(report)


def test_null_and_value_mismatches_are_blocking_evidence():
    records = list(_ten_records())
    records[0] = _record(
        date(2026, 8, 3),
        null_mismatch_count=1,
        value_mismatch_count=2,
        result=PARITY_FAIL,
    )

    report = build_parity_report(records).to_dict()

    assert report["status"] == PARITY_FAIL
    assert report["reasonCodes"] == ["NULL_MISMATCH", "VALUE_MISMATCH"]
    assert report["days"][0]["reasonCodes"] == ["NULL_MISMATCH", "VALUE_MISMATCH"]


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("bundle_sha256", "not-a-hash", "INVALID_SHA256"),
        ("blocking_mismatch_count", -1, "INVALID_COUNT"),
        ("result", "UNKNOWN", "INVALID_RESULT"),
        ("source_data_date", date(2026, 8, 4), "DATE_MISMATCH"),
    ],
)
def test_malformed_daily_record_is_rejected(field, value, code):
    with pytest.raises(ParityValidationError, match=code):
        _record(date(2026, 8, 3), **{field: value})


def test_from_mapping_rejects_unknown_fields_and_preserves_strict_shape():
    record = _record(date(2026, 8, 3))
    payload = {
        "tradingDate": record.trading_date.isoformat(),
        "sourceDataDate": record.source_data_date.isoformat(),
        "bundleVersion": record.bundle_version,
        "bundleSha256": record.bundle_sha256,
        "sourceSnapshotVersion": record.source_snapshot_version,
        "sourceSnapshotSha256": record.source_snapshot_sha256,
        "applicationRevision": record.application_revision,
        "migrationHead": record.migration_head,
        "parityQueryRevision": record.parity_query_revision,
        "targetEnvironmentAlias": record.target_environment_alias,
        "operatorId": record.operator_id,
        "artifactRowCounts": dict(record.artifact_row_counts),
        "blockingMismatchCount": record.blocking_mismatch_count,
        "nullMismatchCount": record.null_mismatch_count,
        "valueMismatchCount": record.value_mismatch_count,
        "replayNoop": record.replay_noop,
        "compatibilityPass": record.compatibility_pass,
        "errorQualityEventCount": record.error_quality_event_count,
        "warningQualityEventCount": record.warning_quality_event_count,
        "result": record.result,
    }
    assert ParityDailyRecord.from_mapping(payload) == record
    payload["unexpected"] = True
    with pytest.raises(ParityValidationError, match="UNKNOWN_FIELD"):
        ParityDailyRecord.from_mapping(payload)


@pytest.mark.parametrize("count", [0, 1, 9, 11])
def test_sequence_requires_exactly_ten_records(count):
    records = list(_ten_records())
    if count < 10:
        records = records[:count]
    else:
        records.append(_record(date(2026, 8, 17)))
    with pytest.raises(ParityValidationError, match="TEN_DAYS_REQUIRED"):
        build_parity_report(records)


def test_sequence_rejects_duplicate_or_out_of_order_dates_without_calendar_assumptions():
    records = list(_ten_records())
    records[1] = _record(records[0].trading_date)
    with pytest.raises(ParityValidationError, match="DUPLICATE_DATE"):
        build_parity_report(records)

    records = list(_ten_records())
    records[1], records[2] = records[2], records[1]
    with pytest.raises(ParityValidationError, match="DATES_NOT_ORDERED"):
        build_parity_report(records)


def test_non_noop_replay_compatibility_failure_and_error_event_are_blocking():
    records = list(_ten_records())
    records[0] = _record(
        date(2026, 8, 3),
        replay_noop=False,
        compatibility_pass=False,
        error_quality_event_count=1,
        result=PARITY_FAIL,
    )

    report = build_parity_report(records).to_dict()

    assert report["status"] == PARITY_FAIL
    assert report["reasonCodes"] == [
        "COMPATIBILITY_FAILED",
        "ERROR_QUALITY_EVENTS",
        "REPLAY_NOT_NOOP",
    ]
