"""B2 Lifecycle V1.3 formal publication/readback boundary."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0037_task_b2_lifecycle_v1_3_formal_publication"
down_revision = "0036_task_ws4_active_reference_daily_projection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topic_lifecycle_formal_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluation_date", sa.Date(), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_slug", sa.String(128), nullable=False),
        sa.Column("previous_stage", sa.String(32)),
        sa.Column("candidate_stage", sa.String(32)),
        sa.Column("final_stage", sa.String(32)),
        sa.Column("stage_entered_at", sa.Date()),
        sa.Column("stage_trading_days", sa.Integer()),
        sa.Column("evaluation_status", sa.String(32), nullable=False),
        sa.Column("data_status", sa.String(48), nullable=False),
        sa.Column("transition_decision", sa.String(64), nullable=False),
        sa.Column("transition_reason", sa.String(256), nullable=False),
        sa.Column("unavailable_reason", sa.String(256)),
        sa.Column("publication_status", sa.String(32), nullable=False),
        sa.Column("evaluation_mode", sa.String(16), nullable=False, server_default="FORMAL"),
        sa.Column("contract_version", sa.String(96), nullable=False),
        sa.Column("policy_version", sa.String(96), nullable=False),
        sa.Column("calculation_version", sa.String(96), nullable=False),
        sa.Column("leadership_evidence", postgresql.JSONB()),
        sa.Column("diffusion_evidence", postgresql.JSONB()),
        sa.Column("group_strength_evidence", postgresql.JSONB()),
        sa.Column("divergence_decay_evidence", postgresql.JSONB()),
        sa.Column("persistence_evidence", postgresql.JSONB()),
        sa.Column("sample_confidence", postgresql.JSONB()),
        sa.Column("confirmation_state", postgresql.JSONB()),
        sa.Column("state_memory", postgresql.JSONB()),
        sa.Column("main_rise_segment", sa.Integer()),
        sa.Column("segment_entry_date", sa.Date()),
        sa.Column("segment_anchor_date", sa.Date()),
        sa.Column("days_since_meaningful_expansion", sa.Integer()),
        sa.Column("drawdown_from_peak_pct", sa.Numeric(12, 4)),
        sa.Column("average_change", sa.Numeric(12, 4)),
        sa.Column("coverage_pct", sa.Numeric(7, 3)),
        sa.Column("input_snapshot_id", postgresql.UUID(as_uuid=True)),
        sa.Column("input_snapshot_identity", sa.String(256)),
        sa.Column("input_snapshot_hash", sa.String(128)),
        sa.Column("membership_snapshot_id", sa.String(128)),
        sa.Column("membership_snapshot_hash", sa.String(128)),
        sa.Column("relation_version", sa.String(128)),
        sa.Column("reference_registry_version", sa.String(64)),
        sa.Column("mapping_policy_version", sa.String(96)),
        sa.Column("session_code", sa.String(128)),
        sa.Column("calendar_code", sa.String(128)),
        sa.Column("source_artifact_id", sa.String(128)),
        sa.Column("source_artifact_hash", sa.String(128)),
        sa.Column("source_reference", postgresql.JSONB()),
        sa.Column("lineage_hash", sa.String(128)),
        sa.Column("member_fact_hashes", postgresql.JSONB()),
        sa.Column("correction_sequence", sa.Integer()),
        sa.Column("supersession_state", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("as_of_at", sa.DateTime(timezone=True)),
        sa.Column("generated_at", sa.DateTime(timezone=True)),
        sa.Column("diagnostic_detail", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topicpilot.topics.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["input_snapshot_id"],
            ["topicpilot.topic_snapshots.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "topic_id",
            "evaluation_date",
            "contract_version",
            name="uq_topic_lifecycle_formal_identity",
        ),
        sa.CheckConstraint(
            "evaluation_mode = 'FORMAL'",
            name="ck_topic_lifecycle_formal_mode",
        ),
        sa.CheckConstraint(
            "publication_status IN ('UNAVAILABLE', 'PUBLISHED', 'SUPERSEDED')",
            name="ck_topic_lifecycle_formal_publication_status",
        ),
        sa.CheckConstraint(
            "supersession_state IN ('ACTIVE', 'SUPERSEDED')",
            name="ck_topic_lifecycle_formal_supersession_state",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_topic_lifecycle_formal_topic_date",
        "topic_lifecycle_formal_results",
        ["topic_id", "evaluation_date", "publication_status"],
        schema="topicpilot",
    )
    op.create_index(
        "ix_topic_lifecycle_formal_date",
        "topic_lifecycle_formal_results",
        ["evaluation_date", "topic_slug", "publication_status"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_topic_lifecycle_formal_date",
        table_name="topic_lifecycle_formal_results",
        schema="topicpilot",
    )
    op.drop_index(
        "ix_topic_lifecycle_formal_topic_date",
        table_name="topic_lifecycle_formal_results",
        schema="topicpilot",
    )
    op.drop_table("topic_lifecycle_formal_results", schema="topicpilot")
