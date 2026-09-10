"""Protected, versioned Topic authority activation boundary.

The JSON artifact is the only write authority accepted here.  Validation and
dry-run are read-only; activation owns one transaction and records an
append-only lineage row after post-write readback succeeds.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from topicpilot_api.orm import TopicAuthorityActivation
from topicpilot_api.orm.models import Topic, TopicHierarchy

SCHEMA_VERSION = "topic-authority-activation.v1"
ACTIVE_TOPIC_STATUSES = frozenset({"ACTIVE", "ENABLED", "PUBLISHED"})
INACTIVE_TOPIC_STATUSES = frozenset({"DISABLED", "RETIRED"})
ALLOWED_ACTIONS = frozenset({"PRESERVE", "RENAME", "CREATE", "RETIRE"})
LEVELS = frozenset({"PARENT", "LEAF"})


class TopicAuthorityActivationError(RuntimeError):
    """Fail-closed activation contract violation."""


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def artifact_hash(payload: dict[str, Any]) -> str:
    canonical = dict(payload)
    canonical.pop("artifactSha256", None)
    return _canonical_hash(canonical)


@dataclass(frozen=True)
class ActivationArtifact:
    payload: dict[str, Any]
    activation_version: str
    artifact_sha256: str
    source_master_sha256: str
    source_revision: str
    target_environment: str
    target_database: str
    approval_reference: str
    effective_date: date
    expected_parent_count: int
    expected_leaf_count: int
    topics: tuple[dict[str, Any], ...]
    hierarchy: tuple[dict[str, Any], ...]
    lifecycle_scope: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ActivationResult:
    operation: str
    activation_version: str
    artifact_sha256: str
    dry_run: bool
    active_parent_count: int
    active_leaf_count: int
    lifecycle_scope_count: int
    readback_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "activationVersion": self.activation_version,
            "artifactSha256": self.artifact_sha256,
            "dryRun": self.dry_run,
            "activeParentCount": self.active_parent_count,
            "activeLeafCount": self.active_leaf_count,
            "lifecycleScopeCount": self.lifecycle_scope_count,
            "readbackSha256": self.readback_sha256,
            "transactional": True,
            "idempotent": True,
        }


def _result(
    operation: str,
    artifact: ActivationArtifact,
    dry_run: bool,
    readback: dict[str, Any],
) -> ActivationResult:
    return ActivationResult(
        operation=operation,
        activation_version=artifact.activation_version,
        artifact_sha256=artifact.artifact_sha256,
        dry_run=dry_run,
        active_parent_count=readback["activeParentCount"],
        active_leaf_count=readback["activeLeafCount"],
        lifecycle_scope_count=readback["lifecycleScopeCount"],
        readback_sha256=readback["readbackSha256"],
    )


def load_activation_artifact(path: Path) -> ActivationArtifact:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TopicAuthorityActivationError(f"cannot read activation artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise TopicAuthorityActivationError("activation artifact must be a JSON object")
    return parse_activation_artifact(payload)


def parse_activation_artifact(payload: dict[str, Any]) -> ActivationArtifact:
    required = {
        "schemaVersion",
        "activationVersion",
        "artifactSha256",
        "sourceMasterSha256",
        "sourceRevision",
        "targetEnvironment",
        "targetDatabase",
        "approvalReference",
        "effectiveDate",
        "expectedParentCount",
        "expectedLeafCount",
        "topics",
        "hierarchy",
        "lifecycleScope",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise TopicAuthorityActivationError(f"activation artifact missing: {','.join(missing)}")
    if payload["schemaVersion"] != SCHEMA_VERSION:
        raise TopicAuthorityActivationError("unsupported activation artifact schema")
    digest = artifact_hash(payload)
    if payload["artifactSha256"] != digest:
        raise TopicAuthorityActivationError("activation artifact content hash mismatch")
    for field in ("sourceMasterSha256", "sourceRevision"):
        value = str(payload[field])
        if len(value) not in (40, 64) or any(char not in "0123456789abcdef" for char in value):
            raise TopicAuthorityActivationError(f"invalid {field}")
    try:
        effective_date = date.fromisoformat(str(payload["effectiveDate"]))
    except ValueError as exc:
        raise TopicAuthorityActivationError("invalid effectiveDate") from exc
    topics = tuple(payload["topics"])
    hierarchy = tuple(payload["hierarchy"])
    scope = tuple(payload["lifecycleScope"])
    if not all(isinstance(row, dict) for row in (*topics, *hierarchy, *scope)):
        raise TopicAuthorityActivationError("activation collections must contain objects")
    artifact = ActivationArtifact(
        payload=payload,
        activation_version=str(payload["activationVersion"]),
        artifact_sha256=digest,
        source_master_sha256=str(payload["sourceMasterSha256"]),
        source_revision=str(payload["sourceRevision"]),
        target_environment=str(payload["targetEnvironment"]),
        target_database=str(payload["targetDatabase"]),
        approval_reference=str(payload["approvalReference"]),
        effective_date=effective_date,
        expected_parent_count=int(payload["expectedParentCount"]),
        expected_leaf_count=int(payload["expectedLeafCount"]),
        topics=topics,
        hierarchy=hierarchy,
        lifecycle_scope=scope,
    )
    validate_artifact(artifact)
    return artifact


def validate_artifact(artifact: ActivationArtifact) -> None:
    if not artifact.activation_version or len(artifact.activation_version) > 96:
        raise TopicAuthorityActivationError("invalid activationVersion")
    if artifact.target_environment != "production":
        raise TopicAuthorityActivationError("artifact targetEnvironment must be production")
    if not artifact.target_database or not artifact.approval_reference:
        raise TopicAuthorityActivationError("targetDatabase and approvalReference are required")

    topic_ids: set[UUID] = set()
    slugs: set[str] = set()
    active_by_id: dict[UUID, dict[str, Any]] = {}
    levels: dict[UUID, str] = {}
    for row in artifact.topics:
        try:
            topic_id = UUID(str(row["topicId"]))
        except (KeyError, ValueError) as exc:
            raise TopicAuthorityActivationError("every topic requires a valid topicId") from exc
        slug = str(row.get("slug", "")).strip()
        action = str(row.get("action", ""))
        level = str(row.get("level", ""))
        status = str(row.get("status", ""))
        if topic_id in topic_ids or (slug and slug in slugs):
            raise TopicAuthorityActivationError("duplicate Topic identity in artifact")
        if action not in ALLOWED_ACTIONS or level not in LEVELS:
            raise TopicAuthorityActivationError("invalid Topic action or ontology level")
        if action == "CREATE" and row.get("creationAuthorized") is not True:
            raise TopicAuthorityActivationError("Topic creation lacks explicit artifact authority")
        if action != "CREATE" and not row.get("expectedCurrentSlug"):
            raise TopicAuthorityActivationError(
                "existing Topic action requires expectedCurrentSlug"
            )
        if status not in ACTIVE_TOPIC_STATUSES | INACTIVE_TOPIC_STATUSES:
            raise TopicAuthorityActivationError("invalid Topic status")
        topic_ids.add(topic_id)
        if slug:
            slugs.add(slug)
        levels[topic_id] = level
        if status in ACTIVE_TOPIC_STATUSES:
            active_by_id[topic_id] = row

    edges: set[tuple[UUID, UUID]] = set()
    child_ids: set[UUID] = set()
    for row in artifact.hierarchy:
        try:
            parent_id = UUID(str(row["parentTopicId"]))
            child_id = UUID(str(row["childTopicId"]))
        except (KeyError, ValueError) as exc:
            raise TopicAuthorityActivationError("invalid hierarchy Topic identity") from exc
        edge = (parent_id, child_id)
        if edge in edges or parent_id == child_id:
            raise TopicAuthorityActivationError("duplicate or self-referencing hierarchy edge")
        if parent_id not in active_by_id or child_id not in active_by_id:
            raise TopicAuthorityActivationError("hierarchy references inactive or unknown Topic")
        if levels[parent_id] != "PARENT" or levels[child_id] != "LEAF":
            raise TopicAuthorityActivationError("Parent/Leaf hierarchy invariant failed")
        if child_id in child_ids:
            raise TopicAuthorityActivationError("Leaf has more than one active Parent")
        edges.add(edge)
        child_ids.add(child_id)

    parents = {
        topic_id
        for topic_id, level in levels.items()
        if level == "PARENT" and topic_id in active_by_id
    }
    leaves = {
        topic_id
        for topic_id, level in levels.items()
        if level == "LEAF" and topic_id in active_by_id
    }
    if (
        len(parents) != artifact.expected_parent_count
        or len(leaves) != artifact.expected_leaf_count
    ):
        raise TopicAuthorityActivationError("active Parent/Leaf count does not match contract")
    if child_ids != leaves:
        raise TopicAuthorityActivationError("every active Leaf must have exactly one Parent")

    research_ids: set[str] = set()
    canonical_ids: set[UUID] = set()
    for row in artifact.lifecycle_scope:
        research = str(row.get("researchIdentity", "")).strip()
        try:
            target = UUID(str(row["canonicalTopicId"]))
        except (KeyError, ValueError) as exc:
            raise TopicAuthorityActivationError("invalid lifecycle canonicalTopicId") from exc
        if not research or research in research_ids or target in canonical_ids:
            raise TopicAuthorityActivationError("duplicate Lifecycle mapping identity")
        if target not in leaves:
            if target in parents:
                raise TopicAuthorityActivationError("Parent cannot enter Lifecycle Leaf scope")
            raise TopicAuthorityActivationError(
                "obsolete or inactive Topic cannot enter Lifecycle scope"
            )
        research_ids.add(research)
        canonical_ids.add(target)
    if len(canonical_ids) != artifact.expected_leaf_count or canonical_ids != leaves:
        raise TopicAuthorityActivationError(
            "Lifecycle mapping does not resolve exact active Leaf scope"
        )


def validate_target(
    session: Session,
    artifact: ActivationArtifact,
    *,
    runtime_environment: str,
    expected_database: str,
) -> None:
    if runtime_environment != "production" or runtime_environment != artifact.target_environment:
        raise TopicAuthorityActivationError("runtime environment is not exact production target")
    if session.bind is None or session.bind.dialect.name != "postgresql":
        raise TopicAuthorityActivationError("Topic authority activation requires PostgreSQL")
    actual_database = session.execute(text("select current_database()")).scalar_one()
    if expected_database != artifact.target_database or actual_database != artifact.target_database:
        raise TopicAuthorityActivationError("database identity does not match activation artifact")


def _existing_topics(session: Session) -> dict[UUID, Topic]:
    return {row.id: row for row in session.scalars(select(Topic).with_for_update())}


def _existing_activation(
    session: Session, activation_version: str
) -> TopicAuthorityActivation | None:
    return session.scalar(
        select(TopicAuthorityActivation)
        .where(TopicAuthorityActivation.activation_version == activation_version)
        .with_for_update()
    )


def _preflight_database(session: Session, artifact: ActivationArtifact) -> None:
    existing = _existing_topics(session)
    artifact_ids = {UUID(str(row["topicId"])) for row in artifact.topics}
    for row in artifact.topics:
        topic_id = UUID(str(row["topicId"]))
        current = existing.get(topic_id)
        action = row["action"]
        if action == "CREATE":
            if current is not None:
                raise TopicAuthorityActivationError("CREATE Topic UUID already exists")
            continue
        if current is None or current.slug != row["expectedCurrentSlug"]:
            raise TopicAuthorityActivationError("existing Topic UUID/slug precondition mismatch")
    active_unmanaged = [
        row.slug
        for row in existing.values()
        if row.status not in INACTIVE_TOPIC_STATUSES and row.id not in artifact_ids
    ]
    if active_unmanaged:
        raise TopicAuthorityActivationError("artifact omits active Topic identities")


def _apply_topics(session: Session, artifact: ActivationArtifact) -> None:
    existing = _existing_topics(session)
    for row in artifact.topics:
        topic_id = UUID(str(row["topicId"]))
        topic = existing.get(topic_id)
        if topic is None:
            topic = Topic(id=topic_id, slug=row["slug"], name=row["name"])
            session.add(topic)
        topic.slug = row["slug"]
        topic.name = row["name"]
        topic.description = row.get("description")
        topic.status = row["status"]
        topic.dictionary_version = artifact.activation_version
        topic.valid_from = (
            artifact.effective_date if row["status"] in ACTIVE_TOPIC_STATUSES else topic.valid_from
        )
        topic.valid_to = (
            artifact.effective_date - timedelta(days=1)
            if row["status"] in INACTIVE_TOPIC_STATUSES
            else None
        )
        metadata = dict(topic.display_metadata or {})
        metadata["topicAuthorityActivation"] = {
            "activationVersion": artifact.activation_version,
            "artifactSha256": artifact.artifact_sha256,
            "approvalReference": artifact.approval_reference,
            "action": row["action"],
            "ontologyLevel": row["level"],
        }
        topic.display_metadata = metadata
    session.flush()


def _apply_hierarchy(session: Session, artifact: ActivationArtifact) -> None:
    desired = {
        (UUID(str(row["parentTopicId"])), UUID(str(row["childTopicId"])))
        for row in artifact.hierarchy
    }
    active_rows = list(
        session.scalars(
            select(TopicHierarchy).where(TopicHierarchy.valid_to.is_(None)).with_for_update()
        )
    )
    existing = {(row.parent_topic_id, row.child_topic_id): row for row in active_rows}
    for edge, row in existing.items():
        if edge not in desired:
            row.valid_to = artifact.effective_date - timedelta(days=1)
    session.flush()
    for parent_id, child_id in sorted(desired, key=lambda edge: (str(edge[0]), str(edge[1]))):
        if (parent_id, child_id) not in existing:
            session.add(
                TopicHierarchy(
                    parent_topic_id=parent_id,
                    child_topic_id=child_id,
                    relationship_type="PARENT",
                    hierarchy_version=artifact.activation_version,
                    valid_from=artifact.effective_date,
                )
            )
    session.flush()


def _readback(session: Session, artifact: ActivationArtifact) -> dict[str, Any]:
    active_topics = list(
        session.scalars(select(Topic).where(Topic.status.not_in(tuple(INACTIVE_TOPIC_STATUSES))))
    )
    active_ids = {row.id for row in active_topics}
    edges = list(
        session.scalars(
            select(TopicHierarchy).where(
                TopicHierarchy.valid_from <= artifact.effective_date,
                (TopicHierarchy.valid_to.is_(None))
                | (TopicHierarchy.valid_to >= artifact.effective_date),
            )
        )
    )
    child_ids = {row.child_topic_id for row in edges if row.child_topic_id in active_ids}
    parent_ids = {row.parent_topic_id for row in edges if row.parent_topic_id in active_ids}
    expected_scope = {UUID(str(row["canonicalTopicId"])) for row in artifact.lifecycle_scope}
    if child_ids != expected_scope:
        raise TopicAuthorityActivationError("post-activation readback scope mismatch")
    if (
        len(parent_ids) != artifact.expected_parent_count
        or len(child_ids) != artifact.expected_leaf_count
    ):
        raise TopicAuthorityActivationError("post-activation Parent/Leaf count mismatch")
    payload = {
        "activationVersion": artifact.activation_version,
        "activeParentIds": sorted(map(str, parent_ids)),
        "activeLeafIds": sorted(map(str, child_ids)),
        "hierarchyEdges": sorted(
            (str(row.parent_topic_id), str(row.child_topic_id)) for row in edges
        ),
    }
    return {
        "activeParentCount": len(parent_ids),
        "activeLeafCount": len(child_ids),
        "lifecycleScopeCount": len(expected_scope),
        "readbackSha256": _canonical_hash(payload),
    }


def activate_topic_authority(
    session: Session,
    artifact: ActivationArtifact,
    *,
    dry_run: bool,
    runtime_environment: str,
    expected_database: str,
    runtime_revision: str,
    operator_id: str,
    confirmation: str | None = None,
) -> ActivationResult:
    validate_artifact(artifact)
    validate_target(
        session,
        artifact,
        runtime_environment=runtime_environment,
        expected_database=expected_database,
    )
    if not operator_id.strip():
        raise TopicAuthorityActivationError("operator identity is required")
    if len(runtime_revision) != 40 or any(
        char not in "0123456789abcdef" for char in runtime_revision
    ):
        raise TopicAuthorityActivationError("exact runtime source revision is required")
    required_confirmation = f"ACTIVATE:{artifact.activation_version}:{artifact.artifact_sha256}"
    if not dry_run and confirmation != required_confirmation:
        raise TopicAuthorityActivationError("exact activation confirmation is required")
    if not dry_run and session.in_transaction():
        session.rollback()

    if dry_run:
        _preflight_database(session, artifact)
        readback = {
            "activeParentCount": artifact.expected_parent_count,
            "activeLeafCount": artifact.expected_leaf_count,
            "lifecycleScopeCount": len(artifact.lifecycle_scope),
            "readbackSha256": _canonical_hash({"plannedArtifactSha256": artifact.artifact_sha256}),
        }
        session.rollback()
        return _result("DRY_RUN_PASS", artifact, True, readback)

    with session.begin():
        existing_activation = _existing_activation(session, artifact.activation_version)
        if existing_activation is not None:
            if existing_activation.artifact_sha256 != artifact.artifact_sha256:
                raise TopicAuthorityActivationError(
                    "activation version exists with different content"
                )
            readback = _readback(session, artifact)
            if existing_activation.readback_sha256 != readback["readbackSha256"]:
                raise TopicAuthorityActivationError("idempotent activation readback drift")
            return _result("NOOP", artifact, False, readback)

        _preflight_database(session, artifact)
        previous = session.scalar(
            select(TopicAuthorityActivation)
            .where(TopicAuthorityActivation.status == "ACTIVE")
            .with_for_update()
        )
        _apply_topics(session, artifact)
        _apply_hierarchy(session, artifact)
        readback = _readback(session, artifact)
        if previous is not None:
            previous.status = "SUPERSEDED"
            session.flush()
        session.add(
            TopicAuthorityActivation(
                activation_version=artifact.activation_version,
                artifact_sha256=artifact.artifact_sha256,
                source_master_sha256=artifact.source_master_sha256,
                source_revision=runtime_revision,
                target_environment=artifact.target_environment,
                target_database=artifact.target_database,
                operator_id=operator_id,
                approval_reference=artifact.approval_reference,
                effective_from=datetime.combine(
                    artifact.effective_date, datetime.min.time(), tzinfo=UTC
                ),
                status="ACTIVE",
                previous_activation_id=previous.id if previous else None,
                active_parent_count=readback["activeParentCount"],
                active_leaf_count=readback["activeLeafCount"],
                lifecycle_scope_count=readback["lifecycleScopeCount"],
                readback_sha256=readback["readbackSha256"],
                artifact=artifact.payload,
            )
        )
        session.flush()
    return _result("ACTIVATED", artifact, False, readback)


__all__ = [
    "SCHEMA_VERSION",
    "ActivationArtifact",
    "ActivationResult",
    "TopicAuthorityActivationError",
    "activate_topic_authority",
    "artifact_hash",
    "load_activation_artifact",
    "parse_activation_artifact",
    "validate_artifact",
    "validate_target",
]
