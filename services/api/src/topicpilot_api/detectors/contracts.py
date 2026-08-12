from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .config import DetectorConfig
    from .context import DetectorContext
    from .result import DetectorResult


class Result(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class Status(StrEnum):
    COMPLETED = "COMPLETED"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID_INPUT = "INVALID_INPUT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class Generation(StrEnum):
    NEXT_V2 = "NEXT / V2"


@dataclass(frozen=True, slots=True)
class Lineage:
    source: str
    observation_hash: str | None = None
    input_hash: str | None = None


class BaseDetector(Protocol):
    detector_id: str
    detector_version: str
    contract_version: str

    def evaluate(self, context: "DetectorContext", config: "DetectorConfig") -> "DetectorResult": ...
