"""FUND-A market-level institutional investor flow contracts.

The contract is deliberately market-scoped and provider-shaped.  It keeps
the official cash-value semantics from TWSE/TPEx explicit (TWD, whole yuan)
and never turns a missing value into a neutral zero.  Persistence, API, and
Today Signals adapters consume the typed facts defined here; this module does
not own product interpretation or recommendation policy.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any, Final
from urllib.parse import urlencode

TAIPEI: Final[str] = "Asia/Taipei"
FLOW_UNIT: Final[str] = "TWD"
FLOW_SCALE: Final[int] = 0

TWSE_INSTITUTIONAL_FLOW_SOURCE_IDENTITY: Final = "TWSE_OFFICIAL_INSTITUTIONAL_AMOUNT"
TWSE_INSTITUTIONAL_FLOW_ADAPTER_VERSION: Final = "twse-official-institutional-amount.v1"
TWSE_INSTITUTIONAL_FLOW_DATASET: Final = "fund.BFI82U"
TWSE_INSTITUTIONAL_FLOW_ENDPOINT: Final = "https://www.twse.com.tw/rwd/zh/fund/BFI82U"

TPEX_INSTITUTIONAL_FLOW_SOURCE_IDENTITY: Final = "TPEX_OFFICIAL_INSTITUTIONAL_AMOUNT"
TPEX_INSTITUTIONAL_FLOW_ADAPTER_VERSION: Final = "tpex-official-institutional-amount.v1"
TPEX_INSTITUTIONAL_FLOW_DATASET: Final = "tpex_3insti_summary"
TPEX_INSTITUTIONAL_FLOW_ENDPOINT: Final = "https://www.tpex.org.tw/openapi/v1/tpex_3insti_summary"

_MISSING_MARKERS: Final = {"", "-", "--", "---", "N/A", "NULL", "NONE"}
_WS_RE: Final = re.compile(r"\s+")

Transport = Callable[[str, float], bytes]


class FlowAvailability(StrEnum):
    """Why a market/date flow fact can or cannot be consumed."""

    AVAILABLE = "AVAILABLE"
    NOT_YET_PUBLISHED = "NOT_YET_PUBLISHED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    INGESTION_FAILED = "INGESTION_FAILED"
    NON_TRADING_DAY = "NON_TRADING_DAY"


class FlowFreshness(StrEnum):
    """Freshness relative to the requested market session."""

    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class InstitutionalFlowContractError(ValueError):
    """Machine-readable provider contract failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class InstitutionalFlowLeg:
    """One institutional category's official cash-value observation."""

    buy: Decimal
    sell: Decimal
    net: Decimal
    unit: str = FLOW_UNIT
    scale: int = FLOW_SCALE
    status: FlowAvailability = FlowAvailability.AVAILABLE

    def to_dict(self) -> dict[str, Any]:
        return {
            "buy": _json_number(self.buy),
            "sell": _json_number(self.sell),
            "net": _json_number(self.net),
            # ``value`` is a compatibility alias for the existing Today
            # Signals input shape.  It is the same formal net fact.
            "value": _json_number(self.net),
            "unit": self.unit,
            "scale": self.scale,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class MarketInstitutionalFlowFact:
    """One market/date fact set, including source and availability lineage."""

    market: str
    trading_date: date | None
    foreign: InstitutionalFlowLeg | None
    investment_trust: InstitutionalFlowLeg | None
    dealer: InstitutionalFlowLeg | None
    total: InstitutionalFlowLeg | None
    source_provider: str
    source_identity: str
    source_dataset: str
    source_endpoint: str
    adapter_version: str
    source_as_of: datetime | None
    published_at: datetime | None
    retrieved_at: datetime
    availability: FlowAvailability
    freshness: FlowFreshness
    status_reason: str | None
    lineage: str
    response_content_hash: str | None = None
    raw_payload: object | None = None

    @property
    def is_available(self) -> bool:
        return self.availability is FlowAvailability.AVAILABLE

    def to_dict(self) -> dict[str, Any]:
        return {
            "market": self.market,
            "tradingDate": self.trading_date.isoformat() if self.trading_date else None,
            "foreign": self.foreign.to_dict() if self.foreign else None,
            "investmentTrust": (self.investment_trust.to_dict() if self.investment_trust else None),
            "dealer": self.dealer.to_dict() if self.dealer else None,
            "total": self.total.to_dict() if self.total else None,
            "sourceProvider": self.source_provider,
            "sourceIdentity": self.source_identity,
            "sourceDataset": self.source_dataset,
            "sourceEndpoint": self.source_endpoint,
            "adapterVersion": self.adapter_version,
            "sourceAsOf": self.source_as_of.isoformat() if self.source_as_of else None,
            "publishedAt": self.published_at.isoformat() if self.published_at else None,
            "retrievedAt": self.retrieved_at.isoformat(),
            "availability": self.availability.value,
            "freshness": self.freshness.value,
            "statusReason": self.status_reason,
            "lineage": self.lineage,
            "responseContentHash": self.response_content_hash,
            "unit": FLOW_UNIT,
            "scale": FLOW_SCALE,
        }


@dataclass(frozen=True)
class FlowWindow:
    """Deterministic rolling evidence; incomplete windows remain null."""

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
            "unit": FLOW_UNIT,
            "scale": FLOW_SCALE,
        }


