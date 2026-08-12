from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from typing import Any, Protocol

FAMILIES = ("PRICE", "VOLUME", "QUOTE", "TRADING_STATUS")


def escape_json_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def json_pointer(*tokens: str) -> str:
    return "/" + "/".join(escape_json_pointer_token(token) for token in tokens)


@dataclass(frozen=True)
class InputEnvelope:
    payload: dict[str, Any]
    instrument_id: uuid.UUID
    source_id: uuid.UUID
    timeline_entry_id: uuid.UUID
    raw_observation_id: uuid.UUID
    observed_at: datetime
    received_at: datetime
    retrieved_at: datetime
    ordering_key: str


@dataclass(frozen=True)
class ReferenceContext:
    reference_data_version: str
    timezone_name: str
    session_code: str
    calendar_code: str
    currency_code: str
    currency_scale: int
    status_catalogue_version: str = "reference-data-v1"
    statuses: frozenset[str] = frozenset()


@dataclass(frozen=True)
class MappingPolicy:
    normalization_contract_version: str = "normalization-contract-v1"
    mapping_policy_version: str = "synthetic-mapping-v1"
    persist_quarantined: bool = True
    session_code: str = "REGULAR"
    calendar_code: str | None = None


@dataclass(frozen=True)
class ReferenceContextRequest:
    reference_data_version: str
    currency_code: str
    timezone_name: str
    session_code: str
    calendar_code: str | None = None


@dataclass(frozen=True)
class NormalizationCandidate:
    family_code: str
    values: dict[str, Any]
    source_paths: tuple[str, ...]
    quality_state: str = "ACCEPTED"
    warnings: tuple[str, ...] = ()
    validation: dict[str, Any] = field(default_factory=dict)
    supersedes_id: str | None = None

    @property
    def source_field_path(self):
        return self.source_paths[0] if self.source_paths else None


@dataclass(frozen=True)
class NormalizationResult:
    candidates: tuple[NormalizationCandidate, ...]
    failures: tuple[NormalizationFailure, ...] = ()


@dataclass(frozen=True)
class NormalizationFailure:
    quality_state: str
    code: str
    detail: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReferenceContextLoader(Protocol):
    def load_reference_context(self, request: ReferenceContextRequest) -> ReferenceContext: ...


class NormalizerMapper(Protocol):
    def __call__(
        self, envelope: InputEnvelope, reference: ReferenceContext, policy: MappingPolicy
    ) -> NormalizationResult: ...


def decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _canonical(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, Decimal):
        # Numeric canonical fields are scale-independent: trailing zeroes do
        # not change the represented value; negative zero is canonical zero.
        normalized = value.normalize()
        return "0" if normalized == 0 else format(normalized, "f")
    if isinstance(value, datetime):
        return ensure_utc(value).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {str(k): _canonical(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(
            (_canonical(item) for item in value),
            key=lambda item: json.dumps(item, ensure_ascii=False, separators=(",", ":")),
        )
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def stable_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("observed time must be timezone-aware")
    # Keep Python 3.10 compatibility for the private provider runtime.
    return value.astimezone(timezone.utc)  # noqa: UP017
