"""Typed, provider-neutral contracts for official market index payloads.

This module parses and maps the official TWSE/TPEx broad-market index
reports. TWSE publishes target-date close/change in
``afterTrading/MI_INDEX`` and daily OHLC in ``MI_5MINS_HIST``; TPEx publishes
OHLC and change in ``tpex_index``. It does not persist facts, expose FastAPI
routes, or map turnover. Invalid or incomplete provider payloads become
``UNAVAILABLE`` results; they never fall back to Preview and never coerce
missing numbers to zero. The fetch helper keeps transport injection at the
runtime boundary.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any, Final
from zoneinfo import ZoneInfo

TAIPEI: Final = ZoneInfo("Asia/Taipei")

TWSE_MARKET_AGGREGATE_SOURCE_IDENTITY: Final = "TWSE_OFFICIAL_MARKET_AGGREGATE"
TWSE_MARKET_AGGREGATE_ADAPTER_VERSION: Final = "twse-official-market-aggregate.v1"
TWSE_MARKET_INDEX_IDENTITY: Final = "TWSE:TAIEX"
TWSE_MARKET_INDEX_DISPLAY_NAME: Final = "Taiwan Stock Exchange Capitalization Weighted Stock Index"
TWSE_MARKET_INDEX_RAW_NAME: Final = "發行量加權股價指數"
TWSE_MARKET_INDEX_DATASET: Final = "afterTrading.MI_INDEX"
TWSE_MARKET_INDEX_ENDPOINT: Final = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
TWSE_MARKET_INDEX_ADAPTER_VERSION: Final = "twse-official-taiex-index.v2"
TWSE_MARKET_INDEX_OHLC_DATASET: Final = "indicesReport.MI_5MINS_HIST"
TWSE_MARKET_INDEX_OHLC_ENDPOINT: Final = (
    "https://www.twse.com.tw/indicesReport/MI_5MINS_HIST"
)
TWSE_INDEX_DATE_FIELD: Final = "日期"
TWSE_INDEX_VALUE_FIELD: Final = "收盤指數"
TWSE_INDEX_SIGN_FIELD: Final = "漲跌"
TWSE_INDEX_CHANGE_FIELD: Final = "漲跌點數"
TWSE_INDEX_CHANGE_PCT_FIELD: Final = "漲跌百分比"
TWSE_INDEX_VALUE_PATH: Final = (
    "$.tables[<title='價格指數(臺灣證券交易所)'>].data["
    "<row where 指數 == '發行量加權股價指數'>].收盤指數"
)
TWSE_TARGET_INDEX_TABLE_TITLE: Final = "價格指數(臺灣證券交易所)"
TWSE_TARGET_INDEX_SIGN_FIELD: Final = "漲跌(+/-)"
TWSE_TARGET_INDEX_CHANGE_FIELD: Final = "漲跌點數"
TWSE_TARGET_INDEX_CHANGE_PCT_FIELD: Final = "漲跌百分比(%)"
TWSE_TARGET_INDEX_VALUE_PATH: Final = TWSE_INDEX_VALUE_PATH
TWSE_INDEX_OHLC_FIELDS: Final = ("開盤指數", "最高指數", "最低指數", "收盤指數")
TWSE_INDEX_OHLC_VALUE_PATH: Final = (
    "$.data[<row where 日期 == target>].[開盤指數,最高指數,最低指數,收盤指數]"
)

TPEX_MARKET_AGGREGATE_SOURCE_IDENTITY: Final = "TPEX_OFFICIAL_MARKET_AGGREGATE"
TPEX_MARKET_AGGREGATE_ADAPTER_VERSION: Final = "tpex-official-market-aggregate.v1"
TPEX_MARKET_INDEX_IDENTITY: Final = "TPEX:TPEx"
TPEX_MARKET_INDEX_DISPLAY_NAME: Final = "TPEx Exchange Capitalization Weighted Stock Index"
TPEX_MARKET_INDEX_DATASET: Final = "tpex_index"
TPEX_MARKET_INDEX_ENDPOINT: Final = "https://www.tpex.org.tw/openapi/v1/tpex_index"
TPEX_INDEX_CROSSCHECK_DATASET: Final = "tpex_index"
TPEX_INDEX_CROSSCHECK_ENDPOINT: Final = "https://www.tpex.org.tw/openapi/v1/tpex_index"
TPEX_INDEX_DATE_FIELD: Final = "Date"
TPEX_INDEX_VALUE_FIELD: Final = "TPExIndex"
TPEX_INDEX_CHANGE_FIELD: Final = "Change"
TPEX_INDEX_VALUE_PATH: Final = "$.<row where Date == target>.Close"
TPEX_INDEX_OHLC_FIELDS: Final = ("Open", "High", "Low", "Close")
TPEX_INDEX_OHLC_VALUE_PATH: Final = "$.<row where Date == target>.[Open,High,Low,Close]"

SOURCE_PUBLICATION_DAILY: Final = "DAILY_RESPONSE_AS_PUBLISHED"
FINALITY_NOT_EXPLICIT: Final = "NOT_EXPLICITLY_DECLARED_BY_SOURCE"
CORRECTION_EVIDENCE: Final = (
    "NO_EXPLICIT_REVISION_FIELD; response content hash recorded for supersession evidence"
)


class IndexDataStatus(StrEnum):
    """Publication state understood by the typed index boundary."""

    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    PREVIEW = "PREVIEW"


class IndexContractError(ValueError):
    """Machine-readable source-payload validation error."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class MarketIndexResult:
    """One normalized broad-market index result without persistence concerns."""

    market: str
    index_identity: str
    display_name: str
    trading_date: date | None
    value: Decimal | None
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    previous_close: Decimal | None
    change: Decimal | None
    change_pct: Decimal | None
    source_provider: str
    source_identity: str
    source_dataset: str
    source_endpoint: str
    source_field_path: str
    raw_provider_date: str | None
    retrieved_at: datetime
    as_of: datetime
    data_status: IndexDataStatus
    quality_status: str
    source_publication: str
    finality: str
    correction_evidence: str
    lineage: str
    adapter_version: str
    status_reason: str | None = None
    response_content_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe shape for focused contract inspection."""

        return {
            "market": self.market,
            "indexIdentity": self.index_identity,
            "displayName": self.display_name,
            "tradingDate": self.trading_date.isoformat() if self.trading_date else None,
            "value": str(self.value) if self.value is not None else None,
            "open": str(self.open) if self.open is not None else None,
            "high": str(self.high) if self.high is not None else None,
            "low": str(self.low) if self.low is not None else None,
            "previousClose": (
                str(self.previous_close) if self.previous_close is not None else None
            ),
            "change": str(self.change) if self.change is not None else None,
            "changePct": str(self.change_pct) if self.change_pct is not None else None,
            "sourceProvider": self.source_provider,
            "sourceIdentity": self.source_identity,
            "sourceDataset": self.source_dataset,
            "sourceEndpoint": self.source_endpoint,
            "sourceFieldPath": self.source_field_path,
            "rawProviderDate": self.raw_provider_date,
            "retrievedAt": self.retrieved_at.isoformat(),
            "asOf": self.as_of.isoformat(),
            "dataStatus": self.data_status.value,
            "qualityStatus": self.quality_status,
            "sourcePublication": self.source_publication,
            "finality": self.finality,
            "correctionEvidence": self.correction_evidence,
            "lineage": self.lineage,
            "adapterVersion": self.adapter_version,
            "statusReason": self.status_reason,
            "responseContentHash": self.response_content_hash,
        }


@dataclass(frozen=True)
class TpexIndexCrossCheck:
    """Normalized point from TPEx's separate historical index endpoint."""

    raw_provider_date: str | None
    trading_date: date | None
    value: Decimal | None
    change: Decimal | None
    data_status: IndexDataStatus
    status_reason: str | None
    response_content_hash: str | None


