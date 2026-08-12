from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class UnsupportedFieldPolicy(StrEnum):
    REJECT = "REJECT"
    PRESERVE_IN_METADATA = "PRESERVE_IN_METADATA"
    DROP_WITH_WARNING = "DROP_WITH_WARNING"


@dataclass(frozen=True)
class FieldMapping:
    source_field: str
    target_field: str
    required: bool = False
    allow_null: bool = True
    transform: str | None = None


@dataclass(frozen=True)
class MappingRule:
    entity: str
    fields: tuple[FieldMapping, ...]
    stable_key: tuple[str, ...]
    unsupported: UnsupportedFieldPolicy = UnsupportedFieldPolicy.PRESERVE_IN_METADATA


@dataclass(frozen=True)
class MappingPolicy:
    version: str
    rules: Mapping[str, MappingRule]

    def rule_for(self, entity: str) -> MappingRule:
        try:
            return self.rules[entity]
        except KeyError as exc:
            raise ValueError(f"No mapping rule registered for entity {entity!r}") from exc


def canonical_mapped_payload(record: Mapping[str, Any], rule: MappingRule) -> dict[str, Any]:
    """Return only deterministic V2-domain fields, after the mapping policy."""
    payload: dict[str, Any] = {}
    for field in rule.fields:
        value = record.get(field.source_field)
        if field.transform == "enabled_to_status":
            value = "ENABLED" if value is True else "DISABLED" if value is False else value
        payload[field.target_field] = value
    return payload


DEFAULT_MAPPING_POLICY = MappingPolicy(
    version="3.6-001.v1",
    rules={
        "market": MappingRule(
            "market",
            (
                FieldMapping("code", "code", True, False),
                FieldMapping("name", "name", True, False),
                FieldMapping("timezone", "timezone", True, False),
                FieldMapping("exchange", "exchange_code"),
            ),
            ("code",),
        ),
        "market_data_source": MappingRule(
            "market_data_source",
            (
                FieldMapping("code", "source_code", True, False),
                FieldMapping("category", "source_category", True, False),
                FieldMapping("adapter_version", "adapter_version", True, False),
            ),
            ("code", "adapter_version"),
        ),
        "instrument": MappingRule(
            "instrument",
            (
                FieldMapping("market", "market_code", True, False),
                FieldMapping("code", "instrument_code", True, False),
                FieldMapping("name", "name"),
                FieldMapping("currency", "currency"),
            ),
            ("market", "code"),
        ),
        "topic": MappingRule(
            "topic",
            (
                FieldMapping("slug", "slug", True, False),
                FieldMapping("name", "name", True, False),
                FieldMapping("description", "description"),
                FieldMapping("enabled", "status", transform="enabled_to_status"),
            ),
            ("slug",),
        ),
        "instrument_topic": MappingRule(
            "instrument_topic",
            (
                FieldMapping("market", "market_code", True, False),
                FieldMapping("instrument", "instrument_code", True, False),
                FieldMapping("topic", "topic_slug", True, False),
                FieldMapping("relation_type", "relation_type", True, False),
                FieldMapping("valid_from", "valid_from", True, False),
            ),
            ("market", "instrument", "topic", "valid_from"),
        ),
        "topic_hierarchy": MappingRule(
            "topic_hierarchy",
            (
                FieldMapping("parent", "parent_slug", True, False),
                FieldMapping("child", "child_slug", True, False),
                FieldMapping("relationship_type", "relationship_type", True, False),
                FieldMapping("hierarchy_version", "hierarchy_version", True, False),
                FieldMapping("valid_from", "valid_from", True, False),
                FieldMapping("valid_to", "valid_to"),
                FieldMapping("display_order", "display_order"),
            ),
            ("parent", "child", "hierarchy_version", "valid_from"),
        ),
        "reference": MappingRule(
            "reference", (), ("namespace", "key", "version"), UnsupportedFieldPolicy.REJECT
        ),
    },
)
