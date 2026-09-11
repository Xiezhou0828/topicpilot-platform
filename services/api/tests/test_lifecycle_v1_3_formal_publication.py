from datetime import date, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import topicpilot_api.lifecycle_formal_publication as formal_publication
from topicpilot_api.lifecycle_formal_publication import (
    A9_FORMAL_TOPIC_SNAPSHOT_START,
    FORMAL_PUBLICATION_STATUS_UNAVAILABLE,
    FormalLifecyclePublisher,
    _formal_gate,
    _prior_or_bootstrap,
    input_snapshot_hash,
    read_formal_lifecycle,
)
from topicpilot_api.orm import TopicLifecycleFormalResult
from topicpilot_api.production_read_model import _read_lifecycle
from topicpilot_api.topic_lifecycle_v1 import (
    BASE,
    DECLINING,
    FERMENTING,
    MAIN_RISE,
    MATURE,
    SPROUTING,
    LifecycleInput,
    LifecycleObservation,
)
from topicpilot_api.topic_lifecycle_v1_3_formal import (
    FORMAL_EVALUATION_MODE,
    FORMAL_INITIALIZATION_CONTRACT_VERSION,
    LIFECYCLE_CALCULATION_VERSION,
    LIFECYCLE_CONTRACT_VERSION,
    evaluate_formal_lifecycle,
)


def _input(
    changes: list[float],
    *,
    previous: str | None = None,
    candidate: str | None = None,
    streak: int = 0,
    memory: dict | None = None,
    roles: list[str] | None = None,
) -> LifecycleInput:
    role_values = roles or ["REPRESENTATIVE"] + ["CORE"] * (len(changes) - 1)
    return LifecycleInput(
        topic_id="formal-test-topic",
        trading_date=date(2026, 8, 10),
        expected_member_count=len(changes),
        observations=tuple(
            LifecycleObservation(
                str(index),
                value,
                role_values[index],
                "FORMAL_ROLE_AUTHORITY",
                100.0,
                100.0,
            )
            for index, value in enumerate(changes)
        ),
        previous_stage=previous,
        previous_stage_entered_at=date(2026, 8, 1) if previous else None,
        previous_stage_trading_days=3 if previous else None,
        previous_candidate_stage=candidate,
        previous_candidate_streak=streak,
        state_memory=memory,
    )


def test_formal_evaluator_binds_frozen_contract_and_is_deterministic():
    value = _input(
        [8, 7, 6, 5, 5, 4, 4, 3, 3, 2],
        previous=FERMENTING,
        candidate=MAIN_RISE,
        streak=1,
    )
    first = evaluate_formal_lifecycle(value)
    second = evaluate_formal_lifecycle(value)

    assert first == second
    assert first.evaluation_mode == FORMAL_EVALUATION_MODE
    assert first.calculation_version == LIFECYCLE_CALCULATION_VERSION
    assert first.data_status == "FORMAL"


