"""Role-based Topic Strength contract for the Design Freeze boundary.

This module is deliberately non-activating.  It defines the frozen topology
and validates explicit response curves, but it does not ship guessed knots or
Grade thresholds.  A caller that has no calibrated curve receives a bounded
``CALIBRATION_REQUIRED`` result instead of an inferred production score.

The legacy Production V1 Breadth/Leadership evaluator remains available under
its historical policy version.  It is not an implementation of this contract.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Final, Literal

from ..structural_role_contract import (
    validate_structural_role,
)

TOPIC_STRENGTH_CONTRACT_VERSION: Final = "topic-strength-role-based.v2"
TOPIC_STRENGTH_CALCULATION_VERSION: Final = "topic-strength-role-based.v2.boundary"

ABSOLUTE: Final = "ABSOLUTE"
RELATIVE: Final = "RELATIVE"
STRENGTH_VIEWS: Final = (ABSOLUTE, RELATIVE)

REPRESENTATIVE: Final = "REPRESENTATIVE"
CORE: Final = "CORE"
RELATED: Final = "RELATED"
ROLE_CAPS: Final = {
    REPRESENTATIVE: 30.0,
    CORE: 60.0,
    RELATED: 10.0,
}
ROLE_CAP_TOTAL: Final = 100.0

REPRESENTATIVE_SCORE_IMPORTANCE: Final = frozenset({1.25, 1.50, 1.75})
CORE_SCORE_IMPORTANCE: Final = frozenset({0.50, 0.75, 1.00})
ROLE_SCORE_IMPORTANCE: Final = {
    REPRESENTATIVE: REPRESENTATIVE_SCORE_IMPORTANCE,
    CORE: CORE_SCORE_IMPORTANCE,
    RELATED: frozenset(),
}

CALIBRATION_REQUIRED: Final = "CALIBRATION_REQUIRED"
PROVISIONAL: Final = "PROVISIONAL"
NOT_FORMAL: Final = "NOT_FORMAL"
FORMAL: Final = "FORMAL"
POLICY_STATUSES: Final = (CALIBRATION_REQUIRED, PROVISIONAL, NOT_FORMAL, FORMAL)

GRADE_S: Final = "S"
GRADE_A: Final = "A"
GRADE_B: Final = "B"
GRADE_D: Final = "D"
GRADES: Final = (GRADE_S, GRADE_A, GRADE_B, GRADE_D)

MARKET_BENCHMARKS: Final = {
    "TWSE": "TAIEX",
    "TPEX": "TPEX_INDEX",
}


class TopicStrengthError(ValueError):
    """Raised when a role-strength input violates the frozen contract."""


def benchmark_for_market(market: str) -> str:
    """Return the member's own market benchmark identity."""

    key = str(market).strip().upper()
    try:
        return MARKET_BENCHMARKS[key]
    except KeyError as exc:
        raise TopicStrengthError(f"RELATIVE_BENCHMARK_UNSUPPORTED:{market}") from exc


@dataclass(frozen=True)
class RoleMemberObservation:
    """One point-in-time member observation owned by the backend."""

    member_id: str
    role: str
    return_pct: float | None
    market: str | None = None
    benchmark_return_pct: float | None = None
    score_importance: float | None = None

    def __post_init__(self) -> None:
        if not self.member_id.strip() or self.member_id != self.member_id.strip():
            raise TopicStrengthError("member_id must be a trimmed non-empty string")
        try:
            validate_structural_role(self.role, allow_null=False)
        except ValueError as exc:
            raise TopicStrengthError("invalid structural role") from exc
        for name in ("return_pct", "benchmark_return_pct", "score_importance"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
            ):
                raise TopicStrengthError(f"{name} must be finite or null")
        if self.market is not None and not self.market.strip():
            raise TopicStrengthError("market must be non-empty when supplied")

    def value_for(self, view: str) -> float | None:
        if view == ABSOLUTE:
            return None if self.return_pct is None else float(self.return_pct)
        if view != RELATIVE:
            raise TopicStrengthError("view must be ABSOLUTE or RELATIVE")
        if self.return_pct is None or self.benchmark_return_pct is None:
            return None
        benchmark_for_market(self.market or "")
        return float(self.return_pct) - float(self.benchmark_return_pct)


