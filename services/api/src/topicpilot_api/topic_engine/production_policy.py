"""Non-activating implementation of the approved Production V1 score policy.

The mechanics in this module are copied from the canonical 003F PM Formula
Approval Brief.  The module is intentionally provider-neutral: callers must
provide an explicit policy bundle, governed Leader Set, and as-of evidence
binding.  There is no module-level production default and no live-data access.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import date
from itertools import pairwise
from typing import Final

from .aggregation import AggregateStatus, FeatureAggregate, QualitySummary
from .features.contracts import FeatureResult, FeatureStatus
from .policy_approval import PolicyApprovalRecord, require_policy_approval
from .scoring_contracts import TopicScore

PRODUCTION_V1_MECHANICS = "production-v1"
POLICY_DRAFT = "DRAFT"
POLICY_CANDIDATE = "CANDIDATE"
POLICY_APPROVED = "APPROVED"
POLICY_DEPRECATED = "DEPRECATED"
POLICY_LIFECYCLE: Final = frozenset(
    {POLICY_DRAFT, POLICY_CANDIDATE, POLICY_APPROVED, POLICY_DEPRECATED}
)

STRONG_POSITIVE = "STRONG_POSITIVE"
POSITIVE = "POSITIVE"
NEUTRAL = "NEUTRAL"
NEGATIVE = "NEGATIVE"
STRONG_NEGATIVE = "STRONG_NEGATIVE"
PARTICIPATION_STATES: Final = (
    STRONG_POSITIVE,
    POSITIVE,
    NEUTRAL,
    NEGATIVE,
    STRONG_NEGATIVE,
)

_PARTICIPATION_VALUES: Final = {
    STRONG_POSITIVE: 1.0,
    POSITIVE: 0.5,
    NEUTRAL: 0.0,
    NEGATIVE: -0.5,
    STRONG_NEGATIVE: -1.0,
}
_NORMALIZATION_KNOTS: Final = (
    (-1.0, 0.0),
    (-0.5, 25.0),
    (0.0, 50.0),
    (0.5, 75.0),
    (1.0, 100.0),
)
_ALLOWED_LEADER_WEIGHTS: Final = frozenset({0.5, 0.75, 1.0})
_CONSENSUS_MODIFIERS: Final = (
    (-math.inf, -0.75, -10.0),
    (-0.75, -0.50, -5.0),
    (-0.50, 0.50, 0.0),
    (0.50, 0.75, 5.0),
    (0.75, math.inf, 10.0),
)


class ProductionPolicyError(ValueError):
    """Raised when an explicit policy or input contract is malformed."""


@dataclass(frozen=True)
class ProductionV1PolicyBundle:
    """Immutable lineage for one explicitly supplied Production V1 policy.

    Identity and reference values are caller-supplied from a governed artifact;
    this class deliberately provides no defaults for them.
    """

    candidate_id: str
    candidate_version: str
    policy_id: str
    policy_version: str
    effective_date: date
    leader_set_version: str
    breadth_policy_ref: str
    leadership_policy_ref: str
    normalization_policy_ref: str
    aggregation_policy_ref: str
    weights_policy_ref: str
    eligibility_policy_ref: str
    grade_threshold_ref: str
    rollback_policy: str
    lifecycle: str

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "candidate_version",
            "policy_id",
            "policy_version",
            "leader_set_version",
            "breadth_policy_ref",
            "leadership_policy_ref",
            "normalization_policy_ref",
            "aggregation_policy_ref",
            "weights_policy_ref",
            "eligibility_policy_ref",
            "grade_threshold_ref",
            "rollback_policy",
            "lifecycle",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ProductionPolicyError(f"{field_name} must be non-empty")
            if value != value.strip():
                raise ProductionPolicyError(f"{field_name} must be trimmed")
        if self.lifecycle not in POLICY_LIFECYCLE:
            raise ProductionPolicyError("lifecycle is not a governed policy state")

    @classmethod
    def from_approval(
        cls,
        record: PolicyApprovalRecord,
        *,
        policy_id: str,
        leader_set_version: str,
    ) -> ProductionV1PolicyBundle:
        """Build a bundle from a verified 003G/003H approval artifact.

        ``policy_id`` and ``leader_set_version`` are intentionally required:
        the current approval artifact carries the approved policy version and
        candidate identity, but must not be guessed into a new policy ID or
        Leader Set identity by the implementation.
        """

        require_policy_approval(record)
        required = {
            "candidate_id": record.approved_candidate_id,
            "candidate_version": record.approved_candidate_version,
            "policy_version": record.approved_policy_version,
            "effective_date": record.approved_effective_date,
            "breadth_policy_ref": record.approved_breadth_policy,
            "leadership_policy_ref": record.approved_leadership_policy,
            "normalization_policy_ref": record.approved_normalization_policy,
            "aggregation_policy_ref": record.approved_aggregation_policy,
            "eligibility_policy_ref": record.approved_eligibility_policy,
            "grade_threshold_ref": record.approved_grade_thresholds,
            "rollback_policy": record.rollback_policy,
        }
        missing = tuple(key for key, value in required.items() if value in (None, ""))
        if missing:
            raise ProductionPolicyError(
                "approval artifact is missing policy fields: " + ", ".join(missing)
            )
        return cls(
            candidate_id=required["candidate_id"],
            candidate_version=required["candidate_version"],
            policy_id=policy_id,
            policy_version=required["policy_version"],
            effective_date=required["effective_date"],
            leader_set_version=leader_set_version,
            breadth_policy_ref=required["breadth_policy_ref"],
            leadership_policy_ref=required["leadership_policy_ref"],
            normalization_policy_ref=required["normalization_policy_ref"],
            aggregation_policy_ref=required["aggregation_policy_ref"],
            weights_policy_ref=record.approved_weights,
            eligibility_policy_ref=required["eligibility_policy_ref"],
            grade_threshold_ref=required["grade_threshold_ref"],
            rollback_policy=required["rollback_policy"],
            lifecycle=POLICY_APPROVED,
        )


@dataclass(frozen=True)
class LeaderDefinition:
    member_id: str
    importance: float

    def __post_init__(self) -> None:
        if not self.member_id.strip():
            raise ProductionPolicyError("Leader member_id must be non-empty")
        if self.importance not in _ALLOWED_LEADER_WEIGHTS:
            raise ProductionPolicyError("Leader importance must be 0.50, 0.75, or 1.00")


@dataclass(frozen=True)
class ParticipationObservation:
    member_id: str
    return_pct: float | None

    def __post_init__(self) -> None:
        if not self.member_id.strip():
            raise ProductionPolicyError("observation member_id must be non-empty")
        if self.return_pct is not None and (
            isinstance(self.return_pct, bool)
            or not isinstance(self.return_pct, (int, float))
            or not math.isfinite(float(self.return_pct))
        ):
            raise ProductionPolicyError("return_pct must be finite or None")


@dataclass(frozen=True)
class ProductionTopicInput:
    """Explicit input bundle for one topic and one approved as-of session."""

    topic_id: str
    as_of: date
    core_member_ids: tuple[str, ...]
    observations: tuple[ParticipationObservation, ...]
    leaders: tuple[LeaderDefinition, ...]
    leader_set_version: str
    observation_as_of: date | None
    latest_approved_session: bool

    def __post_init__(self) -> None:
        if not self.topic_id.strip():
            raise ProductionPolicyError("topic_id must be non-empty")
        if not self.core_member_ids:
            raise ProductionPolicyError("core_member_ids must not be empty")
        if any(not member_id.strip() for member_id in self.core_member_ids):
            raise ProductionPolicyError("core_member_ids must be non-empty")
        if len(set(self.core_member_ids)) != len(self.core_member_ids):
            raise ProductionPolicyError("core_member_ids must be unique")
        if not self.leader_set_version.strip():
            raise ProductionPolicyError("leader_set_version must be non-empty")
        observation_ids = tuple(observation.member_id for observation in self.observations)
        if len(set(observation_ids)) != len(observation_ids):
            raise ProductionPolicyError("observations must have unique member_id values")
        leader_ids = tuple(leader.member_id for leader in self.leaders)
        if len(set(leader_ids)) != len(leader_ids):
            raise ProductionPolicyError("leaders must have unique member_id values")
        unknown = set(observation_ids) - set(self.core_member_ids) - set(leader_ids)
        if unknown:
            raise ProductionPolicyError("observations contain unknown members")


@dataclass(frozen=True)
class EligibilityAudit:
    topic_id: str
    as_of: date
    core_member_count: int
    valid_observed_core_count: int
    core_coverage: float | None
    latest_approved_session: bool
    observation_as_of: date | None
    eligible: bool
    excluded_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ProductionV1Evaluation:
    policy: ProductionV1PolicyBundle
    score: TopicScore
    eligibility_audit: EligibilityAudit
    breadth_raw: float | None
    breadth_score: float | None
    leadership_raw: float | None
    leadership_score: float | None
    consensus_raw: float | None
    consensus_modifier: float
    final_leadership_score: float | None
    leader_weight_coverage: float | None
    quality_flags: tuple[str, ...] = ()


def classify_participation(return_pct: float | None) -> str | None:
    """Classify one same-session absolute return using the approved bounds."""

    if return_pct is None:
        return None
    value = float(return_pct)
    if not math.isfinite(value):
        raise ProductionPolicyError("return_pct must be finite")
    if value >= 7.0:
        return STRONG_POSITIVE
    if value >= 2.0:
        return POSITIVE
    if value > -2.0:
        return NEUTRAL
    if value > -7.0:
        return NEGATIVE
    return STRONG_NEGATIVE


def participation_value(state: str) -> float:
    try:
        return _PARTICIPATION_VALUES[state]
    except KeyError as exc:
        raise ProductionPolicyError(f"unknown participation state: {state}") from exc


def normalize_absolute(raw: float | None) -> float | None:
    """Normalize ``[-1,+1]`` with the approved absolute piecewise mapping."""

    if raw is None:
        return None
    value = float(raw)
    if not math.isfinite(value) or not -1.0 <= value <= 1.0:
        raise ProductionPolicyError("normalization input must be finite and in [-1,+1]")
    for (left_x, left_y), (right_x, right_y) in pairwise(_NORMALIZATION_KNOTS):
        if value <= right_x:
            ratio = (value - left_x) / (right_x - left_x)
            return left_y + ratio * (right_y - left_y)
    return _NORMALIZATION_KNOTS[-1][1]


def grade_for_score(score: float | None) -> str | None:
    if score is None:
        return None
    value = float(score)
    if not math.isfinite(value) or not 0.0 <= value <= 100.0:
        raise ProductionPolicyError("score must be finite and in [0,100]")
    if value >= 80.0:
        return "S"
    if value >= 65.0:
        return "A"
    if value >= 50.0:
        return "B"
    return "D"


def select_rollback(
    current: ProductionV1PolicyBundle,
    approved_history: tuple[ProductionV1PolicyBundle, ...],
    target_policy_version: str,
) -> ProductionV1PolicyBundle:
    """Select an earlier approved policy without editing any history."""

    if current.lifecycle != POLICY_APPROVED:
        raise ProductionPolicyError("rollback current policy must be APPROVED")
    candidates = tuple(
        policy
        for policy in approved_history
        if policy.lifecycle == POLICY_APPROVED
        and policy.policy_id == current.policy_id
        and policy.policy_version == target_policy_version
        and policy.effective_date < current.effective_date
    )
    if len(candidates) != 1:
        raise ProductionPolicyError("rollback target must be one earlier approved policy")
    return candidates[0]


def evaluate_production_v1(
    value: ProductionTopicInput, policy: ProductionV1PolicyBundle
) -> ProductionV1Evaluation:
    """Evaluate one explicit topic input without registering a provider."""

    if value.leader_set_version != policy.leader_set_version:
        raise ProductionPolicyError("Leader Set version does not match policy bundle")
    observations = {item.member_id: item for item in value.observations}
    valid_core = tuple(
        member_id
        for member_id in value.core_member_ids
        if member_id in observations and observations[member_id].return_pct is not None
    )
    core_count = len(value.core_member_ids)
    valid_core_count = len(valid_core)
    coverage = valid_core_count / core_count if core_count else None
    reasons: list[str] = []
    if coverage is None or coverage < 0.60:
        reasons.append("CORE_COVERAGE_BELOW_60_PERCENT")
    if valid_core_count < 3:
        reasons.append("VALID_OBSERVED_CORE_COUNT_BELOW_3")
    if (
        not value.latest_approved_session
        or value.observation_as_of is None
        or value.observation_as_of != value.as_of
    ):
        reasons.append("LATEST_APPROVED_AS_OF_EVIDENCE_MISSING")
    audit = EligibilityAudit(
        value.topic_id,
        value.as_of,
        core_count,
        valid_core_count,
        coverage,
        value.latest_approved_session,
        value.observation_as_of,
        not reasons,
        tuple(reasons),
    )
    if value.as_of < policy.effective_date:
        audit = replace(
            audit,
            eligible=False,
            excluded_reasons=(*audit.excluded_reasons, "POLICY_NOT_EFFECTIVE"),
        )

    if not audit.eligible:
        score = _score_result(
            value,
            policy,
            status="INELIGIBLE",
            eligibility="INELIGIBLE",
            score=None,
            grade=None,
            components=(("breadth", None), ("leadership", None)),
            quality_flags=audit.excluded_reasons,
        )
        return ProductionV1Evaluation(
            policy,
            score,
            audit,
            None,
            None,
            None,
            None,
            None,
            0.0,
            None,
            None,
        )

    breadth_values = tuple(
        participation_value(classify_participation(observations[member_id].return_pct))
        for member_id in valid_core
    )
    breadth_raw = sum(breadth_values) / len(breadth_values)
    breadth_score = normalize_absolute(breadth_raw)

    leader_values: list[tuple[float, float, str]] = []
    total_leader_weight = sum(leader.importance for leader in value.leaders)
    for leader in value.leaders:
        observation = observations.get(leader.member_id)
        if observation is None or observation.return_pct is None:
            continue
        state = classify_participation(observation.return_pct)
        leader_values.append((leader.importance, participation_value(state), state))

    if not leader_values:
        score = _score_result(
            value,
            policy,
            status="COMPONENT_UNAVAILABLE",
            eligibility="ELIGIBLE",
            score=None,
            grade=None,
            components=(("breadth", breadth_score), ("leadership", None)),
            breadth_raw=breadth_raw,
            breadth_score=breadth_score,
            quality_flags=("LEADERSHIP_UNAVAILABLE",),
        )
        return ProductionV1Evaluation(
            policy,
            score,
            audit,
            breadth_raw,
            breadth_score,
            None,
            None,
            None,
            0.0,
            None,
            0.0,
            ("LEADERSHIP_UNAVAILABLE",),
        )

    observed_weight = sum(weight for weight, _, _ in leader_values)
    leadership_raw = sum(weight * raw for weight, raw, _ in leader_values) / observed_weight
    leadership_score = normalize_absolute(leadership_raw)
    leader_weight_coverage = observed_weight / total_leader_weight
    positive_weight = sum(
        weight for weight, _, state in leader_values if state in {POSITIVE, STRONG_POSITIVE}
    )
    negative_weight = sum(
        weight for weight, _, state in leader_values if state in {NEGATIVE, STRONG_NEGATIVE}
    )
    consensus_raw = (positive_weight - negative_weight) / observed_weight
    quality_flags: list[str] = []
    if leader_weight_coverage < 0.50:
        consensus_modifier = 0.0
        quality_flags.append("INSUFFICIENT_LEADER_WEIGHT_COVERAGE")
    else:
        consensus_modifier = _consensus_modifier(consensus_raw)
    final_leadership_score = max(0.0, min(100.0, leadership_score + consensus_modifier))
    score_value = 0.60 * breadth_score + 0.40 * final_leadership_score
    score = _score_result(
        value,
        policy,
        status="SCORED",
        eligibility="ELIGIBLE",
        score=score_value,
        grade=grade_for_score(score_value),
        components=(("breadth", breadth_score), ("leadership", final_leadership_score)),
        breadth_raw=breadth_raw,
        breadth_score=breadth_score,
        leadership_raw=leadership_raw,
        leadership_score=final_leadership_score,
        quality_flags=quality_flags,
    )
    return ProductionV1Evaluation(
        policy,
        score,
        audit,
        breadth_raw,
        breadth_score,
        leadership_raw,
        leadership_score,
        consensus_raw,
        consensus_modifier,
        final_leadership_score,
        leader_weight_coverage,
        tuple(quality_flags),
    )


def _consensus_modifier(raw: float) -> float:
    if raw >= 0.75:
        return 10.0
    if raw >= 0.50:
        return 5.0
    if raw > -0.50:
        return 0.0
    if raw > -0.75:
        return -5.0
    return -10.0


def _score_result(
    value: ProductionTopicInput,
    policy: ProductionV1PolicyBundle,
    *,
    status: str,
    eligibility: str,
    score: float | None,
    grade: str | None,
    components: tuple[tuple[str, float | None], ...],
    breadth_raw: float | None = None,
    breadth_score: float | None = None,
    leadership_raw: float | None = None,
    leadership_score: float | None = None,
    quality_flags: tuple[str, ...] = (),
) -> TopicScore:
    evidence = _production_evidence(
        value,
        policy,
        breadth_raw=breadth_raw,
        breadth_score=breadth_score,
        leadership_raw=leadership_raw,
        leadership_score=leadership_score,
        quality_flags=quality_flags,
        ready=status == "SCORED",
    )
    return TopicScore(
        topic_id=value.topic_id,
        as_of=value.as_of,
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        feature_set_version=PRODUCTION_V1_MECHANICS,
        runtime_version=PRODUCTION_V1_MECHANICS,
        aggregation_version=policy.aggregation_policy_ref,
        status=status,
        score=score,
        grade=grade,
        evidence=evidence,
        components=components,
        confidence=None,
        eligibility=eligibility,
    )


def _production_evidence(
    value: ProductionTopicInput,
    policy: ProductionV1PolicyBundle,
    *,
    breadth_raw: float | None,
    breadth_score: float | None,
    leadership_raw: float | None,
    leadership_score: float | None,
    quality_flags: tuple[str, ...],
    ready: bool,
) -> FeatureAggregate:
    """Adapt explicit Production V1 outputs to the existing evidence contract.

    This is a serialization/lineage adapter only. It does not calculate a
    feature, change a score, or make a provider available by default.
    """

    breadth_status = (
        FeatureStatus.READY if breadth_score is not None else FeatureStatus.DATA_INSUFFICIENT
    )
    leadership_status = (
        FeatureStatus.READY if leadership_score is not None else FeatureStatus.DATA_INSUFFICIENT
    )
    results = (
        FeatureResult(
            "production_breadth",
            PRODUCTION_V1_MECHANICS,
            value.topic_id,
            value.as_of,
            breadth_status,
            {"raw": breadth_raw, "normalized": breadth_score},
        ),
        FeatureResult(
            "production_leadership",
            PRODUCTION_V1_MECHANICS,
            value.topic_id,
            value.as_of,
            leadership_status,
            {"raw": leadership_raw, "normalized": leadership_score},
        ),
    )
    ready_count = sum(result.status == FeatureStatus.READY for result in results)
    insufficient_count = len(results) - ready_count
    return FeatureAggregate(
        topic_id=value.topic_id,
        as_of=value.as_of,
        feature_set_version=PRODUCTION_V1_MECHANICS,
        aggregation_version=policy.aggregation_policy_ref,
        status=AggregateStatus.READY_UNSCORED if ready else AggregateStatus.DATA_INSUFFICIENT,
        feature_results=results,
        quality=QualitySummary(ready_count, insufficient_count, 0, None, None),
        quality_flags=tuple(sorted(set(quality_flags))),
    )


__all__ = [
    "NEGATIVE",
    "NEUTRAL",
    "PARTICIPATION_STATES",
    "POLICY_APPROVED",
    "POLICY_CANDIDATE",
    "POLICY_DEPRECATED",
    "POLICY_DRAFT",
    "POSITIVE",
    "STRONG_NEGATIVE",
    "STRONG_POSITIVE",
    "EligibilityAudit",
    "LeaderDefinition",
    "ParticipationObservation",
    "ProductionPolicyError",
    "ProductionTopicInput",
    "ProductionV1Evaluation",
    "ProductionV1PolicyBundle",
    "classify_participation",
    "evaluate_production_v1",
    "grade_for_score",
    "normalize_absolute",
    "participation_value",
    "select_rollback",
]
