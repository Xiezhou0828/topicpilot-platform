from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from _lib import (
    GOVERNANCE_ROOT,
    emit_errors,
    git_commit_exists,
    load_json_compatible_yaml,
    load_manifest,
    task_manifest_paths,
)

REQUIRED_FIELDS = (
    "task_id",
    "title",
    "status",
    "owner_role",
    "workstream",
    "base_sha",
    "branch",
    "worktree",
    "owned_paths",
    "shared_paths",
    "forbidden_paths",
    "dependencies",
    "implementation_commits",
    "governance_commits",
    "migration_scope",
    "production_scope",
    "owner_decision_required",
    "next_allowed_state",
)
LIST_FIELDS = (
    "owned_paths",
    "shared_paths",
    "forbidden_paths",
    "dependencies",
    "implementation_commits",
    "governance_commits",
    "dependency_notes",
)
VALID_TASK_ID = re.compile(r"^[A-Z0-9][A-Z0-9._-]+$")


def lifecycle_contract() -> dict[str, Any]:
    return load_json_compatible_yaml(GOVERNANCE_ROOT / "task_lifecycle.json")


def validate_manifest(
    manifest: dict[str, Any],
    *,
    source: str = "<manifest>",
    all_task_ids: set[str] | None = None,
    check_commits: bool = False,
) -> list[str]:
    errors: list[str] = []
    missing = [field for field in REQUIRED_FIELDS if field not in manifest]
    errors.extend(f"{source}: missing required field {field}" for field in missing)
    if missing:
        return errors

    task_id = manifest["task_id"]
    if not isinstance(task_id, str) or not VALID_TASK_ID.fullmatch(task_id):
        errors.append(f"{source}: invalid task_id {task_id!r}")

    for field in ("title", "owner_role", "workstream", "migration_scope", "production_scope"):
        if not isinstance(manifest[field], str) or not manifest[field].strip():
            errors.append(f"{source}: {field} must be a non-empty string")

    contract = lifecycle_contract()
    statuses = set(contract.get("statuses", []))
    status = manifest["status"]
    if status not in statuses:
        errors.append(f"{source}: invalid status {status!r}")

    next_state = manifest["next_allowed_state"]
    if next_state not in statuses:
        errors.append(f"{source}: invalid next_allowed_state {next_state!r}")
    elif status in statuses and next_state not in contract.get("transitions", {}).get(status, []):
        errors.append(f"{source}: illegal transition {status} -> {next_state}")

    for field in LIST_FIELDS:
        value = manifest.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"{source}: {field} must be a list of strings")

    if not isinstance(manifest["owner_decision_required"], bool):
        errors.append(f"{source}: owner_decision_required must be boolean")

    branch = manifest["branch"]
    worktree = manifest["worktree"]
    if (branch is None) != (worktree is None):
        errors.append(f"{source}: branch and worktree must both be null or both be set")

    if status == "READY_FOR_INTEGRATION" and not manifest["implementation_commits"]:
        errors.append(f"{source}: READY_FOR_INTEGRATION requires implementation_commits")

    if status == "ABANDONED" and not (
        manifest.get("disposition_evidence") or manifest.get("supersedes")
    ):
        errors.append(f"{source}: ABANDONED requires disposition_evidence or supersedes")

    if all_task_ids is not None:
        for dependency in manifest["dependencies"]:
            if dependency not in all_task_ids:
                errors.append(f"{source}: unknown dependency target {dependency}")

    if check_commits:
        for field in ("implementation_commits", "governance_commits"):
            for commit in manifest[field]:
                if not git_commit_exists(commit):
                    errors.append(f"{source}: {field} commit not found in repository: {commit}")

    return errors


def validate_manifests(
    paths: list[Path] | None = None,
    *,
    check_commits: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    paths = task_manifest_paths() if paths is None else paths
    manifests: list[dict[str, Any]] = []
    errors: list[str] = []
    ids: set[str] = set()

    for path in paths:
        try:
            manifest = load_manifest(path)
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
            continue
        task_id = manifest.get("task_id")
        if task_id in ids:
            errors.append(f"{path}: duplicate task_id {task_id}")
        if isinstance(task_id, str):
            ids.add(task_id)
        manifests.append(manifest)

    for path, manifest in zip(
        [path for path in paths if path.exists()],
        manifests,
        strict=False,
    ):
        errors.extend(
            validate_manifest(
                manifest,
                source=str(path),
                all_task_ids=ids,
                check_commits=check_commits,
            )
        )
    return manifests, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate TopicPilot task manifests.")
    parser.add_argument("--manifest", action="append", type=Path)
    parser.add_argument("--check-commits", action="store_true")
    args = parser.parse_args()
    _, errors = validate_manifests(args.manifest, check_commits=args.check_commits)
    count = len(args.manifest) if args.manifest else len(task_manifest_paths())
    return emit_errors(errors, success_message=f"{count} task manifests validated")


if __name__ == "__main__":
    raise SystemExit(main())
