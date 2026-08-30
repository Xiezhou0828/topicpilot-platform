"""Bind current daily-market projection to the active reference registry.

Reference-registry rollover is append-only: canonical observations retain the
reference version that was used to normalize them.  A current read projection
must therefore exclude observations bound to retired reference versions.  The
previous projection selected non-superseded rows without that binding, so a
rollover could expose both the retired and active canonical rows for one
instrument/date and report ``DUPLICATE_STABLE_KEY``.
"""

from alembic import op

revision = "0036_task_ws4_active_reference_daily_projection"
down_revision = "0035_task_ws1_today_home_v2_formal_publication"
branch_labels = None
depends_on = None


def _create_view() -> None:
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
                COALESCE(ts.status_code, 'UNKNOWN') AS status_code,
                ts.status_reason,
                ts.status_context,
                row_number() OVER (
                    PARTITION BY co.instrument_id,
                        (co.observed_at AT TIME ZONE m.timezone)::date
                    ORDER BY mds.source_rank, co.retrieved_at DESC, co.id DESC
                ) AS source_choice,
                count(*) OVER (
                    PARTITION BY co.instrument_id,
                        (co.observed_at AT TIME ZONE m.timezone)::date
                ) AS candidate_count
            FROM topicpilot.canonical_observations co
            JOIN topicpilot.reference_registry_sets active_reference
              ON active_reference.status = 'ACTIVE'
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
                  AND volume_observation.reference_data_version = co.reference_data_version
                  AND volume_observation.family_code = 'VOLUME'
                  AND volume_observation.quality_state IN ('ACCEPTED', 'INCOMPLETE')
                  AND NOT EXISTS (
                      SELECT 1
                      FROM topicpilot.canonical_observations volume_successor
                      WHERE volume_successor.supersedes_id = volume_observation.id
                        AND volume_successor.family_code = 'VOLUME'
                        AND volume_successor.quality_state IN ('ACCEPTED', 'INCOMPLETE')
                  )
                ORDER BY volume_observation.retrieved_at DESC, volume_observation.id DESC
                LIMIT 1
            ) cv ON true
            LEFT JOIN topicpilot.canonical_observations status_observation
              ON status_observation.timeline_entry_id = co.timeline_entry_id
             AND status_observation.source_id = co.source_id
             AND status_observation.reference_data_version = co.reference_data_version
             AND status_observation.family_code = 'TRADING_STATUS'
             AND status_observation.quality_state = 'ACCEPTED'
             AND NOT EXISTS (
                 SELECT 1
                 FROM topicpilot.canonical_observations status_successor
                 WHERE status_successor.supersedes_id = status_observation.id
                   AND status_successor.family_code = 'TRADING_STATUS'
                   AND status_successor.quality_state = 'ACCEPTED'
             )
            LEFT JOIN topicpilot.canonical_trading_status_observations ts
              ON ts.canonical_observation_id = status_observation.id
            WHERE co.family_code = 'PRICE'
              AND co.quality_state IN ('ACCEPTED', 'INCOMPLETE')
              AND mds.source_code IN ('TWSE_OFFICIAL_DAILY', 'TPEX_OFFICIAL_DAILY')
              AND (
                  co.reference_data_version = active_reference.reference_data_version
                  OR NOT EXISTS (
                      SELECT 1
                      FROM topicpilot.canonical_observations active_co
                      JOIN topicpilot.canonical_price_observations active_cp
                        ON active_cp.canonical_observation_id = active_co.id
                      JOIN topicpilot.market_data_sources active_mds
                        ON active_mds.id = active_co.source_id
                      WHERE active_co.reference_data_version
                                = active_reference.reference_data_version
                        AND active_co.instrument_id = co.instrument_id
                        AND active_co.family_code = 'PRICE'
                        AND active_co.quality_state IN ('ACCEPTED', 'INCOMPLETE')
                        AND active_mds.source_code IN (
                            'TWSE_OFFICIAL_DAILY', 'TPEX_OFFICIAL_DAILY'
                        )
                        AND (active_co.observed_at AT TIME ZONE m.timezone)::date
                                = (co.observed_at AT TIME ZONE m.timezone)::date
                        AND NOT EXISTS (
                            SELECT 1
                            FROM topicpilot.canonical_observations active_successor
                            WHERE active_successor.supersedes_id = active_co.id
                              AND active_successor.family_code = 'PRICE'
                              AND active_successor.quality_state IN ('ACCEPTED', 'INCOMPLETE')
                        )
                  )
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM topicpilot.canonical_observations successor
                  WHERE successor.supersedes_id = co.id
                    AND successor.family_code = 'PRICE'
                    AND successor.quality_state IN ('ACCEPTED', 'INCOMPLETE')
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
            status_code,
            status_reason,
            status_context,
            candidate_count,
            (close IS NOT NULL OR status_code IN (
                'SUSPENDED', 'NO_TRADE', 'EXCHANGE_CONFIRMED_NO_DATA'
            )) AS covered,
            canonical_observation_id,
            source_id,
            observed_at,
            retrieved_at
        FROM candidates
        WHERE source_choice = 1
        """
    )


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS topicpilot.vw_daily_market_observations")
    _create_view()


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS topicpilot.vw_daily_market_observations")
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
                COALESCE(ts.status_code, 'UNKNOWN') AS status_code,
                ts.status_reason,
                ts.status_context,
                row_number() OVER (
                    PARTITION BY co.instrument_id,
                        (co.observed_at AT TIME ZONE m.timezone)::date
                    ORDER BY mds.source_rank, co.retrieved_at DESC, co.id DESC
                ) AS source_choice,
                count(*) OVER (
                    PARTITION BY co.instrument_id,
                        (co.observed_at AT TIME ZONE m.timezone)::date
                ) AS candidate_count
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
                  AND NOT EXISTS (
                      SELECT 1
                      FROM topicpilot.canonical_observations volume_successor
                      WHERE volume_successor.supersedes_id = volume_observation.id
                        AND volume_successor.family_code = 'VOLUME'
                        AND volume_successor.quality_state IN ('ACCEPTED', 'INCOMPLETE')
                  )
                ORDER BY volume_observation.retrieved_at DESC, volume_observation.id DESC
                LIMIT 1
            ) cv ON true
            LEFT JOIN topicpilot.canonical_observations status_observation
              ON status_observation.timeline_entry_id = co.timeline_entry_id
             AND status_observation.source_id = co.source_id
             AND status_observation.family_code = 'TRADING_STATUS'
             AND status_observation.quality_state = 'ACCEPTED'
             AND NOT EXISTS (
                 SELECT 1
                 FROM topicpilot.canonical_observations status_successor
                 WHERE status_successor.supersedes_id = status_observation.id
                   AND status_successor.family_code = 'TRADING_STATUS'
                   AND status_successor.quality_state = 'ACCEPTED'
             )
            LEFT JOIN topicpilot.canonical_trading_status_observations ts
              ON ts.canonical_observation_id = status_observation.id
            WHERE co.family_code = 'PRICE'
              AND co.quality_state IN ('ACCEPTED', 'INCOMPLETE')
              AND mds.source_code IN ('TWSE_OFFICIAL_DAILY', 'TPEX_OFFICIAL_DAILY')
              AND NOT EXISTS (
                  SELECT 1
                  FROM topicpilot.canonical_observations successor
                  WHERE successor.supersedes_id = co.id
                    AND successor.family_code = 'PRICE'
                    AND successor.quality_state IN ('ACCEPTED', 'INCOMPLETE')
              )
        )
        SELECT
            market_code || ':' || instrument_code || ':' || trade_date::text AS stable_key,
            market_code,
            instrument_code,
            trade_date,
            instrument_id,
            open,
            high,
            low,
            close,
            volume,
            quality_state,
            source_code,
            adapter_version,
            status_code,
            status_reason,
            status_context,
            candidate_count,
            (close IS NOT NULL OR status_code IN (
                'SUSPENDED', 'NO_TRADE', 'EXCHANGE_CONFIRMED_NO_DATA'
            )) AS covered,
            canonical_observation_id,
            source_id,
            observed_at,
            retrieved_at
        FROM candidates
        WHERE source_choice = 1
        """
    )
