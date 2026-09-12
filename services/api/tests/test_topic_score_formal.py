from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from topicpilot_api.topic_engine import (
    FORMAL_SCORE_MAPPING_EARLIEST_DATE,
    FORMAL_SCORE_MEMBERSHIP_MODE,
    FORMAL_SCORE_PUBLICATION_MODE,
    FORMAL_SCORE_PUBLICATION_STATE,
    FormalTopicScoreAuthority,
    FormalTopicScoreAuthorityError,
    FormalTopicScoreMemberFact,
    FormalTopicScoreSnapshot,
    GovernedLeaderSet,
    LeaderDefinition,
    ObservationAsOfBinding,
    ProductionV1PolicyBundle,
    derive_formal_topic_score,
)
from topicpilot_api.topic_engine.policy_approval import PolicyApprovalRecord

AS_OF = date(2026, 8, 7)


def _approval() -> PolicyApprovalRecord:
    return PolicyApprovalRecord(
        decision_status="APPROVED",
        reviewed_dataset_id="dataset-1",
        reviewed_dataset_version="v1",
        reviewed_validation_runtime_version="validation.v1",
        reviewed_report_digest="a" * 64,
        approved_candidate_id="candidate-approved",
        approved_candidate_version="v1",
        approved_policy_version="policy.v1",
        approved_effective_date=date(2026, 8, 1),
        approved_scope="production",
        approved_breadth_policy="pm://breadth/v1",
        approved_leadership_policy="pm://leadership/v1",
        approved_normalization_policy="pm://normalization/v1",
        approved_aggregation_policy="pm://aggregation/v1",
        approved_weights="pm://weights/v1",
        approved_eligibility_policy="pm://eligibility/v1",
        approved_grade_thresholds="pm://grade/v1",
        rollback_policy="select-earlier-approved-version",
        owner="pm",
        decision_rationale="approved mechanics",
        limitations="activation prerequisites remain explicit",
    )


def _policy() -> ProductionV1PolicyBundle:
    return ProductionV1PolicyBundle(
        candidate_id="candidate-approved",
        candidate_version="v1",
        policy_id="topic-score-policy",
        policy_version="policy.v1",
        effective_date=date(2026, 8, 1),
        leader_set_version="leaders.v1",
        breadth_policy_ref="pm://breadth/v1",
        leadership_policy_ref="pm://leadership/v1",
        normalization_policy_ref="pm://normalization/v1",
        aggregation_policy_ref="pm://aggregation/v1",
        weights_policy_ref="pm://weights/v1",
        eligibility_policy_ref="pm://eligibility/v1",
        grade_threshold_ref="pm://grade/v1",
        rollback_policy="select-earlier-approved-version",
        lifecycle="APPROVED",
    )


def _authority(*, core: tuple[str, ...] = ("s1", "s2", "s3")) -> FormalTopicScoreAuthority:
    return FormalTopicScoreAuthority(
        approval_record=_approval(),
        policy=_policy(),
        leader_set=GovernedLeaderSet(
            version="leaders.v1",
            lifecycle="APPROVED",
            artifact_id="leader-set-artifact-v1",
            effective_date=date(2026, 8, 1),
            topic_leaders=(
                (
                    "topic-1",
                    (LeaderDefinition("s1", 1.0), LeaderDefinition("s2", 0.75)),
                ),
            ),
        ),
        core_member_ids=core,
        core_authority_id="core-authority-v1",
        observation_binding=ObservationAsOfBinding(
            query_version="canonical-topic-fact-as-of.v1",
            source_id="source-approved-v1",
            as_of=AS_OF,
            session_code="TPE-REGULAR",
            latest_approved_session=True,
            fresh=True,
            observation_count=3,
            input_hash="b" * 64,
            bound_at=datetime(2026, 8, 7, 8, 0, tzinfo=UTC),
        ),
    )


def _snapshot(**overrides: object) -> FormalTopicScoreSnapshot:
    values: dict[str, object] = {
        "snapshot_id": "snapshot-1",
        "snapshot_identity": "formal:topic-1:2026-08-07:artifact-1",
        "topic_id": "topic-1",
        "snapshot_date": AS_OF,
        "publication_mode": FORMAL_SCORE_PUBLICATION_MODE,
        "membership_mode": FORMAL_SCORE_MEMBERSHIP_MODE,
        "publication_state": "PUBLISHED",
        "superseded_by_snapshot_id": None,
        "finality_state": "FINAL",
        "trading_day_state": "TRADING",
        "session_code": "TPE-REGULAR",
        "calendar_code": "TPEX",
        "mapping_effective_from": FORMAL_SCORE_MAPPING_EARLIEST_DATE,
        "membership_snapshot_id": "membership-1",
        "membership_snapshot_hash": "m" * 64,
        "relation_version": "relations.v1",
        "reference_registry_version": "reference.v1",
        "source_artifact_id": "topic-daily-state-artifact-1",
        "source_artifact_hash": "s" * 64,
        "lineage_hash": "l" * 64,
    }
    values.update(overrides)
    return FormalTopicScoreSnapshot(**values)