@dataclass(frozen=True)
class PriceFlowRelation:
    """Evidence-only relationship between index direction and flow direction."""

    market: str
    index_change: Decimal | None
    flow_net: Decimal | None
    market_direction: str
    flow_direction: str
    direction_relation: str
    availability: FlowAvailability

    def to_dict(self) -> dict[str, Any]:
        return {
            "market": self.market,
            "indexChange": _json_number(self.index_change),
            "flowNet": _json_number(self.flow_net),
            "marketDirection": self.market_direction,
            "flowDirection": self.flow_direction,
            "directionRelation": self.direction_relation,
            "availability": self.availability.value,
        }


@dataclass(frozen=True)
class MarketInstitutionalFlowTrend:
    """Current/previous and rolling evidence for one market."""

    market: str
    as_of_date: date | None
    availability: FlowAvailability
    freshness: FlowFreshness
    current: MarketInstitutionalFlowFact | None
    previous: MarketInstitutionalFlowFact | None
    rolling_5_session: FlowWindow
    rolling_20_session: FlowWindow
    streaks: dict[str, dict[str, Any]]
    acceleration: dict[str, Any]
    price_flow_relation: PriceFlowRelation
    source_as_of: datetime | None
    source: str | None
    status_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "market": self.market,
            "asOfDate": self.as_of_date.isoformat() if self.as_of_date else None,
            "availability": self.availability.value,
            "freshness": self.freshness.value,
            "current": self.current.to_dict() if self.current else None,
            "previous": self.previous.to_dict() if self.previous else None,
            "rolling5Session": self.rolling_5_session.to_dict(),
            "rolling20Session": self.rolling_20_session.to_dict(),
            "streaks": self.streaks,
            "acceleration": self.acceleration,
            "priceFlowRelation": self.price_flow_relation.to_dict(),
            "sourceAsOf": self.source_as_of.isoformat() if self.source_as_of else None,
            "source": self.source,
            "statusReason": self.status_reason,
        }


