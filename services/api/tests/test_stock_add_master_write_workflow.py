from __future__ import annotations

from pathlib import Path


def test_production_writer_receives_only_hash_and_protected_plan_secret() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    workflow = (
        repository_root / ".github" / "workflows" / "stock-add-master-write.yml"
    ).read_text(encoding="utf-8")

    assert "      plan_sha256:" in workflow
    assert "      plan_json:" not in workflow
    assert "${{ inputs.plan_json }}" not in workflow
    assert "${{ inputs.plan_sha256 }}" in workflow
    assert "${{ secrets.TOPICPILOT_PRODUCTION_STOCK_ADD_PLAN_JSON }}" in workflow
    assert "from topicpilot_api.stock_add_master_writer import canonical_sha256" in workflow
    assert "declared_sha256 != requested_sha256" in workflow
    assert "computed_sha256 != requested_sha256" in workflow
    assert "topicpilot-stock-add-master-plan.v1" in workflow
    assert "print(raw_plan)" not in workflow
