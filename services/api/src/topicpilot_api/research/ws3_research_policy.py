"""Owner-scoped event-aware research admissibility for WS3 Core V0.

This adapter is deliberately narrower than the WS2 formal publication gate.
It permits research to use real observed OHLCV when continuity is UNKNOWN, as
long as identity, lineage, and technical observations are valid.  It never
turns UNKNOWN into PASS, never creates COVERED_NO_EVENT, and never changes
formal WS2 publication semantics.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

WS3_RESEARCH_POLICY = "EVENT_AWARE_RESEARCH"
WS3_RESEARCH_POLICY_VERSION = "ws3-event-aware-research.v1"

CONTINUITY_PASS_BOUNDED = "CONTINUITY_PASS_BOUNDED"
CONTINUITY_FAIL = "CONTINUITY_FAIL"
CONTINUITY_UNKNOWN = "CONTINUITY_UNKNOWN"
CONTINUITY_STATES = frozenset(
    {CONTINUITY_PASS_BOUNDED, CONTINUITY_FAIL, CONTINUITY_UNKNOWN}
)

EVENT_ACTION_EXCLUDE = "EXCLUDE"
EVENT_ACTION_CORRECT = "CORRECT"
EVENT_ACTION_ANNOTATE = "ANNOTATE"
EVENT_ACTIONS = frozenset(
    {EVENT_ACTION_EXCLUDE, EVENT_ACTION_CORRECT, EVENT_ACTION_ANNOTATE}
)

RESEARCH_ELIGIBLE = "RESEARCH_ELIGIBLE"
RESEARCH_ELIGIBLE_NO_KNOWN_EVENT = "RESEARCH_ELIGIBLE_NO_KNOWN_VERIFIED_BREAKING_EVENT"
RESEARCH_ELIGIBLE_WITH_CORRECTION = "RESEARCH_ELIGIBLE_WITH_CORRECTION"
RESEARCH_ELIGIBLE_WITH_ANNOTATION = "RESEARCH_ELIGIBLE_WITH_ANNOTATION"
RESEARCH_EXCLUDED_BY_EVENT = "RESEARCH_EXCLUDED_BY_VERIFIED_EVENT"
RESEARCH_UNAVAILABLE = "RESEARCH_UNAVAILABLE"
RESEARCH_UNAVAILABLE_CONTINUITY_FAIL = "RESEARCH_UNAVAILABLE_CONTINUITY_FAIL"


class WS3ResearchPolicyError(ValueError):
    """Raised when research evidence is outside the bounded policy contract."""


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise WS3ResearchPolicyError(f"{field} must be a trimmed non-empty string")
    return value


def _lineage(values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(_text(value, "source_lineage") for value in values)
    if not result:
        raise WS3ResearchPolicyError("source_lineage must not be empty")
    return result


@dataclass(frozen=True)
class VerifiedBreakingEvent:
    """A known verified event already classified by existing authority."""

    event_id: str
    event_type: str
    effective_date: date
    action: str
    source_lineage: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.event_id, "event_id")
        _text(self.event_type, "event_type")
        if self.action not in EVENT_ACTIONS:
            raise WS3ResearchPolicyError(f"unsupported verified event action: {self.action}")
        object.__setattr__(self, "source_lineage", _lineage(self.source_lineage))

    def as_dict(self) -> dict[str, object]:
        return {
            "eventId": self.event_id,
            "eventType": self.event_type,
            "effectiveDate": self.effective_date.isoformat(),
            "action": self.action,
            "sourceLineage": list(self.source_lineage),
        }


@dataclass(frozen=True)
class ResearchInputEvidence:
    """Minimum real-input facts required by the WS3 research policy."""

    instrument_identity: str
    real_ohlcv_available: bool
    valid_instrument_identity: bool
    valid_source_lineage: bool
    sufficient_observations: bool
    continuity_state: str
    known_verified_events: tuple[VerifiedBreakingEvent, ...] = ()

    def __post_init__(self) -> None:
        _text(self.instrument_identity, "instrument_identity")
        if self.continuity_state not in CONTINUITY_STATES:
            raise WS3ResearchPolicyError(
                f"unsupported continuity state: {self.continuity_state}"
            )
        if any(not isinstance(value, bool) for value in (
            self.real_ohlcv_available,
            self.valid_instrument_identity,
            self.valid_source_lineage,
            self.sufficient_observations,
        )):
            raise WS3ResearchPolicyError("research input availability flags must be boolean")
        object.__setattr__(self, "known_verified_events", tuple(self.known_verified_events))


@dataclass(frozen=True)
class ResearchEligibility:
    """Deterministic WS3-only research routing result."""

    instrument_identity: str
    state: str
    eligible: bool
    continuity_state: str
    event_overlay: str
    reason_codes: tuple[str, ...]
    verified_event_ids: tuple[str, ...]
    policy: str = WS3_RESEARCH_POLICY
    policy_version: str = WS3_RESEARCH_POLICY_VERSION

    def as_dict(self) -> dict[str, object]:
        return {
            "instrumentIdentity": self.instrument_identity,
            "policy": self.policy,
            "policyVersion": self.policy_version,
            "state": self.state,
            "eligible": self.eligible,
            "continuityState": self.continuity_state,
            "eventOverlay": self.event_overlay,
            "reasonCodes": list(self.reason_codes),
            "verifiedEventIds": list(self.verified_event_ids),
            "unknownPreserved": self.continuity_state == CONTINUITY_UNKNOWN,
            "affirmativeNoEventRequired": False,
            "coveredNoEventCreated": False,
        }


def _unavailable(
    evidence: ResearchInputEvidence,
    state: str,
    reason: str,
) -> ResearchEligibility:
    return ResearchEligibility(
        evidence.instrument_identity,
        state,
        False,
        evidence.continuity_state,
        "NONE",
        (reason,),
        tuple(event.event_id for event in evidence.known_verified_events),
    )


def evaluate_ws3_research_eligibility(
    evidence: ResearchInputEvidence,
) -> ResearchEligibility:
    """Apply the Owner's event-aware research policy without authority promotion."""

    if not evidence.real_ohlcv_available:
        return _unavailable(evidence, RESEARCH_UNAVAILABLE, "REAL_OHLCV_UNAVAILABLE")
    if not evidence.valid_instrument_identity:
        return _unavailable(evidence, RESEARCH_UNAVAILABLE, "INVALID_INSTRUMENT_IDENTITY")
    if not evidence.valid_source_lineage:
        return _unavailable(evidence, RESEARCH_UNAVAILABLE, "INVALID_SOURCE_LINEAGE")
    if not evidence.sufficient_observations:
        return _unavailable(evidence, RESEARCH_UNAVAILABLE, "INSUFFICIENT_TECHNICAL_OBSERVATIONS")

    events = evidence.known_verified_events
    event_ids = tuple(event.event_id for event in events)
    if evidence.continuity_state == CONTINUITY_FAIL and not events:
        return _unavailable(
            evidence,
            RESEARCH_UNAVAILABLE_CONTINUITY_FAIL,
            "CONTINUITY_FAIL_WITHOUT_RESEARCH_OVERLAY",
        )

    if any(event.action == EVENT_ACTION_EXCLUDE for event in events):
        return ResearchEligibility(
            evidence.instrument_identity,
            RESEARCH_EXCLUDED_BY_EVENT,
            False,
            evidence.continuity_state,
            EVENT_ACTION_EXCLUDE,
            ("VERIFIED_BREAKING_EVENT_INTERSECTS_WINDOW",),
            event_ids,
        )
    if any(event.action == EVENT_ACTION_CORRECT for event in events):
        return ResearchEligibility(
            evidence.instrument_identity,
            RESEARCH_ELIGIBLE_WITH_CORRECTION,
            True,
            evidence.continuity_state,
            EVENT_ACTION_CORRECT,
            ("VERIFIED_BREAKING_EVENT_CORRECTION_APPLIED_UPSTREAM",),
            event_ids,
        )
    if any(event.action == EVENT_ACTION_ANNOTATE for event in events):
        return ResearchEligibility(
            evidence.instrument_identity,
            RESEARCH_ELIGIBLE_WITH_ANNOTATION,
            True,
            evidence.continuity_state,
            EVENT_ACTION_ANNOTATE,
            ("VERIFIED_BREAKING_EVENT_ANNOTATION_ATTACHED",),
            event_ids,
        )

    return ResearchEligibility(
        evidence.instrument_identity,
        RESEARCH_ELIGIBLE_NO_KNOWN_EVENT,
        True,
        evidence.continuity_state,
        "NONE",
        ("NO_KNOWN_VERIFIED_BREAKING_EVENT",),
        (),
    )


__all__ = [
    "CONTINUITY_FAIL",
    "CONTINUITY_PASS_BOUNDED",
    "CONTINUITY_UNKNOWN",
    "EVENT_ACTION_ANNOTATE",
    "EVENT_ACTION_CORRECT",
    "EVENT_ACTION_EXCLUDE",
    "RESEARCH_ELIGIBLE_NO_KNOWN_EVENT",
    "RESEARCH_ELIGIBLE_WITH_ANNOTATION",
    "RESEARCH_ELIGIBLE_WITH_CORRECTION",
    "RESEARCH_EXCLUDED_BY_EVENT",
    "RESEARCH_UNAVAILABLE",
    "RESEARCH_UNAVAILABLE_CONTINUITY_FAIL",
    "WS3_RESEARCH_POLICY",
    "WS3_RESEARCH_POLICY_VERSION",
    "ResearchEligibility",
    "ResearchInputEvidence",
    "VerifiedBreakingEvent",
    "WS3ResearchPolicyError",
    "evaluate_ws3_research_eligibility",
]
