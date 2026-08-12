"""Phase 3.4-003 topic domain."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0015_phase3_4_003_topic_domain"
down_revision = "0014_phase3_4_002_identity_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(32), server_default="PROPOSED", nullable=False),
        sa.Column("dictionary_version", sa.String(64)),
        sa.Column("valid_from", sa.Date()),
        sa.Column("valid_to", sa.Date()),
        sa.Column("display_metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="ck_topics_valid_range"),
        sa.UniqueConstraint("slug", name="uq_topics_slug"),
        schema="topicpilot",
    )
    op.create_table(
        "topic_hierarchy",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("parent_topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("child_topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(32), server_default="PARENT", nullable=False),
        sa.Column("hierarchy_version", sa.String(64), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date()),
        sa.Column("display_order", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_topic_id"], ["topicpilot.topics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["child_topic_id"], ["topicpilot.topics.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("parent_topic_id <> child_topic_id", name="ck_topic_hierarchy_no_self_parent"),
        sa.CheckConstraint("valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="ck_topic_hierarchy_valid_range"),
        sa.UniqueConstraint("parent_topic_id", "child_topic_id", "hierarchy_version", "valid_from", name="uq_topic_hierarchy_effective"),
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_table("topic_hierarchy", schema="topicpilot")
    op.drop_table("topics", schema="topicpilot")