def test_base_to_fermenting_can_confirm_without_sprouting():
    changes = [1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
    first = evaluate_formal_lifecycle(_input(changes, previous=BASE))
    second = evaluate_formal_lifecycle(
        _input(
            changes,
            previous=BASE,
            candidate=first.candidate_stage,
            streak=first.confirmation_state["candidateStreak"],
            memory=first.state_memory,
        )
    )

    assert first.candidate_stage == FERMENTING
    assert second.final_stage == FERMENTING


def test_fermenting_failure_returns_to_base_and_never_sprouting():
    value = _input(
        [6, 0, -0.2],
        previous=FERMENTING,
        roles=["REPRESENTATIVE", "RELATED", "RELATED"],
    )
    result = evaluate_formal_lifecycle(value)

    assert result.candidate_stage == SPROUTING
    assert result.final_stage == BASE
    assert result.transition_reason == "CONFIRMED_FERMENTATION_FAILURE_TO_BASE"
    assert result.state_memory["cycleEnded"] is True


def test_mature_renewed_strength_stays_mature():
    result = evaluate_formal_lifecycle(
        _input(
            [8, 7, 6, 5, 5, 4, 4, 3, 3, 2],
            previous=MATURE,
            memory={"mainRiseSegment": 1, "mainRiseAncestry": True},
        )
    )

    assert result.candidate_stage == MAIN_RISE
    assert result.final_stage == MATURE
    assert result.transition_reason == "MATURE_RENEWED_STRENGTH_PERSISTS"


def test_declining_rebound_stays_declining():
    result = evaluate_formal_lifecycle(
        _input([8, 7, 6, 5, 5, 4, 4, 3, 3, 2], previous=DECLINING)
    )

    assert result.candidate_stage == BASE
    assert result.final_stage == DECLINING


def test_missing_formal_observation_fails_closed_even_with_previous_stage():
    result = evaluate_formal_lifecycle(
        LifecycleInput(
            topic_id="formal-test-topic",
            trading_date=date(2026, 8, 10),
            expected_member_count=10,
            observations=(),
            previous_stage=MATURE,
            previous_stage_entered_at=date(2026, 8, 1),
            previous_stage_trading_days=3,
        )
    )

    assert result.final_stage is None
    assert result.data_status == "UNAVAILABLE"
    assert result.transition_decision == "HOLD_FORMAL_GATE"
    assert result.transition_reason == "INSUFFICIENT_FORMAL_INPUT:INSUFFICIENT_DATA"


def _snapshot(*, data_status: str = "COMPLETE", topic_id: UUID | None = None):
    snapshot_id = uuid4()
    return SimpleNamespace(
        id=snapshot_id,
        topic_id=topic_id or uuid4(),
        topic_slug="leaf-topic",
        snapshot_identity="topic-daily-state:2026-08-24:leaf-topic",
        membership_snapshot_id="membership:2026-08-24",
        membership_snapshot_hash="membership-hash",
        relation_version="relations:v1",
        source_artifact_id="artifact:2026-08-24",
        source_artifact_hash="artifact-hash",
        lineage_hash="lineage-hash",
        correction_sequence=0,
        supersedes_snapshot_id=None,
        superseded_by_snapshot_id=None,
        data_status=data_status,
        stock_count=3,
        observed_stock_count=3,
        reference_registry_version="reference:v1",
        mapping_policy_version="mapping:v1",
        session_code="TWSE_REGULAR",
        calendar_code="TWSE",
        source_run_id="topic-daily-state:2026-08-24",
        snapshot_date=date(2026, 8, 24),
        as_of_at=datetime(2026, 8, 24, 7, 0),
    )


def _facts(snapshot, *, missing_role: bool = False):
    return [
        SimpleNamespace(
            snapshot_id=snapshot.id,
            instrument_id=uuid4(),
            fact_identity=f"fact-{index}",
            fact_hash=f"fact-hash-{index}",
            fact_state="OBSERVED",
            structural_role=None if missing_role else "CORE",
            role_source=None if missing_role else "FORMAL_ROLE_AUTHORITY",
        )
        for index in range(3)
    ]


def test_formal_input_gate_rejects_partial_snapshot_and_role_gap():
    partial = _snapshot(data_status="PARTIAL")
    partial_gate = _formal_gate(partial, _facts(partial))
    assert partial_gate.passed is False
    assert partial_gate.reason == "INSUFFICIENT_FORMAL_INPUT:SNAPSHOT_DATA_STATUS_PARTIAL"

    role_gap = _snapshot()
    role_gate = _formal_gate(role_gap, _facts(role_gap, missing_role=True))
    assert role_gate.passed is False
    assert role_gate.reason == (
        "INSUFFICIENT_FORMAL_INPUT:STRUCTURAL_ROLE_AUTHORITY_INCOMPLETE"
    )


def test_formal_input_hash_is_order_independent():
    snapshot = _snapshot()
    facts = _facts(snapshot)
    assert input_snapshot_hash(snapshot, facts) == input_snapshot_hash(
        snapshot, list(reversed(facts))
    )


def test_formal_publisher_rejects_pre_a9_snapshot_authority():
    publisher = FormalLifecyclePublisher(object())

    try:
        publisher.run_once(evaluation_date=date(2026, 8, 23), persist=False)
    except ValueError as exc:
        assert str(exc) == (
            "FORMAL_LIFECYCLE_DATE_BEFORE_A9_AUTHORITY:"
            f"{A9_FORMAL_TOPIC_SNAPSHOT_START.isoformat()}"
        )
    else:
        raise AssertionError("pre-A9 formal lifecycle date was accepted")


def test_bootstrap_is_leaf_local_and_prior_formal_permanently_bypasses_it():
    first_leaf = uuid4()
    late_leaf = uuid4()
    first_date = date(2026, 8, 28)
    late_date = date(2026, 9, 4)

    first_prior, first_mode = _prior_or_bootstrap({}, first_leaf, first_date)
    late_prior, late_mode = _prior_or_bootstrap({}, late_leaf, late_date)
    published = {
        first_leaf: {
            "final_stage": FERMENTING,
            "stage_entered_at": first_date,
            "stage_trading_days": 2,
            "candidate_stage": FERMENTING,
            "candidate_streak": 2,
            "state_memory": {"formal": True},
        }
    }
    next_prior, next_mode = _prior_or_bootstrap(published, first_leaf, late_date)

    assert first_mode == late_mode == FORMAL_INITIALIZATION_CONTRACT_VERSION
    assert first_prior["stage_entered_at"] == first_date
    assert late_prior["stage_entered_at"] == late_date
    assert first_prior["stage_trading_days"] == late_prior["stage_trading_days"] == 0
    assert first_prior["candidate_streak"] == late_prior["candidate_streak"] == 0
    assert first_prior["state_memory"] == late_prior["state_memory"] == {}
    assert next_mode is None
    assert next_prior is published[first_leaf]


def test_formal_leaf_scope_uses_all_107_effective_hierarchy_children():
    parent_id = uuid4()
    leaf_ids = [uuid4() for _ in range(107)]
    topics = [SimpleNamespace(id=parent_id, slug="parent", status="ACTIVE")]
    topics.extend(
        SimpleNamespace(id=item, slug=f"leaf-{index:03}", status="ENABLED")
        for index, item in enumerate(leaf_ids)
    )

    class _TopicSession:
        def __init__(self):
            self.calls = 0

        def scalars(self, _statement):
            self.calls += 1
            return topics if self.calls == 1 else leaf_ids

    leaves = formal_publication._active_leaf_topics(
        _TopicSession(), date(2026, 8, 24)
    )

    assert [topic.id for topic in leaves] == leaf_ids


def test_formal_leaf_scope_never_counts_obsolete_child_as_107th_leaf():
    active_ids = [uuid4() for _ in range(106)]
    obsolete_id = uuid4()
    topics = [
        *(SimpleNamespace(id=item, slug=f"leaf-{index:03}", status="ENABLED")
          for index, item in enumerate(active_ids)),
        SimpleNamespace(id=obsolete_id, slug="obsolete", status="RETIRED"),
    ]

    class _TopicSession:
        def __init__(self):
            self.calls = 0

        def scalars(self, _statement):
            self.calls += 1
            return topics if self.calls == 1 else [*active_ids, obsolete_id]

    try:
        formal_publication._active_leaf_topics(_TopicSession(), date(2026, 8, 24))
    except ValueError as exc:
        assert "expected=107:actual=106" in str(exc)
    else:
        raise AssertionError("obsolete hierarchy child was counted in formal scope")


def test_publisher_bootstraps_first_eligible_formal_observation_from_base(
    monkeypatch,
):
    topic = SimpleNamespace(id=uuid4(), slug="leaf-topic")
    snapshot = _snapshot(topic_id=topic.id)
    facts = _facts(snapshot)
    monkeypatch.setattr(formal_publication, "_active_leaf_topics", lambda *_: [topic])
    monkeypatch.setattr(
        formal_publication,
        "_formal_snapshots_for_date",
        lambda *_: {topic.id: [snapshot]},
    )
    monkeypatch.setattr(formal_publication, "_facts_for_snapshot", lambda *_: facts)
    monkeypatch.setattr(formal_publication, "read_price_evidence", lambda *_: {})
    observations = _input([1, 1, 1]).observations
    monkeypatch.setattr(formal_publication, "_formal_observations", lambda *_: (observations, None))
    monkeypatch.setattr(formal_publication, "_previous_formal_states", lambda *_: {})

    run = FormalLifecyclePublisher(object()).run_once(
        evaluation_date=A9_FORMAL_TOPIC_SNAPSHOT_START,
        persist=False,
    )

    assert run.formal_rows == 1
    assert run.unavailable_rows == 0
    assert run.persisted_rows == 0
    assert run.reason_breakdown == {}
    result = run.topic_results[0]
    assert result["previousStage"] == BASE
    assert result["stageEnteredAt"] == A9_FORMAL_TOPIC_SNAPSHOT_START
    assert result["stageTradingDays"] == 1
    initialization = result["lineage"]["sourceReference"]["formalInitialization"]
    assert initialization == {
        "mode": FORMAL_INITIALIZATION_CONTRACT_VERSION,
        "version": FORMAL_INITIALIZATION_CONTRACT_VERSION,
        "firstEligibleFormalDate": A9_FORMAL_TOPIC_SNAPSHOT_START.isoformat(),
        "logicalPriorState": BASE,
        "logicalPriorEntryDate": A9_FORMAL_TOPIC_SNAPSHOT_START.isoformat(),
        "logicalPriorTradingDayCount": 0,
        "confirmationMemory": "EMPTY_DEFAULT_ZERO",
    }


def test_incomplete_first_observation_remains_unavailable_without_bootstrap(monkeypatch):
    topic = SimpleNamespace(id=uuid4(), slug="leaf-topic")
    snapshot = _snapshot(data_status="PARTIAL", topic_id=topic.id)
    facts = _facts(snapshot)
    monkeypatch.setattr(formal_publication, "_active_leaf_topics", lambda *_: [topic])
    monkeypatch.setattr(
        formal_publication,
        "_formal_snapshots_for_date",
        lambda *_: {topic.id: [snapshot]},
    )
    monkeypatch.setattr(formal_publication, "_facts_for_snapshot", lambda *_: facts)
    monkeypatch.setattr(formal_publication, "read_price_evidence", lambda *_: {})
    monkeypatch.setattr(formal_publication, "_previous_formal_states", lambda *_: {})

    run = FormalLifecyclePublisher(object()).run_once(
        evaluation_date=A9_FORMAL_TOPIC_SNAPSHOT_START, persist=False
    )

    assert run.formal_rows == 0
    assert run.unavailable_rows == 1
    assert run.topic_results[0]["finalStage"] is None
    assert "formalInitialization" not in run.topic_results[0]["lineage"]["sourceReference"]


def test_formal_table_is_separate_and_constrained():
    assert TopicLifecycleFormalResult.__tablename__ == "topic_lifecycle_formal_results"
    assert {
        column.name for column in TopicLifecycleFormalResult.__table__.columns
    } >= {
        "publication_status",
        "evaluation_mode",
        "contract_version",
        "input_snapshot_identity",
        "input_snapshot_hash",
        "lineage_hash",
        "as_of_at",
    }
    assert any(
        constraint.name == "uq_topic_lifecycle_formal_identity"
        for constraint in TopicLifecycleFormalResult.__table__.constraints
    )


class _PersistSession:
    def __init__(self):
        self.row = None
        self.added = []

    def scalar(self, _statement):
        return self.row

    def add(self, row):
        self.added.append(row)
        self.row = row


def test_formal_persistence_retry_is_idempotent():
    session = _PersistSession()
    publisher = FormalLifecyclePublisher(session)
    topic_id = uuid4()
    values = {
        "evaluation_date": date(2026, 8, 24),
        "topic_id": topic_id,
        "topic_slug": "leaf-topic",
        "final_stage": None,
        "candidate_stage": None,
        "transition_reason": "INSUFFICIENT_FORMAL_HISTORY:PREVIOUS_FORMAL_STATE_REQUIRED",
        "publication_status": FORMAL_PUBLICATION_STATUS_UNAVAILABLE,
        "input_snapshot_hash": "same-input",
        "lineage_hash": "same-lineage",
        "evaluation_mode": FORMAL_EVALUATION_MODE,
        "contract_version": LIFECYCLE_CONTRACT_VERSION,
    }
    publisher._persist(values)
    publisher._persist(values)

    assert len(session.added) == 1


def test_corrected_formal_decision_appends_superseding_revision():
    session = _PersistSession()
    publisher = FormalLifecyclePublisher(session)
    values = {
        "evaluation_date": date(2026, 8, 24),
        "topic_id": uuid4(),
        "topic_slug": "leaf-topic",
        "final_stage": None,
        "candidate_stage": None,
        "transition_reason": "OLD_UNAVAILABLE",
        "publication_status": FORMAL_PUBLICATION_STATUS_UNAVAILABLE,
        "input_snapshot_hash": "old-input",
        "lineage_hash": "old-lineage",
        "evaluation_mode": FORMAL_EVALUATION_MODE,
        "contract_version": LIFECYCLE_CONTRACT_VERSION,
    }
    publisher._persist(values)
    old = session.row
    corrected = dict(values)
    corrected.update(
        transition_reason="CORRECTED",
        input_snapshot_hash="corrected-input",
        lineage_hash="corrected-lineage",
    )
    publisher._persist(corrected)

    assert len(session.added) == 2
    assert session.row.supersedes_decision_id == old.id
    assert session.row.decision_revision == 1
    assert session.row.supersession_reason == "CORRECTED_A9_STRUCTURAL_ROLE_AUTHORITY"
    assert old.transition_reason == "OLD_UNAVAILABLE"


class _ReadSession:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self, _statement):
        return self.rows


