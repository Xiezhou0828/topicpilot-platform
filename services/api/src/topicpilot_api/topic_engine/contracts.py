from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class EvaluationBundle:
    calculation_version: str
    as_of: date
    topics: tuple[dict[str, Any], ...] = ()
    memberships: tuple[dict[str, Any], ...] = ()
    hierarchy: tuple[dict[str, Any], ...] = ()
    observations: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class TopicState:
    topic_id: str
    as_of: date
    calculation_version: str
    status: str
    score: float | None
    grade: str | None
    strength: str | None
    coverage: float | None
    member_count: int
    observed_member_count: int
    quality_flags: tuple[str, ...] = field(default_factory=tuple)


def evaluate(bundle: EvaluationBundle) -> tuple[TopicState, ...]:
    from .scoring import calculate_states

    return calculate_states(bundle)
