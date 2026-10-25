from __future__ import annotations

import re
from pathlib import Path


def test_unconfigured_environment_fails_before_any_environment_job_can_start() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    workflow = (
        repository_root / ".github" / "workflows" / "stock-add-authority-readback.yml"
    ).read_text(encoding="utf-8")

    preflight_match = re.search(
        r"(?ms)^  validate_environment:\n(.*?)(?=^  [\w-]+:\n|\Z)", workflow
    )
    readback_match = re.search(r"(?ms)^  readback:\n(.*?)(?=^  [\w-]+:\n|\Z)", workflow)
    assert preflight_match is not None
    assert readback_match is not None

    preflight = preflight_match.group(1)
    readback = readback_match.group(1)
    assert not re.search(r"(?m)^\s+environment:", preflight)
    assert '"$GITHUB_REF" == "refs/heads/main"' in preflight
    assert 'rule.get("type") == "required_reviewers"' in preflight
    assert 'rule.get("prevent_self_review") is False' in preflight
    assert "allow that Owner to self-approve" in preflight
    assert 'names != ["main"]' in preflight
    assert "needs: validate_environment" in readback
    assert "environment: production-catalog-readonly" in readback
