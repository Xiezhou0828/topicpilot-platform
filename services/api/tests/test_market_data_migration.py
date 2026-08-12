from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "0017_phase3_4_005_market_data_source_and_raw_observations.py"
)


def test_market_data_migration_follows_relationship_head_and_owns_raw_foundation():
    source = MIGRATION.read_text(encoding="utf-8")
    assert 'revision = "0017_phase3_4_005_market_data_source_and_raw_observations"' in source
    assert 'down_revision = "0016_phase3_4_004_instrument_topic_relationships"' in source
    assert '"market_data_sources"' in source
    assert '"raw_market_observations"' in source
    assert 'schema="topicpilot"' in source
    assert "normalized_market_observations" not in source
    assert "market_snapshots" not in source
