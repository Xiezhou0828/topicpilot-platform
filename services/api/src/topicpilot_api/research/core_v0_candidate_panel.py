"""Research-only Core V0 A1/A2 candidate panels and readiness.

This module is deliberately persistence-free.  It consumes explicit canonical
evidence, applies the frozen A1/A2 formation policy, and returns bounded
availability/readiness states.  It does not fetch data, calculate production
technical indicators, publish an API, or evaluate performance.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256

from .ws3_research_policy import (
    RESEARCH_EXCLUDED_BY_EVENT,
    ResearchEligibility,
)

CORE_V0_PROTOCOL = "core-v0-walk-forward.v1"
A1_CANDIDATE_ID = "CORE_V0_A1_PRE_BREAKOUT"
A2_CANDIDATE_ID = "CORE_V0_A2_CONFIRMED_BREAKOUT"
A1_DEFINITION_VERSION = "core-v0-a1-pre-breakout.v1"
A2_DEFINITION_VERSION = "core-v0-a2-confirmed-breakout.v1"
REFERENCE_POLICY_ID = "PRIOR_20_ACCEPTED_SESSION_HIGH"
PANEL_CONTRACT_VERSION = "core-v0-candidate-panel.v1"
REFERENCE_WINDOW_SESSIONS = 20
REFERENCE_MATURITY_SESSIONS = 5
MIN_PRIOR_SESSIONS = 60
A1_MAX_REFERENCE_DISTANCE = Decimal("0.03")
OUTCOME_HORIZONS = (1, 3, 5, 10)

FORMED = "FORMED"
NOT_FORMED = "NOT_FORMED"
PANEL_AVAILABLE = "AVAILABLE_FORMATION_EVIDENCE"
PANEL_MISSING_WARMUP = "UNAVAILABLE_INSUFFICIENT_WARMUP"
PANEL_MISSING_MA60 = "UNAVAILABLE_MA60"
PANEL_WAITING_MA60 = "WAITING_FOR_FORMAL_WS2_MA60_EVIDENCE"
PANEL_MISSING_TOPIC = "UNAVAILABLE_PIT_TOPIC_CONTEXT"
PANEL_MISSING_REFERENCE = "UNAVAILABLE_REFERENCE_MATURITY"
PANEL_EXCLUDED_EVENT = "EXCLUDED_BY_VERIFIED_EVENT"
RESEARCH_MA60_AVAILABLE = "RESEARCH_AVAILABLE"

READY = "READY_FOR_CORE_V0_WALK_FORWARD_EXECUTION"
READY_AFTER_WS2 = "READY_AFTER_WS2_MA60_PUBLICATION"
READY_AFTER_OUTCOMES = "READY_AFTER_FORWARD_OUTCOME_PANEL"
READY_AFTER_REC_A1 = "READY_AFTER_REC_A1_PROVENANCE_RECONCILIATION"
BLOCKED_PANEL = "BLOCKED_BY_CANDIDATE_DATE_PANEL"

OUTCOMES_AVAILABLE = "AVAILABLE"
OUTCOMES_INSUFFICIENT = "UNAVAILABLE_INSUFFICIENT_FORWARD_WINDOW"
OUTCOMES_LINEAGE = "UNAVAILABLE_LINEAGE"
OUTCOMES_EXCLUDED = "EXCLUDED_BY_FROZEN_REC_A1_INTEGRITY_POLICY"


class CandidatePanelError(ValueError):
    """Raised when supplied evidence violates the panel boundary."""


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CandidatePanelError(f"{field} must be a trimmed non-empty string")
    return value


def _decimal(value: object, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise CandidatePanelError(f"{field} must be a finite decimal")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CandidatePanelError(f"{field} must be a finite decimal") from exc
    if not parsed.is_finite():
        raise CandidatePanelError(f"{field} must be a finite decimal")
    return parsed


def _lineage(value: Iterable[str], field: str) -> tuple[str, ...]:
    values = tuple(_text(item, field) for item in value)
    if not values:
        raise CandidatePanelError(f"{field} must not be empty")
    return values


def _date_text(value: date | None) -> str | None:
    return value.isoformat() if value is not None else None


@dataclass(frozen=True)
class InstrumentIdentity:
    instrument_id: str
    symbol: str
    name: str
    market: str
    lifecycle_state: str
    source_lineage: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in ("instrument_id", "symbol", "name", "market", "lifecycle_state"):
            _text(getattr(self, field), field)
        object.__setattr__(self, "source_lineage", _lineage(self.source_lineage, "source_lineage"))


@dataclass(frozen=True)
class EvaluationAnchor:
    evaluation_session: str
    evaluation_date: date
    as_of: date
    market_calendar_version: str

    def __post_init__(self) -> None:
        _text(self.evaluation_session, "evaluation_session")
        _text(self.market_calendar_version, "market_calendar_version")
        if self.as_of != self.evaluation_date:
            raise CandidatePanelError("as_of must equal evaluation_date T")


@dataclass(frozen=True)
class CanonicalBar:
    observation_id: str
    session_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    accepted: bool
    as_of: date
    source_lineage: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.observation_id, "observation_id")
        if self.as_of > self.session_date:
            raise CandidatePanelError("bar as_of cannot be after its session_date")
        if not isinstance(self.accepted, bool):
            raise CandidatePanelError("accepted must be boolean")
        for field in ("open", "high", "low", "close", "volume"):
            object.__setattr__(self, field, _decimal(getattr(self, field), field))
        object.__setattr__(self, "source_lineage", _lineage(self.source_lineage, "source_lineage"))


@dataclass(frozen=True)
class PITTopicContext:
    topic_id: str
    topic_name: str
    membership_role: str
    valid_from: date
    valid_to: date | None
    snapshot_id: str
    as_of: date
    publication_mode: str
    source_lineage: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in (
            "topic_id",
            "topic_name",
            "membership_role",
            "snapshot_id",
            "publication_mode",
        ):
            _text(getattr(self, field), field)
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise CandidatePanelError("topic validity interval is inverted")
        object.__setattr__(self, "source_lineage", _lineage(self.source_lineage, "source_lineage"))

    def is_valid_at(self, evaluation_date: date) -> bool:
        return (
            self.as_of <= evaluation_date
            and self.valid_from <= evaluation_date
            and (self.valid_to is None or evaluation_date <= self.valid_to)
        )


@dataclass(frozen=True)
class MA60Evidence:
    indicator_id: str
    algorithm_id: str
    period: int
    value: Decimal | None
    as_of: date
    first_observation_date: date | None
    last_observation_date: date | None
    observation_count: int
    price_basis: str
    continuity_state: str
    publication_state: str
    source_lineage: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in (
            "indicator_id",
            "algorithm_id",
            "price_basis",
            "continuity_state",
            "publication_state",
        ):
            _text(getattr(self, field), field)
        if self.period != 60 or self.observation_count < 0:
            raise CandidatePanelError("MA60 period/count is invalid")
        if self.value is not None:
            object.__setattr__(self, "value", _decimal(self.value, "MA60 value"))
        object.__setattr__(self, "source_lineage", _lineage(self.source_lineage, "source_lineage"))

    def is_formal_consumable(self, evaluation_date: date) -> bool:
        return (
            self.indicator_id == "stock.sma.close.v1"
            and self.algorithm_id == "SMA_CLOSE_V1"
            and self.period == 60
            and self.value is not None
            and self.as_of == evaluation_date
            and self.first_observation_date is not None
            and self.last_observation_date == evaluation_date
            and self.observation_count >= 60
            and self.price_basis == "RAW_OBSERVED"
            and self.continuity_state == "CONTINUITY_PASS_BOUNDED"
            and self.publication_state == "FORMAL_AVAILABLE"
            and bool(self.source_lineage)
        )

    def is_research_consumable(self, evaluation_date: date) -> bool:
        """Accept real MA60 evidence for WS3 without weakening formal WS2."""

        return (
            self.indicator_id == "stock.sma.close.v1"
            and self.algorithm_id == "SMA_CLOSE_V1"
            and self.period == 60
            and self.value is not None
            and self.as_of == evaluation_date
            and self.first_observation_date is not None
            and self.last_observation_date == evaluation_date
            and self.observation_count >= 60
            and self.price_basis == "RAW_OBSERVED"
            and self.continuity_state in {"CONTINUITY_PASS_BOUNDED", "CONTINUITY_UNKNOWN"}
            and (
                self.publication_state == RESEARCH_MA60_AVAILABLE
                or (
                    self.publication_state == "FORMAL_AVAILABLE"
                    and self.continuity_state == "CONTINUITY_PASS_BOUNDED"
                )
            )
            and bool(self.source_lineage)
        )


@dataclass(frozen=True)
class ReferenceLineage:
    birth_session: date | None
    source_lineage: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_lineage", _lineage(self.source_lineage, "reference_lineage")
        )


@dataclass(frozen=True)
class CandidatePanelInput:
    instrument: InstrumentIdentity
    anchor: EvaluationAnchor
    bars: tuple[CanonicalBar, ...]
    ma60: MA60Evidence | None
    reference_lineage: ReferenceLineage | None
    topic_context: PITTopicContext | None
    topic_context_required: bool = True
    panel_contract_version: str = PANEL_CONTRACT_VERSION
    research_eligibility: ResearchEligibility | None = None

    def __post_init__(self) -> None:
        if self.panel_contract_version != PANEL_CONTRACT_VERSION:
            raise CandidatePanelError("unsupported candidate panel contract")
        if not self.bars:
            raise CandidatePanelError("bars must not be empty")


@dataclass(frozen=True)
class ReferenceEvidence:
    policy_id: str
    value: Decimal
    window_session_dates: tuple[date, ...]
    window_observation_ids: tuple[str, ...]
    birth_session: date | None
    age_sessions: int | None
    mature: bool | None
    source_lineage: tuple[str, ...]


@dataclass(frozen=True)
class CandidatePanelRecord:
    contract_version: str
    candidate_record_id: str
    candidate_id: str
    candidate_version: str
    instrument: InstrumentIdentity
    anchor: EvaluationAnchor
    availability_state: str
    formation_state: str
    formation_reason: str
    l1_state: str
    ma60_state: str
    reference: ReferenceEvidence | None
    close: Decimal | None
    open: Decimal | None
    a1_distance: Decimal | None
    a2_breakout_comparison: str | None
    topic_context_state: str
    candidate_inputs: tuple[tuple[str, str], ...]
    source_lineage: tuple[str, ...]
    frozen_at_t: bool
    research_policy_state: str = "NOT_APPLIED"
    research_event_overlay: str = "NONE"
    continuity_state: str = "NOT_EVALUATED"

    def as_dict(self) -> dict[str, object]:
        reference = None
        if self.reference is not None:
            reference = {
                "policyId": self.reference.policy_id,
                "value": str(self.reference.value),
                "windowSessionDates": [
                    _date_text(value) for value in self.reference.window_session_dates
                ],
                "windowObservationIds": list(self.reference.window_observation_ids),
                "birthSession": _date_text(self.reference.birth_session),
                "ageSessions": self.reference.age_sessions,
                "mature": self.reference.mature,
                "sourceLineage": list(self.reference.source_lineage),
            }
        return {
            "contractVersion": self.contract_version,
            "candidateRecordId": self.candidate_record_id,
            "candidateId": self.candidate_id,
            "candidateVersion": self.candidate_version,
            "instrument": {
                "instrumentId": self.instrument.instrument_id,
                "symbol": self.instrument.symbol,
                "name": self.instrument.name,
                "market": self.instrument.market,
                "lifecycleState": self.instrument.lifecycle_state,
            },
            "evaluation": {
                "session": self.anchor.evaluation_session,
                "date": _date_text(self.anchor.evaluation_date),
                "asOf": _date_text(self.anchor.as_of),
                "calendarVersion": self.anchor.market_calendar_version,
            },
            "availabilityState": self.availability_state,
            "formationState": self.formation_state,
            "formationReason": self.formation_reason,
            "l1State": self.l1_state,
            "ma60State": self.ma60_state,
            "reference": reference,
            "close": str(self.close) if self.close is not None else None,
            "open": str(self.open) if self.open is not None else None,
            "a1Distance": str(self.a1_distance) if self.a1_distance is not None else None,
            "a2BreakoutComparison": self.a2_breakout_comparison,
            "topicContextState": self.topic_context_state,
            "candidateInputs": dict(self.candidate_inputs),
            "sourceLineage": list(self.source_lineage),
            "frozenAtT": self.frozen_at_t,
            "researchPolicyState": self.research_policy_state,
            "researchEventOverlay": self.research_event_overlay,
            "continuityState": self.continuity_state,
        }


@dataclass(frozen=True)
class ForwardOutcome:
    horizon: int
    session_date: date
    close: Decimal | None
    source_lineage: tuple[str, ...]
    integrity_state: str = "VALID"

    def __post_init__(self) -> None:
        if self.horizon not in OUTCOME_HORIZONS:
            raise CandidatePanelError("unsupported forward outcome horizon")
        if self.close is not None:
            object.__setattr__(self, "close", _decimal(self.close, "outcome close"))
        object.__setattr__(self, "source_lineage", _lineage(self.source_lineage, "outcome_lineage"))


@dataclass(frozen=True)
class ForwardOutcomePanel:
    candidate_record_id: str
    status: str
    outcomes: tuple[ForwardOutcome, ...]
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "candidateRecordId": self.candidate_record_id,
            "status": self.status,
            "reasonCodes": list(self.reason_codes),
            "outcomes": [
                {
                    "horizon": outcome.horizon,
                    "sessionDate": _date_text(outcome.session_date),
                    "close": str(outcome.close) if outcome.close is not None else None,
                    "sourceLineage": list(outcome.source_lineage),
                    "integrityState": outcome.integrity_state,
                }
                for outcome in self.outcomes
            ],
            "outcomesFlowBackward": False,
        }


@dataclass(frozen=True)
class ExecutionReadiness:
    candidate_record_id: str
    status: str
    blockers: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return self.status == READY

    def as_dict(self) -> dict[str, object]:
        return {
            "candidateRecordId": self.candidate_record_id,
            "status": self.status,
            "blockers": list(self.blockers),
            "readyForCoreV0WalkForwardExecution": self.ready,
        }


def _record_id(
    *, instrument: InstrumentIdentity, anchor: EvaluationAnchor, candidate_id: str, version: str
) -> str:
    payload = {
        "candidateId": candidate_id,
        "candidateVersion": version,
        "instrumentId": instrument.instrument_id,
        "symbol": instrument.symbol,
        "market": instrument.market,
        "evaluationSession": anchor.evaluation_session,
        "evaluationDate": anchor.evaluation_date.isoformat(),
        "asOf": anchor.as_of.isoformat(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _candidate_spec(candidate_id: str) -> tuple[str, str]:
    if candidate_id == A1_CANDIDATE_ID:
        return candidate_id, A1_DEFINITION_VERSION
    if candidate_id == A2_CANDIDATE_ID:
        return candidate_id, A2_DEFINITION_VERSION
    raise CandidatePanelError("only frozen Core V0 A1/A2 candidates are supported")


def _make_record(
    *,
    input_data: CandidatePanelInput,
    candidate_id: str,
    candidate_version: str,
    availability_state: str,
    formation_state: str,
    formation_reason: str,
    l1_state: str,
    ma60_state: str,
    reference: ReferenceEvidence | None = None,
    close: Decimal | None = None,
    open_value: Decimal | None = None,
    a1_distance: Decimal | None = None,
    a2_breakout_comparison: str | None = None,
    topic_context_state: str = "NOT_EVALUATED",
    candidate_inputs: Mapping[str, object] | None = None,
    source_lineage: Iterable[str] = (),
    research_policy_state: str | None = None,
    research_event_overlay: str | None = None,
    continuity_state: str | None = None,
) -> CandidatePanelRecord:
    values = tuple(sorted((key, str(value)) for key, value in (candidate_inputs or {}).items()))
    lineage = tuple(dict.fromkeys((*input_data.instrument.source_lineage, *source_lineage)))
    research_policy = input_data.research_eligibility
    return CandidatePanelRecord(
        contract_version=input_data.panel_contract_version,
        candidate_record_id=_record_id(
            instrument=input_data.instrument,
            anchor=input_data.anchor,
            candidate_id=candidate_id,
            version=candidate_version,
        ),
        candidate_id=candidate_id,
        candidate_version=candidate_version,
        instrument=input_data.instrument,
        anchor=input_data.anchor,
        availability_state=availability_state,
        formation_state=formation_state,
        formation_reason=formation_reason,
        l1_state=l1_state,
        ma60_state=ma60_state,
        reference=reference,
        close=close,
        open=open_value,
        a1_distance=a1_distance,
        a2_breakout_comparison=a2_breakout_comparison,
        topic_context_state=topic_context_state,
        candidate_inputs=values,
        source_lineage=tuple(dict.fromkeys(lineage)),
        frozen_at_t=formation_state == FORMED,
        research_policy_state=(
            research_policy_state
            or (research_policy.state if research_policy is not None else "NOT_APPLIED")
        ),
        research_event_overlay=(
            research_event_overlay
            or (research_policy.event_overlay if research_policy is not None else "NONE")
        ),
        continuity_state=(
            continuity_state
            or (
                research_policy.continuity_state
                if research_policy is not None
                else "NOT_EVALUATED"
            )
        ),
    )


def _reference_evidence(
    input_data: CandidatePanelInput, accepted_bars: Sequence[CanonicalBar]
) -> ReferenceEvidence:
    prior = [bar for bar in accepted_bars if bar.session_date < input_data.anchor.evaluation_date]
    if len(prior) < REFERENCE_WINDOW_SESSIONS:
        raise CandidatePanelError(
            "reference window requires 20 accepted sessions strictly before T"
        )
    window = tuple(prior[-REFERENCE_WINDOW_SESSIONS:])
    reference_value = max(bar.high for bar in window)
    lineage = input_data.reference_lineage
    birth = lineage.birth_session if lineage is not None else None
    age: int | None = None
    mature: bool | None = None
    flattened_lineage = tuple(value for bar in window for value in bar.source_lineage)
    if lineage is not None:
        flattened_lineage = tuple(dict.fromkeys((*flattened_lineage, *lineage.source_lineage)))
        if birth is not None:
            age = sum(
                1
                for bar in accepted_bars
                if bar.accepted and birth < bar.session_date <= input_data.anchor.evaluation_date
            )
            mature = age >= REFERENCE_MATURITY_SESSIONS
    return ReferenceEvidence(
        policy_id=REFERENCE_POLICY_ID,
        value=reference_value,
        window_session_dates=tuple(bar.session_date for bar in window),
        window_observation_ids=tuple(bar.observation_id for bar in window),
        birth_session=birth,
        age_sessions=age,
        mature=mature,
        source_lineage=tuple(dict.fromkeys(flattened_lineage)),
    )


def build_candidate_panel(
    input_data: CandidatePanelInput, candidate_id: str
) -> CandidatePanelRecord:
    """Build one deterministic A1/A2 candidate-date panel from explicit evidence."""

    candidate_id, candidate_version = _candidate_spec(candidate_id)
    anchor_date = input_data.anchor.evaluation_date
    bars = tuple(sorted(input_data.bars, key=lambda bar: (bar.session_date, bar.observation_id)))
    if any(bar.session_date > anchor_date or bar.as_of > anchor_date for bar in bars):
        raise CandidatePanelError("NO_LOOKAHEAD_INPUT: bar is after evaluation date T")
    accepted = tuple(bar for bar in bars if bar.accepted)
    accepted_dates = tuple(bar.session_date for bar in accepted)
    if len(accepted_dates) != len(set(accepted_dates)):
        raise CandidatePanelError("DUPLICATE_ACCEPTED_SESSION")
    evaluation_bars = tuple(bar for bar in accepted if bar.session_date == anchor_date)
    if len(evaluation_bars) != 1:
        return _make_record(
            input_data=input_data,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            availability_state="UNAVAILABLE_MISSING_EVALUATION_BAR",
            formation_state=NOT_FORMED,
            formation_reason="MISSING_OR_DUPLICATE_EVALUATION_SESSION_BAR",
            l1_state="UNAVAILABLE",
            ma60_state="UNAVAILABLE",
        )

    evaluation_bar = evaluation_bars[0]
    prior_accepted = tuple(bar for bar in accepted if bar.session_date < anchor_date)
    research_policy = input_data.research_eligibility
    research_inputs: dict[str, object] = {}
    if research_policy is not None:
        research_inputs = {
            "research_policy": research_policy.policy,
            "research_policy_version": research_policy.policy_version,
            "research_policy_state": research_policy.state,
            "research_event_overlay": research_policy.event_overlay,
            "research_continuity_state": research_policy.continuity_state,
            "research_verified_event_ids": ",".join(research_policy.verified_event_ids),
        }
    common_inputs = {
        "evaluation_session": input_data.anchor.evaluation_session,
        "evaluation_date": anchor_date.isoformat(),
        "as_of": input_data.anchor.as_of.isoformat(),
        "reference_policy_id": REFERENCE_POLICY_ID,
        "reference_window_sessions": REFERENCE_WINDOW_SESSIONS,
        "evaluation_session_excluded_from_reference": True,
        "candidate_frozen_at_T": True,
        **research_inputs,
    }
    bar_lineage = tuple(value for bar in accepted for value in bar.source_lineage)
    if research_policy is not None and not research_policy.eligible:
        excluded = research_policy.state == RESEARCH_EXCLUDED_BY_EVENT
        return _make_record(
            input_data=input_data,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            availability_state=PANEL_EXCLUDED_EVENT if excluded else research_policy.state,
            formation_state=NOT_FORMED,
            formation_reason=research_policy.reason_codes[0],
            l1_state="UNAVAILABLE",
            ma60_state="NOT_EVALUATED",
            close=evaluation_bar.close,
            open_value=evaluation_bar.open,
            candidate_inputs=common_inputs,
            source_lineage=bar_lineage,
        )
    if len(prior_accepted) < MIN_PRIOR_SESSIONS:
        return _make_record(
            input_data=input_data,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            availability_state=PANEL_MISSING_WARMUP,
            formation_state=NOT_FORMED,
            formation_reason="MINIMUM_PRIOR_CANONICAL_SESSIONS_NOT_MET",
            l1_state="UNAVAILABLE_INSUFFICIENT_WARMUP",
            ma60_state="NOT_EVALUATED",
            close=evaluation_bar.close,
            open_value=evaluation_bar.open,
            candidate_inputs={**common_inputs, "prior_accepted_session_count": len(prior_accepted)},
            source_lineage=bar_lineage,
        )

    topic_state = "NOT_REQUIRED"
    topic_lineage: tuple[str, ...] = ()
    if input_data.topic_context_required:
        if input_data.topic_context is None or not input_data.topic_context.is_valid_at(
            anchor_date
        ):
            return _make_record(
                input_data=input_data,
                candidate_id=candidate_id,
                candidate_version=candidate_version,
                availability_state=PANEL_MISSING_TOPIC,
                formation_state=NOT_FORMED,
                formation_reason="PIT_TOPIC_CONTEXT_UNAVAILABLE_AT_T",
                l1_state="UNAVAILABLE",
                ma60_state="NOT_EVALUATED",
                close=evaluation_bar.close,
                open_value=evaluation_bar.open,
                topic_context_state=PANEL_MISSING_TOPIC,
                candidate_inputs=common_inputs,
                source_lineage=bar_lineage,
            )
        topic_state = "AVAILABLE_AT_T"
        topic_lineage = input_data.topic_context.source_lineage

    try:
        reference = _reference_evidence(input_data, accepted)
    except CandidatePanelError:
        return _make_record(
            input_data=input_data,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            availability_state=PANEL_MISSING_REFERENCE,
            formation_state=NOT_FORMED,
            formation_reason="REFERENCE_WINDOW_UNAVAILABLE",
            l1_state="UNAVAILABLE",
            ma60_state="NOT_EVALUATED",
            close=evaluation_bar.close,
            open_value=evaluation_bar.open,
            topic_context_state=topic_state,
            candidate_inputs=common_inputs,
            source_lineage=(*bar_lineage, *topic_lineage),
        )

    if input_data.reference_lineage is None or reference.birth_session is None:
        return _make_record(
            input_data=input_data,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            availability_state=PANEL_MISSING_REFERENCE,
            formation_state=NOT_FORMED,
            formation_reason="REFERENCE_MATURITY_UNAVAILABLE",
            l1_state="UNAVAILABLE",
            ma60_state="NOT_EVALUATED",
            reference=reference,
            close=evaluation_bar.close,
            open_value=evaluation_bar.open,
            topic_context_state=topic_state,
            candidate_inputs={**common_inputs, "reference_value": str(reference.value)},
            source_lineage=(*bar_lineage, *topic_lineage, *reference.source_lineage),
        )

    if input_data.ma60 is None:
        return _make_record(
            input_data=input_data,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            availability_state=PANEL_MISSING_MA60,
            formation_state=NOT_FORMED,
            formation_reason="WS2_MA60_EVIDENCE_MISSING",
            l1_state="UNAVAILABLE_MA60",
            ma60_state=PANEL_MISSING_MA60,
            reference=reference,
            close=evaluation_bar.close,
            open_value=evaluation_bar.open,
            topic_context_state=topic_state,
            candidate_inputs={**common_inputs, "reference_value": str(reference.value)},
            source_lineage=(*bar_lineage, *topic_lineage, *reference.source_lineage),
        )

    formal_ma60 = input_data.ma60.is_formal_consumable(anchor_date)
    research_ma60 = (
        research_policy is not None
        and research_policy.eligible
        and input_data.ma60.is_research_consumable(anchor_date)
    )
    if not formal_ma60 and not research_ma60:
        return _make_record(
            input_data=input_data,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            availability_state=PANEL_WAITING_MA60,
            formation_state=NOT_FORMED,
            formation_reason="WS2_FORMAL_MA60_PUBLICATION_NOT_CONSUMABLE",
            l1_state="UNAVAILABLE_MA60",
            ma60_state=PANEL_WAITING_MA60,
            reference=reference,
            close=evaluation_bar.close,
            open_value=evaluation_bar.open,
            topic_context_state=topic_state,
            candidate_inputs={**common_inputs, "reference_value": str(reference.value)},
            source_lineage=(
                *bar_lineage,
                *topic_lineage,
                *reference.source_lineage,
                *input_data.ma60.source_lineage,
            ),
        )

    ma60_state = "FORMAL_AVAILABLE" if formal_ma60 else RESEARCH_MA60_AVAILABLE
    l1_state = "ELIGIBLE" if evaluation_bar.close >= input_data.ma60.value else "INELIGIBLE_MA60"
    if l1_state != "ELIGIBLE":
        return _make_record(
            input_data=input_data,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            availability_state=PANEL_AVAILABLE,
            formation_state=NOT_FORMED,
            formation_reason="CLOSE_BELOW_MA60",
            l1_state=l1_state,
            ma60_state=ma60_state,
            reference=reference,
            close=evaluation_bar.close,
            open_value=evaluation_bar.open,
            topic_context_state=topic_state,
            candidate_inputs={**common_inputs, "reference_value": str(reference.value)},
            source_lineage=(
                *bar_lineage,
                *topic_lineage,
                *reference.source_lineage,
                *input_data.ma60.source_lineage,
            ),
        )

    if reference.mature is not True:
        reason = (
            "REFERENCE_MATURITY_UNAVAILABLE"
            if reference.mature is None
            else "REFERENCE_MATURITY_LT_5"
        )
        return _make_record(
            input_data=input_data,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            availability_state=PANEL_AVAILABLE,
            formation_state=NOT_FORMED,
            formation_reason=reason,
            l1_state=l1_state,
            ma60_state=ma60_state,
            reference=reference,
            close=evaluation_bar.close,
            open_value=evaluation_bar.open,
            topic_context_state=topic_state,
            candidate_inputs={
                **common_inputs,
                "reference_value": str(reference.value),
                "reference_age_sessions": reference.age_sessions,
            },
            source_lineage=(
                *bar_lineage,
                *topic_lineage,
                *reference.source_lineage,
                *input_data.ma60.source_lineage,
            ),
        )

    base_inputs = {
        **common_inputs,
        "reference_value": str(reference.value),
        "reference_birth_session": reference.birth_session.isoformat(),
        "reference_age_sessions": reference.age_sessions,
        "reference_mature": True,
        "l1_state": l1_state,
    }
    if candidate_id == A1_CANDIDATE_ID:
        if evaluation_bar.close >= reference.value:
            return _make_record(
                input_data=input_data,
                candidate_id=candidate_id,
                candidate_version=candidate_version,
                availability_state=PANEL_AVAILABLE,
                formation_state=NOT_FORMED,
                formation_reason="CLOSE_NOT_BELOW_REFERENCE",
                l1_state=l1_state,
                ma60_state=ma60_state,
                reference=reference,
                close=evaluation_bar.close,
                open_value=evaluation_bar.open,
                topic_context_state=topic_state,
                candidate_inputs=base_inputs,
                source_lineage=(
                    *bar_lineage,
                    *topic_lineage,
                    *reference.source_lineage,
                    *input_data.ma60.source_lineage,
                ),
            )
        distance = (reference.value - evaluation_bar.close) / reference.value
        if distance > A1_MAX_REFERENCE_DISTANCE:
            reason = "A1_REFERENCE_DISTANCE_EXCEEDED"
            formed = NOT_FORMED
        else:
            reason = "A1_FORMED"
            formed = FORMED
        return _make_record(
            input_data=input_data,
            candidate_id=candidate_id,
            candidate_version=candidate_version,
            availability_state=PANEL_AVAILABLE,
            formation_state=formed,
            formation_reason=reason,
            l1_state=l1_state,
            ma60_state=ma60_state,
            reference=reference,
            close=evaluation_bar.close,
            open_value=evaluation_bar.open,
            a1_distance=distance,
            topic_context_state=topic_state,
            candidate_inputs={**base_inputs, "a1_distance": str(distance)},
            source_lineage=(
                *bar_lineage,
                *topic_lineage,
                *reference.source_lineage,
                *input_data.ma60.source_lineage,
            ),
        )

    comparison = "ABOVE" if evaluation_bar.close > reference.value else "AT_OR_BELOW"
    formed = FORMED if comparison == "ABOVE" else NOT_FORMED
    return _make_record(
        input_data=input_data,
        candidate_id=candidate_id,
        candidate_version=candidate_version,
        availability_state=PANEL_AVAILABLE,
        formation_state=formed,
        formation_reason="A2_FORMED" if formed == FORMED else "CLOSE_NOT_ABOVE_REFERENCE",
        l1_state=l1_state,
        ma60_state=ma60_state,
        reference=reference,
        close=evaluation_bar.close,
        open_value=evaluation_bar.open,
        a2_breakout_comparison=comparison,
        topic_context_state=topic_state,
        candidate_inputs={
            **base_inputs,
            "a2_close_comparison": comparison,
            "gap_up": evaluation_bar.open > reference.value,
        },
        source_lineage=(
            *bar_lineage,
            *topic_lineage,
            *reference.source_lineage,
            *input_data.ma60.source_lineage,
        ),
    )


def build_forward_outcome_panel(
    candidate: CandidatePanelRecord, outcomes: Sequence[ForwardOutcome]
) -> ForwardOutcomePanel:
    """Build evaluation-only outcomes without mutating the frozen candidate."""

    if candidate.formation_state != FORMED:
        return ForwardOutcomePanel(
            candidate.candidate_record_id,
            OUTCOMES_INSUFFICIENT,
            (),
            ("CANDIDATE_NOT_FORMED",),
        )
    ordered = tuple(sorted(outcomes, key=lambda outcome: outcome.horizon))
    seen: set[int] = set()
    for outcome in ordered:
        if outcome.horizon in seen:
            raise CandidatePanelError("duplicate forward outcome horizon")
        seen.add(outcome.horizon)
        if outcome.session_date <= candidate.anchor.evaluation_date:
            raise CandidatePanelError("NO_LOOKAHEAD_OUTCOME: outcome must be after T")
    if any(outcome.integrity_state == OUTCOMES_EXCLUDED for outcome in ordered):
        return ForwardOutcomePanel(
            candidate.candidate_record_id,
            OUTCOMES_EXCLUDED,
            ordered,
            ("FROZEN_REC_A1_INTEGRITY_POLICY_EXCLUSION",),
        )
    if any(not outcome.source_lineage or outcome.close is None for outcome in ordered):
        return ForwardOutcomePanel(
            candidate.candidate_record_id,
            OUTCOMES_LINEAGE,
            ordered,
            ("OUTCOME_LINEAGE_OR_CLOSE_MISSING",),
        )
    missing = tuple(horizon for horizon in OUTCOME_HORIZONS if horizon not in seen)
    if missing:
        return ForwardOutcomePanel(
            candidate.candidate_record_id,
            OUTCOMES_INSUFFICIENT,
            ordered,
            (f"MISSING_HORIZONS:{','.join(str(value) for value in missing)}",),
        )
    return ForwardOutcomePanel(candidate.candidate_record_id, OUTCOMES_AVAILABLE, ordered, ())


def assess_execution_readiness(
    candidate: CandidatePanelRecord,
    *,
    rec_a1_state: str,
    outcome_panel: ForwardOutcomePanel | None,
) -> ExecutionReadiness:
    """Return a candidate-level readiness state; never emits an aggregate state."""

    if candidate.ma60_state == PANEL_WAITING_MA60:
        return ExecutionReadiness(
            candidate.candidate_record_id, READY_AFTER_WS2, (PANEL_WAITING_MA60,)
        )
    if candidate.formation_state != FORMED:
        return ExecutionReadiness(
            candidate.candidate_record_id, BLOCKED_PANEL, (candidate.formation_reason,)
        )
    if rec_a1_state != "REC_A1_EVALUATION_INTEGRITY_CONSUMABLE":
        return ExecutionReadiness(
            candidate.candidate_record_id, READY_AFTER_REC_A1, (rec_a1_state,)
        )
    if outcome_panel is None or outcome_panel.status != OUTCOMES_AVAILABLE:
        status = READY_AFTER_OUTCOMES
        blocker = (
            outcome_panel.status if outcome_panel is not None else "FORWARD_OUTCOME_PANEL_MISSING"
        )
        return ExecutionReadiness(candidate.candidate_record_id, status, (blocker,))
    return ExecutionReadiness(candidate.candidate_record_id, READY, ())


def summarize_panel_coverage(panels: Sequence[CandidatePanelRecord]) -> dict[str, object]:
    """Summarize only availability/formation counts; never calculate returns."""

    rows: dict[str, dict[str, int]] = {}
    for panel in panels:
        row = rows.setdefault(
            panel.candidate_id, {"panelCount": 0, "formedCount": 0, "unavailableCount": 0}
        )
        row["panelCount"] += 1
        row["formedCount"] += panel.formation_state == FORMED
        row["unavailableCount"] += panel.availability_state != PANEL_AVAILABLE
    return {"candidateCounts": rows, "metricsGenerated": False}


__all__ = [
    "A1_CANDIDATE_ID",
    "A1_DEFINITION_VERSION",
    "A1_MAX_REFERENCE_DISTANCE",
    "A2_CANDIDATE_ID",
    "A2_DEFINITION_VERSION",
    "BLOCKED_PANEL",
    "CORE_V0_PROTOCOL",
    "MIN_PRIOR_SESSIONS",
    "OUTCOME_HORIZONS",
    "PANEL_EXCLUDED_EVENT",
    "PANEL_WAITING_MA60",
    "READY",
    "READY_AFTER_OUTCOMES",
    "READY_AFTER_REC_A1",
    "READY_AFTER_WS2",
    "REFERENCE_MATURITY_SESSIONS",
    "REFERENCE_POLICY_ID",
    "RESEARCH_MA60_AVAILABLE",
    "CandidatePanelError",
    "CandidatePanelInput",
    "CandidatePanelRecord",
    "CanonicalBar",
    "EvaluationAnchor",
    "ExecutionReadiness",
    "ForwardOutcome",
    "ForwardOutcomePanel",
    "InstrumentIdentity",
    "MA60Evidence",
    "PITTopicContext",
    "ReferenceEvidence",
    "ReferenceLineage",
    "assess_execution_readiness",
    "build_candidate_panel",
    "build_forward_outcome_panel",
    "summarize_panel_coverage",
]
