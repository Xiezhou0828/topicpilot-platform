from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from _lib import (
    GOVERNANCE_ROOT,
    git_commit_exists,
    load_json_compatible_yaml,
    load_manifest,
)


def baseline_registry() -> dict[str, Any]:
    return load_json_compatible_yaml(GOVERNANCE_ROOT / "BASELINE_FAILURE_REGISTRY.yaml")


def evaluate_integration(
    manifest: dict[str, Any],
    observed_failures: Iterable[str] = (),
    *,
    ownership_errors_found: Iterable[str] = (),
    shared_conflicts: Iterable[str] = (),
    dependency_status: dict[str, str] | None = None,
) -> dict[str, Any]:
    registry = baseline_registry()
    known = {entry["test_id"]: entry for entry in registry.get("failures", [])}
    observed = sorted(set(observed_failures))
    blockers: list[str] = []
    notes: list[str] = []

    if manifest.get("status") != "READY_FOR_INTEGRATION":
        blockers.append(f"task status is {manifest.get('status')}, not READY_FOR_INTEGRATION")
    commits = manifest.get("implementation_commits", [])
    if not commits:
        blockers.append("implementation commit is missing")
    for commit in commits:
        if not git_commit_exists(commit):
            blockers.append(f"implementation commit is not present: {commit}")

    blockers.extend(ownership_errors_found)
    if shared_conflicts:
        blockers.append("shared surface conflict: " + ", ".join(shared_conflicts))

    if dependency_status:
        for task_id in manifest.get("dependencies", []):
            status = dependency_status.get(task_id)
            if status not in {"READY_FOR_INTEGRATION", "INTEGRATED", "READY_FOR_RELEASE", "DEPLOYED", "VERIFIED", "CLOSED"}:
                blockers.append(f"dependency is not qualified: {task_id}={status}")

    if manifest.get("owner_decision_required"):
        blockers.append("owner decision is required")

    for test_id in observed:
        entry = known.get(test_id)
        if entry is None:
            blockers.append(f"unknown failure blocks qualification: {test_id}")
            continue
        if (
            entry.get("owner_workstream") == manifest.get("workstream")
            or manifest.get("workstream") in entry.get("blocks_workstreams", [])
        ):
            blockers.append(
                f"known failure blocks this workstream: {test_id} "
                f"({entry.get('owner_workstream')})"
            )
        else:
            notes.append(
                f"known failure retained as non-blocking evidence: {test_id} "
                f"({entry.get('owner_workstream')})"
            )

    status = "READY" if not blockers else "BLOCKED"
    return {
        "status": status,
        "safe_commits": commits if status == "READY" else [],
        "shared_conflicts": list(shared_conflicts),
        "baseline_failures": observed,
        "required_reconciliation": blockers,
        "owner_decision_required": bool(manifest.get("owner_decision_required")),
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the bounded integration gate.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--observed-failure", action="append", default=[])
    parser.add_argument("--shared-conflict", action="append", default=[])
    args = parser.parse_args()
    result = evaluate_integration(
        load_manifest(args.manifest),
        args.observed_failure,
        shared_conflicts=args.shared_conflict,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