def _json_number(value: Decimal | None) -> int | float | None:
    if value is None:
        return None
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _content_hash(payload: object) -> str:
    try:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        encoded = repr(payload)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _label(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    return _WS_RE.sub("", normalized).replace("*", "")


def _decimal(value: object, field: str, *, non_negative: bool = False) -> Decimal:
    raw = str(value).strip().replace(",", "")
    if value is None or raw.upper() in _MISSING_MARKERS:
        raise InstitutionalFlowContractError(f"MISSING_{field.upper()}", f"{field} is required")
    try:
        parsed = Decimal(raw)
    except (InvalidOperation, ValueError) as exc:
        raise InstitutionalFlowContractError("INVALID_NUMBER", f"{field} is not numeric") from exc
    if not parsed.is_finite() or (non_negative and parsed < 0):
        raise InstitutionalFlowContractError("INVALID_NUMBER", f"{field} is invalid")
    return parsed


def _date(value: object, field: str) -> date:
    raw = str(value or "").strip().replace("/", "").replace("-", "")
    if len(raw) == 7 and raw.isdigit():
        year = int(raw[:3]) + 1911
        raw = f"{year:04d}{raw[3:]}"
    if len(raw) != 8 or not raw.isdigit():
        raise InstitutionalFlowContractError("INVALID_DATE", f"{field} is invalid")
    try:
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:]))
    except ValueError as exc:
        raise InstitutionalFlowContractError("INVALID_DATE", f"{field} is invalid") from exc


def _rows(payload: object) -> Sequence[Mapping[str, Any]]:
    candidate: object = payload
    if isinstance(payload, Mapping):
        candidate = payload.get("data", payload.get("value"))
    if not isinstance(candidate, Sequence) or isinstance(candidate, (str, bytes, bytearray)):
        raise InstitutionalFlowContractError("INVALID_PAYLOAD", "provider rows must be an array")
    rows: list[Mapping[str, Any]] = []
    for row in candidate:
        if not isinstance(row, Mapping) and not isinstance(row, Sequence):
            raise InstitutionalFlowContractError("INVALID_PAYLOAD", "provider rows are invalid")
        if isinstance(row, Mapping):
            rows.append(row)
    return rows


def _leg(
    buy: object,
    sell: object,
    net: object,
    *,
    field_prefix: str,
) -> InstitutionalFlowLeg:
    parsed_buy = _decimal(buy, f"{field_prefix}_buy", non_negative=True)
    parsed_sell = _decimal(sell, f"{field_prefix}_sell", non_negative=True)
    parsed_net = _decimal(net, f"{field_prefix}_net")
    if parsed_net != parsed_buy - parsed_sell:
        raise InstitutionalFlowContractError(
            "NET_MISMATCH", f"{field_prefix} net does not equal buy minus sell"
        )
    return InstitutionalFlowLeg(parsed_buy, parsed_sell, parsed_net)


def _sum_legs(*legs: InstitutionalFlowLeg) -> InstitutionalFlowLeg:
    return InstitutionalFlowLeg(
        buy=sum((leg.buy for leg in legs), Decimal(0)),
        sell=sum((leg.sell for leg in legs), Decimal(0)),
        net=sum((leg.net for leg in legs), Decimal(0)),
    )


def _metadata(market: str) -> dict[str, str]:
    if market == "TPE":
        return {
            "provider": "TWSE",
            "identity": TWSE_INSTITUTIONAL_FLOW_SOURCE_IDENTITY,
            "dataset": TWSE_INSTITUTIONAL_FLOW_DATASET,
            "endpoint": TWSE_INSTITUTIONAL_FLOW_ENDPOINT,
            "adapter": TWSE_INSTITUTIONAL_FLOW_ADAPTER_VERSION,
            "lineage": "TWSE -> fund.BFI82U -> official cash-value summary -> FUND-A",
        }
    if market == "TWO":
        return {
            "provider": "TPEx",
            "identity": TPEX_INSTITUTIONAL_FLOW_SOURCE_IDENTITY,
            "dataset": TPEX_INSTITUTIONAL_FLOW_DATASET,
            "endpoint": TPEX_INSTITUTIONAL_FLOW_ENDPOINT,
            "adapter": TPEX_INSTITUTIONAL_FLOW_ADAPTER_VERSION,
            "lineage": "TPEx -> tpex_3insti_summary -> official cash-value summary -> FUND-A",
        }
    raise InstitutionalFlowContractError("INVALID_MARKET", f"unsupported market: {market}")


