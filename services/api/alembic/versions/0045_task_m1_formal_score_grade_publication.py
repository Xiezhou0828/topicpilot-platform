"""Persist formal Topic Score and Grade publication results."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0045_task_m1_formal_score_grade_publication"
down_revision = "0044_task_m1_formal_opportunity_publication"
branch_labels = None
depends_on = None

SCHEMA = "topicpilot"
TABLE = "topic_score_formal_results"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluation_date", sa.Date(), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_slug", sa.String(length=128), nullable=False),
        sa.Column("evaluation_status", sa.String(length=32), nullable=False),
        sa.Column("eligibility", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Numeric(precision=12, scale=4)),
        sa.Column("grade", sa.String(length=8)),
        sa.Column("components", postgresql.JSONB()),
        sa.Column("eligibility_audit", postgresql.JSONB()),
        sa.Column("quality_flags", postgresql.JSONB()),
        sa.Column("publication_status", sa.String(length=24), nullable=False),
        sa.Column("publication_mode", sa.String(length=16), nullable=False),
        sa.Column("contract_version", sa.String(length=96), nullable=False),
        sa.Column("calculation_version", sa.String(length=96), nullable=False),
        sa.Column("policy_id", sa.String(length=128), nullable=False),
        sa.Column("policy_version", sa.String(length=96), nullable=False),
        sa.Column("d001_projection_id", sa.String(length=128)),
        sa.Column("d001_projection_version", sa.String(length=96)),
        sa.Column("input_snapshot_id", postgresql.UUID(as_uuid=True)),
        sa.Column("input_snapshot_identity", sa.String(length=256)),
        sa.Column("input_snapshot_hash", sa.String(length=128)),
        sa.Column("membership_snapshot_id", sa.String(length=128)),
        sa.Column("membership_snapshot_hash", sa.String(length=128)),
        sa.Column("relation_version", sa.String(length=128)),
        sa.Column("reference_registry_version", sa.String(length=64)),
        sa.Column("mapping_policy_version", sa.String(length=96)),
        sa.Column("session_code", sa.String(length=128)),
        sa.Column("calendar_code", sa.String(length=128)),
        sa.Column("source_artifact_id", sa.String(length=128)),
        sa.Column("source_artifact_hash", sa.String(length=128)),
        sa.Column("lineage", postgresql.JSONB()),
        sa.Column("lineage_hash", sa.String(length=128)),
        sa.Column("member_fact_hashes", postgresql.JSONB()),
        sa.Column("decision_revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("supersedes_decision_id", postgresql.UUID(as_uuid=True)),
        sa.Column("supersession_reason", sa.String(length=128)),
        sa.Column("supersession_state", sa.String(length=16), nullable=False, server_default="ACTIVE"),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("as_of_at", sa.DateTime(timezone=True)),
        sa.Column("generated_at", sa.DateTime(timezone=True)),
        sa.Column("diagnostic_detail", sa.Text()),
        sa.PrimaryKeyConstraint("id", name="pk_topic_score_formal_results"),
        sa.ForeignKeyConstraint(["topic_id"], ["topicpilot.topics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["input_snapshot_id"], ["topicpilot.topic_snapshots.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supersedes_decision_id"], ["topicpilot.topic_score_formal_results.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("publication_mode = 'FORMAL'", name="ck_topic_score_formal_publication_mode"),
        sa.CheckConstraint(
            "publication_status IN ('UNAVAILABLE', 'PUBLISHED', 'SUPERSEDED')",
            name="ck_topic_score_formal_publication_status",
        ),
        sa.CheckConstraint(
            "supersession_state IN ('ACTIVE', 'SUPERSEDED')",
            name="ck_topic_score_formal_supersession_state",
        ),
        sa.UniqueConstraint(
            "topic_id", "evaluation_date", "contract_version", "decision_revision",
            name="uq_topic_score_formal_identity",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_topic_score_formal_topic_date", TABLE,
        ["topic_id", "evaluation_date", "publication_status"], schema=SCHEMA
    )
    op.create_index(
        "ix_topic_score_formal_date", TABLE,
        ["evaluation_date", "topic_slug", "publication_status"], schema=SCHEMA
    )


def downgrade() -> None:
    op.drop_index("ix_topic_score_formal_date", table_name=TABLE, schema=SCHEMA)
    op.drop_index("ix_topic_score_formal_topic_date", table_name=TABLE, schema=SCHEMA)
    op.drop_table(TABLE, schema=SCHEMA)
