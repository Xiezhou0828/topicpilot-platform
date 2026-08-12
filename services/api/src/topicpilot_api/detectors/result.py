from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .contracts import Result, Status
from .exceptions import InvalidDetectorOutputError
from .immutability import freeze


@dataclass(frozen=True, slots=True)
class Evidence:
    summary: str | None = None
    facts: Mapping[str, Any] = None  # type: ignore[assignment]
    observation_window: str | None = None
    lineage_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "facts", MappingProxyType(dict(self.facts or {})))


@dataclass(frozen=True, slots=True)
class Diagnostics:
    code: str | None = None
    message: str | None = None
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", tuple(self.details)[:10])
        if sum(len(x) for x in self.details) > 2000:
            raise InvalidDetectorOutputError("diagnostics are too large")


@dataclass(frozen=True, slots=True)
class DetectorResult:
    detector_id: str
    detector_version: str
    result: Result
    status: Status
    confidence: float | None = None
    evidence: Evidence = field(default_factory=Evidence)
    diagnostics: Diagnostics = field(default_factory=Diagnostics)
    configuration_version: str | None = None
    run_id: str | None = None
    lineage: str | None = None
    metadata: Mapping[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.status is not Status.COMPLETED and self.result in (Result.PASS, Result.FAIL):
            raise InvalidDetectorOutputError("authoritative PASS/FAIL requires COMPLETED status")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise InvalidDetectorOutputError("confidence must be between 0 and 1")
        object.__setattr__(self, "metadata", freeze(self.metadata or {}))
