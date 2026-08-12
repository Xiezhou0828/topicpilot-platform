"""Phase 3.6-001B import audit and lineage persistence."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0021_phase3_6_001b_import_audit"
down_revision = "0020_phase3_5_002a_reference_registry"
branch_labels = None
depends_on = None


def upgrade():
    def u():
        return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)

    op.create_table(
        "legacy_import_runs",
        u(),
        sa.Column("export_id", sa.String(160), nullable=False),
        sa.Column("contract_version", sa.String(64), nullable=False),
        sa.Column("mapping_policy_version", sa.String(64), nullable=False),
        sa.Column("migration_baseline", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_legacy_import_runs_export_id", "legacy_import_runs", ["export_id"], schema="topicpilot"
    )
    op.create_table(
        "legacy_import_artifacts",
        u(),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"], ["topicpilot.legacy_import_runs.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("run_id", "filename", name="uq_legacy_import_artifacts_run_file"),
        schema="topicpilot",
    )
    op.create_table(
        "legacy_import_records",
        u(),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity", sa.String(64), nullable=False),
        sa.Column("stable_key", sa.String(512), nullable=False),
        sa.Column("canonical_payload_hash", sa.String(128), nullable=False),
        sa.Column("source_filename", sa.String(255)),
        sa.Column("source_row", sa.Integer()),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True)),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"], ["topicpilot.legacy_import_runs.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("run_id", "entity", "stable_key", name="uq_legacy_import_records_key"),
        schema="topicpilot",
    )
    op.create_index(
        "ix_legacy_import_records_lookup",
        "legacy_import_records",
        ["entity", "stable_key", "canonical_payload_hash"],
        schema="topicpilot",
    )


def downgrade():
    op.drop_index(
        "ix_legacy_import_runs_export_id", table_name="legacy_import_runs", schema="topicpilot"
    )
    op.drop_index(
        "ix_legacy_import_records_lookup", table_name="legacy_import_records", schema="topicpilot"
    )
    op.drop_table("legacy_import_records", schema="topicpilot")
    op.drop_table("legacy_import_artifacts", schema="topicpilot")
    op.drop_table("legacy_import_runs", schema="topicpilot")