@dataclass(frozen=True)
class ResponseCurve:
    """Explicit monotonic response curve; no default knots are supplied."""

    version: str
    knots: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise TopicStrengthError("curve version must be non-empty")
        if len(self.knots) < 2:
            raise TopicStrengthError("response curve requires at least two knots")
        previous_x: float | None = None
        previous_y: float | None = None
        for x, y in self.knots:
            if not math.isfinite(float(x)) or not math.isfinite(float(y)):
                raise TopicStrengthError("response curve knots must be finite")
            if not 0.0 <= float(y) <= 1.0:
                raise TopicStrengthError("response curve output must be in [0,1]")
            if previous_x is not None and float(x) <= previous_x:
                raise TopicStrengthError("response curve x knots must be strictly increasing")
            if previous_y is not None and float(y) < previous_y:
                raise TopicStrengthError("response curve must be monotonic")
            previous_x, previous_y = float(x), float(y)

    def evaluate(self, value: float) -> float:
        value = float(value)
        if not math.isfinite(value):
            raise TopicStrengthError("curve input must be finite")
        if value <= self.knots[0][0]:
            return float(self.knots[0][1])
        if value >= self.knots[-1][0]:
            return float(self.knots[-1][1])
        for (left_x, left_y), (right_x, right_y) in zip(
            self.knots, self.knots[1:], strict=True
        ):
            if value <= right_x:
                ratio = (value - left_x) / (right_x - left_x)
                return float(left_y + ratio * (right_y - left_y))
        return float(self.knots[-1][1])


@dataclass(frozen=True)
class RoleResponseCurves:
    representative: ResponseCurve
    core: ResponseCurve
    related: ResponseCurve

    def for_role(self, role: str) -> ResponseCurve:
        try:
            return {
                REPRESENTATIVE: self.representative,
                CORE: self.core,
                RELATED: self.related,
            }[role]
        except KeyError as exc:
            raise TopicStrengthError(f"unsupported role: {role}") from exc


@dataclass(frozen=True)
class GradePolicy:
    """Explicit calibration fixture for Grade semantics.

    The fields are intentionally mandatory.  The design freeze fixes the
    meaning of S/A/B/D, not these numeric boundaries.
    """

    version: str
    exceptional_min_strength: float
    clear_strength_min: float
    negative_breadth_min: float
    negative_average_max: float

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise TopicStrengthError("grade policy version must be non-empty")
        if not (
            0.0 <= self.clear_strength_min <= self.exceptional_min_strength <= 100.0
        ):
            raise TopicStrengthError("Grade strength boundaries are invalid")
        if not 0.0 <= self.negative_breadth_min <= 1.0:
            raise TopicStrengthError("negative breadth boundary must be in [0,1]")
        for value in (self.negative_average_max,):
            if not math.isfinite(float(value)):
                raise TopicStrengthError("Grade average boundary must be finite")


@dataclass(frozen=True)
class TopicStrengthPolicy:
    """Versioned role-strength policy; curves remain explicit dependencies."""

    policy_version: str = TOPIC_STRENGTH_CONTRACT_VERSION
    calculation_version: str = TOPIC_STRENGTH_CALCULATION_VERSION
    status: str = CALIBRATION_REQUIRED
    absolute_curves: RoleResponseCurves | None = None
    relative_curves: RoleResponseCurves | None = None
    grade_policy: GradePolicy | None = None
    calibration_approved: bool = False

    def __post_init__(self) -> None:
        if not self.policy_version.strip() or not self.calculation_version.strip():
            raise TopicStrengthError("policy and calculation versions are required")
        if self.status not in POLICY_STATUSES:
            raise TopicStrengthError("unsupported Topic Strength policy status")
        if self.status == FORMAL and not self.calibration_approved:
            raise TopicStrengthError("FORMAL Topic Strength requires calibration approval")

    def curves_for(self, view: str) -> RoleResponseCurves | None:
        if view == ABSOLUTE:
            return self.absolute_curves
        if view == RELATIVE:
            return self.relative_curves
        raise TopicStrengthError("view must be ABSOLUTE or RELATIVE")


@dataclass(frozen=True)
class RoleEvidence:
    role: str
    observed_count: int
    valid_count: int
    positive_breadth: float | None
    strong_breadth: float | None
    average_return: float | None
    contribution: float | None
    cap: float
    score_importance: tuple[float, ...]