def _content_hash(payload: object) -> str:
    try:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError):
        canonical = repr(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _decimal(value: object, field: str, *, non_negative: bool = False) -> Decimal:
    if value is None or isinstance(value, bool) or str(value).strip() == "":
        raise IndexContractError(f"MISSING_{field.upper()}", f"{field} is required")
    try:
        parsed = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError) as exc:
        raise IndexContractError("INVALID_NUMBER", f"{field} is not numeric") from exc
    if not parsed.is_finite():
        raise IndexContractError("INVALID_NUMBER", f"{field} must be finite")
    if non_negative and parsed < 0:
        raise IndexContractError("INVALID_NUMBER", f"{field} cannot be negative")
    return parsed


def _roc_date(value: object, field: str) -> date:
    raw = str(value).strip()
    compact = raw.replace("/", "").replace("-", "")
    if len(compact) != 7 or not compact.isdigit():
        raise IndexContractError("INVALID_DATE", f"{field} must be ROC YYYMMDD")
    year = int(compact[:3]) + 1911
    month = int(compact[3:5])
    day = int(compact[5:])
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise IndexContractError("INVALID_DATE", f"{field} is not a valid date") from exc


def _gregorian_date(value: object, field: str) -> date:
    raw = str(value).strip()
    if len(raw) != 8 or not raw.isdigit():
        raise IndexContractError("INVALID_DATE", f"{field} must be Gregorian YYYYMMDD")
    try:
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:]))
    except ValueError as exc:
        raise IndexContractError("INVALID_DATE", f"{field} is not a valid date") from exc


def _market_index_date(value: object, field: str) -> date:
    raw = str(value or "").strip()
    compact = raw.replace("/", "").replace("-", "")
    if len(compact) == 7:
        return _roc_date(raw, field)
    if len(compact) == 8:
        return _gregorian_date(compact, field)
    raise IndexContractError("INVALID_DATE", f"{field} must be ROC or Gregorian date")


