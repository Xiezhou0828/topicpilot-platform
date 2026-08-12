"""Sanitized, deterministic evidence checks for the V1-to-V2 bridge.

This module validates explicitly supplied parity records only.  It never reads
V1, accesses a private path, opens a database connection, or synchronizes
data.  A passing report is evidence for a future source-of-truth decision; it
is not a cutover command.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any, Final

PARITY_CONTRACT_VERSION: Final = "private-parity.v1"
PARITY_PASS: Final = "PASS"
PARITY_FAIL: Final = "FAIL"
PARITY_SEQUENCE_INVALID: Final = "INVALID_SEQUENCE"
_HASH_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_RESULTS: Final = frozenset({PARITY_PASS, PARITY_FAIL})


class ParityValidationError(ValueError):
    """Raised when a supplied parity record violates the evidence contract."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ParityValidationError(
            "REQUIRED_METADATA", f"{field} must be a trimmed non-empty string"
        )
    return value


def _sha256(value: object, field: str) -> str:
    text = _required_text(value, field)
    if not _HASH_RE.fullmatch(text):
        raise ParityValidationError("INVALID_SHA256", f"{field} must be a lowercase SHA-256 digest")
    return text


def _non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ParityValidationError("INVALID_COUNT", f"{field} must be a non-negative integer")
    return value


def _date(value: object, field: str) -> date:
    if type(value) is date:
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ParityValidationError("INVALID_DATE", f"{field} must be an ISO date") from exc
    raise ParityValidationError("INVALID_DATE", f"{field} must be an ISO date")


def _bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ParityValidationError("INVALID_BOOLEAN", f"{field} must be boolean")
    return value


def _counts(value: object) -> dict[str, int]:
    if not isinstance(value, Mapping) or not value:
        raise ParityValidationError(
            "INVALID_ROW_COUNTS", "artifact_row_counts must be a non-empty mapping"
        )
    result: dict[str, int] = {}
    for key, count in value.items():
        if not isinstance(key, str) or not key.strip() or key != key.strip():
            raise ParityValidationError(
                "INVALID_ROW_COUNTS", "artifact row-count keys must be trimmed strings"
            )
        result[key] = _non_negative_int(count, f"artifact_row_counts[{key}]")
    return dict(sorted(result.items()))


