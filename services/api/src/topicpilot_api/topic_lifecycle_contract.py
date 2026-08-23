"""Frozen Topic Lifecycle V0 contract vocabulary and availability boundary.

This module records the existing V2 contract recovered by the WS1 preflight.
It does not approve the provisional numeric policy or production publication.
"""

from __future__ import annotations

from typing import Literal

OWNER_LIFECYCLE_STAGES = ("萌芽", "發酵", "主升", "成熟", "衰退")
BACKEND_LIFECYCLE_STAGES = ("SPROUTING", "FERMENTING", "MAIN_RISE", "MATURE", "DECLINING")
BACKEND_TO_OWNER_LIFECYCLE_STAGE = dict(
    zip(BACKEND_LIFECYCLE_STAGES, OWNER_LIFECYCLE_STAGES, strict=True)
)

# These aliases are retained presentation lineage, not additional stages.
LEGACY_PRESENTATION_ALIASES = {"高檔整理": "成熟", "退潮": "衰退"}
ADJACENT_NON_LIFECYCLE_STATES = frozenset({"升溫", "降溫", "WARMING", "COOLING", "觀察"})

LifecycleAvailability = Literal[
    "AVAILABLE",
    "FORMAL_AVAILABLE",
    "SHADOW_AVAILABLE",
    "INSUFFICIENT_DATA",
    "PENDING",
    "PREVIEW",
    "NOT_AVAILABLE",
    "WAITING_FOR_FORMAL_LINEAGE",
    "FAIL_CLOSED",
]

LIFECYCLE_AVAILABILITY_STATES = (
    "AVAILABLE",
    "FORMAL_AVAILABLE",
    "SHADOW_AVAILABLE",
    "INSUFFICIENT_DATA",
    "PENDING",
    "PREVIEW",
    "NOT_AVAILABLE",
    "WAITING_FOR_FORMAL_LINEAGE",
    "FAIL_CLOSED",
)


def is_backend_lifecycle_stage(value: str | None) -> bool:
    return value in BACKEND_LIFECYCLE_STAGES


__all__ = [
    "ADJACENT_NON_LIFECYCLE_STATES",
    "BACKEND_LIFECYCLE_STAGES",
    "BACKEND_TO_OWNER_LIFECYCLE_STAGE",
    "LEGACY_PRESENTATION_ALIASES",
    "LIFECYCLE_AVAILABILITY_STATES",
    "OWNER_LIFECYCLE_STAGES",
    "LifecycleAvailability",
    "is_backend_lifecycle_stage",
]