def _unavailable(
    market: str,
    *,
    trading_date: date | None,
    retrieved_at: datetime,
    source_as_of: datetime | None,
    availability: FlowAvailability,
    reason: str,
    response_content_hash: str | None = None,
    raw_payload: object | None = None,
) -> MarketInstitutionalFlowFact:
    metadata = _metadata(market)
    freshness = resolve_freshness(trading_date, source_as_of, as_of_date=trading_date)
    return MarketInstitutionalFlowFact(
        market=market,
        trading_date=trading_date,
        foreign=None,
        investment_trust=None,
        dealer=None,
        total=None,
        source_provider=metadata["provider"],
        source_identity=metadata["identity"],
        source_dataset=metadata["dataset"],
        source_endpoint=metadata["endpoint"],
        adapter_version=metadata["adapter"],
        source_as_of=source_as_of,
        published_at=None,
        retrieved_at=retrieved_at,
        availability=availability,
        freshness=freshness,
        status_reason=reason,
        lineage=metadata["lineage"] + f" -> {availability.value.lower()}({reason})",
        response_content_hash=response_content_hash,
        raw_payload=raw_payload,
    )


def parse_twse_institutional_flow(
    payload: object,
    *,
    retrieved_at: datetime,
    source_as_of: datetime | None = None,
    target_date: date | None = None,
) -> MarketInstitutionalFlowFact:
    """Parse TWSE BFI82U, whose official unit is whole TWD."""

    content_hash = _content_hash(payload)
    metadata = _metadata("TPE")
    source_as_of = source_as_of or retrieved_at
    try:
        if not isinstance(payload, Mapping):
            raise InstitutionalFlowContractError(
                "INVALID_PAYLOAD", "TWSE payload must be an object"
            )
        if str(payload.get("stat", "")).upper() != "OK":
            return _unavailable(
                "TPE",
                trading_date=target_date,
                retrieved_at=retrieved_at,
                source_as_of=source_as_of,
                availability=FlowAvailability.NOT_YET_PUBLISHED,
                reason="SOURCE_NOT_PUBLISHED",
                response_content_hash=content_hash,
                raw_payload=payload,
            )
        trading_date = _date(payload.get("date"), "date")
        if target_date is not None and trading_date != target_date:
            reason = (
                "PROVIDER_DATE_BEFORE_TARGET"
                if trading_date < target_date
                else "PROVIDER_DATE_MISMATCH"
            )
            return _unavailable(
                "TPE",
                trading_date=trading_date,
                retrieved_at=retrieved_at,
                source_as_of=source_as_of,
                availability=(
                    FlowAvailability.NOT_YET_PUBLISHED
                    if trading_date < target_date
                    else FlowAvailability.SOURCE_UNAVAILABLE
                ),
                reason=reason,
                response_content_hash=content_hash,
                raw_payload=payload,
            )
        rows = payload.get("data")
        if not isinstance(rows, list):
            raise InstitutionalFlowContractError("INVALID_PAYLOAD", "TWSE data must be an array")
        indexed = {_label(row[0]): row for row in rows if isinstance(row, list) and len(row) >= 4}
        required = {
            "foreign": "外資及陸資(不含外資自營商)",
            "trust": "投信",
            "dealer_self": "自營商(自行買賣)",
            "dealer_hedge": "自營商(避險)",
            "total": "合計",
        }
        if any(_label(label) not in indexed for label in required.values()):
            raise InstitutionalFlowContractError(
                "MISSING_PROVIDER_FIELD", "TWSE summary rows are incomplete"
            )

        def row_leg(label: str, name: str) -> InstitutionalFlowLeg:
            row = indexed[_label(label)]
            return _leg(row[1], row[2], row[3], field_prefix=name)

        foreign = row_leg(required["foreign"], "foreign")
        trust = row_leg(required["trust"], "investment_trust")
        dealer = _sum_legs(
            row_leg(required["dealer_self"], "dealer_self"),
            row_leg(required["dealer_hedge"], "dealer_hedge"),
        )
        total = row_leg(required["total"], "total")
        if total != _sum_legs(foreign, trust, dealer):
            raise InstitutionalFlowContractError(
                "TOTAL_MISMATCH", "TWSE total does not reconcile with foreign, trust, and dealer"
            )
        return MarketInstitutionalFlowFact(
            market="TPE",
            trading_date=trading_date,
            foreign=foreign,
            investment_trust=trust,
            dealer=dealer,
            total=total,
            source_provider=metadata["provider"],
            source_identity=metadata["identity"],
            source_dataset=metadata["dataset"],
            source_endpoint=metadata["endpoint"],
            adapter_version=metadata["adapter"],
            source_as_of=source_as_of,
            published_at=None,
            retrieved_at=retrieved_at,
            availability=FlowAvailability.AVAILABLE,
            freshness=resolve_freshness(
                trading_date, source_as_of, as_of_date=target_date or trading_date
            ),
            status_reason=None,
            lineage=metadata["lineage"],
            response_content_hash=content_hash,
            raw_payload=payload,
        )
    except InstitutionalFlowContractError as exc:
        return _unavailable(
            "TPE",
            trading_date=target_date,
            retrieved_at=retrieved_at,
            source_as_of=source_as_of,
            availability=FlowAvailability.INGESTION_FAILED,
            reason=exc.code,
            response_content_hash=content_hash,
            raw_payload=payload,
        )


