"""Bind lifecycle shadow rows to formal Topic Daily State lineage.

The columns are additive and nullable for historical shadow rows.  This
migration is an artifact only for this task; it is not executed against a
production database.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0032_task_ws1_topic_lifecycle_contract_gap_closure"
down_revision = "0031_task_topic_structural_role_score_projection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = (
        ("snapshot_id", postgresql.UUID(as_uuid=True)),
        ("snapshot_identity", sa.String(256)),
        ("membership_snapshot_id", sa.String(128)),
        ("membership_snapshot_hash", sa.String(128)),
        ("relation_version", sa.String(128)),
        ("source_artifact_id", sa.String(128)),
        ("source_artifact_hash", sa.String(128)),
        ("lineage_hash", sa.String(128)),
        ("member_fact_hashes", postgresql.JSONB()),
        ("correction_sequence", sa.Integer()),
        ("supersedes_snapshot_id", postgresql.UUID(as_uuid=True)),
        ("superseded_by_snapshot_id", postgresql.UUID(as_uuid=True)),
        ("supersession_state", sa.String(32)),
    )
    for name, column_type in columns:
        op.add_column(
            "topic_lifecycle_results",
            sa.Column(name, column_type, nullable=True),
            schema="topicpilot",
        )
    op.create_foreign_key(
        "fk_topic_lifecycle_results_snapshot",
        "topic_lifecycle_results",
        "topic_snapshots",
        ["snapshot_id"],
        ["id"],
        source_schema="topicpilot",
        referent_schema="topicpilot",
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_topic_lifecycle_results_supersedes_snapshot",
        "topic_lifecycle_results",
        "topic_snapshots",
        ["supersedes_snapshot_id"],
        ["id"],
        source_schema="topicpilot",
        referent_schema="topicpilot",
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_topic_lifecycle_results_superseded_by_snapshot",
        "topic_lifecycle_results",
        "topic_snapshots",
        ["superseded_by_snapshot_id"],
        ["id"],
        source_schema="topicpilot",
        referent_schema="topicpilot",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_topic_lifecycle_results_superseded_by_snapshot",
        "topic_lifecycle_results",
        schema="topicpilot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_topic_lifecycle_results_supersedes_snapshot",
        "topic_lifecycle_results",
        schema="topicpilot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_topic_lifecycle_results_snapshot",
        "topic_lifecycle_results",
        schema="topicpilot",
        type_="foreignkey",
    )
    for name in (
        "supersession_state",
        "superseded_by_snapshot_id",
        "supersedes_snapshot_id",
        "correction_sequence",
        "member_fact_hashes",
        "lineage_hash",
        "source_artifact_hash",
        "source_artifact_id",
        "relation_version",
        "membership_snapshot_hash",
        "membership_snapshot_id",
        "snapshot_identity",
        "snapshot_id",
    ):
        op.drop_column("topic_lifecycle_results", name, schema="topicpilot")
