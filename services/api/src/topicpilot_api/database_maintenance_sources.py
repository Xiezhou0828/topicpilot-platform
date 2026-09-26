"""Explicit, read-only data-source helpers for database-maintenance snapshots."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

CANONICAL_MIGRATION_HEAD = "0046_task_stock_maint_relation_weight_authority_001d"


class SourceProbeError(RuntimeError):
    """Raised when a requested source cannot be verified safely."""


def migration_number(revision: str | None) -> int | None:
    if not revision:
        return None
    prefix = str(revision).split("_", 1)[0]
    return int(prefix) if prefix.isdigit() else None


def migration_schema_status(
    source_head: str | None,
    canonical_head: str = CANONICAL_MIGRATION_HEAD,
) -> str:
    """Compare a verified source migration marker with the canonical marker."""

    if not source_head:
        return "UNKNOWN"
    if source_head == canonical_head:
        return "CURRENT"
    source_number = migration_number(source_head)
    canonical_number = migration_number(canonical_head)
    if source_number is None or canonical_number is None:
        return "UNKNOWN"
    if source_number < canonical_number:
        return "OLDER_THAN_CANONICAL"
    if source_number > canonical_number:
        return "NEWER_THAN_CANONICAL"
    return "UNKNOWN"


def _json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "hex"):
        return str(value)
    return value


def _table_columns(connection: Any, schema: str, table: str) -> set[str]:
    from sqlalchemy import text

    rows = connection.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema=:schema AND table_name=:table
            """
        ),
        {"schema": schema, "table": table},
    )
    return {str(row[0]) for row in rows}


def _column_or_null(alias: str, column: str, available: set[str], cast: str = "text") -> str:
    if column in available:
        return f"{alias}.{column} AS {column}"
    return f"NULL::{cast} AS {column}"


def _migration_heads(connection: Any) -> tuple[str, ...]:
    from sqlalchemy import text

    try:
        rows = connection.execute(
            text("SELECT version_num FROM public.alembic_version ORDER BY version_num")
        )
    except Exception as exc:
        raise SourceProbeError("migration marker could not be read") from exc
    heads = tuple(str(row[0]) for row in rows if row[0])
    if not heads:
        raise SourceProbeError("migration marker is empty")
    return heads


