"""Phase 3.4-005 market-data source and raw observation foundation."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0017_phase3_4_005_market_data_source_and_raw_observations"
down_revision = "0016_phase3_4_004_instrument_topic_relationships"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_data_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_code", sa.String(64), nullable=False),
        sa.Column("source_category", sa.String(32), nullable=False),
        sa.Column("adapter_version", sa.String(64), nullable=False),
        sa.Column("observation_semantics", sa.String(64)),
        sa.Column("adjustment_policy", sa.String(64)),
        sa.Column("calendar_policy", sa.String(64)),
        sa.Column("licensing_classification", sa.String(64)),
        sa.Column("status", sa.String(32), server_default="REGISTERED", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_code", "adapter_version", name="uq_market_data_sources_identity"),
        schema="topicpilot",
    )
    op.create_table(
        "raw_market_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True)),
        sa.Column("upstream_observation_id", sa.String(160)),
        sa.Column("source_instrument_identifier", sa.String(128), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("quality_status", sa.String(32), server_default="CAPTURED", nullable=False),
        sa.Column("ingestion_correlation_id", sa.String(128)),
        sa.Column("supersedes_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["topicpilot.market_data_sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["instrument_id"], ["topicpilot.instruments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supersedes_id"], ["topicpilot.raw_market_observations.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("source_id", "content_hash", name="uq_raw_market_observations_source_hash"),
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_table("raw_market_observations", schema="topicpilot")
    op.drop_table("market_data_sources", schema="topicpilot")
