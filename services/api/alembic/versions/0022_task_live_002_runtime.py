"""TASK-LIVE-002 live runtime operations and tracking state."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0022_task_live_002_runtime"
down_revision = "0021_phase3_6_001b_import_audit"
branch_labels = None
depends_on = None


def _common_id():
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)


def upgrade() -> None:
    op.create_table(
        "live_tracking_universe",
        _common_id(),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("market_code", sa.String(32), nullable=False),
        sa.Column("instrument_code", sa.String(64), nullable=False),
        sa.Column("moving_average_period", sa.Integer(), nullable=False),
        sa.Column("moving_average_state", sa.String(16), nullable=False),
        sa.Column("update_mode", sa.String(16), nullable=False),
        sa.Column("latest_close", sa.Numeric(38, 18)),
        sa.Column("moving_average", sa.Numeric(38, 18)),
        sa.Column("observation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reference_observed_at", sa.DateTime(timezone=True)),
        sa.Column("as_of_date", sa.Date()),
        sa.Column("classification_reason", sa.Text(), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["topicpilot.instruments.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["topicpilot.market_data_sources.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("instrument_id", name="uq_live_tracking_universe_instrument"),
        sa.CheckConstraint(
            "update_mode IN ('INTRADAY', 'POST_CLOSE', 'UNKNOWN')",
            name="ck_live_tracking_universe_update_mode",
        ),
        sa.CheckConstraint(
            "moving_average_state IN ('ABOVE', 'BELOW', 'UNKNOWN')",
            name="ck_live_tracking_universe_ma_state",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_live_tracking_universe_mode",
        "live_tracking_universe",
        ["update_mode", "instrument_id"],
        schema="topicpilot",
    )

    op.create_table(
        "live_collector_runs",
        _common_id(),
        sa.Column("run_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("provider_code", sa.String(64), nullable=False),
        sa.Column("adapter_version", sa.String(64), nullable=False),
        sa.Column("config_hash", sa.String(128), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("requested_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("freshness_state", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("provider_status", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("failure_code", sa.String(64)),
        sa.Column("failure_message", sa.Text()),
        sa.Column("metadata", postgresql.JSONB()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "run_type IN ('INTRADAY', 'POST_CLOSE', 'TRACKING_REFRESH')",
            name="ck_live_collector_runs_type",
        ),
        sa.CheckConstraint(
            "status IN ('RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED', 'MARKET_CLOSED', 'WAITING_LIVE_VALIDATION')",
            name="ck_live_collector_runs_status",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_live_collector_runs_started",
        "live_collector_runs",
        ["started_at", "run_type"],
        schema="topicpilot",
    )

    op.create_table(
        "live_collector_attempts",
        _common_id(),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True)),
        sa.Column("instrument_code", sa.String(64), nullable=False),
        sa.Column("market_code", sa.String(32), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True)),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_status", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("freshness_state", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("payload_hash", sa.String(128)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["topicpilot.live_collector_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["topicpilot.instruments.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "status IN ('SUCCESS', 'FAILED', 'TIMEOUT', 'RETRYING', 'SKIPPED')",
            name="ck_live_collector_attempts_status",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_live_collector_attempts_run",
        "live_collector_attempts",
        ["run_id", "started_at"],
        schema="topicpilot",
    )
    op.create_index(
        "ix_live_collector_attempts_instrument",
        "live_collector_attempts",
        ["instrument_id", "observed_at"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_live_collector_attempts_instrument",
        table_name="live_collector_attempts",
        schema="topicpilot",
    )
    op.drop_index(
        "ix_live_collector_attempts_run", table_name="live_collector_attempts", schema="topicpilot"
    )
    op.drop_table("live_collector_attempts", schema="topicpilot")
    op.drop_index(
        "ix_live_collector_runs_started", table_name="live_collector_runs", schema="topicpilot"
    )
    op.drop_table("live_collector_runs", schema="topicpilot")
    op.drop_index(
        "ix_live_tracking_universe_mode", table_name="live_tracking_universe", schema="topicpilot"
    )
    op.drop_table("live_tracking_universe", schema="topicpilot")
