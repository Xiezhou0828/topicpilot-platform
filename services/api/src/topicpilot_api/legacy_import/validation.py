from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .mapping import MappingPolicy


class ValidationSeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class ValidationIssue:
    severity: ValidationSeverity
    code: str
    message: str
    entity: str
    record_index: int
    field: str | None = None

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "entity": self.entity,
            "record_index": self.record_index,
            "field": self.field,
        }


def validate_batch(
    entity: str, records: list[Mapping[str, Any]], policy: MappingPolicy
) -> list[ValidationIssue]:
    rule = policy.rule_for(entity)
    issues: list[ValidationIssue] = []
    for index, record in enumerate(records):
        for field in rule.fields:
            if field.required and (
                field.source_field not in record or record[field.source_field] in (None, "")
            ):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "REQUIRED_FIELD",
                        f"Missing required field {field.source_field!r}",
                        entity,
                        index,
                        field.source_field,
                    )
                )
            if (
                not field.allow_null
                and record.get(field.source_field) in (None, "")
                and field.source_field in record
            ):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "NULL_NOT_ALLOWED",
                        f"Null is not allowed for {field.source_field!r}",
                        entity,
                        index,
                        field.source_field,
                    )
                )
        if any(record.get(key) in (None, "") for key in rule.stable_key):
            issues.append(
                ValidationIssue(
                    ValidationSeverity.ERROR,
                    "STABLE_KEY",
                    "Stable key is incomplete",
                    entity,
                    index,
                )
            )
    return issues
