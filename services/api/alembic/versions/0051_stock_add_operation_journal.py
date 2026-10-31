"""Add an immutable journal for explicitly approved stock-master additions."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0051_stock_add_operation_journal"
down_revision = "0050_task_purge_retired_topics"
branch_labels = None
depends_on = None

SCHEMA = "topicpilot"


def upgrade() -> None:
    op.create_table(
        "stock_add_operations",
        sa.Column("operation_id", sa.String(length=160), nullable=False),
        sa.Column("market_code", sa.String(length=32), nullable=False),
        sa.Column("instrument_code", sa.String(length=64), nullable=False),
        sa.Column("plan_sha256", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("operation_id", name="pk_stock_add_operations"),
        sa.UniqueConstraint(
            "market_code",
            "instrument_code",
            "plan_sha256",
            name="uq_stock_add_operations_identity_plan",
        ),
        schema=SCHEMA,
    )
    op.create_table(
        "stock_add_operation_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_id", sa.String(length=160), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("artifact_sha256", sa.String(length=64), nullable=False),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["operation_id"],
            [f"{SCHEMA}.stock_add_operations.operation_id"],
            name="fk_stock_add_operation_events_operation",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_stock_add_operation_events"),
        sa.UniqueConstraint(
            "operation_id",
            "stage",
            "artifact_sha256",
            name="uq_stock_add_operation_events_checkpoint",
        ),
        sa.CheckConstraint(
            "stage IN ('MASTER_DATA_VERIFIED', 'RESEARCH_DATA_PUBLISHED', "
            "'TOPIC_RELATIONS_VERIFIED', "
            "'REFERENCE_VERSION_ACTIVATED', 'G1_G2_VERIFIED', 'POST_CLOSE_VERIFIED')",
            name="ck_stock_add_operation_events_stage",
        ),
        sa.CheckConstraint(
            "status IN ('PASS', 'BLOCKED')",
            name="ck_stock_add_operation_events_status",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_stock_add_operation_events_operation_time",
        "stock_add_operation_events",
        ["operation_id", "occurred_at"],
        schema=SCHEMA,
    )
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {SCHEMA}.reject_stock_add_journal_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'stock-add operation journal is append-only';
        END;
        $$;
        """
    )
    for table in ("stock_add_operations", "stock_add_operation_events"):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_append_only
            BEFORE UPDATE OR DELETE ON {SCHEMA}.{table}
            FOR EACH ROW
            EXECUTE FUNCTION {SCHEMA}.reject_stock_add_journal_mutation();
            """
        )


def downgrade() -> None:
    op.execute(
        f"DROP TRIGGER IF EXISTS trg_stock_add_operation_events_append_only "
        f"ON {SCHEMA}.stock_add_operation_events"
    )
    op.execute(
        f"DROP TRIGGER IF EXISTS trg_stock_add_operations_append_only "
        f"ON {SCHEMA}.stock_add_operations"
    )
    op.execute(f"DROP FUNCTION IF EXISTS {SCHEMA}.reject_stock_add_journal_mutation()")
    op.drop_index(
        "ix_stock_add_operation_events_operation_time",
        table_name="stock_add_operation_events",
        schema=SCHEMA,
    )
    op.drop_table("stock_add_operation_events", schema=SCHEMA)
    op.drop_table("stock_add_operations", schema=SCHEMA)
