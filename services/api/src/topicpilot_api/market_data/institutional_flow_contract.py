"""Formal whole-market institutional-flow facts for Home V2.

The exchanges already publish the four market-level values needed by Today:
foreign investors, investment trusts, dealers, and the three-institution
total.  This module keeps that provider boundary typed and fail-closed; it
does not infer flow values from prices or from the product universe.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Final
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

TWSE_INSTITUTIONAL_FLOW_ENDPOINT: Final = (
    "https://www.twse.com.tw/rwd/zh/fund/BFI82U"
)
TPEX_INSTITUTIONAL_FLOW_ENDPOINT: Final = (
    "https://www.tpex.org.tw/www/zh-tw/insti/summary"
)
TWSE_INSTITUTIONAL_FLOW_SOURCE: Final = "TWSE_OFFICIAL_BFI82U"
TPEX_INSTITUTIONAL_FLOW_SOURCE: Final = "TPEX_OFFICIAL_INSTI_SUMMARY"
INSTITUTIONAL_FLOW_ADAPTER_VERSION: Final = "market-institutional-flow.v1"

Transport = Callable[[str, float], bytes]


class InstitutionalFlowContractError(ValueError):
    """Machine-readable provider validation error."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class MarketInstitutionalFlowResult:
    """One normalized exchange-level institutional-flow fact set."""

    market: str
    trading_date: date | None
    source_provider: str
    source_identity: str
    source_dataset: str
    source_endpoint: str
    adapter_version: str
    source_as_of: datetime
    published_at: datetime | None
    retrieved_at: datetime
    unit: str
    scale: int
    foreign_buy: Decimal | None
    foreign_sell: Decimal | None
    foreign_net: Decimal | None
    investment_trust_buy: Decimal | None
    investment_trust_sell: Decimal | None
    investment_trust_net: Decimal | None
    dealer_buy: Decimal | None
    dealer_sell: Decimal | None
    dealer_net: Decimal | None
    total_buy: Decimal | None
    total_sell: Decimal | None
    total_net: Decimal | None
    availability: str
    freshness: str
    status_reason: str | None
    lineage: str
    lineage_hash: str
    response_content_hash: str | None
    raw_payload: object | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "market": self.market,
            "tradingDate": self.trading_date.isoformat() if self.trading_date else None,
            "sourceProvider": self.source_provider,
            "sourceIdentity": self.source_identity,
            "sourceDataset": self.source_dataset,
            "sourceEndpoint": self.source_endpoint,
            "adapterVersion": self.adapter_version,
            "sourceAsOf": self.source_as_of.isoformat(),
            "publishedAt": self.published_at.isoformat() if self.published_at else None,
            "retrievedAt": self.retrieved_at.isoformat(),
            "unit": self.unit,
            "scale": self.scale,
            "foreignBuy": str(self.foreign_buy) if self.foreign_buy is not None else None,
            "foreignSell": str(self.foreign_sell) if self.foreign_sell is not None else None,
            "foreignNet": str(self.foreign_net) if self.foreign_net is not None else None,
            "investmentTrustBuy": (
                str(self.investment_trust_buy)
                if self.investment_trust_buy is not None
                else None
            ),
            "investmentTrustSell": (
                str(self.investment_trust_sell)
                if self.investment_trust_sell is not None
                else None
            ),
            "investmentTrustNet": (
                str(self.investment_trust_net)
                if self.investment_trust_net is not None
                else None
            ),
            "dealerBuy": str(self.dealer_buy) if self.dealer_buy is not None else None,
            "dealerSell": str(self.dealer_sell) if self.dealer_sell is not None else None,
            "dealerNet": str(self.dealer_net) if self.dealer_net is not None else None,
            "totalBuy": str(self.total_buy) if self.total_buy is not None else None,
            "totalSell": str(self.total_sell) if self.total_sell is not None else None,
            "totalNet": str(self.total_net) if self.total_net is not None else None,
            "availability": self.availability,
            "freshness": self.freshness,
            "statusReason": self.status_reason,
            "lineage": self.lineage,
            "lineageHash": self.lineage_hash,
            "responseContentHash": self.response_content_hash,
        }


