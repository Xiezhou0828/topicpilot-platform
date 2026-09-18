from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from _lib import (
    GOVERNANCE_ROOT,
    any_path_matches,
    emit_errors,
    git_output,
    load_json_compatible_yaml,
    load_manifest,
    normalize_path,
    path_matches,
)


def ownership_registry() -> dict[str, Any]:
    return load_json_compatible_yaml(GOVERNANCE_ROOT / "WORKSTREAM_OWNERSHIP.yaml")


def paths_from_git(base: str | None = None, include_worktree: bool = False) -> list[str]:
    paths: list[str] = []
    if base:
        output = git_output("diff", "--name-only", f"{base}...HEAD")
        paths.extend(output.splitlines())
    if include_worktree:
        output = git_output("status", "--porcelain")
        for line in output.splitlines():
            if not line:
                continue
            value = line[3:] if len(line) > 3 else line
            if " -> " in value:
                value = value.split(" -> ", 1)[1]
            paths.append(value)
    return sorted({normalize_path(path) for path in paths if path})


def ownership_errors(
    manifest: dict[str, Any],
    paths: list[str],
    registry: dict[str, Any] | None = None,
) -> list[str]:
    registry = registry or ownership_registry()
    workstream = manifest.get("workstream")
    workstreams = registry.get("workstreams", {})
    task_owned = manifest.get("owned_paths", [])
    task_shared = manifest.get("shared_paths", [])
    task_forbidden = manifest.get("forbidden_paths", [])
    shared_policy = manifest.get("shared_surface_policy", "INTEGRATION_OWNER_ONLY")
    errors: list[str] = []

    if workstream not in workstreams:
        errors.append(f"manifest workstream is not registered: {workstream}")
        return errors

    for raw_path in paths:
        path = normalize_path(raw_path)
        if any_path_matches(path, task_forbidden):
            errors.append(f"forbidden modified path: {path}")
            continue

        task_owns = any_path_matches(path, task_owned)
        task_declares_shared = any_path_matches(path, task_shared)
        shared_entry = next(
            (
                item for item in registry.get("shared_surfaces", [])
                if path_matches(path, item.get("pattern", ""))
            ),
            None,
        )

        if task_owns:
            if shared_entry and not (
                workstream == "INTEGRATION" or shared_policy == "EXPLICIT_RECONCILIATION"
            ):
                errors.append(
                    f"shared path requires integration reconciliation: {path} "
                    f"(owner {shared_entry.get('owner')})"
                )
            continue

        if task_declares_shared:
            if shared_policy == "EXPLICIT_RECONCILIATION":
                continue
            errors.append(f"declared shared path is not task-owned: {path}")
            continue

        other_owner = next(
            (
                name for name, details in workstreams.items()
                if name != workstream
                and any_path_matches(path, details.get("owned", []))
            ),
            None,
        )
        if other_owner:
            errors.append(f"unauthorized modified path: {path} (owned by {other_owner})")
            continue

        if shared_entry:
            errors.append(
                f"shared path requires integration reconciliation: {path} "
                f"(owner {shared_entry.get('owner')})"
            )
            continue

        if any_path_matches(path, workstreams[workstream].get("shared", [])):
            errors.append(f"shared path requires explicit reconciliation: {path}")
            continue

        errors.append(f"unregistered modified path: {path}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a task diff against bounded ownership.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--paths", action="append", default=[])
    parser.add_argument("--diff-base")
    parser.add_argument("--include-worktree", action="store_true")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    paths = [normalize_path(path) for path in args.paths]
    paths.extend(paths_from_git(args.diff_base, args.include_worktree))
    paths = sorted(set(paths))
    if not paths:
        return emit_errors(["no paths supplied"], success_message="")
    errors = ownership_errors(manifest, paths)
    return emit_errors(errors, success_message=f"{len(paths)} paths passed ownership checks")


if __name__ == "__main__":
    raise SystemExit(main())
