from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from topicpilot_api.orm import TopicLifecycleResult
from topicpilot_api.production_read_model import _lifecycle_unavailable
from topicpilot_api.schemas import TopicLifecycleRead
from topicpilot_api.topic_lifecycle_contract import (
    BACKEND_LIFECYCLE_STAGES,
    BACKEND_TO_OWNER_LIFECYCLE_STAGE,
    LEGACY_PRESENTATION_ALIASES,
    OWNER_LIFECYCLE_STAGES,
)
from topicpilot_api.topic_lifecycle_engine import (
    MemberPriceEvidence,
    _date_rows,
    _formal_observations,
    _formal_snapshot_lineage,
)


def test_frozen_stage_contract_has_one_owner_sequence_and_no_legacy_stage():
    assert OWNER_LIFECYCLE_STAGES == ("萌芽", "發酵", "主升", "成熟", "衰退")
    assert BACKEND_LIFECYCLE_STAGES == (
        "SPROUTING",
        "FERMENTING",
        "MAIN_RISE",
        "MATURE",
        "DECLINING",
    )
    assert tuple(BACKEND_TO_OWNER_LIFECYCLE_STAGE.values()) == OWNER_LIFECYCLE_STAGES
    assert LEGACY_PRESENTATION_ALIASES == {"高檔整理": "成熟", "退潮": "衰退"}
    assert "資料待累積" not in OWNER_LIFECYCLE_STAGES


def test_lifecycle_result_has_additive_upstream_lineage_fields():
    assert {
        column.name for column in TopicLifecycleResult.__table__.columns
    } >= {
        "snapshot_id",
        "snapshot_identity",
        "membership_snapshot_id",
        "membership_snapshot_hash",
        "source_artifact_id",
        "source_artifact_hash",
        "lineage_hash",
        "member_fact_hashes",
        "correction_sequence",
        "supersession_state",
    }


def test_formal_snapshot_selection_is_published_and_non_superseded():
    class CaptureSession:
        def __init__(self):
            self.statement = None

        def scalars(self, statement):
            self.statement = statement
            return []

    session = CaptureSession()
    assert _date_rows(session, date(2026, 8, 21)) == []
    sql = str(session.statement)
    assert "publication_mode" in sql
    assert "membership_mode" in sql
    assert "publication_state" in sql
    assert "finality_state" in sql
    assert "superseded_by_snapshot_id" in sql


def test_missing_formal_lineage_fails_closed_before_shadow_result_creation():
    snapshot = SimpleNamespace(
        id=uuid4(),
        snapshot_identity="formal:topic:2026-08-21",
        membership_snapshot_id="membership-1",
        membership_snapshot_hash="hash-1",
        relation_version="relations-v1",
        source_artifact_id=None,
        source_artifact_hash=None,
        lineage_hash=None,
        correction_sequence=0,
        supersedes_snapshot_id=None,
        superseded_by_snapshot_id=None,
    )
    lineage, reason = _formal_snapshot_lineage(snapshot, [])
    assert lineage is None
    assert reason == (
        "MISSING_FORMAL_LINEAGE:lineage_hash,source_artifact_hash,source_artifact_id"
    )


def test_formal_member_facts_are_not_filtered_by_current_tracking_universe():
    instrument_id = uuid4()
    evaluation_date = date(2026, 8, 21)
    fact = SimpleNamespace(
        instrument_id=instrument_id,
        observation_date=evaluation_date,
        fact_state="OBSERVED",
        price_observation_id=uuid4(),
        change_pct=1.25,
    )
    observations, reason = _formal_observations(
        SimpleNamespace(),
        [fact],
        {
            instrument_id: MemberPriceEvidence(
                instrument_id,
                evaluation_date,
                Decimal("101.25"),
                Decimal("100"),
            )
        },
        None,
        evaluation_date,
    )
    assert reason is None
    assert observations is not None
    assert len(observations) == 1


def test_lifecycle_api_exposes_lineage_and_keeps_missing_state_backend_owned():
    value = TopicLifecycleRead(
        currentStage=None,
        currentStageEnteredAt=None,
        currentStageTradingDays=None,
        dataStatus="WAITING_FOR_FORMAL_LINEAGE",
        lineage={"snapshotIdentity": "formal:topic:2026-08-21"},
    )
    assert value.model_dump(by_alias=True)["lineage"]["snapshotIdentity"] == (
        "formal:topic:2026-08-21"
    )
    unavailable = _lifecycle_unavailable()
    assert unavailable["currentStage"] is None
    assert unavailable["lineage"] == {}


def test_lifecycle_api_accepts_fail_closed_without_promoting_a_stage():
    value = TopicLifecycleRead(
        currentStage=None,
        currentStageEnteredAt=None,
        currentStageTradingDays=None,
        dataStatus="FAIL_CLOSED",
        transitionReason="LINEAGE_INCOMPLETE",
    )
    dumped = value.model_dump(by_alias=True)
    assert dumped["dataStatus"] == "FAIL_CLOSED"
    assert dumped["currentStage"] is None
