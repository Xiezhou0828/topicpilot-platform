"""Frozen Topic Lifecycle vocabulary and role-diffusion boundary.

This module records the V1.2 upstream stage vocabulary recovered by the WS1
preflight and BASE ontology correction.
It does not approve the provisional numeric policy or production publication.
"""

from __future__ import annotations

from typing import Literal

OWNER_LIFECYCLE_STAGES = ("築底", "萌芽", "發酵", "主升", "成熟", "衰退")
BACKEND_LIFECYCLE_STAGES = (
    "BASE",
    "SPROUTING",
    "FERMENTING",
    "MAIN_RISE",
    "MATURE",
    "DECLINING",
)
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

LIFECYCLE_ROLE_EVIDENCE_CONTRACT_VERSION = "topic-lifecycle-role-diffusion.v2"
LIFECYCLE_ABSOLUTE_AUTHORITY = "PRIMARY"
LIFECYCLE_RELATIVE_AUTHORITY = "CONFIRMATION_ONLY"
LIFECYCLE_DYNAMIC_LEADER_ALLOWED = False
LIFECYCLE_ROLE_BLEND_ALLOWED = False


def is_backend_lifecycle_stage(value: str | None) -> bool:
    return value in BACKEND_LIFECYCLE_STAGES


__all__ = [
    "ADJACENT_NON_LIFECYCLE_STATES",
    "BACKEND_LIFECYCLE_STAGES",
    "BACKEND_TO_OWNER_LIFECYCLE_STAGE",
    "LEGACY_PRESENTATION_ALIASES",
    "LIFECYCLE_ABSOLUTE_AUTHORITY",
    "LIFECYCLE_AVAILABILITY_STATES",
    "LIFECYCLE_DYNAMIC_LEADER_ALLOWED",
    "LIFECYCLE_RELATIVE_AUTHORITY",
    "LIFECYCLE_ROLE_BLEND_ALLOWED",
    "LIFECYCLE_ROLE_EVIDENCE_CONTRACT_VERSION",
    "OWNER_LIFECYCLE_STAGES",
    "LifecycleAvailability",
    "is_backend_lifecycle_stage",
]
