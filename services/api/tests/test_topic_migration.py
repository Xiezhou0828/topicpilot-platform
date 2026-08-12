from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "0015_phase3_4_003_topic_domain.py"
)


def test_topic_migration_follows_identity_head_and_owns_topic_tables():
    source = MIGRATION.read_text(encoding="utf-8")
    assert 'revision = "0015_phase3_4_003_topic_domain"' in source
    assert 'down_revision = "0014_phase3_4_002_identity_domain"' in source
    assert 'op.create_table(\n        "topics"' in source
    assert 'op.create_table(\n        "topic_hierarchy"' in source
    assert 'schema="topicpilot"' in source
    assert "stock_topic_relations" not in source
