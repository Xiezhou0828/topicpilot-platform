"""FUND-B stock-level institutional-flow contracts and official adapters.

This module owns deterministic facts and evidence only.  It deliberately does
not assign a strength score, recommendation, ranking, or strategy meaning.
The canonical unit is shares because both selected exchange datasets publish
per-security institutional activity as share counts.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any, Final
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

TAIPEI: Final[str] = "Asia/Taipei"
STOCK_FLOW_UNIT: Final[str] = "SHARES"
STOCK_FLOW_SCALE: Final[int] = 0

TWSE_STOCK_FLOW_SOURCE_IDENTITY: Final = "TWSE_OFFICIAL_STOCK_INSTITUTIONAL_FLOW"
TWSE_STOCK_FLOW_ADAPTER_VERSION: Final = "twse-official-stock-institutional-flow.v1"
TWSE_STOCK_FLOW_DATASET: Final = "fund.T86"
TWSE_STOCK_FLOW_ENDPOINT: Final = "https://www.twse.com.tw/rwd/zh/fund/T86"

TPEX_STOCK_FLOW_SOURCE_IDENTITY: Final = "TPEX_OFFICIAL_STOCK_INSTITUTIONAL_FLOW"
TPEX_STOCK_FLOW_ADAPTER_VERSION: Final = "tpex-official-stock-institutional-flow.v1"
TPEX_STOCK_FLOW_DATASET: Final = "tpex_3insti_daily_trading"
TPEX_STOCK_FLOW_ENDPOINT: Final = "https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading"

_MISSING_MARKERS: Final = {"", "-", "--", "---", "N/A", "NULL", "NONE"}
_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_WHITESPACE_RE: Final = re.compile(r"\s+")

Transport = Callable[[str, float], bytes]


class StockFlowStatus(StrEnum):
    """Machine-readable availability and quality states."""

    OK = "OK"
    NO_DATA = "NO_DATA"
    NOT_TRADING_DAY = "NOT_TRADING_DAY"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    AUTH_ERROR = "AUTH_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    MAPPING_ERROR = "MAPPING_ERROR"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class StockFlowFreshness(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class StockFlowContractError(ValueError):
    """Raised when an official payload cannot satisfy the formal contract."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class StockFlowLeg:
    buy: Decimal
    sell: Decimal
    net: Decimal
    unit: str = STOCK_FLOW_UNIT
    scale: int = STOCK_FLOW_SCALE

    def to_dict(self) -> dict[str, Any]:
        return {
            "buy": _json_number(self.buy),
            "sell": _json_number(self.sell),
            "net": _json_number(self.net),
            "unit": self.unit,
            "scale": self.scale,
        }


@dataclass(frozen=True)
class StockInstitutionalFlowFact:
    """One stock/session observation with source-shaped subcategory evidence."""

    market: str
    instrument_code: str
    trading_date: date
    foreign: StockFlowLeg
    investment_trust: StockFlowLeg
    dealer: StockFlowLeg
    total: StockFlowLeg
    source_provider: str
    source_identity: str
    source_dataset: str
    source_endpoint: str
    adapter_version: str
    source_as_of: datetime | None
    retrieved_at: datetime
    status: StockFlowStatus = StockFlowStatus.OK
    freshness: StockFlowFreshness = StockFlowFreshness.UNKNOWN
    status_reason: str | None = None
    lineage: str = ""
    response_content_hash: str | None = None
    raw_payload: object | None = None
    foreign_dealer: StockFlowLeg | None = None
    dealer_self: StockFlowLeg | None = None
    dealer_hedge: StockFlowLeg | None = None
    instrument_id: str | None = None

    @property
    def is_available(self) -> bool:
        return self.status is StockFlowStatus.OK

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrumentId": self.instrument_id,
            "instrumentCode": self.instrument_code,
            "market": self.market,
            "tradingDate": self.trading_date.isoformat(),
            "foreign": self.foreign.to_dict(),
            "investmentTrust": self.investment_trust.to_dict(),
            "dealer": self.dealer.to_dict(),
            "total": self.total.to_dict(),
            "foreignDealer": self.foreign_dealer.to_dict() if self.foreign_dealer else None,
            "dealerSelf": self.dealer_self.to_dict() if self.dealer_self else None,
            "dealerHedge": self.dealer_hedge.to_dict() if self.dealer_hedge else None,
            "sourceProvider": self.source_provider,
            "sourceIdentity": self.source_identity,
            "sourceDataset": self.source_dataset,
            "sourceEndpoint": self.source_endpoint,
            "adapterVersion": self.adapter_version,
            "sourceAsOf": self.source_as_of,
            "retrievedAt": self.retrieved_at,
            "status": self.status.value,
            "freshness": self.freshness.value,
            "statusReason": self.status_reason,
            "lineage": self.lineage,
            "responseContentHash": self.response_content_hash,
            "unit": STOCK_FLOW_UNIT,
            "scale": STOCK_FLOW_SCALE,
        }


@dataclass(frozen=True)
class StockInstitutionalFlowBatch:
    market: str
    requested_date: date
    facts: tuple[StockInstitutionalFlowFact, ...]
    status: StockFlowStatus
    status_reason: str | None
    source_date: date | None
    source_as_of: datetime | None
    source_identity: str
    source_dataset: str
    source_endpoint: str
    adapter_version: str
    response_content_hash: str | None = None
    mapping_errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class StockPriceObservation:
    trading_date: date
    close: Decimal | None
    volume: Decimal | None
    source_code: str | None
    quality_state: str | None


