"""Create the enterprise read model and analytics views.

Revision ID: 0001
Revises:
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


JSONB_EMPTY = sa.text("'{}'::jsonb")


def upgrade() -> None:
    op.create_table(
        "stocks",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("market", sa.String(32), nullable=False),
        sa.Column("industry", sa.String(160)),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "topics",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("group_name", sa.String(160)),
        sa.Column("topic_type", sa.String(64), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("contract_version", sa.String(64), nullable=False),
        sa.Column("bundle_version", sa.String(160), nullable=False),
        sa.Column("data_date", sa.Date(), nullable=False),
        sa.Column("bundle_hash", sa.String(64), nullable=False),
        sa.Column("source_kind", sa.String(32), nullable=False),
        sa.Column("source_name", sa.String(160), nullable=False),
        sa.Column("classification", sa.String(64), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("row_counts", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bundle_version"),
    )
    op.create_table(
        "topic_hierarchy",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("parent_topic_id", sa.BigInteger(), nullable=False),
        sa.Column("child_topic_id", sa.BigInteger(), nullable=False),
        sa.Column("weight", sa.Numeric(10, 4)),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.CheckConstraint("parent_topic_id <> child_topic_id", name="ck_topic_hierarchy_not_self"),
        sa.ForeignKeyConstraint(["child_topic_id"], ["topics.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_topic_id"], ["topics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parent_topic_id", "child_topic_id", name="uq_topic_hierarchy_edge"),
    )
    op.create_table(
        "stock_topic_relations",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("stock_id", sa.BigInteger(), nullable=False),
        sa.Column("topic_id", sa.BigInteger(), nullable=False),
        sa.Column("relation_type", sa.String(32), nullable=False),
        sa.Column("weight", sa.Numeric(10, 4)),
        sa.Column("evidence_summary", sa.Text()),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stock_id", "topic_id", "relation_type", name="uq_stock_topic_role"),
    )
    op.create_table(
        "source_artifacts",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("ingestion_run_id", sa.BigInteger(), nullable=False),
        sa.Column("artifact_name", sa.String(80), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingestion_run_id", "artifact_name", name="uq_source_artifact_run_name"
        ),
    )
    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("ingestion_run_id", sa.BigInteger(), nullable=False),
        sa.Column("data_date", sa.Date(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("market", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("total_stocks", sa.Integer()),
        sa.Column("advance_count", sa.Integer()),
        sa.Column("decline_count", sa.Integer()),
        sa.Column("unchanged_count", sa.Integer()),
        sa.Column("unavailable_count", sa.Integer()),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.CheckConstraint(
            "total_stocks IS NULL OR total_stocks >= 0", name="ck_market_total_nonnegative"
        ),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingestion_run_id", "data_date", "market", name="uq_market_snapshot_run"
        ),
    )
    op.create_table(
        "stock_snapshots",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("ingestion_run_id", sa.BigInteger(), nullable=False),
        sa.Column("data_date", sa.Date(), nullable=False),
        sa.Column("stock_id", sa.BigInteger(), nullable=False),
        sa.Column("price", sa.Numeric(18, 4)),
        sa.Column("change_pct", sa.Numeric(12, 4)),
        sa.Column("volume", sa.BigInteger()),
        sa.Column("ma5", sa.Numeric(18, 4)),
        sa.Column("ma20", sa.Numeric(18, 4)),
        sa.Column("rs20", sa.Numeric(12, 4)),
        sa.Column("technical_state", sa.String(80)),
        sa.Column("chip_score", sa.Numeric(12, 4)),
        sa.Column("data_freshness", sa.String(32)),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingestion_run_id", "data_date", "stock_id", name="uq_stock_snapshot_run"
        ),
    )
    op.create_index("ix_stock_snapshots_stock_date", "stock_snapshots", ["stock_id", "data_date"])
    op.create_table(
        "topic_snapshots",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("ingestion_run_id", sa.BigInteger(), nullable=False),
        sa.Column("data_date", sa.Date(), nullable=False),
        sa.Column("topic_id", sa.BigInteger(), nullable=False),
        sa.Column("score", sa.Numeric(12, 4)),
        sa.Column("grade", sa.String(16)),
        sa.Column("strength_state", sa.String(48)),
        sa.Column("advance_count", sa.Integer()),
        sa.Column("decline_count", sa.Integer()),
        sa.Column("unchanged_count", sa.Integer()),
        sa.Column("unavailable_count", sa.Integer()),
        sa.Column("coverage_pct", sa.Numeric(8, 4)),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingestion_run_id", "data_date", "topic_id", name="uq_topic_snapshot_run"
        ),
    )
    op.create_index("ix_topic_snapshots_topic_date", "topic_snapshots", ["topic_id", "data_date"])
    op.create_table(
        "strategy_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("ingestion_run_id", sa.BigInteger(), nullable=False),
        sa.Column("strategy_key", sa.String(8), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("data_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("selected_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.CheckConstraint(
            "strategy_key IN ('MAS','MAV','TMC','BB','PB','KD')", name="ck_strategy_key"
        ),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingestion_run_id", "strategy_key", "data_date", "model_version", name="uq_strategy_run"
        ),
    )
    op.create_table(
        "strategy_candidates",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("strategy_run_id", sa.BigInteger(), nullable=False),
        sa.Column("stock_id", sa.BigInteger(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(12, 4)),
        sa.Column("reason", sa.Text()),
        sa.Column("price", sa.Numeric(18, 4)),
        sa.Column("selected", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("trigger_price", sa.Numeric(18, 4)),
        sa.Column("support_price", sa.Numeric(18, 4)),
        sa.Column("invalidation_price", sa.Numeric(18, 4)),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["strategy_run_id"], ["strategy_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_run_id", "rank", name="uq_strategy_candidate_rank"),
        sa.UniqueConstraint("strategy_run_id", "stock_id", name="uq_strategy_candidate_stock"),
    )
    op.create_table(
        "strategy_performance",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("strategy_run_id", sa.BigInteger(), nullable=False),
        sa.Column("horizon", sa.String(8), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("sample_count", sa.Integer()),
        sa.Column("win_rate_pct", sa.Numeric(8, 4)),
        sa.Column("average_return_pct", sa.Numeric(12, 4)),
        sa.Column("reason", sa.Text()),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.ForeignKeyConstraint(["strategy_run_id"], ["strategy_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_run_id", "horizon", name="uq_strategy_performance_horizon"),
    )
    op.create_table(
        "data_quality_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("ingestion_run_id", sa.BigInteger(), nullable=False),
        sa.Column("data_date", sa.Date(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("event_code", sa.String(80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.String(64)),
        sa.Column("entity_key", sa.String(160)),
        sa.Column("metadata_json", postgresql.JSONB(), server_default=JSONB_EMPTY, nullable=False),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_data_quality_events_date_severity",
        "data_quality_events",
        ["data_date", "severity"],
    )

    op.execute(
        """
        CREATE VIEW vw_latest_stock_snapshot AS
        SELECT DISTINCT ON (ss.stock_id)
            ss.stock_id,
            s.code,
            s.name,
            s.market,
            s.industry,
            ss.data_date,
            ss.price,
            ss.change_pct,
            ss.volume,
            ss.ma5,
            ss.ma20,
            ss.rs20,
            ss.technical_state,
            ss.chip_score,
            ss.data_freshness,
            ss.metadata_json,
            ir.bundle_version,
            ir.generated_at
        FROM stock_snapshots ss
        JOIN stocks s ON s.id = ss.stock_id
        JOIN ingestion_runs ir ON ir.id = ss.ingestion_run_id AND ir.status = 'COMPLETED'
        ORDER BY ss.stock_id, ss.data_date DESC, ir.completed_at DESC, ss.id DESC
        """
    )
    op.execute(
        """
        CREATE VIEW vw_topic_constituents AS
        SELECT
            t.id AS topic_id,
            t.slug AS topic_slug,
            t.name AS topic_name,
            t.group_name,
            s.id AS stock_id,
            s.code AS stock_code,
            s.name AS stock_name,
            r.relation_type,
            r.weight,
            r.evidence_summary
        FROM stock_topic_relations r
        JOIN topics t ON t.id = r.topic_id
        JOIN stocks s ON s.id = r.stock_id
        WHERE t.enabled = true AND s.active = true
        """
    )
    op.execute(
        """
        CREATE VIEW vw_topic_rotation_14d AS
        WITH ranked AS (
            SELECT
                ts.topic_id,
                t.slug AS topic_slug,
                t.name AS topic_name,
                t.group_name,
                ts.data_date,
                ts.score,
                ts.grade,
                ts.strength_state,
                ts.coverage_pct,
                row_number() OVER (
                    PARTITION BY ts.topic_id ORDER BY ts.data_date DESC, ir.completed_at DESC, ts.id DESC
                ) AS newest_rank
            FROM topic_snapshots ts
            JOIN topics t ON t.id = ts.topic_id
            JOIN ingestion_runs ir ON ir.id = ts.ingestion_run_id AND ir.status = 'COMPLETED'
        ),
        windowed AS (
            SELECT * FROM ranked WHERE newest_rank <= 14
        )
        SELECT
            topic_id,
            topic_slug,
            topic_name,
            group_name,
            max(data_date) AS latest_date,
            max(score) FILTER (WHERE newest_rank = 1) AS latest_score,
            max(grade) FILTER (WHERE newest_rank = 1) AS latest_grade,
            max(strength_state) FILTER (WHERE newest_rank = 1) AS latest_strength_state,
            max(coverage_pct) FILTER (WHERE newest_rank = 1) AS latest_coverage_pct,
            max(score) FILTER (WHERE newest_rank = 1)
                - max(score) FILTER (WHERE newest_rank = 14) AS change_14d,
            count(*) AS point_count
        FROM windowed
        GROUP BY topic_id, topic_slug, topic_name, group_name
        """
    )
    op.execute(
        """
        CREATE VIEW vw_strategy_performance AS
        SELECT
            sr.id AS strategy_run_id,
            sr.strategy_key,
            sr.name AS strategy_name,
            sr.model_version,
            sr.data_date,
            sr.status AS run_status,
            sr.candidate_count,
            sr.selected_count,
            sp.horizon,
            sp.status,
            sp.sample_count,
            sp.win_rate_pct,
            sp.average_return_pct,
            sp.reason,
            ir.bundle_version,
            ir.completed_at
        FROM strategy_runs sr
        JOIN ingestion_runs ir ON ir.id = sr.ingestion_run_id AND ir.status = 'COMPLETED'
        JOIN strategy_performance sp ON sp.strategy_run_id = sr.id
        """
    )
    op.execute(
        """
        CREATE VIEW vw_data_quality_daily AS
        WITH quality AS (
            SELECT
                ingestion_run_id,
                count(*) FILTER (WHERE severity = 'INFO') AS info_count,
                count(*) FILTER (WHERE severity = 'WARNING') AS warning_count,
                count(*) FILTER (WHERE severity = 'ERROR') AS error_count
            FROM data_quality_events
            GROUP BY ingestion_run_id
        ),
        artifacts AS (
            SELECT ingestion_run_id, count(*) AS artifact_count
            FROM source_artifacts
            GROUP BY ingestion_run_id
        )
        SELECT
            ir.id AS ingestion_run_id,
            ir.data_date,
            ir.bundle_version,
            ir.status,
            ir.bundle_hash,
            ir.generated_at,
            ir.completed_at,
            ir.row_counts,
            coalesce(q.info_count, 0) AS info_count,
            coalesce(q.warning_count, 0) AS warning_count,
            coalesce(q.error_count, 0) AS error_count,
            coalesce(a.artifact_count, 0) AS artifact_count
        FROM ingestion_runs ir
        LEFT JOIN quality q ON q.ingestion_run_id = ir.id
        LEFT JOIN artifacts a ON a.ingestion_run_id = ir.id
        """
    )


def downgrade() -> None:
    for view in (
        "vw_data_quality_daily",
        "vw_strategy_performance",
        "vw_topic_rotation_14d",
        "vw_topic_constituents",
        "vw_latest_stock_snapshot",
    ):
        op.execute(f"DROP VIEW IF EXISTS {view}")

    op.drop_index("ix_data_quality_events_date_severity", table_name="data_quality_events")
    op.drop_table("data_quality_events")
    op.drop_table("strategy_performance")
    op.drop_table("strategy_candidates")
    op.drop_table("strategy_runs")
    op.drop_index("ix_topic_snapshots_topic_date", table_name="topic_snapshots")
    op.drop_table("topic_snapshots")
    op.drop_index("ix_stock_snapshots_stock_date", table_name="stock_snapshots")
    op.drop_table("stock_snapshots")
    op.drop_table("market_snapshots")
    op.drop_table("source_artifacts")
    op.drop_table("stock_topic_relations")
    op.drop_table("topic_hierarchy")
    op.drop_table("ingestion_runs")
    op.drop_table("topics")
    op.drop_table("stocks")
