from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from topicpilot_api.formal_opportunity_universe import (
    ELIGIBLE,
    FORMAL_SOURCE_STATUS,
    INELIGIBLE,
    NOT_RUN,
    PARTIAL,
    PRICE_UNAVAILABLE,
    READY,
    UNAVAILABLE,
    UNCHANGED_NOT_EXECUTED,
    ZERO_VALID_CANDIDATES,
    FormalOpportunityUniverseConsumer,
    FormalOpportunityUniverseError,
    FormalPriceObservation,
    FormalTopicEligibility,
    FormalTopicMemberRelation,
    FormalTopicState,
)

D = date(2026, 9, 17)


def _topic(topic_id: str, *, as_of: date = D, publication: str = "FORMAL") -> FormalTopicState:
    return FormalTopicState(
        topic_id=topic_id,
        slug=topic_id,
        name=f"Topic {topic_id}",
        topic_type="LEAF",
        as_of=as_of,
        publication_status=publication,
        data_status="FORMAL_PUBLISHED" if publication == "FORMAL" else "NOT_PUBLISHED",
        snapshot_id=f"snapshot:{topic_id}:{as_of}",
        snapshot_hash=f"hash:{topic_id}:{as_of}",
        daily_strength=Decimal("0.8"),
        topic_score=Decimal("82"),
        grade="A",
        lifecycle_stage="FERMENTING",
        expected_member_count=2,
        eligible_member_count=2,
    )


def _eligibility(topic_id: str, *, status: str = ELIGIBLE) -> FormalTopicEligibility:
    return FormalTopicEligibility(
        topic_id=topic_id,
        status=status,
        as_of=D,
        policy_version="formal-topic-eligibility-owner-decision.v1",
        authority_source="formal-policy-authority",
        reason=None if status == ELIGIBLE else "owner policy excluded this fixture Topic",
    )


def _relation(
    relation_id: str,
    topic_id: str,
    instrument_id: str,
    *,
    valid_from: date = date(2026, 8, 7),
    approval: str = "APPROVED",
    market: str = "TPE",
) -> FormalTopicMemberRelation:
    return FormalTopicMemberRelation(
        relation_id=relation_id,
        topic_id=topic_id,
        instrument_id=instrument_id,
        instrument_code=instrument_id,
        instrument_name=f"Instrument {instrument_id}",
        market_code=market,
        relation_type="RELATED",
        approval_state=approval,
        valid_from=valid_from,
        structural_role="CORE" if instrument_id == "stock-a" else "RELATED",
    )


def test_multi_topic_fixture_is_partial_without_claiming_full_universe_and_keeps_provenance():
    consumer = FormalOpportunityUniverseConsumer()
    result = consumer.build(
        as_of=D,
        expected_topic_ids=("topic-a", "topic-b", "topic-c"),
        topics=(_topic("topic-a"), _topic("topic-b"), _topic("topic-c", publication="UNAVAILABLE")),
        eligibility=(
            _eligibility("topic-a"),
            _eligibility("topic-b"),
            _eligibility("topic-c", status="UNAVAILABLE"),
        ),
        relations=(
            _relation("relation-a-stock-a", "topic-a", "stock-a"),
            _relation("relation-a-stock-b", "topic-a", "stock-b"),
            _relation("relation-b-stock-a", "topic-b", "stock-a"),
        ),
    )

    assert result.status == PARTIAL
    assert result.publication_status == "UNAVAILABLE"
    assert result.full_topic_universe is False
    assert result.unique_instrument_count == 2
    assert result.member_relation_count == 3
    overlap = result.instruments[0]
    assert overlap.instrument_id == "stock-a"
    assert overlap.topic_ids == ("topic-a", "topic-b")
    assert overlap.relation_ids == ("relation-a-stock-a", "relation-b-stock-a")
    assert result.unavailable_topic_ids == ("topic-c",)
    assert result.leader_status == "UNAVAILABLE_NOT_GATING"
    assert result.strategy_status == NOT_RUN
    assert result.selector_status == NOT_RUN
    assert result.c1_c5_status == UNCHANGED_NOT_EXECUTED
    assert result.s1_s2_status == UNCHANGED_NOT_EXECUTED
    assert result.fund_c_status == "EVIDENCE_ONLY_NOT_CONSUMED"


def test_complete_formal_topic_universe_is_ready_and_deduplicated():
    result = FormalOpportunityUniverseConsumer().build(
        as_of=D,
        expected_topic_ids=("topic-a", "topic-b"),
        topics=(_topic("topic-a"), _topic("topic-b")),
        eligibility=(_eligibility("topic-a"), _eligibility("topic-b")),
        relations=(
            _relation("relation-a-stock-a", "topic-a", "stock-a"),
            _relation("relation-a-stock-b", "topic-a", "stock-b"),
            _relation("relation-b-stock-a", "topic-b", "stock-a"),
        ),
    )

    assert result.status == READY
    assert result.publication_status == "FORMAL"
    assert result.source_status == FORMAL_SOURCE_STATUS
    assert result.full_topic_universe is True
    assert result.publishable is True
    assert result.unique_instrument_count == 2
    assert result.to_dict()["counts"]["memberRelations"] == 3