@dataclass(frozen=True)
class StockFlowWindow:
    required_sessions: int
    observed_sessions: int
    complete: bool
    foreign_net: Decimal | None
    investment_trust_net: Decimal | None
    dealer_net: Decimal | None
    total_net: Decimal | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "requiredSessions": self.required_sessions,
            "observedSessions": self.observed_sessions,
            "complete": self.complete,
            "foreignNet": _json_number(self.foreign_net),
            "investmentTrustNet": _json_number(self.investment_trust_net),
            "dealerNet": _json_number(self.dealer_net),
            "totalNet": _json_number(self.total_net),
            "unit": STOCK_FLOW_UNIT,
            "scale": STOCK_FLOW_SCALE,
        }


@dataclass(frozen=True)
class StockFlowStreak:
    direction: str
    sessions: int
    status: str = "OK"

    def to_dict(self) -> dict[str, Any]:
        return {"direction": self.direction, "sessions": self.sessions, "status": self.status}


@dataclass(frozen=True)
class StockPriceFlowContext:
    state: str
    price_direction: str
    flow_direction: str
    price_change: Decimal | None
    institutional_net: Decimal | None
    price_basis: str = "RAW_OBSERVED"
    status: str = "OK"

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "priceDirection": self.price_direction,
            "flowDirection": self.flow_direction,
            "priceChange": _json_number(self.price_change),
            "institutionalNet": _json_number(self.institutional_net),
            "priceBasis": self.price_basis,
            "status": self.status,
        }


@dataclass(frozen=True)
class StockFlowReversal:
    state: str
    current_direction: str
    prior_direction: str
    status: str = "OK"

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "currentDirection": self.current_direction,
            "priorDirection": self.prior_direction,
            "status": self.status,
        }


@dataclass(frozen=True)
class StockFlowDivergence:
    state: str
    condition: str
    status: str = "OK"

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state, "condition": self.condition, "status": self.status}


@dataclass(frozen=True)
class StockFlowUnusual:
    state: str = "POLICY_DECISION_REQUIRED"
    metric: Decimal | None = None
    status: str = "DEFERRED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "metric": _json_number(self.metric),
            "status": self.status,
            "reason": "NO_OWNER_APPROVED_ABNORMAL_FLOW_FORMULA",
        }


@dataclass(frozen=True)
class StockFlowLiquidityRelative:
    state: str
    ratio: Decimal | None
    numerator: Decimal | None
    denominator: Decimal | None
    numerator_unit: str = STOCK_FLOW_UNIT
    denominator_unit: str = STOCK_FLOW_UNIT
    status: str = "OK"

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "ratio": _json_number(self.ratio),
            "institutionalNet": _json_number(self.numerator),
            "dailyVolume": _json_number(self.denominator),
            "numeratorUnit": self.numerator_unit,
            "denominatorUnit": self.denominator_unit,
            "status": self.status,
        }


@dataclass(frozen=True)
class StockInstitutionalFlowFeatures:
    market: str
    instrument_code: str
    instrument_id: str | None
    requested_as_of: date
    as_of_date: date | None
    latest_available_date: date | None
    status: StockFlowStatus
    freshness: StockFlowFreshness
    status_reason: str | None
    current: StockInstitutionalFlowFact | None
    sessions: tuple[StockInstitutionalFlowFact, ...]
    one_day: StockFlowWindow
    five_day: StockFlowWindow
    ten_day: StockFlowWindow
    twenty_day: StockFlowWindow
    streaks: Mapping[str, StockFlowStreak]
    reversal: StockFlowReversal
    price_flow: StockPriceFlowContext
    divergence: StockFlowDivergence
    unusual_flow: StockFlowUnusual
    liquidity_relative: StockFlowLiquidityRelative

    def to_dict(self) -> dict[str, Any]:
        source_fact = self.current or (self.sessions[0] if self.sessions else None)
        source_as_of = source_fact.source_as_of if source_fact else None
        return {
            "contractVersion": "fund-b.stock-institutional-flow.v1",
            "instrumentId": self.instrument_id,
            "instrumentCode": self.instrument_code,
            "market": self.market,
            "requestedAsOf": self.requested_as_of,
            "asOfDate": self.as_of_date,
            "latestAvailableDate": self.latest_available_date,
            "status": self.status.value,
            "freshness": self.freshness.value,
            "statusReason": self.status_reason,
            "today": self.current.to_dict() if self.current else None,
            "sessions": [item.to_dict() for item in self.sessions],
            "windows": {
                "oneDay": self.one_day.to_dict(),
                "fiveDay": self.five_day.to_dict(),
                "tenDay": self.ten_day.to_dict(),
                "twentyDay": self.twenty_day.to_dict(),
            },
            "streaks": {key: value.to_dict() for key, value in self.streaks.items()},
            "reversal": self.reversal.to_dict(),
            "priceFlow": self.price_flow.to_dict(),
            "divergence": self.divergence.to_dict(),
            "unusualFlow": self.unusual_flow.to_dict(),
            "liquidityRelative": self.liquidity_relative.to_dict(),
            "sourceAsOf": source_as_of,
            "source": (
                {
                    "provider": source_fact.source_provider,
                    "identity": source_fact.source_identity,
                    "dataset": source_fact.source_dataset,
                    "endpoint": source_fact.source_endpoint,
                    "adapterVersion": source_fact.adapter_version,
                }
                if source_fact
                else None
            ),
            "unit": STOCK_FLOW_UNIT,
            "scale": STOCK_FLOW_SCALE,
        }


def _json_number(value: Decimal | None) -> int | float | None:
    if value is None:
        return None
    return int(value) if value == value.to_integral_value() else float(value)


