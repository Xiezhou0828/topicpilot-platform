"""Single source of truth for persisted structural-role vocabulary."""

from __future__ import annotations

from typing import Final

ALLOWED_STRUCTURAL_ROLES: Final = frozenset({"REPRESENTATIVE", "CORE", "RELATED"})
STRUCTURAL_ROLE_NULL_ALLOWED: Final = True


def validate_structural_role(value: str | None, *, allow_null: bool = True) -> str | None:
    """Validate a role before any canonical authority write."""

    if value is None and allow_null and STRUCTURAL_ROLE_NULL_ALLOWED:
        return None
    if value not in ALLOWED_STRUCTURAL_ROLES:
        raise ValueError(f"invalid structural role: {value!r}")
    return value


__all__ = [
    "ALLOWED_STRUCTURAL_ROLES",
    "STRUCTURAL_ROLE_NULL_ALLOWED",
    "validate_structural_role",
]