def parse_tpex_institutional_flow(
    payload: object,
    *,
    retrieved_at: datetime,
    source_as_of: datetime | None = None,
    target_date: date | None = None,
) -> MarketInstitutionalFlowFact:
    """Parse TPEx OpenAPI ``tpex_3insti_summary`` amount rows."""

    content_hash = _content_hash(payload)
    metadata = _metadata("TWO")
    source_as_of = source_as_of or retrieved_at
    try:
        rows = _rows(payload)
        if not rows:
            raise InstitutionalFlowContractError("MISSING_PROVIDER_FIELD", "TPEx summary is empty")
        dates = {_date(row.get("Date"), "Date") for row in rows}
        if len(dates) != 1:
            raise InstitutionalFlowContractError(
                "AMBIGUOUS_DATE", "TPEx summary has multiple dates"
            )
        trading_date = dates.pop()
        if target_date is not None and trading_date != target_date:
            return _unavailable(
                "TWO",
                trading_date=trading_date,
                retrieved_at=retrieved_at,
                source_as_of=source_as_of,
                availability=(
                    FlowAvailability.NOT_YET_PUBLISHED
                    if trading_date < target_date
                    else FlowAvailability.SOURCE_UNAVAILABLE
                ),
                reason=(
                    "PROVIDER_DATE_BEFORE_TARGET"
                    if trading_date < target_date
                    else "PROVIDER_DATE_MISMATCH"
                ),
                response_content_hash=content_hash,
                raw_payload=payload,
            )
        indexed = {_label(row.get("Investor")): row for row in rows}
        foreign_row = indexed.get(_label("外資及陸資(不含自營商)")) or indexed.get(
            _label("外資及陸資合計")
        )
        trust_row = indexed.get(_label("投信"))
        dealer_row = indexed.get(_label("自營商合計"))
        total_row = indexed.get(_label("三大法人合計*"))
        if not all((foreign_row, trust_row, dealer_row, total_row)):
            raise InstitutionalFlowContractError(
                "MISSING_PROVIDER_FIELD", "TPEx summary rows are incomplete"
            )

        def row_leg(row: Mapping[str, Any], name: str) -> InstitutionalFlowLeg:
            return _leg(
                row.get("PurchaseAmount"), row.get("SaleAmount"), row.get("Net"), field_prefix=name
            )

        foreign = row_leg(foreign_row, "foreign")
        trust = row_leg(trust_row, "investment_trust")
        dealer = row_leg(dealer_row, "dealer")
        total = row_leg(total_row, "total")
        if total != _sum_legs(foreign, trust, dealer):
            raise InstitutionalFlowContractError(
                "TOTAL_MISMATCH", "TPEx total does not reconcile with foreign, trust, and dealer"
            )
        return MarketInstitutionalFlowFact(
            market="TWO",
            trading_date=trading_date,
            foreign=foreign,
            investment_trust=trust,
            dealer=dealer,
            total=total,
            source_provider=metadata["provider"],
            source_identity=metadata["identity"],
            source_dataset=metadata["dataset"],
            source_endpoint=metadata["endpoint"],
            adapter_version=metadata["adapter"],
            source_as_of=source_as_of,
            published_at=None,
            retrieved_at=retrieved_at,
            availability=FlowAvailability.AVAILABLE,
            freshness=resolve_freshness(
                trading_date, source_as_of, as_of_date=target_date or trading_date
            ),
            status_reason=None,
            lineage=metadata["lineage"],
            response_content_hash=content_hash,
            raw_payload=payload,
        )
    except InstitutionalFlowContractError as exc:
        return _unavailable(
            "TWO",
            trading_date=target_date,
            retrieved_at=retrieved_at,
            source_as_of=source_as_of,
            availability=FlowAvailability.INGESTION_FAILED,
            reason=exc.code,
            response_content_hash=content_hash,
            raw_payload=payload,
        )


