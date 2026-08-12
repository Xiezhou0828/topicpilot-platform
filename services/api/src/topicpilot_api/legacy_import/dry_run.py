from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .contracts import ImportBatch
from .export_contract import canonical_record_hash
from .mapping import MappingPolicy, UnsupportedFieldPolicy, canonical_mapped_payload
from .validation import ValidationIssue, ValidationSeverity


@dataclass(frozen=True)
class DryRunReport:
    records_read: int
    valid: int
    rejected: int
    duplicate: int
    conflicts: int
    warnings: int
    issues: tuple[ValidationIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "records_read": self.records_read,
            "valid": self.valid,
            "rejected": self.rejected,
            "duplicate": self.duplicate,
            "conflicts": self.conflicts,
            "warnings": self.warnings,
            "issues": [i.to_dict() for i in self.issues],
        }


def _issue(
    severity: ValidationSeverity,
    code: str,
    message: str,
    entity: str,
    index: int,
    field: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(severity, code, message, entity, index, field)


def validate_dry_run(
    batches: Iterable[ImportBatch],
    policy: MappingPolicy,
    known_payloads: Mapping[tuple[str, tuple[Any, ...]], str] | None = None,
    *,
    known_markets: Iterable[str] = (),
    known_topics: Iterable[str] = (),
) -> DryRunReport:
    issues: list[ValidationIssue] = []
    records_read = valid = rejected = duplicate = conflicts = warnings = 0
    seen: dict[tuple[str, tuple[Any, ...]], tuple[str, int]] = {}
    known_payloads = known_payloads or {}
    market_codes, topic_slugs = set(known_markets), set(known_topics)
    for batch in batches:
        rule = policy.rule_for(batch.entity.value)
        for index, record in enumerate(batch.records):
            records_read += 1
            errors_before = len(issues)
            key_values = tuple(record.get(k) for k in rule.stable_key)
            key = (batch.entity.value, key_values)
            if any(v in (None, "") for v in key_values):
                issues.append(
                    _issue(
                        ValidationSeverity.ERROR,
                        "STABLE_KEY",
                        "Stable key is incomplete",
                        batch.entity.value,
                        index,
                    )
                )
            for field in rule.fields:
                if field.required and (
                    field.source_field not in record or record[field.source_field] in (None, "")
                ):
                    issues.append(
                        _issue(
                            ValidationSeverity.ERROR,
                            "REQUIRED_FIELD",
                            f"Missing required field {field.source_field!r}",
                            batch.entity.value,
                            index,
                            field.source_field,
                        )
                    )
                elif not field.allow_null and record.get(field.source_field) is None:
                    issues.append(
                        _issue(
                            ValidationSeverity.ERROR,
                            "NULL_NOT_ALLOWED",
                            f"Null is not allowed for {field.source_field!r}",
                            batch.entity.value,
                            index,
                            field.source_field,
                        )
                    )
            if market_codes and record.get("market") and record["market"] not in market_codes:
                issues.append(
                    _issue(
                        ValidationSeverity.ERROR,
                        "MARKET_MAPPING",
                        "Unknown market mapping",
                        batch.entity.value,
                        index,
                        "market",
                    )
                )
            if topic_slugs and record.get("topic") and record["topic"] not in topic_slugs:
                issues.append(
                    _issue(
                        ValidationSeverity.ERROR,
                        "TOPIC_MAPPING",
                        "Unknown topic mapping",
                        batch.entity.value,
                        index,
                        "topic",
                    )
                )
            supported = {f.source_field for f in rule.fields} | set(rule.stable_key)
            for field in sorted(set(record) - supported):
                if rule.unsupported == UnsupportedFieldPolicy.REJECT:
                    issues.append(
                        _issue(
                            ValidationSeverity.ERROR,
                            "UNSUPPORTED_FIELD",
                            f"Unsupported field {field!r}",
                            batch.entity.value,
                            index,
                            field,
                        )
                    )
                else:
                    issues.append(
                        _issue(
                            ValidationSeverity.WARNING,
                            "UNSUPPORTED_FIELD",
                            f"Preserved unsupported field {field!r}",
                            batch.entity.value,
                            index,
                            field,
                        )
                    )
            payload_hash = canonical_record_hash(canonical_mapped_payload(record, rule))
            if key in seen:
                previous_hash, _ = seen[key]
                if previous_hash == payload_hash:
                    duplicate += 1
                    issues.append(
                        _issue(
                            ValidationSeverity.WARNING,
                            "DUPLICATE",
                            "Repeated stable key with identical payload",
                            batch.entity.value,
                            index,
                        )
                    )
                else:
                    conflicts += 1
                    issues.append(
                        _issue(
                            ValidationSeverity.ERROR,
                            "CONFLICT",
                            "Stable key has different payload",
                            batch.entity.value,
                            index,
                        )
                    )
            elif (
                key_values
                and all(v not in (None, "") for v in key_values)
                and key in known_payloads
                and known_payloads[key] != payload_hash
            ):
                conflicts += 1
                issues.append(
                    _issue(
                        ValidationSeverity.ERROR,
                        "CONFLICT",
                        "Stable key conflicts with known payload",
                        batch.entity.value,
                        index,
                    )
                )
            else:
                seen[key] = (payload_hash, index)
            record_issues = issues[errors_before:]
            if not any(i.severity == ValidationSeverity.ERROR for i in record_issues):
                valid += 1
            else:
                rejected += 1
            warnings += sum(i.severity == ValidationSeverity.WARNING for i in record_issues)
    if valid + rejected != records_read:
        raise AssertionError("dry-run report invariant violated: valid + rejected != records_read")
    return DryRunReport(
        records_read, valid, rejected, duplicate, conflicts, warnings, tuple(issues)
    )
