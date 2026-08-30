from pathlib import Path

ROOT = Path(__file__).parents[1]
MIGRATION = ROOT / "alembic" / "versions" / (
    "0036_task_ws4_active_reference_daily_projection.py"
)


def test_daily_projection_prefers_active_reference_and_falls_back_by_date():
    source = MIGRATION.read_text(encoding="utf-8")

    assert "active_reference.status = 'ACTIVE'" in source
    assert "co.reference_data_version = active_reference.reference_data_version" in source
    assert "NOT EXISTS (" in source
    assert "active_co.instrument_id = co.instrument_id" in source
    assert "active_co.family_code = 'PRICE'" in source
    assert "active_co.observed_at AT TIME ZONE m.timezone" in source
    assert "volume_observation.reference_data_version = co.reference_data_version" in source
