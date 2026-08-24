"""Official whole-market aggregate facts for Today/Home V2.

The existing index contract reads broad-market index values.  This module
normalizes the adjacent official daily aggregate reports that already power
the post-close exchange providers:

* TWSE ``afterTrading/MI_INDEX`` supplies equity turnover, breadth and
  limit-up/limit-down counts.
* TPEx ``afterTrading/dailyQuotes`` supplies the official whole-market stock
  table and its aggregate turnover.  Breadth is counted from that official
  table, never from TopicPilot's product universe.  TPEx does not publish a
  market limit-count field in this response, so those fields remain NULL.

No persistence or Home policy lives here.  Invalid or unavailable provider
responses become explicit typed unavailable results for the materializer.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Final

TWSE_DAILY_AGGREGATE_ENDPOINT: Final = (
    "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
)
TPEX_DAILY_AGGREGATE_ENDPOINT: Final = (
    "https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes"
)
TWSE_DAILY_AGGREGATE_SOURCE: Final = "TWSE_OFFICIAL_MI_INDEX_DAILY_AGGREGATE"
TPEX_DAILY_AGGREGATE_SOURCE: Final = "TPEX_OFFICIAL_DAILY_QUOTES_AGGREGATE"
TP_EX_STOCK_CODE_RE: Final = re.compile(r"^\d{4}$")
COUNT_RE: Final = re.compile(r"^\s*([\d,]+)(?:\s*\(([\d,]+)\))?\s*$")

Transport = Callable[[str, float], bytes]


class AggregateContractError(ValueError):
    """Machine-readable aggregate provider validation error."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class MarketAggregateResult:
    """One normalized market-level aggregate fact set."""

    market: str
    trading_date: date | None
    turnover: Decimal | None
    currency: str | None
    turnover_unit: str | None
    turnover_scale: int | None
    eligible: int | None
    observed: int | None
    advancers: int | None
    decliners: int | None
    unchanged: int | None
    unavailable: int | None
    limit_up_count: int | None
    limit_down_count: int | None
    source: str
    source_endpoint: str
    lineage: str
    retrieved_at: datetime
    as_of: datetime
    data_status: str
    status_reason: str | None
    response_content_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "market": self.market,
            "tradingDate": self.trading_date.isoformat() if self.trading_date else None,
            "turnover": str(self.turnover) if self.turnover is not None else None,
            "currency": self.currency,
            "turnoverUnit": self.turnover_unit,
            "turnoverScale": self.turnover_scale,
            "eligible": self.eligible,
            "observed": self.observed,
            "advancers": self.advancers,
            "decliners": self.decliners,
            "unchanged": self.unchanged,
            "unavailable": self.unavailable,
            "limitUpCount": self.limit_up_count,
            "limitDownCount": self.limit_down_count,
            "source": self.source,
            "sourceEndpoint": self.source_endpoint,
            "lineage": self.lineage,
            "retrievedAt": self.retrieved_at.isoformat(),
            "asOf": self.as_of.isoformat(),
            "dataStatus": self.data_status,
            "statusReason": self.status_reason,
            "responseContentHash": self.response_content_hash,
        }


def _content_hash(payload: object) -> str:
    try:
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        canonical = repr(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _decimal(value: object, field: str, *, non_negative: bool = False) -> Decimal:
    if value is None or isinstance(value, bool) or str(value).strip() == "":
        raise AggregateContractError(f"MISSING_{field.upper()}", f"{field} is required")
    try:
        result = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError) as exc:
        raise AggregateContractError("INVALID_NUMBER", f"{field} is not numeric") from exc
    if not result.is_finite() or (non_negative and result < 0):
        raise AggregateContractError("INVALID_NUMBER", f"{field} is invalid")
    return result


def _date(value: object, field: str) -> date:
    raw = str(value).strip()
    if len(raw) != 8 or not raw.isdigit():
        raise AggregateContractError("INVALID_DATE", f"{field} must be YYYYMMDD")
    try:
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:]))
    except ValueError as exc:
        raise AggregateContractError("INVALID_DATE", f"{field} is not valid") from exc


