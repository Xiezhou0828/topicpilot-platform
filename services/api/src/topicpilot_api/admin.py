# ruff: noqa: E501, E701
from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, joinedload, selectinload

from .database import get_db
from .orm import (
    Base,
    Instrument,
    InstrumentTopicRelation,
    LegacyImportRecord,
    LegacyImportRun,
    Market,
    Topic,
    TopicHierarchy,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
DbSession = Annotated[Session, Depends(get_db)]
TABLES = {"identity": ["markets", "instruments", "security_identities"], "topics": ["topics", "topic_hierarchy", "instrument_topic_relations"], "market_data": ["market_data_sources", "raw_market_observations"], "timeline": ["observation_timeline_batches", "observation_timeline_entries", "observation_timeline_quality_events"], "canonical": ["canonical_observations", "canonical_price_observations", "canonical_volume_observations", "canonical_quote_observations", "canonical_trading_status_observations"], "reference": ["reference_registry_sets", "reference_currencies", "reference_timezones", "reference_sessions", "reference_trading_statuses", "reference_adjustments"], "legacy_import": ["legacy_import_runs", "legacy_import_artifacts", "legacy_import_records"]}

def _page(items: list[Any], total: int, limit: int, offset: int) -> dict[str, Any]:
    return {"items": items, "total": total, "limit": limit, "offset": offset, "has_more": offset + len(items) < total}

def _id(value: Any) -> str: return str(value)

@router.get("/dashboard")
def dashboard(session: DbSession) -> dict[str, Any]:
    counts = {key: session.scalar(select(func.count()).select_from(model)) or 0 for key, model in {"markets": Market, "instruments": Instrument, "topics": Topic, "topic_hierarchy_relations": TopicHierarchy, "instrument_topic_relations": InstrumentTopicRelation, "legacy_import_runs": LegacyImportRun}.items()}
    latest = session.scalar(select(LegacyImportRun).order_by(LegacyImportRun.created_at.desc()).limit(1))
    revision = session.execute(text("SELECT version_num FROM topicpilot.alembic_version LIMIT 1")).scalar_one_or_none()
    return {"counts": counts, "latest_import": None if latest is None else {"id": _id(latest.id), "status": latest.status, "created_at": latest.created_at}, "alembic_revision": revision, "api_ready": True}

def _schema_tables() -> list[dict[str, Any]]:
    tables = []
    for table in Base.metadata.sorted_tables:
        tables.append({"name": table.name, "group": next((g for g, names in TABLES.items() if table.name in names), "other"), "columns": [{"name": c.name, "type": str(c.type), "nullable": c.nullable, "primary_key": c.primary_key} for c in table.columns], "foreign_keys": [{"column": fk.parent.name, "references": fk.target_fullname} for fk in table.foreign_keys]})
    return tables

@router.get("/schema")
def schema() -> dict[str, Any]:
    tables = _schema_tables()
    return {"schema": "topicpilot", "source": "SQLAlchemy Base.metadata", "tables": tables, "nodes": [{"id": t["name"], "label": t["name"], "group": t["group"]} for t in tables], "edges": [{"source": t["name"], "target": f["references"].split(".")[-2], "column": f["column"]} for t in tables for f in t["foreign_keys"] if "." in f["references"]]}

@router.get("/markets")
def markets(session: DbSession, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    total = session.scalar(select(func.count()).select_from(Market)) or 0
    rows = session.scalars(select(Market).order_by(Market.code).offset(offset).limit(limit)).all()
    return _page([{ "id": _id(x.id), "code": x.code, "name": x.name, "exchange_code": x.exchange_code, "timezone": x.timezone, "is_active": x.is_active } for x in rows], total, limit, offset)

@router.get("/instruments")
def instruments(session: DbSession, q: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    stmt = select(Instrument).order_by(Instrument.instrument_code)
    if q: stmt = stmt.where((Instrument.instrument_code.ilike(f"%{q}%")) | (Instrument.name.ilike(f"%{q}%")))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.scalars(stmt.offset(offset).limit(limit)).all()
    return _page([{ "id": _id(x.id), "code": x.instrument_code, "name": x.name, "market_id": _id(x.market_id), "instrument_type": x.instrument_type, "is_active": x.is_active } for x in rows], total, limit, offset)

@router.get("/instruments/{instrument_id}")
def instrument_detail(instrument_id: uuid.UUID, session: DbSession) -> dict[str, Any]:
    item = session.scalar(select(Instrument).options(joinedload(Instrument.market), selectinload(Instrument.topic_relationships).joinedload(InstrumentTopicRelation.topic)).where(Instrument.id == instrument_id))
    if item is None: raise HTTPException(404, "Instrument not found")
    lineage = session.scalars(select(LegacyImportRecord).where(LegacyImportRecord.target_id == item.id).order_by(LegacyImportRecord.id.desc()).limit(200)).all()
    return {"id": _id(item.id), "code": item.instrument_code, "name": item.name, "instrument_type": item.instrument_type, "currency": item.currency, "is_active": item.is_active, "market": {"id": _id(item.market.id), "code": item.market.code, "name": item.market.name}, "topics": [{"id": _id(r.topic.id), "slug": r.topic.slug, "name": r.topic.name, "relation_type": r.relation_type, "relation_version": r.relation_version, "valid_from": r.valid_from, "valid_to": r.valid_to, "metadata": r.relationship_metadata} for r in item.topic_relationships], "lineage": {"created_at": item.created_at, "updated_at": item.updated_at, "supported": True, "records": [{"record_id": _id(r.id), "run_id": _id(r.run_id), "run_status": r.run.status if r.run else None, "run_started_at": r.run.started_at if r.run else None, "run_completed_at": r.run.completed_at if r.run else None, "source_filename": r.source_filename, "source_row": r.source_row, "outcome": r.outcome, "canonical_payload_hash": r.canonical_payload_hash} for r in lineage], "limitation": "Lineage is limited to audited legacy import records whose target_id equals this instrument UUID; upstream source history outside the audit tables is not available here."}}

@router.get("/topics")
def topics(session: DbSession, q: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    stmt = select(Topic).order_by(Topic.name)
    if q: stmt = stmt.where((Topic.name.ilike(f"%{q}%")) | (Topic.slug.ilike(f"%{q}%")))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.scalars(stmt.offset(offset).limit(limit)).all()
    return _page([{ "id": _id(x.id), "slug": x.slug, "name": x.name, "status": x.status, "description": x.description } for x in rows], total, limit, offset)

@router.get("/topics/{topic_id}")
def topic_detail(topic_id: uuid.UUID, session: DbSession) -> dict[str, Any]:
    item = session.scalar(select(Topic).options(selectinload(Topic.parent_relationships).joinedload(TopicHierarchy.parent), selectinload(Topic.child_relationships).joinedload(TopicHierarchy.child), selectinload(Topic.instrument_relationships).joinedload(InstrumentTopicRelation.instrument)).where(Topic.id == topic_id))
    if item is None: raise HTTPException(404, "Topic not found")
    def hierarchy(rel: TopicHierarchy, other: Topic) -> dict[str, Any]: return {"id": _id(other.id), "slug": other.slug, "name": other.name, "relationship_type": rel.relationship_type, "hierarchy_version": rel.hierarchy_version, "valid_from": rel.valid_from, "valid_to": rel.valid_to}
    all_topics = {x.id: x for x in session.scalars(select(Topic).order_by(Topic.name, Topic.id)).all()}
    links = session.scalars(select(TopicHierarchy).order_by(TopicHierarchy.parent_topic_id, TopicHierarchy.child_topic_id, TopicHierarchy.id)).all()
    parents = {}
    for link in links: parents.setdefault(link.child_topic_id, []).append(link.parent_topic_id)
    def ancestry(node: uuid.UUID, trail: tuple[uuid.UUID, ...] = ()) -> list[list[dict[str, Any]]]:
        if node in trail: return [[{"id": _id(node), "slug": all_topics[node].slug, "name": all_topics[node].name, "cycle": True}]]
        parent_ids = parents.get(node, [])
        current = {"id": _id(node), "slug": all_topics[node].slug, "name": all_topics[node].name}
        if not parent_ids: return [[current]]
        paths = []
        for parent_id in parent_ids:
            for path in ancestry(parent_id, (*trail, node)): paths.append([*path, current])
        return paths
    paths = ancestry(item.id)
    return {"id": _id(item.id), "slug": item.slug, "name": item.name, "status": item.status, "description": item.description, "parents": [hierarchy(r, r.parent) for r in item.parent_relationships], "children": [hierarchy(r, r.child) for r in item.child_relationships], "ancestry_paths": paths, "multi_parent": len(paths) > 1, "instruments": [{"id": _id(r.instrument.id), "code": r.instrument.instrument_code, "name": r.instrument.name, "relation_type": r.relation_type, "relation_version": r.relation_version, "metadata": r.relationship_metadata} for r in item.instrument_relationships], "lineage": {"created_at": item.created_at, "updated_at": item.updated_at}}

@router.get("/relations")
def relations(session: DbSession, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    total = session.scalar(select(func.count()).select_from(InstrumentTopicRelation)) or 0
    rows = session.scalars(select(InstrumentTopicRelation).order_by(InstrumentTopicRelation.created_at.desc()).offset(offset).limit(limit)).all()
    return _page([{ "id": _id(x.id), "instrument_id": _id(x.instrument_id), "topic_id": _id(x.topic_id), "relation_type": x.relation_type, "relation_version": x.relation_version } for x in rows], total, limit, offset)

@router.get("/imports")
def imports(session: DbSession, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    total = session.scalar(select(func.count()).select_from(LegacyImportRun)) or 0
    rows = session.scalars(select(LegacyImportRun).order_by(LegacyImportRun.created_at.desc()).offset(offset).limit(limit)).all()
    return _page([{ "id": _id(x.id), "status": x.status, "export_id": x.export_id, "contract_version": x.contract_version, "mapping_policy_version": x.mapping_policy_version, "created_at": x.created_at, "completed_at": x.completed_at } for x in rows], total, limit, offset)

@router.get("/imports/{run_id}")
def import_detail(run_id: uuid.UUID, session: DbSession, record_limit: int = Query(50, ge=1, le=200), record_offset: int = Query(0, ge=0), outcome: str | None = None, entity: str | None = None) -> dict[str, Any]:
    run = session.scalar(select(LegacyImportRun).options(selectinload(LegacyImportRun.artifacts)).where(LegacyImportRun.id == run_id))
    if run is None: raise HTTPException(404, "Import run not found")
    filters = [LegacyImportRecord.run_id == run_id]
    if outcome: filters.append(LegacyImportRecord.outcome == outcome)
    if entity: filters.append(LegacyImportRecord.entity == entity)
    total = session.scalar(select(func.count()).select_from(LegacyImportRecord).where(*filters)) or 0
    records = session.scalars(select(LegacyImportRecord).options(joinedload(LegacyImportRecord.run)).where(*filters).order_by(LegacyImportRecord.id).offset(record_offset).limit(record_limit)).all()
    outcomes = dict(session.execute(select(LegacyImportRecord.outcome, func.count()).where(LegacyImportRecord.run_id == run_id).group_by(LegacyImportRecord.outcome)).all())
    return {"id": _id(run.id), "export_id": run.export_id, "contract_version": run.contract_version, "mapping_policy_version": run.mapping_policy_version, "migration_baseline": run.migration_baseline, "status": run.status, "started_at": run.started_at, "completed_at": run.completed_at, "artifacts": [{"id": _id(a.id), "filename": a.filename, "sha256": a.sha256, "row_count": a.row_count} for a in run.artifacts], "outcomes": outcomes, "filters": {"outcome": outcome, "entity": entity}, "records": _page([{ "id": _id(r.id), "entity": r.entity, "stable_key": r.stable_key, "source_filename": r.source_filename, "source_row": r.source_row, "target_uuid": _id(r.target_id) if r.target_id else None, "outcome": r.outcome, "canonical_payload_hash": r.canonical_payload_hash } for r in records], total, record_limit, record_offset)}
