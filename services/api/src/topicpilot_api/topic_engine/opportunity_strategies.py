"""Shadow-only V1 Opportunity strategies.

This module adds the first strategy layer above the canonical technical
evidence builders.  It deliberately does not publish a recommendation, write
to PostgreSQL, expose an API, or change the existing Recommendation read
model.  Trend Continuation and Catch-up are evaluated independently; future
strategies return an explicit ``FUTURE_NOT_IMPLEMENTED`` result.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date
from math import isfinite
from typing import Protocol

from .opportunity_contract import (
    CatchUpRankingProfile,
    StrategyRankingProfile,
    TrendContinuationRankingProfile,
)
from .opportunity_evidence import (
    CanonicalOHLCVBar,
    EntryQualityFacts,
    OpportunityEvidencePolicy,
    TechnicalEvidenceBundle,
    build_entry_quality,
    build_technical_evidence,
)
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

OPPORTUNITY_ENGINE_CONTRACT_VERSION = "opportunity-engine.v1.shadow"
OPPORTUNITY_POLICY_VERSION = "topic-opportunity-policy.provisional.1"
POLICY_STATUS_PROVISIONAL = "PROVISIONAL"
QUALIFICATION_FORMAL = "FORMAL_OPPORTUNITY"
QUALIFICATION_EXCEPTION = "EXCEPTION_CANDIDATE"
QUALIFICATION_NONE = "NOT_QUALIFIED"
FORMAL_TOPIC_GRADES = frozenset({"S", "A"})
EXCEPTION_TOPIC_GRADES = frozenset({"B"})
HARD_EXCLUDED_TOPIC_GRADES = frozenset({"D"})
RANKING_CADENCE_POST_CLOSE = "POST_CLOSE"
INTRADAY_BEHAVIOR_STATUS_ONLY = "STATUS_ONLY"
PRESENTATION_CAP_TREND = 3
PRESENTATION_CAP_CATCH_UP = 2
STRATEGY_TREND_CONTINUATION = "TREND_CONTINUATION"
STRATEGY_CATCH_UP = "CATCH_UP"
STRATEGY_EARLY_STRENGTH = "EARLY_STRENGTH"
STRATEGY_PULLBACK_ACCEPTANCE = "PULLBACK_ACCEPTANCE"
V1_STRATEGIES = (STRATEGY_TREND_CONTINUATION, STRATEGY_CATCH_UP)
FUTURE_STRATEGIES = (STRATEGY_EARLY_STRENGTH, STRATEGY_PULLBACK_ACCEPTANCE)
LIFECYCLE_STRATEGY_MATRIX: dict[str, dict[str, str]] = {
    "SPROUTING": {
        STRATEGY_TREND_CONTINUATION: "WAITING_CONFIRMATION",
        STRATEGY_CATCH_UP: "WAITING_CONFIRMATION",
    },
    "FERMENTING": {
        STRATEGY_TREND_CONTINUATION: "HIGH_FIT",
        STRATEGY_CATCH_UP: "MEDIUM_HIGH_FIT",
    },
    "MAIN_RISE": {
        STRATEGY_TREND_CONTINUATION: "HIGH_FIT",
        STRATEGY_CATCH_UP: "HIGH_FIT",
    },
    "MATURE": {
        STRATEGY_TREND_CONTINUATION: "LOW_FIT",
        STRATEGY_CATCH_UP: "RETAIN_STRICTER_GATES",
    },
    "DECLINING": {
        STRATEGY_TREND_CONTINUATION: "HARD_EXCLUDE",
        STRATEGY_CATCH_UP: "HARD_EXCLUDE",
    },
}

RESULT_CANDIDATE = "CANDIDATE"
RESULT_EXCLUDED = "EXCLUDED"
RESULT_DEFERRED = "DEFERRED"
RESULT_FUTURE = "FUTURE_NOT_IMPLEMENTED"

RANKING_STATUS_AVAILABLE = "AVAILABLE"
RANKING_STATUS_UNAVAILABLE = "UNAVAILABLE"
CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW = "LOW"

# Decision-contract states are intentionally distinct from the legacy shadow
# composer states imported above.  The old states remain available for history
# and compatibility; strategy results use these stable uppercase values.
DECISION_STATE_SELECTED = "SELECTED"
DECISION_STATE_WAITING_RETEST = "WAITING_RETEST"
DECISION_STATE_WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
DECISION_STATE_DEFERRED = "DEFERRED"
DECISION_STATE_EXCLUDED = "EXCLUDED"


@dataclass(frozen=True)
class OpportunityPolicy:
    """Versioned V1 strategy policy.

    Defaults are calibration starting points only.  They are centralized here
    and are not presented as PM-frozen production thresholds.
    """

    policy_version: str = OPPORTUNITY_POLICY_VERSION
    policy_status: str = POLICY_STATUS_PROVISIONAL
    technical_policy: OpportunityEvidencePolicy = field(default_factory=OpportunityEvidencePolicy)
    trend_allowed_grades: frozenset[str] = FORMAL_TOPIC_GRADES
    catch_up_allowed_grades: frozenset[str] = FORMAL_TOPIC_GRADES
    exception_grades: frozenset[str] = EXCEPTION_TOPIC_GRADES
    hard_excluded_grades: frozenset[str] = HARD_EXCLUDED_TOPIC_GRADES
    trend_allowed_lifecycles: frozenset[str] = frozenset(
        {"SPROUTING", "FERMENTING", "MAIN_RISE", "MATURE"}
    )
    catch_up_allowed_lifecycles: frozenset[str] = frozenset(
        {"SPROUTING", "FERMENTING", "MAIN_RISE", "MATURE"}
    )
    trend_relative_window: int = 20
    trend_relative_min_pct: float = 0.0
    catch_up_relative_window: int = 20
    catch_up_lag_min_pct: float = -12.0
    catch_up_lag_max_pct: float = -2.0
    catch_up_inflection_lookback: int = 3
    catch_up_inflection_min_change_pct: float = 0.0
    trend_recent_return_window: int = 5
    trend_extension_distance_pct: float = 8.0
    catch_up_extension_distance_pct: float = 8.0
    volume_activation_ratio: float = 1.20
    sprouting_rank_multiplier: float = 0.50
    trend_mature_rank_multiplier: float = 0.75
    catch_up_mature_rank_multiplier: float = 0.85
    rank_weight_theme: float = 1.0
    rank_weight_structure: float = 1.0
    rank_weight_relative_strength: float = 1.0
    rank_weight_volume: float = 1.0
    rank_weight_entry: float = 1.0
    rank_relative_floor_pct: float = -20.0
    rank_relative_ceiling_pct: float = 20.0
    trend_ranking_profile: TrendContinuationRankingProfile = field(
        default_factory=TrendContinuationRankingProfile
    )
    catch_up_ranking_profile: CatchUpRankingProfile = field(default_factory=CatchUpRankingProfile)
    ranking_cadence: str = RANKING_CADENCE_POST_CLOSE
    intraday_behavior: str = INTRADAY_BEHAVIOR_STATUS_ONLY
    presentation_cap_trend: int = PRESENTATION_CAP_TREND
    presentation_cap_catch_up: int = PRESENTATION_CAP_CATCH_UP

    def __post_init__(self) -> None:
        if self.policy_status != POLICY_STATUS_PROVISIONAL:
            raise ValueError("OpportunityPolicy must remain PROVISIONAL")
        if self.trend_allowed_grades != FORMAL_TOPIC_GRADES:
            raise ValueError("Trend formal grades must remain S/A")
        if self.catch_up_allowed_grades != FORMAL_TOPIC_GRADES:
            raise ValueError("Catch-up formal grades must remain S/A")
        if self.exception_grades != EXCEPTION_TOPIC_GRADES:
            raise ValueError("B is the only qualification exception grade")
        if self.hard_excluded_grades != HARD_EXCLUDED_TOPIC_GRADES:
            raise ValueError("D must remain hard excluded")
        if self.ranking_cadence != RANKING_CADENCE_POST_CLOSE:
            raise ValueError("V1 ranking cadence must remain POST_CLOSE")
        if self.intraday_behavior != INTRADAY_BEHAVIOR_STATUS_ONLY:
            raise ValueError("V1 intraday behavior must remain STATUS_ONLY")
        for name in ("presentation_cap_trend", "presentation_cap_catch_up"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        positive_ints = (
            "trend_relative_window",
            "catch_up_relative_window",
            "catch_up_inflection_lookback",
            "trend_recent_return_window",
        )
        for name in positive_ints:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        nonnegative = (
            "trend_relative_min_pct",
            "catch_up_inflection_min_change_pct",
            "trend_extension_distance_pct",
            "catch_up_extension_distance_pct",
            "volume_activation_ratio",
            "sprouting_rank_multiplier",
            "trend_mature_rank_multiplier",
            "catch_up_mature_rank_multiplier",
            "rank_weight_theme",
            "rank_weight_structure",
            "rank_weight_relative_strength",
            "rank_weight_volume",
            "rank_weight_entry",
        )
        for name in nonnegative:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be numeric")
            if float(value) < 0:
                raise ValueError(f"{name} must be non-negative")
        for name in ("rank_relative_floor_pct", "rank_relative_ceiling_pct"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(float(value))
            ):
                raise ValueError(f"{name} must be numeric")
        if self.catch_up_lag_min_pct > self.catch_up_lag_max_pct:
            raise ValueError("catch_up_lag_min_pct must not exceed lag_max")
        if self.rank_relative_floor_pct >= self.rank_relative_ceiling_pct:
            raise ValueError("rank relative floor must be below ceiling")
        if any(
            not isinstance(item, str) or not item.strip()
            for item in (
                *self.trend_allowed_grades,
                *self.catch_up_allowed_grades,
                *self.trend_allowed_lifecycles,
                *self.catch_up_allowed_lifecycles,
            )
        ):
            raise ValueError("grade and lifecycle policy values must be text")

    def as_dict(self) -> dict[str, object]:
        return {
            "policyVersion": self.policy_version,
            "policyStatus": self.policy_status,
            "numericParameterStatus": "PROVISIONAL_TUNABLE",
            "trendAllowedGrades": sorted(self.trend_allowed_grades),
            "catchUpAllowedGrades": sorted(self.catch_up_allowed_grades),
            "exceptionGrades": sorted(self.exception_grades),
            "hardExcludedGrades": sorted(self.hard_excluded_grades),
            "trendAllowedLifecycles": sorted(self.trend_allowed_lifecycles),
            "catchUpAllowedLifecycles": sorted(self.catch_up_allowed_lifecycles),
            "trendRelativeWindow": self.trend_relative_window,
            "trendRelativeMinPct": self.trend_relative_min_pct,
            "catchUpRelativeWindow": self.catch_up_relative_window,
            "catchUpLagMinPct": self.catch_up_lag_min_pct,
            "catchUpLagMaxPct": self.catch_up_lag_max_pct,
            "catchUpInflectionLookback": self.catch_up_inflection_lookback,
            "catchUpInflectionMinChangePct": self.catch_up_inflection_min_change_pct,
            "trendRecentReturnWindow": self.trend_recent_return_window,
            "trendExtensionDistancePct": self.trend_extension_distance_pct,
            "catchUpExtensionDistancePct": self.catch_up_extension_distance_pct,
            "volumeActivationRatio": self.volume_activation_ratio,
            "lifecycleRankMultipliers": {
                "SPROUTING": self.sprouting_rank_multiplier,
                "MATURE_TREND": self.trend_mature_rank_multiplier,
                "MATURE_CATCH_UP": self.catch_up_mature_rank_multiplier,
            },
            "minimumHistoryObservations": self.technical_policy.min_ohlcv_observations,
            "rankRelativeFloorPct": self.rank_relative_floor_pct,
            "rankRelativeCeilingPct": self.rank_relative_ceiling_pct,
            "gates": {
                "themeGrade": "policy-driven",
                "themeLifecycle": "policy-driven",
                "priceTrendStructure": "policy-driven",
                "riskExclusion": "policy-driven",
            },
            "penalties": {
                "extension": "evidence/ranking context",
                "volatility": "evidence/ranking context",
                "weakVolume": "evidence/ranking context",
            },
            "confidenceRequirement": "evidence coverage; not probability",
            "rankingWeights": {
                "theme": self.rank_weight_theme,
                "structure": self.rank_weight_structure,
                "relativeStrength": self.rank_weight_relative_strength,
                "volume": self.rank_weight_volume,
                "entry": self.rank_weight_entry,
            },
            "rankingProfiles": {
                "trendContinuation": self.trend_ranking_profile.as_dict(),
                "catchUp": self.catch_up_ranking_profile.as_dict(),
            },
            "technicalPolicy": self.technical_policy.as_dict(),
            "qualificationSemantics": {
                "formalGrades": ["S", "A"],
                "exceptionGrades": ["B"],
                "hardExcludedGrades": ["D"],
                "twentyMa": "CLOSE_GE_20MA_HARD_GATE",
                "sixtyMa": "STRUCTURE_AND_RANKING_FACTOR_NOT_HARD_GATE",
                "riskBeforeRanking": True,
                "lifecycleMatrixVersion": "opportunity-qualification-policy.v1",
            },
            "cadence": {
                "ranking": self.ranking_cadence,
                "intraday": self.intraday_behavior,
            },
            "presentationCaps": {
                STRATEGY_TREND_CONTINUATION: self.presentation_cap_trend,
                STRATEGY_CATCH_UP: self.presentation_cap_catch_up,
            },
        }


@dataclass(frozen=True)
class ThemeContext:
    """Explicit upstream topic context; this layer never recalculates it."""

    topic_id: str
    topic_name: str
    grade: str | None
    lifecycle: str | None
    topic_strength: float | None
    strength_evidence: tuple[Evidence, ...] = ()
    snapshot_date: date | None = None
    stock_returns_pct: Mapping[int, float | None] | None = None
    no_trade: bool | None = None
    topic_snapshot: Mapping[str, object] | None = None
    topic_returns_pct: Mapping[int, float | None] | None = None
    warming_candidate: bool | None = None
    warming_evidence: tuple[Evidence, ...] = ()
    exception_provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("topic_id", "topic_name"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be a trimmed non-empty string")
        if self.grade is not None and (not isinstance(self.grade, str) or not self.grade.strip()):
            raise ValueError("grade must be text or null")
        if self.lifecycle is not None and (
            not isinstance(self.lifecycle, str) or not self.lifecycle.strip()
        ):
            raise ValueError("lifecycle must be text or null")
        if self.topic_strength is not None and not _finite(self.topic_strength):
            raise ValueError("topic_strength must be finite or null")
        if self.no_trade not in (True, False, None):
            raise ValueError("no_trade must be true, false, or null")
        if self.warming_candidate not in (True, False, None):
            raise ValueError("warming_candidate must be true, false, or null")
        if any(not isinstance(item, Evidence) for item in self.warming_evidence):
            raise ValueError("warming_evidence must contain Evidence values")
        if any(not isinstance(item, str) or not item.strip() for item in self.exception_provenance):
            raise ValueError("exception_provenance must contain non-empty text")
        if self.stock_returns_pct is not None:
            for window, value in self.stock_returns_pct.items():
                if not isinstance(window, int) or window <= 0:
                    raise ValueError("theme return windows must be positive integers")
                if value is not None and not _finite(value):
                    raise ValueError("theme returns must be finite or null")
        if (
            self.topic_returns_pct is not None
            and self.stock_returns_pct is not None
            and dict(self.topic_returns_pct) != dict(self.stock_returns_pct)
        ):
            raise ValueError("stock_returns_pct and topic_returns_pct aliases disagree")
        if self.topic_returns_pct is not None:
            for window, value in self.topic_returns_pct.items():
                if not isinstance(window, int) or window <= 0:
                    raise ValueError("topic return windows must be positive integers")
                if value is not None and not _finite(value):
                    raise ValueError("topic returns must be finite or null")


@dataclass(frozen=True)
class StrategyStockContext:
    """Stock identity and data quality facts supplied to a strategy."""

    instrument_id: str
    symbol: str
    name: str
    topic_id: str
    bars: tuple[CanonicalOHLCVBar, ...]
    liquidity_available: bool | None = True
    no_trade: bool | None = False
    membership_active: bool | None = True
    membership_role: str | None = "CORE"
    relative_gap_history_pct: tuple[float, ...] = ()
    relative_gap_history_dates: tuple[date, ...] = ()

    def __post_init__(self) -> None:
        for name in ("instrument_id", "symbol", "name", "topic_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be a trimmed non-empty string")
        if self.liquidity_available not in (True, False, None):
            raise ValueError("liquidity_available must be true, false, or null")
        if self.no_trade not in (True, False, None):
            raise ValueError("no_trade must be true, false, or null")
        if self.membership_active not in (True, False, None):
            raise ValueError("membership_active must be true, false, or null")
        if self.membership_role is not None and not isinstance(self.membership_role, str):
            raise ValueError("membership_role must be text or null")
        if any(not _finite(item) for item in self.relative_gap_history_pct):
            raise ValueError("relative gap history must be finite")
        if self.relative_gap_history_dates and len(self.relative_gap_history_dates) != len(
            self.relative_gap_history_pct
        ):
            raise ValueError("relative gap history dates must align with gap values")


@dataclass(frozen=True)
class OpportunityStrategyInput:
    theme: ThemeContext
    stock: StrategyStockContext
    as_of: date | None = None
    policy: OpportunityPolicy = OpportunityPolicy()

    def __post_init__(self) -> None:
        if self.theme.topic_id != self.stock.topic_id:
            raise ValueError("theme and stock topic_id must match")


@dataclass(frozen=True)
class StrategyStage:
    name: str
    assessment: StageAssessment


@dataclass(frozen=True)
class OpportunityStrategyResult:
    contract_version: str
    policy_version: str
    strategy_id: str
    strategy_type: str
    instrument_id: str
    topic_id: str
    as_of: date | None
    status: str
    eligibility: str
    exclusion_codes: tuple[str, ...]
    stages: tuple[StrategyStage, ...]
    evidence: tuple[Evidence, ...]
    rank_score: float | None
    ranking_status: str
    confidence: str | None
    confidence_basis: tuple[str, ...]
    opportunity_state: str | None
    publication_status: str = "SHADOW_ONLY"
    qualification_class: str = QUALIFICATION_NONE
    qualification_status: str = "NOT_EVALUATED"
    qualification_reason_codes: tuple[str, ...] = ()
    qualification_exception: bool = False
    qualification_policy_version: str | None = None
    qualification_parameter_version: str | None = None

    def __post_init__(self) -> None:
        if self.contract_version != OPPORTUNITY_ENGINE_CONTRACT_VERSION:
            raise ValueError("unsupported opportunity engine contract")
        if self.status not in {RESULT_CANDIDATE, RESULT_EXCLUDED, RESULT_DEFERRED, RESULT_FUTURE}:
            raise ValueError(f"unknown strategy result status: {self.status}")
        if self.eligibility not in {PASS, FAIL, UNKNOWN}:
            raise ValueError(f"unknown strategy eligibility: {self.eligibility}")
        if self.ranking_status not in {RANKING_STATUS_AVAILABLE, RANKING_STATUS_UNAVAILABLE}:
            raise ValueError("unknown ranking status")
        if self.rank_score is not None and not _finite(self.rank_score):
            raise ValueError("rank_score must be finite or null")
        if self.publication_status != "SHADOW_ONLY":
            raise ValueError("strategy results cannot be published")
        if self.qualification_class not in {
            QUALIFICATION_FORMAL,
            QUALIFICATION_EXCEPTION,
            QUALIFICATION_NONE,
        }:
            raise ValueError("unknown qualification class")
        if not isinstance(self.qualification_status, str) or not self.qualification_status.strip():
            raise ValueError("qualification_status must be non-empty text")
        if any(
            not isinstance(item, str) or not item.strip()
            for item in self.qualification_reason_codes
        ):
            raise ValueError("qualification_reason_codes must contain non-empty text")
        if not isinstance(self.qualification_exception, bool):
            raise ValueError("qualification_exception must be boolean")

    def as_dict(self) -> dict[str, object]:
        # Import lazily so the strategy module remains the low-level evaluator
        # while exposing the 024A decision/explanation projection to shadow
        # callers that serialize a strategy result directly.
        from .opportunity_contract import build_opportunity_explanation, decide_opportunity

        decision = decide_opportunity(self)
        return {
            "contractVersion": self.contract_version,
            "policyVersion": self.policy_version,
            "strategyId": self.strategy_id,
            "strategyType": self.strategy_type,
            "instrumentId": self.instrument_id,
            "topicId": self.topic_id,
            "asOf": self.as_of.isoformat() if self.as_of else None,
            "status": self.status,
            "eligibility": self.eligibility,
            "exclusionCodes": list(self.exclusion_codes),
            "stages": [
                {"name": stage.name, "assessment": stage.assessment.as_dict()}
                for stage in self.stages
            ],
            "evidence": [item.as_dict() for item in self.evidence],
            "rankScore": self.rank_score,
            "rankingStatus": self.ranking_status,
            "confidence": self.confidence,
            "confidenceBasis": list(self.confidence_basis),
            "opportunityState": self.opportunity_state,
            "qualificationClass": self.qualification_class,
            "qualificationStatus": self.qualification_status,
            "qualificationReasonCodes": list(self.qualification_reason_codes),
            "qualificationException": self.qualification_exception,
            "qualificationPolicyVersion": self.qualification_policy_version,
            "qualificationParameterVersion": self.qualification_parameter_version,
            "decision": decision.as_dict(),
            "explanation": build_opportunity_explanation(self, decision).as_dict(),
            "publicationStatus": self.publication_status,
        }


@dataclass(frozen=True)
class OpportunityEngineResult:
    contract_version: str
    policy: OpportunityPolicy
    as_of: date | None
    status: str
    results_by_strategy: tuple[tuple[str, tuple[OpportunityStrategyResult, ...]], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contractVersion": self.contract_version,
            "policy": self.policy.as_dict(),
            "asOf": self.as_of.isoformat() if self.as_of else None,
            "status": self.status,
            "resultsByStrategy": {
                key: [item.as_dict() for item in values] for key, values in self.results_by_strategy
            },
            "globalCrossStrategyRanking": None,
            "publicationStatus": "SHADOW_ONLY",
        }

    def for_strategy(self, strategy_id: str) -> tuple[OpportunityStrategyResult, ...]:
        for key, values in self.results_by_strategy:
            if key == strategy_id:
                return values
        return ()


class OpportunityStrategy(Protocol):
    strategy_id: str

    def evaluate(self, value: OpportunityStrategyInput) -> OpportunityStrategyResult: ...


def _finite(value: object) -> bool:
    try:
        return value is not None and not isinstance(value, bool) and float(value) == float(value)
    except (TypeError, ValueError, OverflowError):
        return False


def _assessment(status: str, code: str, *evidence: Evidence) -> StageAssessment:
    return StageAssessment(status, (code,), tuple(evidence))


def _complete_topic_context(
    context: ThemeContext,
    allowed_grades: frozenset[str],
    allowed_lifecycles: frozenset[str],
    *,
    exception_grades: frozenset[str] = EXCEPTION_TOPIC_GRADES,
    hard_excluded_grades: frozenset[str] = HARD_EXCLUDED_TOPIC_GRADES,
) -> StageAssessment:
    if context.grade is None or context.lifecycle is None:
        return _assessment(
            UNKNOWN,
            "THEME_CONTEXT_INCOMPLETE",
            Evidence("TOPIC_GRADE", EVIDENCE_UNAVAILABLE, context.grade),
            Evidence("TOPIC_LIFECYCLE", EVIDENCE_UNAVAILABLE, context.lifecycle),
        )
    if context.grade in exception_grades:
        has_warming_signal = context.warming_candidate is True or bool(context.warming_evidence)
        if has_warming_signal:
            return _assessment(
                PASS,
                "TOPIC_GRADE_EXCEPTION_CANDIDATE",
                Evidence("TOPIC_GRADE", EVIDENCE_OBSERVED, context.grade),
                Evidence(
                    "EXCEPTION_PROVENANCE",
                    EVIDENCE_DERIVED,
                    ",".join(context.exception_provenance) or "WARMING_OR_IMPROVING",
                ),
                Evidence("FORMAL_GRADES", EVIDENCE_DERIVED, ",".join(sorted(allowed_grades))),
                *context.warming_evidence,
            )
        return StageAssessment(
            FAIL,
            ("TOPIC_GRADE_EXCEPTION_REQUIRED", "THEME_GRADE_NOT_ELIGIBLE"),
            (
                Evidence("TOPIC_GRADE", EVIDENCE_OBSERVED, context.grade),
                Evidence("EXCEPTION_PROVENANCE", EVIDENCE_UNAVAILABLE, "WARMING_OR_IMPROVING"),
            ),
        )
    if context.grade in hard_excluded_grades:
        return _assessment(
            FAIL,
            "TOPIC_GRADE_HARD_EXCLUDED",
            Evidence("TOPIC_GRADE", EVIDENCE_OBSERVED, context.grade),
        )
    if context.grade not in allowed_grades:
        return _assessment(
            FAIL,
            "THEME_GRADE_NOT_ELIGIBLE",
            Evidence("TOPIC_GRADE", EVIDENCE_OBSERVED, context.grade),
            Evidence("ALLOWED_GRADES", EVIDENCE_DERIVED, ",".join(sorted(allowed_grades))),
        )
    if context.lifecycle not in allowed_lifecycles:
        return _assessment(
            FAIL,
            "THEME_LIFECYCLE_NOT_ELIGIBLE",
            Evidence("TOPIC_LIFECYCLE", EVIDENCE_OBSERVED, context.lifecycle),
            Evidence("ALLOWED_LIFECYCLES", EVIDENCE_DERIVED, ",".join(sorted(allowed_lifecycles))),
        )
    return _assessment(
        PASS,
        "THEME_CONTEXT_ELIGIBLE",
        Evidence("TOPIC_GRADE", EVIDENCE_OBSERVED, context.grade),
        Evidence("TOPIC_LIFECYCLE", EVIDENCE_OBSERVED, context.lifecycle),
        Evidence("TOPIC_STRENGTH", EVIDENCE_OBSERVED, context.topic_strength),
        Evidence(
            "TOPIC_SNAPSHOT_DATE",
            EVIDENCE_OBSERVED,
            context.snapshot_date.isoformat() if context.snapshot_date else None,
        ),
        Evidence("TOPIC_SNAPSHOT_AVAILABLE", EVIDENCE_OBSERVED, context.topic_snapshot is not None),
        *context.strength_evidence,
    )


def _data_quality_stage(value: OpportunityStrategyInput) -> StageAssessment:
    stock = value.stock
    theme = value.theme
    if (
        stock.membership_active is None
        or stock.liquidity_available is None
        or stock.no_trade is None
        or theme.no_trade is None
    ):
        return _assessment(
            UNKNOWN, "DATA_QUALITY_INCOMPLETE", Evidence("DATA_QUALITY", EVIDENCE_UNAVAILABLE)
        )
    if not stock.membership_active:
        return _assessment(
            FAIL, "MEMBERSHIP_NOT_ACTIVE", Evidence("MEMBERSHIP_ACTIVE", EVIDENCE_OBSERVED, False)
        )
    if stock.no_trade or theme.no_trade:
        return _assessment(
            FAIL, "FORMAL_NO_TRADE", Evidence("FORMAL_NO_TRADE", EVIDENCE_OBSERVED, True)
        )
    if not stock.liquidity_available:
        return _assessment(
            FAIL, "LIQUIDITY_UNAVAILABLE", Evidence("LIQUIDITY_AVAILABLE", EVIDENCE_OBSERVED, False)
        )
    return _assessment(
        PASS,
        "DATA_QUALITY_CLEAR",
        Evidence("MEMBERSHIP_ACTIVE", EVIDENCE_OBSERVED, True),
        Evidence("MEMBERSHIP_ROLE", EVIDENCE_OBSERVED, stock.membership_role),
        Evidence("LIQUIDITY_AVAILABLE", EVIDENCE_OBSERVED, True),
        Evidence("FORMAL_NO_TRADE", EVIDENCE_OBSERVED, False),
    )


def _lifecycle_stage(context: ThemeContext, strategy_id: str) -> StageAssessment:
    """Consume Topic Engine lifecycle without recalculating or renaming it."""

    if context.lifecycle is None:
        return _assessment(
            UNKNOWN,
            "LIFECYCLE_CONTEXT_UNAVAILABLE",
            Evidence("TOPIC_LIFECYCLE", EVIDENCE_UNAVAILABLE),
        )
    fit = LIFECYCLE_STRATEGY_MATRIX.get(context.lifecycle, {}).get(strategy_id)
    if fit is None:
        return _assessment(
            UNKNOWN,
            "LIFECYCLE_CONTEXT_UNSUPPORTED",
            Evidence("TOPIC_LIFECYCLE", EVIDENCE_OBSERVED, context.lifecycle),
        )
    status = FAIL if fit == "HARD_EXCLUDE" else PASS
    return _assessment(
        status,
        "LIFECYCLE_HARD_EXCLUDE" if status == FAIL else f"LIFECYCLE_{fit}",
        Evidence("TOPIC_LIFECYCLE", EVIDENCE_OBSERVED, context.lifecycle),
        Evidence("LIFECYCLE_STRATEGY_FIT", EVIDENCE_DERIVED, fit),
        Evidence("LIFECYCLE_MATRIX_VERSION", EVIDENCE_DERIVED, "opportunity-policy-v1"),
    )


def _return_pct(bars: Sequence[CanonicalOHLCVBar], window: int) -> float | None:
    closes = [float(bar.close) for bar in bars if bar.close is not None]
    if len(closes) <= window or closes[-window - 1] == 0:
        return None
    return (closes[-1] - closes[-window - 1]) / closes[-window - 1] * 100.0


def _stock_theme_relative(
    value: OpportunityStrategyInput, window: int
) -> tuple[float | None, float | None, float | None]:
    stock_return = _return_pct(value.stock.bars, window)
    topic_returns = (
        value.theme.topic_returns_pct
        if value.theme.topic_returns_pct is not None
        else value.theme.stock_returns_pct
    )
    theme_return = None if topic_returns is None else topic_returns.get(window)
    relative = (
        None if stock_return is None or theme_return is None else stock_return - float(theme_return)
    )
    return stock_return, None if theme_return is None else float(theme_return), relative


def _technical_stage(
    value: OpportunityStrategyInput, technical: TechnicalEvidenceBundle
) -> StageAssessment:
    facts = technical.technical_facts
    if technical.sufficiency.assessment.status != PASS:
        return _assessment(
            UNKNOWN if technical.sufficiency.assessment.status == UNKNOWN else FAIL,
            "TECHNICAL_HISTORY_UNAVAILABLE"
            if technical.sufficiency.assessment.status == UNKNOWN
            else "TECHNICAL_HISTORY_INSUFFICIENT",
            *technical.sufficiency.assessment.evidence,
        )
    if facts.ma20_available is None:
        return _assessment(UNKNOWN, "TECHNICAL_20MA_INCOMPLETE", *technical.ma20.evidence)
    if not facts.ma20_available:
        return _assessment(FAIL, "MA20_UNAVAILABLE", *technical.ma20.evidence)
    if technical.price_volume.assessment.status == UNKNOWN:
        return _assessment(
            UNKNOWN, "PRICE_VOLUME_INCOMPLETE", *technical.price_volume.assessment.evidence
        )
    return _assessment(
        PASS,
        "TREND_STRUCTURE_HEALTHY" if facts.ma_direction else "TREND_STRUCTURE_MIXED",
        *technical.ma20.evidence,
        *technical.price_volume.assessment.evidence,
        *technical.support.assessment.evidence,
    )


def _exclusion_stage(
    value: OpportunityStrategyInput, technical: TechnicalEvidenceBundle
) -> StageAssessment:
    price = technical.price_volume.price
    ma20 = technical.ma20.value
    if price is None or ma20 is None:
        return _assessment(
            UNKNOWN,
            "PRICE_OR_MA20_UNAVAILABLE",
            Evidence("PRICE", EVIDENCE_UNAVAILABLE, price),
            Evidence("MA20", EVIDENCE_UNAVAILABLE, ma20),
        )
    if price < ma20:
        return _assessment(
            FAIL,
            "PRICE_NOT_ABOVE_20MA",
            Evidence("PRICE", EVIDENCE_OBSERVED, price),
            Evidence("MA20", EVIDENCE_DERIVED, ma20),
        )
    if technical.bearish_break.assessment.status == FAIL:
        return _assessment(FAIL, "STRUCTURAL_BREAKDOWN", *technical.bearish_break.evidence)
    return _assessment(PASS, "NO_STRUCTURAL_EXCLUSION", *technical.bearish_break.evidence)


def _rank_score(
    value: OpportunityStrategyInput,
    technical: TechnicalEvidenceBundle,
    relative_pct: float | None,
    *,
    entry_band: float | None,
    allowed_grades: frozenset[str],
    profile: StrategyRankingProfile,
    extension_threshold_pct: float,
) -> tuple[float | None, tuple[str, ...]]:
    policy = value.policy
    if relative_pct is None or technical.price_volume.relative_volume is None or entry_band is None:
        return None, ("RANKING_COMPONENT_UNAVAILABLE",)
    relative_component = max(
        0.0,
        min(
            1.0,
            (relative_pct - profile.relative_floor_pct)
            / (profile.relative_ceiling_pct - profile.relative_floor_pct),
        ),
    )
    structure_component = 1.0 if technical.ma20.direction == "UP" else 0.0
    volume_component = max(
        0.0,
        min(
            1.0, technical.price_volume.relative_volume / max(policy.volume_activation_ratio, 1e-9)
        ),
    )
    entry_component = max(
        0.0,
        min(
            1.0,
            1.0
            - max(entry_band, 0.0)
            / max(policy.technical_policy.support_distance_wait_max_pct, 1e-9),
        ),
    )
    theme_component = 1.0 if value.theme.grade in allowed_grades else 0.0
    price = technical.price_volume.price
    ma20 = technical.ma20.value
    extension_component = 0.0
    if price is not None and ma20 not in (None, 0):
        distance = (price - ma20) / ma20 * 100.0
        extension_component = max(
            0.0,
            min(
                1.0,
                1.0 - max(distance, 0.0) / max(extension_threshold_pct, 1e-9),
            ),
        )
    weights = profile.weights
    components = (
        theme_component,
        structure_component,
        relative_component,
        volume_component,
        entry_component,
        extension_component,
    )
    denominator = sum(weights)
    if denominator <= 0:
        return None, ("RANKING_WEIGHTS_UNAVAILABLE",)
    score = (
        sum(weight * component for weight, component in zip(weights, components, strict=True))
        / denominator
        * 100.0
    )
    lifecycle = value.theme.lifecycle
    if lifecycle == "SPROUTING":
        score *= policy.sprouting_rank_multiplier
    elif lifecycle == "MATURE":
        score *= (
            policy.trend_mature_rank_multiplier
            if profile.strategy_id == STRATEGY_TREND_CONTINUATION
            else policy.catch_up_mature_rank_multiplier
        )
    return score, (
        "THEME_COMPONENT",
        "STRUCTURE_COMPONENT",
        "RELATIVE_STRENGTH_COMPONENT",
        "VOLUME_COMPONENT",
        "ENTRY_COMPONENT",
        "EXTENSION_CONTEXT_COMPONENT",
        "LIFECYCLE_RANK_CONTEXT",
    )


def _confidence(available: int, total: int) -> tuple[str, tuple[str, ...]]:
    if total <= 0 or available <= 0:
        return CONFIDENCE_LOW, ("NO_CONFIDENCE_EVIDENCE",)
    ratio = available / total
    if ratio >= 0.80:
        return CONFIDENCE_HIGH, ("EVIDENCE_COVERAGE_HIGH",)
    if ratio >= 0.50:
        return CONFIDENCE_MEDIUM, ("EVIDENCE_COVERAGE_PARTIAL",)
    return CONFIDENCE_LOW, ("EVIDENCE_COVERAGE_LOW",)


def _result_status(
    stages: Sequence[StrategyStage],
    *,
    soft_fail_stage_names: frozenset[str] = frozenset(),
) -> tuple[str, str]:
    """Apply fail-closed semantics while preserving missing-context deferral."""

    theme_status = next(
        (stage.assessment.status for stage in stages if stage.name == "THEME_CONTEXT"),
        UNKNOWN,
    )
    data_status = next(
        (stage.assessment.status for stage in stages if stage.name == "DATA_QUALITY"),
        UNKNOWN,
    )
    if theme_status == UNKNOWN or data_status == UNKNOWN:
        return RESULT_DEFERRED, UNKNOWN
    if any(
        stage.assessment.status == FAIL and stage.name not in soft_fail_stage_names
        for stage in stages
    ):
        return RESULT_EXCLUDED, FAIL
    if any(stage.assessment.status == UNKNOWN for stage in stages):
        return RESULT_DEFERRED, UNKNOWN
    return RESULT_CANDIDATE, PASS


def _qualification_class(stages: Sequence[StrategyStage]) -> str:
    theme = next((stage for stage in stages if stage.name == "THEME_CONTEXT"), None)
    if theme is None:
        return QUALIFICATION_NONE
    if "TOPIC_GRADE_EXCEPTION_CANDIDATE" in theme.assessment.reason_codes:
        return QUALIFICATION_EXCEPTION
    if theme.assessment.status == PASS:
        return QUALIFICATION_FORMAL
    return QUALIFICATION_NONE


def _state(
    entry_status: str | None,
    candidate: bool,
    *,
    confirmation_wait: bool = False,
    lifecycle_wait: bool = False,
    result_status: str | None = None,
) -> str | None:
    if not candidate:
        if result_status in {RESULT_EXCLUDED, RESULT_FUTURE}:
            return DECISION_STATE_EXCLUDED
        return DECISION_STATE_DEFERRED
    if entry_status == "WAIT":
        return DECISION_STATE_WAITING_RETEST
    if confirmation_wait or lifecycle_wait:
        return DECISION_STATE_WAITING_CONFIRMATION
    return DECISION_STATE_SELECTED


def _entry_stage(
    technical: TechnicalEvidenceBundle,
    policy: OpportunityEvidencePolicy,
) -> tuple[EntryQualityFacts, StrategyStage]:
    entry = build_entry_quality(technical.price_volume.price, technical.support, policy)
    status = PASS if entry.status in {PASS, "WAIT"} else UNKNOWN
    assessment = StageAssessment(status, entry.reason_codes, entry.evidence)
    return entry, StrategyStage("ENTRY_QUALITY", assessment)


def _volume_stage(
    technical: TechnicalEvidenceBundle,
    policy: OpportunityPolicy,
) -> StrategyStage:
    relative_volume = technical.price_volume.relative_volume
    if relative_volume is None:
        return StrategyStage(
            "VOLUME_ACTIVATION",
            _assessment(
                UNKNOWN,
                "VOLUME_ACTIVATION_UNAVAILABLE",
                Evidence("RELATIVE_VOLUME", EVIDENCE_UNAVAILABLE),
            ),
        )
    status = PASS if relative_volume >= policy.volume_activation_ratio else FAIL
    return StrategyStage(
        "VOLUME_ACTIVATION",
        _assessment(
            status,
            "VOLUME_ACTIVATION_CONFIRMED" if status == PASS else "VOLUME_ACTIVATION_BELOW_POLICY",
            Evidence("RELATIVE_VOLUME", EVIDENCE_DERIVED, relative_volume),
            Evidence("VOLUME_ACTIVATION_RATIO", EVIDENCE_DERIVED, policy.volume_activation_ratio),
        ),
    )


def _momentum_stage(
    value: OpportunityStrategyInput,
    technical: TechnicalEvidenceBundle,
    window: int,
) -> StrategyStage:
    closes = [float(bar.close) for bar in value.stock.bars if bar.close is not None]
    if len(closes) <= window + 1:
        return StrategyStage(
            "MOMENTUM_QUALITY",
            _assessment(
                UNKNOWN, "MOMENTUM_EVIDENCE_UNAVAILABLE", Evidence("MOMENTUM", EVIDENCE_UNAVAILABLE)
            ),
        )
    recent_return = (closes[-1] - closes[-window - 1]) / closes[-window - 1] * 100.0
    peak = max(closes[-window:])
    drawdown = (closes[-1] - peak) / peak * 100.0 if peak else None
    daily_returns = [
        (current - prior) / prior * 100.0
        for prior, current in zip(closes[-window - 1 : -1], closes[-window:], strict=True)
        if prior
    ]
    volatility = None
    if daily_returns:
        mean = sum(daily_returns) / len(daily_returns)
        volatility = (sum((item - mean) ** 2 for item in daily_returns) / len(daily_returns)) ** 0.5
    return StrategyStage(
        "MOMENTUM_QUALITY",
        _assessment(
            PASS,
            "MOMENTUM_EVIDENCE_AVAILABLE",
            Evidence("RECENT_RETURN_PCT", EVIDENCE_DERIVED, recent_return),
            Evidence("RECENT_DRAWDOWN_PCT", EVIDENCE_DERIVED, drawdown),
            Evidence("RECENT_VOLATILITY_PCT", EVIDENCE_DERIVED, volatility),
            Evidence("MOMENTUM_WINDOW", EVIDENCE_OBSERVED, window),
            *technical.price_volume.assessment.evidence,
        ),
    )


def _extension_stage(
    technical: TechnicalEvidenceBundle,
    threshold: float,
) -> StrategyStage:
    price = technical.price_volume.price
    ma20 = technical.ma20.value
    if price is None or ma20 in (None, 0):
        return StrategyStage(
            "EXTENSION_RISK",
            _assessment(
                UNKNOWN,
                "EXTENSION_EVIDENCE_UNAVAILABLE",
                Evidence("EXTENSION", EVIDENCE_UNAVAILABLE),
            ),
        )
    distance = (price - ma20) / ma20 * 100.0
    elevated = distance > threshold
    return StrategyStage(
        "EXTENSION_RISK",
        _assessment(
            PASS,
            "EXTENSION_ELEVATED" if elevated else "EXTENSION_WITHIN_POLICY_CONTEXT",
            Evidence("PRICE_TO_MA20_DISTANCE_PCT", EVIDENCE_DERIVED, distance),
            Evidence("EXTENSION_CONTEXT_THRESHOLD_PCT", EVIDENCE_DERIVED, threshold),
            Evidence("EXTENSION_ELEVATED", EVIDENCE_DERIVED, elevated),
        ),
    )


class TrendContinuationStrategy:
    strategy_id = STRATEGY_TREND_CONTINUATION

    def evaluate(self, value: OpportunityStrategyInput) -> OpportunityStrategyResult:
        policy = value.policy
        theme = StrategyStage(
            "THEME_CONTEXT",
            _complete_topic_context(
                value.theme,
                policy.trend_allowed_grades,
                policy.trend_allowed_lifecycles,
                exception_grades=policy.exception_grades,
                hard_excluded_grades=policy.hard_excluded_grades,
            ),
        )
        lifecycle = StrategyStage(
            "LIFECYCLE_FIT", _lifecycle_stage(value.theme, self.strategy_id)
        )
        technical = build_technical_evidence(
            value.stock.bars, policy.technical_policy, as_of=value.as_of
        )
        stages = [theme, lifecycle]
        data_quality = StrategyStage("DATA_QUALITY", _data_quality_stage(value))
        eligibility = StrategyStage("ELIGIBILITY", _technical_stage(value, technical))
        exclusion = StrategyStage("EXCLUSION", _exclusion_stage(value, technical))
        stages.extend((data_quality, eligibility, exclusion))
        stock_return, theme_return, relative = _stock_theme_relative(
            value, policy.trend_relative_window
        )
        relative_status = (
            UNKNOWN
            if relative is None
            else PASS
            if relative >= policy.trend_relative_min_pct
            else FAIL
        )
        relative_stage = StrategyStage(
            "RELATIVE_STRENGTH",
            _assessment(
                relative_status,
                "RELATIVE_STRENGTH_POSITIVE"
                if relative_status == PASS
                else "RELATIVE_STRENGTH_UNAVAILABLE"
                if relative_status == UNKNOWN
                else "RELATIVE_STRENGTH_BELOW_POLICY",
                Evidence("STOCK_RETURN_PCT", EVIDENCE_DERIVED, stock_return),
                Evidence("THEME_RETURN_PCT", EVIDENCE_OBSERVED, theme_return),
                Evidence("RELATIVE_STRENGTH_PCT", EVIDENCE_DERIVED, relative),
                Evidence("RELATIVE_WINDOW", EVIDENCE_OBSERVED, policy.trend_relative_window),
            ),
        )
        volume = StrategyStage("VOLUME_CONFIRMATION", technical.price_volume.assessment)
        momentum = _momentum_stage(value, technical, policy.trend_recent_return_window)
        extension = _extension_stage(technical, policy.trend_extension_distance_pct)
        entry, entry_stage = _entry_stage(technical, policy.technical_policy)
        stages.extend((relative_stage, volume, momentum, extension, entry_stage))
        status, eligibility_status = _result_status(
            stages,
            soft_fail_stage_names=frozenset(
                {"MOMENTUM_QUALITY", "EXTENSION_RISK"}
            ),
        )
        entry_distance = None
        if (
            technical.price_volume.price is not None
            and technical.support.primary_support is not None
        ):
            entry_distance = technical.price_volume.price - technical.support.primary_support.price
            if technical.support.primary_support.price:
                entry_distance = entry_distance / technical.support.primary_support.price * 100.0
        rank_score = None
        if status == RESULT_CANDIDATE:
            rank_score, _rank_basis = _rank_score(
                value,
                technical,
                relative,
                entry_band=entry_distance,
                allowed_grades=policy.trend_allowed_grades,
                profile=policy.trend_ranking_profile,
                extension_threshold_pct=policy.trend_extension_distance_pct,
            )
        confidence, confidence_basis = _confidence(
            sum(stage.assessment.status != UNKNOWN for stage in stages), len(stages)
        )
        evidence = tuple(item for stage in stages for item in stage.assessment.evidence)
        return OpportunityStrategyResult(
            OPPORTUNITY_ENGINE_CONTRACT_VERSION,
            policy.policy_version,
            self.strategy_id,
            self.strategy_id,
            value.stock.instrument_id,
            value.theme.topic_id,
            value.as_of,
            status,
            eligibility_status,
            tuple(
                code
                for stage in stages
                if stage.assessment.status == FAIL
                for code in stage.assessment.reason_codes
            ),
            tuple(stages),
            evidence,
            rank_score,
            RANKING_STATUS_AVAILABLE if rank_score is not None else RANKING_STATUS_UNAVAILABLE,
            confidence,
            confidence_basis,
            _state(
                entry.status if status == RESULT_CANDIDATE else None,
                status == RESULT_CANDIDATE,
                confirmation_wait=any(
                    stage.assessment.status == FAIL
                    for stage in stages
                    if stage.name in {"MOMENTUM_QUALITY", "EXTENSION_RISK"}
                ),
                lifecycle_wait=any(
                    "WAITING_CONFIRMATION" in stage.assessment.reason_codes
                    for stage in stages
                    if stage.name == "LIFECYCLE_FIT"
                ),
                result_status=status,
            ),
            qualification_class=_qualification_class(stages),
        )


class CatchUpStrategy:
    strategy_id = STRATEGY_CATCH_UP

    def evaluate(self, value: OpportunityStrategyInput) -> OpportunityStrategyResult:
        policy = value.policy
        theme = StrategyStage(
            "THEME_CONTEXT",
            _complete_topic_context(
                value.theme,
                policy.catch_up_allowed_grades,
                policy.catch_up_allowed_lifecycles,
                exception_grades=policy.exception_grades,
                hard_excluded_grades=policy.hard_excluded_grades,
            ),
        )
        lifecycle = StrategyStage(
            "LIFECYCLE_FIT", _lifecycle_stage(value.theme, self.strategy_id)
        )
        technical = build_technical_evidence(
            value.stock.bars, policy.technical_policy, as_of=value.as_of
        )
        data_quality = StrategyStage("DATA_QUALITY", _data_quality_stage(value))
        structure = StrategyStage("STRUCTURE_HEALTH", _technical_stage(value, technical))
        exclusion = StrategyStage("EXCLUSION", _exclusion_stage(value, technical))
        stock_return, theme_return, relative = _stock_theme_relative(
            value, policy.catch_up_relative_window
        )
        lag_status = (
            UNKNOWN
            if relative is None
            else PASS
            if policy.catch_up_lag_min_pct <= relative <= policy.catch_up_lag_max_pct
            else FAIL
        )
        lag_stage = StrategyStage(
            "CATCH_UP_LAG",
            _assessment(
                lag_status,
                "CATCHUP_LAG_IN_WINDOW"
                if lag_status == PASS
                else "CATCHUP_LAG_UNAVAILABLE"
                if lag_status == UNKNOWN
                else "CATCHUP_LAG_OUTSIDE_WINDOW",
                Evidence("STOCK_RETURN_PCT", EVIDENCE_DERIVED, stock_return),
                Evidence("THEME_RETURN_PCT", EVIDENCE_OBSERVED, theme_return),
                Evidence("RELATIVE_GAP_PCT", EVIDENCE_DERIVED, relative),
                Evidence("LAG_MIN_PCT", EVIDENCE_DERIVED, policy.catch_up_lag_min_pct),
                Evidence("LAG_MAX_PCT", EVIDENCE_DERIVED, policy.catch_up_lag_max_pct),
            ),
        )
        history = value.stock.relative_gap_history_pct
        if len(history) < policy.catch_up_inflection_lookback + 1:
            inflection_status = UNKNOWN
            change = None
            slope = None
            acceleration = None
        else:
            change = history[-1] - history[-policy.catch_up_inflection_lookback - 1]
            slope = change / policy.catch_up_inflection_lookback
            prior_slope = None
            if len(history) >= policy.catch_up_inflection_lookback * 2 + 1:
                prior_change = (
                    history[-policy.catch_up_inflection_lookback - 1]
                    - history[-policy.catch_up_inflection_lookback * 2 - 1]
                )
                prior_slope = prior_change / policy.catch_up_inflection_lookback
            acceleration = None if prior_slope is None else slope - prior_slope
            inflection_status = (
                PASS if change >= policy.catch_up_inflection_min_change_pct else FAIL
            )
        inflection_stage = StrategyStage(
            "RELATIVE_STRENGTH_INFLECTION",
            _assessment(
                inflection_status,
                "CATCHUP_RS_IMPROVING"
                if inflection_status == PASS
                else "CATCHUP_RS_UNAVAILABLE"
                if inflection_status == UNKNOWN
                else "CATCHUP_RS_DETERIORATING",
                Evidence("RS_GAP_CHANGE_PCT", EVIDENCE_DERIVED, change),
                Evidence("RS_SLOPE_PCT", EVIDENCE_DERIVED, slope),
                Evidence("RS_ACCELERATION_PCT", EVIDENCE_DERIVED, acceleration),
                Evidence("RS_HISTORY_POINTS", EVIDENCE_OBSERVED, len(history)),
            ),
        )
        volume_structure = StrategyStage("VOLUME_CONFIRMATION", technical.price_volume.assessment)
        volume_stage = _volume_stage(technical, policy)
        momentum = _momentum_stage(value, technical, policy.trend_recent_return_window)
        extension = _extension_stage(technical, policy.catch_up_extension_distance_pct)
        entry, entry_stage = _entry_stage(technical, policy.technical_policy)
        stages = [
            theme,
            lifecycle,
            data_quality,
            structure,
            exclusion,
            lag_stage,
            inflection_stage,
            volume_structure,
            volume_stage,
            momentum,
            extension,
            entry_stage,
        ]
        status, eligibility_status = _result_status(
            stages,
            soft_fail_stage_names=frozenset(
                {"VOLUME_CONFIRMATION", "VOLUME_ACTIVATION", "MOMENTUM_QUALITY", "EXTENSION_RISK"}
            ),
        )
        entry_distance = None
        if (
            technical.price_volume.price is not None
            and technical.support.primary_support is not None
        ):
            support_price = technical.support.primary_support.price
            if support_price:
                entry_distance = (
                    (technical.price_volume.price - support_price) / support_price * 100.0
                )
        rank_score = None
        if status == RESULT_CANDIDATE:
            rank_score, _rank_basis = _rank_score(
                value,
                technical,
                relative,
                entry_band=entry_distance,
                allowed_grades=policy.catch_up_allowed_grades,
                profile=policy.catch_up_ranking_profile,
                extension_threshold_pct=policy.catch_up_extension_distance_pct,
            )
        confidence, confidence_basis = _confidence(
            sum(stage.assessment.status != UNKNOWN for stage in stages), len(stages)
        )
        evidence = tuple(item for stage in stages for item in stage.assessment.evidence)
        return OpportunityStrategyResult(
            OPPORTUNITY_ENGINE_CONTRACT_VERSION,
            policy.policy_version,
            self.strategy_id,
            self.strategy_id,
            value.stock.instrument_id,
            value.theme.topic_id,
            value.as_of,
            status,
            eligibility_status,
            tuple(
                code
                for stage in stages
                if stage.assessment.status == FAIL
                for code in stage.assessment.reason_codes
            ),
            tuple(stages),
            evidence,
            rank_score,
            RANKING_STATUS_AVAILABLE if rank_score is not None else RANKING_STATUS_UNAVAILABLE,
            confidence,
            confidence_basis,
            _state(
                entry.status if status == RESULT_CANDIDATE else None,
                status == RESULT_CANDIDATE,
                confirmation_wait=any(
                    stage.assessment.status == FAIL
                    for stage in stages
                    if stage.name
                    in {
                        "VOLUME_CONFIRMATION",
                        "VOLUME_ACTIVATION",
                        "MOMENTUM_QUALITY",
                        "EXTENSION_RISK",
                    }
                ),
                lifecycle_wait=any(
                    "WAITING_CONFIRMATION" in stage.assessment.reason_codes
                    for stage in stages
                    if stage.name == "LIFECYCLE_FIT"
                ),
                result_status=status,
            ),
            qualification_class=_qualification_class(stages),
        )


class _FutureStrategy:
    def __init__(self, strategy_id: str) -> None:
        self.strategy_id = strategy_id

    def evaluate(self, value: OpportunityStrategyInput) -> OpportunityStrategyResult:
        evidence = (
            Evidence("STRATEGY_STATUS", EVIDENCE_UNAVAILABLE, RESULT_FUTURE),
            Evidence("STRATEGY_ID", EVIDENCE_OBSERVED, self.strategy_id),
        )
        return OpportunityStrategyResult(
            OPPORTUNITY_ENGINE_CONTRACT_VERSION,
            value.policy.policy_version,
            self.strategy_id,
            self.strategy_id,
            value.stock.instrument_id,
            value.theme.topic_id,
            value.as_of,
            RESULT_FUTURE,
            UNKNOWN,
            ("STRATEGY_NOT_IMPLEMENTED",),
            (
                StrategyStage(
                    "STRATEGY", StageAssessment(UNKNOWN, ("STRATEGY_NOT_IMPLEMENTED",), evidence)
                ),
            ),
            evidence,
            None,
            RANKING_STATUS_UNAVAILABLE,
            None,
            ("FUTURE_STRATEGY",),
            None,
        )


def strategy_registry() -> dict[str, OpportunityStrategy]:
    return {
        STRATEGY_TREND_CONTINUATION: TrendContinuationStrategy(),
        STRATEGY_CATCH_UP: CatchUpStrategy(),
        STRATEGY_EARLY_STRENGTH: _FutureStrategy(STRATEGY_EARLY_STRENGTH),
        STRATEGY_PULLBACK_ACCEPTANCE: _FutureStrategy(STRATEGY_PULLBACK_ACCEPTANCE),
    }


class OpportunityEngine:
    """Small orchestration facade over the pure strategy registry."""

    def __init__(self, policy: OpportunityPolicy | None = None) -> None:
        self.policy = policy or OpportunityPolicy()

    def evaluate(
        self,
        value: OpportunityStrategyInput,
        strategy_ids: Iterable[str] = V1_STRATEGIES,
    ) -> OpportunityEngineResult:
        bound = value if value.policy == self.policy else replace(value, policy=self.policy)
        return evaluate_opportunity_engine(bound, strategy_ids)

    def replay(
        self,
        cases: Iterable[StrategyReplayCase],
        strategy_ids: Iterable[str] = V1_STRATEGIES,
    ) -> StrategyReplayResult:
        return replay_opportunity_strategies(cases, self.policy, strategy_ids)


def evaluate_opportunity_engine(
    value: OpportunityStrategyInput,
    strategy_ids: Iterable[str] = V1_STRATEGIES,
) -> OpportunityEngineResult:
    from .opportunity_qualification import apply_qualification_policy

    registry = strategy_registry()
    selected = tuple(dict.fromkeys(strategy_ids))
    if not selected:
        raise ValueError("at least one strategy is required")
    unknown = tuple(item for item in selected if item not in registry)
    if unknown:
        raise ValueError(f"unknown strategy ids: {unknown}")
    outputs: list[tuple[str, tuple[OpportunityStrategyResult, ...]]] = []
    for strategy_id in selected:
        result = registry[strategy_id].evaluate(value)
        result = apply_qualification_policy(result, value)
        outputs.append((strategy_id, (result,)))
    return OpportunityEngineResult(
        OPPORTUNITY_ENGINE_CONTRACT_VERSION,
        value.policy,
        value.as_of,
        "AVAILABLE"
        if any(result.status == RESULT_CANDIDATE for _, values in outputs for result in values)
        else "DEFERRED",
        tuple(outputs),
    )


def rank_strategy_results(
    results: Iterable[OpportunityStrategyResult],
) -> tuple[OpportunityStrategyResult, ...]:
    """Rank within one strategy only; never compare A against B globally."""

    values = tuple(results)
    if len({item.strategy_id for item in values}) > 1:
        raise ValueError("rank_strategy_results accepts one strategy at a time")
    return tuple(
        sorted(
            values,
            key=lambda item: (
                item.rank_score is not None,
                item.rank_score if item.rank_score is not None else float("-inf"),
                item.instrument_id,
            ),
            reverse=True,
        )
    )


@dataclass(frozen=True)
class StrategyReplayCase:
    theme: ThemeContext
    stock: StrategyStockContext
    evaluation_dates: tuple[date, ...]


@dataclass(frozen=True)
class StrategyReplayObservation:
    evaluation_date: date
    instrument_id: str
    strategy_id: str
    result: OpportunityStrategyResult
    latest_bar_date: date | None

    def as_dict(self) -> dict[str, object]:
        return {
            "evaluationDate": self.evaluation_date.isoformat(),
            "instrumentId": self.instrument_id,
            "strategyId": self.strategy_id,
            "latestBarDate": self.latest_bar_date.isoformat() if self.latest_bar_date else None,
            "result": self.result.as_dict(),
        }


@dataclass(frozen=True)
class StrategyReplayResult:
    contract_version: str
    policy: OpportunityPolicy
    observations: tuple[StrategyReplayObservation, ...]
    no_lookahead: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "contractVersion": self.contract_version,
            "policy": self.policy.as_dict(),
            "observations": [item.as_dict() for item in self.observations],
            "noLookahead": self.no_lookahead,
            "publicationStatus": "SHADOW_ONLY",
        }


def replay_opportunity_strategies(
    cases: Iterable[StrategyReplayCase],
    policy: OpportunityPolicy | None = None,
    strategy_ids: Iterable[str] = V1_STRATEGIES,
) -> StrategyReplayResult:
    from .opportunity_qualification import apply_qualification_policy

    policy = policy or OpportunityPolicy()
    registry = strategy_registry()
    selected = tuple(strategy_ids)
    observations: list[StrategyReplayObservation] = []
    no_lookahead = True
    for case in sorted(tuple(cases), key=lambda item: item.stock.instrument_id):
        for evaluation_date in sorted(set(case.evaluation_dates)):
            visible = tuple(bar for bar in case.stock.bars if bar.trading_date <= evaluation_date)
            no_lookahead = no_lookahead and all(
                bar.trading_date <= evaluation_date for bar in visible
            )
            gap_values = case.stock.relative_gap_history_pct
            gap_dates = case.stock.relative_gap_history_dates
            if gap_dates:
                bounded_gaps = tuple(
                    value
                    for value, gap_date in zip(gap_values, gap_dates, strict=True)
                    if gap_date <= evaluation_date
                )
                no_lookahead = no_lookahead and all(
                    gap_date <= evaluation_date
                    for gap_date in gap_dates
                    if gap_date <= evaluation_date
                )
            else:
                bounded_gaps = gap_values
            stock = replace(
                case.stock,
                bars=visible,
                relative_gap_history_pct=bounded_gaps,
                relative_gap_history_dates=tuple(
                    gap_date for gap_date in gap_dates if gap_date <= evaluation_date
                ),
            )
            theme = case.theme
            if theme.snapshot_date is not None and theme.snapshot_date > evaluation_date:
                theme = replace(
                    theme,
                    grade=None,
                    lifecycle=None,
                    topic_strength=None,
                    strength_evidence=(),
                    snapshot_date=None,
                    topic_snapshot=None,
                    stock_returns_pct=None,
                    topic_returns_pct=None,
                    warming_candidate=None,
                    warming_evidence=(),
                    exception_provenance=(),
                )
            value = OpportunityStrategyInput(theme, stock, evaluation_date, policy)
            for strategy_id in selected:
                result = registry[strategy_id].evaluate(value)
                result = apply_qualification_policy(result, value)
                observations.append(
                    StrategyReplayObservation(
                        evaluation_date,
                        stock.instrument_id,
                        strategy_id,
                        result,
                        max((bar.trading_date for bar in visible), default=None),
                    )
                )
    return StrategyReplayResult(
        OPPORTUNITY_ENGINE_CONTRACT_VERSION,
        policy,
        tuple(observations),
        no_lookahead,
    )


@dataclass(frozen=True)
class PMCalibrationRow:
    evaluation_date: date
    topic_id: str
    instrument_id: str
    strategy_id: str
    theme_grade: str | None
    lifecycle: str | None
    status: str
    eligibility: str
    exclusion_codes: tuple[str, ...]
    relative_strength_pct: float | None
    rank_score: float | None
    confidence: str | None
    reason_codes: tuple[str, ...]
    lifecycle_at_selection: str | None = None
    topic_grade_at_selection: str | None = None
    opportunity_state_at_selection: str | None = None
    ranking_profile_version: str | None = None
    policy_version: str | None = None
    parameter_version: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "evaluationDate": self.evaluation_date.isoformat(),
            "topicId": self.topic_id,
            "instrumentId": self.instrument_id,
            "strategyId": self.strategy_id,
            "themeGrade": self.theme_grade,
            "lifecycle": self.lifecycle,
            "status": self.status,
            "eligibility": self.eligibility,
            "exclusionCodes": list(self.exclusion_codes),
            "relativeStrengthPct": self.relative_strength_pct,
            "rankScore": self.rank_score,
            "confidence": self.confidence,
            "reasonCodes": list(self.reason_codes),
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
class PMCalibrationReport:
    contract_version: str
    policy_version: str
    rows: tuple[PMCalibrationRow, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "contractVersion": self.contract_version,
            "policyVersion": self.policy_version,
            "rows": [row.as_dict() for row in self.rows],
            "publicationStatus": "SHADOW_ONLY",
        }


def build_pm_calibration_report(
    replay: StrategyReplayResult,
) -> PMCalibrationReport:
    rows: list[PMCalibrationRow] = []
    for observation in replay.observations:
        relative = next(
            (
                item.value
                for item in observation.result.evidence
                if item.code in {"RELATIVE_STRENGTH_PCT", "RELATIVE_GAP_PCT"}
            ),
            None,
        )
        theme_grade = next(
            (item.value for item in observation.result.evidence if item.code == "TOPIC_GRADE"),
            None,
        )
        lifecycle = next(
            (item.value for item in observation.result.evidence if item.code == "TOPIC_LIFECYCLE"),
            None,
        )
        profile = (
            replay.policy.trend_ranking_profile
            if observation.strategy_id == STRATEGY_TREND_CONTINUATION
            else replay.policy.catch_up_ranking_profile
            if observation.strategy_id == STRATEGY_CATCH_UP
            else None
        )
        rows.append(
            PMCalibrationRow(
                observation.evaluation_date,
                observation.result.topic_id,
                observation.instrument_id,
                observation.strategy_id,
                theme_grade if isinstance(theme_grade, str) else None,
                lifecycle if isinstance(lifecycle, str) else None,
                observation.result.status,
                observation.result.eligibility,
                observation.result.exclusion_codes,
                float(relative) if isinstance(relative, (int, float)) else None,
                observation.result.rank_score,
                observation.result.confidence,
                tuple(
                    stage_code
                    for stage in observation.result.stages
                    for stage_code in stage.assessment.reason_codes
                ),
                lifecycle if isinstance(lifecycle, str) else None,
                theme_grade if isinstance(theme_grade, str) else None,
                observation.result.opportunity_state,
                profile.profile_version if profile is not None else None,
                (
                    observation.result.qualification_policy_version
                    or observation.result.policy_version
                ),
                observation.result.qualification_parameter_version,
            )
        )
    return PMCalibrationReport(
        OPPORTUNITY_ENGINE_CONTRACT_VERSION,
        replay.policy.policy_version,
        tuple(rows),
    )


__all__ = [
    "CONFIDENCE_HIGH",
    "CONFIDENCE_LOW",
    "CONFIDENCE_MEDIUM",
    "EXCEPTION_TOPIC_GRADES",
    "FORMAL_TOPIC_GRADES",
    "FUTURE_STRATEGIES",
    "HARD_EXCLUDED_TOPIC_GRADES",
    "INTRADAY_BEHAVIOR_STATUS_ONLY",
    "LIFECYCLE_STRATEGY_MATRIX",
    "OPPORTUNITY_ENGINE_CONTRACT_VERSION",
    "OPPORTUNITY_POLICY_VERSION",
    "POLICY_STATUS_PROVISIONAL",
    "PRESENTATION_CAP_CATCH_UP",
    "PRESENTATION_CAP_TREND",
    "QUALIFICATION_EXCEPTION",
    "QUALIFICATION_FORMAL",
    "QUALIFICATION_NONE",
    "RANKING_CADENCE_POST_CLOSE",
    "RESULT_CANDIDATE",
    "RESULT_DEFERRED",
    "RESULT_EXCLUDED",
    "RESULT_FUTURE",
    "STRATEGY_CATCH_UP",
    "STRATEGY_EARLY_STRENGTH",
    "STRATEGY_PULLBACK_ACCEPTANCE",
    "STRATEGY_TREND_CONTINUATION",
    "V1_STRATEGIES",
    "CatchUpStrategy",
    "OpportunityEngine",
    "OpportunityEngineResult",
    "OpportunityPolicy",
    "OpportunityStrategyInput",
    "OpportunityStrategyResult",
    "PMCalibrationReport",
    "PMCalibrationRow",
    "StrategyReplayCase",
    "StrategyReplayObservation",
    "StrategyReplayResult",
    "StrategyStage",
    "StrategyStockContext",
    "ThemeContext",
    "TrendContinuationStrategy",
    "build_pm_calibration_report",
    "evaluate_opportunity_engine",
    "rank_strategy_results",
    "replay_opportunity_strategies",
    "strategy_registry",
]
