from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .exceptions import RegistryAmbiguousError, RegistryNotFoundError, UnsupportedCapabilityError

if TYPE_CHECKING:
    from .contracts import BaseDetector


@dataclass(frozen=True, slots=True)
class DetectorEntry:
    detector_id: str
    detector_version: str
    detector: BaseDetector
    input_profiles: frozenset[str] = frozenset()
    timeframes: frozenset[str] = frozenset()
    grains: frozenset[str] = frozenset()
    runtime_modes: frozenset[str] = frozenset()
    lifecycle: str = "ACTIVE"


class DetectorRegistry:
    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], DetectorEntry] = {}

    def register(self, entry: DetectorEntry) -> None:
        key = (entry.detector_id, entry.detector_version)
        if key in self._entries:
            raise RegistryAmbiguousError("detector identity/version already registered")
        self._entries[key] = entry

    def lookup(
        self, detector_id: str, version: str, *, allow_deprecated: bool = False
    ) -> DetectorEntry:
        entry = self._entries.get((detector_id, version))
        if entry is None or (entry.lifecycle == "DEPRECATED" and not allow_deprecated):
            raise RegistryNotFoundError("detector version is not available")
        return entry

    @staticmethod
    def validate_capability(entry: DetectorEntry, context: Any) -> None:
        checks = (
            (entry.input_profiles, context.input_profile),
            (entry.timeframes, context.timeframe),
            (entry.grains, context.observation_grain),
            (entry.runtime_modes, context.runtime_mode),
        )
        if any(not value or value not in allowed for allowed, value in checks if allowed):
            raise UnsupportedCapabilityError("requested capability is not registered")
