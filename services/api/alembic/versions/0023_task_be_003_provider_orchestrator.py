"""TASK-BE-003 provider metadata for pluggable source resolution."""

import sqlalchemy as sa

from alembic import op

revision = "0023_task_be_003_provider_orchestrator"
down_revision = "0022_task_live_002_runtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "market_data_sources",
        sa.Column("source_rank", sa.Integer(), nullable=False, server_default="100"),
        schema="topicpilot",
    )
    op.create_check_constraint(
        "ck_market_data_sources_source_rank",
        "market_data_sources",
        "source_rank >= 0",
        schema="topicpilot",
    )
    # Preserve the already documented source policy as data metadata.  The
    # collector/router do not contain this list; future registrations provide
    # their own rank through the provider registry.
    op.execute(
        sa.text(
            """
            UPDATE topicpilot.market_data_sources
            SET source_rank = CASE
                WHEN source_code IN ('TWSE_OFFICIAL_DAILY', 'TPEX_OFFICIAL_DAILY') THEN 10
                WHEN source_code = 'TAISHIN_TECH_ANALYSIS' THEN 20
                ELSE source_rank
            END
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_market_data_sources_source_rank", "market_data_sources", schema="topicpilot"
    )
    op.drop_column("market_data_sources", "source_rank", schema="topicpilot")
