"""Allow checkpoint provider counters to represent not-applicable metrics."""

import sqlalchemy as sa

from alembic import op

revision = "0048_task_checkpoint_provider_metric_applicability"
down_revision = "0047_task_topic_role_strength_design_freeze"
branch_labels = None
depends_on = None

SCHEMA = "topicpilot"
TABLE = "live_collector_checkpoints"
COLUMNS = ("provider_request_count", "provider_failure_count")


def upgrade() -> None:
    """Make only the two metric columns nullable; preserve all existing values."""

    for column in COLUMNS:
        op.alter_column(
            TABLE,
            column,
            schema=SCHEMA,
            existing_type=sa.Integer(),
            existing_nullable=False,
            existing_server_default=sa.text("0"),
            nullable=True,
            server_default=None,
        )


def downgrade() -> None:
    """Refuse rollback if a new N/A checkpoint would be destroyed."""

    connection = op.get_bind()
    for column in COLUMNS:
        null_count = int(
            connection.execute(
                sa.text(
                    f"SELECT count(*) FROM {SCHEMA}.{TABLE} "
                    f"WHERE {column} IS NULL"
                )
            ).scalar_one()
        )
        if null_count:
            raise RuntimeError(
                f"Cannot downgrade 0048: {TABLE}.{column} contains "
                f"{null_count} NULL N/A values; no historical rewrite is authorized"
            )
        op.alter_column(
            TABLE,
            column,
            schema=SCHEMA,
            existing_type=sa.Integer(),
            existing_nullable=True,
            existing_server_default=None,
            nullable=False,
            server_default=sa.text("0"),
        )
