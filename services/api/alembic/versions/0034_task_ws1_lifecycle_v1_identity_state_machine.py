"""Persist V1 identity-aware lifecycle state and role-bearing member facts.

Additive schema-only artifact.  This task does not execute migrations against
production and does not backfill historical or production rows.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0034_task_ws1_lifecycle_v1_identity_state_machine"
down_revision = "0033_task_ws4_reference_registry_transition_merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "topic_snapshot_member_facts",
        sa.Column("structural_role", sa.String(32), nullable=True),
        schema="topicpilot",
    )
    op.add_column(
        "topic_snapshot_member_facts",
        sa.Column("role_source", sa.String(64), nullable=True),
        schema="topicpilot",
    )
    columns = (
        ("main_rise_segment", sa.Integer()),
        ("segment_entry_date", sa.Date()),
        ("segment_anchor_date", sa.Date()),
        ("days_since_meaningful_expansion", sa.Integer()),
        ("drawdown_from_peak_pct", sa.Numeric(12, 4)),
        ("state_memory", postgresql.JSONB()),
    )
    for name, column_type in columns:
        op.add_column(
            "topic_lifecycle_results",
            sa.Column(name, column_type, nullable=True),
            schema="topicpilot",
        )


def downgrade() -> None:
    for name in (
        "state_memory",
        "drawdown_from_peak_pct",
        "days_since_meaningful_expansion",
        "segment_anchor_date",
        "segment_entry_date",
        "main_rise_segment",
    ):
        op.drop_column("topic_lifecycle_results", name, schema="topicpilot")
    op.drop_column("topic_snapshot_member_facts", "role_source", schema="topicpilot")
    op.drop_column("topic_snapshot_member_facts", "structural_role", schema="topicpilot")
