from topicpilot_api.orm.base import Base

IMPLEMENTED_V2_TABLES = {
    "markets",
    "instruments",
    "security_identities",
    "topics",
    "instrument_topic_relations",
    "market_data_sources",
    "raw_market_observations",
    "observation_timeline_batches",
    "observation_timeline_entries",
    "observation_timeline_quality_events",
    "topic_hierarchy",
    "canonical_observations",
    "canonical_price_observations",
    "canonical_volume_observations",
    "canonical_quote_observations",
    "canonical_trading_status_observations",
    "reference_registry_sets",
    "reference_currencies",
    "reference_timezones",
    "reference_sessions",
    "reference_trading_statuses",
    "reference_adjustments",
    "live_tracking_universe",
    "live_collector_runs",
    "live_collector_attempts",
    "topic_snapshots",
}


def test_v2_metadata_contains_only_implemented_tables():
    tables = {table.name for table in Base.metadata.tables.values()}
    assert tables == IMPLEMENTED_V2_TABLES | {
        "legacy_import_runs",
        "legacy_import_artifacts",
        "legacy_import_records",
    }
    assert "detectors" not in tables
    assert "strategy_runs" not in tables
    assert "runtime_runs" not in tables


def test_repository_modules_have_explicit_domain_exports():
    from topicpilot_api.repositories import (
        read_current_canonical_observations,
        replay_observation_timeline,
    )

    assert read_current_canonical_observations.__module__.endswith("canonical_observations")
    assert replay_observation_timeline.__module__.endswith("observation_timeline")
