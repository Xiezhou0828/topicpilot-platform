"""Formal daily-market reconciliation and Lifecycle handoff contract.

This module does not persist a second copy of market data.  It reads the
approved current DAILY_BAR projection from the canonical observation chain and
decides whether a trading date is safe for downstream consumers.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session


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

    @property
    def coverage_pct(self) -> float:
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
) -> DailyMarketReconciliation:
    """Apply the fail-closed production coverage policy.

    An observation with a null close is retained and counted as unavailable,
    never coerced to zero.  Approved ``SUSPENDED``, ``NO_TRADE``, and
    ``EXCHANGE_CONFIRMED_NO_DATA`` statuses count as covered but remain
    unpriced. Unknown/provider-missing instruments remain unexplained.
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
    reasons: list[str] = []
    if market_closed:
        reasons.append("MARKET_CLOSED")
    if expected == 0:
        reasons.append("EMPTY_FORMAL_UNIVERSE")
    if covered != expected:
        reasons.append("INCOMPLETE_COVERAGE")
    if priced != expected:
        reasons.append("UNAVAILABLE_DAILY_CLOSE")
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
            }
            for market in markets
        },
        status=status,
        downstream_ready=ready,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def reconcile_daily_market(
    session: Session,
    trade_date: date,
    *,
    market_closed: bool = False,
    expected_instrument_ids: Collection[Any] | None = None,
) -> DailyMarketReconciliation:
    """Reconcile the canonical daily projection against a date-effective universe."""

    expected_filter = ""
    duplicate_filter = ""
    params: dict[str, Any] = {"trade_date": trade_date}
    if expected_instrument_ids is not None:
        expected_filter = "\n              AND i.id IN :expected_instrument_ids"
        duplicate_filter = "\n                      AND instrument_id IN :expected_instrument_ids"
        params["expected_instrument_ids"] = tuple(expected_instrument_ids)

    rows_query = text(
        f"""
            SELECT
                m.code AS market_code,
                count(*) FILTER (WHERE i.is_active) AS expected_count,
                count(d.instrument_id) AS observed_count,
                count(d.instrument_id) FILTER (WHERE d.close IS NOT NULL) AS priced_count
                ,count(d.instrument_id) FILTER (
                    WHERE d.close IS NOT NULL
                       OR d.status_code IN (
                           'SUSPENDED', 'NO_TRADE', 'EXCHANGE_CONFIRMED_NO_DATA',
                           'DELISTED', 'TERMINATED'
                       )
                ) AS covered_count
            FROM topicpilot.markets m
            JOIN topicpilot.instruments i ON i.market_id = m.id
            LEFT JOIN topicpilot.vw_daily_market_observations d
              ON d.instrument_id = i.id AND d.trade_date = :trade_date
            WHERE m.is_active
              AND i.is_active
              AND i.instrument_type = 'EQUITY'
              AND m.code IN ('TPE', 'TWO')
              {expected_filter}
            GROUP BY m.code
            ORDER BY m.code
            """
    )
    if expected_instrument_ids is not None:
        rows_query = rows_query.bindparams(bindparam("expected_instrument_ids", expanding=True))
    rows = session.execute(rows_query, params).mappings()
    expected_by_market: dict[str, int] = {}
    observed_by_market: dict[str, int] = {}
    priced_by_market: dict[str, int] = {}
    covered_by_market: dict[str, int] = {}
    for row in rows:
        market = str(row["market_code"])
        expected_by_market[market] = int(row["expected_count"] or 0)
        observed_by_market[market] = int(row["observed_count"] or 0)
        priced_by_market[market] = int(row["priced_count"] or 0)
        covered_by_market[market] = int(row["covered_count"] or 0)
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
    )


__all__ = [
    "DailyMarketReconciliation",
    "assess_daily_coverage",
    "reconcile_daily_market",
]
