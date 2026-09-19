"""Read and validate the governed DEC-04 D001 role-importance artifact."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from .orm.models import Instrument, InstrumentTopicRelation, Market, Topic
from .orm.score_projections import TopicScoreProjection, TopicScoreProjectionMember

SCHEMA_VERSION = "topic-d001-role-importance-authority.v1"
ROLE_IMPORTANCE = {
    "CORE": Decimal("1.00"),
    "REPRESENTATIVE": Decimal("0.75"),
    "RELATED": Decimal("0.25"),
}
_ROLE_NAMES = frozenset(ROLE_IMPORTANCE)
PROJECTION_NAMESPACE = uuid.UUID("f54cc0c7-b2c2-5e89-b5e4-08bc09ad52c8")


class D001RoleImportanceAuthorityError(ValueError):
    """Raised when the governed D001 artifact cannot be trusted."""


@dataclass(frozen=True)
class D001RoleImportanceMember:
    topic_id: str
    topic_key: str
    market_code: str
    instrument_code: str
    relation_id: str
    structural_role: str
    importance: Decimal


@dataclass(frozen=True)
class D001RoleImportanceArtifact:
    payload: dict[str, Any]
    authority_version: str
    artifact_sha256: str
    effective_date: date
    approval_reference: str
    source_structural_role_authority_version: str
    source_structural_role_authority_hash: str
    members: tuple[D001RoleImportanceMember, ...]


def _hash(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise D001RoleImportanceAuthorityError(f"{field} is missing or not canonical")
    return value


def _importance(value: Any) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise D001RoleImportanceAuthorityError("importance is invalid") from exc
    if parsed not in ROLE_IMPORTANCE.values():
        raise D001RoleImportanceAuthorityError("importance is outside DEC-04 mapping")
    return parsed


def parse_artifact(payload: dict[str, Any]) -> D001RoleImportanceArtifact:
    required = {
        "schemaVersion",
        "authorityVersion",
        "artifactSha256",
        "effectiveDate",
        "approvalReference",
        "sourceStructuralRoleAuthority",
        "historicalRoleRecoverySource",
        "importancePolicy",
        "memberUniverse",
        "expectedTopicCount",
        "expectedMemberCount",
        "topics",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise D001RoleImportanceAuthorityError("artifact missing: " + ",".join(missing))
    canonical = dict(payload)
    canonical.pop("artifactSha256", None)
    digest = _hash(canonical)
    if payload["schemaVersion"] != SCHEMA_VERSION or payload["artifactSha256"] != digest:
        raise D001RoleImportanceAuthorityError("artifact schema or content hash mismatch")
    try:
        effective_date = date.fromisoformat(str(payload["effectiveDate"]))
    except ValueError as exc:
        raise D001RoleImportanceAuthorityError("effectiveDate is invalid") from exc

    source = payload["sourceStructuralRoleAuthority"]
    if not isinstance(source, dict):
        raise D001RoleImportanceAuthorityError("sourceStructuralRoleAuthority is invalid")
    source_version = _text(source.get("authorityVersion"), "source authority version")
    source_hash = _text(source.get("artifactSha256"), "source authority hash")

    recovery = payload["historicalRoleRecoverySource"]
    if (
        not isinstance(recovery, dict)
        or recovery.get("proposalState") != "PROPOSAL_ONLY_NON_AUTHORITY"
    ):
        raise D001RoleImportanceAuthorityError("historical source must remain non-authority")

    policy = payload["importancePolicy"]
    if not isinstance(policy, dict) or policy.get("roleToImportance") != {
        role: format(value, ".2f") for role, value in ROLE_IMPORTANCE.items()
    }:
        raise D001RoleImportanceAuthorityError("role-to-importance policy is not DEC-04")
    if policy.get("orderAffectsScore") is not False:
        raise D001RoleImportanceAuthorityError("member order cannot affect Score")
    if policy.get("fixedMinRequiredByFormula") is not False:
        raise D001RoleImportanceAuthorityError("fixed minimum is not authorized")
    if policy.get("fixedMaxRequiredByFormula") is not False:
        raise D001RoleImportanceAuthorityError("fixed maximum is not authorized")

    universe = payload["memberUniverse"]
    if not isinstance(universe, dict) or universe.get("mode") != "ALL_FORMAL_TOPIC_MEMBERS":
        raise D001RoleImportanceAuthorityError("member universe is not formal Topic membership")

    members: list[D001RoleImportanceMember] = []
    identities: set[tuple[str, str, str]] = set()
    topics = tuple(payload["topics"])
    if tuple(topic.get("topicId") for topic in topics) != tuple(
        sorted(topic.get("topicId") for topic in topics)
    ):
        raise D001RoleImportanceAuthorityError("Topics are not in stable persistence order")
    for topic in topics:
        topic_id = _text(topic.get("topicId"), "topicId")
        try:
            UUID(topic_id)
        except (ValueError, AttributeError) as exc:
            raise D001RoleImportanceAuthorityError("topicId is invalid") from exc
        topic_key = _text(topic.get("topicKey"), "topicKey")
        topic_members = tuple(topic.get("members", ()))
        if not topic_members:
            raise D001RoleImportanceAuthorityError("formal Topic has no members")
        member_order = tuple(
            (item.get("marketCode"), item.get("instrumentCode"), item.get("relationId"))
            for item in topic_members
        )
        if member_order != tuple(sorted(member_order)):
            raise D001RoleImportanceAuthorityError(
                "Topic members are not in stable persistence order"
            )
        for item in topic_members:
            market_code = _text(item.get("marketCode"), "marketCode")
            instrument_code = _text(item.get("instrumentCode"), "instrumentCode")
            relation_id = _text(item.get("relationId"), "relationId")
            structural_role = _text(item.get("structuralRole"), "structuralRole")
            if structural_role not in _ROLE_NAMES:
                raise D001RoleImportanceAuthorityError("member structural role is invalid")
            if item.get("roleAuthorityVersion") != source_version:
                raise D001RoleImportanceAuthorityError("member role authority version mismatch")
            key = (topic_id, market_code, instrument_code)
            if key in identities:
                raise D001RoleImportanceAuthorityError("duplicate Topic/instrument member")
            identities.add(key)
            actual = _importance(item.get("importance"))
            if actual != ROLE_IMPORTANCE[structural_role]:
                raise D001RoleImportanceAuthorityError("member importance does not match role")
            members.append(
                D001RoleImportanceMember(
                    topic_id,
                    topic_key,
                    market_code,
                    instrument_code,
                    relation_id,
                    structural_role,
                    actual,
                )
            )

    expected_topics = int(payload["expectedTopicCount"])
    expected_members = int(payload["expectedMemberCount"])
    if len(topics) != expected_topics or len(members) != expected_members:
        raise D001RoleImportanceAuthorityError("artifact counts do not match contract")
    if len({member.topic_id for member in members}) != expected_topics:
        raise D001RoleImportanceAuthorityError("artifact does not cover expected Topics")
    return D001RoleImportanceArtifact(
        payload=payload,
        authority_version=_text(payload["authorityVersion"], "authorityVersion"),
        artifact_sha256=digest,
        effective_date=effective_date,
        approval_reference=_text(payload["approvalReference"], "approvalReference"),
        source_structural_role_authority_version=source_version,
        source_structural_role_authority_hash=source_hash,
        members=tuple(members),
    )


def load_artifact(path: Path) -> D001RoleImportanceArtifact:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise D001RoleImportanceAuthorityError(f"cannot read artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise D001RoleImportanceAuthorityError("artifact root must be an object")
    return parse_artifact(payload)


def _target_guard(
    session: Session, artifact: D001RoleImportanceArtifact, expected_database: str
) -> None:
    if artifact.payload.get("targetEnvironment") != "production":
        raise D001RoleImportanceAuthorityError("artifact target is not production")
    if session.bind is None or session.bind.dialect.name != "postgresql":
        raise D001RoleImportanceAuthorityError("D001 materialization requires PostgreSQL")
    actual = session.execute(text("select current_database()")).scalar_one()
    if actual != expected_database:
        raise D001RoleImportanceAuthorityError("database identity mismatch")


def materialize_d001_projections(
    session: Session,
    artifact: D001RoleImportanceArtifact,
    *,
    dry_run: bool,
    expected_database: str,
    operator: str,
    confirmation: str | None = None,
) -> dict[str, Any]:
    """Materialize all formal Topic members into the append-only D001 read model.

    This is a governed runtime operation.  It resolves only identities already
    present in the canonical database and never derives membership from market
    data, rankings, or an AI classifier.
    """

    _target_guard(session, artifact, expected_database)
    if not operator.strip():
        raise D001RoleImportanceAuthorityError("operator identity is required")
    required = f"MATERIALIZE:{artifact.authority_version}:{artifact.artifact_sha256}"
    if not dry_run and confirmation != required:
        raise D001RoleImportanceAuthorityError("exact materialization confirmation is required")
    if session.in_transaction():
        session.rollback()

    grouped: dict[
        str, list[tuple[D001RoleImportanceMember, InstrumentTopicRelation, Instrument]]
    ] = {}
    with session.begin():
        for item in artifact.members:
            topic_id = UUID(item.topic_id)
            relation_id = UUID(item.relation_id)
            resolved = list(
                session.execute(
                    select(InstrumentTopicRelation, Instrument)
                    .join(Instrument, Instrument.id == InstrumentTopicRelation.instrument_id)
                    .join(Market, Market.id == Instrument.market_id)
                    .where(
                        InstrumentTopicRelation.id == relation_id,
                        InstrumentTopicRelation.topic_id == topic_id,
                        Market.code == item.market_code,
                        Instrument.instrument_code == item.instrument_code,
                    )
                    .with_for_update()
                )
            )
            if len(resolved) != 1:
                raise D001RoleImportanceAuthorityError(
                    "member identity does not resolve exactly once: "
                    f"{item.topic_id}/{item.instrument_code}"
                )
            relation, instrument = resolved[0]
            if relation.structural_role != item.structural_role:
                raise D001RoleImportanceAuthorityError("runtime role conflicts with D001 artifact")
            if relation.authority_version != artifact.source_structural_role_authority_version:
                raise D001RoleImportanceAuthorityError("runtime role authority version mismatch")
            if relation.source_artifact_hash != artifact.source_structural_role_authority_hash:
                raise D001RoleImportanceAuthorityError("runtime role authority hash mismatch")
            if relation.approval_state != "APPROVED":
                raise D001RoleImportanceAuthorityError("runtime structural role is not APPROVED")
            if relation.valid_from > artifact.effective_date or (
                relation.valid_to is not None and relation.valid_to < artifact.effective_date
            ):
                raise D001RoleImportanceAuthorityError(
                    "runtime role is outside D001 effective date"
                )
            if (
                instrument.valid_from is not None
                and instrument.valid_from > artifact.effective_date
            ):
                raise D001RoleImportanceAuthorityError("runtime instrument is not effective")
            if instrument.valid_to is not None and instrument.valid_to < artifact.effective_date:
                raise D001RoleImportanceAuthorityError("runtime instrument is obsolete")
            grouped.setdefault(item.topic_id, []).append((item, relation, instrument))

        created = 0
        unchanged = 0
        for topic_id_text, members in grouped.items():
            topic_id = UUID(topic_id_text)
            topic = session.get(Topic, topic_id, with_for_update=True)
            if topic is None or topic.status in {"DISABLED", "RETIRED"}:
                raise D001RoleImportanceAuthorityError("obsolete or missing Topic in runtime")
            projection_id = f"d001:{artifact.authority_version}:{topic_id_text}"
            existing = session.scalar(
                select(TopicScoreProjection)
                .options(selectinload(TopicScoreProjection.members))
                .where(TopicScoreProjection.projection_id == projection_id)
                .with_for_update()
            )
            if existing is not None:
                if (
                    existing.projection_version != artifact.authority_version
                    or existing.effective_from != artifact.effective_date
                    or existing.approval_state != "APPROVED"
                    or len(existing.members) != len(members)
                ):
                    raise D001RoleImportanceAuthorityError("existing D001 projection conflicts")
                expected_members = {
                    (str(instrument.id), str(relation.id)): ROLE_IMPORTANCE[item.structural_role]
                    for item, relation, instrument in members
                }
                actual_members = {
                    (str(member.instrument_id), str(member.structural_role_authority_id)):
                    Decimal(str(member.score_importance))
                    for member in existing.members
                }
                if actual_members != expected_members:
                    raise D001RoleImportanceAuthorityError(
                        "existing D001 projection members conflict"
                    )
                unchanged += 1
                continue
            conflicting = session.scalar(
                select(TopicScoreProjection).where(
                    TopicScoreProjection.topic_id == topic_id,
                    TopicScoreProjection.projection_version == artifact.authority_version,
                    TopicScoreProjection.effective_from == artifact.effective_date,
                )
            )
            if conflicting is not None:
                raise D001RoleImportanceAuthorityError(
                    "Topic has a conflicting projection identity"
                )
            projection = TopicScoreProjection(
                id=uuid.uuid5(PROJECTION_NAMESPACE, projection_id),
                topic_id=topic_id,
                projection_id=projection_id,
                projection_version=artifact.authority_version,
                effective_from=artifact.effective_date,
                effective_to=None,
                approval_state="APPROVED",
                approval_reference=artifact.approval_reference,
                source_structural_role_authority_id=(
                    f"structural-role-authority:{artifact.source_structural_role_authority_version}"
                ),
                source_structural_role_authority_version=artifact.source_structural_role_authority_version,
                projection_lineage={
                    "authorityVersion": artifact.authority_version,
                    "artifactSha256": artifact.artifact_sha256,
                    "memberUniverse": "ALL_FORMAL_TOPIC_MEMBERS",
                    "operator": operator,
                },
                lineage_hash=_hash({
                    "artifactSha256": artifact.artifact_sha256,
                    "projectionId": projection_id,
                    "topicId": topic_id_text,
                }),
                correction_sequence=0,
            )
            for item, relation, instrument in members:
                projection.members.append(
                    TopicScoreProjectionMember(
                        id=uuid.uuid5(
                            PROJECTION_NAMESPACE,
                            f"{projection_id}:{instrument.id}:{relation.id}",
                        ),
                        instrument_id=instrument.id,
                        structural_role_authority_id=relation.id,
                        structural_role_authority_version=artifact.source_structural_role_authority_version,
                        score_importance=ROLE_IMPORTANCE[item.structural_role],
                        member_lineage={
                            "relationId": item.relation_id,
                            "structuralRole": item.structural_role,
                            "importance": format(ROLE_IMPORTANCE[item.structural_role], ".2f"),
                            "authorityVersion": artifact.source_structural_role_authority_version,
                            "d001ArtifactSha256": artifact.artifact_sha256,
                        },
                    )
                )
            session.add(projection)
            created += 1

        session.flush()
        if not dry_run:
            readback = session.scalars(
                select(TopicScoreProjection)
                .options(selectinload(TopicScoreProjection.members))
                .where(TopicScoreProjection.projection_version == artifact.authority_version)
            ).all()
            readback_by_topic = {str(row.topic_id): row for row in readback}
            for topic_id_text, members in grouped.items():
                row = readback_by_topic.get(topic_id_text)
                if row is None or len(row.members) != len(members):
                    raise D001RoleImportanceAuthorityError(
                        "D001 post-materialization readback mismatch"
                    )
                expected_members = {
                    (str(instrument.id), str(relation.id)): ROLE_IMPORTANCE[item.structural_role]
                    for item, relation, instrument in members
                }
                actual_members = {
                    (str(member.instrument_id), str(member.structural_role_authority_id)):
                    Decimal(str(member.score_importance))
                    for member in row.members
                }
                if actual_members != expected_members:
                    raise D001RoleImportanceAuthorityError(
                        "D001 post-materialization member readback mismatch"
                    )
        else:
            session.rollback()
    return {
        "operation": "D001_DRY_RUN_PASS" if dry_run else "D001_MATERIALIZED",
        "authorityVersion": artifact.authority_version,
        "artifactSha256": artifact.artifact_sha256,
        "topicCount": len(grouped),
        "memberCount": len(artifact.members),
        "projectionsCreated": 0 if dry_run else created,
        "projectionsUnchanged": unchanged,
        "transactional": True,
    }


__all__ = [
    "ROLE_IMPORTANCE",
    "SCHEMA_VERSION",
    "D001RoleImportanceArtifact",
    "D001RoleImportanceAuthorityError",
    "D001RoleImportanceMember",
    "load_artifact",
    "materialize_d001_projections",
    "parse_artifact",
]
