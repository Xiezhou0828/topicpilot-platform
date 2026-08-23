from __future__ import annotations

from datetime import date

from topicpilot_api.research.core_v0_candidate_panel import MA60Evidence
from topicpilot_api.research.ws3_research_policy import (
    CONTINUITY_FAIL,
    CONTINUITY_PASS_BOUNDED,
    CONTINUITY_UNKNOWN,
    EVENT_ACTION_ANNOTATE,
    EVENT_ACTION_CORRECT,
    EVENT_ACTION_EXCLUDE,
    RESEARCH_ELIGIBLE_NO_KNOWN_EVENT,
    RESEARCH_ELIGIBLE_WITH_ANNOTATION,
    RESEARCH_ELIGIBLE_WITH_CORRECTION,
    RESEARCH_EXCLUDED_BY_EVENT,
    RESEARCH_UNAVAILABLE,
    RESEARCH_UNAVAILABLE_CONTINUITY_FAIL,
    ResearchInputEvidence,
    VerifiedBreakingEvent,
    evaluate_ws3_research_eligibility,
)


def _evidence(
    *,
    continuity_state: str,
    events: tuple[VerifiedBreakingEvent, ...] = (),
    real_ohlcv_available: bool = True,
    valid_instrument_identity: bool = True,
    valid_source_lineage: bool = True,
    sufficient_observations: bool = True,
) -> ResearchInputEvidence:
    return ResearchInputEvidence(
        instrument_identity="TPE:2330",
        real_ohlcv_available=real_ohlcv_available,
        valid_instrument_identity=valid_instrument_identity,
        valid_source_lineage=valid_source_lineage,
        sufficient_observations=sufficient_observations,
        continuity_state=continuity_state,
        known_verified_events=events,
    )


def _event(action: str, event_id: str = "event-1") -> VerifiedBreakingEvent:
    return VerifiedBreakingEvent(
        event_id,
        "CAPITAL_REDUCTION",
        date(2026, 3, 17),
        action,
        ("official://event/1",),
    )


def test_normal_real_history_proceeds_without_affirmative_no_event() -> None:
    result = evaluate_ws3_research_eligibility(
        _evidence(continuity_state=CONTINUITY_PASS_BOUNDED)
    )

    assert result.state == RESEARCH_ELIGIBLE_NO_KNOWN_EVENT
    assert result.eligible is True
    assert result.event_overlay == "NONE"
    assert result.reason_codes == ("NO_KNOWN_VERIFIED_BREAKING_EVENT",)
    assert result.as_dict()["affirmativeNoEventRequired"] is False
    assert result.as_dict()["coveredNoEventCreated"] is False


def test_verified_breaking_event_is_excluded_and_not_ignored() -> None:
    result = evaluate_ws3_research_eligibility(
        _evidence(continuity_state=CONTINUITY_UNKNOWN, events=(_event(EVENT_ACTION_EXCLUDE),))
    )

    assert result.state == RESEARCH_EXCLUDED_BY_EVENT
    assert result.eligible is False
    assert result.event_overlay == EVENT_ACTION_EXCLUDE
    assert result.verified_event_ids == ("event-1",)


def test_verified_event_correction_and_annotation_are_preserved() -> None:
    corrected = evaluate_ws3_research_eligibility(
        _evidence(continuity_state=CONTINUITY_UNKNOWN, events=(_event(EVENT_ACTION_CORRECT),))
    )
    annotated = evaluate_ws3_research_eligibility(
        _evidence(continuity_state=CONTINUITY_UNKNOWN, events=(_event(EVENT_ACTION_ANNOTATE),))
    )

    assert corrected.state == RESEARCH_ELIGIBLE_WITH_CORRECTION
    assert corrected.eligible is True
    assert corrected.event_overlay == EVENT_ACTION_CORRECT
    assert annotated.state == RESEARCH_ELIGIBLE_WITH_ANNOTATION
    assert annotated.eligible is True
    assert annotated.event_overlay == EVENT_ACTION_ANNOTATE


def test_continuity_unknown_is_preserved_but_does_not_block_research() -> None:
    result = evaluate_ws3_research_eligibility(
        _evidence(continuity_state=CONTINUITY_UNKNOWN)
    )

    assert result.eligible is True
    assert result.continuity_state == CONTINUITY_UNKNOWN
    assert result.as_dict()["unknownPreserved"] is True
    assert result.as_dict()["state"] != CONTINUITY_PASS_BOUNDED


def test_insufficient_ohlcv_remains_unavailable_for_actual_reason() -> None:
    result = evaluate_ws3_research_eligibility(
        _evidence(continuity_state=CONTINUITY_UNKNOWN, sufficient_observations=False)
    )

    assert result.state == RESEARCH_UNAVAILABLE
    assert result.eligible is False
    assert result.reason_codes == ("INSUFFICIENT_TECHNICAL_OBSERVATIONS",)


def test_formal_ws2_ma60_gate_is_unchanged_while_research_mode_accepts_unknown() -> None:
    evidence = MA60Evidence(
        "stock.sma.close.v1",
        "SMA_CLOSE_V1",
        60,
        "100",
        date(2026, 4, 1),
        date(2026, 1, 1),
        date(2026, 4, 1),
        60,
        "RAW_OBSERVED",
        CONTINUITY_UNKNOWN,
        "RESEARCH_AVAILABLE",
        ("ws3://ma60/2026-04-01",),
    )

    assert evidence.is_formal_consumable(date(2026, 4, 1)) is False
    assert evidence.is_research_consumable(date(2026, 4, 1)) is True


def test_continuity_fail_without_overlay_is_not_reclassified_as_research_pass() -> None:
    result = evaluate_ws3_research_eligibility(_evidence(continuity_state=CONTINUITY_FAIL))

    assert result.state == RESEARCH_UNAVAILABLE_CONTINUITY_FAIL
    assert result.eligible is False
    assert result.continuity_state == CONTINUITY_FAIL
