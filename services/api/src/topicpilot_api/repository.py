from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from topicpilot_api.models import IngestionRun
from topicpilot_api.problems import ApiProblem, NotFoundProblem

TPE = ZoneInfo("Asia/Taipei")


def latest_completed_run(session: Session) -> IngestionRun | None:
    return session.scalar(
        select(IngestionRun)
        .where(IngestionRun.status == "COMPLETED")
        .order_by(
            IngestionRun.data_date.desc(), IngestionRun.completed_at.desc(), IngestionRun.id.desc()
        )
        .limit(1)
    )


def data_status(
    run: IngestionRun, freshness_days: int, now: datetime | None = None
) -> dict[str, Any]:
    current_date = (now or datetime.now(TPE)).astimezone(TPE).date()
    age_days = max((current_date - run.data_date).days, 0)
    return {
        "contractVersion": run.contract_version,
        "bundleVersion": run.bundle_version,
        "bundleHash": run.bundle_hash,
        "dataDate": run.data_date,
        "generatedAt": run.generated_at,
        "completedAt": run.completed_at,
        "sourceKind": run.source_kind,
        "sourceName": run.source_name,
        "classification": run.classification,
        "freshness": "CURRENT" if age_days <= freshness_days else "STALE",
        "ageDays": age_days,
        "rowCounts": run.row_counts,
    }


