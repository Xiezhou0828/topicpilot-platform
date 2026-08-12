from pathlib import Path

import pytest

pytestmark = pytest.mark.governance


ROOT = Path(__file__).resolve().parents[3]


def test_completed_phase_36_import_is_not_stale_in_register() -> None:
    register = (ROOT / "docs" / "WORK_ORDERS.md").read_text(encoding="utf-8")
    detail_path = ROOT / "docs" / "work-orders" / "PHASE_3_6_001B_FIRST_POSTGRESQL_LEGACY_IMPORT.md"
    detail = detail_path.read_text(
        encoding="utf-8"
    )
    row = next(line for line in register.splitlines() if "PHASE-3.6-001B" in line)
    assert "COMPLETED / POSTGRESQL IMPORT VERIFIED" in row
    assert "**Status:** `COMPLETED / POSTGRESQL IMPORT VERIFIED`" in detail
