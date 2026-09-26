"""Complete read-only diagnostics for persisted structural-role authority."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel
from sqlalchemy import Select, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .orm.models import Instrument, InstrumentTopicRelation, Market, Topic
from .structural_role_contract import ALLOWED_STRUCTURAL_ROLES

FORMAL_APPROVAL_STATES = frozenset({"DRAFT", "PROPOSED", "APPROVED", "DEPRECATED", "REJECTED"})
ROLE_ALIASES = frozenset({"LEAD", "LEADER", "PRIMARY_TOPIC", "MAIN"})


class StructuralRoleAuthorityAuditItem(BaseModel):
    relation_id: str
    instrument_id: str
    instrument_code: str
    instrument_type: str
    instrument_active: bool
    instrument_valid_from: date | None
    instrument_valid_to: date | None
    market_code: str
    market_active: bool
    topic_id: str
    topic_slug: str
    topic_status: str
    topic_valid_from: date | None
    topic_valid_to: date | None
    relation_type: str
    structural_role: str | None
    role_status: Literal["VALID", "NULL", "INVALID"]
    invalid_role_value: str | None
    invalid_role_category: str | None
    root_cause: str | None
    approval_state: str | None
    authority_version: str | None
    effective_from: date
    effective_to: date | None
    authority_status_bucket: Literal[
        "CURRENT_ACTIVE",
        "HISTORICAL_SUPERSEDED",
        "FUTURE_EFFECTIVE",
        "INACTIVE",
        "PROPOSED",
        "OTHER",
    ]
    current_effective: bool
    supersedes_authority_id: str | None
    superseded_by_authority_id: str | None
    source_artifact_id: str | None
    source_artifact_hash: str | None
    approval_reference: str | None
    correction_sequence: int | None
    lineage_hash: str | None
    supersession_issue: str | None
    lineage_issue: str | None


class StructuralRoleAuthorityAuditSummary(BaseModel):
    as_of_date: date
    total_rows_scanned: int
    valid_role_rows: int
    invalid_role_rows: int
    null_role_rows: int
    unknown_role_rows: int
    duplicate_active_authority_rows: int
    supersession_conflict_rows: int
    lineage_inconsistency_rows: int
    status_counts: dict[str, int]
    invalid_role_values: list[dict[str, Any]]
    current_relation_type_counts: dict[str, int]
    current_structural_role_counts: dict[str, int]
    current_relation_type_x_structural_role: dict[str, int]
    database_constraint: dict[str, Any]


class StructuralRoleAuthorityAuditPage(BaseModel):
    items: list[StructuralRoleAuthorityAuditItem]
    total: int
    limit: int
    offset: int
    has_more: bool
    summary: StructuralRoleAuthorityAuditSummary
    read_only: Literal[True] = True


@dataclass(frozen=True)
class AuditRelation:
    relation_id: str
    instrument_id: str
    instrument_code: str
    instrument_type: str
    instrument_active: bool
    instrument_valid_from: date | None
    instrument_valid_to: date | None
    market_code: str
    market_active: bool
    topic_id: str
    topic_slug: str
    topic_status: str
    topic_valid_from: date | None
    topic_valid_to: date | None
    relation_type: str
    structural_role: str | None
    approval_state: str | None
    authority_version: str | None
    effective_from: date
    effective_to: date | None
    supersedes_authority_id: str | None
    superseded_by_authority_id: str | None
    source_artifact_id: str | None
    source_artifact_hash: str | None
    approval_reference: str | None
    correction_sequence: int | None
    lineage_hash: str | None


def _role_category(value: str) -> str | None:
    if value == "":
        return "EMPTY_STRING"
    if value != value.strip():
        return "WHITESPACE_PADDED"
    if value.upper() in {role.upper() for role in ALLOWED_STRUCTURAL_ROLES}:
        return "CASE_NORMALIZATION_DRIFT"
    if value.upper() in ROLE_ALIASES:
        return "LEGACY_VOCABULARY_DRIFT"
    if value.isdigit() or value.replace(".", "", 1).isdigit():
        return "UNEXPECTED_NUMERIC_OR_STRING"
    return "MALFORMED_ENUM_STRING"


def _role_status(value: str | None) -> tuple[str, str | None, str | None]:
    if value is None:
        return "NULL", None, None
    if value in ALLOWED_STRUCTURAL_ROLES:
        return "VALID", None, None
    return "INVALID", value, _role_category(value)


def _active_entity(row: AuditRelation, as_of: date) -> bool:
    return (
        row.instrument_active
        and row.instrument_type == "EQUITY"
        and (row.instrument_valid_from is None or row.instrument_valid_from <= as_of)
        and (row.instrument_valid_to is None or as_of <= row.instrument_valid_to)
        and row.market_active
        and row.market_code in {"TPE", "TWO"}
        and row.topic_status not in {"DISABLED", "RETIRED"}
        and (row.topic_valid_from is None or row.topic_valid_from <= as_of)
        and (row.topic_valid_to is None or as_of <= row.topic_valid_to)
    )


def _current_effective(row: AuditRelation, as_of: date) -> bool:
    return _active_entity(row, as_of) and row.effective_from <= as_of and (
        row.effective_to is None or as_of <= row.effective_to
    )


def _status_bucket(row: AuditRelation, as_of: date) -> str:
    if not _active_entity(row, as_of):
        return "INACTIVE"
    if row.effective_from > as_of:
        return "FUTURE_EFFECTIVE"
    if row.approval_state in {"DRAFT", "PROPOSED"}:
        return "PROPOSED"
    if row.superseded_by_authority_id is not None or (
        row.effective_to is not None and row.effective_to < as_of
    ):
        return "HISTORICAL_SUPERSEDED"
    if _current_effective(row, as_of) and row.approval_state == "APPROVED":
        return "CURRENT_ACTIVE"
    return "OTHER"


def _lineage_issue(row: AuditRelation) -> str | None:
    formal_fields = (
        row.structural_role,
        row.approval_state,
        row.authority_version,
        row.source_artifact_id,
        row.source_artifact_hash,
        row.approval_reference,
        row.lineage_hash,
    )
    if not any(value is not None for value in formal_fields):
        return None
    missing = [
        name
        for name, value in (
            ("authority_version", row.authority_version),
            ("source_artifact_id", row.source_artifact_id),
            ("source_artifact_hash", row.source_artifact_hash),
            ("approval_reference", row.approval_reference),
            ("lineage_hash", row.lineage_hash),
        )
        if value is None or not value.strip()
    ]
    if missing:
        return "MISSING_REQUIRED_LINEAGE_FIELDS:" + ",".join(missing)
    if row.effective_to is not None and row.effective_to < row.effective_from:
        return "INVALID_EFFECTIVE_RANGE"
    if row.correction_sequence is None or row.correction_sequence < 0:
        return "INVALID_CORRECTION_SEQUENCE"
    return None


def _root_cause(
    role_status: str, supersession_issue: str | None, lineage_issue: str | None
) -> str | None:
    if supersession_issue:
        return "SUPERSESSION_INCONSISTENCY"
    if role_status in {"INVALID", "NULL"} or lineage_issue:
        return "UNKNOWN_ROOT_CAUSE"
    return None


def _supersession_issues(rows: tuple[AuditRelation, ...]) -> dict[str, str]:
    by_id = {row.relation_id: row for row in rows}
    issues: dict[str, str] = {}
    for row in rows:
        checks = (
            (row.supersedes_authority_id, "superseded_by_authority_id"),
            (row.superseded_by_authority_id, "supersedes_authority_id"),
        )
        for target_id, reverse_field in checks:
            if target_id is None:
                continue
            if target_id == row.relation_id:
                issues[row.relation_id] = "SELF_SUPERSESSION"
                continue
            target = by_id.get(target_id)
            if target is None:
                issues[row.relation_id] = "MISSING_SUPERSESSION_TARGET"
                continue
            if (target.instrument_id, target.topic_id) != (row.instrument_id, row.topic_id):
                issues[row.relation_id] = "CROSS_IDENTITY_SUPERSESSION"
                continue
            if getattr(target, reverse_field) != row.relation_id:
                issues[row.relation_id] = "AMBIGUOUS_SUPERSESSION"
    return issues


def _database_constraint_status(session: Session) -> dict[str, Any]:
    try:
        rows = session.execute(
            text(
                """
                SELECT conname, pg_get_constraintdef(pc.oid) AS definition, convalidated
                FROM pg_constraint pc
                JOIN pg_class c ON c.oid = pc.conrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'topicpilot'
                  AND c.relname = 'instrument_topic_relations'
                  AND pc.contype = 'c'
                  AND pc.conname = 'ck_instrument_topic_relation_structural_role'
                """
            )
        ).mappings().all()
    except SQLAlchemyError as exc:
        return {
            "exists": False,
            "validated": False,
            "required_definition": (
                "structural_role IS NULL OR structural_role IN "
                "('REPRESENTATIVE', 'CORE', 'RELATED')"
            ),
            "read_error": str(exc),
        }
    if not rows:
        return {
            "exists": False,
            "validated": False,
            "required_definition": (
                "structural_role IS NULL OR structural_role IN "
                "('REPRESENTATIVE', 'CORE', 'RELATED')"
            ),
        }
    row = rows[0]
    return {
        "exists": True,
        "validated": bool(row["convalidated"]),
        "name": row["conname"],
        "definition": row["definition"],
        "required_definition": (
            "structural_role IS NULL OR structural_role IN "
            "('REPRESENTATIVE', 'CORE', 'RELATED')"
        ),
    }


def audit_relations(
    rows: tuple[AuditRelation, ...], as_of: date, database_constraint: dict[str, Any]
) -> tuple[list[StructuralRoleAuthorityAuditItem], StructuralRoleAuthorityAuditSummary]:
    supersession_issues = _supersession_issues(rows)
    grouped_current: dict[tuple[str, str], list[AuditRelation]] = defaultdict(list)
    for row in rows:
        if _current_effective(row, as_of) and row.approval_state == "APPROVED":
            grouped_current[(row.instrument_id, row.topic_id)].append(row)
    duplicate_rows = sum(
        len(group) for group in grouped_current.values() if len(group) > 1
    )

    items: list[StructuralRoleAuthorityAuditItem] = []
    role_counts = Counter()
    status_counts = Counter()
    type_counts = Counter()
    current_cross_tab = Counter()
    invalid_values: dict[str, dict[str, Any]] = {}
    for row in rows:
        role_status, invalid_value, invalid_category = _role_status(row.structural_role)
        current_effective = _current_effective(row, as_of)
        status_bucket = _status_bucket(row, as_of)
        lineage_issue = _lineage_issue(row)
        supersession_issue = supersession_issues.get(row.relation_id)
        root_cause = _root_cause(role_status, supersession_issue, lineage_issue)
        role_counts[role_status] += 1
        status_counts[status_bucket] += 1
        if current_effective:
            type_counts[row.relation_type] += 1
            if role_status == "VALID":
                current_cross_tab[f"{row.relation_type} x {row.structural_role}"] += 1
        if invalid_value is not None:
            entry = invalid_values.setdefault(
                invalid_value,
                {
                    "invalid_role_value": invalid_value,
                    "category": invalid_category,
                    "count": 0,
                    "relation_ids": [],
                    "authority_versions": [],
                    "source_artifact_ids": [],
                    "approval_states": [],
                    "effective_dates": [],
                },
            )
            entry["count"] += 1
            entry["relation_ids"].append(row.relation_id)
            if row.authority_version and row.authority_version not in entry["authority_versions"]:
                entry["authority_versions"].append(row.authority_version)
            if (
                row.source_artifact_id
                and row.source_artifact_id not in entry["source_artifact_ids"]
            ):
                entry["source_artifact_ids"].append(row.source_artifact_id)
            if row.approval_state and row.approval_state not in entry["approval_states"]:
                entry["approval_states"].append(row.approval_state)
            entry["effective_dates"].append(row.effective_from.isoformat())
        items.append(
            StructuralRoleAuthorityAuditItem(
                relation_id=row.relation_id,
                instrument_id=row.instrument_id,
                instrument_code=row.instrument_code,
                instrument_type=row.instrument_type,
                instrument_active=row.instrument_active,
                instrument_valid_from=row.instrument_valid_from,
                instrument_valid_to=row.instrument_valid_to,
                market_code=row.market_code,
                market_active=row.market_active,
                topic_id=row.topic_id,
                topic_slug=row.topic_slug,
                topic_status=row.topic_status,
                topic_valid_from=row.topic_valid_from,
                topic_valid_to=row.topic_valid_to,
                relation_type=row.relation_type,
                structural_role=row.structural_role,
                role_status=role_status,
                invalid_role_value=invalid_value,
                invalid_role_category=invalid_category,
                root_cause=root_cause,
                approval_state=row.approval_state,
                authority_version=row.authority_version,
                effective_from=row.effective_from,
                effective_to=row.effective_to,
                authority_status_bucket=status_bucket,
                current_effective=current_effective,
                supersedes_authority_id=row.supersedes_authority_id,
                superseded_by_authority_id=row.superseded_by_authority_id,
                source_artifact_id=row.source_artifact_id,
                source_artifact_hash=row.source_artifact_hash,
                approval_reference=row.approval_reference,
                correction_sequence=row.correction_sequence,
                lineage_hash=row.lineage_hash,
                supersession_issue=supersession_issue,
                lineage_issue=lineage_issue,
            )
        )
    items.sort(
        key=lambda item: (
            item.market_code,
            item.instrument_code,
            item.topic_slug,
            item.relation_id,
        )
    )
    summary = StructuralRoleAuthorityAuditSummary(
        as_of_date=as_of,
        total_rows_scanned=len(rows),
        valid_role_rows=role_counts["VALID"],
        invalid_role_rows=role_counts["INVALID"],
        null_role_rows=role_counts["NULL"],
        unknown_role_rows=role_counts["INVALID"] + role_counts["NULL"],
        duplicate_active_authority_rows=duplicate_rows,
        supersession_conflict_rows=sum(1 for item in items if item.supersession_issue),
        lineage_inconsistency_rows=sum(1 for item in items if item.lineage_issue),
        status_counts=dict(sorted(status_counts.items())),
        invalid_role_values=sorted(
            invalid_values.values(), key=lambda item: item["invalid_role_value"]
        ),
        current_relation_type_counts=dict(sorted(type_counts.items())),
        current_structural_role_counts={
            role: sum(
                1
                for item in items
                if item.current_effective
                and item.role_status == "VALID"
                and item.structural_role == role
            )
            for role in sorted(ALLOWED_STRUCTURAL_ROLES)
        },
        current_relation_type_x_structural_role=dict(sorted(current_cross_tab.items())),
        database_constraint=database_constraint,
    )
    return items, summary


def all_structural_role_authority_query() -> Select:
    """Select all authority history without formal-read filtering."""

    return (
        select(InstrumentTopicRelation, Instrument, Topic, Market)
        .join(Instrument, Instrument.id == InstrumentTopicRelation.instrument_id)
        .join(Topic, Topic.id == InstrumentTopicRelation.topic_id)
        .join(Market, Market.id == Instrument.market_id)
        .order_by(
            Market.code,
            Instrument.instrument_code,
            Topic.slug,
            InstrumentTopicRelation.valid_from,
            InstrumentTopicRelation.id,
        )
    )


def read_structural_role_authority_audit(
    session: Session, as_of: date
) -> tuple[list[StructuralRoleAuthorityAuditItem], StructuralRoleAuthorityAuditSummary]:
    rows = tuple(
        AuditRelation(
            relation_id=str(relation.id),
            instrument_id=str(relation.instrument_id),
            instrument_code=instrument.instrument_code,
            instrument_type=instrument.instrument_type,
            instrument_active=instrument.is_active,
            instrument_valid_from=instrument.valid_from,
            instrument_valid_to=instrument.valid_to,
            market_code=market.code,
            market_active=market.is_active,
            topic_id=str(relation.topic_id),
            topic_slug=topic.slug,
            topic_status=topic.status,
            topic_valid_from=topic.valid_from,
            topic_valid_to=topic.valid_to,
            relation_type=relation.relation_type,
            structural_role=relation.structural_role,
            approval_state=relation.approval_state,
            authority_version=relation.authority_version,
            effective_from=relation.valid_from,
            effective_to=relation.valid_to,
            supersedes_authority_id=(
                str(relation.supersedes_authority_id)
                if relation.supersedes_authority_id is not None
                else None
            ),
            superseded_by_authority_id=(
                str(relation.superseded_by_authority_id)
                if relation.superseded_by_authority_id is not None
                else None
            ),
            source_artifact_id=relation.source_artifact_id,
            source_artifact_hash=relation.source_artifact_hash,
            approval_reference=relation.approval_reference,
            correction_sequence=relation.correction_sequence,
            lineage_hash=relation.lineage_hash,
        )
        for relation, instrument, topic, market in session.execute(
            all_structural_role_authority_query()
        ).all()
    )
    return audit_relations(rows, as_of, _database_constraint_status(session))


__all__ = [
    "AuditRelation",
    "StructuralRoleAuthorityAuditItem",
    "StructuralRoleAuthorityAuditPage",
    "StructuralRoleAuthorityAuditSummary",
    "all_structural_role_authority_query",
    "audit_relations",
    "read_structural_role_authority_audit",
]
