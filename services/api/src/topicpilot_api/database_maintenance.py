"""Database-maintenance workbook contract and deterministic import planning.

This module is deliberately independent from Excel.  Excel is an Owner-facing
input surface; the importer validates these rows again before it can reach a
database transaction.  Relation Weight remains a relation-level membership
importance value and is never read as Topic Score, Grade, Lifecycle, Today, or
Opportunity input.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

try:
    from .relation_weight_authority import (
        PRIMARY_MAX,
        PRIMARY_MIN,
        SECONDARY_MAX,
        SECONDARY_MIN,
        parse_weight,
    )
except ImportError as exc:
    # The bundled spreadsheet runtime intentionally does not carry the API's
    # SQLAlchemy dependency.  Keep the Excel contract usable there while the
    # production API continues to use the canonical authority module above.
    if exc.name not in {"sqlalchemy", "datetime"}:
        raise
    PRIMARY_MIN = Decimal("0.5")
    PRIMARY_MAX = Decimal("2.0")
    SECONDARY_MIN = Decimal("0.3")
    SECONDARY_MAX = Decimal("0.8")

    def parse_weight(value: Any, relation_type: str) -> Decimal:
        try:
            parsed = Decimal(str(value).strip())
        except (InvalidOperation, ValueError, TypeError) as error:
            raise ValueError(f"invalid {relation_type} weight: {value!r}") from error
        lower = PRIMARY_MIN if relation_type == "PRIMARY" else SECONDARY_MIN
        upper = PRIMARY_MAX if relation_type == "PRIMARY" else SECONDARY_MAX
        if not lower <= parsed <= upper:
            raise ValueError(f"{relation_type} weight must be between {lower} and {upper}")
        return parsed


TOKEN_SEPARATOR = "|"
TOPIC_ACTIVE_STATUSES = frozenset({"ACTIVE", "ENABLED", "PUBLISHED"})
TOPIC_INACTIVE_STATUSES = frozenset({"DISABLED", "RETIRED"})
MAINTENANCE_ACTIONS = frozenset(
    {
        "ADD_INSTRUMENT",
        "UPDATE_INSTRUMENT",
        "UPSERT_RELATIONS",
        "REPLACE_RELATIONS",
        "DEACTIVATE_INSTRUMENT",
    }
)
MARKET_CODES = frozenset({"TPE", "TWO"})
RELATION_WEIGHT_AUTHORITY_EFFECTIVE_DATE = date(2026, 9, 24)


@dataclass(frozen=True)
class TopicCatalogEntry:
    id: str
    slug: str
    name: str
    status: str
    valid_from: date | None = None
    valid_to: date | None = None
    hierarchy: str | None = None

    @property
    def active(self) -> bool:
        return self.status.upper() in TOPIC_ACTIVE_STATUSES

    def effective_for(self, as_of: date) -> bool:
        return (
            self.active
            and (self.valid_from is None or self.valid_from <= as_of)
            and (self.valid_to is None or as_of <= self.valid_to)
        )


@dataclass(frozen=True)
class InstrumentCatalogEntry:
    id: str
    stock_code: str
    name: str | None
    market: str
    instrument_type: str
    currency: str | None
    active: bool
    valid_from: date | None = None
    valid_to: date | None = None


@dataclass(frozen=True)
class RelationCatalogEntry:
    id: str
    instrument_id: str
    topic_id: str
    market: str
    stock_code: str
    topic_slug: str
    topic_name: str
    relation_type: str
    relation_version: str
    valid_from: date
    valid_to: date | None
    relation_weight: Decimal | None = None
    weight_approval_state: str | None = None

    def active_for(self, as_of: date) -> bool:
        return self.valid_from <= as_of and (self.valid_to is None or as_of <= self.valid_to)


@dataclass(frozen=True)
class MaintenanceCatalog:
    markets: frozenset[str] = frozenset()
    instruments: Mapping[tuple[str, str], InstrumentCatalogEntry] = field(default_factory=dict)
    topics: tuple[TopicCatalogEntry, ...] = ()
    relations: tuple[RelationCatalogEntry, ...] = ()

    @property
    def topics_by_slug(self) -> dict[str, TopicCatalogEntry]:
        return {item.slug: item for item in self.topics}

    @property
    def topics_by_name(self) -> dict[str, tuple[TopicCatalogEntry, ...]]:
        grouped: dict[str, list[TopicCatalogEntry]] = {}
        for item in self.topics:
            grouped.setdefault(item.name, []).append(item)
        return {key: tuple(value) for key, value in grouped.items()}

    @property
    def active_relations(self) -> tuple[RelationCatalogEntry, ...]:
        return tuple(
            item for item in self.relations if item.relation_type in {"PRIMARY", "SECONDARY"}
        )


@dataclass(frozen=True)
class ValidationError:
    row_number: int
    stock_code: str
    field: str
    value: str
    error_code: str
    message: str
    severity: str = "ERROR"

    def as_dict(self) -> dict[str, str | int]:
        return {
            "ROW_NUMBER": self.row_number,
            "STOCK_CODE": self.stock_code,
            "FIELD": self.field,
            "VALUE": self.value,
            "ERROR_CODE": self.error_code,
            "MESSAGE": self.message,
            "SEVERITY": self.severity,
        }


@dataclass(frozen=True)
class NormalizedOperation:
    row_number: int
    record_type: str
    operation: str
    action: str
    market: str
    stock_code: str
    instrument_id: str | None = None
    name: str | None = None
    instrument_type: str | None = None
    active: bool | None = None
    topic_id: str | None = None
    topic_identifier: str | None = None
    topic_name: str | None = None
    relation_type: str | None = None
    relation_weight: Decimal | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    message: str | None = None

    def as_dict(self) -> dict[str, str | int | bool | None]:
        return {
            "ROW_NUMBER": self.row_number,
            "RECORD_TYPE": self.record_type,
            "OPERATION": self.operation,
            "ACTION": self.action,
            "MARKET": self.market,
            "STOCK_CODE": self.stock_code,
            "INSTRUMENT_ID": self.instrument_id,
            "NAME": self.name,
            "INSTRUMENT_TYPE": self.instrument_type,
            "ACTIVE": self.active,
            "TOPIC_ID": self.topic_id,
            "TOPIC_IDENTIFIER": self.topic_identifier,
            "TOPIC_NAME": self.topic_name,
            "RELATION_TYPE": self.relation_type,
            "RELATION_WEIGHT": str(self.relation_weight)
            if self.relation_weight is not None
            else None,
            "EFFECTIVE_FROM": self.effective_from.isoformat() if self.effective_from else None,
            "EFFECTIVE_TO": self.effective_to.isoformat() if self.effective_to else None,
            "MESSAGE": self.message,
        }


@dataclass(frozen=True)
class ValidatedMaintenanceRow:
    row_number: int
    action: str
    market: str
    stock_code: str
    name: str | None
    instrument_type: str | None
    currency: str | None
    active: bool | None
    as_of_date: date
    representative_topic: TopicCatalogEntry | None
    primary_topics: tuple[tuple[TopicCatalogEntry, Decimal], ...]
    secondary_topics: tuple[tuple[TopicCatalogEntry, Decimal], ...]
    notes: str | None
    instrument: InstrumentCatalogEntry | None

    def relation_topics(self) -> tuple[tuple[TopicCatalogEntry, Decimal, str], ...]:
        return tuple((*item, "PRIMARY") for item in self.primary_topics) + tuple(
            (*item, "SECONDARY") for item in self.secondary_topics
        )


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _row_value(row: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None


def _parse_bool(value: Any) -> bool | None:
    text = _text(value).upper()
    if not text:
        return None
    if text in {"TRUE", "T", "YES", "Y", "1", "ACTIVE", "ENABLED"}:
        return True
    if text in {"FALSE", "F", "NO", "N", "0", "INACTIVE", "DISABLED"}:
        return False
    raise ValueError(f"unsupported boolean value: {value}")


def _parse_date(value: Any, default: date) -> date:
    text = _text(value)
    if not text:
        return default
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid ISO date: {text}") from exc


def parse_topic_tokens(value: Any, field: str) -> tuple[str, ...]:
    text = _text(value)
    if not text:
        return ()
    if "," in text or ";" in text:
        raise ValueError(f"{field} must use literal '{TOKEN_SEPARATOR}' as the delimiter")
    tokens = tuple(item.strip() for item in text.split(TOKEN_SEPARATOR))
    if any(not item for item in tokens):
        raise ValueError(f"{field} contains a blank token")
    if len(set(tokens)) != len(tokens):
        raise ValueError(f"{field} contains duplicate topic names")
    return tokens


def parse_weight_tokens(value: Any, field: str) -> tuple[str, ...]:
    text = _text(value)
    if not text:
        return ()
    if "," in text or ";" in text:
        raise ValueError(f"{field} must use literal '{TOKEN_SEPARATOR}' as the delimiter")
    tokens = tuple(item.strip() for item in text.split(TOKEN_SEPARATOR))
    if any(not item for item in tokens):
        raise ValueError(f"{field} contains a blank token")
    return tokens


def _resolve_topic(token: str, catalog: MaintenanceCatalog, as_of: date) -> TopicCatalogEntry:
    by_slug = catalog.topics_by_slug
    if token in by_slug:
        topic = by_slug[token]
    else:
        matches = catalog.topics_by_name.get(token, ())
        if len(matches) > 1:
            raise KeyError(f"topic name is ambiguous: {token}")
        if not matches:
            raise KeyError(f"unknown topic: {token}")
        topic = matches[0]
    if not topic.active:
        raise PermissionError(f"topic is disabled or non-formal: {token}")
    if not topic.effective_for(as_of):
        raise PermissionError(f"topic is not effective for {as_of.isoformat()}: {token}")
    return topic


def _validation_error(
    row_number: int,
    row: Mapping[str, Any],
    field: str,
    value: Any,
    code: str,
    message: str,
) -> ValidationError:
    return ValidationError(
        row_number=row_number,
        stock_code=_text(_row_value(row, "STOCK_CODE", "stock_code", "symbol")),
        field=field,
        value=_text(value),
        error_code=code,
        message=message,
    )


def validate_maintenance_row(
    row: Mapping[str, Any],
    *,
    row_number: int,
    catalog: MaintenanceCatalog,
    default_as_of: date | None = None,
) -> tuple[ValidatedMaintenanceRow | None, tuple[ValidationError, ...]]:
    """Validate one human-maintenance row and resolve topic names to IDs."""

    today = default_as_of or date.today()
    errors: list[ValidationError] = []
    action = _text(_row_value(row, "ACTION", "action")).upper()
    stock_code = _text(_row_value(row, "STOCK_CODE", "stock_code", "symbol"))
    market = _text(_row_value(row, "MARKET", "market")).upper()
    name = _text(_row_value(row, "NAME", "name")) or None
    instrument_type = _text(_row_value(row, "INSTRUMENT_TYPE", "instrument_type")) or None
    currency = _text(_row_value(row, "CURRENCY", "currency")) or None
    notes = _text(_row_value(row, "NOTES", "notes")) or None

    if action not in MAINTENANCE_ACTIONS:
        errors.append(
            _validation_error(
                row_number,
                row,
                "ACTION",
                action,
                "UNKNOWN_ACTION",
                f"unknown ACTION: {action or '<blank>'}",
            )
        )
    if not stock_code:
        errors.append(
            _validation_error(
                row_number,
                row,
                "STOCK_CODE",
                stock_code,
                "MISSING_STOCK_CODE",
                "STOCK_CODE is required",
            )
        )
    if not market:
        errors.append(
            _validation_error(
                row_number, row, "MARKET", market, "INVALID_MARKET", "MARKET is required"
            )
        )
    elif catalog.markets and market not in catalog.markets:
        errors.append(
            _validation_error(
                row_number, row, "MARKET", market, "INVALID_MARKET", f"unknown MARKET: {market}"
            )
        )

    instrument = catalog.instruments.get((market, stock_code)) if market and stock_code else None
    if action == "ADD_INSTRUMENT" and instrument is not None:
        errors.append(
            _validation_error(
                row_number,
                row,
                "STOCK_CODE",
                stock_code,
                "INSTRUMENT_ALREADY_EXISTS",
                f"instrument already exists: {market}:{stock_code}",
            )
        )
    if (
        action
        in {"UPDATE_INSTRUMENT", "UPSERT_RELATIONS", "REPLACE_RELATIONS", "DEACTIVATE_INSTRUMENT"}
        and catalog.instruments
        and instrument is None
    ):
        errors.append(
            _validation_error(
                row_number,
                row,
                "STOCK_CODE",
                stock_code,
                "UNKNOWN_INSTRUMENT",
                f"instrument does not exist: {market}:{stock_code}",
            )
        )
    if action == "ADD_INSTRUMENT" and not name:
        errors.append(
            _validation_error(
                row_number, row, "NAME", name, "MISSING_NAME", "NAME is required for ADD_INSTRUMENT"
            )
        )
    if action == "ADD_INSTRUMENT" and not instrument_type:
        errors.append(
            _validation_error(
                row_number,
                row,
                "INSTRUMENT_TYPE",
                instrument_type,
                "MISSING_INSTRUMENT_TYPE",
                "INSTRUMENT_TYPE is required for ADD_INSTRUMENT",
            )
        )

    try:
        active = _parse_bool(_row_value(row, "ACTIVE/ENABLED", "ACTIVE", "active"))
    except ValueError as exc:
        active = None
        errors.append(
            _validation_error(
                row_number,
                row,
                "ACTIVE/ENABLED",
                _row_value(row, "ACTIVE/ENABLED", "ACTIVE", "active"),
                "INVALID_ACTIVE",
                str(exc),
            )
        )

    try:
        as_of = _parse_date(_row_value(row, "AS_OF_DATE", "as_of_date", "effective_from"), today)
    except ValueError as exc:
        as_of = today
        errors.append(
            _validation_error(
                row_number,
                row,
                "AS_OF_DATE",
                _row_value(row, "AS_OF_DATE", "as_of_date", "effective_from"),
                "INVALID_DATE",
                str(exc),
            )
        )
    if as_of < RELATION_WEIGHT_AUTHORITY_EFFECTIVE_DATE:
        errors.append(
            _validation_error(
                row_number,
                row,
                "AS_OF_DATE",
                as_of.isoformat(),
                "BACKDATED_EFFECTIVE_DATE",
                (
                    "AS_OF_DATE cannot precede "
                    f"{RELATION_WEIGHT_AUTHORITY_EFFECTIVE_DATE.isoformat()} "
                    "for formal relation-weight authority"
                ),
            )
        )

    if action == "UPDATE_INSTRUMENT" and any(
        _text(_row_value(row, field))
        for field in ("PRIMARY_TOPICS", "PRIMARY_WEIGHTS", "SECONDARY_TOPICS", "SECONDARY_WEIGHTS")
    ):
        errors.append(
            _validation_error(
                row_number,
                row,
                "ACTION",
                action,
                "ACTION_RELATIONS_NOT_ALLOWED",
                (
                    "UPDATE_INSTRUMENT changes master fields only; use "
                    "UPSERT_RELATIONS or REPLACE_RELATIONS for topics"
                ),
            )
        )
    if action == "DEACTIVATE_INSTRUMENT" and any(
        _text(_row_value(row, field))
        for field in ("PRIMARY_TOPICS", "PRIMARY_WEIGHTS", "SECONDARY_TOPICS", "SECONDARY_WEIGHTS")
    ):
        errors.append(
            _validation_error(
                row_number,
                row,
                "ACTION",
                action,
                "ACTION_RELATIONS_NOT_ALLOWED",
                "DEACTIVATE_INSTRUMENT does not accept topic lists",
            )
        )

    try:
        primary_tokens = parse_topic_tokens(
            _row_value(row, "PRIMARY_TOPICS", "primary_topics"), "PRIMARY_TOPICS"
        )
    except ValueError as exc:
        primary_tokens = ()
        errors.append(
            _validation_error(
                row_number,
                row,
                "PRIMARY_TOPICS",
                _row_value(row, "PRIMARY_TOPICS", "primary_topics"),
                "INVALID_TOPIC_LIST",
                str(exc),
            )
        )
    try:
        secondary_tokens = parse_topic_tokens(
            _row_value(row, "SECONDARY_TOPICS", "secondary_topics"), "SECONDARY_TOPICS"
        )
    except ValueError as exc:
        secondary_tokens = ()
        errors.append(
            _validation_error(
                row_number,
                row,
                "SECONDARY_TOPICS",
                _row_value(row, "SECONDARY_TOPICS", "secondary_topics"),
                "INVALID_TOPIC_LIST",
                str(exc),
            )
        )
    try:
        primary_weight_tokens = parse_weight_tokens(
            _row_value(row, "PRIMARY_WEIGHTS", "primary_weights"), "PRIMARY_WEIGHTS"
        )
    except ValueError as exc:
        primary_weight_tokens = ()
        errors.append(
            _validation_error(
                row_number,
                row,
                "PRIMARY_WEIGHTS",
                _row_value(row, "PRIMARY_WEIGHTS", "primary_weights"),
                "INVALID_WEIGHT_LIST",
                str(exc),
            )
        )
    try:
        secondary_weight_tokens = parse_weight_tokens(
            _row_value(row, "SECONDARY_WEIGHTS", "secondary_weights"), "SECONDARY_WEIGHTS"
        )
    except ValueError as exc:
        secondary_weight_tokens = ()
        errors.append(
            _validation_error(
                row_number,
                row,
                "SECONDARY_WEIGHTS",
                _row_value(row, "SECONDARY_WEIGHTS", "secondary_weights"),
                "INVALID_WEIGHT_LIST",
                str(exc),
            )
        )

    if len(primary_tokens) != len(primary_weight_tokens):
        errors.append(
            _validation_error(
                row_number,
                row,
                "PRIMARY_WEIGHTS",
                _row_value(row, "PRIMARY_WEIGHTS", "primary_weights"),
                "TOPIC_WEIGHT_COUNT_MISMATCH",
                (
                    f"PRIMARY topics count {len(primary_tokens)} does not match "
                    f"PRIMARY weights count {len(primary_weight_tokens)}"
                ),
            )
        )
    if len(secondary_tokens) != len(secondary_weight_tokens):
        errors.append(
            _validation_error(
                row_number,
                row,
                "SECONDARY_WEIGHTS",
                _row_value(row, "SECONDARY_WEIGHTS", "secondary_weights"),
                "TOPIC_WEIGHT_COUNT_MISMATCH",
                (
                    f"SECONDARY topics count {len(secondary_tokens)} does not match "
                    f"SECONDARY weights count {len(secondary_weight_tokens)}"
                ),
            )
        )
    overlap = sorted(set(primary_tokens).intersection(secondary_tokens))
    if overlap:
        errors.append(
            _validation_error(
                row_number,
                row,
                "PRIMARY_TOPICS/SECONDARY_TOPICS",
                "|".join(overlap),
                "PRIMARY_SECONDARY_CONFLICT",
                f"topic appears in both PRIMARY and SECONDARY: {', '.join(overlap)}",
            )
        )

    resolved_primary: list[tuple[TopicCatalogEntry, Decimal]] = []
    resolved_secondary: list[tuple[TopicCatalogEntry, Decimal]] = []
    for tokens, weights, relation_type, target in (
        (primary_tokens, primary_weight_tokens, "PRIMARY", resolved_primary),
        (secondary_tokens, secondary_weight_tokens, "SECONDARY", resolved_secondary),
    ):
        for token, weight_token in zip(tokens, weights, strict=False):
            try:
                topic = _resolve_topic(token, catalog, as_of)
            except KeyError as exc:
                errors.append(
                    _validation_error(
                        row_number,
                        row,
                        "PRIMARY_TOPICS" if relation_type == "PRIMARY" else "SECONDARY_TOPICS",
                        token,
                        "UNKNOWN_TOPIC",
                        str(exc).replace("'", ""),
                    )
                )
                continue
            except PermissionError as exc:
                code = (
                    "DISABLED_TOPIC"
                    if "disabled" in str(exc) or "non-formal" in str(exc)
                    else "TOPIC_NOT_EFFECTIVE"
                )
                errors.append(
                    _validation_error(
                        row_number,
                        row,
                        "PRIMARY_TOPICS" if relation_type == "PRIMARY" else "SECONDARY_TOPICS",
                        token,
                        code,
                        str(exc),
                    )
                )
                continue
            try:
                weight = parse_weight(weight_token, relation_type=relation_type)
            except Exception as exc:  # parse_weight exposes stable ValueError subclasses
                try:
                    numeric_weight = Decimal(str(weight_token).strip())
                except (InvalidOperation, ValueError, TypeError):
                    numeric_weight = None
                minimum = PRIMARY_MIN if relation_type == "PRIMARY" else SECONDARY_MIN
                maximum = PRIMARY_MAX if relation_type == "PRIMARY" else SECONDARY_MAX
                out_of_range = (
                    numeric_weight is not None and not minimum <= numeric_weight <= maximum
                )
                error_code = (
                    "PRIMARY_WEIGHT_OUT_OF_RANGE"
                    if relation_type == "PRIMARY" and out_of_range
                    else "SECONDARY_WEIGHT_OUT_OF_RANGE"
                    if relation_type == "SECONDARY" and out_of_range
                    else "INVALID_WEIGHT"
                )
                errors.append(
                    _validation_error(
                        row_number,
                        row,
                        "PRIMARY_WEIGHTS" if relation_type == "PRIMARY" else "SECONDARY_WEIGHTS",
                        f"{token}={weight_token}",
                        error_code,
                        f"{token} {relation_type} weight {weight_token}: {exc}",
                    )
                )
                continue
            target.append((topic, weight))

    representative_topic: TopicCatalogEntry | None = None
    representative_token = _text(_row_value(row, "REPRESENTATIVE_TOPIC", "representative_topic"))
    if representative_token:
        try:
            representative_topic = _resolve_topic(representative_token, catalog, as_of)
        except (KeyError, PermissionError) as exc:
            errors.append(
                _validation_error(
                    row_number,
                    row,
                    "REPRESENTATIVE_TOPIC",
                    representative_token,
                    "UNKNOWN_TOPIC",
                    str(exc).replace("'", ""),
                )
            )

    if errors:
        return None, tuple(errors)
    return (
        ValidatedMaintenanceRow(
            row_number=row_number,
            action=action,
            market=market,
            stock_code=stock_code,
            name=name,
            instrument_type=instrument_type,
            currency=currency,
            active=active,
            as_of_date=as_of,
            representative_topic=representative_topic,
            primary_topics=tuple(resolved_primary),
            secondary_topics=tuple(resolved_secondary),
            notes=notes,
            instrument=instrument,
        ),
        (),
    )


def validate_maintenance_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    catalog: MaintenanceCatalog,
    default_as_of: date | None = None,
) -> tuple[tuple[ValidatedMaintenanceRow, ...], tuple[ValidationError, ...]]:
    validated: list[ValidatedMaintenanceRow] = []
    errors: list[ValidationError] = []
    seen_relation_keys: set[tuple[str, str, str, str]] = set()
    for row_number, row in enumerate(rows, start=2):
        if not any(_text(value) for value in row.values()):
            continue
        item, row_errors = validate_maintenance_row(
            row, row_number=row_number, catalog=catalog, default_as_of=default_as_of
        )
        errors.extend(row_errors)
        if item is None:
            continue
        for topic, _, relation_type in item.relation_topics():
            identity = (item.market, item.stock_code, topic.slug, relation_type)
            if identity in seen_relation_keys:
                errors.append(
                    ValidationError(
                        item.row_number,
                        item.stock_code,
                        "STOCK_CODE",
                        item.stock_code,
                        "DUPLICATE_RELATION",
                        f"duplicate relation across workbook rows: {identity}",
                    )
                )
            seen_relation_keys.add(identity)
        validated.append(item)
    return tuple(validated), tuple(errors)


def build_operations(
    validated_rows: Iterable[ValidatedMaintenanceRow],
    *,
    catalog: MaintenanceCatalog,
) -> tuple[NormalizedOperation, ...]:
    operations: list[NormalizedOperation] = []
    current_relations = {
        (item.market, item.stock_code, item.topic_slug, item.relation_type): item
        for item in catalog.active_relations
    }
    for item in validated_rows:
        instrument_id = item.instrument.id if item.instrument else None
        if item.action in {"ADD_INSTRUMENT", "UPDATE_INSTRUMENT", "DEACTIVATE_INSTRUMENT"}:
            operations.append(
                NormalizedOperation(
                    row_number=item.row_number,
                    record_type="INSTRUMENT",
                    operation=item.action,
                    action=item.action,
                    market=item.market,
                    stock_code=item.stock_code,
                    instrument_id=instrument_id,
                    name=item.name,
                    instrument_type=item.instrument_type,
                    active=False if item.action == "DEACTIVATE_INSTRUMENT" else item.active,
                    effective_from=item.as_of_date,
                    message="instrument master operation",
                )
            )
        if item.action in {"UPDATE_INSTRUMENT", "DEACTIVATE_INSTRUMENT"}:
            continue
        desired: set[tuple[str, str, str]] = set()
        for topic, weight, relation_type in item.relation_topics():
            desired.add((topic.slug, relation_type, str(weight)))
            operations.append(
                NormalizedOperation(
                    row_number=item.row_number,
                    record_type="RELATION",
                    operation="UPSERT",
                    action=item.action,
                    market=item.market,
                    stock_code=item.stock_code,
                    instrument_id=instrument_id,
                    name=item.name,
                    active=item.active,
                    topic_id=topic.id,
                    topic_identifier=topic.slug,
                    topic_name=topic.name,
                    relation_type=relation_type,
                    relation_weight=weight,
                    effective_from=item.as_of_date,
                    message="relation-level membership importance",
                )
            )
        if item.action == "REPLACE_RELATIONS":
            for key, relation in sorted(current_relations.items()):
                if key[0] != item.market or key[1] != item.stock_code:
                    continue
                if not any(
                    key[2] == topic_slug and key[3] == relation_type
                    for topic_slug, relation_type, _ in desired
                ):
                    operations.append(
                        NormalizedOperation(
                            row_number=item.row_number,
                            record_type="RELATION",
                            operation="DEACTIVATE",
                            action=item.action,
                            market=item.market,
                            stock_code=item.stock_code,
                            instrument_id=relation.instrument_id,
                            topic_id=relation.topic_id,
                            topic_identifier=relation.topic_slug,
                            topic_name=relation.topic_name,
                            relation_type=relation.relation_type,
                            relation_weight=relation.relation_weight,
                            effective_from=item.as_of_date,
                            effective_to=item.as_of_date,
                            message=(
                                "REPLACE_RELATIONS removes unspecified current relation "
                                "without hard delete"
                            ),
                        )
                    )
    return tuple(operations)


__all__ = [
    "MAINTENANCE_ACTIONS",
    "MARKET_CODES",
    "TOKEN_SEPARATOR",
    "TOPIC_ACTIVE_STATUSES",
    "TOPIC_INACTIVE_STATUSES",
    "InstrumentCatalogEntry",
    "MaintenanceCatalog",
    "NormalizedOperation",
    "RelationCatalogEntry",
    "TopicCatalogEntry",
    "ValidatedMaintenanceRow",
    "ValidationError",
    "build_operations",
    "parse_topic_tokens",
    "parse_weight_tokens",
    "validate_maintenance_row",
    "validate_maintenance_rows",
]
