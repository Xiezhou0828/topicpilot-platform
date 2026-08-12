from pathlib import Path
MIGRATION = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0016_phase3_4_004_instrument_topic_relationships.py"
def test_relationship_migration_owns_instrument_topic_domain():
    source = MIGRATION.read_text(encoding="utf-8")
    assert 'revision = "0016_phase3_4_004_instrument_topic_relationships"' in source
    assert 'down_revision = "0015_phase3_4_003_topic_domain"' in source
    assert '"instrument_topic_relations"' in source and 'schema="topicpilot"' in source
    assert "stock_topic_relations" not in source
