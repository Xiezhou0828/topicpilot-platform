"""Shadow-only Opportunity pipeline over explicit, precomputed facts.

This module is deliberately provider-neutral and side-effect free.  It does
not discover stocks, calculate technical patterns, rank candidates, persist
state, or expose an API.  Callers provide the facts and the eventual approved
policy can replace the shadow composition without changing the evidence
shape.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

OPPORTUNITY_SHADOW_CONTRACT_VERSION = "opportunity-shadow.v1"
SHADOW_ONLY: Final = "SHADOW_ONLY"

PASS: Final = "PASS"
FAIL: Final = "FAIL"
UNKNOWN: Final = "UNKNOWN"
WAIT: Final = "WAIT"

EVIDENCE_OBSERVED: Final = "OBSERVED"
EVIDENCE_DERIVED: Final = "DERIVED"
EVIDENCE_UNAVAILABLE: Final = "UNAVAILABLE"

EVALUATION_READY: Final = "READY"
EVALUATION_BLOCKED: Final = "BLOCKED"
EVALUATION_DEFERRED: Final = "DEFERRED"

STATE_WARMING: Final = "升溫候選"
STATE_STRENGTHENING: Final = "轉強觀察"
STATE_SELECTED: Final = "精選機會"
STATE_WAITING_RETEST: Final = "等待回測"
STATE_INVALIDATED: Final = "失效"
OPPORTUNITY_STATES: Final = (
    STATE_WARMING,
    STATE_STRENGTHENING,
    STATE_SELECTED,
    STATE_WAITING_RETEST,
    STATE_INVALIDATED,
)

_ASSESSMENT_STATUSES: Final = frozenset({PASS, FAIL, UNKNOWN})
_ENTRY_STATUSES: Final = frozenset({PASS, WAIT, UNKNOWN})
_EVIDENCE_KINDS: Final = frozenset({EVIDENCE_OBSERVED, EVIDENCE_DERIVED, EVIDENCE_UNAVAILABLE})
_SCALAR_TYPES: Final = (str, int, float, bool)


class OpportunityShadowError(ValueError):
    """Raised when a shadow input violates its explicit contract."""


@dataclass(frozen=True)
class Evidence:
    """One structured, JSON-safe fact used to explain a shadow result."""

    code: str
    kind: str
    value: str | int | float | bool | None = None
    detail: str | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.code, "evidence code")
        if self.kind not in _EVIDENCE_KINDS:
            raise OpportunityShadowError(f"unknown evidence kind: {self.kind}")
        if self.value is not None and not isinstance(self.value, _SCALAR_TYPES):
            raise OpportunityShadowError("evidence value must be a JSON scalar or null")
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise OpportunityShadowError("evidence float value must be finite")
        if self.detail is not None:
            _require_text(self.detail, "evidence detail")
        if self.source is not None:
            _require_text(self.source, "evidence source")

    def as_dict(self) -> dict[str, str | int | float | bool | None]:
        return {
            "code": self.code,
            "kind": self.kind,
            "value": self.value,
            "detail": self.detail,
            "source": self.source,
        }


@dataclass(frozen=True)
class StageAssessment:
    """Explicit result of one upstream stage; no hidden rule is executed."""

    status: str
    reason_codes: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in _ASSESSMENT_STATUSES:
            raise OpportunityShadowError(f"unknown stage status: {self.status}")
        _require_codes(self.reason_codes, "reason_codes")

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reasonCodes": list(self.reason_codes),
            "evidence": [item.as_dict() for item in self.evidence],
        }


@dataclass(frozen=True)
class TopicOpportunityContext:
    """Topic identity and an explicit, upstream qualification assessment."""

    topic_id: str
    topic_name: str
    qualification: StageAssessment
    grade: str | None = None
    lifecycle: str | None = None
    warming_candidate: bool = False

    def __post_init__(self) -> None:
        _require_text(self.topic_id, "topic_id")
        _require_text(self.topic_name, "topic_name")
        if not isinstance(self.warming_candidate, bool):
            raise OpportunityShadowError("warming_candidate must be a boolean")
        if self.grade is not None:
            _require_text(self.grade, "grade")
        if self.lifecycle is not None:
            _require_text(self.lifecycle, "lifecycle")


@dataclass(frozen=True)
class StockOpportunityContext:
    """Stock identity and the explicit baseline eligibility facts."""

    instrument_id: str
    symbol: str
    name: str
    market: str
    topic_id: str
    price: float | None
    ma20: float | None
    ma60: float | None
    sufficient_ohlcv: bool | None

    def __post_init__(self) -> None:
        for field_name in ("instrument_id", "symbol", "name", "market", "topic_id"):
            _require_text(getattr(self, field_name), field_name)
        _require_finite_or_none(self.price, "price", minimum=0.0)
        _require_finite_or_none(self.ma20, "ma20", minimum=0.0, strictly_positive=True)
        _require_finite_or_none(self.ma60, "ma60", minimum=0.0, strictly_positive=True)
        if self.sufficient_ohlcv not in (True, False, None):
            raise OpportunityShadowError("sufficient_ohlcv must be true, false, or null")


@dataclass(frozen=True)
class TechnicalStructureFacts:
    """Precomputed technical facts; pattern definitions stay outside this module."""

    ma20_available: bool | None
    ma60_available: bool | None
    ma_direction: bool | None
    price_volume_structure: bool | None
    breakout_or_retest: bool | None
    support_available: bool | None
    bearish_break_clear: bool | None
    weak_candle_structure: bool | None
    evidence: tuple[Evidence, ...] = ()

    def assess(self) -> StageAssessment:
        fields = (
            ("TECHNICAL_20MA_AVAILABLE", self.ma20_available),
            ("TECHNICAL_60MA_AVAILABLE", self.ma60_available),
            ("TECHNICAL_MA_DIRECTION", self.ma_direction),
            ("TECHNICAL_PRICE_VOLUME_STRUCTURE", self.price_volume_structure),
            ("TECHNICAL_BREAKOUT_OR_RETEST", self.breakout_or_retest),
            ("TECHNICAL_SUPPORT_AVAILABLE", self.support_available),
            ("TECHNICAL_BEARISH_BREAK_CLEAR", self.bearish_break_clear),
            ("TECHNICAL_WEAK_CANDLE_STRUCTURE", self.weak_candle_structure),
        )
        unknown = tuple(code for code, value in fields if value is None)
        failed = tuple(code for code, value in fields if value is False)
        basic_evidence = tuple(
            Evidence(
                code,
                EVIDENCE_UNAVAILABLE if value is None else EVIDENCE_OBSERVED,
                value,
            )
            for code, value in fields
        )
        evidence = (*self.evidence, *basic_evidence)
        if unknown:
            return StageAssessment(UNKNOWN, ("TECHNICAL_STRUCTURE_INCOMPLETE", *unknown), evidence)
        if failed:
            return StageAssessment(FAIL, ("TECHNICAL_STRUCTURE_NOT_CONFIRMED", *failed), evidence)
        return StageAssessment(PASS, ("TECHNICAL_STRUCTURE_CONFIRMED",), evidence)


@dataclass(frozen=True)
class RiskGateFacts:
    """Explicit upstream risk assessment; this module does not detect risks."""

    assessment: StageAssessment


@dataclass(frozen=True)
class EntryQualityFacts:
    """Entry assessment plus optional support distance, without frozen bands."""

    status: str
    price: float | None
    support_price: float | None
    support_distance_pct: float | None = None
    reason_codes: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in _ENTRY_STATUSES:
            raise OpportunityShadowError(f"unknown entry status: {self.status}")
        _require_finite_or_none(self.price, "entry price", minimum=0.0)
        _require_finite_or_none(
            self.support_price, "support_price", minimum=0.0, strictly_positive=True
        )
        _require_finite_or_none(self.support_distance_pct, "support_distance_pct")
        _require_codes(self.reason_codes, "entry reason_codes")
        if self.status in {PASS, WAIT} and self.support_price is None:
            raise OpportunityShadowError(
                "support_price is required when Entry Quality is pass or wait"
            )
        if self.support_distance_pct is not None and self.support_price is None:
            raise OpportunityShadowError("support distance requires support_price")

    def with_distance(self) -> EntryQualityFacts:
        if self.support_distance_pct is not None:
            return self
        if self.price is None or self.support_price is None:
            return self
        distance = (self.price - self.support_price) / self.support_price * 100.0
        return EntryQualityFacts(
            self.status,
            self.price,
            self.support_price,
            distance,
            self.reason_codes,
            self.evidence,
        )


@dataclass(frozen=True)
class ChipConfirmationFacts:
    """Optional confirmation evidence; never a primary gate in shadow mode."""

    assessment: StageAssessment


@dataclass(frozen=True)
class OpportunityEvidence:
    """Evidence grouped by the four user-facing explanation questions."""

    why_selected: tuple[Evidence, ...] = ()
    confirmations: tuple[Evidence, ...] = ()
    risks: tuple[Evidence, ...] = ()
    priority_limiters: tuple[Evidence, ...] = ()

    def as_dict(self) -> dict[str, list[dict[str, object]]]:
        return {
            "whySelected": [item.as_dict() for item in self.why_selected],
            "confirmations": [item.as_dict() for item in self.confirmations],
            "risks": [item.as_dict() for item in self.risks],
            "priorityLimiters": [item.as_dict() for item in self.priority_limiters],
        }


@dataclass(frozen=True)
class OpportunityShadowInput:
    """One explicit topic/stock snapshot for shadow composition."""

    topic: TopicOpportunityContext
    stock: StockOpportunityContext
    technical: TechnicalStructureFacts
    risk: RiskGateFacts
    entry: EntryQualityFacts
    chip: ChipConfirmationFacts
    previously_tracked_state: str | None = None

    def __post_init__(self) -> None:
        if self.topic.topic_id != self.stock.topic_id:
            raise OpportunityShadowError("topic and stock topic_id must match")
        if (
            self.previously_tracked_state is not None
            and self.previously_tracked_state not in OPPORTUNITY_STATES
        ):
            raise OpportunityShadowError("previously_tracked_state is not an Opportunity state")


@dataclass(frozen=True)
class OpportunityShadowResult:
    """Non-published Opportunity state and structured explanation."""

    contract_version: str
    publication_status: str
    evaluation_status: str
    topic_id: str
    instrument_id: str
    state: str | None
    reason_codes: tuple[str, ...]
    evidence: OpportunityEvidence

    def __post_init__(self) -> None:
        if self.contract_version != OPPORTUNITY_SHADOW_CONTRACT_VERSION:
            raise OpportunityShadowError("unsupported shadow contract version")
        if self.publication_status != SHADOW_ONLY:
            raise OpportunityShadowError("shadow result cannot be published")
        if self.evaluation_status not in {
            EVALUATION_READY,
            EVALUATION_BLOCKED,
            EVALUATION_DEFERRED,
        }:
            raise OpportunityShadowError("unknown shadow evaluation status")
        if self.state is not None and self.state not in OPPORTUNITY_STATES:
            raise OpportunityShadowError("unknown Opportunity state")
        _require_codes(self.reason_codes, "result reason_codes")

    def as_dict(self) -> dict[str, object]:
        return {
            "contractVersion": self.contract_version,
            "publicationStatus": self.publication_status,
            "evaluationStatus": self.evaluation_status,
            "topicId": self.topic_id,
            "instrumentId": self.instrument_id,
            "state": self.state,
            "reasonCodes": list(self.reason_codes),
            "evidence": self.evidence.as_dict(),
        }


def build_opportunity_shadow(value: OpportunityShadowInput) -> OpportunityShadowResult:
    """Compose the explicit pipeline into a non-published shadow result.

    The only baseline hard-gate arithmetic in this shadow contract is the
    explicitly supplied objective: sufficient OHLCV, an available 20MA, and
    ``price >= 20MA``.  Technical-pattern facts, risk decisions, support
    validity, and all thresholds are supplied by callers rather than invented
    here.
    """

    entry = value.entry.with_distance()
    technical = value.technical.assess()
    common = _common_evidence(value, entry, technical)

    topic_result = _topic_gate(value, common)
    if topic_result is not None:
        return topic_result

    eligibility_result = _stock_gate(value, common)
    if eligibility_result is not None:
        return eligibility_result

    if technical.status == UNKNOWN:
        return _result(
            value,
            EVALUATION_DEFERRED,
            None,
            ("TECHNICAL_STRUCTURE_UNAVAILABLE",),
            common,
            risks=technical.evidence,
        )
    if value.risk.assessment.status == UNKNOWN:
        return _result(
            value,
            EVALUATION_DEFERRED,
            None,
            ("RISK_GATE_UNAVAILABLE",),
            common,
            risks=value.risk.assessment.evidence,
        )
    if value.risk.assessment.status == FAIL:
        state = STATE_INVALIDATED if value.previously_tracked_state is not None else None
        return _result(
            value,
            EVALUATION_BLOCKED,
            state,
            ("RISK_GATE_BLOCKED", *value.risk.assessment.reason_codes),
            common,
            risks=value.risk.assessment.evidence,
        )
    if entry.status == UNKNOWN:
        return _result(
            value,
            EVALUATION_DEFERRED,
            None,
            ("ENTRY_QUALITY_UNAVAILABLE",),
            common,
            risks=entry.evidence,
        )
    if technical.status == FAIL:
        state = STATE_WARMING if value.topic.warming_candidate else STATE_STRENGTHENING
        return _result(
            value,
            EVALUATION_READY,
            state,
            ("TECHNICAL_STRUCTURE_NEEDS_CONFIRMATION", *technical.reason_codes),
            common,
            risks=technical.evidence,
            limiters=technical.evidence,
        )
    if entry.status == WAIT:
        return _result(
            value,
            EVALUATION_READY,
            STATE_WAITING_RETEST,
            ("ENTRY_QUALITY_WAIT_FOR_RETEST", *entry.reason_codes),
            common,
            confirmations=technical.evidence,
            risks=entry.evidence,
            limiters=entry.evidence,
        )
    return _result(
        value,
        EVALUATION_READY,
        STATE_SELECTED,
        ("OPPORTUNITY_SHADOW_SELECTED",),
        common,
        confirmations=(*technical.evidence, *value.chip.assessment.evidence),
        risks=value.risk.assessment.evidence,
    )


def _topic_gate(
    value: OpportunityShadowInput, common: tuple[Evidence, ...]
) -> OpportunityShadowResult | None:
    assessment = value.topic.qualification
    if assessment.status == PASS:
        return None
    if assessment.status == FAIL:
        return _result(
            value,
            EVALUATION_BLOCKED,
            STATE_INVALIDATED if value.previously_tracked_state is not None else None,
            ("TOPIC_QUALIFICATION_FAILED", *assessment.reason_codes),
            common,
            risks=assessment.evidence,
        )
    return _result(
        value,
        EVALUATION_DEFERRED,
        None,
        ("TOPIC_QUALIFICATION_UNAVAILABLE", *assessment.reason_codes),
        common,
        risks=assessment.evidence,
    )


def _stock_gate(
    value: OpportunityShadowInput, common: tuple[Evidence, ...]
) -> OpportunityShadowResult | None:
    stock = value.stock
    if stock.sufficient_ohlcv is None:
        return _result(
            value,
            EVALUATION_DEFERRED,
            None,
            ("STOCK_OHLCV_SUFFICIENCY_UNAVAILABLE",),
            common,
            risks=(Evidence("STOCK_OHLCV_SUFFICIENT", EVIDENCE_UNAVAILABLE),),
        )
    if not stock.sufficient_ohlcv:
        return _result(
            value,
            EVALUATION_BLOCKED,
            None,
            ("STOCK_OHLCV_INSUFFICIENT",),
            common,
            risks=(Evidence("STOCK_OHLCV_SUFFICIENT", EVIDENCE_OBSERVED, False),),
        )
    if stock.ma20 is None:
        return _result(
            value,
            EVALUATION_DEFERRED,
            None,
            ("STOCK_20MA_UNAVAILABLE",),
            common,
            risks=(Evidence("STOCK_20MA", EVIDENCE_UNAVAILABLE),),
        )
    if stock.price is None:
        return _result(
            value,
            EVALUATION_DEFERRED,
            None,
            ("STOCK_PRICE_UNAVAILABLE",),
            common,
            risks=(Evidence("STOCK_PRICE", EVIDENCE_UNAVAILABLE),),
        )
    if stock.price < stock.ma20:
        return _result(
            value,
            EVALUATION_BLOCKED,
            STATE_INVALIDATED if value.previously_tracked_state is not None else None,
            ("PRICE_BELOW_20MA",),
            common,
            risks=(
                Evidence("STOCK_PRICE", EVIDENCE_OBSERVED, stock.price),
                Evidence("STOCK_20MA", EVIDENCE_OBSERVED, stock.ma20),
                Evidence("PRICE_AT_OR_ABOVE_20MA", EVIDENCE_DERIVED, False),
            ),
        )
    return None


def _common_evidence(
    value: OpportunityShadowInput,
    entry: EntryQualityFacts,
    technical: StageAssessment,
) -> tuple[Evidence, ...]:
    return (
        Evidence("TOPIC_IDENTITY", EVIDENCE_OBSERVED, value.topic.topic_id),
        Evidence("TOPIC_NAME", EVIDENCE_OBSERVED, value.topic.topic_name),
        Evidence("INSTRUMENT_IDENTITY", EVIDENCE_OBSERVED, value.stock.symbol),
        Evidence("MARKET", EVIDENCE_OBSERVED, value.stock.market),
        Evidence("TOPIC_QUALIFICATION", EVIDENCE_OBSERVED, value.topic.qualification.status),
        Evidence("TECHNICAL_STRUCTURE_STATUS", EVIDENCE_DERIVED, technical.status),
        Evidence("ENTRY_QUALITY_STATUS", EVIDENCE_OBSERVED, entry.status),
        Evidence("SUPPORT_DISTANCE_PCT", EVIDENCE_DERIVED, entry.support_distance_pct),
        Evidence("CHIP_CONFIRMATION_STATUS", EVIDENCE_OBSERVED, value.chip.assessment.status),
    )


def _result(
    value: OpportunityShadowInput,
    evaluation_status: str,
    state: str | None,
    reason_codes: tuple[str, ...],
    common: tuple[Evidence, ...],
    *,
    confirmations: tuple[Evidence, ...] = (),
    risks: tuple[Evidence, ...] = (),
    limiters: tuple[Evidence, ...] = (),
) -> OpportunityShadowResult:
    return OpportunityShadowResult(
        OPPORTUNITY_SHADOW_CONTRACT_VERSION,
        SHADOW_ONLY,
        evaluation_status,
        value.topic.topic_id,
        value.stock.instrument_id,
        state,
        _unique(reason_codes),
        OpportunityEvidence(
            why_selected=(
                (*common, *value.topic.qualification.evidence)
                if evaluation_status == EVALUATION_READY
                else ()
            ),
            confirmations=confirmations,
            risks=risks,
            priority_limiters=limiters,
        ),
    )


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise OpportunityShadowError(f"{field_name} must be a non-empty trimmed string")


def _require_codes(values: tuple[str, ...], field_name: str) -> None:
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise OpportunityShadowError(f"{field_name} must contain non-empty strings")
    if len(values) != len(set(values)):
        raise OpportunityShadowError(f"{field_name} must not contain duplicates")


def _require_finite_or_none(
    value: float | None,
    field_name: str,
    *,
    minimum: float | None = None,
    strictly_positive: bool = False,
) -> None:
    if value is None:
        return
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise OpportunityShadowError(f"{field_name} must be finite or null")
    if minimum is not None and float(value) < minimum:
        raise OpportunityShadowError(f"{field_name} must be >= {minimum}")
    if strictly_positive and float(value) <= 0:
        raise OpportunityShadowError(f"{field_name} must be > 0")


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


__all__ = [
    "EVALUATION_BLOCKED",
    "EVALUATION_DEFERRED",
    "EVALUATION_READY",
    "EVIDENCE_DERIVED",
    "EVIDENCE_OBSERVED",
    "EVIDENCE_UNAVAILABLE",
    "FAIL",
    "OPPORTUNITY_SHADOW_CONTRACT_VERSION",
    "OPPORTUNITY_STATES",
    "PASS",
    "SHADOW_ONLY",
    "STATE_INVALIDATED",
    "STATE_SELECTED",
    "STATE_STRENGTHENING",
    "STATE_WAITING_RETEST",
    "STATE_WARMING",
    "UNKNOWN",
    "WAIT",
    "ChipConfirmationFacts",
    "EntryQualityFacts",
    "Evidence",
    "OpportunityEvidence",
    "OpportunityShadowError",
    "OpportunityShadowInput",
    "OpportunityShadowResult",
    "RiskGateFacts",
    "StageAssessment",
    "StockOpportunityContext",
    "TechnicalStructureFacts",
    "TopicOpportunityContext",
    "build_opportunity_shadow",
]
