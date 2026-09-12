from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from topicpilot_api.orm import TopicSnapshot, TopicSnapshotMemberFact
from topicpilot_api.production_read_model import TOPIC_ROWS_SQL
from topicpilot_api.topic_daily_state import (
    FORMAL_MAPPING_EARLIEST_DATE,
    FormalAuthorityUnavailable,
    MembershipMember,
    MembershipSnapshot,
    SelectedMemberFact,
    TopicMaterializationPlan,
    _hash_payload,
    _snapshot_values,
    resolve_formal_membership,
)


def test_pre_boundary_membership_is_fail_closed_without_database_access():
    with pytest.raises(FormalAuthorityUnavailable, match="pre-boundary"):
        resolve_formal_membership(None, uuid4(), date(2026, 8, 6))


def test_formal_boundary_is_fixed_and_member_order_is_replayable():
    assert date(2026, 8, 7) == FORMAL_MAPPING_EARLIEST_DATE
    first = MembershipMember(uuid4(), "2330", "TPE", "RELATED", "v1", "BOUNDED")
    second = MembershipMember(uuid4(), "6806", "TPE", "RELATED", "v1", "BOUNDED")
    payload_a = {
        "members": [first.instrument_id, second.instrument_id],
        "boundary": FORMAL_MAPPING_EARLIEST_DATE,
    }
    payload_b = {
        "boundary": FORMAL_MAPPING_EARLIEST_DATE,
        "members": [first.instrument_id, second.instrument_id],
    }
    assert _hash_payload(payload_a) == _hash_payload(payload_b)


def test_snapshot_models_expose_typed_formal_and_member_fact_authority():
    snapshot_columns = {column.name for column in TopicSnapshot.__table__.columns}
    assert {
        "publication_mode",
        "membership_mode",
        "relation_version",
        "mapping_effective_from",
        "membership_snapshot_hash",
        "expected_count",
        "eligible_count",
        "no_trade_count",
        "unknown_count",
        "excluded_count",
        "reference_registry_version",
        "source_artifact_hash",
        "snapshot_identity",
        "supersedes_snapshot_id",
        "superseded_by_snapshot_id",
    } <= snapshot_columns
    fact_columns = {column.name for column in TopicSnapshotMemberFact.__table__.columns}
    assert {
        "snapshot_id",
        "instrument_id",
        "fact_identity",
        "fact_hash",
        "fact_state",
        "price_observation_id",
        "volume_observation_id",
        "trading_status_observation_id",
        "raw_fact_payload",
    } <= fact_columns
    assert TopicSnapshot.__table__.c.strong_stock_count.nullable is True
    assert TopicSnapshot.__table__.c.strong_stock_count.default is None
    assert TopicSnapshot.__table__.c.weak_stock_count.nullable is True
    assert TopicSnapshot.__table__.c.weak_stock_count.default is None
    assert any(
        constraint.name == "uq_topic_snapshots_supersedes_once"
        for constraint in TopicSnapshot.__table__.constraints
    )


def test_formal_topic_read_model_filters_to_published_rows():
    sql = TOPIC_ROWS_SQL.text
    assert "publication_mode = 'FORMAL'" in sql
    assert "publication_state = 'PUBLISHED'" in sql
    assert "superseded_by_snapshot_id IS NULL" in sql
    assert "successor.supersedes_snapshot_id = topic_snapshots.id" in sql


def test_member_fact_reader_never_promotes_a_prior_bar_to_target_date():
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "topicpilot_api"
        / "topic_daily_state.py"
    ).read_text(encoding="utf-8")

    assert 'latest["trading_date"] == trading_date' in source
    assert "previous = ranked_prices.get(2) if price is not None else latest" in source


def test_correction_values_are_immutable_and_explicitly_superseding():
    instrument_id = uuid4()
    superseded_id = uuid4()
    member = MembershipMember(instrument_id, "2330", "TPE", "RELATED", "v1", "BOUNDED")
    membership = MembershipSnapshot(
        topic_id=uuid4(),
        trading_date=date(2026, 8, 7),
        relation_version="v1",
        mapping_effective_from=FORMAL_MAPPING_EARLIEST_DATE,
        membership_snapshot_id="membership:hash",
        membership_snapshot_hash="hash",
        reference_registry_version="ref-v1",
        session_code="TPE-REGULAR",
        calendar_code="TWSE",
        trading_day_state="TRADING",
        expected_count=1,
        eligible_count=1,
        excluded_count=0,
        excluded_reasons=(),
        members=(member,),
    )
    fact = SelectedMemberFact(
        instrument_id=instrument_id,
        trading_date=date(2026, 8, 7),
        fact_state="OBSERVED",
        price_observation_id=None,
        volume_observation_id=None,
        trading_status_observation_id=None,
        close=Decimal("1"),
        previous_close=Decimal("1"),
        change_pct=Decimal("0"),
        observed_classification="FLAT",
        observed_at=None,
        retrieved_at=None,
        raw_fact_payload={"instrumentId": str(instrument_id)},
        fact_identity="fact:base",
        fact_hash="base",
    )
    plan = TopicMaterializationPlan(
        trading_date=date(2026, 8, 7),
        topic_id=membership.topic_id,
        topic_slug="topic",
        topic_name="Topic",
        status="READY",
        reason=None,
        membership=membership,
        facts=(fact,),
    )
    values = _snapshot_values(
        plan,
        now=datetime(2026, 8, 14, tzinfo=UTC),
        correction_sequence=1,
        supersedes_snapshot_id=superseded_id,
    )
    assert values["correction_sequence"] == 1
    assert values["supersedes_snapshot_id"] == superseded_id
    assert values["supersession_reason"] == "CORRECTION"


