from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .contracts import Generation, Lineage
from .immutability import freeze


@dataclass(frozen=True, slots=True)
class DetectorContext:
    invocation_id: str
    run_id: str
    correlation_id: str
    generation: Generation | str
    detector_id: str
    detector_version: str
    contract_version: str
    input_payload: Mapping[str, Any]
    input_profile: str
    as_of: str
    lineage: Lineage
    runtime_mode: str = "SYNC"
    timeframe: str | None = None
    observation_grain: str | None = None
    timeout_seconds: float | None = None
    cancellation_requested: bool = False

    def __post_init__(self) -> None:
        if not self.invocation_id or not self.detector_id:
            raise ValueError("invocation_id and detector_id are required")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        object.__setattr__(self, "input_payload", freeze(self.input_payload))
