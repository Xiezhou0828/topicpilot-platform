from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import Connection, text


def suspend_active_reference_registries(connection: Connection) -> tuple[UUID, ...]:
    """Temporarily make the approved integration registry replaceable in tests."""
    active_ids = tuple(
        row[0]
        for row in connection.execute(
            text(
                """
                SELECT id
                FROM topicpilot.reference_registry_sets
                WHERE status = 'ACTIVE'
                ORDER BY id
                """
            )
        ).all()
    )
    if active_ids:
        connection.execute(
            text(
                """
                UPDATE topicpilot.reference_registry_sets
                SET status = 'RETIRED'
                WHERE id = ANY(:ids)
                """
            ),
            {"ids": list(active_ids)},
        )
    return active_ids


def restore_active_reference_registries(
    connection: Connection, registry_ids: Iterable[UUID]
) -> None:
    """Restore the active registry state after an isolated fixture test."""
    ids = tuple(registry_ids)
    if ids:
        connection.execute(
            text(
                """
                UPDATE topicpilot.reference_registry_sets
                SET status = 'ACTIVE'
                WHERE id = ANY(:ids)
                """
            ),
            {"ids": list(ids)},
        )