def _signed_change(sign: object, magnitude: object) -> Decimal:
    parsed = _decimal(magnitude, "change", non_negative=True)
    marker = unicodedata.normalize("NFKC", _provider_text(sign))
    if marker == "+":
        return parsed
    if marker == "-":
        return -parsed
    if marker in {"0", ""} and parsed == 0:
        return Decimal("0")
    raise IndexContractError("INVALID_CHANGE_SIGN", "漲跌 must be +, -, or zero")


def _provider_text(value: object) -> str:
    """Normalize the small HTML fragments used by TWSE table cells."""

    raw = "" if value is None else str(value)
    return html.unescape(re.sub(r"<[^>]*>", "", raw)).strip()


def _rows(payload: object, *, wrapper: str | None = None) -> Sequence[Mapping[str, Any]]:
    candidate: object = payload
    if wrapper is not None:
        if not isinstance(payload, Mapping):
            raise IndexContractError("INVALID_PAYLOAD", "provider payload must be an object")
        candidate = payload.get(wrapper)
    if not isinstance(candidate, Sequence) or isinstance(candidate, (str, bytes, bytearray)):
        raise IndexContractError("INVALID_PAYLOAD", "provider rows must be an array")
    rows: list[Mapping[str, Any]] = []
    for row in candidate:
        if not isinstance(row, Mapping):
            raise IndexContractError("INVALID_PAYLOAD", "provider rows must contain objects")
        rows.append(row)
    return rows


def _source_metadata(market: str) -> dict[str, str]:
    if market == "TPE":
        return {
            "index_identity": TWSE_MARKET_INDEX_IDENTITY,
            "display_name": TWSE_MARKET_INDEX_DISPLAY_NAME,
            "source_provider": "TWSE",
            "source_identity": TWSE_MARKET_AGGREGATE_SOURCE_IDENTITY,
            "source_dataset": TWSE_MARKET_INDEX_DATASET,
            "source_endpoint": TWSE_MARKET_INDEX_ENDPOINT,
            "source_field_path": TWSE_INDEX_VALUE_PATH,
            "adapter_version": TWSE_MARKET_INDEX_ADAPTER_VERSION,
            "lineage": (
                "TWSE -> target-date afterTrading/MI_INDEX + MI_5MINS_HIST "
                "-> TAIEX row selectors -> market index OHLC contract"
            ),
        }
    if market == "TWO":
        return {
            "index_identity": TPEX_MARKET_INDEX_IDENTITY,
            "display_name": TPEX_MARKET_INDEX_DISPLAY_NAME,
            "source_provider": "TPEx",
            "source_identity": TPEX_MARKET_AGGREGATE_SOURCE_IDENTITY,
            "source_dataset": TPEX_MARKET_INDEX_DATASET,
            "source_endpoint": TPEX_MARKET_INDEX_ENDPOINT,
            "source_field_path": TPEX_INDEX_VALUE_PATH,
            "adapter_version": TPEX_MARKET_AGGREGATE_ADAPTER_VERSION,
            "lineage": "TPEx -> tpex_index -> TPExIndex OHLC row -> market index contract",
        }
    raise IndexContractError("INVALID_MARKET", f"unsupported market: {market}")


def _unavailable(
    market: str,
    *,
    retrieved_at: datetime,
    as_of: datetime,
    reason: str,
    raw_provider_date: str | None = None,
    response_content_hash: str | None = None,
) -> MarketIndexResult:
    metadata = _source_metadata(market)
    return MarketIndexResult(
        market=market,
        index_identity=metadata["index_identity"],
        display_name=metadata["display_name"],
        trading_date=None,
        value=None,
        open=None,
        high=None,
        low=None,
        previous_close=None,
        change=None,
        change_pct=None,
        source_provider=metadata["source_provider"],
        source_identity=metadata["source_identity"],
        source_dataset=metadata["source_dataset"],
        source_endpoint=metadata["source_endpoint"],
        source_field_path=metadata["source_field_path"],
        raw_provider_date=raw_provider_date,
        retrieved_at=retrieved_at,
        as_of=as_of,
        data_status=IndexDataStatus.UNAVAILABLE,
        quality_status=reason,
        source_publication=SOURCE_PUBLICATION_DAILY,
        finality=FINALITY_NOT_EXPLICIT,
        correction_evidence=CORRECTION_EVIDENCE,
        lineage=metadata["lineage"],
        adapter_version=metadata["adapter_version"],
        status_reason=reason,
        response_content_hash=response_content_hash,
    )


def unavailable_market_index(
    market: str,
    *,
    retrieved_at: datetime,
    as_of: datetime,
    reason: str,
) -> MarketIndexResult:
    """Build an explicit unavailable result for provider/transport failures."""

    return _unavailable(market, retrieved_at=retrieved_at, as_of=as_of, reason=reason)


