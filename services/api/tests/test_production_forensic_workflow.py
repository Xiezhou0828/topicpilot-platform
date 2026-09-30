from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(__file__).parents[3] / ".github" / "workflows" / "production-forensic-readback.yml"


def test_forensic_workflow_is_protected_and_exact_sha_bound() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in source
    assert "environment: production-readonly" in source
    assert "deployments: read" in source
    assert "required_reviewers" in source
    assert "production-readonly Environment protection" in source
    assert "forensic_ref:" in source
    assert "exact 40-character commit SHA" in source
    assert "git merge-base --is-ancestor" in source
    assert "TOPICPILOT_PRODUCTION_READONLY_DATABASE_URL" in source
    assert "TOPICPILOT_PRODUCTION_READONLY_ROLE" in source
    assert "secrets.DATABASE_URL" not in source
    assert "MIGRATION_DATABASE_URL" not in source


def test_forensic_workflow_has_no_arbitrary_sql_or_shell_surface() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "type: choice" in source
    assert "POST_CLOSE_RUN_READBACK" in source
    assert "POST_CLOSE_DATE_READBACK" in source
    assert "trading_date:" in source
    assert "--command \"$FORENSIC_COMMAND\"" in source
    assert "--run-id \"$RUN_ID\"" in source
    assert "--database-url" not in source
    assert "psql" not in source.lower()
    assert "sql_input" not in source.lower()
