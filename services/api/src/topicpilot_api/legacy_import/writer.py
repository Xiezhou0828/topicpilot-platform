from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..orm.import_audit import LegacyImportArtifact, LegacyImportRecord, LegacyImportRun
from ..orm.models import (
    Instrument,
    InstrumentTopicRelation,
    Market,
    Topic,
    TopicHierarchy,
)
from .contracts import ImportBatch
from .export_contract import canonical_record_hash
from .mapping import MappingPolicy, canonical_mapped_payload


class ImportConflict(RuntimeError):
    pass


def _date(value: Any) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


class TransactionalV2Writer:
    """Single-transaction, stable-key writer for the approved V1 master-data slice."""

    def __init__(
        self, session: Session, migration_baseline: str = "0020_phase3_5_002a_reference_registry"
    ) -> None:
        self.session, self.migration_baseline = session, migration_baseline

    def apply(self, batch: ImportBatch, policy: MappingPolicy) -> None:
        self.apply_all([batch], policy)

    def apply_all(
        self, batches: list[ImportBatch], policy: MappingPolicy, export_id: str | None = None
    ) -> uuid.UUID:
        export_id = export_id or (batches[0].source.artifact_hash if batches else str(uuid.uuid4()))
        now = datetime.now(UTC)
        with self.session.begin():
            run = LegacyImportRun(
                id=uuid.uuid4(),
                export_id=export_id,
                contract_version=batches[0].source.contract_version,
                mapping_policy_version=policy.version,
                migration_baseline=self.migration_baseline,
                status="RUNNING",
                started_at=now,
            )
            self.session.add(run)
            # One immutable artifact row per source artifact per attempt.
            artifacts = {}
            for batch in batches:
                artifacts[batch.source.artifact_name] = batch
                if batch.entity.value not in {
                    "market",
                    "instrument",
                    "topic",
                    "instrument_topic",
                    "topic_hierarchy",
                }:
                    continue
                for index, record in enumerate(batch.records):
                    self._write_record(run, batch, index, record, policy)
            for filename, batch in artifacts.items():
                self.session.add(
                    LegacyImportArtifact(
                        run_id=run.id,
                        filename=filename or "unknown",
                        sha256=batch.source.artifact_hash,
                        row_count=len(batch.records),
                    )
                )
            run.status, run.completed_at = "COMMITTED", datetime.now(UTC)
        return run.id

    def _write_record(self, run, batch, index, record, policy):
        rule = policy.rule_for(batch.entity.value)
        payload = canonical_mapped_payload(record, rule)
        stable = json.dumps([record.get(k) for k in rule.stable_key], separators=(",", ":"))
        digest = canonical_record_hash(payload)
        previous = self.session.scalar(
            select(LegacyImportRecord)
            .where(
                LegacyImportRecord.entity == batch.entity.value,
                LegacyImportRecord.stable_key == stable,
            )
            .order_by(LegacyImportRecord.id.desc())
        )
        if previous and previous.canonical_payload_hash != digest:
            raise ImportConflict(
                f"stable key conflict: {batch.entity.value}:{stable}; "
                f"existing={previous.canonical_payload_hash} incoming={digest}"
            )
        target = self._upsert(batch.entity.value, payload, stable, digest)
        self.session.add(
            LegacyImportRecord(
                run_id=run.id,
                entity=batch.entity.value,
                stable_key=stable,
                canonical_payload_hash=digest,
                source_filename=batch.source.artifact_name,
                source_row=(
                    batch.lineage[index].source_row if index < len(batch.lineage) else index + 1
                ),
                outcome="NOOP" if previous else "CREATED",
                target_id=target.id,
                payload=payload,
            )
        )

    def _upsert(self, entity, p, stable, digest):
        if entity == "market":
            obj = self.session.scalar(select(Market).where(Market.code == p["code"])) or Market(
                code=p["code"],
                name=p["name"],
                timezone=p["timezone"],
                exchange_code=p.get("exchange_code"),
            )
            self.session.add(obj)
        elif entity == "instrument":
            market = self.session.scalar(select(Market).where(Market.code == p["market_code"]))
            obj = self.session.scalar(
                select(Instrument).where(
                    Instrument.market_id == market.id,
                    Instrument.instrument_code == p["instrument_code"],
                )
            ) or Instrument(
                market=market,
                instrument_code=p["instrument_code"],
                name=p.get("name"),
                instrument_type="EQUITY",
                currency=p.get("currency"),
            )
            self.session.add(obj)
        elif entity == "topic":
            obj = self.session.scalar(select(Topic).where(Topic.slug == p["slug"])) or Topic(
                slug=p["slug"],
                name=p["name"],
                description=p.get("description"),
                status=p.get("status") or "PROPOSED",
            )
            self.session.add(obj)
        elif entity == "instrument_topic":
            instrument = self.session.scalar(
                select(Instrument)
                .join(Market)
                .where(
                    Market.code == p["market_code"],
                    Instrument.instrument_code == p["instrument_code"],
                )
            )
            topic = self.session.scalar(select(Topic).where(Topic.slug == p["topic_slug"]))
            obj = self.session.scalar(
                select(InstrumentTopicRelation).where(
                    InstrumentTopicRelation.instrument_id == instrument.id,
                    InstrumentTopicRelation.topic_id == topic.id,
                    InstrumentTopicRelation.valid_from == _date(p["valid_from"]),
                )
            ) or InstrumentTopicRelation(
                instrument=instrument,
                topic=topic,
                relation_type=p["relation_type"],
                relation_version="v1",
                valid_from=_date(p["valid_from"]),
            )
            self.session.add(obj)
        elif entity == "topic_hierarchy":
            parent = self.session.scalar(select(Topic).where(Topic.slug == p["parent_slug"]))
            child = self.session.scalar(select(Topic).where(Topic.slug == p["child_slug"]))
            if not parent or not child:
                missing = p["parent_slug"] if not parent else p["child_slug"]
                raise ImportConflict(f"topic_hierarchy orphan topic: {missing}")
            obj = self.session.scalar(
                select(TopicHierarchy).where(
                    TopicHierarchy.parent_topic_id == parent.id,
                    TopicHierarchy.child_topic_id == child.id,
                    TopicHierarchy.hierarchy_version == p["hierarchy_version"],
                    TopicHierarchy.valid_from == _date(p["valid_from"]),
                )
            ) or TopicHierarchy(
                parent=parent,
                child=child,
                relationship_type=p["relationship_type"],
                hierarchy_version=p["hierarchy_version"],
                valid_from=_date(p["valid_from"]),
                valid_to=_date(p["valid_to"]) if p.get("valid_to") else None,
                display_order=p.get("display_order"),
            )
            self.session.add(obj)
        else:
            raise ValueError(f"Unsupported writer entity: {entity}")
        self.session.flush()
        return obj