def parse_twse_market_index(
    payload: object,
    *,
    retrieved_at: datetime,
    as_of: datetime,
) -> MarketIndexResult:
    """Parse the exact TAIEX row from the official TWSE ``MI_INDEX`` response."""

    content_hash = _content_hash(payload)
    try:
        rows = _rows(payload)
        matches = [row for row in rows if row.get("指數") == TWSE_MARKET_INDEX_RAW_NAME]
        if not matches:
            return _unavailable(
                "TPE",
                retrieved_at=retrieved_at,
                as_of=as_of,
                reason="TARGET_INDEX_ROW_MISSING",
                response_content_hash=content_hash,
            )
        if len(matches) != 1:
            return _unavailable(
                "TPE",
                retrieved_at=retrieved_at,
                as_of=as_of,
                reason="TARGET_INDEX_ROW_AMBIGUOUS",
                response_content_hash=content_hash,
            )
        row = matches[0]
        raw_date = str(row.get(TWSE_INDEX_DATE_FIELD, ""))
        trading_date = _roc_date(raw_date, TWSE_INDEX_DATE_FIELD)
        value = _decimal(row.get(TWSE_INDEX_VALUE_FIELD), TWSE_INDEX_VALUE_FIELD, non_negative=True)
        change = _signed_change(row.get(TWSE_INDEX_SIGN_FIELD), row.get(TWSE_INDEX_CHANGE_FIELD))
        raw_change_pct = row.get(TWSE_INDEX_CHANGE_PCT_FIELD)
        if raw_change_pct is None or str(raw_change_pct).strip() == "":
            raise IndexContractError("MISSING_CHANGE_PCT", "漲跌百分比 is required for TWSE")
        change_pct = _decimal(raw_change_pct, TWSE_INDEX_CHANGE_PCT_FIELD)
        previous_close = value - change
        metadata = _source_metadata("TPE")
        return MarketIndexResult(
            market="TPE",
            index_identity=metadata["index_identity"],
            display_name=metadata["display_name"],
            trading_date=trading_date,
            value=value,
            open=None,
            high=None,
            low=None,
            previous_close=previous_close,
            change=change,
            change_pct=change_pct,
            source_provider=metadata["source_provider"],
            source_identity=metadata["source_identity"],
            source_dataset=metadata["source_dataset"],
            source_endpoint=metadata["source_endpoint"],
            source_field_path=metadata["source_field_path"],
            raw_provider_date=raw_date,
            retrieved_at=retrieved_at,
            as_of=as_of,
            data_status=IndexDataStatus.AVAILABLE,
            quality_status="SOURCE_FIELDS_VALID_BACKEND_PREVIOUS_CLOSE_DERIVED",
            source_publication=SOURCE_PUBLICATION_DAILY,
            finality=FINALITY_NOT_EXPLICIT,
            correction_evidence=CORRECTION_EVIDENCE,
            lineage=metadata["lineage"],
            adapter_version=metadata["adapter_version"],
            response_content_hash=content_hash,
        )
    except IndexContractError as exc:
        raw_date = None
        if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
            target = next(
                (
                    row
                    for row in payload
                    if isinstance(row, Mapping) and row.get("指數") == TWSE_MARKET_INDEX_RAW_NAME
                ),
                None,
            )
            if isinstance(target, Mapping) and target.get(TWSE_INDEX_DATE_FIELD) is not None:
                raw_date = str(target[TWSE_INDEX_DATE_FIELD])
        return _unavailable(
            "TPE",
            retrieved_at=retrieved_at,
            as_of=as_of,
            reason=exc.code,
            raw_provider_date=raw_date,
            response_content_hash=content_hash,
        )