def snapshot_from_database(
    database_url: str,
    *,
    source: str,
    environment: str,
    as_of: date,
    snapshot_note: str,
) -> dict[str, Any]:
    """Read a maintenance snapshot without issuing any database writes."""

    from sqlalchemy import create_engine, text

    engine = None
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as connection:
            try:
                connection.execute(text("SET TRANSACTION READ ONLY"))
            except Exception as exc:
                raise SourceProbeError("read-only transaction could not be established") from exc

            heads = _migration_heads(connection)
            if len(heads) != 1:
                raise SourceProbeError("source has multiple migration heads")
            source_head = heads[0]
            relation_columns = _table_columns(
                connection, "topicpilot", "instrument_topic_relations"
            )
            authority_columns = _table_columns(
                connection, "topicpilot", "relation_weight_authorities"
            )
            markets = [
                dict(row._mapping)
                for row in connection.execute(
                    text(
                        """
                        SELECT id, code, name, exchange_code, timezone, calendar_code,
                               valid_from, valid_to, is_active
                        FROM topicpilot.markets
                        ORDER BY code, id
                        """
                    )
                )
            ]
            instruments = [
                dict(row._mapping)
                for row in connection.execute(
                    text(
                        """
                        SELECT i.id, i.instrument_code, i.name, m.code AS market,
                               i.instrument_type, i.currency, i.is_active,
                               i.valid_from, i.valid_to, i.created_at, i.updated_at
                        FROM topicpilot.instruments i
                        JOIN topicpilot.markets m ON m.id = i.market_id
                        ORDER BY m.code, i.instrument_code, i.id
                        """
                    )
                )
            ]
            topics = [
                dict(row._mapping)
                for row in connection.execute(
                    text(
                        """
                        SELECT id, slug, name, description, status, dictionary_version,
                               valid_from, valid_to, display_metadata
                        FROM topicpilot.topics
                        ORDER BY slug, id
                        """
                    )
                )
            ]

            relation_select = [
                "r.id",
                "i.instrument_code",
                "i.name AS instrument_name",
                "m.code AS market",
                "r.topic_id",
                "t.slug AS topic_slug",
                "t.name AS topic_name",
                _column_or_null("r", "relation_type", relation_columns),
                _column_or_null("r", "relation_version", relation_columns),
                _column_or_null("r", "valid_from", relation_columns, "date"),
                _column_or_null("r", "valid_to", relation_columns, "date"),
                _column_or_null("r", "structural_role", relation_columns),
                _column_or_null("r", "approval_state", relation_columns),
                _column_or_null("r", "source_artifact_id", relation_columns),
                _column_or_null("r", "source_artifact_hash", relation_columns),
                _column_or_null("r", "updated_at", relation_columns, "timestamptz"),
            ]
            has_weight_authority = {
                "relation_id",
                "weight",
                "approval_state",
                "effective_from",
                "effective_to",
                "correction_sequence",
                "created_at",
            }.issubset(authority_columns)
            if has_weight_authority:
                relation_select.extend(
                    [
                        "rwa.weight AS relation_weight",
                        "rwa.approval_state AS weight_approval_state",
                    ]
                )
                weight_join = """
                    LEFT JOIN LATERAL (
                        SELECT weight, approval_state
                        FROM topicpilot.relation_weight_authorities
                        WHERE relation_id = r.id
                          AND approval_state = 'APPROVED'
                          AND effective_from <= :as_of
                          AND (effective_to IS NULL OR effective_to >= :as_of)
                        ORDER BY effective_from DESC, correction_sequence DESC, created_at DESC
                        LIMIT 1
                    ) rwa ON TRUE
                """
            else:
                relation_select.extend(
                    ["NULL::numeric AS relation_weight", "NULL::text AS weight_approval_state"]
                )
                weight_join = ""
            relations = [
                dict(row._mapping)
                for row in connection.execute(
                    text(
                        f"""
                        SELECT {', '.join(relation_select)}
                        FROM topicpilot.instrument_topic_relations r
                        JOIN topicpilot.instruments i ON i.id = r.instrument_id
                        JOIN topicpilot.markets m ON m.id = i.market_id
                        JOIN topicpilot.topics t ON t.id = r.topic_id
                        {weight_join}
                        ORDER BY m.code, i.instrument_code, t.slug, r.relation_type, r.id
                        """
                    ),
                    {"as_of": as_of},
                )
            ]
    except SourceProbeError:
        raise
    except Exception as exc:
        raise SourceProbeError(f"database probe failed: {type(exc).__name__}") from exc
    finally:
        if engine is not None:
            engine.dispose()

    weight_note = (
        "Approved relation-weight authority values were read."
        if has_weight_authority
        else "This source predates relation-weight authority; relation weights are UNKNOWN."
    )
    snapshot = {
        "source": source,
        "environment": environment,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "as_of_date": as_of.isoformat(),
        "source_migration_head": source_head,
        "canonical_migration_head": CANONICAL_MIGRATION_HEAD,
        "source_schema_status": migration_schema_status(source_head),
        "relation_weight_available": has_weight_authority,
        "markets": [row["code"] for row in markets if row.get("is_active")],
        "markets_current": [
            {key: _json_value(value) for key, value in row.items()} for row in markets
        ],
        "instruments": [
            {key: _json_value(value) for key, value in row.items()}
            for row in instruments
        ],
        "topics": [
            {
                **{key: _json_value(value) for key, value in row.items()},
                "hierarchy": None,
            }
            for row in topics
        ],
        "relations": [
            {key: _json_value(value) for key, value in row.items()} for row in relations
        ],
    }
    snapshot["counts"] = {
        "instruments": len(snapshot["instruments"]),
        "topics": len(snapshot["topics"]),
        "relations": len(snapshot["relations"]),
    }
    snapshot["snapshot_note"] = f"{snapshot_note} {weight_note}"
    return snapshot


__all__ = [
    "CANONICAL_MIGRATION_HEAD",
    "SourceProbeError",
    "migration_number",
    "migration_schema_status",
    "snapshot_from_database",
]
