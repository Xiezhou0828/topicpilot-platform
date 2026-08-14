"""TASK-DATA-REF-006G immutable registry transition provenance."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0030_task_data_ref_006g_registry_transition"
down_revision = "0029_task_data_ref_006e_instrument_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reference_registry_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("from_registry_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_registry_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_reference_data_version", sa.String(64), nullable=False),
        sa.Column("to_reference_data_version", sa.String(64), nullable=False),
        sa.Column("from_bundle_sha256", sa.String(64)),
        sa.Column("to_bundle_sha256", sa.String(64), nullable=False),
        sa.Column("transition_kind", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(
            ["from_registry_set_id"],
            ["topicpilot.reference_registry_sets.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["to_registry_set_id"],
            ["topicpilot.reference_registry_sets.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "from_registry_set_id",
            "to_registry_set_id",
            name="uq_reference_registry_transitions_edge",
        ),
        sa.UniqueConstraint(
            "to_registry_set_id", name="uq_reference_registry_transitions_target"
        ),
        sa.CheckConstraint(
            "from_registry_set_id <> to_registry_set_id",
            name="ck_reference_registry_transitions_distinct_sets",
        ),
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_table("reference_registry_transitions", schema="topicpilot")