def resolve_freshness(
    trading_date: date | None,
    source_as_of: datetime | None,
    *,
    as_of_date: date | None,
) -> FlowFreshness:
    """Resolve freshness by exact session identity, with no invented age bucket."""

    if trading_date is None or source_as_of is None or as_of_date is None:
        return FlowFreshness.UNKNOWN
    return FlowFreshness.CURRENT if trading_date >= as_of_date else FlowFreshness.STALE


def fetch_official_market_institutional_flows(
    *,
    target_date: date,
    retrieved_at: datetime,
    transport: Transport,
    source_as_of: datetime | None = None,
    timeout: float = 30.0,
    trading_day_by_market: Mapping[str, bool] | None = None,
) -> tuple[MarketInstitutionalFlowFact, ...]:
    """Fetch TPE and TWO independently; a failed market never poisons the other."""

    twse_query = urlencode(
        {
            "date": target_date.strftime("%Y%m%d"),
            "type": "day",
            "response": "json",
        }
    )
    requests = (
        (
            "TPE",
            f"{TWSE_INSTITUTIONAL_FLOW_ENDPOINT}?{twse_query}",
            parse_twse_institutional_flow,
        ),
        ("TWO", TPEX_INSTITUTIONAL_FLOW_ENDPOINT, parse_tpex_institutional_flow),
    )
    results: list[MarketInstitutionalFlowFact] = []
    for market, endpoint, parser in requests:
        if trading_day_by_market is not None and not trading_day_by_market.get(market, True):
            results.append(
                _unavailable(
                    market,
                    trading_date=target_date,
                    retrieved_at=retrieved_at,
                    source_as_of=source_as_of,
                    availability=FlowAvailability.NON_TRADING_DAY,
                    reason="MARKET_CALENDAR_NON_TRADING_DAY",
                )
            )
            continue
        try:
            payload = json.loads(transport(endpoint, timeout).decode("utf-8"))
            results.append(
                parser(
                    payload,
                    retrieved_at=retrieved_at,
                    source_as_of=source_as_of,
                    target_date=target_date,
                )
            )
        except Exception:
            results.append(
                _unavailable(
                    market,
                    trading_date=target_date,
                    retrieved_at=retrieved_at,
                    source_as_of=source_as_of,
                    availability=FlowAvailability.SOURCE_UNAVAILABLE,
                    reason="PROVIDER_REQUEST_FAILED",
                )
            )
    return tuple(results)


