from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from topicpilot_api.research.core_v0_candidate_panel import (
    A1_CANDIDATE_ID,
    A2_CANDIDATE_ID,
    PANEL_EXCLUDED_EVENT,
    PANEL_WAITING_MA60,
    READY_AFTER_REC_A1,
    READY_AFTER_WS2,
    RESEARCH_MA60_AVAILABLE,
    CandidatePanelError,
    CandidatePanelInput,
    CanonicalBar,
    EvaluationAnchor,
    ForwardOutcome,
    InstrumentIdentity,
    MA60Evidence,
    PITTopicContext,
    ReferenceLineage,
    assess_execution_readiness,
    build_candidate_panel,
    build_forward_outcome_panel,
    summarize_panel_coverage,
)
from topicpilot_api.research.ws3_research_policy import (
    CONTINUITY_UNKNOWN,
    EVENT_ACTION_EXCLUDE,
    ResearchInputEvidence,
    VerifiedBreakingEvent,
    evaluate_ws3_research_eligibility,
)


def _anchor() -> EvaluationAnchor:
    return EvaluationAnchor("T-2026-04-01", date(2026, 4, 1), date(2026, 4, 1), "TPE-2026.v1")


def _instrument() -> InstrumentIdentity:
    return InstrumentIdentity(
        "instrument-1", "2330", "Example", "TPE", "ACTIVE", ("instrument://1",)
    )


def _topic() -> PITTopicContext:
    return PITTopicContext(
        "topic-1",
        "Research Topic",
        "MEMBER",
        date(2025, 1, 1),
        None,
        "topic-snapshot-2026-04-01",
        date(2026, 4, 1),
        "RESEARCH_PIT",
        ("topic://snapshot/2026-04-01",),
    )


def _ma60(*, formal: bool = True) -> MA60Evidence:
    return MA60Evidence(
        "stock.sma.close.v1",
        "SMA_CLOSE_V1",
        60,
        Decimal("100"),
        date(2026, 4, 1),
        date(2026, 1, 1),
        date(2026, 4, 1),
        60,
        "RAW_OBSERVED",
        "CONTINUITY_PASS_BOUNDED",
        "FORMAL_AVAILABLE" if formal else "IMPLEMENTATION_PENDING",
        ("ws2://ma60/2026-04-01",),
    )


def _bars(
    *, close: Decimal = Decimal("103"), high: Decimal = Decimal("105"), birth_offset: int = 5
):
    anchor = _anchor().evaluation_date
    rows: list[CanonicalBar] = []
    for index in range(60):
        session = anchor - timedelta(days=60 - index)
        bar_high = high if session == anchor - timedelta(days=birth_offset) else Decimal("101")
        rows.append(
            CanonicalBar(
                f"obs-{index}",
                session,
                Decimal("100"),
                bar_high,
                Decimal("99"),
                Decimal("100"),
                Decimal("1000"),
                True,
                session,
                (f"ohlcv://{session.isoformat()}",),
            )
        )
    rows.append(
        CanonicalBar(
            "obs-T",
            anchor,
            Decimal("106"),
            Decimal("106"),
            Decimal("102"),
            close,
            Decimal("1200"),
            True,
            anchor,
            ("ohlcv://2026-04-01",),
        )
    )
    return tuple(rows)


def _input(
    *, close: Decimal = Decimal("103"), birth_offset: int = 5, formal_ma60: bool = True, topic=True
):
    anchor = _anchor()
    return CandidatePanelInput(
        _instrument(),
        anchor,
        _bars(close=close, birth_offset=birth_offset),
        _ma60(formal=formal_ma60),
        ReferenceLineage(
            anchor.evaluation_date - timedelta(days=birth_offset), ("reference://lineage",)
        ),
        _topic() if topic else None,
    )


def test_a1_positive_case_freezes_at_t() -> None:
    panel = build_candidate_panel(_input(), A1_CANDIDATE_ID)

    assert panel.formation_state == "FORMED"
    assert panel.formation_reason == "A1_FORMED"
    assert panel.reference is not None
    assert panel.reference.value == Decimal("105")
    assert panel.reference.age_sessions == 5
    assert panel.frozen_at_t is True


