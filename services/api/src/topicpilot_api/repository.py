from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from topicpilot_api.historical_read_model import project_v1_history, read_historical_bars
from topicpilot_api.models import IngestionRun
from topicpilot_api.problems import NotFoundProblem

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
    return project_v1_history(
        read_historical_bars(
            session,
            code,
            from_date,
            to_date,
            market_code,
            limit,
        )
    )


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
