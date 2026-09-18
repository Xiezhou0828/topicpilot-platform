from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _lib import GOVERNANCE_ROOT, load_json_compatible_yaml, load_manifest
from check_integration_gate import evaluate_integration
from check_release_gate import evaluate_migration_lineage
from check_task_lifecycle import validate_manifest_lifecycle
from check_task_ownership import ownership_errors


class GovernanceRuntimeTests(unittest.TestCase):
    def manifest(self, name: str) -> dict:
        return load_manifest(GOVERNANCE_ROOT / "tasks" / name)

    def test_today_cannot_modify_a10_owned_path(self) -> None:
        errors = ownership_errors(
            self.manifest("TASK-TODAY-SIGNALS-CANONICAL-PROMOTION-003.yaml"),
            ["services/api/src/topicpilot_api/live/post_close.py"],
        )
        self.assertTrue(errors)

    def test_a10_cannot_modify_topic_owned_path(self) -> None:
        errors = ownership_errors(
            self.manifest("TASK-A10-POST-CLOSE-CHECKPOINT-RECONCILIATION-002.yaml"),
            ["services/api/src/topicpilot_api/topic_engine/scoring.py"],
        )
        self.assertTrue(errors)

    def test_correct_owned_path_passes_without_c_drive(self) -> None:
        errors = ownership_errors(
            self.manifest("TASK-TODAY-SIGNALS-CANONICAL-PROMOTION-003.yaml"),
            ["services/api/src/topicpilot_api/home_v2_publication.py"],
        )
        self.assertEqual(errors, [])

    def test_ready_without_implementation_commit_fails(self) -> None:
        manifest = self.manifest("TASK-TODAY-SIGNALS-CANONICAL-PROMOTION-003.yaml")
        manifest["status"] = "READY_FOR_INTEGRATION"
        manifest["next_allowed_state"] = "INTEGRATED"
        manifest["implementation_commits"] = []
        errors = validate_manifest_lifecycle(manifest, "synthetic")
        self.assertTrue(any("requires implementation_commits" in error for error in errors))

    def test_abandoned_without_evidence_fails(self) -> None:
        manifest = self.manifest("TASK-TODAY-SIGNALS-CANONICAL-PROMOTION-003.yaml")
        manifest["status"] = "ABANDONED"
        manifest["next_allowed_state"] = "SUPERSEDED"
        manifest["disposition_evidence"] = None
        manifest["supersedes"] = None
        errors = validate_manifest_lifecycle(manifest, "synthetic")
        self.assertTrue(any("ABANDONED requires" in error for error in errors))

    def test_newer_production_migration_blocks_release(self) -> None:
        result = evaluate_migration_lineage(
            "0039_task_a9_b2_formal_correction_supersession",
            "0040_task_a10_recovery_checkpoint_observability",
        )
        self.assertEqual(result["status"], "BLOCKED_MIGRATION")

    def test_known_other_workstream_failure_does_not_block_today(self) -> None:
        manifest = self.manifest("TASK-TODAY-SIGNALS-CANONICAL-RECONCILIATION-002.yaml")
        registry = load_json_compatible_yaml(GOVERNANCE_ROOT / "BASELINE_FAILURE_REGISTRY.yaml")
        result = evaluate_integration(
            manifest,
            [registry["failures"][0]["test_id"]],
        )
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["required_reconciliation"], [])

    def test_unknown_failure_blocks_qualification(self) -> None:
        manifest = self.manifest("TASK-TODAY-SIGNALS-CANONICAL-RECONCILIATION-002.yaml")
        result = evaluate_integration(manifest, ["unknown::test_failure"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("unknown failure" in item for item in result["required_reconciliation"]))


if __name__ == "__main__":
    unittest.main()