def test_a1_distance_and_maturity_boundaries_are_fail_closed() -> None:
    too_far = build_candidate_panel(_input(close=Decimal("100")), A1_CANDIDATE_ID)
    immature = build_candidate_panel(_input(birth_offset=1), A1_CANDIDATE_ID)

    assert too_far.formation_reason == "A1_REFERENCE_DISTANCE_EXCEEDED"
    assert immature.formation_reason == "REFERENCE_MATURITY_LT_5"


def test_a1_close_equal_reference_and_immediate_pullback_are_not_candidates() -> None:
    equal = build_candidate_panel(_input(close=Decimal("105")), A1_CANDIDATE_ID)
    immediate = build_candidate_panel(_input(close=Decimal("103"), birth_offset=1), A1_CANDIDATE_ID)

    assert equal.formation_state == "NOT_FORMED"
    assert equal.formation_reason == "CLOSE_NOT_BELOW_REFERENCE"
    assert immediate.formation_state == "NOT_FORMED"
    assert immediate.formation_reason == "REFERENCE_MATURITY_LT_5"


def test_a2_close_confirmation_and_gap_up_are_allowed_but_high_only_is_not() -> None:
    confirmed = build_candidate_panel(_input(close=Decimal("106")), A2_CANDIDATE_ID)
    failed_close = build_candidate_panel(_input(close=Decimal("104")), A2_CANDIDATE_ID)

    assert confirmed.formation_state == "FORMED"
    assert confirmed.a2_breakout_comparison == "ABOVE"
    assert failed_close.formation_state == "NOT_FORMED"
    assert failed_close.formation_reason == "CLOSE_NOT_ABOVE_REFERENCE"


def test_missing_warmup_and_pit_context_are_candidate_date_states() -> None:
    value = _input()
    short = CandidatePanelInput(
        value.instrument,
        value.anchor,
        value.bars[-20:],
        value.ma60,
        value.reference_lineage,
        value.topic_context,
    )

    short_panel = build_candidate_panel(short, A1_CANDIDATE_ID)
    missing_topic = build_candidate_panel(_input(topic=False), A1_CANDIDATE_ID)

    assert short_panel.availability_state == "UNAVAILABLE_INSUFFICIENT_WARMUP"
    assert missing_topic.availability_state == "UNAVAILABLE_PIT_TOPIC_CONTEXT"


def test_ws2_ma60_is_consumed_as_bounded_dependency() -> None:
    panel = build_candidate_panel(_input(formal_ma60=False), A1_CANDIDATE_ID)
    readiness = assess_execution_readiness(
        panel, rec_a1_state="BLOCKED_BY_REC_A1_PROVENANCE_LEDGER_ARCHIVE_GAP", outcome_panel=None
    )

    assert panel.availability_state == PANEL_WAITING_MA60
    assert readiness.status == READY_AFTER_WS2


def test_ws3_research_mode_allows_unknown_without_formal_continuity_pass() -> None:
    value = _input()
    policy = evaluate_ws3_research_eligibility(
        ResearchInputEvidence(
            "TPE:2330",
            True,
            True,
            True,
            True,
            CONTINUITY_UNKNOWN,
        )
    )
    research_ma60 = MA60Evidence(
        "stock.sma.close.v1",
        "SMA_CLOSE_V1",
        60,
        Decimal("100"),
        date(2026, 4, 1),
        date(2026, 1, 1),
        date(2026, 4, 1),
        60,
        "RAW_OBSERVED",
        CONTINUITY_UNKNOWN,
        RESEARCH_MA60_AVAILABLE,
        ("ws3://ma60/2026-04-01",),
    )
    panel = build_candidate_panel(
        CandidatePanelInput(
            value.instrument,
            value.anchor,
            value.bars,
            research_ma60,
            value.reference_lineage,
            value.topic_context,
            research_eligibility=policy,
        ),
        A1_CANDIDATE_ID,
    )

    assert panel.formation_state == "FORMED"
    assert panel.ma60_state == RESEARCH_MA60_AVAILABLE
    assert panel.continuity_state == CONTINUITY_UNKNOWN
    assert panel.research_event_overlay == "NONE"
    assert panel.research_policy_state == policy.state


