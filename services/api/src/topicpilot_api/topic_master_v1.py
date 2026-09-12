"""Owner-editable Topic Taxonomy + Membership Master V1.

This module is deliberately pure: it reads UTF-8 CSV source files, validates
them deterministically, and produces an explicit canonical sync plan.  It does
not connect to PostgreSQL or mutate production state.

The Owner vocabulary is LEAD/CORE/RELATED.  The current V2 relation carrier
still stores REPRESENTATIVE/CORE/RELATED, so the adapter is explicit and
centralised here rather than being reimplemented by consumers.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

TOPIC_SCHEMA_VERSION = "topic-taxonomy-master.v1"
MEMBERSHIP_SCHEMA_VERSION = "instrument-topic-membership-master.v1"
INSTRUMENT_SCHEMA_VERSION = "instrument-master.v1"
OWNER_ROLES = frozenset({"LEAD", "CORE", "RELATED"})
RELATION_TYPES = frozenset({"PRIMARY", "SECONDARY"})
REVIEW_STATES = frozenset({"APPROVED", "PENDING_REVIEW"})
CANONICAL_ROLE_MAP = {"LEAD": "REPRESENTATIVE", "CORE": "CORE", "RELATED": "RELATED"}

TOPIC_FIELDS = (
    "topic_key",
    "topic_name",
    "parent_topic",
    "enabled",
    "description",
    "governance_state",
)
MEMBERSHIP_FIELDS = (
    "market_code",
    "instrument_code",
    "instrument_name",
    "topic_key",
    "topic_relation_type",
    "structural_role",
    "topic_weight",
    "enabled",
    "review_state",
    "valid_from",
    "valid_to",
    "source_reference",
)
INSTRUMENT_FIELDS = (
    "market_code",
    "instrument_code",
    "instrument_name",
    "instrument_type",
    "currency",
    "enabled",
    "listing_status",
    "valid_from",
    "valid_to",
    "identity_source",
    "provenance_class",
    "owner_review_required",
)
INSTRUMENT_MARKETS = frozenset({"TPE", "TWO"})
INSTRUMENT_STATUSES = frozenset({"ACTIVE", "LISTED", "DELISTED", "SUSPENDED", "TERMINATED"})
_INSTRUMENT_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    record_type: str
    row_number: int | None = None
    key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "record_type": self.record_type,
            "row_number": self.row_number,
            "key": self.key,
        }


@dataclass(frozen=True)
class MasterData:
    topics: tuple[dict[str, str], ...]
    memberships: tuple[dict[str, str], ...]
    topic_path: str
    membership_path: str
    instruments: tuple[dict[str, str], ...] = ()
    instrument_path: str = ""

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "instrument_schema_version": INSTRUMENT_SCHEMA_VERSION,
            "topic_schema_version": TOPIC_SCHEMA_VERSION,
            "membership_schema_version": MEMBERSHIP_SCHEMA_VERSION,
            "instruments": list(self.instruments),
            "topics": list(self.topics),
            "memberships": list(self.memberships),
        }

    @property
    def source_hash(self) -> str:
        encoded = json.dumps(
            self.canonical_payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ValidationReport:
    source_hash: str
    instrument_count: int
    topic_count: int
    membership_count: int
    membership_unique_instrument_count: int
    approved_membership_count: int
    pending_membership_count: int
    issues: tuple[ValidationIssue, ...]

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "ERROR")

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "WARNING")

    @property
    def valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "source_hash": self.source_hash,
            "instrument_count": self.instrument_count,
            "topic_count": self.topic_count,
            "membership_count": self.membership_count,
            "membership_unique_instrument_count": self.membership_unique_instrument_count,
            "approved_membership_count": self.approved_membership_count,
            "pending_membership_count": self.pending_membership_count,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [issue.to_dict() for issue in self.issues],
        }


def _read_csv(path: Path, required_fields: tuple[str, ...]) -> tuple[dict[str, str], ...]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = tuple(reader.fieldnames or ())
            missing = [field for field in required_fields if field not in fields]
            if missing:
                raise ValueError(f"{path}: missing required columns: {', '.join(missing)}")
            rows: list[dict[str, str]] = []
            for row in reader:
                rows.append({field: (row.get(field) or "").strip() for field in required_fields})
            return tuple(rows)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError(f"cannot read CSV source: {path}") from exc


def load_master(
    topic_path: Path,
    membership_path: Path,
    instrument_path: Path | None = None,
) -> MasterData:
    topics = _read_csv(topic_path, TOPIC_FIELDS)
    memberships = _read_csv(membership_path, MEMBERSHIP_FIELDS)
    instruments = _read_csv(instrument_path, INSTRUMENT_FIELDS) if instrument_path else ()
    return MasterData(
        topics=tuple(sorted(topics, key=lambda row: row["topic_key"])),
        memberships=tuple(
            sorted(
                memberships,
                key=lambda row: (
                    row["market_code"],
                    row["instrument_code"],
                    row["topic_key"],
                ),
            )
        ),
        topic_path=str(topic_path),
        membership_path=str(membership_path),
        instruments=tuple(
            sorted(instruments, key=lambda row: (row["market_code"], row["instrument_code"]))
        ),
        instrument_path=str(instrument_path) if instrument_path else "",
    )


def _issue(
    issues: list[ValidationIssue],
    severity: str,
    code: str,
    message: str,
    record_type: str,
    row_number: int | None = None,
    key: str | None = None,
) -> None:
    issues.append(ValidationIssue(severity, code, message, record_type, row_number, key))


def _valid_bool(value: str) -> bool:
    return value.upper() in {"TRUE", "FALSE"}


def _parse_weight(value: str) -> Decimal | None:
    if not value:
        return None
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("not a decimal") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("must be a finite non-negative decimal")
    return result


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def validate_master(
    master: MasterData,
    *,
    known_instruments: Iterable[tuple[str, str]] = (),
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    instrument_rows: dict[tuple[str, str], dict[str, str]] = {}
    if master.instrument_path:
        for index, row in enumerate(master.instruments, start=2):
            market = row["market_code"].upper()
            code = row["instrument_code"]
            key = f"{market}:{code}"
            identity = (market, code)
            if identity in instrument_rows:
                _issue(
                    issues,
                    "ERROR",
                    "DUPLICATE_INSTRUMENT",
                    "duplicate instrument identity in Instrument Master",
                    "instrument",
                    index,
                    key,
                )
            instrument_rows[identity] = row
            if market not in INSTRUMENT_MARKETS:
                _issue(
                    issues,
                    "ERROR",
                    "INVALID_MARKET",
                    "market_code must be TPE or TWO",
                    "instrument",
                    index,
                    key,
                )
            if not _INSTRUMENT_CODE_RE.fullmatch(code):
                _issue(
                    issues,
                    "ERROR",
                    "INVALID_INSTRUMENT_CODE",
                    "instrument_code must be a non-empty stable ticker",
                    "instrument",
                    index,
                    key,
                )
            if not row["instrument_name"]:
                _issue(
                    issues,
                    "ERROR",
                    "REQUIRED_FIELD",
                    "instrument_name is required",
                    "instrument",
                    index,
                    key,
                )
            if not row["instrument_type"]:
                _issue(
                    issues,
                    "ERROR",
                    "REQUIRED_FIELD",
                    "instrument_type is required",
                    "instrument",
                    index,
                    key,
                )
            if not row["currency"]:
                _issue(
                    issues,
                    "ERROR",
                    "REQUIRED_FIELD",
                    "currency is required",
                    "instrument",
                    index,
                    key,
                )
            if not _valid_bool(row["enabled"]):
                _issue(
                    issues,
                    "ERROR",
                    "INVALID_ENABLED",
                    "enabled must be TRUE or FALSE",
                    "instrument",
                    index,
                    key,
                )
            if row["listing_status"] not in INSTRUMENT_STATUSES:
                _issue(
                    issues,
                    "ERROR",
                    "INVALID_LISTING_STATUS",
                    "listing_status is not a supported canonical status",
                    "instrument",
                    index,
                    key,
                )
            if not _valid_bool(row["owner_review_required"]):
                _issue(
                    issues,
                    "ERROR",
                    "INVALID_OWNER_REVIEW_FLAG",
                    "owner_review_required must be TRUE or FALSE",
                    "instrument",
                    index,
                    key,
                )
            try:
                valid_from = _parse_date(row["valid_from"])
                valid_to = _parse_date(row["valid_to"])
                if valid_to is not None and valid_from is not None and valid_to < valid_from:
                    _issue(
                        issues,
                        "ERROR",
                        "INVALID_DATE_RANGE",
                        "valid_to cannot precede valid_from",
                        "instrument",
                        index,
                        key,
                    )
            except ValueError as exc:
                _issue(issues, "ERROR", "INVALID_DATE", str(exc), "instrument", index, key)

    topic_keys: set[str] = set()
    topic_rows: dict[str, dict[str, str]] = {}
    for index, row in enumerate(master.topics, start=2):
        key = row["topic_key"]
        if not key:
            _issue(issues, "ERROR", "REQUIRED_FIELD", "topic_key is required", "topic", index)
            continue
        if key in topic_keys:
            _issue(issues, "ERROR", "DUPLICATE_TOPIC", "duplicate topic_key", "topic", index, key)
        topic_keys.add(key)
        topic_rows[key] = row
        if not row["topic_name"]:
            _issue(issues, "ERROR", "REQUIRED_FIELD", "topic_name is required", "topic", index, key)
        if not _valid_bool(row["enabled"]):
            _issue(
                issues,
                "ERROR",
                "INVALID_ENABLED",
                "enabled must be TRUE or FALSE",
                "topic",
                index,
                key,
            )
        if row["parent_topic"] == key:
            _issue(
                issues, "ERROR", "SELF_PARENT", "topic cannot parent itself", "topic", index, key
            )
    for index, row in enumerate(master.topics, start=2):
        parent = row["parent_topic"]
        if parent and parent not in topic_keys:
            _issue(
                issues,
                "ERROR",
                "UNKNOWN_PARENT",
                f"unknown parent topic: {parent}",
                "topic",
                index,
                row["topic_key"],
            )

    known = set(known_instruments)
    if not master.instrument_path and not known:
        _issue(
            issues,
            "ERROR",
            "INSTRUMENT_MASTER_REQUIRED",
            "validate memberships with config/topic_master_v1/instruments.csv",
            "instrument",
        )
    canonical_instruments = set(instrument_rows)
    relation_keys: set[tuple[str, str, str]] = set()
    approved = 0
    pending = 0
    topic_members: dict[str, list[dict[str, str]]] = {}
    for index, row in enumerate(master.memberships, start=2):
        key_tuple = (row["market_code"], row["instrument_code"], row["topic_key"])
        key = ":".join(key_tuple)
        if key_tuple in relation_keys:
            _issue(
                issues,
                "ERROR",
                "DUPLICATE_MEMBERSHIP",
                "duplicate instrument-topic relation",
                "membership",
                index,
                key,
            )
        relation_keys.add(key_tuple)
        instrument_identity = (row["market_code"], row["instrument_code"])
        if (
            (master.instrument_path and instrument_identity not in canonical_instruments)
            or (not master.instrument_path and known and instrument_identity not in known)
        ):
            _issue(
                issues,
                "ERROR",
                "UNKNOWN_INSTRUMENT",
                "instrument is not in canonical reference universe",
                "membership",
                index,
                key,
            )
        if instrument_identity in instrument_rows:
            canonical_name = instrument_rows[instrument_identity]["instrument_name"]
            if row["instrument_name"] != canonical_name:
                _issue(
                    issues,
                    "ERROR",
                    "INSTRUMENT_NAME_MISMATCH",
                    (
                        "membership instrument_name does not match Instrument Master: "
                        f"{canonical_name}"
                    ),
                    "membership",
                    index,
                    key,
                )
        elif master.instrument_path:
            # The unknown identity issue above is the actionable error.  Keep
            # name validation silent here so one missing identity is not noisy.
            pass
        if row["market_code"] not in INSTRUMENT_MARKETS:
            _issue(
                issues,
                "ERROR",
                "INVALID_MARKET",
                "market_code must be TPE or TWO",
                "membership",
                index,
                key,
            )
        if row["topic_key"] not in topic_keys:
            _issue(
                issues,
                "ERROR",
                "UNKNOWN_TOPIC",
                "topic_key is not in Topic Master",
                "membership",
                index,
                key,
            )
        if row["topic_relation_type"] and row["topic_relation_type"] not in RELATION_TYPES:
            _issue(
                issues,
                "ERROR",
                "INVALID_RELATION_TYPE",
                "topic_relation_type must be PRIMARY or SECONDARY",
                "membership",
                index,
                key,
            )
        if row["structural_role"] and row["structural_role"] not in OWNER_ROLES:
            _issue(
                issues,
                "ERROR",
                "INVALID_STRUCTURAL_ROLE",
                "structural_role must be LEAD, CORE, or RELATED",
                "membership",
                index,
                key,
            )
        if not _valid_bool(row["enabled"]):
            _issue(
                issues,
                "ERROR",
                "INVALID_ENABLED",
                "enabled must be TRUE or FALSE",
                "membership",
                index,
                key,
            )
        if row["review_state"] not in REVIEW_STATES:
            _issue(
                issues,
                "ERROR",
                "INVALID_REVIEW_STATE",
                "review_state must be APPROVED or PENDING_REVIEW",
                "membership",
                index,
                key,
            )
        try:
            _parse_weight(row["topic_weight"])
        except ValueError as exc:
            _issue(issues, "ERROR", "INVALID_WEIGHT", str(exc), "membership", index, key)
        try:
            valid_from = _parse_date(row["valid_from"])
            valid_to = _parse_date(row["valid_to"])
            if valid_from is None:
                _issue(
                    issues,
                    "ERROR",
                    "VALID_FROM_MISSING",
                    "valid_from is required",
                    "membership",
                    index,
                    key,
                )
            if valid_to is not None and valid_from is not None and valid_to < valid_from:
                _issue(
                    issues,
                    "ERROR",
                    "INVALID_DATE_RANGE",
                    "valid_to cannot precede valid_from",
                    "membership",
                    index,
                    key,
                )
        except ValueError as exc:
            _issue(issues, "ERROR", "INVALID_DATE", str(exc), "membership", index, key)
        if row["review_state"] == "APPROVED":
            approved += 1
            if not row["topic_relation_type"]:
                _issue(
                    issues,
                    "ERROR",
                    "APPROVED_RELATION_TYPE_MISSING",
                    "approved relation needs PRIMARY or SECONDARY",
                    "membership",
                    index,
                    key,
                )
            if not row["structural_role"]:
                _issue(
                    issues,
                    "ERROR",
                    "APPROVED_ROLE_MISSING",
                    "approved relation needs a structural_role",
                    "membership",
                    index,
                    key,
                )
        else:
            pending += 1
            if not row["topic_relation_type"] or not row["structural_role"]:
                _issue(
                    issues,
                    "WARNING",
                    "PENDING_REVIEW",
                    "relation is retained but excluded from approved canonical sync until reviewed",
                    "membership",
                    index,
                    key,
                )
        topic_members.setdefault(row["topic_key"], []).append(row)

    for topic_key in sorted(topic_keys):
        rows = [row for row in topic_members.get(topic_key, ()) if row["enabled"] == "TRUE"]
        approved_rows = [row for row in rows if row["review_state"] == "APPROVED"]
        roles = {row["structural_role"] for row in approved_rows if row["structural_role"]}
        if not approved_rows:
            _issue(
                issues,
                "WARNING",
                "NO_APPROVED_MEMBERS",
                "topic has no approved canonical membership rows",
                "topic",
                key=topic_key,
            )
        if not rows or len(rows) < 3:
            _issue(
                issues,
                "WARNING",
                "VERY_SMALL_UNIVERSE",
                "topic has fewer than three enabled members",
                "topic",
                key=topic_key,
            )
        if rows and "LEAD" not in roles:
            _issue(
                issues, "WARNING", "NO_LEAD", "topic has no approved LEAD", "topic", key=topic_key
            )
        if rows and "CORE" not in roles:
            _issue(
                issues, "WARNING", "NO_CORE", "topic has no approved CORE", "topic", key=topic_key
            )
        if rows and roles == {"RELATED"}:
            _issue(
                issues,
                "WARNING",
                "ONLY_RELATED",
                "topic has only RELATED approved members",
                "topic",
                key=topic_key,
            )

    return ValidationReport(
        source_hash=master.source_hash,
        instrument_count=len(master.instruments),
        topic_count=len(master.topics),
        membership_count=len(master.memberships),
        membership_unique_instrument_count=len(
            {(row["market_code"], row["instrument_code"]) for row in master.memberships}
        ),
        approved_membership_count=approved,
        pending_membership_count=pending,
        issues=tuple(
            sorted(
                issues,
                key=lambda issue: (
                    issue.record_type,
                    issue.row_number or 0,
                    issue.code,
                    issue.key or "",
                ),
            )
        ),
    )


def canonical_relation_rows(
    master: MasterData, report: ValidationReport
) -> tuple[dict[str, Any], ...]:
    if not report.valid:
        raise ValueError("cannot produce canonical rows from an invalid Owner Master")
    rows: list[dict[str, Any]] = []
    for row in master.memberships:
        if row["enabled"] != "TRUE" or row["review_state"] != "APPROVED":
            continue
        rows.append(
            {
                "market_code": row["market_code"],
                "instrument_code": row["instrument_code"],
                "topic_key": row["topic_key"],
                "relation_type": row["topic_relation_type"],
                "structural_role": CANONICAL_ROLE_MAP[row["structural_role"]],
                "owner_structural_role": row["structural_role"],
                "topic_weight": row["topic_weight"] or None,
                "valid_from": row["valid_from"] or None,
                "valid_to": row["valid_to"] or None,
                "source_reference": row["source_reference"],
            }
        )
    return tuple(
        sorted(rows, key=lambda row: (row["market_code"], row["instrument_code"], row["topic_key"]))
    )


def canonical_instrument_rows(
    master: MasterData, report: ValidationReport
) -> tuple[dict[str, Any], ...]:
    """Return the validated Owner identities in canonical sync shape."""

    if not report.valid:
        raise ValueError("cannot produce canonical instruments from an invalid Owner Master")
    return tuple(
        {
            "market_code": row["market_code"],
            "instrument_code": row["instrument_code"],
            "name": row["instrument_name"],
            "instrument_type": row["instrument_type"],
            "currency": row["currency"],
            "enabled": row["enabled"],
            "listing_status": row["listing_status"],
            "valid_from": row["valid_from"] or None,
            "valid_to": row["valid_to"] or None,
        }
        for row in master.instruments
    )


def canonical_topic_rows(
    master: MasterData, report: ValidationReport
) -> tuple[dict[str, Any], ...]:
    """Return the full Owner topic state, including disabled rows."""

    if not report.valid:
        raise ValueError("cannot produce canonical topics from an invalid Owner Master")
    return tuple(
        {
            "topic_key": row["topic_key"],
            "topic_name": row["topic_name"],
            "parent_topic": row["parent_topic"] or None,
            "enabled": row["enabled"],
            "description": row["description"],
            "governance_state": row["governance_state"],
        }
        for row in master.topics
    )


def canonical_sync_plan(
    master: MasterData,
    report: ValidationReport,
    *,
    existing_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not report.valid:
        return {
            "status": "REJECTED",
            "reason": "OWNER_MASTER_VALIDATION_FAILED",
            "source_hash": report.source_hash,
            "operations": [],
            "validation": report.to_dict(),
        }
    instrument_rows = canonical_instrument_rows(master, report)
    topic_rows = canonical_topic_rows(master, report)
    rows = canonical_relation_rows(master, report)
    previous_hash = (existing_snapshot or {}).get("owner_master_hash")
    if previous_hash is None:
        operation = "CREATE_SNAPSHOT"
    elif (
        previous_hash == report.source_hash
        and (existing_snapshot or {}).get("snapshot_schema_version")
        == "canonical-instrument-topic-snapshot.v1"
        and (existing_snapshot or {}).get("instrument_rows") == list(instrument_rows)
        and (existing_snapshot or {}).get("topic_rows") == list(topic_rows)
        and (existing_snapshot or {}).get("rows") == list(rows)
    ):
        operation = "NOOP"
    else:
        operation = "REPLACE_SNAPSHOT"
    return {
        "status": "DRY_RUN_PASS",
        "scope": "VALIDATED_INSTRUMENTS_TOPICS_AND_APPROVED_ENABLED_RELATIONS",
        "target": {
            "instruments": "topicpilot.instruments",
            "topics": "topicpilot.topics",
            "relations": "topicpilot.instrument_topic_relations",
        },
        "source_hash": report.source_hash,
        "owner_master_hash": report.source_hash,
        "previous_owner_master_hash": previous_hash,
        "operation": operation,
        "snapshot_schema_version": "canonical-instrument-topic-snapshot.v1",
        "operations": ["SYNC_INSTRUMENTS", "SYNC_TOPICS", "SYNC_RELATIONS"],
        "canonical_instrument_count": len(instrument_rows),
        "canonical_topic_count": len(topic_rows),
        "canonical_relation_count": len(rows),
        "pending_review_count": report.pending_membership_count,
        "role_mapping": CANONICAL_ROLE_MAP,
        "instrument_rows": list(instrument_rows),
        "topic_rows": list(topic_rows),
        "rows": list(rows),
        "validation": report.to_dict(),
    }


def write_canonical_snapshot(plan: dict[str, Any], path: Path) -> None:
    """Write only the deterministic local derivative; never a database write."""

    if plan.get("status") != "DRY_RUN_PASS":
        raise ValueError("cannot write a canonical snapshot from a rejected sync plan")
    payload = {
        "snapshot_schema_version": "canonical-instrument-topic-snapshot.v1",
        "authority_class": "DERIVED_FROM_OWNER_MASTER",
        "owner_master_hash": plan["owner_master_hash"],
        "target": plan["target"],
        "role_mapping": plan["role_mapping"],
        "operations": plan["operations"],
        "instrument_rows": plan["instrument_rows"],
        "topic_rows": plan["topic_rows"],
        "rows": plan["rows"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and dry-run Topic Master V1")
    parser.add_argument("command", choices=("validate", "dry-run"))
    parser.add_argument("--topics", type=Path, required=True)
    parser.add_argument("--memberships", type=Path, required=True)
    instrument_group = parser.add_mutually_exclusive_group()
    instrument_group.add_argument("--instrument-master", type=Path)
    instrument_group.add_argument(
        "--instruments",
        type=Path,
        help="legacy JSON identity input; prefer --instrument-master",
    )
    parser.add_argument("--existing-snapshot", type=Path)
    parser.add_argument("--write-snapshot", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    master = load_master(args.topics, args.memberships, args.instrument_master)
    known: set[tuple[str, str]] = set()
    if args.instruments:
        payload = json.loads(args.instruments.read_text(encoding="utf-8"))
        known = {(str(row["market_code"]), str(row["instrument_code"])) for row in payload}
    report = validate_master(master, known_instruments=known)
    result: dict[str, Any] = report.to_dict()
    if args.command == "dry-run":
        snapshot = None
        if args.existing_snapshot and args.existing_snapshot.exists():
            snapshot = json.loads(args.existing_snapshot.read_text(encoding="utf-8"))
        result = canonical_sync_plan(master, report, existing_snapshot=snapshot)
        if args.write_snapshot:
            write_canonical_snapshot(result, args.write_snapshot)
            result = {**result, "written_snapshot": str(args.write_snapshot)}
    # Keep CLI output ASCII-safe on Windows consoles and when redirected to
    # PowerShell, while the Owner CSV/source files remain UTF-8.
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 0 if report.valid else 1


__all__ = [
    "CANONICAL_ROLE_MAP",
    "INSTRUMENT_FIELDS",
    "INSTRUMENT_SCHEMA_VERSION",
    "MEMBERSHIP_FIELDS",
    "TOPIC_FIELDS",
    "MasterData",
    "ValidationIssue",
    "ValidationReport",
    "canonical_instrument_rows",
    "canonical_relation_rows",
    "canonical_sync_plan",
    "canonical_topic_rows",
    "load_master",
    "main",
    "validate_master",
    "write_canonical_snapshot",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