@dataclass(frozen=True)
class ParityDailyRecord:
    """One sanitized daily parity result supplied by an external operator.

    Operator identity is retained only in memory for private sign-off and is
    deliberately omitted from every public report.  No source rows or raw
    discrepancy text are accepted by this contract.
    """

    trading_date: date
    source_data_date: date
    bundle_version: str
    bundle_sha256: str
    source_snapshot_version: str
    source_snapshot_sha256: str
    application_revision: str
    migration_head: str
    parity_query_revision: str
    target_environment_alias: str
    operator_id: str
    artifact_row_counts: Mapping[str, int]
    blocking_mismatch_count: int
    null_mismatch_count: int
    value_mismatch_count: int
    replay_noop: bool
    compatibility_pass: bool
    error_quality_event_count: int
    warning_quality_event_count: int
    result: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "trading_date", _date(self.trading_date, "trading_date"))
        object.__setattr__(
            self, "source_data_date", _date(self.source_data_date, "source_data_date")
        )
        for field in (
            "bundle_version",
            "source_snapshot_version",
            "application_revision",
            "migration_head",
            "parity_query_revision",
            "target_environment_alias",
            "operator_id",
        ):
            object.__setattr__(self, field, _required_text(getattr(self, field), field))
        object.__setattr__(self, "bundle_sha256", _sha256(self.bundle_sha256, "bundle_sha256"))
        object.__setattr__(
            self,
            "source_snapshot_sha256",
            _sha256(self.source_snapshot_sha256, "source_snapshot_sha256"),
        )
        object.__setattr__(self, "artifact_row_counts", _counts(self.artifact_row_counts))
        for field in (
            "blocking_mismatch_count",
            "null_mismatch_count",
            "value_mismatch_count",
            "error_quality_event_count",
            "warning_quality_event_count",
        ):
            object.__setattr__(self, field, _non_negative_int(getattr(self, field), field))
        for field in ("replay_noop", "compatibility_pass"):
            object.__setattr__(self, field, _bool(getattr(self, field), field))
        if not isinstance(self.result, str) or self.result not in _RESULTS:
            raise ParityValidationError("INVALID_RESULT", "result must be PASS or FAIL")
        if self.source_data_date != self.trading_date:
            raise ParityValidationError("DATE_MISMATCH", "source_data_date must equal trading_date")
        expected = self.expected_result
        if self.result != expected:
            raise ParityValidationError(
                "WRONG_RESULT",
                f"result must be {expected} for the supplied evidence",
            )

    @property
    def expected_result(self) -> str:
        return (
            PARITY_PASS
            if self.blocking_mismatch_count == 0
            and self.null_mismatch_count == 0
            and self.value_mismatch_count == 0
            and self.replay_noop
            and self.compatibility_pass
            and self.error_quality_event_count == 0
            else PARITY_FAIL
        )

    @property
    def reason_codes(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.blocking_mismatch_count:
            reasons.append("BLOCKING_MISMATCH")
        if self.null_mismatch_count:
            reasons.append("NULL_MISMATCH")
        if self.value_mismatch_count:
            reasons.append("VALUE_MISMATCH")
        if not self.replay_noop:
            reasons.append("REPLAY_NOT_NOOP")
        if not self.compatibility_pass:
            reasons.append("COMPATIBILITY_FAILED")
        if self.error_quality_event_count:
            reasons.append("ERROR_QUALITY_EVENTS")
        return tuple(reasons)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ParityDailyRecord:
        """Parse a strict JSON-compatible daily record."""

        required = {
            "tradingDate",
            "sourceDataDate",
            "bundleVersion",
            "bundleSha256",
            "sourceSnapshotVersion",
            "sourceSnapshotSha256",
            "applicationRevision",
            "migrationHead",
            "parityQueryRevision",
            "targetEnvironmentAlias",
            "operatorId",
            "artifactRowCounts",
            "blockingMismatchCount",
            "nullMismatchCount",
            "valueMismatchCount",
            "replayNoop",
            "compatibilityPass",
            "errorQualityEventCount",
            "warningQualityEventCount",
            "result",
        }
        unknown = set(payload) - required
        missing = required - set(payload)
        if unknown:
            raise ParityValidationError("UNKNOWN_FIELD", f"unknown fields: {sorted(unknown)}")
        if missing:
            raise ParityValidationError("MISSING_FIELD", f"missing fields: {sorted(missing)}")
        return cls(
            trading_date=_date(payload["tradingDate"], "tradingDate"),
            source_data_date=_date(payload["sourceDataDate"], "sourceDataDate"),
            bundle_version=payload["bundleVersion"],
            bundle_sha256=payload["bundleSha256"],
            source_snapshot_version=payload["sourceSnapshotVersion"],
            source_snapshot_sha256=payload["sourceSnapshotSha256"],
            application_revision=payload["applicationRevision"],
            migration_head=payload["migrationHead"],
            parity_query_revision=payload["parityQueryRevision"],
            target_environment_alias=payload["targetEnvironmentAlias"],
            operator_id=payload["operatorId"],
            artifact_row_counts=payload["artifactRowCounts"],
            blocking_mismatch_count=payload["blockingMismatchCount"],
            null_mismatch_count=payload["nullMismatchCount"],
            value_mismatch_count=payload["valueMismatchCount"],
            replay_noop=payload["replayNoop"],
            compatibility_pass=payload["compatibilityPass"],
            error_quality_event_count=payload["errorQualityEventCount"],
            warning_quality_event_count=payload["warningQualityEventCount"],
            result=payload["result"],
        )


@dataclass(frozen=True)
class ParityEvidenceReport:
    """Sanitized report for one exactly-ten-day parity sequence."""

    status: str
    day_count: int
    passed_day_count: int
    consecutive_pass_count: int
    trading_date_from: date
    trading_date_to: date
    days: tuple[dict[str, Any], ...]
    reason_codes: tuple[str, ...]
    report_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contractVersion": PARITY_CONTRACT_VERSION,
            "status": self.status,
            "dayCount": self.day_count,
            "passedDayCount": self.passed_day_count,
            "consecutivePassCount": self.consecutive_pass_count,
            "tradingDateFrom": self.trading_date_from.isoformat(),
            "tradingDateTo": self.trading_date_to.isoformat(),
            "days": [dict(day) for day in self.days],
            "reasonCodes": list(self.reason_codes),
            "reportSha256": self.report_sha256,
        }


