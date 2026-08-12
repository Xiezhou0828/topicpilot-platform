"""TASK-DATA-REF-001 reference-only bootstrap support."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0028_task_data_ref_001_reference_bootstrap"
down_revision = "0027_task_be_021_topic_lifecycle_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reference_registry_sets",
        sa.Column("bundle_sha256", sa.String(64)),
        schema="topicpilot",
    )
    op.add_column(
        "reference_registry_sets",
        sa.Column("source_manifest_sha256", sa.String(64)),
        schema="topicpilot",
    )
    op.alter_column(
        "reference_registry_sets",
        "status",
        server_default=sa.text("'DRAFT'"),
        schema="topicpilot",
    )
    op.create_check_constraint(
        "ck_reference_registry_sets_status",
        "reference_registry_sets",
        "status IN ('DRAFT', 'VALIDATED', 'ACTIVE', 'RETIRED')",
        schema="topicpilot",
    )
    op.create_index(
        "uq_reference_registry_sets_active",
        "reference_registry_sets",
        ["status"],
        unique=True,
        schema="topicpilot",
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )
    op.create_table(
        "reference_calendar_dates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("registry_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("calendar_code", sa.String(64), nullable=False),
        sa.Column("calendar_date", sa.Date(), nullable=False),
        sa.Column("date_kind", sa.String(16), nullable=False),
        sa.ForeignKeyConstraint(
            ["registry_set_id"],
            ["topicpilot.reference_registry_sets.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "date_kind IN ('HOLIDAY', 'SUSPENDED')",
            name="ck_reference_calendar_dates_kind",
        ),
        sa.UniqueConstraint(
            "registry_set_id",
            "calendar_code",
            "calendar_date",
            name="uq_reference_calendar_dates_registry_date",
        ),
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_table("reference_calendar_dates", schema="topicpilot")
    op.drop_index(
        "uq_reference_registry_sets_active", table_name="reference_registry_sets", schema="topicpilot"
    )
    op.drop_constraint(
        "ck_reference_registry_sets_status", "reference_registry_sets", schema="topicpilot"
    )
    op.alter_column(
        "reference_registry_sets",
        "status",
        server_default=sa.text("'ACTIVE'"),
        schema="topicpilot",
    )
    op.drop_column("reference_registry_sets", "source_manifest_sha256", schema="topicpilot")
    op.drop_column("reference_registry_sets", "bundle_sha256", schema="topicpilot")