def test_ws3_research_mode_excludes_verified_breaking_event() -> None:
    value = _input()
    policy = evaluate_ws3_research_eligibility(
        ResearchInputEvidence(
            "TPE:2330",
            True,
            True,
            True,
            True,
            CONTINUITY_UNKNOWN,
            (
                VerifiedBreakingEvent(
                    "event-1",
                    "CAPITAL_REDUCTION",
                    date(2026, 3, 17),
                    EVENT_ACTION_EXCLUDE,
                    ("official://event/1",),
                ),
            ),
        )
    )
    panel = build_candidate_panel(
        CandidatePanelInput(
            value.instrument,
            value.anchor,
            value.bars,
            value.ma60,
            value.reference_lineage,
            value.topic_context,
            research_eligibility=policy,
        ),
        A1_CANDIDATE_ID,
    )

    assert panel.availability_state == PANEL_EXCLUDED_EVENT
    assert panel.formation_state == "NOT_FORMED"
    assert panel.research_event_overlay == EVENT_ACTION_EXCLUDE
    assert panel.formation_reason == "VERIFIED_BREAKING_EVENT_INTERSECTS_WINDOW"


def test_forward_outcomes_are_separate_and_never_flow_backward() -> None:
    panel = build_candidate_panel(_input(), A1_CANDIDATE_ID)
    outcomes = tuple(
        ForwardOutcome(
            horizon,
            _anchor().evaluation_date + timedelta(days=horizon),
            Decimal("104"),
            (f"outcome://{horizon}",),
        )
        for horizon in (1, 3, 5, 10)
    )
    outcome_panel = build_forward_outcome_panel(panel, outcomes)
    readiness = assess_execution_readiness(
        panel,
        rec_a1_state="BLOCKED_BY_REC_A1_PROVENANCE_LEDGER_ARCHIVE_GAP",
        outcome_panel=outcome_panel,
    )

    assert outcome_panel.status == "AVAILABLE"
    assert outcome_panel.as_dict()["outcomesFlowBackward"] is False
    assert readiness.status == READY_AFTER_REC_A1
    assert panel.formation_reason == "A1_FORMED"


def test_lookahead_bar_or_outcome_is_rejected() -> None:
    value = _input()
    future_bar = CanonicalBar(
        "future",
        date(2026, 4, 2),
        Decimal("100"),
        Decimal("101"),
        Decimal("99"),
        Decimal("100"),
        Decimal("1000"),
        True,
        date(2026, 4, 2),
        ("ohlcv://future",),
    )
    with pytest.raises(CandidatePanelError, match="NO_LOOKAHEAD_INPUT"):
        build_candidate_panel(
            CandidatePanelInput(
                value.instrument,
                value.anchor,
                (*value.bars, future_bar),
                value.ma60,
                value.reference_lineage,
                value.topic_context,
            ),
            A1_CANDIDATE_ID,
        )

    panel = build_candidate_panel(value, A1_CANDIDATE_ID)
    with pytest.raises(CandidatePanelError, match="NO_LOOKAHEAD_OUTCOME"):
        build_forward_outcome_panel(
            panel,
            (ForwardOutcome(1, value.anchor.evaluation_date, Decimal("104"), ("outcome://bad",)),),
        )


def test_coverage_summary_has_counts_only_and_no_performance_metrics() -> None:
    panels = (
        build_candidate_panel(_input(), A1_CANDIDATE_ID),
        build_candidate_panel(_input(close=Decimal("106")), A2_CANDIDATE_ID),
    )
    summary = summarize_panel_coverage(panels)

    assert summary["metricsGenerated"] is False
    assert summary["candidateCounts"][A1_CANDIDATE_ID]["formedCount"] == 1
    assert summary["candidateCounts"][A2_CANDIDATE_ID]["formedCount"] == 1