def _content_hash(payload: object) -> str:
    try:
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        text = repr(payload)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_metadata(market: str) -> dict[str, str]:
    if market == "TPE":
        return {
            "provider": "TWSE",
            "identity": TWSE_STOCK_FLOW_SOURCE_IDENTITY,
            "dataset": TWSE_STOCK_FLOW_DATASET,
            "endpoint": TWSE_STOCK_FLOW_ENDPOINT,
            "adapter": TWSE_STOCK_FLOW_ADAPTER_VERSION,
            "lineage": "TWSE -> fund.T86 -> stock-level shares -> FUND-B",
        }
    if market == "TWO":
        return {
            "provider": "TPEx",
            "identity": TPEX_STOCK_FLOW_SOURCE_IDENTITY,
            "dataset": TPEX_STOCK_FLOW_DATASET,
            "endpoint": TPEX_STOCK_FLOW_ENDPOINT,
            "adapter": TPEX_STOCK_FLOW_ADAPTER_VERSION,
            "lineage": "TPEx -> tpex_3insti_daily_trading -> stock-level shares -> FUND-B",
        }
    raise StockFlowContractError("INVALID_MARKET", f"unsupported market: {market}")


def _normal_key(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    return _WHITESPACE_RE.sub("", normalized).lower()


def _decimal(value: object, field: str, *, non_negative: bool = False) -> Decimal:
    if value is None or str(value).strip().upper() in _MISSING_MARKERS:
        raise StockFlowContractError(f"MISSING_{field.upper()}", f"{field} is required")
    try:
        parsed = Decimal(str(value).strip().replace(",", "").replace("+", "", 1))
    except (InvalidOperation, ValueError) as exc:
        raise StockFlowContractError("INVALID_NUMBER", f"{field} is invalid") from exc
    if not parsed.is_finite() or (non_negative and parsed < 0):
        raise StockFlowContractError("INVALID_NUMBER", f"{field} is invalid")
    return parsed


def _date(value: object, field: str) -> date:
    raw = str(value or "").strip().replace("/", "").replace("-", "")
    if len(raw) == 7 and raw.isdigit():
        raw = f"{int(raw[:3]) + 1911:04d}{raw[3:]}"
    if len(raw) != 8 or not raw.isdigit():
        raise StockFlowContractError("INVALID_DATE", f"{field} is invalid")
    try:
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:]))
    except ValueError as exc:
        raise StockFlowContractError("INVALID_DATE", f"{field} is invalid") from exc


def _leg(buy: object, sell: object, net: object, field: str) -> StockFlowLeg:
    parsed_buy = _decimal(buy, f"{field}_buy", non_negative=True)
    parsed_sell = _decimal(sell, f"{field}_sell", non_negative=True)
    parsed_net = _decimal(net, f"{field}_net")
    if parsed_net != parsed_buy - parsed_sell:
        raise StockFlowContractError("NET_MISMATCH", f"{field} net does not equal buy minus sell")
    return StockFlowLeg(parsed_buy, parsed_sell, parsed_net)


def _sum_legs(*legs: StockFlowLeg) -> StockFlowLeg:
    return StockFlowLeg(
        sum((leg.buy for leg in legs), Decimal(0)),
        sum((leg.sell for leg in legs), Decimal(0)),
        sum((leg.net for leg in legs), Decimal(0)),
    )


def _base_fact(
    *,
    market: str,
    instrument_code: str,
    trading_date: date,
    foreign: StockFlowLeg,
    investment_trust: StockFlowLeg,
    dealer: StockFlowLeg,
    total: StockFlowLeg,
    retrieved_at: datetime,
    source_as_of: datetime | None,
    metadata: Mapping[str, str],
    response_content_hash: str,
    raw_payload: object,
    foreign_dealer: StockFlowLeg | None = None,
    dealer_self: StockFlowLeg | None = None,
    dealer_hedge: StockFlowLeg | None = None,
) -> StockInstitutionalFlowFact:
    if total != _sum_legs(foreign, investment_trust, dealer):
        raise StockFlowContractError(
            "TOTAL_MISMATCH", "total does not reconcile with normalized legs"
        )
    return StockInstitutionalFlowFact(
        market=market,
        instrument_code=instrument_code,
        trading_date=trading_date,
        foreign=foreign,
        investment_trust=investment_trust,
        dealer=dealer,
        total=total,
        source_provider=metadata["provider"],
        source_identity=metadata["identity"],
        source_dataset=metadata["dataset"],
        source_endpoint=metadata["endpoint"],
        adapter_version=metadata["adapter"],
        source_as_of=source_as_of,
        retrieved_at=retrieved_at,
        freshness=StockFlowFreshness.UNKNOWN,
        lineage=metadata["lineage"],
        response_content_hash=response_content_hash,
        raw_payload=raw_payload,
        foreign_dealer=foreign_dealer,
        dealer_self=dealer_self,
        dealer_hedge=dealer_hedge,
    )


def _payload_rows(payload: object) -> tuple[object, list[object]]:
    if isinstance(payload, list):
        return payload, payload
    if not isinstance(payload, Mapping):
        raise StockFlowContractError("SCHEMA_ERROR", "provider payload must be an object or array")
    stat = str(payload.get("stat", "")).upper()
    if stat and stat != "OK":
        raise StockFlowContractError("NO_DATA", f"provider status is {stat}")
    rows = payload.get("data", payload.get("value"))
    if not isinstance(rows, list):
        raise StockFlowContractError("SCHEMA_ERROR", "provider data must be an array")
    return payload, rows


