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


def test_formal_topic_read_model_filters_to_published_rows():
    sql = TOPIC_ROWS_SQL.text
    assert "publication_mode = 'FORMAL'" in sql
    assert "publication_state = 'PUBLISHED'" in sql
    assert "superseded_by_snapshot_id IS NULL" in sql


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
