"""Persist the formal Opportunity provider publication envelope."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0044_task_m1_formal_opportunity_publication"
down_revision = "0043_task_m1_role_based_d001_importance"
branch_labels = None
depends_on = None

SCHEMA = "topicpilot"
TABLE = "formal_opportunity_publications"


def _json_type() -> sa.types.TypeEngine:
    return postgresql.JSONB()


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("publication_state", sa.String(length=24), nullable=False),
        sa.Column("authority_version", sa.String(length=96), nullable=False),
        sa.Column("contract_version", sa.String(length=96), nullable=False),
        sa.Column("publication_key", sa.String(length=256), nullable=False),
        sa.Column("provider_version", sa.String(length=96), nullable=False),
        sa.Column("source_artifact_id", sa.String(length=256), nullable=False),
        sa.Column("source_artifact_hash", sa.String(length=128), nullable=False),
        sa.Column("lineage_hash", sa.String(length=128), nullable=False),
        sa.Column("page_payload", _json_type(), nullable=False),
        sa.Column("detail_payloads", _json_type(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("diagnostic_reason", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_formal_opportunity_publications"),
        sa.UniqueConstraint(
            "publication_key", name="uq_formal_opportunity_publication_key"
        ),
        sa.CheckConstraint(
            "publication_state IN ('PUBLISHED', 'EMPTY', 'DEFERRED', 'UNAVAILABLE', 'SUPERSEDED')",
            name="ck_formal_opportunity_publication_state",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_formal_opportunity_publication_lookup",
        TABLE,
        ["as_of", "publication_state", "created_at"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_formal_opportunity_publication_lookup", table_name=TABLE, schema=SCHEMA
    )
    op.drop_table(TABLE, schema=SCHEMA)
