from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

type FeatureValue = int | float | dict[str, Any]


class FeatureStatus:
    READY = "READY"
    DATA_INSUFFICIENT = "DATA_INSUFFICIENT"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass(frozen=True)
class FeatureResult:
    feature_name: str
    feature_version: str
    topic_id: str
    as_of: date
    status: str
    value: FeatureValue | None
    coverage: float | None = None
    quality_flags: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FeatureEvaluation:
    """Immutable identity envelope for one deterministic feature-set run."""

    feature_set_version: str
    as_of: date
    results: tuple[FeatureResult, ...]
