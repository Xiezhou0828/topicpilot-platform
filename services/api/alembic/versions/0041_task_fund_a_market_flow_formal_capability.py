"""Add the formal FUND-A daily market institutional-flow fact table."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0041_task_fund_a_market_flow_formal_capability"
down_revision = "0040_task_a10_recovery_checkpoint_observability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_institutional_flow_daily",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("market", sa.String(length=8), nullable=False),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("source_provider", sa.String(length=64), nullable=False),
        sa.Column("source_identity", sa.String(length=128), nullable=False),
        sa.Column("source_dataset", sa.String(length=256), nullable=False),
        sa.Column("source_endpoint", sa.Text(), nullable=False),
        sa.Column("adapter_version", sa.String(length=128), nullable=False),
        sa.Column("source_as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unit", sa.String(length=8), nullable=False),
        sa.Column("scale", sa.Integer(), nullable=False),
        sa.Column("foreign_buy", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("foreign_sell", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("foreign_net", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("investment_trust_buy", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("investment_trust_sell", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("investment_trust_net", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("dealer_buy", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("dealer_sell", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("dealer_net", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("total_buy", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("total_sell", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("total_net", sa.Numeric(precision=38, scale=0), nullable=True),
        sa.Column("availability", sa.String(length=32), nullable=False),
        sa.Column("freshness", sa.String(length=16), nullable=False),
        sa.Column("status_reason", sa.String(length=128), nullable=True),
        sa.Column("lineage", sa.Text(), nullable=False),
        sa.Column("lineage_hash", sa.String(length=128), nullable=False),
        sa.Column("response_content_hash", sa.String(length=128), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.CheckConstraint(
            "market IN ('TPE', 'TWO')",
            name="ck_market_institutional_flow_daily_market",
        ),
        sa.CheckConstraint(
            "availability IN ('AVAILABLE', 'NOT_YET_PUBLISHED', 'SOURCE_UNAVAILABLE', "
            "'INGESTION_FAILED', 'NON_TRADING_DAY')",
            name="ck_market_institutional_flow_daily_availability",
        ),
        sa.CheckConstraint(
            "freshness IN ('CURRENT', 'STALE', 'UNKNOWN')",
            name="ck_market_institutional_flow_daily_freshness",
        ),
        sa.CheckConstraint("unit = 'TWD'", name="ck_market_institutional_flow_daily_unit"),
        sa.CheckConstraint("scale >= 0", name="ck_market_institutional_flow_daily_scale"),
        sa.PrimaryKeyConstraint("id", name="pk_market_institutional_flow_daily"),
        sa.UniqueConstraint(
            "market",
            "trading_date",
            "source_identity",
            name="uq_market_institutional_flow_daily_identity",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_market_institutional_flow_daily_lookup",
        "market_institutional_flow_daily",
        ["market", "trading_date", "source_identity"],
        schema="topicpilot",
    )
    op.create_index(
        "ix_market_institutional_flow_daily_source_as_of",
        "market_institutional_flow_daily",
        ["source_identity", "source_as_of"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_market_institutional_flow_daily_source_as_of",
        table_name="market_institutional_flow_daily",
        schema="topicpilot",
    )
    op.drop_index(
        "ix_market_institutional_flow_daily_lookup",
        table_name="market_institutional_flow_daily",
        schema="topicpilot",
    )
    op.drop_table("market_institutional_flow_daily", schema="topicpilot")