@dataclass(frozen=True)
class TopicStrengthResult:
    topic_id: str
    as_of: date
    view: Literal["ABSOLUTE", "RELATIVE"]
    status: str
    strength: float | None
    grade: str | None
    grade_status: str
    policy_version: str
    calculation_version: str
    curve_version: str | None
    role_evidence: tuple[RoleEvidence, ...]
    coverage: float | None
    benchmark_by_market: tuple[tuple[str, str], ...]
    grade_basis: tuple[str, ...]

    @property
    def absolute_strength(self) -> float | None:
        return self.strength if self.view == ABSOLUTE else None

    @property
    def relative_strength(self) -> float | None:
        return self.strength if self.view == RELATIVE else None

    @property
    def absolute_grade(self) -> str | None:
        return self.grade if self.view == ABSOLUTE else None

    @property
    def relative_grade(self) -> str | None:
        return self.grade if self.view == RELATIVE else None

    def as_dict(self) -> dict[str, object]:
        return {
            "contractVersion": TOPIC_STRENGTH_CONTRACT_VERSION,
            "topicId": self.topic_id,
            "asOf": self.as_of.isoformat(),
            "status": self.status,
            "absoluteStrength": self.absolute_strength,
            "absoluteGrade": self.absolute_grade,
            "relativeStrength": self.relative_strength,
            "relativeGrade": self.relative_grade,
            "gradeStatus": self.grade_status,
            "policyVersion": self.policy_version,
            "calculationVersion": self.calculation_version,
            "curveVersion": self.curve_version,
            "coverage": self.coverage,
            "benchmarkByMarket": dict(self.benchmark_by_market),
            "gradeBasis": list(self.grade_basis),
            "roleEvidence": [
                {
                    "role": item.role,
                    "observedCount": item.observed_count,
                    "validCount": item.valid_count,
                    "positiveBreadth": item.positive_breadth,
                    "strongBreadth": item.strong_breadth,
                    "averageReturn": item.average_return,
                    "contribution": item.contribution,
                    "cap": item.cap,
                    "scoreImportance": list(item.score_importance),
                }
                for item in self.role_evidence
            ],
        }


def _empty_result(
    topic_id: str,
    as_of: date,
    view: str,
    policy: TopicStrengthPolicy,
    observations: tuple[RoleMemberObservation, ...],
    *,
    status: str,
    grade_status: str = CALIBRATION_REQUIRED,
    reason: str = "CALIBRATION_REQUIRED",
) -> TopicStrengthResult:
    return TopicStrengthResult(
        topic_id=topic_id,
        as_of=as_of,
        view=view,  # type: ignore[arg-type]
        status=status,
        strength=None,
        grade=None,
        grade_status=grade_status,
        policy_version=policy.policy_version,
        calculation_version=policy.calculation_version,
        curve_version=None,
        role_evidence=tuple(
            RoleEvidence(role, 0, 0, None, None, None, None, ROLE_CAPS[role], ())
            for role in (REPRESENTATIVE, CORE, RELATED)
        ),
        coverage=None,
        benchmark_by_market=(),
        grade_basis=(reason,),
    )


def _grade(
    strength: float,
    values: tuple[float, ...],
    policy: GradePolicy | None,
) -> tuple[str | None, str, tuple[str, ...]]:
    if policy is None:
        return None, CALIBRATION_REQUIRED, ("GRADE_CALIBRATION_REQUIRED",)
    negative_breadth = sum(value < 0 for value in values) / len(values) if values else 0.0
    average = sum(values) / len(values) if values else 0.0
    if negative_breadth >= policy.negative_breadth_min and average <= policy.negative_average_max:
        return GRADE_D, "PROVISIONAL", ("CONFIRMED_NEGATIVE_EVIDENCE",)
    if strength >= policy.exceptional_min_strength:
        return GRADE_S, "PROVISIONAL", ("EXCEPTIONAL_COORDINATED_STRENGTH",)
    if strength >= policy.clear_strength_min:
        return GRADE_A, "PROVISIONAL", ("CLEAR_COORDINATED_STRENGTH",)
    return GRADE_B, "PROVISIONAL", ("NEUTRAL_OR_ORDINARY_STRUCTURE",)