def _canonical_report_payload(
    *,
    status: str,
    days: tuple[dict[str, Any], ...],
    reason_codes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "contractVersion": PARITY_CONTRACT_VERSION,
        "status": status,
        "dayCount": len(days),
        "passedDayCount": sum(day["status"] == PARITY_PASS for day in days),
        "consecutivePassCount": _trailing_pass_count(days),
        "tradingDateFrom": days[0]["tradingDate"] if days else None,
        "tradingDateTo": days[-1]["tradingDate"] if days else None,
        "days": [dict(day) for day in days],
        "reasonCodes": list(reason_codes),
    }


def _trailing_pass_count(days: tuple[dict[str, Any], ...]) -> int:
    count = 0
    for day in reversed(days):
        if day["status"] != PARITY_PASS:
            break
        count += 1
    return count


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_parity_report(records: Iterable[ParityDailyRecord]) -> ParityEvidenceReport:
    """Evaluate one ordered sequence of exactly ten supplied trading days."""

    ordered = tuple(records)
    if len(ordered) != 10:
        raise ParityValidationError("TEN_DAYS_REQUIRED", "exactly ten daily records are required")
    dates = tuple(record.trading_date for record in ordered)
    if len(set(dates)) != len(dates):
        raise ParityValidationError(
            "DUPLICATE_DATE", "daily records must have unique trading dates"
        )
    if dates != tuple(sorted(dates)):
        raise ParityValidationError("DATES_NOT_ORDERED", "daily records must be chronological")

    days = tuple(
        {
            "tradingDate": record.trading_date.isoformat(),
            "sourceDataDate": record.source_data_date.isoformat(),
            "bundleVersion": record.bundle_version,
            "bundleSha256": record.bundle_sha256,
            "sourceSnapshotVersion": record.source_snapshot_version,
            "sourceSnapshotSha256": record.source_snapshot_sha256,
            "applicationRevision": record.application_revision,
            "migrationHead": record.migration_head,
            "parityQueryRevision": record.parity_query_revision,
            "artifactRowCounts": dict(record.artifact_row_counts),
            "status": record.result,
            "reasonCodes": list(record.reason_codes),
            "warningQualityEventCount": record.warning_quality_event_count,
        }
        for record in ordered
    )
    reason_codes = tuple(sorted({reason for day in days for reason in day["reasonCodes"]}))
    status = PARITY_PASS if all(day["status"] == PARITY_PASS for day in days) else PARITY_FAIL
    payload = _canonical_report_payload(status=status, days=days, reason_codes=reason_codes)
    return ParityEvidenceReport(
        status=status,
        day_count=len(days),
        passed_day_count=payload["passedDayCount"],
        consecutive_pass_count=payload["consecutivePassCount"],
        trading_date_from=dates[0],
        trading_date_to=dates[-1],
        days=days,
        reason_codes=reason_codes,
        report_sha256=_digest(payload),
    )


__all__ = [
    "PARITY_CONTRACT_VERSION",
    "PARITY_FAIL",
    "PARITY_PASS",
    "PARITY_SEQUENCE_INVALID",
    "ParityDailyRecord",
    "ParityEvidenceReport",
    "ParityValidationError",
    "build_parity_report",
]
