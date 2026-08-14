"""TASK-DATA-REF-006E date-effective instrument lifecycle evidence."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0029_task_data_ref_006e_instrument_lifecycle"
down_revision = "0028_task_data_ref_001_reference_bootstrap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reference_instrument_lifecycles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("registry_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status_code", sa.String(32), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.Column("evidence_id", sa.String(128), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.ForeignKeyConstraint(
            ["registry_set_id"],
            ["topicpilot.reference_registry_sets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["topicpilot.instruments.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_reference_instrument_lifecycles_valid_range",
        ),
        sa.UniqueConstraint(
            "registry_set_id",
            "instrument_id",
            "status_code",
            "effective_from",
            "evidence_id",
            name="uq_reference_instrument_lifecycles_event",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_reference_instrument_lifecycles_instrument_effective",
        "reference_instrument_lifecycles",
        ["instrument_id", "effective_from"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_reference_instrument_lifecycles_instrument_effective",
        table_name="reference_instrument_lifecycles",
        schema="topicpilot",
    )
    op.drop_table("reference_instrument_lifecycles", schema="topicpilot")