def evaluate_topic_strength(
    topic_id: str,
    as_of: date,
    observations: tuple[RoleMemberObservation, ...],
    *,
    view: str,
    policy: TopicStrengthPolicy,
) -> TopicStrengthResult:
    """Evaluate one explicit role snapshot without selecting or persisting authority."""

    if not topic_id.strip():
        raise TopicStrengthError("topic_id must be non-empty")
    if view not in STRENGTH_VIEWS:
        raise TopicStrengthError("view must be ABSOLUTE or RELATIVE")
    if not observations:
        return _empty_result(
            topic_id, as_of, view, policy, observations, status="INSUFFICIENT_DATA"
        )
    ids = tuple(item.member_id for item in observations)
    if len(ids) != len(set(ids)):
        raise TopicStrengthError("member observations must be unique")
    for item in observations:
        allowed = ROLE_SCORE_IMPORTANCE[item.role]
        if item.role == RELATED:
            if item.score_importance is not None:
                raise TopicStrengthError("RELATED must not carry Score Importance")
        elif item.score_importance is None:
            raise TopicStrengthError("SCORE_IMPORTANCE_REQUIRED")
        elif round(float(item.score_importance), 2) not in allowed:
            raise TopicStrengthError(f"SCORE_IMPORTANCE_INVALID_FOR_ROLE:{item.role}")
        if view == RELATIVE and item.return_pct is not None:
            benchmark_for_market(item.market or "")

    curves = policy.curves_for(view)
    if curves is None:
        return _empty_result(
            topic_id,
            as_of,
            view,
            policy,
            observations,
            status=CALIBRATION_REQUIRED,
        )

    values_by_role: dict[str, list[tuple[float, float | None]]] = {
        REPRESENTATIVE: [],
        CORE: [],
        RELATED: [],
    }
    benchmark_by_market: dict[str, str] = {}
    all_values: list[float] = []
    for item in observations:
        value = item.value_for(view)
        if item.market is not None and view == RELATIVE:
            benchmark_by_market[item.market.strip().upper()] = benchmark_for_market(item.market)
        values_by_role[item.role].append((value, item.score_importance))
        if value is not None:
            all_values.append(value)

    role_evidence: list[RoleEvidence] = []
    role_scores: dict[str, float] = {}
    for role in (REPRESENTATIVE, CORE, RELATED):
        rows = values_by_role[role]
        valid = [(value, importance) for value, importance in rows if value is not None]
        values = tuple(float(value) for value, _ in valid)
        curve = curves.for_role(role)
        if role == RELATED:
            positive = tuple(value for value in values if value > 0)
            quality = (
                sum(max(0.0, curve.evaluate(value)) for value in positive) / len(values)
                if values
                else 0.0
            )
            contribution = (
                ROLE_CAPS[role] * (len(positive) / len(values)) * quality if values else 0.0
            )
            importance_values: tuple[float, ...] = ()
        else:
            weights = tuple(float(importance) for _, importance in valid if importance is not None)
            denominator = sum(weights)
            contribution = (
                ROLE_CAPS[role]
                * sum(
                    curve.evaluate(value) * weight
                    for value, weight in zip(values, weights, strict=True)
                )
                / denominator
                if values and denominator
                else 0.0
            )
            importance_values = tuple(weights)
        role_scores[role] = max(0.0, min(ROLE_CAPS[role], contribution))
        role_evidence.append(
            RoleEvidence(
                role=role,
                observed_count=len(rows),
                valid_count=len(values),
                positive_breadth=(sum(value > 0 for value in values) / len(values))
                if values
                else None,
                strong_breadth=(sum(value >= 2.0 for value in values) / len(values))
                if values
                else None,
                average_return=sum(values) / len(values) if values else None,
                contribution=role_scores[role],
                cap=ROLE_CAPS[role],
                score_importance=importance_values,
            )
        )

    strength = max(0.0, min(ROLE_CAP_TOTAL, sum(role_scores.values())))
    grade, grade_status, grade_basis = _grade(strength, tuple(all_values), policy.grade_policy)
    return TopicStrengthResult(
        topic_id=topic_id,
        as_of=as_of,
        view=view,  # type: ignore[arg-type]
        status=policy.status,
        strength=round(strength, 6),
        grade=grade,
        grade_status=grade_status,
        policy_version=policy.policy_version,
        calculation_version=policy.calculation_version,
        curve_version="|".join(
            curve.version
            for curve in (
                curves.representative,
                curves.core,
                curves.related,
            )
        ),
        role_evidence=tuple(role_evidence),
        coverage=len(all_values) / len(observations),
        benchmark_by_market=tuple(sorted(benchmark_by_market.items())),
        grade_basis=grade_basis,
    )


__all__ = [
    "ABSOLUTE",
    "CALIBRATION_REQUIRED",
    "CORE",
    "CORE_SCORE_IMPORTANCE",
    "FORMAL",
    "GRADE_A",
    "GRADE_B",
    "GRADE_D",
    "GRADE_S",
    "MARKET_BENCHMARKS",
    "NOT_FORMAL",
    "PROVISIONAL",
    "RELATED",
    "RELATIVE",
    "REPRESENTATIVE",
    "REPRESENTATIVE_SCORE_IMPORTANCE",
    "ROLE_CAPS",
    "ROLE_SCORE_IMPORTANCE",
    "TOPIC_STRENGTH_CALCULATION_VERSION",
    "TOPIC_STRENGTH_CONTRACT_VERSION",
    "GradePolicy",
    "ResponseCurve",
    "RoleEvidence",
    "RoleMemberObservation",
    "RoleResponseCurves",
    "TopicStrengthError",
    "TopicStrengthPolicy",
    "TopicStrengthResult",
    "benchmark_for_market",
    "evaluate_topic_strength",
]