def parse_twse_target_date_market_index(
    payload: object,
    *,
    target_date: date,
    retrieved_at: datetime,
    as_of: datetime,
) -> MarketIndexResult:
    """Parse the target-date TAIEX row from TWSE's official daily report."""

    content_hash = _content_hash(payload)
    raw_provider_date: str | None = None
    try:
        if not isinstance(payload, Mapping):
            raise IndexContractError(
                "INVALID_PAYLOAD", "TWSE target-date payload must be an object"
            )
        raw_provider_date = _provider_text(payload.get("date"))
        provider_date = _gregorian_date(raw_provider_date, "date")
        if provider_date != target_date:
            return _unavailable(
                "TPE",
                retrieved_at=retrieved_at,
                as_of=as_of,
                reason="PROVIDER_DATE_MISMATCH",
                raw_provider_date=raw_provider_date,
                response_content_hash=content_hash,
            )
        tables = payload.get("tables")
        if not isinstance(tables, list):
            raise IndexContractError("INVALID_PAYLOAD", "TWSE target-date tables must be an array")
        candidates = [
            table
            for table in tables
            if isinstance(table, Mapping)
            and _provider_text(table.get("title")).endswith(TWSE_TARGET_INDEX_TABLE_TITLE)
            and isinstance(table.get("data"), list)
        ]
        if not candidates:
            raise IndexContractError("TARGET_INDEX_TABLE_MISSING", "TWSE TAIEX table is missing")
        if len(candidates) != 1:
            raise IndexContractError(
                "TARGET_INDEX_TABLE_AMBIGUOUS", "TWSE TAIEX table is ambiguous"
            )
        table = candidates[0]
        fields = table.get("fields")
        if not isinstance(fields, list) or not fields:
            raise IndexContractError("TARGET_INDEX_FIELDS_MISSING", "TWSE TAIEX fields are missing")
        rows = table["data"]
        mapped_rows: list[Mapping[str, Any]] = []
        for row in rows:
            if isinstance(row, Mapping):
                mapped_rows.append(row)
            elif isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray)):
                mapped_rows.append(
                    dict(zip((_provider_text(field) for field in fields), row, strict=False))
                )
            else:
                raise IndexContractError(
                    "INVALID_PAYLOAD", "TWSE TAIEX rows must be arrays or objects"
                )
        matches = [
            row
            for row in mapped_rows
            if _provider_text(row.get("指數")) == TWSE_MARKET_INDEX_RAW_NAME
        ]
        if not matches:
            raise IndexContractError("TARGET_INDEX_ROW_MISSING", "TWSE TAIEX row is missing")
        if len(matches) != 1:
            raise IndexContractError("TARGET_INDEX_ROW_AMBIGUOUS", "TWSE TAIEX row is ambiguous")
        row = matches[0]
        value = _decimal(
            _provider_text(row.get(TWSE_INDEX_VALUE_FIELD)),
            TWSE_INDEX_VALUE_FIELD,
            non_negative=True,
        )
        change = _signed_change(
            row.get(TWSE_TARGET_INDEX_SIGN_FIELD),
            _provider_text(row.get(TWSE_TARGET_INDEX_CHANGE_FIELD)),
        )
        raw_change_pct = _provider_text(row.get(TWSE_TARGET_INDEX_CHANGE_PCT_FIELD))
        if not raw_change_pct:
            raise IndexContractError("MISSING_CHANGE_PCT", "漲跌百分比(%) is required for TWSE")
        change_pct = _decimal(raw_change_pct.rstrip("%"), TWSE_TARGET_INDEX_CHANGE_PCT_FIELD)
        metadata = _source_metadata("TPE")
        return MarketIndexResult(
            market="TPE",
            index_identity=metadata["index_identity"],
            display_name=metadata["display_name"],
            trading_date=provider_date,
            value=value,
            open=None,
            high=None,
            low=None,
            previous_close=value - change,
            change=change,
            change_pct=change_pct,
            source_provider=metadata["source_provider"],
            source_identity=metadata["source_identity"],
            source_dataset=metadata["source_dataset"],
            source_endpoint=metadata["source_endpoint"],
            source_field_path=TWSE_TARGET_INDEX_VALUE_PATH,
            raw_provider_date=raw_provider_date,
            retrieved_at=retrieved_at,
            as_of=as_of,
            data_status=IndexDataStatus.AVAILABLE,
            quality_status="SOURCE_FIELDS_VALID_TARGET_DATE_BACKEND_PREVIOUS_CLOSE_DERIVED",
            source_publication=SOURCE_PUBLICATION_DAILY,
            finality=FINALITY_NOT_EXPLICIT,
            correction_evidence=CORRECTION_EVIDENCE,
            lineage=(
                "TWSE -> target-date afterTrading/MI_INDEX -> TAIEX row selector "
                "-> signed change and previous-close derivation -> market index contract"
            ),
            adapter_version=TWSE_MARKET_INDEX_ADAPTER_VERSION,
            response_content_hash=content_hash,
        )
    except IndexContractError as exc:
        return _unavailable(
            "TPE",
            retrieved_at=retrieved_at,
            as_of=as_of,
            reason=exc.code,
            raw_provider_date=raw_provider_date,
            response_content_hash=content_hash,
        )


