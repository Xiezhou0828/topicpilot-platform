from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .exceptions import InvalidConfigurationError


@dataclass(frozen=True, slots=True)
class DetectorConfig:
    detector_id: str
    configuration_version: str
    values: Mapping[str, Any]
    schema_version: str = "1"
    resolved_hash: str = ""

    def __post_init__(self) -> None:
        if not self.detector_id or not self.configuration_version:
            raise InvalidConfigurationError(
                "detector identity and configuration version are required"
            )
        frozen = MappingProxyType(json.loads(json.dumps(dict(self.values), sort_keys=True)))
        digest = hashlib.sha256(
            json.dumps(dict(frozen), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        object.__setattr__(self, "values", frozen)
        if self.resolved_hash and self.resolved_hash != digest:
            raise InvalidConfigurationError("configuration hash does not match values")
        object.__setattr__(self, "resolved_hash", digest)

    @classmethod
    def resolve(
        cls, detector_id: str, version: str, values: Mapping[str, Any] | None = None
    ) -> DetectorConfig:
        return cls(detector_id, version, values or {})
