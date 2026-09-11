"""Governed activation of approved Instrument/Topic structural roles."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from topicpilot_api.orm.models import Instrument, InstrumentTopicRelation, Market, Topic

SCHEMA_VERSION = "topic-structural-role-authority.v1"
ALLOWED_ROLES = frozenset({"REPRESENTATIVE", "CORE", "RELATED"})
RELATION_NAMESPACE = uuid.UUID("da995966-4275-5fe0-9c45-8dc84ad2c3c1")


class StructuralRoleAuthorityError(RuntimeError):
    """Fail-closed structural-role authority violation."""


def _hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StructuralRoleArtifact:
    payload: dict[str, Any]
    authority_version: str
    artifact_sha256: str
    source_master_sha256: str
    target_environment: str
    target_database: str
    approval_reference: str
    effective_date: date
    rows: tuple[dict[str, Any], ...]


def parse_artifact(payload: dict[str, Any]) -> StructuralRoleArtifact:
    required = {
        "schemaVersion", "authorityVersion", "artifactSha256", "sourceMasterSha256",
        "targetEnvironment", "targetDatabase", "approvalReference", "effectiveDate", "rows",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise StructuralRoleAuthorityError(f"artifact missing: {','.join(missing)}")
    canonical = dict(payload)
    canonical.pop("artifactSha256", None)
    digest = _hash(canonical)
    if payload["schemaVersion"] != SCHEMA_VERSION or payload["artifactSha256"] != digest:
        raise StructuralRoleAuthorityError("artifact schema or content hash mismatch")
    try:
        effective_date = date.fromisoformat(str(payload["effectiveDate"]))
    except ValueError as exc:
        raise StructuralRoleAuthorityError("invalid effectiveDate") from exc
    rows = tuple(payload["rows"])
    identities: set[tuple[str, str, str]] = set()
    topics: set[UUID] = set()
    for row in rows:
        try:
            topic_id = UUID(str(row["topicId"]))
            relation_id = UUID(str(row["relationId"]))
        except (KeyError, ValueError) as exc:
            raise StructuralRoleAuthorityError("row has invalid topicId") from exc
        identity = (
            str(row.get("marketCode", "")),
            str(row.get("instrumentCode", "")),
            str(topic_id),
        )
        if not all(identity) or identity in identities:
            raise StructuralRoleAuthorityError("duplicate or incomplete relation identity")
        if row.get("structuralRole") not in ALLOWED_ROLES:
            raise StructuralRoleAuthorityError("invalid structural role")
        if row.get("approvalState") != "APPROVED":
            raise StructuralRoleAuthorityError("every role must be explicitly APPROVED")
        relation_version = str(row.get("relationVersion", ""))
        deterministic_name = (
            f"{payload['sourceMasterSha256']}:{identity[0]}:{identity[1]}:"
            f"{topic_id}:{row.get('relationType')}:{payload['effectiveDate']}"
        )
        if (
            not relation_version
            or relation_id != uuid.uuid5(RELATION_NAMESPACE, deterministic_name)
        ):
            raise StructuralRoleAuthorityError(
                "relation UUID/version is not deterministic canonical authority"
            )
        identities.add(identity)
        topics.add(topic_id)
    if len(rows) != int(payload.get("expectedRelationCount", -1)):
        raise StructuralRoleAuthorityError("relation count does not match contract")
    if len(topics) != int(payload.get("expectedLeafCount", -1)):
        raise StructuralRoleAuthorityError("Leaf count does not match contract")
    if payload["targetEnvironment"] != "production":
        raise StructuralRoleAuthorityError("artifact target must be production")
    return StructuralRoleArtifact(
        payload=payload,
        authority_version=str(payload["authorityVersion"]),
        artifact_sha256=digest,
        source_master_sha256=str(payload["sourceMasterSha256"]),
        target_environment=str(payload["targetEnvironment"]),
        target_database=str(payload["targetDatabase"]),
        approval_reference=str(payload["approvalReference"]),
        effective_date=effective_date,
        rows=rows,
    )


def load_artifact(path: Path) -> StructuralRoleArtifact:
    try:
        return parse_artifact(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StructuralRoleAuthorityError(f"cannot read artifact: {path}") from exc


def _target_guard(
    session: Session, artifact: StructuralRoleArtifact, environment: str, database: str
) -> None:
    if environment != "production" or environment != artifact.target_environment:
        raise StructuralRoleAuthorityError("runtime environment is not exact production target")
    if session.bind is None or session.bind.dialect.name != "postgresql":
        raise StructuralRoleAuthorityError("activation requires PostgreSQL")
    actual = session.execute(text("select current_database()")) .scalar_one()
    if actual != database or database != artifact.target_database:
        raise StructuralRoleAuthorityError("database identity mismatch")


def _resolve(
    session: Session, artifact: StructuralRoleArtifact
) -> list[tuple[InstrumentTopicRelation, dict[str, Any]]]:
    resolved: list[tuple[InstrumentTopicRelation, dict[str, Any]]] = []
    for item in artifact.rows:
        rows = list(session.execute(
            select(InstrumentTopicRelation, Topic)
            .join(Instrument, Instrument.id == InstrumentTopicRelation.instrument_id)
            .join(Market, Market.id == Instrument.market_id)
            .join(Topic, Topic.id == InstrumentTopicRelation.topic_id)
            .where(
                Topic.id == UUID(str(item["topicId"])),
                Market.code == item["marketCode"],
                Instrument.instrument_code == item["instrumentCode"],
                InstrumentTopicRelation.valid_from <= artifact.effective_date,
                (InstrumentTopicRelation.valid_to.is_(None))
                | (InstrumentTopicRelation.valid_to >= artifact.effective_date),
            ).with_for_update()
        ))
        if len(rows) != 1:
            raise StructuralRoleAuthorityError("relation identity does not resolve exactly once")
        relation, topic = rows[0]
        if topic.status in {"DISABLED", "RETIRED"}:
            raise StructuralRoleAuthorityError(
                "obsolete Topic cannot receive active role authority"
            )
        resolved.append((relation, item))
    if len({relation.topic_id for relation, _ in resolved}) != 107:
        raise StructuralRoleAuthorityError(
            "authority does not cover exactly 107 active Leaf topics"
        )
    return resolved


def activate(
    session: Session,
    artifact: StructuralRoleArtifact,
    *,
    dry_run: bool,
    environment: str,
    expected_database: str,
    operator: str,
    confirmation: str | None,
) -> dict[str, Any]:
    _target_guard(session, artifact, environment, expected_database)
    if not operator.strip():
        raise StructuralRoleAuthorityError("operator identity is required")
    required = f"ACTIVATE:{artifact.authority_version}:{artifact.artifact_sha256}"
    if not dry_run and confirmation != required:
        raise StructuralRoleAuthorityError("exact activation confirmation is required")
    if session.in_transaction():
        session.rollback()
    with session.begin():
        resolved = _resolve(session, artifact)
        conflicts = [
            relation for relation, item in resolved
            if relation.authority_version == artifact.authority_version
            and (relation.structural_role != item["structuralRole"]
                 or relation.source_artifact_hash != artifact.artifact_sha256)
        ]
        if conflicts:
            raise StructuralRoleAuthorityError("authority version exists with conflicting content")
        changed = 0
        if not dry_run:
            for relation, item in resolved:
                if relation.authority_version == artifact.authority_version:
                    continue
                relation.structural_role = item["structuralRole"]
                relation.approval_state = "APPROVED"
                relation.authority_version = artifact.authority_version
                relation.source_artifact_id = (
                    f"structural-role-authority:{artifact.authority_version}"
                )
                relation.source_artifact_hash = artifact.artifact_sha256
                relation.approval_reference = artifact.approval_reference
                relation.lineage_hash = _hash({
                    "artifactSha256": artifact.artifact_sha256,
                    "relationId": str(relation.id),
                    "role": item["structuralRole"],
                })
                changed += 1
            session.flush()
            readback = _resolve(session, artifact)
            if any(
                relation.structural_role != item["structuralRole"]
                or relation.approval_state != "APPROVED"
                or relation.authority_version != artifact.authority_version
                for relation, item in readback
            ):
                raise StructuralRoleAuthorityError("post-activation readback mismatch")
        else:
            session.rollback()
    return {
        "operation": "DRY_RUN_PASS" if dry_run else ("NOOP" if changed == 0 else "ACTIVATED"),
        "authorityVersion": artifact.authority_version,
        "artifactSha256": artifact.artifact_sha256,
        "relationCount": len(artifact.rows),
        "leafCount": 107,
        "rowsChanged": changed,
        "transactional": True,
    }


def materialize_missing_relations(
    session: Session,
    artifact: StructuralRoleArtifact,
    *,
    dry_run: bool,
    environment: str,
    expected_database: str,
    operator: str,
    confirmation: str | None,
) -> dict[str, Any]:
    """Append only the explicitly authorized missing canonical relations."""

    _target_guard(session, artifact, environment, expected_database)
    if not operator.strip():
        raise StructuralRoleAuthorityError("operator identity is required")
    required = f"MATERIALIZE:{artifact.authority_version}:{artifact.artifact_sha256}"
    if not dry_run and confirmation != required:
        raise StructuralRoleAuthorityError("exact materialization confirmation is required")
    if session.in_transaction():
        session.rollback()
    with session.begin():
        inserts: list[tuple[dict[str, Any], Instrument, Topic]] = []
        existing_count = 0
        for item in artifact.rows:
            instrument_rows = list(session.scalars(
                select(Instrument)
                .join(Market, Market.id == Instrument.market_id)
                .where(
                    Market.code == item["marketCode"],
                    Instrument.instrument_code == item["instrumentCode"],
                )
            ))
            topic_rows = list(session.scalars(
                select(Topic).where(Topic.id == UUID(str(item["topicId"])))
            ))
            if len(instrument_rows) != 1 or len(topic_rows) != 1:
                raise StructuralRoleAuthorityError(
                    "ambiguous canonical Instrument or Topic identity"
                )
            instrument, topic = instrument_rows[0], topic_rows[0]
            existing = list(session.scalars(
                select(InstrumentTopicRelation).where(
                    InstrumentTopicRelation.instrument_id == instrument.id,
                    InstrumentTopicRelation.topic_id == topic.id,
                )
            ))
            if len(existing) > 1:
                raise StructuralRoleAuthorityError("duplicate Production relation authority")
            if existing:
                current = existing[0]
                if current.relation_type != item["relationType"]:
                    raise StructuralRoleAuthorityError(
                        "existing relation conflicts with approved relation type"
                    )
                existing_count += 1
                continue
            if session.get(InstrumentTopicRelation, UUID(str(item["relationId"]))) is not None:
                raise StructuralRoleAuthorityError("deterministic relation UUID collision")
            inserts.append((item, instrument, topic))
        reconciliation = (existing_count, len(inserts))
        if reconciliation not in {(440, 778), (1218, 0)}:
            raise StructuralRoleAuthorityError(
                "relation reconciliation is neither the approved 440 existing plus "
                "778 inserts nor the idempotent 1218 existing plus 0 inserts state"
            )
        if not dry_run:
            for item, instrument, topic in inserts:
                lineage = {
                    "authorityVersion": artifact.authority_version,
                    "artifactSha256": artifact.artifact_sha256,
                    "sourceMasterSha256": artifact.source_master_sha256,
                    "sourceReference": item["sourceReference"],
                    "operator": operator,
                }
                session.add(InstrumentTopicRelation(
                    id=UUID(str(item["relationId"])),
                    instrument_id=instrument.id,
                    topic_id=topic.id,
                    relation_type=item["relationType"],
                    relation_version=item["relationVersion"],
                    valid_from=artifact.effective_date,
                    valid_to=None,
                    relationship_metadata={"canonicalAuthority": lineage},
                    structural_role=item["structuralRole"],
                    approval_state="APPROVED",
                    authority_version=artifact.authority_version,
                    source_artifact_id=(
                        f"structural-role-authority:{artifact.authority_version}"
                    ),
                    source_artifact_hash=artifact.artifact_sha256,
                    approval_reference=artifact.approval_reference,
                    lineage_hash=_hash({**lineage, "relationId": item["relationId"]}),
                ))
            session.flush()
        else:
            session.rollback()
    return {
        "operation": (
            "RELATION_DRY_RUN_PASS"
            if dry_run
            else "RELATIONS_MATERIALIZED" if inserts else "RELATIONS_ALREADY_MATERIALIZED"
        ),
        "existingRelationsPreserved": existing_count,
        "newRelationsCreated": 0 if dry_run else len(inserts),
        "expectedInserts": len(inserts),
        "expectedUpdates": 0,
        "expectedDeletes": 0,
        "expectedDuplicates": 0,
        "ambiguousRelations": 0,
        "transactional": True,
    }