def build_price_flow_relation(
    *, market: str, index_change: Decimal | None, flow_net: Decimal | None
) -> PriceFlowRelation:
    if index_change is None or flow_net is None:
        return PriceFlowRelation(
            market,
            index_change,
            flow_net,
            "UNKNOWN",
            "UNKNOWN",
            "UNKNOWN",
            FlowAvailability.SOURCE_UNAVAILABLE,
        )
    market_direction = "UP" if index_change > 0 else "DOWN" if index_change < 0 else "FLAT"
    flow_direction = "BUY" if flow_net > 0 else "SELL" if flow_net < 0 else "FLAT"
    if market_direction == "FLAT" or flow_direction == "FLAT":
        relation = "NO_DIRECTION"
    elif market_direction == "UP" and flow_direction == "BUY":
        relation = "ALIGNED_POSITIVE"
    elif market_direction == "DOWN" and flow_direction == "SELL":
        relation = "ALIGNED_NEGATIVE"
    else:
        relation = "DIVERGENCE"
    return PriceFlowRelation(
        market,
        index_change,
        flow_net,
        market_direction,
        flow_direction,
        relation,
        FlowAvailability.AVAILABLE,
    )


def _net(fact: MarketInstitutionalFlowFact | None, category: str) -> Decimal | None:
    if fact is None or not fact.is_available:
        return None
    leg = getattr(fact, category)
    return leg.net if leg is not None else None


