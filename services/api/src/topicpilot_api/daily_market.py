"""Formal daily-market reconciliation and Lifecycle handoff contract.

This module does not persist a second copy of market data.  It reads the
approved current DAILY_BAR projection from the canonical observation chain and
decides whether a trading date is safe for downstream consumers.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from topicpilot_api.market_data.availability import (
    LEGITIMATE_UNAVAILABLE_CODES,
    PIPELINE_FAILURE_CODES,
    classify_availability,
)
from topicpilot_api.trading_status_authority import (
    CANONICAL_STATUS_SOURCES,
    AuthorityClass,
    TradingStatusAuthorityRecord,
    resolve_effective_trading_status,
)


@dataclass(frozen=True)
class UnavailableInstrument:
    """Auditable read model for one instrument without a valid close."""

    trading_date: date
    symbol: str
    name: str | None
    market: str
    status: str
    reason_code: str
    source: str
    last_valid_price_date: date | None
    last_valid_close: Any | None
    formal_topic_membership_count: int
    affected_topic_slugs: tuple[str, ...]
    is_legitimate_unavailable: bool
    blocks_formal_publication: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "tradingDate": self.trading_date.isoformat(),
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market,
            "status": self.status,
            "reasonCode": self.reason_code,
            "source": self.source,
            "lastValidPriceDate": (
                self.last_valid_price_date.isoformat()
                if self.last_valid_price_date
                else None
            ),
            "lastValidClose": self.last_valid_close,
            "formalTopicMembershipCount": self.formal_topic_membership_count,
            "affectedTopicSlugs": list(self.affected_topic_slugs),
            "isLegitimateUnavailable": self.is_legitimate_unavailable,
            "blocksFormalPublication": self.blocks_formal_publication,
        }


@dataclass(frozen=True)
class DailyMarketReconciliation:
    trade_date: date
    expected_count: int
    observed_count: int
    priced_count: int
    covered_count: int
    unavailable_count: int
    unexplained_missing_count: int
    wrong_date_count: int
    duplicate_key_count: int
    market_counts: dict[str, dict[str, int]]
    status: str
    downstream_ready: bool
    reason_codes: tuple[str, ...]
    pipeline_failure_count: int = 0
    unknown_count: int = 0
    unavailable_instruments: tuple[UnavailableInstrument, ...] = ()

    @property
    def coverage_pct(self) -> float:
        if not self.expected_count:
            return 0.0
        return round(self.priced_count * 100 / self.expected_count, 4)

    @property
    def covered_coverage_pct(self) -> float:
        if not self.expected_count:
            return 0.0
        return round(self.covered_count * 100 / self.expected_count, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tradeDate": self.trade_date.isoformat(),
            "stableKey": "market_code:instrument_code:trade_date",
            "expectedCount": self.expected_count,
            "observedCount": self.observed_count,
            "pricedCount": self.priced_count,
            "coveredCount": self.covered_count,
            "unavailableCount": self.unavailable_count,
            "unexplainedMissingCount": self.unexplained_missing_count,
            "wrongDateCount": self.wrong_date_count,
            "duplicateKeyCount": self.duplicate_key_count,
            "coveragePct": self.coverage_pct,
            "coveredCoveragePct": self.covered_coverage_pct,
            "eligibleUniverse": self.expected_count,
            "pipelineFailureCount": self.pipeline_failure_count,
            "unknownCount": self.unknown_count,
            "unavailableInstruments": [
                item.to_dict() for item in self.unavailable_instruments
            ],
            "marketCounts": self.market_counts,
            "status": self.status,
            "downstreamReady": self.downstream_ready,
            "reasonCodes": list(self.reason_codes),
        }


def assess_daily_coverage(
    *,
    trade_date: date,
    expected_by_market: dict[str, int],
    observed_by_market: dict[str, int],
    priced_by_market: dict[str, int] | None = None,
    covered_by_market: dict[str, int] | None = None,
    wrong_date_count: int = 0,
    duplicate_key_count: int = 0,
    market_closed: bool = False,
    unavailable_instruments: Sequence[UnavailableInstrument] = (),
) -> DailyMarketReconciliation:
    """Apply the fail-closed production coverage policy.

    An observation with a null close is retained and counted as unavailable,
    never coerced to zero. Canonical exchange-confirmed unavailable statuses
    count as covered but remain unpriced. Unknown/provider-missing instruments
    remain unexplained and fail closed.
    """

    markets = sorted(set(expected_by_market) | set(observed_by_market))
    priced_by_market = observed_by_market if priced_by_market is None else priced_by_market
    covered_by_market = priced_by_market if covered_by_market is None else covered_by_market
    expected = sum(expected_by_market.get(item, 0) for item in markets)
    observed = sum(observed_by_market.get(item, 0) for item in markets)
    priced = sum(priced_by_market.get(item, 0) for item in markets)
    covered = sum(covered_by_market.get(item, 0) for item in markets)
    unavailable = max(0, expected - priced)
    unexplained = max(0, expected - covered)
    unavailable_instruments = tuple(unavailable_instruments)
    pipeline_failure_count = sum(
        item.blocks_formal_publication
        and not item.is_legitimate_unavailable
        and item.reason_code in PIPELINE_FAILURE_CODES
        for item in unavailable_instruments
    )
    unknown_count = sum(
        item.blocks_formal_publication
        and not item.is_legitimate_unavailable
        and item.status == "UNKNOWN"
        and item.reason_code not in PIPELINE_FAILURE_CODES
        for item in unavailable_instruments
    )
    reasons: list[str] = []
    if market_closed:
        reasons.append("MARKET_CLOSED")
    if expected == 0:
        reasons.append("EMPTY_FORMAL_UNIVERSE")
    if covered != expected:
        reasons.append("INCOMPLETE_COVERAGE")
    if priced != expected:
        reasons.append("UNAVAILABLE_DAILY_CLOSE")
    if any(item.is_legitimate_unavailable for item in unavailable_instruments):
        reasons.append("LEGITIMATE_UNAVAILABLE_INSTRUMENTS")
    if pipeline_failure_count:
        reasons.append("PIPELINE_FAILURE")
    if unknown_count:
        reasons.append("UNKNOWN_UNAVAILABLE_STATE")
    if covered > priced:
        reasons.append("APPROVED_NO_TRADE_COVERAGE")
    if unexplained:
        reasons.append("UNEXPLAINED_MISSING_DATA")
    if wrong_date_count:
        reasons.append("DATA_DATE_MISMATCH")
    if duplicate_key_count:
        reasons.append("DUPLICATE_STABLE_KEY")
    for market in markets:
        if covered_by_market.get(market, 0) != expected_by_market.get(market, 0):
            reasons.append(f"{market}_INCOMPLETE")

    blocking_reasons = {
        "MARKET_CLOSED",
        "EMPTY_FORMAL_UNIVERSE",
        "INCOMPLETE_COVERAGE",
        "DATA_DATE_MISMATCH",
        "DUPLICATE_STABLE_KEY",
        "UNEXPLAINED_MISSING_DATA",
        "PIPELINE_FAILURE",
        "UNKNOWN_UNAVAILABLE_STATE",
    }
    ready = not any(
        reason in blocking_reasons or reason.endswith("_INCOMPLETE") for reason in reasons
    )
    status = "MARKET_CLOSED" if market_closed else "READY" if ready else "PARTIAL"
    return DailyMarketReconciliation(
        trade_date=trade_date,
        expected_count=expected,
        observed_count=observed,
        priced_count=priced,
        covered_count=covered,
        unavailable_count=unavailable,
        unexplained_missing_count=unexplained,
        wrong_date_count=wrong_date_count,
        duplicate_key_count=duplicate_key_count,
        market_counts={
            market: {
                "expected": expected_by_market.get(market, 0),
                "observed": observed_by_market.get(market, 0),
                "priced": priced_by_market.get(market, 0),
                "covered": covered_by_market.get(market, 0),
                "unavailable": max(
                    0, expected_by_market.get(market, 0) - priced_by_market.get(market, 0)
                ),
                "unexplainedMissing": max(
                    0, expected_by_market.get(market, 0) - covered_by_market.get(market, 0)
                ),
                "pipelineFailure": sum(
                    item.market == market
                    and item.blocks_formal_publication
                    and item.reason_code
                    in PIPELINE_FAILURE_CODES
                    for item in unavailable_instruments
                ),
                "unknown": sum(
                    item.market == market
                    and item.blocks_formal_publication
                    and item.status == "UNKNOWN"
                    and item.reason_code
                    not in PIPELINE_FAILURE_CODES
                    for item in unavailable_instruments
                ),
            }
            for market in markets
        },
        status=status,
        downstream_ready=ready,
        reason_codes=tuple(dict.fromkeys(reasons)),
        pipeline_failure_count=pipeline_failure_count,
        unknown_count=unknown_count,
        unavailable_instruments=unavailable_instruments,
    )


def read_daily_market_rows(
    session: Session,
    trade_date: date,
    *,
    expected_instrument_ids: Collection[Any] | None = None,
) -> list[dict[str, Any]]:
    """Read one date-effective universe with price/status coverage evidence.

    The price view intentionally contains only price-family candidates.  The
    status CTE therefore reads the canonical trading-status family separately;
    this is what lets a confirmed no-trade instrument be represented without
    manufacturing a price row or a zero close.
    """

    expected_filter = ""
    params: dict[str, Any] = {"trade_date": trade_date}
    if expected_instrument_ids is not None:
        expected_filter = "\n              AND i.id IN :expected_instrument_ids"
        params["expected_instrument_ids"] = tuple(expected_instrument_ids)
    query = text(
        f"""
        WITH universe AS (
            SELECT i.id, i.instrument_code, i.name, m.code AS market
            FROM topicpilot.instruments i
            JOIN topicpilot.markets m ON m.id = i.market_id
            WHERE i.is_active AND m.is_active
              AND i.instrument_type = 'EQUITY'
              AND m.code IN ('TPE', 'TWO')
              AND (i.valid_from IS NULL OR i.valid_from <= :trade_date)
              AND (i.valid_to IS NULL OR i.valid_to >= :trade_date)
              AND (m.valid_from IS NULL OR m.valid_from <= :trade_date)
              AND (m.valid_to IS NULL OR m.valid_to >= :trade_date)
              {expected_filter}
        ), current_price AS (
            SELECT DISTINCT ON (d.instrument_id)
                d.instrument_id, d.close, d.observed_at, d.retrieved_at,
                d.source_code, d.status_code, d.status_reason,
                previous.close AS previous_close
            FROM topicpilot.vw_daily_market_observations d
            LEFT JOIN LATERAL (
                SELECT prior.close
                FROM topicpilot.vw_daily_market_observations prior
                WHERE prior.instrument_id = d.instrument_id
                  AND prior.trade_date < d.trade_date
                  AND prior.close IS NOT NULL
                ORDER BY prior.trade_date DESC, prior.observed_at DESC,
                         prior.canonical_observation_id DESC
                LIMIT 1
            ) previous ON TRUE
            WHERE d.trade_date = :trade_date
            ORDER BY d.instrument_id, d.observed_at DESC,
                     d.retrieved_at DESC, d.canonical_observation_id DESC
        ), current_status AS (
            SELECT DISTINCT ON (co.instrument_id)
                co.instrument_id, co.id AS status_observation_id,
                cts.status_code, cts.status_reason,
                co.observed_at AS status_observed_at,
                co.retrieved_at AS status_retrieved_at,
                source.source_code AS status_source
            FROM topicpilot.canonical_observations co
            JOIN topicpilot.canonical_trading_status_observations cts
              ON cts.canonical_observation_id = co.id
            JOIN topicpilot.instruments si ON si.id = co.instrument_id
            JOIN topicpilot.markets sm ON sm.id = si.market_id
            JOIN topicpilot.market_data_sources source ON source.id = co.source_id
            WHERE co.family_code = 'TRADING_STATUS'
              AND co.quality_state = 'ACCEPTED'
              AND source.observation_semantics = 'DAILY_BAR'
              AND (co.observed_at AT TIME ZONE sm.timezone)::date = :trade_date
              AND NOT EXISTS (
                  SELECT 1
                  FROM topicpilot.canonical_observations successor
                  WHERE successor.supersedes_id = co.id
                    AND successor.family_code = 'TRADING_STATUS'
                    AND successor.quality_state = 'ACCEPTED'
              )
            ORDER BY co.instrument_id, source.source_rank,
                     co.retrieved_at DESC, co.observed_at DESC, co.id DESC
        ), last_price AS (
            SELECT DISTINCT ON (d.instrument_id)
                d.instrument_id, d.trade_date AS last_valid_price_date,
                d.close AS last_valid_close
            FROM topicpilot.vw_daily_market_observations d
            WHERE d.trade_date < :trade_date AND d.close IS NOT NULL
            ORDER BY d.instrument_id, d.trade_date DESC, d.observed_at DESC,
                     d.canonical_observation_id DESC
        ), topic_memberships AS (
            SELECT r.instrument_id,
                   count(DISTINCT t.id)::integer AS formal_topic_membership_count,
                   array_agg(DISTINCT t.slug ORDER BY t.slug) AS affected_topic_slugs
            FROM topicpilot.instrument_topic_relations r
            JOIN topicpilot.topics t ON t.id = r.topic_id
            WHERE COALESCE(r.approval_state, 'APPROVED') = 'APPROVED'
              AND t.status NOT IN ('DISABLED', 'RETIRED')
              AND (r.valid_from IS NULL OR r.valid_from <= :trade_date)
              AND (r.valid_to IS NULL OR r.valid_to >= :trade_date)
              AND (t.valid_from IS NULL OR t.valid_from <= :trade_date)
              AND (t.valid_to IS NULL OR t.valid_to >= :trade_date)
            GROUP BY r.instrument_id
        )
        SELECT u.id AS instrument_id, u.instrument_code AS symbol, u.name,
               u.market, p.close, p.previous_close, p.observed_at,
               p.retrieved_at, p.source_code, p.status_code AS price_status_code,
               p.status_reason AS price_status_reason,
               s.status_observation_id, s.status_code, s.status_reason,
               s.status_observed_at, s.status_retrieved_at, s.status_source,
               l.last_valid_price_date, l.last_valid_close,
               COALESCE(tm.formal_topic_membership_count, 0)
                   AS formal_topic_membership_count,
               COALESCE(tm.affected_topic_slugs, ARRAY[]::text[])
                   AS affected_topic_slugs
        FROM universe u
        LEFT JOIN current_price p ON p.instrument_id = u.id
        LEFT JOIN current_status s ON s.instrument_id = u.id
        LEFT JOIN last_price l ON l.instrument_id = u.id
        LEFT JOIN topic_memberships tm ON tm.instrument_id = u.id
        ORDER BY u.market, u.instrument_code
        """
    )
    if expected_instrument_ids is not None:
        query = query.bindparams(bindparam("expected_instrument_ids", expanding=True))
    return [dict(row) for row in session.execute(query, params).mappings().all()]


def _availability_reason(row: Mapping[str, Any]) -> str:
    status = str(row.get("status_code") or "").upper()
    reason = str(row.get("status_reason") or row.get("price_status_reason") or "").upper()
    if status in LEGITIMATE_UNAVAILABLE_CODES:
        return status
    if reason in PIPELINE_FAILURE_CODES:
        return reason
    if status in PIPELINE_FAILURE_CODES:
        return status
    if row.get("status_observation_id") is None:
        return "MISSING_MARKET_DATA"
    return "UNKNOWN"


def build_unavailable_instruments(
    rows: Sequence[Mapping[str, Any]],
    *,
    trade_date: date,
    corporate_action_authority_by_identity: Mapping[
        tuple[str, str], Sequence[TradingStatusAuthorityRecord]
    ] | None = None,
) -> tuple[UnavailableInstrument, ...]:
    """Build the typed, disclosure-safe read model for unpriced rows."""

    result: list[UnavailableInstrument] = []
    for row in rows:
        if row.get("close") is not None:
            continue
        status_id = row.get("status_observation_id")
        source = str(row.get("status_source") or "")
        official = (
            (
                TradingStatusAuthorityRecord(
                    status_code=str(row.get("status_code") or "UNKNOWN"),
                    effective_from=trade_date,
                    effective_to=trade_date,
                    source=source,
                    source_reference=str(status_id),
                    reason_code=row.get("status_reason"),
                    observed_at=row.get("status_observed_at"),
                    authority_class=AuthorityClass.OFFICIAL_EXCHANGE.value,
                ),
            )
            if status_id is not None and source in CANONICAL_STATUS_SOURCES
            else ()
        )
        corporate_action_authority = ()
        if corporate_action_authority_by_identity:
            corporate_action_authority = corporate_action_authority_by_identity.get(
                (str(row.get("market") or "").upper(), str(row.get("symbol") or "")),
                (),
            )
        resolution = resolve_effective_trading_status(
            row.get("instrument_id"),
            trade_date,
            official_authority=official,
            corporate_action_authority=corporate_action_authority,
            price_source=str(row.get("source_code") or "CANONICAL_DAILY_PRICE"),
        )
        status_code = resolution.status
        reason_code = resolution.reason_code or _availability_reason(row)
        decision = classify_availability(
            status_code=status_code,
            reason_code=reason_code,
            has_canonical_status_evidence=resolution.authority_class
            in {
                AuthorityClass.OFFICIAL_EXCHANGE.value,
                AuthorityClass.OFFICIAL_CORPORATE_ACTION.value,
                AuthorityClass.REFERENCE_LIFECYCLE.value,
            },
        )
        resolved_source = (
            resolution.authority_source
            or row.get("status_source")
            or row.get("source_code")
            or "CANONICAL_DAILY_MARKET_READ_MODEL"
        )
        result.append(
            UnavailableInstrument(
                trading_date=trade_date,
                symbol=str(row.get("symbol") or ""),
                name=row.get("name"),
                market=str(row.get("market") or ""),
                status=decision.status,
                reason_code=decision.reason_code or "UNKNOWN",
                source=str(resolved_source),
                last_valid_price_date=row.get("last_valid_price_date"),
                last_valid_close=row.get("last_valid_close"),
                formal_topic_membership_count=int(
                    row.get("formal_topic_membership_count") or 0
                ),
                affected_topic_slugs=tuple(row.get("affected_topic_slugs") or ()),
                is_legitimate_unavailable=decision.is_legitimate_unavailable,
                blocks_formal_publication=decision.blocks_formal_publication,
            )
        )
    return tuple(result)


def reconcile_daily_market(
    session: Session,
    trade_date: date,
    *,
    market_closed: bool = False,
    expected_instrument_ids: Collection[Any] | None = None,
    corporate_action_authority_by_identity: Mapping[
        tuple[str, str], Sequence[TradingStatusAuthorityRecord]
    ] | None = None,
) -> DailyMarketReconciliation:
    """Reconcile the canonical daily projection against a date-effective universe."""

    duplicate_filter = ""
    params: dict[str, Any] = {"trade_date": trade_date}
    if expected_instrument_ids is not None:
        duplicate_filter = "\n                      AND instrument_id IN :expected_instrument_ids"
        params["expected_instrument_ids"] = tuple(expected_instrument_ids)
    rows = read_daily_market_rows(
        session, trade_date, expected_instrument_ids=expected_instrument_ids
    )
    expected_by_market: dict[str, int] = {}
    observed_by_market: dict[str, int] = {}
    priced_by_market: dict[str, int] = {}
    covered_by_market: dict[str, int] = {}
    for row in rows:
        market = str(row["market"])
        expected_by_market[market] = expected_by_market.get(market, 0) + 1
        has_price_evidence = row.get("observed_at") is not None
        has_status_evidence = row.get("status_observation_id") is not None
        observed_by_market[market] = observed_by_market.get(market, 0) + int(
            has_price_evidence or has_status_evidence
        )
        priced_by_market[market] = priced_by_market.get(market, 0) + int(
            row.get("close") is not None
        )
    unavailable_instruments = build_unavailable_instruments(
        rows,
        trade_date=trade_date,
        corporate_action_authority_by_identity=corporate_action_authority_by_identity,
    )
    for item in unavailable_instruments:
        if item.is_legitimate_unavailable:
            covered_by_market[item.market] = covered_by_market.get(item.market, 0) + 1
    for market in expected_by_market:
        covered_by_market[market] = covered_by_market.get(market, 0) + priced_by_market.get(
            market, 0
        )
    duplicate_query = text(
        f"""
                SELECT count(*) FROM (
                    SELECT stable_key
                    FROM topicpilot.vw_daily_market_observations
                    WHERE trade_date = :trade_date
                      {duplicate_filter}
                      AND candidate_count > 1
                    GROUP BY stable_key
                ) duplicates
                """
    )
    if expected_instrument_ids is not None:
        duplicate_query = duplicate_query.bindparams(
            bindparam("expected_instrument_ids", expanding=True)
        )
    duplicate_count = int(session.scalar(duplicate_query, params) or 0)
    return assess_daily_coverage(
        trade_date=trade_date,
        expected_by_market=expected_by_market,
        observed_by_market=observed_by_market,
        priced_by_market=priced_by_market,
        covered_by_market=covered_by_market,
        duplicate_key_count=duplicate_count,
        market_closed=market_closed,
        unavailable_instruments=unavailable_instruments,
    )


__all__ = [
    "DailyMarketReconciliation",
    "UnavailableInstrument",
    "assess_daily_coverage",
    "build_unavailable_instruments",
    "read_daily_market_rows",
    "reconcile_daily_market",
]
