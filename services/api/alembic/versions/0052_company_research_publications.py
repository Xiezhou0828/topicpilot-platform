"""Store immutable, approved Company Research V4 public projections."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0052_company_research_publications"
down_revision = "0051_stock_add_operation_journal"
branch_labels = None
depends_on = None

SCHEMA = "topicpilot"


def upgrade() -> None:
    op.create_table(
        "company_research_publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("market_code", sa.String(length=32), nullable=False),
        sa.Column("instrument_code", sa.String(length=64), nullable=False),
        sa.Column("publication_version", sa.Integer(), nullable=False),
        sa.Column("research_as_of", sa.Date(), nullable=False),
        sa.Column("source_package_sha256", sa.String(length=64), nullable=False),
        sa.Column("public_payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("public_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("published_by", sa.String(length=128), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("publication_version > 0", name="ck_research_publication_version"),
        sa.CheckConstraint(
            "source_package_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_research_publication_source_sha256",
        ),
        sa.CheckConstraint(
            "public_payload_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_research_publication_payload_sha256",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(public_payload) = 'object' "
            "AND public_payload ->> 'stockCode' = instrument_code "
            "AND public_payload ->> 'publicationStatus' = 'PUBLISHED'",
            name="ck_research_publication_public_payload",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            [f"{SCHEMA}.instruments.id"],
            name="fk_company_research_publications_instrument",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_company_research_publications"),
        sa.UniqueConstraint(
            "instrument_id",
            "publication_version",
            name="uq_company_research_publications_version",
        ),
        sa.UniqueConstraint(
            "instrument_id",
            "source_package_sha256",
            name="uq_company_research_publications_package",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_company_research_publications_latest",
        "company_research_publications",
        ["instrument_id", "publication_version"],
        unique=False,
        schema=SCHEMA,
    )
    op.execute(
        f"""
        CREATE TRIGGER trg_company_research_publications_append_only
        BEFORE UPDATE OR DELETE ON {SCHEMA}.company_research_publications
        FOR EACH ROW
        EXECUTE FUNCTION {SCHEMA}.reject_stock_add_journal_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        f"DROP TRIGGER IF EXISTS trg_company_research_publications_append_only "
        f"ON {SCHEMA}.company_research_publications"
    )
    op.drop_index(
        "ix_company_research_publications_latest",
        table_name="company_research_publications",
        schema=SCHEMA,
    )
    op.drop_table("company_research_publications", schema=SCHEMA)
