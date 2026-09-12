"""Shared read-only historical daily-bar authority for V1 and V2 routes."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from topicpilot_api.problems import ApiProblem, NotFoundProblem

MAX_HISTORICAL_BAR_LIMIT = 200


def attach_bounded_continuity_evidence(result: dict[str, Any]) -> dict[str, Any]:
    """Attach the canonical lifecycle carrier without inferring empty coverage.

    ``reference_instrument_lifecycles`` is an existing bounded carrier for
    known lifecycle discontinuities only.  It cannot prove that other
    corporate-action families are empty, so the envelope remains partial and
    the existing evaluator can return FAIL for an intersecting known event or
    UNKNOWN everywhere else.
    """

    lifecycle = result.get("lifecycle")
    if not isinstance(lifecycle, dict):
        result["continuity_evidence"] = None
        return result

    identity = result.get("instrument_id") or f"{result['market']}:{result['code']}"
    effective_from = lifecycle.get("effective_from")
    evidence_id = lifecycle.get("evidence_id")
    result["continuity_evidence"] = {
        "default": {
            "evidence_id": f"V2-LIFECYCLE:{evidence_id or identity}",
            "method": "REFERENCE_INSTRUMENT_LIFECYCLE",
            "authority": "CANONICAL_REFERENCE_INSTRUMENT_LIFECYCLE",
            "canonical_identity": identity,
            "as_of_session": None,
            "coverage_start_session": result.get("requested_from"),
            "coverage_end_session": result.get("requested_to"),
            "coverage_state": "PARTIAL_UNKNOWN",
            "coverage_complete": False,
            "coverage_complete_for_exact_window": False,
            "known_events": [
                {
                    "event_identity": evidence_id,
                    "event_type": lifecycle.get("status_code"),
                    "effective_date": effective_from,
                    "event_effective_session": effective_from,
                    "event_status": lifecycle.get("status_code"),
                    "event_resolution": None,
                    "continuity_resolved": False,
                }
            ],
            "source_lineage": {
                "carrier": "topicpilot.reference_instrument_lifecycles",
                "evidence_id": evidence_id,
                "reference_data_version": "tw-reference-v1",
                "lineage_state": "VERSIONED",
            },
            "continuity_evaluation_state": "LIFECYCLE_FAMILY_ONLY",
            "reason": "OTHER_CORPORATE_ACTION_FAMILIES_NOT_COVERED",
        }
    }
    return result


def _normalize_market(market_code: str | None) -> str | None:
    normalized = market_code.strip().upper() if market_code else None
    return normalized or None


def _validate_window(from_date: date, to_date: date, limit: int) -> None:
    if to_date < from_date:
        raise ValueError("to must be on or after from")
    if limit < 1 or limit > MAX_HISTORICAL_BAR_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_HISTORICAL_BAR_LIMIT}")


def _source(row: Any) -> dict[str, Any]:
    return {
        "source_code": row["source_code"],
        "adapter_version": row["adapter_version"],
        "observation_semantics": row["observation_semantics"],
        "reference_data_version": row["reference_data_version"],
        "normalization_contract_version": row["normalization_contract_version"],
        "mapping_policy_version": row["mapping_policy_version"],
    }


def read_historical_bars(
    session: Session,
    code: str,
    from_date: date,
    to_date: date,
    market_code: str | None,
    limit: int,
) -> dict[str, Any]:
    """Read bounded accepted canonical DAILY_BAR rows.

    This is the single V1/V2 historical read authority. It never reads the
    retained HIST-002B legacy table, asks a provider for data, fills missing
    values, or derives technical/return semantics.
    """

    _validate_window(from_date, to_date, limit)
    normalized_market = _normalize_market(market_code)
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
            {"code": code, "market_code": normalized_market},
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
    lifecycle = session.execute(
        text(
            """
            SELECT status_code, effective_from, effective_to, evidence_id
            FROM topicpilot.reference_instrument_lifecycles
            WHERE instrument_id = :instrument_id
              AND status_code IN ('DELISTED', 'SUSPENDED', 'TERMINATED')
              AND effective_from <= CAST(:to_date AS date)
              AND (effective_to IS NULL OR effective_to >= CAST(:from_date AS date))
            ORDER BY effective_from DESC, id DESC
            LIMIT 1
            """
        ),
        {
            "instrument_id": identity["id"],
            "from_date": from_date,
            "to_date": to_date,
        },
    ).mappings().one_or_none()

    rows = list(
        session.execute(
            text(
                """
                SELECT
                    (co.observed_at AT TIME ZONE market.timezone)::date AS trading_date,
                    co.observed_at,
                    co.retrieved_at,
                    co.ordering_key,
                    co.id AS observation_id,
                    cp.open,
                    cp.high,
                    cp.low,
                    cp.close,
                    cp.adjustment_state,
                    cv.volume_quantity AS volume,
                    cv.volume_unit_code,
                    cv.volume_scale,
                    cv.aggregation_code AS volume_aggregation,
                    mds.source_code,
                    mds.adapter_version,
                    mds.observation_semantics,
                    co.reference_data_version,
                    co.normalization_contract_version,
                    co.mapping_policy_version,
                    co.quality_state
                FROM topicpilot.canonical_observations co
                JOIN topicpilot.canonical_price_observations cp
                  ON cp.canonical_observation_id = co.id
                JOIN topicpilot.instruments i
                  ON i.id = co.instrument_id
                JOIN topicpilot.markets market
                  ON market.id = i.market_id
                JOIN topicpilot.market_data_sources mds
                  ON mds.id = co.source_id
                LEFT JOIN LATERAL (
                    SELECT
                        volume_detail.volume_quantity,
                        volume_detail.volume_unit_code,
                        volume_detail.volume_scale,
                        volume_detail.aggregation_code
                    FROM topicpilot.canonical_observations volume_observation
                    JOIN topicpilot.canonical_volume_observations volume_detail
                      ON volume_detail.canonical_observation_id = volume_observation.id
                    WHERE volume_observation.instrument_id = co.instrument_id
                      AND volume_observation.source_id = co.source_id
                      AND volume_observation.timeline_entry_id = co.timeline_entry_id
                      AND volume_observation.family_code = 'VOLUME'
                      AND volume_observation.quality_state = 'ACCEPTED'
                      AND volume_detail.aggregation_code = 'DAILY_TOTAL'
                      AND NOT EXISTS (
                          SELECT 1
                          FROM topicpilot.canonical_observations volume_successor
                          WHERE volume_successor.supersedes_id = volume_observation.id
                            AND volume_successor.family_code = 'VOLUME'
                            AND volume_successor.quality_state = 'ACCEPTED'
                      )
                    ORDER BY volume_observation.retrieved_at DESC, volume_observation.id DESC
                    LIMIT 1
                ) cv ON true
                WHERE co.instrument_id = :instrument_id
                  AND co.family_code = 'PRICE'
                  AND co.quality_state = 'ACCEPTED'
                  AND mds.observation_semantics = 'DAILY_BAR'
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
                  AND NOT EXISTS (
                      SELECT 1
                      FROM topicpilot.reference_instrument_lifecycles lifecycle
                      WHERE lifecycle.instrument_id = co.instrument_id
                        AND lifecycle.status_code IN ('DELISTED', 'SUSPENDED', 'TERMINATED')
                        AND lifecycle.effective_from
                            <= (co.observed_at AT TIME ZONE market.timezone)::date
                        AND (
                            lifecycle.effective_to IS NULL
                            OR lifecycle.effective_to
                               >= (co.observed_at AT TIME ZONE market.timezone)::date
                        )
                  )
                ORDER BY
                    (co.observed_at AT TIME ZONE market.timezone)::date,
                    co.observed_at,
                    co.ordering_key,
                    co.id
                LIMIT :query_limit
                """
            ),
            {
                "instrument_id": identity["id"],
                "from_date": from_date,
                "to_date": to_date,
                "query_limit": limit + 1,
            },
        )
        .mappings()
        .all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = [
        {
                    "trading_date": row["trading_date"],
                    "observed_at": row["observed_at"],
                    "retrieved_at": row["retrieved_at"],
                    "ordering_key": row["ordering_key"],
                    "observation_id": row["observation_id"],
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
            "source_code": row["source_code"],
            "source": _source(row),
            "adapter_version": row["adapter_version"],
            "normalization_contract_version": row["normalization_contract_version"],
            "mapping_policy_version": row["mapping_policy_version"],
            "reference_data_version": row["reference_data_version"],
            "quality_state": row["quality_state"],
            # Corporate-action authority is not owned by this task. Keep the
            # bar explicitly raw and adjustment-unknown at this publication
            # boundary, even if a future source row carries a stronger label.
            "adjustment_state": "UNKNOWN",
            "volume_unit_code": row["volume_unit_code"],
            "volume_scale": row["volume_scale"],
            "volume_aggregation": row["volume_aggregation"],
        }
        for row in rows
    ]
    result = {
        "code": identity["instrument_code"],
        "market": identity["market_code"],
        "instrument_id": identity["id"],
        "as_of": items[-1]["retrieved_at"] if items else None,
        "requested_from": from_date,
        "requested_to": to_date,
        "returned_from": items[0]["trading_date"] if items else None,
        "returned_to": items[-1]["trading_date"] if items else None,
        "latest_trading_date": items[-1]["trading_date"] if items else None,
        "latest_observed_at": items[-1]["observed_at"] if items else None,
        "latest_retrieved_at": items[-1]["retrieved_at"] if items else None,
        "status": "AVAILABLE" if items else "UNAVAILABLE",
        "coverage_state": "AVAILABLE" if items else "EMPTY",
        "freshness_state": "AS_OF_LATEST_RETRIEVED" if items else "UNAVAILABLE",
        "availability_reason": None if items else "NO_ACCEPTED_CANONICAL_PRICE_OBSERVATIONS",
        "point_count": len(items),
        "has_more": has_more,
        "lifecycle": dict(lifecycle) if lifecycle is not None else None,
        "items": items,
    }
    return attach_bounded_continuity_evidence(result)


def project_v1_history(result: dict[str, Any]) -> dict[str, Any]:
    """Preserve the V1 projection while sharing the canonical read query."""

    return result


__all__ = [
    "MAX_HISTORICAL_BAR_LIMIT",
    "attach_bounded_continuity_evidence",
    "project_v1_history",
    "read_historical_bars",
]
