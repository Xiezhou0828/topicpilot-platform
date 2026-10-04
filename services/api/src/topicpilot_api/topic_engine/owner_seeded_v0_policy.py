"""Owner-seeded V0 Topic Strength and Lifecycle policy.

This module is an explicit, opt-in policy surface.  It is intentionally
separate from the existing calibration-required and Production policy paths.
The values are Owner input from ``TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-
V0-POLICY-001``; this module does not fit, optimize, or infer them from
historical data.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import date
from statistics import median
from typing import Final, Literal

from .topic_strength_contract import (
    CORE,
    RELATED,
    REPRESENTATIVE,
    benchmark_for_market,
)

POLICY_ID: Final = "topic-strength-lifecycle.owner-seeded-v0"
POLICY_VERSION: Final = "v0"
POLICY_SCHEMA_VERSION: Final = "topic-strength-lifecycle-owner-seeded-v0.v1"
CALIBRATION_METHOD: Final = "OWNER_SEEDED_FROM_DESIGN_FREEZE"
HISTORICAL_CALIBRATION: Final = "NOT_AVAILABLE"
PROVISIONAL: Final = "YES"
OWNER_APPROVED_FOR_REVIEW: Final = "YES"
PRODUCTION_ACTIVE: Final = False
ROLE_ORDER: Final = (REPRESENTATIVE, CORE, RELATED)
LIFECYCLE_STAGES: Final = (
    "BASE",
    "SPROUTING",
    "FERMENTING",
    "MAIN_RISE",
    "MATURE",
    "DECLINING",
)


class OwnerSeededV0Error(ValueError):
    """Raised when the explicit Owner-seeded policy contract is violated."""


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OwnerSeededV0Error(f"{name} must be finite")
    result = float(value)
    if not math.isfinite(result):
        raise OwnerSeededV0Error(f"{name} must be finite")
    return result


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


@dataclass(frozen=True)
class PiecewiseLinearCurve:
    """Monotonic bounded curve with endpoint clamping."""

    name: str
    knots: tuple[tuple[float, float], ...]
    cap: float

    def __post_init__(self) -> None:
        if not self.name.strip() or len(self.knots) < 2:
            raise OwnerSeededV0Error("curve name and at least two knots are required")
        cap = _finite(self.cap, "curve cap")
        if cap <= 0:
            raise OwnerSeededV0Error("curve cap must be positive")
        previous_x: float | None = None
        previous_y: float | None = None
        for x, y in self.knots:
            x_value = _finite(x, "curve x")
            y_value = _finite(y, "curve y")
            if not 0.0 <= y_value <= cap:
                raise OwnerSeededV0Error("curve output must be within its cap")
            if previous_x is not None and x_value <= previous_x:
                raise OwnerSeededV0Error("curve x knots must be strictly increasing")
            if previous_y is not None and y_value < previous_y:
                raise OwnerSeededV0Error("curve must be monotonic")
            previous_x, previous_y = x_value, y_value

    def evaluate(self, value: float) -> float:
        value = _finite(value, "curve input")
        if value <= self.knots[0][0]:
            return self.knots[0][1]
        if value >= self.knots[-1][0]:
            return self.knots[-1][1]
        for (left_x, left_y), (right_x, right_y) in zip(self.knots, self.knots[1:], strict=True):
            if value <= right_x:
                ratio = (value - left_x) / (right_x - left_x)
                return left_y + ratio * (right_y - left_y)
        return self.knots[-1][1]

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "cap": self.cap,
            "knots": [
                {"inputPct": input_pct, "points": points} for input_pct, points in self.knots
            ],
        }


@dataclass(frozen=True)
class BucketTable:
    """Half-open lower/upper bucket table used by RELATED V0."""

    name: str
    rows: tuple[tuple[float, float | None, float], ...]

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.rows:
            raise OwnerSeededV0Error("bucket table requires a name and rows")
        previous_upper: float | None = None
        for lower, upper, value in self.rows:
            lower_value = _finite(lower, "bucket lower bound")
            value_float = _finite(value, "bucket value")
            if upper is not None:
                upper_value = _finite(upper, "bucket upper bound")
                if upper_value <= lower_value:
                    raise OwnerSeededV0Error("bucket upper bound must exceed lower bound")
            else:
                upper_value = None
            if previous_upper is not None and lower_value != previous_upper:
                raise OwnerSeededV0Error("bucket ranges must be contiguous")
            previous_upper = upper_value
            if not math.isfinite(value_float):
                raise OwnerSeededV0Error("bucket value must be finite")

    def evaluate(self, value: float) -> float:
        value = _finite(value, "bucket input")
        if value < self.rows[0][0]:
            return self.rows[0][2]
        for lower, upper, points in self.rows:
            if value >= lower and (upper is None or value < upper):
                return points
        return self.rows[-1][2]

    def as_dict(self) -> list[dict[str, float | None]]:
        return [
            {"lowerInclusive": lower, "upperExclusive": upper, "value": value}
            for lower, upper, value in self.rows
        ]


@dataclass(frozen=True)
class ScoreImportancePolicy:
    representative: tuple[float, ...] = (1.25, 1.50, 1.75)
    core: tuple[float, ...] = (0.50, 0.75, 1.00)

    def __post_init__(self) -> None:
        if self.representative != (1.25, 1.50, 1.75):
            raise OwnerSeededV0Error("REP Score Importance must use the Owner domain")
        if self.core != (0.50, 0.75, 1.00):
            raise OwnerSeededV0Error("CORE Score Importance must use the Owner domain")

    def legal_for(self, role: str) -> tuple[float, ...]:
        if role == REPRESENTATIVE:
            return self.representative
        if role == CORE:
            return self.core
        if role == RELATED:
            return ()
        raise OwnerSeededV0Error(f"unknown role: {role}")

    def as_dict(self) -> dict[str, list[float]]:
        return {
            "REPRESENTATIVE": list(self.representative),
            "CORE": list(self.core),
            "RELATED": [],
        }


@dataclass(frozen=True)
class AbsoluteGradePolicy:
    exceptional_min: float = 82.0
    clear_min: float = 62.0
    d_core_median_max: float = -1.50
    d_core_positive_breadth_max: float = 0.25
    d_core_weak_ratio_min: float = 0.60
    d_rep_weighted_raw_max: float = -1.00
    d_core_median_deep_max: float = -2.50


@dataclass(frozen=True)
class RelativeGradePolicy:
    exceptional_min: float = 80.0
    clear_min: float = 63.0
    d_total_max: float = 42.0
    d_core_median_max: float = -1.50
    d_core_positive_breadth_max: float = 0.25
    d_core_weak_ratio_min: float = 0.60
    d_rep_weighted_raw_max: float = -1.00
    d_core_median_deep_max: float = -2.50


@dataclass(frozen=True)
class LifecyclePolicy:
    """Exact Owner-seeded lifecycle evidence and hysteresis values."""

    sprouting_rep_raw_min: float = 0.80
    sprouting_core_positive_breadth_max: float = 0.50
    sprouting_core_median_min: float = -1.00
    sprouting_core_median_max: float = 1.50
    sprouting_confirmation_sessions: int = 1

    fermenting_core_positive_breadth_min: float = 0.50
    fermenting_core_median_min: float = 1.00
    fermenting_core_strong_breadth_min: float = 0.25
    fermenting_rep_raw_min: float = -1.50
    fermenting_window_sessions: int = 3
    fermenting_required_sessions: int = 2

    main_rise_core_positive_breadth_min: float = 0.65
    main_rise_core_median_min: float = 2.00
    main_rise_core_strong_breadth_min: float = 0.40
    main_rise_related_positive_breadth_min: float = 0.50
    main_rise_related_positive_median_min: float = 1.00
    main_rise_rep_raw_min: float = -1.00
    main_rise_window_sessions: int = 3
    main_rise_required_sessions: int = 2

    expansion_lookback_sessions: int = 5
    expansion_core_breadth_delta: float = 0.10
    expansion_core_median_min: float = 1.50
    expansion_related_breadth_delta: float = 0.15
    expansion_related_core_breadth_min: float = 0.55
    expansion_related_median_min: float = 0.75

    mature_no_expansion_sessions: int = 3
    mature_core_breadth_drawdown: float = 0.20
    mature_core_median_drawdown: float = 1.50
    mature_rep_nonpositive_required: int = 2
    mature_rep_nonpositive_window: int = 3
    mature_late_related_breadth_min: float = 0.50
    mature_late_core_breadth_max: float = 0.50
    mature_confirmation_sessions: int = 2

    declining_core_median_max: float = -1.50
    declining_core_positive_breadth_max: float = 0.30
    declining_core_weak_ratio_min: float = 0.50
    declining_rep_raw_max: float = -1.00
    declining_core_median_deep_max: float = -2.50
    declining_confirmation_sessions: int = 2

    reset_grade: str = "B"
    reset_core_median_min: float = -0.50
    reset_core_median_max: float = 0.50
    reset_core_weak_ratio_max: float = 0.30
    reset_core_positive_breadth_min: float = 0.30
    reset_core_positive_breadth_max: float = 0.60
    reset_confirmation_sessions: int = 3

    relative_deterioration_strength_max: float = 45.0

    def __post_init__(self) -> None:
        percentage_fields = (
            "sprouting_core_positive_breadth_max",
            "fermenting_core_positive_breadth_min",
            "fermenting_core_strong_breadth_min",
            "main_rise_core_positive_breadth_min",
            "main_rise_core_strong_breadth_min",
            "main_rise_related_positive_breadth_min",
            "expansion_core_breadth_delta",
            "expansion_related_breadth_delta",
            "expansion_related_core_breadth_min",
            "mature_core_breadth_drawdown",
            "mature_late_related_breadth_min",
            "mature_late_core_breadth_max",
            "declining_core_positive_breadth_max",
            "declining_core_weak_ratio_min",
            "reset_core_weak_ratio_max",
            "reset_core_positive_breadth_min",
            "reset_core_positive_breadth_max",
        )
        for name in percentage_fields:
            value = _finite(getattr(self, name), name)
            if not 0.0 <= value <= 1.0:
                raise OwnerSeededV0Error(f"{name} must be in [0,1]")
        for name in (
            "sprouting_confirmation_sessions",
            "fermenting_window_sessions",
            "fermenting_required_sessions",
            "main_rise_window_sessions",
            "main_rise_required_sessions",
            "expansion_lookback_sessions",
            "mature_no_expansion_sessions",
            "mature_rep_nonpositive_required",
            "mature_rep_nonpositive_window",
            "mature_confirmation_sessions",
            "declining_confirmation_sessions",
            "reset_confirmation_sessions",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise OwnerSeededV0Error(f"{name} must be a positive integer")

    def as_dict(self) -> dict[str, object]:
        return {key: value for key, value in self.__dict__.items()}


@dataclass(frozen=True)
class OwnerSeededV0Policy:
    absolute_representative: PiecewiseLinearCurve
    absolute_core: PiecewiseLinearCurve
    relative_representative: PiecewiseLinearCurve
    relative_core: PiecewiseLinearCurve
    absolute_related_breadth: BucketTable
    absolute_related_quality: BucketTable
    relative_related_breadth: BucketTable
    relative_related_quality: BucketTable
    score_importance: ScoreImportancePolicy = field(default_factory=ScoreImportancePolicy)
    absolute_grade: AbsoluteGradePolicy = field(default_factory=AbsoluteGradePolicy)
    relative_grade: RelativeGradePolicy = field(default_factory=RelativeGradePolicy)
    lifecycle: LifecyclePolicy = field(default_factory=LifecyclePolicy)

    def as_dict(self) -> dict[str, object]:
        return {
            "policyId": POLICY_ID,
            "policyVersion": POLICY_VERSION,
            "calibrationMethod": CALIBRATION_METHOD,
            "historicalCalibration": HISTORICAL_CALIBRATION,
            "provisional": PROVISIONAL,
            "ownerApprovedForReview": OWNER_APPROVED_FOR_REVIEW,
            "productionActive": PRODUCTION_ACTIVE,
            "roles": {
                "order": list(ROLE_ORDER),
                "caps": {REPRESENTATIVE: 30.0, CORE: 60.0, RELATED: 10.0},
            },
            "scoreImportance": self.score_importance.as_dict(),
            "absolute": {
                "representativeCurve": self.absolute_representative.as_dict(),
                "coreCurve": self.absolute_core.as_dict(),
                "relatedBreadth": self.absolute_related_breadth.as_dict(),
                "relatedMagnitudeQuality": self.absolute_related_quality.as_dict(),
                "grade": self.absolute_grade.__dict__,
            },
            "relative": {
                "benchmarkByMarket": {"TWSE": "TAIEX", "TPEX": "TPEX_INDEX"},
                "representativeCurve": self.relative_representative.as_dict(),
                "coreCurve": self.relative_core.as_dict(),
                "relatedBreadth": self.relative_related_breadth.as_dict(),
                "relatedMagnitudeQuality": self.relative_related_quality.as_dict(),
                "grade": self.relative_grade.__dict__,
            },
            "lifecycle": self.lifecycle.as_dict(),
            "relationWeight": "EXCLUDED",
            "coverage": "EVIDENCE_ONLY_NOT_A_MULTIPLIER",
            "lifecycleAuthority": {
                "absolute": "PRIMARY",
                "relative": "CONFIRMATION_ONLY",
                "dynamicLeader": False,
            },
        }

    def policy_hash(self) -> str:
        payload = json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


DEFAULT_POLICY: Final = OwnerSeededV0Policy(
    absolute_representative=PiecewiseLinearCurve(
        "absolute-representative-v0",
        (
            (-5.00, 0.0),
            (-3.00, 3.0),
            (-2.00, 6.0),
            (-1.00, 10.0),
            (0.00, 14.0),
            (0.50, 18.0),
            (1.00, 21.0),
            (1.50, 24.0),
            (2.00, 26.0),
            (3.00, 28.5),
            (5.00, 30.0),
        ),
        30.0,
    ),
    absolute_core=PiecewiseLinearCurve(
        "absolute-core-v0",
        (
            (-6.00, 0.0),
            (-4.00, 3.0),
            (-3.00, 7.0),
            (-2.00, 12.0),
            (-1.00, 20.0),
            (0.00, 27.0),
            (1.00, 34.0),
            (2.00, 42.0),
            (3.00, 49.0),
            (4.00, 54.0),
            (5.00, 57.0),
            (7.00, 60.0),
        ),
        60.0,
    ),
    relative_representative=PiecewiseLinearCurve(
        "relative-representative-v0",
        (
            (-4.00, 2.0),
            (-3.00, 5.0),
            (-2.00, 8.0),
            (-1.00, 12.0),
            (-0.50, 14.0),
            (0.00, 15.0),
            (0.50, 19.0),
            (1.00, 23.0),
            (2.00, 27.0),
            (3.00, 29.0),
            (4.00, 30.0),
        ),
        30.0,
    ),
    relative_core=PiecewiseLinearCurve(
        "relative-core-v0",
        (
            (-5.00, 5.0),
            (-4.00, 10.0),
            (-3.00, 16.0),
            (-2.00, 22.0),
            (-1.00, 29.0),
            (-0.50, 32.0),
            (0.00, 35.0),
            (0.50, 39.0),
            (1.00, 43.0),
            (2.00, 50.0),
            (3.00, 55.0),
            (4.00, 58.0),
            (6.00, 60.0),
        ),
        60.0,
    ),
    absolute_related_breadth=BucketTable(
        "absolute-related-breadth-v0",
        (
            (0.00, 0.20, 0.0),
            (0.20, 0.30, 1.0),
            (0.30, 0.40, 2.0),
            (0.40, 0.50, 3.5),
            (0.50, 0.60, 5.0),
            (0.60, 0.70, 6.5),
            (0.70, 0.80, 8.0),
            (0.80, 0.90, 9.0),
            (0.90, None, 10.0),
        ),
    ),
    absolute_related_quality=BucketTable(
        "absolute-related-positive-median-quality-v0",
        (
            (0.00, 0.25, 0.25),
            (0.25, 0.50, 0.50),
            (0.50, 1.00, 0.75),
            (1.00, 2.00, 0.90),
            (2.00, None, 1.00),
        ),
    ),
    relative_related_breadth=BucketTable(
        "relative-related-breadth-v0",
        (
            (0.00, 0.20, 0.0),
            (0.20, 0.30, 1.0),
            (0.30, 0.40, 2.0),
            (0.40, 0.50, 3.5),
            (0.50, 0.60, 5.0),
            (0.60, 0.70, 6.5),
            (0.70, 0.80, 8.0),
            (0.80, 0.90, 9.0),
            (0.90, None, 10.0),
        ),
    ),
    relative_related_quality=BucketTable(
        "relative-related-positive-median-quality-v0",
        (
            (0.00, 0.20, 0.25),
            (0.20, 0.50, 0.50),
            (0.50, 1.00, 0.75),
            (1.00, 1.75, 0.90),
            (1.75, None, 1.00),
        ),
    ),
)


@dataclass(frozen=True)
class MemberObservation:
    member_id: str
    role: str
    absolute_return_pct: float | None
    score_importance: float | None = None
    market: str | None = None
    benchmark_return_pct: float | None = None

    def __post_init__(self) -> None:
        if not self.member_id.strip() or self.member_id != self.member_id.strip():
            raise OwnerSeededV0Error("member_id must be a trimmed non-empty string")
        if self.role not in ROLE_ORDER:
            raise OwnerSeededV0Error(f"unsupported structural role: {self.role}")
        for name in ("absolute_return_pct", "score_importance", "benchmark_return_pct"):
            value = getattr(self, name)
            if value is not None:
                _finite(value, name)

    def value_for(self, view: Literal["ABSOLUTE", "RELATIVE"]) -> float | None:
        if view == "ABSOLUTE":
            return self.absolute_return_pct
        if view != "RELATIVE":
            raise OwnerSeededV0Error("view must be ABSOLUTE or RELATIVE")
        if self.absolute_return_pct is None or self.benchmark_return_pct is None:
            return None
        benchmark_for_market(self.market or "")
        return float(self.absolute_return_pct) - float(self.benchmark_return_pct)


@dataclass(frozen=True)
class RoleEvidenceV0:
    role: str
    formal_count: int
    observed_count: int
    valid_count: int
    positive_breadth: float | None
    strong_breadth: float | None
    weak_ratio: float | None
    median_return: float | None
    positive_median_return: float | None
    weighted_raw_return: float | None
    contribution: float

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class StrengthViewResult:
    view: Literal["ABSOLUTE", "RELATIVE"]
    status: str
    strength: float | None
    grade: str | None
    d_guard: bool
    role_evidence: tuple[RoleEvidenceV0, ...]
    grade_basis: tuple[str, ...]
    benchmark_by_market: tuple[tuple[str, str], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "view": self.view,
            "status": self.status,
            "strength": self.strength,
            "grade": self.grade,
            "dGuard": self.d_guard,
            "gradeBasis": list(self.grade_basis),
            "benchmarkByMarket": dict(self.benchmark_by_market),
            "roleEvidence": [item.as_dict() for item in self.role_evidence],
        }


@dataclass(frozen=True)
class TopicEvaluationResult:
    topic_id: str
    trading_date: date
    formal_member_count: int
    observed_member_count: int
    policy_version: str
    absolute: StrengthViewResult
    relative: StrengthViewResult

    def as_dict(self) -> dict[str, object]:
        return {
            "topicId": self.topic_id,
            "tradingDate": self.trading_date.isoformat(),
            "policyVersion": self.policy_version,
            "formalMemberCount": self.formal_member_count,
            "observedMemberCount": self.observed_member_count,
            "absolute": self.absolute.as_dict(),
            "relative": self.relative.as_dict(),
        }


def _empty_role_evidence(role: str, formal_count: int) -> RoleEvidenceV0:
    return RoleEvidenceV0(role, formal_count, 0, 0, None, None, None, None, None, None, 0.0)


def _empty_view(
    view: Literal["ABSOLUTE", "RELATIVE"],
    members: tuple[MemberObservation, ...],
    status: str,
    reason: str,
) -> StrengthViewResult:
    role_evidence = tuple(
        _empty_role_evidence(role, sum(item.role == role for item in members))
        for role in ROLE_ORDER
    )
    return StrengthViewResult(
        view=view,
        status=status,
        strength=None,
        grade="X" if status == "NOT_EVALUABLE" else None,
        d_guard=False,
        role_evidence=role_evidence,
        grade_basis=(reason,),
        benchmark_by_market=(),
    )


def _validate_importance(member: MemberObservation, policy: OwnerSeededV0Policy) -> None:
    legal = policy.score_importance.legal_for(member.role)
    if member.role == RELATED:
        if member.score_importance is not None:
            raise OwnerSeededV0Error("RELATED must not carry per-member Score Importance")
        return
    if member.score_importance is None:
        raise OwnerSeededV0Error(f"{member.role} Score Importance is required")
    if round(float(member.score_importance), 2) not in legal:
        raise OwnerSeededV0Error(f"Score Importance is invalid for {member.role}")


def _role_evidence(
    role: str,
    members: tuple[MemberObservation, ...],
    values: dict[str, float | None],
    curve: PiecewiseLinearCurve | None,
    policy: OwnerSeededV0Policy,
) -> RoleEvidenceV0:
    role_members = tuple(item for item in members if item.role == role)
    valid_pairs = tuple(
        (item, values[item.member_id])
        for item in role_members
        if values[item.member_id] is not None
    )
    valid = tuple(float(value) for _, value in valid_pairs)
    positive = tuple(value for value in valid if value > 0)
    weights = tuple(float(item.score_importance) for item, _ in valid_pairs if item.role != RELATED)
    weighted_raw = (
        sum(float(value) * float(item.score_importance) for item, value in valid_pairs)
        / sum(weights)
        if valid_pairs and role != RELATED
        else None
    )
    if role == RELATED:
        contribution = 0.0
        if valid:
            breadth = len(positive) / len(valid)
            positive_median = median(positive) if positive else None
            breadth_table = policy.absolute_related_breadth
            # The caller replaces this contribution with the view-specific table.
            contribution = breadth_table.evaluate(breadth)
            if positive_median is not None:
                contribution *= policy.absolute_related_quality.evaluate(positive_median)
            else:
                contribution = 0.0
        return RoleEvidenceV0(
            role,
            len(role_members),
            len(role_members),
            len(valid),
            len(positive) / len(valid) if valid else None,
            sum(value >= 2.0 for value in valid) / len(valid) if valid else None,
            sum(value <= -1.0 for value in valid) / len(valid) if valid else None,
            median(valid) if valid else None,
            median(positive) if positive else None,
            None,
            _clamp(contribution, 0.0, 10.0),
        )
    contribution = (
        sum(curve.evaluate(value) * float(item.score_importance) for item, value in valid_pairs)
        / sum(weights)
        if valid_pairs and curve is not None and sum(weights) > 0
        else 0.0
    )
    return RoleEvidenceV0(
        role,
        len(role_members),
        len(role_members),
        len(valid),
        len(positive) / len(valid) if valid else None,
        sum(value >= 2.0 for value in valid) / len(valid) if valid else None,
        sum(value <= -1.0 for value in valid) / len(valid) if valid else None,
        median(valid) if valid else None,
        median(positive) if positive else None,
        weighted_raw,
        _clamp(contribution, 0.0, 30.0 if role == REPRESENTATIVE else 60.0),
    )


def _related_evidence(
    role_members: tuple[MemberObservation, ...],
    values: dict[str, float | None],
    policy: OwnerSeededV0Policy,
    *,
    relative: bool,
) -> RoleEvidenceV0:
    valid = tuple(
        float(values[item.member_id]) for item in role_members if values[item.member_id] is not None
    )
    positive = tuple(value for value in valid if value > 0)
    breadth = len(positive) / len(valid) if valid else None
    positive_median = median(positive) if positive else None
    breadth_table = policy.relative_related_breadth if relative else policy.absolute_related_breadth
    quality_table = policy.relative_related_quality if relative else policy.absolute_related_quality
    contribution = (
        breadth_table.evaluate(breadth) * quality_table.evaluate(positive_median)
        if breadth is not None and positive_median is not None
        else 0.0
    )
    return RoleEvidenceV0(
        RELATED,
        len(role_members),
        len(role_members),
        len(valid),
        breadth,
        sum(value >= 2.0 for value in valid) / len(valid) if valid else None,
        sum(value <= -1.0 for value in valid) / len(valid) if valid else None,
        median(valid) if valid else None,
        positive_median,
        None,
        _clamp(contribution, 0.0, 10.0),
    )


def _grade(
    view: Literal["ABSOLUTE", "RELATIVE"],
    strength: float,
    evidence: dict[str, RoleEvidenceV0],
    policy: OwnerSeededV0Policy,
) -> tuple[str, bool, tuple[str, ...]]:
    core = evidence[CORE]
    rep = evidence[REPRESENTATIVE]
    if view == "ABSOLUTE":
        grade_policy = policy.absolute_grade
        d_guard = bool(
            core.median_return is not None
            and core.positive_breadth is not None
            and core.weak_ratio is not None
            and core.median_return <= grade_policy.d_core_median_max
            and core.positive_breadth <= grade_policy.d_core_positive_breadth_max
            and core.weak_ratio >= grade_policy.d_core_weak_ratio_min
            and (
                (
                    rep.weighted_raw_return is not None
                    and rep.weighted_raw_return <= grade_policy.d_rep_weighted_raw_max
                )
                or core.median_return <= grade_policy.d_core_median_deep_max
            )
        )
    else:
        grade_policy = policy.relative_grade
        d_guard = bool(
            strength <= grade_policy.d_total_max
            and core.median_return is not None
            and core.positive_breadth is not None
            and core.weak_ratio is not None
            and core.median_return <= grade_policy.d_core_median_max
            and core.positive_breadth <= grade_policy.d_core_positive_breadth_max
            and core.weak_ratio >= grade_policy.d_core_weak_ratio_min
            and (
                (
                    rep.weighted_raw_return is not None
                    and rep.weighted_raw_return <= grade_policy.d_rep_weighted_raw_max
                )
                or core.median_return <= grade_policy.d_core_median_deep_max
            )
        )
    if d_guard:
        return "D", True, ("CONFIRMED_BROAD_WEAKNESS",)
    if strength >= grade_policy.exceptional_min:
        return "S", False, ("EXCEPTIONAL_COORDINATED_STRENGTH",)
    if strength >= grade_policy.clear_min:
        return "A", False, ("CLEAR_COORDINATED_STRENGTH",)
    return "B", False, ("NEUTRAL_OR_ORDINARY_STRUCTURE",)


def evaluate_strength_view(
    members: tuple[MemberObservation, ...],
    *,
    view: Literal["ABSOLUTE", "RELATIVE"],
    policy: OwnerSeededV0Policy = DEFAULT_POLICY,
    minimum_formal_member_count: int = 3,
) -> StrengthViewResult:
    """Evaluate one view with exact V0 curves and fail-closed input handling."""

    if not members:
        return _empty_view(view, members, "INSUFFICIENT_DATA", "NO_FORMAL_MEMBERS")
    if minimum_formal_member_count < 0:
        raise OwnerSeededV0Error("minimum_formal_member_count must be non-negative")
    if len(members) < minimum_formal_member_count:
        return _empty_view(view, members, "NOT_EVALUABLE", "MINIMUM_FORMAL_MEMBER_COUNT_NOT_MET")
    ids = tuple(item.member_id for item in members)
    if len(ids) != len(set(ids)):
        raise OwnerSeededV0Error("member observations must be unique")
    for item in members:
        _validate_importance(item, policy)
    values = {item.member_id: item.value_for(view) for item in members}
    if any(value is None for value in values.values()):
        return _empty_view(view, members, "INSUFFICIENT_DATA", "REQUIRED_MEMBER_RETURN_UNAVAILABLE")
    curves = (
        {
            REPRESENTATIVE: policy.absolute_representative,
            CORE: policy.absolute_core,
        }
        if view == "ABSOLUTE"
        else {
            REPRESENTATIVE: policy.relative_representative,
            CORE: policy.relative_core,
        }
    )
    evidence: dict[str, RoleEvidenceV0] = {}
    for role in (REPRESENTATIVE, CORE):
        evidence[role] = _role_evidence(role, members, values, curves[role], policy)
    evidence[RELATED] = _related_evidence(
        tuple(item for item in members if item.role == RELATED),
        values,
        policy,
        relative=view == "RELATIVE",
    )
    strength = _clamp(sum(item.contribution for item in evidence.values()), 0.0, 100.0)
    grade, d_guard, grade_basis = _grade(view, strength, evidence, policy)
    benchmark_by_market = tuple(
        sorted(
            {
                item.market.strip().upper(): benchmark_for_market(item.market)
                for item in members
                if item.market is not None
            }.items()
        )
    )
    return StrengthViewResult(
        view=view,
        status="EVALUATED",
        strength=round(strength, 6),
        grade=grade,
        d_guard=d_guard,
        role_evidence=tuple(evidence[role] for role in ROLE_ORDER),
        grade_basis=grade_basis,
        benchmark_by_market=benchmark_by_market,
    )


def evaluate_topic(
    topic_id: str,
    trading_date: date,
    members: tuple[MemberObservation, ...],
    *,
    policy: OwnerSeededV0Policy = DEFAULT_POLICY,
) -> TopicEvaluationResult:
    """Evaluate Absolute and Relative V0 views for one synthetic/forward day."""

    if not topic_id.strip():
        raise OwnerSeededV0Error("topic_id must be non-empty")
    observed = sum(item.absolute_return_pct is not None for item in members)
    return TopicEvaluationResult(
        topic_id=topic_id,
        trading_date=trading_date,
        formal_member_count=len(members),
        observed_member_count=observed,
        policy_version=POLICY_VERSION,
        absolute=evaluate_strength_view(members, view="ABSOLUTE", policy=policy),
        relative=evaluate_strength_view(members, view="RELATIVE", policy=policy),
    )


@dataclass(frozen=True)
class LifecycleMetrics:
    rep_raw_return: float | None
    core_median_return: float | None
    core_positive_breadth: float | None
    core_strong_breadth: float | None
    core_weak_ratio: float | None
    related_positive_breadth: float | None
    related_positive_median: float | None

    def as_dict(self) -> dict[str, float | None]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class LifecycleDayInput:
    evaluation: TopicEvaluationResult
    members: tuple[MemberObservation, ...]


@dataclass(frozen=True)
class LifecycleHistoryEntry:
    trading_date: date
    metrics: LifecycleMetrics
    fermenting_candidate: bool
    main_rise_candidate: bool
    meaningful_expansion: bool
    mature_candidate: bool
    declining_candidate: bool


@dataclass(frozen=True)
class LifecycleState:
    stage: str = "BASE"
    main_rise_occurred_in_cycle: bool = False
    candidate_stage: str | None = None
    candidate_streak: int = 0
    history: tuple[LifecycleHistoryEntry, ...] = ()


@dataclass(frozen=True)
class LifecycleDayResult:
    trading_date: date
    previous_stage: str
    candidate_stage: str | None
    final_stage: str
    transition_reason: str
    candidate_streak: int
    main_rise_occurred_in_cycle: bool
    meaningful_expansion: bool
    renewed_expansion: bool
    relative_deterioration_confirmation: bool
    early_relative_strength_confirmation: bool
    metrics: LifecycleMetrics

    def as_dict(self) -> dict[str, object]:
        return {
            "tradingDate": self.trading_date.isoformat(),
            "previousLifecycle": self.previous_stage,
            "candidateLifecycle": self.candidate_stage,
            "finalLifecycle": self.final_stage,
            "transitionReason": self.transition_reason,
            "candidateStreak": self.candidate_streak,
            "mainRiseOccurredInCycle": self.main_rise_occurred_in_cycle,
            "meaningfulExpansion": self.meaningful_expansion,
            "renewedExpansion": self.renewed_expansion,
            "relativeDeteriorationConfirmation": self.relative_deterioration_confirmation,
            "earlyRelativeStrengthConfirmation": self.early_relative_strength_confirmation,
            "metrics": self.metrics.as_dict(),
        }


@dataclass(frozen=True)
class ForwardObservationOutput:
    """Deterministic review shape for a future forward-observation day."""

    trading_date: date
    topic: str
    policy_version: str
    formal_member_count: int
    observed_member_count: int
    rep_evidence: dict[str, object]
    core_evidence: dict[str, object]
    related_evidence: dict[str, object]
    absolute_strength: float | None
    absolute_grade: str | None
    absolute_d_guard: bool
    relative_strength: float | None
    relative_grade: str | None
    relative_d_guard: bool
    previous_lifecycle: str
    candidate_lifecycle: str | None
    final_lifecycle: str
    transition_reason: str
    coverage: dict[str, object]
    authority_state: dict[str, object]
    pm_expected_absolute_grade: str | None = None
    pm_expected_relative_grade: str | None = None
    pm_expected_lifecycle: str | None = None
    pm_result: str | None = None
    pm_note: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "trading_date": self.trading_date.isoformat(),
            "topic": self.topic,
            "policy_version": self.policy_version,
            "formal_member_count": self.formal_member_count,
            "observed_member_count": self.observed_member_count,
            "rep_evidence": self.rep_evidence,
            "core_evidence": self.core_evidence,
            "related_evidence": self.related_evidence,
            "absolute_strength": self.absolute_strength,
            "absolute_grade": self.absolute_grade,
            "absolute_d_guard": self.absolute_d_guard,
            "relative_strength": self.relative_strength,
            "relative_grade": self.relative_grade,
            "relative_d_guard": self.relative_d_guard,
            "previous_lifecycle": self.previous_lifecycle,
            "candidate_lifecycle": self.candidate_lifecycle,
            "final_lifecycle": self.final_lifecycle,
            "transition_reason": self.transition_reason,
            "coverage": self.coverage,
            "authority_state": self.authority_state,
            "PM_EXPECTED_ABSOLUTE_GRADE": self.pm_expected_absolute_grade,
            "PM_EXPECTED_RELATIVE_GRADE": self.pm_expected_relative_grade,
            "PM_EXPECTED_LIFECYCLE": self.pm_expected_lifecycle,
            "PM_RESULT": self.pm_result,
            "PM_NOTE": self.pm_note,
        }


def _role_values(members: tuple[MemberObservation, ...], role: str) -> tuple[float, ...]:
    return tuple(
        float(item.absolute_return_pct)
        for item in members
        if item.role == role and item.absolute_return_pct is not None
    )


def _lifecycle_metrics(members: tuple[MemberObservation, ...]) -> LifecycleMetrics:
    rep = _role_values(members, REPRESENTATIVE)
    core = _role_values(members, CORE)
    related = _role_values(members, RELATED)
    related_positive = tuple(value for value in related if value > 0)
    return LifecycleMetrics(
        rep_raw_return=(sum(rep) / len(rep)) if rep else None,
        core_median_return=median(core) if core else None,
        core_positive_breadth=(sum(value > 0 for value in core) / len(core)) if core else None,
        core_strong_breadth=(sum(value >= 2.0 for value in core) / len(core)) if core else None,
        core_weak_ratio=(sum(value <= -1.0 for value in core) / len(core)) if core else None,
        related_positive_breadth=(len(related_positive) / len(related)) if related else None,
        related_positive_median=median(related_positive) if related_positive else None,
    )


def _has_expansion(
    metrics: LifecycleMetrics,
    history: tuple[LifecycleHistoryEntry, ...],
    policy: LifecyclePolicy,
) -> bool:
    prior = history[-policy.expansion_lookback_sessions :]
    if prior and metrics.core_positive_breadth is not None:
        prior_core = [
            item.metrics.core_positive_breadth
            for item in prior
            if item.metrics.core_positive_breadth is not None
        ]
        if (
            prior_core
            and metrics.core_positive_breadth
            >= max(prior_core) + policy.expansion_core_breadth_delta
            and (metrics.core_median_return or 0.0) >= policy.expansion_core_median_min
        ):
            return True
    if prior and metrics.related_positive_breadth is not None:
        prior_related = [
            item.metrics.related_positive_breadth
            for item in prior
            if item.metrics.related_positive_breadth is not None
        ]
        if (
            prior_related
            and metrics.related_positive_breadth
            >= max(prior_related) + policy.expansion_related_breadth_delta
            and (metrics.core_positive_breadth or 0.0) >= policy.expansion_related_core_breadth_min
            and (metrics.related_positive_median or 0.0) >= policy.expansion_related_median_min
        ):
            return True
    return False


def _count_recent(
    history: tuple[LifecycleHistoryEntry, ...],
    predicate: str,
    window: int,
) -> int:
    return sum(bool(getattr(item, predicate)) for item in history[-window:])


def _mature_no_expansion_streak(history: tuple[LifecycleHistoryEntry, ...], required: int) -> int:
    streak = 0
    for item in reversed(history):
        if item.meaningful_expansion:
            break
        streak += 1
        if streak >= required:
            break
    return streak


def _allowed_transition(previous: str, candidate: str) -> bool:
    if previous == candidate:
        return True
    allowed = {
        "BASE": {"SPROUTING", "FERMENTING"},
        "SPROUTING": {"FERMENTING"},
        "FERMENTING": {"MAIN_RISE"},
        "MAIN_RISE": {"MATURE", "DECLINING"},
        "MATURE": {"DECLINING"},
        "DECLINING": {"BASE"},
    }
    return candidate in allowed.get(previous, set())


def advance_lifecycle(
    state: LifecycleState,
    day: LifecycleDayInput,
    *,
    policy: OwnerSeededV0Policy = DEFAULT_POLICY,
) -> tuple[LifecycleState, LifecycleDayResult]:
    """Advance the V0 lifecycle state with explicit confirmation/hysteresis."""

    if state.stage not in LIFECYCLE_STAGES:
        raise OwnerSeededV0Error("unknown lifecycle state")
    metrics = _lifecycle_metrics(day.members)
    lifecycle = policy.lifecycle
    if len(day.members) < 3 or any(item.absolute_return_pct is None for item in day.members):
        result = LifecycleDayResult(
            day.evaluation.trading_date,
            state.stage,
            None,
            state.stage,
            "INSUFFICIENT_FORMAL_MEMBER_EVIDENCE",
            0,
            state.main_rise_occurred_in_cycle,
            False,
            False,
            False,
            False,
            metrics,
        )
        return state, result

    rep = metrics.rep_raw_return
    core_median = metrics.core_median_return
    core_positive = metrics.core_positive_breadth
    core_strong = metrics.core_strong_breadth
    core_weak = metrics.core_weak_ratio
    related_positive = metrics.related_positive_breadth
    related_median = metrics.related_positive_median
    fermenting_candidate = bool(
        core_positive is not None
        and core_median is not None
        and core_strong is not None
        and rep is not None
        and core_positive >= lifecycle.fermenting_core_positive_breadth_min
        and core_median >= lifecycle.fermenting_core_median_min
        and core_strong >= lifecycle.fermenting_core_strong_breadth_min
        and rep > lifecycle.fermenting_rep_raw_min
    )
    main_rise_candidate = bool(
        core_positive is not None
        and core_median is not None
        and core_strong is not None
        and related_positive is not None
        and related_median is not None
        and rep is not None
        and core_positive >= lifecycle.main_rise_core_positive_breadth_min
        and core_median >= lifecycle.main_rise_core_median_min
        and core_strong >= lifecycle.main_rise_core_strong_breadth_min
        and related_positive >= lifecycle.main_rise_related_positive_breadth_min
        and related_median >= lifecycle.main_rise_related_positive_median_min
        and rep > lifecycle.main_rise_rep_raw_min
    )
    sprouting_candidate = bool(
        rep is not None
        and core_positive is not None
        and core_median is not None
        and rep >= lifecycle.sprouting_rep_raw_min
        and core_positive < lifecycle.sprouting_core_positive_breadth_max
        and lifecycle.sprouting_core_median_min < core_median < lifecycle.sprouting_core_median_max
    )
    declining_candidate = bool(
        core_median is not None
        and core_positive is not None
        and core_weak is not None
        and core_median <= lifecycle.declining_core_median_max
        and core_positive <= lifecycle.declining_core_positive_breadth_max
        and core_weak >= lifecycle.declining_core_weak_ratio_min
        and (
            (rep is not None and rep <= lifecycle.declining_rep_raw_max)
            or core_median <= lifecycle.declining_core_median_deep_max
            or day.evaluation.absolute.d_guard
        )
    )
    meaningful_expansion = _has_expansion(metrics, state.history, lifecycle)
    prior_history = state.history
    current_entry = LifecycleHistoryEntry(
        day.evaluation.trading_date,
        metrics,
        fermenting_candidate,
        main_rise_candidate,
        meaningful_expansion,
        False,
        declining_candidate,
    )
    history_with_current = (*prior_history, current_entry)
    mature_condition = bool(
        state.main_rise_occurred_in_cycle
        and _mature_no_expansion_streak(
            history_with_current, lifecycle.mature_no_expansion_sessions
        )
        >= lifecycle.mature_no_expansion_sessions
        and (
            (
                core_positive is not None
                and state.history
                and max(item.metrics.core_positive_breadth or 0.0 for item in state.history)
                - core_positive
                >= lifecycle.mature_core_breadth_drawdown
            )
            or (
                core_median is not None
                and state.history
                and core_median
                <= max(item.metrics.core_median_return or core_median for item in state.history)
                - lifecycle.mature_core_median_drawdown
            )
            or (
                rep is not None
                and sum(
                    (item.metrics.rep_raw_return or 0.0) <= 0.0
                    for item in history_with_current[-lifecycle.mature_rep_nonpositive_window :]
                )
                >= lifecycle.mature_rep_nonpositive_required
            )
            or (
                related_positive is not None
                and core_positive is not None
                and related_positive >= lifecycle.mature_late_related_breadth_min
                and core_positive < lifecycle.mature_late_core_breadth_max
            )
        )
    )
    current_entry = LifecycleHistoryEntry(
        day.evaluation.trading_date,
        metrics,
        fermenting_candidate,
        main_rise_candidate,
        meaningful_expansion,
        mature_condition,
        declining_candidate,
    )
    history_with_current = (*prior_history, current_entry)
    reset_candidate = bool(
        state.stage == "DECLINING"
        and day.evaluation.absolute.grade == lifecycle.reset_grade
        and core_median is not None
        and core_positive is not None
        and core_weak is not None
        and lifecycle.reset_core_median_min < core_median < lifecycle.reset_core_median_max
        and core_weak < lifecycle.reset_core_weak_ratio_max
        and lifecycle.reset_core_positive_breadth_min
        <= core_positive
        <= lifecycle.reset_core_positive_breadth_max
        and not main_rise_candidate
        and not fermenting_candidate
    )

    if state.stage == "DECLINING" and reset_candidate:
        candidate = "BASE"
    elif declining_candidate:
        candidate = "DECLINING"
    elif state.stage != "MATURE" and main_rise_candidate:
        candidate = "MAIN_RISE"
    elif mature_condition:
        candidate = "MATURE"
    elif fermenting_candidate:
        candidate = "FERMENTING"
    elif sprouting_candidate:
        candidate = "SPROUTING"
    else:
        candidate = None

    if candidate == state.candidate_stage:
        candidate_streak = state.candidate_streak + 1
    elif candidate is None:
        candidate_streak = 0
    else:
        candidate_streak = 1
    if candidate in {"FERMENTING", "MAIN_RISE"}:
        window = (
            lifecycle.fermenting_window_sessions
            if candidate == "FERMENTING"
            else lifecycle.main_rise_window_sessions
        )
        required = (
            lifecycle.fermenting_required_sessions
            if candidate == "FERMENTING"
            else lifecycle.main_rise_required_sessions
        )
        candidate_field = (
            "fermenting_candidate" if candidate == "FERMENTING" else "main_rise_candidate"
        )
        qualifying = _count_recent(history_with_current, candidate_field, window)
        confirmed = qualifying >= required
    elif candidate == "SPROUTING":
        confirmed = candidate_streak >= lifecycle.sprouting_confirmation_sessions
    elif candidate == "MATURE":
        qualifying = _count_recent(
            history_with_current,
            "mature_candidate",
            lifecycle.mature_confirmation_sessions,
        )
        confirmed = qualifying >= lifecycle.mature_confirmation_sessions
    elif candidate == "DECLINING":
        confirmed = candidate_streak >= lifecycle.declining_confirmation_sessions
    elif candidate == "BASE":
        confirmed = candidate_streak >= lifecycle.reset_confirmation_sessions
    else:
        confirmed = False

    final_stage = state.stage
    reason = "NO_STAGE_CANDIDATE"
    if candidate is None:
        candidate_streak = 0
    elif candidate == state.stage:
        reason = "CURRENT_STAGE_EVIDENCE_PERSISTS"
        candidate_streak = 0
    elif not _allowed_transition(state.stage, candidate):
        reason = "ILLEGAL_BACKWARD_OR_SKIPPED_TRANSITION_HELD"
    elif not confirmed:
        reason = "CONFIRMATION_PENDING"
    else:
        final_stage = candidate
        reason = "CONFIRMED_OWNER_SEEDED_V0_TRANSITION"

    main_rise_occurred = state.main_rise_occurred_in_cycle or final_stage in {
        "MAIN_RISE",
        "MATURE",
        "DECLINING",
    }
    if state.stage == "DECLINING" and final_stage == "BASE":
        main_rise_occurred = False
    reset_cycle = state.stage == "DECLINING" and final_stage == "BASE"
    renewed_expansion = state.stage == "MATURE" and meaningful_expansion
    relative_deterioration = bool(
        (
            day.evaluation.relative.strength is not None
            and day.evaluation.relative.strength < lifecycle.relative_deterioration_strength_max
        )
        or day.evaluation.relative.grade == "D"
    )
    early_relative = bool(
        day.evaluation.absolute.grade == "B" and day.evaluation.relative.grade in {"A", "S"}
    )
    new_state = LifecycleState(
        stage=final_stage,
        main_rise_occurred_in_cycle=main_rise_occurred,
        candidate_stage=candidate if final_stage == state.stage else None,
        candidate_streak=candidate_streak if final_stage == state.stage else 0,
        history=(
            ()
            if reset_cycle
            else history_with_current[-max(lifecycle.expansion_lookback_sessions, 10) :]
        ),
    )
    result = LifecycleDayResult(
        trading_date=day.evaluation.trading_date,
        previous_stage=state.stage,
        candidate_stage=candidate,
        final_stage=final_stage,
        transition_reason=reason,
        candidate_streak=candidate_streak,
        main_rise_occurred_in_cycle=main_rise_occurred,
        meaningful_expansion=meaningful_expansion,
        renewed_expansion=renewed_expansion,
        relative_deterioration_confirmation=relative_deterioration,
        early_relative_strength_confirmation=early_relative,
        metrics=metrics,
    )
    return new_state, result


def policy_document(policy: OwnerSeededV0Policy = DEFAULT_POLICY) -> dict[str, object]:
    """Return the reproducible machine-readable policy document."""

    return {
        "schemaVersion": POLICY_SCHEMA_VERSION,
        "policyHash": policy.policy_hash(),
        "policy": policy.as_dict(),
    }


def build_forward_observation_output(
    topic: str,
    evaluation: TopicEvaluationResult,
    lifecycle: LifecycleDayResult,
    *,
    policy: OwnerSeededV0Policy = DEFAULT_POLICY,
) -> ForwardObservationOutput:
    """Build the non-activating Owner/PM review record for one forward day."""

    if not topic.strip():
        raise OwnerSeededV0Error("topic must be non-empty")
    absolute_by_role = {item.role: item.as_dict() for item in evaluation.absolute.role_evidence}
    relative_by_role = {item.role: item.as_dict() for item in evaluation.relative.role_evidence}

    def role_review(role: str) -> dict[str, object]:
        return {
            "absolute": absolute_by_role[role],
            "relative": relative_by_role[role],
        }

    return ForwardObservationOutput(
        trading_date=evaluation.trading_date,
        topic=topic,
        policy_version=evaluation.policy_version,
        formal_member_count=evaluation.formal_member_count,
        observed_member_count=evaluation.observed_member_count,
        rep_evidence=role_review(REPRESENTATIVE),
        core_evidence=role_review(CORE),
        related_evidence=role_review(RELATED),
        absolute_strength=evaluation.absolute.strength,
        absolute_grade=evaluation.absolute.grade,
        absolute_d_guard=evaluation.absolute.d_guard,
        relative_strength=evaluation.relative.strength,
        relative_grade=evaluation.relative.grade,
        relative_d_guard=evaluation.relative.d_guard,
        previous_lifecycle=lifecycle.previous_stage,
        candidate_lifecycle=lifecycle.candidate_stage,
        final_lifecycle=lifecycle.final_stage,
        transition_reason=lifecycle.transition_reason,
        coverage={
            "formal_member_count": evaluation.formal_member_count,
            "observed_member_count": evaluation.observed_member_count,
            "policy": policy.as_dict()["coverage"],
        },
        authority_state={
            "operating_mode": "OWNER_SEEDED_V0",
            "historical_calibration": HISTORICAL_CALIBRATION,
            "absolute": "PRIMARY",
            "relative": "CONFIRMATION_ONLY",
            "production_active": PRODUCTION_ACTIVE,
        },
    )


__all__ = [
    "ABSOLUTE_GRADE_POLICY",
    "CALIBRATION_METHOD",
    "DEFAULT_POLICY",
    "HISTORICAL_CALIBRATION",
    "LIFECYCLE_STAGES",
    "POLICY_ID",
    "POLICY_SCHEMA_VERSION",
    "POLICY_VERSION",
    "PRODUCTION_ACTIVE",
    "ForwardObservationOutput",
    "LifecycleDayInput",
    "LifecycleDayResult",
    "LifecycleMetrics",
    "LifecycleState",
    "MemberObservation",
    "OwnerSeededV0Error",
    "OwnerSeededV0Policy",
    "PiecewiseLinearCurve",
    "RoleEvidenceV0",
    "ScoreImportancePolicy",
    "StrengthViewResult",
    "TopicEvaluationResult",
    "advance_lifecycle",
    "build_forward_observation_output",
    "evaluate_strength_view",
    "evaluate_topic",
    "policy_document",
]


ABSOLUTE_GRADE_POLICY = DEFAULT_POLICY.absolute_grade
