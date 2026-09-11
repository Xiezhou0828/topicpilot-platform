"""Append-only A9/B2 formal correction supersession."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0039_task_a9_b2_formal_correction_supersession"
down_revision = "0038_task_b2_topic_authority_activation_v1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_topic_lifecycle_formal_identity",
        "topic_lifecycle_formal_results",
        schema="topicpilot",
        type_="unique",
    )
    op.add_column(
        "topic_lifecycle_formal_results",
        sa.Column("decision_revision", sa.Integer(), nullable=False, server_default="0"),
        schema="topicpilot",
    )
    op.add_column(
        "topic_lifecycle_formal_results",
        sa.Column("supersedes_decision_id", postgresql.UUID(as_uuid=True)),
        schema="topicpilot",
    )
    op.add_column(
        "topic_lifecycle_formal_results",
        sa.Column("supersession_reason", sa.String(128)),
        schema="topicpilot",
    )
    op.create_foreign_key(
        "fk_topic_lifecycle_formal_supersedes_decision",
        "topic_lifecycle_formal_results",
        "topic_lifecycle_formal_results",
        ["supersedes_decision_id"],
        ["id"],
        source_schema="topicpilot",
        referent_schema="topicpilot",
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_topic_lifecycle_formal_identity",
        "topic_lifecycle_formal_results",
        ["topic_id", "evaluation_date", "contract_version", "decision_revision"],
        schema="topicpilot",
    )
    op.create_unique_constraint(
        "uq_topic_lifecycle_formal_supersedes_once",
        "topic_lifecycle_formal_results",
        ["supersedes_decision_id"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_topic_lifecycle_formal_supersedes_once",
        "topic_lifecycle_formal_results",
        schema="topicpilot",
        type_="unique",
    )
    op.drop_constraint(
        "uq_topic_lifecycle_formal_identity",
        "topic_lifecycle_formal_results",
        schema="topicpilot",
        type_="unique",
    )
    op.drop_constraint(
        "fk_topic_lifecycle_formal_supersedes_decision",
        "topic_lifecycle_formal_results",
        schema="topicpilot",
        type_="foreignkey",
    )
    op.drop_column("topic_lifecycle_formal_results", "supersession_reason", schema="topicpilot")
    op.drop_column("topic_lifecycle_formal_results", "supersedes_decision_id", schema="topicpilot")
    op.drop_column("topic_lifecycle_formal_results", "decision_revision", schema="topicpilot")
    op.create_unique_constraint(
        "uq_topic_lifecycle_formal_identity",
        "topic_lifecycle_formal_results",
        ["topic_id", "evaluation_date", "contract_version"],
        schema="topicpilot",
    )