def parse_twse_stock_institutional_flow(
    payload: object,
    *,
    retrieved_at: datetime,
    target_date: date | None = None,
) -> tuple[StockInstitutionalFlowFact, ...]:
    """Parse TWSE T86; normalized foreign excludes foreign dealers."""

    payload_obj, rows = _payload_rows(payload)
    if not isinstance(payload_obj, Mapping):
        raise StockFlowContractError("SCHEMA_ERROR", "TWSE payload is invalid")
    trading_date = _date(payload_obj.get("date"), "date")
    if target_date is not None and trading_date != target_date:
        raise StockFlowContractError("SOURCE_DATE_MISMATCH", "TWSE date differs from request")
    fields = payload_obj.get("fields")
    if not isinstance(fields, list) or not fields:
        raise StockFlowContractError("SCHEMA_ERROR", "TWSE fields are missing")
    required = {
        "code": "證券代號",
        "foreign_buy": "外陸資買進股數(不含外資自營商)",
        "foreign_sell": "外陸資賣出股數(不含外資自營商)",
        "foreign_net": "外陸資買賣超股數(不含外資自營商)",
        "foreign_dealer_buy": "外資自營商買進股數",
        "foreign_dealer_sell": "外資自營商賣出股數",
        "foreign_dealer_net": "外資自營商買賣超股數",
        "trust_buy": "投信買進股數",
        "trust_sell": "投信賣出股數",
        "trust_net": "投信買賣超股數",
        "dealer_self_buy": "自營商買進股數(自行買賣)",
        "dealer_self_sell": "自營商賣出股數(自行買賣)",
        "dealer_self_net": "自營商買賣超股數(自行買賣)",
        "dealer_hedge_buy": "自營商買進股數(避險)",
        "dealer_hedge_sell": "自營商賣出股數(避險)",
        "dealer_hedge_net": "自營商買賣超股數(避險)",
        "dealer_net": "自營商買賣超股數",
        "total_net": "三大法人買賣超股數",
    }
    positions = {_normal_key(value): index for index, value in enumerate(fields)}
    missing = [name for name, label in required.items() if _normal_key(label) not in positions]
    if missing:
        raise StockFlowContractError("SCHEMA_ERROR", f"TWSE fields missing: {','.join(missing)}")
    metadata = _source_metadata("TPE")
    content_hash = _content_hash(payload)
    facts: list[StockInstitutionalFlowFact] = []
    seen: set[str] = set()
    for raw_row in rows:
        if not isinstance(raw_row, list) or len(raw_row) < len(fields):
            raise StockFlowContractError("SCHEMA_ERROR", "TWSE row is incomplete")
        code = str(raw_row[positions[_normal_key(required["code"])]]).strip()
        if not code or not _IDENTIFIER_RE.fullmatch(code):
            continue
        if code in seen:
            raise StockFlowContractError("SCHEMA_ERROR", f"duplicate TWSE instrument row: {code}")
        seen.add(code)
        values = {name: raw_row[positions[_normal_key(label)]] for name, label in required.items()}

        foreign = _leg(
            values["foreign_buy"], values["foreign_sell"], values["foreign_net"], "foreign"
        )
        foreign_dealer = _leg(
            values["foreign_dealer_buy"],
            values["foreign_dealer_sell"],
            values["foreign_dealer_net"],
            "foreign_dealer",
        )
        trust = _leg(
            values["trust_buy"], values["trust_sell"], values["trust_net"], "investment_trust"
        )
        dealer_self = _leg(
            values["dealer_self_buy"],
            values["dealer_self_sell"],
            values["dealer_self_net"],
            "dealer_self",
        )
        dealer_hedge = _leg(
            values["dealer_hedge_buy"],
            values["dealer_hedge_sell"],
            values["dealer_hedge_net"],
            "dealer_hedge",
        )
        dealer = _sum_legs(foreign_dealer, dealer_self, dealer_hedge)
        if dealer.net != _decimal(values["dealer_net"], "dealer_net"):
            raise StockFlowContractError("NET_MISMATCH", f"dealer total mismatch for {code}")
        total = _sum_legs(
            foreign,
            trust,
            dealer,
        )
        if total.net != _decimal(values["total_net"], "total_net"):
            raise StockFlowContractError("TOTAL_MISMATCH", f"TWSE total mismatch for {code}")
        facts.append(
            _base_fact(
                market="TPE",
                instrument_code=code,
                trading_date=trading_date,
                foreign=foreign,
                investment_trust=trust,
                dealer=dealer,
                total=total,
                retrieved_at=retrieved_at,
                source_as_of=retrieved_at,
                metadata=metadata,
                response_content_hash=content_hash,
                raw_payload=raw_row,
                foreign_dealer=foreign_dealer,
                dealer_self=dealer_self,
                dealer_hedge=dealer_hedge,
            )
        )
    return tuple(facts)


def _tpex_value(row: Mapping[str, Any], *aliases: str) -> object:
    indexed = {_normal_key(key): value for key, value in row.items()}
    for alias in aliases:
        key = _normal_key(alias)
        if key in indexed:
            return indexed[key]
    raise StockFlowContractError("SCHEMA_ERROR", f"TPEx field missing: {aliases[0]}")


