from datetime import date

from topicpilot_api.orm import TopicLifecycleResult
from topicpilot_api.production_read_model import _lifecycle_unavailable
from topicpilot_api.schemas import TopicLifecycleRead


def test_lifecycle_result_is_separate_shadow_fact_with_policy_lineage():
    assert TopicLifecycleResult.__tablename__ == "topic_lifecycle_results"
    assert {
        column.name for column in TopicLifecycleResult.__table__.columns
    } >= {
        "topic_id",
        "evaluation_date",
        "final_stage",
        "transition_reason",
        "sample_confidence",
        "policy_version",
        "evaluation_mode",
    }
    assert any(
        constraint.name == "uq_topic_lifecycle_result_identity"
        for constraint in TopicLifecycleResult.__table__.constraints
    )


def test_api_contract_keeps_lifecycle_evidence_backend_owned():
    value = TopicLifecycleRead(
        currentStage="MAIN_RISE",
        currentStageEnteredAt=date(2026, 8, 10),
        currentStageTradingDays=2,
        dataStatus="SHADOW_AVAILABLE",
        evaluationDate=date(2026, 8, 11),
        previousStage="FERMENTING",
        candidateStage="MAIN_RISE",
        transitionDecision="CONFIRMED_TRANSITION",
        transitionReason="ADAPTIVE_CONFIRMATION_SATISFIED",
        policyVersion="topic-lifecycle-policy.provisional.1",
        evidence={"leadership": {"leaderSemanticAvailable": False}},
        confidence={"confidence": 0.8},
    )
    dumped = value.model_dump(by_alias=True)
    assert dumped["currentStage"] == "MAIN_RISE"
    assert dumped["evidence"]["leadership"]["leaderSemanticAvailable"] is False


def test_read_model_fails_closed_when_shadow_storage_is_missing():
    value = _lifecycle_unavailable()
    assert value["dataStatus"] == "NOT_AVAILABLE"
    assert value["currentStage"] is None
    assert value["history"] == []
