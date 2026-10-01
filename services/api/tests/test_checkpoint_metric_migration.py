from pathlib import Path

MIGRATION = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "0048_task_checkpoint_provider_metric_applicability.py"
)


def test_checkpoint_metric_migration_is_linear_and_preserves_legacy_values() -> None:
    source = MIGRATION.read_text(encoding="utf-8")

    assert 'revision = "0048_task_checkpoint_provider_metric_applicability"' in source
    assert 'down_revision = "0047_task_topic_role_strength_design_freeze"' in source
    assert "nullable=True" in source
    assert "server_default=None" in source
    assert "no historical rewrite is authorized" in source


def test_checkpoint_metric_migration_only_targets_the_two_provider_counters() -> None:
    source = MIGRATION.read_text(encoding="utf-8")

    assert 'TABLE = "live_collector_checkpoints"' in source
    assert 'COLUMNS = ("provider_request_count", "provider_failure_count")' in source
    assert "UPDATE" not in source
    assert "DELETE" not in source
