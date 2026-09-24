"""Owner workbook proposal export and strict validation contract.

The canonical workbook surface is relation-granular while remaining one row
per stock for Owner usability. Topic lists and weight lists are positional
``|``-separated pairs. A legacy ``;`` separator is accepted on input only so
that an existing 001D proposal is not silently discarded during transition.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .relation_weight_authority import (
    RelationIdentity,
    RelationWeightError,
    RelationWeightIdentityError,
    RelationWeightProposal,
    parse_weight,
)

WORKBOOK_COLUMNS = (
    "symbol",
    "name",
    "market",
    "representative_topic",
    "primary_topics",
    "secondary_topics",
    "primary_weights",
    "secondary_weights",
    "effective_date",
    "reason",
    "evidence_note",
)
TOKEN_SEPARATOR = "|"
LEGACY_TOKEN_SEPARATOR = ";"


class WorkbookWeightValidationError(RelationWeightError):
    """Raised when an Owner workbook row is not a valid proposal input."""


@dataclass(frozen=True)
class ValidatedWorkbookRow:
    market: str
    symbol: str
    name: str
    representative_topic: str | None
    primary_topics: tuple[str, ...]
    secondary_topics: tuple[str, ...]
    primary_weights: tuple[Decimal, ...]
    secondary_weights: tuple[Decimal, ...]
    effective_date: str | None
    reason: str | None
    evidence_note: str | None

    @property
    def instrument(self) -> str:
        """Compatibility alias for the 001D relation identity vocabulary."""

        return self.symbol

    def identities(self) -> tuple[RelationIdentity, ...]:
        return (
            *(
                RelationIdentity(self.market, self.symbol, topic, "PRIMARY")
                for topic in self.primary_topics
            ),
            *(
                RelationIdentity(self.market, self.symbol, topic, "SECONDARY")
                for topic in self.secondary_topics
            ),
        )


def _value(row: Mapping[str, Any], key: str) -> Any:
    if key in row:
        return row[key]
    aliases = {
        "market": ("market_code", "marketCode"),
        "symbol": ("instrument", "instrument_code", "instrumentCode"),
        "name": ("stock_name", "stockName"),
        "representative_topic": ("representativeTopic",),
        "primary_topics": ("primaryTopics", "primary_topic", "primaryTopic"),
        "secondary_topics": ("secondaryTopics",),
        "primary_weights": ("primaryWeights", "primary_weight", "primaryWeight"),
        "secondary_weights": (
            "secondaryWeights",
            "secondary_weight",
            "secondaryWeight",
        ),
        "effective_date": ("effectiveDate", "effective_from", "effectiveFrom"),
        "evidence_note": ("evidenceNote", "validation_note", "validationNote"),
    }
    for alias in aliases.get(key, ()):
        if alias in row:
            return row[alias]
    return None


def _text(value: Any, field: str) -> str:
    if value is None:
        raise WorkbookWeightValidationError(f"{field} is required")
    text = str(value).strip()
    if not text:
        raise WorkbookWeightValidationError(f"{field} is required")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _tokens(
    value: Any,
    field: str,
    *,
    reject_duplicates: bool = True,
) -> tuple[str, ...]:
    if value is None or str(value).strip() == "":
        return ()
    raw = str(value)
    if "," in raw:
        raise WorkbookWeightValidationError(
            f"{field} must use strict positional '{TOKEN_SEPARATOR}' separators; "
            "comma tokens are invalid"
        )
    has_current = TOKEN_SEPARATOR in raw
    has_legacy = LEGACY_TOKEN_SEPARATOR in raw
    if has_current and has_legacy:
        raise WorkbookWeightValidationError(
            f"{field} must not mix '{TOKEN_SEPARATOR}' and "
            f"'{LEGACY_TOKEN_SEPARATOR}' separators"
        )
    separator = TOKEN_SEPARATOR if has_current else LEGACY_TOKEN_SEPARATOR
    tokens = tuple(token.strip() for token in raw.split(separator))
    if any(not token for token in tokens):
        raise WorkbookWeightValidationError(f"{field} contains a blank token")
    if reject_duplicates and len(set(tokens)) != len(tokens):
        raise WorkbookWeightValidationError(f"{field} contains duplicate Topic relations")
    return tokens


def validate_workbook_row(
    row: Mapping[str, Any],
    *,
    relation_universe: Iterable[RelationIdentity],
    topic_vocabulary: Iterable[str] | None = None,
) -> ValidatedWorkbookRow:
    """Validate one workbook row without coercing or filling values.

    Empty PRIMARY and SECONDARY lists are valid. This deliberately permits
    zero-topic instruments and does not infer a representative Topic.
    """

    market = _text(_value(row, "market"), "market")
    symbol = _text(_value(row, "symbol"), "symbol")
    name = str(_value(row, "name") or "").strip()
    representative_topic = _optional_text(_value(row, "representative_topic"))
    primary_topics = _tokens(_value(row, "primary_topics"), "primary_topics")
    secondary_topics = _tokens(_value(row, "secondary_topics"), "secondary_topics")
    primary_weight_tokens = _tokens(
        _value(row, "primary_weights"),
        "primary_weights",
        reject_duplicates=False,
    )
    secondary_weight_tokens = _tokens(
        _value(row, "secondary_weights"),
        "secondary_weights",
        reject_duplicates=False,
    )

    if len(primary_topics) != len(primary_weight_tokens):
        raise WorkbookWeightValidationError(
            "primary_topics and primary_weights count must match exactly"
        )
    if len(secondary_topics) != len(secondary_weight_tokens):
        raise WorkbookWeightValidationError(
            "secondary_topics and secondary_weights count must match exactly"
        )

    primary_weights = tuple(
        parse_weight(token, relation_type="PRIMARY") for token in primary_weight_tokens
    )
    secondary_weights = tuple(
        parse_weight(token, relation_type="SECONDARY") for token in secondary_weight_tokens
    )

    overlap = set(primary_topics).intersection(secondary_topics)
    if overlap:
        raise WorkbookWeightValidationError(
            "a Topic cannot be both PRIMARY and SECONDARY in one stock row"
        )
    if representative_topic and topic_vocabulary is not None:
        allowed_topics = {str(topic).strip() for topic in topic_vocabulary}
        if representative_topic not in allowed_topics:
            raise RelationWeightIdentityError(
                f"unknown representative Topic vocabulary: {representative_topic}"
            )

    expected = set(relation_universe)
    identities = (
        *(RelationIdentity(market, symbol, topic, "PRIMARY") for topic in primary_topics),
        *(
            RelationIdentity(market, symbol, topic, "SECONDARY")
            for topic in secondary_topics
        ),
    )
    missing = [identity for identity in identities if identity not in expected]
    if missing:
        raise RelationWeightIdentityError(f"unknown stock/Topic/relation identity: {missing[0]}")
    return ValidatedWorkbookRow(
        market=market,
        symbol=symbol,
        name=name,
        representative_topic=representative_topic,
        primary_topics=primary_topics,
        secondary_topics=secondary_topics,
        primary_weights=primary_weights,
        secondary_weights=secondary_weights,
        effective_date=_optional_text(_value(row, "effective_date")),
        reason=_optional_text(_value(row, "reason")),
        evidence_note=_optional_text(_value(row, "evidence_note")),
    )


def validate_workbook_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    relation_universe: Iterable[RelationIdentity],
    topic_vocabulary: Iterable[str] | None = None,
) -> tuple[ValidatedWorkbookRow, ...]:
    universe = tuple(relation_universe)
    validated = tuple(
        validate_workbook_row(
            row,
            relation_universe=universe,
            topic_vocabulary=topic_vocabulary,
        )
        for row in rows
    )
    seen: set[RelationIdentity] = set()
    for row in validated:
        for identity in row.identities():
            if identity in seen:
                raise WorkbookWeightValidationError(
                    f"duplicate Topic relation across workbook rows: {identity}"
                )
            seen.add(identity)
    return validated


def export_proposal_rows(
    proposals: Iterable[RelationWeightProposal],
    *,
    stock_rows: Iterable[Mapping[str, Any]] = (),
) -> tuple[dict[str, str], ...]:
    """Export all relation proposals in Owner-editable positional pairs.

    ``stock_rows`` is optional display metadata. It is also the only way to
    export a zero-relation stock row; no Topic is synthesized when a stock has
    no current relation.
    """

    grouped: dict[tuple[str, str], list[RelationWeightProposal]] = defaultdict(list)
    for proposal in proposals:
        grouped[(proposal.identity.market, proposal.identity.instrument)].append(proposal)

    metadata: dict[tuple[str, str], Mapping[str, Any]] = {}
    for stock in stock_rows:
        market = str(_value(stock, "market") or "").strip()
        symbol = str(_value(stock, "symbol") or "").strip()
        if market and symbol:
            metadata[(market, symbol)] = stock

    rows: list[dict[str, str]] = []
    for market, instrument in sorted(set(grouped).union(metadata)):
        relations = sorted(
            grouped.get((market, instrument), ()),
            key=lambda proposal: (
                proposal.identity.relation_type != "PRIMARY",
                proposal.identity.topic,
            ),
        )
        primary = [p for p in relations if p.identity.relation_type == "PRIMARY"]
        secondary = [p for p in relations if p.identity.relation_type == "SECONDARY"]
        stock = metadata.get((market, instrument), {})
        rows.append(
            {
                "symbol": instrument,
                "name": str(_value(stock, "name") or "").strip(),
                "market": market,
                "representative_topic": str(
                    _value(stock, "representative_topic") or ""
                ).strip(),
                "primary_topics": TOKEN_SEPARATOR.join(
                    p.identity.topic for p in primary
                ),
                "secondary_topics": TOKEN_SEPARATOR.join(
                    p.identity.topic for p in secondary
                ),
                "primary_weights": TOKEN_SEPARATOR.join(
                    format(p.weight, "f") for p in primary
                ),
                "secondary_weights": TOKEN_SEPARATOR.join(
                    format(p.weight, "f") for p in secondary
                ),
                "effective_date": (
                    relations[0].effective_from.isoformat() if relations else ""
                ),
                "reason": str(_value(stock, "reason") or "").strip(),
                "evidence_note": str(_value(stock, "evidence_note") or "").strip(),
            }
        )
    return tuple(rows)


__all__ = [
    "LEGACY_TOKEN_SEPARATOR",
    "TOKEN_SEPARATOR",
    "WORKBOOK_COLUMNS",
    "ValidatedWorkbookRow",
    "WorkbookWeightValidationError",
    "export_proposal_rows",
    "validate_workbook_row",
    "validate_workbook_rows",
]
