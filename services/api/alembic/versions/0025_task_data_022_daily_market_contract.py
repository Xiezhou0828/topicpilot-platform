"""TASK-DATA-022 canonical daily-market read contract.

Revision ID: 0025_task_data_022_daily_market_contract
Revises: 0024_task_be_007_topic_snapshots
"""

from alembic import op

revision = "0025_task_data_022_daily_market_contract"
down_revision = "0024_task_be_007_topic_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE VIEW topicpilot.vw_daily_market_observations AS
        WITH candidates AS (
            SELECT
                co.id AS canonical_observation_id,
                co.instrument_id,
                co.source_id,
                m.code AS market_code,
                i.instrument_code,
                (co.observed_at AT TIME ZONE m.timezone)::date AS trade_date,
                cp.open,
                cp.high,
                cp.low,
                cp.close,
                cv.volume_quantity AS volume,
                co.quality_state,
                co.observed_at,
                co.retrieved_at,
                mds.source_code,
                mds.adapter_version,
                row_number() OVER (
                    PARTITION BY co.instrument_id,
                        (co.observed_at AT TIME ZONE m.timezone)::date
                    ORDER BY mds.source_rank, co.retrieved_at DESC, co.id DESC
                ) AS source_choice
            FROM topicpilot.canonical_observations co
            JOIN topicpilot.canonical_price_observations cp
              ON cp.canonical_observation_id = co.id
            JOIN topicpilot.instruments i ON i.id = co.instrument_id
            JOIN topicpilot.markets m ON m.id = i.market_id
            JOIN topicpilot.market_data_sources mds ON mds.id = co.source_id
            LEFT JOIN LATERAL (
                SELECT volume_detail.volume_quantity
                FROM topicpilot.canonical_observations volume_observation
                JOIN topicpilot.canonical_volume_observations volume_detail
                  ON volume_detail.canonical_observation_id = volume_observation.id
                WHERE volume_observation.instrument_id = co.instrument_id
                  AND volume_observation.source_id = co.source_id
                  AND volume_observation.timeline_entry_id = co.timeline_entry_id
                  AND volume_observation.family_code = 'VOLUME'
                  AND volume_observation.quality_state IN ('ACCEPTED', 'INCOMPLETE')
                ORDER BY volume_observation.retrieved_at DESC, volume_observation.id DESC
                LIMIT 1
            ) cv ON true
            WHERE co.family_code = 'PRICE'
              AND co.quality_state = 'ACCEPTED'
              AND mds.observation_semantics = 'DAILY_BAR'
              AND NOT EXISTS (
                  SELECT 1 FROM topicpilot.canonical_observations successor
                  WHERE successor.supersedes_id = co.id
                    AND successor.family_code = 'PRICE'
                    AND successor.quality_state = 'ACCEPTED'
              )
        )
        SELECT
            market_code || ':' || instrument_code || ':' || trade_date::text AS stable_key,
            market_code,
            instrument_code,
            instrument_id,
            trade_date,
            open,
            high,
            low,
            close,
            volume,
            quality_state,
            source_code,
            adapter_version,
            canonical_observation_id,
            source_id,
            observed_at,
            retrieved_at
        FROM candidates
        WHERE source_choice = 1
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS topicpilot.vw_daily_market_observations")
