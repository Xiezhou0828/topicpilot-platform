"""B2 protected Topic authority activation V1 audit registry."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0038_task_b2_topic_authority_activation_v1"
down_revision = "0037_task_b2_lifecycle_v1_3_formal_publication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topic_authority_activations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("activation_version", sa.String(96), nullable=False),
        sa.Column("artifact_sha256", sa.String(64), nullable=False),
        sa.Column("source_master_sha256", sa.String(64), nullable=False),
        sa.Column("source_revision", sa.String(64), nullable=False),
        sa.Column("target_environment", sa.String(32), nullable=False),
        sa.Column("target_database", sa.String(128), nullable=False),
        sa.Column("operator_id", sa.String(128), nullable=False),
        sa.Column("approval_reference", sa.String(256), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("previous_activation_id", postgresql.UUID(as_uuid=True)),
        sa.Column("active_parent_count", sa.Integer(), nullable=False),
        sa.Column("active_leaf_count", sa.Integer(), nullable=False),
        sa.Column("lifecycle_scope_count", sa.Integer(), nullable=False),
        sa.Column("readback_sha256", sa.String(64), nullable=False),
        sa.Column("artifact", postgresql.JSONB(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["previous_activation_id"],
            ["topicpilot.topic_authority_activations.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "activation_version",
            name="uq_topic_authority_activation_version",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'SUPERSEDED')",
            name="ck_topic_authority_activation_status",
        ),
        sa.CheckConstraint(
            "length(artifact_sha256) = 64 AND length(readback_sha256) = 64",
            name="ck_topic_authority_activation_hashes",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "uq_topic_authority_single_active",
        "topic_authority_activations",
        ["status"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index(
        "uq_topic_authority_single_active",
        table_name="topic_authority_activations",
        schema="topicpilot",
    )
    op.drop_table("topic_authority_activations", schema="topicpilot")