def _formal_row(*, final_stage: str | None):
    return SimpleNamespace(
        final_stage=final_stage,
        evaluation_date=date(2026, 8, 24),
        stage_entered_at=date(2026, 8, 24) if final_stage else None,
        stage_trading_days=1 if final_stage else None,
        main_rise_segment=None,
        segment_entry_date=None,
        segment_anchor_date=None,
        days_since_meaningful_expansion=None,
        drawdown_from_peak_pct=None,
        publication_status=(
            "PUBLISHED" if final_stage else FORMAL_PUBLICATION_STATUS_UNAVAILABLE
        ),
        contract_version=LIFECYCLE_CONTRACT_VERSION,
        calculation_version=LIFECYCLE_CALCULATION_VERSION,
        evaluation_mode=FORMAL_EVALUATION_MODE,
        policy_version="topic-lifecycle-policy.v1",
        previous_stage=None,
        candidate_stage=None,
        transition_decision="HOLD_FORMAL_GATE",
        transition_reason="TEST",
        leadership_evidence=None,
        diffusion_evidence=None,
        group_strength_evidence=None,
        divergence_decay_evidence=None,
        persistence_evidence=None,
        sample_confidence=None,
        input_snapshot_id=None,
        input_snapshot_identity="snapshot-identity",
        input_snapshot_hash="snapshot-hash",
        membership_snapshot_id="membership-id",
        membership_snapshot_hash="membership-hash",
        relation_version="relation-v1",
        reference_registry_version="reference-v1",
        mapping_policy_version="mapping-v1",
        session_code="TWSE_REGULAR",
        calendar_code="TWSE",
        source_artifact_id="artifact-id",
        source_artifact_hash="artifact-hash",
        source_reference={},
        lineage_hash="lineage-hash",
        member_fact_hashes={},
        correction_sequence=0,
        supersession_state="ACTIVE",
        state_memory={},
        as_of_at=datetime(2026, 8, 24, 7, 0),
    )


def test_formal_readback_exposes_unavailable_without_shadow_promotion():
    row = _formal_row(final_stage=None)
    value = read_formal_lifecycle(_ReadSession([row]), uuid4())

    assert value is not None
    assert value["dataStatus"] == "NOT_AVAILABLE"
    assert value["currentStage"] is None
    assert value["publicationStatus"] == FORMAL_PUBLICATION_STATUS_UNAVAILABLE
    assert value["evaluationMode"] == FORMAL_EVALUATION_MODE


def test_production_read_model_prefers_formal_boundary(monkeypatch):
    import topicpilot_api.production_read_model as read_model

    formal_unavailable = {
        "currentStage": None,
        "dataStatus": "NOT_AVAILABLE",
        "publicationStatus": FORMAL_PUBLICATION_STATUS_UNAVAILABLE,
    }
    monkeypatch.setattr(read_model, "read_formal_lifecycle", lambda *_: formal_unavailable)

    assert _read_lifecycle(object(), uuid4()) == formal_unavailable