def test_zero_valid_candidates_is_distinct_from_unavailable_and_excludes_unapproved_relation():
    result = FormalOpportunityUniverseConsumer().build(
        as_of=D,
        expected_topic_ids=("topic-a", "topic-b"),
        topics=(_topic("topic-a"), _topic("topic-b")),
        eligibility=(_eligibility("topic-a"), _eligibility("topic-b", status=INELIGIBLE)),
        relations=(_relation("unapproved", "topic-a", "stock-a", approval="PENDING"),),
    )

    assert result.status == ZERO_VALID_CANDIDATES
    assert result.publication_status == "FORMAL"
    assert result.source_status == FORMAL_SOURCE_STATUS
    assert result.unique_instrument_count == 0
    assert result.excluded_relation_reasons == (("UNAPPROVED_RELATION", 1),)
    assert result.publishable is True


def test_stale_topic_state_cannot_satisfy_requested_date():
    result = FormalOpportunityUniverseConsumer().build(
        as_of=D,
        expected_topic_ids=("topic-a",),
        topics=(_topic("topic-a", as_of=date(2026, 9, 16)),),
        eligibility=(_eligibility("topic-a"),),
        relations=(_relation("relation-a-stock-a", "topic-a", "stock-a"),),
    )

    assert result.status == UNAVAILABLE
    assert result.publishable is False
    assert "TOPIC_AS_OF_MISMATCH:topic-a" in result.reasons


def test_future_relation_is_not_used_as_a_d_plus_one_lookahead():
    result = FormalOpportunityUniverseConsumer().build(
        as_of=D,
        expected_topic_ids=("topic-a",),
        topics=(_topic("topic-a"),),
        eligibility=(_eligibility("topic-a"),),
        relations=(
            _relation("future-relation", "topic-a", "stock-a", valid_from=date(2026, 9, 18)),
        ),
    )

    assert result.status == ZERO_VALID_CANDIDATES
    assert result.unique_instrument_count == 0
    assert result.excluded_relation_reasons == (("FUTURE_RELATION_NOT_LOOKAHEAD", 1),)


def test_price_boundary_requires_exact_date_and_does_not_accept_d_minus_one_or_d_plus_one():
    result = FormalOpportunityUniverseConsumer().build(
        as_of=D,
        expected_topic_ids=("topic-a",),
        topics=(_topic("topic-a"),),
        eligibility=(_eligibility("topic-a"),),
        relations=(_relation("relation-a-stock-a", "topic-a", "stock-a"),),
        prices=(
            FormalPriceObservation(
                instrument_id="stock-a",
                as_of=date(2026, 9, 18),
                status="AVAILABLE",
                close=Decimal("100"),
            ),
        ),
        require_price_evidence=True,
    )

    assert result.status == UNAVAILABLE
    assert result.price_boundary_status == PRICE_UNAVAILABLE
    assert result.publishable is False
    assert "PRICE_AS_OF_MISMATCH:stock-a" in result.reasons


def test_shadow_input_is_rejected_at_formal_boundary():
    with pytest.raises(FormalOpportunityUniverseError, match="shadow/research/fixture"):
        _topic("topic-shadow", publication="SHADOW")


def test_parent_topic_is_not_a_formal_opportunity_unit():
    parent = FormalTopicState(
        topic_id="parent",
        slug="parent",
        name="Parent",
        topic_type="PARENT",
        as_of=D,
        publication_status="FORMAL",
        data_status="FORMAL_PUBLISHED",
        snapshot_id="snapshot:parent",
        snapshot_hash="hash:parent",
    )
    result = FormalOpportunityUniverseConsumer().build(
        as_of=D,
        expected_topic_ids=("parent",),
        topics=(parent,),
        eligibility=(_eligibility("parent"),),
        relations=(),
    )

    assert result.status == UNAVAILABLE
    assert result.unavailable_topic_ids == ("parent",)
    assert "PARENT_TOPIC_NOT_OPPORTUNITY_UNIT:parent" in result.reasons


def test_missing_formal_eligibility_is_owner_decision_required_not_shadow_policy_fallback():
    result = FormalOpportunityUniverseConsumer().build(
        as_of=D,
        expected_topic_ids=("topic-a",),
        topics=(_topic("topic-a"),),
        eligibility=(),
        relations=(_relation("relation-a-stock-a", "topic-a", "stock-a"),),
    )

    assert result.status == "OWNER_DECISION_REQUIRED"
    assert result.publishable is False
    assert "OWNER_DECISION_REQUIRED:MISSING_TOPIC_ELIGIBILITY:topic-a" in result.reasons
