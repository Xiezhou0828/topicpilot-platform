"""Phase 3.5-002A versioned reference registry."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0020_phase3_5_002a_reference_registry"
down_revision = "0019_phase3_5_001b_canonical_observations"
branch_labels = None
depends_on = None


def upgrade():
    def uuid():
        return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)

    op.create_table(
        "reference_registry_sets",
        uuid(),
        sa.Column("reference_data_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("description", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("reference_data_version", name="uq_reference_registry_sets_version"),
        schema="topicpilot",
    )
    specs = {
        "reference_currencies": [("code", sa.String(3)), ("scale", sa.SmallInteger)],
        "reference_timezones": [("name", sa.String(64))],
        "reference_sessions": [("code", sa.String(64)), ("calendar_code", sa.String(64))],
        "reference_trading_statuses": [("code", sa.String(32))],
        "reference_adjustments": [("code", sa.String(32))],
    }
    for table, fields in specs.items():
        cols = [
            uuid(),
            sa.Column("registry_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        ] + [sa.Column(n, t, nullable=False) for n, t in fields]
        cols += [
            sa.ForeignKeyConstraint(
                ["registry_set_id"], ["topicpilot.reference_registry_sets.id"], ondelete="RESTRICT"
            ),
            sa.UniqueConstraint(
                "registry_set_id", fields[0][0], name=f"uq_{table}_registry_{fields[0][0]}"
            ),
        ]
        op.create_table(table, *cols, schema="topicpilot")


def downgrade():
    for table in [
        "reference_adjustments",
        "reference_trading_statuses",
        "reference_sessions",
        "reference_timezones",
        "reference_currencies",
        "reference_registry_sets",
    ]:
        op.drop_table(table, schema="topicpilot")
