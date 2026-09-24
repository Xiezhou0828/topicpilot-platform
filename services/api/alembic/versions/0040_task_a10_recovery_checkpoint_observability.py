"""Add immutable A10 recovery checkpoint events."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0040_task_a10_recovery_checkpoint_observability"
down_revision = "0039_task_a9_b2_formal_correction_supersession"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "live_collector_checkpoints",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "run_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("batch_number", sa.Integer(), nullable=False),
        sa.Column("batch_key", sa.String(length=128), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("succeeded_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "provider_request_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "provider_failure_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("checkpoint_hash", sa.String(length=128), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["topicpilot.live_collector_runs.id"],
            name="fk_live_collector_checkpoints_run_id_live_collector_runs",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_live_collector_checkpoints"),
        sa.CheckConstraint(
            "status IN ('IN_PROGRESS', 'COMPLETED', 'PARTIAL', 'FAILED')",
            name="ck_live_collector_checkpoints_status",
        ),
        sa.UniqueConstraint(
            "run_id",
            "batch_key",
            "attempt_number",
            name="uq_live_collector_checkpoints_event",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_live_collector_checkpoints_run_batch",
        "live_collector_checkpoints",
        ["run_id", "batch_number"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_live_collector_checkpoints_run_batch",
        table_name="live_collector_checkpoints",
        schema="topicpilot",
    )
    op.drop_table("live_collector_checkpoints", schema="topicpilot")
