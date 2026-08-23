"""Formal Topic Daily State authority and immutable member facts.

This is an additive extension of the existing V2 ``topic_snapshots`` table.
Research/legacy rows remain readable, while formal consumers can only select
published, non-superseded PIT rows.  Corrections create a new immutable row and
link the previous row through explicit supersession fields.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0030_task_topic_daily_state_formal_authority"
down_revision = "0029_task_data_ref_006e_instrument_lifecycle"
branch_labels = None
depends_on = None


_ADDED_COLUMNS = (
    ("publication_mode", sa.String(32), "'RESEARCH_ONLY'"),
    ("membership_mode", sa.String(64), "'CURRENT_MAPPING_RECONSTRUCTED_RESEARCH_ONLY'"),
    ("relation_version", sa.String(128), None),
    ("mapping_effective_from", sa.Date(), None),
    ("membership_snapshot_id", sa.String(128), None),
    ("membership_snapshot_hash", sa.String(128), None),
    ("session_code", sa.String(128), None),
    ("calendar_code", sa.String(128), None),
    ("trading_day_state", sa.String(32), "'UNKNOWN'"),
    ("generated_state", sa.String(32), "'UNKNOWN'"),
    ("finality_state", sa.String(32), "'UNKNOWN'"),
    ("publication_state", sa.String(32), "'UNPUBLISHED'"),
    ("generated_at", sa.DateTime(timezone=True), None),
    ("as_of_at", sa.DateTime(timezone=True), None),
    ("finalized_at", sa.DateTime(timezone=True), None),
    ("published_at", sa.DateTime(timezone=True), None),
    ("expected_count", sa.Integer(), None),
    ("eligible_count", sa.Integer(), None),
    ("no_trade_count", sa.Integer(), None),
    ("unknown_count", sa.Integer(), None),
    ("excluded_count", sa.Integer(), None),
    ("positive_count", sa.Integer(), None),
    ("flat_count", sa.Integer(), None),
    ("negative_count", sa.Integer(), None),
    ("freshness_state", sa.String(32), None),
    ("unavailable_reason", sa.Text(), None),
    ("quality_flags", postgresql.JSONB(), None),
    ("reference_registry_version", sa.String(64), None),
    ("mapping_policy_version", sa.String(96), None),
    ("source_run_id", sa.String(128), None),
    ("source_artifact_id", sa.String(128), None),
    ("source_artifact_hash", sa.String(128), None),
    ("lineage_hash", sa.String(128), None),
    ("snapshot_identity", sa.String(256), None),
    ("correction_sequence", sa.Integer(), "0"),
    ("supersedes_snapshot_id", postgresql.UUID(as_uuid=True), None),
    ("superseded_by_snapshot_id", postgresql.UUID(as_uuid=True), None),
    ("superseded_at", sa.DateTime(timezone=True), None),
    ("supersession_reason", sa.String(128), None),
)


def upgrade() -> None:
    op.alter_column(
        "topic_snapshots",
        "strong_stock_count",
        nullable=True,
        server_default=None,
        schema="topicpilot",
    )
    op.alter_column(
        "topic_snapshots",
        "weak_stock_count",
        nullable=True,
        server_default=None,
        schema="topicpilot",
    )
    for name, column_type, default in _ADDED_COLUMNS:
        op.add_column(
            "topic_snapshots",
            sa.Column(
                name,
                column_type,
                nullable=name
                not in {
                    "publication_mode",
                    "membership_mode",
                    "trading_day_state",
                    "generated_state",
                    "finality_state",
                    "publication_state",
                    "correction_sequence",
                },
                server_default=sa.text(default) if default is not None else None,
            ),
            schema="topicpilot",
        )

    op.execute(
        sa.text(
            "UPDATE topicpilot.topic_snapshots "
            "SET snapshot_identity = 'legacy:' || id::text "
            "WHERE snapshot_identity IS NULL"
        )
    )
    op.alter_column("topic_snapshots", "snapshot_identity", nullable=False, schema="topicpilot")
    op.drop_constraint(
        "uq_topic_snapshots_topic_date", "topic_snapshots", schema="topicpilot", type_="unique"
    )
    op.create_unique_constraint(
        "uq_topic_snapshots_identity", "topic_snapshots", ["snapshot_identity"], schema="topicpilot"
    )
    op.create_check_constraint(
        "ck_topic_snapshots_publication_mode",
        "topic_snapshots",
        "publication_mode IN ('FORMAL', 'RESEARCH_ONLY', 'SHADOW')",
        schema="topicpilot",
    )
    op.create_check_constraint(
        "ck_topic_snapshots_membership_mode",
        "topic_snapshots",
        "membership_mode IN ('PIT_FORMAL', 'CURRENT_MAPPING_RECONSTRUCTED_RESEARCH_ONLY', 'SHADOW')",
        schema="topicpilot",
    )
    op.create_check_constraint(
        "ck_topic_snapshots_publication_state",
        "topic_snapshots",
        "publication_state IN ('DRAFT', 'FINALIZED', 'PUBLISHED', 'UNPUBLISHED', 'SUPERSEDED', 'UNAVAILABLE')",
        schema="topicpilot",
    )
    op.create_check_constraint(
        "ck_topic_snapshots_formal_authority",
        "topic_snapshots",
        "publication_mode <> 'FORMAL' OR (membership_mode = 'PIT_FORMAL' AND mapping_effective_from >= DATE '2026-08-07' AND membership_snapshot_id IS NOT NULL AND membership_snapshot_hash IS NOT NULL AND relation_version IS NOT NULL AND snapshot_identity IS NOT NULL)",
        schema="topicpilot",
    )
    op.create_foreign_key(
        "fk_topic_snapshots_supersedes_snapshot_id",
        "topic_snapshots",
        "topic_snapshots",
        ["supersedes_snapshot_id"],
        ["id"],
        source_schema="topicpilot",
        referent_schema="topicpilot",
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_topic_snapshots_superseded_by_snapshot_id",
        "topic_snapshots",
        "topic_snapshots",
        ["superseded_by_snapshot_id"],
        ["id"],
        source_schema="topicpilot",
        referent_schema="topicpilot",
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_topic_snapshots_formal_publication",
        "topic_snapshots",
        [
            "publication_mode",
            "publication_state",
            "snapshot_date",
            "topic_id",
            "superseded_by_snapshot_id",
        ],
        schema="topicpilot",
    )

    op.create_table(
        "topic_snapshot_member_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("membership_order", sa.Integer(), nullable=False),
        sa.Column("fact_identity", sa.String(256), nullable=False),
        sa.Column("fact_hash", sa.String(128), nullable=False),
        sa.Column("fact_state", sa.String(32), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("price_observation_id", postgresql.UUID(as_uuid=True)),
        sa.Column("volume_observation_id", postgresql.UUID(as_uuid=True)),
        sa.Column("trading_status_observation_id", postgresql.UUID(as_uuid=True)),
        sa.Column("close", sa.Numeric(38, 18)),
        sa.Column("previous_close", sa.Numeric(38, 18)),
        sa.Column("change_pct", sa.Numeric(18, 8)),
        sa.Column("observed_classification", sa.String(16)),
        sa.Column("strength_classification", sa.String(32)),
        sa.Column("classifier_version", sa.String(96)),
        sa.Column("observed_at", sa.DateTime(timezone=True)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("raw_fact_payload", postgresql.JSONB(), nullable=False),
        sa.Column("source_artifact_id", sa.String(128)),
        sa.Column("source_artifact_hash", sa.String(128)),
        sa.ForeignKeyConstraint(
            ["snapshot_id"], ["topicpilot.topic_snapshots.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["topicpilot.instruments.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["price_observation_id"],
            ["topicpilot.canonical_observations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["volume_observation_id"],
            ["topicpilot.canonical_observations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["trading_status_observation_id"],
            ["topicpilot.canonical_observations.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("snapshot_id", "instrument_id", name="uq_topic_snapshot_member_fact"),
        sa.CheckConstraint(
            "fact_state IN ('OBSERVED', 'NO_TRADE', 'UNKNOWN')",
            name="ck_topic_snapshot_member_fact_state",
        ),
        schema="topicpilot",
    )
    op.create_index(
        "ix_topic_snapshot_member_facts_snapshot_order",
        "topic_snapshot_member_facts",
        ["snapshot_id", "membership_order"],
        schema="topicpilot",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_topic_snapshot_member_facts_snapshot_order",
        table_name="topic_snapshot_member_facts",
        schema="topicpilot",
    )
    op.drop_table("topic_snapshot_member_facts", schema="topicpilot")
    op.drop_index(
        "ix_topic_snapshots_formal_publication",
        table_name="topic_snapshots",
        schema="topicpilot",
    )
    op.drop_constraint(
        "fk_topic_snapshots_superseded_by_snapshot_id",
        "topic_snapshots",
        schema="topicpilot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_topic_snapshots_supersedes_snapshot_id",
        "topic_snapshots",
        schema="topicpilot",
        type_="foreignkey",
    )
    op.drop_constraint(
        "ck_topic_snapshots_formal_authority", "topic_snapshots", schema="topicpilot", type_="check"
    )
    op.drop_constraint(
        "ck_topic_snapshots_publication_state",
        "topic_snapshots",
        schema="topicpilot",
        type_="check",
    )
    op.drop_constraint(
        "ck_topic_snapshots_membership_mode", "topic_snapshots", schema="topicpilot", type_="check"
    )
    op.drop_constraint(
        "ck_topic_snapshots_publication_mode", "topic_snapshots", schema="topicpilot", type_="check"
    )
    op.drop_constraint(
        "uq_topic_snapshots_identity", "topic_snapshots", schema="topicpilot", type_="unique"
    )
    op.create_unique_constraint(
        "uq_topic_snapshots_topic_date",
        "topic_snapshots",
        ["topic_id", "snapshot_date"],
        schema="topicpilot",
    )
    for name, _, _ in reversed(_ADDED_COLUMNS):
        op.drop_column("topic_snapshots", name, schema="topicpilot")
    op.alter_column(
        "topic_snapshots",
        "strong_stock_count",
        nullable=False,
        server_default="0",
        schema="topicpilot",
    )
    op.alter_column(
        "topic_snapshots",
        "weak_stock_count",
        nullable=False,
        server_default="0",
        schema="topicpilot",
    )
