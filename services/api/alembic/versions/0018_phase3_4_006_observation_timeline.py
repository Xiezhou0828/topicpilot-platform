"""Phase 3.4-006 observation timeline physical schema."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0018_phase3_4_006_observation_timeline"
down_revision = "0017_phase3_4_005_market_data_source_and_raw_observations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_raw_market_observations_lineage",
        "raw_market_observations",
        ["id", "source_id", "instrument_id"],
        schema="topicpilot",
    )
    op.create_table(
        "observation_timeline_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_instrument_id", postgresql.UUID(as_uuid=True)),
        sa.Column("requested_from", sa.DateTime(timezone=True)),
        sa.Column("requested_to", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(32), server_default="OPEN", nullable=False),
        sa.Column("coverage_status", sa.String(32), server_default="UNKNOWN", nullable=False),
        sa.Column("request_key", sa.String(160)),
        sa.Column("metadata", postgresql.JSONB()),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["topicpilot.market_data_sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requested_instrument_id"], ["topicpilot.instruments.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("source_id", "request_key", name="uq_observation_timeline_batches_request"),
        sa.CheckConstraint("(requested_from IS NULL) = (requested_to IS NULL)", name="ck_timeline_batch_requested_window_pair"),
        sa.CheckConstraint("requested_to IS NULL OR requested_to >= requested_from", name="ck_timeline_batch_requested_window_order"),
        sa.CheckConstraint("status IN ('OPEN', 'COMPLETED', 'PARTIAL', 'FAILED')", name="ck_timeline_batch_status"),
        sa.CheckConstraint("coverage_status IN ('UNKNOWN', 'SPARSE', 'COMPLETE', 'CONFLICTED')", name="ck_timeline_batch_coverage"),
        sa.CheckConstraint("status = 'OPEN' OR completed_at IS NOT NULL", name="ck_timeline_batch_completion"),
        schema="topicpilot",
    )
    op.create_table(
        "observation_timeline_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_observation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ordering_key", sa.String(256), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("supersedes_id", postgresql.UUID(as_uuid=True)),
        sa.Column("entry_status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["topicpilot.instruments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_id"], ["topicpilot.market_data_sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["raw_observation_id"], ["topicpilot.raw_market_observations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["raw_observation_id", "source_id", "instrument_id"], ["topicpilot.raw_market_observations.id", "topicpilot.raw_market_observations.source_id", "topicpilot.raw_market_observations.instrument_id"], name="fk_timeline_entry_raw_lineage", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["topicpilot.observation_timeline_batches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supersedes_id"], ["topicpilot.observation_timeline_entries.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("raw_observation_id", name="uq_observation_timeline_entries_raw"),
        sa.UniqueConstraint("instrument_id", "source_id", "observed_at", "content_hash", name="uq_observation_timeline_entries_business_dedup"),
        sa.CheckConstraint("supersedes_id IS NULL OR supersedes_id <> id", name="ck_observation_timeline_entries_no_self_supersession"),
        sa.CheckConstraint("entry_status IN ('ACTIVE', 'SUPERSEDED', 'QUARANTINED')", name="ck_observation_timeline_entries_status"),
        schema="topicpilot",
    )
    op.create_table(
        "observation_timeline_quality_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True)),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("event_code", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["entry_id"], ["topicpilot.observation_timeline_entries.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["batch_id"], ["topicpilot.observation_timeline_batches.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("entry_id IS NOT NULL OR batch_id IS NOT NULL", name="ck_timeline_quality_event_owner"),
        sa.CheckConstraint("severity IN ('INFO', 'WARNING', 'ERROR')", name="ck_timeline_quality_event_severity"),
        schema="topicpilot",
    )
    for table, cols, name in (
        ("observation_timeline_entries", ["instrument_id", "observed_at", "ordering_key", "id"], "ix_timeline_entries_replay"),
        ("observation_timeline_entries", ["source_id", "observed_at"], "ix_timeline_entries_source_time"),
        ("observation_timeline_entries", ["batch_id", "observed_at"], "ix_timeline_entries_batch_time"),
        ("observation_timeline_quality_events", ["entry_id", "detected_at"], "ix_timeline_quality_entry_time"),
        ("observation_timeline_quality_events", ["batch_id", "detected_at"], "ix_timeline_quality_batch_time"),
    ):
        op.create_index(name, table, cols, schema="topicpilot")


def downgrade() -> None:
    for name, table in (
        ("ix_timeline_quality_batch_time", "observation_timeline_quality_events"),
        ("ix_timeline_quality_entry_time", "observation_timeline_quality_events"),
        ("ix_timeline_entries_batch_time", "observation_timeline_entries"),
        ("ix_timeline_entries_source_time", "observation_timeline_entries"),
        ("ix_timeline_entries_replay", "observation_timeline_entries"),
    ):
        op.drop_index(name, table_name=table, schema="topicpilot")
    op.drop_table("observation_timeline_quality_events", schema="topicpilot")
    op.drop_table("observation_timeline_entries", schema="topicpilot")
    op.drop_table("observation_timeline_batches", schema="topicpilot")
    op.drop_constraint("uq_raw_market_observations_lineage", "raw_market_observations", schema="topicpilot", type_="unique")
