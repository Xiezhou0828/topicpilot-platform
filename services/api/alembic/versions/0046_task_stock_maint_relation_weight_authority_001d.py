"""Add the separate effective-dated Relation Weight authority.

This migration is additive and creates no rows.  Proposal generation and
Owner approval are deliberately separate, non-production workflows.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0046_task_stock_maint_relation_weight_authority_001d"
down_revision = "0045_task_m1_formal_score_grade_publication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "relation_weight_authorities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "relation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topicpilot.instrument_topic_relations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "instrument_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topicpilot.instruments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topicpilot.topics.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("relation_type", sa.String(32), nullable=False),
        sa.Column("weight", sa.Numeric(12, 4), nullable=False),
        sa.Column("legacy_original_value", sa.Numeric(12, 4)),
        sa.Column("legacy_recovery_evidence", postgresql.JSONB()),
        sa.Column("approval_state", sa.String(16), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.Column("authority_version", sa.String(64), nullable=False),
        sa.Column("approval_reference", sa.String(256)),
        sa.Column("source_kind", sa.String(64), nullable=False),
        sa.Column("source_artifact_id", sa.String(256)),
        sa.Column("source_artifact_hash", sa.String(128)),
        sa.Column("source_location", sa.String(512)),
        sa.Column("proposal_reason", sa.String(256)),
        sa.Column("correction_sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("supersedes_id", postgresql.UUID(as_uuid=True)),
        sa.Column("lineage_hash", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["supersedes_id"],
            ["topicpilot.relation_weight_authorities.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "relation_id",
            "authority_version",
            "effective_from",
            "correction_sequence",
            name="uq_relation_weight_authority_revision",
        ),
        sa.CheckConstraint(
            "relation_type IN ('PRIMARY', 'SECONDARY')",
            name="ck_relation_weight_authority_relation_type",
        ),
        sa.CheckConstraint(
            "approval_state IN ('PROPOSED', 'APPROVED')",
            name="ck_relation_weight_authority_approval_state",
        ),
        sa.CheckConstraint(
            "effective_from >= DATE '2026-09-24'",
            name="ck_relation_weight_authority_not_backdated",
        ),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_relation_weight_authority_valid_range",
        ),
        sa.CheckConstraint(
            "correction_sequence >= 0",
            name="ck_relation_weight_authority_correction_sequence",
        ),
        sa.CheckConstraint(
            "(relation_type = 'PRIMARY' AND weight >= 0.5 AND weight <= 2.0) OR "
            "(relation_type = 'SECONDARY' AND weight >= 0.3 AND weight <= 0.8)",
            name="ck_relation_weight_authority_weight_range",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_relation_weight_authority_effective",
        "relation_weight_authorities",
        ["relation_id", "effective_from", "effective_to", "approval_state", "correction_sequence"],
        schema="topicpilot",
    )
    op.create_index(
        "ix_relation_weight_authority_identity",
        "relation_weight_authorities",
        ["instrument_id", "topic_id", "relation_type", "effective_from", "approval_state"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_relation_weight_authority_identity",
        table_name="relation_weight_authorities",
        schema="topicpilot",
    )
    op.drop_index(
        "ix_relation_weight_authority_effective",
        table_name="relation_weight_authorities",
        schema="topicpilot",
    )
    op.drop_table("relation_weight_authorities", schema="topicpilot")