def parse_twse_market_index_ohlc(
    payload: object,
    *,
    retrieved_at: datetime,
    as_of: datetime,
    target_date: date | None = None,
) -> MarketIndexResult:
    """Parse the official TWSE daily TAIEX OHLC history report."""

    content_hash = _content_hash(payload)
    raw_date: str | None = None
    try:
        if not isinstance(payload, Mapping):
            raise IndexContractError("INVALID_PAYLOAD", "TWSE OHLC payload must be an object")
        rows = payload.get("data")
        if not isinstance(rows, list):
            raise IndexContractError("INVALID_PAYLOAD", "TWSE OHLC data must be an array")
        candidates = [
            row
            for row in rows
            if isinstance(row, Sequence)
            and not isinstance(row, (str, bytes, bytearray))
            and len(row) >= 5
            and (target_date is None or _market_index_date(row[0], "日期") == target_date)
        ]
        if len(candidates) != 1:
            raise IndexContractError(
                "TARGET_INDEX_ROW_MISSING" if not candidates else "TARGET_INDEX_ROW_AMBIGUOUS",
                "TWSE OHLC target row is missing or ambiguous",
            )
        row = candidates[0]
        raw_date = str(row[0])
        trading_date = _market_index_date(row[0], "日期")
        open_ = _decimal(row[1], "開盤指數", non_negative=True)
        high = _decimal(row[2], "最高指數", non_negative=True)
        low = _decimal(row[3], "最低指數", non_negative=True)
        value = _decimal(row[4], "收盤指數", non_negative=True)
        if not low <= min(open_, high, value) or max(open_, low, value) > high:
            raise IndexContractError("INVALID_OHLC", "TWSE OHLC values violate high/low bounds")
        metadata = _source_metadata("TPE")
        return MarketIndexResult(
            market="TPE",
            index_identity=metadata["index_identity"],
            display_name=metadata["display_name"],
            trading_date=trading_date,
            value=value,
            open=open_,
            high=high,
            low=low,
            previous_close=None,
            change=None,
            change_pct=None,
            source_provider="TWSE",
            source_identity=metadata["source_identity"],
            source_dataset=TWSE_MARKET_INDEX_OHLC_DATASET,
            source_endpoint=TWSE_MARKET_INDEX_OHLC_ENDPOINT,
            source_field_path=TWSE_INDEX_OHLC_VALUE_PATH,
            raw_provider_date=raw_date,
            retrieved_at=retrieved_at,
            as_of=as_of,
            data_status=IndexDataStatus.AVAILABLE,
            quality_status="SOURCE_FIELDS_VALID_OHLC",
            source_publication=SOURCE_PUBLICATION_DAILY,
            finality=FINALITY_NOT_EXPLICIT,
            correction_evidence=CORRECTION_EVIDENCE,
            lineage=(
                "TWSE -> indicesReport/MI_5MINS_HIST -> TAIEX OHLC row "
                "-> market index contract"
            ),
            adapter_version=TWSE_MARKET_AGGREGATE_ADAPTER_VERSION,
            response_content_hash=content_hash,
        )
    except IndexContractError as exc:
        return _unavailable(
            "TPE",
            retrieved_at=retrieved_at,
            as_of=as_of,
            reason=exc.code,
            raw_provider_date=raw_date,
            response_content_hash=content_hash,
        )


def parse_tpex_market_index(
    payload: object,
    *,
    retrieved_at: datetime,
    as_of: datetime,
    target_date: date | None = None,
) -> MarketIndexResult:
    """Parse the TPEx broad-market index from the official daily index response."""

    content_hash = _content_hash(payload)
    raw_date: str | None = None
    try:
        rows = _rows(payload, wrapper="value") if isinstance(payload, Mapping) else _rows(payload)
        if len(rows) == 1:
            row = rows[0]
        elif target_date is not None:
            candidates = []
            for candidate in rows:
                candidate_date = _market_index_date(
                    candidate.get(TPEX_INDEX_DATE_FIELD), TPEX_INDEX_DATE_FIELD
                )
                if candidate_date == target_date:
                    candidates.append(candidate)
            if not candidates:
                return _unavailable(
                    "TWO",
                    retrieved_at=retrieved_at,
                    as_of=as_of,
                    reason="TARGET_INDEX_ROW_MISSING",
                    response_content_hash=content_hash,
                )
            if len(candidates) != 1:
                return _unavailable(
                    "TWO",
                    retrieved_at=retrieved_at,
                    as_of=as_of,
                    reason="TARGET_INDEX_ROW_AMBIGUOUS",
                    response_content_hash=content_hash,
                )
            row = candidates[0]
        else:
            return _unavailable(
                "TWO",
                retrieved_at=retrieved_at,
                as_of=as_of,
                reason="TARGET_INDEX_ROW_AMBIGUOUS" if rows else "TARGET_INDEX_ROW_MISSING",
                response_content_hash=content_hash,
            )
        value_field = "Close" if row.get("Close") is not None else TPEX_INDEX_VALUE_FIELD
        raw_date = str(row.get(TPEX_INDEX_DATE_FIELD, ""))
        if value_field == TPEX_INDEX_VALUE_FIELD and not raw_date.isdigit():
            raise IndexContractError("INVALID_DATE", f"{TPEX_INDEX_DATE_FIELD} is invalid")
        trading_date = _market_index_date(raw_date, TPEX_INDEX_DATE_FIELD)
        value = _decimal(row.get(value_field), value_field, non_negative=True)
        change = _decimal(row.get(TPEX_INDEX_CHANGE_FIELD), TPEX_INDEX_CHANGE_FIELD)
        has_ohlc = all(row.get(field) is not None for field in TPEX_INDEX_OHLC_FIELDS)
        open_ = _decimal(row.get("Open"), "Open", non_negative=True) if has_ohlc else None
        high = _decimal(row.get("High"), "High", non_negative=True) if has_ohlc else None
        low = _decimal(row.get("Low"), "Low", non_negative=True) if has_ohlc else None
        if has_ohlc and (not low <= min(open_, high, value) or max(open_, low, value) > high):
            raise IndexContractError("INVALID_OHLC", "TPEx OHLC values violate high/low bounds")
        previous_close = value - change if has_ohlc else None
        change_pct = (
            change / previous_close * Decimal("100")
            if previous_close is not None and previous_close > 0
            else None
        )
        metadata = _source_metadata("TWO")
        return MarketIndexResult(
            market="TWO",
            index_identity=metadata["index_identity"],
            display_name=metadata["display_name"],
            trading_date=trading_date,
            value=value,
            open=open_,
            high=high,
            low=low,
            previous_close=previous_close,
            change=change,
            change_pct=change_pct,
            source_provider=metadata["source_provider"],
            source_identity=metadata["source_identity"],
            source_dataset=metadata["source_dataset"],
            source_endpoint=metadata["source_endpoint"],
            source_field_path=metadata["source_field_path"],
            raw_provider_date=raw_date,
            retrieved_at=retrieved_at,
            as_of=as_of,
            data_status=IndexDataStatus.AVAILABLE,
            quality_status=(
                "SOURCE_FIELDS_VALID_OHLC_BACKEND_PREVIOUS_CLOSE_DERIVED"
                if has_ohlc
                else "SOURCE_FIELDS_VALID_PREVIOUS_CLOSE_DERIVATION_BLOCKED"
            ),
            source_publication=SOURCE_PUBLICATION_DAILY,
            finality=FINALITY_NOT_EXPLICIT,
            correction_evidence=CORRECTION_EVIDENCE,
            lineage=metadata["lineage"],
            adapter_version=metadata["adapter_version"],
            response_content_hash=content_hash,
        )
    except IndexContractError as exc:
        return _unavailable(
            "TWO",
            retrieved_at=retrieved_at,
            as_of=as_of,
            reason=exc.code,
            raw_provider_date=raw_date,
            response_content_hash=content_hash,
        )


