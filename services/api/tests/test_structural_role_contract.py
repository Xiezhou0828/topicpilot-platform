from pathlib import Path

import pytest

from topicpilot_api.structural_role_contract import (
    ALLOWED_STRUCTURAL_ROLES,
    STRUCTURAL_ROLE_NULL_ALLOWED,
    validate_structural_role,
)


def test_canonical_role_set_and_null_policy_are_explicit() -> None:
    assert {"REPRESENTATIVE", "CORE", "RELATED"} == ALLOWED_STRUCTURAL_ROLES
    assert STRUCTURAL_ROLE_NULL_ALLOWED is True
    assert validate_structural_role(None) is None
    for role in sorted(ALLOWED_STRUCTURAL_ROLES):
        assert validate_structural_role(role, allow_null=False) == role


@pytest.mark.parametrize("value", ["LEAD", "lead", "core", "", " CORE ", "1", "MAIN"])
def test_noncanonical_role_values_fail_before_write(value: str) -> None:
    with pytest.raises(ValueError, match="invalid structural role"):
        validate_structural_role(value, allow_null=False)


def test_database_migration_uses_the_same_allowed_set_and_null_policy() -> None:
    migration = (
        Path(__file__).parents[1]
        / "alembic/versions/0031_task_topic_structural_role_score_projection.py"
    )
    text = migration.read_text(encoding="utf-8")
    assert (
        "structural_role IS NULL OR structural_role IN "
        "('REPRESENTATIVE', 'CORE', 'RELATED')"
    ) in text