def _int(value: object, field: str) -> int:
    parsed = _decimal(value, field, non_negative=True)
    if parsed != parsed.to_integral_value():
        raise AggregateContractError("INVALID_COUNT", f"{field} must be an integer")
    return int(parsed)


def _rows(payload: object, *, wrapper: str | None = None) -> Sequence[Mapping[str, Any]]:
    candidate = payload
    if wrapper is not None:
        if not isinstance(payload, Mapping):
            raise AggregateContractError("INVALID_PAYLOAD", "provider payload must be an object")
        candidate = payload.get(wrapper)
    if not isinstance(candidate, Sequence) or isinstance(candidate, (str, bytes, bytearray)):
        raise AggregateContractError("INVALID_PAYLOAD", "provider rows must be an array")
    rows: list[Mapping[str, Any]] = []
    for row in candidate:
        if not isinstance(row, Mapping):
            raise AggregateContractError("INVALID_PAYLOAD", "provider rows must contain objects")
        rows.append(row)
    return rows


def _count(value: object, field: str) -> tuple[int, int | None]:
    match = COUNT_RE.match(str(value))
    if not match:
        raise AggregateContractError("INVALID_COUNT", f"{field} is not a count")
    return int(match.group(1).replace(",", "")), (
        int(match.group(2).replace(",", "")) if match.group(2) else None
    )


def _unavailable(
    market: str,
    *,
    retrieved_at: datetime,
    as_of: datetime,
    source: str,
    endpoint: str,
    reason: str,
    response_content_hash: str | None = None,
) -> MarketAggregateResult:
    return MarketAggregateResult(
        market=market,
        trading_date=None,
        turnover=None,
        currency="TWD",
        turnover_unit="TWD",
        turnover_scale=0,
        eligible=None,
        observed=None,
        advancers=None,
        decliners=None,
        unchanged=None,
        unavailable=None,
        limit_up_count=None,
        limit_down_count=None,
        source=source,
        source_endpoint=endpoint,
        lineage=f"{source} -> official daily aggregate -> unavailable({reason})",
        retrieved_at=retrieved_at,
        as_of=as_of,
        data_status="UNAVAILABLE",
        status_reason=reason,
        response_content_hash=response_content_hash,
    )