def parse_tpex_stock_institutional_flow(
    payload: object,
    *,
    retrieved_at: datetime,
    target_date: date | None = None,
) -> tuple[StockInstitutionalFlowFact, ...]:
    """Parse TPEx ``tpex_3insti_daily_trading``.

    TPEx's normalized total is foreign/non-dealer + trust + dealers.  Foreign
    dealer sub-fields are retained as source evidence but are not silently
    added to the normalized dealer leg.
    """

    payload_obj, rows = _payload_rows(payload)
    if isinstance(payload_obj, Mapping) and payload_obj.get("stat"):
        raise StockFlowContractError("NO_DATA", str(payload_obj.get("stat")))
    if not rows or not all(isinstance(row, Mapping) for row in rows):
        raise StockFlowContractError("SCHEMA_ERROR", "TPEx rows are missing or invalid")
    typed_rows = [row for row in rows if isinstance(row, Mapping)]
    source_date = _date(_tpex_value(typed_rows[0], "Date"), "Date")
    if any(_date(_tpex_value(row, "Date"), "Date") != source_date for row in typed_rows):
        raise StockFlowContractError("SCHEMA_ERROR", "TPEx rows contain mixed dates")
    metadata = _source_metadata("TWO")
    content_hash = _content_hash(payload)
    foreign_ex_dealer_buy = (
        "Foreign Investors include Mainland Area Investors (Foreign Dealers excluded)-Total Buy"
    )
    foreign_ex_dealer_sell = (
        "Foreign Investors include Mainland Area Investors (Foreign Dealers excluded)-Total Sell"
    )
    foreign_ex_dealer_net = (
        "Foreign Investors include Mainland Area Investors (Foreign Dealers excluded)-Difference"
    )
    facts: list[StockInstitutionalFlowFact] = []
    seen: set[str] = set()
    for row in typed_rows:
        code = str(_tpex_value(row, "SecuritiesCompanyCode")).strip()
        if not code or not _IDENTIFIER_RE.fullmatch(code):
            continue
        if code in seen:
            raise StockFlowContractError("SCHEMA_ERROR", f"duplicate TPEx instrument row: {code}")
        seen.add(code)
        foreign = _leg(
            _tpex_value(
                row,
                foreign_ex_dealer_buy,
            ),
            _tpex_value(
                row,
                foreign_ex_dealer_sell,
            ),
            _tpex_value(
                row,
                foreign_ex_dealer_net,
            ),
            "foreign",
        )
        foreign_dealer = _leg(
            _tpex_value(row, "Foreign Dealers-Total Buy"),
            _tpex_value(row, "Foreign Dealers-TotalSell", "Foreign Dealers-Total Sell"),
            _tpex_value(row, "ForeignDealers-Difference"),
            "foreign_dealer",
        )
        trust = _leg(
            _tpex_value(row, "SecuritiesInvestmentTrustCompanies-TotalBuy"),
            _tpex_value(row, "SecuritiesInvestmentTrustCompanies-TotalSell"),
            _tpex_value(row, "SecuritiesInvestmentTrustCompanies-Difference"),
            "investment_trust",
        )
        dealer = _leg(
            _tpex_value(row, "Dealers-TotalBuy"),
            _tpex_value(row, "Dealers-TotalSell", "Dealers -TotalSell"),
            _tpex_value(row, "Dealers-Difference"),
            "dealer",
        )
        total = _sum_legs(foreign, trust, dealer)
        if total.net != _decimal(_tpex_value(row, "TotalDifference"), "total_net"):
            raise StockFlowContractError("TOTAL_MISMATCH", f"TPEx total mismatch for {code}")
        facts.append(
            _base_fact(
                market="TWO",
                instrument_code=code,
                trading_date=source_date,
                foreign=foreign,
                investment_trust=trust,
                dealer=dealer,
                total=total,
                retrieved_at=retrieved_at,
                source_as_of=retrieved_at,
                metadata=metadata,
                response_content_hash=content_hash,
                raw_payload=dict(row),
                foreign_dealer=foreign_dealer,
            )
        )
    return tuple(facts)


def resolve_freshness(
    *, requested_date: date, source_date: date | None, status: StockFlowStatus
) -> StockFlowFreshness:
    if status is not StockFlowStatus.OK or source_date is None:
        return StockFlowFreshness.UNKNOWN
    return StockFlowFreshness.CURRENT if source_date == requested_date else StockFlowFreshness.STALE


def _status_for_exception(exc: Exception) -> StockFlowStatus:
    if isinstance(exc, StockFlowContractError):
        return {
            "NO_DATA": StockFlowStatus.NO_DATA,
            "SOURCE_DATE_MISMATCH": StockFlowStatus.STALE,
            "SCHEMA_ERROR": StockFlowStatus.SCHEMA_ERROR,
        }.get(exc.code, StockFlowStatus.UNKNOWN)
    if isinstance(exc, HTTPError):
        if exc.code == 401 or exc.code == 403:
            return StockFlowStatus.AUTH_ERROR
        if exc.code == 429:
            return StockFlowStatus.RATE_LIMITED
    if isinstance(exc, (HTTPError, URLError, TimeoutError, OSError)):
        return StockFlowStatus.PROVIDER_UNAVAILABLE
    return StockFlowStatus.UNKNOWN


