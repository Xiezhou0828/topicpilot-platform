"""Add the FUND-B stock-level institutional-flow evidence surface.

This is the forward canonical migration for the FUND-B capability.  The
source task's historical 0033 artifact was created from the 0032 branch and
is retained only as provenance; it is not part of the current chain.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0042_task_fund_b_stock_institutional_flow_forward"
down_revision = "0041_task_fund_a_market_flow_formal_capability"
branch_labels = None
depends_on = None

_STATUS_VALUES = (
    "'OK', 'NO_DATA', 'NOT_TRADING_DAY', 'PROVIDER_UNAVAILABLE', 'AUTH_ERROR', "
    "'RATE_LIMITED', 'SCHEMA_ERROR', 'MAPPING_ERROR', 'PARTIAL', 'STALE', 'UNKNOWN'"
)


def upgrade() -> None:
    op.create_table(
        "stock_institutional_flow_daily",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("market", sa.String(8), nullable=False),
        sa.Column("instrument_code", sa.String(64), nullable=False),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("source_provider", sa.String(64), nullable=False),
        sa.Column("source_identity", sa.String(128), nullable=False),
        sa.Column("source_dataset", sa.String(256), nullable=False),
        sa.Column("source_endpoint", sa.Text(), nullable=False),
        sa.Column("adapter_version", sa.String(128), nullable=False),
        sa.Column("source_as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("unit", sa.String(16), nullable=False, server_default="SHARES"),
        sa.Column("scale", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("foreign_buy", sa.Numeric(38, 0), nullable=False),
        sa.Column("foreign_sell", sa.Numeric(38, 0), nullable=False),
        sa.Column("foreign_net", sa.Numeric(38, 0), nullable=False),
        sa.Column("investment_trust_buy", sa.Numeric(38, 0), nullable=False),
        sa.Column("investment_trust_sell", sa.Numeric(38, 0), nullable=False),
        sa.Column("investment_trust_net", sa.Numeric(38, 0), nullable=False),
        sa.Column("dealer_buy", sa.Numeric(38, 0), nullable=False),
        sa.Column("dealer_sell", sa.Numeric(38, 0), nullable=False),
        sa.Column("dealer_net", sa.Numeric(38, 0), nullable=False),
        sa.Column("total_buy", sa.Numeric(38, 0), nullable=False),
        sa.Column("total_sell", sa.Numeric(38, 0), nullable=False),
        sa.Column("total_net", sa.Numeric(38, 0), nullable=False),
        sa.Column("foreign_dealer_buy", sa.Numeric(38, 0), nullable=True),
        sa.Column("foreign_dealer_sell", sa.Numeric(38, 0), nullable=True),
        sa.Column("foreign_dealer_net", sa.Numeric(38, 0), nullable=True),
        sa.Column("dealer_self_buy", sa.Numeric(38, 0), nullable=True),
        sa.Column("dealer_self_sell", sa.Numeric(38, 0), nullable=True),
        sa.Column("dealer_self_net", sa.Numeric(38, 0), nullable=True),
        sa.Column("dealer_hedge_buy", sa.Numeric(38, 0), nullable=True),
        sa.Column("dealer_hedge_sell", sa.Numeric(38, 0), nullable=True),
        sa.Column("dealer_hedge_net", sa.Numeric(38, 0), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="OK"),
        sa.Column("freshness", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("status_reason", sa.String(256), nullable=True),
        sa.Column("lineage", sa.Text(), nullable=False),
        sa.Column("response_content_hash", sa.String(128), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_stock_institutional_flow_daily"),
        sa.UniqueConstraint(
            "instrument_id",
            "trading_date",
            "source_identity",
            name="uq_stock_institutional_flow_daily_identity",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["topicpilot.instruments.id"],
            name="fk_stock_institutional_flow_daily_instrument",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "market IN ('TPE', 'TWO')",
            name="ck_stock_institutional_flow_daily_market",
        ),
        sa.CheckConstraint(
            f"status IN ({_STATUS_VALUES})",
            name="ck_stock_institutional_flow_daily_status",
        ),
        sa.CheckConstraint(
            "freshness IN ('CURRENT', 'STALE', 'UNKNOWN')",
            name="ck_stock_institutional_flow_daily_freshness",
        ),
        sa.CheckConstraint("unit = 'SHARES'", name="ck_stock_institutional_flow_daily_unit"),
        sa.CheckConstraint("scale = 0", name="ck_stock_institutional_flow_daily_scale"),
        schema="topicpilot",
    )
    op.create_index(
        "ix_stock_institutional_flow_daily_instrument_date",
        "stock_institutional_flow_daily",
        ["instrument_id", "trading_date"],
        schema="topicpilot",
    )
    op.create_index(
        "ix_stock_institutional_flow_daily_source_as_of",
        "stock_institutional_flow_daily",
        ["source_identity", "source_as_of"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_stock_institutional_flow_daily_source_as_of",
        table_name="stock_institutional_flow_daily",
        schema="topicpilot",
    )
    op.drop_index(
        "ix_stock_institutional_flow_daily_instrument_date",
        table_name="stock_institutional_flow_daily",
        schema="topicpilot",
    )
    op.drop_table("stock_institutional_flow_daily", schema="topicpilot")
