from pathlib import Path

MIGRATION = Path(__file__).parents[1] / "alembic" / "versions" / "0050_task_purge_retired_topics.py"
WORKFLOW = Path(__file__).parents[3] / ".github" / "workflows" / "deploy.yml"


def test_retired_topic_purge_is_exactly_guarded_and_scoped() -> None:
    source = MIGRATION.read_text(encoding="utf-8")
    for slug in (
        "PCB",
        "其他建設",
        "其他晶圓材料",
        "其他自動化",
        "其他資安",
        "其他高速互連",
        "大型金融權值",
        "特殊金屬材料",
    ):
        assert f'"{slug}"' in source
    assert 'TOPICPILOT_ALLOW_RETIRED_TOPIC_PURGE") != "1"' in source
    assert "EXPECTED_TOPIC_TOTAL = 140" in source
    assert "EXPECTED_ACTIVE_TOTAL = 132" in source
    assert "topicpilot.instruments" not in source
    assert "topicpilot.canonical_observations" not in source


def test_purge_workflow_requires_exact_sha_and_confirmation() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "release_ref" in source
    assert "DELETE_EIGHT_RETIRED_TOPICS" in source
    assert "apply_migration_0050" in source
    assert "production-db-maintenance" in source
    assert "upgrade 0050_task_purge_retired_topics" in source