def parse_tpex_index_crosscheck(payload: object) -> tuple[TpexIndexCrossCheck, ...]:
    """Normalize TPEx's Gregorian-date historical endpoint for cross-checks only."""

    content_hash = _content_hash(payload)
    rows = _rows(payload, wrapper="value") if isinstance(payload, Mapping) else _rows(payload)
    points: list[TpexIndexCrossCheck] = []
    for row in rows:
        raw_date = str(row.get("Date", ""))
        try:
            points.append(
                TpexIndexCrossCheck(
                    raw_provider_date=raw_date,
                    trading_date=_gregorian_date(raw_date, "Date"),
                    value=_decimal(row.get("Close"), "Close", non_negative=True),
                    change=_decimal(row.get("Change"), "Change"),
                    data_status=IndexDataStatus.AVAILABLE,
                    status_reason=None,
                    response_content_hash=content_hash,
                )
            )
        except IndexContractError as exc:
            points.append(
                TpexIndexCrossCheck(
                    raw_provider_date=raw_date,
                    trading_date=None,
                    value=None,
                    change=None,
                    data_status=IndexDataStatus.UNAVAILABLE,
                    status_reason=exc.code,
                    response_content_hash=content_hash,
                )
            )
    return tuple(points)


def _merge_twse_index_ohlc(
    close_fact: MarketIndexResult,
    ohlc_fact: MarketIndexResult,
) -> MarketIndexResult:
    """Join TWSE's close/change report with its official OHLC report."""

    if close_fact.data_status is not IndexDataStatus.AVAILABLE:
        return close_fact
    if (
        ohlc_fact.data_status is not IndexDataStatus.AVAILABLE
        or ohlc_fact.trading_date != close_fact.trading_date
    ):
        return replace(
            close_fact,
            quality_status="SOURCE_CLOSE_VALID_OHLC_UNAVAILABLE",
            status_reason=ohlc_fact.status_reason or "OHLC_SOURCE_UNAVAILABLE",
        )
    combined_hash = hashlib.sha256(
        f"{close_fact.response_content_hash or ''}:{ohlc_fact.response_content_hash or ''}".encode()
    ).hexdigest()
    return replace(
        close_fact,
        open=ohlc_fact.open,
        high=ohlc_fact.high,
        low=ohlc_fact.low,
        source_dataset=f"{TWSE_MARKET_INDEX_DATASET}+{TWSE_MARKET_INDEX_OHLC_DATASET}",
        source_endpoint=f"{TWSE_MARKET_INDEX_ENDPOINT};{TWSE_MARKET_INDEX_OHLC_ENDPOINT}",
        source_field_path=f"{TWSE_INDEX_VALUE_PATH};{TWSE_INDEX_OHLC_VALUE_PATH}",
        quality_status="SOURCE_FIELDS_VALID_OHLC_AND_CLOSE",
        lineage=(
            "TWSE -> target-date afterTrading/MI_INDEX + indicesReport.MI_5MINS_HIST "
            "-> TAIEX close/change and OHLC rows -> market index contract"
        ),
        response_content_hash=combined_hash,
    )


