#!/usr/bin/env python3
"""Bootstrap explicit Owner-approved relation-weight authority rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import uuid
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, text

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_MIGRATION_HEAD = "0046_task_stock_maint_relation_weight_authority_001d"
TASK_ID = "TASK-RELATION-WEIGHT-INITIAL-AUTHORITY-BOOTSTRAP-001"
AUTHORITY_VERSION = "relation-weight-authority-20260924.v1"
SOURCE_KIND = "OWNER_APPROVED_INITIAL_BOOTSTRAP"
APPROVAL_STATE = "APPROVED"
OWNER_APPROVAL_CONFIRMATION = "APPROVED_TO_CREATE_INITIAL_RELATION_WEIGHT_AUTHORITY_ROWS"
PRIMARY_WEIGHT = Decimal("1.0")
SECONDARY_WEIGHT = Decimal("0.5")
PRIMARY_MIN = Decimal("0.5")
PRIMARY_MAX = Decimal("2.0")
SECONDARY_MIN = Decimal("0.3")
SECONDARY_MAX = Decimal("0.8")
MIN_EFFECTIVE_DATE = date(2026, 9, 24)
UUID_NAMESPACE = uuid.UUID("f3b3c27d-0d36-4c09-8f35-2dd0b9152f2b")
DEFAULT_ARTIFACT_ROOT = Path(
    r"E:\topicpilot-artifacts\relation-weight-initial-authority-bootstrap-001"
)
CURRENT_EFFECTIVE_DATE = datetime.now(ZoneInfo("Asia/Taipei")).date()


@dataclass(frozen=True)
class EligibleRelation:
    relation_id: str
    instrument_id: str
    topic_id: str
    market: str
    instrument_code: str
    topic_slug: str
    topic_name: str
    relation_type: str


@dataclass(frozen=True)
class ExistingAuthority:
    authority_id: str
    relation_id: str
    relation_type: str
    weight: Decimal
    approval_state: str
    effective_from: date
    effective_to: date | None
    authority_version: str
    source_kind: str
    source_artifact_id: str | None
    correction_sequence: int
    created_at: Any


@dataclass(frozen=True)
class BootstrapPlanRow:
    relation: EligibleRelation
    current_authority: ExistingAuthority | None
    proposed_weight: Decimal | None
    operation: str
    effective_from: date

    def as_dict(self) -> dict[str, Any]:
        authority = self.current_authority
        return {
            "RELATION_ID": self.relation.relation_id,
            "MARKET": self.relation.market,
            "INSTRUMENT_CODE": self.relation.instrument_code,
            "INSTRUMENT_ID": self.relation.instrument_id,
            "TOPIC_SLUG": self.relation.topic_slug,
            "TOPIC_NAME": self.relation.topic_name,
            "TOPIC_ID": self.relation.topic_id,
            "RELATION_TYPE": self.relation.relation_type,
            "CURRENT_AUTHORITY_ID": authority.authority_id if authority else "",
            "CURRENT_AUTHORITY_STATE": authority.approval_state if authority else "",
            "CURRENT_WEIGHT": str(authority.weight) if authority else "",
            "PROPOSED_WEIGHT": str(self.proposed_weight) if self.proposed_weight else "",
            "PROPOSED_SOURCE": SOURCE_KIND if self.proposed_weight else "",
            "PROPOSED_AUTHORITY_STATUS": APPROVAL_STATE if self.proposed_weight else "",
            "PROPOSED_EFFECTIVE_DATE": (
                self.effective_from.isoformat() if self.proposed_weight else ""
            ),
            "OPERATION": self.operation,
        }

def _as_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _hash_payload(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _authority_id(relation_id: str, effective_from: date) -> uuid.UUID:
    return uuid.uuid5(
        UUID_NAMESPACE,
        f"{relation_id}|{AUTHORITY_VERSION}|{effective_from.isoformat()}|0",
    )


def _lineage_hash(
    relation: EligibleRelation,
    weight: Decimal,
    effective_from: date,
    source_artifact_hash: str,
) -> str:
    return _hash_payload(
        {
            "relationId": relation.relation_id,
            "instrumentId": relation.instrument_id,
            "topicId": relation.topic_id,
            "relationType": relation.relation_type,
            "weight": str(weight),
            "approvalState": APPROVAL_STATE,
            "effectiveFrom": effective_from.isoformat(),
            "authorityVersion": AUTHORITY_VERSION,
            "sourceKind": SOURCE_KIND,
            "sourceArtifactHash": source_artifact_hash,
        }
    )


def _weight_for(relation_type: str) -> Decimal:
    if relation_type == "PRIMARY":
        return PRIMARY_WEIGHT
    if relation_type == "SECONDARY":
        return SECONDARY_WEIGHT
    raise ValueError(f"unsupported relation type: {relation_type}")


def _validate_policy(effective_from: date) -> None:
    if effective_from < MIN_EFFECTIVE_DATE:
        raise ValueError(f"effective_from cannot precede {MIN_EFFECTIVE_DATE.isoformat()}")
    if not PRIMARY_MIN <= PRIMARY_WEIGHT <= PRIMARY_MAX:
        raise ValueError("PRIMARY initial weight is outside the formal range")
    if not SECONDARY_MIN <= SECONDARY_WEIGHT <= SECONDARY_MAX:
        raise ValueError("SECONDARY initial weight is outside the formal range")


def build_bootstrap_plan(
    relations: Iterable[EligibleRelation],
    authorities: Iterable[ExistingAuthority],
    effective_from: date = CURRENT_EFFECTIVE_DATE,
) -> tuple[BootstrapPlanRow, ...]:
    latest: dict[str, ExistingAuthority] = {}
    for authority in authorities:
        previous = latest.get(authority.relation_id)
        if previous is None or (
            authority.effective_from,
            authority.correction_sequence,
            str(authority.created_at),
        ) > (
            previous.effective_from,
            previous.correction_sequence,
            str(previous.created_at),
        ):
            latest[authority.relation_id] = authority
    plan = []
    for relation in sorted(
        relations,
        key=lambda item: (
            item.market,
            item.instrument_code,
            item.topic_slug,
            item.relation_type,
            item.relation_id,
        ),
    ):
        existing = latest.get(relation.relation_id)
        plan.append(
            BootstrapPlanRow(
                relation=relation,
                current_authority=existing,
                proposed_weight=None if existing else _weight_for(relation.relation_type),
                operation="SKIP_EXISTING_AUTHORITY" if existing else "CREATE_INITIAL_AUTHORITY",
                effective_from=effective_from,
            )
        )
    return tuple(plan)


RELATION_SQL = text(
    """
    SELECT
        r.id AS relation_id,
        r.instrument_id,
        r.topic_id,
        m.code AS market,
        i.instrument_code,
        t.slug AS topic_slug,
        t.name AS topic_name,
        r.relation_type
    FROM topicpilot.instrument_topic_relations r
    JOIN topicpilot.instruments i ON i.id = r.instrument_id
    JOIN topicpilot.markets m ON m.id = i.market_id
    JOIN topicpilot.topics t ON t.id = r.topic_id
    WHERE r.relation_type IN ('PRIMARY', 'SECONDARY')
      AND r.valid_from <= :as_of
      AND (r.valid_to IS NULL OR r.valid_to >= :as_of)
      AND i.is_active = TRUE
      AND (i.valid_from IS NULL OR i.valid_from <= :as_of)
      AND (i.valid_to IS NULL OR i.valid_to >= :as_of)
      AND t.status NOT IN ('DISABLED', 'RETIRED')
      AND (t.valid_from IS NULL OR t.valid_from <= :as_of)
      AND (t.valid_to IS NULL OR t.valid_to >= :as_of)
    ORDER BY m.code, i.instrument_code, t.slug, r.relation_type, r.id
    """
)

AUTHORITY_SQL = text(
    """
    SELECT
        id AS authority_id,
        relation_id,
        relation_type,
        weight,
        approval_state,
        effective_from,
        effective_to,
        authority_version,
        source_kind,
        source_artifact_id,
        correction_sequence,
        created_at
    FROM topicpilot.relation_weight_authorities
    WHERE effective_from <= :as_of
      AND (effective_to IS NULL OR effective_to >= :as_of)
    ORDER BY relation_id, effective_from DESC, correction_sequence DESC, created_at DESC
    """
)


def _read_state(connection, as_of: date) -> tuple[str, tuple[EligibleRelation, ...], tuple[ExistingAuthority, ...]]:
    revision = str(
        connection.execute(text("SELECT version_num FROM public.alembic_version LIMIT 1")).scalar()
        or ""
    )
    relation_rows = connection.execute(RELATION_SQL, {"as_of": as_of}).mappings().all()
    relations = tuple(
        EligibleRelation(
            relation_id=str(row["relation_id"]),
            instrument_id=str(row["instrument_id"]),
            topic_id=str(row["topic_id"]),
            market=str(row["market"]),
            instrument_code=str(row["instrument_code"]),
            topic_slug=str(row["topic_slug"]),
            topic_name=str(row["topic_name"]),
            relation_type=str(row["relation_type"]),
        )
        for row in relation_rows
    )
    authority_rows = connection.execute(AUTHORITY_SQL, {"as_of": as_of}).mappings().all()
    authorities = tuple(
        ExistingAuthority(
            authority_id=str(row["authority_id"]),
            relation_id=str(row["relation_id"]),
            relation_type=str(row["relation_type"]),
            weight=Decimal(str(row["weight"])),
            approval_state=str(row["approval_state"]),
            effective_from=_as_date(row["effective_from"]),
            effective_to=_as_date(row["effective_to"]) if row["effective_to"] else None,
            authority_version=str(row["authority_version"]),
            source_kind=str(row["source_kind"]),
            source_artifact_id=(str(row["source_artifact_id"]) if row["source_artifact_id"] else None),
            correction_sequence=int(row["correction_sequence"]),
            created_at=row["created_at"],
        )
        for row in authority_rows
    )
    return revision, relations, authorities


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> str:
    rows = list(rows)
    if not rows:
        raise ValueError("cannot write an empty bootstrap artifact")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_plan(path: Path, plan: tuple[BootstrapPlanRow, ...]) -> str:
    return _write_csv(path, (row.as_dict() for row in plan))


def _summary(plan: tuple[BootstrapPlanRow, ...]) -> dict[str, Any]:
    operations = Counter(row.operation for row in plan)
    relation_types = Counter(row.relation.relation_type for row in plan)
    return {
        "eligible_rows": len(plan),
        "primary_eligible": relation_types.get("PRIMARY", 0),
        "secondary_eligible": relation_types.get("SECONDARY", 0),
        "create_initial_authority": operations.get("CREATE_INITIAL_AUTHORITY", 0),
        "skip_existing_authority": operations.get("SKIP_EXISTING_AUTHORITY", 0),
        "other_relation_types": 0,
    }


def _authority_source_class(source_kind: str) -> str:
    normalized = source_kind.upper()
    if "OWNER" in normalized or "MANUAL" in normalized:
        return "OWNER_EXISTING_AUTHORITY"
    if normalized in {
        "DEFAULT_INITIALIZATION",
        "LEGACY_RECOVERED",
        "DATABASE_MAINTENANCE_EXCEL",
        "SYSTEM",
    }:
        return "SYSTEM_EXISTING_AUTHORITY"
    return "UNKNOWN_EXISTING_AUTHORITY"


def _require_database_url(explicit: str | None) -> str:
    database_url = explicit or os.environ.get("TOPICPILOT_PRODUCTION_DATABASE_URL")
    if not database_url:
        raise SystemExit(
            "PRODUCTION_DATABASE_URL_REQUIRED: set TOPICPILOT_PRODUCTION_DATABASE_URL "
            "or pass --database-url"
        )
    return database_url


def _verify_revision(revision: str) -> None:
    if revision != CANONICAL_MIGRATION_HEAD:
        raise RuntimeError(
            f"BLOCKED_MIGRATION_REQUIRED: expected {CANONICAL_MIGRATION_HEAD}, got {revision or 'UNKNOWN'}"
        )


def run_dry_run(database_url: str, artifact_root: Path, effective_from: date) -> dict[str, Any]:
    _validate_policy(effective_from)
    pre_dir = artifact_root / "pre-bootstrap"
    plan_path = artifact_root / "bootstrap-plan.csv"
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            revision, relations, authorities = _read_state(connection, effective_from)
    finally:
        engine.dispose()
    _verify_revision(revision)
    plan = build_bootstrap_plan(relations, authorities, effective_from)
    summary = _summary(plan)
    summary.update(
        {
            "migration_head": revision,
            "effective_from": effective_from.isoformat(),
            "existing_authority_rows": len(authorities),
            "existing_authority_sources": Counter(
                _authority_source_class(row.source_kind) for row in authorities
            ),
        }
    )
    if any(
        source != "OWNER_EXISTING_AUTHORITY"
        for source in summary["existing_authority_sources"]
    ) and authorities:
        summary["existing_authority_conflict"] = "OWNER_DECISION_REQUIRED"
    plan_hash = _write_plan(plan_path, plan)
    pre_dir.mkdir(parents=True, exist_ok=True)
    pre_rows = []
    for row in plan:
        payload = row.as_dict()
        payload["CURRENT_AUTHORITY_SOURCE_CLASS"] = (
            _authority_source_class(row.current_authority.source_kind)
            if row.current_authority
            else ""
        )
        pre_rows.append(payload)
    _write_csv(pre_dir / "pre-bootstrap-readback.csv", pre_rows)
    (pre_dir / "pre-bootstrap-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    (artifact_root / "bootstrap-plan.sha256").write_text(
        f"{plan_hash}  bootstrap-plan.csv\n", encoding="utf-8"
    )
    return {**summary, "plan_hash": plan_hash, "plan_path": str(plan_path)}


def _apply_insert(
    connection,
    row: BootstrapPlanRow,
    *,
    effective_from: date,
    plan_hash: str,
    approval_reference: str,
    source_artifact_id: str,
) -> None:
    if row.proposed_weight is None:
        return
    authority_id = _authority_id(row.relation.relation_id, effective_from)
    connection.execute(
        text(
            """
            INSERT INTO topicpilot.relation_weight_authorities
                (id, relation_id, instrument_id, topic_id, relation_type, weight,
                 approval_state, effective_from, effective_to, authority_version,
                 approval_reference, source_kind, source_artifact_id, source_artifact_hash,
                 source_location, proposal_reason, correction_sequence, supersedes_id,
                 lineage_hash)
            VALUES
                (:id, :relation_id, :instrument_id, :topic_id, :relation_type, :weight,
                 :approval_state, :effective_from, NULL, :authority_version,
                 :approval_reference, :source_kind, :source_artifact_id, :source_artifact_hash,
                 :source_location, :proposal_reason, 0, NULL, :lineage_hash)
            ON CONFLICT (relation_id, authority_version, effective_from, correction_sequence)
            DO NOTHING
            """
        ),
        {
            "id": authority_id,
            "relation_id": uuid.UUID(row.relation.relation_id),
            "instrument_id": uuid.UUID(row.relation.instrument_id),
            "topic_id": uuid.UUID(row.relation.topic_id),
            "relation_type": row.relation.relation_type,
            "weight": row.proposed_weight,
            "approval_state": APPROVAL_STATE,
            "effective_from": effective_from,
            "authority_version": AUTHORITY_VERSION,
            "approval_reference": approval_reference,
            "source_kind": SOURCE_KIND,
            "source_artifact_id": source_artifact_id,
            "source_artifact_hash": plan_hash,
            "source_location": source_artifact_id,
            "proposal_reason": "INITIAL_OWNER_APPROVED_RELATION_WEIGHT",
            "lineage_hash": _lineage_hash(
                row.relation, row.proposed_weight, effective_from, plan_hash
            ),
        },
    )


def run_apply(
    database_url: str,
    plan_path: Path,
    effective_from: date,
    approval_reference: str,
    confirmation: str,
) -> dict[str, Any]:
    if confirmation != OWNER_APPROVAL_CONFIRMATION:
        raise SystemExit(
            "OWNER_APPROVAL_CONFIRMATION_REQUIRED: pass the exact governed approval confirmation"
        )
    if not approval_reference.strip():
        raise SystemExit("APPROVAL_REFERENCE_REQUIRED")
    _validate_policy(effective_from)
    plan_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    with plan_path.open("r", encoding="utf-8", newline="") as handle:
        plan_rows = list(csv.DictReader(handle))
    if not plan_rows:
        raise SystemExit("BOOTSTRAP_PLAN_EMPTY")
    engine = create_engine(database_url, pool_pre_ping=True)
    created = 0
    skipped = 0
    try:
        with engine.begin() as connection:
            revision, relations, authorities = _read_state(connection, effective_from)
            _verify_revision(revision)
            current_plan = build_bootstrap_plan(relations, authorities, effective_from)
            current_by_id = {row.relation.relation_id: row for row in current_plan}
            plan_ids = {row["RELATION_ID"] for row in plan_rows}
            if plan_ids != set(current_by_id):
                raise RuntimeError("BLOCKED_TRANSACTION_SAFETY: eligible relation universe changed")
            for planned in plan_rows:
                current = current_by_id[planned["RELATION_ID"]]
                if planned["RELATION_TYPE"] != current.relation.relation_type:
                    raise RuntimeError("BLOCKED_TRANSACTION_SAFETY: relation type changed")
                if current.current_authority is not None:
                    skipped += 1
                    continue
                if planned["OPERATION"] != "CREATE_INITIAL_AUTHORITY":
                    raise RuntimeError("BLOCKED_TRANSACTION_SAFETY: plan operation mismatch")
                expected_weight = str(_weight_for(current.relation.relation_type))
                if planned["PROPOSED_WEIGHT"] != expected_weight:
                    raise RuntimeError("BLOCKED_TRANSACTION_SAFETY: proposed weight changed")
                _apply_insert(
                    connection,
                    current,
                    effective_from=effective_from,
                    plan_hash=plan_hash,
                    approval_reference=approval_reference,
                    source_artifact_id=str(plan_path),
                )
                created += 1
            expected = created
            actual = connection.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM topicpilot.relation_weight_authorities
                    WHERE source_artifact_hash=:plan_hash
                      AND source_kind=:source_kind
                      AND approval_state='APPROVED'
                    """
                ),
                {"plan_hash": plan_hash, "source_kind": SOURCE_KIND},
            ).scalar_one()
            if int(actual) < expected:
                raise RuntimeError("BLOCKED_TRANSACTION_SAFETY: inserted authority count mismatch")
    finally:
        engine.dispose()
    return {
        "status": "APPLIED" if created else "NOOP_IDEMPOTENT",
        "rows_requested": len(plan_rows),
        "rows_created": created,
        "rows_skipped_existing": skipped,
        "rows_failed": 0,
        "plan_hash": plan_hash,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("TOPICPILOT_PRODUCTION_DATABASE_URL"))
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--effective-from", default=CURRENT_EFFECTIVE_DATE.isoformat())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--approval-reference")
    parser.add_argument("--owner-approval-confirmation")
    args = parser.parse_args()
    if args.dry_run == args.apply:
        parser.error("choose exactly one of --dry-run or --apply")
    effective_from = date.fromisoformat(args.effective_from)
    database_url = _require_database_url(args.database_url)
    if args.dry_run:
        result = run_dry_run(database_url, args.artifact_root, effective_from)
    else:
        if not args.plan:
            parser.error("--apply requires --plan")
        result = run_apply(
            database_url,
            args.plan,
            effective_from,
            args.approval_reference or "",
            args.owner_approval_confirmation or "",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