def _read_url(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": "TopicPilot-V2/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _default_clock() -> datetime:
    return datetime.now(ZoneInfo(TAIPEI))


def _fetch_json(transport: Transport, url: str, timeout: float) -> object:
    try:
        raw = transport(url, timeout)
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise StockFlowContractError("SCHEMA_ERROR", "provider response is not JSON") from exc


class TwseStockInstitutionalFlowProvider:
    source_code = TWSE_STOCK_FLOW_SOURCE_IDENTITY
    adapter_version = TWSE_STOCK_FLOW_ADAPTER_VERSION

    def __init__(
        self,
        *,
        target_date: date,
        endpoint: str = TWSE_STOCK_FLOW_ENDPOINT,
        timeout: float = 30.0,
        transport: Transport = _read_url,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.target_date = target_date
        self.endpoint = endpoint
        self.timeout = timeout
        self.transport = transport
        self.clock = clock

    def fetch(self) -> StockInstitutionalFlowBatch:
        retrieved_at = self.clock()
        query = {
            "date": self.target_date.strftime("%Y%m%d"),
            "selectType": "ALL",
            "response": "json",
        }
        url = f"{self.endpoint}?{urlencode(query)}"
        metadata = _source_metadata("TPE")
        try:
            raw = self.transport(url, self.timeout)
            payload = json.loads(raw.decode("utf-8"))
            facts = parse_twse_stock_institutional_flow(
                payload, retrieved_at=retrieved_at, target_date=self.target_date
            )
            return StockInstitutionalFlowBatch(
                market="TPE",
                requested_date=self.target_date,
                facts=tuple(
                    replace(
                        item,
                        freshness=resolve_freshness(
                            requested_date=self.target_date,
                            source_date=item.trading_date,
                            status=item.status,
                        ),
                    )
                    for item in facts
                ),
                status=StockFlowStatus.OK if facts else StockFlowStatus.NO_DATA,
                status_reason=None if facts else "PROVIDER_RETURNED_NO_ROWS",
                source_date=facts[0].trading_date if facts else None,
                source_as_of=retrieved_at,
                source_identity=metadata["identity"],
                source_dataset=metadata["dataset"],
                source_endpoint=metadata["endpoint"],
                adapter_version=metadata["adapter"],
                response_content_hash=facts[0].response_content_hash
                if facts
                else _content_hash(payload),
            )
        except Exception as exc:
            status = _status_for_exception(exc)
            return StockInstitutionalFlowBatch(
                market="TPE",
                requested_date=self.target_date,
                facts=(),
                status=status,
                status_reason=str(exc),
                source_date=None,
                source_as_of=retrieved_at,
                source_identity=metadata["identity"],
                source_dataset=metadata["dataset"],
                source_endpoint=metadata["endpoint"],
                adapter_version=metadata["adapter"],
            )


class TpexStockInstitutionalFlowProvider:
    source_code = TPEX_STOCK_FLOW_SOURCE_IDENTITY
    adapter_version = TPEX_STOCK_FLOW_ADAPTER_VERSION

    def __init__(
        self,
        *,
        target_date: date,
        endpoint: str = TPEX_STOCK_FLOW_ENDPOINT,
        timeout: float = 30.0,
        transport: Transport = _read_url,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.target_date = target_date
        self.endpoint = endpoint
        self.timeout = timeout
        self.transport = transport
        self.clock = clock

    def fetch(self) -> StockInstitutionalFlowBatch:
        retrieved_at = self.clock()
        metadata = _source_metadata("TWO")
        try:
            payload = _fetch_json(self.transport, self.endpoint, self.timeout)
            facts = parse_tpex_stock_institutional_flow(payload, retrieved_at=retrieved_at)
            source_date = facts[0].trading_date if facts else None
            status = (
                StockFlowStatus.OK
                if facts and source_date == self.target_date
                else StockFlowStatus.STALE
            )
            facts = tuple(
                replace(
                    item,
                    freshness=resolve_freshness(
                        requested_date=self.target_date,
                        source_date=item.trading_date,
                        status=StockFlowStatus.OK,
                    ),
                )
                for item in facts
            )
            return StockInstitutionalFlowBatch(
                market="TWO",
                requested_date=self.target_date,
                facts=facts,
                status=status if facts else StockFlowStatus.NO_DATA,
                status_reason=None
                if source_date == self.target_date
                else "TPEx_OPENAPI_IS_CURRENT_SNAPSHOT_ONLY",
                source_date=source_date,
                source_as_of=retrieved_at,
                source_identity=metadata["identity"],
                source_dataset=metadata["dataset"],
                source_endpoint=metadata["endpoint"],
                adapter_version=metadata["adapter"],
                response_content_hash=facts[0].response_content_hash
                if facts
                else _content_hash(payload),
            )
        except Exception as exc:
            return StockInstitutionalFlowBatch(
                market="TWO",
                requested_date=self.target_date,
                facts=(),
                status=_status_for_exception(exc),
                status_reason=str(exc),
                source_date=None,
                source_as_of=retrieved_at,
                source_identity=metadata["identity"],
                source_dataset=metadata["dataset"],
                source_endpoint=metadata["endpoint"],
                adapter_version=metadata["adapter"],
            )


def map_provider_facts(
    facts: Sequence[StockInstitutionalFlowFact],
    canonical_instruments: Mapping[tuple[str, str], str],
) -> tuple[tuple[StockInstitutionalFlowFact, ...], tuple[str, ...]]:
    """Bind provider symbols to canonical market/instrument identities.

    Unknown mappings are returned as observable errors and never converted to
    an arbitrary symbol-only identity.
    """

    mapped: list[StockInstitutionalFlowFact] = []
    errors: list[str] = []
    for fact in facts:
        instrument_id = canonical_instruments.get((fact.market, fact.instrument_code))
        if instrument_id is None:
            errors.append(f"MAPPING_ERROR:{fact.market}:{fact.instrument_code}")
            continue
        mapped.append(fact.__class__(**{**fact.__dict__, "instrument_id": instrument_id}))
    return tuple(mapped), tuple(errors)


def expected_weekday_sessions(
    start_date: date, end_date: date, holidays: Sequence[date] = ()
) -> tuple[date, ...]:
    """Return newest-first weekday sessions excluding authoritative holidays."""

    holiday_set = set(holidays)
    cursor = end_date
    result: list[date] = []
    while cursor >= start_date:
        if cursor.weekday() < 5 and cursor not in holiday_set:
            result.append(cursor)
        cursor -= timedelta(days=1)
    return tuple(result)


def _direction(value: Decimal | None) -> str:
    if value is None:
        return "UNKNOWN"
    if value > 0:
        return "BUY"
    if value < 0:
        return "SELL"
    return "FLAT"


def _price_direction(value: Decimal | None) -> str:
    if value is None:
        return "UNKNOWN"
    if value > 0:
        return "UP"
    if value < 0:
        return "DOWN"
    return "FLAT"


def _net(fact: StockInstitutionalFlowFact | None, category: str) -> Decimal | None:
    if fact is None or not fact.is_available:
        return None
    return getattr(fact, category).net


def _window(
    rows: Sequence[StockInstitutionalFlowFact], required: int, expected_dates: Sequence[date] | None
) -> StockFlowWindow:
    if expected_dates is None:
        candidate = list(rows[:required])
    else:
        by_date = {row.trading_date: row for row in rows}
        candidate = [by_date.get(day) for day in expected_dates[:required]]
    available = [row for row in candidate if row is not None and row.is_available]
    complete = len(candidate) == required and len(available) == required
    return StockFlowWindow(
        required_sessions=required,
        observed_sessions=len(available),
        complete=complete,
        foreign_net=sum((_net(row, "foreign") or Decimal(0) for row in available), Decimal(0))
        if complete
        else None,
        investment_trust_net=sum(
            (_net(row, "investment_trust") or Decimal(0) for row in available), Decimal(0)
        )
        if complete
        else None,
        dealer_net=sum((_net(row, "dealer") or Decimal(0) for row in available), Decimal(0))
        if complete
        else None,
        total_net=sum((_net(row, "total") or Decimal(0) for row in available), Decimal(0))
        if complete
        else None,
    )


def _streak(
    rows: Sequence[StockInstitutionalFlowFact], category: str, expected_dates: Sequence[date] | None
) -> StockFlowStreak:
    if expected_dates is not None:
        by_date = {row.trading_date: row for row in rows}
        ordered = [by_date.get(day) for day in expected_dates]
        if not ordered or ordered[0] is None:
            return StockFlowStreak("UNKNOWN", 0, "UNAVAILABLE")
    else:
        ordered = list(rows)
    current = ordered[0]
    value = _net(current, category)
    if current is None or value is None:
        return StockFlowStreak("UNKNOWN", 0, "UNAVAILABLE")
    direction = _direction(value)
    if direction == "FLAT":
        return StockFlowStreak("FLAT", 0)
    count = 0
    for row in ordered:
        value = _net(row, category)
        if value is None or _direction(value) != direction:
            break
        count += 1
    return StockFlowStreak(direction, count)


def _price_flow(
    current: StockInstitutionalFlowFact | None,
    previous: StockInstitutionalFlowFact | None,
    prices: Mapping[date, StockPriceObservation],
) -> tuple[StockPriceFlowContext, StockFlowDivergence]:
    if current is None or previous is None:
        context = StockPriceFlowContext(
            "UNAVAILABLE", "UNKNOWN", "UNKNOWN", None, None, status="UNAVAILABLE"
        )
        return context, StockFlowDivergence("UNAVAILABLE", "MISSING_FLOW_SESSION", "UNAVAILABLE")
    current_price = prices.get(current.trading_date)
    prior_price = prices.get(previous.trading_date)
    net = current.total.net
    if (
        current_price is None
        or prior_price is None
        or current_price.close is None
        or prior_price.close is None
        or current_price.quality_state not in {None, "ACCEPTED"}
        or prior_price.quality_state not in {None, "ACCEPTED"}
    ):
        context = StockPriceFlowContext(
            "UNAVAILABLE", "UNKNOWN", _direction(net), None, net, status="UNAVAILABLE"
        )
        return context, StockFlowDivergence("UNAVAILABLE", "MISSING_CANONICAL_PRICE", "UNAVAILABLE")
    change = current_price.close - prior_price.close
    price_direction = _price_direction(change)
    flow_direction = _direction(net)
    state = (
        "PRICE_UP_FLOW_BUY"
        if price_direction == "UP" and flow_direction == "BUY"
        else "PRICE_UP_FLOW_SELL"
        if price_direction == "UP" and flow_direction == "SELL"
        else "PRICE_DOWN_FLOW_BUY"
        if price_direction == "DOWN" and flow_direction == "BUY"
        else "PRICE_DOWN_FLOW_SELL"
        if price_direction == "DOWN" and flow_direction == "SELL"
        else f"PRICE_FLAT_FLOW_{flow_direction}"
        if price_direction == "FLAT"
        else f"PRICE_{price_direction}_FLOW_FLAT"
        if flow_direction == "FLAT"
        else "PRICE_FLOW_NEUTRAL"
    )
    if price_direction == "UP" and flow_direction == "SELL":
        divergence = StockFlowDivergence("NEGATIVE_PRICE_FLOW_DIVERGENCE", state)
    elif price_direction == "DOWN" and flow_direction == "BUY":
        divergence = StockFlowDivergence("POSITIVE_PRICE_FLOW_DIVERGENCE", state)
    elif (price_direction == "UP" and flow_direction == "BUY") or (
        price_direction == "DOWN" and flow_direction == "SELL"
    ):
        divergence = StockFlowDivergence("CONFIRMING", state)
    else:
        divergence = StockFlowDivergence("NEUTRAL", state)
    return StockPriceFlowContext(state, price_direction, flow_direction, change, net), divergence


def _reversal(
    current: StockInstitutionalFlowFact | None, previous: StockInstitutionalFlowFact | None
) -> StockFlowReversal:
    if current is None or previous is None:
        return StockFlowReversal("UNAVAILABLE", "UNKNOWN", "UNKNOWN", "UNAVAILABLE")
    current_direction = _direction(current.total.net)
    prior_direction = _direction(previous.total.net)
    if current_direction == "BUY" and prior_direction == "SELL":
        state = "SELL_TO_BUY"
    elif current_direction == "SELL" and prior_direction == "BUY":
        state = "BUY_TO_SELL"
    else:
        state = "NONE"
    return StockFlowReversal(state, current_direction, prior_direction)


def build_stock_institutional_flow_features(
    facts: Sequence[StockInstitutionalFlowFact],
    *,
    market: str,
    instrument_code: str,
    requested_as_of: date,
    instrument_id: str | None = None,
    expected_sessions: Sequence[date] | None = None,
    prices: Mapping[date, StockPriceObservation] | None = None,
) -> StockInstitutionalFlowFeatures:
    """Build deterministic rolling, behavior, and price-flow evidence."""

    rows = sorted(
        (fact for fact in facts if fact.market == market and fact.trading_date <= requested_as_of),
        key=lambda fact: fact.trading_date,
        reverse=True,
    )
    expected = (
        tuple(sorted((day for day in expected_sessions if day <= requested_as_of), reverse=True))
        if expected_sessions
        else None
    )
    by_date = {row.trading_date: row for row in rows if row.is_available}
    current = by_date.get(expected[0]) if expected else (rows[0] if rows else None)
    latest_available = max(by_date, default=None)
    expected_latest = expected[0] if expected else latest_available
    if current is not None:
        status = StockFlowStatus.OK
        freshness = resolve_freshness(
            requested_date=expected_latest or requested_as_of,
            source_date=current.trading_date,
            status=StockFlowStatus.OK,
        )
        status_reason = None
    elif latest_available is not None:
        status = StockFlowStatus.STALE
        freshness = StockFlowFreshness.STALE
        status_reason = "LATEST_EXPECTED_SESSION_NOT_AVAILABLE"
    else:
        status = StockFlowStatus.NO_DATA
        freshness = StockFlowFreshness.UNKNOWN
        status_reason = "NO_PERSISTED_STOCK_INSTITUTIONAL_FLOW"
    one_day = _window(rows, 1, expected)
    five_day = _window(rows, 5, expected)
    ten_day = _window(rows, 10, expected)
    twenty_day = _window(rows, 20, expected)
    if current is not None and not all(
        window.complete for window in (one_day, five_day, ten_day, twenty_day)
    ):
        status = StockFlowStatus.PARTIAL
        status_reason = "ONE_OR_MORE_SESSION_WINDOWS_INCOMPLETE"
    ordered_sessions = tuple(rows)
    previous = None
    if expected and len(expected) > 1:
        previous = by_date.get(expected[1])
    elif len(rows) > 1:
        previous = rows[1]
    price_flow, divergence = _price_flow(current, previous, prices or {})
    return StockInstitutionalFlowFeatures(
        market=market,
        instrument_code=instrument_code,
        instrument_id=instrument_id,
        requested_as_of=requested_as_of,
        as_of_date=current.trading_date if current else latest_available,
        latest_available_date=latest_available,
        status=status,
        freshness=freshness,
        status_reason=status_reason,
        current=current,
        sessions=ordered_sessions,
        one_day=one_day,
        five_day=five_day,
        ten_day=ten_day,
        twenty_day=twenty_day,
        streaks={
            "foreign": _streak(rows, "foreign", expected),
            "investmentTrust": _streak(rows, "investment_trust", expected),
            "dealer": _streak(rows, "dealer", expected),
            "total": _streak(rows, "total", expected),
        },
        reversal=_reversal(current, previous),
        price_flow=price_flow,
        divergence=divergence,
        unusual_flow=StockFlowUnusual(),
        liquidity_relative=_liquidity_relative(current, prices or {}),
    )


def _liquidity_relative(
    current: StockInstitutionalFlowFact | None, prices: Mapping[date, StockPriceObservation]
) -> StockFlowLiquidityRelative:
    if current is None:
        return StockFlowLiquidityRelative("UNAVAILABLE", None, None, None, status="UNAVAILABLE")
    price = prices.get(current.trading_date)
    if (
        price is None
        or price.volume is None
        or price.volume <= 0
        or price.quality_state not in {None, "ACCEPTED"}
    ):
        return StockFlowLiquidityRelative(
            "UNAVAILABLE", None, current.total.net, None, status="UNAVAILABLE"
        )
    return StockFlowLiquidityRelative(
        "AVAILABLE",
        current.total.net / price.volume,
        current.total.net,
        price.volume,
    )


__all__ = [
    "STOCK_FLOW_SCALE",
    "STOCK_FLOW_UNIT",
    "TPEX_STOCK_FLOW_ADAPTER_VERSION",
    "TPEX_STOCK_FLOW_DATASET",
    "TPEX_STOCK_FLOW_ENDPOINT",
    "TPEX_STOCK_FLOW_SOURCE_IDENTITY",
    "TWSE_STOCK_FLOW_ADAPTER_VERSION",
    "TWSE_STOCK_FLOW_DATASET",
    "TWSE_STOCK_FLOW_ENDPOINT",
    "TWSE_STOCK_FLOW_SOURCE_IDENTITY",
    "StockFlowContractError",
    "StockFlowDivergence",
    "StockFlowFreshness",
    "StockFlowLeg",
    "StockFlowLiquidityRelative",
    "StockFlowReversal",
    "StockFlowStatus",
    "StockFlowStreak",
    "StockFlowUnusual",
    "StockFlowWindow",
    "StockInstitutionalFlowBatch",
    "StockInstitutionalFlowFact",
    "StockInstitutionalFlowFeatures",
    "StockPriceFlowContext",
    "StockPriceObservation",
    "TpexStockInstitutionalFlowProvider",
    "TwseStockInstitutionalFlowProvider",
    "build_stock_institutional_flow_features",
    "expected_weekday_sessions",
    "map_provider_facts",
    "parse_tpex_stock_institutional_flow",
    "parse_twse_stock_institutional_flow",
    "resolve_freshness",
]