def list_stocks(session: Session, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    total = session.scalar(select(func.count()).select_from(text("public.stocks"))) or 0
    rows = session.execute(
        text(
            """
            SELECT
                s.code, s.name, s.market, s.industry, s.active,
                latest.data_date, latest.price, latest.change_pct, latest.volume,
                latest.technical_state, latest.data_freshness
            FROM public.stocks s
            LEFT JOIN public.vw_latest_stock_snapshot latest ON latest.stock_id = s.id
            ORDER BY s.code
            LIMIT :limit OFFSET :offset
            """
        ),
        {"limit": limit, "offset": offset},
    ).mappings()
    return [dict(row) for row in rows], int(total)


def list_price_history(
    session: Session,
    code: str,
    from_date: date,
    to_date: date,
    market_code: str | None,
    limit: int,
) -> dict[str, Any]:
    """Read an explicit date-bound canonical PRICE history from PostgreSQL.

    This query is intentionally separate from the legacy ``stock_snapshots``
    read model. It never asks a provider for data, infers a latest row, or
    turns an empty result into a zero-valued observation.
    """

    identity_rows = list(
        session.execute(
            text(
                """
                SELECT i.id, i.instrument_code, m.code AS market_code
                FROM topicpilot.instruments i
                JOIN topicpilot.markets m ON m.id = i.market_id
                WHERE i.instrument_code = :code
                  AND i.is_active = true
                  AND m.is_active = true
                  AND (
                      CAST(:market_code AS varchar) IS NULL
                      OR m.code = CAST(:market_code AS varchar)
                  )
                ORDER BY m.code
                """
            ),
            {"code": code, "market_code": market_code},
        )
        .mappings()
        .all()
    )
    if not identity_rows:
        raise NotFoundProblem(f"Stock {code!r} was not found")
    if len(identity_rows) > 1:
        raise ApiProblem(
            409,
            "Ambiguous instrument",
            "The stock code exists in more than one market; specify market.",
            "https://topicpilot.example/problems/ambiguous-instrument",
        )

    identity = identity_rows[0]
    rows = list(
        session.execute(
            text(
                """
                SELECT
                    (co.observed_at AT TIME ZONE market.timezone)::date AS trading_date,
                    co.observed_at,
                    cp.open,
                    cp.high,
                    cp.low,
                    cp.close,
                    cv.volume_quantity AS volume,
                    mds.source_code,
                    co.quality_state
                FROM topicpilot.canonical_observations co
                JOIN topicpilot.canonical_price_observations cp
                  ON cp.canonical_observation_id = co.id
                JOIN topicpilot.instruments i
                  ON i.id = co.instrument_id
                JOIN topicpilot.markets market
                  ON market.id = i.market_id
                LEFT JOIN topicpilot.canonical_observations volume_observation
                  ON volume_observation.instrument_id = co.instrument_id
                 AND volume_observation.observed_at = co.observed_at
                 AND volume_observation.family_code = 'VOLUME'
                 AND volume_observation.quality_state = 'ACCEPTED'
                LEFT JOIN topicpilot.canonical_volume_observations cv
                  ON cv.canonical_observation_id = volume_observation.id
                JOIN topicpilot.market_data_sources mds ON mds.id = co.source_id
                WHERE co.instrument_id = :instrument_id
                  AND co.family_code = 'PRICE'
                  AND co.quality_state = 'ACCEPTED'
                  AND (co.observed_at AT TIME ZONE market.timezone)::date
                      >= CAST(:from_date AS date)
                  AND (co.observed_at AT TIME ZONE market.timezone)::date
                      <= CAST(:to_date AS date)
                  AND NOT EXISTS (
                      SELECT 1
                      FROM topicpilot.canonical_observations successor
                      WHERE successor.supersedes_id = co.id
                        AND successor.family_code = 'PRICE'
                        AND successor.quality_state = 'ACCEPTED'
                  )
                ORDER BY co.observed_at, co.ordering_key, co.id
                LIMIT :limit
                """
            ),
            {
                "instrument_id": identity["id"],
                "from_date": from_date,
                "to_date": to_date,
                "limit": limit,
            },
        )
        .mappings()
        .all()
    )
    return {
        "code": identity["instrument_code"],
        "market": identity["market_code"],
        "requested_from": from_date,
        "requested_to": to_date,
        "status": "AVAILABLE" if rows else "UNAVAILABLE",
        "availability_reason": None if rows else "NO_ACCEPTED_CANONICAL_PRICE_OBSERVATIONS",
        "point_count": len(rows),
        "items": [
            {
                "trading_date": row["trading_date"],
                "observed_at": row["observed_at"],
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
                "source_code": row["source_code"],
                "quality_state": row["quality_state"],
            }
            for row in rows
        ],
    }


def get_stock(session: Session, code: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
            SELECT
                s.id, s.code, s.name, s.market, s.industry, s.active,
                latest.data_date, latest.price, latest.change_pct, latest.volume,
                latest.ma5, latest.ma20, latest.rs20, latest.technical_state,
                latest.chip_score, latest.data_freshness
            FROM public.stocks s
            LEFT JOIN public.vw_latest_stock_snapshot latest ON latest.stock_id = s.id
            WHERE s.code = :code
            """
            ),
            {"code": code},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise NotFoundProblem(f"Stock {code!r} was not found")
    topics = session.execute(
        text(
            """
            SELECT topic_slug AS slug, topic_name AS name, relation_type, weight
            FROM public.vw_topic_constituents
            WHERE stock_id = :stock_id
            ORDER BY relation_type, topic_slug
            """
        ),
        {"stock_id": row["id"]},
    ).mappings()
    result = dict(row)
    result.pop("id")
    result["topics"] = [dict(item) for item in topics]
    return result


TOPIC_BASE_SQL = """
    SELECT
        t.id, t.slug, t.name, t.group_name, t.topic_type, t.enabled,
        latest.data_date, latest.score, latest.grade, latest.strength_state,
        latest.coverage_pct,
        (SELECT count(*)
         FROM public.stock_topic_relations r
         WHERE r.topic_id = t.id) AS constituent_count
    FROM public.topics t
    LEFT JOIN LATERAL (
        SELECT ts.data_date, ts.score, ts.grade, ts.strength_state, ts.coverage_pct
        FROM public.topic_snapshots ts
        JOIN public.ingestion_runs ir ON ir.id = ts.ingestion_run_id AND ir.status = 'COMPLETED'
        WHERE ts.topic_id = t.id
        ORDER BY ts.data_date DESC, ir.completed_at DESC, ts.id DESC
        LIMIT 1
    ) latest ON true
"""


def list_topics(session: Session, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    total = session.scalar(select(func.count()).select_from(text("public.topics"))) or 0
    rows = session.execute(
        text(f"{TOPIC_BASE_SQL} ORDER BY t.slug LIMIT :limit OFFSET :offset"),
        {"limit": limit, "offset": offset},
    ).mappings()
    return [dict(row) for row in rows], int(total)


def get_topic(session: Session, slug: str) -> dict[str, Any]:
    row = (
        session.execute(text(f"{TOPIC_BASE_SQL} WHERE t.slug = :slug"), {"slug": slug})
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise NotFoundProblem(f"Topic {slug!r} was not found")
    constituents = session.execute(
        text(
            """
            SELECT stock_code AS code, stock_name AS name, relation_type, weight
            FROM public.vw_topic_constituents
            WHERE topic_slug = :slug
            ORDER BY relation_type, stock_code
            """
        ),
        {"slug": slug},
    ).mappings()
    result = dict(row)
    result.pop("id")
    result["constituents"] = [dict(item) for item in constituents]
    return result


LATEST_STRATEGIES_SQL = """
    WITH latest AS (
        SELECT DISTINCT ON (sr.strategy_key)
            sr.id, sr.strategy_key, sr.name, sr.model_version, sr.data_date,
            sr.status, sr.candidate_count, sr.selected_count
        FROM public.strategy_runs sr
        JOIN public.ingestion_runs ir ON ir.id = sr.ingestion_run_id AND ir.status = 'COMPLETED'
        ORDER BY sr.strategy_key, sr.data_date DESC, ir.completed_at DESC, sr.id DESC
    )
"""


def list_strategies(session: Session, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    total = session.scalar(text(f"{LATEST_STRATEGIES_SQL} SELECT count(*) FROM latest")) or 0
    rows = session.execute(
        text(
            f"""
            {LATEST_STRATEGIES_SQL}
            SELECT strategy_key, name, model_version, data_date, status,
                   candidate_count, selected_count
            FROM latest
            ORDER BY strategy_key
            LIMIT :limit OFFSET :offset
            """
        ),
        {"limit": limit, "offset": offset},
    ).mappings()
    return [dict(row) for row in rows], int(total)


def list_candidates(
    session: Session,
    strategy_key: str,
    data_date: date | None,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], int]:
    run = (
        session.execute(
            text(
                """
            SELECT sr.id, sr.strategy_key, sr.model_version, sr.data_date
            FROM public.strategy_runs sr
            JOIN public.ingestion_runs ir ON ir.id = sr.ingestion_run_id AND ir.status = 'COMPLETED'
            WHERE sr.strategy_key = :strategy_key
              AND (CAST(:data_date AS date) IS NULL OR sr.data_date = CAST(:data_date AS date))
            ORDER BY sr.data_date DESC, ir.completed_at DESC, sr.id DESC
            LIMIT 1
            """
            ),
            {"strategy_key": strategy_key, "data_date": data_date},
        )
        .mappings()
        .one_or_none()
    )
    if run is None:
        suffix = f" on {data_date}" if data_date else ""
        raise NotFoundProblem(f"Strategy {strategy_key!r}{suffix} was not found")

    total = (
        session.scalar(
            text("SELECT count(*) FROM public.strategy_candidates WHERE strategy_run_id = :run_id"),
            {"run_id": run["id"]},
        )
        or 0
    )
    rows = session.execute(
        text(
            """
            SELECT
                :strategy_key AS strategy_key, :model_version AS model_version,
                CAST(:data_date AS date) AS data_date, sc.rank, s.code, s.name,
                sc.score, sc.reason, sc.price, sc.selected, sc.trigger_price,
                sc.support_price, sc.invalidation_price
            FROM public.strategy_candidates sc
            JOIN public.stocks s ON s.id = sc.stock_id
            WHERE sc.strategy_run_id = :run_id
            ORDER BY sc.rank, s.code
            LIMIT :limit OFFSET :offset
            """
        ),
        {
            "strategy_key": run["strategy_key"],
            "model_version": run["model_version"],
            "data_date": run["data_date"],
            "run_id": run["id"],
            "limit": limit,
            "offset": offset,
        },
    ).mappings()
    return [dict(row) for row in rows], int(total)


def topic_rotation(
    session: Session, days: int, limit: int, offset: int
) -> tuple[list[dict[str, Any]], int]:
    sql = """
        WITH deduplicated AS (
            SELECT DISTINCT ON (ts.topic_id, ts.data_date)
                ts.topic_id, ts.data_date, ts.score, ts.grade, ts.strength_state,
                ts.coverage_pct, ir.completed_at, ts.id
            FROM public.topic_snapshots ts
            JOIN public.ingestion_runs ir ON ir.id = ts.ingestion_run_id AND ir.status = 'COMPLETED'
            ORDER BY ts.topic_id, ts.data_date, ir.completed_at DESC, ts.id DESC
        ),
        ranked AS (
            SELECT *, row_number() OVER (PARTITION BY topic_id ORDER BY data_date DESC) AS row_num
            FROM deduplicated
        ),
        windowed AS (
            SELECT * FROM ranked WHERE row_num <= :days
        ),
        rotation AS (
            SELECT
                t.slug AS topic_slug,
                t.name AS topic_name,
                t.group_name,
                max(w.data_date) AS latest_date,
                (array_agg(w.score ORDER BY w.data_date DESC))[1] AS latest_score,
                (array_agg(w.grade ORDER BY w.data_date DESC))[1] AS latest_grade,
                (array_agg(w.strength_state ORDER BY w.data_date DESC))[1] AS latest_strength_state,
                (array_agg(w.coverage_pct ORDER BY w.data_date DESC))[1] AS latest_coverage_pct,
                (array_agg(w.score ORDER BY w.data_date DESC))[1]
                  - (array_agg(w.score ORDER BY w.data_date ASC))[1] AS change,
                count(*)::integer AS point_count,
                CAST(:days AS integer) AS days
            FROM windowed w
            JOIN public.topics t ON t.id = w.topic_id
            GROUP BY t.id, t.slug, t.name, t.group_name
        )
    """
    total = session.scalar(text(f"{sql} SELECT count(*) FROM rotation"), {"days": days}) or 0
    rows = session.execute(
        text(
            f"""
            {sql}
            SELECT * FROM rotation
            ORDER BY change DESC NULLS LAST, topic_slug
            LIMIT :limit OFFSET :offset
            """
        ),
        {"days": days, "limit": limit, "offset": offset},
    ).mappings()
    return [dict(row) for row in rows], int(total)


def strategy_performance(
    session: Session,
    strategy_key: str | None,
    horizon: str | None,
    data_date: date | None,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], int]:
    sql = """
        WITH chosen_runs AS (
            SELECT DISTINCT ON (sr.strategy_key)
                sr.id, sr.strategy_key, sr.name, sr.model_version, sr.data_date,
                sr.status AS run_status, sr.candidate_count, sr.selected_count
            FROM public.strategy_runs sr
            JOIN public.ingestion_runs ir ON ir.id = sr.ingestion_run_id AND ir.status = 'COMPLETED'
            WHERE (
                CAST(:strategy_key AS varchar) IS NULL
                OR sr.strategy_key = CAST(:strategy_key AS varchar)
            )
              AND (CAST(:data_date AS date) IS NULL OR sr.data_date = CAST(:data_date AS date))
            ORDER BY sr.strategy_key, sr.data_date DESC, ir.completed_at DESC, sr.id DESC
        ),
        performance AS (
            SELECT
                cr.strategy_key, cr.name AS strategy_name, cr.model_version, cr.data_date,
                cr.run_status, cr.candidate_count, cr.selected_count,
                sp.horizon, sp.status, sp.sample_count, sp.win_rate_pct,
                sp.average_return_pct, sp.reason
            FROM chosen_runs cr
            JOIN public.strategy_performance sp ON sp.strategy_run_id = cr.id
            WHERE (
                CAST(:horizon AS varchar) IS NULL
                OR sp.horizon = CAST(:horizon AS varchar)
            )
        )
    """
    params = {"strategy_key": strategy_key, "horizon": horizon, "data_date": data_date}
    total = session.scalar(text(f"{sql} SELECT count(*) FROM performance"), params) or 0
    rows = session.execute(
        text(
            f"""
            {sql}
            SELECT * FROM performance
            ORDER BY strategy_key, horizon
            LIMIT :limit OFFSET :offset
            """
        ),
        {**params, "limit": limit, "offset": offset},
    ).mappings()
    return [dict(row) for row in rows], int(total)
