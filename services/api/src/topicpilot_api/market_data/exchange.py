"""Official TWSE/TPEx historical daily-bar providers.

The public exchange endpoints are used as an official daily-data supplement.
They are deliberately separate from the Taishin intraday provider: the
exchange sources can backfill daily OHLCV, but they are not treated as a
replacement for the licensed/private intraday runtime.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Final
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from .history import HistoricalBar, HistoricalFetchResult, HistoricalProviderError

TAIPEI: Final = ZoneInfo("Asia/Taipei")
TWSE_DAILY_SOURCE_CODE: Final = "TWSE_OFFICIAL_DAILY"
TWSE_DAILY_ADAPTER_VERSION: Final = "twse-official-daily.v1"
TPEX_DAILY_SOURCE_CODE: Final = "TPEX_OFFICIAL_DAILY"
TPEX_DAILY_ADAPTER_VERSION: Final = "tpex-official-daily.v1"
_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_MISSING_MARKERS: Final = {"", "-", "--", "X", "N/A", "null"}


Transport = Callable[[str, float], bytes]


def _validate_identifier(value: str, label: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise HistoricalProviderError("INVALID_IDENTITY", f"{label} is invalid")
    return value


def _decimal(value: object, label: str) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if text in _MISSING_MARKERS:
        return None
    try:
        result = Decimal(text.replace("+", "", 1))
    except (InvalidOperation, ValueError) as exc:
        raise HistoricalProviderError("INVALID_NUMBER", f"{label} is invalid") from exc
    if not result.is_finite() or (result < 0 and label != "change"):
        raise HistoricalProviderError("INVALID_NUMBER", f"{label} is invalid")
    return result


def _roc_date(value: object) -> date:
    text = str(value).strip().replace(".", "/").replace("-", "/")
    parts = text.split("/")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise HistoricalProviderError("INVALID_DATE", f"exchange date is invalid: {value}")
    year, month, day = (int(part) for part in parts)
    if year < 1000:
        year += 1911
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise HistoricalProviderError("INVALID_DATE", f"exchange date is invalid: {value}") from exc


def _month_starts(start: date, end: date) -> tuple[date, ...]:
    if end < start:
        raise HistoricalProviderError("INVALID_DATE_WINDOW", "end date precedes start date")
    cursor = date(start.year, start.month, 1)
    result: list[date] = []
    while cursor <= end:
        result.append(cursor)
        year = cursor.year + (cursor.month // 12)
        month = cursor.month % 12 + 1
        cursor = date(year, month, 1)
    return tuple(result)


def _read_url(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": "TopicPilot-V2/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _json(transport: Transport, url: str, timeout: float) -> Mapping[str, Any]:
    try:
        payload = json.loads(transport(url, timeout).decode("utf-8"))
    except Exception as exc:
        raise HistoricalProviderError("PROVIDER_REQUEST_FAILED", "exchange request failed") from exc
    if not isinstance(payload, Mapping):
        raise HistoricalProviderError("INVALID_PAYLOAD", "exchange response must be an object")
    return payload


def _validate_bar(bar: HistoricalBar) -> None:
    values = (bar.open, bar.high, bar.low, bar.close)
    if all(value is not None for value in values):
        assert all(value is not None for value in values)
        if bar.low > min(values) or bar.high < max(values) or bar.low < 0:
            raise HistoricalProviderError("INVALID_OHLC", bar.trading_date.isoformat())
    if bar.volume is not None and bar.volume < 0:
        raise HistoricalProviderError("INVALID_VOLUME", bar.trading_date.isoformat())


def _result(
    *,
    instrument_code: str,
    market_code: str,
    source_code: str,
    adapter_version: str,
    bars: list[HistoricalBar],
    retrieved_at: datetime,
    instrument_status: str | None = None,
    status_reason: str | None = None,
    status_explicit: bool = False,
) -> HistoricalFetchResult:
    by_date = {bar.trading_date: bar for bar in bars}
    ordered = tuple(by_date[day] for day in sorted(by_date))
    if instrument_status is None:
        instrument_status = (
            "AVAILABLE" if all(bar.close is not None for bar in ordered) else "UNKNOWN"
        )
    return HistoricalFetchResult(
        instrument_code=instrument_code,
        market_code=market_code,
        source_symbol=instrument_code,
        source_code=source_code,
        adapter_version=adapter_version,
        retrieved_at=retrieved_at,
        bars=ordered,
        raw_point_count=len(ordered),
        instrument_status=instrument_status,
        status_reason=status_reason,
        status_explicit=status_explicit,
    )


class TwseOfficialDailyProvider:
    """Fetch official TWSE daily OHLCV for a bounded date window."""

    source_code = TWSE_DAILY_SOURCE_CODE
    adapter_version = TWSE_DAILY_ADAPTER_VERSION

    def __init__(
        self,
        *,
        start_date: date,
        end_date: date,
        base_url: str = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY",
        timeout: float = 30.0,
        transport: Transport = _read_url,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.start_date = start_date
        self.end_date = end_date
        self.base_url = base_url
        self.timeout = timeout
        self.transport = transport
        self.clock = clock or (lambda: datetime.now(TAIPEI))

    def fetch_daily(self, instrument_code: str, market_code: str) -> HistoricalFetchResult:
        instrument_code = _validate_identifier(instrument_code, "instrument_code")
        market_code = _validate_identifier(market_code, "market_code")
        if market_code != "TPE":
            raise HistoricalProviderError("UNSUPPORTED_MARKET", market_code)
        bars: list[HistoricalBar] = []
        for month_start in _month_starts(self.start_date, self.end_date):
            query = urlencode(
                {
                    "date": month_start.strftime("%Y%m01"),
                    "stockNo": instrument_code,
                    "response": "json",
                }
            )
            payload = _json(self.transport, f"{self.base_url}?{query}", self.timeout)
            if str(payload.get("stat", "")).upper() != "OK":
                raise HistoricalProviderError(
                    "EXCHANGE_NO_DATA", str(payload.get("stat", "unknown"))
                )
            rows = payload.get("data", [])
            if not isinstance(rows, list):
                raise HistoricalProviderError("INVALID_PAYLOAD", "TWSE data must be an array")
            for row in rows:
                if not isinstance(row, list) or len(row) < 7:
                    raise HistoricalProviderError("INVALID_PAYLOAD", "TWSE daily row is incomplete")
                trading_date = _roc_date(row[0])
                if not self.start_date <= trading_date <= self.end_date:
                    continue
                bar = HistoricalBar(
                    trading_date=trading_date,
                    open=_decimal(row[3], "open"),
                    high=_decimal(row[4], "high"),
                    low=_decimal(row[5], "low"),
                    close=_decimal(row[6], "close"),
                    volume=_decimal(row[1], "volume"),
                )
                _validate_bar(bar)
                bars.append(bar)
        return _result(
            instrument_code=instrument_code,
            market_code=market_code,
            source_code=self.source_code,
            adapter_version=self.adapter_version,
            bars=bars,
            retrieved_at=self.clock(),
            instrument_status=("AVAILABLE" if bars else "EXCHANGE_CONFIRMED_NO_DATA"),
            status_reason=(
                None if bars else "official TWSE response contained no row for requested date"
            ),
            status_explicit=not bool(bars),
        )


class TpexOfficialDailyProvider:
    """Fetch official TPEx daily OHLCV for a bounded date window.

    TPEx reports volume in trading lots (張).  The provider converts it to
    shares before handing it to the provider-neutral V2 historical contract.
    """

    source_code = TPEX_DAILY_SOURCE_CODE
    adapter_version = TPEX_DAILY_ADAPTER_VERSION

    def __init__(
        self,
        *,
        start_date: date,
        end_date: date,
        base_url: str = "https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock",
        timeout: float = 30.0,
        transport: Transport = _read_url,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.start_date = start_date
        self.end_date = end_date
        self.base_url = base_url
        self.timeout = timeout
        self.transport = transport
        self.clock = clock or (lambda: datetime.now(TAIPEI))

    def fetch_daily(self, instrument_code: str, market_code: str) -> HistoricalFetchResult:
        instrument_code = _validate_identifier(instrument_code, "instrument_code")
        market_code = _validate_identifier(market_code, "market_code")
        if market_code != "TWO":
            raise HistoricalProviderError("UNSUPPORTED_MARKET", market_code)
        bars: list[HistoricalBar] = []
        for month_start in _month_starts(self.start_date, self.end_date):
            query = urlencode(
                {
                    "date": month_start.strftime("%Y/%m/%d"),
                    "code": instrument_code,
                    "response": "json",
                }
            )
            payload = _json(self.transport, f"{self.base_url}?{query}", self.timeout)
            if str(payload.get("stat", "")).lower() != "ok":
                raise HistoricalProviderError(
                    "EXCHANGE_NO_DATA", str(payload.get("stat", "unknown"))
                )
            tables = payload.get("tables")
            if not isinstance(tables, list) or not tables or not isinstance(tables[0], Mapping):
                raise HistoricalProviderError("INVALID_PAYLOAD", "TPEx tables are missing")
            rows = tables[0].get("data", [])
            if not isinstance(rows, list):
                raise HistoricalProviderError("INVALID_PAYLOAD", "TPEx data must be an array")
            for row in rows:
                if not isinstance(row, list) or len(row) < 7:
                    raise HistoricalProviderError("INVALID_PAYLOAD", "TPEx daily row is incomplete")
                trading_date = _roc_date(row[0])
                if not self.start_date <= trading_date <= self.end_date:
                    continue
                lots = _decimal(row[1], "volume_lots")
                bar = HistoricalBar(
                    trading_date=trading_date,
                    open=_decimal(row[3], "open"),
                    high=_decimal(row[4], "high"),
                    low=_decimal(row[5], "low"),
                    close=_decimal(row[6], "close"),
                    volume=lots * Decimal("1000") if lots is not None else None,
                )
                _validate_bar(bar)
                bars.append(bar)
        return _result(
            instrument_code=instrument_code,
            market_code=market_code,
            source_code=self.source_code,
            adapter_version=self.adapter_version,
            bars=bars,
            retrieved_at=self.clock(),
            instrument_status=("AVAILABLE" if bars else "EXCHANGE_CONFIRMED_NO_DATA"),
            status_reason=(
                None if bars else "official TPEx response contained no row for requested date"
            ),
            status_explicit=not bool(bars),
        )


__all__ = [
    "TPEX_DAILY_ADAPTER_VERSION",
    "TPEX_DAILY_SOURCE_CODE",
    "TWSE_DAILY_ADAPTER_VERSION",
    "TWSE_DAILY_SOURCE_CODE",
    "TpexOfficialDailyProvider",
    "TwseOfficialDailyProvider",
]
