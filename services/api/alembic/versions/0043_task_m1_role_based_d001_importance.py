"""Move D001 Score member importance to the DEC-04 role projection.

This is intentionally a forward-only constraint change.  Existing 0.50 rows
are not rewritten or guessed into RELATED; the migration aborts before the
constraint is changed so an operator must resolve any stale persisted data
through an explicit governed correction.
"""

import sqlalchemy as sa

from alembic import context, op

revision = "0043_task_m1_role_based_d001_importance"
down_revision = "0042_task_fund_b_stock_institutional_flow_forward"
branch_labels = None
depends_on = None

TABLE = "topic_score_projection_members"
SCHEMA = "topicpilot"
CONSTRAINT = "ck_topic_score_projection_member_importance"


def _count_value(value: str) -> int:
    if context.is_offline_mode():
        return 0
    bind = op.get_bind()
    return int(
        bind.execute(
            sa.text(
                "SELECT count(*) FROM topicpilot.topic_score_projection_members "
                "WHERE score_importance = CAST(:value AS NUMERIC)"
            ),
            {"value": value},
        ).scalar_one()
    )


def upgrade() -> None:
    stale = _count_value("0.50")
    if stale:
        raise RuntimeError(
            "DEC-04 migration refused: persisted 0.50 Score projection rows exist; "
            "no automatic 0.50-to-0.25 migration is authorized"
        )
    op.drop_constraint(CONSTRAINT, TABLE, schema=SCHEMA, type_="check")
    op.create_check_constraint(
        CONSTRAINT,
        TABLE,
        "score_importance IN (0.25, 0.75, 1.00)",
        schema=SCHEMA,
    )


def downgrade() -> None:
    current = _count_value("0.25")
    if current:
        raise RuntimeError(
            "DEC-04 downgrade refused: persisted 0.25 Score projection rows exist; "
            "no automatic RELATED-to-legacy migration is authorized"
        )
    op.drop_constraint(CONSTRAINT, TABLE, schema=SCHEMA, type_="check")
    op.create_check_constraint(
        CONSTRAINT,
        TABLE,
        "score_importance IN (0.50, 0.75, 1.00)",
        schema=SCHEMA,
    )
