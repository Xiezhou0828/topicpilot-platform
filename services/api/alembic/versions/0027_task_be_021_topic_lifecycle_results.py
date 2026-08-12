"""TASK-BE-021 explainable topic lifecycle shadow results."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0027_task_be_021_topic_lifecycle_results"
down_revision = "0026_task_data_022a_no_trade_coverage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topic_lifecycle_results",
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
        sa.Column("data_status", sa.String(32), nullable=False),
        sa.Column("transition_decision", sa.String(64), nullable=False),
        sa.Column("transition_reason", sa.String(256), nullable=False),
        sa.Column("leadership_evidence", postgresql.JSONB()),
        sa.Column("diffusion_evidence", postgresql.JSONB()),
        sa.Column("group_strength_evidence", postgresql.JSONB()),
        sa.Column("divergence_decay_evidence", postgresql.JSONB()),
        sa.Column("persistence_evidence", postgresql.JSONB()),
        sa.Column("sample_confidence", postgresql.JSONB()),
        sa.Column("confirmation_state", postgresql.JSONB()),
        sa.Column("policy_version", sa.String(96), nullable=False),
        sa.Column("calculation_version", sa.String(96), nullable=False),
        sa.Column("evaluation_mode", sa.String(16), nullable=False, server_default="SHADOW"),
        sa.Column("snapshot_date", sa.Date()),
        sa.Column("average_change", sa.Numeric(12, 4)),
        sa.Column("coverage_pct", sa.Numeric(7, 3)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["topic_id"], ["topicpilot.topics.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "topic_id", "evaluation_date", "policy_version", "evaluation_mode",
            name="uq_topic_lifecycle_result_identity",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_topic_lifecycle_results_date",
        "topic_lifecycle_results",
        ["evaluation_date", "topic_slug"],
        schema="topicpilot",
    )
    op.create_index(
        "ix_topic_lifecycle_results_topic_date",
        "topic_lifecycle_results",
        ["topic_id", "evaluation_date"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_topic_lifecycle_results_topic_date",
        table_name="topic_lifecycle_results",
        schema="topicpilot",
    )
    op.drop_index(
        "ix_topic_lifecycle_results_date",
        table_name="topic_lifecycle_results",
        schema="topicpilot",
    )
    op.drop_table("topic_lifecycle_results", schema="topicpilot")