def fetch_official_market_indexes(
    *,
    target_date: date,
    retrieved_at: datetime,
    as_of: datetime,
    transport: Callable[[str, float], bytes],
    timeout: float = 30.0,
) -> tuple[MarketIndexResult, ...]:
    """Fetch and validate both official broad-market index facts.

    Transport and date mismatches become explicit unavailable facts. A missing
    aggregate never falls back to constituent prices or Preview data.
    """

    results: list[MarketIndexResult] = []

    try:
        target_endpoint = f"{TWSE_MARKET_INDEX_ENDPOINT}?date={target_date:%Y%m%d}&response=json"
        close_payload = json.loads(transport(target_endpoint, timeout).decode("utf-8"))
        close_fact = parse_twse_target_date_market_index(
            close_payload,
            target_date=target_date,
            retrieved_at=retrieved_at,
            as_of=as_of,
        )
    except Exception:
        close_fact = unavailable_market_index(
            "TPE", retrieved_at=retrieved_at, as_of=as_of, reason="PROVIDER_REQUEST_FAILED"
        )

    try:
        ohlc_endpoint = f"{TWSE_MARKET_INDEX_OHLC_ENDPOINT}?date={target_date:%Y%m%d}&response=json"
        ohlc_payload = json.loads(transport(ohlc_endpoint, timeout).decode("utf-8"))
        ohlc_fact = parse_twse_market_index_ohlc(
            ohlc_payload,
            retrieved_at=retrieved_at,
            as_of=as_of,
            target_date=target_date,
        )
    except Exception:
        ohlc_fact = unavailable_market_index(
            "TPE", retrieved_at=retrieved_at, as_of=as_of, reason="OHLC_PROVIDER_REQUEST_FAILED"
        )
    results.append(_merge_twse_index_ohlc(close_fact, ohlc_fact))

    try:
        payload = json.loads(transport(TPEX_MARKET_INDEX_ENDPOINT, timeout).decode("utf-8"))
        result = parse_tpex_market_index(
            payload,
            retrieved_at=retrieved_at,
            as_of=as_of,
            target_date=target_date,
        )
        if result.trading_date != target_date and result.data_status is IndexDataStatus.AVAILABLE:
            result = unavailable_market_index(
                "TWO", retrieved_at=retrieved_at, as_of=as_of, reason="PROVIDER_DATE_MISMATCH"
            )
    except Exception:
        result = unavailable_market_index(
            "TWO", retrieved_at=retrieved_at, as_of=as_of, reason="PROVIDER_REQUEST_FAILED"
        )
    results.append(result)
    return tuple(results)


__all__ = [
    "CORRECTION_EVIDENCE",
    "FINALITY_NOT_EXPLICIT",
    "SOURCE_PUBLICATION_DAILY",
    "TAIPEI",
    "TPEX_INDEX_CHANGE_FIELD",
    "TPEX_INDEX_CROSSCHECK_DATASET",
    "TPEX_INDEX_CROSSCHECK_ENDPOINT",
    "TPEX_INDEX_DATE_FIELD",
    "TPEX_INDEX_OHLC_FIELDS",
    "TPEX_INDEX_OHLC_VALUE_PATH",
    "TPEX_INDEX_VALUE_FIELD",
    "TPEX_INDEX_VALUE_PATH",
    "TPEX_MARKET_AGGREGATE_ADAPTER_VERSION",
    "TPEX_MARKET_AGGREGATE_SOURCE_IDENTITY",
    "TPEX_MARKET_INDEX_DATASET",
    "TPEX_MARKET_INDEX_DISPLAY_NAME",
    "TPEX_MARKET_INDEX_ENDPOINT",
    "TPEX_MARKET_INDEX_IDENTITY",
    "TWSE_INDEX_CHANGE_FIELD",
    "TWSE_INDEX_CHANGE_PCT_FIELD",
    "TWSE_INDEX_DATE_FIELD",
    "TWSE_INDEX_OHLC_FIELDS",
    "TWSE_INDEX_OHLC_VALUE_PATH",
    "TWSE_INDEX_SIGN_FIELD",
    "TWSE_INDEX_VALUE_FIELD",
    "TWSE_INDEX_VALUE_PATH",
    "TWSE_MARKET_AGGREGATE_ADAPTER_VERSION",
    "TWSE_MARKET_AGGREGATE_SOURCE_IDENTITY",
    "TWSE_MARKET_INDEX_ADAPTER_VERSION",
    "TWSE_MARKET_INDEX_DATASET",
    "TWSE_MARKET_INDEX_DISPLAY_NAME",
    "TWSE_MARKET_INDEX_ENDPOINT",
    "TWSE_MARKET_INDEX_IDENTITY",
    "TWSE_MARKET_INDEX_OHLC_DATASET",
    "TWSE_MARKET_INDEX_OHLC_ENDPOINT",
    "TWSE_MARKET_INDEX_RAW_NAME",
    "IndexContractError",
    "IndexDataStatus",
    "MarketIndexResult",
    "TpexIndexCrossCheck",
    "fetch_official_market_indexes",
    "parse_tpex_index_crosscheck",
    "parse_tpex_market_index",
    "parse_twse_market_index",
    "parse_twse_market_index_ohlc",
    "parse_twse_target_date_market_index",
    "unavailable_market_index",
]
