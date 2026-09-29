"""Role-diffusion evidence boundary for Lifecycle.

This module replaces the conceptual use of a daily max-gainer or a 70/30
authority blend with explicit REP/CORE/RELATED evidence.  It emits candidate
evidence only; the existing persistent state machine still owns hysteresis,
illegal-transition protection, and confirmation memory.

All thresholds are required inputs because the Design Freeze does not approve
numeric lifecycle calibration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from .topic_engine.topic_strength_contract import CORE, RELATED, REPRESENTATIVE
from .topic_lifecycle_contract import BACKEND_LIFECYCLE_STAGES

LIFECYCLE_ROLE_EVIDENCE_CONTRACT_VERSION: Final = "topic-lifecycle-role-diffusion.v2"
LIFECYCLE_ABSOLUTE_AUTHORITY: Final = "PRIMARY"
LIFECYCLE_RELATIVE_AUTHORITY: Final = "CONFIRMATION_ONLY"


class LifecycleRoleEvidenceError(ValueError):
    """Raised when lifecycle role evidence is not structurally valid."""


@dataclass(frozen=True)
class LifecycleRoleObservation:
    member_id: str
    role: str
    absolute_return_pct: float | None
    relative_return_pct: float | None = None

    def __post_init__(self) -> None:
        if not self.member_id.strip():
            raise LifecycleRoleEvidenceError("member_id must be non-empty")
        if self.role not in {REPRESENTATIVE, CORE, RELATED}:
            raise LifecycleRoleEvidenceError(
                "lifecycle evidence accepts only REPRESENTATIVE, CORE, RELATED"
            )
        for name in ("absolute_return_pct", "relative_return_pct"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
            ):
                raise LifecycleRoleEvidenceError(f"{name} must be finite or null")


@dataclass(frozen=True)
class RoleDiffusionThresholds:
    """Provisional fixture parameters; values are not production approval."""

    representative_positive_min_pct: float
    core_diffusion_min_breadth: float
    core_diffusion_min_average_pct: float
    related_substantive_min_breadth: float
    related_substantive_min_average_pct: float
    negative_core_min_breadth: float

    def __post_init__(self) -> None:
        for name in (
            "core_diffusion_min_breadth",
            "related_substantive_min_breadth",
            "negative_core_min_breadth",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise LifecycleRoleEvidenceError(f"{name} must be in [0,1]")
        for name in (
            "representative_positive_min_pct",
            "core_diffusion_min_average_pct",
            "related_substantive_min_average_pct",
        ):
            if not math.isfinite(float(getattr(self, name))):
                raise LifecycleRoleEvidenceError(f"{name} must be finite")


@dataclass(frozen=True)
class RoleBucketEvidence:
    role: str
    observed_count: int
    positive_breadth: float | None
    negative_breadth: float | None
    average_absolute_return_pct: float | None
    average_relative_return_pct: float | None


@dataclass(frozen=True)
class LifecycleRoleEvidence:
    contract_version: str
    buckets: tuple[RoleBucketEvidence, ...]
    absolute_authority: str
    relative_authority: str
    dynamic_leader_authority: bool
    role_blend_authority: bool
    representative_confirmation: bool | None
    core_diffusion: bool | None
    related_substantive_diffusion: bool | None
    sprouting_candidate: bool | None
    fermenting_candidate: bool | None
    main_rise_evidence: bool | None
    mature_evidence: bool | None
    declining_evidence: bool | None
    relative_early_warning: bool | None
    previous_stage: str | None
    calibration_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contractVersion": self.contract_version,
            "absoluteAuthority": self.absolute_authority,
            "relativeAuthority": self.relative_authority,
            "dynamicLeaderAuthority": self.dynamic_leader_authority,
            "roleBlendAuthority": self.role_blend_authority,
            "representativeConfirmation": self.representative_confirmation,
            "coreDiffusion": self.core_diffusion,
            "relatedSubstantiveDiffusion": self.related_substantive_diffusion,
            "sproutingCandidate": self.sprouting_candidate,
            "fermentingCandidate": self.fermenting_candidate,
            "mainRiseEvidence": self.main_rise_evidence,
            "matureEvidence": self.mature_evidence,
            "decliningEvidence": self.declining_evidence,
            "relativeEarlyWarning": self.relative_early_warning,
            "previousStage": self.previous_stage,
            "calibrationStatus": self.calibration_status,
            "buckets": [
                {
                    "role": item.role,
                    "observedCount": item.observed_count,
                    "positiveBreadth": item.positive_breadth,
                    "negativeBreadth": item.negative_breadth,
                    "averageAbsoluteReturnPct": item.average_absolute_return_pct,
                    "averageRelativeReturnPct": item.average_relative_return_pct,
                }
                for item in self.buckets
            ],
        }


def _bucket(
    role: str, observations: tuple[LifecycleRoleObservation, ...]
) -> RoleBucketEvidence:
    absolute = tuple(
        float(item.absolute_return_pct)
        for item in observations
        if item.absolute_return_pct is not None
    )
    relative = tuple(
        float(item.relative_return_pct)
        for item in observations
        if item.relative_return_pct is not None
    )
    return RoleBucketEvidence(
        role=role,
        observed_count=len(absolute),
        positive_breadth=sum(value > 0 for value in absolute) / len(absolute)
        if absolute
        else None,
        negative_breadth=sum(value < 0 for value in absolute) / len(absolute)
        if absolute
        else None,
        average_absolute_return_pct=sum(absolute) / len(absolute) if absolute else None,
        average_relative_return_pct=sum(relative) / len(relative) if relative else None,
    )


def build_role_diffusion_evidence(
    observations: tuple[LifecycleRoleObservation, ...],
    *,
    thresholds: RoleDiffusionThresholds,
    previous_stage: str | None = None,
) -> LifecycleRoleEvidence:
    """Build role-specific Lifecycle evidence without stage mutation."""

    if previous_stage is not None and previous_stage not in BACKEND_LIFECYCLE_STAGES:
        raise LifecycleRoleEvidenceError("unknown lifecycle stage")
    ids = tuple(item.member_id for item in observations)
    if len(ids) != len(set(ids)):
        raise LifecycleRoleEvidenceError("lifecycle member observations must be unique")
    buckets = tuple(
        _bucket(role, tuple(item for item in observations if item.role == role))
        for role in (REPRESENTATIVE, CORE, RELATED)
    )
    by_role = {item.role: item for item in buckets}
    rep = by_role[REPRESENTATIVE]
    core = by_role[CORE]
    related = by_role[RELATED]
    representative_confirmation = bool(
        rep.average_absolute_return_pct is not None
        and rep.average_absolute_return_pct >= thresholds.representative_positive_min_pct
    )
    core_diffusion = bool(
        core.positive_breadth is not None
        and core.average_absolute_return_pct is not None
        and core.positive_breadth >= thresholds.core_diffusion_min_breadth
        and core.average_absolute_return_pct >= thresholds.core_diffusion_min_average_pct
    )
    related_substantive = bool(
        related.positive_breadth is not None
        and related.average_absolute_return_pct is not None
        and related.positive_breadth >= thresholds.related_substantive_min_breadth
        and related.average_absolute_return_pct >= thresholds.related_substantive_min_average_pct
    )
    decline = bool(
        core.negative_breadth is not None
        and core.negative_breadth >= thresholds.negative_core_min_breadth
    )
    relative_values = tuple(
        float(item.relative_return_pct)
        for item in observations
        if item.relative_return_pct is not None
    )
    return LifecycleRoleEvidence(
        contract_version=LIFECYCLE_ROLE_EVIDENCE_CONTRACT_VERSION,
        buckets=buckets,
        absolute_authority=LIFECYCLE_ABSOLUTE_AUTHORITY,
        relative_authority=LIFECYCLE_RELATIVE_AUTHORITY,
        dynamic_leader_authority=False,
        role_blend_authority=False,
        representative_confirmation=representative_confirmation,
        core_diffusion=core_diffusion,
        related_substantive_diffusion=related_substantive,
        sprouting_candidate=representative_confirmation and not core_diffusion,
        fermenting_candidate=core_diffusion and not (core_diffusion and related_substantive),
        main_rise_evidence=core_diffusion and related_substantive,
        mature_evidence=(
            previous_stage == "MAIN_RISE" and not core_diffusion and related_substantive
        ),
        declining_evidence=decline if previous_stage in {"MATURE", "MAIN_RISE"} else False,
        relative_early_warning=bool(relative_values),
        previous_stage=previous_stage,
        calibration_status="PROVISIONAL",
    )


__all__ = [
    "LIFECYCLE_ABSOLUTE_AUTHORITY",
    "LIFECYCLE_RELATIVE_AUTHORITY",
    "LIFECYCLE_ROLE_EVIDENCE_CONTRACT_VERSION",
    "LifecycleRoleEvidence",
    "LifecycleRoleEvidenceError",
    "LifecycleRoleObservation",
    "RoleBucketEvidence",
    "RoleDiffusionThresholds",
    "build_role_diffusion_evidence",
]
