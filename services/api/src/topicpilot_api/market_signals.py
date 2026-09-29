# ruff: noqa: E501, RUF001
"""Deterministic Today Market Signal V1 evaluation.

This module is the single executable authority for the frozen sixteen-signal
catalog.  It accepts already-authorized Home, Topic, turnover, and
institutional facts; it never fetches providers and it never treats missing
formal facts as a negative observation.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from decimal import InvalidOperation
from statistics import median
from typing import Any

FORMAL_STATUSES = frozenset({"AVAILABLE", "PUBLISHED", "FORMAL"})
SIGNAL_ACTIVE = "ACTIVE"
SIGNAL_INACTIVE = "INACTIVE"
SIGNAL_NOT_EVALUABLE = "NOT_EVALUABLE"

SIGNAL_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "signalId": "INDEX_MARKET_DIVERGENCE",
        "signalFamily": "INDEX_STRUCTURE",
        "title": "雙盤分家",
        "condition": "opposite index return signs OR index return spread >= 1.0pp",
        "direction": "Neutral / Watch",
        "description": "加權與櫃買市場不同步。",
        "displayOrder": 1,
    },
    {
        "signalId": "INDEX_BOTH_STRONG",
        "signalFamily": "INDEX_STRUCTURE",
        "title": "雙盤齊揚",
        "condition": "TPE return >= +0.5% and TWO return >= +0.5%, without divergence",
        "direction": "Bullish / Watch",
        "description": "權值與中小型市場同步偏強。",
        "displayOrder": 2,
    },
    {
        "signalId": "INDEX_BOTH_WEAK",
        "signalFamily": "INDEX_STRUCTURE",
        "title": "雙盤走弱",
        "condition": "TPE return <= -0.5% and TWO return <= -0.5%, without divergence",
        "direction": "Bearish / Watch",
        "description": "權值與中小型市場同步偏弱。",
        "displayOrder": 3,
    },
    {
        "signalId": "BREADTH_RED_INDEX_DISCONNECT",
        "signalFamily": "MARKET_BREADTH",
        "title": "紅盤失隊",
        "condition": "TPE return >= +0.3% and positive breadth <= 40%",
        "direction": "Watch",
        "description": "指數上漲但廣泛個股參與不足。",
        "displayOrder": 4,
    },
    {
        "signalId": "BREADTH_BROAD_ADVANCE",
        "signalFamily": "MARKET_BREADTH",
        "title": "全面開花",
        "condition": "positive breadth >= 70%",
        "direction": "Bullish / Watch",
        "description": "多數股票參與上漲。",
        "displayOrder": 5,
    },
    {
        "signalId": "BREADTH_DECLINERS_DOMINATE",
        "signalFamily": "MARKET_BREADTH",
        "title": "跌多漲少",
        "condition": "negative breadth >= 60%",
        "direction": "Bearish / Watch",
        "description": "下跌股票占比偏高。",
        "displayOrder": 6,
    },
    {
        "signalId": "BREADTH_UPSIDE_EXPANSION",
        "signalFamily": "MARKET_BREADTH",
        "title": "上漲擴散",
        "condition": "positive breadth delta >= +15pp and today >= 50%",
        "direction": "Bullish / Watch",
        "description": "上漲參與範圍較前一交易日明顯擴大。",
        "displayOrder": 7,
    },
    {
        "signalId": "BREADTH_DOWNSIDE_EXPANSION",
        "signalFamily": "MARKET_BREADTH",
        "title": "下跌擴散",
        "condition": "negative breadth delta >= +15pp and today >= 50%",
        "direction": "Bearish / Watch",
        "description": "下跌參與範圍較前一交易日明顯擴大。",
        "displayOrder": 8,
    },
    {
        "signalId": "TOPIC_CONCENTRATION",
        "signalFamily": "TOPIC_BREADTH_STRUCTURE",
        "title": "題材集中",
        "condition": "evaluable topics >= 5, positive topics >= 2, top-3 share >= 65%",
        "direction": "Watch",
        "description": "正向強度集中於少數題材。",
        "displayOrder": 9,
    },
    {
        "signalId": "TOPIC_EXPANSION",
        "signalFamily": "TOPIC_BREADTH_STRUCTURE",
        "title": "題材擴散",
        "condition": "evaluable topics >= 5 and positive topic ratio >= 60%",
        "direction": "Bullish / Watch",
        "description": "多數可評估題材同步走強。",
        "displayOrder": 10,
    },
    {
        "signalId": "TOPIC_DISPERSION",
        "signalFamily": "TOPIC_BREADTH_STRUCTURE",
        "title": "題材分化",
        "condition": "evaluable topics >= 5, IQR >= 2.0pp, strong >= 2, weak >= 2",
        "direction": "Watch",
        "description": "題材強弱差距明顯。",
        "displayOrder": 11,
    },
    {
        "signalId": "MARKET_VOLUME_PRICE_ADVANCE",
        "signalFamily": "MARKET_PARTICIPATION",
        "title": "量價齊揚",
        "condition": "whole-market turnover ratio >= 1.15 and both indices >= +0.5%",
        "direction": "Bullish / Watch",
        "description": "全市場成交金額放大且雙市場同步上漲。",
        "displayOrder": 12,
    },
    {
        "signalId": "MARKET_VOLUME_PRICE_DECLINE",
        "signalFamily": "MARKET_PARTICIPATION",
        "title": "量增價跌",
        "condition": "whole-market turnover ratio >= 1.15 and both indices <= -0.5%",
        "direction": "Bearish / Watch",
        "description": "全市場成交金額放大且雙市場同步下跌。",
        "displayOrder": 13,
    },
    {
        "signalId": "INSTITUTIONAL_SUPPORT",
        "signalFamily": "INSTITUTIONAL_STRUCTURE",
        "title": "法人助攻",
        "condition": "foreign ratio >= +0.20% and investment-trust ratio >= +0.20%",
        "direction": "Bullish / Watch",
        "description": "外資與投信同步站在買方。",
        "displayOrder": 14,
    },
    {
        "signalId": "INSTITUTIONAL_HEADWIND",
        "signalFamily": "INSTITUTIONAL_STRUCTURE",
        "title": "法人逆風",
        "condition": "foreign ratio <= -0.20% and investment-trust ratio <= -0.20%",
        "direction": "Bearish / Watch",
        "description": "外資與投信同步站在賣方。",
        "displayOrder": 15,
    },
    {
        "signalId": "INSTITUTIONAL_DIVERGENCE",
        "signalFamily": "INSTITUTIONAL_STRUCTURE",
        "title": "法人分歧",
        "condition": "foreign and investment-trust ratios have opposite signs and one is >= 0.20% in absolute value",
        "direction": "Watch",
        "description": "外資與投信方向不同步。",
        "displayOrder": 16,
    },
)

_CATALOG_BY_ID = {item["signalId"]: item for item in SIGNAL_CATALOG}
_FREQUENCY_TEMPLATES: dict[str, tuple[tuple[int, int | None, str, str], ...]] = {
    "INDEX_MARKET_DIVERGENCE": (
        (1, 3, "LOW", "近20日僅發生 {count} 日，雙市場分化目前較少見。"),
        (4, 6, "NORMAL", "近20日發生 {count} 日，近期權值與中小型股偶有風格分歧。"),
        (7, 9, "HIGH", "近20日發生 {count} 日，近期雙市場分化較為頻繁，盤面風格輪動明顯。"),
        (10, None, "VERY_HIGH", "近20日發生 {count} 日，權值與中小型市場長時間不同步，市場結構呈現高度分化。"),
    ),
    "INDEX_BOTH_STRONG": (
        (1, 2, "LOW", "近20日僅發生 {count} 日，近期雙市場同步走強的情況較少。"),
        (3, 5, "NORMAL", "近20日發生 {count} 日，雙市場偶有同步走強，但尚未形成高頻狀態。"),
        (6, 8, "HIGH", "近20日發生 {count} 日，近期雙市場同步走強的情況明顯增加。"),
        (9, None, "VERY_HIGH", "近20日發生 {count} 日，近期雙市場經常同步偏強，市場多方結構延續性較高。"),
    ),
    "INDEX_BOTH_WEAK": (
        (1, 2, "LOW", "近20日僅發生 {count} 日，近期雙市場同步走弱的情況不多。"),
        (3, 5, "NORMAL", "近20日發生 {count} 日，近期市場偶有全面性壓力。"),
        (6, 8, "HIGH", "近20日發生 {count} 日，近期雙市場同步走弱的情況明顯增加。"),
        (9, None, "VERY_HIGH", "近20日發生 {count} 日，雙市場弱勢頻繁出現，近期市場承壓狀況值得持續留意。"),
    ),
    "BREADTH_RED_INDEX_DISCONNECT": (
        (1, 2, "LOW", "近20日僅發生 {count} 日，近期指數與個股體感背離較少。"),
        (3, 5, "NORMAL", "近20日發生 {count} 日，近期偶有指數上漲但個股未跟進的情況。"),
        (6, 8, "HIGH", "近20日發生 {count} 日，近期紅盤失隊較為頻繁，行情集中度偏高。"),
        (9, None, "VERY_HIGH", "近20日發生 {count} 日，近期指數與個股表現經常脫節，盤面集中於少數強勢股的情況明顯。"),
    ),
    "BREADTH_BROAD_ADVANCE": (
        (1, 2, "LOW", "近20日僅發生 {count} 日，近期全面性上漲較少見。"),
        (3, 5, "NORMAL", "近20日發生 {count} 日，近期市場偶有廣泛上漲。"),
        (6, 8, "HIGH", "近20日發生 {count} 日，近期全面性上漲明顯增加，多方廣度較佳。"),
        (9, None, "VERY_HIGH", "近20日發生 {count} 日，近期多數交易日都有廣泛上漲，市場多方參與度偏高。"),
    ),
    "BREADTH_DECLINERS_DOMINATE": (
        (1, 3, "LOW", "近20日發生 {count} 日，近期跌多漲少的情況不常見。"),
        (4, 6, "NORMAL", "近20日發生 {count} 日，近期市場偶有個股普遍承壓。"),
        (7, 9, "HIGH", "近20日發生 {count} 日，近期跌多漲少較為頻繁，個股體感偏弱。"),
        (10, None, "VERY_HIGH", "近20日發生 {count} 日，近期多數交易日個股跌多漲少，市場弱勢廣度偏高。"),
    ),
    "BREADTH_UPSIDE_EXPANSION": (
        (1, 2, "LOW", "近20日僅發生 {count} 日，近期上漲廣度明顯擴張的情況較少。"),
        (3, 5, "NORMAL", "近20日發生 {count} 日，近期市場偶有多方參與快速擴大的情況。"),
        (6, 8, "HIGH", "近20日發生 {count} 日，近期上漲廣度擴張較為頻繁，市場輪動活躍。"),
        (9, None, "VERY_HIGH", "近20日發生 {count} 日，近期多方參與範圍經常快速擴大，市場廣度變化活躍。"),
    ),
    "BREADTH_DOWNSIDE_EXPANSION": (
        (1, 2, "LOW", "近20日僅發生 {count} 日，近期賣壓快速擴散的情況較少。"),
        (3, 5, "NORMAL", "近20日發生 {count} 日，近期市場偶有下跌廣度快速擴大的情況。"),
        (6, 8, "HIGH", "近20日發生 {count} 日，近期賣壓擴散較為頻繁，需留意弱勢擴大的情況。"),
        (9, None, "VERY_HIGH", "近20日發生 {count} 日，近期下跌廣度經常快速擴大，市場風險偏好持續不穩。"),
    ),
    "TOPIC_CONCENTRATION": (
        (1, 3, "LOW", "近20日僅發生 {count} 日，近期行情集中於少數題材的情況不多。"),
        (4, 6, "NORMAL", "近20日發生 {count} 日，近期偶有資金集中於少數主線。"),
        (7, 9, "HIGH", "近20日發生 {count} 日，近期題材集中較為頻繁，資金偏向少數強勢主線。"),
        (10, None, "VERY_HIGH", "近20日發生 {count} 日，近期行情長時間集中在少數題材，非主線參與度偏低。"),
    ),
    "TOPIC_EXPANSION": (
        (1, 2, "LOW", "近20日僅發生 {count} 日，近期多題材同步走強的情況較少。"),
        (3, 5, "NORMAL", "近20日發生 {count} 日，近期偶有多題材共同轉強。"),
        (6, 8, "HIGH", "近20日發生 {count} 日，近期題材擴散較為頻繁，市場參與範圍較廣。"),
        (9, None, "VERY_HIGH", "近20日發生 {count} 日，近期多數交易日都有多題材參與，盤面輪動與廣度明顯提升。"),
    ),
    "TOPIC_DISPERSION": (
        (1, 3, "LOW", "近20日僅發生 {count} 日，近期題材強弱差距大多不明顯。"),
        (4, 6, "NORMAL", "近20日發生 {count} 日，近期偶有題材強弱分化。"),
        (7, 9, "HIGH", "近20日發生 {count} 日，近期題材分化較為頻繁，資金選擇性明顯提高。"),
        (10, None, "VERY_HIGH", "近20日發生 {count} 日，近期題材強弱長時間分化，市場風格輪動與選擇性都偏高。"),
    ),
    "MARKET_VOLUME_PRICE_ADVANCE": (
        (1, 2, "LOW", "近20日僅發生 {count} 日，近期帶量上漲的情況較少。"),
        (3, 5, "NORMAL", "近20日發生 {count} 日，近期偶有量價同步走強。"),
        (6, 8, "HIGH", "近20日發生 {count} 日，近期量價齊揚較為頻繁，市場多方參與度明顯提高。"),
        (9, None, "VERY_HIGH", "近20日發生 {count} 日，近期帶量上漲經常出現，市場交易活躍且多方參與延續性偏高。"),
    ),
    "MARKET_VOLUME_PRICE_DECLINE": (
        (1, 2, "LOW", "近20日僅發生 {count} 日，近期帶量下跌的情況較少。"),
        (3, 5, "NORMAL", "近20日發生 {count} 日，近期偶有放量下跌，需留意市場賣壓。"),
        (6, 8, "HIGH", "近20日發生 {count} 日，近期量增價跌較為頻繁，市場賣壓參與程度偏高。"),
        (9, None, "VERY_HIGH", "近20日發生 {count} 日，近期帶量下跌經常出現，市場承壓與交易風險明顯提高。"),
    ),
    "INSTITUTIONAL_SUPPORT": (
        (1, 3, "LOW", "近20日僅發生 {count} 日，近期外資與投信同步偏多的情況不多。"),
        (4, 6, "NORMAL", "近20日發生 {count} 日，近期偶有法人同步站在買方。"),
        (7, 9, "HIGH", "近20日發生 {count} 日，近期法人同步偏多較為頻繁，可持續留意外資與投信共同加碼的個股與題材。"),
        (10, None, "VERY_HIGH", "近20日發生 {count} 日，近期外資與投信長時間同步偏多，法人籌碼方向一致性偏高。"),
    ),
    "INSTITUTIONAL_HEADWIND": (
        (1, 3, "LOW", "近20日僅發生 {count} 日，近期法人同步賣超的情況不多。"),
        (4, 6, "NORMAL", "近20日發生 {count} 日，近期偶有外資與投信共同偏空。"),
        (7, 9, "HIGH", "近20日發生 {count} 日，近期法人同步賣超較為頻繁，需留意籌碼壓力延續。"),
        (10, None, "VERY_HIGH", "近20日發生 {count} 日，近期外資與投信長時間同步偏空，法人籌碼壓力明顯偏高。"),
    ),
    "INSTITUTIONAL_DIVERGENCE": (
        (1, 3, "LOW", "近20日僅發生 {count} 日，近期法人方向分歧的情況不多。"),
        (4, 6, "NORMAL", "近20日發生 {count} 日，近期偶有外資與投信不同步。"),
        (7, 9, "HIGH", "近20日發生 {count} 日，近期法人分歧較為頻繁，籌碼方向一致性偏低。"),
        (10, None, "VERY_HIGH", "近20日發生 {count} 日，近期外資與投信長時間不同步，法人資金呈現高度分歧。"),
    ),
}


def catalog_payload() -> list[dict[str, Any]]:
    """Return a defensive, JSON-safe copy of the frozen catalog."""

    return [
        {
            **item,
            "key": item["signalId"],
            "name": item["title"],
            "frequencyBands": [
                {"minimum": low, "maximum": high, "band": band}
                for low, high, band, _message in _FREQUENCY_TEMPLATES[item["signalId"]]
            ],
        }
        for item in SIGNAL_CATALOG
    ]


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, InvalidOperation):
        return None
    return number if number == number and abs(number) != float("inf") else None


def _as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _formal(value: Any) -> bool:
    return str(value or "").upper() in FORMAL_STATUSES


def _index_returns(overview: Mapping[str, Any]) -> dict[str, float] | None:
    values: dict[str, float] = {}
    for item in overview.get("indices") or []:
        if not isinstance(item, Mapping) or not _formal(item.get("status")):
            continue
        value = _number(item.get("changePct"))
        if value is not None and str(item.get("market")) in {"TPE", "TWO"}:
            values[str(item["market"])] = value
    return values if set(values) == {"TPE", "TWO"} else None


def _breadth(overview: Mapping[str, Any]) -> dict[str, float] | None:
    health = overview.get("marketHealth")
    if not isinstance(health, Mapping):
        health = {}
    eligible = _number(health.get("breadthEligible"))
    positive = _number(health.get("advance"))
    negative = _number(health.get("decline"))
    flat = _number(health.get("flat"))
    rows = [item for item in overview.get("breadth") or [] if isinstance(item, Mapping)]
    if eligible is None and positive is not None and negative is not None and flat is not None:
        eligible = positive + negative + flat
    if eligible is None or positive is None or negative is None or flat is None:
        available_rows = [item for item in rows if _formal(item.get("status", "AVAILABLE"))]
        eligible = sum(_number(item.get("eligible")) or 0 for item in available_rows)
        positive = sum(_number(item.get("advance", item.get("advancers"))) or 0 for item in available_rows)
        negative = sum(_number(item.get("decline", item.get("decliners"))) or 0 for item in available_rows)
        flat = sum(_number(item.get("flat", item.get("unchanged"))) or 0 for item in available_rows)
    if eligible <= 0 or positive < 0 or negative < 0 or flat < 0 or positive + negative + flat != eligible:
        return None
    return {
        "eligible_count": eligible,
        "positive_count": positive,
        "negative_count": negative,
        "flat_count": flat,
        "positive_breadth_pct": positive / eligible * 100,
        "negative_breadth_pct": negative / eligible * 100,
    }


def _turnover(overview: Mapping[str, Any]) -> float | None:
    legs: dict[str, float] = {}
    total: float | None = None
    for item in overview.get("turnover") or []:
        if not isinstance(item, Mapping) or not _formal(item.get("status")):
            continue
        market = str(item.get("market") or "")
        value = _number(item.get("value"))
        if value is None or value <= 0:
            continue
        if market in {"TPE", "TWO"}:
            legs[market] = value
        elif market == "TOTAL":
            total = value
    if set(legs) == {"TPE", "TWO"} and total is not None:
        return total
    return None


def _topic_metrics(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        topic_key = str(row.get("topic_id") or row.get("topicId") or row.get("topic_slug") or row.get("topicSlug") or "")
        if not topic_key:
            continue
        trading_date = _as_date(row.get("trading_date") or row.get("tradingDate") or row.get("snapshot_date") or row.get("snapshotDate"))
        if trading_date is None:
            trading_date = date.min
        key = (trading_date.isoformat(), topic_key)
        item = grouped.setdefault(
            key,
            {
                "topic_id": topic_key,
                "topic_slug": row.get("topic_slug", row.get("topicSlug")),
                "topic_name": row.get("topic_name", row.get("topicName")),
                "trading_date": trading_date,
                "formal_member_count": _number(row.get("formal_member_count", row.get("formalMemberCount", row.get("stock_count", row.get("stockCount"))))),
                "core_returns": [],
            },
        )
        if item["formal_member_count"] is None:
            item["formal_member_count"] = _number(row.get("formal_member_count", row.get("formalMemberCount")))
        if isinstance(row.get("core_returns"), Sequence) and not isinstance(row.get("core_returns"), (str, bytes)):
            item["core_returns"].extend(value for value in (_number(v) for v in row["core_returns"]) if value is not None)
        elif str(row.get("structural_role") or row.get("structuralRole") or "").upper() == "CORE" and str(row.get("fact_state") or row.get("factState") or "OBSERVED").upper() == "OBSERVED":
            value = _number(row.get("change_pct", row.get("changePct", row.get("topic_strength_raw", row.get("topicStrengthRaw")))))
            if value is not None:
                item["core_returns"].append(value)
        elif row.get("topic_strength_raw", row.get("topicStrengthRaw")) is not None:
            value = _number(row.get("topic_strength_raw", row.get("topicStrengthRaw")))
            if value is not None:
                item["core_returns"].append(value)

    result: dict[str, dict[str, Any]] = {}
    for item in grouped.values():
        member_count = item["formal_member_count"]
        returns = item["core_returns"]
        if member_count is None or member_count < 3 or not returns:
            continue
        positive = sum(value > 0 for value in returns)
        strong = sum(value >= 2.0 for value in returns)
        result[f"{item['trading_date'].isoformat()}::{item['topic_id']}"] = {
            "topic_id": item["topic_id"],
            "topic_slug": item["topic_slug"],
            "topic_name": item["topic_name"],
            "trading_date": item["trading_date"],
            "formal_member_count": int(member_count),
            "core_member_count": len(returns),
            "core_median_return_pct": median(returns),
            "core_positive_breadth_pct": positive / len(returns) * 100,
            "core_strong_breadth_pct": strong / len(returns) * 100,
        }
    return result


def _topic_metrics_for_date(rows: Iterable[Mapping[str, Any]], target_date: date | None) -> list[dict[str, Any]]:
    metrics = _topic_metrics(rows)
    return [
        item for item in metrics.values()
        if target_date is None or item["trading_date"] == target_date
    ]


def _flow_ratio(overview: Mapping[str, Any]) -> tuple[float, float] | None:
    flows = overview.get("institutionFlows")
    if not isinstance(flows, Mapping) or str(flows.get("status") or "").upper() != "AVAILABLE":
        return None
    markets = flows.get("markets")
    if not isinstance(markets, list):
        return None
    by_market = {str(item.get("market")): item for item in markets if isinstance(item, Mapping)}
    if set(by_market) != {"TPE", "TWO"}:
        return None
    dates: set[date] = set()
    foreign_total = 0.0
    trust_total = 0.0
    for market in ("TPE", "TWO"):
        item = by_market[market]
        if str(item.get("availability") or "").upper() != "AVAILABLE":
            return None
        row_date = _as_date(item.get("asOfDate"))
        if row_date is not None:
            dates.add(row_date)
        current = item.get("current")
        if not isinstance(current, Mapping):
            return None
        foreign = current.get("foreign")
        trust = current.get("investmentTrust")
        foreign_value = _number(foreign.get("net")) if isinstance(foreign, Mapping) else None
        trust_value = _number(trust.get("net")) if isinstance(trust, Mapping) else None
        if foreign_value is None or trust_value is None:
            return None
        foreign_total += foreign_value
        trust_total += trust_value
    turnover = _turnover(overview)
    if turnover is None or turnover <= 0 or len(dates) > 1:
        return None
    return foreign_total / turnover * 100, trust_total / turnover * 100


def _overview_from_session(session: Mapping[str, Any]) -> Mapping[str, Any]:
    nested = session.get("marketOverview")
    return nested if isinstance(nested, Mapping) else session


def _session_date(session: Mapping[str, Any]) -> date | None:
    overview = _overview_from_session(session)
    return _as_date(session.get("tradingDate") or session.get("trading_date") or overview.get("dataDate") or overview.get("tradingDate"))


def _topic_rows_from_session(session: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    rows = session.get("topicObservations") or session.get("topic_observations") or ()
    return rows if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) else ()


def _base_record(item: Mapping[str, Any], status: str, *, summary: str, evidence: list[str], detail: Mapping[str, Any], trading_date: date | None) -> dict[str, Any]:
    signal_id = str(item["signalId"])
    severity = "WARNING" if signal_id in {"BREADTH_DECLINERS_DOMINATE", "BREADTH_DOWNSIDE_EXPANSION", "MARKET_VOLUME_PRICE_DECLINE", "INSTITUTIONAL_HEADWIND"} else "WATCH"
    return {
        "signalId": signal_id,
        "signalFamily": item["signalFamily"],
        "title": item["title"],
        "key": signal_id,
        "name": item["title"],
        "isActive": status == SIGNAL_ACTIVE,
        "signalStatus": status,
        "signalTemporalStatus": "NOT_EVALUABLE" if status == SIGNAL_NOT_EVALUABLE else "INACTIVE",
        "streakDays": None,
        "occurrenceDays20d": None,
        "frequencyStatus": "INSUFFICIENT_HISTORY",
        "frequencyBand": None,
        "frequencyMessage": None,
        "summary": summary,
        "tradingDate": trading_date,
        "evidence": evidence,
        "evidenceDetail": dict(detail),
        "authorityStatus": "FORMAL" if status != SIGNAL_NOT_EVALUABLE else "INSUFFICIENT_FORMAL_DATA",
        "evaluationStatus": status,
        "severity": severity,
        "direction": item["direction"],
        "interpretation": summary,
    }


def _evaluate_one(
    overview: Mapping[str, Any],
    *,
    previous_overview: Mapping[str, Any] | None,
    previous_turnovers: Sequence[float],
    topic_rows: Sequence[Mapping[str, Any]],
    trading_date: date | None,
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    indices = _index_returns(overview)
    breadth = _breadth(overview)
    previous_breadth = _breadth(previous_overview) if previous_overview is not None else None
    topic_metrics = _topic_metrics_for_date(topic_rows, trading_date)
    flow_ratios = _flow_ratio(overview)
    current_turnover = _turnover(overview)
    turnover_ratio = None
    if current_turnover is not None and len(previous_turnovers) >= 20:
        baseline = median(previous_turnovers[:20])
        if baseline > 0:
            turnover_ratio = current_turnover / baseline

    def add(signal_id: str, active: bool, *, evaluable: bool = True, summary: str = "", evidence: list[str] | None = None, detail: Mapping[str, Any] | None = None) -> None:
        records[signal_id] = _base_record(
            _CATALOG_BY_ID[signal_id],
            SIGNAL_NOT_EVALUABLE if not evaluable else SIGNAL_ACTIVE if active else SIGNAL_INACTIVE,
            summary=summary,
            evidence=evidence or [],
            detail=detail or {},
            trading_date=trading_date,
        )

    # Index Structure is intentionally evaluated in precedence order.
    divergence = None
    if indices is not None:
        tpe, two = indices["TPE"], indices["TWO"]
        spread = abs(tpe - two)
        divergence = (tpe > 0 > two) or (two > 0 > tpe) or spread >= 1.0
        dominant = "TPE" if tpe > two else "TWO" if two > tpe else "BALANCED"
        index_detail = {"tpeReturnPct": tpe, "twoReturnPct": two, "spreadPp": spread, "dominantMarket": dominant}
        if divergence:
            lead = "加權明顯強於櫃買" if tpe > two else "櫃買明顯強於加權" if two > tpe else "兩市場報酬差距達到門檻"
            add("INDEX_MARKET_DIVERGENCE", True, summary=f"{lead}，雙市場報酬差 {spread:.2f} 個百分點。", evidence=[f"加權 {tpe:+.2f}%", f"櫃買 {two:+.2f}%"], detail=index_detail)
            add("INDEX_BOTH_STRONG", False, summary="雙盤分家優先於同步強勢判定。", detail=index_detail)
            add("INDEX_BOTH_WEAK", False, summary="雙盤分家優先於同步弱勢判定。", detail=index_detail)
        else:
            add("INDEX_MARKET_DIVERGENCE", False, summary="今日雙市場報酬差距未達分家條件。", detail=index_detail)
            add("INDEX_BOTH_STRONG", tpe >= 0.5 and two >= 0.5, summary="加權與櫃買同步偏強。" if tpe >= 0.5 and two >= 0.5 else "雙市場未同時達到同步偏強門檻。", evidence=[f"加權 {tpe:+.2f}%", f"櫃買 {two:+.2f}%"], detail=index_detail)
            add("INDEX_BOTH_WEAK", tpe <= -0.5 and two <= -0.5, summary="加權與櫃買同步偏弱。" if tpe <= -0.5 and two <= -0.5 else "雙市場未同時達到同步偏弱門檻。", evidence=[f"加權 {tpe:+.2f}%", f"櫃買 {two:+.2f}%"], detail=index_detail)
    else:
        for signal_id in ("INDEX_MARKET_DIVERGENCE", "INDEX_BOTH_STRONG", "INDEX_BOTH_WEAK"):
            add(signal_id, False, evaluable=False, summary="正式 TPE／TWO 報酬資料不足，無法判定。")

    if breadth is not None:
        positive = breadth["positive_breadth_pct"]
        negative = breadth["negative_breadth_pct"]
        breadth_detail = {key: round(value, 4) for key, value in breadth.items()}
        tpe = indices["TPE"] if indices is not None else None
        add("BREADTH_RED_INDEX_DISCONNECT", tpe is not None and tpe >= 0.3 and positive <= 40, summary="指數上漲但廣度偏弱。" if tpe is not None and tpe >= 0.3 and positive <= 40 else "今日未符合紅盤失隊條件。", evidence=[f"上漲廣度 {positive:.2f}%"], detail={**breadth_detail, "tpeReturnPct": tpe})
        add("BREADTH_BROAD_ADVANCE", positive >= 70, summary="多數股票參與上漲。" if positive >= 70 else "上漲股票占比未達全面開花門檻。", evidence=[f"上漲廣度 {positive:.2f}%"], detail=breadth_detail)
        add("BREADTH_DECLINERS_DOMINATE", negative >= 60, summary="下跌股票占比偏高。" if negative >= 60 else "下跌股票占比未達跌多漲少門檻。", evidence=[f"下跌廣度 {negative:.2f}%"], detail=breadth_detail)
        if previous_breadth is not None:
            positive_delta = positive - previous_breadth["positive_breadth_pct"]
            negative_delta = negative - previous_breadth["negative_breadth_pct"]
            add("BREADTH_UPSIDE_EXPANSION", positive_delta >= 15 and positive >= 50, summary="上漲廣度較前一交易日明顯擴大。" if positive_delta >= 15 and positive >= 50 else "上漲廣度未符合擴散條件。", evidence=[f"上漲廣度 {positive:.2f}%（前日 {previous_breadth['positive_breadth_pct']:.2f}%）"], detail={**breadth_detail, "positiveBreadthDeltaPp": positive_delta})
            add("BREADTH_DOWNSIDE_EXPANSION", negative_delta >= 15 and negative >= 50, summary="下跌廣度較前一交易日明顯擴大。" if negative_delta >= 15 and negative >= 50 else "下跌廣度未符合擴散條件。", evidence=[f"下跌廣度 {negative:.2f}%（前日 {previous_breadth['negative_breadth_pct']:.2f}%）"], detail={**breadth_detail, "negativeBreadthDeltaPp": negative_delta})
        else:
            for signal_id in ("BREADTH_UPSIDE_EXPANSION", "BREADTH_DOWNSIDE_EXPANSION"):
                add(signal_id, False, evaluable=False, summary="前一個正式交易日的市場廣度不可用，無法判定擴散。", detail=breadth_detail)
    else:
        for signal_id in ("BREADTH_RED_INDEX_DISCONNECT", "BREADTH_BROAD_ADVANCE", "BREADTH_DECLINERS_DOMINATE", "BREADTH_UPSIDE_EXPANSION", "BREADTH_DOWNSIDE_EXPANSION"):
            add(signal_id, False, evaluable=False, summary="正式全市場廣度資料不足，無法判定。")

    if len(topic_metrics) >= 5:
        strengths = sorted(max(float(item["core_median_return_pct"]), 0.0) for item in topic_metrics)
        positive_strengths = [value for value in strengths if value > 0]
        positive_topic_count = len(positive_strengths)
        positive_total = sum(positive_strengths)
        top3_share = sum(positive_strengths[-3:]) / positive_total * 100 if positive_total > 0 else 0.0
        dominant_share = positive_strengths[-1] / positive_total * 100 if positive_total > 0 else 0.0
        positive_topic_count_expansion = sum(item["core_median_return_pct"] >= 1.0 and item["core_positive_breadth_pct"] >= 55 for item in topic_metrics)
        positive_ratio = positive_topic_count_expansion / len(topic_metrics) * 100
        values = sorted(float(item["core_median_return_pct"]) for item in topic_metrics)
        p25 = _percentile(values, 0.25)
        p75 = _percentile(values, 0.75)
        iqr = p75 - p25
        strong_count = sum(value >= 1.5 for value in values)
        weak_count = sum(value <= -1.0 for value in values)
        topic_detail = {"evaluableFormalTopicCount": len(topic_metrics), "positiveTopicCount": positive_topic_count, "top3PositiveStrengthShare": top3_share, "dominantTopicShare": dominant_share, "positiveTopicRatio": positive_ratio, "topicP25": p25, "topicP75": p75, "topicDispersionIqr": iqr, "strongTopicCount": strong_count, "weakTopicCount": weak_count}
        add("TOPIC_CONCENTRATION", positive_topic_count >= 2 and top3_share >= 65, summary="正向題材強度集中於少數主線。" if positive_topic_count >= 2 and top3_share >= 65 else "正向題材集中度未達門檻。", evidence=[f"前 3 大正向強度占比 {top3_share:.2f}%"], detail=topic_detail)
        add("TOPIC_EXPANSION", positive_ratio >= 60, summary="多數可評估題材同步走強。" if positive_ratio >= 60 else "同步走強的題材比例未達門檻。", evidence=[f"正向題材比例 {positive_ratio:.2f}%"], detail=topic_detail)
        add("TOPIC_DISPERSION", iqr >= 2.0 and strong_count >= 2 and weak_count >= 2, summary="題材強弱差距明顯。" if iqr >= 2.0 and strong_count >= 2 and weak_count >= 2 else "題材強弱分化未同時達到門檻。", evidence=[f"題材 IQR {iqr:.2f} 個百分點", f"強勢題材 {strong_count}、弱勢題材 {weak_count}"], detail=topic_detail)
    else:
        for signal_id in ("TOPIC_CONCENTRATION", "TOPIC_EXPANSION", "TOPIC_DISPERSION"):
            add(signal_id, False, evaluable=False, summary="可評估的正式題材少於 5 個，題材廣度結構暫不評估.", detail={"evaluableFormalTopicCount": len(topic_metrics)})

    if indices is not None and turnover_ratio is not None and divergence is False:
        tpe, two = indices["TPE"], indices["TWO"]
        turnover_detail = {"wholeMarketTurnover": current_turnover, "turnoverBaselineMedianPrevious20": median(previous_turnovers[:20]), "turnoverRatio20d": turnover_ratio, "turnoverBand": _turnover_band(turnover_ratio)}
        add("MARKET_VOLUME_PRICE_ADVANCE", turnover_ratio >= 1.15 and tpe >= 0.5 and two >= 0.5, summary="全市場成交金額放大且雙市場同步上漲。" if turnover_ratio >= 1.15 and tpe >= 0.5 and two >= 0.5 else "今日未同時符合量價齊揚條件。", evidence=[f"20 日量能比 {turnover_ratio:.2f}"], detail=turnover_detail)
        add("MARKET_VOLUME_PRICE_DECLINE", turnover_ratio >= 1.15 and tpe <= -0.5 and two <= -0.5, summary="全市場成交金額放大且雙市場同步下跌。" if turnover_ratio >= 1.15 and tpe <= -0.5 and two <= -0.5 else "今日未同時符合量增價跌條件。", evidence=[f"20 日量能比 {turnover_ratio:.2f}"], detail=turnover_detail)
    else:
        reason = "完整前 20 個正式交易日的全市場成交金額不足，無法判定。" if current_turnover is not None and len(previous_turnovers) < 20 else "正式 TPE、TPEx 成交金額或指數資料不足，無法判定。"
        for signal_id in ("MARKET_VOLUME_PRICE_ADVANCE", "MARKET_VOLUME_PRICE_DECLINE"):
            add(signal_id, False, evaluable=False, summary=reason)

    if flow_ratios is not None:
        foreign_ratio, trust_ratio = flow_ratios
        flow_detail = {"foreignFlowRatioPct": foreign_ratio, "investmentTrustFlowRatioPct": trust_ratio}
        add("INSTITUTIONAL_SUPPORT", foreign_ratio >= 0.20 and trust_ratio >= 0.20, summary="外資與投信同步站在買方，法人籌碼方向一致偏多。" if foreign_ratio >= 0.20 and trust_ratio >= 0.20 else "外資與投信未同時達到助攻門檻。", evidence=[f"外資 {foreign_ratio:+.2f}%", f"投信 {trust_ratio:+.2f}%"], detail=flow_detail)
        add("INSTITUTIONAL_HEADWIND", foreign_ratio <= -0.20 and trust_ratio <= -0.20, summary="外資與投信同步站在賣方，法人籌碼方向一致偏空。" if foreign_ratio <= -0.20 and trust_ratio <= -0.20 else "外資與投信未同時達到逆風門檻。", evidence=[f"外資 {foreign_ratio:+.2f}%", f"投信 {trust_ratio:+.2f}%"], detail=flow_detail)
        opposite = (foreign_ratio > 0 > trust_ratio) or (trust_ratio > 0 > foreign_ratio)
        if opposite:
            direction = "外資買／投信賣" if foreign_ratio > trust_ratio else "外資賣／投信買"
        else:
            direction = "法人方向未形成分歧"
        add("INSTITUTIONAL_DIVERGENCE", opposite and max(abs(foreign_ratio), abs(trust_ratio)) >= 0.20, summary=f"{direction}，法人資金方向不同步。" if opposite and max(abs(foreign_ratio), abs(trust_ratio)) >= 0.20 else "法人方向未同時符合分歧條件。", evidence=[f"外資 {foreign_ratio:+.2f}%", f"投信 {trust_ratio:+.2f}%"], detail=flow_detail)
    else:
        for signal_id in ("INSTITUTIONAL_SUPPORT", "INSTITUTIONAL_HEADWIND", "INSTITUTIONAL_DIVERGENCE"):
            add(signal_id, False, evaluable=False, summary="TWSE 與 TPEx 同日正式法人資料不足，無法判定。")

    return records


def _percentile(values: Sequence[float], quantile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return values[lower] + (values[upper] - values[lower]) * weight


def _turnover_band(ratio: float) -> str:
    if ratio < 0.80:
        return "LOW"
    if ratio < 1.15:
        return "NORMAL"
    if ratio < 1.40:
        return "EXPANDED"
    return "HIGHLY_EXPANDED"


def _frequency(count: int, signal_id: str) -> tuple[str, str]:
    for low, high, band, template in _FREQUENCY_TEMPLATES[signal_id]:
        if count >= low and (high is None or count <= high):
            return band, template.format(count=count)
    return "LOW", ""


def _session_contexts(current: Mapping[str, Any], history: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    combined = [current, *history]
    seen: set[date] = set()
    result: list[Mapping[str, Any]] = []
    for session in sorted(combined, key=lambda item: _session_date(item) or date.min, reverse=True):
        session_date = _session_date(session)
        if session_date is None or session_date in seen:
            continue
        seen.add(session_date)
        result.append(session)
    return result


def evaluate_v1_signals(
    market_overview: Mapping[str, Any],
    *,
    history: Sequence[Mapping[str, Any]] = (),
    topic_observations: Sequence[Mapping[str, Any]] = (),
    trading_date: date | None = None,
) -> list[dict[str, Any]]:
    """Evaluate every catalog entry, adding temporal and 20-session state."""

    current_date = trading_date or _as_date(market_overview.get("dataDate"))
    current = {"marketOverview": market_overview, "tradingDate": current_date, "topicObservations": topic_observations}
    sessions = _session_contexts(current, history)
    per_session: list[dict[str, dict[str, Any]]] = []
    for index, session in enumerate(sessions):
        overview = _overview_from_session(session)
        session_date = _session_date(session)
        previous_overview = _overview_from_session(sessions[index + 1]) if index + 1 < len(sessions) else None
        previous_turnovers = []
        for prior in sessions[index + 1:index + 21]:
            value = _turnover(_overview_from_session(prior))
            if value is None:
                break
            previous_turnovers.append(value)
        per_session.append(_evaluate_one(overview, previous_overview=previous_overview, previous_turnovers=previous_turnovers, topic_rows=_topic_rows_from_session(session), trading_date=session_date))

    if not per_session:
        per_session = [_evaluate_one(market_overview, previous_overview=None, previous_turnovers=[], topic_rows=topic_observations, trading_date=current_date)]
        sessions = [current]
    current_records = per_session[0]
    output: list[dict[str, Any]] = []
    for item in SIGNAL_CATALOG:
        signal_id = str(item["signalId"])
        record = dict(current_records[signal_id])
        current_status = record["signalStatus"]
        statuses = [rows[signal_id]["signalStatus"] for rows in per_session[:20]]
        complete_frequency = len(statuses) >= 20 and all(status != SIGNAL_NOT_EVALUABLE for status in statuses)
        if complete_frequency:
            occurrence = sum(status == SIGNAL_ACTIVE for status in statuses)
            record["occurrenceDays20d"] = occurrence
            record["frequencyStatus"] = "AVAILABLE"
            record["frequencyBand"], record["frequencyMessage"] = _frequency(occurrence, signal_id) if occurrence else ("LOW", None)
        if current_status == SIGNAL_ACTIVE:
            prior_statuses = [rows[signal_id]["signalStatus"] for rows in per_session[1:]]
            if not prior_statuses or prior_statuses[0] == SIGNAL_NOT_EVALUABLE:
                record["signalTemporalStatus"] = "INSUFFICIENT_HISTORY"
                record["streakDays"] = None
            else:
                record["signalTemporalStatus"] = "PERSISTING" if prior_statuses[0] == SIGNAL_ACTIVE else "NEW"
                streak = 1
                for status in prior_statuses:
                    if status != SIGNAL_ACTIVE:
                        break
                    streak += 1
                record["streakDays"] = streak
        elif current_status == SIGNAL_NOT_EVALUABLE:
            record["signalTemporalStatus"] = "NOT_EVALUABLE"
        else:
            record["signalTemporalStatus"] = "INACTIVE"
            record["streakDays"] = 0
        output.append(record)
    return output


def build_market_signals(
    market_overview: Mapping[str, Any],
    *,
    history: Sequence[Mapping[str, Any]] = (),
    topic_observations: Sequence[Mapping[str, Any]] = (),
    trading_date: date | None = None,
) -> list[dict[str, Any]]:
    """Return active V1 signals in stable catalog order."""

    return [
        signal
        for signal in evaluate_v1_signals(
            market_overview,
            history=history,
            topic_observations=topic_observations,
            trading_date=trading_date,
        )
        if signal["isActive"]
    ]


__all__ = ["SIGNAL_CATALOG", "build_market_signals", "catalog_payload", "evaluate_v1_signals"]