def test_partial_snapshot_excludes_legal_no_trade_from_aggregate_truthfully():
    observed_id = uuid4()
    suspended_id = uuid4()
    members = (
        MembershipMember(observed_id, "2330", "TPE", "RELATED", "v1", "BOUNDED"),
        MembershipMember(
            suspended_id,
            "8277",
            "TWO",
            "RELATED",
            "v1",
            "BOUNDED",
            trading_expectation="LEGAL_NO_TRADE",
            availability_reason="SUSPENDED:TPEX-TWO-8277-SUSPENDED-20260910",
            lifecycle_evidence_id="TPEX-TWO-8277-SUSPENDED-20260910",
        ),
    )
    membership = MembershipSnapshot(
        topic_id=uuid4(),
        trading_date=date(2026, 9, 11),
        relation_version="v1",
        mapping_effective_from=FORMAL_MAPPING_EARLIEST_DATE,
        membership_snapshot_id="membership:partial",
        membership_snapshot_hash="partial",
        reference_registry_version="ref-v1",
        session_code="TPE-REGULAR",
        calendar_code="TWSE",
        trading_day_state="TRADING",
        expected_count=2,
        eligible_count=2,
        excluded_count=0,
        excluded_reasons=(),
        members=members,
    )
    facts = (
        SelectedMemberFact(
            instrument_id=observed_id,
            trading_date=date(2026, 9, 11),
            fact_state="OBSERVED",
            price_observation_id=None,
            volume_observation_id=None,
            trading_status_observation_id=None,
            close=Decimal("100"),
            previous_close=Decimal("99"),
            change_pct=Decimal("1.0101"),
            observed_classification="POSITIVE",
            observed_at=None,
            retrieved_at=None,
            raw_fact_payload={"instrumentId": str(observed_id)},
            fact_identity="fact:observed",
            fact_hash="observed",
        ),
        SelectedMemberFact(
            instrument_id=suspended_id,
            trading_date=date(2026, 9, 11),
            fact_state="NO_TRADE",
            price_observation_id=None,
            volume_observation_id=None,
            trading_status_observation_id=None,
            close=None,
            previous_close=Decimal("10"),
            change_pct=None,
            observed_classification=None,
            observed_at=None,
            retrieved_at=None,
            raw_fact_payload={
                "instrumentId": str(suspended_id),
                "tradingStatusReason": "SUSPENDED:TPEX-TWO-8277-SUSPENDED-20260910",
            },
            fact_identity="fact:suspended",
            fact_hash="suspended",
        ),
    )
    plan = TopicMaterializationPlan(
        date(2026, 9, 11),
        membership.topic_id,
        "topic",
        "Topic",
        "READY",
        None,
        membership,
        facts,
    )

    values = _snapshot_values(
        plan,
        now=datetime(2026, 9, 11, tzinfo=UTC),
        correction_sequence=0,
        supersedes_snapshot_id=None,
    )

    assert values["data_status"] == "PARTIAL"
    assert values["observed_stock_count"] == 1
    assert values["no_trade_count"] == 1
    assert values["coverage_pct"] == Decimal("50")
    assert values["quality_flags"]["unavailableMemberCount"] == 1


def test_formal_authority_migration_is_additive_and_single_head():
    migration = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0030_task_topic_daily_state_formal_authority.py"
    ).read_text(encoding="utf-8")
    assert 'revision = "0030_task_topic_daily_state_formal_authority"' in migration
    assert 'down_revision = "0029_task_data_ref_006e_instrument_lifecycle"' in migration
    assert '"topic_snapshot_member_facts"' in migration
    assert "uq_topic_snapshots_topic_date" in migration
    assert "snapshot_identity" in migration
    assert "publication_mode" in migration


def test_formal_correction_migration_adds_append_only_successor_guards():
    migration = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0039_task_a9_b2_formal_correction_supersession.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision = "0038_task_b2_topic_authority_activation_v1"' in migration
    assert "decision_revision" in migration
    assert "supersedes_decision_id" in migration
    assert "uq_topic_lifecycle_formal_supersedes_once" in migration
    assert "uq_topic_snapshots_supersedes_once" in migration
