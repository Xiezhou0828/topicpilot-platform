from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "0014_phase3_4_002_identity_domain.py"
)


def test_identity_migration_owns_shared_schema_creation():
    source = MIGRATION.read_text(encoding="utf-8")

    assert 'op.execute("CREATE SCHEMA IF NOT EXISTS topicpilot")' in source
    assert 'schema="topicpilot"' in source
    assert "DROP SCHEMA" not in source
