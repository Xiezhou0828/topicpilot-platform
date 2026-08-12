from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class ImportMode(StrEnum):
    VALIDATE_ONLY = "VALIDATE_ONLY"
    APPLY = "APPLY"


class ImportEntity(StrEnum):
    MARKET = "market"
    MARKET_DATA_SOURCE = "market_data_source"
    INSTRUMENT = "instrument"
    TOPIC = "topic"
    INSTRUMENT_TOPIC = "instrument_topic"
    REFERENCE = "reference"
    TOPIC_HIERARCHY = "topic_hierarchy"


@dataclass(frozen=True)
class ImportSource:
    system: str = "TopicPilot V1"
    repository: str = "LEGACY / V1"
    artifact_name: str = ""
    artifact_hash: str = ""
    contract_version: str = "v1"


@dataclass(frozen=True)
class Lineage:
    source: ImportSource
    source_entity: ImportEntity
    source_key: str
    source_row: int | None = None
    source_fields: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ImportBatch:
    entity: ImportEntity
    records: tuple[Mapping[str, Any], ...]
    lineage: tuple[Lineage, ...]
    source: ImportSource


@dataclass(frozen=True)
class ImportManifest:
    contract_version: str
    mapping_policy_version: str
    source: ImportSource
    created_at: datetime
    batch_hash: str
    entity_counts: Mapping[ImportEntity, int]