def parse_twse_market_aggregate(
    payload: object, *, retrieved_at: datetime, as_of: datetime
) -> MarketAggregateResult:
    """Parse TWSE MI_INDEX equity turnover, breadth and limit counts."""

    content_hash = _content_hash(payload)
    try:
        if not isinstance(payload, Mapping):
            raise AggregateContractError("INVALID_PAYLOAD", "TWSE payload must be an object")
        trading_date = _date(payload.get("date"), "date")
        tables = payload.get("tables")
        if not isinstance(tables, list):
            raise AggregateContractError("INVALID_PAYLOAD", "TWSE tables must be an array")
        stats = next(
            (
                table
                for table in tables
                if isinstance(table, Mapping)
                and "大盤統計資訊" in str(table.get("title", ""))
                and isinstance(table.get("data"), list)
            ),
            None,
        )
        breadth = next(
            (
                table
                for table in tables
                if isinstance(table, Mapping)
                and table.get("title") == "漲跌證券數合計"
                and isinstance(table.get("data"), list)
            ),
            None,
        )
        if stats is None or breadth is None:
            raise AggregateContractError(
                "AGGREGATE_TABLE_MISSING", "TWSE aggregate tables are missing"
            )
        turnover_row = next(
            (
                row
                for row in stats["data"]
                if isinstance(row, list)
                and row
                and row[0] == "證券合計(1+6+14+15)"
            ),
            None,
        )
        if not turnover_row or len(turnover_row) < 2:
            raise AggregateContractError(
                "TURNOVER_ROW_MISSING", "TWSE equity turnover row is missing"
            )
        turnover = _decimal(turnover_row[1], "turnover", non_negative=True)
        breadth_rows = {
            str(row[0]): row
            for row in breadth["data"]
            if isinstance(row, list) and row
        }
        up, limit_up = _count(breadth_rows["上漲(漲停)"][2], "advancers")
        down, limit_down = _count(breadth_rows["下跌(跌停)"][2], "decliners")
        unchanged = _count(breadth_rows["持平"][2], "unchanged")[0]
        no_trade = _count(breadth_rows["未成交"][2], "unavailable")[0]
        no_compare = _count(breadth_rows["無比價"][2], "unavailable")[0]
        unavailable = no_trade + no_compare
        observed = up + down + unchanged
        return MarketAggregateResult(
            market="TPE",
            trading_date=trading_date,
            turnover=turnover,
            currency="TWD",
            turnover_unit="TWD",
            turnover_scale=0,
            eligible=observed + unavailable,
            observed=observed,
            advancers=up,
            decliners=down,
            unchanged=unchanged,
            unavailable=unavailable,
            limit_up_count=limit_up,
            limit_down_count=limit_down,
            source=TWSE_DAILY_AGGREGATE_SOURCE,
            source_endpoint=TWSE_DAILY_AGGREGATE_ENDPOINT,
            lineage=(
                "TWSE -> afterTrading/MI_INDEX -> 大盤統計資訊 + "
                "漲跌證券數合計 -> formal market facts"
            ),
            retrieved_at=retrieved_at,
            as_of=as_of,
            data_status="AVAILABLE",
            status_reason=None,
            response_content_hash=content_hash,
        )
    except (AggregateContractError, KeyError, IndexError, TypeError) as exc:
        reason = exc.code if isinstance(exc, AggregateContractError) else "INVALID_PAYLOAD"
        return _unavailable(
            "TPE",
            retrieved_at=retrieved_at,
            as_of=as_of,
            source=TWSE_DAILY_AGGREGATE_SOURCE,
            endpoint=TWSE_DAILY_AGGREGATE_ENDPOINT,
            reason=reason,
            response_content_hash=content_hash,
        )


def parse_tpex_market_aggregate(
    payload: object, *, retrieved_at: datetime, as_of: datetime
) -> MarketAggregateResult:
    """Parse TPEx's official whole-market daily-quotes table."""

    content_hash = _content_hash(payload)
    try:
        if not isinstance(payload, Mapping):
            raise AggregateContractError("INVALID_PAYLOAD", "TPEx payload must be an object")
        trading_date = _date(payload.get("date"), "date")
        tables = payload.get("tables")
        if not isinstance(tables, list):
            raise AggregateContractError("INVALID_PAYLOAD", "TPEx tables must be an array")
        table = next(
            (
                item
                for item in tables
                if isinstance(item, Mapping)
                and item.get("title") == "上櫃股票行情"
                and isinstance(item.get("fields"), list)
                and isinstance(item.get("data"), list)
            ),
            None,
        )
        if table is None:
            raise AggregateContractError("AGGREGATE_TABLE_MISSING", "TPEx stock table is missing")
        fields = [str(field) for field in table["fields"]]
        positions = {field: index for index, field in enumerate(fields)}
        required = {"代號", "漲跌", "成交金額(元)"}
        if not required.issubset(positions):
            raise AggregateContractError("FIELD_MISSING", "TPEx stock table fields are incomplete")
        listed = _int(table.get("listedCompanies"), "listedCompanies")
        turnover = _decimal(table.get("totalTradingAmount"), "turnover", non_negative=True)
        stock_rows = [
            row
            for row in table["data"]
            if isinstance(row, list)
            and len(row) > max(positions.values())
            and TP_EX_STOCK_CODE_RE.fullmatch(str(row[positions["代號"]]).strip())
        ]
        advance = decline = unchanged = 0
        observed = 0
        for row in stock_rows:
            raw_change = str(row[positions["漲跌"]]).strip()
            try:
                change = Decimal(raw_change.replace(",", ""))
            except (InvalidOperation, ValueError):
                continue
            if not change.is_finite():
                continue
            observed += 1
            if change > 0:
                advance += 1
            elif change < 0:
                decline += 1
            else:
                unchanged += 1
        unavailable = max(listed - observed, 0)
        reason = "TPEX_LIMIT_COUNTS_NOT_PUBLISHED_BY_DAILY_QUOTES"
        return MarketAggregateResult(
            market="TWO",
            trading_date=trading_date,
            turnover=turnover,
            currency="TWD",
            turnover_unit="TWD",
            turnover_scale=0,
            eligible=listed,
            observed=observed,
            advancers=advance,
            decliners=decline,
            unchanged=unchanged,
            unavailable=unavailable,
            limit_up_count=None,
            limit_down_count=None,
            source=TPEX_DAILY_AGGREGATE_SOURCE,
            source_endpoint=TPEX_DAILY_AGGREGATE_ENDPOINT,
            lineage=(
                "TPEx -> afterTrading/dailyQuotes -> official 上櫃股票行情 rows "
                "-> formal market facts"
            ),
            retrieved_at=retrieved_at,
            as_of=as_of,
            data_status="AVAILABLE",
            status_reason=reason,
            response_content_hash=content_hash,
        )
    except (AggregateContractError, KeyError, IndexError, TypeError) as exc:
        reason = exc.code if isinstance(exc, AggregateContractError) else "INVALID_PAYLOAD"
        return _unavailable(
            "TWO",
            retrieved_at=retrieved_at,
            as_of=as_of,
            source=TPEX_DAILY_AGGREGATE_SOURCE,
            endpoint=TPEX_DAILY_AGGREGATE_ENDPOINT,
            reason=reason,
            response_content_hash=content_hash,
        )


