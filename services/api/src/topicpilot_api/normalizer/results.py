from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .contracts import NormalizationFailure, NormalizationResult


@dataclass(frozen=True)
class PersistedCanonicalReference:
    id: UUID
    family_code: str
    quality_state: str
    idempotency_key: str
    supersedes_id: UUID | None
    created: bool


@dataclass(frozen=True)
class RuntimeResult:
    normalization: NormalizationResult
    persisted: tuple[PersistedCanonicalReference, ...]
    existing: tuple[PersistedCanonicalReference, ...] = ()
    failures: tuple[NormalizationFailure, ...] = ()
