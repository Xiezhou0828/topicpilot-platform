"""Add the append-only daily formal publication receipt stream."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0049_task_daily_formal_publication_receipt"
down_revision = "0048_task_checkpoint_provider_metric_applicability"
branch_labels = None
depends_on = None

SCHEMA = "topicpilot"
TABLE = "daily_formal_publication_receipts"
STATUSES = (
    "'COMPLETE', 'MARKET_CLOSED', 'WAITING_FOR_DATA', 'FAILED_CLOSED', "
    "'DEADLINE_EXCEEDED', 'CORRECTION_COMPLETE', 'CORRECTION_FAILED'"
)


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("calendar_code", sa.String(length=64), nullable=False),
        sa.Column("reference_data_version", sa.String(length=128), nullable=False),
        sa.Column("calendar_decision", postgresql.JSONB(), nullable=False),
        sa.Column("execution_key", sa.String(length=320), nullable=False),
        sa.Column("execution_scope", sa.String(length=64), nullable=False),
        sa.Column("execution_generation", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("receipt_revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_run_status", sa.String(length=32), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("readiness_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("publication_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("post_close_state", sa.String(length=64), nullable=False),
        sa.Column("reconciliation_state", sa.String(length=64), nullable=False),
        sa.Column("absolute_strength_state", sa.String(length=64), nullable=False),
        sa.Column("relative_strength_state", sa.String(length=64), nullable=False),
        sa.Column("formal_grade_state", sa.String(length=64), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=64), nullable=False),
        sa.Column("home_state", sa.String(length=64), nullable=False),
        sa.Column("formal_readback_state", sa.String(length=64), nullable=False),
        sa.Column("receipt_status", sa.String(length=32), nullable=False),
        sa.Column("failure_stage", sa.String(length=128), nullable=True),
        sa.Column("reason_code", sa.String(length=128), nullable=True),
        sa.Column("receipt_hash", sa.String(length=128), nullable=False),
        sa.Column("runtime_provenance", postgresql.JSONB(), nullable=False),
        sa.Column("formal_identifiers", postgresql.JSONB(), nullable=False),
        sa.Column("correction_lineage", postgresql.JSONB(), nullable=False),
        sa.Column("supersedes_receipt_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operational_events", postgresql.JSONB(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_run_id"],
            ["topicpilot.live_collector_runs.id"],
            name="fk_daily_formal_publication_receipts_source_run",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_receipt_id"],
            ["topicpilot.daily_formal_publication_receipts.id"],
            name="fk_daily_formal_publication_receipts_supersedes",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_daily_formal_publication_receipts"),
        sa.CheckConstraint(
            f"receipt_status IN ({STATUSES})",
            name="ck_daily_formal_publication_receipts_status",
        ),
        sa.CheckConstraint(
            "execution_generation >= 1 AND receipt_revision >= 1",
            name="ck_daily_formal_publication_receipts_sequence",
        ),
        sa.UniqueConstraint(
            "execution_key",
            "receipt_hash",
            name="uq_daily_formal_publication_receipts_observation",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_daily_formal_publication_receipts_date_revision",
        TABLE,
        ["trading_date", "receipt_revision", "created_at"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_daily_formal_publication_receipts_run",
        TABLE,
        ["source_run_id", "created_at"],
        schema=SCHEMA,
    )
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {SCHEMA}.reject_daily_formal_publication_receipt_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'daily formal publication receipts are append-only';
        END;
        $$;
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER trg_daily_formal_publication_receipt_append_only
        BEFORE UPDATE OR DELETE ON {SCHEMA}.{TABLE}
        FOR EACH ROW
        EXECUTE FUNCTION {SCHEMA}.reject_daily_formal_publication_receipt_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        f"DROP TRIGGER IF EXISTS trg_daily_formal_publication_receipt_append_only "
        f"ON {SCHEMA}.{TABLE}"
    )
    op.execute(
        f"DROP FUNCTION IF EXISTS {SCHEMA}.reject_daily_formal_publication_receipt_mutation()"
    )
    op.drop_index(
        "ix_daily_formal_publication_receipts_run",
        table_name=TABLE,
        schema=SCHEMA,
    )
    op.drop_index(
        "ix_daily_formal_publication_receipts_date_revision",
        table_name=TABLE,
        schema=SCHEMA,
    )
    op.drop_table(TABLE, schema=SCHEMA)
