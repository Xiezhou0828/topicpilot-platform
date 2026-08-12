"""Shadow-only Opportunity decision, explanation, and read contracts.

TASK-BE-024A intentionally keeps this module provider-neutral and persistence-
neutral.  It turns the deterministic V1 strategy output into a stable contract
that a future API or frontend can consume, without publishing a production
recommendation or asking an LLM to make a decision.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import TYPE_CHECKING

from .opportunity_shadow import FAIL, PASS, UNKNOWN, Evidence

if TYPE_CHECKING:  # pragma: no cover - imports are for static type checkers only
    from .opportunity_strategies import OpportunityStrategyInput, OpportunityStrategyResult


NUMERIC_PARAMETER_STATUS = "PROVISIONAL_TUNABLE_VERSIONED"
RANKING_PROFILE_CONTRACT_VERSION = "opportunity-ranking-profile.v1.shadow"
DECISION_CONTRACT_VERSION = "opportunity-decision.v1.shadow"
EXPLANATION_CONTRACT_VERSION = "opportunity-explanation.v1.shadow"
READ_CONTRACT_VERSION = "opportunity-read.v1.shadow"
CALIBRATION_CONTRACT_VERSION = "opportunity-calibration.v1.placeholder"
CALIBRATION_DATA_SOURCE = "CANONICAL_PRODUCTION_DAILY_OHLCV"
CALIBRATION_SYNTHETIC_ALLOWED = False

DECISION_STATE_SELECTED = "SELECTED"
DECISION_STATE_WAITING_RETEST = "WAITING_RETEST"
DECISION_STATE_WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
DECISION_STATE_DEFERRED = "DEFERRED"
DECISION_STATE_EXCLUDED = "EXCLUDED"
DECISION_STATES = (
    DECISION_STATE_SELECTED,
    DECISION_STATE_WAITING_RETEST,
    DECISION_STATE_WAITING_CONFIRMATION,
    DECISION_STATE_DEFERRED,
    DECISION_STATE_EXCLUDED,
)

CALIBRATION_HORIZONS = ("forward_1d", "forward_3d", "forward_5d", "forward_10d")
CALIBRATION_METRICS = (
    "forward_return",
    "MFE",
    "MAE",
    "support_touch",
    "support_hold",
    "support_fail",
    "invalidation_hit",
    "invalidation_outcome",
    "threshold_hit_3pct",
    "threshold_hit_5pct",
    "threshold_hit_10pct",
)
CALIBRATION_PROVENANCE_FIELDS = (
    "lifecycle_at_selection",
    "topic_grade_at_selection",
    "opportunity_state_at_selection",
    "ranking_profile_version",
    "policy_version",
    "parameter_version",
)


def _finite(value: object) -> bool:
    try:
        return value is not None and not isinstance(value, bool) and isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


@dataclass(frozen=True)
class StrategyRankingProfile:
    """Strategy-local ranking weights.

    Values are calibration starting points only.  They are deliberately
    versioned and marked provisional; this contract does not claim that any
    weight is a PM-frozen investment rule.
    """

    profile_version: str
    strategy_id: str
    theme_quality_weight: float
    structure_weight: float
    relative_strength_weight: float
    volume_weight: float
    entry_quality_weight: float
    extension_context_weight: float
    relative_floor_pct: float = -20.0
    relative_ceiling_pct: float = 20.0
    numeric_parameter_status: str = NUMERIC_PARAMETER_STATUS

    def __post_init__(self) -> None:
        if not self.profile_version.strip() or not self.strategy_id.strip():
            raise ValueError("ranking profile identifiers must be non-empty")
        for name in (
            "theme_quality_weight",
            "structure_weight",
            "relative_strength_weight",
            "volume_weight",
            "entry_quality_weight",
            "extension_context_weight",
        ):
            value = getattr(self, name)
            if not _finite(value) or float(value) < 0:
                raise ValueError(f"{name} must be a finite non-negative number")
        if sum(
            float(getattr(self, name))
            for name in (
                "theme_quality_weight",
                "structure_weight",
                "relative_strength_weight",
                "volume_weight",
                "entry_quality_weight",
                "extension_context_weight",
            )
        ) <= 0:
            raise ValueError("ranking profile must have a positive total weight")
        if not _finite(self.relative_floor_pct) or not _finite(self.relative_ceiling_pct):
            raise ValueError("relative ranking bounds must be finite")
        if self.relative_floor_pct >= self.relative_ceiling_pct:
            raise ValueError("relative ranking floor must be below ceiling")
        if self.numeric_parameter_status != NUMERIC_PARAMETER_STATUS:
            raise ValueError("ranking parameters must remain provisional and versioned")

    @property
    def weights(self) -> tuple[float, ...]:
        return (
            self.theme_quality_weight,
            self.structure_weight,
            self.relative_strength_weight,
            self.volume_weight,
            self.entry_quality_weight,
            self.extension_context_weight,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "profileVersion": self.profile_version,
            "strategyId": self.strategy_id,
            "numericParameterStatus": self.numeric_parameter_status,
            "weights": {
                "themeQuality": self.theme_quality_weight,
                "structure": self.structure_weight,
                "relativeStrength": self.relative_strength_weight,
                "volume": self.volume_weight,
                "entryQuality": self.entry_quality_weight,
                "extensionContext": self.extension_context_weight,
            },
            "relativeBoundsPct": {
                "floor": self.relative_floor_pct,
                "ceiling": self.relative_ceiling_pct,
            },
        }


@dataclass(frozen=True)
class TrendContinuationRankingProfile(StrategyRankingProfile):
    """Default provisional profile for trend continuation."""

    profile_version: str = "trend-continuation-ranking.v1.provisional"
    strategy_id: str = "TREND_CONTINUATION"
    theme_quality_weight: float = 0.20
    structure_weight: float = 0.25
    relative_strength_weight: float = 0.25
    volume_weight: float = 0.15
    entry_quality_weight: float = 0.10
    extension_context_weight: float = 0.05


@dataclass(frozen=True)
class CatchUpRankingProfile(StrategyRankingProfile):
    """Default provisional profile for catch-up."""

    profile_version: str = "catch-up-ranking.v1.provisional"
    strategy_id: str = "CATCH_UP"
    theme_quality_weight: float = 0.20
    structure_weight: float = 0.20
    relative_strength_weight: float = 0.20
    volume_weight: float = 0.15
    entry_quality_weight: float = 0.15
    extension_context_weight: float = 0.10


@dataclass(frozen=True)
class DecisionReason:
    code: str
    status: str
    detail: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {"code": self.code, "status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class OpportunityDecision:
    """Deterministic state decision emitted after strategy evidence."""

    contract_version: str
    strategy_id: str
    eligibility: str
    status: str
    state: str
    reason_codes: tuple[str, ...]
    qualification_class: str = "NOT_QUALIFIED"

    def __post_init__(self) -> None:
        if self.contract_version != DECISION_CONTRACT_VERSION:
            raise ValueError("unsupported opportunity decision contract")
        if self.state not in DECISION_STATES:
            raise ValueError(f"unknown opportunity state: {self.state}")
        if self.qualification_class not in {
            "FORMAL_OPPORTUNITY",
            "EXCEPTION_CANDIDATE",
            "NOT_QUALIFIED",
        }:
            raise ValueError("unknown qualification class")

    def as_dict(self) -> dict[str, object]:
        return {
            "contractVersion": self.contract_version,
            "strategyId": self.strategy_id,
            "eligibility": self.eligibility,
            "status": self.status,
            "state": self.state,
            "reasonCodes": list(self.reason_codes),
            "qualificationClass": self.qualification_class,
        }


@dataclass(frozen=True)
class ExplainabilityFactor:
    """Structured, deterministic evidence suitable for frontend display."""

    code: str
    category: str
    status: str
    value: object | None = None
    benchmark: object | None = None
    source: str = "strategy_evidence"
    evidence_status: str = "STRUCTURED"

    def as_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "displayKey": self.code,
            "category": self.category,
            "status": self.status,
            "value": self.value,
            "benchmark": self.benchmark,
            "source": self.source,
            "evidenceStatus": self.evidence_status,
        }


@dataclass(frozen=True)
class OpportunityExplanation:
    contract_version: str
    strategy: str
    state: str
    summary_code: str
    positive_factors: tuple[ExplainabilityFactor, ...] = ()
    waiting_factors: tuple[ExplainabilityFactor, ...] = ()
    risk_factors: tuple[ExplainabilityFactor, ...] = ()
    exclusion_factors: tuple[ExplainabilityFactor, ...] = ()
    entry_context: tuple[ExplainabilityFactor, ...] = ()
    invalidation_context: tuple[ExplainabilityFactor, ...] = ()
    data_quality: tuple[ExplainabilityFactor, ...] = ()
    confidence_basis: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.contract_version != EXPLANATION_CONTRACT_VERSION:
            raise ValueError("unsupported explanation contract")
        if self.state not in DECISION_STATES:
            raise ValueError("explanation state must be a decision state")

    def as_dict(self) -> dict[str, object]:
        factor_groups = {
            "positiveFactors": self.positive_factors,
            "waitingFactors": self.waiting_factors,
            "riskFactors": self.risk_factors,
            "exclusionFactors": self.exclusion_factors,
            "entryContext": self.entry_context,
            "invalidationContext": self.invalidation_context,
            "dataQuality": self.data_quality,
        }
        payload: dict[str, object] = {
            "contractVersion": self.contract_version,
            "strategy": self.strategy,
            "state": self.state,
            "summaryCode": self.summary_code,
            "confidenceBasis": list(self.confidence_basis),
        }
        payload.update(
            {key: [item.as_dict() for item in values] for key, values in factor_groups.items()}
        )
        return payload


@dataclass(frozen=True)
class OpportunityReadModel:
    """Canonical provider-neutral projection for a future read surface."""

    contract_version: str
    strategy_id: str
    strategy_type: str
    instrument_id: str
    symbol: str
    instrument_name: str
    topic_id: str
    topic_name: str
    as_of: date | None
    opportunity_state: str
    eligibility: str
    status: str
    rank_score: float | None
    ranking_status: str
    confidence: str | None
    confidence_basis: tuple[str, ...]
    entry_context: tuple[ExplainabilityFactor, ...]
    support_context: tuple[ExplainabilityFactor, ...]
    risk_context: tuple[ExplainabilityFactor, ...]
    exclusion_codes: tuple[str, ...]
    explanation: OpportunityExplanation
    policy_version: str
    publication_status: str
    data_status: str
    topic_grade: str | None
    topic_lifecycle: str | None
    topic_strength: float | None
    qualification_status: str = "NOT_EVALUATED"
    qualification_reason_codes: tuple[str, ...] = ()
    qualification_exception: bool = False
    qualification_policy_version: str | None = None
    qualification_parameter_version: str | None = None
    qualification_class: str = "NOT_QUALIFIED"

    def __post_init__(self) -> None:
        if self.contract_version != READ_CONTRACT_VERSION:
            raise ValueError("unsupported opportunity read contract")
        if self.opportunity_state not in DECISION_STATES:
            raise ValueError("read model must use a decision state")
        if self.rank_score is not None and not _finite(self.rank_score):
            raise ValueError("rank score must be finite or null")
        if self.publication_status != "SHADOW_ONLY":
            raise ValueError("read model cannot be published in TASK-BE-024A")
        if self.qualification_class not in {
            "FORMAL_OPPORTUNITY",
            "EXCEPTION_CANDIDATE",
            "NOT_QUALIFIED",
        }:
            raise ValueError("unknown qualification class")

    def as_dict(self) -> dict[str, object]:
        return {
            "contractVersion": self.contract_version,
            "strategyId": self.strategy_id,
            "strategyType": self.strategy_type,
            "instrument": {
                "id": self.instrument_id,
                "symbol": self.symbol,
                "name": self.instrument_name,
            },
            "topic": {"id": self.topic_id, "name": self.topic_name},
            "asOf": self.as_of.isoformat() if self.as_of else None,
            "opportunityState": self.opportunity_state,
            "eligibility": self.eligibility,
            "status": self.status,
            "rankScore": self.rank_score,
            "rankingStatus": self.ranking_status,
            "confidence": self.confidence,
            "confidenceBasis": list(self.confidence_basis),
            "entryContext": [item.as_dict() for item in self.entry_context],
            "supportContext": [item.as_dict() for item in self.support_context],
            "riskContext": [item.as_dict() for item in self.risk_context],
            "exclusionCodes": list(self.exclusion_codes),
            "explanation": self.explanation.as_dict(),
            "policyVersion": self.policy_version,
            "publicationStatus": self.publication_status,
            "dataStatus": self.data_status,
            "upstreamTopic": {
                "grade": self.topic_grade,
                "lifecycle": self.topic_lifecycle,
                "strength": self.topic_strength,
            },
            "qualification": {
                "class": self.qualification_class,
                "status": self.qualification_status,
                "reasonCodes": list(self.qualification_reason_codes),
                "exceptionCandidate": self.qualification_exception,
                "policyVersion": self.qualification_policy_version,
                "parameterVersion": self.qualification_parameter_version,
            },
        }


@dataclass(frozen=True)
class CalibrationObservationPlaceholder:
    """Schema-only placeholder; it deliberately contains no outcome values."""

    strategy_id: str
    instrument_id: str
    evaluation_date: date
    status: str = "NOT_IMPLEMENTED"
    metrics: tuple[tuple[str, object | None], ...] = ()
    lifecycle_at_selection: str | None = None
    topic_grade_at_selection: str | None = None
    opportunity_state_at_selection: str | None = None
    ranking_profile_version: str | None = None
    policy_version: str | None = None
    parameter_version: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "strategyId": self.strategy_id,
            "instrumentId": self.instrument_id,
            "evaluationDate": self.evaluation_date.isoformat(),
            "status": self.status,
            "metrics": {key: value for key, value in self.metrics},
            "selectionProvenance": {
                "lifecycleAtSelection": self.lifecycle_at_selection,
                "topicGradeAtSelection": self.topic_grade_at_selection,
                "opportunityStateAtSelection": self.opportunity_state_at_selection,
                "rankingProfileVersion": self.ranking_profile_version,
                "policyVersion": self.policy_version,
                "parameterVersion": self.parameter_version,
            },
        }


@dataclass(frozen=True)
class OpportunityCalibrationContract:
    contract_version: str = CALIBRATION_CONTRACT_VERSION
    status: str = "PLACEHOLDER_NOT_IMPLEMENTED"
    horizons: tuple[str, ...] = CALIBRATION_HORIZONS
    metrics: tuple[str, ...] = CALIBRATION_METRICS
    provenance_fields: tuple[str, ...] = CALIBRATION_PROVENANCE_FIELDS
    observations: tuple[CalibrationObservationPlaceholder, ...] = ()

    def __post_init__(self) -> None:
        if self.contract_version != CALIBRATION_CONTRACT_VERSION:
            raise ValueError("unsupported calibration contract")

    def as_dict(self) -> dict[str, object]:
        return {
            "contractVersion": self.contract_version,
            "status": self.status,
            "horizons": list(self.horizons),
            "metrics": list(self.metrics),
            "provenanceFields": list(self.provenance_fields),
            "observations": [item.as_dict() for item in self.observations],
            "dataContract": {
                "requiredSource": CALIBRATION_DATA_SOURCE,
                "syntheticAllowed": CALIBRATION_SYNTHETIC_ALLOWED,
                "lookAhead": False,
            },
            "evaluationImplemented": False,
        }


def decide_opportunity(
    result: OpportunityStrategyResult,
    *,
    waiting_confirmation_codes: Sequence[str] = (
        "VOLUME_ACTIVATION_BELOW_POLICY",
        "VOLUME_CONFIRMATION_WEAK",
    ),
) -> OpportunityDecision:
    """Map engine status/stages to deterministic user-facing state."""

    qualification_status = getattr(result, "qualification_status", "NOT_EVALUATED")
    if qualification_status == "EXCLUDED" or result.status in {
        "EXCLUDED",
        "FUTURE_NOT_IMPLEMENTED",
    }:
        state = DECISION_STATE_EXCLUDED
    elif qualification_status == "DEFERRED" or result.status == "DEFERRED":
        state = DECISION_STATE_DEFERRED
    elif qualification_status == "WAITING_CONFIRMATION":
        state = DECISION_STATE_WAITING_CONFIRMATION
    else:
        entry_status = next(
            (stage.assessment.status for stage in result.stages if stage.name == "ENTRY_QUALITY"),
            None,
        )
        entry_codes = next(
            (
                stage.assessment.reason_codes
                for stage in result.stages
                if stage.name == "ENTRY_QUALITY"
            ),
            (),
        )
        if entry_status == "WAIT" or any(
            code in {"ENTRY_WAIT_FOR_RETEST_OR_BETTER_POSITION", "ENTRY_TOO_FAR_FROM_SUPPORT"}
            for code in entry_codes
        ):
            state = DECISION_STATE_WAITING_RETEST
        elif any(code in waiting_confirmation_codes for code in result.exclusion_codes):
            state = DECISION_STATE_WAITING_CONFIRMATION
        else:
            state = DECISION_STATE_SELECTED
    reasons = tuple(result.exclusion_codes)
    return OpportunityDecision(
        DECISION_CONTRACT_VERSION,
        result.strategy_id,
        result.eligibility,
        result.status,
        state,
        reasons,
        getattr(result, "qualification_class", "NOT_QUALIFIED"),
    )


def _factor_from_evidence(
    evidence: Evidence, *, category: str, status: str
) -> ExplainabilityFactor:
    return ExplainabilityFactor(
        code=evidence.code,
        category=category,
        status=status,
        value=evidence.value,
        source=evidence.source,
    )


def build_opportunity_explanation(
    result: OpportunityStrategyResult, decision: OpportunityDecision | None = None
) -> OpportunityExplanation:
    """Create deterministic factor groups from strategy stages and evidence."""

    decision = decision or decide_opportunity(result)
    positive: list[ExplainabilityFactor] = []
    waiting: list[ExplainabilityFactor] = []
    risks: list[ExplainabilityFactor] = []
    exclusions: list[ExplainabilityFactor] = []
    entry: list[ExplainabilityFactor] = []
    invalidation: list[ExplainabilityFactor] = []
    data_quality: list[ExplainabilityFactor] = []
    for stage in result.stages:
        category = stage.name.lower()
        for evidence in stage.assessment.evidence:
            factor = _factor_from_evidence(
                evidence, category=category, status=stage.assessment.status
            )
            code = evidence.code.upper()
            if stage.name in {"DATA_QUALITY", "THEME_CONTEXT"} or code.startswith(
                ("DATA_", "TOPIC_", "MEMBERSHIP", "LIQUIDITY")
            ):
                data_quality.append(factor)
            if stage.name == "ENTRY_QUALITY" or code.startswith(("ENTRY_", "SUPPORT", "PRICE_TO_")):
                entry.append(factor)
            if stage.name in {"EXCLUSION", "RISK_GATE"} or code.startswith(
                ("STRUCTURAL_", "FORMAL_NO_TRADE", "PRICE_NOT_")
            ):
                invalidation.append(factor)
            if stage.assessment.status == PASS:
                positive.append(factor)
            elif stage.assessment.status == UNKNOWN:
                waiting.append(factor)
            elif stage.assessment.status == FAIL:
                risks.append(factor)
                exclusions.append(factor)
    if decision.state == DECISION_STATE_WAITING_RETEST:
        waiting.extend(entry)
    if decision.state == DECISION_STATE_WAITING_CONFIRMATION:
        waiting.extend(risks)
    if decision.state in {DECISION_STATE_EXCLUDED, DECISION_STATE_DEFERRED}:
        exclusions.extend(risks)
    summary_code = {
        DECISION_STATE_SELECTED: "OPPORTUNITY_SELECTED",
        DECISION_STATE_WAITING_RETEST: "OPPORTUNITY_WAITING_RETEST",
        DECISION_STATE_WAITING_CONFIRMATION: "OPPORTUNITY_WAITING_CONFIRMATION",
        DECISION_STATE_DEFERRED: "OPPORTUNITY_DEFERRED_DATA_INCOMPLETE",
        DECISION_STATE_EXCLUDED: "OPPORTUNITY_EXCLUDED_BY_GATE",
    }[decision.state]
    return OpportunityExplanation(
        EXPLANATION_CONTRACT_VERSION,
        result.strategy_id,
        decision.state,
        summary_code,
        tuple(positive),
        tuple(waiting),
        tuple(risks),
        tuple(exclusions),
        tuple(entry),
        tuple(invalidation),
        tuple(data_quality),
        tuple(result.confidence_basis),
    )


def project_opportunity_read_model(
    result: OpportunityStrategyResult,
    value: OpportunityStrategyInput,
    *,
    decision: OpportunityDecision | None = None,
) -> OpportunityReadModel:
    """Project a strategy result without tying it to a provider or database."""

    if getattr(result, "qualification_status", "NOT_EVALUATED") == "NOT_EVALUATED":
        from .opportunity_qualification import apply_qualification_policy

        result = apply_qualification_policy(result, value)
        decision = None
    decision = decision or decide_opportunity(result)
    explanation = build_opportunity_explanation(result, decision)
    unknown_stages = sum(stage.assessment.status == UNKNOWN for stage in result.stages)
    data_status = "COMPLETE" if unknown_stages == 0 else "PARTIAL"
    return OpportunityReadModel(
        READ_CONTRACT_VERSION,
        result.strategy_id,
        result.strategy_type,
        value.stock.instrument_id,
        value.stock.symbol,
        value.stock.name,
        value.theme.topic_id,
        value.theme.topic_name,
        result.as_of,
        decision.state,
        result.eligibility,
        result.status,
        result.rank_score,
        result.ranking_status,
        result.confidence,
        result.confidence_basis,
        explanation.entry_context,
        tuple(
            item
            for item in explanation.entry_context
            if item.category.startswith("support")
            or item.code.startswith(("SUPPORT", "PRIMARY_SUPPORT"))
        ),
            explanation.invalidation_context + explanation.risk_factors,
            result.exclusion_codes,
            explanation,
        result.policy_version,
        result.publication_status,
        data_status,
        value.theme.grade,
        value.theme.lifecycle,
        value.theme.topic_strength,
        getattr(result, "qualification_status", "NOT_EVALUATED"),
        getattr(result, "qualification_reason_codes", ()),
        getattr(result, "qualification_exception", False),
        getattr(result, "qualification_policy_version", None),
        getattr(result, "qualification_parameter_version", None),
        getattr(result, "qualification_class", "NOT_QUALIFIED"),
    )


def build_calibration_contract() -> OpportunityCalibrationContract:
    """Return the schema placeholder; no forward outcome evaluation is run."""

    return OpportunityCalibrationContract()


def _fixture_factor(
    code: str, category: str, status: str = PASS, value: object | None = None
) -> ExplainabilityFactor:
    return ExplainabilityFactor(code, category, status, value, None, "fixture", "STRUCTURED")


def build_frontend_opportunity_fixtures() -> tuple[OpportunityReadModel, ...]:
    """Deterministic payload examples for future frontend contract tests."""

    definitions = (
        ("TREND_CONTINUATION", "TREND_SELECTED", DECISION_STATE_SELECTED, "COMPLETE"),
        ("TREND_CONTINUATION", "TREND_WAITING_RETEST", DECISION_STATE_WAITING_RETEST, "COMPLETE"),
        ("CATCH_UP", "CATCHUP_SELECTED", DECISION_STATE_SELECTED, "COMPLETE"),
        (
            "CATCH_UP",
            "CATCHUP_WAITING_CONFIRMATION",
            DECISION_STATE_WAITING_CONFIRMATION,
            "COMPLETE",
        ),
        ("TREND_CONTINUATION", "TREND_EXCLUDED", DECISION_STATE_EXCLUDED, "COMPLETE"),
        ("CATCH_UP", "CATCHUP_DEFERRED", DECISION_STATE_DEFERRED, "PARTIAL"),
    )
    fixtures: list[OpportunityReadModel] = []
    for index, (strategy, code, state, data_status) in enumerate(definitions, start=1):
        factor_status = (
            FAIL
            if state == DECISION_STATE_EXCLUDED
            else UNKNOWN
            if state == DECISION_STATE_DEFERRED
            else PASS
        )
        factor = _fixture_factor(code, "fixture", factor_status, index)
        explanation = OpportunityExplanation(
            EXPLANATION_CONTRACT_VERSION,
            strategy,
            state,
            code,
            (factor,) if state == DECISION_STATE_SELECTED else (),
            (
                (factor,)
                if state
                in {
                    DECISION_STATE_WAITING_RETEST,
                    DECISION_STATE_WAITING_CONFIRMATION,
                    DECISION_STATE_DEFERRED,
                }
                else ()
            ),
            (factor,) if state == DECISION_STATE_EXCLUDED else (),
            (factor,) if state == DECISION_STATE_EXCLUDED else (),
            (factor,),
            (factor,) if state in {DECISION_STATE_EXCLUDED, DECISION_STATE_WAITING_RETEST} else (),
            (factor,),
            ("fixture_structured_evidence",),
        )
        fixtures.append(
            OpportunityReadModel(
                READ_CONTRACT_VERSION,
                strategy,
                strategy,
                f"fixture-{index}",
                f"FP{index:02d}",
                f"Fixture {index}",
                "topic-fixture",
                "Fixture Topic",
                date(2026, 8, 12),
                state,
                (
                    PASS
                    if state not in {DECISION_STATE_EXCLUDED, DECISION_STATE_DEFERRED}
                    else UNKNOWN
                ),
                (
                    "CANDIDATE"
                    if state not in {DECISION_STATE_EXCLUDED, DECISION_STATE_DEFERRED}
                    else state
                ),
                (
                    70.0 - index
                    if state not in {DECISION_STATE_EXCLUDED, DECISION_STATE_DEFERRED}
                    else None
                ),
                (
                    "AVAILABLE"
                    if state not in {DECISION_STATE_EXCLUDED, DECISION_STATE_DEFERRED}
                    else "UNAVAILABLE"
                ),
                "HIGH" if state == DECISION_STATE_SELECTED else "MEDIUM",
                ("fixture_structured_evidence",),
                explanation.entry_context,
                explanation.entry_context,
                explanation.risk_factors,
                (code,) if state == DECISION_STATE_EXCLUDED else (),
                explanation,
                "topic-opportunity-policy.provisional.1",
                "SHADOW_ONLY",
                data_status,
                "A",
                "FERMENTING",
                70.0,
            )
        )
    return tuple(fixtures)


def validate_frontend_opportunity_fixtures(
    fixtures: Sequence[OpportunityReadModel] | None = None,
) -> tuple[str, ...]:
    fixtures = tuple(fixtures or build_frontend_opportunity_fixtures())
    states = tuple(item.opportunity_state for item in fixtures)
    missing = tuple(state for state in DECISION_STATES if state not in states)
    if missing:
        raise ValueError(f"frontend fixtures missing states: {missing}")
    banned = ("BUY", "SELL", "STRONGBUY", "AI_CONFIDENCE", "TARGET", "STOP_LOSS")
    for item in fixtures:
        payload = str(item.as_dict()).upper().replace(" ", "")
        if any(token in payload for token in banned):
            raise ValueError("frontend fixture contains a prohibited recommendation term")
    return states


# Explicit aliases keep the contract vocabulary discoverable for adapters and
# future work orders without duplicating any runtime schema.
OpportunityDecisionContract = OpportunityDecision
OpportunityReadContract = OpportunityReadModel


__all__ = [
    "CALIBRATION_CONTRACT_VERSION",
    "CALIBRATION_HORIZONS",
    "CALIBRATION_METRICS",
    "CALIBRATION_PROVENANCE_FIELDS",
    "DECISION_CONTRACT_VERSION",
    "DECISION_STATES",
    "DECISION_STATE_DEFERRED",
    "DECISION_STATE_EXCLUDED",
    "DECISION_STATE_SELECTED",
    "DECISION_STATE_WAITING_CONFIRMATION",
    "DECISION_STATE_WAITING_RETEST",
    "EXPLANATION_CONTRACT_VERSION",
    "NUMERIC_PARAMETER_STATUS",
    "RANKING_PROFILE_CONTRACT_VERSION",
    "READ_CONTRACT_VERSION",
    "CalibrationObservationPlaceholder",
    "CatchUpRankingProfile",
    "ExplainabilityFactor",
    "OpportunityCalibrationContract",
    "OpportunityDecision",
    "OpportunityDecisionContract",
    "OpportunityExplanation",
    "OpportunityReadContract",
    "OpportunityReadModel",
    "StrategyRankingProfile",
    "TrendContinuationRankingProfile",
    "build_calibration_contract",
    "build_frontend_opportunity_fixtures",
    "build_opportunity_explanation",
    "decide_opportunity",
    "project_opportunity_read_model",
    "validate_frontend_opportunity_fixtures",
]