def _facts() -> tuple[FormalTopicScoreMemberFact, ...]:
    return tuple(
        FormalTopicScoreMemberFact(
            instrument_id=member_id,
            observation_date=AS_OF,
            fact_state="OBSERVED",
            change_pct=Decimal(str(change)),
            fact_hash=f"fact-{member_id}",
            source_artifact_id=f"artifact-{member_id}",
            source_artifact_hash="f" * 64,
        )
        for member_id, change in (("s1", 7.0), ("s2", 2.0), ("s3", -2.0))
    )


def test_formal_pit_evidence_derives_a_non_persistent_publication_envelope():
    publication = derive_formal_topic_score(_snapshot(), _facts(), _authority())

    assert publication.publication_state == FORMAL_SCORE_PUBLICATION_STATE
    assert publication.evaluation.score.status == "SCORED"
    assert publication.evaluation.score.score is not None
    assert publication.evaluation.score.grade in {"S", "A", "B", "D"}
    assert publication.lineage.snapshot_identity == "formal:topic-1:2026-08-07:artifact-1"
    assert publication.lineage.policy_version == "policy.v1"
    body = publication.as_dict()
    assert body["publicationMode"] == "FORMAL"
    assert body["publicationState"] == "UNPUBLISHED"
    assert body["lineage"]["membershipSnapshotHash"] == "m" * 64


def test_missing_or_unknown_member_evidence_is_not_converted_to_zero():
    facts = (
        *_facts()[:2],
        FormalTopicScoreMemberFact(
            instrument_id="s3",
            observation_date=AS_OF,
            fact_state="UNKNOWN",
            change_pct=None,
            fact_hash="fact-s3-unknown",
            source_artifact_id="artifact-s3",
            source_artifact_hash="f" * 64,
        ),
    )

    publication = derive_formal_topic_score(_snapshot(), facts, _authority())

    assert publication.evaluation.score.status == "INELIGIBLE"
    assert publication.evaluation.score.score is None
    assert publication.evaluation.score.grade is None
    assert (
        "VALID_OBSERVED_CORE_COUNT_BELOW_3" in publication.evaluation.score.evidence.quality_flags
    )


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"publication_mode": "RESEARCH_ONLY"}, "not FORMAL"),
        ({"membership_mode": "SHADOW"}, "not PIT_FORMAL"),
        ({"publication_state": "SUPERSEDED"}, "not PUBLISHED"),
        ({"superseded_by_snapshot_id": "snapshot-2"}, "superseded"),
        ({"snapshot_date": date(2026, 8, 6)}, "before the formal PIT boundary"),
    ],
)
def test_non_formal_or_superseded_snapshots_fail_closed(overrides, message):
    with pytest.raises(FormalTopicScoreAuthorityError, match=message):
        derive_formal_topic_score(_snapshot(**overrides), _facts(), _authority())


def test_missing_leader_set_or_core_authority_fails_closed():
    with pytest.raises(FormalTopicScoreAuthorityError, match="Leader Set"):
        derive_formal_topic_score(
            _snapshot(),
            _facts(),
            FormalTopicScoreAuthority(
                approval_record=_approval(),
                policy=_policy(),
                leader_set=GovernedLeaderSet(
                    version="leaders.v1",
                    lifecycle="APPROVED",
                    artifact_id="leader-set-artifact-v1",
                    effective_date=date(2026, 8, 1),
                    topic_leaders=(),
                ),
                core_member_ids=("s1", "s2", "s3"),
                core_authority_id="core-authority-v1",
                observation_binding=_authority().observation_binding,
            ),
        )

    with pytest.raises(FormalTopicScoreAuthorityError, match="CORE authority"):
        FormalTopicScoreAuthority(
            approval_record=_approval(),
            policy=_policy(),
            leader_set=_authority().leader_set,
            core_member_ids=(),
            core_authority_id="core-authority-v1",
            observation_binding=_authority().observation_binding,
        )


def test_fact_date_and_lineage_must_match_formal_authority():
    bad_fact = FormalTopicScoreMemberFact(
        instrument_id="s1",
        observation_date=date(2026, 8, 6),
        fact_state="OBSERVED",
        change_pct=7.0,
        fact_hash="fact-s1",
        source_artifact_id="artifact-s1",
        source_artifact_hash="f" * 64,
    )
    with pytest.raises(FormalTopicScoreAuthorityError, match="fact"):
        derive_formal_topic_score(_snapshot(), (bad_fact, *_facts()[1:]), _authority())
