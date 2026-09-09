"""Read-only minimum Topic catalog and formal snapshot boundary.

This module is intentionally separate from the broader Stock/Topic production
read model.  It owns only catalog identity, effective hierarchy/membership,
and consumption of already-published formal Topic Daily Snapshots.  It never
calculates a snapshot and never reads legacy/public or shadow data.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from topicpilot_api.problems import NotFoundProblem
from topicpilot_api.topic_daily_state import FORMAL_MAPPING_EARLIEST_DATE

TAIPEI = ZoneInfo("Asia/Taipei")
MAX_HISTORY_DAYS = 366


class TopicCatalogUnavailable(RuntimeError):
    """Raised when the identity read model itself cannot be queried."""


TOPIC_CATALOG_ROWS_SQL = text(
    """
    SELECT t.id AS topic_id, t.slug, t.name, t.status,
           t.dictionary_version
    FROM topicpilot.topics t
    WHERE t.status NOT IN ('DISABLED', 'RETIRED')
      AND (t.valid_from IS NULL OR t.valid_from <= :as_of_date)
      AND (t.valid_to IS NULL OR t.valid_to >= :as_of_date)
      AND (CAST(:slug AS text) IS NULL OR t.slug = CAST(:slug AS text))
    ORDER BY t.slug
    """
)

TOPIC_HIERARCHY_ROWS_SQL = text(
    """
    SELECT h.parent_topic_id, parent.slug AS parent_slug, parent.name AS parent_name,
           h.child_topic_id, child.slug AS child_slug, child.name AS child_name,
           h.relationship_type, h.hierarchy_version, h.valid_from, h.valid_to,
           h.display_order
    FROM topicpilot.topic_hierarchy h
    JOIN topicpilot.topics parent ON parent.id = h.parent_topic_id
    JOIN topicpilot.topics child ON child.id = h.child_topic_id
    WHERE (h.valid_from IS NULL OR h.valid_from <= :as_of_date)
      AND (h.valid_to IS NULL OR h.valid_to >= :as_of_date)
      AND parent.status NOT IN ('DISABLED', 'RETIRED')
      AND child.status NOT IN ('DISABLED', 'RETIRED')
      AND (parent.valid_from IS NULL OR parent.valid_from <= :as_of_date)
      AND (parent.valid_to IS NULL OR parent.valid_to >= :as_of_date)
      AND (child.valid_from IS NULL OR child.valid_from <= :as_of_date)
      AND (child.valid_to IS NULL OR child.valid_to >= :as_of_date)
    ORDER BY h.display_order NULLS LAST, parent.slug, child.slug
    """
)

TOPIC_MEMBER_ROWS_SQL = text(
    """
    SELECT r.topic_id, r.instrument_id, i.instrument_code, i.name AS instrument_name,
           m.code AS market_code, r.relation_type, r.relation_version,
           r.valid_from, r.valid_to
    FROM topicpilot.instrument_topic_relations r
    JOIN topicpilot.instruments i ON i.id = r.instrument_id
    JOIN topicpilot.markets m ON m.id = i.market_id
    JOIN topicpilot.topics t ON t.id = r.topic_id
    WHERE r.valid_from <= :as_of_date
      AND (r.valid_to IS NULL OR r.valid_to >= :as_of_date)
      AND i.is_active = true
      AND m.is_active = true
      AND t.status NOT IN ('DISABLED', 'RETIRED')
      AND (i.valid_from IS NULL OR i.valid_from <= :as_of_date)
      AND (i.valid_to IS NULL OR i.valid_to >= :as_of_date)
      AND (m.valid_from IS NULL OR m.valid_from <= :as_of_date)
      AND (m.valid_to IS NULL OR m.valid_to >= :as_of_date)
      AND (t.valid_from IS NULL OR t.valid_from <= :as_of_date)
      AND (t.valid_to IS NULL OR t.valid_to >= :as_of_date)
    ORDER BY r.topic_id, m.code, i.instrument_code, r.relation_version, r.valid_from
    """
)

FORMAL_SNAPSHOT_COLUMNS = """
    s.snapshot_date, s.topic_id, s.topic_slug, s.topic_name,
    s.topic_direction, s.topic_score, s.market_grade, s.stock_count,
    s.observed_stock_count, s.coverage_pct, s.average_change,
    s.data_status, s.score_status, s.calculation_version, s.as_of_at,
    s.generated_at, s.finalized_at, s.published_at, s.publication_mode,
    s.publication_state, s.membership_mode, s.generated_state, s.finality_state,
    s.trading_day_state, s.freshness_state, s.snapshot_identity,
    s.correction_sequence, s.relation_version, s.mapping_effective_from,
    s.membership_snapshot_id, s.membership_snapshot_hash,
    s.source_run_id, s.source_artifact_id, s.source_artifact_hash,
    s.lineage_hash, s.reference_registry_version, s.mapping_policy_version
