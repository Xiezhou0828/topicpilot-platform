"""Official TWSE/TPEx historical daily-bar providers.

The public exchange endpoints are used as an official daily-data supplement.
They are deliberately separate from the Taishin intraday provider: the
exchange sources can backfill daily OHLCV, but they are not treated as a
replacement for the licensed/private intraday runtime.
"""

from __future__ import annotations

import json
import re
import time
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
TWSE_DAILY_ADAPTER_VERSION: Final = "twse-official-daily.v2"
TPEX_DAILY_SOURCE_CODE: Final = "TPEX_OFFICIAL_DAILY"
TPEX_DAILY_ADAPTER_VERSION: Final = "tpex-official-daily.v2"
DEFAULT_READINESS_MAX_ATTEMPTS: Final = 3
DEFAULT_READINESS_MAX_TOTAL_WAIT_SECONDS: Final = 90.0
DEFAULT_READINESS_BACKOFF_SECONDS: Final = 30.0
_RETRYABLE_READINESS_CODES: Final = frozenset(
    {"EXCHANGE_NOT_READY", "EXCHANGE_EMPTY_PAYLOAD"}
)
_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_MISSING_MARKERS: Final = {"", "-", "--", "---", "X", "N/A", "null"}


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


def _explicit_previous_close(table: Mapping[str, Any], row: list[Any]) -> Decimal | None:
    """Only an explicitly named comparator; never derive close minus change."""
    indices = [index for index, name in enumerate(table["fields"])
               if name in {"previousClose", "前收盤價", "前一交易日收盤價"}]
    if not indices:
        return None
    if len(indices) != 1 or indices[0] >= len(row):
        raise HistoricalProviderError("INVALID_PAYLOAD", "ambiguous previousClose field")
    return _decimal(row[indices[0]], "previousClose")


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
    bars: list[HistoricalBar | None],
    retrieved_at: datetime,
    instrument_status: str | None = None,
    status_reason: str | None = None,
    status_explicit: bool = False,
) -> HistoricalFetchResult:
    # Provider adapters may use ``None`` to represent a symbol absent from an
    # official market-level payload. Absence is a result state, not a bar;
    # filter it before any date dereference and let the caller apply the
    # lifecycle-aware no-trade policy.
    accepted_bars = tuple(bar for bar in bars if bar is not None)
    by_date = {bar.trading_date: bar for bar in accepted_bars}
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
    """Fetch official TWSE daily OHLCV for a bounded date window.

    In ``market_batch`` mode, the one-date ``MI_INDEX`` endpoint is fetched
    once and indexed by symbol for the formal post-close path.  The existing
    instrument/month path remains available for multi-day history.
    """

    source_code = TWSE_DAILY_SOURCE_CODE
    adapter_version = TWSE_DAILY_ADAPTER_VERSION

    def __init__(
        self,
        *,
        start_date: date,
        end_date: date,
        base_url: str = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY",
        market_base_url: str = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX",
        timeout: float = 30.0,
        transport: Transport = _read_url,
        clock: Callable[[], datetime] | None = None,
        market_batch: bool = False,
        readiness_max_attempts: int = DEFAULT_READINESS_MAX_ATTEMPTS,
        readiness_max_total_wait_seconds: float = DEFAULT_READINESS_MAX_TOTAL_WAIT_SECONDS,
        readiness_backoff_seconds: float = DEFAULT_READINESS_BACKOFF_SECONDS,
        readiness_sleep: Callable[[float], None] = time.sleep,
        readiness_clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if readiness_max_attempts < 1:
            raise ValueError("readiness_max_attempts must be positive")
        if readiness_max_total_wait_seconds < 0 or readiness_backoff_seconds < 0:
            raise ValueError("readiness timing must be non-negative")
        self.start_date = start_date
        self.end_date = end_date
        self.base_url = base_url
        self.market_base_url = market_base_url
        self.timeout = timeout
        self.transport = transport
        self.clock = clock or (lambda: datetime.now(TAIPEI))
        self.market_batch = market_batch
        self.readiness_max_attempts = readiness_max_attempts
        self.readiness_max_total_wait_seconds = readiness_max_total_wait_seconds
        self.readiness_backoff_seconds = readiness_backoff_seconds
        self.readiness_sleep = readiness_sleep
        self.readiness_clock = readiness_clock
        self.readiness_attempt_count = 0
        self.readiness_retry_count = 0
        self.readiness_wait_seconds = 0.0
        self.last_market_failure_code: str | None = None
        self._market_cache: tuple[datetime, dict[str, HistoricalBar]] | None = None
        self._market_failure: HistoricalProviderError | None = None

    def _fetch_market_day_once(self) -> tuple[datetime, dict[str, HistoricalBar]]:
        if self.start_date != self.end_date:
            raise HistoricalProviderError(
                "MARKET_BATCH_DATE_WINDOW",
                "market-level daily endpoint requires a single trading date",
            )
        if self._market_cache is not None:
            return self._market_cache
        target_date = self.start_date
        query = urlencode(
            {
                "date": target_date.strftime("%Y%m%d"),
                "type": "ALLBUT0999",
                "response": "json",
            }
        )
        payload = _json(self.transport, f"{self.market_base_url}?{query}", self.timeout)
        if str(payload.get("stat", "")).upper() != "OK":
            raise HistoricalProviderError(
                "EXCHANGE_NOT_READY", str(payload.get("stat", "unknown"))
            )
        response_date = str(payload.get("date", ""))
        if response_date != target_date.strftime("%Y%m%d"):
            raise HistoricalProviderError(
                "PROVIDER_DATE_MISMATCH",
                f"TWSE response date {response_date!r} != {target_date.isoformat()}",
            )
        tables = payload.get("tables")
        if not isinstance(tables, list):
            raise HistoricalProviderError("INVALID_PAYLOAD", "TWSE tables must be an array")
        table = next(
            (
                item
                for item in tables
                if isinstance(item, Mapping)
                and isinstance(item.get("fields"), list)
                and item["fields"]
                and item["fields"][0] == "證券代號"
                and isinstance(item.get("data"), list)
            ),
            None,
        )
        if table is None:
            raise HistoricalProviderError(
                "INVALID_PAYLOAD", "TWSE market close table is missing"
            )
        bars: dict[str, HistoricalBar] = {}
        for row in table["data"]:
            if not isinstance(row, list) or len(row) < 9:
                raise HistoricalProviderError(
                    "INVALID_PAYLOAD", "TWSE market close row is incomplete"
                )
            code = str(row[0]).strip()
            if not code:
                continue
            if code in bars:
                raise HistoricalProviderError("DUPLICATE_INSTRUMENT_ROW", code)
            bar = HistoricalBar(
                trading_date=target_date,
                open=_decimal(row[5], "open"),
                high=_decimal(row[6], "high"),
                low=_decimal(row[7], "low"),
                close=_decimal(row[8], "close"),
                volume=_decimal(row[2], "volume"),
                previous_close=_explicit_previous_close(table, row),
            )
            _validate_bar(bar)
            bars[code] = bar
        if not bars:
            raise HistoricalProviderError(
                "EXCHANGE_EMPTY_PAYLOAD", "TWSE market close table contains no rows"
            )
        self._market_cache = (self.clock(), bars)
        return self._market_cache

    def _fetch_market_day(self) -> tuple[datetime, dict[str, HistoricalBar]]:
        if self._market_failure is not None:
            raise self._market_failure
        if self._market_cache is not None:
            return self._market_cache
        started = self.readiness_clock()
        while True:
            self.readiness_attempt_count += 1
            try:
                return self._fetch_market_day_once()
            except HistoricalProviderError as exc:
                self.last_market_failure_code = exc.code
                if exc.code not in _RETRYABLE_READINESS_CODES:
                    self._market_failure = exc
                    raise
                elapsed = max(0.0, self.readiness_clock() - started)
                remaining = self.readiness_max_total_wait_seconds - elapsed
                if self.readiness_attempt_count >= self.readiness_max_attempts or remaining <= 0:
                    self._market_failure = exc
                    raise
                delay = min(
                    self.readiness_backoff_seconds * (2 ** (self.readiness_attempt_count - 1)),
                    remaining,
                )
                if delay <= 0:
                    self._market_failure = exc
                    raise
                self.readiness_retry_count += 1
                self.readiness_wait_seconds += delay
                self.readiness_sleep(delay)

    def _fetch_market_instrument(
        self, instrument_code: str, market_code: str
    ) -> HistoricalFetchResult:
        retrieved_at, bars = self._fetch_market_day()
        bar = bars.get(instrument_code)
        return _result(
            instrument_code=instrument_code,
            market_code=market_code,
            source_code=self.source_code,
            adapter_version=self.adapter_version,
            bars=[bar] if bar is not None else [],
            retrieved_at=retrieved_at,
            instrument_status=("AVAILABLE" if bar is not None else "EXCHANGE_CONFIRMED_NO_DATA"),
            status_reason=(
                None
                if bar is not None
                else "official TWSE market dataset contained no row for requested instrument/date"
            ),
            status_explicit=bar is None,
        )

    def fetch_market_day(self) -> tuple[datetime, dict[str, HistoricalBar]]:
        """Fetch one validated market-level payload without persistence."""

        return self._fetch_market_day()

    def fetch_daily(self, instrument_code: str, market_code: str) -> HistoricalFetchResult:
        instrument_code = _validate_identifier(instrument_code, "instrument_code")
        market_code = _validate_identifier(market_code, "market_code")
        if market_code != "TPE":
            raise HistoricalProviderError("UNSUPPORTED_MARKET", market_code)
        if self.market_batch and self.start_date == self.end_date:
            return self._fetch_market_instrument(instrument_code, market_code)
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
    In ``market_batch`` mode, the one-date ``dailyQuotes`` endpoint is fetched
    once and indexed by symbol for the formal post-close path.
    """

    source_code = TPEX_DAILY_SOURCE_CODE
    adapter_version = TPEX_DAILY_ADAPTER_VERSION

    def __init__(
        self,
        *,
        start_date: date,
        end_date: date,
        base_url: str = "https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock",
        market_base_url: str = "https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes",
        timeout: float = 30.0,
        transport: Transport = _read_url,
        clock: Callable[[], datetime] | None = None,
        market_batch: bool = False,
        readiness_max_attempts: int = DEFAULT_READINESS_MAX_ATTEMPTS,
        readiness_max_total_wait_seconds: float = DEFAULT_READINESS_MAX_TOTAL_WAIT_SECONDS,
        readiness_backoff_seconds: float = DEFAULT_READINESS_BACKOFF_SECONDS,
        readiness_sleep: Callable[[float], None] = time.sleep,
        readiness_clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if readiness_max_attempts < 1:
            raise ValueError("readiness_max_attempts must be positive")
        if readiness_max_total_wait_seconds < 0 or readiness_backoff_seconds < 0:
            raise ValueError("readiness timing must be non-negative")
        self.start_date = start_date
        self.end_date = end_date
        self.base_url = base_url
        self.market_base_url = market_base_url
        self.timeout = timeout
        self.transport = transport
        self.clock = clock or (lambda: datetime.now(TAIPEI))
        self.market_batch = market_batch
        self.readiness_max_attempts = readiness_max_attempts
        self.readiness_max_total_wait_seconds = readiness_max_total_wait_seconds
        self.readiness_backoff_seconds = readiness_backoff_seconds
        self.readiness_sleep = readiness_sleep
        self.readiness_clock = readiness_clock
        self.readiness_attempt_count = 0
        self.readiness_retry_count = 0
        self.readiness_wait_seconds = 0.0
        self.last_market_failure_code: str | None = None
        self._market_cache: tuple[datetime, dict[str, HistoricalBar]] | None = None
        self._market_failure: HistoricalProviderError | None = None

    def _fetch_market_day_once(self) -> tuple[datetime, dict[str, HistoricalBar]]:
        if self.start_date != self.end_date:
            raise HistoricalProviderError(
                "MARKET_BATCH_DATE_WINDOW",
                "market-level daily endpoint requires a single trading date",
            )
        if self._market_cache is not None:
            return self._market_cache
        target_date = self.start_date
        query = urlencode(
            {"date": target_date.strftime("%Y/%m/%d"), "response": "json"}
        )
        payload = _json(self.transport, f"{self.market_base_url}?{query}", self.timeout)
        if str(payload.get("stat", "")).lower() != "ok":
            raise HistoricalProviderError(
                "EXCHANGE_NOT_READY", str(payload.get("stat", "unknown"))
            )
        response_date = str(payload.get("date", ""))
        if response_date != target_date.strftime("%Y%m%d"):
            raise HistoricalProviderError(
                "PROVIDER_DATE_MISMATCH",
                f"TPEx response date {response_date!r} != {target_date.isoformat()}",
            )
        tables = payload.get("tables")
        if not isinstance(tables, list):
            raise HistoricalProviderError("INVALID_PAYLOAD", "TPEx tables must be an array")
        table = next(
            (
                item
                for item in tables
                if isinstance(item, Mapping)
                and item.get("title") == "上櫃股票行情"
                and isinstance(item.get("fields"), list)
                and item["fields"]
                and item["fields"][0] == "代號"
                and isinstance(item.get("data"), list)
            ),
            None,
        )
        if table is None:
            raise HistoricalProviderError(
                "INVALID_PAYLOAD", "TPEx market close table is missing"
            )
        bars: dict[str, HistoricalBar] = {}
        for row in table["data"]:
            if not isinstance(row, list) or len(row) < 9:
                raise HistoricalProviderError(
                    "INVALID_PAYLOAD", "TPEx market close row is incomplete"
                )
            code = str(row[0]).strip()
            if not code:
                continue
            if code in bars:
                raise HistoricalProviderError("DUPLICATE_INSTRUMENT_ROW", code)
            bar = HistoricalBar(
                trading_date=target_date,
                open=_decimal(row[4], "open"),
                high=_decimal(row[5], "high"),
                low=_decimal(row[6], "low"),
                close=_decimal(row[2], "close"),
                volume=_decimal(row[8], "volume"),
                previous_close=_explicit_previous_close(table, row),
            )
            _validate_bar(bar)
            bars[code] = bar
        if not bars:
            raise HistoricalProviderError(
                "EXCHANGE_EMPTY_PAYLOAD", "TPEx market close table contains no rows"
            )
        self._market_cache = (self.clock(), bars)
        return self._market_cache

    def _fetch_market_day(self) -> tuple[datetime, dict[str, HistoricalBar]]:
        if self._market_failure is not None:
            raise self._market_failure
        if self._market_cache is not None:
            return self._market_cache
        started = self.readiness_clock()
        while True:
            self.readiness_attempt_count += 1
            try:
                return self._fetch_market_day_once()
            except HistoricalProviderError as exc:
                self.last_market_failure_code = exc.code
                if exc.code not in _RETRYABLE_READINESS_CODES:
                    self._market_failure = exc
                    raise
                elapsed = max(0.0, self.readiness_clock() - started)
                remaining = self.readiness_max_total_wait_seconds - elapsed
                if self.readiness_attempt_count >= self.readiness_max_attempts or remaining <= 0:
                    self._market_failure = exc
                    raise
                delay = min(
                    self.readiness_backoff_seconds * (2 ** (self.readiness_attempt_count - 1)),
                    remaining,
                )
                if delay <= 0:
                    self._market_failure = exc
                    raise
                self.readiness_retry_count += 1
                self.readiness_wait_seconds += delay
                self.readiness_sleep(delay)

    def _fetch_market_instrument(
        self, instrument_code: str, market_code: str
    ) -> HistoricalFetchResult:
        retrieved_at, bars = self._fetch_market_day()
        bar = bars.get(instrument_code)
        return _result(
            instrument_code=instrument_code,
            market_code=market_code,
            source_code=self.source_code,
            adapter_version=self.adapter_version,
            bars=[bar] if bar is not None else [],
            retrieved_at=retrieved_at,
            instrument_status=("AVAILABLE" if bar is not None else "EXCHANGE_CONFIRMED_NO_DATA"),
            status_reason=(
                None
                if bar is not None
                else "official TPEx market dataset contained no row for requested instrument/date"
            ),
            status_explicit=bar is None,
        )

    def fetch_market_day(self) -> tuple[datetime, dict[str, HistoricalBar]]:
        """Fetch one validated market-level payload without persistence."""

        return self._fetch_market_day()

    def fetch_daily(self, instrument_code: str, market_code: str) -> HistoricalFetchResult:
        instrument_code = _validate_identifier(instrument_code, "instrument_code")
        market_code = _validate_identifier(market_code, "market_code")
        if market_code != "TWO":
            raise HistoricalProviderError("UNSUPPORTED_MARKET", market_code)
        if self.market_batch and self.start_date == self.end_date:
            return self._fetch_market_instrument(instrument_code, market_code)
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
    "DEFAULT_READINESS_BACKOFF_SECONDS",
    "DEFAULT_READINESS_MAX_ATTEMPTS",
    "DEFAULT_READINESS_MAX_TOTAL_WAIT_SECONDS",
    "TPEX_DAILY_ADAPTER_VERSION",
    "TPEX_DAILY_SOURCE_CODE",
    "TWSE_DAILY_ADAPTER_VERSION",
    "TWSE_DAILY_SOURCE_CODE",
    "TpexOfficialDailyProvider",
    "TwseOfficialDailyProvider",
]
