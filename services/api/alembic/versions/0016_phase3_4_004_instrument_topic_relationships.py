"""Phase 3.4-004 instrument-topic relationship domain."""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "0016_phase3_4_004_instrument_topic_relationships"
down_revision = "0015_phase3_4_003_topic_domain"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("instrument_topic_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(32), nullable=False),
        sa.Column("relation_version", sa.String(64), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False), sa.Column("valid_to", sa.Date()),
        sa.Column("relationship_metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["topicpilot.instruments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["topic_id"], ["topicpilot.topics.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from", name="ck_instrument_topic_relation_valid_range"),
        sa.UniqueConstraint("instrument_id", "topic_id", "relation_version", "valid_from", name="uq_instrument_topic_relation_effective"), schema="topicpilot")

def downgrade() -> None:
    op.drop_table("instrument_topic_relations", schema="topicpilot")