def _content_hash(payload: object) -> str:
    try:
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        canonical = repr(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _date(value: object, field: str) -> date:
    raw = str(value or "").strip()
    digits = re.sub(r"[^0-9]", "", raw)
    if len(digits) == 8:
        year, month, day = int(digits[:4]), int(digits[4:6]), int(digits[6:])
    else:
        parts = re.split(r"[/.-]", raw)
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise InstitutionalFlowContractError("INVALID_DATE", f"{field} is invalid")
        year, month, day = (int(part) for part in parts)
        if year < 1911:
            year += 1911
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise InstitutionalFlowContractError("INVALID_DATE", f"{field} is invalid") from exc


def _rows(payload: object) -> Sequence[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        raise InstitutionalFlowContractError("INVALID_PAYLOAD", "provider tables are missing")
    if isinstance(payload.get("data"), list) and payload["data"]:
        return [{"cells": row} for row in payload["data"] if isinstance(row, list)]
    if not isinstance(payload.get("tables"), list):
        raise InstitutionalFlowContractError("INVALID_PAYLOAD", "provider tables are missing")
    for table in payload["tables"]:
        if isinstance(table, Mapping) and isinstance(table.get("data"), list):
            rows = [row for row in table["data"] if isinstance(row, list)]
            if rows:
                return [{"cells": row} for row in rows]
    raise InstitutionalFlowContractError("ROWS_MISSING", "institutional-flow rows are missing")


def _label(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "")).rstrip("*")


def _money(value: object, field: str) -> Decimal:
    raw = str(value or "").strip().replace(",", "")
    if not raw:
        raise InstitutionalFlowContractError("MISSING_VALUE", f"{field} is missing")
    try:
        result = Decimal(raw)
    except (InvalidOperation, ValueError) as exc:
        raise InstitutionalFlowContractError("INVALID_NUMBER", f"{field} is invalid") from exc
    if not result.is_finite():
        raise InstitutionalFlowContractError("INVALID_NUMBER", f"{field} is invalid")
    return result


def _flow_row(
    rows: Sequence[Mapping[str, Any]], aliases: tuple[str, ...], label: str
) -> tuple[Decimal, Decimal, Decimal]:
    for row in rows:
        cells = row["cells"]
        if not cells or _label(cells[0]) not in aliases:
            continue
        if len(cells) < 4:
            break
        return (
            _money(cells[1], f"{label}.buy"),
            _money(cells[2], f"{label}.sell"),
            _money(cells[3], f"{label}.net"),
        )
    raise InstitutionalFlowContractError("ROW_MISSING", f"{label} row is missing")


def _sum_flow_rows(
    rows: Sequence[Mapping[str, Any]], aliases: tuple[str, ...], label: str
) -> tuple[Decimal, Decimal, Decimal]:
    values = [_flow_row(rows, (alias,), label) for alias in aliases]
    return tuple(sum(item[index] for item in values) for index in range(3))  # type: ignore[return-value]


def _unavailable(
    *,
    market: str,
    source_provider: str,
    source_identity: str,
    source_dataset: str,
    source_endpoint: str,
    target_date: date | None,
    retrieved_at: datetime,
    as_of: datetime,
    reason: str,
    raw_payload: object | None = None,
) -> MarketInstitutionalFlowResult:
    lineage = f"{source_provider} -> {source_dataset} -> unavailable({reason})"
    return MarketInstitutionalFlowResult(
        market=market,
        trading_date=target_date,
        source_provider=source_provider,
        source_identity=source_identity,
        source_dataset=source_dataset,
        source_endpoint=source_endpoint,
        adapter_version=INSTITUTIONAL_FLOW_ADAPTER_VERSION,
        source_as_of=as_of,
        published_at=None,
        retrieved_at=retrieved_at,
        unit="TWD",
        scale=0,
        foreign_buy=None,
        foreign_sell=None,
        foreign_net=None,
        investment_trust_buy=None,
        investment_trust_sell=None,
        investment_trust_net=None,
        dealer_buy=None,
        dealer_sell=None,
        dealer_net=None,
        total_buy=None,
        total_sell=None,
        total_net=None,
        availability="SOURCE_UNAVAILABLE",
        freshness="UNKNOWN",
        status_reason=reason,
        lineage=lineage,
        lineage_hash=hashlib.sha256(lineage.encode("utf-8")).hexdigest(),
        response_content_hash=_content_hash(raw_payload) if raw_payload is not None else None,
        raw_payload=raw_payload,
    )


def _parse(
    payload: object,
    *,
    market: str,
    source_provider: str,
    source_identity: str,
    source_dataset: str,
    source_endpoint: str,
    retrieved_at: datetime,
    as_of: datetime,
) -> MarketInstitutionalFlowResult:
    content_hash = _content_hash(payload)
    try:
        if not isinstance(payload, Mapping):
            raise InstitutionalFlowContractError(
                "INVALID_PAYLOAD", "provider payload is not an object"
            )
        trading_date = _date(payload.get("date"), "date")
        rows = _rows(payload)
        foreign = _flow_row(
            rows,
            ("外資及陸資(不含自營商)", "外資及陸資(不含外資自營商)", "外資及陸資合計"),
            "foreign",
        )
        trust = _flow_row(rows, ("投信",), "investment_trust")
        dealer = (
            _sum_flow_rows(rows, ("自營商(自行買賣)", "自營商(避險)"), "dealer")
            if source_identity == "TWSE_BFI82U"
            else _flow_row(rows, ("自營商合計",), "dealer")
        )
        total = _flow_row(
            rows,
            ("合計", "三大法人合計"),
            "total",
        )
        lineage = f"{source_provider} -> {source_dataset} -> formal market institutional flow"
        return MarketInstitutionalFlowResult(
            market=market,
            trading_date=trading_date,
            source_provider=source_provider,
            source_identity=source_identity,
            source_dataset=source_dataset,
            source_endpoint=source_endpoint,
            adapter_version=INSTITUTIONAL_FLOW_ADAPTER_VERSION,
            source_as_of=as_of,
            published_at=as_of,
            retrieved_at=retrieved_at,
            unit="TWD",
            scale=0,
            foreign_buy=foreign[0],
            foreign_sell=foreign[1],
            foreign_net=foreign[2],
            investment_trust_buy=trust[0],
            investment_trust_sell=trust[1],
            investment_trust_net=trust[2],
            dealer_buy=dealer[0],
            dealer_sell=dealer[1],
            dealer_net=dealer[2],
            total_buy=total[0],
            total_sell=total[1],
            total_net=total[2],
            availability="AVAILABLE",
            freshness="CURRENT",
            status_reason=None,
            lineage=lineage,
            lineage_hash=hashlib.sha256(lineage.encode("utf-8")).hexdigest(),
            response_content_hash=content_hash,
            raw_payload=payload,
        )
    except (InstitutionalFlowContractError, KeyError, IndexError, TypeError) as exc:
        reason = exc.code if isinstance(exc, InstitutionalFlowContractError) else "INVALID_PAYLOAD"
        return _unavailable(
            market=market,
            source_provider=source_provider,
            source_identity=source_identity,
            source_dataset=source_dataset,
            source_endpoint=source_endpoint,
            target_date=None,
            retrieved_at=retrieved_at,
            as_of=as_of,
            reason=reason,
            raw_payload=payload,
        )


def parse_twse_institutional_flow(
    payload: object, *, retrieved_at: datetime, as_of: datetime
) -> MarketInstitutionalFlowResult:
    return _parse(
        payload,
        market="TPE",
        source_provider="TWSE",
        source_identity="TWSE_BFI82U",
        source_dataset="BFI82U 三大法人買賣金額統計表",
        source_endpoint=TWSE_INSTITUTIONAL_FLOW_ENDPOINT,
        retrieved_at=retrieved_at,
        as_of=as_of,
    )


def parse_tpex_institutional_flow(
    payload: object, *, retrieved_at: datetime, as_of: datetime
) -> MarketInstitutionalFlowResult:
    return _parse(
        payload,
        market="TWO",
        source_provider="TPEX",
        source_identity="TPEX_INSTI_SUMMARY",
        source_dataset="insti/summary 三大法人買賣明細資訊",
        source_endpoint=TPEX_INSTITUTIONAL_FLOW_ENDPOINT,
        retrieved_at=retrieved_at,
        as_of=as_of,
    )


def fetch_official_market_institutional_flows(
    *,
    target_date: date,
    retrieved_at: datetime,
    as_of: datetime,
    transport: Transport,
    timeout: float = 30.0,
) -> tuple[MarketInstitutionalFlowResult, ...]:
    """Fetch both official exchange reports and fail closed per market."""

    requests = (
        (
            "TPE",
            f"{TWSE_INSTITUTIONAL_FLOW_ENDPOINT}?dayDate={target_date:%Y%m%d}&response=json",
            parse_twse_institutional_flow,
        ),
        (
            "TWO",
            f"{TPEX_INSTITUTIONAL_FLOW_ENDPOINT}?date={target_date:%Y/%m/%d}",
            parse_tpex_institutional_flow,
        ),
    )
    results: list[MarketInstitutionalFlowResult] = []
    for market, endpoint, parser in requests:
        source_provider = "TWSE" if market == "TPE" else "TPEX"
        source_identity = "TWSE_BFI82U" if market == "TPE" else "TPEX_INSTI_SUMMARY"
        source_dataset = (
            "BFI82U 三大法人買賣金額統計表"
            if market == "TPE"
            else "insti/summary 三大法人買賣明細資訊"
        )
        try:
            payload = json.loads(transport(endpoint, timeout).decode("utf-8"))
            result = parser(payload, retrieved_at=retrieved_at, as_of=as_of)
            if result.availability == "AVAILABLE" and result.trading_date != target_date:
                result = _unavailable(
                    market=market,
                    source_provider=source_provider,
                    source_identity=source_identity,
                    source_dataset=source_dataset,
                    source_endpoint=endpoint.split("?", 1)[0],
                    target_date=target_date,
                    retrieved_at=retrieved_at,
                    as_of=as_of,
                    reason="PROVIDER_DATE_MISMATCH",
                    raw_payload=payload,
                )
            elif result.trading_date is None:
                result = replace(result, trading_date=target_date)
        except Exception:
            result = _unavailable(
                market=market,
                source_provider=source_provider,
                source_identity=source_identity,
                source_dataset=source_dataset,
                source_endpoint=endpoint.split("?", 1)[0],
                target_date=target_date,
                retrieved_at=retrieved_at,
                as_of=as_of,
                reason="PROVIDER_REQUEST_FAILED",
            )
        results.append(result)
    return tuple(results)


def persist_market_institutional_flows(
    session: Session,
    facts: Sequence[MarketInstitutionalFlowResult],
    *,
    ingested_at: datetime,
) -> dict[str, int | str]:
    """Upsert the already-authorized FUND-A fact table, without migrations."""

    statement = text(
        """
        INSERT INTO topicpilot.market_institutional_flow_daily (
            id, created_at, updated_at, market, trading_date,
            source_provider, source_identity, source_dataset, source_endpoint,
            adapter_version, source_as_of, published_at, retrieved_at, ingested_at,
            unit, scale,
            foreign_buy, foreign_sell, foreign_net,
            investment_trust_buy, investment_trust_sell, investment_trust_net,
            dealer_buy, dealer_sell, dealer_net,
            total_buy, total_sell, total_net,
            availability, freshness, status_reason, lineage, lineage_hash,
            response_content_hash, raw_payload
        ) VALUES (
            :id, :created_at, :updated_at, :market, :trading_date,
            :source_provider, :source_identity, :source_dataset, :source_endpoint,
            :adapter_version, :source_as_of, :published_at, :retrieved_at, :ingested_at,
            :unit, :scale,
            :foreign_buy, :foreign_sell, :foreign_net,
            :investment_trust_buy, :investment_trust_sell, :investment_trust_net,
            :dealer_buy, :dealer_sell, :dealer_net,
            :total_buy, :total_sell, :total_net,
            :availability, :freshness, :status_reason, :lineage, :lineage_hash,
            :response_content_hash, CAST(:raw_payload AS jsonb)
        )
        ON CONFLICT (market, trading_date, source_identity) DO UPDATE SET
            updated_at = EXCLUDED.updated_at,
            source_provider = EXCLUDED.source_provider,
            source_dataset = EXCLUDED.source_dataset,
            source_endpoint = EXCLUDED.source_endpoint,
            adapter_version = EXCLUDED.adapter_version,
            source_as_of = EXCLUDED.source_as_of,
            published_at = EXCLUDED.published_at,
            retrieved_at = EXCLUDED.retrieved_at,
            ingested_at = EXCLUDED.ingested_at,
            unit = EXCLUDED.unit,
            scale = EXCLUDED.scale,
            foreign_buy = EXCLUDED.foreign_buy,
            foreign_sell = EXCLUDED.foreign_sell,
            foreign_net = EXCLUDED.foreign_net,
            investment_trust_buy = EXCLUDED.investment_trust_buy,
            investment_trust_sell = EXCLUDED.investment_trust_sell,
            investment_trust_net = EXCLUDED.investment_trust_net,
            dealer_buy = EXCLUDED.dealer_buy,
            dealer_sell = EXCLUDED.dealer_sell,
            dealer_net = EXCLUDED.dealer_net,
            total_buy = EXCLUDED.total_buy,
            total_sell = EXCLUDED.total_sell,
            total_net = EXCLUDED.total_net,
            availability = EXCLUDED.availability,
            freshness = EXCLUDED.freshness,
            status_reason = EXCLUDED.status_reason,
            lineage = EXCLUDED.lineage,
            lineage_hash = EXCLUDED.lineage_hash,
            response_content_hash = EXCLUDED.response_content_hash,
            raw_payload = EXCLUDED.raw_payload
        """
    )
    persisted = 0
    available = 0
    for fact in facts:
        if fact.trading_date is None:
            continue
        payload = (
            json.dumps(fact.raw_payload, ensure_ascii=False)
            if fact.raw_payload is not None
            else None
        )
        session.execute(
            statement,
            {
                "id": uuid4(),
                "created_at": ingested_at,
                "updated_at": ingested_at,
                "market": fact.market,
                "trading_date": fact.trading_date,
                "source_provider": fact.source_provider,
                "source_identity": fact.source_identity,
                "source_dataset": fact.source_dataset,
                "source_endpoint": fact.source_endpoint,
                "adapter_version": fact.adapter_version,
                "source_as_of": fact.source_as_of,
                "published_at": fact.published_at,
                "retrieved_at": fact.retrieved_at,
                "ingested_at": ingested_at,
                "unit": fact.unit,
                "scale": fact.scale,
                "foreign_buy": fact.foreign_buy,
                "foreign_sell": fact.foreign_sell,
                "foreign_net": fact.foreign_net,
                "investment_trust_buy": fact.investment_trust_buy,
                "investment_trust_sell": fact.investment_trust_sell,
                "investment_trust_net": fact.investment_trust_net,
                "dealer_buy": fact.dealer_buy,
                "dealer_sell": fact.dealer_sell,
                "dealer_net": fact.dealer_net,
                "total_buy": fact.total_buy,
                "total_sell": fact.total_sell,
                "total_net": fact.total_net,
                "availability": fact.availability,
                "freshness": fact.freshness,
                "status_reason": fact.status_reason,
                "lineage": fact.lineage,
                "lineage_hash": fact.lineage_hash,
                "response_content_hash": fact.response_content_hash,
                "raw_payload": payload,
            },
        )
        persisted += 1
        available += fact.availability == "AVAILABLE"
    return {"status": "SUCCESS", "persisted": persisted, "available": available}


__all__ = [
    "INSTITUTIONAL_FLOW_ADAPTER_VERSION",
    "TPEX_INSTITUTIONAL_FLOW_ENDPOINT",
    "TPEX_INSTITUTIONAL_FLOW_SOURCE",
    "TWSE_INSTITUTIONAL_FLOW_ENDPOINT",
    "TWSE_INSTITUTIONAL_FLOW_SOURCE",
    "InstitutionalFlowContractError",
    "MarketInstitutionalFlowResult",
    "fetch_official_market_institutional_flows",
    "parse_tpex_institutional_flow",
    "parse_twse_institutional_flow",
    "persist_market_institutional_flows",
]
