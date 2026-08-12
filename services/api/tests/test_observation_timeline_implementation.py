from pathlib import Path

from topicpilot_api.orm.models import (
    ObservationTimelineBatch,
    ObservationTimelineEntry,
    ObservationTimelineQualityEvent,
)

MIGRATION = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0018_phase3_4_006_observation_timeline.py"


def test_timeline_migration_is_single_revision_after_0017_and_downgrade_is_reverse_order():
    source = MIGRATION.read_text(encoding="utf-8")
    assert 'revision = "0018_phase3_4_006_observation_timeline"' in source
    assert 'down_revision = "0017_phase3_4_005_market_data_source_and_raw_observations"' in source
    assert source.index('"observation_timeline_batches"') < source.index('"observation_timeline_entries"') < source.index('"observation_timeline_quality_events"')
    downgrade = source[source.index("def downgrade()") :]
    assert downgrade.index('op.drop_table("observation_timeline_quality_events"') < downgrade.index('op.drop_table("observation_timeline_entries"') < downgrade.index('op.drop_table("observation_timeline_batches"')
    assert "normalized_market_observations" not in source


def test_timeline_models_expose_approved_constraints_indexes_and_lineage():
    constraints = {c.name for c in ObservationTimelineBatch.__table__.constraints if c.name is not None}
    assert "ck_observation_timeline_batches_ck_timeline_batch_requested_window_pair" in constraints
    assert "ck_observation_timeline_batches_ck_timeline_batch_requested_window_order" in constraints
    entry_constraints = {c.name for c in ObservationTimelineEntry.__table__.constraints if c.name is not None}
    assert "uq_observation_timeline_entries_business_dedup" in entry_constraints
    assert "fk_timeline_entry_raw_lineage" in entry_constraints
    assert any(
        fk.parent.name == "raw_observation_id"
        and fk.column.table.name == "raw_market_observations"
        and fk.column.name == "id"
        for fk in ObservationTimelineEntry.__table__.c.raw_observation_id.foreign_keys
    )
    assert any(
        c.name == "ck_observation_timeline_entries_ck_observation_timeline_entries_no_self_supersession"
        for c in ObservationTimelineEntry.__table__.constraints if c.name is not None
    )
    quality_constraints = {c.name for c in ObservationTimelineQualityEvent.__table__.constraints if c.name is not None}
    assert any(
        c.name == "ck_observation_timeline_quality_events_ck_timeline_quality_event_owner"
        for c in ObservationTimelineQualityEvent.__table__.constraints if c.name is not None
    )
    assert "ck_observation_timeline_quality_events_ck_timeline_quality_event_severity" in quality_constraints
    assert {i.name for i in ObservationTimelineEntry.__table__.indexes} >= {"ix_timeline_entries_replay", "ix_timeline_entries_source_time", "ix_timeline_entries_batch_time"}


def test_replay_index_encodes_deterministic_order():
    index = next(i for i in ObservationTimelineEntry.__table__.indexes if i.name == "ix_timeline_entries_replay")
    assert [c.name for c in index.columns] == ["instrument_id", "observed_at", "ordering_key", "id"]


def test_timeline_migration_declares_corrected_fk_and_severity_constraint():
    source = MIGRATION.read_text(encoding="utf-8")
    assert 'sa.ForeignKeyConstraint(["raw_observation_id"], ["topicpilot.raw_market_observations.id"], ondelete="RESTRICT")' in source
    assert 'sa.CheckConstraint("severity IN (\'INFO\', \'WARNING\', \'ERROR\')", name="ck_timeline_quality_event_severity")' in source
