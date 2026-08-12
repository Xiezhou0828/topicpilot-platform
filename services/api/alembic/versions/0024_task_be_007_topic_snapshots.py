"""TASK-BE-007 formal V2 daily topic snapshots."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0024_task_be_007_topic_snapshots"
down_revision = "0023_task_be_003_provider_orchestrator"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topic_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_slug", sa.String(128), nullable=False),
        sa.Column("topic_name", sa.String(160), nullable=False),
        sa.Column("parent_topic", sa.String(160)),
        sa.Column("market_grade", sa.String(16)),
        sa.Column("topic_score", sa.Numeric(12, 4)),
        sa.Column("topic_direction", sa.String(16), nullable=False),
        sa.Column("stock_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("strong_stock_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("weak_stock_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_change", sa.Numeric(12, 4)),
        sa.Column("observed_stock_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("coverage_pct", sa.Numeric(7, 3)),
        sa.Column("data_status", sa.String(32), nullable=False),
        sa.Column("score_status", sa.String(32), nullable=False),
        sa.Column("calculation_version", sa.String(64), nullable=False),
        sa.Column("metadata", postgresql.JSONB()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topicpilot.topics.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("topic_id", "snapshot_date", name="uq_topic_snapshots_topic_date"),
        schema="topicpilot",
    )
    op.create_index(
        "ix_topic_snapshots_date",
        "topic_snapshots",
        ["snapshot_date", "topic_slug"],
        schema="topicpilot",
    )
    op.create_index(
        "ix_topic_snapshots_topic_date",
        "topic_snapshots",
        ["topic_id", "snapshot_date"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index("ix_topic_snapshots_topic_date", table_name="topic_snapshots", schema="topicpilot")
    op.drop_index("ix_topic_snapshots_date", table_name="topic_snapshots", schema="topicpilot")
    op.drop_table("topic_snapshots", schema="topicpilot")