"""

FORMAL_SNAPSHOT_FILTER = """
    s.publication_mode = 'FORMAL'
    AND s.publication_state = 'PUBLISHED'
    AND s.superseded_by_snapshot_id IS NULL
    AND s.membership_mode = 'PIT_FORMAL'
    AND s.finality_state = 'FINAL'
    AND s.mapping_effective_from >= DATE '2026-08-07'
    AND s.membership_snapshot_id IS NOT NULL
    AND s.membership_snapshot_hash IS NOT NULL
    AND s.relation_version IS NOT NULL
    AND s.snapshot_identity IS NOT NULL
    AND s.lineage_hash IS NOT NULL
"""

FORMAL_CURRENT_SNAPSHOT_ROWS_SQL = text(
    f"""
    SELECT {FORMAL_SNAPSHOT_COLUMNS}
    FROM topicpilot.topic_snapshots s
    WHERE {FORMAL_SNAPSHOT_FILTER}
      AND s.snapshot_date <= :as_of_date
    ORDER BY s.topic_id, s.snapshot_date DESC, s.correction_sequence DESC,
             s.updated_at DESC, s.id DESC
    """
)

FORMAL_SNAPSHOT_HISTORY_ROWS_SQL = text(
    f"""
    SELECT {FORMAL_SNAPSHOT_COLUMNS}
    FROM topicpilot.topic_snapshots s
    WHERE {FORMAL_SNAPSHOT_FILTER}
      AND s.topic_id = CAST(:topic_id AS uuid)
      AND s.snapshot_date >= :from_date
      AND s.snapshot_date <= :to_date
    ORDER BY s.snapshot_date DESC, s.correction_sequence DESC,
             s.updated_at DESC, s.id DESC
    LIMIT :limit OFFSET :offset
    """
)

FORMAL_SNAPSHOT_HISTORY_COUNT_SQL = text(
    f"""
    SELECT COUNT(*)
    FROM topicpilot.topic_snapshots s
    WHERE {FORMAL_SNAPSHOT_FILTER}
      AND s.topic_id = CAST(:topic_id AS uuid)
      AND s.snapshot_date >= :from_date
      AND s.snapshot_date <= :to_date
    """
)


def _today() -> date:
    return datetime.now(TAIPEI).date()


def _float(value: Any) -> float | None:
    return float(value) if value is not None else None


def _id(value: Any) -> str:
    return str(value)


def _availability(
    state: str, as_of: date, reason_code: str | None = None, reason: str | None = None
) -> dict[str, Any]:
    return {
        "state": state,
        "reasonCode": reason_code,
        "reason": reason,
        "asOf": as_of,
    }


def _source_ref(authority: str, as_of: date, version: str | None = None) -> dict[str, Any]:
    return {"authority": authority, "asOf": as_of, "version": version}


def _row_value(row: Any, key: str) -> Any:
    return row[key]


def _snapshot_is_valid(row: Any) -> bool:
    """Keep a defensive check beside the SQL fail-closed predicate."""

    required = (
        "publication_mode",
        "publication_state",
        "membership_mode",
        "finality_state",
        "mapping_effective_from",
        "membership_snapshot_id",
        "membership_snapshot_hash",
        "relation_version",
        "snapshot_identity",
        "lineage_hash",
    )
    return (
        all(_row_value(row, key) is not None for key in required)
        and _row_value(row, "publication_mode") == "FORMAL"
        and _row_value(row, "publication_state") == "PUBLISHED"
        and _row_value(row, "membership_mode") == "PIT_FORMAL"
        and _row_value(row, "finality_state") == "FINAL"
        and _row_value(row, "mapping_effective_from") >= FORMAL_MAPPING_EARLIEST_DATE
    )


def _serialize_snapshot(row: Any) -> dict[str, Any] | None:
    if not _snapshot_is_valid(row):
        return None
    publication = {
        "mode": "FORMAL",
        "state": "PUBLISHED",
        "membershipMode": "PIT_FORMAL",
        "generatedState": row["generated_state"],
        "finalityState": "FINAL",
        "tradingDayState": row["trading_day_state"],
        "freshnessState": row["freshness_state"],
        "snapshotIdentity": row["snapshot_identity"],
        "correctionSequence": row["correction_sequence"],
        "relationVersion": row["relation_version"],
        "mappingEffectiveFrom": row["mapping_effective_from"],
        "membershipSnapshotId": row["membership_snapshot_id"],
        "membershipSnapshotHash": row["membership_snapshot_hash"],
        "generatedAt": row["generated_at"],
        "finalizedAt": row["finalized_at"],
        "publishedAt": row["published_at"],
    }
    source = {
        "authority": "topicpilot.topic_snapshots",
        "asOfAt": row["as_of_at"],
        "sourceRunId": row["source_run_id"],
        "sourceArtifactId": row["source_artifact_id"],
        "sourceArtifactHash": row["source_artifact_hash"],
        "lineageHash": row["lineage_hash"],
        "referenceRegistryVersion": row["reference_registry_version"],
        "mappingPolicyVersion": row["mapping_policy_version"],
    }
    return {
        "snapshotDate": row["snapshot_date"],
        "topicId": _id(row["topic_id"]),
        "topicSlug": row["topic_slug"],
        "topicName": row["topic_name"],
        "topicDirection": row["topic_direction"],
        "topicScore": _float(row["topic_score"]),
        "marketGrade": row["market_grade"],
        "stockCount": row["stock_count"],
        "observedStockCount": row["observed_stock_count"],
        "coveragePct": _float(row["coverage_pct"]),
        "averageChange": _float(row["average_change"]),
        "dataStatus": row["data_status"],
        "scoreStatus": row["score_status"],
        "calculationVersion": row["calculation_version"],
        "asOfAt": row["as_of_at"],
        "source": source,
        "publication": publication,
    }


def _load_catalog_rows(session: Session, as_of: date, slug: str | None = None) -> list[Any]:
    try:
        return list(
            session.execute(
                TOPIC_CATALOG_ROWS_SQL, {"as_of_date": as_of, "slug": slug}
            ).mappings()
        )
    except SQLAlchemyError as exc:
        raise TopicCatalogUnavailable("Topic identity read model is unavailable") from exc


def _load_hierarchy_rows(session: Session, as_of: date) -> list[Any]:
    try:
        return list(session.execute(TOPIC_HIERARCHY_ROWS_SQL, {"as_of_date": as_of}).mappings())
    except SQLAlchemyError as exc:
        raise TopicCatalogUnavailable("Topic hierarchy read model is unavailable") from exc


def _load_member_rows(session: Session, as_of: date) -> list[Any]:
    try:
        return list(session.execute(TOPIC_MEMBER_ROWS_SQL, {"as_of_date": as_of}).mappings())
    except SQLAlchemyError as exc:
        raise TopicCatalogUnavailable("Topic membership read model is unavailable") from exc


def _load_current_snapshots(
    session: Session, as_of: date
) -> tuple[dict[str, Any], bool]:
    try:
        rows = session.execute(
            FORMAL_CURRENT_SNAPSHOT_ROWS_SQL, {"as_of_date": as_of}
        ).mappings()
    except SQLAlchemyError:
        return {}, False
    snapshots: dict[str, Any] = {}
    for row in rows:
        topic_id = _id(row["topic_id"])
        if topic_id in snapshots:
            continue
        serialized = _serialize_snapshot(row)
        if serialized is not None:
            snapshots[topic_id] = serialized
    return snapshots, True


def _hierarchy_by_topic(rows: list[Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = defaultdict(lambda: {"parents": [], "children": []})
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        parent = {
            "topicId": _id(row["parent_topic_id"]),
            "slug": row["parent_slug"],
            "name": row["parent_name"],
        }
        child = {
            "topicId": _id(row["child_topic_id"]),
            "slug": row["child_slug"],
            "name": row["child_name"],
        }
        parent_key = (_id(row["child_topic_id"]), "parent", _id(row["parent_topic_id"]))
        child_key = (_id(row["parent_topic_id"]), "child", _id(row["child_topic_id"]))
        if parent_key not in seen:
            result[_id(row["child_topic_id"])]["parents"].append(parent)
            seen.add(parent_key)
        if child_key not in seen:
            result[_id(row["parent_topic_id"])]["children"].append(child)
            seen.add(child_key)
    return result


def _members_by_topic(rows: list[Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        result[_id(row["topic_id"])].append(
            {
                "instrumentId": _id(row["instrument_id"]),
                "code": row["instrument_code"],
                "name": row["instrument_name"],
                "market": row["market_code"],
                "relationType": row["relation_type"],
                "relationVersion": row["relation_version"],
                "validFrom": row["valid_from"],
                "validTo": row["valid_to"],
            }
        )
    return result


def _versions(values: list[str | None]) -> str | None:
    normalized = sorted({value for value in values if value})
    if not normalized:
        return None
    return normalized[0] if len(normalized) == 1 else "MIXED"


def _build_topic(
    topic: Any,
    *,
    as_of: date,
    hierarchy: dict[str, dict[str, Any]],
    members: dict[str, list[dict[str, Any]]],
    current_snapshots: dict[str, Any],
    snapshot_authority_available: bool,
    hierarchy_versions: dict[str, list[str | None]],
    member_versions: dict[str, list[str | None]],
) -> dict[str, Any]:
    topic_id = _id(topic["topic_id"])
    edges = hierarchy.get(topic_id, {"parents": [], "children": []})
    kind = "PARENT" if edges["children"] else "LEAF"
    if kind == "PARENT":
        member_items: list[dict[str, Any]] = []
        members_availability = _availability(
            "NOT_APPLICABLE",
            as_of,
            "PARENT_TOPIC_MEMBERS_NOT_FORMAL_SEMANTICS",
            (
                "Parent topics expose identity and hierarchy only; member semantics belong "
                "to leaf topics."
            ),
        )
    elif as_of < FORMAL_MAPPING_EARLIEST_DATE:
        member_items = []
        members_availability = _availability(
            "UNAVAILABLE",
            as_of,
            "PRE_FORMAL_MEMBERSHIP_BOUNDARY",
            "Formal effective-dated Topic membership is not authorized before 2026-08-07.",
        )
    else:
        member_items = members.get(topic_id, [])
        members_availability = _availability("AVAILABLE", as_of)

    if kind == "PARENT":
        snapshot_availability = _availability(
            "NOT_APPLICABLE",
            as_of,
            "PARENT_TOPIC_NOT_ELIGIBLE_FOR_FORMAL_SNAPSHOT",
            "Formal Topic Snapshots are leaf-only; parent topics are diagnostic hierarchy nodes.",
        )
        snapshot = None
    elif as_of < FORMAL_MAPPING_EARLIEST_DATE:
        snapshot_availability = _availability(
            "UNAVAILABLE",
            as_of,
            "PRE_FORMAL_SNAPSHOT_BOUNDARY",
            "Formal Topic Snapshots are not authorized before 2026-08-07.",
        )
        snapshot = None
    else:
        snapshot = current_snapshots.get(topic_id)
        if snapshot is not None:
            snapshot_availability = _availability("AVAILABLE", as_of)
        else:
            reason_code = (
                "FORMAL_SNAPSHOT_AUTHORITY_UNAVAILABLE"
                if not snapshot_authority_available
                else "FORMAL_SNAPSHOT_NOT_PUBLISHED"
            )
            reason = (
                "The formal Topic Snapshot table is not available at this deployment boundary."
                if not snapshot_authority_available
                else "No current formal, published, final PIT Topic Snapshot is available."
            )
            snapshot_availability = _availability("UNAVAILABLE", as_of, reason_code, reason)

    hierarchy_payload = {
        "kind": kind,
        "parents": edges["parents"],
        "children": edges["children"],
    }
    source = {
        "identity": _source_ref(
            "topicpilot.topics", as_of, topic["dictionary_version"]
        ),
        "hierarchy": _source_ref(
            "topicpilot.topic_hierarchy", as_of, _versions(hierarchy_versions.get(topic_id, []))
        ),
        "members": (
            _source_ref(
                "topicpilot.instrument_topic_relations",
                as_of,
                _versions(member_versions.get(topic_id, [])),
            )
            if kind == "LEAF"
            else None
        ),
        "snapshot": _source_ref(
            "topicpilot.topic_snapshots",
            as_of,
            snapshot["calculationVersion"] if snapshot else None,
        ),
    }
    return {
        "topicId": topic_id,
        "slug": topic["slug"],
        "name": topic["name"],
        "status": topic["status"],
        "enabled": True,
        "kind": kind,
        "asOf": as_of,
        "availability": _availability("AVAILABLE", as_of),
        "hierarchy": hierarchy_payload,
        "members": member_items,
        "membersAvailability": members_availability,
        "source": source,
        "currentFormalSnapshot": {
            "availability": snapshot_availability,
            "snapshot": snapshot,
        },
    }


def _component_state(
    session: Session, as_of: date
) -> tuple[
    list[Any],
    dict[str, dict[str, Any]],
    dict[str, list[dict[str, Any]]],
    dict[str, Any],
    bool,
    dict[str, list[str | None]],
    dict[str, list[str | None]],
]:
    topics = _load_catalog_rows(session, as_of)
    hierarchy_rows = _load_hierarchy_rows(session, as_of)
    member_rows = _load_member_rows(session, as_of)
    hierarchy = _hierarchy_by_topic(hierarchy_rows)
    members = _members_by_topic(member_rows)
    current_snapshots, snapshot_authority_available = _load_current_snapshots(session, as_of)
    hierarchy_versions: dict[str, list[str | None]] = defaultdict(list)
    for row in hierarchy_rows:
        hierarchy_versions[_id(row["parent_topic_id"])].append(row["hierarchy_version"])
        hierarchy_versions[_id(row["child_topic_id"])].append(row["hierarchy_version"])
    member_versions: dict[str, list[str | None]] = defaultdict(list)
    for row in member_rows:
        member_versions[_id(row["topic_id"])].append(row["relation_version"])
    return (
        topics,
        hierarchy,
        members,
        current_snapshots,
        snapshot_authority_available,
        hierarchy_versions,
        member_versions,
    )


def read_topic_minimum_page(
    session: Session, *, as_of: date | None = None, limit: int = 200, offset: int = 0
) -> dict[str, Any]:
    effective_as_of = as_of or _today()
    (
        topics,
        hierarchy,
        members,
        snapshots,
        snapshot_authority_available,
        hierarchy_versions,
        member_versions,
    ) = _component_state(session, effective_as_of)
    items = [
        _build_topic(
            topic,
            as_of=effective_as_of,
            hierarchy=hierarchy,
            members=members,
            current_snapshots=snapshots,
            snapshot_authority_available=snapshot_authority_available,
            hierarchy_versions=hierarchy_versions,
            member_versions=member_versions,
        )
        for topic in topics
    ]
    return {
        "items": items[offset : offset + limit],
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "asOf": effective_as_of,
    }


def read_topic_minimum(session: Session, slug: str, *, as_of: date | None = None) -> dict[str, Any]:
    effective_as_of = as_of or _today()
    topics = _load_catalog_rows(session, effective_as_of, slug)
    if not topics:
        raise NotFoundProblem(f"Topic {slug!r} was not found in the Topic catalog")
    (
        _all_topics,
        hierarchy,
        members,
        snapshots,
        snapshot_authority_available,
        hierarchy_versions,
        member_versions,
    ) = _component_state(session, effective_as_of)
    return _build_topic(
        topics[0],
        as_of=effective_as_of,
        hierarchy=hierarchy,
        members=members,
        current_snapshots=snapshots,
        snapshot_authority_available=snapshot_authority_available,
        hierarchy_versions=hierarchy_versions,
        member_versions=member_versions,
    )


def read_current_formal_snapshot(
    session: Session, slug: str, *, as_of: date | None = None
) -> dict[str, Any]:
    topic = read_topic_minimum(session, slug, as_of=as_of)
    return topic["currentFormalSnapshot"]


def _history_unavailable(as_of: date, reason_code: str, reason: str) -> dict[str, Any]:
    return {
        "items": [],
        "total": 0,
        "limit": 0,
        "offset": 0,
        "asOf": as_of,
        "availability": _availability("UNAVAILABLE", as_of, reason_code, reason),
    }


def read_formal_snapshot_history(
    session: Session,
    slug: str,
    *,
    as_of: date | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    effective_as_of = as_of or _today()
    topic = read_topic_minimum(session, slug, as_of=effective_as_of)
    if topic["kind"] == "PARENT":
        return {
            "items": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "asOf": effective_as_of,
            "availability": _availability(
                "NOT_APPLICABLE",
                effective_as_of,
                "PARENT_TOPIC_NOT_ELIGIBLE_FOR_FORMAL_SNAPSHOT",
                (
                    "Formal Topic Snapshot history is leaf-only; parent topics are diagnostic "
                    "hierarchy nodes."
                ),
            ),
        }
    effective_from = from_date or FORMAL_MAPPING_EARLIEST_DATE
    effective_to = to_date or effective_as_of
    if effective_from < FORMAL_MAPPING_EARLIEST_DATE or effective_to < FORMAL_MAPPING_EARLIEST_DATE:
        return _history_unavailable(
            effective_as_of,
            "PRE_FORMAL_SNAPSHOT_BOUNDARY",
            "Formal Topic Snapshot history is not authorized before 2026-08-07.",
        ) | {"limit": limit, "offset": offset}
    if effective_to < effective_from:
        raise ValueError("to must be on or after from")
    if (effective_to - effective_from).days > MAX_HISTORY_DAYS:
        raise ValueError(f"snapshot history window must not exceed {MAX_HISTORY_DAYS} days")
    params = {
        "topic_id": topic["topicId"],
        "from_date": effective_from,
        "to_date": effective_to,
        "limit": limit,
        "offset": offset,
    }
    try:
        rows = list(session.execute(FORMAL_SNAPSHOT_HISTORY_ROWS_SQL, params).mappings())
        total = int(session.scalar(FORMAL_SNAPSHOT_HISTORY_COUNT_SQL, params) or 0)
    except SQLAlchemyError:
        return {
            "items": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "asOf": effective_as_of,
            "availability": _availability(
                "UNAVAILABLE",
                effective_as_of,
                "FORMAL_SNAPSHOT_AUTHORITY_UNAVAILABLE",
                "The formal Topic Snapshot table is not available at this deployment boundary.",
            ),
        }
    items = [item for row in rows if (item := _serialize_snapshot(row)) is not None]
    if not items:
        return {
            "items": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "asOf": effective_as_of,
            "availability": _availability(
                "UNAVAILABLE",
                effective_as_of,
                "FORMAL_SNAPSHOT_NOT_PUBLISHED",
                (
                    "No formal, published, final PIT Topic Snapshot is available in the "
                    "requested range."
                ),
            ),
        }
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "asOf": effective_as_of,
        "availability": _availability("AVAILABLE", effective_as_of),
    }


__all__ = [
    "MAX_HISTORY_DAYS",
    "TopicCatalogUnavailable",
    "read_current_formal_snapshot",
    "read_formal_snapshot_history",
    "read_topic_minimum",
    "read_topic_minimum_page",
]
