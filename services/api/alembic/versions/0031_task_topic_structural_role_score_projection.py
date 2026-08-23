"""Minimal Structural Role Authority and Score Projection V1 read models.

The relation extension is nullable so legacy/non-formal relation rows remain
readable.  Formal consumers must use the explicit authority/projection fields
and their fail-closed resolvers; this migration performs no data assignment.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0031_task_topic_structural_role_score_projection"
down_revision = "0030_task_topic_daily_state_formal_authority"
branch_labels = None
depends_on = None


_RELATION_COLUMNS = (
    ("structural_role", sa.String(32)),
    ("approval_state", sa.String(32)),
    ("authority_version", sa.String(64)),
    ("source_artifact_id", sa.String(128)),
    ("source_artifact_hash", sa.String(128)),
    ("approval_reference", sa.String(256)),
    ("correction_sequence", sa.Integer(), sa.text("0")),
    ("supersedes_authority_id", postgresql.UUID(as_uuid=True)),
    ("superseded_by_authority_id", postgresql.UUID(as_uuid=True)),
    ("lineage_hash", sa.String(128)),
)


def upgrade() -> None:
    for item in _RELATION_COLUMNS:
        name, column_type, *default = item
        op.add_column(
            "instrument_topic_relations",
            sa.Column(
                name,
                column_type,
                nullable=True,
                server_default=default[0] if default else None,
            ),
            schema="topicpilot",
        )

    op.create_check_constraint(
        "ck_instrument_topic_relation_structural_role",
        "instrument_topic_relations",
        "structural_role IS NULL OR structural_role IN ('REPRESENTATIVE', 'CORE', 'RELATED')",
        schema="topicpilot",
    )
    op.create_check_constraint(
        "ck_instrument_topic_relation_approval_state",
        "instrument_topic_relations",
        "approval_state IS NULL OR approval_state IN ('DRAFT', 'PROPOSED', 'APPROVED', 'DEPRECATED', 'REJECTED')",
        schema="topicpilot",
    )
    op.create_check_constraint(
        "ck_instrument_topic_relation_correction_sequence",
        "instrument_topic_relations",
        "correction_sequence IS NULL OR correction_sequence >= 0",
        schema="topicpilot",
    )
    op.create_foreign_key(
        "fk_instrument_topic_relations_supersedes_authority_id",
        "instrument_topic_relations",
        "instrument_topic_relations",
        ["supersedes_authority_id"],
        ["id"],
        source_schema="topicpilot",
        referent_schema="topicpilot",
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_instrument_topic_relations_superseded_by_authority_id",
        "instrument_topic_relations",
        "instrument_topic_relations",
        ["superseded_by_authority_id"],
        ["id"],
        source_schema="topicpilot",
        referent_schema="topicpilot",
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_instrument_topic_relations_structural_role_effective",
        "instrument_topic_relations",
        [
            "topic_id",
            "instrument_id",
            "structural_role",
            "approval_state",
            "valid_from",
            "valid_to",
            "superseded_by_authority_id",
        ],
        schema="topicpilot",
    )

    op.create_table(
        "topic_score_projections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("projection_id", sa.String(128), nullable=False),
        sa.Column("projection_version", sa.String(64), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.Column("approval_state", sa.String(32), nullable=False),
        sa.Column("approval_reference", sa.String(256), nullable=False),
        sa.Column("source_structural_role_authority_id", sa.String(128), nullable=False),
        sa.Column("source_structural_role_authority_version", sa.String(64), nullable=False),
        sa.Column("projection_lineage", postgresql.JSONB(), nullable=False),
        sa.Column("lineage_hash", sa.String(128), nullable=False),
        sa.Column("correction_sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("supersedes_projection_id", postgresql.UUID(as_uuid=True)),
        sa.Column("superseded_by_projection_id", postgresql.UUID(as_uuid=True)),
        sa.Column("supersession_reason", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topicpilot.topics.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_projection_id"],
            ["topicpilot.topic_score_projections.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["superseded_by_projection_id"],
            ["topicpilot.topic_score_projections.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("projection_id", name="uq_topic_score_projections_projection_id"),
        sa.UniqueConstraint(
            "topic_id",
            "projection_version",
            "effective_from",
            name="uq_topic_score_projections_effective",
        ),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_topic_score_projections_valid_range",
        ),
        sa.CheckConstraint(
            "approval_state IN ('DRAFT', 'PROPOSED', 'APPROVED', 'DEPRECATED', 'REJECTED')",
            name="ck_topic_score_projections_approval_state",
        ),
        sa.CheckConstraint(
            "correction_sequence >= 0",
            name="ck_topic_score_projections_correction_sequence",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_topic_score_projections_effective",
        "topic_score_projections",
        [
            "topic_id",
            "effective_from",
            "effective_to",
            "approval_state",
            "superseded_by_projection_id",
        ],
        schema="topicpilot",
    )

    op.create_table(
        "topic_score_projection_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("projection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("structural_role_authority_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("structural_role_authority_version", sa.String(64), nullable=False),
        sa.Column("score_importance", sa.Numeric(3, 2), nullable=False),
        sa.Column("member_lineage", postgresql.JSONB()),
        sa.ForeignKeyConstraint(
            ["projection_id"],
            ["topicpilot.topic_score_projections.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["topicpilot.instruments.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["structural_role_authority_id"],
            ["topicpilot.instrument_topic_relations.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "projection_id",
            "instrument_id",
            name="uq_topic_score_projection_members_member",
        ),
        sa.CheckConstraint(
            "score_importance IN (0.50, 0.75, 1.00)",
            name="ck_topic_score_projection_member_importance",
        ),
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_table("topic_score_projection_members", schema="topicpilot")
    op.drop_index(
        "ix_topic_score_projections_effective",
        table_name="topic_score_projections",
        schema="topicpilot",
    )
    op.drop_table("topic_score_projections", schema="topicpilot")
    op.drop_index(
        "ix_instrument_topic_relations_structural_role_effective",
        table_name="instrument_topic_relations",
        schema="topicpilot",
    )
    op.drop_constraint(
        "fk_instrument_topic_relations_superseded_by_authority_id",
        "instrument_topic_relations",
        schema="topicpilot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_instrument_topic_relations_supersedes_authority_id",
        "instrument_topic_relations",
        schema="topicpilot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "ck_instrument_topic_relation_correction_sequence",
        "instrument_topic_relations",
        schema="topicpilot",
        type_="check",
    )
    op.drop_constraint(
        "ck_instrument_topic_relation_approval_state",
        "instrument_topic_relations",
        schema="topicpilot",
        type_="check",
    )
    op.drop_constraint(
        "ck_instrument_topic_relation_structural_role",
        "instrument_topic_relations",
        schema="topicpilot",
        type_="check",
    )
    for item in reversed(_RELATION_COLUMNS):
        op.drop_column("instrument_topic_relations", item[0], schema="topicpilot")
