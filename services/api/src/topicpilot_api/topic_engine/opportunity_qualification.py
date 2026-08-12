"""Shadow-only Opportunity Qualification Policy V1.

TASK-BE-024B freezes the semantic order of Opportunity qualification above the
existing 024/024A strategy evaluators.  The policy consumes upstream Topic
Grade/Lifecycle and canonical OHLCV-derived evidence; it never recalculates
Topic Score, Grade, or Lifecycle and it never publishes a recommendation.

Semantic decisions are frozen for this shadow contract.  Numeric thresholds,
weights, and future calibration parameters remain explicitly provisional,
tunable, and versioned.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from .opportunity_evidence import TechnicalEvidenceBundle, build_technical_evidence
from .opportunity_shadow import (
    EVIDENCE_DERIVED,
    EVIDENCE_OBSERVED,
    EVIDENCE_UNAVAILABLE,
    FAIL,
    PASS,
    UNKNOWN,
    Evidence,
    StageAssessment,
)

if TYPE_CHECKING:  # pragma: no cover - type-only imports avoid strategy cycles
    from .opportunity_strategies import (
        OpportunityStrategyInput,
        OpportunityStrategyResult,
    )

QUALIFICATION_CONTRACT_VERSION = "opportunity-qualification.v1.shadow"
QUALIFICATION_POLICY_VERSION = "opportunity-qualification-policy.v1"
QUALIFICATION_POLICY_STATUS = "PM_SEMANTIC_FREEZE_SHADOW"
QUALIFICATION_PARAMETER_VERSION = "opportunity-qualification-parameters.v1.provisional"
QUALIFICATION_PARAMETER_STATUS = "PROVISIONAL_TUNABLE_VERSIONED"

QUALIFICATION_FORMAL = "FORMAL_OPPORTUNITY"
QUALIFICATION_EXCEPTION = "EXCEPTION_CANDIDATE"
QUALIFICATION_WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
QUALIFICATION_DEFERRED = "DEFERRED"
QUALIFICATION_EXCLUDED = "EXCLUDED"
QUALIFICATION_NOT_EVALUATED = "NOT_EVALUATED"
QUALIFICATION_STATUSES = (
    QUALIFICATION_FORMAL,
    QUALIFICATION_EXCEPTION,
    QUALIFICATION_WAITING_CONFIRMATION,
    QUALIFICATION_DEFERRED,
    QUALIFICATION_EXCLUDED,
    QUALIFICATION_NOT_EVALUATED,
)

GRADE_S = "S"
GRADE_A = "A"
GRADE_B = "B"
GRADE_D = "D"
FORMAL_GRADES = frozenset({GRADE_S, GRADE_A})
EXCEPTION_GRADES = frozenset({GRADE_B})
HARD_EXCLUDED_GRADES = frozenset({GRADE_D})

LIFECYCLE_SPROUTING = "SPROUTING"
LIFECYCLE_FERMENTING = "FERMENTING"
LIFECYCLE_MAIN_RISE = "MAIN_RISE"
LIFECYCLE_MATURE = "MATURE"
LIFECYCLE_DECLINING = "DECLINING"
LIFECYCLE_STAGES = (
    LIFECYCLE_SPROUTING,
    LIFECYCLE_FERMENTING,
    LIFECYCLE_MAIN_RISE,
    LIFECYCLE_MATURE,
    LIFECYCLE_DECLINING,
)

STRATEGY_TREND_CONTINUATION = "TREND_CONTINUATION"
STRATEGY_CATCH_UP = "CATCH_UP"
STRATEGY_IDS = (STRATEGY_TREND_CONTINUATION, STRATEGY_CATCH_UP)

LIFECYCLE_QUALIFIED = "QUALIFIED"
LIFECYCLE_CONFIRMATION_REQUIRED = "WAITING_CONFIRMATION"
LIFECYCLE_HARD_EXCLUDE = "HARD_EXCLUDE"
LIFECYCLE_HIGH_FIT = "HIGH_FIT"
LIFECYCLE_MEDIUM_HIGH_FIT = "MEDIUM_HIGH_FIT"
LIFECYCLE_LOW_FIT = "LOW_FIT"
LIFECYCLE_STRICTER_GATES = "RETAIN_STRICTER_GATES"

PRESENTATION_CAP_TREND = 3
PRESENTATION_CAP_CATCH_UP = 2
RANKING_CADENCE_POST_CLOSE = "POST_CLOSE"
INTRADAY_BEHAVIOR_STATUS_ONLY = "STATUS_ONLY"


def _topic_flag(theme: object, *names: str) -> bool:
    for name in names:
        value = getattr(theme, name, None)
        if value is True:
            return True
    snapshot = getattr(theme, "topic_snapshot", None)
    if isinstance(snapshot, dict):
        for name in names:
            if snapshot.get(name) is True:
                return True
    return False


def _tuple_text(values: Iterable[object]) -> tuple[str, ...]:
    return tuple(item.strip() for item in values if isinstance(item, str) and item.strip())


@dataclass(frozen=True)
class OpportunityQualificationPolicy:
    """PM semantic freeze plus versioned provisional parameter metadata."""

    policy_version: str = QUALIFICATION_POLICY_VERSION
    policy_status: str = QUALIFICATION_POLICY_STATUS
    parameter_version: str = QUALIFICATION_PARAMETER_VERSION
    parameter_status: str = QUALIFICATION_PARAMETER_STATUS
    formal_grades: frozenset[str] = FORMAL_GRADES
    exception_grades: frozenset[str] = EXCEPTION_GRADES
    hard_excluded_grades: frozenset[str] = HARD_EXCLUDED_GRADES
    trend_lifecycles: frozenset[str] = frozenset(
        {
            LIFECYCLE_SPROUTING,
            LIFECYCLE_FERMENTING,
            LIFECYCLE_MAIN_RISE,
            LIFECYCLE_MATURE,
        }
    )
    catch_up_lifecycles: frozenset[str] = frozenset(
        {
            LIFECYCLE_SPROUTING,
            LIFECYCLE_FERMENTING,
            LIFECYCLE_MAIN_RISE,
            LIFECYCLE_MATURE,
        }
    )
    mature_catch_up_confirmation: bool = True
    declining_lifecycles: frozenset[str] = frozenset({LIFECYCLE_DECLINING})
    twenty_ma_gate: str = "CLOSE_GE_20MA"
    sixty_ma_role: str = "STRUCTURE_AND_RANKING_FACTOR"
    risk_precedes_ranking: bool = True
    b_grade_requires_warming_or_improving: bool = True
    b_grade_exception_provenance_required: bool = True
    trend_presentation_cap: int = PRESENTATION_CAP_TREND
    catch_up_presentation_cap: int = PRESENTATION_CAP_CATCH_UP
    ranking_cadence: str = RANKING_CADENCE_POST_CLOSE
    intraday_behavior: str = INTRADAY_BEHAVIOR_STATUS_ONLY
    intraday_reranking: bool = False

    def __post_init__(self) -> None:
        if self.policy_status != QUALIFICATION_POLICY_STATUS:
            raise ValueError("qualification policy status must remain PM semantic freeze shadow")
        if self.parameter_status != QUALIFICATION_PARAMETER_STATUS:
            raise ValueError("qualification parameters must remain provisional/versioned")
        if self.formal_grades != FORMAL_GRADES:
            raise ValueError("formal Opportunity grades must remain S/A")
        if self.exception_grades != EXCEPTION_GRADES:
            raise ValueError("exception grade must remain B")
        if self.hard_excluded_grades != HARD_EXCLUDED_GRADES:
            raise ValueError("hard excluded grade must remain D")
        if self.trend_presentation_cap != PRESENTATION_CAP_TREND:
            raise ValueError("Trend presentation cap must remain Top 3")
        if self.catch_up_presentation_cap != PRESENTATION_CAP_CATCH_UP:
            raise ValueError("Catch-up presentation cap must remain Top 2")
        if self.ranking_cadence != RANKING_CADENCE_POST_CLOSE:
            raise ValueError("V1 ranking cadence must remain post-close")
        if self.intraday_behavior != INTRADAY_BEHAVIOR_STATUS_ONLY:
            raise ValueError("V1 intraday behavior must remain status-only")
        if self.intraday_reranking:
            raise ValueError("V1 intraday reranking is disabled")
        for name in ("trend_presentation_cap", "catch_up_presentation_cap"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        for name in (
            "formal_grades",
            "exception_grades",
            "hard_excluded_grades",
            "trend_lifecycles",
            "catch_up_lifecycles",
            "declining_lifecycles",
        ):
            if any(not isinstance(item, str) or not item.strip() for item in getattr(self, name)):
                raise ValueError(f"{name} must contain non-empty text")

    def lifecycle_status(self, strategy_id: str, lifecycle: str) -> str:
        if lifecycle in self.declining_lifecycles:
            return LIFECYCLE_HARD_EXCLUDE
        if strategy_id == STRATEGY_TREND_CONTINUATION:
            if lifecycle == LIFECYCLE_SPROUTING:
                return LIFECYCLE_CONFIRMATION_REQUIRED
            if lifecycle == LIFECYCLE_MATURE:
                return LIFECYCLE_LOW_FIT
            return (
                LIFECYCLE_HIGH_FIT
                if lifecycle in self.trend_lifecycles
                else LIFECYCLE_HARD_EXCLUDE
            )
        if strategy_id == STRATEGY_CATCH_UP:
            if lifecycle not in self.catch_up_lifecycles:
                return LIFECYCLE_HARD_EXCLUDE
            if lifecycle == LIFECYCLE_SPROUTING:
                return LIFECYCLE_CONFIRMATION_REQUIRED
            if lifecycle == LIFECYCLE_MATURE and self.mature_catch_up_confirmation:
                return LIFECYCLE_STRICTER_GATES
            if lifecycle == LIFECYCLE_FERMENTING:
                return LIFECYCLE_MEDIUM_HIGH_FIT
            return LIFECYCLE_HIGH_FIT
        return LIFECYCLE_HARD_EXCLUDE

    def presentation_cap(self, strategy_id: str) -> int:
        if strategy_id == STRATEGY_TREND_CONTINUATION:
            return self.trend_presentation_cap
        if strategy_id == STRATEGY_CATCH_UP:
            return self.catch_up_presentation_cap
        return 0

    def as_dict(self) -> dict[str, object]:
        matrix = {
            strategy: {
                lifecycle: self.lifecycle_status(strategy, lifecycle)
                for lifecycle in LIFECYCLE_STAGES
            }
            for strategy in STRATEGY_IDS
        }
        return {
            "contractVersion": QUALIFICATION_CONTRACT_VERSION,
            "policyVersion": self.policy_version,
            "policyStatus": self.policy_status,
            "parameterVersion": self.parameter_version,
            "parameterStatus": self.parameter_status,
            "gradePolicy": {
                "formal": sorted(self.formal_grades),
                "exception": sorted(self.exception_grades),
                "hardExcluded": sorted(self.hard_excluded_grades),
                "bRequiresWarmingOrImproving": self.b_grade_requires_warming_or_improving,
                "bRequiresExceptionProvenance": self.b_grade_exception_provenance_required,
            },
            "lifecycleStrategyMatrix": matrix,
            "technicalPolicy": {
                "twentyMa": self.twenty_ma_gate,
                "sixtyMa": self.sixty_ma_role,
            },
            "ordering": {
                "riskBeforeRanking": self.risk_precedes_ranking,
                "rankingCadence": self.ranking_cadence,
                "intradayBehavior": self.intraday_behavior,
                "intradayReranking": self.intraday_reranking,
            },
            "presentationCaps": {
                STRATEGY_TREND_CONTINUATION: self.trend_presentation_cap,
                STRATEGY_CATCH_UP: self.catch_up_presentation_cap,
            },
        }


@dataclass(frozen=True)
class OpportunityQualificationDecision:
    contract_version: str
    policy_version: str
    parameter_version: str
    strategy_id: str
    grade: str | None
    lifecycle: str | None
    status: str
    grade_status: str
    lifecycle_status: str
    twenty_ma_status: str
    sixty_ma_status: str
    risk_status: str
    exception_candidate: bool
    presentation_eligible: bool
    reason_codes: tuple[str, ...]
    evidence: tuple[Evidence, ...]

    def __post_init__(self) -> None:
        if self.contract_version != QUALIFICATION_CONTRACT_VERSION:
            raise ValueError("unsupported qualification contract")
        if self.status not in QUALIFICATION_STATUSES:
            raise ValueError(f"unknown qualification status: {self.status}")

    def as_dict(self) -> dict[str, object]:
        return {
            "contractVersion": self.contract_version,
            "policyVersion": self.policy_version,
            "parameterVersion": self.parameter_version,
            "strategyId": self.strategy_id,
            "grade": self.grade,
            "lifecycle": self.lifecycle,
            "status": self.status,
            "gradeStatus": self.grade_status,
            "lifecycleStatus": self.lifecycle_status,
            "twentyMaStatus": self.twenty_ma_status,
            "sixtyMaStatus": self.sixty_ma_status,
            "riskStatus": self.risk_status,
            "exceptionCandidate": self.exception_candidate,
            "presentationEligible": self.presentation_eligible,
            "reasonCodes": list(self.reason_codes),
            "evidence": [item.as_dict() for item in self.evidence],
        }


def _assessment(status: str, code: str, *evidence: Evidence) -> StageAssessment:
    return StageAssessment(status, (code,), tuple(evidence))


def _grade_decision(
    theme: object, policy: OpportunityQualificationPolicy
) -> tuple[str, str, bool, tuple[str, ...], tuple[Evidence, ...]]:
    grade = getattr(theme, "grade", None)
    if grade is None:
        return (
            QUALIFICATION_DEFERRED,
            "UNKNOWN",
            False,
            ("TOPIC_GRADE_UNAVAILABLE",),
            (Evidence("TOPIC_GRADE", EVIDENCE_UNAVAILABLE),),
        )
    if grade in policy.formal_grades:
        return (
            QUALIFICATION_FORMAL,
            "PASS",
            False,
            ("TOPIC_GRADE_FORMAL_UNIVERSE",),
            (Evidence("TOPIC_GRADE", EVIDENCE_OBSERVED, grade),),
        )
    if grade in policy.hard_excluded_grades:
        return (
            QUALIFICATION_EXCLUDED,
            "FAIL",
            False,
            ("TOPIC_GRADE_D_HARD_EXCLUDE",),
            (Evidence("TOPIC_GRADE", EVIDENCE_OBSERVED, grade),),
        )
    if grade in policy.exception_grades:
        warming = _topic_flag(theme, "warming_candidate", "warmingCandidate", "is_warming")
        provenance = _tuple_text(getattr(theme, "exception_provenance", ()))
        warming_evidence = tuple(getattr(theme, "warming_evidence", ()))
        has_warming_signal = warming or bool(warming_evidence)
        # The warming flag is the eligibility signal; it is not itself an
        # auditable exception provenance record.  A B-grade exception must
        # carry an explicit upstream reason/evidence item as well.
        warming = warming or bool(warming_evidence)
        has_provenance = bool(provenance)
        if policy.b_grade_requires_warming_or_improving and not has_warming_signal:
            return (
                QUALIFICATION_EXCLUDED,
                "FAIL",
                False,
                ("TOPIC_GRADE_B_EXCEPTION_NOT_QUALIFIED",),
                (Evidence("TOPIC_GRADE", EVIDENCE_OBSERVED, grade),),
            )
        if policy.b_grade_exception_provenance_required and not has_provenance:
            return (
                QUALIFICATION_EXCLUDED,
                "FAIL",
                False,
                ("TOPIC_GRADE_B_EXCEPTION_PROVENANCE_MISSING",),
                (Evidence("TOPIC_GRADE", EVIDENCE_OBSERVED, grade),),
            )
        evidence = (
            Evidence("TOPIC_GRADE", EVIDENCE_OBSERVED, grade),
            Evidence("TOPIC_WARMING_CANDIDATE", EVIDENCE_OBSERVED, has_warming_signal),
            Evidence(
                "EXCEPTION_PROVENANCE",
                EVIDENCE_DERIVED,
                ",".join(provenance) or "UPSTREAM_WARMING_FLAG",
            ),
            *warming_evidence,
        )
        return (
            QUALIFICATION_EXCEPTION,
            "PASS",
            True,
            ("TOPIC_GRADE_B_EXCEPTION_CANDIDATE",),
            evidence,
        )
    return (
        QUALIFICATION_EXCLUDED,
        "FAIL",
        False,
        ("TOPIC_GRADE_UNSUPPORTED",),
        (Evidence("TOPIC_GRADE", EVIDENCE_OBSERVED, grade),),
    )


def _technical_qualification(
    technical: TechnicalEvidenceBundle,
) -> tuple[str, str, str, tuple[str, ...], tuple[Evidence, ...]]:
    if technical.sufficiency.assessment.status == UNKNOWN:
        return (
            QUALIFICATION_DEFERRED,
            UNKNOWN,
            UNKNOWN,
            ("TECHNICAL_DATA_DEFERRED",),
            technical.sufficiency.assessment.evidence,
        )
    if technical.sufficiency.assessment.status == FAIL:
        return (
            QUALIFICATION_DEFERRED,
            UNKNOWN,
            UNKNOWN,
            ("TECHNICAL_HISTORY_INSUFFICIENT", "TWENTY_MA_REQUIRED_EVIDENCE_UNAVAILABLE"),
            technical.sufficiency.assessment.evidence,
        )
    price = technical.price_volume.price
    ma20 = technical.ma20.value
    if price is None or ma20 is None or technical.ma20.status == UNKNOWN:
        return (
            QUALIFICATION_DEFERRED,
            UNKNOWN,
            UNKNOWN,
            ("TWENTY_MA_REQUIRED_EVIDENCE_UNAVAILABLE",),
            (
                Evidence("PRICE", EVIDENCE_UNAVAILABLE, price),
                Evidence("MA20", EVIDENCE_UNAVAILABLE, ma20),
            ),
        )
    ma20_status = PASS if price >= ma20 else FAIL
    if ma20_status == FAIL:
        return (
            QUALIFICATION_EXCLUDED,
            FAIL,
            UNKNOWN,
            ("CLOSE_BELOW_20MA_HARD_EXCLUDE",),
            (
                Evidence("PRICE", EVIDENCE_OBSERVED, price),
                Evidence("MA20", EVIDENCE_DERIVED, ma20),
                Evidence("TWENTY_MA_GATE", EVIDENCE_DERIVED, "CLOSE_GE_20MA"),
            ),
        )
    ma60 = technical.ma60.value
    if ma60 is None or technical.ma60.status == UNKNOWN:
        return (
            QUALIFICATION_FORMAL,
            PASS,
            UNKNOWN,
            ("TWENTY_MA_GATE_PASS", "SIXTY_MA_STRUCTURE_UNAVAILABLE"),
            (
                Evidence("PRICE", EVIDENCE_OBSERVED, price),
                Evidence("MA20", EVIDENCE_DERIVED, ma20),
                Evidence("MA60", EVIDENCE_UNAVAILABLE, ma60),
            ),
        )
    structure_code = (
        "PRICE_ABOVE_20MA_ABOVE_60MA_STRUCTURE"
        if price >= ma20 >= ma60
        else "PRICE_ABOVE_20MA_RECOVERY_BELOW_60MA"
    )
    sixty_ma_status = PASS if price >= ma60 else "RECOVERY"
    return (
        QUALIFICATION_FORMAL,
        PASS,
        sixty_ma_status,
        ("TWENTY_MA_GATE_PASS", structure_code),
        (
            Evidence("PRICE", EVIDENCE_OBSERVED, price),
            Evidence("MA20", EVIDENCE_DERIVED, ma20),
            Evidence("MA60", EVIDENCE_DERIVED, ma60),
            Evidence("SIXTY_MA_ROLE", EVIDENCE_DERIVED, "STRUCTURE_AND_RANKING_FACTOR"),
        ),
    )


def _risk_qualification(
    technical: TechnicalEvidenceBundle,
) -> tuple[str, str, tuple[str, ...], tuple[Evidence, ...]]:
    bearish = technical.bearish_break
    weak = technical.weak_candle
    if bearish.assessment.status == UNKNOWN:
        return QUALIFICATION_DEFERRED, UNKNOWN, ("RISK_CONTEXT_UNAVAILABLE",), bearish.evidence
    if bearish.assessment.status == FAIL:
        return (
            QUALIFICATION_EXCLUDED,
            FAIL,
            ("CONFIRMED_SUPPORT_OR_STRUCTURAL_BREAK_HARD_EXCLUDE",),
            bearish.evidence,
        )
    evidence = (*bearish.evidence, *weak.evidence)
    if weak.assessment.status == FAIL:
        if technical.price_volume.assessment.status == FAIL:
            return (
                QUALIFICATION_WAITING_CONFIRMATION,
                PASS,
                ("PERSISTENT_WEAKNESS_CONFIRMATION_REQUIRED",),
                evidence,
            )
        return (
            QUALIFICATION_FORMAL,
            PASS,
            ("SINGLE_OR_LIMITED_WEAK_CANDLE_RISK_CONTEXT",),
            evidence,
        )
    if weak.assessment.status == UNKNOWN:
        return QUALIFICATION_DEFERRED, UNKNOWN, ("WEAK_CANDLE_CONTEXT_UNAVAILABLE",), evidence
    return QUALIFICATION_FORMAL, PASS, ("RISK_GATE_CLEAR_BEFORE_RANKING",), evidence


def qualify_opportunity(
    result: OpportunityStrategyResult,
    value: OpportunityStrategyInput,
    policy: OpportunityQualificationPolicy | None = None,
    *,
    technical: TechnicalEvidenceBundle | None = None,
) -> OpportunityQualificationDecision:
    """Evaluate the frozen V1 qualification order deterministically."""

    active = policy or OpportunityQualificationPolicy()
    strategy_id = result.strategy_id
    grade = value.theme.grade
    lifecycle = value.theme.lifecycle
    grade_status, grade_gate, exception_candidate, grade_codes, grade_evidence = _grade_decision(
        value.theme, active
    )
    lifecycle_gate = (
        "UNKNOWN" if lifecycle is None else active.lifecycle_status(strategy_id, lifecycle)
    )
    lifecycle_codes: tuple[str, ...]
    lifecycle_evidence: tuple[Evidence, ...]
    if lifecycle is None:
        lifecycle_codes = ("TOPIC_LIFECYCLE_UNAVAILABLE",)
        lifecycle_evidence = (Evidence("TOPIC_LIFECYCLE", EVIDENCE_UNAVAILABLE),)
        lifecycle_gate = "UNKNOWN"
    elif lifecycle_gate == LIFECYCLE_HARD_EXCLUDE:
        lifecycle_codes = ("TOPIC_LIFECYCLE_NOT_QUALIFIED",)
        lifecycle_evidence = (Evidence("TOPIC_LIFECYCLE", EVIDENCE_OBSERVED, lifecycle),)
    elif lifecycle_gate == LIFECYCLE_CONFIRMATION_REQUIRED:
        lifecycle_codes = ("TOPIC_LIFECYCLE_WAITING_CONFIRMATION",)
        lifecycle_evidence = (
            Evidence("TOPIC_LIFECYCLE", EVIDENCE_OBSERVED, lifecycle),
            Evidence("LIFECYCLE_STRATEGY_FIT", EVIDENCE_DERIVED, lifecycle_gate),
        )
    else:
        lifecycle_codes = (f"TOPIC_LIFECYCLE_{lifecycle_gate}",)
        lifecycle_evidence = (
            Evidence("TOPIC_LIFECYCLE", EVIDENCE_OBSERVED, lifecycle),
            Evidence("LIFECYCLE_STRATEGY_FIT", EVIDENCE_DERIVED, lifecycle_gate),
        )
    technical_bundle = technical or build_technical_evidence(
        value.stock.bars, value.policy.technical_policy, as_of=value.as_of
    )
    technical_status, ma20_status, ma60_status, technical_codes, technical_evidence = (
        _technical_qualification(technical_bundle)
    )
    risk_status, risk_gate, risk_codes, risk_evidence = _risk_qualification(technical_bundle)
    reasons = (*grade_codes, *lifecycle_codes, *technical_codes, *risk_codes)
    evidence = (*grade_evidence, *lifecycle_evidence, *technical_evidence, *risk_evidence)

    if grade_status in {QUALIFICATION_DEFERRED, QUALIFICATION_EXCLUDED}:
        status = grade_status
    elif lifecycle_gate == "UNKNOWN":
        status = QUALIFICATION_DEFERRED
    elif lifecycle_gate == LIFECYCLE_HARD_EXCLUDE:
        status = QUALIFICATION_EXCLUDED
    elif technical_status in {QUALIFICATION_DEFERRED, QUALIFICATION_EXCLUDED}:
        status = technical_status
    elif risk_status in {QUALIFICATION_DEFERRED, QUALIFICATION_EXCLUDED}:
        status = risk_status
    elif result.status == "DEFERRED":
        status = QUALIFICATION_DEFERRED
    elif result.status == "FUTURE_NOT_IMPLEMENTED":
        status = QUALIFICATION_EXCLUDED
    elif result.status == "EXCLUDED":
        soft_codes = {
            "VOLUME_ACTIVATION_BELOW_POLICY",
            "VOLUME_CONFIRMATION_WEAK",
            "PERSISTENT_WEAKNESS_CONFIRMATION_REQUIRED",
        }
        status = (
            QUALIFICATION_WAITING_CONFIRMATION
            if set(result.exclusion_codes).issubset(soft_codes)
            and bool(result.exclusion_codes)
            else QUALIFICATION_EXCLUDED
        )
    elif (
        lifecycle_gate in {LIFECYCLE_CONFIRMATION_REQUIRED, LIFECYCLE_STRICTER_GATES}
        or risk_status == QUALIFICATION_WAITING_CONFIRMATION
    ):
        status = QUALIFICATION_WAITING_CONFIRMATION
    elif grade_status == QUALIFICATION_EXCEPTION:
        status = QUALIFICATION_EXCEPTION
    else:
        status = QUALIFICATION_FORMAL

    presentation_eligible = status in {
        QUALIFICATION_FORMAL,
        QUALIFICATION_EXCEPTION,
        QUALIFICATION_WAITING_CONFIRMATION,
    }
    return OpportunityQualificationDecision(
        QUALIFICATION_CONTRACT_VERSION,
        active.policy_version,
        active.parameter_version,
        strategy_id,
        grade,
        lifecycle,
        status,
        grade_gate,
        lifecycle_gate,
        ma20_status,
        ma60_status,
        risk_gate,
        exception_candidate,
        presentation_eligible,
        _tuple_text(reasons),
        evidence,
    )


def qualification_stage(decision: OpportunityQualificationDecision) -> StageAssessment:
    status = (
        FAIL
        if decision.status == QUALIFICATION_EXCLUDED
        else UNKNOWN
        if decision.status == QUALIFICATION_DEFERRED
        else PASS
    )
    return StageAssessment(status, decision.reason_codes, decision.evidence)


def apply_qualification_policy(
    result: OpportunityStrategyResult,
    value: OpportunityStrategyInput,
    policy: OpportunityQualificationPolicy | None = None,
) -> OpportunityStrategyResult:
    """Attach qualification provenance and enforce gates before presentation."""

    decision = qualify_opportunity(result, value, policy)
    from .opportunity_strategies import (
        DECISION_STATE_DEFERRED,
        DECISION_STATE_EXCLUDED,
        DECISION_STATE_WAITING_CONFIRMATION,
        QUALIFICATION_NONE,
        RANKING_STATUS_UNAVAILABLE,
        RESULT_DEFERRED,
        RESULT_EXCLUDED,
        StrategyStage,
    )
    from .opportunity_strategies import (
        QUALIFICATION_EXCEPTION as RESULT_QUALIFICATION_EXCEPTION,
    )
    from .opportunity_strategies import (
        QUALIFICATION_FORMAL as RESULT_QUALIFICATION_FORMAL,
    )

    stages = (
        *result.stages,
        StrategyStage("QUALIFICATION_POLICY", qualification_stage(decision)),
    )
    evidence = result.evidence + decision.evidence
    status = result.status
    eligibility = result.eligibility
    state = result.opportunity_state
    rank_score = result.rank_score
    ranking_status = result.ranking_status
    if decision.status == QUALIFICATION_EXCLUDED and result.status != "FUTURE_NOT_IMPLEMENTED":
        status = RESULT_EXCLUDED
        eligibility = FAIL
        state = DECISION_STATE_EXCLUDED
        rank_score = None
        ranking_status = RANKING_STATUS_UNAVAILABLE
    elif decision.status == QUALIFICATION_DEFERRED:
        status = RESULT_DEFERRED
        eligibility = UNKNOWN
        state = DECISION_STATE_DEFERRED
        rank_score = None
        ranking_status = RANKING_STATUS_UNAVAILABLE
    elif decision.status == QUALIFICATION_WAITING_CONFIRMATION:
        state = DECISION_STATE_WAITING_CONFIRMATION
    return replace(
        result,
        status=status,
        eligibility=eligibility,
        exclusion_codes=result.exclusion_codes
        + tuple(code for code in decision.reason_codes if code not in result.exclusion_codes)
        if decision.status == QUALIFICATION_EXCLUDED
        else result.exclusion_codes,
        stages=stages,
        evidence=evidence,
        rank_score=rank_score,
        ranking_status=ranking_status,
        opportunity_state=state,
        qualification_status=decision.status,
        qualification_reason_codes=decision.reason_codes,
        qualification_exception=decision.exception_candidate,
        qualification_policy_version=decision.policy_version,
        qualification_parameter_version=decision.parameter_version,
        qualification_class=(
            RESULT_QUALIFICATION_EXCEPTION
            if decision.status == QUALIFICATION_EXCEPTION
            else RESULT_QUALIFICATION_FORMAL
            if decision.status in {QUALIFICATION_FORMAL, QUALIFICATION_WAITING_CONFIRMATION}
            else QUALIFICATION_NONE
        ),
    )


def presentation_candidates(
    results: Iterable[OpportunityStrategyResult],
    policy: OpportunityQualificationPolicy | None = None,
) -> tuple[OpportunityStrategyResult, ...]:
    """Return only the user-facing cap while retaining all backend ranks."""

    active = policy or OpportunityQualificationPolicy()
    values = tuple(results)
    if len({item.strategy_id for item in values}) > 1:
        raise ValueError("presentation_candidates accepts one strategy at a time")
    strategy_id = values[0].strategy_id if values else ""
    cap = active.presentation_cap(strategy_id)
    eligible = tuple(
        item
        for item in values
        if getattr(item, "qualification_status", QUALIFICATION_NOT_EVALUATED)
        in {
            QUALIFICATION_FORMAL,
            QUALIFICATION_EXCEPTION,
            QUALIFICATION_WAITING_CONFIRMATION,
            QUALIFICATION_NOT_EVALUATED,
        }
        and item.opportunity_state not in {"DEFERRED", "EXCLUDED"}
    )
    ordered = tuple(
        sorted(
            eligible,
            key=lambda item: (
                item.rank_score is not None,
                item.rank_score if item.rank_score is not None else float("-inf"),
                item.instrument_id,
            ),
            reverse=True,
        )
    )
    return ordered[:cap]


def policy_for_strategy(value: OpportunityStrategyInput) -> OpportunityQualificationPolicy:
    """Convenience factory kept explicit so policy ownership is discoverable."""

    return OpportunityQualificationPolicy()


__all__ = [
    "EXCEPTION_GRADES",
    "FORMAL_GRADES",
    "GRADE_A",
    "GRADE_B",
    "GRADE_D",
    "GRADE_S",
    "HARD_EXCLUDED_GRADES",
    "INTRADAY_BEHAVIOR_STATUS_ONLY",
    "LIFECYCLE_CONFIRMATION_REQUIRED",
    "LIFECYCLE_DECLINING",
    "LIFECYCLE_FERMENTING",
    "LIFECYCLE_HARD_EXCLUDE",
    "LIFECYCLE_HIGH_FIT",
    "LIFECYCLE_LOW_FIT",
    "LIFECYCLE_MAIN_RISE",
    "LIFECYCLE_MATURE",
    "LIFECYCLE_MEDIUM_HIGH_FIT",
    "LIFECYCLE_SPROUTING",
    "LIFECYCLE_STRICTER_GATES",
    "PRESENTATION_CAP_CATCH_UP",
    "PRESENTATION_CAP_TREND",
    "QUALIFICATION_CONTRACT_VERSION",
    "QUALIFICATION_DEFERRED",
    "QUALIFICATION_EXCEPTION",
    "QUALIFICATION_EXCLUDED",
    "QUALIFICATION_FORMAL",
    "QUALIFICATION_NOT_EVALUATED",
    "QUALIFICATION_PARAMETER_STATUS",
    "QUALIFICATION_PARAMETER_VERSION",
    "QUALIFICATION_POLICY_STATUS",
    "QUALIFICATION_POLICY_VERSION",
    "QUALIFICATION_STATUSES",
    "QUALIFICATION_WAITING_CONFIRMATION",
    "RANKING_CADENCE_POST_CLOSE",
    "STRATEGY_CATCH_UP",
    "STRATEGY_IDS",
    "STRATEGY_TREND_CONTINUATION",
    "OpportunityQualificationDecision",
    "OpportunityQualificationPolicy",
    "apply_qualification_policy",
    "policy_for_strategy",
    "presentation_candidates",
    "qualification_stage",
    "qualify_opportunity",
]
