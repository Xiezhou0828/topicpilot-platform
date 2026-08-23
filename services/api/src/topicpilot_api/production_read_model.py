"""Formal V2 Stock and Topic read models.

This module is deliberately read-only.  It composes the V2 identity, relation,
tracking, canonical observation, and topic snapshot tables without borrowing
the legacy public demo tables or inferring business semantics in the client.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from topicpilot_api.orm import TopicLifecycleResult
from topicpilot_api.problems import NotFoundProblem
from topicpilot_api.topic_lifecycle_engine import LIFECYCLE_POLICY_VERSION

TAIPEI = ZoneInfo("Asia/Taipei")
VALID_MARKETS = {"TPE", "TWO"}
VALID_UPDATE_MODES = {"INTRADAY", "POST_CLOSE", "UNKNOWN"}
VALID_SORTS = {"symbolAsc", "changePctDesc", "priceDesc", "volumeDesc"}
ROLE_VALUES = {
    "代表股",
    "核心股",
    "關聯股",
    "PRIMARY",
    "REPRESENTATIVE",
    "LEADER",
    "CORE",
    "SECONDARY",
    "RELATED",
}


STOCK_ROWS_SQL = text(
    """
    WITH universe AS (
        SELECT i.id AS instrument_id, i.instrument_code, i.name, i.is_active,
               m.code AS market_code, m.exchange_code, m.name AS market_name,
               ltu.update_mode, ltu.moving_average_state, ltu.latest_close AS tracking_close,
               ltu.moving_average, ltu.moving_average_period, ltu.observation_count,
               ltu.reference_observed_at, ltu.as_of_date, ltu.classification_reason
        FROM topicpilot.instruments i
        JOIN topicpilot.markets m ON m.id = i.market_id
        LEFT JOIN topicpilot.live_tracking_universe ltu ON ltu.instrument_id = i.id
        WHERE i.is_active = true
          AND i.instrument_type = 'EQUITY'
          AND m.is_active = true
          AND m.code IN ('TPE', 'TWO')
          AND (CAST(:market_code AS text) IS NULL OR m.code = CAST(:market_code AS text))
          AND (
              CAST(:update_mode AS text) IS NULL
              OR COALESCE(ltu.update_mode, 'UNKNOWN') = CAST(:update_mode AS text)
          )
          AND (
              CAST(:search AS text) IS NULL
              OR POSITION(LOWER(CAST(:search AS text)) IN LOWER(i.instrument_code)) > 0
              OR POSITION(LOWER(CAST(:search AS text)) IN LOWER(COALESCE(i.name, ''))) > 0
          )
    ),
    daily_price_by_day AS (
        SELECT co.id AS observation_id, co.instrument_id,
               (co.observed_at AT TIME ZONE m.timezone)::date AS trading_date,
               cp.open, cp.high, cp.low, cp.close,
               cp.price_currency_code, cp.price_scale, cp.adjustment_state,
               co.observed_at, co.retrieved_at, co.reference_data_version,
               co.normalization_contract_version, co.mapping_policy_version,
               co.quality_state, src.source_code, src.adapter_version,
               src.observation_semantics,
               ROW_NUMBER() OVER (
                   PARTITION BY co.instrument_id,
                                (co.observed_at AT TIME ZONE m.timezone)::date
                   ORDER BY co.observed_at DESC, co.retrieved_at DESC, co.id DESC
               ) AS same_day_rank
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_price_observations cp
          ON cp.canonical_observation_id = co.id
        JOIN topicpilot.instruments i ON i.id = co.instrument_id
        JOIN topicpilot.markets m ON m.id = i.market_id
        JOIN topicpilot.market_data_sources src ON src.id = co.source_id
        WHERE co.family_code = 'PRICE'
          AND co.quality_state = 'ACCEPTED'
          AND cp.close IS NOT NULL
          AND src.observation_semantics = 'DAILY_BAR'
          AND cp.price_context ->> 'source_semantics' = 'DAILY_BAR'
          AND NOT EXISTS (
              SELECT 1
              FROM topicpilot.canonical_observations successor
              WHERE successor.supersedes_id = co.id
                AND successor.family_code = 'PRICE'
                AND successor.quality_state = 'ACCEPTED'
          )
    ),
    daily_price_ranked AS (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY instrument_id
            ORDER BY trading_date DESC, observed_at DESC, retrieved_at DESC, observation_id DESC
        ) AS date_rank
        FROM daily_price_by_day
        WHERE same_day_rank = 1
    ),
    daily_price_conflicts_by_day AS (
        SELECT co.instrument_id,
               (co.observed_at AT TIME ZONE m.timezone)::date AS trading_date,
               BOOL_OR(co.quality_state IN ('AMBIGUOUS', 'CONFLICTING')) AS quality_conflict,
               COUNT(DISTINCT cp.close) FILTER (
                   WHERE co.quality_state = 'ACCEPTED' AND cp.close IS NOT NULL
               ) > 1 AS value_conflict
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_price_observations cp
          ON cp.canonical_observation_id = co.id
        JOIN topicpilot.instruments i ON i.id = co.instrument_id
        JOIN topicpilot.markets m ON m.id = i.market_id
        JOIN topicpilot.market_data_sources src ON src.id = co.source_id
        WHERE co.family_code = 'PRICE'
          AND co.quality_state IN ('ACCEPTED', 'AMBIGUOUS', 'CONFLICTING')
          AND src.observation_semantics = 'DAILY_BAR'
          AND NOT EXISTS (
              SELECT 1
              FROM topicpilot.canonical_observations successor
              WHERE successor.supersedes_id = co.id
                AND successor.family_code = 'PRICE'
                AND successor.quality_state = 'ACCEPTED'
          )
        GROUP BY co.instrument_id, (co.observed_at AT TIME ZONE m.timezone)::date
    ),
    daily_status_by_day AS (
        SELECT co.id AS observation_id, co.instrument_id,
               (co.observed_at AT TIME ZONE m.timezone)::date AS trading_date,
               cts.status_code, cts.status_reason,
               co.observed_at, co.retrieved_at, co.reference_data_version,
               co.normalization_contract_version, co.mapping_policy_version,
               co.quality_state, src.source_code, src.adapter_version,
               src.observation_semantics,
               ROW_NUMBER() OVER (
                   PARTITION BY co.instrument_id,
                                (co.observed_at AT TIME ZONE m.timezone)::date
                   ORDER BY co.observed_at DESC, co.retrieved_at DESC, co.id DESC
               ) AS same_day_rank
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_trading_status_observations cts
          ON cts.canonical_observation_id = co.id
        JOIN topicpilot.instruments i ON i.id = co.instrument_id
        JOIN topicpilot.markets m ON m.id = i.market_id
        JOIN topicpilot.market_data_sources src ON src.id = co.source_id
        WHERE co.family_code = 'TRADING_STATUS'
          AND co.quality_state = 'ACCEPTED'
          AND src.observation_semantics = 'DAILY_BAR'
          AND NOT EXISTS (
              SELECT 1
              FROM topicpilot.canonical_observations successor
              WHERE successor.supersedes_id = co.id
                AND successor.family_code = 'TRADING_STATUS'
                AND successor.quality_state = 'ACCEPTED'
          )
    ),
    daily_status_ranked AS (
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY instrument_id
            ORDER BY trading_date DESC, observed_at DESC, retrieved_at DESC, observation_id DESC
        ) AS date_rank
        FROM daily_status_by_day
        WHERE same_day_rank = 1
    ),
    eod_dates AS (
        SELECT instrument_id, MAX(trading_date) AS eod_date
        FROM (
            SELECT instrument_id, trading_date
            FROM daily_price_ranked
            WHERE date_rank = 1
            UNION ALL
            SELECT instrument_id, trading_date
            FROM daily_status_ranked
            WHERE date_rank = 1
            UNION ALL
            SELECT instrument_id, trading_date
            FROM daily_price_conflicts_by_day
            WHERE quality_conflict OR value_conflict
        ) candidates
        GROUP BY instrument_id
    ),
    eod_previous_price AS (
        SELECT e.instrument_id, p.close AS previous_daily_close,
               p.price_currency_code AS previous_price_currency_code,
               p.price_scale AS previous_price_scale,
               p.adjustment_state AS previous_adjustment_state,
               p.trading_date AS previous_trading_date,
               ROW_NUMBER() OVER (
                   PARTITION BY e.instrument_id
                   ORDER BY p.trading_date DESC, p.observed_at DESC,
                            p.retrieved_at DESC, p.observation_id DESC
               ) AS prior_rank
        FROM eod_dates e
        JOIN daily_price_by_day p
          ON p.instrument_id = e.instrument_id
         AND p.trading_date < e.eod_date
         AND p.same_day_rank = 1
    ),
    intraday AS (
        SELECT co.instrument_id, cp.close AS intraday_close, co.observed_at AS intraday_observed_at,
               co.retrieved_at AS intraday_retrieved_at,
               ROW_NUMBER() OVER (
                   PARTITION BY co.instrument_id
                   ORDER BY co.observed_at DESC, co.retrieved_at DESC, co.id DESC
               ) AS row_rank
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_price_observations cp
          ON cp.canonical_observation_id = co.id
        JOIN topicpilot.market_data_sources src ON src.id = co.source_id
        WHERE co.family_code = 'PRICE'
          AND co.quality_state = 'ACCEPTED'
          AND src.observation_semantics = 'INTRADAY_BAR'
    ),
    daily_volume_by_day AS (
        SELECT co.id AS observation_id, co.instrument_id,
               (co.observed_at AT TIME ZONE m.timezone)::date AS trading_date,
               cv.volume_quantity, cv.volume_unit_code, cv.volume_scale,
               cv.turnover_amount, cv.turnover_currency_code, cv.turnover_scale,
               cv.aggregation_code,
               co.observed_at, co.retrieved_at, co.reference_data_version,
               co.normalization_contract_version, co.mapping_policy_version,
               co.quality_state, src.source_code, src.adapter_version,
               src.observation_semantics,
               ROW_NUMBER() OVER (
                   PARTITION BY co.instrument_id, (co.observed_at AT TIME ZONE m.timezone)::date
                   ORDER BY co.observed_at DESC, co.retrieved_at DESC, co.id DESC
               ) AS same_day_rank
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_volume_observations cv
          ON cv.canonical_observation_id = co.id
        JOIN topicpilot.instruments i ON i.id = co.instrument_id
        JOIN topicpilot.markets m ON m.id = i.market_id
        JOIN topicpilot.market_data_sources src ON src.id = co.source_id
        WHERE co.family_code = 'VOLUME'
          AND co.quality_state = 'ACCEPTED'
          AND src.observation_semantics = 'DAILY_BAR'
          AND cv.aggregation_code = 'DAILY_TOTAL'
          AND NOT EXISTS (
              SELECT 1
              FROM topicpilot.canonical_observations successor
              WHERE successor.supersedes_id = co.id
                AND successor.family_code = 'VOLUME'
                AND successor.quality_state = 'ACCEPTED'
          )
    ),
    intraday_volume AS (
        SELECT co.instrument_id, cv.volume_quantity,
               ROW_NUMBER() OVER (
                   PARTITION BY co.instrument_id
                   ORDER BY co.observed_at DESC, co.retrieved_at DESC, co.id DESC
               ) AS row_rank
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_volume_observations cv
          ON cv.canonical_observation_id = co.id
        JOIN topicpilot.market_data_sources src ON src.id = co.source_id
        WHERE co.family_code = 'VOLUME'
          AND co.quality_state = 'ACCEPTED'
          AND src.observation_semantics = 'INTRADAY_BAR'
    ),
    historical_bounds AS (
        SELECT co.instrument_id,
               MIN((co.observed_at AT TIME ZONE m.timezone)::date) AS history_from,
               MAX((co.observed_at AT TIME ZONE m.timezone)::date) AS history_to,
               COUNT(*) AS history_rows
        FROM topicpilot.canonical_observations co
        JOIN topicpilot.canonical_price_observations cp
          ON cp.canonical_observation_id = co.id
        JOIN topicpilot.instruments i ON i.id = co.instrument_id
        JOIN topicpilot.markets m ON m.id = i.market_id
        JOIN topicpilot.market_data_sources src ON src.id = co.source_id
        WHERE co.family_code = 'PRICE'
          AND co.quality_state = 'ACCEPTED'
          AND src.observation_semantics = 'DAILY_BAR'
          AND NOT EXISTS (
              SELECT 1
              FROM topicpilot.canonical_observations successor
              WHERE successor.supersedes_id = co.id
                AND successor.family_code = 'PRICE'
                AND successor.quality_state = 'ACCEPTED'
          )
          AND NOT EXISTS (
              SELECT 1
              FROM topicpilot.reference_instrument_lifecycles lifecycle
              WHERE lifecycle.instrument_id = co.instrument_id
                AND lifecycle.status_code IN ('DELISTED', 'SUSPENDED', 'TERMINATED')
                AND lifecycle.effective_from
                    <= (co.observed_at AT TIME ZONE m.timezone)::date
                AND (
                    lifecycle.effective_to IS NULL
                    OR lifecycle.effective_to
                       >= (co.observed_at AT TIME ZONE m.timezone)::date
                )
          )
        GROUP BY co.instrument_id
    )
    SELECT u.*, e.eod_date,
           cp.open AS eod_open, cp.high AS eod_high, cp.low AS eod_low,
           cp.close AS daily_close, cp.price_currency_code AS eod_price_currency_code,
           cp.price_scale AS eod_price_scale, cp.adjustment_state AS eod_adjustment_state,
           cp.observed_at AS daily_observed_at, cp.retrieved_at AS daily_retrieved_at,
           cp.observed_at AS eod_price_observed_at, cp.retrieved_at AS eod_price_retrieved_at,
           cp.reference_data_version AS eod_price_reference_data_version,
           cp.normalization_contract_version AS eod_price_normalization_contract_version,
           cp.mapping_policy_version AS eod_price_mapping_policy_version,
           cp.quality_state AS eod_price_quality_state, cp.source_code AS eod_price_source_code,
           cp.adapter_version AS eod_price_adapter_version,
           cp.observation_semantics AS eod_price_observation_semantics,
           pp.previous_daily_close, pp.previous_price_currency_code,
           pp.previous_price_scale, pp.previous_adjustment_state,
           v.observation_id AS volume_observation_id, v.volume_quantity AS daily_volume,
           v.volume_unit_code, v.volume_scale,
           v.turnover_amount, v.turnover_currency_code, v.turnover_scale,
           v.aggregation_code AS volume_aggregation_code,
           v.observed_at AS volume_observed_at, v.retrieved_at AS volume_retrieved_at,
           v.reference_data_version AS volume_reference_data_version,
           v.normalization_contract_version AS volume_normalization_contract_version,
           v.mapping_policy_version AS volume_mapping_policy_version,
           v.quality_state AS volume_quality_state, v.source_code AS volume_source_code,
           v.adapter_version AS volume_adapter_version,
           v.observation_semantics AS volume_observation_semantics,
           s.status_code AS eod_status_code, s.status_reason AS eod_status_reason,
           s.observed_at AS status_observed_at, s.retrieved_at AS status_retrieved_at,
           h.history_from, h.history_to, h.history_rows,
           c.quality_conflict, c.value_conflict,
           intr.intraday_close, intr.intraday_observed_at,
           intr.intraday_retrieved_at, iv.volume_quantity AS intraday_volume
    FROM universe u
    LEFT JOIN eod_dates e ON e.instrument_id = u.instrument_id
    LEFT JOIN daily_price_by_day cp
      ON cp.instrument_id = u.instrument_id
     AND cp.trading_date = e.eod_date
     AND cp.same_day_rank = 1
    LEFT JOIN eod_previous_price pp
      ON pp.instrument_id = u.instrument_id AND pp.prior_rank = 1
    LEFT JOIN daily_volume_by_day v
      ON v.instrument_id = u.instrument_id
     AND v.trading_date = e.eod_date
     AND v.same_day_rank = 1
    LEFT JOIN daily_status_by_day s
      ON s.instrument_id = u.instrument_id
     AND s.trading_date = e.eod_date
     AND s.same_day_rank = 1
    LEFT JOIN historical_bounds h ON h.instrument_id = u.instrument_id
    LEFT JOIN daily_price_conflicts_by_day c
      ON c.instrument_id = u.instrument_id AND c.trading_date = e.eod_date
    LEFT JOIN intraday intr ON intr.instrument_id = u.instrument_id AND intr.row_rank = 1
    LEFT JOIN intraday_volume iv ON iv.instrument_id = u.instrument_id AND iv.row_rank = 1
    ORDER BY u.market_code, u.instrument_code
    """
)

TOPIC_RELATIONS_SQL = text(
    """
    SELECT r.instrument_id, t.id AS topic_id, t.slug AS topic_slug, t.name AS topic_name,
           r.relation_type, r.relationship_metadata,
           CASE
             WHEN COALESCE(
                      r.relationship_metadata ->> 'topicRole', r.relationship_metadata ->> 'role'
                  ) IN
                  ('代表股', 'PRIMARY', 'REPRESENTATIVE', 'LEADER') THEN '代表股'
             WHEN COALESCE(
                      r.relationship_metadata ->> 'topicRole', r.relationship_metadata ->> 'role'
                  ) IN
                  ('核心股', 'CORE', 'SECONDARY') THEN '核心股'
             WHEN COALESCE(
                      r.relationship_metadata ->> 'topicRole', r.relationship_metadata ->> 'role'
                  ) IN
                  ('關聯股', 'RELATED') THEN '關聯股'
             ELSE NULL
           END AS topic_role,
           CASE
             WHEN (r.relationship_metadata ->> 'relationWeight') ~ '^-?[0-9]+(\\.[0-9]+)?$'
               THEN (r.relationship_metadata ->> 'relationWeight')::numeric
             WHEN (r.relationship_metadata ->> 'weight') ~ '^-?[0-9]+(\\.[0-9]+)?$'
               THEN (r.relationship_metadata ->> 'weight')::numeric
             ELSE NULL
           END AS relation_weight
    FROM topicpilot.instrument_topic_relations r
    JOIN topicpilot.topics t ON t.id = r.topic_id
    WHERE r.valid_from <= :as_of_date
      AND (r.valid_to IS NULL OR r.valid_to >= :as_of_date)
      AND t.status NOT IN ('DISABLED', 'RETIRED')
    ORDER BY r.instrument_id, t.slug
    """
)

TOPIC_ROWS_SQL = text(
    """
    WITH latest AS (
        SELECT DISTINCT ON (topic_id) *
        FROM topicpilot.topic_snapshots
        WHERE publication_mode = 'FORMAL'
          AND publication_state = 'PUBLISHED'
          AND superseded_by_snapshot_id IS NULL
        ORDER BY topic_id, snapshot_date DESC, updated_at DESC
    )
    SELECT t.id AS topic_id, t.slug, t.name, t.description, t.status, t.display_metadata,
           parent.name AS parent_name, latest.snapshot_date, latest.market_grade,
           latest.topic_score, latest.topic_direction, latest.stock_count,
           latest.observed_stock_count, latest.coverage_pct, latest.data_status,
           latest.score_status, latest.publication_mode, latest.membership_mode,
           latest.publication_state, latest.trading_day_state, latest.freshness_state,
           latest.expected_count, latest.eligible_count, latest.no_trade_count,
           latest.unknown_count, latest.excluded_count, latest.quality_flags,
           latest.reference_registry_version, latest.mapping_policy_version,
           latest.source_run_id, latest.source_artifact_id, latest.source_artifact_hash,
           latest.lineage_hash, latest.membership_snapshot_id,
           latest.membership_snapshot_hash, latest.relation_version,
           latest.mapping_effective_from, latest.snapshot_identity,
           latest.correction_sequence
    FROM topicpilot.topics t
    LEFT JOIN LATERAL (
        SELECT p.name
        FROM topicpilot.topic_hierarchy h
        JOIN topicpilot.topics p ON p.id = h.parent_topic_id
        WHERE h.child_topic_id = t.id
          AND h.valid_from <= :as_of_date
          AND (h.valid_to IS NULL OR h.valid_to >= :as_of_date)
        ORDER BY h.display_order NULLS LAST, p.slug
        LIMIT 1
    ) parent ON true
    JOIN latest ON latest.topic_id = t.id
    WHERE t.status NOT IN ('DISABLED', 'RETIRED')
      AND (CAST(:slug AS text) IS NULL OR t.slug = CAST(:slug AS text))
    ORDER BY t.slug
    """
)


def _float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _derived_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def _source_lineage(row: Any, prefix: str, *, adjustment_state: str | None = None):
    source_code = row[f"{prefix}_source_code"]
    if source_code is None:
        return None
    return {
        "sourceCode": source_code,
        "adapterVersion": row[f"{prefix}_adapter_version"],
        "observationSemantics": row[f"{prefix}_observation_semantics"],
        "qualityState": row[f"{prefix}_quality_state"],
        "observedAt": row[f"{prefix}_observed_at"],
        "retrievedAt": row[f"{prefix}_retrieved_at"],
        "referenceDataVersion": row[f"{prefix}_reference_data_version"],
        "normalizationContractVersion": row[f"{prefix}_normalization_contract_version"],
        "mappingPolicyVersion": row[f"{prefix}_mapping_policy_version"],
        "adjustmentState": adjustment_state,
    }


def _date_now() -> date:
    return datetime.now(TAIPEI).date()


def normalize_stock_search(value: str | None) -> str | None:
    normalized = value.strip() if value else ""
    return normalized or None


def _freshness(update_mode: str, has_price: bool) -> str:
    if not has_price or update_mode == "UNKNOWN":
        return "資料待更新"
    return "盤中更新" if update_mode == "INTRADAY" else "盤後更新"


def _read_relations(session: Session, as_of_date: date) -> dict[str, list[dict[str, Any]]]:
    rows = session.execute(TOPIC_RELATIONS_SQL, {"as_of_date": as_of_date}).mappings()
    result: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        result.setdefault(str(row["instrument_id"]), []).append(
            {
                "topicId": str(row["topic_id"]),
                "topicSlug": row["topic_slug"],
                "topicName": row["topic_name"],
                "topicRole": row["topic_role"],
                "relationType": row["relation_type"],
                "relationWeight": _float(row["relation_weight"]),
            }
        )
    return result


def _stock_eod(row: Any) -> dict[str, Any] | None:
    trading_date = row["eod_date"]
    if trading_date is None:
        return None

    status_code = row["eod_status_code"]
    no_trade = status_code in {"NO_TRADE", "EXCHANGE_CONFIRMED_NO_DATA"}
    suspended = status_code == "SUSPENDED"
    source_conflict = bool(row["quality_conflict"] or row["value_conflict"])
    daily_close = row["daily_close"]
    previous_close = row["previous_daily_close"]
    current_adjustment = str(row["eod_adjustment_state"] or "UNKNOWN")
    previous_adjustment = str(row["previous_adjustment_state"] or "UNKNOWN")
    known_adjustments = {"ADJUSTED", "UNADJUSTED"}
    adjustment_comparable = (
        current_adjustment in known_adjustments
        and previous_adjustment in known_adjustments
        and current_adjustment == previous_adjustment
    )
    currency_comparable = (
        row["eod_price_currency_code"] is None
        or row["previous_price_currency_code"] is None
        or (
            row["eod_price_currency_code"] == row["previous_price_currency_code"]
            and row["eod_price_scale"] == row["previous_price_scale"]
        )
    )

    if source_conflict:
        data_status = "SOURCE_CONFLICT"
    elif suspended:
        data_status = "SUSPENDED"
    elif no_trade:
        data_status = "NO_TRADE"
    elif daily_close is None:
        data_status = "UNAVAILABLE"
    elif not currency_comparable:
        data_status = "SOURCE_CONFLICT"
    elif (
        previous_close is not None and not adjustment_comparable
    ) or current_adjustment == "UNKNOWN":
        data_status = "ADJUSTMENT_UNKNOWN"
    elif previous_close is None or row["daily_volume"] is None or row["turnover_amount"] is None:
        data_status = "PARTIAL"
    else:
        data_status = "AVAILABLE"

    suppress_current_facts = source_conflict or suspended or no_trade or daily_close is None
    change: Decimal | None = None
    change_pct: Decimal | None = None
    if (
        not suppress_current_facts
        and previous_close is not None
        and adjustment_comparable
        and currency_comparable
    ):
        change = Decimal(daily_close) - Decimal(previous_close)
        if Decimal(previous_close) > 0:
            change_pct = change / Decimal(previous_close) * 100

    price_source = None
    if not source_conflict and daily_close is not None:
        price_source = _source_lineage(
            row,
            "eod_price",
            adjustment_state=current_adjustment,
        )
    volume_source = None
    if not suppress_current_facts and row["volume_observation_id"] is not None:
        volume_source = _source_lineage(row, "volume")

    observed_at = row["daily_observed_at"] if daily_close is not None else row["status_observed_at"]
    retrieved_at = (
        row["daily_retrieved_at"] if daily_close is not None else row["status_retrieved_at"]
    )
    return {
        "tradingDate": trading_date,
        "open": _float(row["eod_open"]) if not suppress_current_facts else None,
        "high": _float(row["eod_high"]) if not suppress_current_facts else None,
        "low": _float(row["eod_low"]) if not suppress_current_facts else None,
        "close": _float(daily_close) if not suppress_current_facts else None,
        "previousClose": _float(previous_close),
        "change": _derived_float(change),
        "changePct": _derived_float(change_pct),
        "volume": _float(row["daily_volume"]) if not suppress_current_facts else None,
        "turnover": _float(row["turnover_amount"]) if not suppress_current_facts else None,
        "adjustmentState": current_adjustment,
        "priceSource": price_source,
        "volumeSource": volume_source,
        "observedAt": observed_at,
        "retrievedAt": retrieved_at,
        "dataStatus": data_status,
    }


def _stock_item(row: Any, relations: list[dict[str, Any]]) -> dict[str, Any]:
    update_mode = row["update_mode"] or "UNKNOWN"
    daily_close = row["daily_close"]
    intraday_close = row["intraday_close"]
    use_intraday = update_mode == "INTRADAY" and intraday_close is not None
    price_value = intraday_close if use_intraday else daily_close
    observed_at = row["intraday_observed_at"] if use_intraday else row["daily_observed_at"]
    retrieved_at = row["intraday_retrieved_at"] if use_intraday else row["daily_retrieved_at"]
    eod = _stock_eod(row)
    change_pct = None if use_intraday or eod is None else eod["changePct"]
    tracking_period = row["moving_average_period"]
    tracking_state = row["moving_average_state"] if row["moving_average"] is not None else None
    return {
        "instrumentId": str(row["instrument_id"]),
        "symbol": row["instrument_code"],
        "code": row["instrument_code"],
        "name": row["name"],
        "market": row["market_code"],
        "exchange": row["exchange_code"],
        "listing": row["market_name"],
        "active": bool(row["is_active"]),
        "enabled": bool(row["is_active"]),
        "price": _float(price_value),
        "changePct": _float(change_pct),
        "volume": _float(
            row["intraday_volume"]
            if use_intraday and row["intraday_volume"] is not None
            else row["daily_volume"]
        ),
        "eod": eod,
        "observedAt": observed_at,
        "retrievedAt": retrieved_at,
        "dataFreshness": _freshness(update_mode, price_value is not None),
        "updateMode": update_mode,
        "marketStatus": _freshness(update_mode, price_value is not None),
        "mainTopic": None,
        "topicRelations": relations,
        "trackingMode": update_mode,
        "trackingReason": row["classification_reason"],
        "ma20State": None,
        "ma60State": tracking_state if tracking_period == 60 else None,
        "historyCoverage": {
            "observedDays": int(row["observation_count"] or 0),
            "requiredDays": 60,
            "state": tracking_state or "UNKNOWN",
            "asOfDate": row["as_of_date"],
            "availableFrom": row.get("history_from"),
            "availableTo": row.get("history_to"),
            "rowCount": int(row.get("history_rows") or 0),
        },
        "favorite": None,
        "opportunity": None,
        "technicalEvidence": {
            "above20MA": None,
            "above60MA": tracking_state == "ABOVE" if tracking_period == 60 else None,
            "ma20": None,
            "ma60": _float(row["moving_average"]) if tracking_period == 60 else None,
            "breakoutState": None,
            "technicalState": None,
        },
        "institutionFlows": None,
        "summary": None,
    }


def read_stocks(
    session: Session,
    *,
    market: str | None = None,
    topic: str | None = None,
    update_mode: str | None = None,
    search: str | None = None,
    sort: str = "symbolAsc",
    limit: int = 1000,
    offset: int = 0,
) -> dict[str, Any]:
    normalized_market = market.upper() if market and market.upper() != "ALL" else None
    normalized_mode = update_mode.upper() if update_mode else None
    normalized_search = normalize_stock_search(search)
    if normalized_market and normalized_market not in VALID_MARKETS:
        raise ValueError("market must be ALL, TPE, or TWO")
    if normalized_mode and normalized_mode not in VALID_UPDATE_MODES:
        raise ValueError("updateMode must be INTRADAY, POST_CLOSE, or UNKNOWN")
    if sort not in VALID_SORTS:
        raise ValueError(f"sort must be one of {sorted(VALID_SORTS)}")
    as_of_date = _date_now()
    relation_map = _read_relations(session, as_of_date)
    rows = session.execute(
        STOCK_ROWS_SQL,
        {
            "market_code": normalized_market,
            "update_mode": normalized_mode,
            "search": normalized_search,
        },
    ).mappings()
    all_items = [_stock_item(row, relation_map.get(str(row["instrument_id"]), [])) for row in rows]
    items = all_items
    if topic:
        items = [
            item
            for item in items
            if any(rel["topicSlug"] == topic for rel in item["topicRelations"])
        ]
    if sort == "changePctDesc":
        items.sort(
            key=lambda item: (item["changePct"] is not None, item["changePct"] or -float("inf")),
            reverse=True,
        )
    elif sort == "priceDesc":
        items.sort(
            key=lambda item: (item["price"] is not None, item["price"] or -float("inf")),
            reverse=True,
        )
    elif sort == "volumeDesc":
        items.sort(
            key=lambda item: (item["volume"] is not None, item["volume"] or -float("inf")),
            reverse=True,
        )
    else:
        items.sort(key=lambda item: (item["market"], item["symbol"]))
    total = len(items)
    universe = {
        "total": len(all_items),
        "priced": sum(item["price"] is not None for item in all_items),
        "missingPrice": sum(item["price"] is None for item in all_items),
        "intraday": sum(item["updateMode"] == "INTRADAY" for item in all_items),
        "postClose": sum(item["updateMode"] == "POST_CLOSE" for item in all_items),
        "unknown": sum(item["updateMode"] == "UNKNOWN" for item in all_items),
        "tpe": sum(item["market"] == "TPE" for item in all_items),
        "two": sum(item["market"] == "TWO" for item in all_items),
    }
    return {
        "items": items[offset : offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "query": {
            "market": normalized_market or "ALL",
            "topic": topic,
            "updateMode": normalized_mode or "ALL",
            "search": normalized_search,
            "sort": sort,
        },
        "universe": universe,
    }


def read_stock(session: Session, symbol: str) -> dict[str, Any]:
    result = read_stocks(session, sort="symbolAsc", limit=1000)
    item = next((row for row in result["items"] if row["symbol"].upper() == symbol.upper()), None)
    if item is None:
        raise NotFoundProblem(f"Stock {symbol!r} was not found in the formal TPE/TWO universe")
    return item


def _topic_state_label(direction: str | None) -> str:
    return {
        "WARMING": "升溫",
        "COOLING": "降溫",
        "FLAT": "盤整",
    }.get(direction or "", "資料待更新")


def _status_items(topic_row: Any, constituents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if constituents:
        changes = [row["changePct"] for row in constituents if row["changePct"] is not None]
        rising: int | None = sum(value > 0 for value in changes)
        falling: int | None = sum(value < 0 for value in changes)
        flat: int | None = sum(value == 0 for value in changes)
        observed = sum(row["price"] is not None for row in constituents)
        total = len(constituents)
        participation = round(observed * 100 / total, 3) if total else None
    else:
        rising = falling = flat = None
        observed = topic_row["observed_stock_count"] or 0
        total = topic_row["stock_count"] or 0
        participation = _float(topic_row["coverage_pct"])
    direction = topic_row["topic_direction"]
    return [
        {
            "key": "族群表現",
            "state": _topic_state_label(direction),
            "evidence": {
                "observedStockCount": observed,
                "totalStockCount": total,
                "risingCount": rising,
                "fallingCount": falling,
                "flatCount": flat,
                "participationPct": participation,
                "semantic": (
                    "TopicSnapshot direction uses average accepted daily close-to-close change."
                ),
            },
        },
        {
            "key": "領漲核心",
            "state": None,
            "evidence": {"status": "NOT_AVAILABLE", "reason": "正式領漲核心判定規則尚未核准。"},
        },
        {
            "key": "動能擴散",
            "state": None,
            "evidence": {"status": "NOT_AVAILABLE", "reason": "正式動能擴散判定規則尚未核准。"},
        },
    ]


def _topic_read_item(
    topic_row: Any,
    constituents: list[dict[str, Any]],
    lifecycle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    direction = topic_row["topic_direction"]
    stock_count = topic_row["stock_count"]
    return {
        "topicId": str(topic_row["topic_id"]),
        "slug": topic_row["slug"],
        "name": topic_row["name"],
        "groupName": topic_row["parent_name"],
        "topicType": "TOPIC",
        "enabled": topic_row["status"] not in {"DISABLED", "RETIRED"},
        "dataDate": topic_row["snapshot_date"],
        "score": _float(topic_row["topic_score"]),
        "grade": topic_row["market_grade"],
        "direction": direction,
        "strengthState": direction,
        "readableState": _topic_state_label(direction),
        "coveragePct": _float(topic_row["coverage_pct"]),
        "constituentCount": int(stock_count if stock_count is not None else len(constituents)),
        "status": _status_items(topic_row, constituents),
        "lifecycle": lifecycle or _lifecycle_unavailable(),
        "constituents": constituents,
        "publication": {
            "mode": topic_row["publication_mode"],
            "membershipMode": topic_row["membership_mode"],
            "state": topic_row["publication_state"],
            "tradingDayState": topic_row["trading_day_state"],
            "freshnessState": topic_row["freshness_state"],
            "membershipSnapshotId": topic_row["membership_snapshot_id"],
            "membershipSnapshotHash": topic_row["membership_snapshot_hash"],
            "relationVersion": topic_row["relation_version"],
            "mappingEffectiveFrom": topic_row["mapping_effective_from"],
            "snapshotIdentity": topic_row["snapshot_identity"],
            "correctionSequence": topic_row["correction_sequence"],
        },
        "quality": {
            "expectedCount": topic_row["expected_count"],
            "eligibleCount": topic_row["eligible_count"],
            "observedCount": topic_row["observed_stock_count"],
            "noTradeCount": topic_row["no_trade_count"],
            "unknownCount": topic_row["unknown_count"],
            "excludedCount": topic_row["excluded_count"],
            "coveragePct": _float(topic_row["coverage_pct"]),
            "flags": topic_row["quality_flags"] or {},
        },
        "lineage": {
            "referenceRegistryVersion": topic_row["reference_registry_version"],
            "mappingPolicyVersion": topic_row["mapping_policy_version"],
            "sourceRunId": topic_row["source_run_id"],
            "sourceArtifactId": topic_row["source_artifact_id"],
            "sourceArtifactHash": topic_row["source_artifact_hash"],
            "lineageHash": topic_row["lineage_hash"],
        },
    }


def _lifecycle_unavailable() -> dict[str, Any]:
    return {
        "currentStage": None,
        "currentStageEnteredAt": None,
        "currentStageTradingDays": None,
        "history": [],
        "dataStatus": "NOT_AVAILABLE",
        "evaluationDate": None,
        "previousStage": None,
        "candidateStage": None,
        "transitionDecision": None,
        "transitionReason": None,
        "policyVersion": None,
        "evidence": {},
        "confidence": {},
        "lineage": {},
    }


def _read_lifecycle(session: Session, topic_id: Any) -> dict[str, Any]:
    try:
        rows = list(
            session.scalars(
                select(TopicLifecycleResult)
                .where(
                    TopicLifecycleResult.topic_id == topic_id,
                    TopicLifecycleResult.evaluation_mode == "SHADOW",
                    TopicLifecycleResult.policy_version == LIFECYCLE_POLICY_VERSION,
                )
                .order_by(TopicLifecycleResult.evaluation_date)
            )
        )
    except SQLAlchemyError:
        # During additive migration rollout, keep the formal catalog readable
        # while lifecycle remains explicitly unavailable.
        return _lifecycle_unavailable()
    if not rows:
        return _lifecycle_unavailable()
    current = rows[-1]
    segments: list[dict[str, Any]] = []
    for row in rows:
        if row.final_stage is None:
            continue
        if not segments or segments[-1]["stage"] != row.final_stage:
            if segments:
                segments[-1]["exitedAt"] = row.evaluation_date
                segments[-1]["current"] = False
            segments.append(
                {
                    "stage": row.final_stage,
                    "enteredAt": row.stage_entered_at,
                    "exitedAt": None,
                    "tradingDays": row.stage_trading_days,
                    "current": True,
                }
            )
        else:
            segments[-1]["tradingDays"] = row.stage_trading_days
    data_status = (
        "SHADOW_AVAILABLE"
        if current.final_stage is not None and current.data_status == "SHADOW"
        else current.data_status
    )
    latest_evidence = {
        "leadership": current.leadership_evidence or {},
        "diffusion": current.diffusion_evidence or {},
        "groupStrength": current.group_strength_evidence or {},
        "divergenceDecay": current.divergence_decay_evidence or {},
        "persistence": current.persistence_evidence or {},
    }
    return {
        "currentStage": current.final_stage,
        "currentStageEnteredAt": current.stage_entered_at,
        "currentStageTradingDays": current.stage_trading_days,
        "history": segments,
        "dataStatus": data_status,
        "evaluationDate": current.evaluation_date,
        "previousStage": current.previous_stage,
        "candidateStage": current.candidate_stage,
        "transitionDecision": current.transition_decision,
        "transitionReason": current.transition_reason,
        "policyVersion": current.policy_version,
        "evidence": latest_evidence,
        "confidence": current.sample_confidence or {},
        "lineage": {
            "snapshotId": str(current.snapshot_id) if current.snapshot_id else None,
            "snapshotIdentity": current.snapshot_identity,
            "membershipSnapshotId": current.membership_snapshot_id,
            "membershipSnapshotHash": current.membership_snapshot_hash,
            "relationVersion": current.relation_version,
            "sourceArtifactId": current.source_artifact_id,
            "sourceArtifactHash": current.source_artifact_hash,
            "lineageHash": current.lineage_hash,
            "memberFactHashes": current.member_fact_hashes or {},
            "correctionSequence": current.correction_sequence,
            "supersedesSnapshotId": (
                str(current.supersedes_snapshot_id)
                if current.supersedes_snapshot_id
                else None
            ),
            "supersededBySnapshotId": (
                str(current.superseded_by_snapshot_id)
                if current.superseded_by_snapshot_id
                else None
            ),
            "supersessionState": current.supersession_state,
        },
    }


def _topic_constituents(session: Session, slug: str, as_of_date: date) -> list[dict[str, Any]]:
    stocks = read_stocks(session, topic=slug, sort="symbolAsc", limit=1000)["items"]
    return [
        {
            "instrumentId": stock["instrumentId"],
            "symbol": stock["symbol"],
            "code": stock["code"],
            "name": stock["name"],
            "role": next(
                (rel["topicRole"] for rel in stock["topicRelations"] if rel["topicSlug"] == slug),
                None,
            ),
            "relationWeight": next(
                (
                    rel["relationWeight"]
                    for rel in stock["topicRelations"]
                    if rel["topicSlug"] == slug
                ),
                None,
            ),
            "price": stock["price"],
            "changePct": stock["changePct"],
            "observedAt": stock["observedAt"],
            "updateMode": stock["updateMode"],
            "freshness": stock["dataFreshness"],
            "technicalState": None,
            "relativeTopicState": None,
        }
        for stock in stocks
    ]


FORMAL_TOPIC_CONSTITUENTS_SQL = text(
    """
    WITH latest AS (
        SELECT DISTINCT ON (snapshot.topic_id) snapshot.id, snapshot.topic_id,
               snapshot.snapshot_date
        FROM topicpilot.topic_snapshots snapshot
        JOIN topicpilot.topics topic ON topic.id = snapshot.topic_id
        WHERE topic.slug = :slug
          AND snapshot.publication_mode = 'FORMAL'
          AND snapshot.publication_state = 'PUBLISHED'
          AND snapshot.superseded_by_snapshot_id IS NULL
        ORDER BY snapshot.topic_id, snapshot.snapshot_date DESC, snapshot.updated_at DESC
    )
    SELECT fact.instrument_id, instrument.instrument_code, instrument.name,
           market.code AS market_code, fact.close, fact.change_pct,
           fact.observed_at, fact.fact_state, fact.observation_date,
           fact.observed_classification, fact.fact_hash
    FROM latest
    JOIN topicpilot.topic_snapshot_member_facts fact ON fact.snapshot_id = latest.id
    JOIN topicpilot.instruments instrument ON instrument.id = fact.instrument_id
    JOIN topicpilot.markets market ON market.id = instrument.market_id
    ORDER BY market.code, instrument.instrument_code, fact.instrument_id
    """
)


def _formal_topic_constituents(session: Session, slug: str) -> list[dict[str, Any]]:
    rows = session.execute(FORMAL_TOPIC_CONSTITUENTS_SQL, {"slug": slug}).mappings()
    return [
        {
            "instrumentId": str(row["instrument_id"]),
            "symbol": row["instrument_code"],
            "code": row["instrument_code"],
            "name": row["name"],
            "role": None,
            "relationWeight": None,
            "price": _float(row["close"]),
            "changePct": _float(row["change_pct"]),
            "observedAt": row["observed_at"],
            "updateMode": "POST_CLOSE",
            "freshness": "AS_OF_TRADING_DATE",
            "technicalState": None,
            "relativeTopicState": None,
            "factState": row["fact_state"],
            "observationDate": row["observation_date"],
            "observedClassification": row["observed_classification"],
            "factHash": row["fact_hash"],
        }
        for row in rows
    ]


def read_topics(
    session: Session, *, slug: str | None = None, limit: int = 200, offset: int = 0
) -> dict[str, Any]:
    as_of_date = _date_now()
    rows = session.execute(TOPIC_ROWS_SQL, {"as_of_date": as_of_date, "slug": slug}).mappings()
    items = [_topic_read_item(row, [], _read_lifecycle(session, row["topic_id"])) for row in rows]
    total = len(items)
    return {
        "items": items[offset : offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "query": {"slug": slug},
    }


def read_topic(session: Session, slug: str) -> dict[str, Any]:
    as_of_date = _date_now()
    row = (
        session.execute(TOPIC_ROWS_SQL, {"as_of_date": as_of_date, "slug": slug}).mappings().first()
    )
    if row is None:
        raise NotFoundProblem(f"Topic {slug!r} was not found in the formal topic read model")
    constituents = _formal_topic_constituents(session, slug)
    return _topic_read_item(row, constituents, _read_lifecycle(session, row["topic_id"]))


__all__ = ["read_stock", "read_stocks", "read_topic", "read_topics"]
