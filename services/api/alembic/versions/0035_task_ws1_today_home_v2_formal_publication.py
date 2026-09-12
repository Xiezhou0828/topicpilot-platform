"""WS1 Today/Home V2 formal publication persistence.

The tables are additive.  They provide a typed publication envelope and
section/fact status without changing the legacy public bundle bridge.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0035_task_ws1_today_home_v2_formal_publication"
down_revision = "0034_task_ws1_lifecycle_v1_identity_state_machine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "home_publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("as_of_at", sa.DateTime(timezone=True)),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("publication_state", sa.String(32), nullable=False),
        sa.Column("publication_version", sa.String(96), nullable=False),
        sa.Column("source_run_id", sa.String(128)),
        sa.Column("source_dataset_id", sa.String(256), nullable=False),
        sa.Column("lineage_hash", sa.String(128), nullable=False),
        sa.Column("completeness", postgresql.JSONB(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("diagnostic_reason", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "trading_date",
            "source_dataset_id",
            "publication_version",
            name="uq_home_publications_identity",
        ),
        sa.CheckConstraint(
            "publication_state IN ('COLLECTED', 'MATERIALIZED', 'VALIDATED', 'PUBLISHED', 'UNAVAILABLE', 'SUPERSEDED')",
            name="ck_home_publications_state",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_home_publications_latest",
        "home_publications",
        ["publication_state", "trading_date", "published_at", "id"],
        schema="topicpilot",
    )

    op.create_table(
        "home_publication_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_key", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("data_date", sa.Date()),
        sa.Column("as_of_at", sa.DateTime(timezone=True)),
        sa.Column("source", sa.String(256)),
        sa.Column("reason_code", sa.String(96)),
        sa.Column("user_message", sa.Text()),
        sa.Column("diagnostic_detail", sa.Text()),
        sa.Column("payload", postgresql.JSONB()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["publication_id"], ["topicpilot.home_publications.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "publication_id", "section_key", name="uq_home_publication_sections_key"
        ),
        sa.CheckConstraint(
            "status IN ('AVAILABLE', 'PARTIAL', 'UNAVAILABLE')",
            name="ck_home_publication_sections_status",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_home_publication_sections_lookup",
        "home_publication_sections",
        ["publication_id", "section_key"],
        schema="topicpilot",
    )

    op.create_table(
        "home_market_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fact_type", sa.String(16), nullable=False),
        sa.Column("market", sa.String(32), nullable=False),
        sa.Column("index_code", sa.String(64)),
        sa.Column("index_name", sa.String(160)),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("session", sa.String(64)),
        sa.Column("value", sa.Numeric(38, 18)),
        sa.Column("previous_close", sa.Numeric(38, 18)),
        sa.Column("change", sa.Numeric(38, 18)),
        sa.Column("change_pct", sa.Numeric(18, 8)),
        sa.Column("currency", sa.String(3)),
        sa.Column("unit", sa.String(32)),
        sa.Column("scale", sa.Integer()),
        sa.Column("as_of_at", sa.DateTime(timezone=True)),
        sa.Column("source", sa.String(256), nullable=False),
        sa.Column("lineage", sa.Text(), nullable=False),
        sa.Column("publication_state", sa.String(32), nullable=False),
        sa.Column("reason_code", sa.String(96)),
        sa.Column("coverage", postgresql.JSONB()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["publication_id"], ["topicpilot.home_publications.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "publication_id",
            "fact_type",
            "market",
            "index_code",
            name="uq_home_market_facts_identity",
        ),
        sa.CheckConstraint(
            "fact_type IN ('INDEX', 'TURNOVER', 'BREADTH', 'LIMITS')",
            name="ck_home_market_facts_type",
        ),
        sa.CheckConstraint(
            "publication_state IN ('MATERIALIZED', 'VALIDATED', 'PUBLISHED', 'UNAVAILABLE')",
            name="ck_home_market_facts_state",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_home_market_facts_publication",
        "home_market_facts",
        ["publication_id", "fact_type", "market"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_home_market_facts_publication",
        table_name="home_market_facts",
        schema="topicpilot",
    )
    op.drop_table("home_market_facts", schema="topicpilot")
    op.drop_index(
        "ix_home_publication_sections_lookup",
        table_name="home_publication_sections",
        schema="topicpilot",
    )
    op.drop_table("home_publication_sections", schema="topicpilot")
    op.drop_index("ix_home_publications_latest", table_name="home_publications", schema="topicpilot")
    op.drop_table("home_publications", schema="topicpilot")
