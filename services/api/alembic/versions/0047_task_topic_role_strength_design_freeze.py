"""Widen Score Projection importance for the REP/CORE Design Freeze.

The database constraint is additive.  Existing 0.25 rows from migration 0043
remain readable as historical compatibility data, while the application
resolver rejects them for current projections.  No persisted row is rewritten
or assigned a guessed Structural Role.
"""

import sqlalchemy as sa

from alembic import op

revision = "0047_task_topic_role_strength_design_freeze"
down_revision = "0046_task_stock_maint_relation_weight_authority_001d"
branch_labels = None
depends_on = None

TABLE = "topic_score_projection_members"
SCHEMA = "topicpilot"
CONSTRAINT = "ck_topic_score_projection_member_importance"


def upgrade() -> None:
    op.drop_constraint(CONSTRAINT, TABLE, schema=SCHEMA, type_="check")
    op.create_check_constraint(
        CONSTRAINT,
        TABLE,
        "score_importance IN (0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75)",
        schema=SCHEMA,
    )


def downgrade() -> None:
    bind = op.get_bind()
    stale = int(
        bind.execute(
            sa.text(
                "SELECT count(*) FROM topicpilot.topic_score_projection_members "
                "WHERE score_importance IN (1.25, 1.50, 1.75)"
            )
        ).scalar_one()
    )
    if stale:
        raise RuntimeError(
            "Design Freeze downgrade refused: current REP importance rows exist; "
            "no automatic REP-to-legacy migration is authorized"
        )
    op.drop_constraint(CONSTRAINT, TABLE, schema=SCHEMA, type_="check")
    op.create_check_constraint(
        CONSTRAINT,
        TABLE,
        "score_importance IN (0.25, 0.50, 0.75, 1.00)",
        schema=SCHEMA,
    )