def _window(rows: Sequence[MarketInstitutionalFlowFact], required: int) -> FlowWindow:
    candidate = rows[:required]
    available = [row for row in candidate if row.is_available]
    complete = len(candidate) == required and len(available) == required
    return FlowWindow(
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


def _streak(rows: Sequence[MarketInstitutionalFlowFact], category: str) -> dict[str, Any]:
    if not rows or not rows[0].is_available:
        return {"direction": "UNKNOWN", "sessions": 0}
    first = _net(rows[0], category)
    if first is None or first == 0:
        return {"direction": "FLAT", "sessions": 0}
    direction = "BUY" if first > 0 else "SELL"
    count = 0
    for row in rows:
        if not row.is_available:
            break
        value = _net(row, category)
        if (
            value is None
            or (value > 0 and direction != "BUY")
            or (value < 0 and direction != "SELL")
            or value == 0
        ):
            break
        count += 1
    return {"direction": direction, "sessions": count}


def _acceleration(rows: Sequence[MarketInstitutionalFlowFact]) -> dict[str, Any]:
    if len(rows) < 10 or not all(row.is_available for row in rows[:10]):
        return {
            "available": False,
            "requiredSessions": 10,
            "observedSessions": sum(row.is_available for row in rows[:10]),
            "foreignDelta": None,
            "investmentTrustDelta": None,
            "dealerDelta": None,
            "totalDelta": None,
            "unit": FLOW_UNIT,
            "scale": FLOW_SCALE,
        }
    current = _window(rows[:5], 5)
    prior = _window(rows[5:10], 5)
    return {
        "available": True,
        "requiredSessions": 10,
        "observedSessions": 10,
        "foreignDelta": current.foreign_net - prior.foreign_net,
        "investmentTrustDelta": current.investment_trust_net - prior.investment_trust_net,
        "dealerDelta": current.dealer_net - prior.dealer_net,
        "totalDelta": current.total_net - prior.total_net,
        "unit": FLOW_UNIT,
        "scale": FLOW_SCALE,
    }


def build_market_institutional_flow_trend(
    facts: Sequence[MarketInstitutionalFlowFact],
    *,
    market: str,
    as_of_date: date | None = None,
    index_change: Decimal | None = None,
) -> MarketInstitutionalFlowTrend:
    """Build a fail-closed trend read model from descending daily facts."""

    rows = sorted(
        (
            fact
            for fact in facts
            if fact.market == market
            and (as_of_date is None or fact.trading_date is None or fact.trading_date <= as_of_date)
        ),
        key=lambda fact: fact.trading_date or date.min,
        reverse=True,
    )
    current = rows[0] if rows else None
    previous = rows[1] if len(rows) > 1 else None
    current_date = current.trading_date if current else as_of_date
    availability = current.availability if current else FlowAvailability.SOURCE_UNAVAILABLE
    freshness = current.freshness if current else FlowFreshness.UNKNOWN
    status_reason = current.status_reason if current else "NO_PERSISTED_FLOW_FACT"
    relation = build_price_flow_relation(
        market=market,
        index_change=index_change,
        flow_net=_net(current, "total"),
    )
    return MarketInstitutionalFlowTrend(
        market=market,
        as_of_date=current_date,
        availability=availability,
        freshness=freshness,
        current=current,
        previous=previous,
        rolling_5_session=_window(rows, 5),
        rolling_20_session=_window(rows, 20),
        streaks={
            "foreign": _streak(rows, "foreign"),
            "investmentTrust": _streak(rows, "investment_trust"),
            "dealer": _streak(rows, "dealer"),
            "total": _streak(rows, "total"),
        },
        acceleration=_acceleration(rows),
        price_flow_relation=relation,
        source_as_of=current.source_as_of if current else None,
        source=current.source_identity if current else None,
        status_reason=status_reason,
    )


def to_home_institutional_flow_payload(
    facts: Sequence[MarketInstitutionalFlowFact],
    *,
    index_changes: Mapping[str, Decimal | None] | None = None,
    as_of_date: date | None = None,
) -> dict[str, Any] | None:
    """Return the additive Home payload without changing Today policy."""

    if not facts:
        return None
    markets = []
    for market in ("TPE", "TWO"):
        trend = build_market_institutional_flow_trend(
            facts,
            market=market,
            as_of_date=as_of_date,
            index_change=(index_changes or {}).get(market),
        )
        markets.append(trend.to_dict())
    available = [
        item for item in markets if item["availability"] == FlowAvailability.AVAILABLE.value
    ]
    status = "AVAILABLE" if len(available) == 2 else "PARTIAL" if available else "UNAVAILABLE"
    freshness_values = {item["freshness"] for item in markets}
    freshness = (
        "CURRENT"
        if freshness_values == {FlowFreshness.CURRENT.value}
        else "STALE"
        if FlowFreshness.STALE.value in freshness_values
        else "UNKNOWN"
    )
    source_as_of = max(
        (fact.source_as_of for fact in facts if fact.source_as_of is not None),
        default=None,
    )
    return {
        "contractVersion": "fund-a.market-flow.v1",
        "asOfDate": as_of_date
        or max((fact.trading_date for fact in facts if fact.trading_date), default=None),
        "status": status,
        "freshness": freshness,
        "markets": markets,
        "sourceAsOf": source_as_of,
        "source": "FUND_A_MARKET_FLOW",
        "unit": FLOW_UNIT,
        "scale": FLOW_SCALE,
    }


__all__ = [
    "FLOW_SCALE",
    "FLOW_UNIT",
    "TPEX_INSTITUTIONAL_FLOW_ADAPTER_VERSION",
    "TPEX_INSTITUTIONAL_FLOW_DATASET",
    "TPEX_INSTITUTIONAL_FLOW_ENDPOINT",
    "TPEX_INSTITUTIONAL_FLOW_SOURCE_IDENTITY",
    "TWSE_INSTITUTIONAL_FLOW_ADAPTER_VERSION",
    "TWSE_INSTITUTIONAL_FLOW_DATASET",
    "TWSE_INSTITUTIONAL_FLOW_ENDPOINT",
    "TWSE_INSTITUTIONAL_FLOW_SOURCE_IDENTITY",
    "FlowAvailability",
    "FlowFreshness",
    "FlowWindow",
    "InstitutionalFlowContractError",
    "InstitutionalFlowLeg",
    "MarketInstitutionalFlowFact",
    "MarketInstitutionalFlowTrend",
    "PriceFlowRelation",
    "build_market_institutional_flow_trend",
    "build_price_flow_relation",
    "fetch_official_market_institutional_flows",
    "parse_tpex_institutional_flow",
    "parse_twse_institutional_flow",
    "resolve_freshness",
    "to_home_institutional_flow_payload",
]