def fetch_official_market_aggregates(
    *,
    target_date: date,
    retrieved_at: datetime,
    as_of: datetime,
    transport: Transport,
    timeout: float = 30.0,
) -> tuple[MarketAggregateResult, ...]:
    """Fetch both existing official daily aggregate reports."""

    requests = (
        (
            "TPE",
            f"{TWSE_DAILY_AGGREGATE_ENDPOINT}?date={target_date:%Y%m%d}&type=ALLBUT0999&response=json",
            parse_twse_market_aggregate,
        ),
        (
            "TWO",
            f"{TPEX_DAILY_AGGREGATE_ENDPOINT}?date={target_date:%Y/%m/%d}&response=json",
            parse_tpex_market_aggregate,
        ),
    )
    results: list[MarketAggregateResult] = []
    for market, endpoint, parser in requests:
        try:
            payload = json.loads(transport(endpoint, timeout).decode("utf-8"))
            result = parser(payload, retrieved_at=retrieved_at, as_of=as_of)
            if result.data_status == "AVAILABLE" and result.trading_date != target_date:
                result = _unavailable(
                    market,
                    retrieved_at=retrieved_at,
                    as_of=as_of,
                    source=result.source,
                    endpoint=result.source_endpoint,
                    reason="PROVIDER_DATE_MISMATCH",
                    response_content_hash=result.response_content_hash,
                )
        except Exception:
            source = TWSE_DAILY_AGGREGATE_SOURCE if market == "TPE" else TPEX_DAILY_AGGREGATE_SOURCE
            source_endpoint = (
                TWSE_DAILY_AGGREGATE_ENDPOINT
                if market == "TPE"
                else TPEX_DAILY_AGGREGATE_ENDPOINT
            )
            result = _unavailable(
                market,
                retrieved_at=retrieved_at,
                as_of=as_of,
                source=source,
                endpoint=source_endpoint,
                reason="PROVIDER_REQUEST_FAILED",
            )
        results.append(result)
    return tuple(results)


__all__ = [
    "TPEX_DAILY_AGGREGATE_ENDPOINT",
    "TPEX_DAILY_AGGREGATE_SOURCE",
    "TWSE_DAILY_AGGREGATE_ENDPOINT",
    "TWSE_DAILY_AGGREGATE_SOURCE",
    "AggregateContractError",
    "MarketAggregateResult",
    "fetch_official_market_aggregates",
    "parse_tpex_market_aggregate",
    "parse_twse_market_aggregate",
]
